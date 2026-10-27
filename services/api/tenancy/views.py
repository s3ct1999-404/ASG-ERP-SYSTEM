from __future__ import annotations

import uuid
from typing import Any, ClassVar, cast

from django.db.models import F
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.service import record
from identity.models import User
from tenancy import services
from tenancy.base import TenantAPIView
from tenancy.models import Branch, Company, Membership, Role, RoleAssignment, Tenant
from tenancy.permissions import PERMISSIONS
from tenancy.serializers import (
    AssignmentSerializer,
    BranchSerializer,
    CompanySerializer,
    MembershipSerializer,
    RoleSerializer,
)


class AddMemberSerializer(serializers.Serializer[dict[str, str]]):
    email = serializers.EmailField()
    full_name = serializers.CharField(required=False, default="")
    initial_password = serializers.CharField(min_length=12, write_only=True)


class MeView(APIView):
    """Who am I and which tenants may I use (system-mode read of the caller's own memberships)."""

    @extend_schema(
        responses={
            200: inline_serializer(
                "Me", {"email": serializers.EmailField(), "tenants": serializers.ListField()}
            )
        }
    )
    def get(self, request: Request) -> Response:
        user: User = request.user  # type: ignore[assignment]
        ms = Membership.objects.filter(user=user, status="active")
        tenants = Tenant.objects.filter(id__in=[m.tenant_id for m in ms])
        return Response(
            {
                "email": user.email,
                "is_platform_operator": user.is_platform_operator,
                "tenants": [{"id": t.id, "name": t.name, "slug": t.slug} for t in tenants],
            }
        )


class ProvisionTenantView(APIView):
    """Platform-operator only. Operators get no membership, hence no business-data access."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=inline_serializer(
            "ProvisionTenant",
            {
                "name": serializers.CharField(),
                "slug": serializers.SlugField(),
                "owner_email": serializers.EmailField(),
                "owner_password": serializers.CharField(),
                "company_name": serializers.CharField(),
            },
        ),
        responses={201: None},
    )
    def post(self, request: Request) -> Response:
        user: User = request.user  # type: ignore[assignment]
        if not user.is_platform_operator:
            record(action="tenant.provision", outcome="denied", actor_id=user.id)
            return Response(
                {"error": {"code": "forbidden", "message": "Not permitted."}}, status=403
            )
        d = cast(dict[str, Any], request.data)
        tenant = services.provision_tenant(
            name=d["name"],
            slug=d["slug"],
            owner_email=d["owner_email"],
            owner_password=d["owner_password"],
            company_name=d["company_name"],
            actor=user,
        )
        return Response({"id": tenant.id, "slug": tenant.slug}, status=status.HTTP_201_CREATED)


class PermissionCatalogView(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"GET": "tenancy.read"}

    @extend_schema(
        responses={200: inline_serializer("PermCatalog", {"permissions": serializers.DictField()})}
    )
    def get(self, request: Request) -> Response:
        return Response({"permissions": PERMISSIONS})


class CompanyListView(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"GET": "tenancy.read", "POST": "tenancy.manage_org"}

    @extend_schema(responses={200: CompanySerializer(many=True)})
    def get(self, request: Request) -> Response:
        qs = self.access.filter_scope(Company.objects.all(), "tenancy.read", "id", None)
        return Response(CompanySerializer(qs.order_by("name"), many=True).data)

    @extend_schema(request=CompanySerializer, responses={201: CompanySerializer})
    def post(self, request: Request) -> Response:
        s = CompanySerializer(data=request.data)
        s.is_valid(raise_exception=True)
        c = services.create_company(self.access, **s.validated_data)
        return Response(CompanySerializer(c).data, status=201)


class BranchListView(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"GET": "tenancy.read", "POST": "tenancy.manage_org"}

    @extend_schema(responses={200: BranchSerializer(many=True)})
    def get(self, request: Request) -> Response:
        qs = self.access.filter_scope(Branch.objects.all(), "tenancy.read", "company_id", "id")
        return Response(BranchSerializer(qs.order_by("name"), many=True).data)

    @extend_schema(request=BranchSerializer, responses={201: BranchSerializer})
    def post(self, request: Request) -> Response:
        s = BranchSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d: dict[str, Any] = s.validated_data
        b = services.create_branch(
            self.access, company_id=d["company"].id, name=d["name"], code=d["code"]
        )
        return Response(BranchSerializer(b).data, status=201)


class RoleListView(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {
        "GET": "tenancy.read",
        "POST": "tenancy.manage_access",
    }

    @extend_schema(responses={200: RoleSerializer(many=True)})
    def get(self, request: Request) -> Response:
        return Response(RoleSerializer(Role.objects.order_by("name"), many=True).data)

    @extend_schema(request=RoleSerializer, responses={201: RoleSerializer})
    def post(self, request: Request) -> Response:
        s = RoleSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        r = services.create_role(self.access, **s.validated_data)
        return Response(RoleSerializer(r).data, status=201)


class MembershipListView(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {
        "GET": "tenancy.read",
        "POST": "tenancy.manage_access",
    }

    @extend_schema(responses={200: MembershipSerializer(many=True)})
    def get(self, request: Request) -> Response:
        return Response(
            MembershipSerializer(
                Membership.objects.annotate(email=F("user__email")), many=True
            ).data
        )

    @extend_schema(request=AddMemberSerializer, responses={201: MembershipSerializer})
    def post(self, request: Request) -> Response:
        s = AddMemberSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        m = services.add_member(self.access, **s.validated_data)
        return Response(MembershipSerializer(m).data, status=201)


class AssignmentCreateView(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"POST": "tenancy.manage_access"}

    @extend_schema(request=AssignmentSerializer, responses={201: AssignmentSerializer})
    def post(self, request: Request, membership_id: uuid.UUID) -> Response:
        s = AssignmentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        a = services.assign_role(
            self.access,
            membership_id=membership_id,
            role_id=d["role"].id,
            company_id=d["company"].id if d.get("company") else None,
            branch_id=d["branch"].id if d.get("branch") else None,
        )
        return Response(AssignmentSerializer(a).data, status=201)


_ = RoleAssignment  # exported model referenced by serializers

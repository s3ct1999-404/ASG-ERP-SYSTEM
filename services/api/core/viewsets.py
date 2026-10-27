"""Small reusable base for tenant+company scoped list/create endpoints."""

from __future__ import annotations

from typing import Any, ClassVar

from django.db.models import Model
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response

from audit.service import record
from tenancy.base import TenantAPIView


class ScopedListCreate(TenantAPIView):
    """GET lists rows visible under ``read_perm`` (company scope); POST requires ``write_perm``
    for the target company. Subclasses set model, serializer_class, perms and audit_name."""

    model: ClassVar[type[Model]]
    serializer_class: ClassVar[type[serializers.ModelSerializer[Any]]]
    read_perm: ClassVar[str]
    write_perm: ClassVar[str]
    audit_name: ClassVar[str]
    order_by: ClassVar[str] = "created_at"

    @classmethod
    def as_view(cls, **initkwargs: Any) -> Any:  # derive permission_map from the two perms
        cls.permission_map = {"GET": cls.read_perm, "POST": cls.write_perm}
        return super().as_view(**initkwargs)

    def get(self, request: Request) -> Response:
        qs = self.access.filter_scope(
            self.model._default_manager.all(), self.read_perm, "company_id", None
        )
        return Response(self.serializer_class(qs.order_by(self.order_by)[:500], many=True).data)

    def post(self, request: Request) -> Response:
        s = self.serializer_class(data=request.data)
        s.is_valid(raise_exception=True)
        company = s.validated_data["company"]
        self.access.require(self.write_perm, company.id)
        for value in s.validated_data.values():  # no cross-company references (IDOR / data mixing)
            owner = getattr(value, "company_id", None) or getattr(
                getattr(value, "company", None), "id", None
            )
            if isinstance(value, Model) and owner is not None and owner != company.id:
                raise serializers.ValidationError(
                    "Referenced record belongs to a different company."
                )
        obj = s.save(tenant_id=self.access.tenant_id)
        record(
            action=f"{self.audit_name}.create",
            tenant_id=self.access.tenant_id,
            company_id=company.id,
            actor_id=self.access.user_id,
            object_type=self.model.__name__,
            object_id=obj.pk,
        )
        return Response(self.serializer_class(obj).data, status=201)

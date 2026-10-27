from __future__ import annotations

from typing import Any, ClassVar

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response

from audit.service import record
from fiscal import services
from fiscal.models import FiscalDocument, FiscalSettings
from tenancy.base import TenantAPIView
from tenancy.models import Company


class SettingsIn(serializers.Serializer[dict[str, Any]]):
    company = serializers.UUIDField()
    enabled = serializers.BooleanField()
    provider = serializers.ChoiceField(choices=["simulator", "ura_s2s"])
    environment = serializers.ChoiceField(choices=["simulated", "sandbox", "production"])
    offline_window_hours = serializers.IntegerField(required=False, allow_null=True, min_value=1)


def _doc(d: FiscalDocument) -> dict[str, Any]:
    return {
        "id": d.id,
        "invoice": d.invoice_id,
        "status": d.status,
        "provider": d.provider,
        "simulated": d.simulated,
        "attempts": d.attempts,
        "fdn": d.fdn,
        "verification_code": d.verification_code,
        "error": d.last_error_code,
        "label": "SIMULATED - not a URA fiscal document" if d.simulated else "URA response",
    }


class StatusView(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"GET": "fiscal.read"}

    @extend_schema(responses={200: None})
    def get(self, request: Request) -> Response:
        return Response(
            {
                "efris_maturity": services.EFRIS_MATURITY,
                "note": "Simulator only. No real URA submission has occurred; see compliance docs.",
            }
        )


class SettingsView(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"GET": "fiscal.read", "PUT": "fiscal.manage"}

    @extend_schema(responses={200: None})
    def get(self, request: Request) -> Response:
        qs = self.access.filter_scope(
            FiscalSettings.objects.all(), "fiscal.read", "company_id", None
        )
        return Response(
            [
                {
                    "company": s.company_id,
                    "enabled": s.enabled,
                    "provider": s.provider,
                    "environment": s.environment,
                    "offline_window_hours": s.offline_window_hours,
                }
                for s in qs
            ]
        )

    @extend_schema(request=SettingsIn, responses={200: None})
    def put(self, request: Request) -> Response:
        s = SettingsIn(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        self.access.require("fiscal.manage", d["company"])
        if not Company.objects.filter(id=d["company"]).exists():
            return Response(
                {"error": {"code": "invalid", "message": "Unknown company."}}, status=422
            )
        if d["provider"] == "ura_s2s" and d["environment"] == "simulated":
            return Response(
                {"error": {"code": "invalid", "message": "ura_s2s cannot run in simulated mode."}},
                status=422,
            )
        obj, _ = FiscalSettings.objects.update_or_create(
            company_id=d["company"],
            defaults={
                "tenant_id": self.access.tenant_id,
                "enabled": d["enabled"],
                "provider": d["provider"],
                "environment": d["environment"],
                "offline_window_hours": d.get("offline_window_hours"),
            },
        )
        record(
            action="fiscal.settings",
            tenant_id=self.access.tenant_id,
            company_id=d["company"],
            actor_id=self.access.user_id,
            object_type="FiscalSettings",
            object_id=obj.id,
            metadata={
                "enabled": d["enabled"],
                "provider": d["provider"],
                "environment": d["environment"],
            },
        )
        return Response({"ok": True})


class DocumentListView(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"GET": "fiscal.read"}

    @extend_schema(responses={200: None})
    def get(self, request: Request) -> Response:
        qs = self.access.filter_scope(
            FiscalDocument.objects.select_related("invoice"),
            "fiscal.read",
            "company_id",
            "invoice__branch_id",
        )
        return Response([_doc(d) for d in qs.order_by("-created_at")[:200]])


class SubmitView(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"POST": "fiscal.submit"}

    @extend_schema(request=None, responses={200: None})
    def post(self, request: Request, doc_id: Any) -> Response:
        return Response(_doc(services.submit_document(self.access, doc_id=doc_id)))


class ReconcileView(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"POST": "fiscal.submit"}

    @extend_schema(request=None, responses={200: None})
    def post(self, request: Request, doc_id: Any) -> Response:
        return Response(_doc(services.reconcile_document(self.access, doc_id=doc_id)))

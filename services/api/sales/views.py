from __future__ import annotations

from typing import Any, ClassVar

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response

from sales import services
from sales.models import SalesInvoice
from tenancy.base import TenantAPIView


class LineIn(serializers.Serializer[dict[str, Any]]):
    product_id = serializers.UUIDField()
    qty = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=0)
    unit_price = serializers.DecimalField(max_digits=20, decimal_places=2, required=False)


class TenderIn(serializers.Serializer[dict[str, Any]]):
    method = serializers.ChoiceField(choices=["cash", "mobile_money", "card", "bank_transfer"])
    amount = serializers.DecimalField(max_digits=20, decimal_places=2, min_value=0)


class InvoiceIn(serializers.Serializer[dict[str, Any]]):
    branch = serializers.UUIDField()
    warehouse = serializers.UUIDField()
    customer = serializers.UUIDField(required=False, allow_null=True)
    operation_id = serializers.CharField(max_length=100)
    date = serializers.DateField(required=False)
    lines = LineIn(many=True)


class PosSaleIn(serializers.Serializer[dict[str, Any]]):
    branch = serializers.UUIDField()
    warehouse = serializers.UUIDField()
    operation_id = serializers.CharField(max_length=100)
    date = serializers.DateField(required=False)
    lines = LineIn(many=True)
    tenders = TenderIn(many=True)


class PaymentIn(serializers.Serializer[dict[str, Any]]):
    method = serializers.ChoiceField(choices=["cash", "mobile_money", "card", "bank_transfer"])
    amount = serializers.DecimalField(max_digits=20, decimal_places=2, min_value=0)
    idempotency_key = serializers.CharField(max_length=100)


def _inv(i: SalesInvoice, created: bool) -> Response:
    return Response(
        {
            "id": i.id,
            "number": i.number,
            "status": i.status,
            "subtotal": i.subtotal,
            "tax_total": i.tax_total,
            "total": i.total,
            "amount_paid": i.amount_paid,
            "fiscal_status": i.fiscal_status,
            "replayed": not created,
        },
        status=201 if created else 200,
    )


class InvoiceListCreate(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"GET": "sales.read", "POST": "sales.confirm"}

    @extend_schema(responses={200: None})
    def get(self, request: Request) -> Response:
        qs = self.access.filter_scope(SalesInvoice.objects.all(), "sales.read")
        return Response(
            [
                {
                    "id": i.id,
                    "number": i.number,
                    "date": i.date,
                    "channel": i.channel,
                    "status": i.status,
                    "total": i.total,
                    "amount_paid": i.amount_paid,
                    "fiscal_status": i.fiscal_status,
                }
                for i in qs.order_by("-created_at")[:200]
            ]
        )

    @extend_schema(request=InvoiceIn, responses={201: None, 200: None})
    def post(self, request: Request) -> Response:
        s = InvoiceIn(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        return _inv(
            *services.create_invoice(
                self.access,
                branch_id=d["branch"],
                warehouse_id=d["warehouse"],
                customer_id=d.get("customer"),
                lines=[dict(x) for x in d["lines"]],
                operation_id=d["operation_id"],
                date=d.get("date"),
            )
        )


class PaymentCreate(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"POST": "payments.record"}

    @extend_schema(request=PaymentIn, responses={201: None, 200: None})
    def post(self, request: Request, invoice_id: Any) -> Response:
        s = PaymentIn(data=request.data)
        s.is_valid(raise_exception=True)
        p, created = services.record_payment(self.access, invoice_id=invoice_id, **s.validated_data)
        return Response(
            {"id": p.id, "amount": p.amount, "method": p.method, "replayed": not created},
            status=201 if created else 200,
        )


class PosSale(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"POST": "pos.sell"}

    @extend_schema(request=PosSaleIn, responses={201: None, 200: None})
    def post(self, request: Request) -> Response:
        s = PosSaleIn(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        return _inv(
            *services.pos_sale(
                self.access,
                branch_id=d["branch"],
                warehouse_id=d["warehouse"],
                lines=[dict(x) for x in d["lines"]],
                tenders=[dict(t) for t in d["tenders"]],
                operation_id=d["operation_id"],
                date=d.get("date"),
            )
        )

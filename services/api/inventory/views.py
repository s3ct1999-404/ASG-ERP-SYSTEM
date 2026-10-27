from __future__ import annotations

from decimal import Decimal
from typing import Any, ClassVar

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response

from inventory import services
from inventory.models import StockBalance, StockMovement
from tenancy.base import TenantAPIView


class ReceiptIn(serializers.Serializer[dict[str, Any]]):
    warehouse = serializers.UUIDField()
    product = serializers.UUIDField()
    qty = serializers.DecimalField(max_digits=18, decimal_places=4)
    unit_cost = serializers.DecimalField(max_digits=20, decimal_places=4)
    idempotency_key = serializers.CharField(max_length=100)


class AdjustIn(serializers.Serializer[dict[str, Any]]):
    warehouse = serializers.UUIDField()
    product = serializers.UUIDField()
    qty_delta = serializers.DecimalField(max_digits=18, decimal_places=4)
    reason = serializers.CharField(max_length=200)
    idempotency_key = serializers.CharField(max_length=100)


def _mv(m: StockMovement, created: bool) -> Response:
    return Response(
        {
            "id": m.id,
            "qty": m.qty,
            "unit_cost": m.unit_cost,
            "kind": m.kind,
            "replayed": not created,
        },
        status=201 if created else 200,
    )


class ReceiptView(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"POST": "inventory.receive"}

    @extend_schema(request=ReceiptIn, responses={201: None, 200: None})
    def post(self, request: Request) -> Response:
        s = ReceiptIn(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        return _mv(
            *services.receive_stock(
                self.access,
                warehouse_id=d["warehouse"],
                product_id=d["product"],
                qty=d["qty"],
                unit_cost=d["unit_cost"],
                idempotency_key=d["idempotency_key"],
            )
        )


class AdjustmentView(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"POST": "inventory.adjust"}

    @extend_schema(request=AdjustIn, responses={201: None, 200: None})
    def post(self, request: Request) -> Response:
        s = AdjustIn(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        return _mv(
            *services.adjust_stock(
                self.access,
                warehouse_id=d["warehouse"],
                product_id=d["product"],
                qty_delta=d["qty_delta"],
                reason=d["reason"],
                idempotency_key=d["idempotency_key"],
            )
        )


class StockView(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"GET": "inventory.read"}

    @extend_schema(responses={200: None})
    def get(self, request: Request) -> Response:
        qs = self.access.filter_scope(
            StockBalance.objects.select_related("product", "warehouse"),
            "inventory.read",
            "warehouse__company_id",
            "warehouse__branch_id",
        )
        return Response(
            [
                {
                    "warehouse": b.warehouse.code,
                    "sku": b.product.sku,
                    "qty": b.qty,
                    "avg_cost": b.avg_cost,
                    "value": (b.qty * b.avg_cost).quantize(Decimal("0.01")),
                }
                for b in qs.order_by("warehouse__code", "product__sku")[:500]
            ]
        )


class MovementListView(TenantAPIView):
    permission_map: ClassVar[dict[str, str]] = {"GET": "inventory.read"}

    @extend_schema(responses={200: None})
    def get(self, request: Request) -> Response:
        qs = self.access.filter_scope(
            StockMovement.objects.select_related("product", "warehouse"), "inventory.read"
        )
        return Response(
            [
                {
                    "id": m.id,
                    "at": m.created_at,
                    "sku": m.product.sku,
                    "warehouse": m.warehouse.code,
                    "kind": m.kind,
                    "qty": m.qty,
                    "unit_cost": m.unit_cost,
                    "ref": m.ref_id,
                }
                for m in qs.order_by("-created_at")[:200]
            ]
        )

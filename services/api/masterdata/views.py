from __future__ import annotations

from typing import ClassVar

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response

from core.viewsets import ScopedListCreate
from masterdata.models import Partner, Product, TaxCode, UnitOfMeasure, Warehouse
from tenancy.base import TenantAPIView


def _ser(m: type, fields: list[str]) -> type[serializers.ModelSerializer]:  # type: ignore[type-arg]
    meta = type("Meta", (), {"model": m, "fields": ["id", *fields], "read_only_fields": ["id"]})
    return type(f"{m.__name__}Serializer", (serializers.ModelSerializer,), {"Meta": meta})


def _view(
    m: type, fields: list[str], name: str, order: str = "created_at"
) -> type[ScopedListCreate]:
    return type(
        f"{m.__name__}ListCreate",
        (ScopedListCreate,),
        {
            "model": m,
            "serializer_class": _ser(m, fields),
            "read_perm": "masterdata.read",
            "write_perm": "masterdata.write",
            "audit_name": name,
            "order_by": order,
        },
    )


TaxCodeView = _view(
    TaxCode,
    ["company", "name", "rate", "is_exempt", "effective_from", "effective_to", "source_note"],
    "taxcode",
)
PartnerView = _view(
    Partner,
    ["company", "kind", "name", "tin", "nin_or_brn", "phone", "is_active"],
    "partner",
    "name",
)
ProductView = _view(
    Product,
    ["company", "sku", "name", "uom", "tax_code", "sale_price", "is_service", "is_active"],
    "product",
    "sku",
)
WarehouseView = _view(Warehouse, ["company", "branch", "code", "name"], "warehouse", "code")


class UnitOfMeasureListView(TenantAPIView):
    """Read-only list of the tenant's units of measure (RLS scopes rows to the tenant).

    Needed by clients to create products; there is no write endpoint yet (known gap).
    """

    permission_map: ClassVar[dict[str, str]] = {"GET": "masterdata.read"}

    @extend_schema(responses={200: None})
    def get(self, request: Request) -> Response:
        rows = UnitOfMeasure.objects.order_by("code")
        return Response([{"id": u.id, "code": u.code, "name": u.name} for u in rows])

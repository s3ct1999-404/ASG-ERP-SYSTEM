from __future__ import annotations

from rest_framework import serializers

from core.viewsets import ScopedListCreate
from masterdata.models import Partner, Product, TaxCode, UnitOfMeasure, Warehouse


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
_ = UnitOfMeasure

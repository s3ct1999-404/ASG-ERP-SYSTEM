from __future__ import annotations

import uuid

from django.db import models
from django.db.models import Q

from masterdata.models import Product, Warehouse
from tenancy.models import Branch, Company, TenantOwned


class StockMovement(TenantOwned):
    """Immutable stock ledger row (DB trigger). qty is signed: + in, - out."""

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="+")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="+")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="+")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="+")
    kind = models.CharField(
        max_length=20
    )  # receipt | sale | adjustment | transfer_in | transfer_out | return
    qty = models.DecimalField(max_digits=18, decimal_places=4)
    unit_cost = models.DecimalField(max_digits=20, decimal_places=4)
    ref_type = models.CharField(max_length=30, blank=True)
    ref_id = models.CharField(max_length=64, blank=True)
    idempotency_key = models.CharField(max_length=100, null=True, blank=True)  # noqa: DJ001 (NULL = no key; unique only when set)
    request_hash = models.CharField(max_length=64, blank=True)
    actor_id = models.UUIDField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "idempotency_key", "product"],
                condition=Q(idempotency_key__isnull=False),
                name="uq_movement_idem",
            ),
            models.CheckConstraint(condition=~Q(qty=0), name="ck_movement_nonzero"),
        ]


class StockBalance(TenantOwned):
    """Derived from movements; reconcilable via inventory.services.reconcile()."""

    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="+")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="+")
    qty = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    avg_cost = models.DecimalField(max_digits=20, decimal_places=4, default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["warehouse", "product"], name="uq_balance")]


_ = uuid

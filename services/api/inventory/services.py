"""Stock ledger with weighted-average costing (D-009) and idempotent, race-safe movements."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from accounting import services as acc
from audit.service import record
from core.exceptions import ConflictError, DomainError
from core.money import q2, q4, request_hash
from inventory.models import StockBalance, StockMovement
from masterdata.models import Product, Warehouse
from tenancy.context import AccessContext


def apply_movement(
    *,
    warehouse: Warehouse,
    product: Product,
    qty: Decimal,
    unit_cost: Decimal | None,
    kind: str,
    ref_type: str = "",
    ref_id: Any = "",
    idempotency_key: str | None = None,
    actor_id: Any = None,
) -> tuple[StockMovement, bool]:
    """Returns (movement, created). A replay of the same key+payload returns the original."""
    if qty == 0:
        raise DomainError("Quantity must not be zero.", "invalid_quantity")
    h = request_hash(
        [str(warehouse.id), str(product.id), str(qty), str(unit_cost), kind, ref_type, str(ref_id)]
    )
    if idempotency_key:
        prior = StockMovement.objects.filter(
            tenant_id=warehouse.tenant_id, idempotency_key=idempotency_key, product=product
        ).first()
        if prior:
            if prior.request_hash != h:
                raise ConflictError(
                    "Idempotency key reused with a different request.", "idempotency_mismatch"
                )
            return prior, False
    StockBalance.objects.get_or_create(
        tenant_id=warehouse.tenant_id, warehouse=warehouse, product=product
    )
    bal = StockBalance.objects.select_for_update().get(
        warehouse=warehouse, product=product
    )  # serialises
    company = warehouse.company
    if qty > 0:
        cost = q4(unit_cost if unit_cost is not None else bal.avg_cost)
        new_qty = bal.qty + qty
        bal.avg_cost = q4((bal.qty * bal.avg_cost + qty * cost) / new_qty) if bal.qty > 0 else cost
    else:
        cost = bal.avg_cost
        new_qty = bal.qty + qty
        if new_qty < 0 and not company.allow_negative_stock:
            raise DomainError(f"Insufficient stock: {bal.qty} available.", "insufficient_stock")
    bal.qty = new_qty
    bal.save(update_fields=["qty", "avg_cost"])
    mv = StockMovement.objects.create(
        tenant_id=warehouse.tenant_id,
        company=company,
        branch_id=warehouse.branch_id,
        warehouse=warehouse,
        product=product,
        kind=kind,
        qty=qty,
        unit_cost=cost,
        ref_type=ref_type,
        ref_id=str(ref_id or ""),
        idempotency_key=idempotency_key,
        request_hash=h,
        actor_id=actor_id,
    )
    return mv, True


def _load(
    ctx: AccessContext, warehouse_id: uuid.UUID, product_id: uuid.UUID
) -> tuple[Warehouse, Product]:
    wh = Warehouse.objects.select_related("company").filter(id=warehouse_id).first()
    pr = Product.objects.filter(id=product_id).first()
    if wh is None or pr is None or pr.company_id != wh.company_id:
        raise ValidationError("Unknown warehouse or product.")
    if pr.is_service:
        raise DomainError("Services are not stocked.", "not_stocked")
    return wh, pr


@transaction.atomic
def receive_stock(
    ctx: AccessContext,
    *,
    warehouse_id: uuid.UUID,
    product_id: uuid.UUID,
    qty: Decimal,
    unit_cost: Decimal,
    idempotency_key: str,
    date: dt.date | None = None,
) -> tuple[StockMovement, bool]:
    wh, pr = _load(ctx, warehouse_id, product_id)
    ctx.require("inventory.receive", wh.company_id, wh.branch_id)
    if qty <= 0 or unit_cost < 0:
        raise DomainError("Quantity must be positive and cost non-negative.", "invalid_quantity")
    mv, created = apply_movement(
        warehouse=wh,
        product=pr,
        qty=qty,
        unit_cost=unit_cost,
        kind="receipt",
        idempotency_key=idempotency_key,
        actor_id=ctx.user_id,
    )
    if created:
        value = q2(qty * unit_cost)
        if value > 0:
            acc.post_entry(
                company=wh.company,
                date=date or dt.date.today(),
                branch_id=wh.branch_id,
                lines=[
                    (acc.rule_account(wh.company_id, "inventory"), value, Decimal(0)),
                    (acc.rule_account(wh.company_id, "grni"), Decimal(0), value),
                ],
                memo=f"Goods receipt {pr.sku}",
                source_type="stock_movement",
                source_id=mv.id,
                actor_id=ctx.user_id,
            )
        record(
            action="stock.receive",
            tenant_id=ctx.tenant_id,
            company_id=wh.company_id,
            branch_id=wh.branch_id,
            actor_id=ctx.user_id,
            object_type="StockMovement",
            object_id=mv.id,
        )
    return mv, created


@transaction.atomic
def adjust_stock(
    ctx: AccessContext,
    *,
    warehouse_id: uuid.UUID,
    product_id: uuid.UUID,
    qty_delta: Decimal,
    reason: str,
    idempotency_key: str,
    date: dt.date | None = None,
) -> tuple[StockMovement, bool]:
    wh, pr = _load(ctx, warehouse_id, product_id)
    ctx.require("inventory.adjust", wh.company_id, wh.branch_id)
    if not reason.strip():
        raise DomainError("A reason is required for an adjustment.", "reason_required")
    mv, created = apply_movement(
        warehouse=wh,
        product=pr,
        qty=qty_delta,
        unit_cost=None,
        kind="adjustment",
        ref_type="reason",
        ref_id=reason[:60],
        idempotency_key=idempotency_key,
        actor_id=ctx.user_id,
    )
    if created:
        value = q2(abs(qty_delta) * mv.unit_cost)
        if value > 0:
            inv, adj = (
                acc.rule_account(wh.company_id, "inventory"),
                acc.rule_account(wh.company_id, "inventory_adjustment"),
            )
            lines = (
                [(inv, value, Decimal(0)), (adj, Decimal(0), value)]
                if qty_delta > 0
                else [(adj, value, Decimal(0)), (inv, Decimal(0), value)]
            )
            acc.post_entry(
                company=wh.company,
                date=date or dt.date.today(),
                branch_id=wh.branch_id,
                lines=lines,
                memo=f"Stock adjustment: {reason}",
                source_type="stock_movement",
                source_id=mv.id,
                actor_id=ctx.user_id,
            )
        record(
            action="stock.adjust",
            tenant_id=ctx.tenant_id,
            company_id=wh.company_id,
            branch_id=wh.branch_id,
            actor_id=ctx.user_id,
            object_type="StockMovement",
            object_id=mv.id,
            metadata={"reason": reason},
        )
    return mv, created


def reconcile(warehouse_id: uuid.UUID, product_id: uuid.UUID) -> dict[str, Decimal]:
    """Balance must equal the sum of movements (Blueprint §6.2)."""
    total = StockMovement.objects.filter(
        warehouse_id=warehouse_id, product_id=product_id
    ).aggregate(s=Sum("qty"))["s"]
    bal = StockBalance.objects.filter(warehouse_id=warehouse_id, product_id=product_id).first()
    return {"ledger": total or Decimal(0), "balance": bal.qty if bal else Decimal(0)}

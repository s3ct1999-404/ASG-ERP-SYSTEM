"""Sales invoicing, POS sale and payments. One transaction = stock + ledger + document."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction

from accounting import services as acc
from audit.service import record
from core.exceptions import ConflictError, DomainError
from core.money import q2, request_hash
from inventory.services import apply_movement
from masterdata.models import Partner, Product, Warehouse
from sales.models import InvoiceLine, Payment, SalesInvoice
from tenancy.context import AccessContext
from tenancy.models import Branch

PAY_RULE = {"cash": "cash", "mobile_money": "mobile_money", "card": "bank", "bank_transfer": "bank"}


def _tax_rate(product: Product, date: dt.date, vat_registered: bool) -> tuple[Decimal, Any]:
    tc = product.tax_code
    if tc is None or not vat_registered or tc.is_exempt:
        return Decimal("0"), tc
    if tc.effective_from > date or (tc.effective_to and tc.effective_to < date):
        raise DomainError(f"Tax code '{tc.name}' is not effective on {date}.", "tax_not_effective")
    return tc.rate, tc


@transaction.atomic
def create_invoice(
    ctx: AccessContext,
    *,
    branch_id: uuid.UUID,
    warehouse_id: uuid.UUID,
    customer_id: uuid.UUID | None,
    lines: list[dict[str, Any]],
    operation_id: str,
    date: dt.date | None = None,
    channel: str = "sales",
) -> tuple[SalesInvoice, bool]:
    """Issue an invoice and its stock/ledger effects atomically. Returns (invoice, created)."""
    perm = "pos.sell" if channel == "pos" else "sales.confirm"
    branch = Branch.objects.select_related("company").filter(id=branch_id).first()
    wh = Warehouse.objects.filter(id=warehouse_id).first()
    if branch is None or wh is None or wh.branch_id != branch.id:
        raise ValidationError("Unknown branch/warehouse, or warehouse not in this branch.")
    ctx.require(perm, branch.company_id, branch.id)
    if not lines:
        raise DomainError("An invoice needs at least one line.", "no_lines")
    if not operation_id:
        raise DomainError("operation_id is required (idempotency).", "operation_id_required")
    date = date or dt.date.today()
    company = branch.company
    h = request_hash(
        {
            "b": str(branch_id),
            "w": str(warehouse_id),
            "c": str(customer_id),
            "d": str(date),
            "ch": channel,
            "l": [{k: str(v) for k, v in ln.items()} for ln in lines],
        }
    )
    prior = SalesInvoice.objects.filter(tenant_id=ctx.tenant_id, operation_id=operation_id).first()
    if prior:
        if prior.request_hash != h:
            raise ConflictError(
                "operation_id reused with a different request.", "idempotency_mismatch"
            )
        return prior, False
    customer = None
    if customer_id:
        customer = Partner.objects.filter(id=customer_id, kind="customer").first()
        if customer is None or customer.company_id != company.id:
            raise ValidationError("Unknown customer.")
    prods = {
        p.id: p
        for p in Product.objects.select_related("tax_code").filter(
            id__in=[ln["product_id"] for ln in lines], company=company
        )
    }
    built = []
    for ln in lines:
        p = prods.get(uuid.UUID(str(ln["product_id"])))
        qty = Decimal(str(ln["qty"]))
        if p is None or not p.is_active or qty <= 0:
            raise DomainError("Unknown/inactive product or non-positive quantity.", "invalid_line")
        price = (
            q2(Decimal(str(ln["unit_price"]))) if ln.get("unit_price") is not None else p.sale_price
        )
        rate, tc = _tax_rate(p, date, company.vat_registered)
        net = q2(qty * price)
        built.append((p, tc, qty, price, rate, net, q2(net * rate)))
    subtotal = sum((b[5] for b in built), Decimal(0))
    tax_total = sum((b[6] for b in built), Decimal(0))
    inv = SalesInvoice.objects.create(
        tenant_id=ctx.tenant_id,
        company=company,
        branch=branch,
        warehouse=wh,
        customer=customer,
        number=acc.next_number(company, "invoice", "INV"),
        channel=channel,
        date=date,
        subtotal=subtotal,
        tax_total=tax_total,
        total=subtotal + tax_total,
        operation_id=operation_id,
        request_hash=h,
        created_by=ctx.user_id,
    )
    cogs = Decimal(0)
    for p, tc, qty, price, rate, net, tax in built:
        unit_cost = Decimal(0)
        if not p.is_service:
            mv, _ = apply_movement(
                warehouse=wh,
                product=p,
                qty=-qty,
                unit_cost=None,
                kind="sale",
                ref_type="invoice",
                ref_id=inv.id,
                idempotency_key=f"inv:{operation_id}",
                actor_id=ctx.user_id,
            )
            unit_cost = mv.unit_cost
            cogs += q2(qty * unit_cost)
        InvoiceLine.objects.create(
            tenant_id=ctx.tenant_id,
            invoice=inv,
            product=p,
            tax_code=tc,
            qty=qty,
            unit_price=price,
            tax_rate=rate,
            net=net,
            tax=tax,
            unit_cost=unit_cost,
        )
    z = Decimal(0)
    lines_je = [
        (acc.rule_account(company.id, "receivable"), inv.total, z),
        (acc.rule_account(company.id, "sales_revenue"), z, subtotal),
    ]
    if tax_total > 0:
        lines_je.append((acc.rule_account(company.id, "vat_output"), z, tax_total))
    if cogs > 0:
        lines_je += [
            (acc.rule_account(company.id, "cogs"), cogs, z),
            (acc.rule_account(company.id, "inventory"), z, cogs),
        ]
    je = acc.post_entry(
        company=company,
        date=date,
        lines=lines_je,
        memo=f"Invoice {inv.number}",
        source_type="invoice",
        source_id=inv.id,
        branch_id=branch.id,
        actor_id=ctx.user_id,
    )
    SalesInvoice.objects.filter(id=inv.id).update(journal_entry_id=je.id)
    inv.journal_entry_id = je.id
    record(
        action="invoice.issue",
        tenant_id=ctx.tenant_id,
        company_id=company.id,
        branch_id=branch.id,
        actor_id=ctx.user_id,
        object_type="SalesInvoice",
        object_id=inv.id,
        metadata={"number": inv.number, "channel": channel, "total": str(inv.total)},
    )
    from fiscal.hooks import on_invoice_issued  # local import: fiscal depends on sales

    on_invoice_issued(inv)
    return inv, True


@transaction.atomic
def record_payment(
    ctx: AccessContext,
    *,
    invoice_id: uuid.UUID,
    method: str,
    amount: Decimal,
    idempotency_key: str,
    date: dt.date | None = None,
) -> tuple[Payment, bool]:
    if method not in PAY_RULE:
        raise DomainError("Unsupported payment method.", "invalid_method")
    amount = q2(amount)
    if amount <= 0 or not idempotency_key:
        raise DomainError("Positive amount and idempotency key are required.", "invalid_payment")
    inv = (
        SalesInvoice.objects.select_for_update()
        .select_related("company")
        .filter(id=invoice_id)
        .first()
    )
    if inv is None:
        raise ValidationError("Unknown invoice.")
    ctx.require("payments.record", inv.company_id, inv.branch_id)
    h = request_hash([str(invoice_id), method, str(amount)])
    prior = Payment.objects.filter(tenant_id=ctx.tenant_id, idempotency_key=idempotency_key).first()
    if prior:
        if prior.request_hash != h:
            raise ConflictError(
                "Idempotency key reused with a different request.", "idempotency_mismatch"
            )
        return prior, False
    if inv.status == "reversed":
        raise ConflictError("Invoice is reversed.", "invoice_reversed")
    if amount > inv.total - inv.amount_paid:
        raise DomainError("Payment exceeds the outstanding balance.", "overpayment")
    date = date or dt.date.today()
    pay = Payment.objects.create(
        tenant_id=ctx.tenant_id,
        company=inv.company,
        branch_id=inv.branch_id,
        invoice=inv,
        method=method,
        amount=amount,
        idempotency_key=idempotency_key,
        request_hash=h,
        created_by=ctx.user_id,
    )
    je = acc.post_entry(
        company=inv.company,
        date=date,
        branch_id=inv.branch_id,
        lines=[
            (acc.rule_account(inv.company_id, PAY_RULE[method]), amount, Decimal(0)),
            (acc.rule_account(inv.company_id, "receivable"), Decimal(0), amount),
        ],
        memo=f"Payment for {inv.number}",
        source_type="payment",
        source_id=pay.id,
        actor_id=ctx.user_id,
    )
    inv.amount_paid += amount
    inv.status = "paid" if inv.amount_paid == inv.total else "issued"
    inv.save(update_fields=["amount_paid", "status"])
    Payment.objects.filter(
        id=pay.id
    )  # payments are immutable; journal link kept on the entry (source_id)
    record(
        action="payment.record",
        tenant_id=ctx.tenant_id,
        company_id=inv.company_id,
        branch_id=inv.branch_id,
        actor_id=ctx.user_id,
        object_type="Payment",
        object_id=pay.id,
        metadata={"method": method, "amount": str(amount), "journal": je.number},
    )
    return pay, True


@transaction.atomic
def pos_sale(
    ctx: AccessContext,
    *,
    branch_id: uuid.UUID,
    warehouse_id: uuid.UUID,
    lines: list[dict[str, Any]],
    tenders: list[dict[str, Any]],
    operation_id: str,
    date: dt.date | None = None,
) -> tuple[SalesInvoice, bool]:
    """Single POS operation (the unit queued offline): invoice + tendered payments, idempotent."""
    inv, created = create_invoice(
        ctx,
        branch_id=branch_id,
        warehouse_id=warehouse_id,
        customer_id=None,
        lines=lines,
        operation_id=operation_id,
        date=date,
        channel="pos",
    )
    for i, t in enumerate(tenders):
        record_payment(
            ctx,
            invoice_id=inv.id,
            method=t["method"],
            amount=Decimal(str(t["amount"])),
            idempotency_key=f"{operation_id}:pay:{i}",
            date=date,
        )
    inv.refresh_from_db()
    return inv, created

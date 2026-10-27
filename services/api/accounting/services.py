"""Double-entry posting engine. Invariants are enforced here AND by DB constraints/triggers."""

from __future__ import annotations

import datetime as dt
import uuid
from collections import defaultdict
from decimal import Decimal
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum

from accounting.models import (
    Account,
    DocumentSequence,
    FiscalPeriod,
    JournalEntry,
    JournalLine,
    PostingRule,
)
from audit.service import record
from core.exceptions import ConflictError, DomainError
from core.money import q2
from tenancy.context import AccessContext
from tenancy.models import Company

# D-008: starter chart. EVERY account is flagged requires_review until an accountant clears it.
STARTER_CHART: list[tuple[str, str, str]] = [
    ("1000", "Cash on hand", "asset"),
    ("1010", "Mobile money", "asset"),
    ("1020", "Bank", "asset"),
    ("1100", "Accounts receivable", "asset"),
    ("1200", "Inventory", "asset"),
    ("2000", "Accounts payable", "liability"),
    ("2100", "VAT payable (output)", "liability"),
    ("2200", "Goods received not invoiced", "liability"),
    ("3000", "Owner's equity", "equity"),
    ("4000", "Sales revenue", "income"),
    ("5000", "Cost of goods sold", "expense"),
    ("5100", "Inventory adjustments", "expense"),
]
STARTER_RULES = {
    "cash": "1000",
    "mobile_money": "1010",
    "bank": "1020",
    "receivable": "1100",
    "inventory": "1200",
    "payable": "2000",
    "vat_output": "2100",
    "grni": "2200",
    "sales_revenue": "4000",
    "cogs": "5000",
    "inventory_adjustment": "5100",
}


def seed_company_accounts(tenant_id: uuid.UUID, company: Company) -> None:
    accts = {
        code: Account.objects.get_or_create(
            tenant_id=tenant_id,
            company=company,
            code=code,
            defaults={"name": name, "type": typ, "requires_review": True},
        )[0]
        for code, name, typ in STARTER_CHART
    }
    for key, code in STARTER_RULES.items():
        PostingRule.objects.get_or_create(
            tenant_id=tenant_id, company=company, key=key, defaults={"account": accts[code]}
        )


def rule_account(company_id: uuid.UUID, key: str) -> Account:
    rule = (
        PostingRule.objects.select_related("account").filter(company_id=company_id, key=key).first()
    )
    if rule is None:
        raise DomainError(
            f"No posting rule '{key}' configured for this company.", "no_posting_rule"
        )
    return rule.account


def next_number(company: Company, key: str, prefix: str) -> str:
    seq, _ = DocumentSequence.objects.select_for_update().get_or_create(
        tenant_id=company.tenant_id, company=company, key=key
    )
    n = seq.next_value
    seq.next_value = n + 1
    seq.save(update_fields=["next_value"])
    return f"{prefix}-{n:06d}"


def _period(company: Company, date: dt.date) -> FiscalPeriod:
    p, _ = FiscalPeriod.objects.get_or_create(
        tenant_id=company.tenant_id, company=company, year=date.year, month=date.month
    )
    return p


def post_entry(
    *,
    company: Company,
    date: dt.date,
    lines: list[tuple[Account, Decimal, Decimal]],
    memo: str = "",
    source_type: str = "",
    source_id: Any = "",
    branch_id: Any = None,
    actor_id: Any = None,
    reverses: JournalEntry | None = None,
    prefix: str = "JE",
) -> JournalEntry:
    """Post a balanced entry. Internal API: callers perform permission checks first."""
    if len(lines) < 2:
        raise DomainError("A journal entry needs at least two lines.", "unbalanced")
    norm = [(a, q2(d), q2(c)) for a, d, c in lines]
    for a, d, c in norm:
        if d < 0 or c < 0 or (d > 0) == (c > 0):
            raise DomainError("Each line must have exactly one positive side.", "invalid_line")
        if a.company_id != company.id or not a.is_active:
            raise DomainError(
                "Account does not belong to this company or is inactive.", "invalid_account"
            )
    if sum(d for _, d, _ in norm) != sum(c for _, _, c in norm):
        raise DomainError("Debits must equal credits.", "unbalanced")
    if _period(company, date).status != "open":
        raise ConflictError("The fiscal period is closed.", "period_closed")
    entry = JournalEntry.objects.create(
        tenant_id=company.tenant_id,
        company=company,
        branch_id=branch_id,
        number=next_number(company, "journal", prefix),
        date=date,
        memo=memo,
        source_type=source_type,
        source_id=str(source_id or ""),
        reverses=reverses,
        posted_by=actor_id,
    )
    JournalLine.objects.bulk_create(
        [
            JournalLine(tenant_id=company.tenant_id, entry=entry, account=a, debit=d, credit=c)
            for a, d, c in norm
        ]
    )
    record(
        action="journal.post",
        tenant_id=company.tenant_id,
        company_id=company.id,
        actor_id=actor_id,
        object_type="JournalEntry",
        object_id=entry.id,
        metadata={"number": entry.number},
    )
    return entry


@transaction.atomic
def post_manual(
    ctx: AccessContext,
    *,
    company_id: uuid.UUID,
    date: dt.date,
    memo: str,
    lines: list[dict[str, Any]],
) -> JournalEntry:
    ctx.require("accounting.post", company_id)
    company = Company.objects.filter(id=company_id).first()
    if company is None:
        raise ValidationError("Unknown company.")
    accts = {a.id: a for a in Account.objects.filter(id__in=[ln["account"] for ln in lines])}
    try:
        built = [
            (
                accts[uuid.UUID(str(ln["account"]))],
                Decimal(str(ln.get("debit", 0))),
                Decimal(str(ln.get("credit", 0))),
            )
            for ln in lines
        ]
    except (KeyError, ValueError, ArithmeticError):
        raise ValidationError("Invalid journal lines.") from None
    return post_entry(
        company=company,
        date=date,
        lines=built,
        memo=memo,
        source_type="manual",
        actor_id=ctx.user_id,
        prefix="JE",
    )


@transaction.atomic
def reverse_entry(
    ctx: AccessContext, *, entry_id: uuid.UUID, date: dt.date, reason: str
) -> JournalEntry:
    entry = JournalEntry.objects.select_related("company").filter(id=entry_id).first()
    if entry is None:
        raise ValidationError("Unknown entry.")
    ctx.require("accounting.reverse", entry.company_id)
    if entry.reverses_id is not None:
        raise ConflictError("A reversal cannot itself be reversed.", "already_reversal")
    if JournalEntry.objects.filter(reverses=entry).exists():
        raise ConflictError("Entry is already reversed.", "already_reversed")
    swapped = [(ln.account, ln.credit, ln.debit) for ln in entry.lines.select_related("account")]
    rev = post_entry(
        company=entry.company,
        date=date,
        lines=swapped,
        memo=f"Reversal of {entry.number}: {reason}",
        source_type="reversal",
        source_id=entry.id,
        branch_id=entry.branch_id,
        actor_id=ctx.user_id,
        reverses=entry,
        prefix="RV",
    )
    record(
        action="journal.reverse",
        tenant_id=ctx.tenant_id,
        company_id=entry.company_id,
        actor_id=ctx.user_id,
        object_type="JournalEntry",
        object_id=entry.id,
        metadata={"reason": reason},
    )
    return rev


def set_period_status(
    ctx: AccessContext, *, company_id: uuid.UUID, year: int, month: int, status: str
) -> FiscalPeriod:
    ctx.require("accounting.manage_periods", company_id)
    if status not in {"open", "closed"}:
        raise ValidationError("Invalid status.")
    company = Company.objects.filter(id=company_id).first()
    if company is None:
        raise PermissionDenied("Not permitted.")
    p, _ = FiscalPeriod.objects.get_or_create(
        tenant_id=ctx.tenant_id, company=company, year=year, month=month
    )
    p.status = status
    p.save(update_fields=["status"])
    record(
        action=f"period.{status}",
        tenant_id=ctx.tenant_id,
        company_id=company_id,
        actor_id=ctx.user_id,
        object_type="FiscalPeriod",
        object_id=p.id,
        metadata={"year": year, "month": month},
    )
    return p


def trial_balance(company_id: uuid.UUID) -> list[dict[str, Any]]:
    rows = (
        JournalLine.objects.filter(entry__company_id=company_id)
        .values("account__code", "account__name", "account__type")
        .annotate(debit=Sum("debit"), credit=Sum("credit"))
        .order_by("account__code")
    )
    return [
        {
            "code": r["account__code"],
            "name": r["account__name"],
            "type": r["account__type"],
            "debit": r["debit"] or Decimal(0),
            "credit": r["credit"] or Decimal(0),
            "balance": (r["debit"] or Decimal(0)) - (r["credit"] or Decimal(0)),
        }
        for r in rows
    ]


def statements(company_id: uuid.UUID) -> dict[str, Any]:
    by: dict[str, Decimal] = defaultdict(Decimal)
    for r in trial_balance(company_id):
        by[r["type"]] += r["balance"]
    income, expense = -by["income"], by["expense"]
    return {
        "income": income,
        "expenses": expense,
        "net_profit": income - expense,
        "assets": by["asset"],
        "liabilities": -by["liability"],
        "equity": -by["equity"] + income - expense,
    }

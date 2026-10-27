"""Fiscal submission service: idempotent, retryable, reconcilable, audited, redacted."""

from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from audit.service import record
from core.exceptions import ConflictError
from fiscal.models import FiscalAttempt, FiscalDocument, FiscalSettings
from fiscal.providers import (
    CONTRACT_VERSION,
    FiscalProvider,
    ProviderResult,
    ProviderUnavailable,
    get_provider,
)
from sales.models import SalesInvoice
from tenancy.context import AccessContext

TERMINAL = {"FISCALISED", "SIMULATED_ACCEPTED", "REJECTED"}
EFRIS_MATURITY = (
    "SIMULATED_AND_TESTED"  # honest level; see compliance docs. Never raise without evidence.
)


def register_invoice(invoice: SalesInvoice) -> FiscalDocument | None:
    s = FiscalSettings.objects.filter(company_id=invoice.company_id, enabled=True).first()
    if s is None:
        return None
    doc = FiscalDocument.objects.create(
        tenant_id=invoice.tenant_id,
        company_id=invoice.company_id,
        invoice=invoice,
        provider=s.provider,
        simulated=not get_provider(s.provider).authoritative,
        submission_ref=uuid.uuid4().hex,
        captured_at=timezone.now(),
    )
    SalesInvoice.objects.filter(id=invoice.id).update(fiscal_status="PENDING_FISCALISATION")
    invoice.fiscal_status = "PENDING_FISCALISATION"
    return doc


def build_payload(inv: SalesInvoice) -> dict[str, Any]:
    return {
        "contract": CONTRACT_VERSION,
        "number": inv.number,
        "date": str(inv.date),
        "seller_tin": inv.company.tin,
        "buyer": {"tin": inv.customer.tin, "id": inv.customer.nin_or_brn} if inv.customer else None,
        "lines": [
            {
                "sku": ln.product.sku,
                "qty": str(ln.qty),
                "unit_price": str(ln.unit_price),
                "tax_rate": str(ln.tax_rate),
                "net": str(ln.net),
                "tax": str(ln.tax),
            }
            for ln in inv.lines.select_related("product")
        ],
        "totals": {"net": str(inv.subtotal), "tax": str(inv.tax_total), "gross": str(inv.total)},
    }


def _summary(inv: SalesInvoice, payload: dict[str, Any]) -> dict[str, Any]:
    """Redacted: no taxpayer identifiers."""
    return {
        "contract": payload["contract"],
        "number": inv.number,
        "gross": payload["totals"]["gross"],
        "lines": len(payload["lines"]),
        "has_buyer": payload["buyer"] is not None,
    }


def _apply(
    doc: FiscalDocument, provider: FiscalProvider, res: ProviderResult, max_attempts: int
) -> str:
    if res.outcome == "accepted" and res.fdn:
        doc.status = "FISCALISED" if provider.authoritative else "SIMULATED_ACCEPTED"
        doc.fdn, doc.verification_code, doc.last_error_code = res.fdn, res.verification_code, ""
        doc.next_attempt_at = None
    elif res.outcome == "rejected":
        doc.status, doc.last_error_code, doc.next_attempt_at = "REJECTED", res.error_code, None
    else:  # retryable or malformed: never mark accepted on an unreadable answer
        doc.last_error_code = res.error_code or "UNKNOWN"
        if doc.attempts >= max_attempts:
            doc.status, doc.next_attempt_at = "NEEDS_ATTENTION", None
        else:
            doc.status = "FAILED_RETRYABLE"
            doc.next_attempt_at = timezone.now() + timedelta(
                seconds=min(2**doc.attempts * 30, 6 * 3600)
            )
    return doc.status


@transaction.atomic
def submit_document(
    ctx: AccessContext | None,
    *,
    doc_id: uuid.UUID,
    provider: FiscalProvider | None = None,
    actor_id: Any = None,
) -> FiscalDocument:
    doc = (
        FiscalDocument.objects.select_for_update(of=("self",))
        .select_related("invoice__company", "invoice__customer")
        .filter(id=doc_id)
        .first()
    )
    if doc is None:
        raise ValidationError("Unknown fiscal document.")
    if ctx is not None:
        ctx.require("fiscal.submit", doc.company_id, doc.invoice.branch_id)
        actor_id = ctx.user_id
    if doc.status in TERMINAL:
        return doc  # idempotent: never resubmit a finished document
    settings = FiscalSettings.objects.get(company_id=doc.company_id)
    provider = provider or get_provider(doc.provider)
    inv = doc.invoice
    payload = build_payload(inv)
    corr = uuid.uuid4().hex
    doc.attempts += 1
    doc.status = "SUBMITTED"
    try:
        res = provider.submit(payload, doc.submission_ref, corr)
    except ProviderUnavailable as e:
        res = ProviderResult("retryable", error_code="UNAVAILABLE", raw={"error": type(e).__name__})
    except NotImplementedError as e:
        res = ProviderResult("retryable", error_code="NOT_CONFIGURED", raw={"error": str(e)[:80]})
    final = _apply(doc, provider, res, settings.max_attempts)
    doc.save()
    SalesInvoice.objects.filter(id=inv.id).update(fiscal_status=final)
    FiscalAttempt.objects.create(
        tenant_id=doc.tenant_id,
        document=doc,
        correlation_id=corr,
        outcome=res.outcome,
        error_code=res.error_code,
        request_summary=_summary(inv, payload),
        response_summary={k: v for k, v in res.raw.items() if k != "buyer"},
        actor_id=actor_id,
    )
    record(
        action="fiscal.submit",
        outcome="success" if final in {"FISCALISED", "SIMULATED_ACCEPTED"} else "failed",
        tenant_id=doc.tenant_id,
        company_id=doc.company_id,
        actor_id=actor_id,
        object_type="FiscalDocument",
        object_id=doc.id,
        metadata={
            "status": final,
            "simulated": doc.simulated,
            "attempt": doc.attempts,
            "correlation_id": corr,
        },
        durable=final not in {"FISCALISED", "SIMULATED_ACCEPTED"},
    )
    return doc


@transaction.atomic
def reconcile_document(
    ctx: AccessContext | None, *, doc_id: uuid.UUID, provider: FiscalProvider | None = None
) -> FiscalDocument:
    """Resolve unknown outcomes (e.g. timeout after provider commit) by asking the provider."""
    doc = (
        FiscalDocument.objects.select_for_update(of=("self",))
        .select_related("invoice")
        .filter(id=doc_id)
        .first()
    )
    if doc is None:
        raise ValidationError("Unknown fiscal document.")
    if ctx is not None:
        ctx.require("fiscal.submit", doc.company_id, doc.invoice.branch_id)
    if doc.status in TERMINAL:
        raise ConflictError("Document already has a final fiscal status.", "already_final")
    provider = provider or get_provider(doc.provider)
    res = provider.query(doc.submission_ref, uuid.uuid4().hex)
    if res is not None and res.outcome == "accepted":
        _apply(doc, provider, res, 0)
        doc.save()
        SalesInvoice.objects.filter(id=doc.invoice_id).update(fiscal_status=doc.status)
        record(
            action="fiscal.reconcile",
            tenant_id=doc.tenant_id,
            company_id=doc.company_id,
            actor_id=getattr(ctx, "user_id", None),
            object_type="FiscalDocument",
            object_id=doc.id,
            metadata={"status": doc.status, "simulated": doc.simulated},
        )
    return doc


def overdue_offline(company_id: uuid.UUID) -> list[FiscalDocument]:
    """Unsent documents past the configured offline window (none configured = EF-006 open)."""
    s = FiscalSettings.objects.filter(company_id=company_id).first()
    if s is None or s.offline_window_hours is None:
        return []
    cutoff = timezone.now() - timedelta(hours=s.offline_window_hours)
    return list(
        FiscalDocument.objects.filter(company_id=company_id, captured_at__lt=cutoff).exclude(
            status__in=TERMINAL
        )
    )

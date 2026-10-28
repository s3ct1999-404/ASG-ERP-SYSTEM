"""EFRIS/fiscalisation. Internal documents are separate from external fiscal acceptance.

FISCALISED means a REAL authoritative provider confirmed it. A simulator can only ever yield
SIMULATED_ACCEPTED. See docs/compliance/uganda/efris-requirements.md for maturity.
"""

from __future__ import annotations

from django.db import models
from django.db.models import Q

from sales.models import SalesInvoice
from tenancy.models import Company, TenantOwned

DOC_STATES = [
    "PENDING_FISCALISATION",
    "SUBMITTED",
    "FISCALISED",
    "SIMULATED_ACCEPTED",
    "REJECTED",
    "FAILED_RETRYABLE",
    "NEEDS_ATTENTION",
]


class FiscalSettings(TenantOwned):
    company = models.OneToOneField(Company, on_delete=models.PROTECT, related_name="+")
    enabled = models.BooleanField(default=False)
    provider = models.CharField(max_length=20, default="simulator")  # simulator | ura_s2s
    environment = models.CharField(
        max_length=12, default="simulated"
    )  # simulated | sandbox | production
    # Unverified (EF-006): left empty until URA's current offline limit is confirmed per channel.
    offline_window_hours = models.IntegerField(null=True, blank=True)
    max_attempts = models.IntegerField(default=8)


class FiscalDocument(TenantOwned):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="+")
    invoice = models.ForeignKey(SalesInvoice, on_delete=models.PROTECT, related_name="fiscal_docs")
    doc_type = models.CharField(max_length=12, default="invoice")  # invoice | credit_note
    status = models.CharField(max_length=24, default="PENDING_FISCALISATION")
    provider = models.CharField(max_length=20)
    simulated = models.BooleanField(default=True)
    submission_ref = models.CharField(
        max_length=64
    )  # stable per document: provider-side dedupe key
    attempts = models.IntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    captured_at = models.DateTimeField()
    fdn = models.CharField("fiscal document number", max_length=64, blank=True)
    verification_code = models.CharField(max_length=64, blank=True)
    last_error_code = models.CharField(max_length=40, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["invoice", "doc_type"], name="uq_fiscal_doc"),
            models.CheckConstraint(condition=Q(status__in=DOC_STATES), name="ck_fiscal_doc_status"),
            # a document can only be FISCALISED if it was NOT produced by a simulator
            models.CheckConstraint(
                condition=~Q(status="FISCALISED", simulated=True),
                name="ck_fiscalised_never_simulated",
            ),
        ]


class FiscalAttempt(TenantOwned):
    """Immutable log of every submission attempt. Request/response are redacted summaries only."""

    document = models.ForeignKey(
        FiscalDocument, on_delete=models.PROTECT, related_name="attempt_log"
    )
    correlation_id = models.CharField(max_length=64)
    outcome = models.CharField(max_length=20)  # accepted | rejected | retryable | malformed | error
    error_code = models.CharField(max_length=40, blank=True)
    request_summary = models.JSONField(default=dict)
    response_summary = models.JSONField(default=dict)
    actor_id = models.UUIDField(null=True, blank=True)

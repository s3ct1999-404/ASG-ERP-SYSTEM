from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q

from tenancy.models import Branch, Company, TenantOwned

ACCOUNT_TYPES = ["asset", "liability", "equity", "income", "expense"]


class Account(TenantOwned):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="+")
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=150)
    type = models.CharField(max_length=10)
    requires_review = models.BooleanField(
        default=True
    )  # D-008: starter chart needs accountant review
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["company", "code"], name="uq_account_code"),
            models.CheckConstraint(condition=Q(type__in=ACCOUNT_TYPES), name="ck_account_type"),
        ]


class PostingRule(TenantOwned):
    """Maps a business event key (e.g. 'sales_revenue') to an account, per company."""

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="+")
    key = models.CharField(max_length=40)
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="+")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["company", "key"], name="uq_postingrule")]


class FiscalPeriod(TenantOwned):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="+")
    year = models.IntegerField()
    month = models.IntegerField()
    status = models.CharField(max_length=10, default="open")  # open | closed

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["company", "year", "month"], name="uq_period"),
            models.CheckConstraint(
                condition=Q(month__gte=1, month__lte=12), name="ck_period_month"
            ),
        ]


class JournalEntry(TenantOwned):
    """Immutable once written (DB trigger). Corrections = a new reversing entry."""

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="+")
    branch = models.ForeignKey(
        Branch, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    number = models.CharField(max_length=30)
    date = models.DateField()
    memo = models.CharField(max_length=300, blank=True)
    source_type = models.CharField(max_length=30, blank=True)
    source_id = models.CharField(max_length=64, blank=True)
    reverses = models.OneToOneField(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="reversed_by"
    )
    posted_by = models.UUIDField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["company", "number"], name="uq_journal_number")
        ]


class JournalLine(TenantOwned):
    entry = models.ForeignKey(JournalEntry, on_delete=models.PROTECT, related_name="lines")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="+")
    debit = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(debit__gte=0, credit__gte=0)
                & (Q(debit=0) | Q(credit=0))
                & ~Q(debit=0, credit=0),
                name="ck_line_one_sided_positive",
            )
        ]


class DocumentSequence(TenantOwned):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="+")
    key = models.CharField(max_length=30)
    next_value = models.IntegerField(default=1)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["company", "key"], name="uq_docseq")]


_ = settings

from __future__ import annotations

from django.db import models
from django.db.models import Q

from masterdata.models import Partner, Product, TaxCode, Warehouse
from tenancy.models import Branch, Company, TenantOwned

FISCAL_STATES = [
    "NOT_REQUIRED",
    "PENDING_FISCALISATION",
    "SUBMITTED",
    "FISCALISED",
    "SIMULATED_ACCEPTED",
    "REJECTED",
    "FAILED_RETRYABLE",
    "NEEDS_ATTENTION",
]


class SalesInvoice(TenantOwned):
    """Internal document. Fiscal state is separate (see fiscal app) and starts NOT fiscalised."""

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="+")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="+")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="+")
    customer = models.ForeignKey(
        Partner, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    number = models.CharField(max_length=30)
    channel = models.CharField(max_length=10, default="sales")  # sales | pos
    status = models.CharField(max_length=10, default="issued")  # issued | paid | reversed
    date = models.DateField()
    subtotal = models.DecimalField(max_digits=20, decimal_places=2)
    tax_total = models.DecimalField(max_digits=20, decimal_places=2)
    total = models.DecimalField(max_digits=20, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    fiscal_status = models.CharField(max_length=24, default="NOT_REQUIRED")
    operation_id = models.CharField(max_length=100)  # client idempotency key (offline-safe)
    request_hash = models.CharField(max_length=64)
    journal_entry_id = models.UUIDField(null=True, blank=True)
    created_by = models.UUIDField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["company", "number"], name="uq_invoice_number"),
            models.UniqueConstraint(fields=["tenant", "operation_id"], name="uq_invoice_operation"),
            models.CheckConstraint(
                condition=Q(fiscal_status__in=FISCAL_STATES), name="ck_invoice_fiscal"
            ),
            models.CheckConstraint(
                condition=Q(amount_paid__lte=models.F("total")), name="ck_no_overpay"
            ),
        ]


class InvoiceLine(TenantOwned):
    invoice = models.ForeignKey(SalesInvoice, on_delete=models.PROTECT, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="+")
    tax_code = models.ForeignKey(TaxCode, null=True, on_delete=models.PROTECT, related_name="+")
    qty = models.DecimalField(max_digits=18, decimal_places=4)
    unit_price = models.DecimalField(max_digits=20, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=6, decimal_places=4)  # snapshot at sale time
    net = models.DecimalField(max_digits=20, decimal_places=2)
    tax = models.DecimalField(max_digits=20, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=20, decimal_places=4, default=0)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(qty__gt=0), name="ck_line_qty_positive")]


class Payment(TenantOwned):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="+")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="+")
    invoice = models.ForeignKey(SalesInvoice, on_delete=models.PROTECT, related_name="payments")
    method = models.CharField(max_length=20)  # cash | mobile_money | card | bank_transfer
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    idempotency_key = models.CharField(max_length=100)
    request_hash = models.CharField(max_length=64)
    journal_entry_id = models.UUIDField(null=True, blank=True)
    created_by = models.UUIDField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tenant", "idempotency_key"], name="uq_payment_idem"),
            models.CheckConstraint(condition=Q(amount__gt=0), name="ck_payment_positive"),
            models.CheckConstraint(
                condition=Q(method__in=["cash", "mobile_money", "card", "bank_transfer"]),
                name="ck_payment_method",
            ),
        ]

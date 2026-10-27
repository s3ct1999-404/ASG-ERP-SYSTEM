"""Master data. All tables tenant-owned (RLS) and company-scoped."""

from __future__ import annotations

from decimal import Decimal

from django.db import models
from django.db.models import Q

from tenancy.models import Branch, Company, TenantOwned


class UnitOfMeasure(TenantOwned):
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=50)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "code"], name="uq_uom_code")]


class TaxCode(TenantOwned):
    """Effective-dated and user-configured. NO rate is hard-coded (Blueprint §6.1, ASG-015)."""

    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="+")
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=6, decimal_places=4)  # 0.1800 = 18%
    is_exempt = models.BooleanField(default=False)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    source_note = models.CharField(max_length=300, blank=True)  # link to compliance record

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(rate__gte=0, rate__lte=1), name="ck_tax_rate_range"),
        ]


class Partner(TenantOwned):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="+")
    kind = models.CharField(max_length=10)  # customer | supplier
    name = models.CharField(max_length=200)
    tin = models.CharField(max_length=20, blank=True)
    nin_or_brn = models.CharField(max_length=30, blank=True)  # buyer identifiers EFRIS may need
    phone = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(kind__in=["customer", "supplier"]), name="ck_partner_kind"
            )
        ]


class Product(TenantOwned):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="+")
    sku = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    uom = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, related_name="+")
    tax_code = models.ForeignKey(
        TaxCode, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    sale_price = models.DecimalField(
        max_digits=20, decimal_places=2, default=Decimal("0")
    )  # tax-exclusive
    is_service = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["company", "sku"], name="uq_product_sku"),
            models.CheckConstraint(condition=Q(sale_price__gte=0), name="ck_product_price"),
        ]


class Warehouse(TenantOwned):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="+")
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name="+")
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["company", "code"], name="uq_warehouse_code")
        ]

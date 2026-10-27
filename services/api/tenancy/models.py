"""Tenant / company / branch / membership / role model (ADR-0003, data dictionary).

Every tenant-owned table carries ``tenant_id`` and has an RLS policy (migration 0002).
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    status = models.CharField(max_length=20, default="active")
    created_at = models.DateTimeField(auto_now_add=True)


class TenantOwned(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Company(TenantOwned):
    name = models.CharField(max_length=200)
    base_currency = models.CharField(max_length=3, default="UGX")
    tin = models.CharField("Tax Identification Number", max_length=20, blank=True)
    vat_registered = models.BooleanField(default=False)
    allow_negative_stock = models.BooleanField(default=False)  # D-009
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "name"], name="uq_company_name")]


class Branch(TenantOwned):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="branches")
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["company", "code"], name="uq_branch_code")]


class Role(TenantOwned):
    name = models.CharField(max_length=100)
    permissions = models.JSONField(default=list)  # list of codes from tenancy.permissions
    is_system = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "name"], name="uq_role_name")]


class Membership(TenantOwned):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    status = models.CharField(max_length=20, default="active")  # active | suspended

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tenant", "user"], name="uq_membership")]


class RoleAssignment(TenantOwned):
    """A role granted at a scope: tenant-wide (no company/branch), company, or branch."""

    membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name="assignments")
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="+")
    company = models.ForeignKey(
        Company, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    branch = models.ForeignKey(
        Branch, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(branch__isnull=True) | Q(company__isnull=False),
                name="ck_assignment_branch_requires_company",
            ),
            models.UniqueConstraint(
                fields=["membership", "role", "company", "branch"],
                name="uq_assignment",
                nulls_distinct=False,
            ),
        ]

"""Tenancy use-cases. Callers pass an AccessContext; every write is audited."""

from __future__ import annotations

import uuid
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from audit.service import record
from core.exceptions import ConflictError
from identity.models import User
from tenancy.context import AccessContext, system_mode
from tenancy.models import Branch, Company, Membership, Role, RoleAssignment, Tenant
from tenancy.permissions import PERMISSIONS, SYSTEM_ROLES


@transaction.atomic
def provision_tenant(
    *,
    name: str,
    slug: str,
    owner_email: str,
    owner_password: str,
    company_name: str,
    branch_name: str = "Main",
    branch_code: str = "MAIN",
    actor: User | None = None,
) -> Tenant:
    """Platform-operator action (system mode). Creates tenant, system roles, first company/branch
    and an Owner membership. The operator receives no membership (D-021)."""
    if Tenant.objects.filter(slug=slug).exists():
        raise ConflictError("Tenant slug already exists.")
    tenant = Tenant.objects.create(name=name, slug=slug)
    roles = {
        n: Role.objects.create(tenant=tenant, name=n, permissions=p, is_system=True)
        for n, p in SYSTEM_ROLES.items()
    }
    owner = User.objects.filter(email=owner_email.lower()).first() or User.objects.create_user(
        owner_email, owner_password
    )
    company = Company.objects.create(tenant=tenant, name=company_name)
    Branch.objects.create(tenant=tenant, company=company, name=branch_name, code=branch_code)
    m = Membership.objects.create(tenant=tenant, user=owner)
    RoleAssignment.objects.create(tenant=tenant, membership=m, role=roles["Owner"])
    record(
        action="tenant.provision",
        tenant_id=tenant.id,
        actor_id=getattr(actor, "id", None),
        object_type="Tenant",
        object_id=tenant.id,
    )
    return tenant


def create_company(ctx: AccessContext, *, name: str, **extra: Any) -> Company:
    ctx.require("tenancy.manage_org")  # creating a company is a tenant-wide act
    c = Company.objects.create(tenant_id=ctx.tenant_id, name=name, **extra)
    record(
        action="company.create",
        tenant_id=ctx.tenant_id,
        company_id=c.id,
        actor_id=ctx.user_id,
        object_type="Company",
        object_id=c.id,
    )
    return c


def create_branch(ctx: AccessContext, *, company_id: uuid.UUID, name: str, code: str) -> Branch:
    company = Company.objects.filter(id=company_id).first()  # RLS limits to this tenant
    if company is None:
        raise ValidationError("Unknown company.")
    ctx.require("tenancy.manage_org", company.id)
    b = Branch.objects.create(tenant_id=ctx.tenant_id, company=company, name=name, code=code)
    record(
        action="branch.create",
        tenant_id=ctx.tenant_id,
        company_id=company.id,
        branch_id=b.id,
        actor_id=ctx.user_id,
        object_type="Branch",
        object_id=b.id,
    )
    return b


def create_role(ctx: AccessContext, *, name: str, permissions: list[str]) -> Role:
    ctx.require("tenancy.manage_access")
    unknown = set(permissions) - set(PERMISSIONS)
    if unknown:
        raise ValidationError(f"Unknown permissions: {sorted(unknown)}")
    r = Role.objects.create(
        tenant_id=ctx.tenant_id, name=name, permissions=sorted(set(permissions))
    )
    record(
        action="role.create",
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        object_type="Role",
        object_id=r.id,
    )
    return r


def add_member(
    ctx: AccessContext, *, email: str, full_name: str, initial_password: str
) -> Membership:
    """MVP 'invite': an authorised admin creates/links the login. No email delivery exists yet
    (documented limitation); the admin hands over the temporary password out-of-band."""
    ctx.require("tenancy.manage_access")
    with system_mode():  # users are global; asg_app has no access to that table
        user = User.objects.filter(email=email.lower()).first()
        if user is None:
            user = User.objects.create_user(email, initial_password, full_name=full_name)
    if Membership.objects.filter(tenant_id=ctx.tenant_id, user=user).exists():
        raise ConflictError("User is already a member.")
    m = Membership.objects.create(tenant_id=ctx.tenant_id, user=user)
    record(
        action="membership.create",
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        object_type="Membership",
        object_id=m.id,
    )
    return m


def assign_role(
    ctx: AccessContext,
    *,
    membership_id: uuid.UUID,
    role_id: uuid.UUID,
    company_id: uuid.UUID | None = None,
    branch_id: uuid.UUID | None = None,
) -> RoleAssignment:
    membership = Membership.objects.filter(id=membership_id).first()
    role = Role.objects.filter(id=role_id).first()
    if membership is None or role is None:
        raise ValidationError("Unknown membership or role.")
    company = Company.objects.filter(id=company_id).first() if company_id else None
    branch = Branch.objects.filter(id=branch_id).first() if branch_id else None
    if (company_id and company is None) or (branch_id and branch is None):
        raise ValidationError("Unknown company or branch.")
    if branch is not None:
        if company is not None and branch.company_id != company.id:
            raise ValidationError("Branch does not belong to the company.")
        company = branch.company
    # D-022: assigner must hold manage_access over the target scope (tenant-wide for tenant-wide).
    ctx.require(
        "tenancy.manage_access", company.id if company else None, branch.id if branch else None
    )
    # No privilege escalation: cannot grant a permission one does not hold over that scope.
    for perm in role.permissions:
        if not ctx.can(perm, company.id if company else None, branch.id if branch else None):
            record(
                action="authz.escalation_blocked",
                outcome="denied",
                tenant_id=ctx.tenant_id,
                actor_id=ctx.user_id,
                metadata={"permission": perm},
                durable=True,
            )
            raise PermissionDenied("Cannot grant permissions you do not hold for that scope.")
    a, created = RoleAssignment.objects.get_or_create(
        tenant_id=ctx.tenant_id, membership=membership, role=role, company=company, branch=branch
    )
    if created:
        record(
            action="role.assign",
            tenant_id=ctx.tenant_id,
            company_id=getattr(company, "id", None),
            branch_id=getattr(branch, "id", None),
            actor_id=ctx.user_id,
            object_type="RoleAssignment",
            object_id=a.id,
        )
    return a

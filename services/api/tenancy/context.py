"""Tenant mode (RLS) and server-side scope evaluation.

``tenant_mode`` switches the transaction to the non-bypass role ``asg_app`` and binds
``app.tenant_id`` so Postgres itself refuses cross-tenant rows. ``AccessContext`` decides
company/branch scope. Deny by default everywhere.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from django.core.exceptions import PermissionDenied
from django.db import DatabaseError, connection, transaction
from django.db.models import Q, QuerySet

from tenancy.models import Branch, Membership, RoleAssignment
from tenancy.rls import APP_ROLE


def enter_tenant(tenant_id: uuid.UUID | str) -> None:
    """Must run inside a transaction (SET LOCAL is transaction-scoped)."""
    uuid.UUID(str(tenant_id))  # validates; never interpolate unvalidated text
    with connection.cursor() as cur:
        cur.execute(f"SET LOCAL ROLE {APP_ROLE}")
        cur.execute("SELECT set_config('app.tenant_id', %s, true)", [str(tenant_id)])


def leave_tenant() -> None:
    try:
        with connection.cursor() as cur:
            cur.execute("RESET ROLE")
            cur.execute("SELECT set_config('app.tenant_id', '', true)")
    except DatabaseError:  # aborted transaction: SET LOCAL is reverted by the rollback anyway
        pass


@contextmanager
def tenant_mode(tenant_id: uuid.UUID | str) -> Iterator[None]:
    with transaction.atomic():
        enter_tenant(tenant_id)
        try:
            yield
        finally:
            leave_tenant()


@contextmanager
def system_mode() -> Iterator[None]:
    """Briefly step out of tenant mode for the few privileged steps that touch global tables
    (users). Restores the previous tenant binding afterwards. Keep usages tiny and audited."""
    with connection.cursor() as cur:
        cur.execute("SELECT nullif(current_setting('app.tenant_id', true), '')")
        bound = cur.fetchone()[0]
        cur.execute("RESET ROLE")
    try:
        yield
    finally:
        if bound:
            enter_tenant(bound)


@dataclass(frozen=True)
class Grant:
    permissions: frozenset[str]
    company_id: uuid.UUID | None
    branch_id: uuid.UUID | None


@dataclass
class AccessContext:
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    membership_id: uuid.UUID
    grants: list[Grant] = field(default_factory=list)

    # --- decision -----------------------------------------------------------------
    def _applicable(self, perm: str) -> list[Grant]:
        return [g for g in self.grants if perm in g.permissions]

    def has_any(self, perm: str) -> bool:
        return bool(self._applicable(perm))

    def can(self, perm: str, company_id: Any = None, branch_id: Any = None) -> bool:
        """True if some grant containing ``perm`` covers the target scope.

        Target scope: tenant-wide (both None), a company, or a branch (company must be given
        too). A tenant-wide grant covers everything; a company grant covers that company and
        its branches; a branch grant covers only that branch.
        """
        cid = uuid.UUID(str(company_id)) if company_id else None
        bid = uuid.UUID(str(branch_id)) if branch_id else None
        if bid and not cid:
            return False  # caller must supply the branch's company: refuse to guess
        for g in self._applicable(perm):
            if g.company_id is None:
                return True
            if cid is None:
                continue  # a scoped grant never satisfies a tenant-wide target
            if g.branch_id is None and g.company_id == cid:
                return True
            if g.branch_id is not None and g.branch_id == bid and g.company_id == cid:
                return True
        return False

    def require(self, perm: str, company_id: Any = None, branch_id: Any = None) -> None:
        if not self.can(perm, company_id, branch_id):
            raise PermissionDenied("Not permitted for this scope.")

    def require_branch(self, perm: str, branch: Branch) -> None:
        self.require(perm, branch.company_id, branch.id)

    # --- query filtering ----------------------------------------------------------
    def scope_q(
        self, perm: str, company_field: str = "company_id", branch_field: str | None = "branch_id"
    ) -> Q | None:
        """Q for rows visible under ``perm``. None = everything; a Q matching nothing = none."""
        grants = self._applicable(perm)
        if any(g.company_id is None for g in grants):
            return None
        q = Q(pk__in=[])
        for g in grants:
            if g.branch_id is None:
                q |= Q(**{company_field: g.company_id})
            elif branch_field:
                q |= Q(**{company_field: g.company_id, branch_field: g.branch_id})
        return q

    def filter_scope(
        self,
        qs: QuerySet[Any],
        perm: str,
        company_field: str = "company_id",
        branch_field: str | None = "branch_id",
    ) -> QuerySet[Any]:
        q = self.scope_q(perm, company_field, branch_field)
        return qs if q is None else qs.filter(q)


def build_access(user_id: uuid.UUID, tenant_id: uuid.UUID) -> AccessContext:
    """Resolve the caller's grants in ``tenant_id`` (system mode). Raises PermissionDenied."""
    membership = Membership.objects.filter(
        tenant_id=tenant_id, user_id=user_id, status="active"
    ).first()
    if membership is None:
        raise PermissionDenied("No access to this tenant.")
    grants = [
        Grant(frozenset(a.role.permissions), a.company_id, a.branch_id)
        for a in RoleAssignment.objects.filter(membership=membership).select_related("role")
    ]
    return AccessContext(user_id, tenant_id, membership.id, grants)

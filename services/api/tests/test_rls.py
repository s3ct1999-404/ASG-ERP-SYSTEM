"""ADR-0004: Postgres itself must refuse cross-tenant access, even for buggy application code."""

from __future__ import annotations

import pytest
from django.db import ProgrammingError, connection, transaction

from audit.models import AuditEvent
from audit.service import record
from tenancy.context import tenant_mode
from tenancy.models import Branch, Company, Tenant
from tests.conftest import World


def test_tenant_mode_sees_only_own_rows(world_a: World, world_b: World) -> None:
    with tenant_mode(world_a.tenant.id):
        assert set(Company.objects.values_list("id", flat=True)) == {world_a.company.id}
        assert set(Branch.objects.values_list("id", flat=True)) == {world_a.branch.id}
        assert list(Tenant.objects.values_list("id", flat=True)) == [world_a.tenant.id]


def test_tenant_mode_cannot_insert_into_other_tenant(world_a: World, world_b: World) -> None:
    with pytest.raises(ProgrammingError), tenant_mode(world_a.tenant.id), transaction.atomic():
        Company.objects.create(tenant_id=world_b.tenant.id, name="evil")


def test_tenant_mode_cannot_update_or_delete_other_tenant_rows(
    world_a: World, world_b: World
) -> None:
    with tenant_mode(world_a.tenant.id):
        assert Company.objects.filter(id=world_b.company.id).update(name="pwned") == 0
        assert Company.objects.filter(id=world_b.company.id).delete()[0] == 0
    world_b.company.refresh_from_db()
    assert world_b.company.name == f"Co {world_b.tenant.slug}"


def test_no_tenant_bound_means_no_rows(world_a: World) -> None:
    with transaction.atomic():
        with connection.cursor() as cur:
            cur.execute("SET LOCAL ROLE asg_app")
        try:
            assert Company.objects.count() == 0
        finally:
            with connection.cursor() as cur:
                cur.execute("RESET ROLE")


def test_app_role_cannot_bypass_rls(db: object) -> None:
    with connection.cursor() as cur:
        cur.execute(
            "SELECT rolsuper, rolbypassrls, rolcanlogin FROM pg_roles WHERE rolname='asg_app'"
        )
        assert cur.fetchone() == (False, False, False)


def test_app_role_cannot_read_password_hashes(world_a: World) -> None:
    with (
        pytest.raises(ProgrammingError),
        tenant_mode(world_a.tenant.id),
        connection.cursor() as cur,
    ):
        cur.execute("SELECT password FROM identity_user")


def test_audit_is_append_only_even_for_owner(world_a: World) -> None:
    ev = record(action="x.test", tenant_id=world_a.tenant.id)
    from django.db import InternalError

    with pytest.raises((InternalError, ProgrammingError, Exception)) as e, transaction.atomic():
        AuditEvent.objects.filter(id=ev.id).update(action="tampered")
    assert "append-only" in str(e.value)
    with pytest.raises(Exception) as e2, transaction.atomic():
        AuditEvent.objects.filter(id=ev.id).delete()
    assert "append-only" in str(e2.value)


def test_audit_isolated_per_tenant(world_a: World, world_b: World) -> None:
    record(action="only.b", tenant_id=world_b.tenant.id)
    with tenant_mode(world_a.tenant.id):
        assert not AuditEvent.objects.filter(action="only.b").exists()


def test_identity_tables_have_rls_and_app_role_sees_only_current_tenant_members(
    world_a: World, world_b: World
) -> None:
    with connection.cursor() as cur:
        cur.execute(
            "SELECT relname, relrowsecurity FROM pg_class WHERE relname IN "
            "('identity_user','identity_authtoken','tenancy_company','audit_auditevent')"
        )
        assert all(enabled for _, enabled in cur.fetchall())
    with tenant_mode(world_a.tenant.id), connection.cursor() as cur:
        cur.execute("SELECT email FROM identity_user")
        assert [r[0] for r in cur.fetchall()] == [world_a.owner.email]
    with (
        pytest.raises(ProgrammingError),
        tenant_mode(world_a.tenant.id),
        connection.cursor() as cur,
    ):
        cur.execute("SELECT key_hash FROM identity_authtoken")

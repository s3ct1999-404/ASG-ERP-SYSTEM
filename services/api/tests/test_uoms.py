"""Units of measure are listable per tenant, permission-checked, and never cross tenants."""

from __future__ import annotations

from rest_framework.test import APIClient

from tests.conftest import World, as_tenant, login


def test_owner_lists_own_tenant_uoms(owner_a: APIClient) -> None:
    r = owner_a.get("/api/v1/uoms/")
    assert r.status_code == 200
    codes = [u["code"] for u in r.json()]
    assert "PCS" in codes
    assert set(r.json()[0]) == {"id", "code", "name"}


def test_uoms_do_not_leak_across_tenants(world_a: World, world_b: World) -> None:
    a = as_tenant(login(world_a.owner.email), world_a.tenant)
    b = as_tenant(login(world_b.owner.email), world_b.tenant)
    ids_a = {u["id"] for u in a.get("/api/v1/uoms/").json()}
    ids_b = {u["id"] for u in b.get("/api/v1/uoms/").json()}
    assert ids_a and ids_b and ids_a.isdisjoint(ids_b)


def test_owner_cannot_read_other_tenants_uoms_by_header_swap(
    world_a: World, world_b: World
) -> None:
    c = as_tenant(login(world_a.owner.email), world_b.tenant)  # a's token, b's tenant id
    assert c.get("/api/v1/uoms/").status_code == 403


def test_uoms_require_authentication(db: object) -> None:
    assert APIClient().get("/api/v1/uoms/").status_code in (401, 403)

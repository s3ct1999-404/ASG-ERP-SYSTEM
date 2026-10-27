from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from rest_framework.test import APIClient

from identity.models import User
from tenancy.context import build_access
from tenancy.models import Branch, Company, Role, Tenant
from tenancy.services import provision_tenant

PW = "correct-horse-battery-1"


def pytest_collection_modifyitems(items: list[Any]) -> None:
    """Durable audit writes use a second connection alias; allow it wherever the DB is used."""
    for item in items:
        if "db" in item.fixturenames or "transactional_db" in item.fixturenames:
            item.add_marker(pytest.mark.django_db(databases="__all__"))


def audit_events(**filters: Any) -> list[Any]:
    """Audit rows from both the in-transaction and the durable connection."""
    from audit.models import AuditEvent

    rows = list(AuditEvent.objects.filter(**filters))
    rows += list(AuditEvent.objects.using("audit").filter(**filters))
    return rows


@dataclass
class World:
    tenant: Tenant
    company: Company
    branch: Branch
    owner: User


def make_world(slug: str) -> World:
    t = provision_tenant(
        name=f"Tenant {slug}",
        slug=slug,
        owner_email=f"owner@{slug}.test",
        owner_password=PW,
        company_name=f"Co {slug}",
    )
    c = Company.objects.get(tenant=t)
    b = Branch.objects.get(company=c)
    return World(t, c, b, User.objects.get(email=f"owner@{slug}.test"))


@pytest.fixture
def world_a(db: Any) -> World:
    return make_world("alpha")


@pytest.fixture
def world_b(db: Any) -> World:
    return make_world("bravo")


def login(email: str, password: str = PW) -> APIClient:
    c = APIClient()
    r = c.post("/api/v1/auth/login/", {"email": email, "password": password}, format="json")
    assert r.status_code == 200, r.content
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['token']}")
    return c


def as_tenant(client: APIClient, tenant: Tenant) -> APIClient:
    client.credentials(
        HTTP_AUTHORIZATION=client._credentials["HTTP_AUTHORIZATION"],
        HTTP_X_TENANT_ID=str(tenant.id),
    )
    return client


@pytest.fixture
def owner_a(world_a: World) -> APIClient:
    return as_tenant(login(world_a.owner.email), world_a.tenant)


@pytest.fixture
def access_a(world_a: World) -> Any:
    return build_access(world_a.owner.id, world_a.tenant.id)


def role(tenant: Tenant, name: str) -> Role:
    return Role.objects.get(tenant=tenant, name=name)

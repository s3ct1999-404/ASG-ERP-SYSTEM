from __future__ import annotations

from rest_framework.test import APIClient

from identity.models import AuthToken, User
from tenancy.models import Branch, Company, Membership, RoleAssignment
from tests.conftest import PW, World, as_tenant, audit_events, login, role


def _member(owner: APIClient, world: World, email: str) -> str:
    r = owner.post(
        "/api/v1/memberships/",
        {"email": email, "full_name": "X", "initial_password": PW},
        format="json",
    )
    assert r.status_code == 201, r.content
    return str(r.json()["id"])


def _assign(owner: APIClient, mid: str, role_id: object, **scope: object) -> int:
    body = {"role": str(role_id), **{k: str(v) for k, v in scope.items()}}
    return owner.post(f"/api/v1/memberships/{mid}/assignments/", body, format="json").status_code


# --- authentication ---------------------------------------------------------------
def test_login_bad_password_and_unknown_user_look_identical(world_a: World) -> None:
    c = APIClient()
    r1 = c.post(
        "/api/v1/auth/login/", {"email": world_a.owner.email, "password": "nope"}, format="json"
    )
    r2 = c.post("/api/v1/auth/login/", {"email": "ghost@x.test", "password": "nope"}, format="json")
    assert r1.status_code == r2.status_code == 401
    assert r1.json() == r2.json()


def test_token_is_stored_hashed_and_logout_revokes(world_a: World) -> None:
    c = login(world_a.owner.email)
    raw = c._credentials["HTTP_AUTHORIZATION"].split()[1]
    assert not AuthToken.objects.filter(key_hash=raw).exists()
    assert c.get("/api/v1/me/").status_code == 200
    assert c.post("/api/v1/auth/logout/").status_code == 204
    assert c.get("/api/v1/me/").status_code == 401


def test_endpoints_require_authentication(world_a: World) -> None:
    c = APIClient(HTTP_X_TENANT_ID=str(world_a.tenant.id))
    for url in ("/api/v1/companies/", "/api/v1/roles/", "/api/v1/memberships/", "/api/v1/me/"):
        assert c.get(url).status_code == 401


def test_production_password_hasher_is_argon2_and_passwords_not_plaintext(world_a: World) -> None:
    from config import settings

    assert settings.PASSWORD_HASHERS[0].endswith("Argon2PasswordHasher")
    assert PW not in User.objects.get(id=world_a.owner.id).password


# --- tenant isolation ---------------------------------------------------------------
def test_owner_sees_only_own_tenant(owner_a: APIClient, world_a: World, world_b: World) -> None:
    ids = {c["id"] for c in owner_a.get("/api/v1/companies/").json()}
    assert ids == {str(world_a.company.id)}


def test_user_cannot_use_a_tenant_they_do_not_belong_to(owner_a: APIClient, world_b: World) -> None:
    as_tenant(owner_a, world_b.tenant)
    for url in ("/api/v1/companies/", "/api/v1/branches/", "/api/v1/memberships/"):
        assert owner_a.get(url).status_code == 403


def test_missing_or_garbage_tenant_header_denied(world_a: World) -> None:
    c = login(world_a.owner.email)
    assert c.get("/api/v1/companies/").status_code == 403
    c.credentials(
        HTTP_AUTHORIZATION=c._credentials["HTTP_AUTHORIZATION"], HTTP_X_TENANT_ID="not-a-uuid"
    )
    assert c.get("/api/v1/companies/").status_code == 403


def test_idor_other_tenant_ids_in_body_rejected(
    owner_a: APIClient, world_a: World, world_b: World
) -> None:
    r = owner_a.post(
        "/api/v1/branches/",
        {"company": str(world_b.company.id), "name": "x", "code": "X"},
        format="json",
    )
    assert r.status_code in (400, 403, 422)
    assert not Branch.objects.filter(company=world_b.company, code="X").exists()
    mid = Membership.objects.get(tenant=world_a.tenant).id
    r = owner_a.post(
        f"/api/v1/memberships/{mid}/assignments/",
        {"role": str(role(world_b.tenant, "Owner").id)},
        format="json",
    )
    assert r.status_code in (400, 403, 422)


def test_same_person_in_two_tenants_gets_separate_scopes(world_a: World, world_b: World) -> None:
    ob = as_tenant(login(world_b.owner.email), world_b.tenant)
    mid = _member(ob, world_b, world_a.owner.email)  # owner of A becomes Viewer in B
    assert _assign(ob, mid, role(world_b.tenant, "Viewer").id) == 201
    me = as_tenant(login(world_a.owner.email), world_b.tenant)
    assert me.get("/api/v1/companies/").status_code == 200
    assert (
        me.post("/api/v1/companies/", {"name": "nope"}, format="json").status_code == 403
    )  # Viewer in B


# --- platform operator ----------------------------------------------------------------
def test_only_operator_can_provision_and_gets_no_tenant_data(db: object) -> None:
    op = User.objects.create_user("op@asg.test", PW, is_platform_operator=True)
    plain = User.objects.create_user("plain@asg.test", PW)
    body = {
        "name": "T",
        "slug": "t1",
        "owner_email": "o@t1.test",
        "owner_password": PW,
        "company_name": "C",
    }
    assert (
        login(plain.email).post("/api/v1/platform/tenants/", body, format="json").status_code == 403
    )
    c = login(op.email)
    assert c.post("/api/v1/platform/tenants/", body, format="json").status_code == 201
    tid = c.get("/api/v1/me/").json()["tenants"]
    assert tid == []  # operator holds no membership (D-021)
    from tenancy.models import Tenant

    as_tenant(c, Tenant.objects.get(slug="t1"))
    assert c.get("/api/v1/companies/").status_code == 403


# --- branch / company scope -----------------------------------------------------------
def test_branch_scoped_user_cannot_touch_other_branch(owner_a: APIClient, world_a: World) -> None:
    b2 = Branch.objects.create(
        tenant=world_a.tenant, company=world_a.company, name="Second", code="B2"
    )
    mid = _member(owner_a, world_a, "cashier@alpha.test")
    assert (
        _assign(
            owner_a,
            mid,
            role(world_a.tenant, "Cashier").id,
            company=world_a.company.id,
            branch=world_a.branch.id,
        )
        == 201
    )
    c = as_tenant(login("cashier@alpha.test"), world_a.tenant)
    # Cashier has no tenancy.read at all -> denied outright
    assert c.get("/api/v1/branches/").status_code == 403
    # a Viewer scoped to branch 1 sees only branch 1
    mid2 = _member(owner_a, world_a, "viewer@alpha.test")
    assert (
        _assign(
            owner_a,
            mid2,
            role(world_a.tenant, "Viewer").id,
            company=world_a.company.id,
            branch=world_a.branch.id,
        )
        == 201
    )
    v = as_tenant(login("viewer@alpha.test"), world_a.tenant)
    ids = {b["id"] for b in v.get("/api/v1/branches/").json()}
    assert ids == {str(world_a.branch.id)} and str(b2.id) not in ids


def test_scoped_user_cannot_grant_tenant_wide_or_unheld_permissions(
    owner_a: APIClient, world_a: World
) -> None:
    mid = _member(owner_a, world_a, "mgr@alpha.test")
    # give the manager manage_access ONLY on branch 1 via a custom role
    r = owner_a.post(
        "/api/v1/roles/",
        {"name": "AccessAdmin", "permissions": ["tenancy.manage_access", "tenancy.read"]},
        format="json",
    )
    assert r.status_code == 201
    assert (
        _assign(owner_a, mid, r.json()["id"], company=world_a.company.id, branch=world_a.branch.id)
        == 201
    )
    mgr = as_tenant(login("mgr@alpha.test"), world_a.tenant)
    victim = _member(owner_a, world_a, "v2@alpha.test")
    owner_role = role(world_a.tenant, "Owner").id
    # tenant-wide grant -> denied (D-022)
    assert _assign(mgr, victim, owner_role) == 403
    # branch grant of Owner role (contains perms the manager lacks) -> escalation blocked
    assert (
        _assign(mgr, victim, owner_role, company=world_a.company.id, branch=world_a.branch.id)
        == 403
    )
    # granting something the manager does hold over that branch is fine
    assert (
        _assign(mgr, victim, r.json()["id"], company=world_a.company.id, branch=world_a.branch.id)
        == 201
    )
    assert audit_events(action="authz.escalation_blocked")
    assert not RoleAssignment.objects.filter(membership_id=victim, role_id=owner_role).exists()


def test_branch_must_belong_to_company(owner_a: APIClient, world_a: World, world_b: World) -> None:
    c2 = Company.objects.create(tenant=world_a.tenant, name="Second Co")
    mid = _member(owner_a, world_a, "z@alpha.test")
    assert (
        _assign(
            owner_a, mid, role(world_a.tenant, "Viewer").id, company=c2.id, branch=world_a.branch.id
        )
        == 422
    )


def test_unknown_permission_in_custom_role_rejected(owner_a: APIClient) -> None:
    r = owner_a.post(
        "/api/v1/roles/", {"name": "Bad", "permissions": ["root.everything"]}, format="json"
    )
    assert r.status_code == 422


def test_writes_are_audited_without_secrets(owner_a: APIClient, world_a: World) -> None:
    owner_a.post(
        "/api/v1/memberships/",
        {"email": "a@a.test", "full_name": "A", "initial_password": PW},
        format="json",
    )
    ev = audit_events(action="membership.create", tenant_id=world_a.tenant.id)
    assert len(ev) == 1 and ev[0].actor_id == world_a.owner.id and PW not in str(ev[0].metadata)


def test_permission_denial_is_audited_durably(owner_a: APIClient, world_a: World) -> None:
    mid = _member(owner_a, world_a, "view@alpha.test")
    assert _assign(owner_a, mid, role(world_a.tenant, "Viewer").id) == 201
    v = as_tenant(login("view@alpha.test"), world_a.tenant)
    assert v.post("/api/v1/companies/", {"name": "x"}, format="json").status_code == 403
    denied = audit_events(tenant_id=world_a.tenant.id, action="authz.denied")
    assert len(denied) == 1 and denied[0].metadata["permission"] == "tenancy.manage_org"


def test_non_member_is_denied_without_leaking_tenant_existence(
    world_a: World, world_b: World
) -> None:
    c = as_tenant(login(world_a.owner.email), world_b.tenant)
    real = c.get("/api/v1/companies/")
    import uuid

    c.credentials(
        HTTP_AUTHORIZATION=c._credentials["HTTP_AUTHORIZATION"], HTTP_X_TENANT_ID=str(uuid.uuid4())
    )
    fake = c.get("/api/v1/companies/")
    assert real.status_code == fake.status_code == 403 and real.json() == fake.json()

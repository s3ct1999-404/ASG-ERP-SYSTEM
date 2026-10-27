"""End-to-end over HTTP: master data, stock, sale/POS, payment, ledger, reports, audit."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from rest_framework.test import APIClient

from tenancy.models import Branch, Company
from tests.conftest import PW, World, as_tenant, audit_events, login, role

D = Decimal


def _setup(owner: APIClient, w: World) -> dict[str, str]:
    Company.objects.filter(id=w.company.id).update(vat_registered=True)
    cid = str(w.company.id)
    uom = owner.get("/api/v1/warehouses/").json()  # warehouse seeded at provisioning
    wh = uom[0]["id"]
    tax = owner.post(
        "/api/v1/tax-codes/",
        {
            "company": cid,
            "name": "Std (test data)",
            "rate": "0.1800",
            "effective_from": "2026-01-01",
        },
        format="json",
    )
    assert tax.status_code == 201, tax.content
    from masterdata.models import UnitOfMeasure
    from tenancy.context import tenant_mode

    with tenant_mode(w.tenant.id):
        uom_id = str(UnitOfMeasure.objects.get().id)
    p = owner.post(
        "/api/v1/products/",
        {
            "company": cid,
            "sku": "SUG1",
            "name": "Sugar 1kg",
            "uom": uom_id,
            "tax_code": tax.json()["id"],
            "sale_price": "5000.00",
        },
        format="json",
    )
    assert p.status_code == 201, p.content
    cu = owner.post(
        "/api/v1/partners/", {"company": cid, "kind": "customer", "name": "Acme Ltd"}, format="json"
    )
    assert cu.status_code == 201
    return {
        "wh": wh,
        "prod": p.json()["id"],
        "cust": cu.json()["id"],
        "branch": str(w.branch.id),
        "cid": cid,
    }


def test_full_business_flow_over_http(owner_a: APIClient, world_a: World) -> None:
    ids = _setup(owner_a, world_a)
    r = owner_a.post(
        "/api/v1/inventory/receipts/",
        {
            "warehouse": ids["wh"],
            "product": ids["prod"],
            "qty": "20",
            "unit_cost": "3000",
            "idempotency_key": "grn-1",
        },
        format="json",
    )
    assert r.status_code == 201, r.content
    again = owner_a.post(
        "/api/v1/inventory/receipts/",
        {
            "warehouse": ids["wh"],
            "product": ids["prod"],
            "qty": "20",
            "unit_cost": "3000",
            "idempotency_key": "grn-1",
        },
        format="json",
    )
    assert again.status_code == 200 and again.json()["replayed"] is True
    inv = owner_a.post(
        "/api/v1/sales/invoices/",
        {
            "branch": ids["branch"],
            "warehouse": ids["wh"],
            "customer": ids["cust"],
            "operation_id": "web-1",
            "lines": [{"product_id": ids["prod"], "qty": "4"}],
        },
        format="json",
    )
    assert inv.status_code == 201, inv.content
    body = inv.json()
    assert (D(body["subtotal"]), D(body["tax_total"]), D(body["total"])) == (
        D("20000.00"),
        D("3600.00"),
        D("23600.00"),
    )
    pay = owner_a.post(
        f"/api/v1/sales/invoices/{body['id']}/payments/",
        {"method": "bank_transfer", "amount": "23600", "idempotency_key": "pay-1"},
        format="json",
    )
    assert pay.status_code == 201, pay.content
    stock = owner_a.get("/api/v1/inventory/stock/").json()
    assert [(s["sku"], D(s["qty"])) for s in stock] == [("SUG1", D(16))]
    tb = {
        r["code"]: D(str(r["balance"]))
        for r in owner_a.get(f"/api/v1/accounting/{ids['cid']}/trial-balance/").json()
    }
    assert sum(tb.values()) == 0 and tb["1020"] == D("23600.00") and tb["1100"] == 0
    st = owner_a.get(f"/api/v1/accounting/{ids['cid']}/statements/").json()
    assert D(str(st["net_profit"])) == D("8000.00")  # 20,000 revenue - 12,000 COGS
    assert owner_a.get("/api/v1/sales/invoices/").json()[0]["status"] == "paid"
    assert audit_events(action="invoice.issue", tenant_id=world_a.tenant.id)


def test_pos_sale_over_http_and_replay(owner_a: APIClient, world_a: World) -> None:
    ids = _setup(owner_a, world_a)
    owner_a.post(
        "/api/v1/inventory/receipts/",
        {
            "warehouse": ids["wh"],
            "product": ids["prod"],
            "qty": "5",
            "unit_cost": "3000",
            "idempotency_key": "g",
        },
        format="json",
    )
    sale = {
        "branch": ids["branch"],
        "warehouse": ids["wh"],
        "operation_id": "till-1-0001",
        "lines": [{"product_id": ids["prod"], "qty": "1"}],
        "tenders": [{"method": "cash", "amount": "5900"}],
    }
    a = owner_a.post("/api/v1/pos/sales/", sale, format="json")
    b = owner_a.post("/api/v1/pos/sales/", sale, format="json")
    assert (a.status_code, b.status_code) == (201, 200) and a.json()["id"] == b.json()["id"]
    assert a.json()["status"] == "paid" and a.json()["fiscal_status"] in {
        "NOT_REQUIRED",
        "PENDING_FISCALISATION",
    }
    assert D(owner_a.get("/api/v1/inventory/stock/").json()[0]["qty"]) == D(4)
    mismatch = dict(sale, lines=[{"product_id": ids["prod"], "qty": "2"}])
    assert owner_a.post("/api/v1/pos/sales/", mismatch, format="json").status_code == 409


def test_business_errors_are_clean_http_codes(owner_a: APIClient, world_a: World) -> None:
    ids = _setup(owner_a, world_a)
    r = owner_a.post(
        "/api/v1/sales/invoices/",
        {
            "branch": ids["branch"],
            "warehouse": ids["wh"],
            "operation_id": "x",
            "lines": [{"product_id": ids["prod"], "qty": "1"}],
        },
        format="json",
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "insufficient_stock"
    r = owner_a.post(
        "/api/v1/sales/invoices/",
        {"branch": ids["branch"], "warehouse": ids["wh"], "operation_id": "y", "lines": []},
        format="json",
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "no_lines"


def test_other_tenant_cannot_see_or_use_ids(
    owner_a: APIClient, world_a: World, world_b: World
) -> None:
    ids = _setup(owner_a, world_a)
    ob = as_tenant(login(world_b.owner.email), world_b.tenant)
    assert ob.get("/api/v1/inventory/stock/").json() == []
    r = ob.post(
        "/api/v1/inventory/receipts/",
        {
            "warehouse": ids["wh"],
            "product": ids["prod"],
            "qty": "1",
            "unit_cost": "1",
            "idempotency_key": "evil",
        },
        format="json",
    )
    assert r.status_code in (400, 403, 422)
    r = ob.post(
        "/api/v1/sales/invoices/",
        {
            "branch": ids["branch"],
            "warehouse": ids["wh"],
            "operation_id": "evil",
            "lines": [{"product_id": ids["prod"], "qty": "1"}],
        },
        format="json",
    )
    assert r.status_code in (400, 403, 422)
    assert ob.get(f"/api/v1/accounting/{ids['cid']}/trial-balance/").status_code in (403, 404)


def test_cashier_scope_over_http(owner_a: APIClient, world_a: World) -> None:
    ids = _setup(owner_a, world_a)
    owner_a.post(
        "/api/v1/inventory/receipts/",
        {
            "warehouse": ids["wh"],
            "product": ids["prod"],
            "qty": "5",
            "unit_cost": "3000",
            "idempotency_key": "g",
        },
        format="json",
    )
    m = owner_a.post(
        "/api/v1/memberships/", {"email": "till@alpha.test", "initial_password": PW}, format="json"
    ).json()["id"]
    from masterdata.models import Warehouse

    b2 = Branch.objects.create(tenant=world_a.tenant, company=world_a.company, name="B2", code="B2")
    wh2 = Warehouse.objects.create(
        tenant=world_a.tenant, company=world_a.company, branch=b2, code="W2", name="W2"
    )
    assert (
        owner_a.post(
            f"/api/v1/memberships/{m}/assignments/",
            {
                "role": str(role(world_a.tenant, "Cashier").id),
                "company": ids["cid"],
                "branch": ids["branch"],
            },
            format="json",
        ).status_code
        == 201
    )
    till = as_tenant(login("till@alpha.test"), world_a.tenant)
    ok = till.post(
        "/api/v1/pos/sales/",
        {
            "branch": ids["branch"],
            "warehouse": ids["wh"],
            "operation_id": "t1",
            "lines": [{"product_id": ids["prod"], "qty": "1"}],
            "tenders": [{"method": "cash", "amount": "5900"}],
        },
        format="json",
    )
    assert ok.status_code == 201, ok.content
    bad = till.post(
        "/api/v1/pos/sales/",
        {
            "branch": str(b2.id),
            "warehouse": str(wh2.id),
            "operation_id": "t2",
            "lines": [{"product_id": ids["prod"], "qty": "1"}],
            "tenders": [],
        },
        format="json",
    )
    assert (
        bad.status_code == 403
    )  # genuine scope denial: branch exists, cashier is not assigned to it
    assert (
        till.post(
            "/api/v1/inventory/adjustments/",
            {
                "warehouse": ids["wh"],
                "product": ids["prod"],
                "qty_delta": "-1",
                "reason": "x",
                "idempotency_key": "a",
            },
            format="json",
        ).status_code
        == 403
    )
    assert till.get(f"/api/v1/accounting/{ids['cid']}/trial-balance/").status_code == 403
    _: Any = None

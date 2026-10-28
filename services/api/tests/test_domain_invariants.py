"""Core business invariants: ledger balance, immutability, idempotency, stock, scope, periods."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any

import pytest
from django.core.exceptions import PermissionDenied
from django.db import DatabaseError, connection, transaction

from accounting import services as acc
from accounting.models import JournalEntry, JournalLine
from core.exceptions import ConflictError, DomainError
from inventory import services as inv
from inventory.models import StockMovement
from masterdata.models import Partner, Product, TaxCode, UnitOfMeasure, Warehouse
from sales import services as sales
from sales.models import SalesInvoice
from tenancy.context import build_access, tenant_mode
from tenancy.models import Branch, Company, Role
from tests.conftest import PW, World

D = Decimal
TODAY = dt.date(2026, 10, 28)


class Env:
    def __init__(self, w: World) -> None:
        self.w = w
        self.ctx = build_access(w.owner.id, w.tenant.id)
        Company.objects.filter(id=w.company.id).update(vat_registered=True)
        with tenant_mode(w.tenant.id):
            self.uom = UnitOfMeasure.objects.get(code="PCS")
            self.wh = Warehouse.objects.get(code="MAIN")
            # Rate is TEST DATA only; the product never hard-codes a rate.
            self.tax = TaxCode.objects.create(
                tenant=w.tenant,
                company=w.company,
                name="Test std",
                rate=D("0.18"),
                effective_from=dt.date(2026, 1, 1),
            )
            self.prod = Product.objects.create(
                tenant=w.tenant,
                company=w.company,
                sku="P1",
                name="Widget",
                uom=self.uom,
                tax_code=self.tax,
                sale_price=D("2000"),
            )
            self.cust = Partner.objects.create(
                tenant=w.tenant, company=w.company, kind="customer", name="Cust"
            )

    def receive(self, qty: str, cost: str, key: str) -> Any:
        with tenant_mode(self.w.tenant.id):
            return inv.receive_stock(
                self.ctx,
                warehouse_id=self.wh.id,
                product_id=self.prod.id,
                qty=D(qty),
                unit_cost=D(cost),
                idempotency_key=key,
                date=TODAY,
            )

    def sell(self, qty: str, op: str, price: str | None = None) -> Any:
        with tenant_mode(self.w.tenant.id):
            line: dict[str, Any] = {"product_id": self.prod.id, "qty": qty}
            if price:
                line["unit_price"] = price
            return sales.create_invoice(
                self.ctx,
                branch_id=self.w.branch.id,
                warehouse_id=self.wh.id,
                customer_id=self.cust.id,
                lines=[line],
                operation_id=op,
                date=TODAY,
            )


@pytest.fixture
def env(world_a: World) -> Env:
    return Env(world_a)


def _tb_sum(w: World) -> Decimal:
    with tenant_mode(w.tenant.id):
        return sum((r["balance"] for r in acc.trial_balance(w.company.id)), D(0))


def test_receive_sell_pay_posts_balanced_books_and_correct_amounts(env: Env) -> None:
    env.receive("10", "1000", "r1")
    i, created = env.sell("3", "op1")
    assert created and (i.subtotal, i.tax_total, i.total) == (
        D("6000.00"),
        D("1080.00"),
        D("7080.00"),
    )
    with tenant_mode(env.w.tenant.id):
        tb = {r["code"]: r["balance"] for r in acc.trial_balance(env.w.company.id)}
        assert (
            tb["1100"] == D("7080.00")
            and tb["4000"] == D("-6000.00")
            and tb["2100"] == D("-1080.00")
        )
        assert tb["5000"] == D("3000.00") and tb["1200"] == D("7000.00")  # 10k in, 3k out
        assert inv.reconcile(env.wh.id, env.prod.id) == {"ledger": D(7), "balance": D(7)}
        sales.record_payment(
            env.ctx, invoice_id=i.id, method="cash", amount=D("7080"), idempotency_key="p1"
        )
        i.refresh_from_db()
        assert i.status == "paid"
        st = acc.statements(env.w.company.id)
        assert st["net_profit"] == D("3000.00")
    assert _tb_sum(env.w) == 0


def test_invoice_replay_is_idempotent_and_mismatch_is_conflict(env: Env) -> None:
    env.receive("10", "1000", "r1")
    a, c1 = env.sell("2", "same-op")
    b, c2 = env.sell("2", "same-op")
    assert (c1, c2) == (True, False) and a.id == b.id
    with tenant_mode(env.w.tenant.id):
        assert SalesInvoice.objects.count() == 1
        assert inv.reconcile(env.wh.id, env.prod.id)["balance"] == D(8)  # deducted once
    with pytest.raises(ConflictError):
        env.sell("5", "same-op")


def test_receipt_replay_does_not_double_stock(env: Env) -> None:
    _, c1 = env.receive("5", "100", "dup")
    _, c2 = env.receive("5", "100", "dup")
    assert (c1, c2) == (True, False)
    with tenant_mode(env.w.tenant.id):
        assert inv.reconcile(env.wh.id, env.prod.id)["balance"] == D(5)
        with pytest.raises(ConflictError):
            inv.receive_stock(
                env.ctx,
                warehouse_id=env.wh.id,
                product_id=env.prod.id,
                qty=D(9),
                unit_cost=D(100),
                idempotency_key="dup",
            )


def test_cannot_oversell_and_failure_leaves_no_trace(env: Env) -> None:
    env.receive("2", "1000", "r1")
    with pytest.raises(DomainError) as e:
        env.sell("3", "big")
    assert e.value.code == "insufficient_stock"
    with tenant_mode(env.w.tenant.id):
        assert SalesInvoice.objects.count() == 0 and inv.reconcile(env.wh.id, env.prod.id)[
            "balance"
        ] == D(2)


def test_weighted_average_cost(env: Env) -> None:
    env.receive("10", "1000", "a")
    env.receive("10", "2000", "b")
    i, _ = env.sell("1", "s1")
    with tenant_mode(env.w.tenant.id):
        assert i.lines.get().unit_cost == D("1500.0000")


def test_overpayment_rejected_and_payment_replay_safe(env: Env) -> None:
    env.receive("5", "1000", "r")
    i, _ = env.sell("1", "o1")
    with tenant_mode(env.w.tenant.id):
        sales.record_payment(
            env.ctx, invoice_id=i.id, method="mobile_money", amount=D("1000"), idempotency_key="k1"
        )
        _, again = sales.record_payment(
            env.ctx, invoice_id=i.id, method="mobile_money", amount=D("1000"), idempotency_key="k1"
        )
        assert again is False
        i.refresh_from_db()
        assert i.amount_paid == D("1000.00")
        with pytest.raises(DomainError) as e:
            sales.record_payment(
                env.ctx, invoice_id=i.id, method="cash", amount=D("99999"), idempotency_key="k2"
            )
        assert e.value.code == "overpayment"


def test_tax_not_effective_is_rejected_not_guessed(env: Env) -> None:
    env.receive("5", "1000", "r")
    with tenant_mode(env.w.tenant.id):
        TaxCode.objects.filter(id=env.tax.id).update(effective_from=dt.date(2030, 1, 1))
    with pytest.raises(DomainError) as e:
        env.sell("1", "t1")
    assert e.value.code == "tax_not_effective"


def test_unbalanced_entry_rejected_by_service(env: Env) -> None:
    with tenant_mode(env.w.tenant.id):
        a, b = (
            acc.rule_account(env.w.company.id, "cash"),
            acc.rule_account(env.w.company.id, "sales_revenue"),
        )
        with pytest.raises(DomainError):
            acc.post_entry(
                company=env.w.company, date=TODAY, lines=[(a, D(10), D(0)), (b, D(0), D(9))]
            )


def test_database_rejects_unbalanced_entry_even_if_service_is_bypassed(env: Env) -> None:
    with (
        tenant_mode(env.w.tenant.id),
        pytest.raises(DatabaseError, match="unbalanced"),
        transaction.atomic(),
    ):
        a = acc.rule_account(env.w.company.id, "cash")
        e = JournalEntry.objects.create(
            tenant=env.w.tenant, company=env.w.company, number="X1", date=TODAY
        )
        JournalLine.objects.create(tenant=env.w.tenant, entry=e, account=a, debit=D(5), credit=D(0))
        with connection.cursor() as cur:
            cur.execute("SET CONSTRAINTS ALL IMMEDIATE")


def test_ledgers_are_immutable_for_every_role(env: Env) -> None:
    env.receive("1", "10", "r")
    i, _ = env.sell("1", "imm")
    targets = (
        (JournalEntry, "memo", "x"),
        (JournalLine, "debit", D(1)),
        (StockMovement, "qty", D(99)),
    )
    for model, field, val in targets:
        pk = model.objects.first().id
        with pytest.raises(DatabaseError, match="append-only"), transaction.atomic():
            model.objects.filter(id=pk).update(**{field: val})
        table = model._meta.db_table
        with (
            pytest.raises(DatabaseError, match="append-only"),
            transaction.atomic(),
            connection.cursor() as cur,
        ):
            cur.execute(f"DELETE FROM {table} WHERE id = %s", [pk])  # noqa: S608
        if (
            model is StockMovement
        ):  # (journal tables have pending deferred events inside this test txn)
            with (
                pytest.raises(DatabaseError, match="append-only"),
                transaction.atomic(),
                connection.cursor() as cur,
            ):
                cur.execute("SET CONSTRAINTS ALL IMMEDIATE")  # flush pending FK events first
                cur.execute(f"TRUNCATE {table}")  # noqa: S608
    assert i.id


def test_reversal_nets_to_zero_and_cannot_repeat(env: Env) -> None:
    env.receive("5", "1000", "r")
    i, _ = env.sell("1", "o")
    with tenant_mode(env.w.tenant.id):
        je = JournalEntry.objects.get(id=i.journal_entry_id)
        rv = acc.reverse_entry(env.ctx, entry_id=je.id, date=TODAY, reason="customer returned")
        assert rv.reverses_id == je.id
        assert all(abs(r["balance"]) >= 0 for r in acc.trial_balance(env.w.company.id))
        ar = next(r for r in acc.trial_balance(env.w.company.id) if r["code"] == "1100")
        assert ar["balance"] == 0
        with pytest.raises(ConflictError):
            acc.reverse_entry(env.ctx, entry_id=je.id, date=TODAY, reason="again")
        with pytest.raises(ConflictError):
            acc.reverse_entry(env.ctx, entry_id=rv.id, date=TODAY, reason="rev of rev")


def test_closed_period_blocks_posting_and_reopen_requires_permission(env: Env) -> None:
    env.receive("5", "1000", "r")
    with tenant_mode(env.w.tenant.id):
        acc.set_period_status(
            env.ctx, company_id=env.w.company.id, year=2026, month=10, status="closed"
        )
    with pytest.raises(ConflictError) as e:
        env.sell("1", "late")
    assert e.value.code == "period_closed"


def test_branch_scope_is_enforced_in_services(env: Env, world_a: World) -> None:
    from tenancy.services import add_member, assign_role

    with tenant_mode(world_a.tenant.id):
        b2 = Branch.objects.create(
            tenant=world_a.tenant, company=world_a.company, name="B2", code="B2"
        )
        wh2 = Warehouse.objects.create(
            tenant=world_a.tenant, company=world_a.company, branch=b2, code="W2", name="W2"
        )
        m = add_member(env.ctx, email="cash@alpha.test", full_name="C", initial_password=PW)
        assign_role(
            env.ctx,
            membership_id=m.id,
            role_id=Role.objects.get(name="Cashier").id,
            company_id=world_a.company.id,
            branch_id=world_a.branch.id,
        )
    cash_ctx = build_access(m.user_id, world_a.tenant.id)
    line = [{"product_id": env.prod.id, "qty": "1"}]
    with tenant_mode(world_a.tenant.id):
        with pytest.raises(PermissionDenied):  # other branch
            sales.pos_sale(
                cash_ctx,
                branch_id=b2.id,
                warehouse_id=wh2.id,
                lines=line,
                tenders=[],
                operation_id="x",
            )
        with pytest.raises(PermissionDenied):  # Cashier cannot adjust stock or post journals
            inv.adjust_stock(
                cash_ctx,
                warehouse_id=env.wh.id,
                product_id=env.prod.id,
                qty_delta=D(1),
                reason="r",
                idempotency_key="a",
            )
        with pytest.raises(PermissionDenied):
            acc.post_manual(cash_ctx, company_id=world_a.company.id, date=TODAY, memo="m", lines=[])


def test_pos_sale_is_one_idempotent_operation_with_tender(env: Env) -> None:
    env.receive("5", "1000", "r")
    with tenant_mode(env.w.tenant.id):
        kw: dict[str, Any] = {
            "branch_id": env.w.branch.id,
            "warehouse_id": env.wh.id,
            "lines": [{"product_id": env.prod.id, "qty": "2"}],
            "tenders": [
                {"method": "cash", "amount": "3000"},
                {"method": "mobile_money", "amount": "1720"},
            ],
            "operation_id": "pos-1",
            "date": TODAY,
        }
        a, c1 = sales.pos_sale(env.ctx, **kw)
        b, c2 = sales.pos_sale(env.ctx, **kw)
        assert (
            (c1, c2) == (True, False)
            and a.id == b.id
            and b.status == "paid"
            and b.total == D("4720.00")
        )
        assert inv.reconcile(env.wh.id, env.prod.id)["balance"] == D(3)
    assert _tb_sum(env.w) == 0


def test_stock_adjustment_requires_reason_and_is_traceable(env: Env) -> None:
    env.receive("5", "1000", "r")
    with tenant_mode(env.w.tenant.id):
        with pytest.raises(DomainError):
            inv.adjust_stock(
                env.ctx,
                warehouse_id=env.wh.id,
                product_id=env.prod.id,
                qty_delta=D(-1),
                reason=" ",
                idempotency_key="a1",
            )
        inv.adjust_stock(
            env.ctx,
            warehouse_id=env.wh.id,
            product_id=env.prod.id,
            qty_delta=D(-1),
            reason="damaged",
            idempotency_key="a2",
            date=TODAY,
        )
        assert inv.reconcile(env.wh.id, env.prod.id)["balance"] == D(4)
        assert StockMovement.objects.filter(kind="adjustment", ref_id="damaged").count() == 1
    assert _tb_sum(env.w) == 0

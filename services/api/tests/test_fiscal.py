"""EFRIS/fiscal boundary: states, idempotency, retries, reconciliation, honesty about simulation."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from django.core.management import call_command
from django.db import DatabaseError, connection, transaction
from django.utils import timezone
from rest_framework.test import APIClient

from core.exceptions import ConflictError
from fiscal import services
from fiscal.models import FiscalAttempt, FiscalDocument, FiscalSettings
from fiscal.providers import SimulatorProvider, UraS2SProvider
from sales.models import SalesInvoice
from tenancy.context import tenant_mode
from tests.conftest import PW, World, as_tenant, audit_events, login, role
from tests.test_domain_invariants import Env


@pytest.fixture(autouse=True)
def _sim() -> None:
    SimulatorProvider.reset("accept")


@pytest.fixture
def fenv(world_a: World) -> Env:
    e = Env(world_a)
    FiscalSettings.objects.create(tenant=world_a.tenant, company=world_a.company, enabled=True)
    e.receive("50", "1000", "r")
    return e


def _doc(fenv: Env, op: str = "f1") -> FiscalDocument:
    inv, _ = fenv.sell("1", op)
    with tenant_mode(fenv.w.tenant.id):
        return FiscalDocument.objects.get(invoice_id=inv.id)


def _submit(fenv: Env, doc: FiscalDocument) -> FiscalDocument:
    with tenant_mode(fenv.w.tenant.id):
        return services.submit_document(fenv.ctx, doc_id=doc.id)


def test_invoice_is_pending_not_fiscalised_until_provider_responds(fenv: Env) -> None:
    d = _doc(fenv)
    assert d.status == "PENDING_FISCALISATION" and d.simulated is True
    assert SalesInvoice.objects.get(id=d.invoice_id).fiscal_status == "PENDING_FISCALISATION"


def test_simulator_success_is_never_reported_as_real_fiscalisation(fenv: Env) -> None:
    d = _submit(fenv, _doc(fenv))
    assert d.status == "SIMULATED_ACCEPTED" and d.fdn.startswith("SIM-")
    assert SalesInvoice.objects.get(id=d.invoice_id).fiscal_status == "SIMULATED_ACCEPTED"
    assert d.status != "FISCALISED"


def test_database_forbids_fiscalised_status_on_simulated_document(fenv: Env) -> None:
    d = _doc(fenv)
    with pytest.raises(DatabaseError), transaction.atomic():
        FiscalDocument.objects.filter(id=d.id).update(status="FISCALISED")


def test_authoritative_provider_acceptance_is_fiscalised_only_when_not_simulated(fenv: Env) -> None:
    class FakeAuthoritative(SimulatorProvider):
        authoritative = True

    d = _doc(fenv)
    FiscalDocument.objects.filter(id=d.id).update(
        simulated=False
    )  # as a real provider doc would be
    with tenant_mode(fenv.w.tenant.id):
        out = services.submit_document(fenv.ctx, doc_id=d.id, provider=FakeAuthoritative())
    assert out.status == "FISCALISED"


def test_resubmitting_a_finished_document_does_not_call_provider_again(fenv: Env) -> None:
    d = _submit(fenv, _doc(fenv))
    SimulatorProvider.reset("timeout")  # would fail if called
    again = _submit(fenv, d)
    assert again.status == "SIMULATED_ACCEPTED" and again.attempts == 1


def test_rejection_is_terminal_and_recorded(fenv: Env) -> None:
    SimulatorProvider.reset("reject")
    d = _submit(fenv, _doc(fenv))
    assert d.status == "REJECTED" and d.last_error_code == "SIM_REJECT"
    assert SalesInvoice.objects.get(id=d.invoice_id).fiscal_status == "REJECTED"
    assert audit_events(action="fiscal.submit", tenant_id=fenv.w.tenant.id)[0].outcome == "failed"


def test_timeout_is_retryable_then_succeeds_on_retry(fenv: Env) -> None:
    SimulatorProvider.reset("timeout")
    d = _submit(fenv, _doc(fenv))
    assert (
        d.status == "FAILED_RETRYABLE" and d.next_attempt_at and d.last_error_code == "UNAVAILABLE"
    )
    SimulatorProvider.reset("accept")
    assert _submit(fenv, d).status == "SIMULATED_ACCEPTED"
    assert FiscalAttempt.objects.filter(document=d).count() == 2


def test_timeout_after_provider_commit_does_not_double_submit(fenv: Env) -> None:
    SimulatorProvider.reset("timeout_after_commit")
    d = _submit(fenv, _doc(fenv))
    assert d.status == "FAILED_RETRYABLE"
    with tenant_mode(fenv.w.tenant.id):  # reconcile finds the provider-side result
        r = services.reconcile_document(fenv.ctx, doc_id=d.id)
    assert r.status == "SIMULATED_ACCEPTED" and r.fdn
    assert len(SimulatorProvider._committed) == 1  # one fiscal record at the provider


def test_retry_after_commit_timeout_reuses_submission_ref_so_provider_dedupes(fenv: Env) -> None:
    SimulatorProvider.reset("timeout_after_commit")
    d = _submit(fenv, _doc(fenv))
    SimulatorProvider.script = "accept"
    out = _submit(fenv, d)
    assert out.status == "SIMULATED_ACCEPTED" and len(SimulatorProvider._committed) == 1


def test_malformed_response_is_never_treated_as_acceptance(fenv: Env) -> None:
    SimulatorProvider.reset("malformed")
    d = _submit(fenv, _doc(fenv))
    assert d.status == "FAILED_RETRYABLE" and not d.fdn


def test_unconfigured_real_provider_fails_safe_and_stays_unfiscalised(fenv: Env) -> None:
    d = _doc(fenv)
    with tenant_mode(fenv.w.tenant.id):
        out = services.submit_document(fenv.ctx, doc_id=d.id, provider=UraS2SProvider())
    assert (
        out.status == "FAILED_RETRYABLE" and out.last_error_code == "NOT_CONFIGURED" and not out.fdn
    )


def test_gives_up_to_needs_attention_after_max_attempts(fenv: Env) -> None:
    FiscalSettings.objects.update(max_attempts=2)
    SimulatorProvider.reset("timeout")
    d = _submit(fenv, _doc(fenv))
    assert d.status == "FAILED_RETRYABLE"
    assert _submit(fenv, d).status == "NEEDS_ATTENTION"


def test_attempt_log_is_redacted_and_immutable(fenv: Env) -> None:
    from masterdata.models import Partner

    Partner.objects.filter(id=fenv.cust.id).update(tin="1000123456", nin_or_brn="CM9900112233")
    d = _submit(fenv, _doc(fenv))
    a = FiscalAttempt.objects.get(document=d)
    blob = str(a.request_summary) + str(a.response_summary)
    assert (
        "1000123456" not in blob and "CM99" not in blob and a.request_summary["has_buyer"] is True
    )
    with (
        pytest.raises(DatabaseError, match="append-only"),
        transaction.atomic(),
        connection.cursor() as cur,
    ):
        cur.execute("DELETE FROM fiscal_fiscalattempt WHERE id = %s", [a.id])


def test_worker_command_submits_due_documents_once(fenv: Env) -> None:
    _doc(fenv, "w1")
    _doc(fenv, "w2")
    call_command("submit_pending_fiscal")
    call_command("submit_pending_fiscal")  # second run: nothing left, no resubmission
    assert set(FiscalDocument.objects.values_list("status", flat=True)) == {"SIMULATED_ACCEPTED"}
    assert set(FiscalDocument.objects.values_list("attempts", flat=True)) == {1}


def test_offline_window_unconfigured_reports_nothing_and_configured_flags_overdue(
    fenv: Env,
) -> None:
    d = _doc(fenv)
    assert services.overdue_offline(fenv.w.company.id) == []  # EF-006 open: no invented limit
    FiscalSettings.objects.update(offline_window_hours=48)
    FiscalDocument.objects.filter(id=d.id).update(captured_at=timezone.now() - timedelta(hours=49))
    assert [x.id for x in services.overdue_offline(fenv.w.company.id)] == [d.id]


def test_disabled_company_gets_no_fiscal_document(world_a: World) -> None:
    e = Env(world_a)
    e.receive("5", "1000", "r")
    inv, _ = e.sell("1", "nf")
    assert inv.fiscal_status == "NOT_REQUIRED" and not FiscalDocument.objects.exists()


def test_fiscal_api_permissions_and_honest_status(fenv: Env, world_a: World) -> None:
    d = _doc(fenv)
    owner = as_tenant(login(world_a.owner.email), world_a.tenant)
    assert owner.get("/api/v1/fiscal/status/").json()["efris_maturity"] == "SIMULATED_AND_TESTED"
    r = owner.post(f"/api/v1/fiscal/documents/{d.id}/submit/").json()
    assert r["status"] == "SIMULATED_ACCEPTED" and "SIMULATED" in r["label"]
    m = owner.post(
        "/api/v1/memberships/", {"email": "c@alpha.test", "initial_password": PW}, format="json"
    ).json()["id"]
    owner.post(
        f"/api/v1/memberships/{m}/assignments/",
        {"role": str(role(world_a.tenant, "Cashier").id)},
        format="json",
    )
    cashier: APIClient = as_tenant(login("c@alpha.test"), world_a.tenant)
    assert cashier.get("/api/v1/fiscal/documents/").status_code == 200  # Cashier has fiscal.read
    assert cashier.post(f"/api/v1/fiscal/documents/{d.id}/submit/").status_code == 403
    assert cashier.put("/api/v1/fiscal/settings/", {}, format="json").status_code == 403
    bad = owner.put(
        "/api/v1/fiscal/settings/",
        {
            "company": str(world_a.company.id),
            "enabled": True,
            "provider": "ura_s2s",
            "environment": "simulated",
        },
        format="json",
    )
    assert bad.status_code == 422
    _: Any = ConflictError

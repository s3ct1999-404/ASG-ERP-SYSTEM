# ASG ERP — PROGRESS (master ledger)

> Statuses: `NOT STARTED` · `IN PROGRESS` · `BLOCKED` · `IN REVIEW` · `DONE`. `DONE` needs evidence.
> Coverage labels: `WORKING MVP` · `PARTIAL` · `SIMULATED` · `NOT IMPLEMENTED`.
> **Backend/API only so far: there is no usable business UI yet.** Labels below describe the API.

## Header
| Field | Value |
|---|---|
| Last updated | 2026-10-28 |
| Working branch | `feat/mvp-completion` (local, from `main` @ `5ae7d0c`; PR #1 `feat/mvp-platform-core` already merged into `main`) |
| Last code commit | see `git log` on `feat/mvp-completion` |
| Remote | `main` @ `5ae7d0c` (verified via `git ls-remote` 2026-10-29; the uploaded zip was byte-identical to `feat/mvp-platform-core` @ `486d777`). **This session's commits are NOT pushed**: no GitHub credential in the sandbox (genuine human step) |
| Supabase | project `hcpzsprnrhpfnodvzals`, Postgres 17. Applied: identity 0001-0002, tenancy 0001-0002, audit 0001-0002. masterdata 0001-0002, accounting 0001-0002, inventory 0001-0003, sales 0001-0003, fiscal 0001-0002 applied 2026-10-28 and verified (see docs/release/supabase-migration-report.md). Live head = repo head (18/18) |
| EFRIS maturity | **SIMULATED_AND_TESTED** (level 3 of 6). No request ever sent to URA |
| CI | Defined, **never run on GitHub** |

## Verified evidence (local PostgreSQL 16, 2026-10-28)
| Check | Result |
|---|---|
| `pytest` (services/api) | PASS: 80 passed |
| `ruff check` / `ruff format --check` | PASS |
| `mypy --strict` | PASS (103 files) |
| `makemigrations --check` | PASS (no drift) |
| OpenAPI generate+validate, committed copy matches | PASS |
| Supabase behavioural RLS test (rolled back) | PASS: own rows 1, other-tenant updates 0, cross-tenant insert/password read/audit update blocked |
| Web typecheck/lint/format/22 tests/build; npm audit 0 vulns; pip-audit clean; live API smoke 18/18 | PASS (see docs/release/verification-report.md) |
| Docker compose, GitHub CI, Playwright E2E, backup/restore | NOT RUN / BLOCKED (see verification report) |

## Coverage matrix (evidence: tests named in `services/api/tests/`)
| Blueprint app | Label | What exists | Not done |
|---|---|---|---|
| Platform admin / tenancy / identity / RBAC / audit | WORKING MVP (API; UI: sign-in, tenant switch, org view) | provision tenant, companies, branches, roles, scoped assignments, escalation block, RLS, immutable audit, login throttle | UI, email invitations, MFA, password reset |
| Master data | WORKING MVP (API; UI partial) | tax codes (user-entered, effective-dated), partners, products, warehouses, read-only UoM list | categories, UoM write, import |
| Inventory | WORKING MVP (API; UI: balances + idempotent receive) | receipts, adjustments, sale issue, weighted-average cost, no-negative-stock, immutable ledger, reconcile | transfers, counts, lots/serials, reorder |
| Sales | PARTIAL | invoices, payments, idempotent; UI: read-only invoice list with honest fiscal labels | quotations, orders, returns, credit notes |
| POS | PARTIAL | one idempotent sale+tender operation, branch scope | till sessions, cash-up, returns, receipts printing |
| Accounting | PARTIAL | seeded chart (needs review), balanced posting (DB-enforced), reversal, period close, trial balance, statements | AP/purchases, bank reconciliation, manual period reopen UX |
| EFRIS / fiscalisation | SIMULATED | provider contract, status machine, retries, reconcile, worker, redaction, simulator, honest labels | real URA wire format, sandbox, credit notes, cancellations |
| Offline sync | PARTIAL | server-side idempotency on invoices/payments/receipts | client outbox, sync endpoint/status API, conflict UI |
| Reporting | PARTIAL | trial balance, statements | dashboards, exports, scheduled reports |
| App marketplace / lifecycle | NOT IMPLEMENTED | contracts only (ADR/APP_PLATFORM.md) | registry, install state machine |
| HR, Projects/tasks, Documents/approvals, Fleet, Notifications | NOT IMPLEMENTED | none | everything |

## Decisions
D-001..D-024 decided under owner authorisation: `docs/adr/0004-autonomous-mvp-decisions.md`.

## Open risks / defects
- R-1 No GitHub credential: work exists only in the local repo until pushed.
- R-2 RESOLVED 2026-10-28: Supabase matches repo head (18/18), behavioural RLS/invariant test 13/13 PASS.
- R-3 Starter chart, costing and rounding rules **need accountant review** (D-007/008/009).
- R-4 Offline limit for S2S unknown (EF-011); accreditation need unconfirmed (EF-008).
- R-5 No UI; no CI run; no dependency audit run.
- R-6 `system_mode()` lets app code leave RLS for user-table work; RLS is defence in depth, not a sandbox.
- R-7 Members get an admin-set temporary password (no email delivery).

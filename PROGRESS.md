# ASG ERP — PROGRESS (master ledger)

> Statuses: `NOT STARTED` · `IN PROGRESS` · `BLOCKED` · `IN REVIEW` · `DONE`. `DONE` needs evidence.
> Coverage labels: `WORKING MVP` · `PARTIAL` · `SIMULATED` · `NOT IMPLEMENTED`.
> **Backend/API only so far: there is no usable business UI yet.** Labels below describe the API.

## Header
| Field | Value |
|---|---|
| Last updated | 2026-10-28 |
| Working branch | `feat/mvp-platform-core` (local; stacked on `docs/asg-015-uganda-research`) |
| Last code commit | `b9aa5ce` (fiscal). Docs commit follows it; see `git log` |
| Remote | `main` @ `7ff17b7`. **Nothing pushed**: no GitHub credential in the build sandbox (genuine human step) |
| Supabase | project `hcpzsprnrhpfnodvzals`, Postgres 17. Applied: identity 0001-0002, tenancy 0001-0002, audit 0001-0002. **NOT yet applied**: masterdata, accounting, inventory, sales, fiscal (see NEXT_SESSION) |
| EFRIS maturity | **SIMULATED_AND_TESTED** (level 3 of 6). No request ever sent to URA |
| CI | Defined, **never run on GitHub** |

## Verified evidence (local PostgreSQL 16, 2026-10-28)
| Check | Result |
|---|---|
| `pytest` (services/api) | PASS: 76 passed |
| `ruff check` / `ruff format --check` | PASS |
| `mypy --strict` | PASS (102 files) |
| `makemigrations --check` | PASS (no drift) |
| OpenAPI generate+validate, committed copy matches | PASS |
| Supabase behavioural RLS test (rolled back) | PASS: own rows 1, other-tenant updates 0, cross-tenant insert/password read/audit update blocked |
| Web tests/build, docker compose, dependency audit, GitHub CI | NOT RUN this session |

## Coverage matrix (evidence: tests named in `services/api/tests/`)
| Blueprint app | Label | What exists | Not done |
|---|---|---|---|
| Platform admin / tenancy / identity / RBAC / audit | WORKING MVP (API) | provision tenant, companies, branches, roles, scoped assignments, escalation block, RLS, immutable audit, login throttle | UI, email invitations, MFA, password reset |
| Master data | WORKING MVP (API) | tax codes (user-entered, effective-dated), partners, products, warehouses | categories, UoM API, import |
| Inventory | WORKING MVP (API) | receipts, adjustments, sale issue, weighted-average cost, no-negative-stock, immutable ledger, reconcile | transfers, counts, lots/serials, reorder |
| Sales | PARTIAL | invoices, payments, idempotent | quotations, orders, returns, credit notes |
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
- R-2 Supabase is behind the repo (5 apps' migrations unapplied). Run NEXT_SESSION step 2.
- R-3 Starter chart, costing and rounding rules **need accountant review** (D-007/008/009).
- R-4 Offline limit for S2S unknown (EF-011); accreditation need unconfirmed (EF-008).
- R-5 No UI; no CI run; no dependency audit run.
- R-6 `system_mode()` lets app code leave RLS for user-table work; RLS is defence in depth, not a sandbox.
- R-7 Members get an admin-set temporary password (no email delivery).

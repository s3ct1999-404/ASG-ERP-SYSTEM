# ASG ERP — Next Session Handoff

## Last updated: 2026-10-28
## State
Branch `feat/mvp-platform-core` (local). Last code commit `b9aa5ce`. 76 tests pass locally; lint/types/migration-drift/OpenAPI all pass. **Nothing pushed** (no credential). See PROGRESS.md for the matrix.

## Restart (the sandbox resets: nothing persists except what is in the repo/bundle)
1. Recreate env: `apt-get update && apt-get install -y postgresql`, `pg_ctlcluster 16 main start`, create role `asg` (superuser, password via `DB_PASSWORD`) and db `asg_erp`; `python3 -m venv .venv && pip install -r services/api/requirements/dev.txt`.
2. `cd services/api && export DB_PASSWORD=... SECRET_KEY=x && python -m pytest -q` (expect 76 passed). If you see mass OperationalError, PostgreSQL is simply down.

## Exact next actions, in order
1. ~~Apply pending migrations~~ DONE 2026-10-28 (docs/release/supabase-migration-report.md). Any NEW migration: `sqlmigrate`, strip BEGIN/COMMIT, append the `django_migrations` insert, apply via MCP, verify ledger vs `showmigrations --plan`, then `get_advisors`.
2. Offline: `SyncOperation` model + `POST /sync/operations/` (batch, per-op status pending/synced/conflict/failed/needs_attention) wrapping pos_sale/receive_stock/payment, with tests for duplicate, out-of-order, revoked access.
3. App lifecycle state machine (registry, install/disable/uninstall, entitlements) with tests.
4. Smallest honest cores: HR, projects/tasks, documents/approvals, fleet, notifications; extend reporting.
5. Web UI shell wired to the API; Docker compose run; dependency audit; GitHub CI when a credential exists.
6. Packaging: README-FIRST.md, handover, coverage matrix, ZIP, checksum, fresh-extract verification.

## Human-only items
- Provide a GitHub credential (or push the bundle yourself) so commits reach the remote.
- URA: test-portal registration, interface spec, accreditation answers (EF-008..EF-011).
- Accountant review of chart/costing/rounding (D-007/008/009).

## Never
Do not claim FISCALISED without a real authoritative response. Do not hard-code tax rates. Do not commit secrets.

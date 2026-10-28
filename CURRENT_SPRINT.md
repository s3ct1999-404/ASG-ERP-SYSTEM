# Current sprint

## Active task
Workstream E (web UI) slice 1 is done; continue with offline sync API (B), app lifecycle (C), remaining app cores (D), packaging.

## Done this session (evidence: docs/release/verification-report.md)
- A: all 12 pending migrations applied to Supabase and verified (18/18, RLS 28/28, behavioural 13/13).
- E: shadcn/ui + Tailwind v4 web foundation (ADR-0005); sign-in, tenant switch, organisation, products, stock receive, invoices; EFRIS banner; 22 web tests; live API smoke 18/18.
- Backend: `GET /uoms/` (+4 tests, OpenAPI regenerated). G: npm audit 0, pip-audit clean.

## Acceptance for the next bounded task (offline sync API, Blueprint 7)
1. `SyncOperation` model + `POST /sync/operations/` (batch): per-op status pending/syncing/synced/conflict/failed/needs_attention with documented transitions.
2. Re-authorises each op; same key + same payload replays; same key + different payload is rejected; dependency ordering enforced.
3. Tests: duplicate, timeout-after-commit replay, out-of-order, revoked membership, token expiry, invalid tenant scope.

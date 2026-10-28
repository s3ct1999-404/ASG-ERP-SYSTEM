# Known limitations (as of 2026-10-29)

Honest residual gaps. Severity: H/M/L.

| # | Area | Limitation | Sev | Next action |
|---|---|---|---|---|
| 1 | Delivery | Nothing from this session is pushed: the build sandbox has no GitHub credential. Work is committed locally on `feat/mvp-completion`; a git bundle is provided. | H | Owner pushes the bundle or supplies a credential. |
| 2 | UI | Web UI covers sign-in, tenant switch, organisation (read), products (list/create), stock (balances/receive), invoices (read). No UI yet for sales creation, POS/till, accounting, reports, HR, projects, documents, fleet, notifications, marketplace. | H | See PROGRESS.md next actions. |
| 3 | UI | Token is in memory only: a page reload signs the user out (deliberate security trade-off, ADR-0005). | L | Revisit with httpOnly-cookie sessions if desired. |
| 4 | UI tests | Component tests use a mocked `fetch`. A live HTTP smoke replays the UI call sequence against the real server (18/18 PASS), but there is **no browser E2E (Playwright) yet**. | M | Add Playwright journey. |
| 5 | API contract | `/inventory/stock/` returns decimals as JSON numbers; other endpoints return strings. Float precision risk for money/quantities. | M | Serialise Decimals as strings in `inventory` views; update OpenAPI and tests. |
| 6 | API contract | Validation errors return `error.message` as a nested object (field errors) but a string for domain errors. Client flattens it; the contract should be uniform. | L | Normalise in `core/exceptions.py`. |
| 7 | Masterdata | `GET /uoms/` is read-only; no create/update of units of measure. | L | Add write endpoint when needed. |
| 8 | Offline | No sync API or client outbox yet (server-side idempotency only). | H | Workstream B. |
| 9 | Platform | App registry/marketplace lifecycle not implemented (contracts only). | H | Workstream C. |
| 10 | Apps | HR, projects/tasks, documents/approvals, fleet, notifications not started. | H | Workstream D. |
| 11 | EFRIS | Simulator only (maturity 3 of 6). No request has ever reached URA. | H | URA registration/spec/credentials (human). |
| 12 | Accounting | Starter chart, costing and rounding need qualified accountant review; they are **not** professionally approved. | M | D-007/008/009. |
| 13 | CI | GitHub Actions never run (needs push). Docker Compose not run. | M | After push; Docker-capable host. |
| 14 | Ops | Backup/restore rehearsal NOT RUN. Supabase performance advisors not reviewed. | M | Run on a staging project. |
| 15 | Supabase | `identity_authtoken` and `django_migrations` have RLS enabled with no policy (deny-all by design); advisor reports them as INFO. | L | None (intentional). |

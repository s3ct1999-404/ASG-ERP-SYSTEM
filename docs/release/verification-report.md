# Verification report

Environment: sandbox Ubuntu 24, PostgreSQL 16 local, Python venv from `services/api/requirements/dev.txt`, Node per `apps/web` lockfile. Date: 2026-10-29. Branch `feat/mvp-completion` (local, from `main` @ `5ae7d0c`). Results are for this exact tree.

| Check | Command | Result |
|---|---|---|
| Backend tests | `cd services/api && SECRET_KEY=x python -m pytest -q` | PASS: 80 passed (76 baseline + 4 new `test_uoms.py`) |
| Backend lint/format/types | `ruff check .`, `ruff format --check .`, `mypy .` | PASS / PASS / PASS (103 files) |
| OpenAPI | `manage.py spectacular --validate` + committed copy test | PASS (0 errors; 44 pre-existing schema warnings from `responses={200: None}` stubs) |
| Fresh DB from migrations | `manage.py migrate` on empty DB | PASS: 18/18 applied |
| Web typecheck | `npm run typecheck` | PASS |
| Web lint | `npm run lint` | PASS (after fixing 2 genuine react-hooks errors) |
| Web format | `npm run format:check` | PASS |
| Web tests | `npm test` | PASS: 22 passed (mocked fetch; component-level) |
| Web production build | `npm run build` | PASS |
| Live API contract smoke | `/tmp/smoke.py` vs real server, synthetic tenant | PASS: 18/18 (login, tenant header enforcement, /uoms/, product create, duplicate rejected, idempotent receipt retry keeps balance 10, fiscal honesty, logout revokes token). Found 2 issues (limitations #5, #6); #6 fixed in the client. |
| Supabase migration + schema | see `supabase-migration-report.md` | PASS: ledger 18/18 = repo head; 28/28 tables RLS; behavioural test 13/13 (rolled back) |
| Supabase security advisors | `get_advisors security` | PASS: 2 INFO (intentional deny-all tables), no WARN/ERROR |
| `npm audit` | `npm audit` | PASS: 0 vulnerabilities (fixed transitive `undici` in lockfile; it was dev-only via jsdom) |
| `pip-audit` | `pip-audit -r requirements/{base,dev}.txt` | PASS: none found |
| GitHub Actions CI | n/a | **BLOCKED**: nothing pushed (no credential) |
| Docker Compose | n/a | **NOT RUN** (no Docker in sandbox) |
| Browser E2E (Playwright) | n/a | **NOT RUN** |
| Secret scan | `python3 scripts/check_secrets.py` (+ grep for local test credentials in staged files) | PASS: no likely secrets |
| Backup/restore rehearsal | n/a | **NOT RUN** |

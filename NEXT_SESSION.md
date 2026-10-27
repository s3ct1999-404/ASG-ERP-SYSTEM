# ASG ERP — Next Session Handoff

## Last updated
2026-10-27

## Start here (read in this order)
1. `ASG_ERP_AGENT_INSTRUCTIONS.md`  2. `CLAUDE.md`  3. `PROGRESS.md`  4. `CURRENT_SPRINT.md`  5. this file  6. active requirement + relevant ADRs (`docs/adr/`)
Then `git status`, `git log --oneline -12`, and **verify this handoff against the actual repo** before editing. PostgreSQL must be running for API tests (it stops between sandbox steps — start it first).

## Current milestone
Stage 1/2: architecture decisions drafted; engineering scaffold built. **Business features are deliberately not started** — they are gated on owner decisions below.

## Current task
ASG-015 — Uganda compliance research (**IN PROGRESS**, first pass done). Status of everything else: `PROGRESS.md`. Summary: DONE: ASG-001 · IN REVIEW: ASG-002, ASG-003, ASG-004, ASG-014 · BLOCKED: ASG-012 · NOT STARTED: ASG-005…011, 013, 016, 017.

## What exists (all on local branches, nothing pushed)
Linear stack, each branch built on the previous (`main` @ `7ff17b7` is unchanged):
1. `chore/bootstrap-foundation` — continuity docs, baseline docs, ADR-0001/0002 (accepted)
2. `feat/asg-004-engineering-foundation` — Django 5.2 LTS API scaffold, React web shell, CI workflow (SHA-pinned), secret scanner + tests, compose, `.env.example`, runbook
3. `docs/asg-002-tenancy-design` — ADR-0003 (**Proposed**) + data dictionary
4. `docs/asg-012-014-contract-drafts` — `packages/contracts/` + tests
5. `docs/asg-015-uganda-research` — compliance records (**unreviewed**) — **top of stack = the complete project**

## What is deliberately NOT built, and why
No tenants, users, auth, products, stock, sales, accounting, POS, HR or any model/migration. These cannot be built honestly yet:
- **ASG-005/006 (tenancy, roles, RLS)** need ADR-0003 accepted (D-024; also D-020…D-023). Django's user model must be fixed before the first migration, so `django.contrib.auth` is not installed.
- **ASG-008/010/011 (stock, ledger, first slice)** need D-007/D-008/D-009 (currency/rounding, accounting policy, costing and negative stock). Blueprint §6 forbids guessing these.
- **ASG-012/013 (offline)** need D-005, and any fiscal-offline behaviour must follow EFRIS's *current* offline window (EF-006, unverified).
- **Fiscalisation, tax rates, payroll** need verified, professionally reviewed rules (ASG-015, D-011, D-012).

## Decisions and assumptions
- Accepted: ADR-0001, ADR-0002 (Django + DRF + PostgreSQL; React + TypeScript; monorepo).
- **Proposed, awaiting you:** ADR-0003 (tenancy; recommends shared schema + PostgreSQL Row-Level Security, conditional on A-002/A-003).
- Tracked assumptions: A-001 team skills unknown · A-002 cloud-hosted + containerised · A-003 modest pilot scale.
- D-018 (partial): agent commits locally to feature branches only; never `main`; never pushes. PR/review policy undefined.

## Validation results (2026-10-27) — fresh clone of branch `docs/asg-015-uganda-research` at `b214e55`
Environment: Python 3.12.3, Node 22.22.2, PostgreSQL 16.15 installed locally in the sandbox (not Docker). Exact commands: `docs/runbooks/local-development.md`.

| Check | Result |
|---|---|
| API: `ruff check` / `ruff format --check` / `mypy` (strict) | PASS / PASS / PASS |
| API: `makemigrations --check --dry-run` | PASS (no models exist) |
| API: `pytest` (12 tests, against PostgreSQL) | PASS (after starting PostgreSQL — the first run errored only because the database was down; confirmed, then re-run) |
| Repo: `ruff` on `scripts`/`tests` (check + format) | PASS |
| Repo: secret scan (`scripts/check_secrets.py`) | PASS — and verified to catch a planted secret (rc=1) |
| Repo: `pytest tests/security tests/contracts` (21 tests) | PASS; 3 negative controls proved the contract tests fail on broken state machines |
| `pip-audit` on pinned `dev.txt` | PASS — no known vulnerabilities |
| Web: `npm ci`, lint, format, typecheck, test (4), build | PASS ×6 |
| `npm audit --omit=dev --audit-level=high` (blocking in CI) | PASS — 0 vulnerabilities |
| `npm audit` (full) | **FAIL (rc=1)** — 1 high advisory in dev-only `undici` via `jsdom` — known **R-008**; fix on/after 2026-10-29 |
| Docs: links, 17 task statuses, D-/ASG- ID references, exactly one active task | PASS |
| `.github/workflows/ci.yml` | YAML parses; **NOT RUN on GitHub** (R-009) |
| `docker-compose.yml` | YAML parses; **NOT RUN** (no Docker) |
| Compliance records, ADR-0003, contracts: correctness/approval | **NOT REVIEWED** by any human or professional |

Not proven: behaviour on another machine, CI services/caching, Docker, security beyond the listed tests, correctness of drafted proposals, anything about Uganda law beyond what the records state with their evidence levels.

## Mistakes caught this session (transparency)
- Earlier "0 vulnerabilities" claim was wrong (install output); corrected (R-008).
- The secret scanner flagged its own test fixtures once tracked — the CI `secrets` job would have failed on first run. Reproduced, fixed at the source on the ASG-004 branch, branches restacked. Also fixed a word-boundary bug that missed `DB_PASSWORD = "…"`.
- A dev-server crash with bad DB credentials briefly produced no test output; diagnosed (Django checks migrations at startup) and re-tested properly.
- Research found my training knowledge stale: a URA notice of 10–11 Aug 2026 (post-cutoff) extends mandatory EFRIS to 12 sectors — now recorded from the primary source.

## Known defects and risks
`PROGRESS.md` R-002…R-010 plus: **R-011-equivalent** — compliance facts are time-sensitive and partially conflicting (tracked in R-006). Priority: EF-006 (accreditation requirement, offline window).

## Questions for the owner (all in `docs/product/decision-register.md`)
1. **D-024** approve/amend ADR-0003 (shared schema + RLS), and answer D-020 (one person in several tenants?), D-021 (operator support access?), D-022 (who assigns tenant-wide grants?), D-023 (entitlement per tenant or company?).
2. **D-001** first customer segment/template — note: 12 URA-listed sectors have mandatory EFRIS regardless of VAT status.
3. **D-005** which workflows must work offline in release 1.
4. **D-007/D-008/D-009** currency/rounding, accounting policy, costing and negative stock (needs an accounting reviewer).
5. **D-016** (was deleting the Blueprint intentional?), **D-018** (push/PR policy so CI can run), D-002/D-013 (confirm assumptions A-002/A-003).

## Exact next action
**Owner:** (a) review the branches; publish the top branch or open a PR so CI runs (closes R-009); (b) answer D-024 and D-020…D-023; (c) pick D-001/D-005.
**Next agent session (in order):**
1. Record the first CI result in `PROGRESS.md`; on green set ASG-004 DONE.
2. On acceptance of ADR-0003, set ASG-002 DONE; then **ASG-005** (tenant/company/branch creation) — start with the RLS spike to verify the ADR's claims, introduce the identity/user-model ADR, then implement with cross-tenant tests. Do **not** start before acceptance.
3. Continue ASG-015 items 1–4 (read the FY2026/27 EFRIS handbook, resolve TX-002, read the DPPA text, research NSSF, obtain professional review).
4. On/after 2026-10-29: resolve R-008 (`npm audit fix`, re-run web checks).

## Git state
- Remote `origin` (read-only use): `main` @ `7ff17b7` — unchanged by this work.
- Local top-of-stack branch: `docs/asg-015-uganda-research`. Working tree clean after the final commit.
- Nothing pushed. Delivered as a zip of the final tree and a git bundle containing all branches.

## GitHub MCP actions actually performed
None (no GitHub MCP available). GitHub API unauthenticated access returned 403; action SHAs were resolved with plain `git ls-remote`/shallow clones of the official `actions/*` repositories.

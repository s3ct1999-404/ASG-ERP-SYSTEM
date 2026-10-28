# CLAUDE.md — ASG ERP

ASG ERP is a configurable, multi-tenant, offline-capable business platform (initial market: Uganda). It has its own code and identity. Repository files — not chat memory — are the source of truth.

## Read first, every session (before editing)
1. `ASG_ERP_AGENT_INSTRUCTIONS.md` — the operating contract
2. `PROGRESS.md` — master checklist and task register (canonical)
3. `CURRENT_SPRINT.md` — the one active task
4. `NEXT_SESSION.md` — restart point
5. The active requirement (`REQUIREMENTS.md`), relevant `docs/adr/`, and `.claude/rules/`

Then inspect `git status`, branch, recent commits and relevant files. **Verify the handoff matches reality; fix stale notes.** Repo identity: `s3ct1999-404/ASG-ERP-SYSTEM`. State the verified state, the single task, acceptance criteria and any approval needed before editing.

## Instruction precedence
1. Security, privacy, repository safety, data integrity
2. `ASG_ERP_AGENT_INSTRUCTIONS.md`, this file, `.claude/rules/`
3. Approved Blueprint (`docs/ASG_ERP_MASTER_BLUEPRINT.md`), requirements, accepted ADRs
4. `PROGRESS.md`, `CURRENT_SPRINT.md`, `NEXT_SESSION.md`
5. The current user task

Conflicting authoritative sources: do not pick silently — record the conflict and ask.

## Working rules
- One bounded task at a time, with acceptance criteria. Prefer one complete vertical slice.
- Architectural or risky change → propose a plan and **wait for approval**.
- No destructive operations (reset --hard, force-push, dropped data, destructive migrations, deploys) without explicit approval and a recovery plan.
- No commit/push unless the owner or established workflow authorises it. Stage specific files only after reviewing the diff.
- Never claim tests/builds/migrations passed unless run. Report `PASS` / `FAIL` / `NOT RUN` / `BLOCKED`.
- Mark stubs, mocks and TODOs explicitly. A feature is not `DONE` because files exist.
- Synthetic data only. No secrets in files, logs, prompts or handoffs.
- Stack is decided (ADR-0002 accepted: Django + React monorepo). Mobile/desktop and tenancy-data approach are NOT decided — do not create `apps/mobile`, `apps/desktop` or tenant-scoped tables.
- Ask when a decision touches data integrity, security, tenancy, accounting, offline conflicts or compliance and no approved decision covers it.
- Uganda tax/EFRIS/payroll/privacy rules: never from memory; verified official sources only (`docs/compliance/uganda/`).

## Handoff triggers (update `PROGRESS.md`, `CURRENT_SPRINT.md`, `NEXT_SESSION.md` together)
After a task or material progress · a defect or unmet requirement · a decision · block/unblock · **before** context compaction, a new chat, or stopping · before handing over. If context is getting crowded, stop starting new work, reach a safe checkpoint, run checks, update the three files, leave one exact next action.

## Where things live
`docs/ASG_ERP_MASTER_BLUEPRINT.md` blueprint · `REQUIREMENTS.md` requirement IDs · `ROADMAP.md` stages/gates · `ARCHITECTURE.md`, `SECURITY.md`, `OFFLINE_SYNC.md`, `APP_PLATFORM.md` design · `docs/adr/` decisions · `docs/product/decision-register.md` owner decisions · `.claude/rules/` detailed rules · `CHANGELOG.md`.

## Verification commands
Stack: Django + DRF + PostgreSQL (`services/api`), React + TypeScript (`apps/web`). Full setup: `docs/runbooks/local-development.md`.
- API (`cd services/api`, venv active, `.env` exported, PostgreSQL running): `ruff check .` · `ruff format --check .` · `mypy .` · `python manage.py makemigrations --check --dry-run` · `python -m pytest`
- Web (`cd apps/web`): `npm run lint` · `npm run format:check` · `npm run typecheck` · `npm test` · `npm run build`
- Dependency audits: `pip-audit -r requirements/dev.txt --no-deps --disable-pip` · `npm audit --omit=dev --audit-level=high`
- Secret scan: `python scripts/check_secrets.py` (self-tests: `python -m pytest tests/security tests/contracts -p no:django -q`)
- OpenAPI contract (`docs/api/openapi.yaml`) must match the code; a test enforces it.
Report each as PASS/FAIL/NOT RUN/BLOCKED. CI (`.github/workflows/ci.yml`) has **never run on GitHub** until a result is recorded in `PROGRESS.md`.
Do not add `django.contrib.auth` or any tenant-scoped model before the identity design and tenancy ADR (ASG-002/ASG-006).

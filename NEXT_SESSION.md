# ASG ERP — Next Session Handoff

## Last updated
2026-10-26

## Start here (read in this order)
1. `ASG_ERP_AGENT_INSTRUCTIONS.md`  2. `CLAUDE.md`  3. `PROGRESS.md`  4. `CURRENT_SPRINT.md`  5. this file  6. active requirement + relevant ADRs (`docs/adr/`)
Then `git status`, `git log --oneline -8`, and **verify this handoff against the actual repo** before editing.

## Current milestone
Stage 2 — Repository and engineering foundation (scaffold built; gate not yet met because CI has not run)

## Current task
ASG-004 — Set up local development and CI (**IN REVIEW**). ASG-003 (continuity docs) also **IN REVIEW** awaiting owner content review. ASG-001 is **DONE**.

## Current state
- **Done:** ADR-0002 accepted (Django 5.2 LTS + DRF + PostgreSQL; React + TypeScript; monorepo). API scaffold, web shell, OpenAPI contract + drift test, pinned deps, CI workflow file, compose file, `.env.example`, runbook.
- **Partial:** CI (defined, never run on GitHub); Docker Compose (never run).
- **Not started:** ASG-002 (tenant/company/branch boundaries ADR + data dictionary) and everything after it; ADR-0003 (mobile/desktop); tenancy-isolation ADR; compliance research; skills/agents; secret-scanning job.
- **Deliberately absent:** `django.contrib.auth`, any model, any migration, `apps/mobile`, `apps/desktop`. Do not add auth or tenant-scoped tables before ASG-002 / the tenancy ADR / ASG-006.

## Decisions and assumptions
- ADR-0001 accepted; ADR-0002 accepted (owner approval in session 2026-10-26).
- Tracked assumptions (owner to confirm): **A-001** team skills unknown ("not sure yet"); **A-002** cloud-hosted + containerised; **A-003** modest pilot scale. Revisit A-001 before Stage 3.
- D-018 (partly decided): agent may commit **locally to feature branches only**; never `main`; **never push**. PR/review policy undefined.
- D-016 open: was deleting the Blueprint from `main` (`7ff17b7`) intentional?
- Django deliberately kept on the 5.2 LTS line (6.1 exists).

## Files changed this session
See `git log`. Commits on local branches (identity `Claude (agent)`, repo-local config):
- `a893af0` docs: bootstrap continuity system and baseline docs (ASG-003) — branch `chore/bootstrap-foundation`
- `f2f5663` docs: accept ADR-0002, close ASG-001, start ASG-004 — same branch
- `3e1403d` feat(platform): engineering foundation scaffold (ASG-004) — branch `feat/asg-004-engineering-foundation`
- A final docs commit (this handoff + progress evidence) follows `3e1403d` on the feature branch.

## Validation results (2026-10-26)
Run in a **fresh clone** of the local feature branch (`/tmp/clean`), following `docs/runbooks/local-development.md`. Environment: Python 3.12.3, Node 22.22.2, PostgreSQL 16.15 installed locally in the sandbox (apt) — **not** Docker.

| Check (exact command) | Result |
|---|---|
| `ruff check .` | PASS |
| `ruff format --check .` | PASS (19 files) |
| `mypy .` (strict, django/drf plugins) | PASS (19 files) |
| `python manage.py makemigrations --check --dry-run` | PASS (no changes; no models exist) |
| `python -m pytest` (against PostgreSQL) | PASS — 12 passed |
| `pip-audit -r requirements/dev.txt --no-deps --disable-pip` | PASS — no known vulnerabilities |
| `npm ci` | PASS |
| `npm run lint` / `format:check` / `typecheck` | PASS / PASS / PASS |
| `npm test` (vitest) | PASS — 4 passed, no `act()` warnings |
| `npm run build` | PASS |
| `npm audit --omit=dev --audit-level=high` | PASS — 0 vulnerabilities (production deps) |
| `npm audit` (full) | **FAIL (rc=1)** — 1 high advisory in dev-only `undici` via `jsdom` — known, tracked as **R-008**, fix on/after 2026-10-29 |
| Live server: `/health/live/` 200; `/health/ready/` 200; unknown path 404; spoofed Host → 400; `X-Frame-Options: DENY` | PASS (observed with curl) |
| Live server, PostgreSQL stopped: ready → 503 `{"status":"unavailable"}`, live → 200, recovery → 200; JSON ERROR log carries `request_id`; DB password absent from log | PASS (observed) |
| Seeded failing test → `pytest` | rc=1 as intended (gate fails when it should); test removed afterwards |
| `.github/workflows/ci.yml` | **NOT RUN** — YAML parses only; never executed on GitHub |
| `docker-compose.yml` / `docker compose up -d db` | **NOT RUN** — Docker unavailable; YAML parses only |
| Human review of content / owner sign-off | **NOT DONE** |

Not proven by these checks: behaviour on another OS/machine, CI services/caching, Docker image behaviour, security beyond the listed tests (`manage.py check --deploy` warnings remain by design — see R-010), and the correctness of the draft requirements.

Corrections made during the session (for transparency): an early statement that npm reported "0 vulnerabilities" was wrong — it was install output; the real audit showed R-008. A mypy-flagged unused `type: ignore`, three ruff findings, a missing clickjacking middleware (`check --deploy` W002) and a React `act()` warning were found and fixed.

## Known defects and risks
`PROGRESS.md` → R-002…R-010. Most relevant now: **R-008** (dev-only npm advisory, dated action), **R-009** (CI/Docker never run), **R-010** (deployment hardening, CSRF decision, rate limiting, secret scanning, action/image pinning deferred).

## Blockers/questions for the owner
1. Push policy and PR/review process (D-018) — needed to run CI on GitHub and close R-009/ASG-004.
2. D-016 — Blueprint deletion intent.
3. Confirm assumptions A-001/A-002/A-003, or answer D-002 (deployment) and D-013 (scale), which the tenancy ADR needs.
4. Review ASG-003 docs and ASG-004 scaffold.

## Exact next action
**Owner:** review the two branches; decide how to publish them (e.g. push `feat/asg-004-engineering-foundation` and open a PR) so CI runs; answer D-016.
**Next agent session (after CI result is known):** record the CI result in `PROGRESS.md`; if green, set ASG-004 (and, with owner sign-off, ASG-003) to DONE. Then start **ASG-002**: write the tenant/company/branch/permission boundary ADR and data dictionary (scope stated per entity, deny-by-default, scope-check points), **docs only — no models** — and surface D-002/D-004/D-013 for decision first. Do not begin ASG-005 until ASG-002 is approved. Also: on/after 2026-10-29 resolve R-008.

## Git state
- Remote `origin` (read-only use): `https://github.com/s3ct1999-404/ASG-ERP-SYSTEM.git`, `main` @ `7ff17b7` — **unchanged by this work**
- Local branches: `chore/bootstrap-foundation` (2 commits ahead of `main`); `feat/asg-004-engineering-foundation` (stacked: bootstrap + scaffold + handoff docs)
- Nothing pushed. Working tree clean after the final docs commit.

## GitHub MCP actions actually performed
None. No GitHub MCP was available; the repo was read via public `git ls-remote`/`git clone`.

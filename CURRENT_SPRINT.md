# Current Sprint

> One active bounded task only. Overall status lives in `PROGRESS.md`.

## Milestone
Stage 2 — Repository and engineering foundation

## Active task
**ASG-004 — Set up local development and CI**
Status: **IN REVIEW** (built and verified locally; CI not yet run on GitHub)
Branch: `feat/asg-004-engineering-foundation` (local; not pushed)

## Goal
A clean checkout can be installed, tested and started from documented commands; CI enforces lint, type-check, tests and migration/contract checks. **No business-domain code.**

## Scope
- `services/api`: Django + DRF project, env-based settings (secure defaults), versioned `/api/v1/` health endpoints (live/ready), JSON structured logging, deny-by-default DRF permissions, OpenAPI generation, baseline tests
- `apps/web`: React + TypeScript (Vite) shell with lint, type-check, test, build
- `docs/api/openapi.yaml` generated and checked for drift
- `docker-compose.yml` (local PostgreSQL only), `.env.example` (placeholders only)
- `.github/workflows/ci.yml`
- `docs/runbooks/local-development.md`; verification commands recorded in `CLAUDE.md`
- Stack-specific `.gitignore` entries

## Out of scope
Tenancy, auth/users, any domain model or migration for business data (ASG-002 → ASG-006), mobile/desktop apps, deployment.

## Acceptance criteria — results (details and commands: `NEXT_SESSION.md`)
1. API starts; live 200; ready 200 with DB up and 503 with DB down — **PASS** (tests + verified on a live server by stopping PostgreSQL; liveness stayed 200; recovery confirmed).
2. Fail-closed settings and deny-by-default DRF — **PASS** (tests; spoofed Host → 400 on live server).
3. JSON structured logs, no secrets — **PASS** for the scenarios tested (tests + live ERROR line with request ID; DB password absent from log). Not a general guarantee.
4. ruff, mypy, pytest (PostgreSQL 16.15), makemigrations check, OpenAPI drift — **PASS** (fresh clone).
5. Web install, lint, format, typecheck, test, build — **PASS** (fresh clone).
6. CI workflow defined — **PARTIAL**: defined and YAML-valid; **NOT RUN** on GitHub.
7. Seeded failing test makes the check fail — **PASS** (pytest rc=1; then removed).
8. Docs let a new developer run everything — **PASS with caveat**: followed from a fresh clone in this sandbox using a locally installed PostgreSQL; the Docker Compose step was **NOT RUN** (no Docker available).

**Not DONE because:** criterion 6 is unmet and criterion 8 is unverified for Docker. Move to DONE after the first successful CI run is recorded (R-009) and the owner reviews.

## Dependencies
ASG-001 (DONE).

## Verification plan
Done locally (see `NEXT_SESSION.md`). Outstanding: first CI run on GitHub.

## Parked (not active work)
ASG-003 remains IN REVIEW awaiting owner content review. D-016 (Blueprint deletion) still open.

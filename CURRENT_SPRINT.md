# Current Sprint

> One active bounded task only. Overall status lives in `PROGRESS.md`.

## Milestone
Stage 2 — Repository and engineering foundation

## Active task
**ASG-004 — Set up local development and CI**
Status: **IN PROGRESS**
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

## Acceptance criteria (observable)
1. API installs from pinned requirements and starts; `GET /api/v1/health/live` returns 200 and `/health/ready` returns 200 with DB up and 503 with DB down (test).
2. Settings refuse to start without `SECRET_KEY`, default `DEBUG` to false, and DRF default permission is deny-by-default (test).
3. Logs are structured JSON (test) and contain no secrets.
4. `ruff`, type-check and `pytest` pass against **PostgreSQL**; `makemigrations --check` and OpenAPI-drift checks pass.
5. Web: install, lint, type-check, test and build pass.
6. CI workflow defined for all of the above. **It can only be marked PASS once it actually runs on GitHub**; until then it is NOT RUN.
7. A seeded failing test makes the local check fail (proves the gate bites).
8. Documentation lets a new developer run everything (verified by following it from a clean clone in this environment).

## Dependencies
ASG-001 (DONE).

## Verification plan
Run each command locally, record exact results in `NEXT_SESSION.md`. CI file is syntactically validated locally but not executed.

## Parked (not active work)
ASG-003 remains IN REVIEW awaiting owner content review. D-016 (Blueprint deletion) still open.

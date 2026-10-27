# Changelog

Meaningful user-facing or system-level changes. Format: newest first.

## [Unreleased]
### Added (ASG-004 — engineering foundation, local branch only)
- `services/api`: Django 5.2 LTS + DRF project, fail-closed settings, deny-by-default DRF permissions, `/api/v1/health/{live,ready}/`, JSON structured logging with request IDs, OpenAPI contract (`docs/api/openapi.yaml`) with drift test, 12 tests, pinned requirements.
- `apps/web`: React + TypeScript (Vite) shell with ESLint, Prettier, Vitest, build.
- `.github/workflows/ci.yml` (defined, not yet run on GitHub), `docker-compose.yml` (local PostgreSQL), `.env.example` (placeholders), `docs/runbooks/local-development.md`.
- ADR-0002 accepted. No business-domain code, models or migrations.
- CI hardening: actions pinned to commit SHAs; `scripts/check_secrets.py` with self-tests and a CI job.

### Added (bootstrap, ASG-003 — uncommitted, awaiting owner review)
- Project continuity system: `PROGRESS.md`, `CURRENT_SPRINT.md`, `NEXT_SESSION.md`, `CLAUDE.md`, `ASG_ERP_AGENT_INSTRUCTIONS.md`.
- Baseline planning docs, ADR-0001 (accepted), ADR-0002 (**proposed**, stack not selected), decision register, scoped rules, Uganda compliance templates.
- Master Blueprint restored to `docs/ASG_ERP_MASTER_BLUEPRINT.md` (was deleted from `main` in `7ff17b7`; see D-016).
- No application code; no stack selected.

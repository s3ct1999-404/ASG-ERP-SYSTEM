# ASG-ERP-SYSTEM

ASG ERP — a configurable, multi-tenant, offline-capable business-management platform (initial market: Uganda).

**Status:** early foundation. The stack is decided ([ADR-0002](docs/adr/0002-technology-stack.md)) and an engineering scaffold exists (API health endpoints, web shell, CI definition). **No business features exist yet.** See [`PROGRESS.md`](PROGRESS.md) for current status.

## Start here
| Purpose | File |
|---|---|
| Operating contract for AI/engineering sessions | [`ASG_ERP_AGENT_INSTRUCTIONS.md`](ASG_ERP_AGENT_INSTRUCTIONS.md), [`CLAUDE.md`](CLAUDE.md) |
| Master checklist and task register | [`PROGRESS.md`](PROGRESS.md) |
| Active task / restart point | [`CURRENT_SPRINT.md`](CURRENT_SPRINT.md), [`NEXT_SESSION.md`](NEXT_SESSION.md) |
| Product and engineering blueprint | [`docs/ASG_ERP_MASTER_BLUEPRINT.md`](docs/ASG_ERP_MASTER_BLUEPRINT.md) |
| Vision, requirements, roadmap | [`VISION.md`](VISION.md), [`REQUIREMENTS.md`](REQUIREMENTS.md), [`ROADMAP.md`](ROADMAP.md) |
| Design | [`ARCHITECTURE.md`](ARCHITECTURE.md), [`SECURITY.md`](SECURITY.md), [`OFFLINE_SYNC.md`](OFFLINE_SYNC.md), [`APP_PLATFORM.md`](APP_PLATFORM.md) |
| Decisions | [`docs/adr/`](docs/adr/), [`docs/product/decision-register.md`](docs/product/decision-register.md) |
| Uganda compliance (templates, unverified) | [`docs/compliance/uganda/`](docs/compliance/uganda/) |

## Running the project
See [`docs/runbooks/local-development.md`](docs/runbooks/local-development.md). Layout: `services/api` (Django + DRF), `apps/web` (React + TypeScript), `docs/api/openapi.yaml` (API contract).

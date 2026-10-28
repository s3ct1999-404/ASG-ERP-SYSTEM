# ADR-0001: The repository is the source of truth; PROGRESS.md is the single task register

- Status: **Accepted** (owner-directed via `ASG_ERP_AGENT_INSTRUCTIONS.md`)
- Date: 2026-10-26
- Deciders: Product owner (instruction set); drafted by agent

## Context
Development will span many chat sessions and context compactions. Chat memory is unreliable and unauditable.

## Decision
- Durable state lives in repository files: `CLAUDE.md`, `PROGRESS.md`, `CURRENT_SPRINT.md`, `NEXT_SESSION.md`, `REQUIREMENTS.md`, `ROADMAP.md`, ADRs, and the decision register.
- `PROGRESS.md` is the **only** task register; `REQUIREMENTS.md` holds requirement IDs/acceptance criteria; `CURRENT_SPRINT.md` holds one active task; `NEXT_SESSION.md` holds the restart point. Other documents link, never duplicate.
- Each session starts by reading these files and verifying them against Git.
- Conflicts between authoritative sources are recorded and resolved by a decision, then the canonical document and an ADR are updated.

## ADR format (used by this repo)
Title · Status (`Proposed`/`Accepted`/`Rejected`/`Superseded by ADR-NNNN`) · Date · Context · Options · Decision · Consequences. Files: `docs/adr/NNNN-kebab-title.md`.

## Consequences
Small documentation overhead per task; recoverable work and honest status. Requires discipline to update the files together at each handoff trigger.

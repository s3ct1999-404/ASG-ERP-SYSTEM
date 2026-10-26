# ADR-0002: Technology stack and workspace model

- Status: **PROPOSED — NOT ACCEPTED. No stack has been selected.**
- Date: 2026-10-26
- Deciders: Product owner (pending). Drafted by agent.
- Task: ASG-001 (BLOCKED on owner)

## Context
The repository is empty (README title only). Blueprint §5.2 requires comparing reasonable choices, then selecting **one coherent default stack** after confirming constraints. Constraints that are **unknown** and materially affect the choice: team skills (D-003), deployment target (D-002), scale (D-013), first-release offline needs (D-005), supported devices (D-006). The recommendation below is therefore conditional.

## Fixed by the Blueprint (not re-decided here)
Modular monolith first · PostgreSQL central database · versioned REST API with OpenAPI · durable background-job queue · object-storage abstraction · containers with separate dev/staging/prod · unit/integration/contract/e2e/security/offline test layers · CI with lint, type-check, tests, migration and dependency checks.

## Decision 1 — Backend (pick one; no two competing primary backends)

| Criterion | A. Django (Python) + DRF | B. NestJS (TypeScript) |
|---|---|---|
| Fit for ERP/ledger work | Mature ORM, migrations, auth, admin built in; large ERP precedent in the Python ecosystem | Strong structure/DI for modules; ORM/migration/auth choices must be assembled |
| Modular-monolith boundaries | Django apps; boundaries enforced by convention/tooling | Nest modules give explicit module/DI boundaries |
| Shared types with TS web/mobile | Via generated OpenAPI clients | Native language sharing possible |
| Migrations | Built-in, reviewed, mature | Depends on chosen ORM |
| Risk | Requires discipline to keep modules decoupled; two languages in repo | More assembly; maturity depends on chosen libraries |
| Hiring/skills | **Unknown** (D-003) | **Unknown** (D-003) |

**Agent recommendation (conditional):** **A. Django + DRF + PostgreSQL**, because built-in migrations/auth and the ledger-heavy domain favour a batteries-included framework. **Choose B instead if the team is TypeScript-only**, since team skill outweighs framework fit. *Versions and current support status must be verified at approval time.*

## Decision 2 — Web client
React + TypeScript (Blueprint candidate). Alternatives not compared in depth because the Blueprint already names it and no constraint contradicts it. **Recommend React + TypeScript**, state management/UI kit deferred to the first slice.

## Decision 3 — Mobile and desktop
Options: React Native, Flutter (mobile); Tauri, Electron, or PWA (desktop). The choice hinges on **offline storage, outbox reliability and device support**, which are not yet specified (D-005, D-006) and are exercised only in Stage 5. **Recommendation: do not decide now.** Create ADR-0003 after Stage 4 once the offline action matrix (ASG-012) exists. Do not create `apps/mobile` or `apps/desktop` until then.

## Decision 4 — Workspace model
Options: monorepo vs multi-repo. **Recommend a single monorepo** (Blueprint §11): atomic changes across API contract and clients, one CI. Layout `services/api`, `apps/web`, `packages/contracts`, created only when each has content. Cost: tooling coupling for two languages if Option A.

## Decision 5 — Multi-tenancy data approach (separate ADR required)
Shared-schema with explicit scope columns vs schema-per-tenant vs database-per-tenant has major security/ops consequences and must follow ASG-002 (scope model per entity). **Not decided here.** Will be ADR-0003/0004 (numbering to be fixed when drafted).

## Rejected / deferred
- Microservices: rejected for now (Blueprint §2.2, §5.1).
- Two backends in parallel: rejected (Blueprint §5.2).
- Mobile/desktop framework: deferred, see Decision 3.

## Consequences if the recommendation is accepted
Follow-up tasks: ASG-004 (tooling/CI/`.env.example`), stack-specific `.gitignore`, a documented verification-command block in `CLAUDE.md`, ADR for tenancy data model. Cost: Python+TS in one repo.

## Questions for the owner (need answers to finalise)
1. What languages/frameworks does the current or planned team know (D-003)?
2. Cloud-hosted, customer-hosted, or both (D-002)?
3. Expected tenants/users/branches/offline devices at pilot and year one (D-013)?
4. Is there any existing infrastructure or vendor constraint?
5. Approve, amend or reject the recommendation above.

## Decision
*Pending owner.*

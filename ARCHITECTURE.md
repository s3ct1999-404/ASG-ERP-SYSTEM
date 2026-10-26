# Architecture

*Status: skeleton. Canonical principles: Blueprint §4–§6. Stack: **undecided** (`docs/adr/0002-technology-stack.md`, Proposed). This file records only what the Blueprint already fixes plus open design work.*

## Fixed principles
- **Modular monolith first**; microservices only with an accepted ADR. Modules have explicit contracts and do not reach into each other's internals.
- Candidate modules (Blueprint §5.1): identity-access, tenancy-organisation, app-registry-marketplace, inventory, sales, accounting, pos, hr, reporting, projects, fleet, documents-workflows, integrations, offline-sync, notifications, audit, subscriptions-entitlements.
- Cross-module writes go through application services or versioned domain events, never direct table manipulation. No circular module dependencies. Business rules stay out of UI components.
- Versioned REST API with an OpenAPI contract; reviewed, versioned DB migrations; PostgreSQL as central database.
- Tenancy hierarchy: platform operator → tenant → company → branch; users hold scoped memberships. Scope is defined **per entity**, not by a blanket `tenant_id`.
- No production-path mocks unless clearly marked with a replacement task.

## Open design work (tracked in `PROGRESS.md`)
| Item | Task |
|---|---|
| Stack and workspace model | ASG-001 |
| Tenant/company/branch scope model and data dictionary | ASG-002 |
| Tenancy data-isolation approach (own ADR, after ASG-002) | — |
| Product/customer data contracts | ASG-007 |
| Accounting posting rules and ledger invariants | ASG-010 |
| Offline action matrix and outbox contract | ASG-012 |
| App manifest and lifecycle state machine | ASG-014 |
| Threat-model outline | Stage 1 |

No architecture diagram exists yet; it is a Stage 1 deliverable.

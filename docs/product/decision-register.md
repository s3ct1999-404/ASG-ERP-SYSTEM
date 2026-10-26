# Owner Decision Register

Source: Blueprint §23 plus items found during bootstrap. The agent must **not** answer these by guessing. Where safe, a deferral is recorded as a tracked assumption with owner and due milestone; where a decision affects security, legal compliance, financial correctness or data loss, nothing is implemented until it is decided.

Status: `OPEN` · `DECIDED` · `DEFERRED (assumption)`.

| ID | Decision needed | Why it matters | Blocks | Status | Owner | Needed by |
|---|---|---|---|---|---|---|
| D-001 | Initial customer segment and first industry template | Scopes MVP and first template | Stage 0 gate | OPEN | Product owner | Stage 0 |
| D-002 | Deployment target: cloud-hosted, customer-hosted, or both | Drives architecture, backup, ops, cost | ASG-002 | DEFERRED (assumption A-002) | Product owner | Stage 1 |
| D-003 | Backend/web/mobile/desktop and monorepo choices; **team skills available** | Cost, hiring, offline capability | — | DECIDED for backend/web/monorepo (ADR-0002); mobile/desktop DEFERRED to ADR-0003; team skills unknown (A-001) | Product owner | Stage 1 |
| D-004 | Subscription/licensing and app-entitlement model | Shapes tenancy/entitlement model | ASG-002 | OPEN | Product owner | Stage 1 |
| D-005 | Offline workflows required in first release | Sets offline matrix | ASG-012 | OPEN | Product owner | Stage 1 |
| D-006 | Officially supported devices and browsers | Test matrix, offline storage | ASG-004, Stage 9 | OPEN | Product owner | Stage 2 |
| D-007 | Currency, multi-currency, rounding policy | Ledger correctness | ASG-010 | OPEN | Product owner + accounting reviewer | Before ASG-010 |
| D-008 | Accounting policy and posting rules (chart of accounts, fiscal periods) | Financial integrity | ASG-010 | OPEN | Product owner + accounting reviewer | Before ASG-010 |
| D-009 | Inventory costing method and negative-stock policy | Stock valuation/ledger | ASG-008, ASG-010 | OPEN | Product owner | Before ASG-008 |
| D-010 | POS payment methods and receipt requirements | POS scope | Stage 6 | OPEN | Product owner | Stage 6 |
| D-011 | EFRIS/URA integration scope and current official requirements | Compliance claims | Stage 8 | OPEN — needs verified research (ASG-015) | Product owner + compliance reviewer | Stage 8 |
| D-012 | Payroll scope and legal review | Legal risk | HR payroll | OPEN | Product owner + legal reviewer | Stage 6 |
| D-013 | Expected scale: tenants, users, branches, transactions, offline devices | Architecture/sizing | tenancy ADR | DEFERRED (assumption A-003) | Product owner | Stage 1 |
| D-014 | Data residency, retention, backup, disaster-recovery expectations | Legal/ops | Stage 9, data model | OPEN | Product owner + legal reviewer | Stage 1 |
| D-015 | Marketplace trust model and third-party execution model | Security | Stage 7 | OPEN | Product owner | Stage 7 |
| D-016 | Was deleting `ASG_ERP_MASTER_BLUEPRINT.md` from `main` (`7ff17b7`) intentional? Bootstrap restores it at `docs/ASG_ERP_MASTER_BLUEPRINT.md` on a local branch only | Avoid fighting an intentional removal | Commit of bootstrap | OPEN | Product owner | Now |
| D-017 | Languages, accessibility, support and training expectations | UX/test scope | Stage 9 | OPEN | Product owner | Stage 6 |
| D-018 | Commit/push workflow: who commits, branch naming, PR/review policy, permission for the agent to commit | Repository safety | — | DECIDED (partially): agent may commit **locally to feature branches only**; never to `main`; **never push**. PR/review policy still undefined | Product owner | PR policy before first push |
| D-019 | Issue tracker choice (GitHub Issues vs other) and GitHub MCP access level | Avoid scattering tasks | ASG-017 | OPEN | Product owner | Stage 2 |

## Tracked assumptions
A-001 (team skills), A-002 (cloud-hosted, containerised), A-003 (modest pilot scale) — defined in `docs/adr/0002-technology-stack.md`. Add rows here (with owner and due milestone) before relying on any further deferral.

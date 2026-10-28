# Roadmap

*Canonical stage definitions and deliverables: Blueprint §15. Live status and checklists: `PROGRESS.md`. A stage is complete only when its **gate** is met, not because code exists.*

| Stage | Name | Gate (summary) |
|---|---|---|
| 0 | Product definition | Owner approves first vertical slice |
| 1 | Architecture & technical decisions | No critical ambiguity in tenancy, ledger, sync, app lifecycle |
| 2 | Repository & engineering foundation | Clean checkout installs, tests, starts via documented commands |
| 3 | Shared platform core | Automated cross-tenant and cross-branch tests pass |
| 4 | First vertical slice (tenant → user → product/customer → stock → sale → accounting → payment → report/audit) | Works UI→API→DB, survives errors, covered by tests |
| 5 | Offline capture & sync | Resilience tests pass; states understandable |
| 6 | Core business apps (inventory, sales, accounting, POS, reporting, documents, HR, projects, fleet, multi-company) | Each app has requirements, permissions, migrations, tests, audit, documented deps |
| 7 | Marketplace & extensibility | Lifecycle tests prove retention and safe failure/retry |
| 8 | Uganda integrations & templates | Integration status truthful; compliance claims evidenced |
| 9 | Cross-platform delivery & ops readiness | Release checklist approved; zero critical security/data-loss defects |

## Current position
Stage 0/1, bootstrap. Next gate work: owner decisions (`docs/product/decision-register.md`), stack ADR-0002, then ASG-002.

## Risks and assumptions (seed)
See `PROGRESS.md` risks R-001…R-006 and Blueprint §2.2 for out-of-scope items. First-slice implementation is **not** authorised until the Stage 0 gate and owner approval.

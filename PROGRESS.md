# ASG ERP — PROGRESS (master checklist)

> Canonical progress ledger. Other records link here; they do not duplicate the task register.
> Status values: `NOT STARTED` · `IN PROGRESS` · `BLOCKED` · `IN REVIEW` · `DONE`.
> Rule: `DONE` requires met acceptance criteria **and** recorded evidence (test output, observed behaviour, or an approved decision). Files existing is not evidence.

## Header

| Field | Value |
|---|---|
| Last updated | 2026-10-26 |
| Current stage | Stage 0 → Stage 1 (Product definition / Architecture decisions) |
| Active task | ASG-003 — see `CURRENT_SPRINT.md` |
| Overall status | **Foundation docs drafted, awaiting owner review. No application code exists. No stack is selected.** |
| Base commit (remote `main`) | `7ff17b7` |
| Working branch | `chore/bootstrap-foundation` (local; **uncommitted**, not pushed) |
| Last verified against repo | 2026-10-26 (fresh clone of `s3ct1999-404/ASG-ERP-SYSTEM`) |
| Next exact task | Owner review of bootstrap + decision on ADR-0002 → closes ASG-003 and ASG-001 (see `NEXT_SESSION.md`) |

### Evidence-based summary
- Remote repo contained only a title-only `README.md`; the Blueprint was added in `e54e53a` and deleted in `7ff17b7`. It is restored here at `docs/ASG_ERP_MASTER_BLUEPRINT.md` (owner to confirm the deletion was not intentional — see decision D-016).
- Planning and continuity documents are drafted. Their only validation so far is the structural check recorded in `NEXT_SESSION.md` (files exist, links resolve, statuses valid, no secret patterns). That is **not** product validation.
- No tests, builds, migrations or CI exist, because no stack is chosen.

## Stage checklist

Gates are defined in the Blueprint §15. A stage is complete only when its gate is met.

### Stage 0 — Product definition
- [x] Vision drafted from Blueprint (`VISION.md`) — *draft, unapproved*
- [x] Requirements register started with IDs/priorities/acceptance criteria (`REQUIREMENTS.md`) — *draft, unapproved*
- [ ] User roles/personas and priority workflows
- [ ] Initial MVP boundary approved
- [x] Risks, assumptions, out-of-scope seeded (`ROADMAP.md`, Blueprint §2.2)
- [ ] **Gate:** owner approves first vertical slice

### Stage 1 — Architecture and technical decisions
- [x] Decision register created (`docs/product/decision-register.md`)
- [x] Stack ADR **proposed** (`docs/adr/0002-technology-stack.md`) — *not accepted*
- [ ] Stack/workspace decision accepted by owner
- [ ] Tenant/company/branch scope model (ADR + data dictionary) — ASG-002
- [ ] Offline support matrix — ASG-012
- [ ] App manifest/lifecycle design — ASG-014
- [ ] Threat-model outline
- [ ] **Gate:** no critical ambiguity in tenancy, ledger, sync, app lifecycle

### Stage 2 — Repository and engineering foundation
- [ ] Workspace structure, local dev instructions — ASG-004
- [ ] Formatter/linter/type-checker/test runner — ASG-004
- [ ] CI pipeline — ASG-004
- [ ] Migration/seed conventions, health endpoint, structured logging
- [ ] **Gate:** clean checkout installs, tests, starts via documented commands

### Stage 3 — Shared platform core
- [ ] Auth/session lifecycle
- [ ] Tenant/company/branch setup — ASG-005
- [ ] Membership/roles/permissions + server-side scope — ASG-006
- [ ] Audit foundation; app registry/entitlement skeleton
- [ ] **Gate:** automated cross-tenant and cross-branch tests pass

### Stage 4 — First complete vertical slice
- [ ] ASG-007 → ASG-011 (see register)
- [ ] **Gate:** UI→API→DB flow works, survives errors, covered by tests

### Stage 5 — Offline capture and synchronisation
- [ ] ASG-012, ASG-013
- [ ] **Gate:** resilience tests pass; pending/accepted/rejected/conflict states understandable

### Stage 6 — Expand core business apps
- [ ] See application checklist below
- [ ] **Gate:** each app has requirements, permissions, migrations, API/UI tests, audit events, documented dependencies

### Stage 7 — Marketplace and extensibility
- [ ] ASG-014 + lifecycle implementation
- [ ] **Gate:** lifecycle tests prove data retention and safe failure/retry

### Stage 8 — Uganda integrations and industry templates
- [ ] ASG-015 + verified EFRIS/URA scope + pilot template
- [ ] **Gate:** integration status truthful; compliance claims have review evidence

### Stage 9 — Cross-platform delivery and operational readiness
- [ ] Release strategy, backup/restore rehearsal, monitoring, perf/a11y, runbooks, pilot
- [ ] **Gate:** release checklist approved; zero critical security/data-loss defects

## Task register

| ID | Title | Pri | Status | Depends on | Acceptance criteria (observable) | Evidence | Notes |
|---|---|---|---|---|---|---|---|
| ASG-001 | Decide stack and repository/workspace model | P0 | **BLOCKED** (awaiting owner) | D-002, D-003, D-013 | ADR-0002 status is `Accepted` with owner approval recorded; rejected alternatives and consequences documented; `.gitignore`/tooling follow-up tasks created | ADR-0002 drafted as `Proposed` only | Not decided by the agent (task card rule 7) |
| ASG-002 | Document tenant/company/branch and permission boundaries | P0 | NOT STARTED | ASG-001 not required for the model itself; D-004 | ADR + data dictionary state scope (tenant/company/branch) for every entity in Blueprint §4; deny-by-default rule and scope-check points listed | — | |
| ASG-003 | Establish project instructions and session handoff process | P0 | **IN REVIEW** | — | `PROGRESS.md`, `CLAUDE.md`, `CURRENT_SPRINT.md`, `NEXT_SESSION.md` exist, are mutually consistent, and direct sessions to read them first; owner has reviewed | Structural check recorded in `NEXT_SESSION.md` (not yet owner-reviewed) | Awaiting owner review and commit decision |
| ASG-004 | Set up local development and CI | P1 | NOT STARTED | ASG-001 | Clean checkout installs/tests/starts via documented commands; CI runs lint, type-check, tests, and fails on a seeded failure | — | Includes `.env.example` (placeholders only) |
| ASG-005 | Implement tenant/company/branch creation | P1 | NOT STARTED | ASG-001, ASG-002, ASG-004 | Tenant→company→branch creatable via API; scope persisted; audit event recorded; tests: success/denial/invalid | — | |
| ASG-006 | Implement scoped membership/roles and cross-tenant tests | P0 | NOT STARTED | ASG-005 | User with branch-A scope cannot read/write branch B or another tenant (API, report, export); automated tests prove denial | — | Gate for Stage 3 |
| ASG-007 | Define product/customer data contracts | P1 | NOT STARTED | ASG-002 | Contracts + OpenAPI fragments reviewed; scope per entity stated | — | |
| ASG-008 | Implement inventory movement ledger | P1 | NOT STARTED | ASG-006, ASG-007, D-009 | Receive stock into permitted warehouse; movement recorded once; same idempotency key does not double quantity; audit entry; tests: success, denial, duplicate, invalid | — | Costing/negative-stock policy needs owner decision |
| ASG-009 | Implement sales order lifecycle | P1 | NOT STARTED | ASG-007, ASG-008 | Quotation→confirmed→fulfilled→invoiced states enforced by state machine; invalid transitions rejected; tests | — | |
| ASG-010 | Define accounting posting rules and ledger invariants | P0 | NOT STARTED | D-008, D-009 | Approved rules document; tests prove debits=credits, posted entries immutable except reversal, rounding rule explicit | — | **No rule may be guessed** (Blueprint §6.1) |
| ASG-011 | Implement one end-to-end sale→stock→accounting workflow | P1 | NOT STARTED | ASG-008, ASG-009, ASG-010 | Slice per Blueprint §15 Stage 4 works UI→API→DB with tests incl. failure paths | — | |
| ASG-012 | Define offline action matrix and outbox contract | P1 | NOT STARTED | D-005, ASG-002 | Matrix states per action: offline-capable?, conflict policy, reference data; statuses/transitions/retry rules documented | — | |
| ASG-013 | Implement idempotent sync processing and conflict handling | P1 | NOT STARTED | ASG-012, ASG-011 | Resilience tests (duplicate, restart, timeout-after-commit, reorder, conflict) pass | — | |
| ASG-014 | Define app manifest and lifecycle state machine | P1 | NOT STARTED | ASG-002 | Manifest schema + explicit state machine documented; dependency-cycle and uninstall-retention rules stated | — | |
| ASG-015 | Create Uganda compliance research records | P1 | NOT STARTED | — | Each record has source URL, date checked, category, summary, impact, evidence, open questions, owner; **only current official sources** | Templates exist (`docs/compliance/uganda/`), **no research done** | Must not be filled from memory |
| ASG-016 | Add scoped Claude skills/agents (plan-feature, review-change, etc.) | P2 | NOT STARTED | ASG-001 | Skills/agents exist per Blueprint §11 and are adapted to installed Claude Code version | — | Starter Pack was **not supplied**; rules in `.claude/rules/` were authored from the Blueprint |
| ASG-017 | Verify GitHub MCP identity/permissions; align issues with register | P2 | NOT STARTED | — | MCP confirmed pointing at `s3ct1999-404/ASG-ERP-SYSTEM`; write permission state recorded; no duplicate issues | — | No GitHub MCP was available in the bootstrap session |

## Application / module checklist

All applications: `NOT STARTED` (no code exists). Order is decided by the roadmap, not this list.

| Application | Status | Requirements | Notes |
|---|---|---|---|
| Platform Administration | NOT STARTED | PLAT-* | Stage 3 |
| Multi-Branch & Multi-Company | NOT STARTED | TEN-* | Scope model first (ASG-002) |
| Stock & Inventory | NOT STARTED | INV-* | Stage 4/6 |
| Sales Tracking | NOT STARTED | SAL-* | Stage 4/6 |
| Finance & Accounting | NOT STARTED | ACC-* | Rules blocked on D-008/D-009 |
| Point of Sale | NOT STARTED | POS-* | Fiscal integration only after verification |
| Reporting & BI | NOT STARTED | RPT-* | |
| Documents & Workflow Approval | NOT STARTED | DOC-* | |
| Human Resources | NOT STARTED | HR-* | Payroll only after legal review |
| Project & Task Management | NOT STARTED | PRJ-* | |
| Fleet & Transport | NOT STARTED | FLT-* | |
| ASG App Marketplace | NOT STARTED | APP-* | Stage 7 |

## Known defects, risks, blockers

| ID | Type | Description | Impact | Owner | Status |
|---|---|---|---|---|---|
| R-001 | Blocker | Stack not decided (ADR-0002 proposed) | Blocks Stage 2 onward | Product owner | Open |
| R-002 | Risk | Starter Pack (skills/agents/rules) not supplied | Rules authored from Blueprint; skills deferred (ASG-016) | Product owner | Open |
| R-003 | Risk | No GitHub MCP/write access in bootstrap session | Nothing pushed; issues not aligned | Product owner | Open |
| R-004 | Risk | Blueprint was deleted from `main` (`7ff17b7`) | Possible intentional removal; restored on branch only | Product owner | Open (D-016) |
| R-005 | Risk | File `ASG_ERP_Master_Blueprint.docx` in project files is plain text, not a real Word file | Word tooling fails on it; canonical copy is the `.md` | Product owner | Open (informational) |
| R-006 | Compliance | No Uganda compliance research done; no claims may be made | Blocks Stage 8 | Product owner | Open |

## Open owner decisions

Authoritative list: `docs/product/decision-register.md`. Decisions that block the next step: **D-002 (deployment), D-003 (team skills/stack), D-013 (scale), D-016 (Blueprint deletion)**.

## Update log

| Date | Change | By |
|---|---|---|
| 2026-10-26 | Initial creation during bootstrap (ASG-003). Statuses reflect an empty repository. | Agent |

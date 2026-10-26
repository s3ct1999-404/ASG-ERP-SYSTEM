# ASG ERP SYSTEM
## Master Blueprint and Claude Code Build Instructions
**Version:** 1.0  
**Product owner:** ASG ERP Systems  
**Initial market:** Uganda  
**Purpose:** Establish the product vision, architecture, project structure, engineering rules, delivery stages, quality gates, and Claude Code operating procedure.

---

# 1. How to use this document

Give this document to Claude Code from the root of a new or existing ASG ERP repository. Tell Claude to follow the **Bootstrap Prompt** in Section 18.

Claude must not attempt to generate the entire ERP in one pass. Its first assignment is to inspect the repository, explain its proposed approach, and create the documentation, directory structure, baseline configuration, and backlog. Actual application features must then be implemented in small, tested vertical slices.

If the repository already contains files, Claude must inspect them and preserve useful work. It must not overwrite, delete, reset, or replace existing files without inspecting and explaining the impact first.

This document is the initial product baseline. If a later decision changes it, Claude must update the relevant source document and record the decision in `docs/adr/` (Architecture Decision Records). Do not allow conflicting copies of requirements to grow unchecked.

# 2. Product vision

ASG ERP is a configurable business-management platform inspired by the broad ERP concept used by products such as Odoo, but it must have its own code, user experience, implementation, and product identity. It will help businesses manage operations in one connected system, with optional applications, industry templates, company branding, multiple companies and branches, and online/offline operation.

The platform must be suitable for small businesses and capable of growing toward larger organisations without requiring a separate product for each company size.

## 2.1 Product goals

1. Deliver a secure, multi-tenant ERP platform.
2. Allow a tenant to manage one or more companies and branches, subject to permissions and subscription entitlements.
3. Provide a common platform and independently installable applications.
4. Support web, desktop, Android, and iOS experiences through a deliberate shared API and design system.
5. Allow supported workflows to be captured offline and synchronised reliably when connectivity returns.
6. Provide configurable industry templates, roles, workflows, fields, print layouts, branding, and app bundles.
7. Support Uganda-specific requirements, integrations, currencies, dates, tax configuration, and local operating realities.
8. Keep accounting, inventory, payments, approvals, and audit records trustworthy.
9. Support third-party and first-party app development through a controlled marketplace.
10. Make upgrades, backups, restore, monitoring, and support repeatable.

## 2.2 Non-goals for the first release

- Reproducing every feature of a mature ERP immediately.
- Microservices before there is evidence they are needed.
- Unrestricted third-party code execution inside the core application.
- Claiming regulatory compliance before current official requirements have been verified and tested.
- Treating an offline transaction as centrally accepted or officially fiscalised before confirmation from the relevant service.
- Building every industry template before the core workflow is reliable.

## 2.3 Success measures

Track at least:
- Critical user journeys passing end-to-end tests.
- No cross-tenant data exposure in automated security tests.
- Financial postings balance and are immutable after posting except through controlled reversal/correction.
- Inventory movements are traceable and idempotent.
- Offline operations survive app restart, retry safely, and expose conflicts rather than silently losing data.
- Database migrations can be applied and, where practical, rolled forward safely in a test environment.
- A new developer can run the project from documented instructions.
- App installation, update, disable, and uninstall follow documented lifecycle rules.
- Backups can be restored in a rehearsal.
- Release blockers, known defects, and compliance assumptions are visible.

# 3. Product application catalogue

The platform should support these applications. Their exact implementation order is determined by the roadmap, not by this list.

1. **Stock & Inventory Management** — products, variants, units of measure, warehouses, locations, receipts, deliveries, adjustments, transfers, reorder rules, lots/serials where required, stock ledger, valuation policy, counts, reservations, and traceability.
2. **Sales Tracking** — leads/opportunities if in scope, quotations, orders, customers, pricing, discounts, fulfilment, returns, credit notes, receipts, and sales history.
3. **Finance & Accounting** — chart of accounts, journals, double-entry ledger, fiscal periods, receivables, payables, payments, bank/cash accounts, reconciliation, tax configuration, financial statements, and controlled period closing.
4. **Human Resources** — employee records, departments, roles, attendance/leave where required, payroll only after local requirements are verified, approvals, and strict employee/payroll access.
5. **Point of Sale (POS)** — fast checkout, tills/sessions, receipts, payment methods, returns, cash-up, offline queue, stock integration, and fiscal integration only under verified rules.
6. **Reporting & Business Intelligence** — operational dashboards, financial reports, filters, scheduled reports, export permissions, and traceability to source records.
7. **Multi-Branch & Multi-Company** — company registry, branch registry, access scopes, inter-branch transfers, intercompany rules where required, company-specific configuration, and consolidated reporting with correct permissions.
8. **Project & Task Management** — projects, tasks, assignments, milestones, status, time/cost tracking if approved, attachments, and approvals.
9. **Fleet & Transport** — vehicles, drivers, assignments, maintenance, fuel, mileage, trips, costs, documents, and compliance reminders.
10. **Documents & Workflow Approval** — document storage and metadata, versioning, retention, access controls, approval routes, delegation, comments, notifications, and audit history.
11. **ASG App Marketplace** — app catalogue, manifests, compatibility, dependencies, install/configure/upgrade/disable/uninstall, entitlements, signing/review, release history, and app-specific permissions.
12. **Platform Administration** — tenant setup, user invitations, roles, permissions, app management, company/branch configuration, branding, subscription/entitlement, system health, audit, and support tools.

## 3.1 Application lifecycle requirements

Apps must be represented in a registry with stable IDs, version, publisher, manifest, dependencies, permissions, configuration schema, migrations, compatibility range, and lifecycle state.

Lifecycle states should be explicit, for example: `available`, `installing`, `installed`, `upgrading`, `disabled`, `uninstalling`, `failed`. Use a state machine rather than scattered booleans.

- Installing an app validates dependencies, compatibility, permissions, configuration, and migration plan.
- Upgrades are versioned and repeatable; migrations must be tested on realistic synthetic data.
- Disabling an app must stop its UI and actions without corrupting shared data.
- Uninstalling must not automatically delete accounting history, posted transactions, or records needed by other apps. Prefer archive/deactivation and an explicit retention policy.
- Third-party app code must not receive unrestricted database or tenant access.
- App permissions must be explicit, least-privilege, reviewable, and revocable.
- App code must be trusted, signed or otherwise verified, versioned, scanned, and reviewed before production publication.
- Dependency cycles must be rejected or deliberately handled.
- Every app installation/update/uninstall must be auditable.

# 4. User, organisation, and tenancy model

Use clear separation between:
- **Platform operator** — operates the ASG service.
- **Tenant** — a customer organisation/account boundary.
- **Company** — a legal or operational company belonging to a tenant.
- **Branch** — a location/business unit belonging to a company.
- **User** — an authenticated person who may be granted scoped access.
- **Role and permission** — named permission bundles and granular actions.
- **App entitlement** — whether a tenant/company may install/use an app.
- **Configuration** — tenant/company/branch settings with documented inheritance rules.

Never assume that a user may access all companies or branches just because they belong to a tenant. Authorisation must be checked server-side on every relevant API, job, report, export, file access, and background task.

A proposed core data model may include:
- Tenant
- Company
- Branch
- User
- Membership
- Role
- Permission
- RolePermission
- MembershipScope
- App
- AppVersion
- AppInstallation
- AppEntitlement
- AuditEvent
- IntegrationConnection
- SyncOperation
- FileMetadata
- WorkflowDefinition
- WorkflowInstance
- Notification
- IdempotencyRecord

The exact schema must be reviewed and documented before implementation. Avoid a generic `tenant_id` column being added blindly to tables where a different ownership model is correct. Define tenant/company/branch scope for each entity in the data dictionary.

# 5. Architecture principles

## 5.1 Start with a modular monolith

Unless a documented Architecture Decision Record justifies otherwise, use a modular monolith for the initial product. Modules have explicit boundaries and contracts; they are not allowed to reach into each other's internal implementation arbitrarily. This keeps early deployment and debugging manageable while preserving a path to split services later.

Potential backend modules:
- identity-access
- tenancy-organisation
- app-registry-marketplace
- inventory
- sales
- accounting
- pos
- hr
- reporting
- projects
- fleet
- documents-workflows
- integrations
- offline-sync
- notifications
- audit
- subscriptions-entitlements

## 5.2 Technology choice

Do not silently select a stack before inspecting any existing repository and confirming constraints. If the repository is empty, prepare a short Architecture Decision Record comparing reasonable choices, then select one coherent default stack.

A reasonable candidate stack to evaluate:
- Web: TypeScript + React.
- Mobile: React Native or Flutter; select one after evaluating offline storage, team skills, shared UI/API needs, and platform support.
- Desktop: Tauri or Electron, or a packaged web/PWA experience if requirements permit.
- Backend: Django/Python or NestJS/TypeScript. Select one for the initial backend; do not create two competing primary backends without a specific reason.
- Central database: PostgreSQL.
- Local offline database: SQLite on native/desktop; browser storage appropriate to the selected web architecture.
- API: versioned REST API initially, with a documented OpenAPI contract.
- Background jobs: durable queue appropriate to the chosen backend.
- Files: object storage abstraction with metadata and access control.
- Tests: unit, integration, API contract, end-to-end, security, and offline/resilience tests.
- CI: lint, type-check, tests, migration checks, dependency/security checks, and build.
- Deployment: containers and separate development/staging/production environments.

This list is a candidate, not an instruction to install all technologies. Keep the initial stack small and internally consistent. Record choices and rejected alternatives in `docs/adr/`.

## 5.3 Platform boundaries

- Apps depend on documented platform contracts.
- Shared services expose stable interfaces.
- Cross-module writes use explicit application services or domain events, not direct table manipulation by unrelated modules.
- Events must be versioned if persisted or consumed asynchronously.
- APIs and app manifests are versioned.
- Database changes use reviewed migrations.
- Avoid circular module dependencies.
- Keep business rules out of UI components.
- Do not use mock implementations in production paths without clearly marking them and creating a replacement task.

# 6. Data integrity and business rules

## 6.1 Accounting
- Use double-entry accounting with debits equal to credits for each posted journal entry.
- Posted entries must not be silently edited or deleted; use controlled reversal/correction records.
- Define currency precision and rounding rules explicitly.
- Record effective dates, posting dates, source references, and actor/audit information where appropriate.
- Use idempotency keys for payments and external callbacks.
- Period closing and reopening require permission and audit.
- Do not hard-code tax rates or assume one tax treatment fits every customer. Use effective-dated configuration after compliance review.

## 6.2 Inventory
- Keep a traceable stock movement ledger.
- Define stock quantity and valuation rules, units of measure, warehouse/location scope, reservation policy, negative stock policy, and transfer lifecycle.
- A stock balance should be derivable/reconcilable against movements.
- Concurrent sales and transfers must not silently oversell or double-consume stock.
- Corrections must create traceable adjustment movements rather than erasing history.

## 6.3 Sales and POS
- Distinguish quotation, confirmed order, fulfilment, invoice, payment, return, and credit note states.
- POS must have an explicit till/session lifecycle and cash reconciliation.
- Payment operations must be idempotent.
- Receipts/invoices must clearly distinguish locally captured, server accepted, and externally fiscalised states where applicable.

## 6.4 Audit
Record who did what, when, against which organisation scope, the outcome, and a safe reference to affected records. Do not log passwords, tokens, full payment credentials, or unnecessary personal data. Audit events must be protected from ordinary application users modifying them.

# 7. Offline-first and synchronisation design

Offline is a product capability with a written contract, not just browser caching.

## 7.1 Required flow
1. The client checks the user's offline capability and downloads permitted reference data.
2. A supported action is validated locally to the extent possible.
3. The action and its outbox record are committed durably in one local transaction before the UI says it is safely queued.
4. Each operation has a unique ID/idempotency key, entity scope, schema/version, timestamp, and retry state.
5. When connectivity returns, the sync engine sends operations in the required dependency order.
6. The server authenticates and authorises again, validates current rules, applies idempotently, and returns an authoritative result.
7. The client records acknowledgement and updates local status.
8. Rejections and conflicts remain visible and recoverable; they are never silently discarded.

## 7.2 Required statuses
At minimum: `pending`, `syncing`, `synced`, `conflict`, `failed`, `needs_attention`. Define transitions and retry rules.

## 7.3 Conflict policy
Define conflict behaviour per entity and operation. Never apply a blanket “last write wins” policy to accounting, stock, payments, approvals, or other high-value transactions. Use explicit resolution, server validation, reservations, version checks, or business-specific policies.

## 7.4 Offline limits
Document what is and is not available offline, how stale reference data is shown, how permissions expire/revoke, and what happens if a device is lost. Do not store secrets unnecessarily. Protect local data appropriate to platform capabilities.

## 7.5 Tests
Test airplane-mode operation, app restart, device restart where practical, duplicate delivery, timeout after server commit, out-of-order operations, token expiry, revoked access, stale data, low storage, conflict, schema upgrade, and failed retry recovery.

## 7.6 Uganda fiscal integration
Any EFRIS/URA integration must be based on current official documentation and a documented compliance review. Do not claim an offline receipt is an officially accepted fiscal invoice. Record whether a document is locally created, submitted, accepted, rejected, or awaiting confirmation.

# 8. Uganda-specific configuration and compliance

Create `docs/compliance/uganda/` with:
- `efris-requirements.md`
- `tax-configuration.md`
- `payroll-requirements.md`
- `data-protection.md`
- `compliance-change-log.md`

For every compliance claim, record:
- Official source and URL
- Date checked
- Applicable business/customer category
- Requirement summary
- Implementation impact
- Test evidence
- Unresolved questions and owner

Use current official sources, including the relevant Uganda Revenue Authority and data-protection authority materials, and obtain qualified professional review where necessary. Do not hard-code legal interpretations based only on model memory. Keep tax rates, invoice rules, payroll settings, retention, and reporting requirements configurable and effective-dated where appropriate.

# 9. Branding, industry templates, and configuration

Templates should be versioned configuration packages, not separate forks of the ERP.

A template may define:
- Industry name and description
- Recommended/required apps
- Default roles and permissions
- Starter chart of accounts (subject to accounting review)
- Product/customer fields
- Workflows and approval thresholds
- Dashboard/report presets
- Invoice/receipt/quotation layouts
- Brand colours, logo, typography and terminology
- Units, tax configuration references, and local defaults
- Sample synthetic data for demos/training

Requirements:
- Preview before applying.
- Explain which settings will change.
- Applying a template must not silently destroy existing business data.
- Support template versioning and migration/upgrade guidance.
- Permit tenant/company branding within safe validation rules.
- Separate customer data from template package content.
- Include templates only after the underlying workflow is stable.

# 10. Security and privacy baseline

Security is a release requirement, not a later polish task.

- Enforce authentication and authorisation on the server.
- Deny access by default; validate company/branch scope on every request.
- Test cross-tenant access attempts.
- Use secure password/session/token handling from mature libraries; do not invent cryptography.
- Keep secrets out of source control, logs, prompts, sample files, and client bundles.
- Use environment variables or a proper secret manager; provide `.env.example` with placeholders only.
- Validate input on server and client; server validation is authoritative.
- Apply rate limits and abuse controls to sensitive endpoints.
- Protect file uploads and downloads with type/size validation, scanning where available, and scoped access.
- Use safe output encoding and parameterised database access/ORM patterns.
- Keep dependencies updated and run security scanning.
- Use least privilege for users, app integrations, service accounts, and MCP tools.
- Separate development, staging, and production credentials and data.
- Use synthetic data in AI prompts and development fixtures.
- Define data retention, export, correction, deletion, and backup policies with legal review.
- Avoid storing unnecessary personal data.
- Log security-relevant events without logging secrets.
- Perform a threat model before public beta and before adding third-party app execution.

# 11. Recommended repository structure

Claude must adapt this to the chosen stack and any existing repository. Do not create empty folders solely to make the tree look complete; each directory should have a purpose.

```text
asg-erp/
├── CLAUDE.md
├── README.md
├── VISION.md
├── REQUIREMENTS.md
├── ROADMAP.md
├── ARCHITECTURE.md
├── SECURITY.md
├── OFFLINE_SYNC.md
├── APP_PLATFORM.md
├── CURRENT_SPRINT.md
├── NEXT_SESSION.md
├── CHANGELOG.md
├── .env.example
├── .gitignore
├── .claude/
│   ├── rules/
│   │   ├── security.md
│   │   ├── database.md
│   │   ├── testing.md
│   │   └── offline-sync.md
│   ├── skills/
│   │   ├── plan-feature/SKILL.md
│   │   ├── implement-feature/SKILL.md
│   │   ├── review-change/SKILL.md
│   │   ├── session-handoff/SKILL.md
│   │   └── release-check/SKILL.md
│   └── agents/
│       ├── architecture-reviewer.md
│       ├── security-reviewer.md
│       └── test-reviewer.md
├── apps/
│   ├── web/
│   ├── mobile/
│   └── desktop/
├── services/
│   └── api/
├── packages/
│   ├── ui/
│   ├── contracts/
│   ├── config/
│   └── shared/
├── database/
│   ├── migrations/
│   ├── seeds/
│   └── docs/
├── tests/
│   ├── integration/
│   ├── e2e/
│   ├── security/
│   └── resilience/
├── docs/
│   ├── adr/
│   ├── api/
│   ├── modules/
│   ├── runbooks/
│   ├── compliance/uganda/
│   └── product/
└── scripts/
```

Do not create every app directory as an implemented application on day one. Create a directory only when the selected workspace and build system can support it or when it has a meaningful README/contract. A monorepo is a reasonable option but must be decided and documented.

# 12. Claude Code project instructions: CLAUDE.md

The root `CLAUDE.md` should be concise enough to remain useful. It should point to the larger documents rather than duplicate them.

## Required root CLAUDE.md content

- Project identity and purpose.
- Instruction precedence: security and repository safety first, then this file and scoped rules, then approved architecture/ADRs, then task-specific requirements.
- Read `CURRENT_SPRINT.md` and `NEXT_SESSION.md` before work.
- Inspect the repository and Git state before editing.
- Make one bounded change at a time.
- Follow module boundaries and API contracts.
- No unapproved destructive operations.
- No claims of tests/builds passing unless actually run.
- Update documentation and handoff after meaningful work.
- Use synthetic data only.
- Ask for clarification when a decision affects data integrity, security, tenancy, accounting, offline conflict handling, or compliance and is not covered by an approved decision.
- Required verification commands must be documented after the stack is chosen.

Detailed security, database, testing, and offline rules belong in `.claude/rules/` and can be scoped to relevant paths if supported by the installed Claude Code version.

# 13. Claude Code working protocol

For every task, Claude must:

1. **Orient:** read `CLAUDE.md`, `CURRENT_SPRINT.md`, `NEXT_SESSION.md`, relevant requirements, architecture, ADRs, and scoped rules.
2. **Inspect:** check `git status`, branch, recent commits, files, tests, and current implementation. Never assume the repository is empty.
3. **Restate:** state the task, acceptance criteria, constraints, assumptions, and files likely to change.
4. **Plan:** break work into a small sequence. For architectural or risky changes, propose the plan and wait for approval.
5. **Implement:** keep the change bounded. Reuse existing patterns and contracts. Do not mix unrelated refactors.
6. **Verify:** run relevant format/lint/type-check/unit/integration/e2e/migration checks available in the repository.
7. **Review:** inspect the diff for security, tenancy, data integrity, accessibility, error handling, and unintended changes.
8. **Document:** update API/module docs, ADRs, changelog, and task status as appropriate.
9. **Handoff:** update `CURRENT_SPRINT.md` and `NEXT_SESSION.md` with what changed, tests and results, known issues, and exact next action.
10. **Report honestly:** list files changed, commands run, pass/fail/skipped checks, risks, and remaining work.

Never say “done” when the code is untested or the implementation is only a placeholder. Explicitly label TODOs, stubs, mock integrations, and unsupported flows.

# 14. Context-window, token, and session continuity protocol

A long chat is not the project's source of truth. The repository is.

Use:
- `CLAUDE.md` for stable rules.
- `VISION.md` for product goals.
- `REQUIREMENTS.md` for requirement IDs and acceptance criteria.
- `ARCHITECTURE.md` and ADRs for technical decisions.
- `CURRENT_SPRINT.md` for active work.
- `NEXT_SESSION.md` for a concise restart point.
- Git commits for durable code checkpoints.
- Issues/tasks for backlog and ownership.

At the start of each session:
- Read the project instructions and handoff.
- Inspect Git status and recent history.
- Verify the described state against the actual code.
- Summarise current state and proposed next step before making edits.

When context is becoming crowded:
- Finish or safely pause the current bounded task.
- Run tests relevant to the current change.
- Update handoff documents.
- Record exact commands and results, including failures.
- Record unresolved questions and the next single action.
- Commit a coherent checkpoint if the diff is reviewed and the user/repository workflow permits.
- Use Claude Code's current supported context-compaction command when continuing the same task; start a fresh conversation/session for a genuinely different task if useful.
- Never rely on “remembering” an uncommitted change or a fact that exists only in chat.

Do not put secrets or personal/customer data in handoff files. Keep handoffs short and factual.

## NEXT_SESSION.md template

```markdown
# ASG ERP — Next Session Handoff
## Last updated
YYYY-MM-DD

## Current milestone
[Milestone ID and title]

## Current task
[One bounded task ID and title]

## Current state
- Completed:
- Partially completed:
- Not started:

## Decisions and assumptions
- [Link to ADR or requirement]

## Files changed
- `path` — purpose

## Validation
- Command:
- Result:
- Failed/skipped checks:

## Known defects and risks
- ...

## Blockers/questions
- ...

## Exact next action
[One clear next action]

## Git state
- Branch:
- Latest commit:
- Uncommitted changes:

## Relevant docs/issues
- ...
```

# 15. Delivery roadmap and stage gates

Do not progress just because code exists. Progress when acceptance criteria and evidence are met.

## Stage 0 — Product definition
Deliver:
- Vision and scope
- User roles/personas and priority workflows
- Requirements register with IDs, priority, dependencies, acceptance criteria
- Initial MVP boundary
- Risks, assumptions, out-of-scope list
Gate: product owner approves the first vertical slice.

## Stage 1 — Architecture and technical decisions
Deliver:
- Architecture diagram and module boundaries
- Stack decision ADRs
- Tenant/company/branch scope model
- Initial data dictionary and API strategy
- Offline support matrix
- App manifest/lifecycle design
- Security/threat model outline
Gate: high-risk decisions are documented; no critical ambiguity in tenancy, ledger, sync, or app lifecycle.

## Stage 2 — Repository and engineering foundation
Deliver:
- Repository/workspace structure
- Local development instructions
- Environment configuration example
- Formatter, linter, type-checker, test runner
- CI pipeline
- Database migration and seed conventions
- Health endpoint and structured logging
- Baseline tests
Gate: a clean checkout can be installed, tested, and started using documented commands.

## Stage 3 — Shared platform core
Deliver:
- Authentication and session lifecycle
- Tenant/company/branch setup
- Membership and role/permission model
- Server-side scope enforcement
- Audit foundation
- App registry/entitlement skeleton
- File/notification/workflow foundations only as needed
Gate: automated cross-tenant and cross-branch access tests pass.

## Stage 4 — First complete vertical slice
Build one end-to-end workflow, not disconnected screens. Recommended first slice:
1. Create tenant/company/branch.
2. Invite/create user and assign scoped permissions.
3. Create product and customer.
4. Receive stock and record a stock movement.
5. Create a sales order/POS sale.
6. Post the required accounting entries using approved rules.
7. Record payment/receipt as applicable.
8. View a report and audit trail.
Gate: the flow works in the UI through API to database, survives errors, and is covered by tests. If a business rule is not decided, mark it as a decision/blocker rather than inventing it.

## Stage 5 — Offline capture and synchronisation
Deliver:
- Supported offline action matrix
- Local persistence and durable outbox
- Idempotent API processing
- Sync status and conflict UI
- Retry/backoff and token-expiry handling
- Duplicate, restart, conflict, and reconnect tests
Gate: resilience tests pass and the user can understand pending, accepted, rejected, and conflicted operations.

## Stage 6 — Expand core business apps
Implement in dependency order, each as a vertical slice:
- Inventory completion
- Sales completion
- Accounting controls and reports
- POS completion
- Reporting/BI
- Documents and workflow approvals
- HR (with sensitive-data controls and verified payroll scope)
- Projects/tasks
- Fleet/transport
- Multi-company consolidation as requirements permit
Gate: each app has requirements, permissions, migrations, API/UI tests, audit events, and documented dependencies.

## Stage 7 — Marketplace and extensibility
Deliver:
- App manifest schema
- App registry and dependency validation
- Install/configure/upgrade/disable/uninstall lifecycle
- Migration/version compatibility checks
- Permissions/entitlements
- Audit and recovery for failed lifecycle operations
- Developer guide, review process, sample app, and security restrictions
Gate: lifecycle tests prove data retention and safe failure/retry behaviour.

## Stage 8 — Uganda integrations and industry templates
Deliver:
- Compliance research records with current official sources
- Integration sandbox and adapter interfaces
- EFRIS/URA requirements and acceptance tests, only after verification
- Industry template package format and versioning
- At least one carefully selected pilot template
Gate: external integration status is truthful and compliance claims have review evidence.

## Stage 9 — Cross-platform delivery and operational readiness
Deliver:
- Web/mobile/desktop release strategy
- Offline storage security and platform-specific tests
- Backup/restore rehearsal
- Monitoring, error reporting, alerting
- Performance/load and accessibility checks
- Release, rollback, incident, and support runbooks
- User/admin documentation
- Staging pilot and feedback loop
Gate: release checklist approved; critical security/data-loss defects are zero.

# 16. Backlog and acceptance criteria

Every task must have:
- ID, e.g. `ASG-001`
- Title and business outcome
- Priority
- Dependencies
- Scope/non-scope
- Acceptance criteria in observable language
- Security/tenancy impact
- Data migration impact
- Offline impact
- Tests required
- Documentation required
- Status and owner

Suggested initial tasks:
- ASG-001: Decide stack and repository/workspace model.
- ASG-002: Document tenant/company/branch and permission boundaries.
- ASG-003: Establish project instructions and session handoff process.
- ASG-004: Set up local development and CI.
- ASG-005: Implement tenant/company/branch creation.
- ASG-006: Implement scoped membership/roles and cross-tenant tests.
- ASG-007: Define product/customer data contracts.
- ASG-008: Implement inventory movement ledger.
- ASG-009: Implement sales order lifecycle.
- ASG-010: Define accounting posting rules and ledger invariants.
- ASG-011: Implement one end-to-end sale-to-stock-to-accounting workflow.
- ASG-012: Define offline action matrix and outbox contract.
- ASG-013: Implement idempotent sync processing and conflict handling.
- ASG-014: Define app manifest and lifecycle state machine.
- ASG-015: Create Uganda compliance research records.

Acceptance criteria should be testable. “Build inventory” is not sufficient. Example: “A permitted branch user can receive stock into an assigned warehouse; the server validates scope; a stock movement is recorded once; retrying the same idempotency key does not double the quantity; the action appears in audit history; tests cover success, denial, duplicate, and invalid input.”

# 17. Tests and quality strategy

- **Unit:** domain rules, calculations, state transitions, validators.
- **Integration:** database transactions, migrations, repositories, queues, external adapters.
- **API/contract:** validation, auth, permission scope, API version compatibility.
- **End-to-end:** high-value user workflows from UI through backend.
- **Security:** tenant isolation, branch scope, role escalation, IDOR, secrets/logging, upload access.
- **Offline/resilience:** duplicates, retries, crash/restart, conflicts, stale data, revoked sessions, reordered operations.
- **Accounting:** debit-credit equality, reversals, rounding, period rules, duplicate payment protection.
- **Inventory:** stock ledger consistency, concurrent reservation/consumption, transfer and adjustment traceability.
- **Marketplace:** dependency cycles, incompatible versions, failed migration, uninstall retention, permissions.
- **Accessibility/usability:** keyboard use, labels, error messages, responsive behaviour.
- **Operational:** backup restore, health checks, deployment/rollback rehearsal.

Never treat a passing unit-test suite as proof of end-to-end readiness. Report exactly which checks were run and which were not.

# 18. Initial Claude Code bootstrap prompt

Paste this into Claude Code after placing this blueprint in the repository as `docs/ASG_ERP_MASTER_BLUEPRINT.md` (or provide the file through the available client).

```text
You are the lead software architect and engineering assistant for ASG ERP Systems.

First read `docs/ASG_ERP_MASTER_BLUEPRINT.md` completely. Then inspect the existing repository and Git state before changing anything.

MISSION FOR THIS FIRST TASK:
Bootstrap the project so it has a reliable product specification, engineering instructions, directory structure, decision log, staged roadmap, task backlog, and repeatable development workflow. Do not attempt to implement the whole ERP in this task.

NON-NEGOTIABLE RULES:
1. Do not assume the repository is empty. Inspect files, Git status, branches, recent commits, and existing configuration.
2. Do not delete, reset, overwrite, or replace existing work without explaining why and obtaining approval.
3. Do not select a technology stack silently. If one is not already established, compare reasonable options against the blueprint and create a concise ADR with a recommendation. State assumptions and ask for approval where a decision materially affects cost, platform coverage, or team workflow.
4. Treat tenant isolation, permission enforcement, financial integrity, inventory traceability, offline idempotency, and app lifecycle safety as foundational requirements.
5. Do not place real credentials, customer records, employee data, or production data in files or prompts.
6. Do not claim commands or tests passed unless you ran them.
7. Make changes in small, reviewable steps. Do not create a huge volume of speculative code.
8. Do not create meaningless empty directories. Each created directory must have a clear purpose or a README/contract.
9. Keep the root CLAUDE.md concise; place detailed policies in scoped rules and detailed design documents.
10. Record important decisions in `docs/adr/` and update the requirement/backlog status when evidence changes.

WORK PLAN:
A. Inspect the repository and report:
   - Existing stack and project structure
   - Git branch/status and uncommitted changes
   - Existing useful documents/configuration
   - Missing foundational items
B. Propose the minimal bootstrap plan before edits. If the repository is empty and the changes are low-risk, proceed after stating the plan; ask before destructive or materially consequential decisions.
C. Create/adapt the following documentation:
   - `README.md`
   - `VISION.md`
   - `REQUIREMENTS.md` with IDs, priorities, dependencies, acceptance criteria, and status
   - `ROADMAP.md`
   - `ARCHITECTURE.md`
   - `SECURITY.md`
   - `OFFLINE_SYNC.md`
   - `APP_PLATFORM.md`
   - `CURRENT_SPRINT.md`
   - `NEXT_SESSION.md`
   - `CHANGELOG.md`
   - `docs/adr/` with initial decisions or explicit decision proposals
   - `docs/compliance/uganda/` research templates
D. Create a concise root `CLAUDE.md` and relevant `.claude/rules/` files for security, database/data integrity, testing, and offline sync. Use the supported conventions of the installed Claude Code version.
E. Create the project directory structure appropriate to the stack decision. Do not generate all ERP features yet.
F. Add `.gitignore` and `.env.example` only where appropriate. The environment example must contain placeholders, never secrets.
G. Set up minimal engineering checks only after confirming the stack: formatting, lint, type checks, tests, and CI configuration where suitable.
H. Add a first backlog with the initial vertical slice and measurable acceptance criteria.
I. Verify the work. Run the checks that are possible and report skipped checks with reasons.
J. Update `CURRENT_SPRINT.md` and `NEXT_SESSION.md` with the exact state and next action.

REQUIRED FINAL REPORT:
1. What you inspected.
2. Decisions made versus decisions awaiting approval.
3. Files/directories created or changed.
4. Commands run and their actual results.
5. Security/tenancy/offline/accounting risks still open.
6. Exact recommended next task, with task ID and acceptance criteria.
7. Git status and whether a commit was made (do not commit unless repository policy/user permission supports it).

Do not begin implementing Inventory, Sales, Accounting, POS, HR, or other full apps until the foundation and first vertical-slice plan are reviewed.
```

# 19. Reusable prompts for ongoing work

## 19.1 Plan a feature
```text
Read CLAUDE.md, CURRENT_SPRINT.md, NEXT_SESSION.md, the relevant requirement, architecture docs, ADRs, and scoped rules. Inspect the implementation and Git state. Plan only the requested feature. Identify affected modules, API/data changes, permissions, tenant/branch scope, offline behaviour, migrations, audit events, tests, risks, and acceptance criteria. Do not edit until you have presented a bounded plan if the change is architectural or high-risk.
```

## 19.2 Implement a bounded task
```text
Implement requirement [ID] only. First confirm the acceptance criteria and inspect existing patterns. Keep the diff focused. Add/update tests and docs. Do not change unrelated modules or silently alter public contracts. Run relevant checks and inspect the final diff. Update task status and NEXT_SESSION.md. Report files, test commands/results, limitations, and remaining risks. Never claim unrun tests passed.
```

## 19.3 Recover after context expiry/new session
```text
Do not rely on previous chat memory. Read CLAUDE.md, CURRENT_SPRINT.md, NEXT_SESSION.md, the active requirement, and relevant architecture/ADR docs. Inspect Git status, recent commits, and actual files. Compare repository reality with the handoff. Summarise completed work, incomplete work, tests/results, blockers, and the single best next action. Do not edit until the state is verified and the plan is clear.
```

## 19.4 Independent review
```text
Review the current diff without making changes first. Look for tenant/branch data leaks, missing server-side authorization, accounting imbalance, duplicate stock/payment effects, unsafe offline retries, weak idempotency, unsafe app install/uninstall, data loss, migration hazards, missing tests, secrets in logs, and misleading compliance states. Categorise findings as Critical/High/Medium/Low, cite file/line references, explain impact, and propose tests. Do not report speculative issues as confirmed facts.
```

## 19.5 End-of-session handoff
```text
Prepare the repository for a clean new Claude Code session. Run relevant checks and inspect Git status/diff. Update CURRENT_SPRINT.md and NEXT_SESSION.md with actual progress, changed files, decisions/ADRs, commands and results, failures/skips, risks, blockers, branch/commit/uncommitted state, and one exact next action. Do not hide failing checks or commit automatically. Ensure no secrets or customer data enter handoff documents.
```

## 19.6 Release readiness
```text
Evaluate release readiness against the documented release checklist. Do not assume readiness. Review tests, security and tenant isolation, migrations, backup/restore evidence, monitoring/alerts, permissions, app lifecycle, offline recovery, accessibility, compliance evidence, rollback procedure, and open defects. Produce a blocker list with evidence and owners. Do not deploy or alter production systems.
```

# 20. MCP servers and supporting tools

MCP servers extend Claude Code's access to tools and data; they do not replace the ERP's actual runtime infrastructure, Git, CI, database, or backups.

Start with a small, trusted set:
1. **GitHub integration or GitHub CLI** — inspect issues/PRs and repository status; keep Git as the source of code history.
2. **Documentation lookup such as Context7** — check current library/API docs. Prefer official documentation for framework and compliance claims.
3. **Playwright** — browser automation and end-to-end testing for the web application.
4. **Database access** — only when useful; use a local/dev database and read-only access by default for inspection. Never connect an AI tool to production with broad write permissions.
5. **One issue tracker** — GitHub Issues, Linear, or Jira; choose one rather than scattering tasks across systems.
6. **Error monitoring such as Sentry** — introduce when the app exists; use a non-production project first.
7. **Figma integration** — optional if designs already live in Figma.

Before adding an MCP server:
- Verify the publisher, source code, package, permissions, and maintenance status.
- Understand whether it can read/write files, execute commands, access the network, or modify remote systems.
- Grant the minimum permissions needed.
- Use environment variables or a secret manager for credentials.
- Never paste secrets into chat or commit them.
- Prefer local/dev/staging data and synthetic fixtures.
- Test with read-only permissions before enabling write operations.
- Review the current official Claude Code MCP setup instructions because command syntax and server support may change.

Avoid adding many MCP servers at once. Start with version control, documentation lookup, and browser testing. Add others only when a real workflow benefits.

# 21. Git, checkpoints, and safe operations

Use feature branches and small commits. Example commands must be adapted to the actual repository:

```bash
git status
git log -5 --oneline
git switch -c feat/tenant-foundation
# implement a bounded task
git diff --check
git diff
git add <specific-files>
git commit -m "feat(platform): add tenant foundation"
git push -u origin feat/tenant-foundation
```

Rules:
- Do not stage all files blindly if unrelated user changes exist.
- Inspect diffs before committing.
- Never force-push, reset hard, delete branches, drop databases, or run destructive migrations without explicit approval and a recovery plan.
- Use a clean working tree before risky operations where possible.
- Keep generated artifacts and secrets out of Git.
- Commit coherent, verified checkpoints according to the user's workflow.

# 22. Deployment and operations

Before any real customer pilot, establish:
- Separate local/dev, staging, and production environments.
- Automated CI with reproducible builds.
- Managed secrets and rotation procedures.
- Database migration and rollback/forward-fix policy.
- Encrypted backups and documented retention.
- A tested restore rehearsal.
- Centralised structured logs, metrics, and error monitoring.
- Health/readiness checks and alert thresholds.
- Incident response and support contacts.
- Release notes and customer communication.
- Access review and least-privilege service accounts.
- Data export/retention and account offboarding procedures.
- Monitoring for sync queue age, failed syncs, conflicts, payment failures, app lifecycle failures, job backlog, and database health.

Do not deploy to production merely because the code compiles. Require a release checklist and human approval.

# 23. Product owner decisions to resolve early

Claude should maintain a decision register and not silently invent answers to these:
1. Initial customer segment and first industry template.
2. Target deployment: cloud-hosted, customer-hosted, or both.
3. Subscription/licensing and app entitlement model.
4. Selected backend, web, mobile, desktop, and monorepo approach.
5. Required offline workflows for the first release.
6. Which device types and browsers are officially supported.
7. Currency, multi-currency, rounding, and accounting policy requirements.
8. Inventory costing and negative-stock policy.
9. POS payment methods and receipt requirements.
10. EFRIS/URA integration scope and current official compliance requirements.
11. Payroll scope and relevant legal review.
12. Data residency, retention, backup, and disaster recovery expectations.
13. Expected number of tenants, users, branches, transactions, and offline devices.
14. Marketplace trust model and third-party app execution model.
15. Languages, accessibility, support and training expectations.

Where the answer can safely be deferred, mark it as a tracked assumption with an owner and due milestone. Where it affects security, legal compliance, financial correctness, or data loss, do not implement a guessed rule.

# 24. First practical checklist

- [ ] Put this document in the repository as `docs/ASG_ERP_MASTER_BLUEPRINT.md`.
- [ ] Initialise or inspect Git; protect existing work.
- [ ] Run Claude Code's diagnostic/help commands supported by the installed version.
- [ ] Run the bootstrap prompt in Section 18.
- [ ] Review the stack recommendation and ADRs before committing to the stack.
- [ ] Review `CLAUDE.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `ARCHITECTURE.md`, and the handoff documents.
- [ ] Configure a small set of trusted MCP integrations only if needed.
- [ ] Approve the first vertical slice and acceptance criteria.
- [ ] Build/test the foundation before expanding feature scope.
- [ ] Maintain a reviewed Git checkpoint and handoff at the end of each bounded task.

---

# Final instruction to Claude

Build ASG ERP as a dependable, extensible business platform—not as a large collection of disconnected screens. Protect tenant boundaries, financial truth, inventory traceability, offline reliability, and customer data first. Prefer small complete workflows over broad unfinished modules. Keep decisions, requirements, tests, and handoffs in the repository so development remains recoverable even when the chat context expires.

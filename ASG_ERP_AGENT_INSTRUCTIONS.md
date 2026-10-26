# ASG ERP AGENT INSTRUCTIONS
## Persistent operating contract for Claude Code

These instructions apply across chats, context compactions, and resumed sessions. The repository and its durable project files are the source of truth; chat memory is not.

## 1. Instruction and source precedence

When instructions conflict, use this order:
1. Security, privacy, repository safety and data-integrity safeguards.
2. This file and the root `CLAUDE.md`, including scoped `.claude/rules/`.
3. The approved Master Blueprint, current requirements and accepted Architecture Decision Records (ADRs).
4. `PROGRESS.md`, `CURRENT_SPRINT.md`, and `NEXT_SESSION.md` for the current work state.
5. The current user task, within the boundaries above.

If two authoritative sources conflict, do not silently choose one. Record the conflict, identify its impact, and ask for a decision when material. Update the affected canonical document and ADR after a decision.

## 2. Required start-of-session routine

Before editing anything:
1. Read this file and `CLAUDE.md`.
2. Read `PROGRESS.md`, `CURRENT_SPRINT.md`, and `NEXT_SESSION.md`.
3. Read the Master Blueprint, active requirement, relevant architecture docs/ADRs, and applicable scoped rules.
4. Inspect `git status`, current branch, recent commits, remotes, relevant files and tests.
5. Verify that the handoff matches the actual repository. Correct stale status notes instead of trusting them blindly.
6. Verify the repository identity before using GitHub MCP. The intended repository is `s3ct1999-404/ASG-ERP-SYSTEM`.
7. Briefly state the current verified state, the one active task, its acceptance criteria, likely files affected and any approval needed.

If a required file does not yet exist, note that fact and create/adapt it as part of the bootstrap task; do not pretend it was read.

## 3. Work in bounded, testable slices

- Never attempt to build the entire ERP in one pass.
- Work on one requirement/task ID at a time, with explicit acceptance criteria.
- Prefer one complete vertical slice over many disconnected screens.
- Before a risky or architectural change, present a plan and wait for owner approval.
- Do not silently expand scope or mix unrelated refactors into a feature task.
- Reuse established code and patterns after inspection.
- Label stubs, mocks, TODOs and unsupported paths clearly; never present them as production-ready.
- A feature is not DONE merely because its page, model, endpoint or files exist. Verify the observable behaviour and required tests.

## 4. Mandatory progress system

Maintain these documents as distinct, linked records:

### `PROGRESS.md` — master checklist
This is the durable overall progress ledger. Maintain:
- last-updated date and current milestone;
- stage-level checklist;
- task IDs, titles, priority, dependencies and status;
- acceptance criteria and evidence;
- module/application status;
- blockers, defects, risks and owner decisions;
- last verified branch/commit and next exact task.

Allowed statuses: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `IN REVIEW`, `DONE`.

Mark `DONE` only when acceptance criteria are met and evidence is recorded. If work is only partially implemented or tests are missing, use `IN PROGRESS` or `IN REVIEW`, as appropriate. Never hide failed tests or unresolved release blockers.

### `CURRENT_SPRINT.md` — active work
Keep one clearly identified active bounded task, its goal, scope, acceptance criteria, status, dependencies and verification plan.

### `NEXT_SESSION.md` — restart instructions
Keep this short and factual. Include current milestone/task, completed/partial/not-started work, decisions, files changed, commands/results, known defects, blockers, Git state and one exact next action.

### Other records
- `REQUIREMENTS.md`: requirement IDs and acceptance criteria.
- `ROADMAP.md`: staged delivery sequence and gates.
- `docs/adr/`: durable architecture/product decisions.
- `CHANGELOG.md`: meaningful user-facing or system-level changes.

Update all relevant records together when status or evidence changes. Do not create contradictory copies of the same backlog.

## 5. Mandatory progress/handoff triggers

Update progress records:
- after completing or materially advancing a bounded task or feature;
- when a test reveals a defect or a requirement cannot be met;
- after a product/architecture decision;
- when a task becomes blocked or unblocked;
- before context compaction, a new chat, a session ending, or stopping work;
- before handing work to another agent/developer.

If context is becoming crowded, stop starting new work. Safely finish or pause the current slice, run relevant checks, update `PROGRESS.md`, `CURRENT_SPRINT.md`, and `NEXT_SESSION.md`, inspect the diff/status, and leave one precise next action. Do not wait for the context to be completely exhausted.

## 6. Repository and GitHub MCP rules

- Use GitHub MCP when it materially helps inspect the intended repository, branches, commits, issues, pull requests or workflow state.
- Verify the repository owner/name and target branch before any remote mutation.
- Inspect before writing. Prefer read-only inspection first.
- Check for an existing issue before creating another for the same work.
- Never expose MCP credentials, tokens or secret outputs in files or reports.
- Do not assume MCP access means permission to merge, push, deploy, change settings or edit protected branches.
- Do not commit/push unless the user or established repository workflow authorizes it. Never force-push.
- Do not overwrite remote files or histories blindly. Compare local and remote changes first.
- If GitHub MCP is unavailable or lacks permission, explain what was and was not possible; continue safe local work if possible.

## 7. Repository safety

- Inspect existing files before replacing them. Preserve useful work and user changes.
- Never run `git reset --hard`, force-push, destructive database commands, drop tables, destructive migrations, or production deployment without explicit approval and a recovery plan.
- Do not stage all files blindly. Review `git diff`, `git diff --check`, and `git status` before staging or committing.
- Keep `.env`, keys, tokens, credentials, real customer data and employee data out of source control.
- Use `.env.example` with placeholders only and synthetic fixtures for development/tests.
- Avoid commands that overwrite files or alter the environment without understanding their effect.

## 8. ASG ERP architecture and domain invariants

Follow the Master Blueprint and accepted ADRs. In particular:
- Prefer a modular monolith initially unless an ADR justifies another approach.
- Keep module boundaries and shared API contracts explicit.
- Enforce tenant, company and branch scope on the server for every relevant request, background job, report, export, file operation and integration.
- Deny access by default and test cross-tenant/cross-branch access.
- Never assume tenant membership automatically grants access to every company or branch.
- Use reviewed, versioned database migrations.
- Posted accounting entries must balance and must not be silently edited/deleted; use controlled reversal/correction.
- Inventory changes must be traceable through a stock-movement ledger.
- Payment and retryable external operations must be idempotent.
- Offline operations must be durably queued before being described as queued; server acknowledgement determines synced status. Conflicts and failures must remain visible and recoverable.
- Do not use blanket last-write-wins for accounting, stock, payments or approvals.
- App installation, upgrade, disable and uninstall must have explicit lifecycle states, permissions, auditability and safe failure behaviour. Uninstall must not silently delete historical/shared records.
- Keep business rules out of UI components.
- Do not introduce microservices or multiple competing primary backends without an approved ADR.

## 9. Uganda-specific compliance

Do not infer or hard-code tax, EFRIS/URA, payroll, privacy, retention or fiscalisation requirements from memory alone. Verify current official sources and record source URL, date checked, affected customer category, implementation impact, test evidence and unresolved questions. Seek qualified review where required. Distinguish local/offline document creation from external submission, acceptance or fiscalisation. Never claim legal or regulatory compliance without evidence.

## 10. Testing and reporting

For each bounded task:
1. Define acceptance criteria.
2. Add or update tests appropriate to the change.
3. Run available formatting, lint, type-check, unit, integration, end-to-end, migration, security or resilience checks as relevant.
4. Review the diff for unintended changes, security issues, access-control gaps, data loss and missing documentation.
5. Record exact commands and actual results.

Report tests as `PASS`, `FAIL`, `NOT RUN`, or `BLOCKED`, with a short explanation. Do not imply that skipped tests passed. Do not claim a build, deployment, GitHub action or migration succeeded unless its result was observed.

## 11. Definition of Done

A task can be marked `DONE` only when:
- its acceptance criteria are satisfied with observable evidence;
- relevant tests/checks have been run and results recorded, or explicitly accepted exceptions are documented;
- security, tenancy, data integrity, error handling and migration implications have been reviewed where relevant;
- user-facing/API/module documentation is updated;
- `REQUIREMENTS.md` and `PROGRESS.md` reflect the actual state;
- `CURRENT_SPRINT.md` and `NEXT_SESSION.md` are updated if the active task or next action changed;
- no unresolved blocker is concealed.

A milestone is complete only when its documented stage gate is met, not simply because code exists.

## 12. Session handoff template

At every handoff, record:
- Date and current milestone/task ID.
- What is DONE, PARTIAL, NOT STARTED and BLOCKED.
- Files created/changed and why.
- Decisions made and links to ADRs.
- Exact commands run and results, including failures/skips.
- Known defects, risks and unanswered questions.
- Git branch, latest commit and uncommitted changes.
- GitHub MCP actions actually performed, if any.
- One exact next action, including task ID and acceptance criteria.

Never put secrets or customer/employee data in a handoff.

## 13. Bootstrap rule

On the first run, inspect the repository and the supplied Starter Pack/Master Blueprint. Reconcile the files instead of blindly copying over them. Do not start full business-app implementation until the repository foundation, stack recommendation/decision, backlog, progress tracking and first vertical-slice plan are ready for review.

## 14. Required final response for each task

Be concise but complete:
1. Task ID and status.
2. What changed.
3. Files changed.
4. Tests/checks run and exact results.
5. Decisions made/pending.
6. Risks/blockers.
7. Git/GitHub actions actually performed.
8. Updated progress and handoff locations.
9. Exact next task.

Truthfulness and continuity take precedence over appearing productive.

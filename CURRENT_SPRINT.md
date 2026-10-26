# Current Sprint

> One active bounded task only. Overall status lives in `PROGRESS.md`.

## Milestone
Stage 0/1 — Product definition and architecture decisions (bootstrap)

## Active task
**ASG-003 — Establish project instructions and session handoff process**
Status: **IN REVIEW** (drafted; awaiting owner review)

## Goal
The repository, not chat history, holds the project's state: any new session can orient itself from files, verify them against Git, and continue with one exact next action.

## Scope
- Progress/handoff system: `PROGRESS.md`, `CURRENT_SPRINT.md`, `NEXT_SESSION.md`, `CLAUDE.md`, `ASG_ERP_AGENT_INSTRUCTIONS.md`
- Baseline planning docs: `VISION.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `SECURITY.md`, `OFFLINE_SYNC.md`, `APP_PLATFORM.md`, `CHANGELOG.md`
- Decision records: `docs/adr/`, `docs/product/decision-register.md`
- Scoped rules: `.claude/rules/` (security, database, testing, offline-sync)
- Uganda compliance **templates only**: `docs/compliance/uganda/`
- Blueprint restored to `docs/ASG_ERP_MASTER_BLUEPRINT.md`

## Out of scope
- Any application code, framework install, CI, migrations
- Selecting the stack (ASG-001 — proposal only, awaiting owner)
- Compliance research (ASG-015), skills/agents (ASG-016), issue alignment (ASG-017)

## Acceptance criteria
1. The four continuity files exist, agree with each other, and tell sessions to read them first. — *drafted; consistency check recorded*
2. `CLAUDE.md` and `ASG_ERP_AGENT_INSTRUCTIONS.md` direct sessions to `PROGRESS.md`, `CURRENT_SPRINT.md`, `NEXT_SESSION.md` before editing. — *drafted*
3. `CURRENT_SPRINT.md` names one task; `NEXT_SESSION.md` states one next action. — *met in drafts*
4. No secrets, destructive changes, or unsupported compliance claims introduced. — *structural scan recorded; no human review yet*
5. **Owner has reviewed the bootstrap.** — *NOT MET*

Task moves to `DONE` only when criterion 5 is met and the owner decides how it is committed.

## Dependencies
None.

## Verification plan
Structural checks only (no stack exists): required files present; relative links resolve; statuses within allowed set; no secret-like strings; `git diff --check`; working tree shows no unintended changes. Results: `NEXT_SESSION.md`.

## Blocked on
Owner review. ADR-0002 (stack) is a separate decision that blocks ASG-001 and Stage 2.

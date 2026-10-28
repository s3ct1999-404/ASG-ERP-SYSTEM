# ADR-0003: Tenant / company / branch scope model and tenant-data isolation

- Status: **PROPOSED — NOT ACCEPTED.** Needs owner decision (D-024) and answers to D-020 … D-023.
- Date: 2026-10-27
- Task: ASG-002
- Related: Blueprint §4, §10; requirements TEN-001, TEN-002, SEC-001, SEC-003; ADR-0002 (deferred this decision); assumptions A-002 (cloud-hosted), A-003 (modest scale)

## Context
Blueprint §4 fixes the vocabulary — platform operator, tenant, company, branch, user, role/permission, app entitlement, configuration — and the rule that **tenant membership never implies access to every company or branch**, with authorisation re-checked server-side on every API, job, report, export, file access and background task. It also forbids "blindly" adding a generic `tenant_id` to every table. ADR-0002 deferred the data-isolation approach to this ADR; **no tenant-scoped table may be created until this is accepted**.

## Part 1 — Scope model (proposed)
- Hierarchy: **Platform operator → Tenant → Company → Branch.** A company belongs to exactly one tenant; a branch to exactly one company.
- The **tenant is the hard isolation boundary**: no query, job, report, export, file or event may cross it except through explicit, audited platform-operator mechanisms (Part 4).
- Every entity is assigned one scope class (full table: `database/docs/data-dictionary.md`):
  | Class | Meaning | Examples |
  |---|---|---|
  | `PLATFORM` | Not owned by any tenant; operator-managed | App catalogue, permission catalogue |
  | `TENANT` | Owned by a tenant, shared across its companies | Memberships, roles, entitlements |
  | `COMPANY` | Belongs to a legal/operational company | Ledger, chart of accounts, tax config |
  | `BRANCH` | Belongs to one branch (and thereby its company/tenant) | Warehouse stock, tills, branch settings |
- Every row of a non-`PLATFORM` entity carries the foreign keys needed to resolve **all** its ancestors, enforced by constraints (e.g. a branch-scoped row's company must equal its branch's company).
- Access is granted through **MembershipScope** (membership × role × scope node). Rules, all deny-by-default:
  1. A grant at a **branch** covers that branch only.
  2. A grant at a **company** covers that company and its branches.
  3. A **tenant-wide** grant is a distinct, explicit, high-privilege assignment (never implied by membership, never a default role); assigning one is audited. *(Who may assign it: D-022.)*
  4. No grant ⇒ no access. Absence of a scope filter is a defect, not a "see everything" mode.

## Part 2 — Isolation approach (options)

| Criterion | A. Shared schema + scope columns, enforced in app **and** PostgreSQL Row-Level Security | B. Schema per tenant | C. Database per tenant |
|---|---|---|---|
| Cross-tenant leak risk | Application bug can leak unless RLS catches it → RLS is mandatory defence in depth | Lower (separate namespaces) but `search_path`/connection mistakes possible | Lowest |
| Migrations & app lifecycle (Blueprint §3.1: per-app install/upgrade migrations tested on realistic data) | One migration run | Every tenant schema must be migrated and each app install/upgrade fanned out; long, partial-failure states | Same fan-out, per database |
| Operational cost at unknown scale (A-003) | Lowest; simplest backup/restore of the whole platform | Moderate; many schemas strain catalogs/tooling at high tenant counts | Highest |
| Per-tenant restore/export/deletion (Blueprint §22, retention) | Harder (filtered operations) | Easier | Easiest |
| Platform-wide reporting / consolidation across companies of one tenant | Natural | Natural within a tenant schema | Natural within a tenant DB |
| Customer-hosted deployment (A-002 uncertain) | Fine | Fine | Fits well |
| Django ecosystem fit | Plain Django + PostgreSQL | Needs third-party tenancy tooling | Multi-DB routing, extra complexity |

**Agent recommendation (conditional):** **A**, with these non-negotiable controls:
1. A single scoped data-access layer (the only supported way to query tenant-owned tables) that **requires** a scope context and fails closed when absent.
2. PostgreSQL **Row-Level Security** on every tenant-owned table, with `FORCE ROW LEVEL SECURITY`; the application connects as a non-owner, non-superuser role (superusers and table owners bypass RLS otherwise).
3. Tenant context set per transaction (`SET LOCAL`), so connection pooling in transaction mode cannot leak context between requests.
4. Cross-tenant and cross-branch denial tests as a **release gate** (Stage 3 gate), including a test that bypassing the data-access layer is still stopped by RLS.
5. Revisit if (a) any customer requires physical isolation or per-tenant restore, or (b) the deployment decision (D-002) makes customer-hosted dominant — option C is the escape path for such tenants, so tenant identifiers must be globally unique and never reused.

*These claims about RLS behaviour must be proved in a spike on this stack (ASG-006) before the ADR is marked fully verified.* The recommendation is conditional on A-002/A-003; if scale or deployment answers change, revisit.

## Part 3 — Authorisation enforcement points
Scope and permission are checked **server-side** at each of these; none may rely on UI hiding:
1. API request entry (one policy function: *actor, permission, target scope → allow/deny*).
2. Data access layer (row filtering by granted scopes) + RLS backstop.
3. Object-level access by ID (IDOR): resolve the object's scope first, then authorise — never fetch-then-trust.
4. Background jobs and scheduled tasks (carry actor + scope; re-authorise at execution, because grants may be revoked between enqueue and run).
5. Reports and exports (scope-filtered at query time; export permission separate from view).
6. File upload/download (authorised via the owning record's scope, not by key knowledge).
7. Integration callbacks/webhooks (verify authenticity, then resolve the owning connection's scope; idempotent).
8. Offline sync ingestion (re-authenticate and re-authorise each operation; Blueprint §7.1).
9. App lifecycle operations and app-originated calls (app permissions are a subset of, never above, the acting user's).
10. Platform-operator support access (Part 4).

## Part 4 — Platform operator separation (proposal, needs D-021)
- Operator identities are separate from tenant user identities and live outside any tenant.
- Default: operators have **no** access to tenant business data. Any support access is a time-limited, tenant-visible, audited grant — **whether to allow it at all is an owner/legal decision (D-021).**

## Out of scope here
User model and authentication (ASG-006; Django's user model must be fixed before the first migration, so `django.contrib.auth` stays uninstalled until then), exact permission catalogue, app entitlement semantics (D-023), accounting/inventory rules.

## Tests this model requires (to be built in ASG-006)
Cross-tenant and cross-branch read/write denial on API, report, export, file and job paths · IDOR by guessed ID · role-escalation attempts (granting a role above one's own) · scope-inheritance cases (branch/company/tenant-wide) · revoked-grant-between-enqueue-and-run · RLS bypass attempt through raw queries · missing-scope-context fails closed.

## Consequences if accepted
Follow-ups: ASG-005 (tenant/company/branch creation), ASG-006 (membership/roles/RLS + tests, incl. the RLS spike), identity/user-model ADR. Cost: RLS adds complexity to migrations, fixtures and testing; benefit: a second line of defence behind application bugs.

## Questions for the owner
D-024 approve/amend Option A (or choose B/C) · D-020 can one person hold memberships in several tenants? · D-021 is operator support access allowed, and under what controls? · D-022 who may assign tenant-wide grants? · D-023 are app entitlements granted per tenant or per company? · Confirm A-002 and A-003.

## Decision
*Pending owner.*

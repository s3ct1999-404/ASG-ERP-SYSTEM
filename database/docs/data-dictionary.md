# Data dictionary — scope of core entities

*Status: **PROPOSED**, tied to `docs/adr/0003-tenancy-scope-and-isolation.md` (not accepted). Covers the Blueprint §4 core entities only; business entities (products, ledgers, stock…) are added per vertical slice and must state their scope here **before** a table is created.*

**Scope classes:** `PLATFORM` (no tenant owner) · `TENANT` · `COMPANY` · `BRANCH` (see ADR-0003). Every non-`PLATFORM` row resolves all ancestors via constrained foreign keys. "Open" items point at the decision register (`docs/product/decision-register.md`).

| Entity | Scope class | Owner / key relationships | Notes and invariants | Open |
|---|---|---|---|---|
| Tenant | `PLATFORM` | — (it *is* the isolation boundary) | Globally unique, never-reused identifier (keeps a later move to per-tenant databases possible) | — |
| Company | `TENANT` | tenant | Legal/operational entity; scope node. Belongs to exactly one tenant | — |
| Branch | `COMPANY` | company (tenant resolved through company; constraint keeps them consistent) | Scope node. Belongs to exactly one company | — |
| User | `PLATFORM` (global identity) | — | Authenticated person. Holds **no** business access by itself; access arises only from Membership + MembershipScope | D-020 (one person in several tenants?) |
| Membership | `TENANT` | user × tenant | A user's presence in a tenant; grants nothing without scopes | D-020 |
| Role | `TENANT` | tenant | Mutable roles belong to one tenant. Platform-defined templates are **copied** into a tenant at provisioning so tenant edits cannot affect others (no mutable rows with a null tenant) | — |
| Permission | `PLATFORM` | owning app / platform module | Read-only catalogue of permission codes registered by modules and apps | — |
| RolePermission | `TENANT` | role × permission | Cannot reference a permission the tenant's installed apps do not provide | — |
| MembershipScope | `TENANT` | membership × role × scope node (tenant\|company\|branch) | The only source of access. Scope node must belong to the same tenant (constraint). Tenant-wide node = explicit high-privilege grant, audited | D-022 (who may assign tenant-wide) |
| App | `PLATFORM` | publisher | Registry record (stable ID) | — |
| AppVersion | `PLATFORM` | app | Manifest, dependencies, permissions, config schema, migrations, compatibility range | — |
| AppInstallation | `TENANT` | tenant × app version | Lifecycle state machine (Blueprint §3.1); audited | D-023 |
| AppEntitlement | `TENANT` (optionally narrowed to `COMPANY`) | tenant [× company] × app | Whether install/use is permitted | D-004, D-023 |
| AuditEvent | `TENANT` (+ nullable company/branch context); operator events are `PLATFORM` | actor, scope, outcome, safe record reference | **Append-only**: application DB role has no UPDATE/DELETE; no secrets/credentials/unneeded personal data; operator events live apart from tenant events so tenants can never read them through tenant policies | retention (D-014) |
| IntegrationConnection | `COMPANY` | company | Credentials held via secret manager reference, never raw in the row. Fiscal/tax connections are per legal company | Tenant-level gateways? (to decide per integration) |
| SyncOperation | inherits target entity's class (`COMPANY` or `BRANCH`) | tenant, company, branch?, user, device | Idempotency key and schema version required (Blueprint §7.1); re-authorised on every ingest | D-005 |
| FileMetadata | inherits owning record's scope | tenant always; owner type + id | Access decided by the owning record's scope, never by storage-key knowledge | — |
| WorkflowDefinition | `TENANT` (optionally `COMPANY` override) | tenant [× company] | Approval routes/thresholds | Company-specific rules? |
| WorkflowInstance | inherits subject record's scope | definition × subject | Immutable decision history | — |
| Notification | `TENANT` | recipient membership | Addressed to a membership; content must not leak data beyond the recipient's scope at read time | — |
| IdempotencyRecord | `TENANT` | tenant × actor × operation × key (unique) | Same key ⇒ same result, no second effect (Blueprint §6) | Retention period |
| Configuration | `TENANT` / `COMPANY` / `BRANCH` levels | node | Documented inheritance: most specific level wins, **only** for settings flagged overridable at that level; each setting declares its allowed levels | Which settings, per module |

## Global invariants (to be enforced by constraints/tests, not convention)
1. No tenant-owned row exists without its ancestors resolved and consistent.
2. No mutable row has a null tenant (platform data is read-only to tenants).
3. Access requires a MembershipScope; absence of a filter fails closed.
4. Tenant identifiers are never reused or reassigned.
5. AuditEvent rows cannot be modified or deleted through the application role.

## Change rule
Adding any table: state its scope class, owner keys, RLS policy intent and tests here first, in the same change as the migration.

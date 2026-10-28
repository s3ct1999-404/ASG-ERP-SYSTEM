# App Platform and Marketplace

*Canonical requirements: Blueprint §3.1, §9. Entitlement/trust decisions are open (D-004, D-015).*

## Registry record (required fields)
Stable ID, version, publisher, manifest, dependencies, permissions, configuration schema, migrations, compatibility range, lifecycle state.

## Lifecycle
States: available → installing → installed → upgrading → disabled → uninstalling → failed (modelled as a **state machine**, not booleans; exact transition table is ASG-014).
- Install validates dependencies, compatibility, permissions, configuration and migration plan.
- Upgrades are versioned/repeatable; migrations tested on realistic **synthetic** data.
- Disable stops UI and actions without corrupting shared data.
- Uninstall never auto-deletes accounting history or records other apps need; prefer archive/deactivation with an explicit retention policy.
- Dependency cycles rejected or deliberately handled; every lifecycle action audited.

## Security
Third-party code gets no unrestricted DB/tenant access; permissions are explicit, least-privilege, reviewable, revocable; code is verified/signed, scanned and reviewed before production publication. Threat model required before third-party execution.

## Templates (§9)
Versioned configuration packages, not forks; preview before apply; never silently destroy business data; customer data separate from template content. Only after underlying workflows are stable.

## Draft design (ASG-014 — PROPOSED, unapproved)
Machine-readable: `packages/contracts/app-manifest.schema.json`, `packages/contracts/app-lifecycle.json` (tested by `tests/contracts/`).

### Manifest (structural contract)
Fields: `manifest_version`, `id` (stable reverse-DNS, never reused), `name`, `version` (semver), `publisher`, `compatibility` (platform min/max), `dependencies` (id + version range), `permissions` (codes + descriptions), `configuration_schema`, `migrations` (id, reversible flag). **There is no code entry-point field**: how third-party code would run is undecided (D-015) and requires a threat model first.
Semantic checks done by the registry (not the schema): dependency graph is acyclic, permission codes are unique and namespaced to the app, versions resolve within the compatibility range, signature/publisher verified.

### Lifecycle state machine
States: `available`, `installing`, `installed`, `upgrading`, `disabled`, `uninstalling`, `failed`.
| From | Event | To |
|---|---|---|
| available | install requested (after validation passes) | installing |
| installing | succeeded / failed | installed / failed |
| installed | upgrade requested | upgrading |
| upgrading | succeeded / failed | installed / failed |
| installed | disable / (disabled) enable | disabled / installed |
| installed, disabled | uninstall requested | uninstalling |
| uninstalling | succeeded / failed | available / failed |
| failed | retry (only the failed operation's retry) | installing / upgrading / uninstalling |
Everything else is illegal (e.g. `available → installed`, `installing → uninstalling`). At most one lifecycle operation per (tenant, app) at a time. Validation failures at install request (dependencies, compatibility, permissions, configuration, migration plan) keep the app `available` and record errors plus an audit event.

### Rules this design commits to (from Blueprint §3.1)
- **Dependency cycles** are rejected at registration/install, with the cycle path in the error.
- **Uninstall retention:** uninstall never deletes accounting history, posted transactions, or records another app needs. Data is archived/deactivated and kept until an explicit retention policy (D-014) says otherwise.
- **Uninstall with dependents:** blocked while another installed app depends on it (proposal; owner to confirm).
- **Permissions:** an app's permissions are a subset of what was approved at install; an upgrade that adds permission codes needs re-approval; an app can never act above the invoking user's own scope (ADR-0003).
- **Audit:** every install/upgrade/disable/uninstall/failure/retry emits an audit event.

### Not decided (do not implement a guess)
Rollback vs forward-fix after a failed upgrade (Blueprint §22) · third-party execution model and sandboxing (D-015) · entitlement scope (D-023) · signing and review process · retention periods (D-014).

## Status
Design drafted as machine-readable contracts with tests (these show internal consistency, not that the rules are right). No registry or lifecycle implementation exists.

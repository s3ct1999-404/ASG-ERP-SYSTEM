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

## Status
Design only. No manifest schema or registry exists.

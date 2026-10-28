# Security

*Canonical baseline: Blueprint §10, §4, §6.4. Enforceable rules for sessions: `.claude/rules/security.md`.*

## Principles
Security is a release requirement. Deny by default; enforce authN/authZ and tenant/company/branch scope on the server everywhere (API, jobs, reports, exports, files); test cross-tenant access; use mature libraries, never custom crypto; keep secrets out of source, logs, prompts and bundles; validate input server-side; rate-limit sensitive endpoints; protect file upload/download; least privilege for users, apps, service accounts and MCP tools; separate dev/staging/prod credentials and data; synthetic data in prompts and fixtures; log security events without secrets.

## Required before milestones
- Threat model before public beta and before any third-party app execution.
- Data retention, export, correction, deletion and backup policy with legal review (D-014).

## Reporting vulnerabilities
Not yet defined — owner to provide a contact/process (add before any external pilot).

## Status
No code exists; no security tests exist. Nothing here is verified by test yet.

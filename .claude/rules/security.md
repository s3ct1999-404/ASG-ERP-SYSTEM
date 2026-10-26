# Security rules (Blueprint §10, §4)
- Deny by default. Enforce authentication **and** tenant/company/branch authorisation on the server for every API, job, report, export, file access and background task. Never infer access from tenant membership alone.
- Every feature touching tenant data ships with a cross-tenant and cross-branch denial test (incl. IDOR attempts).
- Use mature libraries for passwords/sessions/tokens; never invent cryptography.
- No secrets in source, logs, prompts, fixtures, client bundles or handoffs. `.env.example` holds placeholders only.
- Server-side validation is authoritative. Parameterised queries/ORM only. Encode output safely.
- Rate-limit sensitive endpoints. Validate upload type/size; scope file access.
- Audit events: who/what/when/scope/outcome/safe reference. Never log passwords, tokens, payment credentials or unnecessary personal data. Audit data must not be modifiable by ordinary users.
- Use synthetic data in prompts and fixtures. Least privilege for users, service accounts, app integrations and MCP tools.
- Third-party app code never gets unrestricted DB/tenant access.

# Testing rules (Blueprint §17, instructions §10)
- Define acceptance criteria first; add tests proportionate to the change (unit, integration, API/contract, e2e, security, offline/resilience, accounting, inventory, marketplace as relevant).
- Report each check as PASS / FAIL / NOT RUN / BLOCKED with the exact command. Never imply skipped checks passed. A green unit suite is not proof of end-to-end readiness.
- Required cases for high-value features: success, permission denial, cross-tenant denial, duplicate/idempotent retry, invalid input.
- Review the diff for secrets, access-control gaps, data loss and unintended changes before reporting.

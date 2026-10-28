# Module coverage matrix

Generated from `PROGRESS.md` (single source) on 2026-10-29. Labels: WORKING MVP, PARTIAL, SIMULATED, NOT IMPLEMENTED. No app is called complete on the basis of an empty shell.

| Blueprint app | Label | What exists | Not done |
|---|---|---|---|
| Platform admin / tenancy / identity / RBAC / audit | WORKING MVP (API; UI: sign-in, tenant switch, org view) | provision tenant, companies, branches, roles, scoped assignments, escalation block, RLS, immutable audit, login throttle | UI, email invitations, MFA, password reset |
| Master data | WORKING MVP (API; UI partial) | tax codes (user-entered, effective-dated), partners, products, warehouses, read-only UoM list | categories, UoM write, import |
| Inventory | WORKING MVP (API; UI: balances + idempotent receive) | receipts, adjustments, sale issue, weighted-average cost, no-negative-stock, immutable ledger, reconcile | transfers, counts, lots/serials, reorder |
| Sales | PARTIAL | invoices, payments, idempotent; UI: read-only invoice list with honest fiscal labels | quotations, orders, returns, credit notes |
| POS | PARTIAL | one idempotent sale+tender operation, branch scope | till sessions, cash-up, returns, receipts printing |
| Accounting | PARTIAL | seeded chart (needs review), balanced posting (DB-enforced), reversal, period close, trial balance, statements | AP/purchases, bank reconciliation, manual period reopen UX |
| EFRIS / fiscalisation | SIMULATED | provider contract, status machine, retries, reconcile, worker, redaction, simulator, honest labels | real URA wire format, sandbox, credit notes, cancellations |
| Offline sync | PARTIAL | server-side idempotency on invoices/payments/receipts | client outbox, sync endpoint/status API, conflict UI |
| Reporting | PARTIAL | trial balance, statements | dashboards, exports, scheduled reports |
| App marketplace / lifecycle | NOT IMPLEMENTED | contracts only (ADR/APP_PLATFORM.md) | registry, install state machine |
| HR, Projects/tasks, Documents/approvals, Fleet, Notifications | NOT IMPLEMENTED | none | everything |

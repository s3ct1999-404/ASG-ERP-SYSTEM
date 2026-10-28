# Requirements Register

*Status: **draft** — derived mechanically from the Blueprint; not yet approved (Stage 0 gate). Task register is in `PROGRESS.md` (canonical). Acceptance criteria below are observable statements taken from or implied by the cited Blueprint section; **no business, accounting, tax or compliance rule has been invented** — undecided items point to the decision register.*

Priority: P0 foundational/blocking · P1 core · P2 later. Status values as in `PROGRESS.md`. All currently `NOT STARTED`.

| ID | Requirement | Pri | Source | Depends on | Acceptance criteria (draft) |
|---|---|---|---|---|---|
| TEN-001 | Separate platform operator, tenant, company, branch, user, role/permission, entitlement, configuration | P0 | §4 | ASG-002 | Data dictionary states scope for each entity; no blanket `tenant_id` assumption |
| TEN-002 | Membership never implies access to all companies/branches | P0 | §4, §10 | TEN-001 | Test: user scoped to branch A is denied branch B and other tenants on API, report, export, file, job |
| SEC-001 | Server-side authN/authZ on every relevant API/job/report/export/file/task; deny by default | P0 | §4, §10 | TEN-001 | Automated denial tests for each surface |
| SEC-002 | No secrets in source/logs/prompts/bundles; `.env.example` placeholders only | P0 | §10 | ASG-004 | Secret scan in CI passes; sample env contains placeholders only |
| SEC-003 | Audit events (who/what/when/scope/outcome/safe ref), tamper-resistant to ordinary users | P0 | §6.4 | TEN-001 | Event recorded for each privileged action; ordinary user cannot edit/delete; no secrets logged |
| SEC-004 | Threat model before public beta and before third-party app execution | P1 | §10 | — | Threat-model document reviewed before those milestones |
| ACC-001 | Double-entry: debits = credits per posted entry | P0 | §6.1 | ASG-010, D-008 | Test rejects unbalanced entry |
| ACC-002 | Posted entries immutable except controlled reversal/correction | P0 | §6.1 | ACC-001 | Edit/delete of posted entry rejected; reversal creates linked entries |
| ACC-003 | Explicit currency precision and rounding | P0 | §6.1 | D-007 | Rule documented; tests cover rounding |
| ACC-004 | Idempotency keys for payments and external callbacks | P0 | §6.1 | — | Replay of same key produces no second effect |
| ACC-005 | Period close/reopen requires permission and audit | P1 | §6.1 | D-008 | Unpermitted close denied; audit entry exists |
| ACC-006 | Tax rates/rules effective-dated configuration, not hard-coded | P1 | §6.1, §8 | D-011, ASG-015 | No tax rate literal in code; config has effective dates |
| INV-001 | Traceable stock movement ledger; balance reconcilable to movements | P0 | §6.2 | ASG-008 | Reconciliation test: balance == sum(movements) |
| INV-002 | Idempotent receipt: same key does not double quantity | P0 | §6.2, §16 | INV-001 | Duplicate-key test |
| INV-003 | Concurrent sales/transfers cannot oversell or double-consume | P0 | §6.2 | INV-001, D-009 | Concurrency test |
| INV-004 | Corrections are adjustment movements, not edits | P1 | §6.2 | INV-001 | Test: history preserved |
| INV-005 | Costing and negative-stock policy defined | P0 | §6.2 | D-009 | Decision recorded before implementation |
| SAL-001 | Distinct quotation/order/fulfilment/invoice/payment/return/credit-note states via state machine | P1 | §6.3 | ASG-009 | Invalid transitions rejected |
| POS-001 | Explicit till/session lifecycle and cash reconciliation | P1 | §6.3 | D-010 | Session lifecycle tests |
| POS-002 | Receipts distinguish locally captured / server accepted / externally fiscalised | P0 | §6.3, §7.6 | D-011 | State shown and persisted; never labelled fiscalised without confirmation |
| OFF-001 | Action queued only after durable local commit of action + outbox | P0 | §7.1 | ASG-012 | Restart-survival test |
| OFF-002 | Unique operation ID/idempotency key, scope, schema version, timestamp, retry state | P0 | §7.1 | OFF-001 | Duplicate-delivery test |
| OFF-003 | Statuses: pending, syncing, synced, conflict, failed, needs_attention; transitions/retries defined | P0 | §7.2 | ASG-012 | Transition table + tests |
| OFF-004 | Per-entity conflict policy; no blanket last-write-wins for accounting/stock/payments/approvals | P0 | §7.3 | ASG-012 | Policy doc + conflict tests |
| OFF-005 | Rejections/conflicts remain visible and recoverable | P0 | §7.1 | OFF-003 | UI/e2e test |
| OFF-006 | Offline limits, stale data, permission revocation, lost-device handling documented | P1 | §7.4 | D-005 | Document reviewed |
| APP-001 | App registry: stable ID, version, publisher, manifest, deps, permissions, config schema, migrations, compat range, lifecycle state | P1 | §3.1 | ASG-014 | Schema + registry tests |
| APP-002 | Explicit lifecycle state machine (available/installing/installed/upgrading/disabled/uninstalling/failed) | P1 | §3.1 | APP-001 | Illegal transition tests |
| APP-003 | Uninstall never deletes accounting history or records other apps need | P0 | §3.1 | APP-002 | Retention test |
| APP-004 | Dependency cycles rejected/handled; install/update/uninstall audited | P1 | §3.1 | APP-001 | Cycle test; audit test |
| APP-005 | Third-party code has no unrestricted DB/tenant access; trust model decided | P0 | §3.1, §10 | D-015 | Decision + sandbox/permission tests |
| TPL-001 | Templates are versioned config packages; preview before apply; no silent data destruction | P2 | §9 | Stage 7 | Preview + non-destructive-apply tests |
| CMP-001 | Uganda compliance records with official source, date, category, impact, evidence, open questions | P1 | §8 | ASG-015 | Records complete; sources official |
| CMP-002 | No compliance claim without verification evidence | P0 | §7.6, §8 | — | Review checklist |
| CUS-001 | Customer/supplier records can hold BRN, NIN and TIN identifiers (URA's Aug 2026 notice says EFRIS documents must carry the buyer's identifier). **PENDING compliance review** — do not finalise the data contract until EF-004 is reviewed | P1 | `docs/compliance/uganda/efris-requirements.md` EF-004 | ASG-007, ASG-015 | Data contract lists identifier fields, validation rules per reviewed source |
| TAX-001 | Tax rates, thresholds, exemptions and sector rules are effective-dated configuration applied by tax-point date, never code constants. **Strengthened by evidence:** Uganda's FY2026/27 amendments changed tax rules on 1 July 2026, with conflicting reports on their status | P0 | §6.1, §8; TX-001/TX-002 | ASG-015, D-008 | No tax literal in code (scanner/test); config has effective dates; a document uses the config effective at its tax point |
| NFR-001 | Critical user journeys pass e2e tests | P1 | §2.3 | Stage 4 | e2e results |
| NFR-002 | No cross-tenant exposure in automated security tests | P0 | §2.3 | TEN-002 | Security suite passes |
| NFR-003 | Migrations apply and roll forward in test env | P1 | §2.3 | ASG-004 | CI migration check |
| NFR-004 | New developer can run project from docs | P1 | §2.3 | ASG-004 | Clean-checkout walkthrough |
| NFR-005 | Backups restorable in a rehearsal | P1 | §2.3, §22 | Stage 9 | Restore rehearsal record |

Module-level functional requirements (inventory, sales, HR, projects, fleet, documents, reporting) will be added per vertical slice after the Stage 0 gate — not before.

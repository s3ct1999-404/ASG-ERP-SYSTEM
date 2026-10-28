# Database and data-integrity rules (Blueprint §6, §4)
- Schema changes only via reviewed, versioned migrations. Never run destructive migrations or drop data without explicit approval and a recovery plan.
- Define tenant/company/branch ownership **per entity** in the data dictionary; do not add a generic `tenant_id` blindly.
- Accounting: balanced double-entry; posted entries never silently edited/deleted — use reversal/correction; explicit currency precision and rounding; period close/reopen needs permission + audit; **no posting/tax rule is invented — use approved rules only**.
- Inventory: every change is a stock-movement ledger entry; balances reconcilable to movements; corrections are adjustment movements; concurrency must not oversell or double-consume.
- Payments and retryable external operations use idempotency keys.
- Uninstalling an app never deletes accounting history or records other apps need.

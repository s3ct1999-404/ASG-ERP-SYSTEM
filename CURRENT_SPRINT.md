# Current sprint

## Active task
Stage E/F continuation: apply the new migrations to Supabase, then offline sync API, app lifecycle, remaining apps' smallest honest cores, UI, packaging.

## Done this sprint (evidence in PROGRESS.md)
ASG-005/006 platform core; ASG-007/008/009/010/011 domain slice (master data, stock ledger, sales, accounting, e2e); ASG-015 research addendum + fiscal boundary.

## Acceptance for the next bounded task (apply to Supabase)
1. Each pending Django migration applied to `hcpzsprnrhpfnodvzals` via MCP, in order, with a `django_migrations` row.
2. `list_tables` shows RLS enabled on every table; `get_advisors` security run and findings recorded.
3. A rolled-back behavioural test on Supabase proves isolation for a domain table and immutability of the journal.

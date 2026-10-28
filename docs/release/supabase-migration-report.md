# Supabase migration report

Project: `hcpzsprnrhpfnodvzals` ("ASG-DEVS-ERP Project", eu-west-1, Postgres 17). Identity verified via `list_projects` before any write.
Date: 2026-10-28. Source of truth: Django migration files in `services/api/*/migrations/`. SQL was generated with `manage.py sqlmigrate` (no hand-authored schema), with the matching `django_migrations` row inserted in the same atomic call so ledger and schema cannot diverge.

## Before
Supabase ledger held identity 0001-0002, tenancy 0001-0002, audit 0001-0002 (6 rows), 10 tables, all empty. Matched the handoff exactly.

## Applied (Supabase migration name -> Django migrations)
| Supabase migration | Django migrations | Depends on |
|---|---|---|
| masterdata_0001_initial | masterdata.0001 | tenancy.0002 |
| masterdata_0002_rls | masterdata.0002 | masterdata.0001 |
| accounting_0001_initial | accounting.0001 | tenancy.0002 |
| accounting_0002_rls_immutable_balanced | accounting.0002 | accounting.0001 |
| inventory_0001_0002_initial | inventory.0001, 0002 | masterdata.0001 |
| inventory_0003_rls_immutable_ledger | inventory.0003 | inventory.0002 |
| sales_0001_0003_invoices_payments_rls_fiscal_states | sales.0001, 0002, 0003 | masterdata.0001 |
| fiscal_0001_0002_efris_boundary_rls | fiscal.0001, 0002 | sales.0002 |

All additive (new tables/constraints/policies/triggers). The only `DROP` statements are idempotent `DROP POLICY/TRIGGER IF EXISTS` guards. Recovery if ever needed: tables were empty at apply time; drop the new tables in reverse dependency order (fiscal, sales, inventory, accounting, masterdata) and delete their `django_migrations` rows. Forward-fix is preferred.

## After (verified by queries, not assumed)
- Live ledger: 18 rows; names identical to the 18 migrations in the repository head (`showmigrations --plan`).
- 28 application tables, 28 with RLS enabled, 27 policies, 0 tables with RLS off.
- Tables with RLS but no policy: `django_migrations`, `identity_authtoken` (deny-all by design; tokens/passwords readable only by the owner role in `system_mode()`, see `identity/migrations/0002_rls_lockdown.py`). Supabase advisor reports exactly these two as INFO (`rls_enabled_no_policy`); no WARN/ERROR lints.
- Zero `anon`/`authenticated` grants on application tables.
- Append-only triggers on: accounting_journalentry, accounting_journalline, inventory_stockmovement, sales_invoiceline, sales_payment, fiscal_fiscalattempt. Deferred balanced-journal constraint trigger present.
- Behavioural test (synthetic data, forced rollback, no residue; tenants/products/journals = 0 afterwards): 13/13 PASS: balanced entry accepted; unbalanced rejected; journal update and line delete blocked; overpayment blocked; invalid fiscal status blocked; simulated document cannot be FISCALISED; zero-qty stock movement blocked; asg_app sees only own tenant rows; cross-tenant insert blocked; cross-tenant update affects 0 rows; no tenant bound sees 0 rows; asg_app denied auth tokens.

## Not covered here
- Performance advisors not yet reviewed. No data seeded (by design).
- Fresh-database repeatability: repo suite (76 tests) builds a test DB from migrations on local PG16 and passes.
- Backup/restore rehearsal: NOT RUN.
- Future migrations (sync, app registry, new business apps) must follow the same procedure.

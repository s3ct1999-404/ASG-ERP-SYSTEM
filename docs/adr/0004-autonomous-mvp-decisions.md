# ADR-0004: Decisions taken under the owner's autonomous-delivery authorisation

- Status: **Accepted (agent-decided under owner authorisation of 2026-10-27; owner may amend)**
- Supersedes: the "Proposed" state of ADR-0003 (accepted here, with the implementation notes below)
- Basis: `ASG_ERP_AGENT_INSTRUCTIONS.md` §2 and the task card §2/§8 (decide safely, record, continue)

Every decision below is the *least surprising secure option consistent with the Blueprint*, is **configurable or reversible**, and is listed so the owner can override it. None of these is a legal or accounting sign-off: items marked **needs review** must be reviewed by a qualified accountant/lawyer before real customer use.

| ID | Decision | Rationale / reversibility |
|---|---|---|
| D-001 | First segment: **VAT-registered retail/wholesale trading SMEs in Uganda** (one pilot template `retail-trade`, packaged later). EFRIS treated as mandatory for this segment. | Exercises the whole slice (stock→sale→POS→tax→accounting). Template is data, not a fork. |
| D-002/D-013 | Cloud-hosted, containerised; modest pilot scale (A-002/A-003 confirmed as working assumptions). | Required by ADR-0003's RLS option; revisit before >100 tenants. |
| D-005 | Offline in release 1 (matrix in `OFFLINE_SYNC.md`): **POS sale capture** and **goods receipt** and **customer payment receipt**. Everything else online-only. Fiscal state of an offline sale stays `PENDING_FISCALISATION` until an authoritative response. | Smallest set that is useful offline and safe under idempotency. |
| D-007 | **Single base currency per company, default UGX (0 minor-unit decimals for display, stored as `NUMERIC(20,2)`)**; rounding = half-up to 2 dp at line level, tax computed per line. Multi-currency deferred. | Avoids FX accounting. **Needs accounting review.** |
| D-008 | Seeded **starter chart of accounts and posting rules, marked `requires_review`**; monthly fiscal periods; double-entry enforced in DB and service; posted entries immutable (DB trigger), corrected only by reversal. | Blueprint §6.1. **Needs accounting review before real books.** |
| D-009 | Costing: **weighted average**; **negative stock disallowed** by default (company setting). | Simple, auditable. Policy is a setting. **Needs review.** |
| D-010 | Payment methods: cash, mobile money, card, bank transfer (tender types are data). | Typical Uganda retail. |
| D-016 | Blueprint deletion on `main` treated as **unintentional**; canonical copy kept at `docs/ASG_ERP_MASTER_BLUEPRINT.md`, restored by a normal commit. | Instructions §4 require preservation. |
| D-018 | Agent may commit to feature branches and push **when credentials exist**. In the build sandbox **no GitHub credential exists**, so pushing is a genuine human-dependent step (see PROGRESS.md). | Not a policy choice; an access fact. |
| D-020 | One person may hold memberships in several tenants (global `User`, per-tenant `Membership`). | ADR-0003 proposal. |
| D-021 | **Platform operators have no access to tenant business data.** Operator role only provisions tenants. Support access is deferred and would need a new ADR (time-boxed, consented, audited). | Privacy default. |
| D-022 | Only the tenant `Owner` role (permission `tenancy.manage_access`) may assign tenant-wide roles; branch/company managers may assign only within their scope. | Prevents privilege escalation. |
| D-023 | Entitlements are **per tenant** (`AppEntitlement`), company-level restriction deferred. | Simplest; extend later without data loss. |
| D-024 | **Accepted: shared schema + PostgreSQL RLS** (option A). | See below. |

## Implementation notes for D-024 (verified by tests, see `tests/test_rls.py`)
- Two database modes: *system mode* (the migration/owner role; used for authentication, tenant provisioning, platform jobs) and *tenant mode* (`SET ROLE asg_app` + transaction-local `app.tenant_id`). `asg_app` is `NOLOGIN`, not owner, no `BYPASSRLS`, so RLS applies to it. Every tenant-owned table has `tenant_id` and an RLS policy on it.
- RLS is defence in depth. **Company/branch scope is enforced in the service/API layer** (permission + scope check on every request); RLS only guarantees tenant isolation even if application code has a bug.
- Authentication: Django custom user model (`identity.User`, email login, Django password hashers) + our own hashed bearer tokens. **Supabase Auth is not used** (no second identity system).
- The Supabase `postgres` role bypasses RLS; the application must therefore always switch to `asg_app` for tenant work. The Supabase REST/anon API is **not** used and PostgREST roles (`anon`, `authenticated`) get no grants on ERP tables; RLS is also enabled so they could not read anything even if granted.

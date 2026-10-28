# Offline and Synchronisation

*Canonical contract: Blueprint §7. Rules for sessions: `.claude/rules/offline-sync.md`. Offline is a product capability with a written contract, not browser caching.*

## Flow (Blueprint §7.1, summary)
Check offline capability and download permitted reference data → validate locally → commit action **and** outbox record in one local transaction before saying "queued" → each operation carries unique ID/idempotency key, scope, schema version, timestamp, retry state → on reconnect send in dependency order → server re-authenticates, re-authorises, validates, applies idempotently, returns authoritative result → client records acknowledgement → rejections/conflicts stay visible and recoverable.

## Statuses, transitions, retry rules (ASG-012 — PROPOSED, unapproved)
Machine-readable: `packages/contracts/sync-operation-status.json` (tested by `tests/contracts/`).
| From | Event | To |
|---|---|---|
| pending | send started | syncing |
| syncing | server accepted | synced (terminal) |
| syncing | transient failure (timeout/network) | pending (retry) |
| syncing | permanent server rejection | failed (terminal, stays visible with reason) |
| syncing | server reports conflict | conflict |
| syncing | retries exhausted | needs_attention |
| conflict | resolved and resubmitted | pending |
| conflict | needs user decision | needs_attention |
| needs_attention | user retries | pending |
| needs_attention | user marks unrecoverable | failed |
Rules: every retry reuses the same operation ID/idempotency key · a timeout after a possible commit is retried with the same key and the server returns the recorded result, never applying twice · expired auth **pauses the whole queue** (operations stay pending) rather than failing them · a corrected action after `failed` is a **new** operation linked to the original · an operation whose dependency is failed/conflicted/needs-attention stays pending with a recorded blocked reason · conflicts can only be resolved or escalated, never dropped. Backoff is exponential with jitter; **maximum attempts and delays are not decided** (sync ADR).

## Outbox record contract (proposed fields)
`operation_id` (UUID, doubles as idempotency key) · `type` · `schema_version` · scope (`tenant`, `company`, `branch?`) · `actor` · `device_id` · `created_at_client` (advisory only — the server's clock is authoritative) · `payload` · `depends_on[]` · `status` · `attempt_count` · `next_attempt_at` · `last_error` (safe text, no secrets) · `server_result_ref`. The record and the business action it describes are written in **one local transaction**.

## Conflict policy
Per entity and operation, defined in ASG-012. Never blanket last-write-wins for accounting, stock, payments or approvals.

## Offline action matrix (ASG-012 — **blocked on D-005**)
The Blueprint fixes constraints, not which actions go offline in release 1. Candidates below are **undecided**; the owner picks (D-005), then each chosen row needs a conflict policy and reference-data list.
| Candidate action | Blueprint constraint | Offline in release 1? | Conflict policy | Reference data needed |
|---|---|---|---|---|
| Record POS sale | Receipt must not claim server-accepted/fiscalised (§6.3, §7.6); payments idempotent | *undecided* | *undecided* | *undecided* |
| Receive stock | Movement recorded once; idempotent (§6.2) | *undecided* | *undecided* | *undecided* |
| Stock adjustment | Traceable movement, no history edits | *undecided* | *undecided* | *undecided* |
| Record payment/receipt | Idempotent; never last-write-wins | *undecided* | *undecided* | *undecided* |
| Create customer / product | — | *undecided* | *undecided* | *undecided* |
| Approve a document | Never last-write-wins | *undecided* | *undecided* | *undecided* |
| Edit/delete a posted accounting entry | Not allowed at all (§6.1) — reversal only | **No** (fixed by Blueprint) | n/a | n/a |

## Fiscal honesty (Blueprint §7.6)
A document is locally created, submitted, accepted, rejected, or awaiting confirmation — never presented as officially fiscalised without confirmation. Scope depends on verified requirements (D-011).

## Not yet defined
Offline limits, stale-data display, permission revocation, lost-device handling, local storage choice (depends on ADR-0003 mobile/desktop). Test list: Blueprint §7.5.

## Status
Design only; nothing implemented or tested.

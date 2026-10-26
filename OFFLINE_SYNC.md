# Offline and Synchronisation

*Canonical contract: Blueprint §7. Rules for sessions: `.claude/rules/offline-sync.md`. Offline is a product capability with a written contract, not browser caching.*

## Flow (Blueprint §7.1, summary)
Check offline capability and download permitted reference data → validate locally → commit action **and** outbox record in one local transaction before saying "queued" → each operation carries unique ID/idempotency key, scope, schema version, timestamp, retry state → on reconnect send in dependency order → server re-authenticates, re-authorises, validates, applies idempotently, returns authoritative result → client records acknowledgement → rejections/conflicts stay visible and recoverable.

## Statuses
pending · syncing · synced · conflict · failed · needs_attention. Transition table and retry rules: **to be defined (ASG-012)**.

## Conflict policy
Per entity and operation, defined in ASG-012. Never blanket last-write-wins for accounting, stock, payments or approvals.

## Fiscal honesty (Blueprint §7.6)
A document is locally created, submitted, accepted, rejected, or awaiting confirmation — never presented as officially fiscalised without confirmation. Scope depends on verified requirements (D-011).

## Not yet defined
Offline action matrix (D-005), offline limits, stale-data display, permission revocation, lost-device handling, local storage choice (depends on ADR-0003 mobile/desktop). Test list: Blueprint §7.5.

## Status
Design only; nothing implemented or tested.

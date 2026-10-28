# Offline and sync rules (Blueprint §7)
- An action is "queued" only after the action and its outbox record commit in one local transaction.
- Each operation carries a unique ID/idempotency key, scope, schema version, timestamp and retry state.
- Server re-authenticates, re-authorises, validates and applies idempotently; its response is authoritative.
- Statuses at minimum: pending, syncing, synced, conflict, failed, needs_attention — transitions and retry rules documented.
- Conflicts/rejections stay visible and recoverable; never silently discarded.
- **No blanket last-write-wins** for accounting, stock, payments or approvals.
- Never present a locally captured document as server-accepted or externally fiscalised.
- Document offline limits, stale-data display, permission revocation and lost-device handling.

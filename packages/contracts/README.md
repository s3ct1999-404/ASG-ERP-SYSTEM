# packages/contracts

Machine-readable contracts shared by services and clients. **All DRAFT and unapproved** until their tasks move to DONE in `PROGRESS.md`.

| File | Task | Purpose |
|---|---|---|
| `app-manifest.schema.json` | ASG-014 | Structural schema for app manifests (JSON Schema 2020-12) |
| `app-lifecycle.json` | ASG-014 | App lifecycle state machine (states + allowed transitions) |
| `sync-operation-status.json` | ASG-012 | Offline operation statuses, transitions and retry rules |

Self-consistency tests: `tests/contracts/`. The REST contract itself lives in `docs/api/openapi.yaml`.

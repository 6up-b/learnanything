---
title: "reader_capture_outbox"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite reader_capture_outbox"
  - "table reader_capture_outbox"
schema_head: 157
table_name: "reader_capture_outbox"
table_role: "workflow"
functionality_status: "active"
domain_family: "reader"
introduced_in: "091_interaction_events_reader_envelope.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/091_interaction_events_reader_envelope.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/reader/reader_capture.py"
  - "src/learnloop/content/sources/source_deletion.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/reader"
---

# `reader_capture_outbox`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives reader capture outbox a stable database identity so reader interactions remain anchored to durable source content as extraction and rendering evolve. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `annotation_id`, `commitment_id`, `source_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> The durable local-first capture outbox (§5.3, §15.2).

It belongs to the **reader** navigation family. The family context lives in [[Database Catalog#Reader]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/091_interaction_events_reader_envelope.sql`.
- **Schema touched by:** `091_interaction_events_reader_envelope.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `client_idempotency_key` | `TEXT` | yes | — | — | Stored value |
| `capture_kind` | `TEXT` | yes | — | — | Stored value |
| `state` | `TEXT` | yes | `'pending'` | — | Stored value |
| `payload_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `annotation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `commitment_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `source_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `revision_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `render_view_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `interaction_event_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `target_ref` | `TEXT` | no | — | — | Stored value |
| `attempts` | `INTEGER` | yes | `0` | — | Stored value |
| `last_error` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `drained_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_reader_capture_outbox_state` on `state`, `created_at`.
- `sqlite_autoindex_reader_capture_outbox_2` on `client_idempotency_key` (unique).
- `sqlite_autoindex_reader_capture_outbox_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.capture_by_client_key()`
- `Repository.capture_local_transaction()`
- `Repository.delete_source_artifact()`
- `Repository.get_capture_outbox()`
- `Repository.mark_capture_outbox()`
- `Repository.pending_capture_outbox()`
- `Repository.recoverable_capture_outbox()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/reader/reader_capture.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_reader_capture.py`

Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.

## Extension and modification guidance

1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.
2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.
3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.
4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.

## Live schema DDL

> [!tip] Why keep the DDL here?
> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.

```sql
CREATE TABLE reader_capture_outbox (
  id TEXT PRIMARY KEY,
  client_idempotency_key TEXT NOT NULL UNIQUE,
  capture_kind TEXT NOT NULL
    CHECK (capture_kind IN ('annotation', 'flashcard_intent', 'question_intent')),
  state TEXT NOT NULL DEFAULT 'pending'
    CHECK (state IN ('pending', 'draining', 'done', 'failed')),
  payload_json TEXT NOT NULL DEFAULT '{}',
  annotation_id TEXT,
  commitment_id TEXT,
  source_id TEXT,
  revision_id TEXT,
  render_view_id TEXT,
  interaction_event_id TEXT,
  target_ref TEXT,
  attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  drained_at TEXT
);
```

## Related notes

- [[Database Catalog#Reader|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

---
title: "attention_block_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite attention_block_events"
  - "table attention_block_events"
schema_head: 156
table_name: "attention_block_events"
table_role: "receipt"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "096_controller_snapshots.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/096_controller_snapshots.sql"
  - "src/learnloop/scheduling/controller_store.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `attention_block_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of attention block so queue and controller decisions can resume safely and explain why an activity was selected. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `block_id`, `event_ordinal`, `kind`, making the operational relationship explicit. ^table-purpose

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/096_controller_snapshots.sql`.
- **Schema touched by:** `096_controller_snapshots.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `block_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/attention_blocks\|attention_blocks.id]] | Stored value |
| `event_ordinal` | `INTEGER` | yes | — | — | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `detail_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `block_id` → [[Reference/Database/Tables/attention_blocks|`attention_blocks.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_attention_block_events_block` on `block_id`, `event_ordinal`.
- `sqlite_autoindex_attention_block_events_2` on `block_id`, `event_ordinal` (unique).
- `sqlite_autoindex_attention_block_events_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/scheduling/controller_store.py`

### Direct SQL writers

- `src/learnloop/scheduling/controller_store.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`

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
CREATE TABLE attention_block_events (
  id TEXT PRIMARY KEY,
  block_id TEXT NOT NULL REFERENCES attention_blocks(id),
  event_ordinal INTEGER NOT NULL,
  kind TEXT NOT NULL,
  detail_json TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(block_id, event_ordinal)
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

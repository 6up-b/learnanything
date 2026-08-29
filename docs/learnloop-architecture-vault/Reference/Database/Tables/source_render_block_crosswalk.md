---
title: "source_render_block_crosswalk"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite source_render_block_crosswalk"
  - "table source_render_block_crosswalk"
schema_head: 156
table_name: "source_render_block_crosswalk"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "088_source_render_views.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/088_source_render_views.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/sources/source_deletion.py"
  - "src/learnloop/reader/annotations.py"
  - "src/learnloop/reader/source_render_views.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_render_block_crosswalk`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives source render block crosswalk a stable database identity so canonical-source work can be retried without losing provenance or silently changing its input set. It supplies replay-stable input rather than a disposable cache. Rows bind `render_view_id`, `display_node_id`, `extraction_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/088_source_render_views.sql`.
- **Schema touched by:** `088_source_render_views.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `render_view_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/source_render_views\|source_render_views.id]] | Stored value |
| `display_node_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `display_ordinal` | `INTEGER` | yes | — | — | Stored value |
| `extraction_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `span_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `block_content_hash` | `TEXT` | no | — | — | Stored value |
| `block_ordinal` | `INTEGER` | no | — | — | Stored value |
| `display_start` | `INTEGER` | no | — | — | Stored value |
| `display_end` | `INTEGER` | no | — | — | Stored value |
| `katex_node_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `asset_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | `'mapped'` | — | Stored value |
| `reason` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `render_view_id` → [[Reference/Database/Tables/source_render_views|`source_render_views.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_render_crosswalk_span` on `render_view_id`, `span_id`.
- `idx_render_crosswalk_view` on `render_view_id`, `display_ordinal`.
- `sqlite_autoindex_source_render_block_crosswalk_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.delete_source_artifact()`
- `Repository.insert_render_crosswalk_nodes()`
- `Repository.render_crosswalk()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/reader/annotations.py`
- `src/learnloop/reader/source_render_views.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

No table-specific test contains the table name or a detected repository method call. The schema/role invariants are still pinned by `tests/test_migrations.py` and `tests/test_table_roles.py`.

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
CREATE TABLE source_render_block_crosswalk (
  id TEXT PRIMARY KEY,
  render_view_id TEXT NOT NULL REFERENCES source_render_views(id),
  display_node_id TEXT NOT NULL,
  display_ordinal INTEGER NOT NULL,
  extraction_id TEXT NOT NULL,
  span_id TEXT,
  block_content_hash TEXT,
  block_ordinal INTEGER,
  display_start INTEGER,
  display_end INTEGER,
  katex_node_ids_json TEXT NOT NULL DEFAULT '[]',
  asset_ids_json TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'mapped'
    CHECK (status IN ('mapped', 'unmapped', 'ambiguous')),
  reason TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

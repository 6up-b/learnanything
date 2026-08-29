---
title: "source_block_health"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite source_block_health"
  - "table source_block_health"
schema_head: 156
table_name: "source_block_health"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "089_source_block_health.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/089_source_block_health.sql"
  - "src/learnloop/content/sources/block_health.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/sources/source_deletion.py"
  - "src/learnloop/reader/source_render_views.py"
  - "src/learnloop_sidecar/handlers/reader.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_block_health`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives source block health a stable database identity so canonical-source work can be retried without losing provenance or silently changing its input set. It supplies replay-stable input rather than a disposable cache. Rows bind `extraction_id`, `span_id`, `analyzer_version`, making the operational relationship explicit. ^table-purpose

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/089_source_block_health.sql`.
- **Schema touched by:** `089_source_block_health.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `extraction_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/source_extraction_runs\|source_extraction_runs.id]] | Stored value |
| `span_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `analyzer_version` | `TEXT` | yes | — | — | Stored value |
| `status` | `TEXT` | yes | `'unknown'` | — | Stored value |
| `reason_flags_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `signal_provenance_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `confidence` | `REAL` | no | — | — | Stored value |
| `page_health_flags_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `recommended_view` | `TEXT` | yes | `'derived'` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `extraction_id` → [[Reference/Database/Tables/source_extraction_runs|`source_extraction_runs.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_source_block_health_extraction` on `extraction_id`.
- `sqlite_autoindex_source_block_health_2` on `extraction_id`, `span_id`, `analyzer_version` (unique).
- `sqlite_autoindex_source_block_health_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.block_health()`
- `Repository.block_health_for_extraction()`
- `Repository.delete_source_artifact()`
- `Repository.upsert_block_health()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/reader/source_render_views.py`
- `src/learnloop_sidecar/handlers/reader.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_table_roles.py`

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
CREATE TABLE source_block_health (
  id TEXT PRIMARY KEY,
  extraction_id TEXT NOT NULL REFERENCES source_extraction_runs(id),
  span_id TEXT NOT NULL,
  analyzer_version TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'unknown'
    CHECK (status IN ('ok', 'suspect', 'failed', 'unknown')),
  reason_flags_json TEXT NOT NULL DEFAULT '[]',
  signal_provenance_json TEXT NOT NULL DEFAULT '{}',
  confidence REAL,
  page_health_flags_json TEXT NOT NULL DEFAULT '[]',
  recommended_view TEXT NOT NULL DEFAULT 'derived'
    CHECK (recommended_view IN ('derived', 'crop_adjacent', 'crop_default', 'warn_link')),
  created_at TEXT NOT NULL,
  UNIQUE(extraction_id, span_id, analyzer_version)
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

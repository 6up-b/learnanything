---
title: "source_held_out_signal_marks"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "e086fc460dc148f693f76731741d0229ddb8f942"
source_commit_timestamp: "2026-10-20T14:05:23-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite source_held_out_signal_marks"
  - "table source_held_out_signal_marks"
schema_head: 215
table_name: "source_held_out_signal_marks"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "204_source_held_out_signal_marks.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/204_source_held_out_signal_marks.sql"
  - "src/learnloop/content/sources/exam_material.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/db/stores/held_out_signals.py"
  - "src/learnloop/content/sources/source_deletion.py"
  - "src/learnloop/content/synthesis/source_unit_inventory.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_held_out_signal_marks`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Keeps each held-out assessment signal on the reading its model run read (exam protection by extraction identity, migration 204): one row per fresh inventory that held anything out, with the extraction and revision it read, the unit, the role it ran under and the sorted span ids. `content.sources.exam_material` reads protection from it, never from `source_unit_inventories`, whose cache rows a reuse rebinds to another reading. A reuse writes no row. Backfilled rows from rebound cache rows name no reading (`extraction_id` NULL): their book stays protected and they mark no reading. Append-only (an update aborts); deleted only with its book. It supplies replay-stable input rather than a disposable cache. Rows bind `revision_id`, `extraction_id`, `unit_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/204_source_held_out_signal_marks.sql`.
- **Schema touched by:** `204_source_held_out_signal_marks.sql`, `205_write_provenance.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `revision_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/source_revisions\|source_revisions.id]] | Stored value |
| `extraction_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/source_extraction_runs\|source_extraction_runs.id]] | Stored value |
| `unit_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `inventory_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `made_as_role` | `TEXT` | no | — | — | Stored value |
| `span_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `extraction_id` → [[Reference/Database/Tables/source_extraction_runs|`source_extraction_runs.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `revision_id` → [[Reference/Database/Tables/source_revisions|`source_revisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_source_held_out_signal_marks_extraction` on `extraction_id`.
- `idx_source_held_out_signal_marks_revision` on `revision_id`.
- `sqlite_autoindex_source_held_out_signal_marks_1` on `id` (unique).

Database triggers:

- `source_held_out_signal_marks_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

- `Repository.delete_source_artifact()`
- `Repository.held_out_signal_marks()`
- `Repository.insert_unit_inventory()`

### Direct SQL readers

- `src/learnloop/content/sources/exam_material.py`
- `src/learnloop/db/repositories.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/content/synthesis/source_unit_inventory.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_coordinated_migrations.py`
- `tests/test_exam_protection_identity.py`
- `tests/test_ad1_reading_opportunities.py`
- `tests/test_exam_protection_review.py`
- `tests/test_reread_safety.py`

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
CREATE TABLE source_held_out_signal_marks (
  id TEXT PRIMARY KEY,
  revision_id TEXT NOT NULL REFERENCES source_revisions(id),
  extraction_id TEXT REFERENCES source_extraction_runs(id),
  unit_id TEXT NOT NULL,
  inventory_id TEXT NOT NULL,
  made_as_role TEXT,
  -- JSON array of the held-out signals' span ids on that reading, sorted.
  span_ids_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

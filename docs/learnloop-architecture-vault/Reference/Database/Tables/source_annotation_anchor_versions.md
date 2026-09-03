---
title: "source_annotation_anchor_versions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite source_annotation_anchor_versions"
  - "table source_annotation_anchor_versions"
schema_head: 157
table_name: "source_annotation_anchor_versions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "090_source_annotations.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/090_source_annotations.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/sources/source_deletion.py"
  - "src/learnloop/reader/annotations.py"
  - "src/learnloop/reader/reader_capture.py"
  - "src/learnloop/reader/reader_requests.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_annotation_anchor_versions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Pins immutable versions of source annotation anchor so canonical-source work can be retried without losing provenance or silently changing its input set. It supplies replay-stable input rather than a disposable cache. Rows bind `annotation_id`, `source_id`, `revision_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/090_source_annotations.sql`.
- **Schema touched by:** `090_source_annotations.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `annotation_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/source_annotations\|source_annotations.id]] | Stored value |
| `version_ordinal` | `INTEGER` | yes | — | — | Stored value |
| `source_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `revision_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `extraction_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `render_view_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `status` | `TEXT` | yes | — | — | Stored value |
| `algo_version` | `TEXT` | yes | — | — | Stored value |
| `confidence` | `REAL` | no | — | — | Stored value |
| `raw_selection_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `annotation_id` → [[Reference/Database/Tables/source_annotations|`source_annotations.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_source_annotation_anchor_ann` on `annotation_id`, `version_ordinal`.
- `sqlite_autoindex_source_annotation_anchor_versions_2` on `annotation_id`, `version_ordinal` (unique).
- `sqlite_autoindex_source_annotation_anchor_versions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository._write_anchor_version()`
- `Repository.annotation_head()`
- `Repository.annotation_history()`
- `Repository.delete_source_artifact()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/reader/annotations.py`
- `src/learnloop/reader/reader_capture.py`
- `src/learnloop/reader/reader_requests.py`
- `src/learnloop_sidecar/handlers/reader.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_annotations.py`
- `tests/test_p3_journeys.py`
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
CREATE TABLE source_annotation_anchor_versions (
  id TEXT PRIMARY KEY,
  annotation_id TEXT NOT NULL REFERENCES source_annotations(id),
  version_ordinal INTEGER NOT NULL,
  source_id TEXT NOT NULL,
  revision_id TEXT NOT NULL,
  extraction_id TEXT NOT NULL,
  render_view_id TEXT,
  status TEXT NOT NULL
    CHECK (status IN ('exact', 'reanchored', 'needs_reanchor', 'orphaned', 'manually_anchored')),
  algo_version TEXT NOT NULL,
  confidence REAL,
  raw_selection_json TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(annotation_id, version_ordinal)
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

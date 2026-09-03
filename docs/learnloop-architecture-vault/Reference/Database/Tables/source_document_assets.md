---
title: "source_document_assets"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite source_document_assets"
  - "table source_document_assets"
schema_head: 157
table_name: "source_document_assets"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "032_source_layer.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/032_source_layer.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/authoring/exercise_authoring.py"
  - "src/learnloop/content/authoring/practice_leakage.py"
  - "src/learnloop/content/pipeline/jobs.py"
  - "src/learnloop/content/pipeline/revision_refresh.py"
  - "src/learnloop/content/sources/source_deletion.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_document_assets`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives source document asset a stable database identity so canonical-source work can be retried without losing provenance or silently changing its input set. It supplies replay-stable input rather than a disposable cache. Rows bind `extraction_id`, `media_type`, `content_hash`, making the operational relationship explicit. ^table-purpose

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/032_source_layer.sql`.
- **Schema touched by:** `032_source_layer.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | yes | — | PRIMARY KEY | Stored value |
| `extraction_id` | `TEXT` | yes | — | PRIMARY KEY; FK → [[Reference/Database/Tables/source_extraction_runs\|source_extraction_runs.id]] | Stored value |
| `media_type` | `TEXT` | yes | — | — | Stored value |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `path` | `TEXT` | no | — | — | Stored value |
| `caption` | `TEXT` | no | — | — | Stored value |
| `page` | `INTEGER` | no | — | — | Stored value |
| `geometry_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `neighboring_span_ids_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

Declared SQLite foreign keys:

- `extraction_id` → [[Reference/Database/Tables/source_extraction_runs|`source_extraction_runs.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_source_document_assets_1` on `extraction_id`, `id` (unique).

## Who calls it

### Repository access surface

- `Repository.delete_source_artifact()`
- `Repository.load_document_ir()`
- `Repository.persist_document_ir()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/authoring/exercise_authoring.py`
- `src/learnloop/content/authoring/practice_leakage.py`
- `src/learnloop/content/pipeline/jobs.py`
- `src/learnloop/content/pipeline/revision_refresh.py`
- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/content/sources/source_outline.py`
- `src/learnloop/content/synthesis/source_coverage.py`
- `src/learnloop/content/synthesis/source_set_synthesis.py`
- `src/learnloop/content/synthesis/source_unit_inventory.py`
- `src/learnloop/content/synthesis/source_unit_selection.py`
- `src/learnloop/reader/annotations.py`
- `src/learnloop/reader/reader_guidance.py`
- `src/learnloop/reader/reader_progression.py`
- `src/learnloop/reader/reader_quick_check.py`
- `src/learnloop/reader/reader_requests.py`
- `src/learnloop/reader/source_render_views.py`
- `src/learnloop/reader/source_review.py`
- `src/learnloop/reader/span_view.py`
- `src/learnloop_sidecar/handlers/ingest.py`
- `src/learnloop_sidecar/handlers/reader.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`
- `tests/test_ingest_m3.py`
- `tests/test_ingest_runner.py`
- `tests/test_primed_attempts.py`
- `tests/test_sidecar_ingest_m3.py`
- `tests/test_sidecar_quick_add.py`
- `tests/test_sidecar_span_view.py`
- `tests/test_source_deletion.py`
- `tests/test_source_ingestion_v2lite.py`
- `tests/test_source_inventory.py`
- `tests/test_source_layer.py`

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
CREATE TABLE source_document_assets (
  id TEXT NOT NULL,
  extraction_id TEXT NOT NULL REFERENCES source_extraction_runs(id),
  media_type TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  path TEXT,
  caption TEXT,
  page INTEGER,
  geometry_json TEXT,
  neighboring_span_ids_json TEXT,
  PRIMARY KEY(extraction_id, id)
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

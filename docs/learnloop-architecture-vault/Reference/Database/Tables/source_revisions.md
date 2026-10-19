---
title: "source_revisions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "b113e76b04ab40b93ea0e7aa564c54dc086e1ef2"
source_commit_timestamp: "2026-10-18T20:24:12-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite source_revisions"
  - "table source_revisions"
schema_head: 212
table_name: "source_revisions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "032_source_layer.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/032_source_layer.sql"
  - "src/learnloop/capture/inbox.py"
  - "src/learnloop/content/sources/exam_material.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/db/stores/held_out_signals.py"
  - "src/learnloop/db/stores/source_block_fts.py"
  - "src/learnloop/ops/doctor.py"
  - "src/learnloop/substrate/dataset.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/content/authoring/source_exercise_import.py"
  - "src/learnloop/content/pipeline/acquisition_preview.py"
  - "src/learnloop/content/pipeline/add_source.py"
  - "src/learnloop/content/pipeline/build_plan.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_revisions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records immutable revisions of canonical sources and their content identity. It supplies replay-stable input rather than a disposable cache. Rows bind `source_id`, `note_id`, `supersedes_revision_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/032_source_layer.sql`.
- **Schema touched by:** `032_source_layer.sql`, `040_source_unit_selections.sql`, `041_source_unit_inventories.sql`, `088_source_render_views.sql`, `204_source_held_out_signal_marks.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `source_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/source_artifacts\|source_artifacts.id]] | Stored value |
| `asset_hash` | `TEXT` | yes | — | — | Stored value |
| `note_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `original_uri` | `TEXT` | no | — | — | Stored value |
| `retrieved_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `supersedes_revision_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/source_revisions\|source_revisions.id]] | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `supersedes_revision_id` → [[Reference/Database/Tables/source_revisions|`source_revisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `source_id` → [[Reference/Database/Tables/source_artifacts|`source_artifacts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_source_revisions_asset` on `asset_hash`.
- `idx_source_revisions_source` on `source_id`.
- `sqlite_autoindex_source_revisions_2` on `source_id`, `asset_hash` (unique).
- `sqlite_autoindex_source_revisions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository._record_reading_request_for_extraction()`
- `Repository.delete_source_artifact()`
- `Repository.get_source_revision()`
- `Repository.held_out_signal_marks()`
- `Repository.insert_source_revision()`
- `Repository.reading_request_unsettled()`
- `Repository.source_revision_by_asset_hash()`
- `Repository.source_revisions_for()`
- `Repository.upsert_unit_selection()`

### Direct SQL readers

- `src/learnloop/capture/inbox.py`
- `src/learnloop/content/sources/exam_material.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/db/stores/held_out_signals.py`
- `src/learnloop/db/stores/source_block_fts.py`
- `src/learnloop/ops/doctor.py`
- `src/learnloop/substrate/dataset.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/content/authoring/source_exercise_import.py`
- `src/learnloop/content/pipeline/acquisition_preview.py`
- `src/learnloop/content/pipeline/add_source.py`
- `src/learnloop/content/pipeline/build_plan.py`
- `src/learnloop/content/pipeline/exam_marking.py`
- `src/learnloop/content/pipeline/jobs.py`
- `src/learnloop/content/pipeline/quick_add.py`
- `src/learnloop/content/pipeline/reread.py`
- `src/learnloop/content/pipeline/source_ingestion.py`
- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/content/sources/source_library.py`
- `src/learnloop/content/sources/source_outline.py`
- `src/learnloop/content/sources/span_aliases.py`
- `src/learnloop/content/synthesis/source_unit_selection.py`
- `src/learnloop/daily_plan/reading.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/instructional/interventions.py`
- `src/learnloop/ops/doctor.py`
- `src/learnloop/reader/reader_authoring.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/helpers.py`
- `tests/reader_fixtures.py`
- `tests/source_retrieval_fakes.py`
- `tests/source_service_fakes.py`
- `tests/test_exam_protection.py`
- `tests/test_exam_protection_review.py`
- `tests/test_glm_ocr.py`
- `tests/test_ingest_runner.py`
- `tests/test_migrations.py`
- `tests/test_quick_add.py`
- `tests/test_reader_pdf_selection.py`
- `tests/test_reread_safety.py`
- `tests/test_revision_refresh.py`
- `tests/test_sidecar_reader_pdf_view.py`
- `tests/test_source_deletion.py`
- `tests/test_source_inventory.py`
- `tests/test_source_retrieval_guards.py`
- `tests/test_source_retrieval_rereview.py`
- `tests/test_span_view.py`
- `tests/test_t6_followup_rereview.py`

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
CREATE TABLE source_revisions (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES source_artifacts(id),
  asset_hash TEXT NOT NULL,
  note_id TEXT,
  original_uri TEXT,
  retrieved_at TEXT,
  supersedes_revision_id TEXT REFERENCES source_revisions(id),
  created_at TEXT NOT NULL,
  UNIQUE(source_id, asset_hash)
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

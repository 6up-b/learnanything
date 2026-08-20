---
title: "source_extraction_runs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite source_extraction_runs"
  - "table source_extraction_runs"
schema_head: 156
table_name: "source_extraction_runs"
table_role: "workflow"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "032_source_layer.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/032_source_layer.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/pipeline/build_plan.py"
  - "src/learnloop/content/pipeline/jobs.py"
  - "src/learnloop/content/pipeline/quick_add.py"
  - "src/learnloop/content/sources/source_deletion.py"
  - "src/learnloop/content/sources/source_outline.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_extraction_runs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Tracks one execution, input identity, and result for source extraction so canonical-source work can be retried without losing provenance or silently changing its input set. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `revision_id`, `parent_extraction_id`, `extractor_version`, making the operational relationship explicit. ^table-purpose

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/032_source_layer.sql`.
- **Schema touched by:** `032_source_layer.sql`, `040_source_unit_selections.sql`, `041_source_unit_inventories.sql`, `054_extraction_health.sql`, `088_source_render_views.sql`, `089_source_block_health.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `revision_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/source_revisions\|source_revisions.id]] | Stored value |
| `parent_extraction_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/source_extraction_runs\|source_extraction_runs.id]] | Stored value |
| `extractor` | `TEXT` | yes | — | — | Stored value |
| `extractor_version` | `TEXT` | yes | — | — | Stored value |
| `model_versions_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `config_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `page_selection_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `ir_schema_version` | `TEXT` | yes | — | — | Stored value |
| `extraction_request_hash` | `TEXT` | yes | — | — | Stored value |
| `extraction_result_hash` | `TEXT` | no | — | — | Stored value |
| `status` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `completed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `health_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

Declared SQLite foreign keys:

- `parent_extraction_id` → [[Reference/Database/Tables/source_extraction_runs|`source_extraction_runs.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `revision_id` → [[Reference/Database/Tables/source_revisions|`source_revisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_source_extraction_runs_revision` on `revision_id`.
- `sqlite_autoindex_source_extraction_runs_2` on `revision_id`, `extraction_request_hash` (unique).
- `sqlite_autoindex_source_extraction_runs_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.complete_extraction_run()`
- `Repository.delete_source_artifact()`
- `Repository.extraction_run_by_request_hash()`
- `Repository.extraction_runs_for_revision()`
- `Repository.get_extraction_run()`
- `Repository.insert_extraction_run()`
- `Repository.persist_document_ir()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/pipeline/build_plan.py`
- `src/learnloop/content/pipeline/jobs.py`
- `src/learnloop/content/pipeline/quick_add.py`
- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/content/sources/source_outline.py`
- `src/learnloop/content/synthesis/source_unit_inventory.py`
- `src/learnloop/content/synthesis/source_unit_selection.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/reader/annotations.py`
- `src/learnloop/reader/reader_guidance.py`
- `src/learnloop/reader/reader_progression.py`
- `src/learnloop/reader/reader_quick_check.py`
- `src/learnloop/reader/source_render_views.py`
- `src/learnloop/reader/source_search.py`
- `src/learnloop/reader/span_view.py`
- `src/learnloop_sidecar/handlers/ingest.py`
- `src/learnloop_sidecar/handlers/reader.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_ingest_runner.py`
- `tests/test_migrations.py`
- `tests/test_ingest_m3.py`
- `tests/test_primed_attempts.py`
- `tests/test_sidecar_ingest_m3.py`
- `tests/test_sidecar_quick_add.py`
- `tests/test_sidecar_span_view.py`
- `tests/test_source_deletion.py`
- `tests/test_source_inventory.py`
- `tests/test_source_layer.py`
- `tests/test_span_reanchor.py`

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
CREATE TABLE source_extraction_runs (
  id TEXT PRIMARY KEY,
  revision_id TEXT NOT NULL REFERENCES source_revisions(id),
  parent_extraction_id TEXT REFERENCES source_extraction_runs(id),
  extractor TEXT NOT NULL,
  extractor_version TEXT NOT NULL,
  model_versions_json TEXT,
  config_json TEXT,
  page_selection_json TEXT,
  ir_schema_version TEXT NOT NULL,
  extraction_request_hash TEXT NOT NULL,
  extraction_result_hash TEXT,   -- NULL until the run completes
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  completed_at TEXT, health_json TEXT,
  UNIQUE(revision_id, extraction_request_hash)
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

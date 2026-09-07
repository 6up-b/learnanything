---
title: "source_artifacts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite source_artifacts"
  - "table source_artifacts"
schema_head: 157
table_name: "source_artifacts"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "032_source_layer.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/032_source_layer.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/ops/doctor.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/content/pipeline/acquisition_preview.py"
  - "src/learnloop/content/pipeline/jobs.py"
  - "src/learnloop/content/pipeline/quick_add.py"
  - "src/learnloop/content/sources/source_deletion.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_artifacts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Identifies an acquired canonical source independently from any one revision or extraction. It supplies replay-stable input rather than a disposable cache. Rows bind `work_id`, `current_revision_id`, `acquisition_kind`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Source layer v2 (spec_source_ingestion_v2 §2.3/§2.4): immutable source identity (work -> artifact -> revision -> extraction run) plus the Document IR and cross-run span re-anchoring. Schemas follow the spec verbatim with house NOT NULL / REFERENCES added. Legacy subject-scoped notes remain readable in place and are indexed into these rows without moving files (§13).

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/032_source_layer.sql`.
- **Schema touched by:** `032_source_layer.sql`, `040_source_unit_selections.sql`, `062_source_artifact_display_title.sql`, `088_source_render_views.sql`, `094_source_objects.sql`, `104_source_reader_enabled.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `acquisition_kind` | `TEXT` | yes | — | — | Stored value |
| `canonical_uri` | `TEXT` | no | — | — | Stored value |
| `work_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `current_revision_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `display_title` | `TEXT` | no | — | — | Stored value |
| `reader_enabled` | `INTEGER` | yes | `1` | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_source_artifacts_uri` on `canonical_uri`.
- `sqlite_autoindex_source_artifacts_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.all_source_artifacts()`
- `Repository.delete_source_artifact()`
- `Repository.get_source_artifact()`
- `Repository.set_source_current_revision()`
- `Repository.set_source_reader_enabled()`
- `Repository.source_artifact_by_uri()`
- `Repository.upsert_source_artifact()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/content/pipeline/acquisition_preview.py`
- `src/learnloop/content/pipeline/jobs.py`
- `src/learnloop/content/pipeline/quick_add.py`
- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/content/sources/source_library.py`
- `src/learnloop/content/sources/source_outline.py`
- `src/learnloop/ops/doctor.py`
- `src/learnloop/reader/reader_guidance.py`
- `src/learnloop/reader/reader_progression.py`
- `src/learnloop/reader/source_search.py`
- `src/learnloop/reader/span_view.py`
- `src/learnloop_sidecar/handlers/ingest.py`
- `src/learnloop_sidecar/handlers/reader.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_ingest_runner.py`
- `tests/test_migrations.py`
- `tests/test_quick_add.py`
- `tests/test_sidecar_reader_pdf_view.py`
- `tests/test_source_deletion.py`
- `tests/test_source_inventory.py`
- `tests/test_sidecar_reader.py`
- `tests/test_source_layer.py`
- `tests/test_source_search.py`

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
CREATE TABLE source_artifacts (
  id TEXT PRIMARY KEY,
  acquisition_kind TEXT NOT NULL,
  canonical_uri TEXT,
  work_id TEXT,
  current_revision_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
, display_title TEXT, reader_enabled INTEGER NOT NULL DEFAULT 1);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

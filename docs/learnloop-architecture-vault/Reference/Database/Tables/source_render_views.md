---
title: "source_render_views"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite source_render_views"
  - "table source_render_views"
schema_head: 156
table_name: "source_render_views"
table_role: "workflow"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "088_source_render_views.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/088_source_render_views.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop_sidecar/handlers/reader.py"
  - "src/learnloop/content/sources/source_deletion.py"
  - "src/learnloop/reader/source_render_views.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_render_views`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives source render view a stable database identity so canonical-source work can be retried without losing provenance or silently changing its input set. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `source_id`, `revision_id`, `extraction_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/088_source_render_views.sql`.
- **Schema touched by:** `088_source_render_views.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `source_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/source_artifacts\|source_artifacts.id]] | Stored value |
| `revision_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/source_revisions\|source_revisions.id]] | Stored value |
| `extraction_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/source_extraction_runs\|source_extraction_runs.id]] | Stored value |
| `renderer` | `TEXT` | yes | `'marker_markdown'` | — | Stored value |
| `renderer_version` | `TEXT` | yes | — | — | Stored value |
| `model_version` | `TEXT` | no | — | — | Stored value |
| `config_version` | `TEXT` | no | — | — | Stored value |
| `schema_version` | `TEXT` | yes | — | — | Stored value |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `asset_manifest_hash` | `TEXT` | no | — | — | Stored value |
| `status` | `TEXT` | yes | `'ready'` | — | Stored value |
| `health_summary_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `predecessor_view_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/source_render_views\|source_render_views.id]] | Stored value |
| `predecessor_reason` | `TEXT` | no | — | — | Stored value |
| `output_ref` | `TEXT` | no | — | — | Stored value |
| `request_hash` | `TEXT` | yes | — | — | Stored value |
| `result_hash` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `completed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `predecessor_view_id` → [[Reference/Database/Tables/source_render_views|`source_render_views.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `extraction_id` → [[Reference/Database/Tables/source_extraction_runs|`source_extraction_runs.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `revision_id` → [[Reference/Database/Tables/source_revisions|`source_revisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `source_id` → [[Reference/Database/Tables/source_artifacts|`source_artifacts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_source_render_views_revision` on `revision_id`.
- `idx_source_render_views_extraction` on `extraction_id`.
- `sqlite_autoindex_source_render_views_2` on `request_hash` (unique).
- `sqlite_autoindex_source_render_views_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.delete_source_artifact()`
- `Repository.get_render_view()`
- `Repository.insert_render_view()`
- `Repository.latest_render_view_for_extraction()`
- `Repository.render_view_by_request_hash()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/reader/source_render_views.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_p3_journeys.py`
- `tests/test_reader_render_views.py`

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
CREATE TABLE source_render_views (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES source_artifacts(id),
  revision_id TEXT NOT NULL REFERENCES source_revisions(id),
  extraction_id TEXT NOT NULL REFERENCES source_extraction_runs(id),
  renderer TEXT NOT NULL DEFAULT 'marker_markdown',
  renderer_version TEXT NOT NULL,
  model_version TEXT,
  config_version TEXT,
  schema_version TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  asset_manifest_hash TEXT,
  status TEXT NOT NULL DEFAULT 'ready'
    CHECK (status IN ('pending', 'ready', 'failed', 'superseded')),
  health_summary_json TEXT NOT NULL DEFAULT '{}',
  predecessor_view_id TEXT REFERENCES source_render_views(id),
  predecessor_reason TEXT,
  output_ref TEXT,
  request_hash TEXT NOT NULL,
  result_hash TEXT,
  created_at TEXT NOT NULL,
  completed_at TEXT,
  UNIQUE(request_hash)
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

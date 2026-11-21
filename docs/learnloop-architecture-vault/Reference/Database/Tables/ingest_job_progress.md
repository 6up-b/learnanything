---
title: "ingest_job_progress"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite ingest_job_progress"
  - "table ingest_job_progress"
table_name: "ingest_job_progress"
table_role: "workflow"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "258_ingest_job_progress.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/258_ingest_job_progress.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/content/pipeline/jobs.py"
  - "src/learnloop/content/pipeline/wait_detail.py"
  - "src/learnloop/db/stores/ingest_queue.py"
  - "src/learnloop/content/pipeline/runner.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `ingest_job_progress`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives ingest job progress a stable database identity so canonical-source work can be retried without losing provenance or silently changing its input set. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `job_id`, `output_call_id`, `attempt_count`, making the operational relationship explicit. ^table-purpose

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/258_ingest_job_progress.sql`.
- **Schema touched by:** `258_ingest_job_progress.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `job_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_count` | `INTEGER` | yes | — | — | Stored value |
| `try_number` | `INTEGER` | yes | `1` | — | Stored value |
| `try_started_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `step` | `TEXT` | no | — | — | Stored value |
| `drafted_topics` | `INTEGER` | no | — | — | Stored value |
| `reused` | `INTEGER` | no | — | — | Stored value |
| `output_call_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `output_events` | `INTEGER` | yes | `0` | — | Stored value |
| `last_output_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_ingest_job_progress_1` on `job_id` (unique).

## Who calls it

### Repository access surface

- `Repository.delete_finished_ingest_batches()`
- `Repository.ingest_job_progress()`
- `Repository.record_ingest_job_output()`
- `Repository.record_ingest_job_progress()`
- `Repository.start_ingest_job_progress()`

### Direct SQL readers

- `src/learnloop/db/stores/ingest_queue.py`

### Direct SQL writers

- `src/learnloop/db/stores/ingest_queue.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/pipeline/jobs.py`
- `src/learnloop/content/pipeline/runner.py`
- `src/learnloop/content/pipeline/wait_detail.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/ingest_job_progress_migration_helpers.py`
- `tests/test_build_wait_detail.py`
- `tests/test_ingest_job_progress_migration.py`
- `tests/test_ingest_queue_store.py`
- `tests/test_ingest_runner.py`

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
CREATE TABLE ingest_job_progress (
  job_id TEXT PRIMARY KEY,
  attempt_count INTEGER NOT NULL,
  try_number INTEGER NOT NULL DEFAULT 1,
  try_started_at TEXT NOT NULL,
  step TEXT,
  drafted_topics INTEGER,
  reused INTEGER,
  output_call_id TEXT,
  output_events INTEGER NOT NULL DEFAULT 0,
  last_output_at TEXT,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

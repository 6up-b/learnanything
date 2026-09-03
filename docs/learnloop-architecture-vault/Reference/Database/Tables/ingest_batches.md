---
title: "ingest_batches"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite ingest_batches"
  - "table ingest_batches"
schema_head: 157
table_name: "ingest_batches"
table_role: "workflow"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "033_durable_ingest_jobs.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/033_durable_ingest_jobs.sql"
  - "src/learnloop/cli/__init__.py"
  - "src/learnloop/content/pipeline/jobs.py"
  - "src/learnloop/db/stores/ingest_queue.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `ingest_batches`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Tracks a user-visible durable batch of source-pipeline work. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `subject_id`, `source_set_id`, `workflow_type`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Durable ingest workflows (spec_source_ingestion_v2 §6.2): repository-backed batches/jobs/dependencies that survive process restarts, replacing the old in-memory job manager. Schemas follow §6.2 verbatim with house NOT NULL / REFERENCES / defaults added.  `workflow_type` / `job_type` are APPLICATION-validated open strings (core types: import, extract, inventory, legacy_ingest, exam_ingest, bootstrap_synthesis, append_synthesis, extraction_repair). Deliberately NO SQL CHECK on them so a new workflow never needs a migration. Status vocabulary is closed, so a CHECK is appropriate there.

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/033_durable_ingest_jobs.sql`.
- **Schema touched by:** `033_durable_ingest_jobs.sql`, `048_ingest_batch_priority.sql`, `117_question_promotion_jobs_and_queue_revision.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `workflow_type` | `TEXT` | yes | — | — | Stored value |
| `payload_schema_version` | `INTEGER` | yes | `1` | — | Stored value |
| `subject_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `source_set_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `status` | `TEXT` | yes | `'queued'` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `started_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `finished_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `cancel_requested` | `INTEGER` | yes | `0` | — | Stored value |
| `priority` | `INTEGER` | yes | `0` | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_ingest_batches_priority` on `priority`, `created_at`.
- `idx_ingest_batches_status` on `status`.
- `sqlite_autoindex_ingest_batches_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/ingest_queue.py`

### Direct SQL writers

- `src/learnloop/db/stores/ingest_queue.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_ingest_queue_store.py`
- `tests/test_migrations.py`

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
CREATE TABLE ingest_batches (
  id TEXT PRIMARY KEY,
  workflow_type TEXT NOT NULL,
  payload_schema_version INTEGER NOT NULL DEFAULT 1,
  subject_id TEXT,
  source_set_id TEXT,
  status TEXT NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued', 'running', 'waiting_for_input',
                      'completed', 'failed', 'blocked', 'cancelled')),
  created_at TEXT NOT NULL,
  started_at TEXT,
  finished_at TEXT,
  cancel_requested INTEGER NOT NULL DEFAULT 0
, priority INTEGER NOT NULL DEFAULT 0);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

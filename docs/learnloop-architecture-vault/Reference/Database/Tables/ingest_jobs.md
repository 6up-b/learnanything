---
title: "ingest_jobs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite ingest_jobs"
  - "table ingest_jobs"
schema_head: 157
table_name: "ingest_jobs"
table_role: "workflow"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "033_durable_ingest_jobs.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/033_durable_ingest_jobs.sql"
  - "src/learnloop/content/pipeline/jobs.py"
  - "src/learnloop/content/pipeline/quick_add.py"
  - "src/learnloop/db/stores/ingest_queue.py"
  - "src/learnloop_sidecar/context.py"
  - "src/learnloop_sidecar/handlers/animation.py"
  - "src/learnloop_sidecar/handlers/app.py"
  - "src/learnloop_sidecar/handlers/cli.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `ingest_jobs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Tracks individual leased, retryable jobs within an ingest batch. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `batch_id`, `worker_id`, `job_type`, making the operational relationship explicit. ^table-purpose

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/033_durable_ingest_jobs.sql`.
- **Schema touched by:** `033_durable_ingest_jobs.sql`, `078_surface_mint_jobs.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `batch_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/ingest_batches\|ingest_batches.id]] | Stored value |
| `ordinal` | `INTEGER` | yes | — | — | Stored value |
| `job_type` | `TEXT` | yes | — | — | Stored value |
| `payload_schema_version` | `INTEGER` | yes | `1` | — | Stored value |
| `payload_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | `'queued'` | — | Stored value |
| `phase` | `TEXT` | no | — | — | Stored value |
| `message` | `TEXT` | no | — | — | Stored value |
| `current_window` | `INTEGER` | no | — | — | Stored value |
| `total_windows` | `INTEGER` | no | — | — | Stored value |
| `result_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `error_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `usage_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `attempt_count` | `INTEGER` | yes | `0` | — | Stored value |
| `cancel_requested` | `INTEGER` | yes | `0` | — | Stored value |
| `worker_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `heartbeat_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `started_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `finished_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `batch_id` → [[Reference/Database/Tables/ingest_batches|`ingest_batches.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_ingest_jobs_status` on `status`.
- `idx_ingest_jobs_batch` on `batch_id`, `ordinal`.
- `sqlite_autoindex_ingest_jobs_1` on `id` (unique).

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

- `tests/test_build_study_map_routing.py`
- `tests/test_ingest_jobs.py`
- `tests/test_ingest_latency_journey.py`
- `tests/test_ingest_queue_store.py`
- `tests/test_migrations.py`
- `tests/test_sidecar_exams.py`
- `tests/test_sidecar_goals.py`
- `tests/test_sidecar_measurement.py`
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
CREATE TABLE ingest_jobs (
  id TEXT PRIMARY KEY,
  batch_id TEXT NOT NULL REFERENCES ingest_batches(id),
  ordinal INTEGER NOT NULL,
  job_type TEXT NOT NULL,
  payload_schema_version INTEGER NOT NULL DEFAULT 1,
  payload_json TEXT,
  status TEXT NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued', 'running', 'waiting_for_input',
                      'completed', 'failed', 'blocked', 'cancelled')),
  phase TEXT,
  message TEXT,
  current_window INTEGER,
  total_windows INTEGER,
  result_json TEXT,
  error_json TEXT,
  usage_json TEXT,
  attempt_count INTEGER NOT NULL DEFAULT 0,
  cancel_requested INTEGER NOT NULL DEFAULT 0,
  -- Lease: a running job is owned by worker_id and kept alive by heartbeat_at.
  -- Exactly one worker drains at a time; on startup an expired running lease is
  -- recovered to failed(interrupted). waiting_for_input holds NO lease.
  worker_id TEXT,
  heartbeat_at TEXT,
  created_at TEXT NOT NULL,
  started_at TEXT,
  finished_at TEXT
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

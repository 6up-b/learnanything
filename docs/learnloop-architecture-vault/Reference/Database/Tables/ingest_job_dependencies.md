---
title: "ingest_job_dependencies"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite ingest_job_dependencies"
  - "table ingest_job_dependencies"
schema_head: 157
table_name: "ingest_job_dependencies"
table_role: "workflow"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "033_durable_ingest_jobs.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/033_durable_ingest_jobs.sql"
  - "src/learnloop/db/stores/ingest_queue.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `ingest_job_dependencies`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records prerequisite edges between durable ingest jobs. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `job_id`, `depends_on_job_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/033_durable_ingest_jobs.sql`.
- **Schema touched by:** `033_durable_ingest_jobs.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `job_id` | `TEXT` | yes | — | PRIMARY KEY; FK → [[Reference/Database/Tables/ingest_jobs\|ingest_jobs.id]] | Stored value |
| `depends_on_job_id` | `TEXT` | yes | — | PRIMARY KEY; FK → [[Reference/Database/Tables/ingest_jobs\|ingest_jobs.id]] | Stored value |

## Relationships and access paths

Declared SQLite foreign keys:

- `depends_on_job_id` → [[Reference/Database/Tables/ingest_jobs|`ingest_jobs.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `job_id` → [[Reference/Database/Tables/ingest_jobs|`ingest_jobs.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_ingest_job_dependencies_dep` on `depends_on_job_id`.
- `sqlite_autoindex_ingest_job_dependencies_1` on `job_id`, `depends_on_job_id` (unique).

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
CREATE TABLE ingest_job_dependencies (
  job_id TEXT NOT NULL REFERENCES ingest_jobs(id),
  depends_on_job_id TEXT NOT NULL REFERENCES ingest_jobs(id),
  PRIMARY KEY (job_id, depends_on_job_id)
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

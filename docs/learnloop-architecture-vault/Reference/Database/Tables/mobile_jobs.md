---
title: "mobile_jobs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "c6e2e8d3f7207fd2aae6f66eee71c840f8d40e0f"
source_commit_timestamp: "2026-11-09T00:34:52-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite mobile_jobs"
  - "table mobile_jobs"
schema_head: 251
table_name: "mobile_jobs"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "239_mobile_jobs.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/239_mobile_jobs.sql"
  - "src/learnloop/capture/jobs.py"
  - "src/learnloop/capture/report.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `mobile_jobs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Coordinates leased, retryable work for mobile so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `device_id`, `request_id`, `host_boot_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/239_mobile_jobs.sql`.
- **Schema touched by:** `239_mobile_jobs.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `device_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `request_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `method` | `TEXT` | yes | — | — | Stored value |
| `params_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `params_sha256` | `TEXT` | yes | — | — | Stored value |
| `state` | `TEXT` | yes | — | — | Stored value |
| `result_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `error_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `host_boot_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `boot_attempts` | `INTEGER` | yes | `0` | — | Stored value |
| `accepted_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `started_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `finished_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `mobile_jobs_open` on `state`.
- `mobile_jobs_request` on `request_id`.
- `sqlite_autoindex_mobile_jobs_2` on `device_id`, `request_id` (unique).
- `sqlite_autoindex_mobile_jobs_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/capture/jobs.py`
- `src/learnloop/capture/report.py`

### Direct SQL writers

- `src/learnloop/capture/jobs.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_mobile_jobs.py`
- `tests/test_mobile_jobs_migration.py`
- `tests/test_mobile_two_process.py`

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
CREATE TABLE mobile_jobs (
  id TEXT PRIMARY KEY,
  device_id TEXT NOT NULL,
  request_id TEXT NOT NULL,
  method TEXT NOT NULL,
  params_json TEXT NOT NULL,
  params_sha256 TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('accepted', 'running', 'completed', 'failed', 'recorded')),
  result_json TEXT,
  error_json TEXT,
  host_boot_id TEXT NOT NULL,
  boot_attempts INTEGER NOT NULL DEFAULT 0 CHECK (boot_attempts >= 0),
  accepted_at TEXT NOT NULL,
  started_at TEXT,
  finished_at TEXT,
  UNIQUE (device_id, request_id)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

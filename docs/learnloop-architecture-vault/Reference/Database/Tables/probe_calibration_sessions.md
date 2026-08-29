---
title: "probe_calibration_sessions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite probe_calibration_sessions"
  - "table probe_calibration_sessions"
schema_head: 156
table_name: "probe_calibration_sessions"
table_role: "workflow"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "029_probe_selection_and_calibration.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/029_probe_selection_and_calibration.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/calibration_sessions.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `probe_calibration_sessions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Tracks the resumable lifecycle of probe calibration so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `session_id`, `goal_id`, `time_budget_minutes`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §5.9: a calibration session batches multiple episode blocks across a goal's facet scope in one sitting, with its own time budget, progress display, and stop control. It lifts only the per-session qualifying-observation cap.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/029_probe_selection_and_calibration.sql`.
- **Schema touched by:** `029_probe_selection_and_calibration.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `session_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `goal_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `learning_object_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `planned_episode_ids_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `time_budget_minutes` | `INTEGER` | yes | — | — | Stored value |
| `status` | `TEXT` | yes | — | — | Stored value |
| `started_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `ended_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_probe_calibration_sessions_active` on `session_id` (unique).
- `sqlite_autoindex_probe_calibration_sessions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.active_probe_calibration_session()`
- `Repository.end_probe_calibration_session()`
- `Repository.insert_probe_calibration_session()`
- `Repository.probe_calibration_session()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/diagnosis/calibration_sessions.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_graph_correction.py`

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
CREATE TABLE probe_calibration_sessions (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  goal_id TEXT,
  learning_object_ids_json TEXT NOT NULL,
  planned_episode_ids_json TEXT NOT NULL,
  time_budget_minutes INTEGER NOT NULL CHECK (time_budget_minutes >= 1),
  status TEXT NOT NULL CHECK (status IN ('active', 'completed', 'stopped', 'expired')),
  started_at TEXT NOT NULL,
  ended_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

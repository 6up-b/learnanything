---
title: "exam_sessions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite exam_sessions"
  - "table exam_sessions"
schema_head: 156
table_name: "exam_sessions"
table_role: "workflow"
functionality_status: "active"
domain_family: "goals-and-exams"
introduced_in: "024_exam_session.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/024_exam_session.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/goals/exam_session.py"
  - "src/learnloop_sidecar/handlers/goals.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/goals-and-exams"
---

# `exam_sessions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Tracks a held-out exam session from reservation through completion. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `goal_id`, `status`, `started_at`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Exam session: one sitting of a goal's held-out practice exam. The prediction snapshot (exam_predictions) is frozen at start, BEFORE any answer is graded, so the exam is an honest test of the mastery model's projections. Answers are stored per item (exam_answers) as the learner works through the session, and applied through the standard attempt pipeline only at finish. The computed report is persisted on the session row so finish is idempotent by id.

It belongs to the **goals and exams** navigation family. The family context lives in [[Database Catalog#Goals And Exams]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/024_exam_session.sql`.
- **Schema touched by:** `024_exam_session.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `goal_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `status` | `TEXT` | yes | — | — | Stored value |
| `item_order_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `report_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `started_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `completed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_exam_sessions_goal` on `goal_id`, `status`.
- `sqlite_autoindex_exam_sessions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.exam_session()`
- `Repository.exam_session_in_progress_for_goal()`
- `Repository.insert_exam_session()`
- `Repository.latest_completed_exam_session()`
- `Repository.update_exam_session()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/goals/exam_session.py`
- `src/learnloop_sidecar/handlers/goals.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_exam_calibration.py`

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
CREATE TABLE exam_sessions (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('draft', 'in_progress', 'completed', 'abandoned')),
  item_order_json TEXT NOT NULL,
  report_json TEXT,
  started_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  completed_at TEXT
);
```

## Related notes

- [[Database Catalog#Goals And Exams|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

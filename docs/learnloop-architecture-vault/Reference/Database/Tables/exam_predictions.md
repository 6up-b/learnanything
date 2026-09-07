---
title: "exam_predictions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite exam_predictions"
  - "table exam_predictions"
schema_head: 157
table_name: "exam_predictions"
table_role: "receipt"
functionality_status: "active"
domain_family: "goals-and-exams"
introduced_in: "024_exam_session.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/024_exam_session.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/goals/exam_calibration.py"
  - "src/learnloop/goals/exam_session.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/goals-and-exams"
---

# `exam_predictions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records predictions for exam before their outcomes are known so goal progress and held-out certification remain tied to the contract and evidence that produced them. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `session_id`, `practice_item_id`, `predicted_correctness`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Immutable per-item prediction, frozen at start_exam. predicted_correctness is the model's pre-exam belief that the learner answers this item correctly; facet_projection_json snapshots current + projected-at-due recall (and the goal target) for the scope facets this item tests.

It belongs to the **goals and exams** navigation family. The family context lives in [[Database Catalog#Goals And Exams]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/024_exam_session.sql`.
- **Schema touched by:** `024_exam_session.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `session_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/exam_sessions\|exam_sessions.id]] | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `predicted_correctness` | `REAL` | yes | — | — | Stored value |
| `facet_projection_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `session_id` → [[Reference/Database/Tables/exam_sessions|`exam_sessions.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_exam_predictions_session` on `session_id`.
- `sqlite_autoindex_exam_predictions_2` on `session_id`, `practice_item_id` (unique).
- `sqlite_autoindex_exam_predictions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.all_exam_predictions()`
- `Repository.exam_predictions()`
- `Repository.insert_exam_predictions()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/goals/exam_calibration.py`
- `src/learnloop/goals/exam_session.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_characterization_assessment_exam.py`
- `tests/test_exam_session.py`
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
CREATE TABLE exam_predictions (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES exam_sessions(id) ON DELETE CASCADE,
  practice_item_id TEXT NOT NULL,
  predicted_correctness REAL NOT NULL,
  facet_projection_json TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(session_id, practice_item_id)
);
```

## Related notes

- [[Database Catalog#Goals And Exams|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

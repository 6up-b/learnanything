---
title: "exam_answers"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite exam_answers"
  - "table exam_answers"
schema_head: 156
table_name: "exam_answers"
table_role: "raw_ledger"
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
  - "src/learnloop_sidecar/handlers/exams.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/goals-and-exams"
---

# `exam_answers`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Stores answers submitted within an exam session. It supplies replay-stable input rather than a disposable cache. Rows bind `session_id`, `practice_item_id`, `attempt_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Per-item graded answer. grade_json is a serialized ResolvedGrade produced by the caller (sidecar/CLI); no mastery is written until finish applies it through apply_attempt, at which point attempt_id is backfilled.

It belongs to the **goals and exams** navigation family. The family context lives in [[Database Catalog#Goals And Exams]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
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
| `answer_md` | `TEXT` | no | — | — | Stored value |
| `rubric_score` | `INTEGER` | no | — | — | Stored value |
| `correctness` | `REAL` | no | — | — | Stored value |
| `grade_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `answered_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `session_id` → [[Reference/Database/Tables/exam_sessions|`exam_sessions.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_exam_answers_session` on `session_id`.
- `sqlite_autoindex_exam_answers_2` on `session_id`, `practice_item_id` (unique).
- `sqlite_autoindex_exam_answers_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.exam_answer()`
- `Repository.exam_answers()`
- `Repository.set_exam_answer_attempt_id()`
- `Repository.upsert_exam_answer()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/goals/exam_calibration.py`
- `src/learnloop/goals/exam_session.py`
- `src/learnloop_sidecar/handlers/exams.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_exam_session.py`
- `tests/test_grade_resolution_pipeline.py`
- `tests/test_post_attempt_pipeline.py`
- `tests/test_exam_calibration.py`
- `tests/test_sidecar_exams.py`

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
CREATE TABLE exam_answers (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES exam_sessions(id) ON DELETE CASCADE,
  practice_item_id TEXT NOT NULL,
  answer_md TEXT,
  rubric_score INTEGER,
  correctness REAL,
  grade_json TEXT,
  attempt_id TEXT,
  answered_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(session_id, practice_item_id)
);
```

## Related notes

- [[Database Catalog#Goals And Exams|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

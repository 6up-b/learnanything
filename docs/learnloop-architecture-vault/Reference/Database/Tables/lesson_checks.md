---
title: "lesson_checks"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "9b983234725d0afeda2ad1fc375bd05473a49e0a"
source_commit_timestamp: "2026-11-02T19:07:15-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite lesson_checks"
  - "table lesson_checks"
schema_head: 237
table_name: "lesson_checks"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "234_teacher_lessons.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/234_teacher_lessons.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/algorithm_versions.py"
  - "src/learnloop/db/stores/lessons.py"
  - "src/learnloop/evsi_calibration/forecast_report.py"
  - "src/learnloop/learner/lesson_weight.py"
  - "src/learnloop/teacher/checks.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `lesson_checks`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives lesson check a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `lesson_id`, `node_id`, `learning_object_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/234_teacher_lessons.sql`.
- **Schema touched by:** `234_teacher_lessons.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `lesson_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/lessons\|lessons.id]] | Stored value |
| `node_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `check_ref` | `TEXT` | yes | — | — | Stored value |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `minted_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `status` | `TEXT` | yes | — | — | Stored value |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `correctness` | `REAL` | no | — | — | Stored value |
| `tap` | `INTEGER` | no | — | — | Stored value |
| `hedge` | `TEXT` | no | — | — | Stored value |
| `predicted_success` | `REAL` | no | — | — | Stored value |
| `predicted_source` | `TEXT` | no | — | — | Stored value |
| `mass_learned` | `REAL` | no | — | — | Stored value |
| `mass_applied` | `REAL` | no | — | — | Stored value |
| `forecast_correct_key` | `TEXT` | no | — | — | Stored value |
| `forecast_retained_key` | `TEXT` | no | — | — | Stored value |
| `weight_inputs_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `lesson_id` → [[Reference/Database/Tables/lessons|`lessons.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_lesson_checks_lesson` on `lesson_id`, `created_at`.
- `idx_lesson_checks_lo` on `learning_object_id`, `created_at`.
- `sqlite_autoindex_lesson_checks_2` on `attempt_id` (unique).
- `sqlite_autoindex_lesson_checks_1` on `id` (unique).

Database triggers:

- `lesson_checks_no_delete` — schema-enforced lifecycle or immutability constraint.
- `lesson_checks_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/lessons.py`
- `src/learnloop/evsi_calibration/forecast_report.py`
- `src/learnloop/learner/lesson_weight.py`

### Direct SQL writers

- `src/learnloop/db/stores/lessons.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_reader_rw5d_p4b_teacher_visuals.py`
- `tests/test_teacher_te1_lesson.py`
- `tests/test_teacher_te1_migration.py`
- `tests/test_teacher_te1_review_fixes.py`
- `tests/test_teacher_te1_weight.py`

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
CREATE TABLE lesson_checks (
  id TEXT PRIMARY KEY,
  lesson_id TEXT NOT NULL REFERENCES lessons(id),
  node_id TEXT NOT NULL,
  check_ref TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  minted_item_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('answered', 'withdrawn')),
  attempt_id TEXT UNIQUE,
  correctness REAL CHECK (correctness IS NULL OR (correctness >= 0.0 AND correctness <= 1.0)),
  tap INTEGER CHECK (tap IS NULL OR tap BETWEEN 1 AND 5),
  hedge TEXT CHECK (hedge IS NULL OR hedge IN ('hedged', 'confident')),
  predicted_success REAL CHECK (predicted_success IS NULL OR (predicted_success >= 0.0 AND predicted_success <= 1.0)),
  predicted_source TEXT,
  mass_learned REAL CHECK (mass_learned IS NULL OR (mass_learned > 0.0 AND mass_learned < 1.0)),
  mass_applied REAL CHECK (mass_applied IS NULL OR (mass_applied >= 0.0 AND mass_applied <= 1.0)),
  forecast_correct_key TEXT,
  forecast_retained_key TEXT,
  weight_inputs_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  CHECK ((status = 'answered') = (attempt_id IS NOT NULL)),
  CHECK (status = 'withdrawn' OR mass_applied IS NOT NULL)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

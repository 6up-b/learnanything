---
title: "lesson_receipts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "55154e0388c3526da2d1a55ac4d850cea630f066"
source_commit_timestamp: "2026-11-03T13:30:51-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite lesson_receipts"
  - "table lesson_receipts"
schema_head: 239
table_name: "lesson_receipts"
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
  - "src/learnloop/db/stores/lessons.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `lesson_receipts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Freezes the inputs and outcome of each lesson decision so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `lesson_id`, `receipt_version`, `close_reason`, making the operational relationship explicit. ^table-purpose

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
| `lesson_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/lessons\|lessons.id]] | Stored value |
| `receipt_version` | `TEXT` | yes | — | — | Stored value |
| `close_reason` | `TEXT` | yes | — | — | Stored value |
| `receipt_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `lesson_id` → [[Reference/Database/Tables/lessons|`lessons.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_lesson_receipts_1` on `lesson_id` (unique).

Database triggers:

- `lesson_receipts_no_delete` — schema-enforced lifecycle or immutability constraint.
- `lesson_receipts_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/lessons.py`

### Direct SQL writers

- `src/learnloop/db/stores/lessons.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_followups_batch5_lesson.py`
- `tests/test_reader_rw5d_p4b_teacher_visuals.py`
- `tests/test_teacher_te1_lesson.py`
- `tests/test_teacher_te1_migration.py`
- `tests/test_teacher_te1_review_fixes.py`
- `tests/test_teacher_te1_successor.py`
- `tests/test_teacher_te1b_suggestions.py`

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
CREATE TABLE lesson_receipts (
  lesson_id TEXT PRIMARY KEY REFERENCES lessons(id),
  receipt_version TEXT NOT NULL,
  close_reason TEXT NOT NULL,
  receipt_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

---
title: "lesson_plans"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "b1693676a83a561b40dd2333d6b480e71f6ad59f"
source_commit_timestamp: "2026-11-06T18:53:04-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite lesson_plans"
  - "table lesson_plans"
schema_head: 249
table_name: "lesson_plans"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "234_teacher_lessons.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/234_teacher_lessons.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/material_view.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/db/stores/lessons.py"
  - "src/learnloop/teacher/service.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `lesson_plans`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives lesson plan a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It supplies replay-stable input rather than a disposable cache. Rows bind `lesson_id`, `version`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
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
| `version` | `INTEGER` | yes | — | — | Stored value |
| `outline_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `lesson_id` → [[Reference/Database/Tables/lessons|`lessons.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_lesson_plans_2` on `lesson_id`, `version` (unique).
- `sqlite_autoindex_lesson_plans_1` on `id` (unique).

Database triggers:

- `lesson_plans_no_delete` — schema-enforced lifecycle or immutability constraint.
- `lesson_plans_no_update` — schema-enforced lifecycle or immutability constraint.

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

- `tests/test_reader_rw5d_p4b_teacher_visuals.py`
- `tests/test_te3a_lesson_opportunity.py`
- `tests/test_teacher_te1_lesson.py`
- `tests/test_teacher_te1_migration.py`
- `tests/test_teacher_te1_review_fixes.py`
- `tests/test_teacher_te2log_episodes.py`
- `tests/test_teacher_te2log_node_held.py`

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
CREATE TABLE lesson_plans (
  id TEXT PRIMARY KEY,
  lesson_id TEXT NOT NULL REFERENCES lessons(id),
  version INTEGER NOT NULL CHECK (version >= 1),
  outline_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (lesson_id, version)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

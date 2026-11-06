---
title: "lesson_activity_intervals"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "c85c9c438e2298d0425a7a4000cdfdb0b5660d9f"
source_commit_timestamp: "2026-11-06T06:28:25-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite lesson_activity_intervals"
  - "table lesson_activity_intervals"
schema_head: 247
table_name: "lesson_activity_intervals"
table_role: "receipt"
functionality_status: "active"
domain_family: "operations"
introduced_in: "247_lesson_episodes.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/247_lesson_episodes.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/config/schema.py"
  - "src/learnloop/db/stores/lessons.py"
  - "src/learnloop/params/parameter_registry.py"
  - "src/learnloop/teacher/episodes.py"
  - "src/learnloop_sidecar/handlers/lesson.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `lesson_activity_intervals`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives lesson activity interval a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `lesson_id`, `receipt_version`, `screen_session`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/247_lesson_episodes.sql`.
- **Schema touched by:** `247_lesson_episodes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `lesson_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/lessons\|lessons.id]] | Stored value |
| `screen_session` | `TEXT` | yes | — | — | Stored value |
| `seq` | `INTEGER` | yes | — | — | Stored value |
| `started_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `ended_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `seconds` | `REAL` | yes | — | — | Stored value |
| `foreground` | `INTEGER` | yes | — | — | Stored value |
| `occurred_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `received_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `receipt_version` | `TEXT` | yes | — | — | Stored value |

## Relationships and access paths

Declared SQLite foreign keys:

- `lesson_id` → [[Reference/Database/Tables/lessons|`lessons.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_lesson_activity_intervals_lesson` on `lesson_id`, `started_at`.
- `sqlite_autoindex_lesson_activity_intervals_2` on `lesson_id`, `screen_session`, `seq` (unique).
- `sqlite_autoindex_lesson_activity_intervals_1` on `id` (unique).

Database triggers:

- `lesson_activity_intervals_no_delete` — schema-enforced lifecycle or immutability constraint.
- `lesson_activity_intervals_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/lessons.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_teacher_te2log_activity.py`
- `tests/test_teacher_te2log_episodes.py`
- `tests/test_teacher_te2log_migration.py`

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
CREATE TABLE lesson_activity_intervals (
  id TEXT PRIMARY KEY,
  lesson_id TEXT NOT NULL REFERENCES lessons(id),
  -- One mount of the lesson screen (a client-made id); seq counts its intervals from 1.
  screen_session TEXT NOT NULL,
  seq INTEGER NOT NULL CHECK (seq >= 1),
  started_at TEXT NOT NULL,
  ended_at TEXT NOT NULL,
  seconds REAL NOT NULL CHECK (seconds >= 0.0),
  -- 1: the screen was in the foreground with input; 0: it was open but not.
  foreground INTEGER NOT NULL CHECK (foreground IN (0, 1)),
  occurred_at TEXT NOT NULL,
  received_at TEXT NOT NULL,
  receipt_version TEXT NOT NULL,
  CHECK (ended_at >= started_at),
  UNIQUE (lesson_id, screen_session, seq)
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

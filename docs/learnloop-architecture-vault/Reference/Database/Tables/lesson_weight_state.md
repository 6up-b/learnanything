---
title: "lesson_weight_state"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "79532f7149b554db05a40c2ae1dbde68d9efec5a"
source_commit_timestamp: "2026-11-09T16:01:49-05:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite lesson_weight_state"
  - "table lesson_weight_state"
schema_head: 252
table_name: "lesson_weight_state"
table_role: "derived"
functionality_status: "active"
domain_family: "operations"
introduced_in: "234_teacher_lessons.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/234_teacher_lessons.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/learner/lesson_weight.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `lesson_weight_state`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Maintains the decision-facing current projection for lesson weight so maintenance and optional operational work remains inspectable without becoming learner-state authority. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `priors_version`, `family`, `updates`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/234_teacher_lessons.sql`.
- **Schema touched by:** `234_teacher_lessons.sql`.
- **Rebuild owner:** `lesson_weight`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `family` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `state_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `updates` | `INTEGER` | yes | `0` | — | Stored value |
| `through_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `priors_version` | `TEXT` | yes | — | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_lesson_weight_state_1` on `family` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

None found by exact static reference scan.

### Direct SQL writers

- `src/learnloop/learner/lesson_weight.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_reader_rw5d_p4b_teacher_visuals.py`
- `tests/test_rebuild_orchestrator.py`
- `tests/test_teacher_te1_migration.py`
- `tests/test_teacher_te1_successor.py`
- `tests/test_teacher_te1_weight.py`

Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.

## Extension and modification guidance

1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.
2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.
3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.
4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.
5. Update the single owner in `DERIVED_STATE_REPLAYERS`, then prove same-version rebuild equivalence and shadow isolation.

## Live schema DDL

> [!tip] Why keep the DDL here?
> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.

```sql
CREATE TABLE lesson_weight_state (
  family TEXT PRIMARY KEY,
  state_json TEXT NOT NULL,
  updates INTEGER NOT NULL DEFAULT 0 CHECK (updates >= 0),
  through_at TEXT,
  priors_version TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

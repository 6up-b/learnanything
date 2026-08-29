---
title: "exam_pool_items"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite exam_pool_items"
  - "table exam_pool_items"
schema_head: 156
table_name: "exam_pool_items"
table_role: "workflow"
functionality_status: "active"
domain_family: "goals-and-exams"
introduced_in: "023_exam_pool.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/023_exam_pool.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/goals/exam_pool.py"
  - "src/learnloop/content/authoring/practice_generation.py"
  - "src/learnloop/goals/exam_session.py"
  - "src/learnloop/scheduling/controller_ownership.py"
  - "src/learnloop_sidecar/handlers/goals.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/goals-and-exams"
---

# `exam_pool_items`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives exam pool item a stable database identity so goal progress and held-out certification remain tied to the contract and evidence that produced them. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `goal_id`, `practice_item_id`, `facet_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Exam pool: items reserved for a goal's held-out practice exam so ordinary practice cannot contaminate them. A reservation is releasable per goal (released_at set when the exam finishes and the items rejoin practice). An item can sit in at most one *unreleased* pool at a time (partial unique index). facet_id records the primary scope facet the item was reserved to cover; difficulty_stratum is the coarse difficulty bucket used for stratification. Both are provenance for the reservation blueprint, not constraints.

It belongs to the **goals and exams** navigation family. The family context lives in [[Database Catalog#Goals And Exams]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/023_exam_pool.sql`.
- **Schema touched by:** `023_exam_pool.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `goal_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `facet_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `difficulty_stratum` | `TEXT` | no | — | — | Stored value |
| `reserved_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `released_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_exam_pool_goal` on `goal_id`, `released_at`.
- `idx_exam_pool_unreleased_item` on `practice_item_id` (unique).
- `sqlite_autoindex_exam_pool_items_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.insert_exam_pool_items()`
- `Repository.release_exam_pool()`
- `Repository.reserved_exam_pool_item_ids()`
- `Repository.reserved_exam_pool_items()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/authoring/practice_generation.py`
- `src/learnloop/goals/exam_pool.py`
- `src/learnloop/goals/exam_session.py`
- `src/learnloop/scheduling/controller_ownership.py`
- `src/learnloop_sidecar/handlers/goals.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_characterization_assessment_exam.py`
- `tests/test_exam_pool.py`
- `tests/test_goal_scope_material.py`

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
CREATE TABLE exam_pool_items (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  practice_item_id TEXT NOT NULL,
  facet_id TEXT,
  difficulty_stratum TEXT,
  reserved_at TEXT NOT NULL,
  released_at TEXT
);
```

## Related notes

- [[Database Catalog#Goals And Exams|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

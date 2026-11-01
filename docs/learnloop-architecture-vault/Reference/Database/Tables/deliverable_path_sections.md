---
title: "deliverable_path_sections"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "b5ae9988697a3537bfa21426f0070f42e5354f2f"
source_commit_timestamp: "2026-10-31T17:40:16-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite deliverable_path_sections"
  - "table deliverable_path_sections"
schema_head: 228
table_name: "deliverable_path_sections"
table_role: "workflow"
functionality_status: "active"
domain_family: "operations"
introduced_in: "228_deliverable_curriculum.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/228_deliverable_curriculum.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/db/stores/deliverables.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `deliverable_path_sections`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives deliverable path section a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `goal_id`, `learning_object_id`, `extraction_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/228_deliverable_curriculum.sql`.
- **Schema touched by:** `228_deliverable_curriculum.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `goal_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `depth` | `TEXT` | yes | — | — | Stored value |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `extraction_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `section_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `label` | `TEXT` | yes | — | — | Stored value |
| `ordinal` | `INTEGER` | yes | — | — | Stored value |
| `reason` | `TEXT` | yes | — | — | Stored value |
| `exercise_span_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `learner_override` | `TEXT` | no | — | — | Stored value |
| `commitment_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `state_key` | `TEXT` | yes | — | — | Stored value |
| `ledger_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/judgment_ledger\|judgment_ledger.id]] | Stored value |
| `model` | `TEXT` | yes | — | — | Stored value |
| `prompt_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `ledger_id` → [[Reference/Database/Tables/judgment_ledger|`judgment_ledger.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_deliverable_path_sections_reading` on `extraction_id`, `section_id`.
- `idx_deliverable_path_sections_goal` on `goal_id`, `depth`, `created_at`.
- `idx_deliverable_path_sections_judged` on `goal_id`, `depth`, `state_key`, `learning_object_id`, `extraction_id`, `section_id` (unique).
- `sqlite_autoindex_deliverable_path_sections_1` on `id` (unique).

Database triggers:

- `deliverable_path_sections_no_delete` — schema-enforced lifecycle or immutability constraint.
- `deliverable_path_sections_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/deliverables.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_curriculum_c0b_landing.py`
- `tests/test_deliverable_codex_review.py`
- `tests/test_deliverable_curriculum_migration.py`
- `tests/test_deliverable_path.py`
- `tests/test_deliverable_scope.py`

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
CREATE TABLE deliverable_path_sections (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  depth TEXT NOT NULL CHECK (depth IN ('get_the_idea', 'learn_to_use_it', 'fluency')),
  learning_object_id TEXT NOT NULL,
  extraction_id TEXT NOT NULL,
  section_id TEXT NOT NULL,
  label TEXT NOT NULL CHECK (label IN ('core', 'prerequisite', 'alternate', 'already_shown', 'assumed')),
  ordinal INTEGER NOT NULL,
  reason TEXT NOT NULL,
  exercise_span_id TEXT,
  learner_override TEXT CHECK (learner_override IS NULL
    OR learner_override IN ('use_instead', 'read_anyway', 'skip', 'check_later', 'none')),
  commitment_id TEXT,
  state_key TEXT NOT NULL,
  ledger_id TEXT NOT NULL REFERENCES judgment_ledger(id),
  model TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

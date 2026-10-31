---
title: "deliverable_scope_resolutions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "2adf2d18059d6503c417cdc5e0753a7621943065"
source_commit_timestamp: "2026-10-31T14:47:44-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite deliverable_scope_resolutions"
  - "table deliverable_scope_resolutions"
schema_head: 228
table_name: "deliverable_scope_resolutions"
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
  - "src/learnloop/source_retrieval/deliverables.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `deliverable_scope_resolutions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records explicit resolutions of deliverable scope without erasing the original evidence so maintenance and optional operational work remains inspectable without becoming learner-state authority. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `goal_id`, `ledger_id`, `prompt_version`, making the operational relationship explicit. ^table-purpose

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
| `origin` | `TEXT` | yes | — | — | Stored value |
| `input_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `learning_objects_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `unmatched_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `facet_scope_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `state_key` | `TEXT` | yes | — | — | Stored value |
| `ledger_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/judgment_ledger\|judgment_ledger.id]] | Stored value |
| `model` | `TEXT` | yes | — | — | Stored value |
| `prompt_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `ledger_id` → [[Reference/Database/Tables/judgment_ledger|`judgment_ledger.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_deliverable_scope_resolutions_goal` on `goal_id`, `created_at`.
- `sqlite_autoindex_deliverable_scope_resolutions_1` on `id` (unique).

Database triggers:

- `deliverable_scope_resolutions_no_delete` — schema-enforced lifecycle or immutability constraint.
- `deliverable_scope_resolutions_no_update` — schema-enforced lifecycle or immutability constraint.

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

- `tests/test_deliverable_curriculum_migration.py`
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
CREATE TABLE deliverable_scope_resolutions (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  origin TEXT NOT NULL CHECK (origin IN ('resolver', 'learner')),
  input_ids_json TEXT NOT NULL DEFAULT '[]',
  learning_objects_json TEXT NOT NULL DEFAULT '[]',
  unmatched_json TEXT NOT NULL DEFAULT '[]',
  facet_scope_json TEXT NOT NULL DEFAULT '{}',
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

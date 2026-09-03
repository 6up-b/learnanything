---
title: "goal_contract_heads"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite goal_contract_heads"
  - "table goal_contract_heads"
schema_head: 157
table_name: "goal_contract_heads"
table_role: "workflow"
functionality_status: "active"
domain_family: "goals-and-exams"
introduced_in: "068_goal_terminal_contracts.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/068_goal_terminal_contracts.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/goals/goal_contracts.py"
  - "src/learnloop/ops/doctor.py"
  - "src/learnloop/curriculum/golden_path_confirm.py"
  - "src/learnloop/curriculum/golden_path_run.py"
  - "src/learnloop/curriculum/pattern_ladder.py"
  - "src/learnloop/diagnosis/failure_triage.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/goals-and-exams"
---

# `goal_contract_heads`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Points workflow consumers at the current goal-contract version. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `goal_id`, `head_version_id`, `head_version`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> ---------------------------------------------------------------------------- goal_contract_heads (§3.4): the current-head projection. One row per goal, rewritten on every appended successor (a derived projection, not raw history, so it is safe to UPDATE -- unlike the immutable version rows). ----------------------------------------------------------------------------

It belongs to the **goals and exams** navigation family. The family context lives in [[Database Catalog#Goals And Exams]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/068_goal_terminal_contracts.sql`.
- **Schema touched by:** `068_goal_terminal_contracts.sql`, `069_parameter_registry.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `goal_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `head_version_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/goal_contract_versions\|goal_contract_versions.id]] | Stored value |
| `head_version` | `INTEGER` | yes | — | — | Stored value |
| `head_content_hash` | `TEXT` | yes | — | — | Stored value |
| `head_support_hash` | `TEXT` | yes | — | — | Stored value |
| `head_envelope_version` | `TEXT` | no | — | — | Stored value |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `head_version_id` → [[Reference/Database/Tables/goal_contract_versions|`goal_contract_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_goal_contract_heads_1` on `goal_id` (unique).

## Who calls it

### Repository access surface

- `Repository.append_goal_contract_version()`
- `Repository.confirm_golden_path_atomic()`
- `Repository.fetch_goal_contract_head()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/curriculum/golden_path_confirm.py`
- `src/learnloop/curriculum/golden_path_run.py`
- `src/learnloop/curriculum/pattern_ladder.py`
- `src/learnloop/diagnosis/failure_triage.py`
- `src/learnloop/goals/goal_contracts.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_failure_triage.py`
- `tests/test_goal_contracts.py`
- `tests/test_golden_path_assessment.py`
- `tests/test_golden_path_confirm.py`
- `tests/test_golden_path_run.py`
- `tests/test_p2_acceptance.py`

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
CREATE TABLE goal_contract_heads (
  goal_id TEXT PRIMARY KEY,
  head_version_id TEXT NOT NULL REFERENCES goal_contract_versions(id),
  head_version INTEGER NOT NULL,
  head_content_hash TEXT NOT NULL,
  head_support_hash TEXT NOT NULL,
  head_envelope_version TEXT,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Goals And Exams|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

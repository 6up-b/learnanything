---
title: "goal_contract_versions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite goal_contract_versions"
  - "table goal_contract_versions"
schema_head: 157
table_name: "goal_contract_versions"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "goals-and-exams"
introduced_in: "068_goal_terminal_contracts.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/068_goal_terminal_contracts.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/ops/doctor.py"
  - "src/learnloop/cli/contracts.py"
  - "src/learnloop/curriculum/golden_path_confirm.py"
  - "src/learnloop/curriculum/golden_path_fixture.py"
  - "src/learnloop/goals/goal_contracts.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/goals-and-exams"
---

# `goal_contract_versions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Stores immutable goal-contract versions. It supplies replay-stable input rather than a disposable cache. Rows bind `goal_id`, `predecessor_version_id`, `activated_edge_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **goals and exams** navigation family. The family context lives in [[Database Catalog#Goals And Exams]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/068_goal_terminal_contracts.sql`.
- **Schema touched by:** `068_goal_terminal_contracts.sql`, `081_task_blueprints.sql`, `082_golden_path_runs.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `goal_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `version` | `INTEGER` | yes | — | — | Stored value |
| `predecessor_version_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/goal_contract_versions\|goal_contract_versions.id]] | Stored value |
| `contract_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `support_hash` | `TEXT` | yes | — | — | Stored value |
| `contract_schema_version` | `INTEGER` | yes | — | — | Stored value |
| `change_class` | `TEXT` | yes | — | — | Stored value |
| `envelope_version` | `TEXT` | no | — | — | Stored value |
| `predecessor_milestone` | `TEXT` | no | — | — | Stored value |
| `activated_edge_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `evidence_receipt_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `burden_delta_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `author` | `TEXT` | yes | — | — | Stored value |
| `reason` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `predecessor_version_id` → [[Reference/Database/Tables/goal_contract_versions|`goal_contract_versions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_gcv_support` on `goal_id`, `support_hash`.
- `idx_gcv_goal` on `goal_id`.
- `sqlite_autoindex_goal_contract_versions_3` on `goal_id`, `content_hash` (unique).
- `sqlite_autoindex_goal_contract_versions_2` on `goal_id`, `version` (unique).
- `sqlite_autoindex_goal_contract_versions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.append_goal_contract_version()`
- `Repository.confirm_golden_path_atomic()`
- `Repository.fetch_goal_contract_version()`
- `Repository.goal_contract_versions_for_goal()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/contracts.py`
- `src/learnloop/curriculum/golden_path_confirm.py`
- `src/learnloop/curriculum/golden_path_fixture.py`
- `src/learnloop/goals/goal_contracts.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_goal_contracts.py`

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
CREATE TABLE goal_contract_versions (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  version INTEGER NOT NULL CHECK (version >= 1),
  predecessor_version_id TEXT REFERENCES goal_contract_versions(id),
  contract_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  support_hash TEXT NOT NULL,
  contract_schema_version INTEGER NOT NULL,
  change_class TEXT NOT NULL CHECK (change_class IN (
    'confirm', 'support_change', 'authorized_depth_step',
    'evaluation_change', 'reweight', 'metadata'
  )),
  -- authorized_depth_step receipt columns (§3.4); NULL for every other class:
  envelope_version TEXT,
  predecessor_milestone TEXT,
  activated_edge_id TEXT,
  evidence_receipt_json TEXT,
  burden_delta_json TEXT,
  author TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(goal_id, version),
  UNIQUE(goal_id, content_hash)
);
```

## Related notes

- [[Database Catalog#Goals And Exams|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

---
title: "forecasts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite forecasts"
  - "table forecasts"
schema_head: 156
table_name: "forecasts"
table_role: "workflow"
functionality_status: "active"
domain_family: "goals-and-exams"
introduced_in: "057_forecast_ledger.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/057_forecast_ledger.sql"
  - "src/learnloop/config/compat.py"
  - "src/learnloop/config/template.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/goals/forecast_ledger.py"
  - "src/learnloop/ops/doctor.py"
  - "src/learnloop/params/parameter_registry.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/goals-and-exams"
---

# `forecasts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives forecast a stable database identity so goal progress and held-out certification remain tied to the contract and evidence that produced them. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `goal_id`, `algorithm_version`, `resolution_rule_version`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Frozen, gradeable learner-facing forecasts. Rendering references these rows; it never mints a forecast implicitly.

It belongs to the **goals and exams** navigation family. The family context lives in [[Database Catalog#Goals And Exams]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/057_forecast_ledger.sql`.
- **Schema touched by:** `057_forecast_ledger.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `goal_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `issued_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `as_of_input_snapshot_hash` | `TEXT` | yes | — | — | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `resolution_rule_version` | `TEXT` | yes | — | — | Stored value |
| `horizon` | `TEXT` | yes | — | — | Stored value |
| `target_metric` | `TEXT` | yes | — | — | Stored value |
| `predicted_value` | `REAL` | yes | — | — | Stored value |
| `model_coverage_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | `'open'` | — | Stored value |
| `resolved_value` | `REAL` | no | — | — | Stored value |
| `resolved_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `projection_drift` | `REAL` | no | — | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_forecasts_goal` on `goal_id`, `issued_at`, `id`.
- `idx_forecasts_due` on `status`, `horizon`.
- `sqlite_autoindex_forecasts_2` on `goal_id`, `kind`, `as_of_input_snapshot_hash` (unique).
- `sqlite_autoindex_forecasts_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.due_forecasts()`
- `Repository.forecast()`
- `Repository.insert_forecast()`
- `Repository.list_forecasts()`
- `Repository.open_forecasts()`
- `Repository.update_forecast_resolution()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/db/repositories.py`
- `src/learnloop/goals/forecast_ledger.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_config_refactor.py`
- `tests/test_doctor.py`
- `tests/test_forecast_ledger.py`
- `tests/test_sidecar_goals.py`

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
CREATE TABLE forecasts (
  id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('decay', 'pace', 'plan')),
  issued_at TEXT NOT NULL,
  as_of_input_snapshot_hash TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  resolution_rule_version TEXT NOT NULL,
  horizon TEXT NOT NULL,
  target_metric TEXT NOT NULL,
  predicted_value REAL NOT NULL,
  model_coverage_json TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'open'
    CHECK (status IN ('open', 'resolved', 'censored', 'unobservable')),
  resolved_value REAL,
  resolved_at TEXT,
  projection_drift REAL,
  UNIQUE(goal_id, kind, as_of_input_snapshot_hash)
);
```

## Related notes

- [[Database Catalog#Goals And Exams|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

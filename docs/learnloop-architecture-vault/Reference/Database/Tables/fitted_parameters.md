---
title: "fitted_parameters"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite fitted_parameters"
  - "table fitted_parameters"
schema_head: 156
table_name: "fitted_parameters"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "schema-and-change"
introduced_in: "016_fitted_parameters.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/016_fitted_parameters.sql"
  - "src/learnloop/cli/fit.py"
  - "src/learnloop/config/template.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/params/fitted_params.py"
  - "src/learnloop/diagnosis/causal_orchestrator.py"
  - "src/learnloop/diagnosis/causal_probe_coherence.py"
  - "src/learnloop/diagnosis/gate_score.py"
  - "src/learnloop/goals/certification_cold_probe.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/schema-and-change"
---

# `fitted_parameters`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives fitted parameter a stable database identity so schema changes and reviewed mutations remain reproducible and auditable. It supplies replay-stable input rather than a disposable cache. Rows bind `algorithm_version`, `scope`, `fitted_at`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Fitted-parameter store (architecture_pivot.md Stage 1). Versioned home for parameter sets learned from the learner's own logs (FSRS weights, follow-up gate logistic weights, future scopes). Fitted sets are INPUTS to replay, not derived state: rebuild-derived-state must never clear this table. At most one active row per scope, enforced transactionally in the repository (deactivate-then-insert); history rows are never deleted so every replay is auditable back to the parameter set that produced it.

It belongs to the **schema and change** navigation family. The family context lives in [[Database Catalog#Schema And Change]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/016_fitted_parameters.sql`.
- **Schema touched by:** `016_fitted_parameters.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `scope` | `TEXT` | yes | — | — | Stored value |
| `params_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `fitted_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `training_rows_count` | `INTEGER` | yes | — | — | Stored value |
| `training_data_through` | `TEXT` | no | — | — | Stored value |
| `metrics_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `active` | `INTEGER` | yes | `0` | — | Stored value |
| `deactivated_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_fitted_parameters_scope_active` on `scope`, `active`, `fitted_at`.
- `sqlite_autoindex_fitted_parameters_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.active_fitted_parameters()`
- `Repository.deactivate_fitted_parameters()`
- `Repository.insert_fitted_parameters()`
- `Repository.list_fitted_parameters()`
- `Repository.reset_learning_object_derived_state()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/fit.py`
- `src/learnloop/diagnosis/causal_orchestrator.py`
- `src/learnloop/diagnosis/causal_probe_coherence.py`
- `src/learnloop/diagnosis/gate_score.py`
- `src/learnloop/goals/certification_cold_probe.py`
- `src/learnloop/params/fitted_params.py`
- `src/learnloop/substrate/replay.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_cli_fit.py`
- `tests/test_grader_channel_prior_knobs.py`
- `tests/test_fitted_parameters.py`
- `tests/test_gate_score.py`
- `tests/test_item_parameters.py`

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
CREATE TABLE fitted_parameters (
  id TEXT PRIMARY KEY,
  scope TEXT NOT NULL,
  params_json TEXT NOT NULL,
  fitted_at TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  training_rows_count INTEGER NOT NULL,
  training_data_through TEXT,
  metrics_json TEXT,
  active INTEGER NOT NULL DEFAULT 0 CHECK (active IN (0, 1)),
  deactivated_at TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Schema And Change|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

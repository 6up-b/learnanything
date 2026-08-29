---
title: "item_parameter_state"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite item_parameter_state"
  - "table item_parameter_state"
schema_head: 156
table_name: "item_parameter_state"
table_role: "derived"
functionality_status: "active"
domain_family: "schema-and-change"
introduced_in: "016_fitted_parameters.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/016_fitted_parameters.sql"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
  - "src/learnloop/substrate/replay.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/schema-and-change"
---

# `item_parameter_state`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Materializes learned item-parameter state reconstructed from attempt evidence. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `practice_item_id`, `algorithm_version`, `b_mean`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Per-item empirical-Bayes difficulty posterior (Fable's-take item 5). The authored vault difficulty stays the prior mean; this row is the posterior that shrinks toward it as evidence accumulates. Derived state: cleared by reset_learning_object_derived_state and rebuilt by replay.

It belongs to the **schema and change** navigation family. The family context lives in [[Database Catalog#Schema And Change]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/016_fitted_parameters.sql`.
- **Schema touched by:** `016_fitted_parameters.sql`.
- **Rebuild owner:** `learning_state`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `practice_item_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `b_mean` | `REAL` | yes | — | — | Stored value |
| `b_var` | `REAL` | yes | — | — | Stored value |
| `evidence_count` | `INTEGER` | yes | `0` | — | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_item_parameter_state_1` on `practice_item_id` (unique).

## Who calls it

### Repository access surface

- `Repository._upsert_item_parameter_state_record()`
- `Repository.item_parameter_state()`
- `Repository.item_parameter_states()`
- `Repository.record_attempt_outcome()`
- `Repository.replace_attempt_derived_outcome()`
- `Repository.reset_learning_object_derived_state()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/substrate/replay.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_item_parameters.py`
- `tests/test_rebuild_orchestrator.py`

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
CREATE TABLE item_parameter_state (
  practice_item_id TEXT PRIMARY KEY,
  b_mean REAL NOT NULL,
  b_var REAL NOT NULL,
  evidence_count INTEGER NOT NULL DEFAULT 0,
  algorithm_version TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Schema And Change|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

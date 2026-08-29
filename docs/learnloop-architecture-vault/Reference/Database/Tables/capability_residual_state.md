---
title: "capability_residual_state"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite capability_residual_state"
  - "table capability_residual_state"
schema_head: 156
table_name: "capability_residual_state"
table_role: "derived"
functionality_status: "active"
domain_family: "learner-state"
introduced_in: "050_capability_residual_and_identifiability.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/050_capability_residual_and_identifiability.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
  - "src/learnloop/substrate/canonical_projection.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/learner-state"
---

# `capability_residual_state`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Materializes capability residuals after canonical facet evidence has been projected. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `facet_id`, `algorithm_version`, `activation_reason`, making the operational relationship explicit. ^table-purpose

It belongs to the **learner state** navigation family. The family context lives in [[Database Catalog#Learner State]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/050_capability_residual_and_identifiability.sql`.
- **Schema touched by:** `050_capability_residual_and_identifiability.sql`.
- **Rebuild owner:** `canonical_projection`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `facet_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `capability` | `TEXT` | yes | — | — | Stored value |
| `active` | `INTEGER` | yes | `0` | — | Stored value |
| `activation_reason` | `TEXT` | no | — | — | Stored value |
| `residual_alpha` | `REAL` | yes | — | — | Stored value |
| `residual_beta` | `REAL` | yes | — | — | Stored value |
| `residual_mean` | `REAL` | yes | — | — | Stored value |
| `parent_alpha` | `REAL` | yes | — | — | Stored value |
| `parent_beta` | `REAL` | yes | — | — | Stored value |
| `parent_mean` | `REAL` | yes | — | — | Stored value |
| `divergence` | `REAL` | yes | `0` | — | Stored value |
| `independent_groups` | `INTEGER` | yes | `0` | — | Stored value |
| `independent_mass` | `REAL` | yes | `0` | — | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_capability_residual_active` on `active`, `facet_id`.
- `sqlite_autoindex_capability_residual_state_2` on `facet_id`, `capability` (unique).
- `sqlite_autoindex_capability_residual_state_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.capability_residual_state()`
- `Repository.capability_residual_states()`
- `Repository.replace_capability_residual_state()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/substrate/canonical_projection.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_rebuild_orchestrator.py`
- `tests/test_capability_residual.py`
- `tests/test_km5_sim_gates.py`

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
CREATE TABLE capability_residual_state (
  id TEXT PRIMARY KEY,
  facet_id TEXT NOT NULL,
  capability TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 0,
  activation_reason TEXT,
  residual_alpha REAL NOT NULL,
  residual_beta REAL NOT NULL,
  residual_mean REAL NOT NULL,
  parent_alpha REAL NOT NULL,
  parent_beta REAL NOT NULL,
  parent_mean REAL NOT NULL,
  divergence REAL NOT NULL DEFAULT 0,
  independent_groups INTEGER NOT NULL DEFAULT 0,
  independent_mass REAL NOT NULL DEFAULT 0,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(facet_id, capability)
);
```

## Related notes

- [[Database Catalog#Learner State|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

---
title: "item_forecast_scores"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "3d7dd4b116294c885c097ab498fc25532ad57d25"
source_commit_timestamp: "2026-10-27T10:21:01-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite item_forecast_scores"
  - "table item_forecast_scores"
schema_head: 225
table_name: "item_forecast_scores"
table_role: "derived"
functionality_status: "active"
domain_family: "operations"
introduced_in: "214_adaptive_difficulty_serving.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/214_adaptive_difficulty_serving.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/adaptive_difficulty/scoring.py"
  - "src/learnloop/db/stores/ad_serving.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `item_forecast_scores`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives item forecast score a stable database identity so maintenance and optional operational work remains inspectable without becoming learner-state authority. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `receipt_id`, `practice_item_id`, `plan_presentation_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §8.3 (DERIVED; the forecast-score replayer): each valid item forecast receipt joined to its bound attempt through plan_presentations, with §5.3's event read exactly as the update reads it and the scores and splits.

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/214_adaptive_difficulty_serving.sql`.
- **Schema touched by:** `214_adaptive_difficulty_serving.sql`.
- **Rebuild owner:** `item_forecast_scores`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `receipt_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `forecaster` | `TEXT` | yes | — | — | Stored value |
| `practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `plan_presentation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `p` | `REAL` | no | — | — | Stored value |
| `outcome` | `REAL` | no | — | — | Stored value |
| `status` | `TEXT` | yes | — | — | Stored value |
| `log_loss` | `REAL` | no | — | — | Stored value |
| `brier` | `REAL` | no | — | — | Stored value |
| `first_attempt_lo` | `INTEGER` | no | — | — | Stored value |
| `first_surface_cell` | `INTEGER` | no | — | — | Stored value |
| `capability` | `TEXT` | no | — | — | Stored value |
| `detail_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_item_forecast_scores_1` on `receipt_id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

None found by exact static reference scan.

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_ad23_contract.py`
- `tests/test_ad23_migration.py`
- `tests/test_ad23_successor.py`
- `tests/test_ad2_model.py`
- `tests/test_ad_guard.py`
- `tests/test_architecture.py`
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
CREATE TABLE item_forecast_scores (
  receipt_id TEXT PRIMARY KEY,
  forecaster TEXT NOT NULL,
  practice_item_id TEXT,
  plan_presentation_id TEXT,
  attempt_id TEXT,
  p REAL,
  outcome REAL,
  status TEXT NOT NULL CHECK (status IN ('scored', 'pending', 'pre_exposed', 'invalid', 'excluded')),
  log_loss REAL,
  brier REAL,
  first_attempt_lo INTEGER,
  first_surface_cell INTEGER,
  capability TEXT,
  detail_json TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

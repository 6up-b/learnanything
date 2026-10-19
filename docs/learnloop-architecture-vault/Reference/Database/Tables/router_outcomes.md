---
title: "router_outcomes"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "3da2da5b00f680568bdbc2021273b7e1b8b2d94e"
source_commit_timestamp: "2026-10-19T02:08:13-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite router_outcomes"
  - "table router_outcomes"
schema_head: 213
table_name: "router_outcomes"
table_role: "derived"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "181_router_decisions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/181_router_decisions.sql"
  - "src/learnloop/cli/router.py"
  - "src/learnloop/daily_plan/router_retrieval.py"
  - "src/learnloop/db/stores/router.py"
  - "src/learnloop/evsi_calibration/live_report.py"
  - "src/learnloop/probe_tie_upgrade.py"
  - "src/learnloop/router/outcomes.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `router_outcomes`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records the measured outcome and lineage for router so queue and controller decisions can resume safely and explain why an activity was selected. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `decision_id`, `target_practice_item_id`, `target_learning_object_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/181_router_decisions.sql`.
- **Schema touched by:** `181_router_decisions.sql`, `184_voi_forecasts.sql`, `202_router_staged_frame.sql`.
- **Rebuild owner:** `router_outcomes`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `decision_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `outcome_version` | `TEXT` | yes | — | — | Stored value |
| `target_practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `target_learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `action_status` | `TEXT` | yes | — | — | Stored value |
| `action_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `r_next_status` | `TEXT` | yes | — | — | Stored value |
| `r_next_value` | `REAL` | no | — | — | Stored value |
| `r_next_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `r_next_elapsed_seconds` | `INTEGER` | no | — | — | Stored value |
| `r_next_skipped` | `INTEGER` | yes | `0` | — | Stored value |
| `r_cold_status` | `TEXT` | yes | — | — | Stored value |
| `r_cold_value` | `REAL` | no | — | — | Stored value |
| `r_cold_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `r_cold_gap_seconds` | `INTEGER` | no | — | — | Stored value |
| `r_cold_skipped` | `INTEGER` | yes | `0` | — | Stored value |
| `r_next_since_item_seconds` | `INTEGER` | no | — | — | Stored value |
| `r_next_since_facet_seconds` | `INTEGER` | no | — | — | Stored value |
| `r_next_since_lo_seconds` | `INTEGER` | no | — | — | Stored value |
| `r_next_intervening_attempts` | `INTEGER` | no | — | — | Stored value |
| `r_next_predicted_retrievability` | `REAL` | no | — | — | Stored value |
| `r_next_reveal_amount` | `REAL` | no | — | — | Stored value |
| `r_cold_since_item_seconds` | `INTEGER` | no | — | — | Stored value |
| `r_cold_since_facet_seconds` | `INTEGER` | no | — | — | Stored value |
| `r_cold_since_lo_seconds` | `INTEGER` | no | — | — | Stored value |
| `r_cold_intervening_attempts` | `INTEGER` | no | — | — | Stored value |
| `r_cold_predicted_retrievability` | `REAL` | no | — | — | Stored value |
| `r_cold_reveal_amount` | `REAL` | no | — | — | Stored value |
| `coldness_candidates_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `s_status` | `TEXT` | yes | — | — | Stored value |
| `s_value` | `REAL` | no | — | — | Stored value |
| `s_alpha` | `REAL` | yes | — | — | Stored value |
| `observed_through` | `TEXT` | no | — | — | Stored value |
| `detail_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `action_binding` | `TEXT` | no | — | — | Stored value |
| `r_next_reference_status` | `TEXT` | no | — | — | Stored value |
| `r_cold_reference_status` | `TEXT` | no | — | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `router_outcomes_target` on `target_learning_object_id`.
- `sqlite_autoindex_router_outcomes_1` on `decision_id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/router.py`
- `src/learnloop/evsi_calibration/live_report.py`

### Direct SQL writers

- `src/learnloop/db/stores/router.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_daily_plan_replay.py`
- `tests/test_evsi_router_composition.py`
- `tests/test_held_grade_composition.py`
- `tests/test_mvp015_upgrade.py`
- `tests/test_rebuild_orchestrator.py`
- `tests/test_router_coldness_covariates.py`
- `tests/test_router_outcomes.py`
- `tests/test_router_presentations.py`
- `tests/test_router_r1_composition.py`
- `tests/test_router_r2a_serving.py`
- `tests/test_router_r2b_agreement.py`
- `tests/test_voi_forecasts.py`

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
CREATE TABLE router_outcomes (
  decision_id TEXT PRIMARY KEY,
  outcome_version TEXT NOT NULL,
  target_practice_item_id TEXT,
  target_learning_object_id TEXT,
  -- not_taken: the session ended without the chosen candidate attempted.
  action_status TEXT NOT NULL CHECK (
    action_status IN ('taken', 'open', 'superseded', 'overridden', 'not_taken', 'not_applicable')
  ),
  action_attempt_id TEXT,
  r_next_status TEXT NOT NULL CHECK (r_next_status IN ('observed', 'pending', 'not_applicable')),
  r_next_value REAL CHECK (r_next_value IS NULL OR (r_next_value >= 0 AND r_next_value <= 1)),
  r_next_attempt_id TEXT,
  r_next_elapsed_seconds INTEGER,
  r_next_skipped INTEGER NOT NULL DEFAULT 0,
  r_cold_status TEXT NOT NULL CHECK (r_cold_status IN ('observed', 'pending', 'not_applicable')),
  r_cold_value REAL CHECK (r_cold_value IS NULL OR (r_cold_value >= 0 AND r_cold_value <= 1)),
  r_cold_attempt_id TEXT,
  r_cold_gap_seconds INTEGER,
  r_cold_skipped INTEGER NOT NULL DEFAULT 0,
  -- Coldness covariates of the R_next and R_cold attempts (NULL while the
  -- outcome is not observed, or when the input does not exist: no earlier
  -- exposure, no FSRS memory before the attempt).
  r_next_since_item_seconds INTEGER,
  r_next_since_facet_seconds INTEGER,
  r_next_since_lo_seconds INTEGER,
  r_next_intervening_attempts INTEGER CHECK (r_next_intervening_attempts IS NULL OR r_next_intervening_attempts >= 0),
  r_next_predicted_retrievability REAL CHECK (
    r_next_predicted_retrievability IS NULL OR (r_next_predicted_retrievability >= 0 AND r_next_predicted_retrievability <= 1)
  ),
  r_next_reveal_amount REAL CHECK (r_next_reveal_amount IS NULL OR r_next_reveal_amount >= 0),
  r_cold_since_item_seconds INTEGER,
  r_cold_since_facet_seconds INTEGER,
  r_cold_since_lo_seconds INTEGER,
  r_cold_intervening_attempts INTEGER CHECK (r_cold_intervening_attempts IS NULL OR r_cold_intervening_attempts >= 0),
  r_cold_predicted_retrievability REAL CHECK (
    r_cold_predicted_retrievability IS NULL OR (r_cold_predicted_retrievability >= 0 AND r_cold_predicted_retrievability <= 1)
  ),
  r_cold_reveal_amount REAL CHECK (r_cold_reveal_amount IS NULL OR r_cold_reveal_amount >= 0),
  coldness_candidates_json TEXT NOT NULL DEFAULT '[]',
  s_status TEXT NOT NULL CHECK (s_status IN ('final', 'provisional', 'pending', 'not_applicable')),
  s_value REAL CHECK (s_value IS NULL OR (s_value >= 0 AND s_value <= 1)),
  s_alpha REAL NOT NULL,
  observed_through TEXT,
  detail_json TEXT NOT NULL
, action_binding TEXT CHECK (
  action_binding IS NULL OR action_binding IN ('presentation', 'candidate', 'session_rule')
), r_next_reference_status TEXT, r_cold_reference_status TEXT);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

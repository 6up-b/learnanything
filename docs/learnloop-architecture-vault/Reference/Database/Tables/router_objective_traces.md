---
title: "router_objective_traces"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite router_objective_traces"
  - "table router_objective_traces"
table_name: "router_objective_traces"
table_role: "receipt"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "246_router_objective_traces.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/246_router_objective_traces.sql"
  - "src/learnloop/daily_plan/objective_chooser.py"
  - "src/learnloop/db/stores/router.py"
  - "src/learnloop/db/stores/router_objective.py"
  - "src/learnloop/lesson_offers_upgrade.py"
  - "src/learnloop/router_objective/calibration_report.py"
  - "src/learnloop/router_objective/combiner_data.py"
  - "src/learnloop/router_objective/forecast_resolve.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `router_objective_traces`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives router objective trace a stable database identity so queue and controller decisions can resume safely and explain why an activity was selected. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `decision_id`, `decision_state_id`, `session_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/246_router_objective_traces.sql`.
- **Schema touched by:** `246_router_objective_traces.sql`, `247_lesson_episodes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `decision_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `decision_kind` | `TEXT` | yes | — | — | Stored value |
| `decision_state_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `trace_version` | `TEXT` | yes | — | — | Stored value |
| `objective_version` | `TEXT` | yes | — | — | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `local_date` | `TEXT` | yes | — | — | Stored value |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `session_minutes` | `REAL` | no | — | — | Stored value |
| `remembered_minutes` | `REAL` | no | — | — | Stored value |
| `kappa0` | `REAL` | no | — | — | Stored value |
| `kappa_how` | `TEXT` | no | — | — | Stored value |
| `kappa_regime` | `TEXT` | no | — | — | Stored value |
| `chosen_ref` | `TEXT` | yes | — | — | Stored value |
| `drawn_component` | `TEXT` | no | — | — | Stored value |
| `propensity` | `REAL` | no | — | — | Stored value |
| `w` | `REAL` | no | — | — | Stored value |
| `numeric_ref` | `TEXT` | no | — | — | Stored value |
| `llm_status` | `TEXT` | no | — | — | Stored value |
| `numeric_status` | `TEXT` | no | — | — | Stored value |
| `stop_in_support` | `INTEGER` | yes | — | — | Stored value |
| `guard_crossed` | `INTEGER` | yes | `0` | — | Stored value |
| `window_closes_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `trace_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_router_objective_traces_created` on `created_at`.
- `idx_router_objective_traces_local_date` on `local_date`, `created_at`.
- `sqlite_autoindex_router_objective_traces_2` on `decision_id` (unique).
- `sqlite_autoindex_router_objective_traces_1` on `id` (unique).

Database triggers:

- `router_objective_traces_no_delete` — schema-enforced lifecycle or immutability constraint.
- `router_objective_traces_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/daily_plan/objective_chooser.py`
- `src/learnloop/db/stores/router_objective.py`
- `src/learnloop/router_objective/calibration_report.py`
- `src/learnloop/router_objective/combiner_data.py`
- `src/learnloop/router_objective/forecast_resolve.py`
- `src/learnloop/router_objective/goal_read.py`
- `src/learnloop/router_objective/objective_report.py`
- `src/learnloop/router_objective/offer_report.py`
- `src/learnloop/router_objective/preference_report.py`
- `src/learnloop/router_objective/scores.py`
- `src/learnloop/router_objective/stop_coin.py`
- `src/learnloop/router_objective/tail_data.py`
- `src/learnloop/router_objective/tail_report.py`
- `src/learnloop/teacher/episodes.py`

### Direct SQL writers

None found by exact static reference scan.

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_ih2_lessons_compete.py`
- `tests/test_ih3_phone_host.py`
- `tests/test_instruct_handoff_ih0.py`
- `tests/test_ro4_trace_report.py`
- `tests/test_ro4_traces_migration.py`
- `tests/test_ro5_checks.py`
- `tests/test_ro5_codex_review.py`
- `tests/test_ro5_landing.py`
- `tests/test_rofu_learning.py`
- `tests/test_rospeed_join.py`
- `tests/test_te3b_binding.py`

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
CREATE TABLE router_objective_traces (
  id TEXT PRIMARY KEY,
  -- router_decisions.id of the decision (plan_block or plan_interrupt).
  decision_id TEXT NOT NULL UNIQUE,
  decision_kind TEXT NOT NULL CHECK (decision_kind IN ('plan_block', 'plan_interrupt')),
  -- RO0's decision_state_receipts.id (§4 row 9), when one was written.
  decision_state_id TEXT,
  -- The trace's and the objective's code versions (router_objective.trace,
  -- router_objective.value).
  trace_version TEXT NOT NULL,
  objective_version TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  -- The plan's local date (the price's daily seed is per local date).
  local_date TEXT NOT NULL,
  session_id TEXT,
  -- Active minutes in the objective's session at the decision, and the
  -- plan's remembered minutes m-bar.
  session_minutes REAL,
  remembered_minutes REAL,
  -- kappa0 in force and how it was set (day_seed, carried_today,
  -- carried_last, tail_average, floored_at_last_positive); until RO5 the
  -- regime is the seed.
  kappa0 REAL,
  kappa_how TEXT,
  kappa_regime TEXT,
  -- The served choice, the component whose draw chose it, its exact
  -- probability, the weight w_i and the numeric policy's choice.
  chosen_ref TEXT NOT NULL,
  drawn_component TEXT,
  propensity REAL CHECK (propensity IS NULL OR (propensity > 0 AND propensity <= 1)),
  w REAL CHECK (w IS NULL OR (w >= 0 AND w <= 1)),
  numeric_ref TEXT,
  -- Each policy's status: answered, timeout, failed, invalid, spend,
  -- not_ready, unreachable (a failure's share went to staged).
  llm_status TEXT,
  numeric_status TEXT,
  -- Whether stop was in the support, and whether the runaway guard's
  -- session minutes were crossed (reported, never a budget).
  stop_in_support INTEGER NOT NULL CHECK (stop_in_support IN (0, 1)),
  guard_crossed INTEGER NOT NULL DEFAULT 0 CHECK (guard_crossed IN (0, 1)),
  -- When the decision's evaluation window B closes (its score can form only
  -- after it, from outcomes in it).
  window_closes_at TEXT,
  trace_json TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

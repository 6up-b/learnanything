---
title: "daily_plans"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "ca2c0b7e37edfb7cc303e8a6ae97cdcf99124ffd"
source_commit_timestamp: "2026-10-27T18:06:05-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite daily_plans"
  - "table daily_plans"
schema_head: 226
table_name: "daily_plans"
table_role: "workflow"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "180_daily_plans.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/180_daily_plans.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/daily_plan/engine.py"
  - "src/learnloop/daily_plan/estimates.py"
  - "src/learnloop/daily_plan/lanes.py"
  - "src/learnloop/daily_plan/records.py"
  - "src/learnloop/daily_plan/router_card.py"
  - "src/learnloop/daily_plan_upgrade.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `daily_plans`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Holds each local day's finite daily plan (daily-loop DL1, mvp-0.14): its kind (normal, re-entry or a keep-going extension), budget and remembered minutes, the split_v1 lane minutes and the new-material admission it was built with, and its status. Its blocks are attention_blocks rows (daily_plan_id, plan_ordinal, lane, chosen_by) whose every decision is an attention_block_events receipt; nothing here is evidence and replay never reads it. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `parent_plan_id`, `estimator_version`, `algorithm_version`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Daily-loop DL1 (daily_plan_v1, mvp-0.14): the finite daily plan (built as migration 174 at mvp-0.12; renumbered 180 and relabelled mvp-0.14 when it merged after main's 174-179, none of which touches attention_blocks or facet_outcome_observations) (spec_daily_loop_v1.md §6, §10). Workflow and receipt rows only: nothing here is evidence, mastery, certification or FSRS state, and replay never reads it. One plan per local calendar date and kind: the day's normal (or re-entry) plan and its "keep going" extensions, linked by parent_plan_id. Mutable workflow state (status, budget after a minutes tap); the decisions that built it are attention_block_events receipts.

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/180_daily_plans.sql`.
- **Schema touched by:** `180_daily_plans.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `local_date` | `TEXT` | yes | — | — | Stored value |
| `kind` | `TEXT` | yes | — | — | Stored value |
| `parent_plan_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/daily_plans\|daily_plans.id]] | Stored value |
| `minutes_budget` | `REAL` | yes | — | — | Stored value |
| `remembered_minutes` | `INTEGER` | yes | — | — | Stored value |
| `minutes_source` | `TEXT` | yes | — | — | Stored value |
| `split_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `admission_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `estimator_version` | `TEXT` | yes | — | — | Stored value |
| `source` | `TEXT` | yes | — | — | Stored value |
| `chooser` | `TEXT` | yes | — | — | Stored value |
| `status` | `TEXT` | yes | `'open'` | — | Stored value |
| `stop_reason` | `TEXT` | no | — | — | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `config_hash` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `completed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `parent_plan_id` → [[Reference/Database/Tables/daily_plans|`daily_plans.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_daily_plans_date` on `local_date`, `created_at`, `id`.
- `sqlite_autoindex_daily_plans_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/daily_plan/engine.py`
- `src/learnloop/db/stores/daily_plans.py`

### Direct SQL writers

- `src/learnloop/db/stores/daily_plans.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/figure_fixtures.py`
- `tests/source_service_fakes.py`
- `tests/test_ad23_contract.py`
- `tests/test_ad_guard.py`
- `tests/test_architecture.py`
- `tests/test_daily_plan_kill_switch.py`
- `tests/test_daily_plan_reading.py`
- `tests/test_daily_plan_replay.py`
- `tests/test_exam_protection_identity.py`
- `tests/test_mcp_tools.py`
- `tests/test_mvp014_upgrade.py`
- `tests/test_plan_determinism.py`
- `tests/test_plan_follows_path.py`
- `tests/test_reader_rw3b_protection.py`
- `tests/test_reading_step_switch.py`
- `tests/test_router_card.py`
- `tests/test_rw7b_fix_round2.py`
- `tests/test_voi_merge_composition.py`

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
CREATE TABLE daily_plans (
  id TEXT PRIMARY KEY,
  local_date TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('normal', 'reentry', 'keep_going')),
  parent_plan_id TEXT REFERENCES daily_plans(id),
  minutes_budget REAL NOT NULL CHECK (minutes_budget >= 0),
  -- The learner's ordinary daily budget in force (§6.6): carried forward from
  -- the previous plan unless a chip set it; generated budgets never change it.
  remembered_minutes INTEGER NOT NULL CHECK (remembered_minutes > 0),
  minutes_source TEXT NOT NULL CHECK (minutes_source IN ('chip', 'carried', 'generated')),
  -- Lane minutes, loads, caps and one-line reasons (§6.2), plus re-plans.
  split_json TEXT NOT NULL,
  -- §6.3 admission inputs and result.
  admission_json TEXT NOT NULL,
  estimator_version TEXT NOT NULL,
  source TEXT NOT NULL,
  chooser TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open'
    CHECK (status IN ('open', 'complete', 'stopped', 'abandoned')),
  stop_reason TEXT,
  algorithm_version TEXT NOT NULL,
  config_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  completed_at TEXT
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

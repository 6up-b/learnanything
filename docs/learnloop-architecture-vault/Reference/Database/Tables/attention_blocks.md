---
title: "attention_blocks"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "8e529218954fcf26cc284a07612cf76f2f430d67"
source_commit_timestamp: "2026-10-16T10:17:46-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite attention_blocks"
  - "table attention_blocks"
schema_head: 206
table_name: "attention_blocks"
table_role: "workflow"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "096_controller_snapshots.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/096_controller_snapshots.sql"
  - "src/learnloop/daily_plan/engine.py"
  - "src/learnloop/daily_plan/estimates.py"
  - "src/learnloop/daily_plan/records.py"
  - "src/learnloop/daily_plan_upgrade.py"
  - "src/learnloop/db/stores/daily_plans.py"
  - "src/learnloop/evsi_calibration/live_report.py"
  - "src/learnloop/scheduling/controller_store.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `attention_blocks`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives attention block a stable database identity so queue and controller decisions can resume safely and explain why an activity was selected. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `session_id`, `commitment_id`, `daily_plan_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> One coherent 5-15 minute attention block (§4.1): commitment neighborhood + canonical action + subtype + budget + exit rules. A short-circuit (continuation / explicit learner choice / served administration) is logged as such.

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/096_controller_snapshots.sql`.
- **Schema touched by:** `096_controller_snapshots.sql`, `180_daily_plans.sql`, `202_router_staged_frame.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `commitment_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `action` | `TEXT` | yes | — | — | Stored value |
| `subtype` | `TEXT` | no | — | — | Stored value |
| `budget_minutes` | `REAL` | yes | — | — | Stored value |
| `neighborhood_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `exit_rules_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `short_circuit_reason` | `TEXT` | no | — | — | Stored value |
| `content_hash` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `daily_plan_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/daily_plans\|daily_plans.id]] | Stored value |
| `plan_ordinal` | `INTEGER` | no | — | — | Stored value |
| `lane` | `TEXT` | no | — | — | Stored value |
| `chosen_by` | `TEXT` | no | — | — | Stored value |
| `decision_ref` | `TEXT` | no | — | — | Stored value |
| `reading_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

Declared SQLite foreign keys:

- `daily_plan_id` → [[Reference/Database/Tables/daily_plans|`daily_plans.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_attention_blocks_plan` on `daily_plan_id`, `plan_ordinal` (unique).
- `idx_attention_blocks_session` on `session_id`, `created_at`.
- `sqlite_autoindex_attention_blocks_1` on `id` (unique).

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/daily_plan/estimates.py`
- `src/learnloop/db/stores/daily_plans.py`
- `src/learnloop/evsi_calibration/live_report.py`

### Direct SQL writers

- `src/learnloop/db/stores/daily_plans.py`
- `src/learnloop/scheduling/controller_store.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/source_service_fakes.py`
- `tests/test_daily_plan_kill_switch.py`
- `tests/test_daily_plan_owner_decisions.py`
- `tests/test_daily_plan_replay.py`
- `tests/test_forecast_receipts.py`
- `tests/test_mcp_tools.py`
- `tests/test_migrations.py`
- `tests/test_mvp014_upgrade.py`
- `tests/test_router_presentations.py`
- `tests/test_router_r1_composition.py`
- `tests/test_router_r2a_serving.py`
- `tests/test_ux_phase4_landing.py`
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
CREATE TABLE attention_blocks (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  commitment_id TEXT,
  action TEXT NOT NULL,
  subtype TEXT,
  budget_minutes REAL NOT NULL,
  neighborhood_json TEXT NOT NULL DEFAULT '{}',
  exit_rules_json TEXT NOT NULL DEFAULT '[]',
  short_circuit_reason TEXT,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
, daily_plan_id TEXT REFERENCES daily_plans(id), plan_ordinal INTEGER, lane TEXT, chosen_by TEXT, decision_ref TEXT, reading_json TEXT);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

---
title: "scheduler_slate_candidates"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite scheduler_slate_candidates"
  - "table scheduler_slate_candidates"
schema_head: 156
table_name: "scheduler_slate_candidates"
table_role: "workflow"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "010_scheduler_training_logs.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/010_scheduler_training_logs.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop_sidecar/handlers/practice.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_migration.py"
  - "src/learnloop/goals/exam_calibration.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `scheduler_slate_candidates`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Holds candidates for scheduler slate while policy selects or reviews one so queue and controller decisions can resume safely and explain why an activity was selected. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `slate_id`, `practice_item_id`, `learning_object_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/010_scheduler_training_logs.sql`.
- **Schema touched by:** `010_scheduler_training_logs.sql`, `011_training_dataset_logging.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `slate_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/scheduler_slates\|scheduler_slates.id]] | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `rank` | `INTEGER` | yes | — | — | Stored value |
| `returned_rank` | `INTEGER` | no | — | — | Stored value |
| `was_returned` | `INTEGER` | yes | `0` | — | Stored value |
| `chosen_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `selected_mode` | `TEXT` | yes | — | — | Stored value |
| `priority` | `REAL` | yes | — | — | Stored value |
| `selection_reward` | `REAL` | no | — | — | Stored value |
| `predicted_correctness` | `REAL` | no | — | — | Stored value |
| `legacy_priority` | `REAL` | no | — | — | Stored value |
| `expected_information_gain` | `REAL` | no | — | — | Stored value |
| `readiness_factor` | `REAL` | no | — | — | Stored value |
| `components_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `reward_debug_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `target_scope_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `plain_english_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `chosen_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `selection_propensity` | `REAL` | no | — | — | Stored value |
| `exploration_flag` | `INTEGER` | yes | `0` | — | Stored value |
| `selection_temperature` | `REAL` | no | — | — | Stored value |

## Relationships and access paths

Declared SQLite foreign keys:

- `slate_id` → [[Reference/Database/Tables/scheduler_slates|`scheduler_slates.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_scheduler_slate_candidates_chosen` on `chosen_attempt_id`.
- `idx_scheduler_slate_candidates_item` on `practice_item_id`, `created_at`.
- `idx_scheduler_slate_candidates_slate_rank` on `slate_id`, `rank`.
- `sqlite_autoindex_scheduler_slate_candidates_2` on `slate_id`, `practice_item_id` (unique).
- `sqlite_autoindex_scheduler_slate_candidates_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository._link_attempt_to_scheduler_candidate()`
- `Repository.active_probe_presentation_for_session()`
- `Repository.calibration_duel_pairs()`
- `Repository.candidate_propensity_rows()`
- `Repository.chosen_candidate_outcomes()`
- `Repository.find_record()`
- `Repository.record_scheduler_slate()`
- `Repository.scheduler_slate_candidates()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/goals/exam_calibration.py`
- `src/learnloop/scheduling/evaluation.py`
- `src/learnloop/scheduling/scheduler.py`
- `src/learnloop_sidecar/handlers/inspector.py`
- `src/learnloop_sidecar/handlers/practice.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_answer_calibration_duel.py`
- `tests/test_attempts.py`
- `tests/test_causal_repair_sidecar_rpcs.py`
- `tests/test_diagnostic_probe_freshness.py`
- `tests/test_migrations.py`
- `tests/test_probe_episodes.py`
- `tests/test_scheduler.py`
- `tests/test_agent_runs.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_show.py`
- `tests/test_source_ingestion.py`

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
CREATE TABLE scheduler_slate_candidates (
  id TEXT PRIMARY KEY,
  slate_id TEXT NOT NULL REFERENCES scheduler_slates(id) ON DELETE CASCADE,
  practice_item_id TEXT NOT NULL,
  learning_object_id TEXT,
  rank INTEGER NOT NULL CHECK (rank >= 1),
  returned_rank INTEGER CHECK (returned_rank IS NULL OR returned_rank >= 1),
  was_returned INTEGER NOT NULL DEFAULT 0 CHECK (was_returned IN (0, 1)),
  chosen_attempt_id TEXT,
  selected_mode TEXT NOT NULL,
  priority REAL NOT NULL,
  selection_reward REAL,
  predicted_correctness REAL,
  legacy_priority REAL,
  expected_information_gain REAL,
  readiness_factor REAL,
  components_json TEXT NOT NULL,
  reward_debug_json TEXT,
  target_scope_json TEXT,
  plain_english_json TEXT,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  chosen_at TEXT, selection_propensity REAL, exploration_flag INTEGER NOT NULL DEFAULT 0 CHECK (exploration_flag IN (0, 1)), selection_temperature REAL,
  UNIQUE (slate_id, practice_item_id)
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

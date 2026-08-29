---
title: "scheduler_slates"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite scheduler_slates"
  - "table scheduler_slates"
schema_head: 156
table_name: "scheduler_slates"
table_role: "workflow"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "010_scheduler_training_logs.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/010_scheduler_training_logs.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_migration.py"
  - "src/learnloop/diagnosis/probe_audit.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `scheduler_slates`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives scheduler slate a stable database identity so queue and controller decisions can resume safely and explain why an activity was selected. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `session_id`, `chosen_practice_item_id`, `chosen_attempt_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/010_scheduler_training_logs.sql`.
- **Schema touched by:** `010_scheduler_training_logs.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `generated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `requested_limit` | `INTEGER` | no | — | — | Stored value |
| `returned_count` | `INTEGER` | yes | `0` | — | Stored value |
| `candidate_count` | `INTEGER` | yes | `0` | — | Stored value |
| `chosen_practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `chosen_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `selection_policy` | `TEXT` | yes | — | — | Stored value |
| `session_context_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `config_snapshot_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_scheduler_slates_chosen_attempt` on `chosen_attempt_id`.
- `idx_scheduler_slates_session` on `session_id`, `generated_at`, `id`.
- `sqlite_autoindex_scheduler_slates_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository._link_attempt_to_scheduler_candidate()`
- `Repository.active_probe_presentation_for_session()`
- `Repository.all_scheduler_slates()`
- `Repository.find_record()`
- `Repository.latest_scheduler_slate_by_session()`
- `Repository.record_scheduler_slate()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/diagnosis/probe_audit.py`
- `src/learnloop/scheduling/scheduler.py`
- `src/learnloop_sidecar/handlers/inspector.py`
- `src/learnloop_sidecar/handlers/practice.py`
- `src/learnloop_sidecar/handlers/queue.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_answer_calibration_duel.py`
- `tests/test_migrations.py`
- `tests/test_agent_runs.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_attempts.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_diagnostic_probe_freshness.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_intent_planner.py`
- `tests/test_km5_sim_gates.py`
- `tests/test_probe_episodes.py`
- `tests/test_scheduler.py`
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
CREATE TABLE scheduler_slates (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  generated_at TEXT NOT NULL,
  requested_limit INTEGER,
  returned_count INTEGER NOT NULL DEFAULT 0,
  candidate_count INTEGER NOT NULL DEFAULT 0,
  chosen_practice_item_id TEXT,
  chosen_attempt_id TEXT,
  selection_policy TEXT NOT NULL,
  session_context_json TEXT NOT NULL,
  config_snapshot_json TEXT NOT NULL,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

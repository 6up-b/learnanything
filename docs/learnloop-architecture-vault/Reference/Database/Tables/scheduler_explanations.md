---
title: "scheduler_explanations"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite scheduler_explanations"
  - "table scheduler_explanations"
schema_head: 156
table_name: "scheduler_explanations"
table_role: "receipt"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/ops/debug_time.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_migration.py"
  - "src/learnloop/scheduling/scheduler.py"
  - "src/learnloop_sidecar/handlers/inspector.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/receipt"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `scheduler_explanations`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives scheduler explanation a stable database identity so queue and controller decisions can resume safely and explain why an activity was selected. It preserves the decision trail and is never cleared by derived-state rebuilds. Rows bind `session_id`, `practice_item_id`, `algorithm_version`, making the operational relationship explicit. ^table-purpose

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Receipt]].

## Persistence and lifecycle contract

- **Role:** `receipt` — Historical audit/decision receipt. It is preserved and never rebuilt.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `selected_mode` | `TEXT` | yes | — | — | Stored value |
| `priority` | `REAL` | yes | — | — | Stored value |
| `components_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `readiness_factor` | `REAL` | no | — | — | Stored value |
| `expected_information_gain` | `REAL` | no | — | — | Stored value |
| `target_scope_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `plain_english_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_scheduler_explanations_session` on `session_id`, `practice_item_id`.
- `sqlite_autoindex_scheduler_explanations_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.find_record()`
- `Repository.insert_scheduler_explanations()`
- `Repository.latest_scheduler_explanation()`
- `Repository.latest_scheduler_explanations_by_session()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/scheduling/scheduler.py`
- `src/learnloop_sidecar/handlers/inspector.py`
- `src/learnloop_sidecar/handlers/practice.py`
- `src/learnloop_sidecar/handlers/queue.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_agent_runs.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_scheduler.py`
- `tests/test_scheduler_probe_eig.py`
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
CREATE TABLE scheduler_explanations (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  practice_item_id TEXT NOT NULL,
  selected_mode TEXT NOT NULL,
  priority REAL NOT NULL,
  components_json TEXT NOT NULL,
  readiness_factor REAL,
  expected_information_gain REAL,
  target_scope_json TEXT,
  plain_english_json TEXT,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Receipt|receipt policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

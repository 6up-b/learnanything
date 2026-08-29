---
title: "session_checkpoints"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite session_checkpoints"
  - "table session_checkpoints"
schema_head: 156
table_name: "session_checkpoints"
table_role: "workflow"
functionality_status: "active"
domain_family: "scheduling"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/content/authoring/item_authoring.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_migration.py"
  - "src/learnloop_sidecar/context.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/scheduling"
---

# `session_checkpoints`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Tracks recoverable checkpoints within a learning session. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `session_id`, `current_practice_item_id`, `current_answer`, making the operational relationship explicit. ^table-purpose

It belongs to the **scheduling** navigation family. The family context lives in [[Database Catalog#Scheduling]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `session_id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `current_practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `current_answer` | `TEXT` | no | — | — | Stored value |
| `focus_block_state_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `pending_grading_proposal_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `readiness_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_session_checkpoints_1` on `session_id` (unique).

## Who calls it

### Repository access surface

- `Repository.acknowledge_practice_checkpoint()`
- `Repository.clear_session_checkpoint()`
- `Repository.deactivate_practice_item_serving()`
- `Repository.fetch_session_checkpoint()`
- `Repository.find_record()`
- `Repository.update_session_checkpoint()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/content/authoring/item_authoring.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop_sidecar/context.py`
- `src/learnloop_sidecar/handlers/inspector.py`
- `src/learnloop_sidecar/handlers/practice.py`
- `src/learnloop_sidecar/handlers/sessions.py`
- `src/learnloop_sidecar/handlers/teach_back.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_agent_runs.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_item_authoring.py`
- `tests/test_repositories.py`
- `tests/test_show.py`
- `tests/test_sidecar_contract.py`
- `tests/test_sidecar_item_authoring.py`
- `tests/test_sidecar_teach_back.py`
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
CREATE TABLE session_checkpoints (
  session_id TEXT PRIMARY KEY,
  current_practice_item_id TEXT,
  current_answer TEXT,
  focus_block_state_json TEXT,
  pending_grading_proposal_json TEXT,
  readiness_json TEXT,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Scheduling|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

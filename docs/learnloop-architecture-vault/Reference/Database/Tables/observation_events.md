---
title: "observation_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite observation_events"
  - "table observation_events"
schema_head: 157
table_name: "observation_events"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "operations"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/ops/debug_time.py"
  - "src/learnloop/attempts/observations.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_migration.py"
  - "src/learnloop_sidecar/handlers/inspector.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/operations"
---

# `observation_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Stores observations captured through registered observation templates. It supplies replay-stable input rather than a disposable cache. Rows bind `template_id`, `session_id`, `related_learning_object_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **operations** navigation family. The family context lives in [[Database Catalog#Operations]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `template_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `subject` | `TEXT` | no | — | — | Stored value |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `related_learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `related_practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `binding_mode` | `TEXT` | no | — | — | Stored value |
| `response_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `emitted_attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `template_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_observation_events_subject` on `subject`, `created_at`.
- `sqlite_autoindex_observation_events_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.find_record()`
- `Repository.insert_observation_event()`
- `Repository.observation_events()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/observations.py`
- `src/learnloop/cli/app.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop_sidecar/handlers/inspector.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_cli_observations.py`
- `tests/test_observation_templates.py`
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
CREATE TABLE observation_events (
  id TEXT PRIMARY KEY,
  template_id TEXT NOT NULL,
  subject TEXT,
  session_id TEXT,
  related_learning_object_id TEXT,
  related_practice_item_id TEXT,
  binding_mode TEXT CHECK (
    binding_mode IS NULL OR binding_mode IN ('learner_picks', 'template_fixed', 'pending', 'promoted_later')
  ),
  response_json TEXT NOT NULL,
  emitted_attempt_id TEXT,
  template_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Operations|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

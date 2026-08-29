---
title: "change_batches"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite change_batches"
  - "table change_batches"
schema_head: 156
table_name: "change_batches"
table_role: "workflow"
functionality_status: "active"
domain_family: "schema-and-change"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/curriculum/concepts.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/content/proposals/apply_protocol.py"
  - "src/learnloop/content/sources/provenance.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
  - "src/learnloop/diagnosis/causal_migration.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/schema-and-change"
---

# `change_batches`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Groups accepted content mutations into an auditable application unit. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `proposed_patch_item_id`, `reason`, `origin`, making the operational relationship explicit. ^table-purpose

It belongs to the **schema and change** navigation family. The family context lives in [[Database Catalog#Schema And Change]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`, `006_ai_provider_metadata.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `proposed_patch_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `reason` | `TEXT` | yes | — | — | Stored value |
| `origin` | `TEXT` | yes | — | — | Stored value |
| `summary` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_change_batches_proposal_item` on `proposed_patch_item_id` (unique).
- `sqlite_autoindex_change_batches_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.active_source_events_for_entity()`
- `Repository.find_record()`
- `Repository.record_applied_proposal_item()`
- `Repository.synthesis_run_introducing_entity()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/curriculum/concepts.py`
- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/content/proposals/apply_protocol.py`
- `src/learnloop/content/sources/provenance.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop_sidecar/handlers/inspector.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_patch_applier.py`
- `tests/test_proposal_persistence.py`
- `tests/test_agent_runs.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_show.py`
- `tests/test_source_ingestion.py`
- `tests/test_synthesis_runs_repo.py`

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
CREATE TABLE "change_batches" (
  id TEXT PRIMARY KEY,
  proposed_patch_item_id TEXT,
  reason TEXT NOT NULL CHECK (reason IN ('proposal_accept', 'manual_edit', 'import')),
  origin TEXT NOT NULL CHECK (origin IN ('learner', 'system', 'codex', 'ai')),
  summary TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Schema And Change|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

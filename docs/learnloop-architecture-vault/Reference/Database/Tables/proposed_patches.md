---
title: "proposed_patches"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite proposed_patches"
  - "table proposed_patches"
schema_head: 156
table_name: "proposed_patches"
table_role: "workflow"
functionality_status: "active"
domain_family: "schema-and-change"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/ops/doctor.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/content/pipeline/source_ingestion.py"
  - "src/learnloop/content/proposals/patches.py"
  - "src/learnloop/content/proposals/proposals.py"
  - "src/learnloop/content/synthesis/source_append.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/schema-and-change"
---

# `proposed_patches`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Tracks an AI- or user-originated reviewed content proposal. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `agent_run_id`, `purpose`, `summary`, making the operational relationship explicit. ^table-purpose

It belongs to the **schema and change** navigation family. The family context lives in [[Database Catalog#Schema And Change]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`, `035_proposal_dependencies.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `agent_run_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `purpose` | `TEXT` | yes | — | — | Stored value |
| `source_refs_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `summary` | `TEXT` | no | — | — | Stored value |
| `status_cache` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_proposed_patches_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository._refresh_proposal_status()`
- `Repository.find_record()`
- `Repository.persist_proposal_batch()`
- `Repository.proposal_batch()`
- `Repository.proposal_batch_for_agent_run()`
- `Repository.proposal_batches()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/content/pipeline/source_ingestion.py`
- `src/learnloop/content/proposals/patches.py`
- `src/learnloop/content/proposals/proposals.py`
- `src/learnloop/content/synthesis/source_append.py`
- `src/learnloop/content/synthesis/source_set_synthesis.py`
- `src/learnloop/curriculum/graph_edit_proposals.py`
- `src/learnloop/curriculum/subject_registry.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/diagnosis/error_taxonomy.py`
- `src/learnloop/diagnosis/missing_vocabulary.py`
- `src/learnloop/ops/doctor.py`
- `src/learnloop_sidecar/handlers/ingest.py`
- `src/learnloop_sidecar/handlers/inspector.py`
- `src/learnloop_sidecar/handlers/proposals.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`
- `tests/test_agent_runs.py`
- `tests/test_apply_write_ahead.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_cli_generate_practice.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_exam_seeding.py`
- `tests/test_graph_edit_proposals.py`
- `tests/test_missing_vocabulary_notes.py`
- `tests/test_patch_applier.py`
- `tests/test_practice_leakage.py`
- `tests/test_proposal_dependencies.py`
- `tests/test_proposal_persistence.py`
- `tests/test_reader_progression.py`
- `tests/test_repositories.py`
- `tests/test_self_attributed_misconceptions.py`
- `tests/test_show.py`
- `tests/test_sidecar_contract.py`
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
CREATE TABLE proposed_patches (
  id TEXT PRIMARY KEY,
  agent_run_id TEXT NOT NULL,
  purpose TEXT NOT NULL,
  source_refs_json TEXT,
  summary TEXT,
  status_cache TEXT NOT NULL CHECK (
    status_cache IN ('pending', 'partially_accepted', 'accepted', 'rejected', 'invalid')
  ),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Schema And Change|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

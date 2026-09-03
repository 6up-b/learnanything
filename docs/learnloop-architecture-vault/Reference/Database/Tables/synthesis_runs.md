---
title: "synthesis_runs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite synthesis_runs"
  - "table synthesis_runs"
schema_head: 157
table_name: "synthesis_runs"
table_role: "workflow"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "044_provenance_manifests_apply_intents.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/044_provenance_manifests_apply_intents.sql"
  - "src/learnloop/content/pipeline/runner.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop_sidecar/handlers/ingest.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/content/pipeline/jobs.py"
  - "src/learnloop/content/sources/provenance.py"
  - "src/learnloop/content/synthesis/source_append.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `synthesis_runs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Tracks one execution, input identity, and result for synthesis so canonical-source work can be retried without losing provenance or silently changing its input set. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `manifest_id`, `agent_run_id`, `proposal_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §8.4 Synthesis runs: mutable run status/outputs over an immutable manifest.

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/044_provenance_manifests_apply_intents.sql`.
- **Schema touched by:** `044_provenance_manifests_apply_intents.sql`, `063_synthesis_candidate_output.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `manifest_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/synthesis_manifests\|synthesis_manifests.id]] | Stored value |
| `mode` | `TEXT` | yes | — | — | Stored value |
| `agent_run_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `proposal_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `span_request_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `resolved_span_hashes_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `coverage_decisions_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `actual_usage_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `status` | `TEXT` | yes | `'created'` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `completed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `candidate_output_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

Declared SQLite foreign keys:

- `manifest_id` → [[Reference/Database/Tables/synthesis_manifests|`synthesis_manifests.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_synthesis_runs_manifest` on `manifest_id`.
- `sqlite_autoindex_synthesis_runs_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.complete_synthesis_run()`
- `Repository.finalize_stale_synthesis_runs()`
- `Repository.insert_synthesis_run()`
- `Repository.save_synthesis_candidate()`
- `Repository.synthesis_run()`
- `Repository.synthesis_run_introducing_entity()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/content/pipeline/jobs.py`
- `src/learnloop/content/pipeline/runner.py`
- `src/learnloop/content/sources/provenance.py`
- `src/learnloop/content/synthesis/source_append.py`
- `src/learnloop/content/synthesis/source_set_synthesis.py`
- `src/learnloop_sidecar/handlers/ingest.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`
- `tests/test_source_set_synthesis.py`
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
CREATE TABLE synthesis_runs (
  id TEXT PRIMARY KEY,
  manifest_id TEXT NOT NULL REFERENCES synthesis_manifests(id),
  mode TEXT NOT NULL,
  agent_run_id TEXT,
  proposal_id TEXT,
  span_request_json TEXT,
  resolved_span_hashes_json TEXT,
  coverage_decisions_json TEXT,
  actual_usage_json TEXT,
  status TEXT NOT NULL DEFAULT 'created' CHECK (
    status IN ('created', 'running', 'completed', 'failed')
  ),
  created_at TEXT NOT NULL,
  completed_at TEXT
, candidate_output_json TEXT);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

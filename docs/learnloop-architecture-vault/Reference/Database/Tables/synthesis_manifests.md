---
title: "synthesis_manifests"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite synthesis_manifests"
  - "table synthesis_manifests"
schema_head: 156
table_name: "synthesis_manifests"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "044_provenance_manifests_apply_intents.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/044_provenance_manifests_apply_intents.sql"
  - "src/learnloop/content/synthesis/source_append.py"
  - "src/learnloop/content/synthesis/source_set_synthesis.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/sources/provenance.py"
  - "src/learnloop/content/sources/source_deletion.py"
  - "src/learnloop/content/synthesis/synthesis_manifests.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `synthesis_manifests`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Pins the complete input identity for synthesis so canonical-source work can be retried without losing provenance or silently changing its input set. It supplies replay-stable input rather than a disposable cache. Rows bind `source_set_id`, `prompt_version`, `schema_version`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §8.4 Immutable synthesis manifests: the complete input manifest persisted BEFORE model execution. manifest_hash IS the agent_runs.input_context_hash cache seam. Includes the §12.4 completeness fields (curriculum/facet/task hashes, assessment schema version, learner-model contract version).

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/044_provenance_manifests_apply_intents.sql`.
- **Schema touched by:** `044_provenance_manifests_apply_intents.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `manifest_hash` | `TEXT` | yes | — | — | Stored value |
| `source_set_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `membership_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `revision_ids_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `asset_hashes_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `extraction_ids_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `unit_inventory_versions_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `scope_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `brief_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `prompt_version` | `TEXT` | no | — | — | Stored value |
| `schema_version` | `INTEGER` | no | — | — | Stored value |
| `provider` | `TEXT` | no | — | — | Stored value |
| `model` | `TEXT` | no | — | — | Stored value |
| `extractor_versions_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `curriculum_snapshot_hash` | `TEXT` | no | — | — | Stored value |
| `facet_registry_hash` | `TEXT` | no | — | — | Stored value |
| `task_graph_hash` | `TEXT` | no | — | — | Stored value |
| `assessment_schema_version` | `TEXT` | no | — | — | Stored value |
| `learner_model_contract_version` | `TEXT` | no | — | — | Stored value |
| `lock_fingerprint` | `TEXT` | no | — | — | Stored value |
| `token_budget_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `estimated_usage_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_synthesis_manifests_2` on `manifest_hash` (unique).
- `sqlite_autoindex_synthesis_manifests_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.delete_source_artifact()`
- `Repository.insert_synthesis_manifest()`
- `Repository.synthesis_manifest()`
- `Repository.synthesis_manifest_by_hash()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/sources/provenance.py`
- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/content/synthesis/source_append.py`
- `src/learnloop/content/synthesis/source_set_synthesis.py`
- `src/learnloop/content/synthesis/synthesis_manifests.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`
- `tests/test_synthesis_manifests.py`
- `tests/test_synthesis_runs_repo.py`
- `tests/test_source_append.py`
- `tests/test_source_set_synthesis.py`

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
CREATE TABLE synthesis_manifests (
  id TEXT PRIMARY KEY,
  manifest_hash TEXT NOT NULL UNIQUE,
  source_set_id TEXT,
  membership_json TEXT,
  revision_ids_json TEXT,
  asset_hashes_json TEXT,
  extraction_ids_json TEXT,
  unit_inventory_versions_json TEXT,
  scope_json TEXT,
  brief_json TEXT,
  prompt_version TEXT,
  schema_version INTEGER,
  provider TEXT,
  model TEXT,
  extractor_versions_json TEXT,
  curriculum_snapshot_hash TEXT,
  facet_registry_hash TEXT,
  task_graph_hash TEXT,
  assessment_schema_version TEXT,
  learner_model_contract_version TEXT,
  lock_fingerprint TEXT,
  token_budget_json TEXT,
  estimated_usage_json TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

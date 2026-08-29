---
title: "source_unit_inventories"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite source_unit_inventories"
  - "table source_unit_inventories"
schema_head: 156
table_name: "source_unit_inventories"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "041_source_unit_inventories.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/041_source_unit_inventories.sql"
  - "src/learnloop/content/sources/source_outline.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/authoring/practice_leakage.py"
  - "src/learnloop/content/sources/source_deletion.py"
  - "src/learnloop/content/synthesis/facet_candidates.py"
  - "src/learnloop/content/synthesis/source_coverage.py"
  - "src/learnloop/content/synthesis/source_set_synthesis.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_unit_inventories`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives source unit inventorie a stable database identity so canonical-source work can be retried without losing provenance or silently changing its input set. It supplies replay-stable input rather than a disposable cache. Rows bind `source_revision_id`, `extraction_id`, `unit_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/041_source_unit_inventories.sql`.
- **Schema touched by:** `041_source_unit_inventories.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `source_revision_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/source_revisions\|source_revisions.id]] | Stored value |
| `extraction_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/source_extraction_runs\|source_extraction_runs.id]] | Stored value |
| `unit_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `unit_semantic_hash` | `TEXT` | yes | — | — | Stored value |
| `inventory_profile` | `TEXT` | yes | — | — | Stored value |
| `inventory_schema_version` | `INTEGER` | yes | — | — | Stored value |
| `prompt_version` | `TEXT` | yes | — | — | Stored value |
| `provider` | `TEXT` | yes | — | — | Stored value |
| `model` | `TEXT` | yes | — | — | Stored value |
| `inventory_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `usage_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `extraction_id` → [[Reference/Database/Tables/source_extraction_runs|`source_extraction_runs.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `source_revision_id` → [[Reference/Database/Tables/source_revisions|`source_revisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_source_unit_inventories_extraction` on `extraction_id`.
- `idx_source_unit_inventories_semantic_hash` on `unit_semantic_hash`.
- `idx_source_unit_inventories_revision` on `source_revision_id`.
- `sqlite_autoindex_source_unit_inventories_2` on `source_revision_id`, `unit_id`, `unit_semantic_hash`, `inventory_profile`, `inventory_schema_version`, `prompt_version`, `provider`, `model` (unique).
- `sqlite_autoindex_source_unit_inventories_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.delete_source_artifact()`
- `Repository.get_unit_inventory()`
- `Repository.insert_unit_inventory()`
- `Repository.reusable_unit_inventories()`
- `Repository.source_unit_inventory_claims()`
- `Repository.unit_inventories_for_extraction()`
- `Repository.unit_inventories_for_revision()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/authoring/practice_leakage.py`
- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/content/synthesis/facet_candidates.py`
- `src/learnloop/content/synthesis/source_coverage.py`
- `src/learnloop/content/synthesis/source_set_synthesis.py`
- `src/learnloop/content/synthesis/source_unit_inventory.py`
- `src/learnloop_sidecar/handlers/ingest.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_inventory_merge_parallel.py`
- `tests/test_source_inventory.py`

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
CREATE TABLE source_unit_inventories (
  id TEXT PRIMARY KEY,
  source_revision_id TEXT NOT NULL REFERENCES source_revisions(id),
  extraction_id TEXT NOT NULL REFERENCES source_extraction_runs(id),
  unit_id TEXT NOT NULL,
  unit_semantic_hash TEXT NOT NULL,
  inventory_profile TEXT NOT NULL,        -- semantic | practice | assessment | combined (app-validated)
  inventory_schema_version INTEGER NOT NULL,
  prompt_version TEXT NOT NULL,
  provider TEXT NOT NULL,
  model TEXT NOT NULL,
  inventory_json TEXT NOT NULL,
  usage_json TEXT,                        -- per-call input/cached/output tokens (§6.2)
  created_at TEXT NOT NULL,
  UNIQUE(source_revision_id, unit_id, unit_semantic_hash, inventory_profile,
         inventory_schema_version, prompt_version, provider, model)
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

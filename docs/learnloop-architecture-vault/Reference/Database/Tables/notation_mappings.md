---
title: "notation_mappings"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite notation_mappings"
  - "table notation_mappings"
schema_head: 156
table_name: "notation_mappings"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "044_provenance_manifests_apply_intents.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/044_provenance_manifests_apply_intents.sql"
  - "src/learnloop/content/sources/provenance.py"
  - "src/learnloop/content/synthesis/ai_contracts.py"
  - "src/learnloop/content/synthesis/source_append.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/proposals/apply_protocol.py"
  - "src/learnloop/content/proposals/conflict_resolution.py"
  - "src/learnloop/content/sources/source_deletion.py"
  - "src/learnloop/content/synthesis/append_neighborhood.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `notation_mappings`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Maps external or historical identities into notation so canonical-source work can be retried without losing provenance or silently changing its input set. It supplies replay-stable input rather than a disposable cache. Rows bind `subject_id`, `entity_id`, `source_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §10.2 Notation mappings: contextual notation equivalences (append-only, review).

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
| `subject_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `entity_type` | `TEXT` | yes | — | — | Stored value |
| `entity_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `canonical_notation` | `TEXT` | yes | — | — | Stored value |
| `alternate_notation` | `TEXT` | yes | — | — | Stored value |
| `context` | `TEXT` | no | — | — | Stored value |
| `source_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `revision_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `locator` | `TEXT` | no | — | — | Stored value |
| `patch_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `status` | `TEXT` | yes | `'active'` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_notation_mappings_entity` on `entity_type`, `entity_id`.
- `sqlite_autoindex_notation_mappings_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.all_notation_mappings()`
- `Repository.delete_source_artifact()`
- `Repository.insert_notation_mapping()`
- `Repository.notation_mappings_for_entity()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/proposals/apply_protocol.py`
- `src/learnloop/content/proposals/conflict_resolution.py`
- `src/learnloop/content/sources/provenance.py`
- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/content/synthesis/append_neighborhood.py`
- `src/learnloop/content/synthesis/source_append.py`
- `src/learnloop/content/synthesis/study_map_diff.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`
- `tests/test_provenance_service.py`
- `tests/test_source_append.py`
- `tests/test_exam_readiness_and_conflict.py`
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
CREATE TABLE notation_mappings (
  id TEXT PRIMARY KEY,
  subject_id TEXT,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  canonical_notation TEXT NOT NULL,
  alternate_notation TEXT NOT NULL,
  context TEXT,
  source_id TEXT,
  revision_id TEXT,
  locator TEXT,
  patch_id TEXT,
  status TEXT NOT NULL DEFAULT 'active' CHECK (
    status IN ('active', 'superseded', 'rejected')
  ),
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

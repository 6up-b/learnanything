---
title: "source_block_fts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "247722912c7e157729b0531581dd16280d05fdf7"
source_commit_timestamp: "2026-10-25T00:32:33-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite source_block_fts"
  - "table source_block_fts"
schema_head: 220
table_name: "source_block_fts"
table_role: "derived"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "177_source_block_fts.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/177_source_block_fts.sql"
  - "src/learnloop/config/schema.py"
  - "src/learnloop/content/authoring/source_exercise_import.py"
  - "src/learnloop/content/pipeline/add_source.py"
  - "src/learnloop/content/pipeline/quick_add.py"
  - "src/learnloop/content/sources/exam_material.py"
  - "src/learnloop/content/sources/exercise_statements.py"
  - "src/learnloop/db/stores/source_block_fts.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_block_fts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Indexes source block text for FTS5 BM25 keyword search (Slice 2 T6: library search, tutor spans, Quick Add scope); triggers keep it in step with `source_document_blocks` and its one replayer rebuilds it, so it never holds anything the block ledger does not. Hazard: rows are keyed by the blocks' implicit rowid (the block table has a composite key), so a migration that rebuilds `source_document_blocks` must recreate the triggers and rerun the replayer (`learnloop rebuild-derived-state`); deletes also match the block's identity as well as its rowid (migration 177), and `learnloop doctor` reports stale or missing rows. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `extraction_id`, `span_id`, `text`, making the operational relationship explicit. ^table-purpose

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/177_source_block_fts.sql`.
- **Schema touched by:** `177_source_block_fts.sql`.
- **Rebuild owner:** `source_block_fts`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `text` | `ANY` | no | — | — | Stored value |
| `extraction_id` | `ANY` | no | — | — | Application-validated soft reference |
| `span_id` | `ANY` | no | — | — | Application-validated soft reference |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- No secondary index is declared beyond any rowid/primary-key storage.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/source_block_fts.py`

### Direct SQL writers

- `src/learnloop/db/stores/source_block_fts.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/recap_fixtures.py`
- `tests/test_architecture.py`
- `tests/test_compare_methods.py`
- `tests/test_compare_sources_keep.py`
- `tests/test_e0_review_round4.py`
- `tests/test_embedding_recipe_hash_pins.py`
- `tests/test_exam_protection_landing.py`
- `tests/test_passage_links.py`
- `tests/test_reader_inquiry_status.py`
- `tests/test_rebuild_orchestrator.py`
- `tests/test_source_block_fts.py`
- `tests/test_tutor_delivery_fixes.py`

Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.

## Extension and modification guidance

1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.
2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.
3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.
4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.
5. Update the single owner in `DERIVED_STATE_REPLAYERS`, then prove same-version rebuild equivalence and shadow isolation.

## Live schema DDL

> [!tip] Why keep the DDL here?
> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.

```sql
CREATE VIRTUAL TABLE source_block_fts USING fts5(
  text,
  extraction_id UNINDEXED,
  span_id UNINDEXED,
  tokenize = 'porter unicode61 remove_diacritics 2'
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

---
title: "entity_source_links"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite entity_source_links"
  - "table entity_source_links"
schema_head: 157
table_name: "entity_source_links"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "044_provenance_manifests_apply_intents.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/044_provenance_manifests_apply_intents.sql"
  - "src/learnloop/content/authoring/practice_generation.py"
  - "src/learnloop/content/authoring/practice_leakage.py"
  - "src/learnloop/content/proposals/apply_protocol.py"
  - "src/learnloop/content/proposals/patches.py"
  - "src/learnloop/content/sources/provenance.py"
  - "src/learnloop/content/sources/source_deletion.py"
  - "src/learnloop/content/sources/source_outcome_analytics.py"
  - "src/learnloop/content/synthesis/ai_contracts.py"
  - "src/learnloop/content/pipeline/revision_refresh.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `entity_source_links`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves explicit relationship edges for entity source so canonical-source work can be retried without losing provenance or silently changing its input set. It supplies replay-stable input rather than a disposable cache. Rows bind `entity_id`, `source_id`, `revision_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> ING M5 (source-ingestion §8.4, §9.1, §10.2): the provenance, manifest, and crash-safe apply foundation that must exist before an LLM builds curriculum at scale. Schemas follow the spec verbatim with house NOT NULL / DEFAULT / CHECK added; the spec's `status CHECK(a|b)` shorthand is written as `IN (...)`.  Migration numbers 041-043 are reserved for the parallel ING M4 worktree; M5 owns 044+. §9.1 Entity-source links: authoritative aggregate multi-source provenance. YAML provenance.source_refs remains a compatible embedded snapshot. Rows are written by apply_accepted_items for created content and by accepted provenance_link items during append (M7). source_id/revision_id/extraction_id are identifiers, not FKs (a cited revision may be legacy or externally mirrored).

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
| `entity_type` | `TEXT` | yes | — | — | Stored value |
| `entity_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `source_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `revision_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `locator` | `TEXT` | yes | — | — | Stored value |
| `locator_scheme` | `TEXT` | no | — | — | Stored value |
| `relation` | `TEXT` | yes | — | — | Stored value |
| `extraction_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `asset_hash` | `TEXT` | no | — | — | Stored value |
| `span_hash` | `TEXT` | no | — | — | Stored value |
| `patch_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `status` | `TEXT` | yes | `'current'` | — | Stored value |
| `stale_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `superseded_by_link_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/entity_source_links\|entity_source_links.id]] | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `superseded_by_link_id` → [[Reference/Database/Tables/entity_source_links|`entity_source_links.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_entity_source_links_status` on `status`.
- `idx_entity_source_links_revision` on `revision_id`.
- `idx_entity_source_links_entity` on `entity_type`, `entity_id`.
- `sqlite_autoindex_entity_source_links_2` on `entity_type`, `entity_id`, `revision_id`, `locator`, `relation` (unique).
- `sqlite_autoindex_entity_source_links_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.delete_source_artifact()`
- `Repository.entity_source_links()`
- `Repository.entity_source_links_for_revision()`
- `Repository.entity_source_links_for_sources()`
- `Repository.insert_entity_source_link()`
- `Repository.mark_entity_source_link_status()`
- `Repository.stale_entity_source_links()`

### Direct SQL readers

- `src/learnloop/content/synthesis/source_append.py`
- `src/learnloop/content/synthesis/study_map_diff.py`
- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/authoring/practice_leakage.py`
- `src/learnloop/content/pipeline/revision_refresh.py`
- `src/learnloop/content/proposals/apply_protocol.py`
- `src/learnloop/content/sources/provenance.py`
- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/content/sources/source_outcome_analytics.py`
- `src/learnloop/content/synthesis/append_neighborhood.py`
- `src/learnloop/content/synthesis/coverage_rollup.py`
- `src/learnloop/content/synthesis/source_append.py`
- `src/learnloop/content/synthesis/study_map_diff.py`
- `src/learnloop/ops/maintenance_feed.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_apply_write_ahead.py`
- `tests/test_migrations.py`
- `tests/test_source_append.py`
- `tests/test_source_set_synthesis.py`
- `tests/test_source_sets.py`
- `tests/test_tutor_citations.py`
- `tests/test_coldness_receipt.py`
- `tests/test_provenance_service.py`
- `tests/test_revision_refresh.py`
- `tests/test_source_deletion.py`

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
CREATE TABLE entity_source_links (
  id TEXT PRIMARY KEY,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  source_id TEXT,
  revision_id TEXT,
  locator TEXT NOT NULL,
  locator_scheme TEXT,
  relation TEXT NOT NULL CHECK (
    relation IN ('primary', 'support', 'alternate', 'exercise', 'assessment_alignment')
  ),
  extraction_id TEXT,
  asset_hash TEXT,
  span_hash TEXT,
  patch_id TEXT,
  status TEXT NOT NULL DEFAULT 'current' CHECK (
    status IN ('current', 'stale', 'removed', 'needs_reanchor')
  ),
  stale_at TEXT,
  superseded_by_link_id TEXT REFERENCES entity_source_links(id),
  created_at TEXT NOT NULL,
  UNIQUE (entity_type, entity_id, revision_id, locator, relation)
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

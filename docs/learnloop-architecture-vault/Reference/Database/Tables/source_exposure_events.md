---
title: "source_exposure_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite source_exposure_events"
  - "table source_exposure_events"
schema_head: 156
table_name: "source_exposure_events"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "049_source_exposure_events.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/049_source_exposure_events.sql"
  - "src/learnloop/attempts/coldness_receipt.py"
  - "src/learnloop/content/sources/source_outcome_analytics.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/sources/source_deletion.py"
  - "src/learnloop/diagnosis/remediation.py"
  - "src/learnloop/reader/span_view.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_exposure_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of source exposure so canonical-source work can be retried without losing provenance or silently changing its input set. It supplies replay-stable input rather than a disposable cache. Rows bind `extraction_id`, `span_id`, `revision_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Source-exposure telemetry (spec_source_ingestion_v2 §9.2, §14): EVERY Open-in-source view records that the learner was shown a specific source span. This is read/exposure telemetry, distinct from content_events (which records curriculum mutations). One row per view. `context` says which surface opened the span (provenance panel, gate diagnostic, registry review); `entity_type`/ `entity_id` name the curriculum entity whose provenance was being inspected (nullable — a span can be opened without an entity anchor).

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/049_source_exposure_events.sql`.
- **Schema touched by:** `049_source_exposure_events.sql`, `050_capability_residual_and_identifiability.sql`, `052_source_exposure_contexts.sql`, `058_remediation_episodes.sql`, `092_source_exposure_reader_contexts.sql`, `097_source_exposure_index_backfill.sql`, `150_remediation_delivery_exposure.sql`, `151_cold_measurement_opportunities.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `context` | `TEXT` | yes | — | — | Stored value |
| `extraction_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `span_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `revision_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `source_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `entity_type` | `TEXT` | no | — | — | Stored value |
| `entity_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `page` | `INTEGER` | no | — | — | Stored value |
| `locator` | `TEXT` | no | — | — | Stored value |
| `section_path_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_source_exposure_events_created` on `created_at`, `id`.
- `idx_source_exposure_events_entity` on `entity_type`, `entity_id`.
- `idx_source_exposure_events_span` on `extraction_id`, `span_id`.
- `sqlite_autoindex_source_exposure_events_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.delete_source_artifact()`
- `Repository.insert_source_exposure_event()`
- `Repository.source_exposure_events()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/coldness_receipt.py`
- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/content/sources/source_outcome_analytics.py`
- `src/learnloop/diagnosis/remediation.py`
- `src/learnloop/reader/span_view.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_coldness_receipt.py`
- `tests/test_migrations.py`
- `tests/test_reader_restoration.py`
- `tests/test_sidecar_span_view.py`
- `tests/test_source_outcome_analytics.py`
- `tests/test_span_view.py`

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
CREATE TABLE "source_exposure_events" (
  id TEXT PRIMARY KEY,
  context TEXT NOT NULL
    CHECK (context IN (
      'provenance', 'gate_diagnostic', 'registry_review', 'library', 'other',
      'tutor_citation', 'provenance_panel', 'conflict_review', 'remediation',
      'reader', 'reader_restoration',
      -- Coldness receipts v2: prescribed passage text delivered for render.
      'remediation_delivery'
    )),
  extraction_id TEXT NOT NULL,
  span_id TEXT NOT NULL,
  revision_id TEXT,
  source_id TEXT,
  entity_type TEXT,
  entity_id TEXT,
  page INTEGER,
  locator TEXT,
  section_path_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

---
title: "content_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite content_events"
  - "table content_events"
schema_head: 157
table_name: "content_events"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "schema-and-change"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/attempts/regrade.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/content/proposals/apply_protocol.py"
  - "src/learnloop/curriculum/concepts.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/pipeline/revision_refresh.py"
  - "src/learnloop/content/pipeline/source_ingestion.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/schema-and-change"
---

# `content_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Records accepted content lifecycle changes independently from the mutable YAML files. It supplies replay-stable input rather than a disposable cache. Rows bind `change_batch_id`, `entity_id`, `event_type`, making the operational relationship explicit. ^table-purpose

It belongs to the **schema and change** navigation family. The family context lives in [[Database Catalog#Schema And Change]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`, `002_source_span_events.sql`, `006_ai_provider_metadata.sql`, `036_content_events_entity_types.sql`, `049_source_exposure_events.sql`, `065_activity_lineage_substrate.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `change_batch_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `event_type` | `TEXT` | yes | — | — | Stored value |
| `subject` | `TEXT` | no | — | — | Stored value |
| `entity_type` | `TEXT` | yes | — | — | Stored value |
| `entity_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `origin` | `TEXT` | yes | — | — | Stored value |
| `review_status` | `TEXT` | no | — | — | Stored value |
| `summary` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_content_events_recent` on `created_at`, `event_type`.
- `sqlite_autoindex_content_events_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.active_source_events_for_entity()`
- `Repository.content_events_for_entity()`
- `Repository.find_record()`
- `Repository.record_applied_proposal_item()`
- `Repository.record_content_events()`
- `Repository.record_deferred_regrade()`
- `Repository.reject_applied_proposal_item()`
- `Repository.synthesis_run_introducing_entity()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/curriculum/concepts.py`
- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/regrade.py`
- `src/learnloop/cli/app.py`
- `src/learnloop/content/pipeline/revision_refresh.py`
- `src/learnloop/content/pipeline/source_ingestion.py`
- `src/learnloop/content/proposals/apply_protocol.py`
- `src/learnloop/content/proposals/patches.py`
- `src/learnloop/content/sources/provenance.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop_sidecar/handlers/inspector.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_deferred_regrade.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_patch_applier.py`
- `tests/test_agent_runs.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_characterization_probe_regrade.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_concepts.py`
- `tests/test_proposal_persistence.py`
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
CREATE TABLE "content_events" (
  id TEXT PRIMARY KEY,
  change_batch_id TEXT,
  event_type TEXT NOT NULL CHECK (
    event_type IN (
      'created',
      'updated',
      'deactivated',
      'regrade_disagreement',
      'algorithm_version_bumped',
      'source_span_changed',
      'source_span_removed'
    )
  ),
  subject TEXT,
  entity_type TEXT NOT NULL CHECK (
    entity_type IN (
      'learning_object', 'practice_item', 'concept', 'concept_edge', 'rubric', 'error_type',
      'facet', 'task_blueprint', 'provenance_link', 'notation_mapping', 'source_conflict'
    )
  ),
  entity_id TEXT NOT NULL,
  origin TEXT NOT NULL CHECK (origin IN ('learner', 'system', 'codex', 'ai', 'import')),
  review_status TEXT CHECK (
    review_status IS NULL OR review_status IN ('auto_accepted', 'accepted', 'rejected')
  ),
  summary TEXT,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Schema And Change|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

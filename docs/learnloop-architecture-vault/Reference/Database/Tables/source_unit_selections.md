---
title: "source_unit_selections"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite source_unit_selections"
  - "table source_unit_selections"
schema_head: 156
table_name: "source_unit_selections"
table_role: "workflow"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "040_source_unit_selections.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/040_source_unit_selections.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/content/authoring/practice_leakage.py"
  - "src/learnloop/content/pipeline/jobs.py"
  - "src/learnloop/content/sources/source_deletion.py"
  - "src/learnloop/content/synthesis/source_coverage.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_unit_selections`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives source unit selection a stable database identity so canonical-source work can be retried without losing provenance or silently changing its input set. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `extraction_id`, `source_id`, `revision_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Unit selection persistence for ING M3 (spec_source_ingestion_v2 §5.3).  Per (artifact, revision, extraction) the learner's chosen units plus optional boundary overrides (merge-with-next / split-at-heading) layered over the ExtractionRun. Selections survive re-extraction by deterministic re-anchoring (services/source_unit_selection.py): anything unresolved lands in needs_review_json for review and is never silently dropped.  KM2 reserves migrations 037-039; ING M3 owns 040.

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/040_source_unit_selections.sql`.
- **Schema touched by:** `040_source_unit_selections.sql`, `041_source_unit_inventories.sql`, `061_unit_selection_role_override.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `extraction_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/source_extraction_runs\|source_extraction_runs.id]] | Stored value |
| `source_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/source_artifacts\|source_artifacts.id]] | Stored value |
| `revision_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/source_revisions\|source_revisions.id]] | Stored value |
| `selected_unit_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `boundary_overrides_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `needs_review_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `exam_use_modes_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `exam_paper_metadata_json` | `TEXT` | yes | `'{}'` | — | JSON-encoded structured payload |
| `role_override` | `TEXT` | no | — | — | Stored value |

## Relationships and access paths

Declared SQLite foreign keys:

- `revision_id` → [[Reference/Database/Tables/source_revisions|`source_revisions.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `source_id` → [[Reference/Database/Tables/source_artifacts|`source_artifacts.id`]]; on delete `NO ACTION`, on update `NO ACTION`.
- `extraction_id` → [[Reference/Database/Tables/source_extraction_runs|`source_extraction_runs.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_source_unit_selections_source` on `source_id`.
- `idx_source_unit_selections_revision` on `revision_id`.
- `sqlite_autoindex_source_unit_selections_1` on `extraction_id` (unique).

## Who calls it

### Repository access surface

- `Repository.delete_source_artifact()`
- `Repository.get_unit_selection()`
- `Repository.unit_selections_for_revision()`
- `Repository.upsert_unit_selection()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/content/authoring/practice_leakage.py`
- `src/learnloop/content/pipeline/jobs.py`
- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/content/synthesis/source_coverage.py`
- `src/learnloop/content/synthesis/source_set_synthesis.py`
- `src/learnloop/content/synthesis/source_unit_inventory.py`
- `src/learnloop/content/synthesis/source_unit_selection.py`
- `src/learnloop_sidecar/handlers/ingest.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`
- `tests/test_ingest_m3.py`

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
CREATE TABLE source_unit_selections (
  extraction_id TEXT PRIMARY KEY REFERENCES source_extraction_runs(id),
  source_id TEXT REFERENCES source_artifacts(id),
  revision_id TEXT REFERENCES source_revisions(id),
  selected_unit_ids_json TEXT NOT NULL DEFAULT '[]',
  boundary_overrides_json TEXT NOT NULL DEFAULT '[]',
  needs_review_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
, exam_use_modes_json TEXT NOT NULL DEFAULT '{}', exam_paper_metadata_json TEXT NOT NULL DEFAULT '{}', role_override TEXT);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

---
title: "source_conflicts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite source_conflicts"
  - "table source_conflicts"
schema_head: 157
table_name: "source_conflicts"
table_role: "workflow"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "044_provenance_manifests_apply_intents.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/044_provenance_manifests_apply_intents.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop_sidecar/handlers/app.py"
  - "src/learnloop/content/proposals/apply_protocol.py"
  - "src/learnloop/content/proposals/conflict_resolution.py"
  - "src/learnloop/content/sources/provenance.py"
  - "src/learnloop/content/synthesis/append_neighborhood.py"
  - "src/learnloop/content/synthesis/source_append.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `source_conflicts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives source conflict a stable database identity so canonical-source work can be retried without losing provenance or silently changing its input set. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `subject_id`, `entity_id`, `left_source_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> §10.2 Source conflicts: an unresolved two-sided conflict. Accepting persists an open conflict; it never applies either competing definition.

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/044_provenance_manifests_apply_intents.sql`.
- **Schema touched by:** `044_provenance_manifests_apply_intents.sql`, `051_maintenance_feed.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `subject_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `entity_type` | `TEXT` | yes | — | — | Stored value |
| `entity_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `left_source_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `left_revision_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `left_locator` | `TEXT` | no | — | — | Stored value |
| `right_source_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `right_revision_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `right_locator` | `TEXT` | no | — | — | Stored value |
| `statement` | `TEXT` | yes | — | — | Stored value |
| `status` | `TEXT` | yes | `'open'` | — | Stored value |
| `resolution_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `patch_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `resolved_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_source_conflicts_status` on `status`.
- `idx_source_conflicts_entity` on `entity_type`, `entity_id`.
- `sqlite_autoindex_source_conflicts_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.insert_source_conflict()`
- `Repository.resolve_source_conflict()`
- `Repository.source_conflict()`
- `Repository.source_conflicts_by_status()`
- `Repository.source_conflicts_for_entity()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`
- `src/learnloop_sidecar/handlers/app.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/proposals/apply_protocol.py`
- `src/learnloop/content/proposals/conflict_resolution.py`
- `src/learnloop/content/sources/provenance.py`
- `src/learnloop/content/synthesis/append_neighborhood.py`
- `src/learnloop/content/synthesis/source_append.py`
- `src/learnloop/content/synthesis/study_map_diff.py`
- `src/learnloop/ops/maintenance_feed.py`
- `src/learnloop_sidecar/handlers/ingest.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`
- `tests/test_exam_readiness_and_conflict.py`
- `tests/test_maintenance_feed.py`
- `tests/test_provenance_service.py`
- `tests/test_sidecar_append.py`
- `tests/test_source_append.py`
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
CREATE TABLE source_conflicts (
  id TEXT PRIMARY KEY,
  subject_id TEXT,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  left_source_id TEXT,
  left_revision_id TEXT,
  left_locator TEXT,
  right_source_id TEXT,
  right_revision_id TEXT,
  right_locator TEXT,
  statement TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open' CHECK (
    status IN ('open', 'resolved', 'dismissed')
  ),
  resolution_json TEXT,
  patch_id TEXT,
  created_at TEXT NOT NULL,
  resolved_at TEXT
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

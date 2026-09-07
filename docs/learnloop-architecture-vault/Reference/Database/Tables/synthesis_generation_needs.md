---
title: "synthesis_generation_needs"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite synthesis_generation_needs"
  - "table synthesis_generation_needs"
schema_head: 157
table_name: "synthesis_generation_needs"
table_role: "workflow"
functionality_status: "active"
domain_family: "sources-and-ingest"
introduced_in: "045_synthesis_generation_needs.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/045_synthesis_generation_needs.sql"
  - "src/learnloop/curriculum/graph_edit_proposals.py"
  - "src/learnloop/curriculum/subject_registry.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/diagnostic_surface_supply.py"
  - "src/learnloop/content/synthesis/source_set_synthesis.py"
  - "src/learnloop/learner/identifiability.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/sources-and-ingest"
---

# `synthesis_generation_needs`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Queues an identified supply gap for synthesis generation so canonical-source work can be retried without losing provenance or silently changing its input set. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `subject_id`, `source_set_id`, `synthesis_run_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **sources and ingest** navigation family. The family context lives in [[Database Catalog#Sources And Ingest]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/045_synthesis_generation_needs.sql`.
- **Schema touched by:** `045_synthesis_generation_needs.sql`, `147_diagnostic_surface_generation_needs.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `subject_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `source_set_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `synthesis_run_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `need_kind` | `TEXT` | yes | — | — | Stored value |
| `target_key` | `TEXT` | yes | — | — | Stored value |
| `missing_capability` | `TEXT` | yes | — | — | Stored value |
| `facet_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `detail` | `TEXT` | no | — | — | Stored value |
| `status` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `resolved_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_synthesis_generation_needs_subject` on `subject_id`, `status`.
- `sqlite_autoindex_synthesis_generation_needs_2` on `subject_id`, `need_kind`, `target_key` (unique).
- `sqlite_autoindex_synthesis_generation_needs_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.resolve_synthesis_generation_need()`
- `Repository.synthesis_generation_needs()`
- `Repository.upsert_synthesis_generation_need()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/synthesis/source_set_synthesis.py`
- `src/learnloop/curriculum/graph_edit_proposals.py`
- `src/learnloop/curriculum/subject_registry.py`
- `src/learnloop/learner/identifiability.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_identifiability_doctor.py`
- `tests/test_measurement_rank.py`
- `tests/test_subject_registry.py`
- `tests/test_synthesis_identifiability.py`

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
CREATE TABLE synthesis_generation_needs (
  id TEXT PRIMARY KEY,
  subject_id TEXT NOT NULL,
  source_set_id TEXT,
  synthesis_run_id TEXT,
  need_kind TEXT NOT NULL,           -- generate_discriminator | coarsen_distinction
  target_key TEXT NOT NULL,          -- discriminating signature / confusable facet pair
  missing_capability TEXT NOT NULL,  -- capability the discriminator must observe
  facet_ids_json TEXT NOT NULL DEFAULT '[]',
  detail TEXT,
  status TEXT NOT NULL CHECK (status IN ('pending', 'resolved', 'declined')),
  created_at TEXT NOT NULL,
  resolved_at TEXT,
  UNIQUE (subject_id, need_kind, target_key)
);
```

## Related notes

- [[Database Catalog#Sources And Ingest|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

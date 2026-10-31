---
title: "reader_path_depths"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "4267e5ab7ca7767b6b9189c144cd9294163536e7"
source_commit_timestamp: "2026-10-31T14:03:09-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite reader_path_depths"
  - "table reader_path_depths"
schema_head: 226
table_name: "reader_path_depths"
table_role: "workflow"
functionality_status: "active"
domain_family: "reader"
introduced_in: "217_reader_reading_paths.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/217_reader_reading_paths.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/db/stores/reading_paths.py"
  - "src/learnloop/reader/reader_report.py"
  - "src/learnloop/source_retrieval/reading_paths.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/reader"
---

# `reader_path_depths`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives reader path depth a stable database identity so reader interactions remain anchored to durable source content as extraction and rendering evolve. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `source_id`, `depth`, making the operational relationship explicit. ^table-purpose

It belongs to the **reader** navigation family. The family context lives in [[Database Catalog#Reader]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/217_reader_reading_paths.sql`.
- **Schema touched by:** `217_reader_reading_paths.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `source_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `depth` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_reader_path_depths_source` on `source_id`, `created_at`.
- `sqlite_autoindex_reader_path_depths_1` on `id` (unique).

Database triggers:

- `reader_path_depths_no_delete` — schema-enforced lifecycle or immutability constraint.
- `reader_path_depths_no_update` — schema-enforced lifecycle or immutability constraint.

## Who calls it

### Repository access surface

None found by exact static reference scan.

### Direct SQL readers

- `src/learnloop/db/stores/reading_paths.py`
- `src/learnloop/reader/reader_report.py`

### Direct SQL writers

- `src/learnloop/db/stores/reading_paths.py`

### Upstream callers of the repository access surface

None found by exact static reference scan.

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_architecture.py`
- `tests/test_reader_rw7a_migration.py`
- `tests/test_reading_paths.py`

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
CREATE TABLE reader_path_depths (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL,
  depth TEXT NOT NULL CHECK (depth IN ('get_the_idea', 'learn_to_use_it', 'fluency')),
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Reader|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

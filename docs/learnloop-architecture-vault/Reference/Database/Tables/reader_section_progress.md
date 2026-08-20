---
title: "reader_section_progress"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite reader_section_progress"
  - "table reader_section_progress"
schema_head: 156
table_name: "reader_section_progress"
table_role: "workflow"
functionality_status: "active"
domain_family: "reader"
introduced_in: "106_reader_section_progress.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/106_reader_section_progress.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/reader/reader_progression.py"
  - "src/learnloop/content/sources/source_deletion.py"
  - "src/learnloop_sidecar/handlers/reader.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/reader"
---

# `reader_section_progress`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives reader section progress a stable database identity so reader interactions remain anchored to durable source content as extraction and rendering evolve. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `extraction_id`, `section_id`, `generation_batch_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Durable per-section reading progress (reader-first seeding). Previously section reveal/completion lived only in React state and reset per source. generation_batch_id is the idempotence stamp for the section-completion practice-expansion trigger: NULL = not yet triggered; 'none_needed' = mapped to zero targets; else the enqueued batch id.

It belongs to the **reader** navigation family. The family context lives in [[Database Catalog#Reader]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/106_reader_section_progress.sql`.
- **Schema touched by:** `106_reader_section_progress.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `extraction_id` | `TEXT` | yes | — | PRIMARY KEY | Stored value |
| `section_id` | `TEXT` | yes | — | PRIMARY KEY | Stored value |
| `spans_seen` | `INTEGER` | yes | `0` | — | Stored value |
| `span_count` | `INTEGER` | yes | `0` | — | Stored value |
| `revealed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `completed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `generation_batch_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `sqlite_autoindex_reader_section_progress_1` on `extraction_id`, `section_id` (unique).

## Who calls it

### Repository access surface

- `Repository.delete_source_artifact()`
- `Repository.mark_section_generation()`
- `Repository.reader_section_progress_for()`
- `Repository.set_section_generation_batch()`
- `Repository.upsert_reader_section_progress()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop_sidecar/handlers/reader.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

No table-specific test contains the table name or a detected repository method call. The schema/role invariants are still pinned by `tests/test_migrations.py` and `tests/test_table_roles.py`.

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
CREATE TABLE reader_section_progress (
  extraction_id TEXT NOT NULL,
  section_id TEXT NOT NULL,
  spans_seen INTEGER NOT NULL DEFAULT 0,
  span_count INTEGER NOT NULL DEFAULT 0,
  revealed_at TEXT,
  completed_at TEXT,
  generation_batch_id TEXT,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (extraction_id, section_id)
);
```

## Related notes

- [[Database Catalog#Reader|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

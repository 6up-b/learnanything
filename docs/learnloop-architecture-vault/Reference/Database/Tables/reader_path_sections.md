---
title: "reader_path_sections"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "d7dfe17e8b1b56f0ac2ad5096b135933344bf8af"
source_commit_timestamp: "2026-10-25T13:01:37-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite reader_path_sections"
  - "table reader_path_sections"
schema_head: 220
table_name: "reader_path_sections"
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
  - "src/learnloop_sidecar/handlers/reading_paths.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/reader"
---

# `reader_path_sections`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives reader path section a stable database identity so reader interactions remain anchored to durable source content as extraction and rendering evolve. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `extraction_id`, `section_id`, `exercise_span_id`, making the operational relationship explicit. ^table-purpose

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
| `extraction_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `depth` | `TEXT` | yes | — | — | Stored value |
| `section_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `label` | `TEXT` | yes | — | — | Stored value |
| `reason` | `TEXT` | yes | — | — | Stored value |
| `exercise_span_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `learner_override` | `TEXT` | no | — | — | Stored value |
| `ledger_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/judgment_ledger\|judgment_ledger.id]] | Stored value |
| `state_key` | `TEXT` | yes | — | — | Stored value |
| `model` | `TEXT` | yes | — | — | Stored value |
| `prompt_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `ledger_id` → [[Reference/Database/Tables/judgment_ledger|`judgment_ledger.id`]]; on delete `NO ACTION`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_reader_path_sections_reading` on `extraction_id`, `depth`, `created_at`.
- `idx_reader_path_sections_judged` on `extraction_id`, `depth`, `state_key`, `section_id` (unique).
- `sqlite_autoindex_reader_path_sections_1` on `id` (unique).

Database triggers:

- `reader_path_sections_no_delete` — schema-enforced lifecycle or immutability constraint.
- `reader_path_sections_no_update` — schema-enforced lifecycle or immutability constraint.

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
CREATE TABLE reader_path_sections (
  id TEXT PRIMARY KEY,
  extraction_id TEXT NOT NULL,
  depth TEXT NOT NULL CHECK (depth IN ('get_the_idea', 'learn_to_use_it', 'fluency')),
  section_id TEXT NOT NULL,
  label TEXT NOT NULL CHECK (label IN ('core', 'prerequisite', 'enrichment', 'already_shown', 'assumed')),
  reason TEXT NOT NULL,
  exercise_span_id TEXT,
  learner_override TEXT CHECK (learner_override IS NULL OR learner_override IN ('read_anyway', 'skip', 'none')),
  ledger_id TEXT NOT NULL REFERENCES judgment_ledger(id),
  state_key TEXT NOT NULL,
  model TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Reader|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

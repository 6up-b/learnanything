---
title: "reader_topic_question_work"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite reader_topic_question_work"
  - "table reader_topic_question_work"
table_name: "reader_topic_question_work"
table_role: "workflow"
functionality_status: "active"
domain_family: "reader"
introduced_in: "257_reader_topic_question_work.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/257_reader_topic_question_work.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/content/pipeline/jobs.py"
  - "src/learnloop/daily_plan/next_practice.py"
  - "src/learnloop/db/stores/reader.py"
  - "src/learnloop/reader/part_read.py"
  - "src/learnloop/reader/reader_progression.py"
  - "src/learnloop/content/pipeline/add_source.py"
  - "src/learnloop/reader/section_generation.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/reader"
---

# `reader_topic_question_work`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives reader topic question work a stable database identity so reader interactions remain anchored to durable source content as extraction and rendering evolve. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `learning_object_id`, `source_id`, `extraction_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **reader** navigation family. The family context lives in [[Database Catalog#Reader]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/257_reader_topic_question_work.sql`.
- **Schema touched by:** `257_reader_topic_question_work.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `purpose` | `TEXT` | yes | — | — | Stored value |
| `owner` | `TEXT` | yes | — | — | Stored value |
| `source_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `extraction_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `section_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `trigger_event` | `TEXT` | no | — | — | Stored value |
| `passage_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `source_refs_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `requested_count` | `INTEGER` | no | — | — | Stored value |
| `model_settings_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `work_key` | `TEXT` | no | — | — | Stored value |
| `batch_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `job_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `proposal_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `state` | `TEXT` | yes | — | — | Stored value |
| `error` | `TEXT` | no | — | — | Stored value |
| `claimed_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_reader_topic_question_work_batch` on `batch_id`.
- `idx_reader_topic_question_work_source` on `source_id`.
- `idx_reader_topic_question_work_section` on `extraction_id`, `section_id`.
- `sqlite_autoindex_reader_topic_question_work_2` on `learning_object_id`, `purpose` (unique).
- `sqlite_autoindex_reader_topic_question_work_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.index_section_job_topics()`
- `Repository.insert_topic_question_work()`
- `Repository.topic_question_work_for()`
- `Repository.topic_question_work_rows()`
- `Repository.update_topic_question_work()`

### Direct SQL readers

- `src/learnloop/daily_plan/next_practice.py`
- `src/learnloop/db/stores/reader.py`

### Direct SQL writers

- `src/learnloop/db/stores/reader.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/pipeline/add_source.py`
- `src/learnloop/content/pipeline/jobs.py`
- `src/learnloop/reader/part_read.py`
- `src/learnloop/reader/section_generation.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/part_read_helpers.py`
- `tests/reader_topic_question_work_migration_helpers.py`
- `tests/section_question_parts_helpers.py`
- `tests/test_reader_topic_question_work_migration.py`
- `tests/test_section_done_before_build.py`
- `tests/next_practice_helpers.py`
- `tests/test_empty_first_build.py`
- `tests/test_mobile_v4_reader.py`

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
CREATE TABLE reader_topic_question_work (
  id TEXT PRIMARY KEY,
  learning_object_id TEXT NOT NULL,
  purpose TEXT NOT NULL CHECK (purpose IN ('reader_first_set')),
  owner TEXT NOT NULL CHECK (owner IN ('topic', 'section_job')),
  source_id TEXT,
  extraction_id TEXT,
  section_id TEXT,
  trigger_event TEXT CHECK (trigger_event IS NULL OR trigger_event IN ('section_finished', 'part_read')),
  passage_ids_json TEXT NOT NULL DEFAULT '[]',
  source_refs_json TEXT NOT NULL DEFAULT '[]',
  requested_count INTEGER,
  model_settings_json TEXT,
  work_key TEXT,
  batch_id TEXT,
  job_id TEXT,
  proposal_ids_json TEXT NOT NULL DEFAULT '[]',
  state TEXT NOT NULL CHECK (state IN ('queued', 'running', 'written', 'held', 'failed', 'not_needed', 'legacy')),
  error TEXT,
  claimed_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (learning_object_id, purpose),
  CHECK ((owner = 'section_job') = (state = 'legacy')),
  CHECK (owner = 'section_job' OR (trigger_event IS NOT NULL AND work_key IS NOT NULL AND batch_id IS NOT NULL))
);
```

## Related notes

- [[Database Catalog#Reader|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

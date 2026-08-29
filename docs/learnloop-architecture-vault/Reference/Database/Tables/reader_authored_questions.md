---
title: "reader_authored_questions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite reader_authored_questions"
  - "table reader_authored_questions"
schema_head: 156
table_name: "reader_authored_questions"
table_role: "workflow"
functionality_status: "active"
domain_family: "reader"
introduced_in: "105_reader_authored_questions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/105_reader_authored_questions.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/reader/reader_guidance.py"
  - "src/learnloop/reader/reader_quick_check.py"
  - "src/learnloop/content/pipeline/jobs.py"
  - "src/learnloop/content/sources/source_deletion.py"
  - "src/learnloop_sidecar/handlers/reader.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/reader"
---

# `reader_authored_questions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives reader authored question a stable database identity so reader interactions remain anchored to durable source content as extraction and rendering evolve. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `extraction_id`, `section_id`, `source_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Reader quick-check producer: AI-authored section-boundary questions. One row per authored question. The row is the record: statuses live here (proposed -> answered | dismissed | escalated), never on new interaction-event kinds, and answering never touches attempts/mastery.

It belongs to the **reader** navigation family. The family context lives in [[Database Catalog#Reader]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/105_reader_authored_questions.sql`.
- **Schema touched by:** `105_reader_authored_questions.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `extraction_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `section_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `source_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `question_md` | `TEXT` | yes | — | — | Stored value |
| `expected_answer_md` | `TEXT` | yes | — | — | Stored value |
| `span_ids_json` | `TEXT` | yes | `'[]'` | — | JSON-encoded structured payload |
| `prompt_version` | `TEXT` | yes | — | — | Stored value |
| `provider` | `TEXT` | no | — | — | Stored value |
| `model` | `TEXT` | no | — | — | Stored value |
| `status` | `TEXT` | yes | `'proposed'` | — | Stored value |
| `response_md` | `TEXT` | no | — | — | Stored value |
| `answered_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_reader_authored_questions_section` on `extraction_id`, `section_id`, `status`.
- `sqlite_autoindex_reader_authored_questions_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.delete_source_artifact()`
- `Repository.get_reader_authored_question()`
- `Repository.insert_reader_authored_question()`
- `Repository.latest_reader_authored_question()`
- `Repository.reader_authored_questions_for_extraction()`
- `Repository.transition_reader_authored_question()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/pipeline/jobs.py`
- `src/learnloop/content/sources/source_deletion.py`
- `src/learnloop/reader/reader_guidance.py`
- `src/learnloop/reader/reader_quick_check.py`
- `src/learnloop_sidecar/handlers/reader.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_reader_quick_check.py`

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
CREATE TABLE reader_authored_questions (
  id TEXT PRIMARY KEY,
  extraction_id TEXT NOT NULL,
  section_id TEXT NOT NULL,
  source_id TEXT,
  question_md TEXT NOT NULL,
  expected_answer_md TEXT NOT NULL,
  span_ids_json TEXT NOT NULL DEFAULT '[]',
  prompt_version TEXT NOT NULL,
  provider TEXT,
  model TEXT,
  status TEXT NOT NULL DEFAULT 'proposed'
    CHECK (status IN ('proposed', 'answered', 'dismissed', 'escalated')),
  response_md TEXT,
  answered_at TEXT,
  practice_item_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Reader|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

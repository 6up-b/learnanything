---
title: "question_promotion_requests"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite question_promotion_requests"
  - "table question_promotion_requests"
schema_head: 157
table_name: "question_promotion_requests"
table_role: "workflow"
functionality_status: "active"
domain_family: "tutor-and-remediation"
introduced_in: "117_question_promotion_jobs_and_queue_revision.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/117_question_promotion_jobs_and_queue_revision.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/content/pipeline/jobs.py"
  - "src/learnloop/content/pipeline/runner.py"
  - "src/learnloop/tutor/promotions.py"
  - "src/learnloop/tutor/question_queue.py"
  - "src/learnloop_sidecar/handlers/tutor_qa.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/tutor-and-remediation"
---

# `question_promotion_requests`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Queues a durable, retryable request for question promotion so tutor and repair work can be resumed, reviewed, and connected to subsequent evidence. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `question_event_id`, `subject_id`, `learning_object_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Durable question-to-practice authoring and lightweight Today queue invalidation.  A promotion request is written before model work starts, then linked to the ingest batch that performs analysis/authoring.  This makes retries and failures visible instead of collapsing a two-turn model workflow into one synchronous RPC.

It belongs to the **tutor and remediation** navigation family. The family context lives in [[Database Catalog#Tutor And Remediation]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/117_question_promotion_jobs_and_queue_revision.sql`.
- **Schema touched by:** `117_question_promotion_jobs_and_queue_revision.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `question_event_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/question_events\|question_events.id]] | Stored value |
| `intent` | `TEXT` | yes | — | — | Stored value |
| `subject_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `status` | `TEXT` | yes | — | — | Stored value |
| `stage` | `TEXT` | yes | — | — | Stored value |
| `batch_id` | `TEXT` | no | — | FK → [[Reference/Database/Tables/ingest_batches\|ingest_batches.id]] | Stored value |
| `promotion_route` | `TEXT` | no | — | — | Stored value |
| `error_code` | `TEXT` | no | — | — | Stored value |
| `error_message` | `TEXT` | no | — | — | Stored value |
| `retryable` | `INTEGER` | yes | `0` | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `batch_id` → [[Reference/Database/Tables/ingest_batches|`ingest_batches.id`]]; on delete `SET NULL`, on update `NO ACTION`.
- `question_event_id` → [[Reference/Database/Tables/question_events|`question_events.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_question_promotion_requests_status` on `status`, `updated_at`.
- `idx_question_promotion_requests_batch` on `batch_id`.
- `sqlite_autoindex_question_promotion_requests_1` on `question_event_id` (unique).

## Who calls it

### Repository access surface

- `Repository.insert_question_promotion_request()`
- `Repository.question_promotion_request()`
- `Repository.question_promotion_requests_for_events()`
- `Repository.retry_question_promotion_request()`
- `Repository.update_question_promotion_request()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/content/pipeline/jobs.py`
- `src/learnloop/content/pipeline/runner.py`
- `src/learnloop/tutor/promotions.py`
- `src/learnloop/tutor/question_queue.py`
- `src/learnloop_sidecar/handlers/tutor_qa.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`
- `tests/test_question_promotions.py`
- `tests/test_question_promotion_jobs.py`
- `tests/test_sidecar_tutor_qa.py`
- `tests/test_tutor_promotion_service.py`

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
CREATE TABLE question_promotion_requests (
  question_event_id TEXT PRIMARY KEY REFERENCES question_events(id) ON DELETE CASCADE,
  intent TEXT NOT NULL,
  subject_id TEXT,
  learning_object_id TEXT,
  status TEXT NOT NULL,
  stage TEXT NOT NULL,
  batch_id TEXT REFERENCES ingest_batches(id) ON DELETE SET NULL,
  promotion_route TEXT,
  error_code TEXT,
  error_message TEXT,
  retryable INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## Related notes

- [[Database Catalog#Tutor And Remediation|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

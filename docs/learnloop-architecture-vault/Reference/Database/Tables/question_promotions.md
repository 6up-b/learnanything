---
title: "question_promotions"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite question_promotions"
  - "table question_promotions"
schema_head: 157
table_name: "question_promotions"
table_role: "workflow"
functionality_status: "active"
domain_family: "tutor-and-remediation"
introduced_in: "027_question_promotions.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/027_question_promotions.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/tutor/promotions.py"
  - "src/learnloop/tutor/question_queue.py"
  - "src/learnloop/tutor/question_signal.py"
  - "src/learnloop/scheduling/scheduler.py"
  - "src/learnloop_sidecar/handlers/tutor_qa.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/tutor-and-remediation"
---

# `question_promotions`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives question promotion a stable database identity so tutor and repair work can be resumed, reviewed, and connected to subsequent evidence. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `question_event_id`, `learner_claim_id`, `intervention_need_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> question_promotions: one row per promoted tutor turn. PK on the event id makes the pipeline idempotent (a second promote returns the existing row).

It belongs to the **tutor and remediation** navigation family. The family context lives in [[Database Catalog#Tutor And Remediation]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/027_question_promotions.sql`.
- **Schema touched by:** `027_question_promotions.sql`, `086_reader_dialogue.sql`, `117_question_promotion_jobs_and_queue_revision.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `question_event_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/question_events\|question_events.id]] | Stored value |
| `intent` | `TEXT` | yes | — | — | Stored value |
| `attributed_facets_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `question_nature` | `TEXT` | no | — | — | Stored value |
| `attempted_in_thread` | `INTEGER` | no | — | — | Stored value |
| `learner_claim_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `intervention_need_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `proposed_patch_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `saved_note_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `existing_practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `created_learning_object_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `route` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |

## Relationships and access paths

Declared SQLite foreign keys:

- `question_event_id` → [[Reference/Database/Tables/question_events|`question_events.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_question_promotions_existing_item` on `existing_practice_item_id`.
- `idx_question_promotions_created_item` on `created_practice_item_id`.
- `sqlite_autoindex_question_promotions_1` on `question_event_id` (unique).

## Who calls it

### Repository access surface

- `Repository.insert_question_promotion()`
- `Repository.question_promotion()`
- `Repository.question_promotions()`
- `Repository.question_promotions_for_events()`
- `Repository.question_promotions_for_patch()`
- `Repository.requested_practice_item_ids()`
- `Repository.update_question_promotion()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/scheduling/scheduler.py`
- `src/learnloop/tutor/promotions.py`
- `src/learnloop/tutor/question_queue.py`
- `src/learnloop/tutor/question_signal.py`
- `src/learnloop_sidecar/handlers/tutor_qa.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_migrations.py`
- `tests/test_question_promotions.py`
- `tests/test_sidecar_tutor_qa.py`
- `tests/test_question_promotion_jobs.py`
- `tests/test_scheduler_requested_floor.py`
- `tests/test_tutor_promotion_service.py`
- `tests/test_tutor_promotion_w2.py`

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
CREATE TABLE question_promotions (
  question_event_id TEXT PRIMARY KEY REFERENCES question_events(id) ON DELETE CASCADE,
  intent TEXT NOT NULL CHECK (intent IN ('practice', 'gap')),
  attributed_facets_json TEXT,        -- PromotionAnalysis output
  question_nature TEXT CHECK (question_nature IN
    ('core_recall','mechanism','transfer','edge_case','what_if')
    OR question_nature IS NULL),
  attempted_in_thread INTEGER,        -- PromotionAnalysis output (nullable bool)
  learner_claim_id TEXT,              -- gap route: the self_rating claim written
  intervention_need_id TEXT,          -- gap route: the filed need
  proposed_patch_id TEXT,             -- practice route (gap route's patch comes via the need)
  saved_note_id TEXT,                 -- grounding note (reused or created)
  existing_practice_item_id TEXT,     -- dedup route: promotion resolved to an existing item
  created_practice_item_id TEXT,      -- filled when applied
  created_learning_object_id TEXT,    -- filled when a new LO was applied
  route TEXT NOT NULL CHECK (route IN
    ('auto_apply', 'review_required', 'diagnostic_pending', 'existing_item')),
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

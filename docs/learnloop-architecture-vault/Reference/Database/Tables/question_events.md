---
title: "question_events"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite question_events"
  - "table question_events"
schema_head: 157
table_name: "question_events"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "tutor-and-remediation"
introduced_in: "019_question_events.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/019_question_events.sql"
  - "src/learnloop/attempts/coldness_receipt.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/followups.py"
  - "src/learnloop/learner/facet_diagnostics.py"
  - "src/learnloop/reader/reader_dialogue.py"
  - "src/learnloop/tutor/promotions.py"
  - "src/learnloop/tutor/question_queue.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/tutor-and-remediation"
---

# `question_events`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Preserves an append-only chronology of question so tutor and repair work can be resumed, reviewed, and connected to subsequent evidence. It supplies replay-stable input rather than a disposable cache. Rows bind `note_id`, `practice_item_id`, `attempt_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Tutor Q&A ("ask") events. One row per learner question + tutor answer, in one of three contexts: reading a note (library), mid-attempt (practice), or post-grade (feedback). Facets/type come from the tutor classification; hint_equivalent marks substantive mid-attempt questions that dampen the next attempt's evidence through the existing hints pipeline; leak_suspected is telemetry from the practice-context answer-leak check. rating is the learner's 1 (useful) / 0 (not useful) thumb, NULL until rated.

It belongs to the **tutor and remediation** navigation family. The family context lives in [[Database Catalog#Tutor And Remediation]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/019_question_events.sql`.
- **Schema touched by:** `019_question_events.sql`, `026_question_event_answer_status.sql`, `027_question_promotions.sql`, `030_probe_pilot_and_policy.sql`, `086_reader_dialogue.sql`, `102_question_resolution.sql`, `117_question_promotion_jobs_and_queue_revision.sql`, `151_cold_measurement_opportunities.sql`, `154_reveal_ledger.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `context` | `TEXT` | yes | — | — | Stored value |
| `note_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `practice_item_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `attempt_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `question_md` | `TEXT` | yes | — | — | Stored value |
| `answer_md` | `TEXT` | no | — | — | Stored value |
| `question_type` | `TEXT` | no | — | — | Stored value |
| `facets_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `hint_equivalent` | `INTEGER` | yes | `0` | — | Stored value |
| `leak_suspected` | `INTEGER` | yes | `0` | — | Stored value |
| `rating` | `INTEGER` | no | — | — | Stored value |
| `seconds_into_attempt` | `REAL` | no | — | — | Stored value |
| `provider` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `answer_status` | `TEXT` | yes | `'answered'` | — | Stored value |
| `saved_note_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `preceding_tutor_move` | `TEXT` | no | — | — | Stored value |
| `scaffold_level` | `TEXT` | no | — | — | Stored value |
| `warning_state` | `TEXT` | no | — | — | Stored value |
| `learner_mode` | `TEXT` | no | — | — | Stored value |
| `question_opportunity` | `TEXT` | no | — | — | Stored value |
| `hints_used_before` | `INTEGER` | no | — | — | Stored value |
| `direct_explanation_request` | `INTEGER` | yes | `0` | — | Stored value |
| `attempt_progress` | `TEXT` | no | — | — | Stored value |
| `signal_channel` | `TEXT` | no | — | — | Stored value |
| `resolution` | `TEXT` | yes | `'open'` | — | Stored value |
| `source_context_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `leak_overlap` | `REAL` | no | — | — | Stored value |
| `remediation_episode_id` | `TEXT` | no | — | — | Application-validated soft reference |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_question_events_remediation_episode` on `remediation_episode_id`.
- `idx_question_events_created` on `created_at`, `id`.
- `idx_question_events_resolution` on `resolution`, `created_at`.
- `idx_question_events_note` on `note_id`.
- `idx_question_events_item_session` on `practice_item_id`, `session_id`.
- `sqlite_autoindex_question_events_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.count_hint_equivalent_question_events()`
- `Repository.count_question_events()`
- `Repository.insert_question_event()`
- `Repository.question_counts_by_facet()`
- `Repository.question_event()`
- `Repository.question_events()`
- `Repository.set_question_event_rating()`
- `Repository.set_question_event_resolution()`
- `Repository.set_question_event_saved_note()`
- `Repository.update_question_event_answer()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/coldness_receipt.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/learner/facet_diagnostics.py`
- `src/learnloop/reader/reader_dialogue.py`
- `src/learnloop/tutor/promotions.py`
- `src/learnloop/tutor/question_queue.py`
- `src/learnloop/tutor/question_signal.py`
- `src/learnloop/tutor/tutor_qa.py`
- `src/learnloop_sidecar/handlers/facets.py`
- `src/learnloop_sidecar/handlers/tutor_qa.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_coldness_receipt.py`
- `tests/test_migrations.py`
- `tests/test_question_promotions.py`
- `tests/test_question_signal.py`
- `tests/test_reader_dialogue.py`
- `tests/test_reveal_ledger.py`
- `tests/test_tutor_qa.py`
- `tests/test_question_context.py`
- `tests/test_question_promotion_jobs.py`
- `tests/test_question_queue.py`
- `tests/test_scheduler_requested_floor.py`
- `tests/test_sidecar_tutor_qa.py`
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
CREATE TABLE "question_events" (
  id TEXT PRIMARY KEY,
  context TEXT NOT NULL CHECK (context IN ('library', 'practice', 'feedback', 'reader')),
  note_id TEXT,
  practice_item_id TEXT,
  attempt_id TEXT,
  session_id TEXT,
  question_md TEXT NOT NULL,
  answer_md TEXT,
  question_type TEXT CHECK (
    question_type IN ('clarification', 'prerequisite', 'mechanism', 'strategy', 'verification', 'other')
  ),
  facets_json TEXT,
  hint_equivalent INTEGER NOT NULL DEFAULT 0,
  leak_suspected INTEGER NOT NULL DEFAULT 0,
  rating INTEGER,
  seconds_into_attempt REAL,
  provider TEXT,
  created_at TEXT NOT NULL,
  answer_status TEXT NOT NULL DEFAULT 'answered'
    CHECK (answer_status IN ('pending', 'answered', 'failed')),
  saved_note_id TEXT,
  preceding_tutor_move TEXT,
  scaffold_level TEXT,
  warning_state TEXT,
  learner_mode TEXT,
  question_opportunity TEXT,
  hints_used_before INTEGER,
  direct_explanation_request INTEGER NOT NULL DEFAULT 0,
  attempt_progress TEXT,
  signal_channel TEXT CHECK (
    signal_channel IS NULL OR signal_channel IN ('epistemic', 'interaction_preference')
  )
, resolution TEXT NOT NULL DEFAULT 'open'
  CHECK (resolution IN ('open', 'resolved', 'dismissed')), source_context_json TEXT, leak_overlap REAL, remediation_episode_id TEXT);
```

## Related notes

- [[Database Catalog#Tutor And Remediation|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

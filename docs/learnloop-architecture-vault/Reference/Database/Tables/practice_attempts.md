---
title: "practice_attempts"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite practice_attempts"
  - "table practice_attempts"
schema_head: 157
table_name: "practice_attempts"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/attempts/coldness_receipt.py"
  - "src/learnloop/attempts/trace_evidence.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/db/stores/observation_ledger.py"
  - "src/learnloop/diagnosis/probes.py"
  - "src/learnloop/diagnosis/scoreboard.py"
  - "src/learnloop/goals/goal_series.py"
  - "src/learnloop/attempts/attempt_trace.py"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/attempts/calibration_streams.py"
  - "src/learnloop/attempts/clarification.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `practice_attempts`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Stores the authoritative learner-attempt ledger used by grading, replay, diagnosis, and scheduling. It supplies replay-stable input rather than a disposable cache. Rows bind `practice_item_id`, `learning_object_id`, `session_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`, `004_allow_open_text_attempt_type.sql`, `005_attempt_feedback_metadata.sql`, `006_ai_provider_metadata.sql`, `007_recall_coverage_interventions.sql`, `008_ability_transition_events.sql`, `010_scheduler_training_logs.sql`, `011_training_dataset_logging.sql`, `012_facet_diagnostic_state.sql`, `017_followup_ratings.sql`, `018_exam_evidence_attempt_type.sql`, `020_teach_back_attempt_type.sql`, `021_primed_attempts.sql`, `022_exam_attempt_type.sql`, `028_probe_episodes.sql`, `031_block_end_and_longform.sql`, `053_attempt_submission_idempotency.sql`, `058_remediation_episodes.sql`, `111_deterministic_grading_source.sql`, `139_certification_cold_probes.sql`, `141_conjunctive_instruments.sql`, `142_grading_clarifications.sql`, `143_instrument_classes.sql`, `144_diagnostic_augmentation.sql`, `151_cold_measurement_opportunities.sql`, `153_variable_rubric_scales.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `practice_item_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `subject` | `TEXT` | no | — | — | Stored value |
| `concept` | `TEXT` | no | — | — | Stored value |
| `practice_mode` | `TEXT` | yes | — | — | Stored value |
| `attempt_type` | `TEXT` | yes | — | — | Stored value |
| `learner_answer_md` | `TEXT` | no | — | — | Stored value |
| `evidence_facets_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `evidence_weights_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `rubric_score` | `INTEGER` | no | — | — | Stored value |
| `correctness` | `REAL` | no | — | — | Stored value |
| `confidence` | `INTEGER` | no | — | — | Stored value |
| `latency_seconds` | `INTEGER` | no | — | — | Stored value |
| `hints_used` | `INTEGER` | yes | `0` | — | Stored value |
| `error_type` | `TEXT` | no | — | — | Stored value |
| `grader_confidence` | `REAL` | no | — | — | Stored value |
| `manual_review` | `INTEGER` | yes | `0` | — | Stored value |
| `manual_review_reason` | `TEXT` | no | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `session_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `scheduler_slate_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `scheduler_candidate_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `primed` | `INTEGER` | yes | `0` | — | Stored value |
| `probe_presentation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `answer_confidence` | `INTEGER` | no | — | — | Stored value |
| `submission_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `declared_dont_know` | `INTEGER` | yes | `0` | — | Stored value |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_practice_attempts_item_created` on `practice_item_id`, `created_at`, `id`.
- `idx_practice_attempts_created` on `created_at`, `id`.
- `idx_practice_attempts_submission_id` on `submission_id` (unique).
- `idx_attempts_probe_presentation` on `probe_presentation_id` (unique).
- `idx_attempts_item_time` on `practice_item_id`, `created_at`.
- `idx_attempts_lo_time` on `learning_object_id`, `created_at`.
- `sqlite_autoindex_practice_attempts_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository._insert_learning_outcome_labels()`
- `Repository._insert_practice_attempt()`
- `Repository._link_attempt_to_scheduler_candidate()`
- `Repository._projected_causal_candidates()`
- `Repository.attempt_count()`
- `Repository.attempt_count_for_learning_objects()`
- `Repository.attempt_innovation_samples()`
- `Repository.attempt_regrade_marker()`
- `Repository.attempted_practice_item_ids()`
- `Repository.attempts_pending_clarification_review()`
- `Repository.attempts_with_feedback_shown_between()`
- `Repository.calibration_duel_pairs()`
- `Repository.chosen_candidate_outcomes()`
- `Repository.count_attempts_with_error_type()`
- `Repository.count_clean_attempts_since()`
- `Repository.daily_attempt_counts()`
- `Repository.daily_qualifying_attempt_counts_for_learning_objects()`
- `Repository.fetch_practice_attempt()`
- `Repository.find_attempt_id_by_evidence_agent_run()`
- `Repository.find_record()`
- `Repository.followup_source_attempt()`
- `Repository.item_attempt_history()`
- `Repository.learning_object_ids_with_attempts()`
- `Repository.list_all_attempts()`
- `Repository.list_attempt_history()`
- `Repository.list_attempts_by_learning_object()`
- `Repository.list_recent_attempts_by_learning_objects()`
- `Repository.list_recent_attempts_by_practice_item()`
- `Repository.median_attempt_latency_seconds()`
- `Repository.ordinary_practice_attempt_count()`
- `Repository.pending_followup_practice_items()`
- `Repository.pending_self_grade_regrade_attempts()`
- `Repository.practice_attempt_by_submission_id()`
- `Repository.practice_attempt_outcomes_for_items()`
- `Repository.practice_attempts_between()`
- `Repository.practice_attempts_for_items_before()`
- `Repository.prediction_interval_rows()`
- `Repository.primed_attempt_exists_for_learning_object()`
- `Repository.probe_observations_for_episode()`
- `Repository.qualifying_probe_observation_count_for_session()`
- `Repository.real_attempt_trace_rows()`
- `Repository.record_deferred_regrade()`
- `Repository.regrade_epoch_transitions()`
- `Repository.replace_attempt_derived_outcome()`
- `Repository.requested_practice_item_ids()`
- `Repository.reset_learning_object_derived_state()`
- `Repository.review_session_rows()`
- `Repository.session_attempt_counts()`
- `Repository.session_learner_answers()`
- `Repository.update_attempt_grade()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`
- `src/learnloop/db/stores/observation_ledger.py`
- `src/learnloop/diagnosis/probes.py`
- `src/learnloop/diagnosis/scoreboard.py`
- `src/learnloop/goals/goal_series.py`
- `src/learnloop_sidecar/handlers/goals.py`
- `src/learnloop_sidecar/handlers/sessions.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempt_trace.py`
- `src/learnloop/attempts/attempts.py`
- `src/learnloop/attempts/calibration_streams.py`
- `src/learnloop/attempts/clarification.py`
- `src/learnloop/attempts/coldness_receipt.py`
- `src/learnloop/attempts/grade_resolution.py`
- `src/learnloop/attempts/grading.py`
- `src/learnloop/attempts/measurement_corrections.py`
- `src/learnloop/attempts/regrade.py`
- `src/learnloop/cli/app.py`
- `src/learnloop/content/authoring/contract_commissioning.py`
- `src/learnloop/content/authoring/laddered_stems.py`
- `src/learnloop/content/authoring/persona_realism.py`
- `src/learnloop/content/proposals/proposals.py`
- `src/learnloop/curriculum/curriculum_locks.py`
- `src/learnloop/curriculum/graph_edit_proposals.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/calibration_sessions.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_diagnostic_selector.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_activity_backfill.py`
- `tests/test_answer_calibration_duel.py`
- `tests/test_apply_write_ahead.py`
- `tests/test_characterization_probe_regrade.py`
- `tests/test_coldness_receipt.py`
- `tests/test_dialogue_causal_join.py`
- `tests/test_exam_calibration.py`
- `tests/test_exam_seeding.py`
- `tests/test_forecast_ledger.py`
- `tests/test_gate_fit.py`
- `tests/test_goal_pace.py`
- `tests/test_grade_resolution_pipeline.py`
- `tests/test_migrate_fresh.py`
- `tests/test_migrations.py`
- `tests/test_mvp09_upgrade.py`
- `tests/test_p0_cutover_mvp08.py`
- `tests/test_p0_projection_cutover.py`
- `tests/test_question_promotions.py`
- `tests/test_question_signal.py`
- `tests/test_rebuild_orchestrator.py`

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
CREATE TABLE "practice_attempts" (
  id TEXT PRIMARY KEY,
  practice_item_id TEXT NOT NULL,
  learning_object_id TEXT NOT NULL,
  subject TEXT,
  concept TEXT,
  practice_mode TEXT NOT NULL,
  attempt_type TEXT NOT NULL CHECK (
    attempt_type IN (
      'independent_attempt',
      'hinted_attempt',
      'dont_know',
      'diagnostic_probe',
      'guided_walkthrough',
      'reconstruction_after_walkthrough',
      'skip',
      'self_report',
      'open_text',
      'exam_evidence',
      'teach_back',
      'exam_attempt'
    )
  ),
  learner_answer_md TEXT,
  evidence_facets_json TEXT,
  evidence_weights_json TEXT,
  rubric_score INTEGER CHECK (rubric_score IS NULL OR rubric_score >= 0),
  correctness REAL CHECK (correctness IS NULL OR (correctness >= 0.0 AND correctness <= 1.0)),
  confidence INTEGER CHECK (confidence IS NULL OR confidence BETWEEN 1 AND 5),
  latency_seconds INTEGER CHECK (latency_seconds IS NULL OR latency_seconds >= 0),
  hints_used INTEGER NOT NULL DEFAULT 0 CHECK (hints_used >= 0),
  error_type TEXT,
  grader_confidence REAL CHECK (
    grader_confidence IS NULL OR (grader_confidence >= 0.0 AND grader_confidence <= 1.0)
  ),
  manual_review INTEGER NOT NULL DEFAULT 0 CHECK (manual_review IN (0, 1)),
  manual_review_reason TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT,
  session_id TEXT,
  scheduler_slate_id TEXT,
  scheduler_candidate_id TEXT,
  primed INTEGER NOT NULL DEFAULT 0,
  probe_presentation_id TEXT,
  answer_confidence INTEGER,
  submission_id TEXT,
  declared_dont_know INTEGER NOT NULL DEFAULT 0
);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

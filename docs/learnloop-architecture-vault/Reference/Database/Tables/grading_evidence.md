---
title: "grading_evidence"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "671719446447a45d2900f7212e75b625356d61b0"
source_commit_timestamp: "2026-10-26T13:30:49-04:00"
last_verified: "2026-09-23"
aliases:
  - "state.sqlite grading_evidence"
  - "table grading_evidence"
schema_head: 222
table_name: "grading_evidence"
table_role: "raw_ledger"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/adaptive_difficulty/column_classes.py"
  - "src/learnloop/adaptive_difficulty/material_view.py"
  - "src/learnloop/adaptive_difficulty/protected_tables.py"
  - "src/learnloop/attempts/grade_resolution.py"
  - "src/learnloop/attempts/grading_support.py"
  - "src/learnloop/attempts/regrade.py"
  - "src/learnloop/attempts/stuck.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/attempts/attempt_trace.py"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/attempts/clarification.py"
  - "src/learnloop/attempts/coldness_receipt.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/raw-ledger"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `grading_evidence`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives grading evidence a stable database identity so an attempt can be graded, replayed, and traced back to the evidence that changed learner state. It supplies replay-stable input rather than a disposable cache. Rows bind `attempt_id`, `criterion_id`, `agent_run_id`, making the operational relationship explicit. ^table-purpose

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Raw Ledger]].

## Persistence and lifecycle contract

- **Role:** `raw_ledger` — Authoritative replay input or mixed authoritative state. The rebuild umbrella preserves it.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`, `012_facet_diagnostic_state.sql`, `034_assessment_contract_snapshots.sql`, `141_conjunctive_instruments.sql`, `142_grading_clarifications.sql`, `144_diagnostic_augmentation.sql`, `156_projection_ledger_indexes.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `attempt_id` | `TEXT` | yes | — | FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `criterion_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `points_awarded` | `REAL` | yes | — | — | Stored value |
| `evidence` | `TEXT` | no | — | — | Stored value |
| `notes` | `TEXT` | no | — | — | Stored value |
| `agent_run_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `local_grader_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `grader_tier` | `INTEGER` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `superseded_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `superseded_by_evidence_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `learner_confidence` | `TEXT` | no | — | — | Stored value |
| `assessment_contract_version_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `grading_revision` | `INTEGER` | no | — | — | Stored value |
| `observation_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `recipe_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `attribution_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `correlation_group` | `TEXT` | no | — | — | Stored value |

## Relationships and access paths

Declared SQLite foreign keys:

- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `idx_grading_evidence_live_replay` on `attempt_id`, `created_at`, `criterion_id`, `id`.
- `idx_grading_evidence_observation_id` on `observation_id` (unique).
- `idx_grading_evidence_attempt` on `attempt_id`.
- `sqlite_autoindex_grading_evidence_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository._grading_epoch_transitions()`
- `Repository._insert_grading_evidence()`
- `Repository.attempt_regrade_marker()`
- `Repository.clarification_rate_counts()`
- `Repository.fetch_grading_evidence()`
- `Repository.find_attempt_id_by_evidence_agent_run()`
- `Repository.find_record()`
- `Repository.grading_correction_count_between()`
- `Repository.insert_regrade_evidence()`
- `Repository.list_grading_evidence_history()`
- `Repository.observation_attempt_id()`
- `Repository.pending_self_grade_regrade_attempts()`
- `Repository.record_deferred_regrade()`
- `Repository.regrade_epoch_transitions()`
- `Repository.supersede_self_grade_rows()`

### Direct SQL readers

- `src/learnloop/confidence_events.py`
- `src/learnloop/daily_plan/router_teach_back.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/db/stores/answered_contracts.py`
- `src/learnloop/db/stores/facet_identity.py`
- `src/learnloop/db/stores/observation_ledger.py`
- `src/learnloop/db/stores/write_provenance.py`
- `src/learnloop/diagnosis/forecast_receipts.py`
- `src/learnloop/diagnosis/offline_review/report.py`
- `src/learnloop/diagnosis/split/history.py`
- `src/learnloop/diagnosis/split/reports.py`
- `src/learnloop/evsi_calibration/forecast_report.py`
- `src/learnloop/evsi_calibration/live_report.py`
- `src/learnloop/field/outcomes.py`
- `src/learnloop/field/probability_states.py`
- `src/learnloop/held_grades.py`
- `src/learnloop/placement/state.py`
- `src/learnloop/substrate/canonical_projection.py`
- `src/learnloop/workbench/help_outcomes.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempt_trace.py`
- `src/learnloop/attempts/attempts.py`
- `src/learnloop/attempts/clarification.py`
- `src/learnloop/attempts/coldness_receipt.py`
- `src/learnloop/attempts/grade_resolution.py`
- `src/learnloop/attempts/regrade.py`
- `src/learnloop/cli/app.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/diagnosis/causal_orchestrator.py`
- `src/learnloop/diagnosis/causal_probe_coherence.py`
- `src/learnloop/diagnosis/misconceptions.py`
- `src/learnloop/diagnosis/probe_episodes.py`
- `src/learnloop/diagnosis/split/live.py`
- `src/learnloop/learner/facet_evidence_timeline.py`
- `src/learnloop/learner/learner_review_feed.py`
- `src/learnloop/tui/screens/feedback.py`
- `src/learnloop/tutor/tutor_qa.py`
- `src/learnloop_sidecar/handlers/inspector.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/figure_fixtures.py`
- `tests/mcp_world.py`
- `tests/source_service_fakes.py`
- `tests/test_ad23_fix_review.py`
- `tests/test_ad2_model.py`
- `tests/test_ad3_reading.py`
- `tests/test_ad3_subject_view.py`
- `tests/test_answer_signal_arms.py`
- `tests/test_assumed_known.py`
- `tests/test_characterization_certification_ledger.py`
- `tests/test_cli_attempt.py`
- `tests/test_cli_json.py`
- `tests/test_diagnosis_context.py`
- `tests/test_diagnosis_input_provenance.py`
- `tests/test_diagnosis_input_provenance_landing.py`
- `tests/test_diagnostic_augmentation.py`
- `tests/test_e2e_local.py`
- `tests/test_facet_outcome_view.py`
- `tests/test_family_memory_projection.py`
- `tests/test_field_signal_production_paths.py`

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
CREATE TABLE grading_evidence (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES practice_attempts(id) ON DELETE CASCADE,
  criterion_id TEXT NOT NULL,
  points_awarded REAL NOT NULL,
  evidence TEXT,
  notes TEXT,
  agent_run_id TEXT,
  local_grader_id TEXT,
  grader_tier INTEGER NOT NULL CHECK (grader_tier BETWEEN 0 AND 4),
  created_at TEXT NOT NULL,
  superseded_at TEXT,
  superseded_by_evidence_id TEXT
, learner_confidence TEXT, assessment_contract_version_id TEXT, grading_revision INTEGER, observation_id TEXT, recipe_id TEXT, attribution_json TEXT, correlation_group TEXT);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Raw Ledger|raw_ledger policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

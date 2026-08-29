---
title: "attempt_surprise"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite attempt_surprise"
  - "table attempt_surprise"
schema_head: 156
table_name: "attempt_surprise"
table_role: "derived"
functionality_status: "active"
domain_family: "attempts-and-measurement"
introduced_in: "001_initial.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/001_initial.sql"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/followups.py"
  - "src/learnloop/diagnosis/signal_quantiles.py"
  - "src/learnloop/ops/debug_time.py"
  - "src/learnloop/ops/doctor.py"
  - "src/learnloop/scheduling/evaluation.py"
  - "src/learnloop/substrate/rebuild_orchestrator.py"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/content/proposals/proposals.py"
  - "src/learnloop/diagnosis/causal_attribution.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/derived"
  - "learnloop/status/active"
  - "learnloop/domain/attempts-and-measurement"
---

# `attempt_surprise`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Materializes per-attempt Bayesian surprise and follow-up gate diagnostics. Its current rows may be cleared and reconstructed by the registered projection owner. Rows bind `attempt_id`, `algorithm_version`, `predictive_surprise`, making the operational relationship explicit. ^table-purpose

It belongs to the **attempts and measurement** navigation family. The family context lives in [[Database Catalog#Attempts And Measurement]]. Its persistence behavior follows [[Table Roles#Derived]].

## Persistence and lifecycle contract

- **Role:** `derived` — Clearable projection reconstructed by exactly one registered replayer.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/001_initial.sql`.
- **Schema touched by:** `001_initial.sql`, `015_followup_gate_trace.sql`, `017_followup_ratings.sql`.
- **Rebuild owner:** `learning_state`

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `attempt_id` | `TEXT` | no | — | PRIMARY KEY; FK → [[Reference/Database/Tables/practice_attempts\|practice_attempts.id]] | Stored value |
| `predicted_score_dist_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `predicted_error_type_dist_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `observed_joint_bucket_json` | `TEXT` | yes | — | — | JSON-encoded structured payload |
| `predictive_surprise` | `REAL` | no | — | — | Stored value |
| `bayesian_surprise` | `REAL` | no | — | — | Stored value |
| `surprise_direction` | `TEXT` | no | — | — | Stored value |
| `fsrs_interval_factor` | `REAL` | no | — | — | Stored value |
| `posterior_delta_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `triggered_actions_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `suppressed_actions_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `gate_diagnostics_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

Declared SQLite foreign keys:

- `attempt_id` → [[Reference/Database/Tables/practice_attempts|`practice_attempts.id`]]; on delete `CASCADE`, on update `NO ACTION`.

Indexes and uniqueness:

- `sqlite_autoindex_attempt_surprise_1` on `attempt_id` (unique).

## Who calls it

### Repository access surface

- `Repository._insert_attempt_surprise()`
- `Repository.attempt_innovation_samples()`
- `Repository.find_record()`
- `Repository.followup_source_attempt()`
- `Repository.gate_training_rows()`
- `Repository.latest_attempt_surprise()`
- `Repository.list_attempt_history()`
- `Repository.pending_followup_practice_items()`
- `Repository.prediction_interval_rows()`
- `Repository.recent_surprise_signals()`
- `Repository.replace_attempt_derived_outcome()`
- `Repository.reset_learning_object_derived_state()`
- `Repository.review_session_rows()`
- `Repository.update_attempt_surprise_actions()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`
- `src/learnloop_sidecar/handlers/sessions.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`

### Upstream callers of the repository access surface

- `src/learnloop/attempts/attempts.py`
- `src/learnloop/cli/app.py`
- `src/learnloop/content/proposals/proposals.py`
- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/causal_attribution.py`
- `src/learnloop/diagnosis/causal_migration.py`
- `src/learnloop/diagnosis/followups.py`
- `src/learnloop/diagnosis/gate_fit.py`
- `src/learnloop/diagnosis/probe_episodes.py`
- `src/learnloop/diagnosis/signal_quantiles.py`
- `src/learnloop/learner/calibration.py`
- `src/learnloop/learner/facet_evidence_timeline.py`
- `src/learnloop/learner/learner_review_feed.py`
- `src/learnloop/learner/recall_calibration.py`
- `src/learnloop/learner/session_learning_diff.py`
- `src/learnloop/scheduling/evaluation.py`
- `src/learnloop/scheduling/scheduler.py`
- `src/learnloop/substrate/replay.py`
- `src/learnloop_sidecar/handlers/feedback.py`
- `src/learnloop_sidecar/handlers/inspector.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_gate_fit.py`
- `tests/test_rebuild_orchestrator.py`
- `tests/test_signal_quantiles.py`
- `tests/test_agent_runs.py`
- `tests/test_attempt_ai_flow.py`
- `tests/test_attempts.py`
- `tests/test_certification_cold_probe.py`
- `tests/test_cli_attempt.py`
- `tests/test_cli_generate_practice.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_e2e_local.py`
- `tests/test_followups.py`
- `tests/test_instrument_servability_journeys.py`
- `tests/test_irt_end_to_end.py`
- `tests/test_item_parameters.py`
- `tests/test_misconception_routing.py`
- `tests/test_post_attempt_pipeline.py`
- `tests/test_probe_orchestration_remainder.py`
- `tests/test_receipt_derivation.py`

Always include `tests/test_migrations.py` and `tests/test_table_roles.py` when changing its schema or role. DERIVED-table changes also require `tests/test_rebuild_orchestrator.py` and `tests/test_shadow_rebuild.py`.

## Extension and modification guidance

1. Put schema evolution in a new numbered file under `migrations/`; never edit the meaning of an already-applied migration for existing vaults.
2. Update `src/learnloop/db/table_roles.py` in the same change. A new table without a role fails the migration-head registry test.
3. Keep SQL access at the repository/store boundary; put policy in the domain callers listed above.
4. Preserve append-only triggers and historical rows. Do not infer that an empty fixture table is safe to drop.
5. Update the single owner in `DERIVED_STATE_REPLAYERS`, then prove same-version rebuild equivalence and shadow isolation.

## Live schema DDL

> [!tip] Why keep the DDL here?
> It captures CHECK constraints and defaults that a column summary can hide. The migration files remain authoritative.

```sql
CREATE TABLE attempt_surprise (
  attempt_id TEXT PRIMARY KEY REFERENCES practice_attempts(id) ON DELETE CASCADE,
  predicted_score_dist_json TEXT,
  predicted_error_type_dist_json TEXT,
  observed_joint_bucket_json TEXT NOT NULL,
  predictive_surprise REAL,
  bayesian_surprise REAL,
  surprise_direction TEXT CHECK (
    surprise_direction IS NULL OR surprise_direction IN ('positive', 'negative', 'mixed', 'none')
  ),
  fsrs_interval_factor REAL,
  posterior_delta_json TEXT,
  triggered_actions_json TEXT,
  suppressed_actions_json TEXT,
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL
, gate_diagnostics_json TEXT);
```

## Related notes

- [[Database Catalog#Attempts And Measurement|Sibling tables in this family]]
- [[Table Roles#Derived|derived policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

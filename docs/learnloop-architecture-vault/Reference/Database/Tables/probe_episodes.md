---
title: "probe_episodes"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "589b35df8e5e3ce56849cbdab681c6bc12737419"
source_commit_timestamp: "2026-09-03T10:26:28-07:00"
last_verified: "2026-08-18"
aliases:
  - "state.sqlite probe_episodes"
  - "table probe_episodes"
schema_head: 157
table_name: "probe_episodes"
table_role: "workflow"
functionality_status: "active"
domain_family: "diagnosis"
introduced_in: "028_probe_episodes.sql"
generated: true
source_paths:
  - "src/learnloop/db/table_roles.py"
  - "migrations/028_probe_episodes.sql"
  - "src/learnloop/attempts/attempts.py"
  - "src/learnloop/attempts/coldness_receipt.py"
  - "src/learnloop/curriculum/confusable_concepts.py"
  - "src/learnloop/curriculum/golden_path_run.py"
  - "src/learnloop/db/repositories.py"
  - "src/learnloop/diagnosis/calibration_sessions.py"
  - "src/learnloop/diagnosis/causal_activity_policy.py"
  - "src/learnloop/cli/app.py"
  - "src/learnloop/curriculum/curriculum_locks.py"
  - "src/learnloop/curriculum/depth_rungs.py"
tags:
  - "learnloop/database/table"
  - "learnloop/database/role/workflow"
  - "learnloop/status/active"
  - "learnloop/domain/diagnosis"
---

# `probe_episodes`

> [!info] Active
> The table participates in a current persistence, audit, projection, or workflow contract.

## Why it exists

Gives probe episode a stable database identity so diagnostic selection and repair can distinguish competing explanations instead of guessing from a score. It lets interrupted or asynchronous work resume without pretending in-flight state is historical evidence. Rows bind `learning_object_id`, `hypothesis_set_id`, `active_state_segment_id`, making the operational relationship explicit. ^table-purpose

> [!quote] Migration design note
> Probe/EIG redesign (spec_probe_eig_redesign.md): first-class diagnostic episodes, committed presentations, observation traces, state segments, and the versioned Probe Family / Instrument Card hierarchy. §5.1: one row per diagnostic episode; every entry/re-entry gets a fresh ULID.

It belongs to the **diagnosis** navigation family. The family context lives in [[Database Catalog#Diagnosis]]. Its persistence behavior follows [[Table Roles#Workflow]].

## Persistence and lifecycle contract

- **Role:** `workflow` — Mutable queue, session, lease, or other in-flight workflow state. It is preserved across rebuilds.
- **Functionality status:** `active`.
- **Introduced by:** `migrations/028_probe_episodes.sql`.
- **Schema touched by:** `028_probe_episodes.sql`, `059_probe_episode_origin.sql`, `068_goal_terminal_contracts.sql`, `070_p0_measurement_hardening.sql`, `071_probe_robust_cutover.sql`, `083_diagnostic_pack_and_triage.sql`, `110_probe_action_equivalence.sql`, `113_probe_completion_posterior.sql`, `122_causal_activity_events.sql`.
- **Rebuild owner:** none; this table is preserved by the rebuild umbrella.

For the distinction between SQLite state and human-authored vault files, see [[State and Persistence]]. For whole-vault creation and opening behavior, see [[Vault Lifecycle]]. ^table-lifecycle

## Columns

| Column | SQLite type | Required | Default | Key | Operational reading |
|---|---|---:|---|---|---|
| `id` | `TEXT` | no | — | PRIMARY KEY | Stored value |
| `learning_object_id` | `TEXT` | yes | — | — | Application-validated soft reference |
| `status` | `TEXT` | yes | — | — | Stored value |
| `trigger` | `TEXT` | yes | — | — | Stored value |
| `hypothesis_set_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `active_state_segment_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `target_decision_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `required_facets_json` | `TEXT` | no | — | — | JSON-encoded structured payload |
| `minimum_independent_observations` | `INTEGER` | yes | `2` | — | Stored value |
| `maximum_observations` | `INTEGER` | yes | `4` | — | Stored value |
| `entered_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `completed_at` | `TEXT` | no | — | — | Timestamp (ISO-8601 UTC text) |
| `completion_reason` | `TEXT` | no | — | — | Stored value |
| `algorithm_version` | `TEXT` | yes | — | — | Stored value |
| `created_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `updated_at` | `TEXT` | yes | — | — | Timestamp (ISO-8601 UTC text) |
| `origin` | `TEXT` | no | — | — | Stored value |
| `target_contract_version_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `target_support_hash` | `TEXT` | no | — | — | Stored value |
| `calibration_model_id` | `TEXT` | no | — | — | Application-validated soft reference |
| `calibration_model_hash` | `TEXT` | no | — | — | Stored value |
| `probe_mapping_version` | `TEXT` | no | — | — | Stored value |
| `completion_posterior_json` | `TEXT` | no | — | — | JSON-encoded structured payload |

## Relationships and access paths

No SQLite foreign key is declared. Identifier-looking columns are application-validated soft references where applicable; this is common for YAML-owned entities and cross-generation compatibility seams.

Indexes and uniqueness:

- `idx_probe_episodes_target_version` on `target_contract_version_id`.
- `idx_probe_episodes_open` on `learning_object_id` (unique).
- `idx_probe_episodes_lo` on `learning_object_id`, `created_at`.
- `sqlite_autoindex_probe_episodes_1` on `id` (unique).

## Who calls it

### Repository access surface

- `Repository.consumer_pins_for_versions()`
- `Repository.insert_probe_episode()`
- `Repository.latest_completed_probe_episode()`
- `Repository.list_probe_episodes()`
- `Repository.open_probe_episode()`
- `Repository.open_probe_episodes()`
- `Repository.open_state_segment()`
- `Repository.probe_episode()`
- `Repository.probe_episodes_for_learning_object()`
- `Repository.record_scheduler_slate()`
- `Repository.update_probe_episode_status()`

### Direct SQL readers

- `src/learnloop/db/repositories.py`

### Direct SQL writers

- `src/learnloop/db/repositories.py`
- `src/learnloop/diagnosis/probe_episodes.py`

### Upstream callers of the repository access surface

- `src/learnloop/cli/app.py`
- `src/learnloop/curriculum/confusable_concepts.py`
- `src/learnloop/curriculum/curriculum_locks.py`
- `src/learnloop/curriculum/depth_rungs.py`
- `src/learnloop/diagnosis/calibration_sessions.py`
- `src/learnloop/diagnosis/causal_orchestrator.py`
- `src/learnloop/diagnosis/diagnostic_surface_supply.py`
- `src/learnloop/diagnosis/followups.py`
- `src/learnloop/diagnosis/probe_audit.py`
- `src/learnloop/diagnosis/probe_blocks.py`
- `src/learnloop/diagnosis/probe_dialogue.py`
- `src/learnloop/diagnosis/probe_episodes.py`
- `src/learnloop/diagnosis/probe_instance_generation.py`
- `src/learnloop/goals/goal_contracts.py`
- `src/learnloop/scheduling/scheduler.py`
- `src/learnloop/scheduling/state_signals.py`
- `src/learnloop/sim/diagnostic_validation.py`
- `src/learnloop/substrate/canonical_projection.py`
- `src/learnloop/substrate/state_sync.py`
- `src/learnloop/tui/screens/feedback.py`

> [!note] Static-reference boundary
> These lists are evidence from exact table-name SQL and repository-method calls. Dynamic dispatch and higher-level tests may exercise the table without spelling its name.

## Tests that define behavior

- `tests/test_architecture.py`
- `tests/test_causal_orchestrator.py`
- `tests/test_causal_repair_sidecar_rpcs.py`
- `tests/test_characterization_probe_regrade.py`
- `tests/test_characterization_probe_replay.py`
- `tests/test_characterization_probe_submission.py`
- `tests/test_diagnostic_probe_freshness.py`
- `tests/test_dual_authority_administration.py`
- `tests/test_grade_resolution_pipeline.py`
- `tests/test_independent_group_counting.py`
- `tests/test_instrument_servability_journeys.py`
- `tests/test_p2_acceptance.py`
- `tests/test_p2_leakage_suite.py`
- `tests/test_probe_audit.py`
- `tests/test_probe_block_end.py`
- `tests/test_probe_dialogue.py`
- `tests/test_probe_episodes.py`
- `tests/test_probe_hierarchy.py`
- `tests/test_probe_instance_generation.py`
- `tests/test_probe_llm_instances.py`

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
CREATE TABLE "probe_episodes" (
  id TEXT PRIMARY KEY,
  learning_object_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (
    status IN ('pending_items', 'in_progress', 'complete', 'abandoned', 'converted_to_tutoring')
  ),
  trigger TEXT NOT NULL CHECK (
    trigger IN ('initial', 'misconception', 'stale_uncertainty', 'manual', 'goal_diagnostic')
  ),
  hypothesis_set_id TEXT,
  active_state_segment_id TEXT,
  target_decision_json TEXT,
  required_facets_json TEXT,
  minimum_independent_observations INTEGER NOT NULL DEFAULT 2 CHECK (minimum_independent_observations >= 1),
  maximum_observations INTEGER NOT NULL DEFAULT 4 CHECK (maximum_observations >= 1),
  entered_at TEXT,
  completed_at TEXT,
  completion_reason TEXT CHECK (
    completion_reason IS NULL OR completion_reason IN (
      'decision_stable',
      'predictive_uncertainty_below_threshold',
      'observation_budget_exhausted',
      'no_suitable_candidate',
      'converted_to_tutoring',
      'learner_abandoned',
      'manual_stop',
      'fast_path_strong_claim',
      'superseded_by_redesign',
      'couldnt_reliably_distinguish',
      'action_equivalent'
    )
  ),
  algorithm_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  origin TEXT,
  target_contract_version_id TEXT,
  target_support_hash TEXT,
  calibration_model_id TEXT,
  calibration_model_hash TEXT,
  probe_mapping_version TEXT
, completion_posterior_json TEXT);
```

## Related notes

- [[Database Catalog#Diagnosis|Sibling tables in this family]]
- [[Table Roles#Workflow|workflow policy]]
- [[Rebuild Ownership]]
- [[State and Persistence]]
- [[Vault Lifecycle]]

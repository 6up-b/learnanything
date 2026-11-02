---
title: "learnloop.attempts.regrade"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/regrade.py"
source_paths:
  - "src/learnloop/attempts/regrade.py"
source_commit: "42ab0bc90d513d76d7b0eea692d52330b51a8385"
source_commit_timestamp: "2026-10-23T10:49:09-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.regrade module"
  - "src/learnloop/attempts/regrade.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.regrade`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps regrade behavior inside its owning package, [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]]. Its public surface centers on `DeferredRegradeResult`, `run_deferred_regrades`, `run_deferred_ai_regrades`, `regrade_attempt`.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/regrade.py](../../../../../../src/learnloop/attempts/regrade.py) |
| Source lines | 803 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `42ab0bc90d513d76d7b0eea692d52330b51a8385` |
| Commit timestamp | `2026-10-23T10:49:09-04:00` |

## Public API

- `class DeferredRegradeResult` ([source](../../../../../../src/learnloop/attempts/regrade.py), line 59)
  - `as_dict(self) -> dict[str, int | str | None]` (line 65; public)
- `run_deferred_regrades(vault: LoadedVault, repository: Repository, *, runtime: CodexRuntimeReport, codex_client: AIProviderClient | None, limit: int | None=None, clock: Clock | None=None) -> DeferredRegradeResult` ([source](../../../../../../src/learnloop/attempts/regrade.py), line 74)
- `run_deferred_ai_regrades(vault: LoadedVault, repository: Repository, *, runtime: AIRuntimeReport, ai_client: AIProviderClient | None, limit: int | None=None, clock: Clock | None=None) -> DeferredRegradeResult` ([source](../../../../../../src/learnloop/attempts/regrade.py), line 95)
- `regrade_attempt(vault: LoadedVault, repository: Repository, attempt: dict, *, runtime, client: AIProviderClient, grading_source: str, clock: Clock | None, clarification_exchange: dict[str, str] | None=None, purpose: str='grading_regrade') -> 'ValidatedCodexGrade'` ([source](../../../../../../src/learnloop/attempts/regrade.py), line 154) — Re-grade one attempt, superseding its evidence and replaying the LO.

### Module constants

- `LOGGER` ([src/learnloop/attempts/regrade.py](../../../../../../src/learnloop/attempts/regrade.py), line 51)
- `ALL_GRADER_TIERS` ([src/learnloop/attempts/regrade.py](../../../../../../src/learnloop/attempts/regrade.py), line 55)

## Internal implementation anchors

- `_run_deferred_agent_regrades(vault: LoadedVault, repository: Repository, *, runtime, client: AIProviderClient | None, missing_client_reason: str, grading_source: str, limit: int | None, clock: Clock | None) -> DeferredRegradeResult` ([source](../../../../../../src/learnloop/attempts/regrade.py), line 116)
- `_publish_regrade(vault: LoadedVault, repository: Repository, attempt: dict, *, item, learning_object, validated: ValidatedCodexGrade, agent_run_id: str, new_evidence_rows: list[dict], first_new_evidence_id: str, supersede_tiers: tuple[int, ...], new_score: int, rubric, bind_frozen: Any | None, cite_contract: bool=False, primary_error_type: str | None, content_events: list[dict], blind_record: dict | None, prior_blind: dict | None, blind_context_hash: str | None, grader_identity_overrides: dict[str, tuple[str, str] | None] | None, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/attempts/regrade.py), line 561) — Every write of one regrade, in order, inside the caller's transaction.
- `_agent_run_provider_fields(client: AIProviderClient, runtime) -> dict[str, str | None]` ([source](../../../../../../src/learnloop/attempts/regrade.py), line 772)
- `_manual_review_reason(existing: str | None, attempt: dict) -> str | None` ([source](../../../../../../src/learnloop/attempts/regrade.py), line 788)
- `_disagreement_summary(old_evidence, new_evidence_rows, old_score: int, new_score: int) -> str` ([source](../../../../../../src/learnloop/attempts/regrade.py), line 800)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]] — imports `regrade_attempt`; statically calls `regrade_attempt`
- [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]] — imports `DeferredRegradeResult`, `run_deferred_ai_regrades`, `run_deferred_regrades`; statically calls `run_deferred_ai_regrades`, `run_deferred_regrades`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `regrade_attempt`; statically calls `regrade_attempt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `AIProviderClient`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `CodexRuntimeReport`
- [[Reference/Modules/learnloop/ai/runs|learnloop.ai.runs]] — imports `finish_agent_run`; calls `finish_agent_run`
- [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]] — imports `AIRuntimeReport`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `REGRADE_CONTRACT_VERSIONS`, `SOURCE_REFERENCE_GATE_VERSIONS`
- [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] — imports `GRADING_PROMPT_VERSION`, `StuckGradingProposal`, `grading_prompt_version`; calls `grading_prompt_version`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `GradeAttribution`, `_blind_grading_plan`, `assessed_rubric_score`, `attempt_graded_contract`, `regrade_reads_contract`, `snapshot_graded_contract`, `unverified_attribution_json`; calls `GradeAttribution`, `_blind_grading_plan`, `assessed_rubric_score`, `attempt_graded_contract`, `regrade_reads_contract`, `snapshot_graded_contract`, `unverified_attribution_json`
- [[Reference/Modules/learnloop/attempts/blind_grading|learnloop.attempts.blind_grading]] — imports `BLIND_GRADER_OUTPUT_SCHEMA_VERSION`, `split_grading_active`, `validate_blind_grading_proposal`; calls `split_grading_active`, `validate_blind_grading_proposal`
- [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]] — imports `record_clarification`; calls `record_clarification`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `GradingValidationError`, `ValidatedCodexGrade`, `build_grading_context`, `grading_context_hash`, `request_vault_grading_proposal`, `resolved_rubric`, `validate_codex_grading_proposal`, `vault_grading_calibration_identity`, `vault_grading_run_identity`; calls `build_grading_context`, `grading_context_hash`, `request_vault_grading_proposal`, `resolved_rubric`, `validate_codex_grading_proposal`, `vault_grading_calibration_identity`, `vault_grading_run_identity`
- [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] — imports `gated_review_reason`, `record_route_rule_judgment`, `request_blind_grading_run`, `revalidated_support`; calls `gated_review_reason`, `record_route_rule_judgment`, `request_blind_grading_run`, `revalidated_support`
- [[Reference/Modules/learnloop/attempts/stuck|learnloop.attempts.stuck]] — imports `STUCK_READING_KEY`, `record_stuck_reading_judgment`, `stuck_answer_prompt`, `verified_stuck_reading`; calls `record_stuck_reading_judgment`, `stuck_answer_prompt`, `verified_stuck_reading`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `bind_replacement_grade`; calls `bind_replacement_grade`
- [[Reference/Modules/learnloop/db/stores/write_provenance|learnloop.db.stores.write_provenance]] — imports `grading_in_progress`, `record_error_event_lineage`, `record_grading`; calls `grading_in_progress`, `record_error_event_lineage`, `record_grading`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy|learnloop.diagnosis.error_taxonomy]] — imports `persist_unknown_error_type_proposals`; calls `persist_unknown_error_type_proposals`
- [[Reference/Modules/learnloop/grading_epochs|learnloop.grading_epochs]] — imports `next_grading_revision`; calls `next_grading_revision`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `attempt_grade_held`; calls `attempt_grade_held`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `grade_held_for_review`; calls `grade_held_for_review`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `replay_learning_object`; calls `replay_learning_object`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `TEACH_BACK_ATTEMPT_TYPE`, `asked_rubric_score`, `core_criteria`, `restrict_grading_context_to_criteria`; calls `asked_rubric_score`, `core_criteria`, `restrict_grading_context_to_criteria`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/clarification|learnloop.attempts.clarification]], [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]], [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_deferred_regrade.py](../../../../../../tests/test_deferred_regrade.py) — direct import
  - `test_deferred_ai_regrade_records_provider_and_ai_origin`
  - `test_deferred_regrade_failure_leaves_self_grade_current_and_agent_failed`
  - `test_deferred_regrade_preserves_blank_answer_manual_review`
  - `test_deferred_regrade_recomputes_downstream_attempts_for_learning_object`
  - `test_deferred_regrade_records_disagreement_event`
  - `test_deferred_regrade_replays_attempt_derived_state`
  - `test_deferred_regrade_replays_targeted_error_attribution_facets`
  - `test_deferred_regrade_skips_when_runtime_not_ready`
  - `test_deferred_regrade_supersedes_self_grade_and_updates_mastery`
  - `test_deferred_regrade_validates_repaired_trace_against_learner_answer`
- [tests/test_diagnosis_async_router.py](../../../../../../tests/test_diagnosis_async_router.py) — direct import
  - `test_a_failed_or_budget_skipped_diagnosis_is_unavailable_at_the_serve`
- [tests/test_diagnosis_input_provenance.py](../../../../../../tests/test_diagnosis_input_provenance.py) — direct import
  - `test_a_regrade_keeps_the_ids_a_belief_lists_resolvable`
  - `test_f4_a_regrade_to_no_errors_keeps_the_retired_events_answer`
- [tests/test_diagnosis_pipeline.py](../../../../../../tests/test_diagnosis_pipeline.py) — direct import
  - `test_a_crash_between_regrade_publication_steps_publishes_nothing`
  - `test_a_joint_attempt_regraded_in_a_split_vault_is_graded_blind_and_isolated`
  - `test_a_self_graded_fallback_is_regraded_blind_and_queues_its_diagnosis`
  - `test_blind_regrade_supersedes_the_record_and_rediagnoses`
  - `test_regrade_replay_never_reads_the_superseded_diagnosis`
  - `test_regrade_to_full_marks_retires_the_diagnosis`
  - `test_the_accessor_and_the_overlays_agree_on_the_diagnosis_in_force`
- [tests/test_field_split_outcomes.py](../../../../../../tests/test_field_split_outcomes.py) — direct import
  - `test_blind_grades_diagnoses_and_regrades_keep_the_epoch_contract`
- [tests/test_forecast_receipts.py](../../../../../../tests/test_forecast_receipts.py) — direct import
  - `test_a_held_grade_resolves_nothing_until_a_regrade_releases_it`
  - `test_a_regrade_re_resolves_the_forecast`
  - `test_f2_a_grade_that_cites_no_contract_is_never_read_against_todays_rubric`
  - `test_f2_editing_todays_rubric_never_rewrites_a_regraded_self_grade`
  - `test_f3_a_cold_success_regraded_to_failure_is_measured_as_a_failure`
  - `test_f3_a_cold_success_whose_grade_is_now_held_is_not_measured`
- [tests/test_forecast_receipts_landing.py](../../../../../../tests/test_forecast_receipts_landing.py) — direct import
  - `test_the_resolver_reads_the_regraded_events_the_lineage_names_never_a_retired_one`
- [tests/test_grading_support.py](../../../../../../tests/test_grading_support.py) — direct import
  - `test_an_unverified_criterion_writes_no_negative_evidence_even_without_an_attribution`
- [tests/test_held_grade_evidence.py](../../../../../../tests/test_held_grade_evidence.py) — direct import
  - `test_f2_a_regrade_that_validates_nothing_keeps_the_hold`
  - `test_f4_a_validating_regrade_leaves_no_stale_unassessed_row`
  - `test_review_f1_a_regrade_into_a_hold_supersedes_the_assessed_grade_it_replaces`
  - `test_review_f1_the_ledger_reads_the_evidence_as_the_attempt_step_does`
- [tests/test_learner_review_system_entries.py](../../../../../../tests/test_learner_review_system_entries.py) — direct import
- [tests/test_pfc_unassessed_readers.py](../../../../../../tests/test_pfc_unassessed_readers.py) — direct import
  - `test_a_record_written_before_the_rule_keeps_its_interpretation_until_regraded`
  - `test_a_separate_review_concern_survives_the_pfc_flag`
  - `test_the_pfc_flag_is_the_reason_only_when_it_is_the_sole_concern`
- [tests/test_pfc_unverified_unassessed.py](../../../../../../tests/test_pfc_unverified_unassessed.py) — direct import
  - `test_a_regrade_applies_the_same_rule`
- [tests/test_placement_diagnosis_decides.py](../../../../../../tests/test_placement_diagnosis_decides.py) — direct import
  - `test_a_decided_miss_is_not_reopened_by_a_regrade`
- [tests/test_placement_split_grades.py](../../../../../../tests/test_placement_split_grades.py) — direct import
  - `test_a_regrade_to_unverified_keeps_the_topic_in_maintenance`
  - `test_the_check_follows_a_regrade_that_requeues_the_diagnosis`
- [tests/test_provider_resolution_parity.py](../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_config_matrix_executes_all_six_production_resolution_paths`
- [tests/test_reader_recap_review_r3.py](../../../../../../tests/test_reader_recap_review_r3.py) — direct import
- [tests/test_reference_gate_imports.py](../../../../../../tests/test_reference_gate_imports.py) — direct import
- [tests/test_regrade_contract_replay.py](../../../../../../tests/test_regrade_contract_replay.py) — direct import
- [tests/test_regrade_contract_successor.py](../../../../../../tests/test_regrade_contract_successor.py) — direct import
  - `test_a_clarification_regrade_cites_its_contract`
  - `test_a_deferred_regrade_of_a_self_grade_cites_its_contract`
  - `test_a_method_explicit_regrade_cites_its_frozen_contract_under_a_new_revision`
  - `test_the_regrade_snapshot_is_written_in_the_regrade_transaction`
- [tests/test_required_method_authority.py](../../../../../../tests/test_required_method_authority.py) — direct import
  - `test_a_live_answer_its_regrade_and_replay_are_graded_under_the_frozen_field`
- [tests/test_required_method_grading.py](../../../../../../tests/test_required_method_grading.py) — direct import
  - `test_a_regrade_at_the_successor_keeps_the_method_rule_and_a_full_credit_regrade_clears_it`
  - `test_a_regrade_grades_the_statement_and_rubric_its_method_was_frozen_with`
  - `test_a_regrade_never_acquires_a_required_method_added_after_the_answer`
  - `test_every_other_regrade_still_reads_the_item_as_it_is_now`
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — direct import
  - `test_a_ruled_grade_is_calibrated_under_the_rules_identity_and_so_is_its_regrade`
  - `test_f1_live_an_incomplete_regrade_keeps_an_existing_hold`
  - `test_f3_live_a_clarification_regrade_keeps_an_error_the_reply_reveals`
  - `test_f4_the_graders_route_verdict_reaches_the_judgment_ledger_and_regrades_supersede_it`
  - `test_f5_a_joint_regrade_supersedes_a_route_verdict`
  - `test_f5_a_regrade_supersedes_an_mvp017_route_check_verdict`
  - `test_f5_a_regrade_with_the_rule_switched_off_supersedes_the_held_verdict`
  - `test_live_a_regrade_keeps_a_hold_until_the_grader_validates_the_route`
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — direct import
  - `test_a_joint_regrade_rereads_the_stuck_answer_and_supersedes`
  - `test_a_regrade_appends_a_superseding_stuck_judgment`
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_a_teach_back_regraded_blind_keeps_the_blind_identity_through_rebuilds`
  - `test_regrade_teach_back_attempt_restricts_to_graded_criteria`
  - `test_regrade_teach_back_attempt_without_evidence_falls_back_to_core`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_a_regrade_shows_one_rubric_row_per_criterion`
  - `test_f3_a_contest_the_regrade_does_not_uphold_is_queued`
  - `test_f3_a_contest_the_regrade_upholds_needs_no_review`
  - `test_f6_an_ordinary_regrade_history_was_not_held`
  - `test_f6_the_regrade_history_says_the_grade_it_replaced_was_held`
  - `test_f9_a_regrade_outside_the_screen_is_the_current_grade_and_unrecorded`
  - `test_f9f_a_blind_regrade_keeps_the_maximum_recorded_with_it_after_the_question_changed`
  - `test_i_think_i_was_right_regrades_in_place_and_never_hands_the_reason_to_the_grader`

## Modification guidance

- Change regrade policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/regrade.py](../../../../../../src/learnloop/attempts/regrade.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

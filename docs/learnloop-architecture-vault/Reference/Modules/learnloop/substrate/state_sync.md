---
title: "learnloop.substrate.state_sync"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/state_sync.py"
source_paths:
  - "src/learnloop/substrate/state_sync.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.substrate"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.state_sync module"
  - "src/learnloop/substrate/state_sync.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.state_sync`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps state sync behavior inside its owning package, [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]]. Its public surface centers on `StateSyncResult`, `practice_item_activatable`, `reconcile_practice_item_state`, `sync_vault_state`.

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/state_sync.py](../../../../../../src/learnloop/substrate/state_sync.py) |
| Source lines | 292 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class StateSyncResult` ([source](../../../../../../src/learnloop/substrate/state_sync.py), line 14)
  - `as_dict(self) -> dict[str, int]` (line 20; public)
- `practice_item_activatable(item_id: str, item, *, review_parked: set[str], measurement_superseded: set[str], state=None, generated_probe_closed: frozenset[str]=frozenset()) -> bool` ([source](../../../../../../src/learnloop/substrate/state_sync.py), line 29) — The one lifecycle gate shared by full and incremental vault sync.
- `reconcile_practice_item_state(repository: Repository, item_id: str, item, *, state: PracticeItemState | None, review_parked: set[str], measurement_superseded: set[str], content_hash: str | None=None, generated_probe_closed: frozenset[str] | None=None, clock: Clock | None=None) -> tuple[str, bool]` ([source](../../../../../../src/learnloop/substrate/state_sync.py), line 64) — Bring one item's ``active`` flag and content hash in line with its YAML.
- `sync_vault_state(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> StateSyncResult` ([source](../../../../../../src/learnloop/substrate/state_sync.py), line 144) — Reconcile YAML-owned entities with derived SQLite rows.

## Internal implementation anchors

- `_enter_initial_probes(vault: LoadedVault, repository: Repository, *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/substrate/state_sync.py), line 245) — Open initial diagnostic episodes (probe redesign §5/§10).
- `_has_active_local_item(vault: LoadedVault, repository: Repository, learning_object_id: str) -> bool` ([source](../../../../../../src/learnloop/substrate/state_sync.py), line 284)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]] — imports `sync_vault_state`; statically calls `sync_vault_state`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `sync_vault_state`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `sync_vault_state`; statically calls `sync_vault_state`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `sync_vault_state`; statically calls `sync_vault_state`
- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `sync_vault_state`; statically calls `sync_vault_state`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `sync_vault_state`; statically calls `sync_vault_state`
- [[Reference/Modules/learnloop/content/proposals/apply_protocol|learnloop.content.proposals.apply_protocol]] — imports `sync_vault_state`; statically calls `sync_vault_state`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `sync_vault_state`; statically calls `sync_vault_state`
- [[Reference/Modules/learnloop/curriculum/concepts|learnloop.curriculum.concepts]] — imports `sync_vault_state`; statically calls `sync_vault_state`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/actions|learnloop.diagnosis.text_gaps.actions]] — imports `sync_vault_state`; statically calls `sync_vault_state`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/pipeline|learnloop.diagnosis.text_gaps.pipeline]] — imports `sync_vault_state`; statically calls `sync_vault_state`
- [[Reference/Modules/learnloop/goals/goal_lo|learnloop.goals.goal_lo]] — imports `sync_vault_state`; statically calls `sync_vault_state`
- [[Reference/Modules/learnloop/learner/recall_calibration|learnloop.learner.recall_calibration]] — imports `sync_vault_state`; statically calls `sync_vault_state`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `StateSyncResult`, `sync_vault_state`; statically calls `sync_vault_state`
- [[Reference/Modules/learnloop/sim/diagnostic_validation|learnloop.sim.diagnostic_validation]] — imports `sync_vault_state`; statically calls `sync_vault_state`
- [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] — imports `StateSyncResult`, `sync_vault_state`; statically calls `sync_vault_state`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `reconcile_practice_item_state`, `sync_vault_state`; statically calls `reconcile_practice_item_state`, `sync_vault_state`

### Repository tooling consumers

- [scripts/benchmark_sqlite_concurrency.py](../../../../../../scripts/benchmark_sqlite_concurrency.py); calls `sync_vault_state`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `PracticeItemState`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `enter_episode`, `enter_stale_uncertainty_reprobes`; calls `enter_episode`, `enter_stale_uncertainty_reprobes`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `pending_review_instance_ids`; calls `pending_review_instance_ids`
- [[Reference/Modules/learnloop/followup_serve/identity|learnloop.followup_serve.identity]] — imports `closed_probe_ids`; calls `closed_probe_ids`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `resolve_goal_scope`; calls `resolve_goal_scope`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `initial_mastery_state_for_learning_object`; calls `initial_mastery_state_for_learning_object`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `initial_probes_enabled`; calls `initial_probes_enabled`
- [[Reference/Modules/learnloop/scheduling/shadow_components|learnloop.scheduling.shadow_components]] — imports `retire_expired_telemetry`; calls `retire_expired_telemetry`
- [[Reference/Modules/learnloop/substrate/recurrence_groups|learnloop.substrate.recurrence_groups]] — imports `refresh_recurrence_groups`; calls `refresh_recurrence_groups`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `practice_item_hash`; calls `practice_item_hash`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]], [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]], [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] and 12 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/assumed_known_helpers.py](../../../../../../tests/assumed_known_helpers.py) — direct import
- [tests/capability_residual_helpers.py](../../../../../../tests/capability_residual_helpers.py) — direct import
- [tests/causal_factor_deferral_helpers.py](../../../../../../tests/causal_factor_deferral_helpers.py) — direct import
- [tests/causal_p2_acceptance_helpers.py](../../../../../../tests/causal_p2_acceptance_helpers.py) — direct import
- [tests/certification_cold_probe_helpers.py](../../../../../../tests/certification_cold_probe_helpers.py) — direct import
- [tests/daily_loop_reader_authored_practice_helpers.py](../../../../../../tests/daily_loop_reader_authored_practice_helpers.py) — direct import
- [tests/diagnostic_probe_single_use_helpers.py](../../../../../../tests/diagnostic_probe_single_use_helpers.py) — direct import
- [tests/facet_identity_actions_helpers.py](../../../../../../tests/facet_identity_actions_helpers.py) — direct import
- [tests/followup_serve_helpers.py](../../../../../../tests/followup_serve_helpers.py) — direct import
- [tests/graph_editor_reads_helpers.py](../../../../../../tests/graph_editor_reads_helpers.py) — direct import
- [tests/km3_projections_helpers.py](../../../../../../tests/km3_projections_helpers.py) — direct import
- [tests/learner_report_superseded_helpers.py](../../../../../../tests/learner_report_superseded_helpers.py) — direct import
- [tests/learner_text_gaps_flow_helpers.py](../../../../../../tests/learner_text_gaps_flow_helpers.py) — direct import
- [tests/learner_text_gaps_review_helpers.py](../../../../../../tests/learner_text_gaps_review_helpers.py) — direct import
- [tests/lp_claim_fixes_review_helpers.py](../../../../../../tests/lp_claim_fixes_review_helpers.py) — direct import
- [tests/rebuild_equivalence_helpers.py](../../../../../../tests/rebuild_equivalence_helpers.py) — direct import
- [tests/rebuild_equivalence_review_helpers.py](../../../../../../tests/rebuild_equivalence_review_helpers.py) — direct import
- [tests/ro1_self_report_helpers.py](../../../../../../tests/ro1_self_report_helpers.py) — direct import
- [tests/router_probe_ties_helpers.py](../../../../../../tests/router_probe_ties_helpers.py) — direct import
- [tests/test_ad_guard.py](../../../../../../tests/test_ad_guard.py) — direct import
  - `test_incumbent_maintenance_and_vault_loads_never_run_inside_an_operation`
- [tests/test_agent_run_tokens.py](../../../../../../tests/test_agent_run_tokens.py) — direct import
- [tests/test_anti_double_count.py](../../../../../../tests/test_anti_double_count.py) — direct import
- [tests/test_assessment_contracts.py](../../../../../../tests/test_assessment_contracts.py) — direct import
  - `test_legacy_attempt_records_no_observation_lineage`
  - `test_mvp07_attempt_stamps_observation_lineage`
- [tests/test_assumed_known.py](../../../../../../tests/test_assumed_known.py) — direct import
  - `test_kill_switch_ignores_assumptions_made_while_on`
- [tests/test_attempt_ai_flow.py](../../../../../../tests/test_attempt_ai_flow.py) — direct import
  - `test_attempt_ai_flow_records_provider_model_and_ai_source`
- [tests/test_attempt_completion.py](../../../../../../tests/test_attempt_completion.py) — direct import
- [tests/test_attempt_content_state_race.py](../../../../../../tests/test_attempt_content_state_race.py) — direct import
  - `test_a_probe_attempt_still_closes_its_single_use_surface`
- [tests/test_attempt_content_state_successor.py](../../../../../../tests/test_attempt_content_state_successor.py) — direct import
- [tests/test_attempt_write_order.py](../../../../../../tests/test_attempt_write_order.py) — direct import
  - `test_canonical_attempt_write_order_is_receipt_grade_evidence_state_then_post`
- [tests/test_attempts.py](../../../../../../tests/test_attempts.py) — direct import
  - `test_attempt_links_to_scheduler_slate_and_later_retention_label`
  - `test_hinted_attempt_caps_fsrs_rating`
  - `test_self_graded_attempt_updates_attempt_evidence_state_and_surprise`
  - `test_unknown_attempt_type_fails_before_sqlite_insert`
- [tests/test_canonical_projection_fold_skip.py](../../../../../../tests/test_canonical_projection_fold_skip.py) — direct import
- [tests/test_canonical_projection_rollout.py](../../../../../../tests/test_canonical_projection_rollout.py) — direct import
- [tests/test_causal_attribution_exhibit.py](../../../../../../tests/test_causal_attribution_exhibit.py) — direct import
- [tests/test_causal_attribution_p0.py](../../../../../../tests/test_causal_attribution_p0.py) — direct import
  - `test_learner_confirmation_resolves_factor_to_provisional_belief`
  - `test_machine_review_scope_blocks_negative_observation_attribution`
  - `test_nonconfirming_self_report_is_recorded_once_without_reprompt`
- [tests/test_causal_orchestrator.py](../../../../../../tests/test_causal_orchestrator.py) — direct import
  - `test_live_attempt_queues_a_repair_mapping_backfill_that_self_closes`
- [tests/test_causal_repair_mapping_p2.py](../../../../../../tests/test_causal_repair_mapping_p2.py) — direct import
- [tests/test_certification_cold_probe.py](../../../../../../tests/test_certification_cold_probe.py) — direct import
  - `test_a_fresh_diagnostic_surface_remains_selectable_for_the_probe`
  - `test_new_inventory_creates_a_fresh_opportunity_after_structural_refusal`
  - `test_only_administered_diagnostic_candidates_means_no_held_out_surface`
  - `test_rate_is_correct_over_a_mix_of_held_and_failed_certificates`
  - `test_selection_never_picks_an_administered_diagnostic_surface`
- [tests/test_characterization_certification_ledger.py](../../../../../../tests/test_characterization_certification_ledger.py) — direct import
- [tests/test_cli_json.py](../../../../../../tests/test_cli_json.py) — direct import
  - `test_proposals_json_contract`
- [tests/test_codex_attempt_flow.py](../../../../../../tests/test_codex_attempt_flow.py) — direct import
  - `test_attempt_orchestration_falls_back_and_marks_agent_run_failed`
  - `test_attempt_orchestration_falls_back_when_runtime_not_ready`
  - `test_attempt_orchestration_uses_codex_when_runtime_ready`
  - `test_codex_attempt_uses_highest_severity_error_for_observed_joint`
  - `test_codex_graded_attempt_proposes_unknown_error_type`
  - `test_codex_graded_attempt_uses_same_update_path_with_tier_three_evidence`
  - `test_codex_recall_wording_uses_recall_failure_not_new_error_type`
- [tests/test_codex_transport_retired.py](../../../../../../tests/test_codex_transport_retired.py) — direct import
  - `test_an_attempt_graded_by_codex_replays_identically`
- [tests/test_cold_retry_reschedule.py](../../../../../../tests/test_cold_retry_reschedule.py) — direct import
- [tests/test_common_repair_delivery.py](../../../../../../tests/test_common_repair_delivery.py) — direct import
  - `test_receipted_divergence_skips_the_consultation_entirely`
- [tests/test_conjunctive_instruments.py](../../../../../../tests/test_conjunctive_instruments.py) — direct import
- [tests/test_contrast_pairs.py](../../../../../../tests/test_contrast_pairs.py) — direct import
- [tests/test_controller_ownership.py](../../../../../../tests/test_controller_ownership.py) — direct import
- [tests/test_controller_snapshot.py](../../../../../../tests/test_controller_snapshot.py) — direct import
- [tests/test_curriculum_c0b_landing.py](../../../../../../tests/test_curriculum_c0b_landing.py) — direct import
- [tests/test_curriculum_locks.py](../../../../../../tests/test_curriculum_locks.py) — direct import
- [tests/test_daily_loop_lo_lifecycle_serving.py](../../../../../../tests/test_daily_loop_lo_lifecycle_serving.py) — direct import
  - `test_exam_start_does_not_administer_items_of_an_lo_put_away_after_reservation`
- [tests/test_daily_loop_reader_authored_practice.py](../../../../../../tests/test_daily_loop_reader_authored_practice.py) — direct import
  - `test_written_question_keeps_returning_after_it_is_answered`
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
  - `test_startup_maintenance_regrades_pending_self_grade_when_codex_ready`
- [tests/test_device_eligibility.py](../../../../../../tests/test_device_eligibility.py) — direct import
- [tests/test_diagnosis_async_router.py](../../../../../../tests/test_diagnosis_async_router.py) — direct import
  - `test_the_open_factor_takes_the_diagnosis_causes_when_it_lands`
- [tests/test_diagnosis_input_provenance_landing.py](../../../../../../tests/test_diagnosis_input_provenance_landing.py) — direct import
  - `test_q14_on_a_vault_the_coordinator_upgrades_the_receipt_commits_with_the_grade`
- [tests/test_diagnostic_augmentation.py](../../../../../../tests/test_diagnostic_augmentation.py) — direct import
  - `test_a_committed_joint_grade_carries_its_receipt_and_grading_record`
  - `test_a_receipt_that_cannot_be_written_commits_no_augmented_grade`
  - `test_c3_k1_leaves_no_sample_support_on_the_stored_attribution`
- [tests/test_diagnostic_probe_freshness.py](../../../../../../tests/test_diagnostic_probe_freshness.py) — direct import
  - `test_a_fresh_replacement_surface_resolves_the_pending_need`
- [tests/test_diagnostic_probe_single_use.py](../../../../../../tests/test_diagnostic_probe_single_use.py) — direct import
  - `test_vault_sync_does_not_reactivate_an_administered_diagnostic_probe`
- [tests/test_discrimination_profiles.py](../../../../../../tests/test_discrimination_profiles.py) — direct import
- [tests/test_doctor.py](../../../../../../tests/test_doctor.py) — direct import
  - `test_doctor_warns_when_attempt_log_needs_explicit_rebuild_marker`
- [tests/test_dual_authority_administration.py](../../../../../../tests/test_dual_authority_administration.py) — direct import
- [tests/test_durable_promotion_arms.py](../../../../../../tests/test_durable_promotion_arms.py) — direct import
- [tests/test_e2e_codex_mock.py](../../../../../../tests/test_e2e_codex_mock.py) — direct import
  - `test_codex_mocked_end_to_end`
- [tests/test_effective_observation.py](../../../../../../tests/test_effective_observation.py) — direct import
- [tests/test_error_hunt_items.py](../../../../../../tests/test_error_hunt_items.py) — direct import
- [tests/test_evaluation.py](../../../../../../tests/test_evaluation.py) — direct import
- [tests/test_exam_session.py](../../../../../../tests/test_exam_session.py) — direct import
  - `test_an_exam_answer_is_stamped_with_its_graders_calibration_identity`
  - `test_exam_answers_certify_facet_evidence_on_canonical_vault`
- [tests/test_facet_identity_actions.py](../../../../../../tests/test_facet_identity_actions.py) — direct import
- [tests/test_facet_state_write_on_change.py](../../../../../../tests/test_facet_state_write_on_change.py) — direct import
- [tests/test_field_workbench_signals.py](../../../../../../tests/test_field_workbench_signals.py) — direct import
- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f3_a_crash_after_the_pin_ends_the_pin_with_the_retired_item`
  - `test_f3_the_mint_and_the_batch_write_the_identity_before_the_file`
- [tests/test_followup_diagnostic_selection.py](../../../../../../tests/test_followup_diagnostic_selection.py) — direct import
- [tests/test_followup_journey.py](../../../../../../tests/test_followup_journey.py) — direct import
  - `test_the_whole_journey_and_never_again`
- [tests/test_followup_next_matrix.py](../../../../../../tests/test_followup_next_matrix.py) — direct import
- [tests/test_followup_single_use.py](../../../../../../tests/test_followup_single_use.py) — direct import
  - `test_retired_while_unused_stays_retired_after_sync_and_rebuild`
  - `test_state_sync_shares_one_predicate`
- [tests/test_goal_certification_any_of.py](../../../../../../tests/test_goal_certification_any_of.py) — direct import
- [tests/test_grade_resolution_pipeline.py](../../../../../../tests/test_grade_resolution_pipeline.py) — direct import
- [tests/test_grader_channel_prior_knobs.py](../../../../../../tests/test_grader_channel_prior_knobs.py) — direct import
- [tests/test_grading_cli.py](../../../../../../tests/test_grading_cli.py) — direct import
- [tests/test_hot_path_eligibility_cutover.py](../../../../../../tests/test_hot_path_eligibility_cutover.py) — direct import
- [tests/test_identifiability_doctor.py](../../../../../../tests/test_identifiability_doctor.py) — direct import
  - `test_graph_identifiability_report_and_probe_scheduling`
  - `test_pre_first_practice_doctor_watermark`
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_the_certification_cold_probe_selects_an_instrument_as_its_held_out_item`
- [tests/test_intent_fix_round4.py](../../../../../../tests/test_intent_fix_round4.py) — direct import
  - `test_f15_the_probe_contract_carries_the_diagnostic_variant`
- [tests/test_intent_planner.py](../../../../../../tests/test_intent_planner.py) — direct import
- [tests/test_item_authoring.py](../../../../../../tests/test_item_authoring.py) — direct import
  - `test_author_item_creates_learner_card`
  - `test_retire_item_stops_all_serving`
- [tests/test_item_parameters.py](../../../../../../tests/test_item_parameters.py) — direct import
- [tests/test_km2_activation.py](../../../../../../tests/test_km2_activation.py) — direct import
  - `test_app_load_repairs_vault_activated_by_old_upgrade`
  - `test_upgrade_projects_existing_attempts_into_canonical_facet_state`
- [tests/test_km2_sim_gates.py](../../../../../../tests/test_km2_sim_gates.py) — direct import
- [tests/test_km2_write_path.py](../../../../../../tests/test_km2_write_path.py) — direct import
  - `test_rebuild_uses_presented_contract_after_live_target_change`
- [tests/test_km2b_consumer_rekey.py](../../../../../../tests/test_km2b_consumer_rekey.py) — direct import
- [tests/test_km5_sim_gates.py](../../../../../../tests/test_km5_sim_gates.py) — direct import
  - `test_residual_activation_improves_capability_mae_without_parent_inflation`
  - `test_shadow_intent_logs_practice_integration_at_the_right_moment`
- [tests/test_laddered_stems.py](../../../../../../tests/test_laddered_stems.py) — direct import
- [tests/test_large_practice_flow.py](../../../../../../tests/test_large_practice_flow.py) — direct import
  - `test_many_open_text_practice_items_schedule_and_record_attempt`
- [tests/test_learner_report_superseded.py](../../../../../../tests/test_learner_report_superseded.py) — direct import
  - `test_a_new_starting_level_keeps_the_old_one_for_an_lo_first_practised_under_it`
  - `test_random_attempts_and_learner_reports_rebuild_to_live`
- [tests/test_learner_review_system_entries.py](../../../../../../tests/test_learner_review_system_entries.py) — direct import
- [tests/test_learner_text_gaps.py](../../../../../../tests/test_learner_text_gaps.py) — direct import
  - `test_asking_never_lowers_the_record`
- [tests/test_learner_text_gaps_composition.py](../../../../../../tests/test_learner_text_gaps_composition.py) — direct import
- [tests/test_learner_text_gaps_review.py](../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f13_the_pipeline_switched_off_queues_exactly_as_the_predecessor_version`
- [tests/test_lp_claim_fixes.py](../../../../../../tests/test_lp_claim_fixes.py) — direct import
- [tests/test_measurement_corrections.py](../../../../../../tests/test_measurement_corrections.py) — direct import
  - `test_attempted_item_correction_is_append_only_and_projection_versioned`
  - `test_historical_reinterpretation_rejects_a_changed_task`
- [tests/test_measurement_rank.py](../../../../../../tests/test_measurement_rank.py) — direct import
  - `test_computing_the_rank_triggers_no_merge`
  - `test_graph_identifiability_report_publishes_the_rank`
- [tests/test_method_explicit_upgrade.py](../../../../../../tests/test_method_explicit_upgrade.py) — direct import
  - `test_upgrade_from_mvp024_flips_rebuilds_and_rewrites_nothing`
- [tests/test_misconception_resolution.py](../../../../../../tests/test_misconception_resolution.py) — direct import
- [tests/test_mobile_two_process.py](../../../../../../tests/test_mobile_two_process.py) — direct import
  - `test_the_desktop_and_the_host_coexist_with_no_lost_writes`
- [tests/test_mobile_v3_probes.py](../../../../../../tests/test_mobile_v3_probes.py) — direct import
- [tests/test_mvp011_upgrade.py](../../../../../../tests/test_mvp011_upgrade.py) — direct import
  - `test_existing_vaults_keep_their_version_until_the_owner_upgrades`
  - `test_upgrade_from_mvp010_flips_rebuilds_and_preserves_history_and_open_episodes`
- [tests/test_mvp015_upgrade.py](../../../../../../tests/test_mvp015_upgrade.py) — direct import
  - `test_upgrade_from_mvp014_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp016_upgrade.py](../../../../../../tests/test_mvp016_upgrade.py) — direct import
  - `test_upgrade_from_mvp015_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp017_upgrade.py](../../../../../../tests/test_mvp017_upgrade.py) — direct import
  - `test_upgrade_from_mvp016_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp018_upgrade.py](../../../../../../tests/test_mvp018_upgrade.py) — direct import
  - `test_upgrade_from_mvp017_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp020_upgrade.py](../../../../../../tests/test_mvp020_upgrade.py) — direct import
  - `test_upgrade_from_mvp019_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp021_upgrade.py](../../../../../../tests/test_mvp021_upgrade.py) — direct import
  - `test_upgrade_from_mvp020_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp022_upgrade.py](../../../../../../tests/test_mvp022_upgrade.py) — direct import
  - `test_upgrade_from_mvp021_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp023_upgrade.py](../../../../../../tests/test_mvp023_upgrade.py) — direct import
  - `test_upgrade_from_mvp022_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp024_upgrade.py](../../../../../../tests/test_mvp024_upgrade.py) — direct import
  - `test_upgrade_from_mvp023_flips_rebuilds_and_rewrites_nothing`
- [tests/test_observation_ledger_bulk.py](../../../../../../tests/test_observation_ledger_bulk.py) — direct import
- [tests/test_p0_cutover_mvp08.py](../../../../../../tests/test_p0_cutover_mvp08.py) — direct import
  - `test_mvp06_derived_output_is_byte_identical_across_p0_machinery`
- [tests/test_p0_projection_cutover.py](../../../../../../tests/test_p0_projection_cutover.py) — direct import
- [tests/test_placement_fixture_copies.py](../../../../../../tests/test_placement_fixture_copies.py) — direct import
  - `test_placement_ignores_unanswered_opening_episodes_on_fixture_copies`
- [tests/test_placement_opening_probes.py](../../../../../../tests/test_placement_opening_probes.py) — direct import
- [tests/test_placement_unevidenced_return.py](../../../../../../tests/test_placement_unevidenced_return.py) — direct import
  - `test_a_returned_prerequisite_moves_its_dependents_one_layer_later`
- [tests/test_practice_information.py](../../../../../../tests/test_practice_information.py) — direct import
- [tests/test_probe_episodes.py](../../../../../../tests/test_probe_episodes.py) — direct import
  - `test_missing_instruments_park_episode_with_one_deduplicated_need`
  - `test_pending_items_episode_keeps_lo_schedulable_with_belief_updates`
  - `test_scheduler_slate_atomically_commits_its_selected_probe_presentation`
- [tests/test_probe_instance_generation.py](../../../../../../tests/test_probe_instance_generation.py) — direct import
  - `test_provisional_family_instances_park_behind_review`
- [tests/test_probe_llm_instances.py](../../../../../../tests/test_probe_llm_instances.py) — direct import
- [tests/test_probe_orchestration_remainder.py](../../../../../../tests/test_probe_orchestration_remainder.py) — direct import
  - `test_disagreement_between_claim_and_observed_evidence`
  - `test_stale_uncertainty_reprobe_after_configured_days`
  - `test_stale_uncertainty_respects_variance_floor`
- [tests/test_probe_pool_empty.py](../../../../../../tests/test_probe_pool_empty.py) — direct import
  - `test_maintenance_feed_sustains_and_auto_resolves_the_notice`
  - `test_never_authored_pool_is_distinguished_from_excluded_as_seen`
  - `test_notice_clears_when_a_fresh_surface_appears`
  - `test_pending_diagnostic_need_with_no_fresh_surface_raises_and_clears`
- [tests/test_probe_remint.py](../../../../../../tests/test_probe_remint.py) — direct import
  - `test_remediation_cold_pick_rejects_remint_as_same_surface_as_probe_group`
  - `test_remint_does_not_resolve_the_diagnostic_supply_need`
  - `test_remint_enters_ordinary_pool_and_probe_stays_out`
  - `test_remint_starts_with_fresh_fsrs_state`
  - `test_remint_surface_group_stays_probe_ineligible`
- [tests/test_probe_surface_mint.py](../../../../../../tests/test_probe_surface_mint.py) — direct import
  - `test_mint_refuses_a_surface_group_the_learner_has_seen`
  - `test_minted_surface_serves_through_the_probe_branch_and_is_single_use`
- [tests/test_probe_targeting.py](../../../../../../tests/test_probe_targeting.py) — direct import
  - `test_cause_set_diagnostic_selects_discriminating_instrument`
  - `test_embedded_evidence_suppresses_redundant_probe`
  - `test_incomplete_mapping_surfaces_as_a_machine_check_never_as_a_probe`
  - `test_integration_condition_probes_coordination_not_components`
- [tests/test_projection_evidence_polarity.py](../../../../../../tests/test_projection_evidence_polarity.py) — direct import
  - `test_p0_timeline_matches_banked_ledger_including_a6_supporting_credit`
- [tests/test_quick_check.py](../../../../../../tests/test_quick_check.py) — direct import
  - `test_quick_check_is_never_prompted`
- [tests/test_reader_recap_review.py](../../../../../../tests/test_reader_recap_review.py) — direct import
- [tests/test_reader_recap_review_r2.py](../../../../../../tests/test_reader_recap_review_r2.py) — direct import
  - `test_f1_r2_a_later_regrade_does_not_rewrite_the_credit_banked_before_the_cutoff`
  - `test_f1_r2_the_as_of_curve_ignores_gradings_recorded_after_the_cutoff`
- [tests/test_reader_recap_review_r3.py](../../../../../../tests/test_reader_recap_review_r3.py) — direct import
- [tests/test_rebuild_closed_row_answer.py](../../../../../../tests/test_rebuild_closed_row_answer.py) — direct import
  - `test_a_sibling_retired_after_the_last_answer_rebuilds_to_live`
  - `test_an_answer_after_a_sibling_was_retired_rebuilds_to_live`
- [tests/test_rebuild_equivalence.py](../../../../../../tests/test_rebuild_equivalence.py) — direct import
  - `test_a_full_sync_after_a_rebuild_keeps_retired_items_retired`
  - `test_a_retired_item_stays_inactive_through_a_primary_load_and_a_rebuild`
  - `test_a_second_learner_report_on_an_lo_after_an_attempt_rebuilds_to_live`
  - `test_content_sync_nests_inside_a_rebuild_transaction_and_rolls_back_with_it`
  - `test_random_attempt_histories_rebuild_to_live_state_exactly`
  - `test_random_histories_with_claims_after_attempts_and_too_easy_retirements_rebuild_to_live`
- [tests/test_rebuild_equivalence_review.py](../../../../../../tests/test_rebuild_equivalence_review.py) — direct import
- [tests/test_recall_coverage_interventions.py](../../../../../../tests/test_recall_coverage_interventions.py) — direct import
  - `test_bad_item_suspicion_uses_prior_snapshot_not_current_attempt_update`
  - `test_diagnostic_generation_stales_resolved_repeat_failure_need`
  - `test_dont_know_keeps_full_coverage_and_updates_facet_recall`
  - `test_facet_aliases_are_canonicalized_before_recall_updates`
  - `test_high_unfamiliar_probe_posterior_records_intervention_need`
  - `test_intervention_need_targets_failed_facet_not_whole_item`
  - `test_intervention_needs_canonicalize_target_facets_for_dedup`
  - `test_success_breaks_item_streak_before_a_later_failure`
  - `test_success_resets_repeat_failure_gate_and_coverage_is_not_failed`
- [tests/test_recurrence_commands.py](../../../../../../tests/test_recurrence_commands.py) — direct import
  - `test_a_failure_after_preparation_leaves_no_group_in_force`
  - `test_the_kill_switch_takes_effect_at_vault_open_with_groups_already_populated`
- [tests/test_recurrence_deferral.py](../../../../../../tests/test_recurrence_deferral.py) — direct import
- [tests/test_replay.py](../../../../../../tests/test_replay.py) — direct import
  - `test_compute_attempt_application_materializes_outputs_without_persisting`
  - `test_compute_attempt_application_uses_explicit_prior_snapshot`
  - `test_learning_object_replay_matches_live_state_and_is_idempotent`
  - `test_live_and_replay_drive_shared_apply_attempt_step`
  - `test_rebuild_derived_state_replays_attempt_logs`
  - `test_replay_preserves_targeted_error_attribution_facets`
- [tests/test_residual_diagnostics.py](../../../../../../tests/test_residual_diagnostics.py) — direct import
  - `test_positive_residual_dependence_flags_missing_factor`
- [tests/test_review_log.py](../../../../../../tests/test_review_log.py) — direct import
- [tests/test_ro5_picks.py](../../../../../../tests/test_ro5_picks.py) — direct import
- [tests/test_router_offer_log.py](../../../../../../tests/test_router_offer_log.py) — direct import
  - `test_placement_components_and_exclusions_are_in_the_candidate_set`
- [tests/test_router_probe_ties.py](../../../../../../tests/test_router_probe_ties.py) — direct import
  - `test_teach_back_items_are_probe_near_ties_at_the_successor`
  - `test_without_probe_candidates_the_successor_serves_exactly_as_mvp014`
- [tests/test_scoreboard.py](../../../../../../tests/test_scoreboard.py) — direct import
- [tests/test_shadow_components.py](../../../../../../tests/test_shadow_components.py) — direct import
  - `test_state_sync_retires_expired_telemetry_horizon`
- [tests/test_sidecar_close_cancels_jobs.py](../../../../../../tests/test_sidecar_close_cancels_jobs.py) — direct import
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_knowledge_field_is_recipe_topological_and_uses_pooled_ready`
- [tests/test_sidecar_knowledge_model.py](../../../../../../tests/test_sidecar_knowledge_model.py) — direct import
- [tests/test_sidecar_queue_serialization.py](../../../../../../tests/test_sidecar_queue_serialization.py) — direct import
  - `test_queue_serialization_bulk_loads_state_once`
- [tests/test_slate_record.py](../../../../../../tests/test_slate_record.py) — direct import
- [tests/test_sqlite_wal_lifecycle.py](../../../../../../tests/test_sqlite_wal_lifecycle.py) — direct import
  - `test_wal_stays_bounded_across_twenty_queue_builds_on_a_fixture_copy`
- [tests/test_staged_policy.py](../../../../../../tests/test_staged_policy.py) — direct import
- [tests/test_staged_policy_evsi.py](../../../../../../tests/test_staged_policy_evsi.py) — direct import
- [tests/test_staged_policy_short_session.py](../../../../../../tests/test_staged_policy_short_session.py) — direct import
- [tests/test_state_signals.py](../../../../../../tests/test_state_signals.py) — direct import
- [tests/test_state_sync.py](../../../../../../tests/test_state_sync.py) — direct import
  - `test_state_sync_enters_probe_for_new_active_goal_learning_object`
  - `test_state_sync_enters_probe_for_new_active_learning_object_without_goal`
  - `test_state_sync_enters_probe_when_practice_item_arrives_after_learning_object`
  - `test_state_sync_initializes_and_deactivates_missing_yaml`
  - `test_state_sync_no_probe_gap_for_item_less_goal_lo`
  - `test_state_sync_seeds_from_weak_learner_claim_below_probe_threshold`
  - `test_state_sync_uses_strong_learner_claim_for_initial_mastery`
- [tests/test_state_sync_scheduling_race.py](../../../../../../tests/test_state_sync_scheduling_race.py) — direct import
  - `test_a_measurement_correction_after_the_lifecycle_reads_keeps_the_original_retired`
  - `test_a_probe_attempt_after_the_fallback_read_stays_retired`
  - `test_a_stale_snapshot_never_reactivates_a_probe_an_attempt_retired`
  - `test_an_attempt_from_a_second_process_survives_a_concurrent_content_sync`
  - `test_content_change_sync_keeps_an_attempt_committed_after_its_snapshot`
  - `test_creating_sync_keeps_a_row_an_attempt_inserted_after_its_snapshot`
  - `test_deactivating_sync_keeps_an_attempt_committed_after_its_snapshot`
  - `test_review_parking_after_the_lifecycle_reads_keeps_the_item_inactive`
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — direct import
- [tests/test_success_head_cli.py](../../../../../../tests/test_success_head_cli.py) — direct import
  - `test_seen_stem_backfill_embeds_retired_and_earlier_texts_only_explicitly`
  - `test_without_vectors_the_embedding_arms_abstain_and_say_so`
- [tests/test_surfaced_belief_corrections.py](../../../../../../tests/test_surfaced_belief_corrections.py) — direct import
- [tests/test_teacher_te2_probes.py](../../../../../../tests/test_teacher_te2_probes.py) — direct import
  - `test_a_probe_is_generated_once_served_cold_and_never_again`
- [tests/test_today_headline.py](../../../../../../tests/test_today_headline.py) — direct import
  - `test_a_blueprint_lo_with_an_integration_gap_is_learning`
- [tests/test_unresolved_cause_gate.py](../../../../../../tests/test_unresolved_cause_gate.py) — direct import
- [tests/test_ux_phase2_error_type_proposals.py](../../../../../../tests/test_ux_phase2_error_type_proposals.py) — direct import
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1l_the_scheduler_never_commits_or_serves_a_covered_probe`
- [tests/test_voi_forecasts.py](../../../../../../tests/test_voi_forecasts.py) — direct import
- [tests/test_voi_stopping.py](../../../../../../tests/test_voi_stopping.py) — direct import
  - `test_a_served_probe_records_its_probability_over_the_composed_queue`
- [tests/test_voi_v2.py](../../../../../../tests/test_voi_v2.py) — direct import
- [tests/voi_restore_scenarios.py](../../../../../../tests/voi_restore_scenarios.py) — direct import
- [tests/voi_stopping_helpers.py](../../../../../../tests/voi_stopping_helpers.py) — direct import

## Modification guidance

- Change state sync policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/state_sync.py](../../../../../../src/learnloop/substrate/state_sync.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.vault.yaml_io"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/vault/yaml_io.py"
source_paths:
  - "src/learnloop/vault/yaml_io.py"
source_commit: "4b62bc29c46b5f2b8cabe5ac49c9959429cc3ab7"
source_commit_timestamp: "2026-05-19T19:15:00-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop.vault"
layer: "infrastructure"
concepts:
  - "State and Persistence"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.vault.yaml_io module"
  - "src/learnloop/vault/yaml_io.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-vault"
---

# `learnloop.vault.yaml_io`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps yaml io behavior inside its owning package, [[Reference/Modules/learnloop/vault/_package|learnloop.vault]]. Its public surface centers on `read_yaml`, `write_yaml`, `yaml_to_string`, `read_markdown_with_frontmatter`, `write_markdown_with_frontmatter`.

The authoritative system-level explanation remains in [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/vault/yaml_io.py](../../../../../../src/learnloop/vault/yaml_io.py) |
| Source lines | 61 |
| Owning package | [[Reference/Modules/learnloop/vault/_package|learnloop.vault]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `4b62bc29c46b5f2b8cabe5ac49c9959429cc3ab7` |
| Commit timestamp | `2026-05-19T19:15:00-04:00` |

## Public API

- `read_yaml(path: Path) -> dict[str, Any]` ([source](../../../../../../src/learnloop/vault/yaml_io.py), line 18)
- `write_yaml(path: Path, data: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/vault/yaml_io.py), line 27)
- `yaml_to_string(data: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/vault/yaml_io.py), line 34)
- `read_markdown_with_frontmatter(path: Path) -> tuple[dict[str, Any], str]` ([source](../../../../../../src/learnloop/vault/yaml_io.py), line 41)
- `write_markdown_with_frontmatter(path: Path, metadata: dict[str, Any], body: str) -> None` ([source](../../../../../../src/learnloop/vault/yaml_io.py), line 54)

## Internal implementation anchors

- `_yaml() -> YAML` ([source](../../../../../../src/learnloop/vault/yaml_io.py), line 10)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `read_yaml`; statically calls `read_yaml`
- [[Reference/Modules/learnloop/cli/calibration|learnloop.cli.calibration]] — imports `read_yaml`; statically calls `read_yaml`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `read_yaml`, `yaml_to_string`; statically calls `read_yaml`, `yaml_to_string`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `read_yaml`, `write_markdown_with_frontmatter`, `write_yaml`; statically calls `read_yaml`, `write_markdown_with_frontmatter`, `write_yaml`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `read_yaml`, `write_yaml`; statically calls `read_yaml`, `write_yaml`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_eval|learnloop.content.synthesis.synthesis_eval]] — imports `read_yaml`; statically calls `read_yaml`
- [[Reference/Modules/learnloop/curriculum/concepts|learnloop.curriculum.concepts]] — imports `read_markdown_with_frontmatter`, `read_yaml`, `write_markdown_with_frontmatter`, `write_yaml`; statically calls `read_markdown_with_frontmatter`, `read_yaml`, `write_markdown_with_frontmatter`, `write_yaml`
- [[Reference/Modules/learnloop/curriculum/golden_path_fixture|learnloop.curriculum.golden_path_fixture]] — imports `write_yaml`; statically calls `write_yaml`
- [[Reference/Modules/learnloop/curriculum/integration_backfill|learnloop.curriculum.integration_backfill]] — imports `read_yaml`, `write_yaml`, `yaml_to_string`; statically calls `read_yaml`, `write_yaml`, `yaml_to_string`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `read_yaml`, `write_yaml`; statically calls `read_yaml`, `write_yaml`
- [[Reference/Modules/learnloop/learner/learner_profile|learnloop.learner.learner_profile]] — imports `read_yaml`, `write_yaml`; statically calls `read_yaml`, `write_yaml`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `read_yaml`; statically calls `read_yaml`
- [[Reference/Modules/learnloop/sim/profiles|learnloop.sim.profiles]] — imports `read_yaml`; statically calls `read_yaml`
- [[Reference/Modules/learnloop/sim/sweep|learnloop.sim.sweep]] — imports `read_yaml`; statically calls `read_yaml`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `read_markdown_with_frontmatter`, `read_yaml`, `write_markdown_with_frontmatter`, `write_yaml`; statically calls `read_markdown_with_frontmatter`, `read_yaml`, `write_markdown_with_frontmatter`, `write_yaml`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `read_yaml`, `write_yaml`; statically calls `read_yaml`, `write_yaml`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `read_yaml`, `write_yaml`; statically calls `read_yaml`, `write_yaml`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `io`, `pathlib`, `typing`
- Third party: `ruamel`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cli/calibration|learnloop.cli.calibration]], [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] and 12 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/helpers.py](../../../../../../tests/helpers.py) — direct import
- [tests/test_assessment_contracts.py](../../../../../../tests/test_assessment_contracts.py) — direct import
  - `test_contract_hash_changes_when_targets_change`
  - `test_snapshot_authoritative_after_live_rubric_change`
- [tests/test_assessment_enforcement.py](../../../../../../tests/test_assessment_enforcement.py) — direct import
  - `test_detect_contract_drift_and_doctor_surface`
- [tests/test_authoring_context.py](../../../../../../tests/test_authoring_context.py) — direct import
  - `test_authoring_context_includes_blueprint_facets_before_items_exist`
- [tests/test_capability_residual.py](../../../../../../tests/test_capability_residual.py) — direct import
- [tests/test_causal_attribution_exhibit.py](../../../../../../tests/test_causal_attribution_exhibit.py) — direct import
- [tests/test_causal_factor_deferral.py](../../../../../../tests/test_causal_factor_deferral.py) — direct import
- [tests/test_causal_probe_commissioning.py](../../../../../../tests/test_causal_probe_commissioning.py) — direct import
- [tests/test_causal_shadow_selection.py](../../../../../../tests/test_causal_shadow_selection.py) — direct import
- [tests/test_certification_cold_probe.py](../../../../../../tests/test_certification_cold_probe.py) — direct import
  - `test_a_superseded_certificate_has_its_probe_cancelled_and_a_fresh_one_queued`
  - `test_probe_prefers_the_whole_task_item_that_covers_integration`
  - `test_shared_surface_group_makes_the_certificate_unmeasurable`
- [tests/test_characterization_assessment_exam.py](../../../../../../tests/test_characterization_assessment_exam.py) — direct import
  - `test_single_hash_moves_when_any_covered_component_changes`
- [tests/test_cli_attempt.py](../../../../../../tests/test_cli_attempt.py) — direct import
  - `test_cli_attempt_defaults_to_allowed_open_text_attempt_type`
- [tests/test_common_repair_delivery.py](../../../../../../tests/test_common_repair_delivery.py) — direct import
- [tests/test_concepts.py](../../../../../../tests/test_concepts.py) — direct import
  - `test_merge_concepts_rewrites_vault_references`
- [tests/test_conjunctive_instruments.py](../../../../../../tests/test_conjunctive_instruments.py) — direct import
- [tests/test_contract_commissioning.py](../../../../../../tests/test_contract_commissioning.py) — direct import
  - `test_authoring_at_the_contract_capability_makes_the_cell_reachable`
  - `test_max_los_truncates_by_queue_priority`
  - `test_unrubricked_item_is_not_scored_as_a_miss`
- [tests/test_contract_frontier_coverage.py](../../../../../../tests/test_contract_frontier_coverage.py) — direct import
- [tests/test_contract_reachability.py](../../../../../../tests/test_contract_reachability.py) — direct import
  - `test_recipe_duplicate_cells_collapse_to_one_obligation`
  - `test_retired_items_are_not_instruments`
  - `test_unrubricked_items_are_counted_not_silently_dropped`
- [tests/test_contrast_pairs.py](../../../../../../tests/test_contrast_pairs.py) — direct import
  - `test_the_doctor_catches_a_one_sided_pair_binding`
- [tests/test_coverage_denominator_boundary.py](../../../../../../tests/test_coverage_denominator_boundary.py) — direct import
  - `test_a_comment_or_timestamp_touch_does_not_change_the_version`
- [tests/test_curriculum_locks.py](../../../../../../tests/test_curriculum_locks.py) — direct import
  - `test_deactivate_locked_learning_object_is_invalid`
  - `test_locked_facet_refuses_merge_on_independent_mass`
  - `test_locked_facet_refuses_merge_on_surface_groups`
  - `test_locked_semantic_merge_is_invalid`
  - `test_prelock_facet_with_single_surface_group_still_mergeable`
  - `test_unlocked_facet_merge_is_legal_with_review`
- [tests/test_deferred_regrade.py](../../../../../../tests/test_deferred_regrade.py) — direct import
  - `test_deferred_regrade_replays_targeted_error_attribution_facets`
- [tests/test_diagnostic_probe_single_use.py](../../../../../../tests/test_diagnostic_probe_single_use.py) — direct import
- [tests/test_discrimination_profiles.py](../../../../../../tests/test_discrimination_profiles.py) — direct import
- [tests/test_doctor.py](../../../../../../tests/test_doctor.py) — direct import
  - `test_doctor_does_not_merge_opposite_registered_facet_contracts`
  - `test_doctor_does_not_merge_unrelated_equal_length_facet_ids`
  - `test_doctor_fix_state_merges_registered_facet_alias_state`
  - `test_doctor_reports_reference_issues_and_json_cli`
  - `test_doctor_resolves_legacy_error_event_through_causal_taxonomy`
  - `test_doctor_surfaces_likely_facet_merge_candidates`
  - `test_doctor_validates_criterion_facet_maps`
  - `test_doctor_warns_on_duplicate_learning_objects`
  - `test_doctor_warns_on_unknown_yaml_key_that_looks_like_typo`
- [tests/test_error_hunt_items.py](../../../../../../tests/test_error_hunt_items.py) — direct import
- [tests/test_exercise_authoring.py](../../../../../../tests/test_exercise_authoring.py) — direct import
- [tests/test_facet_mint_gate.py](../../../../../../tests/test_facet_mint_gate.py) — direct import
  - `test_ingest_aliases_a_collapsing_candidate_into_a_registered_facet`
- [tests/test_facet_registry_v2.py](../../../../../../tests/test_facet_registry_v2.py) — direct import
  - `test_upsert_facet_promotes_v1_registry_to_v2`
- [tests/test_goal_certification_any_of.py](../../../../../../tests/test_goal_certification_any_of.py) — direct import
- [tests/test_goal_frontier.py](../../../../../../tests/test_goal_frontier.py) — direct import
  - `test_no_active_goals_means_no_goal_frontier`
- [tests/test_goal_projection.py](../../../../../../tests/test_goal_projection.py) — direct import
  - `test_explicit_facet_scope_adds_facet_without_listing_concept`
  - `test_legacy_v1_goal_converts_and_scope_resolves`
- [tests/test_goal_scope_material.py](../../../../../../tests/test_goal_scope_material.py) — direct import
- [tests/test_grading_context.py](../../../../../../tests/test_grading_context.py) — direct import
  - `test_grading_context_uses_default_rubric_when_inline_rubric_is_omitted`
  - `test_legacy_evidence_coverage_wrapper_is_score_independent`
- [tests/test_graph_correction.py](../../../../../../tests/test_graph_correction.py) — direct import
- [tests/test_graph_edit_proposals.py](../../../../../../tests/test_graph_edit_proposals.py) — direct import
  - `test_queue_restructure_request_requires_a_locked_facet`
- [tests/test_identifiability_doctor.py](../../../../../../tests/test_identifiability_doctor.py) — direct import
- [tests/test_inference_precheck.py](../../../../../../tests/test_inference_precheck.py) — direct import
  - `test_b3_requires_a_directly_reachable_downstream_anchor`
- [tests/test_init.py](../../../../../../tests/test_init.py) — direct import
  - `test_bootstrap_seeds_subject_and_starting_level`
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_the_certification_cold_probe_selects_an_instrument_as_its_held_out_item`
- [tests/test_integration_backfill.py](../../../../../../tests/test_integration_backfill.py) — direct import
  - `test_apply_writes_a_drop_as_an_explicit_null`
  - `test_coordination_becomes_keepable_once_an_instrument_observes_it`
- [tests/test_km1_doctor.py](../../../../../../tests/test_km1_doctor.py) — direct import
  - `test_blueprint_invalid_capability_rejected`
  - `test_criterion_dependency_cycle_rejected`
  - `test_valid_blueprint_and_criterion_targets_pass`
- [tests/test_km2_activation.py](../../../../../../tests/test_km2_activation.py) — direct import
  - `test_validate_readiness_flags_incomplete_contract`
- [tests/test_km2_write_path.py](../../../../../../tests/test_km2_write_path.py) — direct import
  - `test_rebuild_uses_presented_contract_after_live_target_change`
- [tests/test_km3_projections.py](../../../../../../tests/test_km3_projections.py) — direct import
- [tests/test_km5_sim_gates.py](../../../../../../tests/test_km5_sim_gates.py) — direct import
  - `test_shadow_intent_logs_practice_integration_at_the_right_moment`
- [tests/test_laddered_stems.py](../../../../../../tests/test_laddered_stems.py) — direct import
- [tests/test_large_practice_flow.py](../../../../../../tests/test_large_practice_flow.py) — direct import
  - `test_many_open_text_practice_items_schedule_and_record_attempt`
- [tests/test_minimal_repair_selection_a1.py](../../../../../../tests/test_minimal_repair_selection_a1.py) — direct import
- [tests/test_persona_gate.py](../../../../../../tests/test_persona_gate.py) — direct import
- [tests/test_probe_targeting.py](../../../../../../tests/test_probe_targeting.py) — direct import
- [tests/test_projection_evidence_polarity.py](../../../../../../tests/test_projection_evidence_polarity.py) — direct import
  - `test_p0_timeline_matches_banked_ledger_including_a6_supporting_credit`
- [tests/test_proposal_persistence.py](../../../../../../tests/test_proposal_persistence.py) — direct import
  - `test_registry_backed_vault_rejects_unknown_evidence_facet`
- [tests/test_reader_progression.py](../../../../../../tests/test_reader_progression.py) — direct import
  - `test_practice_plan_uses_blueprint_facets_before_first_item`
- [tests/test_recall_coverage_interventions.py](../../../../../../tests/test_recall_coverage_interventions.py) — direct import
  - `test_error_attribution_target_facets_are_canonicalized_before_facet_outcomes`
  - `test_error_attribution_targets_unmapped_facet_before_whole_item_fallback`
  - `test_facet_aliases_are_canonicalized_before_recall_updates`
  - `test_intervention_need_targets_failed_facet_not_whole_item`
  - `test_intervention_needs_canonicalize_target_facets_for_dedup`
  - `test_rubric_criterion_names_infer_targeted_facet_outcomes`
  - `test_second_same_facet_failure_counts_across_different_items`
  - `test_zero_score_independent_attempt_uses_rubric_coverage_and_confidence_as_reliability`
- [tests/test_replay.py](../../../../../../tests/test_replay.py) — direct import
  - `test_replay_preserves_targeted_error_attribution_facets`
- [tests/test_scheduler.py](../../../../../../tests/test_scheduler.py) — direct import
  - `test_scheduler_orders_eligible_items_by_selection_reward_before_id`
  - `test_scheduler_persists_bounded_reward_debug_and_rejected_candidates`
  - `test_scheduler_persists_selection_propensity_and_exploration_flag`
  - `test_scheduler_scores_due_goal_item`
  - `test_scheduler_selects_item_on_weak_canonical_facet_boundary`
- [tests/test_scheduler_golden.py](../../../../../../tests/test_scheduler_golden.py) — direct import
  - `test_scheduler_forgetting_risk_zero_before_due_date`
  - `test_scheduler_goal_frontier_follows_explicit_scope_only`
  - `test_scheduler_recent_error_decays_by_exp_days_over_seven`
- [tests/test_scheduler_probe_eig.py](../../../../../../tests/test_scheduler_probe_eig.py) — direct import
  - `test_short_session_keeps_probe_eig_when_probe_is_only_reason`
- [tests/test_scheduler_requested_floor.py](../../../../../../tests/test_scheduler_requested_floor.py) — direct import
- [tests/test_scoreboard.py](../../../../../../tests/test_scoreboard.py) — direct import
- [tests/test_self_attributed_misconceptions.py](../../../../../../tests/test_self_attributed_misconceptions.py) — direct import
- [tests/test_self_grade.py](../../../../../../tests/test_self_grade.py) — direct import
  - `test_dont_know_allowed_when_not_in_attempt_types`
  - `test_self_grade_uses_criterion_total_as_item_scale`
  - `test_self_grade_uses_default_rubric_when_inline_rubric_is_omitted`
- [tests/test_show.py](../../../../../../tests/test_show.py) — direct import
  - `test_show_adds_imported_source_name_without_replacing_ref_id`
- [tests/test_sidecar_item_presentation.py](../../../../../../tests/test_sidecar_item_presentation.py) — direct import
  - `test_rubric_criteria_expose_their_authored_targets_and_dependencies`
- [tests/test_sidecar_trace_and_clarification.py](../../../../../../tests/test_sidecar_trace_and_clarification.py) — direct import
- [tests/test_sim_teach_back.py](../../../../../../tests/test_sim_teach_back.py) — direct import
- [tests/test_simulation.py](../../../../../../tests/test_simulation.py) — direct import
- [tests/test_source_set_synthesis.py](../../../../../../tests/test_source_set_synthesis.py) — direct import
  - `test_locked_subject_bootstrap_refusal`
- [tests/test_state_sync.py](../../../../../../tests/test_state_sync.py) — direct import
  - `test_state_sync_enters_probe_for_new_active_learning_object_without_goal`
  - `test_state_sync_enters_probe_when_practice_item_arrives_after_learning_object`
- [tests/test_synthesis_manifests.py](../../../../../../tests/test_synthesis_manifests.py) — direct import
  - `test_curriculum_change_changes_manifest_hash`
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_ensure_teach_back_item_authors_from_exact_source_and_active_quest`
- [tests/test_vault_writer.py](../../../../../../tests/test_vault_writer.py) — direct import
  - `test_writer_preserves_unknown_keys_and_timestamps`

## Modification guidance

- Make changes here when the responsibility remains yaml io within learnloop.vault; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/vault/yaml_io.py](../../../../../../src/learnloop/vault/yaml_io.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

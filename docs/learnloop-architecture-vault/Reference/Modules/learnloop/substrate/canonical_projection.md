---
title: "learnloop.substrate.canonical_projection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/canonical_projection.py"
source_paths:
  - "src/learnloop/substrate/canonical_projection.py"
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
  - "learnloop.substrate.canonical_projection module"
  - "src/learnloop/substrate/canonical_projection.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.canonical_projection`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.canonical_projection` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: KM2 canonical belief projection (§5.3/§5.4/§6/§7.1).

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/canonical_projection.py](../../../../../../src/learnloop/substrate/canonical_projection.py) |
| Source lines | 1328 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `p0_effective_evidence_mass(repository: Repository, *, interpretation: Mapping[str, Any] | None, attempt_type_mass: float, references: EffectiveObservationReferences | None=None) -> float` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 169) — THE mvp-0.8 response-level evidence-mass discount (P0.3 §4.3), shared by both evidence folds.
- `surface_group_id(item: PracticeItem) -> str` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 212) — The correlation/surface group an item's evidence belongs to (§6).
- `class CanonicalProjectionSnapshot` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 273) — Bulk-loaded, immutable inputs for one canonical evidence replay.
- `load_canonical_projection_snapshot(repository: Repository, *, algorithm_version: str) -> CanonicalProjectionSnapshot` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 289) — Read replay inputs once, before the pure attempt fold begins.
- `attribution_weights(raw: object, targets: list[CriterionTarget]) -> dict[tuple[str, str], float]` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 410) — Normalize persisted failure attribution over the criterion targets.
- `observed_unresolved_failure(observed_fraction: float, targets: Sequence[CriterionTarget], attribution: Mapping[tuple[str, str], float]) -> bool` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 440) — True when an OBSERVED failure has multiple candidate causes and no resolving attribution (§5.3) — the condition that opens an unresolved-cause factor.
- `configured_repeat_discount(vault: LoadedVault) -> float` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 605)
- `project_canonical_facet_state(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None, refresh_factor_candidates_for: Collection[str] | None=None, before: tuple[str, str] | None=None, through: tuple[str, str] | None=None) -> None` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 613) — Recompute and persist the canonical belief cache.
- `project_capability_residuals(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 1140) — Derive lazy capability-residual activation state (§4.2, KM5; DEFAULT OFF).

### Module constants

- `FAILURE_THRESHOLD` ([src/learnloop/substrate/canonical_projection.py](../../../../../../src/learnloop/substrate/canonical_projection.py), line 57)
- `DEFAULT_REPEAT_SURFACE_DISCOUNT` ([src/learnloop/substrate/canonical_projection.py](../../../../../../src/learnloop/substrate/canonical_projection.py), line 62)
- `ASSISTED_ATTEMPT_TYPES` ([src/learnloop/substrate/canonical_projection.py](../../../../../../src/learnloop/substrate/canonical_projection.py), line 114)
- `CANONICAL_PROJECTION_VERSION` ([src/learnloop/substrate/canonical_projection.py](../../../../../../src/learnloop/substrate/canonical_projection.py), line 166)

## Internal implementation anchors

- `class _RecallAcc` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 234)
- `class _CapAcc` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 246)
- `class _HistoricalCriterion` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 264)
- `_contract_unrecorded(repository: Repository) -> frozenset[str]` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 341)
- `_historical_contract(evidence: list[dict[str, Any]], *, contracts_by_source_version: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 348) — Resolve the immutable assessment contract attached to this grading.
- `_contract_criteria(contract: Mapping[str, Any]) -> list[_HistoricalCriterion]` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 373)
- `_contract_surface_group(contract: Mapping[str, Any], practice_item_id: str) -> str` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 400)
- `_target_ref_key(target_ref: Any) -> str` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 459) — Identity of a candidate cause's declared target, for union de-duplication.
- `_facet_target_cause(target: CriterionTarget) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 475) — One synthesized open-world arm for a criterion target.
- `_open_candidate_causes(error_events: Sequence[Mapping[str, Any]], targets: Sequence[CriterionTarget]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 500) — Thin candidate set for an unresolved factor, always open-world.
- `_adjudicated_score_fraction(adjudication: Mapping[str, Any] | None, interpretation: Mapping[str, Any] | None, score_fraction: Mapping[str, float]) -> float | None` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 569) — Observed-outcome override when an adjudication heads the interpretation chain.
- `_ledger_position_within(row: Mapping[str, Any], bound: tuple[str, str], *, inclusive: bool) -> bool` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 1127) — Whether a ledger row lies before (or, inclusive, at) ``bound``.
- `_sync_unresolved_cause_factors(repository: Repository, unresolved: list[dict[str, object]], *, clock: Clock | None, refresh_attempt_ids: Collection[str] | None=None, retire_within_attempt_ids: Collection[str] | None=None) -> None` ([source](../../../../../../src/learnloop/substrate/canonical_projection.py), line 1265) — Idempotently reconcile open unresolved-cause factors with the projection.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempt_trace|learnloop.attempts.attempt_trace]] — imports `FAILURE_THRESHOLD`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `UNASSESSED_INTERPRETATION`, `UNVERIFIED_CRITERION_BLOCK`, `UNVERIFIED_INTERPRETATION_KEY`, `project_canonical_facet_state`, `unassessed_evidence_row`; statically calls `project_canonical_facet_state`, `unassessed_evidence_row`
- [[Reference/Modules/learnloop/attempts/coldness_receipt|learnloop.attempts.coldness_receipt]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]] — imports `UNASSESSED_INTERPRETATION`, `UNVERIFIED_CRITERION_BLOCK`, `UNVERIFIED_INTERPRETATION_KEY`, `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]] — imports `CANONICAL_PROJECTION_VERSION`, `project_canonical_facet_state`; statically calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/curriculum/integration_backfill|learnloop.curriculum.integration_backfill]] — imports `CANONICAL_PROJECTION_VERSION`
- [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]] — imports `held_for_review_attempts`, `pfc_assessments`; statically calls `held_for_review_attempts`, `pfc_assessments`
- [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `surface_group_id`, `unassessed_evidence_row`; statically calls `surface_group_id`, `unassessed_evidence_row`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `surface_group_id`, `unassessed_evidence_row`; statically calls `surface_group_id`, `unassessed_evidence_row`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/diagnosis/guided_redo|learnloop.diagnosis.guided_redo]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/diagnosis/offline_review/planted|learnloop.diagnosis.offline_review.planted]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/diagnosis/split/context|learnloop.diagnosis.split.context]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `UNVERIFIED_CRITERION_BLOCK`, `held_for_review_attempts`, `surface_group_id`, `unverified_evidence_row`; statically calls `held_for_review_attempts`, `surface_group_id`, `unverified_evidence_row`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `project_canonical_facet_state`; statically calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]] — imports `held_for_review_attempts`; statically calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/evsi_calibration/live_report|learnloop.evsi_calibration.live_report]] — imports `held_for_review_attempts`, `unassessed_evidence_row`; statically calls `held_for_review_attempts`, `unassessed_evidence_row`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `UNVERIFIED_CRITERION_BLOCK`, `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `DEFAULT_REPEAT_SURFACE_DISCOUNT`, `FAILURE_THRESHOLD`, `attribution_weights`, `configured_repeat_discount`, `observed_unresolved_failure`, `p0_effective_evidence_mass`, `surface_group_id`, `unassessed_evidence_row`; statically calls `attribution_weights`, `configured_repeat_discount`, `observed_unresolved_failure`, `p0_effective_evidence_mass`, `surface_group_id`, `unassessed_evidence_row`
- [[Reference/Modules/learnloop/learner/independence_audit|learnloop.learner.independence_audit]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/learner/residual_diagnostics|learnloop.learner.residual_diagnostics]] — imports `FAILURE_THRESHOLD`, `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/ops/pf_publish|learnloop.ops.pf_publish]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `project_canonical_facet_state`; statically calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/scheduling/evaluation|learnloop.scheduling.evaluation]] — imports `pfc_assessments`; statically calls `pfc_assessments`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `surface_group_id`; statically calls `surface_group_id`
- [[Reference/Modules/learnloop/substrate/canonical_projection_rollout|learnloop.substrate.canonical_projection_rollout]] — imports `CANONICAL_PROJECTION_VERSION`, `project_canonical_facet_state`; statically calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/substrate/data_quality|learnloop.substrate.data_quality]] — imports `pfc_assessments`; statically calls `pfc_assessments`
- [[Reference/Modules/learnloop/substrate/dataset|learnloop.substrate.dataset]] — imports `pfc_assessments`; statically calls `pfc_assessments`
- [[Reference/Modules/learnloop/substrate/p0_projection|learnloop.substrate.p0_projection]] — imports `CANONICAL_PROJECTION_VERSION`, `project_canonical_facet_state`; statically calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `CANONICAL_PROJECTION_VERSION`, `held_for_review_attempts`, `pfc_assessments`, `project_canonical_facet_state`; statically calls `held_for_review_attempts`, `pfc_assessments`, `project_canonical_facet_state`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `CANONICAL_PROJECTION_VERSION`, `project_canonical_facet_state`; statically calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `unassessed_evidence_row`; statically calls `unassessed_evidence_row`
- [[Reference/Modules/learnloop/why/outcomes_now|learnloop.why.outcomes_now]] — imports `held_for_review_attempts`, `pfc_assessments`; statically calls `held_for_review_attempts`, `pfc_assessments`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `unassessed_evidence_row`; statically calls `unassessed_evidence_row`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `REGRADE_CONTRACT_VERSIONS`
- [[Reference/Modules/learnloop/attempts/effective_observation|learnloop.attempts.effective_observation]] — imports `EffectiveObservationReferences`, `build_effective_observation`, `load_effective_observation_references`; calls `build_effective_observation`, `load_effective_observation_references`
- [[Reference/Modules/learnloop/attempts/evidence|learnloop.attempts.evidence]] — imports `attempt_evidence_mass`; calls `attempt_evidence_mass`
- [[Reference/Modules/learnloop/attempts/outcome_schemas|learnloop.attempts.outcome_schemas]] — imports `COARSE_RESPONSE_SLUG`, `ensure_builtin_schemas`; calls `ensure_builtin_schemas`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/authoring/conjunctive_items|learnloop.content.authoring.conjunctive_items]] — imports `cap_embedded_credit`, `supporting_unexercised`; calls `cap_embedded_credit`, `supporting_unexercised`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] — imports `ASSISTED_ATTEMPT_TYPES`, `resolve_attempt_activity_policy`; calls `resolve_attempt_activity_policy`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `OPEN_SET_CAUSE_ID`
- [[Reference/Modules/learnloop/goals/receipt_contributions|learnloop.goals.receipt_contributions]] — imports `itemize_observation_contributions`; calls `itemize_observation_contributions`
- [[Reference/Modules/learnloop/grading_epochs|learnloop.grading_epochs]] — imports `current_epoch`; calls `current_epoch`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `contract_unrecorded_attempts`, `held_for_review_attempts`, `pfc_assessments`; calls `contract_unrecorded_attempts`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `CANONICAL_STATE_VERSIONS`, `KM_ALGORITHM_VERSION`, `P0_PROJECTION_VERSIONS`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `CriterionOutcome`, `allocate_success_mass`, `certification_credit`, `compile_criterion_targets`, `criterion_pseudo_mass`, `localize_criterion_outcomes`; calls `CriterionOutcome`, `allocate_success_mass`, `certification_credit`, `compile_criterion_targets`, `criterion_pseudo_mass`, `localize_criterion_outcomes`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `UNASSESSED_INTERPRETATION`, `UNVERIFIED_CRITERION_BLOCK`, `UNVERIFIED_INTERPRETATION_KEY`, `unassessed_evidence_row`, `unverified_evidence_row`; calls `unassessed_evidence_row`, `unverified_evidence_row`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `CriterionTarget`, `LoadedVault`, `PracticeItem`; calls `CriterionTarget`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempt_trace|learnloop.attempts.attempt_trace]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/coldness_receipt|learnloop.attempts.coldness_receipt]], [[Reference/Modules/learnloop/attempts/grading_support|learnloop.attempts.grading_support]], [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]] and 38 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/held_grade_evidence_helpers.py](../../../../../../tests/held_grade_evidence_helpers.py) — direct import
- [tests/pfc_unassessed_readers_helpers.py](../../../../../../tests/pfc_unassessed_readers_helpers.py) — direct import
- [tests/test_ad2_model.py](../../../../../../tests/test_ad2_model.py) — direct import
  - `test_surface_group_mirrors_the_projection`
- [tests/test_anti_double_count.py](../../../../../../tests/test_anti_double_count.py) — direct import
  - `test_anti_double_count_claim_seeds_prior_but_earns_no_mass`
  - `test_anti_double_count_observation_attaches_once`
  - `test_anti_double_count_projection_deterministic_and_idempotent`
  - `test_anti_double_count_projection_signal_earns_zero_certification`
- [tests/test_canonical_projection_fold_skip.py](../../../../../../tests/test_canonical_projection_fold_skip.py) — direct import
  - `test_a_noop_refresh_skips_the_fold_and_commits_nothing`
  - `test_the_fold_reads_no_vault_field_its_fingerprint_leaves_out`
- [tests/test_canonical_projection_rollout.py](../../../../../../tests/test_canonical_projection_rollout.py) — direct import
  - `test_fresh_startup_stamps_a_silent_projection_baseline_once`
  - `test_projection_upgrade_stays_silent_while_vault_has_no_attempts`
  - `test_startup_records_one_recalibration_for_an_unstamped_practised_vault`
- [tests/test_causal_activity_policy.py](../../../../../../tests/test_causal_activity_policy.py) — direct import
  - `test_near_clone_is_a_fingerprint_comparison_not_provenance`
  - `test_rebuild_records_the_current_projection_version`
- [tests/test_causal_factor_deferral.py](../../../../../../tests/test_causal_factor_deferral.py) — direct import
  - `test_projection_sync_does_not_resurrect_deferral_closed_factors`
- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_projection_bulk_loads_candidate_cause_error_events_once`
  - `test_projection_version_names_the_open_cause_union`
- [tests/test_characterization_certification_ledger.py](../../../../../../tests/test_characterization_certification_ledger.py) — direct import
  - `test_projection_mass_identical_across_grader_confidence`
  - `test_regrade_of_grading_evidence_changes_projection`
- [tests/test_conjunctive_instruments.py](../../../../../../tests/test_conjunctive_instruments.py) — direct import
  - `test_a_merged_facet_does_not_desynchronise_the_two_folds`
  - `test_a_trace_row_for_a_different_facet_does_not_license_the_supporting_target`
  - `test_an_exercised_supporting_target_does_make_the_failure_ambiguous`
  - `test_an_unexercised_supporting_target_costs_its_criterion_no_measurement`
  - `test_an_unexercised_supporting_target_takes_no_blame_when_its_own_step_fails`
  - `test_failure_at_step_one_leaves_later_steps_unassessed_not_failed`
  - `test_failure_at_step_three_indicts_only_the_diverged_facet`
  - `test_full_pass_credits_every_primary_cell_and_banks_unexercised_supporting_mass`
  - `test_guard_1_holds_in_the_receipt_fold_as_well_as_the_projection`
  - `test_the_configured_share_is_the_ledgers_cap_and_one_point_zero_disables_it`
  - `test_the_projection_version_pins_the_current_replay_semantics`
  - `test_trace_evidence_report_surfaces_unexercised_cells_and_abstains_on_concentration`
  - `test_trace_evidence_turns_the_supporting_target_into_embedded_credit`
- [tests/test_error_hunt_items.py](../../../../../../tests/test_error_hunt_items.py) — direct import
  - `test_clean_solution_false_positive_writes_a_candidate_not_a_facet_failure`
- [tests/test_facet_identity_actions.py](../../../../../../tests/test_facet_identity_actions.py) — direct import
- [tests/test_facet_state_write_on_change.py](../../../../../../tests/test_facet_state_write_on_change.py) — direct import
  - `test_a_new_attempt_moves_updated_at_only_on_the_cells_it_changed`
  - `test_capability_rows_keep_their_created_at_across_projections`
- [tests/test_field_split_outcomes.py](../../../../../../tests/test_field_split_outcomes.py) — direct import
  - `test_an_attempt_with_only_unverified_criteria_has_no_outcome_row`
- [tests/test_grading_cli.py](../../../../../../tests/test_grading_cli.py) — direct import
  - `test_retire_surface_from_cli_preserves_evidence_and_logs_reason`
- [tests/test_grading_support.py](../../../../../../tests/test_grading_support.py) — direct import
  - `test_an_unverified_criterion_writes_no_negative_evidence_even_without_an_attribution`
- [tests/test_held_grade_composition.py](../../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_a_released_hold_is_an_ordinary_outcome_again`
- [tests/test_held_grade_evidence.py](../../../../../../tests/test_held_grade_evidence.py) — direct import
  - `test_f2_a_regrade_that_validates_nothing_keeps_the_hold`
  - `test_f4_a_validating_regrade_leaves_no_stale_unassessed_row`
  - `test_review_f1_a_regrade_into_a_hold_supersedes_the_assessed_grade_it_replaces`
  - `test_the_predicate_is_the_record_and_the_current_evidence`
- [tests/test_independent_group_counting.py](../../../../../../tests/test_independent_group_counting.py) — direct import
  - `test_a_shared_stimulus_outranks_differing_authored_family_names`
  - `test_exam_practiced_surfaces_are_groups`
  - `test_genuinely_unrelated_items_stay_distinct`
- [tests/test_measurement_corrections.py](../../../../../../tests/test_measurement_corrections.py) — direct import
  - `test_attempted_item_correction_is_append_only_and_projection_versioned`
- [tests/test_observation_ledger_bulk.py](../../../../../../tests/test_observation_ledger_bulk.py) — direct import
  - `test_canonical_projection_bulk_loads_historical_contracts_once`
  - `test_p0_replays_bulk_load_calibration_references_once`
  - `test_primed_provenance_reaches_projection_and_blocks_certification`
  - `test_pure_diagnostic_is_unassisted_but_cannot_bank_certification`
  - `test_recorded_near_clone_disqualification_survives_both_replays`
- [tests/test_p0_projection_cutover.py](../../../../../../tests/test_p0_projection_cutover.py) — direct import
  - `test_activation_records_derived_state_rebuild`
  - `test_adjudicating_up_raises_credit_and_unchanged_direction_skips`
  - `test_adjudication_reverses_projection_and_preserves_history`
  - `test_ruling_a_superseded_rows_inert_nonsuperseded_rows_authoritative`
- [tests/test_pfc_unassessed_readers.py](../../../../../../tests/test_pfc_unassessed_readers.py) — direct import
  - `test_a_cold_retry_with_nothing_assessed_neither_confirms_nor_fails_the_repair`
  - `test_a_record_written_before_the_rule_keeps_its_interpretation_until_regraded`
  - `test_a_separate_review_concern_survives_the_pfc_flag`
  - `test_an_ordinary_item_gives_the_unverified_criterion_s_facet_nothing`
- [tests/test_pfc_unverified_unassessed.py](../../../../../../tests/test_pfc_unverified_unassessed.py) — direct import
  - `test_a_complement_route_is_graded_on_its_assessed_criteria_only`
  - `test_a_regrade_applies_the_same_rule`
  - `test_an_attempt_with_no_assessed_criterion_schedules_as_correct_and_is_no_evidence`
  - `test_field_projection_and_timeline_read_unverified_criteria_the_same_way`
  - `test_joint_fixture_replays_through_the_unchanged_path`
  - `test_joint_grades_replay_untouched_beside_blind_unverified_ones`
  - `test_the_stamped_block_is_read_from_text_or_mapping`
- [tests/test_placement_split_grades.py](../../../../../../tests/test_placement_split_grades.py) — direct import
  - `test_the_pinned_block_reason_is_pfcs`
- [tests/test_post_attempt_worker.py](../../../../../../tests/test_post_attempt_worker.py) — direct import
  - `test_a_submission_committed_while_the_worker_projects_is_never_overwritten`
- [tests/test_probe_remint.py](../../../../../../tests/test_probe_remint.py) — direct import
  - `test_remint_creates_ordinary_copy_and_probe_stays_retired`
  - `test_remint_surface_group_stays_probe_ineligible`
- [tests/test_probe_surface_mint.py](../../../../../../tests/test_probe_surface_mint.py) — direct import
  - `test_mint_refuses_a_surface_group_the_learner_has_seen`
- [tests/test_projection_evidence_polarity.py](../../../../../../tests/test_projection_evidence_polarity.py) — direct import
  - `test_missing_evidence_rows_bank_nothing`
  - `test_p0_timeline_matches_banked_ledger_including_a6_supporting_credit`
  - `test_partially_graded_attempt_credits_only_the_graded_criterion`
- [tests/test_reader_recap_review_r2.py](../../../../../../tests/test_reader_recap_review_r2.py) — direct import
  - `test_f1_r2_a_later_regrade_does_not_rewrite_the_credit_banked_before_the_cutoff`
- [tests/test_rebuild_equivalence.py](../../../../../../tests/test_rebuild_equivalence.py) — direct import
  - `test_a_bounded_fold_equals_the_fold_live_left_and_reconciles_no_factor`
- [tests/test_receipt_derivation.py](../../../../../../tests/test_receipt_derivation.py) — direct import
  - `test_per_observation_itemization_sums_to_banked_credit`
  - `test_ready_derivation_matches_canonical_recall_slices`
- [tests/test_receipt_exactness.py](../../../../../../tests/test_receipt_exactness.py) — direct import
  - `test_from_scratch_fold_equals_incremental_fold_on_real_history`
  - `test_timeline_final_credit_equals_banked_ledger_credit`
- [tests/test_reference_gate_imports.py](../../../../../../tests/test_reference_gate_imports.py) — direct import
  - `test_the_projection_reads_the_recorded_status_on_replay`
  - `test_the_regraded_grade_is_gated_live_and_on_rebuild`
- [tests/test_required_method_grading.py](../../../../../../tests/test_required_method_grading.py) — direct import
  - `test_a_regrade_grades_the_statement_and_rubric_its_method_was_frozen_with`
  - `test_a_regrade_never_acquires_a_required_method_added_after_the_answer`
  - `test_grades_recorded_at_the_predecessor_replay_unchanged_after_the_upgrade`
  - `test_live_another_route_fails_the_method_criterion_with_no_quote`
  - `test_live_the_same_mathematics_without_a_required_method_keeps_mvp020s_rule`
  - `test_replay_reproduces_method_grades_without_a_model`
- [tests/test_route_rules_in_grader.py](../../../../../../tests/test_route_rules_in_grader.py) — direct import
  - `test_f2_live_declared_uncertainty_on_a_quoted_step_is_unassessed`
  - `test_f3_live_a_clarification_regrade_keeps_an_error_the_reply_reveals`
  - `test_live_a_wrong_final_answer_is_never_unassessed`
  - `test_live_an_unlocated_mark_down_on_a_divergent_route_is_unassessed`
  - `test_live_nothing_located_and_nothing_validated_is_held`
  - `test_replay_reproduces_ruled_grades_without_a_model`
- [tests/test_stuck_prompt_composition.py](../../../../../../tests/test_stuck_prompt_composition.py) — direct import
  - `test_a_stuck_answers_pfc_unverified_criteria_are_unassessed`
- [tests/test_unresolved_cause_gate.py](../../../../../../tests/test_unresolved_cause_gate.py) — direct import
  - `test_adjudicated_failure_to_success_retires_cause_factor`
  - `test_adjudicated_success_to_failure_opens_cause_factor`
- [tests/test_voi_v2.py](../../../../../../tests/test_voi_v2.py) — direct import
  - `test_a_lookahead_batch_is_built_from_distinct_surfaces`
  - `test_a_lookahead_batch_never_holds_two_checks_on_one_surface`

## Modification guidance

- Change canonical projection policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/canonical_projection.py](../../../../../../src/learnloop/substrate/canonical_projection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

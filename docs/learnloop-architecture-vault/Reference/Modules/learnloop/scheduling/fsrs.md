---
title: "learnloop.scheduling.fsrs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/fsrs.py"
source_paths:
  - "src/learnloop/scheduling/fsrs.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.fsrs module"
  - "src/learnloop/scheduling/fsrs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.fsrs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps fsrs behavior inside its owning package, [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]]. Its public surface centers on `Rating`, `MemoryState`, `forgetting_curve`, `retrievability`, `retrievability_array`, `initial_stability`, `initial_difficulty`, `next_difficulty` and 5 more public symbols.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/fsrs.py](../../../../../../src/learnloop/scheduling/fsrs.py) |
| Source lines | 195 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Rating(IntEnum)` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 13)
- `class MemoryState` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 52)
- `forgetting_curve(stability: float | None, elapsed_days: float, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS) -> float` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 67) — The curve at plain FSRS stability, for FSRS itself: :func:`apply_review`, the weight fit (``fsrs_fitting``) and its evaluation (``evaluation``).
- `retrievability(stability: float | None, elapsed_days: float, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS) -> float` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 77) — The probability of recall ``elapsed_days`` after the last review at ``stability``: the one read every scalar caller makes, so a change to what a read returns (RE8's effective stability) is made here and in :func:`retrievability_array`, and FSRS's own update keeps :func:`forgetti…
- `retrievability_array(stability: Any, elapsed_days: Any, weights: tuple[float, ...]) -> np.ndarray` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 86) — :func:`retrievability` over float64 arrays (anything else is converted first): 0 where stability is not positive or NaN.
- `initial_stability(rating: Rating, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS) -> float` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 102)
- `initial_difficulty(rating: Rating, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS) -> float` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 106)
- `next_difficulty(difficulty: float, rating: Rating, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS) -> float` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 110)
- `next_forget_stability(difficulty: float, stability: float, retrievability: float, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS) -> float` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 118)
- `next_recall_stability(difficulty: float, stability: float, retrievability: float, rating: Rating, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS) -> float` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 133)
- `apply_review(previous: MemoryState | None, rating: Rating, elapsed_days: float, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS) -> MemoryState` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 156)
- `interval_for_retention(stability: float, desired_retention: float=0.9, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS) -> float` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 176)
- `rating_from_score(score: int, max_points: int=4) -> Rating` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 187)

### Module constants

- `FSRS6_DEFAULT_WEIGHTS` ([src/learnloop/scheduling/fsrs.py](../../../../../../src/learnloop/scheduling/fsrs.py), line 22)
- `S_MIN` ([src/learnloop/scheduling/fsrs.py](../../../../../../src/learnloop/scheduling/fsrs.py), line 46)
- `D_MIN` ([src/learnloop/scheduling/fsrs.py](../../../../../../src/learnloop/scheduling/fsrs.py), line 47)
- `D_MAX` ([src/learnloop/scheduling/fsrs.py](../../../../../../src/learnloop/scheduling/fsrs.py), line 48)

## Internal implementation anchors

- `_curve(stability, elapsed_days, decay)` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 58) — FSRS-6's forgetting curve, the one expression of it: Python floats or float64 arrays, ``elapsed_days`` at least 0 and ``stability`` above 0, both already clamped by the caller.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `FSRS6_DEFAULT_WEIGHTS`, `MemoryState`, `Rating`, `apply_review`, `interval_for_retention`, `rating_from_score`; statically calls `MemoryState`, `Rating`, `apply_review`, `interval_for_retention`, `rating_from_score`
- [[Reference/Modules/learnloop/cli/fit|learnloop.cli.fit]] — imports `FSRS6_DEFAULT_WEIGHTS`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `retrievability`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `retrievability`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `retrievability_array`; statically calls `retrievability_array`
- [[Reference/Modules/learnloop/daily_plan/reentry|learnloop.daily_plan.reentry]] — imports `module`; statically calls `retrievability`
- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `retrievability`; statically calls `retrievability`
- [[Reference/Modules/learnloop/delayed_checks|learnloop.delayed_checks]] — imports `interval_for_retention`; statically calls `interval_for_retention`
- [[Reference/Modules/learnloop/field/evaluation|learnloop.field.evaluation]] — imports `FSRS6_DEFAULT_WEIGHTS`
- [[Reference/Modules/learnloop/field/memory|learnloop.field.memory]] — imports `FSRS6_DEFAULT_WEIGHTS`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `retrievability`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `retrievability`; statically calls `retrievability`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `module`; statically calls `initial_stability`, `interval_for_retention`
- [[Reference/Modules/learnloop/intent/report|learnloop.intent.report]] — imports `FSRS6_DEFAULT_WEIGHTS`
- [[Reference/Modules/learnloop/learner_context|learnloop.learner_context]] — imports `retrievability`; statically calls `retrievability`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `FSRS6_DEFAULT_WEIGHTS`
- [[Reference/Modules/learnloop/router_objective/memory|learnloop.router_objective.memory]] — imports `retrievability_array`; statically calls `retrievability_array`
- [[Reference/Modules/learnloop/router_objective/value|learnloop.router_objective.value]] — imports `retrievability_array`; statically calls `retrievability_array`
- [[Reference/Modules/learnloop/scheduling/evaluation|learnloop.scheduling.evaluation]] — imports `MemoryState`, `apply_review`, `forgetting_curve`; statically calls `apply_review`, `forgetting_curve`
- [[Reference/Modules/learnloop/scheduling/family_memory_model|learnloop.scheduling.family_memory_model]] — imports `MemoryState`, `Rating`, `apply_review`, `retrievability`; statically calls `MemoryState`, `Rating`, `apply_review`, `retrievability`
- [[Reference/Modules/learnloop/scheduling/fsrs_fitting|learnloop.scheduling.fsrs_fitting]] — imports `FSRS6_DEFAULT_WEIGHTS`, `MemoryState`, `Rating`, `apply_review`, `forgetting_curve`; statically calls `apply_review`, `forgetting_curve`
- [[Reference/Modules/learnloop/scheduling/review_log|learnloop.scheduling.review_log]] — imports `MemoryState`, `Rating`, `apply_review`, `retrievability`; statically calls `apply_review`, `retrievability`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `FSRS6_DEFAULT_WEIGHTS`, `retrievability`; statically calls `retrievability`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `retrievability`; statically calls `retrievability`
- [[Reference/Modules/learnloop/source_retrieval/deliverable_path|learnloop.source_retrieval.deliverable_path]] — imports `interval_for_retention`; statically calls `interval_for_retention`
- [[Reference/Modules/learnloop/substrate/administration_adapters|learnloop.substrate.administration_adapters]] — imports `FSRS6_DEFAULT_WEIGHTS`
- [[Reference/Modules/learnloop/substrate/card_lineage|learnloop.substrate.card_lineage]] — imports `FSRS6_DEFAULT_WEIGHTS`, `MemoryState`, `Rating`, `apply_review`; statically calls `Rating`, `apply_review`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `retrievability`; statically calls `retrievability`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `retrievability`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `clamp`; calls `clamp`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `enum`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/cli/fit|learnloop.cli.fit]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]], [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] and 24 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ro4_value_helpers.py](../../../../../../tests/ro4_value_helpers.py) — direct import
- [tests/rospeed_ad_link_helpers.py](../../../../../../tests/rospeed_ad_link_helpers.py) — direct import
- [tests/test_administration_adapters.py](../../../../../../tests/test_administration_adapters.py) — direct import
  - `test_ineligible_practice_observation_leaves_card_state_untouched`
  - `test_only_practice_eligible_updates_card_state`
- [tests/test_card_lineage.py](../../../../../../tests/test_card_lineage.py) — direct import
  - `test_fork_starts_new_lineage_and_state_without_inherited_stability`
  - `test_minor_successor_retains_lineage_and_state`
  - `test_rebuild_is_deterministic_and_independent_of_practice_item_cache`
- [tests/test_evaluation.py](../../../../../../tests/test_evaluation.py) — direct import
  - `test_report_on_real_session_flow`
- [tests/test_family_evaluation.py](../../../../../../tests/test_family_evaluation.py) — direct import
  - `test_distance_arm_discounts_only_real_positive_credit`
  - `test_memory_arm_inputs_are_frozen_and_never_a_store`
  - `test_memory_coldness_and_transfer_gate`
  - `test_prequential_predict_all_before_observe_including_memory`
  - `test_shared_key_weights_and_elapsed_are_consistent`
  - `test_unfamilied_falls_back_to_item_and_transfer_never_trains`
- [tests/test_fitted_parameters.py](../../../../../../tests/test_fitted_parameters.py) — direct import
  - `test_resolve_fsrs_weights_defaults_when_absent`
  - `test_resolve_fsrs_weights_falls_back_on_malformed_payload`
  - `test_resolve_fsrs_weights_uses_valid_fitted_set`
- [tests/test_fsrs.py](../../../../../../tests/test_fsrs.py) — direct import
  - `test_again_does_not_increase_stability_like_good`
  - `test_first_review_uses_initial_weights`
  - `test_forgetting_curve_is_one_at_zero_and_decreases`
  - `test_good_review_increases_stability_over_time`
  - `test_interval_grows_with_stability`
  - `test_rating_from_score_buckets`
- [tests/test_fsrs_fitting.py](../../../../../../tests/test_fsrs_fitting.py) — direct import
  - `test_bounds_and_ordering_projection`
  - `test_deterministic`
  - `test_recoverability_beats_defaults_on_perturbed_weights`
  - `test_refuses_below_min_reviews`
  - `test_review_log_loss_skips_short_gaps_and_zero_weight`
  - `test_shrinkage_dominates_at_tiny_n`
- [tests/test_held_grade_composition.py](../../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_router_never_scores_a_held_attempt_and_its_fold_applies_no_review`
- [tests/test_held_grade_evidence.py](../../../../../../tests/test_held_grade_evidence.py) — direct import
  - `test_f8_the_fsrs_fitter_never_fits_a_review_that_never_happened`
- [tests/test_intent_recall_targets.py](../../../../../../tests/test_intent_recall_targets.py) — direct import
  - `test_the_ratio_is_the_fsrs_interval_ratio_and_exactly_one_at_090`
- [tests/test_one_retrievability.py](../../../../../../tests/test_one_retrievability.py) — direct import
  - `test_edge_inputs`
  - `test_known_values`
  - `test_the_array_form_broadcasts_as_the_rollouts_call_it`
  - `test_the_array_form_equals_the_scalar_to_one_ulp_element_by_element`
  - `test_the_curve_passes_0_9_when_elapsed_equals_stability`
  - `test_the_read_is_the_plain_curve_today`
- [tests/test_reader_followups.py](../../../../../../tests/test_reader_followups.py) — direct import
  - `test_without_fsrs_state_the_date_is_the_schedulers_first_interval`
- [tests/test_review_log.py](../../../../../../tests/test_review_log.py) — direct import
  - `test_dont_know_rating_and_weight`
  - `test_hint_cap_and_score_binning_match_live_semantics`
  - `test_reconstruction_reproduces_live_practice_item_state`
- [tests/test_ro0_codex_review.py](../../../../../../tests/test_ro0_codex_review.py) — direct import
- [tests/test_ro0_rows9_13_decision_state.py](../../../../../../tests/test_ro0_rows9_13_decision_state.py) — direct import
  - `test_a_path_that_reads_no_ad_says_so`
  - `test_ad_failing_is_said_and_everything_else_is_kept`
- [tests/test_ro1_interval_factor.py](../../../../../../tests/test_ro1_interval_factor.py) — direct import
  - `test_at_the_tag_due_at_follows_interval_for_retention_of_stability`
  - `test_below_the_tag_and_switched_off_the_factor_stretches_the_interval_as_before`
- [tests/test_ro1_projection.py](../../../../../../tests/test_ro1_projection.py) — direct import
  - `test_at_the_tag_a_rebuild_moves_every_eligible_due_date_to_the_unstretched_interval`
- [tests/test_ro4_trace_report.py](../../../../../../tests/test_ro4_trace_report.py) — direct import
  - `test_the_numeric_policy_honours_its_deadline`
- [tests/test_ro4_value.py](../../../../../../tests/test_ro4_value.py) — direct import
  - `test_the_vectorized_fsrs_is_the_scalar_one`
- [tests/test_rofu_ad_latent.py](../../../../../../tests/test_rofu_ad_latent.py) — direct import
- [tests/test_rofu_ad_link.py](../../../../../../tests/test_rofu_ad_link.py) — direct import
  - `test_the_probe_with_ads_own_predictive_is_pinned`
- [tests/test_rofu_ad_stable.py](../../../../../../tests/test_rofu_ad_stable.py) — direct import
- [tests/test_rofu_monotone.py](../../../../../../tests/test_rofu_monotone.py) — direct import
  - `test_the_probe_before_and_after_r6_is_pinned`
  - `test_the_rollouts_on_the_monotone_prior_never_predict_lower_performance_for_higher_ability`
- [tests/test_rofu_review_draw.py](../../../../../../tests/test_rofu_review_draw.py) — direct import
  - `test_a_practised_topics_outcome_is_drawn_from_the_memory_models_own_p_perform`
  - `test_a_review_right_after_a_review_is_almost_never_a_lapse_with_the_switch_on`
- [tests/test_rofu_speed.py](../../../../../../tests/test_rofu_speed.py) — direct import
  - `test_the_fsrs_update_without_clip_equals_the_schedulers_scalar_formulas`
- [tests/test_router_coldness_covariates.py](../../../../../../tests/test_router_coldness_covariates.py) — direct import
  - `test_the_replayer_records_the_fsrs_predicted_retrievability`
- [tests/test_sg_slip_vs_gap.py](../../../../../../tests/test_sg_slip_vs_gap.py) — direct import
- [tests/test_te3a_lesson_opportunity.py](../../../../../../tests/test_te3a_lesson_opportunity.py) — direct import

## Modification guidance

- Change fsrs policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/fsrs.py](../../../../../../src/learnloop/scheduling/fsrs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

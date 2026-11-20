---
title: "learnloop.router_objective.types"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/types.py"
source_paths:
  - "src/learnloop/router_objective/types.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router_objective"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router_objective.types module"
  - "src/learnloop/router_objective/types.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.types`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.types` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: The plain types the router's objective, its rollouts and its callers share: the action kinds, a candidate (:class:`Action`), and the frozen belief one decision values its candidates on (:class:`Inputs` with its :class:`Topic`, :class:`DatedUse`, :class:`Learning`, :class:`CauseS…

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/types.py](../../../../../../src/learnloop/router_objective/types.py) |
| Source lines | 221 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Topic` ([source](../../../../../../src/learnloop/router_objective/types.py), line 42) — One valued topic (an LO) as the decision believed it.
- `class DatedUse` ([source](../../../../../../src/learnloop/router_objective/types.py), line 64)
- `class CauseSplit` ([source](../../../../../../src/learnloop/router_objective/types.py), line 74) — Slip or gap SG2 (``docs/specs/spec_slip_vs_gap_v1.md`` §3): on a topic whose latest miss has a diagnosis, a lesson's and a repair's effect slope is the mixture over the miss's cause, ``p_gap·γ_gap + p_slip·γ_slip + p_unknown·γ``, instead of ``γ``.
  - `at_mean(self) -> 'CauseSplit'` (line 91; public) — The believed parameters (each posterior's mean, no parameter draw), as the belief's own world reads γ.
- `class Learning` ([source](../../../../../../src/learnloop/router_objective/types.py), line 98) — AD's learning parameters (posterior mean, variance): ``γ`` per practice opportunity, the reading dose curve's ``ḡ_1, ḡ_2`` on scales ``h_1, h_2``; from TE3a, AD's lesson curve (None: RO4's placeholder); from slip or gap SG2, the lesson's and the repair's slope by the miss's caus…
- `class EffectSlope` ([source](../../../../../../src/learnloop/router_objective/types.py), line 112) — ``ΔG = α_v + β_v·f(a)`` (§8.4): each coefficient's posterior mean and variance.
- `class Price` ([source](../../../../../../src/learnloop/router_objective/types.py), line 122) — The attention price at this decision (§8.6): ``κ(x) = κ0·x/m̄`` on session minutes.
- `class Action` ([source](../../../../../../src/learnloop/router_objective/types.py), line 132) — One candidate as the value estimator sees it.
  - `__post_init__(self) -> None` (line 165; internal)
- `class Inputs` ([source](../../../../../../src/learnloop/router_objective/types.py), line 177) — The frozen belief one decision values its candidates on (every number the trace reports).
  - `cutoff(self) -> float` (line 206; public) — ``C`` in days from the decision (§3.2): carried through every rollout.
- `cutoff_for(horizon_days: float, dated: Sequence[DatedUse]) -> float` ([source](../../../../../../src/learnloop/router_objective/types.py), line 213)

### Module constants

- `REVIEW` ([src/learnloop/router_objective/types.py](../../../../../../src/learnloop/router_objective/types.py), line 24)
- `NEW_PRACTICE` ([src/learnloop/router_objective/types.py](../../../../../../src/learnloop/router_objective/types.py), line 25)
- `READING` ([src/learnloop/router_objective/types.py](../../../../../../src/learnloop/router_objective/types.py), line 26)
- `PROBE` ([src/learnloop/router_objective/types.py](../../../../../../src/learnloop/router_objective/types.py), line 27)
- `REPAIR` ([src/learnloop/router_objective/types.py](../../../../../../src/learnloop/router_objective/types.py), line 28)
- `TEACH_BACK` ([src/learnloop/router_objective/types.py](../../../../../../src/learnloop/router_objective/types.py), line 29)
- `LESSON` ([src/learnloop/router_objective/types.py](../../../../../../src/learnloop/router_objective/types.py), line 30)
- `STOP` ([src/learnloop/router_objective/types.py](../../../../../../src/learnloop/router_objective/types.py), line 31)
- `SEQUENCE` ([src/learnloop/router_objective/types.py](../../../../../../src/learnloop/router_objective/types.py), line 34)
- `PRACTICE_KINDS` ([src/learnloop/router_objective/types.py](../../../../../../src/learnloop/router_objective/types.py), line 35)
- `KINDS` ([src/learnloop/router_objective/types.py](../../../../../../src/learnloop/router_objective/types.py), line 36)

### Explicit exports

`__all__` declares:

- `Action`
- `CauseSplit`
- `DatedUse`
- `EffectSlope`
- `Inputs`
- `KINDS`
- `LESSON`
- `Learning`
- `NEW_PRACTICE`
- `PRACTICE_KINDS`
- `PROBE`
- `Price`
- `READING`
- `REPAIR`
- `REVIEW`
- `SEQUENCE`
- `STOP`
- `TEACH_BACK`
- `Topic`
- `LESSON_OFFER_PREFIX`
- `LESSON_OFFER_SUBTYPE`
- `STOP_FOR_TODAY`
- `cutoff_for`
- `is_offer_subtype`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `EffectSlope`, `is_offer_subtype`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `module`; statically calls `Action`, `CauseSplit`, `DatedUse`, `Inputs`, `Learning`, `Price`, `Topic`, `is_offer_subtype`
- [[Reference/Modules/learnloop/daily_plan/objective_job|learnloop.daily_plan.objective_job]] — imports `module`
- [[Reference/Modules/learnloop/router_objective/diagnostic_value|learnloop.router_objective.diagnostic_value]] — imports `Action`, `Inputs`, `PROBE`, `SEQUENCE`
- [[Reference/Modules/learnloop/router_objective/learned_tail|learnloop.router_objective.learned_tail]] — imports `module`
- [[Reference/Modules/learnloop/router_objective/preferences|learnloop.router_objective.preferences]] — imports `module`; statically calls `is_offer_subtype`
- [[Reference/Modules/learnloop/router_objective/rollouts|learnloop.router_objective.rollouts]] — imports `Action`, `DatedUse`, `Inputs`, `LESSON`, `NEW_PRACTICE`, `PRACTICE_KINDS`, `PROBE`, `READING`, `REPAIR`, `REVIEW`, `STOP`; statically calls `Action`
- [[Reference/Modules/learnloop/router_objective/trace_assembly|learnloop.router_objective.trace_assembly]] — imports `LESSON_OFFER_SUBTYPE`, `STOP_FOR_TODAY`, `module`; statically calls `is_offer_subtype`

### Repository tooling consumers

- [scripts/probe_router_report.py](../../../../../../scripts/probe_router_report.py); calls `Action`, `CauseSplit`, `DatedUse`, `Inputs`, `Learning`, `Price`, `Topic`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/plan_refs|learnloop.plan_refs]] — imports `LESSON_OFFER_PREFIX`, `LESSON_OFFER_SUBTYPE`, `STOP_FOR_TODAY`, `is_offer_subtype`
- [[Reference/Modules/learnloop/router_objective/ad_link|learnloop.router_objective.ad_link]] — imports `AdLink`, `LessonCurve`
- [[Reference/Modules/learnloop/router_objective/diagnostic_payload|learnloop.router_objective.diagnostic_payload]] — imports `DiagnosticProbe`
- [[Reference/Modules/learnloop/router_objective/memory|learnloop.router_objective.memory]] — imports `Combiner`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]], [[Reference/Modules/learnloop/daily_plan/objective_job|learnloop.daily_plan.objective_job]], [[Reference/Modules/learnloop/router_objective/diagnostic_value|learnloop.router_objective.diagnostic_value]], [[Reference/Modules/learnloop/router_objective/learned_tail|learnloop.router_objective.learned_tail]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ro4_value_helpers.py](../../../../../../tests/ro4_value_helpers.py) — direct import
- [tests/ro6_codex_review_helpers.py](../../../../../../tests/ro6_codex_review_helpers.py) — direct import
- [tests/rospeed_ad_link_helpers.py](../../../../../../tests/rospeed_ad_link_helpers.py) — direct import
- [tests/test_action_kinds_complete.py](../../../../../../tests/test_action_kinds_complete.py) — direct import
  - `test_a_probe_with_a_diagnostic_payload_has_its_effect_through_the_successor_evaluator`
  - `test_a_sequence_is_valued_by_its_steps`
  - `test_action_kind_has_a_rollout_effect`
  - `test_action_kind_has_its_existing_learned_tail_group`
  - `test_every_kind_has_a_plan_case_or_is_valued_without_a_candidate`
  - `test_stop_ends_the_session_in_its_accepted_branch`
  - `test_stops_trace_label_and_support`
- [tests/test_diagnostic_probe_value.py](../../../../../../tests/test_diagnostic_probe_value.py) — direct import
  - `test_a_lesson_declined_at_the_same_boundary_prices_its_probe_as_exposed`
  - `test_a_probe_anywhere_in_a_sequence_appends_the_rest_and_the_tail_once`
  - `test_a_probe_without_a_payload_is_the_predecessors_and_a_payload_is_refused_there`
  - `test_the_probe_answer_is_not_also_a_binary_ability_observation`
- [tests/test_ih2_lessons_compete.py](../../../../../../tests/test_ih2_lessons_compete.py) — direct import
  - `test_a_probe_mode_item_in_a_contest_is_valued_by_the_probe_bundle`
  - `test_a_question_not_yet_written_takes_the_probe_interface_only_with_the_lesson_in_the_support`
  - `test_the_contest_values_a_generated_probe_with_rous_probe_interface_and_nothing_new`
  - `test_the_followup_decision_values_the_unwritten_probe_with_the_probe_interface`
  - `test_the_journey_on_a_real_miss_lesson_then_not_now_then_the_question`
  - `test_the_offers_declined_branch_is_the_followup_not_the_tail`
- [tests/test_plan_refs.py](../../../../../../tests/test_plan_refs.py) — direct import
  - `test_the_strings_keep_their_bytes_and_every_layer_reads_the_leafs`
- [tests/test_ro4_codex_review.py](../../../../../../tests/test_ro4_codex_review.py) — direct import
  - `test_f5_mid_block_alternatives_are_ordered_sequences_of_their_own_blocks`
- [tests/test_ro4_trace_report.py](../../../../../../tests/test_ro4_trace_report.py) — direct import
  - `test_the_numeric_policy_honours_its_deadline`
- [tests/test_ro4_value.py](../../../../../../tests/test_ro4_value.py) — direct import
  - `test_a_date_inside_a_long_action_is_scored_at_the_date_on_the_state_before_it`
  - `test_a_probe_is_scored_through_its_repair_branches`
  - `test_an_action_crossing_the_cutoff_carries_its_commitment_into_t_c`
  - `test_durations_are_sampled_and_their_spread_costs`
  - `test_f12_a_goal_inside_the_continuation_session_sees_only_the_blocks_before_it`
  - `test_f2_reopened_the_branch_is_chosen_on_the_average_over_imagined_outcomes`
  - `test_f2_the_probe_branch_never_sees_the_repairs_future_result`
  - `test_f3_a_date_crossed_by_a_probe_is_scored_on_the_state_before_it_and_its_repair`
  - `test_f3_a_multi_day_action_counts_no_interval_twice_and_no_session_before_its_end`
  - `test_f4_the_return_gap_follows_every_session_end`
  - `test_f5_a_sequence_values_its_steps_in_order_with_their_own_kinds`
  - `test_f6_the_effect_feature_is_the_difference_of_forecast_probabilities`
  - `test_f7_a_refinement_cut_by_the_deadline_keeps_the_last_complete_batch`
  - `test_offer_branches_match_a_hand_computed_case`
  - `test_one_cutoff_for_every_candidate_and_it_is_the_latest_goal_date_when_further`
  - `test_the_eve_of_exam_regression`
  - `test_the_gain_curve_rises_with_todays_minutes`
  - `test_the_numeric_policy_is_argmax_with_ties_by_support_order`
  - `test_the_same_theta_draw_is_used_across_candidates`
  - `test_v_recomputed_from_the_logged_rows_is_the_tails_next_action`
- [tests/test_ro5_codex_review.py](../../../../../../tests/test_ro5_codex_review.py) — direct import
  - `test_f7_the_trace_freezes_every_dated_goals_forecast_beyond_the_window`
- [tests/test_ro5_stop_coin.py](../../../../../../tests/test_ro5_stop_coin.py) — direct import
  - `test_the_stop_branch_shows_the_return_effect_and_an_inert_shift_drops_out`
- [tests/test_ro6_codex_rereview.py](../../../../../../tests/test_ro6_codex_rereview.py) — direct import
  - `test_f3_a_carried_cutoff_runs_every_rollout_at_it`
- [tests/test_rofu_ad_latent.py](../../../../../../tests/test_rofu_ad_latent.py) — direct import
  - `test_codexs_reproductions_start_at_ads_p_bar`
  - `test_zero_variance_stays_equal`
- [tests/test_rofu_ad_link.py](../../../../../../tests/test_rofu_ad_link.py) — direct import
  - `test_the_probe_with_ads_own_predictive_is_pinned`
  - `test_without_the_link_the_rollouts_are_mvp049s_bitwise`
- [tests/test_rofu_ad_stable.py](../../../../../../tests/test_rofu_ad_stable.py) — direct import
- [tests/test_rofu_monotone.py](../../../../../../tests/test_rofu_monotone.py) — direct import
  - `test_the_probe_before_and_after_r6_is_pinned`
  - `test_the_rollouts_on_the_monotone_prior_never_predict_lower_performance_for_higher_ability`
- [tests/test_rofu_review_draw.py](../../../../../../tests/test_rofu_review_draw.py) — direct import
  - `test_a_review_right_after_a_review_is_almost_never_a_lapse_with_the_switch_on`
- [tests/test_rofu_speed.py](../../../../../../tests/test_rofu_speed.py) — direct import
- [tests/test_rospeed_ad_link.py](../../../../../../tests/test_rospeed_ad_link.py) — direct import
  - `test_the_baselines_and_the_gain_are_the_landing_codes_bit_for_bit`
- [tests/test_sg_slip_vs_gap.py](../../../../../../tests/test_sg_slip_vs_gap.py) — direct import
  - `test_a_probes_repair_branch_and_a_sequences_repair_step_split_too`
  - `test_sg2_moves_only_the_diagnosed_topics_values_and_the_logged_mu_replays`
- [tests/test_te3a_lesson_opportunity.py](../../../../../../tests/test_te3a_lesson_opportunity.py) — direct import
  - `test_a_probe_closes_the_lesson_window_on_the_held_link_too`
  - `test_at_the_seeded_prior_the_lesson_q_bar_equals_ro4s_placeholder`
  - `test_codex_f2_with_fitted_practice_parameters_the_untouched_lesson_curve_moves_no_decision`
  - `test_codex_f3_rollouts_carry_the_lesson_window_as_ads_transition_does`
- [tests/test_te3b_value.py](../../../../../../tests/test_te3b_value.py) — direct import
  - `test_a_committed_delayed_check_enters_the_value_and_none_changes_nothing`
  - `test_offer_branches_match_a_hand_computed_case_for_a_lesson`
  - `test_the_eve_of_exam_regression_holds_with_a_lesson_offer_beside_the_block`
  - `test_the_offer_runs_on_the_held_link_with_it_on_and_on_the_landing_link_with_it_off`

## Modification guidance

- Make changes here when the responsibility remains types within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/types.py](../../../../../../src/learnloop/router_objective/types.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

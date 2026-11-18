---
title: "learnloop.router_objective.rollouts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/rollouts.py"
source_paths:
  - "src/learnloop/router_objective/rollouts.py"
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
  - "learnloop.router_objective.rollouts module"
  - "src/learnloop/router_objective/rollouts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.rollouts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.rollouts` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: How a block is simulated: the rollouts that estimate each candidate's value ``Q̄`` under the router's objective (spec_router_objective_v1 §3.2, §8.1), a pure function of a frozen belief.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/rollouts.py](../../../../../../src/learnloop/router_objective/rollouts.py) |
| Source lines | 1257 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `evaluate(inputs: Inputs, actions: Sequence[Action], *, draws: int, seed: str, max_draws: int | None=None, keep_going: Callable[[], bool] | None=None, deadline: float | None=None, clock: Callable[[], float]=time.monotonic, on_complete: Callable[[Evaluation], None] | None=None, cutoff: float | None=None, unmeasured: Collection[str] | None=None, merged_sessions: bool=False, consistent_review_draw: bool=False, held_ad_link: bool=False) -> Evaluation` ([source](../../../../../../src/learnloop/router_objective/rollouts.py), line 1151) — ``Q`` for every action (and the reference row) under ``draws`` θ draws, adding batches of ``draws`` more while ``keep_going()`` holds, up to ``max_draws``, and never past ``deadline`` (``clock``'s).
- `baselines(inputs: Inputs, window_days: int, *, draws: int, seed: str, merged_sessions: bool=False, consistent_review_draw: bool=False, held_ad_link: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/rollouts.py), line 1210) — §8.7's ``m⁰``: the memory forecast of each use in the evaluation window from the pre-action belief under the tail (the path the pre-action ``V`` values): per topic, the mean ``P(perform)`` on days ``1..B``, and each dated use's at its date.
- `gain(inputs: Inputs, session_lengths: Sequence[float], *, draws: int, seed: str, merged_sessions: bool=False, consistent_review_draw: bool=False, held_ad_link: bool=False) -> dict[float, float]` ([source](../../../../../../src/learnloop/router_objective/rollouts.py), line 1232) — ``G(x)`` (§8.6): the forecast valued uses (no attention cost) when today's session runs ``x`` minutes from the start under the tail, then the tail; for the price's daily seed and the frontier.

### Module constants

- `TAIL_VERSION` ([src/learnloop/router_objective/rollouts.py](../../../../../../src/learnloop/router_objective/rollouts.py), line 97)
- `REFERENCE_REF` ([src/learnloop/router_objective/rollouts.py](../../../../../../src/learnloop/router_objective/rollouts.py), line 99)
- `MINUTES_PER_DAY` ([src/learnloop/router_objective/rollouts.py](../../../../../../src/learnloop/router_objective/rollouts.py), line 100)
- `REVIEW_DRAW_VERSION` ([src/learnloop/router_objective/rollouts.py](../../../../../../src/learnloop/router_objective/rollouts.py), line 113)
- `_STATE_FIELDS` ([src/learnloop/router_objective/rollouts.py](../../../../../../src/learnloop/router_objective/rollouts.py), line 240)

### Explicit exports

`__all__` declares:

- `MINUTES_PER_DAY`
- `REFERENCE_REF`
- `REVIEW_DRAW_VERSION`
- `TAIL_VERSION`
- `baselines`
- `evaluate`
- `gain`

## Internal implementation anchors

- `_seed_int(seed: str, stream: str) -> int` ([source](../../../../../../src/learnloop/router_objective/rollouts.py), line 126)
- `class _Streams` ([source](../../../../../../src/learnloop/router_objective/rollouts.py), line 130) — Counter-free common random numbers: each stream is a fixed array, the same for every candidate.
- `_beta_draw(u: np.ndarray, a: float, b: float) -> np.ndarray` ([source](../../../../../../src/learnloop/router_objective/rollouts.py), line 156) — A Beta(a, b) quantile at ``u`` (inverse CDF by bisection on the regularized incomplete beta): the same uniform gives the same draw for every candidate.
- `_betainc(a: float, b: float, x: float) -> float` ([source](../../../../../../src/learnloop/router_objective/rollouts.py), line 172) — The regularized incomplete beta ``I_x(a, b)`` (Lentz's continued fraction).
- `class _Theta` ([source](../../../../../../src/learnloop/router_objective/rollouts.py), line 203)
- `class _State` ([source](../../../../../../src/learnloop/router_objective/rollouts.py), line 217)
- `class _Model` ([source](../../../../../../src/learnloop/router_objective/rollouts.py), line 243) — One decision's rollouts: the frozen inputs, the draws, and the streams.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `_Model`, `baselines`, `evaluate`, `gain`
- [[Reference/Modules/learnloop/router_objective/trace_assembly|learnloop.router_objective.trace_assembly]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/router_objective/memory|learnloop.router_objective.memory]] — imports `Fsrs`, `logit`, `perform`, `sigmoid`; calls `Fsrs`, `logit`, `perform`, `sigmoid`
- [[Reference/Modules/learnloop/router_objective/objective|learnloop.router_objective.objective]] — imports `Evaluation`, `Valued`, `_Ledger`, `_terms`; calls `Evaluation`, `Valued`, `_terms`
- [[Reference/Modules/learnloop/router_objective/types|learnloop.router_objective.types]] — imports `Action`, `DatedUse`, `Inputs`, `LESSON`, `NEW_PRACTICE`, `PRACTICE_KINDS`, `PROBE`, `READING`, `REPAIR`, `REVIEW`, `STOP`; calls `Action`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `retrievability_array`; calls `retrievability_array`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `math`, `time`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/router_objective/trace_assembly|learnloop.router_objective.trace_assembly]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/rospeed_ad_link_helpers.py](../../../../../../tests/rospeed_ad_link_helpers.py) — direct import
- [tests/test_action_kinds_complete.py](../../../../../../tests/test_action_kinds_complete.py) — direct import
- [tests/test_ih2_lessons_compete.py](../../../../../../tests/test_ih2_lessons_compete.py) — direct import
  - `test_the_offers_declined_branch_is_the_followup_not_the_tail`
- [tests/test_objective_refinement.py](../../../../../../tests/test_objective_refinement.py) — direct import
- [tests/test_ro4_codex_review.py](../../../../../../tests/test_ro4_codex_review.py) — direct import
  - `test_f8_a_reading_candidate_starts_from_ads_dose_position`
- [tests/test_ro4_trace_report.py](../../../../../../tests/test_ro4_trace_report.py) — direct import
  - `test_the_numeric_policy_honours_its_deadline`
- [tests/test_ro4_value.py](../../../../../../tests/test_ro4_value.py) — direct import
  - `test_a_date_inside_a_long_action_is_scored_at_the_date_on_the_state_before_it`
  - `test_a_probe_is_scored_through_its_repair_branches`
  - `test_an_action_crossing_the_cutoff_carries_its_commitment_into_t_c`
  - `test_durations_are_sampled_and_their_spread_costs`
  - `test_f12_a_goal_inside_the_continuation_session_sees_only_the_blocks_before_it`
  - `test_f12_one_draws_action_duration_never_moves_another_draws_clock`
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
  - `test_the_same_theta_draw_is_used_across_candidates`
  - `test_v_recomputed_from_the_logged_rows_is_the_tails_next_action`
- [tests/test_ro5_stop_coin.py](../../../../../../tests/test_ro5_stop_coin.py) — direct import
  - `test_the_stop_branch_shows_the_return_effect_and_an_inert_shift_drops_out`
- [tests/test_ro6_codex_rereview.py](../../../../../../tests/test_ro6_codex_rereview.py) — direct import
  - `test_f3_a_carried_cutoff_runs_every_rollout_at_it`
- [tests/test_ro6_codex_review.py](../../../../../../tests/test_ro6_codex_review.py) — direct import
  - `test_f3_no_carried_cutoff_leaves_the_rollouts_as_ro4s`
- [tests/test_ro6_landing.py](../../../../../../tests/test_ro6_landing.py) — direct import
  - `test_r7_the_rollouts_keep_each_unmeasured_topics_share_apart_on_the_same_paths`
- [tests/test_rofu_ad_latent.py](../../../../../../tests/test_rofu_ad_latent.py) — direct import
- [tests/test_rofu_ad_link.py](../../../../../../tests/test_rofu_ad_link.py) — direct import
  - `test_a_decisions_p_bar_enters_as_ads_latent_and_reads_back_as_itself`
  - `test_an_unpractised_attempt_and_a_probe_are_drawn_from_ads_own_predictive`
  - `test_the_beliefs_step_is_the_laplace_step_under_ads_predictive`
  - `test_the_numeric_policy_reads_ads_own_predictive_only_with_its_switch`
  - `test_the_probe_with_ads_own_predictive_is_pinned`
  - `test_without_the_link_the_rollouts_are_mvp049s_bitwise`
- [tests/test_rofu_ad_stable.py](../../../../../../tests/test_rofu_ad_stable.py) — direct import
- [tests/test_rofu_monotone.py](../../../../../../tests/test_rofu_monotone.py) — direct import
  - `test_the_probe_before_and_after_r6_is_pinned`
  - `test_the_rollouts_on_the_monotone_prior_never_predict_lower_performance_for_higher_ability`
- [tests/test_rofu_review_draw.py](../../../../../../tests/test_rofu_review_draw.py) — direct import
  - `test_a_practised_topics_outcome_is_drawn_from_the_memory_models_own_p_perform`
  - `test_a_review_right_after_a_review_is_almost_never_a_lapse_with_the_switch_on`
  - `test_the_numeric_policy_draws_consistently_only_with_its_switch`
- [tests/test_rofu_speed.py](../../../../../../tests/test_rofu_speed.py) — direct import
  - `test_a_deadline_admits_more_draws_merged_so_the_default_is_the_per_block_loop`
  - `test_merged_sessions_equal_the_per_block_loop`
  - `test_the_merged_path_calls_the_fsrs_update_far_fewer_times`
  - `test_the_numeric_policy_merges_only_with_its_switch`
- [tests/test_rospeed2_connections.py](../../../../../../tests/test_rospeed2_connections.py) — direct import
- [tests/test_rospeed_ad_link.py](../../../../../../tests/test_rospeed_ad_link.py) — direct import
  - `test_the_baselines_and_the_gain_are_the_landing_codes_bit_for_bit`
  - `test_the_held_values_follow_the_state_bit_for_bit`
- [tests/test_sg_slip_vs_gap.py](../../../../../../tests/test_sg_slip_vs_gap.py) — direct import
  - `test_a_probes_repair_branch_and_a_sequences_repair_step_split_too`
  - `test_nothing_adds_a_threshold`
  - `test_the_belief_world_reads_the_slopes_means_only`
  - `test_the_nov_7_shape_a_slip_is_worth_less_than_a_gap_by_the_priors_difference_only`
  - `test_the_slopes_joint_posterior_is_drawn_with_its_covariance`
- [tests/test_te3a_lesson_opportunity.py](../../../../../../tests/test_te3a_lesson_opportunity.py) — direct import
  - `test_a_probe_closes_the_lesson_window_on_the_held_link_too`
- [tests/test_te3b_population.py](../../../../../../tests/test_te3b_population.py) — direct import
  - `test_with_lessons_off_the_same_database_is_valued_without_lessons`
- [tests/test_te3b_value.py](../../../../../../tests/test_te3b_value.py) — direct import
  - `test_a_committed_delayed_check_enters_the_value_and_none_changes_nothing`
  - `test_offer_branches_match_a_hand_computed_case_for_a_lesson`
  - `test_the_eve_of_exam_regression_holds_with_a_lesson_offer_beside_the_block`
  - `test_the_offer_runs_on_the_held_link_with_it_on_and_on_the_landing_link_with_it_off`

## Modification guidance

- Make changes here when the responsibility remains rollouts within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/rollouts.py](../../../../../../src/learnloop/router_objective/rollouts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

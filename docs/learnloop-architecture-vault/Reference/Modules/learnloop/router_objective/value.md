---
title: "learnloop.router_objective.value"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/value.py"
source_paths:
  - "src/learnloop/router_objective/value.py"
source_commit: "235b7218fc0cb9b038c6b03968ace75f2cbaab7c"
source_commit_timestamp: "2026-11-05T22:11:48-05:00"
source_worktree_state: "clean"
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
  - "learnloop.router_objective.value module"
  - "src/learnloop/router_objective/value.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.value`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.value` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO4 §3.2, §8.1: the objective's value estimator ``Q̄``, a pure function of a frozen belief.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/value.py](../../../../../../src/learnloop/router_objective/value.py) |
| Source lines | 1215 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `235b7218fc0cb9b038c6b03968ace75f2cbaab7c` |
| Commit timestamp | `2026-11-05T22:11:48-05:00` |

## Public API

- `class Topic` ([source](../../../../../../src/learnloop/router_objective/value.py), line 105) — One valued topic (an LO) as the decision believed it.
- `class DatedUse` ([source](../../../../../../src/learnloop/router_objective/value.py), line 124)
- `class Learning` ([source](../../../../../../src/learnloop/router_objective/value.py), line 134) — AD's learning parameters (posterior mean, variance): ``γ`` per practice opportunity, the reading dose curve's ``ḡ_1, ḡ_2`` on scales ``h_1, h_2``.
- `class EffectSlope` ([source](../../../../../../src/learnloop/router_objective/value.py), line 145) — ``ΔG = α_v + β_v·f(a)`` (§8.4): each coefficient's posterior mean and variance.
- `class Price` ([source](../../../../../../src/learnloop/router_objective/value.py), line 155) — The attention price at this decision (§8.6): ``κ(x) = κ0·x/m̄`` on session minutes.
- `class Action` ([source](../../../../../../src/learnloop/router_objective/value.py), line 165) — One candidate as the value estimator sees it.
  - `__post_init__(self) -> None` (line 188; internal)
- `class Inputs` ([source](../../../../../../src/learnloop/router_objective/value.py), line 198) — The frozen belief one decision values its candidates on (every number the trace reports).
  - `cutoff(self) -> float` (line 225; public) — ``C`` in days from the decision (§3.2): carried through every rollout.
- `cutoff_for(horizon_days: float, dated: Sequence[DatedUse]) -> float` ([source](../../../../../../src/learnloop/router_objective/value.py), line 232)
- `class Valued` ([source](../../../../../../src/learnloop/router_objective/value.py), line 1038) — One candidate's value (§8.8's terms).
  - `q(self) -> float` (line 1049; public)
- `class Evaluation` ([source](../../../../../../src/learnloop/router_objective/value.py), line 1054)
  - `by_ref(self) -> dict[str, Valued]` (line 1063; public)
  - `v(self) -> float` (line 1067; public) — ``V = Σ_a π_tail(a)·Q(a)``: the tail's next action is deterministic, so ``V`` is its row's ``Q``.
- `evaluate(inputs: Inputs, actions: Sequence[Action], *, draws: int, seed: str, max_draws: int | None=None, keep_going: Callable[[], bool] | None=None, deadline: float | None=None, clock: Callable[[], float]=time.monotonic, on_complete: Callable[[Evaluation], None] | None=None, cutoff: float | None=None, unmeasured: Collection[str] | None=None, merged_sessions: bool=False) -> Evaluation` ([source](../../../../../../src/learnloop/router_objective/value.py), line 1089) — ``Q`` for every action (and the reference row) under ``draws`` θ draws, adding batches of ``draws`` more while ``keep_going()`` holds, up to ``max_draws``, and never past ``deadline`` (``clock``'s).
- `paired_standard_error(a: Valued, b: Valued) -> float` ([source](../../../../../../src/learnloop/router_objective/value.py), line 1141) — The standard error of ``Q̄(a) − Q̄(b)`` over the shared draws (common random numbers).
- `numeric_choice(evaluation: Evaluation, support: Sequence[str]) -> tuple[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/value.py), line 1150) — ``π_Q`` (§8.3): plain argmax of ``Q̄``; candidates within the paired precision of the maximum are broken by support order (staged's pick first).
- `baselines(inputs: Inputs, window_days: int, *, draws: int, seed: str, merged_sessions: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/value.py), line 1169) — §8.7's ``m⁰``: the memory forecast of each use in the evaluation window from the pre-action belief under the tail (the path the pre-action ``V`` values): per topic, the mean ``P(perform)`` on days ``1..B``, and each dated use's at its date.
- `gain(inputs: Inputs, session_lengths: Sequence[float], *, draws: int, seed: str, merged_sessions: bool=False) -> dict[float, float]` ([source](../../../../../../src/learnloop/router_objective/value.py), line 1189) — ``G(x)`` (§8.6): the forecast valued uses (no attention cost) when today's session runs ``x`` minutes from the start under the tail, then the tail; for the price's daily seed and the frontier.

### Module constants

- `OBJECTIVE_VERSION` ([src/learnloop/router_objective/value.py](../../../../../../src/learnloop/router_objective/value.py), line 75)
- `TAIL_VERSION` ([src/learnloop/router_objective/value.py](../../../../../../src/learnloop/router_objective/value.py), line 76)
- `TERMINAL_VERSION` ([src/learnloop/router_objective/value.py](../../../../../../src/learnloop/router_objective/value.py), line 77)
- `REVIEW` ([src/learnloop/router_objective/value.py](../../../../../../src/learnloop/router_objective/value.py), line 80)
- `NEW_PRACTICE` ([src/learnloop/router_objective/value.py](../../../../../../src/learnloop/router_objective/value.py), line 81)
- `READING` ([src/learnloop/router_objective/value.py](../../../../../../src/learnloop/router_objective/value.py), line 82)
- `PROBE` ([src/learnloop/router_objective/value.py](../../../../../../src/learnloop/router_objective/value.py), line 83)
- `REPAIR` ([src/learnloop/router_objective/value.py](../../../../../../src/learnloop/router_objective/value.py), line 84)
- `TEACH_BACK` ([src/learnloop/router_objective/value.py](../../../../../../src/learnloop/router_objective/value.py), line 85)
- `LESSON` ([src/learnloop/router_objective/value.py](../../../../../../src/learnloop/router_objective/value.py), line 86)
- `STOP` ([src/learnloop/router_objective/value.py](../../../../../../src/learnloop/router_objective/value.py), line 87)
- `SEQUENCE` ([src/learnloop/router_objective/value.py](../../../../../../src/learnloop/router_objective/value.py), line 90)
- `PRACTICE_KINDS` ([src/learnloop/router_objective/value.py](../../../../../../src/learnloop/router_objective/value.py), line 91)
- `KINDS` ([src/learnloop/router_objective/value.py](../../../../../../src/learnloop/router_objective/value.py), line 92)
- `REFERENCE_REF` ([src/learnloop/router_objective/value.py](../../../../../../src/learnloop/router_objective/value.py), line 94)
- `MINUTES_PER_DAY` ([src/learnloop/router_objective/value.py](../../../../../../src/learnloop/router_objective/value.py), line 95)
- `_LEDGER_FIELDS` ([src/learnloop/router_objective/value.py](../../../../../../src/learnloop/router_objective/value.py), line 350)

### Explicit exports

`__all__` declares:

- `Action`
- `baselines`
- `DatedUse`
- `EffectSlope`
- `Evaluation`
- `Inputs`
- `KINDS`
- `LESSON`
- `Learning`
- `NEW_PRACTICE`
- `OBJECTIVE_VERSION`
- `PRACTICE_KINDS`
- `PROBE`
- `Price`
- `READING`
- `REFERENCE_REF`
- `REPAIR`
- `REVIEW`
- `SEQUENCE`
- `STOP`
- `TAIL_VERSION`
- `TEACH_BACK`
- `TERMINAL_VERSION`
- `Topic`
- `Valued`
- `cutoff_for`
- `evaluate`
- `gain`
- `numeric_choice`
- `paired_standard_error`

## Internal implementation anchors

- `_seed_int(seed: str, stream: str) -> int` ([source](../../../../../../src/learnloop/router_objective/value.py), line 239)
- `class _Streams` ([source](../../../../../../src/learnloop/router_objective/value.py), line 243) — Counter-free common random numbers: each stream is a fixed array, the same for every candidate.
- `_beta_draw(u: np.ndarray, a: float, b: float) -> np.ndarray` ([source](../../../../../../src/learnloop/router_objective/value.py), line 267) — A Beta(a, b) quantile at ``u`` (inverse CDF by bisection on the regularized incomplete beta): the same uniform gives the same draw for every candidate.
- `_betainc(a: float, b: float, x: float) -> float` ([source](../../../../../../src/learnloop/router_objective/value.py), line 283) — The regularized incomplete beta ``I_x(a, b)`` (Lentz's continued fraction).
- `class _Theta` ([source](../../../../../../src/learnloop/router_objective/value.py), line 314)
- `class _State` ([source](../../../../../../src/learnloop/router_objective/value.py), line 328)
- `class _Ledger` ([source](../../../../../../src/learnloop/router_objective/value.py), line 355) — Per draw: the terms of one path (§8.8's per-candidate terms).
- `class _Model` ([source](../../../../../../src/learnloop/router_objective/value.py), line 401) — One decision's rollouts: the frozen inputs, the draws, and the streams.
- `_terms(ledger: _Ledger, model: '_Model | None'=None) -> dict[str, float]` ([source](../../../../../../src/learnloop/router_objective/value.py), line 1073)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `EffectSlope`, `_Model`, `baselines`, `evaluate`, `gain`, `numeric_choice`, `paired_standard_error`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `module`; statically calls `Action`, `DatedUse`, `Inputs`, `Learning`, `Price`, `Topic`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/router_objective/memory|learnloop.router_objective.memory]] — imports `Combiner`, `Fsrs`, `perform`, `sigmoid`; calls `Fsrs`, `perform`, `sigmoid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `math`, `time`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro4_codex_review.py](../../../../../../tests/test_ro4_codex_review.py) — direct import
  - `test_f5_mid_block_alternatives_are_ordered_sequences_of_their_own_blocks`
  - `test_f8_a_reading_candidate_starts_from_ads_dose_position`
  - `test_f9_the_drawn_options_forecast_is_resolved_and_reported`
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
  - `test_the_numeric_policy_is_argmax_with_ties_by_support_order`
  - `test_the_same_theta_draw_is_used_across_candidates`
  - `test_v_recomputed_from_the_logged_rows_is_the_tails_next_action`
- [tests/test_ro5_codex_review.py](../../../../../../tests/test_ro5_codex_review.py) — direct import
  - `test_f7_the_trace_freezes_every_dated_goals_forecast_beyond_the_window`
- [tests/test_ro5_stop_coin.py](../../../../../../tests/test_ro5_stop_coin.py) — direct import
  - `test_the_stop_branch_shows_the_return_effect_and_an_inert_shift_drops_out`
- [tests/test_ro6_codex_rereview.py](../../../../../../tests/test_ro6_codex_rereview.py) — direct import
  - `test_f3_a_carried_cutoff_runs_every_rollout_at_it`
- [tests/test_ro6_codex_review.py](../../../../../../tests/test_ro6_codex_review.py) — direct import
  - `test_f3_no_carried_cutoff_leaves_the_rollouts_as_ro4s`
- [tests/test_ro6_landing.py](../../../../../../tests/test_ro6_landing.py) — direct import
  - `test_r7_the_rollouts_keep_each_unmeasured_topics_share_apart_on_the_same_paths`
- [tests/test_rofu_speed.py](../../../../../../tests/test_rofu_speed.py) — direct import
  - `test_a_deadline_admits_more_draws_merged_so_the_default_is_the_per_block_loop`
  - `test_merged_sessions_equal_the_per_block_loop`
  - `test_the_merged_path_calls_the_fsrs_update_far_fewer_times`
  - `test_the_numeric_policy_merges_only_at_the_tag_with_its_switch`

## Modification guidance

- Make changes here when the responsibility remains value within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/value.py](../../../../../../src/learnloop/router_objective/value.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

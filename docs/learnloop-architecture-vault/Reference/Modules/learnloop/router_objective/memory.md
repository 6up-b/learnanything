---
title: "learnloop.router_objective.memory"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/memory.py"
source_paths:
  - "src/learnloop/router_objective/memory.py"
source_commit: "58b727566e28cefce7dcffe30042f0958b32bd6a"
source_commit_timestamp: "2026-11-06T00:16:59-05:00"
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
  - "learnloop.router_objective.memory module"
  - "src/learnloop/router_objective/memory.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.memory`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.memory` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO4 §8.4: the memory model the objective's rollouts read, vectorized over parameter draws.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py) |
| Source lines | 323 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `58b727566e28cefce7dcffe30042f0958b32bd6a` |
| Commit timestamp | `2026-11-06T00:16:59-05:00` |

## Public API

- `sigmoid(x: np.ndarray | float) -> np.ndarray` ([source](../../../../../../src/learnloop/router_objective/memory.py), line 75)
- `logit(p: np.ndarray | float) -> np.ndarray` ([source](../../../../../../src/learnloop/router_objective/memory.py), line 79)
- `class Combiner` ([source](../../../../../../src/learnloop/router_objective/memory.py), line 85) — The combination's coefficients: a posterior mean and variance each (diagonal), on ``form``'s parameters: ``(a0, aA, aR)`` for :data:`FORM_LINEAR`, ``(a0, log aA, log(aA − aR))`` for :data:`FORM_MONOTONE`.
  - `as_dict(self) -> dict[str, object]` (line 98; public)
  - `coefficients(self, z: np.ndarray) -> np.ndarray` (line 113; public) — ``(a0, aA, aR)`` per row of standard normal draws ``z`` shaped ``(K, 3)``: the posterior's draws.
  - `at_mean(self) -> 'Combiner'` (line 125; public) — No parameter uncertainty, each coefficient at its posterior mean (the belief's own world): a log-normal slope's mean is ``exp(μ + σ²/2)``, not its median.
- `monotone_prior(**fields: Any) -> Combiner` ([source](../../../../../../src/learnloop/router_objective/memory.py), line 135) — Landing ruling R6's labelled prior (:data:`FORM_MONOTONE`).
- `features(eta: np.ndarray, retrievability: np.ndarray | None, practiced: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/router_objective/memory.py), line 141) — The combiner's design columns ``(1, η, (logit R − η)·[practiced])``, stacked on the last axis.
- `perform(coefficients: np.ndarray, eta: np.ndarray, retrievability: np.ndarray, practiced: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/router_objective/memory.py), line 151) — ``P(perform)``: ``coefficients`` shaped ``(K, 3)`` against ``(K, N)`` sensors.
- `fit_combiner(rows: Sequence[tuple[float, float | None, int]], prior: Combiner | None=None) -> Combiner` ([source](../../../../../../src/learnloop/router_objective/memory.py), line 161) — The posterior of the combiner on ``(η, R or None, outcome 0/1)`` rows: a Laplace approximation by damped Newton on the log posterior (diagonal Gaussian prior).
- `class Fsrs` ([source](../../../../../../src/learnloop/router_objective/memory.py), line 266) — :mod:`learnloop.scheduling.fsrs`'s formulas over arrays (ratings: 1 again, 3 good).
  - `retrievability(self, stability: np.ndarray, elapsed: np.ndarray) -> np.ndarray` (line 274; public)
  - `_initial_difficulty(self, rating: np.ndarray) -> np.ndarray` (line 283; internal)
  - `review(self, difficulty: np.ndarray, stability: np.ndarray, practiced: np.ndarray, elapsed: np.ndarray, good: np.ndarray) -> tuple[np.ndarray, np.ndarray]` (line 287; public) — ``apply_review`` for each element: a first review where ``practiced`` is False.

### Module constants

- `MEMORY_MODEL_VERSION` ([src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py), line 37)
- `COMBINER_FIT_VERSION` ([src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py), line 40)
- `COMBINER_PRIOR_MEAN` ([src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py), line 42)
- `COMBINER_PRIOR_VARIANCE` ([src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py), line 43)
- `FORM_LINEAR` ([src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py), line 50)
- `FORM_MONOTONE` ([src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py), line 51)
- `_AA` ([src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py), line 64)
- `_B` ([src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py), line 65)
- `MONOTONE_PRIOR_MEAN` ([src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py), line 66)
- `MONOTONE_PRIOR_VARIANCE` ([src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py), line 67)
- `_R_CLIP` ([src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py), line 69)
- `_FIT_ITERATIONS` ([src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py), line 71)
- `_FIT_TOLERANCE` ([src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py), line 72)

### Explicit exports

`__all__` declares:

- `COMBINER_PRIOR_MEAN`
- `COMBINER_PRIOR_VARIANCE`
- `Combiner`
- `FORM_LINEAR`
- `FORM_MONOTONE`
- `Fsrs`
- `MEMORY_MODEL_VERSION`
- `MONOTONE_PRIOR_MEAN`
- `MONOTONE_PRIOR_VARIANCE`
- `features`
- `fit_combiner`
- `logit`
- `monotone_prior`
- `perform`
- `sigmoid`

## Internal implementation anchors

- `_log_normal(mean: float, variance: float) -> tuple[float, float]` ([source](../../../../../../src/learnloop/router_objective/memory.py), line 54) — The ``(μ, σ²)`` of the log-normal with this mean and variance (moment matching).
- `_fit_monotone(eta: np.ndarray, r: np.ndarray, practiced: np.ndarray, y: np.ndarray, prior: Combiner) -> Combiner` ([source](../../../../../../src/learnloop/router_objective/memory.py), line 207) — Landing ruling R6: the Laplace fit on :data:`FORM_MONOTONE`'s parameters ``θ = (a0, log aA, log b)``.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `module`; statically calls `Combiner`, `Fsrs`, `fit_combiner`, `monotone_prior`
- [[Reference/Modules/learnloop/router_objective/goal_read|learnloop.router_objective.goal_read]] — imports `module`; statically calls `Combiner`, `fit_combiner`
- [[Reference/Modules/learnloop/router_objective/value|learnloop.router_objective.value]] — imports `Combiner`, `Fsrs`, `logit`, `perform`, `sigmoid`; statically calls `Fsrs`, `logit`, `perform`, `sigmoid`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]], [[Reference/Modules/learnloop/router_objective/goal_read|learnloop.router_objective.goal_read]], [[Reference/Modules/learnloop/router_objective/value|learnloop.router_objective.value]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro4_value.py](../../../../../../tests/test_ro4_value.py) — direct import
  - `test_a_date_inside_a_long_action_is_scored_at_the_date_on_the_state_before_it`
  - `test_a_probe_is_scored_through_its_repair_branches`
  - `test_f12_a_goal_inside_the_continuation_session_sees_only_the_blocks_before_it`
  - `test_f12_one_draws_action_duration_never_moves_another_draws_clock`
  - `test_f5_a_sequence_values_its_steps_in_order_with_their_own_kinds`
  - `test_f7_a_refinement_cut_by_the_deadline_keeps_the_last_complete_batch`
  - `test_the_combiner_is_its_prior_without_outcomes_and_learns_with_them`
  - `test_the_gain_curve_rises_with_todays_minutes`
  - `test_the_same_theta_draw_is_used_across_candidates`
  - `test_the_vectorized_fsrs_is_the_scalar_one`
  - `test_v_recomputed_from_the_logged_rows_is_the_tails_next_action`
- [tests/test_ro5_calibration.py](../../../../../../tests/test_ro5_calibration.py) — direct import
  - `test_the_combiner_is_fitted_on_resolved_checks_and_is_its_prior_with_none`
- [tests/test_rofu_ad_link.py](../../../../../../tests/test_rofu_ad_link.py) — direct import
  - `test_a_decisions_p_bar_enters_as_ads_latent_and_reads_back_as_itself`
  - `test_the_probe_with_ads_own_predictive_is_pinned`
- [tests/test_rofu_ad_stable.py](../../../../../../tests/test_rofu_ad_stable.py) — direct import
  - `test_the_logit_is_stable_and_its_slope_matches_the_transformation`
- [tests/test_rofu_learning.py](../../../../../../tests/test_rofu_learning.py) — direct import
  - `test_the_combiner_is_fitted_on_trace_outcomes_at_the_tag_and_the_trace_names_it`
- [tests/test_rofu_monotone.py](../../../../../../tests/test_rofu_monotone.py) — direct import
  - `test_no_draw_of_a_fitted_posterior_has_a_negative_slope`
  - `test_the_linear_form_is_mvp049s_bitwise`
  - `test_the_linear_prior_has_negative_slopes_the_monotone_prior_has_none`
  - `test_the_monotone_fit_recovers_rising_slopes_and_is_the_posterior_mode`
  - `test_the_numeric_policy_reads_the_monotone_combiner_only_at_the_tag_with_its_switch`
  - `test_the_probe_before_and_after_r6_is_pinned`
  - `test_the_rollouts_on_the_monotone_prior_never_predict_lower_performance_for_higher_ability`
- [tests/test_rofu_review_draw.py](../../../../../../tests/test_rofu_review_draw.py) — direct import
  - `test_a_practised_topics_outcome_is_drawn_from_the_memory_models_own_p_perform`
  - `test_a_review_right_after_a_review_is_almost_never_a_lapse_with_the_switch_on`
- [tests/test_rofu_speed.py](../../../../../../tests/test_rofu_speed.py) — direct import
  - `test_the_fsrs_update_without_clip_equals_the_schedulers_scalar_formulas`
  - `test_the_merged_path_calls_the_fsrs_update_far_fewer_times`
- [tests/test_rospeed_ad_link.py](../../../../../../tests/test_rospeed_ad_link.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains memory within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

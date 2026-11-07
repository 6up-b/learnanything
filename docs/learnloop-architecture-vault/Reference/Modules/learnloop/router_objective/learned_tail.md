---
title: "learnloop.router_objective.learned_tail"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/learned_tail.py"
source_paths:
  - "src/learnloop/router_objective/learned_tail.py"
source_commit: "workspace/uncommitted @ HEAD bc9eadcc88232d3af229b26b721d88b037e39f7d"
source_commit_timestamp: "2026-11-07T01:13:16-05:00"
source_worktree_state: "modified"
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
  - "learnloop.router_objective.learned_tail module"
  - "src/learnloop/router_objective/learned_tail.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.learned_tail`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.learned_tail` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO6 (spec_router_objective_v1 §10): a learned tail.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py) |
| Source lines | 788 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD bc9eadcc88232d3af229b26b721d88b037e39f7d` |
| Commit timestamp | `2026-11-07T01:13:16-05:00` |

## Public API

- `names_for(features_version: str | None) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 107) — The feature names a features version reads (:data:`NAMES_LESSON` at TE3b's, else :data:`NAMES`).
- `class Belief` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 136) — The decision's state features (module docstring).
  - `as_tuple(self) -> tuple[float, ...]` (line 148; public)
- `class TopicNumbers` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 154) — One topic's belief numbers as the decision froze them (the trace's sensors, the value's ``Topic``).
- `belief(*, session_minutes: float | None, remembered: float | None, nearest_goal_days: float | None, horizon_days: float, pending_reports: int | float | None, mastery: Sequence[tuple[float, float]], topics: Sequence[TopicNumbers], cutoff_days: float | None=None) -> Belief` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 164) — The state features.
- `class ActionView` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 190) — One candidate's features' inputs.
- `kind_group(kind: str | None) -> str` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 199)
- `vector(state: Belief, action: ActionView, *, remembered: float | None, features_version: str=FEATURES_VERSION) -> tuple[float, ...]` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 209) — φ(x, a) in :func:`names_for` order (``features_version``: TE3b's adds the ``lesson`` indicator last).
- `class Transition` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 233) — One logged step of a frozen logger version, ready for the backup.
  - `target(self) -> float` (line 251; public) — The residual's part of the backup with no residual at ``x′``: ``R + V̄_tail′ − Q_tail``.
- `class Fit` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 258) — A fitted residual ``ρ = θᵀ((φ − mean)/sd)`` for one generator version (or the prior, ``θ = 0``).
  - `value(self, phi: Sequence[float]) -> float` (line 275; public)
  - `as_dict(self) -> dict[str, Any]` (line 279; public)
  - `from_dict(cls, data: Mapping[str, Any]) -> 'Fit'` (line 286; public)
- `prior_fit(prior_sd: float, generator: str | None=None, *, features_version: str=FEATURES_VERSION) -> Fit` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 296) — No transition: the prior, a residual of zero.
- `fit(transitions: Sequence[Transition], *, prior_sd: float, generator: str | None=None, features_version: str=FEATURES_VERSION) -> Fit` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 306) — FQE's fixed point for one frozen logger version under the labelled Gaussian prior (module docstring).
- `class Contrast` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 355) — One randomized stop-coin decision's realized and frozen predicted contrasts (offer stop vs the next block).
  - `bounds(self) -> tuple[float, float]` (line 378; public)
- `class WeightFit` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 385)
  - `as_dict(self) -> dict[str, Any]` (line 408; public)
- `spearman(x: Sequence[float], y: Sequence[float]) -> float | None` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 435) — Spearman's rank correlation (average ranks for ties); None where either side has no spread.
- `residual_weight(contrasts: Sequence[Contrast], *, prior_sd: float, at: str | None=None) -> WeightFit` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 451) — ``ŵ`` from the randomized contrasts whose windows closed before ``at`` (no peeking; module docstring).
- `coin_contrast(arm: str | None, rate: float) -> float` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 533) — The stop coin's mean-zero contrast in its logged probabilities: ``1[offer]/p − 1[present_next]/p``.
- `class CoinDraw` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 546) — One randomized stop-coin decision of the cohort (chosen on what was fixed before the coin: a frozen residual, stop in the support, a closed window) with its window's return: ``value`` the observed terms (None: no return at all, and why), ``[value + lo, value + hi]`` with its ``m…
- `coin_contrasts(draws: Sequence[CoinDraw]) -> tuple[list[Contrast], dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 572) — The randomized cohort's contrasts, every draw kept (Codex review of RO6, F1; RO6's landing ruling R1).
- `contrasts_hash(contrasts: Sequence[Contrast], record: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 645) — RO6's landing ruling R9: the hash of what calibrated ``ŵ`` (every contrast's realized value, interval, predictions, forcing, missing and excluded counts, and the cohort's status), exact (each float's ``repr``), so a trace's summary is checked against a recomputation from the led…
- `calibration_summary(contrasts: Sequence[Contrast], record: Mapping[str, Any], *, at: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 660) — RO6's landing ruling R9: what a trace keeps of ``ŵ``'s calibration, of a size that does not grow with the log: the contrasts' count and status, the cohort's counts by arm, the missing and excluded counts, the predictions' restriction counts and the hash of its inputs (:func:`con…
- `predicted_contrast(values: Mapping[str, float], mu: Mapping[str, float], stop_ref: str) -> float | None` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 680) — A frozen value's contrast between the coin's arms: stop minus the blocks at the mix's shares among them (what ``present_next`` serves where the mix drew stop, and the mix's own block elsewhere).
- `class WeightedRow` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 697) — One decision's importance ratio (the improvement step's probability of the served action over the logger's) and the window's observed return.
- `class Ratio` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 710) — One decision of the whole logged sequence and its importance ratio (None: not computable, e.g.
- `partial_history(rows: Sequence[WeightedRow], *, window_days: int, sequence: Sequence[Ratio] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 722) — Report only: importance-weighted estimates of the improvement step minus the logger on the window's return, one step (``(ρ_i − 1)·Ĝ_i``) and over each decision's window (the product of the ratios of **every** decision in it), each with its standard error and effective sample siz…

### Module constants

- `FEATURES_VERSION` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 81)
- `FIT_VERSION` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 82)
- `WEIGHT_VERSION` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 83)
- `LEAST_FAVOURABLE` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 85)
- `NO_BOUND` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 86)
- `BOUND_DEFINITION` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 88)
- `CROSS_CHECK_VERSION` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 91)
- `STATE_FEATURES` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 93)
- `ACTION_FEATURES` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 95)
- `NAMES` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 97)
- `FEATURES_VERSION_LESSON` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 102)
- `LESSON_KIND` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 103)
- `NAMES_LESSON` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 104)
- `_FIT_PASSES` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 113)
- `_FIT_TOLERANCE` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 114)
- `_TINY` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 116)
- `_NORMAL` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 118)
- `STOP_KIND` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 120)
- `READING_KIND` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 121)
- `PROBE_KIND` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 122)
- `OFFER_STOP` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 567)
- `PRESENT_NEXT` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 568)
- `UNIDENTIFIED` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 569)
- `CALIBRATION_SUMMARY_VERSION` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 642)
- `INCOMPLETE_HISTORY` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 719)

### Explicit exports

`__all__` declares:

- `ACTION_FEATURES`
- `ActionView`
- `Belief`
- `CROSS_CHECK_VERSION`
- `CoinDraw`
- `Contrast`
- `FEATURES_VERSION`
- `FEATURES_VERSION_LESSON`
- `FIT_VERSION`
- `Fit`
- `INCOMPLETE_HISTORY`
- `LESSON_KIND`
- `NAMES`
- `NAMES_LESSON`
- `names_for`
- `OFFER_STOP`
- `PRESENT_NEXT`
- `Ratio`
- `STATE_FEATURES`
- `TopicNumbers`
- `Transition`
- `UNIDENTIFIED`
- `WEIGHT_VERSION`
- `WeightFit`
- `WeightedRow`
- `coin_contrasts`
- `belief`
- `coin_contrast`
- `fit`
- `kind_group`
- `partial_history`
- `predicted_contrast`
- `prior_fit`
- `residual_weight`
- `spearman`
- `vector`

## Internal implementation anchors

- `_sigmoid(x: float) -> float` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 125)
- `_ranks(values: Sequence[float]) -> list[float]` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 420)
- `_parse(stamp: str) -> datetime` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 447)
- `_noise(x: np.ndarray, y: np.ndarray, precision: np.ndarray, sigma2: float) -> tuple[float, np.ndarray]` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 501) — The regression's noise at ``y``, refined from ``sigma2`` until it settles, and the coefficients of its last pass.
- `_slope_and_rank(rows: Sequence[Contrast], x: np.ndarray, y: np.ndarray, precision: np.ndarray, forced: Sequence[int]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 517) — The slope (posterior mean and sd of ``b``, the tail's ``a``) and the rank at the contrasts ``y``, the noise refined from ``y``'s mean square (module docstring).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]] — imports `module`; statically calls `ActionView`, `CoinDraw`, `Ratio`, `TopicNumbers`, `Transition`, `WeightedRow`, `belief`, `coin_contrasts`, `fit`, `names_for`, `partial_history`, `predicted_contrast`, `vector`
- [[Reference/Modules/learnloop/router_objective/tail_report|learnloop.router_objective.tail_report]] — imports `module`; statically calls `names_for`, `residual_weight`
- [[Reference/Modules/learnloop/router_objective/tail_serve|learnloop.router_objective.tail_serve]] — imports `module`; statically calls `ActionView`, `TopicNumbers`, `belief`, `calibration_summary`, `prior_fit`, `residual_weight`, `vector`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `hashlib`, `json`, `math`, `statistics`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]], [[Reference/Modules/learnloop/router_objective/tail_report|learnloop.router_objective.tail_report]], [[Reference/Modules/learnloop/router_objective/tail_serve|learnloop.router_objective.tail_serve]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro6_codex_rereview.py](../../../../../../tests/test_ro6_codex_rereview.py) — direct import
  - `test_f1_complete_returns_with_identical_arms_give_no_contrast`
  - `test_f1_observation_on_a_pre_coin_feature_leaves_the_contrast_unidentified`
  - `test_f3_the_backup_reads_the_values_and_features_at_the_carried_cutoff`
  - `test_f3_the_chooser_values_the_candidates_again_at_the_carried_cutoff`
  - `test_f7_an_earlier_builds_thirteen_features_are_rebuilt`
  - `test_f7_the_served_features_version_is_part_of_the_generator`
- [tests/test_ro6_codex_review.py](../../../../../../tests/test_ro6_codex_review.py) — direct import
  - `test_f1_an_arm_difference_in_observation_alone_is_no_contrast`
  - `test_f1_an_arm_with_no_observed_return_leaves_the_contrast_unidentified`
  - `test_f1_the_policy_arm_stays_a_zero_whatever_its_return`
  - `test_f4_a_diagnosis_queued_after_the_decisions_moment_never_enters_its_features`
  - `test_f6_a_window_with_a_decision_of_unknown_ratio_is_censored`
- [tests/test_ro6_landing.py](../../../../../../tests/test_ro6_landing.py) — direct import
  - `test_r10_selectively_skipped_checks_never_move_w_hat`
  - `test_r11_a_retention_density_change_with_no_goal_censors_the_transition_objective_changed`
  - `test_r13_the_fill_is_the_exact_minimum_of_the_bound_estimator_at_the_unbounded_noise`
  - `test_r1_complete_outcomes_recover_the_planted_slope_and_equal_the_unbounded_estimate`
  - `test_r1_selectively_missing_terms_never_move_w_hat`
  - `test_r2_a_goal_added_between_two_decisions_censors_the_transition_objective_changed`
  - `test_r7_a_planted_slope_on_supported_terms_is_recovered_beside_many_unsupported_at_the_draw`
  - `test_r7_codexs_reproductions_still_give_w_hat_zero`
  - `test_r7_support_removed_after_the_draw_in_one_arm_only_stays_bounded`
- [tests/test_ro6_learned_tail.py](../../../../../../tests/test_ro6_learned_tail.py) — direct import
  - `test_a_planted_residual_is_recovered_on_synthetic_trajectories`
  - `test_a_residual_that_predicts_nothing_keeps_w_hat_near_zero`
  - `test_the_coin_contrast_and_the_predicted_contrast`
  - `test_the_features_are_numbers_from_the_belief_and_the_candidate`
  - `test_the_fit_round_trips_through_its_trace_record`
  - `test_the_partial_history_weights_are_one_at_the_logger`
  - `test_the_prior_shrinks_a_short_noisy_trajectory_toward_no_residual`
  - `test_w_hat_is_zero_with_no_randomized_contrast`
  - `test_w_hat_moves_toward_the_planted_slope_with_randomized_contrasts`
  - `test_w_hat_reads_no_window_still_open_at_the_decision`
- [tests/test_ro6_serving.py](../../../../../../tests/test_ro6_serving.py) — direct import
  - `test_at_the_tag_the_trace_carries_the_residual_and_its_terms_recompute`
- [tests/test_rofu_carried.py](../../../../../../tests/test_rofu_carried.py) — direct import
- [tests/test_rofu_scope.py](../../../../../../tests/test_rofu_scope.py) — direct import
- [tests/test_te3b_binding.py](../../../../../../tests/test_te3b_binding.py) — direct import
- [tests/test_te3b_clock.py](../../../../../../tests/test_te3b_clock.py) — direct import
- [tests/test_te3b_features.py](../../../../../../tests/test_te3b_features.py) — direct import
  - `test_ro6s_features_gain_the_lesson_indicator_and_the_version_is_a_change_point`
- [tests/test_te3b_population.py](../../../../../../tests/test_te3b_population.py) — direct import
- [tests/test_te3b_value.py](../../../../../../tests/test_te3b_value.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains learned tail within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

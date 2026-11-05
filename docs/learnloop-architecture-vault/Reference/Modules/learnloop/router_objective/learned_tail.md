---
title: "learnloop.router_objective.learned_tail"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/learned_tail.py"
source_paths:
  - "src/learnloop/router_objective/learned_tail.py"
source_commit: "workspace/uncommitted @ HEAD 7f0d6dab15ed0523d22d635b677243892431ba12"
source_commit_timestamp: "2026-11-05T12:54:13-05:00"
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
| Source lines | 603 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 7f0d6dab15ed0523d22d635b677243892431ba12` |
| Commit timestamp | `2026-11-05T12:54:13-05:00` |

## Public API

- `class Belief` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 95) — The decision's state features (module docstring).
  - `as_tuple(self) -> tuple[float, ...]` (line 107; public)
- `class TopicNumbers` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 113) — One topic's belief numbers as the decision froze them (the trace's sensors, the value's ``Topic``).
- `belief(*, session_minutes: float | None, remembered: float | None, nearest_goal_days: float | None, horizon_days: float, pending_reports: int | float | None, mastery: Sequence[tuple[float, float]], topics: Sequence[TopicNumbers], cutoff_days: float | None=None) -> Belief` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 123) — The state features.
- `class ActionView` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 149) — One candidate's features' inputs.
- `kind_group(kind: str | None) -> str` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 158)
- `vector(state: Belief, action: ActionView, *, remembered: float | None) -> tuple[float, ...]` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 168) — φ(x, a) in :data:`NAMES` order.
- `class Transition` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 188) — One logged step of a frozen logger version, ready for the backup.
  - `target(self) -> float` (line 206; public) — The residual's part of the backup with no residual at ``x′``: ``R + V̄_tail′ − Q_tail``.
- `class Fit` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 213) — A fitted residual ``ρ = θᵀ((φ − mean)/sd)`` for one generator version (or the prior, ``θ = 0``).
  - `value(self, phi: Sequence[float]) -> float` (line 230; public)
  - `as_dict(self) -> dict[str, Any]` (line 234; public)
  - `from_dict(cls, data: Mapping[str, Any]) -> 'Fit'` (line 241; public)
- `prior_fit(prior_sd: float, generator: str | None=None) -> Fit` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 251) — No transition: the prior, a residual of zero.
- `fit(transitions: Sequence[Transition], *, prior_sd: float, generator: str | None=None) -> Fit` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 259) — FQE's fixed point for one frozen logger version under the labelled Gaussian prior (module docstring).
- `class Contrast` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 306) — One randomized stop-coin decision's realized and frozen predicted contrasts (offer stop vs the next block).
- `class WeightFit` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 323)
  - `as_dict(self) -> dict[str, Any]` (line 337; public)
- `spearman(x: Sequence[float], y: Sequence[float]) -> float | None` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 359) — Spearman's rank correlation (average ranks for ties); None where either side has no spread.
- `residual_weight(contrasts: Sequence[Contrast], *, prior_sd: float, at: str | None=None) -> WeightFit` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 375) — ``ŵ`` from the randomized contrasts whose windows closed before ``at`` (no peeking; module docstring).
- `coin_contrast(arm: str | None, rate: float) -> float` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 413) — The stop coin's mean-zero contrast in its logged probabilities: ``1[offer]/p − 1[present_next]/p``.
- `class CoinDraw` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 426) — One randomized stop-coin decision of the cohort (chosen on what was fixed before the coin: a frozen residual, stop in the support, a closed window) with its window's observed return (None: not observed, and why).
- `coin_contrasts(draws: Sequence[CoinDraw]) -> tuple[list[Contrast], dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 446) — The randomized cohort's contrasts, every draw kept (Codex review of RO6, F1).
- `predicted_contrast(values: Mapping[str, float], mu: Mapping[str, float], stop_ref: str) -> float | None` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 496) — A frozen value's contrast between the coin's arms: stop minus the blocks at the mix's shares among them (what ``present_next`` serves where the mix drew stop, and the mix's own block elsewhere).
- `class WeightedRow` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 513) — One decision's importance ratio (the improvement step's probability of the served action over the logger's) and the window's observed return.
- `class Ratio` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 526) — One decision of the whole logged sequence and its importance ratio (None: not computable, e.g.
- `partial_history(rows: Sequence[WeightedRow], *, window_days: int, sequence: Sequence[Ratio] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 538) — Report only: importance-weighted estimates of the improvement step minus the logger on the window's return, one step (``(ρ_i − 1)·Ĝ_i``) and over each decision's window (the product of the ratios of **every** decision in it), each with its standard error and effective sample siz…

### Module constants

- `FEATURES_VERSION` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 60)
- `FIT_VERSION` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 61)
- `WEIGHT_VERSION` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 62)
- `CROSS_CHECK_VERSION` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 63)
- `STATE_FEATURES` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 65)
- `ACTION_FEATURES` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 67)
- `NAMES` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 69)
- `_FIT_PASSES` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 72)
- `_FIT_TOLERANCE` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 73)
- `_TINY` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 75)
- `_NORMAL` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 77)
- `STOP_KIND` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 79)
- `READING_KIND` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 80)
- `PROBE_KIND` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 81)
- `OFFER_STOP` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 441)
- `PRESENT_NEXT` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 442)
- `UNIDENTIFIED` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 443)
- `INCOMPLETE_HISTORY` ([src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py), line 535)

### Explicit exports

`__all__` declares:

- `ACTION_FEATURES`
- `ActionView`
- `Belief`
- `CROSS_CHECK_VERSION`
- `CoinDraw`
- `Contrast`
- `FEATURES_VERSION`
- `FIT_VERSION`
- `Fit`
- `INCOMPLETE_HISTORY`
- `NAMES`
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

- `_sigmoid(x: float) -> float` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 84)
- `_ranks(values: Sequence[float]) -> list[float]` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 344)
- `_parse(stamp: str) -> datetime` ([source](../../../../../../src/learnloop/router_objective/learned_tail.py), line 371)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]] — imports `module`; statically calls `ActionView`, `CoinDraw`, `Ratio`, `TopicNumbers`, `Transition`, `WeightedRow`, `belief`, `coin_contrasts`, `fit`, `partial_history`, `predicted_contrast`, `vector`
- [[Reference/Modules/learnloop/router_objective/tail_report|learnloop.router_objective.tail_report]] — imports `module`; statically calls `residual_weight`
- [[Reference/Modules/learnloop/router_objective/tail_serve|learnloop.router_objective.tail_serve]] — imports `module`; statically calls `ActionView`, `TopicNumbers`, `belief`, `prior_fit`, `residual_weight`, `vector`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `math`, `statistics`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]], [[Reference/Modules/learnloop/router_objective/tail_report|learnloop.router_objective.tail_report]], [[Reference/Modules/learnloop/router_objective/tail_serve|learnloop.router_objective.tail_serve]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro6_codex_review.py](../../../../../../tests/test_ro6_codex_review.py) — direct import
  - `test_f1_an_arm_difference_in_observation_alone_is_no_contrast`
  - `test_f1_an_arm_with_no_observed_return_leaves_the_contrast_unidentified`
  - `test_f1_the_policy_arm_stays_a_zero_whatever_its_return`
  - `test_f3_the_next_state_is_valued_at_the_decisions_own_cutoff`
  - `test_f4_a_diagnosis_queued_after_the_decisions_moment_never_enters_its_features`
  - `test_f6_a_window_with_a_decision_of_unknown_ratio_is_censored`
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

## Modification guidance

- Make changes here when the responsibility remains learned tail within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/learned_tail.py](../../../../../../src/learnloop/router_objective/learned_tail.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

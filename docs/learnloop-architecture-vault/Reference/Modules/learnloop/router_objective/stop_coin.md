---
title: "learnloop.router_objective.stop_coin"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/stop_coin.py"
source_paths:
  - "src/learnloop/router_objective/stop_coin.py"
source_commit: "a7fdc90e67184aa039990ad48c89c8b8ee222104"
source_commit_timestamp: "2026-11-06T22:59:23-05:00"
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
  - "learnloop.router_objective.stop_coin module"
  - "src/learnloop/router_objective/stop_coin.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.stop_coin`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.stop_coin` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO5 §9 item 1: the stop coin, stop's return model and the hand-over of ``κ0`` from its seed to a posterior.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py) |
| Source lines | 645 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a7fdc90e67184aa039990ad48c89c8b8ee222104` |
| Commit timestamp | `2026-11-06T22:59:23-05:00` |

## Public API

- `arm_probabilities(rate: float) -> dict[str, float]` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 89)
- `class Coin` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 95)
  - `as_dict(self) -> dict[str, Any]` (line 108; public)
- `eligible(support: Sequence[str], *, session_minutes: float | None) -> bool` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 114) — A reversible boundary the coin applies at: stop beside at least one block, and the session already holds active minutes (landing ruling R4: an offer before any active minute in the session isn't a stop decision, since the learner has just chosen to start; unknown minutes are not…
- `served_distribution(mu: Mapping[str, float], rate: float, support: Sequence[str]) -> dict[str, float]` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 123) — ``P(served = a)`` under the coin and the mix together (module docstring), exactly.
- `flip(seed: str, rate: float, *, support: Sequence[str], mu: Mapping[str, float], drawn: str, availability: Mapping[str, Any]) -> Coin` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 136) — The coin for one decision: its arm from its own uniform (never the mix's), and what is served.
- `pending_assignment(coin: Coin, *, seed: str, support: Sequence[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 161) — The coin's ``policy_experiment_assignments`` row, frozen on the chooser's record and written with the decision (``assignments.record_pending``).
- `class Offer` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 179) — One offered stop with a response, as the likelihood reads it.
- `offer_log_likelihood(kappa0: float, offers: Sequence[Offer]) -> float` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 190) — Luce's form: ``P(continue) = G / (G + κ0·c)``; an offer whose forecast gain is not positive carries no information about ``κ0`` (the same probability on every grid point) and is skipped.
- `kappa_posterior(seed: float, log_sd: float, offers: Sequence[Offer]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 205) — The posterior over ``log κ0`` on a grid around the frozen seed; serves ``exp(E[log κ0])``.
- `offers(connection: Any) -> list[Offer]` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 268) — Every offered stop with a response, from the traces (the decision's forecast) and RO0's receipts.
- `handed_over(connection: Any, config: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 297) — κ0's posterior once a randomized offer has a response, else None (the daily seed stands).
- `class ReturnSlope` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 323) — ``b``'s posterior: the log return gap per remembered session of extra minutes.
  - `as_dict(self) -> dict[str, Any]` (line 331; public)
- `class ReturnRow` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 337) — One randomized coin with its session's outcome, as the return model reads it (Codex review F3).
- `fit_return_slope(rows: Sequence[ReturnRow], prior_sd: float) -> ReturnSlope` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 485) — ``b``, the log return gap per remembered session of extra minutes, identified by the randomized coin alone (Codex review F3): the coin is an instrument for where the session ends.
- `return_rows(connection: Any, *, gap_minutes: float, lessons: bool=False) -> list[ReturnRow]` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 590) — Every coin drawn in a session whose return is observed: its arm's contrast, the availability frozen before its draw, and its session's final minutes and return gap (:class:`ReturnRow`).

### Module constants

- `VERSION` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 67)
- `KAPPA_VERSION` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 68)
- `RETURN_VERSION` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 69)
- `RETURN_ASSUMPTION` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 72)
- `OFFER_STOP` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 73)
- `PRESENT_NEXT` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 74)
- `POLICY` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 75)
- `ARMS` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 76)
- `STOP` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 77)
- `FORCED` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 79)
- `SEED_REGIME` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 81)
- `POSTERIOR_REGIME` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 82)
- `POSTERIOR` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 83)
- `GRID` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 85)
- `_TINY` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 86)
- `_REACH` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 376)
- `_PEAK_SPREADS` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 377)
- `_PRIOR_NODES` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 378)
- `_LOCAL_NODES` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 379)
- `_SPAN_NODES` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 380)
- `_REFINEMENTS` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 381)
- `_WIDENINGS` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 382)
- `_TOLERANCE` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 383)
- `_TAIL_TOLERANCE` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 384)
- `_COLLINEAR` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 385)

### Explicit exports

`__all__` declares:

- `ARMS`
- `Coin`
- `FORCED`
- `KAPPA_VERSION`
- `OFFER_STOP`
- `Offer`
- `POLICY`
- `POSTERIOR`
- `POSTERIOR_REGIME`
- `PRESENT_NEXT`
- `RETURN_ASSUMPTION`
- `RETURN_VERSION`
- `ReturnRow`
- `ReturnSlope`
- `SEED_REGIME`
- `VERSION`
- `arm_probabilities`
- `eligible`
- `fit_return_slope`
- `flip`
- `handed_over`
- `kappa_posterior`
- `offer_log_likelihood`
- `offers`
- `pending_assignment`
- `return_rows`
- `served_distribution`

## Internal implementation anchors

- `_decision_stop_responses(connection: Any) -> dict[str, str]` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 227) — Each stop decision's response: ``overridden`` (a stop_response naming it) or ``accepted`` (an end naming it, the offered stop taken).
- `_gain(trace: Mapping[str, Any]) -> tuple[float | None, float | None]` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 248) — The next block's forecast gain before its own price, over the accepted stop, and that price per κ0.
- `_residuals(values: Sequence[float], design: Sequence[Sequence[float]]) -> list[float]` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 355) — ``values`` less their least-squares fit on the pre-draw ``design`` (with an intercept): availability's own part of the outcome, removed for precision only (the coin's mean-zero contrast is independent of it).
- `class _Moments` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 389) — The session-level sums the Anderson-Rubin statistic needs, ``U_s(b) = A_s − b·B_s``.
- `_session_moments(rows: Sequence[ReturnRow]) -> tuple[_Moments, int]` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 410) — One estimating contribution per session (Codex re-review F9).
- `_integrate(nodes: Any, log_density: Any) -> tuple[float, float, float]` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 435) — Trapezoidal log mass, mean and variance of ``exp(log_density)`` over sorted ``nodes`` (an array; unequal spacing kept).
- `_refine(nodes: Any) -> Any` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 453)
- `_log_prior_tail(beyond: float, sd: float) -> float` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 462) — ``log ∫_beyond^∞ exp(−x²/(2sd²)) dx``: the posterior's unnormalized density is at most the prior's kernel (``AR ≥ 0``), so this bounds the mass the integration leaves out past a bound on the log density's own scale.
- `_nodes(sd: float, peak: tuple[float, float] | None, low: float, high: float) -> Any` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 474) — The prior's range, the likelihood's peak neighbourhood and the span between the bounds, merged and sorted.
- `_parse(stamp: str) -> datetime` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 573)
- `_contrast(arm: str, detail: Mapping[str, Any], propensity: float) -> float` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 577) — The coin's mean-zero contrast in its logged probabilities (offer against present-next).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `eligible`, `flip`, `handed_over`, `pending_assignment`, `served_distribution`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `module`; statically calls `fit_return_slope`, `return_rows`
- [[Reference/Modules/learnloop/router_objective/calibration_report|learnloop.router_objective.calibration_report]] — imports `module`; statically calls `_decision_stop_responses`, `fit_return_slope`, `handed_over`, `return_rows`
- [[Reference/Modules/learnloop/router_objective/objective_report|learnloop.router_objective.objective_report]] — imports `module`
- [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]] — imports `module`
- [[Reference/Modules/learnloop/router_objective/tail_data|learnloop.router_objective.tail_data]] — imports `module`; statically calls `served_distribution`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/router/mixture|learnloop.router.mixture]] — imports `module`; calls `_pick`, `uniform`
- [[Reference/Modules/learnloop/router_objective/assignments|learnloop.router_objective.assignments]] — imports `module`; calls `rows`
- [[Reference/Modules/learnloop/router_objective/price|learnloop.router_objective.price]] — imports `module`; calls `session_active_minutes`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `json`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]], [[Reference/Modules/learnloop/router_objective/calibration_report|learnloop.router_objective.calibration_report]], [[Reference/Modules/learnloop/router_objective/objective_report|learnloop.router_objective.objective_report]], [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_v2_landing_fixes.py](../../../../../../tests/test_mobile_v2_landing_fixes.py) — direct import
  - `test_r2_done_for_today_on_a_pending_stop_records_that_stop_accepted`
  - `test_r2_keep_going_after_done_on_a_pending_stop_is_the_overridden_response`
- [tests/test_ro5_codex_rereview.py](../../../../../../tests/test_ro5_codex_rereview.py) — direct import
  - `test_f3_a_busy_and_a_free_session_carry_no_return_benefit`
  - `test_f8_a_strong_instrument_far_from_the_prior_keeps_its_resolution`
  - `test_f8_a_vanishing_first_stage_leaves_the_prior_never_an_extreme_certain_slope`
  - `test_f9_a_few_sessions_never_make_the_slope_certain`
  - `test_f9_opposing_coins_in_one_session_never_give_a_certain_slope`
- [tests/test_ro5_codex_review.py](../../../../../../tests/test_ro5_codex_review.py) — direct import
  - `test_f3_a_confounded_return_is_not_read_as_a_return_effect`
  - `test_f3_a_planted_causal_slope_is_recovered_through_the_coin`
- [tests/test_ro5_landing.py](../../../../../../tests/test_ro5_landing.py) — direct import
  - `test_r2_a_planted_slope_is_recovered_at_a_narrow_and_at_a_wide_prior`
  - `test_r2_a_weak_instrument_keeps_the_priors_resolution_and_bounds`
  - `test_r2_an_integration_that_cannot_converge_leaves_the_labelled_prior`
  - `test_r2_f11_the_dominant_posterior_peak_outside_the_priors_reach_is_integrated`
  - `test_r4_the_coin_is_not_drawn_before_any_active_minute_of_the_session`
  - `test_r6_the_return_models_assumption_is_labelled_in_the_trace_and_the_report`
- [tests/test_ro5_stop_coin.py](../../../../../../tests/test_ro5_stop_coin.py) — direct import
  - `test_a_planted_return_slope_is_recovered`
  - `test_kappa_stays_the_seed_until_a_randomized_offer_has_a_response`
  - `test_present_next_overrides_only_a_drawn_stop`
  - `test_serving_records_each_coin_with_its_exact_probability_and_availability`
  - `test_the_arms_have_exact_probabilities_and_the_served_distribution_is_exact`
  - `test_the_coin_never_depends_on_the_mix_or_either_policy`
  - `test_the_posterior_with_no_observation_is_the_seed_and_responses_move_it_both_ways`
- [tests/test_ro6_codex_rereview.py](../../../../../../tests/test_ro6_codex_rereview.py) — direct import
  - `test_f1_observation_on_a_pre_coin_feature_leaves_the_contrast_unidentified`
- [tests/test_ro6_codex_review.py](../../../../../../tests/test_ro6_codex_review.py) — direct import
  - `test_f1_an_arm_difference_in_observation_alone_is_no_contrast`
  - `test_f1_an_arm_with_no_observed_return_leaves_the_contrast_unidentified`
  - `test_f1_the_policy_arm_stays_a_zero_whatever_its_return`
- [tests/test_ro6_landing.py](../../../../../../tests/test_ro6_landing.py) — direct import
  - `test_r1_selectively_missing_terms_never_move_w_hat`
  - `test_r4_a_coin_draw_superseded_by_a_waiting_follow_up_is_used_intent_to_treat`
  - `test_r7_a_planted_slope_on_supported_terms_is_recovered_beside_many_unsupported_at_the_draw`
  - `test_r7_support_removed_after_the_draw_in_one_arm_only_stays_bounded`
- [tests/test_te3b_offers.py](../../../../../../tests/test_te3b_offers.py) — direct import
  - `test_g3_mu_recomputes_with_an_offer_in_the_support_on_every_path`

## Modification guidance

- Make changes here when the responsibility remains stop coin within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

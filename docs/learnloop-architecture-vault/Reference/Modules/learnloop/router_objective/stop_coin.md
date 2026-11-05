---
title: "learnloop.router_objective.stop_coin"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/stop_coin.py"
source_paths:
  - "src/learnloop/router_objective/stop_coin.py"
source_commit: "workspace/uncommitted @ HEAD 9a47277b99a9e26c348ea9fea39644fe8799654a"
source_commit_timestamp: "2026-11-05T08:45:43-05:00"
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
| Source lines | 481 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 9a47277b99a9e26c348ea9fea39644fe8799654a` |
| Commit timestamp | `2026-11-05T08:45:43-05:00` |

## Public API

- `arm_probabilities(rate: float) -> dict[str, float]` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 81)
- `class Coin` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 87)
  - `as_dict(self) -> dict[str, Any]` (line 100; public)
- `eligible(support: Sequence[str]) -> bool` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 106) — A reversible boundary the coin applies at: stop beside at least one block.
- `served_distribution(mu: Mapping[str, float], rate: float, support: Sequence[str]) -> dict[str, float]` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 112) — ``P(served = a)`` under the coin and the mix together (module docstring), exactly.
- `flip(seed: str, rate: float, *, support: Sequence[str], mu: Mapping[str, float], drawn: str, availability: Mapping[str, Any]) -> Coin` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 125) — The coin for one decision: its arm from its own uniform (never the mix's), and what is served.
- `pending_assignment(coin: Coin, *, seed: str, support: Sequence[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 150) — The coin's ``policy_experiment_assignments`` row, frozen on the chooser's record and written with the decision (``assignments.record_pending``).
- `class Offer` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 168) — One offered stop with a response, as the likelihood reads it.
- `offer_log_likelihood(kappa0: float, offers: Sequence[Offer]) -> float` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 179) — Luce's form: ``P(continue) = G / (G + κ0·c)``; an offer whose forecast gain is not positive carries no information about ``κ0`` (the same probability on every grid point) and is skipped.
- `kappa_posterior(seed: float, log_sd: float, offers: Sequence[Offer]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 194) — The posterior over ``log κ0`` on a grid around the frozen seed; serves ``exp(E[log κ0])``.
- `offers(connection: Any) -> list[Offer]` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 255) — Every offered stop with a response, from the traces (the decision's forecast) and RO0's receipts.
- `handed_over(connection: Any, config: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 284) — κ0's posterior once a randomized offer has a response, else None (the daily seed stands).
- `class ReturnSlope` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 310) — ``b``'s posterior: the log return gap per remembered session of extra minutes.
  - `as_dict(self) -> dict[str, Any]` (line 318; public)
- `class ReturnRow` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 324) — One randomized coin with its session's outcome, as the return model reads it (Codex review F3).
- `fit_return_slope(rows: Sequence[ReturnRow], prior_sd: float) -> ReturnSlope` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 354) — ``b``, the log return gap per remembered session of extra minutes, identified by the randomized coin alone (Codex review F3): the coin is an instrument for where the session ends.
- `return_rows(connection: Any, *, gap_minutes: float) -> list[ReturnRow]` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 427) — Every coin drawn in a session whose return is observed: its arm's contrast, the availability frozen before its draw, and its session's final minutes and return gap (:class:`ReturnRow`).

### Module constants

- `VERSION` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 62)
- `KAPPA_VERSION` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 63)
- `RETURN_VERSION` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 64)
- `OFFER_STOP` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 65)
- `PRESENT_NEXT` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 66)
- `POLICY` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 67)
- `ARMS` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 68)
- `STOP` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 69)
- `FORCED` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 71)
- `SEED_REGIME` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 73)
- `POSTERIOR_REGIME` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 74)
- `POSTERIOR` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 75)
- `GRID` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 77)
- `_TINY` ([src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py), line 78)

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

- `_decision_stop_responses(connection: Any) -> dict[str, str]` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 216) — Each stop decision's response: ``overridden`` (a stop_response naming it) or ``accepted`` (an end naming it, the offered stop taken).
- `_gain(trace: Mapping[str, Any]) -> tuple[float | None, float | None]` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 235) — The next block's forecast gain before its own price, over the accepted stop, and that price per κ0.
- `_residuals(values: Sequence[float], design: Sequence[Sequence[float]]) -> list[float]` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 342) — ``values`` less their least-squares fit on the pre-draw ``design`` (with an intercept): availability's own part of the outcome, removed for precision only (the coin's mean-zero contrast is independent of it).
- `_parse(stamp: str) -> datetime` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 410)
- `_contrast(arm: str, detail: Mapping[str, Any], propensity: float) -> float` ([source](../../../../../../src/learnloop/router_objective/stop_coin.py), line 414) — The coin's mean-zero contrast in its logged probabilities (offer against present-next).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `eligible`, `flip`, `handed_over`, `pending_assignment`, `served_distribution`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `module`; statically calls `fit_return_slope`, `return_rows`
- [[Reference/Modules/learnloop/router_objective/calibration_report|learnloop.router_objective.calibration_report]] — imports `module`; statically calls `_decision_stop_responses`, `fit_return_slope`, `handed_over`, `return_rows`
- [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]] — imports `module`

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

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]], [[Reference/Modules/learnloop/router_objective/calibration_report|learnloop.router_objective.calibration_report]], [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro5_codex_review.py](../../../../../../tests/test_ro5_codex_review.py) — direct import
  - `test_f3_a_confounded_return_is_not_read_as_a_return_effect`
  - `test_f3_a_planted_causal_slope_is_recovered_through_the_coin`
- [tests/test_ro5_stop_coin.py](../../../../../../tests/test_ro5_stop_coin.py) — direct import
  - `test_a_planted_return_slope_is_recovered`
  - `test_kappa_stays_the_seed_until_a_randomized_offer_has_a_response`
  - `test_present_next_overrides_only_a_drawn_stop`
  - `test_serving_records_each_coin_with_its_exact_probability_and_availability`
  - `test_the_arms_have_exact_probabilities_and_the_served_distribution_is_exact`
  - `test_the_coin_never_depends_on_the_mix_or_either_policy`
  - `test_the_posterior_with_no_observation_is_the_seed_and_responses_move_it_both_ways`

## Modification guidance

- Make changes here when the responsibility remains stop coin within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/stop_coin.py](../../../../../../src/learnloop/router_objective/stop_coin.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

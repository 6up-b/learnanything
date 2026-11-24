---
title: "learnloop.router_objective.probe_coin"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/probe_coin.py"
source_paths:
  - "src/learnloop/router_objective/probe_coin.py"
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
  - "learnloop.router_objective.probe_coin module"
  - "src/learnloop/router_objective/probe_coin.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.probe_coin`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.probe_coin` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: G2: the probe coin, the randomized share of probes the router asks while it cannot value them.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/probe_coin.py](../../../../../../src/learnloop/router_objective/probe_coin.py) |
| Source lines | 134 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `share(config: Any) -> float` ([source](../../../../../../src/learnloop/router_objective/probe_coin.py), line 49) — The share of eligible misses the coin asks the probe on: the stop coin's rate (module docstring).
- `applies(rate: float) -> bool` ([source](../../../../../../src/learnloop/router_objective/probe_coin.py), line 55) — Whether the coin is flipped: a positive share.
- `seed_for(boundary_key: str, decision_id: str) -> str` ([source](../../../../../../src/learnloop/router_objective/probe_coin.py), line 61) — The coin's own seed for one decision: a function of the boundary and the decision, never the mix's seed.
- `draw_uniform(seed: str) -> float` ([source](../../../../../../src/learnloop/router_objective/probe_coin.py), line 67) — The coin's uniform, from its own seed.
- `arm_probabilities(rate: float) -> dict[str, float]` ([source](../../../../../../src/learnloop/router_objective/probe_coin.py), line 73)
- `served_distribution(mu: Mapping[str, float], rate: float, *, probe_ref: str) -> dict[str, float]` ([source](../../../../../../src/learnloop/router_objective/probe_coin.py), line 78) — ``P(served = a)`` under the coin and the mix together, exactly: the probe at ``rate``, every option of the mix at ``(1 − rate)·μ``.
- `class Coin` ([source](../../../../../../src/learnloop/router_objective/probe_coin.py), line 89)
  - `as_dict(self) -> dict[str, Any]` (line 101; public)
- `flip(seed: str, rate: float, *, probe_ref: str, mu: Mapping[str, float], drawn: str, boundary_key: str='') -> Coin` ([source](../../../../../../src/learnloop/router_objective/probe_coin.py), line 107) — The coin for one decision: its arm from its own uniform, and what is served (the probe, or the mix's draw).
- `pending_assignment(coin: Coin, *, seed: str, support: Sequence[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/probe_coin.py), line 120) — The coin's ``policy_experiment_assignments`` row, frozen on the decision's record and written with the decision (``assignments.record_pending``).

### Module constants

- `VERSION` ([src/learnloop/router_objective/probe_coin.py](../../../../../../src/learnloop/router_objective/probe_coin.py), line 39)
- `STAGE` ([src/learnloop/router_objective/probe_coin.py](../../../../../../src/learnloop/router_objective/probe_coin.py), line 41)
- `ASK` ([src/learnloop/router_objective/probe_coin.py](../../../../../../src/learnloop/router_objective/probe_coin.py), line 42)
- `POLICY` ([src/learnloop/router_objective/probe_coin.py](../../../../../../src/learnloop/router_objective/probe_coin.py), line 43)
- `ARMS` ([src/learnloop/router_objective/probe_coin.py](../../../../../../src/learnloop/router_objective/probe_coin.py), line 44)
- `RATE_SOURCE` ([src/learnloop/router_objective/probe_coin.py](../../../../../../src/learnloop/router_objective/probe_coin.py), line 46)

### Explicit exports

`__all__` declares:

- `ARMS`
- `ASK`
- `Coin`
- `POLICY`
- `RATE_SOURCE`
- `STAGE`
- `VERSION`
- `applies`
- `arm_probabilities`
- `draw_uniform`
- `flip`
- `pending_assignment`
- `seed_for`
- `served_distribution`
- `share`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/learner_probe|learnloop.daily_plan.learner_probe]] — imports `module`; statically calls `applies`, `flip`, `pending_assignment`, `seed_for`, `served_distribution`, `share`
- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `applies`, `flip`, `pending_assignment`, `seed_for`, `served_distribution`, `share`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `module`; statically calls `applies`, `flip`, `pending_assignment`, `seed_for`, `served_distribution`, `share`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/router/mixture|learnloop.router.mixture]] — imports `module`; calls `uniform`
- [[Reference/Modules/learnloop/router_objective/assignments|learnloop.router_objective.assignments]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/learner_probe|learnloop.daily_plan.learner_probe]], [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/diagnosis_journey_helpers.py](../../../../../../tests/diagnosis_journey_helpers.py) — direct import
- [tests/probe_router_owned_helpers.py](../../../../../../tests/probe_router_owned_helpers.py) — direct import
- [tests/test_probe_router.py](../../../../../../tests/test_probe_router.py) — direct import
  - `test_at_the_tag_an_unwritten_probe_is_not_an_option_of_either_policy`
  - `test_at_the_tag_the_coin_asks_the_probe_now_with_its_exact_propensity`
  - `test_at_the_tag_the_lane_logs_the_coin_with_its_decision`
  - `test_at_the_tag_with_no_plan_the_coin_decides_and_the_decision_is_logged`
  - `test_the_coin_serves_the_probe_below_the_share_and_the_mix_otherwise`
  - `test_the_probe_coin_has_its_own_seed_and_experiment_independent_of_the_stop_coin`
  - `test_the_served_distribution_is_exact_and_sums_to_one`
  - `test_the_share_is_the_stop_coins_rate_read_through_one_function`
- [tests/test_probe_router_continuation.py](../../../../../../tests/test_probe_router_continuation.py) — direct import
- [tests/test_probe_router_decision_integrity.py](../../../../../../tests/test_probe_router_decision_integrity.py) — direct import
  - `test_r11_the_learner_lane_reads_the_automatic_lanes_decision_and_flips_no_coin`
  - `test_r18_a_retry_draws_the_same_coin_and_a_receipt_never_stands_for_another_status`
- [tests/test_probe_router_learner_lane.py](../../../../../../tests/test_probe_router_learner_lane.py) — direct import
  - `test_an_unlearned_probe_is_offered_only_by_the_coin_with_its_exact_propensity`

## Modification guidance

- Make changes here when the responsibility remains probe coin within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/probe_coin.py](../../../../../../src/learnloop/router_objective/probe_coin.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

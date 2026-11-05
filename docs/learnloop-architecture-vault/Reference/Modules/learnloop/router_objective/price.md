---
title: "learnloop.router_objective.price"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/price.py"
source_paths:
  - "src/learnloop/router_objective/price.py"
source_commit: "838d8ee1fcee48de3b5b41f59e451f042ec9a690"
source_commit_timestamp: "2026-11-05T04:03:05-05:00"
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
  - "learnloop.router_objective.price module"
  - "src/learnloop/router_objective/price.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.price`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.price` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO4 §8.6: the attention price ``κ(x) = κ0·x/m̄`` on session minutes, its daily seed, guard and posterior.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py) |
| Source lines | 162 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `838d8ee1fcee48de3b5b41f59e451f042ec9a690` |
| Commit timestamp | `2026-11-05T04:03:05-05:00` |

## Public API

- `session_active_minutes(connection: Any, *, now: str, gap_minutes: float) -> tuple[float, str | None, dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/price.py), line 51) — The active minutes of the current objective session: activity (attempts at their completion with their latency, Reader visits over their interval) walked back from ``now`` until a gap of ``gap_minutes``.
- `guard_minutes(config: Any, remembered: float) -> float` ([source](../../../../../../src/learnloop/router_objective/price.py), line 92)
- `class Seeded` ([source](../../../../../../src/learnloop/router_objective/price.py), line 99)
  - `as_dict(self) -> dict[str, Any]` (line 106; public)
- `seed_from_gain(gain: Mapping[float, float], *, remembered: float, block_minutes: float, last_positive: float | None) -> tuple[float, str]` ([source](../../../../../../src/learnloop/router_objective/price.py), line 112) — ``κ0`` from the day's gain curve: the marginal gain per minute at ``m̄``, floored at the last positive value; with none ever and no positive marginal, the tail's average marginal gain per minute.
- `choice_log_likelihood(kappa0: float, observations: Iterable[Mapping[str, float]]) -> float` ([source](../../../../../../src/learnloop/router_objective/price.py), line 128) — The stated likelihood: ``P(continue) = σ(gain − price)`` per frontier choice, the price at that choice's session minutes (``κ0·x/m̄`` over the block); a stop says only that the forecast gain was below the price.
- `grid_posterior(seed: float, observations: Sequence[Mapping[str, float]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/price.py), line 142) — The grid posterior over ``κ0``: a log-uniform grid around the seed, prior uniform on it.

### Module constants

- `PRICE_VERSION` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 32)
- `SEED` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 33)
- `DAY_SEED` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 35)
- `CARRIED_DAY` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 36)
- `CARRIED_LAST` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 37)
- `TAIL_AVERAGE` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 38)
- `FLOORED` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 39)
- `GUARD_MULTIPLE` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 41)
- `GRID_MULTIPLES` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 43)
- `_STAMP` ([src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py), line 44)

### Explicit exports

`__all__` declares:

- `CARRIED_DAY`
- `CARRIED_LAST`
- `DAY_SEED`
- `FLOORED`
- `GRID_MULTIPLES`
- `GUARD_MULTIPLE`
- `PRICE_VERSION`
- `SEED`
- `Seeded`
- `TAIL_AVERAGE`
- `choice_log_likelihood`
- `grid_posterior`
- `guard_minutes`
- `seed_from_gain`
- `session_active_minutes`

## Internal implementation anchors

- `_parse(stamp: str) -> datetime` ([source](../../../../../../src/learnloop/router_objective/price.py), line 47)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `Seeded`, `guard_minutes`, `seed_from_gain`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `module`; statically calls `session_active_minutes`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro4_price.py](../../../../../../tests/test_ro4_price.py) — direct import
  - `test_a_session_ends_after_a_gap_of_session_gap_minutes`
  - `test_the_grid_posterior_is_its_prior_with_nothing_fed_and_learns_from_choices`
  - `test_the_runaway_guard_is_three_remembered_minutes_unless_set`
  - `test_the_seed_is_the_days_marginal_gain_floored_at_the_last_positive_value`

## Modification guidance

- Make changes here when the responsibility remains price within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/price.py](../../../../../../src/learnloop/router_objective/price.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

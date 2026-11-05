---
title: "learnloop.router_objective.memory"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/memory.py"
source_paths:
  - "src/learnloop/router_objective/memory.py"
source_commit: "f6e46ff9d1c47643fdb8d2c1c934ce177092f37b"
source_commit_timestamp: "2026-11-05T02:22:58-05:00"
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
| Source lines | 184 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `f6e46ff9d1c47643fdb8d2c1c934ce177092f37b` |
| Commit timestamp | `2026-11-05T02:22:58-05:00` |

## Public API

- `sigmoid(x: np.ndarray | float) -> np.ndarray` ([source](../../../../../../src/learnloop/router_objective/memory.py), line 43)
- `logit(p: np.ndarray | float) -> np.ndarray` ([source](../../../../../../src/learnloop/router_objective/memory.py), line 47)
- `class Combiner` ([source](../../../../../../src/learnloop/router_objective/memory.py), line 53) — The combination's coefficients (a0, aA, aR): a posterior mean and variance each (diagonal).
  - `as_dict(self) -> dict[str, object]` (line 61; public)
- `features(eta: np.ndarray, retrievability: np.ndarray | None, practiced: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/router_objective/memory.py), line 66) — The combiner's design columns ``(1, η, (logit R − η)·[practiced])``, stacked on the last axis.
- `perform(coefficients: np.ndarray, eta: np.ndarray, retrievability: np.ndarray, practiced: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/router_objective/memory.py), line 76) — ``P(perform)``: ``coefficients`` shaped ``(K, 3)`` against ``(K, N)`` sensors.
- `fit_combiner(rows: Sequence[tuple[float, float | None, int]], prior: Combiner | None=None) -> Combiner` ([source](../../../../../../src/learnloop/router_objective/memory.py), line 86) — The posterior of the combiner on ``(η, R or None, outcome 0/1)`` rows: a Laplace approximation by damped Newton on the log posterior (diagonal Gaussian prior).
- `class Fsrs` ([source](../../../../../../src/learnloop/router_objective/memory.py), line 136) — :mod:`learnloop.scheduling.fsrs`'s formulas over arrays (ratings: 1 again, 3 good).
  - `retrievability(self, stability: np.ndarray, elapsed: np.ndarray) -> np.ndarray` (line 141; public)
  - `_initial_difficulty(self, rating: np.ndarray) -> np.ndarray` (line 149; internal)
  - `review(self, difficulty: np.ndarray, stability: np.ndarray, practiced: np.ndarray, elapsed: np.ndarray, good: np.ndarray) -> tuple[np.ndarray, np.ndarray]` (line 153; public) — ``apply_review`` for each element: a first review where ``practiced`` is False.

### Module constants

- `MEMORY_MODEL_VERSION` ([src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py), line 32)
- `COMBINER_PRIOR_MEAN` ([src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py), line 34)
- `COMBINER_PRIOR_VARIANCE` ([src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py), line 35)
- `_R_CLIP` ([src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py), line 37)
- `_FIT_ITERATIONS` ([src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py), line 39)
- `_FIT_TOLERANCE` ([src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py), line 40)

### Explicit exports

`__all__` declares:

- `COMBINER_PRIOR_MEAN`
- `COMBINER_PRIOR_VARIANCE`
- `Combiner`
- `Fsrs`
- `MEMORY_MODEL_VERSION`
- `features`
- `fit_combiner`
- `logit`
- `perform`
- `sigmoid`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `module`; statically calls `Combiner`
- [[Reference/Modules/learnloop/router_objective/value|learnloop.router_objective.value]] — imports `Combiner`, `Fsrs`, `perform`, `sigmoid`; statically calls `Fsrs`, `perform`, `sigmoid`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `math`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]], [[Reference/Modules/learnloop/router_objective/value|learnloop.router_objective.value]].

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

## Modification guidance

- Make changes here when the responsibility remains memory within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/memory.py](../../../../../../src/learnloop/router_objective/memory.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.router.mixture"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router/mixture.py"
source_paths:
  - "src/learnloop/router/mixture.py"
source_commit: "9218ba7a856652fb4091a4d048fdc4cb77d0ee84"
source_commit_timestamp: "2026-11-02T07:45:40-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router.mixture module"
  - "src/learnloop/router/mixture.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router"
---

# `learnloop.router.mixture`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router/_package|learnloop.router]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router.mixture` exists within [[Reference/Modules/learnloop/router/_package|learnloop.router]] to own the behavior summarized by its module contract: Router R2b: the logged model mixture (``model_mixture``) and its exact propensities.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router/mixture.py](../../../../../../src/learnloop/router/mixture.py) |
| Source lines | 257 |
| Owning package | [[Reference/Modules/learnloop/router/_package|learnloop.router]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `9218ba7a856652fb4091a4d048fdc4cb77d0ee84` |
| Commit timestamp | `2026-11-02T07:45:40-05:00` |

## Public API

- `class MixtureError(ValueError)` ([source](../../../../../../src/learnloop/router/mixture.py), line 57) — The mixture's inputs cannot give an exact distribution.
- `effective_weights(weights: Mapping[str, float], failed: Sequence[str] | set[str] | frozenset[str]) -> dict[str, float]` ([source](../../../../../../src/learnloop/router/mixture.py), line 61) — The configured weights, normalized, with each failed model's weight moved to staged.
- `fallback_label(failed: Sequence[str] | set[str] | frozenset[str]) -> str | None` ([source](../../../../../../src/learnloop/router/mixture.py), line 78) — ``decider`` | ``llm`` | ``both`` (the receipt's ``fallback``), or None.
- `normalized(distribution: Mapping[str, float] | None, support: Sequence[str]) -> dict[str, float] | None` ([source](../../../../../../src/learnloop/router/mixture.py), line 89) — A component's distribution over ``support`` (missing refs are 0), renormalized.
- `component_distributions(support: Sequence[str], staged_ref: str, models: Mapping[str, Mapping[str, float] | None]) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/router/mixture.py), line 106) — Every component's distribution over the support (a failed model's is absent).
- `mixture(support: Sequence[str], components: Mapping[str, Mapping[str, float]], weights: Mapping[str, float], epsilon: float) -> dict[str, float]` ([source](../../../../../../src/learnloop/router/mixture.py), line 121) — ``pi`` over the support (exact; sums to one).
- `seed_for(boundary_key: str, decision_id: str) -> str` ([source](../../../../../../src/learnloop/router/mixture.py), line 142) — The decision's seed: a hash of its boundary key and its id.
- `uniform(seed: str, stage: str) -> float` ([source](../../../../../../src/learnloop/router/mixture.py), line 148) — A uniform in [0, 1) from the seed (53 bits of a SHA-256).
- `class Draw` ([source](../../../../../../src/learnloop/router/mixture.py), line 156)
  - `deterministic(self) -> bool` (line 166; public)
- `draw(support: Sequence[str], components: Mapping[str, Mapping[str, float]], weights: Mapping[str, float], epsilon: float, seed: str) -> Draw` ([source](../../../../../../src/learnloop/router/mixture.py), line 186) — The two-stage draw; its marginal is :func:`mixture`.
- `draw_with_uniforms(support: Sequence[str], components: Mapping[str, Mapping[str, float]], weights: Mapping[str, float], epsilon: float, u1: float, u2: float) -> Draw` ([source](../../../../../../src/learnloop/router/mixture.py), line 199) — :func:`draw` with its two uniforms given (a caller that derives its own from its seed, such as teacher TE1b's day draw, which needs a third for its show coin).
- `recompute(record: Mapping[str, Any]) -> float` ([source](../../../../../../src/learnloop/router/mixture.py), line 224) — G3: ``pi(chosen)`` from a logged decision's own components.

### Module constants

- `DESIGN` ([src/learnloop/router/mixture.py](../../../../../../src/learnloop/router/mixture.py), line 45)
- `POLICY` ([src/learnloop/router/mixture.py](../../../../../../src/learnloop/router/mixture.py), line 46)
- `STAGED_POLICY` ([src/learnloop/router/mixture.py](../../../../../../src/learnloop/router/mixture.py), line 48)
- `COMPONENTS` ([src/learnloop/router/mixture.py](../../../../../../src/learnloop/router/mixture.py), line 49)
- `MODEL_COMPONENTS` ([src/learnloop/router/mixture.py](../../../../../../src/learnloop/router/mixture.py), line 50)
- `UNIFORM` ([src/learnloop/router/mixture.py](../../../../../../src/learnloop/router/mixture.py), line 52)
- `DETERMINISTIC_TOLERANCE` ([src/learnloop/router/mixture.py](../../../../../../src/learnloop/router/mixture.py), line 54)

### Explicit exports

`__all__` declares:

- `COMPONENTS`
- `DESIGN`
- `DETERMINISTIC_TOLERANCE`
- `Draw`
- `MODEL_COMPONENTS`
- `MixtureError`
- `POLICY`
- `STAGED_POLICY`
- `UNIFORM`
- `component_distributions`
- `draw`
- `draw_with_uniforms`
- `effective_weights`
- `fallback_label`
- `mixture`
- `normalized`
- `recompute`
- `seed_for`
- `uniform`

## Internal implementation anchors

- `_pick(order: Sequence[str], distribution: Mapping[str, float], u: float) -> str` ([source](../../../../../../src/learnloop/router/mixture.py), line 170)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]] — imports `module`; statically calls `component_distributions`, `draw`, `effective_weights`, `fallback_label`
- [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]] — imports `uniform`; statically calls `uniform`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `seed_for`; statically calls `seed_for`
- [[Reference/Modules/learnloop/router/lesson_suggestions|learnloop.router.lesson_suggestions]] — imports `module`; statically calls `component_distributions`, `draw_with_uniforms`, `effective_weights`, `uniform`
- [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]] — imports `module`; statically calls `uniform`
- [[Reference/Modules/learnloop/router_objective/mix|learnloop.router_objective.mix]] — imports `module`; statically calls `Draw`, `_pick`, `normalized`, `uniform`
- [[Reference/Modules/learnloop/router_objective/picks|learnloop.router_objective.picks]] — imports `module`; statically calls `uniform`
- [[Reference/Modules/learnloop/router_objective/stop_coin|learnloop.router_objective.stop_coin]] — imports `module`; statically calls `_pick`, `uniform`
- [[Reference/Modules/learnloop/scheduling/randomization_layer|learnloop.scheduling.randomization_layer]] — imports `module`; statically calls `component_distributions`, `draw`, `effective_weights`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/router_chooser|learnloop.daily_plan.router_chooser]], [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]], [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]], [[Reference/Modules/learnloop/router/lesson_suggestions|learnloop.router.lesson_suggestions]], [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/router_model_fakes.py](../../../../../../tests/router_model_fakes.py) — direct import
- [tests/test_data_capture_a5_not_ready_floor.py](../../../../../../tests/test_data_capture_a5_not_ready_floor.py) — direct import
  - `test_a_model_that_answers_is_untouched`
  - `test_not_ready_draws_from_the_fallback_distribution_with_its_floor_and_exact_propensity`
  - `test_the_draw_reproduces_from_its_logged_seed`
  - `test_the_floor_can_draw_another_option_than_the_rules`
  - `test_the_restraint_keeps_the_floor_on_not_ready_too`
- [tests/test_followup_router.py](../../../../../../tests/test_followup_router.py) — direct import
  - `test_no_intervention_sits_in_the_mixture_with_its_floor`
- [tests/test_ih5_successor.py](../../../../../../tests/test_ih5_successor.py) — direct import
  - `test_a_lesson_offer_in_the_support_can_be_drawn_when_the_llm_has_no_answer`
- [tests/test_plan_determinism_landing.py](../../../../../../tests/test_plan_determinism_landing.py) — direct import
  - `test_staged_plans_at_mvp024_are_the_same_in_every_session_and_at_start`
  - `test_the_floor_binds_where_the_models_put_no_mass`
  - `test_the_mixture_draws_over_the_same_candidates_in_every_session`
- [tests/test_ro5_landing.py](../../../../../../tests/test_ro5_landing.py) — direct import
- [tests/test_ro5_stop_coin.py](../../../../../../tests/test_ro5_stop_coin.py) — direct import
  - `test_the_arms_have_exact_probabilities_and_the_served_distribution_is_exact`
- [tests/test_router_g3_propensity.py](../../../../../../tests/test_router_g3_propensity.py) — direct import
  - `test_the_logged_propensity_is_reproducible_from_the_logged_components`
  - `test_the_two_stage_marginal_is_the_mixture`
- [tests/test_router_r2b_serving.py](../../../../../../tests/test_router_r2b_serving.py) — direct import
- [tests/test_te3b_offers.py](../../../../../../tests/test_te3b_offers.py) — direct import
- [tests/test_teacher_te1b_rereview_fixes.py](../../../../../../tests/test_teacher_te1b_rereview_fixes.py) — direct import
  - `test_mixture_mode_draws_the_target_by_the_routers_model_mixture`

## Modification guidance

- Make changes here when the responsibility remains mixture within learnloop.router; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router/mixture.py](../../../../../../src/learnloop/router/mixture.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

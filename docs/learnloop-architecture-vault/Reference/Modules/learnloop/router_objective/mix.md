---
title: "learnloop.router_objective.mix"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/mix.py"
source_paths:
  - "src/learnloop/router_objective/mix.py"
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
  - "learnloop.router_objective.mix module"
  - "src/learnloop/router_objective/mix.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.mix`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.mix` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO4 §8.3: the served distribution of the two policies' learned mix, exact and logged (G3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py) |
| Source lines | 133 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `838d8ee1fcee48de3b5b41f59e451f042ec9a690` |
| Commit timestamp | `2026-11-05T04:03:05-05:00` |

## Public API

- `class ObjectiveMixError(ValueError)` ([source](../../../../../../src/learnloop/router_objective/mix.py), line 34) — The mix's inputs cannot give an exact distribution.
- `effective_weights(w: float, failed: Sequence[str] | set[str] | frozenset[str]) -> dict[str, float]` ([source](../../../../../../src/learnloop/router_objective/mix.py), line 38) — ``{staged, llm, numeric}``: ``w`` to the LLM policy and ``1 − w`` to the numeric one, each failed policy's share moved to ``staged`` (failure redistribution exactly as §8.3 writes it).
- `fallback_label(failed: Sequence[str] | set[str] | frozenset[str]) -> str | None` ([source](../../../../../../src/learnloop/router_objective/mix.py), line 53)
- `one_hot(support: Sequence[str], ref: str) -> dict[str, float]` ([source](../../../../../../src/learnloop/router_objective/mix.py), line 60)
- `components(support: Sequence[str], staged_ref: str, *, llm: Mapping[str, float] | None, numeric_ref: str | None) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/router_objective/mix.py), line 66) — Every live component's distribution over the support (a failed policy's is absent).
- `mu(support: Sequence[str], parts: Mapping[str, Mapping[str, float]], weights: Mapping[str, float], epsilon: float) -> dict[str, float]` ([source](../../../../../../src/learnloop/router_objective/mix.py), line 80)
- `draw(support: Sequence[str], parts: Mapping[str, Mapping[str, float]], weights: Mapping[str, float], epsilon: float, seed: str) -> mx.Draw` ([source](../../../../../../src/learnloop/router_objective/mix.py), line 92) — The two-stage draw (its marginal is :func:`mu`).
- `seed_for(boundary_key: str, decision_id: str) -> str` ([source](../../../../../../src/learnloop/router_objective/mix.py), line 111)
- `recompute(record: Mapping[str, Any]) -> dict[str, float]` ([source](../../../../../../src/learnloop/router_objective/mix.py), line 117) — G3: ``μ`` over the support from a logged decision's own values (``support``, ``staged_ref``, ``epsilon``, ``w``, ``failed``, ``llm_distribution``, ``numeric_choice``).

### Module constants

- `DESIGN` ([src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py), line 25)
- `POLICY` ([src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py), line 26)
- `LLM` ([src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py), line 27)
- `NUMERIC` ([src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py), line 28)
- `STAGED` ([src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py), line 29)
- `COMPONENTS` ([src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py), line 30)
- `POLICIES` ([src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py), line 31)

### Explicit exports

`__all__` declares:

- `COMPONENTS`
- `DESIGN`
- `LLM`
- `NUMERIC`
- `ObjectiveMixError`
- `POLICIES`
- `POLICY`
- `STAGED`
- `components`
- `draw`
- `effective_weights`
- `fallback_label`
- `mu`
- `one_hot`
- `recompute`
- `seed_for`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `components`, `draw`, `effective_weights`, `fallback_label`, `seed_for`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/router/mixture|learnloop.router.mixture]] — imports `module`; calls `Draw`, `_pick`, `normalized`, `uniform`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro4_codex_review.py](../../../../../../tests/test_ro4_codex_review.py) — direct import
  - `test_f1_a_slow_llm_leaves_the_numeric_share_in_place`
- [tests/test_ro4_objective_serving.py](../../../../../../tests/test_ro4_objective_serving.py) — direct import
  - `test_a_failed_llm_moves_only_its_share_to_staged`
  - `test_a_numeric_timeout_is_a_failure_and_both_failed_keeps_the_floor`
  - `test_both_policies_mix_with_exact_propensities_and_the_decider_is_advice`
  - `test_the_seed_reproduces_the_draw`
  - `test_with_no_model_the_numeric_policy_serves_with_stop_in_every_support`

## Modification guidance

- Make changes here when the responsibility remains mix within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/mix.py](../../../../../../src/learnloop/router_objective/mix.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

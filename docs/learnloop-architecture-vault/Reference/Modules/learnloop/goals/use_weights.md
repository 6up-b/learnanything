---
title: "learnloop.goals.use_weights"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/goals/use_weights.py"
source_paths:
  - "src/learnloop/goals/use_weights.py"
source_commit: "93929d6875bd7cf04bfe5e375527a1d2f805fd7e"
source_commit_timestamp: "2026-11-05T04:02:41-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.goals"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.goals.use_weights module"
  - "src/learnloop/goals/use_weights.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-goals"
---

# `learnloop.goals.use_weights`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.goals.use_weights` exists within [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] to own the behavior summarized by its module contract: Router objective RO4 §8.5: a goal's use weights, the objective's preferences about what knowledge is for.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/goals/use_weights.py](../../../../../../src/learnloop/goals/use_weights.py) |
| Source lines | 98 |
| Owning package | [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `93929d6875bd7cf04bfe5e375527a1d2f805fd7e` |
| Commit timestamp | `2026-11-05T04:02:41-05:00` |

## Public API

- `class UseWeights` ([source](../../../../../../src/learnloop/goals/use_weights.py), line 30)
  - `for_lo(self, lo: str) -> float` (line 37; public)
  - `as_dict(self) -> dict[str, Any]` (line 40; public)
- `config_defaults(config: Any) -> dict[str, float]` ([source](../../../../../../src/learnloop/goals/use_weights.py), line 45)
- `for_goal(goal: Any, repository: Any, config: Any) -> UseWeights` ([source](../../../../../../src/learnloop/goals/use_weights.py), line 62) — The weights in force for ``goal`` (module docstring's order).
- `copy_at_creation(config: Any, *, dated: float | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/use_weights.py), line 89) — The ``use_weight`` a goal is created with at the tag: the asked weight (or the config's default) and the config's undated density, copied now.

### Module constants

- `CONTRACT` ([src/learnloop/goals/use_weights.py](../../../../../../src/learnloop/goals/use_weights.py), line 24)
- `COPIED` ([src/learnloop/goals/use_weights.py](../../../../../../src/learnloop/goals/use_weights.py), line 25)
- `DEFAULT` ([src/learnloop/goals/use_weights.py](../../../../../../src/learnloop/goals/use_weights.py), line 26)

### Explicit exports

`__all__` declares:

- `CONTRACT`
- `COPIED`
- `DEFAULT`
- `UseWeights`
- `config_defaults`
- `copy_at_creation`
- `for_goal`

## Internal implementation anchors

- `_parsed(value: Any) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/goals/use_weights.py), line 51)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `for_goal`; statically calls `for_goal`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `COPIED`, `copy_at_creation`, `for_goal`; statically calls `copy_at_creation`, `for_goal`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `config_defaults`, `copy_at_creation`; statically calls `config_defaults`, `copy_at_creation`
- [[Reference/Modules/learnloop_sidecar/handlers/router_objective|learnloop_sidecar.handlers.router_objective]] — imports `for_goal`; statically calls `for_goal`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `canonical_use_weight`; calls `canonical_use_weight`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]], [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]], [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]], [[Reference/Modules/learnloop_sidecar/handlers/router_objective|learnloop_sidecar.handlers.router_objective]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro4_goals.py](../../../../../../tests/test_ro4_goals.py) — direct import
  - `test_a_copy_made_at_creation_is_read_and_a_config_change_does_not_move_it`
  - `test_create_goal_copies_the_asked_use_weight_or_the_default_when_left_alone`
  - `test_the_stated_default_for_a_goal_with_no_contract_and_no_copy`

## Modification guidance

- Change use weights policy here when goals owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/goals/use_weights.py](../../../../../../src/learnloop/goals/use_weights.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

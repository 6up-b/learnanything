---
title: "learnloop.learner.blueprint_projection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/blueprint_projection.py"
source_paths:
  - "src/learnloop/learner/blueprint_projection.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Inspect Persistent State"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner.blueprint_projection module"
  - "src/learnloop/learner/blueprint_projection.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.blueprint_projection`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.blueprint_projection` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Blueprint likelihood projections (knowledge-model §9.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/blueprint_projection.py](../../../../../../src/learnloop/learner/blueprint_projection.py) |
| Source lines | 392 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ComponentReadiness` ([source](../../../../../../src/learnloop/learner/blueprint_projection.py), line 65)
  - `as_dict(self) -> dict[str, object]` (line 72; public)
- `class RecipeProjection` ([source](../../../../../../src/learnloop/learner/blueprint_projection.py), line 83)
  - `as_dict(self) -> dict[str, object]` (line 90; public)
- `class BlueprintProjection` ([source](../../../../../../src/learnloop/learner/blueprint_projection.py), line 101)
  - `as_dict(self) -> dict[str, object]` (line 108; public)
- `class LoReadiness` ([source](../../../../../../src/learnloop/learner/blueprint_projection.py), line 119)
  - `as_dict(self) -> dict[str, object]` (line 126; public)
- `guess_floor_for_item(item: PracticeItem, config) -> float` ([source](../../../../../../src/learnloop/learner/blueprint_projection.py), line 164) — The selected-response guess floor for an item (§9.2).
- `project_recipe(recipe: BlueprintRecipe, component_recall: ComponentRecall, *, slip: float, guess: float) -> RecipeProjection` ([source](../../../../../../src/learnloop/learner/blueprint_projection.py), line 205) — Success probability for one recipe (§9.2 recipe core).
- `project_blueprint(blueprint: Blueprint, component_recall: ComponentRecall, *, slip: float, guess: float) -> BlueprintProjection` ([source](../../../../../../src/learnloop/learner/blueprint_projection.py), line 264) — Success probability for one blueprint = max over its applicable recipes.
- `project_lo_readiness(learning_object: LearningObject, component_recall: ComponentRecall, *, slip: float, guess: float=0.0) -> LoReadiness` ([source](../../../../../../src/learnloop/learner/blueprint_projection.py), line 290) — ``readiness(lo) = Σ blueprint.weight × P(success)`` (§9.2), weight-normalized.
- `item_exercised_recipes(vault: LoadedVault, item: PracticeItem, learning_object: LearningObject) -> list[BlueprintRecipe]` ([source](../../../../../../src/learnloop/learner/blueprint_projection.py), line 347) — Recipes an item exercises, via its criteria ``recipe_ids`` (§5.1/§7.2).
- `predict_item_success(vault: LoadedVault, item: PracticeItem, learning_object: LearningObject, component_recall: ComponentRecall) -> float | None` ([source](../../../../../../src/learnloop/learner/blueprint_projection.py), line 370) — P(success) on a specific item via the blueprint recipes it exercises (§9.2).

### Module constants

- `GATING_MODALITIES` ([src/learnloop/learner/blueprint_projection.py](../../../../../../src/learnloop/learner/blueprint_projection.py), line 52)
- `COMPENSATORY_COMPOSITIONS` ([src/learnloop/learner/blueprint_projection.py](../../../../../../src/learnloop/learner/blueprint_projection.py), line 57)
- `_NEUTRAL_PRIOR` ([src/learnloop/learner/blueprint_projection.py](../../../../../../src/learnloop/learner/blueprint_projection.py), line 61)

## Internal implementation anchors

- `_product(values: list[float]) -> float` ([source](../../../../../../src/learnloop/learner/blueprint_projection.py), line 136)
- `_weighted_geometric_mean(pairs: list[tuple[float, float]]) -> float` ([source](../../../../../../src/learnloop/learner/blueprint_projection.py), line 143) — ``Π p_i^(w_i / Σ w)`` over (recall, weight) pairs; 1.0 when empty.
- `_n_options(item: PracticeItem) -> int | None` ([source](../../../../../../src/learnloop/learner/blueprint_projection.py), line 180) — Best-effort option count from a structured expected answer; None if unknown.
- `_gating_conjuncts(recipe: BlueprintRecipe) -> list[RecipeComponent]` ([source](../../../../../../src/learnloop/learner/blueprint_projection.py), line 192) — The components that materially gate this recipe's likelihood (§8.2).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/goals/exam_readiness|learnloop.goals.exam_readiness]] — imports `project_blueprint`; statically calls `project_blueprint`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `LoReadiness`, `project_lo_readiness`; statically calls `project_lo_readiness`
- [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]] — imports `LoReadiness`
- [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]] — imports `predict_item_success`; statically calls `predict_item_success`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `clamp`; calls `clamp`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `Blueprint`, `BlueprintRecipe`, `LearningObject`, `LoadedVault`, `PracticeItem`, `RecipeComponent`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/goals/exam_readiness|learnloop.goals.exam_readiness]], [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]], [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]], [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_anti_double_count.py](../../../../../../tests/test_anti_double_count.py) — direct import
  - `test_anti_double_count_projection_deterministic_and_idempotent`
- [tests/test_blueprint_projection.py](../../../../../../tests/test_blueprint_projection.py) — direct import
  - `test_alternative_recipe_success_does_not_credit_bypassed_requirement`
  - `test_any_of_uses_strongest_alternative`
  - `test_compensatory_composition_is_geometric_mean`
  - `test_conjunctive_bottleneck_not_averaged_away`
  - `test_conjunctive_recipe_is_noisy_and_with_slip`
  - `test_facilitating_component_does_not_drag_readiness`
  - `test_integration_facet_enters_as_conjunct`
  - `test_lo_readiness_is_weight_normalized_sum`
  - `test_lo_without_blueprints_returns_none`
  - `test_path_specific_failure_affects_only_the_exercised_path`
  - `test_selected_response_adds_guess_floor`
- [tests/test_km3_projections.py](../../../../../../tests/test_km3_projections.py) — direct import
  - `test_readiness_rises_when_components_improve`
- [tests/test_today_surfaces.py](../../../../../../tests/test_today_surfaces.py) — direct import
  - `test_blueprint_weight_by_facet_sums_referencing_blueprints`

## Modification guidance

- Change blueprint projection policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/blueprint_projection.py](../../../../../../src/learnloop/learner/blueprint_projection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

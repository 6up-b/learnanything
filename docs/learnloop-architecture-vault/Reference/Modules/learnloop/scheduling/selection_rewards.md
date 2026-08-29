---
title: "learnloop.scheduling.selection_rewards"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/selection_rewards.py"
source_paths:
  - "src/learnloop/scheduling/selection_rewards.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.selection_rewards module"
  - "src/learnloop/scheduling/selection_rewards.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.selection_rewards`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps selection rewards behavior inside its owning package, [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]]. Its public surface centers on `SchedulerIntent`, `LearnerAbilityVector`, `ItemDemandVector`, `SelectionReward`, `score_selection_reward`, `ability_vector`, `probe_information_gain_components`, `item_demand_vector` and 2 more public symbols.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/selection_rewards.py](../../../../../../src/learnloop/scheduling/selection_rewards.py) |
| Source lines | 624 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class SchedulerIntent(str, Enum)` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 23)
- `class LearnerAbilityVector` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 32)
  - `as_dict(self) -> dict[str, object]` (line 41; public)
- `class ItemDemandVector` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 54)
  - `as_dict(self) -> dict[str, object]` (line 67; public)
- `class SelectionReward` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 84)
  - `as_components(self) -> dict[str, float]` (line 94; public)
  - `as_debug(self) -> dict[str, object]` (line 101; public)
- `score_selection_reward(vault: LoadedVault, item: PracticeItem, learning_object: LearningObject, *, mastery: MasteryState | None, facet_states: list[FacetRecallState], quality_state: PracticeItemQualityState | None, active_errors: list[ActiveErrorEvent], base_components: dict[str, float], probe_eig: float, probe_familiarity_discount: float=1.0, intent: SchedulerIntent) -> SelectionReward` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 137)
- `ability_vector(learning_object_id: str, mastery: MasteryState | None, facet_states: list[FacetRecallState], active_errors: list[ActiveErrorEvent], *, facet_aliases: dict[str, str] | None=None) -> LearnerAbilityVector` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 270)
- `probe_information_gain_components(ability: LearnerAbilityVector, demand: ItemDemandVector, *, hypothesis_eig: float, independent_evidence_discount: float=1.0) -> dict[str, object]` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 298) — MVP entropy-reduction decomposition for probe reward.
- `item_demand_vector(vault: LoadedVault, item: PracticeItem, learning_object: LearningObject, quality_state: PracticeItemQualityState | None) -> ItemDemandVector` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 394)
- `predicted_correctness_from_vectors(ability: LearnerAbilityVector, demand: ItemDemandVector, facet_blend_evidence_count: float) -> float` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 460)
- `predicted_facet_recall(mastery_logit_mean: float | None, mastery_evidence_count: int, facet_mean: float | None, facet_mass: float, blend_evidence_count: float) -> float` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 476) — Facet-level predicted recall: LO-mastery backbone, facet evidence overlay.

### Module constants

- `TEACH_BACK_REWARD_FLOOR` ([src/learnloop/scheduling/selection_rewards.py](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 20)
- `_SHAPE_CACHE` ([src/learnloop/scheduling/selection_rewards.py](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 120)

## Internal implementation anchors

- `_item_shape(vault: LoadedVault, item: PracticeItem) -> ItemShape` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 123)
- `_aggregate_facet_states(facet_states: list[FacetRecallState], facet_aliases: dict[str, str]) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 361)
- `_predicted_correctness(vault: LoadedVault, item: PracticeItem, learning_object: LearningObject, ability: LearnerAbilityVector, demand: ItemDemandVector, mastery: MasteryState | None) -> float` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 419) — Item predicted correctness — blueprint likelihood under mvp-0.7, else legacy.
- `_gradient_fit(predicted_correctness: float, intent: SchedulerIntent) -> float` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 516)
- `_facet_weakness(ability: LearnerAbilityVector, demand: ItemDemandVector) -> float` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 528)
- `_facet_uncertainty(ability: LearnerAbilityVector, demand: ItemDemandVector) -> float` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 533)
- `_targeted_boundary_fit(ability: LearnerAbilityVector, demand: ItemDemandVector, gradient_fit: float) -> float` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 537)
- `_repair_value(demand: ItemDemandVector, ability: LearnerAbilityVector, active_errors: list[ActiveErrorEvent]) -> float` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 560)
- `_overload_penalty(predicted_correctness: float, intent: SchedulerIntent) -> float` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 574)
- `_weighted_facet_value(values: dict[str, float], weights: dict[str, float], *, default: float) -> float` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 582)
- `_mode_retrieval_demand(practice_mode: str) -> float` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 590)
- `_inferred_scaffold_level(item: PracticeItem) -> float` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 602)
- `_default_attempt_type_for_reward(item: PracticeItem, intent: SchedulerIntent) -> str` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 608)
- `_sigmoid(value: float) -> float` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 614)
- `_logit(value: float) -> float` ([source](../../../../../../src/learnloop/scheduling/selection_rewards.py), line 622)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]] — imports `ability_vector`, `item_demand_vector`, `predicted_correctness_from_vectors`; statically calls `ability_vector`, `item_demand_vector`, `predicted_correctness_from_vectors`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `predicted_facet_recall`; statically calls `predicted_facet_recall`
- [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]] — imports `predicted_facet_recall`; statically calls `predicted_facet_recall`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `SchedulerIntent`, `score_selection_reward`; statically calls `score_selection_reward`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `predicted_facet_recall`; statically calls `predicted_facet_recall`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/ability_transition|learnloop.attempts.ability_transition]] — imports `estimate_ability_transition`; calls `estimate_ability_transition`
- [[Reference/Modules/learnloop/content/authoring/conjunctive_items|learnloop.content.authoring.conjunctive_items]] — imports `ItemShape`, `classify_item_shape`, `conjunctive_fit`; calls `classify_item_shape`, `conjunctive_fit`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ActiveErrorEvent`, `FacetRecallState`, `MasteryState`, `PracticeItemQualityState`
- [[Reference/Modules/learnloop/learner/blueprint_projection|learnloop.learner.blueprint_projection]] — imports `predict_item_success`; calls `predict_item_success`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `is_canonical_state_vault`; calls `is_canonical_state_vault`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `item_irt_params`; calls `item_irt_params`
- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `clamp`; calls `clamp`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LearningObject`, `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `enum`, `math`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/goals/exam_session|learnloop.goals.exam_session]], [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]], [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]], [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]], [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_goal_frontier.py](../../../../../../tests/test_goal_frontier.py) — direct import
  - `test_repair_reward_includes_goal_frontier_term`
- [tests/test_measurement_state_labels.py](../../../../../../tests/test_measurement_state_labels.py) — direct import
  - `test_ignorance_is_unknown_and_never_inferred`
  - `test_label_does_not_move_a_threshold_a_number_or_a_certification`
  - `test_pooled_prediction_that_rendered_unlabelled_now_carries_inferred`
- [tests/test_predicted_facet_recall.py](../../../../../../tests/test_predicted_facet_recall.py) — direct import
  - `test_absent_mastery_falls_back_to_facet_then_half`
  - `test_facet_mass_saturation_pulls_toward_facet_mean`
  - `test_informed_mastery_dominates_at_low_mass`
  - `test_monotone_in_facet_mass_when_facet_beats_mastery`
  - `test_result_is_clamped`
  - `test_thin_mastery_evidence_cannot_suppress_strong_facet_evidence`
  - `test_zero_evidence_mastery_row_is_uninformative`
- [tests/test_scheduler.py](../../../../../../tests/test_scheduler.py) — direct import
  - `test_selection_propensities_greedy_when_disabled_or_singleton_or_probe`

## Modification guidance

- Change selection rewards policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/selection_rewards.py](../../../../../../src/learnloop/scheduling/selection_rewards.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.scheduling.fsrs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/fsrs.py"
source_paths:
  - "src/learnloop/scheduling/fsrs.py"
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
  - "learnloop.scheduling.fsrs module"
  - "src/learnloop/scheduling/fsrs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.fsrs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps fsrs behavior inside its owning package, [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]]. Its public surface centers on `Rating`, `MemoryState`, `forgetting_curve`, `initial_stability`, `initial_difficulty`, `next_difficulty`, `next_forget_stability`, `next_recall_stability` and 3 more public symbols.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/fsrs.py](../../../../../../src/learnloop/scheduling/fsrs.py) |
| Source lines | 156 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class Rating(IntEnum)` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 10)
- `class MemoryState` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 49)
- `forgetting_curve(stability: float | None, elapsed_days: float, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS) -> float` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 55)
- `initial_stability(rating: Rating, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS) -> float` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 63)
- `initial_difficulty(rating: Rating, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS) -> float` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 67)
- `next_difficulty(difficulty: float, rating: Rating, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS) -> float` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 71)
- `next_forget_stability(difficulty: float, stability: float, retrievability: float, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS) -> float` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 79)
- `next_recall_stability(difficulty: float, stability: float, retrievability: float, rating: Rating, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS) -> float` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 94)
- `apply_review(previous: MemoryState | None, rating: Rating, elapsed_days: float, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS) -> MemoryState` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 117)
- `interval_for_retention(stability: float, desired_retention: float=0.9, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS) -> float` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 137)
- `rating_from_score(score: int, max_points: int=4) -> Rating` ([source](../../../../../../src/learnloop/scheduling/fsrs.py), line 148)

### Module constants

- `FSRS6_DEFAULT_WEIGHTS` ([src/learnloop/scheduling/fsrs.py](../../../../../../src/learnloop/scheduling/fsrs.py), line 19)
- `S_MIN` ([src/learnloop/scheduling/fsrs.py](../../../../../../src/learnloop/scheduling/fsrs.py), line 43)
- `D_MIN` ([src/learnloop/scheduling/fsrs.py](../../../../../../src/learnloop/scheduling/fsrs.py), line 44)
- `D_MAX` ([src/learnloop/scheduling/fsrs.py](../../../../../../src/learnloop/scheduling/fsrs.py), line 45)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `FSRS6_DEFAULT_WEIGHTS`, `MemoryState`, `Rating`, `apply_review`, `interval_for_retention`, `rating_from_score`; statically calls `MemoryState`, `Rating`, `apply_review`, `interval_for_retention`, `rating_from_score`
- [[Reference/Modules/learnloop/cli/fit|learnloop.cli.fit]] — imports `FSRS6_DEFAULT_WEIGHTS`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `forgetting_curve`; statically calls `forgetting_curve`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `FSRS6_DEFAULT_WEIGHTS`
- [[Reference/Modules/learnloop/scheduling/evaluation|learnloop.scheduling.evaluation]] — imports `MemoryState`, `apply_review`, `forgetting_curve`; statically calls `apply_review`, `forgetting_curve`
- [[Reference/Modules/learnloop/scheduling/fsrs_fitting|learnloop.scheduling.fsrs_fitting]] — imports `FSRS6_DEFAULT_WEIGHTS`, `MemoryState`, `Rating`, `apply_review`, `forgetting_curve`; statically calls `apply_review`, `forgetting_curve`
- [[Reference/Modules/learnloop/scheduling/review_log|learnloop.scheduling.review_log]] — imports `Rating`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `FSRS6_DEFAULT_WEIGHTS`, `forgetting_curve`; statically calls `forgetting_curve`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `forgetting_curve`; statically calls `forgetting_curve`
- [[Reference/Modules/learnloop/substrate/administration_adapters|learnloop.substrate.administration_adapters]] — imports `FSRS6_DEFAULT_WEIGHTS`, `Rating`
- [[Reference/Modules/learnloop/substrate/card_lineage|learnloop.substrate.card_lineage]] — imports `FSRS6_DEFAULT_WEIGHTS`, `MemoryState`, `Rating`, `apply_review`; statically calls `Rating`, `apply_review`
- [[Reference/Modules/learnloop/substrate/compat/substrate_cutover|learnloop.substrate.compat.substrate_cutover]] — imports `FSRS6_DEFAULT_WEIGHTS`, `Rating`, `apply_review`; statically calls `apply_review`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `forgetting_curve`; statically calls `forgetting_curve`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `clamp`; calls `clamp`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `enum`, `math`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/cli/fit|learnloop.cli.fit]], [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]], [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]], [[Reference/Modules/learnloop/scheduling/evaluation|learnloop.scheduling.evaluation]] and 8 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_administration_adapters.py](../../../../../../tests/test_administration_adapters.py) — direct import
  - `test_ineligible_practice_observation_leaves_card_state_untouched`
  - `test_only_practice_eligible_updates_card_state`
- [tests/test_card_lineage.py](../../../../../../tests/test_card_lineage.py) — direct import
  - `test_fork_starts_new_lineage_and_state_without_inherited_stability`
  - `test_minor_successor_retains_lineage_and_state`
  - `test_rebuild_is_deterministic_and_independent_of_practice_item_cache`
- [tests/test_evaluation.py](../../../../../../tests/test_evaluation.py) — direct import
  - `test_report_on_real_session_flow`
- [tests/test_event_sufficiency.py](../../../../../../tests/test_event_sufficiency.py) — direct import
- [tests/test_fitted_parameters.py](../../../../../../tests/test_fitted_parameters.py) — direct import
  - `test_resolve_fsrs_weights_defaults_when_absent`
  - `test_resolve_fsrs_weights_falls_back_on_malformed_payload`
  - `test_resolve_fsrs_weights_uses_valid_fitted_set`
- [tests/test_fsrs.py](../../../../../../tests/test_fsrs.py) — direct import
  - `test_again_does_not_increase_stability_like_good`
  - `test_first_review_uses_initial_weights`
  - `test_forgetting_curve_is_one_at_zero_and_decreases`
  - `test_good_review_increases_stability_over_time`
  - `test_interval_grows_with_stability`
  - `test_rating_from_score_buckets`
- [tests/test_fsrs_fitting.py](../../../../../../tests/test_fsrs_fitting.py) — direct import
  - `test_bounds_and_ordering_projection`
  - `test_deterministic`
  - `test_recoverability_beats_defaults_on_perturbed_weights`
  - `test_refuses_below_min_reviews`
  - `test_review_log_loss_skips_short_gaps_and_zero_weight`
  - `test_shrinkage_dominates_at_tiny_n`
- [tests/test_journey6.py](../../../../../../tests/test_journey6.py) — direct import
- [tests/test_review_log.py](../../../../../../tests/test_review_log.py) — direct import
  - `test_dont_know_rating_and_weight`
  - `test_hint_cap_and_score_binning_match_live_semantics`
  - `test_reconstruction_reproduces_live_practice_item_state`
- [tests/test_substrate_cutover.py](../../../../../../tests/test_substrate_cutover.py) — direct import
  - `test_deferred_projection_rebuild_is_deterministic_and_idempotent`
  - `test_diagnostic_and_assessment_write_no_practice_schedule`
  - `test_dual_write_retry_does_not_duplicate_events`
  - `test_fault_after_each_boundary_recovers_to_the_no_fault_state`
  - `test_projection_failure_defers_without_half_update`
  - `test_submit_writes_full_lineage_in_one_unit`

## Modification guidance

- Change fsrs policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/fsrs.py](../../../../../../src/learnloop/scheduling/fsrs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

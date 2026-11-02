---
title: "learnloop.placement.predictor"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/placement/predictor.py"
source_paths:
  - "src/learnloop/placement/predictor.py"
source_commit: "1f2bed45dec6dca4bc6c882b02b980f179aa998b"
source_commit_timestamp: "2026-10-12T12:25:04-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.placement"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.placement.predictor module"
  - "src/learnloop/placement/predictor.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-placement"
---

# `learnloop.placement.predictor`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.placement.predictor` exists within [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] to own the behavior summarized by its module contract: The active learner predictor as placement consumes it (field §4.1, G10).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/placement/predictor.py](../../../../../../src/learnloop/placement/predictor.py) |
| Source lines | 180 |
| Owning package | [[Reference/Modules/learnloop/placement/_package|learnloop.placement]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1f2bed45dec6dca4bc6c882b02b980f179aa998b` |
| Commit timestamp | `2026-10-12T12:25:04-04:00` |

## Public API

- `class PredictorNotActivatable(ValueError)` ([source](../../../../../../src/learnloop/placement/predictor.py), line 28) — The configured active predictor has no live adapter (needs Phase 4).
- `class LiveMasteryPredictor` ([source](../../../../../../src/learnloop/placement/predictor.py), line 37) — ``mastery_ekf`` served from the persisted per-LO posterior.
  - `__init__(self, vault: LoadedVault, repository: Repository, *, mastery_states: Mapping[str, MasteryState] | None=None, now_iso: str='1970-01-01T00:00:00Z') -> None` (line 45; internal)
  - `_state(self, learning_object_id: str) -> tuple[MasteryState, bool]` (line 67; internal) — (posterior or claim-anchored prior, untested).
  - `_item(self, item: ItemFeatures | str) -> tuple[str, float, float]` (line 81; internal)
  - `predict(self, features: ItemFeatures) -> float` (line 95; public)
  - `predict_item(self, item: ItemFeatures | str) -> ItemPrediction` (line 98; public)
  - `region_estimates(self, scope: Iterable[str] | None=None) -> dict[str, RegionEstimate]` (line 106; public)
  - `conditional_gain(self, item: ItemFeatures | str, chosen: Iterable[ItemFeatures | str], weights: Mapping[str, float]) -> float` (line 121; public) — Expected posterior-variance reduction, weighted by region.
  - `observe(self, row: Any) -> None` (line 157; public)
  - `rebuild(self, rows: Iterable[Any]) -> None` (line 160; public)
- `active_predictor(vault: LoadedVault, repository: Repository, *, mastery_states: Mapping[str, MasteryState] | None=None, now_iso: str='1970-01-01T00:00:00Z') -> LearnerPredictor` ([source](../../../../../../src/learnloop/placement/predictor.py), line 164) — The configured ``field.active_predictor``, served live.

### Module constants

- `LIVE_INCUMBENT_VERSION` ([src/learnloop/placement/predictor.py](../../../../../../src/learnloop/placement/predictor.py), line 25)

## Internal implementation anchors

- `_sigmoid(value: float) -> float` ([source](../../../../../../src/learnloop/placement/predictor.py), line 32)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]] — imports `LiveMasteryPredictor`; statically calls `LiveMasteryPredictor`
- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `active_predictor`; statically calls `active_predictor`
- [[Reference/Modules/learnloop/diagnosis/quick_check|learnloop.diagnosis.quick_check]] — imports `active_predictor`; statically calls `active_predictor`
- [[Reference/Modules/learnloop/hints/state|learnloop.hints.state]] — imports `active_predictor`; statically calls `active_predictor`
- [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]] — imports `PredictorNotActivatable`, `active_predictor`; statically calls `active_predictor`
- [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]] — imports `active_predictor`; statically calls `active_predictor`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `active_predictor`; statically calls `active_predictor`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `active_predictor`; statically calls `active_predictor`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `MasteryState`, `Repository`
- [[Reference/Modules/learnloop/field/types|learnloop.field.types]] — imports `ItemFeatures`, `ItemPrediction`, `LearnerPredictor`, `RegionEstimate`; calls `ItemPrediction`, `RegionEstimate`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `initial_mastery_state_for_learning_object`, `resolve_item_irt_params`; calls `initial_mastery_state_for_learning_object`, `resolve_item_irt_params`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]], [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]], [[Reference/Modules/learnloop/diagnosis/quick_check|learnloop.diagnosis.quick_check]], [[Reference/Modules/learnloop/hints/state|learnloop.hints.state]], [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_assumed_known.py](../../../../../../tests/test_assumed_known.py) — direct import
  - `test_fast_track_default_threshold_is_not_met_by_two_answers`
  - `test_predictor_assumption_is_impossible_under_the_incumbent`
- [tests/test_discriminating_search.py](../../../../../../tests/test_discriminating_search.py) — direct import
  - `test_retention_is_posed_only_after_an_assisted_only_success_with_the_active_predictor`
- [tests/test_quick_check.py](../../../../../../tests/test_quick_check.py) — direct import
  - `test_selection_is_the_largest_conditional_gain_and_deterministic`
- [tests/test_reader_followups_review.py](../../../../../../tests/test_reader_followups_review.py) — direct import
  - `test_f12_the_production_valuer_composes_the_attempt_familiarity_discount`
  - `test_f9_a_formative_only_retention_question_reaches_a_valuation_problem`

## Modification guidance

- Make changes here when the responsibility remains predictor within learnloop.placement; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/placement/predictor.py](../../../../../../src/learnloop/placement/predictor.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

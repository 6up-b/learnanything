---
title: "learnloop.field.types"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/field/types.py"
source_paths:
  - "src/learnloop/field/types.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.field"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.field.types module"
  - "src/learnloop/field/types.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-field"
---

# `learnloop.field.types`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/field/_package|learnloop.field]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.field.types` exists within [[Reference/Modules/learnloop/field/_package|learnloop.field]] to own the behavior summarized by its module contract: Immutable, store-free inputs to the prequential learner-field models.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/field/types.py](../../../../../../src/learnloop/field/types.py) |
| Source lines | 237 |
| Owning package | [[Reference/Modules/learnloop/field/_package|learnloop.field]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ArmConstants` ([source](../../../../../../src/learnloop/field/types.py), line 20)
  - `__post_init__(self) -> None` (line 34; internal)
- `class ItemFeatures` ([source](../../../../../../src/learnloop/field/types.py), line 46)
- `class AnswerSignals` ([source](../../../../../../src/learnloop/field/types.py), line 79) — What the learner's own answer says about its chance, before its grade.
  - `__post_init__(self) -> None` (line 98; internal)
- `class AttemptRow` ([source](../../../../../../src/learnloop/field/types.py), line 110)
  - `observed_at(self) -> str` (line 143; public)
  - `lo_id(self) -> str` (line 147; public)
  - `memory_scored(self) -> bool` (line 151; public) — A graded cold retrieval that memory arms predict and are scored on.
  - `memory_eligible(self) -> bool` (line 164; public) — A scored retrieval that also trains memory (not a transfer probe).
- `class FacetRow(AttemptRow)` ([source](../../../../../../src/learnloop/field/types.py), line 175)
- `class SignalRow` ([source](../../../../../../src/learnloop/field/types.py), line 181)
- `class ItemPrediction` ([source](../../../../../../src/learnloop/field/types.py), line 199)
- `class RegionEstimate` ([source](../../../../../../src/learnloop/field/types.py), line 206)
- `class Predictor(Protocol)` ([source](../../../../../../src/learnloop/field/types.py), line 214)
  - `predict(self, features: ItemFeatures) -> float` (line 219; public)
  - `observe(self, row: ObservationRow) -> None` (line 220; public)
- `class LearnerPredictor(Predictor, Protocol)` ([source](../../../../../../src/learnloop/field/types.py), line 224)
  - `predict_item(self, item: ItemFeatures | str) -> ItemPrediction` (line 227; public)
  - `conditional_gain(self, item: ItemFeatures | str, chosen: Iterable[ItemFeatures | str], weights: Mapping[str, float]) -> float` (line 228; public)
  - `region_estimates(self, scope: Iterable[str] | None=None) -> dict[str, RegionEstimate]` (line 234; public)
  - `rebuild(self, rows: Iterable[ObservationRow]) -> None` (line 237; public)

### Module constants

- `MEMORY_TRAINING_RELATIONS` ([src/learnloop/field/types.py](../../../../../../src/learnloop/field/types.py), line 70)
- `ANSWER_CONFIDENCE_PROBABILITY` ([src/learnloop/field/types.py](../../../../../../src/learnloop/field/types.py), line 75)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]] — imports `ItemFeatures`; statically calls `ItemFeatures`
- [[Reference/Modules/learnloop/field/__init__|learnloop.field]] — imports `ArmConstants`, `AttemptRow`, `FacetRow`, `ItemFeatures`, `ItemPrediction`, `LearnerPredictor`, `ObservationRow`, `Predictor`, `RegionEstimate`, `SignalRow`
- [[Reference/Modules/learnloop/field/answer_signals|learnloop.field.answer_signals]] — imports `ANSWER_CONFIDENCE_PROBABILITY`, `AnswerSignals`, `AttemptRow`, `FacetRow`, `ItemFeatures`, `SignalRow`
- [[Reference/Modules/learnloop/field/evaluation|learnloop.field.evaluation]] — imports `AttemptRow`, `FacetRow`, `ObservationRow`, `SignalRow`
- [[Reference/Modules/learnloop/field/item_content|learnloop.field.item_content]] — imports `AttemptRow`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `AnswerSignals`, `AttemptRow`, `FacetRow`, `ItemFeatures`; statically calls `AnswerSignals`, `AttemptRow`, `FacetRow`, `ItemFeatures`
- [[Reference/Modules/learnloop/field/predictors|learnloop.field.predictors]] — imports `ArmConstants`, `AttemptRow`, `FacetRow`, `ItemFeatures`, `ItemPrediction`, `LearnerPredictor`, `ObservationRow`, `Predictor`, `RegionEstimate`, `SignalRow`; statically calls `ArmConstants`, `ItemFeatures`, `ItemPrediction`, `RegionEstimate`
- [[Reference/Modules/learnloop/field/probability_arms|learnloop.field.probability_arms]] — imports `AttemptRow`, `FacetRow`, `ItemFeatures`, `SignalRow`
- [[Reference/Modules/learnloop/field/probability_prep|learnloop.field.probability_prep]] — imports `AttemptRow`, `SignalRow`
- [[Reference/Modules/learnloop/field/probability_states|learnloop.field.probability_states]] — imports `AttemptRow`
- [[Reference/Modules/learnloop/field/signals|learnloop.field.signals]] — imports `AttemptRow`, `SignalRow`; statically calls `SignalRow`
- [[Reference/Modules/learnloop/field/success_head|learnloop.field.success_head]] — imports `FacetRow`, `ItemFeatures`, `ObservationRow`, `SignalRow`
- [[Reference/Modules/learnloop/field/workbench_signals|learnloop.field.workbench_signals]] — imports `SignalRow`; statically calls `SignalRow`
- [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]] — imports `LearnerPredictor`, `RegionEstimate`; statically calls `RegionEstimate`
- [[Reference/Modules/learnloop/placement/predictor|learnloop.placement.predictor]] — imports `ItemFeatures`, `ItemPrediction`, `LearnerPredictor`, `RegionEstimate`; statically calls `ItemPrediction`, `RegionEstimate`
- [[Reference/Modules/learnloop/placement/rules|learnloop.placement.rules]] — imports `RegionEstimate`
- [[Reference/Modules/learnloop/placement/signals|learnloop.placement.signals]] — imports `AttemptRow`, `ItemFeatures`, `SignalRow`; statically calls `AttemptRow`, `ItemFeatures`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `LearnerPredictor`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]], [[Reference/Modules/learnloop/field/__init__|learnloop.field]], [[Reference/Modules/learnloop/field/answer_signals|learnloop.field.answer_signals]], [[Reference/Modules/learnloop/field/evaluation|learnloop.field.evaluation]], [[Reference/Modules/learnloop/field/item_content|learnloop.field.item_content]] and 13 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_answer_signal_arms.py](../../../../../../tests/test_answer_signal_arms.py) — direct import
  - `test_confidence_alone_starts_at_the_duels_mapping`
  - `test_signal_features_follow_the_duel_mapping_and_abstain_when_absent`
  - `test_the_map_fit_learns_an_overconfident_learner`
- [tests/test_assumed_known.py](../../../../../../tests/test_assumed_known.py) — direct import
  - `test_fast_track_receipt_recomputes_its_decision`
- [tests/test_eval_harness.py](../../../../../../tests/test_eval_harness.py) — direct import
  - `test_confusion_blocks_but_curiosity_does_not`
  - `test_facet_predictions_aggregate_before_observe_not_multiply_attempts`
  - `test_first_unseen_split_counts_excluded_encounters_but_not_signals`
  - `test_report2_shares_the_confusion_blocking_predicate`
  - `test_unclean_initial_answer_never_fast_tracks`
- [tests/test_family_evaluation.py](../../../../../../tests/test_family_evaluation.py) — direct import
- [tests/test_field_priors.py](../../../../../../tests/test_field_priors.py) — direct import
  - `test_claim_priors_use_only_preexisting_historical_scopes`
- [tests/test_field_workbench_signals.py](../../../../../../tests/test_field_workbench_signals.py) — direct import
  - `test_a_stuck_step_with_text_is_one_zero_mass_confusion_row_per_chain`
  - `test_enrich_attempts_ignores_workbench_rows`
  - `test_review_f2_a_stuck_answer_keeps_the_step_time_row_through_delete_submit_and_grading`
- [tests/test_interaction_signals.py](../../../../../../tests/test_interaction_signals.py) — direct import
- [tests/test_lo_general.py](../../../../../../tests/test_lo_general.py) — direct import
  - `test_assistance_only_zero_mass_is_replaced_only_by_hint_arms`
  - `test_constants_are_validated`
  - `test_facet_beta_uses_share_without_multiplying_attempt_mass`
  - `test_hints_replace_not_stack_assistance_discount`
  - `test_one_lo_limit_matches_incumbent_including_drift_and_priming`
  - `test_practice_conditional_gain_accumulates_only_chosen_cold_transitions`
  - `test_practice_zero_innovation_commits_exactly_gamma_only_when_cold`
  - `test_rebuild_deterministic_and_no_external_io`
  - `test_signal_cap_resets_only_on_next_day`
  - `test_signals_are_weak_capped_and_not_demonstration`
  - `test_zero_mass_byte_invariance_including_no_new_region`
- [tests/test_placement_signals.py](../../../../../../tests/test_placement_signals.py) — direct import
  - `test_suspected_leak_makes_the_answer_non_cold_for_fast_track`
- [tests/test_placement_split_grades.py](../../../../../../tests/test_placement_split_grades.py) — direct import
  - `test_rules_read_an_unverified_grade_as_unassessed`
- [tests/test_predictor_interface.py](../../../../../../tests/test_predictor_interface.py) — direct import
  - `test_incumbent_uses_explicit_vault_config_without_reading_store`
  - `test_input_contract_is_immutable_and_excludes_outcomes`
  - `test_unchanged_consumer_uses_only_interface`
- [tests/test_probability_arms.py](../../../../../../tests/test_probability_arms.py) — direct import
  - `test_a_cache_from_a_different_past_fails_closed`
  - `test_recalibration_uses_only_past_predictions`
- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
- [tests/test_success_head.py](../../../../../../tests/test_success_head.py) — direct import
- [tests/test_success_head_cli.py](../../../../../../tests/test_success_head_cli.py) — direct import
  - `test_seen_stem_records_follow_the_seen_revision_and_scored_rows`

## Modification guidance

- Make changes here when the responsibility remains types within learnloop.field; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/field/types.py](../../../../../../src/learnloop/field/types.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.field.predictors"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/field/predictors.py"
source_paths:
  - "src/learnloop/field/predictors.py"
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
  - "learnloop.field.predictors module"
  - "src/learnloop/field/predictors.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-field"
---

# `learnloop.field.predictors`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/field/_package|learnloop.field]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.field.predictors` exists within [[Reference/Modules/learnloop/field/_package|learnloop.field]] to own the behavior summarized by its module contract: Pure prequential arms.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/field/predictors.py](../../../../../../src/learnloop/field/predictors.py) |
| Source lines | 562 |
| Owning package | [[Reference/Modules/learnloop/field/_package|learnloop.field]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class LoGeneral` ([source](../../../../../../src/learnloop/field/predictors.py), line 71) — Small joint float64 probability-space EKF, with opt-in coarse factors.
  - `__init__(self, *, name: str='lo_general', extensions: Iterable[str]=(), constants: ArmConstants | None=None, config: MasteryConfig | None=None, items: Iterable[ItemFeatures]=(), general_means: Mapping[str, float] | None=None, lo_priors: Mapping[str, tuple[float, float]] | None=None) -> None` (line 77; internal)
  - `_reset(self) -> None` (line 99; internal)
  - `_components(self, f: ItemFeatures) -> list[tuple[str, float, float]]` (line 110; internal)
  - `_view(self, features: Iterable[ItemFeatures])` (line 130; internal)
  - `_loadings(self, f: ItemFeatures, keys: list[str]) -> np.ndarray` (line 143; internal)
  - `_drift(self, f: ItemFeatures, keys: list[str], covariance: np.ndarray) -> np.ndarray` (line 149; internal)
  - `_features(self, item: ItemFeatures | str) -> ItemFeatures` (line 167; internal)
  - `_logit(self, f: ItemFeatures, keys: list[str], mean: np.ndarray) -> float` (line 170; internal)
  - `predict(self, features: ItemFeatures) -> float` (line 183; public)
  - `predict_item(self, item: ItemFeatures | str) -> ItemPrediction` (line 188; public)
  - `_noise(self, f: ItemFeatures, p: float, mass: float, interpretation: float=0.0) -> float` (line 199; internal)
  - `_register_regions(self, f: ItemFeatures) -> None` (line 207; internal)
  - `observe(self, row: ObservationRow) -> None` (line 216; public)
  - `region_estimates(self, scope: Iterable[str] | None=None) -> dict[str, RegionEstimate]` (line 288; public)
  - `conditional_gain(self, item: ItemFeatures | str, chosen: Iterable[ItemFeatures | str], weights: Mapping[str, float]) -> float` (line 316; public)
  - `rebuild(self, rows: Iterable[ObservationRow]) -> None` (line 353; public)
  - `snapshot_bytes(self) -> bytes` (line 358; public) — Stable diagnostic serialization, including clocks and directness.
- `class MasteryEKF(LoGeneral)` ([source](../../../../../../src/learnloop/field/predictors.py), line 370) — Independent-LO adapter: the update itself is production mastery math.
  - `__init__(self, **kwargs)` (line 373; internal)
  - `_components(self, f)` (line 376; internal)
  - `_drift(self, f, keys, covariance)` (line 381; internal)
  - `observe(self, row: ObservationRow) -> None` (line 390; public)
- `class BetaPredictor` ([source](../../../../../../src/learnloop/field/predictors.py), line 421) — Running beta counts, weighted once per attempt (or by facet share).
  - `__init__(self, *, name='base_rate_lo', **_kwargs)` (line 426; internal)
  - `predict(self, features: ItemFeatures) -> float` (line 432; public)
  - `observe(self, row: ObservationRow) -> None` (line 439; public)
  - `rebuild(self, rows: Iterable[ObservationRow]) -> None` (line 451; public)
  - `snapshot_bytes(self) -> bytes` (line 456; public)
- `register_predictor(name: str, factory: Callable[..., Predictor], *, sweep: bool=False, inputs: Iterable[str]=_EKF_INPUTS, groups: Iterable[str]=()) -> None` ([source](../../../../../../src/learnloop/field/predictors.py), line 470) — Phase 3's family arms register here without changing the harness.
- `registered_predictors(*, include_sweeps: bool=True, group: str | None=None) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/field/predictors.py), line 488)
- `create_predictor(name: str, **kwargs) -> Predictor` ([source](../../../../../../src/learnloop/field/predictors.py), line 496)
- `is_calibrated_predictor(predictor: str | Predictor) -> bool` ([source](../../../../../../src/learnloop/field/predictors.py), line 507)
- `validate_active_predictor(name: str, *, phase: str='F1') -> None` ([source](../../../../../../src/learnloop/field/predictors.py), line 516)

### Module constants

- `_OFFLINE_INERT_MASTERY_KEYS` ([src/learnloop/field/predictors.py](../../../../../../src/learnloop/field/predictors.py), line 46)
- `REPLAY_INPUTS` ([src/learnloop/field/predictors.py](../../../../../../src/learnloop/field/predictors.py), line 462)
- `_EKF_INPUTS` ([src/learnloop/field/predictors.py](../../../../../../src/learnloop/field/predictors.py), line 463)
- `_REGISTRY` ([src/learnloop/field/predictors.py](../../../../../../src/learnloop/field/predictors.py), line 465)
- `_SWEEPS` ([src/learnloop/field/predictors.py](../../../../../../src/learnloop/field/predictors.py), line 466)
- `_GROUPS` ([src/learnloop/field/predictors.py](../../../../../../src/learnloop/field/predictors.py), line 467)
- `_EXTENSIONS` ([src/learnloop/field/predictors.py](../../../../../../src/learnloop/field/predictors.py), line 527)

## Internal implementation anchors

- `_probability(logit: float, clip: float=1e-09) -> float` ([source](../../../../../../src/learnloop/field/predictors.py), line 33)
- `_hash(value: object) -> str` ([source](../../../../../../src/learnloop/field/predictors.py), line 38)
- `_mastery_hash_view(config: MasteryConfig) -> dict` ([source](../../../../../../src/learnloop/field/predictors.py), line 49) — The mastery config as an offline arm's version hash reads it: with the fields arc C retired (``mastery.irt.discrimination_min/max``), so an arm keeps the hash recorded before they went (config/retired.py).
- `_order(row: ObservationRow) -> tuple[str, str, str]` ([source](../../../../../../src/learnloop/field/predictors.py), line 57)
- `_eligible(row: ObservationRow, mass: float | None=None) -> bool` ([source](../../../../../../src/learnloop/field/predictors.py), line 62)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/arms|learnloop.adaptive_difficulty.arms]] — imports `create_predictor`; statically calls `create_predictor`
- [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]] — imports `create_predictor`; statically calls `create_predictor`
- [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]] — imports `registered_predictors`; statically calls `registered_predictors`
- [[Reference/Modules/learnloop/field/answer_signals|learnloop.field.answer_signals]] — imports `_EKF_INPUTS`, `_order`, `create_predictor`, `register_predictor`, `registered_predictors`; statically calls `create_predictor`, `register_predictor`, `registered_predictors`
- [[Reference/Modules/learnloop/field/evaluation|learnloop.field.evaluation]] — imports `create_predictor`, `registered_predictors`; statically calls `create_predictor`, `registered_predictors`
- [[Reference/Modules/learnloop/field/memory|learnloop.field.memory]] — imports `register_predictor`, `registered_predictors`; statically calls `register_predictor`, `registered_predictors`
- [[Reference/Modules/learnloop/field/probability_prep|learnloop.field.probability_prep]] — imports `create_predictor`; statically calls `create_predictor`
- [[Reference/Modules/learnloop/field/success_head|learnloop.field.success_head]] — imports `MasteryEKF`, `_eligible`, `_mastery_hash_view`; statically calls `MasteryEKF`, `_eligible`, `_mastery_hash_view`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `MasteryConfig`; calls `MasteryConfig`
- [[Reference/Modules/learnloop/config/retired|learnloop.config.retired]] — imports `identity_dump`; calls `identity_dump`
- [[Reference/Modules/learnloop/field/types|learnloop.field.types]] — imports `ArmConstants`, `FacetRow`, `ItemFeatures`, `ItemPrediction`, `LearnerPredictor`, `ObservationRow`, `Predictor`, `RegionEstimate`, `SignalRow`; calls `ArmConstants`, `ItemFeatures`, `ItemPrediction`, `RegionEstimate`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `MasteryObservation`, `initial_mastery_state`, `update_mastery`; calls `MasteryObservation`, `initial_mastery_state`, `update_mastery`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/arms|learnloop.adaptive_difficulty.arms]], [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]], [[Reference/Modules/learnloop/cli/field|learnloop.cli.field]], [[Reference/Modules/learnloop/field/answer_signals|learnloop.field.answer_signals]], [[Reference/Modules/learnloop/field/evaluation|learnloop.field.evaluation]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/test_ad23_fix_r8.py](../../../../../../tests/test_ad23_fix_r8.py) — direct import
  - `test_the_challengers_history_never_reads_a_withheld_items_answer`
- [tests/test_answer_signal_arms.py](../../../../../../tests/test_answer_signal_arms.py) — direct import
  - `test_a_control_twin_separates_the_signal_from_recalibration`
  - `test_a_prediction_never_sees_its_own_outcome`
  - `test_confidence_alone_starts_at_the_duels_mapping`
  - `test_signal_arms_are_registered_offline_and_can_never_be_active`
  - `test_the_stack_keeps_its_base_exactly_on_every_row`
- [tests/test_eval_harness.py](../../../../../../tests/test_eval_harness.py) — direct import
  - `test_assistance_only_zero_reaches_hint_replacement_arm`
  - `test_llm_off_by_default_and_sweeps_available`
- [tests/test_family_evaluation.py](../../../../../../tests/test_family_evaluation.py) — direct import
  - `test_family_arms_are_registered_in_the_field_registry`
  - `test_idea_hier_is_lo_general_with_independent_family_priors_and_no_mean_decay`
  - `test_memory_arm_inputs_are_frozen_and_never_a_store`
  - `test_prefix_predictions_do_not_change_with_future_outcomes`
  - `test_zero_ability_mass_trains_memory_but_never_idea_hier`
- [tests/test_field_boundaries.py](../../../../../../tests/test_field_boundaries.py) — direct import
  - `test_predictor_mastery_import_is_arithmetic_only`
- [tests/test_lo_general.py](../../../../../../tests/test_lo_general.py) — direct import
  - `test_assistance_only_zero_mass_is_replaced_only_by_hint_arms`
  - `test_capability_and_transfer_offsets`
  - `test_drift_adds_variance_without_mean_decay`
  - `test_excluded_hint_row_cannot_be_restored_by_replacement_mass`
  - `test_facet_beta_uses_share_without_multiplying_attempt_mass`
  - `test_hint_replacement_requires_explicit_factorization`
  - `test_hint_sweep_and_versions_include_constants`
  - `test_hints_replace_not_stack_assistance_discount`
  - `test_invalid_hint_replacement_mass_is_a_complete_noop`
  - `test_joint_update_generalizes_only_within_subject_and_keeps_directness`
  - `test_llm_difficulty_only_widens_measurement_uncertainty`
  - `test_no_graph_input_and_incumbent_never_propagates`
  - `test_one_lo_limit_matches_incumbent_including_drift_and_priming`
  - `test_practice_conditional_gain_accumulates_only_chosen_cold_transitions`
  - `test_practice_is_predicted_before_outcome_and_not_committed_by_prediction`
  - `test_practice_zero_innovation_commits_exactly_gamma_only_when_cold`
  - `test_priming_probability_uses_shifted_difficulty_without_mutation`
  - `test_priors_and_conditional_information_are_pure`
  - `test_rebuild_deterministic_and_no_external_io`
  - `test_retrievability_and_beta_zero_sweep`
  - `test_signal_cap_resets_only_on_next_day`
  - `test_signals_are_weak_capped_and_not_demonstration`
  - `test_small_mass_is_not_floored_in_challenger`
  - `test_zero_mass_byte_invariance_including_no_new_region`
- [tests/test_predictor_interface.py](../../../../../../tests/test_predictor_interface.py) — direct import
  - `test_activation_eligibility_and_f1_successor_boundary`
  - `test_incumbent_uses_explicit_vault_config_without_reading_store`
  - `test_input_contract_is_immutable_and_excludes_outcomes`
  - `test_unchanged_consumer_uses_only_interface`
- [tests/test_probability_arms.py](../../../../../../tests/test_probability_arms.py) — direct import
  - `test_arms_are_off_by_default_and_can_never_be_active`
- [tests/test_retired_config_identities.py](../../../../../../tests/test_retired_config_identities.py) — direct import
  - `test_predictor_version_hashes_are_the_ones_recorded_before_arc_c`
- [tests/test_success_head.py](../../../../../../tests/test_success_head.py) — direct import
  - `test_t8_arms_are_never_activatable`

## Modification guidance

- Make changes here when the responsibility remains predictors within learnloop.field; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/field/predictors.py](../../../../../../src/learnloop/field/predictors.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

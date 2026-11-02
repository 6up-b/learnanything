---
title: "learnloop.evsi_calibration.world"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/evsi_calibration/world.py"
source_paths:
  - "src/learnloop/evsi_calibration/world.py"
source_commit: "d0ed73fe5b70b267fab771a67b9eb99cdf2d5e21"
source_commit_timestamp: "2026-10-13T00:39:06-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.evsi_calibration"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.evsi_calibration.world module"
  - "src/learnloop/evsi_calibration/world.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-evsi-calibration"
---

# `learnloop.evsi_calibration.world`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.evsi_calibration.world` exists within [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] to own the behavior summarized by its module contract: The simulated diagnostic world: scenarios, the true learner, the system's model.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/evsi_calibration/world.py](../../../../../../src/learnloop/evsi_calibration/world.py) |
| Source lines | 369 |
| Owning package | [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `d0ed73fe5b70b267fab771a67b9eb99cdf2d5e21` |
| Commit timestamp | `2026-10-13T00:39:06-04:00` |

## Public API

- `misconception_hypothesis(misconception_id: str) -> str` ([source](../../../../../../src/learnloop/evsi_calibration/world.py), line 65)
- `route_for(hypothesis: str) -> str` ([source](../../../../../../src/learnloop/evsi_calibration/world.py), line 69)
- `class TruthParams` ([source](../../../../../../src/learnloop/evsi_calibration/world.py), line 78)
  - `__getitem__(self, name: str) -> float` (line 83; internal)
- `class Scenario` ([source](../../../../../../src/learnloop/evsi_calibration/world.py), line 88)
  - `misconceptions(self) -> tuple[str, ...]` (line 97; public)
  - `question(self, question_id: str) -> EediQuestion` (line 100; public)
- `build_scenarios(bank: EediBank, fit: ResponseFit, *, min_questions: int=6, min_misconception_questions: int=2, max_misconceptions: int=5) -> list[Scenario]` ([source](../../../../../../src/learnloop/evsi_calibration/world.py), line 107) — One scenario per subject with enough questions and diagnosable misconceptions.
- `eedi_row(hypothesis: str, question: EediQuestion, params: Mapping[str, float], *, consistency: float | None=None) -> dict[str, float]` ([source](../../../../../../src/learnloop/evsi_calibration/world.py), line 175) — ``P(option | hypothesis, question)`` under the fitted response model.
- `hand_set_row(hypothesis: str, question: EediQuestion) -> dict[str, float]` ([source](../../../../../../src/learnloop/evsi_calibration/world.py), line 229) — Today's ordinal-vocabulary contrast-card row mapped onto four options.
- `system_rows(model: str, scenario: Scenario, question: EediQuestion) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/evsi_calibration/world.py), line 266) — ``{hypothesis: {option: p}}``: the instrument rows the selectors see.
- `class TrueLearner` ([source](../../../../../../src/learnloop/evsi_calibration/world.py), line 281) — One simulated learner: a true hypothesis and per-question consistency draws.
  - `consistency_for(self, question: EediQuestion) -> float` (line 289; public)
  - `row(self, question: EediQuestion) -> dict[str, float]` (line 302; public)
  - `answer(self, question: EediQuestion) -> str` (line 307; public)
- `with_truth(scenarios: Sequence[Scenario], **overrides: float) -> list[Scenario]` ([source](../../../../../../src/learnloop/evsi_calibration/world.py), line 313) — The same scenarios with some response parameters replaced.
- `entropy(distribution: Mapping[str, float]) -> float` ([source](../../../../../../src/learnloop/evsi_calibration/world.py), line 340)
- `model_misfit(scenarios: Sequence[Scenario], model: str) -> dict[str, float]` ([source](../../../../../../src/learnloop/evsi_calibration/world.py), line 344) — Per-row L-infinity distance between a system model and the per-question truth.

### Module constants

- `HYP_KNOWS` ([src/learnloop/evsi_calibration/world.py](../../../../../../src/learnloop/evsi_calibration/world.py), line 42)
- `HYP_OTHER` ([src/learnloop/evsi_calibration/world.py](../../../../../../src/learnloop/evsi_calibration/world.py), line 43)
- `MIS_PREFIX` ([src/learnloop/evsi_calibration/world.py](../../../../../../src/learnloop/evsi_calibration/world.py), line 44)
- `ACTION_CONTINUE` ([src/learnloop/evsi_calibration/world.py](../../../../../../src/learnloop/evsi_calibration/world.py), line 45)
- `ACTION_RETEACH` ([src/learnloop/evsi_calibration/world.py](../../../../../../src/learnloop/evsi_calibration/world.py), line 46)
- `REPAIR_PREFIX` ([src/learnloop/evsi_calibration/world.py](../../../../../../src/learnloop/evsi_calibration/world.py), line 47)
- `SYSTEM_MODELS` ([src/learnloop/evsi_calibration/world.py](../../../../../../src/learnloop/evsi_calibration/world.py), line 49)
- `TRUTH_PARAMETERS` ([src/learnloop/evsi_calibration/world.py](../../../../../../src/learnloop/evsi_calibration/world.py), line 52)

## Internal implementation anchors

- `_spread(weights: Mapping[str, float], mass: float) -> dict[str, float]` ([source](../../../../../../src/learnloop/evsi_calibration/world.py), line 163)
- `_normalized(row: Mapping[str, float]) -> dict[str, float]` ([source](../../../../../../src/learnloop/evsi_calibration/world.py), line 170)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/evsi_calibration/experiments|learnloop.evsi_calibration.experiments]] — imports `HYP_KNOWS`, `HYP_OTHER`, `build_scenarios`, `hand_set_row`, `misconception_hypothesis`, `model_misfit`, `system_rows`, `with_truth`; statically calls `build_scenarios`, `hand_set_row`, `misconception_hypothesis`, `model_misfit`, `system_rows`, `with_truth`
- [[Reference/Modules/learnloop/evsi_calibration/families|learnloop.evsi_calibration.families]] — imports `HYP_KNOWS`, `HYP_OTHER`, `MIS_PREFIX`, `Scenario`, `TrueLearner`, `build_scenarios`, `eedi_row`, `hand_set_row`, `misconception_hypothesis`, `with_truth`; statically calls `TrueLearner`, `build_scenarios`, `eedi_row`, `hand_set_row`, `misconception_hypothesis`, `with_truth`
- [[Reference/Modules/learnloop/evsi_calibration/multifamily|learnloop.evsi_calibration.multifamily]] — imports `HYP_KNOWS`, `HYP_OTHER`, `MIS_PREFIX`, `build_scenarios`, `route_for`; statically calls `build_scenarios`, `route_for`
- [[Reference/Modules/learnloop/evsi_calibration/multisim|learnloop.evsi_calibration.multisim]] — imports `ACTION_CONTINUE`, `HYP_KNOWS`, `Scenario`, `entropy`, `hand_set_row`, `route_for`; statically calls `entropy`, `hand_set_row`, `route_for`
- [[Reference/Modules/learnloop/evsi_calibration/simulate|learnloop.evsi_calibration.simulate]] — imports `HYP_KNOWS`, `Scenario`, `TrueLearner`, `entropy`, `route_for`, `system_rows`; statically calls `TrueLearner`, `entropy`, `route_for`, `system_rows`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `CONTRAST_CONFUSABLE_DEFAULT_ROWS`, `ORDINAL_VOCABULARY`
- [[Reference/Modules/learnloop/evsi_calibration/eedi|learnloop.evsi_calibration.eedi]] — imports `EediBank`, `EediQuestion`, `OPTIONS`
- [[Reference/Modules/learnloop/evsi_calibration/response_fit|learnloop.evsi_calibration.response_fit]] — imports `ResponseFit`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/evsi_calibration/experiments|learnloop.evsi_calibration.experiments]], [[Reference/Modules/learnloop/evsi_calibration/families|learnloop.evsi_calibration.families]], [[Reference/Modules/learnloop/evsi_calibration/multifamily|learnloop.evsi_calibration.multifamily]], [[Reference/Modules/learnloop/evsi_calibration/multisim|learnloop.evsi_calibration.multisim]], [[Reference/Modules/learnloop/evsi_calibration/simulate|learnloop.evsi_calibration.simulate]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_evsi_calibration_sim.py](../../../../../../tests/test_evsi_calibration_sim.py) — direct import
  - `test_each_response_world_simulates_histories_generated_in_that_world`
  - `test_rows_are_distributions_and_the_hand_set_vocabulary_is_read_not_copied`
  - `test_simulation_runs_every_policy_on_common_random_numbers`
  - `test_the_incumbent_arm_includes_todays_robust_completion_gate`
  - `test_the_measured_loss_charges_unresolved_minutes_off_the_diagonal`
- [tests/test_evsi_multisim.py](../../../../../../tests/test_evsi_multisim.py) — direct import
  - `test_each_ablation_puts_back_exactly_one_piece_of_the_successor`
  - `test_every_family_and_a_cross_system_run_all_policies`
  - `test_family_rows_and_priors_are_distributions_and_needs_name_hypotheses`
  - `test_strength_moves_only_holders_in_every_family`
  - `test_the_calibrated_systems_average_responses_over_the_item_pool`
  - `test_the_counted_card_row_starts_at_the_vocabulary_and_follows_the_counts`
  - `test_the_family_loop_reproduces_the_single_family_loop_for_the_latent_class_family`
  - `test_the_implied_consistency_carries_a_subject_clustered_ci`
  - `test_the_learning_scenario_moves_holders_and_keeps_a_distribution`
  - `test_the_multi_family_study_runs_every_episode_without_a_count_bound`
  - `test_the_nrm_row_cache_never_serves_a_revised_bank`
  - `test_the_package_with_every_piece_put_back_is_the_successor`
  - `test_the_successor_arm_values_with_the_nat_scale_when_no_decision_is_at_stake`
  - `test_the_successor_arms_lift_the_episode_maximum_onto_value`
  - `test_true_loss_is_the_loss_table_for_one_need_and_charges_each_unaddressed_need`
- [tests/test_evsi_single_family_unbounded.py](../../../../../../tests/test_evsi_single_family_unbounded.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains world within learnloop.evsi_calibration; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/evsi_calibration/world.py](../../../../../../src/learnloop/evsi_calibration/world.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.evsi_calibration.families"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/evsi_calibration/families.py"
source_paths:
  - "src/learnloop/evsi_calibration/families.py"
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
  - "learnloop.evsi_calibration.families module"
  - "src/learnloop/evsi_calibration/families.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-evsi-calibration"
---

# `learnloop.evsi_calibration.families`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.evsi_calibration.families` exists within [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] to own the behavior summarized by its module contract: Simulator families as true learners over the Eedi 2024 question bank.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/evsi_calibration/families.py](../../../../../../src/learnloop/evsi_calibration/families.py) |
| Source lines | 953 |
| Owning package | [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ScenarioModel` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 121) — One family's truth and calibrated system model on one 2024 subject.
  - `__init__(self, scenario: Scenario) -> None` (line 126; internal)
  - `system_prior(self) -> dict[str, float]` (line 132; public)
  - `system_rows(self, question: EediQuestion) -> dict[str, dict[str, float]]` (line 135; public)
  - `_compute_system_rows(self, question: EediQuestion) -> dict[str, dict[str, float]]` (line 142; internal)
  - `draw_state(self, rng: np.random.Generator) -> Any` (line 146; public)
  - `row(self, state: Any, question: EediQuestion) -> dict[str, float]` (line 149; public)
  - `needs(self, state: Any) -> tuple[str, ...]` (line 152; public)
  - `transition(self, state: Any, uniform: float) -> Any` (line 155; public)
  - `answer(self, state: Any, question: EediQuestion, rng: np.random.Generator) -> str` (line 158; public)
  - `targeted_consistencies(self) -> list[float]` (line 163; public) — The system model's P(the misconception's own distractor | it is held) on every question that targets it (what ``consistency`` means here).
- `class FamilyModel` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 190) — A simulator family at one instrument strength (``None`` = as fitted).
  - `key(self) -> str` (line 198; public)
  - `scenario_model(self, scenario: Scenario) -> ScenarioModel` (line 201; public)
  - `with_strength(self, consistency: float | None) -> 'FamilyModel'` (line 204; public)
- `class LatentClassScenario(ScenarioModel)` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 211)
  - `__init__(self, scenario: Scenario, prior: Mapping[str, float] | None=None) -> None` (line 212; internal)
  - `system_prior(self) -> dict[str, float]` (line 217; public)
  - `_compute_system_rows(self, question: EediQuestion) -> dict[str, dict[str, float]]` (line 220; internal)
  - `draw_state(self, rng: np.random.Generator) -> str` (line 223; public)
  - `row(self, state: str, question: EediQuestion) -> dict[str, float]` (line 227; public)
  - `needs(self, state: str) -> tuple[str, ...]` (line 231; public)
- `class LcaFamily(FamilyModel)` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 236) — The single-family study's world (its scenarios carry the fitted truth).
  - `scenario_model(self, scenario: Scenario) -> ScenarioModel` (line 244; public)
  - `with_strength(self, consistency: float | None) -> 'LcaFamily'` (line 250; public)
- `class LearningScenario(LatentClassScenario)` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 254) — Latent class states that move after every answer (the learning family).
  - `__init__(self, scenario: Scenario, transitions: np.ndarray) -> None` (line 259; internal)
  - `next_distribution(self, state: str) -> dict[str, float]` (line 264; public) — The fitted 3x3 chain on the K-misconception state space: a holder can resolve (to ``knows``) or lose the misconception (to ``other``); an acquisition rate is spread over the subject's misconceptions.
  - `transition(self, state: str, uniform: float) -> str` (line 290; public)
- `class LtaFamily(FamilyModel)` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 301) — The learning family: latent class emissions + fitted transitions.
  - `scenario_model(self, scenario: Scenario) -> ScenarioModel` (line 310; public)
  - `with_strength(self, consistency: float | None) -> 'LtaFamily'` (line 316; public)
- `class CdmProfilePrior` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 324)
  - `weights(self, attributes: int) -> list[tuple[tuple[int, tuple[int, ...]], float]]` (line 330; public)
- `class CdmScenario(ScenarioModel)` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 416)
  - `__init__(self, scenario: Scenario, pool: np.ndarray, prior: CdmProfilePrior) -> None` (line 417; internal)
  - `_held(self, profile: tuple[int, tuple[int, ...]]) -> list[str]` (line 427; internal)
  - `_primary_weights(self, profile: tuple[int, tuple[int, ...]]) -> dict[str, float]` (line 430; internal)
  - `system_prior(self) -> dict[str, float]` (line 436; public)
  - `_profile_row(self, profile: tuple[int, tuple[int, ...]], question: EediQuestion, phi: np.ndarray) -> dict[str, float]` (line 446; internal)
  - `_compute_system_rows(self, question: EediQuestion) -> dict[str, dict[str, float]]` (line 450; internal) — Per hypothesis, the profiles' item-pool-average rows weighted by the profile prior: ``sum_p w_p share_h(p) mean_i P_i(option | p)``.
  - `draw_state(self, rng: np.random.Generator) -> tuple[int, tuple[int, ...]]` (line 465; public)
  - `_item(self, question: EediQuestion) -> np.ndarray` (line 470; internal)
  - `row(self, state: tuple[int, tuple[int, ...]], question: EediQuestion) -> dict[str, float]` (line 473; public)
  - `needs(self, state: tuple[int, tuple[int, ...]]) -> tuple[str, ...]` (line 476; public)
- `class CdmFamily(FamilyModel)` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 503)
  - `_pool(self, subject: int) -> np.ndarray` (line 517; internal)
  - `scenario_model(self, scenario: Scenario) -> ScenarioModel` (line 523; public)
  - `holder_consistency(self, delta: float=0.0) -> float` (line 527; public)
  - `with_strength(self, consistency: float | None) -> 'CdmFamily'` (line 532; public)
- `nrm_threshold(typical: np.ndarray, theta: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 556) — The trait value above which the designated distractor is a learner's most likely answer on the typical item, given ability ``theta``.
- `class NrmScenario(ScenarioModel)` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 565) — The continuous family on one subject.
  - `__init__(self, scenario: Scenario, pool: np.ndarray, typical: np.ndarray, holder_shift: float=0.0) -> None` (line 573; internal)
  - `_needs_batch(self, states: np.ndarray) -> list[tuple[str, ...]]` (line 596; internal)
  - `_logits(self, params: np.ndarray, theta: np.ndarray, eta: np.ndarray, question: EediQuestion) -> np.ndarray` (line 612; internal) — (S, 4 options) logits for states (theta, eta per misconception) on ``question`` for one item (``params`` (7,)); (B, S, 4) for a block of items (``params`` (B, 1, 7)).
  - `_probabilities(self, params: np.ndarray, states: np.ndarray, question: EediQuestion) -> np.ndarray` (line 642; internal)
  - `pool_probabilities(self, states: np.ndarray, question: EediQuestion) -> np.ndarray` (line 648; public) — (S, 4): each state's response probabilities averaged over the item pool (the item a question takes is unknown to the system).
  - `system_prior(self) -> dict[str, float]` (line 658; public)
  - `_compute_system_rows(self, question: EediQuestion) -> dict[str, dict[str, float]]` (line 665; internal)
  - `_rows_for(self, question: EediQuestion, hypotheses: Sequence[str]) -> dict[str, dict[str, float]]` (line 677; internal) — The system rows of ``hypotheses``: the population states weighted by their share of each hypothesis, each state's response averaged over the item pool.
  - `targeted_consistencies(self) -> list[float]` (line 696; public) — As :meth:`ScenarioModel.targeted_consistencies`, from the holders' rows alone (the strength bisection's inner loop): the same rows, without evaluating the population states that hold nothing.
  - `draw_state(self, rng: np.random.Generator) -> tuple[float, ...]` (line 714; public)
  - `row(self, state: tuple[float, ...], question: EediQuestion) -> dict[str, float]` (line 717; public)
  - `needs(self, state: tuple[float, ...]) -> tuple[str, ...]` (line 722; public)
- `nrm_holder_rates(items: np.ndarray, typical: np.ndarray, population: np.ndarray, holder_shift: float=0.0) -> tuple[float, float]` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 726) — Holders' and non-holders' mean P(designated) on a targeted question.
- `class NrmFamily(FamilyModel)` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 746)
  - `scenario_model(self, scenario: Scenario) -> ScenarioModel` (line 758; public)
  - `_population(self) -> np.ndarray` (line 764; internal)
  - `_calibration_items(self) -> np.ndarray` (line 767; internal)
  - `holder_rates(self, holder_shift: float=0.0) -> tuple[float, float]` (line 774; public)
  - `with_strength(self, consistency: float | None) -> 'NrmFamily'` (line 777; public)
- `lta_response_fit(fits: FamilyFits) -> ResponseFit` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 807)
- `build_families(bank: EediBank, fits: FamilyFits) -> dict[str, FamilyModel]` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 813) — Every family (fitted and stress) as a truth world over the bank.
- `class HandSetSystem` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 874) — Today's vocabulary as the system's rows (prior: the truth family's).
  - `rows(self, scenario: Scenario, question: EediQuestion) -> dict[str, dict[str, float]]` (line 879; public)
- `implied_quantities(family: FamilyModel, scenarios: Sequence[Scenario]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 883) — The family's calibrated system model, summarized in the latent class model's terms over the simulation bank: consistency on targeted questions, false alarm, knower slip, unsure success and the hypothesis prevalences.

### Module constants

- `FAMILY_NAMES` ([src/learnloop/evsi_calibration/families.py](../../../../../../src/learnloop/evsi_calibration/families.py), line 88)
- `STRESS_FAMILIES` ([src/learnloop/evsi_calibration/families.py](../../../../../../src/learnloop/evsi_calibration/families.py), line 89)
- `POPULATION_SAMPLE` ([src/learnloop/evsi_calibration/families.py](../../../../../../src/learnloop/evsi_calibration/families.py), line 90)
- `ITEM_BLOCK` ([src/learnloop/evsi_calibration/families.py](../../../../../../src/learnloop/evsi_calibration/families.py), line 92)
- `IMPLIED_BOOTSTRAP` ([src/learnloop/evsi_calibration/families.py](../../../../../../src/learnloop/evsi_calibration/families.py), line 94)
- `_NRM_ROW_CACHE` ([src/learnloop/evsi_calibration/families.py](../../../../../../src/learnloop/evsi_calibration/families.py), line 102)
- `_NRM_ROW_CACHE_LIMIT` ([src/learnloop/evsi_calibration/families.py](../../../../../../src/learnloop/evsi_calibration/families.py), line 103)
- `STRENGTH_ITEMS` ([src/learnloop/evsi_calibration/families.py](../../../../../../src/learnloop/evsi_calibration/families.py), line 105)
- `STRENGTH_POPULATION` ([src/learnloop/evsi_calibration/families.py](../../../../../../src/learnloop/evsi_calibration/families.py), line 106)

### Explicit exports

`__all__` declares:

- `FAMILY_NAMES`
- `STRESS_FAMILIES`
- `CdmFamily`
- `FamilyModel`
- `HandSetSystem`
- `LcaFamily`
- `LtaFamily`
- `NrmFamily`
- `ScenarioModel`
- `build_families`
- `implied_quantities`

## Internal implementation anchors

- `_hash_int(*parts: Any) -> int` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 109)
- `_row(values: Mapping[str, float]) -> dict[str, float]` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 113)
- `_bisect_strength(consistency_at: Any, target: float, lo: float, hi: float, steps: int=30) -> float` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 178) — The smallest-error shift: ``consistency_at`` is increasing in the shift.
- `_cdm_row(phi: np.ndarray, skill: int, triggered: Sequence[str], question: EediQuestion) -> dict[str, float]` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 349) — ``P(option)`` from one item's role-space group rows ``phi`` (4 groups x 4 roles).
- `_cdm_rows(phi: np.ndarray, skill: int, triggered: Sequence[str], question: EediQuestion) -> np.ndarray` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 381) — :func:`_cdm_row` for every item of ``phi`` (items x 4 groups x 4 roles) at once: (items, 4 options) in ``OPTIONS`` order.
- `_logit(p: np.ndarray) -> np.ndarray` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 483)
- `_shift_designated(phi: np.ndarray, delta: float) -> np.ndarray` ([source](../../../../../../src/learnloop/evsi_calibration/families.py), line 488) — Shift the designated role's logit by ``delta`` in the triggered groups.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/evsi_calibration/multifamily|learnloop.evsi_calibration.multifamily]] — imports `FAMILY_NAMES`, `FamilyModel`, `STRESS_FAMILIES`, `build_families`, `implied_quantities`; statically calls `build_families`, `implied_quantities`
- [[Reference/Modules/learnloop/evsi_calibration/multisim|learnloop.evsi_calibration.multisim]] — imports `FamilyModel`, `ScenarioModel`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/evsi_calibration/eedi|learnloop.evsi_calibration.eedi]] — imports `EediBank`, `EediQuestion`, `OPTIONS`
- [[Reference/Modules/learnloop/evsi_calibration/family_fit|learnloop.evsi_calibration.family_fit]] — imports `FamilyFits`, `nrm_logits`; calls `nrm_logits`
- [[Reference/Modules/learnloop/evsi_calibration/response_fit|learnloop.evsi_calibration.response_fit]] — imports `FitSettings`, `ResponseFit`, `assemble_response_fit`; calls `FitSettings`, `assemble_response_fit`
- [[Reference/Modules/learnloop/evsi_calibration/world|learnloop.evsi_calibration.world]] — imports `HYP_KNOWS`, `HYP_OTHER`, `MIS_PREFIX`, `Scenario`, `TrueLearner`, `build_scenarios`, `eedi_row`, `hand_set_row`, `misconception_hypothesis`, `with_truth`; calls `TrueLearner`, `build_scenarios`, `eedi_row`, `hand_set_row`, `misconception_hypothesis`, `with_truth`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `itertools`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/evsi_calibration/multifamily|learnloop.evsi_calibration.multifamily]], [[Reference/Modules/learnloop/evsi_calibration/multisim|learnloop.evsi_calibration.multisim]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_evsi_multisim.py](../../../../../../tests/test_evsi_multisim.py) — direct import
  - `test_every_family_and_a_cross_system_run_all_policies`
  - `test_family_rows_and_priors_are_distributions_and_needs_name_hypotheses`
  - `test_strength_moves_only_holders_in_every_family`
  - `test_the_calibrated_systems_average_responses_over_the_item_pool`
  - `test_the_family_loop_reproduces_the_single_family_loop_for_the_latent_class_family`
  - `test_the_implied_consistency_carries_a_subject_clustered_ci`
  - `test_the_learning_scenario_moves_holders_and_keeps_a_distribution`
  - `test_the_multi_family_study_runs_every_episode_without_a_count_bound`
  - `test_the_nrm_row_cache_never_serves_a_revised_bank`

## Modification guidance

- Make changes here when the responsibility remains families within learnloop.evsi_calibration; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/evsi_calibration/families.py](../../../../../../src/learnloop/evsi_calibration/families.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

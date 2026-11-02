---
title: "learnloop.evsi_calibration.simulate"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/evsi_calibration/simulate.py"
source_paths:
  - "src/learnloop/evsi_calibration/simulate.py"
source_commit: "96588eb76156d8388361729b773faf417691178e"
source_commit_timestamp: "2026-10-13T01:29:40-04:00"
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
  - "learnloop.evsi_calibration.simulate module"
  - "src/learnloop/evsi_calibration/simulate.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-evsi-calibration"
---

# `learnloop.evsi_calibration.simulate`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.evsi_calibration.simulate` exists within [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] to own the behavior summarized by its module contract: Run simulated diagnostic episodes and record every forecast against what happened.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/evsi_calibration/simulate.py](../../../../../../src/learnloop/evsi_calibration/simulate.py) |
| Source lines | 375 |
| Owning package | [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `96588eb76156d8388361729b773faf417691178e` |
| Commit timestamp | `2026-10-13T01:29:40-04:00` |

## Public API

- `class SimulationSettings` ([source](../../../../../../src/learnloop/evsi_calibration/simulate.py), line 53)
  - `as_dict(self) -> dict[str, Any]` (line 70; public)
- `class CheckRecord` ([source](../../../../../../src/learnloop/evsi_calibration/simulate.py), line 78)
- `class EpisodeRecord` ([source](../../../../../../src/learnloop/evsi_calibration/simulate.py), line 96)
- `class LearnerSpec` ([source](../../../../../../src/learnloop/evsi_calibration/simulate.py), line 116)
- `loss_table_for(scenario: Scenario, settings: P.PolicySettings, *, unresolved: float) -> AL.LossTable` ([source](../../../../../../src/learnloop/evsi_calibration/simulate.py), line 130) — The minutes loss over the scenario's routes (real ``build_loss_table``).
- `draw_learners(scenarios: Sequence[Scenario], settings: SimulationSettings) -> list[LearnerSpec]` ([source](../../../../../../src/learnloop/evsi_calibration/simulate.py), line 152) — Flagged learners (common across policies): truth, then a wrong trigger answer.
- `run_learner(scenario: Scenario, spec: LearnerSpec, settings: SimulationSettings) -> tuple[list[CheckRecord], list[EpisodeRecord]]` ([source](../../../../../../src/learnloop/evsi_calibration/simulate.py), line 185)
- `class SimulationRun` ([source](../../../../../../src/learnloop/evsi_calibration/simulate.py), line 345)
- `run_simulation(scenarios: Sequence[Scenario], settings: SimulationSettings, *, learners: Sequence[LearnerSpec] | None=None) -> SimulationRun` ([source](../../../../../../src/learnloop/evsi_calibration/simulate.py), line 352)
- `with_policy(settings: SimulationSettings, **changes: Any) -> SimulationSettings` ([source](../../../../../../src/learnloop/evsi_calibration/simulate.py), line 374)

### Module constants

- `SIMULATION_VERSION` ([src/learnloop/evsi_calibration/simulate.py](../../../../../../src/learnloop/evsi_calibration/simulate.py), line 46)
- `MEMBER_QUANTILES` ([src/learnloop/evsi_calibration/simulate.py](../../../../../../src/learnloop/evsi_calibration/simulate.py), line 49)

## Internal implementation anchors

- `_seed(*parts: Any) -> int` ([source](../../../../../../src/learnloop/evsi_calibration/simulate.py), line 126)
- `_member_quantiles(values: Sequence[float]) -> dict[str, float]` ([source](../../../../../../src/learnloop/evsi_calibration/simulate.py), line 181)
- `_run_chunk(payload: tuple[Sequence[Scenario], Sequence[LearnerSpec], SimulationSettings]) -> tuple[list[CheckRecord], list[EpisodeRecord]]` ([source](../../../../../../src/learnloop/evsi_calibration/simulate.py), line 333)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/evsi_calibration/experiments|learnloop.evsi_calibration.experiments]] — imports `SIMULATION_VERSION`, `SimulationSettings`, `draw_learners`, `run_simulation`, `with_policy`; statically calls `SimulationSettings`, `draw_learners`, `run_simulation`, `with_policy`
- [[Reference/Modules/learnloop/evsi_calibration/metrics|learnloop.evsi_calibration.metrics]] — imports `CheckRecord`, `EpisodeRecord`, `MEMBER_QUANTILES`
- [[Reference/Modules/learnloop/evsi_calibration/multifamily|learnloop.evsi_calibration.multifamily]] — imports `loss_table_for`; statically calls `loss_table_for`
- [[Reference/Modules/learnloop/evsi_calibration/multisim|learnloop.evsi_calibration.multisim]] — imports `CheckRecord`, `EpisodeRecord`, `_member_quantiles`, `loss_table_for`; statically calls `CheckRecord`, `EpisodeRecord`, `_member_quantiles`, `loss_table_for`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/diagnosis/robust_composition|learnloop.diagnosis.robust_composition]] — imports `module`; calls `build_ensemble`, `expected_information_gain`, `observed_update`, `robust_quantile`
- [[Reference/Modules/learnloop/evsi_calibration/eedi|learnloop.evsi_calibration.eedi]] — imports `OPTIONS`
- [[Reference/Modules/learnloop/evsi_calibration/policies|learnloop.evsi_calibration.policies]] — imports `module`; calls `EpisodeState`, `decide`, `identity_channel`, `mixture`
- [[Reference/Modules/learnloop/evsi_calibration/world|learnloop.evsi_calibration.world]] — imports `HYP_KNOWS`, `Scenario`, `TrueLearner`, `entropy`, `route_for`, `system_rows`; calls `TrueLearner`, `entropy`, `route_for`, `system_rows`
- [[Reference/Modules/learnloop/scheduling/action_loss|learnloop.scheduling.action_loss]] — imports `module`; calls `build_loss_table`
- [[Reference/Modules/learnloop/scheduling/evsi|learnloop.scheduling.evsi]] — imports `module`; calls `evsi_for_conditionals`

### Platform and third-party dependencies

- Standard library: `__future__`, `concurrent`, `dataclasses`, `hashlib`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/evsi_calibration/experiments|learnloop.evsi_calibration.experiments]], [[Reference/Modules/learnloop/evsi_calibration/metrics|learnloop.evsi_calibration.metrics]], [[Reference/Modules/learnloop/evsi_calibration/multifamily|learnloop.evsi_calibration.multifamily]], [[Reference/Modules/learnloop/evsi_calibration/multisim|learnloop.evsi_calibration.multisim]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_evsi_calibration_sim.py](../../../../../../tests/test_evsi_calibration_sim.py) — direct import
  - `test_each_response_world_simulates_histories_generated_in_that_world`
  - `test_simulation_runs_every_policy_on_common_random_numbers`
  - `test_the_measured_loss_charges_unresolved_minutes_off_the_diagonal`
- [tests/test_evsi_multisim.py](../../../../../../tests/test_evsi_multisim.py) — direct import
  - `test_the_family_loop_reproduces_the_single_family_loop_for_the_latent_class_family`
  - `test_true_loss_is_the_loss_table_for_one_need_and_charges_each_unaddressed_need`
- [tests/test_evsi_single_family_unbounded.py](../../../../../../tests/test_evsi_single_family_unbounded.py) — direct import
  - `test_an_explicit_bound_still_stops_and_the_unbounded_run_counts_its_stops`
  - `test_the_single_family_path_defaults_to_no_count_bound`

## Modification guidance

- Make changes here when the responsibility remains simulate within learnloop.evsi_calibration; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/evsi_calibration/simulate.py](../../../../../../src/learnloop/evsi_calibration/simulate.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

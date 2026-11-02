---
title: "learnloop.evsi_calibration.experiments"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/evsi_calibration/experiments.py"
source_paths:
  - "src/learnloop/evsi_calibration/experiments.py"
source_commit: "a2521921b55f3a76c4ec661e82f46d8d3e23a657"
source_commit_timestamp: "2026-10-13T14:31:43-04:00"
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
  - "learnloop.evsi_calibration.experiments module"
  - "src/learnloop/evsi_calibration/experiments.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-evsi-calibration"
---

# `learnloop.evsi_calibration.experiments`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.evsi_calibration.experiments` exists within [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] to own the behavior summarized by its module contract: The full Part A study behind ``learnloop evsi simulate``.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/evsi_calibration/experiments.py](../../../../../../src/learnloop/evsi_calibration/experiments.py) |
| Source lines | 534 |
| Owning package | [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a2521921b55f3a76c4ec661e82f46d8d3e23a657` |
| Commit timestamp | `2026-10-13T14:31:43-04:00` |

## Public API

- `class ExperimentSettings` ([source](../../../../../../src/learnloop/evsi_calibration/experiments.py), line 65)
  - `as_dict(self) -> dict[str, Any]` (line 91; public)
- `hand_set_implied(bank: EediBank, scenarios: Sequence[Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/experiments.py), line 119) — What today's constants imply for the quantities Eedi measures.
- `starting_truth_probability(world: Sequence[Any], learners: Sequence[Any], *, system_model: str='eedi_fitted') -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/experiments.py), line 186) — Mean probability the system's starting belief puts on each learner's truth.
- `bound_counts(episodes: Sequence[Any], *, reference_bound: int=REFERENCE_BOUND) -> dict[str, int]` ([source](../../../../../../src/learnloop/evsi_calibration/experiments.py), line 214) — How a count bound bears on one arm's episodes (``count_bound_stops``-style).
- `run_experiments(bank: EediBank, fit: ResponseFit, settings: ExperimentSettings, *, progress: Callable[[str], None] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/experiments.py), line 244)
- `recommendations(report: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/evsi_calibration/experiments.py), line 486) — Structured recommendations; the review file renders and argues them.

### Module constants

- `EXPERIMENTS_VERSION` ([src/learnloop/evsi_calibration/experiments.py](../../../../../../src/learnloop/evsi_calibration/experiments.py), line 57)
- `REFERENCE_BOUND` ([src/learnloop/evsi_calibration/experiments.py](../../../../../../src/learnloop/evsi_calibration/experiments.py), line 61)
- `SWEEPS` ([src/learnloop/evsi_calibration/experiments.py](../../../../../../src/learnloop/evsi_calibration/experiments.py), line 96)
- `SWEEP_POLICIES` ([src/learnloop/evsi_calibration/experiments.py](../../../../../../src/learnloop/evsi_calibration/experiments.py), line 113)
- `DEFAULT_SWEEP_POLICIES` ([src/learnloop/evsi_calibration/experiments.py](../../../../../../src/learnloop/evsi_calibration/experiments.py), line 116)

### Explicit exports

`__all__` declares:

- `ExperimentSettings`
- `REFERENCE_BOUND`
- `SWEEPS`
- `bound_counts`
- `recommendations`
- `run_experiments`

## Internal implementation anchors

- `_policy_rows(run: Any, *, seed: int, draws: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/experiments.py), line 166)
- `_compact(summary: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/experiments.py), line 171)
- `_first_rankings(run: Any, policy: str) -> dict[int, tuple[str, ...]]` ([source](../../../../../../src/learnloop/evsi_calibration/experiments.py), line 210)
- `_best_value(parameter: Mapping[str, Any], policy: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/evsi_calibration/experiments.py), line 470)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/evsi|learnloop.cli.evsi]] — imports `ExperimentSettings`, `SWEEPS`, `run_experiments`; statically calls `ExperimentSettings`, `run_experiments`
- [[Reference/Modules/learnloop/evsi_calibration/compare|learnloop.evsi_calibration.compare]] — imports `SWEEPS`
- [[Reference/Modules/learnloop/evsi_calibration/multifamily|learnloop.evsi_calibration.multifamily]] — imports `DEFAULT_SWEEP_POLICIES`, `SWEEPS`, `SWEEP_POLICIES`, `hand_set_implied`; statically calls `hand_set_implied`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `ProbeConfig`; calls `ProbeConfig`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `BRIDGE_SENSITIVITY`, `BRIDGE_SPECIFICITY`
- [[Reference/Modules/learnloop/diagnosis/robust_composition|learnloop.diagnosis.robust_composition]] — imports `module`; calls `observed_update`
- [[Reference/Modules/learnloop/evsi_calibration/eedi|learnloop.evsi_calibration.eedi]] — imports `EediBank`
- [[Reference/Modules/learnloop/evsi_calibration/metrics|learnloop.evsi_calibration.metrics]] — imports `module`; calls `episode_summary`, `kendall_tau`, `paired_difference`, `summarize`
- [[Reference/Modules/learnloop/evsi_calibration/policies|learnloop.evsi_calibration.policies]] — imports `module`; calls `PolicySettings`
- [[Reference/Modules/learnloop/evsi_calibration/response_fit|learnloop.evsi_calibration.response_fit]] — imports `ResponseFit`
- [[Reference/Modules/learnloop/evsi_calibration/simulate|learnloop.evsi_calibration.simulate]] — imports `SIMULATION_VERSION`, `SimulationSettings`, `draw_learners`, `run_simulation`, `with_policy`; calls `SimulationSettings`, `draw_learners`, `run_simulation`, `with_policy`
- [[Reference/Modules/learnloop/evsi_calibration/world|learnloop.evsi_calibration.world]] — imports `HYP_KNOWS`, `HYP_OTHER`, `build_scenarios`, `hand_set_row`, `misconception_hypothesis`, `model_misfit`, `system_rows`, `with_truth`; calls `build_scenarios`, `hand_set_row`, `misconception_hypothesis`, `model_misfit`, `system_rows`, `with_truth`
- [[Reference/Modules/learnloop/scheduling/action_loss|learnloop.scheduling.action_loss]] — imports `module`
- [[Reference/Modules/learnloop/scheduling/evsi|learnloop.scheduling.evsi]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `time`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/evsi|learnloop.cli.evsi]], [[Reference/Modules/learnloop/evsi_calibration/compare|learnloop.evsi_calibration.compare]], [[Reference/Modules/learnloop/evsi_calibration/multifamily|learnloop.evsi_calibration.multifamily]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_evsi_calibration_sim.py](../../../../../../tests/test_evsi_calibration_sim.py) — direct import
  - `test_each_response_world_simulates_histories_generated_in_that_world`
- [tests/test_evsi_single_family_unbounded.py](../../../../../../tests/test_evsi_single_family_unbounded.py) — direct import
  - `test_an_explicit_bound_still_stops_and_the_unbounded_run_counts_its_stops`
  - `test_cli_simulate_passes_an_explicit_bound_through`
  - `test_the_bound_attribution_needs_the_bound_the_other_report_applied`
  - `test_the_single_family_path_defaults_to_no_count_bound`

## Modification guidance

- Make changes here when the responsibility remains experiments within learnloop.evsi_calibration; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/evsi_calibration/experiments.py](../../../../../../src/learnloop/evsi_calibration/experiments.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

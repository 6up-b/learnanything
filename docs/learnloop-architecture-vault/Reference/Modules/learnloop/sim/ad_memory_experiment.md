---
title: "learnloop.sim.ad_memory_experiment"
type: "module-reference"
status: "current"
refactor_status: "EVALUATION"
version: "1.0.0"
source_path: "src/learnloop/sim/ad_memory_experiment.py"
source_paths:
  - "src/learnloop/sim/ad_memory_experiment.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.sim"
layer: "simulation"
concepts:
  - "Learning System"
workflows:
  []
aliases:
  - "learnloop.sim.ad_memory_experiment module"
  - "src/learnloop/sim/ad_memory_experiment.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/evaluation"
  - "layer/simulation"
  - "package/learnloop-sim"
---

# `learnloop.sim.ad_memory_experiment`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.sim.ad_memory_experiment` exists within [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] to own the behavior summarized by its module contract: Registered ADM0 runs and aggregate diagnostics, never a production reader.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/sim/ad_memory_experiment.py](../../../../../../src/learnloop/sim/ad_memory_experiment.py) |
| Source lines | 224 |
| Owning package | [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] |
| Architecture layer | `simulation` |
| Refactor status | `EVALUATION` |

> [!note] Evaluation-only authority
> This module computes shadow, audit, or offline evidence. Its outputs do not directly choose learner-facing actions unless a governed promotion path says otherwise.

## Public API

- `metrics(p: np.ndarray, y: np.ndarray, covered: np.ndarray | None=None) -> dict` ([source](../../../../../../src/learnloop/sim/ad_memory_experiment.py), line 22)
- `baseline_predictions(data: S.Dataset) -> dict[str, np.ndarray]` ([source](../../../../../../src/learnloop/sim/ad_memory_experiment.py), line 36) — All baselines consume only earlier labels, using the real mastery update.
- `strata(data: S.Dataset) -> dict[str, np.ndarray]` ([source](../../../../../../src/learnloop/sim/ad_memory_experiment.py), line 62)
- `summarize(runs: list[dict], masks: dict[str, np.ndarray]) -> dict` ([source](../../../../../../src/learnloop/sim/ad_memory_experiment.py), line 79)
- `paired_interval(a: list[float], b: list[float]) -> list[float]` ([source](../../../../../../src/learnloop/sim/ad_memory_experiment.py), line 103)
- `compare(a: dict, b: dict) -> dict` ([source](../../../../../../src/learnloop/sim/ad_memory_experiment.py), line 110)
- `selection_findings(results: dict) -> dict` ([source](../../../../../../src/learnloop/sim/ad_memory_experiment.py), line 122)
- `next_inputs(fold: S.ReviewFold, at: float) -> list[tuple[S.Event, S.MemoryInputs]]` ([source](../../../../../../src/learnloop/sim/ad_memory_experiment.py), line 150) — Cached-input workload: stable item metadata plus strict past-only fold lookup.
- `synthetic_next(arm: S.MemoryArm, inputs: list[tuple[S.Event, S.MemoryInputs]]) -> np.ndarray` ([source](../../../../../../src/learnloop/sim/ad_memory_experiment.py), line 159)
- `benchmark() -> dict` ([source](../../../../../../src/learnloop/sim/ad_memory_experiment.py), line 168)
- `run_registered() -> dict` ([source](../../../../../../src/learnloop/sim/ad_memory_experiment.py), line 198)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/model|learnloop.adaptive_difficulty.model]] — imports `module`; calls `band_probability`, `sigmoid`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `MasteryConfig`; calls `MasteryConfig`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `MasteryObservation`, `initial_mastery_state`, `update_mastery`; calls `MasteryObservation`, `initial_mastery_state`, `update_mastery`
- [[Reference/Modules/learnloop/sim/ad_memory_synthetic|learnloop.sim.ad_memory_synthetic]] — imports `module`; calls `Candidate`, `MemoryArm`, `ReviewFold`, `candidates`, `generate`, `replay`, `schedule`, `variance_floor`, `warmth_check`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `math`, `time`
- Third party: `numpy`, `scipy`

## Larger workflow participation

No direct learner/operator workflow is assigned. This module is offline, shadow-only, dormant, or a dependency reached only through the static consumers below.

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad_memory_simulation.py](../../../../../../tests/test_ad_memory_simulation.py) — direct import
  - `test_metrics_and_recovery_are_not_outcome_coverage`
  - `test_registered_experiment`

## Modification guidance

- Make changes here when the responsibility remains ad memory experiment within learnloop.sim; otherwise move the behavior to its owning boundary.
- Keep this module's shadow/offline outputs decision-inert. Promotion into live policy requires the governed evidence and cutover path documented by its source contract.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/sim/ad_memory_experiment.py](../../../../../../src/learnloop/sim/ad_memory_experiment.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

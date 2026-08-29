---
title: "learnloop.sim.sweep"
type: "module-reference"
status: "current"
refactor_status: "EVALUATION"
version: "1.0.0"
source_path: "src/learnloop/sim/sweep.py"
source_paths:
  - "src/learnloop/sim/sweep.py"
source_commit: "565100878e11bc9ac281139570040c118fbaf1a5"
source_commit_timestamp: "2026-07-08T11:43:16-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop.sim"
layer: "simulation"
concepts:
  - "Learning System"
workflows:
  []
aliases:
  - "learnloop.sim.sweep module"
  - "src/learnloop/sim/sweep.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/evaluation"
  - "layer/simulation"
  - "package/learnloop-sim"
---

# `learnloop.sim.sweep`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.sim.sweep` exists within [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] to own the behavior summarized by its module contract: Config sensitivity sweep: which knobs actually change scheduling decisions.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/sim/sweep.py](../../../../../../src/learnloop/sim/sweep.py) |
| Source lines | 296 |
| Owning package | [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] |
| Architecture layer | `simulation` |
| Refactor status | `EVALUATION` |
| Worktree state | `clean` |
| Source commit | `565100878e11bc9ac281139570040c118fbaf1a5` |
| Commit timestamp | `2026-07-08T11:43:16-04:00` |

> [!note] Evaluation-only authority
> This module computes shadow, audit, or offline evidence. Its outputs do not directly choose learner-facing actions unless a governed promotion path says otherwise.

## Public API

- `class SweepEntry` ([source](../../../../../../src/learnloop/sim/sweep.py), line 40)
- `class SweepReport` ([source](../../../../../../src/learnloop/sim/sweep.py), line 46)
  - `as_dict(self) -> dict[str, Any]` (line 50; public)
- `class SweepSpecError(ValueError)` ([source](../../../../../../src/learnloop/sim/sweep.py), line 54)
- `load_sweep_spec(path: Path | None=None) -> list[SweepEntry]` ([source](../../../../../../src/learnloop/sim/sweep.py), line 58) — Load a sweep spec YAML: ``{"sweeps": [{"param_path": ..., "values": [...]}]}``.
- `run_sweep(vault_root: Path, profile: StudentProfile, *, sweep_spec: list[SweepEntry], days: int=30, items_per_day: int=6, seed: int=42, work_dir: Path, reset_state: bool=True, base_overrides: Mapping[str, Any] | None=None, primed_retries: bool=False, goal_due_day: int | None=None) -> SweepReport` ([source](../../../../../../src/learnloop/sim/sweep.py), line 78)

### Module constants

- `DEFAULT_SWEEP_SPEC_PATH` ([src/learnloop/sim/sweep.py](../../../../../../src/learnloop/sim/sweep.py), line 31)
- `_TOPK_OVERLAP_RELEVANCE` ([src/learnloop/sim/sweep.py](../../../../../../src/learnloop/sim/sweep.py), line 33)
- `_KENDALL_RELEVANCE` ([src/learnloop/sim/sweep.py](../../../../../../src/learnloop/sim/sweep.py), line 34)
- `_MAE_RELEVANCE` ([src/learnloop/sim/sweep.py](../../../../../../src/learnloop/sim/sweep.py), line 35)
- `_GOAL_RELEVANCE` ([src/learnloop/sim/sweep.py](../../../../../../src/learnloop/sim/sweep.py), line 36)

## Internal implementation anchors

- `_compare(param_path: str, value: Any, baseline: SimReport, variant: SimReport) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/sweep.py), line 135)
- `_goal_metric_mean(report: SimReport, key: str) -> float | None` ([source](../../../../../../src/learnloop/sim/sweep.py), line 223)
- `_run_summary(report: SimReport) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/sweep.py), line 231)
- `_first_detection_day(report: SimReport) -> float | None` ([source](../../../../../../src/learnloop/sim/sweep.py), line 242)
- `_overlap(left: list[str], right: list[str]) -> float` ([source](../../../../../../src/learnloop/sim/sweep.py), line 252)
- `_kendall_tau(left: list[str], right: list[str]) -> float | None` ([source](../../../../../../src/learnloop/sim/sweep.py), line 262) — Kendall tau over the ranks of items present in both queue orders.
- `_delta(base: float | None, variant: float | None) -> float | None` ([source](../../../../../../src/learnloop/sim/sweep.py), line 283)
- `_mean(values: list[float]) -> float | None` ([source](../../../../../../src/learnloop/sim/sweep.py), line 289)
- `_round(value: float | None, digits: int=6) -> float | None` ([source](../../../../../../src/learnloop/sim/sweep.py), line 295)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/sim|learnloop.cli.sim]] — imports `SweepSpecError`, `load_sweep_spec`, `run_sweep`; statically calls `load_sweep_spec`, `run_sweep`
- [[Reference/Modules/learnloop/params/sensitivity_certificates|learnloop.params.sensitivity_certificates]] — imports `SweepEntry`, `run_sweep`; statically calls `SweepEntry`, `run_sweep`
- [[Reference/Modules/learnloop/sim/__init__|learnloop.sim]] — imports `run_sweep`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `SimReport`, `SimulationError`, `prepare_run_vault`, `run_simulation`; calls `prepare_run_vault`, `run_simulation`
- [[Reference/Modules/learnloop/sim/student|learnloop.sim.student]] — imports `StudentProfile`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`; calls `read_yaml`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

No direct learner/operator workflow is assigned. This module is offline, shadow-only, dormant, or a dependency reached only through the static consumers below.

Static participation evidence comes from [[Reference/Modules/learnloop/cli/sim|learnloop.cli.sim]], [[Reference/Modules/learnloop/params/sensitivity_certificates|learnloop.params.sensitivity_certificates]], [[Reference/Modules/learnloop/sim/__init__|learnloop.sim]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_sim_teach_back.py](../../../../../../tests/test_sim_teach_back.py) — direct import
  - `test_default_sweep_spec_includes_teach_back_knobs`
  - `test_sweep_runs_with_teach_back_knobs`
- [tests/test_simulation.py](../../../../../../tests/test_simulation.py) — direct import
  - `test_sweep_flags_decision_relevant_and_inert_params`

## Modification guidance

- Make changes here when the responsibility remains sweep within learnloop.sim; otherwise move the behavior to its owning boundary.
- Keep this module's shadow/offline outputs decision-inert. Promotion into live policy requires the governed evidence and cutover path documented by its source contract.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/sim/sweep.py](../../../../../../src/learnloop/sim/sweep.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

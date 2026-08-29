---
title: "learnloop.sim.interval_width_viability"
type: "module-reference"
status: "current"
refactor_status: "EVALUATION"
version: "1.0.0"
source_path: "src/learnloop/sim/interval_width_viability.py"
source_paths:
  - "src/learnloop/sim/interval_width_viability.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
package: "learnloop.sim"
layer: "simulation"
concepts:
  - "Learning System"
workflows:
  []
aliases:
  - "learnloop.sim.interval_width_viability module"
  - "src/learnloop/sim/interval_width_viability.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/evaluation"
  - "layer/simulation"
  - "package/learnloop-sim"
---

# `learnloop.sim.interval_width_viability`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.sim.interval_width_viability` exists within [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] to own the behavior summarized by its module contract: P4 step 3 -- interval-width viability of robust EVSI (spec_p4 §16.3, U-021/U-023).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/sim/interval_width_viability.py](../../../../../../src/learnloop/sim/interval_width_viability.py) |
| Source lines | 150 |
| Owning package | [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] |
| Architecture layer | `simulation` |
| Refactor status | `EVALUATION` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

> [!note] Evaluation-only authority
> This module computes shadow, audit, or offline evidence. Its outputs do not directly choose learner-facing actions unless a governed promotion path says otherwise.

## Public API

- `class WidthResult` ([source](../../../../../../src/learnloop/sim/interval_width_viability.py), line 52)
- `class ViabilityReport` ([source](../../../../../../src/learnloop/sim/interval_width_viability.py), line 61)
  - `as_dict(self) -> dict` (line 68; public)
- `run_interval_width_viability(*, concentrations: Sequence[float]=(60.0, 30.0, 12.0, 4.0, 1.5), heuristic_concentration: float=30.0, n_scenarios: int=40, seed: int=20260720, budget: float | None=None) -> ViabilityReport` ([source](../../../../../../src/learnloop/sim/interval_width_viability.py), line 112) — Sweep channel width; report the measure-mode abstention rate per width and whether the heuristic width stays inside the P0 abstention budget.

### Module constants

- `_LOSS` ([src/learnloop/sim/interval_width_viability.py](../../../../../../src/learnloop/sim/interval_width_viability.py), line 31)
- `_PRIOR` ([src/learnloop/sim/interval_width_viability.py](../../../../../../src/learnloop/sim/interval_width_viability.py), line 47)
- `_EXPECTED_MINUTES` ([src/learnloop/sim/interval_width_viability.py](../../../../../../src/learnloop/sim/interval_width_viability.py), line 48)

## Internal implementation anchors

- `_joint_alpha(concentration: float, sep: float) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/sim/interval_width_viability.py), line 82) — Grader channel ``P(E|Z)`` as Dirichlet alphas at a given concentration.
- `_instrument_rows(strength: float) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/sim/interval_width_viability.py), line 93)
- `_scenario_verdict(concentration: float, strength: float, sep: float, seed: str) -> str` ([source](../../../../../../src/learnloop/sim/interval_width_viability.py), line 98)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/diagnosis/robust_composition|learnloop.diagnosis.robust_composition]] — imports `module`; calls `build_ensemble`
- [[Reference/Modules/learnloop/scheduling/action_loss|learnloop.scheduling.action_loss]] — imports `module`; calls `LossCell`, `LossTable`
- [[Reference/Modules/learnloop/scheduling/evsi|learnloop.scheduling.evsi]] — imports `module`; calls `DiagnosticCandidate`, `rank_feasible`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `random`, `typing`
- Third party: none imported directly

## Larger workflow participation

No direct learner/operator workflow is assigned. This module is offline, shadow-only, dormant, or a dependency reached only through the static consumers below.

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_interval_width_viability.py](../../../../../../tests/test_interval_width_viability.py) — direct import
  - `test_heuristic_width_keeps_abstention_within_budget`
  - `test_pathological_width_breach_raises_the_alarm`
  - `test_report_is_deterministic`

## Modification guidance

- Make changes here when the responsibility remains interval width viability within learnloop.sim; otherwise move the behavior to its owning boundary.
- Keep this module's shadow/offline outputs decision-inert. Promotion into live policy requires the governed evidence and cutover path documented by its source contract.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/sim/interval_width_viability.py](../../../../../../src/learnloop/sim/interval_width_viability.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

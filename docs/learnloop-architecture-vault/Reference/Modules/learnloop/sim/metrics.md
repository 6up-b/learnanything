---
title: "learnloop.sim.metrics"
type: "module-reference"
status: "current"
refactor_status: "EVALUATION"
version: "1.0.0"
source_path: "src/learnloop/sim/metrics.py"
source_paths:
  - "src/learnloop/sim/metrics.py"
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
  - "learnloop.sim.metrics module"
  - "src/learnloop/sim/metrics.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/evaluation"
  - "layer/simulation"
  - "package/learnloop-sim"
---

# `learnloop.sim.metrics`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.sim.metrics` exists within [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] to own the behavior summarized by its module contract: End-of-run simulation metrics: belief vs truth, calibration, detection.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/sim/metrics.py](../../../../../../src/learnloop/sim/metrics.py) |
| Source lines | 372 |
| Owning package | [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] |
| Architecture layer | `simulation` |
| Refactor status | `EVALUATION` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

> [!note] Evaluation-only authority
> This module computes shadow, audit, or offline evidence. Its outputs do not directly choose learner-facing actions unless a governed promotion path says otherwise.

## Public API

- `build_metrics(vault: LoadedVault, repository: Repository, student: 'SyntheticStudent', *, attempts: list['SimAttemptRecord'], day_records: list['SimDayRecord'], detection_days: dict[str, dict[str, Any]], lo_facet_weights: dict[str, dict[str, float]], final_day: float, goal_tracking: dict[str, dict[str, Any]] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/metrics.py), line 25)
- `canonical_facet_belief_mae(repository: Repository, student: 'SyntheticStudent', final_day: float, *, facet_truth_key=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/metrics.py), line 95) — KM2 sim re-key (§16): belief-vs-truth MAE over canonical facet parents.

### Module constants

- `_P_CLIP` ([src/learnloop/sim/metrics.py](../../../../../../src/learnloop/sim/metrics.py), line 22)

## Internal implementation anchors

- `_belief_vs_truth(vault: LoadedVault, repository: Repository, student: 'SyntheticStudent', lo_facet_weights: dict[str, dict[str, float]], day_records: list['SimDayRecord'], final_day: float) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/metrics.py), line 52)
- `_calibration(attempts: list['SimAttemptRecord']) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/metrics.py), line 146)
- `_misconceptions(vault: LoadedVault, repository: Repository, student: 'SyntheticStudent', attempts: list['SimAttemptRecord'], detection_days: dict[str, dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/metrics.py), line 167)
- `_final_facet_state(vault: LoadedVault, repository: Repository, facet_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/sim/metrics.py), line 216)
- `_goals(goal_tracking: dict[str, dict[str, Any]], day_records: list['SimDayRecord']) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/metrics.py), line 239) — Due-date attainment and post-due retention per goal.
- `_fraction_at_target(values: dict[str, float], target: float) -> float | None` ([source](../../../../../../src/learnloop/sim/metrics.py), line 293)
- `_fsrs_sanity(attempts: list['SimAttemptRecord']) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/metrics.py), line 302)
- `_counts(repository: Repository, attempts: list['SimAttemptRecord']) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/metrics.py), line 321)
- `_error_event_rows(repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/sim/metrics.py), line 342)
- `_mean(values: Iterable[float]) -> float | None` ([source](../../../../../../src/learnloop/sim/metrics.py), line 360)
- `_clip(value: float) -> float` ([source](../../../../../../src/learnloop/sim/metrics.py), line 367)
- `_round(value: float | None, digits: int=6) -> float | None` ([source](../../../../../../src/learnloop/sim/metrics.py), line 371)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `module`; statically calls `build_metrics`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `mastery_diagnostic_view`; calls `mastery_diagnostic_view`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `display_mastery`; calls `display_mastery`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `SimAttemptRecord`, `SimDayRecord`
- [[Reference/Modules/learnloop/sim/student|learnloop.sim.student]] — imports `SyntheticStudent`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

No direct learner/operator workflow is assigned. This module is offline, shadow-only, dormant, or a dependency reached only through the static consumers below.

Static participation evidence comes from [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_km2_sim_gates.py](../../../../../../tests/test_km2_sim_gates.py) — direct import
  - `test_shared_facet_belief_mae_beats_per_lo`

## Modification guidance

- Make changes here when the responsibility remains metrics within learnloop.sim; otherwise move the behavior to its owning boundary.
- Keep this module's shadow/offline outputs decision-inert. Promotion into live policy requires the governed evidence and cutover path documented by its source contract.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/sim/metrics.py](../../../../../../src/learnloop/sim/metrics.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

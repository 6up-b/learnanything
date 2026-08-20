---
title: "learnloop.cli.sim"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/cli/sim.py"
source_paths:
  - "src/learnloop/cli/sim.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.cli"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Inspect Persistent State"
aliases:
  - "learnloop.cli.sim module"
  - "src/learnloop/cli/sim.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-cli"
---

# `learnloop.cli.sim`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps sim behavior inside its owning package, [[Reference/Modules/learnloop/cli/_package|learnloop.cli]]. Its public surface centers on `sim_probe_validation_command`, `sim_probe_pilot_command`, `sim_benchmark_forgetting_command`, `sim_run_command`, `sim_sweep_command`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/cli/sim.py](../../../../../../src/learnloop/cli/sim.py) |
| Source lines | 357 |
| Owning package | [[Reference/Modules/learnloop/cli/_package|learnloop.cli]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `sim_probe_validation_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root (copied per run, never written).')]=None, seeds: Annotated[int, typer.Option('--seeds', min=1, help='Runs per planted type.')]=5, planted: Annotated[str | None, typer.Option('--planted', help='Comma-separated planted types (default: all).')]=None, learning_object_id: Annotated[str | None, typer.Option('--lo', help='Target Learning Object (default: first with an open episode).')]=None, label_threshold: Annotated[float, typer.Option('--label-threshold', help='Per-type classification accuracy gate.')]=0.6, action_threshold: Annotated[float, typer.Option('--action-threshold', help='Per-type instructional-action accuracy gate.')]=0.6, sets: Annotated[list[str] | None, typer.Option('--set', help='Config override param.path=value (repeatable).')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit the full JSON report.')]=False, output: Annotated[Path | None, typer.Option('--output', '-o', help='Write the full JSON report to a file.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/sim.py), line 11) — Checkpoint-3 episode validation against planted latent hypothesis types.
- `sim_probe_pilot_command(vault: Annotated[Path | None, typer.Option('--vault', help='Fixture vault root (copied per run, never written).')]=None, seeds: Annotated[int, typer.Option('--seeds', min=1, help='Runs per planted type.')]=3, planted: Annotated[str | None, typer.Option('--planted', help='Comma-separated planted types (default: all).')]=None, learning_object_id: Annotated[str | None, typer.Option('--lo', help='Target Learning Object.')]=None, label_threshold: Annotated[float, typer.Option('--label-threshold', help='Checkpoint 4 entry gate: per-type classification accuracy.')]=0.6, action_threshold: Annotated[float, typer.Option('--action-threshold', help='Checkpoint 4 entry gate: per-type action accuracy.')]=0.6, sets: Annotated[list[str] | None, typer.Option('--set', help='Config override param.path=value (repeatable).')]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit the full JSON report.')]=False, output: Annotated[Path | None, typer.Option('--output', '-o', help='Write the full JSON report to a file.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/sim.py), line 73) — Checkpoint-4 fixture-vault pilot: enforce the Checkpoint-3 sim entry gate, drive the full episode accounting against planted students, then run the §13 audit (predicted-vs-realized EIG, negative information, time calibration, cross-surface replication, shadow policies) and the r…
- `sim_benchmark_forgetting_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root (read-only).')]=None, train_fraction: Annotated[float, typer.Option('--train-fraction', min=0.1, max=0.9, help='Temporal split point.')]=0.7, json_output: Annotated[bool, typer.Option('--json', help='Emit the full JSON report.')]=False, output: Annotated[Path | None, typer.Option('--output', '-o', help='Write the full JSON report to a file.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/sim.py), line 158) — Offline DAS3H-style forgetting benchmark (probe redesign Checkpoint 5.6).
- `sim_run_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root (never written by default).')]=None, profile: Annotated[str, typer.Option('--profile', help='Built-in profile name or profile YAML path.')]='intermediate_with_misconception', days: Annotated[int, typer.Option('--days', help='Simulated days.')]=60, items_per_day: Annotated[int, typer.Option('--items-per-day', help='Attempts per simulated day.')]=6, seed: Annotated[int, typer.Option('--seed', help='Student RNG seed.')]=42, fresh_copy: Annotated[bool, typer.Option('--fresh-copy/--in-place', help='Copy the vault to a tmp run dir (default) or simulate in place.')]=True, reset_state: Annotated[bool, typer.Option('--reset-state/--keep-state', help='Drop derived SQLite state in the run copy (default: reset).')]=True, sets: Annotated[list[str] | None, typer.Option('--set', help='Config override param.path=value (repeatable).')]=None, primed_retries: Annotated[bool, typer.Option('--primed-retries/--no-primed-retries', help='After each failed attempt, re-read the source and retry a sibling item as a primed attempt.')]=False, goal_due_day: Annotated[int | None, typer.Option('--goal-due-day', help="Set every active goal's due date N sim-days in (exercises the projection horizon and ramping goal quota).")]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit the full JSON report.')]=False, output: Annotated[Path | None, typer.Option('--output', '-o', help='Write the full JSON report to a file.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/sim.py), line 189) — Simulate a synthetic student through the real scheduling/belief pipeline.
- `sim_sweep_command(vault: Annotated[Path | None, typer.Option('--vault', help='Vault root (never written; each run uses a fresh copy).')]=None, spec: Annotated[Path | None, typer.Option('--spec', help='Sweep spec YAML (defaults to the packaged default_sweep.yaml).')]=None, profile: Annotated[str, typer.Option('--profile', help='Built-in profile name or profile YAML path.')]='intermediate_with_misconception', days: Annotated[int, typer.Option('--days', help='Simulated days per run.')]=30, items_per_day: Annotated[int, typer.Option('--items-per-day', help='Attempts per simulated day.')]=6, seed: Annotated[int, typer.Option('--seed', help='Student RNG seed (shared by all runs).')]=42, reset_state: Annotated[bool, typer.Option('--reset-state/--keep-state', help='Drop derived SQLite state in each run copy (default: reset).')]=True, sets: Annotated[list[str] | None, typer.Option('--set', help='Baseline config override param.path=value (repeatable).')]=None, primed_retries: Annotated[bool, typer.Option('--primed-retries/--no-primed-retries', help='Enable primed source-review retries in every run (needed for the priming_b_offset sweep).')]=False, goal_due_day: Annotated[int | None, typer.Option('--goal-due-day', help="Set every active goal's due date N sim-days in for all runs (needed for the goal quota sweeps).")]=None, json_output: Annotated[bool, typer.Option('--json', help='Emit the full JSON report.')]=False, output: Annotated[Path | None, typer.Option('--output', '-o', help='Write the full JSON report to a file.')]=None) -> None` ([source](../../../../../../src/learnloop/cli/sim.py), line 279) — Sweep config parameters and report which ones change scheduling decisions.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `module`
- [[Reference/Modules/learnloop/diagnosis/probe_audit|learnloop.diagnosis.probe_audit]] — imports `pilot_report`; calls `pilot_report`
- [[Reference/Modules/learnloop/sim/diagnostic_validation|learnloop.sim.diagnostic_validation]] — imports `PLANTED_TYPES`, `run_probe_validation`; calls `run_probe_validation`
- [[Reference/Modules/learnloop/sim/offline_benchmarks|learnloop.sim.offline_benchmarks]] — imports `run_forgetting_benchmark`; calls `run_forgetting_benchmark`
- [[Reference/Modules/learnloop/sim/profiles|learnloop.sim.profiles]] — imports `ProfileError`, `load_profile`; calls `load_profile`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `SimulationError`, `run_simulation`; calls `run_simulation`
- [[Reference/Modules/learnloop/sim/sweep|learnloop.sim.sweep]] — imports `SweepSpecError`, `load_sweep_spec`, `run_sweep`; calls `load_sweep_spec`, `run_sweep`

### Platform and third-party dependencies

- Standard library: `__future__`, `tempfile`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_cli_generate_practice.py](../../../../../../tests/test_cli_generate_practice.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_cli_ingest.py](../../../../../../tests/test_cli_ingest.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]
- [tests/test_teach_back_generation.py](../../../../../../tests/test_teach_back_generation.py) — imports consumer [[Reference/Modules/learnloop/cli/__init__|learnloop.cli]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/cli/sim.py](../../../../../../src/learnloop/cli/sim.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

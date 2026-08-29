---
title: "learnloop.sim.offline_benchmarks"
type: "module-reference"
status: "current"
refactor_status: "EVALUATION"
version: "1.0.0"
source_path: "src/learnloop/sim/offline_benchmarks.py"
source_paths:
  - "src/learnloop/sim/offline_benchmarks.py"
source_commit: "b19e81d9993c28e995049da1aa16f8d316d56d68"
source_commit_timestamp: "2026-07-13T13:41:22-04:00"
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
  - "learnloop.sim.offline_benchmarks module"
  - "src/learnloop/sim/offline_benchmarks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/evaluation"
  - "layer/simulation"
  - "package/learnloop-sim"
---

# `learnloop.sim.offline_benchmarks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.sim.offline_benchmarks` exists within [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] to own the behavior summarized by its module contract: Offline forgetting-model benchmark (spec_probe_eig_redesign.md Checkpoint 5.6).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/sim/offline_benchmarks.py](../../../../../../src/learnloop/sim/offline_benchmarks.py) |
| Source lines | 193 |
| Owning package | [[Reference/Modules/learnloop/sim/_package|learnloop.sim]] |
| Architecture layer | `simulation` |
| Refactor status | `EVALUATION` |
| Worktree state | `clean` |
| Source commit | `b19e81d9993c28e995049da1aa16f8d316d56d68` |
| Commit timestamp | `2026-07-13T13:41:22-04:00` |

> [!note] Evaluation-only authority
> This module computes shadow, audit, or offline evidence. Its outputs do not directly choose learner-facing actions unless a governed promotion path says otherwise.

## Public API

- `class BenchmarkExample` ([source](../../../../../../src/learnloop/sim/offline_benchmarks.py), line 40)
- `build_examples(repository: Repository) -> list[BenchmarkExample]` ([source](../../../../../../src/learnloop/sim/offline_benchmarks.py), line 47) — One example per graded attempt, features from strictly earlier attempts.
- `fit_logistic(examples: list[BenchmarkExample], *, learning_rate: float=0.1, iterations: int=400, l2: float=0.01) -> list[float]` ([source](../../../../../../src/learnloop/sim/offline_benchmarks.py), line 95) — Deterministic full-batch gradient descent (no RNG, fixed iterations).
- `run_forgetting_benchmark(repository: Repository, *, train_fraction: float=0.7, minimum_examples: int=20) -> dict[str, Any]` ([source](../../../../../../src/learnloop/sim/offline_benchmarks.py), line 137) — Temporal-split benchmark: DAS3H-style model vs frequency baselines.

### Module constants

- `WINDOWS_DAYS` ([src/learnloop/sim/offline_benchmarks.py](../../../../../../src/learnloop/sim/offline_benchmarks.py), line 26)
- `_EPS` ([src/learnloop/sim/offline_benchmarks.py](../../../../../../src/learnloop/sim/offline_benchmarks.py), line 27)

## Internal implementation anchors

- `_attempt_succeeded(attempt: dict[str, Any]) -> bool` ([source](../../../../../../src/learnloop/sim/offline_benchmarks.py), line 30)
- `_sigmoid(z: float) -> float` ([source](../../../../../../src/learnloop/sim/offline_benchmarks.py), line 88)
- `_clamp(probability: float) -> float` ([source](../../../../../../src/learnloop/sim/offline_benchmarks.py), line 122)
- `_metrics(predictions: list[float], outcomes: list[bool]) -> dict[str, float | int]` ([source](../../../../../../src/learnloop/sim/offline_benchmarks.py), line 126)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/sim|learnloop.cli.sim]] — imports `run_forgetting_benchmark`; statically calls `run_forgetting_benchmark`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

No direct learner/operator workflow is assigned. This module is offline, shadow-only, dormant, or a dependency reached only through the static consumers below.

Static participation evidence comes from [[Reference/Modules/learnloop/cli/sim|learnloop.cli.sim]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_offline_benchmark.py](../../../../../../tests/test_offline_benchmark.py) — direct import
  - `test_benchmark_is_deterministic_and_report_only`
  - `test_examples_use_only_prior_history`
  - `test_insufficient_data_is_reported_not_fitted`
  - `test_time_window_model_beats_static_baseline_on_forgetting_data`

## Modification guidance

- Make changes here when the responsibility remains offline benchmarks within learnloop.sim; otherwise move the behavior to its owning boundary.
- Keep this module's shadow/offline outputs decision-inert. Promotion into live policy requires the governed evidence and cutover path documented by its source contract.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/sim/offline_benchmarks.py](../../../../../../src/learnloop/sim/offline_benchmarks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

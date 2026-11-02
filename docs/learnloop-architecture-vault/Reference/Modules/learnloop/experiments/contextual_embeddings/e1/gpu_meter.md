---
title: "learnloop.experiments.contextual_embeddings.e1.gpu_meter"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/e1/gpu_meter.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/e1/gpu_meter.py"
source_commit: "5bcead897e0c117ad063e707611aacf640acddad"
source_commit_timestamp: "2026-10-24T00:11:39-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.experiments.contextual_embeddings.e1"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.experiments.contextual_embeddings.e1.gpu_meter module"
  - "src/learnloop/experiments/contextual_embeddings/e1/gpu_meter.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings-e1"
---

# `learnloop.experiments.contextual_embeddings.e1.gpu_meter`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.e1.gpu_meter` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] to own the behavior summarized by its module contract: The E1 GPU-hours meter: <= 4 GPU-hours for ALL of E1 (spec §8, D2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/e1/gpu_meter.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/gpu_meter.py) |
| Source lines | 190 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/_package|learnloop.experiments.contextual_embeddings.e1]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `5bcead897e0c117ad063e707611aacf640acddad` |
| Commit timestamp | `2026-10-24T00:11:39-04:00` |

## Public API

- `class GpuBudgetExceeded(RuntimeError)` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/gpu_meter.py), line 40) — The GPU-hours allowance cannot admit another worker (nothing started).
- `class GpuMeter` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/gpu_meter.py), line 44)
  - `__init__(self, directory: Path, *, cap_hours: float=e1_pins.GPU_HOURS_CAP, grace_s: float=e1_pins.HEARTBEAT_GRACE_S, clock: Callable[[], float]=time.time) -> None` (line 45; internal)
  - `_locked(self) -> Iterator[dict[str, Any]]` (line 56; internal)
  - `_charged(self, entry: dict[str, Any], now: float) -> float` (line 74; internal)
  - `_fresh(self, entry: dict[str, Any], now: float) -> bool` (line 83; internal)
  - `used_s(self) -> float` (line 87; public)
  - `remaining_s(self) -> float` (line 92; public)
  - `open(self, *, plan_id: str, label: str, min_slot_s: float=MIN_SLOT_S) -> tuple[str, float]` (line 95; public) — A new entry and its deadline (unix seconds); refused when the allowance left is below ``min_slot_s`` or another worker is live.
  - `heartbeat(self, entry_id: str, at: float | None=None) -> None` (line 114; public)
  - `close(self, entry_id: str, *, status: str, returncode: int | None=None) -> float` (line 120; public)
  - `report(self) -> dict[str, Any]` (line 128; public)
- `supervise(command: Sequence[str], *, meter: GpuMeter, plan_id: str, label: str, heartbeat: Path, env: dict[str, str] | None=None, popen: Callable[..., Any]=subprocess.Popen, poll_s: float=5.0, sleep: Callable[[float], None]=time.sleep, kill_grace_s: float=e1_pins.KILL_GRACE_S, min_slot_s: float=MIN_SLOT_S, on_open: Callable[[float], None] | None=None, log: Path | None=None) -> dict[str, Any]` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/gpu_meter.py), line 139) — Run one worker under the meter.

### Module constants

- `METER_NAME` ([src/learnloop/experiments/contextual_embeddings/e1/gpu_meter.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/gpu_meter.py), line 35)
- `MIN_SLOT_S` ([src/learnloop/experiments/contextual_embeddings/e1/gpu_meter.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/gpu_meter.py), line 37)

## Internal implementation anchors

- `_read_heartbeat(path: Path) -> float | None` ([source](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/gpu_meter.py), line 186)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/local|learnloop.experiments.contextual_embeddings.e1.local]] — imports `GpuMeter`, `supervise`; statically calls `supervise`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]] — imports `GpuMeter`, `MIN_SLOT_S`; statically calls `GpuMeter`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/pins|learnloop.experiments.contextual_embeddings.e1.pins]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `fcntl`, `json`, `os`, `pathlib`, `signal`, `subprocess`, `time`, `typing`, `uuid`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/local|learnloop.experiments.contextual_embeddings.e1.local]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/run|learnloop.experiments.contextual_embeddings.e1.run]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e1_gpu_meter.py](../../../../../../../../tests/test_e1_gpu_meter.py) — direct import
  - `test_a_different_cap_cannot_reopen_the_meter`
  - `test_a_finished_child_is_closed_with_its_return_code`
  - `test_a_live_worker_blocks_a_second_one_and_a_crashed_one_is_charged_to_its_heartbeat`
  - `test_each_worker_is_charged_its_wall_time_and_the_cap_is_cumulative`
  - `test_the_cap_stops_the_supervised_child_and_it_is_charged`
- [tests/test_e1_harness.py](../../../../../../../../tests/test_e1_harness.py) — direct import
  - `test_the_scoped_launcher_caps_memory_and_passes_no_key`
- [tests/test_e1_worker.py](../../../../../../../../tests/test_e1_worker.py) — direct import
  - `test_the_supervised_worker_writes_its_stderr_to_the_log`

## Modification guidance

- Make changes here when the responsibility remains gpu meter within learnloop.experiments.contextual_embeddings.e1; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/e1/gpu_meter.py](../../../../../../../../src/learnloop/experiments/contextual_embeddings/e1/gpu_meter.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

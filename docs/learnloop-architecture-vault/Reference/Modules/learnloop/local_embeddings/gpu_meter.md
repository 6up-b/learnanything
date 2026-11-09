---
title: "learnloop.local_embeddings.gpu_meter"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/local_embeddings/gpu_meter.py"
source_paths:
  - "src/learnloop/local_embeddings/gpu_meter.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.local_embeddings"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.local_embeddings.gpu_meter module"
  - "src/learnloop/local_embeddings/gpu_meter.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-local-embeddings"
---

# `learnloop.local_embeddings.gpu_meter`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.local_embeddings.gpu_meter` exists within [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] to own the behavior summarized by its module contract: The GPU-hours meter, moved from E1 (spec_local_contextual_retrieval_v1 §7.2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/local_embeddings/gpu_meter.py](../../../../../../src/learnloop/local_embeddings/gpu_meter.py) |
| Source lines | 192 |
| Owning package | [[Reference/Modules/learnloop/local_embeddings/_package|learnloop.local_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class GpuBudgetExceeded(RuntimeError)` ([source](../../../../../../src/learnloop/local_embeddings/gpu_meter.py), line 39) — The GPU-hours allowance cannot admit another worker (nothing started).
- `class GpuMeter` ([source](../../../../../../src/learnloop/local_embeddings/gpu_meter.py), line 43)
  - `__init__(self, directory: Path, *, cap_hours: float | None=None, grace_s: float=local_pins.HEARTBEAT_GRACE_S, clock: Callable[[], float]=time.time) -> None` (line 44; internal)
  - `_locked(self) -> Iterator[dict[str, Any]]` (line 55; internal)
  - `_charged(self, entry: dict[str, Any], now: float) -> float` (line 74; internal)
  - `_fresh(self, entry: dict[str, Any], now: float) -> bool` (line 83; internal)
  - `used_s(self) -> float` (line 87; public)
  - `remaining_s(self) -> float | None` (line 92; public)
  - `open(self, *, plan_id: str, label: str, min_slot_s: float=MIN_SLOT_S) -> tuple[str, float | None]` (line 95; public) — A new entry and its deadline (unix seconds, None uncapped); refused when another worker is live or a capped allowance is below ``min_slot_s``.
  - `heartbeat(self, entry_id: str, at: float | None=None) -> None` (line 114; public)
  - `close(self, entry_id: str, *, status: str, returncode: int | None=None) -> float` (line 120; public)
  - `report(self) -> dict[str, Any]` (line 128; public)
- `supervise(command: Sequence[str], *, meter: GpuMeter, plan_id: str, label: str, heartbeat: Path, env: dict[str, str] | None=None, popen: Callable[..., Any]=subprocess.Popen, poll_s: float=5.0, sleep: Callable[[float], None]=time.sleep, kill_grace_s: float=local_pins.KILL_GRACE_S, min_slot_s: float=MIN_SLOT_S, on_open: Callable[[float | None], None] | None=None, log: Path | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/local_embeddings/gpu_meter.py), line 141) — Run one worker under the meter.

### Module constants

- `METER_NAME` ([src/learnloop/local_embeddings/gpu_meter.py](../../../../../../src/learnloop/local_embeddings/gpu_meter.py), line 34)
- `MIN_SLOT_S` ([src/learnloop/local_embeddings/gpu_meter.py](../../../../../../src/learnloop/local_embeddings/gpu_meter.py), line 36)

## Internal implementation anchors

- `_read_heartbeat(path: Path) -> float | None` ([source](../../../../../../src/learnloop/local_embeddings/gpu_meter.py), line 188)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/local_embeddings/launcher|learnloop.local_embeddings.launcher]] — imports `GpuMeter`, `supervise`; statically calls `supervise`
- [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]] — imports `GpuBudgetExceeded`, `GpuMeter`; statically calls `GpuMeter`
- [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]] — imports `GpuBudgetExceeded`, `GpuMeter`; statically calls `GpuMeter`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/local_embeddings/pins|learnloop.local_embeddings.pins]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `fcntl`, `json`, `os`, `pathlib`, `signal`, `subprocess`, `time`, `typing`, `uuid`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/local_embeddings/launcher|learnloop.local_embeddings.launcher]], [[Reference/Modules/learnloop/source_retrieval/local_index|learnloop.source_retrieval.local_index]], [[Reference/Modules/learnloop/source_retrieval/query_student|learnloop.source_retrieval.query_student]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_local_index.py](../../../../../../tests/test_local_index.py) — direct import
  - `test_the_meter_meters_production_uncapped_and_refuses_a_second_live_worker`
- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — direct import
  - `test_targets_are_one_metered_query_batch_with_the_canaries_and_the_cosine_guard`
  - `test_the_schedule_screens_both_bases_then_recipes_then_seeds_by_expected_utility`

## Modification guidance

- Make changes here when the responsibility remains gpu meter within learnloop.local_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/local_embeddings/gpu_meter.py](../../../../../../src/learnloop/local_embeddings/gpu_meter.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

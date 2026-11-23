---
title: "learnloop_sidecar.polled_jobs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/polled_jobs.py"
source_paths:
  - "src/learnloop_sidecar/polled_jobs.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.polled_jobs module"
  - "src/learnloop_sidecar/polled_jobs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.polled_jobs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.polled_jobs` exists within [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] to own the behavior summarized by its module contract: Jobs the workbench polls (spec_reader_workbench_v2 §3.4: "long work is a job").

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py) |
| Source lines | 289 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class PolledJob` ([source](../../../../../src/learnloop_sidecar/polled_jobs.py), line 59)
  - `note(self, **values: Any) -> None` (line 82; public)
  - `state(self) -> dict[str, Any]` (line 86; public) — A consistent reading of the job: ``status`` as a poll reports it, and what it holds.
- `class Receipt` ([source](../../../../../src/learnloop_sidecar/polled_jobs.py), line 108) — What is kept of a dropped job: enough to answer a repeat of its id.
- `as_job_error(exc: BaseException, *, cancelled: bool) -> SidecarError` ([source](../../../../../src/learnloop_sidecar/polled_jobs.py), line 141) — A job's failure as the poll reports it.
- `class PolledJobs` ([source](../../../../../src/learnloop_sidecar/polled_jobs.py), line 187) — One kind of polled job in one sidecar context: running and recently finished jobs by id.
  - `__init__(self, *, kept: int=MAX_KEPT_JOBS, receipts: int=MAX_RECEIPTS) -> None` (line 190; internal)
  - `get(self, job_id: str) -> PolledJob | None` (line 197; public)
  - `receipt(self, job_id: str) -> Receipt | None` (line 201; public)
  - `cancel(self, job_id: str) -> PolledJob | None` (line 205; public) — Cancel a job that has not finished (a finished job keeps its outcome).
  - `_drop_finished(self) -> None` (line 215; internal) — Under ``self._lock``: drop the oldest finished jobs beyond the bound, keeping their receipts.
  - `start(self, ctx: Any, *, kind: str, job_id: str, work: Callable[[PolledJob], Any], request_key: Any=None, foreground_kind: str | None=None, supersede_key: str | None=None) -> PolledJob` (line 228; public) — Start ``work(job)`` on a thread the context owns; its return value is the job's result.
- `registry(ctx: Any, name: str) -> PolledJobs` ([source](../../../../../src/learnloop_sidecar/polled_jobs.py), line 278) — ``ctx``'s registry of one kind of polled job (made on first use).

### Module constants

- `LOG` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 40)
- `MAX_KEPT_JOBS` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 43)
- `MAX_RECEIPTS` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 45)
- `QUEUED` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 47)
- `RUNNING` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 48)
- `DONE` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 49)
- `FAILED` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 50)
- `CANCELLED` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 51)
- `EXPIRED` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 52)
- `INTERRUPTED_MESSAGE` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 54)
- `INTERNAL_MESSAGE` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 55)

### Explicit exports

`__all__` declares:

- `CANCELLED`
- `DONE`
- `EXPIRED`
- `FAILED`
- `MAX_KEPT_JOBS`
- `MAX_RECEIPTS`
- `QUEUED`
- `RUNNING`
- `PolledJob`
- `PolledJobs`
- `Receipt`
- `as_job_error`
- `registry`

## Internal implementation anchors

- `class _CancelGate` ([source](../../../../../src/learnloop_sidecar/polled_jobs.py), line 118) — Refuses a cancelled job's physical model requests before they are sent; an outer gate (the context's closing gate) is admitted first and settled on a refusal, so nothing it reserved is kept for a request never sent.
- `_job_scope(job: PolledJob, repository: Any, owner_id: str, foreground_kind: str | None) -> Iterator[None]` ([source](../../../../../src/learnloop_sidecar/polled_jobs.py), line 167)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/companion_ask|learnloop_sidecar.handlers.companion_ask]] — imports `module`; statically calls `registry`
- [[Reference/Modules/learnloop_sidecar/handlers/search|learnloop_sidecar.handlers.search]] — imports `module`; statically calls `registry`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `active_request_gate`, `gate_model_requests`, `observe_model_output`, `record_model_calls`; calls `active_request_gate`, `gate_model_requests`, `observe_model_output`, `record_model_calls`
- [[Reference/Modules/learnloop/ai/model_use|learnloop.ai.model_use]] — imports `ModelUseNotAccepted`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `note_unit`, `unit`, `unit_origin`, `unit_stamp`, `unit_token`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCancelled`; calls `SpendCancelled`
- [[Reference/Modules/learnloop/figures/foreground|learnloop.figures.foreground]] — imports `foreground`; calls `foreground`
- [[Reference/Modules/learnloop_sidecar/background_jobs|learnloop_sidecar.background_jobs]] — imports `background_jobs`; calls `background_jobs`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`, `waiting_for_ok_error`; calls `SidecarError`, `waiting_for_ok_error`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `logging`, `sqlite3`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/companion_ask|learnloop_sidecar.handlers.companion_ask]], [[Reference/Modules/learnloop_sidecar/handlers/search|learnloop_sidecar.handlers.search]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rd3a_companion_ask.py](../../../../../tests/test_reader_rd3a_companion_ask.py) — direct import
  - `test_a_finished_job_dropped_from_memory_is_answered_as_expired_never_asked_again`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

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
| Source lines | 424 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `vault_key(ctx: Any) -> str` ([source](../../../../../src/learnloop_sidecar/polled_jobs.py), line 75) — The vault a job belongs to: the context's open vault, resolved ("" with none open).
- `class PolledJob` ([source](../../../../../src/learnloop_sidecar/polled_jobs.py), line 83)
  - `live(self) -> bool` (line 116; public) — False once the context closed or switched vaults after this job started: its completion then touches nothing of the context (no worker woken, no prefetch queued).
  - `note(self, **values: Any) -> None` (line 122; public)
  - `state(self) -> dict[str, Any]` (line 126; public) — A consistent reading of the job: ``status`` as a poll reports it, and what it holds.
- `class Receipt` ([source](../../../../../src/learnloop_sidecar/polled_jobs.py), line 153) — What a registry keeps of a request id apart from its result: enough to answer a repeat of it.
- `as_job_error(exc: BaseException, *, cancelled: bool) -> SidecarError` ([source](../../../../../src/learnloop_sidecar/polled_jobs.py), line 190) — A job's failure as the poll reports it.
- `class PolledJobs` ([source](../../../../../src/learnloop_sidecar/polled_jobs.py), line 239) — One kind of polled job in one sidecar context: running and recently finished jobs, by vault and id.
  - `__init__(self, *, kept: int=MAX_KEPT_JOBS, running: int=MAX_RUNNING, remember_ids: bool=True, remembered: int=MAX_REMEMBERED_IDS, receipts: int=MAX_RECEIPTS) -> None` (line 246; internal)
  - `get(self, vault: str, job_id: str) -> PolledJob | None` (line 256; public)
  - `receipt(self, vault: str, job_id: str) -> Receipt | None` (line 260; public) — The record of an id this registry admitted in ``vault`` whose result is no longer kept.
  - `known(self, vault: str, job_id: str) -> PolledJob | Receipt | None` (line 268; public)
  - `kept_count(self) -> int` (line 271; public)
  - `cancel(self, vault: str, job_id: str) -> PolledJob | None` (line 275; public) — Cancel a job that has not finished (a finished job keeps its outcome).
  - `interrupt(self, vault: str) -> None` (line 285; public) — Interrupt every unfinished job of ``vault`` (its vault was switched away from).
  - `supersede(self, vault: str, key: str) -> None` (line 295; public) — Cancel every unfinished job of ``vault`` with this supersede key (a newer request replaces them).
  - `_running_now(self) -> int` (line 306; internal) — Under ``self._lock``: jobs whose thread has not ended (a cancelled one still holds its thread).
  - `_drop_finished(self) -> None` (line 312; internal) — Under ``self._lock``: drop the oldest finished results beyond the bound; their records stay.
  - `_finished(self) -> None` (line 331; internal)
  - `start(self, ctx: Any, *, kind: str, job_id: str, work: Callable[[PolledJob], Any], request_key: Any=None, foreground_kind: str | None=None, supersede_key: str | None=None, attachments: dict[str, Any] | None=None) -> PolledJob` (line 335; public) — Start ``work(job)`` on a thread the context owns; its return value is the job's result.
- `registry(ctx: Any, name: str, **kwargs: Any) -> PolledJobs` ([source](../../../../../src/learnloop_sidecar/polled_jobs.py), line 395) — ``ctx``'s registry of one kind of polled job (made on first use with ``kwargs``).
- `interrupt_vault(ctx: Any, vault_root: Any) -> None` ([source](../../../../../src/learnloop_sidecar/polled_jobs.py), line 410) — A vault switch: every unfinished polled job of ``vault_root`` sends no further request, ends ``interrupted`` and wakes nothing of the context.

### Module constants

- `LOG` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 50)
- `MAX_KEPT_JOBS` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 53)
- `MAX_RUNNING` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 55)
- `MAX_REMEMBERED_IDS` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 57)
- `MAX_RECEIPTS` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 59)
- `QUEUED` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 61)
- `RUNNING` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 62)
- `DONE` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 63)
- `FAILED` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 64)
- `CANCELLED` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 65)
- `EXPIRED` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 66)
- `INTERRUPTED_MESSAGE` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 68)
- `INTERNAL_MESSAGE` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 69)
- `BUSY_MESSAGE` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 70)
- `IDS_FULL_MESSAGE` ([src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py), line 71)

### Explicit exports

`__all__` declares:

- `CANCELLED`
- `DONE`
- `EXPIRED`
- `FAILED`
- `MAX_KEPT_JOBS`
- `MAX_RECEIPTS`
- `MAX_REMEMBERED_IDS`
- `MAX_RUNNING`
- `QUEUED`
- `RUNNING`
- `PolledJob`
- `PolledJobs`
- `Receipt`
- `as_job_error`
- `interrupt_vault`
- `registry`
- `vault_key`

## Internal implementation anchors

- `class _CancelGate` ([source](../../../../../src/learnloop_sidecar/polled_jobs.py), line 165) — Refuses a cancelled job's physical model requests before they are sent and counts the ones it admits; an outer gate (the context's closing gate) is admitted first and settled on a refusal, so nothing it reserved is kept for a request never sent.
- `_job_scope(job: PolledJob, repository: Any, owner_id: str, foreground_kind: str | None) -> Iterator[None]` ([source](../../../../../src/learnloop_sidecar/polled_jobs.py), line 216)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `interrupt_vault`; statically calls `interrupt_vault`
- [[Reference/Modules/learnloop_sidecar/handlers/companion_ask|learnloop_sidecar.handlers.companion_ask]] — imports `module`; statically calls `registry`, `vault_key`
- [[Reference/Modules/learnloop_sidecar/handlers/ink|learnloop_sidecar.handlers.ink]] — imports `module`; statically calls `registry`, `vault_key`
- [[Reference/Modules/learnloop_sidecar/handlers/passage_union|learnloop_sidecar.handlers.passage_union]] — imports `module`; statically calls `registry`, `vault_key`
- [[Reference/Modules/learnloop_sidecar/handlers/search|learnloop_sidecar.handlers.search]] — imports `module`; statically calls `as_job_error`, `registry`, `vault_key`
- [[Reference/Modules/learnloop_sidecar/handlers/video|learnloop_sidecar.handlers.video]] — imports `module`; statically calls `registry`, `vault_key`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `active_request_gate`, `annotate_calls`, `gate_model_requests`, `observe_model_output`, `record_model_calls`; calls `active_request_gate`, `annotate_calls`, `gate_model_requests`, `observe_model_output`, `record_model_calls`
- [[Reference/Modules/learnloop/ai/model_use|learnloop.ai.model_use]] — imports `ModelUseNotAccepted`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `module`; calls `note_unit`, `unit`, `unit_origin`, `unit_stamp`, `unit_token`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCancelled`; calls `SpendCancelled`
- [[Reference/Modules/learnloop/figures/foreground|learnloop.figures.foreground]] — imports `foreground`; calls `foreground`
- [[Reference/Modules/learnloop_sidecar/background_jobs|learnloop_sidecar.background_jobs]] — imports `background_jobs`; calls `background_jobs`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`, `waiting_for_ok_error`; calls `SidecarError`, `waiting_for_ok_error`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `logging`, `pathlib`, `sqlite3`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/companion_ask|learnloop_sidecar.handlers.companion_ask]], [[Reference/Modules/learnloop_sidecar/handlers/ink|learnloop_sidecar.handlers.ink]], [[Reference/Modules/learnloop_sidecar/handlers/passage_union|learnloop_sidecar.handlers.passage_union]], [[Reference/Modules/learnloop_sidecar/handlers/search|learnloop_sidecar.handlers.search]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/companion_rd3a_helpers.py](../../../../../tests/companion_rd3a_helpers.py) — direct import
- [tests/test_menu_promoted_rows.py](../../../../../tests/test_menu_promoted_rows.py) — direct import
  - `test_a_menu_whose_vault_was_switched_away_from_delivers_nothing`
- [tests/test_reader_rd3_fix_backend.py](../../../../../tests/test_reader_rd3_fix_backend.py) — direct import
  - `test_a_full_record_of_ids_refuses_a_new_id_rather_than_forget_one`
  - `test_a_request_id_is_remembered_after_its_result_is_dropped`
  - `test_results_are_pruned_as_jobs_finish_not_only_when_the_next_starts`
  - `test_running_asks_are_bounded`
- [tests/test_reader_rd3a_companion_ask.py](../../../../../tests/test_reader_rd3a_companion_ask.py) — direct import
  - `test_a_finished_job_dropped_from_memory_is_answered_as_expired_never_asked_again`
- [tests/test_reader_rd8a_rpcs.py](../../../../../tests/test_reader_rd8a_rpcs.py) — direct import
  - `test_a_cancel_before_the_request_is_sent_sends_nothing`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/polled_jobs.py](../../../../../src/learnloop_sidecar/polled_jobs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop_sidecar.background_jobs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/background_jobs.py"
source_paths:
  - "src/learnloop_sidecar/background_jobs.py"
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
  - "learnloop_sidecar.background_jobs module"
  - "src/learnloop_sidecar/background_jobs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.background_jobs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.background_jobs` exists within [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] to own the behavior summarized by its module contract: The asynchronous jobs a sidecar context starts from a request (test-thread-leak review F1).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/background_jobs.py](../../../../../src/learnloop_sidecar/background_jobs.py) |
| Source lines | 142 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class BackgroundJobs` ([source](../../../../../src/learnloop_sidecar/background_jobs.py), line 66) — The request-started job threads of one sidecar context.
  - `__init__(self) -> None` (line 69; internal)
  - `epoch(self) -> int` (line 74; public) — The epoch a job starting now belongs to (capture it before building the job's cancellation predicate, and pass it to :meth:`spawn`).
  - `closed_since(self, epoch: int) -> bool` (line 81; public) — Whether the context was closed after a job of ``epoch`` started.
  - `spawn(self, target: Callable[[], Any], *, name: str, epoch: int | None=None) -> threading.Thread` (line 87; public) — Start ``target`` on a daemon thread owned by this context: a close cancels it (its requests refused from then on) and joins it, bounded.
  - `cancel(self) -> list[threading.Thread]` (line 104; public) — End the current epoch: every job started so far is cancelled.
  - `close(self, timeout: float=CLOSE_JOIN_SECONDS) -> None` (line 113; public) — Cancel every job started so far, then join them for at most ``timeout`` seconds in all.
  - `running(self) -> list[threading.Thread]` (line 124; public)
- `background_jobs(ctx: Any) -> BackgroundJobs` ([source](../../../../../src/learnloop_sidecar/background_jobs.py), line 129) — ``ctx``'s job registry (a stand-in context without one gets its own).

### Module constants

- `CLOSE_JOIN_SECONDS` ([src/learnloop_sidecar/background_jobs.py](../../../../../src/learnloop_sidecar/background_jobs.py), line 39)

### Explicit exports

`__all__` declares:

- `CLOSE_JOIN_SECONDS`
- `BackgroundJobs`
- `background_jobs`

## Internal implementation anchors

- `class _ClosingGate` ([source](../../../../../src/learnloop_sidecar/background_jobs.py), line 42) — Refuses a job's physical model requests once its epoch has ended; an outer gate (installed by the job itself) is admitted first and settled on a refusal, so nothing it reserved is kept for a request never sent.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `BackgroundJobs`
- [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]] — imports `background_jobs`; statically calls `background_jobs`
- [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]] — imports `background_jobs`; statically calls `background_jobs`
- [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]] — imports `background_jobs`; statically calls `background_jobs`
- [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] — imports `background_jobs`; statically calls `background_jobs`
- [[Reference/Modules/learnloop_sidecar/handlers/notes|learnloop_sidecar.handlers.notes]] — imports `background_jobs`; statically calls `background_jobs`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_cue_discovery|learnloop_sidecar.handlers.reader_cue_discovery]] — imports `background_jobs`; statically calls `background_jobs`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_followups|learnloop_sidecar.handlers.reader_followups]] — imports `background_jobs`; statically calls `background_jobs`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_intent|learnloop_sidecar.handlers.reader_intent]] — imports `background_jobs`; statically calls `background_jobs`
- [[Reference/Modules/learnloop_sidecar/handlers/reading_paths|learnloop_sidecar.handlers.reading_paths]] — imports `background_jobs`; statically calls `background_jobs`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `active_request_gate`, `gate_model_requests`; calls `active_request_gate`, `gate_model_requests`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendCancelled`; calls `SpendCancelled`

### Platform and third-party dependencies

- Standard library: `__future__`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/correspondents|learnloop_sidecar.handlers.correspondents]], [[Reference/Modules/learnloop_sidecar/handlers/deliverables|learnloop_sidecar.handlers.deliverables]], [[Reference/Modules/learnloop_sidecar/handlers/hints|learnloop_sidecar.handlers.hints]], [[Reference/Modules/learnloop_sidecar/handlers/library_ask|learnloop_sidecar.handlers.library_ask]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_notes_linked.py](../../../../../tests/test_notes_linked.py) — direct import
  - `test_f4_background_linking_completes_and_the_next_read_shows_it`
- [tests/test_reader_digest_narrative.py](../../../../../tests/test_reader_digest_narrative.py) — direct import
  - `test_the_background_job_narrates_waiting_sessions`
  - `test_the_queue_build_narrates_a_session_with_follow_ups_off`
  - `test_with_the_narrative_off_the_queue_build_starts_no_narration_job`
- [tests/test_reader_rw6b_p2_landing.py](../../../../../tests/test_reader_rw6b_p2_landing.py) — direct import
- [tests/test_sidecar_close_cancels_jobs.py](../../../../../tests/test_sidecar_close_cancels_jobs.py) — direct import
  - `test_a_closed_contexts_job_has_its_next_physical_request_refused`
  - `test_close_is_bounded_when_a_job_does_not_return`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/background_jobs.py](../../../../../src/learnloop_sidecar/background_jobs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

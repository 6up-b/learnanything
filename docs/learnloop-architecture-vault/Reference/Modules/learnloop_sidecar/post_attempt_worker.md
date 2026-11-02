---
title: "learnloop_sidecar.post_attempt_worker"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/post_attempt_worker.py"
source_paths:
  - "src/learnloop_sidecar/post_attempt_worker.py"
source_commit: "cb5b8773979685c93c470bf76e9a5cf5840bb53c"
source_commit_timestamp: "2026-11-02T15:58:22-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.post_attempt_worker module"
  - "src/learnloop_sidecar/post_attempt_worker.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.post_attempt_worker`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.post_attempt_worker` exists within [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] to own the behavior summarized by its module contract: The sidecar's post-attempt worker (Slice 1 §11).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/post_attempt_worker.py](../../../../../src/learnloop_sidecar/post_attempt_worker.py) |
| Source lines | 258 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `cb5b8773979685c93c470bf76e9a5cf5840bb53c` |
| Commit timestamp | `2026-11-02T15:58:22-05:00` |

## Public API

- `class PostAttemptWorker` ([source](../../../../../src/learnloop_sidecar/post_attempt_worker.py), line 48)
  - `__init__(self, *, autostart: bool=True) -> None` (line 49; internal)
  - `note_wait(self, session_id: str, seconds: float) -> None` (line 73; public)
  - `take_wait(self, session_id: str) -> float` (line 77; public)
  - `bind(self, supplier: VaultSupplier) -> None` (line 81; public) — ``supplier`` returns the CURRENT (vault, sqlite path) or None.
  - `notify(self) -> None` (line 89; public) — A job may be runnable: wake both slots (start them on first use).
  - `running(self) -> bool` (line 111; public)
  - `shutdown(self, timeout: float=2.0) -> None` (line 115; public) — Stop the slots: each wakes and returns, and a job in flight stops before its next paid request.
  - `_repository(self, sqlite_path: Any) -> Any` (line 132; internal)
  - `run_pending(self, kind: str='diagnose', *, max_jobs: int=100, clock: Any=None) -> list[Any]` (line 138; public) — Synchronously run runnable jobs of ``kind`` (tests and drains).
  - `_run_gaps(self, vault: Any, repository: Any, *, max_jobs: int, clock: Any) -> list[Any]` (line 182; internal)
  - `_with_busy_retry(self, work: Callable[[], Any]) -> Any` (line 212; internal)
  - `_loop(self, kind: str) -> None` (line 222; internal)
  - `wait_for(self, pending: Callable[[], list[str]], timeout: float) -> tuple[list[str], float]` (line 236; public) — Wait until ``pending()`` is empty or ``timeout`` passes.

### Module constants

- `LOG` ([src/learnloop_sidecar/post_attempt_worker.py](../../../../../src/learnloop_sidecar/post_attempt_worker.py), line 28)
- `IDLE_POLL_SECONDS` ([src/learnloop_sidecar/post_attempt_worker.py](../../../../../src/learnloop_sidecar/post_attempt_worker.py), line 32)
- `BUSY_RETRIES` ([src/learnloop_sidecar/post_attempt_worker.py](../../../../../src/learnloop_sidecar/post_attempt_worker.py), line 35)
- `BUSY_BACKOFF_SECONDS` ([src/learnloop_sidecar/post_attempt_worker.py](../../../../../src/learnloop_sidecar/post_attempt_worker.py), line 36)
- `KINDS` ([src/learnloop_sidecar/post_attempt_worker.py](../../../../../src/learnloop_sidecar/post_attempt_worker.py), line 37)

### Explicit exports

`__all__` declares:

- `PostAttemptWorker`

## Internal implementation anchors

- `_is_busy(exc: BaseException) -> bool` ([source](../../../../../src/learnloop_sidecar/post_attempt_worker.py), line 42)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `PostAttemptWorker`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/split/jobs|learnloop.diagnosis.split.jobs]] — imports `process_next_job`; calls `process_next_job`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `process_next_gap_job`; calls `process_next_gap_job`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextvars`, `logging`, `sqlite3`, `threading`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_figures_prefetch.py](../../../../../tests/test_figures_prefetch.py) — direct import
  - `test_the_gap_worker_fires_the_gap_trigger_after_a_drain`
- [tests/test_learner_text_gaps_flow.py](../../../../../tests/test_learner_text_gaps_flow.py) — direct import
  - `test_the_sidecar_queues_the_reading_and_the_overlay_shows_it_with_undo`
- [tests/test_learner_text_gaps_rereview.py](../../../../../tests/test_learner_text_gaps_rereview.py) — direct import
  - `test_rr_f3_the_sidecar_drain_goes_on_past_a_text_backing_off`
- [tests/test_learner_text_gaps_review.py](../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f16_a_removed_edge_reloads_once_and_bumps_nothing`
- [tests/test_library_ask_review.py](../../../../../tests/test_library_ask_review.py) — direct import
  - `test_the_pinned_tutor_burns_a_reserve_it_reproduces_and_joins_history_and_gaps`
- [tests/test_post_attempt_worker.py](../../../../../tests/test_post_attempt_worker.py) — direct import
  - `test_busy_database_is_retried_with_backoff`
- [tests/test_sidecar_close_cancels_jobs.py](../../../../../tests/test_sidecar_close_cancels_jobs.py) — direct import
  - `test_shutting_down_the_gaps_slot_inside_a_request_sends_no_further_request`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/post_attempt_worker.py](../../../../../src/learnloop_sidecar/post_attempt_worker.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

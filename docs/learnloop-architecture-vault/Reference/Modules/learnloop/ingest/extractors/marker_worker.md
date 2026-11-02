---
title: "learnloop.ingest.extractors.marker_worker"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/extractors/marker_worker.py"
source_paths:
  - "src/learnloop/ingest/extractors/marker_worker.py"
source_commit: "5aa3282f0214010ad88ae1b6a15c2024b76a3816"
source_commit_timestamp: "2026-10-15T07:39:48-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ingest.extractors"
layer: "infrastructure"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
aliases:
  - "learnloop.ingest.extractors.marker_worker module"
  - "src/learnloop/ingest/extractors/marker_worker.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest-extractors"
---

# `learnloop.ingest.extractors.marker_worker`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.extractors.marker_worker` exists within [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] to own the behavior summarized by its module contract: Marker, in a worker process of its own (docs/reviews/marker-pdfium-worker.md).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/extractors/marker_worker.py](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py) |
| Source lines | 483 |
| Owning package | [[Reference/Modules/learnloop/ingest/extractors/_package|learnloop.ingest.extractors]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `5aa3282f0214010ad88ae1b6a15c2024b76a3816` |
| Commit timestamp | `2026-10-15T07:39:48-04:00` |

## Public API

- `class MarkerWorkerError(RuntimeError)` ([source](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 85) — Marker's worker could not read the PDF: Marker failed in it, or the worker crashed (``health_flag`` = ``marker_worker_crashed``) or ran out of time (``marker_worker_timed_out``).
  - `__init__(self, message: str, *, health_flag: str | None=None)` (line 90; internal)
- `run_marker(task: str, raw: bytes, options: Mapping[str, Any], *, pages: int | None=None, torch_device: str | None=None, extractor_version: str | None=None, interrupt: Callable[[], None] | None=None) -> Any` ([source](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 95) — Read the PDF ``raw`` with Marker in a worker process.

### Module constants

- `LOG` ([src/learnloop/ingest/extractors/marker_worker.py](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 60)
- `WORKER_CRASHED` ([src/learnloop/ingest/extractors/marker_worker.py](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 62)
- `WORKER_TIMED_OUT` ([src/learnloop/ingest/extractors/marker_worker.py](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 63)
- `_WORKER` ([src/learnloop/ingest/extractors/marker_worker.py](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 65)
- `_WORKER_MIN_SECONDS` ([src/learnloop/ingest/extractors/marker_worker.py](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 69)
- `_WORKER_SECONDS_PER_PAGE` ([src/learnloop/ingest/extractors/marker_worker.py](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 70)
- `_WORKER_UNKNOWN_PAGES` ([src/learnloop/ingest/extractors/marker_worker.py](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 72)
- `_POLL_SECONDS` ([src/learnloop/ingest/extractors/marker_worker.py](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 74)
- `_LOG_TAIL` ([src/learnloop/ingest/extractors/marker_worker.py](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 75)
- `_ORPHANED` ([src/learnloop/ingest/extractors/marker_worker.py](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 77)
- `_SOURCE` ([src/learnloop/ingest/extractors/marker_worker.py](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 79)
- `_ANSWER` ([src/learnloop/ingest/extractors/marker_worker.py](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 80)
- `_PARTIAL` ([src/learnloop/ingest/extractors/marker_worker.py](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 81)
- `_LOG` ([src/learnloop/ingest/extractors/marker_worker.py](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 82)

### Explicit exports

`__all__` declares:

- `MarkerWorkerError`
- `WORKER_CRASHED`
- `WORKER_TIMED_OUT`
- `run_marker`

## Internal implementation anchors

- `_own_process_group() -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 153) — POSIX: the worker leads a new session, so its process group is it and everything it starts.
- `_send(worker: subprocess.Popen, request: bytes) -> threading.Thread` ([source](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 163) — Write the request to the worker's stdin and keep stdin open (its end is how the worker knows this process is alive).
- `_wait(worker: subprocess.Popen, timeout: float, interrupt: Callable[[], None] | None) -> None` ([source](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 182)
- `_exited(worker: subprocess.Popen, seconds: float) -> bool` ([source](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 196) — Whether the worker exits within ``seconds``.
- `_stop(worker: subprocess.Popen, sender: threading.Thread | None=None) -> int` ([source](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 222) — End the reading's processes, the worker and everything it started, whether it answered, crashed, ran out of time or was cancelled; reap the worker and close its stdin.
- `_page_count(raw: bytes) -> int` ([source](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 246) — The PDF's pages, read by pypdf (pure Python: never pdfium here).
- `_answer(path: Path) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 257)
- `_tail(path: Path) -> str` ([source](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 265)
- `_worker_main() -> None` ([source](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 276) — The private directory in ``sys.argv[1]``: the request on stdin (one JSON line), ``source.pdf`` in, ``answer.json`` (``{"result": ...}`` or ``{"error": ...}``) out.
- `_read_request() -> bytes | None` ([source](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 306) — The request's line from stdin (read from the descriptor, as the watcher does), or None when stdin ends first.
- `_exit_with_parent(directory: Path) -> None` ([source](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 322) — Stop when the process that started this one is gone (the sidecar quit or was killed): only it holds the other end of stdin, so stdin ends.
- `_orphaned(directory: Path) -> NoReturn` ([source](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 341) — The process that started this one is gone, and with it the cleanup of the private directory: remove this worker's own files there (only those, and the directory if that empties it), then end this process and every process it started.
- `_contain_descendants() -> None` ([source](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 366) — Windows: put this process in a job object that kills every process in it when its last handle closes.
- `_job_limit_information() -> Any` ([source](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 381) — ``JOBOBJECT_EXTENDED_LIMIT_INFORMATION`` (144 bytes on 64-bit Windows).
- `_assign_to_kill_on_close_job() -> None` ([source](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 421)
- `_read(request: Mapping[str, Any], path: Path) -> Any` ([source](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py), line 449)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/sources/pdf_extraction|learnloop.content.sources.pdf_extraction]] — imports `MarkerWorkerError`, `run_marker`; statically calls `run_marker`
- [[Reference/Modules/learnloop/ingest/extractors/marker|learnloop.ingest.extractors.marker]] — imports `run_marker`; statically calls `run_marker`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ingest/extractors/marker|learnloop.ingest.extractors.marker]] — imports `chunk_output_to_ir`; calls `chunk_output_to_ir`
- [[Reference/Modules/learnloop/ingest/extractors/pypdf|learnloop.ingest.extractors.pypdf]] — imports `read_embedded_outline`; calls `read_embedded_outline`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `ctypes`, `io`, `json`, `logging`, `os`, `pathlib`, `signal`, `subprocess`, `sys`, `tempfile`, `threading`, `time`, `typing`
- Third party: `marker`, `pypdf`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/sources/pdf_extraction|learnloop.content.sources.pdf_extraction]], [[Reference/Modules/learnloop/ingest/extractors/marker|learnloop.ingest.extractors.marker]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_marker_pdfium_worker.py](../../../../../../../tests/test_marker_pdfium_worker.py) — direct import
  - `test_a_marker_worker_that_crashes_or_hangs_is_recorded_and_the_import_falls_back`
  - `test_every_process_the_marker_worker_started_ends_with_its_reading`
  - `test_the_windows_job_limit_structure_has_its_documented_layout`
- [tests/test_reread_safety_landing.py](../../../../../../../tests/test_reread_safety_landing.py) — direct import
  - `test_a_marker_reread_hands_the_worker_the_stored_originals_bytes`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/extractors/marker_worker.py](../../../../../../../src/learnloop/ingest/extractors/marker_worker.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

# Marker in a pdfium worker process

Stage `marker-pdfium-worker`, branch `fix/marker-pdfium-worker`, worktree `learnanything-glmocr`, base `b9fcaf121` (mvp-0.25). This is a follow-up to the GLM-OCR quality landing ([Codex review](glm-ocr-quality-codex-review.md), owner item 3).

**Paid calls: none. Network: none.** `uv` ran with `--offline`. Marker's models came from the local `~/.cache/datalab` (every checkpoint has a manifest, so nothing downloads), and runs set `HF_HUB_OFFLINE=1`. Tests use fakes. Timings used a synthetic PDF and no vault.

## The race

PDFium is not thread-safe; pypdfium2's documentation says so. The sidecar handles requests on one thread, and the Reader renders PDF pages with pdfium in the sidecar's own process (`reader/span_view.py`). Meanwhile an import runs on the `learnloop-ingest-drain` thread.

The GLM-OCR stage already moved its own pdfium work out of the sidecar's process. Marker was still inside it, and Marker uses pdfium throughout a reading:

- its `PdfProvider` opens the file with `pypdfium2`;
- `pdftext` reads every page's text layer with it;
- the layout and OCR models look at pages that pdfium rendered.

**Fail-first.** I wrote a test that installs an on-disk fake `marker` package. Its converter opens, reads and renders pages through pypdfium2, as Marker's provider does. The test runs a Marker extraction on a thread named like the drain, while the test's thread keeps rendering through `span_view._local_pdf_page_render`. On `b9fcaf121` the whole pytest process died in all 3 of 3 runs:

- 2 runs ended with `Fatal Python error: Aborted`, and 1 with `Segmentation fault`;
- every crash was inside pypdfium2's `document.get_page`, called from the fake's converter through `marker.py` `_run_marker` on the drain thread.

A second test sends two of the Reader's own renders through pdfium at once, from four threads. On the base commit it also segfaulted the process.

## Design: (a), a worker process for Marker, plus a lock inside the Reader

I chose option (a).

- **Why not one process-wide lock.** Option (b), one lock that every in-process pdfium call takes, cannot work for Marker. A lock around a whole Marker reading would hold the Reader off for minutes to hours. A lock around each pdfium call would need wrapping calls that Marker and pdftext make into pypdfium2 and its raw ctypes layer themselves, and that code is not ours to wrap.
- **Why a worker suits Marker.** Marker is easy to run out of process:
  - its input is a file path;
  - its output reduces to the IR (or Markdown);
  - `MarkerDocumentExtractor` already rebuilt its models for every extraction.
- **The worker.** `src/learnloop/ingest/extractors/marker_worker.py` follows `glm_text_layer.pdfium_worker`:
  - it starts `sys.executable -P -c …`, so it inherits the environment and the sidecar's `PYTHONPATH`, and `-P` only drops the working directory;
  - one worker runs per reading.
- **How it differs from the GLM worker.** Marker runs for minutes, and it can print anything, so:
  - **Private directory.** The PDF and the request go in a private (0700) temporary directory, never on the command line, because the legacy path's options can carry an OpenAI-compatible API key.
  - **Answer and log.** The worker writes `answer.json`. Marker's own output (progress bars, warnings, prints) goes to `worker.log` in that directory, never to the sidecar's stdout, which carries JSON-RPC. The last 2,000 characters of that log are logged when the worker fails.
  - **The chunks task maps in the worker.** It runs `chunk_output_to_ir` and `read_embedded_outline` there and returns the IR's JSON. Figure images are hashed there and never cross the process boundary. The mapping code is unchanged, so `CHUNK_MAP_VERSION` stays 3. The IR is byte-identical to the in-process reading (same sha over 7,773 blocks; see Timings).
  - **The markdown task** returns `text_from_rendered`'s text, for the legacy one-shot `extract_pdf_markdown`.
  - **Time limit.** The larger of 30 minutes and 2 minutes a page. Pages come from the page selection, or are counted with pypdf (pure Python, 57–108 ms for 300 pages). If pypdf can't count them, the budget is 1,000 pages. The limit is there for a worker that hangs, not to cut a slow CPU or OCR reading short.
  - **Cancel.** The import's `interrupt` hook is checked every 0.5 s while the worker reads. A cancelled import now kills Marker mid-reading. Before, it ran in-process to the end. `SpendCancelled` propagates and never falls back.
  - **A parent that dies.** The worker reads its stdin file descriptor on a daemon thread. Only the parent holds the other end, so when the sidecar quits or is killed, the read sees EOF and the worker exits with status 70.
  - **Exit.** Once the answer is written, the worker leaves with `os._exit(0)` after flushing its streams, so there is no torch teardown and no wait on threads that libraries left behind.
- **`TORCH_DEVICE`** goes into the worker's environment only. The old code set `os.environ["TORCH_DEVICE"]` in the sidecar for the rest of its life, from both Marker paths.
- **Failures.** A crash or a timeout raises `MarkerWorkerError` with `health_flag`, either `marker_worker_crashed` or `marker_worker_timed_out`.
  - Under `engine = "auto"`, `extract_with_fallback` falls back to pypdf as before. It adds the cause next to `marker_failed_pypdf_fallback`.
  - An exception raised by Marker itself is an ordinary Marker failure, as it was before: the fallback flag only.
  - Under an explicit `marker` engine, the error propagates, and the import fails as itself. A Marker segfault used to take down the whole sidecar.
  - The library card's health line is unchanged, because it keys on `marker_failed_pypdf_fallback`.
- **The Reader's own renders** (`_local_pdf_page_render`, `_local_pdf_block_crop`) now take `span_view._PDFIUM_LOCK`. They also close their bitmap, page and document inside it. Before, they left them for the garbage collector, whose finalizers can run on any thread.
  - Today every caller of those renders that I found runs on the request thread (`get_span_view`, the block region, remediation, restoration and Reader-dialogue views). The lock makes "one thread in pdfium" hold however views are built later.
  - It costs nothing measurable: render medians of 69–70 ms, as before.

The GLM-OCR worker (`glm_text_layer.py`, `glm_ocr._render_pages`) is unchanged.

## pdfium users

| User | Where | Process | Before | After |
|---|---|---|---|---|
| Reader page render, block crop | `src/learnloop/reader/span_view.py` | sidecar (request thread) | in-process, no lock, objects closed by the garbage collector | **stays**: the only pdfium user in the sidecar's process, under `_PDFIUM_LOCK`, objects closed explicitly |
| Marker, durable import and repair (`MarkerDocumentExtractor`; also GLM-OCR's local fallback, `local_pdf_extractor`) | `src/learnloop/ingest/extractors/marker.py` | sidecar (ingest drain thread); CLI import | in-process `PdfConverter` | **moved** to `marker_worker` (`chunks`) |
| Marker, legacy one-shot `extract_pdf_markdown` (`ingest_source` / `fetch_source` for a PDF) | `src/learnloop/content/sources/pdf_extraction.py` | CLI or sidecar caller | in-process, one converter cached per process | **moved** to `marker_worker` (`markdown`) |
| GLM-OCR text layer (footnotes, equation numbers) | `src/learnloop/ingest/extractors/glm_text_layer.py` | worker | worker (GLM-OCR quality F1) | unchanged |
| GLM-OCR page images for a self-hosted server | `src/learnloop/ingest/extractors/glm_ocr.py` `_render_pages` | worker | worker | unchanged |
| B4 benchmark page images | `src/learnloop/source_retrieval/b4.py` `render_page` | `learnloop embeddings compare` (a CLI process with no Reader, one thread) | in-process | unchanged: never in the sidecar |

These read PDFs without pdfium:

- pypdf: fetchers, the pypdf extractor and fallback, outlines, page counts, GLM-OCR's page slicing, the acquisition preview;
- Datalab: hosted HTTP;
- the `native` engine: the chat model;
- the desktop Reader's own PDF view, which renders with pdf.js in the webview.

## Tests

`tests/test_marker_pdfium_worker.py` has 9 tests. `tests/marker_fakes.py` holds the on-disk fake `marker` package and the `fake_marker` fixture. A fake held in `sys.modules` cannot reach a worker process.

| Test | Shows | On `b9fcaf121` |
|---|---|---|
| `test_marker_never_enters_pdfium_in_this_process_while_the_reader_renders` | Both Marker paths run beside the Reader. Only the Reader's thread enters pdfium in the test process. Marker's pdfium reading still happens, in another process: the text came back, and the fake records its pid. | process crashed, 3 of 3 runs |
| `test_a_marker_worker_that_crashes_or_hangs_is_recorded_and_the_import_falls_back` | A crash (`os.abort()`) gives pypdf with `marker_failed_pypdf_fallback` and `marker_worker_crashed`; under an explicit engine it raises with that flag. A hang gives `marker_worker_timed_out`, and the worker is stopped. Marker's own error gives the plain fallback, as before. | not run (an in-process abort kills pytest) |
| `test_the_legacy_one_shot_path_reports_a_marker_worker_crash_as_its_error` | `PdfExtractionError("marker failed to convert PDF: …")` | — |
| `test_a_cancelled_import_stops_the_marker_worker` | `SpendCancelled` propagates with no fallback, and the worker is gone. | — |
| `test_marker_output_never_reaches_this_process_stdout` | What the fake prints never reaches fd 1 or fd 2 (`capfd`). | — |
| `test_a_worker_that_answered_exits_at_once_and_cleanly` | The worker exits with status 0. | written after the timing below found the abort; it failed with `[-6]` against the first watcher, then passed |
| `test_the_worker_carries_the_page_selection_and_torch_device_without_touching_this_process` | `page_range`, `pdftext_workers = 1` and `TORCH_DEVICE` reach the worker. `os.environ` here is untouched. | — |
| `test_a_marker_worker_stops_when_the_process_that_started_it_dies` | The parent is killed with SIGKILL, and the worker exits (POSIX). | — |
| `test_the_readers_own_renders_enter_pdfium_one_at_a_time` | Four threads of page renders and crops never overlap in pdfium, and each runs under the lock. | process crashed (segfault) |

The two concurrency tests passed 5 runs out of 5, and the whole file passed 5 runs out of 5 (about 6 s a run). No worker process was left behind.

In `tests/test_pdf_extraction.py`, 7 legacy Marker tests now use the on-disk fake through the worker. `test_marker_torch_device_pin_sets_env` now asserts that the worker sees the pin and that this process's environment does not.

## Found by the timing run, and fixed before commit

The first stdin watcher read `sys.stdin.buffer`. A daemon thread blocked inside the buffered reader holds its lock, so at interpreter shutdown Python waited about 10 s and then aborted with `_enter_buffered_busy`.

- **Effect.** The answer was already written, so readings still succeeded. Each one, though, paid about 10 s and ended with SIGABRT.
- **Fix.** The watcher now reads the raw file descriptor (`os.read(0, …)`), and the worker leaves with `os._exit(0)` once it has answered.
- **Guard.** `test_a_worker_that_answered_exits_at_once_and_cleanly` now covers it.

## Timings

**Setup.**

- **Machine.** RTX 5090 (CUDA), 32 cores, 30 GB of RAM, shared with other stages (load average 4–8).
- **Software.** marker-pdf 1.10.2 with torch 2.12.1+cu130. They came from the main checkout's `.venv`, run read-only: worktree `src` first on `PYTHONPATH`, `PYTHONDONTWRITEBYTECODE=1`. pypdfium2 there is 4.30.0. Nothing in the main checkout was written, and no vault was opened.
- **PDF.** A synthetic 300-page, 1.5 MB book-like PDF, generated by a scratch script. Each page has a running header, a numbered heading, 40 lines of text, a displayed formula with an equation number, a figure frame and a page number. It and the reports live under the gitignored `fixtures-local/marker-timing/`.

Final numbers, after the shutdown fix:

| Measure | Result |
|---|---|
| Marker, 300 pages, **in the worker, Reader rendering beside it** | **72.0 s**, 7,773 blocks, no health flags; only `MainThread` (the Reader) entered pdfium in the parent |
| Marker, 300 pages, old in-process path, fresh process | 71.9 s, the same 7,773 blocks; IR sha `9be183e3e52c0b40` identical to the worker's |
| Reader page render (scale 1.4, PNG), alone | median 70.3 ms, p95 72.8 ms (n = 40) |
| Reader page render **during** the 300-page import | median 71.7 ms, p95 75.3 ms, max 81.3 ms (n = 265, one every 0.2 s) |
| Marker, 10 pages, worker | median 6.92 s (8.92, 6.92, 6.50) |
| Marker, 10 pages, old in-process path, first reading after process start | median 6.70 s (7.61, 6.10, 6.70) |
| Marker, 10 pages, old in-process path, a repeat reading (torch imported, CUDA up; the durable path still rebuilt models) | median 3.01 s |
| Worker start-up in a fresh process | learnloop worker import 0.07 s; Marker and torch imports 2.5–3.0 s; `create_model_dict` 0.9–1.5 s |
| pypdf page count (the time limit) | 57–108 ms for 300 pages |
| GLM-OCR text-layer worker, 300 pages (unchanged) | 0.99–1.22 s |

**How to read these numbers.**

- **First reading after the sidecar starts.** A Marker reading in the worker costs the same as the old in-process path's first reading.
- **Later readings.** Against a later in-process reading in a sidecar that is already warm, the worker adds about 4 s: imports and CUDA set-up each time. That is about 5% of a 300-page book.
- **What the worker gives back.** The sidecar never holds torch, CUDA contexts or Marker's models after an import ends. Before, it held them for the rest of its life.
- **Pre-fix numbers.** Before the shutdown fix, the same runs measured 83.8–85.0 s for 300 pages and 14.8 s for 10 pages. The first run, with a cold disk cache, measured 101.0 s and 30.5 s.

## Open questions for the owner

1. **Time limit.** It is the larger of 30 minutes and 2 minutes a page, and is not configurable. I recommend keeping it. Marker on a GPU reads about 4 pages a second. The limit only stops a worker that hangs, and a cancel always works. Making it configurable is a one-line change if a CPU-only machine ever needs it.
2. **A warm, long-lived Marker worker** would save about 4 s on repeat imports. It would add lifecycle state (idle timeout, restarts, GPU memory held between imports). I recommend not adding it: imports are rare, and a fresh worker per reading is what makes a crash harmless.
3. **The B4 benchmark** (`source_retrieval/b4.py`) still renders with pdfium in its own CLI process. It has one thread and no Reader, so I left it unchanged.

## Gate

To be filled in from the gate runs on the final commit.

## Files

- `src/learnloop/ingest/extractors/marker_worker.py`: new. `run_marker`, `MarkerWorkerError`, the worker's side.
- `src/learnloop/ingest/extractors/marker.py`: `MarkerDocumentExtractor.extract` goes through the worker; `_run_marker` is gone.
- `src/learnloop/content/sources/pdf_extraction.py`: `_extract_with_marker` goes through the worker; the per-process converter cache is gone.
- `src/learnloop/ingest/extractors/__init__.py`: `extract_with_fallback` records a failure's `health_flag`.
- `src/learnloop/reader/span_view.py`: `_PDFIUM_LOCK`, `_pdf_page`, and explicit closes.
- `tests/marker_fakes.py`, `tests/test_marker_pdfium_worker.py`: new. `tests/test_pdf_extraction.py` is moved onto the on-disk fake.
- `docs/learnloop-architecture-vault/Maps/LearnLoop Pipeline Map.md`: Marker's worker and the Reader as the one pdfium user. `Reference/Configuration/Fields/Config - ingest.md`: the moved `pdf_extraction.py` line citations. Provenance-only churn is left for the landing.

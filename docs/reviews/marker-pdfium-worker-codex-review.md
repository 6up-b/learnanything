# Marker pdfium worker: Codex review fixes

Stage `marker-pdfium-worker`, branch `fix/marker-pdfium-worker`, worktree `learnanything-glmocr`. The Codex review (job `20261015-072036-RUSzpe`) read the branch at `ce0d39216`, on top of base `b9fcaf121` (mvp-0.25). It found two Medium defects. It also found that the original Marker/Reader pdfium race is fixed. The stage's own write-up is [marker-pdfium-worker.md](marker-pdfium-worker.md).

**No paid calls and no network requests.** The tests use the on-disk fake `marker` package. No vault was opened.

## Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Cancellation and parent death leave descendant workers running | **fixed** | `5aa3282f0` | `test_every_process_the_marker_worker_started_ends_with_its_reading[timeout,cancel,crash,error,answer]` and `test_a_marker_worker_and_its_pool_stop_when_the_process_that_started_it_dies` (`tests/test_marker_pdfium_worker.py`) |
| F2 | Medium | Parent death leaves plaintext API credentials in temporary storage | **fixed** | `5aa3282f0` | `test_a_marker_readings_api_key_never_reaches_the_disk_even_when_its_parent_dies` |

No finding was rejected. No finding was High.

### F1: every process a reading started ends with it

**Reproduced first.** The fake `marker` (`tests/marker_fakes.py`) now behaves as pdftext does when `pdftext_workers` is above 1: it starts a `ProcessPoolExecutor` of forked processes, and each one records its pid. Outside the `ok` and `chatty` modes the pool processes sleep, so whatever ends the reading finds them alive. On `ce0d39216` the new tests failed as follows:

- **4 of the 5 endings.** Timeout, cancel, crash and Marker's own error each left both pool pids running, for example `the worker's pool outlived its reading: [3546494, 3546495]`. The fifth ending, a normal answer, passed: the pool shut itself down.
- **Parent death.** Killing the parent with SIGKILL stopped the worker but left both pool processes running.

The "error" ending is one the review did not name: Marker raises while its pool is running. The worker writes `{"error": …}` and leaves with `os._exit(0)`, which skips any pool shutdown. Real pdftext wraps its pool in a `with` block, so this needs an error raised while the pool runs, but the fake shows that nothing outside the worker ever stopped those processes.

**Fix** (`src/learnloop/ingest/extractors/marker_worker.py`):

- **POSIX.** `run_marker` starts the worker with `start_new_session=True`, so the worker leads a session and process group of its own.
  - `_stop` runs in the `finally` around the wait on every path (answered, crashed, timed out, cancelled, or a `KeyboardInterrupt`). It sends `SIGKILL` to the whole group, then reaps the worker.
  - While the worker runs, `_exited` polls with `os.waitid(P_PID, pid, WEXITED | WNOHANG | WNOWAIT)`. An exited worker therefore stays unreaped until its group has been killed, and its pid, which is also the group id, cannot be reused in between. Where `os.waitid` is missing (macOS), it falls back to `Popen.wait`.
  - A worker that answered keeps its exit status of 0. `test_a_worker_that_answered_exits_at_once_and_cleanly` still passes.
- **Parent death.** The orphaned worker's stdin watcher calls `_orphaned`, which runs `killpg(getpgrp(), SIGKILL)` and so kills the worker and everything it started. It does this only when `getpgrp() == getpid()`, that is, when the worker leads the group. A worker that merely joined a group never signals it.
- **Windows.** The worker puts itself in a job object with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`. The worker's handle to the job is never inherited and never closed, so when the worker exits, crashes or is killed, the job closes and kills everything in it. A failure to set up the job is written to the worker's log, and the reading goes on.
  - **Not run on Windows here.** Only the ctypes layout is tested (`test_the_windows_job_limit_structure_has_its_documented_layout`: 144 bytes, `IoInfo` at offset 64, `LimitFlags` at offset 16). Windows checks only the structure's size, so a wrong field would silently move the flag.

**Tests.** `_alive` now counts a zombie as gone, by reading `/proc/<pid>/stat`. A killed pool process waits as a zombie until whoever inherited it reaps it. The new tests kill every pid they recorded in a `finally`, so a failing run never leaves processes asleep for ten minutes. The timeout and cancel endings wait until both pool processes are up before the time runs out or the cancel fires, so nothing depends on timing.

### F2: the request travels on stdin, and an orphan cleans up its own files

**Reproduced first.** A parent process ran `run_marker` with `use_llm` and a synthetic `openai_api_key`. On `ce0d39216`, while the reading was under way, `learnloop-marker-*/request.json` held the key. A parent killed at that point never runs its `TemporaryDirectory` cleanup, so the key stays on disk.

**Fix.**

- **The request goes through stdin.** It travels as one JSON line on the worker's stdin, a pipe only the parent holds, and never as a file or a command-line argument. That covers both paths: the legacy path's options and any `marker_options` the durable extractor forwards.
  - The worker reads the line straight from the descriptor, before it starts its parent watcher or Marker.
  - A thread in the parent writes the request, so a worker that never reads cannot block the caller past its time limit or a cancel.
  - Stdin stays open after the request, because its EOF is still the signal that the parent is gone. A parent that dies before the request is sent counts as an orphaned worker.
- **An orphaned worker cleans up.** Its dead parent can no longer clean the private directory, so the worker removes its own files there (`source.pdf`, `answer.json`, `answer.json.partial`, `worker.log`), and then the directory if that empties it.
  - It removes nothing else, and it never deletes recursively, so a deletion that cannot be sure stops short.
  - The parent-death test asserts that the directory is gone.

**Test.** `test_a_marker_readings_api_key_never_reaches_the_disk_even_when_its_parent_dies` checks two moments:

- **Mid-reading.** The worker has the key, because the fake records its config. No file under the parent's `TMPDIR` holds it.
- **After the parent is killed with SIGKILL and the worker is gone.** Still no file holds it.

`test_marker_llm_options_map_to_openai_service` still shows the key reaching Marker's config in the worker.

## Claims the review said do not hold

- **"A cancelled import now kills Marker mid-reading" and "parent death stops its work".** These now hold for every process the reading started, not only the worker.
- **"Lifecycle tests establish that nothing is left running".** These now cover a worker with a pool of child processes, under all five endings and parent death.

[marker-pdfium-worker.md](marker-pdfium-worker.md) is corrected in three places:

- the request no longer goes in the private directory;
- an orphaned worker cleans up and kills its group, instead of exiting with status 70;
- a new bullet covers the processes the worker starts.

## Out of scope

- **Real Marker.** The fixes were not exercised with real Marker and `pdftext_workers = 2`. The real pdftext pool exists only for the moment the text layer is read, and only when there are at least `WORKER_PAGE_THRESHOLD` pages per worker. That makes it a poor target for a cancel probe. The fake's pool has the same shape as pdftext's: a `ProcessPoolExecutor` with the `fork` context, started from the worker.
- **Other workers.** The GLM-OCR text-layer worker is short-lived and carries no credential, and it is unchanged. The exam-protection identity stage's files were not touched.

## Gate

The code was gated at `5aa3282f0`; the commit after it adds this file only. `TMPDIR` was the worktree's `fixtures-local/tmp`. `uv run --no-sync` keeps the pypdfium2 that `uv pip install` added, because a plain `uv run` would sync it away.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | done (pypdfium2 5.14.0) |
| `uv run --no-sync lint-imports --no-cache` | **17 kept, 0 broken** |
| `tests/test_marker_pdfium_worker.py` after the fix | **16 passed**, 5 runs out of 5 (about 8.6 s a run) |
| The same file on `ce0d39216`, with the new tests | timeout, cancel, crash and error endings failed (both pool pids alive); parent death failed (pool alive); F2 failed (`request.json` held the key); the `answer` ending passed |
| Ingest and Reader files with `-n 8` (`test_marker_pdfium_worker`, `test_glm_ocr`, `test_pdf_extraction`, `test_pdf_extractor_selection`, `test_source_layer`, `test_span_view`, `test_sidecar_span_view`, `test_sidecar_reader_pdf_view`, `test_reader_render_views`, `test_sqlite_file_copies`) | **180 passed** |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | **11,539 passed**, 0 failed, 0 skipped (1,328.1 s, machine shared with other stages). That is the earlier gate's 11,532 plus 7 net new tests. |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | **100 passed**, 11,439 deselected (116.4 s) |
| After the runs | no `marker_worker` process left running, and no `learnloop-marker-*` directory left under `fixtures-local/tmp` |
| Frontend, `src-tauri`, schema, DB references | unchanged: no npm, cargo, migration or reference steps. No architecture note cites `marker_worker.py` lines. |

The 48 warnings in the full suite come from tests outside this stage, for example `fork()` in a multi-threaded xdist worker in `test_migration_coordinator` and `test_vault_lock`.

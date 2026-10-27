# Test-suite thread leak

**Stage:** `test-thread-leak`, branch `fix/test-thread-leak` (worktree `learnanything-tleak`), base `497169069` (main: rebuild-equivalence mvp-0.34, mobile PR-2, migrations through 222).
**Owner request (2026-10-26):** "please fix the thread leak". Symptom: in the landing full suite (`-n 8`) one xdist worker collected ~800 leaked threads that burned ~17 cores (load average 400+ on 32 cores); one full suite stalled for 4 h; `tests/test_reader_rw1c_review.py` leaked ~5 threads per test.
**No migration, no successor, no config key.** No paid or live calls (fakes only).

## 1. Finding every source

### 1.1 The diagnostic

`tests/thread_guard.py` (a pytest plugin, `pytest_plugins` in `tests/conftest.py`) wraps `threading.Thread.start` for the whole test process. Each start records which test, which phase (setup/call/teardown) and which wider-scoped fixture (if any) started the thread, plus its creation stack (40 frames, lines looked up only when reported). A thread started by a tracked thread inherits that thread's owner, so a leaked worker that spawns more is never charged to a later test. After each test's teardown, every thread the test owned that is still alive gets a bounded join; module/class/package/session-fixture threads are checked when that fixture finalizes.

`LEARNLOOP_THREAD_LEAK_REPORT=<file>` turns it into a survey: one JSON line per leaking test (thread name, native id, target, creation site and stack, CPU seconds at the leak, live thread count) instead of a failure, and at session end the CPU each leaked thread had used by then (what kept burning after its test). `LEARNLOOP_THREAD_LEAK_GRACE` shortens the join grace for a survey.

### 1.2 Survey 1: the baseline (base `497169069` + the diagnostic only)

Whole suite (1,052 test files) in four alphabetical shards, each `flock /tmp/learnloop-fullsuite.lock systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G -- python -m pytest -n 6`, report mode, 0.5 s grace, on a `git archive` snapshot of the commit under the worktree's ignored `.pytest_tmp_survey/` (so editing could go on during the run).

| Shard | Wall | Leaking tests | Leaked threads |
|---|---|---|---|
| 00 (`test_action_loss` … `test_e2e_tui`) | 980 s | 246 | 323 |
| 01 | 744 s | 471 | 613 (77 errors: one worker's guard crashed on the sampler of 2.3 and every later test there errored; covered again in survey 2) |
| 02 (the `test_reader_*` files) | **2,929 s** | 659 | 2,062 |
| 03 | 498 s | 657 | 1,106 |

Leaks by creation site, all shards:

| Threads | Thread | Created at | Test files |
|---|---|---|---|
| 3,037 | `learnloop-reading-sweep` | `content/pipeline/jobs.py` `_ensure_reading_sweep` (a `SidecarContext.load` → `DurableIngestJobs.bind`) | 270 |
| 318 ×3 | `learnloop-post-attempt-{diagnose,embed,gaps}` | `learnloop_sidecar/post_attempt_worker.py` `notify` | 38 |
| 57 | `learnloop-quick-check-N` | `jobs.py` `_ensure_worker` | 10 |
| 28 | `source-service-spend-leases` | `source_retrieval/service_spend.py` `_Leases.hold` (process singleton) | 27 |
| 21 | `learnloop-ingest-drain` | `jobs.py` `_ensure_worker` | 11 |
| 3 | `ingest-heartbeat-<job>` | `content/pipeline/runner.py` `_run_claimed` | 2 |
| 2 | `process_request_thread` | the ChatGPT-plan fake server's stalled reply (`tests/chatgpt_plan_fakes.py`) | 2 |
| 1 | `learnloop-codex-interrupt` | `ai/providers/codex.py` `_schedule_turn_stop` (a fake whose interrupt never answers, 2 s) | 1 |
| 1 | `Thread` | `local_embeddings/worker.py` `run_job` (the GPU sampler) | 1 |

No leaked thread was non-daemon.

**What burned the CPU.** At session end, the leaked threads that had kept using CPU after their test were all sidecar background owners of Reader tests, and almost all of them came from one file:

| CPU seconds after the leak | Thread | From |
|---|---|---|
| 33,532 | reading sweep (~100 threads) | `test_reader_rw1c_review.py` |
| 3,821 / 1,921 / 1,854 / 959 / 957 | reading sweep | `test_reader_reconnect.py`, `_inquiry_kill_switch.py`, `_branches.py`, `_inquiry_status.py`, `_reconstruct.py` |
| 2,382 + 1,242 + 1,242 | post-attempt slots | `test_reader_rw1c_review.py` |

The same picture was visible live in the CA1 landing's full suite (read from `/proc` only): one worker at 711 % CPU, 200 threads, 139 of them runnable at ~0.24 cores each with ~316 s of CPU apiece. Shard 02 of the survey took 2,929 s against 500–1,000 s for the others, while one of its workers held 37–77 runnable threads using 20–26 cores.

**Why idle pollers burned cores.** Alone, a sweep pass on the Reader library vault costs 16 ms of CPU and then waits 30 s (measured: `sweep_reading_requests` 3 ms, `resume_book_preparation` 6 ms, `resume_contextual_index` 6 ms, `refresh_fusion_posteriors` ~0; a post-attempt pass 3–16 ms). No loop busy-spins by itself. The cost comes from the count: with hundreds of leaked threads in one interpreter, every wake competes for the GIL, and CPython's GIL hand-off (each waiter wakes every 5 ms switch interval to ask for the lock) turns hundreds of runnable threads into a futex convoy that burns kernel and user time without progress. The passes then take seconds instead of milliseconds, so more threads are runnable at once, and the convoy feeds itself. That is the ~0.24 cores per thread seen in both runs. The fix is to stop leaking the threads, not to tune their pace.

## 2. Root causes and fixes

### 2.1 Production: a sidecar context had no way to stop everything it starts

`SidecarContext` owns the ingest host (drain, quick checks, reading sweep), the exam graders, the post-attempt worker (three slots) and the approach-map builds. The `shutdown` RPC stopped three of them and EOF only drained the map builds; the post-attempt worker was never stopped.

* New `SidecarContext.close()` stops all four, each with a bounded join, idempotent (a later `load` or submit restarts them, as after `shutdown`).
* `handlers/app.py` `shutdown` and `server.serve`'s `finally` (EOF) both call it.
* `PostAttemptWorker.shutdown(timeout)` now joins its three slots within one deadline (it was 2 s per slot), so shutdown stays bounded when a slot is inside a model call. The job in flight is released before its next paid request (unchanged).

### 2.2 Production: the spend-lease heartbeat outlived its last lease

`source_service`'s process-wide `_Leases` heartbeat only noticed it had nothing to renew after a full 60 s beat. `drop` now sets an `_idle` event when the last lease goes, and the thread ends at once; `hold` clears it. (Leases still renew every `HEARTBEAT_SECONDS` while any is held; the reservation semantics are unchanged.)

### 2.3 Production: two sampler threads shadowed `Thread._stop`

`local_embeddings/worker.py` and `experiments/contextual_embeddings/e1/worker.py` each define `Sampler(threading.Thread)` with `self._stop = threading.Event()`. `_stop` is `Thread`'s own private method: once such a thread ends, `is_alive()` and `join()` raise `TypeError: 'Event' object is not callable`. Renamed to `_stop_requested`. (Survey 1 found it because the guard's `is_alive()` crashed on it; the guard now tolerates a broken `is_alive` too.)

### 2.4 Tests: close what the test constructs

Most leaks were tests that build a `SidecarContext` (211 construction sites in 130 files, mostly through helpers such as `recap_fixtures.context`) and return without closing it. Rather than edit every site, `tests/background_owners.py` wraps the constructors of `SidecarContext`, `DurableIngestJobs`, `PostAttemptWorker` and `ExamGradingManager`; an instance constructed **directly by code under `tests/`** is recorded (by weak reference, so a test that drops its host to check that the host's threads end on their own still can; a context's thread-owning parts are held strongly, so a context a test drops, say by rebinding a fresh one, still has its threads stopped), and the autouse `close_test_background_owners` fixture closes them, newest first, when the test ends. Instances built by production code (a context's own ingest host; any host that builds contexts) are not recorded: they are their owner's to stop, so a production owner without a stop path still fails the guard.

Individual fixes where the generic one did not apply:

* `tests/test_daily_plan_reentry.py`: one test replaced its context in a loop (the dropped one was never closed); it now closes each round's context.
* `tests/test_source_service_spend_accounting.py::test_concurrent_admission_counts_the_unreconciled_receipt` admitted four reservations and never settled them, so the process heartbeat renewed them for the rest of the run; it now settles them after its assertions.
* `tests/chatgpt_plan_fakes.py`: a stalled reply slept `stall` seconds (5 s) in the fake server's handler thread; it now waits on a `_closing` event that `close()` sets.

The test semantics are unchanged: no test was skipped, xfailed or loosened; only teardown was added.

### 2.5 The idle desktop sidecar

`tests/test_sidecar_idle_threads.py` (new) pins the production half:

* a loaded sidecar with its post-attempt slots started has exactly the four background threads (`reading-sweep`, `post-attempt-{diagnose,embed,gaps}`) and over a 1 s quiet window they use < 0.05 s CPU (read per thread from `/proc/self/task/<tid>/stat`);
* `close()` stops all of them within 5 s; the `shutdown` RPC does too; EOF on the sidecar's stdin closes its context;
* the lease heartbeat ends within 5 s of its last lease being dropped (its beat is 60 s), and keeps beating while one is held.

## 3. The permanent guard

`tests/thread_guard.py` stays on for every run. A test (or wider-scoped fixture) that leaves a thread alive after a **2 s** join grace (`JOIN_GRACE_SECONDS`, a guardrail: long enough for a worker told to stop to see its event, short enough that a real leak costs little) fails in teardown with each thread's name, daemon flag, target, CPU seconds, the phase it started in, its creation site and the last 12 frames of its creation stack. Daemon threads are not exempt: a daemon that keeps running still burns the worker. Non-daemon threads fail the same way (none were found; a non-daemon leak would also block the xdist worker's exit).

`ALLOWED` is the reviewed allowlist of process-lifetime singletons (a creation-site substring and the reason). It is **empty**: the one process singleton found (the spend-lease heartbeat) now ends with its last lease.

## 4. Surveys after the fix and the gate

(filled in below)

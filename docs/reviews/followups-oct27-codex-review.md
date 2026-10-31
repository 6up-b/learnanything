# Follow-ups Oct 27: Codex review fixes

Branch `fix/followups-oct27`. Review job `20261027-175727-xzTbJZ` (gpt-6.1-sol) on `74b575c82`. Two Medium findings,
both test-harness defects; both fixed. Only tests and review records changed: no production code, migration, config
key, algorithm version or frontend. **Spend: $0. No paid or model calls.** Owner copies came only from
`fixtures-local/owner-copies-mvp035`, as fresh backup-API copies (`fixtures-local/fu27/lane6`, `lane7`).

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | Medium | The hang guard can block indefinitely during cleanup | fixed | `32dd051d4` | `test_the_hang_guard_cancels_a_blocked_job_and_leaves_no_worker`, `test_the_hang_guard_fails_bounded_when_a_job_ignores_cancellation` (`tests/test_plan_first_transport_offer_grants.py`) |
| F2 | Medium | The new snapshot misses writes from disabled Today reads | fixed | `e9c2c9c8e` | `test_daily_plan_kill_switch::test_plan_off_is_dl0_on_fixture_copies` (owner lane); mutation check below |

The two "claims that don't hold" are corrected in `followups-oct27.md` (§1 hang guard, §2 kill-switch check).

### F1: reproduction and fix

**Reproduced.** Two new tests set the hang guard to 0.2 s and enqueue one blocking job. On the old harness both
failed, and each drain sat in the unbounded `thread.join()` for the job's full 60 s safety bound (2 failed in 181 s):

- a job that blocks until it is cancelled was never cancelled, because `stop.set()` reaches only the loop between
  chunks;
- a job that ignores cancellation kept `drain()` from returning until the job ended by itself.

**Fix** (`Harness.drain`, test only):

- a drain that ends on its own is unchanged: it asserts that nothing is pending;
- past the hang guard the worker is told to stop after its chunk, and every batch with a pending job is cancelled
  through `IngestRunner.cancel_batch`. That is the sidecar's Cancel path: queued jobs go straight to `cancelled`, and
  a running handler sees the flag at its next checkpoint (`report()` / `cancelled()`). The worker then gets a
  bounded grace (`_DRAIN_STOP_GRACE_S = 60`, labelled `keep`: a cleanup bound, not a model parameter);
- a worker still alive after the grace fails the drain, naming its stack. No join is unbounded, and the worker
  thread is a daemon.

**After the fix:**

- the cooperative block is cancelled, its job ends `cancelled`, no worker survives, and the drain fails with "did
  not finish";
- for the uncooperative block, the drain returns while the worker is still blocked. The failure names
  `ignores_cancellation` in the worker's stack. The test then releases the job and joins the worker, so the thread
  guard stays clean.
- Both pass in 4.5 s.

**Why not a terminable process.** The harness tests process state: `plan_fallback`'s grants live in the test
process and are read by `_probe` on the worker. The handlers, the `fake_openai` and the RPC stubs are installed by
monkeypatching. A spawned process sees none of these, and forking a process that has threads running is unsafe. A
thread cannot be killed. So the bound is cancellation (which every runner handler honours at its checkpoints) plus a
bounded failure. A job blocked outside any checkpoint is reported, with its stack, and is not waited on. Every
blocking point in the runner itself has a timeout (`vault_mutation_lock(timeout_s=...)`, SQLite `busy_timeout`), so
in this harness the only unbounded block would be a handler. `_probe` does not block.

### F2: reproduction and fix

**Reproduced** with a temporary mutation test (not committed; deleted after the run). It wrapped `get_today_queue`
so that every call on the disabled vault inserted a `daily_plans` row, then ran
`test_plan_off_is_dl0_on_fixture_copies`. On the old test the mutant **passed on all three owner copies** (6 passed,
3 mutants + 3 real). Both disabled-read calls fell outside the snapshot: the first read came before it, and the last
read came after the final comparison.

**Fix.** The snapshot is taken before the first `_today_reads(off)`. It is compared after that read, after the plan
RPCs, and after the final read. On the same copies **the mutant failed on all three**
(`([('mutant_0', ...)], []) == ([], [])` on linear_algebra and arxiv_v2, and a changed row list on probability). The
real test passed on all three. Existing owner plans are still accommodated: no row may be added or changed.

## Gate

- `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken.**
- Targeted pytest (`-n 6`, 5G scope, under `flock /tmp/learnloop-fullsuite.lock`):
  - test files: `test_plan_first_transport_offer_grants.py`, `test_plan_first_transport_offer_grants_r5.py`,
    `test_daily_plan_kill_switch.py`, `test_field_workbench_signals.py` (imports the kill-switch helpers),
    `test_sidecar_idle_threads.py`;
  - contract tests: `test_sqlite_file_copies.py`, `test_public_tip_guards.py`, `test_tracked_fixture_databases.py`;
  - result: **78 passed, 6 skipped.**
- New hang-guard tests alone: before the fix **2 failed** (181 s); after it **2 passed** (4.5 s).
- Owner lane (`-m owner_vaults`, fresh copies `fu27/lane7`, `-n 6`), `test_daily_plan_kill_switch.py` and
  `test_field_workbench_signals.py`: **6 passed.**
- F2 mutation check (fresh copies `fu27/lane6`, `-n 3`): before the fix 6 passed (mutant missed); after it
  **3 failed (the mutants), 3 passed (the real test)**.
- No migration, DB/connection, frontend or src-tauri change, so there was no durability, vitest, cargo or DB-reference
  run. Per the owner's rule the full suite was not run here; it runs in the landing gate.

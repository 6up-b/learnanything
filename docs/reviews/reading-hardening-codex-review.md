# reading-hardening: Codex review and fixes

**Branch:** `ux/reading-hardening` (worktree `learnanything-ux-impl`, base main `c50dd0bcb`, not rebased; the orchestrator merges). **Review:** Codex, `~/.cache/codex-agent/jobs/20261013-183451-akyp7h`, reviewed through `a4629f7fa`. **Stage record:** [reading-hardening.md](reading-hardening.md).

Codex returned two findings, both Medium, and three claims that did not hold. Two of the claims are the findings themselves. Both findings reproduced and are fixed. The third claim is a wrong sentence in the stage record, now corrected; no code changed for it.

## Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Cancel can silently restart the work it cancelled | **fixed** | `5a7880e8f` | `tests/test_reading_hardening_review_fixes.py`: `test_f1_a_cancel_whose_settle_fails_cancels_nothing_and_says_so[settle_reading_request]`, `[pending_reading_request]`, `test_f1_a_crash_between_the_cancel_and_its_settle_leaves_neither_after_a_restart`, `test_f1_the_cli_cancel_commits_with_its_settle_too`, `test_f1_kill_codex_interrupts_nothing_when_its_settle_fails` |
| F2 | Medium | The sweep's own wake signal bypasses failure backoff | **fixed** | `6d892e9de` | same file: `test_f2_planning_and_its_record_both_failing_back_off_through_the_sweeps_own_loop`, `test_f2_on_the_real_threads_a_failing_unrecordable_act_does_not_spin`; guard `test_f2_a_wake_from_outside_the_sweep_still_brings_its_pass_forward` |
| C3 | (claim) | "The CLI acts on no reading request" and never starts a paid follow-on build | **corrected in the record** (no code change) | `ebb1743b4` | Codex is right, and calls it pre-existing, not a regression. A build the CLI drains runs `after_auto_build` (unchanged by this stage) in the CLI process. That step queues the follow-on planner, and the same `drain()` can run it. Changing that is outside the stage's four items: Q-RH6 |

**Fail-first.** Run against `a4629f7fa` before either fix, 7 of the 8 new tests failed. The guard passed.

| Test | Failed with |
|---|---|
| F1 settle fails (both parametrizations) | `DID NOT RAISE`: the cancel reported success |
| F1 crash, then restart | "the cancel survived the crash, its settle did not" (planner `cancelled` and request still due) |
| F1 CLI | `'cancelled' == 'queued'`: the CLI exited non-zero with the cancel already committed |
| F1 kill-codex | `DID NOT RAISE`: the call was interrupted and the request left due |
| F2 through the sweep's loop | a wait already set at entry (`[False, False, True, …]`) |
| F2 on the real threads | "27 failing passes in 1.20 s: the sweep woke itself" (the bound is 8) |

Codex's F1 scenario was reproduced exactly with the production RPC before the fix. The settle fails once, `cancel_ingest_batch` returns `cancelled`, u4 stays due, and the next sweep queued a planner for `['u4', 'u5']` (Ch. 3–4). The cancelled planner had asked for `['u4']`.

## F1: the cancel and its settle are one transaction

**What was wrong.** `_cancel_batch` committed the cancel, then settled the book's reading request in a separate best-effort step that logged and swallowed any error. If reading or settling the request failed, or the process died between the two commits, the cancel stood and the request stayed due. A planner cancelled before it ran has no child build, so its chapters were still unplanned, and the sweep's next pass planned them again behind the learner's back.

**The fix.**
- **One transaction.** `IngestRunner.cancel_batch(batch_id, *, alongside=None)` is now one `Repository.atomic()` transaction. It holds the batch's cancel flag, every unleased job's move to `cancelled`, and the `alongside` write, which commits with the cancel or not at all.
- **Every cancel path passes the settle there** (`settle_reading_for_cancelled_batch`): the sidecar's `cancel_ingest_batch`, the legacy `cancel`, `kill-codex` (`interrupt_job(…, alongside=…)`) and the CLI's `ingest-batches cancel`. The best-effort `_settle_reading_for_cancel` is gone.
- **A failed settle cancels nothing.** If reading or settling the request fails, the whole cancel rolls back and the error reaches the caller: the RPC returns an error, and the CLI exits non-zero. The learner's next cancel commits both. A crash before the commit leaves neither.
- **Kill-codex interrupts last.** The live call is stopped only after the cancel and the settle committed, so a failed cancel leaves the call running.
- **The batch's status refresh stays outside the transaction.** A finished batch's `wal_checkpoint(TRUNCATE)` must not wait on the cancel's own write lock.
- **Unchanged:** the sidecar still holds the reading lock around the cancel, so no act in that process interleaves. The settle is still revision-conditional: a request recorded after the cancel's read survives (`test_c_a_request_recorded_after_the_cancel_survives_it` passes unchanged).

**What remains (documented in the stage record).** The CLI's cancel does not hold the sidecar's in-process lock. A sidecar act that read the request just before the CLI's commit, and checks the book's work just after it, could still plan once. Closing that needs the act's enqueue and settle in one revision-checked transaction. That is wider than this finding.

**Durability.** The F1 tests also pass under `--durable-sqlite` (WAL, `synchronous=FULL`): 5 passed, counting both parametrizations.

## F2: the sweep never wakes itself

**What was wrong.** Suppose an act fails inside the sweep's pass and recording its retry time fails too. `_note_reading_failure` still called `wake_reading_retries()`, which set the sweep's own event. The pass returned its backoff (1, 2, 4, 8, 16, 30 s), but the next `Event.wait()` returned at once, because the event was already set. The request was still due, so the cycle repeated: a tight loop of failing acts and warnings.

**The fix.** `_reading_sweep_pass` marks its thread (a thread-local, `_in_sweep_pass`) for the duration of `sweep_reading_requests()`. `wake_reading_retries()` is a no-op while the mark is set, so the pass's outcome alone sets the next wait.

A wake from anywhere else still brings the pass forward: the Reader's RPC, the start's reconciliation, and the worker after a round. The guard test checks that a wake from another thread is acted on at once while the pace is 30 s. The mark is per thread, so it also holds when the loop runs on the caller's thread (`_reading_sweep_loop`). With the sweep's own thread identity, it would not.

**Tests through the real loop.**
- `_run_reading_sweep`, `_reading_sweep_pass`, the act and `_note_reading_failure` run unchanged. Planning raises and `fail_reading_request` raises. Only the event is replaced, by one that records each wait instead of blocking.
- The waits are 30, 1, 2, 4, 8, 16, 30, 30 s, none of them already set. Every one of the 7 passes acted and could not record the failure, and the request is never given up.
- On the real sweep thread and event (pace 0.5 s, retry 0.1 s), the same double failure makes at most 8 passes in 1.2 s; before the fix it made 27. A loaded machine only makes passes rarer, so this bound cannot fail on load.

## Scope and invariants

- **Migration:** none. **Schema:** unchanged (head 199). **Config:** unchanged. **Algorithm version:** unchanged. Replay reads none of this.
- **Frontend:** nothing under `apps/` changed. A cancel that fails now returns an RPC error, which the existing error path shows. **Rust:** nothing under `src-tauri` changed.
- **References** were regenerated (`d06a4023b`). Only the source-commit stamps and one table's test list (the new test file) moved.
- **Paid calls:** none ($0.00). Every model call in the tests is a house fake. No provider, network or key was used.

## Gate

Run in this worktree with `TMPDIR=<worktree>/fixtures-local/tmp`, at `d06a4023b` (code identical to `6d892e9de`).

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` · `uv pip install pypdfium2` | ok: 163 packages resolved; the sync removes pypdfium2 and the install puts back 5.14.0 |
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10,148 passed**, 0 failed, 47 warnings (8 min 31 s). That is the stage's 10,140 plus the 8 new tests |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 10,049 deselected, 0 failed (2 min 0 s) |
| Frontend (`npm install`, `typecheck`, `test`, `frontend:build`) | not run: nothing under `apps/` changed since the stage's clean frontend gate at `f42f3e223` |
| `cargo check` | not needed: nothing under `src-tauri` changed |
| References | `db_generate_reference.py`: schema head 199, 318 table notes, unchanged. `db_validate_reference.py`: errors `[]`. `validate_vault.py`: passed, 1098 notes |

One of the full suite's warnings is a `PytestUnhandledThreadExceptionWarning` from a `learnloop-reading-sweep` thread. An earlier test's host in the same xdist worker was still referenced, and its sweep woke during `test_success_head.py::test_deterministic_rebuild_and_no_store_or_network`. That test replaces `sqlite3.connect` with `pytest.fail`, which raises a `BaseException` the pass does not catch. The test itself passed. This is test-process hygiene, not something either fix touches, and production raises no such exception.

Targeted runs before the gate: the 8 new tests and the stage's 14 sweep tests passed together (22). The ingest, UX Phase 1, passage-check and ownership suites gave 198 passed.

## Safety

- No paid call, no real provider, no network. No key, credential, `.env` or `settings.env` file was read.
- The owner's working vaults were not opened, and no fixture vault was opened or copied in this round. No manual run was needed: every scenario runs on a fresh test library.
- No tailscale command was run. Nothing was merged, pushed or rebased. A temporary `git stash` used to test the F1 commit on its own was dropped after use.

## Open questions for the owner (recommended defaults applied)

- **Q-RH6.** A build the CLI drains still runs its completion step, which can queue the next keep-ahead planner and run it in the same `drain()` (C3; pre-existing). Should CLI drains leave reading requests to the sidecar instead? Recommended: **keep as is**. The follow-on build passes the same admission as the sidecar's (the daily cap and the ask-first threshold), and the CLI is a developer tool. The stage record now says so plainly.
- **Q-RH7.** A cancel whose settle fails now fails as a whole and reports the error (F1), rather than succeeding and leaving the request due. Recommended: **keep**. An honest failed cancel, which the learner can repeat, beats a cancel that quietly re-plans what it stopped.

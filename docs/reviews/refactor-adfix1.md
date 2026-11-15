# Arc D close fixes, group 1: D-33, SJ-10, D-30, R1-1

Branch `fix/arc-d-close-1`, based on main `7bdec7edb5`. One commit per row, plus one for a third flake found in D-33's file (D-45). Repeats and timing experiments used scratch pytest plugins that are not tracked: one repeats a test N times as fresh items with the same node id (so the pinned draws are the same in every repeat), one starts each test a given number of seconds before local midnight (it moves `SystemClock.now` for the process), one dumps the busy traceback and every thread's stack when the sidecar maps an error to `database_busy`. "Under load" means beside 28 busy-loop processes on the 32-core machine while other steps' landing gates ran (load average 37 to 47).

| Row | Commit | Kind |
|---|---|---|
| D-33 | `c96a4839d1` | the test's loop |
| SJ-10 | `d975ae9d40` | the test's clock (local midnight) |
| D-45 (new) | `66dec2fccd` | the test's wait (a thread it starts) |
| D-30 | `40209ab534` | product: lock order in two repository writes |
| R1-1 | `e671b6f05e` | product: the bound runners at a refusal |

Nothing here changes what a vault stores or what the router serves. D-30 changes when a write takes its lock; R1-1 changes what runs while a vault is refused.

## D-33: `test_the_matrix[plan-complete-before-preparing]`

**Reproduced.** With the cell's pin to `FOLLOWUP_SERVE_ALGORITHM_VERSION` removed it failed at the head every run (`assert 'open' in {'complete', 'stopped'}`). A print of each step `_finish_the_plan` read showed three items skipped and then `{'kind': 'lesson_offer', ...}` with the plan still `open`.

**Cause.** `tests/test_followup_next_matrix.py:148-156` (at the base): the loop stops at the first step that is not an item. At the head the plan's objective draws lesson offers (`daily_plan/lesson_offer.py`, `offers_on`), and this cell's pinned draws put one at its fourth boundary; the plan's next step waits behind an unanswered offer, so the plan never closes. At mvp-0.45 there were no offers, which is why the old tag passed. The other complete-before cells' draws put no offer before the plan's end. This is the screen's step the loop did not answer, not a missed completion: on the desktop the offer page's "Not now" (`answerPlanOffer` in `App.tsx`) answers it and fetches the next step.

**Fix.** The loop answers an offer as "Not now" does (`lesson.suggestion_respond` with `declined`) and goes on; the pin and the unused `version` parameter are gone, so all 66 cells run at the head.

**Not verified.** The desktop itself (no GUI run). Whether an offer drawn at the plan's last boundary and never answered should ever let the plan complete is a product question the row does not raise; the plan waits for the learner's answer by design.

## SJ-10: `test_the_matrix[plan-stopped-after-waiting]`

**Runs.** The cell alone 30 times at `-n 6`, then 30 times at `-n 6` under load: 60 of 60 passed. The whole file at `-n 6` under load, four times: the cell passed each time.

**Reproduced.** The failing assertion means the plan read after `plan_keep_going(stop=True)` is open. `stop_today` closes `latest_today(env)` (`daily_plan/engine.py:6721`), and the plan's day is the machine's local date (`engine.py:602`). Starting the cell 9 or 12 s before local midnight (the cell takes about 12 s under load) failed it every time with exactly SJ-10's assertion: "Done" after midnight finds no plan for the new day, and the next `get_daily_plan` builds an open one. At a 6 s lead the shift happened before the plan was built and the cell passed. The SJ gate that saw the failure ran in the hours after midnight (its record was committed at 02:02 local); the exact minute the file ran is not recorded, so midnight is the reproduced cause, not a proven one for that run. No unpinned draw or background job was found on the cell's path; the cell's draws are pinned by node id.

**Fix.** `_movable_clock` starts the cell's clock one minute after midnight when the real time is within 30 minutes of it (forward, as the cells that add a day already move it), so the day changes under a cell only when the cell moves it. `_close`'s assertion now names the plan's id and day beside today's date. With the fix, the cell started 6, 9, 12 and 20 s before midnight passed, and the whole file started 10 minutes before midnight passed under load.

**Not verified.** Other tests on the real clock may cross midnight the same way; they were not surveyed.

## D-45 (new): the matrix's teardown under load

Running the whole matrix under load for D-33 and SJ-10 failed 4 to 7 cells per run at teardown: `tests/thread_guard.py` found `learnloop-objective-carried` still running after its 2 s grace. The thread is the no-model runtime's carried valuation, started after each plan decision (`daily_plan/objective_chooser.py:1495`, `_defer_carry`). Main's version of the file failed the same way under the same load (4 of 71), so it predates this work; answering the lesson offer in D-33's loop does not add it. Fix: `_desk` uses `join_carried_valuations` (`tests/router_mixture_helpers.py`), so each serve joins the thread it started; no cell reads that valuation. After: 71 of 71 under load, twice.

## D-30: `test_reading_usable_with_synthesis_worker_down`

**Which call and which lane.** The two landing-gate failures (the `fre` and `d5` gates' JUnit files) are `KeyError: 'result'` at `out[2]["result"]`: `out[2]` is the reply with id 2, `reader.invoke_preset`, not the drain (id 3) that the ledger and the test's comment named. Both were in the ordinary lane (the landing run, no `--durable-sqlite`; the test has no durability marker), and the test took 0.2 s, so the error came at once, not after `busy_timeout`.

**Reproduced.** 200 repeats at `-n 6` under load: 12 failed, then 18 of 200. Every failure: `{'code': 'database_busy', 'retryable': True}`, "The vault database is busy with another write. Try again in a moment." The stack dumps (18 of 18) show the request thread failing in `commitment_arcs.create_arc` at `repositories.py` `append_commitment_arc_event` (10) or `append_commitment_arc_version` (8), with the sidecar's ingest drain thread inside `claim_next_ingest_job` or opening its connection to claim.

**Cause.** `db/repositories.py:14437` and `:14481` (at the base) begin with a deferred `BEGIN`, read the arc's last ordinal, then insert. The read holds a shared lock; when another connection has committed (WAL) or holds the reserved lock and is committing (rollback journal) in between, SQLite refuses the upgrade at once with "database is locked" and does not call the busy handler, because waiting could deadlock. The ingest drain claims jobs in short write transactions all the time the sidecar runs.

**What a learner saw.** "Help me remember" (or any commit preset) in the Reader could fail with the busy message while an ingest or a book's build ran in the background. The error is retryable (`server._busy_error`), so the desktop shows it as an error with Try again where the call site offers a retry; the capture itself is idempotent on its client key, so a retry completes it. The frontend was not run.

**Fix.** Both appends take the write lock first (`BEGIN IMMEDIATE`), so they wait for the other writer within `busy_timeout` like every `Repository.atomic()` block. The fail-first test `test_commitment_arcs::test_an_arc_append_holds_the_write_lock_from_its_first_read` (durability lane, WAL, both appends) lets another connection commit right after the append's first `SELECT`: at the base the append raised "database is locked"; after, the other writer waits and the append lands. After the fix: 0 of 400 repeats of the D-30 test failed under the same load, and 0 of 100 of its sibling `test_invoke_preset_commit_enqueues_synthesis_and_proposes`. The test's assertion is unchanged; its comment now names the capture.

**Siblings checked** (every explicit deferred `BEGIN` under `src/`):
- `repositories.py` `_sync_projection` (321): a read-only comparison that rolls back, then `BEGIN IMMEDIATE` before writing. Sound.
- `repositories.py` 6426, 6442, 11521 (`canonical_observation_ledger*`, effective contracts): read snapshots, no write. Sound.
- `repositories.py` 13226 (reader capture outbox): its first statement is an insert, which takes the lock with the busy wait. Sound.
- `db/stores/write_provenance.read_snapshot`, `substrate/data_quality`, the CLI reports (`cli/router.py`, `plan.py`, `field.py`, `data_capture.py`, `success_head.py`, `probability_arms.py`) and `evsi_calibration/*_report.py`: read-only connections. Sound.
- `scheduling/controller_ownership.rebuild_ownership_head` (118): reads the events, then upserts the heads: the same defect. Fixed the same way; it has no production caller (only `test_controller_ownership`), so no fail-first test of its own.
- Without an explicit `BEGIN`, Python's `sqlite3` (isolation level `""`) opens its implicit transaction at the first write, so a read before it has already released its lock and the write takes the lock with the busy wait.

**Not verified.** The desktop's error rendering for this call site.

## R1-1: the bound runners at a refusal

**Reproduced** (`tests/test_sidecar_stops_serving.py`, a context loaded at the head, refused by another process's activation journal beside its database, which `serving()` sees on the next call). At the base:
- `test_a_refusal_stops_the_bound_runners_and_a_load_binds_them_again`: `ctx.ingest_jobs.repository` still returned the refused vault's repository (`DID NOT RAISE`); the map builds still admitted, request-started jobs were not cancelled, and `get_ingest_jobs` served the refused vault.
- `test_an_exam_grading_waiting_for_a_slot_at_the_refusal_never_starts`: a grading queued behind two busy slots ran after the refusal.
- `test_an_ingest_job_in_flight_at_the_refusal_writes_nothing_after_it`: the in-flight job's lease kept being renewed after the refusal (and the job published its write and the drain claimed the queued one).
- `test_exam_session::test_a_background_grading_records_no_grade_once_its_vault_is_no_longer_served`: new parameter (fails at the base by its signature).

**Cause.** `learnloop_sidecar/context.py:831` (`_stop_serving`) set the refusal and moved the generation, which stops handlers, the post-attempt worker and AD admissions, but the four runners were bound with the repository at load and never ask the context again. The ingest RPCs in `handlers/ingest.py` (`get_ingest_job(s)`, `cancel_ingest`, `get_ingest_batch`, `list_ingest_batches`, `cancel_ingest_batch`, `resume_ingest_batch`, `retry_synthesis`) reached only the host, not `require_vault`, so they kept reading and writing the refused vault too.

**Fix.** `_stop_serving` calls `_stop_bound_runners` on the first refusal (not again while it holds). Nothing in it joins a thread: it runs on the request thread or worker that met the refusal, and a join there would hold that request for as long as a runner's provider call runs (`close` still joins, bounded, at shutdown). What each runner does with work in flight at that moment:
- **ingest** (`DurableIngestJobs.halt`, `IngestRunner.halt`): the host lets go of its runner (so `repository` raises "not bound") and stops its loops, which end at their next turn. The runner claims nothing more (`run_next`), renews no lease (the heartbeat returns before its write), and interrupts the job's provider call. The job in flight is fenced through the existing ownership guard (`guard_ingest_writes` takes a `halted` predicate; `_JobGuard.check` raises `JobOwnershipLost`, which the runner already handles by returning without a write), and its outcome, batch refresh and dependency blocking are skipped, so its row stays as it was: still `running` under its lease, requeued by `recover_stale_leases` once the lease expires after the vault is served again. The Reader synthesis drain claims one request at a time and checks the halt before each claim.
- **exam grading** (`ExamGradingManager.halt`): a grading still waiting for a slot ends without grading; one already in its model call asks `ctx.serving()` before it records (`_grade_and_record_exam_answer(serving=...)`) and records nothing when refused. Either way the answer stays persisted and ungraded, and the next resume schedules it again.
- **map builds** (`BackgroundBuilds.halt`): admission closes and the generation moves, which is `close`'s linearisation point without its waits: every later write of a running build fails its fence; a write registered before it may still commit, as at a close's deadline. Its threads are joined at the next `close`.
- **request-started jobs** (`background_jobs.cancel()`): the epoch ends; each job's next model request is refused (`SpendCancelled`) and `closed_since(epoch)` turns true for the jobs that check it.

A load that succeeds (`load`, a full `refresh_vault_files`) binds ingest (a new runner; the host's loops may run again) and the map builds again; the job registry and the graders take new work as after `close`. The ingest handlers above now call `ctx.require_vault()` first and return the refusal's own error.

**Proof that no write reaches the refused vault.** The in-flight test compares the `ingest_jobs` and `ingest_batches` rows taken just after the refusal (once any renewal that began before it has committed) with the rows after the job's thread has ended: equal; no renewal starts in 0.5 s at a 10 ms heartbeat; the handler's write raised `JobOwnershipLost`; the queued job was never claimed; and the refusal returned while the job was still inside its blocked call (nothing was joined). 600 repeats of the file at `-n 6` under load passed (two test-side waits were fixed on the way: the exam test now waits until both slot holders hold their slots, and the in-flight test waits for a renewal already under way before it snapshots).

**What a refusal still does not stop** (ledger D-47, an owner call): a Reader synthesis request already in its model call records its answer; receipts of paid model calls are recorded after the fence (`allow_late_model_records`, the same rule as after a lost lease); a reading-sweep pass already running finishes; a request-started job writes whatever it writes after cancellation unless it checks `closed_since`; an exam grade can land in the moment between its `serving()` check and its write; a heartbeat that passed its halt check just before the halt commits once. Each is one write begun before the refusal. Recommendation: leave them (the proportionate-protection rule), unless the owner wants the journal case (another process's upgrade running) fenced at every write.

**Phone host and MCP.** The phone host's contexts are `SidecarContext.load_secondary` contexts: they bind no ingest and share one post-attempt worker (supplier-checked per context), and their refusal goes through the same `_stop_serving`, so their job registry, exam graders and map builds stop the same way. Same code path, fixed with it. The MCP attach (`learnloop/remote/runtime.py`, `RemoteRuntime`) binds no runners or workers ("no ingest runner and no workers"), and U4 already makes it serve nothing after a failed load: nothing to stop.

**Callers and siblings checked.** `_stop_serving`'s callers: `serving()` (journal seen) and `_stops_serving_when_refused` (`load`, `load_secondary`); both reach the new stop. Every place that rebinds: `load` (map builds, ingest, post-attempt worker), `load_secondary` (map builds). `DurableIngestJobs.bind` after a halt clears `_stop` so the reading sweep starts again; `_ensure_worker` does nothing while halted. `BackgroundBuilds.bind` after a halt does not drain the fenced generation (that would join on the load's thread); `close` still joins it. Found on the way: a vault switch may leave the old drain running on the old runner (D-46, read only, not run).

**Not verified.** The desktop's handling of the ingest RPCs' new refusal error (it gets the same error every other RPC gets while refused). A refusal while a real Codex call runs (the interrupt was exercised only through the code path, with no interruptible client in the test). The phone host end to end.

## Gates

See the report: the targeted test selection (`affected_tests.py --depth 0` on the source files, since `repositories.py` makes the default selection the whole suite, plus the rules' fixed list and every edited test file), `lint-imports`, `ruff`, the four vault validators, `check_gate_partition.py`, and the vault references regenerated once.

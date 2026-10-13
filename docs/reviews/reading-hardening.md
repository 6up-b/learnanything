# UX Phase 1 hardening: reading requests, check offers, the AI opt-out, build spend

**Branch:** `ux/reading-hardening` (worktree `learnanything-ux-impl`, base main `c50dd0bcb`, not rebased; the orchestrator merges). Owner-directed, 2026-10-13.

**Why.** Two UX Phase 1 paths reopened in review five times. Each fix patched one case and Codex found the next (Codex's verify of the finishing pass, `~/.cache/codex-agent/jobs/20261013-152028-hedJsZ`, verdict REOPENED: F1 and F2). This stage redesigns both instead of patching cases, removes a feature the owner did not ask for, and makes automatic builds' spend visible.

| Part | What | Commits |
|---|---|---|
| 1 | The book's reading request is level-triggered: a periodic sweep, no wake-up on the correctness path | `c869a468d`, `5e3aea355`, `4001d4002`, `befc48450` |
| 2 | One check-offer rule in the Reader, called by every offer path | `148f7427b` |
| 3 | The per-book AI opt-out is retired end to end | `70a17e162` (backend), `f42f3e223` (frontend), `5e3aea355` (spec) |
| 4 | `learnloop sources report` shows automatic book preparation's spend | `c10e5964a`, `4001d4002` (its query moved to the ingest queue's store) |

**Paid calls:** none ($0.00). Every model call in the tests is a house fake. No real provider, no network, no key read.

**Migration:** none. **Schema:** unchanged. **Config:** unchanged (no new leaf). **Algorithm version:** unchanged, no successor and no upgrade. Replay reads none of this: `source_auto_build_state` is WORKFLOW (no replayer), the check-offer rule is the Reader's UI, the opt-out decided only which workflow requests and builds ran, and the spend report only reads. `src-tauri` is untouched (no `cargo check` needed). The DB and configuration references were regenerated because their source-line citations moved (see Gate).

## Part 1: level-triggered reading requests

### What stranded, and why patching kept failing

The "keep one chapter ahead" request is durable (migration 199: one per book in `source_auto_build_state`, `wanted_revision` / `wanted_attempts` / `wanted_retry_at`). Whether it was acted on depended on someone waking the ingest worker at the right moment. Codex found five ways that failed:

| # | Scenario (Codex) | Why it stranded |
|---|---|---|
| a | A transient error in the worker's due scan, then its idle exit | The scan's exception was swallowed and counted as "nothing ran"; the exit check looked only for future retries |
| b | Restart reconciliation deferred behind an already-queued build | `bind()` recovers leases but never starts the worker; the deferral woke nothing, so the build and the request both waited |
| c | `cancel_batch` neither settled nor woke | The deferred request stayed due with no worker to see it |
| d | Blocking work finished by the CLI's `IngestRunner.drain()` | The CLI never runs the reading scan |
| e | A reconciliation read failure outside the planning handler | Logged, nothing scheduled; a request whose three worker retries had run out (`retry_at` NULL) was due for nobody |

### The design

**Every pending request is due now or at its retry time, and while the sidecar runs something looks.** `DurableIngestJobs` runs a **reading sweep** thread for as long as it is bound in the background:
- **One pass** is one query, `Repository.pending_reading_requests()` (every book's pending request), then `add_source.act_on_reading_request` on each one due. A request is due when its `retry_at` has passed, or it has none, or the stored value does not parse. Acting keeps its contract: it settles, defers or fails exactly the revision it read (F9), under the in-process reading lock.
- **Pace:** every `READING_SWEEP_SECONDS` (30 s), sooner when the next retry time comes first. The first pass waits one pace, because the start reconciles every request itself.
- **Wakes only bring a pass forward.** The worker wakes the sweep after any round that ran a job. A failed act outside the sweep (the Reader's RPC, the start) wakes it. A failed act inside the sweep's own pass does not: the pass's outcome alone sets its next wait, so its backoff holds (Codex review F2, `6d892e9de`). A Reader report acts at once on its own RPC, as before.
- **A failed pass is never "nothing due".** A failed scan, or an act whose failure could not even be recorded, is retried after `READING_SWEEP_RETRY_SECONDS` (1 s), doubling up to the pace. Every iteration of the loop sits inside that handling, so the thread cannot die on a pass.
- **A failed act backs off and is never given up:** 2, 10, 30, 120 s, then every 300 s (`READING_RETRY_DELAYS`, the last repeating). This replaces the three bounded worker retries and the NULL "retries ran out" state. While a request is unsettled the Reader's next report still asks again at once (F8), and the start still acts on every pending request at once with a fresh backoff.
- **A deferral is not a failure.** If the book's work is unfinished, the request stays due and its failed attempts are forgotten, so the Reader stops re-asking. When that work waits on the worker (queued or running, not only waiting for the learner's input), the act starts the worker. After a restart nothing else would. Work waiting for the learner's answer starts nothing.
- **The worker no longer scans reading requests.** It drains and exits when idle. Its old exit check (`_reading_retry_waiting`) is gone, and with it the race the finish review's F1 patched.
- **Lifecycle.** The sweep starts at a background `bind()`, and a stopped host gets it back from `_ensure_worker`. A foreground rebind (tests, the CLI) makes it step aside at once, and `shutdown()` joins it. Its exit runs under the same lock that starts it, so a start racing an exit either sees the thread gone or keeps it running.
- **The thread holds its host weakly** (`_run_reading_sweep`). It takes the host only for a pass, so a host nobody uses any more ends its sweep at the next wake. That covers a library left behind, or an earlier test's sidecar in the same pytest process: before this, a full-suite worker process kept one idle sweep thread per sidecar a test had made.

**Every path that completes or cancels blocking work leaves the request settled or due:**

| Path | Leaves the request |
|---|---|
| The worker finishes a build | settled by `after_auto_build` (the next chapter is queued), or due if that failed |
| A build fails or is paused for spend, or the kill switch cancels it | due: the sweep's next pass acts (failed chapters wait for the card's Retry; with auto-build off the act settles it) |
| The CLI drains it (`learnloop ingest-batches resume`, `import`, …) | settled by `after_auto_build`, or due for the running sidecar's sweep or the next start. The CLI runs no sweep and no start reconciliation. *Corrected after Codex's review:* a build the CLI drains to completion runs its own completion step (`after_auto_build`, unchanged by this stage) in the CLI process. That step acts on a pending request and queues the follow-on planner, which the same `drain()` may then run, and so the next build too, under the same admission guards (daily cap, ask-first threshold) as the sidecar |
| A cancel: the sidecar's `cancel_ingest_batch`, the legacy `cancel`, `kill-codex`'s interrupt, the CLI's `ingest-batches cancel` | **settled** (below) |
| Undo | forgotten (its revision advances, as before) |
| The start | acted on at once, with a fresh backoff on failure. A failed read leaves it pending, and so due for the sweep |

**`cancel_batch` semantics, decided: a cancel settles the request.** The learner's cancel answers it. `settle_reading_for_cancelled_batch` finds the books whose automatic-build work the batch held: an Add's or a build's planner, a planner's build batch, or a link Add's planner through its import. It settles each book's request at the revision it has now. The cancel and the settle are one transaction (`IngestRunner.cancel_batch(…, alongside=…)`, Codex review F1, `5a7880e8f`). If reading or settling the request fails, nothing is cancelled and the cancel reports the error. A crash before the commit leaves neither. In the sidecar both also run under the reading lock, so no act in that process interleaves.
- **The next ask:** the next section the learner first reaches, reveals or completes is a new revision and is acted on as usual.
- **What gets re-planned:** chapters whose build was cancelled count as failed and wait for the card's Retry, as before. A planner cancelled before it ran leaves its chapters unplanned, so a later ask may plan them.
- **Revision-safe:** a request recorded after the cancel's read survives.
- **Why not "pending, due again when the learner next reads":** leaving it pending would let the sweep re-plan the cancelled work within one pace (the finish review's Q-F1). Parking it needs a not-due state that the start, the sweep and the Reader would all have to agree on.
- **Across processes:** the CLI's cancel does not hold the sidecar's in-process lock. Its cancel and settle commit together, but a sidecar act that read the request just before that commit, and checks the book's work just after it, could still plan once.

### Tests (`tests/test_reading_request_sweep.py`, the real worker and sweep threads, the sweep's clock scripted through `DurableIngestJobs.reading_clock`)

**Fail-first.** Run against `c50dd0bcb` before any fix, 11 of the 12 failed. Codex's five scenarios:

| Test | Failed with |
|---|---|
| (a) `test_a_a_transient_scan_failure_is_retried_not_taken_for_nothing_due` | "the due request was stranded". Codex's exact sequence: the retry is still to come in rounds 1–2, round 3's scan raises once, and the worker exits |
| (b) `test_b_a_start_deferred_behind_a_queued_build_runs_that_build_and_then_acts` | "the build queued before the restart never ran" |
| (c) `test_c_cancelling_the_build_a_request_waits_behind_settles_it` | `'u4' is None` |
| (c) `test_c_a_request_recorded_after_the_cancel_survives_it` | `'u4' == 'u5'` |
| (c) `test_c_the_cli_cancel_settles_the_request_too` | `'u4' is None` |
| (d) `test_d_work_the_cli_finishes_leaves_the_request_due_for_the_sweep` | "the request waited for a wake-up". A CLI runner drains Ch. 3's build, which fails there |
| (e) `test_e_a_read_failure_at_the_start_is_retried_by_the_sweep` | "the request was stranded". The first read raises; retries had run out before the restart |

The pace and lifecycle tests failed too:
- `test_a_failing_request_backs_off_and_is_never_given_up` failed on its scripted backoff (2, 10, 30, 120, 300, 300, 300 s).
- `test_a_request_waiting_on_the_books_work_is_not_replanned_by_the_sweep`, `test_the_sweep_stops_with_the_sidecar_and_a_foreground_host_starts_none` and `test_a_scan_that_keeps_failing_backs_off_to_the_sweeps_pace` (waits 30, 1, 2, 4, 8, 16, 30, 30) failed because the sweep did not exist.
- The guard `test_the_sweep_acts_once_the_books_work_ends_on_the_sidecars_own_worker` passes before and after.
- `test_no_stored_retry_time_keeps_a_request_from_ever_being_due` was added with the hardening commit and fails on `c50dd0bcb` too. `test_the_sweep_ends_with_a_host_nobody_uses` pins the weak hold.

**Under a loaded full suite.** The first two full-suite runs each failed sweep tests in one xdist worker; each passes alone in about 4 s.
- **(b)** finished its builds after the test's 15 s and then 60 s bound. Its library shows the request settled and Ch. 4 built.
- **(a)** was a test artifact. Its scripted scan sequence was shared with every sweep in the process, and its clock moved only after a successful second scan.

The fixes:
- the scripted scans now count only the test's own library, and the clock moves before the read;
- the polls (which return as soon as their condition holds) are bounded at 120 s;
- the sweep thread's weak hold on its host means no idle sweeps pile up in a worker process.

**No hot loop.** A request waiting behind its book's work is re-checked once per pass, which costs a few queries. It works out no chapters and queues nothing (`outline_chapters` is called 0 times over the passes), and it writes nothing after its first deferral. A request waiting on the learner's input starts no worker. The Reader's reports inside a section stay coalesced (`test_f8_a_request_waiting_on_running_work_is_quiet_for_the_reader`, unchanged).

**Earlier tests changed on purpose** (they pinned the bounded worker retries and the worker's exit check):
- `test_ux_phase1_finish.py`:
  - `…the_start_rearms_a_request_whose_retries_ran_out` became `…the_start_acts_at_once_and_rearms_a_backed_off_request`;
  - `…the_worker_stays_for_a_retry_that_falls_due_between_its_scan_and_its_exit` became `…a_retry_falling_due_after_the_worker_stepped_aside_is_acted_on_by_the_sweep`. The real worker loop exits idle, and the sweep acts at the deadline.
- `test_ux_phase1_round2_rereview.py`: `…the_worker_retries_a_bounded_number_of_times…` became `…a_failing_keep_ahead_is_never_given_up_and_the_next_report_asks_again`.

## Part 2: one check-offer rule

**The rule** (`apps/learnloop-tauri/src/screens/reader/checkOffer.ts`, a pure `checkOffer(input)`). It returns `{ offer, reason }`.

A section's check:
- **No check, checks off, or answered or set aside:** never offered.
- **Pinned:** offered earlier this visit, or the learner pressed "quick check →". It stays offered until answered or set aside.
- **While the original PDF's manifest is pending** (`surface: "loading"`): nothing is offered, on any section.
- **Ahead of the reading position:** never offered.
- **Behind the reading position:** offered once the learner reads in this visit.
- **The current section's after-section check** (auto-authored checks are after-section): offered for reading in this visit (`readingMoved`: the learner's own movement or playback since the Reader last placed the page) at its point.
  - In the original: its last page (D22).
  - Without page information, in the text view (including after a manifest error or unavailable), and on video: 70 % of the section.
- **Before- and during-section checks** keep their own points (the start, 45 %).

RW1a's passage-scoped check is offered only on the reconnect line of an open inquiry the learner raised in this visit, and never while skimming.

**Every offer path calls it.** `ReaderScreen` computes the offered set once (`offeredCheckSections`) and pins whatever it offers. Every path reads that set:
- the guide's cards and the rail's badge (`openQuestionSections`);
- the original's section-break offer (`pdfOfferSection`);
- the text view's section-break button (`allowQuestion`);
- the proactive-offer log.

So the manifest-pending and manifest-error/unavailable fallbacks and auto-authored checks need no rules of their own. The reconnect line's quick check (inline and in the rail) is passed only when `checkOffer({ kind: "passage", … })` offers it (`ReconnectLine.onQuickCheck` is optional now).

**One more fix the tests found.** The learner's first scroll set `readingMoved` a frame before the reading position moved, so a scroll *away* from a resumed section's last page offered that section's check. The scroll's movement now lands with the position it led to, in one render (`movedPendingRef`). Placements clear it.

**Fail-first** (`ReaderScreen.checkOffer.test.tsx`, the real screen). Run against the screen at `c50dd0bcb`, 11 of 13 failed, each with "quick check →" already rendered on the resume:
- **manifest pending, guide first:** the text view's button beside the resumed passage (Codex's reproduction; the old test checked only the ready line while pending);
- **manifest error and unavailable, each in both orders, for an auto-authored and a placed check** (8 tests): the 70 % rule pinned the check on resume;
- **original PDF, both orders:** the section-break offer of a leftover check *behind* the resumed section.

Two guards pass before and after: a section first reached by reading follows the normal rule, and an offered check stays after a jump. `checkOffer.test.ts` holds 14 unit tests. The case where the original's manifest arrives before the guide is covered by the existing `ReaderScreen.followsLearner.test.tsx` "#2" tests, which pass. `ReaderScreen.inquiry.test.tsx` gains an RW1a guard: a resume shows no passage check, and a reconnect line the learner raises does.

**Changed on purpose.** `ReaderScreen.inquiry.test.tsx` "the quick-check marker … is static" used an auto-authored check offered on a jump. It now uses a during-section check, which is offered where the page opens, so it keeps testing the marker.

## Part 3: the per-book AI opt-out is retired

**Owner, 2026-10-13:** it is fine to send books to an AI. The per-book opt-out (ux_learnloop_v1 §6.6, "Keep this book on this computer", shipped as "Never send this book to an AI", D23) was not requested.

**Removed:**
- **The controls and every learner-facing string:**
  - Add's "Never send this to an AI";
  - book details' "Never send this book to an AI" and "Let LearnLoop write questions for it";
  - every "Never sent to an AI" status line;
  - the connect sheet's "You can choose never to send a book to an AI when you add it."
- **The RPC fields:** `add_source.keepLocal`, the `keep_local` and `share_with_ai` actions of `source_action` (both now validation errors), and the library card's `keepLocal`. `AddSourceOptions.keep_local`, `keep_on_this_computer` and `share_with_ai` are gone.
- **Every refusal built on it:**
  - question builds: inventory, bootstrap, append, admission and apply;
  - the Reader's Ask;
  - background requests: when queued, when retried, and in the drain;
  - section checks;
  - RW1a's passage check, both when asked (`reader.reconnect_answer`, added at the landing) and when its job runs;
  - the local-only narrowing of whole-file extraction.

**Kept:**
- the one consent sentence and OK when an AI is connected;
- the separate OK before a whole file leaves (`needs_upload_ok`).

**Retired like other retired settings.** The `source_artifacts.keep_local` column (migration 198) stays (no migration) and nothing reads it. `learnloop doctor` warns `source:retired_keep_local`, naming the books that still carry it (`Repository.sources_with_retired_keep_local`, which is safe on a database without the column). States the old code left behind move on with one tap:
- a plan that waited on it: "No questions for this book yet · Build them as you read";
- an import it refused: "This recording isn't ready yet · Get it ready".

These books are not rebuilt automatically, because the learner had chosen otherwise (Q-RH4).

**Spec and records:**
- `ux_learnloop_v1.md` now says there is no per-book opt-out: §6.6, the §6.4 table, §7.2 details, the §8.2 Add box, the §8.3 connect sheet and Q4.
- `ux-phase1.md`'s "Keep-local coverage" decision and `ux-phase1-finish.md`'s D23 and Q-U are marked settled.

**Fail-first:**
- `tests/test_keep_local_retired.py` (8) and the two inverted RW1a landing tests: 10 failed on the previous sources.
- Frontend: `BookShelf`, `AddSource` and `ConnectAI`, 3 failed.

**Removed tests:** the 12 keep-local tests of `test_ux_phase1_review_fixes.py` (F1's keep-local half, its re-review tests, F13), `test_ux_phase1_auto_build.py::test_a_book_kept_on_this_computer_sends_nothing` and `test_ux_phase1_finish.py::test_6_a_book_never_sent_to_an_ai_says_so_plainly`. F1's whole-file OK test stays.

## Part 4: automatic builds' spend, visible

`learnloop sources report` (and `--json`'s new `auto_build_spend`, governed by `--spend-days` like the source service's) adds, from `add_source.auto_build_spend_report` (reads only):

- **Today's daily guard, as admission counts it:**
  - every metered receipt today, and of that, automatic builds';
  - what builds still running hold back (their estimate less what they spent);
  - `ingest.cost_pause.daily_cap_usd` ($5) and what is left;
  - the $1 ask-first threshold.
- **Per UTC day:**
  - automatic builds' metered receipts and dollars (**settled**);
  - the estimates of the metered builds planned that day (**reserved**);
  - subscription receipts and tokens (estimated only, never counted against a cap);
  - every metered receipt that day.
- **The largest builds:** book, chapters, status, reserved vs settled, receipts.

No new UI, setting or cap. One store read was added (`ingest_batch_spend_rows`: an automatic build's receipts with their batch). It lives in `db/stores/ingest_queue.py`, because `tests/test_ingest_queue_store.py` allows only one owner of SQL on the queue tables. The first full-suite run caught it in the model-calls store.

**Tests:** `tests/test_auto_build_spend_report.py` (3). They failed first at import. The CLI help snapshot was regenerated (`sources`, `sources report`).

**On real copies.** On backup-API copies of both tracked fixtures (below) it prints the guard ($0.00 of $5.00, $5.00 left) and zero rows. Neither library has automatic builds yet.

## Manual run (backup-API copies only)

- **Copies:** `learnloop.db.copies.copy_tree_with_databases` copied the worktree's tracked `fixtures/linear_algebra` and `fixtures/probability` to `fixtures-local/rh-linear_algebra` and `fixtures-local/rh-probability`.
- **`learnloop doctor --fix-state --json`:** 106 and 134 issues, the same counts as the landing's parity. None is `source:retired_keep_local`: neither library has a kept-local book.
- **`learnloop sources report --spend-days 3`:** as above.
- No app or server was started. The usability harness was not needed: the component tests drive the real screen through every path in both orders.

## Deviations this stage adds

- **DR1.** A cancel settles the book's reading request (above, with the reason).
- **DR2.** A failed request is never given up (2/10/30/120 s, then every 300 s). The three bounded retries and the NULL "ran out" state are gone. NULL or an unreadable retry time reads as due now.
- **DR3.** The sweep's one query reads `source_auto_build_state` without an index. The table has one row per book, so it is bounded by the size of the library. An index needs a migration (placeholder 200, colliding with the parallel stages): Q-RH1.
- **DR4.** The check-offer rule is a little stricter than "today's rules" in two places. Both follow from D22's "a resume or a jump never offers it":
  - a check left *behind* the reading position also waits for reading in this visit (it was open on arrival);
  - in the text view, a jump (a search hit, a peek) now needs reading before the landed section's after-section check is offered (in the original it already did).
  - Before- and during-section checks keep their points.
  - An auto-authored check in the text view waits for 70 % with reading, where it used to open at once.
- **DR5.** The CLI runs no reading sweep and no start reconciliation: it leaves requests due for the sidecar's sweep or the next start. *Corrected after Codex's review:* a build the CLI drains still runs `after_auto_build`, which acts on the pending request and can queue a follow-on planner that the same drain runs (pre-existing, unchanged here; see the table above).

## Gate

Run in this worktree with `TMPDIR=<worktree>/fixtures-local/tmp`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` · `uv pip install pypdfium2` | ok: 163 packages resolved. The sync removes pypdfium2 and the install puts back 5.14.0 |
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** (at `befc48450`) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10,140 passed**, 0 failed (8 min 25 s, at `befc48450`) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 10,041 deselected (2 min 19 s, at `befc48450`) |
| `npm install` · `npm run typecheck` · `npm test` · `npm run frontend:build` | up to date (281 packages) · clean · **75 files, 506 tests passed** · built, with the existing chunk-size notice. Run at `f42f3e223`; nothing under `apps/` changed after it |
| `cargo check` | not needed: nothing under `src-tauri` changed |
| References | `db_generate_reference.py` at `befc48450`: schema head 199, 318 table notes, 795 configuration leaves, all unchanged. Only source-line citations and the reading-request repository surface moved. `db_validate_reference.py`: errors `[]`. `validate_vault.py`: passed, 1098 notes |

Earlier gate runs, before the last two fixes:
- **At `5e3aea355`:** the full suite gave 10,137 passed and 2 failed. One was `test_ingest_queue_store.py::test_ingest_queue_sql_has_one_persistence_owner`, fixed in `4001d4002`; the other was sweep test (b) on its 15 s bound.
- **At `4001d4002`:** 10,137 passed and 2 failed, sweep tests (a) and (b) in one loaded xdist worker (see Part 1, "Under a loaded full suite"); the durability lane gave 99 passed.
- **Frontend:** a vitest run during another stage's load failed three `PracticeScreen.test.tsx` vault-switch tests on timing. They pass alone (23/23) and in the clean run above.

## Safety

- No paid call, no real provider, no network. No key, credential, `.env` or `settings.env` file was read.
- The owner's working vaults in the main checkout were never opened. The worktree's tracked `fixtures/linear_algebra` and `fixtures/probability` were opened only to make the backup-API copies. `git status fixtures/` is clean.
- No tailscale command was run. Nothing was merged, pushed or rebased.

## Open questions for the owner (recommended defaults applied)

- **Q-RH1.** An index for the sweep's query (`source_auto_build_state(wanted_retry_at) WHERE wanted_section_id IS NOT NULL`, migration placeholder 200)? Recommended: **no**. The table holds one row per book, and the query runs every 30 s.
- **Q-RH2.** Cancel semantics: settle (applied), or keep the request pending until the learner next reads? Recommended: **settle**. The next section the learner reaches asks again.
- **Q-RH3.** The stricter offers in DR4 (a leftover behind a resume, and a text-view jump, wait for reading). Recommended: **keep**.
- **Q-RH4.** Books that still carry the retired choice show one tap ("Build them as you read" / "Get it ready") rather than being rebuilt automatically. Recommended: **keep** (doctor names them).
- **Q-RH5.** The sweep's pace: 30 s. The worker's nudge makes the usual case immediate. Recommended: **keep**.

# reading-hardening, Codex review 2: findings and fixes

**Branch:** `ux/reading-hardening` (worktree `learnanything-ux-impl`, base main `c50dd0bcb`, not rebased; it lands after the exam-protection landing). **Review:** Codex, `~/.cache/codex-agent/jobs/20261013-200341-MF4nxL`, reviewed through `8fcf98f90`, the verify follow-up. **Earlier rounds:** [reading-hardening.md](reading-hardening.md) (the stage and its verify follow-up) and [reading-hardening-codex-review.md](reading-hardening-codex-review.md) (review 1).

Codex returned two findings, both Medium. Its two "claims that don't hold" are the same two findings. Both reproduced exactly as described, and both are fixed. Nothing was rejected.

## Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Settling before worker startup can strand the committed build | **fixed** | `f286c113d` | `tests/test_reading_hardening_2_fixes.py`: `test_f1_a_build_whose_worker_failed_to_start_is_run_by_the_sweep`, `test_f1_a_build_queued_just_before_the_process_ended_runs_at_the_next_start`; for the new API, `test_f1_the_start_and_the_sweep_leave_work_that_cannot_run_alone`, `test_f1_a_foreground_host_starts_no_worker_of_its_own`, `test_f1_a_failed_check_for_queued_work_is_retried_by_the_sweep` |
| F2 | Medium | A delayed video-seek landing still counts as watching | **fixed** | `7e6df9f0d` | `ReaderScreen.checkOffer.test.tsx` › "a video seek (verify N1)": "a report from before the seek, then a landing after the settle window, is still a placement", "a report from before the seek that arrives just after its landing is not playback"; `ReaderScreen.followsLearner.test.tsx`: "reading-hardening review 2 (F2): a jump that lands late, after a report from before it, is not watching"; guard: "a seek whose landing is never reported stops holding playback back" |
| C1 | (claim) | "Recovery does not depend on a wake-up" | **holds again** | `f286c113d` | It was F1: the queue is now checked at the start and on every sweep pass, independently of any request |
| C2 | (claim) | "N1 is fully closed" | **holds again** | `7e6df9f0d` | It was F2: the panel acknowledges each seek's landing, and reports sent before it never reach the Reader |

### Fail-first

Each test was run against `8fcf98f90` (the reviewed revision) before its fix.

| Test | Failed with |
|---|---|
| `test_f1_a_build_whose_worker_failed_to_start_is_run_by_the_sweep` | "the build queued before the worker failed to start was stranded": Ch. 3's planner was still queued after 60 s, with the sweep passing every 0.05 s |
| `test_f1_a_build_queued_just_before_the_process_ended_runs_at_the_next_start` | "the build queued before the restart was stranded": still queued 60 s after the restart |
| the three tests of the new API (`resume_book_preparation`, `has_runnable_ingest_job`) | `AttributeError` (the API is new) |
| checkOffer › "… then a landing after the settle window, is still a placement" | `expected true to be false`: the summary's check was shown at the landing (Codex's exact sequence) |
| checkOffer › "… arrives just after its landing is not playback" | `expected true to be false`: shown at the first report after the settle window, 2.4 s after the click, still inside the cue it landed on |
| followsLearner › "… a jump that lands late …" | the unwatched one-cue Summary's check was authored (`reader_author_section_question` for `u2`) |

Of the 8 new tests, 7 failed. The guard ("a seek whose landing is never reported…") passed before and after: it pins the new design's give-up, not the bug.

## F1: a book's queued preparation is recovered from the queue

**What was wrong.** The verify follow-up (its F1) put the act's settle and its enqueue in one transaction, and started the worker after the commit. That removed the only durable trace of the work. Before it, the request stayed pending until the build was queued. After a failure the start's reconciliation (or the sweep) found it, saw the book's work queued, deferred, and `wake_blocking_work()` started the worker. Now the request is settled at commit. If `_ensure_worker()` then failed, or the process ended first, the planner stayed queued, and nothing durable pointed at it:
- the start's reconciliation and the sweep found no pending request;
- `bind()` recovers leases and starts no worker.

The planner then waited for an unrelated learner action (an enqueue, or opening a book's Reader, which kicks the reader drain). Codex reproduced it with the production repository and enqueue methods; so did the two scenario tests here, through the real RPC, threads and restart.

**The fix.** Enqueue and settle stay one transaction. The work is recovered from the queue itself:
- **`DurableIngestJobs.resume_book_preparation()`.** If the queue holds a book's automatic preparation that the worker could claim now, and no worker is running, it starts the worker (`_ensure_worker`). "A book's automatic preparation" means an Add (`add_source`), a build planner (`auto_study_map`) or a planner's build batch (`batch_auto_…`). It checks each lane only when that lane's thread is not alive. It returns whether it started the worker. A foreground host (the CLI, tests) starts nothing: it drains on its own.
- **The start calls it.** `SidecarContext.load` runs it in the start's maintenance, after `reconcile_reading_builds`, in its own `try` so it never blocks opening the library.
- **Every sweep pass calls it**, whether or not any request is pending. If the check fails, the pass counts as failed and is retried with the sweep's backoff (1, 2, 4 … s up to the pace), never taken for "nothing queued". The check never wakes the sweep it runs on (review 1's F2 still holds).
- **`Repository.has_runnable_ingest_job()`** (in the ingest queue's store, its sole SQL owner) applies the claim's own eligibility. The job is queued, its batch is not being cancelled, and every job it depends on completed. It is read-only, and can be narrowed by job type, workflow and batch-id prefix. Work the worker could not claim never starts an idle worker pass after pass: a job behind a dependency waiting for the learner, or a job in a batch being cancelled.

**Why scoped to a book's preparation.** A first version recovered every queued ingest job. Spec §6.2 says "`queued` resumes" on startup, and no host does that today. The targeted run showed what that widens. `test_reader_reconnect.py::test_the_quick_check_read_reports_its_durable_jobs_state` opens a fresh sidecar over a library with a queued reader quick check, and the start began running it. That is a behaviour change for every workflow (quick checks, legacy ingest, repairs, promotions), outside this stage. So recovery covers exactly the work that lost its durable trace, the work reading requests queue and wait behind (Q-RH10 below). Once the worker is started it drains every eligible job, as it always has.

**What changed on purpose.** A sidecar start, or a sweep pass, with a book's preparation queued and no worker now starts the worker. Before, that work waited for the learner's next action. Nothing else changed: no request semantics, admission, spend or cancel path. The act still reports a failed worker start as a failed act (its build is queued and its request settled, so the failure record is a no-op). The sweep then runs the build.

## F2: a seek is acknowledged when it lands

**What was wrong.** The player's reports are messages, and one sent before a seek can arrive after it. Codex's ordering:
1. While watching, the learner clicks cue `v8`, past 70 % of the unread summary.
2. An in-flight report of the old position (`v5`) arrives 200 ms later. It moved the Reader's last playback cue back to `v5`, not as advancement (inside the 1.5 s settle window).
3. The seek lands at +2 s, after the window, while the player reports playing. `onPlaybackSpan` took `v5` → `v8` as playback, set `readingMoved`, and offered and pinned the summary's check.

The verify follow-up's tests delivered the landing promptly, so they missed this ordering. The same holds for a Contents or guide jump (`seekToSpan`) and the resume seek.

**The fix (the watch panel, `YouTubeWatchPanel`).** Every seek the panel makes (the resume, a transcript cue, a jump) is recorded with its target time, and its landing is acknowledged explicitly:
- **Until it lands, reports are from before it.** A seek has landed when the player reports a time from just before the target cue (the cue lookahead, 0.15 s) to 2.5 s after it (`SEEK_LANDING_LATE_S`). Until then, no time report reaches the transcript or the Reader. The Reader already knows the place from `onSeek`.
- **The landing is a placement, however late it comes.** The cue it lands on is reported with `advancing = false`, and only playing on from there is watching.
- **Just after an early landing,** for the rest of the settle window, a report that is not playing on from the landing is still from before the seek.
- **A seek whose landing is never reported stops waiting after 10 s** (`SEEK_LANDING_WAIT_MS`), for example when the learner moved the player in YouTube's own controls. The next report is where the player is, and it is a placement too.
- `cueAt` is now the one helper behind both the highlighted cue and the landing's cue.

The Reader side (`onPlaybackSeek` resets the movement, starts the settle window and keeps checks already offered pinned) is unchanged from the verify follow-up.

**What remains.** Q-RH9 is unchanged: a jump in the reported time made in YouTube's own controls while playing is still read as playback. A seek that never reports its landing within 2.5 s of its target holds playback back for up to 10 s. That case errs toward not counting, never toward offering a check unwatched (Q-RH11).

## Spec conformance (Codex's table, after the fixes)

- **Durable recovery without another learner action:** done for a book's preparation (F1). The broader "`queued` resumes" of spec §6.2 is Q-RH10.
- **Seek placement must not count as watching:** done (F2), including delayed landings and reports sent before the seek.
- **Unchanged and still as Codex found them:** the revision-checked enqueue and settle; the malformed-retry-time handling; the `keep_local` wording; schema, table roles, replay ownership and WAL settings; replay, evidence, certification, blind grading, embeddings and the verdict ledger; spend controls, dry-run and kill switches; privacy and outbound destinations.

## Scope and invariants

- **Migration:** none. **Schema:** unchanged (head 199). **Config:** unchanged (no new leaf; the seek constants are UI timings, like `SEEN_SETTLE_MS`). **Algorithm version:** unchanged. Replay reads none of this: `ingest_jobs` and `ingest_batches` are WORKFLOW tables, and the panel is UI.
- **Frontend:** `ReaderScreen.tsx` (the watch panel) and two of its test files. **Rust:** nothing under `src-tauri` changed (no `cargo check` needed).
- **References** were regenerated (`2df595b63`). The source-commit stamps moved, as did the configuration citations into `src/learnloop_sidecar/context.py` (nine lines added). The ingest tables' test list now names the new test file.
- **Paid calls:** none ($0.00). Every model call in the tests is a house fake. No provider, network or key was used.

## Gate

Run in this worktree with `TMPDIR=<worktree>/fixtures-local/tmp`, at `2df595b63` (code identical to `7e6df9f0d`).

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` · `uv pip install pypdfium2` | ok: 163 packages resolved. The sync removes pypdfium2 and the install puts back 5.14.0 |
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10,161 passed**, 0 failed, 46 warnings (9 min 49 s; the lock was free). That is the verify follow-up's 10,156 plus the 5 new tests |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 10,062 deselected, 0 failed, 1 warning (2 min 1 s) |
| `npm install` · `npm run typecheck` · `npm test` · `npm run frontend:build` | up to date (281 packages) · clean · **75 files, 512 tests passed** (the verify follow-up's 508 plus the 4 new) · built, with the existing chunk-size notice |
| `cargo check` | not needed: nothing under `src-tauri` changed |
| References | Source-line citations into `context.py` moved, so `db_validate_reference.py` first reported stale configuration citations. Regenerated in `2df595b63`: schema head 199, 318 table notes, unchanged; validation errors `[]`. `validate_vault.py`: passed, 1098 notes |

Targeted runs before the gate:
- every test file that drives the ingest queue or a sidecar context (81 files, with the new one): **1,222 passed**;
- the reading tests (this round's, the verify follow-up's, review 1's, the sweep's) under `--durable-sqlite` (WAL, `synchronous=FULL`): **35 passed**;
- `ReaderScreen.checkOffer.test.tsx` and `ReaderScreen.followsLearner.test.tsx`: **52 passed**.

## Safety

- No paid call, no real provider, no network. No key, credential, `.env` or `settings.env` file was read.
- The owner's working vaults were not opened, and no fixture vault was opened or copied. Every scenario runs on a fresh test library, so no manual run was needed. The reference scripts read `fixtures/migration_head_199` read-only.
- No tailscale command was run. Nothing was merged, pushed or rebased. A temporary `git stash` of `ReaderScreen.tsx`, used to run the new component tests against the unfixed screen, was popped at once.

## Open questions for the owner (recommended defaults applied)

- **Q-RH10.** Spec §6.2 says queued ingest jobs resume on startup. No host does that, so a queued quick check, legacy ingest, repair or promotion left by a closed app waits for the learner's next action. This round recovers only a book's preparation (F1). Should the start (and the sweep) resume every workflow's runnable queued work? Recommended: **yes, as its own change**, outside this stage. It moves behaviour for every workflow, and tests that open a sidecar over queued work need to say whether they expect it to run.
- **Q-RH11.** The seek-landing timings: a landing counts from the cue lookahead before the target to 2.5 s after it, and a seek with no reported landing stops waiting after 10 s. Recommended: **keep**. Both err toward not counting watching; the cost is at most 10 s of watching not counted after a seek the player never confirms.

# UX Phase 1: Codex review fixes

**Branch:** `ux/phase1-first-run` (worktree `learnanything-ux-impl`, base `4276a8d7`, not rebased). The review covered `4276a8d7..be3ad518` (the stage described in `ux-phase1.md`).

**Codex job:** `~/.cache/codex-agent/jobs/20261013-014808-jJ2Ys8`.

**Findings:** three High (F1–F3) and nine Medium (F4–F12), plus six claims in `ux-phase1.md` that did not hold. Every finding reproduced with a failing test first and is fixed (`high_fixed`). None is rejected. Two findings are fixed with a stated limit (F2: admission is per paid job attempt, not per physical request; F1: the separate OK covers whole recordings and whole PDFs on the Add path, the deliberate Ingest and Quick add paths keep their own per-build consent cards).

**Paid calls:** none ($0.00). Every model call in the tests is a house fake (`FakeInventoryClient`, `FakeSynthesisClient`, `FakeAppendClient`, built on `tests/structured_ai.py`); money is counted from synthetic `model_call_receipts` rows. No owner vault was opened or copied; no app or server was started in this step (no walkthrough was needed for the two small frontend changes, which the vitest cover).

**Migration:** `186_add_book_state.sql` (built as 186 while main's chain holds 181–183; expect a renumber at merge, and a conflict on the renamed `fixtures/migration_head_*`):
- `source_artifacts.keep_local` (RAW_LEDGER table, a per-book policy beside migration 104's `reader_enabled`);
- `source_auto_build_state` (WORKFLOW, no replayer): a book's automatic-build generation, advanced by Undo, and the reading position a running build could not act on yet. Source deletion removes its row.

`fixtures/migration_head_180` became `migration_head_186` (backup-API copy, only 186 applied, rollback journal, `integrity_check` ok, `foreign_key_check` clean); the ten tests and two scripts that name it, and both scripts' `SCHEMA_HEAD`, were updated; the DB reference was regenerated and validates (this also brings the configuration reference up to the stage's six new `[ingest]` leaves, which the stage had not regenerated: 678 → 684).

**Serving, replay, evidence, grading, embeddings:** unchanged. **Algorithm successor:** none. Auto-applying study maps from Add stays what the stage called it: a **content change under the owner's R1 decision** ("auto-accepted when confident, with undo"), not a serving change. These fixes only narrow when an automatic build may run or apply (kill switches read at run time, Undo generations, privacy, money); nothing changes how an applied map is scored, scheduled or projected.

## Review

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | "Keep this book on this computer" does not enforce privacy | fixed | `82414af5`, `e63242e5` (fail-first `74c6fa2a`) | `tests/test_ux_phase1_review_fixes.py::test_f1_a_later_build_of_a_kept_local_book_writes_no_questions`, `::test_f1_no_question_build_sends_a_kept_local_book`, `::test_f1_a_kept_local_recording_is_never_sent_to_transcription`, `::test_f1_sending_a_whole_recording_out_waits_for_its_own_ok`, `::test_f1_a_kept_local_book_never_uses_the_whole_pdf_model_or_hosted_marker`, `::test_f1_the_reader_sends_nothing_from_a_kept_local_book`, `::test_f1_book_details_can_keep_a_book_local_and_let_it_go_again`; `tests/test_ux_phase1_add_source.py::test_add_source_with_more_options`; `src/components/BookShelf.test.tsx` "keeps a book on this computer from its details, and lets it go again" |
| F2 | High | The cost pause is not a spend budget | fixed (admission per paid job attempt) | `82414af5` (fail-first `74c6fa2a`) | `::test_f2_build_them_never_passes_the_daily_cap`, `::test_f2_todays_spending_is_what_model_calls_cost_not_planner_estimates`, `::test_f2_each_paid_job_is_admitted_at_the_route_it_really_uses`, `::test_f2_a_retry_is_admitted_against_what_the_build_already_spent`, `::test_f2_the_dry_run_makes_no_call_and_writes_nothing`, `::test_f2_the_dry_run_command`; `tests/test_ux_phase1_auto_build.py::test_the_subscription_never_pauses_for_cost` |
| F3 | High | A crash can orphan an automatically applying build | fixed | `82414af5` (fail-first `74c6fa2a`) | `::test_f3_a_planner_that_dies_after_queuing_its_build_is_never_orphaned` |
| F4 | Medium | Kill switches do not govern already queued automatic work | fixed | `82414af5` (fail-first `74c6fa2a`) | `::test_f4_turning_auto_build_off_stops_queued_automatic_work`, `::test_f4_turning_auto_apply_off_after_planning_keeps_the_build_unapplied` |
| F5 | Medium | Undo permits an in-flight build to put content back | fixed | `82414af5` (fail-first `74c6fa2a`) | `::test_f5_undo_while_a_chapter_builds_keeps_it_from_putting_content_back`, `::test_f5_undo_cancels_a_build_still_waiting_to_run` |
| F6 | Medium | Failed chapters are treated as successfully built | fixed | `82414af5` (fail-first `74c6fa2a`) | `::test_f6_failed_chapters_are_built_again_by_build_the_whole_book` |
| F7 | Medium | Reading progress received during a build is discarded | fixed | `82414af5` (fail-first `74c6fa2a`) | `::test_f7_reading_ahead_while_a_build_runs_is_built_when_it_finishes`, `::test_f7_a_position_that_waited_across_a_restart_is_acted_on_when_the_library_opens` |
| F8 | Medium | Preparation completion throws away the reading position | fixed | `e63242e5` (fail-first `74c6fa2a`) | `src/screens/reader/PreparingView.test.tsx` "hands over at the page and place the learner scrolled to"; `src/screens/ReaderScreen.preparing.test.tsx` "opens the full Reader where the learner had scrolled to in the original"; `src/screens/reader/readingPosition.test.ts` (4 tests) |
| F9 | Medium | "Text recognition" can run the same non-OCR extractor again | fixed | `82414af5` (fail-first `74c6fa2a`) | `::test_f9_text_recognition_without_an_extractor_that_can_do_it_says_so`, `::test_f9_text_recognition_names_an_extractor_that_recognises_text`; `tests/test_ux_phase1_add_source.py::test_add_source_with_more_options` |
| F10 | Medium | Unrelated activity eventually removes older books from workflow accounting | fixed | `82414af5` (fail-first `74c6fa2a`) | `::test_f10_a_books_history_survives_lots_of_other_work`, `::test_f10_connecting_releases_a_book_however_old_its_wait` |
| F11 | Medium | Retry bypasses the specified zero-model repair path | fixed | `82414af5` (fail-first `74c6fa2a`) | `::test_f11_retry_tries_the_zero_model_repair_first_then_a_fresh_run` |
| F12 | Medium | The new Undo verdict is missing from `judgment_ledger` | fixed | `82414af5` (fail-first `74c6fa2a`) | `::test_f12_undo_records_the_owners_verdict_once` |
| C1 | (claim) | "A book kept on this computer sends nothing" | fixed (by F1) | `82414af5` | The test covered only a Markdown import's first plan. It is now true for later builds, retries, any build path, extraction uploads and the Reader's AI requests (F1's seven tests) |
| C2 | (claim) | Progressive-build tests demonstrate successful chapter building | fixed (tests) | `74c6fa2a` | Reproduced: with the bootstrap-only fake the Ch. 3 batch failed (`'FakeSynthesisClient' object has no attribute 'run_append_reconciliation'`) while the tests passed. `tests/ux_phase1_support.py` now uses `FakeBookSynthesisClient` (append lane via the house `FakeAppendClient`), and both progressive tests assert the batch completed and applied (`_assert_build_applied`) |
| C3 | (claim) | The job ledger reliably supports status, progression and Undo | fixed (by F3, F10) | `82414af5` | Deterministic child ids close the orphan window; every per-book read is filtered by source in SQL before any limit |
| C4 | (claim) | Subscription cost is $0 "per the owner's rule" | fixed (by F2) | `82414af5`; this commit (`ux-phase1.md` D3, §2 1.8) | The rule is a token estimate, `estimated_only`. `ux-phase1.md` corrected |
| C5 | (claim) | Kill switches stop automatic building and application | fixed (by F4) | `82414af5` | Now read when the work runs, before each paid stage and immediately before applying |
| C6 | (claim) | "Phase 1 is complete" | not claimed; open items stand | — | `ux-phase1.md` never said complete: D1 (chapter-first extraction), D2 (LLM subject filing) and the §6.7 rows recorded as deviations are owner questions Q-B and Q-C, unchanged here (not widened into this fix step) |

The fail-first commit `74c6fa2a` was run against the reviewed code (`be3ad518`, `src/` and `migrations/` stashed): 27 of the 27 tests in `tests/test_ux_phase1_review_fixes.py` and `test_the_subscription_never_pauses_for_cost` failed. (`test_missing_consent_waits_for_one_ok` also failed in that run, for a test-hygiene reason, not the code: an earlier run of the new F1 test, before it had its own `LEARNLOOP_CONFIG_DIR`, mirrored a recorded OK into the suite's shared `.pytest_tmp/global_settings_isolated/ai_defaults.toml`, which every new library then inherited. The review-fix tests now isolate the machine defaults per test (autouse fixture) and the stray, gitignored file was removed.) On the frontend, with `PreparingView.tsx`, `ReaderScreen.tsx`, `PdfReaderPane.tsx` and `BookCard.tsx` at `be3ad518`, the two F8 tests, the old hand-over test (its `onReady` signature changed) and the BookCard F1 test failed; 16 others passed.

### F1: the book's privacy is the book's, at every outbound boundary

**Reproduced.** A book added with *Keep this book on this computer* got `waiting / kept_local` once; *Build questions for the whole book* and Retry queued fresh planners without the flag and built it. A deliberate inventory of the same book ran. A kept-local recording, and any recording added through Add, went straight to `_extract_audio` (the transcription service). The Reader's section check, Ask and background requests had nothing to consult.

**Fixed.**
- **Persisted with the book.** `source_artifacts.keep_local` (migration 186) is set by `add_source` at registration, before anything is queued, for a local file; for a link, the import sets it the moment the link's book exists, before extraction. Asking for more privacy on a book already in the library always applies.
- **Builds.** The planner reads the persisted flag (not only its payload). `handle_inventory`, the bootstrap and append synthesis handlers and the Reader's quick-check job refuse a kept-local source (`code = kept_local`, not retryable) before any model call, whatever started them (Add, *Build the whole book*, Retry, a resume, a deliberate build from Under the hood).
- **Extraction that would upload the file.** `_pdf_payload_config` never selects the whole-PDF model (`engine = "native"`) or hosted Marker for a kept-local book (identity and extraction both read it, so they agree); a kept-local recording fails with "This recording is kept on this computer, and recordings can only be transcribed online." before any byte leaves (card: *Kept on this computer — this recording can't be read here*).
- **A new data flow asks once, in place (§6.6).** An Add's import carries `require_upload_ok`. Sending a whole recording to transcription, or a whole PDF to a PDF-reading model or hosted Marker, waits for a separate OK, `[ai.consent.whole_files]` (`data_flow = "whole_files"`, with its date). The card says *Transcribing this recording sends it to an online service · OK* (or *Reading this PDF sends the whole file to your AI · OK*); `source_action allow_upload` records the OK and resumes the Add. The connection's OK still covers passages and answers only.
- **Reader.** `reader.ask`, `reader.enqueue_request`, `reader.retry_request` and `reader.author_section_question` refuse a kept-local book (`kept_on_this_computer`).
- **Controllable (§6.4).** Book details now offer *Keep this book on this computer* or, when kept, *Let LearnLoop write questions for it* (`source_action keep_local` / `share_with_ai`; the latter plans a build). `get_source_library` cards carry `keep_local`.

### F2: a confirmation threshold and enforceable limits, counted from real spending

**Reproduced.** With the day's cap spent, *Build them* (`approved`) skipped the whole cost check and built. Today's spending summed planner estimates of automatic builds only; other calls (Reader, grading, embeddings) were invisible. A job's runtime fallback to a pricier route and a retry's second attempt ran under nothing. A subscription build recorded `estimate_usd = 0.0`. There was no dry run.

**Fixed** (`add_source.py`, "Money"):
- **Two things, kept apart.** The confirmation threshold (`threshold_usd`, `daily_cap_fraction`) asks first and *Build them* passes it once. The enforceable limits are the build's **authorization** (silent builds: up to the standing "runs without asking" amount, `threshold_usd`; approved builds: the approved estimate × 1.25 headroom) and **`daily_cap_usd`**, which *Build them* never passes: the card says *Paused — today's AI budget is used · Raise it* (details: "Or wait until tomorrow.").
- **Real spending.** `spent_today_usd` sums `model_call_receipts` since the start of the day: every model call LearnLoop made, whatever started it, the provider's reported cost or else its tokens at the route's price, subscription calls at nothing; plus what automatic builds still running are allowed to spend.
- **Admission of every paid job attempt.** `admit_auto_build_job` runs at the start of each inventory and synthesis attempt of an automatic build (a retry or resume is admitted again). It prices the job at the route resolved **now** (a runtime fallback is priced as itself) and checks it through `learnloop.ai.spend.SpendBudget` against what is left of the build's authorization (spent so far = the receipts of every attempt of every job of the build) and of today's cap. A refused job fails with `spend_paused` before any call; the card says *Questions for Ch. 1–2 would cost more than expected · Build them* (a fresh approval) or the budget line.
- **Subscription.** Never paused or capped (Slice A §5 rule 6); the plan keeps `estimate_tokens` and `cost_basis = "estimated_only"`, with dollars only when the owner set a price for the profile (`estimate_usd = null` otherwise), never $0.
- **Dry run.** `learnloop sources build-preview SOURCE_ID --vault … [--whole-book] [--approved] [--json]` (`preview_auto_build`): chapters, route, tokens, money, authorization, whether it would build, ask first or stop; zero model calls, the database opened read-only, nothing written.

**Limit, stated.** Admission is per paid job attempt, not per physical request. The money a job can spend is still bounded: the job's estimate is computed from the same token ceilings (`[ingest.budgets]`) that the inventory and synthesis services enforce on every call, and the job is admitted only when that ceiling-priced estimate fits. Admitting each physical request would mean putting a `SpendBudget` inside the canonical ingest pipeline (the inventory worker threads answer through a mailbox; synthesis shards), which is shared with deliberate builds: an owner question (Q-R2 below), not widened into this step.

### F3: a build is never orphaned from its planner

**Reproduced** with a `_Crash` (a `BaseException`, the process dying) raised right after `ctx.enqueue_batch` committed: the planner stayed `running` with no result; the card fell back on the planner; after lease recovery the planner was `failed` and resuming it queued a second build.

**Fixed.** The build's batch id is derived from the planner job (`batch_auto_<planner job id>`, `child_batch_id`) and passed to the runner's idempotent `enqueue_batch(batch_id=…)`; the plan (book, chapters, generation, money) travels on the build's jobs in the same enqueue transaction. A planner re-run finds its build and returns it without planning again. Status, coverage, Undo and accounting read `planner_outcome`, which falls back on the build when the planner never saved its result. The test kills the planner at that exact boundary, recovers the lease, resumes it, and checks one build, the right card lines and a working Undo.

### F4: kill switches govern work already queued

**Reproduced.** Flipping `[ingest] auto_build` or `auto_apply_passing_builds` off after the planner ran left the queued inventory and synthesis to call the models and apply.

**Fixed.** `admit_auto_build_job` reads `auto_build` when each paid job of an automatic build starts: off, the rest of the build is cancelled before any call (the card falls quiet). `auto_apply_allowed` is read **immediately before applying**, through a new optional `apply_gate` on `create_study_map`, `revalidate_synthesis_candidate` and `append_source` (default `None`: unchanged for every other caller); off, the proposal is kept unapplied (*Questions for Ch. 1–2 need a look · Review*).

### F5: Undo stops in-flight builds

**Reproduced** (Undo tapped inside the Ch. 3 append call): Undo reverted Ch. 1–2 and skipped the running build, which then applied.

**Fixed.** Undo first advances the book's generation (`source_auto_build_state.generation`), cancels queued planners and builds of the book (a running job is flagged), and only then reverts. A build planned in an older generation is never admitted again and its `apply_gate` is closed, so a late result stays an unapplied record; the card says *taken back out*, reading no longer grows the book's questions, and *Build them again* plans in the new generation.

### F6: coverage separates built, building and failed

**Reproduced.** A failed Ch. 3 build counted as built; *Build questions for the whole book* skipped it.

**Fixed.** `coverage()` returns `built` (finished: applied, or waiting for a look), `reserved` (planned or building) and `failed` (failed or stopped, and nothing later covers it); undone builds count for nothing. New builds skip `built ∪ reserved`; *Build the whole book* includes failed chapters (front matter excluded); reading-order growth also skips failed chapters (they wait for the card's Retry instead of looping).

### F7: reading progress during a build is kept

**Reproduced.** Jumping to Ch. 4 while Ch. 3 built returned nothing and Ch. 4 was never built.

**Fixed.** `advance_reading_build` records the latest position (`wanted_*` in `source_auto_build_state`; the latest wins) when work for the book is running. It is acted on when an automatic build's synthesis finishes (`after_auto_build`), when an AI is connected (`release_waiting_builds`) and when the library opens (`SidecarContext.load`, startup maintenance).

### F8: the hand-over keeps the learner's place

**Reproduced** (vitest): the preparing view handed over with the card only; the full Reader opened at the top.

**Fixed.** `PreparingView` reads the page at the top of its viewport and the offset into it (`readingPositionIn`) when the text becomes ready and passes it to `onReady`. `ReaderScreen.openSource` takes it as a hand-over: the PDF pane's new `scrollToPage(page, offset)` restores the same page and viewport offset (waiting for the page to be laid out), and the passage there (`spanAtPosition`, from the block geometry) becomes the reading position, so it is also where the book reopens. The `ReaderScreen` change is limited to the preparing hand-over (the resume effect yields to a pending hand-over).

### F9: text recognition is real or says it is not set up

**Reproduced.** The Add option and the card action set only `force_ocr`; with `engine = "pypdf"` (or `auto` without Marker) the same non-OCR extractor ran.

**Fixed.** The import names an extractor that recognises text, `{"engine": "marker", "force_ocr": true}`. Add and the card check first (`text_recognition_available`: local Marker, or the owner's hosted-Marker runtime, never for a kept-local book). Without one, Add still adds the book and says "Text recognition isn't set up, so this was added without it. Settings → Advanced → Import can set it up."; the card action fails with `text_recognition_unavailable`; the scanned-pages line offers *Set up text recognition* (opens Settings) instead; a pinned Marker missing at run time reads *Text recognition isn't set up · Set it up*.

### F10: a book's history is complete

**Reproduced** with 520 newer planner jobs for other books: the book's status, Undo and history vanished, and connecting an AI did not release a waiting book.

**Fixed.** New repository reads filter in SQL before anything is limited: `ingest_jobs_for_source` (job types × `source_id` in payload or result), `latest_ingest_job_per_source` (window function, for releasing waiting books) and `ingest_batches_by_workflow` (pending Adds). Spending comes from receipts (F2), not a window over planner jobs.

### F11: Retry repairs first

**Reproduced.** Retry on a build whose synthesis kept its candidate resumed the batch (a paid run).

**Fixed.** `retry_build`: when the failed synthesis kept a candidate and repairing it was not already tried, Retry runs `retry_synthesis(reuse_candidate=True, repair_candidate=True)` (zero model calls); otherwise a fresh synthesis (`retry_synthesis()`, which clears the reuse flags) under a new admission of each paid job. A failed planner's Retry now plans again without counting as *Build them* (the old line sent `build_now`, an approval).

### F12: Undo is an owner verdict

**Reproduced.** Undo left no `judgment_ledger` row.

**Fixed.** One row per reverted proposal: `task = "auto_applied_content"`, `left = proposal`, `right = source`, `judge = owner`, `verdict = rejected`, the item ids and generation in the rationale; the id is derived from the input, so a repeated Undo appends nothing.

## Gate

Run in the worktree at `5b63cfbd` (the code as committed; this review commit adds only documents) with `TMPDIR=<worktree>/fixtures-local/tmp`, after `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`:

| Check | Result |
|---|---|
| `uv run lint-imports --no-cache` | 14 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8706 passed**, 0 failed, 0 skipped (4 min 17 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **94 passed**, 8612 deselected |
| `npm install` · `npm run typecheck` · `npm test` · `npm run frontend:build` (apps/learnloop-tauri) | up to date · clean · **45 files, 252 tests passed** · built |
| `cargo check` (src-tauri) | not required: nothing under `src-tauri` changed in this step |
| DB reference: `db_generate_reference.py`, `db_validate_reference.py` | regenerated; validation `errors: []` (300 table notes, 684 configuration leaves, schema head 186) |
| New tests | `tests/test_ux_phase1_review_fixes.py` 27 passed; the four `tests/test_ux_phase1_*.py` files 46 passed |

The first full-suite run (at `e63242e5`) had two failures: `tests/test_cli_help_snapshot.py` (the new `sources build-preview` command; the snapshot was regenerated in `5b63cfbd`) and `tests/test_ingest_jobs.py::test_background_reader_drain_records_model_call_receipts`, which waits at most 10 s for a background drain thread and timed out under the parallel load; it touches nothing these fixes change, passed alone four times, and passed in the final run.

## Owner questions

- **Q-R1. Authorization headroom.** An approved build may spend up to 1.25 × its estimate; a silent build up to `threshold_usd` ($1). Keep, or change either?
- **Q-R2. Per-request admission.** Admission is per paid job attempt, bounded by the existing token ceilings (F2). Put a `SpendBudget` around each physical request in the canonical ingest pipeline (inventory worker threads, synthesis shards), for deliberate builds too?
- **Q-R3. The whole-file OK** is mirrored to the machine's AI defaults like the connection's OK (Q-F), so a library made later inherits it. Keep?
- **Q-R4. Migration 186** will renumber at merge (main holds 181–183); `fixtures/migration_head_186` conflicts with main's `migration_head_183` rename and must be rebuilt at the merged head.
- Unchanged and still open from `ux-phase1.md`: Q-A to Q-I (chapter-first extraction, LLM subject filing, when "Questions ready" leaves the card, …); captionless video still offers *Try again*, not *Transcribe the audio* (§6.7).

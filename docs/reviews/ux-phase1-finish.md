# UX Phase 1: finishing pass

**Branch:** `ux/phase1-first-run` (worktree `learnanything-ux-impl`, base `3d259303d`, not rebased onto main; the orchestrator merges). This is the last pass before Phase 1 lands on main.

**Inputs:**
- Codex's final verify of usability round 2 (`~/.cache/codex-agent/jobs/20261013-130030-Ux113F`, verdict REOPENED). F1–F7 were confirmed fixed. F8 was reopened, and F9 is new.
- The fresh persona re-test (the stage scratchpad's `usability/retest2.md`, evidence in `usability/_round3_retest/`). It found no blocker and no Phase 1 major. The first answered question came 1 min 43 s after launch, the first graded item at 4 min 32 s, and there was no error banner. It listed 10 remaining issues on Phase 1 surfaces plus the deferred ones.

**Outcome:**
- Part A: F8 and F9 are fixed with one durable request model. The in-memory retry map is gone.
- Part B: items 2–10 are fixed.
- Item 1 (T8) and the deferred Phase 2–5 items are left alone, as instructed.
- Every fix has a test that failed first.
- No new setting and no new panel.

*Superseded in part by Codex's review of this pass (`ux-phase1-finish-codex-review.md`). It found two gaps, and both are fixed there:*
- *F8: the worker could exit just as a retry fell due.*
- *#2: the resumed-check guard missed a PDF manifest that arrived after the guide.*

**Paid calls:** none ($0.00). Every model call in the tests is a house fake. No real provider and no network were used, and no app or server was started.

**Commits:**
- `f74797d66`: Part A (F8, F9), migration 187, the head fixture and the DB reference.
- `23ec08aea`: Part B (#2–#10).
- The commit that adds this file, with the reference stamps regenerated at `23ec08aea`.

**Migration:** one, `187_reading_request_revision.sql`. It adds three WORKFLOW columns to the branch's own `source_auto_build_state`. Both 186 and 187 were built on this branch while main's chain also reached 186, so **both renumber at the merge** (see Q-W).
- **Schema head:** 187.
- **Head fixture:** `migration_head_186` became `migration_head_187`, a backup-API copy of 186 with only 187 applied: checkpointed, rollback journal, `integrity_check` ok, `foreign_key_check` clean. Its README is updated, and so are the 11 test files and 2 scripts that name it.
- **`SCHEMA_HEAD`:** 187 in both reference scripts.

**Config:** unchanged (685 leaves). **Algorithm version:** unchanged. Nothing here changes scoring, scheduling, projections or what Today serves.

## Part A: one durable request for "keep one chapter ahead"

| ID | Severity | Title | Verdict | Commit | Tests (`tests/test_ux_phase1_finish.py`) |
|---|---|---|---|---|---|
| F8 | Medium (reopened) | A failed startup reconciliation strands reading advancement | fixed | `f74797d6` | `test_f8_a_failed_start_reconciliation_is_asked_again_by_the_next_reports`, `test_f8_a_failed_start_reconciliation_is_retried_by_the_worker`, `test_f8_the_start_rearms_a_request_whose_retries_ran_out`; guards `test_f8_a_saved_report_keeps_its_ask_even_when_acting_cannot_start`, `test_f8_a_request_waiting_on_running_work_is_quiet_for_the_reader` |
| F9 | Medium | An older background retry erases a newer deferred reading position | fixed | `f74797d6` | `test_f9_an_older_retry_never_erases_a_newer_deferred_position` (real threads, made deterministic with events), `test_f9_a_settled_request_clears_only_its_own_revision`; guard `test_f9_undo_invalidates_a_request_being_acted_on` |

**Fail-first.** All five main tests were run against `3d259303d` before any fix, using Codex's reproductions, and all five failed:
- **F8, the next reports:** `assert 2 == 3`. There was no third ask after the restart's failed reconciliation.
- **F8, the worker:** `reading_advance_pending` was `False` after the restart.
- **F8, re-arming:** `assert 5 == 6`. The worker never retried after the restart.
- **F9, the interleaving:** `assert None == 'u4'`. This is Codex's exact result: the older retry's unconditional clear deleted the newer position.
- **F9, the store's compare:** there was no request API at all.

The three guards were written with the fix and pin behaviour it must keep.

**The design.** The F1, F7, F8 and F9 findings shared one cause: reading advancement lived in two places, a durable position and an in-memory retry map, and each fix patched one of them. There is now one authoritative state per book: the **reading request**, held in `source_auto_build_state`.
- `wanted_extraction_id`, `wanted_section_id`, `wanted_at`: the position.
- `wanted_revision`: advanced by every new request (the newest position wins) and never reset.
- `wanted_attempts`: failed attempts at the current revision.
- `wanted_retry_at`: when the ingest worker acts on it next. It is due at once when recorded, backed off 2 s, 10 s and 30 s after failures, and NULL once those retries have run out.

**Recording.**
- `reader.mark_section_progress` decides to ask before it writes. It asks when a section is first reached, revealed or completed, or while the book's request is unsettled.
- The ask is recorded in the **same transaction** as the progress (`upsert_reader_section_progress(keep_ahead_request=True)`). A saved report therefore never loses its ask.

**Acting.**
- One function, `add_source.act_on_reading_request`, acts on the book's current request. It runs under one in-process lock (`DurableIngestJobs.reading_lock`).
- It **settles exactly the revision it read**, or marks exactly that revision failed. A newer request recorded meanwhile has a higher revision, so it survives and is acted on next. This is F9.
- Recording a request never waits for the lock.
- The callers:
  - the Reader's RPC (`keep_ahead_for_reader`);
  - the worker's retry pass, which reads due requests from the table (`retry_reading_advances`);
  - the start and AI reconnection (`reconcile_reading_builds`);
  - direct calls (`advance_reading_build`).
- A finished build (`after_auto_build`) also settles only the revision it acted on.
- Undo forgets the request and advances its revision, so an actor still holding the old revision can neither settle nor fail it.

**Outcomes.**
- **Queued, or nothing to do:** the request is settled.
- **Deferred** (the book's work is running): the request stays due. The worker acts on it once that work ends, however it ends. Reading on inside the section stays coalesced, as F1 requires, because a deferred request is not a failure.
- **Failed:** the attempt is counted and a worker retry is set, durably.
  - The Reader's next report asks again (`reading_advance_pending` now reads the durable `wanted_attempts > 0`).
  - **The start re-arms every pending request.** A reconciliation failure is no longer only logged: it gets a fresh set of worker retries and wakes the worker. This is F8.

**Also fixed.**
- The ingest worker could miss a wake that arrived while it was deciding to exit. Its exit now happens under the same lock `_ensure_worker` uses, and it clears its thread handle, so the next wake starts a worker.
- `plan_reading_advance` is the seam the earlier tests inject failures into. Four earlier tests moved to it, because the RPC no longer calls `advance_reading_build`:
  - `test_ux_phase1_add_source.py::test_reading_progress_reaches_the_reading_order_build`;
  - `test_ux_phase1_usability_round1.py::test_u4_…`;
  - the F1 counting test in `test_ux_phase1_round2_review.py`;
  - `_failing` in `test_ux_phase1_round2_rereview.py`, whose retry passes now take a wall-clock `now` (`_LATER`).

## Part B: the persona re-test's Phase 1 minors

| # | Re-test finding | Fix | Tests (failed first unless marked) |
|---|---|---|---|
| 1 | T8: the scan remedy is a terminal command | **left** (owner question Q-O/Q-L, below) | — |
| 2 | Axler reopened on "1.36" with the 1.35 examples on screen, and offered 1.36's leftover quick check before 1.36 was re-read | A resume (saved place or reading history) and a Contents jump put the passage at the **top** of the view (`PdfReaderPane` `scrollToSegment(page, span, "start")`, a 56 px margin under the pane's bar), so the page on screen is the one the header names. A cited or annotated passage is still centred. In the original PDF, a section's check (an after-section or written one) is offered only once the learner's own reading reaches the section's last page in this visit (#8), so a resume never offers it. | `ReaderScreen.followsLearner.test.tsx` "#2: a resume into a section offers its leftover check only after the learner reads there", "#2: Contents puts a section's start at the top of the view…"; the R3 geometry test now expects `(4, "s5", "start")` |
| 3 | "original pdf · 26 ingested pages" on a 404-page book | The header says "original pdf" when every page is shown, and "original pdf · showing 26 of its 404 pages" when only some are. The gap marker reads "⋯ pages 27–30 of the original weren't added to LearnLoop". "Ingested" is gone from the Reader. | `pdfPages.test.ts` (5 new) |
| 4 | Ask answers arrive below the fold | Once an answer lands, its card is scrolled into view (`block: "start"`). The composer keeps focus without pulling the view back. | "#4: a new Ask answer is brought into view, not left below the fold" |
| 5 | The one-time OK stays open over the Library during the build and blocks clicks | The sheet closes once the OK lands. The quiet status is the book's own line ("◐ Writing questions…") and the settings dot. A sign-in keeps its "Connected" line, because there the confirmation is the result. | `ConnectAI.test.tsx` "closes itself once the one-time OK lands"; guards "stays open when the OK did not land…", "keeps a sign-in's confirmation on screen" |
| 6 | Wording: a paper and a two-page handout called "book"; "Keep this book on this computer" ambiguous; "Open in Imports & builds" unexplained; "Build them" built one chapter while details offered "the whole book" | See "#6 in detail" below this table. | `test_ux_phase1_finish.py::test_6_*` (4); `BookShelf.test.tsx` "names a paper a paper in its details…"; updated `BookShelf`, `AddSource`, `denyList` and four Python tests |
| 7 | The guide's section bar is full on arrival at an unread section | The bar shows how much of the section was **read** (`sectionSeen`, or full once its check is done), not where the marker stands. It is a labelled progress bar ("Read of this section"). | "#7: the guide's section bar is empty on arriving at a section not read yet, and fills as it is read" |
| 8 | The section-break check fires before a section's last page | In the original PDF, the current section's check (after-section, or written by LearnLoop) opens once the reading position's page reaches the page of the section's last passage, by the learner's own reading. It stays pinned from then on. With no page information it falls back to 70 % of the section, still reached by the learner's own reading. Video and the text view are unchanged. | "#8: the original's section break waits for the section's last page"; three earlier tests now read after the resumed page settles (see below) |
| 9 | Key bar: "release ctrl capture box union · alt+drag sweep blocks" | Plain words, with "release ctrl" folded into its line: drag "select text", ctrl+drag "select by drawing boxes", alt+drag "select whole paragraphs", alt "clear selection", right-click "tag". | `screens/reader/readerKeys.test.ts` (3) |
| 10 | "Include handled" draws as a white box with near-invisible text on Today | The inbox strip's buttons and select use the app's colours (`.inbox-strip button`). Every button in the strip was a browser default before. | `InboxStrip.test.tsx` "draws its buttons in the app's colours…" |
| 11 | Deferred to Phases 2–5 (tabs, Ingest screen, Start/Today/Feedback/Graph jargon, T5, T6) | **left**, as planned | — |

### #6 in detail

**The kind of PDF.** A PDF is a "PDF" until its text says what it is (`kind_noun("pdf")` and `source_kind_noun`):
- a **paper** when it is short and opens with an Abstract;
- a **book** when it is longer than 10 pages;
- otherwise it stays a **PDF**.

So the hand-over says "Getting this PDF ready", a scan or a two-page handout is a "PDF", and a long text is a "book" once read.

**Details name the kind:**
- "Build questions for the whole paper at once";
- "Undo this paper's questions".

**The privacy choice.** It now says what it does, everywhere the learner sees it:
- the details' choice: "Never send this paper to an AI";
- once chosen: "This paper is never sent to an AI, so no questions are written for it.";
- the status lines: "Never sent to an AI — no questions are written for it", and "Never sent to an AI — this recording can't be read here";
- the backend messages;
- Add's option: "Never send this to an AI";
- the connect sheet: "You can choose never to send a book to an AI when you add it."

**The first-build action** reads "Build them as you read". It starts where the learner reads and keeps ahead of them, beside details' "…the whole book at once".

**The link to Ingest** reads "See how it was added and built". It opens today's Ingest screen, which Phase 2 turns into Under the hood → Imports & builds.

### Fail-first and test updates

**Fail-first, frontend.** All new frontend tests were run against the sources at `f74797d6`, with the test files at the fix. Twelve failed (the `#2`–`#8` Reader tests, the R3 expectation, the BookCard and AddSource wording tests, the ConnectAI close, the inbox strip). `pdfPages.test.ts` and `readerKeys.test.ts` failed at import (no helpers yet). The two ConnectAI guards passed both before and after.

**Fail-first, backend.** The four `test_6_*` tests were run against the Python sources at `f74797d6`, and all four failed: `'book' == 'PDF'` twice, the "Build them" label, and the kept-local message.

**Earlier tests changed on purpose.**
- **Three Reader tests read after the page settles.** "the section break's quick check opens the check…", "keeps the learner's answer beside the intended answer…" and "after the learner compares…" each resumed at a section's last page and scrolled 140 ms later. That was still inside the Reader's 1.5 s settling window, so the scroll was not reading. They passed only because the leftover check was offered on arrival, which is the defect #2 reports. They now wait for the page to settle (`SETTLED_MS`) before the learner reads.
- **The R3 geometry test** now expects the resume at the top of the view (`"start"`).

## Deviations this pass adds

- **D21.** A place to read on from (a resume, a section from Contents) is put at the top of the view; a cited or annotated passage is still centred. This refines round 2's R6 and F4 ("centred once its page is drawn"), which still hold for the passage itself.
- **D22.** In the original PDF, a section's check is offered at the section's last page, reached by the learner's own reading in this visit. A resume or a jump never offers it, whether the check is new or left from an earlier visit. This answers half of Q-N for the leftover case.
- **D23.** The learner-facing name of the per-book privacy choice (spec §6.4, Q4: "Keep this book on this computer") is now "Never send this book to an AI". The behaviour, the `keep_local` column and the API are unchanged.
- **D24.** A PDF's kind is "PDF" until its text says "book" (more than 10 pages) or "paper". This extends D18.
- **D25.** "No questions for this book yet · Build them as you read"; details offer "the whole book at once".
- **D26.** "Open in Imports & builds" → "See how it was added and built", until Phase 2's Under the hood exists.
- **D27.** The keep-ahead request is durable (migration 187). The Reader's ask is written with its progress, and the worker's retries survive a restart.

## Gate

Run in the worktree with `TMPDIR=<worktree>/fixtures-local/tmp`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` · `uv pip install pypdfium2` | ok (the sync removes pypdfium2; the install puts it back) |
| `uv run lint-imports --no-cache` | 14 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8804 passed**, 0 failed, 0 skipped (5 min 6 s; 8804 collected). That is 8792 before plus this pass's 12 new tests: 8 for F8 and F9, and 4 for #6. Run at `23ec08aea`. |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **94 passed**, 8710 deselected (serial, 1 min 33 s) |
| `npm install` · `npm run typecheck` · `npm test` · `npm run frontend:build` | up to date (281 packages) · clean · **53 files, 349 tests passed** (329 before; 18 new tests, plus 2 more deny-list lines) · built |
| `cargo check` | not run: nothing under `src-tauri` changed |
| DB reference scripts | `db_generate_reference.py` regenerated at `23ec08aea` (schema head 187, 300 table notes, 685 configuration leaves); `db_validate_reference.py`: no errors; `validate_vault.py`: passed (1073 notes) |

## Safety

- No paid call, no real provider and no network. No key, credential or `.env` file was read.
- The owner's working vaults in the main checkout were never opened.
- The worktree's tracked `fixtures/linear_algebra`, `fixtures/probability` and `fixtures/arxiv_v2` were not touched. No manual run was needed this pass, so no backup copy was made. `git status fixtures/` shows only the head fixture's planned rename (`migration_head_186` → `migration_head_187`).
- No server was started, and no tailscale command was run.

## Left, and why

- **Item 1 (T8).** A scanned PDF still needs a terminal command (`uv sync --extra pdf`) to become readable. Q-O asks how to word it until Q-L (an in-app install) exists, and both are owner questions.
- **Item 11.** The ten tabs and the Ingest screen (Phase 2); Start, Today and session jargon (Phase 3); grading and feedback, including T6 (Phase 4); the Graph and T5 (Phase 5). The re-test confirmed these unchanged, as planned.
- **Not changed: "You're near the section break" in the guide.** It still comes at 70 % of a section. It is a hint, and only the offered check waits for the last page now.

## Open questions for the owner

- **Q-U.** Is "Never send this book to an AI" the right name for the per-book privacy choice (D23), or should the spec's "Keep this book on this computer" come back with a few words saying what it means?
- **Q-V.** A PDF is a "PDF" up to 10 pages (D24). Is 10 the right line between a handout and a book?
- **Q-W (merge).** Migrations 186 (`add_book_state`) and 187 (`reading_request_revision`) were both built on this branch, after main's own 186. The merge renumbers both after main's head. It also rebuilds `migration_head_*` from main's head plus both, and updates the names in the 11 tests, 2 scripts and the reference. The placeholder algorithm tag `mvp-0.15` relabels as Q-T says.
- Still open from earlier rounds: Q-M, Q-N (keyboard reading; D22 settles the leftover-check half), Q-O, Q-P, Q-Q and Q-S.

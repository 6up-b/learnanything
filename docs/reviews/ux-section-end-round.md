# The section-end round: eight small things around a section's end (ledger UX-70, UX-78 to UX-84)

Branch `ux/section-end-round`, from main `ef403d953d` (latest tag `mvp-0.63`: a section's end finishes it). Two live
walks on the real app on 2026-11-21 (sectionend-1: a first-year student reads a one-section web chapter to its end in a
few minutes, closes a quick check on the way, waits for questions during the book's first build and gives up;
sectionend-2: the same persona, patient, who waited six minutes for questions and answered four) confirmed that reading
to the end finishes the section, and found the things below around it.

Nothing is scheduled, generated, graded or scored differently, and what finishes a section is unchanged. No prompt,
algorithm tag, config key, kill switch or migration. Two optional fields are added to existing replies (compatible
additions for the phone host's allowlist): `completionCause` on each row of `reader.get_progress` and of
`reader.mark_section_progress`'s `progress`, and `allRead` on a book's reading facts (`statusLine.questions`). No
identity pin, golden or structure ratchet moved (below).

## Judgment calls to read first

1. **The section's position reaches its end by the end event, not by completion.** `currentSectionRead` is 1 once the
   section's last passage was shown during the learner's own movement: the end this visit reported (`reachedEnds`),
   or a finish the backend stored as `reached_end` (so after a restart too). A section finished by "I've read this
   section" half-way keeps its real position (tested: 1/3), and a restore at the end moves nothing. The saved counts
   are not changed (raising them would change what reads `spans_seen`). The whole-book bar is a position: the end while
   the book's last passage is in view (scrolling back up lowers it again).
2. **The page-only PDF:** a page that is a section's last passage counts as shown once part of it is in view (the end
   event's existing rule), so the section's bar reads 100 % there. `ReaderScreen.followsLearner.test.tsx` #7 asserted
   50 % at a scroll where the end had already been reported (its view is one page tall, so page 2 never counts without
   page 3 in view); it now asserts 100 %.
3. **A closed check is kept by the Reader, not fetched.** The card hands the guide what it showed when the learner
   pressed "Done with this check"; the guide shows it folded at the top, where the check was, for the rest of the
   Reader visit (keyed by reading and section). Nothing is sent again (one `answered` record, as before). Leaving the
   Reader or opening another book drops the folded copy: the guide plan carries only `proposed` checks
   (`reader/reader_guidance.py:556`), and showing a stored answer after reopening would need a new read of
   `reader_authored_questions.response_md`, which this round does not add. The answer itself stays stored as before.
   The phone's dose question gets the same, under the section, until another section opens.
4. **"Open the book" replaces "Continue reading"** beside a wait for a book read to its end: "Continue reading" beside
   "You’ve read all of “B”." contradicted it. Same handler (opens the book).
5. **"Leave LearnLoop open meanwhile" is the true sentence, not "you can close it and come back".** A running job's
   lease is failed as `interrupted` when the app next opens (`content/pipeline/runner.py:17`-`:19`,
   `recover_stale_leases` `:777`-`:842`); its queued siblings are blocked behind it and nothing tries it again on its
   own: the book's line becomes "Questions for … need another try" with Retry (`content/pipeline/add_source.py:3095`),
   and Today's "Couldn't get “B” ready for questions. Try again, …". Only work that was queued and never started
   resumes on the next start (`content/pipeline/jobs.py:4611`, `resume_book_preparation`). So the block says "closing it
   stops the work until you try again". On the phone, whose app closing stops nothing, it names the desktop.
6. **The guard against the vanished control is a time, once.** When the end finishes the section while "I've read this
   section" is on screen, the first press on the way on (Back to Today, Read the next section) within
   `END_PRESS_GUARD_MS` = 1 s does nothing and clears the guard; a section found finished on opening, or finished by
   the learner's press, has no guard. On the desktop the line "Section finished: you read to the end." takes the
   control's slot; on the phone it is the existing finished line's text (above the foot), and a dose offer tap clears
   the guard (the dose banner's top is its text, where the control was).
7. **UX-84 says the truth instead of hiding the announcement.** Nothing failed or was withheld in the walk: the check
   was written at 60 % and is offered at 70 %. The guide now says "A quick check on this section is ready. It comes up
   as you read on, near the end of the section." for an authored check that is written and not yet shown. Owner-placed
   checks, which "writing a quick check" never announces, keep their lines.
8. **UX-83: the details control appears only when it adds something.** On a first build its one line repeated the
   first-time sentence; it is left out where that sentence is on screen, and the control with it. With a retry, reused
   parts, a further pass, drafted topics or a measured time the details still say those.

## The eight, with causes and fixes

### UX-78: 99 % at the true end

Walk: at the last passage, and after "Section finished", the guide said "99 % through this section" and the header
"99 %". Cause: `screens/reader/useReadingProgress.ts:59` (`READING_MARKER = 0.7`); the section bar is the marker's count
(`:881` `seenHere = at + 1`, `:728`), the header the marker's block (`:854`). Fix: `currentSectionRead` returns 1 for a
section in `reachedEnds` or `endedSections`; `readingProgress` is 1 while the last passage is in view (`lastInView`,
set in `updateReadingPosition` with the end event's criterion; reset in page mode and on a new book).

| Place | Before | After |
|---|---|---|
| Desktop guide, the section bar, at the bottom of the chapter | "98% through this section" / "99% through this section" | "100% through this section" |
| Desktop header bar | "99%" (aria "99% through the book") | "100%" |
| After reopening a section finished by its end | "99% through this section" | "100% through this section" |
| A section finished by "I've read this section" half-way | its position | unchanged: its position |
| Phone | no percentage | unchanged |

### UX-79: closing a quick check hid the answer and the comparison

Cause: `screens/reader/GuideRail.tsx:193`-`:196`, `:208`-`:211` (the close dismisses the section), the offer rule then
settles it (`useReadingProgress.ts:782`) and the card, which alone held the answer, unmounts. Phone:
`read/ReaderScreen.tsx:474` (`onDone` drops the dose). Fix: `onComplete(kept)` from both desktop cards; the guide keeps a
`ClosedCheck` and renders `ClosedCheckRecord` (a `<details>`) above the guide where the check was. Phone: `DoseOffer`'s
`onDone(kept)` and a `<details data-testid="closed-check">` under the section's foot.

| Place | Before | After |
|---|---|---|
| Desktop guide after "Done with this check" (authored check) | nothing | "Your answer to the quick check on “Symmetric matrices”" (folded); opened: the question, "your answer" with the learner's words, "the intended answer · compare, don’t grade" with it |
| Desktop guide after "Done with this check" (placed question) | nothing | the same summary; opened: the question and the answer (it shows no intended answer) |
| After skip / keep reading | nothing | nothing |
| Phone, after the dose question's "Done with this check" | nothing | "Your answer to the quick check on “1 Vectors”" (folded); opened: the question, "› your answer", the words, "◇ the intended answer · compare, don't grade", the answer |

### UX-70: "Keep reading meanwhile." with nothing left to read

Cause: `app/todayCause.ts:589`-`:612` (`causeWait`) always ended with "Keep reading meanwhile."; the book's facts had
no "all read". Fix: `add_source._note_all_read` (called in `reading_questions`'s return line, so the function stays at
200 lines) sets `all_read` when every unit of the reading has a finished progress row; `todayCause` carries `allRead`
(and `phone` on the phone) on `on_the_way` and `section_writing`; `causeWait` says the all-read block (UX-82).

The guide never said "Keep reading meanwhile." itself; its keep-reading lines at the book's end are UX-80's.

| State (Today, desktop and phone) | Before | After |
|---|---|---|
| Book being got ready, every section finished, measured time | "Getting “B” ready for questions · usually about 4 min. Your questions from what you read will be written as soon as “B” is ready. Keep reading meanwhile." | "… · usually about 4 min. You’ve read all of “B”. Your questions from what you read will be written as soon as “B” is ready. They'll be on Today. You don’t need to do anything for them. Leave LearnLoop open meanwhile: closing it stops the work until you try again." |
| Its questions being written | "Writing questions from what you read in “B”… Keep reading meanwhile." | "Writing questions from what you read in “B”… You’ve read all of “B”. They'll be on Today. You don’t need to do anything for them. Leave LearnLoop open meanwhile: closing it stops the work until you try again." |
| Waiting its turn behind another book | "“B” is waiting its turn behind “A” · LearnLoop gets one book ready at a time. Keep reading meanwhile." | "… LearnLoop gets one book ready at a time. You’ve read all of “B”. Leave LearnLoop open meanwhile: closing it stops the work until you try again." |
| The action beside these | "Continue reading" | "Open the book" |
| Phone, the keep-open sentence | — | "Leave LearnLoop open on your desktop meanwhile: closing it there stops the work until you try again." |
| Anything left to read | unchanged | unchanged |

### UX-80: "keep going" at the book's end

Cause: `screens/reader/GuideRail.tsx:287` ("near the section break. Keep going…" at ≥ 70 %), `:391`-`:395` (the green
card), `:261`, `:268`, with no notion of the book's last section. Fix: `lastSection` (the current section has no next).

| Guide line, book's last section | Before | After |
|---|---|---|
| ≥ 70 %, not finished | "You’re near the section break. Keep going, or revisit a useful passage." | "You’re near the end of “B”." ("You’re near the end." without a title) |
| Check answered, still open | "You answered this section's quick check: compare below, then keep reading." | "You answered this section's quick check: compare below." |
| Placed after-section check open | "You’re near the section break. Take a quick check or keep reading." | "A quick check on this section is ready, just below." |
| Finished, check answered | "✓ quick check complete — keep going." | (no card; the section card says "Section finished…" and offers Back to Today) |
| Mid-book (all four) | — | unchanged (tested) |

### UX-81: the control vanished under the pointer

Cause: `GuideRail.tsx:525`-`:567` (`SectionDone` swaps the button for the status and the way on when the backend's
answer has the section finished; nothing told an end from a press; the way on moved up into the button's place); phone
`read/ReaderScreen.tsx:470`, `:477`-`:483`. Fix: `_progress_payload` carries `completion_cause`
(`src/learnloop_sidecar/handlers/reader.py`); the hook keeps `endedSections` from the save's answer and the progress
read; `SectionDone` shows `SECTION_ENDED_LINE` in the control's slot (`data-section-control`), what the finish started
under it, and guards the way on (judgment 6). Phone: the finished line reads `SECTION_ENDED_LINE` for a section the
host stored as `reached_end`; `goOn` has the same guard.

| Place | Before | After |
|---|---|---|
| Desktop, end reached, book not ready | the button replaced by "◐ Your questions from this section will be written as soon as “B” is ready. They'll be on Today." and "Back to Today" moving up | "Section finished: you read to the end." in the button's place, the waiting line under it, "Back to Today" (a press within 1 s does nothing) |
| Desktop, end reached, writing | "◐ Writing questions from this section. They'll be on Today." | "Section finished: you read to the end." and that line |
| Desktop, end reached, nothing started | "Section finished" | "Section finished: you read to the end." |
| Desktop, reopened later | "Section finished" | "Section finished: you read to the end." (no guard) |
| Desktop, finished by the press | unchanged | unchanged |
| Phone, end reached | "Section finished" | "Section finished: you read to the end." (first tap on Read the next section / Back to Today within 1 s does nothing) |

### UX-82: the first build's wait, after reading everything

Cause: `app/waitDetail.ts:117` and `app/todayCause.ts:597` said three separate things (details, the indicator's later
line, "Keep reading meanwhile."), with no state for a book read to its end. Fix: the all-read block (UX-70's table),
with "The first time, this can take several minutes." (`WAITING_COPY.firstBuildLater`, reused) inside it and the
indicator's later line dropped then; the details drop "no time is given" (UX-83).

| Place | Before | After |
|---|---|---|
| Desktop, first build, all read | indicator "Getting “B” ready for questions · 1 of 2 steps done"; after 5 s "The first time, this can take several minutes."; lines "Planning questions · part 1 of 1", "Started 4 minutes ago · still writing"; details ▸ "No book has finished getting ready in this library yet, so no time is given."; "Your questions from what you read will be written as soon as “B” is ready. Keep reading meanwhile." Continue reading | indicator unchanged, no later line; the two lines unchanged; no details control; "You’ve read all of “B”. Your questions from what you read will be written as soon as “B” is ready. They'll be on Today. You don’t need to do anything for them. The first time, this can take several minutes. Leave LearnLoop open meanwhile: closing it stops the work until you try again." Open the book |
| Phone, the same | "Getting “B” ready for questions · 1 of 2 steps done. Your questions … is ready. Keep reading meanwhile." and details ▸ "No book has finished …" | "Getting “B” ready for questions · 1 of 2 steps done. You’ve read all of “B”. Your questions … is ready. They'll be on Today. You don’t need to do anything for them. The first time, this can take several minutes. Leave LearnLoop open on your desktop meanwhile: closing it there stops the work until you try again."; no details control |

### UX-83: "details" added nothing

Cause: `app/waitDetail.ts:167` pushed the measured-time line always, so a first build's details held only "No book has
finished getting ready in this library yet, so no time is given.", which `screens/today/TodayPlace.tsx:1346` showed
as a control whenever lines existed, beside the indicator's "The first time, this can take several minutes." Fix:
`waitDetailOf(cause, "desktop" | "phone")` marks `firstTimeSaid` (desktop first build; phone only in the all-read block)
and `buildWaitWords` leaves that line out then; the control renders only with lines.

| Place | Before | After |
|---|---|---|
| Desktop, first build, planning, no retry | details ▸ "No book has finished getting ready in this library yet, so no time is given." | no details control |
| Desktop, first build with a retry / reused parts / a further pass / drafted topics | details with those lines and the no-time line | details with those lines |
| A measured build | details "Earlier builds in this library took about N minutes … (from K builds)." | unchanged |
| Phone, not all read | details ▸ "No book has finished …" (the phone shows no first-time line) | unchanged |
| Writing, unmeasured, no retry | no details control | unchanged |

### UX-84: "writing a quick check" vanished

Cause: `useReadingProgress.ts:949` asks for the check at 60 %, the poll drops "writing" once it is in the plan
(`:1026`), and `checkOffer.ts:92`/`:130` shows an after-section check from 70 %; between the two the guide's chain
(`GuideRail.tsx:269`-`:288`) fell to "Keep reading at your own pace." Fix: `CHECK_COMES_UP` for an authored check that
is written, not open, not dismissed, answered or finished.

| Guide line | Before | After |
|---|---|---|
| 60 %, being written | "◐ writing a quick check for this section…" | unchanged |
| written, 60-70 % | "Keep reading at your own pace." | "A quick check on this section is ready. It comes up as you read on, near the end of the section." |
| 70 %, shown | "A quick check on this section is ready, just below." | unchanged |

## Tests and fail-first

Written before the fixes and run against the base code (the backend's against the base handler and store; the apps'
against the base modules):

| Test | On the base |
|---|---|
| `tests/test_section_end.py::test_the_reply_and_the_progress_read_say_how_the_section_was_finished[mvp-0.62, mvp-0.63]` | 2 failed (`KeyError: 'completionCause'`) |
| `tests/test_section_done_before_build.py::test_the_fact_says_when_every_section_of_the_book_is_finished` | failed (`KeyError: 'allRead'`) |
| `todayCause.test.ts` "a book read to its end …" (6) | 5 failed, the control (something left to read) passed |
| `sectionEndRound.test.tsx` (11 at the time) | 8 failed; the mid-book controls, "closed without an answer" and "found finished on opening" passed |
| `sectionEndRound.test.tsx` UX-84 test (added with item 8) | failed with the new branch switched off |
| `seenViewport.test.tsx` the two UX-78 tests | 2 failed (0.978, not 1) |
| `sectionEnd.test.tsx` "a section finished by its end is known as such …" | failed |
| `TodayPlace.test.tsx` "the live walk sectionend-1 …" | failed |
| phone `sectionEnd.test.tsx` UX-79, UX-81 (and the two edited below) | 4 failed |
| phone `Today.plan.test.tsx` "one calm block …" | failed |

Assertions changed, each because the behaviour deliberately changes: `ReaderScreen.followsLearner.test.tsx` #7 (50 % →
100 %, judgment 2); `TodayPlace.test.tsx` "a book being got ready …" (the details' no-time line → no details control,
UX-83); `tests/test_reader_seen_passages.py::test_the_passages_survive_a_restart_…` (the key set of a progress row
gains `completionCause`; it still pins that no passages are given); phone `sectionEnd.test.tsx` "reading to the end
finishes the section …" ("Section finished" → "Section finished: you read to the end.") and "'Done with this check'
closes the quick check" (the question's text gone → the check's group gone and its folded record closed). Its helper's
fake host now stores a cause per finished section.

## Commands

Every Python run through the scratch wrapper, `-n 1`, in a 3 GB scope, one at a time, from a script that refuses an
empty target list; vitest with four workers; npm with the shared npm cache.

| Command | Result |
|---|---|
| The two new backend tests (fail-first, then after the fix) | 3 failed; then 3 passed |
| `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`, `test_public_tip_guards`, `test_ingest_queue_store`, `test_reader_seen_passages` | 429 passed, 1 failed (the progress row's key set, edited above); after: `test_reader_seen_passages`, `test_identity_pins`, `test_structure_ratchets`, `test_section_end`, `test_section_done_before_build` 417 passed |
| `scripts/affected_tests.py --files add_source.py handlers/reader.py`: 673 files, so the brief's name filter (section_end, reader, section_done, quick_check, today, first_questions, build_wait, add_source, mobile_v4, mobile_allowlist) united with the affected files naming `reader.get_progress`, `reading_questions`, `completion_cause`, `all_read` or `source_status_line`: 163 files, five chunks, `-m "not arc_close"` | 1012 passed; 508 passed; 739 passed; 539 passed, 3 skipped; 12 failed (UX-85, a test-isolation bug, fixed), then 43 passed |
| `tests/test_test_layout.py` alone; `tests/test_architecture.py` alone | 3 passed; 18 passed |
| `ruff check`; `lint-imports --no-cache`; `scripts/check_gate_partition.py` | All checks passed; 45 kept, 0 broken; collected 32813: landing 32747 + arc_close 66 |
| Desktop `tsc --noEmit`; `vitest run --maxWorkers=4`; `npm run frontend:build` | clean; 328 files, 3656 tests passed; built |
| Phone `tsc --noEmit`; `vitest run --maxWorkers=4`; `npm run build` | clean; 44 files, 468 tests passed; built |
| `desktop_validate.py` | no count moved (one new file, a test); it reports the changed modules' notes stale (the landing regenerates) |

Identity pins: none moved (`--write` not run; the test passed). Structure ratchets: no count rose
(`add_source.reading_questions` stays at 200 lines: the new fact is set by `_note_all_read`, called in its return line).

## What a live-route walk must check

On the real desktop window and the phone, with the sectionend persona (a one-section web chapter, first build):

1. Read to the very bottom by scrolling: the guide's bar and the header read 100 % (not 99 %) at the last passage, and
   after "Section finished: you read to the end." appears in the place "I've read this section" had; scrolling back up
   a screen lowers the header, not the guide's bar. Reopen the book: 100 % and "Section finished: you read to the end.".
2. Click where "I've read this section" was as the end arrives: nothing navigates; Back to Today works on the next
   press. A section finished by the button half-way keeps its position and says "Section finished".
3. Answer the quick check, compare, press "Done with this check": a folded "Your answer to the quick check on …" stays
   at the top of the guide; one press shows the answer and the intended answer. Leave the Reader and come back: gone
   (by design, judgment 3).
4. At the book's last section: no "section break", "keep going" or "keep reading" line; mid-book they read as before.
5. Today after finishing the whole chapter during its first build: one block (You’ve read all of …; They'll be on Today;
   You don’t need to do anything for them; The first time…; Leave LearnLoop open…), no later line under the indicator,
   no "details" control, "Open the book". The same on the phone (the desktop-named sentence). Then while questions are
   written: the writing variant, no "Keep reading meanwhile.".
6. Close the app mid-build and reopen: Today offers Try again ("Couldn't get … ready"), confirming the keep-open
   sentence; Try again resumes.
7. The authored check: between "writing a quick check" and 70 %, "A quick check on this section is ready. It comes up as
   you read on, near the end of the section."; at 70 % the check shows.
8. A later build (a measured time) still shows details with its measured line.

## What was not verified

- No app, browser, WebKitGTK window or phone was run (the rules): layout, the guard's feel, `<details>` in WebKitGTK and
  the real scroll geometry are tested on jsdom with faked rectangles only.
- The owner's vaults; the landing gate, the whole suite, durability and the arc-close gate.
- That a click lands on the ended line rather than on the moved way on depends on real layout; the guard covers the
  case where it lands on the way on.
- The vault references are not regenerated (the landing does).

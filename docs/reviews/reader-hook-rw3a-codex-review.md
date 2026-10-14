# Reader hooks and RW3a: Codex review and fixes

**Branch:** `reader/rw3a` (worktree `learnanything-merge4`, base main `4cf54a295`). **Reviewed:** `4cf54a295..e848974eb` by Codex (job `20261013-233603-70iBbU`), seven findings, six reproduced by the reviewer with the real hooks or placement functions. **Stage record:** `docs/reviews/reader-hook-rw3a.md`.

**Fix step:** every finding reproduced here first as a failing test, committed on its own (`8b4309ca2`) and checked to fail on `e848974eb` for the finding's own reason; then fixed (`c6aae6fc4`). All seven are fixed, none rejected. **Paid calls:** none ($0.00); every model call in the tests is a house fake, no vault was opened, no key read. **Migration:** none; **schema** and **config** unchanged (no `DEFAULTS_SNAPSHOT_BY_ALGORITHM` change, no reference regeneration); `src-tauri` unchanged.

## Findings

| id | severity | title | verdict | commit | test |
|---|---|---|---|---|---|
| F1 | High | Keyboard navigation records unread passages as read | fixed | `c6aae6fc4` | `ReaderScreen.marginMarksReview.test.tsx` "F1: Alt+↓ to a mark already drawn is a placement…"; `readerHooks.parity.test.tsx` "a placement without a jump resets the learner's movement" |
| F2 | Medium | Margin marks retain stale diagnoses after the Guide refreshes | fixed | `c6aae6fc4` | `ReaderScreen.marginMarksReview.test.tsx` "F2: a diagnosis that lands while the book is open reaches the mark's popover, as it reaches the rail" (the real `guidePlan` module and its diagnosis refresh, not mocked) |
| F3 | Medium | Late cue responses navigate away from a different book | fixed | `c6aae6fc4` | `ReaderScreen.marginMarksReview.test.tsx` "F3: a check me answered after the learner opened another book is dropped" and "F3: a plan re-read for the book the learner left never replaces the open book's plan" |
| F4 | Medium | Unrelated actions permanently remove "not relevant" undo | fixed | `c6aae6fc4` | `ReaderScreen.marginMarksReview.test.tsx` "F4: not relevant keeps its undo through the density and another mark set aside, until the learner leaves the book" |
| F5 | Medium | Landscape PDFs violate the one-mark-per-screenful rule | fixed | `c6aae6fc4` | `cues.test.ts` "consecutive landscape pages are closer than a letter-page model says" and "mixed page sizes add up page by page"; `PdfReaderPane.marks.test.tsx` "the pane reports each page's own size before any page is drawn…" |
| F6 | Medium | Impression telemetry counts marks the learner never sees | fixed | `c6aae6fc4` | `ReaderScreen.marginMarks.test.tsx` "a mark counts once per visit when it comes into view, never because it was placed…" (replaces the old expectation) and "a mark the learner never scrolled to is never counted shown" |
| F7 | Medium | "Open" never shows the learner's cited answer | fixed | `c6aae6fc4` | `tests/test_reader_cues.py::test_open_carries_the_cited_attempts_answer_in_the_learners_words`, `::test_a_long_answer_is_clipped_and_an_error_without_an_attempt_has_none`, the split test's new assertion; `ReaderScreen.marginMarks.test.tsx` "Enter opens the popover; open shows…" (the learner's voice) |

### F1 (High): moving to a mark is a placement on every path

**Reproduced.** On the real screen, after ordinary reading had moved the reading marker to the section's second passage (a seen count of 2 saved), Alt+↓ twice reached the far mark, which was already drawn. `focusMark` called `focus()` with no jump. The scroll that focus causes in the webview (simulated: jsdom does not scroll on focus) moved the reading position with `readingMoved` still true. The section's seen count was then saved as **5**. The test failed with `expected 5 to be 2`.

**Fixed.** `focusMark` makes every move a placement:
- On the text view and the original PDF, it always goes through the Reader's `jumpToSpan`. That jump resets the learner's movement, settles for 1.5 s and centres the passage. The mark then takes focus with `preventScroll`, so no second scroll follows. This covers marks already drawn and marks on pages not yet drawn.
- On a transcript, the mark is focused in place, so the video is not moved, after the new `useReadingProgress.notePlacement()`. That is the same placement guard as a jump, without the jump.

The test asserts that no count above 2 is ever saved and that `reader.author_section_question` is never called.

### F2: the margin's content follows the newest plan

**Reproduced** without mocking the transition. The test file uses the real `screens/reader/guidePlan` module, and only `api.readerGuidePlan` is faked: first pending, then diagnosed. After the Reader's own 4 s refresh, the rail's revealed passages named the statement. The open popover still said "LearnLoop's model is still reading that answer".

**Fixed.** Placement now stores only the ids of the drawn and suppressed marks, and their equality compares ids and reasons. `placement` resolves each id against the newest plan's cues on every render. A cue's content therefore changes without moving any mark, and a cue the plan withdraws disappears at once. The test also checks that a resize keeps the popover current.

### F3: answers that arrive after the learner left are dropped

**Reproduced.** Two cases failed on the real screen:
- A check me answered after the learner opened book B still called the shell's `onCheckMe`, with book B's card.
- A "not relevant" re-read of book A's plan, answered after book B opened, replaced B's plan: the rail showed A's sections.

**Fixed.**
- `useReaderCues` binds each request to a visit generation. A layout effect bumps it when the extraction changes and on unmount. Check me, not relevant (its receipt, re-read and undo) and preference changes drop a stale answer, including its error message.
- Check me now hands the shell its origin (source and extraction). `ReaderScreen` attaches the card only when it is that source's card and that source is still open.
- `reloadGuidePlan` compares against the source open now (`openExtractionRef`, set on each render), not against the id it captured, and never replaces another extraction's plan.

### F4: each "not relevant" keeps its undo until the learner leaves the book

**Reproduced.** Setting a mark aside and then changing the density from the Guide's footer removed the only receipt. The withheld cue then had no way back.

**Fixed.**
- The footer now holds a list of receipts. Each mark set aside has its own receipt, keyed by its cue and naming its topic ("Marked not relevant. · Densities"), with its own *undo*. It lasts until the learner leaves the source, and undoing it removes only that receipt.
- Preference receipts (fewer marks, marks off for the book or everywhere) are still one at a time, the latest. The footer's density and "turn back on" controls replace only that receipt, because they are themselves the way back for a preference.

The test sets aside two marks across a density change, undoes the first, and checks that opening another book clears the rest.

### F5: the original's spacing reads each page's own size

**Reproduced** by the pure model. In `cues.ts`, `pdfPageTops` and `pdfPassageTop(tops, page, bboxTop)` did not exist (the old `pdfPassageTop` assumed letter pages). The new tests:
- **Landscape pages.** At 600 px, two consecutive landscape-letter pages put the same box about 478 px apart, so in a 600 px reading area only the higher-ranked mark is drawn.
- **Mixed sizes** (letter, landscape, A4, and a page after a "pages left out" line) add up page by page, each page at its own scale.

**Fixed.**
- **Where the sizes come from.** `PdfReaderPane` reads every shown page's size from pdf.js (`getViewport({ scale: 1 })`) once the document loads, for books with block geometry. It reads them independently of drawing, and reports `onPageLayout({ widthPx, pages })`: the size of each shown page, and whether a "pages left out" line sits above it.
- **How the spacing is computed.** `useReaderCues` places marks on the original from that layout, with cumulative offsets, the pane's 14 px gap and a 28 px left-out line. Until the sizes are read, no mark on the original has a place.
- **Why it stays stable.** An undrawn page's placeholder now takes its own size rather than a letter shape. The layout the spacing assumes is therefore the layout on screen, and nothing moves as pages are drawn.
- **The Reader** resets the layout when it leaves a source.

### F6: a mark counts as shown when the learner could see it

**Reproduced.** The screen test with a stand-in `IntersectionObserver` logged both marks on opening, although only one was in view. A second test, where no mark ever comes into view, logged two impressions.

**Fixed.**
- `MarginMark` observes its own button and reports `onSeen` once at least half of it is in the reading area. The observer is the webview's intersection with the viewport, clipped by the scrolling column, a transcript's list or the original's pane, so a mark below the fold or on a page not reached is never seen.
- Hover, focus or a click also count, since a mark interacted with was seen. That is also the only signal where `IntersectionObserver` is absent, which is the case only in jsdom.
- `useReaderCues.noteSeen` logs `cue_shown` once per visit.

Placement alone logs nothing, so the report's "marks shown", its rates and the proactive load count what the learner saw.

### F7: "open" shows the cited attempt in the learner's words

**Reproduced** by the backend tests (`KeyError: 'answer'`) and by the screen test (no learner voice in the popover).

**Fixed.**
- **Backend.** `reader_cues._earlier_work` adds `answer`: the cited attempt's `learner_answer_md`, verbatim but trimmed, clipped at 600 characters (`MAX_ANSWER_CHARS`) with line breaks kept, and null without an attempt or text.
- **Frontend.** The popover's *open* shows it under the learner's voice (`LearnerVoice`, "your answer"), between the question and the model's reading, which keeps its own voice. The answer never enters the note, the "because" line or the label.

This follows spec §6.1 ("the cited attempt, its diagnosis"). It adds no new data class: the guide plan RPC is desktop only and already carries the attempt's question.

## The review's other claims, re-checked after the fixes

- **"A mark brought into view by focus is a placement, not reading"** now holds on every path (F1).
- **"The margin and the rail agree"** now also holds when content changes without a new cue (F2).
- **"Undo until the learner leaves the source"** now holds for every mark set aside (F4).
- **"At most one mark per screenful"** holds on the original for landscape and mixed pages. The model is the pane's real layout, except the left-out line's height, which is a constant within a few pixels (F5).
- **"The report measures marks shown"** now means marks seen (F6).
- **Not touched:** spec conformance rows the review found in order (the single check-offer rule, the backend 30 s sweep, the display-only path, no new route or spend, desktop-only RPCs, deferred RW3b/RW6). Decision 1 of the stage record (check me on the practice screen until RW2a) is unchanged.

## Corrections to the stage record

`docs/reviews/reader-hook-rw3a.md` decisions 4 and 5 described the behaviour this review changed. Impressions are now marks in view (F6), not marks placed. The original's spacing now reads each page's own size (F5), not a letter-page model. Friction note 5 (a tap re-reads the whole plan) stands; F3's guard makes a late re-read harmless.

## Fail-first evidence (`8b4309ca2` against `e848974eb`)

- **Frontend:** 11 tests fail, 25 pass, in the four touched files. In the new screen file the failures are:
  - F1: `expected 5 to be 2`;
  - F2: the model voice is absent after the refresh, though the rail updated;
  - F3: `onCheckMe` was called once, and book B's section label disappeared under A's plan;
  - F4: the receipt was gone after the density change.

  Elsewhere:
  - F5: `pdfPageTops is not a function`, and `onPageLayout` was never called;
  - F6: `['cue_b1', 'cue_b4']` was logged where only `['cue_b1']` was in view, and two impressions were logged with nothing in view;
  - F7: no `[data-voice='learner']`.
- **Backend:** the three F7 assertions fail with `KeyError: 'answer'`.
- **After the fixes:** all pass, along with every existing test (the old impression expectation was replaced, as the review asked).

## Gate

Run in the worktree with `TMPDIR` set to `fixtures-local/tmp`, against `c6aae6fc4`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 17 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10,680 passed**, 0 failed, 0 skipped (48 warnings), 922 s |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 10,581 deselected (1 warning), 191 s |
| `npm install`, `npm run typecheck` | ok, clean |
| `npm test` (vitest) | 81 files, 568 tests passed |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check` | not run: nothing under `src-tauri` changed in this step |
| DB / config references | not regenerated: schema and config unchanged |

## Not done

- **No real-UI look.** The usability harness is wired to another worktree, and showing a mark needs a vault copy with a live misunderstanding on a cited passage. The screen tests drive the real `ReaderScreen` with jsdom layout and visibility stand-ins.
- **F5's left-out line** is a constant (28 px) rather than a measurement. The pages themselves are exact.

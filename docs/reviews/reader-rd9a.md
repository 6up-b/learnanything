# Reader workbench v2, RD9a: lesson windows

Stage RD9a of `docs/specs/spec_reader_workbench_v2.md` (§11.1, §10, §12.5's Teacher lesson row, §16's RD9a row, §21.1's
lesson rows). Branch `reader/rd9a-lesson-windows`, cut from RD6b part 2's tip. One new RPC (`lesson.list`, desktop
only, no model call, nothing written) and its Rust passthrough; no migration, algorithm tag, prompt change, config key,
kill switch, grading path or persisted-meaning change; nothing on the phone. §11.2–§11.5 (notebooks, the bridge, cells)
are RD9b's: this stage leaves the seam only.

## 1. What landed

| Scope item | Where |
|---|---|
| `LessonView` extracted: the lesson screen's content, with a `frame` (`screen`, the full-screen lesson as it always was; `window`, the same lesson in a desk's window or stack tab). `LessonScreen` renders it in the screen frame and re-exports what it exported; no Teacher test changed | `F:screens/LessonView.tsx`, `F:screens/LessonScreen.tsx` |
| The window lifecycle (§3.6): a paused window opens or reads its lesson only once it is live, checks back on a question being prepared only while live, and registers its activity listeners through the window's hub (a paused window is never "in the foreground"). Outside the desks nothing is paused and the hub is the page's, so the screen behaves as before | `LessonView.tsx` |
| Lessons as stack tabs (§11.1): a stack's items are its pads and its lessons; a lesson's tab reads "Teacher lesson · <topic>" and "made <date> from your <what>"; its paper has the head ("◇ Teacher lesson · yours to keep, like your other pads"), the mode buttons and the lesson | `F:screens/desks/lesson/LessonPaper.tsx`, `lesson/model.ts`; `F:screens/desks/pads/PadStackWindow.tsx` (lesson items beside pads: their tab, their paper, their additions) |
| Lessons as windows: a window whose content is `{kind: "lesson"}` (what `open_window` makes) shows the lesson as a stack of one | `F:screens/desks/DeskShell.tsx` (`paneBody`, the window's title) |
| Every lesson entry opens a window on the current desk: the Reader's "Teach me this" in a source window or on a pad line, `openContent` with a lesson (the menus' Teach me), the app's entries while the desks are its current place (the inspector's Teach me, Something else's lesson; through a `lessons.request` prop, each ask once by its seq), and the path view's row. A stored lesson is focused where it already is, else added to the desk's stack (`add_to_stack`) and scrolled to; a new one opens as a tab in the desk's stack at once, and is stored there when its opening turn returns, keeping the window that opened it (its React key and entry: no remount, no second read, never a second open) | `DeskShell.tsx` (`openLesson`, `placeLesson`), `F:screens/desks/lesson/host.ts` (`LessonDesk`), `F:app/App.tsx` (`openLessonEntry`) |
| Review replay: a finished lesson reopened is read with `lesson.view` alone and replays its recorded turns and checks; no control that starts a turn is shown (no reply, answer, Stop or "Start a fresh lesson" unless the window hands that to the desk's stack) | `LessonView.tsx`, `LessonPaper.tsx`; `tests/test_reader_rd9a_lesson_windows.py` pins `lesson.view` on a finished lesson as no model call and no row written |
| The additions pad (§11.1 "your additions"): the learner's notes under a lesson are a `lesson_additions` pad naming the lesson, created by the first note and written through RD4's pad ops (`create_pad`, `insert_block` via `pad.apply`); its blocks render with every pad insert, edit and menu; shown under the review when it has notes, and on their own under "your additions" (the lesson folded, not unmounted) | `PadStackWindow.tsx` (`writeUnderLesson`, `renderLesson`), `LessonPaper.tsx` |
| The path view's Teacher lesson row (§12.5): under an LO, its newest lesson (one `lesson.list` per path opening), "review it" or "continue it"; a click closes the path and opens the lesson's window | `F:screens/desks/lesson/PathLessonRow.tsx`, `goal/PathView.tsx` and `goal/GoalLayer.tsx` (a `lessonRow` render prop) |
| `lesson.list`: lesson summaries (title, goal, opened, closed and why, its LOs, where it came from, its additions pad), by id, by LO or all; empty with lessons off, as Today's open lessons are | `src/learnloop/teacher/summaries.py`, `src/learnloop_sidecar/handlers/lesson.py`, `db/stores/pad_reads.lesson_additions_pads`; `src-tauri` passthrough; `api/client.ts`, `api/dto.ts` (`LessonSummaryDto`) |
| The notebook seam (RD9b): a view whose `medium` is `notebook` shows the host's `notebookFrame(lessonId, view)` instead of the lesson; no such view is sent yet, and every other lesson shows itself | `LessonPaper.tsx`, `LessonViewDto.medium`, `DeskShell`'s `lessons.notebookFrame` |
| Styles: the lesson pad's head, modes, mode line and frame in the reference's faces, sizes and colours; inside a window LessonView's colour variables are the paper's, the interface text JetBrains Mono and the lesson's reading text Literata; display math fitted (`FitMath`) | `F:styles/lesson.css` |
| Fixture, harness and reference: a finished lesson on softmax with its additions pad and a fake lesson service (`?lesson=1`), the harness's `lesson` run, the visual reference's `rd9` stage | `F:fixtures/desks/lessons.ts`, `fakeCore.ts`, `harness.tsx`; `scripts/desk_harness/run.py`, `visual_reference.py` |

## 2. Judgment calls (please confirm)

1. **One new RPC instead of widening `lesson.view`.** A tab needs a lesson's date and origin before (or without)
   reading its whole view, and the path view needs lessons per LO; `lesson.list` serves both and the additions pad's id.
   `made_from` is read from the lesson's own record, later facts first: origin `router` is "today's suggestion", an open
   turn naming a probe episode is "your check", a goal JSON with `typed` is "your question", entry `reader_selection` is
   "your selection", anything else "your topic".
2. **An open lesson's first mode says "lesson", not "review".** The spec's "review" is "as you left them"; an open
   lesson is still being taken, so the button and its line say so ("the lesson so far · reply, answer its checks, or
   stop it here"). A finished one says "review" with the spec's line.
3. **"your additions" folds the lesson** (kept mounted, so a reply being written or a turn in flight survives) and
   shows the notes with "write under this lesson"; under review the notes show beneath the lesson when there are any.
4. **A lesson reached through `openContent` lands in the stack** (or is focused where it is), so the menus' Teach me,
   which opens `{kind: "lesson"}`, satisfies "a lesson opened from a selection lands in the desk's stack". A window
   that already has lesson content (made by a raw `open_window`) is shown as a stack of one. A control to move a lesson
   out to its own slot is not built.
5. **Focus.** Opening focuses the desk's stack; when the opening turn returns a minute later, the lesson is stored
   without moving the focus.
6. **An opening exists only on this screen until its turn returns** (nothing is stored before the lesson exists). One
   that failed outright offers "let it go" once its step is over; one that failed with the teacher unavailable keeps
   the screen's "Try again".
7. **Check hand-offs and Today's suggestion cards keep the lesson screen**: they live on Today (Practice, the feedback
   card), where the desks are not the current place. Every App entry goes through `openLessonEntry`, which opens a
   window only while the desks are current. The desks' companion has no "learn it with the tutor" yet, so there is
   nothing to route there.
8. **Learner interjection cards keep the screen's mono face** inside a window (the lesson's own design); the teacher's
   words, checks, results and recap are Literata.
9. **"Start a fresh lesson"** (ruling R1) in a window opens the new lesson in the stack through the desk, not in place.
10. **The private capture tool gained `--add-regions`**, which measures newly named regions into an existing capture
    and keeps its screenshot (the `#tabs=distance,pad=3` capture holds the served notebook; recapturing without it
    would have lost that).

## 3. The reference compared (measured)

`visual_reference.py --stage rd9` on `#tabs=distance,pad=3`, both viewports: every lesson region (`lesson_head`,
`lesson_head_glyph`, `lesson_head_faint`, `lesson_mode_on`, `lesson_mode`, `lesson_mode_line`, `lesson_frame` colours
and borders) and the open tab's title and meta (faces, sizes, weight 500, amber ink) match exactly. What still differs
is the pad stack RD4 drew, shared with every pad and owned by the parity round: the paper's and tab's border colour
(`#4a4740` here, `#2a2825` in the reference), the stack window head's colours, and the paper's width (519 px against
542 px at design, from the stack's margins; `lesson_frame` follows it). The frame's content is the notebook in the
reference and the lesson itself here (RD9b).

## 4. Tests

- **No behaviour change to the lesson screen:** the ten files that render it (`LessonScreen*.test.tsx`,
  `App.lessonSuggestion`, `App.offerPage`, `App.brokenControls2`, `App.queueRevision`, `checkHandoff`,
  `LessonSuggestionCard`) pass unchanged, 93 tests, before and after the extraction.
- vitest: `lesson/model.test.ts` (7), `lesson/lessonWindows.test.tsx` (10: review, the tab, paused, the probe poll,
  an opening stored without a remount, let it go, the additions pad, notes beneath, the notebook seam, the path row),
  `lesson/deskLessons.test.tsx` (3: the selection's Teach me lands in the stack, a stored lesson asked for, a lesson
  window). Fail-first: with the pause guards and the opening's React key removed, the paused, probe-poll and
  opening tests fail (3 of 10); restored, all pass. The whole vitest suite passes (370 files).
- sidecar: `tests/test_reader_rd9a_lesson_windows.py` (registration desktop only and `extra="forbid"`, `made_from`,
  `lesson.list` with its additions pad and filters and no write, empty with lessons off, review replay with no model
  call and no write); `tests/test_mobile_allowlist.py` pins `lesson.list`.
- harness: the `lesson` run (12 checks: a paused stack reads nothing, review with no turn, the tab's words, modes,
  notes, faces, display math unclipped, a note to the additions pad through `pad.apply`, an opening from a selection
  stored in the stack, no second read); every run passes (131).

## 5. Not built here, and what waits

- The notebook frame, the bridge, cells (RD9b); redo and extend (RD9c).
- Moving a lesson out of a stack to its own slot, and taking one out of a stack.
- The menus' Teach me verb is the menus worker's (not on this branch); it works through `openContent`/`open_window`
  with `{kind: "lesson"}` as described in §2.4.

## 6. Bugs

None found in the product. `DeskShell.test.tsx` reports six unhandled rejections (its `passageUnionRange` fake answers
without `spans`); they are present at this branch's base and do not come from this stage.

## 7. Not verified

- The desktop app itself (only the harness's real webview and jsdom); a live lesson turn (fakes only).
- The vault's generated desktop notes are not regenerated (the validator's counts are updated; its coverage rows wait
  for the regeneration after landing).

## Fix round: the RD9a adversarial review (Codex Astra, 2026-11-23)

Same branch as RD10's fix round. The review had 7 majors and 1 minor. Each was checked against the code here and
held. Seven are fixed, each with a fail-first test and a ledger row, RD9a-1 upward. One is stopped: it bears on what
an answer counts as. No migration, algorithm tag, prompt or config key.

| Finding | Ledger | What changed | Fail-first test |
|---|---|---|---|
| A desk lesson request replayed after a remount or a vault switch | RD9a-1 | The request carries its vault. DeskShell opens it only in that vault and reports it taken (`lessons.onConsumed`). App forgets it then, and on any vault change | `lesson/deskLessons.test.tsx` |
| Close and undo during an opening sent a second opening turn | RD9a-2 | `LessonDesk.shareOpening` owns the opening's turn: sent once, shared by later views, and its identity settled with no view mounted | `lesson/lessonWindows.test.tsx` ("an opening closed and brought back…") |
| A TE2 quick question is not isolated in a window | RD9a-3 | **Interim, the owner's option (a)**, until RD7's administration guard exists. The quick question is asked on the full lesson screen, never in a desk window. A window's `lesson.view` and `lesson.turn` say `frame: "window"`; the sidecar then neither serves nor shows a ready question (`status: "waiting"`, no first-serve claim; `probes.held_serving`) and refuses `answer_probe` (`probe_on_lesson_screen`). The tab says a quick question is waiting and opens the lesson screen (App's `openProbeScreen`); when that screen closes, the tab reads the lesson again. How an answer is recorded is unchanged. Options (b), a desk-wide guard, and (c), recording such answers as assisted (a tag), stay listed for when RD7 is decided | `test_reader_rd9a_fix.py::test_a_quick_question_is_never_served_or_answered_in_a_desk_window`, `lesson/lessonWindows.test.tsx` ("a lesson's quick question in a desk window…") |
| Two additions pads per lesson | RD9a-4 | The sidecar refuses a second pad per lesson inside the batch's transaction. `lesson.list` names the oldest and lists all of them. The desk creates nothing until the summary lands, takes the stored pad, and shows older duplicates' notes | `test_reader_rd9a_fix.py`, `lesson/lessonWindows.test.tsx` (2) |
| A failed step's recovery reads ignored the lifecycle and unmounting | RD9a-5 | Recovery reads wait for a mounted, live view (`readWhenLive`) | `lesson/lessonWindows.test.tsx` |
| Folded or scrolled-away papers kept polling | RD9a-6 | Each paper's effective lifecycle (`PausedPart` in `lifecycle.tsx`) pauses it while folded or out of view | `lesson/lessonWindows.test.tsx` |
| A TE2 review omitted the question and appended its answer after the close | RD9a-7 | One feed in recorded order. The served question (as its item states it) appears once answered, or in a review | `test_reader_rd9a_fix.py`, `lesson/lessonWindows.test.tsx` |
| A finished lesson's review wrote activity | RD9a-8 | A tracker starts only once the lesson was shown open. A lesson that closes while shown keeps its final flush | `lesson/lessonWindows.test.tsx` |

Judgment calls:
- The review shows a quick question's text from its item as stored now, not regenerated. A revision of the item since would show the new text: the served turn keeps the revision's identity, but not its words.
- Older duplicate additions pads are shown under the lesson, not merged into one pad.
- The desk tells the learner "reading your notes under this lesson" and creates nothing while the summary is unknown.

Assertions changed: for RD9a-3, a window's `lesson.view` input now carries `frame: "window"`. This changes three
`toHaveBeenCalledWith` assertions in `lessonWindows.test.tsx` and the desk harness's lesson-run check on
`lesson.view`'s input. Returning from the probe's lesson screen shows no "lesson kept" notice (the learner is back at
the tab).

Shared files touched (small, additive):
- `App.tsx`: the request's vault and consumption; `openProbeScreen` and its return to the tab.
- `DeskShell.tsx`: honouring them.
- `lifecycle.tsx`: `PausedPart`.
- `PadStackWindow.tsx`: additions known, older pads.
- `pads/blocks.py`: the one-pad rule.
- `db/stores/pad_reads.py`: every pad listed.
- `teacher/service.py`: the feed order.

Checked:
- rd9 visual comparison: unchanged (4 findings before and after, geometry).
- Desk harness, every run: 152 passed.
- The whole vitest suite passes.

# UX fix stage 3: Today explains itself

Stage 3 of the UX journey audit's fix stages (`ux-journey-audit.md` §10, row 3): proposal P1, findings F1, F7 and F9, the follow-ups of UX-4 and UX-6, and two lists stage 1 left (`ux-fix-stage-1.md`: the other refusals in the error channel, and the "Keep going" line). Branch `ux/stage3-today-explains`, from stage 1's branch at `1c99bc8281`, one commit per item. Judged against `ux-journey-audit-criteria.md`. Desktop, simple shell; frontend only, no sidecar change.

| Item | Commit | What |
|---|---|---|
| 1 | `912585b585` | P1: an empty Today names its cause and carries its one action |
| 2 | `b786b3ada5` | "Practise for this goal" with nothing ready says why, and offers the step |
| 6 | `e35b7c9173` | "Keep going" that comes back closed says the right thing for each way |
| 3 | `c9f0f2229e` | F9: each duration on Today says what it measures |
| 4 | `07377e1827` | F7: the Library's OK action says it asks for the OK |
| 5 | `1247f952f0` | Refusals that explain are said in place, not as red errors |

Item 6 was built before item 3 because it reuses item 1's cause line. The deny-list addition (all of this stage's fixed words) and this record are the last commit.

## Item 1 (P1, F1): an empty Today names its cause

**What the learner saw** (student-1 #40-45, `student-1-0045-empty-today-red-toasts.png`; beginner-1 #78-82; retainer-1 #61-63). "Nothing planned for today." with Keep going and Something new, which led nowhere. The cause ("Questions wait for your OK · Review") was only on a Library card.

**What the code did.** `TodayPlace.tsx` rendered "Nothing planned for today." for a closed plan with nothing in it (`planWasEmpty`) and for an open plan with no rows, and nothing else. The causes were already in the desktop's hands: each book card's `statusLine` (the sidecar's `source_status_line`, `add_source.py`), the links still being added (`pending`), the AI connection (`get_ai_connection`: `needs`, `whatLeaves`), and today's list (`get_today_queue`).

**What they see now.** Under "Nothing planned for today.", one status line (`role="status"`, never red) with its one action beside it. The new module `app/todayCause.ts` (`todayCause`, `causeSentence`, `causeActionLabel`) picks the state, and `TodayPlace` renders it with `CauseLine`. Where the action sends passages to a model, a "what's sent ▸" link shows the connection's own `whatLeaves` sentence in place.

| State | The data that tells it | The line | The action |
|---|---|---|---|
| Today's list still has questions | `get_today_queue` has items (read first: then there is something to practise, whatever the books say) | Today's list still has questions, if you'd like some. | **Open today's list** (the full list, as `l`) |
| Questions waiting for the OK | a readable card's action is `connect_ai` and the connection says `needs: "consent"` (without a connection, the sidecar's label "Review") | Questions for “Symmetric Matrices and Variance” are waiting for your OK. (with several: “…” and 2 more are waiting for your OK.) | **Give your OK** (opens the same Connect-an-AI sheet as the card) · **what's sent ▸** |
| No AI connected | a card's action is `connect_ai` and the connection says `needs: "connect"` | LearnLoop needs an AI connected to write questions for “…”. | **Connect** (the same sheet) |
| Getting questions ready failed | a card's line has tone `problem` and a `retry` action labelled "Retry" (question writing stopped) or "Try again" (getting the book ready failed); a pending link the same way | Couldn't get questions ready for “…”. | **Try again** (`source_action` retry on that card, or on the link's batch; a retry the sidecar wants confirmed goes to the Library) · **what's sent ▸** |
| Something else on a card | any other card line with an action, or a problem with none (a cost to approve, a budget used, changes to look at, an upload's OK, a re-read to finish, too much to write at once) | “…” needs a look in your Library. | **Open Library** (Library → Books) |
| Questions being written | a card's line has tone `working` (getting it ready, chapters found, writing questions, questions in about N min), or a link still being added | Questions for “…” are on their way. Keep reading meanwhile. | **Continue reading** (opens the book, as the card's Continue; none for a link with no card yet) |
| Only past exams | every card has the reader off | LearnLoop writes questions from what you read. Add a book, paper or lecture to read. | **+ Add** |
| Everything read has its questions | no card asks for anything, the list is empty, and there is something to read | Everything you've read has its questions. Reading on brings more. | **Continue reading** (the first book ready to read) |
| A plan finished for today | the plan is closed and the day had something in it | (under "Done for today · …") Nothing else is needed today. | nothing needed (Keep going stays where it was) |

When several cards differ, the order is: waiting for the OK, no AI, failed, needs a look, on their way. While a book's questions are on their way, Today reads the library and the list again every 5 s (the shelf does every 3 s), so the line does not outlive its state. The same line shows for an open plan with no rows and nothing being chosen, waited on or held.

**No sidecar field.** Every state above is told from data Today has or already fetched. The one place the plan itself could have helped is a closed plan's reason: a stop the router chose with work left and a day with nothing left to plan look the same in the plan DTO (`stopReason` is free text: the lane-quota chooser's "nothing more worth doing today fits", or the objective chooser's `why`, sometimes the model's rationale; the stop receipt's `feasible_ids` is not in the view). Today's list answers the learner's question (is there more I can do now?) without it, so the one allowed field was not added.

**Props.** `TodayPlace` gains `aiConnection`, `onConnectAi`, `onOpenBook` and `onOpenLibrary`; `App.tsx` passes the shell's connection, `setConnectOpen(true)`, `openBook` and Library → Books. Without a callback the action is not shown.

**Tests** (`apps/learnloop-tauri/src/screens/today/TodayPlace.test.tsx`, "UX fix stage 3, P1: an empty or finished Today names its cause and carries its one action"):
- `questions waiting for the OK: the cause, Give your OK (the one-time OK), and what's sent on demand`
- `several books waiting: the first by name and how many more; with no AI connected, Connect`
- `questions being written: on their way, keep reading, and Continue reading opens the book`
- `question writing failed: Couldn't get questions ready, Try again retries on the card, with what's sent beside it`
- `a card asking for something else (a cost to approve): the book needs a look, and Open Library goes there`
- `everything read has its questions: nothing more to add, and reading on brings more`
- `today's list still has questions: says so (never 'nothing to practise') and opens the list`
- `an open plan with no rows says its cause too`
- `a finished plan: nothing else is needed`
- `every cause line is in plain words`

**Fail-first.** All ten failed before the change: nine with `Unable to find an element by: [data-testid="today-cause"]`, the finished plan with `Unable to find an element by: [data-testid="today-finished"]`.

## Item 2: "Practise for this goal" with nothing ready says why

**What the learner saw** (beginner-1 #80-120, student-1 #42). Stage 1 made "Nothing for this goal is ready to practise yet." a neutral line on the card. It still said nothing about why.

**What the code did.** `TodayPlace.tsx` `practiseGoal` reads today's list and opens its first item on the goal's frontier; with none it set `goalNothingReady`, and the line was a constant.

**What they see now** (`goal-nothing-ready`, `role="status"`):

| State | The data that tells it | The line | The action |
|---|---|---|---|
| The goal has questions of its own, none on today's list | `GoalDto.practicableItemCount > 0` | Nothing for this goal is up today. Its questions come back on the days they're due. | none |
| The goal has no questions yet | `practicableItemCount` 0 or unknown, and a book cause (item 1, with the list counted as empty) | Nothing for this goal is ready to practise yet: questions for “…” are waiting for your OK. (and each cause of item 1 the same way, e.g. "…: everything you've read has its questions. Reading on brings more.") | the cause's own action (Give your OK · what's sent ▸, Connect, Try again · what's sent ▸, Open Library, Continue reading, + Add) |
| The library not read yet | no cards | Nothing for this goal is ready to practise yet. | none |

A goal does not say which books it reads from (`GoalDto` has a concept and facet scope, no source), so the line names the book it is about rather than claiming the book is the goal's.

**Tests** (`TodayPlace.test.tsx`, "UX fix stage 3: Practise for this goal with nothing ready says why, and offers the step"):
- `a goal with no questions yet: the same cause as an empty Today, for the goal, with its action`
- `a goal whose books' questions are all written: reading on brings more`
- changed on purpose: stage 1's `UX-6: Practise for this goal with nothing ready says so on the card, as a notice, never an error` now expects the goal-with-questions line (its fixture goal has 12 questions).

**Fail-first.** All three failed: `expected 'Nothing for this goal is ready to pra…' to contain 'Nothing for this goal is ready to pra…'` (the old line, without its cause) and `… to be 'Nothing for this goal is up today. It…'`.

## Item 3 (F9): one clock

**What the learner saw** (seasoned-1 #0, #82, #98, #110, #134, `seasoned-1-0134-two-clocks.png`). "About 25 minutes suggested today" over about six minutes of rows; "22 minutes left" that did not move across answers; "Done for today · 2 minutes." beside "5 minutes · 6 questions".

**What the code did.** Each number was right for what it measured; the words made them read as one clock. Nothing computed changes; the labels do (`app/todayPlan.ts` `planSentence`, `doneLine`; `components/SessionFinishHud.tsx` `sessionLengthLine`).

| Where | What it measures (code) | Old label | New label |
|---|---|---|---|
| Minute chips | the plan's minutes for today (`rememberedMinutes` among `minuteChoices`); a tap calls `set_plan_minutes` | "10m 15m 25m 40m 60m" (group "minutes today") | unchanged; still hidden once the plan is done |
| Plan sentence, not begun | `minutesBudget`, an upper bound on the blocks chosen | "25 minutes today: finish §5.4…, then…" | "Up to 25 minutes today. Planned so far: finish §5.4…, then…" |
| Same, router objective (RO4) | `minutesBudget`, a suggestion | "About 25 minutes suggested today: …" | "About 25 minutes suggested today. Planned so far: …" |
| Plan sentence, begun | `minutesLeft` = budget − the estimated minutes of the blocks chosen so far (`records.py` `minutes_left`): it does not move while a block is answered | "About 22 minutes left today: …" | "Room for about 22 more minutes today. Next: …" |
| Same, RO4 | the same, may go negative | "About 22 minutes left of today's suggested time: …" | "Room for about 22 more minutes of today's suggested time. Next: …" |
| Same, RO4, past the suggestion | `minutesPastPlan` = chosen blocks' estimates beyond the budget | "About 6 minutes past today's suggested time: …" | "About 6 minutes planned past today's suggested time. Next: …" |
| Block rows | each block's estimate (`estMinutes`, projected `estMinutes`) | "about 3 min" | unchanged |
| why? split | each part's `displayMinutes`, the asked-for minutes | "about 13 min for keeping what you know" | unchanged |
| Re-entry | `reentry.planMinutes` (chosen plus projected, the rows' own total) | "A short catch-up today: 12 minutes of the most useful questions." | unchanged |
| Waiting | time until a hold lifts | "Nothing to do right now. Back in 9 min: …" | unchanged |
| Done | `day.actualMinutes`: each answered question's time plus each reading block's start to end (`daily_plan/view.py` `_actual_minutes`) | "Done for today · 2 minutes." | "Done for today · 2 minutes spent answering." (with reading: "… spent answering and reading.") |
| Session summary card (shown on Today after Done for today) | the session's window, `endedAt − startedAt` | "5 minutes · 6 questions" | "5 minutes this session · 6 questions" |
| Something new | the extension's new items' estimate (`preview.estMinutes`) | "about 9 min of new material today, …" | unchanged |
| Full list | each item's planned estimate | "about 4 min" | unchanged |
| Plan off | the session's minutes | "15 minutes today: starting with …" | unchanged (never beside the plan's sentence) |
| Lesson offer, lesson suggestion, Something else | each option's estimate | "(about 15 min)" | unchanged |

**The minute chips after done.** They stay hidden, as before, now pinned by a test. Once the plan is done a chip means nothing for today: a smaller value only sets later days' minutes, and a larger one reopens today's plan (`engine.set_minutes`). The audit's wish to keep them after done, to steer tomorrow's load, belongs with the forecast and *less / more* (P5, stage 7).

**SessionFinishCard** is shared with the classic shell under the simple practice feedback; only its words change.

**Tests:**
- `apps/learnloop-tauri/src/app/todayPlan.test.ts`, "UX fix stage 3, F9: each duration says what it measures": `the plan's time is its length, and the rows are what is planned so far, never the same clock`; `once begun, the minutes not yet given to a block are room, not a countdown`; `done says the time spent answering (and reading, when there was reading), not the session's length`
- `TodayPlace.test.tsx`, "UX fix stage 3 (item 3, F9): one clock on Today": `a begun plan names its room, the rows their own estimates, and the minute chips the plan's length`; `after the plan is done the minute chips are not shown: today's length means nothing then`
- changed to the new words: `todayPlan.test.ts` (three `planSentence` tests and `done says the time spent`), `TodayPlace.test.tsx` (`states the plan in minutes…`, `one book, no answers yet…`, `done: the time spent…`), `App.today.test.tsx` (T4), `SessionFinishHud.phase4.test.tsx` (two tests).

**Fail-first.** 15 tests failed, e.g. `expected 'About 22 minutes left of today's sug…' to match /^Room for about 22 more minutes of to…/`, `expected 'Done for today · 2 minutes.' to be 'Done for today · 2 minutes spent answ…'`, `Unable to find an element with the text: 26 minutes this session · 9 questions`. The chips-after-done test failed only on its done line: the chips were already hidden, so that part is a pin.

## Item 4 (F7): "Review" in the Library

**What the learner saw** (student-1 #101, beginner-1 #70-74, retainer-1 #70, `retainer-1-0070-review-opens-connect-ai.png`). "Questions wait for your OK · Review" opened "Get questions on what you read", the one-time OK. The learner expected questions.

**What the code did.** The sidecar labels the `connect_ai` action "Review" for `needs_consent` (`add_source.py` `source_status_line`); `BookCard.tsx` `StatusLine` showed the label as it came.

**What they see now.** "Questions wait for your OK · **Give your OK**" (`BookCard.tsx` `cardActionLabel`, `CONSENT_ACTION`), the same words as Today's line. It opens the same sheet. When the OK is asked and what it covers are unchanged (UX-10, the owner's ruling). "Review" on changes to look at (`open_changes`) and "Connect" with no AI keep their words.

**A correction to the brief.** There is no "after the OK" state of this control. Once the OK is given the card's line becomes "Writing questions for …" or "Questions for … come up as you read", neither with an action, so there is nothing to rename to "open them".

**Tests** (`apps/learnloop-tauri/src/components/BookCard.test.tsx`): `F7: the card's OK action says it asks for the OK, and still opens the same sheet` (failed first: `expected <button type="button" …(1)></button> to be null`, the "Review" button); `F7: other actions keep their own words (changes to look at are still Review; no AI is still Connect)` (a control: passed before and after).

## Item 5: refusals that explain, shown as sticky red errors

**What the learner saw.** Nothing in this wave's walks; these are stage 1's sweep (`ux-fix-stage-1.md`, "Other empty states found in the error channel"). In the simple shell `onError` is the red error that never expires.

**What they see now.** A status line where the learner acted (`role="status"`, quiet, never red), in plain words (`copy/refusals.ts`). In Practice it sits above the key bar, goes with the question (cleared when the item or the short check changes) and is replaced by the next refusal.

| Where | Old (`onError`, red) | New (in place) |
|---|---|---|
| Practice, ^h on a check on your own (`PracticeScreen.tsx` `revealHint`) | No hints on this one: it's a check on your own. | No hints on this one: it's a check on your own. |
| Practice, ^h during a short check | hints are disabled during a diagnostic check — answer with what you know, or stop diagnosing. | No hints during this short check. Answer with what you know, or choose “Stop diagnosing and teach me”. |
| Practice, `?` during a short check | ask-tutor is disabled during a diagnostic check — use “Stop diagnosing and teach me” instead. | Ask is paused during this short check. To be taught instead, choose “Stop diagnosing and teach me”. |
| Practice, `?` while teaching back | ask-tutor is disabled during a teach-back conversation. | Ask is paused while you teach this one back, so the tutor can't give the answer away. |
| Feedback, saving a note on a question with no subject (`FeedbackScreen.tsx` `doSaveNote`) | Cannot add note: this item has no associated subject. | in the note panel: This note can't be saved here: the question isn't filed under a subject yet. Your words are still here. (the draft stays) |
| Palette "Ask the tutor about this" while teaching back (`App.tsx`, already a neutral notice) | ask-tutor is disabled during a teach-back conversation. | Ask is paused while you teach this one back, so the tutor can't give the answer away. |
| Same, before the question's check is read (already a notice) | ask-tutor is unavailable until diagnostic safeguards are verified, and stays disabled during diagnostic checks. | Ask opens once this question has loaded, and stays paused during a short check. |

The short check's way out is quoted by its own button's words, which contain "diagnosing"; the button is not this stage's to rename. `PracticeScreen` and `FeedbackScreen` are shared with the classic shell, where the toast becomes the same in-place line. Errors that are failures (a save, a submit, a skip) stay errors.

**Stopped: the two Reader hooks.** `useReaderInquiry.ts` ("That book's passage can't be kept from here; open the book to keep it.") and `useReaderWorkbench.ts` ("This problem was started on an earlier reading of this book, so it can't be reopened on this one.") are not changed. Both are already plain words. Making them notices in place needs a surface in the Reader: the Reader has only `onError`, and the shell holds every notice while a book is open (Reader doc S11, `notices.ts`), so a notice would not show until the learner left the Reader. That is a Reader change, which this stage may not make (the Reader is stage 11). The two lines conflict, so they are left for the owner's call.

**Tests:**
- `apps/learnloop-tauri/src/screens/PracticeScreen.refusals.test.tsx` (new): `a check on your own: no hints on this one, said on the card, never an error`; `a short check: no hints, and how to be taught instead, in plain words`; `a short check: Ask is paused, and how to be taught instead`; `teaching it back: Ask is paused, and why`; `an ordinary question has no such line` (a control)
- `apps/learnloop-tauri/src/screens/FeedbackScreen.refusals.test.tsx` (new): `a question filed under no subject: the note panel says why the note can't be saved, and keeps it`
- changed to the in-place line: `PracticeScreen.hintTelemetry.test.tsx` (two refused-reveal tests), `PracticeScreen.intentCheck.test.tsx` (two), `PracticeScreen.adaptiveHints.test.tsx` (one), `PracticeScreen.ca2OneAsk.test.tsx` (Q4, one more assertion), `PracticeScreen.phase4.test.tsx` (`during a check, Ask's refusal names the control the card shows`)

**Fail-first.** The four new Practice tests, the Feedback test and the five changed refused-reveal tests failed with `Unable to find an element by: [data-testid="practice-refusal"]` (or `note-refusal`). The control passed before and after. The `phase4` test was not written first: it asserted the old `onError` call, failed after the change, and was moved to the in-place line.

## Item 6: "Keep going" that comes back closed

**What the learner saw.** Stage 1's line, "Nothing more to add today. Reading on, or adding a book, gives LearnLoop more to plan.", whenever Keep going came back with a plan that is not open.

**What the code does, checked against the engine.** `plan_keep_going` returns today's latest plan (`_current_view`). So:
- **Abandoned** cannot come back: only an earlier day's open plan is abandoned (`abandon_open_plans_before`).
- **Stopped** (the learner's Done for today) cannot come back: on a stopped plan `keep_going` builds a new extension.
- **The plan off**: the RPC answers `enabled: false` with no plan, and Today becomes the plan-off Begin. No line is the right thing there, and the code already did this; a test now pins it.
- What remains is an extension closed with nothing in it, in two ways the plan cannot tell apart (item 1's note on `stopReason`): nothing was left to plan, or the router chose to stop with work left.

**What they see now.** Where Keep going was pressed: **"Nothing more to plan today."** (`today-keep-going-nothing`, `role="status"`), then the day's cause from item 1, read from today's list first:
- a stop with questions still on the list: "Today's list still has questions, if you'd like some." with **Open today's list**;
- nothing left: the books' cause and its action, e.g. "Everything you've read has its questions. Reading on brings more." with **Continue reading**, or "Questions for “…” are waiting for your OK." with **Give your OK**.

On a finished plan, "Nothing else is needed today." gives way to them. On an empty Today the cause line is already shown, and the lead line is the in-place answer to the press.

**Tests** (`TodayPlace.test.tsx`, "UX fix stage 3 (item 6): Keep going that comes back with nothing open says the right thing for each way"):
- `nothing left to plan: says so where Keep going was pressed, and the day's cause with its action`
- `a stop with questions still on today's list: never 'nothing to add', the list is offered`
- `the plan switched off meanwhile: no 'nothing more' line and no error (Today becomes the plan-off Begin)` (passed before: a pin)
- changed on purpose: stage 1's `UX-4: Keep going with nothing to add says so, in place, and what would give LearnLoop more` now expects the new lead.

**Fail-first.** Three failed: `expected 'Nothing more to add today. Reading on…' to be 'Nothing more to plan today.'` (twice) and `Unable to find an element by: [data-testid="today-cause"]`.

## Plain words

`copy/denyList.test.tsx` gains "the stage 3 sentence: %s" over every fixed string this stage adds: each cause's line, its goal line and its action label, the goal-not-up line, the finished and Keep-going lines, "Give your OK", and the refusals. The deny-list works by rendering and by listed sentences, not by file list. Each new component test also checks its line with `findJargon`.

## Sidecar change

None. No schema, migration, algorithm tag, config key or prompt change, and nothing changes in what is sent to a model. The connection's `whatLeaves` sentence is shown, not changed.

## What was run

Every command ran through the scratch wrapper (`env -i`, isolated HOME, CODEX_HOME and config dir) inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, one at a time. No Python was changed, so no Python ran.

| Command | Result |
|---|---|
| `npm ci` (desktop) | exit 0 (esbuild's install script blocked by allowScripts; vitest and the build run) |
| `npx vitest run --maxWorkers=4 <files>` while iterating | fail-first and passing runs per item, as above |
| `npm run typecheck` | exit 0 |
| `npx vitest run --maxWorkers=4` (desktop, whole suite) | 290 files, 2955 tests passed |
| `npm run frontend:build` | exit 0 (the existing chunk-size warning only) |

## What a re-walk should check

- **Item 1, student-1 #40-45 and beginner-1 #78-82** (a book whose questions wait for the OK): Today says "Questions for “…” are waiting for your OK." with Give your OK, which opens the OK sheet, and what's sent ▸, which shows the sheet's sentence. After the OK, while questions are written: "… are on their way. Keep reading meanwhile." with Continue reading, which then changes by itself.
- **Item 1, retainer-1 #61-63** (three articles waiting): "… and 2 more are waiting for your OK."
- **Item 1 with UX-1's failure** (student-1 #101-120, beginner-1 #74-94): "Couldn't get questions ready for “…”." with Try again. Check that the retry starts and what the card says after.
- **Item 2, beginner-1 #80-120, student-1 #42**: Practise for this goal says why, never red.
- **Item 3, seasoned-1 #0, #98, #110, #134**: the sentence before Begin, after one block, and the done line beside the session card read as different quantities.
- **Item 4, student-1 #101, retainer-1 #70**: the card's action reads "Give your OK" and opens the same sheet.
- **Item 5**: ^h and `?` on a cold follow-up and during a short check (seasoned-1's practice, or a walk that reaches a short check); a note (`j`) on a question with no subject.
- **Item 6, student-1 #44 and retainer-1 #63**: Keep going shows "Nothing more to plan today." and the cause; on a finished day with questions still on the list, the list is offered.
- Layout at the walk's width: the cause line's action and what's sent sit on the line's end and wrap with it.

## Not verified here

- Nothing was walked or launched: no app, browser or dev server. Rendering, wrapping and focus are verified only in jsdom.
- `get_today_queue` is now read on an empty Today, and on a finished one after Keep going comes back with nothing. It is the read the full list makes; its cost on a large library was not measured.
- Whether today's list can hold questions the plan could not serve (a hold until later today): if so, "Today's list still has questions" is true, but opening one may wait. Not checked against a live plan.
- The cause comes from the library as the shelf shows it (`withoutAi` while no AI can write). A card the sidecar has not refreshed (between polls) can lag the plan by a few seconds.
- "Something new" on an empty Today still says "Nothing new is ready yet. Keep reading and LearnLoop will have more." beside a cause that may be the OK; its words were not in this stage.
- The phone's own clocks (`learnloop-mobile/src/today/planWords.ts`, phone-2's "8 minutes left") are unchanged: the phone is stage 4.

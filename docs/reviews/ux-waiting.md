# Waiting you can see

The owner, 2026-11-19: "we could use loading icons for when time between screens is quite long, such as going from Today to the question screen and from the question screen to the feedback screen, and perhaps when models are writing their responses." Frontend only (`apps/learnloop-tauri/src`, `apps/learnloop-mobile/src`): no sidecar or host change, no new request, no polling, nothing sent at a different time. Branch `ux/waiting-indicators` from `713a0efd08`.

| Group | Commit | What |
|---|---|---|
| A + B1 + B2, desktop | `de54dd3ed6` | the shared indicator; Today to the question; Submit to the feedback |
| A + B1 + B2, phone | `1b0f0645b9` | the phone's indicator in the desktop's words; the same two cases |
| B3, both | `ef6ba0822d` | a model writing while the learner watches |
| C, both | `0b12142db2` | the rest of the inventory in the same pattern |

This record is the last commit.

Judged against the audit's criterion 8 ("Every wait has an honest state: what's happening, roughly how long, and that the learner can keep going", `ux-journey-audit-criteria.md`, U9, H1), its H1 heuristic, and the new walks' "Waiting and feedback" sections. Those sections mostly praised the lines that existed (Ask's "looking in your books, then writing an answer", "Reading your answer…", the article's "a minute or two"), and named three gaps: no sense of how close question writing was (retainer-2, expert-1, notes-1), "loading trajectory…" for about nine seconds (seasoned-2, exam-1), and waits where only a disabled control or an ellipsis showed (workbench-1: "Starting practice took a short wait with an ellipsis").

## The inventory

Times are from the new walks' analyst logs (`fixtures-local/ux-walks/<walk>/analyst/steps.jsonl` per step, `bridge.jsonl` per sidecar call; the step timer stops at about 8.7 s, so "8.7 s" means "at least"). D is the desktop's simple shell, P the phone. "Before" is what the screen showed during the wait on `713a0efd08`.

| # | Wait | Starts at | Before | Walk time | Fails / cancels | Now |
|---|---|---|---|---|---|---|
| 1 | D Today: Begin, Continue, Enter | `TodayPlace.begin` (start session, `next_plan_item` serve) | the button says "opening…", all disabled | Begin 8.7 s+ (lesson-1 #3, #60; workbench-1 #2), 4.1 s (seasoned-2 #44); `next_plan_item` 0.2 to 15 s, 6 of 28 over 9 s | fails to the error line; no cancel | "Choosing what's next…" |
| 2 | D Today with the plan off: Begin | `TodayPlace.beginWithoutPlan` | as 1 | not walked | as 1 | "Choosing what's next…" |
| 3 | D a row of today's list | `TodayPlace.openFromList` (`plan_learner_pick`) | rows disabled | 0.7 to 1.1 s | as 1 | "Opening the question…" |
| 4 | D Practise for this goal | `TodayPlace.practiseGoal` (list read, then the pick) | nothing but disabled controls | 4.1 s (exam-1 #9) | as 1 | "Finding a question for this goal…", held across both reads |
| 5 | D Keep going on a finished day | `TodayPlace.keepGoing` (`plan_keep_going`) | disabled | 4.4 s (seasoned-2 #70); 0.4 to 2.4 s | as 1 | "Adding more to today…" |
| 6 | D Resume (a question in progress) | `QuestionInProgress` → `onOpenPractice` | opens at once | none of its own | | the question's read, 7 |
| 7 | D the question's read | `PracticeScreen` load (`get_practice_item`, probe contract) | "Loading the question…" at once, in a card | 0.04 to 0.85 s | "This question isn't available any more." | "Opening the question…" |
| 8 | D feedback's Next | `FeedbackScreen.goOn` (`next_plan_item` serve, or the queue head) | the button says "Opening…" | 2.9, 3.2 s (workbench-1 #65, #69) | the plan view says it | "Choosing what's next…" under Next |
| 9 | P the plan's Begin and Next on Today | `App` `choosing` | "Choosing what's next…" at once, no mark | 2.9 s (phone-3 #8) | error line | the shared indicator, same words |
| 10 | P Next on the feedback, under the plan | `App` `choosing` → `FeedbackScreen` | as 9 | 1.7 s (phone-3 #12, #16, #19) | as 9 | as 9 |
| 11 | P Next on today's list (plan off) | `QuestionScreen` item read | "Opening…" | not walked | error line | "Opening the question…" |
| 12 | P Resume your answer | `PlanToday` | the question again, no serve | none | | unchanged |
| 13 | D Submit | `PracticeScreen.submit` (`submit_attempt`, a model grades) | "Reading your answer…" at once, in a cyan panel | `submit_attempt` 12.8, 13.5, 22.3, 33.1 s; Submit 8.7 s+ (seasoned-2 #46, lesson-1 #8, #46, #64) | retry with the answer kept; no cancel | "Checking your answer…", after 5 s "This can take a minute."; with no AI grading "Saving your answer…" and no second line |
| 14 | D the feedback's read | `FeedbackScreen` (`get_feedback`) | a dashed outline, no words | 0.2 to 10.9 s | "Couldn't load the feedback." | "Opening your feedback…" |
| 15 | P Submit | `QuestionScreen.submit` | "Grading. You can leave; the result will be here when you come back." at once | 2.3, 2.6 s (phone-3 #10, #15) | retry, kept | "Checking your answer…", after 5 s "This can take a minute. You can leave; the result will be here when you come back." |
| 16 | P a grade the host still holds (reload, reopen, a resend it had) | `App` view `waiting` | "Your answer is being graded. The result will be here in a moment." | | | as 15 |
| 17 | P the feedback's read | `FeedbackScreen` | "Reading your feedback…" (no status role) | | error line | "Opening your feedback…" |
| 18 | D workbench submit | `Workbench` (`workbench_submit`) | "sending" (Reader posture) | 13 to 17 s | | unchanged: says it already; see "Left" |
| 19 | D the Ask panel's reply (practice, feedback; Reader-context Ask) | `AskOverlay.send` | "thinking …" (faint) under the question | `ask_tutor_question` 5.7, 9.0, 15.5 s; `reader_ask` 11 to 46 s | "Couldn't get an answer." kept | "Writing a reply…", after 5 s "This can take a minute."; still mark in the Reader context |
| 20 | D the Reader's model actions (Ask rail, library ask, …) | `ModelActionState` pending | "◐ looking in your books, then writing an answer… · cancel" | `reader_ask` 11 to 46 s | seven states, cancel | unchanged words, cancel and timing; the mark is the shared one, still (G54) |
| 21 | D a Teacher lesson's turn | `LessonScreen.run` (`lesson_turn`) | "The teacher is writing…" (faint) at once | 11.2, 31.0, 42.2, 82.9 s | "unavailable" line + Try again | "The teacher is writing…", after 5 s "This can take a minute or two." |
| 22 | D a lesson's typed goal, Find it in my books | `LessonScreen.findGoal` (`lesson_goal`) | "The teacher is writing…" (untrue: no teacher then) | not walked | error | "Looking in your books…", no second line |
| 23 | D a hint for the learner's work | `useAdaptiveHints` pending → `HintPanel` | "Writing a hint for your work…" at once, with "use the item's hint instead" | about 30 s (workbench-1) | notice line | the shared line, after 5 s "This can take up to half a minute."; the item's hint offered from the first moment |
| 24 | D the workbench's hints and Check my work | `Workbench` `HELP_COPY.writing`, `CheckColumn` | "◐ …" lines (Reader posture) | ladder hint about 30 s (workbench-1) | | unchanged; see "Left" |
| 25 | D the look into a miss | `useDiagnosisCard` pending → `FeedbackSurface` | nothing on the simple surface (classic: "analyzing your pattern…") | `diagnosis_status` 0.06 to 10.5 s | the failed line | "Looking into what happened here…" (the phone's words), no second line |
| 26 | P the Reader's Ask | `SelectionSheet.ask` (`reader.ask`) | "Thinking…" | as 20 | one plain line | "Writing a reply…", after 5 s "This can take a minute." |
| 27 | P the look into a miss | `FeedbackScreen` pending | "Looking into what happened here…" at once | | "The look into this answer didn't finish…" | same words, shared indicator |
| 28 | P "I think I was right" sent | `Contest.send` (`trigger_regrade`) | "Looking again…" at once | | error kept | same words, shared indicator |
| 29 | D app start, and every return to Today | `TodayPlace` plan read (`get_daily_plan`) | a dim "…" frame | 0.1 to 2 s, once 19.3 s | "Couldn't plan today · Try again" | "Reading today's plan…" (the phone's words) |
| 30 | D "Something else would help" | `SomethingElse.show` (`plan_something_else_options`) | "Looking at what the plan could do…" at once | 0.4 to 1.8 s | error | same words, shared indicator |
| 31 | D a goal's details | `GoalBanner` series (`get_goal_report_series`) | "loading trajectory…" (faint) | 10.7, 14.5 s uncached (seasoned-2 #14, exam-1 #3) | the error line | "Working out where this goal is heading…" |
| 32 | P app start (the plan) | `PlanToday` | "Reading today's plan…" at once | | "Today's plan couldn't be read." + Try again (unchanged, at once) | same words, shared indicator |
| 33 | P today's list with the plan off | `TodayScreen` | "Reading today's list…" (no status role) | | | "Reading today's list…", shared |
| 34 | P the Read tab | `ReadScreen` | "Reading your books…" at once | | problem line | same words, shared |
| 35 | P opening a book's section | `ReaderScreen` | "Opening the section…" at once | | problem line | same words, shared |
| 36 | P the plan's other options | `SomethingElse` | "Looking at what the plan could do…" at once | | | same words, shared |
| 37 | D figures (Ask's show me, the Reader's, a hint's) | `askFigures`, `FigureInline`, `RichFigure` | "◐ building an interactive version · keep working · it stays here in Ask" and kin | about 20 s (workbench-1) | per host | unchanged; see "Left" |
| 38 | D compare, tutor offers, library notes | `CompareMethods`, `TutorOffers`, `LibraryAnswer` | "◐ comparing…", "◐ looking in your books…", "◐ noting…" | | | unchanged; see "Left" |
| 39 | D question writing for a book | `BookCard` working line, Today's "on their way" (stage 3) | "◐ Writing questions…", "… are on their way. Keep reading meanwhile." | minutes (retainer-2, expert-1, notes-1) | failed line + Try again | unchanged; see "Left" |
| 40 | D adding a source | `AddSource` ("Adding…"), `PreparingView` ("◐ …") | as named | about 4 s to open (notes-1, seasoned-2) | | unchanged; see "Left" |
| 41 | D a project's scope in the Reader ("make it ↵") | `DeliverableScope` (`curriculum_create_deliverable`) | disabled controls; the path lines "◐ choosing a path across your books…" | 4.3 to 12.3 s; 8.7 s+ (expert-1 #13, project-1 #20) | | unchanged; see "Left" |
| 42 | D the practice exam's start and finish | `ExamScreen` | "Preparing exam…" / "Scoring exam…" at once, in a card | a few seconds (exam-1) | error | unchanged; see "Left" |
| 43 | D opening a book in the Reader | `ReaderScreen` | "◐ Opening {title}…" | about 4 s | | unchanged (says it, still) |
| 44 | D a question shown as printed | `AsPrinted` | "◐ …" pending line | `practice_as_printed` up to 19.3 s | | unchanged; see "Left" |
| 45 | D Next while a follow-up question is written | `FeedbackScreen` `nextWaiting` (FG1) | its own line | `followup_status` up to 17.5 s | | unchanged; see "Left" |
| 46 | P a page image, the full answer, the why? details | `PageImage`, `FullAnswer`, `RouterLine` | "Opening the page…", "Opening the full answer…", "Reading…" at once | | | unchanged; see "Left" |
| 47 | P Next while a follow-up question is written | `App` `followupWait` | the host's line ("Preparing a question on this…") | | | unchanged; see "Left" |
| 48 | P capture | `CaptureScreen` (stage 1, UX-9) | "Saved. Sending to your desktop…" | | | unchanged (stage 1's words and pattern) |

Ranked by how long and how often (the walks' times, and how many walks met it): Submit (13), a lesson turn (21), the Reader's and the panel's Ask (19, 20, 26), Today's Begin (1), a hint (23), a goal's details (31), the feedback's read (14), Practise for this goal and Keep going (4, 5), feedback's Next (8, 10), app start (29, 32), then the short ones. All the top ranks are covered.

**48 waits; 32 now show the shared indicator or its mark** (1 to 5, 7 to 11, 13 to 17, 19 to 23, 25 to 36; 20 only its mark), 2 have no wait of their own (6, 12), and 14 are left as they were: 12 with a reason under "Left" (18, 24, 37 to 42, 44 to 47), 43 because it already says it in the Reader, 48 because it is stage 1's line.

## The indicator

One per app: `apps/learnloop-tauri/src/components/Waiting.tsx` and `apps/learnloop-mobile/src/components/Waiting.tsx`. The words are in `apps/learnloop-tauri/src/copy/waiting.ts` (`WAITING_COPY`); the phone imports the same object through `@desktop/copy/waiting` (a pure module: `desktopImports.test.ts` passes), so a wait both apps share is said in the same words. The phone's one line of its own, `CAN_LEAVE` ("You can leave; the result will be here when you come back."), is in its `Waiting.tsx`.

- **Mount for the wait.** A caller renders `<Waiting line=… />` for exactly as long as it waits; unmounting is "done". Its timers go with it.
- **The delay.** Nothing for 350 ms (`WAIT_DELAY_MS`), so a step answered at once never flashes a line. The `role="status"` region with `aria-live="polite"` is in the page from the first moment, empty, so a screen reader announces the line when it fills.
- **The line.** A turning ◐ (a quarter turn at a time, `steps(4)`, 1.6 s a turn: the ◐ ◓ ◑ ◒ the ingest card already steps through) and one plain sentence. The mark is `aria-hidden`.
- **The second line.** Only where the wait is usually long, only after 5 s (`WAIT_LATER_MS`), and only what the walks or the code show. Desktop: dim, 11 px, indented (quieter by size, not colour: `--faint` fails contrast for small text). Phone: `.dim`, 0.8 rem.
- **Reduced motion.** `matchMedia("(prefers-reduced-motion: reduce)")` marks the mark `data-motion="still"`, and the CSS rule stops the animation under the same query (covering a preference changed while it shows).
- **The Reader posture.** The Reader and the workbench never animate (G54, `attentionBudget.test.tsx`). There `still` is passed: the Ask panel in the Reader context, and `WaitMark still` in `ModelActionState`. A new lint in `attentionBudget.test.tsx` fails if any `<Waiting` or `<WaitMark` in a Reader or workbench component lacks `still`.
- **Controls.** It holds no control and covers nothing. A control that works during the wait and belongs on its line (the hint's "use the item's hint instead") is passed as children and shows from the first moment, in the same element, so the words arriving never remount it. No control enabled before is disabled now.
- **CSS.** Desktop `styles/app.css`: `.ll-wait-mark`, `@keyframes ll-wait-turn` (the Reader CSS lint reads only `.ll-reader|qc|marquee|block-sweeping` rules). Phone `styles.css`: `.wait-mark`, `@keyframes wait-turn`, added to the "Motion: only sheets and screens" rule, which now names the waiting mark too.

## The words, per placement

| Placement | Line | Second line (after 5 s) |
|---|---|---|
| D Today Begin, Continue, Enter, plan-off Begin; D feedback's Next; P the plan's Begin and Next; P feedback's Next | Choosing what's next… | none |
| D a list row; D the question's read; P the question's read | Opening the question… | none |
| D Practise for this goal | Finding a question for this goal… | none |
| D Keep going | Adding more to today… | none |
| D and P Submit; P the grade the host still holds | Checking your answer… | D: This can take a minute. P: This can take a minute. You can leave; the result will be here when you come back. |
| D Submit with no AI grading | Saving your answer… | none |
| D and P the feedback's read | Opening your feedback… | none |
| D the Ask panel; P the Reader's Ask | Writing a reply… | This can take a minute. |
| D a lesson turn | The teacher is writing… | This can take a minute or two. |
| D a lesson's typed goal | Looking in your books… | none |
| D a hint | Writing a hint for your work… (`HINT_COPY.writing`, kept) | This can take up to half a minute. |
| D and P the look into a miss | Looking into what happened here… | none |
| P a grade looked at again | Looking again… | none |
| D and P app start / Today | Reading today's plan… | none |
| P today's list (plan off) | Reading today's list… | none |
| P the Read tab | Reading your books… | none |
| P a book's section | Opening the section… | none |
| D and P the plan's other options | Looking at what the plan could do… | none |
| D a goal's details | Working out where this goal is heading… | none |
| D the Reader's model actions | unchanged ("◐ {verb}… · cancel"), the shared mark, still | unchanged ("usually about N s" only when measured) |

"Choosing what's next…" rather than "…your next question": the plan's step can be a reading (Begin opens the Reader then), and it is the phone's and Today's own words for a block being chosen. "Checking your answer…" replaces the desktop's "Reading your answer…" and the phone's "Grading." so both say one thing. The second lines are what the walks show: grading 12.8 to 33.1 s, a reply 5.7 to 46 s, a lesson turn 11 to 83 s, a hint about 30 s. Where the walks have too few or too short times (the look into a miss, a goal's projection, the feedback's read), nothing is claimed.

**Plain words.** `copy/denyList.test.tsx` gains "the waiting line: %s" over every value of `WAITING_COPY`; the phone's `shell/a11y.test.tsx` checks `CAN_LEAVE` and every `WAITING_COPY` line with the desktop's deny-list.

## Tests

Every placement has a vitest test on fake timers (no real sleeps): absent before the delay, the exact line after it, the second line where there is one, gone when the screen or the result arrives. The phone's journey tests reach the screen on real timers, then fake only `setTimeout`/`setInterval` (fake-indexeddb's `setImmediate` stays real), hold one RPC through a wrapper over the fake host's fetch, and let the app run with zero-length timer advances.

| Test file | Tests | Placements |
|---|---|---|
| D `components/Waiting.test.tsx` | 7 | the rules: delay, polite region, hidden mark, second line, no second line, unmount, **reduced motion gives a still mark**, Reader `still`, a control from the first moment |
| D `screens/today/TodayPlace.test.tsx` › "waiting you can see: Today to the question" | 7 | 1 (with and without a session), 3, 4, 5, 29, and a fast step never shows the line |
| D `screens/PracticeScreen.waiting.test.tsx` | 3 | 7, 13, 13 with no AI grading |
| D `screens/FeedbackScreen.waiting.test.tsx` | 3 | 14, 8, 25 |
| D `components/AskOverlay.waiting.test.tsx` | 1 | 19 |
| D `screens/LessonScreen.waiting.test.tsx` | 2 | 21, 22 |
| D `screens/practice/HintPanel.waiting.test.tsx` | 2 | 23, and its offer from the first moment |
| D `screens/reader/modelActionStates.test.tsx` (+1) | 1 | 20 |
| D `screens/today/SomethingElse.test.tsx` (+1) | 1 | 30 |
| D `components/GoalBanner.waiting.test.tsx` | 1 | 31 |
| D `screens/attentionBudget.test.tsx` (+1) | 1 | the lint: every Reader use is still |
| P `components/Waiting.test.tsx` | 4 | the rules, **reduced motion gives a still mark** |
| P `practice/Waiting.journeys.test.tsx` | 5 | 9, 11, 15 (with the second line), 17, 10 |
| P `practice/Waiting.writing.test.tsx` | 3 | 26, 27, 28 |
| P `read/Waiting.places.test.tsx` | 5 | 32, 33, 36, 34, 35 |

**Fail first.** Each group's placement tests were run with that group's changed source files put back to the branch tip before the group (`git show HEAD:<file>`, restored after; the tests and the component kept): desktop group 1, 5 of the 6 Today tests failed (`Unable to find an element by: [data-testid="waiting"]`; the sixth, "a fast step never shows the line", is the control and passes on both), all 3 practice tests and both feedback tests failed the same way; phone group 2, all 5 failed (`expected null to be truthy`: no indicator); desktop group 3, 5 failed: the lesson and hint lines showed before the delay (`expected <span …> to be null`, `expected <div role="status" …> to be null`: the old lines flashed at once), the Ask and goal-lookup lines were missing, and the Reader mark was not the shared one (`expected '' to be 'll-wait-mark'`); the hint's offer guard passed on both, as meant; the desktop diagnosis test failed (`Unable to find … diagnosis-wait`); phone group 3, all 3 failed; group C, desktop 3 of 3 (Today's loading frame was `'…'`, the options line showed at once, the trajectory line was missing) and phone 5 of 5. After each change all passed.

**Existing tests changed.**
- P `practice/Recovery.test.tsx`: seven waits for `/being graded/` now wait for `/Checking your answer…/` (the graded-wait screen's new words; `findByText` waits through the delay).
- D `screens/PracticeScreen.adaptiveHandoff.test.tsx` F2: it waited for the words "Writing a hint for your work…" before pressing "work in steps", to press while the hint is pending. The words now come at 350 ms, the same moment as the first poll, which in that test delivers the hint, so the press came too late. It now waits for the pending line's region (`hint-writing`), there at once. What it checks is unchanged.

## Left, for a later stage

- **D workbench submit, hints and Check my work (18, 24).** They say it already ("◐ …", Reader posture, still). Moving them onto the shared component changes the workbench's layout; worth doing with the workbench's own pass, still.
- **D figures (37).** Already a line; the figures map's F10U1 to F10U7 (no wait estimate, no timeout, cancel that does not cancel) need a design decision first.
- **D compare, tutor offers, library notes (38).** Already "◐ …" lines in the Reader posture; could draw `WaitMark still` for one vocabulary.
- **D question writing for a book (39).** The walks' complaint is "how close": that needs a progress amount the frontend does not have (the book card's minutes estimate is the sidecar's). Design decision.
- **D adding a source (40).** Already has the preparing view; "Adding…" on the button is the only sign for the short add itself. Same pattern, low rank.
- **D a project's scope in the Reader (41).** `DeliverableScope`'s `busy` covers four different actions (make it, decide a leftover, the syllabus, the depth); the words need a choice per action. Same pattern otherwise, 4 to 12 s, still.
- **D the practice exam (42).** "Preparing exam…" / "Scoring exam…" at once in a card: the same small pattern, not reached; `ExamScreen` has no test harness yet.
- **D as printed (44).** Already a pending line; up to 19 s once; a second line needs more times.
- **D and P Next while a follow-up is written (45, 47).** FG1's own line (the phone's comes from the host's step); could draw the mark; the wait's cause is the host's.
- **P page image, full answer, why? details (46).** Short reads; same pattern, low rank.
- **A wait estimate measured per route.** `ModelActionState` already takes `usuallySeconds` "only when measured"; the shared indicator's second lines are fixed sentences from the walks. A measured p50 per route would need a sidecar field: not this stage.

## What was run

All through the scratch wrapper (empty `HOME`, `CODEX_HOME`, config dir), each in `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, one at a time.

- `npm ci` (desktop): exit 0. `npm ci` (phone): exit 0.
- Iterating: the files above with `npx vitest run --maxWorkers=4 <files>`, all passing at each commit; desktop related suites (`src/screens/FeedbackScreen src/screens/PracticeScreen src/app src/screens/today …`): 69 files, 744 tests passed; group 3's: 162 files, 1827 tests, then 43 files, 382 tests passed.
- Fail-first runs: one per group, as described under Tests (`failfirst-<group>.log` in the scratch directory).
- Final, at `0b12142db2` (the code tip; this record changes no code):
  - desktop `npx vitest run --maxWorkers=4`: Test Files 301 passed (301), Tests 3024 passed (3024).
  - desktop `npm run typecheck`: exit 0. `npm run frontend:build`: exit 0, "✓ built in 3.25s" (the usual chunk-size notice).
  - phone `npx vitest run --maxWorkers=4`: Test Files 37 passed (37), Tests 390 passed (390).
  - phone `npm run typecheck`: exit 0. `npm run build`: exit 0, "✓ built in 1.12s" (the same notice).
- Not run (no Python in this stage): `docs/learnloop-architecture-vault/_scripts/desktop_validate.py`. Its three counts were raised by the two new desktop source files (`components/Waiting.tsx`, `copy/waiting.ts`): TypeScript/TSX 330 → 332, entry-reachable build graph 319 → 321, ACTIVE 336 → 338. The new test files are not counted there. The vault references were not regenerated.

## What a walk must check

- **seasoned-2 / student-2 (desktop, Today to the question, case 1).** Press Begin: Begin says "opening…" and, if the plan takes more than a moment, "◐ Choosing what's next…" under the plan, turning. Open a row of the full list: "Opening the question…". Practise for this goal (exam-1 #9): "Finding a question for this goal…", one line through both reads, no blink.
- **lesson-1 / workbench-1 (desktop, Submit, case 2).** Submit: after a moment "◐ Checking your answer…", after five seconds "This can take a minute." beneath it; then the feedback screen's "Opening your feedback…" if its read is slow. With no AI connected: "Saving your answer…". Feedback's Next: "Choosing what's next…" under Next.
- **student-2, expert-1, project-1 (desktop Ask, case 3).** The Ask panel: "◐ Writing a reply…" under the question, then "This can take a minute."; the answer replaces it. In the Reader (AskRail) the line is unchanged and its mark does not move.
- **lesson-1 (desktop lessons).** A lesson's turn: "The teacher is writing…", then "This can take a minute or two.". Typed start, Find it in my books: "Looking in your books…".
- **workbench-1 (desktop hints).** Ctrl+H on the answer box: "Writing a hint for your work…" with "use the item's hint instead" from the first moment; the second line after five seconds.
- **exam-1 / seasoned-2 (desktop goal details).** details ▸: "Working out where this goal is heading…" in place of "loading trajectory…".
- **phone-3 (phone, all three cases).** Begin and Next: "Choosing what's next…" with the turning mark; Submit: "Checking your answer…", then "This can take a minute. You can leave; the result will be here when you come back."; the Reader's Ask: "Writing a reply…"; the Read tab and opening a book: "Reading your books…", "Opening the section…". With the phone's reduced-motion setting on, the mark does not move.
- **Any walk, reduced motion (desktop).** With the system's reduce-motion setting, every mark is still and every line still shows.

## Not verified here

- The turning mark in the real webviews (WebKitGTK for Tauri, Safari on the phone): jsdom does not run CSS animations; the tests check the `data-motion` attribute and the CSS was read, not seen.
- What a screen reader actually announces from the polite region filled after 350 ms.
- The walks' times are synthetic runs with a mix of real and faked model calls; the second lines' "a minute" and "half a minute" rest on them.
- No app, browser, server or model was run.

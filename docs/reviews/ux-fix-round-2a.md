# UX fixes: broken controls, second round (group A)

Stage 3 of the UX journey audit's second part (`ux-journey-audit-2.md` §8, row 3), group A: the defects the second wave of walks found on Today, lessons, the workbench and practice. Ledger ids UX-14, UX-16 to UX-22 and UX-27 (`refactor-bug-ledger.md`, "From the UX journey audit's walks"). Group B (the Reader and the phone: UX-15, UX-23 to UX-26) is another branch's. Branch `ux/broken-controls-2` from main `5f35fa7ac8`, one commit per defect, highest severity first. Judged against `ux-journey-audit-criteria.md`. Desktop, simple shell; frontend only, no sidecar change.

| Defect | Sev | Commit | What |
|---|---|---|---|
| UX-14 | S1 | `4b4b2e0044` | A lesson left open waits on Today, and Close says where it went |
| UX-16 | S2 | `39c95f43b6` | A plan that stopped with work left never says "Nothing else is needed today." |
| UX-17 | S2 | `ad413bf4cf` | The empty goal's sentence agrees with the goal's topics |
| UX-18 | S2 | `8a097c3015` | A quick check that can ask nothing says so where it was asked |
| UX-19 | S2 | `452c266c09` | A press that leaves a step lands on the control it pressed |
| UX-20 | S2 | `42564f8351` | The workbench's failed-hint line names this screen's controls, and goes on the next help |
| UX-21 | S2 | `0add7b1dee` | Begin whose first step is a lesson offer opens the offer |
| UX-22 | S3 | `3b9065475d` | The learner's lesson reply stays on screen while the teacher writes |
| UX-27 | S3 | `bbd9d46685` | The place tabs leave a check screen |
| words | | `69f7cab4bb` | The deny-list checks every sentence this round adds |

This record and the ledger cells are the last commit.

## UX-14 (S1): a closed lesson that could not be reached again

**What the person saw** (lesson-1 #41-55). Over the feedback of an eigenvalue miss, a lesson on dot product; the person pressed "Close" hoping it saved the place (#41-42). Close said nothing, and the default Today had no way back: the person looked in "Something else would help", the Library's Continue and Progress, and gave up.

**Cause.** `screens/LessonScreen.tsx`: Close is `onClose()`, which only unmounts the screen (App `setLessonEntry(null)`); the lesson stays open in the vault (`lessons.closed_at` empty). The way back, `ContinueLessonCard`, renders only in the classic `screens/TodayScreen.tsx`; `screens/today/TodayPlace.tsx` never read the open lessons.

**What they see now.**
- On Today (simple shell), above the plan, one line per open lesson: **Continue your lesson on Dot product** · **Continue** (resumes it, `{ kind: "resume" }`). Read with `lesson.open_lessons` (no model call; it returns lessons whenever lessons are on) when Today opens and again each time a lesson over Today closes (`TodayPlace` gains `lessonOpen`, which the shell sets while a lesson is on screen). One action, as asked: its stop stays inside the lesson ("Stop the lesson"). A failed read shows nothing.
- Close on a lesson still open: the shell's notice **Your lesson is kept. It's on Today when you want it.** (P12's wording). `LessonScreen`'s `onClose` now says whether the lesson is still open (`onClose(kept)`); Close on a lesson that has ended, or on the typed start before anything opened, says nothing.

Nothing about what a lesson is or how it is stored changes. The classic Today keeps its card.

**Tests** (fail-first: 6 failed, 2 controls passed):
- `screens/today/TodayPlace.test.tsx` › "UX-14: a lesson left open waits on Today with its one action": `an open lesson shows as 'Continue your lesson on …', and Continue resumes that lesson`, `read again when a lesson on top of Today closes, so a lesson closed with Close shows at once` (both failed: `Unable to find an element by: [data-testid="today-open-lesson"]`); `without lessons (no onStartLesson) nothing is asked` (control, passed before and after).
- `screens/LessonScreen.brokenControls2.test.tsx`: `UX-14: Close on a lesson still open says it was kept…` (failed: `expected "spy" to be called with arguments: [ true ]`), `UX-14: Close on a lesson that has ended, or before one opened, keeps nothing` (failed: `… [ false ]`).
- `app/App.brokenControls2.test.tsx`: `UX-14: a lesson closed while still open says it is kept and where; Today is told the lesson closed` (failed: `expected 'undefined' to be 'false'`, Today had no `lessonOpen`), `UX-14: closing a lesson that has ended says nothing` (control).

## UX-16 (S2): "Nothing else is needed today." with work left

**What the person saw.** seasoned-2 #59: after one answer, "Done for today. / Nothing else is needed today." while the plan had listed four blocks. returner-1 #49-51: "Catch-up done. Nothing else is needed today." beside nine questions on today's list.

**Cause.** Stage 3's finished line (`app/todayCause.ts` `PLAN_FINISHED`, shown by `TodayPlace` for every closed, non-empty plan). The walk's vault shows the first case exactly: plan `status: complete`, `stop_reason` "LearnLoop's model picked this among 5 close options. A good place to stop for today. You can keep going if you like.", one done block and a `stop_for_today` decision; the three other blocks were projections, which a closed plan's view drops (`daily_plan/view.py` `project_blocks` returns nothing once the plan is closed). A router stop with work feasible and a day with nothing left close the plan the same way, and `stopReason` is free text.

**What they see now.** Today reads what is left from data it already has: a block of the closed plan not done, or questions on today's list (`get_today_queue`, now read on a closed plan too: the read the full list and stage 3's empty-day cause make).
- Work left: **The plan stopped here, but there's more for today if you'd like it.** with **Open today's list** beside it when the list has questions; **Keep going ↵** stays below as before. Under "Done for today · …" or "Catch-up done.".
- Nothing left: **Nothing else is needed today.**, as before.
- Before the list is read: neither line, so the finished line never flashes first.

No plan field was added: the plan's rows and the list say it. The words do not say who stopped (the router, or the learner's own Done for today), so they are true of both.

**Tests** (`TodayPlace.test.tsx` › "UX-16: a plan that stopped with work left never says nothing else is needed"), fail-first: all 4 failed (three `Unable to find an element by: [data-testid="today-stopped-more"]`, one `expected <div …(3)></div> to be null`, the finished line shown before the list was read):
- `stopped with questions still on today's list: says there is more, and offers the list (seasoned-2 #59)`
- `a catch-up done beside a list still holding questions says the same (returner-1 #49-51)`
- `a block of the closed plan not done yet is work left too, whatever the list says`
- `nothing is claimed before the list is read`

**Assertion changed on purpose:** stage 3's `a finished plan: nothing else is needed` now gives an empty list (`getTodayQueue: queue([])`): its old fixture (a default list of two questions) is the defect's own case.

## UX-17 (S2): "None of the topics in your books…" beside a goal box that counted them

**What the person saw.** project-1 #24 vs #27: the Reader's goal box said "3 topics from your books" (rows "added as a new topic"); the goal's details on Today said "Nothing has been checked for this goal yet. None of the topics in your books is part of it so far: add or read a book that covers it, and its questions will count here."

**Cause.** `components/GoalBanner.tsx` `emptyGoalSentence` chose the no-topics sentence on `report.total <= 0`. The report's total counts the goal's skills in scope; the walk's goal had three topics (`facet_scope.concepts`, the three added from the goal box) and no skills or questions on them yet, so the total was 0 while the goal plainly had topics.

**What they see now** (one state per case, read from the goal the banner already has; nothing computed changes):

| State | The data | The sentence (after "Nothing has been checked for this goal yet.") |
|---|---|---|
| No topics | no concepts, no skills, total 0 | None of the topics in your books is part of it so far: add or read a book that covers it, and its questions will count here. (unchanged) |
| Topics, no questions yet | concepts or skills, and total 0 or `practicableItemCount` 0 | **This goal has 3 topics, but no questions on them yet. Once there are some, the ones you answer on your own count here.** (1: "…has 1 topic, but no questions on it yet."; topics known only through the report: "This goal's topics have no questions yet.") |
| Questions, none answered | total > 0, questions to practise | Answer its questions on your own and this report will start to fill in. (unchanged) |
| Answered elsewhere, none checked | as above with answers | "You have answered 3 questions, but none has checked this goal's topics yet." then the row's sentence for its state |

The banner's practise action is unchanged (it was already hidden with no questions).

**Tests** (`components/GoalBanner.emptyGoal.test.tsx`), fail-first: 3 failed, 1 control passed:
- `UX-17: topics in the goal but no questions on them yet: names the topics and says the questions are what is missing` (failed: the text contained "None of the topics in your books")
- `UX-17: one topic, and topics counted by the report with no questions, say it in the same words` (failed: `expected 'Nothing has been checked for this goa…' to be …`)
- `UX-17: no topics at all keeps the no-topics sentence; questions to answer keep theirs` (control)

**Assertion changed on purpose:** UX-8's `answers but nothing checked` fixture has six skills in scope and `practicableItemCount: 0`, so its sentence is now the no-questions one ("This goal's topics have no questions yet. Once there are some…"), not "This goal's questions, answered on your own, are what count here." (a goal with no questions). It failed first with the old string.

**Not changed:** the no-topics sentence is still said for student-2 #42, whose goal really had no topics (`concepts: []`: the library had none built yet); the goal cannot tell "no book" from "a book whose topics aren't built yet", so its advice to add or read a book stays generic. The goal box's own "not in your library yet" (F30, P17) is stage 4's.

## UX-18 (S2): "Check what I already know" that asked nothing

**What the person saw.** expert-1 #68: on a topic marked "✓ I know this", the check opened as "completed · 0 / 4 questions", "already assumed known". #76: on a topic not marked, "completed · 0 / 4 questions", "learning · not enough answers to skip it, so it starts as learning". It never asked.

**Why (established first).** The application's, not the harness's: `diagnosis/quick_check.py` `quick_check_progress` ends the check "completed" when nothing is undecided (#68: an already-assumed topic is decided, so it is never asked about) or `_candidate_items` finds no never-seen servable item (#76: the walk's vault has no practice items at all, `subjects/*/practice-items` is empty, question writing never produced any, UX-13/F20). `screens/CalibrationScreen.tsx` then showed the empty check with the verdict notes as if the learner had answered.

**What they see now.** The start's reply already says the check ended with nothing asked (`finished`, `answered` 0, status `completed`, each topic's verdict), so the shell says it where the check was asked, as a notice, and opens no empty check (`copy/refusals.ts` `quickCheckNothingToAsk`, used by App `startQuickCheck`):
- **Nothing to ask yet on “Construct covariance matrices”: it has no question you haven't already seen. Nothing was changed.** (several: "on “A” and 2 more topics: they have…")
- **“Covariance and variance” is already marked as known, so there's nothing to check now. Its first review is the check.** (several: "“A” and 1 more topic are already marked as known… Their first review is the check.")

From a lesson's "Check what I already know first", the lesson now stays open until a check that can ask opens (it used to close before the start). A check that asks opens as before. No sidecar reason was added: the existing reply is enough. "Nothing was changed" is the sidecar's behaviour: a check with no answers writes an assumption decision for no topic (`placement/decisions.py` `finish_quick_check_split` writes one only for an `assumed` verdict).

**Tests**, fail-first: 5 failed, 1 control passed:
- `copy/refusals.test.ts` (new) › "UX-18: a quick check that could ask nothing says why": four tests, all failed `TypeError: quickCheckNothingToAsk is not a function`.
- `app/App.brokenControls2.test.tsx`: `UX-18: a quick check with nothing to ask says so where it was asked, opens no empty check, and leaves the lesson open` (failed: `expected <div …(1)></div> to be null`, the empty check opened); `UX-18: a quick check with a question to ask opens as before (the lesson closes for it)` (control).

## UX-19 (S2): the first click in "Work in steps" ignored

**What the person saw.** workbench-1 #8, #13, #28: right after typing in step 1, a click on "check my work", "help" or "+ a step" did nothing; the printed keys worked (#14, #25, #29), and a second click worked.

**Cause (found from the step log and the code).** At #8 the walk's focus moved to the pressed button, so mousedown landed on it, yet nothing ran. `render/LiveMarkdownEditor.tsx` swaps the active block's text box for its rendered markdown on blur, which a press elsewhere causes at mousedown. The rendered paragraph is taller than the one-line box (a 13 px `<p>` with the browser's 1 em margins, about 51 px, against a 12.5 px textarea of about 39 px), so every control under the step moved down by about 13 px before the release; the walk's driver clicks a control's centre, so the release fell above the moved button and no click fired. The keys never move anything, so they worked.

**What they see now.** The editor keeps the text box while the press that took the focus is down, and renders the block after the release (and the click it brings). A leave with no press down (Tab, a key) renders at once, as before. One set of window listeners for every editor tracks the press. Nothing else in the workbench changes.

**What I could and could not reproduce in jsdom.** jsdom has no layout, so the lost click cannot be reproduced there: the test checks the mechanism (no swap while the press is down, the click then lands, the step renders after the release). The miss itself, and that the fix removes it, is for the real window (WebKitGTK; the walk ran the web build in Chrome).

**Tests** (`render/LiveMarkdownEditor.test.tsx`): `UX-19: a press elsewhere that takes the focus leaves the text box in place until it is released, then the click lands` (failed first: `expected 'DIV' to be 'TEXTAREA'`); `UX-19: leaving the box with no press down (Tab, a key) renders it at once, as before` (control).

## UX-20 (S2): help levels 1 and 2 failing with a message about controls the screen lacks

**What the person saw.** workbench-1 #16-23: levels 1 and 2 each took about 30 s and ended "I couldn't write a hint that fits here; press Hint again or use the item's hint." The workbench has no Hint button and no item hint. The line stayed beside the step through later help (#27-58).

**Cause, the words.** `hints/service.py` `NO_FITTING_HINT_MESSAGE` (written for the practice screen) is the message of a request no fitting hint could be written for (reason `contract_failed`, or `no_option` on a level-1 or 2 reply); `screens/workbench/useWorkbenchHelp.ts` showed the sidecar's message as it came, and cleared the line only on the next hint request.

**Why the requests failed (the walk's bridge log has no failed call: both jobs ended "done" with a failed result; the vault's `help_assists` rows say why).** Both are the application's. Level 1 (`approach_question`): the hint writer's output failed the writer's own check `approach_question_declares_nothing` in both rounds (its `asks_about` field was not one of approach, assumption, goal, first move; `hints/contracts.py`). Level 2 (`localize`): round 1 `localize_no_quote` (no first questionable step quoted), round 2 `rule2_past_first_questionable`, on a one-step draft that was correct ("An eigenvector v satisfies Av = lambda v, so (A - lambda I)v = 0."): pointing to the first step that doesn't hold has nothing to point at. Both live in the hint contracts or the writer's prompt, which this stage may not change: stage 8 of the second part (the ledger row keeps it open there).

**What they see now.** For those two reasons the workbench says **Couldn't write a hint at this level that fits your work. Your steps are saved: press help to try again, or choose another level.** (`helpModel.ts` `HELP_COPY.noFittingHint`); other failures keep the sidecar's words. The failed line also goes when the learner asks for help again: check my work, or opening the help ladder (Ask does not clear it).

**Tests** (`screens/workbench/brokenControls2.test.tsx`, new), fail-first: 3 failed, 1 control passed:
- `UX-20: a level no hint could be written for names this screen's controls, never a Hint button or the item's hint` and `UX-20: the same for a reply at level 1 or 2 with nothing left at that level` (both failed: `expected 'I couldn't write a hint that fits he…' to be undefined`, before `HELP_COPY.noFittingHint` existed)
- `UX-20: the failed line goes when the learner asks for help again: a check, or the help ladder` (failed: `expected { stepId: null, …(1) } to be null`)
- `UX-20: other failures keep the sidecar's own words` (control)

## UX-21 (S2): Begin did nothing visible on a lesson offer

**What the person saw.** returner-1 #21-23: the plan's first row was "A lesson you could take" (the offer card "Learn Eigenvalues and eigenvectors now?" above it); Begin turned into "Continue ↵" and the screen stayed; Continue then opened a question about 15 s later.

**Cause.** Begin started the session and the plan served the offer step (`next_plan_item` `serve: true` → `kind: "lesson_offer"`), but `app/dailyPlan.ts` `planStepAction` has no action for an offer, so App `beginSession` (no session before) and `TodayPlace.begin` (a session already open) went back to Today with nothing new on it.

**What they see now.** Begin opens the offer's own page, the one feedback's Next already opens for an offer step: **This looks like something to learn. Start a 15 minute lesson on Eigenvalues?** with Start, Not now and the alternatives, and the quiet "Something else would help". Not now goes on to the plan's next step (a question), as on that page. App gains `openPlanOffer`; `TodayPlace` gains `onLessonOffer`.

**Tests**, fail-first: 3 failed, 1 control passed:
- `TodayPlace.test.tsx` › "UX-21: Begin whose first step is a lesson offer leads to the offer": `with a session: the served offer goes to the shell, which opens its page (returner-1 #21-23)` (failed: `expected "spy" to be called with arguments: [ { kind: 'lesson_offer', …(6) } ]`); `without a session: the started session and the offer go to the shell together` (control: it already did; the shell dropped it).
- `app/App.brokenControls2.test.tsx`: `UX-21: Begin whose first step is a lesson offer opens the offer's page`, `UX-21: the same when Begin started the session` (both failed: `Unable to find an element by: [data-testid="lesson-offer-page"]`).

## UX-22 (S3): the lesson reply disappearing

**What the person saw.** lesson-1 #20-24: after Send, their reply vanished until the teacher answered (up to 83 s): "I cannot see my own words".

**Cause.** `screens/LessonScreen.tsx` `send` cleared the box and showed nothing until `lesson.turn` returned a view whose feed held the reply.

**What they see now.** The sent words show at once in the thread, in the learner's card, with **sent** under them, until the lesson shows them itself (the turn's reply, or the saved lesson read after an outage), so they appear once. A step that fails outright puts them back in the box (unless something new was typed there); one the teacher's outage kept for Try again stays shown until the saved lesson shows it. A prediction answer, which cleared its box the same way, gets the same. Nothing sent or stored changes.

**Tests** (`screens/LessonScreen.brokenControls2.test.tsx`), all 3 failed first:
- `UX-22: a sent reply stays in the thread, marked as sent, while the teacher writes, and is shown once after` (`Unable to find an element by: [data-testid="lesson-learner-sent"]`)
- `UX-22: a turn that fails puts the reply back in the box, so nothing typed is lost` (`expected '' to be 'my reply'`)
- `UX-22: with the teacher unavailable, the reply stays in the thread until the saved lesson shows it, once` (`Unable to find an element by: [data-testid="lesson-learner-sent"]`)

## UX-27 (S3): the place tabs on a check screen

**What the person saw.** expert-1 #70-72: on "Check what I already know", Progress moved its highlight and the screen stayed. returner-1 #46-47: on a short check (a practice question, "Feedback comes when this short check ends"), the Today tab did nothing; Escape left it (#49).

**Deliberate?** No. Esc leaves both screens at once with no question (`CalibrationScreen` `onExit`; the practice screen's back), and nothing in the specs holds a learner on them (the one guard the UX spec names is the practice exam's Esc question, `docs/specs/ux_learnloop_v1.md`, the "Exam mode" row, which is not this screen). The causes are side effects: App renders the calibration overlay in place of every tab's body while `calibrationSessionId` is set, and `gotoTab("today")` while on a question leaves `todayStage` at practice because the tab already was Today's.

**What they see now.** A place tab leaves the calibration screen as Esc does (`gotoTab` clears the overlay; the check is kept where it was, and starting it again finds it). The Today tab on a question, or its feedback, goes back to Today's plan, as Esc does (`gotoPlace`). No new words.

**Tests** (`app/App.brokenControls2.test.tsx`), both failed first:
- `UX-27: a place tab leaves the 'Check what I already know' screen` (`expected <div …(1)></div> to be null`)
- `UX-27: Today's tab on a question (a short check among them) goes back to Today's plan` (`expected <div data-testid="practice-pi_1"></div> to be null`)

**Left:** the practice exam's overlay pre-empts the tabs the same way; it was not walked, and its spec wants Esc to ask first, so it is not changed here.

## Plain words

`copy/denyList.test.tsx` gains "the broken controls 2 sentence: %s" over every fixed sentence this round adds (the open lesson's line, LESSON_KEPT, the stopped-with-more line, the three goal sentences, the four nothing-to-ask sentences, the workbench's no-fitting-hint line, "sent"). Each new component test also checks its line with `findJargon`.

## Sidecar change

None. No schema, migration, algorithm tag, config key or prompt change, and nothing changes in what is sent to a model or computed. `lesson.open_lessons` and `get_today_queue` were already there; Today now reads them in more states. No new non-test TypeScript file, so `desktop_validate.py`'s three counts do not move.

## What a walk must check

- **lesson-1 #41-55 (UX-14).** Open "Learn Dot product", answer a turn, press Close: the notice "Your lesson is kept. It's on Today when you want it."; Today shows "Continue your lesson on Dot product · Continue", which reopens it where it was. "Stop the lesson" then Close: the line is gone, no notice.
- **seasoned-2 #44-59 (UX-16).** Answer the first question until the plan stops: "Done for today." with "The plan stopped here, but there's more for today if you'd like it. Open today's list" and Keep going; never "Nothing else is needed today." while the list has questions. Keep going brings blocks back.
- **returner-1 #49-51 (UX-16).** After the catch-up: "Catch-up done." with the same line, not "Nothing else is needed today."
- **project-1 #24-27 (UX-17).** After "make it" adds three topics, the goal's details: "This goal has 3 topics, but no questions on them yet. Once there are some, the ones you answer on your own count here." student-2 #42 (no topics): unchanged.
- **expert-1 #64-77 (UX-18).** "✓ I know this", then "? Check what I already know": a notice "“Covariance and Variance Mastery Check” is already marked as known, so there's nothing to check now. Its first review is the check.", no check screen. On an unmarked topic with no questions: "Nothing to ask yet on “…”: it has no question you haven't already seen. Nothing was changed." On a topic with questions: the check opens and asks.
- **workbench-1 #6-29 (UX-19), in the real window.** Type in step 1, then click "check my work" once: it runs ("reading your steps"). Same for "help" (the ladder opens) and "+ a step". Watch that the step renders after the click and the controls do not jump under the pointer.
- **workbench-1 #14-37 (UX-20).** Take level 1 or 2 (they may still fail, see above): the failed line reads "Couldn't write a hint at this level that fits your work. Your steps are saved: press help to try again, or choose another level."; no "Hint" or "item's hint". Then check my work, or help: the line goes.
- **returner-1 #20-24 (UX-21).** On the welcome plan with a lesson offer first, press Begin: the offer's page opens ("This looks like something to learn. Start a 15 minute lesson on …?"); Not now opens the first question.
- **lesson-1 #20-24 (UX-22).** In a lesson, type a reply and Send: it stays in the thread with "sent" under it while "The teacher is writing…" shows, then appears once in the teacher's turn.
- **expert-1 #70-72, returner-1 #46-47 (UX-27).** On "Check what I already know" press Progress: Progress opens. On a short check press Today: Today's plan opens. Coming back to the check (starting it again) finds it.

## What was run

Every command through the scratch wrapper (`env -i`, isolated HOME, CODEX_HOME, config dir), node in a 5G scope, Python in a 3G scope at `-n 1`, one at a time.

| Command | Result |
|---|---|
| `npm ci` (desktop) | exit 0 (esbuild's install script blocked by allowScripts, as before) |
| `npx vitest run --maxWorkers=4 <files>` per defect, fail-first and passing | as above, per defect |
| `npm run typecheck` | exit 0 |
| `npx vitest run --maxWorkers=4` (desktop, whole suite) | Test Files 305 passed (305), Tests 3071 passed (3071) |
| `npm run frontend:build` | exit 0, "✓ built in 2.94s" (the usual chunk-size notice) |
| `pytest tests/test_identity_pins.py` after each of the nine defect commits | 342 passed, each time |
| `scripts/affected_tests.py --files <the nine changed source files>` | "no test file is affected" (no Python changed) |
| `pytest tests/test_workbench_text_gaps.py` (it reads `helpModel.ts`) | 6 passed |
| `pytest tests/test_structure_ratchets.py` | 3 passed |
| `pytest tests/test_effective_defaults_golden.py` | 3 passed |
| `pytest tests/test_cli_help_snapshot.py` | 26 passed |
| `pytest tests/test_kill_switches.py` | 8 passed |
| `pytest tests/test_sqlite_file_copies.py` | 1 passed |
| `pytest tests/test_test_layout.py` (alone) | 3 passed |
| `pytest tests/test_architecture.py` (alone) | 18 passed |
| `ruff check` | All checks passed! |
| `lint-imports --no-cache` | Contracts: 43 kept, 0 broken. |
| `scripts/check_gate_partition.py` | collected 31709: landing 31644 + arc_close 65 (exit 0) |

## Not verified here

- Nothing was walked or launched: no app, browser or server. Rendering, focus and the notices are verified in jsdom only. UX-19's lost click needs the real window (layout); so does the look of the sent card and of the offer page reached from Begin.
- The walk evidence was read (step logs, observations, copies of the walks' vaults in the scratch directory, read only); nothing of it is in tracked files.
- `get_today_queue` is now read on every closed plan. Its cost on a large library was not measured (stage 3 already read it on empty and Keep-going days).
- Whether today's list can hold questions the plan could not serve now (a hold until later today): if so, "there's more for today" is true but opening one may wait. Stage 3 noted the same for its list line.
- Why the hint writer's level-1 output failed `approach_question_declares_nothing` twice (a prompt or schema mismatch) was not traced past the stored rounds; stage 8.
- The practice exam's tabs (UX-27's sibling) and the classic shell's Today were not changed or walked.

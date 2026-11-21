# The live walk partread-3's round: six small things that still confused the learner

A student reads half of a one-section web chapter, never presses "done", answers what Today offers and reads on
(the live walks partread-1, -2 and -3 of 2026-11-21; partread-3 is this round's acceptance). After the first
evening's steps 4, 6, 7 and 8 landed, the walk still found six things: a third question that vanished without a
word (UX-69), a topic count that started again with each wave of writing (UX-75), an error hunt's work printed twice
(UX-76), "5 questions are ready" beside "Nothing is due tomorrow" (UX-77), a long answer that looked cut off and a
confidence control that appeared where Submit was (UX-67, from partread-2), and a `held` count that went stale
(UX-68, from step 8). Branch `ux/walk3-round`, from origin/main `f4ccb20266`.

Nothing is scheduled, served, generated, graded or scored differently. No prompt, algorithm tag, config key, kill
switch or migration. No identity pin, golden or structure ratchet moved. One workflow state now moves where it did
not (UX-68), and nothing reads it to decide anything (below). The adaptive-hints-off file snapshots moved by exactly
the confidence control's bytes (UX-67, below).

## Judgment calls to read first

1. **UX-69: the offer cannot know a reservation beforehand, so the explanation at the moment is the fix.** Today's "3
   questions … are ready" counts the book's questions on today's list that can be asked now
   (`apps/learnloop-tauri/src/app/todayCause.ts:287-305`; the phone: `askableWritten`, `:173`): not waiting to come
   back and not kept for a later check (the book's `laterItemIds`, `add_source._not_askable_now`). The third question
   was kept by the topic's certification check, which is chosen after an answer
   (`src/learnloop/attempts/post_attempt.py:296-299`, `schedule_certification_cold_probes`: a certificate exists only
   once the answers are graded). So the offer was true when made, and the line comes when the question is kept: under
   Next on feedback, and in the dated lines of the finish card and Today, desktop and phone.
2. **UX-69's words name the question by where it came from, and reuse step 7's.** "1 question from your reading is
   kept for a check on your own, available from 5 December." in place of step 7's "A check on your own is available
   from 5 December." whenever the check keeps one of the books' questions (`readingItemIds`: the readable books'
   `itemIds`, the questions Today offers from reading). A check that keeps another question keeps step 7's words; the
   same day's other checks are said beside it ("Another check on your own is …", "2 other checks on your own are …").
3. **UX-69 on feedback reads Today's plan once, only when Next has nothing to go on to** (the plan done and none of the
   books' questions askable: the key bar's "today's plan is done"). It shares Today's cache entry
   (`["get_daily_plan", session]`), so Today's next read reuses it. The finish card reads nothing: it uses the books
   Today and feedback last read, from the cache (`peek`), and says step 7's words when none are cached.
4. **UX-75: one count for the book, never a share.** "2 topics written · 3 more being written" ("4 topics being written"
   before the first is written). `written` counts every topic of every one of the book's writing jobs whose questions
   were written (held for a look or not; a failed topic is neither), finished waves included; `writing`, the topics
   the jobs writing now still have to write. The count is said where the line names the book, or names the one part
   every question and writing of the book comes from; beside one section's name when other sections have questions it
   is not said (it would not be that section's), and the old rule stands. An older sidecar (no `topics`) keeps "0 of
   4 topics done".
5. **UX-75: step 6's detail is placed in the same count.** The sidecar places the topic being written among its own
   job's topics ("Writing topic 1 of 3"), which restart with each wave; Today now says "Writing topic 3 of 5" (the
   book's `written + 1` of `written + writing`) where the line says the count. A topic with no place (another job
   writes beside it) still has none ("Writing questions on “…”"). Done in the shared `todayCause`, not the sidecar.
6. **UX-76: shown once, in the prompt; never a stem's setup.** The rule is in one shared pure module
   (`app/presentedBlocks.ts`, the phone imports it): an `error_hunt_worked_solution` block whose text, with white space
   collapsed, already lies within a prompt block is not rendered; otherwise every block is, as before. The sidecar's
   blocks, the item, its grading and the label are unchanged: nothing the learner needs is lost, because the text is
   all in the prompt. A laddered stem's shared setup is never left out (tested).
7. **UX-77: no line says that nothing is due.** Every dated review line now says that the questions are ones the
   learner answered and that they come back ("3 questions you answered come back on 30 November."), which is true by
   construction: a question never answered has no due and is in no group (step 7's object). The bare "Nothing is due
   tomorrow." and "Nothing more is due tomorrow." are gone: beside questions ready now they read as nothing to do
   until the date, and the date of the next answered question says it without them. Changed in one place,
   `nextPracticeLines`, which the desktop's Today and finish card and the phone's Today and finish banners share.
8. **UX-67: the box's height is the screen's, and nothing that appears while typing goes above Submit.** The box grows
   with the answer up to the visible height of the screen's scrolling area less what sits under it, so the box and
   Submit fit on one screen once scrolled to; only an answer longer than that scrolls inside the box (with its
   scrollbar). Before, its greatest height was the window less the box's own top, so under a long question it was the
   140-pixel floor (about four lines) and a long answer looked cut off. The optional confidence control, which appears
   once the answer is non-empty, now sits under the row with Submit, on the simple and the classic card. The layout
   rule: a control that appears while the learner types is placed below Submit, never between the box and it.
9. **UX-68: the state is kept true at its source, cheaply.** Every decision on a proposal's items (an OK, a refusal, a
   revert, an undone refusal, a deleted item) already passes through `ContentStoreMixin._refresh_proposal_status` inside
   its own transaction; that now calls the reader store's `settle_reviewed_topic_work` on the same connection, which
   moves the topic work naming that proposal between `held` and `written` by the writing job's own rule
   (`jobs._TopicWork.record`: held while any question of its proposals is pending). Rows in any other state (queued,
   running, failed, not needed, legacy) are the job's to move and are left. `held` stays in the summary.

## Commits

| Commit | What |
|---|---|
| `00699c0b18` | Tests first: a held topic's work follows the review of its questions (UX-68) |
| `23e8d3cb38` | A decision on a proposal's questions moves its topic work between held and written, in the decision's transaction (UX-68) |
| `12dd5f831a` | Tests first: the walk's states on the desktop and the phone (UX-69, UX-75, UX-76, UX-77, UX-67) and the book's topic count across waves |
| `aca8836bc4` | The book's facts carry one topic count across waves (`topics`) (UX-75) |
| `0321d04af2` | Today says the count and places the detail's topic in it; `readingItemIds` (UX-75) |
| `57d7537c88` | The dated lines: answered questions come back, no "nothing is due"; the kept question named on feedback, the finish and Today (UX-77, UX-69) |
| `a34bff5a70` | An error hunt's work already in its prompt is shown once, desktop and phone; `desktop_validate.py`'s counts (UX-76) |
| `9ed1875d21` | The answer box's height; the confidence control under Submit; the adaptive-hints-off snapshots (UX-67) |
| (this record) | This record and the ledger rows |

## UX-69: the third question offered, kept for a check

**What the walk saw** (partread-3, observations 34-48): "3 questions … are ready"; after two answers the feedback said
"today's plan is done", Next led to "No questions ready yet", and "I never learned what happened to the original third
one."

**Cause.** The second answer certified the topic, and its certification check (`post_attempt.py:296-299`) kept the
third question for a check on the learner's own two weeks on; from then the book's facts name it among those that
cannot be asked now (`add_source.py:2846`, `_not_askable_now`), so Begin and Next no longer offer it
(`todayCause.ts:298-299`) and feedback's key bar says "today's plan is done" (`app/dailyPlan.ts:197`). Step 7's summary
already dated the check (`next_practice.checks`), in words that did not connect it with the question offered:
"A check on your own is available from 5 December."

**Fix.** `app/nextPractice.ts` `keptForCheckLine(next, keptItemIds)` and `nextPracticeLines(…, { keptItemIds })`;
`app/todayCause.ts` `readingItemIds(cards)`; feedback (`screens/FeedbackScreen.tsx`, `screens/feedback/FeedbackSurface.tsx`
`nextNote`, `data-testid="feedback-next-note"`), the finish card (`components/SessionFinishHud.tsx`), Today
(`screens/today/TodayPlace.tsx`) and the phone's Today and finish banner (`today/PlanToday.tsx`).

| Where | Before | After |
|---|---|---|
| Desktop feedback (simple card), the plan done and Next with nothing to go on to, a later check keeping a book's question | **Next ↵** · "today's plan is done" | the same, and under it "1 question from your reading is kept for a check on your own, available from 5 December." (two: "2 questions from your reading are kept for checks on your own, available from …") |
| The same, no such check (or the plan's read failed) | **Next ↵** · "today's plan is done" | unchanged |
| Desktop Today (done or empty day), desktop finish card, phone Today (done or empty day) and the phone's finish banner (plan on) | "A check on your own is available from 5 December." | "1 question from your reading is kept for a check on your own, available from 5 December." |
| … with another check the same day | "2 checks on your own are available from 5 December." | the kept line, then "Another check on your own is available from 5 December." ("2 other checks on your own are …") |
| … a check keeping no question from the reading | "A check on your own is available from …" | unchanged |
| The phone's finish banner with the plan off (`TodayScreen`, no books read) | "A check on your own is available from …" | unchanged |
| The desktop finish card with no books in the cache | step 7's line | unchanged |
| Today's offer before the answers | "3 questions from what you’ve read … are ready. More are being written." | unchanged (it cannot know; judgment call 1) |

## UX-75: one topic count across waves

**What the walk saw** (observations 34-66): "0 of 4", "1 of 4", "2 of 4 topics done", then, after reading two more
screens, "0 of 3 topics done": "the counter no longer told me how far through the chapter I was".

**Cause.** `add_source.reading_questions` counted `progress` over the jobs writing now only
(`add_source.py:2707-2714`), and Today said it as "N of M topics done" (`todayCause.ts:526`, `:550`, `:594`). A part
read's next wave is a job of its own, so the first wave's topics dropped out of the count when it finished.

**Fix.** `add_source._count_topics` (the old progress lines moved into it: `reading_questions` is 197 lines, under the 200 the ratchet holds):
`topics: {written, writing}` over every writing job of the book, present only while some are being written.
`todayCause.bookTopics`, `topicCountWords`, `placedDetail`; `dto.ts` `ReadingQuestionsDto.topics`.

| Where (desktop and phone: the shared `todayCause`) | Before | After |
|---|---|---|
| Writing, part read, one section | "Writing questions from what you’ve read in “B” · 0 of 3 topics done. Keep reading meanwhile." | "Writing questions from what you’ve read in “B” · 2 topics written · 3 more being written. Keep reading meanwhile." |
| Writing, nothing written yet | "… · 0 of 4 topics done …" | "… · 4 topics being written …" ("1 topic being written") |
| Writing, a finished section | "Writing questions from “P”, the part you read · 2 of 8 topics done" | "Writing questions from “P”, the part you read · 2 topics written · 6 more being written" (where the count is that part's) |
| Offer while more are written | "5 questions from what you’ve read in “B” are ready. More are being written (0 of 3 topics done)." | "5 questions from what you’ve read in “B” are ready. 3 topics written · 3 more being written." |
| The wait's detail (step 6), one job writing | "Writing topic 1 of 3: “T”" | "Writing topic 3 of 5: “T”" |
| The detail with two jobs writing | "Writing questions on “T”" | unchanged |
| Several sections, the line naming one | "… · 2 of 8 topics done" only where no other section shows (step 6's rule) | unchanged (the book's count is not said beside one section's name) |
| An older sidecar (no `topics`) | "… · 0 of 4 topics done" | unchanged |
| Step 7's dated line | "Questions on 3 more topics are still being written." | unchanged (it agrees: "3 more") |

## UX-76: an error hunt's work printed twice

**What the walk saw** (observation 36): "It marked me Right … though the worked solution was printed twice."

**Cause.** The writer put the work into the prompt ("Submitted work: …") and into the item's
`error_hunt.worked_solution_md`; the sidecar sends both as blocks (`serializers.py:257` and `:283-295`), and both
renderers draw every block (`components/ItemPresentation.tsx:45`, phone `practice/QuestionScreen.tsx:617`).

**Fix.** `app/presentedBlocks.ts` `presentedBlocks(blocks)`, used by `ItemPresentation` (practice, feedback, exams, the
inspector, the workbench: every desktop surface that shows a question) and the phone's `QuestionScreen`.

| Where | Before | After |
|---|---|---|
| Desktop, prompt holding the work | the prompt with the work; then "THE WORK TO CHECK" and the work again | the prompt with the work, once |
| Phone, the same | the prompt; "The work to check"; the work again | the prompt, once |
| Prompt not holding the work (desktop and phone) | the prompt; "The work to check" (desktop in capitals); the work | unchanged |

## UX-77: questions ready beside later days

**What the walk saw** (observation 66): "5 questions … are ready. More are being written." and "Nothing is due
tomorrow. Your next questions are due on 30 November. A check on your own is available from 5 December.": "I do not
know … how the ready questions fit the dates shown below them."

**Cause.** `app/nextPractice.ts:97-105`: the dated lines said "due" and "Nothing is due tomorrow" with no word that the
dates are those of questions already answered.

**Fix.** `nextPracticeLines` alone (desktop Today and finish card, phone Today and both finish banners).

| State | Before | After |
|---|---|---|
| Due tomorrow, minutes supported | "Tomorrow: 2 questions due · about 3 minutes." | "Tomorrow: 2 questions you answered come back · about 3 minutes." |
| Due tomorrow, one, no supported minutes | "Tomorrow: 1 question due." | "Tomorrow: 1 question you answered comes back." |
| Nothing tomorrow, the next day later | "Nothing is due tomorrow. Your next questions are due on 30 November." ("Your next question is due Wednesday.") | "3 questions you answered come back on 30 November." ("1 question you answered comes back Wednesday.") |
| The finish, still due today, then tomorrow | "Still due today: 1 question." "Tomorrow: 2 more questions due · about 3 minutes." | "Still due today: 1 question." "Tomorrow: 2 more questions you answered come back · about 3 minutes." |
| The finish, still due today, the next day later | "Still due today: 1 question." "Nothing more is due tomorrow. Your next question is due on 9 November." | "Still due today: 1 question." "1 more question you answered comes back on 9 November." |
| Only checks, writing or waiting sections; or only still due today | "Nothing is due tomorrow." (or "Nothing more is due tomorrow.") first | no such line; the other lines unchanged |
| Checks, writing, waiting | unchanged | unchanged (the check line is UX-69's where it keeps a question from the reading) |
| The full list's rows ("comes back on 9 November", "a check on your own from …") | unchanged | unchanged |

On the walk's Today the lines now read: "5 questions from what you’ve read in “Symmetric Matrices and Variance” are
ready. 3 topics written · 3 more being written." then "2 questions you answered come back on 30 November." and "1
question from your reading is kept for a check on your own, available from 5 December."

## UX-67: the answer box and Submit

**What the walk saw** (partread-2, steps 48 and 53): "The shortened display of my long first answer looked cut off …
I inserted another version into the middle", and "I also clicked the confidence choice while aiming for the earlier
Submit position".

**Cause.** `screens/PracticeScreen.tsx:514`: the box's greatest height was `max(140, window height − the box's top −
what sits under it − the key bar − 28)`. Under a long question (that walk's error hunt, its work printed twice: UX-76)
the box's top is near the window's bottom, so the height was the 140-pixel floor, about four lines, and a long answer
showed its first lines only. The confidence row (`:2117-:2165`) is rendered once the answer is non-empty, between the
box and the Submit row (`:2322`), so it pushed Submit down by its height as the learner typed.

**Fix.** `answerBoxCap`: the visible height of the screen's scrolling area (`.screen-scroll`; the window less the key
bar where there is none) less what sits under the box, never under 140. The confidence row moved under the Submit row
on both cards. Words unchanged.

| Card | Before | After |
|---|---|---|
| Simple and classic, typing | box · (confidence row appears) · Submit row (moves down) | box · Submit row (stays) · confidence row appears under it |
| A long question (box near the bottom) | box at most 140 pixels: a long answer shows about four lines | box up to the scrolling area's height less what is under it: the answer shows whole up to a screenful, scrolling inside only beyond it |
| The phone | no confidence control; its box is `min-height: 9rem; max-height: 45vh` whatever the question | unchanged: not the same problem (its height does not depend on the question) |

The four adaptive-hints-off file snapshots (`screens/__snapshots__/adaptiveOff.*.html`) were rewritten with `vitest -u`:
compared with the base, each frame's confidence group is byte-identical, and each frame with the group removed is
byte-identical (checked by a script over the four files: same lengths, same groups, same rest). Their test's comment
names this rewrite.

## UX-68: the `held` count kept true

**Cause.** `jobs.py:3742` (`_TopicWork.record`) sets `held` or `written` only while the writing job runs; the
review path (`handlers/proposals.py` `accept_proposal_items`, `reject_proposal_items`, `reset_proposal_items`) never
touched `reader_topic_question_work`, so `next_practice.held` (`next_practice.py:218`) kept counting a topic whose
questions were looked at.

**Fix.** `db/stores/reader.py` `settle_reviewed_topic_work(connection, patch_id, updated_at=…)`, called at the end of
`db/stores/content.py` `_refresh_proposal_status` (`:1393`), which every decision on a proposal's items calls inside its
own transaction (accept and apply, reject, revert, reset, delete, persist). No words: the summary's `held` stays wordless.

**Nothing reads it to decide anything.** The column `reader_topic_question_work.state` is read in `src` only by
`daily_plan/next_practice.py:218` (the `held` count, which no screen says). The rows' other readers
(`reader/part_read.py`, `reader/section_generation.py`, `content/pipeline/add_source.py`, `content/pipeline/jobs.py`,
`learnloop_sidecar/section_questions.py`) read ownership, batches, triggers and proposals, never `state` (searched:
`["state"]`, `.get("state")`, `state =` over those files and every SQL naming the table). The table is WORKFLOW and
denied to adaptive difficulty, as before.

## Tests, with fail-first evidence

Every new test was run against the base's sources before its fix (the tests' commits `00699c0b18` and `12dd5f831a`
sit on the base's code):

- `tests/test_held_topic_work_review.py`: **2 failed, 2 passed** (an OK and a refusal, and an undone refusal, failed:
  `{'lo_early': 'held'} != {'lo_early': 'written'}`; the topic with a question still waiting and the failed topic are
  controls).
- `tests/test_part_read_first_set.py::test_the_topic_count_runs_on_across_waves_of_writing`: **failed**
  (`KeyError: 'topics'`).
- Desktop (`nextPractice.test.ts`, `todayCause.test.ts`, `TodayPlace.test.tsx`, `FeedbackScreen.plan.test.tsx`,
  `SessionFinishHud.phase4.test.tsx`, `denyList.test.tsx`, `denyList.phase4.test.tsx`, `ItemPresentation.test.tsx`,
  `PracticeScreen.answerBox.test.tsx`): **28 failed, 216 passed**; `denyList.test.tsx` failed to load
  (`keptForCheckLine is not a function`). Among the failures: every new walk test, and step 7's assertions moved to
  the new words. Controls that passed on both: an error hunt whose prompt lacks the work, a stem's setup, feedback with
  nothing kept, the several-sections and older-sidecar counts.
- Phone (`Today.plan.test.tsx`, `Today.queue.test.tsx`, `Question.test.tsx`): **7 failed, 75 passed** (the two walk
  tests, the error hunt shown once, step 7's four moved assertions); the error hunt's control passed.

Assertions changed (each the words this round replaces, UX-77): `nextPractice.test.ts` (8: "Tomorrow: 2 questions due …"
→ "… you answered come back …", "Nothing is due tomorrow. Your next … due …" → "N question(s) you answered come(s) back
…", and the bare "Nothing is due tomorrow." / "Nothing more is due tomorrow." removed from three expected lists);
`TodayPlace.test.tsx` (3, step 7's describe); `SessionFinishHud.phase4.test.tsx` (2); `denyList.phase4.test.tsx` (1);
phone `Today.plan.test.tsx` (3) and `Today.queue.test.tsx` (1). No assertion checking behaviour was loosened.

## What was run

Every Python run through the scratch wrapper (empty home, config and Codex dirs); every pytest run from a script that
refuses an empty target list, `-n 1`, in a 3 GB scope, one at a time; vitest with 4 workers; npm through the shared npm
cache.

| Command | Result |
|---|---|
| `tests/test_held_topic_work_review.py` + `tests/test_next_practice.py` (after the UX-68 fix) | 17 passed |
| `tests/test_identity_pins.py` after the first source commit | 357 passed |
| `test_first_questions_today.py`, `test_structure_ratchets.py`, `test_part_read_first_set.py` (after the topic count) | 65 passed |
| `scripts/affected_tests.py --files` the three changed Python sources | 1,356 files (over 150: the name filter below instead) |
| The brief's name filter (today, first_questions, next_practice, build_wait, part_read, add_source, ux_phase4, sessions, followup, proposals, item_presentation, mobile_v2_plan, mobile_v4, mobile_allowlist) plus proposal, topic_question, section_question, reader_progress, section_done and `test_held_topic_work_review.py`: 97 files, chunks of 40, 40, 17, `-m "not arc_close"` | 710 passed; 703 passed; 339 passed, 3 skipped |
| `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`, `test_public_tip_guards`, `test_ingest_queue_store` (after the last commit) | 414 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `tests/test_architecture.py` alone | 18 passed |
| `ruff check` | All checks passed! |
| `lint-imports --no-cache` | Contracts: 45 kept, 0 broken. |
| `scripts/check_gate_partition.py` | collected 32736: landing 32670 + arc_close 66 |
| Desktop `npm run typecheck`; `vitest run --maxWorkers=4` (whole suite); `npm run frontend:build` | clean; 325 files, 3,618 tests passed; built |
| Phone `npm run typecheck`; `vitest run --maxWorkers=4` (whole suite); `npm run build` | clean; 43 files, 460 tests passed; built |
| `desktop_validate.py` | the three counts take `app/presentedBlocks.ts` (336 → 337 TypeScript files, 325 → 326 entry-reachable, ACTIVE 342 → 343); it reports only the new file's missing note and stale notes, which the landing's regeneration writes |

No identity pin, golden or structure ratchet moved (`reading_questions` went from 200 lines to 197; the count of
functions over 200 lines is unchanged). The adaptive-hints-off snapshots moved (UX-67, above).

## What a live-route walk must check

The partread-3 persona on the real desktop window and the phone:

1. **UX-69.** Read to about half, wait for "3 questions … are ready", answer two right. If the second answer certifies
   the topic (a `certification_cold_probe` row in `followup_tasks` with the third question as `selected_item_id`), the
   feedback shows "today's plan is done" and under Next "1 question from your reading is kept for a check on your own,
   available from <the task's not_before as a local day>"; Today's done or empty screen and "Done for today" say the same
   line, not "A check on your own is …". If the line comes late (the check is chosen by the post-attempt worker, after
   the answer's feedback is read), note how late: the feedback reads the plan once when Next has nothing to go on to.
2. **UX-75.** Let the first wave write two topics, read on two screens: Today's line says "N topics written · M more
   being written" with N not restarting at 0; the wait's detail says "Writing topic N+1 of N+M". Check N against the
   book's applied topics.
3. **UX-76.** An error hunt whose prompt contains "Submitted work: …": the work shows once, with no "THE WORK TO
   CHECK" (desktop) or "The work to check" (phone); one whose prompt does not: the label and the work show as before.
   Check the feedback screen's question too.
4. **UX-77.** With questions ready and answered ones due later: the dated lines read "N questions you answered come back
   on <day>." and never "Nothing is due tomorrow"; the day matches `practice_item_state.due_at` (local day).
5. **UX-67.** Under a long question, paste a 40-line answer: the box shows it whole up to a screenful and scrolls inside
   beyond; Submit sits right under the box and does not move when the confidence row appears under it; check at a
   small window height and in the real WebKitGTK window.
6. **UX-68.** A build or part read whose questions were held: accept them in Review; `reader_topic_question_work.state`
   reads `written` at once (and `held` again after undoing a refusal).

## What was not verified

- No app, browser, server, phone or model ran (the rules): every screen is tested in vitest/jsdom; the layout (the
  box's height, the confidence row under Submit, the note under Next) is not seen in the real WebKitGTK window or at
  phone width.
- When the post-attempt worker creates the certification check after feedback's one read of the plan, the note under
  Next does not appear on that screen (Today's lines say it on the next read). Whether the shell's queue-changed signal
  re-reads it is not tested.
- The classic feedback card (`[ui] practice_feedback = "classic"`) shows no note (its key bar keeps "today's plan is
  done"); the phone's finish banner with the plan off says step 7's check line (it reads no books).
- The finish card names the kept question only when the books are in the cache (Today or feedback read them this
  session); otherwise it says step 7's line.
- The real chapter's waves and their topic counts, and a real error hunt's prompt, are not measured (fixtures only).

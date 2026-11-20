# UX-44: Begin and Next after the first answers

A first-day learner answered two of the first three questions written from a section; then "Next" returned to Today, Today still said three questions were ready, Begin reopened the question just answered, and the newly written questions were offered only in the full list. Branch `fix/ux44-begin-after-first-answers`.

## The measurement

A walk on the live route (a fresh library, one web chapter, one section, eight topics; the persona's report, goals 6 to 8 and "Where I got stuck", and its steps 56 to 86, read with the walk's synthetic vault through a read-only connection; nothing from it is copied here but counts and field values):

| Step | Screen | What happened |
|---|---|---|
| 56 | Today | "Nothing planned for today." and "3 questions from what you read in “…” are ready. More are being written (1 of 8 topics done)." with Begin ↵ |
| 58 | Begin | the first question of the first topic |
| 63 | feedback (right) | Next ↵, and under it the key bar's "today's plan is done" |
| 65 | Next | back to Today, the same sentence ("3 questions … are ready") |
| 66 | Begin | the second question of the topic |
| 70 | feedback (right) | "today's plan is done" again |
| 72 | Next | Today, still "3 questions … are ready" |
| 73, 76 | Begin (and Skip, then Begin) | the second question again, the one just answered |
| 78 | "hide this for the session" | the "Felt: easy · about right · hard" row disappeared; the question stayed |
| 83 | Today | "6 questions … are ready. More are being written (2 of 8 topics done)." |
| 84 | all of today's list | three questions of the first topic and three of the second, each "coming back later today" |
| 86 | the list | a question of the second topic, picked by the learner |

The vault at the walk's end: the first two questions answered (right), each with a next due time nine days later; the third question of the topic never attempted and named by a `followup_tasks` row of kind `certification_cold_probe` (status `pending`) as its `selected_item_id`, created at the second answer, `not_before` fourteen days later; the day's one plan (`normal`) built and closed ("Nothing else worth doing fits today.") a second after it was made, nine minutes before the first question existed.

## Step 0: the sequence, reproduced, and the code path of each symptom

Reproduced with the house helpers (no model, no app): `tests/certification_cold_probe_helpers.py` (`_certify`: one topic whose first question, answered right, certifies it; `schedule_certification_cold_probes` then reserves another question of the topic) plus a never-answered question of the same topic, and `read_due_queue` a few minutes later, the build `get_today_queue` serves. The list holds all three: the reserved question first (a new question's rank, due time none), the never-answered one beside it, and the answered one (due time eleven days later, ranked by its goal-frontier pull); after the never-answered one is answered too, all three are still on the list. The book facts' side (`add_source.reading_questions`) was reproduced in `tests/test_first_questions_today.py` (the new tests below): a section's three questions applied, two answered, the third reserved, six more applied from a second section.

**(a) What `questions.count` and `item_ids` count.** Applied ever, not practisable now. `reading_questions` (`src/learnloop/content/pipeline/add_source.py`) collects every accepted, applied practice item of each finished section's part proposals that is still in the vault and not retired; nothing in it reads attempts, due times or follow-up tasks. Today's sentence (`apps/learnloop-tauri/src/app/todayCause.ts`, `todayCause`) then counts `mine`: the book's `itemIds` that are on today's list (`get_today_queue`). The list is the scheduler's routine queue (`scheduling/scheduler.py` `_due_queue`), which keeps an answered question that is not due again (its `dueStatus` is `later`, its `dueAt` in the future: the "Later today" section, `handlers/queue.py` `_SECTION_SPECS`) and the question reserved for a certification cold probe (the routine gate withholds only an open cold *retry*'s item: `serving_exclusions.routine_serving_exclusions` reads `pending_remediation_cold_item_ids`, while `out_of_timing_serving_exclusions`, which adds every open cold task's item, is used by the quick check, `find_practice` and the plan's slot facts, not by the routine queue). So after two answers and one reservation, "3 questions … are ready" counted two answered questions and one reserved one.

**(b) Which item Begin opens.** `causeAction` for `questions_ready` / `questions_ready_with_section_work` opens `itemId`, which is `mine[0]`: the first of the book's questions in today's list order, as a pick from the list (`openFromList` → `plan_learner_pick`). The list's order is the scheduler's rank, and nothing in Today's choice looks at whether the question was answered or reserved, so the first can be one answered minutes ago (the walk: the second question, steps 73 and 76) or the reserved one (the reproduction: it ranks first).

**(c) Why "Next" goes to Today.** Feedback's Next under the plan (`screens/FeedbackScreen.tsx` `goOn`, plan mode) asks the plan for its next step (`useNextPlanStep` → `next_plan_item`, `daily_plan/engine.py`). The day's plan closed before any question existed, so a question opened from Today is an open-list pick after the plan closed (`learner_pick`: a receipt, "the plan does not grow"), and `next_plan_item` on a closed plan answers `done` (`_done_step`, the `if not record.is_open` branch). `routePlanStep` (`app/App.tsx`) sends `done` to Today's place (`planStepAction` → `{ type: "plan" }` → `setTodayStage("queue")`). Nothing on that path looks at the questions Today offers.

**(d) Why the newly applied questions were not offered by Begin.** They were on today's list (every list read is built anew over the vault's items; a new question enters as new material, `placement` / `cold_start_gate`) and in Today's count ("6 questions … are ready" at step 83), and the list showed them (step 84). Begin did not open them because it opens the first of the book's questions in list order, and the first topic's answered (and reserved) questions ranked ahead of them. The plan never took them in either (it closed before they existed; only Keep going builds an extension).

**(e) Where "Today's plan is done" comes from.** Feedback's key bar and Next label: `nextPlanKeyLabel` (`app/dailyPlan.ts`) says "today's plan is done" when the prefetched plan step is `done`, which it always is on a closed plan (c). Today itself said "Nothing planned for today." (the closed, empty plan: `planWasEmpty`) with the book's sentence and Begin under it. So the two screens disagreed: feedback spoke for the plan, Today for the book's questions.

**(f) "hide this for the session".** The accessible name (and tooltip) of the "×" after the optional difficulty rating, "Felt: easy · about right · hard" (`screens/practice/DifficultyRatingTap.tsx`, adaptive difficulty AD1): it hides that rating row for the rest of the session (remembered per session in browser storage) and clears the rating; it never hides or skips the question. The label is wrong for a learner reading it without the row in view: "this" reads as the question (the walk, step 77).

**(g) The phone.** `apps/learnloop-mobile/src/today/PlanToday.tsx` says the shared `causeSentence` under "Nothing planned for today." when the plan is empty, with `listUnknown` (the phone reads no list): a book's questions are counted by `questions.count`, written ever. So the phone said "3 questions from what you read in “…” are ready. More are being written (1 of 8 topics done)." in the same state. It has no Begin of its own (Keep going is its action); its Next after an answer asks the plan (`phone.nextPlanItem`), which answers `done` on a closed plan, and Today then shows the same sentence.

## The fix

| Commit | What |
|---|---|
| `b4cf8c2aa9` | this record's step 0, before any code |
| `471cc4000f` | sidecar: the book's facts name the questions that cannot be asked now (`questions.later_item_ids`) |
| `c51ec32900` | Today (desktop) counts, and Begin opens, only questions that can be asked now; the phone's sentence through the shared cause |
| `c489ed55d6` | feedback's Next, with the plan done, goes on to the question Today offers with Begin, and names it |
| `60fed94f22` | the rating row's hide control says what it hides |

This record's remaining sections and the ledger rows are the last commit.

**What "can be asked now" means.** One of a book's questions from reading, on today's list, that is neither waiting to come back (answered, and its next due time is still ahead: the list's own row says it, `dueStatus` `later` with a `dueAt` in the future) nor kept for a later check on your own (the book's new fact). A question answered and due again (`dueStatus` `due`) can be asked again. Nothing else holds a question back here: what the routine gate withholds (an exam reservation, held-out material, a cold retry's question, a put-away topic, …) is not on the list in the first place.

**The fact (sidecar, `add_source.reading_questions`).** `later_item_ids`: of `item_ids`, in their order, those whose `practice_item_state.due_at` is after now, and those named by an open (`pending` or `served`) `cold_retry` or `certification_cold_probe` follow-up whose `not_before` is after now. Present only when there are some, so every other reader of the fact (and its exact-equality test) is unchanged; camel-cased `laterItemIds` on the card (`ReadingQuestionsDto`). Read-only: two `SELECT`s over the book's own question ids; no write, schema, migration, config key, prompt or algorithm tag. Why a fact and not only the list: the phone reads no list, and nothing on the list says a question is reserved (`isFollowup` is false until the check is due; its row reads as any new question). Why the list's due time as well on the desktop: the books are re-read on a schedule of their own (`TAG.sources` is not invalidated by an answer), while the list is invalidated by every answer, so a book card read just before the answer would otherwise still count it.

**Today (desktop, `todayCause.ts`, `TodayPlace.tsx`).** `todayCause` takes `listWaiting` (`waitingOnList` over the list's rows). A book's offer counts and opens only its questions that can be asked now; the book's questions on the list that cannot are no longer "Today's list still has questions" either. With none left, the ranking below the list applies unchanged, so a section still being written gives its writing line and a book with nothing being written gives "Nothing from … is up today". The phone (`listUnknown`) counts `count` minus `laterItemIds`.

**Next (`autoAdvance.useNextReadingQuestion`, `FeedbackScreen`).** Under the plan, when the plan's next step is `done`, feedback reads the books and today's list through Today's own cache entries and names the question Today's Begin would open (`askableReadingQuestion`: `todayCause` itself over the list without the question on screen, so Next and Begin cannot disagree). On Next it reads both again (a topic applied, an answer just given, a check just reserved all change them), and opens that question as Today's Begin does: a pick from the list (`plan_learner_pick`, the open-list pick a closed plan records), handed to the shell as an item step that opens at once. With none, Next does what it did: the `done` step, back to Today. A step the plan has next is followed as before and the books are not read (an existing test checks no queue read; the new one checks no library read either).

**The day's plan is unchanged.** The plan is not asked to take in questions written during the session: Next makes the same open-list pick Begin makes, which records the learner's pick and does not grow a closed plan (`learner_pick`). No change to scheduling, the plan's contents, the reservation of the later check, grading or any stored meaning; so this task's stop did not apply.

**"hide this for the session".** The control is right and its name was wrong; one wording change in its two attributes (`aria-label`, `title`): "hide easy · about right · hard for this session".

## Every state after the first answers (desktop Today on a closed, empty plan; feedback with the plan's next step `done`)

"…" is the book's title; the walk's reading is one section, so the book is named. Begin and Enter are the same; "a pick" is `openFromList` / `plan_learner_pick`.

| State | Today's words | Today's action | Feedback's Next label | What Next does |
|---|---|---|---|---|
| Some can be asked now, more being written | "N questions from what you read in “…” are ready. More are being written (k of 8 topics done)." (N counts only those) | **Begin ↵**: the first of them in list order, a pick | "next: *its topic*" | opens that question (a pick), not Today |
| Some can be asked now, nothing being written | "N questions from what you read in “…”. More come as you finish sections." | Begin ↵, as above | "next: *its topic*" | opens it |
| Some can be asked now, a topic could not be written | the two lines above plus "Not every topic's questions could be written." (Try again once the writing stopped) | Begin ↵; Try again | "next: *its topic*" | opens it |
| None can be asked now, more being written (the walk after the second answer, before the second topic applied) | waiting line "Writing questions from what you read in “…” · k of 8 topics done", then "Keep reading meanwhile." | Continue reading; no Begin (Enter is Keep going, as on any done day without an offer) | "today's plan is done" | back to Today, which says the line on the left |
| None can be asked now, nothing being written | "Nothing from “…” is up today. More questions come as you finish sections." | Continue reading | "today's plan is done" | back to Today |
| None of the book's, but another question on the list can be asked | "Today's list still has questions, if you'd like some." | Open today's list | "today's plan is done" | back to Today |
| None can be asked now, a section's writing stopped | "Couldn't write the questions from what you read in “…”. Try again, or keep reading: nothing is lost." | Try again | "today's plan is done" | back to Today |
| An answered question due again | counted again, as any question that can be asked | Begin ↵ may open it | "next: *its topic*" | opens it |
| Books or list still being read on feedback | (Today unchanged) | | "next" | reads both, then opens or goes back as above |
| The plan has a next step (an item, a block, a reading, a lesson offer) | (unchanged) | | unchanged ("next: …", "next block", …) | unchanged; the books are not read |

So "today's plan is done" is now said only where Today offers no Begin, and wherever Today offers Begin, Next goes to the same question. A plan that had questions and is done ("Done for today · …", "The plan stopped here, but there's more for today if you'd like it." with Open today's list) offers no book Begin of its own; there, too, Next goes on to the book's question that can be asked now when there is one (the "more for today").

**The question kept for a later check.** Today never counts it and Begin and Next never open it. Today says nothing about it. The full list still shows it, as "coming back later today", like every never-answered question ("later" with no due time; `fullListWhy`), and the learner can still pick it there (what serving it before its day does to the check was not run here; UX-44b, UX-44c below). The full list's "on your own · no hints" appears only once the check is due and the list carries it as a follow-up.

## The phone

`PlanToday` says the shared `causeSentence` under "Nothing planned for today." when the plan is empty (unchanged), now counting `count` minus `laterItemIds`:

| State | Phone sentence |
|---|---|
| Two answered, one kept for a later check, six written since, more being written | "6 questions from what you read in “…” are ready. More are being written (3 of 8 topics done)." |
| None can be asked now, more being written | "Writing questions from what you read in “…” · 1 of 8 topics done. Keep reading meanwhile." |
| None can be asked now, nothing being written | "Nothing from “…” is up today. More questions come as you finish sections." |

The phone still has no Begin of its own (Keep going stays its one action) and its Next after an answer asks the plan as before (`phone.nextPlanItem`); it reads no list, so it cannot go on to a question outside the plan. Not changed here.

## Tests, fail first

Each new test was run on the code before its fix: the Python ones on the branch's base, the screens' with the six changed desktop sources put back from `HEAD` for the run and restored after (a script with a restoring trap; the tree was checked unchanged after).

| File | Tests | On the code before |
|---|---|---|
| `tests/test_first_questions_today.py` (UX-44 section) | 4: the measured sequence (three applied, two answered by the learner's own self-graded answers, the third kept by a `certification_cold_probe` follow-up two weeks on, six applied from a second finished section): `count` 9, `later_item_ids` the first three; a month on, both due again and the check's day come: no `later_item_ids`; the card's line carries it now; nothing answered or kept: no key | **3 failed** (`TypeError: reading_questions() got an unexpected keyword argument 'clock'` twice, `KeyError: 'later_item_ids'`); the control passed |
| `apps/learnloop-tauri/src/screens/today/TodayPlace.test.tsx`, describe "After the first answers…" | 5: the measured sequence (nine written, three not askable, the first topic ranked first): "6 questions … are ready. More are being written (3 of 8 topics done)." and Begin picks `pi_4`; a list read after the answers with the books read before: the list's due times keep the answered out, the writing line, no Begin, Enter picks nothing; none left and nothing written: "Nothing from … is up today…"; another list question that can be asked: "Today's list still has questions…"; an answered question due again is offered | **4 failed** ("9 questions …" where 6 was expected; the writing line not found; "3 questions from what you read in …" where "Nothing from" was expected; "2 questions …" where "Today's list still has questions" was expected); the due-again control passed |
| `apps/learnloop-tauri/src/screens/FeedbackScreen.plan.test.tsx`, describe "Next when the plan is done…" | 4: after the second answer with one written since, Next names "next: Construct a diagonalization" (not "today's plan is done") and picks `pi_4` (never the one on screen), handing the shell `{kind: "item", practiceItemId: "pi_4", presentationId: "pres_pi_4", boundary: false}`; a topic applied while feedback shows: Next reads again and picks it; the last askable answered while more are written: "today's plan is done", Next hands `done`, no pick; a step the plan has next: followed as before, no books or list read | **2 failed** (the label not found; no pick); the two controls passed |
| `apps/learnloop-tauri/src/app/dailyPlan.test.tsx` | 1: `nextPlanKeyLabel` with the plan done names the book's question, says "next" while unread, "today's plan is done" with none, and leaves a plan step's label alone | **1 failed** (`expected 'today's plan is done' to be 'next: Construct a diagonalization'`) |
| `apps/learnloop-mobile/src/today/Today.plan.test.tsx`, describe "after the first answers (UX-44)…" | 3: the phone's three sentences above | **3 failed** ("9 questions …"; "3 questions … are ready …" where the writing line was expected; "3 questions … More come as you finish sections." where "Nothing from" was expected) |
| `DifficultyRatingTap.test.tsx`, `PracticeScreen.adaptiveDifficulty.test.tsx` | the control found by its new name (three queries changed from "hide this for the session") | **2 failed** on the old label; the locked-row query (`queryByRole(…) toBeNull`) passes on both |

**Assertions changed, and why.** Only the three button-name queries of the rating row's hide control (`DifficultyRatingTap.test.tsx` lines 46 and 52, `PracticeScreen.adaptiveDifficulty.test.tsx` line 130): the control's name is what changed. The locked-row query keeps checking the control is absent, under its new name. No other existing assertion changed; the fact's exact-equality test (`test_a_built_book_with_no_section_finished_says_none_came_yet`) holds because the new key is present only when it says something.

## What I ran

Every Python run through the scratch wrapper (`env -i`, empty `HOME`/`CODEX_HOME`/config dir) as `uv run --no-sync pytest -q -n 1 -p no:cacheprovider` from a script file that refuses an empty target list, in a 3G scope, one at a time; every npm/npx run through the same wrapper with the shared npm cache in a 5G scope.

- Step 0's reproduction of the list (a throwaway test, deleted): the reserved question first on `read_due_queue`'s list, the answered one on it with its due time eleven days on, all three still on it after the second answer.
- Python fail-first: `tests/test_first_questions_today.py -k "askable or come_back or carries_them or says_nothing_new"`: **3 failed, 1 passed**; after: `tests/test_first_questions_today.py`: **32 passed**.
- After the sidecar commit: `tests/test_identity_pins.py tests/test_structure_ratchets.py`: **348 passed** (no pin, no ratchet moved); `tests/test_architecture.py`: **18 passed**.
- Vitest fail-first (sources put back from `HEAD`): desktop `TodayPlace.test.tsx FeedbackScreen.plan.test.tsx dailyPlan.test.tsx -t UX-44`: **7 failed, 3 passed**; phone `Today.plan.test.tsx -t UX-44`: **3 failed**; the rating row's two files on the old label: **2 failed, 11 passed**.
- Desktop: `npm run typecheck` exit 0; `npx vitest run --maxWorkers=4`: **Test Files 315 passed (315), Tests 3276 passed (3276)**; `npm run frontend:build` exit 0, "✓ built in 3.09s".
- Phone: `npm run typecheck` exit 0; `npx vitest run --maxWorkers=4`: **Test Files 42 passed (42), Tests 427 passed (427)**; `npm run build` exit 0, "✓ built in 1.17s".
- `scripts/affected_tests.py --files src/learnloop/content/pipeline/add_source.py` listed 557 files. I ran every test file whose name contains today, queue, plan_keep, section or first_questions, with the affected ones whose names contain add_source, source_library, status_line, ux_phase1 or library (36 files: **466 passed, 3 skipped**), and the affected ones whose names contain empty_first_build, keep_ahead, reread, ingest_runner, apply_recovery, sidecar_contract, desktop_rpc_contract, mobile_rpc, mobile_v2_plan, reader_progression, section_done, study_map, auto_build or cert (12 files: **363 passed, 5 skipped, 1 error**). The error was at teardown of `test_mobile_v2_plan.py::test_a_none_origin_never_enters_the_device_branch`: the thread guard found the post-attempt embed thread a "don't know" answer starts still running after its 2 s grace (`database is locked` in a background read under the chunk's load); the file alone: **13 passed**. Nothing on that path reads a book's facts.
- Gates: `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`, `test_mobile_allowlist`: **718 passed** (no pin, golden, ratchet or snapshot moved). `test_test_layout` alone: **3 passed**. `test_architecture` alone: **18 passed**. `ruff check`: **All checks passed!** `lint-imports --no-cache`: **Contracts: 43 kept, 0 broken.** `scripts/check_gate_partition.py`: **collected 31975: landing 31910 + arc_close 65**. `git diff --check`: exit 0.
- No new TypeScript file (`desktop_validate.py`'s counts do not move); no vault reference regenerated.

## What a walk must check

The patient first-day persona on the live route (a fresh library, one web chapter, one section, eight topics), as in the measurement:

1. Once the first topic's three questions apply: Today "3 questions from what you read in “…” are ready. More are being written (1 of 8 topics done)." with Begin ↵; Begin opens one of them.
2. Answer it. On feedback, under Next, **"next: *the topic*"**, not "today's plan is done"; **Next opens the second question at once** (no Today in between).
3. Answer the second, right. If its answer reserved the third for a later check and no other topic has applied yet: feedback says "today's plan is done", Next goes to Today, and Today says **"◐ Writing questions from what you read in “…” · 1 of 8 topics done" / "Keep reading meanwhile."** with Continue reading and **no Begin**. If a second topic applied meanwhile: Next names its topic and opens one of its questions.
4. When the next topic applies (no press): Today "3 questions … are ready …", counting only the new ones; **Begin opens a question never answered**, never one answered minutes ago, never the one kept for the later check. Repeat through further topics: the number follows each topic and each answer.
5. Once everything written is answered and the writing has ended: "Nothing from “…” is up today. More questions come as you finish sections."
6. The full list (l) still shows the answered and the reserved questions, each "coming back later today" (unchanged: UX-44b, UX-44c); note whether the persona picks the reserved one there.
7. The rating row's ×: its name reads "hide easy · about right · hard for this session".
8. The phone, with an empty plan, at steps 3 to 5: the same counts and lines as the desktop, Keep going the only action.

## Not verified

- No app, browser, server or model ran: the screens are vitest on fake RPCs (Today on its test harness's fakes, feedback through the real client and query cache with a fake transport), the fact pytest on house fakes, seeded rows and self-graded answers. The reservation in the fact's tests is a `followup_tasks` row written with the store's own `create_followup_task`, not the certification step (step 0's reproduction ran the real certification scheduling, for the list only).
- That `later_item_ids` reaches the desktop as `laterItemIds`: read from the sidecar's existing camel-casing of the line (`item_ids` → `itemIds` today), not run through the sidecar.
- Today's books are read with the stale-while-revalidate rule: on the way back to Today after an answer, a book card read before that answer is shown until its re-read lands, so a reservation made by that answer can be counted for that moment (the answered question itself is kept out by the list, which every answer invalidates). Next reads both afresh before it opens anything.
- With the plan off (its kill switch), feedback's Next still opens the head of today's queue (`useNextQueueItem`), which can be a question answered minutes ago; that path was not changed (the walk ran under the plan).
- The phone's Next after an answer asks the plan only; with the plan done it goes back to Today, which now says the true line. A phone route into the book's questions is not added here.
- The reserved question picked from the full list (what it does to its check) was not run.

## Found and not fixed here

- **UX-44b** (ledger): Today's routine list carries the question a certification cold probe keeps for its check, as an ordinary new question, and the full list lets the learner pick it; withholding it is a serving rule (the quick check and `find_practice` already do), outside this task's bounds.
- **UX-44c** (ledger): the full list says "coming back later today" for a never-answered question and for one answered with its next due time days on alike; and a done plan's "there's more for today" counts the rows waiting to come back.

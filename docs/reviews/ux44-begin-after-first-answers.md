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

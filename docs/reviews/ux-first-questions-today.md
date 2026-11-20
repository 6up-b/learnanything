# First questions arrive: Today offers them, or says what must happen first

The screen half of the UX audit's stage "First questions arrive" (`ux-journey-audit-2.md`: F20, P11; the backend half is UX-13, `ux13-first-questions.md`). Branch `ux/first-questions-today`, from main `9a91561184`.

## Step 0: why no first-day learner got a question from Today

Read with read-only connections (`file:…?mode=ro`) from the five walks' synthetic vaults (`fixtures-local/ux-walks/<walk>/vault/state.sqlite` in the audit worktree: `ingest_batches`, `ingest_jobs`, `reader_section_progress`, `reader_authored_questions`, `practice_item_state`, `daily_plans`, `source_document_units`, the vault's `subjects/*/practice-items/`) and their analyst logs (`steps.jsonl` with each step's observation). Times are the walks' clock (UTC).

| Walk | What the build wrote, when | Practice questions in the vault | Sections finished | Today's plan after that | What Today said last | Why nothing was offered |
|---|---|---|---|---|---|---|
| student-2 | chapter (one section, "Document", 59 passages) added 00:34:27; inventory failed, Try again at #37 (00:36:38) worked; the synthesis pass failed at 00:40:06 (10,352 > 10,000, UX-13) | 0 (no `practice-items/` files, no `practice_item_state` rows) | none (12 of 59 passages seen; no quick check written) | `normal` plan built 00:34:10, before the book existed, closed "Nothing else worth doing fits today."; `keep_going` 00:35:29, closed the same way; none after | "Questions for “…” are on their way" (#53, 00:37:33); at #83 (00:41:20) the app's tabs had scrolled off (UX-15), so the failure was never seen | the build failed (UX-13, fixed on main since), and it would have written no practice questions anyway (below) |
| retainer-2 | three sources; their builds waited for the OK until #61 (00:47:19); the chapter's inventory failed at 00:48:19 ("inventory output exceeded its configured token budget", not retried: UX-13); one elevator-paradox copy still inventorying (4 of 6 windows) and the other queued at the walk's end | 0 | none (elevator copy 2, section u2: 7 of 7 passages seen, its quick check dismissed with "don't bring this back" at #84) | `normal` 00:44:32 and `keep_going` 00:47:19, both closed empty, both before any build ended | "Couldn't get questions ready for “…”" (#85) | builds failed or still running; and a section read through is not a finished section (below) |
| expert-1 | chapter (one section) added 00:49:51; inventory failed, retried by the learner at #20 (00:51:11); synthesis applied 00:54:26: 6 concepts, 8 facets, 6 topics (learning objects), 6 task blueprints | 0: the build's `item_counts` has no `practice_item` | none (12 of 59 passages seen) | `normal` 00:49:31, `keep_going` 00:53:50, both closed empty, both before the build applied; none after | "Everything you've read has its questions. Reading on brings more." (#73, #78), read as "practice is ready" | the build applied and, by design, wrote no practice questions; no section was finished, so none were written |
| project-1 | chapter added 00:57:16; the build completed at 01:01:29 as a proposal waiting for a look (`auto_applied_item_ids: []`, 14 items for review, after the goal box made topics of its own at #20) | 0 | none (12 of 59 passages seen) | `normal` 00:56:28, closed empty; the learner never returned to Today after #27 | "Questions for “…” are on their way" (#25, #27) | the build was not applied (it waited for a look) and wrote no practice questions; no section finished |
| notes-1 | transcript applied 01:11:09 (5 topics, 5 blueprints); flashcards still in synthesis, trace-and-determinant queued at the walk's end | 0 | none: the transcript (one section, 6 of 7 passages seen) had its quick check written (01:11:33) and answered (01:12:08, "compare with the source"), but "done for now" was never pressed | `normal` 01:06:30, `keep_going` 01:08:35, both closed empty, before any build ended | "Questions for “Trace and determinant” are on their way" (#96: a building book ranks above a built one) | as expert-1, one press short: the quick check answered but the section not finished |

In none of the five vaults does a single practice question exist. The plan's closed state, the daily budget, goals and eligibility played no part: there was nothing to plan.

### The rule: when a new question may be practised

1. **The first build writes no practice questions.** A book added through Add is built "as you read" (`add_source.py`, `_default_brief({"practice_items": "as_you_read"}, …)`): the synthesis is told to emit an empty `practice_items` list (`content/synthesis/ai_contracts.py`, "When `brief.practice_items` is `"as_you_read"`, output an EMPTY…"). It writes topics, ideas, facets and question plans (blueprints). The card's "Writing questions for this article" and Today's "Questions … are on their way" describe that build.
2. **A section's practice questions are written when the learner finishes the section**, once: `reader.mark_section_progress` with `completed: true` stamps `reader_section_progress.generation_batch_id` and queues a `practice_expansion` job for the topics whose sources cite that section (`learnloop_sidecar/handlers/reader.py`, `reader_mark_section_progress` → `_trigger_section_generation`; `learnloop/reader/reader_progression.py`). Three questions per topic at most (`handle_practice_expansion`, `target_items_per_lo=3`); grounded rows the model routes to `auto_apply` apply at once, others wait for a look (`content/proposals/proposals.py`, the review policy).
3. **What finishes a section.** On the desktop, only the Reader's guide rail: the section's quick check answered and compared, then "done for now" (`GuideRail.tsx` `AuthoredQuestionCard` → `completeSection`), or a choice on a placed section question (`SectionQuestionCard.choose`). Reading every passage ticks the section in Contents ("read") but sends no completion (`useReadingProgress.ts`: only `completeSection` sends `completed: true`). On the phone, "Done with this section" / "Next section" finishes it (`apps/learnloop-mobile/src/read/ReaderScreen.tsx`, `report(true)`).
4. **Once applied, they may be practised the same day.** A new question is never-attempted material on a topic with no evidence: placement marks it new material (`scheduling/scheduler.py` `placement`), so the cold-start gate lets it through (`cold_start_gate`), and it is in today's list (`get_today_queue`). The job's completion bumps the queue revision (`runner.py`, `_QUEUE_AFFECTING_JOB_TYPES`), so a Today on screen reads the list again. A plan already closed for the day does not rebuild by itself (by design, the shell's ruling R1); today's list and Keep going reach them.

F20's "questions come as you read sections" is therefore not exact: they come when a section is **finished**, and on the desktop finishing means finishing its quick check.

### What this means for the fix, and the stop rule

The cause in the walks is (a) builds that failed or were still running (UX-13, on main) and (b) the as-you-read rule itself: no walker finished a section, so no question was ever written. That is a rule about when questions are written, not a defect in when written questions become practisable (4 shows they are practisable at once) or in the plan not seeing them. So this task does not change it: Today says the rule in plain words and offers the allowed step (Continue reading), names the questions once they exist, and offers them with Begin.

One finding is close to the stop rule and is reported, not fixed (UX-29 below): on the desktop, a section read to its end shows as read but writes no questions unless its quick check is finished. None of the five walks reached a section's end, so it was not their cause; it will be the next learner's.

## Commits

| Commit | What |
|---|---|
| `fb8c8ed520` | A: the facts on the book card's line, and the revision bump when a build ends |
| `17bcaeaa62` | B: Today (desktop simple shell) uses them |
| `c94a8dd812` | C: the phone's empty Today says the same sentences |

This record and the ledger rows are the last commit.

## A. Facts on the book card's status line

All additive keys on `source_status_line` (`content/pipeline/add_source.py`), present only where they say something; the line's text, tone and action are unchanged, so an older screen reads what it read. The sidecar sends them camel-cased (`statusLine.progress`, `.minutes`, `.retried`, `.questions.itemIds`, …; `apps/learnloop-tauri/src/api/dto.ts`, `ReadingQuestionsDto`). No stored row, schema, migration, tag, prompt or config field changes.

| Fact | On which line | Where it comes from |
|---|---|---|
| `progress: {done, total}` | a build under way (tone `working`, "Writing questions for …") | `build_progress(jobs)`: the build batch's own steps, each inventory model window and each synthesis pass. Inventory reports windows finished (`current_window`); the synthesis reports the pass it is on, so its last pass counts only when the job completes. A job not started counts one step: exact for a first document (one window, one pass); a big book's total can grow when its synthesis starts. None once a step stopped. |
| `minutes` | the same, only where measured | `build_minutes` (split out of `build_minutes_phrase`, whose words are unchanged): the median, over this library's last five finished automatic builds, of each build's time from start to end per section in its scope, times this build's sections. A library's first build has no measurement, so no duration is said (P11's "about 2 minutes" is not given there). |
| `retried: bool` | a stopped build ("… need another try", Retry); `false` on a planner that stopped | `runner.retried_on_its_own(row)`: the automatic-retry rule (UX-13) read back from the stored job row. Nothing records the second try, but the stored failure is the second try's whenever the job retries on its own and its stored error code is one a fresh try cures (the code names of `AIProviderUnavailable`'s family without `AIInterrupted`'s, `InventoryValidationError`'s, `timeout`, `budget_exceeded`). A code this process never imported reads as not retried, so it never claims a retry that did not happen. Derived, not written: no stored-row change. |
| `questions: {count, item_ids, sections, writing, failed, to_look_at, section_count}` | a built book's "come up as you read" line always; any other line once a finished section gave something | `reading_questions`: the reading's finished sections (`reader_section_progress.completed_at`) → each one's generation stamp → its `practice_expansion` job → the job's proposal → its practice items accepted and applied and still in the vault, not retired. `writing`: sections stamped `enqueuing`/`deferred_to_primary` or whose job is queued or running; `failed`: sections whose job failed, with `resume_id`, the batch Today resumes; `to_look_at`: written questions waiting for a look; `section_count`: the reading's sections (one: a whole web page, labelled "Document"). |
| a build's end | — | `runner._refresh_batch`: a batch of workflow `bootstrap_synthesis`, `append_synthesis` or `practice_expansion` that becomes terminal (completed, failed, blocked, cancelled) bumps `queue_state.revision`, the token the shell reads every 3 s on every screen (`useQueueRevisionPoll`). Before, only a *completed* `practice_expansion` (and other queue jobs) bumped it, never a build, never a failure. No polling added. |

The failed section's key is `resume_id`, not `batch_id`: the sidecar walks responses for `batch_id` keys to relay model-fallback offers (`server.py` `_BATCH_KEYS`), and a card's fact must not start that.

## B. Today (desktop, simple shell)

`app/todayCause.ts` now reads the facts; `TodayPlace.tsx` renders them. Every state, its words and its action (the title is the book's; "…" stands for it):

| State | When | Words | Action |
|---|---|---|---|
| First questions on today's list | today's list has items, and some are a book's `questions.itemIds` | "2 questions from “Conditional probability”, the part you read. More come as you finish sections." (one section read of several); "1 question from what you read in “Symmetric Matrices and Variance”. More come as you finish sections." (a one-section reading, or several sections) | **Begin ↵** (and Enter): opens the first of them in today's list order, as a pick from the list (`openFromList`: a session for the plan's minutes first when none is open) |
| Today's list has other questions | list has items, none from a book's reading | Today's list still has questions, if you'd like some. (unchanged) | Open today's list |
| Waiting for the OK | unchanged | Questions for “…” are waiting for your OK. | Give your OK · what's sent ▸ |
| No AI | unchanged | LearnLoop needs an AI connected to write questions for “…”. | Connect |
| A build stopped after its own retry | problem line with `retried: true` | Couldn't get “…” ready for questions, after trying twice. Try again, or keep reading: nothing is lost. | Try again (`source_action` retry) · what's sent ▸ |
| A build stopped, no retry | `retried: false` | Couldn't get “…” ready for questions. Try again, or keep reading: nothing is lost. | Try again · what's sent ▸ |
| Getting a book ready failed (import, no fact) | problem line, retry "Try again"/"Retry" with no `retried` (label match kept only here) | Couldn't get questions ready for “…”. (unchanged) | Try again · what's sent ▸ |
| A finished section's questions stopped | `questions.failed` | Couldn't write the questions from “Section”. Try again, or keep reading: nothing is lost. (or "… from what you read in “…”.") | Try again (`resume_ingest_batch` on `resumeId`, the Activity's own resume) · what's sent ▸ |
| Needs a look | unchanged; also written questions only waiting for a look | “…” needs a look in your Library. | Open Library |
| A build under way | tone `working` | waiting indicator: "Getting “…” ready for questions · 1 of 2 steps done · usually about 4 min" (amount only with `progress`, time only with `minutes`; "usually under a minute" below one), then "Questions come as you finish sections. Keep reading meanwhile." | Continue reading, beside the line from the first moment |
| A finished section's questions being written | `questions.writing` | waiting indicator: "Writing questions from “Section”, the part you read…" (or "… from what you read in “…”…"), then "Keep reading meanwhile." | Continue reading |
| Only past exams | unchanged | LearnLoop writes questions from what you read. Add a book, paper or lecture to read. | + Add |
| Built, no section finished | `questions.count` 0 (or an older sidecar with no fact) | Your first questions come when you finish a section of “…”: read to its end and finish its quick check. | Continue reading |
| Questions from reading, none on today's list | `count` > 0, none listed | Nothing from “…” is up today. More questions come as you finish sections. | Continue reading |

Replaced: "Questions for “…” are on their way. Keep reading meanwhile." and "Everything you've read has its questions. Reading on brings more." (F20: read as "practice is ready"). Why not P11's "Writing questions for “…”" for the build: step 0 shows the build writes no question to practise; the card keeps its own sidecar words (UX-30). Order when books differ: list first; then OK, no AI, a stopped build, a stopped section, needs a look, a build under way, a section being written; then no reading; then (phone only) questions written; then built-with-none-finished; then none up.

The waiting indicator (`components/Waiting.tsx`) is the status region of a wait cause (its frame is not one too); Today is not the Reader, so its mark moves (reduced motion stills it). "Practise for this goal" with nothing ready says the same causes after its lead ("Nothing for this goal is ready to practise yet: your first questions come when you finish a section of “…”: …").

**A build that ends elsewhere.** Today subscribes to the shell's queue-changed signal (`subscribeQueueChanged`) while it shows a cause and reads the books again on it. With A's bump, a build that ends while the learner is in the Reader or the Library is a revision change the shell sees; on the way back to Today (or at once, if Today is shown) the line follows it, no press and no new poll. The 5 s re-read while a wait shows is kept and now covers a section being written too.

**Label matching.** `todayCause` matched the sidecar's labels in three places: "Retry"/"Try again" for failures, "Review" for the OK. A stopped build is now told by `retried`; the label set stays only for the import failure ("Try again") and an older sidecar, which carry no fact. The OK's "Review" stays: no fact exists for it (the AI connection's `needs` is preferred when known, as before).

`CONSENT_ACTION`, `SIDECAR_CONSENT_LABEL` and `readableTitle` moved from `components/BookCard.tsx` into `app/todayCause.ts` (BookCard re-exports them), so the module is pure and the phone can import it. No new TypeScript file: `desktop_validate.py`'s counts do not move.

## C. The phone

`apps/learnloop-mobile/src/today/PlanToday.tsx`: when the day's plan has nothing in it (no planned question, no reading, no block), the phone reads the books (`get_source_library`, already allowlisted, the Read tab's call; the new fields ride on it, so the host's allowlist is unchanged) and says the shared `causeSentence` under "Nothing planned for today." (in place of "Done for today."). Today's list is not read there (`listUnknown`), so a book's questions are said by how many were written ("5 questions from “Conditional probability”, the part you read. More come as you finish sections."), with no Begin of its own; Keep going stays the action. A wait is the same sentence, without the moving mark (the shared indicator is the desktop's component). A failed read says nothing. Nothing else on the phone changes.

## Tests (fail first)

| File | Tests | On the branch's base (sources put back with `git show HEAD:…`, restored after) |
|---|---|---|
| `tests/test_first_questions_today.py` (new) | 12: progress counted from windows and passes (plain rows); a building book's line carries progress and no unmeasured time; the measured time; `retried_on_its_own` on plain rows; a build stopped after its own retry (`retried: true`) and one stopped by an interruption (`false`); a built book with no section finished (`questions` with count 0); a finished section's questions while written and once written (2 applied, 1 waiting for a look); a stopped section with its `resume_id`; another state's line carries `questions` only once there is something; a stopped build and a finished build each bump the revision | 12 of 12 failed: the two pure tests on the missing functions, `KeyError` for `progress`, `minutes`, `retried` (2), `questions` (4), and `assert 0 > 0` for both bumps |
| `apps/learnloop-tauri/src/screens/today/TodayPlace.test.tsx`, new describe "First questions arrive (P11, F20)…" | 12: a build under way (amount, time, action from the first moment, the wait is the status region); no time when unmeasured, "under a minute"; stopped after trying twice and without; built with none finished; a section being written; first questions on the list with Begin (pick `pi_1` from the list, a session started); Enter is that Begin; a one-section reading named by its book; none up today; a stopped section's Try again resumes its batch; a queue-changed signal rereads the books with no press (within 2 s, before the 5 s re-read); plain words | 11 of 12 failed; the plain-words guard passes on both (the old words were plain too) |
| the same file, stage 3's tests changed on purpose | 5 assertions (below) | 5 failed against the new code before they were changed |
| `apps/learnloop-mobile/src/today/Today.plan.test.tsx`, new describe "first questions arrive (P11)…" | 5: built with none finished, under "Nothing planned for today.", Keep going stays; questions written, no Begin; a build under way; a day with work reads no books, a failed read says nothing; plain words | 5 of 5 failed |
| `apps/learnloop-tauri/src/copy/denyList.test.tsx` | the stage-3 cause list gains every new state and each wait's two lines | (extended guard) |

**Assertions changed, and why** (all in `TodayPlace.test.tsx`; the words changed on purpose, per step 0):
- "questions being written: on their way…": now expects "Getting “Symmetric Matrices and Variance” ready for questions" in the waiting line and "Questions come as you finish sections. Keep reading meanwhile."; still checks no what's-sent link and Continue reading.
- "everything read has its questions…": now expects the finish-a-section rule and that "Everything you've read" is absent; Continue reading unchanged.
- "an open plan with no rows says its cause too": "are on their way" → the waiting line's "ready for questions".
- "a goal whose books' questions are all written": the goal's lead followed by the finish-a-section rule.
- Keep going's "nothing left to plan": "Everything you've read…" → "Your first questions come when you finish a section of".
- `denyList.test.tsx`: the old `all_read` kind is gone; `failed` and `on_the_way` causes carry their new fields.

## What I ran

Every Python run through the scratch wrapper (`env -i`, empty `HOME`/`CODEX_HOME`/config dir) as `uv run --no-sync pytest -q -n 1 -p no:cacheprovider` from a script file, in a 3G scope, one at a time; every npm/npx run through the same wrapper in a 5G scope.

- New backend file: 12 passed (fail-first: 12 failed, above).
- Nearest backend files (`test_ux_phase1_auto_build`, `test_first_questions_arrive`, `test_ux_phase1_usability_round1/2`, `test_ux_phase1_review_fixes`, `test_keep_ahead_append_units`, `test_reread_safety`, `test_glm_ocr`, `test_keep_local_retired`, `test_inventory_output_allowance`, `test_host_queue_revision`, `test_ingest_runner`, `test_apply_recovery`, `test_ux_phase1_add_source`): 412 passed.
- `tests/test_identity_pins.py` after the backend commit: 342 passed (no pin moved).
- `scripts/affected_tests.py --files add_source.py runner.py` listed 661 files. I ran the 74 whose names contain inventory, ingest, add_source, synthesis, article, budget, auto_build, ux_phase1, build_plan, runner, append, checkpoint, spend, transport, quick_add, keep_ahead, reread, glm, study_map, cost, retry, progressive, book, first_questions, reader_progression, apply_recovery, desktop_rpc_contract, sidecar_contract, daily_plan_build, vault_watcher, question_queue, question_promotion, learner_text_gaps_review, host_queue and the mobile files that read the queue revision (mobile_rpc, mobile_handoff, mobile_host_coexistence, mobile_jobs, mobile_v2_plan, mobile_two_process, secondary_attach, capture_route_recovery), in two chunks with `-m "not arc_close"`: 804 passed; 549 passed, 5 skipped.
- Gates: the new file with `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`: 395 passed (no pin, golden or ratchet moved). `test_test_layout` alone: 3 passed. `test_architecture` alone: 18 passed. `ruff check`: all checks passed. `lint-imports --no-cache`: 43 kept, 0 broken. `scripts/check_gate_partition.py`: 31,779 collected, landing 31,714 + arc_close 65.
- Desktop: `npm run typecheck` exit 0; `npx vitest run --maxWorkers=4` 311 of 312 files, 3169 of 3170 tests: `SketchFigure.test.tsx > draws a new sample with another seed` timed out at 12 s under the full run's load; alone it passed (19 of 19); `npm run frontend:build` exit 0.
- Phone: `npm run typecheck` exit 0; `npx vitest run --maxWorkers=4` 41 files, 414 tests passed (`desktopImports.test.ts` included: `todayCause` reaches no Tauri binding); `npm run build` exit 0.

## What a walk must check

The five first-day personas, each on a fresh library with the live route (UX-13's ceilings and retry are on main), with the step each should now reach:

- **student-2 (a chapter, then a past exam).** After Add, Today: the waiting line "◐ Getting “Understanding Linear Algebra …” ready for questions · 0 of 2 steps done" (no time in a new library), then "1 of 2", with Continue reading beside it. Read the chapter in the Reader; when the build ends there, coming back to Today shows the built state at once (no "on their way" left over): "Your first questions come when you finish a section of “…”: read to its end and finish its quick check." If the synthesis stops after its own retry: "Couldn't get “…” ready for questions, after trying twice. Try again, or keep reading: nothing is lost." **Step to reach:** read the chapter to its end, answer the quick check, compare, press "done for now"; Today then shows "◐ Writing questions from what you read in “…”…", then "N questions from what you read in “…”. More come as you finish sections. [Begin ↵]", and Begin (or Enter) opens a question.
- **expert-1 (knows it, wants to test out).** The same, with a learner who skips ahead: Today must never say "Everything you've read has its questions"; with nothing finished it says the finish-a-section rule. Check "Practise for this goal" says the same rule after its lead.
- **retainer-2 (two books, OK first).** "…are waiting for your OK" until Give your OK; then the first book's waiting line. A web article read to its end in one section shows ✓ in Contents but writes nothing until its quick check is finished (UX-29: note whether the person finds "done for now").
- **project-1 (a project goal).** A build that ends waiting for a look shows "“…” needs a look in your Library."; once applied, the finish-a-section rule.
- **notes-1 (own notes).** The transcript's quick check: answer, compare, then **"done for now"** (the press notes-1 did not make); Today then names "N questions from what you read in “Lecture 07 Transcript”" with Begin while other notes still build (the question offer ranks above a building book).
- **phone (any of them, after the desktop's Add).** With an empty plan, Today reads "Nothing planned for today." and the same sentence as the desktop; once questions are written, "N questions from …" with Keep going as the only action; Keep going should serve them (not verified here).

## Not verified

- No app, browser, server or model was run; every state above is from vitest on fake RPCs and pytest on house fakes and seeded rows (a section's questions were seeded as an applied proposal, not written by the real section job).
- That a section's questions, once applied, are on `get_today_queue` the same day was read from the code (step 0, rule 4: placement's new material and the cold-start gate), not run end to end; nor that the phone's Keep going serves them.
- `retried` is derived from the stored error code: a failure class not imported by the sidecar's process reads as "not retried" (conservative); a job that failed while the app was quitting (the runner halted before its retry) would read as retried. Neither was exercised.
- `progress` for a book whose synthesis has several passes: the total grows once the synthesis starts (by design, documented); only one-pass builds were exercised through the runner.
- The turning mark in the real webview and what a screen reader announces from the wait's polite region (as in `ux-waiting.md`).
- The Library showing section questions that wait for a look (Today sends "Open Library" for them); not walked.

## Found and not fixed here

- **UX-29** (ledger): on the desktop, a section read to its end writes no questions unless its quick check is finished; a decision for the orchestrator and the owner (it changes when question writing starts), not this step's.
- **UX-30** (ledger): the book card's "Writing questions for …" while the first build writes no question to practise; Today now says "Getting “…” ready for questions".

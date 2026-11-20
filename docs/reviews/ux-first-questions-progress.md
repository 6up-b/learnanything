# Question writing you can follow: how far it is, what is ready meanwhile, a topic that could not be written

The screen step after UX-31, UX-33 and UX-37 (`ux31-section-done-before-build.md`, `ux33-section-questions-in-parts.md`, `ux37-first-questions-first.md`): a finished section's questions are written one topic at a time and each topic's questions apply at once, so Today can offer the first while more are written and say when a topic's could not be. Frontend only (`apps/learnloop-tauri/src`, the phone through the shared `todayCause`); no sidecar change. Branch `ux/first-questions-progress`, from main `1119b97462`.

| Commit | What |
|---|---|
| `e16e06cd53` | Today (desktop simple shell): the writing amount, questions ready while more are written, the failed-topic line with Try again, the first build's second line |
| `306c125837` | The phone's empty day: the same sentences (tests only: they come through `todayCause`) |
| `1ca70ac188` | The first-build line only on a build's own line, never on the sections' count the sidecar copies onto "Chapters found" |

This record and the ledger row UX-38 are the last commit.

## Step 0: which fields carry each fact

Read from `src/learnloop/content/pipeline/add_source.py` (`reading_questions`, `source_status_line`), what they read (`content/pipeline/jobs.py` `handle_practice_expansion`; `content/proposals/proposals.py` `_apply_authoring_parts`; `content/pipeline/runner.py` `resume_batch`), and `apps/learnloop-tauri/src/api/dto.ts`. The sidecar camel-cases the line (`statusLine.questions.itemIds`, …); the desktop already receives every field below on `get_source_library`'s cards, and the phone on the same call through the host.

| Fact | Field | How it is made |
|---|---|---|
| Parts done and total of a section's writing | `statusLine.questions.progress` `{done, total}` | Each finished section's `practice_expansion` job adds `total_windows` (or, before it reports, its payload's `learning_object_ids` count) to `total` and `current_window` to `done`. The handler reports `current_window` = topics finished **without an error**, `total_windows` = the section's topics (`_apply_authoring_parts.report`). It is the **sum over every finished section of the reading**, the running one and earlier ones; see UX-38. Not declared in `ReadingQuestionsDto` before this step (UX-33 named that); added there as optional. |
| The same, on the line | `statusLine.progress` | `source_status_line` copies `questions.progress` onto the line when the line has none of its own (`setdefault`): a build under way keeps the build's steps. On "Chapters found" (a planner choosing chapters) it is the sections' topics; see UX-38. |
| Questions already applied and practisable | `questions.count`, `questions.itemIds`, `questions.sections` | Accepted, applied practice items of every part proposal (`question_parts[].patch_id`, `result.patch_ids`), still in the vault and not retired, during running, failed and completed jobs (UX-37). Practisable today = those ids on today's list (`get_today_queue`, which the desktop reads; the phone does not). `sections`: labels of finished sections that gave at least one. |
| Writing still going on | `questions.writing` | Labels of finished sections stamped `enqueuing`/`deferred_to_primary`, or whose job is queued or running (an automatic retry included). |
| A topic failed, its label and resume id | `questions.failed[]` `{label, resumeId}` | **One entry per section**, not per topic. A section whose job has topic errors (`question_parts[].error`, set for a model failure and for a saved part with rows refused or held for review): label `"Section: Topic A, Topic B"` (the failed topics' titles joined); a section whose job stopped with no topic error: label `"Section"`. `resumeId` is the section's batch. An entry appears **while the job still runs** (the first pass goes on to later topics after a failure) as well as after it stopped. |
| Measured build time | `statusLine.minutes` | Only on a build's own working line, and only where the library has a finished automatic build to measure (`build_minutes`: none before the library's first). |

**What a resume does** (`runner.resume_batch`): it requeues only jobs that are failed, blocked or cancelled. A section job still running is left as it is, so Try again on a failed entry whose section is still being written would do nothing.

### Facts the brief's states need that are not in the reply (stops)

1. **How many topics failed.** "With several failed, the count": the count of failed topics is not a field. It is only inside one label per section (`"Section: A, B"`), and titles can hold commas; `progress.total − progress.done` equals it only once that section's writing has stopped and no other finished section is in the sum. **Stopped on the count.** The line says no number and is true for one topic or several: **"Not every topic's questions could be written."** (in place of the brief's "One topic's questions couldn't be written."). The missing field would be a per-entry topic count (for example `failed[].topics`).
2. **Try again while that section is still being written.** The resume action exists (`resumeId`), but it requeues nothing while the job runs (above), and no field says whether an entry's job is still running. It is told by the labels: an entry belongs to a section still being written when its label is a `writing` label or starts with one followed by ": " (the format `reading_questions` writes). While it is, the failed line shows **without** Try again; once the writing stops (the job's end bumps the revision Today rereads on), Try again appears beside it. A failed entry of another, stopped section keeps its Try again.

No other stop: every other fact is in the reply.

## States, words and actions

"…" is the book's title, “Section” the finished section's label. "N questions" is "1 question" for one. The amount "· 2 of 8 topics done" / "(2 of 8 topics done)" is said only when `questions.progress` has `total > 0` **and** no other finished section is in that sum: every label of `sections` is in `writing`, and every `failed` entry belongs to a section in `writing`; otherwise no amount ("1 topic" for a total of one). Rows marked *new* are this step's; the others are unchanged and listed for the walk.

| State | When (desktop) | Words | Action |
|---|---|---|---|
| *new* A section's questions being written, with how far | `questions.writing` non-empty, nothing of this book on today's list, the amount attributable | waiting indicator: "Writing questions from “Section”, the part you read · 2 of 8 topics done" (one-section reading: "Writing questions from what you read in “…” · 2 of 8 topics done"), then "Keep reading meanwhile." | Continue reading |
| A section's questions being written, no amount (unchanged) | the same, no attributable amount | "Writing questions from “Section”, the part you read…" (or "… from what you read in “…”…"), then "Keep reading meanwhile." | Continue reading |
| *new* Questions ready while more are written | some of this book's `itemIds` on today's list and `writing` non-empty | "3 questions from “Section” are ready. More are being written (2 of 8 topics done)." / without an amount "… are ready. More are being written." / one question "1 question from “Section” is ready. …" / one-section reading "3 questions from what you read in “…” are ready. …" (a status line, not the moving indicator: nothing is waited for) | **Begin ↵** (and Enter): the first of them in today's list order, as a pick from the list (`openFromList`; a session for the plan's minutes first when none is open) |
| *new* Ready, and a topic could not be written, writing stopped | some on today's list, `failed` non-empty, its section not in `writing` | first line: the unchanged offer "3 questions from “Section”, the part you read. More come as you finish sections." (or "… from what you read in “…”. …") with **Begin ↵**; second line: "Not every topic's questions could be written." | Begin ↵ (and Enter); on the second line **Try again** (`resume_ingest_batch` on the first stopped entry's `resumeId`) and **what's sent ▸** |
| *new* Ready, more being written, and a topic failed meanwhile | on today's list, `writing` and `failed` non-empty, the entry's section still writing | first line: "3 questions from “Section” are ready. More are being written (4 of 8 topics done)."; second line: "Not every topic's questions could be written." | Begin ↵ (and Enter); no Try again until that writing stops (then as the row above) |
| *new* Several topics, or several sections, failed | as above, with more topics in a label or more entries | the same second line (no count: stop 1) | Try again resumes the first stopped entry's batch (as the existing failed-section state does) |
| All failed, nothing ready (unchanged) | `failed` non-empty, nothing of this book on today's list | "Couldn't write the questions from “Section”. Try again, or keep reading: nothing is lost." (its part is the entry's label, so a topic failure reads "… from “Section: Bayes' rule”…", as before) | Try again · what's sent ▸ |
| *new* A new library's first build, after five seconds | a build's own working line with `progress` and no `minutes` | under the unchanged "Getting “…” ready for questions · 0 of 2 steps done", after 5 s (the indicator's `WAIT_LATER_MS`) the quiet second line "The first time, this can take several minutes." | Continue reading, as before |
| A build with a measured time (unchanged) | `minutes` present | "Getting “…” ready for questions · 1 of 2 steps done · usually about 4 min", no second line | Continue reading |
| A working line that is not a build's own (unchanged words) | "Chapters found", or a line whose `progress` equals the sections' copied `questions.progress` | no second line, at any time | Continue reading |

The first-build line needs the build's own `progress` as well as no `minutes` (stricter than "no `minutes`"): "Chapters found" carries no minutes in any library, and it can carry the sections' copied count as its `progress`; neither says anything about the library's first build. The words stand on the walks' measurements (first step about 1 minute, second 3.5 to 7 minutes); the line claims no number.

While the combined state shows writing, Today rereads the books and the list every 5 s (the existing re-read for a section being written) and on the shell's queue-changed signal (each applied topic bumps the revision; the signal also marks today's list stale), so the count and the amount follow the parts with no press and no new poll.

Ranking is unchanged: today's list first (a book's questions on it win, now with the writing or failure beside them), then the OK, no AI, a stopped build, a stopped section, needs a look, a build under way, a section being written, a section waiting.

## The phone

`PlanToday` says the shared `causeSentence` under "Nothing planned for today." when the day's plan is empty; it does not read today's list (`listUnknown`), so "ready" means written (`questions.count`). Where a book has written questions and its writing still goes on or a topic stopped, the cause that was "Writing questions from …" or "Couldn't write the questions from …" is now the combined one, in one paragraph, with no action of its own (Keep going stays the only one):

| State | Phone sentence |
|---|---|
| Writing, with amount | "Writing questions from “Conditional probability”, the part you read · 2 of 8 topics done. Keep reading meanwhile." |
| Written while more are | "3 questions from “Conditional probability” are ready. More are being written (2 of 8 topics done)." |
| Written, a topic not (stopped) | "3 questions from “Conditional probability”, the part you read. More come as you finish sections. Not every topic's questions could be written." |
| Written, more being written, a topic not | "3 questions from “Conditional probability” are ready. More are being written (4 of 8 topics done). Not every topic's questions could be written." |
| Nothing written, the section stopped (unchanged) | "Couldn't write the questions from “Conditional probability”. Try again, or keep reading: nothing is lost." |

The phone shows no first-build second line (its cause is a plain sentence, not the timed indicator).

## Code

- `app/todayCause.ts`: the cause `questions_ready_with_section_work` (the state UX-37 named) with `writing: {progress} | null`, `failedTopics`, `resumeId` (null while that section is still being written); `section_writing` gains `progress`; `on_the_way` gains `firstBuild`; `causeWait` returns `later`; `readyWithWorkSentence`, `causeTopicsFailed`, `TOPICS_NOT_WRITTEN`. Still pure (it now imports `copy/waiting`, also pure; the phone's `desktopImports.test.ts` passes).
- `copy/waiting.ts`: `firstBuildLater`.
- `screens/today/TodayPlace.tsx`: `CauseLine` passes `later` to `Waiting`, and renders the combined state as the offer with Begin plus a `today-cause-failed` line holding Try again and what's sent; Enter is Begin there; the 5 s re-read covers the combined state while it shows writing.
- `api/dto.ts`: `ReadingQuestionsDto.progress?`.
- No new TypeScript file: `desktop_validate.py`'s three counts do not move.

## Tests (fail first)

| File | Tests | On the code before the change |
|---|---|---|
| `screens/today/TodayPlace.test.tsx`, new describe "Question writing you can follow…" | 13: the writing line with amount (a section; a one-section reading, "0 of 1 topic done"); no amount without the fact or with another finished section in the sum; ready while written (sentence, no "More come as you finish sections", Begin picks `pi_1` from the list, the count and amount follow a queue-changed signal: 2 → 3, 2 of 8 → 3 of 8); one question from a one-section reading, Enter is Begin; ready plus a stopped topic (Try again resumes `batch_sec`, what's sent beside it, Begin still picks); a topic failed while still writing (no Try again; it appears once the writing stops, and resumes `batch_sec`); several topics and sections (same line, Try again resumes `batch_a`); all failed, nothing ready (unchanged words); the first build's second line after 5 s only without `minutes` (fake timers: absent at 400 ms and 4,700 ms, present at 5,100 ms), none with `minutes` (6.4 s), none on "Chapters found", none on "Chapters found" carrying the copied count; plain words | first commit's 12: **7 failed** (`Unable to find an element with the text: Writing questions from “Conditional probability”, the part you read · 2 of 8 topics done`; the old offer "2 questions … the part you read. More come as you finish sections." where "are ready. More are being written" was expected, twice; `Unable to find an element by: [data-testid="today-cause-failed"]` twice; "1 question from “Conditional probability”, the part you read…" where "is ready" was expected; `Unable to find … today-cause-wait-later`), 5 passed on both (the no-amount guard, the all-failed control, the measured-time and Chapters-found controls, plain words). The 13th (copied count) on the first commit's code: **1 failed** (`expected <div …> to be null`: the second line showed), 3 passed. |
| `apps/learnloop-mobile/src/today/Today.plan.test.tsx`, new describe "question writing you can follow…" | 5: each phone sentence above, plain words, Keep going present, no Begin or Try again | **4 failed** (the old "Writing questions from ……" or "Couldn't write the questions from …" where the combined sentence was expected; the writing line without its amount), the unchanged stopped-section control passed |
| `copy/denyList.test.tsx` | the stage-3 cause list gains the six new causes; each cause's `later` and failed line are checked too; `firstBuildLater` through `WAITING_COPY` (desktop) and the phone's `shell/a11y.test.tsx` | the file failed to load (`TypeError: causeTopicsFailed is not a function`) |

No existing assertion changed.

## What I ran

Every npm/npx run through the scratch wrapper (`env -i`, empty `HOME`/`CODEX_HOME`/config dir, `npm_config_cache=/home/saturn/.npm`) in `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, one at a time.

- `npm ci`, desktop and phone: exit 0 (install scripts not run, as npm reports by default here; vitest and vite ran).
- Fail-first, as above: desktop `npx vitest run --maxWorkers=4 src/screens/today/TodayPlace.test.tsx src/copy/denyList.test.tsx`: Test Files 2 failed, Tests 7 failed | 109 passed (116); phone `src/today/Today.plan.test.tsx`: Tests 4 failed | 33 passed (37); the copied-count test: Tests 1 failed | 3 passed | 113 skipped.
- After: the same desktop files 337 passed (337); phone 37 passed (37).
- Final, at `1ca70ac188` (this record changes no code):
  - desktop `npm run typecheck`: exit 0; `npx vitest run --maxWorkers=4`: Test Files 315 passed (315), Tests 3254 passed (3254); `npm run frontend:build`: exit 0, "✓ built in 2.70s".
  - phone `npm run typecheck`: exit 0; `npx vitest run --maxWorkers=4`: Test Files 42 passed (42), Tests 422 passed (422); `npm run build`: exit 0, "✓ built in 859ms".
- Not run: no Python (no file under `src/` or `tests/` changed; the step is frontend only). `desktop_validate.py` not run; its counts do not move (no new TypeScript file). Vault references not regenerated.

## What a walk must check

The patient first-day persona (one web chapter, the live route, a fresh library):

1. Add the chapter. Today: "◐ Getting “…” ready for questions · 0 of 2 steps done" with Continue reading; **after five seconds, beneath it, "The first time, this can take several minutes."** (no "usually about"). It should stay through the build (1 + 3.5 to 7 minutes on the walks).
2. Read the section to its end and press "Done with this section" (or finish its quick check). Back on Today: "◐ Writing questions from “…”, the part you read · 0 of 8 topics done" (one-section article: "◐ Writing questions from what you read in “…” · 0 of 8 topics done"). **Wait without pressing anything: the count goes up** (about one topic every 1.5 to 2.4 minutes).
3. As soon as the first topic's questions apply (before the rest are written): Today says "N questions from … are ready. More are being written (1 of 8 topics done)." (up to three per topic) with **Begin ↵**. The number and the amount follow each topic with no press.
4. **Begin opens one of them** (Enter too). Coming back to Today later shows the current count.
5. If a topic fails: "Not every topic's questions could be written." under the offer, with no Try again while the rest are written; once the writing has stopped, **Try again** appears there and asks for that part again (the first questions stay offered meanwhile). Note whether the line ever reads wrong for the number that failed.
6. The phone, with an empty plan: the same sentences under "Nothing planned for today.", Keep going the only action.
7. A second library build (any later book): the line says "usually about N min" and no "first time" line.

## Not verified

- No app, browser, server or model ran; every state is from vitest on fake RPCs. The facts' values on the live route (that `questions.progress` reads "2 of 8" in step order, that `writing` stays set through the automatic retry) were read from the code, not run.
- The label rule that tells a failed entry of a section still being written (`"Section"` or `"Section: …"`) relies on the sidecar's label format; a section whose label itself starts with another writing section's label followed by ": " would be taken for that one (its Try again hidden until the writing stops; nothing wrong is said).
- A book with several finished sections: the amount is hidden where another finished section shows in the fact; one that gave no question and did not stop (its job found nothing to write) does not show and still adds to the sum (UX-38).

- The waiting indicator's turning mark and the polite region's announcement in the real webview (as in `ux-waiting.md`).

## Found and not fixed here

- **UX-38** (ledger): `questions.progress` adds up every finished section and counts a completed job that reported no topics (one that found nothing to write, or one written before the per-topic parts) as 0 done; the sidecar also copies it onto "Chapters found", where Today says it as "N of M steps done" (unchanged words; this step only keeps the first-build line off it). The screen hides the amount where it can tell; the sidecar fix is owed.

## UX-38: the amount belongs to the section being written

Before: `reading_questions` added the reported or payload topic count from every finished section's practice job, including completed and stopped jobs. A completed job that reported no topics could leave `progress` at 0 of its payload total. `source_status_line` copied that sum onto any line without its own progress; Today could then call the topics on “Chapters found” build steps.

After: only an active section job (queued, running, or waiting for input, including an automatic retry) contributes to `questions.progress`. These are the same job sections put in `questions.writing`; stamped enqueuing or deferred sections still have no reported amount. Completed, failed, cancelled, and nothing-needed sections contribute nothing. With no active job reporting a positive total, the fact has no `progress` key, so a completed job cannot leave an unfinished amount on the fact. Two active sections sum their own done and total. The `{done, total}` shape is unchanged.

`_source_status_line` can return: no line; import preparation or failure; changed-reading, reread, exam, or reading-health lines; an unbuilt book's no-questions or needs-look line; “Chapters found” or a stopped planner; AI/consent or cost waiting; an active, stopped, undone, or needs-look build; and the built “Questions for … come up as you read” line. Previously, all of these kinds copied a present `questions.progress` when their line had no `progress` of its own. An active build with its own progress kept that value. Now only the built “Questions for … come up as you read” line receives the copy. An active build still keeps its own build progress. In particular, “Chapters found” carries `questions.progress` inside `questions` but no outer `progress`.

Readers found by searching `src/` and both apps' `src/`: `reading_questions` makes the nested fact; `source_status_line` copies it; the shared desktop `apps/learnloop-tauri/src/app/todayCause.ts` reads `questions.progress` for section-writing and ready-with-work text, and outer `line.progress` for build-step text and its first-build guard. Desktop Today renders that cause; phone Today uses its sentence through the shared cause. No reader depends on completed section jobs remaining in the sum.

Tests were written against unchanged production first. `t.sh tests/test_first_questions_today.py -q -n 2`: **7 failed, 19 passed**. The failures covered stopped/completed jobs retaining progress, a completed empty job at 0 of 3, a completed empty section diluting 2 of 8 to 2 of 11, and “Chapters found” borrowing 2 of 8. After adding a finished third section to the two-active-sections case, `t.sh tests/test_first_questions_today.py -q -n 2 -k two_sections_being_written`: **1 failed** (3 of 15 instead of 3 of 11). The existing active-build line assertion checks that its own 2 of 3 remains.

Verification after the fix, with the supplied isolated wrappers and at most two pytest workers:

- `t.sh tests/test_first_questions_today.py tests/test_section_question_parts.py -q -n 2`: **38 passed**.
- `t.sh tests/test_first_questions_arrive.py tests/test_first_questions_today.py tests/test_library_ask.py tests/test_library_ask_expand.py tests/test_library_ask_review.py tests/test_library_asks_migration.py tests/test_library_exercises.py tests/test_plan_first_transport_today_quiet.py tests/test_today_headline.py tests/test_today_surfaces.py tests/test_tui_today.py tests/test_ux_phase1_add_source.py tests/test_ux_phase3_today.py -q -n 2 -m 'not arc_close'`: **159 passed, 3 skipped, 1 failed**. The failure is `test_the_plan_route_request_is_byte_identical_under_a_ceiling`: its fake HTTP server cannot create a socket (`PermissionError: [Errno 1] Operation not permitted`), so it is not counted as verified.
- `t.sh tests/test_identity_pins.py tests/test_structure_ratchets.py tests/test_mobile_allowlist.py -q -n 2 -m 'not arc_close'`: **680 passed**.
- `t.sh tests/test_test_layout.py -q -n 1`: **3 passed**.
- `py.sh ruff check`: **All checks passed!**
- `py.sh lint-imports --no-cache`: **Contracts: 43 kept, 0 broken.**
- `git diff --check`: exit 0, no whitespace errors.

The desktop's `writingProgress` guard is now stricter than necessary: it still hides an active section's amount when another section has written questions or stopped, although the sidecar sum already excludes that section. Its copied-count equality check also remains, even though “Chapters found” no longer receives the copy; coincidentally equal build and writing counts could hide a first-build hint. Those are notes for a later frontend step; no frontend file changed here. No live UI, network, model, private vault, or landing gate was run.

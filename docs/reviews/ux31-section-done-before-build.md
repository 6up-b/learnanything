# UX-31: a section finished before its book is ready still gets its questions

Found by the verification walk firstq-1 on the real model route (steps 30 to 59), after "First questions arrive" (`ux-first-questions-today.md`) landed: a first-day learner read the article's one section to its end, pressed "Done with this section", and never got a question. Branch `fix/ux31-section-done-before-build`, from main `ece7907885`.

## Step 0: why nothing was queued

Read from the walk's vault with a read-only connection (`state.sqlite?mode=ro`: `reader_section_progress`, `ingest_batches`, `ingest_jobs`), its learning-object files, `persona/report.md` and `analyst/steps.jsonl` (the walk's clock).

| Time | What happened |
|---|---|
| 07:44:49–50 | The article is added; its one section `u1` (59 passages, labelled "Document"). The planner queues the build (`chapter_ids: ["u1"]`, `whole_source: true`). |
| 07:45:53 | The inventory ends; the bootstrap synthesis (the topics) starts. |
| 07:46:34 | Step 30, "Done with this section": `reader.mark_section_progress` with `completed`. `reader_section_progress` for `u1`: 59 of 59 seen, `completed_at` 07:46:34, `generation_batch_id = 'none_needed'`. The Reader said "✓ Done with this section." (nothing queued). |
| 07:49:19 | The synthesis applies: 6 learning objects, each citing passages of `u1` (`span:ext_01M7VYMK9DQQSV1K0K4FW917ZK/s41`, …). No practice item is ever written. |
| 07:50:16 | Step 54, "Build questions for the whole article at once": a planner `auto_study_map` with `chapter_ids: ["u1"]`, completed at once with `{"outcome": "skipped", "reason": "nothing_to_build"}`. |

**Which condition returned "none needed".** `_trigger_section_generation` (`handlers/reader.py`) asked `section_generation_candidates` for the topics citing the section that need questions; `learning_objects_for_section` found none, because the build's synthesis was still running: no topic existed yet. It stamped `none_needed` and returned. The build's status was never consulted.

**Does anything re-evaluate a finished section?** No. The only code that moved a stamp after the completion was the phone's drain (`drain_deferred_section_generations`, on the desktop's start and the Reader's `get_progress`), and it read only `deferred_to_primary`. A build that applied ran `after_auto_build`, which acts on reading requests (keep-ahead), not on finished sections.

**Every value `generation_batch_id` held, and who read it (main):**

| Value | Written by | Read by |
|---|---|---|
| NULL | the progress upsert | `mark_section_progress` (`is None` → trigger); `mark_section_generation`'s `WHERE … IS NULL` |
| `enqueuing` | the trigger's claim, before the enqueue | `reading_questions` (the section is "writing"); the phone drain's hand-back |
| `none_needed` | the trigger, when no topic needed questions | `reading_questions` (skipped: nothing to say) |
| `deferred_to_primary` | a completion on the phone host | the phone drain; `reading_questions` ("writing") |
| a batch id | `set_section_generation_batch` | `reading_questions` (its job: writing, stopped, written) |

`carry_reader_section_progress` copies any of them to a new reading of the same book. `reader.get_progress` sends the raw value to both frontends; neither interprets it.

**What the whole-article press did.** It queued a planner for every outline chapter; `u1` was built, so `_choose_scope` returned nothing and the planner completed as `skipped / nothing_to_build`. The card's line speaks for the newest planner (`latest_planner`), and a skip has no line (`_health_line` → None), so the card showed "Chapters found" while the planner was queued (step 54) and then no line (step 56). Today lost the book's `questions` fact with the line and fell through to its last fallback, "Your first questions come when you finish a section of …" (steps 57-58). (Before the press, steps 47-50, Today said the same from the fact: `count` 0, the `none_needed` section counted as nothing.)

**The phone.** The same defect: the phone host stamps `deferred_to_primary`; the desktop's drain ran the same trigger from that stamp and, before the build applied, swapped it to `none_needed`. And a phone-finished section whose build had applied stayed `deferred_to_primary`, shown on Today as "Writing questions from …", until the desktop's Reader opened that book or the app restarted.

## The rule, before and after

**Before.** A section's questions were written when it was finished, from the topics citing it at that moment; with none, it was settled as needing none, forever.

**After.** A section's questions are still written only when it is finished, from the topics citing it, three per topic at most; nothing about which sections or how many changes. What changes is when "none" is decided:

1. A finished section with topics citing it that need questions: its writing starts at once (as before).
2. With none: if the build of the section's chapter has **settled** (finished, nothing of it waiting for a look, not taken back out; `add_source.section_topics_settled`), it is `none_needed_after_build`. Otherwise it is `waiting_for_build`.
3. When a build's synthesis applies (bootstrap, an append, or a retry that works: `after_auto_build` → `start_waiting_sections`), every waiting section of that book with topics citing it now gets its writing started. One still without (its build left them for a look) keeps waiting.
4. Every read of the books (`get_source_library`: Today and the shelf), the Reader opening a book (`reader.get_progress`) and the desktop's start (`drain_owed_section_questions`) decide what is still owed: a waiting section whose chapter's build has settled (started, or settled as needing none), a phone-finished one, and an older `none_needed` row (below). A waiting section whose build has not settled costs one read of the build's rows, no reading of the book.

Front matter is in no build's own scope: a front-matter section is settled once any build of the book is. A book built through the Ingest screen (no automatic planner) is settled once its study map is applied. "None needed" is never decided on the sidecar's in-memory vault alone: when the build has settled and that snapshot shows no topic, the vault is read again from disk first (the sidecar reloads after a background build only when a read of the books notices it, so a completion that came first read the snapshot from before; `test_a_completion_read_on_a_vault_loaded_before_the_build_applied_still_finds_its_topics` fails on main).

Model work starts only for a section the learner finished (`completed_at` set: every path reads rows of `deferred_section_generations`, which selects `completed_at IS NOT NULL`, or the completion itself). No prompt, scheduling, eligibility, schema, migration or tag changes; no config field.

## The guard against writing twice

One guard, unchanged: every move of `reader_section_progress.generation_batch_id` is a compare-and-set from the value the mover read (`mark_section_generation` from NULL, `swap_section_generation` from any other), and only the winner of the move to `enqueuing` queues anything. Every path takes it (`learnloop.reader.section_generation.start_section_questions`, and the build's `start_waiting_sections`). In the build's path the claim, the queueing (`ctx.enqueue_batch`) and the batch id it names are one transaction, so a section either keeps waiting or has exactly one batch. In the sidecar's paths a failed enqueue hands the claim back to the stamp it came from, as the phone drain did; a first completion's failed enqueue stays `enqueuing`, as before. Nothing is paid twice: a section is queued once, and its job's own retries reuse its checkpoints as any `practice_expansion` does. A failure leaves the section in the existing failed-section state (`questions.failed` with its `resume_id`; Today's "Couldn't write the questions from …" with Try again).

## Old rows

No migration, no stored column. `none_needed` changes meaning: it is now what older versions wrote, possibly while the book's topics were not in yet, and is read as undecided. The first read of the books on the desktop (or the Reader opening the book, or the start) decides each such finished section once:

- its chapter's build has not settled: `waiting_for_build`;
- it was finished after that build ended (`completed_at > ` the build batch's `finished_at`), or the book keeps no build time (built through the Ingest screen): the older answer was decided on the topics and stands, `none_needed_after_build`, with no reading of the book;
- otherwise (finished before or as its chapter's build ended): decided again from the topics, so it gets its writing started or becomes `none_needed_after_build`.

**Trigger chosen: the read of the books.** A build applying is not enough for old rows: a one-section article (the walk's) never builds again, so its row would never be picked up. The read is where the learner looks for their questions (Today, the shelf), so the line they read already says "Writing questions from …"; it happens on the desktop only (never the phone host), and starts model work only for a finished section. The walk's own vault would be picked up on its first Today.

## States and words

The status line's `questions` fact gains `waiting`: the labels of finished sections waiting for the book's build. A line carries `questions` once anything is waiting too. "A finished section is waiting for the book to be ready" (`waiting` non-empty) is now distinct from "no section finished yet" (`count` 0, all lists empty).

| Where | When | Words |
|---|---|---|
| Today (desktop; the phone's shared sentence) | the book is being got ready and a finished section waits | the wait "Getting “Book” ready for questions · 1 of 2 steps done", then "Your questions from “Section” will be written as soon as “Book” is ready. Keep reading meanwhile." · Continue reading |
| Today | a finished section waits and the card says nothing else | "Your questions from “Section” will be written as soon as “Book” is ready." · Continue reading (one-section reading: "Your questions from what you read will be written as soon as “Book” is ready.") |
| Today | the writing starts later | the existing "◐ Writing questions from “Section”, the part you read…", on the shell's queue-changed signal (the build's end bumps the revision), no press |
| Reader, after "Done with this section" | the completion waits for the book | "◐ Your questions from this section will be written as soon as “Book” is ready. They'll be on Today." (still mark) |
| Library, whole-book press | nothing left to build | "All of this article is ready for questions. Each section's questions are written when you finish it." or "All of this article is already being got ready for questions. …" (status line, not a failure) |

A stopped build, an OK or an AI connection still outrank the waiting sentence on Today (their action is what makes the book ready). Today's ranking otherwise: … a build under way, a section being written, then a section waiting.

## The whole-article action

From step 0: on a built article the press queued a planner that could find nothing, and its skip hid the card's line. Now `source_action build_whole_book` first applies the planner's own rule (`add_source.whole_book_state`: chapters not exam material, not front matter, not built or building); with nothing left it queues nothing and answers `notice` (the words above), which the Library shows. With chapters left it starts as before (the card's working line, Today's wait). And `latest_planner` no longer speaks for a planner that found nothing to build, so a skip from any other path (keep-ahead, reconcile) never hides the card's line either.

Separate, filed as **UX-32**: the press writes no question to practise in any case (its build is as-you-read: topics and question plans; each section's questions still come when it is finished). Renaming it belongs with UX-30's words pass; writing every section's questions at once would start model work for sections not finished, the owner's call.

## Tests (fail first)

| File | Tests | On main (sources put back with `git show HEAD:…`, restored after) |
|---|---|---|
| `tests/test_section_done_before_build.py` (new) | 14: finished before the build applies → waiting, then queued once when it applies, never again on any read or a second completion; before a build that stops, then a Retry that works; the phone's deferred section waits too; a section no topic cites settles as none after the build; finished after the build applies, as before; a completion on a snapshot from before the build still finds its topics; a section in a chapter no build covers yet waits; an old `none_needed` row with topics citing it is picked up once on the next read; an old row that was right stays without questions; the status fact in the waiting state; the whole-book press on a built book and while it is built (notice, nothing queued); with chapters left it starts; a planner that found nothing never hides the line | 13 of 14 failed (`KeyError: 'waitingForBuild'`, `'none_needed' == 'waiting_for_build'`, `0 == 1` batches, `KeyError: 'questions'`, a batch id where none was expected, a None line); the started-press guard passes on both |
| `tests/test_first_questions_today.py` | one assertion extended (below) | fails on main (no `waiting` key) |
| `apps/learnloop-tauri/src/screens/today/TodayPlace.test.tsx`, describe "A section finished before its book is ready … (UX-31)" | 5: the wait with the promise, not "finish a section"; a one-section reading; the promise alone with Continue reading; the writing shows on queue-changed with no press; plain words | 4 of 5 failed; plain words passes on both |
| `apps/learnloop-tauri/src/screens/reader/sectionDone.test.tsx` | 2: the Reader's waiting line with the book's title (still mark, plain words); without a title | 2 of 2 failed ("✓ Done with this section.") |
| `apps/learnloop-tauri/src/screens/LibraryPlace.wholeBook.test.tsx` (new) | 2: the notice as a status, the card keeps its line; a press that started says nothing of its own | 1 of 2 failed; the started case passes on both |
| `apps/learnloop-tauri/src/copy/denyList.test.tsx` | the cause list gains the four new states | the file fails to load on main (`causeSentence` of an unknown kind) |
| `apps/learnloop-mobile/src/today/Today.plan.test.tsx`, describe "a section finished before its book is ready (UX-31)" | 2: the wait with the promise; the promise alone | 2 of 2 failed |

**Assertions changed, and why.** `test_first_questions_today.py::test_a_built_book_with_no_section_finished_says_none_came_yet` compares the whole fact; it now also expects `"waiting": []` (the fact gained a key; nothing loosened). No other assertion changed.

## Code moved

`_trigger_section_generation` and `drain_deferred_section_generations` left `handlers/reader.py` (held at 2,980 lines by the structure ratchet; now 2,895): the rule is `learnloop.reader.section_generation.start_section_questions`, bound to the sidecar's queue in `learnloop_sidecar/section_questions.py` (`start_section_questions`, `drain_owed_section_questions`). The stamp values are named constants in `learnloop.db.stores.reader` beside the column's store (`SECTION_WAITING_FOR_BUILD`, …; `section_generation` re-exports them), so `add_source` reads them without a new cross-domain import. Whether a chapter's build settled is `add_source.section_topics_settled`, passed to the rule as a callable (an import each way was a new cycle for the cycle ratchet). The build's hook `start_waiting_sections` is in `content/pipeline/jobs.py`, which already imports the Reader's job modules at the top (from `add_source` it was a new function-local cross-domain edge, which `test_architecture`'s frozen inventory refuses). `jobs.practice_expansion_payload` is the one payload both the sidecar and the build use. `deferred_section_generations` also returns `completed_at`. No test patched the moved names.

## What I ran

RUNS_PLACEHOLDER

## What a walk must check

firstq (a first-day learner, one article, the live route):

1. Add the article; open it; read its one section to the end **while Today still says "Getting “…” ready for questions"** (the synthesis still running) and press "Done with this section". The Reader says "◐ Your questions from this section will be written as soon as “…” is ready. They'll be on Today." (not "✓ Done with this section.").
2. Go to Today while the book is still being got ready: the wait, then "Your questions from what you read will be written as soon as “…” is ready. Keep reading meanwhile." Never "finish a section".
3. Wait (no press) until the build ends: Today shows "◐ Writing questions from what you read in “…”…", then "N questions from what you read in “…”. More come as you finish sections. [Begin ↵]". Begin (or Enter) opens one of them.
4. In the Library, "Build questions for the whole article at once": the shelf says "All of this article is ready for questions. Each section's questions are written when you finish it."; the card keeps its line; no "Chapters found".
5. Optional: the phone. Finish a section on the phone while the desktop's book is still being got ready; on the desktop, Today after the build ends shows "Writing questions from …" without opening the Reader.

## Not verified

- No app, browser, server or model ran; every state is from pytest on the house fakes (the build's synthesis is `FakeBookSynthesisClient`; section questions were queued, not written) and vitest on fake RPCs.
- The real worker thread: the build's hook runs inside the synthesis job and enqueues through the runner in one transaction; tested through the foreground drain only.
- The Reader's waiting line does not change by itself when the writing starts (it is the press's answer, as the "writing" line is); Today follows the truth. A section finished in an earlier visit and still waiting shows "✓ Done with this section." in the Reader.
- A build waiting for a look that the learner then accepts in the Library: the section should be started on the next read of the books (the settled rule counts a build with no item left pending); read from the code, not tested.
- An old `none_needed` row on a book whose chapter was built twice (an Undo, then "Build them again"): compared with the newest build's end; read from the code.
- Cost on a large library: each read of the books reads the owed rows (three small queries) and, per book with a waiting or old row, its planners' rows; an old row is decided once, reading the book's text at most once.

## Seen in the walk, not this step's

The persona could not reach the quick check's "compare" after typing an answer (steps 22-28), and several passages refer to figures and data the reading does not show (steps 11-15). Neither is UX-31; they are for the walk's own findings.

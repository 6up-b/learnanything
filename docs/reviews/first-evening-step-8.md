# The first evening, step 8: one explanation of where questions come from, where to read to, held questions

Step 8 of the stage "The first evening, finished" (the design's §4 part "Wording and held questions": rows F45/UX-52,
UX-30, UX-32, UX-44c, the bare streak, QUESTIONS-REVIEW; §5's rows "Wait/progress/Today wording" and "Held-question
Today line"; §6's row 8; §7's row 8). Two live walks on 2026-11-21 (a student who reads half a one-section chapter and
never presses "done") found the part-read questions working and the words around them contradicting each other: Today
said "More come as you read on" in one place and "More questions come as you finish sections" in another (UX-64), said
"Questions come as you finish sections" during the build to someone who had read half a section and the Library said
it afterwards (UX-65), "Read a little further" did not say how far (UX-63), an error hunt captioned the work to check
"Worked solution" (UX-66), and questions held for the learner's OK had no line of their own. Branch
`ux/first-evening-wording` from `ux/first-evening-next-practice` at `1ac9290577`.

Nothing is scheduled, served, generated, graded or stored differently, with one deliberate exception (UX-60/UX-61): a
request for a first set from the part read gets its own instruction line and leaves out note excerpts not wholly within
seen passages. No algorithm tag, config key, kill switch or migration. No identity pin, golden or structure ratchet
moved.

## Judgment calls to read first

1. **The explanation is two constants, not one sentence.** `QUESTIONS_FROM_READING` ("Questions are written from the
   parts you read.") is said wherever the rule itself is given; `MORE_AS_YOU_READ` ("More come as you read on.") is
   its consequence, said after questions offered or none up today. One sentence everywhere ("Questions are written
   from the parts you read, and more come as you read on.") would say "more" before any question exists (a build, a
   book not read yet) and would repeat "from what you've read" right after an offer that just said it. Both live in
   `apps/learnloop-tauri/src/app/todayCause.ts`, which the phone imports; the sidecar's card line and whole-book notice
   say the rule in its own `READING_RULE` (`add_source.py`), the same words.
2. **F45's heading is "No questions ready yet." alone.** The design's status ("No questions ready yet. Questions from
   what you've read are being written.") would repeat the cause line right under it ("Writing questions from what
   you've read of …") and would be false during a build with nothing read. The heading replaces "Nothing planned for
   today." (done or open empty day, desktop and phone), "Nothing more to plan today." (Keep going that added nothing)
   and the full list's "Nothing else for today." only while the cause is work under way (`causeUnderway`: a book
   being got ready, questions being written, a section waiting for its book or the desktop). Elsewhere the old words
   stand.
3. **The held line opens nothing.** Until the answer-hidden review surface (UX-40b) lands, every screen that takes a
   held question shows its answer. The line says the count and nothing else: no button, no link, no question text.
   What it does instead: it tells the learner the questions exist and wait for them, so a "None up today" or "Read
   …" beside it is not taken for "nothing was written". When every question a book's reading gave is held, the line
   is the cause itself ("3 questions from what you've read in “B” need your OK.") with Continue reading, replacing
   "“B” needs a look in your Library." with Open Library, which led only to a Library whose Review shows answers.
4. **The held line's count is the rows an OK would apply** (`add_source._awaiting_ok`): a pending
   `practice_item` row, `operation = create`, `validation_status` not `invalid` (a `warning` is valid), and
   `dependency_status` not `blocked`, the same refusals `patches._apply_accepted_locked` and the dependency closure
   make. It is a new fact, `awaiting_ok` (present only when some), beside the existing `to_look_at` (every pending
   row). "more" appears when any book has questions in (`count > 0`). It is shown on the desktop once the day's plan
   is done or holds nothing (as the dated lines are, step 7's judgment 1), never under the full list, never twice;
   on the phone on an empty day and on a done plan (the phone now reads the books on a done plan, to know it).
5. **Step 7's `held` fact gets no words** (ledger UX-68, open): `next_practice.held` counts topics whose
   `reader_topic_question_work.state` is `held`, and nothing moves that state when the learner later accepts or
   rejects the questions, so it can be stale. Its `waiting` fact gets words in the dated lines ("Questions from 2
   finished sections are waiting to be written."), left out on Today when a cause line shows (as `writing` is).
6. **Where to read to names the furthest unseen passage of the nearest topic.** Nearest: of the topics this reading can
   complete by reading on (every unseen cited passage on this reading; none unresolved or held out), the one whose
   furthest unseen passage comes first. The place is that passage, so reaching it is enough for that topic and the
   line never promises more. It is named by the inner heading it lies under (a `SectionHeader` block after the
   section's own first passage), else its opening six words (or those of the first later passage in the section that
   has plain words: a formula or code is skipped forward, which still means the place was passed), else the section's
   end. A web or Markdown book has no heading blocks (its headings are only slugs in `section_path`; the walk's chapter
   showed none inside its one section), so on it the place is the passage's opening words.
7. **"Read through “H”"**, not "Read to “H”": the passage can lie anywhere under the heading; reading through it reaches
   the passage. It can ask for a little more than needed; it never asks for less.
8. **UX-30's "derive an actual count"** is the card line's "· N written so far" (the book's applied, live questions).
   No count is invented: absent when none.
9. **`moreLeft`** (a done plan's "there's more for today") now leaves out a book's question kept for a later check
   (`laterItemIds`) as well as rows waiting to come back; step 7's day words for the full list ("not answered yet",
   "comes back Monday", "a check on your own from Saturday") already tell the three kinds apart and are reused unchanged.
10. **No identity pin moved under the prompt change.** The registered section-authoring answer key renders fixed
    instructions and no note; nothing registered renders the part-read line. The playbook's rule (step 1: a change that
    does not alter persisted meaning needs no tag; step 4: an identity pin moves only with a version decision) applies
    with the decision "no tag: what the writer is asked changes, no stored row's meaning, review policy, gate, grade or
    schedule does" (the design's §5 row "Partial first sets", UX-40's precedent). `python tests/test_identity_pins.py
    --write` rewrote nothing. The request bytes are pinned instead in `tests/test_part_read_request.py` (below).

## Commits

| Commit | What |
|---|---|
| `63c3f94300` | A part-read request's own line, and its notes kept to excerpts within seen passages; request digests |
| `730afa5c21` | The book's facts: the working line carries the part read (UX-65), `read_to` (UX-63), `awaiting_ok`; the card line and whole-book notice; the error hunt's caption (UX-66) |
| `c6fff920f7` | Today (desktop and phone), the Library's details, the Reader's guide, the dated lines' `waiting`, the streak |
| (this record) | The record and the ledger rows |

## The one explanation and where it is used

| Constant | Words | Used by |
|---|---|---|
| `QUESTIONS_FROM_READING` (`app/todayCause.ts`) | "Questions are written from the parts you read." | Today's build line with nothing read (`causeWait`, `on_the_way`), the not-yet-read line (`finish_section`), desktop and phone; the Library's whole-book press explanation (`BookCard`, `whole-book-why`); the Reader's guide (`GuideRail`, `guide-questions-from`, not offline) |
| `MORE_AS_YOU_READ` (`app/todayCause.ts`) | "More come as you read on." | Every offer's tail (`readySentence`: from the part read, from a finished section, from the book) and "none up today" (`none_up`), desktop and phone |
| `READING_RULE` / `reading_rule_for` (`content/pipeline/add_source.py`) | "Questions are written from the parts you read." / "Questions for {Ch. 1–2} are written from the parts you read" | The book card's line (and its no-AI line), the whole-book notice (`whole_book_notice`) |

The tests assert on the constants, never on copies (`todayCause.test.ts`, `TodayPlace.test.tsx`, `sectionDone.test.tsx`,
`LibraryPlace.wholeBook.test.tsx`, the phone's `Today.plan.test.tsx`), and that no line says "finish sections", "finish
a section" or "when you finish" any more.

Not changed because it does not state the rule: the finish card (its dated lines say what is being written, with no
rule), the Reader's section-done lines ("Writing questions from this section. They'll be on Today.", the
waiting-for-the-book line), and "LearnLoop writes questions from what you read." (no books), which agrees.

## Why the before-build line did not show (UX-65), and what changed

Step 4 added `before_build` to `add_source.reading_questions` and the words "Questions from what you've read will
follow when “B” is ready." to Today's `on_the_way` cause, keyed on `questions.beforeBuild`. Its test read
`reading_questions` directly. But during a build, Today reads the card's *working* line ("Getting … ready for
questions"), and `add_source.source_status_line` attaches the facts to a line of another state only when they hold
questions, writing, waiting, failed or held rows: a learner who had read part of a section, with nothing else, had a
`before_build` that was dropped. Today's cause then had `waiting = null` and said its default, "Questions come as you
finish sections. Keep reading meanwhile." Not the cause lines' precedence: the state never reached them. Now the line
carries the facts when `before_build`, `owed` or `read_further` says something
(`test_the_line_while_the_book_is_got_ready_carries_what_was_read_of_it`, failed on the base with `KeyError:
'questions'`), and the default after a build line is `QUESTIONS_FROM_READING`.

## Every line, before and after

Desktop Today (`TodayPlace`, the cause line under an empty or done day; the same sentences on the phone's `PlanToday`,
which shares `todayCause`). "B" is the book, "P" a section, "H" a heading.

| State | Before | After |
|---|---|---|
| Book being got ready, nothing read | heading "Nothing planned for today."; "Getting “B” ready for questions · 1 of 2 steps done. Questions come as you finish sections. Keep reading meanwhile." | heading "No questions ready yet."; "Getting “B” ready for questions · 1 of 2 steps done. Questions are written from the parts you read. Keep reading meanwhile." |
| Being got ready, part of a section read (the walk) | the same as above (the fact was dropped) | heading "No questions ready yet."; "Getting “B” ready for questions · 1 of 2 steps done. Questions from what you’ve read will follow when “B” is ready. Keep reading meanwhile." |
| Questions being written (part read or finished) | heading "Nothing planned for today."; "Writing questions from what you’ve read of “P”… Keep reading meanwhile." | heading "No questions ready yet."; the cause unchanged |
| A finished section waiting for its book | heading "Nothing planned for today."; "Your questions from “P” will be written as soon as “B” is ready." | heading "No questions ready yet."; the cause unchanged |
| Ready, from the part read | "2 questions from what you’ve read of “P” are ready. More come as you read on." **Begin ↵** | unchanged (the tail is `MORE_AS_YOU_READ`) |
| Ready, from a finished section | "2 questions from “P”, the part you read. More come as you finish sections." / "… from what you read in “B”. More come as you finish sections." | "… More come as you read on." |
| Ready while more are written | "1 question from what you’ve read of “P” is ready. More are being written (2 of 8 topics done)." | unchanged |
| Ready + writing + a topic not written + held | the offer and "Not every topic's questions could be written." (held questions: nothing) | the same, and under it "2 more questions need your OK." |
| Every question held | "“B” needs a look in your Library." **Open Library** | "3 questions from what you’ve read in “B” need your OK." **Continue reading** |
| Held, beside a done or empty day | nothing | "2 more questions need your OK." ("1 more question needs your OK."; without "more" when no book has questions in) |
| None up today | "Nothing from “B” is up today. More questions come as you finish sections." | "Nothing from “B” is up today. More come as you read on." |
| Built, nothing read | "Your first questions come when you finish a section of “B”: finish its quick check, or press Done with this section at its end." | "Read “B” for your first questions. Questions are written from the parts you read." |
| Read some, none qualifies, inner heading | "Read a little further in “B” for your first questions." | "Read through “H” in “B” for your first questions." |
| … no inner heading | the same | "Read as far as the passage that begins “Suppose we have a dataset of…” in “B” for your first questions." |
| … the place is the section's last passage | the same | "Read to the end of “P” in “B” for your first questions." (one section: "Read to the end of “B” …") |
| … no place known (another book needed, unresolved) | the same | unchanged |
| No topics found | "… Try again, or keep reading: the sections you finish get their questions once topics are found." | "… Try again, or keep reading: what you read gets its questions once topics are found." |
| Goal line, built and nothing read | "Nothing for this goal is ready to practise yet: your first questions come when you finish a section of “B”: …" | "Nothing for this goal is ready to practise yet: read “B” for your first questions. Questions are written from the parts you read." |
| Keep going that added nothing, work under way | "Nothing more to plan today." | "No questions ready yet." |
| Full list empty, work under way | "Nothing else for today." | "No questions ready yet." |
| Done plan; the list holds only a book's question kept for a later check, never answered | "The plan stopped here, but there's more for today if you'd like it. Open today's list" | "Nothing else is needed today." |
| Footer streak | "4 days · best 9", "1 day" | "4 days in a row · best 9", "1 day in a row" |
| Dated lines (done or empty day, no cause line; the finish card) | nothing for sections waiting | "Questions from 2 finished sections are waiting to be written." |
| Open plan with questions | the plan | unchanged: no cause, no held line |

One meaningful Enter target throughout: with questions offered only Begin shows ↵; with work under way only Keep going
does (tested). The held line has no control.

Phone (`apps/learnloop-mobile/src/today/PlanToday.tsx`): every cause sentence above, the same heading change ("Nothing
planned for today." → "No questions ready yet." while work is under way, on an empty day and a done one), the held line
(`today-held`) on an empty day and on a done plan, no held line while the plan holds questions (the books are not read
then). The phone shows no book card lines.

Library (desktop `BookCard`; the sidecar's lines):

| Place | Before | After |
|---|---|---|
| A built book's line | "Questions for Ch. 1–2 are written as you finish sections" | "Questions for Ch. 1–2 are written from the parts you read" ("· 2 written so far" once some are in) |
| Its no-AI line | "… are written as you finish sections once an AI is connected" | "… are written from the parts you read once an AI is connected" |
| Details' press | "Get the whole article ready for questions at once" | "Get the whole article ready for questions", and under it "Questions are written from the parts you read." |
| The press's notice, all built / being built | "All of this article is ready for questions. Each section's questions are written when you finish it." (and "… is already being got ready for questions. …") | "All of this article is ready for questions. Questions are written from the parts you read." (and the same for "already being got ready") |

Reader guide (`GuideRail`): under the section's status line ("Keep reading at your own pace." etc.), a new line
"Questions are written from the parts you read." (not offline). Its other lines are unchanged.

Practice (an error hunt, desktop `ItemPresentation` and phone `QuestionScreen`, both rendering the sidecar's label): the
caption over the work to check "Worked solution" (the desktop shows it in capitals) becomes "The work to check". The
item, its prompt ("Submitted work: …" where the writer wrote it), its grading and what is shown are unchanged; the
caption still says nothing about whether the work holds an error.

## How "where to read to" is computed

`reader.part_read.place_to_read(order, section_of, blocks, unseen_by_topic)` (plain values; `_read_to` feeds it from
`assess`): for each settled unfinished section with seen passages where no topic qualifies, of its candidate topics
(needing questions, owned by nobody) those whose coverage reason is `unseen` and whose every unseen passage is on this
reading; per topic the furthest unseen passage in reading order; the smallest of those is the place. Read-only: it uses
`assess`'s coverage (remembered per reading). `reading_questions` carries the first `read_further` section's place as
`read_to` (`section`, `heading`, `words`, `section_end`). On the eigen fixture, reading P3 and P4 only: the house topic
waits only on P1, so the place is "Paragraph P1 about the aardvark is…" (`lo_early` waits on P1 and P2, every other
topic on a later passage).

## The request change (UX-60, UX-61) and its digests

`jobs.handle_practice_expansion`: when every topic-work row of the job was claimed with trigger `part_read`
(`_TopicWork.part_read`; one claim is one trigger), the instruction's first sentences are "These items seed practice
for the part of a section the learner has read so far (reader_section_completed:<section>); they have not finished it.
The cited source spans are the passages they have read: ground every item in them and ask about nothing beyond them."
and its context keeps a note only when `reader.part_read.seen_text_filter` finds its 280-character excerpt inside one run
of consecutive seen passages of the claims' readings (whitespace collapsed); `build_authoring_context(note_filter=…)`
applies it to the whole request and every part (so the frozen `:requests` checkpoint carries no other note either). Any
other job, the finish included, sends the same bytes as before.

Digests (`tests/test_part_read_request.py`: one topic of the section-writer fixture, claimed as a finish or as a part
read; the request's SHA-256 with the library's temporary path named `<library>`):

| Request | Base (`1ac9290577` + the tests) | Branch |
|---|---|---|
| Finish (`section_finished`) | `7d64213113f46133ea1d7749ff9f1e35ad5ee4927e118831474d209b76cfbeb1` | `7d64213113f46133ea1d7749ff9f1e35ad5ee4927e118831474d209b76cfbeb1` (unchanged) |
| Part read (`part_read`) | `7d64213113f46133ea1d7749ff9f1e35ad5ee4927e118831474d209b76cfbeb1` (the finish's bytes) | `0df739ef507d2de295c1ebfd5bb0bf03c19dadba58766413a93321c3918756ed` (its line; the fixture's one note left out: nothing of the library was seen) |

On a note-backed book (`test_a_part_read_request_on_a_note_backed_book_sends_no_unread_note_text`, the eigen book with
two notes in its subject, one whose body is P1, read, one whose body is P5, not read): both part-read prompts and both
frozen requests carry the read note and not the unread one, and no unread paragraph's word; the later finish's prompts
carry both notes, as before. Identity pins: none moved (judgment call 10).

## Tests, with fail-first evidence

Fail-first, each against the base's sources (the tests at the branch; for the apps, the seven changed source files
put back to the base and restored after):

- Prompt: `test_part_read_request.py` and the three prompt tests in `test_part_read_first_set.py` on the base: the
  part-read line and note tests failed (`'the part of a section the learner has read so far' in …`; `'note_unread_part'
  not in …`); the finish tests passed (the control: the bytes before).
- Facts and wording, backend: `test_sidecar_item_presentation.py`, `test_first_questions_today.py`,
  `test_part_read_first_set.py`, `test_section_done_before_build.py` on the base: **13 failed, 74 passed** (`'Worked
  solution' == 'The work to check'`; the card's old line; `KeyError: 'awaiting_ok'`; `KeyError: 'questions'`;
  `KeyError: 'readTo'`; `ImportError: place_to_read` ×5; the two notices); `test_nothing_held_says_no_count_of_held_questions`
  passed on both (the control).
- Desktop: `todayCause.test.ts`, `nextPractice.test.ts`, `todayPlan.test.ts`, `TodayPlace.test.tsx`,
  `sectionDone.test.tsx`, `LibraryPlace.wholeBook.test.tsx` on the base sources: **42 failed, 187 passed** (every new
  case but the open-plan control, and the moved assertions).
- Phone: `Today.plan.test.tsx` on the base sources: **14 failed, 47 passed**.

New tests: backend `tests/test_part_read_request.py` (2), `test_part_read_first_set.py` (3 request tests, 5
place-from-plain-values tests, the `readTo` assertion), `test_first_questions_today.py` (4: the working line, held
counts, nothing held, the card line's count), `test_sidecar_item_presentation.py` (the caption). Desktop:
`todayCause.test.ts` (9), `TodayPlace.test.tsx` (12, the state matrix: ready + writing + held + failure, all held, all
waiting to come back with one held, a question kept for a check, no topics, read further with the place, an open plan,
during the build with part read, during the build with nothing read, none up, the full list, Keep going),
`nextPractice.test.ts` (1), `sectionDone.test.tsx` (1), `LibraryPlace.wholeBook.test.tsx` (1), `denyList.test.tsx`
(`STEP8_SENTENCES`: every new line). Phone: `Today.plan.test.tsx` (6).

Assertions changed (each the words this step replaces):

- Backend: the card line "Questions for Ch. 1–2 (1–3) are written as you finish sections" → "… from the parts you read"
  in `test_first_questions_today.py`, `test_apply_recovery.py`, `test_ux_phase1_add_source.py`,
  `test_ux_phase1_usability_round1.py`, `test_ux_phase1_usability_round2.py` (and its no-AI line),
  `test_ux_phase1_review_fixes.py` (2), `test_ux_phase1_auto_build.py` (2); the whole-book notices and the card line in
  `test_section_done_before_build.py` (3).
- Desktop `TodayPlace.test.tsx`: the build's default after-line (2), the not-yet-read line (4, one as the goal line, one
  as a `toContain` of its start), the offer tails (4), none up (3), the no-topics sentence; "an empty, finished plan
  with nothing offered: the heading stays" → the heading is `NO_QUESTIONS_YET`; two `not.toContain("Your first questions
  come when you finish a section")` (vacuous now) → `not.toMatch(/for your first questions|finish a section/)`; one
  `not.toMatch(/…|More come as you finish sections/)` → `/…|More come as you (finish sections|read on)/` (the offer while
  more are written still has no plain-offer tail); the streak "4 days · best 9" → "4 days in a row · best 9" (also
  `App.today.test.tsx`, `todayPlan.test.ts` with "1 day in a row").
- `BookShelf.test.tsx`, `LibraryPlace.wholeBook.test.tsx`, `denyList.test.tsx`: the card lines and the press's label.
- Phone `Today.plan.test.tsx`: the same sentences (7) and the UX-52b heading with writing → `NO_QUESTIONS_YET`.

No assertion checking real behaviour was loosened.

## What was run

Every Python run through the scratch wrapper (empty home, config and Codex dirs); every pytest run from a script that
refuses an empty target list, `-n 1`, in a 3 GB scope, one at a time; vitest with 4 workers; npm through the shared npm
cache.

| Command | Result |
|---|---|
| `tests/test_part_read_request.py` + the three prompt tests of `test_part_read_first_set.py` (after the prompt commit) | 5 passed |
| `test_part_read_request.py`, `test_part_read_first_set.py`, `test_section_question_parts.py` (`-m "not arc_close"`) | 48 passed |
| `test_identity_pins.py` after the prompt commit | 357 passed |
| `test_sidecar_item_presentation.py`, `test_first_questions_today.py`, `test_part_read_first_set.py`, `test_section_done_before_build.py` (after the facts commit) | 87 passed |
| The edited card-line files: `test_apply_recovery`, `test_ux_phase1_add_source`, `_usability_round1`, `_usability_round2`, `_review_fixes`, `_auto_build`, `test_empty_first_build`, plus the `readTo` test | 136 passed |
| `scripts/affected_tests.py --files` the six changed sources | about 740 files (over 150: the name filter below instead) |
| The brief's name filter (today, first_questions, part_read, next_practice, add_source, section_question, practice_generation, ux_phase, mobile_v2_plan, mobile_v4, mobile_allowlist: 33 files) plus `test_apply_recovery`, `test_section_done_before_build`, `test_sidecar_item_presentation`: 36 files, one chunk, `-m "not arc_close"` | 932 passed, 3 skipped |
| `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`, `test_public_tip_guards`, `test_ingest_queue_store` (after the last commit) | 414 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `tests/test_architecture.py` alone | 18 passed |
| `python tests/test_identity_pins.py --write` | no file changed |
| `scripts/check_gate_partition.py` | collected 32710: landing 32644 + arc_close 66 |
| `ruff check` | All checks passed! |
| `lint-imports --no-cache` | Contracts: 45 kept, 0 broken |
| Desktop `npm run typecheck`; `vitest run --maxWorkers=4` (whole suite); `npm run frontend:build` | clean; 323 files, 3,517 tests passed; built |
| Phone `npm run typecheck`; `vitest run --maxWorkers=4` (whole suite); `npm run build` | clean; 43 files, 453 tests passed; built |

No identity pin, golden, structure ratchet or snapshot moved. No new non-test TypeScript file (`desktop_validate.py`'s
counts unchanged).

## What a live-route walk must check

The patient first-day persona and the learner who stops at 60 % (the design's §7 row 8), on the real desktop window and
the phone:

1. **During the build, read part of the first section and go to Today:** the heading "No questions ready yet." and
   "Getting “B” ready for questions · … Questions from what you’ve read will follow when “B” is ready. Keep reading
   meanwhile." Never "finish sections". The Library card afterwards: "Questions for … are written from the parts you
   read".
2. **Stop where no topic qualifies (the walk's 48 %):** Today names the place. On the walk's web chapter (no inner
   headings) it should be "Read as far as the passage that begins “…” in “…”"; read to that passage and check Today
   turns to "Writing questions from what you’ve read …" within a report, or, if it does not, print
   `part_read.topic_coverage` for the nearest topic: the place must be its furthest unseen cited passage.
3. **One explanation:** with questions offered, the tail is "More come as you read on."; none up today, the same; the
   Reader's guide and the Library's details say "Questions are written from the parts you read."; nowhere "finish
   sections", "finish a section" or "when you finish it".
4. **Held questions:** a build or section whose questions were held (`review_required`): Today's "N more questions need
   your OK." beside the offer or the writing line, with no control and no question text; with every question held, "N
   questions from what you’ve read in “B” need your OK." with Continue reading. The count equals the valid, unblocked
   pending question rows of the book's writing jobs.
5. **Error hunt:** an error-hunt question shows "THE WORK TO CHECK" (desktop) / "The work to check" (phone) over the work,
   before answering.
6. **The heading over work under way** on the done and the open empty day, Keep going that adds nothing, and the full
   list (`l`) with nothing on it: "No questions ready yet.", and Enter is Keep going's.
7. **A done plan** whose list holds only an answered question or one kept for a check: "Nothing else is needed today."
8. **The footer:** "1 day in a row" on the first evening.
9. **The part-read request** (a note-backed book only: an older vault): its frozen `…:requests` checkpoint has the
   part-read line and no note whose excerpt is outside the seen passages; a finish request's has the finish line.

## What was not verified

- No app, browser, server, phone or real model ran (the rules): every screen is tested in vitest/jsdom; layout at phone
  width and in the real WebKitGTK window is not seen (the held line, the guide's added line, the details' explanation).
- Real readings: whether real builds' topic citations give a useful place (a PDF's `SectionHeader` blocks; a web
  chapter's opening words), and whether a real note-backed book's note excerpt ever lies within seen passages (its body
  may start with a title, which the rule then leaves out).
- The held line's count against a real held build (only fixtures).
- The answer-hidden review surface (UX-40b) is not built; the held line links nowhere until it is.
- UX-67 (answer box and confidence control layout) and UX-68 (step 7's stale `held`) are filed, not fixed.

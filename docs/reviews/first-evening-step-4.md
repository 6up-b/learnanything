# The first evening, step 4: a first set of questions from the part of a section read

Step 4 of the stage "The first evening, finished" (the design's §2 "The rule for a first set from the part read", §5's
row "Partial first sets and topic claims", §6's starred row 4, §7's row 4 and §8's first and fourth points). The
owner decided on 2026-11-20 that a learner who has read part of a section gets a first set of questions from the
part they read. Before this step a section's questions were written only once it was finished; now a topic gets its
first set as soon as every passage it cites has been seen by the learner's own reading (step 2's
`reader_seen_spans`), through step 3's per-topic claims (trigger `part_read`, admitted there and unused until now).
Today, on the desktop and the phone, says what is ready, being written, waiting for the book, or not yet possible for
a section read in part. Branch `ux/first-evening-part-read` from main `3f42da228a`.

No algorithm tag, no config key, no kill switch, no prompt-contract change (the per-topic request keeps its shape; only
its bundles differ). Review policy, grading, eligibility, scheduling, reading credit and exposure are untouched. The
Reader's own finish behaviour does not change (a section is finished exactly as before; step 5 changes that).

## Judgment calls to read first

1. **A report reconciles its own book; the books' reads reconcile every book read.** A progress report that adds
   passages claims for the reading it reports on (`reader.mark_section_progress`). A topic of book A that also cites
   book B qualifies when B's passage is seen, and is claimed on the next read of the books (Today, the shelf, the
   Reader opening A, the desktop's start), not by B's report: reconciling every read book on each report would cost an
   assessment of every book per debounced report.
2. **The build hook does not wait for "settled".** The build's own batch is still running when its synthesis's
   after-hook runs (`after_auto_build` → `jobs.start_waiting_sections`), so by `section_topics_settled` its chapter is
   not settled yet. The hook reconciles with the topics the build just applied (a fresh vault), as the waiting
   finished sections there already do; topics the build left for a look are not in that vault and are claimed when a
   review applies them (the review trigger). Every other caller uses `section_topics_settled` unchanged.
3. **The report reloads the vault once after a background build applied.** The sidecar's vault is the one loaded
   before a background build applied its topics; a report would otherwise find no topic to qualify until a read of the
   books reloaded it. The report path calls the books' own reload rule first (`_reload_applied_batches`: once per
   applied job, nothing when none).
4. **`assess` is remembered per reading** (`part_read._MEMO`) until something it reads changes: a seen passage of any
   reading (count and newest row), the queue's revision (bumped by every job's end and every apply), the number of
   topic claims, the reading's section progress rows (finish and stamp), or the vault object. Today's polled reads pay
   for it once. A change it does not see (an exam mark added or removed, a topic file edited outside the app while the
   same vault object is loaded) is read on the next change it does see. The build hook does not use or keep it.
5. **The reply to a progress report stays a progress report's** (`enqueuedGeneration: false`, `batchId: null`) when a
   part-read claim is made: the Reader's own words after a report are unchanged in this step. The stamp in the reply's
   `progress.generationBatchId` reads `topic_managed`, which neither app reads.
6. **A part-read stamp before the finish.** A section whose part read claimed topics is `topic_managed` while
   unfinished. Its first finish (not a repeat) claims the rest through the same claims
   (`start_section_questions(from_stamp="topic_managed")`); on the phone it moves `topic_managed` → `deferred_to_primary`
   and the desktop's drain claims the rest. A finish with nothing left to write keeps `topic_managed` (it no longer
   becomes `none_needed_after_build`, which Today read as "nothing to write here" and so hid the part-read questions).
7. **The request's instruction still says "material the learner just finished reading"** (`jobs.handle_practice_expansion`'s
   `extra_instructions`, with the section reason): changing it is a prompt-contract change this step may not make. The
   part-read request differs only in its bundles.
8. **Protection reuses the Reader checks' row** (`exam_material.SURFACE_SETS["reader_checks"]`, the held-out
   partition; its comment now names `reader.part_read`). A new row would need a protection-matrix column; the part read
   is the Reader's own question work, which that row already governs.
9. **The finish-section sentence is unchanged** ("Your first questions come when you finish a section …"). It is now
   incomplete (a topic read whole gets questions before), but it is said only when no section has been read in part
   with a fact to name; rewording it moves eight existing assertions, some of them "not contains" checks that would go
   vacuous. It belongs to step 8's wording row.

## Commits

| Commit | What |
|---|---|
| `71f512f30a` | The rule, the grounding, the triggers, the later finish, Today's facts; backend tests |
| `36e781cc69` | Today's words on the desktop and the phone (`todayCause`); frontend tests |
| `aab49032b8` | A canonical reference whose id is a note standing for a book resolves as the section map matches it |
| (last) | The reader-first-set design value named and registered; the protection row's comment; this record; ledger row UX-60 |

## The qualification rule, as built

`learnloop.reader.part_read.topic_coverage` (and `_coverage`, `_resolve`), a new helper; `section_map`'s membership
functions are unchanged. For each active topic:

1. Its references: its own provenance `source_refs` (priority 0) and those of every facet in its facet union
   (priority 1).
2. A reference that is not a passage reference (`existing_entity`, `session`, `manual_context`) cites no passage and is
   skipped. A `canonical_source` or `note` reference names its book by `source_id`, else by an `ref_id` that is a
   library artifact, else by a note that stands for a library book (`section_map.canonical_note_ids`).
3. Its passages, each exactly, on the book's current reading (the reading being read, or another book's
   `current_reading`): every explicit `span_ids` entry (on the same reading, or through the alias authority with an
   exact alias only); a `t=` locator's every overlapping cue (not only the nearest, as the section map takes); a span
   locator or legacy quote through `section_map.anchor_for_ref` over the reading's readable passages, across section
   boundaries, accepted only as `current`.
4. It **qualifies** when it cites at least one passage, every passage reference resolved, every cited passage has exact
   seen evidence (`seen_passages.seen_on`, which carries an earlier reading's evidence by exact alias only), and none is
   held out.

**Exclusions**, each tested (`tests/test_part_read_first_set.py`) and each reported by `TopicCoverage.reason`:

| Exclusion | `reason` | Test |
|---|---|---|
| a cited passage not seen (straddling, after the stop) | `unseen` | `test_before_the_finish_only_the_topics_read_whole_get_their_first_set` |
| a passage in another section not seen | `unseen` | `test_a_topic_citing_another_section_waits_for_that_sections_passage_too` |
| a passage of another book not seen (mixed source) | `unseen` (`(ext_other, b2)`) | `test_a_topic_citing_another_book_needs_that_books_passages_seen_too` |
| a reference that resolves to no passage exactly (a missing span; an ambiguous quote; a moved passage; a book with no reading; a note that is no library book) | `unresolved` | `test_a_reference_that_cannot_be_resolved_exactly_is_never_read` |
| a cited passage held out | `held_out` | `test_a_held_out_passage_keeps_its_topic_for_the_finish` |
| no passage cited at all | `no_citation` | `test_a_topic_with_no_citation_never_qualifies` |

No percentage, threshold or "first N topics" exists anywhere in the rule. A topic that does not qualify waits for its
section's finish (the existing full-section route), which writes it with the full section's bundles.

## The grounding rule, and the proof that no unseen passage is sent

`part_read.seen_grounding`: a qualifying topic's bundles are its cited passages (at most four, its own references'
first, then reading order: the finished section's own anchor choice), each widened by up to five neighbours on each
side inside its section **only while each neighbour is seen** (a contiguous seen run), merged where they touch, built
by the same `reader_progression.citation_bundle` the finished section uses (extracted from `source_refs_for_section`
unchanged: its request digests and `test_reader_source_refs_preserve_bounded_span_context` pass). A topic with any
unseen cited passage gets no grounding (it does not qualify). The bundles are frozen at the claim
(`passage_ids_json`, `source_refs_json`, the topic key over its own bundles, step 3's scheme) and in `<key>:requests`
before the first call.

Proof, on the frozen request and on what the model was sent:

- `test_the_grounding_quotes_no_passage_the_learner_has_not_seen`: every paragraph carries a word of its own. For both
  claimed topics, the frozen `<work_key>:requests` checkpoint's bundles cite only seen spans, the whole frozen request
  contains no unseen paragraph's word, the claim rows' passage ids are all seen, and neither prompt the fake writer
  received contains an unseen paragraph's word. `lo_early` (cites P1, P2) is grounded on P1..P4: its seen neighbours,
  and not P5.
- `test_reading_on_and_finishing_during_a_blocked_call_…`: P5, seen during the first call, is in no request frozen
  before it; it is in `lo_straddle`'s (claimed after it), and P6 is not.
- `test_a_topic_citing_another_section_waits_…`: `lo_cross`'s bundles are exactly P1, P2 (P1 seen beside P2) and Q1.
- `test_a_topic_citing_another_book_…`: the other book's seen passage is quoted; its unseen neighbour is not.

**Not covered by this proof** (ledger UX-60): the authoring context also carries a 280-character excerpt of every
vault note in scope (`proposals.build_authoring_context`). A book added through Add has no vault note, so the proof
above holds for it; a book ingested the older way has a note whose body is the book's text, and its excerpt can be
text the learner has not read. The section-finish route sends the same excerpt today.

## Every trigger

Reconciliation claims only topics that newly qualify and nobody owns (`part_read.reconcile_part_read`, which re-reads
ownership before each section's claim); a claimed topic is never claimed again by any trigger or by the finish.
Readiness is `add_source.section_topics_settled` except in the build hook (judgment call 2).

| Trigger | Where |
|---|---|
| A progress report that keeps any seen passage (not a finish report) | `src/learnloop_sidecar/handlers/reader.py:2178` (reload rule at `:2186`, the claim at `:2188`) |
| A build's synthesis applied (the build hook scans the reading's seen passages, not only finished sections) | `src/learnloop/content/pipeline/jobs.py:3553` (`start_waiting_sections`, called from `add_source.after_auto_build` at `src/learnloop/content/pipeline/add_source.py:1769`) |
| The primary's start | `src/learnloop_sidecar/context.py:316` → `src/learnloop_sidecar/section_questions.py:113` (the owed-work drain, every read book) |
| The owed-work drain on the books' reads (Today, the shelf) | `src/learnloop_sidecar/handlers/ingest.py:546` → `section_questions.py:113` |
| The Reader opening a book | `src/learnloop_sidecar/handlers/reader.py:2072` → `section_questions.py:113` (that book) |
| A review that applies held topics | `src/learnloop_sidecar/handlers/proposals.py:241` (`_claim_part_read_questions`, every read book) |
| The section's later finish (the rest, through the same claims) | `src/learnloop_sidecar/handlers/reader.py:2159` (first finish of a `topic_managed` section) |

Never on the phone host's secondary attach: the secondary records passages (step 2) and its finish stamps
`deferred_to_primary`; the primary claims from them. No periodic request, no debounce payment rule.

## The quantity

`min(3 − the topic's practice questions, 3)` when positive: the existing plan
(`build_practice_expansion_plan(target_items_per_lo=3, max_new_per_lo=3)`), unchanged. The 3 is now named once,
`section_generation.READER_FIRST_SET_TARGET`, used by the candidates, the requested counts and the writing job
(`jobs.handle_practice_expansion`), and registered in the parameter registry
(`section_generation:READER_FIRST_SET_TARGET`, structural, `constraint`, rationale: the section-seeding contract's
existing target, inherited, a bound on what is commissioned). A held or refused first set is never topped up (step 3's
claims: a claimed topic is never claimed again).

## The later finish

`test_the_later_finish_writes_only_the_remaining_topics`: after the part read wrote `lo_diagonalize_symmetric` and
`lo_early`, finishing the section claims `lo_straddle`, `lo_late`, `lo_cross` (trigger `section_finished`) and asks
only them; five topics asked once each; finishing again and reading again ask nothing. On the phone:
`test_a_section_finished_on_the_phone_after_its_part_read_claims_only_the_rest_on_the_desktop` (the phone moves
`topic_managed` → `deferred_to_primary`, the desktop's read claims the three others, the stamp returns to
`topic_managed`). Reading on and finishing during a blocked call: `test_reading_on_and_finishing_during_a_blocked_call_…`
(P5 seen inside the first call claims `lo_straddle` as `part_read`; the finish inside it claims `lo_late` and `lo_cross`
as `section_finished`; the frozen work ran to completion; every topic asked once).

## Today's facts and words

`add_source.reading_questions` (the facts the book card carries; camelCase over the wire). Before: only finished
sections were read; a section read in part was invisible. After:

| Fact | Meaning |
|---|---|
| `count`, `item_ids`, `sections`, `writing`, `failed`, `to_look_at`, `progress` | now also count an unfinished section's part-read work (its own claims' jobs), the same per-job logic |
| `part_read` (new, present only when some) | unfinished sections with first sets from the part read |
| `before_build` (new) | unfinished sections with seen passages whose chapter's topics are not in yet |
| `owed` (new) | unfinished sections with a qualifying topic not claimed yet (desktop: claimed on this very read; phone: left to the desktop) |
| `read_further` (new) | unfinished sections with seen passages, no claim of their own, whose topics need questions and none has every passage seen |

A finished section with part-read claims reports them whatever its stamp (deferred, waiting, none needed). The
existing keys and their exact-dict tests are unchanged when nothing was read in part.

Words (`apps/learnloop-tauri/src/app/todayCause.ts`, shared by the phone):

| State | Before | After (desktop and phone) |
|---|---|---|
| Questions from the part read on the list | (nothing: invisible; or "Your first questions come when you finish a section of …") | "2 questions from what you’ve read of “Part” are ready. More come as you read on." **Begin ↵** (the phone: how many can be asked now, no Begin) |
| … while more are written | — | "1 question from what you’ve read of “Part” is ready. More are being written." |
| Being written from the part read (or owed, on the desktop) | — | "Writing questions from what you’ve read of “Part”… Keep reading meanwhile." |
| Owed, on the phone | — | "Your reading is saved. Questions will be written when the desktop is running." |
| Read some, none qualifies | "Your first questions come when you finish a section of “Book”: …" | "Read a little further in “Book” for your first questions." **Continue reading** |
| Read before the book is ready | "Getting “Book” ready … Questions come as you finish sections. Keep reading meanwhile." | "Getting “Book” ready … Questions from what you’ve read will follow when “Book” is ready. Keep reading meanwhile." (with no build line: "Questions from what you’ve read will follow when “Book” is ready.") |
| A finished section's states | unchanged | unchanged (`a finished section's words are unchanged beside it`) |

An offer from the part read has no "Nothing planned for today." above it on the phone (it is an offer, as before);
"read further" and "saved" are not offers and keep the heading. No new non-test TypeScript file
(`desktop_validate.py`'s counts do not move). The design's held-questions line ("2 more questions need your OK") is
step 8's and was not added.

## What it costs when the learner abandons the reading

One initial authoring request per newly qualifying topic with a deficit, plus the existing validation, repair and
bounded retry for those topics; no request for a topic not wholly read. On the fixtures (fake writer's calls counted):

| Fixture | Stop | Topics citing the section | Requests |
|---|---|---|---|
| The eigen book (`tests/part_read_helpers.py`), section 1 of six passages | after P4 (67 %) | 5 (`lo_diagonalize_symmetric`, `lo_early`, `lo_straddle`, `lo_late`, `lo_cross`) | 2 (the two read whole); repeated reports and reads: still 2 |
| the same | after P3 (50 % of six passages; the 60 % stop of the design falls between P3 and P4) | 5 | 2 (by coverage, not by a run: the same two qualify) |
| the same, P3 and P4 only (no P1) | — | 5 | 0 ("read a little further") |
| The house book (`tests/ux_phase1_support.BOOK_MARKDOWN`), section "1 Probability and counting" of two passages | after its first passage (50 %) | 1 | 1 |

**The "every cited passage" rule and a realistic first evening.** On both synthetic fixtures a learner stopping at 60 %
gets a first set (2 of 5 topics; 1 of 1). The tracked migration-head fixture has no reading (no extraction), so it
cannot be measured; the owner's vaults may not be opened. Whether real builds cite a chapter's last passages for most
topics is not measured: the live walk below must check it, and the rule is not loosened.

## Tests, with fail-first evidence

Fail-first (the new and edited test files against main's code, in a scratch copy of the tip's `src` and `tests`):

- Backend, against main: `tests/test_part_read_first_set.py` fails to collect (`ModuleNotFoundError:
  learnloop.reader.part_read`); the guard `test_nothing_in_src_reads_the_passages_…` fails. With only the new helper
  module, the store's two reads and the extracted bundle builder copied in (no trigger, no Today, no finish change):
  **13 failed, 18 passed** (every wiring test fails: no claims, no Today keys; the coverage-reason tests pass, as they
  test the helper alone). `tests/test_first_questions_today.py`: **2 failed, 32 passed** (its two new tests).
- Desktop, `todayCause.test.ts` and `TodayPlace.test.tsx` against the branch's base `todayCause.ts` and `TodayPlace.tsx`:
  **10 failed, 144 passed** (the three preservation cases pass: mixed sections are not "from what you've read", a book
  with questions does not ask to read further, a finished section's words are unchanged).
- Phone, `Today.plan.test.tsx` against the base `todayCause.ts`: **3 failed, 47 passed**.

New backend tests (`tests/test_part_read_first_set.py`, the eigen book through Add, the real progress report, the real
sidecar queue, `tests/part_read_helpers.SeenWriter` counting calls and keeping prompts):
`test_before_the_finish_only_the_topics_read_whole_get_their_first_set`,
`test_the_grounding_quotes_no_passage_the_learner_has_not_seen`,
`test_repeated_progress_reports_claim_nothing_twice_and_send_nothing_twice`,
`test_the_later_finish_writes_only_the_remaining_topics`,
`test_reading_on_and_finishing_during_a_blocked_call_adds_claims_and_leaves_the_frozen_work_alone`,
`test_a_topic_citing_another_section_waits_for_that_sections_passage_too`,
`test_a_learner_who_left_while_the_build_ran_gets_the_first_set_when_it_finishes` (claimed by the build's own drain, no
report or read after),
`test_reading_on_the_phone_is_saved_there_and_its_first_set_is_written_by_the_desktop` (a secondary attach records,
says `owed`, claims nothing; the desktop's read claims),
`test_the_desktop_claims_the_phones_reading_when_it_starts`,
`test_a_section_finished_on_the_phone_after_its_part_read_claims_only_the_rest_on_the_desktop`,
`test_reading_that_completes_no_topic_says_read_further`, and the four exclusion tests above.
`tests/test_first_questions_today.py`: `test_a_section_read_in_part_says_what_its_reading_can_give`,
`test_a_section_read_before_its_build_settles_waits_for_it`.

Frontend: `todayCause.test.ts` (7 cases), `TodayPlace.test.tsx` (6), `denyList.test.tsx` (the seven new cause shapes
join the plain-words sweep), the phone's `Today.plan.test.tsx` (3).

**Assertions changed:** `tests/test_reader_seen_passages.py::test_nothing_in_src_reads_the_passages_but_their_store_and_the_one_reading`
now admits exactly one reader: `reader/part_read.py` calls `seen_on`, `seen_marker` and `seen_readings`; the store's
two new reads (`reader_seen_spans_marker`, `reader_seen_readings`) are called only by `seen_passages`;
`section_ends_on` is still called by nothing. No other existing assertion changed.

## What was run

Every Python run through the scratch wrapper (empty home, config and Codex dirs); every pytest run from a script that
refuses an empty target list, `-n 1`, in a 3 GB scope, one at a time; vitest with 4 workers; npm through the shared npm
cache.

| Command | Result |
|---|---|
| `tests/test_part_read_first_set.py` (final) | 15 passed |
| The step's core files: `test_reader_seen_passages`, `test_section_question_parts`, `test_section_done_before_build`, `test_first_questions_today`, `test_reader_progression`, `test_mobile_v4_reader`, `test_empty_first_build`, `test_part_read_first_set` | 142 passed |
| `scripts/affected_tests.py --files` the changed sources | 1,352 files (over 150: the filter below was run instead) |
| The brief's name filter (section_question, section_done, reader_progress, reader_seen, first_questions, add_source, today, mobile_v4, mobile_allowlist, ingest_job, plus part_read, reader_progression, empty_first_build) united with every test file naming `reading_questions`, `mark_section_progress`, `start_waiting_sections`, `section_generation`, `source_refs_for_section`, `drain_owed_section_questions`, `accept_proposal_items`, `part_read`, `seen_passages`, `source_status_line`, `topic_question_work`, `upsert_reader_section_progress`, `get_source_library`, `after_auto_build` or `citation_bundle`: 77 files, chunks of 35, 35, 7, `-m "not arc_close"` | 822 passed (16 warnings); 551 passed, 11 skipped; 103 passed |
| `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`, `test_public_tip_guards` (after the first commit) | 403 passed |
| The same seven with `test_registry_audit`, `test_sensitivity_certificates`, `test_protection_surface_sets`, `test_figures_show_me_codex_review`, `test_part_read_first_set`, `test_section_question_parts` (after the registration) | 605 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `tests/test_architecture.py` alone | 18 passed (it first failed on two new function-local `content.pipeline → reader.part_read` edges; the imports moved to module level, as `jobs.py`'s other reader imports are) |
| `ruff check` | All checks passed! |
| `lint-imports --no-cache` | Contracts: 45 kept, 0 broken |
| `scripts/check_gate_partition.py` | collected 32363: landing 32298 + arc_close 65 |
| Desktop `npm run typecheck`; `vitest run --maxWorkers=4` (whole suite); `npm run frontend:build` | clean; 320 files, 3,390 tests passed; built |
| Phone `npm run typecheck`; `vitest run --maxWorkers=4` (whole suite); `npm run build` | clean; 43 files, 439 tests passed; built |

No identity pin, golden or snapshot moved. One structure ratchet rose during the work
(`functions_over_200_lines`: `add_source.reading_questions` reached 205 lines); the function was shortened back under
200, and no golden was raised.

## What a live-route walk must check

This is the first step a walk can see. The patient first-day persona and a learner who stops at 60 % (the design's §7
row 4), on the real desktop window and the phone:

1. **The 60 % learner:** read a built book's first section by scrolling to about 60 % and stop. Within a report
   (about 1.5 s) `reader_topic_question_work` gains `part_read` rows for exactly the topics whose every cited passage is
   in `reader_seen_spans`; Today says "Writing questions from what you’ve read …", then "N questions from what you’ve
   read … are ready." with Begin; the section is not finished in the Reader (no "Section finished", no
   `completed_at`). Straddling and later topics have no row.
2. **The content question the fixtures cannot answer:** print, for the real chapter, each topic's cited spans and the
   position of its last one (`part_read.topic_coverage`); if no topic qualifies at 60 %, Today must say "Read a little
   further …", and the result is a finding for the owner, not a reason to loosen the rule.
3. **Build finishing after the learner left:** add a book, read part of its first section while the build runs, leave
   the Reader (or the app's Today) alone: when the build applies, the rows appear with no further report, and Today
   shows them on its next read.
4. **No unseen text sent:** for one part-read request, read its frozen `…:requests` checkpoint and confirm every
   bundle's spans are in `reader_seen_spans`; for an older, note-backed book check UX-60.
5. **Reading on:** keep scrolling while the first set is written: new topics are claimed in a new batch; nothing is
   asked twice (the model-call receipts per topic).
6. **The later finish:** press "Done with this section" (or finish its quick check): only the remaining topics are
   written; Today counts all of them, now as a finished section's.
7. **The phone:** read part of a section on the phone with the desktop closed: the phone's Today says "Your reading is
   saved. Questions will be written when the desktop is running."; open the desktop: the rows appear on its start and
   the questions follow. Finish the section on the phone after a part read on the desktop: only the rest is written.
8. **Reading before the build:** Today says "Questions from what you’ve read will follow when “Book” is ready."
9. **Review:** a build that left topics for a look; accept them: topics already wholly read are claimed at once.
10. The sidecar log: no "questions from the part read were not queued" warning and no "database is locked" around a
    report.

## What was not verified

- No app, browser, server, phone or real model ran (the rules). The fake queue runs in the foreground; the
  background worker picking the claimed batch up is read, not run.
- The cost and timing of `assess` on a large real book (one IR load, one plan per read section, per change) is not
  measured; it is remembered between changes.
- Real topic maps: whether real builds' citations let a 60 % reader qualify anything (above).
- A reread of a book with part-read claims (the claims stay on the reading they were made on; Today reports them under
  that section's label, as step 3's claims are) is read, not run.
- Provider billing across a death between the provider's acceptance and the answer's checkpoint (the design's §8).
- UX-60 (note excerpts), filed, not fixed.

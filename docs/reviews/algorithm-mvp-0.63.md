# mvp-0.63: a section's end finishes it, and a quick check's close does not (the first evening, step 5)

Branch `ux/first-evening-section-end`, from main `5876c1ffa6` (latest tag `mvp-0.62`), with
`ux/first-evening-wording-and-wait` (steps 6 and 8, migration 258) merged in before the migration was written. The
owner decided on 2026-11-20 (SECTION-END) that reaching a section's last passage by the learner's own reading finishes
the section once, and that closing a quick check is not finishing a section. The design is the first evening's build
sheet (§3 "The section's end" whole; §4 "Quick-check controls above the fold"; §5's row "Automatic section end; check
no longer completes section" and "Why SECTION-END needs the tag"; §6 row 5; §7 row 5). Everything below was measured
on synthetic vaults and fakes; the owner's vaults are the orchestrator's (the last sections).

| Commit | What |
|---|---|
| `ccdecf14a0` | The tag: one constant, the chain entry, its set and predicate, one upgrade row, one test row; the mechanical moves by the tag string |
| `5481dc4eaa` | Merge of `ux/first-evening-wording-and-wait` (no conflict) |
| `c575a7a79d` | Migration 259 (the completion's cause and tag), the head fixture upgraded from 258, sixteen earlier migrations' diffs |
| `41f1597660` | The rule (`learnloop.reader.section_end`), the progress report through it, the store, the reread carry; backend tests |
| `a1d18681d7` | The desktop Reader: backend-acknowledged finish, split controls, position, the check above the fold; tests |
| `98d93f7ff3` | The phone Reader: the end finishes once the host has it, completion apart from going on; UX-59's test |
| (this record) | This record, the G2 design renumbered to `mvp-0.64`, ledger rows UX-29, UX-59 and UX-70 |

No kill switch, no config key, no prompt change, no change to the seen-passage recording, to qualification or to
grading. One migration (259), because the cause and the tag needed columns.

## The rule

`learnloop.reader.section_end.section_finish(config, completed, completed_by, end_span_id)`, the one rule the progress
report (`reader.mark_section_progress`) applies, on the desktop's sidecar and the phone host alike:

- **At mvp-0.63 and later** a section is finished by the learner's word (`completed: true` with no `completedBy`, or
  `completedBy: "learner"`: "I've read this section"; the phone and every older client send it so) or by an
  acknowledged end observation: the end the report's own check keeps (`seen_passages.check_report`'s `end_span_id`:
  the section's last readable passage, observed during the learner's own reading and among this report's or an earlier
  report's kept passages). `completedBy: "check_closed"` (a quick check's "Done with this check") and
  `completedBy: "idea_chosen"` (the choice of what to do with its idea) finish nothing. The completion stores its cause,
  `reached_end` or `learner_said` (the learner's word wins when one report carries both), and the vault's tag.
- **Below the tag** every completion the Reader sends finishes the section, a check's close and an idea's choice
  included, an end finishes nothing, and no cause or tag is stored: mvp-0.62 exactly.

The Reader sends each event as what it is and the backend decides by the vault's tag, so neither app needs to know the
tag, and one backend operation serves the automatic end and the explicit completion. Both reach the same
`upsert_reader_section_progress(completed=…)`, the same `start_section_questions` (the part read's later finish
included), the same phone-host deferral and the same plan-block ending.

**Once.** `completed_at` is stamped once (`COALESCE`); the cause and tag are written in the same statement, only when
that statement first stamps `completed_at` (a `CASE` on the old row), so a second report returns the original
completion, cause and tag. The questions start only when the generation stamp allows (unchanged); the plan is told
`completed=True` only for the first finish at the tag (below it, every completion report is passed on, as before;
`note_reading_progress` itself only ends a current block). A report naming an end again after the section is finished
changes nothing.

**What does not finish a section.** Opening, restoring, searching, a Contents choice, a margin jump, a seek and layout
settling send no end (step 2's and UX-62's client rules, unchanged and re-tested); a full count (the "left after 60 %"
shortcut can fill it), all passages seen without an end, and an end whose last passage was never seen finish nothing.
An end recorded before the upgrade finishes nothing: only a new report carrying an end does.

## The tag

- `SECTION_END_ALGORITHM_VERSION = "mvp-0.63"`, appended to `SUCCESSOR_CHAIN`; `SECTION_END_VERSIONS =
  successors_from(it)`; one predicate, `section_end_on(config)`, read by `section_finish` alone.
- `Link(SECTION_END_ALGORITHM_VERSION, idempotent_projection)`: **only new events behave differently.** The playbook's
  rule (step 3, and the table's comment "most successors are this: new behaviour behind the tag for new events only"):
  no projection is derived from section completions (`reader_section_progress` is WORKFLOW, never replayed or
  cleared), so nothing already derived moves and no whole-vault rebuild is needed; the design asks for a future-events
  activation with no historical end turned into a completion and no completion or exposure receipt cleared, which the
  projection activation does by doing nothing to these rows.
- One test row in `tests/test_upgrades.py`'s `EXPECTED_ACTIVATIONS`.
- Effective defaults: only the `algorithms.algorithm_version` line (no key added).

## What activates at the tag, and what stays below it

| | Below mvp-0.63 (as mvp-0.62) | At mvp-0.63 |
|---|---|---|
| The section's end observed by the learner's own reading | recorded (`reader_section_ends`), finishes nothing | recorded, and finishes the section (cause `reached_end`) |
| "I've read this section" (desktop), the phone's button | finishes it (no cause stored) | finishes it (cause `learner_said`) |
| A quick check's "Done with this check" (both desktop cards) | finishes it (the old "done for now") | closes the check only |
| The idea's choice on a placed question | finishes it | changes nothing about the section |
| Cause and tag columns | NULL | written with the first completion |
| Plan block | every completion report is passed on | ends on the first finish only |

The Reader's words are the new ones at both tags; what shows finished is always the backend's answer, so below the tag
closing a check shows the section finished (as its completion then was), and at the tag it does not.

## Every reader of a section's completion, and what the new cause changes

`reader_section_progress.completed_at` at this tip (after the merge). "When" means: from the tag the completion can be
written by the learner's reading reaching the end without a press, and is no longer written by a check's close or an
idea's choice. None of these readers reads the cause or the tag; none treats a completion as evidence of understanding,
and none certifies (each is a reading, workflow or display fact, as before).

| Reader | What it does with the completion | What changes |
|---|---|---|
| `src/learnloop_sidecar/handlers/reader.py:2132` (`first_finish`), `:2161` (the questions' start), `:2216` (the plan) | starts the section's questions once; ends a current reading block | the when, through `section_finish`; the plan hears only the first finish at the tag |
| `src/learnloop_sidecar/section_questions.py:103`; `src/learnloop/db/stores/reader.py:1376` (`deferred_section_generations`) | the desktop's drain of sections the phone finished or that waited for their build | the when (a phone end now leaves `deferred_to_primary` too) |
| `src/learnloop/reader/part_read.py:450`, `:471`, `:547` | a finished section's remaining topics go through the later finish; Today's part-read facts | the when |
| `src/learnloop/content/pipeline/add_source.py:2762`, `:2797` (`reading_questions`) | Today's facts: finished sections' questions vs part-read ones | the when |
| `src/learnloop/daily_plan/next_practice.py:213` | counts finished sections waiting for their questions | the when |
| `src/learnloop/reading_sources.py:100` | a finished section is a `section_read` reading opportunity and its worked examples `in_completed_section`, for AD's receipts (`adaptive_difficulty/reading.py:16`, authority `salience_only`) and data capture's `reading_exposure_receipts` | the when: a section read to its end now gives this exposure without a press; a section whose check was closed no longer does. Exposure (salience), never a grade or a certificate |
| `src/learnloop/data_capture/reading_exposures.py:250` (`db/stores/data_capture.py:208`) | a completed section's LOs as exposures, read live | the when |
| `src/learnloop/instructional/exposure.py:114`, `src/learnloop/db/stores/source_service.py:811` | a completed (or count-full) section's worked examples count as studied for the independent-check exposure rule | the when; the rule already counted a full count, so a section read to its end mostly counted already. More exposure makes fewer items count as independent, the conservative direction |
| `src/learnloop/daily_plan/reading.py:199`, `:287`; `src/learnloop/daily_plan/engine.py:487` | a finished section is no reading step; progress exists | the when |
| `src/learnloop/figures/prefetch.py:1524` | a section's finish time, for figure prefetch timing | the when |
| `src/learnloop/reader/recap.py:229`, `:411` | "Last time here": sections completed in a session | the when |
| `src/learnloop/source_retrieval/deliverable_path.py:393`, `:1572`; `reading_paths.py:1004`; `section_coverage.py:2078` | a section read or done for paths and minutes left | the when |
| `src/learnloop/content/pipeline/reread.py:297`-`:320`, `:560`; `db/stores/reader.py` `carry_reader_section_progress` | a completion carried to a new reading (now with its cause and tag) | the cause and tag carried; nothing else |
| `src/learnloop_sidecar/handlers/reader.py:2053` (`_progress_payload`) and the apps | `completedAt` in the reply and `reader.get_progress` | the apps now show finished only from it (below) |
| Desktop: Contents tick, the check-offer rule, the authoring trigger, the section-break offer, `DoseOffer` | read `completedSections` | `completedSections` grows only by the backend's answer; a check already open is no longer closed by its section finishing |
| Phone: `SectionList`, the footer | read the progress list | the footer shows "Section finished" from it |

`learner_context.py:1198` reads a remediation episode's `completed_at`, not a section's.

## What does not move on upgrade

The upgrade is the idempotent projection: no whole-vault rebuild, no migration data change. `reader_section_progress`
rows (their `completed_at`, stamps and counts), `reader_section_ends`, `reader_seen_spans`, reading-opportunity and
exposure receipts, plan block events and topic claims are left as they are; an end recorded before the upgrade is not
turned into a completion; a completion recorded before it keeps NULL cause and tag (it could have come from a check's
close). Mastery, facet and scheduling projections do not read completions. Only reports after the upgrade use the new
rule.

## The controls and states, before and after

Desktop (the guide's section card and its quick-check cards):

| | Before | After |
|---|---|---|
| Section control | "Done with this section", shown only once the Contents' "read" rule held | "I’ve read this section", shown from the section's start (a short section that needs no scrolling can be finished) |
| Finished state | "✓ Done with this section." shown at once (optimistically) | "Section finished" (or what the finish started: "Writing questions from this section. They'll be on Today." / the waiting line) only from the backend's answer; a failed save says "Couldn't save that. Try again." and keeps the control |
| After finishing | nothing | "Read the next section" (moves the reading there; navigation only), or "Back to Today" at the book's last section; no "Keep reading at your own pace." on a finished section |
| A section finished by its end | impossible | the same state, from the save's answer; a check already open stays open |
| Quick check close | "done for now" (finished the section) | "Done with this check" (closes the check; finishes the section only below the tag) |
| Idea's choice | finished the section and closed the card | passed on as `idea_chosen`; the card stays until "Done with this check" |
| Section bar | "Read of this section", forced to 100 % on completion | "Position through this section" and "N% through this section", never forced |
| Header bar | "N% read" | "N% through the book" |
| Check placement | under the section card and the guide's header and path | first in the guide; its action area right under the answer box and, after the comparison, right under the learner's answer (before the intended answer), brought into the guide's own view; "Done with this check" takes focus when the answer box goes |

Phone (the section's foot):

| | Before | After |
|---|---|---|
| Foot | one button: "Next section" / "Finish the book's last section" / "Done with this section" (plan), which completed, drew the dose, then moved on | "I’ve read this section" (completes through the outbox, draws the dose once, stays) and "Read the next section" / "Back to Today" (navigation only); under the plan the banner's "Back to today's plan", and after finishing a foot "Back to today's plan" |
| Reaching the end | queued the end, nothing else | queues the end; once the outbox has delivered it, reads the host's progress: if the section is finished there (the tag), "Section finished" and the dose, once, no move |
| Dose question | "Done for now" | "Done with this check" |

## UX-59: refuted

The finding said the phone's count observer is rooted at the section's `.book` box. It is not: the count's
`new IntersectionObserver(callback)` gets no options (root: the viewport, clipped by the scroller); `const root =
body.current` there only finds the passages to observe. No commit of the file ever passed a root. A test
(`apps/learnloop-mobile/src/read/sectionEnd.test.tsx`, "UX-59: …") pins that every observer the Reader makes has no root
and that one passage on screen reports `spansSeen: 1` of 3; it passes before and after this step. Nothing is fixed, and
Contents and Today's reading step show nothing different. The stale comments repeating the claim are corrected. Not
seen on a real phone.

## Pins and goldens that moved

- **The tag commit, by the tag string alone** (as at mvp-0.62): `tests/goldens/identities.toml` nine pins
  (`A1-A4.manifest_hash.init`, `C3.boundary.init`, `C3.boundary_offer.init`, `C3b.chooser`, `C3b.chooser_offer`,
  `C3b.start_key`, `C3b.start_key_offer`, `C5.init`, `C6.init`: the six of mvp-0.62's tag and the three mvp-0.62 added),
  regenerated with `tests/test_identity_pins.py --write`; `tests/goldens/effective_defaults.toml` (the algorithm line);
  `tests/cli_surface.json` (`upgrade --to`'s default, edited by hand); `tests/goldens/placement_stored_misses.json`
  (its manifest's tag); `tests/fixtures/diagnosis_journey_golden.json` (311 tag strings and its two decision states'
  config and snapshot hashes, nothing else); latest-tag and chain-position pins in 39 earlier successors' test files,
  `tests/test_check_credit_activation.py::test_the_tag` among them (mvp-0.62 is now `SUCCESSOR_CHAIN[-2]` and its set
  holds mvp-0.63).
- **The behaviour commits**: no identity pin moved and none was added (completion is no compared identity). No golden
  moved. Desktop: six switch-off snapshot files (26 snapshots: `intentSwitchOff`, `libraryAskSwitchOff`,
  `readingPathsSwitchOff`, `recapSwitchOff`, `tutorSwitchOff`, `workbench/switchOff`) moved by the header bar's
  `aria-label` alone ("100% read" → "100% through the book"), checked by a markup diff. Pinned draws: no node id changed.
- **Migration**: the head fixture holds 259; sixteen earlier migrations' "nothing else changed" diffs admit
  `SECTION_END_ALTERED_TABLES` (`tests/reader_section_completion_migration_helpers.py`) beside K3.5's.
- **Assertions changed**: `tests/test_reader_seen_passages.py`'s end test pinned at mvp-0.62 and renamed
  `test_below_the_tag_reaching_the_end_…`; desktop `sectionDone.test.tsx` rewritten to the split controls (its
  "absent before the section's last passage is read" and "the same completion as done for now" premises are gone, and
  its finished-state words are "Section finished"); two progressbar queries renamed ("Position through this section");
  the phone's `Reader.test.tsx` and `seenPassages.test.tsx` press "I’ve read this section" then "Read the next
  section" where they pressed "Next section" (which did both). Structure ratchets: no count rose.

## Both tags

| Test | mvp-0.62 | mvp-0.63 |
|---|---|---|
| `tests/test_section_end.py::test_both_tags_reading_to_the_end` | the end recorded; no completion, no questions, the plan told `completed=False` | finished, cause `reached_end`, tag `mvp-0.63`, the questions started once, the plan told `True` |
| `::test_both_tags_closing_a_quick_check_or_choosing_its_ideas_fate[check_closed / idea_chosen]` | finished (no cause), questions started | nothing finished, nothing started |
| `::test_both_tags_the_learner_says_they_read_it[None / learner]` | finished (no cause) | finished, `learner_said` |
| `::test_both_tags_the_end_and_the_learners_word_end_one_reading_block` | the end ends no block; the learner's word ends it; one ending | the end ends it; the word and a repeated end end nothing more; one ending |
| `::test_below_the_tag_the_phones_end_finishes_nothing` / `::test_the_phones_end_finishes_the_section_once_for_the_desktop_to_write` | nothing finished | finished, `deferred_to_primary`; a duplicate delivery and a repeated end change nothing |
| `::test_the_upgrade_finishes_nothing_recorded_before_it_and_a_new_end_finishes_once` | history: a check-closed completion, an end | after the upgrade and a whole-vault rebuild both tables byte-equal; a new end finishes the other section once |
| Desktop `sectionEnd.test.tsx` "below the tag an end finishes nothing" / "reading to the section's end finishes it…" | the backend answers unfinished: nothing shown | answered finished: shown, with what it started |
| Phone `sectionEnd.test.tsx` "below the tag…" / "reading to the end…" | no "Section finished", no dose; the word finishes and draws once | "Section finished" and the dose once, no move |

Also at the tag: `test_the_end_and_the_explicit_completion_are_one_completion`, `test_the_learner_first_then_the_end_keeps_the_learners_completion`,
`test_no_end_no_finish`, `test_an_end_on_a_section_already_finished_below_the_tag_changes_nothing`,
`test_reading_to_the_end_writes_only_the_topics_the_part_read_left` (the eigen book: the part read wrote two topics,
the end writes the other three, every topic asked once, a second end and the button ask nothing),
`test_reaching_the_end_before_the_build_waits_for_it_then_writes` (`waiting_for_build`, then written after the build).

**Fail-first.** Backend: `tests/test_section_end.py` against the old handler and store (migration present): 16 failed,
6 passed (the tag test and the below-the-tag arms). Desktop `sectionEnd.test.tsx` and `sectionDone.test.tsx` against
the base hook and rail: 15 failed, 7 passed (below-the-tag, the writing and waiting lines, offline, the open check, the
questions-from line). `checkControls.test.tsx`: 3 failed, 1 passed (typed work and focus surviving a refresh held on
the base rail; the hook test "a quick check the learner has open stays open…" is the one that failed there). Phone
`sectionEnd.test.tsx`, `Reader.test.tsx`, `seenPassages.test.tsx` against the base Reader: 11 failed, 6 passed (UX-59's
refutation among the passes).

## Judgment calls to read first

1. **The tag lives in the backend; the apps send what happened.** The apps do not know the vault's tag, so each sends
   the event as what it is (`completedBy`) and shows finished only from the backend's answer. Below the tag the new
   words show, and a check's close then shows the section finished (as its completion did). An outbox record queued by
   an older phone carries no `completedBy` and counts as the learner's word.
2. **The phone shows the learner's word at once** (durably queued; it finishes at both tags) but an end only after the
   outbox delivered it and the host's progress says finished (so below the tag nothing shows and no dose is drawn: the
   dose arm's trigger is persisted meaning). Offline, an end shows nothing until a later progress read.
3. **A check already open stays open when its section finishes** (`settled` is a dismissal, or a completion of a check
   not yet offered): otherwise the end arriving mid-answer unmounts the card and loses typed work. Below the tag an
   idea's choice therefore no longer closes the card by itself; "Done with this check" does.
4. **No sticky action area.** A sticky bar covers whatever scrolls under it (the answer box or the learner's answer);
   instead the action area sits right under the box, stays in the same place after the comparison (above the intended
   answer), and is brought into the guide's own view with `scrollIntoViewWithin` (the guide only, never the chapter).
5. **The plan hears only the first finish at the tag.** `note_reading_progress` ends only a current block, but a
   repeated end could otherwise meet a later block on the same section.
6. **The cause and tag columns are NULL below the tag**, not "learner_said": a below-tag completion could have been a
   check's close.
7. **"Back to Today" at the end of any book's last section**, not only a one-section book (the design's row names the
   one-section book; a last section has no next either). Today's own "Keep reading meanwhile." while a finished book's
   questions are written is Today's wording: filed as UX-70, not changed here.

## Playbook gates (synthetic; the owner copies are the orchestrator's)

Every Python run through the scratch wrapper, `-n 1`, in a 3 GB scope, one at a time; vitest with four workers.

| Gate | Command | Result |
|---|---|---|
| Effective defaults (step 4) | `tests/test_effective_defaults_golden.py --write`, then the test | the algorithm line only; passed |
| Identity review (step 4) | `tests/test_identity_pins.py --write` at the tag commit; the test after each source commit | nine tag pins at the tag; none moved after |
| Upgrade path, recovery, idempotent re-run (step 8) | `tests/test_upgrades.py` (every row incl. mvp-0.63) | 194 passed at the tag; passed in the gate set below |
| Replay and rebuild equivalence (step 6) | the upgrade and rebuild files in the name filter; `test_the_upgrade_finishes_nothing_recorded_before_it…` (activation and a whole-vault rebuild leave both tables byte-equal) | passed |
| Shadow rebuild on copies, foreign keys, doctor, live hash, second rebuild (steps 7, 8) | the orchestrator's (below) | not run here |
| Tag commit's own files (44: the moved successor files, pins, defaults, CLI snapshot, placement, journey golden, upgrades) | | 1200 passed, 12 skipped, 3 xfailed |
| Migration diffs (46 files naming migration objects, then the 16 edited) | | 284 passed + 22 then 53 + 32 passed after the edits |
| `tests/test_section_end.py` | | 22 passed |
| The brief's name filter (reader, section_done, section_question, part_read, first_questions, reading_sources, daily_plan, quick_check, upgrades, algorithm_version, effective_defaults, diagnosis_journey, due_queue, mobile_v4, mobile_allowlist, successor, reread) united with the files naming `mark_section_progress`, `reader_section_progress`, `carry_reader_section_progress`, `upsert_reader_section_progress` or `section_end`: 216 of `scripts/affected_tests.py`'s 1,376, six chunks, `-m "not arc_close"` | | 551 passed (2 failed: `test_ad1_migration`, fixed with the five later diffs), 965, 513, 718, 8992 passed (2 failed: the step-2 end test and the readers guard, fixed: below), 337 passed |
| `test_reader_seen_passages` after the fixes | | 16 passed |
| `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`, `test_public_tip_guards`, `test_ingest_queue_store`, `test_section_end`, `test_upgrades`, `test_retired_config_identities`, `test_diagnosis_journey_golden`, `test_migrations`, `test_ad_protected_tables`, `test_tracked_fixture_databases` | | 718 passed |
| `tests/test_test_layout.py` alone; `tests/test_architecture.py` alone | | 3 passed; 18 passed |
| `ruff check`; `lint-imports --no-cache`; `scripts/check_gate_partition.py` | | All checks passed; 45 kept, 0 broken; collected 32805: landing 32739 + arc_close 66 |
| Desktop `npm run typecheck`; `vitest run --maxWorkers=4`; `npm run frontend:build` | | clean; 326 files, 3593 tests passed; built |
| Phone `npm run typecheck`; `vitest run --maxWorkers=4`; `npm run build` | | clean; 44 files, 461 tests passed; built |
| `db_generate_reference.py`; `db_validate_reference.py` | | `schema_head` 259, 401 table notes; `"errors": []`. Their output was restored, not committed: the landing regenerates |

The readers guard (`test_nothing_in_src_reads_the_passages_…`) failed on a comment in `algorithm_versions.py` naming
the end table; the comment now says "as the progress report records it" (no new reader of the tables: the rule reads
the end the report's own check returns). `desktop_validate.py`: no count moved (no new non-test TypeScript file); it
reports the changed modules' notes stale and step 6's new `waitDetail.ts` note missing (the landing regenerates).

## What the orchestrator must run on owner copies

On idle backup-API copies of `arxiv_v2`, `linear_algebra` and `probability`, with this branch:

1. Record the live databases' SHA-256.
2. Before: dump `reader_section_progress` (every column), `reader_section_ends`, `ad_reading_opportunities` and
   `reading_exposure_receipts` counts, and the plan's `attention_block_events` count; note how many sections have an end
   row and no `completed_at` (those stay unfinished after the upgrade).
3. `learnloop upgrade --vault "$COPY" --to mvp-0.63` (the copies at mvp-0.62 after mvp-0.62's landing, or earlier ones
   through it): expect `completed the activation of mvp-0.63 (its projection activation)`; the migration to 259 on open
   adds two NULL columns.
4. `learnloop rebuild --shadow --json --vault "$COPY"`: zero mastery, facet and scheduling deltas (rows differing only
   in their `algorithm_version` stamp are what a projection activation leaves, as at mvp-0.62).
5. The dumps of step 2 again: byte-equal apart from the two new columns, all NULL; no section newly finished.
6. `learnloop doctor --vault "$COPY"`, `PRAGMA foreign_key_check`, `integrity_check`: clean (pre-existing content
   findings aside).
7. A second shadow rebuild identical to the first; the live databases' SHA-256 unchanged.

## What a live-route walk must check

With the patient first-day persona and the learner who stops at 60 % (§7 row 5), on the real desktop window (WebKitGTK)
and the phone:

1. **The end finishes, once, with no press**: read a section to its last passage by scrolling: the guide shows
   "Section finished" (or "Writing questions from this section…") within a save (about 1.5 s); `reader_section_progress`
   has `completed_at`, `completion_cause = 'reached_end'`, `completion_algorithm_version = 'mvp-0.63'`; the reading
   block (if the plan sent the learner) ends once; the dose offer, if drawn, appears once.
2. **A skim to the bottom** by the learner's own scrolling finishes it; **reopening the book at the end** (a restore), a
   Contents jump to the last passage, the End key landing in one frame after a jump: nothing finishes until the learner
   moves.
3. **"Done with this check" closes only the check**: the section stays unfinished (Contents, the guide, Today's facts);
   the idea's choice likewise.
4. **A short section** that fits the window: "I’ve read this section" finishes it.
5. **A save failing** (stop the sidecar briefly while reaching the end): no "Section finished" until a retry lands.
6. **Read the next section** only moves; **the book's last section** offers "Back to Today" and no keep-reading line in
   the Reader (Today's "Keep reading meanwhile." is UX-70).
7. **The check above the fold**: opening a check shows its question, the answer box and compare/skip without scrolling
   the guide; after comparing, "Done with this check" is visible and focused; reading on to the section's end while
   typing in a check keeps the text and the focus. Check at a narrow window and with the keyboard only.
8. **The position bar** says "N% through this section" and is not forced to 100 % on finishing.
9. **The phone**: reach a section's end by scrolling with the desktop up: "Section finished" and the dose once, no
   move; with the desktop away: nothing shown until the outbox delivers and a later read; "I’ve read this section" then
   "Read the next section".
10. The 60 % learner: no finish without reaching the end; part-read questions unchanged; finishing later writes only
    the remaining topics.

## The owner-copy lane, as run (2026-11-21; aggregates only)

Backup-API copies of the owner's three vaults in a gitignored directory, with this branch; the copies were
deleted afterwards. The live databases' SHA-256 were equal before the copy, after it and at the end.

| | arxiv_v2 | linear_algebra | probability |
|---|---|---|---|
| Tag before | mvp-0.61 | mvp-0.58 | mvp-0.58 |
| `learnloop upgrade --to mvp-0.63` | upgraded | upgraded | upgraded |
| Section progress rows; finished, before and after | 12; 5 and 5 | 13; 13 and 13 | 9; 8 and 8 |
| Digest of the progress rows (section, counts, completion, stamp), before and after | equal | equal | equal |
| Completions with a cause after the upgrade | 0 | 0 | 0 |
| Recorded ends; ends without a completion | 0; 0 | 0; 0 | 0; 0 |
| Shadow rebuild: mastery, facet and schedule VALUES that differ | 0 | 0 | 0 |
| Rows that differ only in their `algorithm_version` stamp | 37 mastery, 12 facet | 21 mastery, 4 facet | 18 mastery, 1 facet |
| A second shadow rebuild | identical | identical | identical |
| `foreign_key_check`; `integrity_check` | 0 rows; ok | 0 rows; ok | 0 rows; ok |
| Attempts and receipt counts before and after | equal | equal | equal |

No section is newly finished by the upgrade, no completion gains a cause, and no end existed to be turned
into one (the owner's vaults predate the seen-passage tables). Doctor's errors are the content findings that
predate this tag (see `algorithm-mvp-0.62.md`).

## Remaining limitations

- The phone learns an end's finish only after a delivered outbox flush and a progress read; an end delivered on a later
  flush (offline at the time) shows on the next progress read, and its dose is drawn only if the section is still open
  in that visit.
- The desktop's end retries three times and on leaving the book or the Reader (step 2's save); an app quit with the
  end unsaved loses that end: the next reading to the end, or the learner's word, finishes it.
- Below the tag the new words show while a check's close still finishes the section.
- UX-70 (Today's "Keep reading meanwhile." for a finished book) is open.

## Not verified

- No app, browser, WebKitGTK window or phone was run (the rules): fold, focus and scrolling are tested on jsdom and
  fakes; `scrollIntoViewWithin`'s effect on the real guide scroller is not.
- The owner's vaults and the comparison on copies (the orchestrator's); the landing gate and the whole suite;
  durability (`--durable-sqlite`) on the new tests; the arc-close gate.
- Real iOS `IntersectionObserver` behaviour for UX-59.
- The vault references are not regenerated (the landing does).

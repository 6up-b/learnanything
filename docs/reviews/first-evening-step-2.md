# The first evening, step 2: which passages were seen, and a section's end

Step 2 of the stage "The first evening, finished" (the design's §2 "Passage evidence", §3's "automatic event"
paragraph, §5's row "Exact seen spans" and §6's row 2). The owner decided on 2026-11-20 that a first set of questions
is written from the part of a section read, and that a section's end finishes it; those behaviours are steps 4 and 5.
This step records facts only: nothing is generated, scheduled, finished or shown differently. Branch
`ux/first-evening-seen-spans` from main `4e824350ba`.

| Commit | What |
|---|---|
| `c5d2e2fd99` | Migration 256 (two tables), their table roles and AD classes, the head fixture upgraded in place, earlier migrations' diffs |
| `8bb333fb10` | `reader.mark_section_progress` takes `seenSpanIds` and `reachedEnd`; `learnloop.reader.seen_passages` checks and reads them |
| `116ee46b49` | Comments and docstrings of the two commits above name no stage |
| `3fc5db57c4` | The desktop Reader reports the passages its learner's own reading observed, and a section's end |
| `0d6ee615c1` | The phone Reader does the same through its outbox, which unions them |

This record and the ledger row UX-59 (a defect found by reading, not fixed here) are the last commit. No algorithm
tag, no config key, no kill switch, no prompt change. No new non-test TypeScript file:
`desktop_validate.py`'s counts do not move.

## What is recorded, and by whom

- **`reader_seen_spans`**: one row per passage of one reading (identity `(extraction_id, span_id)`), with the section
  it was reported in, the first time it was reported and the origin (`desktop` or `phone`). Written by
  `reader.mark_section_progress` when the report names `seenSpanIds`.
- **`reader_section_ends`**: one row per section of one reading (identity `(extraction_id, section_id)`), with the
  section's last readable passage (`span_id`), the first time and the origin. Written when the report says
  `reachedEnd`.

The origin is the host's, never a parameter: `phone` when the phone host runs the call (`ctx.request_origin`, set
from the paired token), `desktop` otherwise.

**Checked before anything is written** (`learnloop.reader.seen_passages.check_report`): every id must be one of the
section's readable passages on that reading (`section_map.extraction_sections`, the one section definition the guide,
the phone and the quick checks share); an unknown reading, an unknown section or a passage of another section refuses
the whole report (`validation_error`), its count included, so a client's mistake never lands half a report. An end
needs the section's last readable passage seen, in this report or an earlier one on the same reading.

**Nothing acts on either.** A section is finished exactly as before (only `completed: true` stamps `completed_at`); the
generation trigger, the plan's reading block (`note_reading_progress` is told `completed=False` for an end) and the
reply (`progress`, `enqueuedGeneration`, `waitingForBuild`, `batchId`, unchanged keys) are as they were. `reader.get_progress`
returns the same keys as before.

## The table and its role; the migration

`256_reader_seen_spans.sql` (the next free number in `migrations/` when written; 255 was the head): two tables, each
append-only by a `no_update` and a `no_delete` trigger, `origin` checked `IN ('desktop', 'phone')`, and one index
`idx_reader_seen_spans_section (extraction_id, section_id)`. No backfill: `reader_section_progress` keeps its counts,
and a count is never turned into passages (the phone's count cannot say which passages were seen).

- **Table role: `WORKFLOW`** for both (`db/table_roles.py`), as `reader_section_progress` beside them: never cleared
  by a rebuild (only `DERIVED` is), and outside the dataset export and the adjudication evidence, which take
  `RAW_LEDGER` and `RECEIPT` tables (`db/stores/collection.py`, `substrate/dataset.py`). `RAW_LEDGER` was the other
  candidate (inputs to a later computation); it would have put the rows into the export now, which is a reader.
- **Adaptive difficulty: `DENIED`** for both (`adaptive_difficulty/protected_tables.py`): never read inside an AD
  operation. Their columns are classed `metadata` (`column_classes.py`).
- **Head fixture** (`fixtures/migration_head/`, its README section): upgraded in place by the B1 procedure. A
  backup-API copy of the tracked `state.sqlite` into the scratch directory (`learnloop.db.copies.backup_database`),
  `apply_migrations` under `upgrade_allowance(UPGRADE_SCRATCH_COPY)`, which applied `[256]` only;
  `wal_checkpoint(TRUNCATE)` `(0, 0, 0)`, `journal_mode=DELETE`, header bytes `01 01`, `integrity_check` ok,
  `foreign_key_check` empty; the tracked file removed and the copy written into its place with `backup_database`, no
  companion files. Compared with the 255 file: nine objects added (the two tables, their two autoindexes, the index,
  four triggers), no existing object's definition changed, and only `schema_migrations` gained a row (256).
- **Earlier migrations' "nothing else changed" diffs**: 17 test files admit `SEEN_SPANS_ADDED_OBJECTS`
  (`tests/reader_seen_spans_migration_helpers.py`), by a scripted edit beside each `B1_ADDED_OBJECTS` use (`-` in a
  subtraction, `|` in a union) and one import line each: `test_ad1_migration`, `test_ad23_migration`,
  `test_approach_maps_schema`, `test_data_capture_migration`, `test_help_assist_figures_migration`,
  `test_help_assist_work_md_migration`, `test_help_assists_schema`, `test_learner_claim_application_migration`,
  `test_learner_claim_superseded_migration`, `test_library_asks_migration`, `test_reader_ca2_fix_orchestrator`,
  `test_reader_rw3b_migration`, `test_reader_rw7a_migration`, `test_retrieval_spaces_migration`,
  `test_rw2d_receipts_migration`, `test_section_coverage_migration`, `test_t1_batch_origin_migration`. No other
  assertion changed.
- **The vault's database reference** is regenerated by the landing (`db_generate_reference.py`); this branch ran both
  scripts and committed none of their output (results below).

## What the desktop sends, and when it sends nothing

The report the Reader already sends (`readerNoteReadingProgress`, debounced 1.5 s, retried three times, sent again on
leaving the book or the Reader) gains `seenSpanIds` (only the passages not yet acknowledged) and `reachedEnd`, each
present only when there is something to say, so a count-only report is byte for byte the old one.

A passage is **observed** (`observedPassages`, `screens/reader/useReadingProgress.ts`) only where the count's own guard
passes: after the learner moved the page themselves (wheel, keys, touch, the scrollbar; or playback advancing), once
placement has settled:

- the text view and a video's transcript: the passage under the reading marker;
- a page-only PDF (passages know only their page): a page's passages share it in order (as `spanOnPage` reads them),
  and one is observed once the marker is 85 % through its share (the count's within-page rule, which this is for a page
  with one passage), or once the learner's own reading carries the marker forward past it.

It sends **nothing** for: a restore, a search hit or a return (placed, not read); a jump (Contents, a margin mark, a
citation); a seek of a video; a placement without a jump; the count's position-derived prefix (a resume at the fourth
passage counts four, observes one); the count's "left after 60 %" rule (a section's count can be full without its end);
the "Done with this section" and quick-check completion (the completion alone, as before); a guide answered for
another reading. A section's **end** is its last passage observed that way, sent with it.

Passages the backend refuses as not the section's (`validation_error`) are dropped and never sent again, so the counts
beside them still save.

## What the phone sends, and when it sends nothing

The phone's count is unchanged. Beside it, `apps/learnloop-mobile/src/read/ReaderScreen.tsx` records the passages **on screen** (an
`IntersectionObserver` with no root: the viewport, through the app frame's clip) **once the learner has moved the page
themselves** in this visit to the section: a scroll heard on the document within 1.2 s of their touch, wheel or scroll
key (the desktop's rule). Opening a section (Continue reading, Next, the section list) observes nothing until they
scroll; a scroll they did not make (the page settling) observes nothing; a passage held out from the phone (a
placeholder, `data-withheld`) is never read, so a section whose last passage is held out never reaches its end on the
phone; "Next section" / "Done with this section" sends the completion alone. The end is the section's last passage so
observed. Each passage and end is queued once per section.

## The union rule

- **The host**: `INSERT … ON CONFLICT DO NOTHING` on each identity, in the progress upsert's transaction. A repeated,
  a smaller, an empty or a replayed report removes nothing and keeps each passage's first time and origin; a report
  with no ids touches neither table. The same for an end.
- **The phone's outbox**: queued reports of one section coalesce into one (as before), now taking the **union** of
  `seenSpanIds` and keeping `reachedEnd` beside `completed` and `revealed`; counts stay the larger. The stored record
  shape is unchanged (`params` is open; records queued before this merge as before).
- **The desktop**: each passage is sent until acknowledged, then never again; a failed save sends it again.
- **Rereads**: `seen_on(repository, extraction_id)` reads a reading's own rows and the book's other readings' through
  **exact aliases only**: `content.sources.span_aliases.SpanTranslator` (persisted `source_span_reanchors`, else the
  same computation in memory), status `current` (match kinds `exact_hash` and `manual`). A changed passage
  (`needs_reanchor`) or one with no alias carries nothing. Nothing is written onto the new reading; a late report on
  the old reading (a phone away while the book was read again) carries too. The earliest observation wins. Ends are
  read on their own reading only (`section_ends_on`).

## The readers

**None but tests.** Nothing in `src` reads either table but the store; the store's two reads
(`reader_seen_spans_for`, `reader_section_ends_for`) are called only by `learnloop.reader.seen_passages`; and its two
reads (`seen_on`, `section_ends_on`) are called by nothing in `src`. The one read inside `src` is the check of an end
(`check_report` reads the reading's recorded passages to accept an end whose last passage came in an earlier report).
No mastery, exposure, scheduling, reading-credit or generation reader reads them; AD is denied both.
`tests/test_reader_seen_passages.py::test_nothing_in_src_reads_the_passages_but_their_store_and_the_one_reading` fails
on a new reader, on purpose: it belongs to the step that makes the rows mean something (step 4).

## Tests, with fail-first evidence

Backend, `tests/test_reader_seen_passages.py` (new; the real handler on the synthetic three-section book of
`tests/mobile_v4_reader_helpers.py`, the phone through the real host, rereads on `tests/reread_safety_helpers.py`'s
`studied`). Run against main's handler (store, module and migration present): **13 failed, 6 passed** (the 4 migration
tests, and the two "nothing invented" guards that hold on main too: a count or a completion makes no passage, and the
readers guard):

- `test_a_report_records_each_observed_passage_once_with_its_section_time_and_origin`
- `test_a_report_naming_a_passage_not_in_its_reading_and_section_is_refused_whole` (unknown passage, another section's, unknown section)
- `test_a_report_on_a_reading_that_does_not_exist_is_refused`
- `test_reports_union_and_a_smaller_report_removes_nothing_or_changes_a_first_observation` (desktop then phone)
- `test_a_duplicate_report_and_an_outbox_replay_write_nothing_new`
- `test_the_passages_survive_a_restart_and_later_reports_union_with_them` (and `get_progress` keeps its keys)
- `test_a_count_or_a_completion_is_never_turned_into_passages`
- `test_reaching_the_end_is_recorded_with_its_origin_and_acted_on_by_nothing` (no `completed_at`, no generation start, the plan told `completed=False`, the same reply keys; the phone's end is `phone`; a second end keeps the first)
- `test_an_end_is_recorded_only_when_its_last_passage_is_seen`
- `test_an_exact_alias_carries_a_seen_passage_to_a_reread_and_a_changed_one_does_not` (aliases recorded, and computed)
- `test_section_ends_are_read_on_their_own_reading_only`
- `test_nothing_in_src_reads_the_passages_but_their_store_and_the_one_reading`

Migration, `tests/test_reader_seen_spans_migration.py` (new): both tables `WORKFLOW` and AD `DENIED`; the head fixture
holds both empty in rollback mode; a vault one below the head gains exactly `SEEN_SPANS_ADDED_OBJECTS` and nothing
else (`reader_section_progress`'s rows unchanged); one row per identity, a known origin, append-only. Before the
migration existed the file failed to collect (`StopIteration`: no `reader_seen_spans` migration).

Desktop, `screens/reader/seenPassages.test.tsx` (new; the hook on fake RPCs). Against main's hook: **6 failed, 2
passed** (the two "nothing invented" guards: the completion control sends the completion alone; a guide for another
reading observes nothing):

- `a restore observes nothing; the learner's own reading observes the passage under the marker, never the prefix before it` (count 4, passages `["s3"]`)
- `a jump observes nothing, not even the passage the reading left; reading on after it observes again`
- `reaching a section's last passage by reading is its end, sent with that passage; the count's leave-after-60% rule is neither`
- `a passage is sent until acknowledged (a failed save sends it again), and never after`
- `passages the backend refuses as not the section's are dropped, so the counts beside them still save`
- `observedPassages: …` (the page-only rule, unit)

Phone: `src/read/seenPassages.test.tsx` (new; the real App on the fake host with a driven `IntersectionObserver`) and
one case in `src/store/outbox.test.ts`. Against main's Reader and outbox: **3 failed** (all three):

- `opening a section observes nothing until the learner scrolls; then what is on screen is read, its end included`
- `a scroll the learner did not make, opening the next section and finishing one observe nothing; a held-out passage is never read`
- `queued reports of a section union the passages they observed and keep an end and a completion, not the larger count's alone`

No existing assertion changed except the 17 migration diffs above. No identity pin, golden or snapshot moved.

## What was run

Every Python and CLI run through the scratch wrapper (empty home, config and Codex dirs), every pytest run `-n 1` in a
3 GB memory scope, one at a time; the frontend suites with two workers.

| Command | Result |
|---|---|
| `tests/test_reader_seen_passages.py`, `tests/test_reader_seen_spans_migration.py` | 19 passed |
| The 137 test files whose names contain migration, table_roles, reader_progress, reading_progress, section_progress, mobile_outbox, mobile_allowlist, sidecar_reader or tracked_fixture, or that name `mark_section_progress`, `reader_section_progress`, `upsert_reader_section_progress`, `seen_passages`, `reader_seen_spans`, `protected_tables`, `column_classes` or `table_roles` (the name filter over `scripts/affected_tests.py`'s 1,334 files), four chunks of 32-35, `-m "not arc_close"` | 488 passed; 775 passed; 545 passed, 3 skipped; 8,662 passed |
| `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`, `test_public_tip_guards` and the two new files | 419 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `tests/test_architecture.py` alone | 18 passed |
| `ruff check` | All checks passed |
| `lint-imports --no-cache` | 44 kept, 0 broken |
| `scripts/check_gate_partition.py` | collected 32074: landing 32009 + arc_close 65 |
| Desktop `npm run typecheck`; `vitest run` (whole suite); `npm run frontend:build` | clean; 320 files, 3,352 tests passed; built |
| Phone `npm run typecheck`; `vitest run` (whole suite); `npm run build` | clean; 43 files, 435 tests passed; built |
| `db_generate_reference.py`; `db_validate_reference.py` | `schema_head` 256, 399 table notes; `"errors": []`. Their output (two new table notes, the catalog, `reader_section_progress`'s note, `_generated.md`) was restored, not committed: the landing regenerates |

No identity pin, golden or snapshot moved; no structure ratchet number rose.

## What a walk must check

With the patient first-day persona and a learner who stops at 60 % (the design's §7, row 2), on the real desktop window
(WebKitGTK) and the phone:

1. Scrolling a text section saves passages: after a few screens, `reader_seen_spans` holds the passages that passed the
   reading marker, origin `desktop`; reopening the book (a restore) and a Contents jump add none until the learner
   scrolls again.
2. Close and reopen, and switch devices: the passages survive; the phone adds `phone` rows only for what it showed
   after the learner's own scroll; no invented prefix or suffix (a resume at the middle of a section adds that passage,
   not those before it).
3. **The end of a long section on the text view**: scrolling into the next section records the end (`reader_section_ends`).
   **The end of the book's last section, and of a short section that fits the window**: the reading marker sits 70 %
   down the view, so a last passage that cannot scroll up to it is never under it; neither the count nor the end is
   reached there today. Step 5 needs that answered (the design's §8 "final-passage detection" test).
4. A page-only PDF (no block boxes): passages are recorded as the marker passes 85 % of each one's share of its page.
   Check a page with several passages, a scrollbar drag and the End key.
5. A video: playback advancing records the transcript cues it passes; a seek records nothing.
6. The phone: on a real phone the frame's scroll and the viewport observer behave as the fakes do (touch then scroll;
   momentum after the finger lifts keeps counting, since the movement holds for the visit); a held-out passage is never
   recorded; a section ending in one never records an end.
7. Nothing else changes: "Done with this section", Today, the quick checks and question writing behave exactly as on
   main.

## What was not verified

- No browser, desktop window or phone was run (the rules). The geometry (which passage is under the marker, what the
  viewport observer reports on iOS Safari, momentum scrolling, the frame's scroll events) is tested on fakes only.
- **The phone's existing count** (found by reading, filed as UX-59): its `IntersectionObserver` is rooted at the
  section's `.book` box, which does not scroll (the app's `.frame` does). By the IntersectionObserver specification, a
  target is clipped only by containers between it and the root and then by the root's own box, so every laid-out
  passage of the section intersects: the count reaches the section's size about 1.5 s after a section opens, whatever
  was on screen. Not observed in a browser. Left as it is here: changing it changes what the count, Contents and
  Today's reading step say (this step's bounds); the new passages use their own observer with no root.
- The end at the bottom of the book's last section and of a short section (walk item 3).
- Performance: a report with passages loads the reading's IR once to check them (`load_document_ir`), as the guide plan
  does; reports are debounced (1.5 s) and carry only unacknowledged passages. Not measured on a large book.

# Re-read safety: reading a studied book again keeps what the learner has

**Branch:** `fix/reread-safety` (worktree `learnanything-ux-impl`, base main `bffe086ec` = mvp-0.23, not rebased; the orchestrator merges). Owner-directed 2026-10-14. The GLM-OCR live check on backup copies of the owner's books found that the Library card's "Read it again with text recognition" breaks a studied book today, whatever the engine (findings: the live check's "Downstream" section, E1 and E2, and its "Code changes needed" items 1-7). The live GLM-OCR run the same day (39 requests, $0.0923) confirmed E2 with GLM-OCR itself: progress, Guide passages, highlights and the unit selection were lost, and 7/7 and 13/13 citations landed on other passages. It added one detail for E1: the originals store's files have no extension, so `resolve_source` refuses a store path; a re-read has to be handed the stored **bytes**.

| Item | What | Where |
|---|---|---|
| 1 (E1, High) | A re-read, and any import naming an existing book, reads the current revision's own bytes (originals store first, then the recorded files), hash-checked, never re-classifying the book's path; refuses plainly otherwise; a revision becomes current only once it has a completed reading; one-tap repair for a library already in the E1 state | `content/pipeline/reread.py`, `jobs.handle_import`, `source_library.register_source_revision`, `source_outline.resolve_extraction_id`, card line + `source_action restore_reading` |
| 2 | The re-read keeps the previous reading's pages and carries the unit selection, exam use modes included | `source_action text_recognition`, `reread.carry_selection` |
| 3 | One alias authority (`content/sources/span_aliases.py`: `reanchor_spans` persisted in `source_span_reanchors`) that every reader of old span ids goes through: progress, Guide, LO highlights, links, citations, annotations, the saved reading place, source conflicts, margin cues | `span_aliases`, `reread.carry_over`, reader, retrieval and conflict readers, `reader.saved_place`, desktop |
| 4 | Doctor: an error for the E1 state (fixed by `--fix-state`), warnings for changed citations and for links pinned to a reading that is no longer current | `ops/doctor._check_reread_state` |
| 5 | The card's z.ai OK line and the re-read's confirmation name the pages and the estimated cost (`glm_ocr.estimate`) | `jobs.glm_upload_estimate`, `add_source._import_failure_line`, `reread.reread_plan` |
| 6 | Normaliser/estimate from live answers | Not here: it waits for the live GLM-OCR results (owner's stage list) |
| 7 (optional) | Smaller GLM-OCR window uploads | Measured, not done: 2% (below) |

**No algorithm successor** (`docs/algorithm-change-playbook.md`). Nothing scored, scheduled, projected or graded changes, and replay reads none of what changed. The tables written are `source_span_reanchors`, `source_annotation_anchor_versions`/`_segments`, `source_artifacts.current_revision_id` and `source_object_citations.block_content_hash` (RAW_LEDGER), and `reader_section_progress` and `source_unit_selections` (WORKFLOW). No DERIVED table and no replayer is touched. `rebuild --shadow` on the copies gave a byte-identical `learner_state_diff` before and after a re-read; only the `source_block_fts` replayer grows, by the new reading's blocks: 972 → 998 rows (linear algebra) and 510 → 558 (probability). **Migration:** none; **schema:** unchanged (head 202). **Config:** unchanged. **CLI help:** unchanged (doctor gains checks, no option). **RPCs:** `reader.saved_place` is new; `source_action`, `get_source_library`, `reader.render_view`, `reader.guide_plan` and `list_source_conflicts` are extended. All are desktop only and pinned in `tests/test_mobile_allowlist.py`.

**Paid calls: none ($0.00).** The tests use fakes: the fake extractor `Readings`, and GLM-OCR through a fake transport that fails the test on any real request. The scenarios below ran with every key blanked and the machine settings not loaded (`LEARNLOOP_CONFIG_DIR` pointed at an empty scratch directory). Every socket connection was refused, and the card's text recognition was rewritten to the local pypdf reader at enqueue time. All copies show zero `model_call_receipts` from today.

## Item 1: E1, the bytes a re-read reads

**Before.** `source_action text_recognition` enqueued an import of the book's `canonical_uri`. On the owner's machine that path is a 132-byte git-LFS pointer. The import:
- registered the pointer as a new revision and stored it;
- made that revision current before extracting it;
- then failed to extract it.

The book then resolved to no reading: `reader.render_view` and the outline said `extraction_not_found`, and the card showed nothing. Pointing the copies' books at their stored originals didn't help either: a store file has no extension, so `resolve_source` refused it (`UnsupportedSourceError`, live run).

**Fix.**
- **The bytes.** `handle_import` reads an import that names an existing book (`source_id`: the card's re-read, a retry, an Add of a book already here) like this:
  - It keeps the book's own `acquisition_kind` and `canonical_uri`, and never classifies its path again.
  - It is handed the book's current revision as bytes. `reread.revision_bytes` tries, in order: the originals store (`stored_original_path(asset_hash)`), the revision's `original_uri`, the book's `canonical_uri` when it is a local file, then a link. The first candidate whose `asset_hash` is the revision's wins.
  - Nothing else is read, so nothing is registered: re-reading reuses the revision.
  - A retried import that registered a revision itself (its job payload now records the `revision_id`) reads that revision's own bytes.
  - `handle_extraction_repair` reads the same way.
  - When no bytes match, the import refuses with `original_changed`: "The file this book came from has changed or is missing, so it can't be read again. The reading you have stays as it is."
  - The card checks this before enqueueing anything, and its line reads "Couldn't read it again: its original file changed or is missing".
- **The current revision.** `register_source_revision` no longer moves `current_revision_id` for a book that has a completed reading. The import adopts the new revision once that revision's own reading completes (`reread.adopt_revision`), so a failed import leaves the previous revision current.
- **The repair.** A library already in the E1 state has a current revision with no completed reading while an older revision has one. For such a library:
  - `resolve_extraction_id` and the Library card fall back to the newest readable revision, so the book opens again.
  - The card says "This book's file changed after it was read" with one action, "Open the reading you had" (`source_action restore_reading`). That action makes the readable revision current again and deletes nothing.
  - `learnloop doctor --fix-state` does the same.

**Tests** (`tests/test_reread_safety.py`, all written to fail first):
- `test_e1_the_reread_reads_the_stored_original_and_reuses_the_revision`, run twice: once with the book's file replaced by an LFS pointer and once with it deleted. The re-read reads the stored bytes, reuses the revision and completes. The book resolves to a reading throughout, and nothing is stored under the pointer's hash.
- `test_e1_the_reread_hands_the_import_the_stored_bytes_never_a_store_path`: the live run's finding. The book's recorded path is the extensionless store file itself, and the PDF is gone. Before the fix the import failed with `UnsupportedSourceError`; now it completes from the stored bytes and registers nothing. The test PDFs carry a NUL in their header's binary comment, as a real book's compressed streams do near the start, so a store copy can't be classified.
- `test_e1_bytes_that_match_nowhere_refuse_plainly_and_register_nothing`.
- `test_e1_a_failed_import_of_new_bytes_leaves_the_previous_revision_current`.
- `test_a_retried_import_reads_the_revision_it_registered_not_the_current_one`.
- `test_e1_one_tap_repair_for_a_library_already_in_that_state`.

## Item 2: the page scope and the selection

**Before.** The card passed no page selection. Re-reading Axler (read on 26 pages) would have read, and with GLM-OCR billed, all 404 pages. The new reading had no unit selection, so it also lost any `exam_use_modes` (held-out exam material).

**Fix.**
- The re-read sends the previous top-level reading's `page_selection`.
- `reread.carry_selection` moves the selection to the new reading through the unit map:
  - Selected units and boundary overrides go to the units they map to.
  - Where two old units land in one new unit, the more protective exam mode wins.
  - A unit that doesn't map is listed in `needs_review`.
- Held-out material can't be released along the way. `exam_material` reads every held-out mark on every reading of the source, by label, and withholds the whole reading when a label doesn't resolve (fail closed).

The unit map (`reread.unit_map`) tries these in order:
1. the same unit id with the same label;
2. `reanchor_units`;
3. a unique label;
4. the new unit holding more than half of the old unit's spans through the aliases;
5. **new in this round:** the new unit holding more than half of the old unit's blocks by page.

Step 5 is for a coarser reading. On the Axler copy, Marker's 60 fine units against the PDF outline's 13 had left 4 of the 11 read sections unmatched.

**Tests:**
- `test_the_reread_keeps_the_page_scope_and_carries_the_selection`: through the card, 26 of 40 pages, the selection with a held-out unit.
- `test_a_glm_reread_of_a_sliced_book_sends_only_its_pages`: the real GLM-OCR extractor on a fake transport uploads 26 pages, not 40.
- `test_section_progress_and_the_unit_selection_carry_to_the_new_reading`.
- `test_held_out_material_stays_withheld_on_the_new_reading`.
- `test_unit_map_falls_back_to_the_pages_a_coarser_reading_puts_them_on`.
- `test_progress_on_a_coarser_reading_is_read_through_only_where_every_part_was`.

## Item 3: one alias authority

`content/sources/span_aliases.py` is the only place old span ids are read.

**How a reference resolves.** A same-revision re-read records `reanchor_spans(old, new)` in `source_span_reanchors` when it completes (`record_aliases`, idempotent). Each kind of alias resolves this way:

| Alias | Means | Status | Shown |
|---|---|---|---|
| `exact_hash` or a learner's manual alias | the same text | `current` | resolves there |
| a geometry or section alias | the same place, other text | `needs_reanchor` | flagged |
| none | nothing matches | `stale` | no span; never "the current reading + the old span id" |

A pair of readings with nothing recorded (a re-read made by an older build) is computed in memory, in a bounded memo, and never written from a read path.

**Where it is used:**

| Reader of old span ids | Now |
|---|---|
| Section progress | carried by the unit map (`carry_progress`). A new section is read through only when every old section landing in it was. Otherwise its share of spans seen is carried, rounded down |
| Guide passages (`reader_guidance`) | the YAML refs of items and LOs resolve through a `SpanTranslator`. A moved passage shows flagged ("reworded since you read it") with the words that were cited |
| LO highlights (`learning_objects_for_section` / `_for_span`, and `suggest`, which reads it) | refs from the earlier reading count for their place |
| Grounding refs (`source_refs_for_section`) | exact aliases only |
| Retrieval (`find_sources` provenance, facet and correction lists) | `CurrentKeys`: a link moves to the current reading only through an exact alias, and otherwise stays on the reading whose text it names |
| Source-object citations (`find_sources.source_object_lists`, `corpus.role_proposal_keys`) | `CitationResolver`: each citation resolves against the reading it was made on, by its `block_content_hash` when recorded, else by the reading completed when it was made. New citations now record `block_content_hash` (`reader_requests._land_proposals`) |
| Annotations | re-anchored automatically on completion (`carry_annotations`, one block pass per reading). A `needs_reanchor` anchor shows the Reader's "anchor needs review" |
| Saved reading place (desktop `localStorage`) | stored as `{extractionId, spanId}`. A place saved on another reading, or a bare legacy span id once the book was read again, is translated by `reader.saved_place`. "This book was read again: you're near where you left off." when approximate; the reading history resumes when stale |
| **Source conflicts** (`list_source_conflicts`, Maintenance "open in source") | **new in this round:** the screen opened the revision's latest reading with the locator's span id. Each side now resolves through `span_aliases.locator_key`, and the screen opens the span the sidecar names |
| **Margin cues** (RW3a, `reader_cues`) | **new in this round:** only a passage whose cited words are there gets a margin mark. A flagged passage stays in the rail, flagged |
| Exam material (`exam_material`) | held-out marks are read on every reading, by label, failing closed. **Not safe as first claimed** (Codex review F1, F2; fixed in `reread-safety-codex-review.md`): a source-set exam scope's reused unit id and a held-out inventory signal's old span id resolved on the latest reading |

Until all this was in, the card asked before re-reading. It still does for any book with study state: a confirmation names the pages, the cost and what moves to the new reading, with "Read it again" and "Not now". It also asks when z.ai would read the book with its OK already given, since then no OK line would show the cost.

**Tests:**
- `test_every_reference_lands_on_the_same_text_or_is_flagged_never_another_block`.
- `test_the_guide_and_lo_highlights_survive_with_moved_passages_flagged`.
- `test_citations_resolve_against_the_reading_they_were_made_on`.
- `test_a_new_citation_records_its_blocks_content_hash`.
- `test_annotations_reanchor_automatically`.
- `test_the_saved_reading_place_translates_through_the_aliases`.
- `test_references_still_resolve_for_a_reread_made_before_the_aliases_were_recorded`.
- `test_source_conflicts_open_the_span_they_cite_never_another_block`.
- `test_a_margin_cue_marks_only_a_passage_whose_cited_words_are_there`.
- `test_unit_map_keeps_outline_unit_ids_that_name_the_same_sections`.
- Desktop: `LibraryPlace.reread.test.tsx` (3 tests: the confirmation, "Not now", the one-tap repair) and `ReaderScreen.guide.test.tsx` (4 tests: the flagged passage, and the saved place translated, used as is, and legacy).

## Item 4: doctor

`_check_reread_state` adds three checks:
- **`source:current_revision_unread`**, an error: the E1 state, with its fix (`--fix-state`, or the card's "Open the reading you had"). `--fix-state` repairs it.
- **`source:citation_text_changed`**, a warning: source-object citations whose text on the current reading differs from the reading they cite.
- **`source:links_on_old_reading`**, a warning: `entity_source_links` and YAML source refs pinned to a reading that is no longer current that don't match the same text on it.

Both warnings read through `span_aliases`.

**Tests:**
- `test_doctor_is_quiet_on_a_book_read_once`.
- `test_doctor_warns_for_changed_citations_and_links_on_an_old_reading`.
- `test_doctor_reports_the_e1_state_with_its_fix`.

## Item 5: pages and cost where the re-read is asked

- **The z.ai OK line.** The card's line now reads, for example, "Reading this document (404 pages, about $0.07) sends the whole file to z.ai (GLM-OCR)". The `needs_upload_ok` error carries `pages`, `estimated_usd` and `page_selection`, computed by `glm_ocr.estimate` over the pages the import asks for.
- **The re-read confirmation.** It names the same estimate: "z.ai (GLM-OCR) reads it: less than $0.01." for 26 pages, or "Read on this computer: free."

**Tests:**
- `test_the_z_ai_ok_line_names_pages_and_cost_for_a_404_page_book`.
- `test_the_reread_confirmation_shows_pages_and_cost_when_z_ai_reads_it`.
- Three `test_glm_ocr.py` assertions updated to the new line.

## Item 7 (optional): window upload size, measured

On the probability copy's Blitzstein original (7.19 MB, 630 pages, 21 windows of 30 pages), with pypdf 6.14.2:

| Windows | Total | Largest window |
|---|---|---|
| as now | 37.6 MB | 3.6 MB |
| with `compress_identical_objects(remove_identicals, remove_orphans)` | 36.9 MB | 3.5 MB |

The saving is 2%. The duplication is across windows (each window carries the shared fonts), not within one, so deduplicating a window doesn't remove it. Not done. The upload stays within the 50 MB limit and costs nothing extra.

## E1 and E2 again, on fresh backup-API copies (free, offline)

**The copies.** I made `learnloop.db.copies.copy_tree_with_databases` copies of the owner's working vaults (`learnanything/fixtures/{linear_algebra,probability}` in the main checkout), opened at the source only for the backup. They are under the worktree's gitignored `fixtures-local/reread-safety/copies/`:
- `before_e1/` and `before_e2/` ran the base code (`git archive bffe086ec src migrations`, first on `PYTHONPATH`);
- `after/` ran this branch.

Each copy was migrated 165 → 202 and loaded once by the sidecar.

**The runs** (`fixtures-local/reread-safety/scripts/scenario.py`):
- **E1:** the card's own path, with the book's recorded path as it is: an LFS pointer.
- **E2 before the fix:** the same path with the recorded path pointed at a `.pdf` copy of the stored original, as the earlier check did.
- **After the fix:** one run with the recorded path as it is: E1, then E2 on the result.

The engine is pypdf (one block per page), the free stand-in the earlier check used. GLM-OCR would match far more text exactly. The live run found `reanchor_spans` resolving 40% (Axler) to 67% (Blitzstein) of referenced spans with GLM-OCR.

**Untouched.** The main checkout's `git status fixtures/` is identical before and after. The only change in the source directories is the mtime of the gitignored `-shm` index (`fixtures-local/reread-safety/notes/`).

### E1: the recorded file is a git-LFS pointer (all four PDFs)

| | Before (base) | After (fix) |
|---|---|---|
| The card's import | failed (`PyPdfExtractionError`, reading the 132-byte pointer) | completed, from the originals store (hash-checked) |
| A revision registered from the pointer | yes: 2 revisions, the pointer stored | no: 1 revision |
| Current revision | moved to the unread pointer revision | unchanged |
| The book opens from the Library | no: `extraction_not_found` | yes |
| Card line | none | none; a book with study state first asks (below) |

### E2: what the learner has, after a completed re-read

| | Axler before | Axler after | Blitzstein before | Blitzstein after |
|---|---|---|---|---|
| Asked first | no | yes: "Pages 15–40 (26 pages), as before. / Read on this computer: free. / Your progress (11 sections), 4 notes, the passages your questions and notes cite and your study-map chapters move to the new reading. Anything that can't be matched is marked so you can place it again." | no | yes: "Pages 12–54 (43 pages), as before. …" (8 sections, 12 notes) |
| Pages read | whole book (404) | 26, as before | whole book (617 pages with text) | 43, as before |
| Section progress on the reading the Reader opens | 11 read through → 0 | 6 sections carry progress, 1 read through (the outline's 13 sections are coarser than Marker's 60; a section is read through only where every part was) | 8 → 0 | 8 of 8 read through |
| Guide passages | 20 → 0, not personalized | 6, all flagged "reworded since you read it", personalized | 22 → 0 | 16, all flagged, personalized |
| LOs highlighted in the Reader's sections | 19 → 0 | 18 | 17 → 0 | 16 |
| LO, facet and item links (166 / 194) | stay on the old reading; none on the new one | through the aliases: 79 `needs_reanchor` (flagged), 87 `stale` (not shown); none silently elsewhere | stay on the old reading | 140 `needs_reanchor`, 54 `stale` |
| Source-object citations (7 / 13) | **7 of 7 resolve to a different block** (s179, "(−1+√3i)/2", now §5D "Diagonalizable Operators") | **0 misplaced**: 7 kept on the reading they cite, flagged by doctor | **13 of 13 different** (s57, "Definition 1.3.1 (Naive definition…)", now conditional probability) | **0 misplaced**: 13 kept on their reading |
| Saved reading place (the first passage of each read section: 11 / 8) | 11 of 11 on a different block | 11 of 11 "near where you left off" (said so) | 8 of 8 different | 8 of 8 near, said so |
| Annotations (4 / 12) | stay on the old reading, re-anchored by hand | re-anchored automatically onto the new reading, all `needs_reanchor` ("anchor needs review") | stay on the old reading | 12 re-anchored, `needs_reanchor` |
| Unit selection | 59 units → none | 11 of the new reading's 13 units; 3 old units flagged `needs_review` | 10 → none | 10 |
| Aliases recorded | 0 | 252 | 0 | 295 |
| Doctor (new issues) | none (blind) | `source:citation_text_changed` 1, `source:links_on_old_reading` 1 | none | 1 and 2 (Blitzstein and pset1) |
| `rebuild --shadow` | (base, the earlier check) identical | `learner_state_diff` identical before and after the re-read | identical | identical |

The two problem sets (pset1, recitation1):
- **Before:** E1 the same; after E2, their selections were lost (2 → 0, 1 → 0) and their saved places pointed at other or missing blocks.
- **After:** selections 2 → 1 (the new reading has one unit) and 1 → 1; places are said approximate; pset1's 4 links are 1 `needs_reanchor` and 3 `stale`.

None of these books holds held-out exam material (`exam_use_modes` `{}`), so the tests cover that case.

## Residual and open questions

1. **Old blocks in library search.** Both readings' blocks stay in `source_block_fts`, but library search's scope (`corpus.library_scope`) is the books' current readings only, so it never hits an old reading (Codex review: the premise did not hold). What remained was a hit found before a re-read completed and opened after it; it now carries its reading (Codex review F8).
2. **Exam-unit scopes on source sets.** Corrected by Codex review F1: a reused unit id resolved (to another unit) instead of failing, so the exam material was released. Every completed reading of the pinned revision is now a possible origin of the scope and each interpretation is withheld (`reread-safety-codex-review.md`). Over-protective until the scope records its reading.
3. **Links aren't given successor rows.** They resolve through the alias table (the report's alternative to successor rows) and are left pinned, YAML locators included. Doctor's `links_on_old_reading` counts what still needs placing. Still open (Codex review confirmed): no action places them again; annotations have their re-anchor action, the Guide shows moved passages flagged, and stale links simply don't show.
4. **Desktop reference.** `docs/learnloop-architecture-vault/_scripts/desktop_validate.py` fails on main too: `apps/learnloop-tauri/src/copy/denyList.ts`, from UX Phase 1, is unclassified. Not touched here.

## Gate

Run on the final code tree, `fbcfb38fe`. Only this record was committed after it. `TMPDIR` was the worktree's `fixtures-local/tmp`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 17 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10,997 passed**, 0 failed (14 min 30 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **100 passed**, 10,897 deselected |
| `apps/learnloop-tauri`: `npm install`, `npm run typecheck` | ok, no errors |
| `npm test` (vitest) | **582 passed** in 82 files |
| `npm run frontend:build` | built |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` (`reader_saved_place` passthrough) | ok |
| `db_generate_reference.py` / `db_validate_reference.py` | regenerated (`f49fc55d8`, `fbcfb38fe`: provenance and moved source lines; schema head 202, 321 table notes, 837 configuration leaves); validation passes |
| `module_validate.py` | passes |

Two earlier runs failed:
- **The first full suite** (`376c6835a`) had 1 failure, with 10,996 passed: `test_architecture.py::test_function_local_domain_imports_match_the_frozen_edge_inventory` found six new function-local cross-domain imports. The inventory is closed to new entries, so the imports became module-level imports instead (`59093b2b1`); none has a cycle, each module imports on its own, and lint-imports still holds.
- **One vitest run** had a timing failure in `FeedbackScreen.test.tsx`, under load from parallel suites. It passed alone and in the full rerun.

**Tests added:** 29 in `tests/test_reread_safety.py`. 3 assertions changed in `tests/test_glm_ocr.py`. RPC pins added in `tests/test_mobile_allowlist.py`. On the desktop, 3 in `LibraryPlace.reread.test.tsx` and 4 in `ReaderScreen.guide.test.tsx`, plus test doubles updated in `ReaderScreen.preparing` and `ReaderScreen.review`.

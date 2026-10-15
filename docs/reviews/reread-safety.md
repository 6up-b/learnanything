# Re-read safety: reading a studied book again keeps what the learner has

**Branch:** `fix/reread-safety` (worktree `learnanything-ux-impl`, base main `bffe086ec` = mvp-0.23, not rebased; the orchestrator merges). Owner-directed 2026-10-14. The GLM-OCR live check on backup copies of the owner's books found that the Library card's "Read it again with text recognition" breaks a studied book today, whatever the engine (findings: the live check's "Downstream" section, E1 and E2, and its "Code changes needed" items 1-7). The live GLM-OCR run the same day (39 requests, $0.0923) confirmed E2 with GLM-OCR itself: progress, Guide passages, highlights and the unit selection were lost, and 7/7 and 13/13 citations landed on other passages. It added one detail for E1: the originals store's files have no extension, so `resolve_source` refuses a store path; a re-read has to be handed the stored **bytes**.

| Item | What | Where |
|---|---|---|
| 1 (E1, High) | A re-read, and any import naming an existing book, reads the current revision's own bytes (originals store first, then the recorded files), hash-checked, never re-classifying the book's path; refuses plainly otherwise; a revision becomes current only once it has a completed reading; one-tap repair for a library already in the E1 state | `content/pipeline/reread.py`, `jobs.handle_import`, `source_library.register_source_revision`, `source_outline.resolve_extraction_id`, card line + `source_action restore_reading` |
| 2 | The re-read keeps the previous reading's pages and carries the unit selection (since the protection redesign, never its exam use modes) | `source_action text_recognition`, `reread.carry_selection` |
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
  - Exam use modes are not carried (protection redesign, `reread-safety-codex-review.md`): the owner marks each reading.
  - A unit that doesn't map is listed in `needs_review`.
- Held-out material can't be released along the way. As first built, `exam_material` read every held-out mark on every reading of the source, by label. Since the protection redesign (`reread-safety-codex-review.md`), no protection carries to another reading: a reading of a book with exam or held-out material marked elsewhere is withheld whole until the owner marks it ("Mark exam material on this reading" on its card).

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
| Exam material (`exam_material`) | held-out marks are read on every reading, by label, failing closed. **Not safe as first claimed** (Codex review F1, F2, then the re-review and the final verify; `reread-safety-codex-review.md`). Since the protection redesign the aliases carry no protection at all: a reading with none marked on it is withheld whole until the owner marks it |

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
2. **Exam-unit scopes on source sets.** Corrected by Codex review F1: a reused unit id resolved (to another unit) instead of failing, so the exam material was released. Since the protection redesign a scope names the first completed reading of its pinned revision, and every other reading of the book is withheld whole until the owner marks it (`reread-safety-codex-review.md`). Recording the scope's reading in `source_sets.yaml` remains open.
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

## Landing onto main

**Branch:** `merge/reread-safety-onto-main` (worktree `learnanything-merge2`), from main `fdfcf1934` (`mvp-0.25` LATEST; migration head 203, head fixture `fixtures/migration_head_203`, seventeen defaults snapshots `mvp-0.9`..`mvp-0.25`). Not pushed. Owner-directed, 2026-10-15, single phase. The sections above, `reread-safety-codex-review.md`, `exam-protection-identity.md` and its Codex review describe the branch as built and keep its placeholder (migration 225).

**Commits:**
- `1ef2f14eb`: a real `--no-ff` merge of `fix/reread-safety` (`ca114c1e2`, unchanged, 39 commits from `bffe086ec`), with the conflict resolution, the renumber and the coordinated-migration conversions the merged tree needs to run.
- `c4dee14ae`: the compositions, with their landing tests.
- `61728b042`: the regenerated references and the Pipeline Map.
- This record.

**Main since `bffe086ec`, composed:**
- Router R2b + R2c (`mvp-0.24`), plan determinism, and method-explicit items (`mvp-0.25`: `presented_prompt`, `answered_prompt`, `fit_presented_prompt`, the Decider task).
- GLM-OCR quality (3,500 tokens a page, `MAP_VERSION` 2, the text layer read in a pdfium worker) and the Marker pdfium worker (`marker_worker.py`; the Reader renders under a lock).
- The chat frontend's C1a (`learnloop_mcp`, attach-only `learnloop.remote`, `learner_protection.py`, migration 203, 22 import-linter contracts).
- The storage spec, the adaptive-difficulty spec and its revision.

No algorithm successor: the branch has none, and the landing changes no scoring, scheduling, projection or config value.

### Conflicts

469 files:
- **373 generated reference notes** (322 under `Reference/Database`, 51 under `Reference/Configuration`): main's side, then regenerated.
- **72 head-fixture files**, a rename/rename (the base's `migration_head_202` became main's `migration_head_203` and the branch's `migration_head_225`): main's `migration_head_203` kept, the branch's `migration_head_225` dropped, then renamed and rebuilt (below).
- **24 other files** (21 test files, both `_scripts/db_*_reference.py`, `docs/decider-tier1-migration.md`): every hunk was the head number, 203 against 225. Each was resolved to 204.

### The renumber: migration 225 → 204

- **Migration.** `migrations/225_source_held_out_signal_marks.sql` became `migrations/204_source_held_out_signal_marks.sql`. Its header names both numbers (built as 225, a placeholder, renumbered 204 after main's 203). Only the comment above the `CREATE TABLE` changed, so no stored DDL moves. `source_held_out_signal_marks` stays `RAW_LEDGER` in `table_roles.py`, so it needs no replayer.
- **Every mention of 225 now says 204:** `migration_coordinator.py`, `db/stores/held_out_signals.py`, `exam_material.py`, `vault/writer.py`, `table_roles.py`, `tests/test_coordinated_migrations.py`, `tests/test_exam_protection_identity.py` (its `[225]` assertions and `DELETE ... version = 225` setups), `Architecture/State and Persistence.md` and the generator's table description. Two comments in the identity tests describe `bbe340ce9`, where the number was 225, and say so ("225 (now 204)").
- **Head fixture.** `git mv fixtures/migration_head_203 fixtures/migration_head_204`. Its `state.sqlite` was rebuilt:
  - a backup-API copy (`learnloop.db.copies.backup_database`) of main's 203 database;
  - only 204 applied through `apply_migrations`;
  - `wal_checkpoint(TRUNCATE)` → `(0, 0, 0)`, then `journal_mode=DELETE` (header bytes 18-19 are 1/1);
  - `integrity_check` ok, `foreign_key_check` empty;
  - copied back with the backup API, with no companion files.

  Its `sqlite_master` equals the branch's head-225 fixture's except `interaction_events` (main's 203 CHECK widening). The new ledger has 0 rows (no inventories to backfill). The README gains the 204 paragraph and the build chain.
- **Hard-coded head paths.** 24 test files name `migration_head_204`: the 21 conflicted ones, plus main's `test_mvp024_upgrade.py`, `test_plan_determinism.py` and `test_method_explicit_upgrade.py`. Also: both reference scripts (`SCHEMA_PATH`, `SCHEMA_HEAD = 204`, the generator's other mention), the max-migration assertion (`test_route_rules_in_grader.py`: 204) and `docs/decider-tier1-migration.md`. (The merge commit's message says "27 test files". It means these 27 files.)

### Coordinated migrations on main's code

`tests/test_coordinated_migrations.py` failed on the merged tree at first. It found main's three `Repository(path)` sites, exactly the ones `exam-protection-identity.md` predicted:
- `router_mixture_upgrade.py` (the `mvp-0.24` step) and `method_explicit_upgrade.py` (`mvp-0.25`) now use `open_vault_repository(vault.root, sqlite_path)`, as the branch did for the `mvp-0.22`/`0.23` steps.
- `content/proposals/method_phrasing.py` (`run_method_phrasing`, below the CLI's entry) now uses `vault_repository(VaultPaths(...))`.

Neither MCP C1a nor the Marker worker constructs a `Repository` or calls `apply_migrations`. After the conversions, the guard passes (6 tests).

**Attach-only, confirmed:**
- `learnloop.remote.runtime.RemoteRuntime.attach` checks that the applied migrations equal this code's (`check_schema`), then uses `Repository.attach`. The guard pins that only the coordinator (and the offline review's scratch copy) call `apply_migrations`.
- `learnloop mcp serve` exits 78 on `SchemaMismatch`. `tests/test_mcp_runtime.py::test_secondary_attach_refuses_a_schema_it_does_not_match` checks the 78 and that the vault's `schema_migrations` is unchanged. The mobile host does the same.
- One wording fix rode along. The mismatch hint said "run `learnloop doctor` once to migrate", but doctor migrates only with `--fix-state`, on main and here. The hint now names `learnloop doctor --fix-state` in `remote/runtime.py`, the `mcp serve` help (CLI help snapshot regenerated: only `mcp serve` moves), and the mobile host and its doctor.

### Compositions

1. **Protection reaches every model-visible path.** `learner_protection.withheld_items` reads `exam_material.exam_material` and `item_exam_status`. The chat's `find_sources` filters by `exam_material` (the service's `exam_withheld` pool filter, then `remote.sources._shown`'s last check). Rule 4's held-back readings are whole extractions in that material (`unmarked_reading`), so every path sees them with no code change. Landing test `test_an_unmarked_reading_of_a_protected_book_is_withheld_from_every_model_visible_path`:
   - the chat frontend's world gets a re-read of its book (`ext_book_r2`, now current) carrying a passage only it has, and an item made from that passage, answered and graded against a pinned contract;
   - control: before any mark, MCP `find_sources` returns the passage, and `learning_context` and router R2a's card show the answer with its question;
   - then a held-out mark is made exactly on the book's first reading. The re-read is held back (`reading_held_back`, verdict `unmarked_reading`). MCP `find_sources` returns nothing of it and counts it under `withheld.exam_material`. `learning_context` and the card both withhold the answer as "exam or held-out material", keeping its result.
2. **Prompt rendering.** `test_a_cue_on_a_reread_resolves_the_cited_passage_and_shows_the_question_with_its_method`:
   - an item cites `s1`-`s3` and `s5` on `ext1`, and its answer was graded under a contract that froze a required method;
   - the book is read again (`ext2`: the same text under other span ids), and `carry_over` records the aliases;
   - `SpanTranslator` resolves every cited span exactly, and the Guide of the re-read places each passage there (`current`), never the old span id;
   - the margin cue's "Open" shows the answered question with the method's sentence whole (`answered_question` → `fit_presented_prompt`).
3. **Cost tests.** GLM-OCR quality's estimate is 3,500 tokens a page:
   - `test_the_z_ai_ok_line_names_pages_and_cost_for_a_404_page_book` computes the line from `glm_ocr.ESTIMATED_TOKENS_PER_PAGE` (now "about $0.04");
   - `test_the_reread_confirmation_shows_pages_and_cost_when_z_ai_reads_it` reads the constant instead of 6000;
   - `glm_estimate_phrase`'s docstring says $0.04.
4. **The workers get the stored original's bytes.** In both tests, `canonical_uri` holds a git-LFS pointer and the re-read runs through the real `default_extract`:
   - `test_a_marker_reread_hands_the_worker_the_stored_originals_bytes` (Marker with `force_ocr`, `marker_worker.run_marker` captured): every byte string handed to the worker hashes to the revision's `asset_hash`, and no revision is registered;
   - `test_a_glm_reread_uploads_pages_of_the_stored_original_not_the_pointer` (GLM-OCR through a fake transport): the uploads are the reading's 26 pages, read from the store.

   No code change: `_extract_pdf_locally` hands `fetched.raw_bytes` to both readers, and on a re-read `fetched` is `original_bytes`.

**Also:**
- `tests/test_mobile_allowlist.py` pins `source_action`'s actions (`restore_reading`, `mark_exam_material` among them). `reader.saved_place` came pinned from the branch.
- No `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry moves: the branch changed only a comment in `config/schema.py`, and the template is untouched. The snapshot tests pass.

### Generated files

- **References.** `db_generate_reference.py`, then `db_validate_reference.py`: **0 errors**; schema head 204, 322 table notes, 857 effective configuration leaves. `Database.md`'s prose counts were corrected: 322 tables, 19 `DERIVED`, 303 others. `validate_vault.py` passes: 1,107 notes, all reachable from Home.
- **Pipeline Map.**
  - A re-read reads the stored original (hash-checked, never `canonical_uri`), and Marker's worker and GLM-OCR get those bytes.
  - The one alias authority and what routes through it.
  - Rule 4, marks bound to the reading they were made on, and the owner's marking. Protection is not behind `plan.reading_from_furthest`, and the chat and the card read it through `learner_protection`.
  - Only the coordinator upgrades a vault's database.
  - Its source paths and gaps list are updated to match.

### Gate

Run on the final code tree, `61728b042`; only this record was committed after it. `TMPDIR` was the worktree's `fixtures-local/tmp`. No paid calls ($0.00); every test uses fakes, and npm and cargo ran `--offline`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` (5.14.0); `uv run --no-sync` afterwards | ok |
| `uv run lint-imports --no-cache` | **22 kept**, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | **11,815 passed**, 0 failed (14 min 23 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability -n auto` | **105 passed** |
| `apps/learnloop-tauri`: `npm install` (up to date), `npm run typecheck` | ok, no errors |
| `npm test` (vitest) | **599 passed** in 84 files |
| `npm run frontend:build` | built |
| `cargo check --manifest-path src-tauri/Cargo.toml` (src-tauri changed: the branch's `reader_saved_place` passthrough) | ok |
| `db_generate_reference.py` / `db_validate_reference.py` / `validate_vault.py` | 0 errors / passes (above) |

**The first full suite**, on the merge commit `1ef2f14eb` alone, had 3 failures and 11,807 passed. Each was a composition this landing then made (`c4dee14ae`):
- the CLI help snapshot (`mcp serve`'s corrected hint);
- the two cost tests, still at 6,000 tokens a page.

No test failed on timing, so nothing needed a rerun alone.

**Tests:**
- 4 added in `tests/test_reread_safety_landing.py`, and 1 in `tests/test_mobile_allowlist.py` (`source_action`'s actions);
- 2 changed in `tests/test_reread_safety.py` (they read the estimate constant);
- 24 test files' head path and `test_route_rules_in_grader.py`'s max migration moved to 204;
- `tests/test_exam_protection_identity.py` and `tests/test_coordinated_migrations.py` renumbered to 204.

### Parity

**Setup:**
- **Copies.** Backup-API copies (`copy_tree_with_databases`) of this worktree's tracked `fixtures/linear_algebra` and `fixtures/probability`, under `fixtures-local/tmp/parity`.
- **Main's side.** Main `fdfcf1934`, exported with `git archive` (`src`, `migrations`) and put first on `PYTHONPATH` (the probe printed the export's `learnloop/__init__.py`). It applied 48 migrations, to 203.
- **The merge's side:** 49 migrations, to 204, each copy through `migrate_vault`.
- **Runs.** `learnloop rebuild --shadow --json` and `learnloop doctor --json` on each copy, with `LEARNLOOP_CONFIG_DIR` set to an empty directory.
- **Comparison.** Shadows were compared structurally, with ULIDs, timestamps, hashes and paths set aside. Doctor reports were compared positionally and as multisets, with the copy's directory name normalized.

| Fixture | Shadow (facet / mastery / schedule) | Shadow differences | Doctor main → merge |
|---|---|---:|---|
| linear algebra | 22 / 6 / 47 on both sides | **0** | 107 → 107 (1 error, 106 warnings); identical positionally and as multisets |
| probability | 2 / 1 / 1 on both sides | **0** | 138 → 138 (49 errors, 46 of them `criterion:unknown_dependency`); identical |

**Checks:**
- **New doctor checks.** Re-read safety adds five: `source:current_revision_unread` (error, fixed by `--fix-state`), `source:reread_carry_incomplete`, `source:reading_held_back`, `source:citation_text_changed` and `source:links_on_old_reading`. None fires on these copies before a re-read.
- **The copies are unchanged.** `live_database.unchanged` is true on every shadow. Each copy's `state.sqlite` hash (checkpointed) is the same before and after its shadow and doctor.
- **No protected sources, nothing held back.** On the merge's copies:
  - `source_marks` is empty (0 protected books);
  - exam material and the held-out partition are empty;
  - no current reading is held back (0 of 3, 0 of 4), and no selection has exam use modes.
- **The 204 backfill** wrote one ledger row in linear algebra: a held-out signal on a lecture video's inventory, role not recorded. That book is not exam material, so it protects nothing.
- **The 15 withheld items** in linear algebra are a goal's reserved exam pool (`reserved_exam_pool_item_ids`) on both sides, not source protection.
- **The tracked fixtures were only copied.** Their hashes (`a3972c00…`, `0ac51001…`) are the same before and after, and `git status fixtures/` is clean. `arxiv_v2` was not opened, and the main checkout was not touched.

### E1 and E2 on main and on the merge (free, offline)

**Setup:**
- The stage's `scenario.py`, unchanged except for the receipts date, ran on fresh backup-API copies of the same two fixtures:
  - `before_e1` (as is) and `before_e2` (repointed) ran main `fdfcf1934`, the code before the fix;
  - `after` ran the merge.
- Each copy was prepared by its own side's code (migrated, then loaded once by the sidecar).
- The tracked copies record their books at paths in the main checkout. So that nothing outside the copies was read, each copy's `canonical_uri` and `original_uri` were first pointed at a local git-LFS pointer file (`oid` and `size` of the revision), which is what the owner's checkout holds there.
- The engine is pypdf, rewritten at enqueue time. Every key was blanked and every socket refused. `model_call_receipts` from today: 0 on every copy.

The counts match the stage's run on the owner's working vaults, case by case.

**E1 (the recorded file is a git-LFS pointer; all four PDFs):**

| | Before (main) | After (the merge) |
|---|---|---|
| The card's import | failed (`PyPdfExtractionError`, "Stream has ended unexpectedly": it read the pointer) | completed, from the originals store (hash-checked) |
| A revision registered from the pointer | yes: 2 revisions, the pointer stored | no: 1 revision |
| Current revision | moved to the unread pointer revision | unchanged |
| The book opens from the Library | no: `extraction_not_found` | yes (`reader.render_view` by source; the two problem sets are reader-disabled) |

**E2 (what the learner has after a completed re-read).** Before the fix, the recorded path was repointed at a `.pdf` of the stored bytes:

| | Axler before | Axler after | Blitzstein before | Blitzstein after |
|---|---|---|---|---|
| Asked first | no | yes: "Pages 15–40 (26 pages), as before. / Read on this computer: free. / Your progress (11 sections), 4 notes, …" | no | yes: "Pages 12–54 (43 pages), as before. …" (8 sections, 12 notes) |
| Pages read | whole book (404) | 26, as before | whole book (617) | 43, as before |
| Section progress on the reading the Reader opens | 11 read through → 0 | 6 sections carry progress, 1 read through | 8 → 0 | 8 of 8 read through |
| Guide passages | 20 → 0, not personalized | 6, all flagged, personalized | 22 → 0 | 16, all flagged |
| LOs highlighted | 19 → 0 | 18 | 17 → 0 | 16 |
| LO, facet and item links (166 / 194) | stay on the old reading | 79 `needs_reanchor`, 87 `stale` | stay on the old reading | 140 `needs_reanchor`, 54 `stale` |
| Source-object citations (7 / 13) | **7 of 7 on a different block** (s179 "(−1+√3i)/2" → §5D) | **0 misplaced**: 7 kept on their reading, flagged | **13 of 13 different** (s57 "Definition 1.3.1" → conditional probability) | **0 misplaced** |
| Saved reading place (11 / 8 samples) | 11 of 11 on a different block | 11 of 11 near, said so | 8 of 8 different | 8 of 8 near, said so |
| Annotations (4 / 12) | stay on the old reading | re-anchored onto the new reading, `needs_reanchor` | stay | 12 re-anchored, `needs_reanchor` |
| Unit selection | 59 units → none | 11 of the new reading's units, 3 old units `needs_review` | 10 → none | 10 |
| Aliases recorded | 0 | 252 | 0 | 295 |
| Doctor (new issues) | none | `source:citation_text_changed` 1, `source:links_on_old_reading` 1 | none | 1 and 2 (Blitzstein, pset1) |

**The problem sets:**
- **Before:** E1 the same. After E2, their selections were lost (2 → 0, 1 → 0), and their saved places pointed at missing or other blocks (6 missing, 3 different).
- **After:** selections 2 → 1 and 1 → 1; places are said approximate (6, 3); pset1's 4 links are 1 `needs_reanchor` and 3 `stale`.

**Replay is unaffected.** `rebuild --shadow` was run on one more fresh copy of each fixture, prepared the same way, before and after its re-read:
- the `learner_state_diff` is byte-identical (linear algebra 2 / 7 / 48, probability 2 / 1 / 1);
- only the `source_block_fts` replayer grows, by the new reading's blocks: 972 → 998 and 510 → 558 rows, as the stage found;
- `live_database.unchanged` holds.

These counts differ from the parity copies' 22 / 6 / 47 because preparation also loads each copy once in the sidecar, before the re-read. The comparison that matters is the same copy before and after.

### Open questions for the owner (defaults as landed)

1. **No owner "un-protect a book" action yet.** A book is protected while any mark or signal names one of its readings. A signal made under an exam role stays in the append-only ledger after the book leaves every set. **Default:** fail closed. Every reading of a protected book that is not marked exactly is held back until "Mark exam material on this reading" is confirmed on it. No action removes a book's protection, and a recorded signal cannot be withdrawn. A "this book holds no exam material" action is the owner's to decide.
2. **Library search keeps finding, then withholding, exam hits.** `corpus.library_scope` excludes nothing (the sources merge's "found, then withheld" transparency). A held-back reading's hits are found, then every caller filters each hit, so nothing of it is shown. **Default:** as landed (pinned by `test_sources_merge_composition`).
3. **The marking suggestion is not editable.** "Mark exam material on this reading" holds out the whole suggestion: the units the book's marks would protect on this reading by their own unit ids, and legacy marks' units. The marking is bound to the reading and the proposal hash it showed. **Default:** confirm it as shown, or decline it.
4. **Search does not cover old readings.** Both readings' blocks stay in `source_block_fts`, but library search covers the books' current readings only. A hit found before a re-read and opened after it is translated onto the reading the Reader opened. **Default:** current readings only.
5. **No UI to re-place `needs_reanchor` links.** LO, facet and item links resolve through the aliases and are left pinned to their reading:
   - a `needs_reanchor` link shows flagged, and a `stale` one does not show;
   - doctor's `source:links_on_old_reading` counts them;
   - annotations have their re-anchor action, and the Guide shows moved passages flagged.

   **Default:** no "place it again" action yet.

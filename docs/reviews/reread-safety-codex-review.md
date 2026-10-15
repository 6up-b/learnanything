# Re-read safety: Codex review fixes

Stage: `fix/reread-safety` (worktree `learnanything-ux-impl`), stage record `reread-safety.md`.
Reviewed diff: `bffe086ec..5132074e8`. Review: Codex job `20261014-193248-YXSRjr`, 9 findings (3 High, 5 Medium,
1 Low). All 9 reproduced and fixed. None was rejected. Main was not merged here.

## Review

### Findings

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | Reused unit IDs release source-set exam scopes | fixed | `0eacfc61d` | `test_reread_safety.py::test_f1_reused_unit_ids_never_release_a_source_set_exam_scope` |
| F2 | High | Held-out inventory signals still use "latest reading + old span ID" | fixed | `0eacfc61d` | `test_f2_held_out_signals_stay_on_the_passage_they_name_after_a_reread`, `test_f2_a_held_out_signal_that_matches_nowhere_withholds_the_reading` |
| F3 | High | Reviewing a legacy citation silently changes what it cites | fixed | `0eacfc61d` | `test_f3_reviewing_a_legacy_citation_after_a_reread_keeps_what_it_cites` (also covers a copy made before the fix), `test_f3_a_reviewed_copy_keeps_its_citations_origin` |
| F4 | Medium | A page repair becomes the next re-read's entire scope | fixed | `0eacfc61d` | `test_f4_a_page_repair_never_becomes_the_next_rereads_scope` |
| F5 | Medium | Legacy saved places silently bind to another reading when aliases are absent | fixed | `0eacfc61d` | `test_f5_a_legacy_saved_place_with_an_unknown_reading_falls_back_to_the_history`, `test_f5_a_legacy_saved_place_after_a_reread_with_no_alias_falls_back_to_the_history`, `test_f5_a_legacy_saved_place_on_a_book_read_once_is_on_its_reading`; `ReaderScreen.guide.test.tsx`: "F5: a bare place on a book read again with no alias recorded asks the sidecar…", "F5: a bare place on a book never read again is used as it is" |
| F6 | Medium | Reusing a cached extraction moves annotations backward | fixed | `0eacfc61d` | `test_f6_an_import_that_reuses_an_older_reading_never_moves_annotations_backward` (through the card and the real import queue) |
| F7 | Medium | Carry-over failures become successful imports with permanently missing state | fixed | `0eacfc61d` | `test_f7_a_carry_over_that_fails_is_finished_later_never_lost[aliases, progress, selection, annotations]`, `test_f7_doctor_fix_state_finishes_a_carry_over_left_owed` |
| F8 | Medium | Search-hit navigation discards the hit's reading identity | fixed | `0eacfc61d` | `ReaderScreen.guide.test.tsx`: "F8: a search hit found on a reading the book was read again since is translated, not opened as is", "F8: a search hit on the reading the book opens on lands there with no translation" |
| F9 | Low | Self-hosted GLM-OCR is described and priced as z.ai | fixed | `0eacfc61d` | `test_f9_a_self_hosted_glm_ocr_reread_is_named_and_priced_as_local` |

`0eab17514` regenerates the DB and config references. It changes provenance only, plus `span_aliases.py` as a reader
of `source_object_citations` and the new test as a reader of `source_unit_inventories`.

**Reproduction first.** The tests were written before the fixes and run against the reviewed code: 15 Python tests
(F1 to F7, F9) and 2 vitest cases (F5, F8) failed, each for the reason the finding gives. Added with the fixes: F3's
check of a copy a review made before the fix, and F7's doctor `--fix-state` test. Two vitest guard cases (a bare
place on a book never read again, a hit on the open reading) pass both before and after.
- **F1:** after the re-read, neither reading's exam question was covered (`covers('extXA', 'x1')` was False). The
  scope's `u1` had resolved to B's Theory unit, and A's Theory unit was then withheld by label.
- **F2:** the partition held `('extXB', 'x1')`, the latest reading plus the old span id. Neither A's `x1` nor B's `y3`
  was in it.
- **F3:** after a status-only review, `source_object_lists` returned `('extB', 'a1')`, `('extB', 'a2')` and
  `('extB', 'a5')`: span ids of A read on B. Doctor counted the reviewed copies as `current`.
- **F4:** the plan read the repair child: no study state, so the card did not ask, and the import was queued with
  `page_selection [20]`.
- **F5:** `reader.saved_place` returned `('q1', 'current')` for a bare span id after a re-read that matched nothing,
  and `render_view` had no reading history. Vitest: the bare place was used as is, with no `reader_saved_place` call.
- **F6:** the cached import of B moved the annotation head from C to B while the Reader kept opening C.
- **F7:** the card showed "No questions for this book yet". Nothing recorded the failed carry-over, and nothing could
  finish it.
- **F8:** vitest: the hit's `s_before` was opened as a span of the current reading, and nothing was asked.
- **F9:** `engine == 'glm_ocr'`, priced and worded as z.ai.

### What changed

- **F1** (`exam_material._member_units`). A source-set scope's unit ids name units of the reading it was made on, and
  the scope does not record which one. So every completed top-level reading of the pinned revision is treated as a
  possible origin, and every interpretation is withheld:
  - in each origin, by unit id, plus by the labels the other origins resolve the scope to;
  - in every other extraction, by all those labels.

  A label that is missing, or an id that doesn't resolve in an origin, withholds that whole reading, as before. With
  one reading the behaviour is unchanged. Reused ids now over-protect (A's and B's "Exam" and "Theory" are both
  withheld) and never release anything.

  This departs from the finding's "withhold the source until explicitly repaired". The union already covers the true
  origin, whichever reading it was, without withholding the whole book. Binding a scope to its reading needs a new
  `source_sets.yaml` field and a change to every writer of a set (CLI, revision refresh, sidecar), which goes beyond
  this stage (open question A).
- **F2** (`exam_material._add_signals`).
  - Each inventory row's signals hold on the row's own `extraction_id`, and carry to every other completed reading of
    the revision through `span_aliases.SpanTranslator`. An exact alias or a same-place alias protects the aliased span.
    A span with no alias withholds that whole reading (`unresolved_signal`).
  - An inventory's unit counts as an exam unit when the member's exam material (rules 1 and 2, with F1's
    interpretations) covers it on the inventory's own reading. Before, the inventory's unit id was looked up in the
    latest reading's scope.
- **F3**. The fix has two parts:
  - `set_source_object_status` copies each citation with its original `created_at`, so a copy keeps when the citation
    was made.
  - The three readers of citations (`find_sources.source_object_lists`, `corpus.role_proposal_keys` and doctor's
    `citation_text_changed`) read a citation's origin as its first copy's time (`span_aliases.CITATION_MADE_AT_SQL`:
    same object, ordinal, revision and span). Copies already stamped with a review's time therefore resolve as their
    first version did.
- **F4** (`reread.reread_reading`). The confirmation's pages and study state, and the queued re-read's
  `page_selection`, come from the completed top-level reading the Reader opens (`resolve_extraction_id`), never a
  repair child.
- **F5**. Three parts:
  - `reader.render_view` returns `other_readings`: the book's other completed readings, whether or not aliases were
    recorded.
  - On the desktop, a bare span id counts as being on the open reading only when the book has no other reading.
    Otherwise `reader.saved_place` is asked.
  - `reader.saved_place` resolves a bare id only when its reading is certain
    (`span_aliases.legacy_place_origin`): the book was never read again; or it has exactly one other reading, an
    earlier one of the same revision, from which this reading's aliases were recorded. In that case this build made
    the reading, and this build never saves a bare place. Any other case returns `stale` with
    `reason: unknown_reading`, and the reading history decides.
- **F6** (`reread.carry_over`, `carry_annotations`).
  - A carry-over runs only onto the reading the Reader opens. An import whose cache hands back an older reading carries
    nothing (`skipped: not_the_current_reading`).
  - Annotations move only from earlier readings of the same revision, never from a newer reading or another revision.
  - Progress and the selection come from the newest earlier reading that has them, so a reading whose own carry never
    finished doesn't hide the learner's state.
  - Imports run one at a time (single drain lease), so completions can't overlap.
- **F7** (`jobs.handle_import`, `reread.carry_owed` / `finish_carry_over`).
  - Before a reading that owes a carry-over completes (or a cached reading is carried again), the import job's payload
    names it (`carry_over_for`). After the carry-over succeeds, the payload records it done (`carry_over_done`).
  - A carry-over that fails, or a worker that dies between completion and the carry-over, leaves it owed. The book's
    card then says "Your progress and notes didn't all move to the new reading" with "Finish moving them" (the card's
    `retry` action finishes it in the sidecar).
  - Doctor warns `source:reread_carry_incomplete`, and `--fix-state` finishes it.
  - The carry-over is idempotent, so a partial one (any step) finishes to the same state.
  - The reading itself stands throughout, and the import completes.
- **F8** (`ReaderScreen` / `useReadingProgress`).
  - A search hit opens with `jumpReading: hit.extractionId`, and a return from the stack carries its entry's
    `extractionId`.
  - A jump to another reading's span is translated through `reader.saved_place`, like a saved place. Approximate: "This
    book was read again: you're near the passage you found." Stale: the reading history decides.
  - The detour entry records the hit's own reading.
- **F9**. `_reread_plan` passes `selected_backend(...)` itself (`"api"`, `"local"` or None) instead of a boolean.
  - A self-hosted server is priced as free, with engine `glm_ocr_local`. Its line reads "GLM-OCR on this computer reads
    it: free." for a loopback `local_url`, and "Your GLM-OCR server reads it: free." for another computer.
  - Only z.ai with its OK already given asks for the cost confirmation.

**Nothing persisted changes meaning.** There is no algorithm successor, migration or schema change (head 202), and no
config change. Replay reads none of what changed: the job payload keys, `source_object_citations.created_at` on new
copies, and the read-side exam and alias resolution. New RPC fields (`other_readings`, `reason` on
`reader.saved_place`, `glm_ocr_local`) are additive and desktop-only. No RPC was added, so the pins in
`test_mobile_allowlist.py` are unchanged. No read path writes: `exam_material`, `reader.saved_place`, the card line and
doctor without `--fix-state` only read.

### The stage notes' focus items

1. **E1.** No finding. The re-read and repair paths read hash-checked bytes, and nothing here touches them.
2. **The alias authority.** F3, F5 and F8 were the remaining paths that resolved "latest reading + old span id"; all
   three now go through `span_aliases`. The MCP branch `mcp/c1-read-context` delegates retrieval to the shared
   `find_sources`/`corpus` service (Codex's spec table), so it inherits these fixes when it lands. It was not re-read
   here.
3. **Exam safety.** F1 and F2: held-out marks and source-set exam scopes can no longer be released by a re-read. Open
   question 2's "fails closed" now holds; before, a reused id resolved instead of failing.
4. **Replay and live database.** Unaffected (above). `rebuild --shadow` was not rerun, since no replayer or replayed
   table changed.
5. **Saved-place migration.** The `{extractionId, spanId}` encoding is unchanged. F5 removes the one unsafe case: a
   bare legacy value on a book read again with no recorded aliases.

### Open questions

- **A (F1's binding).** Should a source-set scope record the reading it was made on (a `source_sets.yaml` field)? Then
  the union of interpretations could narrow to the true origin. Until then a reused id over-protects. The owner's
  books have no exam scopes.
- **Open question 1 (search covering old readings).** It does not. `corpus.library_scope` searches the books' current
  readings only, so the stage's premise did not hold (Codex). The one remaining gap, a hit opened after a re-read
  completed, is F8.
- **Open question 3 (re-placing links).** Still open, as the stage said. Annotations have their re-anchor action, and
  the Guide shows moved passages flagged. A `needs_reanchor` or `stale` LO, facet or item link has no "place it again"
  action; doctor's `links_on_old_reading` counts them. That needs a link-placement UI, which this fix step does not
  add.

### Gate

Run on the final code tree, `0eab17514` (`0eacfc61d` plus regenerated references). Only this record was committed
after it. `TMPDIR` was the worktree's `fixtures-local/tmp`. No paid calls ($0.00); every test uses fakes.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 17 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **11,012 passed, 1 failed** (11 min 52 s, under parallel stages). The failure is `test_reader_rw3a_landing.py::test_check_me_goes_through_the_plan_path_and_is_logged_once[planned]`: the router chose `pi_svd_define_002` rather than `_001`. Rerun alone it passes: the file 5/5, and the test 3/3, three times. It is a load-only flake in a path this fix doesn't touch. |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **100 passed**, 10,913 deselected |
| `apps/learnloop-tauri`: `npm install`, `npm run typecheck` | ok, no errors |
| `npm test` (vitest) | **586 passed** in 82 files (582 before, plus 4 new) |
| `npm run frontend:build` | built |
| `cargo check` | not required: nothing under `src-tauri` changed in this fix step |
| `db_generate_reference.py` / `db_validate_reference.py`, `module_validate.py` | regenerated (`0eab17514`); both validations pass (schema head 202, 321 table notes) |
| CLI help / snapshots / RPC pins | unchanged: no option, no RPC and no snapshot changed |

**Tests added:**
- Python: 13 in `tests/test_reread_safety.py` (one parametrized four ways), so 16 cases. The file now collects 45.
- Desktop: 4 vitest cases in `ReaderScreen.guide.test.tsx`.

## Re-review

Codex job `20261014-205916-cK3SUy` re-reviewed `bffe086ec..d97237136`. Its verdict was REOPENED: F1 and F2 reopened,
F3 confirmed fixed, and one new finding, F10. All three open findings reproduced and are fixed in `9f1023b49`. None
was rejected. Main was not merged here.

### Findings

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | Matching labels still count as the same exam material (reopened) | fixed | `9f1023b49` | `test_rereview_f1_a_reused_unit_id_with_the_question_moved_out_keeps_it_withheld`, `test_rereview_f1_a_held_out_mark_follows_its_question_not_its_label[carried, not_carried]`, `test_rereview_f1_a_scope_whose_question_the_reread_reworded_withholds_the_reread` |
| F2 | High | Approximate aliases count as complete protection (reopened) | fixed | `9f1023b49` | `test_rereview_f2_a_held_out_passage_split_in_two_protects_both_halves`, `test_rereview_f2_a_half_moved_past_another_passage_withholds_the_reading`, `test_rereview_f2_a_held_out_unit_split_across_units_protects_both_halves[carried, not_carried]`, `test_rereview_f2_a_held_out_passage_merged_with_its_neighbour_holds_out_the_merged_block`, `test_rereview_f2_a_long_block_between_the_parts_of_a_split_withholds_the_reading` |
| F3 | High | Reviewing a legacy citation silently changes what it cites | confirmed fixed by the re-review; no change | `0eacfc61d` | the first round's F3 tests |
| F10 | Medium | Search translation discards the destination reading | fixed | `9f1023b49` | `test_rereview_f10_a_place_is_translated_onto_the_reading_the_reader_has_open`; `readerHooks.parity.test.tsx`: "(re-read F10): a hit's place answered on a reading other than the open one is never applied", "(re-read F10): a hit's place answered on the open reading lands there"; `ReaderScreen.guide.test.tsx`: "F10: a translation that lands on a reading other than the open one is never applied to it" |
| — | (same class as F10) | The original's PDF geometry is asked by source id, so it can be another reading's | fixed (not a finding) | `9f1023b49` | `ReaderScreen.guide.test.tsx`: "F10 (same class): the original's page geometry is asked for the reading the Reader rendered, never the book's latest" |

**Reproduction first.** Each test ran against the reviewed code (`d97237136`) and failed for the finding's reason:
- **F1:** `covers('extXB', 'y4')` was False. The scope's `u1` named A's Exam unit; B reused `u1` for Theory and moved
  the question out of its "Exam" unit, and the label carried protection to the heading alone. The held-out mark
  failed the same way, with or without the carry-over (`is_held_out('extXB', 'y4')` False). With the question
  reworded, the reviewed code released B (`extractions` was empty).
- **F2:** with `x1` split into `y1` and `y2`, only `y1` (the approximate alias) was held out, so `y2` was released.
  With a half moved past an exactly matched passage, nothing withheld B. A rule-3 held-out unit whose second question
  went into a unit of its own released that question (`y3`). A merged block holding the held-out question was not
  held out.
- **F10:** the sidecar rejected `toExtractionId` (`extra_forbidden`). In the hook test, an answer on C's span ids
  (status `current`, the reviewer's case) was applied to render B with no approximation line (`setActiveSpan('s2')`).
  On the screen, the approximate line showed for an answer on another reading.
- **PDF geometry:** `reader_pdf_view` was asked with the source id.

The two "lands there" vitest cases are controls and pass both before and after. The long-block F2 case guards the
new rule's fail-closed edge and is not a reproduction.

### What changed

- **One verified carry: `span_aliases.SpanCarrier`.** Protection never takes one alias as the whole answer. It asks
  where a protected span's words can lie on the other reading:
  - A same-text alias (an exact content hash) carries a span to its block.
  - Any other span carries to the whole stretch between the images of the nearest same-text anchors around it, plus
    its own alias. That holds only when the stretch is verified:
    - the anchors keep their order;
    - the span's letters and digits run on, in order, through the stretch (both parts of a split, the whole of a
      merge);
    - the run may skip the stretch's short blocks (40 letters and digits or fewer: a heading, a page number or a
      running head the re-read put between the parts), never a long one.
  - A span whose words changed, or moved past an anchor, or that has no anchor on either side returns `None`. The
    caller then withholds that whole reading (fail closed).
  - Order inside the stretch doesn't matter for safety, because the whole stretch is protected. The words check only
    rules out a part that lies outside it.
- **F1** (`exam_material._member_units`, `_held_out_units`). Each origin's interpretation of a source-set scope, and
  each held-out mark, now reaches every other completed reading of its revision through the carry, never by label.
  A carry that can't be verified withholds the whole reading. Another revision's readings and page-repair children
  still resolve by label, as the exam-protection stage designed:
  - a re-read never registers a new revision (E1);
  - the Reader, library search and the MCP branch open only top-level readings, so a repair child is never served.

  The finding's two options are both taken: the scope is bound to verified material, and an ambiguous reading is
  withheld. Recording a scope's own reading in `source_sets.yaml` (first round, open question A) is still not done.
- **F2** (`exam_material._add_signals`, and the marks above). Signals and marks reach every block that may hold their
  words, never only the block an approximate alias names.
- **F10** (`reader.saved_place`, `useReadingProgress`).
  - The RPC takes `to_extraction_id`, the reading the Reader has open. An unknown reading is `extraction_not_found`;
    another book's is `validation_error`. Without it, the RPC uses the book's current reading, as before.
  - The Reader sends `toExtractionId: reading.extractionId`. It applies an answer only when `landed.extractionId` is
    that reading; any other answer falls back to the reading history.
  - A bare place on B, with C completed, has two other readings, so `legacy_place_origin` stays unknown (`stale`).
- **Same class as F10** (`ReaderScreen`). The PDF view is asked for, and cached under, `view.extractionId`. Before,
  a source id resolved to the latest reading, whose block geometry (highlights, selection to span) could be another
  reading's.

**Nothing persisted changes meaning.** There is no migration, schema change, algorithm successor or config change.
- The carry reads the readings' IR and their aliases (persisted, or computed in memory as before) and writes nothing.
- `reader.saved_place` only reads.
- Replay reads none of it.
- `to_extraction_id` is an additive, optional RPC field. No RPC was added, so the pins in `test_mobile_allowlist.py`
  are unchanged; only its comment now says where the place is translated.
- The DB reference regenerated with provenance-only changes (the source commit hash). They were not committed, and
  validation passes.

**Cost.** The carry loads both readings' IR only when a protected span has no same-text alias, once per build. Only a
book read again that has exam or held-out material pays it.

### The stage notes' focus items, re-assessed

1. **E1.** Unchanged in this step, and the re-review raised nothing.
2. **The alias authority.** F10 closes the search path's last silent case, and the PDF geometry was the same class.
   The MCP branch `mcp/c1-read-context` (`34527fa13`) was read here:
   - `remote/sources.py` reads each `find_sources` hit's block by the hit's own extraction id;
   - `learner_context.withheld_items` asks `exam_material`, `held_out_items` and `item_exam_status`;
   - it resolves no span of its own, so it inherits the verified carry when it lands.
3. **Exam safety.** A re-read can no longer release a held-out mark, a held-out signal or a source-set exam scope.
   Every unverifiable carry withholds the whole reading (tests above), so open question 2's over-protective default
   holds.
4. **Replay and the live database.** Unaffected (above). No read path writes.
5. **Saved-place migration.** The `{extractionId, spanId}` encoding is unchanged. A translation now names the reading
   it is for.

### Open questions

- **B (new, owner): the cost of failing closed.** A re-read whose words differ inside a protected unit withholds that
  whole reading. Examples are an exam-scoped unit, a held-out mark or a held-out signal after a GLM-OCR re-read whose
  math or hyphenation came out differently. In that case:
  - the Reader refuses its model contexts on the whole book (held-out);
  - the leakage gate fingerprints every block;
  - teaching contexts withhold the reading (exam material).

  Nothing tells the learner why yet. The owner's vault copies (backup copies from 2026-10-13, read-only) have no exam
  member, exam scope, held-out mark or outline exam pick, so nothing changes for them today. The options:
  - keep it (the default);
  - fuzzy verification, which is narrower but could release a fragment that moved;
  - a "mark it again on this reading" action that confirms the new reading's own units.
- **Open question 1 (search covering old readings).** Unchanged: `corpus.library_scope` searches current readings
  only. A hit opened after a re-read is translated onto the reading the Reader opened (F8, F10).
- **Open question 3 (re-placing links).** Still open. A `needs_reanchor` or `stale` LO, facet or item link has no
  "place it again" action.

### Gate

Run on `9f1023b49`, the final code tree; only this record was committed after it. `TMPDIR` was the worktree's
`fixtures-local/tmp`. No paid calls were made ($0.00), and every test uses fakes. The owner's vault copies were read
only, through backup copies already under `fixtures-local/`, to count exam roles and marks.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 17 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **11,024 passed**, 0 failed (13 min 7 s, after waiting for another worktree's run) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **100 passed**, 10,924 deselected |
| `apps/learnloop-tauri`: `npm install`, `npm run typecheck` | ok, no errors |
| `npm test` (vitest) | **590 passed** in 82 files (586 before, plus 4 new) |
| `npm run frontend:build` | built |
| `cargo check` | not required: nothing under `src-tauri` changed |
| `db_validate_reference.py`, `module_validate.py`, `validate_vault.py` | pass. No schema change, so the regenerated DB reference (provenance only) was not committed. `desktop_validate.py` fails on `src/copy/denyList.ts` ("unclassified desktop source"), a file from UX Phase 1 that this stage never touched. It is not part of this gate. |
| CLI help / snapshots / RPC pins | unchanged: no option, no RPC and no snapshot changed. `to_extraction_id` is an additive field. |

During a parallel screen run, `FeedbackScreen.test.tsx` "falls back to the list when the queue is empty…" failed once
under load. Rerun alone it passed (11/11), and it passed in the full `npm test` above.

**Tests added:**
- Python: 9 in `tests/test_reread_safety.py` (two parametrized two ways), so 11 cases. The file now collects 56.
- Desktop: 4 vitest cases, 2 in `ReaderScreen.guide.test.tsx` and 2 in `readerHooks.parity.test.tsx`. Four existing
  saved-place expectations now include `toExtractionId`.

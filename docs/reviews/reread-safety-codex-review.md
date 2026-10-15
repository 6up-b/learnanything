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

## Protection redesign

The final Codex verify (job `20261015-011515-uLjC1L`, `d97237136..9b933cc21`) confirmed F3 and F10 fixed, reopened
F1 and F2, and found F11 (High). All three concern one mechanism: carrying exam and held-out protection to a new
reading by matching its content. This was the third round on that mechanism (labels, then aliases, then the verified
carry), so the orchestrator decided to redesign rather than patch, consistent with the owner's fail-closed and
one-authority principles. Main was not merged here.

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | Label-only protection on unpinned revisions (reopened) | fixed by the redesign | `5fb11639f` | `test_redesign_f1_a_moved_question_on_a_new_revisions_reread_is_never_unprotected`, `test_redesign_f1_a_moved_question_under_a_held_out_mark_is_never_unprotected` |
| F2 | High | One exact alias counted as complete protection (reopened) | fixed by the redesign | `5fb11639f` | `test_redesign_f2_duplicate_and_fragment_copies_are_never_unprotected[held_out_mark, exam_scope]` |
| F11 | High | Verification erases mathematical operators | fixed by the redesign | `5fb11639f` | `test_redesign_f11_operators_are_never_erased_into_a_release` |
| F3, F10 | High, Medium | (earlier rounds) | confirmed fixed by the verify; no change | `0eacfc61d`, `9f1023b49` | the earlier rounds' tests |

`55059e4af` regenerates the DB and config references (provenance, moved `doctor.py` and `jobs.py` lines, and
`exam_marking.py` among the readers of the source tables). `d47a94f44` updates one more test the first full run
found: the source-retrieval guard that expected an exam override to reach a re-import by its label.

### The rule, as built

**Protection never carries to another reading** by content, alias or label matching. The one predicate,
`content/sources/exam_material.py`, decides it as its new rule 4; every consumer already reads that module.

- **A protected source.** Any extraction of any revision of the source carries positional protection:
  - an exam scope (a source-set scope entry overridden to `exam`, rule 2);
  - a held-out mark (`held_out_evaluation` in a unit selection, rule 3);
  - or a held-out assessment signal of an exam unit's inventory.

  A whole-source exam role (an exam member, an outline pick of `exam`, rule 1) names no reading, so it still reaches
  every extraction as before.
- **Withheld wholesale.** Every extraction of a protected source with no protection marked directly on it is added
  whole to the held-out partition (reason `unmarked_reading`), and so to exam material. That covers each reading of a
  new revision too. Because every consumer already reads the predicate, a held-back reading gets:
  - no Reader Ask, dialogue, preset or check: `held_out_material`;
  - no teaching or tutor context, generation or retrieval: `exam_material` and the corpus exclusions;
  - no leakage-gate pass: `held_out_spans` fingerprints every block;
  - no `find_sources` hit;
  - no margin cue.

  The Library's own keyword search, the learner looking through their own books with no model involved, is unchanged,
  as it is for any exam material.
- **Marked.** An extraction is marked when the owner's protection is on it:
  - the reading an exam scope names. That is the first completed top-level reading of the member's pinned revision.
    A re-read only ever adds later readings, so this binding never moves.
  - a held-out mark in its own unit selection;
  - the owner's "Mark exam material on this reading", recorded as `exam_paper_metadata.protection_marked` in that
    reading's selection. It marks the reading even when nothing on it is held out.

  A held-out signal marks the reading it was made on only when the source carries no owner's mark at all. So an
  inventory that a build makes on a held-back reading never releases it.
- **Exactly as marked.** A marked reading is protected by its own marks only, by unit id:
  - rule 2 resolves on the scope's reading only;
  - rule 3 resolves on the marking extraction only;
  - signals hold on their own reading only.

  The earlier cross-extraction carries are gone: labels for other revisions and page repairs, label occurrence and
  content hash, and the verified carry. So is the scope's "every reading is a possible origin" union.
  - A held-out mark that does not resolve withholds its own extraction.
  - An exam scope that does not resolve on its reading, or whose pinned revision has no reading, withholds every
    extraction of the source, as on main.
- **Removed.**
  - `span_aliases.SpanCarrier` with its word normalisation and the furniture rule;
  - `_Reader.carry_into`, `origins` and `pinned`;
  - the label-occurrence logic and `unresolved_signal`.

  Aliases now serve references only: progress, citations, notes, links and the saved place. Those, E1's stored
  bytes, the page scope, the earlier doctor checks and the card's estimate are unchanged.

**The owner's action** (`content/pipeline/exam_marking.py`):

- **The card.** While the reading the Reader opens is held back, the card says "This reading is held back until you
  mark its exam material" (tone `problem`), with one action, "Mark exam material on this reading"
  (`source_action mark_exam_material`). Its details say: "You marked exam material in another reading of this book.
  LearnLoop doesn't guess where that material is in this reading, so it keeps the whole reading out of explanations,
  questions and search until you mark its exam material here. The other reading stays protected as you marked it."
  The line comes after the E1 repair and "Finish moving them", and before every other line.
- **The confirmation.** The first call returns a confirmation and writes nothing. It names what will be held out, for
  example "Held out as exam material: 3 Exam review." with "These are suggested from what you marked in the other
  reading: check them. The rest of this reading becomes available for explanations, questions and search." The
  buttons are "Mark them" (or "Mark it") and "Not now". The desktop's existing confirmation dialog shows it: the
  Library uses an alert dialog, and the preparing view uses the same confirm.
- **The suggestion.** It is non-authoritative and deliberately over-inclusive. It is drawn from every marked reading
  of the book: their held-out spans and their exam-scope units. A unit of the new reading is suggested when any of
  these holds:
  - `reread.unit_map` maps a protected unit to it;
  - a protected span's alias (the same text or the same place) lands in it;
  - it has a block on the same page as a protected block.
- **The marking.** Confirmed, the action finishes any carry-over the re-read still owes, so that the study map's
  chapters arrive. It then writes the suggested units as `held_out_evaluation` and the owner's mark into the reading's
  own selection. A scope's exam units are held out there too, which is stricter than the exam role they have on the
  first reading. The earlier reading keeps its own marks untouched.
- **Doctor.** `source:reading_held_back` is a warning naming each book whose current reading is held back, and
  counting its older held-back readings. Only the owner can mark, so `--fix-state` never does.
- **The Reader's refusals.** On a held-back reading the four refusal paths and the section check say "This reading of
  the book is held back until you mark its exam material (on the book's card in the Library), so LearnLoop won't
  explain it or make questions from it yet." They no longer say "an exam you'll sit later" (`held_out_refusal`).
- **The re-read confirmation.** For a protected book it adds "Your exam material isn't moved: the new reading stays
  out of explanations, questions and search until you mark its exam material on the book's card", and always asks.

**Two supporting changes**, without which a mark would not stay where the owner put it:

- `save_unit_selection` keeps the stored exam use modes and paper metadata when the caller names none. The desktop's
  and the CLI's study-map saves name none. Before, such a save erased every held-out mark (a release on main too) and
  would have erased the owner's mark. An explicit `{}` still clears them.
- `revision_refresh` no longer advances a member whose scope overrides units to `exam`. Its unit ids would name other
  units on the new revision's reading, which is a carry by position. The member stays pinned, and `RefreshResult`
  reports it in `kept_pinned` (an additive key). The new revision's readings are held back until marked.

`carry_selection` carries chapters, boundary overrides and paper metadata, and never exam use modes or the owner's
mark. If the owner's marking made the new reading's selection before the carry-over ran, the carry-over fills in its
chapters and keeps its marks.

### Reproduction first

Each reproduction uses only APIs that both designs have. All five cases were run against `9b933cc21`, with its `src`
and `migrations` first on the path, and failed for the verify's reason:

| Case | Unprotected copies on `9b933cc21` |
|---|---|
| F1: the scope pins R1; R2's B1 keeps the question under "Exam" and B2 moves it to a Questions unit | `('extR2B2', 'z2')` |
| F1, held-out variant | `('extR2B2', 'z2')` |
| F2: an exact copy plus split copies, held-out mark | `('extPB', 'y3')`, `('extPB', 'y4')` |
| F2: an exact copy plus split copies, exam scope | `('extPB', 'y3')`, `('extPB', 'y4')` |
| F11: `Solve x+1=2. Solve x-1=2.` held out, re-segmented past the notes | `('extPB', 'b3')` |

In F11's scenario, the old code's Reader refusal predicate returned `[]` for `b3`, `held_out_items` omitted an item
made from `b3`, and the partition held only `b1`. Now the predicate returns `['b3']`, the item is held out, and
`extPB` is withheld whole. On the new code every case leaves no unprotected copy. Each also checks that the reading
the protection was marked on stays exactly as marked: A's Theory, appendix and unprotected question stay usable.

**New tests** (`tests/test_reread_safety.py`, 11 cases; the file now collects 67):

- the five reproductions above;
- `test_redesign_marking_the_new_reading_makes_it_usable`. It covers, in order:
  - the card line and its action;
  - the doctor warning;
  - the plain refusal;
  - the plan writes nothing;
  - the marking holds out only "3 Exam review", keeps the carried study map, and leaves A as marked;
  - the warning and the line are gone, and nothing is left to mark.
- `test_redesign_a_study_map_save_keeps_the_owners_marks`;
- `test_redesign_an_unprotected_book_is_unaffected`: nothing is withheld for it, even beside a protected book;
- `test_redesign_a_reading_of_a_new_revision_is_held_back_until_marked`: marking the current revision's reading
  holds out the moved question and releases its Theory; the other R2 reading stays held back, and doctor counts it;
- `test_redesign_a_signal_a_build_makes_on_a_held_back_reading_never_releases_it`;
- `test_redesign_a_refresh_keeps_an_exam_scoped_member_on_its_revision`.

The card's full flow was added to `test_the_reread_keeps_the_page_scope_and_carries_the_selection`: the re-read
confirmation's line, the held-back line, the confirmation, the marking, and the reading usable afterwards.

Desktop: one vitest case in `LibraryPlace.reread.test.tsx`. A held-back card's action asks, names what it holds out,
and calls again with `confirmed`.

**Tests changed by the rule** (their protective intent kept):

- `test_reread_safety.py`. Selections no longer carry exam use modes, in four places: progress and selection, the
  coarser reading, the card's selection, and F7's finished carry-over. Also changed:
  - `test_held_out_material_stays_withheld_on_the_new_reading`: B is withheld whole with `unmarked_reading`, and A
    exactly as marked;
  - the margin cue: none on the held-back reading; after marking, only `b1`;
  - three re-review tests now assert the held-back reading, then the owner's marking: the question that moved to a
    Questions unit is held out and Theory is usable; both halves of a split are held out and the appendix is usable;
    the merged block is held out with the rest of B.
- `test_exam_protection_review.py`, the exam-protection stage's F2 tests. Two extractions that each carry marks are
  each held by their own marks exactly; neither's mark reaches the other by label. A third extraction with no marks is
  withheld whole.
  - `test_held_out_marks_in_two_extractions_each_reach_the_other` is now
    `..._each_hold_their_own_extraction_exactly`.
  - `test_the_same_occurrence_with_other_content_is_not_the_same_unit` is now
    `test_a_second_extraction_marked_by_the_owner_is_held_by_its_own_marks_only`.
- `test_source_retrieval_guards.py` (`d47a94f44`). `test_a_unit_override_is_resolved_in_every_extraction_by_label`
  is now `..._resolved_on_its_reading_and_an_unmarked_reimport_is_held_back_whole`. The override holds on its
  reading, and the re-import is in `teaching_exclusions` whole. That assertion fails on `9b933cc21`, where only
  `ext_exam` was there.

### The owner's vaults

Backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) were made of the main checkout's
`fixtures/linear_algebra` and `fixtures/probability`, opened only to copy. They are under the worktree's gitignored
`fixtures-local/protection-redesign/copies/`, as `old/` and `new/`. The same probe ran on each: `9b933cc21` on `old/`,
this redesign on `new/`.

Both vaults have no exam member, no exam scope entry, no held-out or exam-pick selection, and no exam inventory. Each
has 4 completed readings. With both codes:

- exam material, the held-out partition and held-out items are empty and identical;
- the redesign finds no protected source and no held-back reading.

Nothing changes for them. The main checkout's `git status fixtures/` was identical before and after. Only the mtime of
the gitignored `-shm` index changed; the databases' size and mtime are the same, and each `-wal` is still empty.

### Persisted meaning, RPCs, cost

- There is no migration or schema change (head 202), no config change and no algorithm successor.
- The writes are to `source_unit_selections` (WORKFLOW) and `sources/source_sets.yaml` (a member kept pinned), and
  replay reads neither. Read paths write nothing.
- `source_action` gains the action `mark_exam_material` and a `marked` result; `get_source_library` gains the
  held-back line; `RefreshResult` gains `kept_pinned`. All are additive and desktop-only. No RPC was added, so the
  mobile pins are unchanged; only their comment names the action.
- CLI help and the sidecar serializer snapshots are unchanged.
- Cost: the predicate no longer loads both readings' IR. A protected book costs one selection query and its exam
  members' inventories per build. Only the confirmation and the marking compute the suggestion, which uses the alias
  map, the unit map and pages.
- No paid calls ($0.00).

### Open questions for the owner

- **A (still open): binding a scope to its reading.** A scope names the first completed reading of its pinned
  revision. A scope hand-written after a re-read with the later reading's unit ids would be read on the first reading.
  The later reading stays held back whole, so the reading the Reader opens is never released this way. Exam role
  overrides are written only by hand or through `upsert_source_set` (no desktop surface writes them), and the owner's
  books have none. A `source_sets.yaml` field naming the reading would close it.
- **B (superseded): the cost of failing closed.** It is now one tap on the card, which says why in plain words.
- **C (new): editing the suggestion.** The marking holds out the whole suggestion, which is over-inclusive. There is
  no per-unit editor for exam use modes on the desktop, as before. To narrow it, the owner would need one.

### Gate

Run on `d47a94f44`, the final code tree. Only this record was committed after it, along with five corrected lines in
`reread-safety.md` that described the retired carry. `TMPDIR` was the worktree's `fixtures-local/tmp`. No paid calls
were made ($0.00), and every test uses fakes.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 17 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **11,035 passed**, 0 failed (10 min 50 s). An earlier run on `55059e4af` had 11,034 passed and 1 failed: the retrieval guard above, a behaviour test (not a timing failure), updated in `d47a94f44`. |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **100 passed**, 10,935 deselected |
| `apps/learnloop-tauri`: `npm install`, `npm run typecheck` | ok, no errors |
| `npm test` (vitest) | **591 passed** in 82 files (590 before, plus 1 new) |
| `npm run frontend:build` | built |
| `cargo check` | not required: nothing under `src-tauri` changed |
| `db_generate_reference.py` / `db_validate_reference.py` | regenerated (`55059e4af`); validation passes, with no errors (schema head 202, 321 table notes) |
| `validate_vault.py` | passes |
| `module_validate.py`, `desktop_validate.py` | Both fail before and after, and neither is part of this gate. `module_validate.py` reports missing module notes for hundreds of modules (it fails the same way on `9b933cc21`); `exam_marking.py` adds one. `desktop_validate.py` fails on the unclassified `src/copy/denyList.ts`, as recorded in earlier rounds. |
| CLI help / snapshots / RPC pins | `test_cli_help_snapshot.py`, `test_sidecar_serializer_snapshot.py` and `test_controller_snapshot.py` pass unchanged. No RPC was added; the mobile allowlist's comment names the new action. |

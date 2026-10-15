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

# Astra batch review 1: fixes (eaf9859ad..680bb9e18)

Stage `astra-batch1-fixes`, branch `fix/astra-batch1` from main `680bb9e18`.
Findings: one High (the as-printed crop could show the solution), one Medium
(the metered Ask budget reset across the answer box -> Work in Steps ->
Reader handoff), plus the queued CA1 polish the owner decided. No migration,
no algorithm successor, no paid or live model calls (every model a fake).

## A. High: the free crop never shows the solution

*Its read-time rules (leak test, "unsure" solution blocks, the lexical figure
rule, merged crops) are superseded by the Redesign section below.*

Owner decision (2026-10-26, binding): "viewing the original exam page picture
ocr is fine to make sure theres no latex errors in the exam question, but i
would hope that crop excludes the solution."

* **Import time** (`content/authoring/exercise_authoring.py`,
  `_owned_spans`): a single-exercise import owns only the blocks its anchored
  statement covers, as a split's items already did; it no longer marks every
  selected span as owned. A paraphrased statement (the full selection became
  the prompt) owns nothing. A selection-level edit owns nothing, except one
  item whose statement is the whole edited passage (the capture editor's OCR
  fix of what the learner selected), which owns the whole selection.
* **Read time** (`reader/as_printed.py`, `_without_solutions`, applied by
  `printed_origin` to selection imports and `canonical_exercise` alike, so
  items marked by the old rule are covered without rewriting them):
  * a block on the import's book-solution spans (`verification.book_solution`
    / `solution_search` of its `source_exercise_imports` rows), led by
    "Solution", or with a `solution` effective role the statement shares no
    words with, leaves the crop and the original page's outline;
  * a block that holds the stem and its solution together (a solution or
    proof lead starts a later part of it; or, its words beside the statement
    give the expected answer away per `tutor_qa.span_leaks_expected` while
    the statement does not), or a solution-region block the statement shares
    words with (ambiguous), leaves **no free crop**: `NO_CROP` ("the crop
    isn't available for this problem · the original page is") with the
    charged original page (one hint-equivalent before Submit, unchanged);
  * a guard that cannot be read fails closed the same way.
  * The Reader sits below source retrieval (import contract: no
    `reader -> source_retrieval`), so the desktop RPC
    (`learnloop_sidecar/handlers/as_printed.py`) passes the role reader
    (`source_retrieval.corpus.block_roles`) and the leak matcher in; a direct
    caller without them still gets the solution-span, lead and stored-hint
    rules.
* No new constant: comparisons are structural (whole-word runs), and the
  leak test is the tutor's existing matcher.

Tests (`tests/test_reader_ca1_astra_fixes.py`): the Astra scenario (problem +
separate solution block, single-item import) owns and crops only the problem;
the same item with old-rule marks crops only the problem; a block named by the
import's book solution is never cropped; a merged block (lead) and a merged
block (answer stated beside the stem, no lead) give `NO_CROP` with the page
offered; a multi-item split still crops each item's own block; whole-passage
and partial selection-level edits; a canonical exercise naming a solution
block. `tests/test_reader_ca1_codex_review.py::_import_selection` now uses a
statement over all three selected blocks (it encoded the old rule); the
solution-neighbour geometry tests are unchanged and pass.

## B. Medium: one attempt, one Ask budget, across the handoff

* `workbench.open` from the practice screen or the plan records the answer
  box's draft keys on the problem: the key the screen sends
  (`WorkbenchOpenInput.submissionId`, new, optional; the practice screen now
  sends `submissionId.current` on open and resume) and the key of the draft
  its practice session's checkpoint holds on the item. Stored as a
  salience-only `reader_action_invoked` event, `event =
  workbench_draft_handed` (`interaction_events`, a raw ledger): recorded once
  per key, never the workbench's own `workbench:<id>`. **No migration.**
* `reader.workbench.attempt_identities` resolves the attempt's identities
  both ways (a workbench brings the draft keys handed into it; a draft key
  brings the item's workbenches it was handed into), to a fixed point. The
  sidecar adapter carries them as `tutor_qa.AttemptAliases` into the
  transcript, the tutor's thread, the per-attempt budget (`question_usage`)
  and the recovered-answer count. `tutor_qa` never reads the workbench
  (import contract W1: replay, evidence and serving internals never read the
  workbench; a first cut that imported the store from `tutor_qa` broke it and
  was moved).
* Raw question rows are unchanged (each keeps the key it was asked under).
  The subscription (plan) route stays unbounded. A new attempt (an attempt row
  after the questions) starts a fresh allowance; another serving's key is
  still another attempt.

Tests (`tests/test_reader_ca2_astra_handoff.py`): the 3/3 scenario stays 3/3
in the Reader and the fourth question is refused; Astra's probe on the
counting functions (3/3 before and after; 0/3 without the resolved
identities, the old rule, shown in the same test); the reverse direction;
raw rows; the checkpoint fallback with no screen key; recorded once and
salience only; a Reader open hands no draft; another serving; a fresh
allowance after an attempt; the plan route unbounded. Verified failing with
the resolution disabled (4 of 10 fail), passing with it.
`PracticeScreen.workbench.test.tsx` checks the screen sends its draft key.

### Algorithm-change playbook

Not a change to persisted meaning: the Ask budget is a request guardrail read
at ask time, not scoring, scheduling, a projection or admissibility. Hint
equivalents (the evidence path, `hint_equivalents_for_submission`) are
item-window counts and are untouched; no replay or rebuild reads the new
event. **No successor needed**; no table, no fingerprint change.

## C. CA1 polish

* The book in the header is the learner title (`add_source.learner_title`:
  display title, else the file name in words) in `practice.as_printed` and in
  the canonical-exercise DTO, so an untitled book is named as the Library
  names it, not "your book".
* An empty or blank exercise label is no label: the server returns
  `exerciseLabel: null`; the practice header renders "From <book>" without a
  dangling ": ", and the after-feedback locator drops the empty part.

## Redesign (Opus, 2026-10-27): the free crop by construction

Two Codex rounds on A's text heuristics each left narrower residuals; the
final verify (job `20261027-042324-138aCi`) reopened F2, F3, F5 and F6. By
the escalation rule this is a redesign, not a third round. It replaces A's
read-time rules and the re-review's lexical figure rule. F1, F4, the CA2
handoff (B) and the polish (C) are kept unchanged, and their tests pass.

### The design (`reader/as_printed.py` module docstring)

1. **Solution blocks leave.** A block on the import's book-solution spans,
   with a `solution` effective role, or led by "Solution" is never cropped
   or outlined, whatever the stored marks say. (Unchanged from A.)
2. **Text by containment.** Every own text block that remains must lie
   inside the statement: its whole text, less at most a leading label or
   heading (F1's `_is_label`, kept), is a run of the statement's words. The
   comparison ignores spaces, so "3 + 3" still places "3+3". A block that is
   only a label also prints. Anything else is doubt: words after the
   statement, other words before it, or a block the statement does not
   place. There are no answer-leak tests, because a block inside the
   statement shows nothing the prompt does not. `tutor_qa.span_leaks_expected`,
   the "unsure" solution kind, the later-part lead test on text and the
   `leaks` plumbing through the sidecar are gone.
3. **Coverage from what prints.** The blocks that print must print the whole
   statement between them. A dropped block supplies nothing (F3). A printed
   figure whose text the statement quotes counts.
4. **Figures by role, decided at import.** The import author already reads
   the selection. Its structured output now carries `figure_roles` per item
   (`stimulus | answer | worked | unrelated`) for the selection's figures,
   which it receives in `context.figures`. The figure context and its
   instructions are left out when the selection holds no figure, as
   `book_solution` is. The prompt is `mvp-0.4-figure-roles-criteria-by-fact-v2`.
   Validation (`exercise_authoring._figure_roles`) only narrows a claim:
   * an id outside the selection's figures is ignored;
   * a figure the author does not name is `unrelated`;
   * two claims on one figure resolve away from `stimulus`;
   * a figure any item calls `answer` or `worked` is no item's stimulus
     (`another_exercise_answer`);
   * a statement that names figure numbers rejects a numbered figure
     carrying none of them (`figure_number_mismatch`; "Figures 1 and 2" names
     both).

   Each figure ref records `figure_role` (and `figure_role_rejected`). The
   figure is `owned` only as a validated stimulus, whatever text overlaps
   it. This persists in the existing provenance JSON, so there is **no
   migration**. A `canonical_exercise` honours a recorded refusal on its
   figure refs. `ingest.block_roles.referenced_figures` and its "shown/the
   diagram" vocabulary are deleted. `figure_numbers` remains only as the
   cross-check, now reading lists through the module's existing reference
   grammar.
5. **One rule reads every owned figure, new or legacy.**
   * During a check on your own (Q10), an owned figure shows unless it is a
     solution block.
   * In the free crop, an owned figure shows only when it comes before every
     solution block and every block a solution or proof lead runs into, in
     reading order. Any other owned figure is left to the original page
     beside the crop.
   * The learner's sub-box is kept in both cases.
6. **One crop per retained region.** `crop_boxes` never merges. A crop is
   exactly one block's box, or its sub-box clipped to that box, so it holds
   no pixel of a block or sub-box that was left out (F6). The neighbour
   query and the area-based merge test (`_union`, `_shows_more_of`, exact
   `Fraction` areas) are gone. The DTO shape is unchanged (a list of crops,
   each with `span_ids`, now one id each), so the frontend is unchanged and
   already stacks several crops.

### How each open finding is closed

| Finding | Closed by | Test (`tests/test_reader_ca1_astra_redesign.py`) |
| --- | --- | --- |
| F2 "Estimate f(2) from the graph." | the author's `stimulus` role, not the statement's words | `test_f2_a_required_input_graph_is_shown_in_a_check_on_your_own`, `test_f2_the_input_graph_prints_with_the_problem_outside_a_check` |
| F3 part (b) in a dropped solution block | coverage only from printed blocks | `test_f3_a_partial_problem_gives_no_free_crop`, `test_f3_up_to_moved_spaces_too`; control `test_f3_the_whole_problem_in_printed_blocks_still_crops` |
| F5 "Draw the diagram ..." + completed diagram | role `answer`, or no role at all, is not stimulus | `test_f5_a_completed_answer_diagram_is_not_stimulus[author_says_answer, author_says_nothing]`, `test_f5_a_completed_answer_diagram_never_prints_for_free` |
| F5 "Use Figure 1" + only Figure 2 | `figure_number_mismatch` refuses even an author's stimulus | `test_f5_a_figure_whose_number_contradicts_the_statement_is_refused[author_says_stimulus, author_says_nothing]` |
| F6 merged crop restores the inset | no merging | `test_f6_an_excluded_inset_never_returns_through_a_merged_crop`, `test_f6_and_in_a_check_on_your_own`, `test_f6_and_when_the_text_gives_no_free_crop`, `test_f6_crop_boxes_returns_one_crop_per_retained_region` |

Fail-before was run on the pre-redesign tip (`073b1b4ff`, exported to a
scratch tree) with the new test file. The scratch copy has a shim that drops
`figure_roles` when the old schema lacks it, so the old code ran its lexical
rule. All 22 tests that touch the change failed for the reported reason:

* F2: `kind == "none"` cold, and the warm crop `[["q1"]]` without the graph.
* F3: a free crop of part (a).
* F5: the answer diagram `owned` and merged into the crop `[["d1", "d2"]]`;
  Figure 2 `owned` under "Use Figure 1".
* F6: blue inset pixels in the merged crop `(0, 50, 540, 320)`, and in the
  cold figure crop.

One legacy test passes before and after (`..._on_the_solution_spans_never_prints`).

### Legacy items (imported before the redesign, no role recorded)

A check on your own **cannot** open the charged original page (`_page_without_crop`
returns nothing when cold). The brief's second branch therefore applies to
cold checks. In the free view, the page **is** offered beside the crop, so
the brief's first branch applies there. Rule 5 is exactly that, applied to
every item, because one rule is simpler than two and the ordering test only
costs availability on new items:

* **Cold:** main's figures (the owned ones) less solution-span,
  solution-role and "Solution"-led figures. The problem stays answerable.
* **Free crop:** additionally, only figures before every solution start;
  the rest stay behind the original page.

**Residual:** a legacy single-exercise import marked every block owned. An
unmarked completed answer figure (no solution span, role or lead) selected
with "Sketch y=x^2." therefore shows, in the free crop and cold, as on main.
`test_the_legacy_residual_an_old_mark_on_an_unmarked_answer_graph_keeps_mains_rule`
pins it. An item re-imported after this lands gets roles.

### Tests rewritten (they encoded a heuristic)

* Crop merging: `test_each_of_the_problems_blocks_is_its_own_crop_in_reading_order`
  (was `..._splits_the_crop_and_each_page_has_its_own`),
  `test_the_crops_from_the_page_hold_only_the_problems_own_ink`,
  `test_the_crop_rpc_takes_a_problems_blocks`,
  `test_without_the_original_...` (four crops, not three). In
  `test_reader_ca1_codex_review.py`, the solution-neighbour geometry:
  * `test_a_neighbour_reaching_into_the_gap_is_in_no_crop_...` still holds;
  * `test_adjacent_blocks_stay_two_crops` and `test_a_crop_is_exactly_its_blocks_box`
    replace the two tests that pinned when a join was allowed;
  * `test_a_reader_selection_import_shows_its_print_after_binding` and
    `test_a_region_selection_s_sub_box_is_the_crop_shown` expect one crop per
    block.
* Figure ownership: `_import_selection` (codex review) and the F2/F5/F6
  tests of `test_reader_ca1_astra_codex_review.py` and
  `test_reader_ca1_astra_rereview.py` now pass the author's figure role
  through the fake. A paraphrase owns its figure by role (`[False, True]`).
  `test_a_figure_is_referenced_by_its_number_or_by_a_pointer_to_the_one_selected`
  is deleted with `referenced_figures`; `test_figure_roles_are_validated_never_widened`
  replaces it. The two "old rule ... answer graph" tests became the
  documented legacy residual test.
* Whole-passage edit (`test_reader_ca1_astra_fixes.py`): a prompt that holds
  the book's solution gets `NO_CROP`. Its solution block is dropped and
  supplies no coverage. The old exception counted a dropped block wholly
  inside the statement, and that exception was F3's hole.

### Kept items

They pass after the change. They were verified failing on main `680bb9e18`
(an exported tree with these test files copied in):

* F1's regressions: words after the statement; an answer before it; an
  owned block the statement does not place; the 22 label cases.
* F4's tests (`test_reader_ca2_astra_handoff_recovery.py`) and the CA2
  handoff (`test_reader_ca2_astra_handoff.py`).
* The Astra scenario, the multi-item split, the canonical exercise naming
  a solution block, and the solution-neighbour geometry.

On main the kept tests fail: 25 failed, and 3 files error at collection
because their APIs are absent. Twenty-five tests pass on main as well; they
pin behaviour main already had.

### Spec

`ux_reader_compare_ask_v1` §15 Q10 now reads "a figure the problem uses as
input". §8.5's body ("an attached `figure` block") still describes the
pre-redesign trigger. It is left for the docs pass, because editing it takes
more than the one line allowed here.

### Algorithm-change playbook

No persisted meaning changes. The crop is a view. `figure_role` is
provenance JSON that only the view reads; no scoring, scheduling,
projection, replay or rebuild reads it. **No successor, no migration.** The
authoring prompt version moved (`mvp-0.4-...`). Its output schema gained an
optional list, and the version suffix the method-rule tests pin is kept.

### Owner questions

1. **Legacy residual.** Old single-exercise imports with an unmarked
   completed answer figure still show that figure, cold and in the free
   crop, as on main. There are two options:
   * (a) accept it: no figure-bearing legacy item has been reported, and a
     re-import fixes it;
   * (b) hold every legacy figure behind the original page in the free crop,
     and show it cold only when it precedes the statement's last text
     block. This costs availability, and possibly answerability cold.

   Recommendation: (a).
2. **Warm `NO_CROP` with a stimulus figure.** When the text gives no free
   crop, a stimulus figure shows only during a check on your own. Outside
   one, the learner opens the charged page to see it. Should the free view
   show the stimulus figure alone (no text crop, no locator) too? That needs
   a client change (crops with a notice), so it is not done here.
3. **Re-import or backfill.** Should legacy figure-bearing Reader imports
   get roles by a one-off author pass? That would be a model call per
   item, so it needs an owner OK.

### Sol verify of `89e140a2a` (job `20261027-051210-SODKXG`): three closed

Sol confirmed F1, F2, F3, F4, F5 and the CA2 aliasing fixed, and reopened
three. The design is unchanged; each fix tightens one of its rules.

1. **High: duplicate claims bypassed the global refusal.**
   * Cause: `_claimed_roles` kept the first non-stimulus claim, so
     `[unrelated, answer]` became `unrelated`. The answer claim was lost,
     and a sibling's `stimulus` then owned the answer figure.
   * Fix: every claim counts. Within an item the strongest claim stands,
     whatever the order (answer or worked, then unrelated, then stimulus).
     The global refusal set is read from every raw claim of every item
     (`_answer_figures`).
   * Tests: `test_a_duplicate_answer_claim_is_never_lost[4 orders]`,
     `test_a_sibling_never_owns_a_figure_one_item_calls_its_answer_among_duplicates[3]`.
     Fail-before on `89e140a2a`: `[unrelated, answer]` and
     `[unrelated, worked]` gave the sibling the figure cold (`'figure' == 'none'`);
     `[answer, unrelated]` already held.
2. **Medium: the solution-lead rule hid an input graph.**
   * Cause: "Solution concentration (mol/L) versus time (s)." matched the
     lexical lead on a figure's text.
   * Fix:
     - The heading test never reads a figure. A figure leaves only by its
       solution span, its solution role or its validated figure role.
     - On text, the lead must be a heading (`_ANSWER_HEADING`): "Solution"
       or "Proof", optionally numbered or enumerated, then punctuation or the
       end of the line. A word starting a sentence does not count. The same
       heading test marks a solution start for the figure-ordering rule.
   * Tests: `test_a_graph_titled_solution_concentration_shows_in_a_check_on_your_own`,
     `..._prints_with_the_problem`, `test_a_legacy_graph_..._still_shows_cold`, and
     `test_a_solution_lead_is_a_heading_not_a_word_starting_a_sentence[13 cases]`.
     Fail-before: `kind == "none"` cold, and the crop was `[["c9"]]`
     without the graph. Every existing "Solution"-led text case still drops.
3. **High: overlapping boxes could still show excluded pixels (F6).**
   The first fix (`3bbd0c538`) masked excluded areas in each crop and
   exempted containers. The Sol verify of `3bbd0c538` (job
   `20261027-052851-Bf60oF`) reopened it twice:
   * an enclosing solution, answer or worked box went unpainted (852
     answer pixels, status ok);
   * the remainder mask of figure A blanked a retained stimulus figure B
     (100% white during a check, so the problem was unanswerable).

   Replaced, per the coordinator's ruling under the owner's bar, by **one
   rule**, with no masks and no exemptions (`as_printed.shows_unsafe`):
   * **R:** the retained display areas, which are the crops. Each is a
     retained text block's box, or a retained figure's selected sub-box or
     full box.
   * **U, unsafe:** the boxes, on the problem's pages, of blocks excluded as
     a solution by book-solution span, solution role or heading; of figures
     refused as `answer` or `worked`; and the rest of a
     sub-box-selected figure's box. `_problem_only` computes U for every
     block on the problem's pages, not only the selection, and carries it
     on the origin as `unsafe_span_ids`.
   * **N:** every other non-retained block. It is neutral: a scale label
     over a graph is not ambiguity.
   * Nothing is ever painted. A crop shows its retained area whole.
   * **If any U area overlaps any R area,** the free crop is `NO_CROP`
     with the charged original page. This is the owner's fallback, and it
     fails closed if it cannot be read.
   * **During a check on your own,** retained figures still show whole, so
     the problem stays answerable. Retained text never shows during a
     check.
   * Refused figures also leave the original page's outline.
   * The renderer's `masks` parameter, `excluded_areas` and `_masks_for`
     (the container exemption) are deleted.
   * Tests (all in the redesign file):
     - `test_a_problem_inside_an_excluded_box_gets_no_free_crop[solution_span,
       solution_role, solution_heading, answer_figure, worked_figure]`:
       Codex's enclosing-box probe, giving `NO_CROP`, no crops and no
       answer pixel.
     - `test_and_a_check_on_your_own_shows_nothing_of_it`.
     - `test_a_retained_figure_under_another_figures_excluded_rest_shows_whole_in_a_check`
       (Codex's (c): B fully green) and
       `test_and_outside_a_check_the_rule_withholds_the_free_crop` (U ∩ R
       is non-empty, so `NO_CROP`).
     - `test_a_scale_label_over_a_graph_is_neutral_and_the_graph_stays`
       (the label pixels are kept), and the same during a check.
     - The earlier F6 tests (`test_f6_*`, the Astra review's inset)
       unchanged.
     - The inset probe rewritten:
       `test_an_overlapping_figure_box_over_another_figures_excluded_rest_gives_no_free_crop`
       and `test_in_a_check_on_your_own_both_figures_stay_whole`.
     - `test_a_box_overlapping_a_dropped_solution_block_gives_no_free_crop`.
     - The container-exemption unit test is deleted, together with the
       exemption.
   * Fail-before on `3bbd0c538` (11 tests):
     - the five enclosing probes showed a free crop;
     - the inset and solution-overlap cases showed a free crop;
     - B was blanked during a check;
     - the masked Figure 4 was only 79% green;
     - the scale label was painted out (0 pixels).

Residual, with its reasoning. During a check on your own, unsafe ink that
lies inside a retained figure's own box shows with that figure. Examples:
the inset probe's inset inside Figure 4's box, or a solution box drawn over
a validated-stimulus or legacy-owned graph. A check cannot open the page,
and painting would erase input the learner needs, as Sol's (c) showed. The
owner's bar ranks an unanswerable problem as unacceptable, and the free crop
still withholds in exactly these cases. A neutral block overlapping a crop
shows where it overlaps; it is not a solution by any recorded signal.

Gate for this round: `lint-imports` 36 kept, 0 broken. Targeted
`pytest -n 6` over the same 74 files: **2,041 passed, 5 skipped, 0 failed**
(3 min 13 s). The first fix's gate was 2,030 passed.

### Gate (redesign)

Targeted only. The rules followed:

* every pytest run in `systemd-run --user --scope -p MemoryMax=5G -p
  MemorySwapMax=1G`, behind `flock /tmp/learnloop-fullsuite.lock`, `-n 6`;
* every CLI run outside pytest under `env -i` with an empty HOME, CODEX_HOME
  and LEARNLOOP_CONFIG_DIR;
* no live calls: every model is a fake.

Main `9de12c2c1` (thread guard) was merged first.

* `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2`: ok.
* `uv run lint-imports --no-cache`: 36 kept, 0 broken.
* `uv run pytest -n 6` over 272 files (every test file naming as_printed,
  exercise_authoring, block_roles, import_exercise or source_exercise,
  tutor_qa, or workbench, the earlier gate's 109, the contract tests, and
  the new `test_reader_ca1_astra_redesign.py`): **10,920 passed, 8 failed,
  16 skipped, 2 xfailed** (15 min).
  * 6 failures are `test_codex_lockdown_round2/3` on the installed Codex CLI,
    which is environmental. They fail identically on the pre-redesign tip
    `073b1b4ff` (7 there).
  * 2 failures were `test_source_service_spend_envelopes` cap calibrations.
    The authoring output schema grew by about 500 bytes (figure roles), so
    the authoring reservation grew by about $0.005 at $10 per million. The
    test caps were moved as before, from $0.31 to $0.32 and from $0.28 to
    $0.29, with the same meaning: two calls fit and three do not, one import
    fits and two do not. After the move, 22 of 22 pass.
* The frontend is unchanged (the DTO shape is the same), so vitest,
  typecheck and cargo were not run. The durability lane and the DB
  reference scripts were not run either: there is no migration and no
  connection code changed.

## Gate (before the redesign)

Targeted only (owner rule 2026-10-17: the full suite runs once, in the
landing gate). Every test command in a `systemd-run --user --scope -p
MemoryMax=5G -p MemorySwapMax=1G` scope; the pytest run behind
`flock /tmp/learnloop-fullsuite.lock`.

* `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2`: ok.
* `uv run lint-imports --no-cache`: 36 kept, 0 broken.
* `uv run pytest -n 6` over the 109 files below: **2,347 passed, 3 skipped,
  0 failed** (5 min 41 s).
* `apps/learnloop-tauri`: `npm install` ok; `npm run typecheck` clean;
  `npx vitest run --maxWorkers=4` over `src/components/AsPrinted.test.tsx`,
  `src/screens/PracticeScreen.asPrinted.test.tsx`,
  `src/screens/PracticeScreen.workbench.test.tsx`,
  `src/screens/PracticeScreen.ca2OneAsk.test.tsx`: 4 files, 54 tests passed;
  `npm run frontend:build` ok.
* Not run (nothing changed there): cargo check (no `src-tauri` change), the
  durability lane (no migration, no DB or connection code), the DB reference
  scripts (no schema change).

Pytest files run:

- `tests/test_ad1_codex_rereview_fixes.py`
- `tests/test_ad1_codex_review_fixes.py`
- `tests/test_ad1_fix_round4.py`
- `tests/test_ad1_fix_round5.py`
- `tests/test_ad1_fix_round6.py`
- `tests/test_ad1_send_guard.py`
- `tests/test_ad23_contract.py`
- `tests/test_ad23_fix_r8.py`
- `tests/test_ad3_relatedness.py`
- `tests/test_adaptive_difficulty_ad1.py`
- `tests/test_ad_epoch.py`
- `tests/test_ad_protected_readings.py`
- `tests/test_architecture.py`
- `tests/test_batch3_landing.py`
- `tests/test_canonical_exercise_serialization.py`
- `tests/test_capture_desktop.py`
- `tests/test_capture_route_recovery.py`
- `tests/test_codex_output_schema.py`
- `tests/test_compare_methods.py`
- `tests/test_controller_snapshot.py`
- `tests/test_desktop_rpc_contract.py`
- `tests/test_exam_protection.py`
- `tests/test_exam_protection_review.py`
- `tests/test_exercise_arm.py`
- `tests/test_exercise_authoring.py`
- `tests/test_facet_locks_landing.py`
- `tests/test_field_signal_production_paths.py`
- `tests/test_field_workbench_signals.py`
- `tests/test_figures_show_me_codex_review.py`
- `tests/test_graph_edit_proposals.py`
- `tests/test_hint_h2b_fix3.py`
- `tests/test_hint_h2b_fix4.py`
- `tests/test_hint_h2b_rereview.py`
- `tests/test_hint_h2b_review.py`
- `tests/test_import_split_parity.py`
- `tests/test_learner_text_gaps_flow.py`
- `tests/test_library_ask_review.py`
- `tests/test_library_exercises.py`
- `tests/test_maintenance_feed.py`
- `tests/test_mobile_allowlist.py`
- `tests/test_openrouter_client.py`
- `tests/test_owner_capture_1025.py`
- `tests/test_pf_generation.py`
- `tests/test_placement_opening_probes.py`
- `tests/test_plan_first_transport_offer_grants.py`
- `tests/test_probe_pool_empty.py`
- `tests/test_question_queue.py`
- `tests/test_reader_ca1_as_printed.py`
- `tests/test_reader_ca1_astra_fixes.py`
- `tests/test_reader_ca1_codex_review.py`
- `tests/test_reader_ca2_astra_handoff.py`
- `tests/test_reader_ca2_codex_rereview.py`
- `tests/test_reader_ca2_codex_review.py`
- `tests/test_reader_ca2_fix_orchestrator.py`
- `tests/test_reader_ca2_one_ask.py`
- `tests/test_reader_compare_table.py`
- `tests/test_reader_rw2b_fix10.py`
- `tests/test_reader_rw2b_fix11.py`
- `tests/test_reader_rw2b_fix12.py`
- `tests/test_reader_rw2b_fix13.py`
- `tests/test_reader_rw2b_fix14.py`
- `tests/test_reader_rw2b_fix15.py`
- `tests/test_reader_rw2b_fix3.py`
- `tests/test_reader_rw2b_fix4.py`
- `tests/test_reader_rw2b_fix5.py`
- `tests/test_reader_rw2b_fix6.py`
- `tests/test_reader_rw2b_fix7.py`
- `tests/test_reader_rw2b_fix8.py`
- `tests/test_reader_rw2b_fix9.py`
- `tests/test_reader_rw2b_review.py`
- `tests/test_reader_rw4b_admission_idempotency.py`
- `tests/test_reader_rw4b_fix6.py`
- `tests/test_reader_workbench_rw2a.py`
- `tests/test_required_method_authority.py`
- `tests/test_required_method_items.py`
- `tests/test_reread_safety.py`
- `tests/test_router_r2a_landing.py`
- `tests/test_sidecar_append.py`
- `tests/test_sidecar_serializer_snapshot.py`
- `tests/test_sidecar_source_retrieval.py`
- `tests/test_sidecar_tutor_qa.py`
- `tests/test_source_exercise_import.py`
- `tests/test_source_exercise_rpcs.py`
- `tests/test_source_first_needs.py`
- `tests/test_source_outcome_analytics.py`
- `tests/test_structured_transport_parity.py`
- `tests/test_table_roles.py`
- `tests/test_tracked_fixture_databases.py`
- `tests/test_tutor_delivery_fixes.py`
- `tests/test_tutor_practice_request.py`
- `tests/test_tutor_qa.py`
- `tests/test_tutor_tool_requests.py`
- `tests/test_ux_phase3_today.py`
- `tests/test_workbench_assistance.py`
- `tests/test_workbench_check_kinds.py`
- `tests/test_workbench_check_map.py`
- `tests/test_workbench_check.py`
- `tests/test_workbench_chooser.py`
- `tests/test_workbench_discriminate.py`
- `tests/test_workbench_help_kill_switch.py`
- `tests/test_workbench_hint_service.py`
- `tests/test_workbench_hints.py`
- `tests/test_workbench_in_session_gaps.py`
- `tests/test_workbench_passage_draw.py`
- `tests/test_workbench_report.py`
- `tests/test_workbench_route_example.py`
- `tests/test_workbench_step_graph.py`
- `tests/test_workbench_text_gaps.py`
- `tests/test_workbench_trace.py`

## Open items

* After the redesign: the legacy residual and the warm `NO_CROP` stimulus
  figure (Redesign, owner questions 1 and 2).
* The pending (not yet bound) workbench crop (`reader.block_original_region`)
  crops the blocks the learner selected in the Reader, the book already open
  beside it; unchanged (now one crop per block).
* Closed by the redesign: a merged stem+solution block no longer withholds
  the figure during a check on your own (figures are read apart from the
  text); old-rule marks on a non-solution block outside the statement now
  give `NO_CROP` (containment); the short-answer matcher is no longer used,
  so "Exercise 12" with answer 12 crops.

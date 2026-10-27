# Astra batch fixes: Codex review (gpt-6.1-sol) and fixes

Stage `astra-batch1-fixes`, branch `fix/astra-batch1` (worktree
`learnanything-astrafix`), on top of the batch fixes in
`docs/reviews/astra-batch1-fixes.md` (main `680bb9e18`). Codex job
`20261027-034118-4yhMBC`. Four findings: two High, two Medium. All four
reproduced as failing tests before the fix and are fixed. No migration, no
schema change, no algorithm successor, no new parameter, no paid or live
model call (every model a fake).

## Review

### Findings

| id | severity | title | verdict | commit | test |
|---|---|---|---|---|---|
| F1 | High | Single-digit answers still leak through the free crop | fixed | `8cc4c7420` (+ docstring `9f66ea341`) | `tests/test_reader_ca1_astra_codex_review.py::test_words_after_the_statement_in_its_block_give_no_free_crop[m1-...-4]`, `[y1-...-Yes]`, `::test_an_owned_block_sharing_no_words_with_the_statement_gives_no_free_crop`; control `::test_a_label_before_the_statement_still_crops` |
| F2 | High | Statement-only ownership drops required stimulus figures | fixed | `8cc4c7420` | `tests/test_reader_ca1_astra_codex_review.py::test_a_statement_that_names_but_does_not_echo_its_figure_keeps_it`, `::test_a_check_on_your_own_still_shows_the_figure_the_statement_names`, `::test_a_paraphrased_statement_keeps_its_figure_for_a_check_on_your_own`, `::test_a_problem_with_no_free_crop_keeps_its_figure_for_a_check_on_your_own`; control `::test_a_paraphrase_shows_no_free_crop_of_its_figure_alone` |
| F3 | Medium | Known solution spans bypass the mixed-block safeguard | fixed | `8cc4c7420` | `tests/test_reader_ca1_astra_codex_review.py::test_a_named_solution_block_holding_part_of_the_statement_withholds_the_whole_crop` |
| F4 | Medium | A failed handoff write restores the paid Ask allowance | fixed | `841bbed51` | `tests/test_reader_ca2_astra_handoff_recovery.py` (failure injection on open and on resume, restart, unreadable handoff at ask time) |

Reproduction: before the fixes, the new CA1 file failed 8 of 10 (the two
controls passed) and the new CA2 file failed 3 of 4 (the restart test is a
happy-path guard and passed); after, all pass.

### F1 (High): an affirmative stem-only boundary

`reader/as_printed.py`: the free crop no longer rests on a negative leak
test. `_beside_statement` places a block against the statement (whole-word
runs: inside it, it inside the block, or an edge overlap; then, for an edit
that only moved spaces, the same characters without spaces) and returns the
block's words before and after the statement. `_stem_only` is true only
when the statement places the block and every other word of it comes
**before** the statement (a label, a heading). Words after the statement in
its block (the review's `Compute 2+2. The answer is 4.` with answer `4`, or
`Is 7 prime? Yes.` with `Yes`, both of which the leak matcher ignores), a
block the statement does not place (an old-rule mark on an unlabelled
solution block `The sum is 4.`), or a solution/proof lead in a later part
give `NO_CROP`, the original page still offered (one hint before Submit,
unchanged). The leak matcher still checks the words before the statement.
Figures are exempt from the text test (they are the stimulus).

The CA1 base fixture's canonical item had a prompt (`Define SVD.`)
unrelated to its blocks' text (`block e1` ...): under the affirmative rule
that is correctly no free crop. The fixture now writes the prompt as the
blocks' text, as an import does; one base test
(`test_the_practice_view_locates_the_problem_outside_a_check_and_records_nothing`)
had passed vacuously over an empty crop list (`all([])`) and now asserts a
crop. The Astra-fixes canonical test sets its prompt to its block's
statement for the same reason.

### F2 (High): the stimulus figure

`content/authoring/exercise_authoring.py`: a single-exercise import marks
the selection's figure blocks `stimulus: true` on their refs (any
statement, anchored or paraphrased), and when its statement owns any block
it also owns those figures (`_owned_spans(..., figures=...)`), so the warm
crop shows the problem with its figure as before the batch fix. A split
still gives a figure only to the item whose statement covers it (unchanged).
`reader/as_printed.py`: `PrintedOrigin.figure_span_ids` (owned or stimulus
blocks, solution blocks dropped) is what a check on your own crops figures
from, **before** the free-crop decision: a problem whose text gives no free
crop (a paraphrase, an answer in the stem's block) still shows its figure
during a cold check. A guard that cannot be read still withholds
everything. This also closes the batch fix's open item "a merged stem +
solution block also withholds a figure-only crop during a check on your
own".

### F3 (Medium): a named solution block holding statement words

`_without_solutions.solution_kind`: a block on the import's book-solution
spans or led by "Solution" is dropped only when the statement does not
place it or holds it whole (a learner's whole-passage edit that kept the
solution text). When the statement places part of itself beside other
words in that block (the review's final subquestion followed by its
answer), it is `unsure`, and an own `unsure` block withholds the whole crop
(`NO_CROP`, page offered): never a crop of the problem in part.

### F4 (Medium): the handoff commits with the open

`reader/workbench.py`: `open_session` and `resume_session` take
`draft_submission_ids` and record them (`workbench_draft_handed`, salience
only, once per key) inside their own `repository.atomic()` transaction on
every path (new, resumed, idempotent retry); `record_draft_handoff` shares
the helper. `learnloop_sidecar/handlers/workbench.py` computes the keys
(screen key, checkpoint key) before the open and passes them in; the old
post-commit `_record_handoff` that logged and swallowed a failure is gone.
A handoff that cannot be written now fails the open whole: no problem is
exposed (or reopened from abandoned) whose Reader budget would read a
fresh allowance, and there is no crash window between two commits; the
retry opens it with its handoff. `attempt_identities` no longer reads an
unreadable handoff as none: it raises, so the ask is refused before any
model call (the transcript read fails the same way, as it would on any
unreadable ledger).

### Claims, re-checked

* "The free crop never shows the solution": now affirmative (F1), and a
  solution block holding statement words is never silently dropped (F3).
* "A merged stem/solution block always yields `NO_CROP`, never a partial
  print": holds for lead, role, leak, trailing-words and named-span cases.
* "Required figure behavior remains intact": the figure is kept as the
  single exercise's stimulus independent of the statement's text (F2).
* "The handoff preserves one metered allowance across resume": the
  association is committed with the open or resume, or neither is (F4).

### Not changed / open items

* A block the statement cannot place gives no free crop (fails toward
  hiding, page offered): this includes a learner's whole-passage edit that
  changed words (not only spaces) in a block, and a pypdf-fallback block
  whose Unicode math the import transliterated to LaTeX (such blocks
  usually have no box, so no crop was possible anyway).
* Words after the statement that are not an answer (a hint in
  parentheses, the next exercise in the same block) also give no free
  crop; C10 already excluded showing another exercise.
* A split's figure belongs to the item whose statement covers it; a figure
  no sibling's statement covers stays unowned (unchanged; which exercise
  it serves is not known).
* The batch fix's other open items stand (old-rule marks on non-solution
  blocks are now caught by F1 when the statement does not place them; the
  pending workbench crop is unchanged).

### Algorithm-change playbook

No persisted meaning changes: the free crop is a read-time view rule; the
`stimulus` ref mark is new provenance metadata read only by the view; the
handoff event and its meaning are unchanged (only its transaction
boundary). No replay, rebuild, scoring, scheduling or projection reads any
of it. No successor; no table, column, fingerprint or parameter.

## Gate

Targeted only (owner rule 2026-10-17: the full suite runs once, in the
landing gate). Every test command in a `systemd-run --user --scope --quiet
-p MemoryMax=5G -p MemorySwapMax=1G` scope; the pytest run behind
`flock /tmp/learnloop-fullsuite.lock`.

* `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2`: ok.
* `uv run lint-imports --no-cache`: 36 kept, 0 broken.
* Iteration runs (pass): the four CA1 files (`test_reader_ca1_astra_codex_review.py`,
  `test_reader_ca1_astra_fixes.py`, `test_reader_ca1_as_printed.py`,
  `test_reader_ca1_codex_review.py`): **70 passed**; the two CA2 handoff files
  (`test_reader_ca2_astra_handoff.py`, `test_reader_ca2_astra_handoff_recovery.py`):
  **14 passed**.
* Targeted run, `uv run pytest -n 6` over the 118 files below (the batch fix's
  109 plus every test file naming a changed module, plus the two new files):
  **NOT FINISHED when this step had to report** (started 04:01, at 17% with 0
  failures). The landing gate must rerun it, or the full suite covers it.
* Not run (nothing changed there): vitest / npm / frontend build (no frontend
  change), cargo check (no `src-tauri` change), the durability lane (no
  migration, no DB or connection code: only a reader transaction boundary,
  which uses the existing nestable `Repository.atomic()`), the DB reference
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
- `tests/test_hint_telemetry.py`
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
- `tests/test_reader_ca1_astra_codex_review.py`
- `tests/test_reader_ca1_astra_fixes.py`
- `tests/test_reader_ca1_codex_review.py`
- `tests/test_reader_ca2_astra_handoff.py`
- `tests/test_reader_ca2_astra_handoff_recovery.py`
- `tests/test_reader_ca2_codex_rereview.py`
- `tests/test_reader_ca2_codex_review.py`
- `tests/test_reader_ca2_fix_orchestrator.py`
- `tests/test_reader_ca2_one_ask.py`
- `tests/test_reader_compare_table.py`
- `tests/test_reader_recap.py`
- `tests/test_reader_recap_review.py`
- `tests/test_reader_recap_review_r2.py`
- `tests/test_reader_rw1c_review.py`
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
- `tests/test_rw2c_fix_round3.py`
- `tests/test_sidecar_append.py`
- `tests/test_sidecar_serializer_snapshot.py`
- `tests/test_sidecar_source_retrieval.py`
- `tests/test_sidecar_tutor_qa.py`
- `tests/test_source_exercise_import.py`
- `tests/test_source_exercise_rpcs.py`
- `tests/test_source_first_needs.py`
- `tests/test_source_outcome_analytics.py`
- `tests/test_structured_transport_parity.py`
- `tests/test_success_head_cli.py`
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

## Re-review (Codex job `20261027-040307-F7FaoL`, verdict REOPENED)

The re-review confirmed F2 and F4 fixed, reopened F1 and F3, and raised two
new Highs (F5, F6). All four open findings reproduced as failing tests
before the fix (commit `727f3c3ea`) and are fixed. No migration, no schema
change, no algorithm successor, no new parameter (the label vocabulary and
the figure-reference cues are structural, not weights), no frontend or
`src-tauri` change, no paid or live model call (every model a fake).

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High (reopened) | `_stem_only` accepts arbitrary text before the statement | fixed | `727f3c3ea` | `tests/test_reader_ca1_astra_rereview.py::test_an_answer_before_the_statement_in_its_block_gives_no_free_crop`, `::test_labels_and_headings_are_labels[*]`, `::test_other_words_before_the_statement_are_not_labels[*]`; control `tests/test_reader_ca1_astra_codex_review.py::test_a_label_before_the_statement_still_crops` |
| F2 | High | stimulus figure of a single-exercise import | confirmed fixed (narrowed by F5) | `8cc4c7420` | re-review confirmed; `test_reader_ca1_astra_codex_review.py` F2 tests still pass, one renamed for F5 (below) |
| F3 | Medium (reopened) | whitespace edits still permit a partial print | fixed | `727f3c3ea` | `tests/test_reader_ca1_astra_rereview.py::test_a_solution_block_holding_part_of_the_statement_up_to_spaces_withholds_the_crop`, `::test_a_solution_block_holding_the_statement_in_its_middle_withholds_the_crop`, `::test_a_placement_starts_and_ends_where_words_do`; control `::test_a_statement_the_kept_blocks_print_whole_still_crops` |
| F4 | Medium | handoff write shares the open/resume transaction | confirmed fixed | `841bbed51` | re-review confirmed; `tests/test_reader_ca2_astra_handoff_recovery.py` passes |
| F5 | High | every selected figure becomes free stimulus | fixed | `727f3c3ea` | `tests/test_reader_ca1_astra_rereview.py::test_a_completed_answer_graph_selected_with_sketch_is_not_the_problems`, `::test_a_completed_answer_graph_is_not_shown_in_a_check_on_your_own`, `::test_an_old_rule_import_never_crops_an_answer_graph_the_statement_does_not_refer_to`, `::test_an_old_rule_import_crops_only_the_stem_beside_an_answer_graph`, `::test_a_figure_is_referenced_by_its_number_or_by_a_pointer_to_the_one_selected`; control (input diagram) `::test_a_required_input_diagram_stays_the_problems_stimulus` |
| F6 | High | retained cold-check figures lose their selected bounds | fixed | `727f3c3ea` | `tests/test_reader_ca1_astra_rereview.py::test_a_kept_figure_keeps_its_sub_box_when_the_text_gives_no_free_crop`, `::test_a_stimulus_figure_without_textual_ownership_keeps_its_sub_box`; control `::test_the_sub_box_is_kept_while_warm_too` |

Reproduction: the new file was run against the code before the fix (with a
`_is_label` shim that accepts every prefix, the rule as it stood): 17 failed,
14 passed. The behavioural failures were 9 (F1 x1, F3 x2, F5 x4, F6 x2) plus
the 8 negative label cases; the 4 behavioural controls and the positive label
cases passed. After the fix: 36 passed (the file gained 5 cases for the rules
themselves).

### F1: words before the statement must be a label

`reader/as_printed.py::_is_label`: the words a block holds before the
statement are allowed only when every one is a label word: an exercise kind
(`Exercise(s)`, `Problem(s)`, `Question(s)`, `Part`, `Task`, `Example`; `Ex.`,
`Prob.`, `No.`, `Q` only with a number after them), a number (`12.`, `3.2:`),
a letter or a roman numeral only as an enumerator (`(a)`, `b)`, `iv.`; a bare
`a` or `mix` is a word), a section/difficulty mark (`§`, `*`, `†`, `★`), or a
dash. `The answer is 4. Compute 2+2.` therefore gives `NO_CROP` (the original
page still offered), whatever the leak matcher says; the leak test still
runs over an accepted label. A bare number before the statement (`4 Compute
...`) is accepted as an exercise number, as `content.sources.exercise_statements`
already reads one.

### F3: placement without spaces, and the whole statement printed

`_placement` (replacing `_beside_statement`) compares the block and the
statement as the same characters without spaces for every case, the edge
overlaps included, and each match must start and end on a word boundary in
both texts (so a lone `4` never places itself inside `24`). The review's
named solution block `(b) Compute 3+3. We get 6.` against the statement
`... (b) Compute 3 + 3.` is now placed (an edge overlap with words after it):
`unsure`, the whole crop withheld. A second rule closes the class: the free
crop must print the whole statement (`_covers`): the parts the kept blocks
place, plus those of a dropped solution block wholly inside the statement
(the capture editor's whole-passage edit, unchanged), must leave no part of
the statement out. A solution block holding part (b) in its middle (`We get
4. (b) Compute 3+3. We get 6.`, placed by nothing) now withholds the crop
instead of printing (a) alone.

### F5: a figure is the problem's only when the statement refers to it

`ingest/block_roles.py::referenced_figures` (shared by the import and the
read): a figure selected with a problem is its own only when the statement
names its number (`Figure 3.2` in both) or points at a figure shown
(`shown`, `pictured`, `the figure`, `the diagram below`, ...) and the
selection holds exactly one figure (a pointer cannot tell two apart).
`Sketch y=x^2.` refers to nothing, so the completed graph selected with it
is neither owned nor stimulus. The import (`exercise_authoring`) marks
stimulus, and owns figures for a single item, by that rule only (a figure the
anchored statement's slice overlaps stays owned, as before F2). At read time
a Reader selection's figures (owned or stimulus, so an old-rule import that
owned every block too) are kept only when the statement refers to them or
echoes text of them that no kept text block prints; a dropped figure leaves
the free crop and the check on your own. A `canonical_exercise` is unchanged:
its blocks are the sources service's exercise region, not a selection.

One test of the previous round asserted the opposite of F5 (an unreferenced
figure beside `Compute 2+2.` kept for a check on your own); it is now
`test_reader_ca1_astra_codex_review.py::test_a_figure_the_statement_does_not_refer_to_is_not_its_stimulus`,
and the no-free-crop case with a referenced figure is covered by the F6
tests. Spec note for the landing: §15 Q10's figure-only exception now reads
"a figure the statement refers to", not "a figure the problem was imported
with".

### F6: kept figures keep their sub-box

The learner's drawn region now stays with every kept figure: in
`_selection_origin` for owned and stimulus figures alike, and in
`_without_solutions` on both the free-crop and the withheld path (it used
to clear `regions` when withholding). With selected bounds that leave an
answer inset out of the figure block, the check on your own crops the
sub-box only (the test draws the inset blue and asserts none of it).

### Gate (as run in this step)

- `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: 36 kept, 0 broken.
- targeted pytest, `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -n 6 <files>`: **1319 passed**, 0 failed (102.8 s), over:
  - changed or added: `tests/test_reader_ca1_astra_rereview.py`, `tests/test_reader_ca1_astra_codex_review.py`;
  - exercising `reader/as_printed`, `content/authoring/exercise_authoring`, `ingest/block_roles`: `tests/test_reader_ca1_as_printed.py`, `tests/test_reader_ca1_astra_fixes.py`, `tests/test_reader_ca1_codex_review.py`, `tests/test_reader_ca2_astra_handoff_recovery.py`, `tests/test_exercise_authoring.py`, `tests/test_compare_sources_keep.py`, `tests/test_document_ir.py`, `tests/test_import_split_parity.py`, `tests/test_library_exercises.py`, `tests/test_required_method_authority.py`, `tests/test_required_method_items.py`, `tests/test_source_exercise_import.py`, `tests/test_source_exercise_rpcs.py`, `tests/test_source_retrieval_rereview.py`, `tests/test_tutor_delivery_fixes.py`, `tests/test_glm_ocr.py`, `tests/test_facet_locks_landing.py`, `tests/test_codex_output_schema.py`, `tests/test_structured_transport_parity.py`, `tests/test_openrouter_client.py`;
  - contracts: `tests/test_architecture.py`, `tests/test_cli_help_snapshot.py`, `tests/test_sidecar_serializer_snapshot.py`, `tests/test_desktop_rpc_contract.py`, `tests/test_mobile_allowlist.py`, `tests/test_table_roles.py`, `tests/test_coordinated_migrations.py`, `tests/test_tracked_fixture_databases.py`.
- Not run (nothing in scope changed): durability lane (no migration or DB/connection code), npm/vitest/frontend build (no frontend change), cargo check (no `src-tauri` change), DB reference scripts (no schema change). The full suite is left to the landing gate (owner rule, 2026-10-17).

# Astra batch review 1: fixes (eaf9859ad..680bb9e18)

Stage `astra-batch1-fixes`, branch `fix/astra-batch1` from main `680bb9e18`.
Findings: one High (the as-printed crop could show the solution), one Medium
(the metered Ask budget reset across the answer box -> Work in Steps ->
Reader handoff), plus the queued CA1 polish the owner decided. No migration,
no algorithm successor, no paid or live model calls (every model a fake).

## A. High: the free crop never shows the solution

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

## Gate

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

* A merged stem+solution block also withholds a figure-only crop during a
  check on your own (the figure exception, Q10) for that problem; rare
  (needs a merged block and a figure) and fails toward hiding.
* Old-rule marks on a single-item import may still cover a non-solution
  block outside the statement (e.g. a worked example the learner selected
  along): solution blocks are filtered, those are not re-derived at read
  time.
* The pending (not yet bound) workbench crop (`reader.block_original_region`)
  crops the blocks the learner selected in the Reader, the book already open
  beside it; unchanged.
* `_holds_its_solution` reuses the tutor's short-answer matcher: an exercise
  number equal to a short numeric answer outside the statement ("Exercise 12
  ..." with answer 12) withholds the free crop (the page is still offered).

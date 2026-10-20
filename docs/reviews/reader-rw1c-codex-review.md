# Reader workbench RW1c: Codex review and fix round 1 (stage `reader-rw1c`)

Branch `reader/rw1c` in `learnanything-merge4`, base `fab576ac1`. Codex reviewed the stage through `0e8db0762`
(job `20261019-022936-oEEQfH`, read-only) and found **10 findings (3 High, 7 Medium)**. This round reproduced each
one with a test that fails on the old code, then fixed it. **None were rejected.** The fixes are in `015e02706`; the
references regenerated on top of it are committed with this record. The stage record is `docs/reviews/reader-workbench-RW1c.md`. Its §4 ("a Reader
answer's reveal handling is unchanged") and open question 5 ("no chip until the owner asks") are **superseded** by F1
and F8 below.

**Paid calls: none ($0.00).** Every model is a fake. No vault copy was opened and no manual run was made.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Workbench tutor help bypasses hint and reveal accounting | fixed | `015e02706` | `test_reader_rw1c_review.py::test_a_bound_reader_question_counts_on_its_items_submission`, `::test_the_bridge_is_scored_with_the_answer` (both failed on the old code: no item on the row, so `hint_equivalents_for_submission` was 0 and no reveal was written). Control: `::test_an_unbound_reader_question_stays_unbound` |
| F2 | High | Cold attempts still execute offer lookups | fixed | `015e02706` | `::test_a_cold_ask_offers_nothing` (old code: `coldActive` still returned a `practiceRequest`); `::test_a_server_derived_cold_administration_refuses_every_tool` (old code: tool requests were written under a server-derived cold); `::test_a_bound_reader_question_rebuilds_as_its_items_caller` (old code: a bound question rebuilt as `reading`) |
| F3 | High | Assisted-practice filtering stops before the complete tutor context | fixed | `015e02706` | `::test_item_bound_the_neighbours_and_references_are_guarded_too` (old code: the solution blocks next to the selected exercise reached the tutor); `::test_the_excerpt_guard_catches_a_short_key` (old code: `2/13` was quoted) |
| F4 | Medium | Invisible practice candidates receive exposure impressions | fixed | `015e02706` | `tutorReview.test.tsx` "F4" (old code: 3 rendered, 5 impression keys) |
| F5 | Medium | Verification failures become permanent "nothing fits" results | fixed | `015e02706` | `tutorReview.test.tsx` "F5" ×2 (old code: an `unverified: over_budget` run became *nothing … fits* with no button; an `unavailable` comparison was rendered as a comparison) |
| F6 | Medium | Collapsing an answer reruns its eager lookups | fixed | `015e02706` | `tutorReview.test.tsx` "F6", through `ReaderAskBranches` collapse and reopen (old code: two lookups and the pressed result lost) |
| F7 | Medium | "Another way" can repeat passages already shown | fixed | `015e02706` | `::test_another_way_drops_a_repeated_excerpt_and_citation` (old code: the selection quoted and cited again); `::test_another_way_excludes_what_the_inquirys_offers_showed` (old code: a passage a pressed offer showed was not excluded) |
| F8 | Medium | The specified personalization control is absent | fixed | `015e02706` | `tutorReader.test.tsx` "the personalized chip …" through `ReaderScreen` (old code: no chip, nothing sent), and the control "without the tutor looking things up there is no chip"; the server side (off: no gaps in the query, no work in context, no bridge) is the existing `test_reader_tutor_retrieval.py::test_personalized_queries_carry_the_open_gaps_and_the_bridge_sees_the_work` |
| F9 | Medium | Retrieved excerpts lack usable source navigation | fixed | `015e02706` | `tutorReview.test.tsx` "F9" ×2 (old code: no button on the excerpt; another book's citation was plain text) |
| F10 | Medium | Tutor comparisons discard the actual comparison | fixed | `015e02706` | `tutorReview.test.tsx` "F10" (old code: only contributions were shown; the relations, the unchecked source and the missing perspective were dropped) |

## What each fix does

* **F1.** `reader.ask` derives the binding on the server (`handlers/reader_tutor._accounting_binding`). The item
  comes from the named workbench session (`library_ask.reader_caller`, never the client's word). The practice session
  is resolved the way the workbench's own question count resolves it (`handlers/workbench._question_hints`: the
  session's `practice_session_id` while it is open, else the most recent open session). `ReaderTutorRequest` carries
  both (`bound_item`, `practice_session_id`) for every policy, including cold. `tutor_qa.ask_question` stores them on
  the question row (`practice_item_id`, `session_id`, the item's presented contract), so the submit's existing fold
  (`hint_equivalents_for_submission`) counts a hint-equivalent question type as it counts a practice-context one. The
  key overlap is measured on everything the answer shows (`reader_modes.displayed_text`: explanation, excerpt and
  bridge) and recorded once as the existing `tutor_answer` reveal (`basis = tutor_qa:reader`). The cited passages and
  the excerpt are a `source_review` reveal (`tutor_qa:reader:workbench_cited_source_span`), as T6's cited retrieved
  spans already are. No double count: a Reader Ask is not a `help_assists` row, and when the client's cold path already
  records the question as a hint on the same item (`_record_cold_hint_equivalent`), no binding is made. The fields and
  their meaning are the existing ones, so no successor is needed (RW1c is not on `main`). Edge: with no open practice
  session the row has no session, so the submit's session-scoped count does not see it. This is the workbench's own
  rule for questions, and the reveal is recorded either way.
* **F2.** `ReaderTutorRequest.policy` keeps the derived policy apart from the exclusion item. The new
  `handlers/reader_tutor.tools_refused` refuses the tool handler, the practice request, the fallback request and
  every offer when the client says cold (`coldActive`), when the server derives `cold_attempt`, or when the question is
  bound. During cold, `tutor_offers` is absent too. With both RW1c switches off, the base wire is kept (the
  switch-off golden still passes). `instructional.policy.caller_for_question_event` rebuilds a Reader question stored
  on an item as that item's practice caller, so anything later rebuilt from it reads as `assisted_practice` or
  `cold_attempt`, never `reading`.
* **F3.** `source_retrieval.reader_tutor.ItemBoundGuard` (injected as `ReaderTutorRequest.context_guard`; the tutor
  package still never imports retrieval) applies T6's item-bound rules to every span the tutor is given. Those are the
  selection, its neighbours, the blocks they cite and the retrieved passages after hydration. The rules: the item's
  linked passages (`item_exclusions`), solution blocks by lead or effective role (`block_roles`), exercise blocks other
  than the learner's own selection, and `span_leaks_expected`. Drops go on the delivery receipt (`item_bound_withheld`).
  `_admitted` uses the same guard. `verify_excerpt` uses `span_leaks_expected` on the quote and on its passage.
* **F4.** A practice lookup keeps only the proposals it renders (`MAX_SHOWN = 3`), and the impression names exactly
  those.
* **F5.** A result counts as *found* or *nothing fits* only when its call succeeded (`ok`). An `unverified: …`
  passage run, a practice result that is not `ok` with no items, and a comparison that is `unavailable`, `over_budget`,
  `cancelled`, `failed` or route-skipped are *unchecked*. Unchecked keeps its button, runs again on the press, and,
  still unchecked, says *Your books couldn't be checked just now (reason) — press to try again.* Nothing is recorded as
  shown.
* **F6.** The lookups, presses, impressions and the `tutor_offer_shown` log live in an exchange-scoped store
  (`createTutorOfferStore`, one per `ReaderScreen`, passed as `tutor.offerStore`). A collapse unmounts the component,
  not the state: in-flight lookups settle into the store, a remount runs nothing, and only a failed or unchecked lookup
  runs again, on its press.
* **F7.** The shown set for *another way* is the inquiry's exchanges (selections, citations, excerpts, retrieved
  passages) plus the exposure rows its offers wrote (`offer_shown_span_keys`: `source_tool_call` exposures of the
  tutor's requests from these questions, and the excerpts' own rows). It excludes from retrieval as before, and
  `finalize` now enforces it on what is displayed. An excerpt of a shown passage is dropped (*this inquiry has already
  shown that passage*), and citations of shown passages are not shown again (counted as `repeated_citations`). The
  passages stay in the tutor's context.
* **F8.** The Ask composer shows a *personalized ● / ○* chip while the tutor looks things up. It starts at
  `library_ask.personalized_default` (via the contract's `personalizedDefault`), and its value is sent as
  `personalized` with every question and follow-up, *another way* and *that didn't help* included. With retrieval
  off there is no chip and nothing is sent.
* **F9.** The excerpt has *open in your book ▸*, and a citation from another extraction carries its `source_id`
  (added in `finalize` from the retrieved span) and is a button. Both go through `onOpenPassage`. This source
  peeks at the passage; another book opens through RW4a's `openLibraryHit` detour, with the return stack, so Alt+←
  comes back.
* **F10.** `compareTableFromRun` maps the tool's comparison into the Reader's own `CompareTable` (the
  `library_ask.compare_table` mapping). *Contributes*, *assumes* (`different_assumptions`) and *differs from the
  others* (every other relation) are shown, plus the unchecked sources as *possible match, not checked*, *too few
  sources*, and the missing perspectives as *not covered by your books: …*.

Also corrected: the `[reader_tutor]` comments in `config/schema.py`, `config/template.py` and
`params/parameter_registry.py` now describe the binding (Codex's note that "shown answers reach attempts through
existing `tutor_answer` reveals" did not hold).

## Gate (fix round 1)

Run in the worktree with `TMPDIR=fixtures-local/tmp`, after `uv sync --extra dev --extra mobile` and
`uv pip install pypdfium2` (5.14.0). Targeted only (owner rule 2026-10-17).

| step | result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | 28 kept, 0 broken |
| fail-before, Python: `git checkout 0e8db0762 -- src`, then `uv run pytest -n auto tests/test_reader_rw1c_review.py` | 9 failed, 2 passed (the two passes are controls that hold on both trees: `test_an_unbound_reader_question_stays_unbound` and `test_another_way_shown_set_reaches_the_request`); `src` restored to `HEAD` |
| fail-before, frontend: the seven changed non-test sources under `apps/learnloop-tauri/src` checked out at `0e8db0762`, then `npx vitest run src/screens/reader/tutorReview.test.tsx src/screens/reader/tutorReader.test.tsx` | 8 failed, 3 passed (F4, F5 ×2, F6, F9 ×2, F10, F8 failed; the 3 passes are pre-existing tests); sources restored to `HEAD` |
| targeted pytest, `uv run pytest -n auto` over 53 files (below) | **915 passed** |
| `npm install`; `npm run typecheck` | ok, 0 errors |
| `npx vitest run src/screens/reader src/screens/ReaderScreen src/app/App.wrapUpSkim.test.tsx src/screens/attentionBudget.test.tsx src/screens/workbench/switchOff.test.tsx` | **407 passed over 55 files** |
| `npm run frontend:build` | built |
| `db_validate_reference.py` | 0 errors (head 213; no schema change, no migration) |
| `module_validate.py`; `validate_vault.py` | 508/508 notes, links resolved; vault validation passed (1130 notes) |
| `desktop_validate.py` | fails on `apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticBook.ts` ("unclassified desktop source"): that file is on the base (`b1087be0a`, an ancestor of `fab576ac1`) and untouched by RW1c, so it is out of this stage's scope (for the landing gate) |

Not run, by the owner rule: the full suite, the whole durability lane and the whole vitest run (landing gate). No
migration and no DB/connection change, so no durability tests; nothing under `src-tauri`, so no `cargo check`. The
config template's `.pyc` was cleared before the run; the change to `config/template.py` is a comment, so no defaults
snapshot moved.

Pytest files run (53): `test_reader_rw1c_review.py`, `test_reader_tutor_retrieval.py`, `test_reader_tutor_offers.py`,
`test_reader_tutor_switch_off.py`, `test_reader_intent.py`, `test_reader_inquiry_kill_switch.py`,
`test_keep_local_retired.py`, `test_method_explicit_landing.py`, `test_reader_active_reading.py`,
`test_reader_branches.py`, `test_reader_cues.py`, `test_reader_inquiry_status.py`, `test_reader_reconnect.py`,
`test_reader_report.py`, `test_reading_hardening_landing.py`, `test_rw4_kill_switches.py`, `test_sidecar_reader.py`,
`test_sidecar_reader_p3.py`, `test_ux_phase1_landing.py`, `test_retrieval_interventions_write_points.py`,
`test_tool_dispatch_policy.py`, `test_tool_results_withhold_answers.py`, `test_tutor_practice_request.py`,
`test_reader_find_sources_callers.py`, `test_find_sources_intents.py`, `test_library_ask.py`,
`test_library_ask_review.py`, `test_tutor_qa.py`, `test_reader_dialogue.py`, `test_reveal_ledger.py`,
`test_dialogue_causal_join.py`, `test_question_context.py`, `test_tutor_citations.py`, `test_tutor_delivery_fixes.py`,
`test_tutor_tool_requests.py`, `test_source_retrieval_tutor.py`, `test_source_retrieval_guards.py`,
`test_sidecar_source_retrieval.py`, `test_exam_protection.py`, `test_exam_protection_review.py`,
`test_reader_rw1b_review.py`, `test_reader_rw2b_review.py`, `test_architecture.py`, `test_cli_help_snapshot.py`,
`test_sidecar_serializer_snapshot.py`, `test_desktop_rpc_contract.py`, `test_mobile_allowlist.py`,
`test_table_roles.py`, `test_coordinated_migrations.py`, `test_tracked_fixture_databases.py`,
`test_sqlite_file_copies.py`, `test_config_refactor.py`, `test_registry_audit.py` (all under `tests/`).

Vitest files run (55): every `*.test.ts(x)` in `src/screens/reader/` (35, including `tutorReview.test.tsx`,
`tutorReader.test.tsx`, `TutorOffers.test.tsx`, `TutorAnswer.test.tsx`, `tutorSwitchOff.test.tsx`), the 17
`src/screens/ReaderScreen.*.test.tsx`, `src/app/App.wrapUpSkim.test.tsx`, `src/screens/attentionBudget.test.tsx` and
`src/screens/workbench/switchOff.test.tsx`.

## Re-review (fix round 2)

Codex re-reviewed fix round 1 (`015e02706`; job `20261019-043710-eeEcM1`, read-only). Verdict **REOPENED**. F1
and F2 (High) were reopened, F3 (High) was confirmed fixed, and one new finding was raised, F11 (Medium). Each
reopened or new finding was reproduced with a test that fails on the round-1 code, then fixed. **None were
rejected.** The fixes are in `6ab56047b`. The references regenerated on top of it are committed with this record.

**Paid calls: none ($0.00).** Every model is a fake. No vault copy was opened, and no manual run was made.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 (reopened) | High | The cold de-duplication path drops a bound question's reveals | fixed | `6ab56047b` | `test_reader_rw1c_review.py::test_a_cold_bound_question_keeps_its_reveals_and_counts_one_hint`. Old code: `practice_item_id` was None and no `tutor_answer` reveal was written |
| F2 (reopened) | High | A cold question rebuilds as `reading`; with retrieval off, server cold is not derived | fixed | `6ab56047b` | `::test_an_explicitly_cold_question_rebuilds_cold`. Old code: the caller rebuilt as `reading`, and `find_sources` under the question's ref was not cold. `::test_a_server_derived_cold_refuses_tools_whatever_the_retrieval_switch[False]`. Old code: a `practiceRequest` and `toolRequests` were returned. `::test_retrieval_off_a_bound_question_offers_nothing_and_rebuilds_as_its_item`. Old code: tools ran, and the caller rebuilt as `reading`. The `[True]` case is a control that passes on both trees |
| F3 | High | Assisted-practice filtering stops before the complete tutor context | confirmed fixed by Codex (round 1, `015e02706`) | — | no change |
| F11 | Medium | A displayed excerpt is debited twice | fixed | `6ab56047b` | `::test_a_displayed_excerpt_is_debited_once`. The excerpt exposes 0.286 of the key. Old code wrote two reveal rows summing to 0.571, which crosses the 0.35 auto-prime threshold. Now one row of 0.286 is written and `reveal_total_for_submission` stays below 0.35 |

### What each fix does

* **F1.** `handlers/reader_tutor._accounting_binding` keeps the binding when the client's cold path names an
  attempt on the same item. The bound question is still stored on the item and the practice session, so its
  `tutor_answer` and `source_review` reveals are written. The new field
  `ReaderTutorRequest.hint_counted_elsewhere` marks the question. `tutor_qa.ask_question` then leaves the bound
  row's `hint_equivalent` false, because the cold path's practice row
  (`reader_dialogue._record_cold_hint_equivalent`, unconditionally hint-equivalent under L6) already counts the
  hint. The submit's `hint_equivalents_for_submission` therefore sees exactly 1.
* **F2.** `handlers/reader_tutor.restriction` derives a `ReaderRestriction` (caller, policy, bound item, client
  cold) on the server for every `reader.ask` while either RW1c switch is on. It no longer depends on
  `retrieval_enabled`. `tools_refused(restriction)` refuses tools, the practice request, the fallback request and
  the offers when the question is cold (the client's flag, or the server's derivation for the bound item) or bound.
  `build_request` reuses the same caller and policy. The restriction is stored on the question as it lands
  (`source_context.reader_caller`: policy, cold, item, derived_from), through a new `reader_caller` argument on
  `reader_dialogue.ask` and `tutor_qa.ask_question`. `instructional.policy.caller_for_question_event` reads it
  back, and it also reads the lookup's own `reader_tutor.retrieval.policy`. A stored cold stays cold whatever
  today's status, and a stored item rebuilds as that item's practice. Source-service RPCs that rebuild the caller
  (`find_sources`, `find_practice`, tool requests, interventions) are therefore never wider than the question.
  With both switches off nothing is derived or stored. Only the client's cold flag counts, as on the base, so the
  switch-off golden is unchanged. This is deliberate: the kill switches restore the base byte for byte.
* **F11.** For a bound item, the `tutor_answer` overlap is measured on the explanation and the bridge only
  (`reader_modes.displayed_text(..., excerpt=False)`). The excerpt is debited once, in the `source_review` entry
  with the passages the answer opens: the maximum of its passage and its quote, together with the citations. Each
  displayed component is counted once.

### Gate (fix round 2)

All steps ran in the worktree with `TMPDIR=fixtures-local/tmp`. Only targeted tests were run (owner rule
2026-10-17).

| step | result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | 28 kept, 0 broken |
| fail-before: the 6 new cases on the round-1 code (`8ca83b080`), before the fix | 5 failed, 1 passed (the `[True]` control). The F11 case first failed for an unrelated reason (its question retrieved no passage), so it was switched to the root question. It then failed on the double debit (0.571 against 0.286) |
| targeted pytest, `uv run pytest -n auto` over 114 files (list below) | **2,777 passed, 2 xfailed** |
| targeted pytest, `uv run pytest -n auto` over `test_reader_rw2b_review.py`, `test_keep_local_retired.py`, `test_registry_audit.py`, `test_reader_tutor_offers.py`, `test_config_refactor.py` and the 14 `test_workbench*.py` | **229 passed** |
| `uv run pytest -n auto` over `test_reader_rw1c_review.py`, `test_reader_tutor_retrieval.py`, `test_reader_tutor_offers.py`, `test_reader_tutor_switch_off.py` (after the fix) | **54 passed** |
| `db_generate_reference.py`, then `db_validate_reference.py` | 0 errors (head 213). Before the regeneration, 8 configuration line citations into the changed files were stale |
| `module_validate.py`; `validate_vault.py` | 508/508 notes; links resolved; vault validation passed (1130 notes) |
| `git diff --check` | clean |

Not run, by the owner rule: the full suite, the whole durability lane and the whole vitest run. Those belong to the
landing gate. Other steps were skipped because nothing triggered them:

* No migration and no DB/connection change, so no durability tests.
* No frontend change, so no npm or vitest run.
* Nothing under `src-tauri`, so no `cargo check`.
* No configuration key change, so no defaults snapshot.

`module_generate.py` stops on missing package descriptions that predate this stage, and it wrote nothing.

Pytest files in the 114-file run: `test_ad1_fix_round4.py`, `test_ad1_reading_opportunities.py`, `test_ai_config.py`, `test_assumed_known.py`, `test_capture_desktop.py`, `test_capture_route_recovery.py`, `test_causal_p2_acceptance.py`, `test_chatgpt_plan_provider.py`, `test_chatgpt_plan_workspace.py`, `test_codex_output_schema.py`, `test_coldness_receipt.py`, `test_config_refactor.py`, `test_contamination_report.py`, `test_daily_loop_reader_authored_practice.py`, `test_daily_loop_reader_retire.py`, `test_daily_loop_reference_adoption.py`, `test_daily_plan_composition.py`, `test_diagnosis_input_provenance_landing.py`, `test_diagnosis_input_provenance.py`, `test_dialogue_causal_join.py`, `test_embedding_route_isolation.py`, `test_exam_protection.py`, `test_exam_protection_review.py`, `test_facet_locks_landing.py`, `test_family_memory_projection.py`, `test_field_signal_production_paths.py`, `test_find_sources_intents.py`, `test_hint_h2a_review_round2.py`, `test_integration_daily_loop_field.py`, `test_judge_routes.py`, `test_learner_text_gaps_composition.py`, `test_learner_text_gaps_flow.py`, `test_learner_text_gaps.py`, `test_learner_text_gaps_review.py`, `test_library_ask.py`, `test_library_ask_review.py`, `test_method_explicit_landing.py`, `test_mobile_allowlist.py`, `test_model_usage_report.py`, `test_output_budget.py`, `test_p2_leakage_suite.py`, `test_p3_journeys.py`, `test_pinned_span_bridge.py`, `test_placement_opening_probes.py`, `test_placement_signals.py`, `test_practice_availability.py`, `test_question_context.py`, `test_question_promotions.py`, `test_question_signal.py`, `test_quick_check.py`, `test_reader_active_reading.py`, `test_reader_activity.py`, `test_reader_branches.py`, `test_reader_cues.py`, `test_reader_dialogue.py`, `test_reader_find_sources_callers.py`, `test_reader_guidance.py`, `test_reader_inquiry_kill_switch.py`, `test_reader_inquiry_status.py`, `test_reader_intent.py`, `test_reader_observation_records.py`, `test_reader_passage_check.py`, `test_reader_recap.py`, `test_reader_recap_review.py`, `test_reader_recap_review_r2.py`, `test_reader_reconnect.py`, `test_reader_report.py`, `test_reader_rw1b_review.py`, `test_reader_rw1c_review.py`, `test_reader_tutor_retrieval.py`, `test_reader_tutor_switch_off.py`, `test_reader_wrap_up.py`, `test_reading_hardening_landing.py`, `test_retrieval_interventions_write_points.py`, `test_reveal_ledger.py`, `test_rw4_kill_switches.py`, `test_serve_eligibility.py`, `test_serve_eligibility_review.py`, `test_sidecar_reader_p3.py`, `test_sidecar_reader.py`, `test_sidecar_serializer_snapshot.py`, `test_sidecar_source_retrieval.py`, `test_sidecar_teach_back.py`, `test_source_retrieval_followup.py`, `test_source_retrieval_guards.py`, `test_source_retrieval_rereview_cost.py`, `test_source_retrieval_rereview.py`, `test_source_retrieval_search.py`, `test_source_retrieval_tutor.py`, `test_source_service_spend_envelopes.py`, `test_sources_merge_composition.py`, `test_structured_transport_parity.py`, `test_stuck_prompt.py`, `test_tool_dispatch_policy.py`, `test_tool_results_withhold_answers.py`, `test_tutor_citations.py`, `test_tutor_delivery_fixes.py`, `test_tutor_practice_request.py`, `test_tutor_promotion_w2.py`, `test_tutor_qa.py`, `test_tutor_tool_requests.py`, `test_ux_phase1_connect_ai.py`, `test_ux_phase1_landing.py`, `test_ux_phase1_usability_round1.py`, `test_ux_phase4_feedback.py`, `test_ux_phase4_landing.py`, `test_valuation_calibration_fields.py`, `test_architecture.py`, `test_desktop_rpc_contract.py`,
`test_coordinated_migrations.py`, `test_tracked_fixture_databases.py`, `test_table_roles.py`,
`test_sqlite_file_copies.py`, `test_cli_help_snapshot.py` (all under `tests/`). The 107 listed first are every
test file that names `caller_for_question_event`, `instructional.policy`, `reader_modes`, `reader_dialogue`,
`reader.ask`, the reader handlers, `displayed_text`, `tutor_qa`, `reveal_ledger` or `hint_equivalents_for`.

## Fix round 3 (orchestrator)

Codex's final verify of fix round 2 (`6ab56047b`; job `20261019-050055-6iISEz`, read-only) confirmed F2, F3 and
F11 fixed and **reopened F1**. The orchestrator ruled on the fix, and this round applies it. The fix is in
`607bda02b`. The references regenerated on top of it are committed with this record.

**Paid calls: none ($0.00).** Every model is a fake. No vault copy was opened, and no manual run was made.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 (reopened twice) | High | A cold attempt in another practice session takes a bound question's hint out of its own session | fixed | `607bda02b` | `test_reader_rw1c_review.py::test_a_hint_shown_in_the_bound_session_counts_there_once[other_session]` and `[null_session]`. Old code: `hint_equivalents_for_submission(I, B)` and `hint_equivalents_for_attempt` for the later B attempt were both **0**. Controls that pass on both trees: `[no_attempt]` (`coldAttemptId` null, so no replacement row is written) and `::test_a_same_session_cold_hint_still_counts_once` (1, not 2) |
| F2 | High | A cold question rebuilds as `reading`; with retrieval off, server cold is not derived | confirmed fixed by Codex (round 2, `6ab56047b`) | — | no change |
| F3 | High | Assisted-practice filtering stops before the complete tutor context | confirmed fixed by Codex (round 1, `015e02706`) | — | no change |
| F11 | Medium | A displayed excerpt is debited twice | confirmed fixed by Codex (round 2, `6ab56047b`) | — | no change |

**The defect.** Round 2's `handlers/reader_tutor._accounting_binding` set `hint_counted_elsewhere` because the cold
attempt was on the same item. It did not check the session. The cold path's replacement row
(`reader_dialogue._record_cold_hint_equivalent`) is written on the cold attempt's own (item, session). If that attempt
belongs to another practice session A, or to no session, while the workbench is bound to session B, the bound
question's `hint_equivalent` was false and the only hint row was outside B. B's submission therefore counted 0, while
the same-session control counted 1.

**The ruling and the fix.**

* `_accounting_binding` now resolves the accounting session first. That is the workbench session's
  `practice_session_id` while it is open, else the most recent open session, as before.
* It then marks the hint counted elsewhere only when the replacement row counts in the same submission window as the
  bound question. Three things must hold: the cold attempt resolves (the cold path writes its row only for an attempt
  it can fetch), the attempt is on the bound item, and the attempt's `session_id` equals the resolved session.
  `count_hint_equivalent_question_events` filters on the item and the session. Its window start is the item's latest
  prior attempt, so two rows on the same item and session share the window.
* In every other case the bound question keeps `hint_equivalent = true` in its own session B. That includes a cold
  attempt in another session, one in no session, an unresolvable attempt and a null `coldAttemptId`. A hint shown
  in B counts in B's next submission exactly once. The cold row still counts in A, which is the cold path's own L6
  accounting and is unchanged.
* The same-session case is unchanged. The bound question leaves the hint to the cold row, so B counts 1, not 2.
* The comments on `ReaderTutorRequest.hint_counted_elsewhere` (`tutor/reader_modes.py`) and on the flag in
  `tutor_qa.ask_question` now name the same-session condition.

**Reading the verify's "or null".** The verify reproduced the bug with the cold attempt's session null. A null
`coldAttemptId` writes no replacement row, and round 2 already kept the hint in that case. Both cases are tested:
the null-session attempt fails before the fix, and the null `coldAttemptId` is a control.

### Gate (fix round 3)

All steps ran in the worktree with `TMPDIR=fixtures-local/tmp`. Only targeted tests were run (owner rule
2026-10-17).

| step | result |
|---|---|
| fail-before: the 4 new cases on `b3a1a4090` (`git archive` of `src` and `migrations` into `fixtures-local/rw1c-r3-base`, run with this branch's tests and `-o pythonpath=fixtures-local/rw1c-r3-base/src`) | **2 failed, 2 passed**. `[other_session]` and `[null_session]` failed with `hint_equivalents_for_submission(I, B)` 0 against 1. A probe without that assertion showed `hint_equivalents_for_attempt` 0 against 1 too. The `[no_attempt]` control and the same-session control passed |
| `uv run lint-imports --no-cache` | 28 kept, 0 broken |
| targeted pytest, `uv run pytest -n auto` over 17 files (list below) | **317 passed** |
| `uv run pytest -n auto tests/test_workbench*.py` (14 files) | **124 passed** |
| `db_generate_reference.py`, then `db_validate_reference.py` | 0 errors (head 213). Before the regeneration, 2 configuration line citations into the changed files were stale (`tutor_qa.py`, `reader_tutor.py`) |
| `module_validate.py`; `validate_vault.py` | 508/508 notes; links resolved; vault validation passed (1130 notes) |
| `git diff --check` | clean |

Pytest files in the 17-file run: `test_architecture.py`, `test_hint_h2a_review_round2.py`,
`test_hint_h2a_review_round3.py`, `test_reader_dialogue.py`, `test_reader_rw1c_review.py`,
`test_reader_rw2b_fix10.py`, `test_reader_rw2b_fix11.py`, `test_reader_rw2b_fix12.py`, `test_reader_rw2b_fix4.py`,
`test_reader_rw2b_review.py`, `test_reader_tutor_offers.py`, `test_reader_tutor_retrieval.py`,
`test_reader_tutor_switch_off.py`, `test_reader_workbench_rw2a.py`, `test_reveal_ledger.py`, `test_tutor_qa.py`,
`test_workbench_assistance.py` (all under `tests/`). This is every `test_reader_tutor_*`, `test_reader_rw1c*`,
`test_tutor_qa*`, `test_reader_workbench*` and `test_workbench_assistance` file, `test_architecture.py`, and every
test file that names `hint_equivalents_for`, `count_hint_equivalent_question_events` or `hint_fold`.

Not run, by the owner rule: the full suite, the whole durability lane and the whole vitest run. Those belong to the
landing gate. Nothing triggered the other steps: no migration, no DB or connection change, no frontend change, nothing
under `src-tauri` and no configuration key change.

## Fix round 4 (orchestrator)

Codex's whole-stage verify of `fab576ac1..eaaad1e51` (job `20261019-100708-x0kXEm`, read-only) confirmed several things:

* the five session cases from round 3;
* the reveal split and the RW2b fold integration;
* held-out filtering, offers, routes, caps and configuration;
* both golden prompts, which were byte-identical.

It found **2 High and 2 Medium** defects. The orchestrator ruled on each, and this round applies the rulings. The fixes
are in `823242a36`. The references regenerated on top of it are committed with this record. **None were rejected.**

**Paid calls: none ($0.00).** Every model is a fake. No vault copy was opened, and no manual run was made.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 (round 4) | High | A bound hint is lost when the practice session changes or does not yet exist | fixed | `823242a36` | `test_reader_rw1c_review.py::test_a_bound_hint_asked_before_any_practice_session_counts_once`, `::test_a_bound_hint_asked_in_an_ended_session_counts_in_the_next`, `::test_a_cold_bound_hint_survives_a_session_change_once`. Old code: C's submission counted **0**. Controls: `::test_an_unbound_reader_question_still_counts_nowhere`, and the later attempt counts 0 inside the ended-session case |
| F2 (round 4) | High | A cold-bound request turns the item's guards off | fixed | `823242a36` | `::test_a_cold_bound_question_keeps_the_items_guards[client]` and `[server]`. Old code: the solution "The required probability is 2/13." reached the tutor and was shown as the excerpt. The unbound control in the same test shows it |
| F3 (round 4) | Medium | The desktop drops the binding when only offers are on | fixed | `823242a36` | `apps/learnloop-tauri/src/screens/reader/tutorBoundAsk.test.tsx` (old screen: no `workbenchSessionId`). Its backend half replays the shared fixture's request through the handler: `::test_the_desktops_offers_only_bound_ask_refuses_tools_when_cold` |
| F4 (round 4) | Medium | "Another way" repeats passages in the sources-service fallback | fixed | `823242a36` | `::test_another_way_in_the_fallback_repeats_nothing`. Old code: with verification unavailable, the shown selection was quoted and cited again |

### What each fix does

* **F1.** Accounting is no longer keyed on practice sessions. A bound Reader question counts in the item's window,
  as the ruling requires:
  * The window holds every question on the item asked after the item's last attempt, in any practice session or in
    none.
  * Whichever attempt of the item commits next counts it once. After that the window moves past it, so nothing new is
    stored and no migration is needed.
  * The rule lives in `Repository.count_hint_equivalent_question_events`. A hint-equivalent row whose context is in
    `ITEM_WINDOW_QUESTION_CONTEXTS` (`("reader",)`) counts whatever its `session_id`.
  * Only RW1c's server-derived binding writes a Reader row with an item. An unbound Reader question has no item, so it
    still counts nowhere, as before.
  * Every consumer reads this one query: the submit's `hint_equivalents_for_submission`, the post-hoc
    `hint_equivalents_for_attempt` and the workbench's "help used" line. With no practice session open, the line now
    counts the item-window rows (`item_window_only`), because the submit opens its own session. Before, the line
    returned 0 there.
* **F1, the cold row.** Round 3's dedup made the cold path's practice row the one that counts. That row counts only in
  its attempt's session, so under the item window it would lose the hint after a session change, or count it twice in
  that session. The ruling's "no double count" is kept by moving the count onto the bound question:
  * When the client's cold path names an attempt on the bound item, `_accounting_binding` sets
    `ReaderTutorRequest.carries_cold_hint`. The session is no longer compared.
  * `tutor_qa.ask_question` then marks the bound row hint-equivalent whatever its type. Under L6 a cold Ask is a hint.
  * `reader_dialogue._record_cold_hint_equivalent` still writes the cold row as the link to the cold attempt, but with
    its flag off, because the question row already counts on the same item.
  * Exactly one row counts in every arrangement. The same-session control is still 1, and the other-session case
    never reaches 2 in A.
  * One side effect: the learner field's `practice_assistance` signal read the cold row's flag, so a cold Ask on a bound
    item no longer emits that signal. This happens only on that RW1c path, which exists only on this branch.
* **F2.** In `build_request` the guarded item is the bound item whatever the policy. That gives the `ItemBoundGuard`
  over the whole delivered context and the excerpt's expected-answer check (`ReaderTutorRequest.item`). During a cold
  administration retrieval still adds nothing (`ReaderLookup`: `cold_attempt`). Tools, the practice request and the
  offers are still refused, separately, by `tools_refused`.
* **F3.** `ReaderScreen` sets `askWorkbenchSessionRef` whenever `readerTutor` is in the contract, which is while
  either switch is on. Before, it was set only while retrieval was on. A shared fixture,
  `apps/learnloop-tauri/src/fixtures/readerBoundOffersOnlyAsk.json`, links the two halves of the regression. The
  vitest checks that the desktop's request has exactly the fixture's keys, binding included, and that nothing eager
  runs. The pytest replays those keys through `reader.ask` under a server-derived cold administration. It asserts that
  the answer carries no tool requests, no practice request and no offers, and that no tool call is written. Its
  control, the old desktop's unbound request, runs tools.
* **F4.** The request keeps the requested intent, which is the presentation's. `finalize` therefore drops a shown
  excerpt or citation in the fallback too. Only the lookup's retrieval intent falls back to `explain`
  (`ReaderLookup.__call__`, unchanged). With the service off, the wire's `tutor.intent` for "another way" is now
  `alternative`, while `tutor.retrieval.intent` stays `explain`. `test_reader_tutor_retrieval.py::
  test_with_the_service_absent_the_base_find_sources_serves_explain` pinned the old presentation value and was updated.

### Gate (fix round 4)

All steps ran in the worktree with `TMPDIR=fixtures-local/tmp`. Only targeted tests were run (owner rule
2026-10-17).

| step | result |
|---|---|
| backend fail-before on `eaaad1e51` (`git archive` of `src` and `migrations` into `fixtures-local/rw1c-r4-base`, run with this branch's tests and `-o pythonpath=fixtures-local/rw1c-r4-base/src`) | `test_reader_rw1c_review.py`: **9 failed, 20 passed** (detail below the table) |
| frontend fail-before (`eaaad1e51`'s `apps/learnloop-tauri` extracted to the scratchpad, with the new test and fixture copied in and `node_modules` linked) | `tutorBoundAsk.test.tsx`: **1 failed, 1 passed**. The offers-only case failed (`workbenchSessionId` undefined); the switch-off control passed |
| `uv run lint-imports --no-cache` | 28 kept, 0 broken |
| targeted pytest, `uv run pytest -n auto` over the round-3 17-file list | **325 passed** |
| `uv run pytest -n auto tests/test_workbench*.py` (14 files) | **124 passed** |
| vitest, `src/screens/reader/` and the `ReaderScreen.*.test.tsx` files | **398 passed** (53 files, including the 6 reader tutor files) |
| `npm run typecheck` | clean |
| `db_generate_reference.py`, then `db_validate_reference.py` | 0 errors (head 213). Before the regeneration, 2 configuration line citations into the changed files were stale |
| `module_validate.py`; `validate_vault.py` | 508/508 notes; links resolved; vault validation passed (1130 notes) |
| `git diff --check` | clean |

The backend fail-before covers 11 cases:

* **6 new cases failed:** the before-any-session, ended-session and cold-survives cases (each 0 against 1), both guard
  cases and the fallback case.
* **3 updated round-3 cases failed:** they now assert the new carrier, which is the bound row's flag on and the cold
  row's off. Their counts were 1 on both trees.
* **2 new cases passed:** the unbound control, and the desktop replay. The server already refused tools once the
  binding was sent; the defect was on the desktop.

Not run, by the owner rule: the full suite, the whole durability lane and the whole vitest run. Those belong to the
landing gate. `desktop_validate.py` stops on `components/pdfSelection/testing/syntheticBook.ts`, which needs an
activation classification. That file predates this stage: its last change is `b1087be0a`. Nothing triggered the
other steps: no migration, no DB or connection change, nothing under `src-tauri` and no configuration key change.

## Fix round 5 (orchestrator rulings)

Codex's verify of fix round 4 (`a58a6b860`; job `20261019-201825-K6nwlx`, read-only) confirmed F3 and F4 of round 4,
**reopened F1 and F2**, and found **F5 (High), F6 (Medium) and F7 (High)**. The common root of F1 and F2: round 4 hung
the binding, the guards and the accounting off `build_request`, which returns None while retrieval is off. The
orchestrator ruled on each (R1-R4), and this round applies the rulings. The fixes are in `6828b96fe`. The references
regenerated on top of it are committed with this record. **None were rejected.**

**Paid calls: none ($0.00).** Every model is a fake. No vault copy was opened, and no manual run was made.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 (round 5, reopened) | High | Some bound Reader answers still escape hint accounting | fixed (R1) | `6828b96fe` | `test_reader_rw1c_review.py::test_a_cold_bound_ask_is_a_hint_whatever_its_type_and_its_cold_row` ×4 (null and unfetchable `coldAttemptId` × `verification` and `other`; old code: stored flag false, response true, next attempt 0), `::test_an_offers_only_bound_question_counts_once` (old code: no item on the row, 0), `::test_the_responses_hint_flag_is_the_stored_flag` ×8 (5 fail on the old code; the 3 cases where the old flag happened to agree pass on both) |
| F2 (round 5, reopened) | High | Offers-only bound requests still deliver the item's solution to the tutor | fixed (R1) | `6828b96fe` | `::test_offers_only_the_bound_items_guards_hold[none]`, `[client]`, `[server]` (old code: "The required probability is 2/13." reached the tutor and the manifest). The unbound control in the same test shows it |
| F3 (round 4) | Medium | The desktop drops the binding when only offers are on | confirmed fixed by Codex | — | no change |
| F4 (round 4) | Medium | "Another way" repeats passages in the sources-service fallback | confirmed fixed by Codex | — | no change |
| F5 | High | Earlier inquiry answers bypass the bound and cold context guards | fixed (R2) | `6828b96fe` | `::test_an_earlier_answer_is_rechecked_under_the_binding` ×4 (retrieval on/off × cold or not; old code: the 2/13 answer was in the tutor's `thread`); `::test_the_learner_work_keeps_the_learners_own_steps` (the audit's guard, new function) |
| F6 | Medium | Cold-row deduplication loses the field report's question attribution | fixed (R3) | `6828b96fe` | `::test_a_bound_question_precedes_the_next_attempt_in_the_field[bound_cold-True]` and `[bound-True]` (old code: `preceded_by_question` false). Control `[unbound-False]` passes on both trees |
| F7 | High | Disabling both switches does not restore base rendering for saved RW1c answers | fixed (R4) | `6828b96fe` | `::test_switching_both_off_restores_the_base_history_projection` (old code: the history still projected `tutor`; compared against `fab576ac1`'s own `ask_history`, read with `git archive`); `TutorAnswer.test.tsx` "renders no RW1c part of a saved answer while the contract supplies no controls" (old code: the excerpt rendered) |

### What each fix does

* **R1 (F1, F2): the binding is independent of retrieval.**
  * `handlers/reader_tutor.bound_ask` builds a `tutor/reader_modes.BoundAsk` whenever either RW1c switch is on and the
    request names a workbench session the server resolves to an item (`restriction.item_id`, never the client's word).
    It is built before and apart from `build_request` and is handed to `reader_dialogue.ask` and
    `tutor_qa.ask_question` as `reader_binding`. It holds the item, the practice session (the workbench's own
    resolution, as before), the restriction's cold status (the client's flag or the server's derivation) and the
    item's guard (`ItemBoundGuard`, with a new `text_leaks` for single texts). Round 4's `_accounting_binding` and the
    request's `item`, `bound_item`, `practice_session_id`, `carries_cold_hint` and `context_guard` fields are gone:
    `ReaderTutorRequest` now only scopes the lookup.
  * Guards: `tutor_qa._build_context` applies the binding's guard to the selection, its neighbours and the blocks they
    cite on the Reader path, retrieval on or off, cold or not; `_reader_lookup_context` still guards the retrieved
    passages. The excerpt check reads the bound item. The manifest records the spans the tutor was given (guarded)
    whenever a binding exists; its `delivery.item_bound_withheld` counts what was withheld.
  * Accounting: the bound row always carries its item. Its flag is `BoundAsk.hint_equivalent`: a cold Ask is a hint
    whatever its `question_type`, whether or not the cold attempt row exists or can be fetched; a non-cold bound Ask uses
    the ordinary classification. The cold practice row only deduplicates (`_record_cold_hint_equivalent`, unchanged:
    it leaves its flag off when the bound row on the same item carries the hint). `reader_dialogue.ask` reads the
    response's and the exchange's `hint_equivalent` from the stored row (`result["hint_equivalent"]`) whenever a
    binding exists; unbound, it stays the base's client cold flag.
  * Both switches off: `restriction.active` is False, so no binding is built and the path is the base's (the
    switch-off goldens pass byte for byte).
  * One visible consequence: a bound, non-cold, substantive question now answers `hintEquivalent: true` (it was the
    client's cold flag, false). That is what is stored and counted.
* **R2 (F5): earlier answers are re-checked under the current restriction.** `reader_modes.guard_thread` passes every
  earlier answer in the thread (the RW1a branch ancestors or, with inquiry off, the flat same-span thread) through the
  binding's `answer_guard`. An answer that fails is replaced by *[An earlier answer is left out while you work this
  problem.]*; the learner's questions and the thread's shape stay, nothing is refused, and the stored exchange is not
  altered. The manifest's `prior_exchanges` is guarded the same way and `delivery.earlier_answers_left_out` counts
  them. The audit of the learner-work context (`guard_learner_work`): the learner's own workbench steps stay; an open
  question's statement (LearnLoop's reading, model-written) and a workbench problem line (source text) are left out
  when the guard says they give the answer away. Cold without a binding has no item to check against, so it is
  unchanged (the base's cold rules apply).
* **R3 (F6): attribution separate from counting.** The window's session rule now lives once, in
  `learnloop/hint_window.py` (a leaf module importing nothing from LearnLoop): `counts_in_session`, its SQL form
  `session_clause` (`Repository.count_hint_equivalent_question_events` uses it) and `following_attempt`
  (`field.signals._link_practice_questions` uses it for practice rows, as before, and now for bound Reader rows).
  A bound Reader row gets `_window_attempt_id`, not `attempt_id`. The derivation then emits one `bound_question`
  attribution row on that attempt's LO when the question's own targets do not include it: no outcome, no mass, no
  attempt link, a type that blocks nothing. `preceded_by_question` therefore flips back to true; `hints_used`,
  coldness and help-before-work are unchanged (asserted in the test), and an unbound Reader question attributes
  nothing. `SIGNAL_VERSION` is not bumped: only bound Reader rows, which exist only on this branch, are affected.
* **R4 (F7): switches off restore base rendering.** `reader_dialogue.ask_history` gains `tutor_views` (default False);
  `reader.ask_history` passes it only while either switch is on, and `build_request` passes it for its own reads (the
  shown passages). With both off the projection equals the base's for the same stored event. `TutorAnswer` renders
  RW1c's parts only when the contract supplies its controls (`tutor` prop). The durable event keeps the view.

### Gate (fix round 5)

All steps ran in the worktree with `TMPDIR=fixtures-local/tmp`. Only targeted tests were run (owner rule
2026-10-17). The pytest runs waited on `/tmp/learnloop-fullsuite.lock` (another stage's run held it) and ran under it.

| step | result |
|---|---|
| backend fail-before on `a58a6b860` (`git archive` of `src` and `migrations` into `fixtures-local/rw1c-r5-base`, run with this branch's tests and `-o pythonpath=fixtures-local/rw1c-r5-base/src`) | 25 new cases: **21 failed, 4 passed** (the passes are controls: the unbound field case and the 3 flag cases where the old value agreed). The 4 F5 cases fail at the import of the new placeholder constant; a probe with the constant inlined showed the behavioural failure on all 4 (the thread carried "The required probability is 2/13."). The learner-work case fails at the import of the new function |
| frontend fail-before (`a58a6b860`'s `apps/learnloop-tauri` extracted to the scratchpad, the new test copied in, `node_modules` linked) | `TutorAnswer.test.tsx`: **1 failed, 6 passed** (the excerpt rendered with no controls) |
| `uv run lint-imports --no-cache` | 28 kept, 0 broken |
| targeted pytest, `uv run pytest -n auto` over 54 files (list below) | **7,112 passed, 36 xfailed** (15 min 53 s) |
| `--durable-sqlite` on the 25 new cases | **25 passed** |
| vitest, `src/screens/reader/` and the `ReaderScreen.*.test.tsx` files | **399 passed** (53 files) |
| `npm run typecheck`; `npm run frontend:build` | clean; built |
| `db_generate_reference.py`, then `db_validate_reference.py` | 0 errors (head 213). Before the regeneration, configuration line citations into the changed files were stale (`tutor_qa.py`, `reader_dialogue.py`, `handlers/reader_tutor.py`) |
| `git diff --check` | clean |

Pytest files in the 54-file run: round 4's 17 files, the 14 `test_workbench*.py` files, the 6 `test_field_*.py`
files, `test_desktop_rpc_contract.py`, `test_sidecar_contract.py`, and every test file that names `field.signals`,
`ask_history`, `hint_window`, `ITEM_WINDOW_QUESTION_CONTEXTS` or `count_hint_equivalent`
(`test_eval_harness.py`, `test_interaction_signals.py`, `test_learner_text_gaps*.py` (4), `test_library_ask_review.py`,
`test_mobile_allowlist.py`, `test_placement_signals.py`, `test_reader_branches.py`, `test_reader_inquiry_kill_switch.py`,
`test_reader_inquiry_status.py`, `test_reader_rw1b_review.py`, `test_sidecar_reader.py`, `test_stuck_prompt.py`,
`test_stuck_prompt_replay.py`).

Not run, by the owner rule: the full suite, the whole durability lane and the whole vitest run. Pre-existing and
unchanged by this round: `desktop_validate.py` stops on `components/pdfSelection/testing/syntheticBook.ts` (needs an
activation classification), and `module_validate.py` reports missing module notes (474/917 source modules covered;
the new `learnloop/hint_window.py` is one more uncovered leaf). No migration, no DB or connection change, nothing
under `src-tauri` and no configuration key change.

## Fix round 6 (orchestrator rulings)

Codex's verify of fix round 5 (`48ed78307`; job `20261019-205559-Js5GhV`, read-only) confirmed F1, F2 and F7,
**reopened F5 (High) and F6 (Medium)**, and found **F8 (High)**. The orchestrator ruled on each (R1-R3), and this
round applies the rulings. The fixes are in `c67059173`. The references regenerated on top of it are committed with
this record. **None were rejected.**

**Paid calls: none ($0.00).** Every model is a fake. No vault copy was opened, and no manual run was made.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1, F2, F7 (round 5) | High | (see fix round 5) | confirmed fixed by Codex | — | no change |
| F5 (round 6, reopened) | High | Ancestor filtering still admits a complete answer split across turns; the placeholder itself is not validated | fixed (R1) | `c67059173` | `test_reader_rw1c_review.py::test_an_answer_split_across_earlier_turns_is_not_delivered_whole` ×4 (retrieval on/off × cold or not; old code: both halves delivered, so the thread scored 1.0 against the key), `::test_a_placeholder_the_key_matches_is_replaced_by_nothing` (old code: the replacement line matched the degenerate key "while you work this problem") |
| F6 (round 6, reopened) | Medium | A mapped LO can suppress the required question attribution | fixed (R2) | `c67059173` | `::test_a_mapped_lo_does_not_suppress_the_attribution` (old code: `preceded_by_question` false when the passage maps to the item's LO and the item's subject is `math`) |
| F8 | High | Personalized lookup queries bypass the binding's answer guard | fixed (R3) | `c67059173` | `::test_a_leaking_gap_statement_never_reaches_the_lookup` (old code: the query was "How should I start? The required probability is 2/13.", and the verification's prompt carried it); the audit's `::test_that_didnt_help_bound_withholds_a_leaking_misconception` (old code: the item's LO's misconception stating the key reached the verification's context) |

### What each fix does

* **R1 (F5): aggregation and the placeholder.** `reader_modes.withhold` is the one rule for every set of model-written
  texts a bound prompt carries together:
  * each text that gives the key away alone is withheld;
  * then, while the kept texts still give it away combined (joined as the tutor reads them, with the replacement in
    place of each withheld one), the kept text with the highest individual overlap is withheld, ties going to the
    most recent, and the whole is checked again.
  * The matcher is the binding's guard (`ItemBoundGuard.text_leaks`), and the ranking is the same matcher's score
    (new `ItemBoundGuard.text_overlap`: `span_answer_overlap`, a solution lead counting 1.0), injected as
    `BoundAsk.answer_overlap`.
  * `guard_thread` uses it for the thread and for the manifest's `prior_exchanges`. The verify's split ("Swapping two
    rows multiplies the determinant." 0.67, "By minus one, so it flips." 0.33, together 1.0) now delivers the second
    half only; the unrelated root answer and all three learner questions are kept.
  * The placeholder is validated: if *[An earlier answer is left out while you work this problem.]* itself matches
    the item's guard (or the placeholders combined with the kept answers still do), the empty string replaces the
    answer instead. Learner-written questions and learner work are never removed.
* **R2 (F6): the attribution row is always emitted.** `field.signals` emits the zero-mass `bound_question` row for every
  bound Reader question with a window attempt, whether or not the question's own row already names the LO. That row
  carried the question's subject (`default`, none was recorded), not the item's (`math`), so it did not attribute. The
  test compares the derivation with and without the window link: every other signal is identical (types, masses,
  subjects, links), the attempts differ only in `preceded_by_question`, the new row has no mass, no outcome and no
  attempt link and does not block fast-tracking, and the hint count is 1.
* **R3 (F8): one sanitized copy of every model-written lookup input.** `handlers/reader_tutor.reader_inputs` builds a
  `ReaderInputs` once per lookup, before the query is constructed:
  * `gaps`: the open-gap and misconception statements on the passage's LOs (`open_questions`), passed through
    `reader_modes.guard_statements` (the same `withhold` rule; a withheld statement is dropped). This one copy builds
    the lookup query, so the query rewrite and the verification's `context.question` see it too, and it is the open
    questions of the bridge's learner work (`source_retrieval.reader_tutor.learner_work(gaps=…)`, which no longer
    reads them a second time).
  * `learner_work`: those guarded statements plus the learner's own steps (untouched) and the problem line (guarded,
    round 5).
  * `misconceptions` (the audit): "that didn't help" (`remediate`) under a binding sends the resolved misconceptions
    and their corrections to the verification's context; the adapter now resolves them itself
    (`instructional.sources.resolve_misconceptions`, the named gaps or the item's LO's active ones), guards
    statement and correction together, and hands the result to `propose_sources` as `misconceptions`, so the service
    never resolves an unguarded copy.
  * The learner's typed question and their earlier questions are kept as they are. The rest of `build_request` was
    audited: the excluded and shown span keys and the named-gap refs are identifiers, and the item's own practice
    question in the verification's context is the base's (T6) and unchanged. Unbound, nothing is guarded, as before.

### Gate (fix round 6)

All steps ran in the worktree with `TMPDIR=fixtures-local/tmp`. Only targeted tests were run (owner rule
2026-10-17). The pytest runs waited on `/tmp/learnloop-fullsuite.lock` and ran under it.

| step | result |
|---|---|
| backend fail-before on `48ed78307` (`git archive` of `src` and `migrations` into `fixtures-local/rw1c-r6-base`, run with this branch's tests and `-o pythonpath=fixtures-local/rw1c-r6-base/src`) | 8 new cases: **8 failed, 0 passed**. The placeholder case fails at the new `text_overlap`; a probe of the old `guard_thread` with the degenerate key showed the replacement line still matching the guard |
| `uv run lint-imports --no-cache` | 28 kept, 0 broken |
| targeted pytest, `uv run pytest -n auto` over round 5's 54 files | **1,102 passed** (53 s; `--collect-only` on the same list also gives 1,102) |
| `--durable-sqlite` on the 8 new cases | **8 passed** |
| vitest, `src/screens/reader/` and the `ReaderScreen.*.test.tsx` files (no frontend change this round) | **399 passed** (53 files) |
| `db_generate_reference.py`, then `db_validate_reference.py` | 0 errors (head 213). Before the regeneration, 1 configuration line citation into `handlers/reader_tutor.py` was stale |
| `git diff --check` | clean |

**Correction to the round-5 record.** Fix round 5's gate row reads "7,112 passed, 36 xfailed (15 min 53 s)" for the
same 54-file list. That list collects 1,102 tests now (1,094 on the round-5 tree, before this round's 8), so the
round-5 log's count cannot belong to that list and is withdrawn; the run above is the targeted gate over it, on a
tree that contains every round-5 change.

Not run, by the owner rule: the full suite, the whole durability lane and the whole vitest run. No frontend change, so
no typecheck or build. Pre-existing and unchanged: `desktop_validate.py` (`syntheticBook.ts`) and `module_validate.py`
(missing module notes). No migration, no DB or connection change, nothing under `src-tauri` and no configuration key
change.

## Fix round 7 (orchestrator ruling)

Codex's verify of fix round 6 (`2f9e6f468`; job `20261019-212720-YsSQ0w`, read-only) confirmed F5 and F6, **reopened
F8 (High)**, and raised **F9 (High)**. The orchestrator ruled F8's final shape (R1) and ruled F9 **non-blocking**
(see below). The fix is in `f9acffb68`. The references regenerated on top of it are committed with this record.

**Paid calls: none ($0.00).** Every model is a fake. No vault copy was opened, and no manual run was made.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F5, F6 (round 6) | High, Medium | (see fix round 6) | confirmed fixed by Codex | — | no change |
| F8 (round 7, reopened) | High | Separately guarded inputs reconstruct the answer in one prompt | fixed (R1) | `f9acffb68` | `test_reader_rw1c_review.py::test_an_earlier_answer_and_a_gap_are_withheld_as_one[bound]` and `[bound_cold]` (old code: the earlier answer and the open gap were delivered together, scoring 1.0); `::test_a_gap_and_a_misconceptions_correction_are_withheld_as_one` (old code: the verification's question and misconceptions together gave the key away); `::test_a_three_slot_split_is_withheld_as_one` (old code: answer, open question and problem line delivered together). Controls `[unbound]` and `[switches_off]` pass on both trees |
| F9 | High | A bound Ask in the same second as an attempt can fall out of hint accounting | **non-blocking (orchestrator ruling)**: an inherited cross-cutting ordering issue, queued as its own follow-up; not touched here | — | see open questions below |

### What the fix does

* **One plan per bound request, read per model call.** `tutor/reader_modes.plan_bound_delivery` collects every
  model-written or learner-model-derived text the request delivers and withholds from them ONCE:
  * the lookup's verification call (and its query rewrite, which reads a prefix of the same query) carries the open-gap
    statements in its question and, under "that didn't help", the misconceptions with their corrections in its
    context;
  * the tutor call carries the earlier answers, the bridge's open questions (the same gap statements, one slot with
    them) and the problem line of the learner's work.
* `withhold_for_call(slots, binding)` reads one call's union in delivery order with the existing `withhold` (leaking
  alone first, then the highest individual overlap, ties the most recent; a withheld earlier answer counts as its
  validated placeholder, a withheld statement or line as nothing). A text either call withholds is withheld from every
  slot, and the calls are read again until nothing changes (the first three gap statements KEPT are the ones used, so
  what each call carries depends on what is withheld). The placeholder is then validated against the tutor call's
  delivered union too (empty when it would match).
* **Delivered from the same set.** `tutor_qa.ask_question` builds the plan as soon as the binding is known, before the
  lookup runs: the thread the tutor reads, the lookup's inputs (`ReaderLookup` now builds its query at call time from
  the kept gap statements, and hands the kept misconceptions to `propose_sources`), the bridge's work and the
  exchange's manifest (`prior_exchanges` is the delivered thread, `delivery.bound_withheld` counts each slot) all come
  from it. Round 6's per-source guarded copies (`guard_statements`, `guard_learner_work`, the guarded
  `reader_inputs`) are gone: the adapter now collects the inputs as read (`ReaderInputs`), resolving "that didn't
  help"'s misconceptions itself when bound so the service never resolves a copy of its own.
* **Never withheld:** the learner's own words (their question, their earlier questions, their workbench steps).
  Unbound and with both switches off nothing is planned, so the delivery is as before (the switch-off goldens pass).
* **Boundary kept as ruled.** The union is the model-written and learner-model-derived text. The book's own passages
  (the selection, its neighbours, the retrieved passages) stay under the item's span guard
  (`ItemBoundGuard`, rounds 1-5) and are not part of the union.
* The round-5 unit test of the learner-work audit now exercises the plan (`::test_the_learner_work_keeps_the_learners_own_steps`).

### Open questions

* **F9 (ruled non-blocking, its own follow-up).** Question and attempt rows have second-resolution `created_at`. A
  bound Ask started in the same second an attempt completes gets the same stamp, and the item window counts only
  questions with `created_at` after the previous attempt, so it counts 0; `hint_window.following_attempt` also links it
  to the preceding attempt. The fix is a durable ordering that tells events within one second apart, used by the
  submission count, the post-hoc reconstruction and the field's attribution (not `>` to `>=`, which would count earlier
  help twice). This is inherited and cross-cutting; RW1c does not change it.

### Gate (fix round 7)

All steps ran in the worktree with `TMPDIR=fixtures-local/tmp`. Only targeted tests were run (owner rule
2026-10-17). The pytest runs waited on `/tmp/learnloop-fullsuite.lock` and ran under it.

| step | result |
|---|---|
| backend fail-before on `2f9e6f468` (`git archive` of `src` and `migrations` into `fixtures-local/rw1c-r7-base`, run with this branch's tests and `-o pythonpath=fixtures-local/rw1c-r7-base/src`) | 6 new cases: **4 failed, 2 passed** (the passes are the unbound and switches-off controls) |
| `uv run lint-imports --no-cache` | 28 kept, 0 broken |
| targeted pytest, `uv run pytest -n auto` over the 54-file list (1,108 tests collected) | **1,108 passed** (54 s) |
| `--durable-sqlite` on the 6 new cases and the updated learner-work case | **7 passed** |
| vitest, `src/screens/reader/` and the `ReaderScreen.*.test.tsx` files (no frontend change) | **399 passed** (53 files) |
| `db_generate_reference.py`, then `db_validate_reference.py` | 0 errors (head 213). Before the regeneration, 8 configuration line citations into the changed files were stale |
| `git diff --check` | clean |

Not run, by the owner rule: the full suite, the whole durability lane and the whole vitest run. Pre-existing and
unchanged: `desktop_validate.py` (`syntheticBook.ts`) and `module_validate.py` (missing module notes). No migration, no
DB or connection change, nothing under `src-tauri` and no configuration key change.

## Fix round 8 (orchestrator ruling)

Codex's verify of fix round 7 (`3c0f97753`; job `20261019-215502-FCtES7`, read-only) confirmed the union rule (9,168
split checks), counting, and unbound and switch-off parity, and **reopened F8 (High) on one path**: the bound lookup
query was cut at 2,000 characters AFTER the plan, so a passing gap statement could be cut into the key. The fix is in
`fc70cf041`. The references regenerated on top of it are committed with this record. **Nothing was rejected.**

**Paid calls: none ($0.00).** Every model is a fake. No vault copy was opened, and no manual run was made.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F8 (round 8, reopened) | High | Query truncation can create a leak after the delivery plan | fixed (R1) | `fc70cf041` | `test_reader_rw1c_review.py::test_a_length_limit_never_cuts_a_statement_into_the_key` ×6 (explain, another way, that didn't help × sources service on/off; old code: "The probability is 2/130." became "… The probability is 2/13" in the query and the verification's question). Controls: `::test_a_statement_that_fits_whole_is_still_delivered`, `::test_the_learners_question_is_truncated_as_before[False]` (unbound: the old query, byte for byte) pass on both trees; `[True]` fails on the old code (the bound query ended in the cut statement) |
| F9 (round 7) | High | Same-second timestamp boundary | non-blocking (orchestrator ruling, round 7); its own follow-up | — | unchanged, see round 7's open questions |

### What the fix does

* **One helper, `reader_modes.fit_slots`,** builds any bound, length-limited, model-bound string from planned slots:
  * the learner's own text first, truncated at the limit as before (it is theirs);
  * then the model-written slots WHOLE, in order; the first that does not fit is dropped with every later one (the
    latest, lowest priority first); no model-written slot is ever cut mid-text;
  * then a final check: the binding's guard reads the model-written fragments actually present
    (`withhold`, the plan's own rule), and any slot it names is dropped and the string rebuilt.
* **The bound lookup query** (`source_retrieval.reader_tutor.reader_query`, with the plan's binding passed through
  `BoundDelivery.lookup_inputs`) uses it at `BOUND_QUERY_CHARS`, the smallest of its own limit and every later cut of
  the same string: the search and the rewrite cut the whitespace-normalized query at `MAX_QUERY_CHARS`, the
  verification prompts at `QUESTION_CHARS` (all 2,000 today). The bound query is whitespace-normalized and within that
  limit, so none of those later cuts reaches a statement; the rewrite's input and the verification's question are
  that query. Unbound, `reader_query` is unchanged.
* **The audit of the other cuts on these paths:**
  * The verification's `context.misconceptions` (statements and corrections) and the tutor's thread and bridge lines
    are not cut after the plan.
  * `open_questions` (300 characters a statement) and the workbench problem line (300) are cut BEFORE the plan, so the
    plan's guard reads exactly the delivered text; such a cut cannot turn a checked text into a leaking one.
  * One cut after a guard was found outside the model-written slots: the context budget (`reader_modes.deliver`) can
    trim a retrieved passage after the item's span guard read it whole. `_reader_lookup_context` now runs the guard
    again over what is delivered, and the counts join `item_bound_withheld`.
* **A test-isolation fix found on the way.** `instructional.tools` binds `propose_sources` by name when it is first
  imported. Under xdist's scheduling with this round's added tests, a worker could first import it inside
  `test_reader_tutor_retrieval.py::test_without_a_ready_verification_nothing_is_retrieved_or_claimed`, while that
  test's failing stand-in was patched in, so a later offers test in the worker failed ("retrieved without
  verification"; 3 of 10 runs). That test (and this round's recording helper) now imports `instructional.tools` before
  patching: 0 failures in 15 repeated runs of the four RW1c files. On the round-7 tree, without the new tests, 0 of 8
  runs failed.

### Gate (fix round 8)

All steps ran in the worktree with `TMPDIR=fixtures-local/tmp`. Only targeted tests were run (owner rule
2026-10-17). The pytest runs took `/tmp/learnloop-fullsuite.lock`.

| step | result |
|---|---|
| backend fail-before on `3c0f97753` (`git archive` of `src` and `migrations` into `fixtures-local/rw1c-r8-base`, run with this branch's tests and `-o pythonpath=fixtures-local/rw1c-r8-base/src`) | 9 new cases: **7 failed, 2 passed** (the passes are the fits-whole and unbound controls) |
| `uv run lint-imports --no-cache` | 28 kept, 0 broken |
| targeted pytest, `uv run pytest -n auto` over the 54-file list | **1,117 passed** (55 s) |
| `--durable-sqlite` on the 9 new cases | **9 passed** |
| vitest, `src/screens/reader/` and the `ReaderScreen.*.test.tsx` files (no frontend change) | **399 passed** |
| `db_generate_reference.py`, then `db_validate_reference.py` | 0 errors (head 213). Before the regeneration, 2 configuration line citations into the changed files were stale |
| `git diff --check` | clean |

Not run, by the owner rule: the full suite, the whole durability lane and the whole vitest run. Pre-existing and
unchanged: `desktop_validate.py` (`syntheticBook.ts`) and `module_validate.py` (missing module notes). No migration, no
DB or connection change, nothing under `src-tauri` and no configuration key change.

## Fix round 9 (orchestrator ruling)

Codex's verify of fix round 8 (`fc3b44b98`; job `20261019-222618-Me8DDE`, read-only) confirmed the truncation fix (12
combinations), the post-trim passage re-guard, unbound and switch-off parity and the counting, and **reopened F8
(High) on one path**: `fit_slots`' final check read only the fitted query statements, while the verification call
also receives the remediation misconceptions and corrections, so dropping a later statement for length changed the
delivered union ("The probability numerator is 2" next to "13 is the denominator." scores 1.0 against 2/13; 52 prefix
lengths 1,918-1,969). The fix is in `bdb5ef8e7`. The references regenerated on top of it are committed with this
record. **Nothing was rejected.**

**Paid calls: none ($0.00).** Every model is a fake. No vault copy was opened, and no manual run was made.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F8 (round 9, reopened) | High | Whole-slot dropping can recreate a leaking verification union | fixed (R1) | `bdb5ef8e7` | `test_reader_rw1c_review.py::test_a_misconception_beside_a_fitted_gap_never_reaches_the_verification` (the verify's reproduction end to end at 1,950 characters; old code: the verification received the numerator statement and the misconception together); `::test_the_verification_union_is_checked_after_fitting` ×52 (learner text 1,918-1,969 characters); `::test_the_fixpoint_reads_the_rebuilt_call_again` (a case needing a second pass) |
| F9 (round 7) | High | Same-second timestamp boundary | non-blocking (orchestrator ruling, round 7); its own follow-up | — | unchanged |

### What the fix does

* **One owner of the final check.** `reader_modes.plan_bound_delivery`'s fixpoint loop is the only place a bound
  request's model-written texts are checked. It now fits the lookup query itself: the request carries the learner's
  own query text (`ReaderLookup.learner_query`: the question and the latest ancestors' questions, never withheld) and
  the limit (`BOUND_QUERY_CHARS`), and each pass fits the kept gap statements whole after it (`fit_slots`, which
  now only fits).
* **Each call as delivered.** On every pass the verification call's union is the statements that FIT plus the
  misconceptions with their corrections; the tutor call's is the earlier answers (withheld ones as the validated
  placeholder), the bridge's open questions and the problem line. `withhold_for_call` reads each; any text it
  withholds is withheld from every slot, and every call is rebuilt (the fitted statements change when one is
  withheld: a later one may now fit) and read again until a pass withholds nothing. It ends because withholding only
  grows; the last pass read every call as it is delivered.
* **The lookup sends the plan's query.** `BoundDelivery.query` is the fitted query the last pass checked;
  `ReaderLookup.__call__` sends it unchanged (no second fitting, so nothing is dropped after the check). Unbound, the
  query is `reader_query`'s, as before (the bound branch of `reader_query` from round 8 is gone).
* In the verify's reproduction the two statements' individual overlaps tie at 0.0, so the more recent text, the
  misconception, is withheld; the numerator statement stays in the query. In the two-pass case, the first pass
  withholds a statement that leaks alone, which frees room for the next statement; the second pass reads the rebuilt
  call (that statement beside the misconception) and withholds the misconception.

### Gate (fix round 9)

All steps ran in the worktree with `TMPDIR=fixtures-local/tmp`. Only targeted tests were run (owner rule
2026-10-17). The pytest runs took `/tmp/learnloop-fullsuite.lock`.

| step | result |
|---|---|
| backend fail-before on `fc3b44b98` (`git archive` of `src` and `migrations` into `fixtures-local/rw1c-r9-base`, run with this branch's tests and `-o pythonpath=fixtures-local/rw1c-r9-base/src`) | 54 new cases: **54 failed**. The end-to-end case fails on the delivered union (the numerator statement and the misconception reached the verification together). The 53 plan-level cases fail on the new `plan_bound_delivery(query_learner=…)`; a probe of round 8's own path (plan, then `fit_slots` with its final check, then the misconception delivered) leaked at 43 of the 52 lengths (the 9 shortest fit both statements, which keeps the two halves apart) |
| `uv run lint-imports --no-cache` | 28 kept, 0 broken |
| targeted pytest, `uv run pytest -n auto` over the 54-file list | **1,171 passed** (56 s) |
| `--durable-sqlite` on the 54 new cases | **54 passed** |
| vitest, `src/screens/reader/` and the `ReaderScreen.*.test.tsx` files (no frontend change) | **399 passed** |
| `db_generate_reference.py`, then `db_validate_reference.py` | 0 errors (head 213). Before the regeneration, 4 configuration line citations into the changed files were stale |
| `git diff --check` | clean |

Not run, by the owner rule: the full suite, the whole durability lane and the whole vitest run. Pre-existing and
unchanged: `desktop_validate.py` (`syntheticBook.ts`) and `module_validate.py` (missing module notes). No migration, no
DB or connection change, nothing under `src-tauri` and no configuration key change.

## Fix round 10 (orchestrator rulings)

Codex's verify of fix round 9 (`b1a740eca`; job `20261019-225424-0vt8Hw`, read-only) confirmed round 9's fixpoint (0 of
52 leaks, 1,200 union cases, 60 unbound, 16 history, 108 counting, no regression) and **reopened F8 (High)**: the
verification's practice question (`verification_context` → `practice_question(item)`) was added outside the plan.
(a) A gap "The favorable count is 2" and a model-authored stem "13 equally likely outcomes make up the sample space.
What is the probability?" each pass alone and score 1.0 together, with nothing withheld. (b) A stem containing "A
comparison probability is 2/130." placed so the 700-character cut ends "2/13" scores 1.0. The fix is in `570869ab3`.
The references regenerated on top of it are committed with this record. **Nothing was rejected.**

**Paid calls: none ($0.00).** Every model is a fake. No vault copy was opened, and no manual run was made.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F8 (round 10, reopened) | High | Verification's practice question bypasses the delivery fixpoint | fixed (R1-R3) | `570869ab3` | `test_reader_rw1c_review.py::test_the_practice_question_is_a_planned_member_of_the_verification` ×12 (both reproductions × explain, another way, that didn't help × sources service on/off; old code: the delivered union scored as leaking in all 12); `::test_a_whole_token_cut_never_splits_a_token_or_a_group` ×79 (every limit 1-79); `::test_the_stem_is_never_withheld`; `::test_no_bound_model_call_receives_item_text_from_outside_the_plan` ×6 (scan) |
| F9 (round 7) | High | Same-second timestamp boundary | non-blocking (orchestrator ruling, round 7); its own follow-up | — | unchanged |

### What the fix does

* **R1: the practice question is planned.** When the verification carries the item's question (an assisted-practice
  lookup: the adapter sets `ReaderTutorRequest.practice_question_limit = PRACTICE_QUESTION_CHARS`),
  `plan_bound_delivery` fits the item's presented question ONCE (`fit_presented_prompt`, the required method's
  instruction kept whole) with `reader_modes.whole_token_cut`: whitespace collapsed, cut only at a space outside braces
  and outside `$...$` math at or before the limit, so a token, a number or a LaTeX group is never split ("2/130" never
  becomes "2/13"). The fitted text is `BoundDelivery.practice_question`; `ReaderLookup` passes it as
  `planned_practice_question` through `propose_sources` / `find_sources_for_caller` to `find_sources`, whose
  `verification_context` sends it unchanged (it builds and cuts its own only when no planned value is given: every
  unbound and non-Reader caller, as before).
* **The audit of item-text insertions on the bound path.** `verification_context` was the only one a bound Reader
  request reaches. `verify.verify_spans` takes its practice question as an argument from its caller
  (`source_retrieval.tutor`, the practice/feedback/library tutor's provider), which a Reader request does not use;
  the tutor's Reader context carries no item text (`tutor_qa._build_context` returns before the practice context's
  `practice_item_prompt`); tool and practice requests, which would show item prompts, are refused under a binding
  (round 1, F2); the other `fit_presented_prompt` callers are the desktop's previews.
* **R2: a fixed member of the union.** The fitted question joins the verification call's slots as `practice_question`,
  marked fixed in `withhold_for_call` (`withhold(fixed=…)`): it is read with the rest and never a candidate, so when a
  union with it leaks, the model-written slots are withheld under the existing rule (here the gap statement). A
  fitted question that states the key alone is the item's own authoring: recorded (`BoundDelivery.stem_leaks_alone`,
  `delivery.practice_question_states_key`, Low), left out of the union read, and nothing is withheld on its account;
  it is still delivered.

### Gate (fix round 10)

All steps ran in the worktree with `TMPDIR=fixtures-local/tmp`. Only targeted tests were run (owner rule
2026-10-17). The pytest runs took `/tmp/learnloop-fullsuite.lock`.

| step | result |
|---|---|
| backend fail-before on `b1a740eca` (`git archive` of `src` and `migrations` into `fixtures-local/rw1c-r10-base`, run with this branch's tests and `-o pythonpath=fixtures-local/rw1c-r10-base/src`) | 98 new cases: **98 failed**. The 12 end-to-end cases fail on the delivered union (each verification prompt scored as leaking). The 6 scan cases fail at the import of the new cutter; a probe with that import replaced showed the old code building the question itself in every bound lookup (the refusing builder failed each lookup, so no verification ran). The 79 cut cases fail at the same import; the old cutter (`verify._cut`) splits a token, a group or "2/130" at 70 of the 79 limits. The never-withheld case fails on the new plan argument |
| `uv run lint-imports --no-cache` | 28 kept, 0 broken |
| targeted pytest, `uv run pytest -n auto` over the 54-file list | **1,269 passed** (59 s) |
| `--durable-sqlite` on the 98 new cases | **98 passed** |
| vitest, `src/screens/reader/` and the `ReaderScreen.*.test.tsx` files (no frontend change) | **399 passed** |
| `db_generate_reference.py`, then `db_validate_reference.py` | 0 errors (head 213). Before the regeneration, 5 configuration line citations into the changed files were stale |
| `git diff --check` | clean |

Not run, by the owner rule: the full suite, the whole durability lane and the whole vitest run. Pre-existing and
unchanged: `desktop_validate.py` (`syntheticBook.ts`) and `module_validate.py` (missing module notes). No migration, no
DB or connection change, nothing under `src-tauri` and no configuration key change.

## Fix round 11 (orchestrator rulings)

Codex's verify of fix round 10 (`1d2c2981d`; job `20261019-231238-ZR55fz`, read-only) confirmed round 10's stem fix
(both reproductions 0.0, 1,715 union cases, 1,344 cutter checks, parity and counting) and reopened the class:
**F8 (High)**, a gap that is the key with its spaces doubled, or turned into newlines or tabs, scored 0.0 in the plan
and the search's whitespace collapse then sent the exact key to the rewrite (18 cases); **F10 (Medium)**,
`whole_token_cut` read an opening `$$` as two delimiters and cut inside display math. The orchestrator ruled to close
the class. The fix is in `0687cdfa3`. The references regenerated on top of it are committed with this record.
**Nothing was rejected.**

**Paid calls: none ($0.00).** Every model is a fake. No vault copy was opened, and no manual run was made.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F8 (round 11, reopened) | High | Query normalization creates a leak after the fixpoint | fixed (R1-R3) | `0687cdfa3` | `test_reader_rw1c_review.py::test_a_whitespace_variant_of_the_key_never_reaches_the_rewrite` ×18 (the verify's cases: spaces, newlines, tabs × explain, another way, that didn't help × service on/off; old code: the rewrite prompt carried the key); the send-boundary contract `::test_every_sent_model_written_fragment_was_checked` ×72; the unbound pin `::test_unbound_queries_are_built_as_before` |
| F10 | Medium | Whole-token cutting splits display-math groups | fixed (R4) | `0687cdfa3` | `::test_a_cut_never_opens_a_group_it_does_not_close` ×5 (display, inline, `\(…\)`, `\[…\]`, braces, every limit; old code: display, paren and bracket failed), `::test_the_verifys_display_math_case_is_cut_before_the_group` |
| F9 (round 7) | High | Same-second timestamp boundary | non-blocking (orchestrator ruling, round 7); its own follow-up | — | unchanged |

### What the fix does

* **R1: one canonical form.** `learnloop/text_canon.py` (a leaf module) holds `collapse_whitespace`, which is now
  the search's and the rewrite's own normalisation (`practice_index.query_vectors.normalize_query` returns it: one
  function, so they cannot drift), and `canonical`: Unicode NFKC, the invisible format characters (category `Cf`:
  zero-width spaces and joiners, the byte-order mark, soft hyphens) removed, then `collapse_whitespace`. It is
  idempotent and every later whitespace collapse leaves it unchanged. The bound guard (`ItemBoundGuard.text_leaks`
  and `.text_overlap`, the matcher `withhold` and `plan_bound_delivery` use) scores the canonical form.
* **R2: the text checked is the text sent.** `plan_bound_delivery` canonicalises every model-written slot before it
  reads it and delivers that form: the earlier answers, the gap statements (so the query, its rewrite and the
  verification), the bridge's open questions and problem line, the misconceptions' statements and corrections (a
  copy of each record) and the item's question (canonicalised, then fitted). The learner's own text is untouched
  here; it is whitespace-collapsed only where the query already did it. Unbound, nothing changes (pinned: the
  unbound query keeps a zero-width character as written). `BoundDelivery.checked` records each call's final
  delivered texts (`lookup`: the fitted statements, the misconceptions, the question; `tutor`: the answers as sent,
  the open questions, the problem line).
* **R3: the send-boundary contract.** `::test_every_sent_model_written_fragment_was_checked` runs a bound request for
  each intent × sources service on/off × cold/non-cold × six variants of the planted texts (doubled spaces, tabs,
  newlines, no-break spaces, zero-width characters, upper case; one is the whole key, others parts of it). It
  captures the exact prompts the fake tutor, the rewrite (the production `rewrite_prompt`, from the text the search
  hands it) and the verification receive, and asserts (a) every model-written fragment in them, canonical, is a text
  the plan's final pass checked (the query equals the plan's; its part after the learner's words is the checked
  statements; each misconception and the question are checked slots; each answer, open question and problem line in
  the tutor's context is a checked slot) and (b) the guard passes over the delivered model-written union with the
  item's question. It also asserts the whole-key variant was read as the key and withheld.
* **R4: matched groups.** `whole_token_cut` is now a scanner with explicit states: inline `$...$`, display `$$...$$`,
  `\(...\)`, `\[...\]` (the open group's closing delimiter) and brace depth; an escaped character (`\$`, `\{`) opens
  nothing. It cuts only at a space where no group is open.

### Gate (fix round 11)

All steps ran in the worktree with `TMPDIR=fixtures-local/tmp`. Only targeted tests were run (owner rule
2026-10-17). The pytest runs took `/tmp/learnloop-fullsuite.lock`.

| step | result |
|---|---|
| backend fail-before on `1d2c2981d` (`git archive` of `src` and `migrations` into `fixtures-local/rw1c-r11-base`, run with this branch's tests and `-o pythonpath=fixtures-local/rw1c-r11-base/src`) | 97 new cases: **94 failed, 3 passed**. The 18 F8 cases fail on the delivered rewrite prompt (the key, after the search's collapse). The F10 sweeps fail for display, paren and bracket and the verify's case; inline and brace pass (round 10 handled them). The 72 contract cases fail at the import of the new `text_canon` module (the contract reads the plan's new `checked` record); the 18 behavioural cases cover the same send path. The unbound pin passes on both trees, as it should |
| `uv run lint-imports --no-cache` | 28 kept, 0 broken |
| targeted pytest, `uv run pytest -n auto` over 58 files (the 54-file list plus the four that name `normalize_query` or `query_vectors`: `test_matching.py`, `test_practice_index_find.py`, `test_practice_index_adapters.py`, `test_source_retrieval_search.py`) | **1,421 passed** (81 s) |
| `--durable-sqlite` on the 97 new cases | **97 passed** |
| vitest, `src/screens/reader/` and the `ReaderScreen.*.test.tsx` files (no frontend change) | **399 passed** |
| `db_generate_reference.py`, then `db_validate_reference.py` | 0 errors (head 213). Before the regeneration, 2 configuration line citations into the changed files were stale |
| `git diff --check` | clean |

Not run, by the owner rule: the full suite, the whole durability lane and the whole vitest run. Pre-existing and
unchanged: `desktop_validate.py` (`syntheticBook.ts`) and `module_validate.py` (missing module notes; the new
`learnloop/text_canon.py` is one more leaf without a note). No migration, no DB or connection change, nothing under
`src-tauri` and no configuration key change.

## Fix round 12 (orchestrator rulings)

Codex's verify of fix round 11 (`1ac5b3ac9`; job `20261020-011901-4FpwD0`, read-only) confirmed F10 and the original
F8 whitespace cases (576 union, 105 normalisation and cache parity, 136 unbound, 16 + 16 base, 54 + 36 counting) and
**reopened F8 (High)**: `canonical()` was not idempotent. "A", a zero-width space and a combining ring canonicalised
once to "A" + ring (removing the format character exposed a composition), again to "Å". The plan delivered the
once-canonical text while the guard re-canonicalised and scored "Å = 2" (0.0); the exact delivered fragment scores
1.0 against the key "a = 2" in a cold tutor thread. Round 11's contract test re-canonicalised too, so it missed it.
The fix is in `459f4b4ec`. The references were regenerated on top of it (no citation had moved) and are committed
with this record. **Nothing was rejected.**

**Paid calls: none ($0.00).** Every model is a fake. No vault copy was opened, and no manual run was made.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F8 (round 12, reopened) | High | Non-idempotent canonicalisation makes the guard score different text from delivery | fixed (R1-R3) | `459f4b4ec` | `test_reader_rw1c_review.py::test_the_verifys_cold_thread_case_delivers_what_was_scored` ×2 (cold, and non-cold; old code: the delivered "A" + ring was not a fixed point and the matcher found the key in it); `::test_canonical_is_a_fixed_point`; `::test_the_guard_reads_only_delivered_text`; the contract `::test_every_sent_model_written_fragment_was_checked` gains the `cf_combining` variant (×12, all failing on the old code) and now scores the exact delivered bytes |
| F10 | Medium | Whole-token cutting splits display-math groups | confirmed fixed by Codex | — | no change |
| F9 (round 7) | High | Same-second timestamp boundary | non-blocking (orchestrator ruling, round 7); its own follow-up | — | unchanged |

### What the fix does

* **R1: a true fixed point.** `text_canon.canonical` repeats its pass (NFKC, remove category `Cf`, collapse
  whitespace) until nothing changes (bounded at 16 passes; it raises rather than return a non-fixed point, which no
  input has produced). `canonical(canonical(x)) == canonical(x)` is tested over every string of up to three
  characters of an alphabet of bases, format characters between bases and combining marks, Hangul jamo and
  syllables, compatibility forms (ligatures, fullwidth, circled digits, fractions, Ohm and Angstrom signs) and every
  kind of whitespace, and over 20,000 seeded longer strings.
* **R2: the guard scores exactly what is delivered.** `ItemBoundGuard.text_leaks` and `.text_overlap` no longer
  transform their input: they check that it is already canonical (`canonical(x) == x`) and refuse it otherwise
  (`ValueError`), so a mismatch fails loudly instead of being scored as other text. `plan_bound_delivery` is the
  only place canonicalisation happens: every model-written slot is canonicalised there, the fitted practice question
  too, and a call's union is its canonical fragments joined by one space (`reader_modes._JOIN`, empty stand-ins
  skipped), which is itself canonical.
* **R3: the contract scores the exact bytes.** `::test_every_sent_model_written_fragment_was_checked` now compares the
  query exactly (no re-canonicalisation), asserts every delivered model-written fragment is a canonical fixed point,
  and scores the exact delivered union with both the underlying matcher (`span_leaks_expected`) and the guard. Its
  variants add `cf_combining` (a zero-width space between "a" and a combining ring, and between "x" and an acute).
  The verify's cold-thread reproduction runs end to end, cold and not.

### Gate (fix round 12)

All steps ran in the worktree with `TMPDIR=fixtures-local/tmp`. Only targeted tests were run (owner rule
2026-10-17). The pytest runs took `/tmp/learnloop-fullsuite.lock`.

| step | result |
|---|---|
| backend fail-before on `1ac5b3ac9` (`git archive` of `src` and `migrations` into `fixtures-local/rw1c-r12-base`, run with this branch's tests and `-o pythonpath=fixtures-local/rw1c-r12-base/src`) | the 16 new cases (the fixed-point test, the guard test, the two cold-thread cases, the 12 `cf_combining` contract cases): **16 failed**. The contract's 72 earlier variants, now scoring exact bytes, pass on both trees |
| `uv run lint-imports --no-cache` | 28 kept, 0 broken |
| targeted pytest, `uv run pytest -n auto` over the 58 files of round 11 | **1,437 passed** (71 s) |
| `--durable-sqlite` on the contract and the new cases | **88 passed** |
| vitest, `src/screens/reader/` and the `ReaderScreen.*.test.tsx` files (no frontend change) | **399 passed** |
| `db_generate_reference.py`, then `db_validate_reference.py` | 0 errors (head 213); no line citation had moved |
| `git diff --check` | clean |

Not run, by the owner rule: the full suite, the whole durability lane and the whole vitest run. Pre-existing and
unchanged: `desktop_validate.py` (`syntheticBook.ts`) and `module_validate.py` (missing module notes). No migration, no
DB or connection change, nothing under `src-tauri` and no configuration key change.

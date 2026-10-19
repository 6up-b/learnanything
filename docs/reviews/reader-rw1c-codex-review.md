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

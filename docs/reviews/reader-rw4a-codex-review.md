# Reader workbench RW4a: Codex review and fixes (stage `reader-rw4a`)

Branch `reader/rw4a` (worktree `learnanything-merge4`). Reviewed range `8eb1ba5d2..95de574aa`
(codex job `20261017-205008-GIiA8v`; the reviewer would not land it yet). Fixes in
`ece5d0786`. No migration, no schema change, no config change; no grading, regrade, replay,
eligibility or scheduling change. RW1b's reader_requests / reader_capture revert and landing
paths and RW6a's recap reads were not touched. No paid or live model calls (fakes only).

## Review

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Library asks bypass held-out selection protection | fixed | `ece5d0786` | `test_library_ask_review.py::test_a_held_out_selection_is_refused_before_any_retrieval[held_out_selection, reading_held_back]` (no `find_sources` call, no row; the library search still asks); vitest `libraryAsk.test.tsx` "a held-out selection's ask says why it was refused (F1)" |
| F2 | High | Comparison quotes are shown without exposure records | fixed | `ece5d0786` | `test_a_comparison_records_exposure_for_every_passage_it_shows` (a counterpart the ask never showed gets a `source_exposure_events` row; a reused comparison shown again records again) |
| F3 | High | Pinned tutor answers bypass the Reader's answer finalization | fixed | `ece5d0786` | `test_the_pinned_tutor_burns_a_reserve_it_reproduces_and_joins_history_and_gaps` (the reproduced reserve is burned and no longer unseen; the exchange is in `reader_dialogue.ask_history`; the `tutor_question` gap job is queued) |
| F4 | High | Follow-ups discard the original ask's practice/cold policy | fixed | `ece5d0786` | `test_a_compare_without_its_session_stays_the_items_practice` (no session: still `pi_eigen_1`'s practice; another session: `caller_mismatch`), `test_the_tutor_grounds_a_bound_asks_pins_under_the_items_filters` (a solution pin is dropped, never in the prompt), `test_the_tutor_refuses_a_bound_ask_while_its_cold_administration_is_open` (tutor and compare refuse `cold_attempt`, no model call) |
| F5 | Medium | Organizer admission can exceed its daily cap | fixed | `ece5d0786` | `test_two_organizer_requests_in_flight_cannot_both_pass_the_cap` (two metered requests, the first held in flight: the second is `capped` with no call), `test_a_subscription_organizer_is_not_refused_by_the_metered_cap` (cap $0, Codex: judged); `test_library_ask.py::test_the_organizers_daily_cap_holds` now uses a metered route (it passed before only because the subscription fake was wrongly refused) |
| F6 | Medium | Background notes block the serial sidecar and cannot be cancelled | fixed | `ece5d0786` | `test_a_blocked_organizer_never_holds_up_the_next_reader_rpc` (while a fake model is blocked: `reader.prompt_contract` and `get_span_view` answer; cancel fences the job; the paid output is kept and reused), `test_every_model_backed_rpc_answers_with_a_job`; vitest "each part runs as a sidecar job…(F6)" and "a pending comparison or tutor answer can be cancelled (F6)" |
| F7 | Medium | Pinned tutor grounding ignores the context budget | fixed | `ece5d0786` | `test_pinned_passages_are_held_to_the_tutors_context_budget` (budget 1,000: the 50,000-character pin trimmed to ≤ 4,000 characters, the second dropped, both on `source_context.delivery`; grounded keys, label and citations are the delivered pin) |
| F8 | Medium | A crash can permanently erase organizer lines from the served result | fixed | `ece5d0786` | `test_a_crash_after_the_ledger_commit_keeps_the_notes_recoverable` (crash between the ledger commit and the notes; the retry is `cached`, pays nothing, recovers the lines from the checkpoint and still drops the line citing another passage), `test_with_no_paid_answer_left_a_cached_line_stays_out_and_is_retried` |
| F9 | Medium | Verification failures are misreported as a one-source comparison | fixed | `ece5d0786` | `test_the_table_carries_unchecked_sources_and_why`; vitest "a verification failure is not called one source…(F9)" |
| F10 | Medium | Library-page practice proposals cannot be selected | fixed | `ece5d0786` | vitest "on the library page, a practice proposal can be picked (F10)" (the pick reaches `onCheckMe` with the answer's first passage and its book's card) |

**Fail-first.** The 15 new backend tests in `tests/test_library_ask_review.py` were run against
the reviewed tip's source (`git archive 95de574aa src migrations` under `fixtures-local/tmp/base`,
`PYTHONPATH` to it, `-o pythonpath=.`): **15 of 15 fail** (F1: no refusal; F2: no exposure row;
F3: no burn, history or gap; F4: the unbound caller, the solution pin grounded, no cold refusal;
F5: the subscription capped, `_OrganizerAdmission` absent; F6: a synchronous answer, the blocked
model holds the loop; F7: `ask_tutor` has no injected answer path and no budget; F8: lines lost;
F9: no `verification`). The new vitest cases depend on the job wire, so they cannot run against
the base frontend; F9 and F10 were reproduced there by the reviewer (in-memory rendering) and are
visible in the base code (`unverifiedSources` ignored; `onPracticePick={null}`).

### What changed, finding by finding

- **F1** — `library_ask.ask_library` checks the held-out partition (`exam_material.held_out_material`:
  the reading held back whole, or a held-out passage among the anchor spans) before any
  `find_sources`, query rewrite, embedding, row or event, and refuses `exam_material` with the
  Reader's own refusal line. This covers Ctrl+Shift+F (its spans are the selection), the palette
  rows and the RPC directly; the library search (no reading anchor) is unchanged. The Reader shows
  the refusal's words instead of "Couldn't look in your books."
- **F2** — `library_ask.compare` takes an injected `record_shown` (the sidecar binds
  `record_shown_spans`, context `library`, entity `library_ask`) and records one exposure row per
  passage the table quotes (each row's passage), every time the table is shown.
- **F3** — `reader_dialogue.ask` gains `source_span_provider` (None: every other Ask, unchanged):
  the pins replace the selection delivery, and the manifest records the spans actually given.
  `library_ask.ask_tutor` takes the Reader's answer path by injection (`ask=`), so the pinned answer
  gets reveal detection, warming and burning, the `learner_question_asked` /
  `reader_answer_submitted` events (the inquiry history), and the sidecar queues its learner-text
  gap (`queue_tutor_question_gap`). Any held-out pin is refused before the call.
- **F4** — The sidecar's `follow_up_caller` rebuilds compare's and the tutor's caller from the
  ask's stored binding (`manifest.caller.item_id`, plus the workbench session id now recorded),
  with today's cold status; a follow-up naming a session bound to another item is refused
  (`caller_mismatch`), and a binding whose item has left the vault fails closed. The tutor refuses
  `cold_attempt`; for a bound ask, `OnlyPinned(..., item=)` grounds the pins under the item's
  practice filters (no exercise, solution, item-linked or answer-reproducing passage).
- **F5** — `library_ask.max_daily_cost_usd` is now a `SharedDailyEnvelope` of its own (envelope
  `library_ask.max_daily_cost_usd` in `source_service_spend`; receipts `library_organizer`; rate
  `source_retrieval.llm_price_per_million`), reserved inside one BEGIN IMMEDIATE transaction per
  metered attempt through `judge_listwise`'s `admit` hook and released when the call is over (its
  receipt then counts by itself). `SharedDailyEnvelope` gains `name`, `owner_kinds` and
  `price_per_million` arguments whose defaults are the service's own cap (unchanged; its spend
  tests pass). The route's billing is resolved first: a subscription route (Codex, the ChatGPT
  plan) is never refused by the metered cap.
- **F6** — The four model-backed RPCs (`reader.library_ask`, `_ask_notes`, `_compare`,
  `_ask_tutor`) start their work on a worker thread (the intent router's pattern, own
  `Repository.attach`, receipts owned as `sidecar_rpc`) and answer at once with a job;
  `reader.library_job` (a wait of at most a second) and `reader.library_job_cancel` are new,
  desktop-only (pinned in `test_mobile_allowlist.py`, Tauri passthroughs). The hook reads each job
  until it is done; *cancel* on the pending notes, compare and tutor lines, Esc (closing the
  pane) and a new ask cancel the jobs in flight, and a cancelled or superseded job never lands.
  Cancelling fences the result; a model call already sent finishes and its receipt and paid
  output are kept (the notes are then reused without a second call), as a cancelled Reader Ask's
  are. A cancelled notes line offers *write the notes ↵*.
- **F7** — `tutor_qa._build_context`'s pinned reader branch runs the pins through `apply_budget`
  at `tutor_qa.context_token_budget` with its receipt on `source_context.delivery`; `ask_tutor`
  reports the delivered pins (`grounded_keys`, `trimmed_keys`), lists a budget-dropped pin in
  `dropped_pins`, and the label counts what was delivered. The citation allowlist is the delivered
  context, so a dropped pin can never be cited.
- **F8** — When the ledger answers `cached` and no stored notes match, `organize` recovers the paid
  answer from the call's own checkpoint (else its completed receipt, `receipt_answer`) and validates
  it again (each line must still cite exactly its own passage). With neither, the lines stay out,
  are marked `unchecked`, and `unchecked_lines` makes the next request try again rather than serve
  the result as final.
- **F9** — `compare_table` carries `verification` (status, why it stopped, sources verified). The
  table says "Not every book's passage could be checked (today's checking budget is used)…" and lists
  each unchecked source as "possible match, not checked" (in a partial comparison too); a true
  single-source result says "Only one of your books has a checked passage on this…".
- **F10** — On the library page, *practice this ▸* is the same learner pick (`onCheckMe`), coming
  back to the answer's first passage; with the workbench on, that passage's book opens so the
  check opens beside it (a detour, as *open* is).

### Claims corrected

- **G19 / follow-ups** now hold for compare and the tutor (F4).
- **The tutor joins learner-text gaps and the inquiry history like an ordinary Reader question**:
  now true (F3).
- **Every model-backed part follows the seven-state contract**: pending now has *cancel* everywhere
  and nothing waits on the request path (F6); verification failures are labelled (F9).
- **The organizer's daily cap holds**: now atomic across threads and processes, subscriptions
  exempt (F5).
- **"Excerpts land before any model call"** (stage record §3 item 2) is withdrawn: the passages land
  before the organizer's call, but the main retrieval is deep search and may use T6's
  `source_query_rewrite` and query embedding first (the stage's smoke run recorded exactly that). It
  now runs off the request path (F6).

### Not changed (recorded)

- `reader.ask` (the Reader's ordinary Ask) is still synchronous on the serial sidecar; it is not
  RW4a's, and its job wire would be a separate change. The jobs mechanism here is reusable.
- The reviewer's spec-conformance notes "ask/peek crumbs and facet-target plumbing missing" carry no
  finding; peek stays a pane layer and *open* a crumb (stage record §3 item 8, open question 1).

## Gate

Run in the worktree with `TMPDIR=fixtures-local/tmp`; `/tmp/learnloop-fullsuite.lock` was not
held. Owner rule 2026-10-17: targeted tests only.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **24 kept**, 0 broken |
| targeted `uv run pytest -n auto -q -p no:cacheprovider` over 214 files (listed below) | **3,852 passed, 2 xfailed**, 0 failed (9 min 28 s) |
| after the F9 test was added: `test_library_ask_review.py`, `test_library_ask.py`, `test_mobile_allowlist.py`, `test_desktop_rpc_contract.py` | **210 passed** |
| `pytest --durable-sqlite` on `test_library_ask_review`, `test_library_ask`, `test_library_ask_expand`, `test_reader_compare_table`, `test_rw4_kill_switches`, `test_reader_find_sources_callers`, `test_source_service_spend_envelopes` | **79 passed** |
| `pytest -m durability` on `test_source_service_spend_envelopes`, `test_source_service_spend_accounting`, `test_library_asks_migration`, `test_tracked_fixture_databases`, `test_coordinated_migrations` | **6 passed** (68 deselected) |
| fail-first: `tests/test_library_ask_review.py` against `95de574aa`'s source | **15 of 15 failed** |
| `npm install`, `npm run typecheck` | ok, exit 0 |
| vitest `src/screens/reader`, `src/screens/ReaderScreen.*.test.tsx`, `src/screens/LibraryPlace.reread.test.tsx` | **47 files, 368 tests passed** (unloaded run; `libraryAsk.test.tsx` 15 including the 5 new, `libraryAskSwitchOff.test.tsx` 4 with its base snapshots unchanged). A first run concurrent with the pytest gate had 4 timing failures (`ReaderScreen.marginMarks`, `.recap`, `.review`, `reader/nextStepFold`, 5 s waits); alone they passed 3 of 3 (37 tests each time) |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | finished, exit 0 (two passthroughs added) |
| references | no schema, config or CLI change: not regenerated; config defaults snapshot, CLI help snapshot, serializer snapshot, desktop RPC contract, mobile allowlist, architecture, table_roles, coordinated migrations and tracked fixture databases ran in the targeted set and pass |

**The 214 pytest files run** (the stage gate's 213, plus `test_library_ask_review` and the
source-service spend files that read `service_spend`):

```text
test_ai_config test_architecture test_attach_to_family test_auto_build_spend_report
test_build_study_map_routing test_canonical_exercise_serialization test_capture_desktop
test_capture_route_recovery test_chatgpt_plan_provider test_chatgpt_plan_workspace test_cli_help_snapshot
test_codex_output_schema test_compare_sources test_config_refactor test_constraint_engine
test_coordinated_migrations test_daily_loop_reader_authored_practice test_daily_loop_reader_retire
test_daily_loop_reference_adoption test_daily_plan_replay test_decider_landing test_desktop_rpc_contract
test_diagnosis_context test_diagnosis_history_modes test_diagnosis_input_provenance_landing
test_diagnosis_input_provenance test_diagnosis_replay test_dialogue_causal_join test_discriminating_search
test_embedding_route_isolation test_exam_protection_identity test_exam_protection test_exam_protection_review
test_exercise_arm test_facet_identity_actions test_facet_locks_landing test_field_config
test_field_signal_production_paths test_find_sources_intents test_forecast_receipts_landing
test_forecast_receipts test_grading_cli test_hypothesis_reference_contract test_import_split_parity
test_instructional_layering test_integration_daily_loop_field test_intervention_outcomes_replayer
test_judge_routes test_key_ladder_labels test_kinship_feature test_learner_pick_proposal
test_learner_text_gaps_composition test_learner_text_gaps_flow test_learner_text_gaps
test_learner_text_gaps_review test_learner_text_source_widening test_library_ask_expand test_library_ask
test_library_ask_review test_library_asks_migration test_mcp_c1a_narrow test_mcp_c1a_review test_mcp_cli
test_mcp_tools test_method_explicit_landing test_method_explicit_upgrade test_migrations
test_misconception_routing test_mobile_allowlist test_model_usage_report test_mvp010_upgrade
test_mvp011_upgrade test_mvp013_upgrade test_mvp014_upgrade test_mvp015_upgrade test_mvp016_upgrade
test_mvp017_route_check_replay test_mvp017_upgrade test_mvp018_upgrade test_mvp020_upgrade
test_mvp021_upgrade test_mvp022_upgrade test_mvp023_upgrade test_mvp024_upgrade test_open_world_gate
test_output_budget test_p0_cutover_mvp08 test_pfc_unverified_unassessed test_pf_generation
test_pinned_span_bridge test_placement_opening_probes test_placement_signals test_plan_determinism
test_practice_availability test_practice_proposal_caller_columns test_prescription_passages
test_probability_cli test_project_cli test_proposal_impressions test_provider_resolution_parity
test_question_context test_question_promotions test_question_signal test_quick_check
test_reader_active_reading test_reader_activity test_reader_adoption_ownership test_reader_authoring
test_reader_branches test_reader_capture test_reader_compare_table test_reader_cues test_reader_dialogue
test_reader_find_sources_callers test_reader_formative_texts test_reader_guidance
test_reader_inquiry_kill_switch test_reader_inquiry_status test_reader_intentions test_reader_intent
test_reader_observation_records test_reader_passage_check test_reader_pdf_selection test_reader_progression
test_reader_quick_check test_reader_recap test_reader_recap_review test_reader_recap_review_r2
test_reader_recap_review_r3 test_reader_reconnect test_reader_reconstruct test_reader_render_views
test_reader_report test_reader_requests test_reader_restoration test_reader_rw1b_final_verify
test_reader_rw1b_fix_round4 test_reader_rw1b_rereview test_reader_rw1b_review test_reader_rw3a_landing
test_reader_workbench_rw2a test_reader_wrap_up test_reading_hardening_landing test_reading_step_switch
test_rebuild_orchestrator test_recurrence_commands test_recurrence_live test_reference_check_binding
test_reference_gate_imports test_registry_audit test_regrade_contract_successor test_regrade_contract_upgrade
test_required_method_authority test_required_method_reopened test_required_method_rereview
test_required_method_round3_final_verify test_required_method_round3 test_required_method_round3_rereview
test_required_method_round3_review test_reread_safety_landing test_reread_safety
test_retrieval_interventions_write_points test_reveal_ledger test_router_r2a_landing test_router_r2a_serving
test_router_r2bc_landing test_route_rules_in_grader test_rw4_kill_switches test_sensitivity_certificates
test_serve_eligibility_review test_shadow_rebuild test_sidecar_queue_serialization test_sidecar_reader_p3
test_sidecar_reader test_sidecar_serializer_snapshot test_sidecar_source_retrieval test_sidecar_teach_back
test_source_block_fts test_source_exercise_import test_source_exercise_rpcs test_source_first_needs
test_source_retrieval_codex_unavailable test_source_retrieval_followup test_source_retrieval_guards
test_source_retrieval_rereview_cost test_source_retrieval_rereview test_source_retrieval_search
test_source_retrieval_tutor test_source_service_spend_accounting test_source_service_spend_envelopes
test_sources_merge_composition test_sources_outcomes_report test_sqlite_file_copies
test_structured_transport_parity test_stuck_prompt test_stuck_prompt_replay test_table_roles
test_tier1_decider test_tool_dispatch_policy test_tool_registry test_tool_results_withhold_answers
test_tools_cli test_tracked_fixture_databases test_tutor_citations test_tutor_delivery_fixes
test_tutor_practice_request test_tutor_promotion_w2 test_tutor_qa test_tutor_tool_requests
test_ux_phase1_connect_ai test_ux_phase1_landing test_ux_phase1_usability_round1 test_ux_phase4_feedback
test_valuation_calibration_fields
```

## Open questions (default taken)

1. Should the Reader's ordinary Ask (`reader.ask`) move to the same job wire? **Default: not in
   RW4a** (it is not this stage's; the mechanism is ready to reuse).
2. A cancelled tutor job's answer is still written (its exchange appears in the inquiry history),
   as a cancelled Reader Ask's is. **Default: keep** (the paid answer exists and the history is
   honest about it); fencing the write itself would need cancellation inside `reader_dialogue.ask`.
3. On the library page with the workbench on, picking a proposal opens the first passage's book.
   **Default: yes** (the check needs its passage beside it); without the workbench the practice
   screen opens with the way back to that passage.

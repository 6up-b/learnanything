# Reader CA2, one Ask: Codex review and fix round

Stage `reader-ca2-one-ask`, branch `reader/ca2-one-ask` in `learnanything-dl2`. The review read
`eae00d58a..cb548afd85` (codex-job `20261025-204600-pjtleU`) and found 3 High, 7 Medium and 1 Low. This round
reproduced each one as a failing test first (the new tests were run against the pre-fix sources of
`cb548afd8`: 15 backend and 8 vitest cases failed there and pass now), then fixed it, or rejected the part that
conflicts with the owner's queue. Fakes only: no live model call, no paid call, no vault opened.

## Review

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Earlier-thread help loses its cost when switching to steps or restarting | fixed | `736469cba`, `ea17b9547` | `test_reader_ca2_codex_review.py`: `test_an_earlier_attempt_opened_before_submit_costs_one_hint_across_a_restart`, `test_the_draft_moved_into_steps_is_counted_once_by_its_submit_whatever_its_key`, `test_a_new_draft_never_inherits_an_earlier_opening`; vitest `PracticeScreen.ca2OneAsk.test.tsx` (the opening is saved on the draft, never in the client's count; restored after a remount) |
| F2 | High | Ask delivers worked answers without the take step | fixed (leak control + take step); strategy routing rejected | `736469cba`, `9b9f7b155`, `ea17b9547` | `test_an_answer_that_gives_the_answer_away_is_withheld_with_the_take_step`, `test_panel_off_the_answer_is_delivered_as_before`, `test_an_ordinary_answer_is_delivered`; vitest `AskOverlay.panel.test.tsx` F2. Rejected part: see below |
| F3 | High | The Reader inline path bypasses the Reader's cold policy | fixed | `736469cba` | `test_a_workbench_question_on_a_cold_item_grounds_nothing_and_follows_the_workbench_rule[True/False]`, `test_the_answer_box_on_a_cold_item_grounds_nothing_too_and_counts_as_practice_does`, `test_off_a_cold_item_the_answer_box_grounds_as_before` (a real open `cold_retry` task, `tests/ad23_fakes.cold_followup`, no mocked predicate) |
| F4 | Medium | Taking worked help first on a cold follow-up makes Submit fail | fixed | `736469cba` | `test_worked_help_taken_first_on_a_cold_follow_up_is_practice_with_help[L4/L5 × on/off]` (end to end: `practice.request_hint` with `takenLevel` 4 or 5 through the hint service, then `submit_attempt`) |
| F5 | Medium | Closing an inline Ask hides its answers from that step | fixed | `ea17b9547` | vitest `AskOverlay.panel.test.tsx` F5 |
| F6 | Medium | One unfinished workbench uses different thread keys in different hosts | fixed | `736469cba`, `ea17b9547` | `test_a_workbench_thread_is_the_same_from_the_practice_steps_and_the_reader`, `test_a_workbench_of_another_item_is_refused` |
| F7 | Medium | The help footer disagrees with the submission fold | fixed | `736469cba`, `ea17b9547` | `test_the_help_record_lists_what_submit_folds_including_an_earlier_serves_question`, `test_a_free_clarification_is_listed_for_its_own_attempt_only`; vitest `PracticeScreen.ca2OneAsk.test.tsx` (the record after a remount) |
| F8 | Medium | The money budget is a three-question count cap | fixed for the subscription route; metered route keeps its request bound | `736469cba`, `ea17b9547` | `test_a_subscription_route_has_no_request_bound_and_a_metered_route_keeps_it`; vitest `AskOverlay.panel.test.tsx` F8. Open part: see below |
| F9 | Medium | "Book first" shows no excerpt and becomes false after reopening | fixed (excerpt, citations, mode restored, excerpt before the explanation); the separate bridge voice is open | `736469cba`, `ea17b9547` | `test_a_cited_passage_carries_its_excerpt_as_provided_and_stores_it`; vitest `AskOverlay.panel.test.tsx` F9 |
| F10 | Medium | Reader working-posture Ask requires an unrelated practice session | fixed | `736469cba`, `ea17b9547`, `d7f157e36` | `test_a_reader_question_with_no_practice_session_still_counts_at_the_submit`; vitest `reader/paletteAskPostures.test.tsx` (item-bound problem, no practice session: Ask opens inline) |
| F11 | Low | The shared keyboard contract differs across hosts | fixed | `ea17b9547`, `d7f157e36` | vitest `AskOverlay.panel.test.tsx` F11, `ReaderScreen.inquiry.test.tsx` (the rail with the panel on) |

### What changed, per finding

* **F1.** Opening *earlier on this question* before Submit is recorded on the draft's checkpoint, keyed by the
  draft's retry key (`save_practice_draft` `earlierOpened`, `sessions._with_earlier_opened`, no schema change),
  the way `hintSeen` already is. The submit's server side counts it (`practice._earlier_opened_hint`, added to the
  question hints `submit_attempt_on` folds) whichever surface submits the draft: the answer box, or the steps it
  moved into (the workbench submit runs before it releases the checkpoint). The client no longer adds it to
  `hintsUsed`, so it never counts twice and never rides `carriedHints`. A restart restores it (`checkpoint_dto`
  `earlierOpened`, and the transcript's `helpRecord.earlierOpened`), and the panel says it is already counted. A
  new draft (new key) never inherits it. The workbench record line counts it too.
* **F2 (K9).** With the panel on, every practice Ask answer passes the hint service's level 1-3 leak control
  (`hints.contracts.leak_flags`, injected by the adapter so `learnloop.tutor` never imports `learnloop.hints`),
  plus the existing overlap threshold, before it is shown. An answer that would give the answer away is withheld:
  the learner gets the ladder's take step inline (*That's worked help ◌ — work a piece of it for me · show me the
  worked answer · or ask something smaller*), which calls the host's own ladder (`useAdaptiveHints.takeWorked` on
  the answer box, `useWorkbenchHelp.take` in steps and the Reader), so worked help is recorded as rung 4 or 5 only
  if taken. Nothing counts or debits for the withheld text (no hint-equivalent, reveal amount 0, citations
  dropped); the row keeps it under `source_context.withheld`, and every read back (transcript, recovery, earlier
  threads, the tutor's own thread) shows the take step instead.
  **Rejected part:** routing strategy questions through the hint service and a model's pre-answer judgment in
  `judgment_ledger`. The spec gives that to H4 ("Recognizing a strategy question to hand to the hint service is
  H4's", §7.5), and H4 waits on its own checkpoint in the owner's queue (H2's owner sign-in and real hint use).
  The leak control and the take step cover K9's acceptance criteria without it: no Ask answer serves worked help.
* **F3 (K7).** The cold status is the server's (`handlers.tutor_qa._item_cold`: an open cold follow-up or a held-out
  exam, `cold_administration_open`, or a "Check once" served cold), for every practice question with the panel
  on. A cold item grounds in nothing (`cold_attempt`, as `reader.ask`), on the answer box and in a workbench. A
  workbench question on a cold item follows the workbench's cold rule: while the one help rule is off (or below
  `mvp-0.34`) every question counts, as `reader.ask`'s predecessor counts; under it only a substantive one. The
  answer box keeps practice's own rule (substantive only) in both.
* **F4 (Q4).** Submit's eligibility input gains `worked_help_taken`, read from the persisted fold (a shown level 4-5
  row of the submission, or an open problem's held worked help), never the client's `primed`. Under the one help
  rule a cold follow-up with worked help taken first is admitted as practice with help (`COLD_CHECK_HELP_TAKEN`,
  claims no task); arbitrary pre-existing priming still refuses, and switched off it refuses as before.
* **F5.** Restored exchanges carry their stored workbench and step (`sourceContext.attemptKey`), so an inline panel
  under a step shows that step's exchanges after a close, remount or restart; the panel at the foot of the steps
  is the whole problem's and shows the attempt's whole thread.
* **F6, F10.** The attempt identity is the server's: a workbench question's key is the answer box's own (when the
  practice screen handed its draft to the steps) or the workbench submit's `workbench:<id>`, and its thread matches
  either key or the workbench (`tutor_qa.attempt_key_matches`), whatever its practice session. The Reader sends no
  key and no practice session; the server applies the workbench submit's own session rule (`_practice_session`:
  the open one, the session's, the most recent open one, else a new one), so the question counts at the submit.
  The transcript takes `workbenchSessionId` and validates it against the item. The Reader's working posture asks
  inline on any item-bound problem, with or without a practice session.
* **F7 (K8).** The transcript returns `helpRecord`: the questions Submit folds (the item's window under the shared
  `hint_window` session rule, including one asked on an earlier serving of the item, labelled so), this attempt's
  free clarifications, the hint service's shown rows under the attempt's key (worked help as worked help with its
  level, which primes rather than counts) and the earlier opening, in order, with `counted` equal to what the
  submit's server side adds. The practice footer is built from it (refreshed on mount, after each answer and
  hint), adding only what the client alone counts (authored hints the server has no row for, the book). The
  submit still folds by the window, unchanged: folding by key would drop the answer box's questions when the
  draft moves into steps (the workbench submit's key differs), and the window never undercounts.
* **F8 (K5).** On a subscription route (Codex, the ChatGPT plan) a practice question has no request bound at all
  (owner, 2026-10-12, Slice A §5 rule 6): `question_usage(metered=False)` returns no limit, `remaining` is null and
  the panel never shows the capped state. Its cost stays estimated from the agent run's token usage
  (`estimated_only`). A metered route keeps the per-item, per-UTC-day request bound (Slice A keeps the
  physical-request bound on metered routes). **Open:** a dollar envelope for a metered tutor route needs a price
  for the tutor (no `tutor_qa.price_per_million` exists, and unknown prices fail closed); left for the owner.
* **F9 (K11).** Each kept citation carries its passage's text as the tutor was given it (`excerpt`, cut to
  `CITATION_EXCERPT_CHARS = 600`, a `keep` display bound), stored with the answer. The panel renders the excerpt,
  then the `§` chips, then *◇ LearnLoop's explanation*; a restored answer keeps its citations, excerpt and mode, so
  it never turns into *Your books don't cover this directly*. **Open:** the separate bridge voice (*◇ connecting it
  to your work*) needs the practice tutor's contract to return one (a prompt and version change); not built.
* **F11 (§7.1).** The docked and inline panels use one multiline box: `↵` sends, `⇧↵` a new line, `^↵` sends too.
  The Reader rail does the same while the panel is on (`AskRail.enterSends`); off, the rail is as before.

Also fixed while running the gate: the stage's own vitest files used `Array.prototype.at`, which the ES2020
`tsconfig` rejects, so `npm run typecheck` failed on them (two lines, `AskOverlay.panel.test.tsx` and
`PracticeScreen.ca2OneAsk.test.tsx`).

### Claims the review said did not hold, now

* *Earlier attempt opened before Submit adds one*: on every surface and after a restart (F1).
* *One help record*: the footer is the server's record of what Submit folds (F7).
* *Money bound per item per UTC day*: no request bound on the subscription route; the metered route keeps a
  request bound, and a dollar envelope is open (F8).
* *Inline panels show their own exchanges*: by their stored step, across close and restart (F5).
* *Book first*: the excerpt leads and survives a reopen (F9); the bridge voice is open.
* *Off restores the predecessor exactly*: the workbench path now follows the workbench's predecessor cold rule
  with the one help rule off (F3).

## Gate (targeted; the full suite runs once in the landing gate)

Every pytest, vitest and npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p
MemorySwapMax=1G`; pytest at `-n 6`, vitest at `--maxWorkers=4`, one test run at a time.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken (a first run broke "deferred cycles are frozen": `learnloop.tutor` importing `learnloop.hints`; the leak control is now injected by the adapter, `9b9f7b155`) |
| reproduction: the new backend tests against `cb548afd8`'s sources | 15 failed (two runs: 9 of the first 14 cases, then F1, F4 and F9 added: 8 of 10); the cases that passed there pin what must stay unchanged |
| reproduction: the new vitest cases against `cb548afd8`'s `AskOverlay.tsx`, `PracticeScreen.tsx`, `ReaderWorkingPosture.tsx` | 8 failed |
| pytest, the new file `tests/test_reader_ca2_codex_review.py` | 25 passed |
| pytest, targeted batch (165 files, below) | 9,935 passed, 10 skipped, 2 xfailed, 5 failed: 3 pinned the request bound this round removes on the subscription route (F8; `test_owner_capture_1025.py` B3 transcript, `test_sidecar_tutor_qa.py` x2), updated (the limit test now pins B3's count cap with the panel off); 2 load flakes that pass alone (`test_chatgpt_plan_provider.py::test_the_deadline_shuts_a_stalled_stream`, `test_plan_first_transport_offer_grants.py::test_p1_after_a_yes_to_one_method_only_its_requests_and_units_use_openrouter`). Rerun of those 4 files plus the new file: 61 passed |
| `npm install`, `npm run typecheck`, `npm run frontend:build` (apps/learnloop-tauri) | done, clean (after the `.at(-1)` fix), built |
| vitest: `src/components/AskOverlay*`, `src/components/DockedAsk*`, `src/screens/PracticeScreen*`, `src/screens/workbench`, `src/screens/practice`, `src/screens/reader`, `src/screens/ReaderScreen*`, `src/screens/FeedbackScreen*`, `src/app` | 148 files, 1,354 passed |
| cargo check | not run: nothing under `src-tauri` changed (no new RPC; `get_tutor_transcript`, `ask_tutor_question` and `save_practice_draft` gained optional fields only) |
| durability lane, DB reference scripts | not run: no migration, no DB or connection code, no schema change (the draft flag lives in the checkpoint's existing JSON envelope) |

**Backend files run** (every test file naming a changed module or function, plus the contracts):

test_ad1_attempt_columns.py test_ad1_codex_review_fixes.py test_ad1_fix_round4.py test_ad1_reading_opportunities.py test_ad23_contract.py test_ad3_dose_arm.py test_ai_config.py test_approach_map_replay.py test_approach_maps.py test_architecture.py test_capture_desktop.py test_capture_route_recovery.py test_chatgpt_plan_provider.py test_chatgpt_plan_workspace.py test_cli_help_snapshot.py test_codex_lockdown_round2.py test_codex_lockdown_round3.py test_codex_output_schema.py test_codex_tool_lockdown.py test_compare_methods.py test_compare_sources_keep.py test_config_refactor.py test_constraint_engine.py test_daily_loop_reader_authored_practice.py test_daily_loop_reader_retire.py test_daily_loop_reference_adoption.py test_desktop_rpc_contract.py test_diagnosis_async_router.py test_diagnosis_card.py test_diagnosis_input_provenance_landing.py test_diagnosis_input_provenance.py test_dialogue_causal_join.py test_dl2_rw4b_keyed_pick_check.py test_e0_delivery.py test_embedding_route_isolation.py test_exam_protection.py test_exam_protection_review.py test_field_signal_production_paths.py test_figure_offers.py test_figures_rw5b_fix_round2.py test_figures_rw5b_review.py test_hint_authored_reveal_ruling.py test_hint_blind.py test_hint_evidence.py test_hint_h2a_review.py test_hint_h2a_review_round2.py test_hint_h2a_review_round3.py test_hint_h2b_fix3.py test_hint_h2b_fix4.py test_hint_h2b_rereview.py test_hint_h2b_review.py test_hint_kill_switch.py test_hint_outcome.py test_hint_report.py test_hint_service.py test_hint_telemetry.py test_integration_daily_loop_field.py test_intent_checks.py test_intent_codex_rereview.py test_intent_codex_review.py test_intent_fix_round4.py test_intent_fix_round5.py test_intent_orchestrator_rulings.py test_intent_plan.py test_item_authoring.py test_judge_routes.py test_learner_text_gaps_composition.py test_learner_text_gaps_flow.py test_learner_text_gaps.py test_learner_text_gaps_review.py test_library_ask.py test_library_ask_review.py test_library_exercises.py test_mobile_allowlist.py test_model_usage_report.py test_output_budget.py test_owner_capture_1025.py test_pf_generation.py test_pinned_span_bridge.py test_placement_opening_probes.py test_placement_sidecar.py test_placement_signals.py test_plan_first_transport_grant_scope.py test_plan_first_transport_offer_grants.py test_plan_first_transport.py test_public_tip_guards.py test_question_context.py test_question_promotions.py test_question_queue.py test_question_signal.py test_quick_check.py test_reader_branches.py test_reader_ca2_codex_review.py test_reader_ca2_one_ask.py test_reader_dialogue.py test_reader_find_sources_callers.py test_reader_inquiry_kill_switch.py test_reader_inquiry_status.py test_reader_intent.py test_reader_reconnect.py test_reader_report.py test_reader_rw1b_review.py test_reader_rw1c_review.py test_reader_rw2b_fix10.py test_reader_rw2b_fix11.py test_reader_rw2b_fix12.py test_reader_rw2b_fix13.py test_reader_rw2b_fix14.py test_reader_rw2b_fix15.py test_reader_rw2b_fix4.py test_reader_rw2b_fix5.py test_reader_rw2b_review.py test_reader_rw3a_landing.py test_reader_tutor_offers.py test_reader_tutor_retrieval.py test_reader_tutor_switch_off.py test_reader_workbench_rw2a.py test_registry_audit.py test_repositories.py test_reveal_ledger.py test_router_offer_log.py test_router_r2a_serving.py test_router_r2bc_landing.py test_rw4_kill_switches.py test_salience_firewall.py test_serve_eligibility.py test_serve_eligibility_review.py test_sidecar_contract.py test_sidecar_item_authoring.py test_sidecar_reader_p3.py test_sidecar_reader.py test_sidecar_registry.py test_sidecar_serializer_snapshot.py test_sidecar_source_retrieval.py test_sidecar_teach_back.py test_sidecar_trace_and_clarification.py test_sidecar_tutor_qa.py test_source_retrieval_followup.py test_source_retrieval_guards.py test_source_retrieval_rereview_cost.py test_source_retrieval_rereview.py test_source_retrieval_search.py test_source_retrieval_tutor.py test_source_space_resolver.py test_structured_transport_parity.py test_stuck_prompt.py test_table_roles.py test_teacher_te0_confidence_events.py test_tool_dispatch_policy.py test_tracked_fixture_databases.py test_tutor_citations.py test_tutor_delivery_fixes.py test_tutor_practice_request.py test_tutor_promotion_w2.py test_tutor_qa.py test_tutor_tool_requests.py test_ux_phase1_connect_ai.py test_ux_phase1_landing.py test_ux_phase1_usability_round1.py test_ux_phase4_feedback.py test_workbench_assistance.py test_workbench_check.py test_workbench_help_kill_switch.py test_workbench_in_session_gaps.py test_workbench_trace.py

No paid or live call was made: every model is a fake, no vault was opened, no provider was routed.

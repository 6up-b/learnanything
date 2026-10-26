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

## Re-review

The re-review (codex-job `20261025-214712-4hpWbY`) read `cb548afd8..113bcadbe`: F3 confirmed fixed, F1 and F2
reopened, and three new findings (2 High, 1 Medium). Each was reproduced first: the new backend tests
(`tests/test_reader_ca2_codex_rereview.py`) were run against `113bcadbe`'s sources (an archive of `src/` put first
on pytest's `pythonpath`, the branch's migrations linked beside it) and the new vitest cases against
`113bcadbe`'s `PracticeScreen.tsx` and `AskOverlay.tsx`, then the fix. Fakes only: no live or paid call, no vault
opened.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | The earlier opening is lost when another item's draft replaces the checkpoint | fixed | `363fc7c1b` | `test_f1_an_opening_carried_into_steps_survives_another_items_draft_and_counts_once` (failed before: the workbench carried 0, the submit recorded 0), `test_f1_a_carried_opening_is_not_counted_again_from_the_draft`, `test_f1_after_steps_the_answer_box_submit_counts_the_carried_opening_once`, `test_f1_a_reader_open_never_takes_the_answer_boxs_opening` |
| F2 | High | Strategy questions still use the ordinary tutor; F12 bypasses the withholding | bypass fixed (F12); strategy routing rejected | `363fc7c1b` | the bypass: F12's tests. Routing: rejected, reason below |
| F3 | High | Cold policy | confirmed fixed by the re-review | `736469cba` | no change |
| F12 | High | Saving a withheld answer exposes it without taking worked help | fixed | `363fc7c1b` | `test_f12_a_withheld_answer_is_never_stored_saved_promoted_or_queued` (failed before: the row held the answer's text), `test_f12_an_ordinary_answer_still_saves_as_a_note`; vitest `AskOverlay.panel.test.tsx` re-review F12 (failed before: *save as note* shown under the take step) |
| F13 | High | The sessionless Reader flow loses assistance accounting across sessions | fixed | `363fc7c1b` | `test_f13_a_sessionless_reader_question_counts_after_its_session_ends_and_the_problem_resumes` (failed before: the submit in session B recorded 0), `test_f13_an_unbound_practice_question_keeps_its_own_session_rule`, `test_f13_the_field_link_reads_the_same_rule` |
| F14 | Medium | Worked help adds a phantom ordinary hint to the footer | fixed | `363fc7c1b` | vitest `PracticeScreen.ca2OneAsk.test.tsx` re-review F14 (failed before with the review's exact line, `help used: a hint · worked help (L4) · practice with help`) |

### What changed, per finding

* **F1.** The checkpoint stays where an answer-box draft's opening lives, but it no longer has to outlive the
  draft: when the practice screen hands the draft to the steps (`workbench.open`, origin `practice` or `plan`, new
  or resumed), the server reads the draft's checkpoint (the practice session the screen now names,
  `practiceSessionId`, else the most recent open one) and, if the draft opened an earlier attempt's help that is
  not carried yet, adds it to the problem's `carried_hints` (the answer box's hints carried into steps, durable on
  `workbench_sessions` whatever later drafts or sessions do; no schema change) and marks the draft's marker
  `carriedTo` the problem. From then on the checkpoint adds nothing (`sessions.draft_earlier_uncarried`), and every
  submit of the item already folds an open problem's carried hints (`hint_fold.combine_held`, the larger of the
  client's count and the problem's), so it counts once from the workbench submit, from an answer-box submit after
  leaving the steps (the screen's count gets the carried hints back), or after item B's draft replaced the
  checkpoint. A later save that resends `earlierOpened` keeps the carried marker; the panel still says *already
  counted*. A Reader open never takes the answer box's opening (that draft may still be submitted from the answer
  box, which then counts it).
* **F12 (and F2's bypass).** A withheld answer's text is never stored: the question row's `answer_md` is the take
  step, and `source_context.withheld` keeps the reason, the leak flags, the take levels and a digest
  (`answer_sha256`, `answer_chars`), as `help_assists` keeps the learner's work. Taking worked help is the ladder's
  rung 4 or 5, which writes its own help, so nothing ever needs the withheld text delivered, and every read path
  (transcript, recovery, earlier threads, the tutor's own thread, the question queue, contamination scans, notes,
  promotions) sees only the take step by construction. `build_tutor_qa_note` and `promote_tutor_question` refuse a
  withheld turn (*That answer was worked help, so it was not shown: take it from the hints instead.*), and the panel
  shows no rating, *save as note* or promotion under a take step.
* **F13.** A practice question a workbench binds (its server-written `source_context.attempt_key.workbench_session_id`)
  now counts in the item's window whatever its practice session, the rule a bound Reader question already follows:
  `hint_window.workbench_bound`, read by `counts_in_session`, `session_clause` (SQL `json_extract` over
  `source_context_json`, so the submit's count, the post-hoc count and the workbench record line agree) and
  `following_attempt` (so the learner field links the question to the attempt that counts it). The thread restored for
  the workbench already matches by the same key in every session (F6), so the count and the thread agree. Rows
  without the key (every row before CA2, and every answer-box question) keep their own session's rule, so replay
  of existing history is unchanged.
* **F14.** The footer reconciles by identity: the help record's hint, check and worked rows carry their
  `help_assists` id (`assistId`), the screen passes its hint entries' ids and levels, and only an entry the record
  does not list is the screen's own: a level 4-5 one is listed as worked help (it primes, never a hint), the rest as
  hints. Without adaptive hints the old subtraction stays (no entries to reconcile).

### Rejected: strategy routing (F2)

Routing a strategy question to the hint service before answering, with a model's judgment in `judgment_ledger`, is
H4's by the spec this stage builds: §7.5 says *"Recognizing a strategy question to hand to the hint service is H4's
(hints §4.1)"*, and H4 waits on its own checkpoint in the owner's queue (H2's owner sign-in and real hint use). K9's
acceptance criteria are met without it: every practice Ask answer passes the hint service's level 1-3 leak control
before it is shown, and an answer that would give the answer away returns the rung 4/5 take step, recorded as that
rung only if taken; with F12 fixed, no path delivers the withheld text. The tutor's `question_type` stays the
model's judgment with its receipt on the event (model, prompt version, agent run).

### Re-review gate (targeted; the full suite runs once in the landing gate)

Every pytest, vitest and npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p
MemorySwapMax=1G`; pytest at `-n 6`, vitest at `--maxWorkers=4`, one test run at a time.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| reproduction: `tests/test_reader_ca2_codex_rereview.py` against `113bcadbe`'s `src/` (`-o pythonpath=<archive>/src`) | the three scenario tests failed as the review describes (F1: carried 0; F12: the row held the answer's text; F13: the session-B submit recorded 0); the cases pinning what stays unchanged passed or failed only on the new RPC field / helper |
| reproduction: the new vitest cases against `113bcadbe`'s `PracticeScreen.tsx` and `AskOverlay.tsx` | 2 failed (F14 with the review's exact line; F12 *save as note* shown), restored after |
| pytest, `tests/test_reader_ca2_codex_rereview.py` | 9 passed |
| pytest, targeted batch (202 files, below) | 10,970 passed, 13 skipped, 2 xfailed, 0 failed (644 s) |
| `npm install`, `npm run typecheck`, `npm run frontend:build` (apps/learnloop-tauri) | done, clean, built |
| vitest: `src/components/AskOverlay*`, `src/components/DockedAsk*`, `src/screens/PracticeScreen*`, `src/screens/workbench`, `src/screens/practice`, `src/screens/reader`, `src/screens/ReaderScreen*`, `src/screens/FeedbackScreen*`, `src/app` | 148 files, 1,357 passed |
| cargo check | not run: nothing under `src-tauri` changed (`workbench.open` gained one optional field) |
| durability lane, DB reference scripts | not run: no migration, no DB or connection code, no schema change (the carry uses `workbench_sessions.carried_hints` and the checkpoint's JSON envelope; the window rule reads the existing `source_context_json`) |

**Backend files run** (the previous round's 165, every test file naming a changed module or function, the
learner-field tests, and the contracts):

test_ad1_attempt_columns.py test_ad1_codex_review_fixes.py test_ad1_fix_round4.py test_ad1_reading_opportunities.py test_ad23_contract.py test_ad23_fix_r8.py test_ad23_fix_review.py test_ad23_owner_decisions.py test_ad3_dose_arm.py test_ai_config.py test_answer_signal_arms.py test_approach_map_replay.py test_approach_maps.py test_architecture.py test_assumed_known.py test_capture_desktop.py test_capture_route_recovery.py test_chatgpt_plan_provider.py test_chatgpt_plan_workspace.py test_cli_help_snapshot.py test_codex_lockdown_round2.py test_codex_lockdown_round3.py test_codex_output_schema.py test_codex_tool_lockdown.py test_compare_methods.py test_compare_sources_keep.py test_config_refactor.py test_constraint_engine.py test_coordinated_migrations.py test_daily_loop_reader_authored_practice.py test_daily_loop_reader_retire.py test_daily_loop_reference_adoption.py test_daily_plan_composition.py test_daily_plan_owner_decisions.py test_desktop_rpc_contract.py test_diagnosis_async_router.py test_diagnosis_card.py test_diagnosis_input_provenance_landing.py test_diagnosis_input_provenance.py test_dialogue_causal_join.py test_dl2_rw4b_keyed_pick_check.py test_e0_delivery.py test_embedding_route_isolation.py test_eval_harness.py test_exam_protection.py test_exam_protection_review.py test_facet_outcome_view.py test_family_evaluation.py test_family_memory_projection.py test_field_boundaries.py test_field_cli.py test_field_priors.py test_field_signal_production_paths.py test_field_split_outcomes.py test_field_workbench_signals.py test_figure_offers.py test_figures_rw5b_fix_round2.py test_figures_rw5b_review.py test_held_grade_composition.py test_hint_authored_reveal_ruling.py test_hint_blind.py test_hint_evidence.py test_hint_h2a_review.py test_hint_h2a_review_round2.py test_hint_h2a_review_round3.py test_hint_h2b_fix3.py test_hint_h2b_fix4.py test_hint_h2b_rereview.py test_hint_h2b_review.py test_hint_kill_switch.py test_hint_outcome.py test_hint_report.py test_hint_service.py test_hint_telemetry.py test_integration_daily_loop_field.py test_intent_checks.py test_intent_codex_rereview.py test_intent_codex_review.py test_intent_fix_round4.py test_intent_fix_round5.py test_intent_orchestrator_rulings.py test_intent_plan.py test_interaction_signals.py test_item_authoring.py test_judge_routes.py test_learner_text_gaps_composition.py test_learner_text_gaps_flow.py test_learner_text_gaps.py test_learner_text_gaps_rereview.py test_learner_text_gaps_review.py test_library_ask.py test_library_ask_review.py test_library_exercises.py test_lo_general.py test_mobile_allowlist.py test_model_usage_report.py test_output_budget.py test_owner_capture_1025.py test_pfc_unassessed_readers.py test_pfc_unverified_unassessed.py test_pf_generation.py test_pinned_span_bridge.py test_placement_opening_probes.py test_placement_sidecar.py test_placement_signals.py test_placement_split_grades.py test_plan_first_transport_grant_scope.py test_plan_first_transport_offer_grants.py test_plan_first_transport.py test_predictor_interface.py test_probability_arms.py test_probability_prep.py test_public_tip_guards.py test_question_context.py test_question_promotions.py test_question_queue.py test_question_signal.py test_quick_check.py test_reader_branches.py test_reader_ca2_codex_rereview.py test_reader_ca2_codex_review.py test_reader_ca2_one_ask.py test_reader_dialogue.py test_reader_find_sources_callers.py test_reader_inquiry_kill_switch.py test_reader_inquiry_status.py test_reader_intent.py test_reader_observation_records.py test_reader_reconnect.py test_reader_report.py test_reader_rw1b_review.py test_reader_rw1c_review.py test_reader_rw2b_fix10.py test_reader_rw2b_fix11.py test_reader_rw2b_fix12.py test_reader_rw2b_fix13.py test_reader_rw2b_fix14.py test_reader_rw2b_fix15.py test_reader_rw2b_fix4.py test_reader_rw2b_fix5.py test_reader_rw2b_review.py test_reader_rw3a_landing.py test_reader_tutor_offers.py test_reader_tutor_retrieval.py test_reader_tutor_switch_off.py test_reader_workbench_rw2a.py test_rebuild_orchestrator.py test_recurrence_merge_composition.py test_registry_audit.py test_repositories.py test_reveal_ledger.py test_router_offer_log.py test_router_r2a_serving.py test_router_r2bc_landing.py test_rw4_kill_switches.py test_salience_firewall.py test_serve_eligibility.py test_serve_eligibility_review.py test_sidecar_contract.py test_sidecar_item_authoring.py test_sidecar_reader_p3.py test_sidecar_reader.py test_sidecar_registry.py test_sidecar_serializer_snapshot.py test_sidecar_source_retrieval.py test_sidecar_teach_back.py test_sidecar_trace_and_clarification.py test_sidecar_tutor_qa.py test_source_retrieval_followup.py test_source_retrieval_guards.py test_source_retrieval_rereview_cost.py test_source_retrieval_rereview.py test_source_retrieval_search.py test_source_retrieval_tutor.py test_source_space_resolver.py test_structured_transport_parity.py test_stuck_prompt.py test_stuck_prompt_replay.py test_success_head_cli.py test_success_head.py test_table_roles.py test_teacher_te0_confidence_events.py test_tier1_decider.py test_tool_dispatch_policy.py test_tracked_fixture_databases.py test_tutor_citations.py test_tutor_delivery_fixes.py test_tutor_practice_request.py test_tutor_promotion_service.py test_tutor_promotion_w2.py test_tutor_qa.py test_tutor_tool_requests.py test_ux_phase1_connect_ai.py test_ux_phase1_landing.py test_ux_phase1_usability_round1.py test_ux_phase3_today.py test_ux_phase4_feedback.py test_workbench_assistance.py test_workbench_check.py test_workbench_help_kill_switch.py test_workbench_in_session_gaps.py test_workbench_trace.py 

No paid or live call was made: every model is a fake, no vault was opened, no provider was routed.

## Fix round (orchestrator)

The final verify (codex-job `20261025-222152-BNsrcW`, `113bcadbe..4e9b92d4f`) confirmed F3 and F13 fixed and
reopened F1, F2, F12 and F14, with one new finding, F15 (High). The orchestrator's rulings (the owner's
proportionate bar): fix F15, F1, F12 and F14; F2's strategy routing is ruled Low and out of scope (H4's, adaptive
hints §4.1), recorded as open. One owner decision was applied in the same round (2026-10-26): the practice Ask budget
stays per attempt. Every fix is fail-first: the new backend tests (`tests/test_reader_ca2_fix_orchestrator.py`) and
vitest cases failed on the previous tip's sources (`4e9b92d4f`, and for the two later items the tip before them, run
from an archive of `src/` and `migrations/` put first on pytest's `pythonpath`), then passed. Fakes only: no live or
paid call, no vault opened.

| id | severity | title | verdict | test |
|---|---|---|---|---|
| F15 | High | Carrying an earlier opening into steps reveals an authored hint on the way back | fixed | `test_f15_an_earlier_opening_carried_into_steps_is_not_an_authored_hint` (failed before: `carriedHints` 1), `test_f15_authored_reveals_and_the_opening_are_carried_apart`, `test_f15_after_steps_the_answer_box_submit_counts_the_reveals_and_the_opening` (failed before: 2, not 3), `test_f15_the_help_record_still_counts_a_carried_opening_after_another_items_draft`, `test_f15_an_abandoned_problem_never_takes_the_opening_with_it` (a regression of this round's first cut, caught before the verify: failed with 0); vitest `PracticeScreen.ca2OneAsk.test.tsx` "fix round F15" (failed before: *help used: nothing yet*, the opening lost on the way back) |
| F1 | Medium | A resume swallows a second distinct event | fixed | `test_f1_a_resume_after_carried_reveals_counts_a_new_opening_too` (failed before: 1, not 2), `test_f1_the_opening_counts_once_however_often_the_problem_resumes`; the re-review's F1 tests now read the two components |
| F12 | Low | The question queue returns a stored withheld answer's text | fixed | `test_f12_a_stored_withheld_answer_reaches_the_queue_only_as_its_take_step` (failed before: the raw text in the queue) |
| F14 | Low | The no-record footer calls worked help "a hint" | fixed | vitest "fix round F14: without the record, the screen's entries are classified by level too" (failed before: `help used: a hint`) |
| F2 | Low (ruled) | Strategy routing | open, out of scope | H4's (hints §4.1); the bypass half stays fixed (F12) |
| owner 2026-10-26 | n/a | The practice Ask budget is per attempt | applied | `test_each_attempt_gets_its_own_practice_budget_on_every_route[subscription, metered]` (failed before: unbounded on the subscription route, the day's count on the metered one), `test_the_practice_thread_and_its_budget_are_keyed_by_the_attempt` (failed before), B3's `test_b3_a_reattempt_starts_a_fresh_ask_thread` restored as at `eae00d58a` (failed on the previous tip: `remaining` None), and `test_tutor_qa.py`'s and `test_sidecar_tutor_qa.py`'s limit tests restored as at `eae00d58a` |

### What changed

* **One component model (F15, F1).** An attempt's help has four components, each counted once: the answer box's
  authored reveals (the client's `hintsUsed`, carried into steps as `workbench_sessions.carried_hints`, which is the
  answer box's reveal index on the way back and nothing else), the book left open (`source_shown_at`), an earlier
  attempt's help opened before Submit, and the questions the server folds. The earlier opening now has its own column,
  **migration 221** `workbench_sessions.earlier_opened_at` (LIFECYCLE state on a WORKFLOW table, set once; NULL on
  every older row). `workbench.open` from the practice screen sets it when the draft's checkpoint holds the opening,
  and never adds it into `carried_hints` (so a resume's max over the authored reveals cannot swallow it, and the
  answer box never reveals an authored hint for it). The server counts it with one read,
  `practice._earlier_opened_hint`: 1 when the draft's checkpoint holds the opening under its current key **or** an
  open problem of the item carries it, ORed (one opening per attempt), read by the answer-box submit, the workbench
  submit, the help record and the workbench record line (which names it, *an earlier attempt's help*). The view sends
  `earlierOpened`; the answer box, back from steps, marks the opening counted (`earlierCountedFor`) without touching
  `hintsUsed`, so its footer says it and its submit sends only the authored reveals.
* **F12.** `list_question_queue`, the Reader dialogue's prior exchanges and branch thread, and a promotion's
  steering thread read `delivered_answer_md`, so a withheld row stored before the take step was (an earlier build's
  raw text beside the `withheld` marker) reads as its take step on every learner-facing and model-facing read.
* **F14.** `helpRecordLine`'s no-record branch classifies the screen's entries by level, as the record branch does.
* **The practice Ask budget (owner, 2026-10-26).** `question_usage` counts the attempt's thread
  (`practice_thread_events`, keyed by the attempt's submission id or the unfinished workbench the server names while
  the panel is on, B3's window when it is off) against `max_questions_practice` on every route. K5's per-item,
  per-UTC-day bound and F8's unbounded subscription route are withdrawn (`_tutor_route_subscription` removed); the
  transcript reads the budget with the same keys as the thread it shows, and a capture's recovered question with its
  stored attempt key. The spec's K5 row carries the decision.
* **Head fixture and pins.** `fixtures/migration_head_221/` is a backup-API copy of `migration_head_220` with only
  221 applied (`wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE`, header bytes 1/1, `integrity_check` ok,
  `foreign_key_check` empty, no companion files; its README says so). The head pins in the migration tests, the two
  reference scripts (`SCHEMA_HEAD = 221`) and the successor pin in `test_regrade_contract_upgrade.py` (stale on the
  branch since CA2's own `mvp-0.34`; it now reads `ONE_ASK_ALGORITHM_VERSION`) moved. The reference generator now
  names CA2's `ask` config section (it failed with `KeyError: 'ask'` before, a gap since CA2's config), and the
  prose leaf counts read 1,050 leaves in 71 sections. References regenerated; the validator reports no error.

### Numbers for the landing

* **Migration**: 221 on this branch. Main already holds 221 (the learner-claim fixes) and curriculum C0a's 222 lands
  first, so the landing renumbers this one (223 or later) and rebuilds the head fixture from main's.
* **Successor**: `mvp-0.34` on this branch, unchanged. fix/rebuild-equivalence also claims `mvp-0.34` and lands
  before this stage, so the landing renumbers CA2's successor too.

### Fix-round gate (targeted; the full suite runs once in the landing gate)

Every pytest, vitest and npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p
MemorySwapMax=1G`; pytest at `-n 6`, vitest at `--maxWorkers=4`, one test run at a time. Scripts outside pytest ran
under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

| Check | Result |
|---|---|
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| pytest, every test file naming the migration runner or the head fixture (84 files) | 1,289 passed, 7 skipped; 4 failed, each a head pin this round moved (two migration diffs, the 219 column order, and the stale successor pin), fixed and rerun green, durability lane included |
| pytest, the re-review's 202-file batch plus this round's files (205 files) | 11,033 passed, 13 skipped, 2 xfailed, 0 failed (794 s) |
| pytest, the CA2 and workbench files after the abandon fix (8 files) | 182 passed |
| `db_generate_reference.py`, `db_validate_reference.py` | regenerated; `errors: []` |
| `npm run typecheck`, `npm run frontend:build` | clean, built |
| vitest: `src/components/AskOverlay*`, `src/components/DockedAsk*`, `src/screens/PracticeScreen*`, `src/screens/workbench`, `src/screens/practice`, `src/screens/reader`, `src/screens/ReaderScreen*`, `src/screens/FeedbackScreen*`, `src/app` | 148 files, 1,359 passed |
| cargo check | not run: nothing under `src-tauri` changed |

### Open

* F2's strategy routing (H4's).
* An earlier opening carried onto a problem stays held while that problem is open, so a later attempt of the item
  submitted from the answer box while the problem is still open counts it too: the same held rule the problem's
  carried authored hints and book already follow (RW2a review F2), not a new one.

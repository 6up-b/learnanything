# Reader CA2: one Ask panel

Stage `reader-ca2-one-ask`, branch `reader/ca2-one-ask` in `learnanything-dl2`, base `eae00d58a` (main with RW7b
`mvp-0.32`, mobile PR-1, the owner-capture 1025 fixes = CA0, the Reader Compare/Ask and curriculum specs). Spec:
`docs/specs/ux_reader_compare_ask_v1.md` §7 (CA2), §11 K5-K11, §13 (the successor ruling and the kill switches) and §15
Q1-Q6 (owner decisions 2026-10-25). Fakes only: no live model call, no paid call, no vault touched.

## 1. The successor ruling (§13, K10): yes, `mvp-0.34`

The task's rule: if the unified rule changes an attempt's classification beyond today's `hints_used` meaning, stop and
make it a successor. Two of CA2's rules do, so they ship as one successor with one kill switch; everything else is
presentation or keeps the existing meaning and ships behind the panel's own switch with no tag.

| Rule | Today (`mvp-0.32`) | CA2 | Classification change? |
|---|---|---|---|
| **K10, the Reader's cold Ask** (`tutor_qa.py`'s bound row, `reader_dialogue`'s cold link row) | every cold question is hint-equivalent (L6), whatever its `question_type` | only a substantive one (`HINT_EQUIVALENT_TYPES`), as practice already does | **yes**: a cold check with a Reader clarification question stays *on your own* instead of becoming practice with help |
| **Q4, help on a cold follow-up** (`cold_retry`, `certification_cold_probe`) | submit refuses a hinted attempt (`COLD_CHECK_ASSISTED`), so the simple shell withholds hints ("No hints on this one") | the take step; submit admits the attempt as practice with help | **yes**: an attempt the predecessor refused is now recorded (assisted), and what submit admits changes |
| K6, *earlier on this question* opened before Submit | (no such door) | one hint-equivalent, said first | no: `hints_used` += 1 with its existing meaning (the book-left-open rule, spec §5.4) |
| Practice Ask's own rule (§7.7) | substantive questions count | the same | no |

So: `ONE_ASK_ALGORITHM_VERSION = "mvp-0.34"` (one constant, after RW7b's `mvp-0.32`; the LP claim fixes hold `mvp-0.33`
on their branch), `ONE_ASK_VERSIONS`, `learnloop upgrade --to mvp-0.34` (`learnloop/one_ask_upgrade.py`, RW7b's chained
pattern: the predecessor, or `mvp-0.9` onwards through the chain; anything older refused), the defaults snapshot, and
the kill switch **`ask.cold_help_converts`** (default true). Below the tag, or switched off, both rules are the
predecessor's exactly (`serve_eligibility.help_converts_active`).

**Persisted meaning.** Nothing recorded is rewritten or re-read under the new rule: replay reads the stored
`question_events.hint_equivalent` and `practice_attempts.hints_used`, never the rule. The one place an assisted attempt
could now meet a cold measurement (the repair cold retry's and the certification probe's consumers) skips it
unconditionally (`remediation.assisted_attempt`); before the successor submit refused such an attempt, so no recorded
attempt reaches that branch and replay is unchanged. The projection, scoring weights and FSRS are untouched: an
assisted attempt is dampened by its `hints_used` as any hinted attempt is.

## 2. What changed

### Backend

* **Q4, help converts a cold follow-up** (`serve_eligibility._decide_submit`, `attempts.submit_decision`): under the
  rule, a hinted submit on a due cold follow-up is `SERVE` with reason `COLD_CHECK_HELP_TAKEN`, claims no task (the cold
  measurement is not answered by an assisted attempt), primed or not (the help may have shown the answer). With no help
  taken, every predecessor refusal stands (a primed or auto-primed unassisted draft is still refused). The consumers
  (`remediation.record_remediation_attempt`, `certification_cold_probe._record_probe_outcome`) leave the task open for
  an assisted attempt; the next serve withdraws it with the existing typed disposition
  (`COLD_CHECK_PRACTISED_SINCE_SCHEDULED`, causal outcome `unmeasurable_no_held_out_surface`).
* **The take step on a cold follow-up** (`intent.checks`): `served_check` no longer serves a "Check once" on a cold
  follow-up item in the measured view (no help offered) under the rule, and `cold_followup_view` gives a due cold
  follow-up with no "Check once" the cold view (the banner, the ladder header, locators hidden until feedback, D46).
  The practice serve attaches it as `intentCheck` (`handlers/practice.py`).
* **K10** (`reader_modes.BoundAsk.cold_counts_every_question`, set by `handlers/reader_tutor.bound_ask`;
  `reader_dialogue.ask` and `_record_cold_hint_equivalent`): under the rule a cold Ask counts only when substantive; the
  cold link row stores the tutor's `question_type` instead of `other`. Leak overlap still writes its reveal row whatever
  the type (unchanged code).
* **K5, the attempt's thread** (`tutor_qa.practice_thread_events(submission_id=)`, `ask_question(submission_id=,
  workbench_session_id=, about_step=)`): a practice question stores `source_context.attempt_key` when it is asked (no
  migration: `source_context_json`); the thread, the turns the tutor is given and the transcript are the submission's.
  A question recorded before CA2 has no key and keeps B3's window rule. **The budget** is a money bound per item per UTC
  day while the panel is on (K5: "its window doesn't reset per serve"; B3 had made it per attempt).
* **K7** (`handlers/tutor_qa._ask_panel_inputs`): `ask_tutor_question` takes `submissionId`, `workbenchSessionId`
  (refused unless that workbench session is bound to the question's item), `aboutStep` (said to the tutor with the
  steps) and a one-question `answerMode`. Policy and counts stay the server's.
* **§7.4, the help style is the answer mode** (`tutor_qa.HELP_STYLE_ANSWER_MODES`): *let me struggle* → ask me first,
  *balanced* → help me reason, *guide me* → answer directly. The adapter resolves the mode from `hints.help_style` (a
  workbench session's per-problem style wins, D31) for practice and feedback, and the Reader's `reader.ask` uses it when
  the client sends none (Q5). The practice prompt gains `_TUTOR_QA_PRACTICE_MODE_TASKS` (every mode inside the practice
  context's leak control) and the version suffix `+answer-mode-v1`; with no mode the prompt and version are today's.
  The answer's mode is stored on the row (`question_events.answer_mode`; AD's reading sweep reads only reader and
  library rows, so nothing reads practice rows' mode) and returned.
* **The receipt** (§7.5): every Ask answer's `source_context.receipt` names the model, prompt version and agent run its
  `question_type` came from (the question event lacked them).
* **K6, earlier on this question** (`tutor_qa.earlier_threads`, `handlers/tutor_qa._earlier`): the practice and feedback
  transcripts carry the item's earlier attempts' help, newest first (each attempt with a date, how it ended in the
  evidence vocabulary, its questions and its hints), `earlierCountsAsHint` (practice: true; feedback: false) and
  `cold` (server-derived: a cold "Check once" or a due cold follow-up; then the list is empty). Nothing earlier enters
  any model context (C6).
* **Config**: `[ask] panel_enabled` (the presentation's switch, no tag) and `cold_help_converts` (the successor's),
  both classified in `parameter_registry` (structural kill switches: the model's typed `question_type` decides, no new
  weight, margin or threshold). The app snapshot sends `ask` only while the panel is on. One guardrail constant,
  `tutor_qa.EARLIER_THREADS_LIMIT = 20`, labelled `keep` (a display bound on how much history one panel loads).

### Frontend (`apps/learnloop-tauri/src`)

* **One component, three hosts** (`components/AskOverlay.tsx`, `variant`): `modal` (the library, capture and Reader
  overlay contexts keep it), `docked` (practice and feedback: `components/DockedAsk.tsx`, a 360 px column, resizable
  and remembered, a sheet over the lower half below 1,040 px) and `inline` (under the focused workbench step). The panel
  parts: the context line with chips (`about › Exercise 6.1.12 · your draft ×`, `step 3 · your steps 1–4`, *ⓘ what's
  sent*), the stored help style (`components/askPanel.tsx`, `StoredHelpStyle`), the thread with one voice label per
  answer (`◇ model · about step 3 · helping you reason · counts as a hint` / `a clarification · free` / on a cold check
  `counts as help` / `a clarification · still on your own`), book first (`§ from your books` chips, else *Your books
  don't cover this directly — this is LearnLoop's model's explanation*), the box with the cost said before sending, *change*
  for one question's mode, and *earlier on this question ▸ · opening one counts as a hint*. Esc closes the panel, never
  the screen; ↵ in the box never reaches the screen's ^↵.
* **The practice screen** docks the panel instead of App's overlay, and in Work in Steps `?` (and the palette, and
  "ask about this step · ?") opens it inline under the focused step (`Workbench.renderAsk`, `askSignal`); a question
  about the whole problem sits at the foot of the steps. The live draft (or the steps) is read when the question goes.
  The help record line (`helpRecordLine`, K8) lists hints, the book left open, an earlier attempt's help and each
  question with its cost; in steps the questions join the workbench's footer. An earlier attempt opened before Submit
  adds one to the submitted `hintsUsed` (as the book does), once per submission key, and never to `authoredHints`.
* **Cold** (§7.7): the banner changes to *Practice with help ◌ — you asked about the maths* only after a substantive
  answer; a cold follow-up served with the take step (Q4) offers Hint through the ladder's header instead of "No hints on
  this one" (without it, the predecessor's copy and behaviour stand).
* **The Reader** (Q5): the rail's mode select is replaced by the help style (one stored preference); the Reader's
  working posture asks inline under a step when the problem is bound to an item in a practice session, instead of
  *"Ask the tutor is beside the book. Leave for now…"*. Feedback's Ask docks beside feedback (and no longer counts as an
  overlay covering the answer).
* **The hint panel** shows *help style: …* beside its `⋯` menu (C7).

## 3. Not built in this stage (open questions)

* **K9, a request for the answer through the take step.** Recognizing "just show me" before answering needs a model's
  typed judgment logged in `judgment_ledger` (§7.5) or H4's strategy routing; neither exists yet. The practice context's
  Socratic prompt and leak overlap accounting apply to every Ask answer as before.
* **Strategy questions answered by the hint service (H4)** and the workbench's *help so far ▸* thread in the help
  column: not built (H4 waits on its own checkpoint). Inline panels show their own exchanges; the docked panel shows the
  attempt's whole thread.
* **The diagnostic block's one line** (*Ask opens after this short set · your question is kept*): Ask stays hidden and
  refused during a diagnostic block, as today.
* **The earlier-attempt count across a restart.** It is client-counted (like the book left open, with no new ledger
  kind: `interaction_events.kind` and `help_assists.assist_kind` are CHECK-constrained, so a durable row needs a
  migration). A restart mid-attempt forgets that it was opened; opening it again counts it again (the link says so).
* **The submit's fold still counts by the window.** A question asked under one serve's key, the item skipped and served
  again with a new key, folds into the next attempt on the item (B3's window, unchanged evidence semantics), though the
  new serve's thread starts empty. Folding by key would change classification again (another successor); left as is.
* **The help record** lists the questions answered in this visit; a thread restored from the transcript after a
  remount is shown in the panel but not re-listed in the record line.
* **The successor's number.** `fix/rebuild-equivalence` (`c8a138009`) also names its bounded-replay successor
  `mvp-0.34`. Both are one constant; whichever lands second renumbers (and moves its predecessor).
* **Q4's measurement.** An assisted cold follow-up leaves its measurement to be withdrawn at the next serve (the repair
  ends unmeasurable, honestly). Whether a fresh cold retry should be scheduled instead is a scheduling decision for the
  owner.

## 4. Gate (targeted; the full suite runs once in the landing gate)

Every command ran in `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`; pytest at `-n 6` or
fewer, vitest at `--maxWorkers=4`, one test run at a time.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | 36 kept, 0 broken |
| pytest, the new file `tests/test_reader_ca2_one_ask.py` | 30 passed |
| pytest batch 1 (35 files: the successor's chain pins and the contracts, below) | 1,258 passed, 14 skipped, 5 failed (chain-tail pins and the CLI help snapshot this stage moves); fixed, then the 5 files plus `test_ad_guard.py`, `test_ad_protected_tables.py`, `test_architecture.py`, `test_reader_ca2_one_ask.py`, `test_sidecar_tutor_qa.py`, `test_capture_route_recovery.py`: 217 passed, 3 skipped |
| pytest batch 2 (151 files that exercise a changed module, below) | 8,948 passed, 3 skipped, 2 xfailed, 6 failed; fixed (B3's budget assertion is K5's now; two tests of other things pin the panel off; the recovered capture answer carries its mode; RW1c's golden strips the new receipt), then the 6 files: 119 passed, and `test_reader_tutor_switch_off.py` 2 passed |
| `npm install`, `npm run typecheck`, `npm run frontend:build` (apps/learnloop-tauri) | clean, clean, built |
| vitest, new: `src/components/AskOverlay.panel.test.tsx`, `src/screens/PracticeScreen.ca2OneAsk.test.tsx` | 12 passed, 7 passed |
| vitest, touched (148 files: `src/components/AskOverlay*`, `src/screens/PracticeScreen*`, `src/screens/workbench`, `src/screens/practice`, `src/screens/reader`, `src/screens/ReaderScreen.workbench`, `.inquiry`, `.inquiryOff`, `src/screens/FeedbackScreen*`, `src/app`) | 1,341 passed, 5 failed: all in `src/app/App.fixRound4.test.tsx`, 5 s timeouts under the parallel load; alone 9 passed |
| cargo check | not run: nothing under `src-tauri` changed (no new RPC; `ask_tutor_question` and `get_tutor_transcript` are passthroughs) |
| durability lane, DB reference scripts | not run: no migration, no DB or connection code, no schema change (`source_context_json` and `answer_mode` already exist) |

**Batch 1:** `test_ad23_successor.py test_field_workbench_signals.py test_intent_codex_rereview.py
test_method_explicit_upgrade.py test_mvp09_upgrade.py test_mvp010_upgrade.py test_mvp011_upgrade.py
test_mvp013_upgrade.py`-`test_mvp018_upgrade.py test_mvp020_upgrade.py`-`test_mvp024_upgrade.py
test_reading_step_switch.py test_recurrence_commands.py test_regrade_contract_successor.py
test_required_method_grading.py test_route_rules_in_grader.py test_serve_eligibility_review.py
test_serve_eligibility.py test_plan_follows_path.py test_config_refactor.py test_cli_help_snapshot.py
test_sidecar_serializer_snapshot.py test_sidecar_contract.py test_desktop_rpc_contract.py test_mobile_allowlist.py
test_architecture.py test_table_roles.py test_constraint_engine.py`.

**Batch 2** (every test file naming `tutor_qa`, `reader_modes`, `reader_dialogue`, `reader.ask`, `served_check`,
`intent.checks`, `config_dto`, `tutor_qa_prompt`, `certification_cold_probe`, `remediation`, `ask_tutor_question`,
`get_tutor_transcript`, `BoundAsk` or `reader_tutor`, less those in batch 1): test_ad1_attempt_columns.py test_ad1_codex_review_fixes.py test_ad1_fix_round4.py test_ad1_reading_opportunities.py test_ad23_contract.py test_ad3_dose_arm.py test_adaptive_difficulty_ad1.py test_ai_config.py test_assumed_known.py test_authoring_contract.py test_capture_desktop.py test_capture_route_recovery.py test_causal_attribution_p0.py test_causal_attribution_p2.py test_causal_cold_outcomes.py test_causal_factor_deferral.py test_causal_orchestrator.py test_causal_p2_acceptance.py test_causal_repair_sidecar_rpcs.py test_certification_cold_probe.py test_chatgpt_plan_provider.py test_chatgpt_plan_workspace.py test_codex_lockdown_round2.py test_codex_lockdown_round3.py test_codex_output_schema.py test_codex_tool_lockdown.py test_coldness_receipt.py test_collection_dataset.py test_common_repair_delivery.py test_compare_sources_keep.py test_daily_loop_reader_authored_practice.py test_daily_loop_reader_retire.py test_daily_loop_reference_adoption.py test_diagnosis_input_provenance_landing.py test_diagnosis_input_provenance.py test_diagnostic_probe_freshness.py test_dialogue_causal_join.py test_dl2_rw4b_keyed_pick_check.py test_e0_delivery.py test_embedding_route_isolation.py test_exam_protection.py test_exam_protection_review.py test_field_signal_production_paths.py test_figure_offers.py test_figures_rw5b_fix_round2.py test_figures_rw5b_review.py test_followup_diagnostic_selection.py test_forecast_receipts.py test_goal_certification_any_of.py test_goal_series.py test_guided_redo.py test_held_grade_evidence.py test_hint_kill_switch.py test_hypothesis_surface_wiring.py test_instrument_servability_journeys.py test_instrument_serving.py test_integration_daily_loop_field.py test_intent_checks.py test_intent_codex_review.py test_intent_fix_round4.py test_intent_fix_round5.py test_intent_orchestrator_rulings.py test_intent_plan.py test_judge_routes.py test_learner_text_gaps_composition.py test_learner_text_gaps_flow.py test_learner_text_gaps.py test_learner_text_gaps_review.py test_library_ask.py test_library_ask_review.py test_mcp_c1a_landing.py test_migrations.py test_misconception_transitions_intake.py test_model_usage_report.py test_output_budget.py test_owner_capture_1025.py test_p2_leakage_suite.py test_p3_journeys.py test_pfc_unassessed_readers.py test_pf_generation.py test_pinned_span_bridge.py test_placement_opening_probes.py test_placement_signals.py test_plan_first_transport_grant_scope.py test_plan_first_transport_offer_grants.py test_plan_first_transport.py test_post_attempt_pipeline.py test_prescription_passages.py test_primed_attempts.py test_probe_remint.py test_question_context.py test_question_promotions.py test_question_queue.py test_question_signal.py test_quick_check.py test_reader_activity.py test_reader_branches.py test_reader_dialogue.py test_reader_guidance.py test_reader_inquiry_kill_switch.py test_reader_inquiry_status.py test_reader_intent.py test_reader_observation_records.py test_reader_passage_check.py test_reader_recap.py test_reader_recap_review.py test_reader_recap_review_r2.py test_reader_reconnect.py test_reader_report.py test_reader_rw1b_review.py test_reader_rw1c_review.py test_reader_tutor_offers.py test_reader_tutor_retrieval.py test_reader_tutor_switch_off.py test_reader_wrap_up.py test_remediation_cold_retry.py test_retrieval_interventions_write_points.py test_reveal_ledger.py test_rw2c_switch_off.py test_rw4_kill_switches.py test_salience_firewall.py test_scheduler.py test_scoreboard.py test_sidecar_measurement.py test_sidecar_reader_p3.py test_sidecar_reader.py test_sidecar_remediation_surfaces.py test_sidecar_source_retrieval.py test_sidecar_teach_back.py test_sidecar_tutor_qa.py test_source_retrieval_followup.py test_source_retrieval_guards.py test_source_retrieval_rereview_cost.py test_source_retrieval_rereview.py test_source_retrieval_search.py test_source_retrieval_tutor.py test_source_space_resolver.py test_structured_transport_parity.py test_stuck_prompt.py test_teacher_te0_confidence_events.py test_tutor_citations.py test_tutor_delivery_fixes.py test_tutor_practice_request.py test_tutor_promotion_w2.py test_tutor_qa.py test_tutor_tool_requests.py test_ux_phase1_connect_ai.py test_ux_phase1_landing.py test_ux_phase1_usability_round1.py test_ux_phase2_shell.py test_ux_phase4_feedback.py

No paid or live call was made: every model is a fake, no vault was opened, no provider was routed.

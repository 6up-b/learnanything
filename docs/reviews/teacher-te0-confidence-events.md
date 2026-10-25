# Teacher TE0: confidence as events in model contexts and on the router card

Stage `teacher-te0`, branch `teacher/te0` in `learnanything-dl2`, base `e9d4de1aa` (main with T1, AD2+AD3 at
mvp-0.30, RW2d at mvp-0.31, local retrieval P1; migration head 220). Spec: `docs/specs/spec_teacher_v1.md` §0 item 4,
§5.2, §15.2 and §20's TE0 row ("None (context and card only)").

## 1. What changed

One shared module, `learnloop.confidence_events`, reads the two existing readings and renders them as **events in
words with the outcome**. It never renders a raw scalar or a threshold count.

* **The tap.** The source is `practice_attempts.answer_confidence` (1–5, migration 031).
* **The hedge read.** The source is `grading_evidence.learner_confidence` on the attempt's current (unsuperseded)
  rows.
  * A row counts only if it was read as `hedged` or `confident`. `absent` and `unknown` say nothing.
  * An attempt whose criteria were read both ways is "parts of the answer as hedged". No threshold is involved.
  * Rows written from a stated number are not hedge reads (`NOT_GRADER_READS`). These are a self-grade (`self`), an
    imported exam outcome (`exam_import`) and a simulated grade (`sim`).
* **Events**, for example:
  * "marked 5/5 sure; wrong"
  * "no tap; the grader read the answer as hedged; right"
  * "marked 4/5 sure; the grader read parts of the answer as hedged; partly right"
  * "marked 3/5 sure; held for review (no score yet)". The held predicate is THE predicate; a held grade never shows
    a score.
* **The stated limit** (`taps_limit`), for example "your taps so far are all 4–5 (29 taps)".
  * It appears whenever the taps so far do not span the tap's own 1–5 scale. The scale bounds are structural, so no
    constant decides what spread is enough (see open question 1).
* **Readers.**

  | Reader | What it gets | Without confidence data |
  |---|---|---|
  | **Router card**, `learner_state_card_v2` (`router/card.py`, gathered in `daily_plan/router_card.py`) | Each recent-work line gains its event. A typed section `confidence_7d` lists the candidate topics' events in the card's 7-day window, newest first, each with its own outcome. `confidence_limit` carries the limit | `CARD_VERSION` is `learner_state_card_v2` (`PREDECESSOR_CARD_VERSION` is v1, and `AD_CARD_VERSION` is now `v2+ad23`). The card's text and every typed field are byte-identical to a v1 card's. Only the version label differs. This is pinned by hashes of a v1 card built by the base commit's builder |
  | **History-aware diagnoser** (`diagnosis/split`) | `HistoryAttempt` gains `answer_confidence` and `confidence_event`. A blind-overlaid attempt takes the blind record's own read; a joint one takes the current grading evidence. Each rendered history row (and its snapshot export file) gains `confidence`. The diagnosed attempt gains a `confidence` block (version, note, event, taps so far) from `live.current_confidence` | Renders and hashes exactly as before (the stuck-reading and workbench-trace precedent). `DIAGNOSIS_PROMPT_VERSION` and `DIAGNOSIS_CONTEXT_VERSION` are unchanged: the block carries its own `version` (`confidence-events-v1`) and the context hash is content-addressed |
  | **Hint writer** (`hints/writer.build_prompt`, read once per request in `hints/service._write`) | `learner_confidence`: the topic's events, newest first, bounded at `CONTEXT_EVENT_LIMIT` = 12 per topic (a prompt-size bound, `keep`) | The prompt is unchanged. The Decider's state and `state_hash` are untouched |
  | **Tutor** (`tutor_qa._build_context`, practice, feedback and library contexts) | `TutorQAContext.learner_confidence` | `None`, which `tutor_context_payload` drops, so the prompt and `input_context_hash` are as before. The Reader context never carries it (§4, open question 2) |

  The teacher contexts do not exist yet (TE1). `learner_events` is the block `LessonBriefV1` can take.
* **Never the grader.**
  * Nothing in `learnloop.attempts` imports `learnloop.confidence_events`. A new import-linter contract,
    `graders-never-read-confidence-events`, pins this, and an AST test pins it for `blind_grading.py` and
    `grading.py`.
  * `BlindGradingContext` has no field for confidence, and a test pins it.
  * A blind-grading prompt built in a vault whose prior attempt is "marked 5/5 sure, hedged, wrong" contains none
    of it.

## 2. Protection

* **The hint writer and the tutor** read through the shared protection (`learner_protection.withheld_items` and
  `attempt_protection`).
  * An attempt on exam or held-out material, exam work, a reserved surface, an item a check or a cold retry holds,
    or a diagnostic probe contributes no event.
  * When the protection cannot be read, no event shows at all (fail closed).
  * The protection is read only when the topic has some confidence data. A topic without any costs one query and
    no protection read.
  * The block names no question, no answer and no score.
  * Protected attempts' taps still count toward the vault-wide "taps so far" limit. That is only a number, with no
    item, result or text (open question 5).
* **The router card** keeps its own rule, which predates TE0: protected past work keeps its result and shows no
  question and no answer. Its event (tap, hedge read, result) stays with it, because the event carries no more than
  the result the card already shows. A test checks that an exam attempt's event is shown while its answer text is
  not.
* **The diagnoser** is history-aware: it already reads every measuring attempt and the reference solution. TE0 adds
  only these measurement fields. Its records carry no diagnosis prose, as before.
* **The MCP chat read model** (`learner_context.learning_context`) is unchanged. The spec lists no chat consumer for
  TE0, and C1a's narrow text guard applies.

## 3. Playbook review: does TE0 change persisted meaning?

Checked against `docs/algorithm-change-playbook.md`. **No successor**, which confirms the spec's 2026-10-24 default.

1. **Scoring, scheduling, projections, admissibility.** None of these reads anything new.
   * There is no migration, no new table and no default change. The one config key, the kill switch
     `teacher.confidence_events_enabled`, came with the Codex review (F5).
   * Every `table_roles` classification and every defaults snapshot is unchanged.
   * Replay and rebuild never read the card, a model context or `confidence_events`.
2. **The card version.**
   * `card_version` is stored with each decision's card payload (`router_decision_payloads.format_version`) and its
     hash. It is display and provenance only: `plan_log` shows it as `format_version`, and `learnloop router card`
     prints it.
   * No code branches on it.
   * The mixture design's sampling and its logged propensity, the staged frame's feasibility and the rule's
     choices read the candidates, not the card's version.
   * The similar-decisions retrieval embeds `router_retrieval.context_text` (session, candidates, topics and open
     problems). That text reads neither `recent_work` nor the new section, so v1 and v2 decisions stay comparable
     in that index.
3. **Served decisions.**
   * The 2026-10-17 rule (one eligibility decision, mvp-0.27) makes a change to which items are served as
     measurements, or to which attempts are primed, a successor. TE0 changes neither: eligibility, priming and the
     feasible set are computed before the card is built.
   * What changes is a model input: the router models', when confidence data exists. That input already changes
     with every new attempt.
   * The diagnoser's, the hint writer's and the tutor's model inputs also change, and only when data exists. Their
     outputs are recorded with content-addressed context hashes and keep their meaning:
     * a hint is help, never evidence;
     * a diagnosis is a typed proposal its validators check;
     * the tutor's question classification (whether a question is hint-equivalent) is read from the question as
       before.
   * This is the same class of change as RW2b's workbench trace in the diagnoser context, which landed without a
     successor.
4. **No learned weight.** No weight, margin or threshold is introduced. The constants are:
   * `TAP_MIN`/`TAP_MAX`: structural, the tap's own scale;
   * `CONTEXT_EVENT_LIMIT`: a prompt-size bound, `keep`.

   None is a config key, and none of the touched modules is in the parameter registry's `MODULE_INVENTORY`, so the
   registry is unchanged. The tap/hedge recalibration is LP-min, later.

## 4. Gate

The commands, pass counts and the list of test files run are recorded at the end of this file (§6).

* **Paid calls:** none.
* **Live calls:** none.
* **Manual runs:** none. No `fixtures-local` copy was needed: the stage has no paid command, and the fakes cover the
  interfaces.
* **Ad hoc Python:** the only Python run outside pytest was a stdlib-only parity script under `env -i` with an empty
  `HOME`. It computed the v1 golden from the base commit's `router/card.py`.

## 5. Open questions for the owner

1. **The limit's rule.** The limit is stated whenever the taps do not span 1–5, so "all 4–5", "all 2–5" and "all 5"
   are each stated, and taps that include both 1 and 5 are not. This rule needs no made-up spread threshold. If the
   owner wants it only for a narrower band, that band is a choice the spec would need to name.
2. **The Reader tutor.** The Reader tutor (`context == "reader"`, with or without retrieval) gets no confidence
   events. Its manifest (design A.2) excludes any learner ability reading, and an event carries a past outcome.
   §15.2 says "tutor contexts". Should the Reader tutor be included?
3. **No kill switch.** *Resolved by the Codex review (F5, `docs/reviews/teacher-te0-codex-review.md`):*
   `teacher.confidence_events_enabled` (default on) is checked by every reader, and off restores each predecessor
   context. It adds one key to every defaults snapshot, which superseded §3's "no config key".
4. **The card's 7-day section is unbounded within the window.** *Resolved by the Codex review (F3):* each topic
   keeps its newest `CONTEXT_EVENT_LIMIT` events, and the section is the first thing the token budget trims. Both
   omissions are stated.
5. **The scope of "taps so far".** It counts every tap before the context's cutoff, vault-wide, including taps on
   protected attempts (as numbers only). The alternatives are to restrict it to unprotected attempts, or to the
   context's topics.
6. **Self-grades.** A self-grade's `learner_confidence` is derived from the learner's self-grade confidence. It is
   treated as neither a tap nor a hedge read. Should it be rendered as its own event ("self-graded, sure")?

## 6. Gate (as run)

All test commands ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, one at a time.

* `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2`.
* `uv run lint-imports --no-cache`: **36 kept, 0 broken**. This includes the new
  `graders-never-read-confidence-events` contract.
* `uv run pytest -n 6 tests/test_teacher_te0_confidence_events.py`: **19 passed**.
* The contract tests: `uv run pytest -n 6 tests/test_architecture.py tests/test_instructional_layering.py
  tests/test_sidecar_serializer_snapshot.py tests/test_desktop_rpc_contract.py tests/test_mobile_allowlist.py
  tests/test_cli_help_snapshot.py tests/test_table_roles.py tests/test_coordinated_migrations.py
  tests/test_tracked_fixture_databases.py tests/test_sqlite_file_copies.py`: **317 passed**.
* The targeted run: `uv run pytest -n 6 -p no:cacheprovider <the files below>`. These are every existing test file
  that exercises a changed module (router card and gatherer, router chooser and staged frame, `diagnosis.split`,
  hints service and writer, tutor QA and its contracts, `learner_protection`), plus the new file. The run gave
  **5,063 passed, 2 skipped, 2 xfailed** in 22 min.
* **Not run.** These are not applicable: there is no migration, DB or connection change (so no durability tests), no
  frontend change, no change under `src-tauri`, no schema change and no config change. Per the owner's rule, the
  full suite was not run.

Files in the targeted run:

- `tests/test_active_errors_overlay.py`
- `tests/test_ad1_fix_round4.py`
- `tests/test_ad23_fix_review.py`
- `tests/test_ad2_serving.py`
- `tests/test_ad3_subject_view.py`
- `tests/test_adaptive_difficulty_ad1.py`
- `tests/test_ai_compare.py`
- `tests/test_ai_config.py`
- `tests/test_approach_map_replay.py`
- `tests/test_authoring_contract.py`
- `tests/test_capture_desktop.py`
- `tests/test_capture_route_recovery.py`
- `tests/test_chatgpt_plan_landing.py`
- `tests/test_chatgpt_plan_provider.py`
- `tests/test_chatgpt_plan_workspace.py`
- `tests/test_codex_lockdown_round2.py`
- `tests/test_codex_lockdown_round3.py`
- `tests/test_codex_output_schema.py`
- `tests/test_codex_tool_lockdown.py`
- `tests/test_coldness_receipt.py`
- `tests/test_compare_methods.py`
- `tests/test_compare_sources_keep.py`
- `tests/test_config_refactor.py`
- `tests/test_daily_loop_reader_authored_practice.py`
- `tests/test_daily_loop_reader_retire.py`
- `tests/test_daily_loop_reference_adoption.py`
- `tests/test_daily_plan_composition.py`
- `tests/test_daily_plan_kill_switch.py`
- `tests/test_daily_plan_owner_decisions.py`
- `tests/test_daily_plan_replay.py`
- `tests/test_diagnose_review.py`
- `tests/test_diagnosis_async_router.py`
- `tests/test_diagnosis_card.py`
- `tests/test_diagnosis_context.py`
- `tests/test_diagnosis_contract.py`
- `tests/test_diagnosis_embeddings.py`
- `tests/test_diagnosis_history_modes.py`
- `tests/test_diagnosis_input_provenance_landing.py`
- `tests/test_diagnosis_input_provenance.py`
- `tests/test_diagnosis_pipeline.py`
- `tests/test_diagnosis_replay.py`
- `tests/test_diagnosis_reports.py`
- `tests/test_dialogue_causal_join.py`
- `tests/test_e0_delivery.py`
- `tests/test_embedding_backfill.py`
- `tests/test_embedding_recipe_hash_pins.py`
- `tests/test_embedding_route_isolation.py`
- `tests/test_exam_protection.py`
- `tests/test_exam_protection_review.py`
- `tests/test_field_signal_production_paths.py`
- `tests/test_field_split_outcomes.py`
- `tests/test_figure_offers.py`
- `tests/test_figures_codex_review.py`
- `tests/test_figures_rw5b_fix_round2.py`
- `tests/test_figures_rw5b_review.py`
- `tests/test_figures_scope_redesign.py`
- `tests/test_forecast_receipts_landing.py`
- `tests/test_forecast_receipts.py`
- `tests/test_grading_support.py`
- `tests/test_held_grade_composition.py`
- `tests/test_held_grade_evidence.py`
- `tests/test_help_outcomes.py`
- `tests/test_hint_authored_reveal_ruling.py`
- `tests/test_hint_blind.py`
- `tests/test_hint_contracts.py`
- `tests/test_hint_discriminating.py`
- `tests/test_hint_evidence.py`
- `tests/test_hint_feedback_texts.py`
- `tests/test_hint_h2a_review.py`
- `tests/test_hint_h2a_review_round2.py`
- `tests/test_hint_h2a_review_round3.py`
- `tests/test_hint_h2a_review_round4.py`
- `tests/test_hint_h2b_fix3.py`
- `tests/test_hint_h2b_fix4.py`
- `tests/test_hint_h2b_rereview.py`
- `tests/test_hint_h2b_review.py`
- `tests/test_hint_kill_switch.py`
- `tests/test_hint_outcome.py`
- `tests/test_hint_replies.py`
- `tests/test_hint_report.py`
- `tests/test_hint_service.py`
- `tests/test_hint_telemetry.py`
- `tests/test_integration_daily_loop_field.py`
- `tests/test_intent_codex_review.py`
- `tests/test_intent_fix_round7.py`
- `tests/test_judge_routes.py`
- `tests/test_learner_text_gaps_composition.py`
- `tests/test_learner_text_gaps_flow.py`
- `tests/test_learner_text_gaps.py`
- `tests/test_learner_text_gaps_rereview.py`
- `tests/test_learner_text_gaps_review.py`
- `tests/test_library_ask.py`
- `tests/test_library_ask_review.py`
- `tests/test_library_exercises.py`
- `tests/test_mcp_c1a_landing.py`
- `tests/test_mcp_tools.py`
- `tests/test_method_explicit_landing.py`
- `tests/test_method_explicit_upgrade.py`
- `tests/test_mobile_allowlist.py`
- `tests/test_model_usage_report.py`
- `tests/test_mvp010_upgrade.py`
- `tests/test_mvp013_upgrade.py`
- `tests/test_mvp014_upgrade.py`
- `tests/test_mvp015_upgrade.py`
- `tests/test_mvp016_upgrade.py`
- `tests/test_mvp017_upgrade.py`
- `tests/test_mvp018_upgrade.py`
- `tests/test_mvp020_upgrade.py`
- `tests/test_mvp021_upgrade.py`
- `tests/test_mvp022_upgrade.py`
- `tests/test_mvp023_upgrade.py`
- `tests/test_mvp024_upgrade.py`
- `tests/test_openai_chat_client.py`
- `tests/test_output_budget.py`
- `tests/test_pfc_unassessed_readers.py`
- `tests/test_pfc_unverified_unassessed.py`
- `tests/test_pinned_span_bridge.py`
- `tests/test_placement_diagnosis_decides.py`
- `tests/test_placement_opening_probes.py`
- `tests/test_placement_signals.py`
- `tests/test_placement_split_grades.py`
- `tests/test_plan_first_transport_grant_scope.py`
- `tests/test_plan_first_transport_offer_grants.py`
- `tests/test_plan_first_transport_offer_grants_r5.py`
- `tests/test_plan_first_transport.py`
- `tests/test_post_attempt_worker.py`
- `tests/test_question_context.py`
- `tests/test_question_promotion_jobs.py`
- `tests/test_question_promotions.py`
- `tests/test_question_signal.py`
- `tests/test_quick_check.py`
- `tests/test_reader_branches.py`
- `tests/test_reader_cues.py`
- `tests/test_reader_dialogue.py`
- `tests/test_reader_formative_texts.py`
- `tests/test_reader_guidance.py`
- `tests/test_reader_inquiry_kill_switch.py`
- `tests/test_reader_inquiry_status.py`
- `tests/test_reader_recap_review_r3.py`
- `tests/test_reader_reconnect.py`
- `tests/test_reader_report.py`
- `tests/test_reader_rw1b_review.py`
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
- `tests/test_reader_tutor_offers.py`
- `tests/test_reader_tutor_retrieval.py`
- `tests/test_reader_tutor_switch_off.py`
- `tests/test_reader_workbench_rw2a.py`
- `tests/test_recurrence_benchmarks.py`
- `tests/test_recurrence_commands.py`
- `tests/test_recurrence_deferral.py`
- `tests/test_recurrence_groups.py`
- `tests/test_recurrence_live.py`
- `tests/test_recurrence_merge_composition.py`
- `tests/test_reference_gate_imports.py`
- `tests/test_regrade_contract_replay.py`
- `tests/test_regrade_contract_successor.py`
- `tests/test_required_method_authority.py`
- `tests/test_required_method_grading.py`
- `tests/test_required_method_items.py`
- `tests/test_required_method_round3_review.py`
- `tests/test_reread_safety_landing.py`
- `tests/test_reveal_ledger.py`
- `tests/test_router_card.py`
- `tests/test_router_g1_feasibility.py`
- `tests/test_router_r2a_landing.py`
- `tests/test_router_r2a_serving.py`
- `tests/test_router_r2bc_landing.py`
- `tests/test_router_r2c_retrieval.py`
- `tests/test_router_r2c_teach_back.py`
- `tests/test_route_rules_in_grader.py`
- `tests/test_router_why_copy.py`
- `tests/test_rw2c_fix_round2.py`
- `tests/test_rw2c_fix_round3.py`
- `tests/test_rw2c_switch_off.py`
- `tests/test_rw4_kill_switches.py`
- `tests/test_sidecar_reader_p3.py`
- `tests/test_sidecar_reader.py`
- `tests/test_sidecar_source_retrieval.py`
- `tests/test_sidecar_teach_back.py`
- `tests/test_source_retrieval_followup.py`
- `tests/test_source_retrieval_guards.py`
- `tests/test_source_retrieval_rereview_cost.py`
- `tests/test_source_retrieval_rereview.py`
- `tests/test_source_retrieval_search.py`
- `tests/test_source_retrieval_tutor.py`
- `tests/test_source_space_resolver.py`
- `tests/test_structured_transport_parity.py`
- `tests/test_stuck_prompt_composition.py`
- `tests/test_stuck_prompt.py`
- `tests/test_stuck_prompt_replay.py`
- `tests/test_teach_back.py`
- `tests/test_tutor_citations.py`
- `tests/test_tutor_delivery_fixes.py`
- `tests/test_tutor_practice_request.py`
- `tests/test_tutor_promotion_service.py`
- `tests/test_tutor_promotion_w2.py`
- `tests/test_tutor_qa.py`
- `tests/test_tutor_tool_requests.py`
- `tests/test_ux_phase1_connect_ai.py`
- `tests/test_ux_phase1_landing.py`
- `tests/test_ux_phase1_usability_round1.py`
- `tests/test_ux_phase4_feedback.py`
- `tests/test_ux_phase4_landing.py`
- `tests/test_voi_stopping.py`
- `tests/test_workbench_assistance.py`
- `tests/test_workbench_check.py`
- `tests/test_workbench_chooser.py`
- `tests/test_workbench_discriminate.py`
- `tests/test_workbench_hint_service.py`
- `tests/test_workbench_hints.py`
- `tests/test_workbench_passage_draw.py`
- `tests/test_workbench_route_example.py`
- `tests/test_workbench_text_gaps.py`
- `tests/test_workbench_trace.py`
- `tests/test_teacher_te0_confidence_events.py`

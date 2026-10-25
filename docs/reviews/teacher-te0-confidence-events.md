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
   *Ruled at the landing (default): the limit is stated whenever the taps do not cover 1–5.*
2. **The Reader tutor.** The Reader tutor (`context == "reader"`, with or without retrieval) gets no confidence
   events. Its manifest (design A.2) excludes any learner ability reading, and an event carries a past outcome.
   §15.2 says "tutor contexts". Should the Reader tutor be included?
   *Ruled at the landing (default): the Reader tutor gets no confidence events.*
3. **No kill switch.** *Resolved by the Codex review (F5, `docs/reviews/teacher-te0-codex-review.md`):*
   `teacher.confidence_events_enabled` (default on) is checked by every reader, and off restores each predecessor
   context. It adds one key to every defaults snapshot, which superseded §3's "no config key".
4. **The card's 7-day section is unbounded within the window.** *Resolved by the Codex review (F3):* each topic
   keeps its newest `CONTEXT_EVENT_LIMIT` events, and the section is the first thing the token budget trims. Both
   omissions are stated. Fix round 2: once every event is trimmed, the stated limit and then the omission notice
   drop too when they do not fit, so the card fits whenever the predecessor's card would.
5. **The scope of "taps so far".** It counts every tap before the context's cutoff, vault-wide, including taps on
   protected attempts (as numbers only). The alternatives are to restrict it to unprotected attempts, or to the
   context's topics. *Ruled at the landing (default): it counts all taps, numbers only.*
6. **Self-grades.** A self-grade's `learner_confidence` is derived from the learner's self-grade confidence. It is
   treated as neither a tap nor a hedge read. Should it be rendered as its own event ("self-graded, sure")?
   *Ruled at the landing (default): a self-grade's confidence is not an event.*

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

## Landing onto main

Landed in `learnanything-merge2` on `merge/te0-onto-main`, cut from main `e3f6ab082` (UX Phase 3 and storage S0 on
top of the stage's base `e9d4de1aa`; `mvp-0.31`, migration head 220). The stage tip is `a1a7b27db`. Orchestrator
rulings: Codex review F1–F5 fixed and confirmed; the scoped verify's two Mediums (R2-1, R2-2) fixed in fix round 2
with fail-first tests; ready to land. **No algorithm successor (ruled), no migration; one new config section,
`[teacher]`.** Main was neither fast-forwarded nor pushed.

### Commits and conflicts

- `732974941`: the `--no-ff` merge of `teacher/te0`. **One conflict**, in the generated reference page
  `Reference/Configuration/Fields/Config - ai.md`, front matter only (`source_commit` / `source_commit_timestamp`):
  main's side taken, then regenerated. Nothing else overlapped. S0's work survives as is: no TE0 test reads an
  owner vault (`tests/test_teacher_te0_*.py` build their own vaults), so nothing moved to the `owner_vaults` lane,
  and the diff against main adds no database or binary (G8) and leaves the root `.gitignore` unchanged.
- `e6139e7c3`: `Config - ai.md` regenerated. Its line citations moved with TE0 (`offline_review/runner.py:218` to
  `:219`, `params/parameter_registry.py:1822` to `:1833`).
- `27332b631`: **a landing fix** found by the full suite (below).
- This record (docs only).

### Landing fix (`27332b631`)

`tests/test_e0_isolation.py::test_the_import_linter_contract_names_every_production_package` failed on the merged
tree. Main's E0 harness contract, `experiments-stay-outside-production` in `pyproject.toml`, must name every
production module, and TE0's new `learnloop.confidence_events` came from a base before E0 landed. The module is
now in the contract's `source_modules`. The failing full-suite run is the fail-first evidence. After the fix the
file gives 4 passed, and `lint-imports` keeps 36 contracts.

### Regeneration

- **References.** `db_generate_reference.py` rewrote 423 notes. The only change other than `source_commit` provenance
  was in `Config - ai.md` (committed, above); the rest were discarded. The branch's own `Config - teacher.md` is
  present. `db_validate_reference.py`: **0 errors**, 351 table notes, 1,047 configuration leaves (`[teacher]`'s key
  is the one more).
- **Defaults snapshots.** All **22** recomputed with `defaults_fingerprint_for_version` (template `.pyc` cleared,
  `-B`, `env -i`): **0 mismatches**. The branch's recomputed values (only `[teacher]`'s key moves them) hold on the
  composed defaults.
- **CLI help snapshot, RPC pins** (serializer snapshot, desktop RPC contract, mobile allowlist): their tests pass
  with no file changed (337 passed, together with the three TE0 test files, `test_architecture` and
  `test_public_tip_guards`).
- **`validate_vault.py`**: passes (1,155 notes, 1,153/1,153 reachable).
- **Failing before this stage, not fixed:** `desktop_validate.py` still stops on
  `components/pdfSelection/testing/syntheticBook.ts`; `module_validate.py` reports **1,193** issues (main: 1,191;
  the two new ones are the `confidence_events` module's missing module note).

### Gate

Setup: `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2` (5.14.0) in 5G scopes; `TMPDIR` = merge2's
`fixtures-local/tmp`. pytest lanes ran in 10G / 2G swap scopes under `flock /tmp/learnloop-fullsuite.lock`;
everything else ran in 5G / 1G scopes. Every Python run, the pytest lanes included, used `env -i` with empty `HOME`,
`CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. Logs are in `fixtures-local/te0-landing/`.

| Step | Result |
|---|---|
| `lint-imports --no-cache` | **36 kept**, 0 broken (before and after the landing fix) |
| full suite (`pytest -n 8`, at `e6139e7c3`, 67 min 59 s) | **21,359 passed**, 2 failed, 74 skipped (the owner lane), 38 xfailed |
| failure 1 | `test_e0_isolation::test_the_import_linter_contract_names_every_production_package`: real, fixed in `27332b631` (above) |
| failure 2, alone, 3 times | `test_reading_request_sweep::test_b_a_start_deferred_behind_a_queued_build_runs_that_build_and_then_acts`: **3/3 passed** (7 to 11 s). It is a load flake in the same sweep file as the known one: the parity runs shared the machine, and TE0 changes nothing on the reading sweep's path |
| durability (`-m durability`, at `27332b631`) | **123 passed**, 1 skipped |
| `owner_vaults` lane (`-m owner_vaults -n 6`; `LEARNLOOP_OWNER_VAULTS` = `fixtures-local/owner-lane-te0/`: backup-API copies of the three working vaults in `vault-backups-20261025-mvp030/`) | **77 passed**, 6 failed. Two are the pre-existing data-dependent failures (`test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events`, `test_placement_fixture_copies[arxiv_v2]`). The other four need the five retired vaults, which were not copied because no TE0-touched test uses them (`test_doctor` `conic-sections`, `test_migrate_fresh` and `test_sidecar_contract` `arxiv`, `test_goal_decay_projection` `linear_algebra_legacy`) |
| `npm install`; `npm run typecheck` | ok; clean |
| `npm test -- --maxWorkers=4` (whole vitest) | **210 files, 1,822 tests passed** |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | finished |
| worktree, tracked fixtures | `git status` clean apart from `fixtures-local/`; no non-empty `-wal` beside a tracked fixture |

### Parity (backup-API copies; no model call)

**Setup.** Scripts are in `fixtures-local/landing-te0/scripts/` (UX3's, re-pathed). New ones:
- `setup_te0.sh`, `a_te0.sh`, `bc_te0.sh` and `ctxmain.sh` drive the runs;
- `plan_dump_te0.py`: UX3's plan dump, with deterministic ids and every router decision and payload;
- `card_diff.py`, `ctx_dump.py`, `ctx_cmp.py`, `c_detail.py`, `hint_keys.py`, `prot_check.py` and
  `teacher_off.py` do the dumps and comparisons.

The details:
- **Copies.** The owner's backups `fixtures-local/vault-backups-20261025-mvp030/{linear_algebra,probability}` (in the
  main checkout; `mvp-0.30`, schema 218) were each copied once with `copy_tree_with_databases` into
  `landing-te0/orig/`, and every other copy came from those. `u31` is `orig` brought to `mvp-0.31` **with main's
  code**: `upgrade --to mvp-0.31` (219 and 220 applied), then `rebuild-derived-state` twice, rc 0 each.
  **Not opened:** anything in `~/learnloop-vaults`.
- **Code.** Main's is `git archive e3f6ab082` and the merge's is `git archive e6139e7c3`, each first on `sys.path`.
  The audit hook logs every process start and socket connection, and refuses Codex processes and non-loopback
  connections. It **logged nothing**: no process start, no connection.
- **Environment and routes.** `env -i` with empty `HOME` / `CODEX_HOME` / `LEARNLOOP_CONFIG_DIR` (still empty
  afterwards). `neutralize3.py` set 60 route fields to `127.0.0.1:9` loopback profiles with unset keys (63 tasks
  resolved on both codes; the only one not on a loopback is the disabled, keyless `embedding` profile). Rewrite,
  rerank, dense and embeddings are off, and so are `build_on_serve` and outcome placement.
- **Clock and ids.** The clock is frozen at 2026-10-19 09:00 UTC. New at this landing: the plan and context dumps
  mint **deterministic ids** (a fixed millisecond and random start; the monotonic rule increments them). Main run
  twice now gives byte-identical plans, including `card_hash` and `snapshot_hash`. This retires the run-to-run hash
  noise recorded since DL2, so the card hashes can be compared directly.

**(a) Main vs the merge, at `mvp-0.31`** (copies of `u31` opened by each code: 0 migrations applied, head 220).
- **Schema and rows:** identical, raw, row for row. LA has 1,503 objects, 356 tables and 18,301 rows; probability
  has 1,502 objects and 8,208 rows. FK 0, integrity ok, journal WAL, 0 `model_call_receipts`.
- **`rebuild --shadow`:** 0 / 0 / 0 on both codes, live database unchanged. **`doctor`:** 0 differences (LA 57 issues
  / 1 error, probability 101 / 48).
- **Certification and curves** (LA 129,651 bytes, probability 17,495) and **the Today queue** (no session, a
  session, greedy; LA 43 items, 528,665 bytes; probability 67, 741,269 bytes): **byte-identical**.
- **The daily plan** (read, serve, serve again, read):
  - **Identical:** every RPC answer, the presentations and the AD selections. The router's choice is the same on
    both vaults, in `chooser_choice`, `chosen_ref`, the chosen item, LO and scheduler candidate (LA
    `repair:ab702492f0b61bc8`, probability `maintain:ff645a40cf76e7e1`). The served items are also the same (LA
    `pi_orient_operations_omission_rewrite`, probability `pi_three_independent_birthd`, both serves).
  - **Different, and only in the card:** the card payload and its hash, the decision's `card_hash`, its
    `snapshot_hash` (which covers the card: with the switch off it equals main's, (b)), and `detail_json.router`'s
    `card_hash` and `card_version`.
  - **The version label** moves from `learner_state_card_v1+ad23` to `learner_state_card_v2+ad23`.
  - **The content** moves because both vaults hold confidence data, so it is the TE0 content, not only the label.
    - LA: 28 of the 30 recent-work lines gain their event, `confidence_limit` is "your taps so far are all 4–5
      (29 taps)", and the text gains the 7-day section ("none on these topics": the newest attempt is July 28, and
      the frozen clock is October 19) with the limit.
    - Probability: 2 recent-work lines gain their events ("marked 5/5 sure; …" and "marked 1/5 sure; the grader
      read parts of the answer as hedged; partly right"), with no limit, since the taps include 1 and 5.
  - **The card's own protection rule holds** (§2). Protected past work keeps its result and its event, and its
    question and answer stay withheld. Examples are "… · no tap; the grader read the answer as confident; right ·
    question and answer withheld (exam or held-out material)", a diagnostic probe's line, and two lines with a
    check waiting. The held review grade shows "marked 5/5 sure; held for review (no score yet)" with no score.

**(b) The kill switch off** (`[teacher] confidence_events_enabled = false` on copies of `u31`, the merge's code,
against main's code on copies of `u31`).
- **The plan dump is byte-identical to main's** on both vaults (LA 80,349 bytes, probability 40,451). That covers
  the card payload, `format_version` `learner_state_card_v1+ad23`, `content_hash`, `card_hash`, `snapshot_hash` and
  `detail_json`.
- **The model contexts are identical to main's** (`ctx_dump.py`, built offline):
  - **The diagnoser** (live assembly, `_plan_current` plus `assemble_diagnosis_context` over
    `live_history_store`): 8 LA attempts (4 tapped, 2 with only a hedge read, 2 with neither, including 2 exam
    attempts) and 2 probability attempts. Context hash, tokens and the rendered prompt are equal.
  - **The hint writer** (`request_hint` with an in-process capturing fake writer): 10 LA items and 3 probability
    items. Status, writer calls and every prompt are equal.
  - **The tutor** (`_build_context`, practice and Reader contexts, 16 + 2): payload, `_tutor_context_hash` and the
    prompt are equal.
  - **The blind grader's prompt** is equal.
  - A second main run of the same dumps is identical to the first, so the comparison is deterministic.

**(c) The switch on** (the default; the merge's code against main's).
- **What is added.**
  - **The diagnoser:** each prompt changes by one line, the context JSON, which gains confidence fields. Each
    history row gains its event (LA 3 to 35 events per context), and the diagnosed attempt gains its block. An
    example is "marked 4/5 sure; the grader read the answer as confident; partly right" with "your taps so far are
    all 4–5 (29 taps)". The count is the taps before that attempt, so earlier attempts read 24 to 28. Context
    hashes and token counts move (LA +61 to +798 tokens). On probability the first attempt reads "marked 1/5 sure;
    the grader read parts of the answer as hedged; partly right" with "all 1 (1 tap)". The second has no limit (1
    and 5).
  - **The hint writer:** in 7 of 10 LA prompts and 2 of 3 probability prompts the only key that differs in the
    prompt's JSON is `context.learner_confidence`. These are the items whose topic has unprotected events. Example
    topics: "What Makes a Vector Space?" 5 events, "Orient to the Vector-Space Idea" 7, "Read and apply the
    vector-space definition" 2, with the LA limit. The other prompts, with no events on their topic, are unchanged.
  - **The tutor:** every practice context differs only in the payload key `learner_confidence`. Every **Reader**
    context is unchanged (hash and prompt), as ruled.
- **Linear algebra's 29 taps are all 4–5.** Of those, 26 are 5 and 3 are 4, and every context states the limit:
  "your taps so far are all 4–5 (29 taps)". On probability (taps 1 and 5) no limit is stated.
- **Protection** (`prot_check.py`: every attempt with a tap or a hedge read, against the events the hint writer and
  tutor would carry):
  - **0 violations.** On LA, 62 attempts have a reading and 34 of them are protected: 30 exam attempts (exam or
    held-out material), 1 diagnostic probe and 2 with a check waiting in the app (one of them a teach-back). None
    contributes an event.
  - Two topics have only exam attempts ("Operations and the Vector-Space Axiom Checklist" 7, "Prove Vector
    Identities from Scalar Laws" 10). They get no block at all.
  - The one held grade reads "2026-07-25: marked 5/5 sure; held for review (no score yet)", with no score.
- **The blind grader's prompt is unchanged** on every chosen attempt, the tapped and hedge-read ones included (the
  prompt is byte-identical to main's). None of these strings occurs in it: "/5 sure", "no tap",
  `confidence-events-v1`, "taps so far", "hedge read", "read the answer as", "read parts of the answer",
  `answer_confidence`.

**Calls.** The 22 learner databases under `landing-te0/` that are not dump copies have **0** `model_call_receipts`
rows. The 8 context-dump copies (`ctx_main`, `ctx_main2`, `ctx_on`, `ctx_off` × 2 vaults) hold **40 `completed`
rows**, all with provider `fake_writer` and model `fake-writer-model`. They are the hint service's receipts for the
in-process capturing fake (`tests.hint_fakes.WriterFake`), which returns a canned answer: no process, no socket, no
provider. **No real model was called. Spend: $0.**

### New findings

1. **The AD feature audit's row count still varies between runs** (UX3's new finding 1, main's code). The plan
   runs added 30, 20 and 30 `judgment_ledger` rows on LA, and 15, 20 and 20 on probability, main and merge alike.
   These are `unavailable` records, since the routes are loopback. Nothing served or dumped differs. This is for
   the AD track.
2. **A contract that lists every module catches new modules from other stages only at the landing.** E0's contract
   met TE0's new module here. A stage that adds a top-level module should add it to
   `experiments-stay-outside-production`.

### For the owner

- **No migration, no successor.** Your vaults stay at `mvp-0.31`. There is nothing to run.
- **What changes:** model inputs and the router card only. **Nothing on screen changes.**
  - The router card, the history-aware diagnoser, the hint writer and the practice and feedback tutor now see each
    attempt's confidence as an event, with its outcome: your tap and how the grader read the answer's tone.
  - When your taps never span 1–5, they also see the stated limit. Linear algebra's are all 4–5, so the models read
    "your taps so far are all 4–5 (29 taps)".
  - Exam, held-out, check-waiting and probe attempts contribute nothing to the hint writer and tutor. The card keeps
    its own rule: the result and event stay, the question and answer are withheld.
  - The blind grader never sees any of it.
  - Which items are served, the plan's choices, certification, curves and Today are unchanged (parity (a)).
- **Kill switch:** `[teacher] confidence_events_enabled = false`. The card is then the predecessor's
  (`learner_state_card_v1`), and every context is byte-identical to main's (parity (b)).

### Open items

1. **Rulings recorded at their defaults** (§5):
   - the tap-limit statement shows whenever the taps do not cover 1–5;
   - the Reader tutor gets no confidence events;
   - "taps so far" counts all taps, numbers only;
   - a self-grade's confidence is not an event;
   - TE1's `LessonBriefV1` will take `confidence_events.learner_events`.
2. The tap/hedge recalibration (a learned weight) stays with LP-min (spec_learned_parameters_v1), as planned.
3. `desktop_validate.py` fails as before. `module_validate.py` has two more issues: `confidence_events` has no
   module note.
4. Owner-lane coverage of the five retired vaults was not run at this landing; their four tests do not touch TE0.
5. The parity copies' backup-API reads left empty `state.sqlite-wal` files and refreshed `-shm` files beside the
   three backup databases in the main checkout's `fixtures-local/vault-backups-20261025-mvp030/`, as at the previous
   landings. The databases are unchanged. This is harmless and they were left in place.

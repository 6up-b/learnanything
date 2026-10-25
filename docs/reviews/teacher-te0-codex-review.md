# Teacher TE0: Codex review and fixes

Stage `teacher-te0`, branch `teacher/te0` in `learnanything-dl2`, base `e9d4de1aa`. The review is Codex job
`20261025-023043-v8L3yb`, run on the stage at `e5a03beeb`. The stage write-up is
`docs/reviews/teacher-te0-confidence-events.md`.

## Review

Codex found five Medium defects and no High. Each was reproduced first, by a test that failed on `e5a03beeb`, and
then fixed. The tests are in `tests/test_teacher_te0_review_fixes.py`.

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | The diagnosed attempt's confidence event labelled a held grade as an outcome | fixed | `e821b00de` | `test_a_held_current_attempt_reads_held_for_review_never_wrong`. It failed with "marked 5/5 sure; wrong" on a real route-rule hold, which `held_attempts` reports as held |
| F2 | Medium | Confidence events could combine two grading revisions | fixed | `e821b00de` | `test_a_regrade_between_the_reads_never_mixes_revisions_in_the_tutor_and_hint_block` and `..._on_the_card` (both `durability`, WAL). Both failed with "confident; wrong", which is in neither revision |
| F3 | Medium | Confidence history bypassed the card's token budget | fixed | `e821b00de` | `test_a_heavy_confidence_week_stays_within_the_card_budget_and_keeps_recent_work`. It failed with 17,289 tokens against 16,000. Also `test_the_gatherer_bounds_each_topics_events_and_states_the_omission` (it failed with 17 events where the bound is 12) and `test_a_card_within_budget_states_no_omission` |
| F4 | Medium | Offline diagnosis evaluated a different confidence context | fixed | `e821b00de` | `test_offline_and_live_diagnosis_share_the_confidence_block` and `test_the_offline_runner_renders_the_confidence_block_into_each_arms_prompt`. In the runner test, the arms' `CurrentAttempt.confidence` was `None` |
| F5 | Medium | The live context change had no kill switch | fixed | `e821b00de`, `35c392055` | `test_the_switch_is_on_by_default_and_registered`, `test_switched_off_every_reader_gets_its_predecessor_context` and `test_switched_off_the_card_is_the_predecessors_card` |

No finding was rejected.

### F1: held grades on the diagnosed attempt

`diagnosis.split.live.current_confidence` now reads THE held predicate. A grade is held if either of these holds it:

* the record handed in (`outcome_contract.grade_held_for_review` on its `grading_support`);
* the ledger, now (`learner_protection.held_attempts`, read in the same snapshot as the rest).

A held grade passes `held=True` to `result_class`, so the event says "held for review (no score yet)" and never
"wrong". The test uses an actual stored blind record that holds the grade. It checks the held case both with and
without the support in the record handed in, and through `current_attempt_for`'s rendered context.

### F2: one read snapshot

These reads now happen inside one `write_provenance.read_snapshot`, on one connection:

* **`confidence_events.learner_events`** (the hint writer's and the tutor's block): the attempt rows (outcome and
  tap), the hedge reads, the held grades and the taps so far. Before the fix, the held grades and the taps were
  read on a second connection.
* **`current_confidence`**: the tap, the hedge-read fallback, the ledger's held predicate and the taps.
* **The router card's gatherer** (`daily_plan.router_card.CardGatherer.inputs`): its whole read block. This covers
  the results, the held status (`PastWork.held`) and the confidence readings.

The two regressions commit a real regrade (hedged/wrong to confident/right) on a second connection between the
outcome read and the hedge read. They are `durability` tests, because snapshot isolation between a reader and a
committing writer exists only under WAL. The withheld-items protection is still read on its own connection. It
decides only whether an attempt shows at all, and it fails closed, so it cannot pair an outcome with another
revision's hedge read.

### F3: the card's budget

There are now two bounds.

* **The selection.** The gatherer keeps each candidate topic's newest `CONTEXT_EVENT_LIMIT` events, the same
  prompt-size bound (`keep`) that the hint writer and the tutor use. It counts the rest in `confidence_omitted`.
* **The budget.** In `router.card.build_card`, the 7-day confidence events are the first thing trimmed, oldest
  first across topics. Trimming checks the size of both renderings (the typed card and its text), and the drop
  count is recorded in `truncation["dropped_confidence_events"]`.
  * The events go before recent work because each shown attempt's line keeps its own event, so the section is the
    least informative part to lose.
  * The heavy-history test keeps all 4 recent-work entries with their stems.

The card states every omission: the typed `confidence_omitted` field and the line "(N older confidence events left
out)" in the confidence section. Both keys are added only when something was left out, so the v1-parity hashes in
`test_teacher_te0_confidence_events.py` are unchanged.

### F4: offline diagnosis

The live and offline paths now build the block with the same code:

* `confidence_events.current_block` builds the block;
* `live.confidence_for_offline_target` assembles it for an offline arm.

`offline_review.runner.stage_diagnoses` passes the block into `current_attempt_from` for every arm, from that arm's
own blind record.

* **A real target** reads its tap and the taps before its completion time from the review's copy. It takes the
  hedge read and the held status from the arm's record only (`vault_grade=False`), so the vault's own grading is
  never mixed into another grade's event.
* **A planted target** has no tap, and its planted history has no taps, so only its record's hedge read shows.

The token estimate in `plan_review` still uses a placeholder grade without the block. That is an allowance,
not a prompt.

Codex also noted that `CurrentAttempt._render` strips each criterion's `learner_confidence`. That is unchanged, and
it is the same in both paths: in both, the hedge read reaches the diagnoser only through the `confidence` block.

### F5: the kill switch

The new key is `teacher.confidence_events_enabled`, default `true`. It is a new `[teacher]` section in
`config/schema.py` (`TeacherConfig`), where TE1's lesson switches will go (spec §18).

* **Readers.** `confidence_events.enabled(vault)` is read by every reader:
  * `learner_events`, for the hint writer and the tutor;
  * `VaultHistoryStore`, for the history rows;
  * `current_confidence` and `confidence_for_offline_target`, for the live and offline diagnosed attempt;
  * the card's gatherer.
* **Off.**
  * No reader carries an event or the stated limit.
  * Every context renders and hashes as its predecessor's.
  * The card is a `learner_state_card_v1` card, version label included (`CardInputs.confidence_enabled`, and
    `v1+ad23` with adaptive difficulty's fields).
* **Classification.** The key is in `params/parameter_registry.py` as `structural` / `operational`: a kill switch,
  not a weight.
* **Snapshots and reference.**
  * All 22 defaults snapshots were recomputed with `defaults_fingerprint_for_version`. Each one moved only because
    the effective config gains the key. No other value changed, and there is no successor.
  * The references were regenerated: 1,047 configuration leaves in 70 sections, and `Config - teacher.md`.
* **No new constants.** The fixes add no learned weight, margin or threshold. The one bound used, `CONTEXT_EVENT_LIMIT`,
  was already classified `keep` (a prompt-size bound).

## Gate

Every test command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, one at a time.

* `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2`.
* `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
* The reproductions on `e5a03beeb` (before any fix): `uv run pytest -n 6 tests/test_teacher_te0_review_fixes.py`
  gave **10 failed, 1 passed**. The one that passed is `test_a_card_within_budget_states_no_omission`, a guard
  that held before the fix too.
* After the fixes: `uv run pytest -n 6 tests/test_teacher_te0_review_fixes.py tests/test_teacher_te0_confidence_events.py`
  gave **30 passed**.
* The reference scripts, under `env -i` with an empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`:
  * `db_generate_reference.py` gave 351 table notes;
  * `db_validate_reference.py` gave **0 errors**, after the two prose leaf counts were updated from 1,046 to
    1,047;
  * `validate_vault.py` passed (1,155 notes).
* The targeted run: `uv run pytest -n 6 -p no:cacheprovider -q <the 262 files below>` gave **5,336 passed, 2 skipped, 2 xfailed** in 30 min. The files are every test file that exercises a changed module: `confidence_events`, the router card and its gatherer, `diagnosis.split` live and history, the offline review runner, the config schema and template (the defaults snapshots and the upgrade chains), the parameter registry, the hint service and writer, the tutor, `learner_protection` and `held_grades`. They include both TE0 test files and the contract tests: architecture, instructional layering, the CLI help snapshot, the serializer snapshot, the desktop RPC contract, the mobile allowlist, table roles, coordinated migrations, the tracked fixture databases and the SQLite file copies.
* **Not run, by the owner's rule:** the full suite, the whole durability lane and the whole vitest run. **Not
  applicable:** there is no migration, DB or connection-code change, no frontend change and no `src-tauri` change.
  The two durability-marked regressions ran inside the targeted run.
* **Paid calls:** none. **Live calls:** none. **Manual runs:** none.

Files in the targeted run:

- `tests/codex_cli_fakes.py`
- `tests/conftest.py`
- `tests/diagnosis_fakes.py`
- `tests/helpers.py`
- `tests/hint_fakes.py`
- `tests/library_ask_fixtures.py`
- `tests/mcp_world.py`
- `tests/reader_tutor_fakes.py`
- `tests/rw2b_fix10_base_sequence.py`
- `tests/rw2b_fix11_base_sequence.py`
- `tests/rw2c_base_sequence.py`
- `tests/source_service_fakes.py`
- `tests/structured_ai.py`
- `tests/test_ad1_codex_review_fixes.py`
- `tests/test_ad1_fix_round4.py`
- `tests/test_ad23_owner_decisions.py`
- `tests/test_ad23_successor.py`
- `tests/test_ad23_t1_routes.py`
- `tests/test_ad2_model.py`
- `tests/test_ad3_subject_view.py`
- `tests/test_ai_compare.py`
- `tests/test_ai_config.py`
- `tests/test_ai_runtime.py`
- `tests/test_ai_tool_isolation.py`
- `tests/test_approach_map_replay.py`
- `tests/test_architecture.py`
- `tests/test_blueprint_projection.py`
- `tests/test_capture_desktop.py`
- `tests/test_capture_route_recovery.py`
- `tests/test_card_lineage.py`
- `tests/test_characterization_mastery_reliability.py`
- `tests/test_chatgpt_plan_cli.py`
- `tests/test_chatgpt_plan_landing.py`
- `tests/test_chatgpt_plan_provider.py`
- `tests/test_chatgpt_plan_workspace.py`
- `tests/test_cli_generate_practice.py`
- `tests/test_cli_help_snapshot.py`
- `tests/test_codex_isolation_mcp_check.py`
- `tests/test_codex_lockdown_round2.py`
- `tests/test_codex_lockdown_round3.py`
- `tests/test_codex_output_schema.py`
- `tests/test_codex_tool_lockdown.py`
- `tests/test_cold_start_revision.py`
- `tests/test_compare_sources_keep.py`
- `tests/test_config_refactor.py`
- `tests/test_constraint_engine.py`
- `tests/test_coordinated_migrations.py`
- `tests/test_daily_loop_reader_authored_practice.py`
- `tests/test_daily_loop_reader_retire.py`
- `tests/test_daily_loop_reference_adoption.py`
- `tests/test_decider_client.py`
- `tests/test_decider_landing.py`
- `tests/test_desktop_rpc_contract.py`
- `tests/test_diagnose_review.py`
- `tests/test_diagnose_review_spend.py`
- `tests/test_diagnosis_context.py`
- `tests/test_diagnosis_contract.py`
- `tests/test_diagnosis_history_modes.py`
- `tests/test_diagnosis_input_provenance_landing.py`
- `tests/test_diagnosis_input_provenance.py`
- `tests/test_diagnosis_isolation.py`
- `tests/test_diagnosis_pipeline.py`
- `tests/test_diagnosis_replay.py`
- `tests/test_dialogue_causal_join.py`
- `tests/test_difficulty_band_guards.py`
- `tests/test_e0_delivery.py`
- `tests/test_embedding_route_isolation.py`
- `tests/test_evidence_config.py`
- `tests/test_evsi_calibration_sim.py`
- `tests/test_evsi_multisim.py`
- `tests/test_exam_protection.py`
- `tests/test_exam_protection_review.py`
- `tests/test_facet_identity_composition.py`
- `tests/test_facet_reword_confirm_review.py`
- `tests/test_family_proposals.py`
- `tests/test_field_config.py`
- `tests/test_field_priors.py`
- `tests/test_field_signal_production_paths.py`
- `tests/test_field_workbench_signals.py`
- `tests/test_figure_offers.py`
- `tests/test_figures_rw5b_fix_round2.py`
- `tests/test_figures_rw5b_review.py`
- `tests/test_figures_scope_redesign.py`
- `tests/test_forecast_receipts.py`
- `tests/test_gate_fit.py`
- `tests/test_glm_ocr.py`
- `tests/test_grading_cli.py`
- `tests/test_held_grade_evidence.py`
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
- `tests/test_hint_h2b_rereview.py`
- `tests/test_hint_h2b_review.py`
- `tests/test_hint_kill_switch.py`
- `tests/test_hint_outcome.py`
- `tests/test_hint_replies.py`
- `tests/test_hint_report.py`
- `tests/test_hint_service.py`
- `tests/test_ingest_m3.py`
- `tests/test_ingest_runner.py`
- `tests/test_instructional_layering.py`
- `tests/test_integration_daily_loop_field.py`
- `tests/test_intent_codex_rereview.py`
- `tests/test_item_parameters.py`
- `tests/test_judge_routes.py`
- `tests/test_kinship_feature.py`
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
- `tests/test_mvp011_upgrade.py`
- `tests/test_mvp013_upgrade.py`
- `tests/test_mvp014_upgrade.py`
- `tests/test_mvp015_upgrade.py`
- `tests/test_mvp016_upgrade.py`
- `tests/test_mvp017_route_check_replay.py`
- `tests/test_mvp017_upgrade.py`
- `tests/test_mvp018_upgrade.py`
- `tests/test_mvp020_upgrade.py`
- `tests/test_mvp021_upgrade.py`
- `tests/test_mvp022_upgrade.py`
- `tests/test_mvp023_upgrade.py`
- `tests/test_mvp024_upgrade.py`
- `tests/test_native_media_readiness.py`
- `tests/test_openai_embedding_client.py`
- `tests/test_openrouter_video_client.py`
- `tests/test_open_world_gate.py`
- `tests/test_output_budget.py`
- `tests/test_p0_cutover_mvp08.py`
- `tests/test_pf_cli.py`
- `tests/test_pfc_unassessed_readers.py`
- `tests/test_pfc_unverified_unassessed.py`
- `tests/test_pinned_span_bridge.py`
- `tests/test_placement_opening_probes.py`
- `tests/test_placement_signals.py`
- `tests/test_plan_determinism.py`
- `tests/test_plan_first_transport_grant_scope.py`
- `tests/test_plan_first_transport_offer_grants.py`
- `tests/test_plan_first_transport_offer_grants_r5.py`
- `tests/test_plan_first_transport_paid_roles.py`
- `tests/test_plan_first_transport.py`
- `tests/test_practice_index_find.py`
- `tests/test_probability_prep.py`
- `tests/test_project_atomicity.py`
- `tests/test_project_blindness.py`
- `tests/test_project_capture.py`
- `tests/test_project_cli.py`
- `tests/test_project_hooks.py`
- `tests/test_project_probes.py`
- `tests/test_project_redaction.py`
- `tests/test_project_report.py`
- `tests/test_provider_resolution_parity.py`
- `tests/test_question_context.py`
- `tests/test_question_promotions.py`
- `tests/test_question_signal.py`
- `tests/test_quick_check.py`
- `tests/test_reader_branches.py`
- `tests/test_reader_dialogue.py`
- `tests/test_reader_inquiry_kill_switch.py`
- `tests/test_reader_inquiry_status.py`
- `tests/test_reader_intentions.py`
- `tests/test_reader_recap_review_r3.py`
- `tests/test_reader_reconnect.py`
- `tests/test_reader_report.py`
- `tests/test_reader_rw1b_review.py`
- `tests/test_reader_rw1c_review.py`
- `tests/test_reader_rw2b_fix11.py`
- `tests/test_reader_rw2b_fix14.py`
- `tests/test_reader_rw2b_fix15.py`
- `tests/test_reader_rw2b_fix9.py`
- `tests/test_reader_rw2b_review.py`
- `tests/test_reader_tutor_switch_off.py`
- `tests/test_reading_paths.py`
- `tests/test_reading_step_switch.py`
- `tests/test_recall_calibration.py`
- `tests/test_recurrence_benchmarks.py`
- `tests/test_recurrence_commands.py`
- `tests/test_registry_audit.py`
- `tests/test_regrade_contract_successor.py`
- `tests/test_regrade_contract_upgrade.py`
- `tests/test_required_method_round3_review.py`
- `tests/test_reread_safety_landing.py`
- `tests/test_reveal_ledger.py`
- `tests/test_router_card.py`
- `tests/test_router_offer_log.py`
- `tests/test_router_probe_ties.py`
- `tests/test_router_r2a_landing.py`
- `tests/test_router_r2c_teach_back.py`
- `tests/test_rw2c_fix_round2.py`
- `tests/test_rw2c_switch_off.py`
- `tests/test_rw4_kill_switches.py`
- `tests/test_scheduler.py`
- `tests/test_self_attributed_misconceptions.py`
- `tests/test_sensitivity_certificates.py`
- `tests/test_serve_eligibility_review.py`
- `tests/test_sidecar_reader_p3.py`
- `tests/test_sidecar_reader.py`
- `tests/test_sidecar_serializer_snapshot.py`
- `tests/test_sidecar_source_retrieval.py`
- `tests/test_sidecar_teach_back.py`
- `tests/test_sim_teach_back.py`
- `tests/test_simulation.py`
- `tests/test_source_retrieval_followup.py`
- `tests/test_source_retrieval_guards.py`
- `tests/test_source_retrieval_rereview_cost.py`
- `tests/test_source_retrieval_rereview.py`
- `tests/test_source_retrieval_search.py`
- `tests/test_source_retrieval_tutor.py`
- `tests/test_source_roles.py`
- `tests/test_sources_merge_composition.py`
- `tests/test_source_space_resolver.py`
- `tests/test_sqlite_file_copies.py`
- `tests/test_structured_transport_parity.py`
- `tests/test_stuck_prompt.py`
- `tests/test_surprise.py`
- `tests/test_t6_followup_review.py`
- `tests/test_table_roles.py`
- `tests/test_teacher_te0_confidence_events.py`
- `tests/test_teacher_te0_review_fixes.py`
- `tests/test_tier1_decider.py`
- `tests/test_tracked_fixture_databases.py`
- `tests/test_tutor_citations.py`
- `tests/test_tutor_delivery_fixes.py`
- `tests/test_tutor_practice_request.py`
- `tests/test_tutor_promotion_w2.py`
- `tests/test_tutor_qa.py`
- `tests/test_tutor_tool_requests.py`
- `tests/test_ux_phase1_connect_ai.py`
- `tests/test_ux_phase1_landing.py`
- `tests/test_ux_phase1_round2_review.py`
- `tests/test_ux_phase1_usability_round1.py`
- `tests/test_ux_phase2_shell.py`
- `tests/test_ux_phase4_feedback.py`
- `tests/test_ux_phase4_landing.py`
- `tests/test_voi_merge_composition.py`
- `tests/test_voi_stopping.py`
- `tests/test_voi_v2.py`
- `tests/test_voyage_fallback.py`
- `tests/test_workbench_assistance.py`
- `tests/test_workbench_hint_service.py`
- `tests/test_workbench_trace.py`
- `tests/text_gap_fakes.py`
- `tests/voi_restore_scenarios.py`

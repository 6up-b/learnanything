# FG1: Codex review and its fixes (`followup/fg1-generate-serve`)

Review job `20261104-001943-FALikC` (gpt-6.1-sol), against the build at `efd8948867`. Eight findings; all eight reproduced and fixed. Tests: `tests/test_followup_codex_review.py`.

## Findings

| Id | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | Generation spend omitted from the daily cap | fixed | `a01ecfbb27` | `test_f1_*`: successive, failed and in-flight requests, and the router's own next request |
| F2 | High | Router details reveal held causes without marking exposure | fixed | `a01ecfbb27` | `test_f2_*`; vitest "while the causes are held" |
| F3 | High | A crash can publish a probe without its single-use identity | fixed | `a01ecfbb27` | `test_f3_*`: fault injection after the file, after the pin, a failed write, the mint and the batch |
| F4 | High | Abandonment does not close generated probes outside workflows | fixed | `a01ecfbb27` | `test_f4_*`: serve, skip, direct reopen through the sidecar; the claim has no wildcard |
| F5 | High | Protected exam text can reach generation through hypotheses | fixed | `a01ecfbb27` | `test_f5_*`: a sentinel in the statement, the author's builder, exam attempts, the writer's record |
| F6 | Medium | Completion can commit before its workflow handoff | fixed | `a01ecfbb27` | `test_f6_*`: crashes at each boundary, recovery by Next and at startup |
| F7 | Medium | Switching FG1 off can strand a standing plan | fixed | `a01ecfbb27` | `test_f7_*`: a standing plan and `next_plan_item` through the sidecar |
| F8 | Medium | Generation retries redraw a committed router decision | fixed | `a01ecfbb27` | `test_f8_*`: a transport failure and a lease recovery under a plan, a duplicate receipt, the commit |

**How they were reproduced.** After the fixes were written, the new tests were run against a scratch export of `efd8948867` (`git archive HEAD src migrations`, `-o pythonpath=<export>/src`): 36 failed and 3 passed. Each finding has tests failing on behaviour: for example F1 `DID NOT RAISE SpendRefused`, F3 `is_generated_probe` False on the orphan, F4 a skipped entry probe reopening, F7 Next still offering the item, F8 a second draw. The passes are the tests that pin what must stay true (a skip of an ordinary item changes nothing).

## What changed

**F1.** `followup_generation` joins `GUARDED_OWNERS`, so every generation request's start receipt is admitted against the day's shared total, reservations and failed requests included. The total is shared both ways: a day's generation spend can also refuse a router model's metered request, which then falls back to the staged rule.

**F2.** `decision_view` is the one read for the Feedback line and the plan's line. While any miss's causes are held it leaves out the card, the rationale and the observational record, on the server. Ordinary block decisions are held too, because every card can list open problems. The line and the models' numbers stay, and *details* says the rest comes after the question. Opening it is not a disclosure, so it marks nothing.

**F3.** The identity and the family link now commit before the file exists, on the author's path and on the mint and batch paths under FG1. On the author's path the link's `pending_review` parks the item against state sync, so a crash leaves a question no door serves. A mint or batch item needs no review, so after a crash it is simply a single-use probe with its identity. The serve door refuses one that is not admitted, or that a workflow owns and never bound. A retry withdraws what the interrupted run left (`admission.withdraw_interrupted`): the item retires, its pin ends, and its candidate is rejected, or the retry's own question would be refused as a duplicate class. An entry or need job has no workflow to retry under, so its orphan stays parked.

**F4.** `abandon` closes every registered generated probe, workflow or not, and ends its open presentation. The door now claims against the presentation actually open for the item, not the id a workflow row remembers, and a missing presentation is no longer a wildcard. A burn made before any presentation was committed binds to the next one and ends once any presentation of the item is answered or ended. Next no longer offers a served probe whose presentation ended. The skip handler now abandons only after its session-ownership check, so a refused skip closes nothing.

**F5.** New rule `PastWork.exam_reason`, checked by `authoring.hypotheses_exam_reason` before the router's card facts and the author's prompt, and again in the context builder for entry and need work. It reads provenance, never the words: the attempts of the hypothesis's episode, and the items and sources its writer recorded reading (`text_write_provenance`). Such a miss takes the practice lane, so nothing is spent and Next goes on. Unreadable protection fails the workflow with no request, as before.

**F6.** The joint-vault job and the probe's settlement now commit in the completion's transaction. `jobs.recover_workflow` covers the diagnosis worker's gap: at startup and on Next, a pending workflow whose diagnosis ended and whose job is missing gets it, and one whose job ended fails with its line.

While fixing this I found a stranding the review did not name: a joint vault with shadow diagnosis never got a job, because a shadow diagnosis doesn't move a workflow. The job now depends only on whether the vault is blind.

**F7.** `settle_open_when_off` closes what a workflow prepared, through `workflow.close_probe`, the one closing now shared with *Continue without it*, abandonment and a retired wait: the probe retires, its presentation ends, an empty episode is abandoned. A standing plan displaces the retired item at its next reconcile, which reads the ledger whatever the switch says. Burns persist.

**F8.** `router.decide_once` reuses the workflow's recorded decision on retry and lease recovery, with no model asked. Logging the decision and naming it on the workflow now commit together. A receipt already logged resolves to its own row, whose arm and propensity stand.

## Claims from the review

| Claim | Now |
|---|---|
| "Every physical call" is in the envelope | F1 |
| Single use for every generated probe | F3, F4, with the limit below |
| "Next never strands" | F4, F6, F7 |
| Only what `protection_view` admits reaches authoring | F5 |
| Retry and crash recovery keep the intervention's identity | F8 |
| The tests cover these end to end | Each finding's tests are in the new file. The principal journey test itself still runs a joint vault with no plan |

## What stays as it is, and what the owner may want to change

1. **Exam-sitting misses now take the practice lane.** Their causes rest on exam work, so under F5 they generate no probe. §3.1 implied they might, and it now says this. The eligibility and cap stay. Spec §8's exam protection decides it, but this narrows the lane, so it is the owner's to overrule.
2. **F5 stops on exam material, not on every protected reason.** A check waiting on the item or a diagnostic probe already answered does not stop the probe lane. The learner just answered that question, and sending these to the practice lane would remove the probe from ordinary re-misses. The router card's stricter rule is unchanged for its own reader.
3. **One repeat remains possible.** A workflow-less probe burned before any presentation is committed, whose contract then comes back inactive (no episode in progress, a session cap), can reopen until it is answered or skipped. No measurement is at stake and no answer has been given, so under the proportionate bar it stays the same administration. Retiring it on an inactive contract would lose a question each time a cap applies.
4. **A retry after a crash spends one more authoring call.** Recovery parks and re-authors rather than resuming a half-admitted question: simpler, bounded by the job's retries, and rare.

## Gate

- `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0`.
- `lint-imports --no-cache` (empty env): 42 contracts kept, 0 broken, so the frozen-cycles list holds.
- Targeted pytest, capped scope, `-n 6`, on the 393 files below: **7515 passed, 46 skipped, 8 xfailed, 3 failed**. It includes the CLI help snapshot, the process-launch list (`test_codex_lockdown_round3.py`), the display label's audit (`test_sidecar_measurement.py`), config defaults, serializer, desktop RPC, mobile allowlist, architecture, table roles, coordinated migrations and tracked fixtures.
- The 3 failures came from the FG1 build, not these fixes; the build's narrower gate never ran these two files. `test_judge_routes.py` didn't know the new `followup_probe_author` route, and `test_sidecar_idle_threads.py` (2 tests) didn't know the fourth worker slot. Their pins are updated. Those two files then ran: **29 passed**. I did not rerun all 393 files after this test-only change; the landing's full suite covers them.
- After the regeneration: `test_followup_codex_review.py`, those two files, CLI help, the process-launch list, module inventory and public-tip guards: **108 passed**.
- Durability, `--durable-sqlite` on the FG1 files, the new one included (a store module changed; no migration did): **117 passed**.
- Frontend: `npm install`, typecheck clean, `vitest --maxWorkers=4` on `FeedbackScreen.followup.test.tsx`: **7 passed**; `frontend:build` ok. No change under `src-tauri`, so no `cargo check`.
- References: the schema didn't change, but moved source lines made the catalogs stale, so all three were regenerated. DB validate `errors: []` (385 table notes), desktop 318 TS and 6 Rust, modules 1188 notes and 66 maps, vault validation passes.
- The full suite, the whole durability lane and the whole vitest run were not run, per the owner's rule: they are for the landing gate.

Process notes: the first patch script of this step ran without the `env -i` wrapper. It only rewrote source text with `pathlib` and made no call of any kind; every later script and `lint-imports` ran under the wrapper. No paid or live call, no app or GUI launched, synthetic vaults only.

<details><summary>Test files run</summary>

tests/test_active_errors_overlay.py
tests/test_ad1_attempt_columns.py
tests/test_ad1_codex_rereview_fixes.py
tests/test_ad1_codex_review_fixes.py
tests/test_ad1_fix_round4.py
tests/test_ad1_fix_round5.py
tests/test_ad1_fix_round6.py
tests/test_ad23_contract.py
tests/test_ad23_fix_r8.py
tests/test_ad23_fix_review.py
tests/test_ad23_intent_compose.py
tests/test_ad23_pool_membership.py
tests/test_ad23_successor.py
tests/test_ad2_serving.py
tests/test_ad3_dose_arm.py
tests/test_adaptive_difficulty_ad1.py
tests/test_ai_config.py
tests/test_ai_runtime.py
tests/test_ai_tool_isolation.py
tests/test_approach_map_replay.py
tests/test_approach_maps.py
tests/test_architecture.py
tests/test_assumed_known.py
tests/test_attempt_completion.py
tests/test_attempt_content_state_successor.py
tests/test_attempt_write_order.py
tests/test_batch3_landing.py
tests/test_build_study_map_routing.py
tests/test_canonical_projection_fold_skip.py
tests/test_canonical_projection_rollout.py
tests/test_capture_desktop.py
tests/test_causal_orchestrator.py
tests/test_causal_p2_acceptance.py
tests/test_causal_probe_commissioning.py
tests/test_causal_repair_sidecar_rpcs.py
tests/test_causal_shadow_selection.py
tests/test_characterization_assessment_exam.py
tests/test_characterization_probe_regrade.py
tests/test_characterization_probe_replay.py
tests/test_chatgpt_plan_sidecar.py
tests/test_cli_generate_practice.py
tests/test_cli_help_snapshot.py
tests/test_codex_lockdown_frozen.py
tests/test_codex_lockdown_round3.py
tests/test_codex_runtime.py
tests/test_coldness_receipt.py
tests/test_cold_retry_reschedule.py
tests/test_collection_dataset.py
tests/test_config_refactor.py
tests/test_coordinated_migrations.py
tests/test_curriculum_c1_fix_round3.py
tests/test_curriculum_c1_fix_round4.py
tests/test_curriculum_c1_plan_follows_path.py
tests/test_daily_loop_golden_path_lifecycle.py
tests/test_daily_loop_lo_lifecycle_serving.py
tests/test_daily_loop_reader_retire.py
tests/test_daily_loop_reentry_break.py
tests/test_daily_loop_reentry_cap.py
tests/test_daily_loop_reference_adoption.py
tests/test_daily_loop_start_minutes.py
tests/test_daily_plan_composition.py
tests/test_daily_plan_kill_switch.py
tests/test_daily_plan_owner_decisions.py
tests/test_daily_plan_reading.py
tests/test_daily_plan_reentry.py
tests/test_daily_plan_replay.py
tests/test_daily_plan_review_regressions.py
tests/test_daily_plan_rpc.py
tests/test_data_capture_a1_prefilter.py
tests/test_data_capture_a2_measurement.py
tests/test_data_capture_a4_delayed_completion.py
tests/test_data_capture_a5_not_ready_floor.py
tests/test_data_capture_a6_delayed_pick.py
tests/test_data_capture_codex_review.py
tests/test_data_capture_landing_review.py
tests/test_data_capture_phone.py
tests/test_data_capture_report.py
tests/test_data_capture_successor.py
tests/test_decider_landing.py
tests/test_deliverable_path.py
tests/test_desktop_rpc_contract.py
tests/test_device_eligibility.py
tests/test_diagnosis_async_router.py
tests/test_diagnosis_card.py
tests/test_diagnosis_embeddings.py
tests/test_diagnosis_input_provenance_landing.py
tests/test_diagnosis_input_provenance.py
tests/test_diagnosis_pipeline.py
tests/test_diagnosis_reports.py
tests/test_diagnostic_probe_freshness.py
tests/test_dialogue_causal_join.py
tests/test_doctor.py
tests/test_dual_authority_administration.py
tests/test_e0_relabel_round.py
tests/test_embedding_route_isolation.py
tests/test_evsi_router_composition.py
tests/test_exam_pool.py
tests/test_exam_protection_identity.py
tests/test_exam_protection.py
tests/test_exam_protection_review.py
tests/test_exam_session.py
tests/test_facet_identity_actions.py
tests/test_facet_identity.py
tests/test_facet_reword_paths.py
tests/test_facet_rewords.py
tests/test_facet_state_write_on_change.py
tests/test_field_signal_production_paths.py
tests/test_field_split_outcomes.py
tests/test_field_workbench_signals.py
tests/test_figures_codex_review.py
tests/test_figures_help.py
tests/test_figures_prefetch_boundary.py
tests/test_figures_prefetch.py
tests/test_figures_prefetch_review_fixes.py
tests/test_figures_show_me.py
tests/test_find_sources_intents.py
tests/test_followup_codex_review.py
tests/test_followup_diagnostic_selection.py
tests/test_followup_generate_e2e.py
tests/test_followup_journey.py
tests/test_followup_migration.py
tests/test_followup_router.py
tests/test_followups_batch6_review_fixes.py
tests/test_followups_batch6_verify_fixes.py
tests/test_followup_single_use.py
tests/test_followups_nov2_help_fold.py
tests/test_followup_successor.py
tests/test_followup_workflow.py
tests/test_forecast_receipts.py
tests/test_goal_scope_material.py
tests/test_grade_resolution_pipeline.py
tests/test_graph_editor_reads.py
tests/test_held_grade_composition.py
tests/test_held_grade_evidence.py
tests/test_help_assist_work_md_migration.py
tests/test_help_fold_attach_successor.py
tests/test_hint_authored_reveal_ruling.py
tests/test_hint_blind.py
tests/test_hint_discriminating.py
tests/test_hint_evidence.py
tests/test_hint_feedback_texts.py
tests/test_hint_h2a_review.py
tests/test_hint_h2a_review_round2.py
tests/test_hint_h2a_review_round3.py
tests/test_hint_h2b_fix3.py
tests/test_hint_h2b_rereview.py
tests/test_hint_h2b_review.py
tests/test_hint_kill_switch.py
tests/test_hint_outcome.py
tests/test_hint_report.py
tests/test_hint_service.py
tests/test_hint_telemetry.py
tests/test_host_queue_revision.py
tests/test_import_split_parity.py
tests/test_independent_group_counting.py
tests/test_ingest_jobs.py
tests/test_ingest_latency_journey.py
tests/test_ingest_runner.py
tests/test_init.py
tests/test_instrument_servability_journeys.py
tests/test_integration_daily_loop_field.py
tests/test_intent_codex_rereview.py
tests/test_intent_fix_round4.py
tests/test_intent_orchestrator_rulings.py
tests/test_intent_rpc.py
tests/test_inventory_merge_parallel.py
tests/test_judge_routes.py
tests/test_keep_local_retired.py
tests/test_km2_activation.py
tests/test_km4_taxonomy.py
tests/test_knowledge_map_text_neighbors.py
tests/test_learner_blindness_relax_codex_review.py
tests/test_learner_blindness_relax.py
tests/test_learner_data_relax_2.py
tests/test_learner_pick_proposal.py
tests/test_learner_report_superseded.py
tests/test_learner_text_gaps_composition.py
tests/test_learner_text_gaps_flow.py
tests/test_learner_text_gaps_rereview.py
tests/test_learner_text_gaps_review.py
tests/test_library_ask_review.py
tests/test_library_exercises.py
tests/test_lp_claim_fixes.py
tests/test_lp_claim_fixes_rereview.py
tests/test_lp_claim_fixes_review.py
tests/test_mcp_c1a_landing.py
tests/test_mcp_runtime.py
tests/test_method_explicit_upgrade.py
tests/test_mobile_allowlist.py
tests/test_mobile_handoff.py
tests/test_mobile_host_coexistence.py
tests/test_mobile_jobs_migration.py
tests/test_mobile_jobs.py
tests/test_mobile_rpc.py
tests/test_mobile_two_process.py
tests/test_module_catalog_inventory.py
tests/test_mvp011_upgrade.py
tests/test_mvp013_upgrade.py
tests/test_mvp014_upgrade.py
tests/test_mvp015_upgrade.py
tests/test_mvp016_upgrade.py
tests/test_mvp017_upgrade.py
tests/test_mvp018_upgrade.py
tests/test_mvp020_upgrade.py
tests/test_mvp021_upgrade.py
tests/test_mvp022_upgrade.py
tests/test_mvp023_upgrade.py
tests/test_mvp024_upgrade.py
tests/test_notes_as_learner_text.py
tests/test_notes_c2b_review5.py
tests/test_owner_capture_1025.py
tests/test_p2_acceptance.py
tests/test_p2_leakage_suite.py
tests/test_pfc_unverified_unassessed.py
tests/test_placement_diagnosis_decides.py
tests/test_placement_opening_probes.py
tests/test_placement_sidecar.py
tests/test_placement_split_grades.py
tests/test_plan_determinism_landing.py
tests/test_plan_determinism.py
tests/test_plan_first_transport_grant_scope.py
tests/test_plan_first_transport_offer_grants.py
tests/test_plan_first_transport_offer_grants_r5.py
tests/test_plan_first_transport.py
tests/test_plan_first_transport_today_quiet.py
tests/test_plan_follows_path.py
tests/test_post_attempt_pipeline.py
tests/test_post_attempt_worker.py
tests/test_pr4_superseded_claims_landing.py
tests/test_practice_index_adapters.py
tests/test_probe_audit.py
tests/test_probe_block_end.py
tests/test_probe_coverage.py
tests/test_probe_dialogue.py
tests/test_probe_episodes.py
tests/test_probe_hierarchy.py
tests/test_probe_instance_generation.py
tests/test_probe_lifecycle.py
tests/test_probe_llm_instances.py
tests/test_probe_longform_families.py
tests/test_probe_orchestration_remainder.py
tests/test_probe_policy.py
tests/test_probe_pool_empty.py
tests/test_probe_predictive_eig.py
tests/test_probe_remint.py
tests/test_probe_robust_cutover.py
tests/test_probe_surface_mint.py
tests/test_public_tip_guards.py
tests/test_question_promotions.py
tests/test_quick_add.py
tests/test_rbeq_pr2_landing.py
tests/test_reader_ca1_as_printed.py
tests/test_reader_ca1_codex_review.py
tests/test_reader_ca2_astra_handoff_recovery.py
tests/test_reader_ca2_codex_rereview.py
tests/test_reader_ca2_codex_review.py
tests/test_reader_ca2_fix_orchestrator.py
tests/test_reader_ca2_one_ask.py
tests/test_reader_cues.py
tests/test_reader_followups_successor.py
tests/test_reader_formative_texts.py
tests/test_reader_guidance.py
tests/test_reader_pdf_selection.py
tests/test_reader_question_note_id_placement.py
tests/test_reader_recap.py
tests/test_reader_recap_review.py
tests/test_reader_recap_review_r2.py
tests/test_reader_recap_review_r3.py
tests/test_reader_rw1b_review.py
tests/test_reader_rw2b_fix10.py
tests/test_reader_rw2b_fix11.py
tests/test_reader_rw2b_fix12.py
tests/test_reader_rw2b_fix13.py
tests/test_reader_rw2b_fix14.py
tests/test_reader_rw2b_fix4.py
tests/test_reader_rw2b_fix5.py
tests/test_reader_rw2b_review.py
tests/test_reader_rw3a_landing.py
tests/test_reader_rw4b_admission_idempotency.py
tests/test_reader_rw4b_fix6.py
tests/test_reader_workbench_rw2a.py
tests/test_reader_wrap_up.py
tests/test_reading_request_sweep.py
tests/test_reading_step_switch.py
tests/test_rebuild_equivalence.py
tests/test_rebuild_equivalence_review.py
tests/test_recurrence_commands.py
tests/test_recurrence_live.py
tests/test_recurrence_merge_composition.py
tests/test_reference_gate_imports.py
tests/test_regrade_contract_replay.py
tests/test_regrade_contract_successor.py
tests/test_regrade_contract_upgrade.py
tests/test_request_origin.py
tests/test_required_method_grading.py
tests/test_required_method_round3_review.py
tests/test_reread_safety_landing.py
tests/test_reread_safety.py
tests/test_reveal_ledger.py
tests/test_router_card_reading_gaps.py
tests/test_router_coldness_covariates.py
tests/test_router_g3_propensity.py
tests/test_router_g4_restraint.py
tests/test_router_g7_fallback.py
tests/test_router_offer_log.py
tests/test_router_outcomes.py
tests/test_router_p2_bridge.py
tests/test_router_presentations.py
tests/test_router_probe_ties.py
tests/test_router_r1_composition.py
tests/test_router_r2a_landing.py
tests/test_router_r2a_serving.py
tests/test_router_r2b_agreement.py
tests/test_router_r2bc_landing.py
tests/test_router_r2b_requests.py
tests/test_router_r2b_serving.py
tests/test_router_r2c_retrieval.py
tests/test_router_r2c_teach_back.py
tests/test_route_rules_in_grader.py
tests/test_rw2c_switch_off.py
tests/test_scheduler_probe_eig.py
tests/test_scheduler.py
tests/test_secondary_attach.py
tests/test_serve_eligibility.py
tests/test_serve_eligibility_review.py
tests/test_session_ownership.py
tests/test_settings_store.py
tests/test_sidecar_adjudication.py
tests/test_sidecar_close_cancels_jobs.py
tests/test_sidecar_contract.py
tests/test_sidecar_exams.py
tests/test_sidecar_goals.py
tests/test_sidecar_idle_threads.py
tests/test_sidecar_item_authoring.py
tests/test_sidecar_item_presentation.py
tests/test_sidecar_measurement.py
tests/test_sidecar_probe.py
tests/test_sidecar_serializer_snapshot.py
tests/test_sidecar_teach_back.py
tests/test_sidecar_trace_and_clarification.py
tests/test_sidecar_transport.py
tests/test_sidecar_tutor_qa.py
tests/test_simulation.py
tests/test_source_deletion.py
tests/test_source_exercise_import.py
tests/test_source_retrieval_search.py
tests/test_source_sets.py
tests/test_source_set_synthesis.py
tests/test_sqlite_file_copies.py
tests/test_sqlite_wal_lifecycle.py
tests/test_sqlite_wal.py
tests/test_state_sync_scheduling_race.py
tests/test_structured_transport_parity.py
tests/test_stuck_prompt_composition.py
tests/test_stuck_prompt.py
tests/test_subject_registry.py
tests/test_table_roles.py
tests/test_teacher_te0_confidence_events.py
tests/test_teacher_te0_fix_round2.py
tests/test_teacher_te0_review_fixes.py
tests/test_teacher_te1b_review_fixes.py
tests/test_teacher_te1b_suggestions.py
tests/test_teacher_te1_successor.py
tests/test_today_surfaces.py
tests/test_tool_dispatch_policy.py
tests/test_tool_registry.py
tests/test_tools_cli.py
tests/test_tracked_fixture_databases.py
tests/test_tui_practice.py
tests/test_ux_phase1_add_source.py
tests/test_ux_phase1_connect_ai.py
tests/test_ux_phase1_finish.py
tests/test_ux_phase1_landing.py
tests/test_ux_phase1_review_fixes.py
tests/test_ux_phase1_round2_rereview.py
tests/test_ux_phase1_round2_review.py
tests/test_ux_phase1_usability_round1.py
tests/test_ux_phase1_usability_round2.py
tests/test_ux_phase2_shell.py
tests/test_ux_phase4_feedback.py
tests/test_ux_phase4_landing.py
tests/test_value_candidates.py
tests/test_vault_epigraphs.py
tests/test_vault_watcher_refresh.py
tests/test_voi_forecasts.py
tests/test_voi_merge_composition.py
tests/test_voi_stopping.py
tests/test_voi_v2.py
tests/test_workbench_assistance.py
tests/test_workbench_check.py
tests/test_workbench_in_session_gaps.py
tests/test_workbench_text_gaps.py
tests/test_workbench_trace.py

</details>

## Re-review

Review job `20261104-014917-A3gt3E` (gpt-6.1-sol), verdict REOPENED. It confirmed F1, F2, F3, F4, F6 and F8 as fixed, reopened F5 and F7, and added F9 and F10. All four reproduced as failing tests before the fix, and all four are fixed in `06461f09cc`. Tests: the `test_f5_rereview_*`, `test_f7_rereview_*`, `test_f9_*` and `test_f10_*` tests in `tests/test_followup_codex_review.py`.

| Id | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F5 | High | Missing, incomplete or stale provenance admitted a cause, and recorded learner questions weren't read | fixed | `06461f09cc` | `test_f5_rereview_*`: each kind at both requests, every input field, a question no longer on record, a vault with nothing to protect, exam work elsewhere |
| F7 | Medium | `skipped` committed before the probe closed | fixed | `06461f09cc` | `test_f7_rereview_*`: a crash in cleanup at each of four doors and two points, a standing plan after a startup crash, preference and outcome with the move, skip through the sidecar |
| F9 | Medium | Decision reuse bypassed current hard refusals | fixed | `06461f09cc` | `test_f9_*`: "Not now" and a blocking check, on both arms, with no plan, during authoring, after a crash that pinned |
| F10 | Medium | An interrupted withdrawal couldn't finish its cleanup | fixed | `06461f09cc` | `test_f10_*`: a crash at each cleanup step and through a job, a closed probe's candidate, a failed workflow's leftovers |

**F5.** `hypotheses_exam_reason` now needs a complete record whose hash matches the statement as it stands. It checks answers, items, solution items, sources and recorded learner questions before either request. A question counts through its attempt and its item; one no longer on record is refused. Such a miss takes the practice lane. The workflow event says `causes_not_accounted_for`, apart from `causes_from_exam_material`, so the two can be counted.

One departure from the finding's words: where the vault holds no exam or held-out material, no live reservation and no exam work (`PastWork.nothing_exam_to_quote`), an uncovered record doesn't refuse, since there is nothing it could quote. The recorded inputs are still checked. Without this, old causes would silently lose the probe lane on a vault with no exams, with no protection gained. Spec §3.1 says this.

**F7.** New `workflow.skip_and_close` commits the move and the closing together. `settle_open_when_off`, `retire_waiting`, `continue_without` and `abandon` all use it, since all four had the same gap. The last two also commit their preference and outcome in that transaction. A crash now leaves the workflow open, so the next startup or click redoes it.

**F9.** `decide_once` keeps the recorded draw and asks `hard_refusal` again when the arm would still generate. A refusal that holds moves the workflow to `refused` and appends a `refused` outcome against the existing decision; the decision row and the workflow's `chosen_ref` stay as drawn. The refusals are asked once more after authoring, before anything is written, so a "Not now" during the model call stops the offer. What an interrupted run left is withdrawn before the decision, so a refused retry leaves nothing behind.

**F10.** New `identity.withdraw` retires the probe, ends its open presentations and rejects its candidates in one commit; `retire_unbound` runs it under one transaction, so a crash leaves the item selected for the next recovery. `admission.withdraw_interrupted` is gone.

**Beyond the findings, in the same code:**

- **`abandon` raised on any open workflow's probe.** `serving.abandon` read `wf.OPEN_STATES`, which the module didn't have, so `skip_practice_item` and the plan's skip raised `AttributeError` for a workflow's probe. That is a stranded Next the earlier tests missed, because they only took the workflow-less branch. `workflow.OPEN_STATES` now exists, and a test goes through the sidecar.
- **Every closed probe's candidate is rejected, not only an interrupted one's.** `close_probe`, `abandon` and the worker's failure paths all use `withdraw`. An `active` candidate on a retired item would otherwise stay selectable by the predecessor's offer after the switch goes off, pinning a question every door refuses.
- **`fail_workflow` withdraws what the last run left,** in the commit that fails the workflow and enqueues the need, or the need's own question hits `duplicate_instrument_class`.
- **`close_probe` also withdraws anything unbound,** for a workflow skipped after a crash and before its retry.
- **Smaller commits:** refused and no-intervention moves commit with their outcome, and the ready or waiting move with its binding.

### For the owner

1. **A vault with exam material sends causes without a complete, current record to the practice lane.** The learner gets no question there, and feedback is released at once. Causes written before records existed (migration 205), or by a diagnoser whose history includes such text, are the likely cases. I did not open any owner vault, so how often this happens there is unmeasured; count `causes_not_accounted_for` in `followup_workflow_events` on a copy. If it is common on the exam vaults, the choice is between this protection and the probe lane there.
2. **A retry whose author returns a question identical to the crashed run's is refused** (`probe_item_not_eligible`), because the item id is already retired. The learner gets no question and Next goes on. I saw this only with a fake that repeats itself; it is left as it is.

### Gate

- `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0`.
- `lint-imports --no-cache` (empty env): 42 contracts kept, 0 broken, so the frozen-cycles list holds.
- Targeted pytest, capped scope, `-n 6`, on the 395 files below: **7566 passed, 46 skipped, 8 xfailed, 0 failed** (42 min). It includes the CLI help snapshot, the process-launch list (`test_codex_lockdown_round3.py`), the display label's audit (`test_sidecar_measurement.py`), serializer, desktop RPC, mobile allowlist, architecture, table roles, judge routes and public-tip guards.
- Durability, `--durable-sqlite` on the seven FG1 test files (a store module changed; no migration did): **149 passed**.
- References: the schema didn't change, but moved source lines made the catalogs stale, so all three were regenerated. DB validate `errors: []` (385 table notes), desktop 318 TS and 6 Rust, modules 1188 notes and 66 maps, vault validation passes.
- No frontend or `src-tauri` change, so no npm run, vitest or `cargo check`.
- The full suite, the whole durability lane and the whole vitest run were not run, per the owner's rule: they are for the landing gate.
- All scripts and `lint-imports` ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. One exception: the small patch scripts that rewrote source text with plain `python3` ran without the wrapper; they imported nothing from the project and made no calls. No model call of any kind; every model-backed test uses fakes.

<details><summary>Test files run (re-review)</summary>

tests/followup_serve_helpers.py
tests/test_active_errors_overlay.py
tests/test_ad1_attempt_columns.py
tests/test_ad1_codex_rereview_fixes.py
tests/test_ad1_codex_review_fixes.py
tests/test_ad1_fix_round4.py
tests/test_ad1_fix_round5.py
tests/test_ad1_fix_round6.py
tests/test_ad23_contract.py
tests/test_ad23_fix_r8.py
tests/test_ad23_fix_review.py
tests/test_ad23_intent_compose.py
tests/test_ad23_pool_membership.py
tests/test_ad23_successor.py
tests/test_ad2_serving.py
tests/test_ad3_dose_arm.py
tests/test_adaptive_difficulty_ad1.py
tests/test_ai_config.py
tests/test_ai_runtime.py
tests/test_ai_tool_isolation.py
tests/test_approach_map_replay.py
tests/test_approach_maps.py
tests/test_architecture.py
tests/test_assumed_known.py
tests/test_attempt_completion.py
tests/test_attempt_content_state_successor.py
tests/test_attempt_write_order.py
tests/test_batch3_landing.py
tests/test_build_study_map_routing.py
tests/test_canonical_projection_fold_skip.py
tests/test_canonical_projection_rollout.py
tests/test_capture_desktop.py
tests/test_causal_attribution_p2.py
tests/test_causal_orchestrator.py
tests/test_causal_p2_acceptance.py
tests/test_causal_probe_commissioning.py
tests/test_causal_repair_sidecar_rpcs.py
tests/test_causal_shadow_selection.py
tests/test_characterization_assessment_exam.py
tests/test_characterization_probe_regrade.py
tests/test_characterization_probe_replay.py
tests/test_chatgpt_plan_sidecar.py
tests/test_cli_generate_practice.py
tests/test_cli_help_snapshot.py
tests/test_codex_lockdown_frozen.py
tests/test_codex_lockdown_round3.py
tests/test_codex_runtime.py
tests/test_coldness_receipt.py
tests/test_cold_retry_reschedule.py
tests/test_collection_dataset.py
tests/test_config_refactor.py
tests/test_coordinated_migrations.py
tests/test_curriculum_c1_fix_round3.py
tests/test_curriculum_c1_fix_round4.py
tests/test_curriculum_c1_plan_follows_path.py
tests/test_daily_loop_golden_path_lifecycle.py
tests/test_daily_loop_lo_lifecycle_serving.py
tests/test_daily_loop_reader_retire.py
tests/test_daily_loop_reentry_break.py
tests/test_daily_loop_reentry_cap.py
tests/test_daily_loop_reference_adoption.py
tests/test_daily_loop_start_minutes.py
tests/test_daily_plan_composition.py
tests/test_daily_plan_kill_switch.py
tests/test_daily_plan_owner_decisions.py
tests/test_daily_plan_reading.py
tests/test_daily_plan_reentry.py
tests/test_daily_plan_replay.py
tests/test_daily_plan_review_regressions.py
tests/test_daily_plan_rpc.py
tests/test_data_capture_a1_prefilter.py
tests/test_data_capture_a2_measurement.py
tests/test_data_capture_a4_delayed_completion.py
tests/test_data_capture_a5_not_ready_floor.py
tests/test_data_capture_a6_delayed_pick.py
tests/test_data_capture_codex_review.py
tests/test_data_capture_landing_review.py
tests/test_data_capture_phone.py
tests/test_data_capture_report.py
tests/test_data_capture_successor.py
tests/test_decider_landing.py
tests/test_deliverable_path.py
tests/test_desktop_rpc_contract.py
tests/test_device_eligibility.py
tests/test_diagnosis_async_router.py
tests/test_diagnosis_card.py
tests/test_diagnosis_embeddings.py
tests/test_diagnosis_input_provenance_landing.py
tests/test_diagnosis_input_provenance.py
tests/test_diagnosis_pipeline.py
tests/test_diagnosis_reports.py
tests/test_diagnostic_probe_freshness.py
tests/test_dialogue_causal_join.py
tests/test_doctor.py
tests/test_dual_authority_administration.py
tests/test_e0_relabel_round.py
tests/test_embedding_route_isolation.py
tests/test_evsi_router_composition.py
tests/test_exam_pool.py
tests/test_exam_protection_identity.py
tests/test_exam_protection.py
tests/test_exam_protection_review.py
tests/test_exam_session.py
tests/test_facet_identity_actions.py
tests/test_facet_identity.py
tests/test_facet_reword_paths.py
tests/test_facet_rewords.py
tests/test_facet_state_write_on_change.py
tests/test_field_signal_production_paths.py
tests/test_field_split_outcomes.py
tests/test_field_workbench_signals.py
tests/test_figures_codex_review.py
tests/test_figures_help.py
tests/test_figures_prefetch_boundary.py
tests/test_figures_prefetch.py
tests/test_figures_prefetch_review_fixes.py
tests/test_figures_show_me.py
tests/test_find_sources_intents.py
tests/test_followup_codex_review.py
tests/test_followup_diagnostic_selection.py
tests/test_followup_generate_e2e.py
tests/test_followup_journey.py
tests/test_followup_migration.py
tests/test_followup_router.py
tests/test_followups_batch6_review_fixes.py
tests/test_followups_batch6_verify_fixes.py
tests/test_followup_single_use.py
tests/test_followups_nov2_help_fold.py
tests/test_followup_successor.py
tests/test_followup_workflow.py
tests/test_forecast_receipts.py
tests/test_goal_scope_material.py
tests/test_grade_resolution_pipeline.py
tests/test_graph_editor_reads.py
tests/test_held_grade_composition.py
tests/test_held_grade_evidence.py
tests/test_help_assist_work_md_migration.py
tests/test_help_fold_attach_successor.py
tests/test_hint_authored_reveal_ruling.py
tests/test_hint_blind.py
tests/test_hint_discriminating.py
tests/test_hint_evidence.py
tests/test_hint_feedback_texts.py
tests/test_hint_h2a_review.py
tests/test_hint_h2a_review_round2.py
tests/test_hint_h2a_review_round3.py
tests/test_hint_h2b_fix3.py
tests/test_hint_h2b_rereview.py
tests/test_hint_h2b_review.py
tests/test_hint_kill_switch.py
tests/test_hint_outcome.py
tests/test_hint_report.py
tests/test_hint_service.py
tests/test_hint_telemetry.py
tests/test_host_queue_revision.py
tests/test_import_split_parity.py
tests/test_independent_group_counting.py
tests/test_ingest_jobs.py
tests/test_ingest_latency_journey.py
tests/test_ingest_runner.py
tests/test_init.py
tests/test_instrument_servability_journeys.py
tests/test_integration_daily_loop_field.py
tests/test_intent_codex_rereview.py
tests/test_intent_fix_round4.py
tests/test_intent_orchestrator_rulings.py
tests/test_intent_rpc.py
tests/test_inventory_merge_parallel.py
tests/test_judge_routes.py
tests/test_keep_local_retired.py
tests/test_km2_activation.py
tests/test_km4_taxonomy.py
tests/test_knowledge_map_text_neighbors.py
tests/test_learner_blindness_relax_codex_review.py
tests/test_learner_blindness_relax.py
tests/test_learner_data_relax_2.py
tests/test_learner_pick_proposal.py
tests/test_learner_report_superseded.py
tests/test_learner_text_gaps_composition.py
tests/test_learner_text_gaps_flow.py
tests/test_learner_text_gaps_rereview.py
tests/test_learner_text_gaps_review.py
tests/test_library_ask_review.py
tests/test_library_exercises.py
tests/test_lp_claim_fixes.py
tests/test_lp_claim_fixes_rereview.py
tests/test_lp_claim_fixes_review.py
tests/test_mcp_c1a_landing.py
tests/test_mcp_runtime.py
tests/test_method_explicit_upgrade.py
tests/test_mobile_allowlist.py
tests/test_mobile_handoff.py
tests/test_mobile_host_coexistence.py
tests/test_mobile_jobs_migration.py
tests/test_mobile_jobs.py
tests/test_mobile_rpc.py
tests/test_mobile_two_process.py
tests/test_module_catalog_inventory.py
tests/test_mvp011_upgrade.py
tests/test_mvp013_upgrade.py
tests/test_mvp014_upgrade.py
tests/test_mvp015_upgrade.py
tests/test_mvp016_upgrade.py
tests/test_mvp017_upgrade.py
tests/test_mvp018_upgrade.py
tests/test_mvp020_upgrade.py
tests/test_mvp021_upgrade.py
tests/test_mvp022_upgrade.py
tests/test_mvp023_upgrade.py
tests/test_mvp024_upgrade.py
tests/test_notes_as_learner_text.py
tests/test_notes_c2b_review5.py
tests/test_owner_capture_1025.py
tests/test_p2_acceptance.py
tests/test_p2_leakage_suite.py
tests/test_pfc_unverified_unassessed.py
tests/test_placement_diagnosis_decides.py
tests/test_placement_opening_probes.py
tests/test_placement_sidecar.py
tests/test_placement_split_grades.py
tests/test_plan_determinism_landing.py
tests/test_plan_determinism.py
tests/test_plan_first_transport_grant_scope.py
tests/test_plan_first_transport_offer_grants.py
tests/test_plan_first_transport_offer_grants_r5.py
tests/test_plan_first_transport.py
tests/test_plan_first_transport_today_quiet.py
tests/test_plan_follows_path.py
tests/test_post_attempt_pipeline.py
tests/test_post_attempt_worker.py
tests/test_pr4_superseded_claims_landing.py
tests/test_practice_index_adapters.py
tests/test_probe_audit.py
tests/test_probe_block_end.py
tests/test_probe_coverage.py
tests/test_probe_dialogue.py
tests/test_probe_episodes.py
tests/test_probe_hierarchy.py
tests/test_probe_instance_generation.py
tests/test_probe_lifecycle.py
tests/test_probe_llm_instances.py
tests/test_probe_longform_families.py
tests/test_probe_orchestration_remainder.py
tests/test_probe_policy.py
tests/test_probe_pool_empty.py
tests/test_probe_predictive_eig.py
tests/test_probe_remint.py
tests/test_probe_robust_cutover.py
tests/test_probe_surface_mint.py
tests/test_public_tip_guards.py
tests/test_question_promotions.py
tests/test_quick_add.py
tests/test_rbeq_pr2_landing.py
tests/test_reader_ca1_as_printed.py
tests/test_reader_ca1_codex_review.py
tests/test_reader_ca2_astra_handoff_recovery.py
tests/test_reader_ca2_codex_rereview.py
tests/test_reader_ca2_codex_review.py
tests/test_reader_ca2_fix_orchestrator.py
tests/test_reader_ca2_one_ask.py
tests/test_reader_cues.py
tests/test_reader_followups_successor.py
tests/test_reader_formative_texts.py
tests/test_reader_guidance.py
tests/test_reader_pdf_selection.py
tests/test_reader_question_note_id_placement.py
tests/test_reader_recap.py
tests/test_reader_recap_review.py
tests/test_reader_recap_review_r2.py
tests/test_reader_recap_review_r3.py
tests/test_reader_rw1b_review.py
tests/test_reader_rw2b_fix10.py
tests/test_reader_rw2b_fix11.py
tests/test_reader_rw2b_fix12.py
tests/test_reader_rw2b_fix13.py
tests/test_reader_rw2b_fix14.py
tests/test_reader_rw2b_fix4.py
tests/test_reader_rw2b_fix5.py
tests/test_reader_rw2b_review.py
tests/test_reader_rw3a_landing.py
tests/test_reader_rw4b_admission_idempotency.py
tests/test_reader_rw4b_fix6.py
tests/test_reader_workbench_rw2a.py
tests/test_reader_wrap_up.py
tests/test_reading_request_sweep.py
tests/test_reading_step_switch.py
tests/test_rebuild_equivalence.py
tests/test_rebuild_equivalence_review.py
tests/test_recurrence_commands.py
tests/test_recurrence_live.py
tests/test_recurrence_merge_composition.py
tests/test_reference_gate_imports.py
tests/test_regrade_contract_replay.py
tests/test_regrade_contract_successor.py
tests/test_regrade_contract_upgrade.py
tests/test_request_origin.py
tests/test_required_method_grading.py
tests/test_required_method_round3_review.py
tests/test_reread_safety_landing.py
tests/test_reread_safety.py
tests/test_reveal_ledger.py
tests/test_router_card_reading_gaps.py
tests/test_router_coldness_covariates.py
tests/test_router_g3_propensity.py
tests/test_router_g4_restraint.py
tests/test_router_g7_fallback.py
tests/test_router_offer_log.py
tests/test_router_outcomes.py
tests/test_router_p2_bridge.py
tests/test_router_presentations.py
tests/test_router_probe_ties.py
tests/test_router_r1_composition.py
tests/test_router_r2a_landing.py
tests/test_router_r2a_serving.py
tests/test_router_r2b_agreement.py
tests/test_router_r2bc_landing.py
tests/test_router_r2b_requests.py
tests/test_router_r2b_serving.py
tests/test_router_r2c_retrieval.py
tests/test_router_r2c_teach_back.py
tests/test_route_rules_in_grader.py
tests/test_rw2c_switch_off.py
tests/test_scheduler_probe_eig.py
tests/test_scheduler.py
tests/test_secondary_attach.py
tests/test_serve_eligibility.py
tests/test_serve_eligibility_review.py
tests/test_session_ownership.py
tests/test_settings_store.py
tests/test_sidecar_adjudication.py
tests/test_sidecar_close_cancels_jobs.py
tests/test_sidecar_contract.py
tests/test_sidecar_exams.py
tests/test_sidecar_goals.py
tests/test_sidecar_idle_threads.py
tests/test_sidecar_item_authoring.py
tests/test_sidecar_item_presentation.py
tests/test_sidecar_measurement.py
tests/test_sidecar_probe.py
tests/test_sidecar_serializer_snapshot.py
tests/test_sidecar_teach_back.py
tests/test_sidecar_trace_and_clarification.py
tests/test_sidecar_transport.py
tests/test_sidecar_tutor_qa.py
tests/test_simulation.py
tests/test_source_deletion.py
tests/test_source_exercise_import.py
tests/test_source_retrieval_search.py
tests/test_source_sets.py
tests/test_source_set_synthesis.py
tests/test_sqlite_file_copies.py
tests/test_sqlite_wal_lifecycle.py
tests/test_sqlite_wal.py
tests/test_state_sync_scheduling_race.py
tests/test_structured_transport_parity.py
tests/test_stuck_prompt_composition.py
tests/test_stuck_prompt.py
tests/test_subject_registry.py
tests/test_table_roles.py
tests/test_teacher_te0_confidence_events.py
tests/test_teacher_te0_fix_round2.py
tests/test_teacher_te0_review_fixes.py
tests/test_teacher_te1b_review_fixes.py
tests/test_teacher_te1b_suggestions.py
tests/test_teacher_te1_successor.py
tests/test_today_surfaces.py
tests/test_tool_dispatch_policy.py
tests/test_tool_registry.py
tests/test_tools_cli.py
tests/test_tracked_fixture_databases.py
tests/test_tui_practice.py
tests/test_ux_phase1_add_source.py
tests/test_ux_phase1_connect_ai.py
tests/test_ux_phase1_finish.py
tests/test_ux_phase1_landing.py
tests/test_ux_phase1_review_fixes.py
tests/test_ux_phase1_round2_rereview.py
tests/test_ux_phase1_round2_review.py
tests/test_ux_phase1_usability_round1.py
tests/test_ux_phase1_usability_round2.py
tests/test_ux_phase2_shell.py
tests/test_ux_phase4_feedback.py
tests/test_ux_phase4_landing.py
tests/test_value_candidates.py
tests/test_vault_epigraphs.py
tests/test_vault_watcher_refresh.py
tests/test_voi_forecasts.py
tests/test_voi_merge_composition.py
tests/test_voi_stopping.py
tests/test_voi_v2.py
tests/test_workbench_assistance.py
tests/test_workbench_check.py
tests/test_workbench_in_session_gaps.py
tests/test_workbench_text_gaps.py
tests/test_workbench_trace.py

</details>

## Final verify

Verify job `20261104-030053-ASNG4N` (gpt-6.1-sol), verdict REOPENED. It confirmed F1 to F6, F8 and F10 as fixed and reopened F7 and F9, with no new findings. Both are fixed under the orchestrator's rulings R1 and R2, which `docs/reviews/followup-fg1.md` records verbatim at landing. Tests: the `test_f7_verify_*` and `test_f9_verify_*` tests in `tests/test_followup_codex_review.py`.

| Id | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F7 | Medium | Terminal recovery paths left an interrupted run's probe live | fixed | `7465040da5` | `test_f7_verify_*`: eight exits after a crash that pinned, a crash inside the exit, an answer's leftovers, a shared episode, a late generator, the scan |
| F9 | Medium | Revalidation missed checks on the whole learning object | fixed | `8783ae293a` | `test_f9_verify_*`: at the retry and after authoring; another object or a non-blocking kind refuses nothing |

**How they were reproduced.** Against `c14d2d062d`, 19 of the 35 new F7 tests failed, including both of Codex's reproductions (`newer_grade`, `causes_not_accounted_for`); the other 16 are the scan's 15 checks on itself and a pin that the settled exit asks for no question. For F9, 2 of 3 failed: the retry reached authoring (`fake.calls` 1, wanted 0) and the workflow went `ready`, wanted `refused`. The third pins what must keep working.

**F7 (R1).** `workflow.finish` is now the only way into a terminal state. In one commit it moves the workflow and closes what the workflow prepared: its probe and anything unbound are withdrawn (retired, presentations ended, candidate rejected) and an empty episode is abandoned. `move` raises on a terminal state. `skip_and_close` is gone, since `finish` replaces it. `test_f7_verify_no_other_writer_of_a_terminal_state` walks `src/` and fails on a terminal `move`, a `to_state` it can't read, a `move_workflow` or `_apply_move` outside `finish` and `move`, or SQL that writes `followup_workflows.state` anywhere else. A second test checks that the scan catches each kind of writer.

**F9 (R2).** `router.hard_refusal` passes the workflow's learning object to `pending_machine_checks_for_factor`. The first decision uses the same function, so it changes too.

**What R1 needed that the finding didn't name:**

- **An interrupted run's episode.** A pin that never reached `ready` isn't on the workflow row, so nothing would have closed its episode. `store.episodes_pinned_by_workflow` finds it through `generated_probe_items` and the item's presentations. Only episodes this workflow pinned a probe on are touched, so an old `pending_items` episode with no such presentation stays as it is.
- **When an episode closes.** It now closes only if it is still open, has no observation and has no presentation left open. Before, a presentation not yet ended didn't stop it, so a skipped workflow could abandon an episode another revision's workflow had just pinned on.
- **An answer.** `probe_answered` also goes through `finish`, with `answered_item`: that question, its presentation and what its answer measured stay, and only leftovers close. The outcome binding now commits with the move.
- **A burn's reason.** On a terminal exit, an unbound probe's retirement carries the exit's reason instead of `publication_interrupted`, which stays for a retry.
- **A late generator.** It already withdrew its item; it now also closes the episode it pinned.

**Left as it is.** A workflow that had drawn a decision and then leaves by `newer_grade` or the practice lane appends no outcome against that decision. The finding doesn't cover this and it strands nothing, so it stays out of this fix.

R5's three Low items aren't fixed here, per that ruling.

### Gate

Targeted only, per the brief; the full gate comes at landing.

- `tests/test_followup_*.py`, `test_table_roles`, `test_coordinated_migrations`, `test_architecture`, capped scope, `-n 6`: **238 passed, 0 failed**.
- `--durable-sqlite` on the nine `tests/test_followup_*.py` files: **196 passed**.
- `lint-imports --no-cache`, empty env: **42 kept, 0 broken**.
- Not run yet: the reference catalogs. Moved source lines leave them stale until step 3 of the landing regenerates them.
- No model call; every model-backed test uses fakes.

## What the landing smoke found on real copies

The FG1 tests ran a joint vault whose items have no task features. Real vaults are blind and their items do have them, so these reached the smoke rather than a test. New fixture: `live_shape_vault`, `BlindRivalClient`, `live_miss` in `tests/followup_serve_helpers.py`; tests in `tests/test_followup_live_shape.py`. Each fix was reproduced first, on the fixture as well as on a copy.

| Fix | Commit | Reproduced | What changed |
|---|---|---|---|
| The `H_OTHER` arm | `8a6a50b24f` | `factor_not_probeable`, no question, on both real open factors and every fresh miss | A second `materialize_causal_episode` rewrote a factor's refs from the arms with a statement, and the open arm has none. At the tag the rewrite keeps it, and `author_probe` restores it on a row written earlier |
| Task features | `c9bc2c4f23` | `manipulation_audit_rejected` after one authoring call, for 32 of 32, 96 of 99 and 46 of 77 items | The audit diffs each task feature as an axis, and the author may declare only `AUTHOR_AXES`. The contract now names those axes as incidental, read from the missed item and the new one |
| The seven failures | `6b384c0278` | See below | |

**The older offer path ("Take the quick check") fails the same way.** With divergent causes, `commission_probe_instrument` returns `factor_not_probeable` on a live factor. It is fixed at the source behind `generate_and_serve_on`, so below mvp-0.45 and with the switch off the row is as it was, and a test pins that. At the tag, commissioning gets past the arm. A row written before the tag keeps the old failure on that path until `rebuild-derived-state` rewrites it, which the owner runs after the upgrade; checked on both real open factors. The lane restores the arm anyway.

**The seven failures of the first full run:**

| Test | Cause | Change |
|---|---|---|
| `test_ad23_inversion::test_the_codes_vocabulary_covers_the_incumbents_reasons` | AD's closed pool vocabulary lacked the two `generated_probe_*` gates, so a refusal reached AD as `pool:other` | The two codes added |
| `test_library_asks_migration` (2), `test_help_assists_schema` (2) | They imported `FOLLOWUP_ADDED_OBJECTS` and never used it | Added to their union: those objects are migration 241's own, by name |
| `test_e0_isolation::test_the_import_linter_contract_names_every_production_package` | The experiments contract didn't cover the three new packages, a real gap | `followup_run`, `followup_serve`, `followup_serve_upgrade` added |
| `test_followup_router::test_a_wait_keeps_its_room_and_next_continues_the_block` | No neighbour. Alone, 1 run in 60 fails: an unpinned draw leaves a one-item first block, so that advance is the boundary, where the fixture's made-up factor rightly retires the wait | The draw is pinned, and the test asserts the block has more than one item. The behaviour is unchanged |

## The owner's ruling of Nov 4, replacing R3

Commits `64883ad765`, `1aeac0b66f`, `34938523e9`. Tests: `tests/test_followup_reserved_only.py` (14 of the first 16 failed on the old rule). Spec §3.1 and §8 amended, with the date.

- **What stops a probe now.** A cause, or a generated question, that reproduces a question still reserved or withheld for an exam or an assessment. `causes_match_reserved` runs before the router's card and the author's prompt, over a cause's statement and the words of its typed target. `admission.persist_item` runs over the generated stem, key, rubric and hints before anything is written, and before the structural gate, which would otherwise call an exact echo a duplicate. The mint and batch paths refuse the same way at the tag.
- **What no longer does.** Past exam answers, finished-sitting work, and a missing, incomplete or stale record. `PastWork.exam_reason`, `nothing_exam_to_quote`, `CAUSE_UNRECORDED`, `causes_refusal`, `causes_from_exam_material` and `causes_not_accounted_for` are gone. The admission receipt keeps `causes_record`: per cause, its record's state and how many answers, exam answers, items, sources and questions it names. Counts, no words.
- **The new reason codes.** `cause_matches_reserved_question`, `question_matches_reserved_question`.
- **The list.** `withheld_items`' reasons `WITHHELD_EXAM` and `WITHHELD_RESERVED`, and held-out spans. No second list. A check waiting or a diagnostic probe isn't reserved, as before.
- **Context.** `build_context` leaves out an item's stem, the source question and the objective's summary when they quote a reserved question. Keys and rubrics of reserved items never entered it.
- **A sitting's own misses.** They can take the probe lane after `finish_exam`, inside the cap, with feedback not held, since the exam's report shows it. Nothing interrupts a sitting, because the pipeline runs at its end. Generated probes stay out of exam pools (`test_followup_single_use.py`).

**The measure.** The repo's own gate, `practice_leakage.check_leakage`: contiguous six-word shingles and distinctive numbers. Two additions, neither a new constant. A whole reserved stem counts, because a stem under six words has no shingle to match. And what an ordinary item already shows is subtracted, because the learner sees it anyway: this removes 57 of 2057 reserved shingles on linear_algebra, mostly formulas like `(u+v)+w = u+(v+w)`. `DEFAULT_SHINGLE_N` is now a registered `keep`.

- **It catches:** a reproduced phrase of six words or more, a whole stem, and a distinctive number. On linear_algebra's real questions, 15 of 15 stems and 15 of 15 keys match themselves.
- **It misses:** a paraphrase or a restatement with the same meaning, and a phrase of a reserved question that an ordinary item also shows.
- **It over-matches.** As a proxy for a new question, leave-one-out over linear_algebra's 84 ordinary items: 21 would match at order 6, all on topics with a reserved question, usually on a notation or subject phrase (`where f is r or c`). 6 at order 8, 2 at 10, 0 at 12. Real causes matching: 0 of 9. A false match on a question costs one paid authoring call and that miss's question. The order stays 6, the ingest gate's own value, and changing it is the owner's call.

**`linear_algebra`, fresh misses after the ruling:** 14 of 14 reach a question, against 0 of 14 before, and the machine check stopped 0. Those 14 use a fake author and fake causes. On the real copy, a cause quoting a real reserved stem settles as `cause_matches_reserved_question` with no authoring call, and an author echoing one settles as `question_matches_reserved_question` with no identity written; both released feedback and Next went on.

## Corrections to what was reported earlier

- **"An attempt with 7 causes" was wrong.** That attempt has 7 versions of 1 cause: 7 rows, one `episode_key`. It is from July 23, before the split diagnosis, with no model and no agent run.
- **"17 reserved items on linear_algebra" was wrong.** It counted other holds. There are 15 exam or held-out questions, plus 2 checks waiting and 1 diagnostic check.
- **Slips.** A bare `sqlite3` read of `schema_migrations` on a smoke copy, before the wrapper. A `git stash list` inside a chained command while committing, in the worktree, with its output discarded: the brief forbids it even in that form. Neither changed anything.

The references are stale until the gate's regeneration: code moved after `ec8343061b`.

### Gate for this section

Targeted only; the full gate hasn't resumed. The earlier full run was on `ec8343061b`, before these fixes.

- 27 test files (all `test_followup_*`, table roles, coordinated migrations, architecture, the registry audit, the seven failures' files, the label audit, CLI help snapshot, process-launch list, causal attribution, commissioning, acceptance, probe mint, public-tip guards), capped scope, `-n 6`: **475 passed, 0 failed**.
- `--durable-sqlite` on the `test_followup_*` files: **205 passed**.
- `lint-imports --no-cache`: **42 kept, 0 broken**.
- No model call; every model-backed test and smoke run uses fakes.

## R9 and R10

The rulings are verbatim in `docs/reviews/followup-fg1.md`, under "Landing onto main". Spec §4 and §8 amended, with the date.

### R9: rival causes get a factor (`7d730fa39d`)

`lanes.open_rival_factor`, just before `select_lane`, behind `generate_and_serve_on`. Tests: `tests/test_followup_rival_factor.py`; every shape failed first with no question and `no_open_factor`. Two older tests relied on the default fake's two causes settling on the practice lane, and now say which lane they mean.

- **All four shapes** (no `target_ref`, no repair suggestion, a repair aimed at another criterion, a trivial error type), with the router on ask now and on `no_intervention`. On the fixture: factor opens, question prepared and served, its answer closes the factor, feedback released, Next goes on. A decline makes no authoring call.
- **On the real copies**, with a plan and fake models, all 4 shapes on all 3 vaults: 23 of 24 runs pass every check. The other is linear_algebra's trivial shape with the router unforced: its floor drew `continue_current`, so the driver's "still held" check didn't apply. That is the wait arm working, not a fault. New model receipts: 0. Non-loopback sockets: 0. No Codex process.
- **A mark.** The factor carries `followup_rival_causes_v1`. The machine check sweep skips it, since it owes no mapping and a check would refuse its question.
- **Beyond the ruling's words: it closes when its question won't be asked.** On `no_intervention`, a refusal, a skip or the practice lane it closes as `retired`, `followup_declined`, in the move's commit. Left open it would hold the topic in the plan's repair lane with nothing to serve. A failed workflow keeps it for its need (§6.2), and an answered one resolves or stays open like any factor.
- **One concrete cause stays as it was.** So does an attempt that has had a factor of any status, or a grade held for review.

**Measurement.** Opening the factor leaves the rebuild's own facet, mastery and schedule snapshot and the certification rows unchanged. After an answered probe, facet and mastery match a mapped factor's run, compared to four places because mastery decays by the wall clock.

**Downstream, with no repair class.** No machine check owed, no cold retry or remediation opened (on a mapped factor either). The one difference is that a mapped factor has a `causal_probe_decision_receipts` row and this one has none, since the receipt is written on the post-attempt path before the factor exists. Nothing found requires it.

**What the learner sees after answering.** The worked answer and the causal feedback are released, with causes labelled "Possible explanation — not yet confirmed", as on a mapped factor. Repair suggestions appear if the diagnoser wrote any, with no common repair offer and no guided redo. Next goes on. With `no_repair` there is no repair text at all.

**Trivial-only misses do spend more.** Before R9, none. Now one authoring call per such miss when the diagnoser names two or more causes and the router asks, plus the retry on a reserved match, or one later call for the need if the workflow fails. On real history: 11 of 22 misses are trivial-only (linear_algebra 9 of 16, probability 2 of 3, arxiv_v2 0 of 3), but none was diagnosed and none has any cause on record, so **0 of them would spend a call as they stand**. The rate for new misses isn't measurable here.

**A limit of "the router decides".** With no plan there is no draw, so a weak case always gets its question (§5.1). With a plan and unreachable models the staged rule drew ask now at 98%. The router only declines weak cases when its models answer.

### R10: fewer false matches (`fa2f73234b`)

Reproduced first (`test_r10_*`). A matched phrase is asked of `source_block_fts`, whose porter tokenizer also counts a plural as the same word; one shown in a block `withheld.exam` doesn't cover no longer counts. A whole stem always counts. An index that can't answer shows nothing, so the check stands.

**Cost.** One index query per phrase that matched, memoized for the check; none for a question that matches nothing. Median 0.01 ms on linear_algebra (972 blocks), 0.08 ms on arxiv_v2 (4606), worst 13 ms. Building the reserved list: 11 ms, reading `withheld_items`: 25 ms.

| linear_algebra, 84 ordinary items as new questions, order 6 | Items that would match | Phrases matched |
|---|---|---|
| Before: ordinary items subtracted | 21 | 45 |
| After: source text outside held-out spans also subtracted | **21** | 44 |

**The subtraction barely helps on this copy.** It works (tested both ways), and no block here is held out. But the copy's 972 source blocks don't show these phrases: they are formulas and item-writers' wording (`where f is r or c`, `for all u v w v`). A vault with more of the book indexed may do better; that isn't measured.

**So the retry is what saves the question.** A draft that matches runs again at once, no backoff, told only the stretches of its own draft that matched, read back from a workflow note so a crash keeps them. `MAX_GENERATION_ATTEMPTS` stays 2 in all: a second match, or a match on an attempt that is already the second, settles as `question_matches_reserved_question`. A false match now costs one more paid call and usually keeps the question, if a real author avoids the phrase; a real run has to show that.

**Real questions, after both.** Linear_algebra's 15 stems and 15 keys all still match themselves. A real stem quoted in a cause settles with no author call. An author echoing one on both tries makes 2 calls, writes no identity, and settles on the practice lane, with feedback released and Next going on.

### Gate for this section

Numbers below are for the tip's code; the full gate hasn't resumed, and the references are stale until it does.

- 30 test files (all `test_followup_*`, table roles, coordinated migrations, architecture, the registry audit, the seven failures' files, the label audit, CLI help snapshot, process-launch list, causal attribution, orchestrator, factor deferral, commissioning, acceptance, probe mint, public-tip guards), capped scope, `-n 6`: **534 passed, 0 failed**.
- `--durable-sqlite` on the `test_followup_*` files: **232 passed, 0 failed**.
- `lint-imports --no-cache`: **42 kept, 0 broken**.
- No model call; every model-backed test and smoke run uses fakes.

## F20: the attempt limit across crashes

Verify job `20261104-053133-bwYwSu` (gpt-6.1-sol), over `30e1b53185..7fe97de9dd`, found this and no other defect. Ruling R11, recorded under "Landing onto main".

| Id | Severity | Title | Verdict | Test |
|---|---|---|---|---|
| F20 | Medium | Crash recovery exceeds R10's two-attempt limit | fixed | `test_f20_*` in `tests/test_followup_reserved_only.py` |

**Reproduced.** A crash doesn't requeue a job; its lease lapses and the next lease counts up. `MAX_GENERATION_ATTEMPTS` only bounded requeuing after a failure, so a third lease called the author: 3 calls, wanted 2. It failed for a draft that matched then a crash, a transport failure then a crash, two crashes after a pin, and a need job.

**Fixed.** The limit is checked before any authoring call. An exhausted workflow settles through `settle_practice_lane`, logged `generation_attempts_exhausted`: what the crashed runs prepared closes in the move's commit, feedback is released, the predecessor's chooser runs and Next goes on. The job isn't excluded from leasing, since that would strand Next. A job with no workflow (an entry or a need) ends as `failed` with the same code; no learner waits on it. Exits that cost nothing still take their own way out: a newer grade on a third lease settles as `newer_grade`. Every lease counts, including one that crashed before its call, so a job can end with fewer than two calls.

## R12: Next and a probe nobody would serve

The landing smoke found this, and it stopped the landing. `followup_next` told a ready workflow to continue whenever the plan feature was on, so the plan had to place the probe. A plan that had completed or been stopped never would, and neither would the queue screen. The question went unasked and the answer stayed held. The common case was the plan's last item: the screen fetches the next step while feedback shows (`dailyPlan.ts:111`), which completes the plan before generation finishes.

**The fix (`39f6b09965`).** `serving.plan_will_place`: the plan serves the probe only if the attempt's `plan_presentation_id` is set and today's plan is open. Otherwise Next opens it. No new field and no frontend change: the server already records where the attempt came from, validated when the attempt is written, so the phone and any later screen get this too. A wait whose question is still being written no longer holds Next, since what it held is already released.

**The matrix (`tests/test_followup_next_matrix.py`).** Through the real handlers, with the screen's fetch of the next step, 60 cells:

- Surface and plan state: plan × {open, complete, stopped before generation, stopped after}; queue × {the same four, none}; no plan × none.
- By workflow state: preparing, ready, waiting, a wait still being written, failed, settled.
- "Plan × none" doesn't exist, since a miss from the plan needs a plan.
- A plan can't complete after a ready probe without going through it, so "complete" closes before generation.

Each cell asserts that the next thing served is the probe, or that the feedback is released and Next goes on. Before the fix, 26 cells and one separate test failed: every ready and preparing cell with a closed plan or from the queue, and every wait still being written. All pass now. Two more tests: a queue miss with a plan open opens the probe and the plan doesn't serve it again; a wait that outlasts its plan has its answer released and its probe labelled exposed (§6.0).

**The measurement test (`dc5f4156b5`).** It now freezes the clock, so the two runs compare exactly and no tolerance is needed.

**Linear_algebra's miss that settled `no_open_factor`.** No defect; it's the bounded-deferral exit. The factor opened normally and `causal_factor_deferral` closed it at once as `escalated_unrepaired`, `unengaged_recurrences`, k=3, because the sweep repeats one cause's wording on a topic and skips every probe. R9 then doesn't reopen a closed factor. Six misses on that topic: all six get a question if each probe is answered; only the first two if each is skipped. A real learner would hit this only by skipping repeatedly on causes the deferral treats as the same. Feedback is released and Next goes on.

**The Decider's reachability probe.** It runs only if the route's provider is ready, which for the code-default `openrouter_decider` profile means `OPENROUTER_API_KEY` is present. There is no separate opt-in: an empty `ai.routing.router_decider` means that default profile, not off. Tested with every other route at `:9`:

| Case | Reaches for `openrouter.ai` |
|---|---|
| No key, route unset | No |
| Key present, route unset | Yes: the probe (no key and no learner text sent), then the paid decision request carrying the state card |
| Key present, `LEARNLOOP_ROUTER_MODELS=off` | No |

So a real vault with no route set but the key present does reach OpenRouter; the key's presence is the only consent. This predates FG1. It's reported to the coordinator and not changed here. On the smoke's guard, every such socket was refused, so nothing was delivered.

**Slips and a smoke-config gap.**

- About 70 refused attempts to `openrouter.ai` during the smoke: with a dummy key set, my `neutralize.py` left the Decider on its default URL. It now points at `127.0.0.1:9`. The guard refused every socket and nothing was delivered.
- One comparison ran under zsh, which didn't split a `--set`, so `neutralize.py` failed on that copy. It was discarded and rerun. Smoke scripts run under bash from here on.

**Reruns on the real copies, after this fix.** Routes down, the real-causes journey, and ask, Continue without it and wait on all three, with fake models unless a run says otherwise. Every run passes, with one expected exception: real causes with a plan fails only my driver's "the plan serves it" check. That attempt has no plan presentation, so under R12 Next correctly opens the probe, and it passes with no plan. Non-loopback attempts in the whole rerun: 0.

**A shadow read after each journey.** 0/0/0 on the 11 runs whose journey called `rebuild_derived_state` itself. On the 12 that didn't (routes down), one mastery row and one schedule row differ: `logit_mean` by about 1e-8 and `due_at` by one second. Main at mvp-0.44 shows the same after one plain miss with no FG1 code in the path: the live write uses the clock's sub-second time and replay uses the stored whole second. So this predates FG1, and a rebuild clears it. Not changed here.

**The two door checks.**

- `find_practice` returned 5 results on linear_algebra and 2 on probability, with the probe absent from both. It returned 0 on arxiv_v2, so that copy proves nothing.
- The exam-candidate check doesn't prove the exclusion on any copy. With the identity set emptied, the probe still isn't a candidate on linear_algebra (3 candidates) or probability (1), and arxiv_v2 has none. The pin is `test_followup_single_use.py`, where a generated item would otherwise be reserved.

### Gate for this section

Targeted only; references, the whole gate and timing wait for the coordinator.

- 31 test files, capped scope, `-n 6`: **601 passed, 0 failed**.
- `--durable-sqlite` on the 13 `test_followup_*` files: **299 passed**.
- `lint-imports --no-cache`: **42 kept, 0 broken**.

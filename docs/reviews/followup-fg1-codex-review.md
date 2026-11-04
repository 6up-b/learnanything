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

# Refactor D2b (part 2c): the second pass over tests that name old tags

Step D2b part 2c of arc D, on branch `refactor/d2b4-old-tag-tests-2`, based on main `655e7a2d07` (floor mvp-0.58, head mvp-0.59). Tests and test helpers only; nothing under `src/` changed; no test deleted. **This is a partial landing** (127 files edited, 1,793 of 3,331 below-the-floor cases moved to the head); what is not done is listed in section 7.

## 1. Method

- **Census.** The first pass's plugin, rebuilt as a scratch plugin (not committed): it wraps `tests.helpers.allow_below_floor`, which every test that opens a vault below the floor reaches (`tests/helpers.py`), and records the test, the vault's tag and the call stack's test-file frames; `version_floor.may_open_below_floor` is wrapped the same way for the first count. Candidates are the 988 `test_*.py` files that name a tag, a tag writer, a vault builder or import a helper that does (upgrade and successor files left out), run in chunks of 100 at `-n 4`, `-m "not arc_close"`. The 25 files the first pass's D4 list names are left out (another step owns them), which leaves 343 files.
- **Experiment.** As in the first pass: every old tag a helper writes is taken to the head and each case run. It is the sort (a test that fails there has the old path as its subject, a switch, or a difference to read) and it is necessary, not sufficient: it does not prove a test still tests anything. Here it found 158 all-passing files and 185 files with 534 failing cases.
- **Edit by helper, not by line.** The stack record names the site that writes each old tag, so the work went per helper default (section 3) and per file, not by a pattern over lines. After each helper edit the files that import it (`scripts/affected_tests.py`, then by hand) were run at the head; a test that failed there, and was in the experiment's failing set, kept its tag by naming it. A test's own explicit old tag was never touched, which is why a transition test (replay, upgrade, "written at", predecessor and successor in one body) cannot have been emptied by this pass: its body still names both tags (section 5).
- Scripts for mechanical exact edits (the scratch `pin.py`, `tagrep.py`, `pindef.py`, `localtag.py`): adding `version=<constant>` to the first call of a named helper in a named test; replacing the word `TAG` by the old constant inside named tests; adding `pin_default_tag(monkeypatch, <constant>)` as the first statement of named tests; moving a test file's `TAG = <X>_ALGORITHM_VERSION` to `LATEST_ALGORITHM_VERSION`. Each run was followed by the tests and `ruff`.

## 2. Census before and after

| | cases | files |
|---|---|---|
| before (this tip's parent), 343 files, `allow_below_floor` record | 3,331 | 336 |
| before, `may_open_below_floor` record (the first pass's) | 3,376 | 343 |
| after, `allow_below_floor` record | 1,538 | 255 |

After the last commit the 343 files ran green in full at `-n 4` (5,996 passed, 43 skipped on the owner-vault marker, 0 failed), and so did the 25 D4 files and the targeted gate (section 8). Files emptied: 81; partly moved: 89; untouched: 166. The 25 D4 files are not in the census; three of their shared helpers were changed so that they behave as before (section 3).

## 3. Per helper: the decision

Every default below moved to `LATEST_ALGORITHM_VERSION`, never a literal; "users" are the test files that call it.

| helper | decision | what the users that need the old tag do |
|---|---|---|
| `km2_write_path_helpers.build_mvp07_vault` (renamed `build_shared_facet_vault`) | default is the head | `KM2_OLD_TAG` (mvp-0.7): `test_km2_write_path` (1 test, fixture `old_tag_vault`), `test_measurement_corrections` (1) |
| `km3_projections_helpers.build_blueprint_vault` (`blueprint_vault` fixture) | default is the head | `BLUEPRINT_OLD_TAG` (mvp-0.7): `test_km3_projections` (4, fixture `blueprint_vault_old_tag`), `test_map_untested` (3), `test_sidecar_knowledge_model` (3), `test_sidecar_contract` (1), `test_today_headline` (1); `graph_editor_reads_helpers._blueprint_ctx` takes `version` |
| `followup_serve_helpers.TAG`, `rival_causes_vault` | `TAG` is the head; `built_at` names the tag the acceptance vault is built and synced at | `test_followup_journey` (the off arm of the predecessor test names the tag with the switch), `test_followup_generate_e2e` (1: built at mvp-0.7, stamped mvp-0.45), `test_followup_router` (1: a randomized check pin), `test_followup_next_matrix` (1 cell) |
| `causal_p2_acceptance_helpers._acceptance_vault` | **kept at mvp-0.7** (default is `KM2_OLD_TAG`, named): its users are the D4 test files, which move it | `followup_serve_helpers` passes the head |
| `followup_journey_helpers.journey` | head; `journey_old_tag` added | `test_hypothesis_marks_context` (1 test, a D4 file, one line: it asserts the card's version string) |
| 13 `TAG = <X>_ALGORITHM_VERSION` helpers: `cold_retry_reschedule`, `lp_claim_fixes_review`, `ih2_lessons_compete`, `curriculum_c1_plan_follows_path`, `plan_follows_path`, `ro5_calibration`, `te3b_offers`, `mobile_v3_probes`, `ro5_checks`, `teacher_te1b_suggestions`, `reader_ca2_codex_review`, `rospeed_join` (+ `version` param), `teacher_te2_probes` | `TAG` is the head | the tests of a tag constant, a predecessor arm or the tag's own plan/card name the old constant (about 90 places, section 4) |
| `teacher_fakes.build_teacher_vault` | default is the module's `DEFAULT_TAG` (the head); `pin_default_tag(monkeypatch, tag)` moves it for one test | 13 tests that read TE0/TE1's first lesson, cards and forecasts; the local helpers of those files build without a version, so the tag is moved at the module |
| `intent_fakes.make_intent_vault`, `reading_path_fixtures.build_path_vault`, `router_card_helpers._card_world` and `A` (also `mcp_c1a_landing_helpers`, `reader_rw3a_landing_helpers`), `forecast_receipts_helpers._diagnosed`, `pfc_unverified_unassessed_helpers._mapped_split_vault`, `recurrence_live_helpers._vault`, `probe_robust_cutover_helpers._load`, `reader_workbench_rw2a_helpers._vault`, `causal_factor_deferral_helpers._vault`, `teacher_te0_confidence_events_helpers._gathered_card` | default is the head (`causal_factor_deferral` drops its `set_algorithm_version`) | about 25 tests name the old constant, as above |
| 25 test files with a local `TAG = <X>_ALGORITHM_VERSION` (`ih3/ih4/ih6/ih7`, `ro1_*`, `ro4_*`, `ro5_*`, `ro6_tail_data`, `rofu_*`, `sg_slip_vs_gap`, `te3a`, `reader_ca2_one_ask` ...) | `TAG` is the head in 25 of 35 files; 10 were put back because more than half of their tests need the tag or their local helpers read `TAG` | the failing tests replace `TAG` by the constant |
| **not changed** (a user needs the old tag in most tests, or a D4 file uses it) | `assumed_known_helpers`, `learner_text_gaps*_helpers`, `data_capture_*`, `certification_cold_probe`, `goal_certification_any_of`, `required_method_grading`, `route_rules_in_grader`, `regrade_contract_successor` (D4 files); `split_live_helpers.split_vault` (default was already the head; its 285 remaining cases are callers that pass a tag, mostly `test_pfc_unverified_unassessed`, which is parametrized over every tag of `DIAGNOSIS_SPLIT_VERSIONS`), `daily_plan_build_helpers` (a pass-through), `ux_phase1_support.set_config` (an allowance for callers' explicit tags), `voi_stopping_helpers`, `serve_eligibility_helpers`, `ro1_availability_reads_helpers`, `ro1_interval_factor_helpers` (callers pass the tag) | per file, section 7 |

Renames, one commit: `build_mvp07_vault` to `build_shared_facet_vault`; fixtures `mvp07` (three files) to `facet_vault`; `_mvp07` (`test_causal_repair_mapping_p2`) to `_shared_facet_vault`; `_mvp07_vault` (the two characterization files) to `_head_vault`. The helper's docstrings that said a tag now say "the head by default". Names that still say a tag build at it (`_mvp06`, `_mvp07` in `test_km4_taxonomy`, `_mvp010`).

## 4. Per file: counts by disposition

Emptied (every case now at the head): 81 files. Partly moved (some cases still on a tag, by name): 89. Untouched: 166. The table is every file of the census, largest move first; "pins added" counts the lines that name an old constant or fixture in the file (`version=<CONSTANT>`, `pin_default_tag(...)`, `*_old_tag` fixtures).

| file | cases before | after | disposition | pins added |
|---|---|---|---|---|
| `test_followup_codex_review.py` | 78 | 0 | emptied |  |
| `test_followup_next_matrix.py` | 71 | 1 | partial |  |
| `test_km2b_consumer_rekey.py` | 57 | 0 | emptied |  |
| `test_reader_workbench_rw2a.py` | 58 | 1 | partial | 1 |
| `test_reading_paths.py` | 48 | 2 | partial | 6 |
| `test_ih7_lesson_sources_follow_diagnosis.py` | 44 | 3 | partial |  |
| `test_ih2_lessons_compete.py` | 40 | 3 | partial |  |
| `test_ih2_one_open_offer.py` | 36 | 0 | emptied |  |
| `test_followup_fg1c_r1_exposure_independence.py` | 35 | 0 | emptied |  |
| `test_hypothesis_marks.py` | 34 | 0 | emptied |  |
| `test_ih6_workbench_open_item.py` | 37 | 5 | partial |  |
| `test_teacher_exam_question_guard.py` | 33 | 2 | partial | 1 |
| `test_ih4_preferences_inform_router.py` | 34 | 4 | partial |  |
| `test_teacher_te1_review_fixes.py` | 30 | 0 | emptied |  |
| `test_recurrence_live.py` | 30 | 1 | partial |  |
| `test_facet_identity_actions.py` | 28 | 0 | emptied |  |
| `test_facet_outcome_view.py` | 28 | 0 | emptied |  |
| `test_followup_reserved_only.py` | 29 | 1 | partial |  |
| `test_ih_lesson_candidate_after_cold_miss.py` | 28 | 5 | partial |  |
| `test_durable_promotion_arms.py` | 22 | 0 | emptied |  |
| `test_intent_resolution.py` | 22 | 0 | emptied |  |
| `test_followup_rival_factor.py` | 22 | 1 | partial |  |
| `test_ih2_offer_ceiling_and_unseen.py` | 23 | 2 | partial |  |
| `test_teacher_te2log_episodes.py` | 23 | 2 | partial | 2 |
| `test_curriculum_c1_plan_follows_path.py` | 25 | 5 | partial | 4 |
| `test_facet_span_support.py` | 20 | 0 | emptied |  |
| `test_reader_ca2_codex_review.py` | 20 | 0 | emptied |  |
| `test_sg_slip_vs_gap.py` | 24 | 4 | partial |  |
| `test_intent_fix_round6.py` | 44 | 25 | partial | 1 |
| `test_followup_journey.py` | 19 | 1 | partial |  |
| `test_reader_rw5d_p4b_teacher_visuals.py` | 21 | 3 | partial | 3 |
| `test_teacher_te1_lesson.py` | 17 | 1 | partial |  |
| `test_followup_router.py` | 15 | 0 | emptied |  |
| `test_intent_exclusion.py` | 15 | 0 | emptied |  |
| `test_causal_factor_deferral.py` | 14 | 0 | emptied |  |
| `test_cold_retry_reschedule.py` | 18 | 4 | partial |  |
| `test_ih3_learner_preferences.py` | 16 | 2 | partial |  |
| `test_intent_codex_review.py` | 25 | 11 | partial | 9 |
| `test_ro1_availability_reads.py` | 21 | 7 | partial |  |
| `test_teacher_te2_review_fixes.py` | 14 | 0 | emptied |  |
| `test_followup_fg1c_codex_review.py` | 13 | 0 | emptied |  |
| `test_te3a_lesson_opportunity.py` | 16 | 3 | partial |  |
| `test_forecast_receipts.py` | 17 | 5 | partial | 2 |
| `test_ih_numeric_seed.py` | 12 | 0 | emptied |  |
| `test_mobile_v3_codex_review.py` | 12 | 0 | emptied |  |
| `test_rofu_switch_key.py` | 12 | 0 | emptied |  |
| `test_teacher_te2_probes.py` | 12 | 0 | emptied |  |
| `test_curriculum_c1_fix_round2.py` | 13 | 2 | partial | 2 |
| `test_intent_fix_round4.py` | 30 | 19 | partial | 2 |
| `test_lp_claim_fixes_review.py` | 15 | 4 | partial |  |
| `test_facet_authority_rereview.py` | 10 | 0 | emptied |  |
| `test_facet_authority_review.py` | 10 | 0 | emptied |  |
| `test_followup_generate_e2e.py` | 11 | 1 | partial | 2 |
| `test_intent_checks.py` | 10 | 0 | emptied |  |
| `test_intent_fix_round5.py` | 10 | 0 | emptied |  |
| `test_plan_follows_path.py` | 15 | 5 | partial | 9 |
| `test_reader_ca2_astra_handoff.py` | 10 | 0 | emptied |  |
| `test_teacher_te1_weight.py` | 10 | 0 | emptied |  |
| `test_attempt_chain_records.py` | 10 | 1 | partial |  |
| `test_curriculum_c1_fix_round3.py` | 9 | 0 | emptied |  |
| `test_followup_workflow.py` | 10 | 1 | partial |  |
| `test_ih3_phone_host.py` | 9 | 0 | emptied |  |
| `test_intent_fix_round7.py` | 9 | 0 | emptied |  |
| `test_intent_orchestrator_rulings.py` | 9 | 0 | emptied |  |
| `test_required_method_round3_review.py` | 9 | 0 | emptied |  |
| `test_ro0_codex_review.py` | 14 | 5 | partial | 1 |
| `test_teacher_te2_lessons.py` | 13 | 4 | partial |  |
| `test_curriculum_c1_fix_round5.py` | 8 | 0 | emptied |  |
| `test_facet_reword_confirm_review.py` | 8 | 0 | emptied |  |
| `test_followup_single_use.py` | 8 | 0 | emptied |  |
| `test_graph_editor_reads.py` | 8 | 0 | emptied |  |
| `test_intent_plan.py` | 11 | 3 | partial |  |
| `test_km2_write_path.py` | 9 | 1 | partial |  |
| `test_mobile_v3_probes.py` | 9 | 1 | partial |  |
| `test_rw7b_codex_review_fixes.py` | 10 | 2 | partial | 2 |
| `test_success_head_cli.py` | 8 | 0 | emptied |  |
| `test_te3b_offers.py` | 9 | 1 | partial | 1 |
| `test_curriculum_c1_codex_review_fixes.py` | 9 | 2 | partial | 2 |
| `test_curriculum_c1_fix_round4.py` | 7 | 0 | emptied |  |
| `test_followup_live_shape.py` | 8 | 1 | partial |  |
| `test_followups_batch5_lesson.py` | 7 | 0 | emptied |  |
| `test_followups_batch5_recap_dependencies.py` | 7 | 0 | emptied |  |
| `test_lp_claim_fixes_rereview.py` | 8 | 1 | partial |  |
| `test_rospeed_join.py` | 7 | 0 | emptied |  |
| `test_router_card_reading_gaps.py` | 7 | 0 | emptied |  |
| `test_sidecar_adjudication.py` | 7 | 0 | emptied |  |
| `test_anti_double_count.py` | 6 | 0 | emptied |  |
| `test_curriculum_c1_round5_followups.py` | 6 | 0 | emptied |  |
| `test_decider_landing.py` | 7 | 1 | partial |  |
| `test_followups_batch5_recap_protection.py` | 7 | 1 | partial | 1 |
| `test_intent_rpc.py` | 6 | 0 | emptied |  |
| `test_mobile_v2_followup.py` | 6 | 0 | emptied |  |
| `test_ro5_checks.py` | 6 | 0 | emptied |  |
| `test_router_card.py` | 9 | 3 | partial | 3 |
| `test_teacher_te2log_activity.py` | 6 | 0 | emptied |  |
| `test_causal_repair_mapping_p2.py` | 5 | 0 | emptied |  |
| `test_intent_codex_rereview.py` | 9 | 4 | partial |  |
| `test_probe_robust_cutover.py` | 7 | 2 | partial |  |
| `test_ro1_availability.py` | 7 | 2 | partial |  |
| `test_ro5_codex_rereview.py` | 5 | 0 | emptied |  |
| `test_te3b_codex_review.py` | 9 | 4 | partial | 3 |
| `test_facet_evidence_timeline.py` | 4 | 0 | emptied |  |
| `test_forced_withdrawal_records.py` | 10 | 6 | partial |  |
| `test_intent_goal_deadline.py` | 4 | 0 | emptied |  |
| `test_intent_recall_targets.py` | 4 | 0 | emptied |  |
| `test_mcp_c1a_landing.py` | 5 | 1 | partial |  |
| `test_mobile_v2_checks.py` | 4 | 0 | emptied |  |
| `test_narrative_rollback_overlap.py` | 4 | 0 | emptied |  |
| `test_placement_unevidenced_return.py` | 20 | 16 | partial |  |
| `test_reader_ca2_astra_handoff_recovery.py` | 4 | 0 | emptied |  |
| `test_reader_question_note_id_placement.py` | 4 | 0 | emptied |  |
| `test_reader_rw6b_p2_landing.py` | 4 | 0 | emptied |  |
| `test_ro4_codex_review.py` | 6 | 2 | partial | 2 |
| `test_rofu_carried.py` | 5 | 1 | partial |  |
| `test_teacher_te1b_suggestions.py` | 20 | 16 | partial | 15 |
| `test_ux_phase3_today.py` | 4 | 0 | emptied |  |
| `test_voi_forecasts.py` | 4 | 0 | emptied |  |
| `test_causal_attribution_p0.py` | 3 | 0 | emptied |  |
| `test_dl2_rw4b_keyed_pick_check.py` | 3 | 0 | emptied |  |
| `test_facet_authority.py` | 3 | 0 | emptied |  |
| `test_facet_identity_composition.py` | 3 | 0 | emptied |  |
| `test_figures_prefetch_review_fixes.py` | 3 | 0 | emptied |  |
| `test_km2_sim_gates.py` | 3 | 0 | emptied |  |
| `test_probe_targeting.py` | 4 | 1 | partial |  |
| `test_reader_ca2_codex_rereview.py` | 8 | 5 | partial |  |
| `test_refusal_records.py` | 6 | 3 | partial |  |
| `test_ro1_interval_factor.py` | 7 | 4 | partial |  |
| `test_ro5_calibration.py` | 4 | 1 | partial |  |
| `test_ro5_codex_review.py` | 3 | 0 | emptied |  |
| `test_ro5_picks.py` | 4 | 1 | partial |  |
| `test_rofu_learning.py` | 5 | 2 | partial |  |
| `test_rospeed2_connections.py` | 8 | 5 | partial | 2 |
| `test_teacher_te2log_node_held.py` | 5 | 2 | partial | 2 |
| `test_teacher_te2log_report.py` | 4 | 1 | partial | 1 |
| `test_curriculum_c1_landing.py` | 2 | 0 | emptied |  |
| `test_exam_protection_landing.py` | 2 | 0 | emptied |  |
| `test_km3_projections.py` | 6 | 4 | partial | 9 |
| `test_pfc_unassessed_readers.py` | 5 | 3 | partial |  |
| `test_reader_rw3a_landing.py` | 5 | 3 | partial | 1 |
| `test_remaining_decision_records.py` | 4 | 2 | partial |  |
| `test_ro1_projection.py` | 17 | 15 | partial |  |
| `test_ro1_self_report.py` | 3 | 1 | partial |  |
| `test_ro5_stop_coin.py` | 3 | 1 | partial | 1 |
| `test_router_reader_activity.py` | 18 | 16 | partial | 1 |
| `test_rw7b_fix_round2.py` | 5 | 3 | partial | 2 |
| `test_teacher_te2_landing_r1.py` | 2 | 0 | emptied |  |
| `test_ux_phase4_feedback.py` | 28 | 26 | partial |  |
| `test_apply_recovery.py` | 1 | 0 | emptied |  |
| `test_causal_orchestrator.py` | 1 | 0 | emptied |  |
| `test_field_workbench_signals.py` | 15 | 14 | partial |  |
| `test_followups_batch6_router_report.py` | 2 | 1 | partial | 1 |
| `test_followups_nov2_figure_provenance.py` | 1 | 0 | emptied |  |
| `test_forecast_receipts_landing.py` | 1 | 0 | emptied |  |
| `test_held_grade_composition.py` | 1 | 0 | emptied |  |
| `test_measurement_corrections.py` | 2 | 1 | partial |  |
| `test_method_explicit_landing.py` | 2 | 1 | partial | 1 |
| `test_mobile_v2_rereview_fixes.py` | 1 | 0 | emptied |  |
| `test_mobile_v2_review_fixes.py` | 1 | 0 | emptied |  |
| `test_pfc_unverified_unassessed.py` | 190 | 189 | partial |  |
| `test_reader_ca1_as_printed.py` | 1 | 0 | emptied |  |
| `test_reader_ca2_fix_orchestrator.py` | 9 | 8 | partial |  |
| `test_reader_ca5a_find_section.py` | 1 | 0 | emptied |  |
| `test_residual_diagnostics.py` | 1 | 0 | emptied |  |
| `test_sidecar_knowledge_model.py` | 4 | 3 | partial | 4 |
| `test_te3b_population.py` | 2 | 1 | partial |  |
| `test_teacher_te1b_landing_r2.py` | 9 | 8 | partial | 8 |
| `test_teacher_te1b_rereview_fixes.py` | 5 | 4 | partial | 4 |
| `test_teacher_te1b_review_fixes.py` | 7 | 6 | partial | 6 |
| `test_why_cases.py` | 2 | 1 | partial |  |
| `test_why_reader.py` | 5 | 4 | partial |  |
| `test_active_errors_overlay.py` | 1 | 1 | untouched |  |
| `test_ad23_fix_r5.py` | 1 | 1 | untouched |  |
| `test_ad2_serving.py` | 2 | 2 | untouched |  |
| `test_ad3_relatedness.py` | 1 | 1 | untouched |  |
| `test_ai_compare.py` | 1 | 1 | untouched |  |
| `test_arcb_close_fixes.py` | 5 | 5 | untouched |  |
| `test_assessment_contracts.py` | 5 | 5 | untouched |  |
| `test_batch3_landing.py` | 3 | 3 | untouched |  |
| `test_canonical_projection_rollout.py` | 3 | 3 | untouched |  |
| `test_chat_total_transport_deadline.py` | 1 | 1 | untouched |  |
| `test_curriculum_c0b_landing.py` | 2 | 2 | untouched |  |
| `test_daily_plan_kill_switch.py` | 1 | 1 | untouched |  |
| `test_diagnosis_async_router.py` | 2 | 2 | untouched |  |
| `test_diagnosis_card.py` | 1 | 1 | untouched |  |
| `test_diagnosis_pipeline.py` | 2 | 2 | untouched |  |
| `test_diagnosis_replay.py` | 2 | 2 | untouched |  |
| `test_diagnostic_pack.py` | 10 | 10 | untouched |  |
| `test_doctor.py` | 1 | 1 | untouched |  |
| `test_embedding_store.py` | 1 | 1 | untouched |  |
| `test_evsi_router_composition.py` | 5 | 5 | untouched |  |
| `test_evsi_staged_binding.py` | 2 | 2 | untouched |  |
| `test_exam_protection.py` | 1 | 1 | untouched |  |
| `test_exam_protection_review.py` | 1 | 1 | untouched |  |
| `test_exam_session.py` | 3 | 3 | untouched |  |
| `test_failure_triage.py` | 22 | 22 | untouched |  |
| `test_failure_triage_causal_gate.py` | 1 | 1 | untouched |  |
| `test_family_memory_projection.py` | 1 | 1 | untouched |  |
| `test_figure_wait_estimate.py` | 1 | 1 | untouched |  |
| `test_followup_fg1d_panel_read.py` | 8 | 8 | untouched |  |
| `test_followup_fg1d_probe_shadow.py` | 12 | 12 | untouched |  |
| `test_followups_batch6_review_fixes.py` | 2 | 2 | untouched | 2 |
| `test_followups_batch6_te1b_card.py` | 3 | 3 | untouched | 3 |
| `test_followups_nov2_help_fold.py` | 8 | 8 | untouched |  |
| `test_generated_item_gate.py` | 3 | 3 | untouched |  |
| `test_golden_path_fixture.py` | 4 | 4 | untouched |  |
| `test_hot_path_eligibility_cutover.py` | 3 | 3 | untouched |  |
| `test_instrument_servability_journeys.py` | 1 | 1 | untouched |  |
| `test_km1_doctor.py` | 5 | 5 | untouched |  |
| `test_km4_taxonomy.py` | 9 | 9 | untouched |  |
| `test_learner_blindness_relax.py` | 2 | 2 | untouched |  |
| `test_learner_text_gaps_rereview.py` | 18 | 18 | untouched |  |
| `test_lp_claim_fixes.py` | 17 | 17 | untouched |  |
| `test_map_untested.py` | 3 | 3 | untouched | 2 |
| `test_misconception_registry.py` | 7 | 7 | untouched |  |
| `test_mvp017_route_check_replay.py` | 2 | 2 | untouched |  |
| `test_observation_ledger_bulk.py` | 4 | 4 | untouched |  |
| `test_p0_projection_cutover.py` | 6 | 6 | untouched |  |
| `test_p2_acceptance.py` | 3 | 3 | untouched |  |
| `test_p2_leakage_suite.py` | 2 | 2 | untouched |  |
| `test_placement_diagnosis_decides.py` | 1 | 1 | untouched |  |
| `test_placement_opening_probes.py` | 17 | 17 | untouched |  |
| `test_placement_report.py` | 5 | 5 | untouched |  |
| `test_placement_sidecar.py` | 8 | 8 | untouched |  |
| `test_placement_signals.py` | 5 | 5 | untouched |  |
| `test_plan_determinism.py` | 12 | 12 | untouched |  |
| `test_plan_determinism_landing.py` | 19 | 19 | untouched |  |
| `test_pr4_superseded_claims_landing.py` | 1 | 1 | untouched |  |
| `test_practice_information.py` | 3 | 3 | untouched |  |
| `test_probe_episodes.py` | 2 | 2 | untouched |  |
| `test_projection_evidence_polarity.py` | 3 | 3 | untouched |  |
| `test_provenance.py` | 17 | 17 | untouched |  |
| `test_quick_add.py` | 4 | 4 | untouched |  |
| `test_quick_check.py` | 19 | 19 | untouched |  |
| `test_reader_ca2_one_ask.py` | 19 | 19 | untouched |  |
| `test_reader_dialogue.py` | 1 | 1 | untouched |  |
| `test_reader_digest_narrative.py` | 30 | 30 | untouched |  |
| `test_reader_followups.py` | 36 | 36 | untouched |  |
| `test_reader_followups_rereview.py` | 6 | 6 | untouched |  |
| `test_reader_followups_review.py` | 18 | 18 | untouched |  |
| `test_reader_followups_round3.py` | 6 | 6 | untouched |  |
| `test_reader_followups_round4.py` | 2 | 2 | untouched |  |
| `test_reader_followups_round5.py` | 3 | 3 | untouched |  |
| `test_reader_followups_round6.py` | 3 | 3 | untouched |  |
| `test_reader_followups_round7.py` | 3 | 3 | untouched |  |
| `test_reader_followups_round8.py` | 4 | 4 | untouched |  |
| `test_reader_guidance.py` | 9 | 9 | untouched |  |
| `test_reader_recap_review.py` | 4 | 4 | untouched |  |
| `test_reader_recap_review_r2.py` | 3 | 3 | untouched |  |
| `test_reader_recap_review_r3.py` | 5 | 5 | untouched |  |
| `test_reader_rw1b_review.py` | 2 | 2 | untouched |  |
| `test_reader_rw4b_admission_idempotency.py` | 5 | 5 | untouched |  |
| `test_reader_rw4b_fix6.py` | 4 | 4 | untouched |  |
| `test_reader_rw6b_landing.py` | 5 | 5 | untouched |  |
| `test_reading_step_switch.py` | 1 | 1 | untouched |  |
| `test_rebuild_equivalence.py` | 4 | 4 | untouched |  |
| `test_rebuild_equivalence_review.py` | 3 | 3 | untouched |  |
| `test_rebuild_orchestrator.py` | 6 | 6 | untouched |  |
| `test_recall_calibration.py` | 2 | 2 | untouched |  |
| `test_recall_coverage_interventions.py` | 1 | 1 | untouched |  |
| `test_receipt_derivation.py` | 2 | 2 | untouched |  |
| `test_receipt_exactness.py` | 4 | 4 | untouched |  |
| `test_recurrence_commands.py` | 23 | 23 | untouched |  |
| `test_recurrence_deferral.py` | 3 | 3 | untouched |  |
| `test_recurrence_groups.py` | 11 | 11 | untouched |  |
| `test_reference_gate_imports.py` | 17 | 17 | untouched |  |
| `test_ro0_codex_verify.py` | 16 | 16 | untouched |  |
| `test_ro0_gate.py` | 5 | 5 | untouched |  |
| `test_ro0_report.py` | 3 | 3 | untouched |  |
| `test_ro0_row10_cold_timing.py` | 3 | 3 | untouched |  |
| `test_ro0_row12_trajectory.py` | 3 | 3 | untouched |  |
| `test_ro0_row3_ask_availability.py` | 7 | 7 | untouched |  |
| `test_ro0_rows7_8_sessions.py` | 4 | 4 | untouched |  |
| `test_ro0_rows9_13_decision_state.py` | 13 | 13 | untouched |  |
| `test_ro2_ad_document_ir.py` | 6 | 6 | untouched |  |
| `test_ro2_ad_raw_document_reads.py` | 2 | 2 | untouched |  |
| `test_ro2_history_protection.py` | 2 | 2 | untouched |  |
| `test_ro4_goals.py` | 4 | 4 | untouched |  |
| `test_ro4_objective_serving.py` | 6 | 6 | untouched |  |
| `test_ro4_trace_report.py` | 1 | 1 | untouched |  |
| `test_ro5_landing.py` | 10 | 10 | untouched |  |
| `test_ro6_codex_rereview.py` | 2 | 2 | untouched |  |
| `test_ro6_codex_review.py` | 1 | 1 | untouched |  |
| `test_ro6_landing.py` | 4 | 4 | untouched |  |
| `test_ro6_serving.py` | 5 | 5 | untouched |  |
| `test_ro6_tail_data.py` | 6 | 6 | untouched |  |
| `test_rofu_ad_link.py` | 3 | 3 | untouched |  |
| `test_rofu_generator_switches.py` | 12 | 12 | untouched |  |
| `test_rofu_monotone.py` | 3 | 3 | untouched |  |
| `test_rofu_review_draw.py` | 3 | 3 | untouched |  |
| `test_rofu_speed.py` | 3 | 3 | untouched |  |
| `test_roles_switch_off.py` | 1 | 1 | untouched |  |
| `test_rospeed_ad_link.py` | 1 | 1 | untouched |  |
| `test_router_failure_records.py` | 8 | 8 | untouched |  |
| `test_router_g1_feasibility.py` | 8 | 8 | untouched |  |
| `test_router_g3_propensity.py` | 2 | 2 | untouched |  |
| `test_router_g4_restraint.py` | 12 | 12 | untouched |  |
| `test_router_g7_fallback.py` | 3 | 3 | untouched |  |
| `test_router_presentations.py` | 6 | 6 | untouched |  |
| `test_router_probe_ties.py` | 9 | 9 | untouched |  |
| `test_router_r1_composition.py` | 8 | 8 | untouched |  |
| `test_router_r2a_landing.py` | 4 | 4 | untouched | 2 |
| `test_router_r2a_serving.py` | 10 | 10 | untouched |  |
| `test_router_r2b_agreement.py` | 3 | 3 | untouched |  |
| `test_router_r2b_requests.py` | 1 | 1 | untouched |  |
| `test_router_r2b_serving.py` | 20 | 20 | untouched |  |
| `test_router_r2bc_landing.py` | 6 | 6 | untouched |  |
| `test_router_r2c_retrieval.py` | 8 | 8 | untouched |  |
| `test_router_r2c_teach_back.py` | 6 | 6 | untouched |  |
| `test_rw5c_switch_off.py` | 1 | 1 | untouched |  |
| `test_serve_eligibility.py` | 17 | 17 | untouched |  |
| `test_serve_eligibility_review.py` | 22 | 22 | untouched |  |
| `test_shadow_rebuild.py` | 4 | 4 | untouched |  |
| `test_sidecar_contract.py` | 1 | 1 | untouched | 1 |
| `test_sim_goals.py` | 3 | 3 | untouched |  |
| `test_sim_probe_validation.py` | 1 | 1 | untouched |  |
| `test_sim_teach_back.py` | 2 | 2 | untouched |  |
| `test_simulation.py` | 4 | 4 | untouched |  |
| `test_source_first_needs.py` | 17 | 17 | untouched |  |
| `test_source_set_synthesis.py` | 1 | 1 | untouched |  |
| `test_stuck_prompt_replay.py` | 3 | 3 | untouched |  |
| `test_subject_registry.py` | 4 | 4 | untouched |  |
| `test_te3b_clock.py` | 1 | 1 | untouched |  |
| `test_te3b_features.py` | 1 | 1 | untouched |  |
| `test_teach_back.py` | 3 | 3 | untouched |  |
| `test_teacher_te0_review_fixes.py` | 3 | 3 | untouched | 4 |
| `test_teacher_te2_sidecar.py` | 2 | 2 | untouched |  |
| `test_today_headline.py` | 1 | 1 | untouched | 1 |
| `test_unresolved_cause_gate.py` | 6 | 6 | untouched |  |
| `test_ux_phase1_round2_rereview.py` | 2 | 2 | untouched |  |
| `test_ux_phase2_error_type_proposals.py` | 1 | 1 | untouched |  |
| `test_ux_phase4_landing.py` | 5 | 5 | untouched |  |
| `test_value_candidates.py` | 3 | 3 | untouched |  |
| `test_version_floor.py` | 1 | 1 | untouched |  |
| `test_voi_merge_composition.py` | 8 | 8 | untouched |  |
| `test_voi_stopping.py` | 34 | 34 | untouched |  |
| `test_voi_v2.py` | 22 | 22 | untouched |  |

## 5. Subject check and vacuity check

**Subject (rule 4).** The experiment's rule was applied per test, not per file: a test moved only if (a) it passes at the head and (b) its body names no tag of its own. Names and bodies were scanned for replay, upgrade, historical, legacy, "written at", "below the tag", "at the tag only", predecessor, successor, older, rebuild, migrat and before/after the (97 of the 561 tests moved in the first 121 files). Of those 97, 3 name a tag in their body, and they are the `switch_off`, `router_off` and `lessons_off` arms of `test_off_or_below_the_tag_nothing_is_drawn_or_written`: the `below_tag` arm keeps `PREDECESSOR_TAG` and the three arms that moved test the switch at the head. The other 94 mention the words in the sense of a feature (a legacy question, a rebuild of the projection, "after the deadline"), not of a version; the subject of every moved test is the behaviour its name states, which exists at the head. A transition test (two tags in one body, or a tag set and then another written) was never edited by this pass: the helpers' defaults moved, and an explicit tag stays. One-line subject notes were written per file in the working notes, not per test (3,331 cases), because the moved tests inherit their tag from a helper default; no test of this kind had a version in its body to depend on.

**Vacuity (rule 5).** For each of the 69 files whose tests moved in the first helper rounds (561 tests; the 121 files of the affected-test selection, 69 of which lost cases), the scratch tool `mut.py` wrote a copy with the first `assert` of the first moved test negated and ran it, then the same with the last `assert`: 69 files, 138 mutations, all failed with `AssertionError` at the negated line (78 failing parametrized cases each time), and none passed. Negating the first assertion shows the test reaches an assertion; the last shows it reaches its end. Four of the first assertions compare an empty value (`{}`, `[]`), and the last-assertion run covers them; the check does not prove the assertions are strong, only that the moved tests execute and assert. The 25 local-`TAG` files and the last helper round (about 1,230 more cases) were run green at the head but not mutated: not checked.

## 6. Every assertion changed, and why

**None.** No expected value, no comparison and no `assert` line was changed in meaning. Where `TAG` stood for the old value in an assertion (`row["algorithm_version"] == TAG`, `SUCCESSOR_CHAIN.index(TAG)`, `DELIVERABLE_PLAN_VERSIONS == frozenset({TAG, ...})`) it now names the constant with the old value (`LESSON_SUGGESTIONS_ALGORITHM_VERSION`, `DELIVERABLE_PLAN_ALGORITHM_VERSION`, ...): the same string. Two non-assertion changes beyond tag names:

1. `test_followup_router::test_a_wait_keeps_its_room_and_next_continues_the_block` builds with `RANDOMIZED_CHECKS_OFF` (D2b part 2a's fragment) and its comment says why: at the head the randomized check's block is the plan's first and holds one item, which the test's `len(first.current_block().items) > 1` excludes. A pin of a draw the subject does not own.
2. `test_followup_generate_e2e::test_a_mint_under_fg1_is_model_written_single_use_and_needs_no_review` builds its acceptance vault at mvp-0.7 and stamps mvp-0.45, as it always has (`built_at=KM2_OLD_TAG`): built at the head and stamped mvp-0.45 the entry job already exists and `enqueue_entry` returns None. The hybrid is the old test's setup; it waits on D5 (the canonical-projection gate).

## 7. The old-path list, and what is not done

Grouped by the package whose gate the file exercises (`docs/specs/refactor_strategy_v3.md` section 2.6: D5 substrate, rebuild, doctor; D6 the rest and the sets; D7 kill switches), **by file name and tag only**: no test was read to its gate, except where a gate is named below. The tag column is the tag(s) the census saw. A file listed here has cases left on a tag, whether or not it also has moved ones. The groups are the starting point for each step's own step 0.

Gates named: the tag-writing sets the tests I pinned read are `algorithm_versions.py` `CANONICAL_STATE_VERSIONS` (line 1038; read at `attempts/attempts.py:105`, `:3646`: D4's file, but the facet-capability projection the km3 pins read is substrate, D5), `TEACHER_VERSIONS` (1183; `daily_plan/lesson_suggestion.py:117`), `LESSON_SUGGESTIONS_VERSIONS` (1193; `lesson_suggestion.py:111`), `READING_PATH_PLAN_VERSIONS` (1138; `daily_plan/engine.py:211`), `DELIVERABLE_PLAN_VERSIONS` (1180; `engine.py:234`), `INTENT_VERSIONS` (1121; `scheduling/intent/serving.py:126`), `ROUTER_STAGED_FRAME_VERSIONS` (1092; `daily_plan/policy.py:5`), `LESSON_OFFERS_VERSIONS` (1252; `router_objective_switches.py:353`), `DIAGNOSIS_SPLIT_VERSIONS` (1014; `attempts/blind_grading.py:85`), `ELIGIBILITY_DECISION_VERSIONS` (1116; `serve_eligibility.py:989`), `FOLLOWUP_SERVE_VERSIONS` (1204; `followup_serve/gates.py:3`). The pins this pass added, grouped:

- **D5**: `BLUEPRINT_OLD_TAG`/`KM2_OLD_TAG` pins (km2, km3, map-untested, sidecar knowledge model and contract, today headline, measurement corrections, the acceptance-vault hybrid of `test_followup_generate_e2e`).
- **D6**: the teacher (`pin_default_tag`, `LESSON_SUGGESTIONS`, `LESSON_OFFERS`, TE0 cards), intent (`INTENT_ALGORITHM_VERSION`), reading path and deliverable plan, router card (`ROUTER_STAGED_FRAME`), `DIAGNOSIS_SPLIT`, `ELIGIBILITY_DECISION`, claim fixes.
- **D7**: the predecessor arms (`test_ro1_*` off arms, `test_the_successor_is_one_constant_*`, `test_off_is_the_predecessor_*`, the switch-off arm of `test_followup_journey`), which stay with their switch.

### D5

| file | cases left on a tag | tags (top 3, cases) |
|---|---|---|
| `test_assessment_contracts.py` | 5 | mvp-0.7(4),mvp-0.6(1) |
| `test_canonical_projection_rollout.py` | 3 | mvp-0.7(3) |
| `test_diagnostic_pack.py` | 10 | None(10) |
| `test_doctor.py` | 1 | mvp-0.6(1) |
| `test_embedding_store.py` | 1 | mvp-0.6(1) |
| `test_failure_triage.py` | 22 | None(22) |
| `test_failure_triage_causal_gate.py` | 1 | None(1) |
| `test_family_memory_projection.py` | 1 | mvp-0.6(1) |
| `test_followup_fg1d_probe_shadow.py` | 12 | mvp-0.45(6),mvp-0.46(6) |
| `test_forecast_receipts.py` | 5 | mvp-0.20(2),mvp-0.10(2),mvp-0.25(1) |
| `test_generated_item_gate.py` | 3 | mvp-0.7(2),mvp-0.6(1) |
| `test_golden_path_fixture.py` | 4 | None(5) |
| `test_km1_doctor.py` | 5 | mvp-0.7(3),mvp-0.6(2) |
| `test_km2_write_path.py` | 1 | mvp-0.7(1) |
| `test_km3_projections.py` | 4 | mvp-0.7(4) |
| `test_km4_taxonomy.py` | 9 | mvp-0.7(7),mvp-0.6(3) |
| `test_map_untested.py` | 3 | mvp-0.7(3) |
| `test_measurement_corrections.py` | 1 | mvp-0.7(1) |
| `test_misconception_registry.py` | 7 | mvp-0.6(7) |
| `test_observation_ledger_bulk.py` | 4 | mvp-0.7(4) |
| `test_p0_projection_cutover.py` | 6 | mvp-0.8(6) |
| `test_p2_acceptance.py` | 3 | None(3) |
| `test_p2_leakage_suite.py` | 2 | None(2) |
| `test_practice_information.py` | 3 | None(3) |
| `test_projection_evidence_polarity.py` | 3 | mvp-0.7(3) |
| `test_provenance.py` | 17 | mvp-0.6(17) |
| `test_quick_add.py` | 4 | mvp-0.7(4) |
| `test_rebuild_equivalence.py` | 4 | mvp-0.33(1),mvp-0.34(1),mvp-0.35(1) |
| `test_rebuild_equivalence_review.py` | 3 | mvp-0.33(3) |
| `test_rebuild_orchestrator.py` | 6 | mvp-0.6(7) |
| `test_recall_calibration.py` | 2 | None(2) |
| `test_receipt_derivation.py` | 2 | mvp-0.7(2) |
| `test_receipt_exactness.py` | 4 | mvp-0.7(2),mvp-0.8(2) |
| `test_reference_gate_imports.py` | 17 | mvp-0.18(15),mvp-0.17(3) |
| `test_ro1_projection.py` | 15 | mvp-0.45(20),mvp-0.46(2) |
| `test_shadow_rebuild.py` | 4 | mvp-0.6(4) |
| `test_sidecar_contract.py` | 1 | mvp-0.7(1) |
| `test_sidecar_knowledge_model.py` | 3 | mvp-0.7(3) |
| `test_sim_goals.py` | 3 | mvp-0.7(3) |
| `test_sim_probe_validation.py` | 1 | mvp-0.6(1) |
| `test_sim_teach_back.py` | 2 | mvp-0.7(2) |
| `test_simulation.py` | 4 | mvp-0.7(4) |
| `test_source_first_needs.py` | 17 | mvp-0.19(17),mvp-0.18(1) |
| `test_subject_registry.py` | 4 | mvp-0.7(4) |
| `test_today_headline.py` | 1 | mvp-0.7(1) |

### D6

| file | cases left on a tag | tags (top 3, cases) |
|---|---|---|
| `test_active_errors_overlay.py` | 1 | mvp-0.9(1) |
| `test_ad23_fix_r5.py` | 1 | mvp-0.29(1) |
| `test_ad2_serving.py` | 2 | mvp-0.29(2) |
| `test_ad3_relatedness.py` | 1 | mvp-0.29(1) |
| `test_ai_compare.py` | 1 | mvp-0.25(1) |
| `test_arcb_close_fixes.py` | 5 | mvp-0.24(6) |
| `test_attempt_chain_records.py` | 1 | mvp-0.21(1) |
| `test_batch3_landing.py` | 3 | mvp-0.35(4) |
| `test_chat_total_transport_deadline.py` | 1 | mvp-0.39(1) |
| `test_cold_retry_reschedule.py` | 4 | mvp-0.37(5) |
| `test_curriculum_c0b_landing.py` | 2 | mvp-0.38(3) |
| `test_curriculum_c1_codex_review_fixes.py` | 2 | mvp-0.40(2) |
| `test_curriculum_c1_fix_round2.py` | 2 | mvp-0.40(2) |
| `test_curriculum_c1_plan_follows_path.py` | 5 | mvp-0.40(8),mvp-0.39(5) |
| `test_decider_landing.py` | 1 | mvp-0.21(1) |
| `test_diagnosis_async_router.py` | 2 | mvp-0.9(1),mvp-0.10(1) |
| `test_diagnosis_card.py` | 1 | mvp-0.9(1) |
| `test_diagnosis_pipeline.py` | 2 | mvp-0.9(2) |
| `test_diagnosis_replay.py` | 2 | mvp-0.6(2) |
| `test_evsi_router_composition.py` | 5 | mvp-0.15(5) |
| `test_evsi_staged_binding.py` | 2 | mvp-0.23(2) |
| `test_exam_protection.py` | 1 | mvp-0.7(1) |
| `test_exam_protection_review.py` | 1 | mvp-0.7(1) |
| `test_exam_session.py` | 3 | mvp-0.8(1),mvp-0.10(1),mvp-0.9(1) |
| `test_field_workbench_signals.py` | 14 | mvp-0.31(17),mvp-0.30(4) |
| `test_figure_wait_estimate.py` | 1 | mvp-0.57(1) |
| `test_followup_fg1d_panel_read.py` | 8 | mvp-0.45(4),mvp-0.46(4) |
| `test_followup_generate_e2e.py` | 1 | mvp-0.7(1),mvp-0.45(1) |
| `test_followup_journey.py` | 1 | mvp-0.44(2) |
| `test_followup_live_shape.py` | 1 | mvp-0.44(1) |
| `test_followup_next_matrix.py` | 1 | mvp-0.45(1) |
| `test_followup_reserved_only.py` | 1 | mvp-0.44(1) |
| `test_followup_rival_factor.py` | 1 | mvp-0.44(1) |
| `test_followup_workflow.py` | 1 | mvp-0.44(1) |
| `test_followups_batch5_recap_protection.py` | 1 | mvp-0.41(1) |
| `test_followups_batch6_review_fixes.py` | 2 | mvp-0.43(2) |
| `test_followups_batch6_router_report.py` | 1 | mvp-0.43(1) |
| `test_followups_batch6_te1b_card.py` | 3 | mvp-0.43(3) |
| `test_followups_nov2_help_fold.py` | 8 | mvp-0.42(8) |
| `test_forced_withdrawal_records.py` | 6 | mvp-0.24(5),mvp-0.54(1) |
| `test_hot_path_eligibility_cutover.py` | 3 | mvp-0.8(3),mvp-0.6(2) |
| `test_ih2_lessons_compete.py` | 3 | mvp-0.54(3) |
| `test_ih3_learner_preferences.py` | 2 | mvp-0.54(2) |
| `test_ih4_preferences_inform_router.py` | 4 | mvp-0.54(4) |
| `test_ih6_workbench_open_item.py` | 5 | mvp-0.54(6) |
| `test_ih7_lesson_sources_follow_diagnosis.py` | 3 | mvp-0.54(3) |
| `test_ih_lesson_candidate_after_cold_miss.py` | 5 | mvp-0.54(5) |
| `test_instrument_servability_journeys.py` | 1 | mvp-0.7(1) |
| `test_intent_codex_rereview.py` | 4 | mvp-0.27(5),mvp-0.14(1),mvp-0.26(1) |
| `test_intent_codex_review.py` | 11 | mvp-0.29(10),mvp-0.20(1) |
| `test_intent_fix_round4.py` | 19 | mvp-0.29(19) |
| `test_intent_fix_round6.py` | 25 | mvp-0.29(25) |
| `test_intent_plan.py` | 3 | mvp-0.29(3) |
| `test_learner_blindness_relax.py` | 2 | mvp-0.39(3) |
| `test_learner_text_gaps_rereview.py` | 18 | mvp-0.16(18) |
| `test_lp_claim_fixes.py` | 17 | mvp-0.33(15),mvp-0.32(6) |
| `test_lp_claim_fixes_rereview.py` | 1 | mvp-0.33(1) |
| `test_lp_claim_fixes_review.py` | 4 | mvp-0.33(2),mvp-0.32(2) |
| `test_mcp_c1a_landing.py` | 1 | mvp-0.24(1) |
| `test_method_explicit_landing.py` | 1 | mvp-0.23(1) |
| `test_mobile_v3_probes.py` | 1 | mvp-0.53(1) |
| `test_mvp017_route_check_replay.py` | 2 | mvp-0.17(2) |
| `test_pfc_unassessed_readers.py` | 3 | mvp-0.7(3) |
| `test_pfc_unverified_unassessed.py` | 189 | mvp-0.38(4),mvp-0.39(4),mvp-0.40(4) |
| `test_placement_diagnosis_decides.py` | 1 | mvp-0.10(1) |
| `test_placement_opening_probes.py` | 17 | mvp-0.10(19),mvp-0.11(17) |
| `test_placement_report.py` | 5 | mvp-0.11(5) |
| `test_placement_sidecar.py` | 8 | mvp-0.11(7),mvp-0.9(1) |
| `test_placement_signals.py` | 5 | mvp-0.11(6) |
| `test_placement_unevidenced_return.py` | 16 | mvp-0.55(23) |
| `test_plan_determinism.py` | 12 | mvp-0.23(23),mvp-0.22(2),mvp-0.14(2) |
| `test_plan_determinism_landing.py` | 19 | mvp-0.24(24) |
| `test_plan_follows_path.py` | 5 | mvp-0.32(12),mvp-0.31(4) |
| `test_pr4_superseded_claims_landing.py` | 1 | mvp-0.36(1) |
| `test_probe_episodes.py` | 2 | mvp-0.6(1),mvp-0.7(1) |
| `test_probe_robust_cutover.py` | 2 | mvp-0.8(1),mvp-0.7(1) |
| `test_probe_targeting.py` | 1 | mvp-0.7(1) |
| `test_quick_check.py` | 19 | mvp-0.11(18),mvp-0.9(1) |
| `test_reader_ca2_codex_rereview.py` | 5 | mvp-0.35(5) |
| `test_reader_ca2_fix_orchestrator.py` | 8 | mvp-0.35(8) |
| `test_reader_ca2_one_ask.py` | 19 | mvp-0.35(21),mvp-0.34(1) |
| `test_reader_dialogue.py` | 1 | None(1) |
| `test_reader_digest_narrative.py` | 30 | mvp-0.39(29),mvp-0.38(1) |
| `test_reader_followups.py` | 36 | mvp-0.39(36) |
| `test_reader_followups_rereview.py` | 6 | mvp-0.39(6) |
| `test_reader_followups_review.py` | 18 | mvp-0.39(18) |
| `test_reader_followups_round3.py` | 6 | mvp-0.39(6) |
| `test_reader_followups_round4.py` | 2 | mvp-0.39(3) |
| `test_reader_followups_round5.py` | 3 | mvp-0.39(4) |
| `test_reader_followups_round6.py` | 3 | mvp-0.39(6) |
| `test_reader_followups_round7.py` | 3 | mvp-0.39(3) |
| `test_reader_followups_round8.py` | 4 | mvp-0.39(4) |
| `test_reader_guidance.py` | 9 | mvp-0.10(7),mvp-0.9(2) |
| `test_reader_recap_review.py` | 4 | mvp-0.7(4) |
| `test_reader_recap_review_r2.py` | 3 | mvp-0.7(4) |
| `test_reader_recap_review_r3.py` | 5 | mvp-0.7(4),mvp-0.25(3) |
| `test_reader_rw1b_review.py` | 2 | mvp-0.16(2) |
| `test_reader_rw3a_landing.py` | 3 | mvp-0.23(3) |
| `test_reader_rw4b_admission_idempotency.py` | 5 | mvp-0.22(5) |
| `test_reader_rw4b_fix6.py` | 4 | mvp-0.22(4) |
| `test_reader_rw5d_p4b_teacher_visuals.py` | 3 | mvp-0.41(6) |
| `test_reader_rw6b_landing.py` | 5 | mvp-0.39(5) |
| `test_reader_workbench_rw2a.py` | 1 | mvp-0.27(1) |
| `test_reading_paths.py` | 2 | mvp-0.29(2) |
| `test_recall_coverage_interventions.py` | 1 | mvp-0.6(1) |
| `test_recurrence_commands.py` | 23 | mvp-0.10(13),mvp-0.12(10) |
| `test_recurrence_deferral.py` | 3 | mvp-0.12(2),mvp-0.10(1) |
| `test_recurrence_groups.py` | 11 | mvp-0.12(11),mvp-0.10(1) |
| `test_recurrence_live.py` | 1 | mvp-0.10(1) |
| `test_refusal_records.py` | 3 | mvp-0.24(4) |
| `test_remaining_decision_records.py` | 2 | mvp-0.24(2) |
| `test_ro0_codex_review.py` | 5 | mvp-0.24(4),mvp-0.43(1) |
| `test_ro0_codex_verify.py` | 16 | mvp-0.44(10),mvp-0.43(6) |
| `test_ro0_gate.py` | 5 | mvp-0.44(4),mvp-0.43(4),mvp-0.24(1) |
| `test_ro0_report.py` | 3 | mvp-0.24(3) |
| `test_ro0_row10_cold_timing.py` | 3 | mvp-0.44(3) |
| `test_ro0_row12_trajectory.py` | 3 | mvp-0.24(3) |
| `test_ro0_row3_ask_availability.py` | 7 | mvp-0.24(8) |
| `test_ro0_rows7_8_sessions.py` | 4 | mvp-0.24(4) |
| `test_ro0_rows9_13_decision_state.py` | 13 | mvp-0.24(13) |
| `test_ro1_availability.py` | 2 | mvp-0.45(2) |
| `test_ro1_availability_reads.py` | 7 | mvp-0.45(7) |
| `test_ro1_interval_factor.py` | 4 | mvp-0.45(4),mvp-0.46(2) |
| `test_ro1_self_report.py` | 1 | mvp-0.45(1) |
| `test_ro2_ad_document_ir.py` | 6 | mvp-0.45(3),mvp-0.46(3) |
| `test_ro2_ad_raw_document_reads.py` | 2 | mvp-0.46(1),mvp-0.47(1) |
| `test_ro2_history_protection.py` | 2 | mvp-0.22(1),mvp-0.46(1) |
| `test_ro4_codex_review.py` | 2 | mvp-0.47(2) |
| `test_ro4_goals.py` | 4 | mvp-0.46(3),mvp-0.47(3) |
| `test_ro4_objective_serving.py` | 6 | mvp-0.47(6),mvp-0.46(1) |
| `test_ro4_trace_report.py` | 1 | mvp-0.46(1) |
| `test_ro5_calibration.py` | 1 | mvp-0.47(1) |
| `test_ro5_landing.py` | 10 | mvp-0.48(7),mvp-0.47(3) |
| `test_ro5_picks.py` | 1 | mvp-0.47(1) |
| `test_ro5_stop_coin.py` | 1 | mvp-0.47(1),mvp-0.48(1) |
| `test_ro6_codex_rereview.py` | 2 | mvp-0.49(2) |
| `test_ro6_codex_review.py` | 1 | mvp-0.49(1) |
| `test_ro6_landing.py` | 4 | mvp-0.49(4) |
| `test_ro6_serving.py` | 5 | mvp-0.49(5),mvp-0.48(1) |
| `test_ro6_tail_data.py` | 6 | mvp-0.49(6) |
| `test_rofu_ad_link.py` | 3 | mvp-0.50(2),mvp-0.49(1) |
| `test_rofu_carried.py` | 1 | mvp-0.49(1) |
| `test_rofu_learning.py` | 2 | mvp-0.49(2) |
| `test_rofu_monotone.py` | 3 | mvp-0.50(2),mvp-0.49(1) |
| `test_rofu_review_draw.py` | 3 | mvp-0.50(2),mvp-0.49(1) |
| `test_rofu_speed.py` | 3 | mvp-0.50(2),mvp-0.49(1) |
| `test_rospeed2_connections.py` | 5 | mvp-0.50(5),mvp-0.49(1),mvp-0.53(1) |
| `test_rospeed_ad_link.py` | 1 | mvp-0.50(2),mvp-0.49(1) |
| `test_router_card.py` | 3 | mvp-0.23(3) |
| `test_router_failure_records.py` | 8 | mvp-0.47(7),mvp-0.24(1) |
| `test_router_g1_feasibility.py` | 8 | mvp-0.23(8),mvp-0.22(1) |
| `test_router_g3_propensity.py` | 2 | mvp-0.24(2) |
| `test_router_g4_restraint.py` | 12 | mvp-0.24(12),mvp-0.23(1) |
| `test_router_g7_fallback.py` | 3 | mvp-0.24(3) |
| `test_router_presentations.py` | 6 | mvp-0.22(6) |
| `test_router_probe_ties.py` | 9 | mvp-0.15(7),mvp-0.14(6) |
| `test_router_r1_composition.py` | 8 | mvp-0.15(8),mvp-0.11(1) |
| `test_router_r2a_landing.py` | 4 | mvp-0.23(4) |
| `test_router_r2a_serving.py` | 10 | mvp-0.23(10),mvp-0.22(1) |
| `test_router_r2b_agreement.py` | 3 | mvp-0.24(3) |
| `test_router_r2b_requests.py` | 1 | mvp-0.24(1) |
| `test_router_r2b_serving.py` | 20 | mvp-0.24(21),mvp-0.23(2) |
| `test_router_r2bc_landing.py` | 6 | mvp-0.24(6) |
| `test_router_r2c_retrieval.py` | 8 | mvp-0.24(9) |
| `test_router_r2c_teach_back.py` | 6 | mvp-0.24(8),mvp-0.23(1) |
| `test_router_reader_activity.py` | 16 | mvp-0.39(15),mvp-0.23(1) |
| `test_rw7b_codex_review_fixes.py` | 2 | mvp-0.32(2) |
| `test_rw7b_fix_round2.py` | 3 | mvp-0.32(3) |
| `test_serve_eligibility.py` | 17 | mvp-0.27(17) |
| `test_serve_eligibility_review.py` | 22 | mvp-0.27(19),mvp-0.26(6) |
| `test_sg_slip_vs_gap.py` | 4 | mvp-0.55(5) |
| `test_source_set_synthesis.py` | 1 | mvp-0.6(1) |
| `test_stuck_prompt_replay.py` | 3 | mvp-0.12(3) |
| `test_te3a_lesson_opportunity.py` | 3 | mvp-0.51(3) |
| `test_te3b_clock.py` | 1 | mvp-0.52(1) |
| `test_te3b_codex_review.py` | 4 | mvp-0.53(4) |
| `test_te3b_features.py` | 1 | mvp-0.52(1) |
| `test_te3b_population.py` | 1 | mvp-0.52(1) |
| `test_teach_back.py` | 3 | mvp-0.10(2),mvp-0.9(2) |
| `test_teacher_exam_question_guard.py` | 2 | mvp-0.41(2),mvp-0.51(1) |
| `test_teacher_te0_review_fixes.py` | 3 | mvp-0.23(4) |
| `test_teacher_te1_lesson.py` | 1 | mvp-0.40(1) |
| `test_teacher_te1b_landing_r2.py` | 8 | mvp-0.43(8) |
| `test_teacher_te1b_rereview_fixes.py` | 4 | mvp-0.43(4) |
| `test_teacher_te1b_review_fixes.py` | 6 | mvp-0.43(6) |
| `test_teacher_te1b_suggestions.py` | 16 | mvp-0.43(16),mvp-0.42(3) |
| `test_teacher_te2_lessons.py` | 4 | mvp-0.50(4) |
| `test_teacher_te2_sidecar.py` | 2 | mvp-0.51(2),mvp-0.50(1) |
| `test_teacher_te2log_episodes.py` | 2 | mvp-0.41(2) |
| `test_teacher_te2log_node_held.py` | 2 | mvp-0.41(2) |
| `test_teacher_te2log_report.py` | 1 | mvp-0.41(1) |
| `test_unresolved_cause_gate.py` | 6 | mvp-0.8(6),mvp-0.7(1) |
| `test_ux_phase1_round2_rereview.py` | 2 | mvp-0.14(2) |
| `test_ux_phase2_error_type_proposals.py` | 1 | mvp-0.6(1) |
| `test_ux_phase4_feedback.py` | 26 | mvp-0.10(12),mvp-0.20(6),mvp-0.11(3) |
| `test_ux_phase4_landing.py` | 5 | mvp-0.25(2),mvp-0.24(2),mvp-0.20(1) |
| `test_value_candidates.py` | 3 | mvp-0.8(2),mvp-0.6(1) |
| `test_version_floor.py` | 1 | mvp-0.57(1) |
| `test_voi_merge_composition.py` | 8 | mvp-0.21(9) |
| `test_voi_stopping.py` | 34 | mvp-0.21(20),mvp-0.20(15),mvp-0.10(2) |
| `test_voi_v2.py` | 22 | mvp-0.21(28),mvp-0.20(2) |
| `test_why_cases.py` | 1 | mvp-0.47(1) |
| `test_why_reader.py` | 4 | mvp-0.47(4) |

### D7

| file | cases left on a tag | tags (top 3, cases) |
|---|---|---|
| `test_daily_plan_kill_switch.py` | 1 | mvp-0.13(1) |
| `test_ih2_offer_ceiling_and_unseen.py` | 2 | mvp-0.55(1),mvp-0.54(1) |
| `test_reading_step_switch.py` | 1 | mvp-0.9(2),mvp-0.13(1),mvp-0.14(1) |
| `test_rofu_generator_switches.py` | 12 | mvp-0.50(21),mvp-0.49(1) |
| `test_roles_switch_off.py` | 1 | mvp-0.6(1) |
| `test_rw5c_switch_off.py` | 1 | mvp-0.6(1) |
| `test_te3b_offers.py` | 1 | mvp-0.53(1) |


**Not done**, in the order the next part should take it: (1) the 89 partly moved files: their tests that still need a tag are named, but 166 files are untouched, mostly callers that pass a tag through `split_vault`, `daily_plan_build_helpers`, `ux_phase1_support.set_config`, `voi_stopping_helpers` and `serve_eligibility_helpers` (981 cases in the untouched files and 557 left in the partly moved ones: each caller decides); (2) the ten local-`TAG` files put back (`test_batch3_landing`, `test_reader_ca2_one_ask`, `test_ro5_landing`, `test_ro6_tail_data`, `test_rofu_generator_switches`, `test_lp_claim_fixes`, `test_field_workbench_signals`, `test_ro4_objective_serving`, `test_ro6_serving`, `test_router_failure_records`): their local helpers read `TAG`, so the moved half needs a `version` parameter first; (3) `test_pfc_unverified_unassessed` (189 cases, parametrized over every tag of the split family: the head is one parameter; the others are D5/D6's set); (4) the vacuity sample covers the first helper rounds only; (5) the D4 files are not touched except `test_hypothesis_marks_context`.

## 8. Findings, ledger, gates

- **D-33** (ledger): `test_followup_next_matrix::test_the_matrix[plan-complete-before-preparing]` fails at the head with the plan's status still `open` after `_finish_the_plan`'s steps (`assert 'open' in {'complete', 'stopped'}`); it passes at mvp-0.45. The cell is pinned to `FOLLOWUP_SERVE_ALGORITHM_VERSION` in the test. Cause not read. Due at arc D's close (D7's lane, since the cell is the `preparing` arm of the follow-up switch).
- `test_hypothesis_marks_context::test_with_no_mark_the_card_is_what_it_was...` asserts `card_version.startswith(CARD_VERSION)` (`learner_state_card_v2`); the head's card is `learner_state_card_v3+ad23`. Not a bug: the test reads the first tag's card; it uses `journey_old_tag`.
- Gates run: the 343 census files and 25 D4 files, all green; `tests/test_identity_pins.py`, `test_retired_config_identities`, `test_architecture`, `test_test_layout`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_structure_ratchets`, `test_version_floor`, `test_affected_tests` (894 passed, 2 xfailed, the xfails existing); `lint-imports --no-cache` (42 kept, 0 broken); `ruff check`; `check_gate_partition.py` (collected 30835). The landing selection was not run (the orchestrator's).

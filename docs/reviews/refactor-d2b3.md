# Refactor D2b (part 2b): tests that name old tags

Step D2b part 2b of arc D (`docs/specs/refactor_strategy_v3.md` §2.6), on branch `refactor/d2b3-old-tag-tests`, based on main `1da959e7d7` (D1 landed, floor mvp-0.58, head mvp-0.59). Tests and test helpers only; nothing under `src/` changed; no test deleted. **This is a partial landing**: the census is 4,850 test cases in 442 files and the step stopped at a batch boundary with 873 cases emptied (§3). What is done, what passes at the head but is not yet edited, and what stays on its tag are all listed below.

## 1. Method

- **Census.** D1's plugin (a wrapper of `version_floor.may_open_below_floor` that records the running test and the vault's tag when the vault is below the floor), rebuilt as a scratch plugin, over every `test_*.py` that names a tag, a tag writer or a vault builder (481 candidate files plus the 470 of D1's appendix: 442 files hold a case), run in chunks of about 100 files at `-n 4`, `-m "not arc_close"`. Upgrade and successor files (names containing `upgrade` or `successor`) are left to D3 and not counted.
- **Experiment (the sort).** A second scratch plugin takes every old tag a test helper writes to the head instead: `tests.helpers._set_algorithm_version_at` returns without writing when the tag is below the floor, and `pin_old_basic_vault` returns its argument. Every census file was run that way. A test that passes there only needed some tag (re-tag); a test that fails has the old path as its subject, a kill switch, or finds a difference to read. 223 of the 442 files pass entirely; 219 hold at least one failing test (870 failing tests in all). Passing under the experiment does not by itself prove an assertion non-vacuous: the re-tagged files kept every assertion and ran green at the head, and I read the ones I edited by hand (§4).
- **Edit.** Batch 1 by hand (the AD helpers). Batch 2 by script: exact-pattern line rules over the 223 all-passing files and the 37 helper modules only they use: a whole-statement `set_algorithm_version(x, <old tag>)` line is deleted, `x = pin_old_basic_vault(x)` is deleted, `version=<old tag>` at a call site becomes `version=LATEST_ALGORITHM_VERSION`; then `ruff --select F401,F821 --fix` on the changed files and a manual import for the 30 files the script left without one.

## 2. Census before and after

| | test cases | files |
|---|---|---|
| before (this tip's parent) | 4850 | 442 |
| after (emptied: 73 files) | 3977 | 369 |

The "after" count combines the re-run of the edited files and the before count of every untouched file; the whole census was not re-run (the orchestrator's landing run is the check).

## 3. What each file is

- **Re-tagged** (cases now 0): 73 files.
- **Re-tag pending**: 150 files (1470 cases) whose every test passes at the head under the experiment but whose tag comes in through a helper's default or a shared fixture (`TAG`/`version=` defaults in `*_helpers.py` used also by files that fail at the head, `allow_below_floor(root)` for a copied fixture, or a config written directly). They need a per-helper edit (pass `LATEST_ALGORITHM_VERSION` at the call sites, or move the default once its other users have moved); none was edited here.
- **Old path / switch / finding, pending classification**: 219 files (2507 cases, 870 tests that fail at the head). Not read test by test. A file here may hold re-taggable tests beside failing ones; the split is per test.

### Table of every file

| file | cases before | cases after | tests failing at the head | disposition |
|---|---|---|---|---|
| `test_active_errors_overlay.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_ad1_codex_rereview_fixes.py` | 7 | 0 | 0 | re-tagged |
| `test_ad1_codex_review_fixes.py` | 11 | 0 | 0 | re-tagged |
| `test_ad1_fix_round4.py` | 5 | 0 | 0 | re-tagged |
| `test_ad1_fix_round5.py` | 8 | 0 | 0 | re-tagged |
| `test_ad1_fix_round6.py` | 6 | 0 | 0 | re-tagged |
| `test_ad1_fix_round7.py` | 2 | 0 | 0 | re-tagged |
| `test_ad1_fix_round8.py` | 10 | 0 | 0 | re-tagged |
| `test_ad1_fix_round9.py` | 4 | 0 | 0 | re-tagged |
| `test_ad1_outside_and_cli.py` | 8 | 0 | 0 | re-tagged |
| `test_ad1_send_guard.py` | 7 | 0 | 0 | re-tagged |
| `test_ad23_contract.py` | 17 | 0 | 0 | re-tagged |
| `test_ad23_fix_r5.py` | 7 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_ad23_fix_r6.py` | 3 | 0 | 0 | re-tagged |
| `test_ad23_fix_r7.py` | 5 | 0 | 0 | re-tagged |
| `test_ad23_fix_r8.py` | 13 | 0 | 0 | re-tagged |
| `test_ad23_fix_r9.py` | 4 | 0 | 0 | re-tagged |
| `test_ad23_fix_review.py` | 10 | 0 | 0 | re-tagged |
| `test_ad23_intent_compose.py` | 53 | 0 | 0 | re-tagged |
| `test_ad23_inversion.py` | 45 | 0 | 0 | re-tagged |
| `test_ad23_owner_decisions.py` | 5 | 0 | 0 | re-tagged |
| `test_ad23_pool_membership.py` | 42 | 0 | 0 | re-tagged |
| `test_ad2_model.py` | 12 | 0 | 0 | re-tagged |
| `test_ad2_serving.py` | 30 | 2 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_ad3_monitoring.py` | 3 | 0 | 0 | re-tagged |
| `test_ad3_reading.py` | 2 | 0 | 0 | re-tagged |
| `test_ad3_relatedness.py` | 6 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_ad3_subject_view.py` | 5 | 0 | 0 | re-tagged |
| `test_ad_denial_log.py` | 10 | 9 | 8 | old path / switch / finding pending (8 tests fail at the head) |
| `test_ad_epoch.py` | 12 | 0 | 0 | re-tagged |
| `test_ad_guard.py` | 37 | 0 | 0 | re-tagged |
| `test_ad_guard_offer_receipts.py` | 5 | 0 | 0 | re-tagged |
| `test_ad_guard_reachable_reads.py` | 4 | 0 | 0 | re-tagged |
| `test_ad_projection.py` | 3 | 0 | 0 | re-tagged |
| `test_ad_protected_readings.py` | 154 | 0 | 0 | re-tagged |
| `test_ad_protected_tables.py` | 4 | 0 | 0 | re-tagged |
| `test_adaptive_difficulty_ad1.py` | 12 | 0 | 0 | re-tagged |
| `test_ai_compare.py` | 1 | 1 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_anti_double_count.py` | 6 | 6 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_arcb_close_fixes.py` | 5 | 5 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_assessment_contracts.py` | 5 | 5 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_assumed_known.py` | 38 | 38 | 6 | old path / switch / finding pending (6 tests fail at the head) |
| `test_attempt_chain_records.py` | 10 | 10 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_attempt_completion.py` | 4 | 4 | 4 | old path / switch / finding pending (4 tests fail at the head) |
| `test_attempt_content_state_race.py` | 6 | 6 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_batch3_landing.py` | 22 | 22 | 19 | old path / switch / finding pending (19 tests fail at the head) |
| `test_canonical_projection_rollout.py` | 3 | 3 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_capability_residual.py` | 3 | 0 | 0 | re-tagged |
| `test_causal_attribution_exhibit.py` | 2 | 0 | 0 | re-tagged |
| `test_causal_attribution_p0.py` | 3 | 3 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_causal_factor_deferral.py` | 14 | 14 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_causal_orchestrator.py` | 1 | 1 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_causal_p2_acceptance.py` | 16 | 16 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_causal_repair_mapping_p2.py` | 5 | 5 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_certification_cold_probe.py` | 25 | 25 | 24 | old path / switch / finding pending (24 tests fail at the head) |
| `test_characterization_assessment_exam.py` | 2 | 0 | 0 | re-tagged |
| `test_characterization_certification_ledger.py` | 4 | 0 | 0 | re-tagged |
| `test_chat_total_transport_deadline.py` | 1 | 1 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_cold_retry_reschedule.py` | 30 | 30 | 12 | old path / switch / finding pending (12 tests fail at the head) |
| `test_conjunctive_instruments.py` | 28 | 0 | 0 | re-tagged |
| `test_contract_frontier_coverage.py` | 2 | 0 | 0 | re-tagged |
| `test_contrast_pairs.py` | 12 | 0 | 0 | re-tagged |
| `test_coverage_denominator_boundary.py` | 6 | 0 | 0 | re-tagged |
| `test_curriculum_c0b_landing.py` | 2 | 2 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_curriculum_c1_codex_review_fixes.py` | 9 | 9 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_curriculum_c1_fix_round2.py` | 13 | 13 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_curriculum_c1_fix_round3.py` | 9 | 9 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_curriculum_c1_fix_round4.py` | 7 | 7 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_curriculum_c1_fix_round5.py` | 8 | 8 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_curriculum_c1_landing.py` | 7 | 7 | 5 | old path / switch / finding pending (5 tests fail at the head) |
| `test_curriculum_c1_plan_follows_path.py` | 37 | 37 | 16 | old path / switch / finding pending (16 tests fail at the head) |
| `test_curriculum_c1_round5_followups.py` | 6 | 6 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_daily_plan_composition.py` | 1 | 0 | 0 | re-tagged |
| `test_daily_plan_kill_switch.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_data_capture_a1_prefilter.py` | 9 | 9 | 6 | old path / switch / finding pending (6 tests fail at the head) |
| `test_data_capture_a2_measurement.py` | 22 | 22 | 18 | old path / switch / finding pending (18 tests fail at the head) |
| `test_data_capture_a5_not_ready_floor.py` | 8 | 8 | 6 | old path / switch / finding pending (6 tests fail at the head) |
| `test_data_capture_a6_delayed_pick.py` | 8 | 8 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_data_capture_codex_rereview.py` | 24 | 24 | 24 | old path / switch / finding pending (24 tests fail at the head) |
| `test_data_capture_codex_review.py` | 8 | 8 | 7 | old path / switch / finding pending (7 tests fail at the head) |
| `test_data_capture_landing_review.py` | 24 | 24 | 24 | old path / switch / finding pending (24 tests fail at the head) |
| `test_data_capture_report.py` | 3 | 3 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_decider_landing.py` | 7 | 7 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_diagnosis_async_router.py` | 2 | 2 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_diagnosis_card.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_diagnosis_pipeline.py` | 2 | 2 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_diagnosis_replay.py` | 1 | 1 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_diagnostic_pack.py` | 10 | 10 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_discrimination_profiles.py` | 17 | 0 | 0 | re-tagged |
| `test_dl2_rw4b_keyed_pick_check.py` | 3 | 3 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_doctor.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_durable_promotion_arms.py` | 22 | 22 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_embedding_store.py` | 1 | 1 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_error_hunt_items.py` | 13 | 0 | 0 | re-tagged |
| `test_evsi_router_composition.py` | 5 | 5 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_evsi_staged_binding.py` | 2 | 2 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_exam_protection.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_exam_protection_landing.py` | 2 | 2 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_exam_protection_review.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_exam_session.py` | 3 | 3 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_facet_authority.py` | 3 | 3 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_facet_authority_rereview.py` | 10 | 10 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_facet_authority_review.py` | 10 | 10 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_facet_evidence_timeline.py` | 4 | 4 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_facet_identity_actions.py` | 28 | 28 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_facet_identity_composition.py` | 3 | 3 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_facet_outcome_view.py` | 28 | 28 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_facet_reword_confirm.py` | 33 | 33 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_facet_reword_confirm_review.py` | 8 | 8 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_facet_reword_paths.py` | 12 | 12 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_facet_rewords.py` | 6 | 6 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_facet_span_support.py` | 20 | 20 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_failure_triage.py` | 22 | 22 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_failure_triage_causal_gate.py` | 1 | 1 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_family_memory_projection.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_field_split_outcomes.py` | 1 | 0 | 0 | re-tagged |
| `test_field_workbench_signals.py` | 16 | 16 | 7 | old path / switch / finding pending (7 tests fail at the head) |
| `test_figure_wait_estimate.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_figures_prefetch_review_fixes.py` | 3 | 3 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_followup_codex_review.py` | 80 | 78 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_followup_fg1c_codex_review.py` | 13 | 13 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_followup_fg1c_r1_exposure_independence.py` | 35 | 35 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_followup_fg1d_panel_read.py` | 8 | 8 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_followup_fg1d_probe_shadow.py` | 12 | 12 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_followup_generate_e2e.py` | 11 | 11 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_followup_journey.py` | 19 | 19 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_followup_live_shape.py` | 8 | 8 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_followup_next_matrix.py` | 71 | 71 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_followup_reserved_only.py` | 29 | 29 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_followup_rival_factor.py` | 22 | 22 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_followup_router.py` | 15 | 15 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_followup_single_use.py` | 8 | 8 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_followup_workflow.py` | 10 | 10 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_followups_batch5_lesson.py` | 7 | 7 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_followups_batch5_recap_dependencies.py` | 12 | 7 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_followups_batch5_recap_protection.py` | 7 | 7 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_followups_batch6_review_fixes.py` | 2 | 2 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_followups_batch6_router_report.py` | 2 | 2 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_followups_batch6_te1b_card.py` | 3 | 3 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_followups_batch7_prefetch_capped_resume.py` | 3 | 3 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_followups_nov2_figure_provenance.py` | 1 | 1 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_followups_nov2_help_fold.py` | 6 | 6 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_forced_withdrawal_records.py` | 10 | 10 | 6 | old path / switch / finding pending (6 tests fail at the head) |
| `test_forecast_receipts.py` | 17 | 17 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_forecast_receipts_landing.py` | 2 | 1 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_generated_item_gate.py` | 3 | 3 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_goal_certification_any_of.py` | 14 | 14 | 8 | old path / switch / finding pending (8 tests fail at the head) |
| `test_golden_path_fixture.py` | 4 | 4 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_grading_cli.py` | 9 | 0 | 0 | re-tagged |
| `test_graph_editor_reads.py` | 8 | 8 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_held_grade_composition.py` | 5 | 1 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_held_grade_evidence.py` | 16 | 16 | 4 | old path / switch / finding pending (4 tests fail at the head) |
| `test_hint_telemetry.py` | 1 | 0 | 0 | re-tagged |
| `test_hot_path_eligibility_cutover.py` | 3 | 3 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_hypothesis_marks.py` | 35 | 34 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_hypothesis_marks_context.py` | 11 | 11 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_identifiability_doctor.py` | 3 | 0 | 0 | re-tagged |
| `test_ih2_lessons_compete.py` | 40 | 40 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_ih2_offer_ceiling_and_unseen.py` | 23 | 23 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_ih2_one_open_offer.py` | 36 | 36 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_ih3_learner_preferences.py` | 16 | 16 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_ih3_phone_host.py` | 9 | 9 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_ih4_preferences_inform_router.py` | 34 | 34 | 4 | old path / switch / finding pending (4 tests fail at the head) |
| `test_ih6_workbench_open_item.py` | 37 | 37 | 5 | old path / switch / finding pending (5 tests fail at the head) |
| `test_ih7_lesson_sources_follow_diagnosis.py` | 44 | 44 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_ih_lesson_candidate_after_cold_miss.py` | 28 | 28 | 5 | old path / switch / finding pending (5 tests fail at the head) |
| `test_ih_numeric_seed.py` | 12 | 12 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_instruct_handoff_ih1.py` | 6 | 0 | 0 | re-tagged |
| `test_instrument_servability_journeys.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_intent_checks.py` | 10 | 10 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_intent_codex_rereview.py` | 10 | 10 | 5 | old path / switch / finding pending (5 tests fail at the head) |
| `test_intent_codex_review.py` | 25 | 25 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_intent_exclusion.py` | 15 | 15 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_intent_fix_round4.py` | 30 | 30 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_intent_fix_round5.py` | 26 | 10 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_intent_fix_round6.py` | 44 | 44 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_intent_fix_round7.py` | 12 | 9 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_intent_goal_deadline.py` | 4 | 4 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_intent_orchestrator_rulings.py` | 9 | 9 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_intent_plan.py` | 11 | 11 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_intent_recall_targets.py` | 4 | 4 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_intent_resolution.py` | 22 | 22 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_intent_rpc.py` | 6 | 6 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_km1_doctor.py` | 5 | 5 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_km2_activation.py` | 7 | 7 | 5 | old path / switch / finding pending (5 tests fail at the head) |
| `test_km2_sim_gates.py` | 3 | 3 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_km2_write_path.py` | 9 | 9 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_km2b_consumer_rekey.py` | 57 | 57 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_km3_projections.py` | 6 | 6 | 4 | old path / switch / finding pending (4 tests fail at the head) |
| `test_km4_taxonomy.py` | 9 | 9 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_km5_sim_gates.py` | 2 | 0 | 0 | re-tagged |
| `test_laddered_stems.py` | 5 | 0 | 0 | re-tagged |
| `test_learner_blindness_relax.py` | 2 | 2 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_learner_protection_predicates.py` | 4 | 0 | 0 | re-tagged |
| `test_learner_report_superseded.py` | 57 | 57 | 20 | old path / switch / finding pending (20 tests fail at the head) |
| `test_learner_text_gaps.py` | 28 | 28 | 4 | old path / switch / finding pending (4 tests fail at the head) |
| `test_learner_text_gaps_composition.py` | 7 | 7 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_learner_text_gaps_flow.py` | 13 | 13 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_learner_text_gaps_rereview.py` | 18 | 18 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_learner_text_gaps_review.py` | 29 | 29 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_lp_claim_fixes.py` | 18 | 18 | 7 | old path / switch / finding pending (7 tests fail at the head) |
| `test_lp_claim_fixes_rereview.py` | 23 | 23 | 15 | old path / switch / finding pending (15 tests fail at the head) |
| `test_lp_claim_fixes_review.py` | 21 | 21 | 8 | old path / switch / finding pending (8 tests fail at the head) |
| `test_map_untested.py` | 3 | 3 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_mcp_c1a_landing.py` | 5 | 5 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_measurement_corrections.py` | 2 | 2 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_measurement_rank.py` | 4 | 0 | 0 | re-tagged |
| `test_method_explicit_landing.py` | 2 | 2 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_misconception_registry.py` | 7 | 7 | 7 | old path / switch / finding pending (7 tests fail at the head) |
| `test_mobile_v2_checks.py` | 4 | 4 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_mobile_v2_followup.py` | 6 | 6 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_mobile_v2_rereview_fixes.py` | 1 | 1 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_mobile_v2_review_fixes.py` | 1 | 1 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_mobile_v3_codex_review.py` | 15 | 12 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_mobile_v3_probes.py` | 9 | 9 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_mvp017_route_check_replay.py` | 3 | 3 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_narrative_rollback_overlap.py` | 4 | 4 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_observation_ledger_bulk.py` | 5 | 4 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_p0_cutover_mvp08.py` | 8 | 8 | 6 | old path / switch / finding pending (6 tests fail at the head) |
| `test_p0_projection_cutover.py` | 6 | 6 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_p2_acceptance.py` | 3 | 3 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_p2_leakage_suite.py` | 2 | 2 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_pfc_unassessed_readers.py` | 7 | 5 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_pfc_unverified_unassessed.py` | 190 | 190 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_placement_diagnosis_decides.py` | 32 | 1 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_placement_opening_probes.py` | 17 | 17 | 14 | old path / switch / finding pending (14 tests fail at the head) |
| `test_placement_report.py` | 5 | 5 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_placement_sidecar.py` | 8 | 8 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_placement_signals.py` | 5 | 5 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_placement_split_grades.py` | 10 | 0 | 0 | re-tagged |
| `test_placement_unevidenced_return.py` | 24 | 24 | 11 | old path / switch / finding pending (11 tests fail at the head) |
| `test_plan_determinism.py` | 12 | 12 | 10 | old path / switch / finding pending (10 tests fail at the head) |
| `test_plan_determinism_landing.py` | 19 | 19 | 16 | old path / switch / finding pending (16 tests fail at the head) |
| `test_plan_follows_path.py` | 16 | 16 | 6 | old path / switch / finding pending (6 tests fail at the head) |
| `test_planted_misgrade.py` | 1 | 0 | 0 | re-tagged |
| `test_pr4_superseded_claims_landing.py` | 4 | 4 | 4 | old path / switch / finding pending (4 tests fail at the head) |
| `test_practice_information.py` | 3 | 3 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_probe_episodes.py` | 2 | 2 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_probe_robust_cutover.py` | 7 | 7 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_probe_targeting.py` | 4 | 4 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_projection_evidence_polarity.py` | 4 | 3 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_provenance.py` | 1 | 1 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_quick_add.py` | 2 | 2 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_quick_check.py` | 19 | 19 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_rbeq_pr2_landing.py` | 10 | 10 | 10 | old path / switch / finding pending (10 tests fail at the head) |
| `test_reader_ca1_as_printed.py` | 1 | 1 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_ca2_astra_handoff.py` | 10 | 10 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_ca2_astra_handoff_recovery.py` | 4 | 4 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_ca2_codex_rereview.py` | 8 | 8 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_ca2_codex_review.py` | 20 | 20 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_ca2_fix_orchestrator.py` | 9 | 9 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_ca2_one_ask.py` | 20 | 20 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_ca5a_find_section.py` | 1 | 1 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_cues.py` | 1 | 0 | 0 | re-tagged |
| `test_reader_dialogue.py` | 1 | 1 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_digest_narrative.py` | 30 | 30 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_followups.py` | 36 | 36 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_followups_rereview.py` | 6 | 6 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_followups_review.py` | 18 | 18 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_followups_round3.py` | 6 | 6 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_followups_round4.py` | 2 | 2 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_followups_round5.py` | 3 | 3 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_followups_round6.py` | 3 | 3 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_followups_round7.py` | 3 | 3 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_followups_round8.py` | 4 | 4 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_guidance.py` | 9 | 9 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_reader_question_note_id_placement.py` | 4 | 4 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_recap_review.py` | 4 | 4 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_reader_recap_review_r2.py` | 2 | 2 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_reader_recap_review_r3.py` | 5 | 5 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_reader_rw1b_review.py` | 2 | 2 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_rw3a_landing.py` | 5 | 5 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_reader_rw4b_admission_idempotency.py` | 5 | 5 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_reader_rw4b_fix6.py` | 4 | 4 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_reader_rw5d_p4b_teacher_visuals.py` | 21 | 21 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_reader_rw6b_landing.py` | 5 | 5 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_rw6b_p2_landing.py` | 4 | 4 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_reader_workbench_rw2a.py` | 58 | 58 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_reading_paths.py` | 48 | 48 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_reading_step_switch.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_rebuild_equivalence.py` | 4 | 4 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_rebuild_equivalence_review.py` | 8 | 8 | 7 | old path / switch / finding pending (7 tests fail at the head) |
| `test_rebuild_orchestrator.py` | 6 | 6 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_recall_calibration.py` | 2 | 2 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_recall_coverage_interventions.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_receipt_derivation.py` | 2 | 2 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_receipt_exactness.py` | 4 | 4 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_recurrence_benchmarks.py` | 23 | 0 | 0 | re-tagged |
| `test_recurrence_commands.py` | 44 | 44 | 30 | old path / switch / finding pending (30 tests fail at the head) |
| `test_recurrence_deferral.py` | 3 | 3 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_recurrence_groups.py` | 11 | 11 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_recurrence_live.py` | 30 | 30 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_recurrence_merge_composition.py` | 5 | 0 | 0 | re-tagged |
| `test_reference_gate_imports.py` | 17 | 17 | 6 | old path / switch / finding pending (6 tests fail at the head) |
| `test_refusal_records.py` | 6 | 6 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_remaining_decision_records.py` | 4 | 4 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_required_method_authority.py` | 4 | 0 | 0 | re-tagged |
| `test_required_method_grading.py` | 19 | 19 | 8 | old path / switch / finding pending (8 tests fail at the head) |
| `test_required_method_reopened.py` | 4 | 0 | 0 | re-tagged |
| `test_required_method_rereview.py` | 4 | 0 | 0 | re-tagged |
| `test_required_method_round3.py` | 4 | 0 | 0 | re-tagged |
| `test_required_method_round3_final_verify.py` | 10 | 0 | 0 | re-tagged |
| `test_required_method_round3_rereview.py` | 4 | 0 | 0 | re-tagged |
| `test_required_method_round3_review.py` | 14 | 9 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_residual_diagnostics.py` | 2 | 1 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_ro0_codex_review.py` | 14 | 14 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_ro0_codex_verify.py` | 16 | 16 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_ro0_gate.py` | 5 | 5 | 4 | old path / switch / finding pending (4 tests fail at the head) |
| `test_ro0_report.py` | 3 | 3 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_ro0_row10_cold_timing.py` | 3 | 3 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_ro0_row12_trajectory.py` | 3 | 3 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_ro0_row3_ask_availability.py` | 7 | 7 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_ro0_rows7_8_sessions.py` | 4 | 4 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_ro0_rows9_13_decision_state.py` | 13 | 13 | 5 | old path / switch / finding pending (5 tests fail at the head) |
| `test_ro1_availability.py` | 7 | 7 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_ro1_availability_reads.py` | 21 | 21 | 6 | old path / switch / finding pending (6 tests fail at the head) |
| `test_ro1_interval_factor.py` | 7 | 7 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_ro1_projection.py` | 17 | 17 | 11 | old path / switch / finding pending (11 tests fail at the head) |
| `test_ro1_self_report.py` | 3 | 3 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_ro2_ad_document_ir.py` | 6 | 6 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_ro2_ad_raw_document_reads.py` | 2 | 2 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_ro2_history_protection.py` | 2 | 2 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_ro4_codex_review.py` | 6 | 6 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_ro4_goals.py` | 4 | 4 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_ro4_objective_serving.py` | 6 | 6 | 4 | old path / switch / finding pending (4 tests fail at the head) |
| `test_ro4_trace_report.py` | 3 | 1 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_ro5_calibration.py` | 4 | 4 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_ro5_checks.py` | 6 | 6 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_ro5_codex_rereview.py` | 5 | 5 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_ro5_codex_review.py` | 4 | 3 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_ro5_landing.py` | 10 | 10 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_ro5_picks.py` | 3 | 3 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_ro5_stop_coin.py` | 3 | 3 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_ro6_codex_rereview.py` | 2 | 2 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_ro6_codex_review.py` | 2 | 1 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_ro6_landing.py` | 4 | 4 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_ro6_serving.py` | 5 | 5 | 4 | old path / switch / finding pending (4 tests fail at the head) |
| `test_ro6_tail_data.py` | 6 | 6 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_rofu_ad_latent.py` | 1 | 0 | 0 | re-tagged |
| `test_rofu_ad_link.py` | 3 | 3 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_rofu_carried.py` | 5 | 5 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_rofu_generator_switches.py` | 12 | 12 | 11 | old path / switch / finding pending (11 tests fail at the head) |
| `test_rofu_learning.py` | 5 | 5 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_rofu_monotone.py` | 3 | 3 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_rofu_review_draw.py` | 3 | 3 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_rofu_speed.py` | 3 | 3 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_rofu_switch_key.py` | 12 | 12 | 11 | old path / switch / finding pending (11 tests fail at the head) |
| `test_roles_switch_off.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_rospeed2_connections.py` | 8 | 8 | 4 | old path / switch / finding pending (4 tests fail at the head) |
| `test_rospeed2_section_map.py` | 16 | 0 | 0 | re-tagged |
| `test_rospeed_ad_link.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_rospeed_join.py` | 7 | 7 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_route_rules_in_grader.py` | 26 | 26 | 9 | old path / switch / finding pending (9 tests fail at the head) |
| `test_router_card.py` | 9 | 9 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_router_card_reading_gaps.py` | 7 | 7 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_router_failure_records.py` | 8 | 8 | 8 | old path / switch / finding pending (8 tests fail at the head) |
| `test_router_g1_feasibility.py` | 8 | 8 | 6 | old path / switch / finding pending (6 tests fail at the head) |
| `test_router_g3_propensity.py` | 2 | 2 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_router_g4_restraint.py` | 12 | 12 | 10 | old path / switch / finding pending (10 tests fail at the head) |
| `test_router_g7_fallback.py` | 3 | 3 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_router_offer_log.py` | 2 | 0 | 0 | re-tagged |
| `test_router_presentations.py` | 6 | 6 | 5 | old path / switch / finding pending (5 tests fail at the head) |
| `test_router_probe_ties.py` | 9 | 9 | 4 | old path / switch / finding pending (4 tests fail at the head) |
| `test_router_r1_composition.py` | 8 | 8 | 4 | old path / switch / finding pending (4 tests fail at the head) |
| `test_router_r2a_landing.py` | 4 | 4 | 4 | old path / switch / finding pending (4 tests fail at the head) |
| `test_router_r2a_serving.py` | 10 | 10 | 5 | old path / switch / finding pending (5 tests fail at the head) |
| `test_router_r2b_agreement.py` | 3 | 3 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_router_r2b_requests.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_router_r2b_serving.py` | 20 | 20 | 15 | old path / switch / finding pending (15 tests fail at the head) |
| `test_router_r2bc_landing.py` | 6 | 6 | 5 | old path / switch / finding pending (5 tests fail at the head) |
| `test_router_r2c_retrieval.py` | 8 | 8 | 5 | old path / switch / finding pending (5 tests fail at the head) |
| `test_router_r2c_teach_back.py` | 6 | 6 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_router_reader_activity.py` | 18 | 18 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_router_why_copy.py` | 1 | 0 | 0 | re-tagged |
| `test_rw5c_switch_off.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_rw7b_codex_review_fixes.py` | 10 | 10 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_rw7b_fix_round2.py` | 5 | 5 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_scoreboard.py` | 1 | 0 | 0 | re-tagged |
| `test_serve_eligibility.py` | 17 | 17 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_serve_eligibility_review.py` | 23 | 23 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_sg_slip_vs_gap.py` | 24 | 24 | 4 | old path / switch / finding pending (4 tests fail at the head) |
| `test_shadow_rebuild.py` | 4 | 4 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_sidecar_adjudication.py` | 7 | 7 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_sidecar_close_cancels_jobs.py` | 2 | 0 | 0 | re-tagged |
| `test_sidecar_contract.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_sidecar_knowledge_model.py` | 4 | 4 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_sim_goals.py` | 3 | 3 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_sim_probe_validation.py` | 1 | 1 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_sim_teach_back.py` | 2 | 2 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_simulation.py` | 4 | 4 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_source_first_needs.py` | 17 | 17 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_source_set_synthesis.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_stuck_prompt.py` | 46 | 46 | 5 | old path / switch / finding pending (5 tests fail at the head) |
| `test_stuck_prompt_composition.py` | 6 | 6 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_stuck_prompt_replay.py` | 4 | 0 | 0 | re-tagged |
| `test_subject_registry.py` | 4 | 4 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_success_head_cli.py` | 8 | 8 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_t6_followup_composition.py` | 2 | 0 | 0 | re-tagged |
| `test_te3a_lesson_opportunity.py` | 16 | 16 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_te3b_clock.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_te3b_codex_review.py` | 9 | 9 | 4 | old path / switch / finding pending (4 tests fail at the head) |
| `test_te3b_features.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_te3b_offers.py` | 9 | 9 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_te3b_population.py` | 2 | 2 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_teach_back.py` | 3 | 3 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_teacher_exam_question_guard.py` | 33 | 33 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_teacher_te0_confidence_events.py` | 3 | 3 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_teacher_te0_review_fixes.py` | 3 | 3 | 3 | old path / switch / finding pending (3 tests fail at the head) |
| `test_teacher_te1_curriculum_c4.py` | 3 | 0 | 0 | re-tagged |
| `test_teacher_te1_lesson.py` | 17 | 17 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_teacher_te1_review_fixes.py` | 30 | 30 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_teacher_te1_weight.py` | 10 | 10 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_teacher_te1b_landing_r2.py` | 9 | 9 | 8 | old path / switch / finding pending (8 tests fail at the head) |
| `test_teacher_te1b_rereview_fixes.py` | 5 | 5 | 4 | old path / switch / finding pending (4 tests fail at the head) |
| `test_teacher_te1b_review_fixes.py` | 7 | 7 | 6 | old path / switch / finding pending (6 tests fail at the head) |
| `test_teacher_te1b_suggestions.py` | 21 | 21 | 17 | old path / switch / finding pending (17 tests fail at the head) |
| `test_teacher_te2_landing_r1.py` | 2 | 2 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_teacher_te2_lessons.py` | 13 | 13 | 4 | old path / switch / finding pending (4 tests fail at the head) |
| `test_teacher_te2_probes.py` | 12 | 12 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_teacher_te2_review_fixes.py` | 15 | 14 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_teacher_te2_sidecar.py` | 2 | 2 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_teacher_te2log_activity.py` | 6 | 6 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_teacher_te2log_episodes.py` | 23 | 23 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_teacher_te2log_node_held.py` | 5 | 5 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_teacher_te2log_receipt.py` | 3 | 3 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_teacher_te2log_report.py` | 4 | 4 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_tier1_decider.py` | 7 | 0 | 0 | re-tagged |
| `test_today_headline.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_unresolved_cause_gate.py` | 6 | 6 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_ux_phase1_round2_rereview.py` | 2 | 2 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_ux_phase2_error_type_proposals.py` | 1 | 1 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_ux_phase3_today.py` | 4 | 4 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_ux_phase4_feedback.py` | 28 | 28 | 12 | old path / switch / finding pending (12 tests fail at the head) |
| `test_ux_phase4_landing.py` | 5 | 5 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_value_candidates.py` | 3 | 3 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_version_floor.py` | 3 | 3 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_voi_forecasts.py` | 4 | 4 | 0 | re-tag pending (passes at the head with the old tags taken there) |
| `test_voi_merge_composition.py` | 8 | 8 | 2 | old path / switch / finding pending (2 tests fail at the head) |
| `test_voi_stopping.py` | 34 | 34 | 16 | old path / switch / finding pending (16 tests fail at the head) |
| `test_voi_v2.py` | 22 | 22 | 6 | old path / switch / finding pending (6 tests fail at the head) |
| `test_why_cases.py` | 2 | 2 | 1 | old path / switch / finding pending (1 tests fail at the head) |
| `test_why_reader.py` | 5 | 5 | 3 | old path / switch / finding pending (3 tests fail at the head) |

## 4. Every assertion changed, and why

1. `test_adaptive_difficulty_ad1::test_forecast_receipt_written_in_serve_transaction`: the forecasters that wrote a receipt were exactly `["lo_general+composite", "mastery_ekf"]`; at the head AD2's `ad_threshold@...` forecasters write theirs in the same transaction. The assertion now filters those out and keeps the two AD1 forecasters exact; the later counts (`== 2`, receipt ids `== 2`) are `len(receipts)`, the same transaction property.
2. `test_ad3_monitoring::test_monitoring_applies_field_rule_as_monitor_never_gate`: the report had four honest lines and a lessons flag absent "below its tag". At the head the lessons line (Teacher TE3a) and flag are reported. The four subject lines are asserted as before (the lessons line is filtered, and asserted to be present exactly once); the flag set is now the full `FLAG_SWITCHES`.
3. `test_ro2_ad_raw_document_reads::test_a_guard_denial_in_ads_serve_leaves_the_learners_serve_unchanged`: the two steps compared equal modulo `presentation_id`, `block_id`, `plan_id`; at the head the step's `adaptive_difficulty` note also carries `selection_id`, a fresh id per vault (read: the two steps differ only there). It is stripped as the other ids are; every other field is still compared.

No other assertion changed. The two builders `ad23_vault` and `ad_plan_vault` take RO5's randomized check to zero (`RANDOMIZED_CHECKS_OFF`, D2b part 2a's fragment) because with it on 82 AD tests failed at the head and with it at zero 79 of them passed unchanged (the check's block is the plan's first, which D2b part 2a read; the AD slot record is not written for it). That is a pin of a draw the subject does not own, as the rules block allows.

## 5. Findings

- **D-27** (`test_ad23_contract::test_protected_material_is_indistinguishable_from_absent_material[default]`, strict xfail): at the head the protected copy and the absent copy write different `facet_uncertainty` rows (belief 0.99999, status `resolved`, against 0.65, `resolving`). At mvp-0.30 the test held because no facet belief was written. Not read further; ledger row D-27 (the id may collide with another step's: renumber at merge).

## 6. The old-path list (second deliverable)

Grouped by the package whose gate the file exercises, **by the file's name only**: I did not read each failing test to its gate's `file:line`, so the grouping is a starting point for D4-D7's own step 0, not a claim. The tag column is the tag(s) the census saw; "fail" is the number of tests that fail at the head when the tag is taken there.

### D4

| file | cases | fail | tags |
|---|---|---|---|
| `test_certification_cold_probe.py` | 25 | 24 | see census |
| `test_data_capture_codex_rereview.py` | 24 | 24 | see census |
| `test_data_capture_landing_review.py` | 24 | 24 | see census |
| `test_learner_report_superseded.py` | 57 | 20 | see census |
| `test_data_capture_a2_measurement.py` | 22 | 18 | see census |
| `test_route_rules_in_grader.py` | 26 | 9 | see census |
| `test_goal_certification_any_of.py` | 14 | 8 | see census |
| `test_required_method_grading.py` | 19 | 8 | see census |
| `test_data_capture_codex_review.py` | 8 | 7 | see census |
| `test_assumed_known.py` | 38 | 6 | see census |
| `test_data_capture_a1_prefilter.py` | 9 | 6 | see census |
| `test_data_capture_a5_not_ready_floor.py` | 8 | 6 | see census |
| `test_stuck_prompt.py` | 46 | 5 | see census |
| `test_attempt_completion.py` | 4 | 4 | see census |
| `test_held_grade_evidence.py` | 16 | 4 | see census |
| `test_learner_text_gaps.py` | 28 | 4 | see census |
| `test_data_capture_report.py` | 3 | 3 | see census |
| `test_learner_text_gaps_flow.py` | 13 | 3 | see census |
| `test_learner_text_gaps_composition.py` | 7 | 2 | see census |
| `test_learner_text_gaps_review.py` | 29 | 2 | see census |
| `test_attempt_content_state_race.py` | 6 | 1 | see census |
| `test_causal_p2_acceptance.py` | 16 | 1 | see census |
| `test_data_capture_a6_delayed_pick.py` | 8 | 1 | see census |
| `test_hypothesis_marks_context.py` | 11 | 1 | see census |
| `test_stuck_prompt_composition.py` | 6 | 1 | see census |

### D5

| file | cases | fail | tags |
|---|---|---|---|
| `test_recurrence_commands.py` | 44 | 30 | see census |
| `test_ro1_projection.py` | 17 | 11 | see census |
| `test_rebuild_equivalence_review.py` | 8 | 7 | see census |
| `test_km2_activation.py` | 7 | 5 | see census |
| `test_km3_projections.py` | 6 | 4 | see census |
| `test_km4_taxonomy.py` | 9 | 3 | see census |
| `test_rebuild_equivalence.py` | 4 | 3 | see census |
| `test_p0_projection_cutover.py` | 6 | 2 | see census |
| `test_canonical_projection_rollout.py` | 3 | 1 | see census |
| `test_doctor.py` | 1 | 1 | see census |
| `test_family_memory_projection.py` | 1 | 1 | see census |
| `test_km1_doctor.py` | 5 | 1 | see census |
| `test_km2_write_path.py` | 9 | 1 | see census |
| `test_recurrence_deferral.py` | 3 | 1 | see census |
| `test_recurrence_groups.py` | 11 | 1 | see census |
| `test_recurrence_live.py` | 30 | 1 | see census |
| `test_router_reader_activity.py` | 18 | 1 | see census |

### D6

| file | cases | fail | tags |
|---|---|---|---|
| `test_batch3_landing.py` | 22 | 19 | see census |
| `test_teacher_te1b_suggestions.py` | 21 | 17 | see census |
| `test_curriculum_c1_plan_follows_path.py` | 37 | 16 | see census |
| `test_plan_determinism_landing.py` | 19 | 16 | see census |
| `test_voi_stopping.py` | 34 | 16 | see census |
| `test_lp_claim_fixes_rereview.py` | 23 | 15 | see census |
| `test_router_r2b_serving.py` | 20 | 15 | see census |
| `test_placement_opening_probes.py` | 17 | 14 | see census |
| `test_cold_retry_reschedule.py` | 30 | 12 | see census |
| `test_ux_phase4_feedback.py` | 28 | 12 | see census |
| `test_placement_unevidenced_return.py` | 24 | 11 | see census |
| `test_rofu_generator_switches.py` | 12 | 11 | see census |
| `test_rofu_switch_key.py` | 12 | 11 | see census |
| `test_plan_determinism.py` | 12 | 10 | see census |
| `test_rbeq_pr2_landing.py` | 10 | 10 | see census |
| `test_router_g4_restraint.py` | 12 | 10 | see census |
| `test_ad_denial_log.py` | 9 | 8 | see census |
| `test_lp_claim_fixes_review.py` | 21 | 8 | see census |
| `test_router_failure_records.py` | 8 | 8 | see census |
| `test_teacher_te1b_landing_r2.py` | 9 | 8 | see census |
| `test_field_workbench_signals.py` | 16 | 7 | see census |
| `test_lp_claim_fixes.py` | 18 | 7 | see census |
| `test_misconception_registry.py` | 7 | 7 | see census |
| `test_forced_withdrawal_records.py` | 10 | 6 | see census |
| `test_p0_cutover_mvp08.py` | 8 | 6 | see census |
| `test_plan_follows_path.py` | 16 | 6 | see census |
| `test_reference_gate_imports.py` | 17 | 6 | see census |
| `test_ro1_availability_reads.py` | 21 | 6 | see census |
| `test_router_g1_feasibility.py` | 8 | 6 | see census |
| `test_teacher_te1b_review_fixes.py` | 7 | 6 | see census |
| `test_voi_v2.py` | 22 | 6 | see census |
| `test_curriculum_c1_landing.py` | 7 | 5 | see census |
| `test_ih6_workbench_open_item.py` | 37 | 5 | see census |
| `test_ih_lesson_candidate_after_cold_miss.py` | 28 | 5 | see census |
| `test_intent_codex_rereview.py` | 10 | 5 | see census |
| `test_ro0_rows9_13_decision_state.py` | 13 | 5 | see census |
| `test_router_presentations.py` | 6 | 5 | see census |
| `test_router_r2a_serving.py` | 10 | 5 | see census |
| `test_router_r2bc_landing.py` | 6 | 5 | see census |
| `test_router_r2c_retrieval.py` | 8 | 5 | see census |
| `test_ih4_preferences_inform_router.py` | 34 | 4 | see census |
| `test_pr4_superseded_claims_landing.py` | 4 | 4 | see census |
| `test_ro0_gate.py` | 5 | 4 | see census |
| `test_ro4_objective_serving.py` | 6 | 4 | see census |
| `test_ro6_serving.py` | 5 | 4 | see census |
| `test_rospeed2_connections.py` | 8 | 4 | see census |
| `test_router_probe_ties.py` | 9 | 4 | see census |
| `test_router_r1_composition.py` | 8 | 4 | see census |
| `test_router_r2a_landing.py` | 4 | 4 | see census |
| `test_sg_slip_vs_gap.py` | 24 | 4 | see census |
| `test_te3b_codex_review.py` | 9 | 4 | see census |
| `test_teacher_te1b_rereview_fixes.py` | 5 | 4 | see census |
| `test_teacher_te2_lessons.py` | 13 | 4 | see census |
| `test_followups_batch6_te1b_card.py` | 3 | 3 | see census |
| `test_forecast_receipts.py` | 17 | 3 | see census |
| `test_ih2_lessons_compete.py` | 40 | 3 | see census |
| `test_ih3_learner_preferences.py` | 16 | 3 | see census |
| `test_ih7_lesson_sources_follow_diagnosis.py` | 44 | 3 | see census |
| `test_map_untested.py` | 3 | 3 | see census |
| `test_reader_recap_review.py` | 4 | 3 | see census |
| `test_reader_recap_review_r3.py` | 5 | 3 | see census |
| `test_reader_rw4b_fix6.py` | 4 | 3 | see census |
| `test_reader_rw5d_p4b_teacher_visuals.py` | 21 | 3 | see census |
| `test_ro1_interval_factor.py` | 7 | 3 | see census |
| `test_ro4_goals.py` | 4 | 3 | see census |
| `test_ro6_landing.py` | 4 | 3 | see census |
| `test_router_card.py` | 9 | 3 | see census |
| `test_router_g7_fallback.py` | 3 | 3 | see census |
| `test_router_r2b_agreement.py` | 3 | 3 | see census |
| `test_sidecar_knowledge_model.py` | 4 | 3 | see census |
| `test_te3a_lesson_opportunity.py` | 16 | 3 | see census |
| `test_teacher_te0_confidence_events.py` | 3 | 3 | see census |
| `test_teacher_te0_review_fixes.py` | 3 | 3 | see census |
| `test_why_reader.py` | 5 | 3 | see census |
| `test_ad2_serving.py` | 2 | 2 | see census |
| `test_curriculum_c1_codex_review_fixes.py` | 9 | 2 | see census |
| `test_diagnosis_pipeline.py` | 2 | 2 | see census |
| `test_evsi_staged_binding.py` | 2 | 2 | see census |
| `test_followups_batch6_review_fixes.py` | 2 | 2 | see census |
| `test_intent_codex_review.py` | 25 | 2 | see census |
| `test_intent_fix_round4.py` | 30 | 2 | see census |
| `test_probe_robust_cutover.py` | 7 | 2 | see census |
| `test_reader_guidance.py` | 9 | 2 | see census |
| `test_reader_rw3a_landing.py` | 5 | 2 | see census |
| `test_reader_rw4b_admission_idempotency.py` | 5 | 2 | see census |
| `test_reading_paths.py` | 48 | 2 | see census |
| `test_ro0_codex_review.py` | 14 | 2 | see census |
| `test_ro1_availability.py` | 7 | 2 | see census |
| `test_ro4_codex_review.py` | 6 | 2 | see census |
| `test_ro5_landing.py` | 10 | 2 | see census |
| `test_ro6_tail_data.py` | 6 | 2 | see census |
| `test_rofu_learning.py` | 5 | 2 | see census |
| `test_router_g3_propensity.py` | 2 | 2 | see census |
| `test_sim_probe_validation.py` | 1 | 2 | see census |
| `test_teach_back.py` | 3 | 2 | see census |
| `test_teacher_te2log_episodes.py` | 23 | 2 | see census |
| `test_teacher_te2log_node_held.py` | 5 | 2 | see census |
| `test_ux_phase4_landing.py` | 5 | 2 | see census |
| `test_voi_merge_composition.py` | 8 | 2 | see census |
| `test_active_errors_overlay.py` | 1 | 1 | see census |
| `test_ad23_fix_r5.py` | 1 | 1 | see census |
| `test_ad3_relatedness.py` | 1 | 1 | see census |
| `test_arcb_close_fixes.py` | 5 | 1 | see census |
| `test_assessment_contracts.py` | 5 | 1 | see census |
| `test_curriculum_c1_fix_round2.py` | 13 | 1 | see census |
| `test_curriculum_c1_fix_round3.py` | 9 | 1 | see census |
| `test_daily_plan_kill_switch.py` | 1 | 1 | see census |
| `test_decider_landing.py` | 7 | 1 | see census |
| `test_diagnosis_async_router.py` | 2 | 1 | see census |
| `test_diagnosis_card.py` | 1 | 1 | see census |
| `test_exam_protection.py` | 1 | 1 | see census |
| `test_exam_protection_review.py` | 1 | 1 | see census |
| `test_exam_session.py` | 3 | 1 | see census |
| `test_figure_wait_estimate.py` | 1 | 1 | see census |
| `test_followup_generate_e2e.py` | 11 | 1 | see census |
| `test_followup_journey.py` | 19 | 1 | see census |
| `test_followup_live_shape.py` | 8 | 1 | see census |
| `test_followup_next_matrix.py` | 71 | 1 | see census |
| `test_followup_rival_factor.py` | 22 | 1 | see census |
| `test_followup_router.py` | 15 | 1 | see census |
| `test_followup_workflow.py` | 10 | 1 | see census |
| `test_followups_batch5_recap_protection.py` | 7 | 1 | see census |
| `test_followups_batch6_router_report.py` | 2 | 1 | see census |
| `test_generated_item_gate.py` | 3 | 1 | see census |
| `test_hot_path_eligibility_cutover.py` | 3 | 1 | see census |
| `test_ih2_offer_ceiling_and_unseen.py` | 23 | 1 | see census |
| `test_instrument_servability_journeys.py` | 1 | 1 | see census |
| `test_intent_fix_round6.py` | 44 | 1 | see census |
| `test_intent_plan.py` | 11 | 1 | see census |
| `test_measurement_corrections.py` | 2 | 1 | see census |
| `test_method_explicit_landing.py` | 2 | 1 | see census |
| `test_mobile_v3_probes.py` | 9 | 1 | see census |
| `test_placement_sidecar.py` | 8 | 1 | see census |
| `test_probe_episodes.py` | 2 | 1 | see census |
| `test_probe_targeting.py` | 4 | 1 | see census |
| `test_quick_check.py` | 19 | 1 | see census |
| `test_reader_recap_review_r2.py` | 2 | 1 | see census |
| `test_reader_workbench_rw2a.py` | 58 | 1 | see census |
| `test_reading_step_switch.py` | 1 | 1 | see census |
| `test_recall_coverage_interventions.py` | 1 | 1 | see census |
| `test_refusal_records.py` | 6 | 1 | see census |
| `test_remaining_decision_records.py` | 4 | 1 | see census |
| `test_ro0_codex_verify.py` | 16 | 1 | see census |
| `test_ro0_row10_cold_timing.py` | 3 | 1 | see census |
| `test_ro1_self_report.py` | 3 | 1 | see census |
| `test_ro5_calibration.py` | 4 | 1 | see census |
| `test_ro5_picks.py` | 3 | 1 | see census |
| `test_ro5_stop_coin.py` | 3 | 1 | see census |
| `test_ro6_codex_rereview.py` | 2 | 1 | see census |
| `test_rofu_ad_link.py` | 3 | 1 | see census |
| `test_rofu_carried.py` | 5 | 1 | see census |
| `test_rofu_monotone.py` | 3 | 1 | see census |
| `test_rofu_review_draw.py` | 3 | 1 | see census |
| `test_rofu_speed.py` | 3 | 1 | see census |
| `test_roles_switch_off.py` | 1 | 1 | see census |
| `test_rospeed_ad_link.py` | 1 | 1 | see census |
| `test_router_r2b_requests.py` | 1 | 1 | see census |
| `test_router_r2c_teach_back.py` | 6 | 1 | see census |
| `test_rw5c_switch_off.py` | 1 | 1 | see census |
| `test_rw7b_fix_round2.py` | 5 | 1 | see census |
| `test_serve_eligibility_review.py` | 23 | 1 | see census |
| `test_sidecar_contract.py` | 1 | 1 | see census |
| `test_source_first_needs.py` | 17 | 1 | see census |
| `test_source_set_synthesis.py` | 1 | 1 | see census |
| `test_te3b_clock.py` | 1 | 1 | see census |
| `test_te3b_features.py` | 1 | 1 | see census |
| `test_te3b_offers.py` | 9 | 1 | see census |
| `test_te3b_population.py` | 2 | 1 | see census |
| `test_teacher_exam_question_guard.py` | 33 | 1 | see census |
| `test_teacher_te1_lesson.py` | 17 | 1 | see census |
| `test_teacher_te2_sidecar.py` | 2 | 1 | see census |
| `test_teacher_te2log_report.py` | 4 | 1 | see census |
| `test_today_headline.py` | 1 | 1 | see census |
| `test_unresolved_cause_gate.py` | 6 | 1 | see census |
| `test_ux_phase2_error_type_proposals.py` | 1 | 1 | see census |
| `test_value_candidates.py` | 3 | 1 | see census |
| `test_why_cases.py` | 2 | 1 | see census |

### D7 (switch tests)

None moved behind a switch in this step; the experiment did not separate a failure caused by a kill switch's predecessor path from one caused by an old tag's gate. D2b part 2a's list stands (`test_learner_pick_proposal`, the 21 `RANDOMIZED_CHECKS_OFF` tests).

### Predecessor arms that stay

`test_ad2_serving` (`mvp-0.29` arms of the generation-contract and selection-switch tests), `test_ad23_fix_r5` (`mvp-0.29` predecessor copy), `test_ad3_relatedness` (`mvp-0.29`): the predecessor is the subject; their other arms run at the head now. D6 (adaptive difficulty's tag gate).

## 7. Helper changes

- `tests/ad23_fakes.py`: `SUCCESSOR` is `LATEST_ALGORITHM_VERSION` (was `mvp-0.30`); `ad23_vault` appends `RANDOMIZED_CHECKS_OFF`.
- `tests/ad_fakes.py`: `ad_plan_vault`'s default tag is the head (was `mvp-0.22`) and it appends `RANDOMIZED_CHECKS_OFF`.
- 56 test and helper files edited by the script of §1 (list: `git diff --stat` of the second commit).

## 8. Open items

- The re-tag-pending files (§3) and the mixed files' re-taggable tests: a next part of this step. The recount plugin and the experiment plugin are scratch files, not committed; D1's description of the plugin is enough to rebuild the first, and the second is five lines (patch `_set_algorithm_version_at` and `pin_old_basic_vault`).
- Files that use `create_daily_plan_vault` or `plan_world` were not skipped by name (the d21 sweep's list was not given to me); none of the edits above touched a draw.
- Not run: the landing selection, the durability lane, `--fresh-connections`, vitest, the vault regeneration and its validators, `test_structure_ratchets`. See the report.


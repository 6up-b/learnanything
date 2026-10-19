# Adaptive difficulty AD2+AD3: Codex review and fix round

Stage `adaptive-difficulty-ad23`, branch `adaptive-difficulty/ad23`, worktree
`learnanything-ad1`. Codex reviewed the stage at `8f86cd81f` (codex-job
`20261019-014237-2Hta6W`): one High and eight Medium findings. This round
fixes all nine in commit `a8f9053de`. Each fix has a test in
`tests/test_ad23_fix_review.py`, and F6 also has two vitest files.

No model calls were made: no paid or live calls, and no smoke runs on a vault
copy. Every model-backed path is tested with fakes. F5's generator is a
`StructuredClientFake` behind the real durable job queue.

## Review

### Findings

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Frozen inputs allow wholly unassessed attempts to train AD | fixed | `a8f9053de` | `test_a_wholly_unassessed_frozen_attempt_trains_nothing_and_tests_no_cell`: a real PF-c submission through `complete_attempt_with_ai_required`, bound to a presentation whose serve froze its inputs. On the old tree it trained as eligible. `test_a_partly_unverified_frozen_attempt_reads_its_assessed_grade` is the control |
| F2 | Medium | Nonempty "I'm stuck" answers are always treated as failures | fixed | `a8f9053de` | `test_a_stuck_answer_is_forced_to_fail_only_when_empty` (4 cases), `test_an_i_dont_know_answer_still_fails_whatever_its_grade` |
| F3 | Medium | Cache fingerprints miss changes to replay inputs | fixed | `a8f9053de` | `test_the_live_cache_follows_replacements_updates_and_other_connections`. It covers the init-wizard delete-and-insert (count and max rowid unchanged), an in-place update and a quarantine, each written from another connection and each checked against an uncached replay |
| F4 | Medium | Selection runs before recent reading enters the state | fixed | `a8f9053de` | `test_a_draw_reads_reading_recorded_since_the_last_serve`: a worked example studied between presentations, with no sweep run by hand. The selection's state hash and the serve receipt's must both include it |
| F5 | Medium | Serve-time commissions never launch generation | fixed | `a8f9053de` | `test_a_serve_commission_queues_its_generation_once_at_its_point` (the real `DurableIngestJobs` queue, foreground, with a fake generator), `test_the_sidecar_queues_a_serve_commission_after_the_serve` (the plan's serve RPC) |
| F6 | Medium | The extra-question offer can repeat the ordinary quick check | fixed | `a8f9053de` | `test_the_offer_names_the_sections_other_question_and_its_answer_is_the_extra` (two questions; the RPC returns the other one; answering it records the opportunity naming the offer). Vitest: `ReaderScreen.doseOffer.test.tsx` (the real screen with two questions) and `DoseOffer.test.tsx` |
| F7 | Medium | The grid comparator leaks future answers into earlier predictions | fixed | `a8f9053de` | `test_the_grid_arm_never_reads_a_later_answer`: appending or changing later outcomes leaves earlier `:grid` forecasts unchanged |
| F8 | Medium | Two monitoring conditions cannot fire through the production report | fixed | `a8f9053de` | `test_readiness_errors_read_each_report_window`, `test_repeated_reports_fire_the_readiness_flag_through_build`, `test_density_lowerings_join_offers_to_their_visits` (real `ad_dose_offers` and `interaction_events` rows through `build`) |
| F9 | Medium | An LO can say "likely ready" while required cells remain untested | fixed | `a8f9053de` | `test_a_partly_untested_lo_never_reads_likely_ready` |

**Fail-first.** 16 of the 17 Python tests fail on the old tree. To check
this, the 12 changed `src/` files were replaced by their `8f86cd81f`
versions, the new test file was run, and the files were restored. The 17th
test is F1's control (`..._reads_its_assessed_grade`), and it passes on both
trees. Two kinds of failure appear:

- **The behaviour itself.** F1, F3, F4, F5 (both tests) and F6 fail on their
  assertions.
- **A missing helper.** The tests for F2 (`forced_failure`), F7 (`_GridArm`),
  F8 (`readiness_errors`, `density_lowerings` and `report_every`) and F9
  (`aggregate_line`) fail because the helper does not exist on the old tree.
  Codex reproduced the behaviour behind each of these in memory, and every
  helper exists only to make that behaviour testable.

`ReaderScreen.doseOffer.test.tsx` fails on the old frontend: the draw never
named `showingQuestionId`.

### What changed

- **F1.** `field.outcomes` gains the shared PF-c helpers
  (`current_criterion_evidence`, `unverified_criterion_ids`,
  `wholly_unassessed`); field's loader now uses them, a refactor with no
  behaviour change. It also gains `measurement_masses`, an attempt's
  effective mass without its item-dependent (familiarity) and assistance
  discounts. That is field's `mass_without_assistance` without familiarity.
  `replay.load_events` resolves both from the authoritative ledger alone,
  for every attempt, frozen inputs or not. A wholly unverified attempt is
  excluded as `unassessed`; a grade that measures nothing is excluded as
  `zero_mass`. Neither trains or marks a cell tested, but both still close
  reading windows (§5.6). Hints and reveals are not discounted here: §5.3
  categorizes them. The current grade is field's rule: the latest surviving
  row of each criterion.
- **F2.** `replay.forced_failure`: only an empty stuck submission, or an "I
  don't know" answer, is category 0 whatever its grade. A nonempty stuck
  answer is classified by its correctness and help timing.
- **F3.** The cache key is now the sha256 of the events the replay reads:
  the attempts with their frozen inputs, the claims, the opportunities, the
  relatedness structure and the vault maps. It is no longer each table's
  `COUNT(*)` and `MAX(rowid)`. Every input reaches the replay through
  `load_events`, so a cached snapshot is exactly an uncached replay of the
  same events. The cache now saves only the filter over the events. On the
  stage's test vaults (10 eligible of 210 attempts), reading the events took
  8 to 19 ms and the filter 4 to 5 ms.
- **F4.** `serving.decide_slot` sweeps reading opportunities through the
  decision instant, in the serve transaction, before it scores the support.
  The sweep is tagged `sweep = 'serve'` with `sweep_ref` set to the decision
  key. The serve hook's own sweep, at the same instant, then finds nothing
  new. As in the serve hook, a failed sweep is logged and never blocks the
  draw.
- **F5.**
  - `generation.schedule_commission_generation` hands each open
    serve-time commission (`decision_key` containing `:serve:`) to an
    enqueue callable. Commissions that the generation path drew for itself
    are generated by that path already.
  - The sidecar's `_schedule_ad` calls it after each plan read and serve,
    before the AD1 background switches are checked. It enqueues through
    `ctx.ingest_jobs.enqueue_practice_expansion(..., ad_commission_id=...)`.
    A test can inject `ctx.ad_commission_enqueue`. With
    `LEARNLOOP_AD_MODELS=off` and nothing injected, nothing is queued.
  - The batch id is `batch_ad_commission_<selection id>`, so a commission is
    generated once however often scheduling runs. A crash between the serve
    and the enqueue is recovered by the next call.
  - The job (`jobs._handle_ad_commission`) is a no-op if the commission has
    landed or the contract is off. Otherwise it runs
    `generate_post_probe_practice_proposal` with `max_new_per_lo = 1` and
    the commission id. `build_practice_expansion_plan` and
    `commission_point` then write the target at that commission's own point
    and capability, rather than drawing a new commission.
  - Spend, fencing, the rung, surface, persona and pair gates, and the
    review policy are the generation path's own. The landed item gets its
    §7.4 receipt at a later serve, as before.
- **F6.**
  - The `reader.dose_offer` RPC adds `offer.question` to an
    `extra_question` offer: the chosen question's id, prompt, expected
    answer and spans, read at response time. Nothing more is persisted.
  - `ReaderScreen` passes the completed section's ordinary check as
    `showingQuestionId`, so the backend excludes it from the support. This
    exclusion already existed.
  - On "yes", `DoseOffer` shows that exact question in the quick-check card
    (`AuthoredQuestionCard`, now exported) rather than reopening the
    section's check. Answering it calls `reader.authored_question_action` on
    the delivered id, and its reading opportunity names the offer.
- **F7.** `arms._GridArm` runs inside the base run's observer. Before each
  attempt it reads the shared means from the subject view as it stands. The
  separate full-history replay is gone.
- **F8.**
  - `report.readiness_errors` gives the band-region error of
    `@subject` at each report: one report at each multiple of 200 AD
    selections (§10.4: "reported every 200 AD selections"), scored on the
    prequential records up to that selection, then this run.
  - `build` derives `previous_errors` from these by default. A test can
    still pass them explicitly.
  - `report.density_lowerings` reads `cue_density_changed` events to a lower
    density. One counts when it falls after a delivered extra offer and no
    later than the end of that offer's visit (its close, else its last
    visit-carrying event), on the same source when the event names one.
    `build` passes these to the burden flag.
- **F9.** `readiness.aggregate_line`: "likely ready" only when every cell is
  tested and likely. A partly untested LO reads "not yet likely (a
  prediction; k of n parts untested)".

### Behaviour changes worth knowing

- **F1.** Historical attempts at a P0 version that have no interpretation
  have zero reliable mass (`missing_interpretation`, §4.3). They are now
  excluded from AD as `zero_mass`, as field already excludes them. The
  stage's self-graded and blind-graded test attempts all carry an
  interpretation, at mass 1.0.
- **F2.** A stuck learner's nonempty, correct answer can now be an
  unassisted success (category 2), when no help came before work.

### Not addressed here (outside the nine findings)

The review's conformance table also lists gaps that no finding names. This
round does not take them on, so as not to widen the stage:

- ranked probability scores, skip-rate deciles and the fixed-share or
  stacking ensembles (§8);
- `learnloop eval` integration (§10.4);
- the glass-box monitoring and "What helps you" lines (§12);
- per-candidate feature and signal provenance in the selection support;
- the §14 simulation gates, whose failures `adaptive-difficulty-ad23.md`
  already discloses.

### Open questions for the owner

1. **F8 report history.** The readiness flag's "two consecutive reports"
   is read as deterministic report windows, one per 200 AD selections
   (§10.4), recomputed from the prequential records. The report stays a pure
   read with no history table. The alternative is a persisted report-run
   history, which needs a table. Accept the windows, or ask for persistence?
2. **F5, a commission whose generation fails or is rejected.** The
   commission stays open, so §6.1's "at most one open per cell" suppresses
   further commissions for that cell. The job runs once per commission, which
   bounds spend. Should an unlanded commission expire, for example after its
   job has finished plus N days, so that a fresh one can be drawn? A
   generated item routed to review lands only after it is accepted.
3. **F8, density lowerings.** These are matched to a visit by time, because
   `cue_density_changed` events carry no `visit_id`. Should the Reader send
   the visit with the preference change?

## Gate (this fix step)

The owner rule of 2026-10-17 applies: targeted tests only. The full suite,
the whole durability lane and the whole vitest run happen once, in the
landing gate.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 27 kept, 0 broken |
| `tests/test_ad23_fix_review.py` alone, before the commit | 17 passed |
| targeted pytest, run 1: `uv run pytest -n auto` over 133 files (below) | **8,134 passed, 36 xfailed** (820.9 s) |
| targeted pytest, run 2: the stage's other 115 affected files (its 186-file list, less run 1) | **2,583 passed** (472.1 s) |
| after the final comment and import tidy: `test_ad23_fix_review.py`, `test_ad2_model.py`, `test_ad3_subject_view.py` | 48 passed |
| `npm install`, `npm run typecheck` | ok, 0 errors |
| vitest: `src/screens/ReaderScreen*` and `src/screens/reader/*` | **49 files, 373 passed** |
| vitest after the typecheck fix: `ReaderScreen.doseOffer.test.tsx`, `DoseOffer.test.tsx` | 2 files, 6 passed |
| `npm run frontend:build` | built |
| durability lane, `cargo check`, DB reference scripts | not applicable: no migration, DB or connection code, `src-tauri` or schema change |
| CLI help, RPC contract, serializer, mobile allowlist, config defaults, table roles, coordinated migrations, tracked fixture databases | in run 1, passed |

Two runs needed a second look:

- **vitest under load.** A first run of the Reader vitest set, made while
  pytest ran in parallel, failed 10 timing-bound tests in `inquiry`,
  `parity`, `pdfSelection`, `recap` and `review`. Run alone,
  `pdfSelection` passed and `recap` passed three times in a row. The whole
  set then passed, 373 of 373, once pytest had finished.
- **`desktop_validate.py`.** This architecture-vault script, run as a
  courtesy and not part of this gate, fails on
  `apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticBook.ts`,
  a file from `b1087be0a` that this stage did not touch.

`tests/test_ad23_fix_review.py` (17 tests) is untracked until the commit, so
`git grep` did not put it in run 1. It ran on its own before the commit (17
passed) and again in the final three-file run (48 passed).

**Run 1's 133 files** (`git grep` for the changed modules and functions, plus
the contract tests): test_ad1_attempt_columns.py, test_ad1_codex_rereview_fixes.py, test_ad1_codex_review_fixes.py, test_ad1_fix_round4.py, test_ad1_fix_round5.py, test_ad1_fix_round6.py, test_ad1_fix_round7.py, test_ad1_fix_round8.py, test_ad1_fix_round9.py, test_ad1_migration.py, test_ad1_outside_and_cli.py, test_ad1_reading_opportunities.py, test_ad1_send_guard.py, test_ad23_migration.py, test_ad23_sim.py, test_ad23_successor.py, test_ad2_model.py, test_ad2_serving.py, test_ad3_dose_arm.py, test_ad3_monitoring.py, test_ad3_reading.py, test_ad3_relatedness.py, test_ad3_subject_view.py, test_adaptive_difficulty_ad1.py, test_answer_signal_arms.py, test_architecture.py, test_assumed_known.py, test_attempt_completion.py, test_causal_attribution_p0.py, test_chatgpt_plan_workspace.py, test_cli_help_snapshot.py, test_config_refactor.py, test_contract_commissioning.py, test_coordinated_migrations.py, test_daily_plan_composition.py, test_daily_plan_kill_switch.py, test_daily_plan_owner_decisions.py, test_daily_plan_reading.py, test_daily_plan_reentry.py, test_daily_plan_review_regressions.py, test_daily_plan_rpc.py, test_decider_landing.py, test_desktop_rpc_contract.py, test_difficulty_band_guards.py, test_eval_harness.py, test_exam_protection.py, test_exam_protection_review.py, test_facet_diagnostics_v03.py, test_facet_outcome_view.py, test_family_evaluation.py, test_family_memory_projection.py, test_field_boundaries.py, test_field_cli.py, test_field_priors.py, test_field_signal_production_paths.py, test_field_split_outcomes.py, test_glm_ocr.py, test_goal_scope_material.py, test_held_grade_composition.py, test_import_split_parity.py, test_ingest_instrument_gates.py, test_ingestion_checkpoints.py, test_ingest_jobs.py, test_ingest_latency_journey.py, test_ingest_m3.py, test_ingest_ownership.py, test_ingest_queue_store.py, test_ingest_runner.py, test_ingest_transcripts.py, test_integration_daily_loop_field.py, test_interaction_signals.py, test_inventory_runner_mailbox.py, test_keep_local_retired.py, test_learner_text_gaps_composition.py, test_learner_text_gaps.py, test_learner_text_gaps_rereview.py, test_learner_text_gaps_review.py, test_lo_general.py, test_mobile_allowlist.py, test_persona_gate.py, test_pfc_unassessed_readers.py, test_pfc_unverified_unassessed.py, test_placement_signals.py, test_placement_split_grades.py, test_plan_determinism.py, test_practice_item_quality_gates.py, test_practice_leakage.py, test_predictor_interface.py, test_probability_arms.py, test_probability_prep.py, test_provider_resolution_parity.py, test_quick_add.py, test_quick_check.py, test_reader_active_reading.py, test_reader_observation_records.py, test_reader_passage_check.py, test_reader_progression.py, test_reader_reconnect.py, test_reader_rw1b_review.py, test_reader_rw3a_landing.py, test_reading_hardening_2_fixes.py, test_reading_hardening_landing.py, test_reading_hardening_review_fixes.py, test_reading_hardening_verify_fixes.py, test_reading_request_sweep.py, test_rebuild_orchestrator.py, test_recall_coverage_interventions.py, test_recurrence_merge_composition.py, test_reread_safety.py, test_router_r1_composition.py, test_router_r2a_serving.py, test_router_r2bc_landing.py, test_router_r2b_serving.py, test_rw1a_composition.py, test_salience_firewall.py, test_shadow_rebuild.py, test_sidecar_animation.py, test_sidecar_serializer_snapshot.py, test_source_exercise_rpcs.py, test_sqlite_file_copies.py, test_stuck_prompt.py, test_stuck_prompt_replay.py, test_success_head_cli.py, test_success_head.py, test_table_roles.py, test_tier1_decider.py, test_tracked_fixture_databases.py, test_tutor_promotion_w2.py, test_ux_phase1_auto_build.py, test_ux_phase1_connect_ai.py, test_ux_phase1_finish.py, test_ux_phase1_landing.py, test_ux_phase1_review_fixes.py.

**Run 2's 115 files** (the stage's 186-file list in
`adaptive-difficulty-ad23.md`, less those in run 1): test_ai_config.py, test_ai_tool_isolation.py, test_approach_map_replay.py, test_approach_maps_schema.py, test_block_chooser_interface.py, test_card_lineage.py, test_chatgpt_plan_provider.py, test_constraint_engine.py, test_daily_plan_build.py, test_daily_plan_replay.py, test_decider_client.py, test_diagnosis_context.py, test_diagnosis_history_modes.py, test_diagnosis_input_provenance.py, test_diagnosis_replay.py, test_diagnostic_pack.py, test_embedding_store.py, test_evsi_router_composition.py, test_evsi_staged_binding.py, test_exam_protection_landing.py, test_facet_identity_actions.py, test_field_config.py, test_forecast_receipts_landing.py, test_forecast_receipts.py, test_grading_cli.py, test_held_grade_evidence.py, test_help_assists_schema.py, test_hint_feedback_widening.py, test_hint_telemetry.py, test_intervention_outcomes_replayer.py, test_item_fingerprints.py, test_judge_routes.py, test_kinship_feature.py, test_km2_activation.py, test_learner_pick_proposal.py, test_learner_text_gaps_flow.py, test_learner_text_source_widening.py, test_library_ask.py, test_library_asks_migration.py, test_mcp_c1a_landing.py, test_mcp_c1a_narrow.py, test_mcp_tools.py, test_method_explicit_landing.py, test_method_explicit_upgrade.py, test_migrations.py, test_mvp010_upgrade.py, test_mvp011_upgrade.py, test_mvp013_upgrade.py, test_mvp014_upgrade.py, test_mvp015_upgrade.py, test_mvp016_upgrade.py, test_mvp017_route_check_replay.py, test_mvp017_upgrade.py, test_mvp018_upgrade.py, test_mvp020_upgrade.py, test_mvp021_upgrade.py, test_mvp022_upgrade.py, test_mvp023_upgrade.py, test_mvp024_upgrade.py, test_mvp09_upgrade.py, test_openai_embedding_client.py, test_open_world_gate.py, test_p0_cutover_mvp08.py, test_p3_journeys.py, test_plan_determinism_landing.py, test_practice_index_dossiers.py, test_probability_cli.py, test_project_cli.py, test_project_experiment_store.py, test_project_probes.py, test_project_report.py, test_randomization_layer.py, test_reader_activity.py, test_reader_authoring.py, test_reader_cues.py, test_reader_dialogue.py, test_reader_formative_texts.py, test_reader_intent.py, test_reader_recap_review_r3.py, test_reader_reconstruct.py, test_reader_restoration.py, test_reader_workbench_rw2a.py, test_reading_step_switch.py, test_recurrence_commands.py, test_recurrence_live.py, test_registry_audit.py, test_regrade_contract_replay.py, test_regrade_contract_successor.py, test_regrade_contract_upgrade.py, test_required_method_authority.py, test_required_method_grading.py, test_reread_safety_landing.py, test_router_card.py, test_router_coldness_covariates.py, test_router_g1_feasibility.py, test_router_g4_restraint.py, test_router_g7_fallback.py, test_router_offer_log.py, test_router_outcomes.py, test_router_presentations.py, test_router_r2a_landing.py, test_router_r2c_retrieval.py, test_router_r2c_teach_back.py, test_route_rules_in_grader.py, test_router_why_copy.py, test_sensitivity_certificates.py, test_serve_eligibility.py, test_serve_eligibility_review.py, test_source_block_fts.py, test_sqlite_wal_lifecycle.py, test_ux_phase4_feedback.py, test_ux_phase4_landing.py, test_voi_merge_composition.py, test_voi_stopping.py, test_voi_v2.py.

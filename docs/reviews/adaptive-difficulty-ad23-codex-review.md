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
   **Owner decision 2026-10-19:** "F8. Readiness's "two consecutive reports" uses deterministic report windows (one per 200 AD selections), with no history table. Accepted as built; just record the decision." Recorded; no code change (the spec's §10.4 flag table now says so).
2. **F5, a commission whose generation fails or is rejected.** The
   commission stays open, so §6.1's "at most one open per cell" suppresses
   further commissions for that cell. The job runs once per commission, which
   bounds spend. Should an unlanded commission expire, for example after its
   job has finished plus N days, so that a fresh one can be drawn? A
   generated item routed to review lands only after it is accepted.
   **Owner decision 2026-10-19:** "F5. An unlanded commission (its generation failed or was rejected) EXPIRES 7 days after its job finished, so a fresh one can be drawn for that cell. Keep "at most one open per cell". A commission routed to review stays open while its item is in review. Add tests." Done in the final round below (`ad_serving.open_commissions`, three tests).
3. **F8, density lowerings.** These are matched to a visit by time, because
   `cue_density_changed` events carry no `visit_id`. Should the Reader send
   the visit with the preference change?
   **Owner, 2026-10-19:** not in scope here. **Follow-up for a Reader stage:** the Reader sends the
   visit id with the cue-density change, and the burden flag joins on it instead of on time.

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

## Re-review

Codex re-reviewed the fix round at `9854531f0` (codex-job
`20261019-024319-NFrlqi`, verdict REOPENED). It confirmed F2-F7 and F9 as
fixed, reopened F1 (High) and F8 (Medium), and raised one new Medium finding,
F10. This round fixes F1 and F10 and rejects the reopened F8 with its reason,
in commit `eb52b613f`. The regressions are in `tests/test_ad23_fix_review.py`.
No model calls were made: no paid or live calls, and no smoke runs. F10's
generator is a `StructuredClientFake` behind the production client seam
(`jobs.default_synthesis_client`, monkeypatched), so even the old tree's
failure made no call.

### Findings

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | The PF-c check merges criteria across grading epochs instead of reading the current epoch | fixed | `eb52b613f` | `test_a_historical_regrade_reads_its_current_epoch_not_a_surviving_obsolete_criterion`: a frozen-input attempt whose first grade (revision 0) verified `c_obsolete` and whose later revision-less regrade dropped it and left every criterion unverified. On the old tree it trained as eligible |
| F2-F7, F9 | Medium | (confirmed fixed by the re-review) | fixed | `a8f9053de` | confirmed by Codex; their tests still pass (below) |
| F8 | Medium | The readiness flag has no persisted report history | rejected | n/a | The spec defines the report's cadence itself, at §10.4: "reported every 200 AD selections (`learnloop ad report`)". A report is therefore a 200-selection window. Two runs of the command at 100 selections are one report read twice, not two consecutive reports, and by the spec no report is due yet. A history of invocations would make the flag fire on how often the owner runs the CLI: two runs a minute apart would count as "two consecutive reports". It would also add a table to migration 214. The windowed reading is the spec's own text, and the owner has accepted the specs' recorded defaults (2026-10-12). It stays open question 1 below, so the owner can override it at the checkpoint |
| F10 | Medium | Queued commissions bypass the models-off switch | fixed | `eb52b613f` | `test_a_commission_queued_before_models_go_off_waits_and_resumes`: enqueued with models on, drained with `LEARNLOOP_AD_MODELS=off`, then resumed. On the old tree the handler resolved the production client with models off |

**Fail-first.** Both new tests fail on the tree at `9854531f0`. The F1 test
fails on `not event.eligible`, because the attempt trained. The F10 test fails
on `resolved == []`, because the client seam was called once with
`LEARNLOOP_AD_MODELS=off`. Both pass after the fix.

### What changed

- **F1.** `replay.load_events` resolves the attempt's current grading epoch
  with `grading_epochs.current_epoch`, the rule the canonical projection reads
  at the regrade-contract successor. It then applies PF-c's
  `wholly_unassessed` to that epoch's rows only. AD runs only from its own
  successor, which is past mvp-0.26, so the epoch rule always applies.
  `field.outcomes.current_criterion_evidence`, field's own per-criterion
  merge, is unchanged. Field's loader keeps its pre-existing rule; see open
  question 4.
- **F10.**
  - `jobs._handle_ad_commission` rechecks `models_off()` after the contract
    and open-commission checks and before it resolves a client. Only an
    explicitly injected `synthesis_client_factory` (a test's fake) may run
    with models off; production never sets one.
  - With models off, the job fails retryable with code `ad_models_off`
    (`jobs.AD_MODELS_OFF_CODE`) and the message "Adaptive difficulty's
    models are off, so this question waits until they are back on." It does
    not complete, so the commission stays open and its batch can be resumed.
  - `DurableIngestJobs.enqueue_practice_expansion`, called by the scheduler
    after each serve, finds the commission's batch waiting on that code. With
    models on it resumes the batch (`resume_batch` requeues the failed job);
    with models off it leaves the batch as it is.
  - The commission's item is still generated once. A completed batch is never
    resumed.

### Open questions for the owner (updated)

1. **F8 report history** (unchanged; the re-review asks for an explicit
   answer). Accept "two consecutive reports" as two consecutive 200-selection
   windows (§10.4), or ask for a persisted report-run history, which needs a
   table and a migration?
   **Owner decision 2026-10-19:** "F8. Readiness's "two consecutive reports" uses deterministic report windows (one per 200 AD selections), with no history table. Accepted as built; just record the decision."
2. and 3. Unchanged from the first round.
4. **Field's PF-c merge (new, out of this stage).** `field.outcomes._load`
   still reads an attempt's grade as the latest surviving row of each
   criterion across every live epoch. This rule predates the stage. AD now
   reads the current epoch. Should field move to `current_epoch` too, as its
   own change, under the algorithm-change playbook?

### Gate (this re-review fix step)

Targeted tests only (owner rule 2026-10-17).

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 27 kept, 0 broken |
| `tests/test_ad23_fix_review.py` alone | 19 passed |
| targeted pytest, `uv run pytest -n auto` over 30 files (below) | **506 passed, 36 xfailed (452.6 s)** |
| durability lane, frontend, `cargo check`, DB reference scripts, snapshots | not applicable: no migration, DB or connection code, `apps/`, schema, config, CLI or RPC change |

**The 30 files** (`git grep` for `load_events`, the replay module,
`schedule_commission_generation`, `ad_commission`, `practice_expansion`,
`enqueue_practice_expansion` and `grading_epochs`, plus the AD suites, the
PF-c readers and the contract tests): test_ad23_fix_review.py, test_ad23_migration.py, test_ad23_successor.py, test_ad23_sim.py, test_ad2_model.py, test_ad2_serving.py, test_ad3_reading.py, test_ad3_subject_view.py, test_ad3_monitoring.py, test_ad3_dose_arm.py, test_ad3_relatedness.py, test_adaptive_difficulty_ad1.py, test_architecture.py, test_characterization_certification_ledger.py, test_contract_commissioning.py, test_ingest_runner.py, test_ingest_jobs.py, test_ingest_queue_store.py, test_reader_progression.py, test_reader_recap_review_r3.py, test_rebuild_orchestrator.py, test_regrade_contract_successor.py, test_sidecar_measurement.py, test_pfc_unverified_unassessed.py, test_pfc_unassessed_readers.py, test_field_split_outcomes.py, test_desktop_rpc_contract.py, test_coordinated_migrations.py, test_table_roles.py, test_tracked_fixture_databases.py.

## Final verify and the owner's decisions (2026-10-19)

Codex's final verify of `9854531f0..3c1a83c58` (codex-job `20261019-030226-tPl9CI`, verdict
REOPENED) confirmed F1 and F10 as fixed, reopened F8 and raised F11. The owner then decided F8, F5,
the history fallback and the failed simulation gates (`adaptive-difficulty-ad23.md` §3.4 and its open
questions 1, 4 and 8). This round applies the decisions and fixes F11. The regressions are in
`tests/test_ad23_owner_decisions.py`. No model calls: fakes only (the generator is a
`StructuredClientFake`; the production client seam is monkeypatched).

| Id | Severity | Title | Verdict | Test or decision |
|---|---|---|---|---|
| F8 | Medium | The readiness flag has no persisted report history | accepted as built | **Owner decision 2026-10-19:** "F8. Readiness's "two consecutive reports" uses deterministic report windows (one per 200 AD selections), with no history table. Accepted as built; just record the decision." |
| F11 | Medium | Automatic commission retry overrides explicit cancellation | fixed | `test_a_cancelled_commission_stays_cancelled_when_models_come_back_on`: queued, failed with `ad_models_off`, cancelled, models back on and the ordinary schedule run twice: the batch stays cancelled, the job failed, no client resolved; only the learner's explicit resume runs it |
| F5 | (open question 2) | An unlanded commission blocks its cell for ever | decided and built | **Owner decision 2026-10-19:** "F5. An unlanded commission (its generation failed or was rejected) EXPIRES 7 days after its job finished, so a fresh one can be drawn for that cell. Keep "at most one open per cell". A commission routed to review stays open while its item is in review. Add tests." Tests: `test_an_unlanded_commission_expires_seven_days_after_its_job_and_a_fresh_one_is_drawn`, `test_a_commission_whose_item_is_in_review_stays_open_until_the_decision`, `test_a_commission_waiting_on_models_stays_open_and_a_cancelled_one_expires` |

**Fail-first.** The six tests of `tests/test_ad23_owner_decisions.py` were run against
`3c1a83c58`'s `src/` and `migrations/` (`git archive` into a scratch directory, `-o pythonpath`
pointing at it): **6 of 6 fail**. F11's test fails on its assertion ("an automatic retry cleared the
learner's cancellation": `cancel_requested` false and the job requeued). The three F5 tests fail
because `open_commissions` takes no time (the old commission is open for ever). The defaults test
fails on `history_fallback`, and the history test on `excluded == reconstructed_current`.

### What changed

- **F11.** `IngestRunner.requeue_failed_unless_cancelled(batch_id, error_code=...)` checks the batch's
  cancellation and requeues the jobs that failed with that code in one `atomic()` transaction, and
  never clears a cancellation. `DurableIngestJobs.enqueue_practice_expansion` uses it for a
  commission's `ad_models_off` job instead of `resume_batch()`. Clearing a cancellation stays with the
  explicit `resume_batch` (the learner's resume).
- **F5.** `ad_serving.open_commissions(connection, *, now=None)`: a commission is open while it has no
  landed result and has neither expired nor been superseded.
  - It expires 7 days (`COMMISSION_EXPIRY_DAYS`) after its generation finished without landing: the
    job completed (nothing landed), failed for any reason other than waiting on models that are off,
    or its batch was cancelled. If a review decision on an item proposed for its LO since the draw
    came later, the 7 days run from that decision.
  - It stays open while its job is not queued, still queued or running, or waiting on the models; and
    while an item proposed for its LO since the draw is in review (a pending `practice_item` creation
    that is not `invalid`).
  - A commission the generation path drew for itself has no job of its own, so its clock starts at
    the draw. (Superseded at fix round 5, F14 below: such a commission names the job it was drawn
    in and its clock starts when that job finished.)
  - It is **superseded** by a later commission for the same cell. The one-open rule allows that only
    after this one closed, so an expiry is never undone, and an explicit resume of an old job finds
    its commission closed (the handler's no-op).
  - Every caller passes its decision time: the serve draw, the generation path, the landing receipts
    and the job handler. The scheduler uses the wall clock. The job's outcome is read through
    `ingest_queue.batch_outcome`, so the queue's SQL keeps its one owner.
- **The defaults** (`adaptive-difficulty-ad23.md` §3.4 and open question 4): `calibrate_below = 0.25`
  (amendment A17); `learned_coupling = false`; `adaptive_difficulty.history_fallback =
  "current_content"`, read by AD's replay and the AD report's field comparators. `field.legacy_fallback`
  stays `"exclude"`, because it also drives the field harness and field's DERIVED facet-outcome view.
  The new key is classified in the parameter registry (decision, constraint; `ENUM_DECISION_LEAVES`).
  The 20 defaults snapshots were recomputed.
- **Density lowerings' `visit_id`** (open question 3): not in scope; recorded as a follow-up for a
  Reader stage, here and in the spec's §10.4.

### Gate (this round; owner rule 2026-10-17: targeted only)

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 27 kept, 0 broken |
| targeted pytest, `uv run pytest -n auto` over 88 files: every `test_ad*` file (`test_ad23_sim.py` included), `test_salience_firewall.py`, the config, registry, defaults-snapshot and CLI/serializer snapshot tests (every file naming `DEFAULTS_SNAPSHOT`, `defaults_fingerprint` or the parameter registry), the content pipeline job tests (`test_ingest_jobs`, `test_ingest_runner`, `test_ingest_queue_store`, `test_question_promotion_jobs`), `test_architecture.py`, `test_mobile_allowlist.py` | **7,149 passed, 36 xfailed, 1 failed** (1,063.9 s). The failure, `test_ingest_queue_store.py::test_ingest_queue_sql_has_one_persistence_owner`, was this round's queue SQL in `ad_serving`; it moved to `ingest_queue.batch_outcome` |
| after that fix: `test_ingest_queue_store`, `test_ad23_owner_decisions`, `test_ad23_fix_review`, `test_ad2_serving`, `test_architecture` | 75 passed |
| and `test_ingest_jobs`, `test_ingest_runner`, `test_ad23_successor`, `test_ad3_subject_view`, `test_ad3_relatedness`, `test_ad2_model`, `test_mobile_allowlist`, `test_registry_audit`, `test_config_refactor` | 397 passed |
| `-m durability tests/test_ad23_migration.py` | 1 passed |
| the 36 xfails | the strict xfails of the failed simulation gates, all still failing at `calibrate_below = 0.25` |
| `python -m learnloop.sim.ad_gates` | re-run at 0.25; figures in `adaptive-difficulty-ad23.md` §3.4 |
| references: `db_generate_reference.py`, `db_validate_reference.py` | 0 errors (927 configuration leaves; the two prose counts updated) |
| CLI help snapshot | unchanged (no command or option changed); `test_cli_help_snapshot.py` passed in the run |
| vitest, `cargo check` | not applicable: no frontend or `src-tauri` change |

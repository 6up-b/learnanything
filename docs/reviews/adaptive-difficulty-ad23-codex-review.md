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

## Fix round 5: the final verify's F12-F15 (2026-10-19)

Codex's verify of the owner-decision round (codex-job `20261019-201825-NEf5k1`, verdict REOPENED)
confirmed F11 as fixed and raised F12 and F13 (High) and F14 and F15 (Medium). This round fixes all
four under the orchestrator's binding rulings R1-R4, in commit `da3def4dd`; the owner decisions of
2026-10-19 stand exactly as recorded above. The regressions are in `tests/test_ad23_fix_r5.py`. No
model calls: fakes only (the generator is a `StructuredClientFake` behind the real durable job queue;
the relatedness proposal is `ProposalLLM`).

| Id | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F11 | Medium | Automatic commission retry overrides explicit cancellation | confirmed fixed by the verify | `1d105282c` | `test_a_cancelled_commission_stays_cancelled_when_models_come_back_on` (still passes) |
| F12 | High | Report forecasts use learned coupling while it is off | fixed (R1) | `da3def4dd` | `test_the_report_forecasts_with_the_configured_coupling` |
| F13 | High | Today retains AD deferrals after the kill switch is off | fixed (R2) | `da3def4dd` | `test_with_selection_off_the_projection_offers_a_once_deferred_item`, `test_with_the_kill_switch_off_today_projects_the_predecessors_blocks` (parity) |
| F14 | Medium | Generation-origin commissions expire before seven days after completion | fixed (R3) | `da3def4dd` | `test_a_generation_jobs_commission_expires_seven_days_after_the_job_finished`, `test_a_commission_drawn_outside_a_job_names_none` |
| F15 | Medium | Expiry prevents recording already-landed commissions | fixed (R4) | `da3def4dd` | `test_an_item_that_landed_before_expiry_gets_its_receipt_at_a_later_serve`, `test_an_item_that_lands_after_expiry_gets_a_marked_receipt_and_a_later_draw_owns_later_items` |

### What changed

- **F12 (R1).** `arms.prequential` replays its base run with `RP.ReplaySettings.from_config(vault.config)`,
  the one function serving's snapshot and the AD replayer already read, and returns those settings;
  `report.build` runs its snapshot (and so the prior sensitivity, which varies the snapshot's
  settings) with them. The ablation arms (`:noread`, `:noverdict`, `:hyper_fine`, `+outside`,
  `+rating`, `+timing`) vary one part of the configured settings. No coupling is hardcoded in the
  report or the arms; no coupling-on what-if was added. The test builds an adopted coupling version
  (an adversarial proposal), four right answers on one LO and a first answer on the related LO: with
  `learned_coupling = false` the report's `ad_threshold@subject` forecast for that answer equals the
  uncoupled replay's (and differs from the coupled one by 0.14 on this case), and every replay the
  report runs is uncoupled; with the switch on it equals the coupled replay's.
- **F13 (R2).** `PlanRecord.exclusion_ids()` holds only the planned and skipped items. AD deferrals
  enter a pool only through the switch-aware context (`engine._context`: `PoolContext.ad_deferred`,
  empty with `selection` off, less what a boundary released); `simulate_blocks` adds the context's
  deferrals to the record's exclusions and nothing else. `PlanRecord.ad_deferrals()` is unchanged (the
  fold from the plan's events, so a rebuild reproduces it; `test_ad2_serving`'s rebuild assertion now
  checks it directly). The verify's scenario (displaced as ineligible, the reveal aged past the delay,
  `selection` off): the projection's first candidate pool contains `pi_a` and equals the base's rule
  (the context's pool less planned and skipped). Parity: on two copies of a vault holding AD draws
  and an `ad_ineligible` displacement, Today's projected blocks (`project_blocks` and the simulated
  items) with `selection = false` equal the predecessor's (`mvp-0.27`), and project `pi_a` again.
- **F14 (R3).** Migration 214 (still this stage's) gains `ad_selections.generating_job_id`
  (TEXT, no foreign key: job rows may be pruned). The generation path's commission draw records the
  durable job running on its thread for this database (`db.scopes.current_ingest_job_id`, read from
  the job runner's existing write guard). `ad_serving._expiry_clock` reads that job through
  `ingest_queue.job_outcome` (the queue's SQL keeps its one owner): queued, running or waiting for
  input keeps the commission open; any terminal state (completed, failed, cancelled) starts the 7 days
  at the job's `finished_at`. A job row that is gone falls back to the draw timestamp (why-comment in
  the store). A commission drawn outside any job (a synchronous generation run, the CLI's) keeps its
  clock at the draw. The review-decision rule (a pending proposal keeps it open; a later decision
  moves the clock) is unchanged. Test: a real reader-first `practice_expansion` job draws the
  commission (`generating_job_id` = the job); drawn at T, job failed at T+10 min: open at T+7 d+5 min,
  expired at T+7 d+11 min; running or queued: open at T+60 d; job row deleted: open a minute before
  T+7 d, expired at it.
- **F15 (R4).** `generation.record_landed_commissions` reconciles every commission without a receipt,
  open, expired or superseded (the scan, the simpler exact option: no hook in the content pipeline's
  apply path). An item belongs to the commission that was its cell's latest when it landed (drawn at or
  before the item, with no later commission for the cell drawn before it); the one-open rule makes
  that the commission open, or last open, at the landing, so no item is attributed to two commissions.
  Items are grouped by LO first, so the wider scan stays cheap. Migration 214's
  `ad_commission_results` gains `landed_after_expiry` (0/1): 1 when the item landed at or after
  `ad_serving.commission_expires_at`. The report's commission section counts them
  (`selection.commissions.landed_after_expiry`). Expiry still only closes a commission to new draws;
  supersession (at most one open per cell) is unchanged; content and evidence are never touched.
  Tests: the verify's case (landed on day 1, the next reconciliation on day 9, after expiry) gets exactly
  one receipt, not marked late; a second reconciliation and a whole `rebuild_all_derived_state` change no
  row. An item landing on day 8 gets a receipt marked late; after a fresh commission is drawn for the
  cell on day 10, an item at the old point landing on day 11 is never the old commission's.
- **The spec** (`spec_adaptive_difficulty_v1.md` §6.1 step 0, the F5 record in §6.1, §7.4 and the
  table rows of §11.2) records the three behaviours; F5's "What changed" above notes its supersession.
- **The head fixture.** `fixtures/migration_head_214` rebuilt as before: a backup-API copy of git
  `29a49b5e6`'s `migration_head_213` with only 214 applied (`UPGRADE_SCRATCH_COPY`),
  `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE`, header bytes 1/1, `integrity_check` ok,
  `foreign_key_check` empty, no companion files; its README names the two columns.
  `table_roles` is unchanged (no new table); `db_generate_reference.py` and `db_validate_reference.py`
  rerun (0 errors).

**Fail-before.** `git archive a87979dfb src migrations` into `fixtures-local/ad23-r5-base`, the new
file run with `-o pythonpath=fixtures-local/ad23-r5-base/src`: **7 of 7 fail**. F12 on the forecast
(off by 0.1437 from the uncoupled replay); F13's scenario on the pool (`{'pi_o1', 'pi_o2'}`, no `pi_a`)
and the parity test on `pi_a` never projected (the two copies agree, both wrong); F14's two tests on the
missing `generating_job_id`; F15's two tests on reconciliation writing nothing (`0 == 1`). All 7 pass
after the fix.

### Gate (this round; owner rule 2026-10-17: targeted only)

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 27 kept, 0 broken |
| `tests/test_ad23_fix_r5.py` alone | 7 passed |
| targeted pytest, `uv run pytest -n auto` over 96 files: every `test_ad*` and `test_adaptive_difficulty*` file (`test_ad23_sim.py` included), every `test_daily_plan*` and `test_today*` file, every file naming `migration_head_214`, `DEFAULTS_SNAPSHOT`, `defaults_fingerprint` or the parameter registry, `test_table_roles`, `test_rebuild_orchestrator`, `test_shadow_rebuild`, `test_architecture`, the queue and job tests (`test_ingest_queue_store`, `test_ingest_jobs`, `test_ingest_runner`, `test_ingest_ownership`, `test_question_promotion_jobs`, `test_contract_commissioning`), `test_tracked_fixture_databases`, `test_coordinated_migrations`, `test_sqlite_file_copies`, `test_cli_help_snapshot`, `test_desktop_rpc_contract`, `test_salience_firewall`, `test_mobile_allowlist` | **7,112 passed, 36 xfailed** (953 s); the 36 are the failed simulation gates' strict xfails, unchanged |
| `--durable-sqlite`: `test_ad23_fix_r5.py`, `test_ad23_migration.py`, `test_tracked_fixture_databases.py` | 13 passed |
| references: `db_generate_reference.py`, `db_validate_reference.py` | 0 errors; the two new columns in the `ad_selections` and `ad_commission_results` notes; configuration catalog unchanged (927 leaves) |
| defaults snapshots, CLI help | unchanged (no config key, command or option changed) |
| vitest, `cargo check` | not applicable: no frontend or `src-tauri` change |

## Fix round 6: the round-5 verify's F15 (reopened) and F16 (2026-10-19)

Codex's verify of round 5 (codex-job `20261019-205930-JA9yfv`, verdict REOPENED) confirmed F12, F13
and F14 and migration 214 with its table roles (22 DERIVED tables, one replayer each). It reopened F15
and raised F16. This round fixes both under the orchestrator's rulings R1 and R2, in commit
`ca191d538`. The regressions are in `tests/test_ad23_fix_r6.py`. No model calls: fakes only.

| Id | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F12, F13, F14 | High, High, Medium | (confirmed fixed by the verify) | fixed | `da3def4dd` | their round-5 tests still pass |
| F15 | Medium | Late items disappear when the successor commission requests different features | fixed (R1) | `ca191d538` | `test_a_late_item_off_the_successors_point_is_the_successors_landing` |
| F16 | Medium | Same-second reconciliation can attribute one item to two commissions | fixed (R2) | `ca191d538` | `test_one_owner_at_equal_timestamps_and_the_first_attribution_is_final`, `test_draws_of_one_second_are_ordered_by_insertion` |

### What changed

- **F15 (R1).** Landing ownership is by cell and order only, never by feature match.
  - `generation.landing_owner`: an active item belongs to the cells of its facets at its capability. Of
    those cells' commissions drawn at or before its landing, the last in draw order owns it, whether
    that commission is open, expired or superseded now.
  - `record_landed_commissions` walks the items, not the commissions. A commission can therefore own
    several items, and every active item that lands in a commissioned cell gets one receipt. An item
    that landed before any commission of its cells is not a commissioned landing.
  - The receipt records the item's realized (audited) features and their re-forecast.
    `ad_commission_results.features_match` (new inside migration 214, 0/1) says whether those features
    are the requested point. The report counts the off-point landings
    (`selection.commissions.off_point`).
  - The verify's case: A asks complexity c on day 0 and expires; B asks the other complexity on
    day 9; an item at A's point lands on day 10. It gets exactly one receipt, owned by B, recording
    A's point as the realized features with `features_match = 0`. Round 5's late-landing test now
    also requires the fresh commission to own the item that lands after it.
- **F16 (R2).** One owner per item, enforced in persistence.
  - `ad_commission_results` is `UNIQUE(practice_item_id)` (it replaces `UNIQUE(selection_id,
    practice_item_id)`). `insert_commission_result` stays idempotent for the same pair; a second
    owner raises on the constraint.
  - Reconciliation skips items that already have a receipt, so the first attribution is final.
  - Draws are totally ordered by `(created_at, rowid)` (`ad_serving.commissions_in_draw_order`),
    because timestamps carry whole seconds. `open_commissions`' supersession now reads the same order
    (it read `(created_at, id)`, and ULIDs are random within a millisecond), so the open commission
    and the landing owner always agree.
  - The verify's same-second case: `pi` lands in the second of A's draw and is receipted to A; B is
    drawn for the cell and point in that second. Repeated reconciliation and a whole
    `rebuild_all_derived_state` leave exactly `[(A, pi)]`, and inserting `(B, pi)` fails with
    `UNIQUE`. With two draws in one second, a landing in it belongs to the one inserted last, which
    is also the cell's open commission.
  - `test_ad23_migration`'s foreign-key insert now uses its own item id, so it still tests the
    foreign key and not the new uniqueness.
- **Migration 214, the fixture and the references.** `fixtures/migration_head_214` was rebuilt
  again, the same way: git `29a49b5e6`'s `migration_head_213` with only 214 applied, checkpointed,
  `journal_mode=DELETE`, header bytes 1/1, `integrity_check` ok, `foreign_key_check` empty, no
  companion files. Its README records the change. `table_roles` is unchanged. The reference scripts
  were rerun (0 errors), and `ad_commission_results`' note shows `features_match` and the uniqueness.
- **The spec** (§7.4's F15 record and the `ad_commission_results` row of §11.2) states the
  ownership rule, the total order and the one-owner constraint.

**Fail-before.** `git archive 880bdd592 src migrations` into `fixtures-local/ad23-r6-base`, run with
`-o pythonpath=fixtures-local/ad23-r6-base/src`: **3 of 3 new tests fail**.
- F15's case: reconciliation wrote nothing (`0 == 1`).
- The same-second case: a second reconciliation wrote `(B, pi)`.
- The tie case: nothing written, because the latest draw asked for another point.

All three pass after the fix. The round-5 file passes on both trees: its extended assertion holds on
the old tree only because that run's fresh draw happened to request the old point.

### Gate (this round; owner rule 2026-10-17: targeted only)

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 27 kept, 0 broken |
| `test_ad23_fix_r6.py`, `test_ad23_fix_r5.py`, `test_ad23_migration.py` | 14 passed |
| targeted pytest, `uv run pytest -n auto` over 97 files (round 5's 96 plus `test_ad23_fix_r6.py`) | **7,115 passed, 36 xfailed** (934 s); the 36 are the failed simulation gates' strict xfails, unchanged |
| `--durable-sqlite`: `test_ad23_fix_r6.py`, `test_ad23_fix_r5.py`, `test_ad23_migration.py`, `test_tracked_fixture_databases.py` | 16 passed |
| references: `db_generate_reference.py`, `db_validate_reference.py` | 0 errors |
| defaults snapshots, CLI help, vitest, `cargo check` | unchanged or not applicable (no config, command, frontend or `src-tauri` change) |

## Fix round 7: the round-6 verify's F17 and F18 (2026-10-19)

Codex's verify of round 6 (codex-job `20261019-212940-fdjMvO`, verdict REOPENED) confirmed F15 and
F16, migration 214 and the replayers. It raised F17 (High) and F18 (Medium). The orchestrator accepted
round 6's origin-independent cell landings (§7.4) as the definition. This round fixes both findings
under rulings R1 and R2, in commit `915228c37`, with no migration change. The regressions are in
`tests/test_ad23_fix_r7.py`. No model calls: fakes only.

| Id | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F15, F16 | Medium | (confirmed fixed by the verify) | fixed | `ca191d538` | their round-6 tests still pass |
| F17 | High | Held-out items enter commission forecasts and close commissions | fixed (R1) | `915228c37` | `test_a_protected_landing_never_closes_forecasts_or_receipts_a_commission`, `test_with_the_predicate_unavailable_nothing_is_reconciled`, `test_a_protected_item_never_steers_the_commissioned_cell_or_readiness` |
| F18 | Medium | `features_match` compares stamped features instead of the recorded audited features | fixed (R2) | `915228c37` | `test_features_match_reads_the_audited_features_the_receipt_records` (both directions) |

### What changed

- **F17 (R1), reconciliation.** `record_landed_commissions` computes
  `protection(vault, repository)` once per reconciliation. It skips every item that
  `protected.covers(item)` reports, before ownership resolution, forecasting or a receipt.
  - A protected landing never closes, supersedes or receipts a commission.
  - If the predicate is unavailable (`material is None`), reconciliation reads nothing, writes nothing
    and leaves the commissions open until a reconciliation that can tell.
  - The verify's case (an exam reservation stands for the protection): A stays open, there is no
    receipt, and `current_spec` is never asked about the protected item. With the predicate
    unavailable, even an unprotected landing waits; once the predicate is readable again it gets its
    receipt.
- **F17 (R1), the audit of the other AD paths that scan items.**
  - **Generation targeting.** `generation.lo_cell_facet` now takes `protected` and reads only
    unprotected items for the LO's facets and weights. Its callers pass a fresh predicate: the
    commission draw in `commission_point`, and the dose arm's forecast covariate. With the predicate
    unavailable, only the LO's authored facets remain, unweighted.
  - **The relatedness proposal's prompt.** `relatedness.lo_facets` takes `protected`. Its fallback
    (an LO with no authored facets) no longer takes facets from protected items, so a facet that
    only held-out material names is never quoted to the proposal. `subject_inputs` passes its
    predicate; it already dropped protected stems.
  - **Readiness and the router card.** `readiness._cells` and `card_fields` read only unprotected
    items for the LO's cells and facet weights.
  - **The report's field comparators.** `arms._field_arms` now applies the replay's own held-out rule
    (`held_out_items`, failing closed: no row observed when it is unreadable), so no attempt on
    held-out material updates `mastery_ekf` or `lo_general`. Before, they observed every field row.
  - **Checked and unchanged.**
    - The AD replay and rebuild already exclude attempts on held-out material and fail closed.
    - The feature audit, the outside forecasters, the backfill and the serve receipts already ask the
      predicate.
    - `data_check` only counts items and attempts for the owner's data report; it feeds no AD input.
    - `relatedness.facet_maps` (the replay structure's facet map) reads authored LO facets first and
      has no repository. Its item fallback is unchanged.
- **F18 (R2).** Reconciliation resolves one mapping per landing: `spec.features`, the audited
  features where an audit exists, else the stamp. That same mapping is the receipt's
  `features_json`, the re-forecast's input and the input of `_matches_point`, which now takes it
  instead of the item. Tests:
  - stamped on the requested point but audited off it: `features_match = 0`, the receipt records the
    audited value, and the report's `off_point` is 1;
  - the inverse: `features_match = 1`, `off_point` 0.
- **The spec** (§7.4's record) states both rules and the audited paths.

**Fail-before.** `git archive 6a626617e src migrations` into `fixtures-local/ad23-r7-base`, run with
`-o pythonpath=fixtures-local/ad23-r7-base/src`: **5 of 5 fail**.
- The protected case: a receipt was written to A.
- The unavailable predicate: a receipt was written anyway.
- The targeting test: `lo_cell_facet` had no `protected` (the old tree counted every item).
- Both F18 directions: the flag was inverted (`1 == 0`, `0 == 1`).

### Gate (this round; owner rule 2026-10-17: targeted only)

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 27 kept, 0 broken |
| `test_ad23_fix_r7.py` alone | 5 passed |
| targeted pytest, `uv run pytest -n auto` over 101 files (round 6's 97, `test_ad23_fix_r7.py` and the relatedness, readiness and router-card files) | **7,140 passed, 36 xfailed** (858 s); the 36 are the failed simulation gates' strict xfails, unchanged |
| `--durable-sqlite`: `test_ad23_fix_r7.py`, `test_ad23_fix_r6.py`, `test_ad23_fix_r5.py` | 15 passed |
| references: `db_generate_reference.py`, `db_validate_reference.py` | 0 errors (commit labels; no schema change) |
| migration 214, head fixture, defaults snapshots, CLI help, vitest, `cargo check` | unchanged or not applicable |

## Fix round 8: one protected material view (verify F19-F27, 2026-10-19)

Codex's verify of round 7 (codex-job `20261019-215812-pCHeIT`, verdict REOPENED) confirmed F17 and
F18. Its full A8 audit then found seven High leaks (F19-F25) and two Medium findings (F26, F27). Point
fixes had not converged, so the orchestrator's ruling was structural: one protected material view for
AD, enforced by an architecture test. The ruling also says to fix inherited readers here, because
AD2+AD3 is what makes them live. Commit `f0c85f2f7` carries the fix, with no migration change. The
regressions are in `tests/test_ad23_fix_r8.py` (16 tests) and `tests/test_ad23_material_view.py`
(4 tests). No model calls: fakes only.

| Id | Severity | Title | Origin | Verdict | Commit | Test |
|---|---|---|---|---|---|---|
| F17, F18 | High, Medium | (confirmed fixed by the verify) | stage | fixed | `915228c37` | round-7 tests pass |
| F19 | High | Replay and reading mappings still admit protected items | the replay's facet map is this stage's (AD3); the Reader map's `lo_for_item`/`facets_for_lo` are inherited from AD1 | fixed | `f0c85f2f7` | `test_a_withheld_items_facet_never_enters_the_facet_maps_or_the_reading_map`, `test_a_claim_moves_no_forecast_through_a_withheld_items_facet` |
| F20 | High | Excluded held-out attempts still change forecasts and replay state | stage (AD2/AD3: serve warmth, replay exposures and windows, replayed receipts) | fixed | `f0c85f2f7` | `test_an_attempt_on_held_out_material_warms_nothing_and_is_invisible_to_the_replay`, `test_a_reading_receipt_whose_source_is_held_out_now_is_not_replayed` |
| F21 | High | AD generation prompts still contain protected item metadata | inherited generation helpers, made live by the stage's commissioned path | fixed | `f0c85f2f7` | `test_a_withheld_items_metadata_never_reaches_an_ad_generation_target` |
| F22 | High | AD selection uses a switchable protection filter and does not fail closed | stage (`ad_slot`); the routine exclusions' switch is inherited | fixed | `f0c85f2f7` | `test_ad_selection_withholds_held_out_material_with_held_out_selection_off`, `test_an_unreadable_predicate_makes_ad_unavailable_and_the_incumbent_serves` |
| F23 | High | The dose arm can select and return a held-out question | stage (AD3 dose arm) | fixed | `f0c85f2f7` | `test_the_dose_arm_never_offers_or_returns_a_held_out_question` |
| F24 | High | In-process forecasts and outside-signal calibration retain unfiltered history | inherited from AD1 (challenger, `z_v1` recalibration) | fixed | `f0c85f2f7` | `test_the_challengers_history_never_reads_a_withheld_items_answer`, `test_z_v1_calibration_never_reads_a_withheld_items_forecast` |
| F25 | High | Report sensitivity re-forecasts currently protected items | stage (AD3 report) | fixed | `f0c85f2f7` | `test_report_sensitivity_never_re_forecasts_a_withheld_item` |
| F26 | Medium | Ungraded or protected attempts erase the recorded dose moderator | stage (AD3 dose arm) | fixed | `f0c85f2f7` | `test_the_dose_moderator_window_closes_only_at_a_visible_graded_attempt` |
| F27 | Medium | Held-out attempt durations change the practice burden recommendation | stage (AD3 report) | fixed | `f0c85f2f7` | `test_practice_minutes_come_from_the_visible_practice_cohort` |
| (ruling) | | The boundary, enforced | | built | `f0c85f2f7` | `test_ad23_material_view.py`; the degradation tests (selection, generation, report, dose) in `test_ad23_fix_r8.py` |

### What changed

- **The view** (`src/learnloop/adaptive_difficulty/material_view.py`). `material_view(vault,
  repository)` computes the held-out predicate once per operation; a caller passes the view on rather
  than recomputing it.
  - It is the only reader AD uses for items, item facets and surface families, attempts (with
    latency), field rows, the observation ledger, Reader questions, reading-opportunity receipts,
    plan presentations, reveals, saved revisions and forecast history.
  - Each reader is filtered by `Protection.covers`: held-out material plus current exam reservations.
    A withheld item's attempts, presentations, reveals, forecasts and receipts are withheld with it,
    and so is any facet only withheld items name.
  - Reading receipts are revalidated by resolving their source again. A source row deleted since
    leaves its frozen receipt standing (§5.11); an unreadable one is withheld.
  - The protection never reads `goals.held_out_selection`.
  - When the predicate is unavailable, the view is empty (`UNAVAILABLE`).
- **Replay** (`replay.load_events`, `snapshot`, `rebuild`; `relatedness.load_structure`; scoring).
  - Attempts, reveals, presentations, the ledger, field rows, revisions and receipts come from the
    view. An attempt on a withheld item (or on a withheld revision) is invisible: no event, no
    reading window closed, no first surface taken, no warmth.
  - The facet maps are the view's. `relatedness.facet_maps` is gone; `lo_facets(view, lo)`
    delegates to the view.
  - The `held_out` exclusion reason no longer appears: a withheld attempt is absent, not excluded.
- **Serving** (`serving._warmth`, `decide_slot`, `_maybe_commission`, `threshold_receipts`,
  `frozen_loadings`, `why_for_presentation`) and **the serve hook** (`serve.record_plan_serve`).
  - One view per serve and per slot. Warmth reads the view's attempts, reveals and revalidated
    receipts.
  - `predict.current_spec`, `serve_inputs.signal_vector`, `z_v1_recalibration` and `_z_v1` take the
    view, so `z_v1`'s calibration observations are the view's forecasts and attempts (F24).
- **Selection** (`daily_plan/ad_slot.py`, `daily_plan/engine._ad_slot_serve`).
  - `slot_view` raises `AdUnavailable` when the predicate is unavailable, and so does a failing
    routine exclusion. The engine then serves the planned item as the incumbent does: nothing is
    written, and no exception reaches the caller (F22).
  - A withheld candidate fails check 0 with `held_out` whatever the routine switch says.
  - `deferrals_to_clear` releases nothing while AD is unavailable.
- **Generation**.
  - `generation.lo_cell_facet(view, ...)` and `commission_point(..., view=)`: unavailable means no
    commission.
  - `record_landed_commissions(..., view=)`.
  - In `practice_generation`, under the generation contract with an available view, the targets'
    counts (and so the deficit), facet unions and surface families come from `view.items()` (F21).
    With the contract off, or the view unavailable, the shared helpers read the vault exactly as
    before (`items=None`), and `_ad_commissioned_rung` returns the predecessor's rung.
- **The reading sweep** (`reading.VaultReadingMap`, `sweep`).
  - The map's held-out check, section spans, `lo_for_item` and `facets_for_lo` are the view's (F19).
  - The Reader-question collectors read the view's questions.
  - A sweep with the predicate unavailable records nothing, so the next sweep that can tell reads
    those rows.
- **The dose arm** (`dose.feasible_variants`, `decide`, `dose_taken`, `offer_withheld`; the
  `reader.dose_offer` RPC).
  - Extras come from the view: an example on held-out material, or a question whose extraction,
    anchors or cited spans are held out, is never feasible.
  - A cached draw whose extra is withheld now returns no offer (`withheld`), and the RPC
    revalidates the question at response time (F23).
  - With the predicate unavailable, nothing is drawn (`protection_unavailable`).
  - F26: the moderator's window closes at the LOs' last visible attempt that closes a window as the
    replay reads it (`material_view.closes_window`: graded, not a skip or self-report). Only visible
    receipts count.
- **The report.** `arms.prequential` returns its view, which the report reuses.
  - Field comparators read `view.field_rows`.
  - Sensitivity revalidates each support member, re-forecasts only visible ones, and discloses
    `support_refs` and `withheld` (F25).
  - Practice minutes are the median of the practice cohort (`view.practice_minutes`: visible, graded
    practice answers with a positive latency; F27).
  - Offer outcomes read the view's reveals.
  - A new `protection` block discloses `available`, `reason` and the withheld-item count. With the
    predicate unavailable, the report has zero observations and says why.
- **The rest.**
  - Readiness and router-card cells, the outside forecasters' history card and presentation lookup
    (`presentation_status` keeps a withheld presentation reported `protected`), backfill
    (`view.audit_revisions` keeps the `protected_skipped` count) and background preparation (a
    withheld unit reports `protected` and leaves the queue settled) all read through the view.
  - The in-process challenger rebuilds on `view.field_rows` (F24).
- **The boundary test** (`tests/test_ad23_material_view.py`). It is an AST scan over every module of
  `adaptive_difficulty/`, `daily_plan/ad_slot.py` and the sidecar's AD handlers, plus the commissioned
  functions of `practice_generation.py`, for the raw readers:
  - the vault's item map (`.practice_items`, `getattr(..., "practice_items")`);
  - `load_attempt_rows`, `load_authoritative_observation_ledger`, the held-out predicate functions
    and `get_reader_authored_question`;
  - SQL reads (`FROM`/`JOIN`, docstrings excluded) of `practice_attempts`,
    `reader_authored_questions`, `plan_presentations`, `reveal_events`, `practice_item_snapshots` and
    `ad_reading_opportunities`.

  The allowlist: the view, the predicate (`protection.py`), `data_check.py` (descriptive inventory),
  and three background-queue scheduling functions. Those functions compute revision keys of work to
  prepare; each run reads them back through its own view. They stay outside the view because
  computing the predicate at scheduling would drop a batch that fails before its first revision
  (AD1 fix round 5's regression). One test checks that the scan itself catches a planted leak.
- **Tests touched.**
  - The round-7 targeting test now uses the view.
  - The reading tests' fake `VaultReadingMap` factories accept the view.
  - `why_for_presentation` callers pass a view.
  - `test_ad3_subject_view` passes a view to `load_structure`.
  - `test_salience_firewall`'s reader allowlist adds `material_view.py`, which revalidates the
    receipts and still hands them to the replay only through the carve-out.
- **The spec.** A8 names the view as the boundary, its fail-closed degradations and its test.

**Fail-before.** `git archive 7afd509fb src migrations` into `fixtures-local/ad23-r8-base`, run with
`-o pythonpath=fixtures-local/ad23-r8-base/src`: **15 of the 16 behavioural tests fail**, on
behaviour, with the verify's own figures:

| Finding | Before | Now |
|---|---|---|
| F19 facet map | `['secret'] == []` | none |
| F19 forecast | 0.7807798714 | 0.49 |
| F20 warmth | 0.84648172 | 0 |
| F20 replayed receipts | two receipts | one |
| F21 existing items | `2 == 1` | 1 |
| F22, switch off | the held-out item drawn | never drawn or served |
| F22, unreadable predicate | `RuntimeError` | the incumbent serves |
| F23 | `extra_question` feasible | not offered |
| F24 challenger | the spy saw the attempt | not read |
| F24 `z_v1` | `n = 1` | `n = 0` |
| F25 | the spy saw the item | not re-forecast |
| F26 | `worked_example` 0 | 1 |
| F27 | 500.5 minutes | 1 |
| report with predicate unavailable | no `protection` block | disclosed |
| dose with predicate unavailable | drew | `protection_unavailable` |

The 16th test, the generation degradation, passes on both trees: the old tree also commissioned
nothing with the predicate raising. The boundary scan, run over the old tree's sources, reports **61
raw reads** in 18 files (0 now).

### Gate (this round; owner rule 2026-10-17: targeted only)

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 27 kept, 0 broken |
| `test_ad23_fix_r8.py`, `test_ad23_material_view.py` | 20 passed |
| targeted pytest, `uv run pytest -n auto` over 113 files: round 7's 101, the two new files and the generation tests this round touches (`test_ingest_instrument_gates`, `test_facet_diagnostics_v03`, `test_persona_gate`, `test_practice_item_quality_gates`, `test_difficulty_band_guards`, `test_reader_progression`, `test_practice_leakage`, `test_goal_scope_material`, `test_recall_coverage_interventions`, `test_tutor_promotion_w2`, `test_serving_exclusions`) | **7,284 passed, 36 xfailed, 2 failed** (978 s) |
| the two failures | `test_salience_firewall::test_ad_replayer_reads_the_receipt_only_through_the_carve_out` (its allowlist predates the view; updated); `test_ad3_subject_view::test_coupling_is_prediction_only`, whose plain-vs-adversarial evidence masses differed by a uniform 0.9916 factor once, under the gate's load. It passes in isolation and 6 of 6 repeats, and its evidence tables are written by code outside AD. Recorded as a load-sensitive flake to watch at the landing gate |
| rerun: `test_ad3_subject_view.py`, `test_salience_firewall.py` | 5,544 passed (three runs) |
| `--durable-sqlite`: `test_ad23_fix_r8.py`, `test_ad23_material_view.py`, `test_ad23_fix_r7.py`, `test_ad23_migration.py` | 29 passed |
| kill switch off | round 5's parity test (`test_with_the_kill_switch_off_today_projects_the_predecessors_blocks`) passes in the gate; with AD off no view is computed on the plan path |
| references: `db_generate_reference.py`, `db_validate_reference.py` | 0 errors (commit labels; no schema change) |
| migration 214, defaults snapshots, CLI help, vitest, `cargo check` | unchanged or not applicable |

## Fix round 9: the A8 contract, protected == absent (2026-10-20)

Codex's verify of round 8 (codex-job `20261019-230404-jvyfJE`, verdict REOPENED) confirmed F19,
F22, F23 and F25. It reopened F20, F21, F24, F26 and F27, and raised F28 (High) and F29-F32 (Medium).
It also showed that the AST scan alone misses aliases, repository methods, external helpers and the
full generation path.

The orchestrator's rulings R1-R8 are structural:

- filter at the source, before any derivation;
- carry the view through generation and revalidate the request before it is sent;
- route every report cohort through the view;
- make the metamorphic test "protected == absent" the A8 contract.

Commit `1001054f2` implements them, with no migration change. The tests are
`tests/test_ad23_contract.py` (3 tests: the contract, the unavailable harness, the no-protection
parity) and `tests/test_ad23_fix_r9.py` (4 focused regressions). No model calls: fakes only.

| Id | Severity | Title | Origin | Verdict | Commit | Test |
|---|---|---|---|---|---|---|
| F19, F22, F23, F25 | High | (confirmed fixed by the verify) | | fixed | `f0c85f2f7` | round-8 tests pass; the contract covers them |
| F20 | High | Protected historical attempts still warm forecasts and enter prompts | stage (warmth) and AD1 (history card) | fixed (R1) | `1001054f2` | the contract (steps, receipts, the outside prompt inputs, the replay); `test_an_attempt_on_a_held_out_answered_revision_is_filtered_at_the_source` |
| F21 | High | Commissioned generation still quotes protected stems and metadata | inherited authoring context and contract reachability, made live by the commissioned path | fixed (R2) | `1001054f2` | the contract (the captured request and its sentinels); `test_a_commissioned_request_quoting_withheld_material_is_refused_before_it_is_sent` |
| F24 | High | Protected answers affect retained field rows before filtering | AD1 (challenger) and stage (report comparators) | fixed (R1) | `1001054f2` | the contract (challenger receipts, the report, `ad eval`) |
| F26 | Medium | Protected revisions still erase the dose moderator | stage | fixed (R1) | `1001054f2` | the contract (the dose draw's `dose_taken`); the focused R1 test (the window cutoff) |
| F27 | Medium | Protected revisions still inflate practice burden | stage | fixed (R1) | `1001054f2` | the contract (the report); the focused R1 test (practice minutes) |
| F28 | High | Raw duration history changes AD selection support | stage (the slot uses the plan's estimator) | fixed (R1) | `1001054f2` | the contract (the slot request's candidate estimates) |
| F29 | Medium | Protected commission forecasts remain in report figures | stage | fixed (R3) | `1001054f2` | the contract (the report, `ad report`); the unavailable harness (suppression) |
| F30 | Medium | Round 8 changes frozen reading evidence without protected material | round 8 | fixed (R4) | `1001054f2` | `test_with_no_protection_a_frozen_dose_on_an_absent_facet_stands` |
| F31 | Medium | Answered-question projection omits the citations needed for protection | round 8 | fixed (R5) | `1001054f2` | the contract (the sweep's writes: an answered question citing a held-out span, and its self-check verdict) |
| F32 | Medium | Relatedness can send requests when the predicate is unavailable | stage (relatedness), AD1 (SendGuard) | fixed (R6) | `1001054f2` | `test_with_the_predicate_unavailable_relatedness_prepares_nothing`, `test_send_guard_refuses_an_unavailable_predicate_whatever_the_job_quotes`; the unavailable harness |

### What changed

- **R1, filtering at the source** (`material_view.py`).
  - `attempts()` withholds an attempt when its current item is withheld, or when any revision it
    answered is: the presentation's frozen revision (`item_serve_inputs`), or field's own revision
    resolution (`item_snapshot_hash`). It is resolved once per view on the raw table, only to decide
    what is withheld. Presentations are withheld with their frozen revision.
  - Every derived quantity is computed from those rows:
    - `field.outcomes.load_attempt_rows(..., attempt_rows=...)` is a new injectable source, so the
      familiarity history and reveal windows of a kept row never see a withheld answer.
      `MaterialView.field_rows` uses it for the challenger, the report's comparators and the replay.
    - `daily_plan.estimates.load_duration_evidence(..., attempt_rows=...)` is another new injectable
      source. AD's slot builds its candidate estimates from the view's rows (`ad_slot._estimator`);
      the slot's own planned estimate stays the plan's.
    - Warmth, the dose moderator's window, practice minutes and the outside forecasters' history
      card were already read from `attempts()`, so they follow.
  - With AD off, nothing passes these parameters: the incumbent reads are unchanged.
- **R2, generation.**
  - Under the generation contract with the view available, `build_practice_expansion_plan` reads
    `MaterialView.vault_view()` (the same vault with only visible items) for contract reachability
    (`commission_plan`), contrast-pair reachability, the targets' counts, facets and surface
    families.
  - The plan carries its view (`PracticeExpansionPlan.material_view`). The three plan-based
    generators pass `vault_view` and `request_guard` to `generate_authoring_proposal` (new default-off
    parameters). The authoring context is built from the vault the view sees, re-read at send time.
  - `CommissionedRequestGuard` scans the serialized request before the agent run is recorded or
    anything is sent. It refuses (`ProtectedRequest`, logged) a request quoting a withheld item's id
    or stem, or a facet or surface family only withheld material names, and refuses everything while
    the predicate is unavailable.
  - A commissioned target leaves out the incumbent's `mastery_mean`, as it already left out the band:
    under the contract the difficulty is AD's point.
  - `open_commissions(landed=...)`: a result on a withheld item does not close its commission
    (`MaterialView.open_commissions`, used by the slot, the generation path, scheduling and the
    commission job).
  - On "no commission written": the commission draw happens while the plan is built, before the
    request exists. A refused request therefore leaves its draw in place, and it expires as an
    unlanded commission. Nothing is generated or sent.
- **R3, the report.** Commission results (`visible_commission_results`), dose rows and offer outcomes
  (`MaterialView.dose_rows`: a draw whose extra is withheld now, with its uptake, is left out) go
  through the view. With the predicate unavailable, the selection and dose-arm sections are
  `{"suppressed": "held_out_predicate_unavailable"}`.
- **R4 (F30).** A reading dose drops only facets that withheld material alone names
  (`protected_only_facets`, judged over current items and saved revisions). A frozen dose on a facet
  merely absent from current content stands, as in round 7.
- **R5 (F31).** `answered_questions` selects `span_ids_json` as well as the anchors before the check.
- **R6 (F32).** `propose_subject` returns `unavailable` before assembling, claiming or sending
  anything. `SendGuard` refuses an unavailable predicate whatever the job quotes.
- **R7, the contract** (`tests/test_ad23_contract.py`).
  - **Setup.** One vault is built and copied twice. The "protected" copy gets every kind of protected
    material listed in A8's record:
    - a held-out current item with a sentinel stem, facet and surface family;
    - a held-out item sharing the public LO, facet and family;
    - a public item whose earlier answered revision is held out (snapshot, presentation, frozen serve
      inputs, attempt);
    - correct protected answers with 1,000-minute latencies;
    - a reveal, a commission result and a reading receipt on protected material;
    - a Reader question citing a held-out span (one unanswered, one answered with its verdict), and a
      dose draw that offered it.

    The "absent" copy never has that material. The AD decisions that are not derived from it (the
    base commission draw, the dose draw) exist in both.
  - **Run.** Ids are deterministic: each stage mints from its own fixed millisecond, so non-AD writes
    that exist in one copy only (state sync of the protected items) never shift AD's ids. The system
    clock is frozen, and the hints' background approach-map build is off. The harness runs on both
    copies:
    - serves with the slot draw (its candidates' estimates captured), the serve hook, an answer and a
      second serve;
    - `RP.rebuild` and the forecast-score rebuild;
    - the outside forecasters' item view and history card;
    - the commission draw and the commissioned generation request (captured by a fake generator);
    - the relatedness inputs and proposal (captured by a fake);
    - readiness and the router card;
    - two dose decisions (fresh, and the earlier draw's boundary);
    - a backfill reading sweep through a Reader map;
    - the report;
    - `ad report --json` and `ad eval --json` through the CLI.
  - **Assertions.** No sentinel appears in any captured request or prompt input. Every AD write
    (`ad_selections`, `ad_commission_results`, `ad_dose_offers`, `ad_reading_opportunities`,
    `forecast_receipts`, `item_serve_inputs`, `ad_relatedness_runs`, the plan's block events and the
    answers) and every DERIVED table (`ad_state`, `ad_attempt_trace`, `item_forecast_scores`) is
    identical. So is every returned figure: steps, estimates, prompts, readiness, card, dose, sweep,
    report and CLI output.

    Only the report's `protection` disclosure block and its `generated_at` are set aside. One
    carve-out is recorded: AD1's `mastery_ekf` receipt (and its score rows) records the incumbent's
    live mastery state verbatim. An exam answer is evidence in the incumbent by design; the receipt
    trains and selects nothing in AD and quotes no material.
  - **The unavailable harness** (predicate raising) checks that:
    - the incumbent serves both planned items;
    - no AD row is written;
    - relatedness reports `unavailable` and the dose arm `protection_unavailable`;
    - the sweep writes nothing;
    - generation carries no contract text or commission;
    - the report is suppressed with zero records.
  - **The no-protection parity case** pins F30.
  - The round-8 AST scan stays as a lint (`test_ad23_material_view.py`).

**Fail-before.**
- `tests/test_ad23_contract.py` and `tests/test_ad23_fix_r9.py` against `22eb66d72` (`git archive`
  into `fixtures-local/ad23-r9-base`, `-o pythonpath`): **7 of 7 fail**.
  - The contract fails first on its sentinel check: stem, facet, family, `pi_secret` and `pi_shared`
    all appeared in the commissioned request (F21).
  - With the sentinel check set aside, its comparison differs in the following entry points, each
    covering one or more of the verify's findings:
    - the slot's candidate estimates (F28);
    - the steps, serve receipts and serve inputs (F20/F24 warmth and challenger history);
    - the outside prompt inputs (F20);
    - the generation request (F21);
    - the replay trace and the scores (F20/F24);
    - the reading sweep's writes (F31: an in-passage receipt for the cited question);
    - the report's and `ad report`'s commission figures (F29);
    - the plan's events.
  - The unavailable harness fails on a relatedness run written with the predicate unavailable (F32).
  - The parity case fails on an emptied frozen dose (F30).
  - The focused tests fail as follows:
    - R1: the held-out revision's answer was visible;
    - R2: the guard did not exist;
    - R6 relatedness: `ok`, a request built and sent;
    - R6 SendGuard: no refusal.
- All 7 pass after the fix.

### Gate (this round; owner rule 2026-10-17: targeted only)

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 27 kept, 0 broken (the AD estimator is built in `daily_plan/ad_slot.py`; the view never imports the plan) |
| `test_ad23_contract.py`, `test_ad23_fix_r9.py` | 7 passed |
| targeted pytest, `uv run pytest -n auto` over 134 files: round 8's 113, the two new files, every `test_field*` file, and every test naming `build_authoring_context`, `generate_authoring_proposal`, `load_attempt_rows` or `load_duration_evidence` | **7,612 passed, 36 xfailed** (1,028 s), 0 failed |
| `--durable-sqlite`: `test_ad23_contract.py`, `test_ad23_fix_r9.py`, `test_ad23_fix_r8.py`, `test_ad23_migration.py` | 27 passed |
| references: `db_generate_reference.py`, `db_validate_reference.py` | 0 errors (commit labels; no schema change) |
| migration 214, defaults snapshots, CLI help, vitest, `cargo check` | unchanged or not applicable |

### For the next verify

Per the orchestrator, the R7 metamorphic test is the A8 contract. A finding should show an entry
point or an input kind it does not cover. Two boundaries are recorded rather than covered:

- AD1's live incumbent receipt (`mastery_ekf`) and the incumbent numbers the frozen `llm_v3` state
  quotes from it. These are numbers from the incumbent's own evidence, never material.
- Incumbent planning, which keeps the plan's own estimates (only AD's candidate estimates are
  filtered).

## Fix round 10: time-varying protection and the remaining raw readers (2026-10-20)

Codex's verify of round 9 (codex-job `20261020-014655-xFFz0U`, verdict REOPENED) confirmed F24 and
F26-F32. It reopened F20, F21 and F28, and raised F33, F34 and F36 (High) and F35 (Medium). Its
point was that the round-9 contract compares two copies at one moment, and so misses three kinds
of case: a reader whose rows it never seeded, an AD decision that reads the incumbent's evidence,
and protection that changes between two moments of one operation.

The orchestrator's rulings R1-R8 are implemented in commit `80edc01a5`, with no migration change.
All tests are in `tests/test_ad23_contract.py`, which goes from 3 tests to 14 (R8: the contract
file carries every scenario). No model calls: fakes only.

| Id | Severity | Title | Origin | Verdict | Commit | Test |
|---|---|---|---|---|---|---|
| F24, F26, F27, F29-F32 | | (confirmed fixed by the verify) | | fixed | `1001054f2` | round-9 tests pass |
| F20 | High | Historical protected reveals still warm forecasts | stage (warmth) | fixed (R1) | `80edc01a5` | the contract (a reveal on the public `pi_hist` belonging to the answer to its held-out revision: steps, receipts, scores) |
| F21 | High | Protected answers still choose a commission's capability | inherited (`select_rung`'s incumbent inputs), made live by the commissioned path | fixed (R2) | `80edc01a5` | the contract (wrong protected answers that carry the incumbent's evidence count past the legacy rung's threshold: the commission's capability and point); `test_the_commissioned_generation_path_reads_no_incumbent_diagnosis_or_probe_counts` |
| F28 | High | Protected feedback dwell still changes AD candidate admission | stage (the plan's dwell reader) | fixed (R3) | `80edc01a5` | the contract (ten protected completion-to-next-serve pairs: the slot's candidate estimates and failures); `test_feedback_dwell_skips_a_serve_withheld_with_its_presentation` |
| F33 | High | Frozen outside forecasts omit answered-revision protection identities | AD1 (frozen inputs) | fixed (R4) | `80edc01a5` | `test_a_frozen_history_is_refused_once_an_answered_revision_behind_it_is_held_out` |
| F34 | High | Commissioned repair requests bypass protection revalidation | inherited (the repair pass), made reachable by the commissioned path | fixed (R5) | `80edc01a5` | `test_a_commissioned_repair_after_protection_changed_mid_call_is_refused` (held out, unavailable); `test_request_authoring_proposal_is_called_from_the_guarded_dispatch_only` (AST) |
| F35 | Medium | Protected dose deliveries still trigger report burden flags | stage | fixed (R6) | `80edc01a5` | the contract (three delivered protected offers, each followed in its visit by a cue-density lowering: the report's and `ad report`'s burden flag) |
| F36 | High | Dose uptake writes survive the kill switch | stage | fixed (R7) | `80edc01a5` | the contract (late callbacks for the protected offers; the unavailable harness); `test_a_late_uptake_callback_writes_nothing_when_ad_cannot_record_it` (AD off, dose arm off, unavailable); `test_the_sidecar_uptake_callback_answers_a_no_op_with_ad_off` |
| self-audit | | Dose budget, taken offers, report visits and the generation gates read raw rows or the whole vault | stage | fixed | `80edc01a5` | `test_withheld_dose_offers_neither_spend_the_budget_nor_count_as_taken`; `test_the_commissioned_generation_path_reads_no_incumbent_diagnosis_or_probe_counts` |

### What changed

- **R1 (F20), reveals** (`MaterialView.reveals`). A reveal is resolved through the attempt it
  belongs to: its `attempt_id`, or its tutor question's attempt (`question_events.attempt_id`).
  That attempt is judged by `attempt_withheld`, the same answered-revision rule as `attempts()`,
  so a reveal on a public item is withheld with an answer given to a held-out revision of it.
- **R2 (F21), the commissioned rung.** Under the generation contract with the view available,
  `build_practice_expansion_plan` reads no incumbent mastery or evidence:
  - `select_rung`'s inputs are the view's own count of graded answers
    (`MaterialView.graded_counts`, the replay's window-closing cohort) and the learner's claim. No
    `mastery_ekf` value is read, so the band entry is the rung's default (claim, else `recall`).
  - `select_rung(..., episode_hypotheses=False)` skips the probe episode's top hypothesis, which is
    the incumbent's diagnosis and can count withheld answers.
  - A commissioned target's request also leaves out `probe_attempts_completed` and
    `probe_attempts_target`, as it already left out `mastery_mean` and the band.
  - The predecessor's path (contract off, or the view unavailable) is unchanged.
- **R3 (F28), feedback dwell.** `load_duration_evidence(..., event_visible=...)` is a new injectable
  rule, passed by AD's slot only (`MaterialView.plan_event_visible`). An event is invisible when:
  - it names a withheld item;
  - it completes a withheld attempt;
  - it is a serve whose presentation (found by block and item, since plan events name no
    presentation) froze a withheld revision.

  An invisible event is skipped as if it had never been written: it neither starts, ends nor breaks
  a pair. With no rule (the plan), every event pairs exactly as before.
- **R4 (F33), frozen histories.** `history_card` records, for each history entry, the attempt id
  and the source identity of every revision that attempt answered (`answered_revision_items`), next
  to the current item's identity. The frozen payload carries `history_attempts`. At dispatch,
  `SendGuard` re-judges each of those attempts through a fresh material view
  (`attempt_withheld_by_id`; a missing attempt is withheld). A now-protected entry refuses the job
  (`protected`, nothing sent). A frozen payload without `history_attempts` (written before this
  round) is never sent: it expires, as already accepted.
- **R5 (F34), one guarded dispatch** (`proposals.dispatch_authoring_request`). It is the only
  caller of `request_authoring_proposal`. It serves the first request and every repair:
  - A commissioned request (a request guard present) is revalidated on its serialized prompt
    immediately before it goes out.
  - `CommissionedRequestGuard` now reloads the vault from its root and builds a fresh material view
    for every call, so protection is read afresh and an unreadable predicate refuses.
  - A commissioned request with no guard is refused.
  - Any guard failure raises `AuthoringRequestRefused`. `_repair_invalid_proposal_items` re-raises
    it rather than treating it as a best-effort repair failure, so the whole run stops and nothing
    is persisted.
  - The refusal's message is generic. What the request quoted stays in the guard's log and the
    chained cause, never in the agent run's persisted `error_message`.
  - The diagnostic authoring path calls the dispatch with no guard (never commissioned). The AST
    test pins both facts and that the three plan-based generators pass AD's request options.
- **R6 (F35), density lowerings.** `density_lowerings(connection, view=...)` derives its offer cohort
  from `view.dose_rows()` and skips a lowering on an extraction held out as a whole. While the
  predicate is unavailable it returns none, so the burden flag cannot fire; the dose sections are
  already suppressed.
- **R7 (F36), uptake.** `record_uptake` gates at the write: with AD or `reading_dose_offers` off,
  the predicate unavailable, or the draw's extra withheld now, it writes nothing and returns None.
  The sidecar's `reader.dose_offer_event` answers `{"rowId": null, "recorded": false}`. The desktop
  client's type is widened to match; it ignores the result.
- **Self-audit** (R8's last paragraph). A sweep of `adaptive_difficulty/` and its callers for raw
  `attention_block_events`, `reveal_events`, dose rows, `interaction_events` and model dispatch
  found four more readers, now routed through the view:
  - the dose friction budget (`budget(..., view=)`): a withheld offer spends nothing;
  - `taken_offers(..., view=)`: a withheld offer tags no reading receipt;
  - the report's visits (`_visits(..., view=)`): a visit to an extraction held out as a whole is
    not one, and none is read while the predicate is unavailable;
  - the post-generation gates of the three plan-based generators (`_ad_gate_vault`): they compare a
    commissioned batch against the vault the view sees, so a withheld item's surface family or
    facet never decides what is kept, and the persona gate builds its personas from that vault.

  `MaterialView.dose_extra_withheld` now fails closed while unavailable. It distinguishes a
  question that is protected now (withheld) from one merely deleted (the offer stands, as F30's
  frozen dose does).

### Behaviour changes worth knowing

- Under the generation contract, every target of a plan built through the view (commissioned or
  not) selects its rung without the incumbent's mastery or probe diagnosis, and its difficulty band
  inverts around the learner's claim only. With the contract off nothing changes.
- A protected offer no longer spends the dose budget, so a section or day whose only offer is now
  protected can be offered again.
- A frozen outside-forecast request written before this round is never sent (it lacks
  `history_attempts`).
- A commissioned authoring run refused at dispatch is recorded as a failed agent run with the
  generic refusal message. One refused at its repair stops after the first call and persists
  nothing.

### Boundaries recorded, not changed

- `learnloop ad data-check` (AD1) counts raw graded attempts on a read-only backup copy: aggregate
  figures for the owner, never an AD decision, state or prompt.
- `build_practice_expansion_plan` still reads the incumbent's `lo_probe_state` for the predecessor's
  completed-probe gate, which decides whether an LO with no contract cell gets a target at all.
  It no longer reaches the request (the counts are left out of a commissioned target) or the rung.
  Whether a held-out answer can complete a probe is a question for the next verify.
- AD1's incumbent receipt (`mastery_ekf`) stays the recorded carve-out, for report comparison only.
  After R2 it reaches no generation targeting.

**Fail-before.** `tests/test_ad23_contract.py` against `190bf5a78` (`git archive` into
`fixtures-local/ad23-r10-base`, `-o pythonpath`): **13 of 14 fail**. The one that passes is round
9's F30 parity case, which this round does not touch.
- The contract fails on its comparison, which differs in these entry points:
  - the slot's candidate estimates: 6.8 against 2.3 minutes, and an extra `over_block_budget`
    failure (F28);
  - the serve receipts' warmth (0.812 against 0.017), the forecasts and the scores (F20);
  - the commission's capability and point: `retrieval` at complexity 1 against
    `schema_interpretation` at complexity 2, and a second commission draw (F21);
  - the report's and `ad report`'s `dose_offers_a_burden` flag: 3 lowerings, fires, against 0
    (F35);
  - three late uptake writes against none (F36), and the dose rows written.
- The unavailable harness fails on the uptake writes (F36).
- The focused tests fail as follows:
  - F33: no `history_attempts` was frozen;
  - F34: the refusal did not exist, and the AST test finds three direct callers;
  - F36: `taken` was appended with AD off, the dose arm off or the predicate unavailable, and the
    RPC had no `recorded`;
  - R3's presentation case: there was no event rule;
  - the self-audit tests: `budget` took no view, and `_ad_gate_vault` did not exist.
- All 14 pass after the fix.

### Gate (this round; owner rule 2026-10-17: targeted only)

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 27 kept, 0 broken |
| `test_ad23_contract.py` | 14 passed (with `test_ad23_fix_review.py` and `test_ad23_material_view.py`: 37 passed) |
| targeted pytest, `uv run pytest -n 12` over 157 files: round 9's 134, and every test naming `select_rung`, `request_authoring_proposal`, `_repair_invalid_proposal_items`, `record_uptake`, `dose_offer_event`, `density_lowerings`, `SendGuard`, `history_card`, `freeze_presentation_inputs`, `taken_offers`, `build_practice_expansion_plan`, `material_view`, `reveal_events`, `feedback_dwell`, `practice_generation`, `depth_rungs` or `adaptive_difficulty` | **8,423 passed, 36 xfailed** (1,954 s), 0 failed |
| `--durable-sqlite`: `test_ad23_contract.py`, `test_ad23_fix_r9.py`, `test_ad23_fix_r8.py`, `test_ad23_migration.py` | 38 passed |
| desktop: `npm run typecheck`; vitest `DoseOffer.test.tsx`, `ReaderScreen.doseOffer.test.tsx` | clean; 6 passed (the uptake result type gains `recorded` and a nullable `rowId`) |
| references: `db_generate_reference.py`, `db_validate_reference.py` | 0 errors (commit labels; no schema change) |
| migration 214, defaults snapshots, CLI help, `cargo check` | unchanged or not applicable |

### For the next verify

The contract file now carries the time-varying cases next to the one-moment comparison. Three
boundaries are recorded rather than covered: `ad data-check`'s raw aggregates, the predecessor's
completed-probe gate on LO eligibility, and AD1's `mastery_ekf` comparator receipt (report
comparison only).


## Fix round 11: the whole-pipeline differential contract (2026-10-20)

Codex's verify of round 10 (codex-job `20261020-124929-uzJT57`, verdict REOPENED) confirmed:

- R3, R4, R6 and R7, and the structural dispatch test;
- the owner defaults, A17's `0.25`, migration 214 and the head fixture;
- the 7-day expiry, and that cancelled work is never requeued automatically;
- that no forbidden writer exists;
- that boundaries (a) `ad data-check`, (b) the legacy completed-probe gate and (c) the
  `mastery_ekf` comparator carry no High.

It found four Highs (F20 reopened, F34 reopened, F37, F38) and a Medium (F39). All five are A8
readers outside the material view. After ten rounds of finding such readers one at a time, the
orchestrator's rulings are:

- R1: fix the five;
- R2: make the contract a whole-pipeline differential that catches the next reader.

Commit `ecd7e6652` implements both, with no migration change.

| Id | Severity | Title | Origin | Verdict | Commit | Caught by the differential as |
|---|---|---|---|---|---|---|
| F20 | High | Protected historical reveals still affect AD eligibility | stage (the slot's check 0 and the frozen `pre_exposed`, through the incumbent's reveal reader) | fixed | `ecd7e6652` | `pi_p4` failing `pre_exposed` and `recent_reveal` in the slot's estimates and the selections' `excluded` |
| F34 | High | Guarded repairs still accept newly protected grounding spans | round 10's guard (item tokens only) | fixed | `ecd7e6652` | a request dispatched after the late span was held out quotes it (the cited request's repair); the cross-source and cited repairs not refused |
| F37 | High | Goal generation still uses protected incumbent evidence to choose prompt focus | inherited (`goal_report`), made live by the contract path | fixed | `ecd7e6652` | the goal request refused in A (its focus named the protected-only facet), sent in B |
| F38 | High | Saved relatedness loadings retain protected-only facets | stage | fixed | `ecd7e6652` | with learned coupling on: the frozen loadings, forecasts and scores naming `SENTINEL_FACET_AX9`, and the judgment ids frozen with them |
| F39 | Medium | Protected selections still change report counts and windows | stage | fixed | `ecd7e6652` | the report's and `ad report`'s serve draws, mode shares, time to usable, commission draws and prior-sensitivity cohort |

### What changed (R1)

- **F20, exposure.** `serve_inputs.pre_exposed(..., view=)` gives the incumbent's rule
  (`serve_eligibility.submit_exposure`) the view's reveals of the item or its LO, and the item's
  last visible attempt as the window's opening. Both AD callers use it: the slot's check 0 and the
  frozen `pre_exposed` of the serve inputs.
- **F20, recent reveals.** The slot's exclusions (`ad_slot._exclusions(env, view)`) take the
  recent-reveal set with the view's withheld reveal ids left out
  (`MaterialView.withheld_reveal_ids`). Two new optional parameters carry this,
  `out_of_timing_serving_exclusions(exclude_reveal_ids=)` and
  `items_revealed_between(exclude_ids=)`; omitted, both read exactly as before, so the incumbent
  is unchanged.
- **F34, grounding identities.** A commissioned request's guard now revalidates source identities
  against fresh protection at every dispatch, the repair included. It checks two sets:
  - its context's source refs (`proposals.context_sources`: each ref's extraction and spans);
  - the grounding spans the generator registers (`CommissionedRequestGuard.ground`). The
    cross-source generator registers every `CROSS_SOURCE_CONTEXT` span through
    `_ad_request_options(plan, grounding=)`.

  A span held out since the request was built refuses the request, whether or not any item
  derives from it.

  The guard protocol gains a `sources` keyword, which `_check_request` passes. The repair pass
  replaces the instructions, so a cross-source repair does not re-quote its spans. It is refused
  anyway: the ruling revalidates every grounding span at each dispatch.
- **F37, goal focus.** Under the contract, `build_goal_practice_plan` takes its focus from
  `adaptive_difficulty.generation.goal_focus_facets`. This returns the visible facets of the scope's
  LOs whose AD forecast of an unassisted success at the retrieval entry point is below the goal's
  `target_recall`. The forecast is AD's own state on visible evidence. The predecessor path keeps
  `goal_report`.
- **F38, loadings.**
  - `relatedness.load_structure` revalidates each saved revision unit. A revision that is withheld,
    judged by its own sources (`MaterialView.revision_hash_withheld`), has no unit. A loading onto
    a protected-only facet is dropped (`MaterialView.visible_loadings`).
  - The replay revalidates frozen `loadings_json` the same way.
  - `serving.frozen_loadings` freezes only the judgment ids behind the loadings still in force.
  - The ledger and the frozen rows are never rewritten.
- **F39, the selection cohort.** `MaterialView.selections(kind=)` leaves out three kinds of
  selection:
  - a draw that chose a withheld item;
  - a draw into a presentation withheld with its frozen revision;
  - a commission of a protected-only facet's cell.

  The report's selection statistics, its window boundaries (`readiness_errors`), its prior
  sensitivity and "why this item" all read through it. `MaterialView.open_commissions` drops the
  same commissions. The ledger is unchanged.

### R2, the differential contract

`tests/test_ad23_contract.py::test_protected_material_is_indistinguishable_from_absent_material`
is parametrized `default` (the owner's `learned_coupling` off) and `coupled`. The module docstring
lists the fixture's protected classes: every class the verifies named, including those added
this round. AD's full pipeline runs on each copy:

- the plan serves with the slot draw and an answer;
- the replay, its rebuild and the score rebuild;
- the outside forecasters, as `llm_v3` dispatched from the serves' frozen inputs;
- item preparation (the feature audit, then `llm_v1:item`);
- generation and commissions:
  - the commission draw with commissioned post-probe generation;
  - goal generation and cross-source generation, each with its repair request;
  - a Reader-cited post-probe generation with its repair;
  - the cross-source and cited requests see a grounding span held out while in flight;
- relatedness, readiness and the router card;
- the dose arm with late uptake callbacks;
- the reading sweep;
- the report, `ad report` and `ad eval`.

**What is compared.**
- every prompt captured by the fakes;
- the new rows of every table (`sqlite_master`, not a hand list), apart from nine incumbent
  tables (`OUT_OF_SCOPE`, each named with its reason; no AD module reads any of them):
  - the incumbent's answer pipeline: `attempt_completion_work`, `attempt_debug_payloads`,
    `attempt_surprise`, `hypothesis_recurrence_state`, `learning_object_mastery`,
    `learning_outcome_labels`;
  - its item-state sync: `practice_item_state`, `facet_recall_state`,
    `facet_capability_evidence`;
- the DERIVED replay tables, whole;
- every returned figure.

The test fails on any difference, on any sentinel in a captured request, and on any request
dispatched after a span was held out that quotes it.

**Construction of B.** B is the copy where the protected material was never written: physically
absent, and so is everything derived from it, the incumbent's state included. A copy with the rows
deleted afterwards would keep incumbent state computed from them. That would hide exactly the
F21/F37 class (an AD decision reading incumbent evidence).

**Normalisations** (the complete list):
1. Wall-clock stamps with sub-second digits (`WALL_CLOCK`): the model-call records' own clock.
2. The report's `protection` disclosure block and `generated_at` (`DISCLOSURE`).

Every other id and stamp is made identical at the source:
- ULIDs and uuid4 ids (the judgment ledger, the model-call records) mint per stage from fixed
  counters;
- the clocks are frozen;
- both copies run at one root path, so a hash over `vault_root` matches.

**Carve-outs**, each excluded at its one field by name (`_carve_outs`, `INCUMBENT`): the
incumbent's `mastery_ekf` comparator. Its receipt rows are left out, and the copy of it that
`llm_v3`'s frozen state quotes (`outside._incumbent_inputs`) is pinned to one value in both runs.
This follows round 9's boundary, the round-10 verify's judgment (c) and R2. `ad data-check` is not
in the pipeline.

**Stage coverage** is asserted too, so that nothing is equal by being absent:
- `pi_p4` is a slot candidate;
- the goal request and its repair are both made;
- the public and late grounding texts reach their first requests;
- forecasts and preparation run.

The per-reader tests of rounds 9 and 10 stay.

**Fail-before** (`git archive e005188fe` into `fixtures-local/ad23-r11-base`, `-o pythonpath`,
counted with `AD23_CONTRACT_DIFF`):

| Config | Distinct violations on `e005188fe` | At the tip |
|---|---|---|
| `default` | **31** | 0 |
| `coupled` | **41** | 0 |

By finding:
- **F20:** `pi_p4` fails `pre_exposed` and `recent_reveal` in both serves' estimates and in both
  selections' `excluded`.
- **F34:** the cited repair quotes the late-protected span, and neither the cross-source nor the
  cited repair is refused.
- **F37:** the goal request is refused in A (its focus named the protected-only facet) and sent in
  B. The proposals, agent runs and prompts differ with it.
- **F39:** 9 figures in the report and 9 in `ad report` differ (serve draws 3 against 2, band
  share, time to usable, answers before band, commission draws, prior sensitivity).
- **F38** (`coupled` only): the frozen loadings and the judgment ids frozen with them name
  `SENTINEL_FACET_AX9`, and the serve receipts' `p`, their inputs and the scores differ.

The stage-coverage assertion also fails (the goal request is never made in A).

### Behaviour changes worth knowing

- Under the contract, a goal's generation focus is AD's forecast against `target_recall`, not the
  incumbent's goal projection.
- A cross-source or cited commissioned request is refused when a span it grounds in, or cites, is
  held out before any of its dispatches. This includes a repair that would not re-quote it.
- A commission of a protected-only facet's cell is not open.
- With learned coupling on, a protected-only facet carries no loading, saved or frozen.

### Gate (this round; owner rule 2026-10-17: targeted only)

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 27 kept, 0 broken |
| `test_ad23_contract.py` with `test_ad23_fix_r9.py`, `test_ad23_material_view.py`, `test_ad23_fix_review.py`, `test_ad3_dose_arm.py` | 54 passed (the contract file: 15 tests, the differential in both configurations) |
| targeted pytest, `uv run pytest -n 16` over 158 files: round 10's 157 and every test naming `out_of_timing_serving_exclusions`, `items_revealed_between`, `pre_exposed`, the goal or cross-source generators, `load_structure`, `frozen_loadings`, `why_for_presentation`, `open_commissions`, `serving_exclusions` or `reveal_events` | **8,425 passed, 36 xfailed, 6 failed** (1,649 s) |
| the six failures | all in `test_ad2_serving.py`: test doubles of the private `ad_slot._exclusions(env)`, whose signature gains the slot's view; updated to `(env, view)` |
| rerun: `test_ad2_serving.py` | 34 passed |
| `--durable-sqlite`: `test_ad23_contract.py`, `test_ad23_fix_r9.py`, `test_ad23_fix_r8.py`, `test_ad23_migration.py` | 39 passed |
| references: `db_generate_reference.py`, `db_validate_reference.py` | 0 errors (commit labels; no schema change) |
| migration 214, defaults snapshots, CLI help, vitest, `cargo check` | unchanged or not applicable (no frontend change) |

### For the next verify

The differential test is now the contract. A finding should name an AD reader the pipeline
reaches, together with a class of protected material the fixture lacks. Adding that material to
`_protect` should then make the test fail. The incumbent tables left out of the comparison are
listed in `OUT_OF_SCOPE`, each with its reason.

## Fix round 12: goal scope, relatedness provenance, canonical notes, and a hardened contract (2026-10-20)

Codex's verify of round 11 (codex-job `20261020-141057-jGLYeA`, verdict REOPENED) confirmed:

- F20, and F34's grounding-span fixes;
- the owner defaults, A17's `0.25`, migration 214 and the head fixture;
- the history fallback, the report windows, the 7-day expiry and cancellation-preserving retry.

It found three Highs (F37 and F38 reopened, F40) and three Mediums (F39 reopened, F41, F42). The
orchestrator's rulings (binding) are implemented in commit `74e65c7db`, with no migration change.

**Restoring this file.** Round 11's record commit (`044f363ca`) truncated this file to its own
section. The script opened the file for writing before reading it. This commit restores rounds 1-10
from `e005188fe` verbatim, keeps the round-11 section as committed, and adds this section.

| Id | Severity | Title | Origin | Verdict | Commit | Test (each fails on `044f363ca`) |
|---|---|---|---|---|---|---|
| F37 | High | Goal generation still resolves scope from protected items | round 11 (scope resolved before the view) | fixed (ruling 1) | `74e65c7db` | `test_a_goal_over_a_facet_only_a_protected_item_measures_has_no_scope`; the differential (`goal_r12`) |
| F38 | High | Relatedness judgments retain influence from protected prompt context | stage | fixed (ruling 2, the blunt rule) | `74e65c7db` | `test_a_saved_run_proposed_before_its_subject_was_protected_is_not_used`; the differential (`coupled`: the stale run's coupling, loading and frozen judgment ids) |
| F40 | High | Protected canonical notes enter commissioned prompts | inherited (`build_authoring_context`), made live by the contract path | fixed (ruling 3) | `74e65c7db` | `test_a_held_out_sources_canonical_note_never_reaches_a_commissioned_request`; the differential (`SENTINEL_NOTE_AX9` in eight captured requests) |
| F39 | Medium | Protected empty-support selections still affect reports | round 11 (the cohort read the choice and the cell only) | fixed (ruling 4) | `74e65c7db` | `test_an_empty_support_draw_of_a_protected_slot_leaves_the_report_cohort`; the differential |
| F41 | Medium | Goal focus ignores `promoted_predictor=false` | round 11 | fixed (ruling 5) | `74e65c7db` | `test_goal_focus_follows_the_live_decision_view_with_promoted_predictor_off` |
| F42 | Medium | The differential contract can conceal missing stages and meaningful differences | round 11 | fixed (ruling 6) | `74e65c7db` | the hardened differential itself (its fail-before below) |
| (new) | High | A protected reading receipt moves the serve sweep's window | stage | fixed | `74e65c7db` | found by the hardened differential: with the production Reader mapping, a public exposure was recorded at the serve in the absent copy and only at the backfill in the protected one |

### What changed

- **F37 (ruling 1).** Under the contract, `build_goal_practice_plan` resolves the goal's scope on
  `MaterialView.vault_view()` before planning. A facet only a withheld item measures brings no LO
  in. The LO-to-facet mapping is kept through to the focus: `goal_focus_facets(scope=...)` reads
  each LO's scope facets.
- **F38 (ruling 2, the blunt rule).**
  - Recording: each relatedness run records its subject's protection fingerprint at proposal time,
    as a reserved unit (`relatedness.PROTECTION_UNIT`, so no schema change). The fingerprint is a
    digest of the withheld current items and saved revisions of the subject's LOs, each by item id,
    revision hash and source identity (`protection_fingerprint`).
  - Using: at `load_structure` and in the replay, a run whose subject's current fingerprint differs
    is not used. Its LO couplings and its loadings are all dropped. A run without a fingerprint
    (recorded before this round) is not used either. Frozen `loadings_json` that names a judgment of
    such a run (`stale_judgments`) is dropped, and `serving.frozen_loadings` never names one.
    `touched_units` counts only runs under the current protection, so once protection changes,
    every unit is re-proposed.
  - No model call is made in the replay.
  - The round-11 per-loading revalidation stays for runs under the current protection.
- **F40 (ruling 3).**
  - Filtering: `vault_view()` leaves out a note whose source holds held-out material. A source
    revision names its canonical note (`source_revisions.note_id`). The note is withheld when any
    of that revision's extractions holds held-out material (`note_withheld`).
  - Revalidating: `context_sources` now returns typed identities, spans and the included notes.
    The guard revalidates notes against fresh protection at every dispatch, repairs included.
- **F39 (ruling 4).** `MaterialView.selections()` revalidates the originating `slot_item_id` and
  its presentation as well as the chosen item, for every selection kind, empty support included.
- **F41 (ruling 5).** `goal_focus_facets` predicts with `serving.view_for()` per LO: the subject
  view only while `promoted_predictor` is on.
- **New, found by the contract.** A serve's reading sweep bounded its window by the newest receipt
  of any source, a withheld one included. It now uses the newest visible receipt
  (`MaterialView.reading_opportunities`).
- **Item state (ruling 6, the exclusion audit).** AD reads `practice_item_state` through
  `MaterialView.item_states()`. This covers the slot's `StagedFrame` admission (a new optional
  `item_states` reader; omitted, the plan reads the repository as before) and generation's
  active-item helpers (a new optional `states=`). It returns visible items only, with their
  lifecycle `active` flag. The fields the incumbent's scheduler derives from answers read as a
  fresh item's. AD's candidates are never-attempted items, so a public candidate reads exactly
  what it did. `practice_item_state` is compared through that reader (`COMPARED_THROUGH_VIEW`) and
  is no longer excluded.

### F42 (ruling 6): the hardened contract

- **Stages must have an effect.** Every claimed stage now asserts a successful, non-empty effect,
  identically in both copies:
  - the replay and the score rebuild persisted rows in all three DERIVED tables;
  - the reading sweeps wrote receipts;
  - the public dose offer's delivery was recorded;
  - a relatedness run was recorded with status `ok` (with learned coupling on; `disabled` by
    default);
  - every `llm_v3` forecast status is `ok`;
  - the serve-time commission was queued and completed by the worker, which made its request;
  - the protected-facet goal has no scope;
  - the read trace saw AD's reads.
- **No normalisation of stamps.** Wall-clock stamps are no longer replaced. The model-call
  records' own clock (`datetime.now` in `ai.execution` and the model-call store) is frozen at the
  source, like the other clocks, so no stamp is normalised. The one rewritten field is a disclosure
  that differs by construction: a relatedness run's recorded fingerprint, compared by meaning
  (whether it equals the subject's current fingerprint in that copy). Together with the report's
  `protection` block and `generated_at` (`DISCLOSURE`), that is the complete list.
- **Production paths.** The extraction has a real document IR and source revision. The production
  `VaultReadingMap` serves the dose arm and the sweeps, and LO provenance maps the sections. The
  serve-time commission goes through `schedule_commission_generation`, the durable ingest queue and
  its worker (`DurableIngestJobs`, foreground).
- **Exclusions justified by traced reads.** The harness traces every table an AD reader reads,
  transitively, through SQLite's authorizer on every connection (`_trace_ad_reads`). AD readers are
  the `adaptive_difficulty` modules, `ad_slot`, and the generation path under the contract. The
  incumbent's own maintenance (`sync_vault_state`, the self-graded attempt) is not counted. The
  test fails if AD reads an `OUT_OF_SCOPE` table. The one exception is the named carve-out:
  `learning_object_mastery`, read only by `adaptive_difficulty.forecasters`, the `mastery_ekf`
  comparator.

  The traced run reads 81 tables. Of the nine round-11 exclusions:
  - seven are read by no AD path: `attempt_completion_work`, `attempt_debug_payloads`,
    `attempt_surprise`, `hypothesis_recurrence_state`, `learning_outcome_labels`,
    `facet_recall_state`, `facet_capability_evidence`;
  - `learning_object_mastery` is read only by the carve-out;
  - `practice_item_state` is read by `material_view` and generation (now through the view), so it
    is compared.
- **New fixture classes** (protected copy):
  - a goal naming only the protected-only facet;
  - a later relatedness run, proposed before the protection, with an LO-to-LO coupling and a
    public-to-public loading;
  - the held-out source's canonical note;
  - an empty-support draw of a slot planned with the held-out item.
- **The `mastery_ekf` carve-out** is unchanged and named exactly as before.

**Fail-before** (`git archive 044f363ca` into `fixtures-local/ad23-r12-base`, `-o pythonpath`; the
harness reads the base's own item-state reader where `item_states` does not exist):

| Test | On `044f363ca` | At the tip |
|---|---|---|
| differential, `default` | **366 violations**, and the stage assertion fails (the protected-facet goal had a scope) | 0 |
| differential, `coupled` | **367 violations**, the same | 0 |
| the five focused round-12 tests | 5 of 5 fail | pass |
| the whole contract file | 7 of 20 fail (the two differential runs and the five focused tests) | 20 pass |

The violations come from these root causes:
- **The serve sweep's window.** It shifts every later id and stamp in the serve stage, hence most
  of the count: forecast receipts, scores, measurement and grading rows, selections, presentations,
  block events.
- **F40:** `SENTINEL_NOTE_AX9` appears in 8 captured requests.
- **F37:** the protected-facet goal resolves a scope in A.
- **Item state:** `pi_p4` and `pi_hist` read their answer-derived fields.
- **F39:** the empty-support draw stays in the report's cohort.
- **F38 (`coupled`):** the stale run's judgment is in the frozen loadings.

### Owner notes

- **Protecting material in a subject resets its learned coupling.** AD predicts there with no
  learned coupling until the owner re-proposes that subject's relatedness and adopts the new
  version. The same happens when material is released. `learned_coupling` is off by default
  (owner decision 2026-10-19), so this affects only an adopted version. Runs recorded before this
  round carry no fingerprint and are not used: the owner re-proposes once after turning learned
  coupling on. Recorded in the spec, §5.10.
- **What AD reads of the scheduler's item state.** AD reads only an item's lifecycle (`active`),
  never its due date or memory state. Its candidates are never-attempted items, so nothing changes
  for a public candidate.

### Gate (this round; owner rule 2026-10-17: targeted only)

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 27 kept, 0 broken |
| targeted pytest, `uv run pytest -n 14` over 163 files: round 11's 158 and every test naming `StagedFrame`, `resolve_goal_scope`, `scope_facets`, `vault_view`, `context_sources` or `items_revealed_between` | first run: **8,541 passed, 36 xfailed, 1 failed**. The failure was `test_architecture` (material_view imported the repository's private `_practice_item_state`); fixed by reading `repository.practice_item_states()` |
| rerun after that last code change, the whole 163 files | **8,542 passed, 36 xfailed, 0 failed** (2,114 s) |
| `--durable-sqlite`: `test_ad23_contract.py`, `test_ad23_fix_r9.py`, `test_ad23_fix_r8.py`, `test_ad23_migration.py` | 44 passed |
| references: `db_generate_reference.py`, `db_validate_reference.py` | 0 errors (commit labels; no schema change) |
| migration 214, defaults snapshots, CLI help, vitest, `cargo check` | unchanged or not applicable (no frontend change) |

Two existing tests changed with the rules:
- `test_ad3_relatedness`: a run's units now include the reserved protection unit.
- `test_ad23_fix_r8`'s sensitivity case: it now reserves a support member that is neither the
  draw's choice nor its slot item, since reserving either drops the draw from the cohort (F39).

## Fix round 13: recorded prompt context, protected note exchanges, view-counted caps, a deeper contract (2026-10-20)

Codex's verify of round 12 (codex-job `20261020-162449-eEf7LH`, verdict REOPENED) confirmed:

- F37, F39, F40's prompt path, F41 and the sweep window;
- migration 214 and the head fixture;
- the owner defaults and the replay boundaries.

It found F38 (reopened), F43 and F44 (High), and F45 and F42 (Medium). The orchestrator's rulings
are implemented in commit `f38ba8384`, with no migration change: no UNIQUE constraint in 214 forced
one. This section was appended to the file, not written over it.

| Id | Severity | Title | Origin | Verdict | Commit | Test (fails on `696ff2e9f`) |
|---|---|---|---|---|---|---|
| F38 | High | The protection fingerprint loses historical prompt context | round 12 | fixed (ruling 1) | `f38ba8384` | `test_a_run_whose_quoted_revision_was_replaced_then_protected_is_not_used`; the differential's temporal case (pinned: the public run out of use) |
| F45 | Medium | A re-proposal can stay "current" after invalidation | round 12 | fixed (ruling 2) | `f38ba8384` | `test_a_stale_run_never_answers_for_a_re_proposal`; the differential's temporal case (pinned, coupled: the re-proposal is made) |
| F43 | High | Protected canonical-note tutor exchanges still enter predictions | stage | fixed (ruling 3) | `f38ba8384` | `test_a_tutor_exchange_on_a_protected_canonical_note_enters_no_prediction`; the differential (`qe_note_r13`) |
| F44 | High | Protected receipts still consume reading caps | stage | fixed (ruling 4) | `f38ba8384` | `test_a_protected_receipt_occupies_no_daily_cap_slot`; the differential (`sxe_held_r13`'s receipt) |
| F42 | Medium | The hardened contract still misses reads and permits missing stages | round 12 | fixed (ruling 5) | `f38ba8384` | the contract itself (fail-before below), `test_every_ad_cache_and_file_read_is_audited`, `test_the_replay_cache_never_serves_a_snapshot_across_a_protection_change` |

### What changed

- **F38 (ruling 1).**
  - What a run records: every run records its whole prompt context as a reserved unit
    (`relatedness.CONTEXT_UNIT`; no schema change). That is every item revision the prompt quoted,
    with its source identity, including context outside the proposed units.
  - When a run is used: `run_in_force` holds only if three things are true:
    - the run's subject fingerprint is the current one (round 12's subject-wide rule stays);
    - it recorded a context;
    - nothing in that recorded context is protected now (`context_protected`: the item is
      withheld, its revision is withheld, or its recorded source identity lies in held-out
      material).

    Replacing, deleting or re-scoping an item cannot hide its old revision's protection.
  - Who applies it: `load_structure`, `stale_judgments` (frozen loadings), `touched_units` and the
    duplicate check.
  - Legacy runs (no fingerprint, or no recorded context) are never in force.
- **F45 (ruling 2).** The run key and the claim key carry the run's protection identity
  (`protection_identity`: the subject fingerprint and the recorded context, never in the prompt).
  The duplicate check accepts only a run that is in force, so a stale successful run never answers
  "current".
- **F43 (ruling 3).**
  - Collection: the sweep rejects a tutor or library question on a withheld note before any
    fallback to its item (`_note_withheld`).
  - The map: `VaultReadingMap.los_for_note` reads through the view (`note_withheld`).
  - Receipts: revalidating a receipt withholds a question-event receipt whose note is withheld.
- **F44 (ruling 4).**
  - Occupancy: the cap occupancy of passage views (1 per LO per day) and of tutor exchanges (3) is
    counted over the receipts the view sees (`reading.occupancy`), and kept up to date as the sweep
    writes.
  - Keys: a capped receipt's key names its source event
    (`<bucket>:<lo>:<day>:<source_table>:<source_id>`), so keys never collide and a public event is
    admitted beside a withheld receipt's existing key. Old keys stay as written.

### F42 (ruling 5): the contract, hardened again

- **The read trace** opens its connections with `cached_statements=0`, so every execution prepares
  afresh and a cached statement cannot hide a read. It records each read with its database identity
  (file and schema name).
- **The audit of Python-side caches and file-backed reads.** `AD_DEPENDENCIES` lists every
  module-level cache and file read in the AD modules, with how protection reaches it:
  - the replay's snapshot cache, served only while the fingerprint of the view's events is
    unchanged (a behavioural test shows a narrower view is not served from it);
  - its lock;
  - the numeric inverse memo;
  - the guard's fresh `load_vault`;
  - the document IR load.

  `test_every_ad_cache_and_file_read_is_audited` scans the AD modules and fails on any unlisted one.
- **Pinned outcomes.**
  - Readiness: exactly the cells (`apply_pub`, `recall`) at retrieval, as predictions in range.
  - The card: its cell, kind and ordering, equal to readiness at the top.
  - The dose decisions: eligible, no refusal.
  - The late uptake callbacks: none recorded.
  - Item preparation: exactly the four prepared items, each audited and `llm_v1` ok.
  - The temporal outcomes and the expiry boundary.
- **A second run mode.** The clock advances an hour per stage, identically in both copies, beside
  the frozen mode. It advances by the harness's steps, not by read counts, which are incumbent
  behaviour. Expiry boundary: a public commission expires two and a half hours into the run. It is
  open at the start in both modes, and expired at the end only on the advancing clock.
- **Temporal scenarios**, the same events in both copies:
  - pi_p3's source-backed revision (never served or audited, so in no snapshot) is replaced, then
    its former source held out. The public run must then be out of use: no coupling, no loading.
  - The subject is proposed; then a saved historical revision's source is held out while the prompt
    stays the same, and it is re-proposed. With coupling on, both are made, never "current".
- **Protected classes added** (protected copy only):
  - a tutor exchange on the held-out source's canonical note;
  - a passage-view receipt from a held-out span occupying the LO's daily slot on the day a public
    view waits;
  - a held-out reading receipt stamped exactly as the public one (an ordering tie).

**Fail-before** (`git archive 696ff2e9f` into `fixtures-local/ad23-r13-base`, `-o pythonpath`):

| Test | On `696ff2e9f` | At the tip |
|---|---|---|
| differential, default/frozen | **37 violations**; F38's pinned temporal outcome fails | 0 |
| differential, default/advancing | **37**; the same | 0 |
| differential, coupled/frozen | **37**; the same (and F45's, behind it) | 0 |
| differential, coupled/advancing | **37**; the same | 0 |
| the four focused round-13 tests | 4 of 4 fail | pass |
| the whole contract file | 8 of 28 fail | 28 pass |

The 37 violations are F43 and F44: the protected note exchange recorded, and the public passage
view dropped. They show up in the receipts, the replay state, the scores, the serve forecasts and
the selections.

### Owner notes

- A relatedness run now also records the prompt context it was proposed with. A run is used only
  while none of that context is protected and its subject's protection is unchanged. Protecting
  material (or releasing it) in a subject still resets that subject's learned coupling until it is
  re-proposed and re-adopted. Runs recorded before this round are not used. `learned_coupling` stays
  off by default.
- A Reader or library tutor exchange on a source's canonical note stops counting as reading as soon
  as that source holds held-out material.

### Environment

No ad-hoc Python touching LearnLoop ran outside pytest this round. The only scripts outside pytest
were file-editing scripts (standard library only) and the two reference scripts. The reference
scripts ran under `env -i` with an empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, and make
no model call.

### Gate (this round; owner rule 2026-10-17: targeted only)

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 27 kept, 0 broken |
| the AD test files (contract, r8, r9, material view, fix review, dose arm, relatedness, subject view, reading, reading opportunities, serving) | 148 passed |
| targeted pytest, `uv run pytest -n 14` over round 12's 163 files, run once after the last code change | **8,550 passed, 36 xfailed, 0 failed** (1,859 s) |
| `--durable-sqlite`: `test_ad23_contract.py`, `test_ad23_fix_r9.py`, `test_ad23_fix_r8.py`, `test_ad23_migration.py` | 52 passed |
| references: `db_generate_reference.py`, `db_validate_reference.py` (under `env -i`) | 0 errors (commit labels; no schema change) |
| migration 214, head fixture, defaults snapshots, CLI help, vitest, `cargo check` | unchanged or not applicable |

One existing test changed with the rules: `test_ad3_relatedness` (a run's units now include both
reserved protection units).

## Fix round 14: tutor context, dose origin, the background scheduler, and controls (2026-10-20)

Codex's verify of round 13 (codex-job `20261020-175808-RoJ26Y`, verdict REOPENED) confirmed:

- F38's recorded context, F43 and F44;
- migration 214 and the head fixture;
- the owner decisions, switch-off, the replay and write isolation.

It found F46 and F47 (High), and F45 (reopened) and F42 (Medium). The fixes are in commit
`a209efcf5`, with no migration change. This section was appended.

| Id | Severity | Title | Origin | Verdict | Commit | Test (fails on `a3ae61099`) |
|---|---|---|---|---|---|---|
| F46 | High | Tutor exchanges ignore protected secondary prompt context | stage | fixed | `a209efcf5` | `test_a_tutor_exchange_whose_recorded_context_quotes_a_protected_span_enters_no_prediction`; the differential (`qe_context_r14`) |
| F47 | High | Protected originating sections still spend dose budgets | stage | fixed | `a209efcf5` | `test_a_dose_draw_at_a_protected_origin_is_a_draw_never_made`; the differential (`dose_origin_r14`: the public boundaries' `daily_budget`) |
| F45 | Medium | Background scheduling still counts context-invalid runs as current | round 13 | fixed | `a209efcf5` | `test_the_background_scheduler_sees_a_run_whose_recorded_context_is_protected`; the differential's temporal case (pinned: `stale_subjects` finds the subject) |
| F42 | Medium | The contract still permits missing behaviour and misses actual caches | round 13 | fixed | `a209efcf5` | the audit, the pinned dose draws, the one clock, and five negative controls (below) |

### What changed

- **F46.** `MaterialView.question_event_withheld` is the one protection reader of a tutor question.
  It judges the question's complete recorded source context: the anchor (`note_id`, a span key or a
  canonical note), its item, and every mapping with an extraction id in `source_context`. That
  covers the anchor, `source_spans`, `citations`, retrieval and delivery records. The sweep's tutor
  and library collection uses it before any mapping or fallback to an item, and so does receipt
  revalidation.
- **F47.**
  - `MaterialView.dose_draw_withheld` withholds a draw whose originating section (the boundary it
    was drawn at) is withheld, as well as one whose extra is.
  - It filters the cohort (`dose_rows`, so the budget, taken offers, density lowerings and offer
    outcomes), saved-draw retrieval in `decide`, and uptake.
  - A new decision at a withheld section is refused before the section is mapped
    (`withheld_section`). A draw made there earlier is returned with no offer (`withheld`).
- **F45.** `relatedness_jobs.stale_subjects` reads runs exactly as `propose_subject` does: through
  the view, with `run_in_force`. A run whose recorded context is protected now leaves its units to
  be proposed again.

### F42: the contract

- **The audit uses actual module state.** It covers every module-level dict, set, list, deque or
  `lru_cache` that its module mutates at runtime (found by AST: mutating calls, subscript stores,
  `global`), in every AD module and in the authoring and reading modules AD calls
  (`AUDITED_MODULES`). It also covers every file read there (`load_vault`, `load_document_ir`,
  `read_text`, `read_bytes`, `open`). Each is listed in `AD_DEPENDENCIES` with how protection
  reaches it:
  - background's `_PREPARED`, `_QUEUES`, `_INFLIGHT` and `_DEFAULT`;
  - the replay cache;
  - the inverse memo;
  - the generators' and the authoring call's `load_vault`;
  - the IR loads.

  The test also fails on a listed entry that no longer exists. A mutable module-level table that
  nothing mutates is a constant and needs no entry.
- **The pinned dose draws are the operation's own.** The draws the dose decisions made in the run
  are pinned: the row persisted now, at its boundary key, with its recorded propensities
  (`{"none": 1.0}`) and its chosen variant (`none`, no offer). The seeded delivery stays a separate
  check.
- **One clock.** There is one monotone operation clock (`_OP`). In advancing mode it gains an hour
  at every stage in the order the stages run, never by stage number, from `RUN` at the start of
  each copy's run. Every explicit clock, `now`, `as_of` and `served_at` in the run reads it, and the
  `_Frozen(RUN)` holdouts are gone from the run. The focused tests keep their own fixed clocks.
- **Negative controls.** Each control makes a test-only mutation, identical in both copies, and the
  contract then FAILS:
  - the dose operation removed: the pinned persisted draws are missing;
  - the background `stale_subjects` reporting nothing: the temporal case fails;
  - the commission queue removed: the worker stage fails;
  - the replay cache's protection removed (a constant events fingerprint): the cache test fails;
  - the view's receipt revalidation removed: the comparison fails.
- **Temporal case.**
  - s0: the subject is proposed: `current`, nothing changed.
  - s1: a saved revision's source is held out, and the subject is re-proposed.
  - s2: pi_p3 is replaced and proposed, so only its new revision is asked.
  - s3: pi_p3's former source is held out. The fingerprint is unchanged, but s1's recorded context
    is now protected. `runs_in_force` must be `[False, False, True]`, the background scheduler must
    find the subject stale, and the re-proposal is made.
- **Fixture changes.** The held-out spans move to their own section (`sec5`), so a public section
  is a public origin. The daily dose budget is two, so one draw decides it.

**Fail-before** (`git archive a3ae61099` into `fixtures-local/ad23-r14-base`, `-o pythonpath`):

| Test | On `a3ae61099` | At the tip |
|---|---|---|
| differential, each of default/frozen, default/advancing, coupled/frozen, coupled/advancing | **342 violations**; the pinned dose assertion fails (`daily_budget` at both public boundaries) | 0 |
| the three focused round-14 tests | 3 of 3 fail | pass |
| the whole contract file | 8 of 36 fail | 36 pass |

The violations have two root causes:
- **F46:** the protected-context exchange is recorded in A, which shifts every later id of the serve
  stage.
- **F47:** the protected-origin draw spends A's daily budget.

### Owner notes

- A tutor exchange stops counting as reading once ANY span it was given or cited is held out, not
  only its anchor.
- A dose offer drawn at a section that is held out now counts as never made. It spends no daily
  budget, and no new offer is drawn there.

### Environment

No ad-hoc Python touching LearnLoop ran outside pytest. The other scripts were standard-library
file editors, plus one read-only schema read of the migration head fixture under `env -i`. The
reference scripts ran under `env -i` with an empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

### Gate (this round; owner rule 2026-10-17: targeted only)

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 27 kept, 0 broken |
| the AD test files (contract, r8, r9, material view, fix review, dose arm, relatedness, subject view, reading, reading opportunities, serving) | 155 passed, 1 failed; the failure was `test_ad23_fix_r8`'s saved-draw case, which a decision at a withheld origin now answered `withheld_section`. Fixed in code: a saved draw at a withheld origin is returned as `withheld` with its id, and only a new decision there is `withheld_section`. The dose and contract tests then passed (20, and 36 in the contract file) |
| targeted pytest, `uv run pytest -n 14` over 179 files (round 13's 163 and every test naming `relatedness_jobs`, `stale_subjects`, `record_uptake`, `dose_rows` or `question_events`), run once after the last code change | **8,908 passed, 38 xfailed, 0 failed** (1,528 s) |
| `--durable-sqlite`: `test_ad23_contract.py`, `test_ad23_fix_r9.py`, `test_ad23_fix_r8.py`, `test_ad23_migration.py` | 60 passed |
| references: `db_generate_reference.py`, `db_validate_reference.py` (under `env -i`) | 0 errors (commit labels; no schema change) |
| migration 214, head fixture, defaults snapshots, CLI help, vitest, `cargo check` | unchanged or not applicable |

## Redesign (Option B + E1 + E2): guarded AD operations (2026-10-21)

There was no fix round 15. The round-14 verify (`20261020-191113-0filV9`) reopened with F48 and F49
(High) and F50 and F42 (Medium). Under the owner's rule after round 14 (no more point fixes), an Opus
architecture review proposed a structural redesign. The owner decided its open questions, and the
redesign implements its recommendation: Option B with E1 and E2.

### Diagnosis (summary of the review)

Fourteen rounds filtered protected material **at each reader**: a hand-written chain in the material
view per table, with injection parameters into shared helpers. Each verify then found a reader, a
helper, a cache or a count the chains had missed:

- F48: the Reader's whole-section mapping resolved provenance against the raw IR;
- F49: the preparation batch was sliced before it was filtered;
- F50: a process cache kept protected outcomes as done;
- F42: the contract could not enumerate what it did not trace.

The defect was structural. Nothing stopped a read; the contract could only compare outputs, and only
for the paths it exercised. Option B moves the boundary to the data sources:

- an AD operation refuses any read the rules do not make;
- it hands AD a projection in which held-out material is absent, not filtered;
- one epoch scopes everything computed from that projection.

### Decisions (binding)

| | Decision |
|---|---|
| Owner Q1 (E1) | A8 ends at AD's commission target plus the egress guard. The generator's internals are governed by the incumbent's exam protection; the generation protections already built stay as built, not extended. |
| Owner Q2 (E2) | One vault-wide protection epoch. Any protection change resets an adopted learned coupling and expires pending background forecasts. |
| Owner Q3 | A guard denial in production fails closed: AD is unavailable for that operation, with incumbent behaviour. The denial is logged and `learnloop ad report` shows a denial count. No UI notice. |
| Orchestrator Q4 | The next verify runs against the proposal's §3.5 closed checklist (below). |
| Orchestrator Q5 | No separate Option-A round: F48-F50 are fixed by construction (steps 4 and 5), with explicit cases in the epoch and projection tests. |
| Orchestrator Q6 | Step 6 only if the plan-building functions are proven read-only for a commissioned plan. **Skipped: they are not** (below). |

### Steps done

| Step | Commit | What |
|---|---|---|
| 1 | `07ac808ab` | `operation.py`: `ad_operation`, the `entry` decorator on every AD entry point, the guard (an SQLite authorizer, observe mode), the connection hook in `db/scopes.py` and `db/connection.py`. `material_view()` with no view is an error outside an operation (`detached_view` for the egress guards and the generation boundary). |
| 2 | `de6aa6454` | `protected_tables.py`: every table the step-1 trace saw (neutral, protected, predicate, denied), and every column of every protected table (a value or a reference kind). `MaterialView.keep` is the one rule; the readers became `rows` / `filter` / `lookup` / `stored` over it; the rules' SQL carries `/* ad-rules */`. |
| 3 | `e4435c678` | Deny mode. Every denial the AD test files surfaced was routed (see the commit): AD's raw reads through the view; the egress `suspended()`; the slot's incumbent constraints in the named incumbent scope; the plan's records read before the operation; the estimator's plan events injected; a write's own checks, triggers and `own_write`. |
| 4 | `96ebaa3e0` | The projected vault and IR (F48), the span-alias memo keyed by the projection, `load_vault` refused inside an operation. |
| 5 | `3993274d6` | The epoch (F49, F50; E2): keys-only preparation queue with admission inside the operation, `_PREPARED` and the replay cache by epoch, relatedness runs and frozen outside states stamped. The fingerprint machinery and the history re-judgment deleted. |
| 6 | (skipped) | Planning writes: `build_practice_expansion_plan` calls `curriculum.depth_rungs.select_rung`, which writes `task_feature_schema_versions` (`ensure_builtin_task_feature_schema`) and `capability_aliases` (`ensure_capability_alias_registry`). Under the guard both writes would be refused, so generation planning stays exactly as built (E1). |
| fixes | `a894722f1`, `30a3bd574` | What the new tests found: SQLite's column-read refusal ("access to T.C is prohibited") was not recognized as a denial; the incumbent activity and grading tables reclassified as denied; administrations and surfaces given their own rule; the report's denial count; a dead method. |
| 7 | `95345b0a1` | The new test contract (below); `test_ad23_material_view.py` deleted. |

### The contract now

- **The guard** (`operation.py`): while an operation is open, every connection to its database
  carries the authorizer, including the serve transaction's pinned connection (installed at entry,
  removed at exit) and connections handed to an entry point. Its rules:
  - a protected table is read only in the rules' scope (the material view);
  - a predicate table only while the predicate is computed;
  - a denied table never, except the `mastery_ekf` carve-out's two tables;
  - the incumbent's serve-time constraints only in `incumbent_constraints()`, and only by the
    registry's named incumbent readers;
  - a write only to an AD-owned table.

  Leaving the rules' scope expires every guarded connection's statement cache, so a statement
  prepared there is never reused unchecked. With AD off, no operation opens and nothing is installed.
- **The registry** (`protected_tables.py`): roles by name; every protected column classified. The
  named exceptions:
  - a frozen receipt whose source was deleted stands (F30);
  - a facet map (doses, loadings) drops facets only withheld material names.
- **The projection** (`MaterialView.projected_vault`, `document_ir`, `span_reanchors`;
  `projection.py`'s repository facade).
- **The epoch** (`operation.epoch_of`), stamped or keyed in:
  - relatedness runs (`protection:epoch`, and in their run and claim keys);
  - frozen outside states (`protection_epoch`; the send guard refuses any other epoch);
  - `_PREPARED`, the replay cache, and the span-alias memo (`projection_key`).

**Named, not closed** (for the verify's checklist):

- the incumbent's serve-time constraints on a visible candidate: the routine exclusions and the
  staged frame's admission read the incumbent's own state in the incumbent scope;
- the generator's internals (E1);
- non-SQL sources outside the vault and the IR;
- multi-client races (Medium by calibration; the egress guard re-reads at send).

### Deleted

- **Relatedness**: `PROTECTION_UNIT`, `CONTEXT_UNIT`, `context_protected`, `protection_fingerprint`,
  `protection_identity`, `subject_lo_ids` and the per-subject fingerprint loop of `stale_judgments`
  (replaced by the epoch).
- **The send guard**: `attempt_ids` and the history identities (`history_card`'s `identities` and
  `attempt_ids`, `MaterialView.answered_revision_items`, `attempt_withheld_by_id`); replaced by the
  frozen epoch.
- **Tests**:
  - `tests/test_ad23_material_view.py` (the AST scan);
  - from the contract: the advancing-clock mode, the coupled differential, the fingerprint-era
    temporal scenarios and their assertions, the read trace (`_trace_ad_reads`), the module-state
    audit (`AD_DEPENDENCIES`, `_mutated_names`, `_audit_sites`), the five negative controls, and the
    F33 history re-judgment test (the epoch test replaces it).

  The contract file went from 2,544 to 2,086 lines. It keeps the per-reader regressions of rounds
  8-14 that still apply and one default-config, frozen-clock differential as a smoke test.

**Sizes, `b1d082afb..HEAD`.**

- Production: +2,224 / -670 lines (net +1,554). The proposal estimated a net shrink of about 200;
  the net is a growth, for these reasons:
  - the guard is about 520 lines with its documentation;
  - the registry is about 420, most of it the explicit column listing;
  - the material view kept its per-entity predicates as the rule's resolvers, so the per-reader
    regressions stay the oracle (§3.1 step 2), and gained the rule, the projection and the new
    readers (+560 / -185);
  - the relatedness and send-guard deletions removed about 210 lines.
- Tests: +841 / -723 (net +118).

### New tests, fail-before

On `b1d082afb` (`git archive` into `fixtures-local/ad23-redesign-base`, the new files copied in,
`-o pythonpath="src ."`):

| Test | On `b1d082afb` | At the tip |
|---|---|---|
| F48: `test_ad_projection.py::test_a_public_span_in_a_mixed_section_maps_only_to_visible_provenance` | fails: the public view's receipt went to `lo_f48_held`, whose only citation is the held-out span | passes |
| F49: `test_ad_epoch.py::test_twenty_protected_revisions_queued_first_never_hold_back_the_public_one` | fails: `[] == ['pi_public']` | passes |
| F49 (synchronous): `test_ad_epoch.py::test_the_synchronous_preparation_counts_visible_revisions_only` | fails: `[] == ['pi_public']` | passes |
| F50: `test_ad_epoch.py::test_a_revision_prepared_while_protected_is_prepared_once_it_is_public` | fails: `[] == ['pi_prot_00']` | passes |
| the planted-read negative control: `test_ad_guard.py::test_negative_control_with_the_guard_disabled_the_planted_read_check_fails` | n/a (no guard) | passes: with the guard in observe mode, the planted-read check fails |

The other new tests use APIs the redesign added, so they do not import on `b1d082afb`. They are
contract tests of the new mechanism:
- `test_ad_guard.py`: the zero-denial pipeline, the pinned connection, a non-AD write, maintenance
  and vault loads, AD off, and the marker lint;
- `test_ad_protected_tables.py`: the column classification;
- `test_ad_projection.py`: the IR and vault projections, and every protected table's rows equal
  across the two copies;
- `test_ad_epoch.py`: the epoch's changes and the artefact classes.

### Behaviour changes worth knowing

- **Learned coupling.** Any protection change takes every relatedness run out of force until the
  subject is proposed and adopted again (E2).
- **Outside forecasts.** A frozen outside-forecast state is sent only at its epoch. A span held out
  after the serve, even one the card does not quote, expires it (E2). Two send-guard controls that
  held out an unrelated span now hold out nothing.
- **Item preparation.** Protected revisions no longer count against a run's 20, and a revision is
  done for one epoch only.
- **Activity rows.** An activity administration or surface used only by withheld answers is absent
  to AD. The incumbent's activity and grading tables are denied to AD outside its rules.
- **The report.** `learnloop ad report` has a top-level `guard` block (`denials`), and the rendered
  report has a line when it is above zero.

### Owner notes

- Any protection change, anywhere in the vault (marking or unmarking held-out material, reserving or
  releasing an exam pool), resets an adopted learned coupling until the subject is re-proposed and
  re-adopted. It also expires pending background outside forecasts; the next serve freezes new ones.
- `learnloop ad report` shows the AD guard's denial count. Each denial left AD unavailable for that
  operation, and the incumbent served. The details are in `ad_guard_denials.jsonl` beside the
  database. There is no UI notice; any count above zero is a bug to report.

### Environment

**Ambient-environment runs** (no `env -i`): two `uv run python -c` commands were run with the
ambient environment.
- In fix round 14: `uv run python -c "print(1)"`.
- In this redesign: an import-only `uv run python -c "import learnloop.adaptive_difficulty.report,
  ..."`, and later `uv run python -c "pass"`.

None opened or created a vault, so there are no `model_call_receipts` to check, and none made a
model call.

Everything else outside pytest ran under `env -i PATH=$PATH HOME=<empty> CODEX_HOME=<empty>
LEARNLOOP_CONFIG_DIR=<empty>`: standard-library file editors, read-only schema reads of the
migration head fixture, and the reference scripts. The trace runs used a scratch pytest plugin
(observe mode) that was never committed.

### For the next verify (the proposal's §3.5 closed checklist)

1. A read in an operation that bypasses the guard: a non-SQL source, or a path the pipeline does
   not exercise.
2. A misclassified column in `protected_tables.COLUMNS`.
3. An artefact or cache that is not epoch-scoped.
4. A counting or limiting step outside an operation.

File findings on the generator's internals under E1's ruling, and findings on the incumbent's
exam protection separately. Neither is a stage blocker.

### Gate (owner rule 2026-10-17: targeted only; run once after the last code change, `30a3bd574`)

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 27 kept, 0 broken (no new contract needed: AD imports no daily-plan module; the estimator's plan events are injected from `daily_plan/ad_slot.py`) |
| targeted pytest, `-n 14`, part 1: every AD test file (the four new ones included) and every test file naming an edited module (`db.scopes`, `connection_hook`, `span_aliases`, `pipeline.jobs` and the commission jobs, the sidecar's AD handlers, `cli.ad`, `daily_plan.engine`, `daily_plan.estimates`, `practice_generation`), the salience firewall, rebuild orchestrator, Decider landing and repository scopes: 130 files | **8,149 passed, 36 xfailed, 0 failed** (1,540 s) |
| targeted pytest, part 2: the rest of the stage's 186-file targeted set: 101 files | **1,993 passed, 0 failed** (320 s) |
| `--durable-sqlite`: `test_ad_guard.py`, `test_ad_epoch.py`, `test_ad23_migration.py`, `test_ad1_migration.py` | 24 passed |
| references: `db_generate_reference.py`, then `db_validate_reference.py` (under `env -i`) | regenerated (commit labels and the cited source lines; no schema change), 0 errors; `module_validate.py` and `validate_vault.py` pass; `desktop_validate.py` fails on an unclassified desktop source (`apps/learnloop-tauri/src/components/pdfSelection/testing/syntheticBook.ts`) that this branch does not touch |
| migration 214, the head fixture, the defaults snapshots, the CLI help, vitest, `cargo check` | unchanged or not applicable (no schema, config, CLI or desktop change) |
| owner decisions | unchanged: selection on with the simulation gates as strict-xfail monitors, `calibrate_below` 0.25, `learned_coupling` off, `history_fallback = current_content`, the report windows, the seven-day commission expiry; replay makes zero model calls; no evidence, mastery or certification write (the import-linter contract, and the guard's write rule at runtime) |

## Redesign round 2: closing the checklist's classes (2026-10-21)

The closed-checklist verify (`20261021-081118-y3cr1s`) found 5 High and 3 Medium findings, all
inside the checklist. Under the orchestrator's binding rulings, each CLASS is closed by a rule that
the registry or the guard enforces, not per instance.

### Class 3, epoch completeness and stamping (findings 1-4)

**(a) The epoch digests everything the projection withholds** (`MaterialView.epoch`).
- What it digests:
  - the predicate's material (whole extractions and span keys) and the exam reservations;
  - `Protection.ids`, the protected current items;
  - the withheld revisions (current items' and saved snapshots', by content hash);
  - the withheld notes, and the facets only withheld material names.
- Equal epochs mean equal projections.
- Finding 1: a history item that moves onto an already-held-out span changes `Protection.ids`, so
  the epoch changes too.
- `operation.epoch_of` now takes a view, never a `Protection`.
- A property test changes each field of `Protection` and of `Material` that decides what is
  withheld (`Material.covers` reads extractions and spans; `reasons` and `pinned_revisions` only
  explain) and asserts the epoch changes. A new field fails the test until it is classified there.

**(b) Every AD artefact AD reads back carries its epoch, and the rules read it only at that epoch**
(`protected_tables.EPOCH`).
- **Stamped in a column:**
  - `ad_selections` (serve draws, and commissions with their chosen point, suppression and expiry:
    finding 2);
  - `ad_commission_results`;
  - `ad_dose_offers`;
  - `item_serve_inputs` (frozen signals and loadings: finding 4);
  - `ad_reading_opportunities` (frozen doses: finding 3).
- **Stamped in JSON:**
  - `forecast_receipts` (`versions.protection_epoch`, every AD forecast);
  - `item_forecast_payloads` (the frozen outside state);
  - `ad_relatedness_runs` (`units["protection:epoch"]`).
- **`free`, each with its reason:**
  - `ad_coupling_versions`: a pointer to epoch-scoped runs;
  - `ad_state`, `ad_attempt_trace`, `item_forecast_scores`: DERIVED, never read by AD;
  - `judgment_ledger`: AD's judgments are of content, or are read through an in-force run;
  - `practice_item_snapshots`: a revision's own content.
- **The rule:** `MaterialView.keep` withholds a row whose stamp is not the current epoch. A row with
  no stamp, written before stamps existed, is never in force.
- **What a row of another epoch becomes, by consumer:**
  - an idempotency lookup reports it `withheld`, so nothing is rewritten over it;
  - a reading receipt counts for nothing, and the sweep maps its source again under the current
    projection. The receipt's identity gained the epoch, so it can be recorded again;
  - frozen serve inputs are ignored, and the replay reconstructs the attempt from current content
    (`history_fallback`);
  - a commission is not open: it neither suppresses a fresh draw nor supplies a target;
  - a frozen outside state is reported `protected` and never sent.
- **Completeness:** `test_ad_protected_tables.py` fails on any AD-owned table (AD-writable and
  protected) without an epoch rule, or on a stamped table whose stamp column is not classified
  `epoch`.
- **Migration 214 amended (not landed):**
  - a last column `protection_epoch` on `ad_selections`, `ad_commission_results` and
    `ad_dose_offers`;
  - `item_serve_inputs.protection_epoch` added;
  - `ad_reading_opportunities` rebuilt with the same columns, indexes and triggers plus
    `protection_epoch NOT NULL DEFAULT ''`, its two uniqueness constraints gaining the epoch. A
    legacy row reads `''`, which keeps its identity unique and is never in force.
- **The head fixture** was rebuilt from the same 213 base blob with only 214 applied: rollback mode,
  integrity and foreign-key checks clean, every pre-existing row unchanged. Its README records this.

**The facet-map exceptions are gone.**
- The registry's `facet_map` kind, `MaterialView._transformed` and `MaterialView.visible_loadings`
  are deleted, and so are the loading filters in `load_structure` and the replay.
- A mapping computed under another epoch is recomputed (a reading receipt is swept again), or
  counts for nothing (frozen loadings and runs). One computed at the current epoch was computed
  under this very projection, so it stands as recorded.
- `relatedness.stale_judgments` is replaced by `live_judgments`: the judgments of the runs in force.

**Found by the differential while doing this:** the send guard judged an operation's projected
vault and repository (a guard built inside an operation was handed `op.vault`). It now unwraps them
and judges the vault as loaded.

### Classes 2 and 4, proposals (finding 5)

- `proposed_patch_items` has a `self` rule: a proposal is withheld when the item its effective
  payload (the edit, else the payload) creates or changes has a withheld id, or its canonical
  exercise or provenance refs lie in held-out material, or its source refs name a withheld item. An
  unreadable item payload is withheld.
- `ad_serving.open_commissions`, `commission_expires_at`, `landed_after_expiry` and the expiry clock
  take the view's commissions (`rows`) and its proposal rule (`proposal_visible`). Supersession, the
  pending `any()` and the `max(decided_at)` now run over filtered rows only.

### Class 1, scope leaks (findings 6 and 7)

- Leaving `own_write()`, on any exit, re-installs the authorizer on every guarded connection, which
  expires their prepared statements.
- While a write is being authorized, a read passes without the rules only when it is of the write's
  own target or of a table its declared foreign keys reach (parents and children, read from the
  schema and cached per schema version). Trigger statements pass by their trigger source. The
  blanket allowance is gone, so a DELETE whose subquery reads a protected table is refused.

### Class 6, denials fail closed by construction (finding 8)

The first denial poisons the operation:
- every later read of a non-neutral table, and every write, is refused;
- the operation's exit raises `OperationPoisoned`, so its output is discarded however the code
  inside handled the refusal;
- writes made after the denial are refused, and the enclosing savepoints roll back what the
  exception reached.

The callers are fail-closed boundaries:
- the slot is AD-unavailable;
- the serve hook returns `skipped: failed` (`entry(poisoned=...)`; logging never breaks the serve);
- the Reader's dose offer answers no offer;
- the readiness RPC answers "not predicted", and "why this item" answers nothing;
- generation targeting takes the incumbent's rung;
- the commission job finds no commission open.

`dose.decide`'s forecast covariate and the slot's exposure check re-raise a denial instead of
turning it into a missing covariate or a candidate's exclusion.

### Tests, and fail-before on `96c23b28a`

`git archive` into `fixtures-local/ad23-r2-base`, the new test files copied in,
`-o pythonpath="src ."`:

| Finding | Test | On `96c23b28a` |
|---|---|---|
| 1 | `test_ad_epoch.py::test_a_history_item_newly_protected_by_its_own_provenance_expires_the_frozen_forecast` | fails: `{'ok'} == {'protected'}` (sent) |
| 2 | `test_ad_epoch.py::test_a_commission_drawn_under_other_protection_is_not_open` | fails: the old commission stays open |
| 3 | `test_ad_epoch.py::test_a_reading_receipt_recorded_under_other_protection_is_mapped_again` | fails: `{'fp': 0.5}` replayed |
| 4 | `test_ad_epoch.py::test_frozen_serve_signals_trained_on_a_newly_protected_answer_are_not_replayed` | fails: the frozen inputs (and their `z_v1`) replayed |
| 5 | `test_ad_epoch.py::test_a_protected_pending_proposal_never_holds_a_commission_open` | fails: the commission stays open |
| 6 | `test_ad_guard.py::test_a_statement_prepared_in_own_write_is_not_reused_outside_it` | fails: DID NOT RAISE (the cached statement ran) |
| 7 | `test_ad_guard.py::test_a_write_reads_only_its_own_target_and_declared_constraints` | fails: DID NOT RAISE (the subquery read passed) |
| 8 | `test_ad_guard.py::test_a_planted_read_swallowed_in_the_dose_decision_yields_no_decision_and_no_rows` | fails: DID NOT RAISE (a draw was made) |
| 8 | `test_ad_guard.py::test_a_swallowed_denial_poisons_the_operation` | fails (no poisoning) |
| 3a | `test_ad_epoch.py::test_any_change_to_the_protection_changes_the_epoch` | fails (the view had no epoch; the old one omitted `ids`) |
| 3b | `test_ad_protected_tables.py::test_every_ad_owned_table_ad_reads_has_an_epoch_rule` | fails (no rule existed) |

Two other checks:
- the planted-read negative control still fails with the guard off
  (`test_negative_control_with_the_guard_disabled_the_planted_read_check_fails` passes);
- the zero-denial pipeline still holds.

**Test adaptations:**
- Seeded AD rows are now stamped with the epoch they model being written under: `ad_epoch` and
  `restamp` in `tests/ad23_fakes.py`. The contract's fixture restamps each copy once its
  protection is final, and writes the protected copy's canonical note before computing that epoch.
- The contract's frozen loadings no longer seed a protected-only facet in the protected copy: AD
  could not freeze one at that epoch.
- Five round-8 regressions now pin E2's reset where a protection change happened mid-test:
  - F20 receipts: the old receipts are out of force, and receipts of the new epoch are
    revalidated;
  - F26: the studied example re-recorded;
  - F24 `z_v1`: its receipt is stamped;
  - F25: the old draw is out of the cohort;
  - and the contract's relatedness cases assert live judgments.
- The migration tests now expect 214 to alter exactly the two AD1 receipts it stamps.
- The projection test names each copy's epoch stamp.

### Consequences for the owner

- **One protection change resets AD's accumulated history** (E2, now applied to every AD artefact).
  A protection change is marking or unmarking held-out material, reserving or releasing an exam
  pool, or moving an item onto or off held-out material. After one:
  - forecast receipts written before it no longer feed scoring or `z_v1` calibration;
  - serve selections leave the report's cohort and windows;
  - frozen serve inputs give way to current-content reconstruction;
  - commissions close;
  - dose offers stop counting in the budget;
  - reading receipts are swept again.
- **Rows written before this round have no epoch**, so in an owner vault none of them is ever in
  force. This includes AD1's receipts if AD1 has run there. Reading receipts are swept again at the
  next serve; the forecast and selection history starts afresh.

### Sizes, `96c23b28a..` the round-2 commit

Production and migration: +546 / -204. Tests: +528 / -111.

### Gate (owner rule 2026-10-17: targeted only; run once after the last code change)

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 27 kept, 0 broken |
| targeted pytest, `-n 14`, 229 files: round 1's two sets (every AD test file and every file naming an edited module, then the rest of the stage's 186-file set), plus every file naming the head fixture, `ad_reading_opportunities` or `item_serve_inputs` | **10,152 passed, 36 xfailed, 0 failed** (1,481 s) |
| `--durable-sqlite`: `test_ad_guard.py`, `test_ad_epoch.py`, `test_ad23_migration.py`, `test_ad1_migration.py` | 33 passed |
| migration 214 and the head fixture | amended and rebuilt (above); the migration tests pass, as do the tracked-fixture and table-role tests |
| references, under `env -i`: `db_generate_reference.py`, then `db_validate_reference.py`; `module_validate.py`, `validate_vault.py` | regenerated (the amended tables, commit labels, cited lines), 0 errors; both validators pass |
| owner decisions | unchanged: selection on with the sim gates as strict-xfail monitors, `calibrate_below` 0.25, `learned_coupling` off, `history_fallback = current_content`, the report windows, the seven-day commission expiry; the replay makes zero model calls; no evidence, mastery or certification write |

### Environment

Every Python run outside pytest this round ran under `env -i PATH=$PATH HOME=<empty>
CODEX_HOME=<empty> LEARNLOOP_CONFIG_DIR=<empty>`: the file edits, the head fixture's rebuild, and the
reference scripts. The two epoch-debugging pytest plugins stayed in the scratchpad, uncommitted. No
model call was made.

## Redesign round 3 (2026-10-21)

The closed-checklist verify (`20261021-104418-6QARfA`) found three findings (one High, two
Medium), each closed under the orchestrator's binding rulings.

### Finding 1 (High): span aliases come from the projected readings

- Inside an operation, `ProjectedRepository.span_reanchors_between` serves `MaterialView.span_reanchors`.
  That is the only alias set a `SpanTranslator` built on `op.repository` sees.
- Its automatic aliases (`exact_hash`, `geometry_section`) are computed again from the two
  projected readings by the new `span_aliases.computed_aliases`. It is cached by the projected
  repository's `projection_key`, that is per protection epoch.
- A persisted or incumbent automatic alias is never accepted, even with both endpoints public: its
  match may have been decided by held-out neighbours.
- **Which alias kinds exist.** `source_span_reanchors.match_kind` allows `exact_hash`,
  `geometry_section` and `manual`. Only the first two are ever written in production
  (`record_aliases`, from `reanchor_spans`). `manual` is written by no production path, only by
  `Repository.insert_span_reanchor`, which only a test calls. A `manual` row is kept only when the
  rules show both its endpoints, and it then overrides the computed alias of its span.
- `test_ad_projection.py::test_span_aliases_are_recomputed_from_the_projected_ir` is the
  projection-equality case. A book is read twice. A duplicated public block's held-out neighbours
  decide its recorded alias `dup_old -> dup_x`. Without them the block is ambiguous.
  - The protected copy's translator inside an operation resolves exactly as the absent copy's does
    (stale).
  - The sweep records the same opportunities in both copies, and none for the LO that cites
    `dup_old`.
  - On `54ae865ca` the translator used the persisted alias. A sweep-only variant of the same case
    also failed there, recording a `passage_viewed` row for `lo_m1`.

### Finding 2 (Medium): poisoning expires cached statements

- At the first denial, `Guard._deny` re-installs the authorizer on every guarded connection: the
  same expiry `own_write()` and `rules()` use on exit. Every statement prepared before the denial is
  then authorized again on its next run, and `_write` refuses it because the operation is poisoned.
- Re-installing happens inside the authorizer's own callback. The guard therefore installs one
  stable bound method (`Guard._hook`), so re-installing frees no callable that is running.
- `test_ad_guard.py::test_a_cached_ad_write_is_refused_once_the_operation_is_poisoned`: an
  `ad_dose_offers` insert, a swallowed denial, then the identical insert with new parameters is
  refused and writes nothing. On `54ae865ca`: DID NOT RAISE.

### Finding 3 (Medium): the serve operation sits inside its savepoint

- `entry(..., savepoint=True)` opens the repository's savepoint OUTSIDE the operation. A poisoned
  operation's exit raises inside the savepoint, which rolls back before anything is released, and
  the `poisoned` fallback runs after the rollback. This holds however the function returned.
- The serve hook uses it: `@entry(poisoned=_serve_unrecorded, savepoint=True)`. It returns
  `skipped="failed"` and the incumbent's serve goes on.
- `test_ad_guard.py::test_a_write_then_a_swallowed_denial_then_an_early_return_keeps_no_ad_rows`
  runs the verify's sequence through the daily plan's serve. A planted sweep writes a reading
  receipt and then swallows a refused read, and the hook returns early because the item is
  protected. The result: no AD rows, and the incumbent's presentation served. On `54ae865ca` the
  receipt survived (`1 == 0`).
- The other entry points keep their current shape. A refusal there propagates through their own
  savepoints since rounds 2 and 3; after it, every write and every cached statement is refused.

The planted-read negative control still fails with the guard off: its test passes on both trees.

### Gate (run once, after the last code change)

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 27 kept, 0 broken |
| targeted pytest, `-n 14`: round 2's 229 files plus every file naming `span_aliases`, `SpanTranslator` or `span_reanchor` | **10,160 passed, 36 xfailed, 0 failed** (1,389 s) |
| `--durable-sqlite`: `test_ad_guard.py`, `test_ad_epoch.py`, `test_ad23_migration.py`, `test_ad1_migration.py` | 35 passed |
| migration 214, head fixture | unchanged this round |
| references, under `env -i` | regenerated (commit labels, cited lines); `db_validate_reference.py` 0 errors; `module_validate.py` and `validate_vault.py` pass |

Sizes, `54ae865ca..` the round-3 code commit: production +67 / -17 (5 files), tests +153 (2 files).
Every Python run outside pytest ran under `env -i` with an empty HOME, CODEX_HOME and
LEARNLOOP_CONFIG_DIR. No model call was made; owner decisions are unchanged.

## Redesign round 4 (2026-10-21)

The closed-checklist verify (`20261021-112836-xjtGDx`) found two findings: one High, one Medium.

### Finding 1 (High): every reference is located through one key function

- **The key function.** `exam_material.reference_keys` places a reference of any shape through
  `source_ref_keys`:
  - a provenance ref: its extraction, its span ids (plain or namespaced), and the span its
    `block_span_v1` locator names;
  - a recorded mapping: `extraction_id` (else the parent's), `span_id`, `span_ids`, `locator` /
    `href`, a nested `anchor` or citation under its parent's extraction, and `*_key(s)` strings in
    `ext:span` form;
  - any string that is a `span:ext/span` locator.
- **The projection removes a reference with ANY withheld key** (`MaterialView._visible_ref`). It no
  longer trims span lists. Nothing of a removed reference survives, so its quote or locator cannot
  restore its anchor. The Reader's quote fallback, inside the operation, runs over the projected
  references and the projected IR only.
- **The same function now places the other shapes AD judges:**
  - a tutor event's whole source context (`question_event_withheld`, which used to read only
    `extraction_id` with `span_id`, and so missed anchors, locators and keys);
  - a Reader question's anchors and cited spans;
  - a note reference given as a span locator;
  - the registry's `span@C` and `spans@C` columns.
- **Grep.** In what AD reads, the reference shapes are `locator`, `span_ids`, `anchor`, `citations`,
  `source_spans`, retrieval and delivery records, and `grounded_keys` / `trimmed_keys`. I found no
  `href` in AD-read data; the field is covered for safety.
- **Tests:**
  - `test_ad_projection.py::test_a_locator_only_reference_into_held_out_material_is_withheld` is the
    verify's case as a projection-equality test: `HELD_LO` cites only `locator="span:ext/H"`, with a
    quote that public P contains. The absent copy has neither H nor the reference into it (the
    reference is protected material). Inside the operation both copies map P to `[LO]` only, and
    both sweeps record the same rows, none for `HELD_LO`.
  - `test_every_recorded_reference_shape_is_located_through_the_shared_key_function` pins each
    shape.
  - On `1c920e102` the first test failed (the reference was kept) and the second failed with an
    ImportError (no `reference_keys`).

### Finding 2 (Medium): every writing entry point is in the savepoint form

- **`ad_operation(..., savepoint=True)`** opens the repository's savepoint OUTSIDE the operation.
  When the operation is poisoned, joined or not, it raises `OperationPoisoned` inside that savepoint.
  Every write therefore rolls back before anything is released, and the caller's fallback runs after.
  `optional_operation` and `entry` pass the option through.
- **Every `@entry` declares exactly one write form.** The decorator refuses one with none, or with
  more than one, when it is defined:
  - `savepoint=True`, for entry points that write AD decisions or receipts:
    - `dose.decide`, `dose.record_uptake`;
    - `reading.sweep`;
    - `serving.decide_slot`;
    - `serve.record_plan_serve`;
    - `generation.commission_point`, `generation.record_landed_commissions`;
  - `read_only=True`: the guard refuses any write while it runs, which also poisons the operation.
    This covers the replay, the report, scoring rows, readiness, arms, relatedness inputs and its
    shadow report, the queueable commissions, stale subjects and the feasible dose variants;
  - `durable="why"`: see the deviation below.
- **Operations opened directly** are in the savepoint form too:
  - the slot (`ad_slot`, which used to open its savepoint manually);
  - the commission job (`jobs`, which had its savepoint inside the operation; now outside);
  - the Reader's dose offer, whose response construction (the offered question's read) is inside
    the savepoint.
  - "Why this item" opens a `read_only` operation.
- **Tests:**
  - `test_ad_guard.py::test_every_ad_entry_point_declares_its_write_form_and_writers_use_the_savepoint_form`
    is the AST sweep over `src/learnloop` and the sidecar.
  - `test_a_read_only_entry_point_cannot_write`.
  - `test_a_denied_dose_response_rolls_the_draw_back[raised|swallowed]` is the verify's sequence
    through the sidecar handler: a draw of an extra question, then a refused read of that question.
    The offer is unavailable, no dose row survives and `budget()` has room. On `1c920e102` the draw
    survived (`1 == 0`).

**Deviation: the entry points that send to a model use the `durable` form, not the savepoint.**
- These are `outside.forecast_item`, `outside.forecast_presentation`, `background.prepare_items`
  (and its run's operation), `relatedness.propose_subject`, `feature_audit.audit_revision` and
  `backfill.backfill`.
- Their units commit on their own by design:
  - the durable work claim, which other processes and the lease check must see;
  - the spend ledger, which must record money spent;
  - each item's receipt.
- One transaction around them would hold the database's write lock across network calls and hide
  their claims. Tried on `forecast_item`, the savepoint form broke three outside-forecaster tests:
  the claim's lease check read `stale` and the spend refusal never ran.
- What they committed before the first denial read nothing withheld: any such read is that denial.
  Every write after it is refused (rounds 2 and 3, including cached statements), and their exit
  raises `OperationPoisoned`, so their output is discarded.

The planted-read negative control still fails with the guard off: its test passes on both trees.

### Gate (run once, after the last code change; rerun from scratch after a session restart interrupted the first run)

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 27 kept, 0 broken |
| targeted pytest, `-n 14`: round 3's files plus every file naming `exam_material`, `source_ref_keys`, `reader_dose_offer`, `optional_operation` or `ad_slot` | **10,504 passed, 38 xfailed, 0 failed** (2,038 s) |
| `--durable-sqlite`: `test_ad_guard.py`, `test_ad_epoch.py`, `test_ad_projection.py`, `test_ad23_migration.py`, `test_ad1_migration.py` | 46 passed |
| migration 214, head fixture | unchanged this round |
| references, under `env -i` | regenerated; `db_validate_reference.py` 0 errors; `module_validate.py` and `validate_vault.py` pass |

Sizes, `1c920e102..` the round-4 code commit: production +219 / -77 (21 files), tests +183 (2 files).
Every Python run outside pytest ran under `env -i` with an empty HOME, CODEX_HOME and
LEARNLOOP_CONFIG_DIR. No model call was made; owner decisions are unchanged.

## Redesign round 5 (2026-10-21)

The closed-checklist verify (`20261021-130727-0eZbnv`) found 3 findings, all class 2: content that
was readable because its table was classified "neutral". The class is closed by construction.

### A column-complete registry, enforced by the authorizer

- **The registry.** The new `adaptive_difficulty/column_classes.py` classifies every column of
  every table an operation can read, i.e. every table in `protected_tables.ROLES`: 116 tables,
  1,487 columns. A table outside `ROLES` is unreadable inside an operation.
  - `metadata`: ids, timestamps, counts, statuses, kinds, costs, versions, hashes, tokens, and JSON
    lists of ids or numbers.
  - `content`: any text, JSON or blob that can carry source text, an item, a prompt, an answer, a
    rubric or a model's input or output.
  - The draft came from name and type rules. It was reviewed table by table and is conservative:
    when in doubt, `content`.
- **The authorizer is column-aware** (`Guard._read`).
  - Outside the rules' scopes, a read of a content column is refused, whatever the table's role.
    The rules' scopes are the material view's rules (`/* ad-rules */`), the predicate's, and the
    incumbent's named constraint readers, which hand AD only a pass or a refusal.
  - A neutral table's metadata columns stay readable raw.
  - A read that names no column (`COUNT(*)`) and `rowid` count as metadata. An unclassified column
    counts as content (fail closed).
- **What the verify named is now content:**
  - `model_call_receipts.input_text` and `output_text`, while its accounting (`cost`, the token
    counts, `status`) stays metadata;
  - `assessment_contract_versions.contract_json`, while its `practice_item_id`, hash and version
    stay metadata.
- **The completeness test** (`test_ad_protected_tables.py::test_every_column_of_every_readable_table_is_metadata_or_content`)
  fails on any column of a classified table that is unclassified, classified twice, or gone from
  the head schema. A migration therefore classifies the columns it adds.
- **The one reclassification the AD suite surfaced:**
  - `grader_calibration_models.provenance_json` and `evidence_manifest_json` are read by the
    incumbent's effective-observation references, which the replay uses.
  - They name a calibration model's policy, bundle and evidence counts
    (`attempts.grader_calibration`), never an answer or an item, so they are metadata. The registry
    says so in a comment.
- **AD readers that need a content column:** none in the AD pipeline reads a content column of a
  neutral table. The full AD suite and the zero-denial pipeline pass with no other change.
  - For assessment contracts the rules now have the one reader, `MaterialView.assessment_contract`.
  - It withholds a contract whose item is withheld, or one an answer was graded against whose
    historical revision is withheld (`grading_evidence` and `question_events` attempts, through
    `attempt_withheld`), or one a withheld tutor question cites.
- **Tests:**
  - `test_ad_guard.py::test_a_raw_read_of_a_content_column_of_a_neutral_table_is_refused` (three
    cases): the metadata columns are readable; the content column, `SELECT *`, and a WHERE on the
    content column are refused.
  - `test_an_exam_reserved_items_contract_is_read_only_through_the_rules` (the verify's scenario 2).
  - `test_an_incumbent_model_calls_text_is_unreadable_raw_while_its_accounting_is` (scenario 3).
  - `test_the_rules_read_a_content_column_inside_an_operation`.

### Finding 1 (High): roles over the projection

- `MaterialView.worked_example_spans` no longer calls `role_keys` on the raw extraction. It applies
  the incumbent's `effective_hint` to the projection:
  - only visible blocks are classified;
  - a block's heading is resolved against visible headers only;
  - a section-path element that names a withheld header, by its block id or by its text when no
    visible header shares that text, resolves to no heading. That is what a dangling element does
    when the header was never extracted.
- So withheld heading text never gives a public block its role. Both the reading sweep's
  `worked_example` receipts and the dose arm's extra-example offers go through this method.
- `test_ad_projection.py::test_a_withheld_heading_never_gives_a_public_block_its_role` is the
  verify's case. Header H "Worked Examples" is withheld. Public P sits under it with an inherited
  `worked_example` hint and no lead cue.
  - Positive control: with H public, P is a worked example.
  - With H held out, the view's worked examples are empty, as in the copy without H, and the sweep
    records the same `reading/passage_viewed` row in both copies.

### Fail-before on `f66400f28`

Every new test fails there:
- the three content-column cases, and scenario 3: DID NOT RAISE;
- the contract scenario: there was no rules reader, and the raw read passed;
- the heading case: `{'p_span'} == set()`;
- the completeness test: no registry.

The planted-read negative control still fails with the guard off.

### Gate (run once after the last change)

- The first run had 2 failures. Two source scans list the modules that name `ad_reading_opportunities`
  and `keep_local`, and the new registry names every column; both scans now admit it (it reads
  nothing).
- The whole gate was then run again:

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 27 kept, 0 broken |
| targeted pytest, `-n 14`: round 4's files plus every file naming `role_keys`, `worked_example_spans`, `model_call_receipts`, `assessment_contract`, `protected_tables` or `column_classes` | **11,678 passed, 38 xfailed, 0 failed** (1,708 s) |
| `--durable-sqlite`: `test_ad_guard.py`, `test_ad_epoch.py`, `test_ad_projection.py`, `test_ad23_migration.py`, `test_ad1_migration.py` | 53 passed |
| migration 214, head fixture | unchanged this round |
| references, under `env -i` | regenerated; `db_validate_reference.py` 0 errors; `module_validate.py` and `validate_vault.py` pass |

Sizes of the round-5 code commit:
- production: +609 / -10 (4 files), of which `column_classes.py` is 522 lines of registry;
- tests: +191 / -3 (5 files).

Every Python run outside pytest ran under `env -i` with an empty HOME, CODEX_HOME and
LEARNLOOP_CONFIG_DIR, the registry's generator included. No model call was made; owner decisions
are unchanged.

## Redesign round 6 (2026-10-22)

The closed-checklist verify was an Opus adversarial review, since Codex is out of quota until
Oct 27. It found one High and two Lows, and confirmed the following:
- the column guard and its classifications;
- triggers;
- epoch scoping;
- batch limiting;
- the durable entry points;
- the invariants.

### High: heading resolution by position, never by text

- **The flaw.** Round 5 blanked withheld header titles keyed by normalized text. The incumbent's
  `_heading` looks a raw path element up after `strip()` only. A GLM-OCR multi-line or
  double-spaced heading ("Worked\nExamples", "Worked  Examples") therefore missed the blanking, and
  the withheld text set the role.
- **The fix is structural.** `MaterialView.worked_example_spans` resolves each visible block's
  heading by POSITION: the nearest preceding visible `SectionHeader` of its reading, by ordinal.
  - A withheld block is neither classified nor anyone's heading.
  - The stored section path is not read at all, so no text equality remains in the role path.
  - The incumbent's `effective_hint` is handed a one-element path naming that positional heading,
    or an empty path when there is none.
- **A consequence for every book, protected material or not.** AD's worked-example map now follows
  position where the incumbent follows the stored path. For Marker output the two coincide: the
  nearest preceding header is the path's last element. The incumbent's own `role_keys` is
  unchanged.
- **Test.** `test_ad_projection.py::test_a_withheld_heading_named_by_text_never_gives_a_public_block_its_role`
  covers "Worked Examples", "Worked\nExamples" and "Worked  Examples", with P's section path naming
  H by its text.
  - Positive control: with H public, P is a worked example.
  - With H held out: P is not one, as in the copy without H, and the two sweeps are equal.
  - Round 5's block-id case still passes.
  - On `603df25f6` the multi-line and double-spaced cases fail (H's text gave P its role). The
    single-spaced case passed there, which is the reason round 5 missed this.

### Low: the incumbent scope's column rule

- `Guard._read` evaluates the column class in the incumbent scope as well. Content columns are
  allowed there only to a reader in `INCUMBENT_READERS`.
- Test: `test_ad_guard.py::test_in_the_incumbent_scope_only_its_named_readers_read_content`. A
  module that is not listed, reading `model_call_receipts.output_text` inside
  `incumbent_constraints()`, is refused; its `status` column stays readable. It fails on
  `603df25f6`.

### Low: latent write-statement gaps

Every rule below was checked against callback logs on the installed SQLite 3.53.1.

- **The write context ends with its statement.**
  - The guard installs SQLite's statement trace on every guarded connection, beside its
    authorizer. The trace fires when each statement starts running, after its preparation.
  - At that moment the guard clears the write context (`_writing`, and whether an UPDATE was seen).
    Every denial clears it too.
  - The next statement is therefore prepared with no context, so its own SET expressions and
    subqueries are judged as reads.
  - An UPDATE's SET reads come before its UPDATE action, as the probe showed:
    `READ p.b, READ p.id, READ t.id, UPDATE t.a, SELECT`. Before this fix, an earlier write's
    context could let them through.
- **`UPDATE ... SET (subquery)` and `UPDATE ... FROM` are refused.**
  - SQLite authorizes both as a SELECT action after the UPDATE action. The guard refuses a SELECT
    once the statement has an UPDATE action.
  - An UPDATE's WHERE subquery is plain reads, without a SELECT action, and is judged as before.
  - `INSERT ... SELECT` is unchanged.
- **`RETURNING` poisons the operation.**
  - The authorizer cannot tell a RETURNING read from a WHERE read: for `UPDATE ... RETURNING a`
    SQLite gives `UPDATE t.a, READ t.a`.
  - Refusing at execution with `interrupt()` was tried and rejected: SQLite then rolls back the
    whole enclosing transaction, the incumbent's serve included.
  - So the statement trace detects the clause instead, after literals, quoted identifiers and
    comments are stripped, and poisons the operation. Its exit raises, its output is discarded, and
    in the savepoint form its writes roll back.
- **Tests, in `test_ad_guard.py`:**
  - `test_an_update_with_a_subquery_set_or_a_from_clause_is_refused` (4 cases);
  - `test_a_write_with_returning_poisons_the_operation_and_rolls_back` (INSERT, UPDATE and DELETE);
  - `test_a_write_context_never_outlives_its_statement`.
- **On `603df25f6`:** all fail except one UPDATE case. `UPDATE ad_dose_offers ... FROM` was
  already refused there by accident: its target's own read came after the SELECT reset and was
  judged as a raw read of a protected table. The same shape on the neutral `judgment_work_claims`
  fails before.
- **No production SQL changed.**
  - No statement in `src` uses RETURNING, and no AD writer uses an UPDATE FROM or an UPDATE SET
    subquery.
  - The one SET subquery in `src` is the incumbent's session close-out (`UPDATE sessions`, in
    `repositories.py`). It writes a table no operation may write in any case.
  - The full AD suite passes unchanged.

The planted-read negative control still fails with the guard off.

### Gate (run once after the last change)

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 27 kept, 0 broken |
| targeted pytest, `-n 14`: round 5's 229-plus files | **11,690 passed, 38 xfailed, 0 failed** (1,832 s) |
| `--durable-sqlite`: `test_ad_guard.py`, `test_ad_epoch.py`, `test_ad_projection.py`, `test_ad23_migration.py`, `test_ad1_migration.py` | 65 passed |
| migration 214, head fixture | unchanged this round |
| references, under `env -i` | regenerated; `db_validate_reference.py` 0 errors; `module_validate.py` and `validate_vault.py` pass |

Sizes of the round-6 code commit: production +70 / -28 (2 files), tests +116 / -5 (2 files).

The session restarted mid-round. The worktree held the round's complete edits, which were kept and
then tested from scratch. Every Python run outside pytest, including the authorizer probes, ran
under `env -i` with an empty HOME, CODEX_HOME and LEARNLOOP_CONFIG_DIR. No model call was made;
owner decisions are unchanged.

## Redesign round 7: values derived from other rows (2026-10-22)

Closed-checklist verify 17 reopened with one High and one Low. It confirmed round 6's own items:
- the incumbent scope;
- the statement trace;
- RETURNING poisoning;
- the named exceptions.

**The High (classes 2 and 1).**
- What went wrong: a visible block's OWN stored columns carried withheld header text.
  - Ingest derived `role_hint` and `section_path_json` from the running heading stack, and that
    stack holds withheld headers.
  - `worked_example_spans` filtered on the stored hint.
  - `project_ir` kept the stored path, which `reanchor._context_score` compares (+3).
- What the verify's probes showed:
  - A withheld "Worked Examples (continued)" or "Exercises" decided a public block's role, and so
    the receipt kind and the dose arm's extra example.
  - In a re-read, H's exact text decided an alias.
- Why the tests missed it: their "absent" copies kept P's inherited hint and path.

This is the third round on one class: withheld content reaching AD through data derived from it.
Under the owner's rule, this round fixes the class, not the two columns.

### The audit: every non-reference column of a table that can hold a visible row

**Columns that are derived:**

| Column | Derived at ingest or later from | Treatment |
|---|---|---|
| `source_document_blocks.section_path_json` | the extractor's heading stack: Marker's `section_hierarchy`, GLM-OCR's `_Headings` placer, the Markdown heading levels; withheld headers included | **recomputed** by position (`project_ir` → `ingest.block_roles.positional_structure`): the nearest preceding *visible* header |
| `source_document_blocks.role_hint` | `classify_block_role` over that stored path | **recomputed**: `classify_block_role` over the positional path |
| `source_document_blocks.ordinal` | position, counting withheld blocks | **recomputed**: dense, in reading order |
| `source_document_blocks.extractor_block_id` | layout ids that count blocks per page and type (`/page/0/Text/3`, `glm/page/0/region/7`), withheld ones included | **recomputed**: kept only as a caption cue's own time locator (`t=…`), else none |
| `source_document_blocks.text` | the block's own region text, except GLM-OCR's `_join_split_labels`, which joins a label's number when the NEIGHBOURING labels' numbering vouches for it | **recomputed**: GLM-OCR text and header blocks in the neighbour-free form (`glm_ocr.canonical_label_text`) |
| `source_document_blocks.content_hash` | a hash of that text | **recomputed** over AD's text |
| `source_document_units.label`, `locator_json`, `parent_unit_id`, `ordinal`, `semantic_hash`, `page_start`, `page_end` | units at headings (GLM-OCR's `_heading_units`, Markdown's `_units_from_headings`, Marker's table of contents), withheld headings included; the hash and pages over all blocks | **recomputed**: a unit opened by a withheld block is no unit, and its visible blocks join the unit before it (at the start, the one after it); the rest keep their identity and label; ordinal dense; a dropped parent left out; hash and pages over visible blocks |
| `source_exposure_events.section_path_json` | a copy of the viewed block's stored path | **unread**: AD maps an exposure by its span through the projected IR |
| `reader_section_progress.spans_seen`, `span_count` | counts over the section's spans, withheld ones included | **unread**: AD reads a section's completion only |
| `source_span_reanchors.match_kind`, `confidence` (value) | `reanchor_spans` over the full readings | automatic rows are never used; since round 3 AD recomputes aliases from the projected readings. A `manual` row is an owner's decision |
| `source_extraction_runs.health_json`, `extraction_result_hash` (neutral, metadata) | page counts by block type, and a digest of the whole reading, withheld blocks included | metadata by round 5's rule (counts, hashes), and never consumed by AD: the projection recomputes the IR's health from visible blocks. Classifying them as content was tried and refused every `SELECT *` of a run (88 failures, alias computation first), so they stay readable as counts and a hash |

**Tables AD cannot read at all:** the chunk, full-text, embedding, outline and chunk-map tables
(heading-prefixed or context-including text, digests that cross blocks). They are not in the
registry's `ROLES`, so they are unreadable inside an operation.

**Columns that are the row's own and not derived:**
- `block_type`, `page`, `bbox_json`, `polygon_json` and `asset_ids_json` of a block are its own
  region.
- An asset's `caption`, `page`, `geometry`, `media_type`, `path` and `content_hash` are its own.
- An exposure's `locator`, `page` and `context` are its own.
- A unit's `unit_id` is an identity, which the Reader's progress rows name. A merged unit's id leaves
  AD's projection; the Reader's section of that id is already withheld by its withheld heading
  (`section_withheld`).

**The other value columns are not derived from source rows:**
- AD's own artefacts are epoch-scoped (round 2).
- The learner's events and the incumbent's rows (attempts, presentations, plan events, questions,
  administrations) are resolved by their references.
- A tutor event's source context is withheld by any withheld key in it (round 4).
- Generated candidates are withheld by their items and revisions.

### The rule, by construction

- **A new registry kind, `derived_by_position`** (`protected_tables.DERIVED`), with a named
  treatment per column (`DERIVED_TREATMENT`).
- **The guard refuses a derived column outside the derivation scope** (`rules("derive")`), even
  inside the rules. The predicate and the incumbent's named readers are the exceptions.
- **The rules never hand a derived column out.** Their select lists leave it out (`_select`).
- **Raw readings are loaded only inside the derivation scope:**
  - `MaterialView.document_ir` then hands out only `project_ir`'s recomputed reading;
  - `section_spans` hands out only the Reader's section membership.
- **`project_ir` derives everything again from visible blocks, for every reading** (withheld or
  not, so two readings compare alike). It also recomputes the health block counts.
- **`worked_example_spans` reads the projected reading.** The role is `classify_block_role` over
  the positional heading, then the incumbent's `effective_hint`; never the stored hint.
- **Reanchor's inputs are projected readings** (paths, neighbours, hashes, ordinals), via
  `computed_aliases` since round 3.
- **A scope change expires prepared statements.** Leaving any rules scope for a narrower one
  (`derive` back into `view`, or `view` out of the rules) re-installs the authorizer. Before, this
  happened only at the outermost exit.

**Consequences for AD's behaviour.** These follow from "derived again from visible rows", in every
book:
- AD's worked-example map follows the positional heading and the real ingest classifier.
- A Marker book's blocks under a "Worked Examples" heading are now worked examples for AD. Marker's
  stored paths are block ids, which never gave ingest a cue, so before this round they were not.
- A header that names a worked-example unit ("Worked Examples") counts as one, as ingest classifies
  it.

### The systemic test: "never extracted" by the real ingest derivation

**The builder.** `tests/ad_ingest_fakes.py` emulates only what an extractor reports before ingest
derives anything:
- Marker's blocks with the `section_hierarchy` Marker computes from the headers present;
- GLM-OCR's title and text regions.

It then runs the production converters, `marker.chunk_output_to_ir` and `glm_ocr.responses_to_ir`.
The never-extracted copy is the document with the withheld elements deleted BEFORE that run; no
stored derived column is copied. Span ids are given back their element's id, since ingest numbers
spans by position.

**The outputs compared**, inside an operation, between the protected copy and the never-extracted
one:
- `worked_example_spans`;
- `learning_objects_for_span` for every visible span;
- `feasible_variants` (the dose arm's extras);
- the sweep's receipts (kind, subkind, LO and source span);
- `computed_aliases` between two readings.

**The tests** (`tests/test_ad_never_extracted.py`):
- **Property, 25 seeds × Marker and GLM-OCR:** withheld header texts (multi-line, double-spaced,
  continued, unit and section headings), levels and positions, withheld body blocks.
- **Re-read property, 10 seeds × 2 styles:** a pair that differs only in withheld text, with
  duplicated public blocks. Its outputs also equal those of the same pair with other withheld text.
- **The verify's three probes, × 2 styles:**
  - a withheld "Worked Examples (continued)" or "Exercises" under a visible "Worked Examples",
    deciding P's role, its receipt and the extra-example offer;
  - a re-read whose duplicate block sits under H, deciding its alias by H's exact text.

**The existing projection tests' copies now come from the same builder.** These are the mixed
section, the re-read, the locator-only reference and the withheld heading, by block id and by
text.

**What the property found during the work:** GLM-OCR's heading units. A section opened by a
withheld heading moved a public block's span-to-LO mapping (the Reader maps a span by its
section). That is the unit merge in `project_ir`.

### The Low: a write's own accesses

- **Narrowed allowance.** The foreign-key allowance now covers the declared key columns only: the
  parents' referenced keys and the children's referencing columns, as `(table, column)` from the
  schema. A write's own target is read by its METADATA columns only.
- **Callback evidence** (SQLite 3.53.1). The verify's statement (`DELETE FROM judgment_ledger WHERE
  id IN (SELECT judgment_id FROM activity_family_membership_events WHERE practice_item_id = ...)`)
  was already refused on `26923e913`, but only incidentally. SQLite authorizes the foreign-key
  check's own read of the child after the subquery's SELECT action. That reset the write context,
  so the read was judged as a protected raw read. Its subquery's `practice_item_id` read had passed.
- **Now** that read is refused itself.
- **Fail-before:** the reachable variants reading a target's own content column in a WHERE, or in a
  subquery on the target, were authorized before and are refused now:
  - `DELETE FROM model_call_receipts WHERE output_text LIKE ...`;
  - `... WHERE id IN (SELECT parent_call_id FROM model_call_receipts WHERE input_text LIKE ...)`.

### Fail-before on `26923e913`

17 of the new cases fail there:
- 6 of the 25 GLM-OCR property seeds;
- both alias probes (Marker and GLM-OCR);
- the GLM-OCR role probe;
- the block-id heading case;
- the four derived-column guard cases;
- the two target-content DELETE cases;
- the registry's treatment test.

Those that pass there are named here:
- Marker's role probe and Marker's property seeds: Marker's stored paths are header block ids,
  which never gave ingest a role cue, so H's text could not reach the role there; Marker's aliases
  could.
- The re-read property's seeds: the probe pins the alias case.
- The two protected-table DELETE cases: refused before by later reads, as described above.

The planted-read negative control still fails with the guard off.

### Gate (round 7, run once after the last change)

The gate ran under the owner's 2026-10-23 memory rule: every pytest command inside `systemd-run
--user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, with `-n 6`, one command at a time. The 300
targeted files ran as three sequential thirds.

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | 27 kept, 0 broken |
| targeted pytest: round 6's files, plus `test_ad_never_extracted.py` and every file naming `glm_ocr`, `block_roles`, `project_ir` or `extraction_sections` | **11,862 passed, 38 xfailed, 1 failed** (1,943 + 1,989 + 7,930) |
| the one failure | `test_voi_v2.py::test_in_the_real_probe_vault_the_gate_no_longer_ends_a_paying_episode`, which touches no AD code. It passed alone and with its file (39 passed) on the same tree: a flake under load |
| `--durable-sqlite`: guard, epoch, projection, never-extracted, `test_ad23_migration.py`, `test_ad1_migration.py` | 147 passed |
| migration 214, head fixture | unchanged |
| references, under `env -i` | regenerated (9ca3f1c56); `db_validate_reference.py` 0 errors; `module_validate.py` and `validate_vault.py` pass |

Sizes of the round-7 code commit (8b66d516b):
- production: +262 / -77 (6 files);
- tests: +100 / -27 (3 files), plus the new `ad_ingest_fakes.py` and `test_ad_never_extracted.py`.

Three session restarts interrupted the round. Each time the worktree held the real edits and the
regenerated references, and nothing else: no temporary outputs. Progress was committed before this
gate. Every Python run outside pytest ran under `env -i` with an empty HOME, CODEX_HOME and
LEARNLOOP_CONFIG_DIR. No model call was made; owner decisions are unchanged.

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

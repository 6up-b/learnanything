# Router objective RO1 (`router/ro1-interval`, base `90f7def5e3`)

Built from `docs/specs/spec_router_objective_v1.md` §5 (owner decisions Nov 3-4 2026; no gates, no evidence
thresholds). Successor `mvp-0.46` after FG1's `mvp-0.45` (`INTERVAL_FACTOR_ALGORITHM_VERSION`), upgrade
`learnloop.interval_factor_upgrade`, migration 242 (`242_availability_time.sql`). FG1c and RO0 also claim
migration 242 and land first, so the landing renumbers this one (one file) and the head fixture; neither claims a
successor, so `mvp-0.46` should hold. What was built where the spec differs is in the spec itself, §5.7.

## What exists now

| Spec | Where |
|---|---|
| §5.1 the change | `attempts/attempts.py:4611`: at the gate the surprise record's `fsrs_interval_factor` is 1.0, and the interval line (`:4663`) multiplies by it, which is exact. The gate is `router_objective_switches.interval_factor_removed(config)`, its own (not `hot_path_applies_practice_review`) |
| §5.2 what stays | Rating, S, D and every surprise value are computed as before; direction, the follow-up gate, the re-probe trigger and `signal_quantiles` read the same record. Replay goes through the same function, so a rebuild writes 1.0 under the same gate. `alpha_interval`, `f_min`, `f_max` stay in `config/schema.py` with a note; the full template (`LEGACY_DEFAULT_CONFIG_TEXT`, the one that stores them) carries the note; `recall_targets.py`'s docstring; `sim/default_sweep.yaml` now sweeps `remove_interval_factor = false` (alpha is inert at the latest version) |
| §5.3 availability | Migration 242: `practice_attempts.received_at`, `received_at_source` (`recorded`, `inferred`), the backfill of `exam_evidence` rows from the id's ULID time (SQL: a Crockford GLOB and a base-32 fold of the first ten characters), invalid ids left null. `AttemptDraft.received_at` -> the attempt record -> `_insert_practice_attempt` (written only when set). `goals/exam_seeding.py` sets it (new `clock` argument, the import's time). `router_objective_switches.available_at(row)`, `AVAILABLE_AT_SQL`, `attempt_time_column(config)`. Replay's UPDATE never touches the column |
| §5.3 decision-time reads | `daily_plan/router_card.py`: `as_of_attempt_id` (`:209`), `_attempts` (`:445`) and the week of activity (`_interaction`, codex review F1) filter by availability at the gate. Outcomes, FSRS, mastery and the diagnoser's history keep `created_at` |
| §5.4 | `diagnosis/split/history.py:916`: `validated_resolution_ids` drops `learner_report:*` at the gate. Status and `resolution_observation_ids_json` untouched |
| §5.5 version and switches | `algorithm_versions.py`, `config/schema.py` (`SchedulerSurpriseConfig.remove_interval_factor`, `RouterObjectiveConfig.available_at_reads`, `.self_report_not_validated`), the registry's three `_ConfigRule`s (structural, operational), every defaults snapshot recomputed and `mvp-0.46`'s added. CLI `upgrade --to`, the openers' completion (`cli/runtime.py`, `learnloop_sidecar/context.py`), the activation journal docstring, the import contracts' module list |
| §5.5 the projection change | `derived_state_rebuilds.projection_switches_json`, written by both rebuild writers; `Repository.latest_whole_vault_rebuild`; `ops/doctor.py::_check_projection_switches` (`sql:projection_switches_stale`). The upgrade's activation runs a whole-vault rebuild under the tag in its transaction (rebuild equivalence's pattern; completion is that rebuild's receipt) |
| §5.5 the upgrade's report | `daily_plan/schedule_effects.py`, added by `learnloop rebuild --shadow --json`; `ShadowRebuildResult.schedule_before/after`, and (codex review F2, F3) `shadow_rebuild(observe=serving_schedule)`'s `observed_before/after`: serving's own population (`engine.review_population`) and the recall-target anchors on each side |

**`RouterObjectiveConfig` and RO0.** RO0 adds the same class with `receipts`. This branch adds it with RO1's two
keys at the same place in `LearnLoopConfig`; the merge keeps one class with all three keys, and the
`test_ro1_successor` and `test_data_capture_successor` pins then compare `router_objective` with `receipts` in it.
The defaults snapshots are recomputed again at the merge.

**AD column classes.** The three new columns are classified `metadata` in `adaptive_difficulty/column_classes.py`
(the guard's completeness test requires every head column classified).

## The audit of §5.4

`resolution_observation_ids_json` has three readers and two writers on this branch:

| Site | What it does | Counts? |
|---|---|---|
| `diagnosis/split/history.py:916` | `validated_evidence_count` for the diagnoser | Yes: the one count. Fixed at the gate |
| `db/repositories.py:17902` (`unresolved_cause_factor`) | Decodes the list into the factor payload | No: nothing reads `payload["resolution_observation_ids"]` to count (git grep over `src`, the sidecar and the desktop) |
| `adaptive_difficulty/column_classes.py:635` | Classifies the column for AD's guard | No |
| `diagnosis/causal_attribution.py:3709` | Writes `[learner_report:<id>]` at a pick | Writer |
| `diagnosis/causal_orchestrator.py:2773` (the spec's `:2735`) | Writes a probe's `[cdo:<hash>]` on `matched_single` | Writer; still counts at the tag |

Two related counts were checked. The provisional belief a pick appends (`causal_hypotheses.evidence_json`, with a
`learner_confirmation` key) is a mapping, and `history.py:885` counts a mapping as 0 at every version, so a pick
never counted there. `diagnosis/split/snapshot.py:159` hashes `validated_evidence_count` into the diagnosis
snapshot, so at the tag a vault with picks gets a new snapshot id for those contexts: the intended change, and
byte-identical with the switch off (tested).

## Choices the spec left open, and where the code moved

1. **Line references.** The spec's references are to `9780ca3baf`. At this base: the multiplication is at
   `attempts.py:4663` (spec `:4646`), the insert list at `repositories.py:18678` (spec `:18655`), the router card's
   read at `router_card.py:206` before this change (spec `:205`), the orchestrator's resolution at
   `causal_orchestrator.py:2773` (spec `:2735`). Same code in each case.
2. **Where the "projection's defaults snapshot" lives.** Nothing of that name existed: `DEFAULTS_SNAPSHOT_BY_ALGORITHM`
   is per version, not per vault, and the activation receipt (`p0_projection_activation`) replays no attempt.
   Smallest form that does what §5.5 asks: a nullable JSON column on the rebuild receipt, written only by rebuilds
   that replay attempts, read by doctor from the latest whole-vault rebuild. A vault with no recorded rebuild (a new
   vault at the tag, or one whose rebuilds predate 242) is not compared, since nothing says how its stored dates
   were derived; every upgraded vault has one because the upgrade rebuilds.
3. **Whether the upgrade rebuilds.** §5.5 says due dates shift "at the next derived-state rebuild or upgrade" and
   are "visible at upgrade". FG1's upgrade only re-ran the canonical projection, which writes no due date, so this
   one follows the rebuild-equivalence upgrade (`replay_ledger_upgrade.py`): a whole-vault rebuild in the
   activation transaction, completion read from that receipt. The owner's routine rebuild after an upgrade is then a
   no-op for RO1.
4. **"Marked inferred".** A second column (`received_at_source`) rather than a convention inside the timestamp, so a
   reader can tell an inferred value from a recorded one. Only `exam_evidence` rows are backfilled: exam sittings
   stamp `created_at` at the finish (`exam_session.py:567`), which is the write.
5. **Decision-time reads beyond `:205`.** The card's `_attempts` filter is the same clause as the `as_of` read (the
   card's recent work and per-topic evidence), so it reads availability too; its ordering and dates stay
   `created_at` (when it happened). RO0's snapshots, RO2's cards and RO6's features are not on this branch; the
   helper is there for them. RO0 lands first. Read from its branch (`router/ro0-logging` at `d4996b8db9`,
   `router_objective/decision_state.py`): its attempt reads are session minutes (`latency_seconds` summed over
   `created_at >= session start`, `:213`, `:222`), which are occurrence time and right for minutes, and open
   factors and hypotheses with no time filter. None filters attempts by what was known at the decision, so nothing
   there needs `attempt_time_column` today; the merge should recheck the final code.
6. **The report's minutes.** `projected_review_load` takes minutes per item; the report passes 1.0 and labels the
   result reviews per day, rather than calling the estimator from a report. The plan multiplies each review by the
   item's own estimate, so minutes move with it item by item. No new constant: 1.0 is the unit.
7. **The sweep.** `alpha_interval` is inert at the latest version with the switch on, so its sweep entry would
   report nothing; it is replaced by `remove_interval_factor: [false]`, which measures what RO1 changed.
8. **Not done:** nothing in §5 was dropped. (The Codex review found the card's week of activity unfiltered and the
   report's queue, load and interval anchors not serving's; fixed, `router-ro1-codex-review.md`.)

## The upgrade's report, measured on a synthetic vault

`tests/test_ro1_upgrade_report.py::build_history`: the placement vault at `mvp-0.45`, all 8 items reviewed 5 times
6 days apart with mixed scores (4, 3, 1, 4, 0, 2, 4, 4 cycling), 40 attempts. Built under the worktree's
`fixtures-local/ro1-synthetic/` (gitignored), read with `shadow_rebuild(--set algorithms.algorithm_version=mvp-0.46)`
and `schedule_effects` at the day after the last round (2026-06-13), plan horizon 14 days. No model call.

| Measure | Before (`mvp-0.45`) | After (`mvp-0.46`) |
|---|---|---|
| Item due dates moved | | 8 of 8 (6 earlier, 2 later) |
| Shift, days (min / median / max) | | -18.98 / -1.61 / +32.42 |
| New interval / old (min / median / max) | | 0.817 / 0.938 / 1.379 (inside [1/1.5, 1/0.5]) |
| Queue due at 2026-06-13 | 0 | 0 |
| Queue due 3, 7, 14 days later | 2, 2, 2 | 2, 2, 2 (none newly due, none no longer due) |
| Admission's review load, reviews/day (14 days), at 0 / 3 / 7 / 14 days | 1.000 / 1.000 / 1.071 / 1.071 | 0.857 / 0.929 / 0.929 / 0.929 |
| Activity cards | 0 rows | 0 rows |
| Mastery and facet rows | | Only the version stamp, beyond one mastery row a same-version shadow also shows (this vault's replay-against-live difference, not RO1's) |
| Live database | | Unchanged (hash before = after) |

After the Codex review's F2/F3 fix (the report now reads serving's population and the recall-target anchors) the
same builder gives the same numbers at 0, 3, 7 and 14 days: this vault has no commitment, no primed retry, no held
grade and no inactive item, so serving's population is every row and each anchor is the last attempt.

Reading: on this history the factor had mostly stretched intervals (a positive residual on the hard items and
correct answers), so most dates come earlier, but the two longest intervals were compressed by misses and move
later; with intervals of weeks, nothing crosses "due now" in the first two weeks, and admission's projected load
falls slightly because two items now fall outside the 14-day horizon. An owner vault's numbers will differ: run the
shadow on a backup-API copy before the upgrade (below).

## What the owner runs

On a backup-API copy first (never the live vault):

```bash
uv run learnloop rebuild --shadow --set algorithms.algorithm_version=mvp-0.46 --json --vault <copy>   # schedule_effects is the report
uv run learnloop upgrade --vault <vault>        # mvp-0.45 -> mvp-0.46, with the whole-vault rebuild
uv run learnloop doctor --vault <vault>         # no sql:projection_switches_stale
```

## Gate

Run in the worktree, every pytest inside `systemd-run --user --scope -p MemoryMax=5G -p MemorySwapMax=1G`, `-n 6`,
one run at a time (the RO0 worktree's own suite was running on the same machine). No full suite, no full durability
lane, no vitest: nothing under `apps/` changed, so no npm, vitest, frontend build or cargo.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | done |
| `uv run lint-imports --no-cache` | 42 kept, 0 broken (the frozen-cycles list unchanged; a first draft put the report in `substrate` and broke two contracts, so it moved to `daily_plan`) |
| Targeted, chunk A: 238 files (every new or changed test file, every file exercising a changed module found by `git grep`, the contract files: config defaults via the successor tests, CLI help snapshot, serializer snapshot, desktop RPC contract, mobile allowlist, architecture, table roles, coordinated migrations, tracked fixture databases, public-tip guards, AD protected tables, the label audit `test_measurement_state_labels.py`, the process-launch list `test_codex_lockdown_round3.py`) | 10555 passed, 22 skipped, 6 xfailed, **27 failed**: 15 migration-diff pins (242 alters two tables), 4 version-set pins, AD's protected-table columns, and `test_model_grade_lane` (at the tag a mastery change no longer moves the due date). All fixed; those 21 files rerun: 175 passed, 6 skipped, 1 xfailed; `test_model_grade_lane.py` after its edit: 2 passed |
| Targeted, chunk B: 36 upgrade, successor and landing files | 427 passed, 3 skipped, 0 failed |
| Final batch on the final code: 49 files (`tests/test_ro1_*.py`, the contract files above, AD guard files, the 15 migration files, the fixed pins, exam seeding, diagnosis context) | 789 passed, 6 skipped, 1 xfailed, 0 failed |
| `pytest -m durability` on `test_ro1_availability.py`, the 15 migration files, `test_migrations.py`, `test_tracked_fixture_databases.py`, `test_followup_migration.py`, `test_data_capture_migration.py` | 15 passed |
| `pytest --durable-sqlite` on `test_ro1_availability.py`, `test_ro1_projection.py`, `test_ro1_successor.py` | 37 passed |
| `db_generate_reference.py`, `db_validate_reference.py` | errors `[]` (prose leaf counts 1134 -> 1137, sections 79 -> 80) |
| `module_generate.py`, `module_validate.py`; `desktop_validate.py`; `validate_vault.py` | PASS; passed (unchanged); passed |

New test files: `tests/test_ro1_interval_factor.py`, `tests/test_ro1_successor.py`, `tests/test_ro1_availability.py`,
`tests/test_ro1_self_report.py`, `tests/test_ro1_projection.py`, `tests/test_ro1_upgrade_report.py`.

**Calls and spend.** No model or network call: no paid command was needed (RO1 has no model-backed code), so
nothing was run on a copy of an owner vault. Every script outside pytest ran under `env -i` with empty `HOME`,
`CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, with one slip: one read-only `sqlite3` query on the tracked head fixture
(`mode=ro`, counting attempt types) ran without `env -i`; it opened no vault and wrote nothing.

<details><summary>The 274 targeted files (chunks A and B)</summary>

- `tests/test_ad1_migration.py`
- `tests/test_ad23_contract.py`
- `tests/test_ad23_fix_r5.py`
- `tests/test_ad23_fix_r6.py`
- `tests/test_ad23_fix_r8.py`
- `tests/test_ad23_migration.py`
- `tests/test_ad23_successor.py`
- `tests/test_ad2_model.py`
- `tests/test_ad3_subject_view.py`
- `tests/test_adaptive_difficulty_ad1.py`
- `tests/test_ad_epoch.py`
- `tests/test_ad_guard_offer_receipts.py`
- `tests/test_ad_guard.py`
- `tests/test_ad_guard_reachable_reads.py`
- `tests/test_ad_projection.py`
- `tests/test_ad_protected_readings.py`
- `tests/test_ad_protected_tables.py`
- `tests/test_anti_double_count.py`
- `tests/test_apply_write_ahead.py`
- `tests/test_approach_map_replay.py`
- `tests/test_approach_maps_schema.py`
- `tests/test_architecture.py`
- `tests/test_assessment_enforcement.py`
- `tests/test_assumed_known.py`
- `tests/test_attempt_content_state_successor.py`
- `tests/test_attempts.py`
- `tests/test_batch3_landing.py`
- `tests/test_calibration.py`
- `tests/test_canonical_projection_rollout.py`
- `tests/test_capability_residual.py`
- `tests/test_causal_activity_policy.py`
- `tests/test_causal_attribution_p1.py`
- `tests/test_causal_p2_acceptance.py`
- `tests/test_causal_repair_sidecar_rpcs.py`
- `tests/test_chatgpt_plan_cli.py`
- `tests/test_chatgpt_plan_workspace.py`
- `tests/test_cli_attempt.py`
- `tests/test_cli_generate_practice.py`
- `tests/test_cli_help_snapshot.py`
- `tests/test_codex_attempt_flow.py`
- `tests/test_codex_lockdown_frozen.py`
- `tests/test_codex_lockdown_round3.py`
- `tests/test_codex_runtime.py`
- `tests/test_cold_retry_reschedule.py`
- `tests/test_compare_sources_keep.py`
- `tests/test_concepts.py`
- `tests/test_config_refactor.py`
- `tests/test_contract_frontier_coverage.py`
- `tests/test_contract_reachability.py`
- `tests/test_contrast_pairs.py`
- `tests/test_coordinated_migrations.py`
- `tests/test_coverage_denominator_boundary.py`
- `tests/test_curriculum_c0b_landing.py`
- `tests/test_curriculum_c1_landing.py`
- `tests/test_curriculum_c1_plan_follows_path.py`
- `tests/test_daily_plan_admission.py`
- `tests/test_daily_plan_composition.py`
- `tests/test_daily_plan_replay.py`
- `tests/test_data_capture_a3_time_metric.py`
- `tests/test_data_capture_landing_review.py`
- `tests/test_data_capture_migration.py`
- `tests/test_data_capture_successor.py`
- `tests/test_deliverable_codex_review.py`
- `tests/test_deliverable_curriculum_migration.py`
- `tests/test_desktop_rpc_contract.py`
- `tests/test_diagnosis_context.py`
- `tests/test_diagnosis_contract.py`
- `tests/test_diagnosis_history_modes.py`
- `tests/test_diagnosis_input_provenance.py`
- `tests/test_diagnosis_pipeline.py`
- `tests/test_diagnosis_replay.py`
- `tests/test_diagnostic_probe_single_use.py`
- `tests/test_discrimination_profiles.py`
- `tests/test_doctor.py`
- `tests/test_durable_promotion_arms.py`
- `tests/test_e0_isolation.py`
- `tests/test_e2e_codex_mock.py`
- `tests/test_e2e_local.py`
- `tests/test_embedding_store.py`
- `tests/test_error_hunt_items.py`
- `tests/test_evsi_router_composition.py`
- `tests/test_exam_protection_identity.py`
- `tests/test_exam_protection_review.py`
- `tests/test_exam_seeding.py`
- `tests/test_facet_authority.py`
- `tests/test_facet_authority_rereview.py`
- `tests/test_facet_diagnostics_v03.py`
- `tests/test_facet_identity_actions.py`
- `tests/test_family_memory_projection.py`
- `tests/test_field_config.py`
- `tests/test_field_workbench_signals.py`
- `tests/test_figure_prefetch_migration.py`
- `tests/test_figure_requests_migration.py`
- `tests/test_figures_migration.py`
- `tests/test_figures_prefetch_boundary.py`
- `tests/test_followup_codex_review.py`
- `tests/test_followup_journey.py`
- `tests/test_followup_migration.py`
- `tests/test_followup_rival_factor.py`
- `tests/test_followup_single_use.py`
- `tests/test_followups.py`
- `tests/test_followup_successor.py`
- `tests/test_forecast_receipts.py`
- `tests/test_gate_fit.py`
- `tests/test_goal_series.py`
- `tests/test_graph_correction.py`
- `tests/test_graph_nomination.py`
- `tests/test_held_grade_composition.py`
- `tests/test_held_grade_evidence.py`
- `tests/test_help_assist_figures_migration.py`
- `tests/test_help_assists_schema.py`
- `tests/test_help_assist_work_md_migration.py`
- `tests/test_help_fold_attach_successor.py`
- `tests/test_hint_telemetry.py`
- `tests/test_identifiability_doctor.py`
- `tests/test_ingest_instrument_gates.py`
- `tests/test_intent_codex_rereview.py`
- `tests/test_intent_codex_review.py`
- `tests/test_intent_fix_round5.py`
- `tests/test_intent_recall_targets.py`
- `tests/test_intervention_outcomes_replayer.py`
- `tests/test_irt_end_to_end.py`
- `tests/test_item_fingerprints.py`
- `tests/test_keep_local_retired.py`
- `tests/test_km1_doctor.py`
- `tests/test_km2b_consumer_rekey.py`
- `tests/test_km2_sim_gates.py`
- `tests/test_km2_write_path.py`
- `tests/test_laddered_stems.py`
- `tests/test_learner_blindness_relax.py`
- `tests/test_learner_claim_application_migration.py`
- `tests/test_learner_claim_superseded_migration.py`
- `tests/test_learner_gap_unlinked_migration.py`
- `tests/test_learner_notes_migration.py`
- `tests/test_learner_note_source_kind_migration.py`
- `tests/test_learner_notes_vault_origin_migration.py`
- `tests/test_learner_report_superseded.py`
- `tests/test_learner_review_system_entries.py`
- `tests/test_learner_text_gaps.py`
- `tests/test_learner_text_gaps_rereview.py`
- `tests/test_library_asks_migration.py`
- `tests/test_lp_claim_fixes.py`
- `tests/test_lp_claim_fixes_rereview.py`
- `tests/test_lp_claim_fixes_review.py`
- `tests/test_mcp_c1a_landing.py`
- `tests/test_mcp_tools.py`
- `tests/test_measurement_corrections.py`
- `tests/test_measurement_state_labels.py`
- `tests/test_method_explicit_landing.py`
- `tests/test_method_explicit_upgrade.py`
- `tests/test_migrations.py`
- `tests/test_misconception_resolution.py`
- `tests/test_misconception_routing.py`
- `tests/test_mobile_allowlist.py`
- `tests/test_mobile_jobs_migration.py`
- `tests/test_model_grade_lane.py`
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
- `tests/test_mvp09_upgrade.py`
- `tests/test_notes_never_read.py`
- `tests/test_p0_cutover_mvp08.py`
- `tests/test_p0_projection_cutover.py`
- `tests/test_pfc_unassessed_readers.py`
- `tests/test_pfc_unverified_unassessed.py`
- `tests/test_plan_determinism.py`
- `tests/test_plan_first_transport.py`
- `tests/test_plan_follows_path.py`
- `tests/test_post_attempt_pipeline.py`
- `tests/test_pr4_superseded_claims_landing.py`
- `tests/test_practice_index_dossiers.py`
- `tests/test_probe_orchestration_remainder.py`
- `tests/test_public_tip_guards.py`
- `tests/test_reader_ca2_fix_orchestrator.py`
- `tests/test_reader_ca2_one_ask.py`
- `tests/test_reader_digest_narrative.py`
- `tests/test_reader_followups.py`
- `tests/test_reader_followups_successor.py`
- `tests/test_reader_question_note_id_placement.py`
- `tests/test_reader_rw3b_migration.py`
- `tests/test_reader_rw7a_migration.py`
- `tests/test_reader_session_digests_migration.py`
- `tests/test_reader_workbench_rw2a.py`
- `tests/test_reading_hardening_landing.py`
- `tests/test_reading_step_switch.py`
- `tests/test_rebuild_equivalence.py`
- `tests/test_rebuild_equivalence_review.py`
- `tests/test_rebuild_orchestrator.py`
- `tests/test_recurrence_commands.py`
- `tests/test_recurrence_live.py`
- `tests/test_reference_gate_imports.py`
- `tests/test_registry_audit.py`
- `tests/test_regrade_contract_replay.py`
- `tests/test_regrade_contract_successor.py`
- `tests/test_regrade_contract_upgrade.py`
- `tests/test_replay.py`
- `tests/test_required_method_authority.py`
- `tests/test_required_method_grading.py`
- `tests/test_required_method_items.py`
- `tests/test_required_method_round3_review.py`
- `tests/test_reread_safety_landing.py`
- `tests/test_reread_safety.py`
- `tests/test_retrieval_spaces_migration.py`
- `tests/test_ro1_availability.py`
- `tests/test_ro1_interval_factor.py`
- `tests/test_ro1_projection.py`
- `tests/test_ro1_self_report.py`
- `tests/test_ro1_successor.py`
- `tests/test_ro1_upgrade_report.py`
- `tests/test_router_card.py`
- `tests/test_router_coldness_covariates.py`
- `tests/test_router_outcomes.py`
- `tests/test_router_r1_composition.py`
- `tests/test_router_r2a_landing.py`
- `tests/test_router_r2a_serving.py`
- `tests/test_router_r2c_teach_back.py`
- `tests/test_router_reader_activity.py`
- `tests/test_route_rules_in_grader.py`
- `tests/test_rw2d_receipts_migration.py`
- `tests/test_rw5c_migration.py`
- `tests/test_rw5c_never_evidence.py`
- `tests/test_rw5c_recheck.py`
- `tests/test_salience_firewall.py`
- `tests/test_section_coverage_migration.py`
- `tests/test_serve_eligibility.py`
- `tests/test_serve_eligibility_review.py`
- `tests/test_session_ownership_migration.py`
- `tests/test_shadow_rebuild.py`
- `tests/test_sidecar_contract.py`
- `tests/test_sidecar_serializer_snapshot.py`
- `tests/test_signal_quantiles.py`
- `tests/test_sim_teach_back.py`
- `tests/test_simulation.py`
- `tests/test_source_append.py`
- `tests/test_source_block_fts.py`
- `tests/test_source_sets.py`
- `tests/test_source_set_synthesis.py`
- `tests/test_source_space_resolver.py`
- `tests/test_sqlite_file_copies.py`
- `tests/test_sqlite_wal_lifecycle.py`
- `tests/test_sqlite_wal.py`
- `tests/test_stuck_prompt.py`
- `tests/test_stuck_prompt_replay.py`
- `tests/test_surfaced_belief_corrections.py`
- `tests/test_surprise.py`
- `tests/test_synthesis_criterion_dependencies.py`
- `tests/test_t1_batch_origin_migration.py`
- `tests/test_table_roles.py`
- `tests/test_teach_back.py`
- `tests/test_teacher_te0_confidence_events.py`
- `tests/test_teacher_te0_review_fixes.py`
- `tests/test_teacher_te1b_migration.py`
- `tests/test_teacher_te1b_review_fixes.py`
- `tests/test_teacher_te1b_suggestions.py`
- `tests/test_teacher_te1_migration.py`
- `tests/test_teacher_te1_review_fixes.py`
- `tests/test_teacher_te1_successor.py`
- `tests/test_teacher_te1_weight.py`
- `tests/test_tracked_fixture_databases.py`
- `tests/test_voi_forecasts.py`
- `tests/test_voi_merge_composition.py`
- `tests/test_voi_stopping.py`
- `tests/test_workbench_assistance.py`

</details>

## Open items

1. At the merge with RO0: one `RouterObjectiveConfig` with `receipts` and RO1's two keys; recompute every defaults
   snapshot; renumber 242 (after FG1c's and RO0's); rename the head fixture again (rebuild it from main's tracked head
   with only this migration applied); extend the applied-migration lists the head pins carry; check RO0's
   decision-state reads for a time filter on attempts (item 5 above).
2. The owner may want `received_at` set by other writers whose `created_at` is not the write time if any appear (the
   phone's offline captures record their own times through RO0's `log_interaction_event`, not attempts).

## Landing onto main

Main was at `90a2f430c9`, holding FG1c (migration 242) and RO0 (243). RO1 merged it in `eff30f881a`, with the references
regenerated in `248421272c`. The gate and the smoke ran on `248421272c`. Step 0's fix (ruling R1) is `4a801f1afc`, recorded in
`router-ro1-codex-review.md`.

### Rulings (verbatim)

- R1: "F1 has reopened on sibling reads, so it goes structural: every decision-time read of practice_attempts with a time cutoff goes through one availability predicate, which at the tag with available_at_reads on filters on coalesce(received_at, created_at) and otherwise is the predecessor's SQL unchanged; every loader feeding such a read selects received_at. This covers the adaptive-difficulty frozen history card (adaptive_difficulty/outside.py), the diagnoser's prior history and its loader (diagnosis/split/history.py) with the diagnosis contexts and snapshot exports built from it, the router card, and every other decision-time reader. Outcomes, FSRS, mastery and reports keep occurrence time and are named on an allowlist. A test fails on any time-cutoff read of practice_attempts in src/ that neither uses the predicate nor is on the allowlist. Below the tag or with the switch off, every such read is byte-identical to mvp-0.45."
- R2: "Live serving can't see an import before it is written, so the harm here is to the historical evaluation RO2-RO6 run at past cutoffs. The R1 fix carries Codex's reproductions (an exam on May 1 imported May 19, a May 5 cutoff, in the frozen card and the diagnoser's history) as tests, so there's no further Codex round. A further finding on this class is Low unless a decision-time read at a past cutoff that RO2-RO6 would train or evaluate on still includes a row received after that cutoff."
- R3: "The builder's open question stands outside RO1: when intent_serving returns None, admission's review load measures from last_attempt_at, so a primed retry or a held grade shortens it. It predates RO1, the report mirrors admission, and changing it changes admission, so it goes to the follow-up batch with its own playbook entry."
- R4: "The upgrade moves due dates, as the owner decided (spec §1, no gates). The smoke reports each copy's schedule_effects from the shadow rebuild before the real upgrade, so the owner sees how far their due dates move before they run it."
- R5: "The other open questions stand as recorded: the projection snapshot is a new column on the rebuild receipt and doctor compares only rebuilds that recorded it; only exam seeding sets received_at, and any future backdating writer must set it."

### The merge

- **Migration.** `242_availability_time.sql` is now `244_availability_time.sql`; its text is unchanged. It alters only
  `practice_attempts` and `derived_state_rebuilds`, so RO0's replaced `*_no_update` guards (plan_presentations,
  decision_objectives, decision_measurement_events) are untouched.
- **Head fixture.** `fixtures/migration_head_244/` was renamed from main's tracked, sanitized `migration_head_243` and rebuilt
  with only 244 applied:
  - applied to a backup-API copy outside the checkout, under the scratch-copy allowance;
  - `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE` (header bytes 1/1), `integrity_check` ok, `foreign_key_check` empty;
  - copied back with the backup API, with no companion files; every new column is null.
  - The README has a new section. The hard-coded paths and `SCHEMA_HEAD = 244` are updated in both reference scripts
    (`db_generate_reference.py` names the fixture 3 times), the sanitizer's usage line and every test pin, 69 references in all.
- **Tests' pins.** Applied-migration lists gained 244 and max-version pins moved to 244. RO1's two altered tables are
  folded into `TE1_AND_TE1B_ALTERED_TABLES` (`tests/test_teacher_te1b_migration.py`), the same way RO0 folded in its own.
  AD1's diff now names both later alterations of its tables (question_events by 243, practice_attempts by 244). RO1's own
  tests are renumbered (`test_244_*`, `RO1_ALTERED_TABLES` unchanged).
- **Config.** One `RouterObjectiveConfig` holds RO0's `receipts` and RO1's `available_at_reads` and
  `self_report_not_validated`. The parameter registry carries all three (RO0's and RO1's blocks both merged cleanly).
  All 37 defaults snapshots were recomputed from the composed defaults, mvp-0.46 included, and a second pass changed
  nothing. The frozen digests were re-pinned:
  - `test_ro1_successor.py` now freezes main's mvp-0.45 value at `90a2f430c9`. Dropping RO1's three keys reproduces
    `ec22e2fc…`, which is also main's snapshot.
  - The two RO0/RO1 pops in `test_data_capture_successor.py` became one. The TE1/TE1b successor tests pop
    `router_objective` and `remove_interval_factor`.
- **Other files.** The playbook and `table_roles.py` merged without conflict. 504 generated reference notes conflicted only in
  their stamps; I took main's and regenerated them. The prose leaf counts went from 1136 to 1139 in `Database.md` and
  `Configuration.md`.

### Early checks (step 2)

These are 107 files: every migration, upgrade and successor test, `test_ro1_*`, RO0's tests, the config tests,
`test_cli_help_snapshot.py`, `test_codex_lockdown_round3.py` (the process-launch allowlist),
`test_measurement_state_labels.py`, `test_table_roles.py`, `test_coordinated_migrations.py`, `test_public_tip_guards.py`,
`test_tracked_fixture_databases.py`, `test_architecture.py`, the parameter-registry, shadow-rebuild, doctor and
rebuild-orchestrator tests. Result: 1195 passed, 4 skipped, 2 failed. Both failures were frozen digests that still froze
main's earlier value (`test_ro1_successor`, and `test_data_capture_successor` with its doubled pop). After the fix, those
two and the TE1/TE1b successor and `test_ro1_availability_reads` files gave 79 passed. lint-imports: 43 kept, 0 broken
(the frozen cycles unchanged).

### References (step 3)

- `db_generate_reference.py` + `db_validate_reference.py`: errors `[]` at head 244, 1139 leaves.
- `desktop_generate` / `desktop_validate`: passed.
- `module_generate` / `module_validate`: PASS.
- `validate_vault.py`: passed (2190 notes).
- Config fingerprints: recomputed, as above.

### Gate (step 4, at `248421272c`)

| Lane | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | done |
| `lint-imports --no-cache` | 43 kept, 0 broken |
| Full suite (`-n 8 --dist worksteal`, 10G scope, under the full-suite lock) | **26296 passed, 91 skipped, 47 xfailed, 0 failed** (56:30) |
| Durability lane (`-m durability`) | 401 passed, 1 skipped |
| Owner lane (fresh backup-API copies of `owner-copies-mvp035` in `fixtures-local/landing-ro1/`) | 83 passed, 4 skipped, the 2 known failures only (`test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events`, `test_placement_fixture_copies[arxiv_v2]`). No new owner-lane failure |
| Desktop: typecheck, vitest (`--maxWorkers=4`, 5G), frontend build | ok; 2751 passed (270 files); ok |
| `cargo check` | ok |
| Mobile: typecheck, build | ok; ok |

There were no unexpected failures, so nothing needed a rerun.

### Smoke (step 5)

Setup:

- Copies: fresh backup-API copies of `~/learnloop-backups/mvp043-20261103-copy/{arxiv_v2,linear_algebra,probability}` in
  `fixtures-local/landing-ro1-smoke/`.
- Routes: every AI route pointed at `127.0.0.1:9`.
- Code: main code (`git archive 90a2f430c9`) and branch code (`git archive 248421272c`), both archived with `migrations/`.
- Preparation: each copy was upgraded to mvp-0.45 on main code, then `rebuild-derived-state` (head 243).
- Drivers: the FG1 and FG1c drivers, adapted:
  - Today, the plan dump and Next (serve) through the real sidecar handlers, on a frozen clock with module-stream ids;
  - a real `submit_attempt` through the tests' in-process grader and diagnoser fake, with the diagnosis drained;
  - the router card's JSON and text, the grader's and diagnoser's prompts, and every new row.

**R4: each copy's `schedule_effects`.** Branch code, `rebuild --shadow --set algorithms.algorithm_version=mvp-0.46 --json` on the
mvp-0.45 copy, run with the clock moved 0, 3, 7 and 14 days:

| Copy | Items | Due dates moved | Earlier / later | Shift, days (min / median / max) | Interval ratio (min / median / max) | Queue due before → after at 0 / 3 / 7 / 14 days | Admission's review load, reviews/day, before → after |
|---|---|---|---|---|---|---|---|
| arxiv_v2 | 32 | 1 | 1 / 0 | -0.010 | 0.992 | 2 → 2 at each | 1.571 → 1.571 at each |
| linear_algebra | 99 | 53 | 47 / 6 | -2.411 / -0.237 / +0.647 | 0.846 / 0.971 / 2.000 | 23 → 23 at each (none newly due, none no longer due) | 7.500 → 7.143 at each |
| probability | 77 | 1 | 1 / 0 | -6.070 | 0.890 | 0 → 0 at each | 0 → 0 |

- Activity cards: 0 rows on every copy.
- The shadow's learner-state diff before the upgrade, as facet / mastery / schedule rows: arxiv_v2 4 / 34 / 1,
  linear_algebra 76 / 21 / 53, probability 2 / 18 / 1. The facet and mastery rows are the version stamp.
- Bounds: linear_algebra's 2.000 is the ratio's upper bound, 1/f_min. That item's factor had been 0.5, a miss that
  compressed the interval.

**The upgrade.** `learnloop upgrade --to mvp-0.46` printed `Upgraded vault: mvp-0.45 -> mvp-0.46` and nothing else.

- Wall time on fresh copies: 1.5 s (arxiv_v2), 3.0 s (linear_algebra), 1.8 s (probability).
- After it: head 244, `algorithm_version = "mvp-0.46"`.
- Due dates against the mvp-0.45 copy, which match the shadow's counts exactly:

| Copy | Same | Earlier | Later |
|---|---|---|---|
| arxiv_v2 | 31 | 1 | 0 |
| linear_algebra | 46 | 47 | 6 |
| probability | 76 | 1 | 0 |

**Below the tag, and at the tag with the three switches off: identical to main.** The checks covered Today, the plan
dump, Next, the submit with its feedback, the 4 to 25 feedback bundles, the router card, the grader's and diagnoser's
prompts, and every row written (ids and times aside).

- Below the tag: branch code on a copy left at mvp-0.45, migrated to 244 by the open. IDENTICAL on all three copies.
- Switches off: `remove_interval_factor`, `available_at_reads` and `self_report_not_validated` set false, then upgraded
  to mvp-0.46. IDENTICAL on all three copies.
- What the comparison set aside:
  - RO1's own null columns (`received_at`, `received_at_source`, `projection_switches_json`);
  - RO1's three keys inside the config record RO0's receipts carry (`prefilter_payloads`, `decision_state_receipts`),
    and that record's compressed size.
- Seed draw: in both comparisons, as in FG1's smoke, the router mixture's seed is pinned to the decision id. That seed
  hashes the version string. Unpinned, linear_algebra's off copy (labelled mvp-0.46) drew a different reentry plan
  from the same distribution. Below the tag nothing was pinned to begin with and it was identical anyway.

**At the tag (switches on).**

- due_at on every eligible review: on every item with an FSRS-eligible, unheld anchor, `due_at = anchor +
  interval_for_retention(S)`, with no exceptions (arxiv_v2 2, linear_algebra 53, probability 1).
- Unchanged against the predecessor:
  - `practice_item_state` S, D, R and `last_attempt_at` (due_at aside);
  - every `attempt_surprise` column, `fsrs_interval_factor` aside (now 1.0 on every row);
  - the rating: `fsrsRating` in the bundles.
- Held and ineligible attempts: linear_algebra has one held and one ineligible attempt, and one of them falls after its
  item's anchor. arxiv_v2 has one held attempt, probability one ineligible. None moved a due date.
- How Today and the plan changed, on every copy:
  - unchanged: Today's items and their order, the plan's blocks, Next's sequence, the router card's text, and the
    grader's and diagnoser's prompts;
  - changed: `dueAt` and `nextDueAt` (and `fsrsIntervalFactor` in the bundles), the version strings, and on
    linear_algebra the plan's `reviewLoadPerDay`.

**Interrupted upgrade.** On a fresh linear_algebra copy, the upgrade was SIGKILLed inside activation's whole-vault rebuild,
after the replay had written and before the commit.

- What the vault looked like after the kill:
  - `integrity_check` ok, foreign keys clean, head 244;
  - still `mvp-0.45`, with no whole-vault rebuild receipt at mvp-0.46 and no activation journal (the kill came before
    the publication);
  - every due date equal to the mvp-0.45 copy's (99 of 99);
  - `doctor` showed only the copy's pre-existing `layout:missing_directory`.
- The rerun took 3.0 s and completed: mvp-0.46, one whole-vault rebuild receipt, and due dates, S, D, R and the surprise
  rows identical to the clean upgrade's.

**R1, an exam import with a past occurrence.** On the tag copies of linear_algebra and probability, a real item with
attempts on its topic was tagged `exam_q:1`. `seed_exam_attempts` then imported an exam dated 10 days back, at the real
time.

- The row: `created_at` 2026-10-26T12:00:00Z, `received_at` at the import (2026-11-05T03:12Z), source `recorded`.
- At a cutoff two days after the exam and before the import:
  - the router card's attempts don't read it, and `as_of_attempt_id` isn't it;
  - AD's frozen card shows no exam entry (11 entries on linear_algebra, 3 on probability), although the material view
    holds the row;
  - the diagnoser's history doesn't include it, and lists it as lag (1).
- After the import, every reader has it: the card's row and `as_of`; the frozen card gains it (12 and 4 entries); the
  diagnoser's history has it with lag 0.

**After the upgrade.**

- `rebuild --shadow` on each upgraded copy and on the interrupted-then-completed copy: 0 / 0 / 0. These copies ran no
  journey, so FG1's known item-scope facet case didn't arise.
- A second `rebuild-derived-state` left every DERIVED table identical, apart from the rebuild's own stamps
  (`facet_capability_evidence.created_at`/`updated_at`, `facet_recall_state.updated_at`,
  `subject_identifiability_watermarks.checked_at`).
- `doctor`: no `sql:projection_switches_stale` on any copy. Its errors were the same on main's mvp-0.45 copies:
  arxiv_v2 46 `criterion:unknown_dependency` + `layout:missing_directory`, linear_algebra `layout:missing_directory`,
  probability 46 `criterion:unknown_dependency` + 2 `yaml:invalid`.

**Time, main (mvp-0.45) against the tag.** Three fresh copies a side, medians:

| Copy | Today (n=15) | Plan | Next | Submit (n=3) |
|---|---|---|---|---|
| arxiv_v2 | 177 → 184 ms | 808 → 809 ms | 558 → 554 ms | 508 → 492 ms |
| linear_algebra | 254 → 273 ms | 1155 → 1182 ms | 698 → 714 ms | 519 → 409 ms |
| probability | 203 → 200 ms | 974 → 984 ms | 778 → 745 ms | 998 → 1018 ms |

The differences are within run-to-run noise, in both directions.

**Calls, sockets, processes.**

- Model calls: no `model_call_receipts` row with a real model. The tag copies hold the mvp-0.43 copies' counts
  (0, 0, 56), and each driven submit wrote two `fake-model` receipts, on main's side as well.
- Network: the watch logged no non-loopback connect and no name resolution.
- Processes: no Codex process. The only processes started were `git` (the code revision) and `powerprofilesctl`.

### What the owner runs

1. Close the desktop app, the MCP server and the phone page, and stop `learnloop-mobile`.
2. Pull main and run `uv sync --extra dev --extra mobile`. Nothing under `apps/` changed, so the desktop app needs no rebuild.
3. For each vault in `~/learnloop-vaults/<name>`:

```
# a vault still at mvp-0.43 takes FG1's and FG1c's pair first:
learnloop upgrade --to mvp-0.45 --vault ~/learnloop-vaults/<name>
learnloop rebuild-derived-state --vault ~/learnloop-vaults/<name>
# R4: on a backup-API copy, see how far the due dates move:
learnloop rebuild --shadow --set algorithms.algorithm_version=mvp-0.46 --json --vault <copy>   # schedule_effects
learnloop upgrade --to mvp-0.46 --vault ~/learnloop-vaults/<name>   # migration 244 and the whole-vault rebuild; due dates move
learnloop doctor --vault ~/learnloop-vaults/<name>                    # no sql:projection_switches_stale
```

4. Restart the phone host.

An upgrade interrupted at any point is completed by the next guarded open or by rerunning the same command. To keep
mvp-0.45's schedule at the tag, set `[scheduler.surprise] remove_interval_factor = false` before upgrading. The other two
switches are `[router_objective] available_at_reads` and `self_report_not_validated`.

### Open items

- R3: admission's review load with no intent view measures from `last_attempt_at`. This goes to the follow-up batch with
  its own playbook entry.
- R5, as recorded: only exam seeding sets `received_at`, and any future backdating writer must set it. Doctor compares
  only rebuilds that recorded the projection snapshot.
- RO0's decision-time reads of attempts are lower-bound windows read at the decision itself: session minutes and the
  trajectory's uptake. Neither has an upper cutoff a past evaluation could leak through, so neither is on the allowlist or
  needs the predicate. RO2-RO6 must ask `attempt_time_sql` / `known_at` for any read at a past cutoff, and the structural
  test enforces it for SQL.
- `StaticHistoryStore` (planted learners) carries no receipt time and is unchanged.
- The queue due counts don't change between 0 and 14 days on these copies: the long intervals and the plan's population
  keep the same items due. A vault with a denser schedule will show more movement. Run the shadow first (R4).

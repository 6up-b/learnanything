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

# Follow-up generate and serve, FG1 (`followup/fg1-generate-serve`, base `9780ca3baf`)

Built from `docs/specs/spec_followup_generate_serve_v1.md`, every section except §7's marks table and report (FG1c). Successor
`mvp-0.45` after `mvp-0.44`, kill switch `followup.generate_and_serve`, migration 241 (recheck the number against main at landing).

## What exists now

| Spec | Where |
|---|---|
| §5 item 1, §3.1: the durable workflow | `followup_serve/workflow.py` (a leaf), `db/stores/followup_serve.py`, `attempts/post_attempt.py::_open_followup_workflow`, `diagnosis/split/jobs.py::_workflow_diagnosis_ended`, the fourth worker slot in `learnloop_sidecar/post_attempt_worker.py` |
| §4.2: single use | `followup_serve/identity.py`, the doors listed below, `generated_probe_items`, `generated_probe_burns` |
| §4.1, §5.1: authoring to the pinned offer | `followup_run/authoring.py`, `followup_run/admission.py`, `accept_probe_offer(candidate_id=, followup_workflow_id=)` |
| §4.3: entry and needs | `probe_episodes.enter_episode` enqueues; `followup_run/jobs.py::_run_entry`, `_run_need`, `_run_factor_need` |
| §5: the router | `daily_plan/router_chooser.py::FollowupGate`, `router/plan_log.py::build_followup_decision`, `followup_run/router.py`, `router_decision_bindings`, `router/outcomes.py::_follow_binding`, `daily_plan/engine.py::_place_followup_probes` |
| §6: the desktop | `followup_run/serving.py`, `learnloop_sidecar/handlers/followup.py`, `screens/feedback/FollowupPanel.tsx`, `screens/FeedbackScreen.tsx` |
| §10: the phone | The phone's own miss opens no workflow; `device_deferred_count` counts a pending probe, so the existing "waiting for the desktop" line says so |
| §9 | All five specs carry a dated "Amended by FG1" note |

**Package split.** The import contract forbids a new cycle, so `learnloop.followup_serve` is a leaf (switches, workflow record,
queue writes, identity) that domain packages may read, and `learnloop.followup_run` is the composition, imported only by the
sidecar. A small `attempt_followup_grade` lives in `diagnosis/followups.py`, so `attempts` keeps its one existing edge.

## The doors of §4.2

| Door | What it does now |
|---|---|
| Queue, direct-by-id | `routine_withhold_reason` (`generated_probe_closed`, `generated_probe_reserved`), `sidecar/serving.py::refuse_generated_probe_door` on `open_queue_item`, `get_practice_item`, `get_probe_contract` |
| Plan pool | Same gates through `pool_admission`; `reconcile` displaces a standing planned item that is retired or was served elsewhere. A probe served here and unanswered reopens as the same administration |
| `find_practice` | Unchanged (diagnostic modes excluded); a stale pick meets the serve door |
| Teacher | `_probe_headers` leaves out every generated probe |
| AD | `admitted_new_material_ids` subtracts them |
| Exams | `exam_pool` candidates leave them out |
| Phone | The door refuses any serve with a request origin; submit's rejection is unchanged |
| MCP | Unchanged: read-only, no question text |
| Follow-up tasks | `_insert_pending_followups` drops them, overriding the repair-journey allowance |
| Rebuild replay | `replay_learning_object` keeps ledger-closed items inactive; nothing generates during rebuild |
| `state_sync` | `practice_item_activatable` takes the ledger |
| Check once | `admission_reason(requested=True)` refuses, so standing assignments too |
| Remint | `generated_probe_single_use` |

## Where the build departs from the spec's words, and why

1. **Constraint refusals arrive after generation on the plan path.** The plan's constraint engine reads an item, and at decision
   time none exists (§5 item 2 requires the decision first). The orchestrator's refusals (a learner's "Not now", pending machine
   checks, an episode conflict) still come before any spend. A plan constraint is checked when a waiting probe reaches its
   boundary. Smallest alternative to a full check: a learning-object-level constraint read before generation, if a dry run shows
   the wasted generations matter.
2. **Automated adversarial review does not run.** §4.1 runs it "only if its cost fits the wait". It would double the physical
   calls per probe, so the default is off and the admission receipt says `adversarial_review: not_run`. Real latency is for the
   owner's run on a copy, which can change this.
3. **A pinned follow-up presentation has no TTL.** §4.2 says abandonment closes it. A wait can outlast the 240-minute default, and
   an expiry after a burn would make the one submission fail.
4. **The routine session caps don't refuse a workflow's probe** (`get_probe_contract`). The router already decided, and otherwise a
   burned probe would serve as ordinary practice with its measurement lost.
5. **No-plan misses get no `no_intervention` draw**, the spec's stated default in §5.1.
6. **A block's follow-up uses the attempt that closed it**, when that attempt is a miss. §3.1 says completion "releases
   eligibility" without saying which of a block's misses it picks. The earlier misses keep the block's own diagnosis path.
7. **Teach-back misses stay on the predecessor's path.** Their door has its own screen, with no pending and skip UI (§3.1's rule).
8. **New vaults store no `auto_generate_on_entry = true`.** §4.3 says "new vaults get `true`", and the successor's effective setting
   gives every vault at the tag exactly that. The decision-only template holds no `[probe.generation]` section (the spec's line 286 is
   the older full template), and adding one would make the switch's off state differ from mvp-0.44 on a new vault. The review's own
   rule (§10) wins: off, the stored value applies, and new and old vaults alike store none.
9. **The feedback's "Show anyway" is the only hold exit from the plain surface.** The inspector can still read an attempt's raw
   record if the learner digs there; it records its own exposure, as today, and §6.0's flag for the probe's independence comes from
   the workflow only. If the owner wants the inspector held too, it reads the same `is_holding`.
10. **A pre-FG1 generated probe keeps its old rules.** The identity is registered as an item is written; an upgrade does not
    backfill items already in a vault, whose diagnostic mode still makes them single use by the attempt rule. Open question below.

### Gates that could not be made fully observational

None on this lane. Checked: the follow-up value check never runs while the workflow owns the attempt (insertion is withheld before
it); the probe contract's value refusal is reached only with no committed presentation, and a workflow's probe always has one;
`decide_probe` and repair-class divergence are logged on the row (`detail_json.observational`), and with shared repair classes that
fact goes on the router's card.

## Measured with fakes

Physical authoring calls per probe: 1 (`test_a_miss_with_two_rivals_generates_one_pinned_probe`). A transport failure: 2, the first
and the one retry the workflow admits, then the failure line (`MAX_GENERATION_ATTEMPTS`). A hard refusal, a `no_intervention` draw
or unreadable protection: 0. Every physical call is admitted and recorded through `runtime.spend.metered` under
`owner_kind=followup_generation`, one owner per job, so the owner's run on a copy reads calls and cost per probe from
`model_call` receipts. Real latency and vault growth are for that run: no paid call was made in this stage.

## Open questions for the owner

1. Backfill the single-use identity onto `pi_gen_*` items already in the owner's vaults, or leave them on the older attempt rule?
2. Q4 (§12) stands at its default: the answer is held until the probe is answered and released on a wait.
3. Run on a copy: real latency and calls per probe, whether the adversarial review fits the wait, and vault growth.

## Gate, before the Codex review and the landing (no full suite, per the owner's rule)

- `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0`.
- `lint-imports --no-cache` (empty env): 42 contracts kept, 0 broken.
- Targeted pytest, capped scope, `-n 6`: **5582 passed, 30 skipped, 8 xfailed, 0 failed** across the 257 files listed below (every FG1 file, every file exercising a changed module or pinning the chain or head, the contract files: config defaults, CLI help, serializer, desktop RPC, mobile allowlist, architecture, table roles, coordinated migrations, tracked fixtures, frozen cycles and the process-launch checks).
- Durability: `--durable-sqlite` on the FG1 files and `test_data_capture_migration.py`: 84 passed.
- Frontend: `npm install`, typecheck clean, `vitest --maxWorkers=4` on the `FeedbackScreen`, `TodayScreen` and `PracticeScreen` files touched: 132 passed; `frontend:build` ok.
- `cargo check` ok (four new passthrough commands).
- References: DB generate and validate (385 table notes, errors `[]`), desktop catalog (318 TS, 6 Rust), module catalog (1188 notes, 66 maps), vault validation passes.
- No paid call and no live call. No app or GUI launched.

Not exercised: the owner's run on a copy (latency, calls per probe with real routes, vault growth), and the full suite, both for later.

<details><summary>Test files run</summary>

tests/test_active_errors_overlay.py
tests/test_ad1_attempt_columns.py
tests/test_ad23_fix_r8.py
tests/test_ad23_fix_review.py
tests/test_ad23_pool_membership.py
tests/test_ad23_successor.py
tests/test_adaptive_difficulty_ad1.py
tests/test_ai_config.py
tests/test_approach_map_replay.py
tests/test_approach_maps.py
tests/test_assumed_known.py
tests/test_attempt_completion.py
tests/test_attempt_content_state_successor.py
tests/test_attempt_write_order.py
tests/test_batch3_landing.py
tests/test_build_study_map_routing.py
tests/test_canonical_projection_fold_skip.py
tests/test_causal_orchestrator.py
tests/test_causal_p2_acceptance.py
tests/test_causal_probe_commissioning.py
tests/test_causal_repair_sidecar_rpcs.py
tests/test_causal_shadow_selection.py
tests/test_characterization_assessment_exam.py
tests/test_characterization_probe_regrade.py
tests/test_characterization_probe_replay.py
tests/test_cli_generate_practice.py
tests/test_codex_runtime.py
tests/test_cold_retry_reschedule.py
tests/test_collection_dataset.py
tests/test_config_refactor.py
tests/test_curriculum_c1_plan_follows_path.py
tests/test_daily_loop_lo_lifecycle_serving.py
tests/test_daily_plan_reentry.py
tests/test_daily_plan_replay.py
tests/test_daily_plan_review_regressions.py
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
tests/test_deliverable_path.py
tests/test_device_eligibility.py
tests/test_diagnosis_async_router.py
tests/test_diagnosis_card.py
tests/test_diagnosis_input_provenance_landing.py
tests/test_diagnosis_pipeline.py
tests/test_diagnostic_probe_freshness.py
tests/test_doctor.py
tests/test_dual_authority_administration.py
tests/test_exam_pool.py
tests/test_exam_protection.py
tests/test_exam_protection_review.py
tests/test_exam_session.py
tests/test_facet_identity.py
tests/test_facet_state_write_on_change.py
tests/test_field_signal_production_paths.py
tests/test_field_workbench_signals.py
tests/test_figures_help.py
tests/test_figures_prefetch.py
tests/test_figures_prefetch_review_fixes.py
tests/test_followups_batch6_review_fixes.py
tests/test_followups_nov2_help_fold.py
tests/test_forecast_receipts.py
tests/test_goal_scope_material.py
tests/test_grade_resolution_pipeline.py
tests/test_held_grade_composition.py
tests/test_held_grade_evidence.py
tests/test_help_assist_work_md_migration.py
tests/test_help_fold_attach_successor.py
tests/test_hint_authored_reveal_ruling.py
tests/test_hint_blind.py
tests/test_hint_evidence.py
tests/test_hint_h2a_review.py
tests/test_hint_h2a_review_round2.py
tests/test_hint_h2a_review_round3.py
tests/test_hint_h2b_fix3.py
tests/test_hint_h2b_rereview.py
tests/test_hint_h2b_review.py
tests/test_hint_kill_switch.py
tests/test_hint_outcome.py
tests/test_hint_report.py
tests/test_hint_telemetry.py
tests/test_host_queue_revision.py
tests/test_independent_group_counting.py
tests/test_ingest_runner.py
tests/test_init.py
tests/test_instrument_servability_journeys.py
tests/test_intent_codex_rereview.py
tests/test_intent_fix_round4.py
tests/test_intent_orchestrator_rulings.py
tests/test_intent_rpc.py
tests/test_inventory_merge_parallel.py
tests/test_learner_blindness_relax.py
tests/test_learner_blindness_relax_codex_review.py
tests/test_learner_data_relax_2.py
tests/test_learner_report_superseded.py
tests/test_learner_text_gaps_composition.py
tests/test_learner_text_gaps_flow.py
tests/test_learner_text_gaps_rereview.py
tests/test_learner_text_gaps_review.py
tests/test_library_ask_review.py
tests/test_lp_claim_fixes.py
tests/test_lp_claim_fixes_review.py
tests/test_mcp_c1a_landing.py
tests/test_method_explicit_upgrade.py
tests/test_mobile_allowlist.py
tests/test_mobile_handoff.py
tests/test_mobile_jobs.py
tests/test_mobile_jobs_migration.py
tests/test_mobile_rpc.py
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
tests/test_owner_capture_1025.py
tests/test_p2_acceptance.py
tests/test_p2_leakage_suite.py
tests/test_pfc_unverified_unassessed.py
tests/test_placement_opening_probes.py
tests/test_plan_determinism.py
tests/test_plan_determinism_landing.py
tests/test_plan_follows_path.py
tests/test_post_attempt_pipeline.py
tests/test_post_attempt_worker.py
tests/test_pr4_superseded_claims_landing.py
tests/test_probe_audit.py
tests/test_probe_block_end.py
tests/test_probe_dialogue.py
tests/test_probe_episodes.py
tests/test_probe_hierarchy.py
tests/test_probe_instance_generation.py
tests/test_probe_llm_instances.py
tests/test_probe_longform_families.py
tests/test_probe_orchestration_remainder.py
tests/test_probe_policy.py
tests/test_probe_pool_empty.py
tests/test_probe_predictive_eig.py
tests/test_probe_remint.py
tests/test_probe_robust_cutover.py
tests/test_probe_surface_mint.py
tests/test_question_promotions.py
tests/test_quick_add.py
tests/test_reader_ca2_codex_rereview.py
tests/test_reader_ca2_codex_review.py
tests/test_reader_ca2_fix_orchestrator.py
tests/test_reader_ca2_one_ask.py
tests/test_reader_cues.py
tests/test_reader_followups_successor.py
tests/test_reader_guidance.py
tests/test_reader_recap_review_r2.py
tests/test_reader_recap_review_r3.py
tests/test_reader_rw2b_fix10.py
tests/test_reader_rw2b_fix11.py
tests/test_reader_rw2b_fix12.py
tests/test_reader_rw2b_fix13.py
tests/test_reader_rw2b_fix14.py
tests/test_reader_rw2b_fix4.py
tests/test_reader_rw2b_fix5.py
tests/test_reader_rw2b_review.py
tests/test_reader_rw3a_landing.py
tests/test_reader_workbench_rw2a.py
tests/test_reading_step_switch.py
tests/test_rebuild_equivalence.py
tests/test_rebuild_equivalence_review.py
tests/test_recurrence_commands.py
tests/test_recurrence_merge_composition.py
tests/test_reference_gate_imports.py
tests/test_regrade_contract_replay.py
tests/test_regrade_contract_successor.py
tests/test_regrade_contract_upgrade.py
tests/test_request_origin.py
tests/test_required_method_grading.py
tests/test_reread_safety_landing.py
tests/test_reveal_ledger.py
tests/test_route_rules_in_grader.py
tests/test_router_coldness_covariates.py
tests/test_router_g3_propensity.py
tests/test_router_g4_restraint.py
tests/test_router_g7_fallback.py
tests/test_router_offer_log.py
tests/test_router_outcomes.py
tests/test_router_presentations.py
tests/test_router_probe_ties.py
tests/test_router_r2a_landing.py
tests/test_router_r2a_serving.py
tests/test_router_r2b_agreement.py
tests/test_router_r2b_requests.py
tests/test_router_r2b_serving.py
tests/test_router_r2bc_landing.py
tests/test_router_r2c_retrieval.py
tests/test_router_r2c_teach_back.py
tests/test_scheduler.py
tests/test_scheduler_probe_eig.py
tests/test_serve_eligibility.py
tests/test_serve_eligibility_review.py
tests/test_session_ownership.py
tests/test_settings_store.py
tests/test_sidecar_close_cancels_jobs.py
tests/test_sidecar_contract.py
tests/test_sidecar_exams.py
tests/test_sidecar_probe.py
tests/test_sidecar_teach_back.py
tests/test_sidecar_trace_and_clarification.py
tests/test_sidecar_tutor_qa.py
tests/test_simulation.py
tests/test_source_deletion.py
tests/test_source_retrieval_search.py
tests/test_source_set_synthesis.py
tests/test_source_sets.py
tests/test_stuck_prompt.py
tests/test_stuck_prompt_composition.py
tests/test_subject_registry.py
tests/test_teacher_te0_confidence_events.py
tests/test_teacher_te1_successor.py
tests/test_teacher_te1b_review_fixes.py
tests/test_teacher_te1b_suggestions.py
tests/test_today_surfaces.py
tests/test_ux_phase1_round2_rereview.py
tests/test_ux_phase4_feedback.py
tests/test_ux_phase4_landing.py
tests/test_value_candidates.py
tests/test_vault_epigraphs.py
tests/test_voi_forecasts.py
tests/test_voi_stopping.py
tests/test_voi_v2.py
tests/test_workbench_assistance.py
tests/test_workbench_trace.py
tests/test_ai_tool_isolation.py
tests/test_architecture.py
tests/test_cli_help_snapshot.py
tests/test_figures_prefetch_boundary.py
tests/test_desktop_rpc_contract.py
tests/test_table_roles.py
tests/test_coordinated_migrations.py
tests/test_tracked_fixture_databases.py
tests/test_sidecar_serializer_snapshot.py
tests/test_e0_relabel_round.py
tests/test_followup_journey.py
tests/test_followup_router.py
tests/test_followup_single_use.py
tests/test_followup_generate_e2e.py
tests/test_followup_workflow.py
tests/test_followup_successor.py
tests/test_followup_migration.py

</details>

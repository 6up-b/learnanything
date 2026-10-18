# Adaptive difficulty AD1: Codex review and fix round

Stage `adaptive-difficulty-ad1`, branch `adaptive-difficulty/ad1`, worktree
`learnanything-ad1`. Codex reviewed `16a0071f2..b85acc8a0` (codex-job
`20261018-154345-vMSgui`): two High and eight Medium findings. This round
fixes all ten. Each fix has a test in `tests/test_ad1_codex_review_fixes.py`.
16 of its 17 tests fail on `b85acc8a0`, the tip Codex read. They were run
against that tip's `src/` and `migrations/` through `git archive` into
`fixtures-local/tmp/old` with `-o pythonpath=`. The 17th test,
`test_a_refused_forecast_appends_no_judgment`, is F8's control and passes on
both trees.

No model calls were made: no paid or live calls and no smoke runs on a vault
copy. Every model-backed path is tested with fakes (`tests/ad_fakes.py`).

## Review

### Findings

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Historical audits can send held-out text to models | fixed | `5db4ad2a1` | `test_historical_snapshots_of_held_out_material_are_never_audited`. Its sentinel reached the Decider body on the old tree. `test_a_revision_is_protected_by_its_own_source_even_under_an_ordinary_id` |
| F2 | High | Outside forecasts use post-serve knowledge while claiming pre-serve inputs | fixed | `5db4ad2a1` | `test_outside_forecasts_send_the_inputs_frozen_at_the_serve`. On the old tree the card read `correct` after the regrade. `test_a_presentation_without_frozen_inputs_is_never_forecast` |
| F3 | Medium | Reopening an unrecorded presentation fabricates historical receipts | fixed | `5db4ad2a1` | `test_reopening_a_presentation_served_while_ad_was_off_records_nothing`. The old tree wrote 2 backdated receipts |
| F4 | Medium | Delayed tutor answers are backdated before they existed | fixed | `5db4ad2a1` | `test_a_pending_tutor_answer_is_stamped_when_it_completes` (the real pending-to-answered lifecycle, and an answer later than the overlap window). `test_the_tutor_turn_stamps_its_answer_on_its_own_clock` |
| F5 | Medium | Background preparation bypasses the vault lifecycle fence | fixed | `5db4ad2a1` | `test_a_vault_switch_fences_the_feature_audit` (the registry closes while the Decider request is out), `test_a_vault_switch_fences_the_outside_forecasters` |
| F6 | Medium | Concurrent preparations can purchase the same audit twice | fixed | `5db4ad2a1` | `test_overlapping_preparations_audit_a_revision_once` (`[A,B]` and `[B]` on two threads; the old tree asked about B twice), `test_a_claim_held_by_another_process_is_skipped` |
| F7 | Medium | The configured metered price fails parameter classification | fixed | `5db4ad2a1` | `test_a_configured_ad_price_is_a_classified_config_leaf` (`price_per_million = 1.0`) |
| F8 | Medium | Outside-forecaster verdicts never reach judgment_ledger | fixed | `5db4ad2a1` | `test_accepted_outside_forecasts_append_one_judgment_each`, `test_a_refused_forecast_appends_no_judgment` |
| F9 | Medium | Backfill dry-run does not estimate the work it will charge | fixed | `5db4ad2a1` | `test_the_backfill_dry_run_plans_routes_through_the_spend_framework` (metered with no price, priced, and the Decider switch off); `test_ad_backfill_dry_run_plans_and_writes_nothing` updated |
| F10 | Medium | New-item preparation is missing from authoring and import | fixed | `5db4ad2a1` | `test_a_reload_prepares_the_revisions_published_since_the_last_load`, `test_the_watchers_changed_items_are_prepared` |

The regenerated references are commit `0998ab337` (head 213, 0 errors).

### What changed

- **F1.** `protection.Protection` evaluates the held-out predicate once per
  pass and checks each revision. `covers(item)` asks `held_out_item_ids` of
  the revision's own canonical exercise and provenance refs, not only whether
  its id is among the current items. It still fails closed.
  - The backfill's `_revisions` uses it for current items and for every
    `practice_item_snapshots` revision: a snapshot of a deleted item, or an
    earlier revision under an ordinary id.
  - `audit_revision`, `forecast_item`, `forecast_presentation` and the serve
    hook use the same guard. The dry run reports `protected_skipped` per
    revision.
- **F2.** The serve transaction freezes the `llm_v3` request inputs
  (`outside.freeze_presentation_inputs`). The frozen state is the served
  revision's item view plus the history card as the serve saw it: the
  incumbent's numbers from its own receipt, and each earlier attempt's grade
  as it then stood.
  - It is stored as an `item_forecast_payloads` request row, owner key
    `ad_llm_v3_state:plan_presentation:<id>`, `created_at` = the serve, with
    its state hash.
  - The background job sends exactly that state and verifies the hash.
    Receipts carry `inputs.state_hash` and `inputs.frozen_inputs`.
  - A presentation with no frozen inputs is `no_frozen_inputs`, and nothing
    is sent.
- **F3.** `daily_plan.engine._serve` calls the AD hook only when this serve
  inserts the `plan_presentations` row. A reopen keeps the first serve's
  `served_at`, so recording then would backdate today's state.
  - A presentation served while AD was off, or whose first recording rolled
    back, keeps no AD record and its inputs stay unavailable.
- **F4.** Migration 213 adds `question_events.answered_at`, nullable with no
  default. `Repository.update_question_event_answer` sets it once, on the
  first `answered` update (`COALESCE`); a failed turn leaves it null. The
  tutor turn passes its own clock.
  - The sweep stamps a tutor exchange with `COALESCE(answered_at,
    created_at)`. A row written already answered has its completion time in
    `created_at`.
  - The sweep reads every answered reader or library exchange not yet
    recorded (an anti-join), ignoring the overlap window's lower bound, so a
    slow answer is never missed.
  - Legacy limit: rows answered before this migration keep `created_at`.
- **F5 and F6.** New module `adaptive_difficulty/claims.py`. Each unit of
  paid work takes a durable claim in `judgment_work_claims` (task
  `ad_background_work`) through the map builds' lease and heartbeat:
  - a revision's audit, keyed by content hash;
  - a revision's `llm_v1:item`;
  - a presentation's `llm_v3` pair.

  The claim is taken without waiting: `busy` when someone else holds it. The
  holder re-reads what is persisted before asking. Work writes through
  `FencedRepository`:
  - judgments, payloads and receipts, and a model call's start receipt
    (written before the request is sent), commit only in `_fenced_txn`, which
    holds while the lease and the job's own registry fence hold and registers
    the commit against a close;
  - finish receipts and the spend ledger are not fenced, so a request already
    sent keeps its accounting.

  The background launcher passes the fence object to the job, not
  `fence.live`. `worker.require_live()` runs before each request. A closed
  fence gives `stale`.
- **F7.** `adaptive_difficulty.price_per_million` joins the AD rule
  (`structural`, `operational`).
- **F8.** An accepted outside forecast appends one `judgment_ledger` row in
  the same transaction as its payloads and receipt, and only when the receipt
  is newly written, so the write is idempotent.
  - The row has task `ad_item_forecast`. The left side is
    `practice_item_revision` (the content hash) for `llm_v1`, or
    `plan_presentation` for `llm_v3`; the right side is the forecaster.
  - The judge is `llm` or `decider`, with model, prompt version, the request
    hash as `input_hash`, `p` as score, and the receipt key and id in the
    rationale.
  - A refused or failed forecast gets no verdict.
- **F9.** The dry run plans each resolved route through the spend framework:
  - LLM routes go through `PaidCalls.plan`, with the output allowance per
    call, the billing label (`estimated_only` on the subscription) and a
    refusal when a metered route has no price;
  - the Decider is planned at its profile's listed input price, with no
    output allowance;
  - with the Decider on, the LLM fallback's worst-case exposure is shown;
    with `[decider_routes] ad_feature_audit` off, the LLM is primary and the
    Decider gets 0 requests;
  - a `spend` block gives the cap, today's spend, what remains, the
    worst-case metered dollars (null when a part is unpriced) and
    `fits_today`.
- **F10.** `SidecarContext.load` compares a reload of the same vault with the
  vault it replaces, and `refresh_vault_files` passes its changed ids. Every
  new or edited active revision is then prepared in the background
  (`background.schedule_new_revisions`); a publication or import ends in one
  of the two.
  - A first open schedules nothing, because the existing pool belongs to the
    owner-run backfill (dry-run first).
  - The plan hook is still the recovery path, for example after a CLI import.
- **Spec amendments**, in `spec_adaptive_difficulty_v1.md`: §5.11 (the tutor
  exchange's source time), §8.1 (frozen `llm_v3` inputs, fresh serves only,
  the `ad_item_forecast` verdict) and the §14 AD1 migration line
  (`question_events.answered_at`).
- **Head fixture.** `fixtures/migration_head_213/state.sqlite` was rebuilt
  from `16a0071f2`'s `migration_head_212` through the backup API and
  `apply_migrations` under the scratch-copy allowance, then set to
  `journal_mode=DELETE`. The five hard-coded paths are unchanged (still
  `migration_head_213`).

### The review's "claims that don't hold", now

- "Inputs … completed before the serve": they are now the frozen inputs (F2).
- "A reopened step writes nothing new": only the inserting serve records (F3).
- Reading receipts reproduce what each serve saw: tutor exchanges are now
  stamped at completion (F4).
- Jobs check their fence: every unit is claimed and fenced, with a liveness
  check before each request (F5).
- Null-default pricing is classified (F7).
- "Once per revision": a durable claim plus a re-check under the claim (F6).

## Gate results

Test runs used `TMPDIR=<worktree>/fixtures-local/tmp` and `LEARNLOOP_AD_MODELS=off`
(set by conftest). There was no full suite, no whole durability lane and no
whole vitest run (owner rule, 2026-10-17). The frontend and `src-tauri` are
unchanged, so npm and cargo were not run.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 27 kept, 0 broken |
| targeted pytest `-n auto`, 216 files (listed below) | **4249 passed, 2 xfailed** (741 s) |
| AD files rerun after the `ad_fakes.everything_text` change (6 files) | 55 passed |
| `pytest -m durability` on the migration and schema files (10 files) | 46 passed |
| `pytest --durable-sqlite` on the AD1 behaviour files (4 files) | 44 passed |
| threaded tests (F5, F6, F10) rerun alone 3 times | 4 passed ×3 |
| new tests against `b85acc8a0`'s code | 16 failed, 1 passed (F8's control) |
| `db_generate_reference.py` / `db_validate_reference.py` | regenerated; 0 errors |
| `git diff --check` | clean |

**Targeted files (216).** The selection rule, for the landing gate:

- every AD1 file;
- every file that imports `learnloop.daily_plan.engine` (the `_serve` change);
- every file that touches `question_events` or
  `update_question_event_answer`;
- the tutor files;
- every `SidecarContext()` user and `refresh_vault_files` user;
- every file naming `migration_head_213`;
- the contract tests: architecture, registry audit, config refactor, CLI
  help snapshot, sidecar serializer snapshot, desktop RPC contract, mobile
  allowlist, table roles, coordinated migrations, tracked fixture databases,
  migrations, SQLite WAL.

The files:

`test_ad1_attempt_columns.py test_ad1_codex_review_fixes.py test_ad1_migration.py test_ad1_outside_and_cli.py
test_ad1_reading_opportunities.py test_adaptive_difficulty_ad1.py test_approach_map_replay.py test_approach_maps.py
test_approach_maps_schema.py test_architecture.py test_block_chooser_interface.py test_canonical_projection_rollout.py
test_capture_desktop.py test_capture_route_recovery.py test_chatgpt_plan_sidecar.py test_cli_help_snapshot.py
test_coldness_receipt.py test_config_refactor.py test_contamination_report.py test_coordinated_migrations.py
test_daily_loop_lo_lifecycle_serving.py test_daily_loop_reader_retire.py test_daily_loop_reentry_break.py
test_daily_loop_reentry_cap.py test_daily_loop_reference_adoption.py test_daily_loop_start_minutes.py
test_daily_plan_build.py test_daily_plan_composition.py test_daily_plan_kill_switch.py
test_daily_plan_owner_decisions.py test_daily_plan_reading.py test_daily_plan_reentry.py test_daily_plan_replay.py
test_daily_plan_review_regressions.py test_daily_plan_rpc.py test_decider_landing.py test_desktop_rpc_contract.py
test_diagnosis_async_router.py test_diagnosis_card.py test_diagnosis_input_provenance_landing.py
test_diagnosis_input_provenance.py test_diagnosis_replay.py test_dialogue_causal_join.py
test_evsi_router_composition.py test_evsi_staged_binding.py test_exam_protection_identity.py
test_exam_protection_landing.py test_exam_protection.py test_exam_protection_review.py test_facet_identity_actions.py
test_facet_reword_paths.py test_facet_rewords.py test_family_memory_projection.py test_field_signal_production_paths.py
test_goal_scope_material.py test_graph_editor_reads.py test_help_assists_schema.py test_hint_authored_reveal_ruling.py
test_hint_blind.py test_hint_discriminating.py test_hint_evidence.py test_hint_feedback_texts.py
test_hint_h2a_review.py test_hint_h2a_review_round2.py test_hint_h2b_review.py test_hint_kill_switch.py
test_hint_outcome.py test_hint_report.py test_hint_service.py test_hint_telemetry.py test_ingest_jobs.py
test_ingest_latency_journey.py test_instrument_servability_journeys.py test_integration_daily_loop_field.py
test_interaction_signals.py test_keep_local_retired.py test_km2_activation.py test_knowledge_map_text_neighbors.py
test_learner_pick_proposal.py test_learner_text_gaps_flow.py test_learner_text_gaps_review.py test_library_ask.py
test_library_asks_migration.py test_mcp_c1a_narrow.py test_mcp_runtime.py test_mcp_tools.py
test_method_explicit_upgrade.py test_migrations.py test_mobile_allowlist.py test_mvp010_upgrade.py
test_mvp011_upgrade.py test_mvp013_upgrade.py test_mvp014_upgrade.py test_mvp015_upgrade.py test_mvp016_upgrade.py
test_mvp017_upgrade.py test_mvp018_upgrade.py test_mvp020_upgrade.py test_mvp021_upgrade.py test_mvp022_upgrade.py
test_mvp023_upgrade.py test_mvp024_upgrade.py test_pfc_unverified_unassessed.py test_placement_opening_probes.py
test_placement_sidecar.py test_placement_signals.py test_plan_determinism_landing.py test_plan_determinism.py
test_practice_index_adapters.py test_probability_prep.py test_question_promotion_jobs.py test_question_promotions.py
test_question_queue.py test_question_signal.py test_reader_branches.py test_reader_dialogue.py
test_reader_inquiry_status.py test_reader_pdf_selection.py test_reader_recap.py test_reader_rw3a_landing.py
test_reader_workbench_rw2a.py test_reading_request_sweep.py test_reading_step_switch.py test_rebuild_orchestrator.py
test_recurrence_commands.py test_registry_audit.py test_regrade_contract_replay.py test_regrade_contract_successor.py
test_regrade_contract_upgrade.py test_required_method_round3_review.py test_reread_safety.py test_reveal_ledger.py
test_router_card.py test_router_g1_feasibility.py test_router_g4_restraint.py test_router_g7_fallback.py
test_router_offer_log.py test_router_outcomes.py test_router_p2_bridge.py test_router_presentations.py
test_router_probe_ties.py test_router_r1_composition.py test_router_r2a_landing.py test_router_r2a_serving.py
test_router_r2b_serving.py test_router_r2c_retrieval.py test_router_r2c_teach_back.py test_route_rules_in_grader.py
test_router_why_copy.py test_rw4_kill_switches.py test_scheduler_requested_floor.py test_serve_eligibility.py
test_serve_eligibility_review.py test_shadow_rebuild.py test_sidecar_adjudication.py test_sidecar_animation.py
test_sidecar_append.py test_sidecar_blueprint_picker.py test_sidecar_contract.py test_sidecar_diagnostic.py
test_sidecar_epigraphs.py test_sidecar_exams.py test_sidecar_goals.py test_sidecar_golden_path_assessment.py
test_sidecar_golden_path.py test_sidecar_ingest_m3.py test_sidecar_item_authoring.py
test_sidecar_item_presentation.py test_sidecar_knowledge_model.py test_sidecar_ladder.py test_sidecar_measurement.py
test_sidecar_probe.py test_sidecar_queue_serialization.py test_sidecar_quick_add.py test_sidecar_reader_p3.py
test_sidecar_reader_p3_slice2.py test_sidecar_reader_p3_slice3.py test_sidecar_reader_pdf_view.py
test_sidecar_reader.py test_sidecar_registry.py test_sidecar_remediation_surfaces.py
test_sidecar_serializer_snapshot.py test_sidecar_source_retrieval.py test_sidecar_span_view.py
test_sidecar_synthesis.py test_sidecar_teach_back.py test_sidecar_trace_and_clarification.py
test_sidecar_transport.py test_sidecar_tutor_qa.py test_source_exercise_import.py test_source_retrieval_tutor.py
test_sqlite_wal.py test_stuck_prompt.py test_table_roles.py test_tier1_decider.py test_tracked_fixture_databases.py
test_tutor_citations.py test_tutor_delivery_fixes.py test_tutor_practice_request.py test_tutor_promotion_service.py
test_tutor_promotion_w2.py test_tutor_qa.py test_tutor_tool_requests.py test_ux_phase1_add_source.py
test_ux_phase1_connect_ai.py test_ux_phase1_finish.py test_ux_phase1_landing.py test_ux_phase1_review_fixes.py
test_ux_phase1_round2_rereview.py test_ux_phase1_round2_review.py test_ux_phase4_feedback.py
test_ux_phase4_landing.py test_vault_watcher_refresh.py test_voi_merge_composition.py test_voi_stopping.py
test_voi_v2.py`

Durability (`-m durability`): `test_ad1_migration.py test_approach_maps_schema.py test_coordinated_migrations.py
test_diagnosis_replay.py test_help_assists_schema.py test_hint_feedback_widening.py
test_learner_text_source_widening.py test_library_asks_migration.py test_sqlite_wal.py
test_exam_protection_identity.py`.

## Open points for the orchestrator or the owner

- **A shared table changed.** F4 adds `question_events.answered_at` (nullable,
  set by the tutor's pending-to-answered update). This is outside AD's own
  tables but inside its migration 213. Rows answered before the migration
  keep `created_at` as their exchange time, which is the only historical
  record.
- **New revisions are prepared after a reload (F10).** Every new or edited
  item revision a reload or the watcher reports is audited and gets an
  `llm_v1:item` forecast in the background. A bulk import of many items
  therefore queues that many audits: Codex on the subscription, and the
  Decider inside `adaptive_difficulty.daily_spend_cap_usd`. The spec's §7.2
  "after any item is generated or imported" asks for exactly this. A first
  open still schedules nothing.
- **Frozen inputs are pruned (F2).** They live in the WORKFLOW payload table
  and are pruned after `router.payload_retention_days`. A presentation whose
  background forecast never ran within that window is never forecast, and it
  reports `no_frozen_inputs`.
- **Presentation paths are plan-only (unchanged).** The review's conformance
  table noted that probe and scheduler-bound presentations are not covered.
  That is not a finding, and nothing changed here.

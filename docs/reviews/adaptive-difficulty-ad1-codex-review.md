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

## Re-review (Codex, `b85acc8a0..f9429d94e`)

Codex confirmed F1 and F2 fixed and reopened the stage with three new
findings. Each one was reproduced first. The tests in
`tests/test_ad1_codex_rereview_fixes.py` failed on `f9429d94e` for the reason
each docstring gives, and they pass on the fix. All of them use fakes only,
and no model was called.

| id | severity | title | verdict | commit | test or reason |
|----|----------|-------|---------|--------|----------------|
| F11 | High | Frozen history bypasses newly applied held-out protection | fixed | `bae5dcaf9` | `test_frozen_history_marked_held_out_after_the_serve_is_never_sent[still_current, revision_since_replaced]`, `test_a_target_revision_held_out_after_the_serve_is_never_sent`, `test_frozen_inputs_without_their_source_identities_are_never_sent`, `test_unprotected_frozen_inputs_are_still_sent_exactly` |
| F12 | Medium | An edit during preparation loses the new revision's job | fixed | `bae5dcaf9` | `test_an_edit_during_a_preparation_prepares_the_new_revision_too` |
| F13 | Medium | "Worst-case" spend omits permitted retries | fixed | `bae5dcaf9` | `test_the_worst_case_plans_the_permitted_truncation_retry` |
| (note) | - | Extra blank line at EOF in `tests/test_ad1_codex_review_fixes.py` | fixed | `bae5dcaf9` | `git diff --check` is clean |

**F11.** Before sending, the job now revalidates everything the frozen state
quotes against the held-out predicate as it stands at send time.

- *What the serve freezes.* `freeze_presentation_inputs` stores
  `protection_identities` beside the state. These are kept in the payload and
  are never sent. They hold the `source_identity` (item id, plus the block
  keys and whole extractions of the item's own canonical exercise and
  provenance refs) of the served revision and of each history item the card
  quotes.
- *The check before sending.* `forecast_presentation` builds a fresh
  `Protection` under the presentation's claim, immediately before sending.
  It refuses the whole forecast (`protected`) when any of these is protected:
  - the current item;
  - the frozen target revision;
  - any frozen history identity (`Protection.covers_identity`: the id, or the
    frozen source keys, using the same rule as `held_out_item_ids`).
- *Why the frozen sources matter.* An item that has since been replaced by
  ordinary practice is still judged by the revision the card quotes.
- *Fail closed.* Frozen inputs without the identities do not validate
  (`no_frozen_inputs`), and an identity that cannot be read counts as
  protected.

**F12.** A preparation job's in-flight key is now `content_key` of the
sorted `(item_id, revision hash)` pairs instead of the item ids alone. A
reload that finds A2 while A1's job is still running therefore starts A2's
job. A revision that two jobs share is still paid for once, under its durable
claim (F6).

**F13.** `_llm_plan` now plans every attempt that execution permits:

- the first attempt at the route's output allowance;
- plus `max_retries` (the execution path's `_CAPS`, 1 for both the feature
  audit and `llm_v1:item`) retries at `TRUNCATION_RETRY_FACTOR` x the
  allowance.

The test shows the planned worst case equals the sum of the estimates that a
truncating metered fake reserved during execution. A remaining cap between
the first-attempt cost and that sum now reports `fits_today: false`. The plan
also reports `attempts_per_call` and `retry_output_tokens`. The doubled
allowance is an upper bound: a transport ceiling can only lower it. The
Decider has no retry path, so its plan is unchanged.

### Gate (re-review fix step)

- `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2`.
- `uv run lint-imports --no-cache`: 27 kept, 0 broken.
- `uv run pytest -n auto` (`TMPDIR=fixtures-local/tmp`) over
  `tests/test_ad1_codex_rereview_fixes.py tests/test_ad1_codex_review_fixes.py
  tests/test_ad1_attempt_columns.py tests/test_ad1_migration.py
  tests/test_ad1_outside_and_cli.py tests/test_ad1_reading_opportunities.py
  tests/test_adaptive_difficulty_ad1.py tests/test_decider_landing.py
  tests/test_architecture.py tests/test_registry_audit.py`: **111 passed**.
- The new file run alone, serially, three times: 7 passed each time. This
  checks the threaded F12 test.
- `db_generate_reference.py`, then `db_validate_reference.py`: 0 errors. The
  regenerated commit labels and line citations are in `58d269b95`.
- Not run, because nothing they cover changed:
  - durability: there is no migration or DB/connection change this round;
  - frontend and cargo: nothing under `apps/` changed;
  - config keys: none added, so the parameter registry is unchanged.
- Model calls: 0.

## Fix round 3 (orchestrator)

The final Codex verify (codex-job `20261018-164756-bRhYCN`, over
`f9429d94e..da8c3f611`) confirmed F1, F2, F12 and F13 fixed and reopened
F11 [High] at `outside.py:587`. The held-out check of the frozen identities
ran once, before the whole forecaster pair. Two cases still leaked:

- a source marked held out while the first LLM request ran still reached
  the Decider request after it;
- an LLM retry after `AIOutputTruncated` still sent it.

Both outcomes reported `ok`.

**Binding ruling (orchestrator).** Every frozen identity is revalidated
against the current held-out predicate immediately before each physical
model request. That covers:

- each forecaster in the pair, the Decider request, and every retry or
  fallback attempt;
- every other place AD sends frozen or historical content: the feature
  audit's Decider request and its LLM fallback, and the backfill.

The check has one home, a pre-send guard in AD's paid-call path, not one
check per call site. When it fails, that request and every later request in
the job are refused as `protected`. Requests already sent keep their
accounting. No receipt or judgment may record `ok` on a refused request.

| id | severity | title | verdict | commit | test |
|----|----------|-------|---------|--------|------|
| F11 (reopened) | High | Protection changes between model requests still leak frozen history | fixed | `b1e520ce7` | `tests/test_ad1_send_guard.py` (below) |

**The guard.** `learnloop.adaptive_difficulty.sending` is AD's only
paid-call path. `ask_llm` wraps `PaidCalls` and `ask_decider` wraps
`decider_judgments.ask_decider`. They carry every AD request:

- `llm_v3:llm`, `llm_v3:decider` and `llm_v1:item` in `outside.py`;
- the feature audit's Decider request and its LLM fallback in
  `feature_audit.py`;
- the backfill and the background preparation, which run those two.

Each job builds one `SendGuard` from what its requests quote:

- the item id;
- the current revision;
- for a presentation, the frozen `protection_identities` (the target and
  the history).

`SendGuard.check` holds the why-comment that cites F11. It reads the
predicate afresh each time with `protection.protection`. A predicate the
caller computed earlier can add ids, but it never replaces today's
predicate. The check is consulted at three points:

- **before every attempt.** This is `PaidCalls`' `admit` hook, which it
  also asks before allowing a retry, so the retry after `AIOutputTruncated`
  is checked again. The Decider request is checked before its admission.
- **before every physical request.** The guard is also installed as the
  context's request gate (`ai.execution.gate_model_requests`). It sits in
  front of any gate already installed, found through the new
  `ai.execution.active_request_gate()`, and never replaces it. A mark that
  lands after the attempt was admitted but before the transport sends the
  request is still refused.
- **before each record.** A response that comes back after its content was
  marked held out does not get its receipt, payloads (which quote the
  content) or judgment written. This step is stricter than the ruling,
  which forbids only an `ok` built on a refused request. It also keeps A8's
  "never written into an AD payload".

The first refusal is sticky. `ProtectedContent` is an `AIInterrupted`, so no
retry loop or transport relabels it. Every later request of the job is then
refused, and AD reports `protected`:

- the forecasters return `protected` with no receipt;
- the audit returns `status: protected`, with `decider_status` or
  `llm_status` set to `protected`.

A transport that reports the refusal as its own failure is still classified
`protected`, through the sticky state. Requests already sent keep their
`model_call_receipts` and their spend. The tests assert this: one completed
or truncated receipt per request sent, and none for a refused one. The old
one-time check (`_frozen_protected`) is gone. Its revalidation rule,
`Protection.covers_identity`, is unchanged.

**Tests** (`tests/test_ad1_send_guard.py`, fakes only). 6 of 7 failed on
`da8c3f611` through `git archive da8c3f611` into `fixtures-local/tmp` with
`-o pythonpath=<tmp>/src`, each for the behavioral reason in its docstring.
None failed on an import.

- `test_a_source_held_out_during_the_llm_request_refuses_the_decider_request`
  is the verify's first reproduction. On the old tree the Decider was sent
  the sentinel.
- `test_a_source_held_out_inside_a_truncated_attempt_refuses_the_retry` is
  the verify's second. On the old tree 2 LLM prompts were sent.
- `test_a_source_held_out_just_before_the_physical_request_is_refused_by_the_request_gate`
  covers the request-gate layer. On the old tree the Decider request was
  sent.
- `test_a_revision_held_out_during_the_decider_request_refuses_the_llm_fallback`
  covers the feature audit's fallback. On the old tree the fallback was sent
  the stem and both judges were ledgered.
- `test_a_revision_held_out_inside_a_truncated_fallback_attempt_refuses_the_retry`
  covers the fallback's retry. On the old tree 2 prompts were sent.
- `test_a_unit_held_out_while_the_backfill_runs_refuses_its_later_forecasts`
  covers the backfill. On the old tree it reused its start-of-run predicate
  and forecast the newly held-out items.
- `test_with_nothing_protected_the_pair_is_unchanged` is the control. It
  passes on both trees: another span is marked held out mid-pair, both
  forecasts are sent exactly and recorded `ok`, with two judgments.

### Gate (fix round 3, targeted per the owner rule)

- `uv run lint-imports --no-cache`: 27 kept, 0 broken.
- `uv run pytest -n auto` (`TMPDIR=fixtures-local/tmp`): **283 passed**.
  The files:
  - AD: `tests/test_ad1_send_guard.py tests/test_ad1_codex_rereview_fixes.py
    tests/test_ad1_codex_review_fixes.py tests/test_ad1_attempt_columns.py
    tests/test_ad1_migration.py tests/test_ad1_outside_and_cli.py
    tests/test_ad1_reading_opportunities.py tests/test_adaptive_difficulty_ad1.py`;
  - required: `tests/test_architecture.py tests/test_registry_audit.py
    tests/test_judge_routes.py`. No `test_parameter_registry*` file exists;
    the parameter registry is covered by `test_registry_audit.py`;
  - touched (the request gate, the model-call receipts):
    `tests/test_decider_landing.py tests/test_model_call_receipt_owners.py
    tests/test_glm_ocr.py tests/test_ux_phase1_review_fixes.py`.
- `--durable-sqlite` on `tests/test_ad1_send_guard.py`: 7 passed.
- `db_generate_reference.py`, then `db_validate_reference.py`: 0 errors.
  The commit labels and the moved line citations (`backfill.py`,
  `feature_audit.py`) were regenerated in `75b172c66`.
- `git diff --check`: clean.
- Model calls: 0.

## Fix round 4 (orchestrator)

The orchestrator's whole-stage Codex verify (codex-job
`20261018-170901-bDctp7`) confirmed four things:

- migration 213 keeps all 534 rows across 335 tables, and the FK check is
  clean;
- the head fixture;
- the request-gate nesting and its thread isolation;
- nothing changed in serving, scheduling, evidence or replay.

It also accepted round 3's record check as the conservative reading of A8,
and it reopened five items. The orchestrator's binding rulings are applied
below. Each item has a test that failed on `de34b5d01`:

- backend: `git archive de34b5d01` into `fixtures-local/tmp/before-de34`,
  with `-o pythonpath=<tmp>/src`;
- frontend: the new tests run against `de34b5d01`'s `apps/learnloop-tauri`,
  extracted to the scratchpad.

| id | severity | title | verdict | commit | test |
|----|----------|-------|---------|--------|------|
| V1 | High | Protection uses stale vault content | fixed | `d03b6bba0` | `test_a_same_vault_reload_adding_an_exam_scope_refuses_the_next_request_and_the_record`, `test_another_vault_or_none_loaded_refuses` |
| V2 | Medium | Bulk preparation bypasses the workload bound | fixed | `d03b6bba0` | `test_an_import_of_1000_revisions_prepares_at_most_20_per_run`, `test_two_watcher_batches_share_one_worker` |
| V3 | Medium | Model checkpoints bypass the lifecycle fence | fixed | `d03b6bba0` | `test_an_answer_after_a_vault_switch_writes_no_checkpoint_and_settles_its_spend` |
| V4 | Medium | A restored draft can mislabel its second hint as its first | fixed | `d03b6bba0` | vitest: `a restored draft with an earlier hint and no marker records no marker at a later hint`; `useFirstHintProgress.test.tsx` |
| V5 | Medium | Tutor receipts lose the required answer-mode subkind | fixed | `d03b6bba0` | `test_a_reader_tutor_exchange_is_recorded_under_its_answer_mode`; `test_reading_opportunities_frozen_and_ordered_by_source_time` corrected |

**V1.** `SendGuard` now takes `live_vault`, a provider of the vault that is
loaded at the time of the check.

- The sidecar passes `SidecarContext.loaded_vault` from the reload, the
  watcher and the plan-read hooks. It reaches every job through
  `schedule_*`, `prepare_items`, `audit_revision`, `forecast_item` and
  `forecast_presentation`.
- Every check builds the held-out predicate from that vault: each attempt,
  each physical request and each record. A same-vault reload's source-set
  or exam-scope edit is therefore seen by jobs that are already running.
- If the provider returns another vault (a different root), none, or an
  error, the request is refused as `protected`. A vault switch is also
  stopped by the job's fence.
- The forecast inputs stay frozen; only protection is re-resolved.
- A caller with no provider keeps its own vault as the current one. The CLI
  backfill is such a caller: it never reloads.

The test covers the real path through the sidecar:

- `ctx.load`, then an edited item;
- `ctx.reload`, which starts the preparation;
- while the audit's Decider request runs, the owner adds an exam scope to
  the vault's source-sets file and `ctx.reload` runs again;
- the test's held-out predicate depends only on the source sets of the vault
  object it is handed, as the real one does.

Result: the audit records nothing, and the `llm_v1:item` request is never
sent. On `de34b5d01` the request was sent with the held-out stem.
`test_another_vault_or_none_loaded_refuses` fails there only because
`live_vault` did not exist yet (`TypeError`).

**V2.** Preparation now has one deduplicated queue per vault, keyed by its
database, with one worker at a time.

- Each queued entry is the revision as it was found, so F12's A1/A2 still
  both get prepared.
- A run takes at most `PREPARE_LIMIT` (20) revisions. A caller's `limit`
  can only lower that, and reload no longer passes `limit=len(ids)`.
- The rest wait for a later run. The next reload starts one, even with
  nothing new, and so does a plan read. A run never chains into the next one.
- Watcher batches feed the same queue. While the worker runs, a second batch
  is only queued.
- Revisions the run never reached, because its vault was switched or closed,
  go back to the front of the queue.
- No config key was added.

The tests replace the audit and the forecast with recorders:

- 1,000 imported revisions give runs of exactly 20: 20, 40, 60 after three
  triggers, each revision once, in arrival order. On `de34b5d01` one run
  prepared all 1,000.
- Two watcher batches give one worker (at most one at a time), and the
  second batch runs at the next trigger. On `de34b5d01` a second thread was
  started.

**V3.** `FencedRepository.save_model_checkpoint` and
`discard_model_checkpoint` now write in `_fenced_txn`, as the approach-map
repository does. A checkpoint that is fenced out is dropped (logged), and
the job's next write reports `stale`. The finish receipt of a request
already sent, and the spend settlement on the base repository, stay
deliberately unfenced.

The test sends a metered `llm_v1:item` request, and the vault's registry is
closed mid-request:

- no `model_work_checkpoints` row is written, and the outcome is `stale`;
- the root model-call receipt is `completed`;
- the `source_service_spend` reservation is `settled`.

On `de34b5d01` the checkpoint row was written.

**V4.** `useFirstHintProgress` now takes `hintsBefore`. `PracticeScreen`
sets it from the restored draft's hints (`restoredHints > 0`). It also gets
`noteUntimedHint()`, which `PracticeScreen` calls when a book is carried on
the problem. Either one latches "the first hint has already happened" when
no marker was saved. For that attempt the marker stays null (unknown), so
the next reveal is never recorded as the first. A saved marker is always
kept.

The vitest scenario restores a draft with one hint and no marker, the
learner types, then reveals another hint. Submit sends no
`firstHintProgress`, and no draft save carries one. On `de34b5d01` it sent
`draft_started`. A fresh draft still records `no_draft` or `draft_started`
at its first hint (the existing tests, plus a hook-level control).

**V5.** The answer mode was persisted only in the Reader dialogue's
`reader_answer_submitted` interaction event, on its synchronous path. It was
not on the question event, and not on the tutor's own path, which also
serves other callers. So, per the ruling:

- Migration 213, still unlanded, gains a nullable
  `question_events.answer_mode`, CHECKed to `answer_directly`,
  `help_me_reason` or `ask_me_first`.
- `tutor_qa.ask_question` sets it once, when the question is asked, for a
  reader question. `insert_question_event` writes it.
- The sweep's subkind for a tutor exchange is that answer mode. It is
  `unknown` where none was stored: every row from before 213, and every
  library question, which has no answer mode.
- `ad_reading_opportunities` has no context field, so the context is
  dropped from the receipt.
- The carve-out allowlist (`reading.SOURCES`) now names the three modes and
  `unknown`.
- `test_reading_opportunities_frozen_and_ordered_by_source_time`, which
  asserted subkind `reader`, now asserts the answer mode.

The new test asks through `reader_dialogue.ask` with `ask_me_first`, and
records `ask_me_first`. A row inserted without a mode records `unknown`. On
`de34b5d01` the subkind was `reader`. `test_ad1_migration` covers the new
column: nullable, the three values accepted, any other value refused.

- **A shared table changed.** `question_events.answer_mode` is a second
  shared-table column inside migration 213, beside F4's `answered_at`.
- **Head fixture.** `fixtures/migration_head_213` was rebuilt the same way
  as before:
  - a backup-API copy of git `16a0071f2`'s `migration_head_212`;
  - only 213 applied, under `UPGRADE_SCRATCH_COPY`;
  - `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE`, header
    bytes 1/1, `integrity_check` ok, `foreign_key_check` empty;
  - copied into place with the backup API, with no companion files;
  - its README updated.
- **Open point for the owner.** Library tutor exchanges have no answer mode,
  so all of them are `unknown`. If the owner wants them told apart from
  pre-213 rows, a separate subkind needs a ruling.

### Gate (fix round 4, targeted)

- `uv run lint-imports --no-cache`: 27 kept, 0 broken.
- `uv run pytest -n auto` (`TMPDIR=fixtures-local/tmp`) over 124 files:
  **2469 passed, 2 xfailed**. The files:
  - every `tests/test_ad1_*.py`, and `test_adaptive_difficulty_ad1`;
  - `test_architecture`, `test_registry_audit`, `test_judge_routes`;
  - the request-gate and receipt files: `test_decider_landing`,
    `test_model_call_receipt_owners`, `test_glm_ocr`,
    `test_ux_phase1_review_fixes`;
  - every file that touches `question_events` or the tutor (`tutor_qa`,
    `insert_question_event`, `ask_question`);
  - `test_table_roles`, `test_coordinated_migrations`,
    `test_tracked_fixture_databases`;
  - the 30 files that pin `migration_head_213`;
  - `test_vault_watcher_refresh`, `test_daily_plan_rpc` (the sidecar hooks
    changed).
- `-m durability tests/test_ad1_migration.py`: 1 passed.
- `--durable-sqlite` on `tests/test_ad1_fix_round4.py` and
  `tests/test_ad1_send_guard.py`: 13 passed.
- Frontend:
  - `npm run typecheck`: clean;
  - vitest on the 14 practice files (`src/screens/practice/*`, every
    `PracticeScreen.*.test.tsx`, `src/app/practiceDraft.test.ts`): 128
    passed;
  - `npm run frontend:build`: built.
- `db_generate_reference.py`, then `db_validate_reference.py`: 0 errors.
  The references were regenerated in `d05aed3e5`
  (`question_events.answer_mode`, commit labels, line citations).
- Model calls: 0. Cargo was not run: nothing under `src-tauri` changed.

## Fix round 5 (orchestrator)

The round-4 verify (codex-job `20261018-174551-Zrw5DA`) confirmed three
things:

- V5 and migration 213: 534 rows kept, the FK and integrity checks clean;
- the head fixture;
- no other regression.

It reopened V1 to V4 on narrower cases. The orchestrator's binding rulings
are applied below, with the same methods as round 4: every test except the
V3 pins failed on `7efda77fb` (`git archive 7efda77fb`, with
`-o pythonpath=<tmp>/src`; the frontend tests ran against `7efda77fb`'s
`apps/learnloop-tauri`, extracted to the scratchpad).

| id | severity | title | verdict | commit | test |
|----|----------|-------|---------|--------|------|
| V1 | High | A reload can race the protection check | fixed | `be610ee66` | `test_a_reload_while_protection_is_built_is_never_judged_by_the_vault_it_replaced` (the verify's threaded reproduction), `test_an_admission_after_a_reload_since_its_check_is_refused` |
| V2 | Medium | Unsettled and unvisited revisions disappear from the queue | fixed | `be610ee66` | `test_a_refused_spend_revision_is_retried_on_the_next_reload`, `test_busy_unavailable_and_incomplete_revisions_stay_queued`, `test_an_exception_keeps_the_current_and_every_unvisited_revision`, `test_an_exception_before_the_first_revision_keeps_the_whole_batch` |
| V3 | Medium | Receipt recovery resurrects a fenced-out answer | **rejected as a defect** (orchestrator) | pinned in `be610ee66` | `test_a_recovered_answer_whose_content_is_protected_now_is_refused`, `test_a_recovered_answer_still_unprotected_is_recorded_without_a_second_request` |
| V4 | Medium (two cases) | First-hint timing invented after a restore | fixed | `be610ee66` | vitest `PracticeScreen.firstHintRestore.test.tsx` (case 4, case 5, the fresh draft, the marker off); `test_the_draft_keeps_hint_seen_under_its_retry_key[on, off]` |
| V4-residual | Low | A pre-AD1 draft whose only hint was delivered by the service cannot be detected | recorded | - | known residual: a one-time transition |

**V1.** `SidecarContext` now has `vault_generation`. Its `__setattr__` bumps
the generation every time the loaded vault object is replaced: a load, a
reload, or a re-read after recovery or adoption. The bump comes after the
new vault is in place. `loaded_vault` is now a provider object (it was a
method): calling it returns the vault, and `generation()` returns the
generation.

`SendGuard` reads the generation before it reads the vault and builds the
predicate, and again afterwards. If the generation moved, it rebuilds from
the new vault, up to `RELOAD_RETRIES` (3) times, then refuses as
`protected`.

The two admissions bind to the generation their check returned:

- **Each physical request.** The request gate and `PaidCalls`' per-attempt
  hook run `confirm(check())`.
- **Each record.** `SendGuard.confirm` runs inside the write transaction:
  the forecast's `_write`, every feature-audit `_append`, and the fallback's
  payload insert. A reload since the check refuses, the transaction rolls
  back, and every later request of the job is refused.

The CLI, which has no provider, keeps today's behaviour.

The test is the verify's threaded reproduction. While `protection()` builds
the predicate, another thread adds an exam scope and runs `ctx.reload`. On
`7efda77fb` the guard allowed the request; now it refuses.

**V2.** Only settled revisions leave the queue:

- prepared;
- already done (`current`);
- terminal: protected, the switch off, no longer active, or no longer in the
  vault.

Everything else is retried:

- **Unvisited revisions** go back to the front of the queue. That covers an
  exception, including the revision that raised, and a vault switch or close.
- **Visited but unsettled revisions** go to the back, so a revision that
  keeps failing never starves new ones. That covers `refused_spend`,
  `busy`, `unavailable`, `failed`, `stale` and an incomplete audit.

Retries happen only at the next trigger (a reload or a plan read), still at
most 20 a run. Runs never chain.

On `7efda77fb` each test's retry trigger found an empty queue:

- a `refused_spend` revision was not retried by the next reload;
- busy, unavailable and incomplete revisions were dropped;
- an exception mid-batch, or before the first revision, dropped the whole
  batch.

**V3: rejected as a defect, per the orchestrator's ruling.** Recovering an
answer that was already paid for, within the same vault, is the designed
pattern: H1 and H2b recover checkpointed or receipted answers so that
nothing is paid twice. The fence exists to stop writes into a vault that is
no longer the loaded one, not to throw away an answer that was legitimately
bought.

What must hold instead, and is now pinned: a recovered answer passes the
`SendGuard` record check again, against the vault loaded at recovery time.
The frozen inputs are also re-read and hash-checked by the job. In the test:

- the LLM's answer lands after a vault switch, so the job is `stale`, writes
  no checkpoint, and keeps its completed receipt;
- the vault is reopened after its lease lapses;
- the second run recovers the answer from the receipt, with no new request;
- if the history source was held out at recovery time, the answer is
  refused (`protected`) and nothing is recorded, and the Decider is refused
  too;
- without that, it is recorded `ok`.

Both pins pass on `7efda77fb` and on this round, which is expected: they pin
behaviour that already holds.

**V4.** The saved draft gains `hintSeen`, kept with the draft's retry key in
the practice envelope (`save_practice_draft`'s `hint_seen`;
`get_session`'s `checkpoint.hintSeen`, present only when true):

- The practice screen sets it at the first hint of any kind: an authored
  reveal, a hint the H2b panel delivered, hints carried back from steps, or a
  carried book.
- It is saved whatever the switches. This is persistence only:
  `hintsUsed`, the assistance count and grading are unchanged. As a
  consequence, with the switches off a draft that saw a hint also carries
  `hintSeen: true`. That is deliberate: a later switch-on then knows the
  first hint's timing is unknown.

On restore, the marker stays null (unknown) for the attempt in either case:

- `hintSeen` is true and no marker was saved;
- a legacy draft without the field has `restoredHints > 0`.

Carried hints arriving from a workbench without a marker call
`noteUntimedHint()` (the verify's case 4). On `7efda77fb` both cases sent
`draft_started`. A fresh draft still records `no_draft` and saves
`hintSeen: true` with `hintsUsed: 1`.

**Known residual (Low).** A legacy draft, saved before AD1 or before
`hintSeen` existed, whose only hint was a service delivery saved neither
`hintSeen` nor a counted hint. The client cannot detect it, so its next
hint can still supply the marker. This is a one-time transition for drafts
in progress when this lands.

### Gate (fix round 5, targeted)

- `uv run lint-imports --no-cache`: 27 kept, 0 broken.
- `uv run pytest -n auto` (`TMPDIR=fixtures-local/tmp`) over 208 files:
  **4369 passed, 2 xfailed**. The files:
  - round 4's 124 files;
  - `tests/test_ad1_fix_round5.py`;
  - `test_desktop_rpc_contract`, `test_sidecar_contract`,
    `test_sidecar_serializer_snapshot`;
  - every file that uses `SidecarContext`, `save_practice_draft`,
    `patch_checkpoint` or `get_session`. The context's `__setattr__` and the
    draft envelope changed.
- `-m durability tests/test_ad1_migration.py`: 1 passed.
- `--durable-sqlite tests/test_ad1_fix_round5.py`: 10 passed.
- Frontend:
  - `npm run typecheck`: clean;
  - vitest on the 26 practice and app files: 188 passed;
  - `npm run frontend:build`: built.
- `db_generate_reference.py`, then `db_validate_reference.py`: 0 errors.
  The commit labels and line citations were regenerated in `dcfbba20c`. No
  schema change this round.
- Model calls: 0.

## Fix round 6 (orchestrator)

The round-5 verify (codex-job `20261018-183139-KmfWBT`) confirmed V3's
recovery path, V4 and migration 213, and found four remaining items. The
orchestrator's binding rulings are applied below. Each new test failed on
`c6dd14a29` (`git archive c6dd14a29`, with `-o pythonpath=<tmp>/src`).

**The guarantee, stated precisely.** It is in `sending.py`'s why-comment
(the module docstring and `SendGuard.check`):

> Nothing is sent or recorded whose content was held out in the vault
> snapshot current at that request's or record's admission. Reading the
> snapshot and admitting are one atomic step relative to reload.

A reload that lands *after* admission cannot be told apart from an owner
edit made a moment after the send, so it is out of scope. No lock is held
across protection building, a model call, transport work or an SQLite
commit.

| id | severity | title | verdict | commit | test |
|----|----------|-------|---------|--------|------|
| V1-a | High | The vault and its generation are not published atomically | fixed | `87bb2df57` | `test_a_publication_paused_between_assignment_and_bump_is_never_admitted` |
| V1-b | High | A reload remains possible after the final confirmation | **rejected as out of scope** (orchestrator) | pinned in `87bb2df57` | `test_the_last_confirmation_runs_after_the_outer_gate_and_the_receipt` |
| V3 | Medium | A transient refusal is treated as settled | fixed | `87bb2df57` | `test_a_harmless_reload_between_the_audits_check_and_its_record_is_retried`, `test_four_interrupted_checks_are_stale_and_retried`, `test_a_stale_refusal_reports_stale_and_held_out_content_reports_protected` |
| V4 | Medium | A failing revision starves the rest | fixed | `87bb2df57` | `test_a_revision_that_keeps_raising_never_starves_the_rest`; round 5's `test_an_exception_keeps_the_revision_that_raised_queued` updated to this ruling |

**V1-a.** `SidecarContext._vault_lock` is a `threading.Lock`.
`__setattr__("vault")` assigns the vault and bumps `vault_generation`
together under it. Two methods on the `loaded_vault` provider use the same
lock:

- `snapshot()` reads `(vault, generation)` under it;
- `admit(generation)` compares the generation under it.

`SendGuard` reads the snapshot both before and after it builds protection,
and `confirm` admits through `admit()`. So a reader can never pair the new
vault with the old generation, and no reload is published between the
comparison and the admission. The lock is held only for those instructions.

The test reproduces the verify's interleaving. A worker is judging the old
vault while a reload, published as the context publishes it, assigns the
protected vault and pauses before the bump. On `c6dd14a29` the worker
passed both `check()` and `confirm()`. Now it waits for the whole
publication, sees the generation move, judges the new vault, and refuses
(`protected`).

**V1-b: rejected as out of scope, per the orchestrator's ruling.** A reload
after the final confirmation is the case the guarantee excludes: it cannot
be told apart from an owner edit made right after the send, and closing it
would mean holding a lock across transport work or a commit. What changed
instead is that the confirmation now sits as close to dispatch as the code
allows:

- The guard's request gate admits *after* the outer gate. A refusal settles
  the outer admission, so nothing it reserved is kept.
- The last confirmation runs once the request's start receipt is written
  (`claims.FencedRepository.record_model_event` calls
  `sending.before_dispatch`). That is the last work before the transport
  sends. A refusal there closes the receipt as `interrupted`: never sent,
  no usage.
- For a record, the confirmation stays the last check before the insert,
  inside its write transaction (`_write`, `_append`).

The pin installs an outer gate. It checks that each request (the LLM's and
the Decider's) is sent straight after `receipt` and then `confirm`, and that
after the Decider's outer admission the order is `confirm`, `receipt`,
`confirm`, then the send. On `c6dd14a29` the guard confirmed before the
outer gate, and nothing confirmed after the receipt.

**V3.** The refusal statuses are now split:

- `ProtectedContent` / `protected` means the content is held out in the
  snapshot that was judged. It is terminal.
- `StaleSnapshot` (a subclass) / `stale` is retryable. It covers a reload
  under the check, a confirmation whose generation moved, another vault or
  none loaded, an unreadable provider, and retries exhausted.

`refusal_status` maps an exception to its status. The forecasts and the
audit report `stale`, and `decider_status` / `llm_status` are labelled the
same way. `stale` is not in `_SETTLED`: the revision stays queued at the
back, is never cached in `_PREPARED`, and an audit left with unanswered
dimensions because of it is not settled.

On `c6dd14a29`:

- a harmless reload between the audit's record check and its record
  admission refused the record as `protected`; with the forecast off, the
  revision was cached as settled and never retried;
- four interrupted checks did the same.

Now both are `stale`, and the next trigger audits the revision.

**V4.** `_prepare` catches each revision's exception. That revision is
recorded as visited and unsettled (`failed`), goes to the back of the queue
as retryable, and the run continues with the next revision, still at most
20 per run. Revisions the run never reached (an exception outside any one
revision, or a vault switch) keep their place at the front.

With A raising every time, the visits are A, B, C, then A on each later
trigger. On `c6dd14a29` they were A on every trigger.

### Gate (fix round 6, targeted)

- `uv run lint-imports --no-cache`: 27 kept, 0 broken.
- `uv run pytest -n auto` over 116 files: **2289 passed**. The files:
  - every `tests/test_ad1_*.py`, and `test_adaptive_difficulty_ad1`;
  - `test_architecture`, `test_registry_audit`, `test_judge_routes`;
  - the request-gate and receipt files;
  - `test_desktop_rpc_contract`, `test_sidecar_contract`,
    `test_sidecar_serializer_snapshot`;
  - every file that uses `SidecarContext`. This is the trimmed list the
    ruling allows.
- `--durable-sqlite tests/test_ad1_fix_round6.py`: 6 passed.
- The round-5 and round-6 files run serially three times, 16 passed each
  time. This checks the threaded tests.
- `db_generate_reference.py`, then `db_validate_reference.py`: 0 errors.
  The commit labels and line citations were regenerated in `73e82119e`.
- Nothing under `apps/` changed this round, so the frontend was not rerun.
  Model calls: 0.

## Fix round 7

The round-6 verify (codex-job `20261018-185215-YLlz6Q`) confirmed atomic
publication, the queue, migration 213 and no other regression. It left two
items. Both tests failed on `0977c3fb5`.

| id | severity | title | verdict | commit | test |
|----|----------|-------|---------|--------|------|
| R7-1 | Medium | A dispatch refusal at the Decider's start receipt is swallowed | fixed | `a806508a8` | `test_a_refusal_at_the_deciders_start_receipt_stops_the_request` |
| R7-2 | Low | A refused Decider record leaves `decider_status` at `ok` | fixed | `a806508a8` | `test_a_refused_decider_record_labels_the_decider_status` |

**R7-1.** The Decider's receipts go through `review_spend.UsageCollector`,
which treats its sink as telemetry and swallows the sink's exceptions. So
when `before_dispatch()` refused at the start receipt, the request was sent
anyway. Its receipt stayed `interrupted` with null cost, and the outer gate
settled real usage.

This was the smallest change to the shared class: `UsageCollector` now
re-raises only an exception that declares `admission_refused`. Only
`ProtectedContent` and its subclasses do (the same pattern as
`SpendBudget`'s `spend_refused`), so every other sink failure is still
swallowed for other callers.

The test runs a harmless reload after the Decider's gate check and before
its start receipt. The result:

- no transport call;
- the receipt is `interrupted` / `StaleSnapshot`, with no cost;
- the outer gate's admission for the Decider is settled with no usage;
- the Decider's outcome is `stale`.

**R7-2.** `admit_decider()` now catches `ProtectedContent`, sets
`decider_status = refusal_status(exc)` and re-raises, as the LLM's handler
does. A reload after the Decider's record check now gives `stale` for both
the audit and its `decider_status`.

### Gate (fix round 7, targeted)

- `lint-imports --no-cache`: 27 kept, 0 broken.
- `pytest -n auto`: **381 passed**. The files:
  - the AD files: every `tests/test_ad1_*.py`, and
    `test_adaptive_difficulty_ad1`;
  - every test that touches `review_spend` or `UsageCollector`:
    `test_decider_landing`, `test_output_budget`, `test_tier1_decider`,
    `test_t6_followup_review`;
  - the receipt and gate files: `test_model_call_receipt_owners`,
    `test_glm_ocr`, `test_ux_phase1_review_fixes`;
  - `test_architecture`.
- `--durable-sqlite tests/test_ad1_fix_round7.py`: 2 passed.
- References: regenerated in `2a978bb4c`, 0 errors. Model calls: 0.

## Fix round 8

The round-7 verify (codex-job `20261018-190233-RjEeLO`) confirmed round 7's
normal path and its Low fix. It found two older holes at the same place,
AD's start receipt:

- **A cleanup error masked the refusal.** If closing the receipt after a
  `StaleSnapshot` failed, the storage error replaced the refusal. The
  Decider's `UsageCollector` then swallowed it, and the request was sent.
- **A lost lease did not stop the request.** A `_LeaseLost` at the start
  receipt carried no admission marker, so the collector swallowed it and the
  old worker sent the request even though another worker now held the claim.

**Binding ruling: AD's start receipt fails closed.** It is applied in
`claims.FencedRepository._start` (commit `8120221bb`). Every exception
stops the dispatch:

- **Lease lost.** `_LeaseLost` from `_fenced_txn` becomes
  `ReceiptLeaseLost`. It is both a `DispatchStopped` and a `LeaseLost`, so
  every AD handler that stops a job on a lost lease reports it as `stale`
  (retryable: the claim's new owner does the work).
- **Storage error.** Any other error writing the receipt becomes
  `ReceiptWriteFailed`. The forecasts and the audit report it as `failed`,
  send nothing, write nothing more, and the preparation queue retries it at
  the back.
- **Refusal.** A refusal by `before_dispatch()` closes the receipt as
  `interrupted` and is raised as itself, so it keeps its own status.
- **Cleanup error.** If closing the receipt fails, that failure is logged
  and the *original* refusal is raised. The cleanup error never replaces it.
- **An error in the check itself** is a `ReceiptWriteFailed` too.

Both new exceptions are AD-marked interruptions: subclasses of
`DispatchStopped` (an `AIInterrupted`) that carry `admission_refused`, with
the original error as `__cause__`. `UsageCollector` is unchanged from round
7, and ordinary telemetry errors elsewhere are still swallowed.

**Tests** (`tests/test_ad1_fix_round8.py`, 10). Each injection (a finish
failure after `StaleSnapshot`, `_LeaseLost` at the start receipt, a storage
error at the start receipt) is run on three paths: the presentation's
Decider, the presentation's LLM, and the `llm_v1:item` path. Each gives zero
transport calls and the right status (`stale`, `stale`, `failed`). One more
test pins that the cleanup failure is logged and the refusal stands.

6 of the 10 failed on `7ee922e29`:

- the Decider path for all three injections: the request was sent;
- the cleanup test;
- the item path's finish-failure and storage cases: the storage error
  escaped `forecast_item`.

The other 4 pass on both trees and pin behaviour that already held: the
presentation LLM path for all three injections, and the item path's lease
case.

### Gate (fix round 8, targeted: the round-7 set)

- `lint-imports --no-cache`: 27 kept, 0 broken.
- `pytest -n auto`: **391 passed**. The files: every `tests/test_ad1_*.py`,
  `test_adaptive_difficulty_ad1`, `test_decider_landing`,
  `test_output_budget`, `test_tier1_decider`, `test_t6_followup_review`,
  `test_model_call_receipt_owners`, `test_glm_ocr`,
  `test_ux_phase1_review_fixes`, `test_architecture`.
- `--durable-sqlite tests/test_ad1_fix_round8.py`: 10 passed.
- References: regenerated in `51396816a`, 0 errors. Model calls: 0.

## Fix round 9

The round-8 verify (codex-job `20261018-191723-N7zC1m`) found no High and
one Medium, at `feature_audit.py:370`. A `ReceiptWriteFailed` at the
Decider's start receipt only set a local status. The audit then:

- wrote five `failed` judgments;
- ran the LLM fallback;
- could return `audited`, which the queue then settled.

**Ruling, under round 8's contract.** A `ReceiptWriteFailed` or a
`ReceiptLeaseLost` (any `DispatchStopped` other than a protection refusal)
at any audit request now returns from the audit at once (commit
`9dbe585eb`):

- no further judgment write and no fallback;
- `decider_status` (or the fallback's `llm_status`) and the audit's status
  are `failed`, or `stale` for a lost lease;
- the remaining dimensions are left unanswered;
- the queue keeps the revision and retries it at the back.

A protection refusal keeps its existing handling.

**Tests** (`tests/test_ad1_fix_round9.py`, 4, all failing on `2ad80dff7`):

- the verify's case, through `audit_revision`, for a storage error and for
  a lost lease;
- the backfill path;
- the queue's settle decision: the next trigger audits the revision.

Each shows no fallback call, no judgment written after the failure, and the
status `failed` or `stale`. On `2ad80dff7`:

- the storage case sent the fallback and returned `audited`;
- the lease case left `decider_status` unset;
- the backfill reported `audited`;
- the queue settled the revision.

### Gate (fix round 9: the round-8 set)

- `lint-imports --no-cache`: 27 kept, 0 broken.
- `pytest -n auto`: **395 passed**. The files: every `tests/test_ad1_*.py`,
  `test_adaptive_difficulty_ad1`, `test_decider_landing`,
  `test_output_budget`, `test_tier1_decider`, `test_t6_followup_review`,
  `test_model_call_receipt_owners`, `test_glm_ocr`,
  `test_ux_phase1_review_fixes`, `test_architecture`.
- `--durable-sqlite tests/test_ad1_fix_round9.py`: 4 passed.
- References: regenerated in `116f7ebfa`, 0 errors. Model calls: 0.

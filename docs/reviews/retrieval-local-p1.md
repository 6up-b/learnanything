# Local contextual retrieval P0 + P1a + P1b (stage `retrieval-local-p1`)

**Branch** `retrieval/local-p1` (worktree `learnanything-lr1`), base `5cefbd3c1` (main `bd0bb7267` with T1 and RW5b, plus the E0/E1 harness). **Spec** [spec_local_contextual_retrieval_v1](../specs/spec_local_contextual_retrieval_v1.md) (owner D6 amendment 2026-10-24). **Migration** 219 (AD2+AD3 holds 214 on its own branch; check `ls migrations/` at the merge). No GPU run, no download and no paid or model call was made in this stage: every model, provider and process is a fake in the tests.

## What landed

| Phase | What | Where |
|---|---|---|
| P0 | A **true 8,192-token profile path**: a profile entry `{"pool": [...], "target": N}` is fitted by the model's OWN token count (binary search over the pool's prefix, the last chunk trimmed by words), so the 8,192 window measures 8,192 tokens up to one word (E1's estimate-built window reached 5,603). Pools are teaching text only. The command is left for the owner (below); it was not run | `local_embeddings/worker.py` (`fit_window`, `profile`), `source_retrieval/local_index.py` (`profile_pools`, `run_profile`), `learnloop embeddings local profile` |
| P1a | The production package `learnloop.local_embeddings`: pins and identity (moved from E1, pinned equal by test), the worker (moved: same probes, start refusals, sampler, aborts, smoke, unload; plus the fixed public canary set), the GPU meter (moved; uncapped for production indexing, capped for phase budgets), the launcher (its own `systemd-run --user --scope -p MemoryMax=12G -p MemorySwapMax=0`, the GPU lock and the full-suite lock taken non-blocking), the owner-run setup (separate env, pinned download, every file checked by size and SHA-256, the software epoch recorded; `--adopt-*` records E1's artefacts without moving them), the vector cache `<vault>/.learnloop/vector-cache/<space_id>.sqlite` keyed by the whole window, and the fusion core | `src/learnloop/local_embeddings/` |
| P1a | The index job: every owed window of both variants (grouped and singleton) in ONE worker batch; identical window texts encoded once; canaries checked against the space's stored ones (cos ≥ 0.999) before anything is stored, else `epoch_drift` and nothing stored; `waiting_for_gpu` / `waiting_for_batch` instead of failing; queued on extraction (`local_source_index`) only while `embedding.local.enabled` | `source_retrieval/local_index.py`, `content/pipeline/jobs.py` |
| P1a/P1b | The shared window rule `w4096-section-policy-v1` over production blocks: ≤ 4,096 estimated tokens, never across a section or a policy class (`teaching`, `solution`, `exam`, `assessment_lane`), every block once, split-by-offsets with a token-weighted mean; keys change with any member text, offset or class, so stale vectors are never found | `source_retrieval/windows.py` |
| P1b | The Voyage fallback: `voyage_contextual_embedding` profile type (refused by EVERY AI task, the Qwen `embedding` route included, and never a generation profile, so no route or `LEARNLOOP_AI_PROVIDER` reaches it); the client moved from E0's adapter (nested inputs, `input_type` document/query, L2-normalized, redirects refused, errors carry status or class only, never the key or a body); the backfill (window-keyed rows in `embedding_vectors` with `model_id` = the space id; admitted at the full $0.12/M; `max_cost_usd_per_run` = $1 keep cap; receipts `embedding_backfill`); queries cached and receipted (`source_query_embedding`); queued on extraction (`source_fallback_backfill`) only while on | `ai/providers/voyage_contextual.py`, `source_retrieval/fallback_space.py` |
| Seam | **The one new seam**: `search_spans` asks `resolve_source_spaces` only while `embedding.local.enabled` or `embedding.fallback.enabled` is on. Each available space ranks its own covered extractions by its own cosine; rankings fuse by rank with the served weights; an extraction no positively weighted space covers is served by the cheapest covering stand-in (local, then Qwen, then Voyage, by price) with the weight of the space it stands in for, so a hosted space is queried only for what it alone covers. Every result records `space_selection`: per space its status and reason (`ok`, `incomplete`, `encoder_unavailable`, `encoder_late`, `disabled`, `epoch_drift`, `retired`), assigned sources and query status (paid or not), the served, seed and learned weights, `rrf_k`, the exploration draw and the receipt id | `source_retrieval/spaces.py`, `source_retrieval/search.py` |
| Logging | `retrieval_feedback` (RECEIPT): one `query` row and one `delivered` row per span (its rank in every contributing space's list, position, propensity); `cited` rows from the tutor's validated citations (joined to the delivery by the question's retrieval owner id); `opened` rows by `record_open(receipt_id, span)`; consumers named (`tutor`, `find_sources:<intent>`, `library`, `compare`) | `source_retrieval/feedback.py`, `db/stores/retrieval_spaces.py`, `tutor/tutor_qa.py` |
| Learned rule (logged) | `retrieval_fusion_posteriors` (DERIVED, one replayer): an IPS-weighted logistic examination-and-relevance model per context, partially pooled under the global fit; refitted from the receipts in order, deterministic (byte-identical replay, tested). With `learned_fusion` off (default) the seed serves and the learned weights are only logged; `exploration` (off by default) reorders only spans whose posterior score gap is smaller than its own posterior standard deviation, with logged propensities and a receipt-keyed seed | `local_embeddings/fusion.py`, `substrate/rebuild_orchestrator.py` |
| Migration | 219: `embedding_spaces` (WORKFLOW), `retrieval_feedback` (RECEIPT, append-only by trigger), `retrieval_fusion_posteriors` (DERIVED); head fixture `migration_head_219` (renamed from 218, only 219 applied, rollback mode); references regenerated (342 table notes, 1,025 config leaves, 0 validation errors) | `migrations/219_retrieval_spaces.sql` |

**Config** (all off or at the seed): `[embedding.local]` `enabled = false`, `index_on_extract = true`, `index_batch_minutes = 15` (keep); `[embedding.fallback]` `enabled = false`, `provider = "voyage_context"`, `maintain_index = true`, `max_cost_usd_per_run = 1.0` (keep), `price_per_million = 0.12`; `[embedding.source_space]` `default = "qwen"`, `learned_fusion = false`, `exploration = false`, `log_feedback = true`. Every defaults snapshot moved (the effective config gained the sections; no serving change).

## Byte-identity with the switches at their defaults

* With both new switches off, `search_spans` never consults the resolver, never reads a new table and never writes: the result is today's (`space_selection` is empty and absent from `describe()`; no feedback row), tested.
* With the Voyage fallback ON and indexed but the default left at Qwen and Qwen covering the scope, the hits (keys, ranks, pool roles), the fused order, the lists, list ends and `dense` equal the defaults', and `find_sources` hits are byte-identical as JSON; Voyage is never queried (tested).

## No made-up constants (owner, 2026-10-24)

Every new weight is learned with a labelled prior (`fusion.PRIOR_BASIS`): `beta` mean at the current default (legacy) scaled by the default-only MLE (empirical), unit-information covariance (published: Kass and Wasserman 1995), `gamma` at the logit of the pooled rate (empirical), the examination curve seeded at `1/pos` (published: Joachims et al. 2017) and learned only from randomized deliveries, `rrf_k` seeded at the config (legacy) and chosen by Laplace marginal likelihood over an octave grid. The exploration band is structural (a gap below its own posterior spread). Everything fixed is labelled `keep` and classified in `params/parameter_registry.py` (20 pins, the window rule, the Voyage limits, the fusion core's numerical budgets, the three new config keys): memory floors and scopes, canary and smoke identity checks, money caps, the batch wait, provider limits.

## Commands left for the owner (none run here)

```bash
# 1. Setup (owner): plan first; adopt E1's verified artefacts without moving them, or download.
uv run learnloop embeddings local setup --dry-run
uv run learnloop embeddings local setup --adopt-model-dir <learnanything-e1/fixtures-local/...model dir> \
    --adopt-env-python <learnanything-e1/fixtures-local/...env>/bin/python
#    (or: uv run learnloop embeddings local setup --i-understand-this-downloads-33-gb)
# 2. P0: the true 8,192-token profile on a backup-API copy (metered; nothing indexed).
uv run learnloop embeddings local profile --vault fixtures-local/<copy> --extraction-id <id> --json
# 3. P1a: set embedding.local.enabled = true in the vault, then index (dry run first).
uv run learnloop embeddings local index --vault <vault> --dry-run
uv run learnloop embeddings local index --vault <vault> --now
uv run learnloop embeddings local status --vault <vault>
# 4. P1b (after the Voyage training opt-out, Q7; vaults outside the checkout, Q6): add the profile
#    [ai.providers.voyage_context] type = "voyage_contextual_embedding" and [embedding.fallback] enabled = true.
uv run learnloop embeddings fallback backfill --vault <vault> --dry-run
# 5. The posterior (no model call): refit from the receipts.
uv run learnloop embeddings fusion refit --vault <vault>
```

## Deviations from the spec, and why

*Codex review (see [retrieval-local-p1-codex-review](retrieval-local-p1-codex-review.md)):* 4 (opens) and 5 (no timer) are fixed: the Reader's search-result click sends the open, and the ingest host's sweep wakes a deferred index batch. Exploration now runs at each consumer's delivery boundary, learned fusion serves Thompson draws at the posterior's `rrf_k`, and lists are bound to space identities. 7's P0 bank posterior and pooling simulation remain owed (owner question).

1. **The local space has no query encoder in P1.** The student is P2 and the teacher session P1c; until one exists the local space indexes, reports coverage and `encoder_unavailable`, and never contributes. `spaces.LOCAL_QUERY_ENCODER` is the hook they plug into (tested with a fake encoder). With `default = "local:grouped"` and no encoder, Qwen stands in.
2. **Module placement.** The index job lives in `source_retrieval/local_index.py` and the fusion core in `local_embeddings/fusion.py`, so the import graph stays acyclic (`frozen-cross-package-cycles`): `source_retrieval` drives `local_embeddings`, never the reverse; the tutor records citations through the store, not through `source_retrieval`.
3. **E1's worker stays E1's record.** The production worker is a moved copy (E1's plan id pins E1's file); `test_the_moved_pins_equal_e1s` pins every shared value equal.
4. **Opens: the recorder, not the desktop wiring.** `record_open(receipt_id, span)` and its tests land; the result's receipt id is in `space_selection`; sending it from the Reader / library result click (TS client, Tauri, RPC) is a follow-up.
5. **Batching is per vault**, and a `waiting_for_batch` job completes with its reason: the next extraction's job or `embeddings local index` drains it (no timer was added).
6. **The policy check runs per query while a new space is on** (the window keys are recomputed from the current exam, held-out and role predicates); off by default, so today's cost is unchanged.
7. **Not in this stage:** P0's bank posterior and pooling simulation (§10's P0 row beyond the profile path), P1c, P2, P3, the MCP cost admission of the fallback's query bound, teacher anchors.

## Open questions for the owner

1. **The orchestrator's P1 scoping** (built this way, pending your confirmation): log citations and opens and the learned rule's would-be weights, but serve the seed weights (`learned_fusion = false`) until enough feedback exists; exploration behind its own switch (`exploration = false`), reordering only posterior near-ties.
2. **P0 beyond the profile path**: the bank posterior of §9.1 (with its label-noise model) and the pooling-hyperprior simulation are not built here; a separate P0 stage, or fold them into P2?
3. **Opens from the desktop**: `record_open` lands, but the Reader / library result click does not send the receipt id yet (TS client, Tauri, RPC). A follow-up stage?
4. **The local space serves no queries until P1c or P2**: it indexes and reports coverage, and Qwen stands in, so setting `default = "local:grouped"` alone changes nothing yet.

## Gate (this step; the full suite runs once in the landing gate)

Run at `489ef94c7` (the fixes) on top of `2437d50fa`; every pytest inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, one run at a time, `-n 6` at most.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **32 kept, 0 broken** (before and after the fixes) |
| Targeted pytest, 325 files (below), `-n 6` | **6,711 passed, 4 failed, 2 skipped, 2 xfailed** (28 min) |
| The 4 failures | 3 audit lists that did not know new code: `test_every_process_launch_site_is_approved` (the three local-package launch sites, each reviewed: argv lists, no shell, nothing that can start Codex; plus E1's three, inherited from the E0/E1 base merge), `test_http_clients_are_imported_only_by_audited_modules` (the Voyage client, inside `model_call` with redirects refused; plus E0's adapter, inherited), `test_golden_projection_survives_one_umbrella_rebuild_exactly_and_stale_rows_clear` (it plants one stale row per DERIVED table; now one in `retrieval_fusion_posteriors`). 1 load flake: `test_reading_hardening_2_fixes.py::test_f1_a_build_whose_worker_failed_to_start_is_run_by_the_sweep` (a thread-start race under load; passes alone **3/3**; this stage's pipeline hook returns before any work with the switches off) |
| Rerun after the fixes: `test_codex_lockdown_round3`, `test_plan_first_transport`, `test_rebuild_orchestrator`, `test_reading_hardening_2_fixes`, `test_source_space_resolver`, `test_tutor_qa`, `test_tutor_citations`, `test_reader_tutor_retrieval`, `test_source_retrieval_tutor` | **146 passed** |
| `-m durability`: `test_retrieval_spaces_migration`, `test_coordinated_migrations`, `test_sqlite_wal_lifecycle`, `test_reader_rw7a_migration`, `test_t1_batch_origin_migration`, `test_migrations`, `test_tracked_fixture_databases` | **9 passed** |
| `--durable-sqlite`: `test_retrieval_spaces_migration`, `test_source_space_resolver`, `test_rebuild_orchestrator` | **21 passed** (all 21 collected) |
| `db_generate_reference.py` / `db_validate_reference.py` (under `env -i`, empty HOME / CODEX_HOME / LEARNLOOP_CONFIG_DIR) | 342 table notes; **0 validation errors** (4,646 wikilinks checked) |
| Frontend / Tauri | unchanged (no file under `apps/`): no npm, vitest or cargo step |

Fix in this step besides the lists: the tutor's citation hook (`tutor_qa._record_retrieval_citations`) now returns before opening a connection while neither new space is on (or `log_feedback` is off), so the default path does no new reads either; tested (`test_the_tutor_citation_hook_does_nothing_with_the_switches_off_and_joins_its_delivery_when_on`).

Targeted files (325): `test_ad1_codex_rereview_fixes.py`, `test_ad1_codex_review_fixes.py`, `test_ad1_fix_round4.py`, `test_ad1_migration.py`, `test_adaptive_difficulty_ad1.py`, `test_ai_compare.py`, `test_ai_config.py`, `test_ai_runtime.py`, `test_approach_map_replay.py`, `test_approach_maps.py`, `test_approach_maps_schema.py`, `test_architecture.py`, `test_assumed_known.py`, `test_capture_desktop.py`, `test_capture_route_recovery.py`, `test_chatgpt_plan_cli.py`, `test_chatgpt_plan_landing.py`, `test_chatgpt_plan_provider.py`, `test_chatgpt_plan_sidecar.py`, `test_chatgpt_plan_workspace.py`, `test_cli_help_snapshot.py`, `test_codex_lockdown_round2.py`, `test_codex_lockdown_round3.py`, `test_codex_output_schema.py`, `test_codex_tool_lockdown.py`, `test_compare_sources_keep.py`, `test_compare_sources.py`, `test_concept_animation_service.py`, `test_config_refactor.py`, `test_constraint_engine.py`, `test_coordinated_migrations.py`, `test_daily_loop_reader_authored_practice.py`, `test_daily_loop_reader_retire.py`, `test_daily_loop_reference_adoption.py`, `test_daily_plan_composition.py`, `test_daily_plan_replay.py`, `test_decider_client.py`, `test_decider_landing.py`, `test_desktop_rpc_contract.py`, `test_diagnosis_embeddings.py`, `test_diagnosis_input_provenance_landing.py`, `test_diagnosis_input_provenance.py`, `test_diagnosis_replay.py`, `test_dialogue_causal_join.py`, `test_difficulty_band_guards.py`, `test_doctor.py`, `test_e0_adapters.py`, `test_e0_bank.py`, `test_e0_budget.py`, `test_e0_corpus.py`, `test_e0_credentials.py`, `test_e0_delivery.py`, `test_e0_dry_run.py`, `test_e0_isolation.py`, `test_e0_metrics_stop_rules.py`, `test_e0_paid_fakes.py`, `test_e0_relabel_round.py`, `test_e0_review_round1.py`, `test_e0_review_round2.py`, `test_e0_review_round3.py`, `test_e0_review_round4_followup.py`, `test_e0_review_round4.py`, `test_e0_review_round5.py`, `test_e0_review_round6.py`, `test_e0_review_round7.py`, `test_e0_review_round8.py`, `test_e1_gpu_meter.py`, `test_e1_harness.py`, `test_e1_supplement.py`, `test_e1_worker.py`, `test_embedding_backfill.py`, `test_embedding_compare.py`, `test_embedding_recipe_hash_pins.py`, `test_embedding_route_isolation.py`, `test_embedding_store.py`, `test_evsi_calibration_sim.py`, `test_evsi_multisim.py`, `test_evsi_router_composition.py`, `test_exam_protection_identity.py`, `test_exam_protection.py`, `test_exam_protection_review.py`, `test_exercise_arm.py`, `test_facet_identity_actions.py`, `test_facet_identity_composition.py`, `test_facet_identity_ingest.py`, `test_facet_locks_landing.py`, `test_facet_reword_confirm_review.py`, `test_family_memory_projection.py`, `test_family_proposals.py`, `test_field_cli.py`, `test_field_config.py`, `test_field_signal_production_paths.py`, `test_figure_offers.py`, `test_figures_migration.py`, `test_figures_rw5b_fix_round2.py`, `test_figures_rw5b_review.py`, `test_figures_scope_redesign.py`, `test_find_sources_intents.py`, `test_forecast_receipts_landing.py`, `test_forecast_receipts.py`, `test_glm_ocr.py`, `test_grading_cli.py`, `test_grading_hardcases.py`, `test_graph_nomination_ingest.py`, `test_held_grade_composition.py`, `test_held_grade_evidence.py`, `test_help_assists_schema.py`, `test_hint_feedback_widening.py`, `test_hint_telemetry.py`, `test_import_split_parity.py`, `test_ingestion_checkpoints.py`, `test_ingest_jobs.py`, `test_ingest_latency_journey.py`, `test_ingest_m3.py`, `test_ingest_ownership.py`, `test_ingest_runner.py`, `test_ingest_transcripts.py`, `test_integration_daily_loop_field.py`, `test_intent_codex_rereview.py`, `test_intervention_outcomes_replayer.py`, `test_inventory_merge_parallel.py`, `test_inventory_runner_mailbox.py`, `test_item_fingerprints.py`, `test_judge_routes.py`, `test_keep_local_retired.py`, `test_kinship_feature.py`, `test_knowledge_map_text_neighbors.py`, `test_learner_text_gaps_composition.py`, `test_learner_text_gaps_flow.py`, `test_learner_text_gaps.py`, `test_learner_text_gaps_review.py`, `test_learner_text_source_widening.py`, `test_library_ask_expand.py`, `test_library_ask.py`, `test_library_ask_review.py`, `test_library_asks_migration.py`, `test_library_exercises.py`, `test_local_fusion_core.py`, `test_local_index.py`, `test_mcp_c1a_review.py`, `test_mcp_tools.py`, `test_method_explicit_landing.py`, `test_method_explicit_upgrade.py`, `test_method_phrasing_report.py`, `test_migrations.py`, `test_mobile_allowlist.py`, `test_mobile_host_coexistence.py`, `test_model_usage_report.py`, `test_model_work_checkpoints.py`, `test_mvp010_upgrade.py`, `test_mvp011_upgrade.py`, `test_mvp013_upgrade.py`, `test_mvp014_upgrade.py`, `test_mvp015_upgrade.py`, `test_mvp016_upgrade.py`, `test_mvp017_route_check_replay.py`, `test_mvp017_upgrade.py`, `test_mvp018_upgrade.py`, `test_mvp020_upgrade.py`, `test_mvp021_upgrade.py`, `test_mvp022_upgrade.py`, `test_mvp023_upgrade.py`, `test_mvp024_upgrade.py`, `test_native_media_readiness.py`, `test_openai_embedding_client.py`, `test_openrouter_client.py`, `test_openrouter_video_client.py`, `test_open_world_gate.py`, `test_output_budget.py`, `test_p0_cutover_mvp08.py`, `test_p2_acceptance.py`, `test_passage_links.py`, `test_pf_cli.py`, `test_pfc_unassessed_readers.py`, `test_pfc_unverified_unassessed.py`, `test_pinned_span_bridge.py`, `test_placement_opening_probes.py`, `test_placement_signals.py`, `test_plan_determinism.py`, `test_plan_first_transport_grant_scope.py`, `test_plan_first_transport_offer_grants.py`, `test_plan_first_transport_offer_grants_r5.py`, `test_plan_first_transport_paid_roles.py`, `test_plan_first_transport.py`, `test_practice_index_dossiers.py`, `test_practice_index_find.py`, `test_prescription_passages.py`, `test_probability_prep.py`, `test_project_cli.py`, `test_provider_resolution_parity.py`, `test_question_context.py`, `test_question_promotion_jobs.py`, `test_question_promotions.py`, `test_question_signal.py`, `test_quick_add.py`, `test_quick_check.py`, `test_reader_active_reading.py`, `test_reader_branches.py`, `test_reader_compare_table.py`, `test_reader_dialogue.py`, `test_reader_find_sources_callers.py`, `test_reader_inquiry_kill_switch.py`, `test_reader_inquiry_status.py`, `test_reader_intentions.py`, `test_reader_intent.py`, `test_reader_passage_check.py`, `test_reader_progression.py`, `test_reader_reconnect.py`, `test_reader_report.py`, `test_reader_rw1b_review.py`, `test_reader_rw1c_review.py`, `test_reader_rw2b_fix9.py`, `test_reader_rw2b_review.py`, `test_reader_rw3b_migration.py`, `test_reader_rw3b_review_fixes.py`, `test_reader_rw7a_migration.py`, `test_reader_tutor_retrieval.py`, `test_reader_tutor_switch_off.py`, `test_reader_workbench_rw2a.py`, `test_reading_hardening_2_fixes.py`, `test_reading_hardening_landing.py`, `test_reading_hardening_review_fixes.py`, `test_reading_hardening_verify_fixes.py`, `test_reading_paths.py`, `test_reading_request_sweep.py`, `test_reading_step_switch.py`, `test_rebuild_orchestrator.py`, `test_recurrence_benchmarks.py`, `test_recurrence_commands.py`, `test_recurrence_live.py`, `test_registry_audit.py`, `test_regrade_contract_replay.py`, `test_regrade_contract_successor.py`, `test_regrade_contract_upgrade.py`, `test_required_method_authority.py`, `test_required_method_grading.py`, `test_required_method_round3_review.py`, `test_reread_safety.py`, `test_retrieval_spaces_migration.py`, `test_reveal_ledger.py`, `test_roles_switch_off_legacy_parity.py`, `test_roles_switch_off.py`, `test_router_coldness_covariates.py`, `test_router_offer_log.py`, `test_router_outcomes.py`, `test_router_probe_ties.py`, `test_router_r1_composition.py`, `test_router_r2a_serving.py`, `test_router_r2b_agreement.py`, `test_router_r2b_serving.py`, `test_route_rules_in_grader.py`, `test_rw2c_switch_off.py`, `test_rw4_kill_switches.py`, `test_sensitivity_certificates.py`, `test_serve_eligibility_review.py`, `test_settings_sidecar.py`, `test_settings_store.py`, `test_shadow_rebuild.py`, `test_sidecar_animation.py`, `test_sidecar_contract.py`, `test_sidecar_goals.py`, `test_sidecar_ingest_m3.py`, `test_sidecar_reader_p3.py`, `test_sidecar_reader.py`, `test_sidecar_serializer_snapshot.py`, `test_sidecar_source_retrieval.py`, `test_sidecar_teach_back.py`, `test_source_block_fts.py`, `test_source_exercise_rpcs.py`, `test_source_ingestion_v2lite.py`, `test_source_inventory.py`, `test_source_retrieval_cli.py`, `test_source_retrieval_codex_unavailable.py`, `test_source_retrieval_followup.py`, `test_source_retrieval_guards.py`, `test_source_retrieval_rereview_cost.py`, `test_source_retrieval_rereview.py`, `test_source_retrieval_search.py`, `test_source_retrieval_suites.py`, `test_source_retrieval_tutor.py`, `test_source_roles.py`, `test_source_service_spend_envelopes.py`, `test_source_sets.py`, `test_sources_merge_composition.py`, `test_source_space_resolver.py`, `test_source_vector_backfill.py`, `test_source_windows.py`, `test_sqlite_file_copies.py`, `test_sqlite_wal_lifecycle.py`, `test_structured_transport_parity.py`, `test_stuck_prompt.py`, `test_stuck_prompt_replay.py`, `test_success_head_cli.py`, `test_t1_batch_origin_migration.py`, `test_t6_followup_rereview.py`, `test_t6_followup_review.py`, `test_table_roles.py`, `test_tier1_decider.py`, `test_tool_results_withhold_answers.py`, `test_tracked_fixture_databases.py`, `test_tutor_citations.py`, `test_tutor_delivery_fixes.py`, `test_tutor_practice_request.py`, `test_tutor_promotion_w2.py`, `test_tutor_qa.py`, `test_tutor_tool_requests.py`, `test_ux_phase1_add_source.py`, `test_ux_phase1_auto_build.py`, `test_ux_phase1_connect_ai.py`, `test_ux_phase1_finish.py`, `test_ux_phase1_first_run.py`, `test_ux_phase1_landing.py`, `test_ux_phase1_review_fixes.py`, `test_ux_phase1_round2_rereview.py`, `test_ux_phase1_round2_review.py`, `test_ux_phase1_usability_round1.py`, `test_ux_phase1_usability_round2.py`, `test_ux_phase2_error_type_proposals.py`, `test_ux_phase2_shell.py`, `test_ux_phase4_feedback.py`, `test_voi_merge_composition.py`, `test_voi_stopping.py`, `test_voi_v2.py`, `test_voyage_fallback.py`, `test_workbench_assistance.py`.

## Calls and cost

None. No paid request, no model load, no download, no GPU process; every Python run outside pytest used `env -i` with an empty HOME and LEARNLOOP_CONFIG_DIR and no routes.

## Landing onto main

Landed in `learnanything-merge2` on `merge/lr-p1-onto-main`, from main `6e1d40717` (AD2+AD3 at `mvp-0.30` with
migration 214, RW2d at `mvp-0.31` with migration 219 and `fixtures/migration_head_219`) and `retrieval/local-p1` at
`13c80e0c4`. The branch's base carried the E0/E1 experiment branches (harness code, specs, the E0/E1 reports); they
land with it. **No algorithm successor** (spec §6): the chain, `LATEST_ALGORITHM_VERSION` (`mvp-0.31`) and the
template text are main's. Orchestrator rulings: Codex final verify `20261024-224526-GAsewL` confirmed F1-F4 and F17
fixed; F5, F18 and F19 are non-blocking (open items below).

### Commits and conflicts

- `6b4cfb65e`: the merge (`--no-ff`). **425 files conflicted**:
  - 412 generated references: main's side taken, then regenerated.
  - `config/template.py` (20 hunks): both stages' comment lines on every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry
    (P1's line added to `mvp-0.30` and `mvp-0.31` too); all 22 hashes recomputed after.
  - `substrate/rebuild_orchestrator.py`: AD2+AD3's `adaptive_difficulty` and `item_forecast_scores` replayers and
    P1's `retrieval_fusion_posteriors`, each with its runner.
  - `tests/test_rebuild_orchestrator.py`: the stale-row oracle plants a row in AD's three DERIVED tables and in
    `retrieval_fusion_posteriors`.
  - Seven migration tests (`test_ad1_migration`, `test_approach_maps_schema`, `test_help_assists_schema`,
    `test_library_asks_migration`, `test_reader_rw3b_migration`, `test_reader_rw7a_migration`,
    `test_t1_batch_origin_migration`): main's side, then the "nothing else changed" diffs subtract both
    `RW2D_ADDED_OBJECTS` and `P1_ADDED_OBJECTS`, and the applied lists end `219, 220`.
  - `fixtures/migration_head_219/{README.md,state.sqlite}` and `tests/cli_help_snapshot.json`: main's side, then
    rebuilt and regenerated (below).
- `83814302d`: the renumber and the head fixture (below).
- `247722912`: the 22 defaults snapshots.
- `55111b0ae`: references and the CLI help snapshot.
- `5a2c5db04`: a landing fix. The branch's import-linter contract `experiments-stay-outside-production` lists every
  production module, and `test_e0_isolation::test_the_import_linter_contract_names_every_production_package` failed in
  the gate on the composed tree: main's `learnloop.ad_successor_upgrade` (AD2+AD3) and
  `learnloop.workbench_field_signals_upgrade` (RW2d) were missing. Both added; the test (failing first, in the full
  suite) passes, `lint-imports` 35 kept.

Files both sides changed that merged cleanly include `db/table_roles.py`, `params/parameter_registry.py`,
`config/schema.py`, `tests/test_architecture.py` (both stores in the audited-writer list) and the launch-site and
HTTP-client audit lists; each composed with no overlap.

The E0/E1 material was checked: `docs/reviews/experiments-e0-*.md`, `experiments-e1-*.md` and
`docs/reviews/artifacts/experiments-e{0,1}/` hold aggregates, pins, prices, plans and metrics only (no book text, no
question text; the only long quotations are the labelling rubric in the E0 Codex review). Nothing under
`fixtures-local/` and no model weights or vectors are tracked; no added file exceeds 200 KB.

### Renumber and head fixture

- `migrations/219_retrieval_spaces.sql` is now `220_retrieval_spaces.sql` (its header says why). Nothing inside
  names a version; the store, table-role and replayer comments, `test_architecture`'s note and
  `test_retrieval_spaces_migration` (now from 219 to 220) follow. `test_rw2d_receipts_migration` subtracts P1's
  objects on its way to head.
- `fixtures/migration_head_220` is a backup-API copy of main's `migration_head_219` (which holds 214 and RW2d's
  219) with only 220 applied under `UPGRADE_SCRATCH_COPY`, copied into place with the backup API:
  `wal_checkpoint(TRUNCATE)` (0, 0, 0), `journal_mode=DELETE`, header bytes 1/1, `integrity_check` ok,
  `foreign_key_check` empty, no companion files. Against main's 219 it adds exactly 220's ten objects (three
  tables, three autoindexes, two indexes, two triggers), all identical to the branch's head; no other object changed
  and only `schema_migrations` gained a row.
- `migration_head_219` was renamed to it (as T1 and RW2d did); the README was composed (header, the 220 paragraph,
  this rebuild).
- The head path is named in 36 test files and in the two `db_*_reference.py` scripts (three times in
  `db_generate_reference.py`), with `SCHEMA_HEAD = 220` in both; the head-version asserts read 220.
- `table_roles`: `embedding_spaces` WORKFLOW, `retrieval_feedback` RECEIPT, `retrieval_fusion_posteriors` DERIVED
  with exactly one replayer (`test_table_roles`, `test_retrieval_spaces_migration` pass).

### Regeneration

- **References.** `db_generate_reference.py` then `db_validate_reference.py`: **0 errors**, schema head **220**,
  **351** table notes, **1,046** configuration leaves (main 348 and 1,034), 4,743 wikilinks checked. The hand-written
  counts in `Database.md` and `Configuration.md` were updated.
- **Defaults snapshots.** All **22** recomputed with `defaults_fingerprint_for_version` (template `.pyc` cleared); a
  rerun gives 0 mismatches. Checked against main's code at every version: **no value changed and no key removed**;
  each version gains exactly 12 keys, all under `embedding.local`, `embedding.fallback` and `embedding.source_space`.
  The successor chain, the latest tag and the template text are identical to main's.
- **CLI help snapshot.** Regenerated: main's entries plus `embeddings local {setup,index,profile,status}`,
  `embeddings fallback backfill`, `embeddings fusion refit` and `experiments e0/e1`; only `<root>` and `embeddings`
  changed text.
- **RPC pins** (serializer snapshot, desktop RPC contract, mobile allowlist): pass in the full suite; no file changed.
- **`validate_vault.py`**: passes (1,154 notes, 1,152/1,152 reachable).
- **Failing before this stage, not fixed:** `desktop_validate.py` still stops on
  `components/pdfSelection/testing/syntheticBook.ts`; `module_validate.py` reports **1,189** issues (1,079 at RW2d's
  landing; the new ones are this stage's and E0/E1's modules without module notes).

### Gate

Setup: `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2` (5.14.0) in 5G scopes, `TMPDIR` = merge2's
`fixtures-local/tmp`. Every later Python command ran from the venv under `env -i` with empty `HOME`, `CODEX_HOME` and
`LEARNLOOP_CONFIG_DIR`. pytest lanes in 10G/2G scopes at `-n 8` under `flock /tmp/learnloop-fullsuite.lock`;
everything else in 5G/1G. Gate head `55111b0ae` (the landing fix `5a2c5db04` changes only `pyproject.toml`'s
contract). Logs: `fixtures-local/lr-p1-landing-*.log`.

| Step | Result |
|---|---|
| `lint-imports --no-cache` | **35 kept**, 0 broken (before and after the fix) |
| full suite (`pytest -n 8`, 63 min 16 s) | **22,447 passed**, 2 failed, 3 skipped, 38 xfailed |
| failure 1 | `test_e0_isolation::test_the_import_linter_contract_names_every_production_package`: real, a composition gap; fixed in `5a2c5db04` (above); the file passes (4) |
| failure 2, alone, 3 times | `test_reading_hardening_2_fixes::test_f1_a_build_whose_worker_failed_to_start_is_run_by_the_sweep`: **3/3 passed** (4.5 s each). The known load flake (the parity runs shared the machine) |
| durability (`-m durability`) | **122 passed** (RW2d's 121 plus this stage's) |
| `npm install`; `npm run typecheck` | ok; clean |
| `npm test -- --maxWorkers=4` (whole vitest) | **206 files, 1,738 tests passed** |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path src-tauri/Cargo.toml` | finished |
| worktree, tracked fixtures | `git status` clean after every lane; no non-empty `-wal` beside a fixture |

### Parity (backup-API copies; no model call)

**Setup.** Scripts in `fixtures-local/landing-lr-p1/scripts/`, outputs in `out/`.
- **Copies.** The owner's backups `fixtures-local/vault-backups-20261025-mvp030/{linear_algebra,probability}`
  (`mvp-0.30`, schema 218 with 214, 0 `model_call_receipts`) were each copied once as whole trees with
  `copy_tree_with_databases` into `landing-lr-p1/orig/`; every other copy came from those through the same helper.
- **Not opened:** the main checkout's `fixtures/linear_algebra`, `fixtures/probability` and `fixtures/arxiv_v2`.
- **Code.** Main's is `git archive main` (`6e1d40717`), the merge's `git archive 55111b0ae` (whole trees, so each
  code runs its own `migrations/`), each first on `sys.path`. An audit hook logs every process start and every
  socket connection and refuses any Codex process and any non-loopback connection. **None was attempted: the log is
  empty** (no process start, no connection at all).
- **Environment and routes.** `env -i` with empty `HOME` / `CODEX_HOME` / `LEARNLOOP_CONFIG_DIR`. Every route at
  `127.0.0.1:9` through unset-key loopback profiles (63 tasks; only the disabled, keyless `embedding` profile is not
  a loopback); rewrite, rerank, dense and embeddings off; `embedding.local` / `embedding.fallback` at their defaults
  (off); `build_on_serve` and outcome placement off. Clock frozen at 2026-10-19 09:00 UTC.

**(a) At `mvp-0.31`, main vs the merge.**
- `upgrade --to mvp-0.31` plus `rebuild-derived-state` twice with main's code (`u31`) and with the merge's (`m31`):
  rc 0 on both vaults ("mvp-0.30 -> mvp-0.31").
- **Schema** (`u31` vs `m31`, and `u31` opened by each code, `c31_main` / `c31_merge`): the merge has exactly 220's
  ten objects more; no SQL differs, no column added, nothing only on main. FK 0, integrity ok on all.
- **Rows** (353 common tables; LA 18,300 rows, probability 8,207): `c31_main` vs `c31_merge` identical, row for row
  (`schema_migrations` has 220 extra). `u31` vs `m31` identical once the ids and timestamps each run mints are
  masked (raw, only those differ in ten tables, among them `parameter_registry` with the same 352 keys). The three
  new tables are empty.
- **`rebuild --shadow`** (main on `u31`; the merge on `m31` and on `c31_merge`): 0 / 0 / 0 (facet, mastery,
  schedule), live database unchanged. The only difference in the report is the replayer list (13 vs 14): the new
  `retrieval_fusion_posteriors` replayer runs, owns only its table and writes 0 rows (no receipts on these vaults).
  Its byte-identical replay on seeded receipts is a branch test (`test_local_fusion_core`, `test_rebuild_orchestrator`).
- **`doctor`**: 0 differences after normalisation (LA 57 issues / 1 error, probability 101 / 48, the same on both).
- **Served reads.** Certification and curves and the Today queue (no session, a session, greedy) are
  **byte-identical** on `c31_merge` and on `m31` against main's `c31_main` (LA cert 129,651 bytes, Today 43 items,
  528,665 bytes; probability 17,495 and 67, 741,269 bytes). The daily plan (read, serve, serve again, read) is
  identical except `card_hash`, `snapshot_hash` and the card hash inside `detail_json`, which differ between any two
  runs (as recorded at DL2's, T1's, AD2+AD3's and RW2d's landings).

**(b) Search at the defaults** (copies `s_main` / `s_merge` of `c31_main` / `c31_merge`). Ten fixed queries (five
linear algebra, five probability) on both vaults, each through `search_library` (quick and deep), `search_spans` over
the library scope, `find_sources` (`reading` policy, `explain` intent) and the tutor's `tutor_pool` (two LOs, library
context), wall timings stripped.
- **Identical main vs merge** on both vaults. The only difference in the raw dump is the merge's new in-memory
  dataclass field `SpanSearch.resolution` (`None`; `repr=False`, never serialized), present in the field dump of
  `search_spans` and `tutor_pool` and nowhere in any serialized result. `space_selection` is empty on every merge
  result (20 per vault) and absent from `describe()`.
- **No row written**: every table's row count and content digest are unchanged by the searches on both codes;
  `embedding_spaces`, `retrieval_feedback` and `retrieval_fusion_posteriors` stay at 0 rows.
- The same run on a copy with `[embedding.local] enabled = true` and no setup gives the same bytes and writes no row
  (dense retrieval is off on these copies, so there is no meaning list for the seam to resolve).

**(c) The owner-run commands.** The CLI help lists them (above). On a copy of `c31_merge` (linear algebra) with an
empty `--data-root`, under the strict hook (every process start and every non-loopback connection refused and
logged; none was attempted):

| Command | Result |
|---|---|
| `embeddings local setup --dry-run` | rc 0, the plan (paths, pins, disk 783 GiB free of 45 needed); nothing created |
| `embeddings local setup` (no flag) | rc 1, `invalid`: "pass --i-understand-this-downloads-33-gb (or --adopt-model-dir); run --dry-run first" |
| `embeddings local status` | rc 0, `enabled: false` |
| `embeddings local index --dry-run` / `--now` | rc 1, `disabled` ("embedding.local.enabled is false") |
| `embeddings local profile --extraction-id …` | rc 1, `not_set_up` ("run `learnloop embeddings local setup`") |
| `embeddings fallback backfill --dry-run` / without | `disabled` per source, estimate 0 tokens / $0, nothing charged |
| `embeddings fusion refit` | rc 0, 0 contexts, 0 rows |

The database is unchanged by all of them, and the data root and `HOME` stay empty.

**Calls.** `model_call_receipts` has 0 rows in all 23 parity databases (no COMPLETED row, no row at all); no process
was started and no connection opened. No GPU, download or paid request. Spend: $0.

### Owner notes

- **Nothing changes until you run setup.** With `embedding.local.enabled` and `embedding.fallback.enabled` off (the
  defaults) retrieval, serving and plans are main's, byte for byte, and no new row is written. There is no
  successor and no `upgrade` to run; the migration (220, three empty tables) applies on the next open.
- **Commands** (from the stage record; none was run here):
  1. `uv run learnloop embeddings local setup --dry-run`, then either
     `uv run learnloop embeddings local setup --adopt-model-dir <E1 model dir> --adopt-env-python <E1 env>/bin/python`
     (records E1's verified artefacts without moving them) or `--i-understand-this-downloads-33-gb`.
  2. P0, the true 8,192-token profile, on a backup-API copy:
     `uv run learnloop embeddings local profile --vault fixtures-local/<copy> --extraction-id <id> --json`
     (one metered worker; nothing indexed).
  3. Set `embedding.local.enabled = true` in a vault, then `embeddings local index --vault <vault> --dry-run`,
     `--now`, and `embeddings local status --vault <vault>`. The local space indexes and reports coverage but serves
     no query until P1c/P2 (Qwen stands in).
  4. The Voyage fallback: **first opt out of Voyage's data use for training (spec Q7)** in the Voyage dashboard
     (Admin access and a payment method needed; it cannot be undone in the dashboard), and only for vaults outside
     the checkout (Q6). Then add `[ai.providers.voyage_context] type = "voyage_contextual_embedding"` and
     `[embedding.fallback] enabled = true`, and run `embeddings fallback backfill --vault <vault> --dry-run` first
     ($1 per run cap, admitted at the full $0.12/M).
  5. `uv run learnloop embeddings fusion refit --vault <vault>` (no model call).
- **Memory and GPU safety.** The worker runs in its own `systemd-run --user --scope -p MemoryMax=12G
  -p MemorySwapMax=0`, takes the GPU lock and the full-suite lock non-blocking (it waits rather than competing with a
  test run), and refuses to start under its memory and GPU floors. Run indexing and the profile when the machine is
  otherwise quiet (no full suite, no other GPU job).

### Open items

1. **F5 (High per Codex; ruled non-blocking by the orchestrator).** Exposures recorded from passages the new spaces
   show (MCP `find_passages`, library ask, tutor picks) can change coldness. An exposure is a true record of what was
   shown, the exposure-to-coldness rule is unchanged, showing a different passage is like adding content, spec §6
   says no successor, and at the defaults behaviour is main's byte for byte. **Owner decision requested:** keep §6's
   "No" (as landed), or make the P1 switches a successor for exposure-recording consumers (the P3 consumer audit
   should list them either way).
2. **F18 and F19 (Medium per Codex; ruled Low).** IPS propensities after an encoder-failure reassignment, and legacy
   randomized receipts read as p = 1. They affect only the learned fusion fit, which does not serve
   (`learned_fusion = false`), and no legacy receipts exist outside the branch. **MUST be fixed before
   `embedding.source_space.learned_fusion` is turned on.**
3. **Owner questions (pending):** confirm the P1 scoping (log citations, opens and the would-be learned weights,
   serve the seed; exploration off and near-tie only); the P0 bank posterior and pooling simulation proposed to fold
   into P2 (F10); the local space serves no query until P1c/P2.
4. **Desktop open-receipt wiring follow-up.** `record_open` and the Reader's search-hit click (`reader.retrieval_open`)
   landed; other result surfaces (library list, compare) do not send the receipt yet.
5. **The 8,192-token profile command** (P0) is owed: owner-run, on a backup-API copy, after setup.
6. `desktop_validate.py` and `module_validate.py` fail as before (above; 110 more module-note issues).
7. The parity copies' backup-API reads left empty `state.sqlite-wal` and `-shm` files beside both backup databases in
   the main checkout's `fixtures-local/vault-backups-20261025-mvp030/` (as at RW2d's landing). Harmless; left in
   place.

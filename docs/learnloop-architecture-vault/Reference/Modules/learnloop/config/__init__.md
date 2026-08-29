---
title: "learnloop.config"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/config/__init__.py"
source_paths:
  - "src/learnloop/config/__init__.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.config"
layer: "infrastructure"
concepts:
  - "Configuration"
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop.config module"
  - "src/learnloop/config/__init__.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-config"
---

# `learnloop.config`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/config/_package|learnloop.config]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.config` exists within [[Reference/Modules/learnloop/config/_package|learnloop.config]] to own the behavior summarized by its module contract: Typed configuration, compatibility normalization, templates, and loading.

The authoritative system-level explanation remains in [[Configuration]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/config/__init__.py](../../../../../../src/learnloop/config/__init__.py) |
| Source lines | 6 |
| Owning package | [[Reference/Modules/learnloop/config/_package|learnloop.config]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

No public top-level function or class definition is declared in this file.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `AIProviderConfig`, `LearnLoopConfig`
- [[Reference/Modules/learnloop/ai/multimodal|learnloop.ai.multimodal]] — imports `AIProviderConfig`
- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `AIProviderConfig`, `CodexConfig`; statically calls `CodexConfig`
- [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]] — imports `AIProviderConfig`, `CodexConfig`
- [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] — imports `AIProviderConfig`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]] — imports `AIProviderConfig`, `LearnLoopConfig`
- [[Reference/Modules/learnloop/attempts/evidence|learnloop.attempts.evidence]] — imports `EvidenceConfig`; statically calls `EvidenceConfig`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `EvidenceConfig`
- [[Reference/Modules/learnloop/attempts/surprise|learnloop.attempts.surprise]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/bootstrap|learnloop.bootstrap]] — imports `global_ai_defaults_path`, `load_config`; statically calls `global_ai_defaults_path`, `load_config`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `CODEX_PROVIDER_NAMES`, `ConfigLoadError`
- [[Reference/Modules/learnloop/content/pipeline/acquisition_preview|learnloop.content.pipeline.acquisition_preview]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/content/pipeline/build_plan|learnloop.content.pipeline.build_plan]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `AudioIngestConfig`, `IngestBudgetsConfig`; statically calls `AudioIngestConfig`, `IngestBudgetsConfig`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `PdfIngestConfig`
- [[Reference/Modules/learnloop/content/sources/pdf_extraction|learnloop.content.sources.pdf_extraction]] — imports `PdfIngestConfig`; statically calls `PdfIngestConfig`
- [[Reference/Modules/learnloop/diagnosis/gate_fit|learnloop.diagnosis.gate_fit]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/diagnosis/predictive_eig|learnloop.diagnosis.predictive_eig]] — imports `ProbeIRTConfig`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `ProbeIRTConfig`; statically calls `ProbeIRTConfig`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `ProbeIRTConfig`, `ProbeSelfTagConfig`; statically calls `ProbeIRTConfig`, `ProbeSelfTagConfig`
- [[Reference/Modules/learnloop/diagnosis/signal_quantiles|learnloop.diagnosis.signal_quantiles]] — imports `SchedulerFollowupConfig`
- [[Reference/Modules/learnloop/ingest/transcription|learnloop.ingest.transcription]] — imports `AudioIngestConfig`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `MasteryConfig`
- [[Reference/Modules/learnloop/learner/recall_calibration|learnloop.learner.recall_calibration]] — imports `SeverityExampleConfig`, `default_severity_examples`; statically calls `default_severity_examples`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `EvidenceConfig`, `LearnLoopConfig`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `CODEX_PROVIDER_NAMES`, `LearnLoopConfig`, `OPENROUTER_TRANSCRIPTION_PROVIDER`, `load_config`; statically calls `load_config`
- [[Reference/Modules/learnloop/ops/settings_store|learnloop.ops.settings_store]] — imports `AIProviderConfig`, `CODEX_PROVIDER_NAMES`, `ENV_KEY_RE`
- [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]] — imports `CODEX_PROVIDER_NAMES`
- [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] — imports `LearnLoopConfig`; statically calls `LearnLoopConfig`
- [[Reference/Modules/learnloop/scheduling/fsrs_fitting|learnloop.scheduling.fsrs_fitting]] — imports `FsrsFittingConfig`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `LearnLoopConfig`; statically calls `LearnLoopConfig`
- [[Reference/Modules/learnloop/substrate/shadow_rebuild|learnloop.substrate.shadow_rebuild]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `CODEX_PROVIDER_NAMES`
- [[Reference/Modules/learnloop/tutor/question_signal|learnloop.tutor.question_signal]] — imports `TutorPromotionConfig`, `TutorQAConfig`
- [[Reference/Modules/learnloop/tutor/teach_back|learnloop.tutor.teach_back]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_config`, `write_default_config`; statically calls `load_config`, `write_default_config`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop_sidecar/__main__|learnloop_sidecar.__main__]] — imports `load_dotenv`; statically calls `load_dotenv`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `CODEX_PROVIDER_NAMES`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `CODEX_PROVIDER_NAMES`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `CODEX_PROVIDER_NAMES`, `global_ai_defaults_path`, `global_settings_path`; statically calls `global_ai_defaults_path`, `global_settings_path`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/config/compat|learnloop.config.compat]] — imports `module`
- [[Reference/Modules/learnloop/config/loader|learnloop.config.loader]] — imports `module`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `module`
- [[Reference/Modules/learnloop/config/template|learnloop.config.template]] — imports `module`

### Platform and third-party dependencies

- Standard library: none imported directly
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]], [[Reference/Modules/learnloop/ai/multimodal|learnloop.ai.multimodal]], [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]], [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]], [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] and 41 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/helpers.py](../../../../../../tests/helpers.py) — direct import
- [tests/test_agent_run_tokens.py](../../../../../../tests/test_agent_run_tokens.py) — direct import
- [tests/test_ai_config.py](../../../../../../tests/test_ai_config.py) — direct import
  - `test_ai_provider_profiles_load_openai_chat`
  - `test_animation_config_and_routing_parity`
  - `test_canonical_ingest_retry_defaults_codex_for_codex_vault`
  - `test_canonical_ingest_retry_follows_ingest_for_non_codex`
  - `test_codex_checkout_path_env_override_applies_to_codex_and_ai_provider`
  - `test_codex_checkout_path_loaded_from_global_settings_file`
  - `test_default_config_contains_ai_codex_profile`
  - `test_default_config_contains_audio_and_native_ingest`
  - `test_default_config_contains_recall_error_impacts`
  - `test_default_config_seeds_openrouter_profile`
  - `test_default_config_ships_blank_codex_checkout_path`
  - `test_error_impacts_max_sharpening_maps_to_recall_coverage_runtime_field`
  - `test_global_ai_timeout_is_applied_to_codex_sdk_profiles`
  - `test_in_memory_defaults_match_persisted_algorithm_and_codex_profile`
  - `test_legacy_codex_config_maps_to_ai_profile`
  - `test_legacy_codex_routes_upgrade_to_workload_specific_effort_profiles`
  - `test_pdf_native_engine_and_input_modalities_parse`
  - `test_shell_env_wins_over_global_settings_file`
  - `test_sparse_codex_ai_profile_uses_current_codex_defaults`
- [tests/test_ai_runtime.py](../../../../../../tests/test_ai_runtime.py) — direct import
  - `test_ai_runtime_reports_missing_provider`
  - `test_openai_chat_runtime_uses_vault_dotenv`
  - `test_openrouter_runtime_defaults_to_openrouter_key_env`
  - `test_openrouter_runtime_ready_with_api_key`
  - `test_openrouter_runtime_requires_api_key`
  - `test_vault_dotenv_does_not_override_shell_env`
- [tests/test_blueprint_projection.py](../../../../../../tests/test_blueprint_projection.py) — direct import
- [tests/test_characterization_mastery_reliability.py](../../../../../../tests/test_characterization_mastery_reliability.py) — direct import
  - `test_error_impact_turns_reliability_into_observation_weight`
- [tests/test_cli_generate_practice.py](../../../../../../tests/test_cli_generate_practice.py) — direct import
  - `test_provider_timeout_override_reaches_codex_sdk_client`
- [tests/test_codex_http_client.py](../../../../../../tests/test_codex_http_client.py) — direct import
  - `test_http_codex_client_health_and_grading_round_trip`
  - `test_http_codex_client_misconception_match_bare_payload`
  - `test_http_codex_client_misconception_match_round_trip`
- [tests/test_codex_output_schema.py](../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_http_adapter_strips_the_usage_envelope_but_not_a_bad_field`
  - `test_sdk_authoring_path_passes_strict_schema_to_codex`
  - `test_sdk_codex_client_logs_full_prompt_and_response`
  - `test_sdk_codex_turn_timeout_interrupts_and_returns`
  - `test_sdk_reader_preset_regenerates_when_app_server_rejects_hex_escape`
  - `test_sdk_reader_preset_repairs_invalid_unicode_json_once`
  - `test_sdk_teach_back_authoring_passes_source_and_quest_to_prompt`
- [tests/test_codex_runtime.py](../../../../../../tests/test_codex_runtime.py) — direct import
  - `test_codex_runtime_ready_when_checkout_revision_and_health_pass`
  - `test_codex_runtime_reports_auth_required`
  - `test_codex_runtime_reports_missing_checkout`
  - `test_codex_runtime_reports_revision_mismatch`
  - `test_codex_runtime_reports_startup_timeout`
  - `test_codex_runtime_reports_unavailable_without_transport_or_failed_health`
  - `test_codex_runtime_starts_app_server_after_initial_health_failure`
- [tests/test_cold_start_revision.py](../../../../../../tests/test_cold_start_revision.py) — direct import
  - `test_channel_doubt_never_inverts_direction_on_easy_items`
  - `test_interpretation_variance_broadens_not_blocks`
  - `test_soft_score_replaces_raw_fraction`
- [tests/test_config_refactor.py](../../../../../../tests/test_config_refactor.py) — direct import
  - `test_canonical_transcription_route_wins_over_legacy_audio_input`
  - `test_config_responsibilities_have_canonical_module_owners`
  - `test_defaults_snapshot_is_keyed_by_algorithm_version`
  - `test_endpoint_audio_config_does_not_create_a_chat_route`
  - `test_generated_template_is_decision_only_schema_v2`
  - `test_legacy_codex_is_input_only_and_sidecar_does_not_reexport_it`
  - `test_legacy_openrouter_audio_becomes_a_dedicated_transcription_route`
  - `test_minimal_template_preserves_non_provider_effective_defaults`
  - `test_provider_profiles_use_discriminated_types_and_ignore_retired_auth`
  - `test_provider_without_type_keeps_codex_sdk_compatibility`
  - `test_retired_keys_parse_and_are_ignored`
  - `test_schema_v1_is_accepted_but_v2_is_generated`
  - `test_tracked_fixture_config_corpus_is_compatibly_normalized`
- [tests/test_conjunctive_instruments.py](../../../../../../tests/test_conjunctive_instruments.py) — direct import
  - `test_a_no_reliable_decomposition_contract_does_not_suppress_elicitation`
  - `test_an_item_with_an_available_trace_contract_is_self_documenting`
  - `test_default_config_share_is_one_half`
  - `test_disabling_elicitation_wins_over_every_other_arm`
  - `test_method_selection_without_a_contract_is_elicited_with_a_decision_prompt`
  - `test_procedure_execution_shows_its_work`
  - `test_schema_interpretation_gets_the_applicability_prompt`
  - `test_the_session_budget_is_hard`
- [tests/test_evidence_config.py](../../../../../../tests/test_evidence_config.py) — direct import
  - `test_default_config_text_round_trips_canonical_values`
  - `test_override_flows_through_resolvers`
  - `test_partial_toml_override_keeps_other_types_at_defaults`
- [tests/test_fsrs_fitting.py](../../../../../../tests/test_fsrs_fitting.py) — direct import
  - `test_bounds_and_ordering_projection`
  - `test_deterministic`
  - `test_recoverability_beats_defaults_on_perturbed_weights`
  - `test_refuses_below_min_reviews`
  - `test_shrinkage_dominates_at_tiny_n`
- [tests/test_gate_fit.py](../../../../../../tests/test_gate_fit.py) — direct import
  - `test_label_assembly`
  - `test_label_assembly_excludes_old_feature_semantics`
- [tests/test_gate_score.py](../../../../../../tests/test_gate_score.py) — direct import
- [tests/test_ingest_m3.py](../../../../../../tests/test_ingest_m3.py) — direct import
  - `test_acquisition_preview_audio_is_always_external`
  - `test_acquisition_preview_flags_potential_external_consent`
  - `test_acquisition_preview_pdf_native_engine_is_external`
  - `test_acquisition_preview_reports_recognition_dupes_and_existing`
  - `test_build_plan_warns_when_provider_has_no_configured_context_limit`
  - `test_legacy_openrouter_audio_translation_preserves_consent_surface`
- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_default_synthesis_client_resolves_openrouter_in_inherited_new_vault`
  - `test_openrouter_transcription_setting_routes_audio_via_chat`
- [tests/test_ingest_transcription.py](../../../../../../tests/test_ingest_transcription.py) — direct import
- [tests/test_irt_difficulty.py](../../../../../../tests/test_irt_difficulty.py) — direct import
  - `test_conditional_masses_match_spec_table_at_b_zero`
  - `test_default_step_cap_leaves_normal_attempts_untouched`
  - `test_difficulty_defaults_to_zero_when_unset`
  - `test_difficulty_falls_back_to_learning_object_prior`
  - `test_difficulty_from_prior_toggle_pins_b_to_default`
  - `test_difficulty_is_clamped_to_b_abs_max`
  - `test_difficulty_resolves_practice_item_first`
  - `test_eig_prefers_boundary_items_over_trivial_and_impossible`
  - `test_enabled_ekf_differs_from_legacy_on_target`
  - `test_every_conditional_is_normalized`
  - `test_kalman_gain_well_defined_at_extreme_difficulty`
  - `test_misconception_overlay_routes_error_fractions_exactly`
  - `test_mu_clamp_bounds_the_mean`
  - `test_step_cap_limits_overshoot_on_broad_prior`
  - `test_sustained_brutal_corrects_do_not_drift_past_mu_abs_max`
- [tests/test_item_parameters.py](../../../../../../tests/test_item_parameters.py) — direct import
  - `test_resolver_uses_posterior_only_when_enabled`
- [tests/test_mastery.py](../../../../../../tests/test_mastery.py) — direct import
  - `test_drift_increases_movement_after_long_gap`
  - `test_hint_dampening_reduces_update`
  - `test_low_confidence_moves_mean_less_than_high_confidence`
  - `test_positive_score_raises_mean`
  - `test_zero_score_does_not_raise_mean`
- [tests/test_multimodal_client.py](../../../../../../tests/test_multimodal_client.py) — direct import
  - `test_openrouter_inherits_media_methods_with_headers`
  - `test_supports_input_modality_and_audio_format_helpers`
- [tests/test_openai_chat_client.py](../../../../../../tests/test_openai_chat_client.py) — direct import
- [tests/test_openrouter_client.py](../../../../../../tests/test_openrouter_client.py) — direct import
- [tests/test_pdf_extraction.py](../../../../../../tests/test_pdf_extraction.py) — direct import
  - `test_cache_key_excludes_api_key`
  - `test_explicit_marker_engine_requires_marker`
  - `test_marker_empty_output_raises`
  - `test_marker_engine_converts_and_caches`
  - `test_marker_llm_options_map_to_openai_service`
  - `test_marker_pdftext_worker_override_is_preserved`
  - `test_marker_torch_device_pin_sets_env`
  - `test_marker_upgrade_changes_cache_key`
  - `test_resolved_pdf_config_overrides_and_validates`
- [tests/test_primed_attempts.py](../../../../../../tests/test_primed_attempts.py) — direct import
  - `test_cold_attempt_advances_last_evidence_at`
  - `test_primed_attempt_keeps_last_evidence_at_ekf`
  - `test_primed_attempt_keeps_last_evidence_at_legacy`
  - `test_primed_failure_moves_mean_more_than_cold_failure`
  - `test_primed_success_moves_mean_less_than_cold_success`
  - `test_primed_success_shrinks_variance_less`
- [tests/test_provider_resolution_parity.py](../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_composition_root_uses_fallback_and_preserves_requested_selection`
  - `test_config_matrix_executes_all_six_production_resolution_paths`
  - `test_explicit_and_environment_selections_suppress_fallback`
  - `test_legacy_http_declares_exactly_its_endpoint_operations`
  - `test_manual_is_a_typed_no_client_outcome`
  - `test_named_codex_profile_identity_survives_provider_construction`
  - `test_provider_resolution_config_matrix_is_uniform`
- [tests/test_reader_dialogue.py](../../../../../../tests/test_reader_dialogue.py) — direct import
  - `test_reader_enabled_by_default`
- [tests/test_recall_calibration.py](../../../../../../tests/test_recall_calibration.py) — direct import
  - `test_recall_calibration_examples_are_config_backed`
- [tests/test_registry_audit.py](../../../../../../tests/test_registry_audit.py) — direct import
- [tests/test_scheduler.py](../../../../../../tests/test_scheduler.py) — direct import
- [tests/test_self_attributed_misconceptions.py](../../../../../../tests/test_self_attributed_misconceptions.py) — direct import
- [tests/test_settings_sidecar.py](../../../../../../tests/test_settings_sidecar.py) — direct import
  - `test_new_vault_inherits_ai_routes_but_existing_vault_is_untouched`
  - `test_update_ai_settings_materializes_openrouter_grading_profile`
  - `test_update_ai_settings_rejects_unknown_values_without_persisting`
  - `test_update_ingest_settings_persists_budgets_and_provider_limits`
  - `test_update_ingest_settings_rejects_bad_budgets_without_persisting`
- [tests/test_settings_store.py](../../../../../../tests/test_settings_store.py) — direct import
  - `test_apply_config_updates_creates_missing_tables`
  - `test_apply_config_updates_preserves_comments_and_unrelated_lines`
  - `test_copy_ai_settings_copies_routing_and_materialized_profiles`
  - `test_copy_ai_settings_default_source_is_semantic_noop`
  - `test_copy_ai_settings_errors_on_missing_or_invalid_source`
  - `test_openrouter_task_profile_values_round_trip`
  - `test_save_ai_settings_to_creates_target_and_seeds_new_vault`
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_sidecar_create_vault_inherits_ai_settings_from_active_vault`
  - `test_sidecar_create_vault_reopen_does_not_touch_existing_ai_settings`
  - `test_update_ai_settings_persists_openrouter_grading_route`
  - `test_update_ai_settings_rejects_unknown_provider_use_case_and_slug`
  - `test_update_ingest_settings_toggles_native_and_transcription`
  - `test_update_ingest_settings_transcription_provider_switch`
- [tests/test_signal_quantiles.py](../../../../../../tests/test_signal_quantiles.py) — direct import
  - `test_absolute_fallback_below_min_samples`
  - `test_absolute_mode_disables_quantiles`
  - `test_current_attempt_excluded`
  - `test_positive_direction_rows_do_not_count`
  - `test_quantile_resolution_with_enough_samples`
  - `test_severity_quantile_reads_gate_diagnostics`
  - `test_window_limits_history`
- [tests/test_sim_teach_back.py](../../../../../../tests/test_sim_teach_back.py) — direct import
  - `test_teach_back_config_overrides_round_trip`
- [tests/test_simulation.py](../../../../../../tests/test_simulation.py) — direct import
  - `test_config_overrides_apply_in_memory_only`
- [tests/test_source_ingestion_adapters.py](../../../../../../tests/test_source_ingestion_adapters.py) — direct import
  - `test_pdf_source_is_normalized_to_markdown`
  - `test_pdf_without_text_layer_raises`
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import
  - `test_chat_transport_executes_every_feature_operation`
  - `test_legacy_http_supports_exactly_eight_operations_and_degrades_the_rest`
  - `test_sdk_transport_executes_every_feature_operation`
- [tests/test_surprise.py](../../../../../../tests/test_surprise.py) — direct import
  - `test_fsrs_interval_factor_within_bounds`

## Modification guidance

- Change this file when intentionally adding or removing a package-level re-export; keep implementation logic in the owning module.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/config/__init__.py](../../../../../../src/learnloop/config/__init__.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

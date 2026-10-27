"""Every column of every table an AD operation can read, classified (the AD23 redesign round 5).

``protected_tables`` classifies tables; a NEUTRAL table is readable raw inside an operation. A
neutral table can still hold content (a model call's prompt and output, an assessment contract's
question and answer), so the guard is column-aware: every column of every table in
``protected_tables.ROLES`` is one of

* ``metadata``: ids, timestamps, counts, statuses, kinds, costs, versions, hashes, token counts,
  and JSON lists of ids or numbers: readable raw (by the table's role);
* ``content``: any text, JSON or blob that can carry source text, an item, a prompt, an answer, a
  rubric or a model's input or output. Inside an operation it is read only by the rules
  (``rules()``: the material view, whose SQL carries ``/* ad-rules */``), which resolve protection
  first; any other read of it is refused (``operation.Guard``).

A table outside ``ROLES`` is unreadable inside an operation altogether. The completeness test
(``tests/test_ad_protected_tables.py``) fails on any column of a classified table in the head schema
that is not classified here (or classified twice, or no longer exists), so a migration classifies
the columns it adds. When in doubt a column is ``content``.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

METADATA = "metadata"
CONTENT = "content"

#: table -> (metadata columns, content columns), space-separated.
_CLASSES: dict[str, tuple[str, str]] = {
    "activity_administrations": (
        "id surface_id card_version_id family_id purpose administration_snapshot_hash "
        "target_contract_version_id target_support_hash grader_model_version_id "
        "selection_policy_version_id decision_params_hash eligibility_json reservation_id "
        "legacy_backfilled created_at",
        "snapshot_json assistance_json feedback_condition reading_phase admin_context_json"),
    "activity_card_versions": (
        "id card_id version card_contract_hash schema_version predecessor_card_version_id lineage_kind "
        "legacy_contract_version_id created_at",
        "contract_json"),
    "activity_cards": (
        "id family_id created_at",
        ""),
    "activity_exposure_events": (
        "id surface_id administration_id surface_hash kind purpose consumes_unseen created_at",
        "fingerprint detail_json"),
    "activity_families": (
        "id purpose legacy_kind created_at",
        "title"),
    "activity_family_membership_events": (
        "seq id family_id card_id practice_item_id action proposal_id judgment_id created_at",
        "variant_relation"),
    "activity_family_versions": (
        "id family_id version created_at",
        "family_spec_json"),
    "activity_observations": (
        "id administration_id surface_id attempt_id active_interpretation_id created_at",
        "response_ref evidence_eligibility eligibility_reason"),
    "activity_surface_lifecycle_events": (
        "id surface_id reservation_id administration_id kind created_at",
        "reason detail_json"),
    "activity_surface_reservations": (
        "id surface_id goal_id target_contract_version_id target_support_hash purpose status "
        "eligibility_json administration_id reserved_at closed_at",
        ""),
    "activity_surfaces": (
        "id card_version_id surface_hash legacy_practice_item_id legacy_surface_unverifiable created_at",
        "fingerprint surface_json"),
    "ad_attempt_trace": (
        "attempt_id view input_status category prior_mean prior_var post_mean post_var information",
        "p_categories_json points_json detail_json"),
    "ad_commission_results": (
        "id selection_id practice_item_id content_hash p_bar status state_hash landed_after_expiry "
        "features_match created_at protection_epoch",
        "features_json"),
    "ad_coupling_versions": (
        "id subject_id version coupling_version run_ids_json adopted_by adopted_at",
        "note"),
    "ad_dose_offers": (
        "id row_kind draw_id draw_key visit_id extraction_id section_id learning_object_ids_json "
        "base_version floor seed u chosen_variant forecast_p created_at protection_epoch",
        "feasible_json infeasible_json propensities_json content_json detail_json"),
    "ad_reading_opportunities": (
        "id opportunity_key kind subkind source_table source_id source_written_at learning_object_id "
        "dose_offer_id mapping_version sweep swept_at protection_epoch",
        "facet_doses_json authority_class sweep_ref"),
    "ad_relatedness_runs": (
        "id run_key subject_id input_hash judgment_ids_json status prompt_version created_at",
        "units_json judge_model"),
    "ad_selections": (
        "id decision_key kind view learning_object_id daily_plan_id block_id slot_position slot_item_id "
        "mode seed u chosen_item_id propensity router_decision_id router_propensity pair_propensity "
        "empty_support state_hash algorithm_version generating_job_id created_at protection_epoch",
        "cell_facet cell_capability support_json excluded_json constants_json chosen_point_json "
        "versions_json"),
    "ad_state": (
        "view state_hash",
        "part payload_json as_of versions_json"),
    "agent_runs": (
        "id purpose model provider prompt_version sdk_version codex_revision input_context_hash "
        "started_at completed_at status provider_type provider_revision est_input_tokens "
        "est_output_tokens actual_input_tokens actual_output_tokens",
        "output_schema error_message prompt_template"),
    "assessment_contract_versions": (
        "id practice_item_id contract_hash schema_version created_at",
        "contract_json"),
    "assumption_decisions": (
        "id learning_object_id source trigger_kind trigger_ref p q_used theta_known predictor predictor_version "
        "first_review_due quick_check_session_id algorithm_version created_at",
        "interval_json config_json inputs_json"),
    "assumption_returns": (
        "id assumption_id learning_object_id reason trigger_ref algorithm_version created_at",
        ""),
    "attempt_diagnoses": (
        "id attempt_id blind_grade_record_id agent_run_id diagnosis_prompt_version provider model mode "
        "history_mode status latency_seconds supersedes_id created_at",
        "proposal_json causal_view_json validation_report_json error"),
    "attention_block_events": (
        "id block_id event_ordinal kind created_at",
        "detail_json"),
    "attention_blocks": (
        "id session_id commitment_id action subtype budget_minutes neighborhood_json exit_rules_json "
        "short_circuit_reason content_hash created_at daily_plan_id plan_ordinal lane chosen_by "
        "decision_ref",
        "reading_json"),
    "blind_grade_records": (
        "id attempt_id agent_run_id grading_prompt_version output_schema_version context_hash "
        "supersedes_id created_at",
        "record_json"),
    "capability_aliases": (
        "id registry_version legacy_value canonical created_at",
        ""),
    "causal_activity_classification_events": (
        "id attempt_id seq near_clone closes_pre_intervention_segment eligible_for_fsrs "
        "eligible_for_certification source policy_version created_at",
        "contamination_class near_clone_basis detail_json"),
    "causal_hypotheses": (
        "id episode_key version supersedes_id attempt_id error_event_id learning_object_id operation "
        "repair_class_id status generation_agent_run_id model created_at",
        "cause_scope statement statement_normalized mechanism target_ref_json applicability_json "
        "postdictive_claims_json evidence_json repair_class_basis repair_class_unresolved_reason"),
    "commitment_events": (
        "id commitment_id commitment_version_id kind created_at",
        "detail_json"),
    "commitment_target_versions": (
        "id commitment_version_id target_kind salience role created_at",
        "target_ref provenance_json"),
    "commitment_versions": (
        "id commitment_id version predecessor_version_id goal_id depth_policy_version_id "
        "depth_envelope_version_id target_set_hash version_hash created_at",
        "intent_text interpretation_text depth_preset attention_bounds_json due_hint hiatus_hint reason "
        "provenance_json change_reason author"),
    "commitments": (
        "id learner_id idempotency_key created_at",
        "created_action"),
    "composed_selector_telemetry_horizons": (
        "id horizon_days opened_at retires_at retired_at status",
        "detail_json"),
    "controller_ownership": (
        "commitment_id ownership_version policy_version receipt_id assigned_at",
        "owner"),
    "daily_plans": (
        "id local_date kind parent_plan_id minutes_budget remembered_minutes minutes_source split_json "
        "admission_json estimator_version source chooser status stop_reason algorithm_version config_hash "
        "created_at updated_at completed_at",
        ""),
    "decision_features": (
        "id decision_id decision_type algorithm_version created_at",
        "ability_vector_json item_demand_vector_json context_json"),
    "depth_envelope_versions": (
        "id envelope_version content_hash created_at",
        "bounds_json reviewed_edges_json"),
    "depth_policy_versions": (
        "id policy content_hash created_at",
        "body_json"),
    "derived_state_rebuilds": (
        "id scope learning_object_ids_json algorithm_version rebuilt_learning_objects replayed_attempts "
        "created_at canonical_projection_version coverage_denominator_version",
        ""),
    "diagnosis_context_receipts": (
        "id diagnosis_id context_hash context_as_of_attempt_id lagged_attempts failure_attempt_ids_json "
        "success_attempt_ids_json hypothesis_ids_json registry_candidate_ids_json anchoring_suspect "
        "created_at",
        "prerequisite_refs_json retrieval_json validated_citations_json"),
    "diagnosis_feedback": (
        "id diagnosis_id attempt_id cited_attempt_id forwarded_factor_id shown_at responded_at",
        "response"),
    "entity_source_links": (
        "id entity_type entity_id source_id revision_id extraction_id asset_hash span_hash patch_id "
        "status stale_at superseded_by_link_id created_at",
        "locator locator_scheme relation"),
    "error_events": (
        "id attempt_id learning_object_id error_type severity is_misconception status created_at "
        "updated_at misconception_id",
        "repair_plan_json misconception_statement misconception_consistent_answer"),
    "exam_pool_items": (
        "id goal_id practice_item_id facet_id difficulty_stratum reserved_at released_at",
        ""),
    "facet_capability_evidence": (
        "facet_id direct_positive_mass direct_negative_mass embedded_positive_mass embedded_negative_mass "
        "certification_credit algorithm_version created_at updated_at direct_certification_credit "
        "embedded_certification_credit unexercised_supporting_mass",
        "capability independent_surface_groups_json"),
    "facet_identity_actions": (
        "id created_at origin scope run_id proposal_id action survivor_facet_id retired_facet_ids_json "
        "judgment_ids_json judge prompt_version status applied_at undone_at",
        "before_json after_json merge_rows_json judge_model detail_json undo_detail_json"),
    "facet_merges": (
        "retired_facet_id surviving_facet_id merged_at proposal_item_id",
        "rationale"),
    "facet_recall_state": (
        "id facet_id capability_key practice_item_id recall_alpha recall_beta recall_mean recall_variance "
        "independent_evidence_mass raw_coverage_mass last_observed_at last_error_at consecutive_failures "
        "algorithm_version created_at updated_at",
        ""),
    "facet_registry_saves": (
        "id created_at status judgment_ids_json action_ids_json applied_at abandoned_at",
        "facets_json settle_detail_json"),
    "figure_predictions": (
        "id figure_id extraction_id prediction_index matched created_at",
        "learner_answer observed_json explanation_text"),
    "fitted_parameters": (
        "id scope fitted_at algorithm_version training_rows_count active deactivated_at created_at",
        "params_json training_data_through metrics_json"),
    "followup_tasks": (
        "id kind case_kind source_attempt_id remediation_episode_id expires_at status selected_item_id "
        "consumed_attempt_id learning_object_id created_at updated_at measurement_opportunity_id",
        "case_ref not_before context_json"),
    "forecast_receipts": (
        "id receipt_key kind forecaster forecaster_version scope decision_kind decision_ref "
        "source_attempt_id learning_object_id facet_id practice_item_id item_content_hash binding_kind "
        "plan_presentation_id probe_presentation_id followup_task_id scheduler_candidate_id event p "
        "inputs_hash status algorithm_version created_at received_at",
        "hypothesis_ref censor_reason forecast_json inputs_json inputs_as_of parameters_json "
        "versions_json"),
    "grade_adjudications": (
        "id observation_id administration_id reviewed_raw_event_ids_json adjudicator_source "
        "bounded_trust_weight resulting_interpretation_id superseded_adjudication_id created_at",
        "resolved_class resolved_distribution_json rationale provenance_json"),
    "grade_interpretations": (
        "id raw_grade_event_id observation_id administration_id calibration_model_id "
        "calibration_model_hash projection_algorithm_version channel_posterior_snapshot_id "
        "reference_prior_ids_json certainty_discount review_flag influence_flag created_at "
        "shared_certainty_lcb",
        "response_posterior_json criterion_posteriors_json credible_interval_json quarantine_state "
        "fallback_reason"),
    # A calibration model's alphas are numbers keyed by emission, as the model's reliability bins are.
    "grader_calibration_alphas": (
        "id model_id true_class alpha_json created_at",
        ""),
    # A calibration model's provenance and evidence manifest name its policy, bundle and evidence
    # counts (``attempts.grader_calibration``), never an answer or an item: metadata.
    "grader_calibration_models": (
        "id grading_prompt_version grader_output_schema_version grader_identity_hash semver "
        "parent_model_id content_hash scope_level outcome_schema_id outcome_schema_version domain "
        "length_bucket backoff_chain_json status count_heuristic_prior count_planted_sim "
        "count_exploratory_em count_adjudicated_anchor count_held_out_evaluation prequential_log_loss "
        "multiclass_brier reliability_bins_json sample_count eval_time_range_json prior_concentration "
        "created_at grader_provider grader_model_revision provenance_json evidence_manifest_json",
        ""),
    "grading_evidence": (
        "id attempt_id criterion_id points_awarded agent_run_id local_grader_id grader_tier created_at "
        "superseded_at superseded_by_evidence_id assessment_contract_version_id grading_revision "
        "observation_id recipe_id",
        "evidence notes learner_confidence attribution_json correlation_group"),
    "hypothesis_recurrence_groups": (
        "episode_key group_key root_episode_key class_count joined_by judge builder_version",
        "statement_normalized joined_by_ref"),
    "hypothesis_recurrence_review": (
        "id case_kind occurred_at builder_version",
        "left_ref right_ref blocking_left_ref blocking_right_ref source_ref detail_json"),
    "hypothesis_recurrence_state": (
        "scope builder_version active group_count member_count review_count",
        "input_fingerprint"),
    "ingest_batches": (
        "id workflow_type payload_schema_version subject_id source_set_id status created_at started_at "
        "finished_at cancel_requested priority origin_method",  # origin_method: T1's 218, an RPC method name
        ""),
    "ingest_job_dependencies": (
        "job_id depends_on_job_id",
        ""),
    "ingest_jobs": (
        "id batch_id ordinal job_type payload_schema_version status phase current_window total_windows "
        "usage_json attempt_count cancel_requested worker_id heartbeat_at created_at started_at "
        "finished_at",
        "payload_json message result_json error_json"),
    "interaction_events": (
        "id kind subject_type subject_id administration_id surface_id attempt_id affect_tap_kind "
        "attempt_duration_ms origin created_at occurred_at received_at client_id session_id visit_id "
        "payload_schema_version source_id revision_id render_view_id annotation_id commitment_id "
        "activity_id payload_hash client_idempotency_key producer_version app_version policy_version "
        "supersedes_event_id",
        "payload_json actor locator_json privacy_locality consent_context"),
    "interactive_figures": (
        "id extraction_id span_ids_json asset_id input_span_ids_json origin supersedes_id spec_version kind "
        "verification unsupported_kind model prompt_version input_hash created_at "
        # Reader RW5d P1 (migration 224).
        "request_id grounding tier program_version engine_sha256 runtime_digest instrumented_sha256 "
        "media_file_name fuller_of_id",
        "region_json revision_note spec_json verification_report_json goal_text input_span_keys_json checks_json"),
    "item_forecast_payloads": (
        "id owner_key forecaster kind content_hash created_at",
        "content_json"),
    "item_forecast_scores": (
        "receipt_id forecaster practice_item_id plan_presentation_id attempt_id p outcome status log_loss "
        "brier first_attempt_lo first_surface_cell",
        "capability detail_json"),
    "item_parameter_state": (
        "practice_item_id b_mean b_var evidence_count algorithm_version updated_at",
        ""),
    "item_serve_inputs": (
        "id receipt_key presentation_kind plan_presentation_id probe_presentation_id "
        "scheduler_candidate_id practice_item_id learning_object_id content_hash served_at pre_exposed "
        "resolution_version coupling_version created_at protection_epoch",
        "stamped_features_json task_feature_schema audit_json resolved_features_json signals_json "
        "z_v1_recalibration loadings_json"),
    "json_each": (
        "key type atom id parent fullkey path value",
        ""),
    "judgment_ledger": (
        "id created_at supersedes_id task left_kind left_id right_kind right_id judge prompt_version "
        "input_hash score",
        "judge_model verdict rationale"),
    "judgment_work_claims": (
        "claim_key task producer prompt_version input_hash state lease_owner lease_expires_at lease_epoch "
        "judgment_id created_at updated_at",
        ""),
    "learner_claims": (
        "id claim_type scope_type scope_id evidence_family claimed_level prior_pseudo_count source "
        "created_at applied_after_attempts",
        ""),
    "learner_gap_check_advances": (
        "id gap_id learning_object_id intent assumption_id original_due advanced_due algorithm_version created_at",
        ""),
    "learner_gap_commitments": (
        "id gap_id learning_object_id practice_item_id first_review_due algorithm_version created_at",
        ""),
    "learner_text_gap_reversals": (
        "id gap_id reversal actor created_at",
        "detail_json"),
    "learning_object_mastery": (
        "learning_object_id logit_mean logit_variance evidence_count last_evidence_at algorithm_version "
        "updated_at",
        ""),
    "lo_probe_state": (
        "learning_object_id status probe_phase_id hypothesis_set_id probe_attempts_completed "
        "probe_attempts_target entered_at completed_at algorithm_version updated_at",
        "families_converged_json completion_reason"),
    "measurement_contract_corrections": (
        "id correction_set_id source_practice_item_id source_contract_version_id "
        "corrected_practice_item_id corrected_contract_version_id consuming_projection_version "
        "historical_evidence_policy created_at",
        "reason correction_json"),
    "misconception_disposition_events": (
        "id misconception_id created_at replacement_misconception_id",
        "disposition reason"),
    "misconceptions": (
        "id learning_object_id concept_id facet_ids_json severity status source_error_event_ids_json "
        "created_at updated_at resolved_at operation correction_source_span_ids_json",
        "statement signature mechanism target_facet confused_with_facet trigger_conditions_json "
        "expected_signatures_json first_divergence_json non_applicable_controls_json promotion_reason "
        "correction_statement"),
    "model_call_receipts": (
        "id parent_call_id owner_kind owner_id purpose provider model prompt_hash schema_hash status "
        "started_at finished_at input_tokens output_tokens cached_input_tokens reasoning_tokens cost "
        "provider_response_id finish_reason error_type output_budget_tokens collection_version endpoint "
        "resolved_model cache_write_tokens usage_json budget_json judge question_set_version state_hash",
        "input_text schema_json output_text"),
    "model_work_checkpoints": (
        "cache_key purpose usage_json created_at",
        "result_json"),
    "outcome_schema_versions": (
        "id schema_id version observed_classes_json true_classes_json has_signature_error has_unanswered "
        "score_fraction_json content_hash created_at",
        ""),
    "outcome_schemas": (
        "id slug kind created_at",
        ""),
    "passage_links": (
        "id extraction_id span_id target_kind target_id relation pick_rank ledger_id state_key model "
        "prompt_version created_at",
        "quote ranks_json roles_json target_facets_json"),
    "pf_candidates": (
        "id run_id mint_request_id family_id parent_item_id learning_object_id prompt_version "
        "content_hash status difficulty difficulty_source published_item_id published_at created_at "
        "updated_at",
        "round tier generation_path declared_relation final_relation proposer_model payload_json "
        "verification verification_check rejection_filter filters_json panel_json selection_json "
        "cost_json judged_inputs_json"),
    "plan_presentations": (
        "id block_id router_decision_id controller_decision_id practice_item_id position origin "
        "scheduler_candidate_id probe_presentation_id session_id served_at",
        ""),
    "practice_attempts": (
        "id practice_item_id learning_object_id subject practice_mode attempt_type rubric_score "
        "correctness confidence latency_seconds hints_used error_type grader_confidence manual_review "
        "created_at updated_at session_id scheduler_slate_id scheduler_candidate_id primed "
        "probe_presentation_id answer_confidence submission_id declared_dont_know collection_version "
        "declared_stuck reference_status plan_presentation_id",
        "concept learner_answer_md evidence_facets_json evidence_weights_json manual_review_reason "
        "entry_surface evidence_origin difficulty_rating first_hint_progress"),
    "practice_item_snapshots": (
        "content_hash practice_item_id created_at",
        "item_json"),
    "practice_item_state": (
        "practice_item_id difficulty stability retrievability due_at active content_hash last_attempt_at "
        "updated_at",
        ""),
    "probe_episodes": (
        "id learning_object_id status hypothesis_set_id active_state_segment_id "
        "minimum_independent_observations maximum_observations entered_at completed_at algorithm_version "
        "created_at updated_at origin target_contract_version_id target_support_hash calibration_model_id "
        "calibration_model_hash probe_mapping_version",
        "trigger target_decision_json required_facets_json completion_reason completion_posterior_json "
        "completion_detail_json"),
    "probe_generation_needs": (
        "id probe_episode_id learning_object_id target_key status created_at resolved_at",
        "missing_capability"),
    "probe_item_family_links": (
        "practice_item_id instrument_card_id instrument_card_version generator_id generator_version "
        "generation_seed created_at",
        "instance_metadata_json"),
    "probe_observations": (
        "id attempt_id entropy_before entropy_after realized_information_gain "
        "independent_evidence_discount updates_belief eligible_for_completion created_at",
        "posterior_before_json posterior_after_json contamination_json grader_channel_json features_json"),
    "probe_presentations": (
        "id probe_episode_id practice_item_id scheduler_candidate_id state_segment_id "
        "probe_family_template_id probe_family_template_version instrument_card_id "
        "instrument_card_version entropy_at_selection expected_information_gain selection_policy_version "
        "status served_at submitted_at expires_at ended_at created_at updated_at",
        "instrument_card_snapshot_json target_hypothesis_pairs_json target_facets_json "
        "posterior_at_selection_json end_reason selection_components_json"),
    "proposed_patch_items": (
        "id proposed_patch_id client_item_id item_type operation target_entity_type target_entity_id "
        "decision validation_status applied_change_batch_id decided_at decided_by created_at updated_at "
        "source_ref_ids_json dependency_status",
        "payload_json edited_payload_json validation_errors_json audit_json dependency_block_reason_json"),
    "proposed_patches": (
        "id agent_run_id purpose status_cache created_at updated_at",
        "source_refs_json summary"),
    "question_events": (
        "id note_id practice_item_id attempt_id session_id question_type hint_equivalent leak_suspected "
        "rating seconds_into_attempt provider created_at answer_status saved_note_id scaffold_level "
        "learner_mode hints_used_before direct_explanation_request leak_overlap remediation_episode_id "
        "assessment_contract_version_id answered_at answer_mode",
        "context question_md answer_md facets_json preceding_tutor_move warning_state "
        "question_opportunity attempt_progress signal_channel resolution source_context_json"),
    "question_promotions": (
        "question_event_id intent question_nature attempted_in_thread learner_claim_id intervention_need_id "
        "proposed_patch_id saved_note_id existing_practice_item_id created_practice_item_id "
        "created_learning_object_id route created_at updated_at",
        "attributed_facets_json"),
    "queue_state": (
        "singleton revision updated_at",
        ""),
    "raw_grade_events": (
        "id administration_id observation_id attempt_id role grading_prompt_version "
        "grader_output_schema_version grader_identity_hash agent_run_id model_confidence "
        "response_classifier_version criterion_classifier_version exact_word_count predecessor_event_id "
        "created_at",
        "response_ref grader_provider grader_model_revision raw_output_json criterion_evidence_json "
        "observed_class confidence_bucket criterion_observed_classes_json context_features_json "
        "declared_length_bucket"),
    "reader_authored_questions": (
        "id extraction_id section_id source_id span_ids_json prompt_version provider model status "
        "answered_at practice_item_id created_at updated_at scope_kind anchor_span_ids_json "
        "inquiry_root_event_id",
        "question_md expected_answer_md response_md question_style self_check answer_basis"),
    "reader_cue_impressions": (
        "id cue_id link_id extraction_id span_id learning_object_id kind visit_id shown suppressed_reason "
        "propensity seed p_open p_open_source density response created_at responded_at response_text_hash",
        ""),
    "reader_path_depths": (
        "id source_id depth created_at",
        ""),
    "reader_path_sections": (
        "id extraction_id depth section_id label learner_override exercise_span_id ledger_id state_key model "
        "prompt_version created_at",
        "reason"),
    "reader_section_progress": (
        "extraction_id section_id spans_seen span_count revealed_at completed_at generation_batch_id "
        "updated_at",
        ""),
    "section_coverage": (
        "id extraction_id section_id learning_object_id treatment origin candidate_rank learner_override "
        "section_hash lo_hash state_key ledger_id model prompt_version created_at",
        "roles_json assumes_json notation_md learner_text"),
    "reveal_events": (
        "id practice_item_id learning_object_id remediation_episode_id source_kind amount "
        "question_event_id attempt_id created_at",
        "basis"),
    "rung_variant_requests": (
        "id source_practice_item_id learning_object_id status attempt_id learner_claim_id batch_id "
        "patch_id created_practice_item_id created_at updated_at variant_kind",
        "direction source_waypoint_slug target_waypoint_slug target_rung_json failure_reason"),
    "scheduler_slate_candidates": (
        "id slate_id practice_item_id learning_object_id rank returned_rank was_returned "
        "chosen_attempt_id selected_mode priority selection_reward predicted_correctness legacy_priority "
        "expected_information_gain readiness_factor algorithm_version created_at chosen_at "
        "selection_propensity exploration_flag selection_temperature propensity_kind",
        "components_json reward_debug_json target_scope_json plain_english_json"),
    # The offer's candidate ids are a JSON list of ids; its entry surface is classified as
    # ``submission_intents``' is.
    "scheduler_offer_receipts": (
        "slate_id returned_candidate_ids_json collection_version created_at",
        "entry_surface"),
    "schema_migrations": (
        "version name applied_at",
        ""),
    "source_artifacts": (
        "id acquisition_kind canonical_uri work_id current_revision_id created_at updated_at "
        "display_title reader_enabled keep_local",
        ""),
    "source_document_assets": (
        "id extraction_id media_type content_hash path page neighboring_span_ids_json",
        "caption geometry_json"),
    "source_document_blocks": (
        "extraction_id span_id extractor_block_id block_type page content_hash asset_ids_json ordinal",
        "role_hint bbox_json polygon_json section_path_json text"),
    "source_document_units": (
        "extraction_id unit_id parent_unit_id ordinal semantic_hash page_start page_end span_ids_json",
        "label locator_json"),
    "source_exposure_events": (
        "id extraction_id span_id revision_id source_id entity_type entity_id page created_at",
        "context locator section_path_json"),
    # A run's health counts its blocks by page and type, and its result hash digests the whole
    # reading, withheld blocks included (round 7's audit): counts and a hash, metadata by the
    # round-5 rule, never consumed by AD (the projection recomputes the IR's health from visible
    # blocks). Refusing them would refuse every ``SELECT *`` of a run (the alias computation's).
    "source_extraction_runs": (
        "id revision_id parent_extraction_id extractor extractor_version model_versions_json config_json "
        "page_selection_json ir_schema_version extraction_request_hash extraction_result_hash status "
        "created_at completed_at health_json",
        ""),
    "source_held_out_signal_marks": (
        "id revision_id extraction_id unit_id inventory_id made_as_role span_ids_json created_at",
        ""),
    "source_revisions": (
        "id source_id asset_hash note_id original_uri retrieved_at supersedes_revision_id created_at",
        ""),
    "source_service_spend": (
        "id envelope day reserved_usd charged_usd state legacy process lease_expires_at resolved_by "
        "created_at updated_at",
        ""),
    "source_span_reanchors": (
        "from_extraction_id from_span_id to_extraction_id to_span_id match_kind confidence created_at",
        ""),
    "source_unit_selections": (
        "extraction_id source_id revision_id selected_unit_ids_json boundary_overrides_json "
        "needs_review_json created_at updated_at exam_use_modes_json role_override",
        "exam_paper_metadata_json"),
    "sqlite_master": (
        "type name tbl_name rootpage sql",
        ""),
    "sqlite_temp_master": (
        "type name tbl_name rootpage sql",
        ""),
    "submission_intents": (
        "submission_id session_id practice_item_id scheduler_candidate_id viewing_status "
        "collection_version created_at",
        "entry_surface"),
    "task_feature_schema_versions": (
        "id schema_slug version dimensions_json content_hash created_at",
        ""),
    "trace_exercised_facets": (
        "id attempt_id facet_id role criterion_id source agent_run_id grading_prompt_version created_at",
        "observation_scope evidence"),
    "unresolved_cause_factors": (
        "id attempt_id observation_id status resolution_observation_ids_json algorithm_version created_at "
        "updated_at resolution_kind",
        "candidate_causes_json resolution_detail_json"),
}

CLASSES: Mapping[str, Mapping[str, str]] = MappingProxyType({
    table: MappingProxyType({**{column: METADATA for column in metadata.split()},
                             **{column: CONTENT for column in content.split()}})
    for table, (metadata, content) in _CLASSES.items()
})


def column_class(table: str, column: str | None) -> str:
    """A column's class. A read naming no column (``COUNT(*)``: SQLite passes an empty name) and
    ``rowid`` are metadata; an unclassified column is content (fail closed)."""

    if not column or column.lower() in ("rowid", "_rowid_", "oid"):
        return METADATA
    return CLASSES.get(table, {}).get(column, CONTENT)


__all__ = ["CLASSES", "CONTENT", "METADATA", "column_class"]

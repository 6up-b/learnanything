"""The AD guard's table registry (the AD23 redesign, step 2; ``operation`` enforces it).

Every table an AD operation can reach is classified here, by name, never by pattern (as
``db.table_roles`` does for rebuild policy):

* ``NEUTRAL``: carries no protected material and no state derived from it (schema, job and model
  accounting, plan scaffolding, source metadata, the learner's own claims). Read freely.
* ``PROTECTED``: rows can name a protected entity (an item, a revision, a span, an extraction, a
  note, an attempt...). Read only by the rules (the material view's readers), which withhold a row
  any of whose references resolves to a withheld entity.
* ``PREDICATE``: the held-out predicate's own inputs (unit selections, held-out marks, exam pools
  and reservations). Read only while the predicate is computed.
* ``DENIED``: the incumbent's state derived from every answer, protected ones included (mastery,
  scheduling and probe state, diagnosis, recurrence). Never read inside an operation, except by its
  named carve-out (:data:`CARVE_OUTS`: AD1's ``mastery_ekf`` comparator) or by the rules, which read
  an incumbent table only to hand AD the part the view allows (the item states' lifecycle).

Writes inside an operation go only to :data:`AD_WRITABLE`.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

NEUTRAL = "neutral"
PROTECTED = "protected"
PREDICATE = "predicate"
DENIED = "denied"
#: The scope name of the incumbent's serve-time constraints (``operation.incumbent_constraints``).
INCUMBENT = "incumbent"

_ROLES: tuple[tuple[str, str], ...] = (
    ("activity_administrations", PROTECTED),
    ("activity_card_versions", PROTECTED),
    ("activity_cards", PROTECTED),
    ("activity_exposure_events", PROTECTED),
    ("activity_families", NEUTRAL),
    ("activity_family_membership_events", PROTECTED),
    ("activity_family_versions", NEUTRAL),
    ("activity_observations", PROTECTED),
    ("activity_surface_lifecycle_events", PROTECTED),
    ("activity_surface_reservations", PREDICATE),
    ("activity_surfaces", PROTECTED),
    ("ad_attempt_trace", PROTECTED),
    ("ad_commission_results", PROTECTED),
    ("ad_coupling_versions", PROTECTED),
    ("ad_dose_offers", PROTECTED),
    ("ad_reading_opportunities", PROTECTED),
    ("ad_relatedness_runs", PROTECTED),
    ("ad_selections", PROTECTED),
    ("ad_state", PROTECTED),
    ("agent_runs", NEUTRAL),
    ("assessment_contract_versions", NEUTRAL),
    ("attempt_diagnoses", DENIED),
    ("attention_block_events", PROTECTED),
    ("attention_blocks", NEUTRAL),
    ("blind_grade_records", DENIED),
    ("capability_aliases", NEUTRAL),
    ("causal_activity_classification_events", PROTECTED),
    ("causal_hypotheses", DENIED),
    ("commitment_events", DENIED),
    ("commitment_target_versions", DENIED),
    ("commitment_versions", DENIED),
    ("commitments", DENIED),
    ("composed_selector_telemetry_horizons", DENIED),
    ("controller_ownership", DENIED),
    ("daily_plans", NEUTRAL),
    ("decision_features", PROTECTED),
    ("derived_state_rebuilds", NEUTRAL),
    ("diagnosis_context_receipts", DENIED),
    ("diagnosis_feedback", DENIED),
    ("entity_source_links", PROTECTED),
    ("error_events", DENIED),
    ("exam_pool_items", PREDICATE),
    ("facet_capability_evidence", DENIED),
    ("facet_identity_actions", NEUTRAL),
    ("facet_merges", NEUTRAL),
    ("facet_recall_state", DENIED),
    ("facet_registry_saves", NEUTRAL),
    ("fitted_parameters", DENIED),
    ("followup_tasks", PROTECTED),
    ("forecast_receipts", PROTECTED),
    ("grade_adjudications", PROTECTED),
    ("grade_interpretations", PROTECTED),
    ("grader_calibration_models", NEUTRAL),
    ("grading_evidence", PROTECTED),
    ("hypothesis_recurrence_groups", DENIED),
    ("hypothesis_recurrence_review", DENIED),
    ("hypothesis_recurrence_state", DENIED),
    ("ingest_batches", NEUTRAL),
    ("ingest_job_dependencies", NEUTRAL),
    ("ingest_jobs", NEUTRAL),
    ("interaction_events", PROTECTED),
    ("item_forecast_payloads", PROTECTED),
    ("item_forecast_scores", PROTECTED),
    ("item_parameter_state", DENIED),
    ("item_serve_inputs", PROTECTED),
    ("json_each", NEUTRAL),
    ("judgment_ledger", PROTECTED),
    ("judgment_work_claims", NEUTRAL),
    ("learner_claims", NEUTRAL),
    ("learning_object_mastery", DENIED),
    ("lo_probe_state", DENIED),
    ("measurement_contract_corrections", NEUTRAL),
    ("misconception_disposition_events", DENIED),
    ("misconceptions", DENIED),
    ("model_call_receipts", NEUTRAL),
    ("model_work_checkpoints", NEUTRAL),
    ("outcome_schema_versions", NEUTRAL),
    ("outcome_schemas", NEUTRAL),
    ("pf_candidates", PROTECTED),
    ("plan_presentations", PROTECTED),
    ("practice_attempts", PROTECTED),
    ("practice_item_snapshots", PROTECTED),
    ("practice_item_state", DENIED),
    ("probe_episodes", DENIED),
    ("probe_generation_needs", DENIED),
    ("probe_item_family_links", DENIED),
    ("probe_observations", DENIED),
    ("probe_presentations", PROTECTED),
    ("proposed_patch_items", PROTECTED),
    ("proposed_patches", NEUTRAL),
    ("question_events", PROTECTED),
    ("queue_state", NEUTRAL),
    ("raw_grade_events", PROTECTED),
    ("reader_authored_questions", PROTECTED),
    ("reader_section_progress", PROTECTED),
    ("reveal_events", PROTECTED),
    ("rung_variant_requests", PROTECTED),
    ("scheduler_slate_candidates", PROTECTED),
    ("schema_migrations", NEUTRAL),
    ("source_artifacts", NEUTRAL),
    ("source_document_assets", PROTECTED),
    ("source_document_blocks", PROTECTED),
    ("source_document_units", PROTECTED),
    ("source_exposure_events", PROTECTED),
    ("source_extraction_runs", NEUTRAL),
    ("source_held_out_signal_marks", PREDICATE),
    ("source_revisions", NEUTRAL),
    ("source_service_spend", NEUTRAL),
    ("source_span_reanchors", PROTECTED),
    ("source_unit_selections", PREDICATE),
    ("sqlite_master", NEUTRAL),
    ("sqlite_temp_master", NEUTRAL),
    ("submission_intents", PROTECTED),
    ("task_feature_schema_versions", NEUTRAL),
    ("trace_exercised_facets", DENIED),
    ("unresolved_cause_factors", DENIED),
)

ROLES: Mapping[str, str] = MappingProxyType(dict(_ROLES))
if len(ROLES) != len(_ROLES):  # pragma: no cover - a registry edit error
    raise RuntimeError("a table is classified twice in protected_tables")


def _table(refs: Mapping[str, str], *, values: str) -> Mapping[str, str]:
    return MappingProxyType({**dict(refs), **{column: VALUE for column in values.split()}})


VALUE = "value"

#: Every column of every PROTECTED table, classified (``tests/test_ad_protected_tables.py`` checks
#: the head schema against it: a migration adding a column fails until it is classified here).
#:
#: A column is a ``value`` (it names nothing the predicate can withhold) or a reference the material
#: view resolves (``material_view.MaterialView.keep``); a row is withheld when ANY reference resolves
#: to a withheld entity. The kinds:
#:
#: * ``item``, ``revision`` (a content hash), ``attempt``, ``presentation`` (a plan presentation),
#:   ``note``, ``reader_question``, ``question_event``, ``facet`` (withheld when only withheld material
#:   names it), ``dose_draw``, ``selection``, ``receipt`` (a forecast receipt), ``administration`` and
#:   ``surface`` (through the surface's legacy item), ``extraction`` (a whole extraction held out);
#: * ``span@C``, ``section@C``, ``spans@C`` (a JSON list of spans): in the extraction column ``C``;
#: * ``entity@C``: polymorphic, by the kind named in column ``C`` (:data:`ENTITY_KINDS`);
#: * ``self``: the row's own identity, resolved by its table's rule (an attempt by the revisions it
#:   answered, a presentation by its frozen revision, a Reader question by its anchors and cited
#:   spans, a tutor question by its whole recorded source context, a saved revision by its own
#:   sources, a dose draw by its originating section and chosen extra);
#: * ``served_item@C``: an item, withheld also when its presentation in block ``C`` is (a
#:   selection's chosen and slot items: Codex verify F39);
#: * ``source@C``: a reading receipt's source row in table ``C``, resolved again now; a source since
#:   deleted leaves its frozen receipt standing (Codex verify F30's named exception);
#: * ``doses``: not a withholding reference: a receipt's doses drop the facets only withheld
#:   material names (the second named exception);
#: * ``dose_extra@C``: a dose draw's chosen extra (its question or its example span), by variant ``C``;
#: * ``plan_detail@C``: a plan block event's detail (its item, its attempt, its serve in block ``C``).
#:
#: A JSON column holding a draw's frame (a selection's support and exclusions, a receipt's inputs)
#: is a ``value``: it is recorded, never read back as a learner input, and the row stands or falls
#: by its references above.
COLUMNS: Mapping[str, Mapping[str, str]] = MappingProxyType({
    "activity_administrations": _table({"surface_id": "surface"},
        values="id card_version_id family_id purpose administration_snapshot_hash snapshot_json "
               "target_contract_version_id target_support_hash grader_model_version_id selection_policy_version_id "
               "decision_params_hash assistance_json feedback_condition eligibility_json reservation_id "
               "legacy_backfilled created_at reading_phase admin_context_json"),
    "activity_card_versions": _table({},
        values="id card_id version card_contract_hash contract_json schema_version predecessor_card_version_id "
               "lineage_kind legacy_contract_version_id created_at"),
    "activity_cards": _table({},
        values="id family_id created_at"),
    "activity_exposure_events": _table({"surface_id": "surface", "administration_id": "administration"},
        values="id surface_hash fingerprint kind purpose consumes_unseen detail_json created_at"),
    "activity_family_membership_events": _table({"practice_item_id": "item"},
        values="seq id family_id card_id variant_relation action proposal_id judgment_id created_at"),
    "activity_observations": _table({
        "administration_id": "administration", "surface_id": "surface", "attempt_id": "attempt",
    },
        values="id response_ref active_interpretation_id evidence_eligibility eligibility_reason created_at"),
    "activity_surface_lifecycle_events": _table({"surface_id": "surface", "administration_id": "administration"},
        values="id reservation_id kind reason detail_json created_at"),
    "activity_surfaces": _table({"legacy_practice_item_id": "item"},
        values="id card_version_id surface_hash fingerprint surface_json legacy_surface_unverifiable created_at"),
    "ad_attempt_trace": _table({"attempt_id": "attempt"},
        values="view input_status category prior_mean prior_var post_mean post_var p_categories_json information "
               "points_json detail_json"),
    "ad_commission_results": _table({
        "selection_id": "selection", "practice_item_id": "item", "content_hash": "revision",
    },
        values="id features_json p_bar status state_hash landed_after_expiry features_match created_at"),
    "ad_coupling_versions": _table({},
        values="id subject_id version coupling_version run_ids_json adopted_by note adopted_at"),
    "ad_dose_offers": _table({
        "id": "self", "row_kind": "self", "extraction_id": "self", "section_id": "self", "chosen_variant": "self",
        "content_json": "self", "draw_id": "dose_draw",
    },
        values="draw_key visit_id learning_object_ids_json feasible_json infeasible_json base_version floor "
               "propensities_json seed u forecast_p detail_json created_at"),
    "ad_reading_opportunities": _table({
        "source_id": "source@source_table", "facet_doses_json": "doses", "dose_offer_id": "dose_draw",
    },
        values="id opportunity_key kind subkind source_table source_written_at learning_object_id mapping_version "
               "authority_class sweep sweep_ref swept_at"),
    "ad_relatedness_runs": _table({},
        values="id run_key subject_id input_hash units_json judgment_ids_json status prompt_version judge_model "
               "created_at"),
    "ad_selections": _table({
        "chosen_item_id": "served_item@block_id", "slot_item_id": "served_item@block_id", "cell_facet": "facet",
    },
        values="id decision_key kind view learning_object_id cell_capability daily_plan_id block_id slot_position "
               "mode support_json excluded_json constants_json seed u chosen_point_json propensity "
               "router_decision_id router_propensity pair_propensity empty_support state_hash versions_json "
               "algorithm_version generating_job_id created_at"),
    "ad_state": _table({},
        values="view part payload_json state_hash as_of versions_json"),
    "attention_block_events": _table({"detail_json": "plan_detail@block_id"},
        values="id block_id event_ordinal kind created_at"),
    "causal_activity_classification_events": _table({"attempt_id": "attempt"},
        values="id seq contamination_class near_clone near_clone_basis closes_pre_intervention_segment "
               "eligible_for_fsrs eligible_for_certification source policy_version detail_json created_at"),
    "decision_features": _table({},
        values="id decision_id decision_type ability_vector_json item_demand_vector_json context_json "
               "algorithm_version created_at"),
    "entity_source_links": _table({"entity_id": "entity@entity_type", "extraction_id": "extraction"},
        values="id entity_type source_id revision_id locator locator_scheme relation asset_hash span_hash patch_id "
               "status stale_at superseded_by_link_id created_at"),
    "followup_tasks": _table({
        "source_attempt_id": "attempt", "selected_item_id": "item", "consumed_attempt_id": "attempt",
    },
        values="id kind case_kind case_ref remediation_episode_id not_before expires_at status context_json "
               "learning_object_id created_at updated_at measurement_opportunity_id"),
    "forecast_receipts": _table({
        "source_attempt_id": "attempt", "practice_item_id": "item", "item_content_hash": "revision",
        "plan_presentation_id": "presentation", "facet_id": "facet",
    },
        values="id receipt_key kind forecaster forecaster_version scope decision_kind decision_ref "
               "learning_object_id hypothesis_ref binding_kind probe_presentation_id followup_task_id "
               "scheduler_candidate_id censor_reason event p forecast_json inputs_json inputs_hash inputs_as_of "
               "parameters_json versions_json status algorithm_version created_at received_at"),
    "grade_adjudications": _table({"administration_id": "administration"},
        values="id observation_id reviewed_raw_event_ids_json adjudicator_source resolved_class "
               "resolved_distribution_json rationale provenance_json bounded_trust_weight "
               "resulting_interpretation_id superseded_adjudication_id created_at"),
    "grade_interpretations": _table({"administration_id": "administration"},
        values="id raw_grade_event_id observation_id calibration_model_id calibration_model_hash "
               "projection_algorithm_version channel_posterior_snapshot_id response_posterior_json "
               "criterion_posteriors_json reference_prior_ids_json certainty_discount credible_interval_json "
               "review_flag influence_flag quarantine_state fallback_reason created_at shared_certainty_lcb"),
    "grading_evidence": _table({"attempt_id": "attempt"},
        values="id criterion_id points_awarded evidence notes agent_run_id local_grader_id grader_tier created_at "
               "superseded_at superseded_by_evidence_id learner_confidence assessment_contract_version_id "
               "grading_revision observation_id recipe_id attribution_json correlation_group"),
    "interaction_events": _table({
        "administration_id": "administration", "surface_id": "surface", "attempt_id": "attempt",
        "subject_id": "entity@subject_type",
    },
        values="id kind subject_type affect_tap_kind attempt_duration_ms payload_json origin created_at occurred_at "
               "received_at actor client_id session_id visit_id payload_schema_version source_id revision_id "
               "render_view_id locator_json annotation_id commitment_id activity_id payload_hash "
               "client_idempotency_key privacy_locality consent_context producer_version app_version policy_version "
               "supersedes_event_id"),
    "item_forecast_payloads": _table({"content_hash": "revision"},
        values="id owner_key forecaster kind content_json created_at"),
    "item_forecast_scores": _table({
        "receipt_id": "receipt", "practice_item_id": "item", "plan_presentation_id": "presentation",
        "attempt_id": "attempt",
    },
        values="forecaster p outcome status log_loss brier first_attempt_lo first_surface_cell capability "
               "detail_json"),
    "item_serve_inputs": _table({
        "plan_presentation_id": "presentation", "practice_item_id": "item", "content_hash": "revision",
    },
        values="id receipt_key presentation_kind probe_presentation_id scheduler_candidate_id learning_object_id "
               "served_at stamped_features_json task_feature_schema audit_json resolved_features_json signals_json "
               "z_v1_recalibration pre_exposed resolution_version loadings_json coupling_version created_at"),
    "judgment_ledger": _table({"left_id": "entity@left_kind", "right_id": "entity@right_kind"},
        values="id created_at supersedes_id task left_kind right_kind judge judge_model prompt_version input_hash "
               "verdict score rationale"),
    "pf_candidates": _table({"parent_item_id": "item", "published_item_id": "item", "content_hash": "revision"},
        values="id run_id mint_request_id round tier family_id learning_object_id generation_path declared_relation "
               "final_relation proposer_model prompt_version payload_json verification verification_check status "
               "rejection_filter filters_json difficulty difficulty_source panel_json selection_json cost_json "
               "judged_inputs_json published_at created_at updated_at"),
    "plan_presentations": _table({"id": "self", "practice_item_id": "self"},
        values="block_id router_decision_id controller_decision_id position origin scheduler_candidate_id "
               "probe_presentation_id session_id served_at"),
    "practice_attempts": _table({"id": "self", "practice_item_id": "self", "plan_presentation_id": "self"},
        values="learning_object_id subject concept practice_mode attempt_type learner_answer_md evidence_facets_json "
               "evidence_weights_json rubric_score correctness confidence latency_seconds hints_used error_type "
               "grader_confidence manual_review manual_review_reason created_at updated_at session_id "
               "scheduler_slate_id scheduler_candidate_id primed probe_presentation_id answer_confidence "
               "submission_id declared_dont_know collection_version entry_surface evidence_origin declared_stuck "
               "reference_status difficulty_rating first_hint_progress"),
    "practice_item_snapshots": _table({"content_hash": "self", "item_json": "self", "practice_item_id": "item"},
        values="created_at"),
    "probe_presentations": _table({"practice_item_id": "item"},
        values="id probe_episode_id scheduler_candidate_id state_segment_id probe_family_template_id "
               "probe_family_template_version instrument_card_id instrument_card_version "
               "instrument_card_snapshot_json target_hypothesis_pairs_json target_facets_json "
               "posterior_at_selection_json entropy_at_selection expected_information_gain selection_policy_version "
               "status end_reason served_at submitted_at expires_at ended_at created_at updated_at "
               "selection_components_json"),
    "proposed_patch_items": _table({"target_entity_id": "entity@target_entity_type"},
        values="id proposed_patch_id client_item_id item_type operation target_entity_type payload_json "
               "edited_payload_json decision validation_status validation_errors_json applied_change_batch_id "
               "decided_at decided_by created_at updated_at audit_json source_ref_ids_json dependency_status "
               "dependency_block_reason_json"),
    "question_events": _table({
        "id": "self", "note_id": "self", "practice_item_id": "self", "source_context_json": "self",
        "attempt_id": "attempt",
    },
        values="context session_id question_md answer_md question_type facets_json hint_equivalent leak_suspected "
               "rating seconds_into_attempt provider created_at answer_status saved_note_id preceding_tutor_move "
               "scaffold_level warning_state learner_mode question_opportunity hints_used_before "
               "direct_explanation_request attempt_progress signal_channel resolution leak_overlap "
               "remediation_episode_id assessment_contract_version_id answered_at answer_mode"),
    "raw_grade_events": _table({"administration_id": "administration", "attempt_id": "attempt"},
        values="id observation_id response_ref role grader_provider grader_model_revision grading_prompt_version "
               "grader_output_schema_version grader_identity_hash agent_run_id raw_output_json "
               "criterion_evidence_json observed_class model_confidence confidence_bucket "
               "criterion_observed_classes_json response_classifier_version criterion_classifier_version "
               "context_features_json exact_word_count declared_length_bucket predecessor_event_id created_at"),
    "reader_authored_questions": _table({
        "id": "self", "extraction_id": "self", "anchor_span_ids_json": "self", "span_ids_json": "self",
        "practice_item_id": "item",
    },
        values="section_id source_id question_md expected_answer_md prompt_version provider model status response_md "
               "answered_at created_at updated_at scope_kind question_style inquiry_root_event_id self_check "
               "answer_basis"),
    "reader_section_progress": _table({"extraction_id": "extraction", "section_id": "section@extraction_id"},
        values="spans_seen span_count revealed_at completed_at generation_batch_id updated_at"),
    "reveal_events": _table({
        "practice_item_id": "item", "attempt_id": "attempt", "question_event_id": "question_event",
    },
        values="id learning_object_id remediation_episode_id source_kind amount basis created_at"),
    "rung_variant_requests": _table({
        "source_practice_item_id": "item", "created_practice_item_id": "item", "attempt_id": "attempt",
    },
        values="id learning_object_id direction source_waypoint_slug target_waypoint_slug target_rung_json status "
               "learner_claim_id batch_id patch_id failure_reason created_at updated_at variant_kind"),
    "scheduler_slate_candidates": _table({"practice_item_id": "item", "chosen_attempt_id": "attempt"},
        values="id slate_id learning_object_id rank returned_rank was_returned selected_mode priority "
               "selection_reward predicted_correctness legacy_priority expected_information_gain readiness_factor "
               "components_json reward_debug_json target_scope_json plain_english_json algorithm_version created_at "
               "chosen_at selection_propensity exploration_flag selection_temperature propensity_kind"),
    "source_document_assets": _table({
        "extraction_id": "extraction", "neighboring_span_ids_json": "spans@extraction_id",
    },
        values="id media_type content_hash path caption page geometry_json"),
    "source_document_blocks": _table({"extraction_id": "extraction", "span_id": "span@extraction_id"},
        values="extractor_block_id block_type role_hint page bbox_json polygon_json section_path_json text "
               "content_hash asset_ids_json ordinal"),
    "source_document_units": _table({"extraction_id": "extraction", "span_ids_json": "spans@extraction_id"},
        values="unit_id parent_unit_id label ordinal locator_json semantic_hash page_start page_end"),
    "source_exposure_events": _table({
        "extraction_id": "extraction", "span_id": "span@extraction_id", "entity_id": "entity@entity_type",
    },
        values="id context revision_id source_id entity_type page locator section_path_json created_at"),
    "source_span_reanchors": _table({
        "from_extraction_id": "extraction", "from_span_id": "span@from_extraction_id",
        "to_extraction_id": "extraction", "to_span_id": "span@to_extraction_id",
    }, values="match_kind confidence created_at"),
    "submission_intents": _table({"practice_item_id": "item"},
        values="submission_id session_id scheduler_candidate_id entry_surface viewing_status collection_version "
               "created_at"),
})

#: The polymorphic entity kinds (entity@C): a kind not listed names nothing withheld.
ENTITY_KINDS: Mapping[str, str] = MappingProxyType({
    "attempt": "attempt",
    "extraction": "extraction",
    "facet": "facet",
    "note": "note",
    "plan_presentation": "presentation",
    "practice_item": "item",
    "practice_item_revision": "revision",
    "question_event": "question_event",
    "reader_authored_question": "reader_question",
    "source_note": "note",
})

#: The incumbent's serve-time constraints AD's slot asks of a visible candidate (would the incumbent
#: serve it now: the routine and out-of-timing exclusions, the staged frame's admission on a fresh
#: controller snapshot). Read only in the operation's ``incumbent_constraints()`` scope, only by these
#: modules, never written; what reaches AD is a pass or a named refusal per visible candidate. Named,
#: not closed (the AD23 redesign's boundary list): the incumbent's own state is what it constrains with.
INCUMBENT_READERS = frozenset({
    "learnloop.content.sources.exam_material",
    "learnloop.daily_plan.staged_frame",
    "learnloop.goals.exam_pool",
    "learnloop.placement.state",
    "learnloop.scheduling.constraint_engine",
    "learnloop.scheduling.controller_ownership",
    "learnloop.scheduling.controller_snapshot",
    "learnloop.scheduling.controller_store",
    "learnloop.scheduling.serving_exclusions",
})

#: Tables an operation may write: AD's own, and the receipts and accounting its jobs write.
AD_WRITABLE = frozenset({
    "ad_attempt_trace", "ad_commission_results", "ad_coupling_versions", "ad_dose_offers",
    "ad_reading_opportunities", "ad_relatedness_runs", "ad_selections", "ad_state", "forecast_receipts",
    "item_forecast_payloads", "item_forecast_scores", "item_serve_inputs", "judgment_ledger",
    "judgment_work_claims", "model_call_receipts", "model_work_checkpoints", "practice_item_snapshots",
    "source_service_spend",
})

#: The named carve-outs: a DENIED table a named AD module may read (on the stack of the read).
#: ``mastery_ekf`` is the incumbent's live forecast, which AD1 records as its comparator (round 9's
#: recorded boundary, kept by the round-10 verify's judgment (c) and by the redesign).
CARVE_OUTS: Mapping[str, frozenset[str]] = MappingProxyType({
    "learning_object_mastery": frozenset({"learnloop.adaptive_difficulty.forecasters"}),
    "item_parameter_state": frozenset({"learnloop.adaptive_difficulty.forecasters"}),
    "practice_item_state": frozenset({"learnloop.adaptive_difficulty.forecasters"}),
    "probe_episodes": frozenset({"learnloop.adaptive_difficulty.forecasters"}),
    "probe_observations": frozenset({"learnloop.adaptive_difficulty.forecasters"}),
})

_WHY = {PROTECTED: "a protected table read outside the rules",
        PREDICATE: "the predicate's input read outside the predicate",
        DENIED: "the incumbent's derived state read inside an AD operation"}


def role(table: str) -> str | None:
    return ROLES.get(table)


def read_verdict(table: str, *, rules: str | None, reader: str = "", stack: tuple[str, ...] = ()) -> str | None:
    """None when the read is allowed, else why it is refused."""

    kind = ROLES.get(table)
    if kind == NEUTRAL:
        return None
    if kind is None:
        return "an unclassified table"
    if rules == INCUMBENT:
        return None if reader in INCUMBENT_READERS else "a read in the incumbent's scope by another module"
    if kind == PREDICATE:
        return None if rules == "predicate" else _WHY[kind]
    if rules is not None:
        return None
    if any(module in CARVE_OUTS.get(table, ()) for module in stack):
        return None
    return _WHY[kind]


def write_verdict(table: str) -> str | None:
    if table in AD_WRITABLE or table.startswith("sqlite_"):
        return None
    return "a write to a table AD does not own"


__all__ = ["AD_WRITABLE", "CARVE_OUTS", "COLUMNS", "DENIED", "ENTITY_KINDS", "INCUMBENT", "INCUMBENT_READERS",
           "NEUTRAL", "PREDICATE", "PROTECTED", "ROLES", "VALUE", "read_verdict", "role", "write_verdict"]

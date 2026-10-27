"""The AD guard's table registry (the AD23 redesign, step 2; ``operation`` enforces it).

Every table an AD operation can reach is classified here, by name, never by pattern (as
``db.table_roles`` does for rebuild policy):

* ``NEUTRAL``: carries no protected material and no state derived from it (schema, job and model
  accounting, plan scaffolding, source metadata, the learner's own claims). Its METADATA columns are
  read freely; its content columns (a model call's prompt and output, an assessment contract's
  question and answer) only by the rules (``column_classes``, the AD23 redesign round 5).
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

_ROLES: tuple[tuple[str, str], ...] = (
    ("activity_administrations", PROTECTED),
    ("activity_card_versions", DENIED),
    ("activity_cards", DENIED),
    ("activity_exposure_events", DENIED),
    ("activity_families", NEUTRAL),
    ("activity_family_membership_events", PROTECTED),
    ("activity_family_versions", NEUTRAL),
    ("activity_observations", DENIED),
    ("activity_surface_lifecycle_events", DENIED),
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
    ("assumption_decisions", DENIED),
    ("assumption_returns", DENIED),
    ("attempt_diagnoses", DENIED),
    ("attention_block_events", PROTECTED),
    ("attention_blocks", NEUTRAL),
    ("blind_grade_records", DENIED),
    ("capability_aliases", NEUTRAL),
    ("causal_activity_classification_events", DENIED),
    ("causal_hypotheses", DENIED),
    ("commitment_events", DENIED),
    ("commitment_target_versions", DENIED),
    ("commitment_versions", DENIED),
    ("commitments", DENIED),
    ("composed_selector_telemetry_horizons", DENIED),
    ("controller_ownership", DENIED),
    ("daily_plans", NEUTRAL),
    ("decision_features", DENIED),
    ("depth_envelope_versions", NEUTRAL),
    ("depth_policy_versions", NEUTRAL),
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
    ("figure_predictions", PROTECTED),
    ("fitted_parameters", DENIED),
    ("followup_tasks", DENIED),
    ("forecast_receipts", PROTECTED),
    ("grade_adjudications", DENIED),
    ("grade_interpretations", DENIED),
    ("grader_calibration_models", NEUTRAL),
    ("grading_evidence", DENIED),
    ("hypothesis_recurrence_groups", DENIED),
    ("hypothesis_recurrence_review", DENIED),
    ("hypothesis_recurrence_state", DENIED),
    ("ingest_batches", NEUTRAL),
    ("ingest_job_dependencies", NEUTRAL),
    ("ingest_jobs", NEUTRAL),
    ("interaction_events", PROTECTED),
    ("interactive_figures", PROTECTED),
    ("item_forecast_payloads", PROTECTED),
    ("item_forecast_scores", PROTECTED),
    ("item_parameter_state", DENIED),
    ("item_serve_inputs", PROTECTED),
    ("json_each", NEUTRAL),
    ("judgment_ledger", PROTECTED),
    ("judgment_work_claims", NEUTRAL),
    ("learner_claims", NEUTRAL),
    ("learner_gap_check_advances", DENIED),
    ("learner_gap_commitments", DENIED),
    ("learner_text_gap_reversals", DENIED),
    ("learning_object_mastery", DENIED),
    ("lo_probe_state", DENIED),
    ("measurement_contract_corrections", NEUTRAL),
    ("misconception_disposition_events", DENIED),
    ("misconceptions", DENIED),
    ("model_call_receipts", NEUTRAL),
    ("model_work_checkpoints", NEUTRAL),
    ("outcome_schema_versions", NEUTRAL),
    ("outcome_schemas", NEUTRAL),
    ("passage_links", PROTECTED),
    ("pf_candidates", PROTECTED),
    ("plan_presentations", PROTECTED),
    ("practice_attempts", PROTECTED),
    ("practice_item_snapshots", PROTECTED),
    ("practice_item_state", DENIED),
    ("probe_episodes", DENIED),
    ("probe_generation_needs", DENIED),
    ("probe_item_family_links", DENIED),
    ("probe_observations", DENIED),
    ("probe_presentations", DENIED),
    ("proposed_patch_items", PROTECTED),
    ("proposed_patches", NEUTRAL),
    ("question_events", PROTECTED),
    ("question_promotions", DENIED),
    ("queue_state", NEUTRAL),
    ("raw_grade_events", DENIED),
    ("reader_authored_questions", PROTECTED),
    ("reader_cue_impressions", PROTECTED),
    ("reader_path_depths", NEUTRAL),
    ("reader_path_sections", PROTECTED),
    ("reader_section_progress", PROTECTED),
    ("reveal_events", PROTECTED),
    ("rung_variant_requests", DENIED),
    ("scheduler_slate_candidates", DENIED),
    # The incumbent scheduler's published offer (migration 161): which of a slate's candidates the
    # learner was shown. Field's serving attribution reads it, inside the rules, only to label an
    # attempt picked from that offer ``learner_pick`` (``field.outcomes._serving``); like its slate's
    # candidates it is the incumbent's serving state, never read raw (owner-vault upgrade blocker,
    # 2026-10-27: unclassified, it poisoned every AD operation over a vault with such an attempt).
    ("scheduler_offer_receipts", DENIED),
    ("schema_migrations", NEUTRAL),
    # Curriculum C0a (migration 222): a coverage row names a reading's section.
    ("section_coverage", PROTECTED),
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
    ("submission_intents", DENIED),
    ("task_feature_schema_versions", NEUTRAL),
    ("trace_exercised_facets", DENIED),
    ("unresolved_cause_factors", DENIED),
)

ROLES: Mapping[str, str] = MappingProxyType(dict(_ROLES))
if len(ROLES) != len(_ROLES):  # pragma: no cover - a registry edit error
    raise RuntimeError("a table is classified twice in protected_tables")


def _table(refs: Mapping[str, str], *, values: str, derived: str = "") -> Mapping[str, str]:
    return MappingProxyType({**dict(refs), **{column: VALUE for column in values.split()},
                             **{column: DERIVED for column in derived.split()}})


VALUE = "value"
#: A visible row's column whose stored value was DERIVED, at ingest or later, from OTHER rows'
#: content (the heading stack, a role from a heading, an order counting withheld blocks, a hash or
#: a count over a whole section, a normalizer judging a block by its neighbours): it can carry
#: withheld material although its row is visible (the AD23 redesign round 7). The guard refuses it
#: outside the derivation scope (``operation.rules("derive")``) and the rules never hand it out.
#: Since round 8 (Option B) the scope is entered only at the reading chokepoint, for a reading no
#: withheld block touches, whose stored structure is then derived from visible blocks alone
#: (:data:`DERIVED_TREATMENT`); the kind stays live as the guard's proof that no other reader exists.
DERIVED = "derived_by_position"

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
#: * ``epoch``: the protection epoch the row was computed under (an AD artefact's stamp,
#:   :data:`EPOCH`): a row of another epoch is, for AD, never written;
#: * ``dose_extra@C``: a dose draw's chosen extra (its question or its example span), by variant ``C``;
#: * ``plan_detail@C``: a plan block event's detail (its item, its attempt, its serve in block ``C``);
#: * ``derived_by_position``: :data:`DERIVED` (a value derived from other rows; never read as stored);
#: * ``reading_payload``: a recorded event's payload or locator naming a reading (a Reader visit, a
#:   cue-density change): withheld when any reading it names is withheld (round 8, Option B).
#:
#: A JSON column holding a draw's frame (a selection's support and exclusions, a receipt's inputs)
#: is a ``value``: it is recorded, never read back as a learner input, and the row stands or falls
#: by its references above.
COLUMNS: Mapping[str, Mapping[str, str]] = MappingProxyType({
    "activity_administrations": _table({"id": "self", "surface_id": "surface"},
        values="card_version_id family_id purpose administration_snapshot_hash snapshot_json "
               "target_contract_version_id target_support_hash grader_model_version_id selection_policy_version_id "
               "decision_params_hash assistance_json feedback_condition eligibility_json reservation_id "
               "legacy_backfilled created_at reading_phase admin_context_json"),
    "activity_family_membership_events": _table({"practice_item_id": "item"},
        values="seq id family_id card_id variant_relation action proposal_id judgment_id created_at"),
    "activity_surfaces": _table({"id": "self", "legacy_practice_item_id": "item"},
        values="card_version_id surface_hash fingerprint surface_json legacy_surface_unverifiable created_at"),
    "ad_attempt_trace": _table({"attempt_id": "attempt"},
        values="view input_status category prior_mean prior_var post_mean post_var p_categories_json information "
               "points_json detail_json"),
    "ad_commission_results": _table({
        "selection_id": "selection", "practice_item_id": "item", "content_hash": "revision",
        "protection_epoch": "epoch",
    },
        values="id features_json p_bar status state_hash landed_after_expiry features_match created_at"),
    "ad_coupling_versions": _table({},
        values="id subject_id version coupling_version run_ids_json adopted_by note adopted_at"),
    "ad_dose_offers": _table({
        "id": "self", "row_kind": "self", "extraction_id": "self", "section_id": "self", "chosen_variant": "self",
        "content_json": "self", "draw_id": "dose_draw", "protection_epoch": "epoch",
    },
        values="draw_key visit_id learning_object_ids_json feasible_json infeasible_json base_version floor "
               "propensities_json seed u forecast_p detail_json created_at"),
    "ad_reading_opportunities": _table({
        "source_id": "source@source_table", "dose_offer_id": "dose_draw", "protection_epoch": "epoch",
    },
        values="id opportunity_key kind subkind source_table source_written_at learning_object_id facet_doses_json "
               "mapping_version "
               "authority_class sweep sweep_ref swept_at"),
    "ad_relatedness_runs": _table({},
        values="id run_key subject_id input_hash units_json judgment_ids_json status prompt_version judge_model "
               "created_at"),
    "ad_selections": _table({
        "chosen_item_id": "served_item@block_id", "slot_item_id": "served_item@block_id", "cell_facet": "facet",
        "protection_epoch": "epoch",
    },
        values="id decision_key kind view learning_object_id cell_capability daily_plan_id block_id slot_position "
               "mode support_json excluded_json constants_json seed u chosen_point_json propensity "
               "router_decision_id router_propensity pair_propensity empty_support state_hash versions_json "
               "algorithm_version generating_job_id created_at"),
    "ad_state": _table({},
        values="view part payload_json state_hash as_of versions_json"),
    "attention_block_events": _table({"detail_json": "plan_detail@block_id"},
        values="id block_id event_ordinal kind created_at"),
    "entity_source_links": _table({"entity_id": "entity@entity_type", "extraction_id": "extraction",
                                   "locator": "span@extraction_id"},
        values="id entity_type source_id revision_id locator_scheme relation asset_hash span_hash patch_id "
               "status stale_at superseded_by_link_id created_at"),
    "forecast_receipts": _table({
        "source_attempt_id": "attempt", "practice_item_id": "item", "item_content_hash": "revision",
        "plan_presentation_id": "presentation", "facet_id": "facet",
    },
        values="id receipt_key kind forecaster forecaster_version scope decision_kind decision_ref "
               "learning_object_id hypothesis_ref binding_kind probe_presentation_id followup_task_id "
               "scheduler_candidate_id censor_reason event p forecast_json inputs_json inputs_hash inputs_as_of "
               "parameters_json versions_json status algorithm_version created_at received_at"),
    "interaction_events": _table({
        "administration_id": "administration", "surface_id": "surface", "attempt_id": "attempt",
        "subject_id": "entity@subject_type", "payload_json": "reading_payload", "locator_json": "reading_payload",
    },
        values="id kind subject_type affect_tap_kind attempt_duration_ms origin created_at occurred_at "
               "received_at actor client_id session_id visit_id payload_schema_version source_id revision_id "
               "render_view_id annotation_id commitment_id activity_id payload_hash "
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
        "protection_epoch": "epoch",
    },
        values="id receipt_key presentation_kind probe_presentation_id scheduler_candidate_id learning_object_id "
               "served_at stamped_features_json task_feature_schema audit_json resolved_features_json signals_json "
               "z_v1_recalibration pre_exposed resolution_version loadings_json coupling_version created_at"),
    # Main's RW5a (migration 216; the compose round): a figure built over a reading's spans and the
    # learner's predictions on it are READING rows; the built spec and its check, from the spans sent
    # (a tutor or library figure can send spans of other readings), are never read as stored.
    "figure_predictions": _table({"extraction_id": "extraction"},
        values="id figure_id prediction_index learner_answer observed_json matched explanation_text created_at"),
    "interactive_figures": _table({
        "extraction_id": "extraction", "span_ids_json": "spans@extraction_id",
        "input_span_ids_json": "spans@extraction_id",
    },
        values="id region_json asset_id origin supersedes_id revision_note spec_version kind verification "
               "unsupported_kind model prompt_version input_hash created_at "
               # Reader RW5d P1 (migration 224): the request's id, the grounding mode, the tier
               # and P2b's reserved runtime columns name nothing the predicate withholds.
               "request_id grounding tier program_version engine_sha256 runtime_digest instrumented_sha256 "
               "media_file_name fuller_of_id checks_json",
        # The goal and the retrieved passages' keys (any reading, any source) are never read as stored.
        derived="spec_json verification_report_json goal_text input_span_keys_json"),
    "judgment_ledger": _table({"left_id": "entity@left_kind", "right_id": "entity@right_kind"},
        values="id created_at supersedes_id task left_kind right_kind judge judge_model prompt_version input_hash "
               "verdict score rationale"),
    # Main's RW3b (migration 215; the compose round): a cue is a reading's passage picked for one of
    # the incumbent's diagnosis targets (a recurrence group, a hypothesis, a misconception, a gap, a
    # demonstrated facet, an unchecked claim) and ranked against other passages: a READING row whose
    # target, ranks and judged roles are the incumbent's state and other readings, never read as stored.
    "passage_links": _table({"extraction_id": "extraction", "span_id": "span@extraction_id"},
        values="id quote ledger_id model prompt_version created_at",
        derived="target_kind target_id relation pick_rank ranks_json roles_json target_facets_json state_key"),
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
    "proposed_patch_items": _table({
        "target_entity_id": "entity@target_entity_type", "payload_json": "self", "edited_payload_json": "self",
        "item_type": "self", "source_ref_ids_json": "self",
    },
        values="id proposed_patch_id client_item_id operation target_entity_type decision validation_status validation_errors_json applied_change_batch_id "
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
    "reader_authored_questions": _table({
        "id": "self", "extraction_id": "self", "anchor_span_ids_json": "self", "span_ids_json": "self",
        "practice_item_id": "item",
    },
        values="section_id source_id question_md expected_answer_md prompt_version provider model status response_md "
               "answered_at created_at updated_at scope_kind question_style inquiry_root_event_id self_check "
               "answer_basis"),
    # RW3b's impressions: a READING row per visit and cue; the cue's target and its open-propensity
    # (the learner model's) and the holdout's draw are never read as stored.
    "reader_cue_impressions": _table({"extraction_id": "extraction", "span_id": "span@extraction_id"},
        values="id cue_id link_id visit_id shown seed response response_text_hash created_at responded_at",
        derived="kind learning_object_id suppressed_reason propensity p_open p_open_source density"),
    # Main's RW7a (migration 217; the compose round): the path judge's label per reading, depth and
    # learner state is a READING row; the label, its reason and the state key it was judged under
    # (the incumbent's learner state) are never read as stored.
    "reader_path_sections": _table({
        "extraction_id": "extraction", "section_id": "section@extraction_id", "exercise_span_id": "span@extraction_id",
    },
        values="id depth learner_override ledger_id model prompt_version created_at",
        derived="label reason state_key"),
    "reader_section_progress": _table({"extraction_id": "extraction", "section_id": "section@extraction_id"},
        values="revealed_at completed_at generation_batch_id updated_at", derived="spans_seen span_count"),
    # Curriculum C0a (migration 222): the coverage judge's treatment of one LO by one section is a
    # READING row; what the judge or the learner wrote and the hashes and keys it was judged under are
    # never read as stored (AD reads no coverage).
    "section_coverage": _table({"extraction_id": "extraction", "section_id": "section@extraction_id"},
        values="id learning_object_id origin learner_override ledger_id model prompt_version created_at",
        derived="treatment roles_json assumes_json notation_md candidate_rank learner_text section_hash lo_hash "
                "state_key"),
    "reveal_events": _table({
        "practice_item_id": "item", "attempt_id": "attempt", "question_event_id": "question_event",
    },
        values="id learning_object_id remediation_episode_id source_kind amount basis created_at"),
    "source_document_assets": _table({
        "extraction_id": "extraction", "neighboring_span_ids_json": "spans@extraction_id",
    },
        values="id media_type content_hash path caption page geometry_json"),
    "source_document_blocks": _table({"extraction_id": "extraction", "span_id": "span@extraction_id"},
        values="block_type page bbox_json polygon_json asset_ids_json",
        derived="extractor_block_id role_hint section_path_json text content_hash ordinal"),
    "source_document_units": _table({"extraction_id": "extraction", "span_ids_json": "spans@extraction_id"},
        values="unit_id",
        derived="parent_unit_id label ordinal locator_json semantic_hash page_start page_end"),
    "source_exposure_events": _table({
        "extraction_id": "extraction", "span_id": "span@extraction_id", "entity_id": "entity@entity_type",
    },
        values="id context revision_id source_id entity_type page locator created_at", derived="section_path_json"),
    "source_span_reanchors": _table({
        "from_extraction_id": "extraction", "from_span_id": "span@from_extraction_id",
        "to_extraction_id": "extraction", "to_span_id": "span@to_extraction_id",
    }, values="match_kind confidence created_at"),
})

#: Every AD-owned artefact table (AD writes it and reads it back), and how its rows carry the
#: protection epoch they were computed under (the AD23 redesign round 2, class 3b). The rules read a
#: row only at the current epoch: a row of another epoch, or one recorded before rows carried one, is
#: absent to AD (ignored, expired, or recomputed and recorded again: a reading receipt is swept again
#: under the current projection). ``column:C``: the row's own column; ``json:C:K``: key ``K`` of the
#: JSON object in column ``C``; ``free: why``: nothing in it was computed from a projection.
#: ``tests/test_ad_protected_tables.py`` fails on an AD-owned table AD reads that has no rule.
EPOCH: Mapping[str, str] = MappingProxyType({
    "ad_attempt_trace": "free: DERIVED, rebuilt by the replayer from epoch-scoped inputs, never read by AD",
    "ad_commission_results": "column:protection_epoch",
    "ad_coupling_versions": "free: the owner's adoption of runs, each epoch-scoped (a run of another epoch "
                            "is out of force, so an adopted coupling resets with the epoch: E2)",
    "ad_dose_offers": "column:protection_epoch",
    "ad_reading_opportunities": "column:protection_epoch",
    "ad_relatedness_runs": "json:units_json:protection:epoch",
    "ad_selections": "column:protection_epoch",
    "ad_state": "free: DERIVED, rebuilt by the replayer from epoch-scoped inputs, never read by AD",
    "forecast_receipts": "json:versions_json:protection_epoch",
    "item_forecast_payloads": "json:content_json:protection_epoch",
    "item_forecast_scores": "free: DERIVED from epoch-scoped receipts, never read by AD",
    "item_serve_inputs": "column:protection_epoch",
    "judgment_ledger": "free: AD's judgments are of content (the feature audit), or read only through an "
                       "epoch-scoped relatedness run",
    "practice_item_snapshots": "free: a revision's own content, never computed from a projection",
})

#: The polymorphic entity kinds (``entity@C``): a kind not listed names nothing withheld.
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

#: There is no incumbent scope (the final round: inversion, owner decision 2026-10-24). The plan
#: computes its own verdicts about a slot before AD runs, outside any operation
#: (``daily_plan.slot_facts``), and AD reads them as a schema-checked facts record; incumbent code
#: called inside an operation has no privilege at all, so its reads of protected or denied tables
#: are refused and the operation is poisoned (fail closed).

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
})

#: How AD reads each :data:`DERIVED` column (the round-7 audit, revised by round 8's Option B):
#: ``chokepoint: ...`` (read as stored, inside ``rules("derive")``, only through the reading
#: chokepoint ``MaterialView.document_ir`` or the incumbent's role reader, and only for a reading no
#: withheld block touches; a reading the withheld material touches is absent) or ``unread: <why>``.
_CHOKEPOINT = ("chokepoint: read as stored only for a reading no withheld block touches, through "
               "MaterialView.document_ir (or role_keys); a reading the withheld material touches is absent")
DERIVED_TREATMENT: Mapping[tuple[str, str], str] = MappingProxyType({
    **{("source_document_blocks", column): _CHOKEPOINT for column in (
        "section_path_json", "role_hint", "ordinal", "extractor_block_id", "text", "content_hash")},
    **{("source_document_units", column): _CHOKEPOINT for column in (
        "parent_unit_id", "label", "ordinal", "locator_json", "semantic_hash", "page_start", "page_end")},
    ("source_exposure_events", "section_path_json"): "unread: the viewed block's stored path; AD maps an "
                                                     "exposure by its span through the reading chokepoint",
    ("reader_section_progress", "spans_seen"): "unread: counts over the section's spans; AD reads a "
                                               "section's completion only",
    ("reader_section_progress", "span_count"): "unread: counts over the section's spans; AD reads a "
                                               "section's completion only",
    # The compose round (main 558e85ab1): AD reads none of RW3b's, RW5a's or RW7a's tables.
    **{("interactive_figures", column): "unread: a model's figure from the spans sent, which can cite other "
                                        "readings; AD reads no figure" for column in (
        "spec_json", "verification_report_json", "goal_text", "input_span_keys_json")},
    **{("passage_links", column): "unread: the cue judge's pick for an incumbent diagnosis target, ranked "
                                  "against other passages; AD reads no cue" for column in (
        "target_kind", "target_id", "relation", "pick_rank", "ranks_json", "roles_json", "target_facets_json",
        "state_key")},
    **{("reader_cue_impressions", column): "unread: the cue's target and the learner model's open-propensity "
                                           "and the holdout's draw; AD reads no impression" for column in (
        "kind", "learning_object_id", "suppressed_reason", "propensity", "p_open", "p_open_source", "density")},
    **{("reader_path_sections", column): "unread: the path judge's label under the incumbent's learner state; "
                                         "AD reads no reading path" for column in ("label", "reason", "state_key")},
    # Curriculum C0a: AD reads no section coverage.
    **{("section_coverage", column): "unread: the coverage judge's (or the learner's) reading of a section "
                                     "against an LO, ranked among other readings' sections; AD reads no "
                                     "coverage" for column in (
        "treatment", "roles_json", "assumes_json", "notation_md", "candidate_rank", "learner_text",
        "section_hash", "lo_hash", "state_key")},
})

#: The READING tables (round 8, Option B): rows that describe a reading's structure or a reading
#: event on it. Their ``extraction``, ``span``, ``spans`` and ``section`` references resolve against
#: the READING (``MaterialView.reading_withheld``): a row of a reading the withheld material touches
#: is withheld, whatever block it names. Self-ruled reading tables apply the same rule in their own
#: rule (Reader questions, dose draws; a reading receipt by its source row). Two tables hold reading
#: events beside attempt evidence and apply it to their reading rows only (round 8 follow-up): a
#: tutor question asked in the Reader or the library (a practice or feedback one keeps the block
#: rule), and a Reader or library interaction event (any other kind's payload is a value).
READING = frozenset({
    "source_document_blocks", "source_document_units", "source_document_assets", "source_exposure_events",
    "reader_section_progress", "reader_authored_questions", "question_events", "source_span_reanchors",
    "ad_reading_opportunities", "ad_dose_offers", "interaction_events",
    # The compose round (main 558e85ab1): RW3b's cues and impressions, RW5a's figures and predictions,
    # RW7a's path labels (none is attempt evidence).
    "passage_links", "reader_cue_impressions", "interactive_figures", "figure_predictions", "reader_path_sections",
    # Curriculum C0a: section coverage (display and retrieval context, never attempt evidence).
    "section_coverage",
})
#: Tables with extraction-like references that are ITEM provenance, not reading: judged by the
#: withheld material itself, as before (an item's own sources), each with why.
ITEM_PROVENANCE: Mapping[str, str] = MappingProxyType({
    "entity_source_links": "an entity's (an item's, an LO's) own source citations: judged block by block",
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


__all__ = ["AD_WRITABLE", "CARVE_OUTS", "COLUMNS", "DENIED", "DERIVED", "DERIVED_TREATMENT", "ENTITY_KINDS", "EPOCH",
           "ITEM_PROVENANCE", "READING",
           "NEUTRAL", "PREDICATE", "PROTECTED", "ROLES", "VALUE", "read_verdict", "role", "write_verdict"]

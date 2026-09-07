"""Persistent-table roles for migration-head ``state.sqlite``.

The registry is deliberately explicit.  A schema migration which adds or
removes a user table must make the corresponding policy decision here; table
names are not classified by naming convention.

``RAW_LEDGER`` includes authoritative authored definitions, captured
provider/source output, measured calibration artifacts, and authoritative
state whose only replay input is co-located in the same row.  Those rows are
inputs to later computation and must never be cleared by the rebuild umbrella.
``RECEIPT`` is reserved for historical audit/decision artifacts, while mutable
queues, sessions, leases, and other in-flight lifecycle state are
``WORKFLOW``.  Only state intended to be cleared and recomputed is
``DERIVED``.  ``COMPAT`` tables are frozen legacy or abandoned seams retained
for existing vaults.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType


class TableRole(str, Enum):
    """The rebuild policy for one persistent user table."""

    RAW_LEDGER = "raw_ledger"
    DERIVED = "derived"
    RECEIPT = "receipt"
    WORKFLOW = "workflow"
    COMPAT = "compat"


# Keep this list alphabetical so schema diffs and review are mechanical.  An
# item list (rather than a dict literal) lets us reject an accidental duplicate
# instead of silently keeping the last declaration.
_TABLE_ROLE_ITEMS: tuple[tuple[str, TableRole], ...] = (
    ("ability_transition_events", TableRole.DERIVED),
    ("activity_administrations", TableRole.RAW_LEDGER),
    ("activity_card_authoring", TableRole.RAW_LEDGER),
    # The scheduling head and its only historical review stream are co-located
    # in projection_head_json.  Until that stream has its own ledger this is
    # authoritative captured state, not a clearable projection.
    ("activity_card_state", TableRole.RAW_LEDGER),
    ("activity_card_versions", TableRole.RAW_LEDGER),
    ("activity_cards", TableRole.RAW_LEDGER),
    ("activity_exposure_events", TableRole.RAW_LEDGER),
    ("activity_families", TableRole.RAW_LEDGER),
    ("activity_family_authoring", TableRole.RAW_LEDGER),
    ("activity_family_versions", TableRole.RAW_LEDGER),
    ("activity_observations", TableRole.RAW_LEDGER),
    ("activity_pattern_versions", TableRole.RAW_LEDGER),
    ("activity_patterns", TableRole.RAW_LEDGER),
    ("activity_surface_authoring", TableRole.RAW_LEDGER),
    ("activity_surface_lifecycle_events", TableRole.RECEIPT),
    ("activity_surface_reservations", TableRole.WORKFLOW),
    ("activity_surfaces", TableRole.RAW_LEDGER),
    ("agent_runs", TableRole.RECEIPT),
    ("angle_inventories", TableRole.RAW_LEDGER),
    ("apply_intents", TableRole.WORKFLOW),
    ("assessment_contract_versions", TableRole.RAW_LEDGER),
    # Carries immutable diagnosis/firewall receipts and recorded priming inputs
    # alongside the replay trace.  There is no external lossless source for the
    # receipt portion, so the table is an authoritative attempt artifact.
    ("attempt_debug_payloads", TableRole.RAW_LEDGER),
    ("attempt_feedback_metadata", TableRole.RAW_LEDGER),
    ("attempt_submission_receipts", TableRole.RECEIPT),
    ("attempt_surprise", TableRole.DERIVED),
    ("attention_block_events", TableRole.RECEIPT),
    ("attention_blocks", TableRole.WORKFLOW),
    ("calibration_stream_samples", TableRole.RAW_LEDGER),
    ("canonical_mapping_proposals", TableRole.WORKFLOW),
    ("capability_aliases", TableRole.RAW_LEDGER),
    ("capability_residual_state", TableRole.DERIVED),
    ("card_lineage_edges", TableRole.RAW_LEDGER),
    ("card_lineages", TableRole.RAW_LEDGER),
    ("causal_activity_classification_events", TableRole.RAW_LEDGER),
    ("causal_attribution_reports", TableRole.RECEIPT),
    ("causal_blind_prediction_bundles", TableRole.RECEIPT),
    ("causal_cold_outcomes", TableRole.RAW_LEDGER),
    ("causal_cold_verifications", TableRole.RAW_LEDGER),
    ("causal_discriminating_observations", TableRole.RAW_LEDGER),
    ("causal_hypotheses", TableRole.RAW_LEDGER),
    ("causal_machine_checks", TableRole.RECEIPT),
    ("causal_mechanism_taxonomy_assignments", TableRole.RAW_LEDGER),
    ("causal_mechanism_taxonomy_retirements", TableRole.RAW_LEDGER),
    ("causal_mechanism_taxonomy_versions", TableRole.RAW_LEDGER),
    ("causal_probe_candidate_events", TableRole.RECEIPT),
    ("causal_probe_candidates", TableRole.WORKFLOW),
    ("causal_probe_decision_receipts", TableRole.RECEIPT),
    ("causal_probe_preference_events", TableRole.RAW_LEDGER),
    ("causal_repair_class_definitions", TableRole.RAW_LEDGER),
    ("causal_shadow_selection_receipts", TableRole.RECEIPT),
    ("certification_cold_probe_outcomes", TableRole.RAW_LEDGER),
    ("change_batches", TableRole.WORKFLOW),
    ("cold_measurement_opportunities", TableRole.RECEIPT),
    ("cold_measurement_opportunity_decisions", TableRole.RECEIPT),
    ("coldness_receipts", TableRole.RECEIPT),
    ("commitment_arc_events", TableRole.RECEIPT),
    ("commitment_arc_versions", TableRole.RAW_LEDGER),
    ("commitment_arcs", TableRole.RAW_LEDGER),
    ("commitment_events", TableRole.RECEIPT),
    ("commitment_target_versions", TableRole.RAW_LEDGER),
    ("commitment_versions", TableRole.RAW_LEDGER),
    ("commitments", TableRole.RAW_LEDGER),
    ("composed_selector_telemetry_horizons", TableRole.WORKFLOW),
    ("concept_animations", TableRole.RAW_LEDGER),
    ("content_events", TableRole.RAW_LEDGER),
    ("contrast_pair_servings", TableRole.RECEIPT),
    ("controller_candidates", TableRole.WORKFLOW),
    ("controller_constraint_manifests", TableRole.RECEIPT),
    ("controller_decisions", TableRole.RECEIPT),
    ("controller_outcome_windows", TableRole.WORKFLOW),
    ("controller_ownership", TableRole.WORKFLOW),
    ("controller_ownership_events", TableRole.RECEIPT),
    ("controller_prequential_reports", TableRole.RECEIPT),
    ("controller_shadow_predictions", TableRole.RECEIPT),
    ("controller_snapshots", TableRole.RECEIPT),
    ("decision_features", TableRole.RECEIPT),
    ("depth_edge_instances", TableRole.RAW_LEDGER),
    ("depth_edge_template_versions", TableRole.RAW_LEDGER),
    ("depth_edge_templates", TableRole.RAW_LEDGER),
    ("depth_envelope_versions", TableRole.RAW_LEDGER),
    ("depth_milestone_versions", TableRole.RAW_LEDGER),
    ("depth_policy_versions", TableRole.RAW_LEDGER),
    ("derived_state_rebuilds", TableRole.RECEIPT),
    ("diagnosis_adjudications", TableRole.RAW_LEDGER),
    ("diagnostic_augmentation_receipts", TableRole.RECEIPT),
    ("diagnostic_eval_cases", TableRole.RAW_LEDGER),
    ("diagnostic_eval_runs", TableRole.RECEIPT),
    ("diagnostic_pack_cards", TableRole.RAW_LEDGER),
    ("diagnostic_pack_events", TableRole.RECEIPT),
    ("diagnostic_pack_pins", TableRole.RAW_LEDGER),
    ("diagnostic_packs", TableRole.RAW_LEDGER),
    ("diagnostic_surface_generation_needs", TableRole.WORKFLOW),
    ("discrimination_profile_matches", TableRole.RECEIPT),
    ("elicitation_events", TableRole.COMPAT),
    ("entity_source_links", TableRole.RAW_LEDGER),
    # Normalized per-attempt evidence; replay consumes the structured
    # attribution stored here because older grading rows do not contain it.
    ("error_events", TableRole.RAW_LEDGER),
    ("error_hunt_outcomes", TableRole.RECEIPT),
    ("evidence_facet_recall_state", TableRole.COMPAT),
    ("exam_answers", TableRole.RAW_LEDGER),
    ("exam_pool_items", TableRole.WORKFLOW),
    ("exam_predictions", TableRole.RECEIPT),
    ("exam_sessions", TableRole.WORKFLOW),
    ("facet_capability_evidence", TableRole.DERIVED),
    ("facet_merges", TableRole.RAW_LEDGER),
    ("facet_recall_state", TableRole.DERIVED),
    ("facet_uncertainty", TableRole.COMPAT),
    ("failure_triage_events", TableRole.RECEIPT),
    ("failure_triage_routes", TableRole.RAW_LEDGER),
    ("familiarity_kernel_events", TableRole.RECEIPT),
    ("familiarity_kernel_features", TableRole.RECEIPT),
    ("familiarity_kernel_models", TableRole.RAW_LEDGER),
    ("family_evidence_cap_policies", TableRole.RAW_LEDGER),
    ("fitted_parameters", TableRole.RAW_LEDGER),
    ("followup_ratings", TableRole.RAW_LEDGER),
    ("followup_tasks", TableRole.WORKFLOW),
    ("forecasts", TableRole.WORKFLOW),
    ("goal_contract_drafts", TableRole.WORKFLOW),
    ("goal_contract_heads", TableRole.WORKFLOW),
    ("goal_contract_versions", TableRole.RAW_LEDGER),
    ("golden_path_artifacts", TableRole.RECEIPT),
    ("golden_path_run_events", TableRole.RECEIPT),
    ("golden_path_runs", TableRole.WORKFLOW),
    ("grade_adjudications", TableRole.RAW_LEDGER),
    ("grade_interpretations", TableRole.RAW_LEDGER),
    ("grader_calibration_alphas", TableRole.RAW_LEDGER),
    ("grader_calibration_models", TableRole.RAW_LEDGER),
    ("grading_clarification_responses", TableRole.RAW_LEDGER),
    ("grading_clarifications", TableRole.RAW_LEDGER),
    ("grading_evidence", TableRole.RAW_LEDGER),
    ("hypothesis_events", TableRole.RAW_LEDGER),
    ("hypothesis_sets", TableRole.COMPAT),
    ("ingest_batches", TableRole.WORKFLOW),
    ("ingest_job_dependencies", TableRole.WORKFLOW),
    ("ingest_jobs", TableRole.WORKFLOW),
    ("interaction_events", TableRole.RAW_LEDGER),
    ("intervention_needs", TableRole.WORKFLOW),
    # A measured calibration artifact which may include provider trials and
    # observed evidence.  The deterministic backfill is not its full source.
    ("item_misconception_discrimination", TableRole.RAW_LEDGER),
    ("item_parameter_state", TableRole.DERIVED),
    ("lapse_episodes", TableRole.WORKFLOW),
    ("learner_claims", TableRole.RAW_LEDGER),
    ("learner_state_beliefs", TableRole.COMPAT),
    ("learner_theta", TableRole.COMPAT),
    ("learning_object_mastery", TableRole.DERIVED),
    ("learning_outcome_labels", TableRole.DERIVED),
    ("lo_probe_state", TableRole.COMPAT),
    ("maintenance_notices", TableRole.WORKFLOW),
    ("measurement_contract_corrections", TableRole.RAW_LEDGER),
    ("measurement_events", TableRole.RAW_LEDGER),
    ("misconception_candidates", TableRole.WORKFLOW),
    ("misconception_disposition_events", TableRole.RAW_LEDGER),
    ("misconception_transition_events", TableRole.RECEIPT),
    ("misconceptions", TableRole.WORKFLOW),
    ("missing_vocabulary_notes", TableRole.RAW_LEDGER),
    ("notation_mappings", TableRole.RAW_LEDGER),
    ("observation_events", TableRole.RAW_LEDGER),
    ("observation_templates", TableRole.RAW_LEDGER),
    ("outcome_schema_versions", TableRole.RAW_LEDGER),
    ("outcome_schemas", TableRole.RAW_LEDGER),
    ("p2_ladder_policies", TableRole.RAW_LEDGER),
    ("p2_ladder_stages", TableRole.RAW_LEDGER),
    ("parameter_bind_events", TableRole.RECEIPT),
    # Effective values are projectable, but promotions, lifecycle decisions,
    # and evidence links currently live only in this row.  Treat the mixed row
    # as authoritative until those decisions have a separate event ledger.
    ("parameter_registry", TableRole.RAW_LEDGER),
    ("parameter_registry_manifests", TableRole.RECEIPT),
    ("parameter_sensitivity_certificates", TableRole.RECEIPT),
    ("persona_realism_runs", TableRole.RECEIPT),
    ("policy_experiment_assignments", TableRole.RECEIPT),
    ("practice_attempts", TableRole.RAW_LEDGER),
    ("practice_item_quality_state", TableRole.DERIVED),
    # Migration 075 defines this as the active legacy compatibility projection;
    # activity_card_state is its partial successor.
    ("practice_item_state", TableRole.COMPAT),
    ("practice_pool_events", TableRole.RECEIPT),
    ("practice_pool_surfaces", TableRole.RAW_LEDGER),
    ("practice_pools", TableRole.RAW_LEDGER),
    ("probe_calibration_sessions", TableRole.WORKFLOW),
    ("probe_episodes", TableRole.WORKFLOW),
    # Includes reviewed-human evidence and empirical posteriors, neither of
    # which can be regenerated from the attempt ledger.
    ("probe_family_calibrations", TableRole.RAW_LEDGER),
    ("probe_family_lifecycle_events", TableRole.RECEIPT),
    ("probe_family_templates", TableRole.RAW_LEDGER),
    ("probe_generation_needs", TableRole.WORKFLOW),
    ("probe_instrument_cards", TableRole.RAW_LEDGER),
    ("probe_item_calibrations", TableRole.RAW_LEDGER),
    ("probe_item_family_links", TableRole.RAW_LEDGER),
    ("probe_manipulation_audits", TableRole.RECEIPT),
    ("probe_observations", TableRole.RAW_LEDGER),
    ("probe_presentations", TableRole.RAW_LEDGER),
    ("probe_regrade_checks", TableRole.RECEIPT),
    ("probe_state_segments", TableRole.WORKFLOW),
    ("progression_policy_versions", TableRole.RAW_LEDGER),
    ("proposed_patch_item_dependencies", TableRole.WORKFLOW),
    ("proposed_patch_items", TableRole.WORKFLOW),
    ("proposed_patches", TableRole.WORKFLOW),
    ("question_events", TableRole.RAW_LEDGER),
    ("question_promotion_requests", TableRole.WORKFLOW),
    ("question_promotions", TableRole.WORKFLOW),
    ("queue_state", TableRole.WORKFLOW),
    ("raw_grade_events", TableRole.RAW_LEDGER),
    ("reader_authored_questions", TableRole.WORKFLOW),
    ("reader_background_requests", TableRole.WORKFLOW),
    ("reader_capture_outbox", TableRole.WORKFLOW),
    ("reader_section_progress", TableRole.WORKFLOW),
    ("remediation_episodes", TableRole.WORKFLOW),
    ("retirement_records", TableRole.RECEIPT),
    ("reveal_events", TableRole.RAW_LEDGER),
    ("rung_variant_requests", TableRole.WORKFLOW),
    ("scheduler_explanations", TableRole.RECEIPT),
    ("scheduler_slate_candidates", TableRole.WORKFLOW),
    ("scheduler_slates", TableRole.WORKFLOW),
    ("schema_migrations", TableRole.RECEIPT),
    ("session_checkpoints", TableRole.WORKFLOW),
    ("sessions", TableRole.WORKFLOW),
    ("shadow_component_events", TableRole.RECEIPT),
    # Captured feature vectors; their generating inputs are not durably logged.
    ("soft_kinship_features", TableRole.RAW_LEDGER),
    ("source_annotation_anchor_segments", TableRole.RAW_LEDGER),
    ("source_annotation_anchor_versions", TableRole.RAW_LEDGER),
    ("source_annotation_events", TableRole.RAW_LEDGER),
    ("source_annotation_versions", TableRole.RAW_LEDGER),
    ("source_annotations", TableRole.RAW_LEDGER),
    ("source_artifacts", TableRole.RAW_LEDGER),
    # Migration 089 defines an additive, versioned analyzer artifact.  Some
    # analyzer inputs (for example equation confidence) live only in this row.
    ("source_block_health", TableRole.RAW_LEDGER),
    ("source_conflict_resolutions", TableRole.RECEIPT),
    ("source_conflicts", TableRole.WORKFLOW),
    ("source_document_assets", TableRole.RAW_LEDGER),
    ("source_document_blocks", TableRole.RAW_LEDGER),
    ("source_document_units", TableRole.RAW_LEDGER),
    ("source_exam_profiles", TableRole.COMPAT),
    ("source_exposure_events", TableRole.RAW_LEDGER),
    ("source_extraction_runs", TableRole.WORKFLOW),
    ("source_locator_schemes", TableRole.COMPAT),
    ("source_object_citations", TableRole.RAW_LEDGER),
    ("source_object_relations", TableRole.RAW_LEDGER),
    ("source_object_versions", TableRole.RAW_LEDGER),
    ("source_objects", TableRole.RAW_LEDGER),
    ("source_render_block_crosswalk", TableRole.RAW_LEDGER),
    ("source_render_views", TableRole.WORKFLOW),
    ("source_revisions", TableRole.RAW_LEDGER),
    ("source_span_reanchors", TableRole.RAW_LEDGER),
    ("source_unit_inventories", TableRole.RAW_LEDGER),
    ("source_unit_selections", TableRole.WORKFLOW),
    ("subject_identifiability_watermarks", TableRole.DERIVED),
    ("surface_fingerprint_memberships", TableRole.RAW_LEDGER),
    ("surface_mint_requests", TableRole.WORKFLOW),
    ("synthesis_generation_needs", TableRole.WORKFLOW),
    ("synthesis_manifests", TableRole.RAW_LEDGER),
    ("synthesis_runs", TableRole.WORKFLOW),
    ("synthesis_shard_results", TableRole.RAW_LEDGER),
    ("target_exemplars", TableRole.RAW_LEDGER),
    ("task_blueprint_review_events", TableRole.RECEIPT),
    ("task_blueprint_versions", TableRole.RAW_LEDGER),
    ("task_blueprints", TableRole.RAW_LEDGER),
    ("task_feature_schema_versions", TableRole.RAW_LEDGER),
    ("trace_exercised_facets", TableRole.RAW_LEDGER),
    ("unresolved_cause_factors", TableRole.WORKFLOW),
    ("vault_epigraphs", TableRole.RAW_LEDGER),
)


def _build_registry(items: tuple[tuple[str, TableRole], ...]) -> dict[str, TableRole]:
    registry = dict(items)
    if len(registry) != len(items):
        seen: set[str] = set()
        duplicates: set[str] = set()
        for table_name, _role in items:
            if table_name in seen:
                duplicates.add(table_name)
            seen.add(table_name)
        names = ", ".join(sorted(duplicates))
        raise RuntimeError(f"duplicate table-role declarations: {names}")
    return registry


TABLE_ROLES: Mapping[str, TableRole] = MappingProxyType(_build_registry(_TABLE_ROLE_ITEMS))


@dataclass(frozen=True, slots=True)
class TableRoleMismatch:
    """The two directions in which a schema and registry can disagree."""

    unclassified: frozenset[str]
    unknown: frozenset[str]

    @property
    def is_complete(self) -> bool:
        return not self.unclassified and not self.unknown


def role_for_table(table_name: str) -> TableRole:
    """Return ``table_name``'s declared role, raising ``KeyError`` if absent."""

    return TABLE_ROLES[table_name]


def tables_for_role(role: TableRole) -> frozenset[str]:
    """Return every table assigned to ``role``."""

    return frozenset(name for name, declared_role in TABLE_ROLES.items() if declared_role is role)


def user_table_names(connection: sqlite3.Connection) -> frozenset[str]:
    """Read the non-SQLite table names from an open database connection."""

    rows = connection.execute(
        """
        SELECT name
          FROM sqlite_master
         WHERE type = 'table'
           AND name NOT LIKE 'sqlite_%'
        """
    )
    return frozenset(str(row[0]) for row in rows)


def registry_mismatch(table_names: Iterable[str]) -> TableRoleMismatch:
    """Compare an observed schema to the declarative registry."""

    observed = frozenset(table_names)
    registered = frozenset(TABLE_ROLES)
    return TableRoleMismatch(
        unclassified=observed - registered,
        unknown=registered - observed,
    )


def assert_complete_registry(table_names: Iterable[str]) -> None:
    """Raise ``ValueError`` unless observed and registered tables match exactly."""

    mismatch = registry_mismatch(table_names)
    if mismatch.is_complete:
        return
    parts: list[str] = []
    if mismatch.unclassified:
        parts.append("unclassified: " + ", ".join(sorted(mismatch.unclassified)))
    if mismatch.unknown:
        parts.append("unknown: " + ", ".join(sorted(mismatch.unknown)))
    raise ValueError("table-role registry mismatch (" + "; ".join(parts) + ")")


__all__ = [
    "TABLE_ROLES",
    "TableRole",
    "TableRoleMismatch",
    "assert_complete_registry",
    "registry_mismatch",
    "role_for_table",
    "tables_for_role",
    "user_table_names",
]

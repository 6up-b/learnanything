---
title: "learnloop.content.proposals.ai_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/proposals/ai_contracts.py"
source_paths:
  - "src/learnloop/content/proposals/ai_contracts.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.proposals"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.proposals.ai_contracts module"
  - "src/learnloop/content/proposals/ai_contracts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-proposals"
---

# `learnloop.content.proposals.ai_contracts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.proposals.ai_contracts` exists within [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] to own the behavior summarized by its module contract: Feature-owned authoring-proposal AI contract.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py) |
| Source lines | 911 |
| Owning package | [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class FacetWeightPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 33) — One facet-weight pair (strict-schema-safe map entry).
- `class CriterionFacetWeightsPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 40) — Facet weights for one rubric criterion (strict-schema-safe map entry).
- `class CheckpointDependencyPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 47) — One checkpoint's prerequisites (strict-schema-safe map entry).
- `class SourceRef(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 149)
- `class TargetEntity(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 168)
- `class ProposalItemAudit(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 173)
- `class LearningObjectPatchPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 195)
- `class CriterionTargetPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 211) — One ``(facet, capability, role)`` observation a criterion makes.
- `class RubricCriterionPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 245)
- `class RubricFatalErrorPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 269)
- `class RubricPatchPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 277)
  - `derive_max_points_from_criteria(self) -> 'RubricPatchPayload'` (line 284; public)
- `class RequiredMethodPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 295) — The method an item's statement requires (owner rule 2026-10-13).
- `class TaskFeaturesPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 312) — Point TaskFeature vector (p1_launch schema, spec_p1 §3.4).
- `class TraceRecipePayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 328)
- `class TraceContractPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 334)
  - `validate_trace_contract(self) -> 'TraceContractPayload'` (line 339; public)
- `class DiscriminationProfilePayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 366) — A5's authored candidate shape (``spec_measurement_efficiency_v1`` §3.A5).
- `class DifferingComponentPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 403) — The one ``(facet, capability)`` requirement an A4 pair differs on (§3.A4).
- `class PlantedErrorPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 424) — One registry-sourced error planted in an A3 worked solution (§3.A3).
- `class ErrorHuntPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 453) — An A3 worked solution plus its plants, or the clean rotation (§3.A3).
- `class LadderedStemPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 465) — One part of an A2 laddered stem (§3.A2).
- `class VariantManipulationPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 480)
- `class VariantAuthoringContractPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 486)
- `class PracticeItemPatchPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 520)
- `class ConceptPatchPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 684)
- `class ConceptEdgePatchPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 693)
- `class ErrorTypePatchPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 701)
- `class AuthoringProposalItem(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 721)
  - `coerce_payload_by_item_type(cls, data: Any) -> Any` (line 735; public)
  - `validate_target_rules(self) -> 'AuthoringProposalItem'` (line 763; public)
- `class AuthoringContext` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 776)
- `class AuthoringProposal(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 791)
- `authoring_prompt(context: AuthoringContext) -> str` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 876)

### Module constants

- `EXPECTED_MINUTES_MAX` ([src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 497)
- `AUTHORING_PROMPT_VERSION` ([src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 804)
- `DIAGNOSTIC_AUTHORING_PROMPT_VERSION` ([src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 805)
- `PRACTICE_GENERATION_PROMPT_VERSION` ([src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 806)
- `DIAGNOSTIC_AUTHORING_PROMPT` ([src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 808)
- `_DIFFICULTY_GUIDANCE` ([src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 829)
- `_PRACTICE_METADATA_GUIDANCE` ([src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 837)
- `_FACET_VOCABULARY_GUIDANCE` ([src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 855)
- `_AUDIT_GUIDANCE` ([src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 866)

### Explicit exports

`__all__` declares:

- `AUTHORING_PROMPT_VERSION`
- `DIAGNOSTIC_AUTHORING_PROMPT`
- `DIAGNOSTIC_AUTHORING_PROMPT_VERSION`
- `PRACTICE_GENERATION_PROMPT_VERSION`
- `AuthoringContext`
- `AuthoringProposal`
- `authoring_prompt`

## Internal implementation anchors

- `_inlined_json_schema(model: type[BaseModel]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 54) — Return ``model``'s schema with every ``$ref`` resolved in place.
- `_pair_list_schema(model: type[BaseModel]) -> WithJsonSchema` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 77)
- `_facet_weight_map(value: Any) -> Any` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 81) — Accept ``[{facet_id, weight}, ...]`` as well as ``{facet_id: weight}``.
- `_criterion_facet_weight_map(value: Any) -> Any` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 98) — Accept ``[{criterion_id, weights}, ...]`` as well as the nested map.
- `_checkpoint_dependency_map(value: Any) -> Any` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 115) — Accept ``[{checkpoint_id, depends_on}, ...]`` as well as the map form.
- `_lenient_expected_minutes(value: Any) -> float | None` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 500) — A model's minutes estimate, kept inside the vault model's bounds (DL1 F8).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `AuthoringProposal`
- [[Reference/Modules/learnloop/content/authoring/ai_contracts|learnloop.content.authoring.ai_contracts]] — imports `CriterionFacetWeightsPayload`, `FacetWeightPayload`, `RequiredMethodPayload`, `RubricCriterionPayload`, `RubricPatchPayload`, `TaskFeaturesPayload`, `TraceContractPayload`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `PRACTICE_GENERATION_PROMPT_VERSION`
- [[Reference/Modules/learnloop/content/pipeline/ai_contracts|learnloop.content.pipeline.ai_contracts]] — imports `_AUDIT_GUIDANCE`, `_DIFFICULTY_GUIDANCE`, `_PRACTICE_METADATA_GUIDANCE`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `AuthoringProposal`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `AUTHORING_PROMPT_VERSION`, `AuthoringContext`, `AuthoringProposal`, `AuthoringProposalItem`, `DIAGNOSTIC_AUTHORING_PROMPT`, `DIAGNOSTIC_AUTHORING_PROMPT_VERSION`, `ProposalItemAudit`, `SourceRef`, `authoring_prompt`; statically calls `AuthoringContext`, `authoring_prompt`
- [[Reference/Modules/learnloop/curriculum/ai_contracts|learnloop.curriculum.ai_contracts]] — imports `TaskFeaturesPayload`
- [[Reference/Modules/learnloop/curriculum/graph_edit_proposals|learnloop.curriculum.graph_edit_proposals]] — imports `AuthoringProposal`, `AuthoringProposalItem`; statically calls `AuthoringProposal`
- [[Reference/Modules/learnloop/diagnosis/missing_vocabulary|learnloop.diagnosis.missing_vocabulary]] — imports `AUTHORING_PROMPT_VERSION`
- [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]] — imports `TraceContractPayload`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`, `describe_wire_validation_error`; calls `describe_wire_validation_error`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/attempt_types|learnloop.attempt_types]] — imports `AttemptType`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `CRITERIA_BY_FACT_GUIDANCE`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/content/authoring/ai_contracts|learnloop.content.authoring.ai_contracts]], [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/content/pipeline/ai_contracts|learnloop.content.pipeline.ai_contracts]], [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad23_contract_helpers.py](../../../../../../../tests/ad23_contract_helpers.py) — direct import
- [tests/proposal_persistence_helpers.py](../../../../../../../tests/proposal_persistence_helpers.py) — direct import
- [tests/required_method_authority_helpers.py](../../../../../../../tests/required_method_authority_helpers.py) — direct import
- [tests/source_ingestion_helpers.py](../../../../../../../tests/source_ingestion_helpers.py) — direct import
- [tests/structured_ai.py](../../../../../../../tests/structured_ai.py) — direct import
- [tests/test_ad23_contract.py](../../../../../../../tests/test_ad23_contract.py) — direct import
- [tests/test_ad23_fix_r5.py](../../../../../../../tests/test_ad23_fix_r5.py) — direct import
- [tests/test_ad23_fix_review.py](../../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_a_commission_queued_before_models_go_off_waits_and_resumes`
  - `test_a_serve_commission_queues_its_generation_once_at_its_point`
- [tests/test_ad23_owner_decisions.py](../../../../../../../tests/test_ad23_owner_decisions.py) — direct import
- [tests/test_agent_runs.py](../../../../../../../tests/test_agent_runs.py) — direct import
  - `test_generate_authoring_proposal_with_fake_client_has_lineage`
  - `test_persist_authoring_proposal_records_agent_run`
- [tests/test_codex_output_schema.py](../../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_authoring_payload_rejects_unknown_attempt_type`
  - `test_strict_schema_preserves_a_field_named_title`
  - `test_trace_recipe_dependencies_travel_as_pairs`
  - `test_undeclared_field_inside_a_proposal_item_names_the_payload_model`
  - `test_undeclared_wire_field_is_rejected_by_name`
  - `test_weight_maps_still_accept_the_legacy_map_form`
  - `test_weight_maps_travel_as_pairs_and_land_as_maps`
- [tests/test_daily_plan_review_regressions.py](../../../../../../../tests/test_daily_plan_review_regressions.py) — direct import
  - `test_f8_out_of_range_expected_minutes_reach_the_writer_bounded`
- [tests/test_diagnostic_generation.py](../../../../../../../tests/test_diagnostic_generation.py) — direct import
- [tests/test_diagnostic_review_policy.py](../../../../../../../tests/test_diagnostic_review_policy.py) — direct import
- [tests/test_doctor.py](../../../../../../../tests/test_doctor.py) — direct import
  - `test_doctor_warns_on_duplicate_diagnostic_practice_proposals`
- [tests/test_duration_estimates.py](../../../../../../../tests/test_duration_estimates.py) — direct import
  - `test_generated_items_carry_expected_minutes_through_the_wire_payload`
- [tests/test_e2e_codex_mock.py](../../../../../../../tests/test_e2e_codex_mock.py) — direct import
- [tests/test_exam_seeding.py](../../../../../../../tests/test_exam_seeding.py) — direct import
- [tests/test_ingest_instrument_gates.py](../../../../../../../tests/test_ingest_instrument_gates.py) — direct import
- [tests/test_missing_vocabulary_notes.py](../../../../../../../tests/test_missing_vocabulary_notes.py) — direct import
  - `test_authoring_facet_abstention_notes_read_the_criteria`
- [tests/test_persona_gate.py](../../../../../../../tests/test_persona_gate.py) — direct import
- [tests/test_practice_leakage.py](../../../../../../../tests/test_practice_leakage.py) — direct import
  - `test_generated_practice_never_reproduces_held_out_wording`
- [tests/test_proposal_persistence.py](../../../../../../../tests/test_proposal_persistence.py) — direct import
  - `test_accept_learning_object_create_adds_missing_concept_for_graph`
  - `test_ai_proposal_acceptance_records_ai_origin`
  - `test_auto_apply_batches_dependency_order_for_new_lo_and_practice_item`
  - `test_canonical_source_refs_flow_into_learning_object_provenance`
  - `test_create_payload_missing_required_fields_is_invalid`
  - `test_edit_proposal_item_updates_payload_and_refreshes_duplicate_validation`
  - `test_failed_repair_call_keeps_original_invalid_item`
  - `test_generate_persists_one_item_per_proposal_item`
  - `test_generated_item_local_criterion_may_honestly_omit_facets`
  - `test_generated_practice_missing_evidence_facets_is_invalid`
  - `test_generated_practice_missing_evidence_weights_is_not_smeared`
  - `test_generated_practice_missing_reward_metadata_is_invalid`
  - `test_generated_practice_rejects_unknown_metadata_keys`
  - `test_generated_practice_rubric_criterion_total_defines_grading_scale`
  - `test_generated_practice_single_facet_backfills_criterion_facet_weights`
  - `test_invalid_concept_edge_proposal_is_persisted_invalid`
  - `test_invalid_generated_item_gets_one_repair_round_trip`
  - `test_manual_practice_missing_evidence_weights_is_warning`
  - `test_practice_item_without_resolved_rubric_is_invalid_until_edited`
  - `test_registry_backed_vault_rejects_unknown_evidence_facet`
  - `test_reject_route_item_is_persisted_invalid_and_not_applied`
  - `test_source_grounded_auto_apply_accepts_low_risk_create`
  - `test_source_linked_generated_practice_missing_audit_is_invalid`
  - `test_source_linked_generated_practice_with_passed_audit_auto_applies`
  - `test_timed_out_repair_fails_without_persisting_first_pass`
  - `test_unresolved_source_ref_is_persisted_invalid`
  - `test_update_learning_object_proposal_preserves_existing_required_fields`
  - `test_update_practice_item_proposal_preserves_existing_learning_object`
  - `test_valid_proposal_skips_repair_round_trip`
- [tests/test_proposal_review_policy.py](../../../../../../../tests/test_proposal_review_policy.py) — direct import
  - `test_manual_context_auto_apply_route_still_requires_review`
- [tests/test_question_promotion_jobs.py](../../../../../../../tests/test_question_promotion_jobs.py) — direct import
  - `test_durable_promotion_persists_no_item_failure_for_retry`
- [tests/test_reader_progression.py](../../../../../../../tests/test_reader_progression.py) — direct import
- [tests/test_required_method_authority.py](../../../../../../../tests/test_required_method_authority.py) — direct import
  - `test_a_generated_proposal_never_changes_a_source_items_field`
- [tests/test_required_method_items.py](../../../../../../../tests/test_required_method_items.py) — direct import
  - `test_an_imported_exercise_keeps_a_required_method_only_by_its_one_time_judgment`
  - `test_authoring_prompts_carry_the_rule_and_moved_their_versions`
- [tests/test_required_method_reopened.py](../../../../../../../tests/test_required_method_reopened.py) — direct import
- [tests/test_required_method_rereview.py](../../../../../../../tests/test_required_method_rereview.py) — direct import
  - `test_f14_the_generation_guidance_leaves_the_sentence_to_the_writer`
- [tests/test_required_method_round3.py](../../../../../../../tests/test_required_method_round3.py) — direct import
- [tests/test_show.py](../../../../../../../tests/test_show.py) — direct import
  - `test_show_inspects_every_deterministic_id`
- [tests/test_source_ingestion.py](../../../../../../../tests/test_source_ingestion.py) — direct import
  - `test_composite_note_id_locator_source_ref_resolves`
  - `test_regrounded_update_clears_active_source_span_events`
  - `test_section_level_source_ref_resolves_to_child_chunks`
  - `test_youtube_missing_source_ref_accepts_registered_note_timecoded_id`
  - `test_youtube_missing_source_ref_is_reconstructed_from_timecoded_id`
  - `test_youtube_missing_source_ref_without_timecoded_id_stays_invalid`
  - `test_youtube_time_range_source_refs_can_span_caption_cues`
- [tests/test_source_ingestion_adapters.py](../../../../../../../tests/test_source_ingestion_adapters.py) — direct import
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — direct import
- [tests/test_teach_back_generation.py](../../../../../../../tests/test_teach_back_generation.py) — direct import
  - `test_practice_item_patch_payload_accepts_tiered_rubric`
  - `test_rubric_criterion_payload_tier_round_trip`
  - `test_teach_back_item_missing_core_criterion_for_facet_is_invalid`
  - `test_teach_back_item_with_unmapped_criterion_is_invalid`
  - `test_teach_back_item_without_rubric_is_invalid_despite_default_rubrics`
  - `test_well_formed_teach_back_item_is_valid`
- [tests/test_tutor_promotion_service.py](../../../../../../../tests/test_tutor_promotion_service.py) — direct import
  - `test_gap_inline_diagnostic_generation_when_available`
  - `test_practice_promotion_with_no_authored_item_fails_instead_of_claiming_review`
- [tests/text_gap_fakes.py](../../../../../../../tests/text_gap_fakes.py) — direct import
- [tests/tutor_promotion_service_helpers.py](../../../../../../../tests/tutor_promotion_service_helpers.py) — direct import

## Modification guidance

- Change feature context, prompt assembly, result models, and operation purposes here; keep provider mechanics in `learnloop.ai`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

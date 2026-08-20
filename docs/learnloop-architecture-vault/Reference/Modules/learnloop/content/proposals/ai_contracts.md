---
title: "learnloop.content.proposals.ai_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/proposals/ai_contracts.py"
source_paths:
  - "src/learnloop/content/proposals/ai_contracts.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.proposals.ai_contracts` exists within [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] to own the behavior summarized by its module contract: Feature-owned authoring-proposal AI contract.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py) |
| Source lines | 846 |
| Owning package | [[Reference/Modules/learnloop/content/proposals/_package|learnloop.content.proposals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class FacetWeightPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 32) — One facet-weight pair (strict-schema-safe map entry).
- `class CriterionFacetWeightsPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 39) — Facet weights for one rubric criterion (strict-schema-safe map entry).
- `class CheckpointDependencyPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 46) — One checkpoint's prerequisites (strict-schema-safe map entry).
- `class SourceRef(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 148)
- `class TargetEntity(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 167)
- `class ProposalItemAudit(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 172)
- `class LearningObjectPatchPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 194)
- `class CriterionTargetPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 210) — One ``(facet, capability, role)`` observation a criterion makes.
- `class RubricCriterionPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 244)
- `class RubricFatalErrorPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 268)
- `class RubricPatchPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 276)
  - `derive_max_points_from_criteria(self) -> 'RubricPatchPayload'` (line 283; public)
- `class TaskFeaturesPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 294) — Point TaskFeature vector (p1_launch schema, spec_p1 §3.4).
- `class TraceRecipePayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 310)
- `class TraceContractPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 316)
  - `validate_trace_contract(self) -> 'TraceContractPayload'` (line 321; public)
- `class DiscriminationProfilePayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 348) — A5's authored candidate shape (``spec_measurement_efficiency_v1`` §3.A5).
- `class DifferingComponentPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 385) — The one ``(facet, capability)`` requirement an A4 pair differs on (§3.A4).
- `class PlantedErrorPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 406) — One registry-sourced error planted in an A3 worked solution (§3.A3).
- `class ErrorHuntPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 435) — An A3 worked solution plus its plants, or the clean rotation (§3.A3).
- `class LadderedStemPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 447) — One part of an A2 laddered stem (§3.A2).
- `class VariantManipulationPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 462)
- `class VariantAuthoringContractPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 468)
- `class PracticeItemPatchPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 478)
- `class ConceptPatchPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 627)
- `class ConceptEdgePatchPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 636)
- `class ErrorTypePatchPayload(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 644)
- `class AuthoringProposalItem(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 664)
  - `coerce_payload_by_item_type(cls, data: Any) -> Any` (line 678; public)
  - `validate_target_rules(self) -> 'AuthoringProposalItem'` (line 706; public)
- `class AuthoringContext` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 719)
- `class AuthoringProposal(WireModel)` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 734)
- `authoring_prompt(context: AuthoringContext) -> str` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 811)

### Module constants

- `AUTHORING_PROMPT_VERSION` ([src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 740)
- `DIAGNOSTIC_AUTHORING_PROMPT_VERSION` ([src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 741)
- `PRACTICE_GENERATION_PROMPT_VERSION` ([src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 742)
- `DIAGNOSTIC_AUTHORING_PROMPT` ([src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 744)
- `_DIFFICULTY_GUIDANCE` ([src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 765)
- `_PRACTICE_METADATA_GUIDANCE` ([src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 773)
- `_FACET_VOCABULARY_GUIDANCE` ([src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 790)
- `_AUDIT_GUIDANCE` ([src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 801)

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

- `_inlined_json_schema(model: type[BaseModel]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 53) — Return ``model``'s schema with every ``$ref`` resolved in place.
- `_pair_list_schema(model: type[BaseModel]) -> WithJsonSchema` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 76)
- `_facet_weight_map(value: Any) -> Any` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 80) — Accept ``[{facet_id, weight}, ...]`` as well as ``{facet_id: weight}``.
- `_criterion_facet_weight_map(value: Any) -> Any` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 97) — Accept ``[{criterion_id, weights}, ...]`` as well as the nested map.
- `_checkpoint_dependency_map(value: Any) -> Any` ([source](../../../../../../../src/learnloop/content/proposals/ai_contracts.py), line 114) — Accept ``[{checkpoint_id, depends_on}, ...]`` as well as the map form.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `AuthoringProposal`
- [[Reference/Modules/learnloop/content/authoring/ai_contracts|learnloop.content.authoring.ai_contracts]] — imports `CriterionFacetWeightsPayload`, `FacetWeightPayload`, `RubricCriterionPayload`, `RubricPatchPayload`, `TaskFeaturesPayload`, `TraceContractPayload`
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

- [tests/structured_ai.py](../../../../../../../tests/structured_ai.py) — direct import
- [tests/test_agent_runs.py](../../../../../../../tests/test_agent_runs.py) — direct import
  - `test_generate_authoring_proposal_with_fake_client_has_lineage`
  - `test_persist_authoring_proposal_records_agent_run`
- [tests/test_codex_output_schema.py](../../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_authoring_payload_rejects_unknown_attempt_type`
  - `test_codex_authoring_schema_is_strict_response_format_compatible`
  - `test_sdk_authoring_path_passes_strict_schema_to_codex`
  - `test_trace_recipe_dependencies_travel_as_pairs`
  - `test_undeclared_field_inside_a_proposal_item_names_the_payload_model`
  - `test_undeclared_wire_field_is_rejected_by_name`
  - `test_weight_maps_still_accept_the_legacy_map_form`
  - `test_weight_maps_travel_as_pairs_and_land_as_maps`
- [tests/test_diagnostic_generation.py](../../../../../../../tests/test_diagnostic_generation.py) — direct import
- [tests/test_diagnostic_review_policy.py](../../../../../../../tests/test_diagnostic_review_policy.py) — direct import
- [tests/test_doctor.py](../../../../../../../tests/test_doctor.py) — direct import
  - `test_doctor_warns_on_duplicate_diagnostic_practice_proposals`
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

## Modification guidance

- Change feature context, prompt assembly, result models, and operation purposes here; keep provider mechanics in `learnloop.ai`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/proposals/ai_contracts.py](../../../../../../../src/learnloop/content/proposals/ai_contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

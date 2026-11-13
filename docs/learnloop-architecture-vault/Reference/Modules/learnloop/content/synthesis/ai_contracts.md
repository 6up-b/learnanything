---
title: "learnloop.content.synthesis.ai_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/ai_contracts.py"
source_paths:
  - "src/learnloop/content/synthesis/ai_contracts.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.synthesis"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.synthesis.ai_contracts module"
  - "src/learnloop/content/synthesis/ai_contracts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.ai_contracts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.ai_contracts` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Structured AI contracts owned by source inventory and synthesis.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py) |
| Source lines | 1061 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class InventoryConceptMention(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 14)
- `class InventoryClaim(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 22)
- `class InventoryProcedureSignal(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 37)
  - `coerce_span_ids(cls, data: Any) -> Any` (line 47; public) — Accept ``span_ids``, the name every other inventory row uses.
- `class InventoryPracticeSignal(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 68)
- `class InventoryAssessmentSignal(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 81)
- `class InventoryMisconceptionSignal(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 94)
- `class InventoryCoverageClaim(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 103)
- `class InventoryWarning(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 110)
- `class SynthSpanRef(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 128) — One span citation (§8.5).
- `class SynthSpanRequest(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 141) — A pass-1 evidence-view request (§8.5).
- `class SynthConcept(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 150)
- `class SynthFacet(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 159) — A canonical facet registry entry (knowledge-model §3.2), span-cited.
- `class SynthRecipeComponent(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 180) — An `all_of`/`any_of` recipe component.
- `class SynthIntegrationComponent(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 204) — The optional `integration` component of a recipe (knowledge-model §7.2).
- `class SynthRecipe(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 228)
- `class SynthBlueprint(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 236) — A performance blueprint (knowledge-model §7.2).
- `class SynthLearningObject(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 253)
- `class SynthCriterionTarget(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 268) — An authored criterion target (A1).
- `class SynthCriterion(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 285)
- `class SynthEvidenceFingerprint(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 296)
- `class SynthRequiredMethod(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 304) — Method-explicit items (owner rule 2026-10-13): the method an item's prompt requires, only when its target IS that method; the writer drops it anywhere else and appends the explicit instruction when it is missing.
- `class SynthPracticeItem(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 313)
- `class SynthConflict(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 335)
- `class ConceptRelation(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 342) — One typed concept-graph edge (knowledge-model concept graph).
- `class ConceptMergeGroup(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 361) — One set of semantically-duplicate concepts to fold into a canonical one.
- `class AppendProvenanceLink(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 379) — A `provenance_link` additive item (span_attach / alternate_explanation / assessment_alignment, §10.2).
- `class AppendNotationMapping(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 398) — A contextual notation equivalence (`notation_mapping`, review-required).
- `class AppendConflict(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 410) — A two-sided conflict (`source_conflict`, always reviewed).
- `class AppendFacetWording(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 422) — The new wording of an existing facet, for a facet restructure (a reword).
- `class AppendRestructure(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 454) — A semantic replacement/removal (`restructure_unlocked`; update/deactivate).
- `class SourceUnitInventoryContext` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 474)
- `class SourceSetSynthesisContext` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 483)
- `class ConceptGraphContext` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 500)
- `class AppendReconciliationContext` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 516)
- `class VaultEpigraphContext` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 533) — Bounded digest of freshly synthesized material for the Start-screen epigraphs (quotes/haiku).
- `class SourceUnitInventory(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 551)
- `class SourceSetSynthesis(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 565)
- `class ConceptGraphStructuring(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 579)
- `class RegistryConceptMerge(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 585) — The structuring model's decision that a candidate IS a registry concept (T5).
- `class ConceptGraphStructuringWithRegistry(ConceptGraphStructuring)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 597)
- `class AppendReconciliation(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 601)
- `class VaultEpigraph(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 618) — One Start-screen epigraph: a one-line aphorism or a three-line haiku.
- `class VaultEpigraphBatch(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 628)
- `source_unit_inventory_prompt(context: SourceUnitInventoryContext) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 988)
- `source_set_synthesis_prompt_version(one_facet_per_skill: bool) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 996)
- `source_set_synthesis_prompt(context: SourceSetSynthesisContext) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 1003)
- `concept_graph_has_registry_nominations(context: ConceptGraphContext | None) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 1014)
- `concept_graph_structuring_prompt(context: ConceptGraphContext) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 1021)
- `append_reconciliation_prompt_version(one_facet_per_skill: bool) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 1039)
- `append_reconciliation_prompt(context: AppendReconciliationContext) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 1046)
- `vault_epigraphs_prompt(context: VaultEpigraphContext) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 1056)

### Module constants

- `SOURCE_UNIT_INVENTORY_PROMPT_VERSION` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 632)
- `SOURCE_SET_SYNTHESIS_PROMPT_VERSION` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 636)
- `SOURCE_SET_SYNTHESIS_FACET_IDENTITY_PROMPT_VERSION` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 639)
- `CONCEPT_GRAPH_STRUCTURING_PROMPT_VERSION` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 640)
- `CONCEPT_GRAPH_REGISTRY_PROMPT_VERSION` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 641)
- `APPEND_RECONCILIATION_PROMPT_VERSION` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 642)
- `APPEND_RECONCILIATION_FACET_IDENTITY_PROMPT_VERSION` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 643)
- `VAULT_EPIGRAPHS_PROMPT_VERSION` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 644)
- `SOURCE_UNIT_INVENTORY_PROMPT` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 646)
- `SOURCE_SET_SYNTHESIS_PROMPT` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 681)
- `SOURCE_SET_SYNTHESIS_PROMPT` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 815)
- `ONE_FACET_PER_SKILL_RULE` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 817)
- `APPEND_ONE_FACET_PER_SKILL_RULE` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 826)
- `CONCEPT_GRAPH_STRUCTURING_PROMPT` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 833)
- `CONCEPT_GRAPH_REGISTRY_ADDENDUM` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 883)
- `APPEND_RECONCILIATION_PROMPT` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 901)
- `APPEND_RECONCILIATION_PROMPT` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 957)
- `VAULT_EPIGRAPHS_PROMPT` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 959)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `SOURCE_SET_SYNTHESIS_PROMPT_VERSION`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `AppendReconciliation`, `AppendReconciliationContext`, `SourceSetSynthesis`, `append_reconciliation_prompt`, `append_reconciliation_prompt_version`; statically calls `AppendReconciliationContext`, `SourceSetSynthesis`, `append_reconciliation_prompt`, `append_reconciliation_prompt_version`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `CONCEPT_GRAPH_REGISTRY_PROMPT_VERSION`, `ConceptGraphContext`, `ConceptGraphStructuring`, `ConceptGraphStructuringWithRegistry`, `SourceSetSynthesis`, `SourceSetSynthesisContext`, `concept_graph_has_registry_nominations`, `concept_graph_structuring_prompt`, `source_set_synthesis_prompt`, `source_set_synthesis_prompt_version`; statically calls `ConceptGraphContext`, `SourceSetSynthesis`, `SourceSetSynthesisContext`, `concept_graph_has_registry_nominations`, `concept_graph_structuring_prompt`, `source_set_synthesis_prompt`, `source_set_synthesis_prompt_version`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `SOURCE_UNIT_INVENTORY_PROMPT_VERSION`, `SourceUnitInventory`, `SourceUnitInventoryContext`, `source_unit_inventory_prompt`; statically calls `SourceUnitInventory`, `SourceUnitInventoryContext`, `source_unit_inventory_prompt`
- [[Reference/Modules/learnloop/content/synthesis/vault_epigraphs|learnloop.content.synthesis.vault_epigraphs]] — imports `VAULT_EPIGRAPHS_PROMPT_VERSION`, `VaultEpigraph`, `VaultEpigraphBatch`, `VaultEpigraphContext`, `vault_epigraphs_prompt`; statically calls `VaultEpigraphContext`, `vault_epigraphs_prompt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `CRITERIA_BY_FACT_GUIDANCE`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]], [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]], [[Reference/Modules/learnloop/content/synthesis/vault_epigraphs|learnloop.content.synthesis.vault_epigraphs]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/facet_authority_helpers.py](../../../../../../../tests/facet_authority_helpers.py) — direct import
- [tests/facet_identity_ingest_helpers.py](../../../../../../../tests/facet_identity_ingest_helpers.py) — direct import
- [tests/facet_reword_paths_helpers.py](../../../../../../../tests/facet_reword_paths_helpers.py) — direct import
- [tests/identity_pins_helpers.py](../../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/source_append_helpers.py](../../../../../../../tests/source_append_helpers.py) — direct import
- [tests/source_inventory_helpers.py](../../../../../../../tests/source_inventory_helpers.py) — direct import
- [tests/source_set_synthesis_helpers.py](../../../../../../../tests/source_set_synthesis_helpers.py) — direct import
- [tests/structured_ai.py](../../../../../../../tests/structured_ai.py) — direct import
- [tests/test_cli_append_units.py](../../../../../../../tests/test_cli_append_units.py) — direct import
- [tests/test_codex_output_schema.py](../../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_append_schema_declares_properties_on_bare_restructure_payload`
- [tests/test_exam_protection_identity.py](../../../../../../../tests/test_exam_protection_identity.py) — direct import
  - `test_identity_review_f2_an_unbound_signal_never_lets_a_known_one_mark_its_origin`
- [tests/test_facet_authority.py](../../../../../../../tests/test_facet_authority.py) — direct import
  - `test_a_bootstrap_candidate_carrying_a_registered_id_rewords_it_uncited_only_with_the_owners_confirm`
  - `test_a_cited_bootstrap_candidate_carrying_a_registered_id_rewords_it_as_a_checked_update`
  - `test_an_uncited_append_facet_carrying_a_registered_id_never_rewrites_it`
- [tests/test_facet_identity.py](../../../../../../../tests/test_facet_identity.py) — direct import
  - `test_an_undone_in_run_merge_stays_apart_when_the_run_is_planned_again`
  - `test_in_run_consolidation_of_the_regression_set`
  - `test_the_plan_is_off_with_the_kill_switch`
- [tests/test_facet_identity_composition.py](../../../../../../../tests/test_facet_identity_composition.py) — direct import
  - `test_the_ledger_records_merged_pairs_and_shortlisted_different_pairs_only`
- [tests/test_facet_identity_ingest.py](../../../../../../../tests/test_facet_identity_ingest.py) — direct import
  - `test_a_duplicate_candidate_is_merged_before_the_gates_and_undo_re_mints_it`
  - `test_append_attaches_a_new_facet_to_the_registered_one_it_restates`
  - `test_the_kill_switch_restores_the_prompt_and_never_calls_the_judge`
- [tests/test_facet_reword_confirm.py](../../../../../../../tests/test_facet_reword_confirm.py) — direct import
  - `test_a_bootstrap_candidate_carrying_a_registered_id_uncited_is_kept_for_confirm`
  - `test_a_bootstrap_reword_citing_exam_material_under_the_wrong_unit_is_dropped_not_held`
  - `test_an_exam_only_bootstrap_candidate_carrying_a_registered_id_is_dropped_not_held`
- [tests/test_facet_reword_confirm_review.py](../../../../../../../tests/test_facet_reword_confirm_review.py) — direct import
  - `test_an_attach_absorbing_an_exam_span_cited_under_the_wrong_unit_never_grows_the_facet`
  - `test_the_append_schema_lets_a_provider_send_a_title_and_worked_examples`
  - `test_with_the_kill_switch_an_uncited_absorbed_example_joins_as_an_alias_only`
- [tests/test_facet_reword_paths.py](../../../../../../../tests/test_facet_reword_paths.py) — direct import
  - `test_the_append_schema_lets_a_facet_reword_cite_its_spans`
  - `test_the_append_schema_lets_a_provider_reword_a_facet`
- [tests/test_graph_nomination_ingest.py](../../../../../../../tests/test_graph_nomination_ingest.py) — direct import
  - `test_backfill_after_apply_reuses_the_vectors_paid_at_ingest`
  - `test_guarded_registry_merge_is_ledgered_but_not_applied`
  - `test_kill_switch_restores_the_pre_t5_request`
  - `test_structuring_sees_registry_definitions_and_decides_a_registry_merge`
- [tests/test_ingest_instrument_gates.py](../../../../../../../tests/test_ingest_instrument_gates.py) — direct import
  - `test_omitted_component_capability_defaults_with_diagnostic`
  - `test_omitted_criterion_target_capability_defaults_with_diagnostic`
  - `test_single_alternative_any_of_gets_review_diagnostic`
  - `test_vacuous_recipe_hard_fails_at_the_gate`
- [tests/test_ingest_runner.py](../../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_public_import_inventory_dependency_resolves_extraction_and_units`
- [tests/test_ingestion_checkpoints.py](../../../../../../../tests/test_ingestion_checkpoints.py) — direct import
  - `test_evidence_followup_keeps_the_full_inventory_in_its_cached_prefix`
- [tests/test_inventory_choice.py](../../../../../../../tests/test_inventory_choice.py) — direct import
  - `test_a_row_under_the_current_prompt_label_beats_an_older_label`
- [tests/test_model_work_checkpoints.py](../../../../../../../tests/test_model_work_checkpoints.py) — direct import
- [tests/test_openai_chat_client.py](../../../../../../../tests/test_openai_chat_client.py) — direct import
  - `test_extended_method_repairs_invalid_json_once`
- [tests/test_outer_cache_keys.py](../../../../../../../tests/test_outer_cache_keys.py) — direct import
  - `test_a_shard_prompt_edited_under_the_same_label_is_paid_once`
- [tests/test_required_method_items.py](../../../../../../../tests/test_required_method_items.py) — direct import
  - `test_authoring_prompts_carry_the_rule_and_moved_their_versions`
  - `test_synthesis_publishes_a_required_method_presented_with_the_canonical_sentence`
- [tests/test_required_method_rereview.py](../../../../../../../tests/test_required_method_rereview.py) — direct import
  - `test_f14_the_generation_guidance_leaves_the_sentence_to_the_writer`
- [tests/test_source_append.py](../../../../../../../tests/test_source_append.py) — direct import
  - `test_a_retry_after_an_append_gate_failure_pays_for_a_fresh_answer`
  - `test_append_vocabulary_auto_apply_rules`
  - `test_conflict_accept_creates_open_row_reject_creates_none`
  - `test_conflict_reject_creates_no_row`
  - `test_narrow_adjunct_deterministically_drops_model_restructures`
  - `test_post_append_near_duplicate_is_aliased_at_mint_and_never_auto_merged`
  - `test_provenance_links_without_a_resolvable_span_are_dropped_not_hard_failed`
  - `test_specialized_side_effects_recover_idempotently`
- [tests/test_source_inventory.py](../../../../../../../tests/test_source_inventory.py) — direct import
  - `test_inventory_rejects_uncited_and_unknown_spans`
  - `test_procedure_signal_span_ids_coercion_and_validation`
- [tests/test_source_set_synthesis.py](../../../../../../../tests/test_source_set_synthesis.py) — direct import
  - `test_blueprint_requires_at_least_one_recipe`
  - `test_bootstrap_canonicalizes_prerequisite_and_confusable_concepts`
  - `test_bootstrap_persists_vault_epigraphs`
  - `test_evidence_pass_retry_reuses_first_paid_pass`
  - `test_graph_structuring_merges_near_duplicates_and_authors_relations`
  - `test_graph_structuring_relations_become_concept_edges`
  - `test_integration_capability_has_no_schema_default`
  - `test_invalid_structuring_nomination_is_a_noop`
  - `test_lo_prerequisites_derive_concept_edges_without_model_relations`
  - `test_non_ascii_output_is_charged_by_characters_not_escapes`
  - `test_synthesis_capabilities_use_closed_vocabulary`
  - `test_synthesis_shards_namespace_declarations_and_references`
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — direct import
- [tests/test_synthesis_criterion_dependencies.py](../../../../../../../tests/test_synthesis_criterion_dependencies.py) — direct import
  - `test_the_prompts_say_criterion_depends_on_names_sibling_criteria_only`
- [tests/test_ux_phase1_usability_round1.py](../../../../../../../tests/test_ux_phase1_usability_round1.py) — direct import
- [tests/test_vault_epigraphs.py](../../../../../../../tests/test_vault_epigraphs.py) — direct import
  - `test_a_batch_with_nothing_valid_is_not_replayed`
  - `test_generate_drops_invalid_items_and_in_batch_duplicates`
  - `test_generate_persists_three_rows_with_stamps`
  - `test_prompt_round_trips_through_the_structured_fake`

## Modification guidance

- Change feature context, prompt assembly, result models, and operation purposes here; keep provider mechanics in `learnloop.ai`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

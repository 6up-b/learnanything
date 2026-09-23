---
title: "learnloop.content.synthesis.ai_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/ai_contracts.py"
source_paths:
  - "src/learnloop/content/synthesis/ai_contracts.py"
source_commit: "0395ae32f9e2e40d1cb98b38402631299a94003f"
source_commit_timestamp: "2026-09-07T12:49:13-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.ai_contracts` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Structured AI contracts owned by source inventory and synthesis.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py) |
| Source lines | 886 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `0395ae32f9e2e40d1cb98b38402631299a94003f` |
| Commit timestamp | `2026-09-07T12:49:13-04:00` |

## Public API

- `class InventoryConceptMention(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 13)
- `class InventoryClaim(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 21)
- `class InventoryProcedureSignal(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 36)
  - `coerce_span_ids(cls, data: Any) -> Any` (line 46; public) — Accept ``span_ids``, the name every other inventory row uses.
- `class InventoryPracticeSignal(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 67)
- `class InventoryAssessmentSignal(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 80)
- `class InventoryMisconceptionSignal(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 93)
- `class InventoryCoverageClaim(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 102)
- `class InventoryWarning(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 109)
- `class SynthSpanRef(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 127) — One span citation (§8.5).
- `class SynthSpanRequest(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 140) — A pass-1 evidence-view request (§8.5).
- `class SynthConcept(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 149)
- `class SynthFacet(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 158) — A canonical facet registry entry (knowledge-model §3.2), span-cited.
- `class SynthRecipeComponent(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 179) — An `all_of`/`any_of` recipe component.
- `class SynthIntegrationComponent(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 203) — The optional `integration` component of a recipe (knowledge-model §7.2).
- `class SynthRecipe(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 227)
- `class SynthBlueprint(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 235) — A performance blueprint (knowledge-model §7.2).
- `class SynthLearningObject(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 252)
- `class SynthCriterionTarget(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 267) — An authored criterion target (A1).
- `class SynthCriterion(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 284)
- `class SynthEvidenceFingerprint(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 295)
- `class SynthPracticeItem(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 303)
- `class SynthConflict(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 324)
- `class ConceptRelation(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 331) — One typed concept-graph edge (knowledge-model concept graph).
- `class ConceptMergeGroup(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 350) — One set of semantically-duplicate concepts to fold into a canonical one.
- `class AppendProvenanceLink(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 368) — A `provenance_link` additive item (span_attach / alternate_explanation / assessment_alignment, §10.2).
- `class AppendNotationMapping(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 387) — A contextual notation equivalence (`notation_mapping`, review-required).
- `class AppendConflict(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 399) — A two-sided conflict (`source_conflict`, always reviewed).
- `class AppendRestructure(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 411) — A semantic replacement/removal (`restructure_unlocked`; update/deactivate).
- `class SourceUnitInventoryContext` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 426)
- `class SourceSetSynthesisContext` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 435)
- `class ConceptGraphContext` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 449)
- `class AppendReconciliationContext` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 459)
- `class VaultEpigraphContext` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 474) — Bounded digest of freshly synthesized material for the Start-screen epigraphs (quotes/haiku).
- `class SourceUnitInventory(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 492)
- `class SourceSetSynthesis(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 506)
- `class ConceptGraphStructuring(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 520)
- `class AppendReconciliation(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 526)
- `class VaultEpigraph(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 543) — One Start-screen epigraph: a one-line aphorism or a three-line haiku.
- `class VaultEpigraphBatch(WireModel)` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 553)
- `source_unit_inventory_prompt(context: SourceUnitInventoryContext) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 848)
- `source_set_synthesis_prompt(context: SourceSetSynthesisContext) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 856)
- `concept_graph_structuring_prompt(context: ConceptGraphContext) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 865)
- `append_reconciliation_prompt(context: AppendReconciliationContext) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 873)
- `vault_epigraphs_prompt(context: VaultEpigraphContext) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 881)

### Module constants

- `SOURCE_UNIT_INVENTORY_PROMPT_VERSION` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 557)
- `SOURCE_SET_SYNTHESIS_PROMPT_VERSION` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 558)
- `CONCEPT_GRAPH_STRUCTURING_PROMPT_VERSION` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 559)
- `APPEND_RECONCILIATION_PROMPT_VERSION` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 560)
- `VAULT_EPIGRAPHS_PROMPT_VERSION` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 561)
- `SOURCE_UNIT_INVENTORY_PROMPT` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 563)
- `SOURCE_SET_SYNTHESIS_PROMPT` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 598)
- `CONCEPT_GRAPH_STRUCTURING_PROMPT` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 724)
- `APPEND_RECONCILIATION_PROMPT` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 774)
- `VAULT_EPIGRAPHS_PROMPT` ([src/learnloop/content/synthesis/ai_contracts.py](../../../../../../../src/learnloop/content/synthesis/ai_contracts.py), line 819)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `SOURCE_SET_SYNTHESIS_PROMPT_VERSION`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `APPEND_RECONCILIATION_PROMPT_VERSION`, `AppendReconciliation`, `AppendReconciliationContext`, `SourceSetSynthesis`, `SynthSpanRef`, `append_reconciliation_prompt`; statically calls `AppendReconciliationContext`, `SourceSetSynthesis`, `append_reconciliation_prompt`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `ConceptGraphContext`, `ConceptGraphStructuring`, `SOURCE_SET_SYNTHESIS_PROMPT_VERSION`, `SourceSetSynthesis`, `SourceSetSynthesisContext`, `concept_graph_structuring_prompt`, `source_set_synthesis_prompt`; statically calls `ConceptGraphContext`, `SourceSetSynthesis`, `SourceSetSynthesisContext`, `concept_graph_structuring_prompt`, `source_set_synthesis_prompt`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `SOURCE_UNIT_INVENTORY_PROMPT_VERSION`, `SourceUnitInventory`, `SourceUnitInventoryContext`, `source_unit_inventory_prompt`; statically calls `SourceUnitInventory`, `SourceUnitInventoryContext`, `source_unit_inventory_prompt`
- [[Reference/Modules/learnloop/content/synthesis/vault_epigraphs|learnloop.content.synthesis.vault_epigraphs]] — imports `VAULT_EPIGRAPHS_PROMPT_VERSION`, `VaultEpigraph`, `VaultEpigraphBatch`, `VaultEpigraphContext`, `vault_epigraphs_prompt`; statically calls `VaultEpigraphContext`, `vault_epigraphs_prompt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`

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

- [tests/structured_ai.py](../../../../../../../tests/structured_ai.py) — direct import
- [tests/test_codex_output_schema.py](../../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_append_schema_declares_properties_on_bare_restructure_payload`
- [tests/test_ingest_instrument_gates.py](../../../../../../../tests/test_ingest_instrument_gates.py) — direct import
  - `test_omitted_component_capability_defaults_with_diagnostic`
  - `test_omitted_criterion_target_capability_defaults_with_diagnostic`
  - `test_single_alternative_any_of_gets_review_diagnostic`
  - `test_vacuous_recipe_hard_fails_at_the_gate`
- [tests/test_ingest_runner.py](../../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_public_import_inventory_dependency_resolves_extraction_and_units`
- [tests/test_ingestion_checkpoints.py](../../../../../../../tests/test_ingestion_checkpoints.py) — direct import
  - `test_evidence_followup_keeps_the_full_inventory_in_its_cached_prefix`
- [tests/test_openai_chat_client.py](../../../../../../../tests/test_openai_chat_client.py) — direct import
  - `test_extended_method_repairs_invalid_json_once`
- [tests/test_source_append.py](../../../../../../../tests/test_source_append.py) — direct import
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
- [tests/test_vault_epigraphs.py](../../../../../../../tests/test_vault_epigraphs.py) — direct import
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

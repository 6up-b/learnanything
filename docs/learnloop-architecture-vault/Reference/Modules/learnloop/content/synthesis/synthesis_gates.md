---
title: "learnloop.content.synthesis.synthesis_gates"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/synthesis_gates.py"
source_paths:
  - "src/learnloop/content/synthesis/synthesis_gates.py"
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
  - "learnloop.content.synthesis.synthesis_gates module"
  - "src/learnloop/content/synthesis/synthesis_gates.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.synthesis_gates`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.synthesis_gates` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Deterministic synthesis quality gates (source-ingestion §8.7).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/synthesis_gates.py](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py) |
| Source lines | 1044 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class GateDiagnostic` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 44)
  - `to_dict(self) -> dict[str, Any]` (line 51; public)
- `class ProvenanceRef` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 62) — A source span backing a proposed entity (§4.2/§8.5).
- `class GateItem` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 80)
  - `is_semantic(self) -> bool` (line 103; public)
  - `is_destructive(self) -> bool` (line 108; public)
  - `refs(self) -> tuple[str, ...]` (line 113; public)
- `class GateProposal` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 118)
- `class GateContext` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 127)
- `class GateReport` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 161)
  - `hard_fails(self) -> list[GateDiagnostic]` (line 165; public)
  - `reviews(self) -> list[GateDiagnostic]` (line 169; public)
  - `blocked(self) -> bool` (line 173; public) — True when any hard_fail is present — the proposal cannot be persisted.
  - `requires_review(self) -> bool` (line 179; public)
  - `gates_fired(self) -> set[str]` (line 182; public)
- `run_synthesis_gates(proposal: GateProposal, ctx: GateContext) -> GateReport` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 186) — Run every §8.7 gate and collect typed diagnostics.

### Module constants

- `SEMANTIC_AUTHORITY_ROLES` ([src/learnloop/content/synthesis/synthesis_gates.py](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 33)
- `_SEMANTIC_ITEM_TYPES` ([src/learnloop/content/synthesis/synthesis_gates.py](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 37)
- `_TOKEN_RE` ([src/learnloop/content/synthesis/synthesis_gates.py](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 38)
- `_ADDITIVE_ITEM_TYPES` ([src/learnloop/content/synthesis/synthesis_gates.py](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 786)
- `_PROPOSAL_ONLY_KEYS` ([src/learnloop/content/synthesis/synthesis_gates.py](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 841)
- `ATTACH_GROWABLE_FIELDS` ([src/learnloop/content/synthesis/synthesis_gates.py](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 847)
- `_GATES` ([src/learnloop/content/synthesis/synthesis_gates.py](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 937)

## Internal implementation anchors

- `_gate_span_resolution(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 200)
- `_gate_scope(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 223)
- `_gate_unit_id_validity(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 242)
- `_gate_citation_scope(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 267) — A citation outside the selected scope supports nothing (Codex verification of F6).
- `_hard_failed_citation(ref: ProvenanceRef, ctx: GateContext) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 295) — Whether the span/scope/unit gates already fail this citation.
- `_gate_conflict_disposition(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 309)
- `_gate_lock_guard(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 331)
- `_lock_reason_for(item: GateItem, ctx: GateContext) -> str | None` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 350) — Delegate to can_apply when a vault/repository is wired, else use the item's injected lock_reason.
- `_gate_adequate_provenance(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 375)
- `_has_semantic_authority(item: GateItem) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 397)
- `_known_facet_references(proposal: GateProposal, ctx: GateContext) -> set[str]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 403) — Facet ids a reference may name: registered, proposed, or an alias of either.
- `_gate_criterion_targets_dag(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 426)
- `_gate_recipe_validity(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 475)
- `_gate_dependency_closure(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 561)
- `_gate_exam_authority(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 592)
- `_gate_held_out_leakage(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 616)
- `_gate_token_truncation(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 637)
- `_gate_practice_exam_only(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 660)
- `_gate_duplicate_ids_dangling(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 681)
- `_endpoint_known(endpoint: str, proposal: GateProposal) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 727)
- `_cosine_note(ctx: GateContext, left: Any, right: Any) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 734) — ``", cosine 0.91"`` beside the Jaccard, when T5 vectors exist (display only).
- `_gate_near_duplicate_facets(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 746)
- `_gate_append_vocabulary(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 791) — Append vocabulary gate (§10.2/§10.3).
- `_is_alias_only_facet_append(item: GateItem, ctx: GateContext) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 850) — Is this a D2 alias registration — provably additive, so append-legal?
- `_default_identifiability(proposal: GateProposal, ctx: GateContext) -> list[GateDiagnostic]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 896) — Degenerate identifiability check (SEAM for KM5's §11.3 doctor).
- `_criteria_of(item: GateItem) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 961)
- `_blueprints_of(item: GateItem) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 971)
- `_facet_tokens(payload: dict[str, Any]) -> set[str]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 978)
- `_facet_signature(payload: dict[str, Any]) -> tuple[str, ...]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 983)
- `_text_tokens(text: str) -> set[str]` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 991)
- `_jaccard(left: set[str], right: set[str]) -> float` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 995)
- `_first_cycle(graph: dict[str, Iterable[str]]) -> list[str] | None` ([source](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py), line 1016)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `GateDiagnostic`; statically calls `GateDiagnostic`
- [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] — imports `ProvenanceRef`; statically calls `ProvenanceRef`
- [[Reference/Modules/learnloop/content/facet_identity/grouping|learnloop.content.facet_identity.grouping]] — imports `facet_tokens`, `jaccard`; statically calls `facet_tokens`, `jaccard`
- [[Reference/Modules/learnloop/content/facet_identity/plan|learnloop.content.facet_identity.plan]] — imports `facet_tokens`, `jaccard`; statically calls `facet_tokens`, `jaccard`
- [[Reference/Modules/learnloop/content/synthesis/facet_mint_gate|learnloop.content.synthesis.facet_mint_gate]] — imports `facet_tokens`, `jaccard`; statically calls `facet_tokens`, `jaccard`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `ASSESSMENT_ONLY_ROLES`, `GateItem`, `GateProposal`, `ProvenanceRef`, `run_synthesis_gates`; statically calls `GateItem`, `GateProposal`, `run_synthesis_gates`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `ATTACH_GROWABLE_FIELDS`, `GateContext`, `GateDiagnostic`, `GateItem`, `GateProposal`, `ProvenanceRef`, `run_synthesis_gates`; statically calls `GateContext`, `GateDiagnostic`, `GateItem`, `GateProposal`, `ProvenanceRef`, `run_synthesis_gates`
- [[Reference/Modules/learnloop/curriculum/depth_edge_authoring|learnloop.curriculum.depth_edge_authoring]] — imports `GateDiagnostic`; statically calls `GateDiagnostic`
- [[Reference/Modules/learnloop/curriculum/depth_rungs|learnloop.curriculum.depth_rungs]] — imports `GateDiagnostic`; statically calls `GateDiagnostic`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/role_authority|learnloop.content.sources.role_authority]] — imports `ASSESSMENT_ONLY_ROLES`, `EXAM_UNCORROBORATED`, `EXPLANATORY`, `support_verdict`; calls `support_verdict`
- [[Reference/Modules/learnloop/curriculum/curriculum_locks|learnloop.curriculum.curriculum_locks]] — imports `Operation`, `can_apply`; calls `Operation`, `can_apply`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]], [[Reference/Modules/learnloop/content/facet_identity/grouping|learnloop.content.facet_identity.grouping]], [[Reference/Modules/learnloop/content/facet_identity/plan|learnloop.content.facet_identity.plan]], [[Reference/Modules/learnloop/content/synthesis/facet_mint_gate|learnloop.content.synthesis.facet_mint_gate]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_facet_authority.py](../../../../../../../tests/test_facet_authority.py) — direct import
  - `test_a_notes_citation_never_corroborates_exam_material_at_the_gate`
- [tests/test_facet_identity.py](../../../../../../../tests/test_facet_identity.py) — direct import
  - `test_judge_writes_one_ledger_row_per_pair_and_never_pays_twice`
- [tests/test_facet_identity_composition.py](../../../../../../../tests/test_facet_identity_composition.py) — direct import
  - `test_the_ledger_records_merged_pairs_and_shortlisted_different_pairs_only`
- [tests/test_facet_identity_ingest.py](../../../../../../../tests/test_facet_identity_ingest.py) — direct import
  - `test_revalidation_replays_the_plan_without_a_judge_call`
  - `test_revalidation_with_the_switch_off_replays_no_stored_plan`
  - `test_the_alias_only_append_gate_refuses_a_precondition_growth`
  - `test_the_gate_knows_aliases_only_while_facet_identity_is_on`
- [tests/test_facet_rewords.py](../../../../../../../tests/test_facet_rewords.py) — direct import
  - `test_the_gate_lets_a_facet_update_through_and_still_guards_a_practised_learning_object`
- [tests/test_graph_nomination.py](../../../../../../../tests/test_graph_nomination.py) — direct import
  - `test_synthesis_gate_and_facet_candidates_show_cosine_beside_jaccard`
- [tests/test_source_append.py](../../../../../../../tests/test_source_append.py) — direct import
  - `test_append_vocabulary_gate_rejects_mutation_outside_restructure`
- [tests/test_synthesis_gates.py](../../../../../../../tests/test_synthesis_gates.py) — direct import
  - `test_clean_proposal_passes_all_gates`
  - `test_each_gate_emits_typed_diagnostic`
  - `test_exam_authority_allows_manual_override`
  - `test_report_separates_hard_fail_and_review`

## Modification guidance

- Change synthesis gates policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/synthesis_gates.py](../../../../../../../src/learnloop/content/synthesis/synthesis_gates.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

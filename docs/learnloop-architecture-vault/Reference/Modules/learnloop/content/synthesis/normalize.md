---
title: "learnloop.content.synthesis.normalize"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/normalize.py"
source_paths:
  - "src/learnloop/content/synthesis/normalize.py"
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
  - "learnloop.content.synthesis.normalize module"
  - "src/learnloop/content/synthesis/normalize.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.normalize`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.normalize` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: A synthesis answer into proposal rows: concepts, facets, learning objects, blueprints, practice items and concept edges, each as a row beside the gate item the synthesis gates read.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/normalize.py](../../../../../../../src/learnloop/content/synthesis/normalize.py) |
| Source lines | 1597 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Normalized` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 55)
- `normalize(synth: Any, inputs: Any, vault: LoadedVault, now: str, *, subject_id: str, items_off: bool=False, nominator: Any=None, facet_identity_plan: Any=None) -> Normalized` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 1568) — The proposal rows, gate items and diagnostics of one synthesis answer; the module docstring gives the order.

## Internal implementation anchors

- `_slug(prefix: str, text: str, fallback: str) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 49)
- `_dump(obj: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 79)
- `class _NormalizeState` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 84) — What the stages share: the inputs, the id maps, the rows and gate items built so far, and the diagnostics.
- `_span_refs(refs: list[Any], inputs: Any, *, default_relation: str) -> tuple[list[ProvenanceRef], list[dict[str, Any]], list[str]]` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 164) — Build gate ProvenanceRefs + YAML source_refs from synth span refs.
- `_unresolved_citations(gate_refs: list[ProvenanceRef]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 225) — The citations of a candidate that did not resolve, by their ids (they support nothing).
- `_joined_contribution(candidate: Mapping[str, Any]) -> facet_meaning.Contribution` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 236) — What a retired candidate offers the survivor its meaning joins (in-run consolidation or attach).
- `_support_citations(gate_refs: list[ProvenanceRef]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 253) — The validated citations of a candidate, as a proposal's ``meaning_support`` carries them.
- `_facet_identity_actions(retired_targets: Mapping[str, tuple[str, str, Any, dict[str, Any]]], *, pre_union: Mapping[str, dict[str, Any]], minted_payload_by_id: Mapping[str, dict[str, Any]], registered_before: Mapping[str, dict[str, Any]], rows: Sequence[Mapping[str, Any]], vault: LoadedVault, aliased: set[str] | None=None, contract_notes: Mapping[str, Sequence[str]] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 264) — One undoable action per survivor the proposal changes (facet identity).
- `_keep_sibling_criterion_dependencies(item_id: str, criteria: list[dict[str, Any]], dropped_diagnostics: list[dict[str, Any]]) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 359) — Keep each criterion's ``depends_on`` to sibling criterion ids (in place).
- `_method_target_view(vault: LoadedVault, rows: list[dict[str, Any]]) -> Any` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 410) — The registry plus this batch's concepts, facets and learning objects, as :func:`learnloop.vault.required_method.method_targets` reads them.
- `_row(item_type: str, entity_id: str, payload: dict[str, Any], depends_on: list[str], *, client_id: str, now: str, target_entity_id: str | None=None, target_entity_type: str | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 441)
- `_register_concept_reference(st: _NormalizeState, concept_id: str, *values: str) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 467)
- `_resolve_concept_reference(st: _NormalizeState, reference: str) -> tuple[str | None, str | None]` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 474)
- `_resolve_concept_references(st: _NormalizeState, *, learning_object_id: str, field_name: str, client_references: list[str], canonical_references: list[str]) -> tuple[list[str], list[str]]` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 488)
- `_mint_concept(st: _NormalizeState, *, title: str, description: str, learning_object_id: str, detail: str) -> tuple[str, str]` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 529) — Synthesize a concept so a learning object with no resolvable concept still lands (degraded fallback, §8.5).
- `_index_registry_concepts(st: _NormalizeState) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 570) — The registry's concepts resolve by id, title and alias, before any of the answer's are minted.
- `_concepts(st: _NormalizeState) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 577) — The answer's concepts, with ``unique`` ids; an untitled one takes a ULID-prefix id.
- `_facet_candidates(st: _NormalizeState) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 599) — Every facet as a candidate (payload, citations, support), none judged yet.
- `_facet_retirements(st: _NormalizeState) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 660) — Candidates facet identity retired leave the batch; an in-run survivor takes each retiree's meaning first.
- `_mint_gate(st: _NormalizeState) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 705) — The D2 mint gate's verdict on each remaining candidate: mint a row, alias into a neighbour, or drop a reword.
- `_retired_references(st: _NormalizeState) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 814) — A retired candidate's references follow its survivor; its id becomes the survivor's alias where it is free.
- `_register_aliases(st: _NormalizeState) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 856) — Add the collected aliases (and an attach's grown contract) to their targets: in place for a minted facet, through an `update` row for a registered one.
- `_identity_actions(st: _NormalizeState) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 965) — The undoable facet-identity actions, from the rows the stages above wrote.
- `_learning_objects(st: _NormalizeState) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 978) — Learning objects, each anchored to a concept (minted from its title when the answer's reference is lost).
- `_blueprints(st: _NormalizeState) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 1059) — Task blueprints, merged onto their learning object, their recipe components resolved to facet ids.
- `_practice_items(st: _NormalizeState) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 1205) — Practice items and their rubric criteria; under items-off the model's items are dropped, not trusted.
- `_reaches(adjacency: dict[str, set[str]], start: str, goal: str) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 1380)
- `_resolve_endpoint(st: _NormalizeState, reference: Any) -> str | None` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 1393)
- `_edge_review(st: _NormalizeState, message: str, refs: list[str], action: str) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 1404)
- `_add_concept_edge(st: _NormalizeState, source_ref: Any, target_ref: Any, relation_type: str, *, rationale: str, strength: float=1.0) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 1416)
- `_concept_edges(st: _NormalizeState) -> None` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 1497) — The model's explicit relations, then the floor derived from the learning objects' prerequisites and confusables.
- `_finalize(st: _NormalizeState) -> Normalized` ([source](../../../../../../../src/learnloop/content/synthesis/normalize.py), line 1541)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `Normalized`, `_dump`, `_row`, `_span_refs`, `_support_citations`, `normalize`; statically calls `_dump`, `_row`, `_span_refs`, `_support_citations`, `normalize`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `Normalized`, `normalize`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] — imports `module`; calls `CitationProblem`, `Contribution`, `check_meaning_write`, `join_candidate`, `meaning_policy`, `overlay`, `support_entries`
- [[Reference/Modules/learnloop/content/facet_identity/views|learnloop.content.facet_identity.views]] — imports `UNION_LIST_FIELDS`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `compute_target_hash`; calls `compute_target_hash`
- [[Reference/Modules/learnloop/content/synthesis/facet_mint_gate|learnloop.content.synthesis.facet_mint_gate]] — imports `MintDisposition`, `judge_facet_mints`, `mint_diagnostic`; calls `judge_facet_mints`, `mint_diagnostic`
- [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] — imports `annotate_mint_report`; calls `annotate_mint_report`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_gates|learnloop.content.synthesis.synthesis_gates]] — imports `ATTACH_GROWABLE_FIELDS`, `GateItem`, `ProvenanceRef`; calls `GateItem`, `ProvenanceRef`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`, `snake_case`; calls `new_ulid`, `snake_case`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `advisory_statement_flag`, `method_targets`, `normalize_required_method`; calls `advisory_statement_flag`, `method_targets`, `normalize_required_method`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `copy`, `dataclasses`, `types`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/facet_authority_helpers.py](../../../../../../../tests/facet_authority_helpers.py) — direct import
- [tests/normalize_helpers.py](../../../../../../../tests/normalize_helpers.py) — direct import
- [tests/test_facet_authority.py](../../../../../../../tests/test_facet_authority.py) — direct import
  - `test_a_bootstrap_candidate_carrying_a_registered_id_rewords_it_uncited_only_with_the_owners_confirm`
  - `test_a_citations_locator_is_derived_from_its_validated_ids`
  - `test_a_cited_bootstrap_candidate_carrying_a_registered_id_rewords_it_as_a_checked_update`
  - `test_citations_take_the_units_role_override`
- [tests/test_facet_reword_confirm.py](../../../../../../../tests/test_facet_reword_confirm.py) — direct import
  - `test_a_bootstrap_candidate_carrying_a_registered_id_uncited_is_kept_for_confirm`
  - `test_a_bootstrap_reword_citing_exam_material_under_the_wrong_unit_is_dropped_not_held`
  - `test_an_exam_only_bootstrap_candidate_carrying_a_registered_id_is_dropped_not_held`
- [tests/test_required_method_items.py](../../../../../../../tests/test_required_method_items.py) — direct import
  - `test_synthesis_keeps_a_required_method_only_on_a_procedure_target`

## Modification guidance

- Change normalize policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/normalize.py](../../../../../../../src/learnloop/content/synthesis/normalize.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

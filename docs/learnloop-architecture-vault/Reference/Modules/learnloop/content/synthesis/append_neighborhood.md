---
title: "learnloop.content.synthesis.append_neighborhood"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/append_neighborhood.py"
source_paths:
  - "src/learnloop/content/synthesis/append_neighborhood.py"
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
  - "learnloop.content.synthesis.append_neighborhood module"
  - "src/learnloop/content/synthesis/append_neighborhood.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.append_neighborhood`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.append_neighborhood` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Deterministic, reviewable affected-neighborhood selection for append (ING M7).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/append_neighborhood.py](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py) |
| Source lines | 544 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class MatchReason` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 72)
- `class Neighborhood` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 79) — The bounded existing-map neighborhood sent to append reconciliation.
  - `as_context(self) -> dict[str, Any]` (line 105; public) — The compact dict placed in the reconciliation prompt context.
  - `as_manifest_record(self) -> dict[str, Any]` (line 120; public)
  - `entity_refs(self) -> set[str]` (line 133; public)
- `extract_new_signals(new_inventories: list[dict[str, Any]], *, source_ids: Iterable[str]=(), revision_ids: Iterable[str]=()) -> _NewSignals` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 156) — Pull the deterministic match signals out of the new/changed inventories.
- `select_neighborhood(vault: LoadedVault, repository: Repository, new_inventories: list[dict[str, Any]], *, budget_tokens: int, source_ids: Iterable[str]=(), revision_ids: Iterable[str]=(), fingerprint_threshold: float=0.25, loose_threshold: float=0.12, nominator: Any=None) -> Neighborhood` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 208) — Select the bounded affected-map neighborhood (deterministic, §10.1/§3.2).

### Module constants

- `_TOKEN_RE` ([src/learnloop/content/synthesis/append_neighborhood.py](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 43)
- `_STOPWORDS` ([src/learnloop/content/synthesis/append_neighborhood.py](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 44)

## Internal implementation anchors

- `_tokens(text: str) -> set[str]` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 53)
- `_jaccard(left: set[str], right: set[str]) -> float` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 57)
- `_estimate_tokens(obj: Any) -> int` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 64)
- `class _NewSignals` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 141)
- `_hash_entity(payload: dict[str, Any]) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 203)
- `_embedding_reasons(nominator: Any, new_inventories: list[dict[str, Any]]) -> dict[str, MatchReason]` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 308) — The top-k definition-embedding neighbours of the new material (T5).
- `_provenance_matched_entities(repository: Repository, signals: _NewSignals) -> dict[str, MatchReason]` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 353)
- `_unresolved_candidates(signals: _NewSignals, scored: dict[str, tuple[float, list[MatchReason]]]) -> list[str]` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 373) — Concept names in the new inventory that matched no existing entity yet.
- `_materialize(vault: LoadedVault, repository: Repository, ordered: list[tuple[str, tuple[float, list[MatchReason]]]], *, budget_tokens: int, rounds: int) -> Neighborhood` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 383)
- `_facet_contract(facet: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py), line 532)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `select_neighborhood`; statically calls `select_neighborhood`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] — imports `CONCEPT_RECIPE`, `FACET_RECIPE`, `inventory_queries`, `undefined_concept_mentions`; calls `inventory_queries`, `undefined_concept_mentions`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `hashlib`, `json`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_graph_nomination.py](../../../../../../../tests/test_graph_nomination.py) — direct import
  - `test_append_neighbourhood_unions_embedding_nominations_after_lexical`
  - `test_append_neighbourhood_without_vectors_is_the_lexical_selection`
  - `test_concept_queries_carry_their_linked_definitions`
  - `test_dry_run_counts_the_calls_each_query_group_sends`
- [tests/test_source_append.py](../../../../../../../tests/test_source_append.py) — direct import
  - `test_append_context_bounded_by_neighborhood`
  - `test_planted_full_map_resend_fails_scaling_gate`

## Modification guidance

- Change append neighborhood policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/append_neighborhood.py](../../../../../../../src/learnloop/content/synthesis/append_neighborhood.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

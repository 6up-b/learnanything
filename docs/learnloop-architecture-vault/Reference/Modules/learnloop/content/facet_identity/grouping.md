---
title: "learnloop.content.facet_identity.grouping"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/facet_identity/grouping.py"
source_paths:
  - "src/learnloop/content/facet_identity/grouping.py"
source_commit: "c427afc433d21bf4c3097c18abe85be9051eeb35"
source_commit_timestamp: "2026-10-13T01:31:57-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.facet_identity"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.facet_identity.grouping module"
  - "src/learnloop/content/facet_identity/grouping.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-facet-identity"
---

# `learnloop.content.facet_identity.grouping`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.facet_identity.grouping` exists within [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] to own the behavior summarized by its module contract: Concept neighbourhoods of facets: the groups one judge call partitions.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/facet_identity/grouping.py](../../../../../../../src/learnloop/content/facet_identity/grouping.py) |
| Source lines | 307 |
| Owning package | [[Reference/Modules/learnloop/content/facet_identity/_package|learnloop.content.facet_identity]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `c427afc433d21bf4c3097c18abe85be9051eeb35` |
| Commit timestamp | `2026-10-13T01:31:57-04:00` |

## Public API

- `class FacetNode` ([source](../../../../../../../src/learnloop/content/facet_identity/grouping.py), line 38) — One facet in scope: a registered facet or a run candidate.
- `class Grouping` ([source](../../../../../../../src/learnloop/content/facet_identity/grouping.py), line 48)
  - `summary(self) -> dict[str, Any]` (line 60; public)
- `centred_unit(vectors: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]` ([source](../../../../../../../src/learnloop/content/facet_identity/grouping.py), line 92) — Mean-centred unit rows over the given set (Slice 1 §9.2 maths).
- `shortlist_pairs(unit: Mapping[str, np.ndarray], *, top_k: int, eligible: set[str] | None=None) -> list[tuple[str, str, float, int]]` ([source](../../../../../../../src/learnloop/content/facet_identity/grouping.py), line 109) — Each facet's top-k neighbours: (query, neighbour, cosine, rank).
- `neighbourhood_groups(nodes: Sequence[FacetNode], *, concept_edges: Iterable[tuple[str, str]]=(), extra_pairs: Iterable[tuple[str, str]]=(), vectors: Mapping[str, np.ndarray] | None=None, top_k: int=4, max_group_size: int=40, lexical_threshold: float=DEFAULT_LEXICAL_THRESHOLD, shortlist_edges: bool=True) -> Grouping` ([source](../../../../../../../src/learnloop/content/facet_identity/grouping.py), line 125) — Connected concept neighbourhoods, bounded to ``max_group_size``.

### Module constants

- `DEFAULT_LEXICAL_THRESHOLD` ([src/learnloop/content/facet_identity/grouping.py](../../../../../../../src/learnloop/content/facet_identity/grouping.py), line 34)

### Explicit exports

`__all__` declares:

- `DEFAULT_LEXICAL_THRESHOLD`
- `FacetNode`
- `Grouping`
- `centred_unit`
- `neighbourhood_groups`
- `shortlist_pairs`

## Internal implementation anchors

- `class _Union` ([source](../../../../../../../src/learnloop/content/facet_identity/grouping.py), line 72)
- `_agglomerate(members: list[str], unit: Mapping[str, np.ndarray], cap: int) -> list[list[str]]` ([source](../../../../../../../src/learnloop/content/facet_identity/grouping.py), line 211) — Average-link clustering under a size cap (deterministic), heap-based.
- `_pack_by_concept(members: list[str], by_key: Mapping[str, FacetNode], adjacency: Mapping[str, set[str]], cap: int) -> list[list[str]]` ([source](../../../../../../../src/learnloop/content/facet_identity/grouping.py), line 259) — Whole concepts packed in concept-graph order; huge concepts are chunked.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/facet_identity/dedupe|learnloop.content.facet_identity.dedupe]] — imports `FacetNode`, `neighbourhood_groups`; statically calls `FacetNode`, `neighbourhood_groups`
- [[Reference/Modules/learnloop/content/facet_identity/plan|learnloop.content.facet_identity.plan]] — imports `FacetNode`, `neighbourhood_groups`; statically calls `FacetNode`, `neighbourhood_groups`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/synthesis/synthesis_gates|learnloop.content.synthesis.synthesis_gates]] — imports `facet_tokens`, `jaccard`; calls `facet_tokens`, `jaccard`
- [[Reference/Modules/learnloop/matching/shortlist|learnloop.matching.shortlist]] — imports `module`; calls `centred_unit`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `heapq`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/facet_identity/dedupe|learnloop.content.facet_identity.dedupe]], [[Reference/Modules/learnloop/content/facet_identity/plan|learnloop.content.facet_identity.plan]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_facet_identity.py](../../../../../../../tests/test_facet_identity.py) — direct import
  - `test_a_neighbourhood_of_hundreds_of_facets_splits_in_seconds`
  - `test_an_oversized_neighbourhood_is_split_and_every_facet_lands_once`
  - `test_neighbourhoods_link_concepts_graph_lexical_and_the_embedding_shortlist`
  - `test_the_heap_split_matches_the_reference_average_link`
  - `test_the_regression_neighbourhood_holds_every_merge_worthy_pair`
- [tests/test_facet_identity_composition.py](../../../../../../../tests/test_facet_identity_composition.py) — direct import
  - `test_facet_grouping_centres_vectors_with_matchings_shortlist_maths`
  - `test_the_ledger_records_merged_pairs_and_shortlisted_different_pairs_only`

## Modification guidance

- Change grouping policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/facet_identity/grouping.py](../../../../../../../src/learnloop/content/facet_identity/grouping.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.matching.shortlist"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/matching/shortlist.py"
source_paths:
  - "src/learnloop/matching/shortlist.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.matching"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.matching.shortlist module"
  - "src/learnloop/matching/shortlist.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-matching"
---

# `learnloop.matching.shortlist`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/matching/_package|learnloop.matching]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.matching.shortlist` exists within [[Reference/Modules/learnloop/matching/_package|learnloop.matching]] to own the behavior summarized by its module contract: Embeddings shortlist candidate pairs; they never decide (Slice 2 R1, R4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/matching/shortlist.py](../../../../../../src/learnloop/matching/shortlist.py) |
| Source lines | 303 |
| Owning package | [[Reference/Modules/learnloop/matching/_package|learnloop.matching]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class CandidatePair` ([source](../../../../../../src/learnloop/matching/shortlist.py), line 47)
- `class Shortlist` ([source](../../../../../../src/learnloop/matching/shortlist.py), line 57)
  - `summary(self) -> dict[str, Any]` (line 73; public)
- `class ModelActivation` ([source](../../../../../../src/learnloop/matching/shortlist.py), line 91) — Which stored model ranks a kind's subjects, and why (Slice 1 §9.6).
  - `summary(self) -> dict[str, Any]` (line 100; public)
- `active_model(connection: sqlite3.Connection, kind: MatchKind, subjects: Sequence[Subject], *, configured: str) -> ModelActivation` ([source](../../../../../../src/learnloop/matching/shortlist.py), line 110) — The configured model once its backfill covers what the others cover, else the previous one.
- `stored_width(connection: sqlite3.Connection, kind: MatchKind, *, model_id: str) -> int | None` ([source](../../../../../../src/learnloop/matching/shortlist.py), line 134) — The width of a model's stored vectors for this kind (one per model).
- `compatible_cutoff(entry: Any, kind: MatchKind, *, model_id: str, dims: int | None) -> tuple[float | None, str, str | None]` ([source](../../../../../../src/learnloop/matching/shortlist.py), line 146) — (cutoff, basis, refusal) for a configured benchmark cutoff entry.
- `stored_vectors(connection: sqlite3.Connection, kind: MatchKind, subjects: Sequence[Subject], *, model_id: str, identity: EmbeddingIdentity | None=None) -> dict[str, np.ndarray]` ([source](../../../../../../src/learnloop/matching/shortlist.py), line 171) — Current vectors (content hash matches) for these subjects, by subject id.
- `unit_rows(vectors: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]` ([source](../../../../../../src/learnloop/matching/shortlist.py), line 200) — Unit-length rows, not centred (asymmetric kinds: two prompt spaces).
- `centred_unit(vectors: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]` ([source](../../../../../../src/learnloop/matching/shortlist.py), line 211) — Mean-centred, unit-length rows over the given set (Slice 1 §9.2).
- `shortlist_pairs(connection: sqlite3.Connection, kind: MatchKind, *, queries: Sequence[Subject], pool: Sequence[Subject], model_id: str, top_k: int, cutoff: float | None, compatible: Callable[[Subject, Subject], bool], settled: Callable[[Subject, Subject], bool] | None=None, centre_over: Sequence[Subject] | None=None, query_vectors: Mapping[str, np.ndarray] | None=None) -> Shortlist` ([source](../../../../../../src/learnloop/matching/shortlist.py), line 227) — Top-k compatible, unsettled pool neighbours of each query.

### Explicit exports

`__all__` declares:

- `CandidatePair`
- `ModelActivation`
- `Shortlist`
- `active_model`
- `centred_unit`
- `compatible_cutoff`
- `shortlist_pairs`
- `stored_vectors`
- `stored_width`
- `unit_rows`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/facet_identity/grouping|learnloop.content.facet_identity.grouping]] — imports `module`; statically calls `centred_unit`
- [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]] — imports `CandidatePair`; statically calls `CandidatePair`
- [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]] — imports `Shortlist`, `active_model`, `compatible_cutoff`, `shortlist_pairs`, `stored_width`; statically calls `Shortlist`, `active_model`, `compatible_cutoff`, `shortlist_pairs`, `stored_width`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/candidates|learnloop.diagnosis.text_gaps.candidates]] — imports `CandidatePair`, `shortlist_pairs`, `stored_vectors`; statically calls `CandidatePair`, `shortlist_pairs`, `stored_vectors`
- [[Reference/Modules/learnloop/matching/__init__|learnloop.matching]] — imports `CandidatePair`, `Shortlist`, `shortlist_pairs`
- [[Reference/Modules/learnloop/matching/judge|learnloop.matching.judge]] — imports `CandidatePair`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] — imports `current_records_by_model`; calls `current_records_by_model`
- [[Reference/Modules/learnloop/matching/kinds|learnloop.matching.kinds]] — imports `EmbeddingIdentity`, `MatchKind`, `Subject`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `sqlite3`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/facet_identity/grouping|learnloop.content.facet_identity.grouping]], [[Reference/Modules/learnloop/diagnosis/recurrence/guard|learnloop.diagnosis.recurrence.guard]], [[Reference/Modules/learnloop/diagnosis/recurrence/judging|learnloop.diagnosis.recurrence.judging]], [[Reference/Modules/learnloop/diagnosis/text_gaps/candidates|learnloop.diagnosis.text_gaps.candidates]], [[Reference/Modules/learnloop/matching/__init__|learnloop.matching]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_facet_identity_composition.py](../../../../../../tests/test_facet_identity_composition.py) — direct import
  - `test_facet_grouping_centres_vectors_with_matchings_shortlist_maths`
- [tests/test_matching.py](../../../../../../tests/test_matching.py) — direct import
  - `test_a_cutoff_applies_only_to_the_vectors_it_was_measured_on`
  - `test_a_partially_backfilled_replacement_model_never_ranks`
- [tests/test_tier1_decider.py](../../../../../../tests/test_tier1_decider.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains shortlist within learnloop.matching; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/matching/shortlist.py](../../../../../../src/learnloop/matching/shortlist.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

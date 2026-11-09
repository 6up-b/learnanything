---
title: "learnloop.practice_index.text"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/practice_index/text.py"
source_paths:
  - "src/learnloop/practice_index/text.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.practice_index"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.practice_index.text module"
  - "src/learnloop/practice_index/text.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-practice-index"
---

# `learnloop.practice_index.text`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.practice_index.text` exists within [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] to own the behavior summarized by its module contract: Keyword search and rank fusion for the practice index (no model calls).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/practice_index/text.py](../../../../../../src/learnloop/practice_index/text.py) |
| Source lines | 96 |
| Owning package | [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `tokenize(text: str) -> list[str]` ([source](../../../../../../src/learnloop/practice_index/text.py), line 24) — Lowercased alphanumeric tokens, stopwords removed, plural 's' folded.
- `class BM25` ([source](../../../../../../src/learnloop/practice_index/text.py), line 37) — Okapi BM25 over a fixed document collection.
  - `__init__(self, documents: Mapping[str, str], *, k1: float=1.2, b: float=0.75)` (line 40; internal)
  - `scores(self, query: str, candidates: Iterable[str] | None=None) -> dict[str, float]` (line 55; public) — Positive scores only; documents sharing no query term are omitted.
  - `ranking(self, query: str, candidates: Iterable[str] | None=None) -> list[str]` (line 75; public)
- `reciprocal_rank_fusion(rankings: Mapping[str, Sequence[str]], *, k: int=60) -> tuple[list[str], dict[str, dict[str, int]]]` ([source](../../../../../../src/learnloop/practice_index/text.py), line 80) — Fuse ranked lists; returns the fused order and each id's per-list rank.

### Module constants

- `_TOKEN` ([src/learnloop/practice_index/text.py](../../../../../../src/learnloop/practice_index/text.py), line 16)
- `_STOPWORDS` ([src/learnloop/practice_index/text.py](../../../../../../src/learnloop/practice_index/text.py), line 17)

### Explicit exports

`__all__` declares:

- `BM25`
- `reciprocal_rank_fusion`
- `tokenize`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]] — imports `reciprocal_rank_fusion`; statically calls `reciprocal_rank_fusion`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `BM25`, `reciprocal_rank_fusion`; statically calls `BM25`, `reciprocal_rank_fusion`
- [[Reference/Modules/learnloop/source_retrieval/b4|learnloop.source_retrieval.b4]] — imports `BM25`, `reciprocal_rank_fusion`; statically calls `BM25`, `reciprocal_rank_fusion`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `reciprocal_rank_fusion`; statically calls `reciprocal_rank_fusion`
- [[Reference/Modules/learnloop/source_retrieval/suggest|learnloop.source_retrieval.suggest]] — imports `BM25`, `reciprocal_rank_fusion`; statically calls `BM25`, `reciprocal_rank_fusion`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `math`, `re`, `unicodedata`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/quick_add|learnloop.content.pipeline.quick_add]], [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]], [[Reference/Modules/learnloop/source_retrieval/b4|learnloop.source_retrieval.b4]], [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]], [[Reference/Modules/learnloop/source_retrieval/suggest|learnloop.source_retrieval.suggest]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/practice_index_fakes.py](../../../../../../tests/practice_index_fakes.py) — direct import
- [tests/source_retrieval_fakes.py](../../../../../../tests/source_retrieval_fakes.py) — direct import
- [tests/test_practice_index_text.py](../../../../../../tests/test_practice_index_text.py) — direct import
  - `test_bm25_ranks_overlap_and_omits_documents_without_it`
  - `test_reciprocal_rank_fusion_uses_ranks_and_breaks_ties_by_id`
  - `test_tokenizer_folds_case_plurals_and_request_boilerplate`

## Modification guidance

- Make changes here when the responsibility remains text within learnloop.practice_index; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/practice_index/text.py](../../../../../../src/learnloop/practice_index/text.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

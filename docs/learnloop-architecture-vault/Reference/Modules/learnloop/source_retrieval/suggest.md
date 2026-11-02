---
title: "learnloop.source_retrieval.suggest"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/suggest.py"
source_paths:
  - "src/learnloop/source_retrieval/suggest.py"
source_commit: "7ee17730cc8fb532f5e438aeda915444cf9609f2"
source_commit_timestamp: "2026-10-12T17:19:54-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.source_retrieval.suggest module"
  - "src/learnloop/source_retrieval/suggest.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.suggest`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.suggest` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: A labelled nearest-LO suggestion for a reader span without provenance (T6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/suggest.py](../../../../../../src/learnloop/source_retrieval/suggest.py) |
| Source lines | 151 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `7ee17730cc8fb532f5e438aeda915444cf9609f2` |
| Commit timestamp | `2026-10-12T17:19:54-04:00` |

## Public API

- `suggest_learning_objects(vault: LoadedVault, repository: Repository, *, extraction_id: str, span_id: str, limit: int=DEFAULT_LIMIT) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/suggest.py), line 95) — Provenance-linked LOs, or (when there are none) labelled nearest-LO suggestions.
- `suggested_learning_objects(vault: LoadedVault, repository: Repository, *, extraction_id: str, span_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/suggest.py), line 143) — The tutor's injection seam: the labelled suggestions only.

### Module constants

- `DEFAULT_LIMIT` ([src/learnloop/source_retrieval/suggest.py](../../../../../../src/learnloop/source_retrieval/suggest.py), line 43)

### Explicit exports

`__all__` declares:

- `DEFAULT_LIMIT`
- `suggest_learning_objects`
- `suggested_learning_objects`

## Internal implementation anchors

- `_active_learning_objects(vault: LoadedVault) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/suggest.py), line 46)
- `_facets_by_lo(vault: LoadedVault, learning_objects: dict[str, Any]) -> dict[str, set[str]]` ([source](../../../../../../src/learnloop/source_retrieval/suggest.py), line 50)
- `_lo_document(vault: LoadedVault, learning_object: Any, facets: Iterable[str]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/suggest.py), line 55)
- `_meaning_ranking(vault: LoadedVault, repository: Repository, block_text: str, record_id: str, facets_by_lo: dict[str, set[str]]) -> tuple[list[str], str]` ([source](../../../../../../src/learnloop/source_retrieval/suggest.py), line 64) — LOs ranked by their best facet's cosine to the span; ``(ranking, status)``.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]] — imports `suggest_learning_objects`; statically calls `suggest_learning_objects`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `suggest_learning_objects`, `suggested_learning_objects`; statically calls `suggest_learning_objects`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] — imports `IncompleteEmbeddingIndex`, `get_vector`, `retrieve`; calls `get_vector`, `retrieve`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `blocks_by_key`, `section_header_titles`; calls `blocks_by_key`, `section_header_titles`
- [[Reference/Modules/learnloop/practice_index/text|learnloop.practice_index.text]] — imports `BM25`, `reciprocal_rank_fusion`; calls `BM25`, `reciprocal_rank_fusion`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_for_span`; calls `learning_objects_for_span`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `DOC_TASK_PREFIX`, `SOURCE_BLOCK_FIELD`, `SOURCE_BLOCK_KIND`, `SOURCE_BLOCK_RECIPE`, `SOURCE_RETRIEVAL_RECIPES`, `block_record_id`, `source_block_text`; calls `block_record_id`, `source_block_text`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `EMBEDDING_RECIPES`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `learning_object_facet_union`; calls `learning_object_facet_union`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_source_retrieval_search.py](../../../../../../tests/test_source_retrieval_search.py) — direct import
  - `test_with_retrieval_off_reader_answers_carry_no_suggestion_field`
- [tests/test_source_retrieval_tutor.py](../../../../../../tests/test_source_retrieval_tutor.py) — direct import
  - `test_a_reader_question_records_the_suggestion_and_promotion_names_it`
  - `test_an_unmapped_span_gets_labelled_suggestions_never_candidates`
  - `test_suggestions_respect_provenance_and_the_switches`

## Modification guidance

- Make changes here when the responsibility remains suggest within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/suggest.py](../../../../../../src/learnloop/source_retrieval/suggest.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

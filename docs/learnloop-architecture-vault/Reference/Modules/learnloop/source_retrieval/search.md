---
title: "learnloop.source_retrieval.search"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/search.py"
source_paths:
  - "src/learnloop/source_retrieval/search.py"
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
  - "learnloop.source_retrieval.search module"
  - "src/learnloop/source_retrieval/search.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.search`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.search` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: Hybrid span retrieval: ranked lists fused by reciprocal rank (no thresholds).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/search.py](../../../../../../src/learnloop/source_retrieval/search.py) |
| Source lines | 607 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SpanHit` ([source](../../../../../../src/learnloop/source_retrieval/search.py), line 87)
  - `key(self) -> SpanKey` (line 104; public)
  - `record_id(self) -> str` (line 108; public)
  - `section(self) -> str | None` (line 112; public)
- `class SpanSearch` ([source](../../../../../../src/learnloop/source_retrieval/search.py), line 117)
  - `basis(self) -> str` (line 155; public) — Which kinds of evidence ranked the hits: keyword, meaning, rewrite.
  - `describe(self) -> dict[str, Any]` (line 169; public)
- `dense_plus_bm25(lists: Mapping[str, Sequence[str]], *, dense_k: int, extras_m: int, rrf_k: int, widening: Sequence[str]=('keyword',)) -> tuple[list[str], dict[str, str], dict[str, dict[str, int]]]` ([source](../../../../../../src/learnloop/source_retrieval/search.py), line 197) — The dense top ``dense_k`` then each widening list's top ``extras_m`` not already in the pool (deduplicated), in that order.
- `role_filter(vault: LoadedVault, repository: Repository, scope: Scope, roles: Sequence[str], *, eligible: Eligibility | None=None) -> tuple[set[SpanKey], dict[str, int]]` ([source](../../../../../../src/learnloop/source_retrieval/search.py), line 232) — The spans the ``roles`` positive filter permits in ``scope``, and its basis.
- `search_spans(vault: LoadedVault, repository: Repository, query: str, scope: Scope, *, limit: int=40, deep: bool=True, rewrite: bool | None=None, context_text: str | None=None, include_substring: bool=False, prefix_last: bool=False, extra_lists: Mapping[str, Sequence[SpanKey]] | None=None, embedder: Any | None=None, rewrite_client: Any | None=None, query_vectors: Mapping[str, np.ndarray] | None=None, rewritten: Rewrite | None=None, owner_id: str='', deadline: float | None=None, budget: SpendBudget | None=None, pool: str | None=None, pool_dense: int | None=None, pool_extras: int | None=None, roles: Sequence[str]=(), list_depth: int | Mapping[str, int]=LIST_DEPTH, eligible: Eligibility | None=None, consumer: str | None=None) -> SpanSearch` ([source](../../../../../../src/learnloop/source_retrieval/search.py), line 274) — Hybrid retrieval over ``scope``; never raises for a paid step's failure.

### Module constants

- `LIST_DEPTH` ([src/learnloop/source_retrieval/search.py](../../../../../../src/learnloop/source_retrieval/search.py), line 75)
- `POOL_HYBRID_RRF` ([src/learnloop/source_retrieval/search.py](../../../../../../src/learnloop/source_retrieval/search.py), line 78)
- `POOL_DENSE_PLUS_BM25` ([src/learnloop/source_retrieval/search.py](../../../../../../src/learnloop/source_retrieval/search.py), line 79)
- `POOL_MODES` ([src/learnloop/source_retrieval/search.py](../../../../../../src/learnloop/source_retrieval/search.py), line 80)
- `_NON_WIDENING` ([src/learnloop/source_retrieval/search.py](../../../../../../src/learnloop/source_retrieval/search.py), line 83)

### Explicit exports

`__all__` declares:

- `LIST_DEPTH`
- `POOL_DENSE_PLUS_BM25`
- `POOL_HYBRID_RRF`
- `POOL_MODES`
- `SpanHit`
- `SpanKey`
- `SpanSearch`
- `dense_plus_bm25`
- `role_filter`
- `search_spans`

## Internal implementation anchors

- `_hit(block: BlockRow, scope: Scope, ranks: Mapping[str, int], titles: Mapping[str, str], pool_role: str | None=None) -> SpanHit` ([source](../../../../../../src/learnloop/source_retrieval/search.py), line 182)
- `_ms(started: float) -> int` ([source](../../../../../../src/learnloop/source_retrieval/search.py), line 193)
- `_resolved_meaning(vault: LoadedVault, repository: Repository, scope: Scope, result: SpanSearch, lists: dict[str, list[SpanKey]], *, index: DenseIndex, retrieval_text: str, rewrite_result: Rewrite | None, keep: Any, depth: Any, embedder: Any, owner_id: str, budget: SpendBudget | None, deadline: float | None, query_vectors: Mapping[str, np.ndarray] | None, consumer: str, kind: str) -> Any` ([source](../../../../../../src/learnloop/source_retrieval/search.py), line 518) — The meaning lists through the space resolver (spec §5): each contributing space ranks its own extractions, the rankings fuse by rank.
- `_log_delivery(vault: LoadedVault, repository: Repository, result: SpanSearch, resolution: Any, *, owner_id: str) -> None` ([source](../../../../../../src/learnloop/source_retrieval/search.py), line 577) — The query receipt of one resolved search, with its candidates' ranks (never fails the search).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `POOL_HYBRID_RRF`, `search_spans`; statically calls `search_spans`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `search_spans`; statically calls `search_spans`
- [[Reference/Modules/learnloop/instructional/exercises|learnloop.instructional.exercises]] — imports `POOL_HYBRID_RRF`, `SpanSearch`, `search_spans`; statically calls `search_spans`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `SpanHit`, `search_spans`; statically calls `SpanHit`, `search_spans`
- [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]] — imports `POOL_DENSE_PLUS_BM25`, `POOL_HYBRID_RRF`, `SpanHit`, `search_spans`; statically calls `search_spans`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `POOL_HYBRID_RRF`, `SpanHit`, `SpanKey`, `role_filter`, `search_spans`; statically calls `role_filter`, `search_spans`
- [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]] — imports `search_spans`; statically calls `search_spans`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `search_spans`; statically calls `search_spans`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `search_spans`; statically calls `search_spans`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `SpanHit`, `SpanKey`, `SpanSearch`, `search_spans`; statically calls `SpanHit`, `search_spans`
- [[Reference/Modules/learnloop/source_retrieval/verify|learnloop.source_retrieval.verify]] — imports `SpanHit`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `BlockRow`, `blocks_by_key`, `search_blocks`, `section_header_titles`; calls `blocks_by_key`, `search_blocks`, `section_header_titles`
- [[Reference/Modules/learnloop/practice_index/query_vectors|learnloop.practice_index.query_vectors]] — imports `normalize_query`; calls `normalize_query`
- [[Reference/Modules/learnloop/practice_index/text|learnloop.practice_index.text]] — imports `reciprocal_rank_fusion`; calls `reciprocal_rank_fusion`
- [[Reference/Modules/learnloop/reader/source_roles|learnloop.reader.source_roles]] — imports `positive_filter_enabled`; calls `positive_filter_enabled`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `Eligibility`, `Scope`, `effective_eligibility`, `role_keys`, `role_proposal_keys`; calls `effective_eligibility`, `role_keys`, `role_proposal_keys`
- [[Reference/Modules/learnloop/source_retrieval/dense|learnloop.source_retrieval.dense]] — imports `DenseIndex`, `load_dense_index`; calls `DenseIndex`, `load_dense_index`
- [[Reference/Modules/learnloop/source_retrieval/feedback|learnloop.source_retrieval.feedback]] — imports `module`; calls `log_search`, `new_receipt_id`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `MAX_QUERY_CHARS`, `Rewrite`, `embed_query_texts`, `is_conceptual`, `rewrite_query`, `rewritten_text`; calls `embed_query_texts`, `is_conceptual`, `rewrite_query`, `rewritten_text`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `block_record_id`, `section_path`, `split_record_id`; calls `block_record_id`, `section_path`, `split_record_id`
- [[Reference/Modules/learnloop/source_retrieval/spaces|learnloop.source_retrieval.spaces]] — imports `meaning_lists`, `query_kind`, `resolve_source_spaces`, `resolver_active`, `space_ranks`; calls `meaning_lists`, `query_kind`, `resolve_source_spaces`, `resolver_active`, `space_ranks`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `time`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]], [[Reference/Modules/learnloop/instructional/exercises|learnloop.instructional.exercises]], [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]], [[Reference/Modules/learnloop/source_retrieval/evaluation|learnloop.source_retrieval.evaluation]] and 6 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_exercise_arm.py](../../../../../../tests/test_exercise_arm.py) — direct import
  - `test_the_positive_role_filter_keeps_only_effective_exercise_blocks`
- [tests/test_query_student.py](../../../../../../tests/test_query_student.py) — direct import
- [tests/test_reader_ca4_table_by_point.py](../../../../../../tests/test_reader_ca4_table_by_point.py) — direct import
- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
- [tests/test_section_coverage_review.py](../../../../../../tests/test_section_coverage_review.py) — direct import
  - `test_f3_a_failed_qwen_query_still_searches_deep`
- [tests/test_source_retrieval_followup.py](../../../../../../tests/test_source_retrieval_followup.py) — direct import
  - `test_search_spans_builds_the_pool_and_ranks_it_dense_first`
  - `test_the_pool_is_the_dense_top_k_then_bm25_extras_dense_missed`
  - `test_without_a_complete_dense_index_the_pool_is_todays_hybrid`
- [tests/test_source_retrieval_guards.py](../../../../../../tests/test_source_retrieval_guards.py) — direct import
  - `test_an_exam_reimport_is_excluded_whatever_revision_the_set_pins`
  - `test_the_practice_question_is_never_the_retrieval_query`
- [tests/test_source_retrieval_search.py](../../../../../../tests/test_source_retrieval_search.py) — direct import
  - `test_a_failed_rewrite_degrades_to_the_unrewritten_search`
  - `test_a_metered_rewrite_without_a_price_is_skipped_not_guessed`
  - `test_a_new_import_leaves_meaning_search_on_for_the_embedded_sources`
  - `test_a_query_vector_of_another_width_is_noted_not_ranked`
  - `test_only_conceptual_questions_are_rewritten`
  - `test_teaching_scope_excludes_every_assessment_span`
  - `test_with_embeddings_off_the_index_is_not_read_and_nothing_is_embedded`
  - `test_without_a_complete_index_search_is_keyword_only_and_says_so`
- [tests/test_source_space_resolver.py](../../../../../../tests/test_source_space_resolver.py) — direct import
  - `test_a_cli_budget_has_room_for_every_query_encoder_and_the_rewrite`
  - `test_a_failed_query_hands_its_sources_to_an_available_fallback`
  - `test_the_fallback_query_spends_from_the_callers_budget_and_is_planned`
  - `test_the_fallback_serves_a_source_qwen_does_not_cover`
  - `test_the_local_space_reports_no_encoder_in_p1_and_serves_through_the_hook`
- [tests/test_t6_followup_review.py](../../../../../../tests/test_t6_followup_review.py) — direct import
  - `test_a_cached_verification_is_served_even_when_the_caps_are_spent`
  - `test_every_verification_attempt_is_admitted_under_the_shared_caps`

## Modification guidance

- Make changes here when the responsibility remains search within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/search.py](../../../../../../src/learnloop/source_retrieval/search.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

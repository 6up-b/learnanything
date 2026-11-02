---
title: "learnloop.source_retrieval.compare"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/compare.py"
source_paths:
  - "src/learnloop/source_retrieval/compare.py"
source_commit: "b237188353e28f65610a200a5439b20e69a4b61d"
source_commit_timestamp: "2026-11-01T13:47:46-05:00"
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
  - "learnloop.source_retrieval.compare module"
  - "src/learnloop/source_retrieval/compare.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.compare`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.compare` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: ``compare_sources``: syntopic retrieval as a first-class operation (spec_source_practice_and_probes_v1 §9.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/compare.py](../../../../../../src/learnloop/source_retrieval/compare.py) |
| Source lines | 875 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `b237188353e28f65610a200a5439b20e69a4b61d` |
| Commit timestamp | `2026-11-01T13:47:46-05:00` |

## Public API

- `class Contribution(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/compare.py), line 137)
- `class PairRelation(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/compare.py), line 144)
- `class SourceComparison(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/compare.py), line 153) — Per-source contributions and pairwise relations; deliberately no consensus field.
- `class PointCell(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/compare.py), line 161)
- `class ComparisonPoint(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/compare.py), line 168)
- `class SourceComparisonV2(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/compare.py), line 176) — Reader CA4: points, each with per-source cells and its pairs' relations; deliberately no consensus field.
- `class Comparison` ([source](../../../../../../src/learnloop/source_retrieval/compare.py), line 184)
  - `as_dict(self) -> dict[str, Any]` (line 201; public)
- `compare_sources(vault: LoadedVault, repository: Repository, query: str, *, caller: CallerContext, facet_ids: Sequence[str]=(), requested_perspectives: Sequence[str]=(), pinned_span_ids: Sequence[Any]=(), pinned_span_keys: Sequence[Any]=(), anchor_span_keys: Sequence[Any]=(), source_ids: Sequence[str]=(), by_point: bool=False, policy: str | None=None, deadline: float | None=None, client: Any | None=None, verify_client: Any | None=None, embedder: Any | None=None, clock: Clock | None=None) -> Comparison` ([source](../../../../../../src/learnloop/source_retrieval/compare.py), line 235)

### Module constants

- `COMPARE_PROMPT_VERSION` ([src/learnloop/source_retrieval/compare.py](../../../../../../src/learnloop/source_retrieval/compare.py), line 96)
- `COMPARE_PROMPT_VERSION_V2` ([src/learnloop/source_retrieval/compare.py](../../../../../../src/learnloop/source_retrieval/compare.py), line 98)
- `KEYS_PER_SOURCE` ([src/learnloop/source_retrieval/compare.py](../../../../../../src/learnloop/source_retrieval/compare.py), line 103)
- `VERIFY_PAGE` ([src/learnloop/source_retrieval/compare.py](../../../../../../src/learnloop/source_retrieval/compare.py), line 104)
- `PASSAGE_CHARS` ([src/learnloop/source_retrieval/compare.py](../../../../../../src/learnloop/source_retrieval/compare.py), line 105)
- `NO_SUCH_PASSAGE` ([src/learnloop/source_retrieval/compare.py](../../../../../../src/learnloop/source_retrieval/compare.py), line 108)
- `RELATIONS` ([src/learnloop/source_retrieval/compare.py](../../../../../../src/learnloop/source_retrieval/compare.py), line 109)
- `_INSTRUCTIONS` ([src/learnloop/source_retrieval/compare.py](../../../../../../src/learnloop/source_retrieval/compare.py), line 110)
- `_INSTRUCTIONS_V2` ([src/learnloop/source_retrieval/compare.py](../../../../../../src/learnloop/source_retrieval/compare.py), line 122)

### Explicit exports

`__all__` declares:

- `COMPARE_PROMPT_VERSION`
- `COMPARE_PROMPT_VERSION_V2`
- `Comparison`
- `ComparisonPoint`
- `PointCell`
- `RELATIONS`
- `SourceComparison`
- `SourceComparisonV2`
- `compare_sources`

## Internal implementation anchors

- `_normalized(text: str) -> str` ([source](../../../../../../src/learnloop/source_retrieval/compare.py), line 213)
- `_quote_in(quote: str, passage: str) -> bool` ([source](../../../../../../src/learnloop/source_retrieval/compare.py), line 217)
- `_by_source(scope: Scope) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/source_retrieval/compare.py), line 221)
- `_pin_reason(scope: Scope, key: tuple[str, str], *, policy: str, item: Any) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/compare.py), line 228)
- `_compare_sources(vault: LoadedVault, repository: Repository, query: str, *, caller: CallerContext, facet_ids: Sequence[str], requested_perspectives: Sequence[str], pinned_span_ids: Sequence[Any], pinned_span_keys: Sequence[Any], anchor_span_keys: Sequence[Any]=(), source_ids: Sequence[str]=(), by_point: bool=False, policy: str | None=None, deadline: float | None=None, client: Any | None, verify_client: Any | None, embedder: Any | None, clock: Clock | None) -> Comparison` ([source](../../../../../../src/learnloop/source_retrieval/compare.py), line 273)
- `_cell_holders(repository: Repository, refs: Mapping[str, SpanHit], anchor: SpanHit | None, anchor_blocks: Sequence[tuple[str, str]]) -> dict[str, list[tuple[str, str, str]]]` ([source](../../../../../../src/learnloop/source_retrieval/compare.py), line 692) — Per ref, the blocks of its passage as ``(extraction, span, text)`` (an anchor of several blocks is all of them, in order), so a quoted cell names the block that holds its quote.
- `_verified_points(answer: SourceComparisonV2, refs: Mapping[str, SpanHit], passages: Mapping[str, str], holders: Mapping[str, list[tuple[str, str, str]]], requested: list[str], dropped: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/compare.py), line 708) — The v2 output as it may be shown (K13): every quoted cell's quote is in its own source's passage (else ``not_addressed``, listed as dropped); every compared source has a cell on every point; a relation stands only between two quoted cells of its point with both quotes verified (…
- `_ordered_keys(values: Sequence[Any]) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/source_retrieval/compare.py), line 798) — ``_span_keys`` in the given order (an anchor's first block names it).
- `_anchor_hit(repository: Repository, scope: Scope, keys: Sequence[tuple[str, str]]) -> tuple[SpanHit, list[tuple[str, str]]]` ([source](../../../../../../src/learnloop/source_retrieval/compare.py), line 807) — The anchor as one passage: its blocks of the first block's extraction, in the learner's order, joined (cut to the prompt bound as any passage), and those blocks (the first names the passage).
- `_also_in(vault: LoadedVault, repository: Repository, query: str, scope: Scope, others: Mapping[str, list[str]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/compare.py), line 827) — The other books with a keyword passage on the question (CA3, Q13): one unchecked hit each, exam material withheld, never sent to a model.
- `_entry(hit: SpanHit, ref: str, anchor: SpanHit | None, anchor_blocks: Sequence[tuple[str, str]]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/compare.py), line 846)
- `_source_entry(hit: SpanHit, ref: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/compare.py), line 858)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `module`
- [[Reference/Modules/learnloop/instructional/sources|learnloop.instructional.sources]] — imports `Comparison`, `compare_sources`; statically calls `compare_sources`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `compare_sources`; statically calls `compare_sources`
- [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]] — imports `COMPARE_PROMPT_VERSION`, `COMPARE_PROMPT_VERSION_V2`, `_quote_in`; statically calls `_quote_in`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`; calls `SpendBudget`, `SpendCaps`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `record_reveal`; calls `record_reveal`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `blocks_by_key`, `search_blocks`; calls `blocks_by_key`, `search_blocks`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `add_comparison_reuse_provenance`, `find_comparison`, `insert_comparison`; calls `add_comparison_reuse_provenance`, `find_comparison`, `insert_comparison`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `route_skip`; calls `route_skip`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `plan_route`, `resolve_client`, `transport_problem`; calls `PaidCalls`, `plan_route`, `resolve_client`, `transport_problem`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `Scope`, `exam_withheld`, `item_exclusions`; calls `Scope`, `exam_withheld`, `item_exclusions`
- [[Reference/Modules/learnloop/source_retrieval/feedback|learnloop.source_retrieval.feedback]] — imports `deliver`; calls `deliver`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `INTENT_VERDICTS`, `_span_keys`, `_verify`, `facet_lists`, `scope_for`; calls `_span_keys`, `_verify`, `facet_lists`, `scope_for`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `CallerContext`, `PolicyRefused`, `derive_policy`; calls `PolicyRefused`, `derive_policy`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `embed_query_texts`; calls `embed_query_texts`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `SpanHit`, `search_spans`; calls `SpanHit`, `search_spans`
- [[Reference/Modules/learnloop/source_retrieval/service_spend|learnloop.source_retrieval.service_spend]] — imports `service_spend`; calls `service_spend`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `span_leaks_expected`; calls `span_leaks_expected`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `json`, `time`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]], [[Reference/Modules/learnloop/instructional/sources|learnloop.instructional.sources]], [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]], [[Reference/Modules/learnloop/source_retrieval/kept_comparisons|learnloop.source_retrieval.kept_comparisons]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/source_service_fakes.py](../../../../../../tests/source_service_fakes.py) — direct import
- [tests/test_compare_sources.py](../../../../../../tests/test_compare_sources.py) — direct import
  - `test_every_source_is_considered_and_uncompared_ones_are_listed`
  - `test_two_sources_are_compared_with_verified_quotes_and_stored`
- [tests/test_compare_sources_keep.py](../../../../../../tests/test_compare_sources_keep.py) — direct import
- [tests/test_e0_review_round3.py](../../../../../../tests/test_e0_review_round3.py) — direct import
  - `test_f20_the_search_observer_is_scoped_and_removed`
- [tests/test_library_ask.py](../../../../../../tests/test_library_ask.py) — direct import
  - `test_every_rw4a_event_is_salience_only_refused_as_evidence_and_never_client_recorded`
- [tests/test_library_ask_review.py](../../../../../../tests/test_library_ask_review.py) — direct import
  - `test_a_compare_without_its_session_stays_the_items_practice`
  - `test_a_comparison_records_exposure_for_every_passage_it_shows`
  - `test_the_table_carries_unchecked_sources_and_why`
- [tests/test_reader_ca3_codex_review.py](../../../../../../tests/test_reader_ca3_codex_review.py) — direct import
  - `test_f3_a_pin_from_a_book_not_named_is_dropped_before_verification`
  - `test_f3_the_anchor_stays_the_one_exception`
  - `test_f3_without_named_books_a_pin_is_compared_as_today`
  - `test_f4_a_one_block_anchor_is_stored_as_before`
  - `test_f4_the_stored_entry_and_cache_identity_name_every_anchor_block`
- [tests/test_reader_ca3_codex_round3.py](../../../../../../tests/test_reader_ca3_codex_round3.py) — direct import
- [tests/test_reader_ca3_compare_anywhere.py](../../../../../../tests/test_reader_ca3_compare_anywhere.py) — direct import
  - `test_a_named_book_outside_the_scope_is_refused_before_anything_is_read`
  - `test_an_anchor_needs_no_pin_and_leads_as_its_books_passage`
  - `test_an_anchor_obeys_the_pins_filters`
  - `test_named_books_only_narrow_and_the_others_are_listed_never_sent`
  - `test_without_the_ca3_arguments_the_manifest_is_todays`
- [tests/test_reader_ca4_table_by_point.py](../../../../../../tests/test_reader_ca4_table_by_point.py) — direct import
  - `test_a_cell_names_the_anchor_block_that_holds_its_quote`
  - `test_a_quote_across_two_anchor_blocks_is_not_shown_as_one_blocks_words`
  - `test_a_relation_stands_only_between_two_quoted_cells_of_its_point`
  - `test_a_v2_request_never_reuses_a_v1_row_and_reuses_its_own`
  - `test_an_invented_quote_is_dropped_never_shown`
  - `test_compare_sources_by_point_is_one_call_on_the_same_route_and_stores_v2`
  - `test_every_cells_quote_is_verified_in_code_and_a_failed_one_is_not_addressed`
  - `test_perspectives_are_points_in_the_learners_words_and_one_no_book_fills_is_kept_as_not_found`
  - `test_reopening_a_keep_by_point_shows_what_was_kept_and_its_hidden_rows`
  - `test_switched_off_a_hidden_row_sharing_a_quote_stays_hidden_by_book`
  - `test_the_readers_comparison_is_by_point_with_columns_by_book`
  - `test_the_v2_schema_has_points_cells_and_relations_and_no_consensus_field`
- [tests/test_reader_compare_table.py](../../../../../../tests/test_reader_compare_table.py) — direct import
- [tests/test_source_service_spend_envelopes.py](../../../../../../tests/test_source_service_spend_envelopes.py) — direct import
  - `test_a_comparison_is_capped_only_when_the_owner_sets_a_cap`
- [tests/test_sources_merge_composition.py](../../../../../../tests/test_sources_merge_composition.py) — direct import
  - `test_find_sources_and_compare_never_hand_exam_material_to_a_model`
- [tests/test_whole_comparison_reuse_provenance.py](../../../../../../tests/test_whole_comparison_reuse_provenance.py) — direct import
  - `test_f1_rereview_a_reuse_for_an_unknown_question_is_not_persisted`
  - `test_nov1_open_item_3_a_fresh_comparisons_pin_naming_no_passage_is_not_persisted`

## Modification guidance

- Make changes here when the responsibility remains compare within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/compare.py](../../../../../../src/learnloop/source_retrieval/compare.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

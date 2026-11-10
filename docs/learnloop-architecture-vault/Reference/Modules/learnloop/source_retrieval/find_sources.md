---
title: "learnloop.source_retrieval.find_sources"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/find_sources.py"
source_paths:
  - "src/learnloop/source_retrieval/find_sources.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.source_retrieval.find_sources module"
  - "src/learnloop/source_retrieval/find_sources.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.find_sources`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.find_sources` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: ``find_sources``: passages for an instructional intent (spec_source_practice_and_probes_v1 §9).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/find_sources.py](../../../../../../src/learnloop/source_retrieval/find_sources.py) |
| Source lines | 938 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class IntentJudgment(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 124)
- `class IntentVerification(WireModel)` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 130)
- `intent_task(intent: str) -> ListwiseTask` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 135)
- `class SourceHits` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 150) — Verbatim passages for an intent, plus the receipt-grade manifest (§5.5).
  - `as_dict(self) -> dict[str, Any]` (line 160; public)
- `span_keys(values: Sequence[Any]) -> set[SpanKey]` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 165)
- `scope_for(vault: LoadedVault, repository: Repository, *, policy: str, scope: str, learning_object_ids: Sequence[str], item: PracticeItem | None) -> Scope` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 180) — The policy's scope (§5.1).
- `facet_lists(vault: LoadedVault, repository: Repository, facet_ids: Sequence[str]) -> tuple[dict[str, list[SpanKey]], list[dict[str, str]]]` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 249) — Facet targeting (§9.1): one ranked list of the spans the facets' teaching source links cite (primary first), and each facet's label for the verification context.
- `expanded_learning_objects(vault: LoadedVault, lo_ids: Sequence[str], kind: str) -> list[str]` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 278) — The LOs one LO-graph expansion reaches from ``lo_ids``, read as the vault stores the graph (similarity never creates an edge).
- `expansion_lists(vault: LoadedVault, repository: Repository, lo_ids: Sequence[str], expand: Sequence[str]) -> dict[str, list[SpanKey]]` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 341) — One ranked list per LO-graph expansion, labelled on the hit (the Reader's rule).
- `correction_lists(vault: LoadedVault, repository: Repository, misconception: Any, extraction_ids: Sequence[str]) -> tuple[dict[str, list[SpanKey]], dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 354) — §9.3: the misconception's correction facets' spans, and keyword hits in the sources ``correction_source_span_ids`` names (source ids, §3.2 item 2).
- `source_object_lists(vault: LoadedVault, repository: Repository, intent: str, extraction_ids: Sequence[str], *, eligible: Callable[[list[SpanKey]], list[SpanKey]] | None=None) -> dict[str, list[SpanKey]]` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 395) — Source objects whose type (or RW4e authorial role) matches the intent (§9.2).
- `verification_question(query: str, intent: str, misconceptions: Sequence[Any]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 501) — The question searched for and judged against: the query, or, for a remediation with no query, the first misconception's statement and correction.
- `verification_context(intent: str, *, policy: str, misconceptions: Sequence[Any]=(), excluded: Iterable[SpanKey]=(), learner_work_md: str | None=None, item: PracticeItem | None=None, facet_labels: Sequence[Mapping[str, str]]=(), planned_practice_question: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 511) — The request-specific context the verification is given beside its candidates.
- `verification_candidates(vault: LoadedVault, pool: Sequence[SpanHit]) -> tuple[list[dict[str, Any]], dict[str, SpanKey]]` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 546) — The candidates one verification judges (``p1``, ``p2``, ...) and their span keys.
- `widest_candidates(vault: LoadedVault, count: int=VERIFY_POOL) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 561) — ``count`` candidates at their largest prompt encoding (every field at its limit, the passage at the vault's judged-passage limit, every character :data:`WIDEST_CHAR`): no real pool's prompt is larger.
- `verification_prompt(intent: str, question: str, candidates: Sequence[Mapping[str, Any]], pick_at_most: int, context: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 570) — The verification's prompt (a dry run renders the same one to estimate it).
- `find_sources(vault: LoadedVault, repository: Repository, query: str, *, policy: str, intent: str='explain', scope: str='library', learning_object_ids: Sequence[str]=(), facet_ids: Sequence[str]=(), item: PracticeItem | None=None, roles: Sequence[str]=(), expand: Sequence[str]=(), exclude_span_ids: Sequence[Any]=(), exclude_span_keys: Sequence[Any]=(), target_hypotheses: Sequence[Mapping[str, Any]]=(), learner_work_md: str | None=None, personalized: bool=True, verify: bool=False, limit: int=8, cursor: Mapping[str, Any] | None=None, embedder: Any | None=None, rewrite_client: Any | None=None, rerank_client: Any | None=None, deadline: float | None=None, owner_id: str='', clock: Clock | None=None, misconceptions: Sequence[Any]=(), caller: CallerContext | None=None, compare_client: Any | None=None, rewrite: bool | None=None, planned_practice_question: str | None=None) -> SourceHits` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 612) — Verbatim passages for ``intent`` under ``policy`` (the caller's, derived on the server).
- `find_sources_for_caller(vault: LoadedVault, repository: Repository, query: str, *, caller: CallerContext, policy: str | None=None, item: PracticeItem | None=None, **kwargs: Any) -> SourceHits` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 898) — ``find_sources`` under the caller's derived policy; a differing ``policy`` is refused (G2).

### Module constants

- `INTENTS` ([src/learnloop/source_retrieval/find_sources.py](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 73)
- `EXPANSIONS` ([src/learnloop/source_retrieval/find_sources.py](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 74)
- `INTENT_FIT_TASK` ([src/learnloop/source_retrieval/find_sources.py](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 75)
- `INTENT_PROMPT_VERSION` ([src/learnloop/source_retrieval/find_sources.py](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 76)
- `SOURCE_CHARS` ([src/learnloop/source_retrieval/find_sources.py](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 79)
- `SECTION_CHARS` ([src/learnloop/source_retrieval/find_sources.py](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 80)
- `QUESTION_CHARS` ([src/learnloop/source_retrieval/find_sources.py](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 82)
- `WIDEST_CHAR` ([src/learnloop/source_retrieval/find_sources.py](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 86)
- `HIT_TEXT_CHARS` ([src/learnloop/source_retrieval/find_sources.py](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 87)
- `VERIFY_POOL` ([src/learnloop/source_retrieval/find_sources.py](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 89)
- `PROVENANCE_SPANS_PER_LO` ([src/learnloop/source_retrieval/find_sources.py](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 90)
- `INTENT_VERDICTS` ([src/learnloop/source_retrieval/find_sources.py](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 94)
- `_DROP` ([src/learnloop/source_retrieval/find_sources.py](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 100)
- `_INSTRUCTIONS` ([src/learnloop/source_retrieval/find_sources.py](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 102)
- `FACET_LINK_RELATIONS` ([src/learnloop/source_retrieval/find_sources.py](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 234)

### Explicit exports

`__all__` declares:

- `EXPANSIONS`
- `FACET_LINK_RELATIONS`
- `facet_lists`
- `INTENTS`
- `INTENT_FIT_TASK`
- `INTENT_VERDICTS`
- `IntentVerification`
- `SourceHits`
- `correction_lists`
- `expanded_learning_objects`
- `expansion_lists`
- `find_sources`
- `find_sources_for_caller`
- `intent_task`
- `scope_for`
- `source_object_lists`
- `verification_candidates`
- `verification_context`
- `verification_prompt`
- `verification_question`
- `widest_candidates`

## Internal implementation anchors

- `_provenance_list(vault: LoadedVault, repository: Repository, lo_ids: Sequence[str]) -> list[SpanKey]` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 224)
- `_locator_span_id(locator: str | None) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 237) — A source link's span id: its ``block_span_v1`` locator, or the early-v2 ``span:<id>`` form (as the cross-source grounding reads them).
- `_hit_dict(hit: SpanHit, revision_ids: Mapping[str, str | None], *, verdict: str | None, rationale: str | None, expansion: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 472)
- `_answer_overlap(repository: Repository, item: PracticeItem) -> Callable[[list[SpanKey]], set[SpanKey]]` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 488) — The keys whose passage reproduces ``item``'s key: the answer-overlap filter ``find_sources`` applies to an assisted-practice pool, read for its effective eligibility (fix round 3) from the same block text.
- `_candidate(ref: str, source_title: str, section_path: Sequence[str], passage: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 541)
- `_verify(vault: LoadedVault, repository: Repository, *, intent: str, question: str, pool: Sequence[SpanHit], pick_at_most: int, context: Mapping[str, Any], client: Any | None, owner_id: str, deadline: float | None, clock: Clock | None) -> tuple[str, dict[SpanKey, Mapping[str, Any]], list[SpanKey], str | None]` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 584)
- `_caller_for_policy(policy: str, item: PracticeItem | None, lo_ids: Sequence[str]) -> CallerContext` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 840) — A server-side caller whose derived policy is ``policy`` (for a caller-less call).
- `_delegate_compare(vault: LoadedVault, repository: Repository, query: str, result: SourceHits, *, policy: str, item: PracticeItem | None, lo_ids: Sequence[str], facet_ids: Sequence[str], caller: CallerContext | None, deadline: float | None, embedder: Any | None, rerank_client: Any | None, compare_client: Any | None, clock: Clock | None) -> SourceHits` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 851) — ``intent="compare"``: the comparison's sources as hits, the comparison on the manifest.
- `_record_post_attempt_reveal(repository: Repository, item: PracticeItem, hits: Sequence[Mapping[str, Any]], *, clock: Clock | None) -> str | None` ([source](../../../../../../src/learnloop/source_retrieval/find_sources.py), line 882) — A ``post_attempt`` display of the item's own passages or solutions is a reveal: the family is treated as revealed afterwards (§5.1, §5.4 rule 2).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]] — imports `INTENTS`, `find_sources`; statically calls `find_sources`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `PROVENANCE_SPANS_PER_LO`
- [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]] — imports `find_sources_for_caller`; statically calls `find_sources_for_caller`
- [[Reference/Modules/learnloop/hints/map_seeds|learnloop.hints.map_seeds]] — imports `find_sources_for_caller`
- [[Reference/Modules/learnloop/instructional/sources|learnloop.instructional.sources]] — imports `SourceHits`, `find_sources`, `find_sources_for_caller`; statically calls `find_sources`, `find_sources_for_caller`
- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `INTENTS`
- [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]] — imports `module`; statically calls `intent_task`, `verification_context`, `verification_prompt`, `verification_question`, `widest_candidates`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `_span_keys`, `_verify`, `facet_lists`, `scope_for`; statically calls `_span_keys`, `_verify`, `facet_lists`, `scope_for`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `EXPANSIONS`, `expanded_learning_objects`; statically calls `expanded_learning_objects`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `correction_lists`, `expanded_learning_objects`, `source_object_lists`; statically calls `correction_lists`, `expanded_learning_objects`, `source_object_lists`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `QUESTION_CHARS`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `_verify`, `correction_lists`, `scope_for`, `span_keys`; statically calls `_verify`, `correction_lists`, `scope_for`, `span_keys`
- [[Reference/Modules/learnloop/workbench/route_example|learnloop.workbench.route_example]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/compare_scope|learnloop_sidecar.handlers.compare_scope]] — imports `scope_for`; statically calls `scope_for`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_tutor|learnloop_sidecar.handlers.reader_tutor]] — imports `find_sources_for_caller`; statically calls `find_sources_for_caller`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInvalidOutput`; calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `record_reveal`; calls `record_reveal`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `build_cross_source_spans`; calls `build_cross_source_spans`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_material`; calls `exam_material`
- [[Reference/Modules/learnloop/content/sources/provenance|learnloop.content.sources.provenance]] — imports `get_entity_provenance`; calls `get_entity_provenance`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `CITATION_MADE_AT_SQL`, `CitationResolver`, `CurrentKeys`; calls `CitationResolver`, `CurrentKeys`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `blocks_by_key`, `search_blocks`; calls `blocks_by_key`, `search_blocks`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `parse_block_span`; calls `parse_block_span`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `ListwiseTask`, `judge_listwise`; calls `ListwiseTask`, `judge_listwise`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `estimated_call_tokens`; calls `estimated_call_tokens`
- [[Reference/Modules/learnloop/reader/source_roles|learnloop.reader.source_roles]] — imports `PROPOSAL_KIND_SQL`, `positive_filter_enabled`, `role_proposals`; calls `positive_filter_enabled`, `role_proposals`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `compare_sources`; calls `compare_sources`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `Eligibility`, `Scope`, `block_roles`, `effective_eligibility`, `exam_withheld`, `extraction_scope`, `item_exclusions`, `library_scope`, `teaching_scope`; calls `Scope`, `block_roles`, `effective_eligibility`, `exam_withheld`, `extraction_scope`, `item_exclusions`, `library_scope`, `teaching_scope`
- [[Reference/Modules/learnloop/source_retrieval/feedback|learnloop.source_retrieval.feedback]] — imports `deliver`; calls `deliver`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `CallerContext`, `POLICIES`, `PolicyRefused`, `derive_policy`; calls `CallerContext`, `PolicyRefused`, `derive_policy`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `query_id`; calls `query_id`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `POOL_HYBRID_RRF`, `SpanHit`, `SpanKey`, `role_filter`, `search_spans`; calls `role_filter`, `search_spans`
- [[Reference/Modules/learnloop/source_retrieval/verify|learnloop.source_retrieval.verify]] — imports `PRICE_SETTING`, `judged_passage`, `passage_limit`, `practice_question`, `verify_caps`; calls `judged_passage`, `passage_limit`, `practice_question`, `verify_caps`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `span_leaks_expected`; calls `span_leaks_expected`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/system_arms|learnloop.experiments.contextual_embeddings.system_arms]], [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop/figures/service|learnloop.figures.service]], [[Reference/Modules/learnloop/hints/map_seeds|learnloop.hints.map_seeds]], [[Reference/Modules/learnloop/instructional/sources|learnloop.instructional.sources]] and 10 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/reader_tutor_fakes.py](../../../../../../tests/reader_tutor_fakes.py) — direct import
- [tests/source_service_fakes.py](../../../../../../tests/source_service_fakes.py) — direct import
- [tests/test_approach_maps.py](../../../../../../tests/test_approach_maps.py) — direct import
  - `test_worked_examples_come_from_t6_under_the_item_bound_policy`
- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_iv_with_the_student_off_rw5ds_grounding_retrieval_is_p1s`
- [tests/test_compare_methods.py](../../../../../../tests/test_compare_methods.py) — direct import
  - `test_the_reference_is_read_by_id_and_a_reveal_on_the_item_comes_first`
- [tests/test_e0_review_round2.py](../../../../../../tests/test_e0_review_round2.py) — direct import
  - `test_f20_a_completed_comparison_is_ranked_and_a_dense_arm_needs_its_query_embedding`
  - `test_f20_a_failed_delegated_comparison_is_missing_not_ranked`
- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
  - `test_an_exam_reserved_item_is_a_cold_administration_for_every_caller`
  - `test_post_attempt_never_reopens_an_exam_extraction_or_an_exam_item_s_own_span`
- [tests/test_exam_protection_identity.py](../../../../../../tests/test_exam_protection_identity.py) — direct import
  - `test_f12_a_legacy_scope_over_reversed_unit_ids_withholds_every_reading`
  - `test_f3_final_a_cli_upgrade_records_what_membership_qualifies_before_a_hand_edit`
- [tests/test_figures_help.py](../../../../../../tests/test_figures_help.py) — direct import
- [tests/test_figures_show_me.py](../../../../../../tests/test_figures_show_me.py) — direct import
- [tests/test_find_sources_intents.py](../../../../../../tests/test_find_sources_intents.py) — direct import
  - `test_a_low_confidence_proposal_counts_only_when_nothing_better_exists`
  - `test_a_policy_argument_cannot_widen_the_callers`
  - `test_a_proposal_never_admits_a_block_into_an_item_bound_scope`
  - `test_alternative_excludes_what_was_shown_and_prefers_other_sources`
  - `test_assisted_practice_drops_exercises_solutions_and_item_answers`
  - `test_cold_attempt_returns_nothing_and_authoring_is_not_a_policy`
  - `test_expansions_are_labelled_ranked_lists`
  - `test_explain_returns_verbatim_labelled_hits_with_identity`
  - `test_explain_verifies_when_asked_and_other_intents_always_do`
  - `test_facet_ids_target_retrieval_and_verification`
  - `test_find_sources_compare_delegates_to_compare_sources`
  - `test_post_attempt_opens_the_solution_only_after_the_window_closes_and_records_a_reveal`
  - `test_reader_consumer_contract_calls`
  - `test_roles_match_an_rw4e_proposal`
  - `test_the_compare_switch_holds_on_every_entry_point`
- [tests/test_library_ask_expand.py](../../../../../../tests/test_library_ask_expand.py) — direct import
  - `test_a_similar_passage_never_becomes_an_expansion`
  - `test_concept_edges_and_lo_ids_are_read_too`
  - `test_the_graph_is_read_as_it_is`
  - `test_the_sources_specs_expand_lists_read_the_same_graph`
- [tests/test_library_exercises.py](../../../../../../tests/test_library_exercises.py) — direct import
  - `test_with_the_sources_service_faked_the_fallbacks_call_is_the_documented_one`
- [tests/test_mcp_c1a_review.py](../../../../../../tests/test_mcp_c1a_review.py) — direct import
  - `test_no_character_encodes_wider_than_the_dry_runs_filler`
  - `test_the_dry_run_bounds_the_live_verification`
- [tests/test_prescription_passages.py](../../../../../../tests/test_prescription_passages.py) — direct import
  - `test_ranked_and_verified_passages_replace_the_first_linked_span`
- [tests/test_reader_find_sources_callers.py](../../../../../../tests/test_reader_find_sources_callers.py) — direct import
  - `test_a_workbench_session_asks_as_its_items_practice`
  - `test_with_the_sources_spec_faked_the_readers_calls_are_the_documented_ones`
- [tests/test_reader_rw1c_review.py](../../../../../../tests/test_reader_rw1c_review.py) — direct import
  - `test_no_bound_model_call_receives_item_text_from_outside_the_plan`
  - `test_switching_both_off_restores_the_base_history_projection`
- [tests/test_reader_tutor_retrieval.py](../../../../../../tests/test_reader_tutor_retrieval.py) — direct import
  - `test_with_the_service_absent_the_base_find_sources_serves_explain`
  - `test_with_the_service_faked_the_readers_calls_are_the_documented_ones`
- [tests/test_required_method_round3_review.py](../../../../../../tests/test_required_method_round3_review.py) — direct import
  - `test_f5_find_sources_keeps_the_instruction_of_a_long_stem`
- [tests/test_reread_safety.py](../../../../../../tests/test_reread_safety.py) — direct import
  - `test_citations_resolve_against_the_reading_they_were_made_on`
  - `test_f3_reviewing_a_legacy_citation_after_a_reread_keeps_what_it_cites`
- [tests/test_roles_switch_off.py](../../../../../../tests/test_roles_switch_off.py) — direct import
- [tests/test_roles_switch_off_legacy_parity.py](../../../../../../tests/test_roles_switch_off_legacy_parity.py) — direct import
- [tests/test_source_roles.py](../../../../../../tests/test_source_roles.py) — direct import
  - `test_a_proposal_held_out_later_is_never_returned`
  - `test_a_proposal_never_admits_a_block_nor_removes_an_exclusion`
  - `test_a_stronger_proposal_the_caller_excluded_never_blocks_the_low_confidence_one_under_roles`
  - `test_a_stronger_proposal_the_roles_filter_rejects_never_blocks_the_low_confidence_one`
  - `test_a_stronger_proposal_the_scope_excludes_never_blocks_the_low_confidence_one`
  - `test_an_intent_list_takes_a_low_confidence_proposal_only_when_no_stronger_one_is_in_scope`
  - `test_intent_lists_read_proposals_by_role_and_by_their_mapped_type`
  - `test_roles_filters_match_ingest_hints_and_proposals_with_the_low_confidence_rule`
  - `test_the_roles_filter_falls_back_when_the_caller_excluded_every_stronger_passage`
- [tests/test_source_space_resolver.py](../../../../../../tests/test_source_space_resolver.py) — direct import
  - `test_ordinary_use_completes_the_loop_opens_ask_citations_and_the_background_refit`
  - `test_with_the_default_at_qwen_the_fallback_changes_nothing_served`
- [tests/test_sources_merge_composition.py](../../../../../../tests/test_sources_merge_composition.py) — direct import
  - `test_find_sources_and_compare_never_hand_exam_material_to_a_model`
- [tests/test_tool_results_withhold_answers.py](../../../../../../tests/test_tool_results_withhold_answers.py) — direct import
  - `test_an_unbound_agent_never_reads_a_solution_block_or_an_exam`
- [tests/test_workbench_route_example.py](../../../../../../tests/test_workbench_route_example.py) — direct import
  - `test_without_the_sources_specs_s3_the_example_is_absent_not_approximated`

## Modification guidance

- Make changes here when the responsibility remains find sources within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/find_sources.py](../../../../../../src/learnloop/source_retrieval/find_sources.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

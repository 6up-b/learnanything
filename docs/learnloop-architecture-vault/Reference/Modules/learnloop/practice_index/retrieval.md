---
title: "learnloop.practice_index.retrieval"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/practice_index/retrieval.py"
source_paths:
  - "src/learnloop/practice_index/retrieval.py"
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
  - "learnloop.practice_index.retrieval module"
  - "src/learnloop/practice_index/retrieval.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-practice-index"
---

# `learnloop.practice_index.retrieval`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.practice_index.retrieval` exists within [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] to own the behavior summarized by its module contract: ``find_practice(query, constraints)``: recall, rerank, admit; never serve.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py) |
| Source lines | 1750 |
| Owning package | [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `canonical_intent(value: str | None) -> str` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 122)
- `class IntentUnavailable(ValueError)` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 138) — A typed refusal: the intent needs something this call was not given.
  - `__init__(self, code: str, message: str) -> None` (line 141; internal)
- `class ContinuationMismatch(ValueError)` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 146) — A cursor resumed another request than the one that made it (Codex third pass F12).
- `continuation_binding(text: str, constraints: 'PracticeConstraints') -> str` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 152) — What a cursor is bound to: the normalized query and every normalized constraint (Codex third pass F12).
- `class PracticeConstraints` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 161) — Exact filters applied before ranking; ``limit`` is a display page.
  - `__post_init__(self) -> None` (line 192; internal)
  - `from_mapping(cls, values: Mapping[str, Any] | None) -> PracticeConstraints` (line 219; public)
  - `as_dict(self) -> dict[str, Any]` (line 235; public) — The receipt form.
  - `matches(self, vault: LoadedVault, item_id: str, context: 'FilterContext | None'=None) -> bool` (line 246; public)
  - `failed_filter(self, vault: LoadedVault, item_id: str, context: 'FilterContext | None'=None) -> str | None` (line 249; public) — The first exact filter the item fails, or None (an unknown value fails a set filter).
  - `_base_matches(self, vault: LoadedVault, item: Any) -> bool` (line 275; internal)
- `class FilterContext` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 300) — What the exact filters read besides the item: attempts, reveals, minutes.
- `filter_context(vault: LoadedVault, repository: Repository, constraints: 'PracticeConstraints', *, estimator: Any | None=None, clock: Clock | None=None) -> FilterContext` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 309) — Read the sets the exact filters need, once.
- `class IndexSnapshot` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 340) — One consistent read of the index: texts, manifests and completeness.
  - `dossier_available(self) -> bool` (line 362; public)
  - `uses_vectors(self) -> bool` (line 366; public)
  - `manifest(self) -> dict[str, Any]` (line 369; public) — What a retrieval evaluation's verdict depends on.
  - `manifest_hash(self) -> str` (line 391; public)
- `dossier_documents(dossiers: Mapping[str, DossierRow], facets: Mapping[str, Any]) -> dict[str, str]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 416) — Keyword text of each dossier: the facet's label and every field.
- `load_snapshot(vault: LoadedVault, repository: Repository, *, embedder: Any | None=None) -> IndexSnapshot` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 424) — Read the index; never calls a model.
- `class Ranking` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 490)
- `rank_direct(snapshot: IndexSnapshot, repository: Repository, query_text: str, query: np.ndarray | None, corpus: Sequence[str]) -> Ranking` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 525)
- `rank_dossier(snapshot: IndexSnapshot, repository: Repository, query_text: str, query: np.ndarray | None, corpus: Sequence[str]) -> Ranking` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 552)
- `facet_shortlist(vault: LoadedVault, repository: Repository, query: str, *, limit: int=10) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 584) — Facets for a phrase: BM25 over labels and dossiers, plus stored dossier vectors when the query's vector is already cached (canonical sources S4, the router's ``facet_lookup``).
- `choose_path(vault: LoadedVault, repository: Repository, snapshot: IndexSnapshot) -> tuple[str, str]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 624) — ``(path, reason)`` under ``practice_index.retrieval_path``.
- `class RerankOutcome` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 649)
- `rerank_caps(vault: LoadedVault, pool_size: int) -> SpendCaps` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 719) — One rerank request and at most one retry, under the configured dollar cap.
- `rerank_pool(vault: LoadedVault, repository: Repository, *, query_text: str, pool: Sequence[str], pick_at_most: int, owner_id: str, client: Any | None=None) -> RerankOutcome` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 730) — The live LLM rerank: judge the pool, pick the best few, ledger every verdict.
- `admissible_corpus(vault: LoadedVault, repository: Repository, constraints: PracticeConstraints, *, clock: Clock | None=None, estimator: Any | None=None) -> tuple[list[str], dict[str, int]]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 764) — Item ids that pass admission and the constraints, plus exclusion counts.
- `plan_find_practice(vault: LoadedVault, repository: Repository, query: str, constraints: PracticeConstraints | Mapping[str, Any] | None=None, *, embedder: Any | None=None, rerank_client: Any | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 889) — Dry run of ``find_practice``: what it would embed and rerank, at what cost.
- `practice_modes(vault: LoadedVault) -> list[str]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 1034) — The closed practice-mode vocabulary: modes in use plus default rubrics'.
- `provisional_metadata(entry: Any, exercise: Mapping[str, Any], vocabulary: Sequence[Mapping[str, str]], modes: Sequence[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 1058) — The model's provisional facets and mode, checked in code (§8.1).
- `class MixedOutcome` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 1082)
- `rerank_mixed_pool(vault: LoadedVault, repository: Repository, *, query_text: str, items: Sequence[str], exercises: Sequence[Mapping[str, Any]], pick_at_most: int, owner_id: str, constraints: PracticeConstraints, client: Any | None=None) -> MixedOutcome` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 1091) — One listwise call over items and textbook exercises (canonical sources S1).
- `find_practice(vault: LoadedVault, repository: Repository, query: str, constraints: PracticeConstraints | Mapping[str, Any] | None=None, *, origin: str='api', embedder: Any | None=None, rerank_client: Any | None=None, clock: Clock | None=None, caller: Mapping[str, Any] | None=None, exercise_arm: Any | None=None, valuer: Any | None=None, estimator: Any | None=None, cursor: Mapping[str, Any] | None=None, system_initiated: bool=False, pending_decision: Mapping[str, Any] | None=None, deadline: float | None=None, already_chosen: Sequence[str]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 1164) — Propose practice items for a natural-language request.
- `exercise_filter(constraints: PracticeConstraints, metadata: Mapping[str, Any] | None, estimator: Any | None) -> str | None` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 1510) — A raw exercise's exact-filter verdict from its provisional metadata (§8.1).

### Module constants

- `DOC_TASK_PREFIX` ([src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py), line 89)
- `ITEM_RECIPE_PREFERENCE` ([src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py), line 90)
- `DOSSIER_RECIPES` ([src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py), line 91)
- `RERANK_PROMPT_VERSION` ([src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py), line 92)
- `QUERY_EMBEDDING_CAPS` ([src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py), line 94)
- `CANDIDATE_PROMPT_CHARS` ([src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py), line 96)
- `MAX_QUERY_CHARS` ([src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py), line 97)
- `_RERANK_INSTRUCTIONS` ([src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py), line 99)
- `INTENTS` ([src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py), line 114)
- `VALUE_INTENTS` ([src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py), line 115)
- `INTENT_ALIASES` ([src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py), line 118)
- `KINDS` ([src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py), line 119)
- `_LATER_FIELD_DEFAULTS` ([src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py), line 131)
- `FACET_SHORTLIST_LABEL` ([src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py), line 581)
- `RERANK_TASK` ([src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py), line 697)
- `MIXED_RERANK_PROMPT_VERSION` ([src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py), line 970)
- `EXERCISE_STATEMENT_PROMPT_CHARS` ([src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py), line 971)
- `_MIXED_INSTRUCTIONS` ([src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py), line 972)
- `MIXED_RERANK_TASK` ([src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py), line 983)

### Explicit exports

`__all__` declares:

- `DOSSIER_RECIPES`
- `INTENTS`
- `INTENT_ALIASES`
- `IndexSnapshot`
- `ContinuationMismatch`
- `IntentUnavailable`
- `KINDS`
- `MIXED_RERANK_PROMPT_VERSION`
- `MIXED_RERANK_TASK`
- `exercise_filter`
- `practice_modes`
- `provisional_metadata`
- `rerank_mixed_pool`
- `PracticeConstraints`
- `VALUE_INTENTS`
- `canonical_intent`
- `continuation_binding`
- `RERANK_PROMPT_VERSION`
- `Ranking`
- `RerankOutcome`
- `admissible_corpus`
- `choose_path`
- `dossier_documents`
- `find_practice`
- `load_snapshot`
- `plan_find_practice`
- `rank_direct`
- `rank_dossier`
- `rerank_caps`
- `rerank_pool`

## Internal implementation anchors

- `_complete(connection, recipe_name: str, manifest: Mapping[str, str], model_id: str) -> bool` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 395)
- `_manifest(vault: LoadedVault, recipe_name: str) -> dict[str, str]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 403)
- `_dossier_manifest(dossiers: Mapping[str, DossierRow], recipe_name: str) -> dict[str, str]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 408) — The SELECTED revision's content hash per facet (the recipe offers every revision).
- `_vector_ranking(connection, snapshot: IndexSnapshot, recipe_name: str, manifest: Mapping[str, str], query: np.ndarray, candidates: Sequence[str] | None) -> list[str]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 499)
- `_item_lists(connection, snapshot: IndexSnapshot, query_text: str, query: np.ndarray | None, candidates: Sequence[str]) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 512)
- `_top_facets(snapshot: IndexSnapshot, facet_order: Sequence[str], corpus: Sequence[str]) -> list[str]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 533) — At least ``facet_top_k`` facets, then more in rank order until their admissible items fill the candidate pool.
- `_candidate_clip(text: str, limit: int) -> str` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 657)
- `_candidate_context(vault: LoadedVault, pool: Sequence[str]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 662)
- `_validate_rerank(result: PracticeRerank, refs: Mapping[str, str]) -> PracticeRerank` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 679)
- `_rerank_prompt(query_text: str, pick_at_most: int, context: list[dict[str, Any]]) -> str` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 688)
- `_rerank_request(vault: LoadedVault, route, query_text: str, pool: Sequence[str], pick_at_most: int) -> tuple[str, dict[str, str], str, dict[str, str]]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 708) — The rerank prompt, its candidate refs, input hash and per-item ledger ids.
- `_rerank_skip(route, price: float | None, *, injected: bool) -> str | None` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 725)
- `_plan_query_embedding(vault: LoadedVault, repository: Repository, text: str, needed: bool, reason: str | None) -> tuple[dict[str, Any], Any]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 788) — The live query embedding's plan, and its cached vector if there is one.
- `_largest_rerank_prompt(vault: LoadedVault, text: str, corpus: Sequence[str], size: int, pick_at_most: int) -> str` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 817) — The longest rerank prompt any pool of at most ``size`` corpus items renders.
- `_plan_rerank(vault: LoadedVault, repository: Repository, text: str, pool: Sequence[str], pick_at_most: int, *, enabled: bool, pool_exact: bool, corpus: Sequence[str], client: Any | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 833) — The live rerank's plan: cache hit, recoverable answer, or one capped call.
- `_proposed_entry(entry: Mapping[str, Any], *, with_rationale: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 956) — One proposed candidate as the receipt keeps it.
- `_mixed_context(vault: LoadedVault, items: Sequence[str], exercises: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, str]]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 993) — Prompt context for one judged pool; refs map to item ids or exercise keys.
- `_facet_vocabulary(vault: LoadedVault, constraints: PracticeConstraints) -> list[dict[str, str]]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 1015) — The registry ids a raw exercise's provisional facets may be chosen from: the constraint facets and the constraint LOs' facet union (canonical ids), including the facets the LOs' own practice items declare.
- `_validate_mixed(result: MixedPracticeRerank, refs: Mapping[str, str], exercise_refs: set[str]) -> MixedPracticeRerank` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 1041)
- `_quote_in(quote: str, text: str) -> bool` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 1050)
- `_exercise_entry(exercise: Mapping[str, Any], judgment: Mapping[str, Any], metadata: Mapping[str, Any] | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 1148)
- `_valued_order(valuation: Mapping[str, Any], relevant: Sequence[str]) -> list[str]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 1535) — Checks that clear the stop first (in check order, per problem), then the valuer's presentation order, then the rest of the relevant candidates in relevance order: learner-initiated results list every group; nothing falls back to an entropy order.
- `_remediation_corpus(vault: LoadedVault, repository: Repository, constraints: PracticeConstraints, corpus: list[str]) -> tuple[list[str], dict[str, Any] | None]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 1558) — Remediate: practice keyed to the named misconception (a fatal error or a profile naming it, or its target facet); relevance ranks, no EVSI.
- `class _Carried` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 1582) — A continuation's earlier relevant candidates (F5): order, judgments, provisional metadata and the exercise records the valuer needs.
- `_carried_relevance(cursor: Mapping[str, Any] | None, *, admissible: set[str]) -> _Carried` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 1592)
- `_readmit_carried(carried: _Carried, *, vault: LoadedVault, repository: Repository, text: str, constraints: PracticeConstraints, estimator: Any | None, exercise_arm: Any | None, owner_id: str) -> Counter[str]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 1613) — Drop the carried exercises the arm or the exact filters would not admit now; keep the rest as the arm records them now (Codex third pass F12).
- `_carry_relevance(order: Sequence[str], judgments: Mapping[str, Any], metadata: Mapping[str, Any], by_key: Mapping[str, Mapping[str, Any]], vault: LoadedVault) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 1649) — The cursor's record of the relevant candidates judged so far (F5).
- `_paging(constraints: PracticeConstraints, *, ranked: Sequence[str], judged_items: set[str], judged_exercises: set[str], pending_exercises: set[str], exercise_pool: Any, valuation: Mapping[str, Any] | None, outcome: RerankOutcome, estimator: Any | None, vault: LoadedVault) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 1662) — Why paging stopped, and the cursor that resumes it (§8.3.4).
- `_below_perfect_information(valuation: Mapping[str, Any], unjudged: Sequence[str], vault: LoadedVault, estimator: Any | None) -> bool` ([source](../../../../../../src/learnloop/practice_index/retrieval.py), line 1701) — No unjudged candidate can be worth more than perfect information (§6.2 C).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/practice_index|learnloop.cli.practice_index]] — imports `PracticeConstraints`, `choose_path`, `find_practice`, `load_snapshot`, `plan_find_practice`; statically calls `PracticeConstraints`, `choose_path`, `find_practice`, `load_snapshot`, `plan_find_practice`
- [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]] — imports `IntentUnavailable`
- [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]] — imports `PracticeConstraints`, `find_practice`; statically calls `PracticeConstraints`, `find_practice`
- [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]] — imports `PracticeConstraints`, `find_practice`; statically calls `PracticeConstraints`, `find_practice`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `IntentUnavailable`, `PracticeConstraints`, `canonical_intent`, `find_practice`, `practice_modes`; statically calls `IntentUnavailable`, `canonical_intent`, `find_practice`, `practice_modes`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `ContinuationMismatch`, `PracticeConstraints`
- [[Reference/Modules/learnloop/instructional/tools|learnloop.instructional.tools]] — imports `ContinuationMismatch`, `INTENTS`, `IntentUnavailable`, `PracticeConstraints`, `admissible_corpus`, `facet_shortlist`; statically calls `PracticeConstraints`, `admissible_corpus`, `facet_shortlist`
- [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]] — imports `PracticeConstraints`, `admissible_corpus`, `load_snapshot`, `rank_direct`, `rank_dossier`; statically calls `PracticeConstraints`, `admissible_corpus`, `load_snapshot`, `rank_direct`, `rank_dossier`
- [[Reference/Modules/learnloop/practice_index/tool|learnloop.practice_index.tool]] — imports `PracticeConstraints`, `find_practice`; statically calls `find_practice`
- [[Reference/Modules/learnloop_sidecar/handlers/practice_index|learnloop_sidecar.handlers.practice_index]] — imports `IntentUnavailable`, `PracticeConstraints`, `find_practice`; statically calls `find_practice`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `IntentUnavailable`, `PracticeConstraints`, `find_practice`; statically calls `find_practice`
- [[Reference/Modules/learnloop_sidecar/handlers/source_service|learnloop_sidecar.handlers.source_service]] — imports `IntentUnavailable`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInvalidOutput`; calls `AIInvalidOutput`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; calls `SpendBudget`, `SpendCaps`, `SpendEstimate`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `utc_now_iso`; calls `SystemClock`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] — imports `retrieve`; calls `retrieve`
- [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]] — imports `DossierRow`, `checkpointed_keys`, `insert_proposal`, `judgments_by_ids`, `latest_evaluation`, `stored_vector_hashes`; calls `checkpointed_keys`, `insert_proposal`, `judgments_by_ids`, `latest_evaluation`, `stored_vector_hashes`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `COLD_RETRIEVAL_DELAY`
- [[Reference/Modules/learnloop/diagnosis/robust_composition|learnloop.diagnosis.robust_composition]] — imports `BURDEN_COST`, `LAMBDA_TIME`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `estimated_tokens`; calls `estimated_tokens`
- [[Reference/Modules/learnloop/practice_index/admission|learnloop.practice_index.admission]] — imports `PracticeAdmission`
- [[Reference/Modules/learnloop/practice_index/catalog|learnloop.practice_index.catalog]] — imports `facet_label`, `item_facets`, `registered_facets`; calls `facet_label`, `item_facets`, `registered_facets`
- [[Reference/Modules/learnloop/practice_index/contracts|learnloop.practice_index.contracts]] — imports `MixedPracticeRerank`, `PracticeRerank`, `RELEVANCE_SCORE`
- [[Reference/Modules/learnloop/practice_index/dossiers|learnloop.practice_index.dossiers]] — imports `select_current_dossiers`; calls `select_current_dossiers`
- [[Reference/Modules/learnloop/practice_index/listwise|learnloop.practice_index.listwise]] — imports `ListwiseTask`, `judge_listwise`, `ledger_ids`, `listwise_caps`, `request_input_hash`, `route_skip`; calls `ListwiseTask`, `judge_listwise`, `ledger_ids`, `listwise_caps`, `request_input_hash`, `route_skip`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `checkpoint_key`, `estimated_call_tokens`, `plan_route`, `receipt_answer`; calls `PaidCalls`, `checkpoint_key`, `estimated_call_tokens`, `plan_route`, `receipt_answer`
- [[Reference/Modules/learnloop/practice_index/query_vectors|learnloop.practice_index.query_vectors]] — imports `cached_query_vectors`, `embed_queries`, `embedding_ready`, `normalize_query`, `query_embedding_price`, `query_id`; calls `cached_query_vectors`, `embed_queries`, `embedding_ready`, `normalize_query`, `query_embedding_price`, `query_id`
- [[Reference/Modules/learnloop/practice_index/text|learnloop.practice_index.text]] — imports `BM25`, `reciprocal_rank_fusion`; calls `BM25`, `reciprocal_rank_fusion`
- [[Reference/Modules/learnloop/reveal_coverage|learnloop.reveal_coverage]] — imports `routine_coverage_sql`, `routine_window_start`; calls `routine_coverage_sql`, `routine_window_start`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `DOSSIER_FIELDS`, `EMBEDDING_RECIPES`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `learning_object_facet_union`; calls `learning_object_facet_union`
- [[Reference/Modules/learnloop/vault/required_method|learnloop.vault.required_method]] — imports `fit_presented_prompt`, `presented_prompt`; calls `fit_presented_prompt`, `presented_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `json`, `time`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/practice_index|learnloop.cli.practice_index]], [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]], [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]], [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]], [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] and 7 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_discriminating_search.py](../../../../../../tests/test_discriminating_search.py) — direct import
  - `test_a_carried_exercise_imported_since_is_not_restored`
  - `test_a_continuation_with_other_constraints_is_refused`
  - `test_a_refused_rerank_leaves_its_page_pending_and_a_resume_judges_it`
  - `test_a_value_search_pages_on_until_a_stop_inside_one_call`
  - `test_an_earlier_impression_and_a_source_exposure_exclude`
  - `test_an_exposed_item_is_not_proposed_for_a_value_intent`
  - `test_an_unverified_import_is_excluded_from_value_intents_but_not_practice`
  - `test_discriminate_values_items_and_bounds_exercises`
  - `test_final_assembly_never_restores_a_hard_exclusion`
  - `test_item_filters_and_the_required_estimator`
  - `test_paging_resumes_with_a_cursor`
  - `test_post_import_validation_rejects_lo_fallback_and_long_drafts`
  - `test_raw_exercise_filters_read_quote_verified_metadata`
  - `test_reader_aliases_and_value_intent_without_a_valuer`
  - `test_system_initiated_item_point_checks_abstain`
  - `test_the_discriminating_search_switch_refuses_value_intents`
- [tests/test_exercise_arm.py](../../../../../../tests/test_exercise_arm.py) — direct import
  - `test_an_already_imported_exercise_is_dropped`
  - `test_exercise_paging_reaches_every_region_through_exhaustion`
  - `test_find_practice_judges_items_and_exercises_in_one_pool`
  - `test_kinds_items_skips_the_arm_and_source_exercises_skips_items`
  - `test_the_arm_returns_regions_in_the_teaching_scope_only`
  - `test_the_positive_role_filter_keeps_only_effective_exercise_blocks`
  - `test_unjudged_exercises_are_never_proposed`
- [tests/test_library_exercises.py](../../../../../../tests/test_library_exercises.py) — direct import
- [tests/test_practice_index_dossiers.py](../../../../../../tests/test_practice_index_dossiers.py) — direct import
  - `test_reverting_sources_selects_the_matching_earlier_dossier`
- [tests/test_practice_index_evaluation.py](../../../../../../tests/test_practice_index_evaluation.py) — direct import
  - `test_end_to_end_with_fakes_persists_a_decision_and_reruns_free`
- [tests/test_practice_index_find.py](../../../../../../tests/test_practice_index_find.py) — direct import
  - `test_a_forced_dossier_path_falls_back_while_dossiers_are_missing`
  - `test_a_metered_rerank_without_a_price_is_skipped_and_labelled`
  - `test_a_partial_rerank_is_retried_then_reported_unreranked`
  - `test_a_rerank_whose_checkpoint_failed_is_recovered_from_its_receipt`
  - `test_an_alternative_embedding_model_takes_an_explicit_price`
  - `test_changed_index_content_voids_an_earlier_evaluation_approval`
  - `test_constraints_filter_before_ranking`
  - `test_direct_item_search_is_the_default_and_leaves_a_receipt`
  - `test_find_dry_run_bounds_the_rerank_pool_the_query_vector_will_fill`
  - `test_find_dry_run_keeps_the_keyword_pool_when_no_query_embedding_will_run`
  - `test_find_dry_run_names_metered_rerank_prices_and_caps`
  - `test_find_dry_run_plans_embedding_and_rerank_without_clients_or_writes`
  - `test_item_skeleton_vectors_rank_items_only_once_they_cover_every_item`
  - `test_kill_switch_and_the_agent_tool`
  - `test_proposing_never_serves_or_writes_learning_state`
  - `test_rerank_verdicts_go_to_the_ledger_and_are_reused`
  - `test_the_dossier_path_needs_a_winning_evaluation_on_the_current_index`
  - `test_usage_signals_are_ledgered_and_joined_to_attempts`
- [tests/test_practice_proposal_caller_columns.py](../../../../../../tests/test_practice_proposal_caller_columns.py) — direct import
  - `test_a_service_caller_is_recorded_with_its_intent`
  - `test_reader_intent_aliases_are_canonicalized`
  - `test_without_a_caller_the_receipt_is_phase_5b_s`
- [tests/test_proposal_impressions.py](../../../../../../tests/test_proposal_impressions.py) — direct import
- [tests/test_reader_followups.py](../../../../../../tests/test_reader_followups.py) — direct import
  - `test_the_exact_filters_reach_find_practice_admission`
- [tests/test_reader_followups_review.py](../../../../../../tests/test_reader_followups_review.py) — direct import
  - `test_f12_the_production_valuer_composes_the_attempt_familiarity_discount`
  - `test_f9_a_formative_only_retention_question_reaches_a_valuation_problem`
- [tests/test_required_method_round3_review.py](../../../../../../tests/test_required_method_round3_review.py) — direct import
  - `test_f4_the_practice_index_result_presents_the_question`
- [tests/test_source_exercise_rpcs.py](../../../../../../tests/test_source_exercise_rpcs.py) — direct import
- [tests/test_source_retrieval_guards.py](../../../../../../tests/test_source_retrieval_guards.py) — direct import
  - `test_tutor_verification_and_the_practice_rerank_share_one_listwise_judge`
- [tests/test_tutor_practice_request.py](../../../../../../tests/test_tutor_practice_request.py) — direct import
  - `test_the_caller_is_rederived_on_the_server_and_cannot_widen`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains retrieval within learnloop.practice_index; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/practice_index/retrieval.py](../../../../../../src/learnloop/practice_index/retrieval.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

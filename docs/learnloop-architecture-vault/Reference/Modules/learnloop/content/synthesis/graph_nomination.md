---
title: "learnloop.content.synthesis.graph_nomination"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/synthesis/graph_nomination.py"
source_paths:
  - "src/learnloop/content/synthesis/graph_nomination.py"
source_commit: "301e60bcd8d44ae9d2e1f699881441b9fa02c578"
source_commit_timestamp: "2026-10-12T13:23:49-04:00"
source_worktree_state: "clean"
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
  - "learnloop.content.synthesis.graph_nomination module"
  - "src/learnloop/content/synthesis/graph_nomination.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-synthesis"
---

# `learnloop.content.synthesis.graph_nomination`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.synthesis.graph_nomination` exists within [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] to own the behavior summarized by its module contract: Slice 2 T5: embedding nominations for ingest and graph review (spec §8).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/synthesis/graph_nomination.py](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py) |
| Source lines | 1070 |
| Owning package | [[Reference/Modules/learnloop/content/synthesis/_package|learnloop.content.synthesis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `301e60bcd8d44ae9d2e1f699881441b9fa02c578` |
| Commit timestamp | `2026-10-12T13:23:49-04:00` |

## Public API

- `is_active(config: Any) -> bool` ([source](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 90) — The kill switch and the embedding master switch must both be on.
- `class Nomination` ([source](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 97)
  - `as_dict(self) -> dict[str, Any]` (line 102; public)
- `class QueryText` ([source](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 107) — New text to embed (or find already embedded) for one comparison.
- `facet_query(payload: Mapping[str, Any], record_id: str | None=None) -> QueryText | None` ([source](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 123) — A candidate facet's ``facet/definition`` text, hashed as its backfill would.
- `concept_query(concept: Any, record_id: str) -> QueryText | None` ([source](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 132)
- `repair_query(text: str) -> QueryText | None` ([source](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 139)
- `undefined_concept_mentions(new_inventories: Iterable[Mapping[str, Any]]) -> int` ([source](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 180) — Concept mentions no claim defines: they stay lexical-only (no query).
- `inventory_queries(new_inventories: Iterable[Mapping[str, Any]]) -> tuple[list[QueryText], list[QueryText]]` ([source](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 197) — LLM-written inventory claims (vs facets) and concept mentions (vs concepts).
- `class RegistryIndex` ([source](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 249) — The complete current index of one registry recipe for one model.
  - `__init__(self, recipe_name: str, vectors: Mapping[str, np.ndarray])` (line 252; internal)
  - `__len__(self) -> int` (line 267; internal)
  - `__contains__(self, record_id: object) -> bool` (line 270; internal)
  - `_centre(self, vector: np.ndarray) -> np.ndarray | None` (line 273; internal)
  - `_scores(self, centred_query: np.ndarray) -> np.ndarray` (line 279; internal)
  - `nearest(self, vector: np.ndarray, k: int, *, exclude: Collection[str]=()) -> list[Nomination]` (line 284; public) — Top-k by mean-centred cosine; ties break on record id (deterministic).
  - `ranks(self, vector: np.ndarray, *, exclude: Collection[str]=()) -> dict[str, tuple[int, float]]` (line 298; public) — Every record's (rank, cosine) against ``vector``; used by the report.
  - `vector(self, record_id: str) -> np.ndarray | None` (line 304; public)
  - `cosine(self, left: np.ndarray, right: np.ndarray) -> float | None` (line 308; public) — Mean-centred cosine of two vectors under this index's centroid.
  - `pair(self, left_id: str, right_id: str) -> float | None` (line 317; public)
  - `pairwise(self) -> np.ndarray` (line 323; public) — All-pairs centred cosine matrix (the report's noise floor).
- `raw_cosine(left: np.ndarray | None, right: np.ndarray | None) -> float | None` ([source](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 331) — Uncentred cosine, for text pairs with no registry centroid (repair shadow).
- `class GraphNominator` ([source](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 340) — Stored-vector lookups plus capped embedding of new candidate text.
  - `__init__(self, vault: LoadedVault, sqlite_path: Path, *, allow_new_text: bool, repository: Any=None, client_factory: Callable[[], EmbeddingClient] | None=None) -> None` (line 347; internal)
  - `lexical_only(self, reason: str, count: int) -> None` (line 387; public) — Record new material that had nothing to embed and stays lexical.
  - `for_review(cls, vault: LoadedVault) -> GraphNominator | None` (line 397; public) — Stored vectors only; ``None`` when the kill switch or embeddings are off.
  - `for_ingest(cls, vault: LoadedVault, repository: Any, *, client_factory: Callable[[], EmbeddingClient] | None=None) -> GraphNominator | None` (line 405; public)
  - `stored_only(self) -> GraphNominator` (line 416; public) — The same vault and model with no paid path (revalidation, review).
  - `_note(self, reason: str) -> None` (line 423; internal)
  - `summary(self) -> dict[str, Any]` (line 427; public) — Honest label for run records and reports: what was and was not nominated.
  - `_status(self) -> str` (line 446; internal)
  - `identity(self, recipes: Sequence[str]=(FACET_RECIPE, CONCEPT_RECIPE), *, prompt_version: str | None=None) -> dict[str, Any]` (line 456; public) — The stable inputs that decide what this nominator can show a model.
  - `index(self, recipe_name: str) -> RegistryIndex | None` (line 498; public) — The complete current index for one registry recipe, or ``None``.
  - `vectors(self, queries: Sequence[QueryText | None]) -> dict[str, np.ndarray]` (line 535; public) — ``content_hash -> vector`` for every query that is stored or embeddable.
  - `_key(self, query: QueryText) -> tuple[str, str, str, str]` (line 580; internal)
  - `_ready_client(self) -> EmbeddingClient | None` (line 583; internal)
  - `_embed(self, pending: list[QueryText]) -> dict[QueryText, np.ndarray]` (line 613; internal)
  - `_observer(self, prefix: str, usage: dict[str, Any]) -> Callable[[str, dict[str, Any]], None]` (line 697; internal)
  - `nominate(self, recipe_name: str, queries: Sequence[QueryText | None], *, exclude: Mapping[str, Collection[str]] | None=None, k: int | None=None) -> dict[str, list[Nomination]]` (line 717; public) — ``query.record_id -> top-k registry nominations``; empty when degraded.
  - `nominate_vectors(self, recipe_name: str, vectors: Mapping[str, np.ndarray], *, exclude: Mapping[str, Collection[str]] | None=None, k: int | None=None) -> dict[str, list[Nomination]]` (line 737; public)
  - `facet_cosine(self, left: Any, right: Any) -> float | None` (line 752; public) — Cosine of two facets, each a registered id or a proposal payload.
  - `pair_cosine(self, recipe_name: str, left_id: str, right_id: str) -> float | None` (line 779; public)
  - `cosine_column(self, recipe_name: str, left_id: str, right_id: str) -> dict[str, Any]` (line 783; public) — The review-pass cosine column: a value, or why there is none.
- `plan_ingest_embedding(vault: LoadedVault, sqlite_path: Path, *, entry: str, new_inventories: Sequence[Mapping[str, Any]]=()) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 820) — What one synthesis (``entry='bootstrap'``) or append run may pay to embed.
- `annotate_mint_report(nominator: GraphNominator, report: Any, candidates: Sequence[Mapping[str, Any]], registered: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 930) — Shadow record beside the D2 verdicts.

### Module constants

- `NOMINATION_VERSION` ([src/learnloop/content/synthesis/graph_nomination.py](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 65)
- `DOCUMENT_PREFIX` ([src/learnloop/content/synthesis/graph_nomination.py](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 66)
- `FACET_RECIPE` ([src/learnloop/content/synthesis/graph_nomination.py](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 67)
- `CONCEPT_RECIPE` ([src/learnloop/content/synthesis/graph_nomination.py](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 68)
- `REPAIR_RECIPE` ([src/learnloop/content/synthesis/graph_nomination.py](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 69)
- `INVENTORY_CLAIM_KIND` ([src/learnloop/content/synthesis/graph_nomination.py](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 73)
- `INVENTORY_CONCEPT_KIND` ([src/learnloop/content/synthesis/graph_nomination.py](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 74)
- `INVENTORY_QUERY_VERSION` ([src/learnloop/content/synthesis/graph_nomination.py](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 75)
- `INVENTORY_CONCEPT_QUERY_VERSION` ([src/learnloop/content/synthesis/graph_nomination.py](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 78)
- `_MAX_DEFINING_CLAIMS` ([src/learnloop/content/synthesis/graph_nomination.py](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 80)
- `OWNER_KIND` ([src/learnloop/content/synthesis/graph_nomination.py](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 81)
- `_BATCH` ([src/learnloop/content/synthesis/graph_nomination.py](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 82)

### Explicit exports

`__all__` declares:

- `CONCEPT_RECIPE`
- `FACET_RECIPE`
- `GraphNominator`
- `NOMINATION_VERSION`
- `Nomination`
- `QueryText`
- `REPAIR_RECIPE`
- `RegistryIndex`
- `annotate_mint_report`
- `concept_query`
- `facet_query`
- `inventory_queries`
- `is_active`
- `plan_ingest_embedding`
- `raw_cosine`
- `repair_query`
- `undefined_concept_mentions`

## Internal implementation anchors

- `_digest(payload: Any) -> str` ([source](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 85)
- `_recipe_query(recipe_name: str, record_id: str, text: str) -> QueryText` ([source](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 118)
- `_inventory_query(kind: str, text: str, version: int=INVENTORY_QUERY_VERSION) -> QueryText | None` ([source](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 146)
- `_mention_definitions(inventory: Mapping[str, Any]) -> dict[str, str]` ([source](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 156) — ``mention_id -> definition`` from the LLM-written claims linked to it.
- `_text_tokens(queries: Iterable[QueryText]) -> int` ([source](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 796)
- `_embed_calls(groups: Iterable[Sequence[QueryText]]) -> int` ([source](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py), line 801) — Requests the run sends for these query groups, batched as it batches them.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `annotate_mint_report`; statically calls `annotate_mint_report`
- [[Reference/Modules/learnloop/content/facet_identity/dedupe|learnloop.content.facet_identity.dedupe]] — imports `FACET_RECIPE`, `GraphNominator`
- [[Reference/Modules/learnloop/content/facet_identity/plan|learnloop.content.facet_identity.plan]] — imports `FACET_RECIPE`, `facet_query`; statically calls `facet_query`
- [[Reference/Modules/learnloop/content/synthesis/append_neighborhood|learnloop.content.synthesis.append_neighborhood]] — imports `CONCEPT_RECIPE`, `FACET_RECIPE`, `inventory_queries`, `undefined_concept_mentions`; statically calls `inventory_queries`, `undefined_concept_mentions`
- [[Reference/Modules/learnloop/content/synthesis/facet_candidates|learnloop.content.synthesis.facet_candidates]] — imports `FACET_RECIPE`
- [[Reference/Modules/learnloop/content/synthesis/facet_doctor|learnloop.content.synthesis.facet_doctor]] — imports `FACET_RECIPE`, `GraphNominator`
- [[Reference/Modules/learnloop/content/synthesis/source_append|learnloop.content.synthesis.source_append]] — imports `GraphNominator`, `plan_ingest_embedding`; statically calls `plan_ingest_embedding`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `CONCEPT_RECIPE`, `GraphNominator`, `annotate_mint_report`, `concept_query`, `plan_ingest_embedding`; statically calls `annotate_mint_report`, `concept_query`, `plan_ingest_embedding`
- [[Reference/Modules/learnloop/ops/graph_nomination_report|learnloop.ops.graph_nomination_report]] — imports `CONCEPT_RECIPE`, `FACET_RECIPE`, `GraphNominator`, `NOMINATION_VERSION`, `RegistryIndex`, `annotate_mint_report`, `raw_cosine`, `repair_query`; statically calls `GraphNominator`, `annotate_mint_report`, `raw_cosine`, `repair_query`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/embedding|learnloop.ai.embedding]] — imports `EMBEDDING_PRICES_PER_MILLION`, `EmbeddingClient`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `observe_model_calls`; calls `observe_model_calls`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendEstimate`, `SpendLimitExceeded`; calls `SpendBudget`, `SpendCaps`, `SpendEstimate`
- [[Reference/Modules/learnloop/content/synthesis/facet_mint_gate|learnloop.content.synthesis.facet_mint_gate]] — imports `distinct_repair`; calls `distinct_repair`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] — imports `IncompleteEmbeddingIndex`, `current_vectors`, `get_vector_by_content`, `put_vector`; calls `current_vectors`, `get_vector_by_content`, `put_vector`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_gate|learnloop.diagnosis.diagnostic_gate]] — imports `normalize_answer`; calls `normalize_answer`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/vault/embedding_recipes|learnloop.vault.embedding_recipes]] — imports `EMBEDDING_RECIPES`, `concept_definition_text`, `facet_definition_text`, `repair_record_id`; calls `concept_definition_text`, `facet_definition_text`, `repair_record_id`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `hashlib`, `json`, `pathlib`, `sqlite3`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/content/facet_identity/dedupe|learnloop.content.facet_identity.dedupe]], [[Reference/Modules/learnloop/content/facet_identity/plan|learnloop.content.facet_identity.plan]], [[Reference/Modules/learnloop/content/synthesis/append_neighborhood|learnloop.content.synthesis.append_neighborhood]], [[Reference/Modules/learnloop/content/synthesis/facet_candidates|learnloop.content.synthesis.facet_candidates]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_facet_identity_composition.py](../../../../../../../tests/test_facet_identity_composition.py) — direct import
  - `test_the_ledger_records_merged_pairs_and_shortlisted_different_pairs_only`
- [tests/test_graph_nomination.py](../../../../../../../tests/test_graph_nomination.py) — direct import
  - `test_append_neighbourhood_unions_embedding_nominations_after_lexical`
  - `test_append_neighbourhood_without_vectors_is_the_lexical_selection`
  - `test_backfill_reuses_a_vector_paid_at_ingest_under_another_id`
  - `test_candidate_payload_text_hashes_like_the_registry_record`
  - `test_concept_and_repair_recipes_embed_llm_written_definitions`
  - `test_concept_queries_carry_their_linked_definitions`
  - `test_content_addressed_lookup_and_complete_index`
  - `test_dry_run_counts_the_calls_each_query_group_sends`
  - `test_incomplete_index_degrades_without_paying`
  - `test_ingest_embeds_new_text_once_with_receipts`
  - `test_inventory_queries_are_deterministic_and_deduplicated`
  - `test_mint_shadow_never_changes_a_disposition`
  - `test_paid_path_failures_degrade_to_lexical`
  - `test_ranking_matches_phase_1_retrieval`
  - `test_repair_shadow_reports_the_text_verdict_and_embedding_view`
  - `test_review_mode_never_constructs_a_client`
  - `test_switches_return_no_nominator`

## Modification guidance

- Change graph nomination policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/synthesis/graph_nomination.py](../../../../../../../src/learnloop/content/synthesis/graph_nomination.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

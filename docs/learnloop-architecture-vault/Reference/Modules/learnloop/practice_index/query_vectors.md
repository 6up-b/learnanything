---
title: "learnloop.practice_index.query_vectors"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/practice_index/query_vectors.py"
source_paths:
  - "src/learnloop/practice_index/query_vectors.py"
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
  - "learnloop.practice_index.query_vectors module"
  - "src/learnloop/practice_index/query_vectors.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-practice-index"
---

# `learnloop.practice_index.query_vectors`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.practice_index.query_vectors` exists within [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] to own the behavior summarized by its module contract: Query embeddings for the practice index: cached, capped, and opt-in.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/practice_index/query_vectors.py](../../../../../../src/learnloop/practice_index/query_vectors.py) |
| Source lines | 242 |
| Owning package | [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `normalize_query(text: str) -> str` ([source](../../../../../../src/learnloop/practice_index/query_vectors.py), line 40)
- `query_id(text: str) -> str` ([source](../../../../../../src/learnloop/practice_index/query_vectors.py), line 47)
- `class QueryVectors` ([source](../../../../../../src/learnloop/practice_index/query_vectors.py), line 65)
  - `as_dict(self) -> dict[str, Any]` (line 73; public)
- `embedding_ready(vault: LoadedVault, embedder: EmbeddingClient | None) -> str | None` ([source](../../../../../../src/learnloop/practice_index/query_vectors.py), line 79) — Why query embeddings cannot be used, or None.
- `cached_query_vectors(repository: Repository, model_id: str, queries: dict[str, str], *, record_kind: str=QUERY_RECORD_KIND) -> dict[str, np.ndarray]` ([source](../../../../../../src/learnloop/practice_index/query_vectors.py), line 86) — Stored query vectors; ``record_kind`` keeps another consumer's queries apart (Slice 2 T6 uses ``source_query``).
- `query_embedding_price(model_id: str, price_per_million: float | None) -> tuple[float | None, str]` ([source](../../../../../../src/learnloop/practice_index/query_vectors.py), line 100) — The owner's explicit price, else the published estimate; unknown is None.
- `plan_query_embedding(vault: LoadedVault, repository: Repository, queries: dict[str, str], *, price_per_million: float | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/query_vectors.py), line 108) — Dry-run view: how many query texts would be embedded, and at what cost.
- `embed_queries(vault: LoadedVault, repository: Repository, queries: dict[str, str], *, budget: SpendBudget, embedder: EmbeddingClient | None=None, price_per_million: float | None=None, owner_kind: str='practice_query_embedding', owner_id: str='', cancelled: Callable[[], bool] | None=None, record_kind: str=QUERY_RECORD_KIND, deadline: float | None=None) -> QueryVectors` ([source](../../../../../../src/learnloop/practice_index/query_vectors.py), line 127) — Vectors for ``{record_id: text}``, embedding only what is not cached.

### Module constants

- `QUERY_RECORD_KIND` ([src/learnloop/practice_index/query_vectors.py](../../../../../../src/learnloop/practice_index/query_vectors.py), line 34)
- `QUERY_FIELD` ([src/learnloop/practice_index/query_vectors.py](../../../../../../src/learnloop/practice_index/query_vectors.py), line 35)
- `QUERY_TASK_PREFIX` ([src/learnloop/practice_index/query_vectors.py](../../../../../../src/learnloop/practice_index/query_vectors.py), line 36)
- `BATCH_SIZE` ([src/learnloop/practice_index/query_vectors.py](../../../../../../src/learnloop/practice_index/query_vectors.py), line 37)

### Explicit exports

`__all__` declares:

- `QUERY_FIELD`
- `QUERY_RECORD_KIND`
- `QUERY_TASK_PREFIX`
- `QueryVectors`
- `cached_query_vectors`
- `embed_queries`
- `embedding_ready`
- `normalize_query`
- `plan_query_embedding`
- `query_embedding_price`
- `query_id`

## Internal implementation anchors

- `_content_hash(text: str, record_kind: str=QUERY_RECORD_KIND) -> str` ([source](../../../../../../src/learnloop/practice_index/query_vectors.py), line 51)
- `_identity(record_id: str, text: str, model_id: str, record_kind: str=QUERY_RECORD_KIND) -> dict[str, str]` ([source](../../../../../../src/learnloop/practice_index/query_vectors.py), line 57)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `normalize_query`, `query_id`; statically calls `normalize_query`, `query_id`
- [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]] — imports `cached_query_vectors`, `embed_queries`, `normalize_query`, `plan_query_embedding`, `query_id`; statically calls `cached_query_vectors`, `embed_queries`, `normalize_query`, `plan_query_embedding`, `query_id`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `cached_query_vectors`, `embed_queries`, `embedding_ready`, `normalize_query`, `query_embedding_price`, `query_id`; statically calls `cached_query_vectors`, `embed_queries`, `embedding_ready`, `normalize_query`, `query_embedding_price`, `query_id`
- [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]] — imports `cached_query_vectors`, `normalize_query`, `query_embedding_price`; statically calls `cached_query_vectors`, `normalize_query`, `query_embedding_price`
- [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] — imports `embed_queries`, `normalize_query`; statically calls `embed_queries`, `normalize_query`
- [[Reference/Modules/learnloop/source_retrieval/search|learnloop.source_retrieval.search]] — imports `normalize_query`; statically calls `normalize_query`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `cached_query_vectors`, `estimated_tokens`, `normalize_query`, `query_embedding_price`; statically calls `cached_query_vectors`, `estimated_tokens`, `normalize_query`, `query_embedding_price`
- [[Reference/Modules/learnloop/source_retrieval/verify|learnloop.source_retrieval.verify]] — imports `normalize_query`; statically calls `normalize_query`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/embedding|learnloop.ai.embedding]] — imports `EmbeddingClient`, `embedding_request_timeout`; calls `embedding_request_timeout`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIProviderUnavailable`; calls `AIInterrupted`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `observe_model_calls`; calls `observe_model_calls`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `ready_client_for_task`; calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendEstimate`, `SpendLimitExceeded`; calls `SpendEstimate`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/embedding_vectors|learnloop.db.stores.embedding_vectors]] — imports `get_vector`, `put_vector`; calls `get_vector`, `put_vector`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `PRICES_PER_MILLION`, `estimated_tokens`; calls `estimated_tokens`
- [[Reference/Modules/learnloop/text_canon|learnloop.text_canon]] — imports `collapse_whitespace`; calls `collapse_whitespace`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `hashlib`, `json`, `time`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]], [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]], [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]], [[Reference/Modules/learnloop/source_retrieval/library|learnloop.source_retrieval.library]], [[Reference/Modules/learnloop/source_retrieval/queries|learnloop.source_retrieval.queries]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_discriminating_search.py](../../../../../../tests/test_discriminating_search.py) — imports consumer [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]]
- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — imports consumer [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]]
- [tests/test_exam_protection_review.py](../../../../../../tests/test_exam_protection_review.py) — imports consumer [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]]
- [tests/test_proposal_impressions.py](../../../../../../tests/test_proposal_impressions.py) — imports consumer [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]]
- [tests/test_retrieval_interventions_write_points.py](../../../../../../tests/test_retrieval_interventions_write_points.py) — imports consumer [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]]
- [tests/test_source_exercise_rpcs.py](../../../../../../tests/test_source_exercise_rpcs.py) — imports consumer [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]]
- [tests/test_source_service_spend_envelopes.py](../../../../../../tests/test_source_service_spend_envelopes.py) — imports consumer [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]]
- [tests/test_tutor_practice_request.py](../../../../../../tests/test_tutor_practice_request.py) — imports consumer [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]]
- [tests/test_valuation_calibration_fields.py](../../../../../../tests/test_valuation_calibration_fields.py) — imports consumer [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]]
- [tests/test_practice_index_adapters.py](../../../../../../tests/test_practice_index_adapters.py) — imports consumer [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]]
- [tests/test_practice_index_evaluation.py](../../../../../../tests/test_practice_index_evaluation.py) — imports consumer [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]]
- [tests/test_practice_index_find.py](../../../../../../tests/test_practice_index_find.py) — imports consumer [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]]

## Modification guidance

- Make changes here when the responsibility remains query vectors within learnloop.practice_index; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/practice_index/query_vectors.py](../../../../../../src/learnloop/practice_index/query_vectors.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

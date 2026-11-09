---
title: "learnloop.ai.embedding"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/embedding.py"
source_paths:
  - "src/learnloop/ai/embedding.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ai"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.embedding module"
  - "src/learnloop/ai/embedding.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.embedding`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.embedding` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: Model-independent embedding contract.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/embedding.py](../../../../../../src/learnloop/ai/embedding.py) |
| Source lines | 54 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `embedding_request_timeout(seconds: float | None) -> Iterator[None]` ([source](../../../../../../src/learnloop/ai/embedding.py), line 19) — Bound the embedding requests made inside this scope to ``seconds``.
- `current_embedding_timeout() -> float | None` ([source](../../../../../../src/learnloop/ai/embedding.py), line 35) — The request timeout set by :func:`embedding_request_timeout`, or None.
- `class EmbeddingClient(Protocol)` ([source](../../../../../../src/learnloop/ai/embedding.py), line 42)
  - `embed(self, inputs: list[EmbedInput], task_prefix: str) -> list[Vector]` (line 48; public) — Embed one batch in input order; callers own admission and retries.

### Module constants

- `TASK_PREFIXES` ([src/learnloop/ai/embedding.py](../../../../../../src/learnloop/ai/embedding.py), line 10)
- `EMBEDDING_PRICES_PER_MILLION` ([src/learnloop/ai/embedding.py](../../../../../../src/learnloop/ai/embedding.py), line 13)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/providers/openai_embedding|learnloop.ai.providers.openai_embedding]] — imports `EmbedInput`, `TASK_PREFIXES`, `Vector`, `current_embedding_timeout`; statically calls `current_embedding_timeout`
- [[Reference/Modules/learnloop/ai/providers/voyage_contextual|learnloop.ai.providers.voyage_contextual]] — imports `Vector`, `current_embedding_timeout`; statically calls `current_embedding_timeout`
- [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]] — imports `EMBEDDING_PRICES_PER_MILLION`, `EmbeddingClient`
- [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]] — imports `embedding_request_timeout`; statically calls `embedding_request_timeout`
- [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] — imports `EmbeddingClient`
- [[Reference/Modules/learnloop/diagnosis/split/retrieval|learnloop.diagnosis.split.retrieval]] — imports `EmbeddingClient`
- [[Reference/Modules/learnloop/ops/embedding_backfill|learnloop.ops.embedding_backfill]] — imports `EMBEDDING_PRICES_PER_MILLION`, `EmbeddingClient`
- [[Reference/Modules/learnloop/ops/graph_nomination_report|learnloop.ops.graph_nomination_report]] — imports `EmbeddingClient`
- [[Reference/Modules/learnloop/practice_index/query_vectors|learnloop.practice_index.query_vectors]] — imports `EmbeddingClient`, `embedding_request_timeout`; statically calls `embedding_request_timeout`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `embedding_request_timeout`; statically calls `embedding_request_timeout`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `collections`, `contextlib`, `contextvars`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/providers/openai_embedding|learnloop.ai.providers.openai_embedding]], [[Reference/Modules/learnloop/ai/providers/voyage_contextual|learnloop.ai.providers.voyage_contextual]], [[Reference/Modules/learnloop/content/synthesis/graph_nomination|learnloop.content.synthesis.graph_nomination]], [[Reference/Modules/learnloop/daily_plan/router_retrieval|learnloop.daily_plan.router_retrieval]], [[Reference/Modules/learnloop/diagnosis/split/embeddings|learnloop.diagnosis.split.embeddings]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_graph_nomination_ingest.py](../../../../../../tests/test_graph_nomination_ingest.py) — direct import
- [tests/test_openai_embedding_client.py](../../../../../../tests/test_openai_embedding_client.py) — direct import
  - `test_batched_openrouter_request_mrl_order_and_receipt`
  - `test_prefix_mapping_is_coarse_and_bounded`
- [tests/test_source_retrieval_rereview_cost.py](../../../../../../tests/test_source_retrieval_rereview_cost.py) — direct import
  - `test_the_openai_embedding_client_sends_the_request_timeout`
  - `test_the_tutors_query_embedding_request_carries_the_time_left_when_the_time_box_is_restored`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/embedding.py](../../../../../../src/learnloop/ai/embedding.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

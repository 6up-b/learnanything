---
title: "learnloop.ai.providers.openai_embedding"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/providers/openai_embedding.py"
source_paths:
  - "src/learnloop/ai/providers/openai_embedding.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ai.providers"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.providers.openai_embedding module"
  - "src/learnloop/ai/providers/openai_embedding.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai-providers"
---

# `learnloop.ai.providers.openai_embedding`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.providers.openai_embedding` exists within [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] to own the behavior summarized by its module contract: One paid, metered request per batch; no hidden retries or batch splitting.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/providers/openai_embedding.py](../../../../../../../src/learnloop/ai/providers/openai_embedding.py) |
| Source lines | 162 |
| Owning package | [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `image_capable(model_id: str) -> bool` ([source](../../../../../../../src/learnloop/ai/providers/openai_embedding.py), line 27)
- `prefixed_text(text: str, task_prefix: str, model_id: str) -> str` ([source](../../../../../../../src/learnloop/ai/providers/openai_embedding.py), line 31) — Map the three stable tasks to model conventions, never arbitrary instructions.
- `class OpenAIEmbeddingProviderClient` ([source](../../../../../../../src/learnloop/ai/providers/openai_embedding.py), line 48)
  - `__init__(self, provider_name: str, profile: AIProviderConfig)` (line 52; internal)
  - `supports(self, capability: str) -> bool` (line 75; public)
  - `embed(self, inputs: list[EmbedInput], task_prefix: str) -> list[Vector]` (line 78; public)
  - `_image_input(self, value) -> dict` (line 128; internal) — One image as an OpenRouter multimodal input (image-capable models only).
  - `_vectors(self, response, count: int) -> list[Vector]` (line 139; internal)

### Module constants

- `DEFAULT_MODEL` ([src/learnloop/ai/providers/openai_embedding.py](../../../../../../../src/learnloop/ai/providers/openai_embedding.py), line 17)
- `DEFAULT_BASE_URL` ([src/learnloop/ai/providers/openai_embedding.py](../../../../../../../src/learnloop/ai/providers/openai_embedding.py), line 18)
- `IMAGE_EMBEDDING_MODELS` ([src/learnloop/ai/providers/openai_embedding.py](../../../../../../../src/learnloop/ai/providers/openai_embedding.py), line 21)
- `IMAGE_MEDIA_TYPES` ([src/learnloop/ai/providers/openai_embedding.py](../../../../../../../src/learnloop/ai/providers/openai_embedding.py), line 22)
- `MAX_IMAGE_BYTES` ([src/learnloop/ai/providers/openai_embedding.py](../../../../../../../src/learnloop/ai/providers/openai_embedding.py), line 24)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `OpenAIEmbeddingProviderClient`; statically calls `OpenAIEmbeddingProviderClient`
- [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]] — imports `OpenAIEmbeddingProviderClient`; statically calls `OpenAIEmbeddingProviderClient`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]] — imports `DEFAULT_BASE_URL`, `DEFAULT_MODEL`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]] — imports `OpenAIEmbeddingProviderClient`; statically calls `OpenAIEmbeddingProviderClient`
- [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]] — imports `OpenAIEmbeddingProviderClient`; statically calls `OpenAIEmbeddingProviderClient`
- [[Reference/Modules/learnloop/source_retrieval/b4|learnloop.source_retrieval.b4]] — imports `image_capable`; statically calls `image_capable`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/embedding|learnloop.ai.embedding]] — imports `EmbedInput`, `TASK_PREFIXES`, `Vector`, `current_embedding_timeout`; calls `current_embedding_timeout`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`; calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `model_call`, `report_call_usage`; calls `model_call`, `report_call_usage`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `EMBEDDING`
- [[Reference/Modules/learnloop/ai/usage|learnloop.ai.usage]] — imports `receipt_fields_from_chat_response`; calls `receipt_fields_from_chat_response`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `AIProviderConfig`

### Platform and third-party dependencies

- Standard library: `__future__`, `base64`, `hashlib`, `math`, `os`
- Third party: `openai`

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]], [[Reference/Modules/learnloop/diagnosis/recurrence/benchmarks|learnloop.diagnosis.recurrence.benchmarks]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/e1/replay|learnloop.experiments.contextual_embeddings.e1.replay]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/live|learnloop.experiments.contextual_embeddings.live]], [[Reference/Modules/learnloop/ops/embedding_compare|learnloop.ops.embedding_compare]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_approach_map_replay.py](../../../../../../../tests/test_approach_map_replay.py) — direct import
- [tests/test_contamination_report.py](../../../../../../../tests/test_contamination_report.py) — direct import
  - `test_the_report_never_calls_an_embedding_provider`
- [tests/test_daily_plan_replay.py](../../../../../../../tests/test_daily_plan_replay.py) — direct import
  - `test_rebuild_ignores_the_plan_and_calls_no_model`
- [tests/test_e0_review_round3.py](../../../../../../../tests/test_e0_review_round3.py) — direct import
  - `test_f21_omitted_embedding_usage_keeps_the_reservation_through_the_real_wrapper`
- [tests/test_e0_review_round8.py](../../../../../../../tests/test_e0_review_round8.py) — direct import
  - `test_the_contract_error_reasons_are_the_production_clients_fixed_messages`
- [tests/test_embedding_store.py](../../../../../../../tests/test_embedding_store.py) — direct import
  - `test_replay_preserves_paid_inputs_without_models`
- [tests/test_hint_telemetry.py](../../../../../../../tests/test_hint_telemetry.py) — direct import
  - `test_rebuild_with_help_assists_populated_calls_no_model_and_never_reads_it`
- [tests/test_knowledge_map_text_neighbors.py](../../../../../../../tests/test_knowledge_map_text_neighbors.py) — direct import
  - `test_render_never_calls_a_model_or_writes`
- [tests/test_lo_general.py](../../../../../../../tests/test_lo_general.py) — direct import
  - `test_rebuild_deterministic_and_no_external_io`
- [tests/test_openai_embedding_client.py](../../../../../../../tests/test_openai_embedding_client.py) — direct import
  - `test_prefix_mapping_is_coarse_and_bounded`
- [tests/test_source_retrieval_rereview_cost.py](../../../../../../../tests/test_source_retrieval_rereview_cost.py) — direct import
  - `test_the_openai_embedding_client_sends_the_request_timeout`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/providers/openai_embedding.py](../../../../../../../src/learnloop/ai/providers/openai_embedding.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

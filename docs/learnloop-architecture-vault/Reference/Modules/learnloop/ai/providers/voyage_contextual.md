---
title: "learnloop.ai.providers.voyage_contextual"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/providers/voyage_contextual.py"
source_paths:
  - "src/learnloop/ai/providers/voyage_contextual.py"
source_commit: "986e7227906adc3349ee514cbba0eb6a4d5c7a0e"
source_commit_timestamp: "2026-10-24T14:49:56-04:00"
source_worktree_state: "clean"
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
  - "learnloop.ai.providers.voyage_contextual module"
  - "src/learnloop/ai/providers/voyage_contextual.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai-providers"
---

# `learnloop.ai.providers.voyage_contextual`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.providers.voyage_contextual` exists within [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] to own the behavior summarized by its module contract: The Voyage contextualized-chunk client (spec_local_contextual_retrieval_v1 §8; P1b).

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/providers/voyage_contextual.py](../../../../../../../src/learnloop/ai/providers/voyage_contextual.py) |
| Source lines | 179 |
| Owning package | [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `986e7227906adc3349ee514cbba0eb6a4d5c7a0e` |
| Commit timestamp | `2026-10-24T14:49:56-04:00` |

## Public API

- `class HttpResult` ([source](../../../../../../../src/learnloop/ai/providers/voyage_contextual.py), line 45)
- `urllib_post(url: str, *, headers: Mapping[str, str], body: Mapping[str, Any], timeout: float) -> HttpResult` ([source](../../../../../../../src/learnloop/ai/providers/voyage_contextual.py), line 59) — The real HTTPS POST (redirects refused; the error body is never read into a message).
- `class VoyageContextualClient` ([source](../../../../../../../src/learnloop/ai/providers/voyage_contextual.py), line 100)
  - `__init__(self, provider_name: str, profile: AIProviderConfig, *, transport: Transport | None=None) -> None` (line 104; internal)
  - `supports(self, capability: str) -> bool` (line 120; public)
  - `_request(self, inputs: list[list[str]], input_type: str, method: str) -> Any` (line 123; internal)
  - `embed_documents(self, documents: Sequence[Sequence[str]]) -> list[list[Vector]]` (line 148; public) — One vector per chunk of each document (window), in input order.
  - `embed_queries(self, queries: Sequence[str]) -> list[Vector]` (line 161; public)

### Module constants

- `DEFAULT_MODEL` ([src/learnloop/ai/providers/voyage_contextual.py](../../../../../../../src/learnloop/ai/providers/voyage_contextual.py), line 34)
- `DEFAULT_BASE_URL` ([src/learnloop/ai/providers/voyage_contextual.py](../../../../../../../src/learnloop/ai/providers/voyage_contextual.py), line 35)
- `MAX_INPUTS_PER_REQUEST` ([src/learnloop/ai/providers/voyage_contextual.py](../../../../../../../src/learnloop/ai/providers/voyage_contextual.py), line 37)
- `MAX_CHUNKS_PER_REQUEST` ([src/learnloop/ai/providers/voyage_contextual.py](../../../../../../../src/learnloop/ai/providers/voyage_contextual.py), line 38)
- `MAX_TOKENS_PER_REQUEST` ([src/learnloop/ai/providers/voyage_contextual.py](../../../../../../../src/learnloop/ai/providers/voyage_contextual.py), line 39)
- `MAX_TOKENS_PER_DOCUMENT` ([src/learnloop/ai/providers/voyage_contextual.py](../../../../../../../src/learnloop/ai/providers/voyage_contextual.py), line 40)
- `REQUEST_TIMEOUT_S` ([src/learnloop/ai/providers/voyage_contextual.py](../../../../../../../src/learnloop/ai/providers/voyage_contextual.py), line 41)
- `_OPENER` ([src/learnloop/ai/providers/voyage_contextual.py](../../../../../../../src/learnloop/ai/providers/voyage_contextual.py), line 56)

### Explicit exports

`__all__` declares:

- `DEFAULT_BASE_URL`
- `DEFAULT_MODEL`
- `HttpResult`
- `MAX_CHUNKS_PER_REQUEST`
- `MAX_INPUTS_PER_REQUEST`
- `MAX_TOKENS_PER_DOCUMENT`
- `MAX_TOKENS_PER_REQUEST`
- `VoyageContextualClient`
- `urllib_post`

## Internal implementation anchors

- `class _NoRedirect(urllib.request.HTTPRedirectHandler)` ([source](../../../../../../../src/learnloop/ai/providers/voyage_contextual.py), line 51)
- `_unit(row: Any, dims: int, where: str) -> Vector` ([source](../../../../../../../src/learnloop/ai/providers/voyage_contextual.py), line 79)
- `_ordered(rows: Any, count: int, where: str) -> list[Any]` ([source](../../../../../../../src/learnloop/ai/providers/voyage_contextual.py), line 91)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `VoyageContextualClient`; statically calls `VoyageContextualClient`
- [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]] — imports `MAX_CHUNKS_PER_REQUEST`, `MAX_INPUTS_PER_REQUEST`, `MAX_TOKENS_PER_REQUEST`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/embedding|learnloop.ai.embedding]] — imports `Vector`, `current_embedding_timeout`; calls `current_embedding_timeout`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`; calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `model_call`, `report_call_usage`; calls `model_call`, `report_call_usage`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `EMBEDDING`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `AIProviderConfig`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `math`, `os`, `typing`, `urllib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]], [[Reference/Modules/learnloop/source_retrieval/fallback_space|learnloop.source_retrieval.fallback_space]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_voyage_fallback.py](../../../../../../../tests/test_voyage_fallback.py) — direct import
  - `test_errors_never_carry_the_key_or_the_body`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/providers/voyage_contextual.py](../../../../../../../src/learnloop/ai/providers/voyage_contextual.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

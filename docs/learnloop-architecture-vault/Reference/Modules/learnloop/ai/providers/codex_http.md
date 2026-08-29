---
title: "learnloop.ai.providers.codex_http"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/providers/codex_http.py"
source_paths:
  - "src/learnloop/ai/providers/codex_http.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.ai.providers"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.providers.codex_http module"
  - "src/learnloop/ai/providers/codex_http.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai-providers"
---

# `learnloop.ai.providers.codex_http`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.providers.codex_http` exists within [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] to own the behavior summarized by its module contract: Legacy endpoint-per-operation Codex HTTP adapter.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/providers/codex_http.py](../../../../../../../src/learnloop/ai/providers/codex_http.py) |
| Source lines | 228 |
| Owning package | [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class HttpCodexClient(TokenUsageAccounting)` ([source](../../../../../../../src/learnloop/ai/providers/codex_http.py), line 24) — Minimal local Codex app-server client.
  - `__init__(self, config: CodexConfig)` (line 32; internal)
  - `supports(self, capability: str) -> bool` (line 38; public) — Declare only the eight endpoint operations this adapter implements.
  - `complete_legacy(self, request: StructuredRequest[WireResult], *, context: object) -> WireResult` (line 43; public) — Execute one of the adapter's eight endpoint-bound operations.
  - `_validated(self, model_type: type[BaseModel], payload: dict, *, purpose: str) -> Any` (line 70; internal) — Validate one app-server response body against its wire contract.
  - `_post(self, path: str, payload: dict, *, purpose: str) -> dict` (line 96; internal)
- `class HttpAdapterProviderClient(HttpCodexClient)` ([source](../../../../../../../src/learnloop/ai/providers/codex_http.py), line 222)
  - `__init__(self, provider_name: str, profile: AIProviderConfig)` (line 225; internal)

### Module constants

- `_HTTP_ENVELOPE_KEYS` ([src/learnloop/ai/providers/codex_http.py](../../../../../../../src/learnloop/ai/providers/codex_http.py), line 21)
- `_HTTP_OPERATIONS` ([src/learnloop/ai/providers/codex_http.py](../../../../../../../src/learnloop/ai/providers/codex_http.py), line 194)
- `_HTTP_PATHS` ([src/learnloop/ai/providers/codex_http.py](../../../../../../../src/learnloop/ai/providers/codex_http.py), line 205)

## Internal implementation anchors

- `_url(base_url: str, path: str) -> str` ([source](../../../../../../../src/learnloop/ai/providers/codex_http.py), line 186)
- `_decode_lossy(raw: bytes) -> str` ([source](../../../../../../../src/learnloop/ai/providers/codex_http.py), line 190)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `HttpAdapterProviderClient`; statically calls `HttpAdapterProviderClient`
- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `HttpCodexClient`; statically calls `HttpCodexClient`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInvalidOutput`, `AIProviderUnavailable`, `CodexUnavailable`; calls `AIInvalidOutput`, `AIProviderUnavailable`, `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `_log_codex_debug`, `codex_config_from_ai_profile`; calls `_log_codex_debug`, `codex_config_from_ai_profile`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `describe_wire_validation_error`; calls `describe_wire_validation_error`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `StructuredRequest`, `WireResult`, `prompt_safe`; calls `prompt_safe`
- [[Reference/Modules/learnloop/ai/usage|learnloop.ai.usage]] — imports `TokenUsageAccounting`, `usage_from_chat_response`; calls `usage_from_chat_response`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `AIProviderConfig`, `CodexConfig`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `typing`, `urllib`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]], [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_codex_http_client.py](../../../../../../../tests/test_codex_http_client.py) — direct import
  - `test_http_codex_client_health_and_grading_round_trip`
  - `test_http_codex_client_misconception_match_bare_payload`
  - `test_http_codex_client_misconception_match_round_trip`
- [tests/test_codex_output_schema.py](../../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_http_adapter_strips_the_usage_envelope_but_not_a_bad_field`
- [tests/test_provider_resolution_parity.py](../../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_legacy_http_declares_exactly_its_endpoint_operations`
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — direct import
  - `test_legacy_http_supports_exactly_eight_operations_and_degrades_the_rest`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/providers/codex_http.py](../../../../../../../src/learnloop/ai/providers/codex_http.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

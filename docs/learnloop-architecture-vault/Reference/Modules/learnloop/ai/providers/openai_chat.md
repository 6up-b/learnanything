---
title: "learnloop.ai.providers.openai_chat"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/providers/openai_chat.py"
source_paths:
  - "src/learnloop/ai/providers/openai_chat.py"
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
  - "learnloop.ai.providers.openai_chat module"
  - "src/learnloop/ai/providers/openai_chat.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai-providers"
---

# `learnloop.ai.providers.openai_chat`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.providers.openai_chat` exists within [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] to own the behavior summarized by its module contract: OpenAI-compatible chat structured transport.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/providers/openai_chat.py](../../../../../../../src/learnloop/ai/providers/openai_chat.py) |
| Source lines | 269 |
| Owning package | [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class OpenAIChatProviderClient(TokenUsageAccounting)` ([source](../../../../../../../src/learnloop/ai/providers/openai_chat.py), line 42)
  - `__init__(self, provider_name: str, profile: AIProviderConfig)` (line 49; internal)
  - `complete(self, request: StructuredRequest[Any]) -> Any` (line 76; public) — Execute one validated structured request with one bounded repair.
  - `supports(self, capability: str) -> bool` (line 100; public)
  - `run_media_transcription(self, context: MediaTranscriptionContext) -> MediaTranscript` (line 110; public) — Native-multimodal audio → timestamped transcript ([ingest.native]).
  - `run_media_markdown(self, context: PdfExtractionContextNative) -> str` (line 129; public) — Native-multimodal PDF → GitHub-flavored Markdown ([ingest.pdf] engine "native").
  - `_run_json_messages(self, messages: list[dict[str, Any]], model_type: type[BaseModel]) -> Any` (line 153; internal)
  - `_chat(self, prompt: str, model_type: type[BaseModel] | None=None) -> str` (line 164; internal)
  - `_chat_messages(self, messages: list[dict[str, Any]], model_type: type[BaseModel] | None=None, *, use_response_format: bool=True) -> str` (line 173; internal)
  - `_create_with_retry(self, kwargs: dict[str, Any]) -> Any` (line 204; internal)
  - `_response_format(self, model_type: type[BaseModel] | None) -> dict[str, Any] | None` (line 224; internal)
  - `_reasoning_kwargs(self) -> dict[str, Any]` (line 241; internal)
  - `_default_headers(self) -> dict[str, str] | None` (line 253; internal)

### Module constants

- `_RETRY_DELAYS_SECONDS` ([src/learnloop/ai/providers/openai_chat.py](../../../../../../../src/learnloop/ai/providers/openai_chat.py), line 39)

## Internal implementation anchors

- `_is_retryable(exc: Exception) -> bool` ([source](../../../../../../../src/learnloop/ai/providers/openai_chat.py), line 257)
- `_repair_prompt(text: str, model_type: type[BaseModel]) -> str` ([source](../../../../../../../src/learnloop/ai/providers/openai_chat.py), line 264)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `OpenAIChatProviderClient`; statically calls `OpenAIChatProviderClient`
- [[Reference/Modules/learnloop/ai/providers/openrouter|learnloop.ai.providers.openrouter]] — imports `OpenAIChatProviderClient`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInvalidOutput`, `CodexUnavailable`; calls `AIInvalidOutput`, `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/multimodal|learnloop.ai.multimodal]] — imports `MediaTranscript`, `MediaTranscriptionContext`, `PdfExtractionContextNative`, `audio_content_parts`, `media_transcription_prompt`, `pdf_content_parts`, `pdf_markdown_prompt`, `strip_markdown_fences`; calls `audio_content_parts`, `media_transcription_prompt`, `pdf_content_parts`, `pdf_markdown_prompt`, `strip_markdown_fences`
- [[Reference/Modules/learnloop/ai/strict_schema|learnloop.ai.strict_schema]] — imports `strict_output_schema`; calls `strict_output_schema`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `MEDIA_MARKDOWN`, `MEDIA_TRANSCRIPTION`, `STRUCTURED_COMPLETION`, `StructuredRequest`
- [[Reference/Modules/learnloop/ai/usage|learnloop.ai.usage]] — imports `TokenUsageAccounting`, `usage_from_chat_response`; calls `usage_from_chat_response`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `AIProviderConfig`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `logging`, `os`, `sys`, `time`, `typing`
- Third party: `openai`, `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]], [[Reference/Modules/learnloop/ai/providers/openrouter|learnloop.ai.providers.openrouter]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_agent_run_tokens.py](../../../../../../../tests/test_agent_run_tokens.py) — direct import
  - `test_chat_client_accumulates_usage_across_calls_and_resets_on_consume`
  - `test_chat_client_counts_tokens_of_a_call_whose_body_is_unusable`
  - `test_chat_client_survives_a_response_with_no_usage`
- [tests/test_multimodal_client.py](../../../../../../../tests/test_multimodal_client.py) — direct import
  - `test_empty_markdown_raises`
  - `test_run_media_markdown_sends_file_part_and_suppresses_response_format`
  - `test_run_media_transcription_builds_input_audio_parts`
  - `test_run_media_transcription_repairs_invalid_json_text_only`
- [tests/test_openai_chat_client.py](../../../../../../../tests/test_openai_chat_client.py) — direct import
  - `test_chat_does_not_retry_non_retryable_errors`
  - `test_chat_retries_rate_limited_requests_with_backoff`
  - `test_extended_method_repairs_invalid_json_once`
  - `test_json_schema_response_format_sends_strict_per_request_schema`
  - `test_openai_chat_client_repairs_invalid_json_once`
  - `test_openai_chat_client_sends_deepseek_json_request`
  - `test_openai_chat_transport_runs_extended_requests`
  - `test_structured_providers_share_one_transport_surface`
- [tests/test_provider_resolution_parity.py](../../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_chat_complete_and_declared_media_capabilities_share_one_contract`
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — direct import
  - `test_chat_transport_executes_every_feature_operation`
  - `test_structured_providers_expose_no_feature_named_methods`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/providers/openai_chat.py](../../../../../../../src/learnloop/ai/providers/openai_chat.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.ai.providers.openai_chat"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/providers/openai_chat.py"
source_paths:
  - "src/learnloop/ai/providers/openai_chat.py"
source_commit: "c8380692deed1903626f67efd5804067a25db401"
source_commit_timestamp: "2026-09-23T12:25:12-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
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
| Source lines | 416 |
| Owning package | [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `c8380692deed1903626f67efd5804067a25db401` |
| Commit timestamp | `2026-09-23T12:25:12-04:00` |

## Public API

- `class OpenAIChatProviderClient(TokenUsageAccounting)` ([source](../../../../../../../src/learnloop/ai/providers/openai_chat.py), line 62)
  - `__init__(self, provider_name: str, profile: AIProviderConfig)` (line 69; internal)
  - `complete(self, request: StructuredRequest[Any]) -> Any` (line 103; public) — Execute one validated structured request with one bounded repair.
  - `supports(self, capability: str) -> bool` (line 118; public)
  - `run_media_transcription(self, context: MediaTranscriptionContext) -> MediaTranscript` (line 128; public) — Native-multimodal audio → timestamped transcript ([ingest.native]).
  - `run_media_markdown(self, context: PdfExtractionContextNative) -> str` (line 147; public) — Native-multimodal PDF → GitHub-flavored Markdown ([ingest.pdf] engine "native").
  - `_run_json_messages(self, messages: list[dict[str, Any]], model_type: type[BaseModel]) -> Any` (line 171; internal)
  - `_chat(self, prompt: str, model_type: type[BaseModel] | None=None) -> str` (line 182; internal)
  - `_system_prompt(self, model_type: type[BaseModel]) -> str` (line 191; internal) — The system turn for a first structured attempt.
  - `_chat_messages(self, messages: list[dict[str, Any]], model_type: type[BaseModel] | None=None, *, use_response_format: bool=True) -> str` (line 214; internal)
  - `_create_with_retry(self, kwargs: dict[str, Any]) -> Any` (line 244; internal)
  - `_send_once(self, kwargs: dict[str, Any]) -> Any` (line 270; internal) — One physical request under its own receipt.
  - `_meter_response(self, response: Any) -> None` (line 295; internal) — Record usage on the receipt and the run, and spend the request budget.
  - `_retry_delay(self, error: Exception, attempt: int, *, started: float, deadline_seconds: float | None) -> float | None` (line 307; internal) — Seconds to wait before the next attempt, or None to give up.
  - `_is_retryable(self, error: Exception) -> bool` (line 328; internal)
  - `_response_format(self, model_type: type[BaseModel] | None) -> dict[str, Any] | None` (line 336; internal)
  - `_reasoning_kwargs(self) -> dict[str, Any]` (line 356; internal)
  - `_default_headers(self) -> dict[str, str] | None` (line 368; internal)

### Module constants

- `_MAX_ATTEMPTS` ([src/learnloop/ai/providers/openai_chat.py](../../../../../../../src/learnloop/ai/providers/openai_chat.py), line 44)
- `_BACKOFF_BASE_SECONDS` ([src/learnloop/ai/providers/openai_chat.py](../../../../../../../src/learnloop/ai/providers/openai_chat.py), line 45)
- `_BACKOFF_CAP_SECONDS` ([src/learnloop/ai/providers/openai_chat.py](../../../../../../../src/learnloop/ai/providers/openai_chat.py), line 46)
- `_RETRY_AFTER_CAP_SECONDS` ([src/learnloop/ai/providers/openai_chat.py](../../../../../../../src/learnloop/ai/providers/openai_chat.py), line 48)
- `_MIN_ATTEMPT_SECONDS` ([src/learnloop/ai/providers/openai_chat.py](../../../../../../../src/learnloop/ai/providers/openai_chat.py), line 50)
- `_RETRYABLE_STATUS_CODES` ([src/learnloop/ai/providers/openai_chat.py](../../../../../../../src/learnloop/ai/providers/openai_chat.py), line 52)
- `_JSON_ONLY_SYSTEM_PROMPT` ([src/learnloop/ai/providers/openai_chat.py](../../../../../../../src/learnloop/ai/providers/openai_chat.py), line 58)

## Internal implementation anchors

- `class _RequestFailed(Exception)` ([source](../../../../../../../src/learnloop/ai/providers/openai_chat.py), line 372) — The provider request itself failed; ``error`` is what it raised.
- `_retry_after_seconds(error: Exception) -> float | None` ([source](../../../../../../../src/learnloop/ai/providers/openai_chat.py), line 380) — The server's requested pause from ``retry-after-ms`` or ``Retry-After``.
- `_prompt_schema(model_type: type[BaseModel]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ai/providers/openai_chat.py), line 401)
- `_repair_prompt(text: str, model_type: type[BaseModel]) -> str` ([source](../../../../../../../src/learnloop/ai/providers/openai_chat.py), line 411)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `OpenAIChatProviderClient`; statically calls `OpenAIChatProviderClient`
- [[Reference/Modules/learnloop/ai/providers/openrouter|learnloop.ai.providers.openrouter]] — imports `OpenAIChatProviderClient`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInvalidOutput`, `AIOutputTruncated`, `CodexUnavailable`; calls `AIInvalidOutput`, `AIOutputTruncated`, `CodexUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `model_call`, `report_call_usage`; calls `model_call`, `report_call_usage`
- [[Reference/Modules/learnloop/ai/multimodal|learnloop.ai.multimodal]] — imports `MediaTranscript`, `MediaTranscriptionContext`, `PdfExtractionContextNative`, `audio_content_parts`, `media_transcription_prompt`, `pdf_content_parts`, `pdf_markdown_prompt`, `strip_markdown_fences`; calls `audio_content_parts`, `media_transcription_prompt`, `pdf_content_parts`, `pdf_markdown_prompt`, `strip_markdown_fences`
- [[Reference/Modules/learnloop/ai/strict_schema|learnloop.ai.strict_schema]] — imports `strict_output_schema`; calls `strict_output_schema`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `MEDIA_MARKDOWN`, `MEDIA_TRANSCRIPTION`, `STRUCTURED_COMPLETION`, `StructuredRequest`
- [[Reference/Modules/learnloop/ai/usage|learnloop.ai.usage]] — imports `TokenUsageAccounting`, `receipt_fields_from_chat_response`, `usage_from_chat_response`; calls `receipt_fields_from_chat_response`, `usage_from_chat_response`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `AIProviderConfig`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextvars`, `email`, `json`, `logging`, `os`, `random`, `time`, `typing`
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
- [tests/test_ingestion_checkpoints.py](../../../../../../../tests/test_ingestion_checkpoints.py) — direct import
  - `test_retry_policy_records_each_failed_request_with_unknown_usage`
  - `test_truncation_or_exhausted_repair_budget_records_usage_without_repaying`
- [tests/test_model_usage_report.py](../../../../../../../tests/test_model_usage_report.py) — direct import
- [tests/test_multimodal_client.py](../../../../../../../tests/test_multimodal_client.py) — direct import
  - `test_empty_markdown_raises`
  - `test_run_media_markdown_sends_file_part_and_suppresses_response_format`
  - `test_run_media_transcription_builds_input_audio_parts`
  - `test_run_media_transcription_repairs_invalid_json_text_only`
- [tests/test_openai_chat_client.py](../../../../../../../tests/test_openai_chat_client.py) — direct import
  - `test_chat_does_not_retry_non_retryable_errors`
  - `test_chat_gives_up_when_retry_after_outlasts_the_deadline`
  - `test_chat_honours_retry_after`
  - `test_chat_jitter_spreads_retry_delays_below_the_ceiling`
  - `test_chat_retries_connection_failures_and_timeouts`
  - `test_chat_retries_rate_limited_requests_with_jittered_backoff`
  - `test_chat_retries_share_one_deadline`
  - `test_chat_retry_count_stays_bounded`
  - `test_extended_method_repairs_invalid_json_once`
  - `test_failed_receipt_finish_keeps_the_paid_response`
  - `test_json_object_route_carries_the_output_schema_in_the_system_turn`
  - `test_json_schema_response_format_sends_strict_per_request_schema`
  - `test_json_schema_route_does_not_duplicate_the_schema_in_the_prompt`
  - `test_observer_control_exceptions_propagate_unchanged`
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

---
title: "learnloop.ai.providers.chatgpt_plan"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/providers/chatgpt_plan.py"
source_paths:
  - "src/learnloop/ai/providers/chatgpt_plan.py"
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
  - "learnloop.ai.providers.chatgpt_plan module"
  - "src/learnloop/ai/providers/chatgpt_plan.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai-providers"
---

# `learnloop.ai.providers.chatgpt_plan`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.providers.chatgpt_plan` exists within [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] to own the behavior summarized by its module contract: The ``chatgpt_plan`` transport: OpenAI models billed to the owner's ChatGPT plan.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/providers/chatgpt_plan.py](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py) |
| Source lines | 663 |
| Owning package | [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class ChatGPTPlanRequestRejected(AIProviderUnavailable)` ([source](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py), line 121) — The route refused this request's shape or this client; retrying the same body cannot help.
- `class ChatGPTPlanTransient(AIProviderUnavailable)` ([source](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py), line 125) — A network, server or availability failure; the credentials are kept.
- `class ChatGPTPlanUnauthorized(AIProviderUnavailable)` ([source](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py), line 129) — The access token was not accepted (401); the next request refreshes it first.
- `class ChatGPTPlanProviderClient(TokenUsageAccounting)` ([source](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py), line 140)
  - `__init__(self, provider_name: str, profile: AIProviderConfig, *, session: PlanSession | None=None) -> None` (line 143; internal)
  - `supports(self, capability: str) -> bool` (line 177; public)
  - `workspace_activity(self) -> list[str] | None` (line 185; public) — The paths (relative to the workspace root) the last workspace turn served.
  - `workspace_record(self) -> dict[str, Any] | None` (line 196; public) — The last workspace turn's full record: every call and every served range.
  - `interrupt(self) -> bool` (line 211; public)
  - `complete(self, request: StructuredRequest[Any]) -> Any` (line 220; public)
  - `_instructions(self, model_type: type[BaseModel]) -> str` (line 265; internal)
  - `_text_format(self, model_type: type[BaseModel]) -> dict[str, Any]` (line 272; internal)
  - `_respond(self, instructions: str, prompt: str, model_type: type[BaseModel], *, deadline: float, effort: str | None=None, extra: dict[str, Any] | None=None, budget: int | None=None) -> str` (line 278; internal)
  - `_workspace_turn(self, root: Path, instructions: str, prompt: str, model_type: type[BaseModel], *, deadline: float, effort: str | None, budget: int | None=None) -> str` (line 288; internal) — Serve ``root`` to the model (function calls or inline); returns the final text.
  - `_tool_loop(self, workspace: ServedWorkspace, instructions: str, prompt: str, model_type: type[BaseModel], *, deadline: float, effort: str | None, budget: int | None=None) -> str` (line 329; internal) — Rounds of function calls over ``workspace``, then the final answer.
  - `_send(self, body: dict[str, Any], *, deadline: float, extra: dict[str, Any] | None=None, budget: int | None=None) -> StreamResult` (line 392; internal) — One physical request, resent on a transient failure or after a token refresh.
  - `_stop_if_due(self, deadline: float) -> None` (line 422; internal)
  - `_send_once(self, body: dict[str, Any], *, deadline: float, observed_pause: dict[str, Any] | None, extra: dict[str, Any] | None=None, budget: int | None=None) -> StreamResult` (line 428; internal) — One physical request under its own receipt (the token step sends no model request).
  - `_meter(self, response: dict[str, Any], request_id: str | None, *, text: str | None=None, extra: dict[str, Any] | None=None) -> None` (line 494; internal) — Record usage on the receipt and the run before anything inspects the body.
  - `_classify(self, error: ResponsesError) -> Exception` (line 523; internal) — Map a ChatGPT-plan error to LearnLoop's taxonomy; records pause/eligibility state.
  - `_classified(self, error: ResponsesError) -> tuple[Exception, str | None]` (line 539; internal)
- `list_plan_models(base_url: str=CHATGPT_PLAN_API_BASE_URL, *, session: PlanSession | None=None, timeout: float=20.0) -> list[dict[str, str]]` ([source](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py), line 585) — The signed-in account's model picker: ``GET {base_url}/models``, ``visibility == "list"``.

### Module constants

- `PROVIDER_TYPE` ([src/learnloop/ai/providers/chatgpt_plan.py](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py), line 96)
- `DEFAULT_TIMEOUT_SECONDS` ([src/learnloop/ai/providers/chatgpt_plan.py](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py), line 97)
- `TURN_INPUT_FACTOR` ([src/learnloop/ai/providers/chatgpt_plan.py](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py), line 100)
- `_MAX_ATTEMPTS` ([src/learnloop/ai/providers/chatgpt_plan.py](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py), line 101)
- `_BACKOFF_SECONDS` ([src/learnloop/ai/providers/chatgpt_plan.py](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py), line 102)
- `_MIN_ATTEMPT_SECONDS` ([src/learnloop/ai/providers/chatgpt_plan.py](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py), line 103)
- `_JSON_ONLY` ([src/learnloop/ai/providers/chatgpt_plan.py](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py), line 104)
- `_TRANSIENT_CODES` ([src/learnloop/ai/providers/chatgpt_plan.py](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py), line 105)
- `_TRANSIENT_STATUSES` ([src/learnloop/ai/providers/chatgpt_plan.py](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py), line 109)
- `_CONFIG_CODES` ([src/learnloop/ai/providers/chatgpt_plan.py](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py), line 110)
- `_PLAN_UNAVAILABLE` ([src/learnloop/ai/providers/chatgpt_plan.py](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py), line 136)

### Explicit exports

`__all__` declares:

- `ChatGPTPlanProviderClient`
- `list_plan_models`
- `ChatGPTPlanRequestRejected`
- `ChatGPTPlanTransient`
- `ChatGPTPlanUnauthorized`
- `PROVIDER_TYPE`

## Internal implementation anchors

- `_count(value: Any) -> int | None` ([source](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py), line 629)
- `_prompt_schema(model_type: type[BaseModel]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py), line 635)
- `_with_budget(prompt: str, budget: int | None) -> str` ([source](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py), line 642) — ``prompt`` with the output budget stated once at its end (the route takes no ``max_output_tokens``).
- `_repair_prompt(text: str, model_type: type[BaseModel]) -> str` ([source](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py), line 650)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `ChatGPTPlanProviderClient`; statically calls `ChatGPTPlanProviderClient`
- [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]] — imports `list_plan_models`; statically calls `list_plan_models`
- [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]] — imports `list_plan_models`; statically calls `list_plan_models`

### Repository tooling consumers

- [scripts/benchmark_chatgpt_plan_latency.py](../../../../../../../scripts/benchmark_chatgpt_plan_latency.py); calls `ChatGPTPlanProviderClient`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/chatgpt_plan/oauth|learnloop.ai.chatgpt_plan.oauth]] — imports `EndpointUnreachable`, `urllib_call`; calls `urllib_call`
- [[Reference/Modules/learnloop/ai/chatgpt_plan/responses|learnloop.ai.chatgpt_plan.responses]] — imports `ResponsesError`, `ResponsesStream`, `StreamCancelled`, `StreamIncomplete`, `StreamResult`, `echo_items`, `error_fields`, `function_calls`, `request_body`; calls `ResponsesStream`, `echo_items`, `error_fields`, `function_calls`, `request_body`
- [[Reference/Modules/learnloop/ai/chatgpt_plan/session|learnloop.ai.chatgpt_plan.session]] — imports `ChatGPTPlanNotEligible`, `ChatGPTPlanNotEnabled`, `ChatGPTPlanUsageExhausted`, `ChatGPTSignInRequired`, `MANAGE_USAGE_URL`, `PlanSession`; calls `ChatGPTPlanNotEligible`, `ChatGPTPlanUsageExhausted`, `PlanSession`
- [[Reference/Modules/learnloop/ai/chatgpt_plan/workspace|learnloop.ai.chatgpt_plan.workspace]] — imports `INSTRUCTIONS_INLINE`, `INSTRUCTIONS_TOOLS`, `NAMESPACE`, `ServedWorkspace`, `WorkspaceTooLarge`; calls `ServedWorkspace`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIOutputTruncated`, `AIProviderUnavailable`, `AITurnTimeout`; calls `AIInterrupted`, `AIInvalidOutput`, `AIOutputTruncated`, `AIProviderUnavailable`, `AITurnTimeout`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `model_call`, `report_call_usage`, `single_request_active`; calls `model_call`, `report_call_usage`, `single_request_active`
- [[Reference/Modules/learnloop/ai/isolation|learnloop.ai.isolation]] — imports `TOOL_FREE`
- [[Reference/Modules/learnloop/ai/plan_fallback|learnloop.ai.plan_fallback]] — imports `note_plan_failure`; calls `note_plan_failure`
- [[Reference/Modules/learnloop/ai/strict_schema|learnloop.ai.strict_schema]] — imports `strict_output_schema`; calls `strict_output_schema`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `BOUNDED_STRUCTURED_COMPLETION`, `INTERRUPT`, `ISOLATED_TURN`, `READ_ONLY_WORKSPACE`, `STRUCTURED_COMPLETION`, `StructuredRequest`
- [[Reference/Modules/learnloop/ai/usage|learnloop.ai.usage]] — imports `TokenUsageAccounting`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `AIProviderConfig`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `CHATGPT_PLAN_API_BASE_URL`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `logging`, `pathlib`, `random`, `threading`, `time`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]], [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]], [[Reference/Modules/learnloop_sidecar/handlers/first_run|learnloop_sidecar.handlers.first_run]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_chatgpt_plan_landing.py](../../../../../../../tests/test_chatgpt_plan_landing.py) — direct import
  - `test_a_snapshot_diagnosis_on_the_plan_records_what_it_served_with_its_row_and_forecasts`
- [tests/test_chatgpt_plan_provider.py](../../../../../../../tests/test_chatgpt_plan_provider.py) — direct import
  - `test_a_401_under_single_request_fails_and_the_next_call_refreshes`
  - `test_an_interrupt_during_the_token_refresh_keeps_the_new_tokens_and_sends_nothing`
  - `test_incomplete_truncated_and_broken_streams`
  - `test_model_list_keeps_listed_models_in_server_order`
  - `test_rejected_structured_output_names_the_setting`
  - `test_single_request_never_repairs_or_retries`
- [tests/test_chatgpt_plan_workspace.py](../../../../../../../tests/test_chatgpt_plan_workspace.py) — direct import
  - `test_inline_mode_serves_a_workspace_over_its_budget_in_tools_mode`
  - `test_rejected_workspace_tools_name_the_inline_setting`
- [tests/test_plan_first_transport.py](../../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_doctor_names_a_configured_slug_the_account_does_not_list`
  - `test_f7_an_explicit_inline_never_sends_tools_and_a_tools_turn_caps_its_resent_input`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/providers/chatgpt_plan.py](../../../../../../../src/learnloop/ai/providers/chatgpt_plan.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

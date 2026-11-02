---
title: "learnloop.ai.chatgpt_plan.responses"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/chatgpt_plan/responses.py"
source_paths:
  - "src/learnloop/ai/chatgpt_plan/responses.py"
source_commit: "d71f18bdc6a66eacf669414d1754476801395a29"
source_commit_timestamp: "2026-10-15T16:01:49-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ai.chatgpt_plan"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.chatgpt_plan.responses module"
  - "src/learnloop/ai/chatgpt_plan/responses.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai-chatgpt-plan"
---

# `learnloop.ai.chatgpt_plan.responses`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/chatgpt_plan/_package|learnloop.ai.chatgpt_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.chatgpt_plan.responses` exists within [[Reference/Modules/learnloop/ai/chatgpt_plan/_package|learnloop.ai.chatgpt_plan]] to own the behavior summarized by its module contract: One streamed Responses API request on the ChatGPT plan.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/chatgpt_plan/responses.py](../../../../../../../src/learnloop/ai/chatgpt_plan/responses.py) |
| Source lines | 427 |
| Owning package | [[Reference/Modules/learnloop/ai/chatgpt_plan/_package|learnloop.ai.chatgpt_plan]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `d71f18bdc6a66eacf669414d1754476801395a29` |
| Commit timestamp | `2026-10-15T16:01:49-04:00` |

## Public API

- `class ResponsesError(Exception)` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/responses.py), line 69) — The request failed; ``code`` and ``param`` are the API's when it sent them.
  - `__init__(self, message: str, *, status: int | None, code: str | None=None, param: str | None=None, request_id: str | None=None, response: Mapping[str, Any] | None=None) -> None` (line 72; internal)
- `class StreamCancelled(Exception)` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/responses.py), line 82) — The deadline passed or the caller interrupted; ``reason`` says which.
  - `__init__(self, reason: str) -> None` (line 85; internal)
- `class StreamIncomplete(Exception)` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/responses.py), line 90)
  - `__init__(self, reason: str | None, response: Mapping[str, Any]) -> None` (line 91; internal)
- `class StreamResult` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/responses.py), line 98)
  - `output(self) -> list[dict[str, Any]]` (line 114; public) — The response's output items (the terminal response's, else the streamed ones).
- `request_body(*, model: str, instructions: str, prompt: str | None=None, text_format: Mapping[str, Any] | None, reasoning_effort: str | None=None, input_items: list[Mapping[str, Any]] | None=None, tools: list[Mapping[str, Any]] | None=None) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/responses.py), line 123) — One request body.
- `validate_tools(tools: list[Mapping[str, Any]]) -> None` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/responses.py), line 151) — The plan route takes function tools grouped in namespaces, and nothing hosted.
- `function_calls(output: list[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/responses.py), line 165) — The ``function_call`` items of a response's output, in order.
- `echo_items(output: list[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/responses.py), line 171) — A tool round's output as the next request's input (see :data:`_ECHOED_FIELDS`).
- `iter_sse(readline: Callable[[], bytes]) -> Iterator[tuple[str | None, str]]` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/responses.py), line 194) — ``(event name, data)`` per server-sent event (the WHATWG framing).
- `output_text(response: Mapping[str, Any]) -> tuple[str, str | None]` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/responses.py), line 221) — ``(text, refusal)`` from a terminal response's ``output`` items.
- `error_fields(payload: Any) -> tuple[str | None, str | None, str | None]` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/responses.py), line 239) — ``(code, message, param)`` from an error object, an error event or ``{"detail": ...}``.
- `class ResponsesStream` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/responses.py), line 267) — One request, one connection; ``cancel()`` shuts it down from any thread.
  - `__init__(self, base_url: str) -> None` (line 270; internal)
  - `cancel(self, reason: str) -> None` (line 282; public)
  - `_raise_if_cancelled(self) -> None` (line 294; internal)
  - `send(self, body: Mapping[str, Any], *, access_token: str, timeout: float, on_event: Callable[[str, Mapping[str, Any]], None] | None=None) -> StreamResult` (line 298; public)
  - `_read_stream(self, response: http.client.HTTPResponse, *, request_id: str | None, started: float, headers_at: float, on_event: Callable[[str, Mapping[str, Any]], None] | None) -> StreamResult` (line 356; internal)

### Module constants

- `UNSUPPORTED_FIELDS` ([src/learnloop/ai/chatgpt_plan/responses.py](../../../../../../../src/learnloop/ai/chatgpt_plan/responses.py), line 48)
- `REASONING_INCLUDE` ([src/learnloop/ai/chatgpt_plan/responses.py](../../../../../../../src/learnloop/ai/chatgpt_plan/responses.py), line 55)
- `_ECHOED_FIELDS` ([src/learnloop/ai/chatgpt_plan/responses.py](../../../../../../../src/learnloop/ai/chatgpt_plan/responses.py), line 61)
- `_ERROR_TEXT_LIMIT` ([src/learnloop/ai/chatgpt_plan/responses.py](../../../../../../../src/learnloop/ai/chatgpt_plan/responses.py), line 66)

### Explicit exports

`__all__` declares:

- `REASONING_INCLUDE`
- `ResponsesError`
- `ResponsesStream`
- `StreamCancelled`
- `StreamIncomplete`
- `StreamResult`
- `UNSUPPORTED_FIELDS`
- `echo_items`
- `error_fields`
- `function_calls`
- `iter_sse`
- `output_text`
- `request_body`
- `validate_tools`

## Internal implementation anchors

- `_str(value: Any) -> str | None` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/responses.py), line 255)
- `_request_id(headers: Mapping[str, str] | http.client.HTTPMessage) -> str | None` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/responses.py), line 259)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]] — imports `ResponsesError`, `ResponsesStream`, `StreamCancelled`, `StreamIncomplete`, `StreamResult`, `echo_items`, `error_fields`, `function_calls`, `request_body`; statically calls `ResponsesStream`, `echo_items`, `error_fields`, `function_calls`, `request_body`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `http`, `json`, `socket`, `ssl`, `threading`, `time`, `typing`, `urllib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_chatgpt_plan_provider.py](../../../../../../../tests/test_chatgpt_plan_provider.py) — direct import
  - `test_request_shape_follows_the_plan_route_rules`
- [tests/test_chatgpt_plan_workspace.py](../../../../../../../tests/test_chatgpt_plan_workspace.py) — direct import
  - `test_echo_items_keep_only_what_store_false_can_resend`
  - `test_tool_rounds_serve_files_and_record_each_served_entry`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/chatgpt_plan/responses.py](../../../../../../../src/learnloop/ai/chatgpt_plan/responses.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

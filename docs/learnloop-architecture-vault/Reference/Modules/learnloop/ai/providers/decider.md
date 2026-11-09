---
title: "learnloop.ai.providers.decider"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/providers/decider.py"
source_paths:
  - "src/learnloop/ai/providers/decider.py"
source_commit: "workspace/uncommitted @ HEAD 79532f7149b554db05a40c2ae1dbde68d9efec5a"
source_commit_timestamp: "2026-11-09T16:01:49-05:00"
source_worktree_state: "modified"
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
  - "learnloop.ai.providers.decider module"
  - "src/learnloop/ai/providers/decider.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai-providers"
---

# `learnloop.ai.providers.decider`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.providers.decider` exists within [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] to own the behavior summarized by its module contract: The ``decider`` transport: Perplexity's Decider over OpenRouter or direct.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/providers/decider.py](../../../../../../../src/learnloop/ai/providers/decider.py) |
| Source lines | 360 |
| Owning package | [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 79532f7149b554db05a40c2ae1dbde68d9efec5a` |
| Commit timestamp | `2026-11-09T16:01:49-05:00` |

## Public API

- `class DecisionRequestFailed(AIProviderUnavailable)` ([source](../../../../../../../src/learnloop/ai/providers/decider.py), line 81) — The provider answered with an error status; nothing was parsed.
  - `__init__(self, message: str, *, status: int, retry_after: float | None=None) -> None` (line 84; internal)
- `class DeciderSettings` ([source](../../../../../../../src/learnloop/ai/providers/decider.py), line 91) — A profile's effective, non-secret settings (``api`` fills the gaps).
  - `as_dict(self) -> dict[str, Any]` (line 103; public)
- `resolved_decider_settings(profile: AIProviderConfig) -> DeciderSettings` ([source](../../../../../../../src/learnloop/ai/providers/decider.py), line 113)
- `encode_body(body: Mapping[str, Any]) -> bytes` ([source](../../../../../../../src/learnloop/ai/providers/decider.py), line 133) — Deterministic bytes that keep insertion order.
- `estimate_input_tokens(body: Mapping[str, Any]) -> int` ([source](../../../../../../../src/learnloop/ai/providers/decider.py), line 143)
- `redact_key_like(text: str, secrets: tuple[str, ...]=()) -> str` ([source](../../../../../../../src/learnloop/ai/providers/decider.py), line 161) — ``text`` without the given secrets or anything shaped like a key.
- `class DeciderProviderClient` ([source](../../../../../../../src/learnloop/ai/providers/decider.py), line 197) — ``DecisionClient`` over HTTP; never a chat or structured-completion transport.
  - `__init__(self, provider_name: str, profile: AIProviderConfig, *, http: HttpTransport | None=None) -> None` (line 202; internal)
  - `supports(self, capability: str) -> bool` (line 230; public)
  - `estimated_cost(self, input_tokens: int) -> float` (line 233; public) — Input-only price; the Decider's output tokens are free.
  - `decide(self, state: DecisionState, questions: Mapping[str, Question], *, purpose: str, timeout_seconds: float | None=None) -> DecisionResult` (line 238; public) — One physical request.
- `probe_decider_endpoint(profile: AIProviderConfig, *, http: HttpTransport | None=None, timeout: float=10.0) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/ai/providers/decider.py), line 306) — Free reachability check: OpenRouter's public endpoint listing for the model.

### Module constants

- `DECISIONS` ([src/learnloop/ai/providers/decider.py](../../../../../../../src/learnloop/ai/providers/decider.py), line 47)
- `_DIALECTS` ([src/learnloop/ai/providers/decider.py](../../../../../../../src/learnloop/ai/providers/decider.py), line 49)
- `DEFAULT_TIMEOUT_SECONDS` ([src/learnloop/ai/providers/decider.py](../../../../../../../src/learnloop/ai/providers/decider.py), line 63)
- `BYTES_PER_TOKEN_ESTIMATE` ([src/learnloop/ai/providers/decider.py](../../../../../../../src/learnloop/ai/providers/decider.py), line 66)
- `_ERROR_TEXT_LIMIT` ([src/learnloop/ai/providers/decider.py](../../../../../../../src/learnloop/ai/providers/decider.py), line 68)
- `_KEY_LIKE` ([src/learnloop/ai/providers/decider.py](../../../../../../../src/learnloop/ai/providers/decider.py), line 72)
- `_REDACTED` ([src/learnloop/ai/providers/decider.py](../../../../../../../src/learnloop/ai/providers/decider.py), line 75)

### Explicit exports

`__all__` declares:

- `DECISIONS`
- `DeciderProviderClient`
- `DeciderSettings`
- `DecisionRequestFailed`
- `HttpTransport`
- `encode_body`
- `estimate_input_tokens`
- `probe_decider_endpoint`
- `redact_key_like`
- `resolved_decider_settings`

## Internal implementation anchors

- `_urllib_transport(method: str, url: str, headers: Mapping[str, str], body: bytes | None, timeout: float) -> tuple[int, Mapping[str, str], bytes]` ([source](../../../../../../../src/learnloop/ai/providers/decider.py), line 147)
- `_error_message(raw: bytes, secrets: tuple[str, ...]=()) -> str` ([source](../../../../../../../src/learnloop/ai/providers/decider.py), line 170)
- `_retry_after(headers: Mapping[str, str]) -> float | None` ([source](../../../../../../../src/learnloop/ai/providers/decider.py), line 187)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]] — imports `resolved_decider_settings`; statically calls `resolved_decider_settings`
- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `DeciderProviderClient`; statically calls `DeciderProviderClient`
- [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]] — imports `resolved_decider_settings`; statically calls `resolved_decider_settings`
- [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]] — imports `DeciderProviderClient`, `estimate_input_tokens`, `probe_decider_endpoint`, `resolved_decider_settings`; statically calls `DeciderProviderClient`, `estimate_input_tokens`, `probe_decider_endpoint`, `resolved_decider_settings`
- [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] — imports `estimate_input_tokens`, `probe_decider_endpoint`; statically calls `estimate_input_tokens`, `probe_decider_endpoint`
- [[Reference/Modules/learnloop/diagnosis/offline_review/runner|learnloop.diagnosis.offline_review.runner]] — imports `resolved_decider_settings`; statically calls `resolved_decider_settings`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/decisions|learnloop.ai.decisions]] — imports `DecisionResult`, `DecisionState`, `Question`, `parse_response`, `request_body`, `validate_questions`; calls `parse_response`, `request_body`, `validate_questions`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIProviderUnavailable`; calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `model_call`, `report_call_usage`; calls `model_call`, `report_call_usage`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `AIProviderConfig`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `DEFAULT_DECIDER_MODEL`, `DEFAULT_DECIDER_PRICE_PER_MILLION_INPUT`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `http`, `json`, `math`, `os`, `re`, `typing`, `urllib`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/backfill|learnloop.adaptive_difficulty.backfill]], [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]], [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]], [[Reference/Modules/learnloop/cli/probability_arms|learnloop.cli.probability_arms]], [[Reference/Modules/learnloop/daily_plan/router_runtime|learnloop.daily_plan.router_runtime]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_decider_client.py](../../../../../../../tests/test_decider_client.py) — direct import
  - `test_a_rejected_request_keeps_its_status_and_redacted_error_on_the_receipt`
  - `test_a_transport_error_echoing_a_key_reaches_neither_receipt_nor_caller`
  - `test_an_unreachable_endpoint_is_recorded_as_network_without_a_status`
  - `test_error_statuses_surface_without_parsing`
  - `test_missing_key_and_oversized_state_refuse_before_any_request`
  - `test_openrouter_dialect_posts_the_typed_request_and_parses_typed_answers`
  - `test_probe_reads_the_free_listing_without_a_key`
  - `test_redaction_keeps_slugs_and_drops_key_shapes`
  - `test_settings_resolve_from_the_dialect`
- [tests/test_decider_landing.py](../../../../../../../tests/test_decider_landing.py) — direct import
  - `test_inside_an_automatic_builds_request_gate_the_span_check_is_admitted_and_settled`
- [tests/test_probability_prep.py](../../../../../../../tests/test_probability_prep.py) — direct import
  - `test_rate_limits_retry_within_caps_and_malformed_answers_fail_closed`
- [tests/test_router_outcomes.py](../../../../../../../tests/test_router_outcomes.py) — direct import
  - `test_the_replayer_rebuilds_router_outcomes_deterministically_with_no_model_call`
- [tests/test_router_r2a_serving.py](../../../../../../../tests/test_router_r2a_serving.py) — direct import
  - `test_router_outcomes_v2_replay_twice_with_no_model_call`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/providers/decider.py](../../../../../../../src/learnloop/ai/providers/decider.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

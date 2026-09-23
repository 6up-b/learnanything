---
title: "learnloop.ai.execution"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/execution.py"
source_paths:
  - "src/learnloop/ai/execution.py"
source_commit: "c21b9745d699c2d212cc505c0ddf573184f400f9"
source_commit_timestamp: "2026-09-23T12:13:26-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop.ai"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.execution module"
  - "src/learnloop/ai/execution.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.execution`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.execution` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: Request-scoped limits and durable call observations, without storage coupling.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/execution.py](../../../../../../src/learnloop/ai/execution.py) |
| Source lines | 154 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `c21b9745d699c2d212cc505c0ddf573184f400f9` |
| Commit timestamp | `2026-09-23T12:13:26-04:00` |

## Public API

- `report_call_usage(values: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/ai/execution.py), line 30)
- `content_key(payload: Any) -> str` ([source](../../../../../../src/learnloop/ai/execution.py), line 40)
- `model_settings(client: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ai/execution.py), line 44) — The client settings that change what a request produces.
- `observe_model_calls(observer: Callable[[str, dict[str, Any]], Any])` ([source](../../../../../../src/learnloop/ai/execution.py), line 65)
- `generation_limit(output_tokens: int | None)` ([source](../../../../../../src/learnloop/ai/execution.py), line 74)
- `output_limit() -> int | None` ([source](../../../../../../src/learnloop/ai/execution.py), line 86)
- `observed_sdk_turn(function)` ([source](../../../../../../src/learnloop/ai/execution.py), line 90)
- `model_call(client: Any, *, purpose: str, prompt: Any=None, schema: Any=None, budget: int | None=None)` ([source](../../../../../../src/learnloop/ai/execution.py), line 101)

## Internal implementation anchors

- `_failure_status(exc: BaseException) -> str` ([source](../../../../../../src/learnloop/ai/execution.py), line 135)
- `_record_finish(observer: Callable[[str, dict[str, Any]], Any], call_id: str, metadata: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/ai/execution.py), line 143) — Best-effort: the durable start is the safety guarantee, the finish is telemetry.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `generation_limit`, `observed_sdk_turn`, `output_limit`, `report_call_usage`; statically calls `generation_limit`, `output_limit`, `report_call_usage`
- [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]] — imports `report_call_usage`; statically calls `report_call_usage`
- [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] — imports `model_call`, `report_call_usage`; statically calls `model_call`, `report_call_usage`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `model_call`, `output_limit`; statically calls `model_call`, `output_limit`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `observe_model_calls`; statically calls `observe_model_calls`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `observe_model_calls`; statically calls `observe_model_calls`
- [[Reference/Modules/learnloop/content/pipeline/runner|learnloop.content.pipeline.runner]] — imports `observe_model_calls`; statically calls `observe_model_calls`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `content_key`; statically calls `content_key`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `content_key`, `generation_limit`, `model_settings`; statically calls `content_key`, `generation_limit`, `model_settings`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `content_key`, `generation_limit`, `model_settings`; statically calls `content_key`, `generation_limit`, `model_settings`
- [[Reference/Modules/learnloop/reader/reader_requests|learnloop.reader.reader_requests]] — imports `observe_model_calls`; statically calls `observe_model_calls`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `observe_model_calls`; statically calls `observe_model_calls`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIOutputTruncated`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `contextvars`, `datetime`, `functools`, `hashlib`, `json`, `logging`, `typing`, `uuid`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]], [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]], [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]], [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] and 7 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_agent_run_tokens.py](../../../../../../tests/test_agent_run_tokens.py) — direct import
  - `test_usage_readers_leave_the_open_receipt_alone`
- [tests/test_ingestion_checkpoints.py](../../../../../../tests/test_ingestion_checkpoints.py) — direct import
  - `test_codex_does_not_repair_when_reported_output_consumed_the_budget`
  - `test_retry_policy_records_each_failed_request_with_unknown_usage`
  - `test_truncation_or_exhausted_repair_budget_records_usage_without_repaying`
- [tests/test_model_usage_report.py](../../../../../../tests/test_model_usage_report.py) — direct import
- [tests/test_openai_chat_client.py](../../../../../../tests/test_openai_chat_client.py) — direct import
  - `test_failed_receipt_finish_keeps_the_paid_response`
  - `test_observer_control_exceptions_propagate_unchanged`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/execution.py](../../../../../../src/learnloop/ai/execution.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

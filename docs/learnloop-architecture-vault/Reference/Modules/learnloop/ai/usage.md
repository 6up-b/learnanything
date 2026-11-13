---
title: "learnloop.ai.usage"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/usage.py"
source_paths:
  - "src/learnloop/ai/usage.py"
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
  - "learnloop.ai.usage module"
  - "src/learnloop/ai/usage.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.usage`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.usage` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: Provider-reported token accounting (spec_diagnostic_augmentation_v1.md §2 A7).

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/usage.py](../../../../../../src/learnloop/ai/usage.py) |
| Source lines | 259 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class TokenUsage` ([source](../../../../../../src/learnloop/ai/usage.py), line 34) — What one or more model calls actually cost, as the provider reported it.
  - `__add__(self, other: TokenUsage) -> TokenUsage` (line 47; internal)
  - `total_tokens(self) -> int` (line 55; public)
- `class TokenUsageAccounting` ([source](../../../../../../src/learnloop/ai/usage.py), line 59) — Per-client token accumulator mixed into every provider client.
  - `_usage_mutex(self) -> threading.Lock` (line 79; internal)
  - `record_token_usage(self, input_tokens: int, output_tokens: int) -> None` (line 89; public) — Add one model call's reported usage.
  - `consume_usage(self) -> TokenUsage` (line 103; public) — Read and reset.
  - `snapshot_usage(self) -> TokenUsage` (line 117; public) — Read without draining the enclosing run's accounting.
- `snapshot_client_usage(client: Any | None) -> TokenUsage` ([source](../../../../../../src/learnloop/ai/usage.py), line 123)
- `class UsageMeter` ([source](../../../../../../src/learnloop/ai/usage.py), line 131) — Provider-reported usage of the calls a client made since the meter started.
  - `__init__(self, client: Any | None)` (line 140; internal)
  - `reported(self) -> TokenUsage` (line 144; public)
  - `output_charge(self, estimate: int) -> int` (line 152; public)
- `consume_client_usage(client: Any | None) -> TokenUsage` ([source](../../../../../../src/learnloop/ai/usage.py), line 156) — Drain ``client``'s accumulator, tolerating clients that have none.
- `usage_from_chat_response(response: Any) -> tuple[int, int]` ([source](../../../../../../src/learnloop/ai/usage.py), line 177) — Pull (input, output) tokens off an OpenAI-shaped chat completion.
- `receipt_fields_from_chat_response(response: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/ai/usage.py), line 199) — The call-receipt view of an OpenAI-shaped chat completion.

### Module constants

- `_USAGE_INIT_LOCK` ([src/learnloop/ai/usage.py](../../../../../../src/learnloop/ai/usage.py), line 30)

## Internal implementation anchors

- `_attr_or_key(payload: Any, name: str) -> Any` ([source](../../../../../../src/learnloop/ai/usage.py), line 226)
- `_coerce_tokens(value: Any) -> int` ([source](../../../../../../src/learnloop/ai/usage.py), line 232) — Non-negative int or 0.
- `_optional_tokens(value: Any) -> int | None` ([source](../../../../../../src/learnloop/ai/usage.py), line 244)
- `_optional_cost(value: Any) -> float | None` ([source](../../../../../../src/learnloop/ai/usage.py), line 254)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]] — imports `TokenUsageAccounting`
- [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] — imports `TokenUsageAccounting`, `receipt_fields_from_chat_response`, `usage_from_chat_response`; statically calls `receipt_fields_from_chat_response`, `usage_from_chat_response`
- [[Reference/Modules/learnloop/ai/providers/openai_embedding|learnloop.ai.providers.openai_embedding]] — imports `receipt_fields_from_chat_response`; statically calls `receipt_fields_from_chat_response`
- [[Reference/Modules/learnloop/ai/runs|learnloop.ai.runs]] — imports `TokenUsage`, `consume_client_usage`; statically calls `consume_client_usage`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `TokenUsage`
- [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]] — imports `consume_client_usage`; statically calls `consume_client_usage`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `consume_client_usage`; statically calls `consume_client_usage`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `TokenUsage`, `UsageMeter`, `consume_client_usage`; statically calls `TokenUsage`, `UsageMeter`, `consume_client_usage`
- [[Reference/Modules/learnloop/content/synthesis/source_unit_inventory|learnloop.content.synthesis.source_unit_inventory]] — imports `UsageMeter`; statically calls `UsageMeter`
- [[Reference/Modules/learnloop/content/synthesis/vault_epigraphs|learnloop.content.synthesis.vault_epigraphs]] — imports `consume_client_usage`; statically calls `consume_client_usage`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `TokenUsage`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `math`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/providers/chatgpt_plan|learnloop.ai.providers.chatgpt_plan]], [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]], [[Reference/Modules/learnloop/ai/providers/openai_embedding|learnloop.ai.providers.openai_embedding]], [[Reference/Modules/learnloop/ai/runs|learnloop.ai.runs]], [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] and 6 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/facet_identity_fakes.py](../../../../../../tests/facet_identity_fakes.py) — direct import
- [tests/http_provider_double.py](../../../../../../tests/http_provider_double.py) — direct import
- [tests/structured_ai.py](../../../../../../tests/structured_ai.py) — direct import
- [tests/test_agent_run_tokens.py](../../../../../../tests/test_agent_run_tokens.py) — direct import
  - `test_accounting_state_is_per_instance`
  - `test_add_agent_run_usage_is_additive`
  - `test_chat_client_accumulates_usage_across_calls_and_resets_on_consume`
  - `test_chat_client_survives_a_response_with_no_usage`
  - `test_complete_agent_run_records_actual_usage`
  - `test_complete_agent_run_without_usage_preserves_recorded_cost`
  - `test_consume_client_usage_tolerates_a_client_without_the_method`
  - `test_finish_agent_run_without_a_client_leaves_cost_untouched`
  - `test_grading_path_persists_actual_tokens`
  - `test_usage_from_chat_response_never_raises`
  - `test_usage_readers_leave_the_open_receipt_alone`
- [tests/test_chatgpt_plan_cli.py](../../../../../../tests/test_chatgpt_plan_cli.py) — direct import
  - `test_latency_stops_a_later_metered_provider_once_the_shared_cap_is_spent`
- [tests/test_scoreboard.py](../../../../../../tests/test_scoreboard.py) — direct import
  - `test_tokens_metric_reports_the_ratio_over_metered_episodes`
- [tests/test_synthesis_tail_golden.py](../../../../../../tests/test_synthesis_tail_golden.py) — direct import
- [tests/test_vault_epigraphs.py](../../../../../../tests/test_vault_epigraphs.py) — direct import
- [tests/text_gap_fakes.py](../../../../../../tests/text_gap_fakes.py) — direct import

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/usage.py](../../../../../../src/learnloop/ai/usage.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.ai.agent_harness"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/agent_harness.py"
source_paths:
  - "src/learnloop/ai/agent_harness.py"
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
  - "learnloop.ai.agent_harness module"
  - "src/learnloop/ai/agent_harness.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.agent_harness`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.agent_harness` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: A Codex (agent-harness) profile is refused for every task.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/agent_harness.py](../../../../../../src/learnloop/ai/agent_harness.py) |
| Source lines | 65 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class AgentHarnessRefused(AIProviderUnavailable)` ([source](../../../../../../src/learnloop/ai/agent_harness.py), line 22) — A Codex (agent-harness) profile was selected; it serves nothing.
- `is_agent_harness_type(profile_type: str | None) -> bool` ([source](../../../../../../src/learnloop/ai/agent_harness.py), line 26)
- `is_agent_harness_profile(profile: Any) -> bool` ([source](../../../../../../src/learnloop/ai/agent_harness.py), line 30)
- `refusal_message(provider_name: str) -> str` ([source](../../../../../../src/learnloop/ai/agent_harness.py), line 34)
- `harness_refusal(provider_name: str, profile: Any) -> str | None` ([source](../../../../../../src/learnloop/ai/agent_harness.py), line 42) — Why ``profile`` may not serve, or ``None`` when it is not a Codex profile.
- `refuse_agent_harness(provider_name: str, profile: Any) -> None` ([source](../../../../../../src/learnloop/ai/agent_harness.py), line 50) — Raise :class:`AgentHarnessRefused` for a Codex profile.

### Explicit exports

`__all__` declares:

- `AgentHarnessRefused`
- `harness_refusal`
- `is_agent_harness_profile`
- `is_agent_harness_type`
- `refusal_message`
- `refuse_agent_harness`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `refuse_agent_harness`; statically calls `refuse_agent_harness`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `harness_refusal`, `is_agent_harness_profile`; statically calls `harness_refusal`, `is_agent_harness_profile`
- [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]] — imports `harness_refusal`; statically calls `harness_refusal`
- [[Reference/Modules/learnloop/ops/plan_transport|learnloop.ops.plan_transport]] — imports `is_agent_harness_profile`; statically calls `is_agent_harness_profile`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `is_agent_harness_profile`; statically calls `is_agent_harness_profile`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `AGENT_HARNESS_PROFILE_TYPES`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]], [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]], [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]], [[Reference/Modules/learnloop/ops/plan_transport|learnloop.ops.plan_transport]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/http_provider_double.py](../../../../../../tests/http_provider_double.py) — direct import
- [tests/test_codex_transport_retired.py](../../../../../../tests/test_codex_transport_retired.py) — direct import
  - `test_an_old_config_naming_codex_loads_and_every_entry_refuses_it_clearly`
- [tests/test_e0_review_round4_followup.py](../../../../../../tests/test_e0_review_round4_followup.py) — direct import
  - `test_the_label_passes_never_reach_a_codex_turn`
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_a_harness_profile_raises_before_any_process`
  - `test_an_old_opt_in_still_loads_and_admits_nothing`
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_sidecar_submit_attempt_never_falls_back_to_codex_when_routed_ai_unavailable`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/agent_harness.py](../../../../../../src/learnloop/ai/agent_harness.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

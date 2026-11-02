---
title: "learnloop.ai.agent_harness"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/agent_harness.py"
source_paths:
  - "src/learnloop/ai/agent_harness.py"
source_commit: "42ab0bc90d513d76d7b0eea692d52330b51a8385"
source_commit_timestamp: "2026-10-23T10:49:09-04:00"
source_worktree_state: "clean"
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
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.agent_harness` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: The Codex agent harness is refused for serving unless the owner opts in.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/agent_harness.py](../../../../../../src/learnloop/ai/agent_harness.py) |
| Source lines | 72 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `42ab0bc90d513d76d7b0eea692d52330b51a8385` |
| Commit timestamp | `2026-10-23T10:49:09-04:00` |

## Public API

- `class AgentHarnessRefused(AIProviderUnavailable)` ([source](../../../../../../src/learnloop/ai/agent_harness.py), line 27) — A Codex (agent-harness) profile was selected without the owner's opt-in.
- `is_agent_harness_type(profile_type: str | None) -> bool` ([source](../../../../../../src/learnloop/ai/agent_harness.py), line 31)
- `is_agent_harness_profile(profile: Any) -> bool` ([source](../../../../../../src/learnloop/ai/agent_harness.py), line 35)
- `refusal_message(provider_name: str) -> str` ([source](../../../../../../src/learnloop/ai/agent_harness.py), line 39)
- `harness_refusal(provider_name: str, profile: Any, *, opt_in: bool) -> str | None` ([source](../../../../../../src/learnloop/ai/agent_harness.py), line 48) — Why ``profile`` may not serve, or ``None`` when it may (not Codex, or opted in).
- `require_harness_opt_in(provider_name: str, profile: Any, *, opt_in: bool) -> None` ([source](../../../../../../src/learnloop/ai/agent_harness.py), line 56) — Raise :class:`AgentHarnessRefused` for a Codex profile without the opt-in.

### Module constants

- `OPT_IN_SETTING` ([src/learnloop/ai/agent_harness.py](../../../../../../src/learnloop/ai/agent_harness.py), line 24)

### Explicit exports

`__all__` declares:

- `AgentHarnessRefused`
- `OPT_IN_SETTING`
- `harness_refusal`
- `is_agent_harness_profile`
- `is_agent_harness_type`
- `refusal_message`
- `require_harness_opt_in`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `require_harness_opt_in`; statically calls `require_harness_opt_in`
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

- [tests/test_codex_lockdown_round2.py](../../../../../../tests/test_codex_lockdown_round2.py) — direct import
  - `test_an_http_profile_is_refused_by_the_lockdown`
- [tests/test_plan_first_transport.py](../../../../../../tests/test_plan_first_transport.py) — direct import
  - `test_a_harness_profile_without_the_opt_in_raises_before_any_process`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/agent_harness.py](../../../../../../src/learnloop/ai/agent_harness.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

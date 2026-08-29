---
title: "learnloop.ai.providers.openrouter"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/providers/openrouter.py"
source_paths:
  - "src/learnloop/ai/providers/openrouter.py"
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
  - "learnloop.ai.providers.openrouter module"
  - "src/learnloop/ai/providers/openrouter.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai-providers"
---

# `learnloop.ai.providers.openrouter`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps openrouter behavior inside its owning package, [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]]. Its public surface centers on `OpenRouterProviderClient`.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/providers/openrouter.py](../../../../../../../src/learnloop/ai/providers/openrouter.py) |
| Source lines | 37 |
| Owning package | [[Reference/Modules/learnloop/ai/providers/_package|learnloop.ai.providers]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class OpenRouterProviderClient(OpenAIChatProviderClient)` ([source](../../../../../../../src/learnloop/ai/providers/openrouter.py), line 11) — OpenAI-compatible chat client pointed at OpenRouter.
  - `_default_headers(self) -> dict[str, str] | None` (line 26; internal)
  - `_reasoning_kwargs(self) -> dict[str, Any]` (line 32; internal)

### Module constants

- `OPENROUTER_BASE_URL` ([src/learnloop/ai/providers/openrouter.py](../../../../../../../src/learnloop/ai/providers/openrouter.py), line 7)
- `OPENROUTER_API_KEY_ENV` ([src/learnloop/ai/providers/openrouter.py](../../../../../../../src/learnloop/ai/providers/openrouter.py), line 8)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `OpenRouterProviderClient`; statically calls `OpenRouterProviderClient`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] — imports `OpenAIChatProviderClient`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_multimodal_client.py](../../../../../../../tests/test_multimodal_client.py) — direct import
  - `test_openrouter_inherits_media_methods_with_headers`
- [tests/test_openrouter_client.py](../../../../../../../tests/test_openrouter_client.py) — direct import
  - `test_make_ai_provider_client_dispatches_openrouter`
  - `test_openrouter_attribution_headers_configurable`
  - `test_openrouter_defaults_base_url_key_env_and_title_header`
  - `test_openrouter_missing_key_raises`
  - `test_openrouter_profile_base_url_overrides_default`
  - `test_openrouter_reasoning_effort_maps_to_unified_body`
  - `test_openrouter_supports_exercise_authoring`
  - `test_openrouter_thinking_disabled_sends_no_reasoning`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/providers/openrouter.py](../../../../../../../src/learnloop/ai/providers/openrouter.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

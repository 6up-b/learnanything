---
title: "learnloop.ai.client"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/client.py"
source_paths:
  - "src/learnloop/ai/client.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
package: "learnloop.ai"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.client module"
  - "src/learnloop/ai/client.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.client`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps client behavior inside its owning package, [[Reference/Modules/learnloop/ai/_package|learnloop.ai]]. Its public surface centers on `make_ai_provider_client`, `make_ai_provider_client_from_profile`.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/client.py](../../../../../../src/learnloop/ai/client.py) |
| Source lines | 57 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `make_ai_provider_client(config: LearnLoopConfig, vault_root: Path, *, provider_name: str | None=None, timeout_seconds: int | None=None) -> AIProviderClient` ([source](../../../../../../src/learnloop/ai/client.py), line 17)
- `make_ai_provider_client_from_profile(provider_name: str, profile: AIProviderConfig, vault_root: Path) -> AIProviderClient` ([source](../../../../../../src/learnloop/ai/client.py), line 35)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `make_ai_provider_client`; statically calls `make_ai_provider_client`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `AIProviderClient`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `AIProviderClient`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `AIProviderClient`
- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `AIProviderClient`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `AIProviderClient`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`; calls `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `CodexSDKProviderClient`; calls `CodexSDKProviderClient`
- [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]] — imports `HttpAdapterProviderClient`; calls `HttpAdapterProviderClient`
- [[Reference/Modules/learnloop/ai/providers/openai_chat|learnloop.ai.providers.openai_chat]] — imports `OpenAIChatProviderClient`; calls `OpenAIChatProviderClient`
- [[Reference/Modules/learnloop/ai/providers/openrouter|learnloop.ai.providers.openrouter]] — imports `OpenRouterProviderClient`; calls `OpenRouterProviderClient`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `OperationClient`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `AIProviderConfig`, `LearnLoopConfig`

### Platform and third-party dependencies

- Standard library: `__future__`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]], [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]], [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ai_config.py](../../../../../../tests/test_ai_config.py) — direct import
  - `test_global_ai_timeout_is_applied_to_codex_sdk_profiles`
- [tests/test_openrouter_client.py](../../../../../../tests/test_openrouter_client.py) — direct import
  - `test_make_ai_provider_client_dispatches_openrouter`
- [tests/test_provider_resolution_parity.py](../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_named_codex_profile_identity_survives_provider_construction`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/client.py](../../../../../../src/learnloop/ai/client.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.ai.routing"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/routing.py"
source_paths:
  - "src/learnloop/ai/routing.py"
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
  - "learnloop.ai.routing module"
  - "src/learnloop/ai/routing.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.routing`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.routing` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: Provider selection and the single AI client composition root.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/routing.py](../../../../../../src/learnloop/ai/routing.py) |
| Source lines | 308 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class AIProviderSelection` ([source](../../../../../../src/learnloop/ai/routing.py), line 63)
- `class ResolvedClient` ([source](../../../../../../src/learnloop/ai/routing.py), line 70) — Typed outcome of provider selection, readiness, fallback, and build.
  - `ready(self) -> bool` (line 88; public)
  - `__iter__(self) -> Iterator[Any]` (line 91; internal)
- `provider_for_task(config: LearnLoopConfig, task: AITask, *, explicit_provider: str | None=None, allow_env: bool=True) -> AIProviderSelection` ([source](../../../../../../src/learnloop/ai/routing.py), line 97) — Select a configured name with explicit > environment > route precedence.
- `provider_for_operation(config: LearnLoopConfig, operation: str, *, explicit_provider: str | None=None, allow_env: bool=True) -> AIProviderSelection` ([source](../../../../../../src/learnloop/ai/routing.py), line 117)
- `fallback_provider_for(config: LearnLoopConfig, selection: AIProviderSelection) -> str | None` ([source](../../../../../../src/learnloop/ai/routing.py), line 136)
- `runtime_for_provider(vault_root: Path, config: LearnLoopConfig, provider_name: str) -> AIRuntimeReport` ([source](../../../../../../src/learnloop/ai/routing.py), line 143) — Return one provider-neutral readiness report for any configured name.
- `client_for_provider(vault_root: Path, config: LearnLoopConfig, provider_name: str, *, timeout_seconds: int | None=None) -> Any | None` ([source](../../../../../../src/learnloop/ai/routing.py), line 161) — Build a configured provider client, returning no client for manual mode.
- `ready_client_for_task(vault_root: Path, config: LearnLoopConfig, task: AITask, *, explicit: str | None=None, allow_env: bool=True, timeout_seconds: int | None=None) -> ResolvedClient` ([source](../../../../../../src/learnloop/ai/routing.py), line 188) — Resolve selection, readiness, fallback, and construction exactly once.

### Module constants

- `MANUAL_PROVIDER` ([src/learnloop/ai/routing.py](../../../../../../src/learnloop/ai/routing.py), line 16)
- `ROUTE_FOR_OPERATION` ([src/learnloop/ai/routing.py](../../../../../../src/learnloop/ai/routing.py), line 33)

### Explicit exports

`__all__` declares:

- `MANUAL_PROVIDER`
- `ROUTE_FOR_OPERATION`
- `AIProviderSelection`
- `AITask`
- `ResolvedClient`
- `client_for_provider`
- `fallback_provider_for`
- `provider_for_operation`
- `provider_for_task`
- `ready_client_for_task`
- `runtime_for_provider`

## Internal implementation anchors

- `_resolve_selected_provider(vault_root: Path, config: LearnLoopConfig, selection: AIProviderSelection, provider_name: str, *, timeout_seconds: int | None, fallback_from: str | None=None) -> ResolvedClient` ([source](../../../../../../src/learnloop/ai/routing.py), line 235)
- `_manual_resolution(selection: AIProviderSelection, *, fallback_from: str | None=None) -> ResolvedClient` ([source](../../../../../../src/learnloop/ai/routing.py), line 274)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `client_for_provider`, `fallback_provider_for`, `provider_for_task`, `ready_client_for_task`, `runtime_for_provider`; statically calls `client_for_provider`, `fallback_provider_for`, `provider_for_task`, `ready_client_for_task`, `runtime_for_provider`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `provider_for_task`, `ready_client_for_task`; statically calls `provider_for_task`, `ready_client_for_task`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `runtime_for_provider`; statically calls `runtime_for_provider`
- [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]] — imports `ready_client_for_task`, `runtime_for_provider`; statically calls `ready_client_for_task`, `runtime_for_provider`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `ready_client_for_task`; statically calls `ready_client_for_task`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `ready_client_for_task`, `runtime_for_provider`; statically calls `ready_client_for_task`, `runtime_for_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `MANUAL_PROVIDER`, `client_for_provider`, `ready_client_for_task`, `runtime_for_provider`; statically calls `client_for_provider`, `ready_client_for_task`, `runtime_for_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]] — imports `provider_for_task`; statically calls `provider_for_task`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/client|learnloop.ai.client]] — imports `make_ai_provider_client`; calls `make_ai_provider_client`
- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/runtime|learnloop.ai.runtime]] — imports `AIRuntimeReport`, `check_ai_runtime`; calls `AIRuntimeReport`, `check_ai_runtime`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `os`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]], [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]], [[Reference/Modules/learnloop/ops/startup|learnloop.ops.startup]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ingest_runner.py](../../../../../../tests/test_ingest_runner.py) — direct import
  - `test_openrouter_transcription_setting_routes_audio_via_chat`
- [tests/test_provider_resolution_parity.py](../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_composition_root_uses_fallback_and_preserves_requested_selection`
  - `test_config_matrix_executes_all_six_production_resolution_paths`
  - `test_explicit_and_environment_selections_suppress_fallback`
  - `test_manual_is_a_typed_no_client_outcome`
  - `test_operation_routes_include_semantic_diagnostic_grading`
  - `test_provider_resolution_config_matrix_is_uniform`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/routing.py](../../../../../../src/learnloop/ai/routing.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

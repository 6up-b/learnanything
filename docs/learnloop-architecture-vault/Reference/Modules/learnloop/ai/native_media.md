---
title: "learnloop.ai.native_media"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/native_media.py"
source_paths:
  - "src/learnloop/ai/native_media.py"
source_commit: "40a0c0e11541329274f4e4c0a1d053c2c56af620"
source_commit_timestamp: "2026-09-03T10:49:04-07:00"
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
  - "learnloop.ai.native_media module"
  - "src/learnloop/ai/native_media.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.native_media`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.native_media` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: Readiness of native media ingestion, per modality.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/native_media.py](../../../../../../src/learnloop/ai/native_media.py) |
| Source lines | 160 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `40a0c0e11541329274f4e4c0a1d053c2c56af620` |
| Commit timestamp | `2026-09-03T10:49:04-07:00` |

## Public API

- `class NativeModalityReadiness` ([source](../../../../../../src/learnloop/ai/native_media.py), line 39)
  - `as_dict(self) -> dict[str, Any]` (line 59; public)
- `native_requested(config: LearnLoopConfig, modality: str) -> bool` ([source](../../../../../../src/learnloop/ai/native_media.py), line 63) — Whether the vault config selects the native path for ``modality``.
- `native_max_mb(config: LearnLoopConfig, modality: str) -> int` ([source](../../../../../../src/learnloop/ai/native_media.py), line 73)
- `native_modality_readiness(config: LearnLoopConfig, modality: str, *, requested: bool | None=None) -> NativeModalityReadiness` ([source](../../../../../../src/learnloop/ai/native_media.py), line 77) — Resolve the routed provider for ``modality`` and judge it.

### Module constants

- `NATIVE_MODALITIES` ([src/learnloop/ai/native_media.py](../../../../../../src/learnloop/ai/native_media.py), line 28)
- `NATIVE_TASK` ([src/learnloop/ai/native_media.py](../../../../../../src/learnloop/ai/native_media.py), line 29)
- `NATIVE_PROVIDER_TYPES` ([src/learnloop/ai/native_media.py](../../../../../../src/learnloop/ai/native_media.py), line 30)
- `REASON_MANUAL_PROVIDER` ([src/learnloop/ai/native_media.py](../../../../../../src/learnloop/ai/native_media.py), line 32)
- `REASON_PROVIDER_MISSING` ([src/learnloop/ai/native_media.py](../../../../../../src/learnloop/ai/native_media.py), line 33)
- `REASON_PROVIDER_NOT_CHAT` ([src/learnloop/ai/native_media.py](../../../../../../src/learnloop/ai/native_media.py), line 34)
- `REASON_MODALITY_NOT_DECLARED` ([src/learnloop/ai/native_media.py](../../../../../../src/learnloop/ai/native_media.py), line 35)

### Explicit exports

`__all__` declares:

- `NATIVE_MODALITIES`
- `NATIVE_PROVIDER_TYPES`
- `NATIVE_TASK`
- `REASON_MANUAL_PROVIDER`
- `REASON_MODALITY_NOT_DECLARED`
- `REASON_PROVIDER_MISSING`
- `REASON_PROVIDER_NOT_CHAT`
- `NativeModalityReadiness`
- `native_max_mb`
- `native_modality_readiness`
- `native_requested`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/acquisition_preview|learnloop.content.pipeline.acquisition_preview]] — imports `native_modality_readiness`; statically calls `native_modality_readiness`
- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `native_modality_readiness`; statically calls `native_modality_readiness`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `native_modality_readiness`; statically calls `native_modality_readiness`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `NATIVE_MODALITIES`, `native_modality_readiness`; statically calls `native_modality_readiness`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `AITask`, `provider_for_task`; calls `provider_for_task`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `LearnLoopConfig`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/acquisition_preview|learnloop.content.pipeline.acquisition_preview]], [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]], [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_native_media_readiness.py](../../../../../../tests/test_native_media_readiness.py) — direct import
  - `test_as_dict_is_camel_safe_payload`
  - `test_environment_override_selects_the_provider_like_runtime`
  - `test_ready_when_route_is_a_chat_provider_declaring_the_modality`
  - `test_reasons_are_typed`
  - `test_requested_follows_each_modality_authority`
  - `test_unknown_modality_is_rejected`

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/native_media.py](../../../../../../src/learnloop/ai/native_media.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop_sidecar.handlers.ai_providers"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/ai_providers.py"
source_paths:
  - "src/learnloop_sidecar/handlers/ai_providers.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
aliases:
  - "learnloop_sidecar.handlers.ai_providers module"
  - "src/learnloop_sidecar/handlers/ai_providers.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.ai_providers`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps ai providers behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]]. Its public surface centers on `ready_grading_provider`, `ready_tutor_qa_provider`, `ready_teach_back_provider`, `ready_canonical_ingest_provider`, `runtime_for_provider`, `client_for_provider`, `grading_source_for_provider`, `provider_label` and 2 more public symbols.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/ai_providers.py](../../../../../../src/learnloop_sidecar/handlers/ai_providers.py) |
| Source lines | 128 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `ready_grading_provider(vault, override: str | None=None) -> tuple[str, Any, Any | None]` ([source](../../../../../../src/learnloop_sidecar/handlers/ai_providers.py), line 18) — Resolve the grading backend, honoring the runtime override.
- `ready_tutor_qa_provider(vault) -> tuple[str, Any, Any | None]` ([source](../../../../../../src/learnloop_sidecar/handlers/ai_providers.py), line 37) — Resolve the tutor Q&A backend via the ``tutor_qa`` routing entry.
- `ready_teach_back_provider(vault) -> tuple[str, Any, Any | None]` ([source](../../../../../../src/learnloop_sidecar/handlers/ai_providers.py), line 47) — Resolve the teach-back (naive student) backend via ``teach_back`` routing.
- `ready_canonical_ingest_provider(vault) -> tuple[str, Any, Any | None]` ([source](../../../../../../src/learnloop_sidecar/handlers/ai_providers.py), line 57) — Resolve the medium-effort canonical-ingest/synthesis route.
- `runtime_for_provider(vault, provider_name: str)` ([source](../../../../../../src/learnloop_sidecar/handlers/ai_providers.py), line 67)
- `client_for_provider(vault, provider_name: str)` ([source](../../../../../../src/learnloop_sidecar/handlers/ai_providers.py), line 71)
- `grading_source_for_provider(provider_name: str) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/ai_providers.py), line 78)
- `provider_label(provider_name: str) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/ai_providers.py), line 86)
- `class SetGradingProviderParams(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ai_providers.py), line 94)
- `set_grading_provider(ctx: SidecarContext, params: SetGradingProviderParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ai_providers.py), line 99) — Switch the AI grading backend at runtime (not persisted to learnloop.toml).

## Internal implementation anchors

- `_ready_routed_provider(vault, task: str) -> tuple[str, Any, Any | None]` ([source](../../../../../../src/learnloop_sidecar/handlers/ai_providers.py), line 63)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]] — imports `ready_grading_provider`; statically calls `ready_grading_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `ready_grading_provider`; statically calls `ready_grading_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `client_for_provider`, `grading_source_for_provider`, `provider_label`, `ready_grading_provider`; statically calls `client_for_provider`, `grading_source_for_provider`, `provider_label`, `ready_grading_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `ready_canonical_ingest_provider`; statically calls `ready_canonical_ingest_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `ready_grading_provider`; statically calls `ready_grading_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `provider_label`, `ready_canonical_ingest_provider`, `ready_tutor_qa_provider`; statically calls `provider_label`, `ready_canonical_ingest_provider`, `ready_tutor_qa_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `MANUAL_PROVIDER`, `provider_label`, `ready_grading_provider`, `ready_teach_back_provider`; statically calls `provider_label`, `ready_grading_provider`, `ready_teach_back_provider`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `provider_label`, `ready_tutor_qa_provider`; statically calls `provider_label`, `ready_tutor_qa_provider`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `MANUAL_PROVIDER`, `client_for_provider`, `ready_client_for_task`, `runtime_for_provider`; calls `client_for_provider`, `ready_client_for_task`, `runtime_for_provider`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `CODEX_PROVIDER_NAMES`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`, `available_grading_providers`; calls `available_grading_providers`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]], [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]], [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_provider_resolution_parity.py](../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_config_matrix_executes_all_six_production_resolution_paths`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/ai_providers.py](../../../../../../src/learnloop_sidecar/handlers/ai_providers.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

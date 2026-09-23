---
title: "learnloop_sidecar.handlers.animation"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/animation.py"
source_paths:
  - "src/learnloop_sidecar/handlers/animation.py"
source_commit: "e97d2e15256a04b74ec95b6da207772675f3f8f2"
source_commit_timestamp: "2026-09-03T10:31:35-07:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-09-23"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.animation module"
  - "src/learnloop_sidecar/handlers/animation.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.animation`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.animation` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Concept explainer-animation RPCs (spec_fork_features §2).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/animation.py](../../../../../../src/learnloop_sidecar/handlers/animation.py) |
| Source lines | 176 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e97d2e15256a04b74ec95b6da207772675f3f8f2` |
| Commit timestamp | `2026-09-03T10:31:35-07:00` |

## Public API

- `get_animation_runtime(ctx: SidecarContext, _params: EmptyParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/animation.py), line 71)
- `class RequestConceptAnimationInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/animation.py), line 106)
- `request_concept_animation(ctx: SidecarContext, params: RequestConceptAnimationInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/animation.py), line 113)
- `class ConceptAnimationStatusInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/animation.py), line 154)
- `get_concept_animation_status(ctx: SidecarContext, params: ConceptAnimationStatusInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/animation.py), line 159)
- `class ConceptAnimationsForConceptInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/animation.py), line 167)
- `list_concept_animations(ctx: SidecarContext, params: ConceptAnimationsForConceptInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/animation.py), line 173)

## Internal implementation anchors

- `_json_field(raw: Any, default: Any) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/animation.py), line 31)
- `_animation_row_payload(row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/animation.py), line 40)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `provider_for_task`; calls `provider_for_task`
- [[Reference/Modules/learnloop/content/authoring/concept_animation|learnloop.content.authoring.concept_animation]] — imports `ConceptAnimationError`, `manim_runtime`, `request_concept_animation`, `resolve_manim_command`, `video_generation_readiness`; calls `manim_runtime`, `request_concept_animation`, `resolve_manim_command`, `video_generation_readiness`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `EmptyParams`, `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_sidecar_animation.py](../../../../../../tests/test_sidecar_animation.py) — direct import
  - `test_animation_runtime_reports_probe_and_routed_model`
  - `test_request_generates_and_status_reports_completed`
  - `test_request_rejects_missing_consent_and_missing_manim`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/animation.py](../../../../../../src/learnloop_sidecar/handlers/animation.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

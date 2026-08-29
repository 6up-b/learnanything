---
title: "learnloop_sidecar.handlers.item_authoring"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/item_authoring.py"
source_paths:
  - "src/learnloop_sidecar/handlers/item_authoring.py"
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
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop_sidecar.handlers.item_authoring module"
  - "src/learnloop_sidecar/handlers/item_authoring.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.item_authoring`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.item_authoring` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Learner-owned practice-item authoring RPCs: author, edit, retire, split.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/item_authoring.py](../../../../../../src/learnloop_sidecar/handlers/item_authoring.py) |
| Source lines | 247 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class AuthorPracticeItemInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/item_authoring.py), line 28)
- `class EditPracticeItemInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/item_authoring.py), line 36)
- `class RetirePracticeItemInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/item_authoring.py), line 44)
- `class SplitPracticeItemPart(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/item_authoring.py), line 50)
- `class SplitPracticeItemInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/item_authoring.py), line 55)
- `class RequestRungVariantInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/item_authoring.py), line 61)
- `class RungVariantStatusInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/item_authoring.py), line 67)
- `class RemintDiagnosticProbeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/item_authoring.py), line 71)
- `request_rung_variant_rpc(ctx: SidecarContext, params: RequestRungVariantInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/item_authoring.py), line 97) — Learner-initiated re-runging: record the request + evidence package synchronously, then enqueue the variant authoring job (interactive band).
- `get_rung_variant_status(ctx: SidecarContext, params: RungVariantStatusInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/item_authoring.py), line 129)
- `remint_diagnostic_probe(ctx: SidecarContext, params: RemintDiagnosticProbeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/item_authoring.py), line 145) — Keep an administered diagnostic probe as an ordinary practice item.
- `author_practice_item(ctx: SidecarContext, params: AuthorPracticeItemInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/item_authoring.py), line 168)
- `edit_practice_item(ctx: SidecarContext, params: EditPracticeItemInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/item_authoring.py), line 187)
- `retire_practice_item(ctx: SidecarContext, params: RetirePracticeItemInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/item_authoring.py), line 206)
- `split_practice_item(ctx: SidecarContext, params: SplitPracticeItemInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/item_authoring.py), line 234)

## Internal implementation anchors

- `_root(ctx: SidecarContext)` ([source](../../../../../../src/learnloop_sidecar/handlers/item_authoring.py), line 75)
- `_variant_request_payload(row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/item_authoring.py), line 80)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] — imports `ItemAuthoringError`, `author_item`, `edit_item`, `retire_item`, `split_item`; calls `author_item`, `edit_item`, `retire_item`, `split_item`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `RungVariantError`, `request_rung_variant`; calls `request_rung_variant`
- [[Reference/Modules/learnloop/diagnosis/probe_remint|learnloop.diagnosis.probe_remint]] — imports `ProbeRemintError`, `remint_probe_as_practice_item`; calls `remint_probe_as_practice_item`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_desktop_rpc_contract.py](../../../../../../tests/test_desktop_rpc_contract.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_goal_scope_material.py](../../../../../../tests/test_goal_scope_material.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_graph_editor_reads.py](../../../../../../tests/test_graph_editor_reads.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_adjudication.py](../../../../../../tests/test_sidecar_adjudication.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_exams.py](../../../../../../tests/test_sidecar_exams.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_goals.py](../../../../../../tests/test_sidecar_goals.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_item_presentation.py](../../../../../../tests/test_sidecar_item_presentation.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_measurement.py](../../../../../../tests/test_sidecar_measurement.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_sidecar_trace_and_clarification.py](../../../../../../tests/test_sidecar_trace_and_clarification.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/item_authoring.py](../../../../../../src/learnloop_sidecar/handlers/item_authoring.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

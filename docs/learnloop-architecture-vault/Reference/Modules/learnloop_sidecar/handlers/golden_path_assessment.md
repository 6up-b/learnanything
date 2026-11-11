---
title: "learnloop_sidecar.handlers.golden_path_assessment"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/golden_path_assessment.py"
source_paths:
  - "src/learnloop_sidecar/handlers/golden_path_assessment.py"
generated: true
generated_at: "2026-11-02"
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
  - "learnloop_sidecar.handlers.golden_path_assessment module"
  - "src/learnloop_sidecar/handlers/golden_path_assessment.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.golden_path_assessment`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.golden_path_assessment` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: P2 ASSESSMENT + RESTORATION + MILESTONE track -- sidecar RPC (spec_p2_narrow_golden_path §9; design B.8-B.10).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/golden_path_assessment.py](../../../../../../src/learnloop_sidecar/handlers/golden_path_assessment.py) |
| Source lines | 190 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class RunIdInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/golden_path_assessment.py), line 28)
- `assess_open(ctx: SidecarContext, params: RunIdInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/golden_path_assessment.py), line 33)
- `class AssessSubmitInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/golden_path_assessment.py), line 79)
- `assess_submit(ctx: SidecarContext, params: AssessSubmitInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/golden_path_assessment.py), line 94)
- `assess_result(ctx: SidecarContext, params: RunIdInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/golden_path_assessment.py), line 123)
- `restore(ctx: SidecarContext, params: RunIdInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/golden_path_assessment.py), line 132)
- `boundary_diff(ctx: SidecarContext, params: RunIdInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/golden_path_assessment.py), line 144)
- `depth_invitation(ctx: SidecarContext, params: RunIdInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/golden_path_assessment.py), line 155)
- `accept_edge(ctx: SidecarContext, params: RunIdInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/golden_path_assessment.py), line 168)
- `class DeclineInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/golden_path_assessment.py), line 179)
- `decline_edge(ctx: SidecarContext, params: DeclineInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/golden_path_assessment.py), line 185)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/curriculum/golden_path_assessment|learnloop.curriculum.golden_path_assessment]] — imports `module`; calls `assessment_result`, `open_assessment`, `submit_assessment`
- [[Reference/Modules/learnloop/curriculum/golden_path_restoration|learnloop.curriculum.golden_path_restoration]] — imports `module`; calls `accept_depth_invitation`, `decline_depth_invitation`, `restore`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `item_presentation`; calls `item_presentation`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`
- [[Reference/Modules/learnloop_sidecar/serving|learnloop_sidecar.serving]] — imports `refuse_unservable_item`; calls `refuse_unservable_item`

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

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/facet_reword_paths_helpers.py](../../../../../../tests/facet_reword_paths_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/graph_editor_reads_helpers.py](../../../../../../tests/graph_editor_reads_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/plan_first_transport_offer_grants_helpers.py](../../../../../../tests/plan_first_transport_offer_grants_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/reader_workbench_rw2a_helpers.py](../../../../../../tests/reader_workbench_rw2a_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/reading_path_fixtures.py](../../../../../../tests/reading_path_fixtures.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/recap_fixtures.py](../../../../../../tests/recap_fixtures.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/router_offer_log_helpers.py](../../../../../../tests/router_offer_log_helpers.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/rw2b_fix10_base_sequence.py](../../../../../../tests/rw2b_fix10_base_sequence.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/rw2b_fix11_base_sequence.py](../../../../../../tests/rw2b_fix11_base_sequence.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/rw2c_base_sequence.py](../../../../../../tests/rw2c_base_sequence.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/rw2c_state_parity.py](../../../../../../tests/rw2c_state_parity.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad1_attempt_columns.py](../../../../../../tests/test_ad1_attempt_columns.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/golden_path_assessment.py](../../../../../../src/learnloop_sidecar/handlers/golden_path_assessment.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

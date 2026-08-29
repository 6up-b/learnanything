---
title: "learnloop_sidecar.handlers.graph"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/graph.py"
source_paths:
  - "src/learnloop_sidecar/handlers/graph.py"
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
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.graph module"
  - "src/learnloop_sidecar/handlers/graph.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.graph`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps graph behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]]. Its public surface centers on `get_concept_graph`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/graph.py](../../../../../../src/learnloop_sidecar/handlers/graph.py) |
| Source lines | 86 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `get_concept_graph(ctx: SidecarContext, _params) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/graph.py), line 12) — Concept graph for the Graph screen: concepts + edges + per-concept rollups.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `display_mastery`; calls `display_mastery`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
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

1. Modify [src/learnloop_sidecar/handlers/graph.py](../../../../../../src/learnloop_sidecar/handlers/graph.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

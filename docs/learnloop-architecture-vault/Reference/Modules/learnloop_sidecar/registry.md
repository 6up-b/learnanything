---
title: "learnloop_sidecar.registry"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/registry.py"
source_paths:
  - "src/learnloop_sidecar/registry.py"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop_sidecar"
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
  - "learnloop_sidecar.registry module"
  - "src/learnloop_sidecar/registry.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar"
---

# `learnloop_sidecar.registry`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps registry behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]]. Its public surface centers on `MethodSpec`, `method`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/registry.py](../../../../../src/learnloop_sidecar/registry.py) |
| Source lines | 36 |
| Owning package | [[Reference/Modules/learnloop_sidecar/_package|learnloop_sidecar]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class MethodSpec` ([source](../../../../../src/learnloop_sidecar/registry.py), line 14)
- `method(name: str, params_model: type[ParamsModel]=EmptyParams) -> Callable[[Handler], Handler]` ([source](../../../../../src/learnloop_sidecar/registry.py), line 23)

### Module constants

- `METHOD_REGISTRY` ([src/learnloop_sidecar/registry.py](../../../../../src/learnloop_sidecar/registry.py), line 20)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/app|learnloop_sidecar.handlers.app]] — imports `METHOD_REGISTRY`, `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/claims|learnloop_sidecar.handlers.claims]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/cli|learnloop_sidecar.handlers.cli]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/diagnostic|learnloop_sidecar.handlers.diagnostic]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/facets|learnloop_sidecar.handlers.facets]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path|learnloop_sidecar.handlers.golden_path]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path_assessment|learnloop_sidecar.handlers.golden_path_assessment]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/graph|learnloop_sidecar.handlers.graph]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/graph_edit|learnloop_sidecar.handlers.graph_edit]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/inspector|learnloop_sidecar.handlers.inspector]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_model|learnloop_sidecar.handlers.knowledge_model]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/ladder|learnloop_sidecar.handlers.ladder]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/library|learnloop_sidecar.handlers.library]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/proposals|learnloop_sidecar.handlers.proposals]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/provenance|learnloop_sidecar.handlers.provenance]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/registry|learnloop_sidecar.handlers.registry]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/review|learnloop_sidecar.handlers.review]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/sqlite_admin|learnloop_sidecar.handlers.sqlite_admin]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/handlers/vault|learnloop_sidecar.handlers.vault]] — imports `method`; statically calls `method`
- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `METHOD_REGISTRY`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `EmptyParams`, `ParamsModel`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]], [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]], [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]], [[Reference/Modules/learnloop_sidecar/handlers/app|learnloop_sidecar.handlers.app]], [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]] and 35 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../tests/test_causal_repair_sidecar_rpcs.py) — direct import
  - `test_causal_repair_methods_are_registered_and_accept_the_client_payloads`
- [tests/test_desktop_rpc_contract.py](../../../../../tests/test_desktop_rpc_contract.py) — direct import
  - `test_every_decorated_handler_is_loaded_once`
- [tests/test_dialogue_causal_join.py](../../../../../tests/test_dialogue_causal_join.py) — direct import
- [tests/test_goal_scope_material.py](../../../../../tests/test_goal_scope_material.py) — direct import
- [tests/test_graph_editor_reads.py](../../../../../tests/test_graph_editor_reads.py) — direct import
- [tests/test_instrument_servability_journeys.py](../../../../../tests/test_instrument_servability_journeys.py) — direct import
- [tests/test_sidecar_adjudication.py](../../../../../tests/test_sidecar_adjudication.py) — direct import
- [tests/test_sidecar_exams.py](../../../../../tests/test_sidecar_exams.py) — direct import
- [tests/test_sidecar_goals.py](../../../../../tests/test_sidecar_goals.py) — direct import
- [tests/test_sidecar_item_presentation.py](../../../../../tests/test_sidecar_item_presentation.py) — direct import
- [tests/test_sidecar_measurement.py](../../../../../tests/test_sidecar_measurement.py) — direct import
- [tests/test_sidecar_trace_and_clarification.py](../../../../../tests/test_sidecar_trace_and_clarification.py) — direct import
- [tests/test_sidecar_transport.py](../../../../../tests/test_sidecar_transport.py) — direct import
  - `test_duplicate_method_registration_fails_loudly`
  - `test_unexpected_handler_failure_marks_the_commit_outcome_unknown`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/registry.py](../../../../../src/learnloop_sidecar/registry.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

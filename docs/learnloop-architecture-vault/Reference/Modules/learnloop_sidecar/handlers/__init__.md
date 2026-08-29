---
title: "learnloop_sidecar.handlers"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/__init__.py"
source_paths:
  - "src/learnloop_sidecar/handlers/__init__.py"
source_commit: "971d7c274e09873d726d43578cd080e4d8865571"
source_commit_timestamp: "2026-07-27T06:01:19-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-08-18"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
aliases:
  - "learnloop_sidecar.handlers module"
  - "src/learnloop_sidecar/handlers/__init__.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module establishes the Python package boundary for [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]].

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/__init__.py](../../../../../../src/learnloop_sidecar/handlers/__init__.py) |
| Source lines | 43 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `971d7c274e09873d726d43578cd080e4d8865571` |
| Commit timestamp | `2026-07-27T06:01:19-04:00` |

## Public API

No public top-level function or class definition is declared in this file.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop_sidecar/handlers/adjudication|learnloop_sidecar.handlers.adjudication]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/ai_providers|learnloop_sidecar.handlers.ai_providers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/animation|learnloop_sidecar.handlers.animation]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/app|learnloop_sidecar.handlers.app]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/calibration|learnloop_sidecar.handlers.calibration]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/claims|learnloop_sidecar.handlers.claims]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/cli|learnloop_sidecar.handlers.cli]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/diagnostic|learnloop_sidecar.handlers.diagnostic]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/facets|learnloop_sidecar.handlers.facets]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path|learnloop_sidecar.handlers.golden_path]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/golden_path_assessment|learnloop_sidecar.handlers.golden_path_assessment]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/graph|learnloop_sidecar.handlers.graph]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/graph_edit|learnloop_sidecar.handlers.graph_edit]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/inspector|learnloop_sidecar.handlers.inspector]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/item_authoring|learnloop_sidecar.handlers.item_authoring]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_model|learnloop_sidecar.handlers.knowledge_model]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/ladder|learnloop_sidecar.handlers.ladder]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/library|learnloop_sidecar.handlers.library]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/proposals|learnloop_sidecar.handlers.proposals]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/provenance|learnloop_sidecar.handlers.provenance]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/registry|learnloop_sidecar.handlers.registry]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/remediation|learnloop_sidecar.handlers.remediation]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/review|learnloop_sidecar.handlers.review]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/settings|learnloop_sidecar.handlers.settings]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/sqlite_admin|learnloop_sidecar.handlers.sqlite_admin]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/teach_back|learnloop_sidecar.handlers.teach_back]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/tutor_qa|learnloop_sidecar.handlers.tutor_qa]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/vault|learnloop_sidecar.handlers.vault]] — imports `module`

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/server|learnloop_sidecar.server]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_desktop_rpc_contract.py](../../../../../../tests/test_desktop_rpc_contract.py) — direct import
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — direct import
- [tests/test_goal_scope_material.py](../../../../../../tests/test_goal_scope_material.py) — direct import
- [tests/test_graph_editor_reads.py](../../../../../../tests/test_graph_editor_reads.py) — direct import
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
- [tests/test_sidecar_adjudication.py](../../../../../../tests/test_sidecar_adjudication.py) — direct import
- [tests/test_sidecar_exams.py](../../../../../../tests/test_sidecar_exams.py) — direct import
- [tests/test_sidecar_goals.py](../../../../../../tests/test_sidecar_goals.py) — direct import
- [tests/test_sidecar_item_presentation.py](../../../../../../tests/test_sidecar_item_presentation.py) — direct import
- [tests/test_sidecar_measurement.py](../../../../../../tests/test_sidecar_measurement.py) — direct import
- [tests/test_sidecar_trace_and_clarification.py](../../../../../../tests/test_sidecar_trace_and_clarification.py) — direct import

## Modification guidance

- Change this file when intentionally adding or removing a package-level re-export; keep implementation logic in the owning module.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/__init__.py](../../../../../../src/learnloop_sidecar/handlers/__init__.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

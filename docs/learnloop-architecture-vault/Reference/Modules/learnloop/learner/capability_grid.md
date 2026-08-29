---
title: "learnloop.learner.capability_grid"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/capability_grid.py"
source_paths:
  - "src/learnloop/learner/capability_grid.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Inspect Persistent State"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner.capability_grid module"
  - "src/learnloop/learner/capability_grid.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.capability_grid`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.capability_grid` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Capability grid — facet × capability heatmap for an LO neighborhood (KM §9.6).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/capability_grid.py](../../../../../../src/learnloop/learner/capability_grid.py) |
| Source lines | 228 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class GridCell` ([source](../../../../../../src/learnloop/learner/capability_grid.py), line 45)
  - `as_dict(self) -> dict[str, object]` (line 61; public)
- `class CapabilityGrid` ([source](../../../../../../src/learnloop/learner/capability_grid.py), line 81)
  - `as_dict(self) -> dict[str, object]` (line 88; public)
- `capability_grid(vault: LoadedVault, repository: Repository, learning_object_id: str) -> CapabilityGrid` ([source](../../../../../../src/learnloop/learner/capability_grid.py), line 106) — Facet × capability grid for one LO (canonical facet keys).
- `lo_blueprint_readiness(vault: LoadedVault, repository: Repository, learning_object_id: str) -> LoReadiness | None` ([source](../../../../../../src/learnloop/learner/capability_grid.py), line 206) — Per-LO blueprint recipe readiness (§9.2) for the recipe-tree surface.

## Internal implementation anchors

- `_lo_required_facets(vault: LoadedVault, repository: Repository, learning_object) -> list[str]` ([source](../../../../../../src/learnloop/learner/capability_grid.py), line 98)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]] — imports `lo_blueprint_readiness`; statically calls `lo_blueprint_readiness`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `lo_blueprint_readiness`; statically calls `lo_blueprint_readiness`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_model|learnloop_sidecar.handlers.knowledge_model]] — imports `capability_grid`, `lo_blueprint_readiness`; statically calls `capability_grid`, `lo_blueprint_readiness`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/goals/certification|learnloop.goals.certification]] — imports `is_demonstrated_credit`; calls `is_demonstrated_credit`
- [[Reference/Modules/learnloop/goals/goal_certification|learnloop.goals.goal_certification]] — imports `required_capabilities_for_facet`; calls `required_capabilities_for_facet`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `project_lo_blueprint_readiness`; calls `project_lo_blueprint_readiness`
- [[Reference/Modules/learnloop/learner/blueprint_projection|learnloop.learner.blueprint_projection]] — imports `LoReadiness`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `required_facets`; calls `required_facets`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `facet_recall_states_for_lo`, `is_canonical_state_vault`; calls `facet_recall_states_for_lo`, `is_canonical_state_vault`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `covering_learner_claim`; calls `covering_learner_claim`
- [[Reference/Modules/learnloop/learner/measurement_state|learnloop.learner.measurement_state]] — imports `classify_measurement_state`, `require_measurement_state`; calls `classify_measurement_state`, `require_measurement_state`
- [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]] — imports `predicted_facet_recall`; calls `predicted_facet_recall`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/facet_detail|learnloop_sidecar.handlers.facet_detail]], [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]], [[Reference/Modules/learnloop_sidecar/handlers/knowledge_model|learnloop_sidecar.handlers.knowledge_model]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_measurement_state_labels.py](../../../../../../tests/test_measurement_state_labels.py) — direct import
  - `test_capability_grid_labels_the_ready_number`
  - `test_emission_boundary_rejects_a_label_outside_the_vocabulary`
  - `test_labelling_writes_nothing`

## Modification guidance

- Change capability grid policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/capability_grid.py](../../../../../../src/learnloop/learner/capability_grid.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

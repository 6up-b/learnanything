---
title: "learnloop_sidecar.handlers.facet_detail"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/facet_detail.py"
source_paths:
  - "src/learnloop_sidecar/handlers/facet_detail.py"
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
  - "learnloop_sidecar.handlers.facet_detail module"
  - "src/learnloop_sidecar/handlers/facet_detail.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.facet_detail`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.facet_detail` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Graph/knowledge-map editor read RPCs (§3.4 locks, §8 graphs, §9.6 UI).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/facet_detail.py](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py) |
| Source lines | 345 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class FacetIdInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 43)
- `get_facet_detail(ctx: SidecarContext, params: FacetIdInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 48) — Facet contract + lock reasons + blueprint membership + evidence (§9.6).
- `list_facets(ctx: SidecarContext, _params) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 146) — Lightweight facet list for autocomplete pickers, sorted by id.
- `class PreviewBlueprintReadinessParams(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 168)
- `preview_blueprint_readiness(ctx: SidecarContext, params: PreviewBlueprintReadinessParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 176) — Current-vs-proposed LO readiness for an edited blueprint payload (§9.2).

## Internal implementation anchors

- `_components_with_role(recipe)` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 226) — (role, component) for every component of a recipe, integration included.
- `_facet_evidence(vault, repository, facet_id: str, item_los: list[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 237) — Capability ledger + facet-global readiness/evidence-mass for a facet.
- `_facet_readiness(vault, repository, facet_id: str, item_los: list[str]) -> tuple[float | None, float | None]` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 262) — Facet-global predicted recall, averaged over LOs exercising the facet.
- `_readiness_summary(readiness) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 307) — The ``{readiness, bottleneck}`` pair the blast-radius panel renders.
- `_identifiability_warnings(vault, learning_object) -> list[str]` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 318) — Identifiability findings that touch this LO's facet neighborhood (§11.3).
- `_affected_goals(vault, repository, learning_object_id: str) -> list[dict[str, str]]` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 336) — Active goals whose resolved scope includes this LO (or its facets).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/curriculum/curriculum_locks|learnloop.curriculum.curriculum_locks]] — imports `Operation`, `can_apply`, `identity_locks`; calls `Operation`, `can_apply`, `identity_locks`
- [[Reference/Modules/learnloop/goals/certification|learnloop.goals.certification]] — imports `is_demonstrated_credit`; calls `is_demonstrated_credit`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `resolve_goal_scope`; calls `resolve_goal_scope`
- [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]] — imports `lo_blueprint_readiness`; calls `lo_blueprint_readiness`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `CanonicalFacetStateReader`, `facet_recall_states_for_lo`, `is_canonical_state_vault`, `resolve_canonical_facet`; calls `CanonicalFacetStateReader`, `facet_recall_states_for_lo`, `is_canonical_state_vault`, `resolve_canonical_facet`
- [[Reference/Modules/learnloop/learner/identifiability|learnloop.learner.identifiability]] — imports `analyze_identifiability`, `build_registry_view`; calls `analyze_identifiability`, `build_registry_view`
- [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]] — imports `predicted_facet_recall`; calls `predicted_facet_recall`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LearningObject`, `recipe_components`; calls `recipe_components`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: `pydantic`

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

1. Modify [src/learnloop_sidecar/handlers/facet_detail.py](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

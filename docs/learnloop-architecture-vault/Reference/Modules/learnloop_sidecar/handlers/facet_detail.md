---
title: "learnloop_sidecar.handlers.facet_detail"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/facet_detail.py"
source_paths:
  - "src/learnloop_sidecar/handlers/facet_detail.py"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.facet_detail` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Graph/knowledge-map editor read RPCs (§3.4 facet history, §8 graphs, §9.6 UI).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/facet_detail.py](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py) |
| Source lines | 328 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class FacetIdInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 44)
- `get_facet_detail(ctx: SidecarContext, params: FacetIdInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 49) — Facet contract + history + blueprint membership + evidence (§9.6).
- `list_facets(ctx: SidecarContext, _params) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 139) — Lightweight facet list for autocomplete pickers, sorted by id.
- `class PreviewBlueprintReadinessParams(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 155)
- `preview_blueprint_readiness(ctx: SidecarContext, params: PreviewBlueprintReadinessParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 163) — Current-vs-proposed LO readiness for an edited blueprint payload (§9.2).

## Internal implementation anchors

- `_components_with_role(recipe)` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 213) — (role, component) for every component of a recipe, integration included.
- `_facet_evidence(vault, repository, facet_id: str, item_los: list[str]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 224) — Capability ledger + facet-global readiness/evidence-mass for a facet.
- `_facet_readiness(vault, repository, facet_id: str, item_los: list[str]) -> tuple[float | None, float | None]` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 249) — Facet-global predicted recall, averaged over LOs exercising the facet.
- `_readiness_summary(readiness) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 290) — The ``{readiness, bottleneck}`` pair the blast-radius panel renders.
- `_identifiability_warnings(vault, learning_object) -> list[str]` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 301) — Identifiability findings that touch this LO's facet neighborhood (§11.3).
- `_affected_goals(vault, repository, learning_object_id: str) -> list[dict[str, str]]` ([source](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py), line 319) — Active goals whose resolved scope includes this LO (or its facets).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/facet_identity/actions|learnloop.content.facet_identity.actions]] — imports `facet_history`; calls `facet_history`
- [[Reference/Modules/learnloop/goals/certification|learnloop.goals.certification]] — imports `is_demonstrated_credit`; calls `is_demonstrated_credit`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `resolve_goal_scope`; calls `resolve_goal_scope`
- [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]] — imports `lo_blueprint_readiness`; calls `lo_blueprint_readiness`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `CanonicalFacetStateReader`, `facet_recall_states_for_lo`, `resolve_canonical_facet`; calls `CanonicalFacetStateReader`, `facet_recall_states_for_lo`, `resolve_canonical_facet`
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

1. Modify [src/learnloop_sidecar/handlers/facet_detail.py](../../../../../../src/learnloop_sidecar/handlers/facet_detail.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

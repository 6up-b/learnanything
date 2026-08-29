---
title: "learnloop_sidecar.handlers.knowledge_map"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/knowledge_map.py"
source_paths:
  - "src/learnloop_sidecar/handlers/knowledge_map.py"
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
  - "learnloop_sidecar.handlers.knowledge_map module"
  - "src/learnloop_sidecar/handlers/knowledge_map.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.knowledge_map`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps knowledge map behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]]. Its public surface centers on `get_knowledge_map`, `get_knowledge_map_history`, `PreviewEdge`, `PreviewKnowledgeMapParams`, `preview_knowledge_map`.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/knowledge_map.py](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py) |
| Source lines | 960 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `get_knowledge_map(ctx: SidecarContext, _params) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 47) — Deterministic 2D embedding of every practice item (the knowledge map).
- `get_knowledge_map_history(ctx: SidecarContext, _params) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 163) — Attempt events + reconstructed mastery trajectories for the chronicle.
- `class PreviewEdge(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 726)
- `class PreviewKnowledgeMapParams(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 732)
- `preview_knowledge_map(ctx: SidecarContext, params: PreviewKnowledgeMapParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 738) — Item-map MDS against a hypothetical semantic edge set (§8 layer honesty).

### Module constants

- `_FACET_BLEND` ([src/learnloop_sidecar/handlers/knowledge_map.py](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 29)
- `_GRAPH_BLEND` ([src/learnloop_sidecar/handlers/knowledge_map.py](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 30)
- `_GRAPH_RELATIONS` ([src/learnloop_sidecar/handlers/knowledge_map.py](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 36)
- `_TOP_FACETS` ([src/learnloop_sidecar/handlers/knowledge_map.py](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 38)
- `_TITLE_MAX` ([src/learnloop_sidecar/handlers/knowledge_map.py](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 39)
- `_NEIGHBOR_COUNT` ([src/learnloop_sidecar/handlers/knowledge_map.py](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 43)

## Internal implementation anchors

- `_facet_field(vault, repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 223) — Facet topology + dual evidence/prediction axes for the gravity field.
- `_cold_check_pending_learning_objects(vault, repository) -> set[str]` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 451) — Learning objects carrying a live, unspent repair cold check.
- `_facet_current_retentions(vault, repository) -> dict[str, float]` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 479) — Evidence-weighted present-day FSRS retention by facet item family.
- `_weighted_adjacency(nodes, edge_weights) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 518)
- `_shortest_paths(start: str, adjacency) -> tuple[dict[str, float], dict[str, str]]` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 528)
- `_facet_graph_distances(facets: list[str], adjacency) -> list[list[float]]` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 545)
- `_next_gap(vault, repository, points, adjacency) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 560) — One model-selected gap pin, routed to its native drill-down.
- `_diagnostic_target(repository, attempt_id: str) -> tuple[str, str]` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 651) — Route ambiguity to its probe episode when one owns the observation.
- `_item_title(prompt: str) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 664)
- `_facet_vector(item) -> dict[str, float]` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 671) — L2-normalized facet weights (missing declared weights default to 1.0).
- `_cosine_distance(u: dict[str, float], v: dict[str, float]) -> float` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 687)
- `_vault_edge_tuples(vault) -> list[tuple[str, str, str]]` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 694) — The loaded vault's semantic edges as ``(source, target, relation_type)``.
- `_item_map_geometry(vault, edges: list[tuple[str, str, str]]) -> tuple[list, dict[str, str | None], list[list[float]], list[tuple[float, float]], float]` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 700) — Pure item-map geometry against an explicit semantic edge set.
- `_concept_geodesics(edges: list[tuple[str, str, str]], concepts: set[str]) -> dict[tuple[str, str], int | None]` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 788) — BFS hop counts between concepts over undirected structural edges.
- `_blended_distances(items: list, vectors: list[dict[str, float]], concept_of: dict[str, str | None], hops: dict[tuple[str, str], int | None]) -> list[list[float]]` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 819)
- `_classical_mds(distances: list[list[float]]) -> tuple[list[tuple[float, float]], float]` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 852) — Cached exact MDS keyed by the deterministic distance matrix.
- `_classical_mds_cached(distances: tuple[tuple[float, ...], ...]) -> tuple[tuple[tuple[float, float], ...], float]` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 863) — Torgerson classical MDS to 2D, plus Kruskal stress-1.
- `_jacobi_eigh(matrix: list[list[float]]) -> tuple[list[float], list[list[float]]]` ([source](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py), line 923) — Cyclic Jacobi eigendecomposition for a small symmetric matrix.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/curriculum/curriculum_locks|learnloop.curriculum.curriculum_locks]] — imports `identity_locks`; calls `identity_locks`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `resolve_item_irt`; calls `resolve_item_irt`
- [[Reference/Modules/learnloop/goals/certification|learnloop.goals.certification]] — imports `is_demonstrated_credit`; calls `is_demonstrated_credit`
- [[Reference/Modules/learnloop/goals/goal_certification|learnloop.goals.goal_certification]] — imports `lo_certification`; calls `lo_certification`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `resolve_goal_scope`; calls `resolve_goal_scope`
- [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]] — imports `lo_blueprint_readiness`; calls `lo_blueprint_readiness`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `CAPABILITY_VOCABULARY`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `facet_evidence_timelines`; calls `facet_evidence_timelines`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `display_mastery`, `sigmoid`; calls `display_mastery`, `sigmoid`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `predicted_correctness`; calls `predicted_correctness`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_fsrs_weights`; calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `forgetting_curve`; calls `forgetting_curve`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `build_due_queue`; calls `build_due_queue`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `functools`, `hashlib`, `heapq`, `json`, `math`, `typing`
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

- [tests/test_graph_editor_reads.py](../../../../../../tests/test_graph_editor_reads.py) — direct import
  - `test_classical_mds_reuses_exact_cached_layout`
- [tests/test_sidecar_remediation_surfaces.py](../../../../../../tests/test_sidecar_remediation_surfaces.py) — direct import
  - `test_cold_check_pending_learning_objects_clear_once_the_check_is_answered`
  - `test_facet_points_carry_cold_check_pending_without_touching_demonstrated`

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/knowledge_map.py](../../../../../../src/learnloop_sidecar/handlers/knowledge_map.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

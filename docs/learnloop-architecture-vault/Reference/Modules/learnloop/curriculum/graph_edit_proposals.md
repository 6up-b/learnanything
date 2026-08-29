---
title: "learnloop.curriculum.graph_edit_proposals"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/graph_edit_proposals.py"
source_paths:
  - "src/learnloop/curriculum/graph_edit_proposals.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.curriculum"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.curriculum.graph_edit_proposals module"
  - "src/learnloop/curriculum/graph_edit_proposals.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.graph_edit_proposals`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.graph_edit_proposals` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: User-authored graph/knowledge-map edits (graph editor, spec §8/§12).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/graph_edit_proposals.py](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py) |
| Source lines | 684 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class GraphEditError(ValueError)` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 56) — A user graph-edit request that cannot be compiled (maps to a SidecarError).
  - `__init__(self, code: str, message: str) -> None` (line 59; internal)
- `propose_graph_edits(root: Path, rationale: str, edits: list[dict[str, Any]], *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 67) — Compile a batch of user graph edits into ONE pending proposal batch.
- `queue_restructure_request(root: Path, facet_ids: list[str], requested_operation: str, rationale: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 297) — Queue a durable restructure-intent record for LOCKED facets (spec §17).
- `resolve_edge_direction(root: Path, edge_id: str, resolution: str, rationale: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 379) — Resolve an ``ambiguous_edge_direction`` notice into a concept_edge edit.
- `ambiguous_edge_direction_notices(vault: LoadedVault, repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 466) — Deterministic ambiguous-direction notices (design "Write path" heuristics).
- `restructure_request_notices(vault: LoadedVault, repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 655) — Surface queued restructure-intent records in the maintenance feed (§17).

### Module constants

- `_GRAPH_EDIT_ITEM_TYPES` ([src/learnloop/curriculum/graph_edit_proposals.py](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 39)
- `_AUTHORING_ITEM_TYPES` ([src/learnloop/curriculum/graph_edit_proposals.py](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 40)
- `_EDIT_OPERATIONS` ([src/learnloop/curriculum/graph_edit_proposals.py](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 41)
- `_OPERATION_MAP` ([src/learnloop/curriculum/graph_edit_proposals.py](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 44)
- `_GRAPH_EDITOR_PURPOSE` ([src/learnloop/curriculum/graph_edit_proposals.py](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 46)
- `_GRAPH_EDITOR_PROVIDER` ([src/learnloop/curriculum/graph_edit_proposals.py](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 47)
- `_EDGE_RESOLUTIONS` ([src/learnloop/curriculum/graph_edit_proposals.py](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 49)
- `AMBIGUOUS_EDGE_DIRECTION_NOTICE` ([src/learnloop/curriculum/graph_edit_proposals.py](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 51)
- `RESTRUCTURE_REQUEST_NOTICE` ([src/learnloop/curriculum/graph_edit_proposals.py](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 52)
- `RESTRUCTURE_REQUEST_NEED_KIND` ([src/learnloop/curriculum/graph_edit_proposals.py](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 53)

## Internal implementation anchors

- `_persist_graph_edit_batch(root: Path, vault: LoadedVault, repository: Repository, rationale: str, edits: list[dict[str, Any]], *, clock: Clock | None) -> tuple[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 94)
- `_authoring_item(edit: dict[str, Any], index: int, vault: LoadedVault) -> AuthoringProposalItem` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 170)
- `_snapshot_edge_for_deactivate(payload: dict[str, Any], target_entity_id: Any, vault: LoadedVault) -> None` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 211) — Fill a concept_edge deactivate payload from the live edge.
- `_raw_row(edit: dict[str, Any], index: int, now: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 233) — A directly-built proposal row for a learnable-map type with no authoring payload model (``task_blueprint``) — persisted the way synthesis persists it.
- `_stamp_expected_target_hash(row: dict[str, Any], vault: LoadedVault) -> None` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 260) — Stamp the §8.2 accept-time staleness hash on update/deactivate rows.
- `_item_dto(row: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 281)
- `_subject_for_facets(vault: LoadedVault, facet_ids: list[str]) -> str` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 366)
- `_edge_resolution_edit(edge: Any, resolution: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 423)
- `_resolve_edge_direction_notices(repository: Repository, edge_id: str, *, clock: Clock | None) -> list[str]` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 447)
- `_edge_notice(vault: LoadedVault, repository: Repository, *, dedup_key: str, entity_id: str | None, edge_id: str | None, source: str, target: str, relation_type: str, rationale: str | None, reason: str, proposal_item_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 530)
- `_direction_evidence(vault: LoadedVault, repository: Repository, source_concept: str, target_concept: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 572) — Success on the target's items before vs after the first correct attempt on any source item.
- `_items_for_concept(vault: LoadedVault, concept_id: str) -> list[str]` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 604)
- `_is_correct(outcome: dict[str, Any]) -> bool` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 613)
- `_concept_title(vault: LoadedVault, concept_id: str) -> str` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 621)
- `_reachable(adjacency: dict[str, set[str]], start: str, goal: str) -> bool` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 626)
- `_pending_prerequisite_edge_items(repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py), line 640)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ops/maintenance_feed|learnloop.ops.maintenance_feed]] — imports `ambiguous_edge_direction_notices`, `restructure_request_notices`; statically calls `ambiguous_edge_direction_notices`, `restructure_request_notices`
- [[Reference/Modules/learnloop_sidecar/handlers/graph_edit|learnloop_sidecar.handlers.graph_edit]] — imports `GraphEditError`, `propose_graph_edits`, `queue_restructure_request`, `resolve_edge_direction`; statically calls `propose_graph_edits`, `queue_restructure_request`, `resolve_edge_direction`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]] — imports `AuthoringProposal`, `AuthoringProposalItem`; calls `AuthoringProposal`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `compute_target_hash`; calls `compute_target_hash`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `auto_apply_rows`, `proposal_item_row`; calls `auto_apply_rows`, `proposal_item_row`
- [[Reference/Modules/learnloop/curriculum/curriculum_locks|learnloop.curriculum.curriculum_locks]] — imports `Operation`, `can_apply`; calls `Operation`, `can_apply`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`; calls `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/ops/maintenance_feed|learnloop.ops.maintenance_feed]], [[Reference/Modules/learnloop_sidecar/handlers/graph_edit|learnloop_sidecar.handlers.graph_edit]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_graph_edit_proposals.py](../../../../../../tests/test_graph_edit_proposals.py) — direct import
  - `test_accept_concept_edge_deactivate_removes_edge`
  - `test_concept_edge_deactivate_snapshots_edge_into_payload`
  - `test_propose_graph_edits_creates_one_user_batch`
  - `test_propose_graph_edits_rejects_concept_delete_at_filing`
  - `test_propose_graph_edits_rejects_unknown_item_type`
  - `test_propose_graph_edits_requires_rationale_and_edits`
  - `test_propose_graph_edits_task_blueprint_raw_row`
  - `test_propose_graph_edits_update_stamps_target_hash`
  - `test_queue_restructure_request_records_and_surfaces_in_feed`
  - `test_queue_restructure_request_rejects_bad_operation`
  - `test_queue_restructure_request_requires_a_locked_facet`
  - `test_reject_after_apply_restores_concept_edge`
  - `test_resolve_edge_direction_flip_files_proposal_and_resolves_notice`
  - `test_resolve_edge_direction_keep_resolves_without_filing`
  - `test_resolve_edge_direction_retire_removes_and_can_restore`
  - `test_resolve_edge_direction_unknown_edge_errors`

## Modification guidance

- Change graph edit proposals policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/graph_edit_proposals.py](../../../../../../src/learnloop/curriculum/graph_edit_proposals.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

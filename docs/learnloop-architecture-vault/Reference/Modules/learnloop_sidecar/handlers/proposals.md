---
title: "learnloop_sidecar.handlers.proposals"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/proposals.py"
source_paths:
  - "src/learnloop_sidecar/handlers/proposals.py"
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
  - "learnloop_sidecar.handlers.proposals module"
  - "src/learnloop_sidecar/handlers/proposals.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.proposals`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps proposals behavior inside its owning package, [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]]. Its public surface centers on `get_proposals`, `ProposalDecisionInput`, `accept_proposal_items`, `reject_proposal_items`, `reset_proposal_items`, `EditProposalItemInput`, `edit_proposal_item`, `RefreshProposalItemValidationInput` and 3 more public symbols.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/proposals.py](../../../../../../src/learnloop_sidecar/handlers/proposals.py) |
| Source lines | 318 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `get_proposals(ctx: SidecarContext, _params) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/proposals.py), line 190) — Codex authoring inbox: proposal batches + items + agent-run lineage.
- `class ProposalDecisionInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/proposals.py), line 200)
- `accept_proposal_items(ctx: SidecarContext, params: ProposalDecisionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/proposals.py), line 206) — Accept (and apply) pending proposal items, then return the refreshed inbox.
- `reject_proposal_items(ctx: SidecarContext, params: ProposalDecisionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/proposals.py), line 224) — Reject proposal items (reverting any already-applied change), then refresh.
- `reset_proposal_items(ctx: SidecarContext, params: ProposalDecisionInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/proposals.py), line 241) — Undo a rejection (never-applied items back to pending), then refresh.
- `class EditProposalItemInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/proposals.py), line 252)
- `edit_proposal_item(ctx: SidecarContext, params: EditProposalItemInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/proposals.py), line 259) — Replace a pending proposal item's payload with edited JSON, then refresh.
- `class RefreshProposalItemValidationInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/proposals.py), line 284)
- `refresh_proposal_item_validation(ctx: SidecarContext, params: RefreshProposalItemValidationInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/proposals.py), line 290) — Re-run validation for the stored pending proposal payload, then refresh.
- `class DeleteProposalItemInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/proposals.py), line 301)
- `delete_proposal_item(ctx: SidecarContext, params: DeleteProposalItemInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/proposals.py), line 307) — Permanently remove a proposal item (reverting it first if applied), then refresh.

### Module constants

- `_AUTO_APPLY_TYPES` ([src/learnloop_sidecar/handlers/proposals.py](../../../../../../src/learnloop_sidecar/handlers/proposals.py), line 28)

## Internal implementation anchors

- `_duration_s(started_at: str | None, completed_at: str | None) -> float | None` ([source](../../../../../../src/learnloop_sidecar/handlers/proposals.py), line 31)
- `_review_route(item: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/proposals.py), line 42) — Display route for an item: how the review policy would treat it.
- `_render_value(value: Any) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/proposals.py), line 59)
- `_payload_lines(payload: dict[str, Any]) -> list[list[str]]` ([source](../../../../../../src/learnloop_sidecar/handlers/proposals.py), line 69) — Flatten a payload into ordered [key, rendered-value] rows for the preview.
- `_source_refs(item: dict[str, Any], batch: dict[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/proposals.py), line 79)
- `_item_dto(item: dict[str, Any], batch: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/proposals.py), line 100)
- `_count_decisions(items: list[dict[str, Any]]) -> dict[str, int]` ([source](../../../../../../src/learnloop_sidecar/handlers/proposals.py), line 133)
- `_proposals_payload(ctx: SidecarContext) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/proposals.py), line 141)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/graph_edit|learnloop_sidecar.handlers.graph_edit]] — imports `_proposals_payload`; statically calls `_proposals_payload`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `PatchApplicationError`
- [[Reference/Modules/learnloop/content/proposals/proposals|learnloop.content.proposals.proposals]] — imports `accept_items`, `delete_proposal_item`, `edit_proposal_item`, `refresh_proposal_item_validation`, `reject_items`, `reset_items`; calls `accept_items`, `delete_proposal_item`, `edit_proposal_item`, `refresh_proposal_item_validation`, `reject_items`, `reset_items`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `reconcile_accepted_question_promotion_patch`, `reconcile_rejected_question_promotion_patch`, `reconcile_reset_question_promotion_patch`; calls `reconcile_accepted_question_promotion_patch`, `reconcile_rejected_question_promotion_patch`, `reconcile_reset_question_promotion_patch`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/graph_edit|learnloop_sidecar.handlers.graph_edit]].

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

1. Modify [src/learnloop_sidecar/handlers/proposals.py](../../../../../../src/learnloop_sidecar/handlers/proposals.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.curriculum.depth_edge_authoring"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/depth_edge_authoring.py"
source_paths:
  - "src/learnloop/curriculum/depth_edge_authoring.py"
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
  - "learnloop.curriculum.depth_edge_authoring module"
  - "src/learnloop/curriculum/depth_edge_authoring.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.depth_edge_authoring`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.depth_edge_authoring` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: Depth-edge authoring: the P1 curated-edge half (spec v2 §depth, spec_p1 §3.1.1).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/depth_edge_authoring.py](../../../../../../src/learnloop/curriculum/depth_edge_authoring.py) |
| Source lines | 578 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class DepthEdgeAuthoringError(ValueError)` ([source](../../../../../../src/learnloop/curriculum/depth_edge_authoring.py), line 52)
- `request_depth_edge_instances(client: StructuredTransport, context: DepthEdgeInstanceContext) -> DepthEdgeInstanceBatch` ([source](../../../../../../src/learnloop/curriculum/depth_edge_authoring.py), line 56) — Author depth-edge candidates through the shared transport.
- `create_edge_template(repository: Repository, *, template_slug: str, body: Mapping[str, Any], domain_scope: Mapping[str, Any] | None=None, clock: Clock | None=None) -> tuple[str, str]` ([source](../../../../../../src/learnloop/curriculum/depth_edge_authoring.py), line 74) — Create a template with its version 1 (status ``draft``).
- `append_template_version(repository: Repository, *, template_slug: str, body: Mapping[str, Any], clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/curriculum/depth_edge_authoring.py), line 100)
- `review_edge_template(repository: Repository, *, version_id: str, status: str, reviewed_by: str='owner', clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/curriculum/depth_edge_authoring.py), line 122)
- `author_edge_instances(repository: Repository, client: Any, *, commitment_id: str, template_version_ids: list[str], count: int=1, author: str='codex', clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/curriculum/depth_edge_authoring.py), line 155) — LLM-author edge instances from reviewed templates; each is immediately gated and stored ``admitted`` or ``rejected`` with its full admission report.
- `admit_edge_instance(repository: Repository, *, instance: Mapping[str, Any], template_version: Mapping[str, Any], envelope_row: Mapping[str, Any]) -> list[GateDiagnostic]` ([source](../../../../../../src/learnloop/curriculum/depth_edge_authoring.py), line 253) — The six §5.7-adjacent admission gates over one candidate edge instance.
- `pin_admitted_edges(repository: Repository, *, commitment_id: str, instance_ids: list[str], confirmed_by: str='learner', receipt_key: str | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/curriculum/depth_edge_authoring.py), line 402) — Append confirmed admitted instances into a NEW envelope version (bounds unchanged — no widening) plus matching ``depth_milestone_versions`` rows.

### Module constants

- `EXIT_GATE_KINDS` ([src/learnloop/curriculum/depth_edge_authoring.py](../../../../../../src/learnloop/curriculum/depth_edge_authoring.py), line 40)
- `FRESH_PROOF_KINDS` ([src/learnloop/curriculum/depth_edge_authoring.py](../../../../../../src/learnloop/curriculum/depth_edge_authoring.py), line 41)
- `_ORDERED_VOCAB` ([src/learnloop/curriculum/depth_edge_authoring.py](../../../../../../src/learnloop/curriculum/depth_edge_authoring.py), line 45)

## Internal implementation anchors

- `_validate_template_body(body: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/curriculum/depth_edge_authoring.py), line 138)
- `_envelope_row(repository: Repository, envelope_version_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/depth_edge_authoring.py), line 493)
- `_as_dict(value: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/curriculum/depth_edge_authoring.py), line 502)
- `_value_within_bound(dim: str, value: Any, allowed: Any) -> bool` ([source](../../../../../../src/learnloop/curriculum/depth_edge_authoring.py), line 511) — Is one task-feature value inside one envelope bound?
- `_predecessor_features(repository: Repository, envelope_row: Mapping[str, Any], predecessor_milestone: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/curriculum/depth_edge_authoring.py), line 533) — The predecessor milestone's task-feature point (+capability), or None when the milestone has no stored contract (root milestones).
- `_dimension_step(dim: str, prev: Any, new: Any) -> int | None` ([source](../../../../../../src/learnloop/curriculum/depth_edge_authoring.py), line 558) — Signed depth step for one dimension (positive = deeper), or None when the values cannot be compared.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/depth|learnloop.cli.depth]] — imports `DepthEdgeAuthoringError`, `author_edge_instances`, `create_edge_template`, `pin_admitted_edges`, `review_edge_template`; statically calls `author_edge_instances`, `create_edge_template`, `pin_admitted_edges`, `review_edge_template`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `StructuredTransport`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`
- [[Reference/Modules/learnloop/content/synthesis/synthesis_gates|learnloop.content.synthesis.synthesis_gates]] — imports `GateDiagnostic`; calls `GateDiagnostic`
- [[Reference/Modules/learnloop/curriculum/ai_contracts|learnloop.curriculum.ai_contracts]] — imports `DepthEdgeInstanceBatch`, `DepthEdgeInstanceContext`, `depth_edge_instance_prompt`; calls `DepthEdgeInstanceContext`, `depth_edge_instance_prompt`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `change_depth_envelope`, `resolve_head`
- [[Reference/Modules/learnloop/curriculum/depth_rungs|learnloop.curriculum.depth_rungs]] — imports `project_task_contract`; calls `project_task_contract`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`; calls `canonical_hash`
- [[Reference/Modules/learnloop/substrate/activity_patterns|learnloop.substrate.activity_patterns]] — imports `LEGACY_UNMAPPED`, `ensure_builtin_task_feature_schema`, `ensure_capability_alias_registry`, `map_capability`, `validate_task_features`; calls `ensure_builtin_task_feature_schema`, `ensure_capability_alias_registry`, `map_capability`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/depth|learnloop.cli.depth]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change depth edge authoring policy here when curriculum owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/depth_edge_authoring.py](../../../../../../src/learnloop/curriculum/depth_edge_authoring.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

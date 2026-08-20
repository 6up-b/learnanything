---
title: "learnloop_sidecar.handlers.ladder"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/ladder.py"
source_paths:
  - "src/learnloop_sidecar/handlers/ladder.py"
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
  - "learnloop_sidecar.handlers.ladder module"
  - "src/learnloop_sidecar/handlers/ladder.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.ladder`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.ladder` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: P2 LEARNING + PRACTICE track sidecar RPC (spec_p2_narrow_golden_path §7.1-§7.3, §9; design B.6-B.7).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/ladder.py](../../../../../../src/learnloop_sidecar/handlers/ladder.py) |
| Source lines | 332 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class LadderPolicyInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 28)
- `ladder_policy(ctx: SidecarContext, params: LadderPolicyInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 33)
- `class LadderStatusInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 42)
- `ladder_status(ctx: SidecarContext, params: LadderStatusInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 47)
- `class LadderEnterInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 56)
- `ladder_enter(ctx: SidecarContext, params: LadderEnterInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 64)
- `class LadderAdvanceInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 79)
- `ladder_advance(ctx: SidecarContext, params: LadderAdvanceInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 90)
- `class PoolAssembleInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 112)
- `pool_assemble(ctx: SidecarContext, params: PoolAssembleInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 119)
- `class PoolAdmitInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 133)
- `pool_admit_surface(ctx: SidecarContext, params: PoolAdmitInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 142)
- `class PoolReviewInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 158)
- `pool_review(ctx: SidecarContext, params: PoolReviewInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 164)
- `class PoolStatusInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 173)
- `pool_status(ctx: SidecarContext, params: PoolStatusInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 178)
- `class PoolNextInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 187)
- `pool_next_surface(ctx: SidecarContext, params: PoolNextInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 194)
- `class PoolForRunInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 252)
- `pool_for_run(ctx: SidecarContext, params: PoolForRunInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 257)
- `class PoolSeedForRunInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 262)
- `pool_seed_for_run(ctx: SidecarContext, params: PoolSeedForRunInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 267) — Assemble a candidate pool from the run blueprint's familiar-anchor exemplars (§7.3).
- `class PoolAdmitAnchorInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 303)
- `pool_admit_anchor(ctx: SidecarContext, params: PoolAdmitAnchorInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 310) — Owner admits one seeded anchor surface: resolves the legacy practice item to its P0 surface (idempotent) and admits it with the run's assessment reserve as the collision guard (§7.3 hard-collision refusal).

## Internal implementation anchors

- `_require_run(ctx: SidecarContext, run_id: str) -> tuple[Any, Any, dict[str, Any]]` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 212)
- `_run_pool_view(vault: Any, repository: Any, run: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/ladder.py), line 220)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/curriculum/pattern_ladder|learnloop.curriculum.pattern_ladder]] — imports `module`; calls `active_ladder`, `advance_stage`, `enter_ladder`, `ladder_status`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `resolve_legacy_item`; calls `resolve_legacy_item`
- [[Reference/Modules/learnloop/substrate/surface_pool|learnloop.substrate.surface_pool]] — imports `module`; calls `admit_pool_surface`, `assemble_pool`, `next_practice_surface`, `pool_status`, `review_pool`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
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

1. Modify [src/learnloop_sidecar/handlers/ladder.py](../../../../../../src/learnloop_sidecar/handlers/ladder.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

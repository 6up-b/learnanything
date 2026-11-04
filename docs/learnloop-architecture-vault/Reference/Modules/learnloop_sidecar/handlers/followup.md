---
title: "learnloop_sidecar.handlers.followup"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/followup.py"
source_paths:
  - "src/learnloop_sidecar/handlers/followup.py"
source_commit: "a01ecfbb27093bad0f8c7924a0558bfc49acbc22"
source_commit_timestamp: "2026-11-04T01:43:14-05:00"
source_worktree_state: "clean"
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
  - "learnloop_sidecar.handlers.followup module"
  - "src/learnloop_sidecar/handlers/followup.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.followup`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.followup` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: FG1's RPCs: what the feedback screen's Next and its held feedback read (spec §6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/followup.py](../../../../../../src/learnloop_sidecar/handlers/followup.py) |
| Source lines | 78 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a01ecfbb27093bad0f8c7924a0558bfc49acbc22` |
| Commit timestamp | `2026-11-04T01:43:14-05:00` |

## Public API

- `class FollowupInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/followup.py), line 16)
- `followup_status(ctx: SidecarContext, params: FollowupInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/followup.py), line 34)
- `followup_next(ctx: SidecarContext, params: FollowupInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/followup.py), line 49) — Next pressed (§6.1): wait, open the probe, or go on with the plan or the queue.
- `followup_continue_without(ctx: SidecarContext, params: FollowupInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/followup.py), line 66)
- `followup_show_anyway(ctx: SidecarContext, params: FollowupInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/followup.py), line 74)

## Internal implementation anchors

- `_fresh_vault(ctx: SidecarContext, vault: Any, repository: Any, attempt_id: str) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/followup.py), line 20) — The worker wrote the question on its own slot: this process's vault reads it now.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `plan_active`; calls `plan_active`
- [[Reference/Modules/learnloop/followup_run/serving|learnloop.followup_run.serving]] — imports `continue_without`, `next_action`, `show_anyway`, `view`; calls `continue_without`, `next_action`, `show_anyway`, `view`
- [[Reference/Modules/learnloop/followup_serve/gates|learnloop.followup_serve.gates]] — imports `generate_and_serve_on`; calls `generate_and_serve_on`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `attempt_workflow`; calls `attempt_workflow`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `to_camel`, `versioned`; calls `to_camel`, `versioned`
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

- [tests/reading_path_fixtures.py](../../../../../../tests/reading_path_fixtures.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/recap_fixtures.py](../../../../../../tests/recap_fixtures.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/rw2b_fix10_base_sequence.py](../../../../../../tests/rw2b_fix10_base_sequence.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/rw2b_fix11_base_sequence.py](../../../../../../tests/rw2b_fix11_base_sequence.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/rw2c_base_sequence.py](../../../../../../tests/rw2c_base_sequence.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/rw2c_state_parity.py](../../../../../../tests/rw2c_state_parity.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad1_attempt_columns.py](../../../../../../tests/test_ad1_attempt_columns.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad23_intent_compose.py](../../../../../../tests/test_ad23_intent_compose.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad23_successor.py](../../../../../../tests/test_ad23_successor.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad2_serving.py](../../../../../../tests/test_ad2_serving.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/followup.py](../../../../../../src/learnloop_sidecar/handlers/followup.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

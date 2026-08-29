---
title: "learnloop.substrate.instrument_serving"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/instrument_serving.py"
source_paths:
  - "src/learnloop/substrate/instrument_serving.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.substrate"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.instrument_serving module"
  - "src/learnloop/substrate/instrument_serving.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.instrument_serving`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.instrument_serving` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: Which instrument classes the serving surface can actually carry.

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/instrument_serving.py](../../../../../../src/learnloop/substrate/instrument_serving.py) |
| Source lines | 115 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `unservable_reason(item) -> UnservableReason | None` ([source](../../../../../../src/learnloop/substrate/instrument_serving.py), line 65) — Why ``item`` must not be scheduled, or None when it can be served.
- `unservable_refusal(item) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/substrate/instrument_serving.py), line 90) — The refusal payload for ``item``, or None when it can be served.

### Module constants

- `UNSERVABLE_REMEDIES` ([src/learnloop/substrate/instrument_serving.py](../../../../../../src/learnloop/substrate/instrument_serving.py), line 62)
- `UNSERVABLE_ERROR_CODE` ([src/learnloop/substrate/instrument_serving.py](../../../../../../src/learnloop/substrate/instrument_serving.py), line 87)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `unservable_reason`; statically calls `unservable_reason`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]] — imports `unservable_reason`; statically calls `unservable_reason`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `unservable_refusal`; statically calls `unservable_refusal`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `unservable_reason`; statically calls `unservable_reason`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `unservable_refusal`; statically calls `unservable_refusal`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `unservable_reason`; statically calls `unservable_reason`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `unservable_reason`; statically calls `unservable_reason`
- [[Reference/Modules/learnloop/learner/contract_reachability|learnloop.learner.contract_reachability]] — imports `unservable_reason`; statically calls `unservable_reason`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `UNSERVABLE_REMEDIES`, `unservable_reason`; statically calls `unservable_reason`
- [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]] — imports `unservable_reason`; statically calls `unservable_reason`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `unservable_reason`; statically calls `unservable_reason`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `unservable_refusal`; statically calls `unservable_refusal`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `UNSERVABLE_ERROR_CODE`, `unservable_refusal`; statically calls `unservable_refusal`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]], [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]], [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]], [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] and 8 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_the_retirement_left_no_arm_behind_and_no_journey_unwritten`
- [tests/test_instrument_serving.py](../../../../../../tests/test_instrument_serving.py) — direct import
  - `test_a_laddered_stem_part_is_servable_now_that_the_stimulus_renders`
  - `test_an_error_hunt_is_servable_now_that_the_worked_solution_renders`
  - `test_an_explicitly_absent_contract_is_servable`
  - `test_an_item_carrying_both_contracts_is_servable`
  - `test_an_ordinary_item_is_servable`
  - `test_every_arm_states_a_remedy`
  - `test_the_predicate_currently_declares_no_arms`
  - `test_the_predicate_ignores_unrelated_attributes`
  - `test_the_seam_survives_the_retirement`

## Modification guidance

- Change instrument serving policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/instrument_serving.py](../../../../../../src/learnloop/substrate/instrument_serving.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

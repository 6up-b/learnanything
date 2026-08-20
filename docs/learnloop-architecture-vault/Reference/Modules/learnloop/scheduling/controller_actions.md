---
title: "learnloop.scheduling.controller_actions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/controller_actions.py"
source_paths:
  - "src/learnloop/scheduling/controller_actions.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.controller_actions module"
  - "src/learnloop/scheduling/controller_actions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.controller_actions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.controller_actions` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P4 -- the canonical action taxonomy (spec_p4_controller_and_scale §1.1).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py) |
| Source lines | 74 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `is_action(action: str) -> bool` ([source](../../../../../../src/learnloop/scheduling/controller_actions.py), line 61)
- `validate(action: str, subtype: str | None) -> None` ([source](../../../../../../src/learnloop/scheduling/controller_actions.py), line 65) — Raise if the action/subtype pair is not in the canonical taxonomy.

### Module constants

- `MEASURE_DIAGNOSTIC` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 17)
- `INSTRUCT` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 18)
- `PRACTICE` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 19)
- `ASSESS_TERMINAL` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 20)
- `MAINTAIN` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 21)
- `EXPAND_MODEL` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 22)
- `STOP` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 23)
- `ACTIONS` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 25)
- `COMPLETION_OR_REPAIR` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 31)
- `INTEGRATION` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 32)
- `TRANSFER` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 33)
- `DEPTH_PROGRESSION` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 34)
- `FLUENCY` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 35)
- `PRACTICE_SUBTYPES` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 37)
- `STOP_GOAL_SATISFIED` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 42)
- `STOP_GOAL_SATISFIED_NO_AUTHORIZED_DEPTH` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 43)
- `STOP_NO_POSITIVE_ROBUST_VALUE` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 44)
- `STOP_SAME_ACTION_ACROSS_HYPOTHESES` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 45)
- `STOP_BURDEN_OR_FATIGUE_CAP` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 46)
- `STOP_WAITING_FOR_DELAY_OR_FRESH_SURFACE` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 47)
- `STOP_MODEL_EXPANSION_NEEDED` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 48)
- `STOP_LEARNER_PAUSED_OR_STOPPED` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 49)
- `STOP_NO_FEASIBLE_ACTIVITY` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 50)
- `STOP_REASONS` ([src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py), line 52)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/scheduling/controller_cutover|learnloop.scheduling.controller_cutover]] — imports `module`
- [[Reference/Modules/learnloop/scheduling/short_session|learnloop.scheduling.short_session]] — imports `module`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `module`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/scheduling/controller_cutover|learnloop.scheduling.controller_cutover]], [[Reference/Modules/learnloop/scheduling/short_session|learnloop.scheduling.short_session]], [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_controller_cutover.py](../../../../../../tests/test_controller_cutover.py) — direct import
  - `test_advance_live_veto_persists_typed_marker`
  - `test_constraint_emptied_feasible_set_is_a_veto`
  - `test_evsi_abstain_is_a_veto`
  - `test_ladder_stop_is_not_a_veto`
  - `test_ownership_only_emptying_is_not_a_veto`
- [tests/test_reentry_short_session.py](../../../../../../tests/test_reentry_short_session.py) — direct import
  - `test_reentry_pins_target_caps_and_reports_without_backlog`
  - `test_short_session_depth_edge_stops_if_it_cannot_fit`
  - `test_short_session_stops_honestly_when_nothing_fits`
  - `test_three_minute_activity_completes_a_session`
- [tests/test_staged_policy.py](../../../../../../tests/test_staged_policy.py) — direct import
  - `test_affect_check_precedes_depth_edge`
  - `test_depth_progression_only_under_auto_within_envelope`
  - `test_no_feasible_activity_is_typed_stop`
  - `test_one_edge_discipline_and_u018_gate_off`
  - `test_planted_state_selects_expected_action`
- [tests/test_staged_policy_evsi.py](../../../../../../tests/test_staged_policy_evsi.py) — direct import
  - `test_evsi_stop_is_a_typed_stop_not_no_feasible_activity`

## Modification guidance

- Change controller actions policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/controller_actions.py](../../../../../../src/learnloop/scheduling/controller_actions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

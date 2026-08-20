---
title: "learnloop.scheduling.state_signals"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/state_signals.py"
source_paths:
  - "src/learnloop/scheduling/state_signals.py"
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
  - "learnloop.scheduling.state_signals module"
  - "src/learnloop/scheduling/state_signals.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.state_signals`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.state_signals` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P4 §14.2 cutover -- live StateSignals adapters (scope item 1).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/state_signals.py](../../../../../../src/learnloop/scheduling/state_signals.py) |
| Source lines | 209 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `misspecification(repository: Repository, snapshot: cs.ControllerSnapshot, commitment_id: str | None) -> bool` ([source](../../../../../../src/learnloop/scheduling/state_signals.py), line 85) — True when an unresolved open-set / ``other_or_unknown`` alarm exists on any commitment learning object (§4.2 rung 2).
- `decision_relevant_robust_value(repository: Repository, snapshot: cs.ControllerSnapshot, commitment_id: str | None) -> float` ([source](../../../../../../src/learnloop/scheduling/state_signals.py), line 102) — Positive when an ``in_progress`` open diagnostic episode on a commitment learning object carries unresolved decision-relevant uncertainty (§4.2 rung 3).
- `target_acquired(snapshot: cs.ControllerSnapshot, commitment_id: str | None) -> bool` ([source](../../../../../../src/learnloop/scheduling/state_signals.py), line 122) — True when the commitment has reached at least one depth milestone (§4.2 rung 4 negation).
- `retention_near_limit(snapshot: cs.ControllerSnapshot, *, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/scheduling/state_signals.py), line 135) — True when a commitment card is at or over its due boundary (§4.2 rung 9).
- `terminal_signals(repository: Repository, snapshot: cs.ControllerSnapshot, commitment_id: str | None, *, run_mode: str | None=None, terminal_shown: bool=False) -> tuple[bool, bool]` ([source](../../../../../../src/learnloop/scheduling/state_signals.py), line 150) — (``terminal_required_unshown``, ``terminal_reserve_valid``) for §4.2 rung 7.
- `derive_signals(repository: Repository, snapshot: cs.ControllerSnapshot, *, commitment_id: str | None, run_mode: str | None=None, terminal_shown: bool=False, pending_triage_route: dict[str, Any] | None=None, milestone_reached: str | None=None, milestone_evidence_receipt: dict[str, Any] | None=None, capability_fragile: bool=False, integration_failing: bool=False, goal_satisfied: bool=False, clock: Clock | None=None) -> sp.StateSignals` ([source](../../../../../../src/learnloop/scheduling/state_signals.py), line 171) — Assemble a live :class:`StateSignals` from real vault state (the five deterministic adapters above) plus the run-supplied stage material (triage route / milestone / capability-fragility / integration / goal-satisfaction), which the P2 orchestration knows directly from its stage.

### Module constants

- `OPEN_EPISODE_ROBUST_VALUE` ([src/learnloop/scheduling/state_signals.py](../../../../../../src/learnloop/scheduling/state_signals.py), line 42)

## Internal implementation anchors

- `_commitment_learning_object_ids(repository: Repository, snapshot: cs.ControllerSnapshot, commitment_id: str | None) -> set[str]` ([source](../../../../../../src/learnloop/scheduling/state_signals.py), line 45) — Learning objects in scope for THIS commitment's decision (audit M3/D4).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/scheduling/controller_cutover|learnloop.scheduling.controller_cutover]] — imports `module`; statically calls `derive_signals`
- [[Reference/Modules/learnloop/scheduling/reentry_adapter|learnloop.scheduling.reentry_adapter]] — imports `module`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/curriculum/commitments|learnloop.curriculum.commitments]] — imports `module`; calls `resolve_head`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]] — imports `module`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `module`; calls `StateSignals`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/scheduling/controller_cutover|learnloop.scheduling.controller_cutover]], [[Reference/Modules/learnloop/scheduling/reentry_adapter|learnloop.scheduling.reentry_adapter]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_state_signals.py](../../../../../../tests/test_state_signals.py) — direct import
  - `test_derive_signals_composes_all_five`
  - `test_misspecification_false_when_alarm_resolved`
  - `test_misspecification_false_when_no_alarm`
  - `test_misspecification_scoped_to_commitment_head_targets`
  - `test_misspecification_true_with_pending_generation_need`
  - `test_pending_items_episode_is_not_measurement_value`
  - `test_practice_only_run_never_requires_terminal`
  - `test_retention_near_limit_when_overdue`
  - `test_retention_not_near_limit_when_future_due`
  - `test_robust_value_positive_with_in_progress_episode`
  - `test_robust_value_zero_without_open_episode`
  - `test_target_acquired_true_with_reached_milestone`
  - `test_target_not_acquired_without_milestone`
  - `test_terminal_reserve_invalid_without_reservation`
  - `test_terminal_reserve_valid_when_reservation_present`

## Modification guidance

- Change state signals policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/state_signals.py](../../../../../../src/learnloop/scheduling/state_signals.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

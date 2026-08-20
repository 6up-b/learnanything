---
title: "learnloop.scheduling.reentry_adapter"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/reentry_adapter.py"
source_paths:
  - "src/learnloop/scheduling/reentry_adapter.py"
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
  - "learnloop.scheduling.reentry_adapter module"
  - "src/learnloop/scheduling/reentry_adapter.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.reentry_adapter`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.reentry_adapter` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P4 §12.1 -- the hiatus re-entry block-planner adapter (spec §12.1, §16.9).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/reentry_adapter.py](../../../../../../src/learnloop/scheduling/reentry_adapter.py) |
| Source lines | 287 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class CellStatus` ([source](../../../../../../src/learnloop/scheduling/reentry_adapter.py), line 63) — One facet cell's re-entry status with intervals + context (never a deficit label).
  - `as_dict(self) -> dict[str, Any]` (line 76; public)
- `class ReentryPlan` ([source](../../../../../../src/learnloop/scheduling/reentry_adapter.py), line 91)
  - `as_dict(self) -> dict[str, Any]` (line 107; public)
- `classify_cells(vault: LoadedVault, repository: Repository, goal: Goal, *, clock: Clock | None=None) -> list[CellStatus]` ([source](../../../../../../src/learnloop/scheduling/reentry_adapter.py), line 125) — Classify each decay-estimated facet cell into retained / recoverable / needs_attention by comparing FSRS Ready at the last session end vs now (§12.1).
- `plan_reentry(vault: LoadedVault, repository: Repository, goal: Goal, session: Any | None=None, *, question_cap: int=REENTRY_QUESTION_CAP, gap_days: int | None=None, mode: str='shadow', run_measure_block: bool=True, receipt_key: str | None=None, clock: Clock | None=None) -> ReentryPlan` ([source](../../../../../../src/learnloop/scheduling/reentry_adapter.py), line 214) — Plan the hiatus re-entry (§12.1).

### Module constants

- `REENTRY_QUESTION_CAP` ([src/learnloop/scheduling/reentry_adapter.py](../../../../../../src/learnloop/scheduling/reentry_adapter.py), line 50)
- `REENTRY_RECOVERABLE_BAND` ([src/learnloop/scheduling/reentry_adapter.py](../../../../../../src/learnloop/scheduling/reentry_adapter.py), line 55)
- `_RETAINED` ([src/learnloop/scheduling/reentry_adapter.py](../../../../../../src/learnloop/scheduling/reentry_adapter.py), line 57)
- `_RECOVERABLE` ([src/learnloop/scheduling/reentry_adapter.py](../../../../../../src/learnloop/scheduling/reentry_adapter.py), line 58)
- `_NEEDS_ATTENTION` ([src/learnloop/scheduling/reentry_adapter.py](../../../../../../src/learnloop/scheduling/reentry_adapter.py), line 59)

## Internal implementation anchors

- `_pinned_target(repository: Repository, goal: Goal, cells: list[CellStatus]) -> pt.TargetSet` ([source](../../../../../../src/learnloop/scheduling/reentry_adapter.py), line 185) — Pin the frozen predictive target distribution for the episode (§12.1 bullet 2).
- `_goal_conditioned_priority(cell: CellStatus) -> tuple[float, float, str]` ([source](../../../../../../src/learnloop/scheduling/reentry_adapter.py), line 203) — Re-entry sampling priority over the pinned frozen target (§12.1 bullet 3): the historically fragile / target-frontier cells first, high blueprint weight first.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

No live LearnLoop module directly imports this module in the static graph.

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`; calls `SystemClock`, `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `module`; calls `resolve_head`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `facet_projections_at`, `goal_report`; calls `facet_projections_at`, `goal_report`
- [[Reference/Modules/learnloop/learner/overconfidence|learnloop.learner.overconfidence]] — imports `blueprint_weight_by_facet`; calls `blueprint_weight_by_facet`
- [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]] — imports `module`; calls `build_snapshot`
- [[Reference/Modules/learnloop/scheduling/predictive_targets|learnloop.scheduling.predictive_targets]] — imports `module`; calls `build_from_contract_version`, `build_target_set`
- [[Reference/Modules/learnloop/scheduling/reentry_summary|learnloop.scheduling.reentry_summary]] — imports `ReentrySummary`, `reentry_summary`; calls `reentry_summary`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `module`; calls `StateSignals`, `decide`
- [[Reference/Modules/learnloop/scheduling/state_signals|learnloop.scheduling.state_signals]] — imports `module`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `Goal`, `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

No live LearnLoop module imports it directly; its current reach is tests, repository tooling, dynamic registration, or explicit manual invocation where documented above.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reentry_short_session.py](../../../../../../tests/test_reentry_short_session.py) — direct import
  - `test_reentry_classifies_retained_recoverable_needs_attention`
  - `test_reentry_pins_target_caps_and_reports_without_backlog`
  - `test_reentry_welcome_back_makes_no_diagnostic_claim`

## Modification guidance

- Change reentry adapter policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/reentry_adapter.py](../../../../../../src/learnloop/scheduling/reentry_adapter.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

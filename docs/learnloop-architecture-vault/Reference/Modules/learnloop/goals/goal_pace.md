---
title: "learnloop.goals.goal_pace"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/goals/goal_pace.py"
source_paths:
  - "src/learnloop/goals/goal_pace.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.goals"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.goals.goal_pace module"
  - "src/learnloop/goals/goal_pace.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-goals"
---

# `learnloop.goals.goal_pace`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.goals.goal_pace` exists within [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] to own the behavior summarized by its module contract: Pace read-model for a goal: work rate vs.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/goals/goal_pace.py](../../../../../../src/learnloop/goals/goal_pace.py) |
| Source lines | 100 |
| Owning package | [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class GoalPace` ([source](../../../../../../src/learnloop/goals/goal_pace.py), line 24)
  - `as_dict(self) -> dict[str, Any]` (line 34; public)
- `compute_goal_pace(vault: LoadedVault, repository: Repository, goal: Goal, report: GoalReport, *, clock: Clock | None=None) -> GoalPace` ([source](../../../../../../src/learnloop/goals/goal_pace.py), line 49)

### Module constants

- `PACE_WINDOW_DAYS` ([src/learnloop/goals/goal_pace.py](../../../../../../src/learnloop/goals/goal_pace.py), line 20)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/goals/forecast_ledger|learnloop.goals.forecast_ledger]] — imports `compute_goal_pace`; statically calls `compute_goal_pace`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `compute_goal_pace`; statically calls `compute_goal_pace`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`; calls `SystemClock`, `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `GoalReport`, `resolve_goal_scope`; calls `resolve_goal_scope`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `Goal`, `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/goals/forecast_ledger|learnloop.goals.forecast_ledger]], [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_goal_pace.py](../../../../../../tests/test_goal_pace.py) — direct import
  - `test_compute_goal_pace_open_ended`
  - `test_compute_goal_pace_with_due_date`
  - `test_daily_attempt_counts_is_zero_filled_and_buckets_by_day`
  - `test_pace_as_dict_shape`
  - `test_unknowable_remaining_surfaces_as_none`
- [tests/test_goal_projection.py](../../../../../../tests/test_goal_projection.py) — direct import

## Modification guidance

- Change goal pace policy here when goals owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/goals/goal_pace.py](../../../../../../src/learnloop/goals/goal_pace.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

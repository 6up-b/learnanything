---
title: "learnloop.goals.goal_series"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/goals/goal_series.py"
source_paths:
  - "src/learnloop/goals/goal_series.py"
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
  - "learnloop.goals.goal_series module"
  - "src/learnloop/goals/goal_series.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-goals"
---

# `learnloop.goals.goal_series`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.goals.goal_series` exists within [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] to own the behavior summarized by its module contract: Historical goal-progress series, derived by replay (no snapshot tables).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/goals/goal_series.py](../../../../../../src/learnloop/goals/goal_series.py) |
| Source lines | 247 |
| Owning package | [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class GoalSeriesPoint` ([source](../../../../../../src/learnloop/goals/goal_series.py), line 38)
  - `as_dict(self) -> dict[str, Any]` (line 53; public)
- `goal_report_series(vault: LoadedVault, repository: Repository, goal: Goal, *, clock: Clock | None=None, interval_days: int=DEFAULT_INTERVAL_DAYS, max_points: int=DEFAULT_MAX_POINTS) -> list[GoalSeriesPoint]` ([source](../../../../../../src/learnloop/goals/goal_series.py), line 88) — Weekly on-track counts from goal creation to now (last point is live).

### Module constants

- `DEFAULT_INTERVAL_DAYS` ([src/learnloop/goals/goal_series.py](../../../../../../src/learnloop/goals/goal_series.py), line 34)
- `DEFAULT_MAX_POINTS` ([src/learnloop/goals/goal_series.py](../../../../../../src/learnloop/goals/goal_series.py), line 35)

## Internal implementation anchors

- `_point_from_report(at: datetime, report) -> GoalSeriesPoint` ([source](../../../../../../src/learnloop/goals/goal_series.py), line 72)
- `_decay_point(vault, repository, goal, live, at: datetime, now: datetime) -> GoalSeriesPoint` ([source](../../../../../../src/learnloop/goals/goal_series.py), line 123)
- `_checkpoints(created: datetime, now: datetime, *, interval_days: int, max_points: int) -> list[datetime]` ([source](../../../../../../src/learnloop/goals/goal_series.py), line 144)
- `_historical_points(vault: LoadedVault, repository: Repository, goal: Goal, scope_los: list[str], checkpoints: list[datetime]) -> list[GoalSeriesPoint]` ([source](../../../../../../src/learnloop/goals/goal_series.py), line 162) — Replay-backed points, sharing one replay across checkpoints that match.
- `_attempt_counts(repository: Repository, checkpoints: list[datetime]) -> list[int]` ([source](../../../../../../src/learnloop/goals/goal_series.py), line 191)
- `_replayed_run(vault: LoadedVault, repository: Repository, goal: Goal, scope_los: list[str], checkpoints: list[datetime]) -> list[GoalSeriesPoint]` ([source](../../../../../../src/learnloop/goals/goal_series.py), line 202)
- `_replay_and_report(vault: LoadedVault, scratch_repo: Repository, goal: Goal, scope_los: list[str], checkpoints: list[datetime]) -> list[GoalSeriesPoint]` ([source](../../../../../../src/learnloop/goals/goal_series.py), line 217)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `prune_rows`; statically calls `prune_rows`
- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `goal_report_series`; statically calls `goal_report_series`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `FrozenClock`, `SystemClock`, `parse_utc`; calls `FrozenClock`, `SystemClock`, `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `goal_report`, `projected_ready_mean_at`, `resolve_goal_scope`; calls `goal_report`, `projected_ready_mean_at`, `resolve_goal_scope`
- [[Reference/Modules/learnloop/goals/goal_series_store|learnloop.goals.goal_series_store]] — imports `prune_rows`; calls `prune_rows`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `rebuild_derived_state`; calls `rebuild_derived_state`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `Goal`, `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `pathlib`, `shutil`, `tempfile`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]], [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_goal_series.py](../../../../../../tests/test_goal_series.py) — direct import
  - `test_series_caps_points_and_keeps_recent_window`
  - `test_series_reflects_evidence_arriving_over_time`
  - `test_series_replays_past_non_cascading_attempt_references`
  - `test_series_scratch_copy_attaches_without_migrating`
  - `test_series_shares_one_replay_across_unchanged_checkpoints`

## Modification guidance

- Change goal series policy here when goals owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/goals/goal_series.py](../../../../../../src/learnloop/goals/goal_series.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.goals.forecast_ledger"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/goals/forecast_ledger.py"
source_paths:
  - "src/learnloop/goals/forecast_ledger.py"
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
  - "learnloop.goals.forecast_ledger module"
  - "src/learnloop/goals/forecast_ledger.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-goals"
---

# `learnloop.goals.forecast_ledger`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.goals.forecast_ledger` exists within [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] to own the behavior summarized by its module contract: Issuance and reality-based resolution of frozen learner forecasts.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/goals/forecast_ledger.py](../../../../../../src/learnloop/goals/forecast_ledger.py) |
| Source lines | 274 |
| Owning package | [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ForecastError(ValueError)` ([source](../../../../../../src/learnloop/goals/forecast_ledger.py), line 18)
- `issue_forecast(repository: Repository, *, goal_id: str, kind: str, input_snapshot_hash: str, algorithm_version: str, horizon: str, target_metric: str, predicted_value: float, model_coverage: Mapping[str, Any] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/forecast_ledger.py), line 22)
- `resolve_due_forecasts(repository: Repository, *, current_estimates: Mapping[str, float] | None=None, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/goals/forecast_ledger.py), line 117) — Resolve due rows only from outcomes; estimates become projection drift.
- `active_forecasts(repository: Repository, goal_id: str) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/goals/forecast_ledger.py), line 167) — Read-only: the current open issued forecast per kind for a goal.
- `forecast_track_record(repository: Repository, goal_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/forecast_ledger.py), line 183)
- `issue_goal_forecasts(vault, repository: Repository, *, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/goals/forecast_ledger.py), line 206) — Issue material decay/pace snapshots at session start, never at render.

### Module constants

- `RESOLUTION_RULE_VERSION` ([src/learnloop/goals/forecast_ledger.py](../../../../../../src/learnloop/goals/forecast_ledger.py), line 15)

## Internal implementation anchors

- `_scoped_attempts(repository: Repository, forecast: Mapping[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/goals/forecast_ledger.py), line 57)
- `_cold_outcomes(repository: Repository, forecast: Mapping[str, Any], now) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/goals/forecast_ledger.py), line 78)
- `_attempt_facets(attempt: Mapping[str, Any]) -> set[str]` ([source](../../../../../../src/learnloop/goals/forecast_ledger.py), line 104) — Read facets from either a decoded attempt or the repository's raw row.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]] — imports `active_forecasts`, `forecast_track_record`; statically calls `active_forecasts`, `forecast_track_record`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `resolve_due_forecasts`; statically calls `resolve_due_forecasts`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `issue_goal_forecasts`, `resolve_due_forecasts`; statically calls `issue_goal_forecasts`, `resolve_due_forecasts`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/goals/goal_pace|learnloop.goals.goal_pace]] — imports `compute_goal_pace`; calls `compute_goal_pace`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `goal_report`, `resolve_goal_scope`; calls `goal_report`, `resolve_goal_scope`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/goals|learnloop_sidecar.handlers.goals]], [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]], [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_forecast_ledger.py](../../../../../../tests/test_forecast_ledger.py) — direct import
  - `test_do_nothing_forecast_is_censored_when_scope_was_practiced`
  - `test_pace_forecast_resolves_on_first_pass_beyond_horizon`
  - `test_unpracticed_decay_forecast_resolves_against_cold_outcomes_only`
- [tests/test_sidecar_goals.py](../../../../../../tests/test_sidecar_goals.py) — direct import

## Modification guidance

- Change forecast ledger policy here when goals owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/goals/forecast_ledger.py](../../../../../../src/learnloop/goals/forecast_ledger.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

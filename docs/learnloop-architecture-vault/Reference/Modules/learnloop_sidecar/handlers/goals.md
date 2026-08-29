---
title: "learnloop_sidecar.handlers.goals"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/goals.py"
source_paths:
  - "src/learnloop_sidecar/handlers/goals.py"
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
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop_sidecar.handlers.goals module"
  - "src/learnloop_sidecar/handlers/goals.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.goals`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.goals` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Goal endpoints: list/report/series, creation (wizard), status review.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/goals.py](../../../../../../src/learnloop_sidecar/handlers/goals.py) |
| Source lines | 699 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class GoalIdInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 52)
- `class GoalSeriesInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 56)
- `class ForecastTrackRecordInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 62)
- `class OptionalGoalInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 66)
- `class CreateGoalInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 70)
- `class UpdateGoalStatusInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 85)
- `class UpdateGoalIntentInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 90)
- `class GoalFeasibilityInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 95)
- `goals_list(ctx: SidecarContext, params: EmptyParams) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 317)
- `get_goal_report(ctx: SidecarContext, params: GoalIdInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 327)
- `get_goal_report_series(ctx: SidecarContext, params: GoalSeriesInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 342)
- `goal_feasibility(ctx: SidecarContext, params: GoalFeasibilityInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 374) — Wizard live read: projected standing of a not-yet-created goal.
- `get_forecast_track_record(ctx: SidecarContext, params: ForecastTrackRecordInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 421)
- `get_overconfidence_list(ctx: SidecarContext, params: GoalIdInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 429) — F5 overconfidence list (§4.3): Ready-high / Demonstrated-false facets.
- `get_reentry_summary(ctx: SidecarContext, params: OptionalGoalInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 441) — F7 welcome-back diff (§4.4): survival-first re-entry summary for a goal.
- `get_decay_pressure(ctx: SidecarContext, params: OptionalGoalInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 471) — F7 no-goal fallback (§4.5): facets ranked by soonest target crossing.
- `create_goal(ctx: SidecarContext, params: CreateGoalInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 487)
- `class GenerateStarterPracticeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 593)
- `generate_starter_practice(ctx: SidecarContext, params: GenerateStarterPracticeInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 599) — Author practice for named learning objects that have none yet.
- `update_goal_status(ctx: SidecarContext, params: UpdateGoalStatusInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 644)
- `update_goal_intent(ctx: SidecarContext, params: UpdateGoalIntentInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 668) — Add, replace, or clear a learner's larger purpose after creation.

### Module constants

- `_GOAL_STATUSES` ([src/learnloop_sidecar/handlers/goals.py](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 35)
- `_SERIES_CACHE_MAX` ([src/learnloop_sidecar/handlers/goals.py](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 45)
- `_SERIES_PAYLOAD_VERSION` ([src/learnloop_sidecar/handlers/goals.py](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 49)

## Internal implementation anchors

- `_find_goal(vault: LoadedVault, goal_id: str) -> Goal` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 105)
- `_nearest_active_goal(vault: LoadedVault) -> Goal | None` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 112) — The active goal with the nearest due date (ties -> higher priority).
- `_latest_exam_dto(repository: Repository, goal: Goal) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 127)
- `_report_dto(vault: LoadedVault, report: GoalReport, *, include_facets: bool, repository: Repository | None=None, goal: Goal | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 137)
- `_practicable_item_count(vault: LoadedVault, goal: Goal, repository: Repository | None) -> int | None` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 244) — Active, non-exam-reserved Practice Items inside the goal's scope.
- `_goal_dto(vault: LoadedVault, goal: Goal, report: GoalReport | None, repository: Repository | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 282)
- `_slugify(title: str) -> str` ([source](../../../../../../src/learnloop_sidecar/handlers/goals.py), line 481)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]] — imports `GoalIdInput`, `_find_goal`; statically calls `_find_goal`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/goals/forecast_ledger|learnloop.goals.forecast_ledger]] — imports `active_forecasts`, `forecast_track_record`; calls `active_forecasts`, `forecast_track_record`
- [[Reference/Modules/learnloop/goals/goal_intent|learnloop.goals.goal_intent]] — imports `resolve_goal_quest`; calls `resolve_goal_quest`
- [[Reference/Modules/learnloop/goals/goal_pace|learnloop.goals.goal_pace]] — imports `compute_goal_pace`; calls `compute_goal_pace`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `GoalReport`, `goal_material_gaps`, `goal_report`, `resolve_goal_scope`; calls `goal_material_gaps`, `goal_report`, `resolve_goal_scope`
- [[Reference/Modules/learnloop/goals/goal_series|learnloop.goals.goal_series]] — imports `goal_report_series`; calls `goal_report_series`
- [[Reference/Modules/learnloop/learner/measurement_state|learnloop.learner.measurement_state]] — imports `require_measurement_state`; calls `require_measurement_state`
- [[Reference/Modules/learnloop/learner/overconfidence|learnloop.learner.overconfidence]] — imports `overconfidence_facets`; calls `overconfidence_facets`
- [[Reference/Modules/learnloop/scheduling/decay_pressure|learnloop.scheduling.decay_pressure]] — imports `decay_pressure`; calls `decay_pressure`
- [[Reference/Modules/learnloop/scheduling/reentry_summary|learnloop.scheduling.reentry_summary]] — imports `reentry_summary`; calls `reentry_summary`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `Goal`, `LoadedVault`; calls `Goal`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/yaml_io|learnloop.vault.yaml_io]] — imports `read_yaml`, `write_yaml`; calls `read_yaml`, `write_yaml`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `EmptyParams`, `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/exams|learnloop_sidecar.handlers.exams]].

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

1. Modify [src/learnloop_sidecar/handlers/goals.py](../../../../../../src/learnloop_sidecar/handlers/goals.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.router_objective.calibration_report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/calibration_report.py"
source_paths:
  - "src/learnloop/router_objective/calibration_report.py"
source_commit: "workspace/uncommitted @ HEAD 9a47277b99a9e26c348ea9fea39644fe8799654a"
source_commit_timestamp: "2026-11-05T08:45:43-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router_objective"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router_objective.calibration_report module"
  - "src/learnloop/router_objective/calibration_report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.calibration_report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.calibration_report` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO5 §9: the calibration section of ``learnloop router objective-report``: each arm per day with what it costs in minutes, the price's regime, the return model, the weight's scores, the goal-date read and the probe-versus-continue contrast from FG1's ``no_intervention`` floor.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/calibration_report.py](../../../../../../src/learnloop/router_objective/calibration_report.py) |
| Source lines | 212 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 9a47277b99a9e26c348ea9fea39644fe8799654a` |
| Commit timestamp | `2026-11-05T08:45:43-05:00` |

## Public API

- `stop_coin_section(connection: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/calibration_report.py), line 41)
- `checks_section(connection: Any, *, through: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/calibration_report.py), line 75)
- `floor_section(connection: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/calibration_report.py), line 109) — §9 item 5: the probe-versus-continue contrast read from FG1's ``no_intervention`` floor.
- `build(connection: Any, vault: Any, *, now: str, weight: Mapping[str, Any] | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/calibration_report.py), line 149)
- `lines(report: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/router_objective/calibration_report.py), line 185)

### Module constants

- `VERSION` ([src/learnloop/router_objective/calibration_report.py](../../../../../../src/learnloop/router_objective/calibration_report.py), line 30)
- `FLOOR_LABEL` ([src/learnloop/router_objective/calibration_report.py](../../../../../../src/learnloop/router_objective/calibration_report.py), line 31)

### Explicit exports

`__all__` declares:

- `FLOOR_LABEL`
- `VERSION`
- `build`
- `checks_section`
- `floor_section`
- `lines`
- `stop_coin_section`

## Internal implementation anchors

- `_local(stamp: str) -> str` ([source](../../../../../../src/learnloop/router_objective/calibration_report.py), line 34)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `module`; statically calls `build`, `lines`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/router_objective/assignments|learnloop.router_objective.assignments]] — imports `module`; calls `rows`
- [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]] — imports `module`; calls `administered`, `completion`, `resolve`
- [[Reference/Modules/learnloop/router_objective/goal_read|learnloop.router_objective.goal_read]] — imports `module`; calls `read`
- [[Reference/Modules/learnloop/router_objective/picks|learnloop.router_objective.picks]] — imports `module`
- [[Reference/Modules/learnloop/router_objective/scores|learnloop.router_objective.scores]] — imports `module`; calls `scores`
- [[Reference/Modules/learnloop/router_objective/stop_coin|learnloop.router_objective.stop_coin]] — imports `module`; calls `_decision_stop_responses`, `fit_return_slope`, `handed_over`, `return_rows`
- [[Reference/Modules/learnloop/router_objective/weight|learnloop.router_objective.weight]] — imports `module`; calls `posterior`, `unique_assessments`, `weight`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `statistics`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro5_calibration.py](../../../../../../tests/test_ro5_calibration.py) — direct import
  - `test_the_first_week_on_a_copy_shaped_synthetic_vault`
  - `test_the_floor_contrast_is_read_from_fg1s_no_intervention_draws`

## Modification guidance

- Make changes here when the responsibility remains calibration report within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/calibration_report.py](../../../../../../src/learnloop/router_objective/calibration_report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

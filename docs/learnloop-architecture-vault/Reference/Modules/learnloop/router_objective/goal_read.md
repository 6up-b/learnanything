---
title: "learnloop.router_objective.goal_read"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/goal_read.py"
source_paths:
  - "src/learnloop/router_objective/goal_read.py"
source_commit: "84b890f02cd674436ba3b9ce3ab22628680d0783"
source_commit_timestamp: "2026-11-05T07:25:07-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router_objective"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.router_objective.goal_read module"
  - "src/learnloop/router_objective/goal_read.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.goal_read`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.goal_read` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO5 §9 item 3: the goal-date read, a stand-in in two stages, both versioned sensors.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/goal_read.py](../../../../../../src/learnloop/router_objective/goal_read.py) |
| Source lines | 214 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `84b890f02cd674436ba3b9ce3ab22628680d0783` |
| Commit timestamp | `2026-11-05T07:25:07-05:00` |

## Public API

- `calibration_rows(connection: Any, *, through: str) -> list[tuple[float, None, float, int]]` ([source](../../../../../../src/learnloop/router_objective/goal_read.py), line 68) — ``(logit forecast, None, Y, lag)`` for each completed randomized check with a frozen forecast at its lag.
- `calibration(connection: Any, *, through: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/goal_read.py), line 87)
- `calibrated(forecast: float, fit: Mapping[str, Any]) -> float` ([source](../../../../../../src/learnloop/router_objective/goal_read.py), line 99)
- `goal_type(goal: Any) -> str` ([source](../../../../../../src/learnloop/router_objective/goal_read.py), line 103)
- `transfer(connection: Any, goals: Sequence[Any], fit: Mapping[str, Any], *, prior_sd: float, ready: Sequence[Mapping[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/goal_read.py), line 135) — The transfer slope per goal type, on each past dated goal's results paired with the calibrated pool forecast of the newest trace before its date.
- `read(connection: Any, vault: Any, *, now: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/goal_read.py), line 179) — Each active dated goal's read now, with both sensors' versions; and the ready reads, self-selected.

### Module constants

- `CALIBRATION_VERSION` ([src/learnloop/router_objective/goal_read.py](../../../../../../src/learnloop/router_objective/goal_read.py), line 31)
- `TRANSFER_VERSION` ([src/learnloop/router_objective/goal_read.py](../../../../../../src/learnloop/router_objective/goal_read.py), line 32)
- `CALIBRATION_PRIOR_MEAN` ([src/learnloop/router_objective/goal_read.py](../../../../../../src/learnloop/router_objective/goal_read.py), line 34)
- `CALIBRATION_PRIOR_VARIANCE` ([src/learnloop/router_objective/goal_read.py](../../../../../../src/learnloop/router_objective/goal_read.py), line 35)
- `READY_VIA` ([src/learnloop/router_objective/goal_read.py](../../../../../../src/learnloop/router_objective/goal_read.py), line 36)
- `SELF_SELECTED` ([src/learnloop/router_objective/goal_read.py](../../../../../../src/learnloop/router_objective/goal_read.py), line 37)

### Explicit exports

`__all__` declares:

- `CALIBRATION_PRIOR_MEAN`
- `CALIBRATION_PRIOR_VARIANCE`
- `CALIBRATION_VERSION`
- `TRANSFER_VERSION`
- `calibrated`
- `calibration`
- `calibration_rows`
- `goal_type`
- `read`
- `transfer`

## Internal implementation anchors

- `_parse(stamp: str) -> datetime` ([source](../../../../../../src/learnloop/router_objective/goal_read.py), line 40)
- `_logit(p: float) -> float` ([source](../../../../../../src/learnloop/router_objective/goal_read.py), line 44)
- `_sigmoid(x: float) -> float` ([source](../../../../../../src/learnloop/router_objective/goal_read.py), line 49)
- `_traces(connection: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/goal_read.py), line 53)
- `_ready_reads(connection: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/goal_read.py), line 107) — Every "Am I ready?" Check once (its goal, LO, creation) and its first answer, flagged self-selected.
- `_results(connection: Any, lo: str, on: str) -> list[float]` ([source](../../../../../../src/learnloop/router_objective/goal_read.py), line 129)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/router_objective/calibration_report|learnloop.router_objective.calibration_report]] — imports `module`; statically calls `read`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]] — imports `module`; calls `resolve`
- [[Reference/Modules/learnloop/router_objective/memory|learnloop.router_objective.memory]] — imports `module`; calls `Combiner`, `fit_combiner`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/router_objective/calibration_report|learnloop.router_objective.calibration_report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro5_calibration.py](../../../../../../tests/test_ro5_calibration.py) — direct import
  - `test_the_goal_read_on_a_vault_with_no_results_is_its_priors_and_labels_ready_reads`
  - `test_the_pool_recalibration_moves_with_overconfident_checks`

## Modification guidance

- Make changes here when the responsibility remains goal read within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/goal_read.py](../../../../../../src/learnloop/router_objective/goal_read.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

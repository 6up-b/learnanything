---
title: "learnloop.teacher.report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/report.py"
source_paths:
  - "src/learnloop/teacher/report.py"
source_commit: "workspace/uncommitted @ HEAD 271a042fd6e7c418c6abdb96d8eb08fd1d8e595a"
source_commit_timestamp: "2026-11-06T11:32:04-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.teacher"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.teacher.report module"
  - "src/learnloop/teacher/report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.report` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: The learned lesson-check weight's report lines (spec_teacher_v1 §12.1 "Kill switch and monitoring").

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/report.py](../../../../../../src/learnloop/teacher/report.py) |
| Source lines | 322 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 271a042fd6e7c418c6abdb96d8eb08fd1d8e595a` |
| Commit timestamp | `2026-11-06T11:32:04-05:00` |

## Public API

- `report(vault: Any, repository: Any, *, today: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/report.py), line 44)
- `lesson_report(vault: Any, repository: Any, *, today: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/report.py), line 302) — TE2-log's report lines (spec §11.10), read-only: lessons (opened, closed by reason, active and elapsed minutes apart with the intervals missing, delayed checks committed, due, answered and their results), episodes (by kind; probes generated, refused, retired and answered; detour…

### Module constants

- `COVERAGE_FIELDS` ([src/learnloop/teacher/report.py](../../../../../../src/learnloop/teacher/report.py), line 108)

### Explicit exports

`__all__` declares:

- `COVERAGE_FIELDS`
- `lesson_report`
- `report`

## Internal implementation anchors

- `_posterior_sd(state: LW.WeightState, index: int) -> float` ([source](../../../../../../src/learnloop/teacher/report.py), line 36)
- `_scores(pairs: list[tuple[float, float]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/report.py), line 124)
- `_score_words(scores: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/teacher/report.py), line 134)
- `_has(connection: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/teacher/report.py), line 141)
- `_lessons_part(vault: Any, repository: Any, connection: Any, today: str) -> tuple[dict[str, Any], list[str]]` ([source](../../../../../../src/learnloop/teacher/report.py), line 146)
- `_episodes_part(episodes: list[dict[str, Any]]) -> tuple[dict[str, Any], list[str]]` ([source](../../../../../../src/learnloop/teacher/report.py), line 203)
- `_coverage_part(episodes: list[dict[str, Any]]) -> tuple[dict[str, Any], list[str]]` ([source](../../../../../../src/learnloop/teacher/report.py), line 237)
- `_forecasts_part(vault: Any, connection: Any, today: str) -> tuple[dict[str, Any], list[str]]` ([source](../../../../../../src/learnloop/teacher/report.py), line 249) — ``lesson_probe_correct`` against the probes' grades; ``lesson_node_held`` against natural outcomes (the first qualifying cold outcome: self-selected) and, apart, against RO5's randomized checks (each with its ``r``).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/teacher|learnloop.cli.teacher]] — imports `report`; statically calls `report`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/lessons|learnloop.db.stores.lessons]] — imports `module`; calls `episode_tables_present`, `episodes`, `receipt`
- [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]] — imports `resolved_receipts`; calls `resolved_receipts`
- [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]] — imports `module`; calls `pool_trajectory`, `replay_state`
- [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]] — imports `module`; calls `resolve`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `LESSON_NODE_HELD`
- [[Reference/Modules/learnloop/teacher/episodes|learnloop.teacher.episodes]] — imports `module`; calls `lesson_minutes`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/teacher|learnloop.cli.teacher]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_teacher_te1_weight.py](../../../../../../tests/test_teacher_te1_weight.py) — direct import
  - `test_the_report_lines`
- [tests/test_teacher_te2_lessons.py](../../../../../../tests/test_teacher_te2_lessons.py) — direct import
  - `test_the_report_counts_probes_by_refusal_reason`
- [tests/test_teacher_te2log_report.py](../../../../../../tests/test_teacher_te2log_report.py) — direct import
  - `test_randomized_checks_are_scored_apart_with_their_r`
  - `test_the_pool_weights_trajectory_per_forecaster`
  - `test_the_report_on_a_synthetic_lesson`

## Modification guidance

- Make changes here when the responsibility remains report within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/report.py](../../../../../../src/learnloop/teacher/report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

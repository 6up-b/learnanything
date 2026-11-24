---
title: "learnloop.db.stores.grade_curves"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/grade_curves.py"
source_paths:
  - "src/learnloop/db/stores/grade_curves.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.db.stores.grade_curves module"
  - "src/learnloop/db/stores/grade_curves.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.grade_curves`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.grade_curves` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Immutable inputs of the lesson-weight fit.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/grade_curves.py](../../../../../../../src/learnloop/db/stores/grade_curves.py) |
| Source lines | 120 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

## Public API

- `class GradeCurve` ([source](../../../../../../../src/learnloop/db/stores/grade_curves.py), line 15)
  - `trace(self) -> dict` (line 24; public)
- `current_curve(connection: sqlite3.Connection, attempt_id: str) -> GradeCurve` ([source](../../../../../../../src/learnloop/db/stores/grade_curves.py), line 39)
- `capture_grade_curve(connection: sqlite3.Connection, attempt_id: str, prediction: Mapping[str, float], version: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/grade_curves.py), line 57) — The curve the current epoch's grade was applied with.
- `snapshot_grade_curves(connection: sqlite3.Connection, predecessor: str, *, score_bucket: Callable[[float], str]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/grade_curves.py), line 97) — Fill uncovered epochs, returning whether any first snapshots need to commit.

## Internal implementation anchors

- `_epochs(connection: sqlite3.Connection, attempt_id: str) -> list[dict]` ([source](../../../../../../../src/learnloop/db/stores/grade_curves.py), line 28)
- `_key(epoch: GradingEpoch | None) -> tuple[str, int | None]` ([source](../../../../../../../src/learnloop/db/stores/grade_curves.py), line 34)
- `_insert(connection: sqlite3.Connection, attempt_id: str, key: str, revision: int | None, a: float | None, b: float | None, version: str, provenance: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/grade_curves.py), line 49)
- `_historical_pair(payload: str | None) -> tuple[float | None, float | None]` ([source](../../../../../../../src/learnloop/db/stores/grade_curves.py), line 70)
- `_applied_current(observed_json: str | None, correctness: float | None, score_bucket: Callable[[float], str]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/grade_curves.py), line 82) — Whether the surprise row can describe the current epoch: its observed score bucket is the current grade's.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `current_curve`; statically calls `current_curve`
- [[Reference/Modules/learnloop/db/stores/attempts|learnloop.db.stores.attempts]] — imports `capture_grade_curve`; statically calls `capture_grade_curve`
- [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]] — imports `current_curve`; statically calls `current_curve`
- [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]] — imports `snapshot_grade_curves`; statically calls `snapshot_grade_curves`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `capture_grade_curve`; statically calls `capture_grade_curve`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/grading_epochs|learnloop.grading_epochs]] — imports `GradingEpoch`, `current_epoch`, `group_epochs`; calls `current_epoch`, `group_epochs`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `math`, `sqlite3`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/db/stores/attempts|learnloop.db.stores.attempts]], [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]], [[Reference/Modules/learnloop/ops/upgrades|learnloop.ops.upgrades]], [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_teacher_te5_grade_curves.py](../../../../../../../tests/test_teacher_te5_grade_curves.py) — direct import
  - `test_regrade_adds_a_curve_for_only_the_new_epoch`
  - `test_upgrade_labels_superseded_epochs_and_keeps_a_legacy_stamp`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/grade_curves.py](../../../../../../../src/learnloop/db/stores/grade_curves.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

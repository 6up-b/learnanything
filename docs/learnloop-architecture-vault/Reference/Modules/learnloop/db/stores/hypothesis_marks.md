---
title: "learnloop.db.stores.hypothesis_marks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/hypothesis_marks.py"
source_paths:
  - "src/learnloop/db/stores/hypothesis_marks.py"
source_commit: "workspace/uncommitted @ HEAD 4a801f1afce0faaf0246a9bd404a8ed73abf2dfb"
source_commit_timestamp: "2026-11-04T19:32:38-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop.db.stores"
layer: "infrastructure"
concepts:
  - "State and Persistence"
  - "Architecture Overview"
workflows:
  - "Inspect Persistent State"
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.db.stores.hypothesis_marks module"
  - "src/learnloop/db/stores/hypothesis_marks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.hypothesis_marks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.hypothesis_marks` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: FG1c's records (migration 242): the exposure receipts and the raw marks ledger.

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/hypothesis_marks.py](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py) |
| Source lines | 190 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 4a801f1afce0faaf0246a9bd404a8ed73abf2dfb` |
| Commit timestamp | `2026-11-04T19:32:38-05:00` |

## Public API

- `present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 36) — False on a database below migration 242: every reader treats that as no marks.
- `insert_exposure(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 61) — One display of a list; its id, or None (a warning) when refused.
- `insert_mark(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str | None` ([source](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 68) — One mark, appended; its id, or None (a warning) when refused.
- `link_probe_answer(connection: sqlite3.Connection, *, attempt_id: str, probe_attempt_id: str, at: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 75) — Each earlier display of this attempt's list gets its later receipt; a repeat adds nothing, and the exposure rows themselves never change.
- `marks_for_attempt(connection: sqlite3.Connection, attempt_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 111) — Every mark on the attempt, oldest first.
- `marks_for_learning_objects(connection: sqlite3.Connection, learning_object_ids: Iterable[str], *, before: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 118) — Every mark on these topics made before ``before``, oldest first.
- `all_marks(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 132)
- `all_exposures(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 136)
- `exposures_for_attempt(connection: sqlite3.Connection, attempt_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 140)
- `exposures_of_causes(connection: sqlite3.Connection, *, attempt_id: str, factor_id: str | None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 145) — Every display of this attempt's causes or this factor's, oldest first.
- `probe_links(connection: sqlite3.Connection, attempt_id: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 155)
- `latest_observation(connection: sqlite3.Connection, factor_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 162) — The newest answered observation of a factor (the discriminating-observation receipt), or None.
- `attempt_of_item(connection: sqlite3.Connection, practice_item_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 174) — The first answer to a (single-use) item, or None.
- `decode_ids(value: Any) -> list[str]` ([source](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 185)

### Module constants

- `EXPOSURES` ([src/learnloop/db/stores/hypothesis_marks.py](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 21)
- `PROBE_LINKS` ([src/learnloop/db/stores/hypothesis_marks.py](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 22)
- `MARKS` ([src/learnloop/db/stores/hypothesis_marks.py](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 23)
- `EXPOSURE_COLUMNS` ([src/learnloop/db/stores/hypothesis_marks.py](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 25)
- `MARK_COLUMNS` ([src/learnloop/db/stores/hypothesis_marks.py](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 29)
- `_MARKS_WITH_STATEMENT` ([src/learnloop/db/stores/hypothesis_marks.py](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 105)

## Internal implementation anchors

- `_insert(connection: sqlite3.Connection, table: str, columns: tuple[str, ...], row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 45)
- `_rows(cursor: Iterable[Any]) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py), line 100)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `module`; statically calls `marks_for_learning_objects`, `present`
- [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]] — imports `module`; statically calls `all_marks`, `present`
- [[Reference/Modules/learnloop/followup_run/marks|learnloop.followup_run.marks]] — imports `module`; statically calls `insert_exposure`, `insert_mark`, `marks_for_attempt`, `present`
- [[Reference/Modules/learnloop/followup_serve/marks|learnloop.followup_serve.marks]] — imports `module`; statically calls `attempt_of_item`, `latest_observation`, `marks_for_attempt`, `present`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `module`; statically calls `exposures_of_causes`, `link_probe_answer`, `present`
- [[Reference/Modules/learnloop/ops/capture_report|learnloop.ops.capture_report]] — imports `module`; statically calls `all_exposures`, `all_marks`, `decode_ids`, `present`, `probe_links`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `logging`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]], [[Reference/Modules/learnloop/diagnosis/split/history|learnloop.diagnosis.split.history]], [[Reference/Modules/learnloop/followup_run/marks|learnloop.followup_run.marks]], [[Reference/Modules/learnloop/followup_serve/marks|learnloop.followup_serve.marks]], [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followup_fg1c_r1_exposure_independence.py](../../../../../../../tests/test_followup_fg1c_r1_exposure_independence.py) — direct import
- [tests/test_hypothesis_marks.py](../../../../../../../tests/test_hypothesis_marks.py) — direct import
  - `test_a_refused_row_rolls_back_alone_and_the_rest_of_the_transaction_stands`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/hypothesis_marks.py](../../../../../../../src/learnloop/db/stores/hypothesis_marks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

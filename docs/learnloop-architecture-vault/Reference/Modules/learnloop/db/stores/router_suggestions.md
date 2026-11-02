---
title: "learnloop.db.stores.router_suggestions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/router_suggestions.py"
source_paths:
  - "src/learnloop/db/stores/router_suggestions.py"
source_commit: "6e6bd6afe66bdfe4b5aa19c8e19cb4e05d849b2d"
source_commit_timestamp: "2026-11-02T08:47:44-05:00"
source_worktree_state: "clean"
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
  - "learnloop.db.stores.router_suggestions module"
  - "src/learnloop/db/stores/router_suggestions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.router_suggestions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.router_suggestions` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: The only SQL for teacher TE1b's lesson suggestions (migration 236; spec_teacher_v1 §15.1, §18.1).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/router_suggestions.py](../../../../../../../src/learnloop/db/stores/router_suggestions.py) |
| Source lines | 206 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `6e6bd6afe66bdfe4b5aa19c8e19cb4e05d849b2d` |
| Commit timestamp | `2026-11-02T08:47:44-05:00` |

## Public API

- `tables_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 35)
- `receipt_key(day: str) -> str` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 41)
- `decision_for_day(connection: sqlite3.Connection, day: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 53)
- `decision(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 61)
- `decisions(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 68) — Every lesson-suggestion decision, oldest first.
- `responses(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 75) — Every learner response (never a release), in response order.
- `releases(connection: sqlite3.Connection) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 84) — Every reservation let go (``released`` or ``expired``), in order.
- `response_for(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 93) — The decision's one learner response (never its release).
- `release_for(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 103) — The row that let the decision's reservation go, if one did.
- `response_for_lesson(connection: sqlite3.Connection, lesson_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 113)
- `insert_response(connection: sqlite3.Connection, *, decision_id: str, response: str, candidate_ref: str, learning_object_ids: Sequence[str], responded_at: str, lesson_id: str | None=None, session_id: str | None=None, detail: Mapping[str, Any] | None=None) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 120) — Append the decision's one response (or its one release); a second of either is a no-op (False).
- `lesson_exists(connection: sqlite3.Connection, lesson_id: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 148)
- `open_lesson_learning_objects(connection: sqlite3.Connection) -> set[str]` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 152) — The LOs of every lesson still open.
- `last_lesson_opened_by_learning_object(connection: sqlite3.Connection) -> dict[str, str]` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 163) — Per LO, when the latest lesson on it opened.
- `attempts_by_learning_object(connection: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 175) — Each LO's attempts, oldest first (what the candidate reasons read).

### Module constants

- `RECEIPT_PREFIX` ([src/learnloop/db/stores/router_suggestions.py](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 19)
- `RESPONSE_KINDS` ([src/learnloop/db/stores/router_suggestions.py](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 22)
- `RELEASE_KINDS` ([src/learnloop/db/stores/router_suggestions.py](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 25)
- `_RESPONSE_SQL` ([src/learnloop/db/stores/router_suggestions.py](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 26)
- `_RELEASE_SQL` ([src/learnloop/db/stores/router_suggestions.py](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 27)
- `RESPONSE_COLUMNS` ([src/learnloop/db/stores/router_suggestions.py](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 29)

### Explicit exports

`__all__` declares:

- `RECEIPT_PREFIX`
- `RELEASE_KINDS`
- `RESPONSE_KINDS`
- `attempts_by_learning_object`
- `decision`
- `decision_for_day`
- `decisions`
- `insert_response`
- `last_lesson_opened_by_learning_object`
- `lesson_exists`
- `open_lesson_learning_objects`
- `receipt_key`
- `release_for`
- `releases`
- `response_for`
- `response_for_lesson`
- `responses`
- `tables_present`

## Internal implementation anchors

- `_decision(row: sqlite3.Row | Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/router_suggestions.py), line 45)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `module`; statically calls `decisions`, `releases`, `responses`, `tables_present`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `module`; statically calls `attempts_by_learning_object`, `decision`, `decision_for_day`, `decisions`, `insert_response`, `last_lesson_opened_by_learning_object`, `lesson_exists`, `open_lesson_learning_objects`, `receipt_key`, `release_for`, `releases`, `response_for`, `responses`, `tables_present`
- [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]] — imports `module`; statically calls `decisions`, `releases`, `responses`, `tables_present`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `module`; statically calls `lesson_exists`, `release_for`, `response_for`, `tables_present`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]], [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]], [[Reference/Modules/learnloop/daily_plan/router_card|learnloop.daily_plan.router_card]], [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followups_batch6_review_fixes.py](../../../../../../../tests/test_followups_batch6_review_fixes.py) — direct import
  - `test_f3_the_cli_labels_the_r_cold_comparison_with_observed_cold_outcomes`
- [tests/test_followups_batch6_router_report.py](../../../../../../../tests/test_followups_batch6_router_report.py) — direct import
  - `test_router_report_on_a_database_before_lesson_suggestions_is_refused`
- [tests/test_teacher_te1b_landing_r2.py](../../../../../../../tests/test_teacher_te1b_landing_r2.py) — direct import
  - `test_not_now_on_a_pending_card_releases_the_reservation`
  - `test_the_store_keeps_one_response_and_one_release_per_decision`

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/router_suggestions.py](../../../../../../../src/learnloop/db/stores/router_suggestions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

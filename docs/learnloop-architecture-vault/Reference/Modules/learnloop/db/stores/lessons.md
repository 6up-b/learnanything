---
title: "learnloop.db.stores.lessons"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/lessons.py"
source_paths:
  - "src/learnloop/db/stores/lessons.py"
source_commit: "6975ac1949e79b05a13f0cf392d617aa1d91fc25"
source_commit_timestamp: "2026-11-02T03:56:28-05:00"
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
  - "learnloop.db.stores.lessons module"
  - "src/learnloop/db/stores/lessons.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-db-stores"
---

# `learnloop.db.stores.lessons`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.lessons` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Teacher TE1 persistence (migration 234; spec_teacher_v1 §18.1).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/lessons.py](../../../../../../../src/learnloop/db/stores/lessons.py) |
| Source lines | 188 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `6975ac1949e79b05a13f0cf392d617aa1d91fc25` |
| Commit timestamp | `2026-11-02T03:56:28-05:00` |

## Public API

- `payload_hash(payload: Any) -> str` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 29)
- `insert_lesson(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 33)
- `close_lesson(connection: sqlite3.Connection, lesson_id: str, *, reason: str, closed_at: str) -> bool` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 45)
- `lesson(connection: sqlite3.Connection, lesson_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 52)
- `lessons_on(connection: sqlite3.Connection, learning_object_ids: Sequence[str], *, closed_only: bool=True, exclude: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 63) — Lessons whose LOs meet ``learning_object_ids``, newest first.
- `next_seq(connection: sqlite3.Connection, lesson_id: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 84)
- `append_turn(connection: sqlite3.Connection, *, lesson_id: str, actor: str, action: str, validation: str, refs: Mapping[str, Any] | None, payload: Any, created_at: str) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 89)
- `turns(connection: sqlite3.Connection, lesson_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 105)
- `insert_plan(connection: sqlite3.Connection, *, lesson_id: str, outline: Any, created_at: str) -> int` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 120)
- `plans(connection: sqlite3.Connection, lesson_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 130)
- `insert_check(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 137)
- `checks(connection: sqlite3.Connection, lesson_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 152)
- `insert_receipt(connection: sqlite3.Connection, *, lesson_id: str, version: str, close_reason: str, receipt: Mapping[str, Any], created_at: str) -> None` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 162)
- `receipt(connection: sqlite3.Connection, lesson_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 169)

### Explicit exports

`__all__` declares:

- `append_turn`
- `checks`
- `close_lesson`
- `insert_check`
- `insert_lesson`
- `insert_plan`
- `insert_receipt`
- `lesson`
- `lessons_on`
- `payload_hash`
- `plans`
- `receipt`
- `turns`

## Internal implementation anchors

- `_dumps(value: Any) -> str` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 21)
- `_row(cursor: sqlite3.Cursor, row: Sequence[Any]) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 25)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]] — imports `module`; statically calls `receipt`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `module`; statically calls `checks`, `lessons_on`, `receipt`, `turns`
- [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]] — imports `module`; statically calls `insert_check`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `module`; statically calls `append_turn`, `checks`, `close_lesson`, `insert_lesson`, `insert_plan`, `insert_receipt`, `lesson`, `plans`, `turns`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]], [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]], [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]], [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — imports consumer [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]]
- [tests/test_data_capture_a6_delayed_pick.py](../../../../../../../tests/test_data_capture_a6_delayed_pick.py) — imports consumer [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]]
- [tests/test_followups_batch5_recap_dependencies.py](../../../../../../../tests/test_followups_batch5_recap_dependencies.py) — imports consumer [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]]
- [tests/test_followups_batch5_recap_protection.py](../../../../../../../tests/test_followups_batch5_recap_protection.py) — imports consumer [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]]
- [tests/test_teacher_te1b_landing_r2.py](../../../../../../../tests/test_teacher_te1b_landing_r2.py) — imports consumer [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]]
- [tests/test_teacher_te1b_suggestions.py](../../../../../../../tests/test_teacher_te1b_suggestions.py) — imports consumer [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]]
- [tests/teacher_fakes.py](../../../../../../../tests/teacher_fakes.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_figures_prefetch.py](../../../../../../../tests/test_figures_prefetch.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../../tests/test_figures_prefetch_review_fixes.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch5_lesson.py](../../../../../../../tests/test_followups_batch5_lesson.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch6_review_fixes.py](../../../../../../../tests/test_followups_batch6_review_fixes.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]
- [tests/test_followups_batch6_router_report.py](../../../../../../../tests/test_followups_batch6_router_report.py) — imports consumer [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]]

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/lessons.py](../../../../../../../src/learnloop/db/stores/lessons.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

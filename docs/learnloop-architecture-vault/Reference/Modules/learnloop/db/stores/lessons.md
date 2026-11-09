---
title: "learnloop.db.stores.lessons"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/db/stores/lessons.py"
source_paths:
  - "src/learnloop/db/stores/lessons.py"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.db.stores.lessons` exists within [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] to own the behavior summarized by its module contract: Teacher TE1 persistence (migration 234; spec_teacher_v1 §18.1).

The authoritative system-level explanation remains in [[State and Persistence]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/db/stores/lessons.py](../../../../../../../src/learnloop/db/stores/lessons.py) |
| Source lines | 312 |
| Owning package | [[Reference/Modules/learnloop/db/stores/_package|learnloop.db.stores]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |

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
- `pending_delayed_checks(connection: sqlite3.Connection, *, at: str, config: Any=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 174) — Teacher TE3b (spec_teacher_v1 rev 5 §15.1a, owner decision 5): every lesson delayed check committed by a receipt written by ``at`` and not yet answered as of ``at`` (no attempt on its item after the lesson closed, known at or before ``at``: RO1's availability predicate, a decisi…
- `episode_tables_present(connection: sqlite3.Connection) -> bool` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 226)
- `insert_episode(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 232) — One episode at its opening; False when its opening action already has one (a recovered action).
- `close_episode(connection: sqlite3.Connection, episode_id: str, fields: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 246) — Set an open episode's closing fields once; False when it was already closed.
- `episodes(connection: sqlite3.Connection, lesson_id: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 258)
- `insert_interval(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 270) — One activity interval; False when its (lesson, screen session, seq) is already recorded (a resend).
- `intervals(connection: sqlite3.Connection, lesson_id: str | None=None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/db/stores/lessons.py), line 282)

### Module constants

- `EPISODE_OPEN_COLUMNS` ([src/learnloop/db/stores/lessons.py](../../../../../../../src/learnloop/db/stores/lessons.py), line 208)
- `EPISODE_CLOSE_COLUMNS` ([src/learnloop/db/stores/lessons.py](../../../../../../../src/learnloop/db/stores/lessons.py), line 217)

### Explicit exports

`__all__` declares:

- `EPISODE_CLOSE_COLUMNS`
- `EPISODE_OPEN_COLUMNS`
- `append_turn`
- `checks`
- `close_episode`
- `close_lesson`
- `episode_tables_present`
- `episodes`
- `insert_episode`
- `insert_interval`
- `intervals`
- `insert_check`
- `insert_lesson`
- `insert_plan`
- `insert_receipt`
- `lesson`
- `lessons_on`
- `pending_delayed_checks`
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

- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `module`; statically calls `pending_delayed_checks`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]] — imports `module`; statically calls `lesson`, `turns`
- [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]] — imports `module`; statically calls `receipt`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `module`; statically calls `checks`, `lessons_on`, `receipt`, `turns`
- [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]] — imports `module`; statically calls `insert_check`
- [[Reference/Modules/learnloop/teacher/episodes|learnloop.teacher.episodes]] — imports `module`; statically calls `close_episode`, `episode_tables_present`, `episodes`, `insert_episode`, `insert_interval`, `intervals`, `lesson`
- [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]] — imports `module`; statically calls `append_turn`, `lesson`, `turns`
- [[Reference/Modules/learnloop/teacher/report|learnloop.teacher.report]] — imports `module`; statically calls `episode_tables_present`, `episodes`, `receipt`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `module`; statically calls `append_turn`, `checks`, `close_lesson`, `episode_tables_present`, `episodes`, `insert_lesson`, `insert_plan`, `insert_receipt`, `lesson`, `plans`, `turns`
- [[Reference/Modules/learnloop/teacher/te2|learnloop.teacher.te2]] — imports `module`; statically calls `lessons_on`, `plans`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `attempt_time_sql`; calls `attempt_time_sql`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]], [[Reference/Modules/learnloop/diagnosis/text_gaps/sources|learnloop.diagnosis.text_gaps.sources]], [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]], [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]], [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]] and 5 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ih7_lesson_sources_follow_diagnosis.py](../../../../../../../tests/test_ih7_lesson_sources_follow_diagnosis.py) — direct import
- [tests/test_te3a_lesson_opportunity.py](../../../../../../../tests/test_te3a_lesson_opportunity.py) — direct import
  - `test_landing_r1_a_probe_lesson_freezes_every_display_and_its_receipt_is_judged_not_failed_closed`
- [tests/test_te3b_population.py](../../../../../../../tests/test_te3b_population.py) — direct import
  - `test_the_population_holds_los_with_a_pending_lesson_check`
- [tests/test_teacher_te2_probes.py](../../../../../../../tests/test_teacher_te2_probes.py) — direct import
  - `test_a_reserved_question_match_gives_no_probe`
- [tests/test_teacher_te2_review_fixes.py](../../../../../../../tests/test_teacher_te2_review_fixes.py) — direct import
  - `test_f3_a_fault_after_the_attempt_rolls_everything_back_and_the_answer_can_be_sent_again`
- [tests/test_teacher_te2log_activity.py](../../../../../../../tests/test_teacher_te2log_activity.py) — direct import
  - `test_a_bad_interval_is_refused_alone`
- [tests/test_teacher_te2log_episodes.py](../../../../../../../tests/test_teacher_te2log_episodes.py) — direct import
  - `test_a_refused_episode_row_rolls_back_alone_and_never_blocks_the_turn`
  - `test_te1s_forecast_node_is_resolved_and_guarded_with_the_switch_off`
- [tests/test_teacher_te2log_receipt.py](../../../../../../../tests/test_teacher_te2log_receipt.py) — direct import

## Modification guidance

- Change persistence mechanics or the owning table-family API here. Schema changes must include a migration, an explicit table role, and rebuild/compatibility review.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/db/stores/lessons.py](../../../../../../../src/learnloop/db/stores/lessons.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

---
title: "learnloop.teacher.episodes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/episodes.py"
source_paths:
  - "src/learnloop/teacher/episodes.py"
source_commit: "c1bfacd6622a998fac040f390a11c4132f80bd82"
source_commit_timestamp: "2026-11-06T01:49:29-05:00"
source_worktree_state: "clean"
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
  - "learnloop.teacher.episodes module"
  - "src/learnloop/teacher/episodes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.episodes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.episodes` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: Teacher TE2-log: item 5's logging for lessons (spec_teacher_v1 §11.3, §11.6, §11.7, §11.9; §20 row TE2-log).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/episodes.py](../../../../../../src/learnloop/teacher/episodes.py) |
| Source lines | 564 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `c1bfacd6622a998fac040f390a11c4132f80bd82` |
| Commit timestamp | `2026-11-06T01:49:29-05:00` |

## Public API

- `on(vault: Any) -> bool` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 66) — ``teacher.episode_log`` (on without a teacher section).
- `paragraph() -> str` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 74)
- `instructions(text: str, episodes: bool) -> str` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 78)
- `prompt_version(base: str, episodes: bool) -> str` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 82)
- `turn_model(base: type[TeacherTurnV1], episodes: bool) -> type[TeacherTurnV1]` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 86) — The turn's strict schema: ``base`` (TE1's or the visuals turn) off, with ``note_detour`` and ``p_held`` on.
- `doctrine_family(doctrine: str, episodes: bool) -> str` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 94) — §12.2: a turn under the episode paragraph is a different forecaster (its own λ posterior).
- `text_hash(texts: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 100)
- `has_table(connection: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 109)
- `prior_belief(repository: Any, brief: Mapping[str, Any], learning_object_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 117) — At the opening: the brief's predicted success for the node's LO with its interval and its source (the active predictor, named as the brief names it; no new read of any item parameter), the LO's mastery mean and variance now, and the open misconceptions and causal hypotheses on i…
- `origin_ids(repository: Any, lesson: Mapping[str, Any], opened_at: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 158) — The lesson's origin (``learner_pick``, or ``router`` with the accepted offer's decision id), that decision's ``router_objective_traces`` id when there is one, and every RO5 assignment (stop coin, randomized checks, open picks) in force for the lesson's day: made on the opening's…
- `open_episode(repository: Any, *, lesson: Mapping[str, Any], brief: Mapping[str, Any], kind: str, opened_by: str, opened_at: str, node_id: str | None, learning_object_id: str | None, hypotheses: Sequence[str]=(), hypothesis_payload_id: str | None=None, repair_class: str | None=None, teacher_p: float | None=None, teacher_forecast_receipt_id: str | None=None, refs: Mapping[str, Any] | None=None) -> str | None` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 208) — Insert one episode at its opening (``kind`` in :data:`KINDS`); its id, or None (refused, or its opening action already has one).
- `close_episodes(repository: Any, lesson_id: str, *, closed_at: str, reason: str, node_id: str | None=None, kind: str | None=None, outcome: Mapping[str, Any] | None=None) -> list[str]` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 240) — Close every open episode of the lesson (on ``node_id`` and of ``kind`` when given) once, with its minutes from opening to ``closed_at`` and the outcome refs; the ids closed.
- `minutes(spans: Iterable[Mapping[str, Any]], opened_at: str, closed_at: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 280) — Over ``[opened_at, closed_at]``: ``elapsed_seconds`` (the wall clock), ``active_seconds`` (the foreground intervals inside it), ``unreported_seconds`` (elapsed time no interval, foreground or not, covers: missing, never filled in), ``missing_intervals`` (seqs absent between a sc…
- `lesson_minutes(repository: Any, lesson: Mapping[str, Any], *, closed_at: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 330) — The lesson's minutes (§8.3 ``minutes``): from ``opened_at`` to its close (or ``closed_at``).
- `class ActivityRefused(ValueError)` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 352)
  - `__init__(self, code: str, message: str) -> None` (line 353; internal)
- `record_intervals(vault: Any, repository: Any, *, lesson_id: str, intervals: Sequence[Mapping[str, Any]], occurred_at: str | None, received_at: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 365) — Append the screen's intervals (one row per (lesson, screen session, seq); a resend writes nothing), each in its own savepoint.
- `node_held_receipts(state: Any, outline: Sequence[Mapping[str, Any]], *, learning_objects: Collection[str], version: int, family: str, prompt: str, doctrine: str, now: str) -> list[Any]` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 407) — One ``lesson_node_held`` forecast per plan node with ``p_held`` on a vault LO (the node's ``lo_id``, or a node named by its LO; an ``lo_id`` that is no vault LO writes none): bound to the first qualifying cold outcome on the LO, as ``lesson_step_retained`` is.
- `turn_plans(turn_obj: Any) -> list[list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 442) — The outlines a turn's ``write_plan`` requests write, in request order.
- `logged_fields(turn_obj: Any) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 449) — ``(location, text)`` of every field a turn's model wrote that a log row, a receipt or a note's payload may copy: a note's ``hypothesis`` and ``node`` (episode turns only), each plan node's ``id`` and ``lo_id`` (every turn: they reach the lesson receipt's ``nodes``).
- `node_known(state: Any, turn_obj: Any, node_id: str | None) -> bool` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 470) — A note's node names a node of the lesson's latest plan, of a plan its own turn writes (before or after the note), or a brief LO.
- `outline_lo(outline: Sequence[Mapping[str, Any]], node_id: str, learning_objects: Collection[str]) -> str | None` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 481) — The node's LO in ``outline``: its ``lo_id`` when that is a vault LO, else the node's id when that is one; None otherwise (never a guess such as the goal's LO).
- `node_lo(learning_objects: Collection[str], state: Any, turn_obj: Any, node_id: str) -> str | None` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 494) — A note's node's LO: from the newest plan holding the node (a plan its own turn writes first), else the node as an LO; :func:`outline_lo`'s rule.
- `inserted_nodes(previous: Sequence[Mapping[str, Any]] | None, outline: Sequence[Mapping[str, Any]]) -> list[str]` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 505) — Nodes a revised plan inserts before a node the previous plan had (a foundation stepped back to), in order; none for a first plan or for nodes only appended after them.
- `receipt_episodes(repository: Any, lesson_id: str) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 522) — §8.3 ``episodes``: the lesson's episode ids by kind.

### Module constants

- `LOG` ([src/learnloop/teacher/episodes.py](../../../../../../src/learnloop/teacher/episodes.py), line 50)
- `EPISODES_VERSION` ([src/learnloop/teacher/episodes.py](../../../../../../src/learnloop/teacher/episodes.py), line 53)
- `PROMPT_SUFFIX` ([src/learnloop/teacher/episodes.py](../../../../../../src/learnloop/teacher/episodes.py), line 55)
- `EPISODE_ROW_VERSION` ([src/learnloop/teacher/episodes.py](../../../../../../src/learnloop/teacher/episodes.py), line 57)
- `INTERVAL_VERSION` ([src/learnloop/teacher/episodes.py](../../../../../../src/learnloop/teacher/episodes.py), line 58)
- `KINDS` ([src/learnloop/teacher/episodes.py](../../../../../../src/learnloop/teacher/episodes.py), line 59)
- `UNLOGGED` ([src/learnloop/teacher/episodes.py](../../../../../../src/learnloop/teacher/episodes.py), line 60)
- `_PARAGRAPH` ([src/learnloop/teacher/episodes.py](../../../../../../src/learnloop/teacher/episodes.py), line 61)
- `_OPEN_HYPOTHESIS_STATUSES` ([src/learnloop/teacher/episodes.py](../../../../../../src/learnloop/teacher/episodes.py), line 63)

### Explicit exports

`__all__` declares:

- `ActivityRefused`
- `EPISODES_VERSION`
- `EPISODE_ROW_VERSION`
- `INTERVAL_VERSION`
- `KINDS`
- `PROMPT_SUFFIX`
- `UNLOGGED`
- `close_episodes`
- `doctrine_family`
- `has_table`
- `inserted_nodes`
- `instructions`
- `lesson_minutes`
- `logged_fields`
- `minutes`
- `node_held_receipts`
- `node_known`
- `node_lo`
- `on`
- `open_episode`
- `origin_ids`
- `outline_lo`
- `paragraph`
- `prior_belief`
- `prompt_version`
- `receipt_episodes`
- `record_intervals`
- `text_hash`
- `turn_model`
- `turn_plans`

## Internal implementation anchors

- `_local_day_start(at: datetime) -> datetime` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 153)
- `_guarded(repository: Any, what: str, write: Any) -> Any` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 193) — One row's write in its own savepoint of the caller's transaction: refused, it rolls back alone with a warning and the caller goes on (the turn is never blocked).
- `_overlap(start: datetime, end: datetime, lo: datetime, hi: datetime) -> tuple[datetime, datetime] | None` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 275)
- `_union_seconds(spans: Sequence[tuple[datetime, datetime]]) -> float` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 309)
- `_missing(rows: Sequence[Mapping[str, Any]]) -> int` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 323)
- `_stamp(value: Any, name: str) -> datetime` ([source](../../../../../../src/learnloop/teacher/episodes.py), line 358)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/teacher/report|learnloop.teacher.report]] — imports `module`; statically calls `lesson_minutes`
- [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]] — imports `module`; statically calls `close_episodes`, `doctrine_family`, `has_table`, `inserted_nodes`, `instructions`, `lesson_minutes`, `logged_fields`, `node_held_receipts`, `node_known`, `node_lo`, `on`, `open_episode`, `outline_lo`, `prompt_version`, `receipt_episodes`, `turn_model`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `module`; statically calls `record_intervals`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/stores/lessons|learnloop.db.stores.lessons]] — imports `module`; calls `close_episode`, `episode_tables_present`, `episodes`, `insert_episode`, `insert_interval`, `intervals`, `lesson`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/router_objective/assignments|learnloop.router_objective.assignments]] — imports `EXPERIMENTS`, `TABLE`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `ForecastReceipt`, `LESSON_COLD_OUTCOME`, `LESSON_NODE_HELD`; calls `ForecastReceipt`
- [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]] — imports `TeacherTurnEpisodesV1`, `TeacherTurnV1`, `TeacherTurnVisualsEpisodesV1`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `functools`, `hashlib`, `logging`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/teacher/report|learnloop.teacher.report]], [[Reference/Modules/learnloop/teacher/service|learnloop.teacher.service]], [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — direct import
  - `test_a_visual_turn_builds_a_teacher_figure_shown_inline_with_its_predictions_suppressed`
- [tests/test_teacher_te2log_activity.py](../../../../../../tests/test_teacher_te2log_activity.py) — direct import
  - `test_an_unknown_lesson_is_refused`
  - `test_intervals_are_appended_once_each_with_both_times`
  - `test_minutes_keep_active_and_elapsed_apart_and_missing_as_missing`
- [tests/test_teacher_te2log_episodes.py](../../../../../../tests/test_teacher_te2log_episodes.py) — direct import
  - `test_a_detour_is_one_row_with_item_5s_fields_closed_once_at_its_recheck`
  - `test_a_plan_that_inserts_a_foundation_with_no_note_is_an_unlogged_detour`
  - `test_switch_on_offers_the_paragraph_the_schema_and_its_own_forecaster`
- [tests/test_teacher_te2log_node_held.py](../../../../../../tests/test_teacher_te2log_node_held.py) — direct import
  - `test_each_p_held_is_a_lesson_node_held_forecast_on_its_lo`
- [tests/test_teacher_te2log_receipt.py](../../../../../../tests/test_teacher_te2log_receipt.py) — direct import
  - `test_a_refused_detour_row_is_a_receipt_warning`

## Modification guidance

- Make changes here when the responsibility remains episodes within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/episodes.py](../../../../../../src/learnloop/teacher/episodes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

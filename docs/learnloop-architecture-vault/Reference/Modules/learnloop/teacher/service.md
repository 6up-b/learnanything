---
title: "learnloop.teacher.service"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/service.py"
source_paths:
  - "src/learnloop/teacher/service.py"
source_commit: "356f531bdc2bfce7214becc24b5fb40e602fbd63"
source_commit_timestamp: "2026-11-06T09:10:30-05:00"
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
  - "learnloop.teacher.service module"
  - "src/learnloop/teacher/service.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-teacher"
---

# `learnloop.teacher.service`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.service` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: The lesson lifecycle behind ``lesson.turn`` (spec_teacher_v1 §6, §7, §9, §17).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py) |
| Source lines | 2495 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `356f531bdc2bfce7214becc24b5fb40e602fbd63` |
| Commit timestamp | `2026-11-06T09:10:30-05:00` |

## Public API

- `class LessonError(ValueError)` ([source](../../../../../../src/learnloop/teacher/service.py), line 96)
  - `__init__(self, code: str, message: str, *, details: Mapping[str, Any] | None=None) -> None` (line 97; internal)
- `lessons_active(vault: Any) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 104) — A lesson may open: the vault is at the teacher's successor and ``teacher.enabled`` is on.
- `require_active(vault: Any) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 111)
- `class Clients` ([source](../../../../../../src/learnloop/teacher/service.py), line 119) — The model clients one ``lesson.turn`` may use: the teacher's and the grader's (resolved lazily), and (Reader RW5d P4b) the host's figure builder for the teacher's visuals (None: the host builds no figure, so the lesson offers none and the teacher's prompt is TE1's).
- `class LessonState` ([source](../../../../../../src/learnloop/teacher/service.py), line 138)
  - `lesson_id(self) -> str` (line 164; public)
  - `closed(self) -> bool` (line 168; public)
  - `los(self) -> list[str]` (line 172; public)
  - `node_lo(self, node_id: str | None, *, outline: Sequence[Mapping[str, Any]] | None=None) -> str | None` (line 175; public) — The node's LO: its ``lo_id`` in ``outline`` (default: the latest stored plan), else the node as a brief LO, else the goal's first LO (TE1's rule).
- `load_state(repository: Any, lesson_id: str) -> LessonState` ([source](../../../../../../src/learnloop/teacher/service.py), line 192)
- `transcript(state: LessonState) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/service.py), line 258) — Every step so far, in order, as the teacher reads it (its own turns, the learner's words, results).
- `protection_changed(vault: Any, repository: Any, state: LessonState) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 344) — Whether the lesson must end before its next teacher call (ruling R1): the vault's protection state differs from the one recorded when the brief was built, it cannot be read, or a passage the lesson delivered is no longer teachable (its reading left the library, or it became prot…
- `open_lesson(vault: Any, repository: Any, *, entry: str, learning_object_ids: Sequence[str]=(), selection: Mapping[str, Any] | None=None, goal_text: str | None=None, clients: Clients, driver: str='desktop', clock: Clock | None=None, origin: str='learner_pick', origin_ref: str | None=None, lesson_id: str | None=None, add_topics: Sequence[str]=(), subject_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 635) — Open a lesson the learner started (TE1: an LO's or a Reader selection's "Teach me this"; TE1b: the Start of a router suggestion, ``origin = 'router'`` with the decision id and the lesson id its response recorded), build its brief from the ledger and run the teacher's first turn.
- `recover(vault: Any, repository: Any, state: LessonState, *, clock: Clock | None=None, reads: bool=True, builder: V.Builder | None=None) -> '_Outcome | None'` ([source](../../../../../../src/learnloop/teacher/service.py), line 755) — Run what an interrupted action left of its last accepted teacher turn (review F9): each effect the ledger does not mark done, idempotently, with its reads' results riding with the next call.
- `view_lesson(vault: Any, repository: Any, lesson_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 866) — ``lesson.view``: the lesson as the screen shows it, after recovering an interrupted action's remaining effects (no model call).
- `take_turn(vault: Any, repository: Any, *, lesson_id: str, action: str, payload: Mapping[str, Any], clients: Clients, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 876) — One learner action on an open lesson (``reply``, ``answer_prediction``, ``answer_check``, ``stop``), or ``resume``: run the teacher's turn an outage interrupted (nothing new from the learner).
- `located(field: str, indices: Sequence[int]) -> str` ([source](../../../../../../src/learnloop/teacher/service.py), line 1520) — ``check.anchors[0], check.anchors[2]``: a refusal's fields by location (landing ruling R1 (b)).
- `displayed_texts(state: LessonState, *, extra: Sequence[str]=()) -> list[str]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2192) — Everything the lesson displayed to the learner so far (accepted turns' fields), and ``extra``.
- `view(vault: Any, repository: Any, lesson_id: str, *, outcome: _Outcome | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2341) — The lesson as the screen shows it: what was shown, in order, the plan map, the open check (never its solution), the open prediction, and the close card.
- `open_lessons(vault: Any, repository: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2459) — Teacher TE2 (§11.8): Today's *Continue your lesson on X*, newest first: every open lesson with its topic in plain words.

### Module constants

- `MAX_CONTRACT_FAILURES` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 86)
- `TEACHER_PURPOSE` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 87)
- `LEARNER_ACTIONS` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 88)
- `TE2_LEARNER_ACTIONS` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 91)
- `LEARNER_TEXT_ACTIONS` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 93)
- `PROTECTION_CHANGED_NOTICE` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 340)
- `_CALLS_TEACHER` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 782)
- `_TE2_CALLS_TEACHER` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 786)
- `_TE2_RETIREMENTS_CALLING_TEACHER` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 787)
- `_FIGURE_WITHHELD` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 1880)

### Explicit exports

`__all__` declares:

- `Clients`
- `LEARNER_ACTIONS`
- `TE2_LEARNER_ACTIONS`
- `open_lessons`
- `LessonError`
- `MAX_CONTRACT_FAILURES`
- `lessons_active`
- `load_state`
- `open_lesson`
- `require_active`
- `transcript`
- `take_turn`
- `view`

## Internal implementation anchors

- `_model_result(result: Any) -> Any` ([source](../../../../../../src/learnloop/teacher/service.py), line 250) — An action's result as the teacher reads it (the alias bookkeeping stays with code).
- `_te2_transcript_entry(entry: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 321) — A TE2 step as the teacher reads it (a probe's, a filed gap, an added topic), or None for TE1's steps.
- `_end_for_protection(vault: Any, repository: Any, state: LessonState, *, clock: Clock | None, outcome: '_Outcome') -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 367)
- `_prompt(state: LessonState, *, results: Sequence[Mapping[str, Any]], help_reply: bool, visuals: bool=False, episodes: bool=False, te2: bool=False) -> str` ([source](../../../../../../src/learnloop/teacher/service.py), line 373)
- `_prompt_version(visuals: bool, episodes: bool, te2: bool) -> str` ([source](../../../../../../src/learnloop/teacher/service.py), line 396)
- `_te2_now(vault: Any, state: LessonState) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 400) — TE2 serves this lesson now: it was opened under TE2 (its brief) and the switch is on now.
- `_te2_turn(vault: Any, turn_entry: Mapping[str, Any] | None) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 406) — TE2 writes for this turn: it was written under the TE2 paragraph and the switch is on now.
- `_append(repository: Any, state: LessonState, *, actor: str, action: str, validation: str='ok', refs: Mapping[str, Any] | None=None, payload: Any=None, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 417)
- `_effect_refs(turn_entry: Mapping[str, Any] | None, effect: str, extra: Mapping[str, Any] | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 430) — The refs marking one effect of an accepted teacher turn (recovery skips what is marked).
- `_model_name(client: Any) -> str | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 440)
- `_family_of(model: str | None, *, visuals: bool=False, episodes: bool=False, te2: bool=False) -> str` ([source](../../../../../../src/learnloop/teacher/service.py), line 444) — The forecaster of §12.2's pool: the doctrine version and the teacher model.
- `_turn_flags(turn_entry: Mapping[str, Any] | None) -> dict[str, bool]` ([source](../../../../../../src/learnloop/teacher/service.py), line 454) — The paragraphs a stored turn was written under (its family and prompt version follow them).
- `_family(client: Any) -> str` ([source](../../../../../../src/learnloop/teacher/service.py), line 462)
- `_subscription(config: Any, client: Any) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 471)
- `_spent_usd(state: LessonState) -> float` ([source](../../../../../../src/learnloop/teacher/service.py), line 480) — What the lesson's metered requests cost so far: each settled request's ``spend`` row, and each reservation no settlement replaced at its whole estimate (re-review F1: a request sent before the process died may have been charged, so its reservation stands, as for a request that r…
- `_lesson_tokens(state: LessonState, outcome: '_Outcome') -> dict[str, int]` ([source](../../../../../../src/learnloop/teacher/service.py), line 497) — The whole lesson's teacher calls and tokens (every action's ``usage`` row, and this action's).
- `_spend_gate_class() -> type` ([source](../../../../../../src/learnloop/teacher/service.py), line 510)
- `_lesson_spend(vault: Any, repository: Any, state: LessonState, *, clock: Clock | None) -> Iterator[Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 561) — Hold the lesson's spend gate over one action (every model request it makes).
- `_refused_by_budget(state: LessonState, exc: BaseException) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 584)
- `_require_metered_settings(vault: Any, client: Any) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 595) — A metered (OpenRouter) lesson needs its price and its per-lesson cap first (T1 redesign D; Q7).
- `_accepted_suggestion(repository: Any, decision_id: str | None, lesson_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 611) — The learner's Start on a router suggestion (TE1b, spec §15.1): its recorded response names the lesson id and the LOs, so a lesson with origin ``router`` opens only on a response the learner gave.
- `_record_goal_los(vault: Any, repository: Any, lesson_id: str, created: Sequence[Mapping[str, Any]], *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 733) — TE2 (§11.5): one ``goal_lo`` ledger entry and one ``goal_lo`` episode row per topic the typed goal added.
- `_boundary(entry: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 790) — Whether a ledger step waits for a teacher call (it starts an action's calls).
- `class _PendingCall` ([source](../../../../../../src/learnloop/teacher/service.py), line 803) — The teacher call an interrupted action still owes (``resume`` runs it), with the mode it had.
- `_pending_call(state: LessonState) -> _PendingCall | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 813) — The call the ledger still waits for, read from the ledger itself (so it survives a restart and clears only when the consuming teacher turn commits): a learner's or code's step with no accepted teacher turn after it, with the help mode its reply recorded (re-review F15); or an ac…
- `_owes_followup(state: LessonState, accepted: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 847) — Whether ``accepted`` is the first accepted turn of its action, asked for reads, and they ran: its reads' results are owed one further call (the structural bound of :func:`_teach_loop`).
- `_learner_action(vault: Any, repository: Any, state: LessonState, action: str, payload: Mapping[str, Any], *, clients: Clients, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 925)
- `_record_help(repository: Any, state: LessonState, text: str, *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 981) — Help while a check is open (§12): one ``help_assists`` row (surface ``tutor``); never evidence.
- `_answer_check(vault: Any, repository: Any, state: LessonState, payload: Mapping[str, Any], *, clients: Clients, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 999)
- `_answer_probe(vault: Any, repository: Any, state: LessonState, payload: Mapping[str, Any], *, clients: Clients, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1083) — TE2 (§11.3): the learner's answer to the open probe, graded blind (the answer only), recorded as a ``diagnostic_probe`` attempt with the attempt id its forecast is bound to; then the teacher reads the result.
- `_latest_forecast(state: LessonState, kind: str, ref: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1118)
- `_update_weight_state(vault: Any, repository: Any) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1126) — Refresh the DERIVED weight tables after a check (the replayer's own function and bound: through the latest answered check, so a rebuild reproduces them row for row).
- `class _Outcome` ([source](../../../../../../src/learnloop/teacher/service.py), line 1142)
- `_teach(vault: Any, repository: Any, state: LessonState, *, clients: Clients, client: Any, help_reply: bool, clock: Clock | None, closing: str | None=None, followup: bool=False, results: Sequence[Mapping[str, Any]]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1154)
- `_teach_loop(vault: Any, repository: Any, state: LessonState, *, client: Any, help_reply: bool, clock: Clock | None, closing: str | None, outcome: '_Outcome', followup: bool=False, followup_results: Sequence[Mapping[str, Any]]=(), builder: V.Builder | None=None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1173)
- `_record_usage(client: Any, outcome: _Outcome) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1246)
- `_displayed(turn_obj: TeacherTurnV1) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1254) — Every learner-facing text of a turn, by field (review F3): the message and its choices, a prediction, a check, plan statements (the map) and a close's recap.
- `_logged(state: LessonState, turn_obj: TeacherTurnV1) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1276) — The model's fields a log row, a receipt or a note's payload copies, never shown, by location, on every turn (TE1's included, with ``teacher.episode_log`` off): the plan nodes' ids and ``lo_id`` (they reach the lesson receipt's ``nodes`` and, on, the episode rows), the posed chec…
- `_check_solution_fields(turn_obj: TeacherTurnV1) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1298) — The posed check's committed solution and rubric facts, by location (they become its vault item: ``checks.mint_check_item``).
- `_outline_at(state: LessonState, turn_obj: TeacherTurnV1, index: int) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1310) — The plan in force when request ``index`` runs: the last ``write_plan`` before it in the turn, else the latest stored plan (``_execute`` stores each plan before the next request runs).
- `_copies_node(state: LessonState, turn_obj: TeacherTurnV1, request: ActionRequestV1) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 1321) — Whether :func:`_forecast` copies the request's node into its receipt's key and inputs: every forecast but a check forecast with a check open or posed in the turn (its receipt names the check's ref, code-made).
- `_forecast_lo(state: LessonState, turn_obj: TeacherTurnV1, index: int, request: ActionRequestV1) -> str | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1329) — The LO :func:`_forecast` copies into request ``index``'s receipt (ruling R2: guarded before the turn is accepted): for a check forecast, the open check's (one this turn poses included), else the node's.
- `_field_names(model: type[Any]) -> frozenset[str]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1346) — Every field name of a turn schema and the models it nests (a schema refusal's location names these only).
- `_schema_detail(exc: BaseException, model: type[Any]) -> str` ([source](../../../../../../src/learnloop/teacher/service.py), line 1372) — A schema refusal as the teacher reads it (TE2-log landing, ruling R1 (b)): each failing field by its location (``requests[0].node``) and pydantic's message, never its input, so no untrusted text (an over-long node id carrying protected words) enters the transcript before the gua…
- `_call_teacher(vault: Any, repository: Any, state: LessonState, client: Any, *, results: Sequence[Mapping[str, Any]], help_reply: bool, outcome: _Outcome, clock: Clock | None, deliver: Sequence[str]=(), visuals: bool=False, episodes: bool=False, te2: bool=False) -> tuple[TeacherTurnV1, dict[str, Any]] | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1405) — One teacher call: validated, guarded, recorded.
- `_contract_problem(state: LessonState, turn_obj: TeacherTurnV1, *, vault: Any=None) -> str | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1526) — A correctable contract problem, or None.
- `_record_reveals(vault: Any, repository: Any, state: LessonState, message: str, *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1586) — Teaching text and cited passages (§12): ``tutor_answer`` for each item on the lesson's LOs whose key the text overlaps (amount = overlap, as the tutor), ``source_review`` for what a cited passage exposes; basis ``lesson:<id>``.
- `_withdraw(vault: Any, repository: Any, state: LessonState, *, overlap: float, clock: Clock | None, outcome: _Outcome, turn_entry: Mapping[str, Any] | None=None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1616)
- `_execute(vault: Any, repository: Any, state: LessonState, turn_obj: TeacherTurnV1, *, turn_entry: Mapping[str, Any], model: str | None, deferred: bool, outcome: _Outcome, clock: Clock | None, help_reply: bool, done: set[str] | frozenset[str]=frozenset(), reads: bool=True, builder: V.Builder | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1640) — An accepted turn's effects, in order, each marked with the turn and its name (``refs.effect``) in the transaction that makes it, then a ``turn_executed`` marker: recovery runs only what is unmarked (``done``), so an interrupted action resumes idempotently (review F9).
- `_episodes_turn(vault: Any, turn_entry: Mapping[str, Any] | None) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 1731) — TE2-log writes for this turn: it was written under the episode paragraph and the switch is on now.
- `_note_detour(vault: Any, repository: Any, state: LessonState, turn_obj: TeacherTurnV1, request: ActionRequestV1, *, turn_entry: Mapping[str, Any] | None, effect: str, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1737) — ``note_detour`` (§11.7): the hypothesis in the turn's payload (a ``note_detour`` entry, marked as the turn's effect) and one ``detour`` episode row, its own savepoint (a refused row rolls back alone, with a warning).
- `_serve_probe(vault: Any, repository: Any, state: LessonState, turn_obj: TeacherTurnV1, request: ActionRequestV1, *, turn_entry: Mapping[str, Any] | None, effect: str, model: str | None, outcome: '_Outcome', clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1762) — ``serve_probe`` (§11.3): its ledger entry, the ``lesson_probe_correct`` receipt (before any serve), FG1's generation job and the probe's episode row, in one transaction marked as the turn's effect.
- `_learner_turn(state: LessonState, ref: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1785) — The learner's turn a transcript ``ref`` (``t<seq>``) names, or None.
- `_gap_problem(state: LessonState, index: int, request: ActionRequestV1) -> str | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1794)
- `_gap_learning_object(state: LessonState, learner: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1804) — The LO a gap is about: the check's, when the learner's words answered one; else the lesson's first topic.
- `_propose_gap(vault: Any, repository: Any, state: LessonState, request: ActionRequestV1, *, turn_entry: Mapping[str, Any] | None, effect: str, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1821) — ``propose_gap`` (§11.7): the learner's words to the text-gap pipeline with ``source_kind = 'lesson'`` (its ``propose_gap`` entry is the source; the pipeline reads the learner's turn it names, the teacher's words as the context model's reading) and one ``gap`` episode row.
- `_plan_episodes(vault: Any, repository: Any, state: LessonState, turn_obj: TeacherTurnV1, outline: Sequence[Mapping[str, Any]], previous: Sequence[Mapping[str, Any]] | None, *, version: int, entry: Mapping[str, Any], model: str | None, turn_entry: Mapping[str, Any] | None, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1850) — A stored plan's TE2-log rows: a ``lesson_node_held`` forecast receipt per node with ``p_held`` (§11.3; each receipt its own savepoint, so a refused one leaves its siblings: Codex review F2), and an ``unlogged`` detour when it inserts a node before ones the previous plan had and…
- `_visual(vault: Any, repository: Any, state: LessonState, turn_obj: TeacherTurnV1, *, builder: V.Builder, outcome: _Outcome, clock: Clock | None, turn_entry: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1886) — Reader RW5d P4b: build the turn's visual and record it.
- `_figure_entry(vault: Any, repository: Any, record: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1936) — A lesson figure as the feed shows it (Reader RW5d P4b): its view NOW, with no predictions.
- `_pose_check(vault: Any, repository: Any, state: LessonState, check: CheckV1, *, outcome: _Outcome, clock: Clock | None, turn_entry: Mapping[str, Any] | None=None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1949)
- `_read_action(vault: Any, repository: Any, state: LessonState, request: ActionRequestV1, *, model: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1969)
- `_forecast(vault: Any, repository: Any, state: LessonState, request: ActionRequestV1, *, model: str | None, clock: Clock | None, turn_entry: Mapping[str, Any] | None=None, effect: str='forecast') -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1979)
- `_close(vault: Any, repository: Any, state: LessonState, *, reason: str, recap: str | None, clock: Clock | None, outcome: _Outcome, turn_entry: Mapping[str, Any] | None=None, effect: str='close') -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 2059) — Close the lesson: commit the delayed checks, write the receipt, close the row and append the close entry in one transaction (§7 step 7; review F9: never a closed row without its close entry).
- `_close_te2(vault: Any, repository: Any, state: LessonState, *, closed_at: str, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 2119) — At a TE2 lesson's close: every unanswered probe retired unused (reason ``lesson_closed``); each gap episode closed with the pipeline's result so far (``resolved`` with its action, else ``lesson_closed`` pending); each added topic's episode closed with its LO's undo state.
- `_receipt_te2_fields(repository: Any, state: LessonState) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2153) — A TE2 lesson's receipt additions (§8.3): its probes (status, item, attempt, grade, independence, the refusal reason), its filed gaps and the topics it added (``gaps``, ``created_los``); {} for any other lesson.
- `_lesson_shown(vault: Any, state: LessonState) -> list[str]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2184) — The lesson's own check items and the vault items its displayed text reproduced so far.
- `_receipt(vault: Any, repository: Any, state: LessonState, *, reason: str, recap: str | None, delayed_checks: Sequence[Mapping[str, Any]], warnings: Sequence[str], landed: Sequence[Mapping[str, Any]], rows: Sequence[Mapping[str, Any]], usage: Mapping[str, int], shown_items: Sequence[str]=(), closed_at: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2208) — ``LessonReceiptV1`` (§8.3).
- `_receipt_episode_fields(vault: Any, repository: Any, state: LessonState, *, closed_at: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2286) — §8.3's ``episodes`` (the lesson's episode ids by kind) and ``minutes`` (active and elapsed, and their source; never blended), and the ``lesson_node_held`` receipt keys; ``{}`` while ``teacher.episode_log`` is off.
- `_stability_inputs(repository: Any, landed: Sequence[Mapping[str, Any]], rows: Sequence[Mapping[str, Any]], state: LessonState) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2307) — Per landed node, the liquid-stability inputs ``u`` (§8.3; logged before the family activates).
- `_view_te2(vault: Any, repository: Any, state: LessonState, out: dict[str, Any], *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 2421) — A TE2 lesson's view additions: the probe card (*Preparing a question on this…* with *Teach it anyway*, or the open question, served now through FG1's first-serve claim: the question only, never its key), its results in the feed, and the topics the lesson added.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `load_state`; statically calls `load_state`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `lessons_active`; statically calls `lessons_active`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `module`; statically calls `Clients`, `open_lesson`, `open_lessons`, `require_active`, `take_turn`, `view_lesson`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInvalidOutput`, `AIOutputTruncated`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `gate_model_requests`; calls `gate_model_requests`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `output_budget`; calls `output_budget`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `MeteredRequestGate`, `SpendLimitExceeded`, `is_subscription_transport`; calls `is_subscription_transport`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `execute_structured_operation`, `render_structured_prompt`; calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `TEACHER_VERSIONS`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `record_reveal_strict`; calls `record_reveal_strict`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] — imports `insert_assist`; calls `insert_assist`
- [[Reference/Modules/learnloop/db/stores/lessons|learnloop.db.stores.lessons]] — imports `module`; calls `append_turn`, `checks`, `close_lesson`, `episode_tables_present`, `episodes`, `insert_lesson`, `insert_plan`, `insert_receipt`, `lesson`, `plans`, `turns`
- [[Reference/Modules/learnloop/db/stores/router_suggestions|learnloop.db.stores.router_suggestions]] — imports `module`; calls `lesson_exists`, `release_for`, `response_for`, `tables_present`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `enqueue_lesson_gap`, `pipeline_enabled`; calls `enqueue_lesson_gap`, `pipeline_enabled`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]] — imports `predicted_success`, `read_hedges`, `replay_state`, `tables_through`, `write_state`; calls `predicted_success`, `replay_state`, `tables_through`, `write_state`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `ForecastReceipt`, `LESSON_CHECK_ATTEMPT`, `LESSON_COLD_OUTCOME`, `record_receipts`; calls `ForecastReceipt`, `record_receipts`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `AUTO_PRIME_REVEAL_THRESHOLD`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `CoverageError`, `Library`; calls `Library`
- [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]] — imports `caller_for`, `module`; calls `caller_for`, `run_read`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `LessonRefused`, `SourceBook`, `build_brief`, `lo_prediction`, `protection_state`, `resolve_goal`, `revoke_unteachable`; calls `build_brief`, `lo_prediction`, `protection_state`, `resolve_goal`, `revoke_unteachable`
- [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]] — imports `module`; calls `check_mass`, `cold_reference`, `grade_answer`, `lesson_item`, `mint_check_item`, `record_answered_check`, `withdraw_check`
- [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]] — imports `ActionRequestV1`, `CheckV1`, `READ_ACTIONS`, `RECEIPT_VERSION`, `TURN_VERSION`, `TeacherTurnV1`
- [[Reference/Modules/learnloop/teacher/delayed|learnloop.teacher.delayed]] — imports `module`; calls `commit_checks`, `shown_vault_items`
- [[Reference/Modules/learnloop/teacher/doctrines|learnloop.teacher.doctrines]] — imports `DOCTRINE_VERSION`, `doctrine_identity`, `doctrine_text`; calls `doctrine_identity`, `doctrine_text`
- [[Reference/Modules/learnloop/teacher/episodes|learnloop.teacher.episodes]] — imports `module`; calls `close_episodes`, `close_one`, `doctrine_family`, `has_table`, `inserted_nodes`, `instructions`, `lesson_minutes`, `logged_fields`, `node_held_receipts`, `node_known`, `node_lo`, `on`, `open_episode`, `outline_lo`, `prompt_version`, `receipt_episodes`, `turn_model`
- [[Reference/Modules/learnloop/teacher/guards|learnloop.teacher.guards]] — imports `module`; calls `GuardVerdict`, `check_all`, `cited_aliases`, `key_guard`, `key_sets`, `lesson_keys`, `open_check_guard`, `reserved_book`, `reserved_guard`, `shown_feedback`, `solution_overlap`
- [[Reference/Modules/learnloop/teacher/notes|learnloop.teacher.notes]] — imports `notes_still_deliverable`, `your_notes`
- [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]] — imports `module`; calls `contract_problem`, `finish_recorded`, `logged_fields`, `open_probe`, `probes`, `record_answer`, `request`, `retire`, `serve`, `transcript_entry`, `unanswered`
- [[Reference/Modules/learnloop/teacher/te2|learnloop.teacher.te2]] — imports `module`; calls `doctrine_family`, `instructions`, `learner_ref`, `lesson_te2`, `on`, `prompt_version`, `stored_turn`, `turn_model`
- [[Reference/Modules/learnloop/teacher/topics|learnloop.teacher.topics]] — imports `module`; calls `plan_open`
- [[Reference/Modules/learnloop/teacher/visuals|learnloop.teacher.visuals]] — imports `module`; calls `active`, `build`, `contract_problem`, `displayed`, `figure_row`, `figure_text`, `instructions`, `lesson_view`, `not_built_for_protection`, `on`, `prompt_version`, `resolve`, `summary`, `turn_model`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `answer_leak_overlap`, `span_answer_overlap`; calls `answer_leak_overlap`, `span_answer_overlap`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `hashlib`, `json`, `pathlib`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/teacher_fakes.py](../../../../../../tests/teacher_fakes.py) — direct import
- [tests/test_figures_prefetch.py](../../../../../../tests/test_figures_prefetch.py) — direct import
  - `test_lesson_trigger_builds_the_planned_visuals_of_nodes_not_yet_reached`
- [tests/test_figures_prefetch_review_fixes.py](../../../../../../tests/test_figures_prefetch_review_fixes.py) — direct import
  - `test_f8_a_te1_lesson_plan_has_no_planned_visual_so_nothing_is_prebuilt`
  - `test_r5_a_planned_visual_is_prebuilt_and_the_lesson_step_reuses_it_with_no_author_call`
  - `test_r5_a_planned_visual_on_a_held_out_passage_is_not_a_candidate`
- [tests/test_followups_batch5_lesson.py](../../../../../../tests/test_followups_batch5_lesson.py) — direct import
  - `test_c_a_step_of_a_saved_lesson_whose_route_is_down_says_it_is_saved`
  - `test_c_an_opening_whose_teacher_call_fails_after_the_save_says_it_is_saved_and_carries_its_id`
  - `test_d_resume_after_a_help_action_with_a_read_follow_up_makes_no_call`
  - `test_e_the_figures_daily_budget_refusing_a_visual_leaves_the_lesson_open`
  - `test_e_the_lesson_envelope_refusing_a_visual_still_closes_the_lesson_with_budget`
- [tests/test_followups_batch5_recap_dependencies.py](../../../../../../tests/test_followups_batch5_recap_dependencies.py) — direct import
  - `test_f1_a_recap_inherited_through_last_lessons_is_left_out_with_its_source`
  - `test_f1_the_inherited_recap_stays_while_its_source_is_teachable`
  - `test_f2_a_recap_after_a_your_notes_header_is_left_out_too`
  - `test_f2_a_recap_after_read_note_is_left_out_once_only_the_note_s_source_is_protected`
  - `test_f2_the_recap_stays_when_protection_moved_elsewhere`
- [tests/test_followups_batch5_recap_protection.py](../../../../../../tests/test_followups_batch5_recap_protection.py) — direct import
  - `test_an_item_the_earlier_lesson_was_shown_now_reserved_for_an_exam_drops_its_recap`
- [tests/test_followups_batch6_review_fixes.py](../../../../../../tests/test_followups_batch6_review_fixes.py) — direct import
  - `test_f3_the_cli_labels_the_r_cold_comparison_with_observed_cold_outcomes`
- [tests/test_followups_batch6_router_report.py](../../../../../../tests/test_followups_batch6_router_report.py) — direct import
  - `test_router_report_prints_the_split_from_the_ledgers_read_only`
- [tests/test_followups_batch7_prefetch_capped_resume.py](../../../../../../tests/test_followups_batch7_prefetch_capped_resume.py) — direct import
  - `test_a_resumed_planned_visual_is_the_lesson_steps_own_request`
- [tests/test_followups_nov2_figure_provenance.py](../../../../../../tests/test_followups_nov2_figure_provenance.py) — direct import
  - `test_a_lesson_figure_keeps_its_record_and_is_rechecked_by_its_learner_inputs`
- [tests/test_reader_rw5d_p4b_teacher_visuals.py](../../../../../../tests/test_reader_rw5d_p4b_teacher_visuals.py) — direct import
  - `test_a_lesson_figure_never_spawns_a_rich_job`
  - `test_a_planned_visual_is_the_identical_request_and_hits_the_same_figure`
  - `test_a_shown_figure_held_out_since_is_no_longer_shown`
  - `test_a_shown_figures_words_count_as_the_lessons_displayed_text`
  - `test_a_visual_turn_builds_a_teacher_figure_shown_inline_with_its_predictions_suppressed`
  - `test_held_out_inputs_are_refused_before_any_call`
  - `test_lesson_turn_builds_the_visual_through_the_figure_service`
  - `test_lesson_view_never_builds_a_pending_figure`
  - `test_review_f1_a_recovered_visual_is_never_built_after_protection_changed`
  - `test_review_f1_a_visual_after_protection_changed_mid_action_is_not_built`
  - `test_review_f2_a_suppressed_prediction_is_never_counted_as_shown`
  - `test_review_f3_a_visuals_lesson_forecasts_under_its_own_family`
  - `test_review_f4_a_budget_refusal_while_recovering_a_visual_closes_the_lesson`
  - `test_switching_visuals_off_hides_a_lessons_figures_and_stops_a_pending_one`
  - `test_the_figure_never_reaches_the_grader_and_is_never_a_help_row`
- [tests/test_teacher_exam_question_guard.py](../../../../../../tests/test_teacher_exam_question_guard.py) — direct import
- [tests/test_teacher_te1_curriculum_c4.py](../../../../../../tests/test_teacher_te1_curriculum_c4.py) — direct import
  - `test_a_note_never_reaches_the_grader`
  - `test_the_brief_reads_the_deliverable_its_path_and_the_learners_notes`
  - `test_with_c4_off_the_brief_has_no_deliverable_no_notes_and_read_note_refuses`
- [tests/test_teacher_te1_lesson.py](../../../../../../tests/test_teacher_te1_lesson.py) — direct import
  - `test_a_reader_selection_of_protected_material_is_refused_in_one_line`
  - `test_a_reader_selection_opens_on_its_sections_topics`
  - `test_a_whole_lesson_opens_teaches_checks_and_closes_with_delayed_checks`
  - `test_exam_and_held_out_sentinels_never_reach_the_teacher_or_a_screen`
  - `test_forecasts_are_receipts_with_their_bindings`
  - `test_help_that_gives_the_solution_away_withdraws_the_check_with_no_attempt`
  - `test_off_or_below_the_tag_no_lesson_opens`
  - `test_read_source_find_sources_find_practice_and_read_history_return_safe_results`
  - `test_the_minted_check_item_is_held_to_its_lesson`
  - `test_while_a_check_is_open_its_solution_is_never_shown`
  - `test_with_the_learned_weight_off_a_check_enters_at_the_types_configured_mass`
- [tests/test_teacher_te1_review_fixes.py](../../../../../../tests/test_teacher_te1_review_fixes.py) — direct import
  - `test_f10_deferred_read_results_are_kept_until_a_turn_consumes_them`
  - `test_f11_an_opening_failure_carries_the_saved_lesson_and_resume_runs_it`
  - `test_f11_the_sidecar_error_carries_the_lesson_id`
  - `test_f9_an_accepted_check_turn_interrupted_before_its_effects_recovers_on_reload`
  - `test_f9_an_interrupted_turns_reads_run_with_the_next_action_never_in_lesson_view`
  - `test_f9_closing_is_one_transaction_and_an_interrupted_close_recovers`
  - `test_r3_f4_a_lesson_whose_protection_changed_ends_without_another_call`
  - `test_r3_f4_an_item_held_out_after_its_history_was_read_ends_the_lesson`
  - `test_rr_f14_resume_runs_a_read_follow_up_an_outage_interrupted`
  - `test_rr_f15_resume_keeps_the_pending_help_mode`
  - `test_rr_f1_a_reservation_is_durable_before_the_request_and_outlives_a_crash`
  - `test_rr_f1_a_settled_request_replaces_its_reservation`
- [tests/test_teacher_te1_successor.py](../../../../../../tests/test_teacher_te1_successor.py) — direct import
  - `test_a_metered_lesson_turn_needs_its_price_and_cap`
- [tests/test_teacher_te1_weight.py](../../../../../../tests/test_teacher_te1_weight.py) — direct import
- [tests/test_teacher_te1b_landing_r2.py](../../../../../../tests/test_teacher_te1b_landing_r2.py) — direct import
  - `test_an_overnight_reservation_whose_lo_is_gone_is_set_aside_and_the_day_draws`
  - `test_not_now_on_a_pending_card_releases_the_reservation`
  - `test_release_needs_a_pending_lesson`
- [tests/test_teacher_te1b_rereview_fixes.py](../../../../../../tests/test_teacher_te1b_rereview_fixes.py) — direct import
  - `test_a_reserved_lesson_is_dropped_once_teach_me_opened_one_on_it`
  - `test_a_start_left_unopened_overnight_is_offered_the_next_day`
- [tests/test_teacher_te1b_review_fixes.py](../../../../../../tests/test_teacher_te1b_review_fixes.py) — direct import
  - `test_a_provider_failure_before_the_lesson_is_saved_leaves_an_idempotent_open`
  - `test_a_start_interrupted_before_its_lesson_opened_stays_on_the_card`
- [tests/test_teacher_te1b_suggestions.py](../../../../../../tests/test_teacher_te1b_suggestions.py) — direct import
  - `test_a_closed_suggested_lessons_receipt_names_the_decision`
  - `test_responses_move_the_acceptance_model`
  - `test_the_candidate_reasons`
  - `test_the_shell_reads_lessons_and_room_to_learn_as_the_teacher_does`
- [tests/test_teacher_te2_lessons.py](../../../../../../tests/test_teacher_te2_lessons.py) — direct import
  - `test_no_to_every_leftover_teaches_the_rest_and_a_protected_goal_is_refused`
  - `test_on_the_brief_is_v2_and_the_turn_carries_te2s_actions`
  - `test_switch_off_or_below_the_tag_gives_te1s_lesson_byte_for_byte`
  - `test_the_next_lesson_on_the_same_topics_starts_where_the_last_left_off`
  - `test_today_lists_open_lessons_and_close_it_closes_with_no_teacher_call`
  - `test_typed_goals_need_the_switch`
  - `test_yes_to_a_leftover_creates_the_topic_with_teacher_goal_v1_and_one_goal_lo_episode`
- [tests/test_teacher_te2_probes.py](../../../../../../tests/test_teacher_te2_probes.py) — direct import
  - `test_a_probe_is_generated_once_served_cold_and_never_again`
- [tests/test_teacher_te2_review_fixes.py](../../../../../../tests/test_teacher_te2_review_fixes.py) — direct import
  - `test_f3_a_fault_after_the_attempt_rolls_everything_back_and_the_answer_can_be_sent_again`
  - `test_f3_a_second_submit_of_an_answered_probe_returns_its_result`
  - `test_f4_resume_after_a_probe_result_whose_teacher_call_never_ran`
  - `test_f4_resume_after_teach_it_anyway_whose_teacher_call_never_ran`
  - `test_f5_a_metered_typed_goal_resolver_is_sent_nothing`
  - `test_f6_today_can_close_a_te1_lesson_left_open_before_te2_was_switched_on`
- [tests/test_teacher_te2_sidecar.py](../../../../../../tests/test_teacher_te2_sidecar.py) — direct import
  - `test_lesson_goal_and_open_lessons_through_the_handlers`
- [tests/test_teacher_te2log_activity.py](../../../../../../tests/test_teacher_te2log_activity.py) — direct import
  - `test_an_episodes_minutes_come_from_the_screens_intervals`
- [tests/test_teacher_te2log_episodes.py](../../../../../../tests/test_teacher_te2log_episodes.py) — direct import
  - `test_a_detour_is_one_row_with_item_5s_fields_closed_once_at_its_recheck`
  - `test_a_plan_node_carrying_another_los_reserved_key_is_withheld_by_location`
  - `test_switch_off_keeps_te1s_lesson_byte_identical`
  - `test_switch_on_offers_the_paragraph_the_schema_and_its_own_forecaster`
  - `test_te1s_forecast_node_is_resolved_and_guarded_with_the_switch_off`
- [tests/test_teacher_te2log_node_held.py](../../../../../../tests/test_teacher_te2log_node_held.py) — direct import
  - `test_each_p_held_is_a_lesson_node_held_forecast_on_its_lo`
- [tests/test_teacher_te2log_receipt.py](../../../../../../tests/test_teacher_te2log_receipt.py) — direct import
- [tests/test_teacher_te2log_report.py](../../../../../../tests/test_teacher_te2log_report.py) — direct import
  - `test_the_pool_weights_trajectory_per_forecaster`

## Modification guidance

- Make changes here when the responsibility remains service within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

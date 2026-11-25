---
title: "learnloop.teacher.service"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/teacher/service.py"
source_paths:
  - "src/learnloop/teacher/service.py"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.teacher.service` exists within [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] to own the behavior summarized by its module contract: The lesson lifecycle behind ``lesson.turn`` (spec_teacher_v1 §6, §7, §9, §17).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py) |
| Source lines | 3335 |
| Owning package | [[Reference/Modules/learnloop/teacher/_package|learnloop.teacher]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class LessonError(ValueError)` ([source](../../../../../../src/learnloop/teacher/service.py), line 111)
  - `__init__(self, code: str, message: str, *, details: Mapping[str, Any] | None=None) -> None` (line 112; internal)
- `lessons_active(vault: Any) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 119) — A lesson may open: ``teacher.enabled`` is on.
- `require_active(vault: Any) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 125)
- `class Clients` ([source](../../../../../../src/learnloop/teacher/service.py), line 131) — The model clients one ``lesson.turn`` may use: the teacher's and the grader's (resolved lazily), and (Reader RW5d P4b) the host's figure builder for the teacher's visuals (None: the host builds no figure, so the lesson offers none and the teacher's prompt is TE1's).
- `class LessonState` ([source](../../../../../../src/learnloop/teacher/service.py), line 150)
  - `lesson_id(self) -> str` (line 176; public)
  - `capabilities(self) -> Capabilities` (line 180; public)
  - `closed(self) -> bool` (line 184; public)
  - `los(self) -> list[str]` (line 188; public)
  - `node_lo(self, node_id: str | None, *, outline: Sequence[Mapping[str, Any]] | None=None) -> str | None` (line 193; public) — The node's LO: its ``lo_id`` in ``outline`` (default: the latest stored plan), else the node as a brief LO, else the goal's first LO (TE1's rule).
- `load_state(repository: Any, lesson_id: str) -> LessonState` ([source](../../../../../../src/learnloop/teacher/service.py), line 210)
- `transcript(state: LessonState) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/service.py), line 276) — Every step so far, in order, as the teacher reads it (its own turns, the learner's words, results).
- `protection_changed(vault: Any, repository: Any, state: LessonState) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 369) — Whether the lesson must end before its next teacher call (ruling R1): the vault's protection state differs from the one recorded when the brief was built, it cannot be read, or a passage the lesson delivered is no longer teachable (its reading left the library, or it became prot…
- `wire_model(allowed: Capabilities) -> type[TeacherTurnV1]` ([source](../../../../../../src/learnloop/teacher/service.py), line 517) — The provider schema whose identity the recorded lesson capabilities select.
- `submission(repository: Any, state: LessonState, ref: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 727) — The answer submitted to a check or probe that no grade has recorded yet (saved before its grader is called).
- `open_lesson(vault: Any, repository: Any, *, entry: str, learning_object_ids: Sequence[str]=(), selection: Mapping[str, Any] | None=None, goal_text: str | None=None, clients: Clients, driver: str='desktop', clock: Clock | None=None, origin: str='learner_pick', origin_ref: str | None=None, lesson_id: str | None=None, add_topics: Sequence[str]=(), subject_id: str | None=None, preference_id: str | None=None, probe_episode_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 838) — Open a lesson the learner started (TE1: an LO's or a Reader selection's "Teach me this"; TE1b: the Start of a router suggestion, ``origin = 'router'`` with the decision id and the lesson id its response recorded), build its brief from the ledger and run the teacher's first turn.
- `recover(vault: Any, repository: Any, state: LessonState, *, clock: Clock | None=None, reads: bool=True, builder: V.Builder | None=None, resolver: Callable[[], Any] | None=None) -> '_Outcome | None'` ([source](../../../../../../src/learnloop/teacher/service.py), line 993) — Run what an interrupted action left of its last accepted teacher turn (review F9): each effect the ledger does not mark done, idempotently, with its reads' results riding with the next call.
- `view_lesson(vault: Any, repository: Any, lesson_id: str, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1112) — ``lesson.view``: the lesson as the screen shows it, after recovering an interrupted action's remaining effects (no model call).
- `take_turn(vault: Any, repository: Any, *, lesson_id: str, action: str, payload: Mapping[str, Any], clients: Clients, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1122) — One learner action on an open lesson (``reply``, ``answer_prediction``, ``answer_check``, ``stop``), or ``resume``: run the teacher's turn an outage interrupted (nothing new from the learner).
- `awaiting_teacher(state: LessonState) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 1188) — A recorded step waits for the teacher (a reply, an answer's result, a read's follow-up): the lesson's ``resume`` answers it (Continue after a restart sends it, nothing is retyped).
- `retry_kind(repository: Any, lesson_id: str) -> str` ([source](../../../../../../src/learnloop/teacher/service.py), line 1197) — What *Try again* does after a failed action: ``resume`` when the lesson recorded a step that waits for the teacher (or an accepted turn whose effects did not all run), else ``repeat``: nothing of the failed action was recorded (an Add whose topic check failed before the learner'…
- `located(field: str, indices: Sequence[int]) -> str` ([source](../../../../../../src/learnloop/teacher/service.py), line 2105) — ``check.anchors[0], check.anchors[2]``: a refusal's fields by location (landing ruling R1 (b)).
- `displayed_texts(state: LessonState, *, extra: Sequence[str]=()) -> list[str]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2852) — Everything the lesson displayed to the learner so far (accepted turns' fields), and ``extra``.
- `view(vault: Any, repository: Any, lesson_id: str, *, outcome: _Outcome | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 3116) — The lesson as the screen shows it: what was shown, in order, the plan map, the open check (never its solution), the open prediction, and the close card.
- `open_lessons(vault: Any, repository: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/service.py), line 3295) — Teacher TE2 (§11.8): Today's *Continue your lesson on X*, newest first: every open lesson with its topic in plain words.

### Module constants

- `MAX_CONTRACT_FAILURES` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 99)
- `TEACHER_PURPOSE` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 100)
- `LEARNER_ACTIONS` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 101)
- `TE2_LEARNER_ACTIONS` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 104)
- `LEARNER_TEXT_ACTIONS` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 106)
- `LIBRARY_LOOKUP` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 108)
- `PROTECTION_CHANGED_NOTICE` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 366)
- `SUBMISSION_PURPOSE` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 720)
- `METERED_SETTINGS_LINE` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 787)
- `_CALLS_TEACHER` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 1028)
- `_TE2_CALLS_TEACHER` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 1032)
- `_TE2_RETIREMENTS_CALLING_TEACHER` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 1033)
- `TEACHER_MESSAGE_CONTRACT` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 1865)
- `TURN_CHECKPOINT_PURPOSE` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 1885)
- `EXPOSURE_KEY` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 2177)
- `_FIGURE_WITHHELD` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 2512)
- `SHOWN_WITHHELD` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 3044)
- `SHOWN_UNCHECKED` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 3046)
- `_SHOWN_FIELDS` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 3048)
- `_TE2_FEED` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 3236)
- `UNASSESSED_NOTE` ([src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py), line 3240)

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

- `_model_result(result: Any) -> Any` ([source](../../../../../../src/learnloop/teacher/service.py), line 268) — An action's result as the teacher reads it (the alias bookkeeping stays with code).
- `_te2_transcript_entry(entry: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 339) — A TE2 step as the teacher reads it (a probe's, a filed gap, an added topic), or None for TE1's steps.
- `_end_for_protection(vault: Any, repository: Any, state: LessonState, *, clock: Clock | None, outcome: '_Outcome') -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 392)
- `_prompt(state: LessonState, *, results: Sequence[Mapping[str, Any]], help_reply: bool, visuals: bool=False, episodes: bool=False, te2: bool=False, goal_topics: bool=False, history: list[dict[str, Any]] | None=None) -> str` ([source](../../../../../../src/learnloop/teacher/service.py), line 398)
- `_prompt_version(visuals: bool, episodes: bool, te2: bool, goal_topics: bool=False) -> str` ([source](../../../../../../src/learnloop/teacher/service.py), line 424)
- `_limited_prompt(vault: Any, repository: Any, state: LessonState, client: Any, limit: int, fields: Mapping[str, Any]) -> tuple[str, C.Projection, int | None]` ([source](../../../../../../src/learnloop/teacher/service.py), line 428) — The prompt to send, its projection, and the request gate's estimate of the prompt sent (recorded on its receipt for the next forecast).
- `_te2_now(vault: Any, state: LessonState) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 460) — TE2 serves this lesson now: it was opened under TE2 (its brief) and lessons are on now.
- `_append(repository: Any, state: LessonState, *, actor: str, action: str, validation: str='ok', refs: Mapping[str, Any] | None=None, payload: Any=None, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 471)
- `_effect_refs(turn_entry: Mapping[str, Any] | None, effect: str, extra: Mapping[str, Any] | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 484) — The refs marking one effect of an accepted teacher turn (recovery skips what is marked).
- `_model_name(client: Any) -> str | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 494)
- `_family_of(model: str | None, *, visuals: bool=False, episodes: bool=False, te2: bool=False, goal_topics: bool=False) -> str` ([source](../../../../../../src/learnloop/teacher/service.py), line 498) — The forecaster of §12.2's pool: the doctrine version and the teacher model.
- `_turn_flags(turn_entry: Mapping[str, Any] | None) -> dict[str, bool]` ([source](../../../../../../src/learnloop/teacher/service.py), line 509) — The paragraphs a stored turn was written under (its family and prompt version follow them).
- `_stored_turn(entry: Mapping[str, Any]) -> TeacherTurnV2` ([source](../../../../../../src/learnloop/teacher/service.py), line 523)
- `_recovery_turn(entry: Mapping[str, Any]) -> TeacherTurnV2` ([source](../../../../../../src/learnloop/teacher/service.py), line 532)
- `_family(client: Any) -> str` ([source](../../../../../../src/learnloop/teacher/service.py), line 543)
- `_subscription(config: Any, client: Any) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 552)
- `_spent_usd(state: LessonState) -> float` ([source](../../../../../../src/learnloop/teacher/service.py), line 561) — What the lesson's metered requests cost so far: each settled request's ``spend`` row, and each reservation no settlement replaced at its whole estimate (re-review F1: a request sent before the process died may have been charged, so its reservation stands, as for a request that r…
- `_lesson_tokens(state: LessonState, outcome: '_Outcome') -> dict[str, int]` ([source](../../../../../../src/learnloop/teacher/service.py), line 578) — The whole lesson's teacher calls and tokens (every action's ``usage`` row, and this action's).
- `_spend_gate_class() -> type` ([source](../../../../../../src/learnloop/teacher/service.py), line 591)
- `_lesson_spend(vault: Any, repository: Any, state: LessonState, *, clock: Clock | None) -> Iterator[Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 654) — Hold the lesson's spend gate over one action (every model request it makes).
- `_refused_by_budget(state: LessonState, exc: BaseException) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 677)
- `_budget_notice(state: LessonState, outcome: '_Outcome') -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 688) — A lesson closed because a metered request had no spending limit to be held to says so in plain words.
- `_record_budget_close(repository: Any, state: LessonState, exc: BaseException) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 696) — The refusal that closes the lesson with ``budget``, as a ``spend_admission`` record (refactor B8): the close receipt says only ``budget``, and the gate's refusal (which request, its estimate, the limit) was kept nowhere.
- `_answer_turn(turns: Sequence[Mapping[str, Any]], action: str, key: str, ref: str, answer: str | None=None) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 709) — The learner's answer turn already recorded for one check (``check_ref``) or probe (``probe_ref``), or None; with ``answer``, only one recording that exact text (an edited answer is its own revision).
- `_submission_key(state: LessonState, ref: str) -> str` ([source](../../../../../../src/learnloop/teacher/service.py), line 723)
- `_save_submission(repository: Any, state: LessonState, ref: str, record: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 734)
- `_shown_submission(repository: Any, state: LessonState, ref: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 743)
- `_drop_submission(repository: Any, state: LessonState, ref: str) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 748)
- `_bound_attempt(repository: Any, state: LessonState, action: str, key: str, ref: str, answer: str) -> str` ([source](../../../../../../src/learnloop/teacher/service.py), line 752) — The attempt id ``answer`` is graded under: a saved submission's or a stranded answer turn's of the same text whose attempt is not recorded yet, else a new one.
- `_close_for_budget_keeping_answer(vault: Any, repository: Any, state: LessonState, exc: BaseException, *, action: str, key: str, ref: str, refs: Mapping[str, Any], answer: Mapping[str, Any], clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 765) — The lesson's envelope refused the grader's request for an answer (§17): the lesson closes with ``budget`` and the learner's submitted text is kept, once per check or probe, as its answer turn marked unassessed, in the close's own transaction (the closed question cannot be answer…
- `_metered_ready(vault: Any, client: Any) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 791) — A metered client may be sent a lesson's request: the lesson's price and per-lesson cap are both set (a subscription client needs neither; the tests' doubles, provider type ``fake``, are exempt as before).
- `_require_metered_settings(vault: Any, client: Any) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 801) — A metered (OpenRouter) lesson needs its price and its per-lesson cap first (T1 redesign D; Q7): the teacher's route is checked before its first call; every other request (the grader's) meets the same rule at the gate.
- `_accepted_suggestion(repository: Any, decision_id: str | None, lesson_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 814) — The learner's Start on a router suggestion (TE1b, spec §15.1): its recorded response names the lesson id and the LOs, so a lesson with origin ``router`` opens only on a response the learner gave.
- `_record_goal_los(vault: Any, repository: Any, lesson_id: str, created: Sequence[Mapping[str, Any]], *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 971) — TE2 (§11.5): one ``goal_lo`` ledger entry and one ``goal_lo`` episode row per topic the typed goal added.
- `_turn_model(state: LessonState, entry: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1017) — The model that produced an accepted turn: recorded on the turn; a turn accepted before it names none, and its lesson's opening model stands in (the only identity it kept).
- `_boundary(entry: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 1036) — Whether a ledger step waits for a teacher call (it starts an action's calls).
- `class _PendingCall` ([source](../../../../../../src/learnloop/teacher/service.py), line 1049) — The teacher call an interrupted action still owes (``resume`` runs it), with the mode it had.
- `_pending_call(state: LessonState) -> _PendingCall | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1059) — The call the ledger still waits for, read from the ledger itself (so it survives a restart and clears only when the consuming teacher turn commits): a learner's or code's step with no accepted teacher turn after it, with the help mode its reply recorded (re-review F15); or an ac…
- `_owes_followup(state: LessonState, accepted: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 1093) — Whether ``accepted`` is the first accepted turn of its action, asked for reads, and they ran: its reads' results are owed one further call (the structural bound of :func:`_teach_loop`).
- `_learner_action(vault: Any, repository: Any, state: LessonState, action: str, payload: Mapping[str, Any], *, clients: Clients, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1210)
- `_topic_decision(vault: Any, repository: Any, state: LessonState, verb: str, offer: Mapping[str, Any], *, clients: Clients, clock: Clock | None, command: str='') -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1270)
- `_published(vault: Any, state: LessonState, offer: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 1326) — Whether this request already wrote its topic (the writer records the lesson as its goal and the learner's phrase in the LO's provenance): finishing it only synchronizes; a request that wrote nothing must check the catalog again first.
- `_finish_topic_requests(vault: Any, repository: Any, state: LessonState, *, clock: Clock | None, resolver: Callable[[], Any] | None=None, recheck: bool=True) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 1342) — Finish durable learner decisions.
- `_record_help(repository: Any, state: LessonState, text: str, *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1391) — Help while a check is open (§12): one ``help_assists`` row (surface ``tutor``); never evidence.
- `_answer_check(vault: Any, repository: Any, state: LessonState, payload: Mapping[str, Any], *, clients: Clients, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1409)
- `_answer_probe(vault: Any, repository: Any, state: LessonState, payload: Mapping[str, Any], *, clients: Clients, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1521) — TE2 (§11.3): the learner's answer to the open probe, graded blind (the answer only), recorded as a ``diagnostic_probe`` attempt with the attempt id its forecast is bound to; then the teacher reads the result.
- `_latest_forecast(state: LessonState, kind: str, ref: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1562)
- `_update_weight_state(vault: Any, repository: Any) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1570) — Refresh the DERIVED weight tables after a check (the replayer's own function and bound: through the latest answered check, so a rebuild reproduces them row for row).
- `class _Outcome` ([source](../../../../../../src/learnloop/teacher/service.py), line 1586)
- `_teach(vault: Any, repository: Any, state: LessonState, *, clients: Clients, client: Any, help_reply: bool, clock: Clock | None, closing: str | None=None, followup: bool=False, results: Sequence[Mapping[str, Any]]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1598)
- `_teach_loop(vault: Any, repository: Any, state: LessonState, *, client: Any, help_reply: bool, clock: Clock | None, closing: str | None, outcome: '_Outcome', followup: bool=False, followup_results: Sequence[Mapping[str, Any]]=(), builder: V.Builder | None=None, resolver: Callable[[], Any] | None=None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1619)
- `_record_usage(client: Any, outcome: _Outcome) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1690)
- `_displayed(turn_obj: TeacherTurnV1) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1698) — Every learner-facing text of a turn, by field (review F3): the message and its choices, a prediction, a check, plan statements (the map) and a close's recap.
- `_logged(state: LessonState, turn_obj: TeacherTurnV1) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1722) — The model's fields a log row, a receipt or a note's payload copies, never shown, by location, on every turn (TE1's included, with ``teacher.episode_log`` off): the plan nodes' ids and ``lo_id`` (they reach the lesson receipt's ``nodes`` and, on, the episode rows), the posed chec…
- `_check_solution_fields(turn_obj: TeacherTurnV1) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1746) — The posed check's committed solution and rubric facts, by location (they become its vault item: ``checks.mint_check_item``).
- `_outline_at(state: LessonState, turn_obj: TeacherTurnV1, index: int) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1758) — The plan in force when request ``index`` runs: the last ``write_plan`` before it in the turn, else the latest stored plan (``_execute`` stores each plan before the next request runs).
- `_check_outline(state: LessonState, turn_obj: TeacherTurnV1) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1769) — The plan a check this turn poses is read against: the turn's own last plan when it writes one (the plan the lesson holds once the turn has run, the one the close's delayed checks read), else the stored plan.
- `_copies_node(state: LessonState, turn_obj: TeacherTurnV1, request: ActionRequestV1) -> bool` ([source](../../../../../../src/learnloop/teacher/service.py), line 1777) — Whether :func:`_forecast` copies the request's node into its receipt's key and inputs: every forecast but a check forecast with a check open or posed in the turn (its receipt names the check's ref, code-made).
- `_forecast_lo(state: LessonState, turn_obj: TeacherTurnV1, index: int, request: ActionRequestV1) -> str | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1785) — The LO :func:`_forecast` copies into request ``index``'s receipt (ruling R2: guarded before the turn is accepted): for a check forecast, the open check's (one this turn poses included), else the node's.
- `_field_names(model: type[Any]) -> frozenset[str]` ([source](../../../../../../src/learnloop/teacher/service.py), line 1802) — Every field name of a turn schema and the models it nests (a schema refusal's location names these only).
- `_schema_detail(exc: BaseException, model: type[Any]) -> str` ([source](../../../../../../src/learnloop/teacher/service.py), line 1828) — A schema refusal as the teacher reads it (TE2-log landing, ruling R1 (b)): each failing field by its location (``requests[0].node``) and pydantic's message, never its input, so no untrusted text (an over-long node id carrying protected words) enters the transcript before the gua…
- `class _BlankTeacherTurn(Exception)` ([source](../../../../../../src/learnloop/teacher/service.py), line 1861) — A rejected blank returns to the existing consecutive-failure policy.
- `_teacher_contract_failure(info: ContractFailure) -> Exception` ([source](../../../../../../src/learnloop/teacher/service.py), line 1871)
- `_turn_checkpoint(repository: Any, state: LessonState, client: Any, model: type, prompt: str) -> Any` ([source](../../../../../../src/learnloop/teacher/service.py), line 1888) — The slot a teacher's answer is saved in the moment it passes its contract, under the request's identity (the lesson, the producing model and the exact first prompt, whose prompt version names the schema), before the turn is guarded and recorded: a crash in between reuses it on r…
- `_request_teacher_turn(vault: Any, repository: Any, state: LessonState, client: Any, *, prompt: str, model: type, outcome: _Outcome, clock: Clock | None, sending: Callable[[str], None] | None=None, checkpoint: Any=None) -> Any` ([source](../../../../../../src/learnloop/teacher/service.py), line 1901) — ``sending``: told each prompt actually sent (the first, then a correction's) at its request start, before its receipt opens.
- `_call_teacher(vault: Any, repository: Any, state: LessonState, client: Any, *, results: Sequence[Mapping[str, Any]], help_reply: bool, outcome: _Outcome, clock: Clock | None, allowed: Capabilities, deliver: Sequence[str]=()) -> tuple[TeacherTurnV2, dict[str, Any]] | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 1953) — One teacher call: validated, guarded, recorded.
- `_contract_problem(state: LessonState, turn_obj: TeacherTurnV1, *, vault: Any=None) -> str | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 2111) — A correctable contract problem, or None.
- `_record_reveals(vault: Any, repository: Any, state: LessonState, message: str, *, clock: Clock | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2181) — Teaching text and cited passages (§12): ``tutor_answer`` for each item on the lesson's LOs whose key the text overlaps (amount = overlap, as the tutor), ``source_review`` for what a cited passage exposes; basis ``lesson:<id>``.
- `_withdraw(vault: Any, repository: Any, state: LessonState, *, overlap: float, clock: Clock | None, outcome: _Outcome, turn_entry: Mapping[str, Any] | None=None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 2224)
- `_execute(vault: Any, repository: Any, state: LessonState, turn_obj: TeacherTurnV2, *, turn_entry: Mapping[str, Any], model: str | None, deferred: bool, outcome: _Outcome, clock: Clock | None, help_reply: bool, done: set[str] | frozenset[str]=frozenset(), reads: bool=True, builder: V.Builder | None=None, resolver: Callable[[], Any] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2248) — An accepted turn's effects, in order, each marked with the turn and its name (``refs.effect``) in the transaction that makes it, then a ``turn_executed`` marker: recovery runs only what is unmarked (``done``), so an interrupted action resumes idempotently (review F9).
- `_record_read(vault: Any, repository: Any, state: LessonState, request: ActionRequestV1, *, model: str | None, clock: Clock | None, turn_entry: Mapping[str, Any], effect: str, deferred: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2341)
- `_write_plan(vault: Any, repository: Any, state: LessonState, turn_obj: TeacherTurnV2, request: ActionRequestV1, *, model: str | None, clock: Clock | None, turn_entry: Mapping[str, Any], effect: str) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 2354)
- `_note_detour(vault: Any, repository: Any, state: LessonState, turn_obj: TeacherTurnV1, request: ActionRequestV1, *, turn_entry: Mapping[str, Any] | None, effect: str, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 2370) — ``note_detour`` (§11.7): the hypothesis in the turn's payload (a ``note_detour`` entry, marked as the turn's effect) and one ``detour`` episode row, its own savepoint (a refused row rolls back alone, with a warning).
- `_serve_probe(vault: Any, repository: Any, state: LessonState, turn_obj: TeacherTurnV1, request: ActionRequestV1, *, turn_entry: Mapping[str, Any] | None, effect: str, model: str | None, outcome: '_Outcome', clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 2395) — ``serve_probe`` (§11.3): its ledger entry, the ``lesson_probe_correct`` receipt (before any serve), FG1's generation job and the probe's episode row, in one transaction marked as the turn's effect.
- `_learner_turn(state: LessonState, ref: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 2418) — The learner's turn a transcript ``ref`` (``t<seq>``) names, or None.
- `_gap_problem(state: LessonState, index: int, request: ActionRequestV1) -> str | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 2427)
- `_gap_learning_object(state: LessonState, learner: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 2437) — The LO a gap is about: the check's, when the learner's words answered one; else the lesson's first topic.
- `_propose_gap(vault: Any, repository: Any, state: LessonState, request: ActionRequestV1, *, turn_entry: Mapping[str, Any] | None, effect: str, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 2454) — ``propose_gap`` (§11.7): the learner's words to the text-gap pipeline with ``source_kind = 'lesson'`` (its ``propose_gap`` entry is the source; the pipeline reads the learner's turn it names, the teacher's words as the context model's reading) and one ``gap`` episode row.
- `_plan_episodes(vault: Any, repository: Any, state: LessonState, turn_obj: TeacherTurnV1, outline: Sequence[Mapping[str, Any]], previous: Sequence[Mapping[str, Any]] | None, *, version: int, entry: Mapping[str, Any], model: str | None, turn_entry: Mapping[str, Any] | None, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 2483) — A stored plan's TE2-log rows: a ``lesson_node_held`` forecast receipt per node with ``p_held`` (§11.3; each receipt its own savepoint, so a refused one leaves its siblings: Codex review F2), and an ``unlogged`` detour when it inserts a node before ones the previous plan had and…
- `_visual(vault: Any, repository: Any, state: LessonState, turn_obj: TeacherTurnV1, *, builder: V.Builder | None, outcome: _Outcome, clock: Clock | None, turn_entry: Mapping[str, Any]) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 2518) — Reader RW5d P4b: build the turn's visual and record it.
- `_figure_entry(vault: Any, repository: Any, record: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2569) — A lesson figure as the feed shows it (Reader RW5d P4b): its view NOW, with no predictions.
- `_pose_check(vault: Any, repository: Any, state: LessonState, check: CheckV1, *, outcome: _Outcome, clock: Clock | None, turn_entry: Mapping[str, Any] | None=None, outline: Sequence[Mapping[str, Any]] | None=None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 2582)
- `_read_action(vault: Any, repository: Any, state: LessonState, request: ActionRequestV1, *, model: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2603)
- `_forecast(vault: Any, repository: Any, state: LessonState, request: ActionRequestV1, *, model: str | None, clock: Clock | None, turn_entry: Mapping[str, Any] | None=None, effect: str='forecast') -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 2613)
- `_close(vault: Any, repository: Any, state: LessonState, *, reason: str, recap: str | None, clock: Clock | None, outcome: _Outcome, turn_entry: Mapping[str, Any] | None=None, effect: str='close') -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 2693) — Close the lesson: commit the delayed checks, write the receipt, close the row and append the close entry in one transaction (§7 step 7; review F9: never a closed row without its close entry).
- `_close_te2(vault: Any, repository: Any, state: LessonState, *, closed_at: str, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 2759) — At a TE2 lesson's close: every unanswered probe retired unused (reason ``lesson_closed``); each gap episode closed with the pipeline's result so far (``resolved`` with its action, else ``lesson_closed`` pending); each added topic's episode closed with its LO's undo state.
- `_receipt_te2_fields(repository: Any, state: LessonState) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2793) — A TE2 lesson's receipt additions (§8.3): its probes (status, item, attempt, grade, independence, the refusal reason), its filed gaps and the topics it added (``gaps``, ``created_los``); {} for any other lesson.
- `_landed_before(state: Any, node_id: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2824) — The nodes whose retention checks the commitment allocates before ``node_id``'s, as of now (FR3-15): the landed nodes in landing order (``_close``'s), up to this node, or all of them when it has not landed yet (it is then committed after them).
- `_lesson_shown(vault: Any, state: LessonState) -> list[str]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2834) — The lesson's own check items and the vault items its displayed text reproduced so far.
- `_taught(state: LessonState) -> list[str]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2842) — What the lesson showed so far, its words and the passages they cited (a later question's answer is measured against them).
- `_receipt(vault: Any, repository: Any, state: LessonState, *, reason: str, recap: str | None, delayed_checks: Sequence[Mapping[str, Any]], warnings: Sequence[str], landed: Sequence[Mapping[str, Any]], rows: Sequence[Mapping[str, Any]], usage: Mapping[str, int], shown_items: Sequence[str]=(), closed_at: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2868) — ``LessonReceiptV1`` (§8.3).
- `_passage_readings(book: SourceBook) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2956) — ``exposure.readings``: ``{alias, extraction_id, span_id}`` per delivered passage, in alias order (no text).
- `_receipt_identities(vault: Any, state: LessonState, item_ids: Sequence[Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2963) — ``{"identities": ...}`` for the receipt's exposure (landing ruling R1): the union of the identities frozen on each displayed record when it was shown (:data:`EXPOSURE_KEY`: an accepted turn, a shown figure, a served probe's question) and the close's own (the recap; every item th…
- `_receipt_episode_fields(vault: Any, repository: Any, state: LessonState, *, closed_at: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/teacher/service.py), line 2988) — §8.3's ``episodes`` (the lesson's episode ids by kind) and ``minutes`` (active and elapsed, and their source; never blended), and the ``lesson_node_held`` receipt keys; ``{}`` while ``teacher.episode_log`` is off.
- `_stability_inputs(repository: Any, landed: Sequence[Mapping[str, Any]], rows: Sequence[Mapping[str, Any]], state: LessonState) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/teacher/service.py), line 3009) — Per landed node, the liquid-stability inputs ``u`` (§8.3; logged before the family activates).
- `class _DisplayScreen` ([source](../../../../../../src/learnloop/teacher/service.py), line 3051) — Today's protection over a lesson's saved words as the screen shows them: a string that quotes a question kept for an exam or held out (``quotes_reserved``, the one predicate) or cites a delivered passage that is no longer teachable is replaced in plain words.
- `_unassessed_note(data: Mapping[str, Any]) -> dict[str, str]` ([source](../../../../../../src/learnloop/teacher/service.py), line 3243)
- `_te2_feed_entry(vault: Any, action: str, data: Mapping[str, Any], *, answered: set[str], closed: bool) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/teacher/service.py), line 3247) — A TE2 turn as the feed shows it, in place (the question as the item states it: nothing is generated again).
- `_view_te2(vault: Any, repository: Any, state: LessonState, out: dict[str, Any], *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/teacher/service.py), line 3267) — A TE2 lesson's view additions: the probe card (*Preparing a question on this…* with *Teach it anyway*, or the open question, served now through FG1's first-serve claim: the question only, never its key), its results in the feed, and the topics the lesson added.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `load_state`; statically calls `load_state`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `lessons_active`; statically calls `lessons_active`
- [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]] — imports `module`; statically calls `Clients`, `lessons_active`, `open_lesson`, `open_lessons`, `require_active`, `retry_kind`, `take_turn`, `view_lesson`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIOutputTruncated`, `AIProviderUnavailable`, `AITurnTimeout`; calls `AIInterrupted`, `AIInvalidOutput`, `AITurnTimeout`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `ModelCheckpoint`, `active_request_gate`, `content_key`, `gate_model_requests`, `generation_ceiling`; calls `ModelCheckpoint`, `active_request_gate`, `content_key`, `gate_model_requests`, `generation_ceiling`
- [[Reference/Modules/learnloop/ai/output_budget|learnloop.ai.output_budget]] — imports `output_budget`; calls `output_budget`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `MeteredRequestGate`, `SpendLimitExceeded`, `is_subscription_transport`; calls `SpendLimitExceeded`, `is_subscription_transport`
- [[Reference/Modules/learnloop/ai/structured_contracts|learnloop.ai.structured_contracts]] — imports `ContractFailure`, `ContractRejected`, `Predicate`, `RecoveryAllowance`, `checked_structured_call`; calls `Predicate`, `RecoveryAllowance`, `checked_structured_call`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `execute_structured_operation`, `render_structured_prompt`; calls `execute_structured_operation`, `render_structured_prompt`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `record_reveal_strict`; calls `record_reveal_strict`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `FrozenClock`, `parse_utc`, `utc_now_iso`; calls `FrozenClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] — imports `insert_assist`; calls `insert_assist`
- [[Reference/Modules/learnloop/db/stores/lessons|learnloop.db.stores.lessons]] — imports `module`; calls `append_turn`, `checks`, `close_lesson`, `episode_tables_present`, `episodes`, `insert_lesson`, `insert_plan`, `insert_receipt`, `lesson`, `plans`, `turns`
- [[Reference/Modules/learnloop/db/stores/router_suggestions|learnloop.db.stores.router_suggestions]] — imports `module`; calls `lesson_exists`, `release_for`, `response_for`, `tables_present`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/jobs|learnloop.diagnosis.text_gaps.jobs]] — imports `enqueue_lesson_gap`, `pipeline_enabled`; calls `enqueue_lesson_gap`, `pipeline_enabled`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]] — imports `predicted_success`, `replay_state`, `tables_through`, `write_state`; calls `predicted_success`, `replay_state`, `tables_through`, `write_state`
- [[Reference/Modules/learnloop/refusal_records|learnloop.refusal_records]] — imports `module`; calls `lesson_budget_record`, `write`
- [[Reference/Modules/learnloop/scheduling/forecast_receipts|learnloop.scheduling.forecast_receipts]] — imports `ForecastReceipt`, `LESSON_CHECK_ATTEMPT`, `LESSON_COLD_OUTCOME`, `record_receipts`; calls `ForecastReceipt`, `record_receipts`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `AUTO_PRIME_REVEAL_THRESHOLD`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `CoverageError`, `Library`; calls `Library`
- [[Reference/Modules/learnloop/teacher/actions|learnloop.teacher.actions]] — imports `caller_for`, `module`, `resolve_offer`; calls `caller_for`, `resolve_offer`, `run_read`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `LessonRefused`, `SourceBook`, `build_brief`, `lo_prediction`, `passage_teachable`, `protection_state`, `resolve_goal`, `revoke_unteachable`; calls `build_brief`, `lo_prediction`, `passage_teachable`, `protection_state`, `resolve_goal`, `revoke_unteachable`
- [[Reference/Modules/learnloop/teacher/carried|learnloop.teacher.carried]] — imports `module`; calls `in_brief`, `instructions`, `prompt_version`
- [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]] — imports `module`; calls `check_mass`, `cold_reference`, `grade_answer`, `lesson_item`, `mint_check_item`, `prepare_check_attempt`, `record_answered_check`, `withdraw_check`
- [[Reference/Modules/learnloop/teacher/compaction|learnloop.teacher.compaction]] — imports `module`; calls `Projection`, `context_limit`, `decision`, `forecast`, `latest`, `recent_start`, `record_requests`, `summarize`
- [[Reference/Modules/learnloop/teacher/contracts|learnloop.teacher.contracts]] — imports `ActionRequestV1`, `Capabilities`, `CheckV1`, `CreateGoalLo`, `READ_ACTIONS`, `RECEIPT_VERSION`, `TURN_VERSION`, `TeacherTurnV1`, `TeacherTurnV2`, `capabilities`, `lesson_capabilities`, `parse_turn`; calls `ActionRequestV1`, `CreateGoalLo`, `capabilities`, `lesson_capabilities`, `parse_turn`
- [[Reference/Modules/learnloop/teacher/delayed|learnloop.teacher.delayed]] — imports `module`; calls `commit_checks`, `shown_vault_items`
- [[Reference/Modules/learnloop/teacher/diagnosed_sources|learnloop.teacher.diagnosed_sources]] — imports `module`; calls `consumed_preference`
- [[Reference/Modules/learnloop/teacher/doctrines|learnloop.teacher.doctrines]] — imports `DOCTRINE_VERSION`, `doctrine_identity`, `doctrine_text`; calls `doctrine_identity`, `doctrine_text`
- [[Reference/Modules/learnloop/teacher/episodes|learnloop.teacher.episodes]] — imports `module`; calls `close_episodes`, `close_one`, `doctrine_family`, `has_table`, `inserted_nodes`, `instructions`, `lesson_minutes`, `logged_fields`, `node_held_receipts`, `node_known`, `node_lo`, `on`, `open_episode`, `outline_lo`, `prompt_version`, `receipt_episodes`, `turn_model`
- [[Reference/Modules/learnloop/teacher/exposure|learnloop.teacher.exposure]] — imports `module`
- [[Reference/Modules/learnloop/teacher/from_check|learnloop.teacher.from_check]] — imports `from_check`; calls `from_check`
- [[Reference/Modules/learnloop/teacher/guards|learnloop.teacher.guards]] — imports `module`; calls `GuardVerdict`, `check_all`, `cited_aliases`, `key_guard`, `key_sets`, `lesson_keys`, `open_check_guard`, `quotes_reserved`, `reserved_book`, `reserved_guard`, `screen_context`, `shown_feedback`, `solution_overlap`
- [[Reference/Modules/learnloop/teacher/notes|learnloop.teacher.notes]] — imports `notes_still_deliverable`, `your_notes`
- [[Reference/Modules/learnloop/teacher/probes|learnloop.teacher.probes]] — imports `module`; calls `contract_problem`, `finish_recorded`, `logged_fields`, `open_probe`, `probes`, `record_answer`, `request`, `retire`, `serve`, `serving_held`, `transcript_entry`, `unanswered`
- [[Reference/Modules/learnloop/teacher/te2|learnloop.teacher.te2]] — imports `module`; calls `doctrine_family`, `instructions`, `learner_ref`, `lesson_te2`, `on`, `prompt_version`, `stored_turn`, `turn_model`
- [[Reference/Modules/learnloop/teacher/topics|learnloop.teacher.topics]] — imports `module`; calls `create_offered_topic`, `offer_decision`, `offer_text`, `plan_open`, `proposal_text`
- [[Reference/Modules/learnloop/teacher/visuals|learnloop.teacher.visuals]] — imports `module`; calls `active`, `build`, `contract_problem`, `displayed`, `figure_row`, `figure_text`, `instructions`, `lesson_view`, `not_built_for_protection`, `on`, `prompt_version`, `resolve`, `summary`, `turn_model`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `answer_leak_overlap`, `span_answer_overlap`; calls `answer_leak_overlap`, `span_answer_overlap`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `hashlib`, `json`, `pathlib`, `time`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/lesson|learnloop_sidecar.handlers.lesson]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/figures_prefetch_review_fixes_helpers.py](../../../../../../tests/figures_prefetch_review_fixes_helpers.py) — direct import
- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/live_dialogue_contract_helpers.py](../../../../../../tests/live_dialogue_contract_helpers.py) — direct import
- [tests/reader_rw5d_p4b_teacher_visuals_helpers.py](../../../../../../tests/reader_rw5d_p4b_teacher_visuals_helpers.py) — direct import
- [tests/teacher_fakes.py](../../../../../../tests/teacher_fakes.py) — direct import
- [tests/teacher_te1_lesson_helpers.py](../../../../../../tests/teacher_te1_lesson_helpers.py) — direct import
- [tests/teacher_te1_review_fixes_helpers.py](../../../../../../tests/teacher_te1_review_fixes_helpers.py) — direct import
- [tests/teacher_te2_probes_helpers.py](../../../../../../tests/teacher_te2_probes_helpers.py) — direct import
- [tests/teacher_te2log_receipt_helpers.py](../../../../../../tests/teacher_te2log_receipt_helpers.py) — direct import
- [tests/test_data_capture_a6_delayed_pick.py](../../../../../../tests/test_data_capture_a6_delayed_pick.py) — direct import
  - `test_a_nodes_forecast_is_allocated_after_the_nodes_landed_before_it`
- [tests/test_figure_build_golden.py](../../../../../../tests/test_figure_build_golden.py) — direct import
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
- [tests/test_ih7_lesson_sources_follow_diagnosis.py](../../../../../../tests/test_ih7_lesson_sources_follow_diagnosis.py) — direct import
  - `test_a_lesson_the_learner_started_is_unchanged`
  - `test_a_reader_selection_or_a_typed_topic_ignores_a_preference`
  - `test_a_request_not_on_record_consumes_nothing`
  - `test_a_request_opens_one_lesson_and_a_second_opening_is_ignored_and_recorded`
  - `test_over_budget_the_added_section_falls_to_the_outline_and_the_linked_one_stays_whole`
  - `test_switch_off_and_below_the_tag_a_learner_asked_lesson_is_byte_identical`
  - `test_the_learner_asked_lesson_keeps_its_record_in_the_open_turn`
- [tests/test_ih_lesson_candidate_after_cold_miss.py](../../../../../../tests/test_ih_lesson_candidate_after_cold_miss.py) — direct import
  - `test_only_a_miss_since_the_last_lesson_counts`
- [tests/test_lesson_answer_turns.py](../../../../../../tests/test_lesson_answer_turns.py) — direct import
  - `test_a_budget_refused_check_answer_is_saved_unassessed_with_the_close`
  - `test_a_lesson_check_answer_turn_commits_with_its_grade`
  - `test_a_lesson_probe_answer_turn_commits_with_its_grade`
  - `test_a_retry_of_a_stranded_check_answer_turn_appends_no_second`
- [tests/test_lesson_grade_forecast.py](../../../../../../tests/test_lesson_grade_forecast.py) — direct import
  - `test_lesson_forecast_is_prepared_once_outside_the_writer`
  - `test_withdrawal_during_preparation_discards_the_losing_grade`
- [tests/test_lesson_weight_facts.py](../../../../../../tests/test_lesson_weight_facts.py) — direct import
  - `test_a_check_is_stamped_under_the_writer_lock`
- [tests/test_live_dialogue_contract_baseline.py](../../../../../../tests/test_live_dialogue_contract_baseline.py) — direct import
  - `test_initial_deadline_and_cancellation`
- [tests/test_notebook_lessons.py](../../../../../../tests/test_notebook_lessons.py) — direct import
- [tests/test_reader_rd10_fix_sweep.py](../../../../../../tests/test_reader_rd10_fix_sweep.py) — direct import
  - `test_a_lesson_on_a_topic_whose_check_is_due_names_nothing_in_its_tab`
- [tests/test_reader_rd9a_fix.py](../../../../../../tests/test_reader_rd9a_fix.py) — direct import
  - `test_a_quick_question_is_never_served_or_answered_in_a_desk_window`
- [tests/test_reader_rd9a_lesson_windows.py](../../../../../../tests/test_reader_rd9a_lesson_windows.py) — direct import
  - `test_lesson_list_names_each_lesson_with_its_additions_pad`
  - `test_review_replays_a_finished_lesson_with_no_model_call_and_no_write`
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
- [tests/test_te3a_lesson_opportunity.py](../../../../../../tests/test_te3a_lesson_opportunity.py) — direct import
  - `test_codex_f1_the_teachers_close_records_each_delivered_passages_reading`
  - `test_landing_r1_a_probe_lesson_freezes_every_display_and_its_receipt_is_judged_not_failed_closed`
  - `test_landing_r1_an_item_replaced_before_the_close_is_judged_by_the_revision_the_lesson_revealed`
  - `test_landing_r1_the_receipt_unions_frozen_identities_and_a_display_without_them_fails_closed`
- [tests/test_teacher_carried_questions.py](../../../../../../tests/test_teacher_carried_questions.py) — direct import
- [tests/test_teacher_exam_question_guard.py](../../../../../../tests/test_teacher_exam_question_guard.py) — direct import
  - `test_a_lesson_with_no_reserved_text_is_byte_identical_with_the_guard_off`
  - `test_unreadable_protection_fails_closed`
- [tests/test_teacher_from_check.py](../../../../../../tests/test_teacher_from_check.py) — direct import
- [tests/test_teacher_structured_contracts.py](../../../../../../tests/test_teacher_structured_contracts.py) — direct import
  - `test_all_eight_turn_variants_check_inside_receipt`
  - `test_stop_between_blank_and_correction_sends_nothing`
  - `test_three_blanks_close_and_resume_never_resends`
  - `test_two_failed_turns_leave_the_existing_third_slot`
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
  - `test_help_that_gives_the_solution_away_in_a_choice_withdraws_the_check`
  - `test_help_that_gives_the_solution_away_withdraws_the_check_with_no_attempt`
  - `test_help_that_lists_a_multiple_choice_checks_own_options_again_keeps_the_check`
  - `test_read_source_find_sources_find_practice_and_read_history_return_safe_results`
  - `test_switched_off_no_lesson_opens`
  - `test_the_minted_check_item_is_held_to_its_lesson`
  - `test_while_a_check_is_open_its_solution_is_never_shown`
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
  - `test_the_next_lesson_on_the_same_topics_starts_where_the_last_left_off`
  - `test_today_lists_open_lessons_and_close_it_closes_with_no_teacher_call`
  - `test_yes_to_a_leftover_creates_the_topic_with_teacher_goal_v1_and_one_goal_lo_episode`
- [tests/test_teacher_te2_probes.py](../../../../../../tests/test_teacher_te2_probes.py) — direct import
  - `test_a_probe_is_generated_once_served_cold_and_never_again`
- [tests/test_teacher_te2_review_fixes.py](../../../../../../tests/test_teacher_te2_review_fixes.py) — direct import
  - `test_f3_a_fault_after_the_attempt_rolls_everything_back_and_the_answer_can_be_sent_again`
  - `test_f3_a_second_submit_of_an_answered_probe_returns_its_result`
  - `test_f4_resume_after_a_probe_result_whose_teacher_call_never_ran`
  - `test_f4_resume_after_teach_it_anyway_whose_teacher_call_never_ran`
  - `test_f5_a_metered_typed_goal_resolver_is_sent_nothing`
  - `test_f6_today_can_close_a_te1_lesson_left_open_before_te2`
- [tests/test_teacher_te2_sidecar.py](../../../../../../tests/test_teacher_te2_sidecar.py) — direct import
  - `test_lesson_goal_and_open_lessons_through_the_handlers`
- [tests/test_teacher_te2log_activity.py](../../../../../../tests/test_teacher_te2log_activity.py) — direct import
  - `test_an_episodes_minutes_come_from_the_screens_intervals`
- [tests/test_teacher_te2log_episodes.py](../../../../../../tests/test_teacher_te2log_episodes.py) — direct import
  - `test_a_detour_is_one_row_with_item_5s_fields_closed_once_at_its_recheck`
  - `test_a_plan_node_carrying_another_los_reserved_key_is_withheld_by_location`
  - `test_switch_off_keeps_the_lesson_without_the_episode_paragraph`
  - `test_switch_on_offers_the_paragraph_the_schema_and_its_own_forecaster`
  - `test_te1s_forecast_node_is_resolved_and_guarded_with_the_switch_off`
- [tests/test_teacher_te2log_node_held.py](../../../../../../tests/test_teacher_te2log_node_held.py) — direct import
  - `test_each_p_held_is_a_lesson_node_held_forecast_on_its_lo`
- [tests/test_teacher_te2log_report.py](../../../../../../tests/test_teacher_te2log_report.py) — direct import
  - `test_the_pool_weights_trajectory_per_forecaster`
- [tests/test_teacher_te5_compaction.py](../../../../../../tests/test_teacher_te5_compaction.py) — direct import
  - `test_a_correction_receipt_records_its_own_prompt_estimate`
  - `test_a_long_current_reply_after_short_nested_sends_is_forecast`
  - `test_an_accepted_topic_survives_compaction`
  - `test_compacted_correction_records_one_boundary`
  - `test_decision_write_failure_retries_before_any_compacted_send`
  - `test_growth_spread_and_cold_start_are_lesson_local`
  - `test_interrupted_compaction_preserves_evidence_and_replays_receipt`
  - `test_live_boundary_and_predecessor_bytes`
- [tests/test_teacher_te5_contracts.py](../../../../../../tests/test_teacher_te5_contracts.py) — direct import
  - `test_a_lesson_uses_the_capabilities_recorded_at_open`
  - `test_predecessor_prompt_bytes`
  - `test_recovery_keeps_the_predecessors_plan_and_read_payloads`
  - `test_wire_and_union_admit_the_same_inputs`
- [tests/test_teacher_te5_goal_topics.py](../../../../../../tests/test_teacher_te5_goal_topics.py) — direct import
  - `test_consent_rechecks_a_changed_catalog`
  - `test_decline_then_stale_consent_never_creates`
  - `test_guard_precedes_resolver`
  - `test_lookup_consent_replay_and_receipt`
  - `test_pre_offer_schema_and_executor_refuse_new_action`
  - `test_resume_after_yaml_publication_finishes_consent_once`
- [tests/test_teacher_te5_grade_curves.py](../../../../../../tests/test_teacher_te5_grade_curves.py) — direct import
  - `test_pool_only_endpoint_uses_its_snapshot_and_reports_an_unapplied_replacement`
- [tests/test_teacher_te5_review_evidence.py](../../../../../../tests/test_teacher_te5_review_evidence.py) — direct import
  - `test_a_check_on_a_newly_added_topic_credits_that_topic`
  - `test_a_forecast_carries_one_probability_everywhere`
  - `test_a_withdrawn_only_check_writes_no_weight_rows_live_or_rebuilt`
  - `test_teaching_on_an_itemless_topic_makes_a_generated_probe_on_it_dependent`
  - `test_the_live_weight_refresh_commits_with_the_answer`
- [tests/test_teacher_te5_review_protection.py](../../../../../../tests/test_teacher_te5_review_protection.py) — direct import
  - `test_a_passage_protected_after_the_turn_is_withheld_from_every_view`
  - `test_a_question_reserved_after_the_turn_is_withheld_in_the_closing_response`
  - `test_catalog_never_sends_another_topics_protected_summary`
- [tests/test_teacher_te5_review_recovery.py](../../../../../../tests/test_teacher_te5_review_recovery.py) — direct import
  - `test_a_graded_answer_survives_a_crash_and_is_graded_once`
  - `test_a_library_lookup_is_journaled_as_an_action_and_cannot_be_cited_as_learner_text`
  - `test_a_recovered_forecast_names_the_model_that_produced_its_turn`
  - `test_a_teacher_turn_returned_before_a_crash_is_not_bought_again`
  - `test_an_answer_edited_after_a_stranded_one_is_graded_as_its_own_revision`
  - `test_an_edited_answer_refused_by_the_budget_is_saved_as_typed`
  - `test_an_open_lesson_is_read_listed_and_closed_with_lessons_off`
  - `test_an_oversized_catalog_is_noted_and_close_always_works`
  - `test_consent_interrupted_before_publication_rechecks_the_catalog`
  - `test_continue_after_a_restart_answers_a_saved_reply`
  - `test_try_again_after_an_interrupted_add_repeats_the_add`
- [tests/test_teacher_te5_review_spend.py](../../../../../../tests/test_teacher_te5_review_spend.py) — direct import
  - `test_a_budget_refused_answer_says_it_was_saved_and_not_graded`
  - `test_a_metered_grader_with_the_settings_is_reserved_and_settled_into_the_close`
  - `test_a_metered_grader_without_the_lessons_settings_is_never_sent`

## Modification guidance

- Make changes here when the responsibility remains service within learnloop.teacher; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/teacher/service.py](../../../../../../src/learnloop/teacher/service.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.

"""The lesson lifecycle behind ``lesson.turn`` (spec_teacher_v1 §6, §7, §9, §17).

One lesson is one origin action: every model-calling step (open, a learner
reply, a prediction's answer, a check's answer, a stop) goes through
:func:`turn`, so a T1 grant on ``lesson.turn`` covers the whole lesson, and a
check's grading runs inline under the same grant.

**Each learner action** runs one teacher call (``TeacherTurnV1``). When that
turn asks for read actions, they run and their results go back in exactly one
further call; read actions that call asks for run too and their results ride
with the next learner action (a structural bound, no count to choose). A turn
that fails validation or a guard is refused back to the model as correctable;
three consecutive refusals close the lesson with ``teacher_contract_failure``
(``keep``: a contract guardrail, §18.4).

**State** is the lesson ledger itself (``lesson_turns`` and their payloads,
``lesson_plans``, ``lesson_checks``): a lesson resumes after a restart or after
the plan returns.

**Code owns** what enters the model's context (the brief, the delivered
passages, the action results, all through the protection the brief uses), the
guards, grading (the blind grader), evidence and its weight, reveal accounting,
the delayed checks and their dates, caps and receipts. The teacher owns the
pedagogy.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from learnloop.ai.transport import execute_structured_operation, render_structured_prompt
from learnloop.algorithm_versions import TEACHER_VERSIONS
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.stores import lessons as store
from learnloop.ids import new_ulid
from learnloop.teacher import checks as CK
from learnloop.teacher import guards as G
from learnloop.teacher.brief import LessonRefused, SourceBook, build_brief, resolve_goal
from learnloop.teacher.contracts import (
    PROMPT_VERSION,
    READ_ACTIONS,
    RECEIPT_VERSION,
    TURN_VERSION,
    ActionRequestV1,
    CheckV1,
    TeacherTurnV1,
)
from learnloop.teacher.doctrines import DOCTRINE_VERSION, doctrine_identity, doctrine_text

#: Consecutive refused turns that close a lesson (keep: a contract guardrail, spec §18.4).
MAX_CONTRACT_FAILURES = 3
TEACHER_PURPOSE = "teacher_turn"
LEARNER_ACTIONS = ("reply", "answer_prediction", "answer_check", "stop")


class LessonError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def lessons_active(vault: Any) -> bool:
    """A lesson may open: the vault is at the teacher's successor and ``teacher.enabled`` is on."""

    return (vault.config.algorithms.algorithm_version in TEACHER_VERSIONS
            and bool(vault.config.teacher.enabled))


def require_active(vault: Any) -> None:
    if vault.config.algorithms.algorithm_version not in TEACHER_VERSIONS:
        raise LessonError("teacher_unavailable", "Lessons need this vault upgraded (learnloop upgrade).")
    if not vault.config.teacher.enabled:
        raise LessonError("teacher_disabled", "Lessons are switched off (teacher.enabled = false).")


@dataclass
class Clients:
    """The model clients one ``lesson.turn`` may use: the teacher's and the grader's (resolved lazily)."""

    teacher: Callable[[], Any]
    grading: Callable[[], Any]
    grading_source: str = "ai"


# =============================================================================
# State, read back from the ledger
# =============================================================================


@dataclass
class LessonState:
    lesson: dict[str, Any]
    brief: dict[str, Any]
    book: SourceBook
    turns: list[dict[str, Any]]
    checks: list[dict[str, Any]]
    plans: list[dict[str, Any]]
    open_check: dict[str, Any] | None = None
    open_prediction: dict[str, Any] | None = None
    pending_results: list[dict[str, Any]] = field(default_factory=list)
    failures: int = 0
    forecasts: dict[str, dict[str, Any]] = field(default_factory=dict)
    minted: dict[str, str] = field(default_factory=dict)
    landed: list[str] = field(default_factory=list)

    @property
    def lesson_id(self) -> str:
        return str(self.lesson["id"])

    @property
    def closed(self) -> bool:
        return self.lesson.get("closed_at") is not None

    @property
    def los(self) -> list[str]:
        return [node["id"] for node in self.brief.get("nodes") or []]

    def node_lo(self, node_id: str | None) -> str | None:
        if not node_id:
            return None
        plan = self.plans[-1]["outline"] if self.plans else []
        for node in plan:
            if node.get("id") == node_id and node.get("lo_id"):
                return str(node["lo_id"])
        if node_id in self.los:
            return node_id
        goal = (self.brief.get("goal") or {}).get("learning_object_ids") or []
        return str(goal[0]) if goal else None


def load_state(repository: Any, lesson_id: str) -> LessonState:
    with repository.connection() as connection:
        lesson = store.lesson(connection, lesson_id)
        if lesson is None:
            raise LessonError("not_found", f"No lesson {lesson_id}.")
        turns = store.turns(connection, lesson_id)
        checks = store.checks(connection, lesson_id)
        plans = store.plans(connection, lesson_id)
    opened = next((t for t in turns if t["action"] == "open"), None)
    payload = (opened or {}).get("payload") or {}
    state = LessonState(lesson=lesson, brief=payload.get("brief") or {}, book=SourceBook.from_dict(payload.get("book")),
                        turns=turns, checks=checks, plans=plans)
    ended = {check["check_ref"] for check in checks}
    for entry in turns:
        data = entry.get("payload") or {}
        action = entry["action"]
        if action == "pose_check":
            state.minted[data["check_ref"]] = data["item_id"]
            state.open_check = None if data["check_ref"] in ended else data
        elif action in ("check_result", "check_withdrawn") and state.open_check is not None \
                and state.open_check.get("check_ref") == data.get("check_ref"):
            state.open_check = None
        elif action == "pose_prediction":
            state.open_prediction = data
        elif action == "prediction_answer":
            state.open_prediction = None
        if action in READ_ACTIONS:
            state.book.passages.update((data.get("result") or {}).get("book_additions") or {})
        if action in READ_ACTIONS and data.get("deferred"):
            state.pending_results.append({"turn_id": entry["id"], "action": action,
                                          "result": _model_result(data.get("result"))})
        elif action == "results_delivered":
            delivered = set(data.get("turn_ids") or [])
            state.pending_results = [r for r in state.pending_results if r.get("turn_id") not in delivered]
        elif action == "forecast":
            state.forecasts[str(data.get("key"))] = data
            if data.get("kind") == "lesson_step_retained" and data.get("node"):
                state.landed.append(str(data["node"]))
        if entry["actor"] == "teacher" and action == "teacher_turn":
            state.failures = 0 if entry["validation"] == "ok" else state.failures + 1
    return state


# =============================================================================
# The transcript the teacher reads
# =============================================================================


def _model_result(result: Any) -> Any:
    """An action's result as the teacher reads it (the alias bookkeeping stays with code)."""

    if isinstance(result, Mapping):
        return {key: value for key, value in result.items() if key not in ("book_additions", "tool_call_id")}
    return result


def transcript(state: LessonState) -> list[dict[str, Any]]:
    """Every step so far, in order, as the teacher reads it (its own turns, the learner's words, results)."""

    out: list[dict[str, Any]] = []
    for entry in state.turns:
        data = entry.get("payload") or {}
        action = entry["action"]
        if action == "teacher_turn":
            if entry["validation"] == "ok":
                out.append({"by": "teacher", "turn": data.get("turn")})
            else:
                out.append({"by": "code", "refused": data.get("reason"), "detail": data.get("detail")})
        elif action == "learner_reply":
            out.append({"by": "learner", "reply": data.get("text"), "during_open_check": bool(data.get("help"))})
        elif action == "prediction_answer":
            out.append({"by": "learner", "prediction_answer": data.get("answer")})
        elif action == "check_answer":
            out.append({"by": "learner", "check_answer": data.get("answer"), "your_thinking": data.get("thinking"),
                        "confidence_tap": data.get("tap"), "check_ref": data.get("check_ref")})
        elif action == "check_result":
            out.append({"by": "code", "check_result": {k: data.get(k) for k in (
                "check_ref", "correctness", "result", "grader_feedback", "hedge")}})
        elif action == "check_withdrawn":
            out.append({"by": "code", "check_withdrawn": data.get("check_ref"),
                        "why": "your reply gave the check's solution away; ask a fresh question"})
        elif action in READ_ACTIONS and not data.get("deferred"):
            out.append({"by": "code", "result_of": action, "result": _model_result(data.get("result"))})
        elif action == "write_plan":
            out.append({"by": "code", "plan_stored": data.get("version")})
        elif action == "forecast":
            out.append({"by": "code", "forecast_recorded": {k: data.get(k) for k in ("kind", "node", "p")}})
        elif action == "learner_stop":
            out.append({"by": "learner", "asked_to_stop": True})
    return out


def _prompt(state: LessonState, *, results: Sequence[Mapping[str, Any]], help_reply: bool) -> str:
    context = {
        "brief": state.brief,
        "open_check": state.open_check and {k: state.open_check.get(k) for k in ("check_ref", "check")},
        "open_prediction": state.open_prediction,
        "plan": state.plans[-1]["outline"] if state.plans else None,
        "results": list(results),
        "help_reply": help_reply,
        "transcript": transcript(state),
    }
    return render_structured_prompt(
        "LearnLoop lesson: you are the teacher", PROMPT_VERSION,
        {"instructions": doctrine_text(), "context": context}, context_tail_fields=("transcript",))


# =============================================================================
# Writing the ledger
# =============================================================================


def _append(repository: Any, state: LessonState, *, actor: str, action: str, validation: str = "ok",
            refs: Mapping[str, Any] | None = None, payload: Any = None, clock: Clock | None) -> dict[str, Any]:
    if actor == "teacher" and action == "teacher_turn":
        state.failures = 0 if validation == "ok" else state.failures + 1
    with repository.atomic():
        row = store.append_turn(repository.connection(), lesson_id=state.lesson_id, actor=actor, action=action,
                                validation=validation, refs=refs, payload=payload, created_at=utc_now_iso(clock))
    entry = {"id": row["id"], "seq": row["seq"], "actor": actor, "action": action, "validation": validation,
             "refs": dict(refs or {}), "payload": payload, "created_at": utc_now_iso(clock)}
    state.turns.append(entry)
    return entry


def _model_name(client: Any) -> str | None:
    return getattr(client, "model", None)


def _family(client: Any) -> str:
    """The forecaster of §12.2's pool: the doctrine version and the teacher model."""

    return f"{DOCTRINE_VERSION}:{_model_name(client) or 'unknown'}"


# =============================================================================
# Opening
# =============================================================================


def open_lesson(vault: Any, repository: Any, *, entry: str, learning_object_ids: Sequence[str] = (),
                selection: Mapping[str, Any] | None = None, goal_text: str | None = None,
                clients: Clients, driver: str = "desktop", clock: Clock | None = None) -> dict[str, Any]:
    """Open a lesson the learner started (TE1: an LO's or a Reader selection's "Teach me this"), build
    its brief from the ledger and run the teacher's first turn."""

    require_active(vault)
    try:
        los, how, selected = resolve_goal(vault, repository, entry=entry, learning_object_ids=learning_object_ids,
                                          selection=selection)
    except LessonRefused as exc:
        raise LessonError(exc.code, str(exc)) from exc
    titles = [vault.learning_objects[lo].title for lo in los]
    text = (goal_text or "").strip() or ", ".join(titles)
    lesson_id = f"les_{new_ulid().lower()}"
    constraints = {"max_lesson_cost_usd": vault.config.teacher.max_lesson_cost_usd,
                   "sources_tokens": vault.config.teacher.context.sources_tokens}
    from learnloop.teacher.notes import your_notes

    brief, book = build_brief(vault, repository, learning_object_ids=los, how=how, goal_text=text,
                              selection=selected, driver=driver, lesson_id=lesson_id, constraints=constraints,
                              notes_provider=your_notes)
    client = clients.teacher()
    now = utc_now_iso(clock)
    with repository.atomic():
        connection = repository.connection()
        store.insert_lesson(connection, {
            "id": lesson_id, "driver": driver, "origin": "learner_pick", "origin_ref": None, "entry": entry,
            "goal_text": text, "goal": brief["goal"], "learning_object_ids": los,
            "doctrine_version": DOCTRINE_VERSION, "brief_version": brief["version"],
            "route": getattr(client, "provider_name", None), "model": _model_name(client),
            "algorithm_version": vault.config.algorithms.algorithm_version, "opened_at": now})
        store.append_turn(connection, lesson_id=lesson_id, actor="code", action="open", validation="ok",
                          refs={"selection": selected}, payload={"brief": brief, "book": book.as_dict()},
                          created_at=now)
    state = load_state(repository, lesson_id)
    return _teach(vault, repository, state, clients=clients, client=client, help_reply=False, clock=clock)


# =============================================================================
# The learner's actions
# =============================================================================


def take_turn(vault: Any, repository: Any, *, lesson_id: str, action: str, payload: Mapping[str, Any],
         clients: Clients, clock: Clock | None = None) -> dict[str, Any]:
    """One learner action on an open lesson (``reply``, ``answer_prediction``, ``answer_check``, ``stop``)."""

    require_active(vault)
    if action not in LEARNER_ACTIONS:
        raise LessonError("validation_error", f"Unknown lesson action {action!r}.")
    state = load_state(repository, lesson_id)
    if state.closed:
        return view(vault, repository, lesson_id)
    if action == "stop":
        _append(repository, state, actor="learner", action="learner_stop", payload={}, clock=clock)
        client = clients.teacher()
        return _teach(vault, repository, state, clients=clients, client=client, help_reply=False, clock=clock,
                      closing="learner_stop")
    if action == "reply":
        text = str(payload.get("text") or "").strip()
        if not text:
            raise LessonError("validation_error", "Write something first.")
        help_request = state.open_check is not None
        _append(repository, state, actor="learner", action="learner_reply", payload={"text": text, "help": help_request},
                clock=clock)
        if help_request:
            _record_help(repository, state, text, clock=clock)
        client = clients.teacher()
        return _teach(vault, repository, state, clients=clients, client=client, help_reply=help_request, clock=clock)
    if action == "answer_prediction":
        if state.open_prediction is None:
            raise LessonError("validation_error", "There is no open prediction.")
        _append(repository, state, actor="learner", action="prediction_answer",
                payload={"answer": str(payload.get("answer") or ""), "node": state.open_prediction.get("node")},
                clock=clock)
        state.open_prediction = None
        client = clients.teacher()
        return _teach(vault, repository, state, clients=clients, client=client, help_reply=False, clock=clock)
    # answer_check
    return _answer_check(vault, repository, state, payload, clients=clients, clock=clock)


def _record_help(repository: Any, state: LessonState, text: str, *, clock: Clock | None) -> None:
    """Help while a check is open (§12): one ``help_assists`` row (surface ``tutor``); never evidence."""

    import hashlib

    from learnloop.db.stores.help_assists import insert_assist

    assert state.open_check is not None
    now = utc_now_iso(clock)
    with repository.atomic():
        insert_assist(repository.connection(), {
            "id": f"ha_{new_ulid().lower()}", "surface": "tutor", "assist_kind": "hint",
            "practice_item_id": state.open_check["item_id"], "chooser": "learner_pick", "shown": 1,
            "work_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(), "work_chars": len(text),
            "strategy": f"lesson:{state.lesson_id}", "requested_at": now, "shown_at": now,
        })


def _answer_check(vault: Any, repository: Any, state: LessonState, payload: Mapping[str, Any], *, clients: Clients,
                  clock: Clock | None) -> dict[str, Any]:
    from learnloop.learner.lesson_weight import read_hedges
    from learnloop.vault.loader import load_vault

    open_check = state.open_check
    if open_check is None:
        raise LessonError("validation_error", "There is no open check.")
    if payload.get("check_ref") and str(payload["check_ref"]) != str(open_check["check_ref"]):
        raise LessonError("stale_check", "That check is no longer open.")
    answer = str(payload.get("answer") or "").strip()
    if not answer:
        raise LessonError("validation_error", "Write an answer first.")
    tap = payload.get("tap")
    tap = int(tap) if tap is not None and int(tap) in (1, 2, 3, 4, 5) else None
    thinking = str(payload.get("thinking") or "").strip() or None
    vault = load_vault(vault.root) if open_check["item_id"] not in vault.practice_items else vault
    item = vault.practice_items.get(open_check["item_id"])
    if item is None:
        raise LessonError("not_found", "The check's question could not be read.")
    attempt_id = new_ulid()
    _append(repository, state, actor="learner", action="check_answer",
            refs={"item": item.id, "attempt": attempt_id},
            payload={"check_ref": open_check["check_ref"], "answer": answer, "thinking": thinking, "tap": tap},
            clock=clock)
    # The blind grader sees the answer only: never the thinking note, the lesson or the learner's history.
    grading_client = clients.grading()
    try:
        grade, run_id = CK.grade_answer(vault, repository, grading_client, item=item, attempt_id=attempt_id,
                                        answer=answer, clock=clock)
    except Exception as exc:  # noqa: BLE001 - the check stays open; the learner can submit again
        raise LessonError("grading_unavailable", f"Your answer couldn't be graded right now ({type(exc).__name__}). "
                                                 "Try submitting it again.") from exc
    max_points = max(int(getattr(vault.rubric_for_item(item), "max_points", 1) or 1), 1)
    correctness = max(0.0, min(1.0, float(grade.rubric_score) / max_points))
    hedges = [row.get("learner_confidence") for row in grade.evidence_rows
              if row.get("learner_confidence") in ("hedged", "confident")]
    hedge = None if not hedges else ("hedged" if "hedged" in hedges else "confident")
    as_of = utc_now_iso(clock)
    node_id = str(open_check["check"]["node"])
    lo = str(item.learning_object_id)
    retained = _latest_forecast(state, "lesson_step_retained", node_id)
    family = _family(clients.teacher())
    mass = CK.check_mass(vault, repository, learning_object_id=lo, tap=tap, hedge=hedge, correctness=correctness,
                         item=item, as_of=as_of, p_teacher_retained=(retained or {}).get("p"), family=family)
    correct_forecast = _latest_forecast(state, "lesson_check_correct", open_check["check_ref"])
    CK.record_answered_check(
        vault, repository, lesson_id=state.lesson_id, node_id=node_id, check_ref=open_check["check_ref"], item=item,
        attempt_id=attempt_id, answer=answer, grade=grade, grading_run_id=run_id,
        grading_source=clients.grading_source, tap=tap, mass=mass, created_at=as_of,
        forecast_correct_key=(correct_forecast or {}).get("key"), forecast_retained_key=(retained or {}).get("key"),
        clock=clock)
    _update_weight_state(vault, repository)
    result = {"check_ref": open_check["check_ref"], "correctness": correctness,
              "result": "right" if correctness >= 1.0 else ("wrong" if correctness <= 0.0 else "partly right"),
              "grader_feedback": grade.feedback_md, "hedge": hedge, "mass_applied": mass["mass_applied"],
              "attempt_id": attempt_id, "unanchored": not bool(open_check["check"].get("anchors"))}
    _append(repository, state, actor="code", action="check_result", refs={"attempt": attempt_id, "item": item.id},
            payload=result, clock=clock)
    state.open_check = None
    state.checks.append({"check_ref": result["check_ref"], "status": "answered", "minted_item_id": item.id})
    return _teach(vault, repository, state, clients=clients, client=clients.teacher(), help_reply=False, clock=clock)


def _latest_forecast(state: LessonState, kind: str, ref: str) -> dict[str, Any] | None:
    found = None
    for forecast in state.forecasts.values():
        if forecast.get("kind") == kind and str(forecast.get("node")) == str(ref):
            found = forecast
    return found


def _update_weight_state(vault: Any, repository: Any) -> None:
    """Refresh the DERIVED weight tables after a check (the replayer's own function, as of now)."""

    from learnloop.learner.lesson_weight import replay_state, write_state

    with repository.atomic():
        write_state(repository, replay_state(vault, repository))


# =============================================================================
# The teacher's turn
# =============================================================================


@dataclass
class _Outcome:
    shown: list[dict[str, Any]] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)
    vault_changed: bool = False
    usage: dict[str, int] = field(default_factory=lambda: {"calls": 0, "input_tokens": 0, "output_tokens": 0})


def _teach(vault: Any, repository: Any, state: LessonState, *, clients: Clients, client: Any, help_reply: bool,
           clock: Clock | None, closing: str | None = None) -> dict[str, Any]:
    outcome = _Outcome()
    results = list(state.pending_results)
    if results:
        _append(repository, state, actor="code", action="results_delivered",
                payload={"turn_ids": [r.get("turn_id") for r in results]}, clock=clock)
        state.pending_results = []
    # Accepted turns this action: the first one's read requests get one follow-up call; later ones ride with
    # the next learner action (a refused turn does not count, so its correction never defers a read).
    accepted = 0
    if closing:
        results = [*results, {"code": "the learner asked to stop: close the lesson now with a recap"}]
    while not state.closed:
        try:
            parsed = _call_teacher(vault, repository, state, client, results=results, help_reply=help_reply,
                                   outcome=outcome, clock=clock)
        except LessonError:
            raise
        except Exception as exc:  # noqa: BLE001 - the plan is down or the route refused: the lesson waits
            from learnloop.ai.errors import AIProviderUnavailable

            unavailable = isinstance(exc, AIProviderUnavailable) or "unavailable" in type(exc).__name__.lower()
            if closing:
                _close(vault, repository, state, reason=closing, recap=None, clock=clock, outcome=outcome)
                break
            raise LessonError("plan_unavailable" if unavailable else "teacher_unavailable",
                              "The teacher isn't available right now; your lesson is saved and resumes when it "
                              "is.") from exc
        if parsed is None:
            if state.failures >= MAX_CONTRACT_FAILURES:
                _close(vault, repository, state, reason="teacher_contract_failure", recap=None, clock=clock,
                       outcome=outcome)
                break
            continue
        turn_obj, turn_entry = parsed
        requested_reads = [request for request in turn_obj.requests if request.action in READ_ACTIONS]
        deferred = accepted >= 1
        accepted += 1
        new_results = _execute(vault, repository, state, turn_obj, client=client, deferred=deferred,
                               outcome=outcome, clock=clock, help_reply=help_reply)
        if state.closed:
            break
        if closing:
            _close(vault, repository, state, reason=closing, recap=None, clock=clock, outcome=outcome)
            break
        if requested_reads and not deferred:
            results = new_results
            help_reply = False
            continue
        break
    if outcome.usage["calls"]:
        _append(repository, state, actor="code", action="usage", payload={"usage": dict(outcome.usage)}, clock=clock)
    return view(vault, repository, state.lesson_id, outcome=outcome)


def _call_teacher(vault: Any, repository: Any, state: LessonState, client: Any, *, results: Sequence[Mapping[str, Any]],
                  help_reply: bool, outcome: _Outcome, clock: Clock | None) -> tuple[TeacherTurnV1, dict[str, Any]] | None:
    """One teacher call: validated, guarded, recorded. None when refused (a correctable error)."""

    _admit_spend(vault, client, state)
    prompt = _prompt(state, results=results, help_reply=help_reply)
    raw = execute_structured_operation(client, purpose=TEACHER_PURPOSE, prompt=prompt, result_model=TeacherTurnV1)
    usage = client.consume_usage() if hasattr(client, "consume_usage") else None
    outcome.usage["calls"] += 1
    if usage is not None:
        outcome.usage["input_tokens"] += int(getattr(usage, "input_tokens", 0) or 0)
        outcome.usage["output_tokens"] += int(getattr(usage, "output_tokens", 0) or 0)
    try:
        turn_obj = raw if isinstance(raw, TeacherTurnV1) else TeacherTurnV1.model_validate(raw)
    except ValidationError as exc:
        _append(repository, state, actor="teacher", action="teacher_turn", validation="invalid",
                payload={"reason": "schema", "detail": str(exc)[:2000]}, clock=clock)
        return None
    problem = _contract_problem(state, turn_obj)
    if problem is not None:
        _append(repository, state, actor="teacher", action="teacher_turn", validation="invalid",
                payload={"reason": "contract", "detail": problem, "turn": turn_obj.model_dump()}, clock=clock)
        return None
    exempt = list(state.minted.values())
    keys, unreadable = G.lesson_keys(vault, repository, state.los, exempt)
    texts = [turn_obj.message, *(turn_obj.choices or [])]
    if turn_obj.prediction is not None:
        texts.extend([turn_obj.prediction.prompt, *turn_obj.prediction.choices])
    if turn_obj.check is not None:
        texts.extend([turn_obj.check.question, *turn_obj.check.choices])
    # The open check's solution guard also covers the check this turn poses: its message (never its
    # options, which carry the right one by design) must not give the solution away.
    posing = turn_obj.check.model_dump() if turn_obj.check is not None else None
    for index, text in enumerate(texts):
        open_check = state.open_check and state.open_check.get("check")
        if open_check is None and posing is not None and index == 0:
            open_check = posing
        verdict = G.check_all(text, keys=keys, unreadable=unreadable, book=state.book,
                              open_check=open_check, help_reply=help_reply)
        if not verdict.ok:
            _append(repository, state, actor="teacher", action="teacher_turn", validation="withheld",
                    payload={"reason": verdict.reason, "detail": verdict.detail, "turn": turn_obj.model_dump()},
                    clock=clock)
            return None
    entry = _append(repository, state, actor="teacher", action="teacher_turn", validation="ok",
                    payload={"turn": turn_obj.model_dump(), "turn_version": TURN_VERSION}, clock=clock)
    if turn_obj.message:
        outcome.shown.append({"kind": "message", "text": turn_obj.message, "choices": list(turn_obj.choices)})
        _record_reveals(vault, repository, state, turn_obj.message, clock=clock)
    if help_reply and state.open_check is not None:
        overlap = G.solution_overlap(turn_obj.message, str(state.open_check["check"]["committed_solution"]))
        from learnloop.serve_eligibility import AUTO_PRIME_REVEAL_THRESHOLD

        if overlap >= AUTO_PRIME_REVEAL_THRESHOLD:
            _withdraw(vault, repository, state, overlap=overlap, clock=clock, outcome=outcome)
    return turn_obj, entry


def _contract_problem(state: LessonState, turn_obj: TeacherTurnV1) -> str | None:
    if turn_obj.check is not None and state.open_check is not None:
        return "a check is already open: wait for its answer before posing another"
    if turn_obj.check is not None and turn_obj.prediction is not None:
        return "pose a prediction or a check in one turn, not both"
    if turn_obj.check is not None:
        check = turn_obj.check
        if check.form == "choices" and len(check.choices) < 2:
            return "a choices check needs at least two options"
        unknown = [alias for alias in check.anchors if alias not in state.book.passages]
        if unknown:
            return f"the check's anchors were never delivered to you: {', '.join(unknown)}"
    for request in turn_obj.requests:
        if request.action == "write_plan":
            for node in request.plan:
                unknown = [alias for alias in node.anchors
                           if alias not in state.book.passages and alias not in state.book.sections]
                if unknown:
                    return f"plan node {node.id}: these anchors don't resolve: {', '.join(unknown)}"
        if request.action == "forecast" and (request.forecast_kind is None or request.p is None or not request.node):
            return "a forecast needs forecast_kind, node and p"
        if request.action == "close" and request.close_reason is None:
            return "close needs a close_reason"
    if not turn_obj.message and turn_obj.check is None and turn_obj.prediction is None and not turn_obj.requests:
        return "the turn is empty"
    return None


def _admit_spend(vault: Any, client: Any, state: LessonState) -> None:
    """A metered (OpenRouter) lesson needs its price and its per-lesson cap (T1 redesign D; Q7)."""

    from learnloop.ai.spend import is_subscription_transport

    if is_subscription_transport(client=client) or getattr(client, "provider_type", None) == "fake":
        return
    config = vault.config.teacher
    if config.metered_price_per_million is None or config.max_lesson_cost_usd is None:
        raise LessonError("plan_unavailable", "A lesson on OpenRouter needs teacher.metered_price_per_million and "
                                              "teacher.max_lesson_cost_usd set first.")
    spent = _spent_usd(state, float(config.metered_price_per_million))
    if spent >= float(config.max_lesson_cost_usd):
        raise LessonError("budget", "This lesson reached its spending cap.")


def _spent_usd(state: LessonState, price_per_million: float) -> float:
    tokens = 0
    for entry in state.turns:
        usage = (entry.get("payload") or {}).get("usage") if entry["action"] == "usage" else None
        if usage:
            tokens += int(usage.get("input_tokens", 0)) + int(usage.get("output_tokens", 0))
    return tokens * price_per_million / 1_000_000.0


def _record_reveals(vault: Any, repository: Any, state: LessonState, message: str, *, clock: Clock | None) -> None:
    """Teaching text and cited passages (§12): ``tutor_answer`` for each item on the lesson's LOs whose key
    the text overlaps (amount = overlap, as the tutor), ``source_review`` for what a cited passage exposes;
    basis ``lesson:<id>``. The lesson's own check items are the attempts themselves, not reveals."""

    from learnloop.attempts.reveal_ledger import record_reveal
    from learnloop.tutor.tutor_qa import answer_leak_overlap, span_answer_overlap

    los = set(state.los)
    minted = set(state.minted.values())
    passages = [state.book.passages[alias]["text"] for alias in G.cited_aliases(message) if alias in state.book.passages]
    basis = f"lesson:{state.lesson_id}"
    with repository.atomic():
        for item in sorted(vault.practice_items.values(), key=lambda value: value.id):
            if item.learning_object_id not in los or item.id in minted or CK.lesson_item(item):
                continue
            amount = answer_leak_overlap(message, item.expected_answer)
            record_reveal(repository, practice_item_id=item.id, source_kind="tutor_answer", amount=amount,
                          learning_object_id=item.learning_object_id, basis=basis, clock=clock)
            if passages:
                exposed = max(span_answer_overlap(text, item.expected_answer) for text in passages)
                record_reveal(repository, practice_item_id=item.id, source_kind="source_review", amount=exposed,
                              learning_object_id=item.learning_object_id, basis=basis, clock=clock)


def _withdraw(vault: Any, repository: Any, state: LessonState, *, overlap: float, clock: Clock | None,
              outcome: _Outcome) -> None:
    from learnloop.vault.loader import load_vault

    assert state.open_check is not None
    check = state.open_check
    loaded = vault if check["item_id"] in vault.practice_items else load_vault(vault.root)
    item = loaded.practice_items[check["item_id"]]
    CK.withdraw_check(repository, lesson_id=state.lesson_id, node_id=str(check["check"]["node"]),
                      check_ref=check["check_ref"], item=item, overlap=overlap, created_at=utc_now_iso(clock))
    _append(repository, state, actor="code", action="check_withdrawn", refs={"item": item.id},
            payload={"check_ref": check["check_ref"], "overlap": overlap}, clock=clock)
    state.open_check = None
    outcome.notices.append("That reply gave the check's answer away, so the check was withdrawn; it doesn't count "
                           "either way.")


# =============================================================================
# The actions
# =============================================================================


def _execute(vault: Any, repository: Any, state: LessonState, turn_obj: TeacherTurnV1, *, client: Any,
             deferred: bool, outcome: _Outcome, clock: Clock | None, help_reply: bool) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    if turn_obj.prediction is not None:
        data = turn_obj.prediction.model_dump()
        _append(repository, state, actor="teacher", action="pose_prediction", payload=data, clock=clock)
        state.open_prediction = data
        outcome.shown.append({"kind": "prediction", **data})
    if turn_obj.check is not None:
        _pose_check(vault, repository, state, turn_obj.check, outcome=outcome, clock=clock)
    for request in turn_obj.requests:
        if request.action in READ_ACTIONS:
            result = _read_action(vault, repository, state, request, client=client)
            entry = _append(repository, state, actor="code", action=request.action,
                            refs={"tool_call": result.get("tool_call_id")} if result.get("tool_call_id") else None,
                            payload={"request": request.model_dump(), "result": result, "deferred": deferred},
                            clock=clock)
            if deferred:
                state.pending_results.append({"turn_id": entry["id"], "action": request.action,
                                              "result": _model_result(result)})
            else:
                results.append({"action": request.action, "result": _model_result(result)})
        elif request.action == "write_plan":
            outline = [node.model_dump() for node in request.plan]
            with repository.atomic():
                version = store.insert_plan(repository.connection(), lesson_id=state.lesson_id, outline=outline,
                                            created_at=utc_now_iso(clock))
            state.plans.append({"version": version, "outline": outline})
            _append(repository, state, actor="code", action="write_plan", payload={"version": version}, clock=clock)
        elif request.action == "forecast":
            _forecast(vault, repository, state, request, client=client, clock=clock)
        elif request.action == "close":
            _close(vault, repository, state, reason=str(request.close_reason), recap=request.recap, clock=clock,
                   outcome=outcome)
            break
    return results


def _pose_check(vault: Any, repository: Any, state: LessonState, check: CheckV1, *, outcome: _Outcome,
                clock: Clock | None) -> None:
    lo = state.node_lo(check.node)
    if lo is None or lo not in vault.learning_objects:
        lo = (state.brief.get("goal") or {}).get("learning_object_ids", [None])[0]
    check_ref = f"c{len(state.minted) + 1}"
    item_id = CK.mint_check_item(Path(vault.root), lesson_id=state.lesson_id, check_ref=check_ref, check=check,
                                 learning_object_id=str(lo), book=state.book, clock=clock)
    data = {"check_ref": check_ref, "item_id": item_id, "learning_object_id": lo, "check": check.model_dump()}
    _append(repository, state, actor="teacher", action="pose_check", refs={"item": item_id}, payload=data, clock=clock)
    state.minted[check_ref] = item_id
    state.open_check = data
    outcome.vault_changed = True
    outcome.shown.append({"kind": "check", "check_ref": check_ref, "node": check.node, "question": check.question,
                          "form": check.form, "choices": list(check.choices),
                          "unanchored": not bool(check.anchors)})


def _read_action(vault: Any, repository: Any, state: LessonState, request: ActionRequestV1, *,
                 client: Any) -> dict[str, Any]:
    from learnloop.teacher import actions as A

    try:
        return A.run_read(vault, repository, state, request, model=_model_name(client))
    except A.ActionRefused as exc:
        return {"refused": exc.code, "message": str(exc)}


def _forecast(vault: Any, repository: Any, state: LessonState, request: ActionRequestV1, *, client: Any,
              clock: Clock | None) -> None:
    from learnloop.scheduling.forecast_receipts import (
        LESSON_CHECK_ATTEMPT,
        LESSON_COLD_OUTCOME,
        ForecastReceipt,
        record_receipts,
    )
    from learnloop.teacher.brief import lo_prediction

    kind = str(request.forecast_kind)
    node = str(request.node)
    family = _family(client)
    now = utc_now_iso(clock)
    if kind == "lesson_check_correct":
        ref = state.open_check["check_ref"] if state.open_check is not None else node
        lo = (state.open_check or {}).get("learning_object_id") or state.node_lo(node)
        inputs = {"lesson_id": state.lesson_id, "check_ref": ref, "learning_object_id": lo, "family": family}
        scope, binding, event = "lesson_check", LESSON_CHECK_ATTEMPT, "lesson_check_correct"
        node = ref
    else:
        lo = state.node_lo(node)
        p_a = lo_prediction(vault, repository, lo).get("p") if lo else None
        inputs = {"lesson_id": state.lesson_id, "node_id": node, "learning_object_id": lo, "family": family,
                  "p_a": p_a}
        scope, binding, event = "lesson_node", LESSON_COLD_OUTCOME, "cold_success"
    key = f"{kind}:{state.lesson_id}:{node}:{len(state.forecasts) + 1}"
    receipt = ForecastReceipt(
        receipt_key=key, kind=kind, forecaster="teacher", forecaster_version=family, scope=scope,
        decision_kind="lesson", binding_kind=binding, event=event,
        forecast={"emission_alphabet": ["success", "failure"],
                  "predicted_outcomes": {"success": round(float(request.p), 8),
                                         "failure": round(1.0 - float(request.p), 8)}},
        inputs=inputs, parameters=[{"name": "p", "value": float(request.p), "provenance": "model"}],
        versions={"doctrine": DOCTRINE_VERSION, "prompt": PROMPT_VERSION}, inputs_as_of=now, p=float(request.p),
        columns={"decision_ref": state.lesson_id, "learning_object_id": lo})
    written = record_receipts(repository, [receipt], vault=vault, clock=clock, created_at=now)
    data = {"key": key, "kind": kind, "node": node, "p": float(request.p), "learning_object_id": lo,
            "written": bool(written)}
    _append(repository, state, actor="code", action="forecast", payload=data, clock=clock)
    state.forecasts[key] = data
    if kind == "lesson_step_retained":
        state.landed.append(str(request.node))


# =============================================================================
# Closing
# =============================================================================


def _close(vault: Any, repository: Any, state: LessonState, *, reason: str, recap: str | None, clock: Clock | None,
           outcome: _Outcome) -> None:
    """Close the lesson: commit the delayed checks, write the receipt, close the row (§7 step 7)."""

    from learnloop.teacher import delayed as D
    from learnloop.vault.loader import load_vault

    if state.closed:
        return
    loaded = load_vault(vault.root) if any(i not in vault.practice_items for i in state.minted.values()) else vault
    landed_ids = list(dict.fromkeys(state.landed))
    with repository.connection() as connection:
        rows = store.checks(connection, state.lesson_id)
    right_nodes = {row["node_id"] for row in rows if row["status"] == "answered" and (row["correctness"] or 0) >= 1.0}
    for node_id in right_nodes:
        if node_id not in landed_ids:
            landed_ids.append(node_id)
    landed = []
    for node_id in landed_ids:
        lo = state.node_lo(node_id)
        landed.append({"id": node_id, "lo_id": lo})
    lesson_items_by_lo: dict[str, list[str]] = {}
    for row in rows:
        lesson_items_by_lo.setdefault(row["learning_object_id"], []).append(row["minted_item_id"])
    delayed_checks: list[dict[str, Any]] = []
    warnings: list[str] = []
    if reason in ("goal_reached", "learner_stop", "budget", "teacher_contract_failure", "plan_unavailable"):
        delayed_checks, warnings = D.commit_checks(
            loaded, repository, lesson_id=state.lesson_id, landed=landed,
            goal_learning_object_ids=(state.brief.get("goal") or {}).get("learning_object_ids") or [],
            lesson_items_by_lo=lesson_items_by_lo, shown_items=state.minted.values(), clock=clock)
    receipt = _receipt(loaded, repository, state, reason=reason, recap=recap, delayed_checks=delayed_checks,
                       warnings=warnings, landed=landed, rows=rows, usage=outcome.usage)
    now = utc_now_iso(clock)
    with repository.atomic():
        connection = repository.connection()
        store.insert_receipt(connection, lesson_id=state.lesson_id, version=RECEIPT_VERSION, close_reason=reason,
                             receipt=receipt, created_at=now)
        store.close_lesson(connection, state.lesson_id, reason=reason, closed_at=now)
    _append(repository, state, actor="code", action="close",
            refs={"commitments": [c["commitment_id"] for c in delayed_checks if c.get("commitment_id")]},
            payload={"reason": reason, "recap": recap, "delayed_checks": delayed_checks}, clock=clock)
    state.lesson["closed_at"], state.lesson["close_reason"] = now, reason
    outcome.shown.append({"kind": "close", "reason": reason, "recap": recap,
                          "delayed_checks": [c for c in delayed_checks if c.get("commitment_id")]})


def _receipt(vault: Any, repository: Any, state: LessonState, *, reason: str, recap: str | None,
             delayed_checks: Sequence[Mapping[str, Any]], warnings: Sequence[str], landed: Sequence[Mapping[str, Any]],
             rows: Sequence[Mapping[str, Any]], usage: Mapping[str, int]) -> dict[str, Any]:
    """``LessonReceiptV1`` (§8.3)."""

    with repository.connection() as connection:
        reveal_rows = connection.execute(
            "SELECT practice_item_id, source_kind, amount FROM reveal_events WHERE basis = ? ORDER BY created_at, id",
            (f"lesson:{state.lesson_id}",)).fetchall()
    landed_ids = {node["id"] for node in landed}
    nodes = []
    plan = state.plans[-1]["outline"] if state.plans else []
    for node in plan or [{"id": lo, "lo_id": lo, "anchors": []} for lo in state.brief.get("goal", {}).get(
            "learning_object_ids", [])]:
        node_checks = [{"attempt_id": row["attempt_id"], "status": row["status"], "correctness": row["correctness"]}
                       for row in rows if row["node_id"] == node["id"]]
        if node["id"] in landed_ids:
            status = "landed"
        elif node_checks:
            status = "taught"
        else:
            status = "uncertain"
        nodes.append({"id": node["id"], "lo_id": node.get("lo_id"), "status": status,
                      "anchors": node.get("anchors") or [], "checks": node_checks})
    weight_inputs = [{
        "check_ref": row["check_ref"], "attempt_id": row["attempt_id"], "tap": row["tap"], "hedge": row["hedge"],
        "predicted_success": row["predicted_success"], "predicted_source": row["predicted_source"],
        "mass_learned": row["mass_learned"], "mass_applied": row["mass_applied"],
        "rule": (row["weight_inputs"] or {}).get("rule"), "forecast_key": row["forecast_correct_key"],
    } for row in rows if row["status"] == "answered"]
    stability_inputs = _stability_inputs(repository, landed, rows, state)
    return {
        "version": RECEIPT_VERSION,
        "lesson_id": state.lesson_id,
        "driver": state.lesson["driver"],
        "model": state.lesson.get("model"),
        "route": state.lesson.get("route"),
        "doctrine": doctrine_identity(),
        "goal": state.brief.get("goal"),
        "learning_object_ids": state.lesson.get("learning_object_ids"),
        "close_reason": reason,
        "recap": recap,
        "plan_versions": state.plans,
        "nodes": nodes,
        "nodes_summary": [{"id": n["id"], "lo_id": n["lo_id"], "status": n["status"]} for n in nodes],
        "exposure": {"reveals": [{"item_id": r[0], "kind": r[1], "amount": r[2]} for r in reveal_rows],
                     "passages": sorted(state.book.passages)},
        "gaps": [],
        "created_los": [],
        "delayed_checks": list(delayed_checks),
        "forecasts": sorted(state.forecasts),
        "weight_inputs": weight_inputs,
        "stability_inputs": stability_inputs,
        "origin": state.lesson.get("origin"),
        "cost": {**dict(usage), "route": state.lesson.get("route")},
        "warnings": list(warnings),
    }


def _stability_inputs(repository: Any, landed: Sequence[Mapping[str, Any]], rows: Sequence[Mapping[str, Any]],
                      state: LessonState) -> list[dict[str, Any]]:
    """Per landed node, the liquid-stability inputs ``u`` (§8.3; logged before the family activates)."""

    out = []
    for node in landed:
        lo = node.get("lo_id")
        if not lo:
            continue
        with repository.connection() as connection:
            last = connection.execute(
                "SELECT attempt_type, hints_used, primed, answer_confidence, correctness, id FROM practice_attempts "
                "WHERE learning_object_id = ? ORDER BY created_at DESC, id DESC LIMIT 1", (lo,)).fetchone()
            surprise = None
            if last is not None:
                row = connection.execute("SELECT predictive_surprise FROM attempt_surprise WHERE attempt_id = ?",
                                         (last[5],)).fetchone()
                surprise = row[0] if row else None
        tap = last[3] if last else None
        out.append({
            "node_id": node["id"], "learning_object_id": lo, "how_learned": f"lesson:{state.lesson_id}",
            "checks": [{"correctness": r["correctness"], "status": r["status"]} for r in rows if r["node_id"] == node["id"]],
            "hint_depth": last[1] if last else None, "last_attempt_type": last[0] if last else None,
            "last_tap": tap, "confident_miss": bool(tap is not None and tap >= 4 and last and (last[4] or 0) <= 0.0),
            "last_surprise": surprise,
        })
    return out


# =============================================================================
# The view the desktop shows
# =============================================================================


def view(vault: Any, repository: Any, lesson_id: str, *, outcome: _Outcome | None = None) -> dict[str, Any]:
    """The lesson as the screen shows it: what was shown, in order, the plan map, the open check
    (never its solution), the open prediction, and the close card. Forecasts, receipts and routes
    stay in the inspector (``inspector``)."""

    state = load_state(repository, lesson_id)
    feed: list[dict[str, Any]] = []
    for entry in state.turns:
        data = entry.get("payload") or {}
        action = entry["action"]
        if action == "teacher_turn" and entry["validation"] == "ok":
            turn_data = data.get("turn") or {}
            if turn_data.get("message"):
                feed.append({"kind": "message", "text": turn_data["message"], "choices": turn_data.get("choices") or []})
        elif action == "pose_prediction":
            feed.append({"kind": "prediction", **{k: data.get(k) for k in ("node", "prompt", "choices")}})
        elif action == "pose_check":
            check = data.get("check") or {}
            feed.append({"kind": "check", "check_ref": data.get("check_ref"), "node": check.get("node"),
                         "question": check.get("question"), "form": check.get("form"),
                         "choices": check.get("choices") or [], "unanchored": not check.get("anchors")})
        elif action in ("learner_reply", "prediction_answer", "check_answer"):
            feed.append({"kind": "learner", "text": data.get("text") or data.get("answer"),
                         "check_ref": data.get("check_ref")})
        elif action == "check_result":
            feed.append({"kind": "check_result", **{k: data.get(k) for k in (
                "check_ref", "result", "grader_feedback", "unanchored")},
                "answer_label": "LearnLoop's answer" if data.get("unanchored") else None})
        elif action == "check_withdrawn":
            feed.append({"kind": "notice", "text": "That reply gave the check's answer away, so the check was "
                                                   "withdrawn; it doesn't count either way."})
        elif action == "close":
            feed.append({"kind": "close", "reason": data.get("reason"), "recap": data.get("recap"),
                         "delayed_checks": [{"learning_object_id": c.get("learning_object_id"),
                                             "title": (vault.learning_objects.get(c.get("learning_object_id") or "")
                                                       .title if vault.learning_objects.get(
                                                           c.get("learning_object_id") or "") else None),
                                             "purpose": c.get("purpose"), "due": c.get("due")}
                                            for c in data.get("delayed_checks") or [] if c.get("commitment_id")]})
    plan = state.plans[-1]["outline"] if state.plans else []
    visited = {str(c.get("node_id")) for c in state.checks if c.get("node_id")}
    current = (state.open_check or {}).get("check", {}).get("node") if state.open_check else None
    plan_map = [{"id": node["id"], "statement": node.get("statement"),
                 "position": "current" if node["id"] == current else (
                     "visited" if node["id"] in visited or node["id"] in state.landed else "upcoming")}
                for node in plan]
    out = {
        "lesson_id": lesson_id,
        "goal": (state.brief.get("goal") or {}).get("text"),
        "learning_object_ids": state.lesson.get("learning_object_ids"),
        "closed": state.closed,
        "close_reason": state.lesson.get("close_reason"),
        "feed": feed,
        "plan": plan_map,
        "open_check": None if state.open_check is None else {
            "check_ref": state.open_check["check_ref"], "question": state.open_check["check"]["question"],
            "form": state.open_check["check"]["form"], "choices": state.open_check["check"].get("choices") or []},
        "open_prediction": state.open_prediction and {k: state.open_prediction.get(k) for k in ("node", "prompt", "choices")},
        "quick_check": {"learning_object_ids": (state.brief.get("goal") or {}).get("learning_object_ids") or []},
        "inspector": {"doctrine": state.lesson.get("doctrine_version"), "route": state.lesson.get("route"),
                      "model": state.lesson.get("model"), "forecasts": sorted(state.forecasts)},
    }
    if outcome is not None:
        out["shown_now"] = outcome.shown
        out["notices"] = outcome.notices
        out["vault_changed"] = outcome.vault_changed
    return out


__all__ = [
    "Clients",
    "LEARNER_ACTIONS",
    "LessonError",
    "MAX_CONTRACT_FAILURES",
    "lessons_active",
    "load_state",
    "open_lesson",
    "require_active",
    "transcript",
    "take_turn",
    "view",
]

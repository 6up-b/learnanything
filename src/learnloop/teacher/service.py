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

**Guards** (§9.3) run on every learner-facing field of a turn (the message
and its choices, a prediction, a check, plan statements, a close's recap), and
every displayed field is accounted as exposure (reveal rows). Before every
model call the saved context is revalidated against protection as it is NOW
(:func:`revalidate_material`): a passage or an item that became exam or
held-out material since it was delivered is never resent, read back or citable.

**State** is the lesson ledger itself (``lesson_turns`` and their payloads,
``lesson_plans``, ``lesson_checks``): a lesson resumes after a restart or after
the plan returns. An accepted turn, its delivered results and its reveal rows
are one transaction; each of its effects is marked with the turn in the
transaction that makes it, and a ``turn_executed`` marker ends them, so an
interrupted action is resumed idempotently (:func:`recover`, run by the next
action and by ``lesson.view``); closing (receipt, row, close entry) is one
transaction. ``resume`` runs the teacher's turn an outage interrupted.

**Spend** (§17): every physical metered request of a lesson action (the
teacher's, the inline grader's, a retrieval call's) is admitted by the lesson's
envelope (``ai.spend.MeteredRequestGate``) against what the lesson already
spent, reserved before it is sent and settled into a durable ``spend`` row;
a refused request closes the lesson with ``budget``.

**Code owns** what enters the model's context (the brief, the delivered
passages, the action results, all through the protection the brief uses), the
guards, grading (the blind grader), evidence and its weight, reveal accounting,
the delayed checks and their dates, caps and receipts. The teacher owns the
pedagogy.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
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
LEARNER_ACTIONS = ("reply", "answer_prediction", "answer_check", "stop", "resume")


class LessonError(ValueError):
    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        #: What the screen needs to resume (``lesson_id`` once the lesson is saved).
        self.details: dict[str, Any] = dict(details or {})


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
    #: Accepted teacher turns whose effects all ran (a ``turn_executed`` marker), and per accepted
    #: turn the effects already recorded (``refs.effect``): recovery resumes the rest (§7, §18).
    executed: set[str] = field(default_factory=set)
    effects_done: dict[str, set[str]] = field(default_factory=dict)
    #: The last accepted teacher turn, when its effects did not all run (an interrupted action).
    unexecuted: dict[str, Any] | None = None
    #: The lesson's spend gate while an action runs (§17).
    gate: Any = None
    #: Brief items withheld since the lesson opened (recomputed before every call: review F4).
    withheld_items: set[str] = field(default_factory=set)

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
    last_accepted: dict[str, Any] | None = None
    for entry in turns:
        data = entry.get("payload") or {}
        action = entry["action"]
        refs = entry.get("refs") or {}
        if refs.get("turn") and refs.get("effect"):
            state.effects_done.setdefault(str(refs["turn"]), set()).add(str(refs["effect"]))
        if action == "turn_executed":
            state.executed.add(str(data.get("turn_id")))
        if entry["actor"] == "teacher" and action == "teacher_turn" and entry["validation"] == "ok":
            last_accepted = entry
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
    if last_accepted is not None and str(last_accepted["id"]) not in state.executed and not state.closed:
        state.unexecuted = last_accepted
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
    deferred: dict[str, dict[str, Any]] = {}
    for entry in state.turns:
        data = entry.get("payload") or {}
        action = entry["action"]
        if action in READ_ACTIONS and data.get("deferred"):
            # A deferred read's result enters the transcript where it was delivered (review F10):
            # before that it rides in the call's ``results``.
            deferred[str(entry["id"])] = {"by": "code", "result_of": action,
                                          "result": _model_result(data.get("result"))}
            continue
        if action == "results_delivered":
            out.extend(deferred.pop(str(turn_id)) for turn_id in data.get("turn_ids") or [] if str(turn_id) in deferred)
            continue
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


WITHDRAWN = "no longer available: this material is now kept for an exam or held out; don't use or cite it"


def revalidate_material(vault: Any, repository: Any, state: LessonState) -> None:
    """Before every model call (review F4): which delivered passages and which brief items are no
    longer teachable as of NOW (protection the lesson's saved context predates). Their text is
    never resent (:func:`_redact`), and a revoked alias can't be cited or read back."""

    from learnloop.learner_protection import withheld_items
    from learnloop.source_retrieval.section_coverage import Library
    from learnloop.teacher.brief import revoke_unteachable

    revoke_unteachable(Library(vault, repository), state.book)
    withheld = withheld_items(vault, repository)
    probes = {str(probe.get("id")) for node in state.brief.get("nodes") or [] for probe in node.get("probes") or []}
    state.withheld_items = {item for item in probes if withheld.reason(item)}


def _redact(value: Any, state: LessonState) -> Any:
    """``value`` with every revoked passage's text and every now-withheld item's stem taken out."""

    if isinstance(value, Mapping):
        alias = value.get("alias")
        if isinstance(alias, str) and alias in state.book.revoked:
            return {"alias": alias, "withdrawn": WITHDRAWN}
        if "stem" in value and str(value.get("id")) in state.withheld_items:
            return {"id": value.get("id"), "withdrawn": WITHDRAWN}
        return {key: _redact(item, state) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item, state) for item in value]
    return value


def _redacted_transcript(state: LessonState) -> list[dict[str, Any]]:
    out = []
    for entry in transcript(state):
        if entry.get("by") == "teacher" and state.book.revoked:
            cited = set(G.CITATION.findall(json.dumps(entry.get("turn"), ensure_ascii=False)))
            if cited & state.book.revoked:
                out.append({"by": "code", "turn_withdrawn": "an earlier turn of yours cited material that is "
                                                            "now kept for an exam or held out; it is left out"})
                continue
        out.append(_redact(entry, state))
    return out


def _prompt(state: LessonState, *, results: Sequence[Mapping[str, Any]], help_reply: bool) -> str:
    context = {
        "brief": _redact(state.brief, state),
        "open_check": state.open_check and {k: state.open_check.get(k) for k in ("check_ref", "check")},
        "open_prediction": state.open_prediction,
        "plan": state.plans[-1]["outline"] if state.plans else None,
        "results": _redact(list(results), state),
        "help_reply": help_reply,
        "transcript": _redacted_transcript(state),
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


def _effect_refs(turn_entry: Mapping[str, Any] | None, effect: str,
                 extra: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
    """The refs marking one effect of an accepted teacher turn (recovery skips what is marked)."""

    refs = dict(extra or {})
    if turn_entry is not None:
        refs.update({"turn": str(turn_entry["id"]), "effect": effect})
    return refs or None


def _model_name(client: Any) -> str | None:
    return getattr(client, "model", None)


def _family_of(model: str | None) -> str:
    """The forecaster of §12.2's pool: the doctrine version and the teacher model."""

    return f"{DOCTRINE_VERSION}:{model or 'unknown'}"


def _family(client: Any) -> str:
    return _family_of(_model_name(client))


# =============================================================================
# Spend: one durable envelope per lesson (§17, T1 redesign D)
# =============================================================================


def _subscription(config: Any, client: Any) -> bool:
    from learnloop.ai.spend import is_subscription_transport

    if is_subscription_transport(client=client):
        return True
    profile = config.ai.providers.get(getattr(client, "provider_name", None) or "")
    return profile is not None and is_subscription_transport(profile=profile)


def _spent_usd(state: LessonState) -> float:
    """What the lesson's metered requests cost so far (each settled request's ``spend`` row)."""

    return float(sum(float((entry.get("payload") or {}).get("usd") or 0.0)
                     for entry in state.turns if entry["action"] == "spend"))


def _lesson_tokens(state: LessonState, outcome: "_Outcome") -> dict[str, int]:
    """The whole lesson's teacher calls and tokens (every action's ``usage`` row, and this action's)."""

    totals = {"calls": 0, "input_tokens": 0, "output_tokens": 0}
    for entry in state.turns:
        usage = (entry.get("payload") or {}).get("usage") if entry["action"] == "usage" else None
        for key in totals:
            totals[key] += int((usage or {}).get(key) or 0)
    for key in totals:
        totals[key] += int(outcome.usage.get(key) or 0)
    return totals


def _spend_gate_class() -> type:
    from learnloop.ai.spend import MeteredRequestGate

    class LessonSpendGate(MeteredRequestGate):
        """The lesson's envelope: every physical metered request of a lesson action (the teacher's,
        the inline grader's, a retrieval call's) is reserved against what the lesson already spent
        before it is sent, and each settled request is written to the ledger (a ``spend`` row), so
        the next action, and the next process, starts from the durable total (review F1)."""

        def __init__(self, repository: Any, state: LessonState, clock: Clock | None, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            self._repository = repository
            self._state = state
            self._clock = clock
            self._purposes: dict[int, str] = {}

        def admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> Any:
            admission = super().admit(client, purpose=purpose, prompt=prompt, budget=budget)
            if admission is not None:
                self._purposes[admission.key] = purpose
            return admission

        def settle(self, admission: Any, usage: Mapping[str, Any]) -> None:
            if admission is None:
                return
            before = self.spent_usd
            super().settle(admission, usage)
            _append(self._repository, self._state, actor="code", action="spend", payload={
                "usd": round(self.spent_usd - before, 10), "estimated_usd": round(admission.estimated_usd, 10),
                "purpose": self._purposes.pop(admission.key, None), "provider": admission.provider,
                "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens"),
            }, clock=self._clock)

    return LessonSpendGate


@contextmanager
def _lesson_spend(vault: Any, repository: Any, state: LessonState, *, clock: Clock | None) -> Iterator[Any]:
    """Hold the lesson's spend gate over one action (every model request it makes)."""

    from learnloop.ai.execution import gate_model_requests
    from learnloop.ai.output_budget import output_budget

    config = vault.config.teacher
    price = config.metered_price_per_million
    gate = _spend_gate_class()(
        repository, state, clock,
        limit_usd=None if config.max_lesson_cost_usd is None else float(config.max_lesson_cost_usd),
        price_per_token=lambda _provider: None if price is None else float(price) / 1_000_000.0,
        is_subscription=lambda client: _subscription(vault.config, client),
        default_output_tokens=int(output_budget(vault.config, "teacher")),
        spent_before_usd=_spent_usd(state))
    state.gate = gate
    try:
        with gate_model_requests(gate):
            yield gate
    finally:
        state.gate = None


def _refused_by_budget(state: LessonState, exc: BaseException) -> bool:
    from learnloop.ai.spend import SpendLimitExceeded

    seen: BaseException | None = exc
    while seen is not None:
        if isinstance(seen, SpendLimitExceeded):
            return True
        seen = seen.__cause__ or seen.__context__
    return state.gate is not None and state.gate.refusal is not None


def _require_metered_settings(vault: Any, client: Any) -> None:
    """A metered (OpenRouter) lesson needs its price and its per-lesson cap first (T1 redesign D; Q7)."""

    if _subscription(vault.config, client) or getattr(client, "provider_type", None) == "fake":
        return
    config = vault.config.teacher
    if config.metered_price_per_million is None or config.max_lesson_cost_usd is None:
        raise LessonError("plan_unavailable", "A lesson on OpenRouter needs teacher.metered_price_per_million and "
                                              "teacher.max_lesson_cost_usd set first.")


# =============================================================================
# Opening
# =============================================================================


def open_lesson(vault: Any, repository: Any, *, entry: str, learning_object_ids: Sequence[str] = (),
                selection: Mapping[str, Any] | None = None, goal_text: str | None = None,
                clients: Clients, driver: str = "desktop", clock: Clock | None = None) -> dict[str, Any]:
    """Open a lesson the learner started (TE1: an LO's or a Reader selection's "Teach me this"), build
    its brief from the ledger and run the teacher's first turn. A failure after the lesson is saved
    carries its id (``LessonError.details``), so the screen resumes it instead of opening another."""

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
    try:
        with _lesson_spend(vault, repository, state, clock=clock):
            return _teach(vault, repository, state, clients=clients, client=client, help_reply=False, clock=clock)
    except LessonError as exc:
        exc.details.setdefault("lesson_id", lesson_id)
        raise


# =============================================================================
# The learner's actions
# =============================================================================


def recover(vault: Any, repository: Any, state: LessonState, *, clock: Clock | None = None,
            reads: bool = True) -> "_Outcome | None":
    """Run what an interrupted action left of its last accepted teacher turn (review F9): each effect
    the ledger does not mark done, idempotently, with its reads' results riding with the next call.
    No teacher call. ``reads=False`` (``lesson.view``, which makes no model call at all) leaves the
    turn's read actions, which may retrieve, for the next action, under its spend envelope."""

    entry = state.unexecuted
    if entry is None or state.closed:
        return None
    data = entry.get("payload") or {}
    turn_obj = TeacherTurnV1.model_validate(data.get("turn") or {})
    outcome = _Outcome()
    done = state.effects_done.setdefault(str(entry["id"]), set())
    _execute(vault, repository, state, turn_obj, turn_entry=entry, model=state.lesson.get("model"), deferred=True,
             outcome=outcome, clock=clock, help_reply=bool(data.get("help_reply")), done=done, reads=reads)
    if str(entry["id"]) in state.executed:
        state.unexecuted = None
    return outcome


def _awaits_teacher(state: LessonState) -> str | None:
    """Whether the ledger's last step is the learner's or code's with no accepted teacher turn after
    it (an action interrupted before the teacher answered): ``"stop"`` for a stop, else ``"turn"``."""

    for entry in reversed(state.turns):
        action = entry["action"]
        if action == "teacher_turn":
            return None if entry["validation"] == "ok" else "turn"
        if action == "learner_stop":
            return "stop"
        if action in ("open", "learner_reply", "prediction_answer", "check_result", "check_withdrawn"):
            return "turn"
    return None


def view_lesson(vault: Any, repository: Any, lesson_id: str, *, clock: Clock | None = None) -> dict[str, Any]:
    """``lesson.view``: the lesson as the screen shows it, after recovering an interrupted action's
    remaining effects (no model call)."""

    require_active(vault)
    state = load_state(repository, lesson_id)
    outcome = recover(vault, repository, state, clock=clock, reads=False)
    return view(vault, repository, lesson_id, outcome=outcome)


def take_turn(vault: Any, repository: Any, *, lesson_id: str, action: str, payload: Mapping[str, Any],
              clients: Clients, clock: Clock | None = None) -> dict[str, Any]:
    """One learner action on an open lesson (``reply``, ``answer_prediction``, ``answer_check``, ``stop``),
    or ``resume``: run the teacher's turn an outage interrupted (nothing new from the learner)."""

    require_active(vault)
    if action not in LEARNER_ACTIONS:
        raise LessonError("validation_error", f"Unknown lesson action {action!r}.")
    state = load_state(repository, lesson_id)
    if state.closed:
        return view(vault, repository, lesson_id)
    try:
        with _lesson_spend(vault, repository, state, clock=clock):
            recover(vault, repository, state, clock=clock)
            if state.closed:
                return view(vault, repository, lesson_id)
            return _learner_action(vault, repository, state, action, payload, clients=clients, clock=clock)
    except LessonError as exc:
        exc.details.setdefault("lesson_id", lesson_id)
        raise


def _learner_action(vault: Any, repository: Any, state: LessonState, action: str, payload: Mapping[str, Any], *,
                    clients: Clients, clock: Clock | None) -> dict[str, Any]:
    if action == "resume":
        waiting = _awaits_teacher(state)
        if waiting is None:
            return view(vault, repository, state.lesson_id)
        return _teach(vault, repository, state, clients=clients, client=clients.teacher(), help_reply=False,
                      clock=clock, closing="learner_stop" if waiting == "stop" else None)
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
        if _refused_by_budget(state, exc):
            # The lesson's envelope refused the grader's request (§17): the lesson closes with ``budget``.
            outcome = _Outcome()
            _close(vault, repository, state, reason="budget", recap=None, clock=clock, outcome=outcome)
            return view(vault, repository, state.lesson_id, outcome=outcome)
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
    # The pool's forecaster is the one that made the forecast being mixed in (its doctrine and model).
    family = str((retained or {}).get("family") or _family_of(state.lesson.get("model")))
    reference = None
    if retained is not None:
        reference = CK.cold_reference(vault, repository, lo, lesson_id=state.lesson_id,
                                      exclude=_lesson_shown(vault, state),
                                      lesson_item_ids=[c["minted_item_id"] for c in state.checks
                                                       if c.get("minted_item_id")])
    mass = CK.check_mass(vault, repository, learning_object_id=lo, tap=tap, hedge=hedge, correctness=correctness,
                         item=item, as_of=as_of, p_teacher_retained=(retained or {}).get("p"), family=family,
                         reference=reference)
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
    """Refresh the DERIVED weight tables after a check (the replayer's own function and bound: through
    the latest answered check, so a rebuild reproduces them row for row)."""

    from learnloop.learner.lesson_weight import replay_state, tables_through, write_state

    with repository.atomic():
        write_state(repository, replay_state(vault, repository, through=tables_through(repository)))


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
    try:
        _teach_loop(vault, repository, state, client=client, help_reply=help_reply, clock=clock, closing=closing,
                    outcome=outcome)
    except Exception as exc:
        if not _refused_by_budget(state, exc):
            raise
        # The lesson's envelope refused the next request (§17): the lesson closes with ``budget``.
        _close(vault, repository, state, reason="budget", recap=None, clock=clock, outcome=outcome)
    finally:
        if outcome.usage["calls"]:
            _append(repository, state, actor="code", action="usage", payload={"usage": dict(outcome.usage)},
                    clock=clock)
    return view(vault, repository, state.lesson_id, outcome=outcome)


def _teach_loop(vault: Any, repository: Any, state: LessonState, *, client: Any, help_reply: bool,
                clock: Clock | None, closing: str | None, outcome: "_Outcome") -> None:
    # Deferred read results ride with this call; they are marked delivered only with the accepted
    # turn that consumed them (review F10), so an outage keeps them pending.
    results = list(state.pending_results)
    undelivered = [str(r.get("turn_id")) for r in results if r.get("turn_id")]
    _require_metered_settings(vault, client)
    # Accepted turns this action: the first one's read requests get one follow-up call; later ones ride with
    # the next learner action (a refused turn does not count, so its correction never defers a read).
    accepted = 0
    if closing:
        results = [*results, {"code": "the learner asked to stop: close the lesson now with a recap"}]
    while not state.closed:
        try:
            parsed = _call_teacher(vault, repository, state, client, results=results, help_reply=help_reply,
                                   outcome=outcome, clock=clock, deliver=undelivered)
        except LessonError:
            raise
        except Exception as exc:  # noqa: BLE001 - the plan is down or the route refused: the lesson waits
            from learnloop.ai.errors import AIProviderUnavailable

            if _refused_by_budget(state, exc):
                raise
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
        undelivered = []
        turn_obj, turn_entry = parsed
        requested_reads = [request for request in turn_obj.requests if request.action in READ_ACTIONS]
        deferred = accepted >= 1
        accepted += 1
        new_results = _execute(vault, repository, state, turn_obj, turn_entry=turn_entry, model=_model_name(client),
                               deferred=deferred, outcome=outcome, clock=clock, help_reply=help_reply)
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


def _record_usage(client: Any, outcome: _Outcome) -> None:
    usage = client.consume_usage() if hasattr(client, "consume_usage") else None
    outcome.usage["calls"] += 1
    if usage is not None:
        outcome.usage["input_tokens"] += int(getattr(usage, "input_tokens", 0) or 0)
        outcome.usage["output_tokens"] += int(getattr(usage, "output_tokens", 0) or 0)


def _displayed(turn_obj: TeacherTurnV1) -> list[tuple[str, str]]:
    """Every learner-facing text of a turn, by field (review F3): the message and its choices, a
    prediction, a check, plan statements (the map) and a close's recap."""

    out: list[tuple[str, str]] = [("message", turn_obj.message)]
    out.extend(("choice", choice) for choice in turn_obj.choices or [])
    if turn_obj.prediction is not None:
        out.append(("prediction", turn_obj.prediction.prompt))
        out.extend(("prediction", choice) for choice in turn_obj.prediction.choices)
    if turn_obj.check is not None:
        out.append(("check", turn_obj.check.question))
        out.extend(("check", choice) for choice in turn_obj.check.choices)
    for request in turn_obj.requests:
        if request.action == "write_plan":
            out.extend(("plan", str(node.statement or "")) for node in request.plan)
        elif request.action == "close" and request.recap:
            out.append(("recap", str(request.recap)))
    return [(name, text) for name, text in out if text]


def _call_teacher(vault: Any, repository: Any, state: LessonState, client: Any, *, results: Sequence[Mapping[str, Any]],
                  help_reply: bool, outcome: _Outcome, clock: Clock | None,
                  deliver: Sequence[str] = ()) -> tuple[TeacherTurnV1, dict[str, Any]] | None:
    """One teacher call: validated, guarded, recorded. None when refused (a correctable error)."""

    from learnloop.ai.errors import AIInvalidOutput

    revalidate_material(vault, repository, state)
    prompt = _prompt(state, results=results, help_reply=help_reply)
    try:
        raw = execute_structured_operation(client, purpose=TEACHER_PURPOSE, prompt=prompt, result_model=TeacherTurnV1)
    except AIInvalidOutput as exc:
        # The provider could not produce a valid TeacherTurnV1 even after its own repair (review F12):
        # a correctable contract refusal, counted toward the consecutive-failure rule.
        _record_usage(client, outcome)
        _append(repository, state, actor="teacher", action="teacher_turn", validation="invalid",
                payload={"reason": "schema", "detail": str(exc)[:2000]}, clock=clock)
        return None
    _record_usage(client, outcome)
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
    displayed = _displayed(turn_obj)
    # The open check's solution guard also covers the check this turn poses: every displayed field but
    # the posed check's own (its options carry the right one by design) must not give the solution away.
    posing = turn_obj.check.model_dump() if turn_obj.check is not None else None
    for name, text in displayed:
        open_check = state.open_check and state.open_check.get("check")
        if open_check is None and posing is not None and name != "check":
            open_check = posing
        verdict = G.check_all(text, keys=keys, unreadable=unreadable, book=state.book,
                              open_check=open_check, help_reply=help_reply)
        if not verdict.ok:
            _append(repository, state, actor="teacher", action="teacher_turn", validation="withheld",
                    payload={"reason": verdict.reason, "detail": f"{name}: {verdict.detail}",
                             "turn": turn_obj.model_dump()}, clock=clock)
            return None
    # One transaction: the delivered results, the accepted turn and its exposure (reveal rows from every
    # displayed field), so an interruption leaves all of it or none.
    with repository.atomic():
        if deliver:
            _append(repository, state, actor="code", action="results_delivered", payload={"turn_ids": list(deliver)},
                    clock=clock)
        entry = _append(repository, state, actor="teacher", action="teacher_turn", validation="ok",
                        payload={"turn": turn_obj.model_dump(), "turn_version": TURN_VERSION,
                                 "help_reply": bool(help_reply)}, clock=clock)
        _record_reveals(vault, repository, state, "\n".join(text for _name, text in displayed), clock=clock)
    if deliver:
        delivered = set(deliver)
        state.pending_results = [r for r in state.pending_results if str(r.get("turn_id")) not in delivered]
    if turn_obj.message:
        outcome.shown.append({"kind": "message", "text": turn_obj.message, "choices": list(turn_obj.choices)})
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
        unknown = [alias for alias in check.anchors if not state.book.available(alias)]
        if unknown:
            return f"the check's anchors were never delivered to you: {', '.join(unknown)}"
    for request in turn_obj.requests:
        if request.action == "write_plan":
            for node in request.plan:
                unknown = [alias for alias in node.anchors
                           if not state.book.available(alias) and alias not in state.book.sections]
                if unknown:
                    return f"plan node {node.id}: these anchors don't resolve: {', '.join(unknown)}"
        if request.action == "forecast" and (request.forecast_kind is None or request.p is None or not request.node):
            return "a forecast needs forecast_kind, node and p"
        if request.action == "close" and request.close_reason is None:
            return "close needs a close_reason"
    if not turn_obj.message and turn_obj.check is None and turn_obj.prediction is None and not turn_obj.requests:
        return "the turn is empty"
    return None


def _record_reveals(vault: Any, repository: Any, state: LessonState, message: str, *, clock: Clock | None) -> None:
    """Teaching text and cited passages (§12): ``tutor_answer`` for each item on the lesson's LOs whose key
    the text overlaps (amount = overlap, as the tutor), ``source_review`` for what a cited passage exposes;
    basis ``lesson:<id>``. The lesson's own check items are the attempts themselves, not reveals."""

    from learnloop.attempts.reveal_ledger import record_reveal
    from learnloop.tutor.tutor_qa import answer_leak_overlap, span_answer_overlap

    if not message:
        return
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
              outcome: _Outcome, turn_entry: Mapping[str, Any] | None = None) -> None:
    from learnloop.vault.loader import load_vault

    assert state.open_check is not None
    check = state.open_check
    loaded = vault if check["item_id"] in vault.practice_items else load_vault(vault.root)
    item = loaded.practice_items[check["item_id"]]
    with repository.atomic():
        CK.withdraw_check(repository, lesson_id=state.lesson_id, node_id=str(check["check"]["node"]),
                          check_ref=check["check_ref"], item=item, overlap=overlap, created_at=utc_now_iso(clock))
        _append(repository, state, actor="code", action="check_withdrawn",
                refs=_effect_refs(turn_entry, "withdraw", {"item": item.id}),
                payload={"check_ref": check["check_ref"], "overlap": overlap}, clock=clock)
    state.open_check = None
    outcome.notices.append("That reply gave the check's answer away, so the check was withdrawn; it doesn't count "
                           "either way.")


# =============================================================================
# The actions
# =============================================================================


def _execute(vault: Any, repository: Any, state: LessonState, turn_obj: TeacherTurnV1, *,
             turn_entry: Mapping[str, Any], model: str | None, deferred: bool, outcome: _Outcome,
             clock: Clock | None, help_reply: bool, done: set[str] | frozenset[str] = frozenset(),
             reads: bool = True) -> list[dict[str, Any]]:
    """An accepted turn's effects, in order, each marked with the turn and its name (``refs.effect``) in
    the transaction that makes it, then a ``turn_executed`` marker: recovery runs only what is unmarked
    (``done``), so an interrupted action resumes idempotently (review F9)."""

    results: list[dict[str, Any]] = []
    skipped = False
    if "withdraw" not in done and help_reply and state.open_check is not None:
        overlap = G.solution_overlap(turn_obj.message, str(state.open_check["check"]["committed_solution"]))
        from learnloop.serve_eligibility import AUTO_PRIME_REVEAL_THRESHOLD

        if overlap >= AUTO_PRIME_REVEAL_THRESHOLD:
            _withdraw(vault, repository, state, overlap=overlap, clock=clock, outcome=outcome, turn_entry=turn_entry)
    if turn_obj.prediction is not None and "prediction" not in done:
        data = turn_obj.prediction.model_dump()
        _append(repository, state, actor="teacher", action="pose_prediction",
                refs=_effect_refs(turn_entry, "prediction"), payload=data, clock=clock)
        state.open_prediction = data
        outcome.shown.append({"kind": "prediction", **data})
    if turn_obj.check is not None and "check" not in done:
        _pose_check(vault, repository, state, turn_obj.check, outcome=outcome, clock=clock, turn_entry=turn_entry)
    for index, request in enumerate(turn_obj.requests):
        effect = f"request:{index}"
        if effect in done:
            continue
        if request.action in READ_ACTIONS and not reads:
            skipped = True
            continue
        if request.action in READ_ACTIONS:
            result = _read_action(vault, repository, state, request, model=model)
            extra = {"tool_call": result.get("tool_call_id")} if result.get("tool_call_id") else None
            entry = _append(repository, state, actor="code", action=request.action,
                            refs=_effect_refs(turn_entry, effect, extra),
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
                _append(repository, state, actor="code", action="write_plan", refs=_effect_refs(turn_entry, effect),
                        payload={"version": version}, clock=clock)
            state.plans.append({"version": version, "outline": outline})
        elif request.action == "forecast":
            _forecast(vault, repository, state, request, model=model, clock=clock, turn_entry=turn_entry,
                      effect=effect)
        elif request.action == "close":
            _close(vault, repository, state, reason=str(request.close_reason), recap=request.recap, clock=clock,
                   outcome=outcome, turn_entry=turn_entry, effect=effect)
            break
    if skipped:
        return results
    _append(repository, state, actor="code", action="turn_executed", payload={"turn_id": str(turn_entry["id"])},
            clock=clock)
    state.executed.add(str(turn_entry["id"]))
    return results


def _pose_check(vault: Any, repository: Any, state: LessonState, check: CheckV1, *, outcome: _Outcome,
                clock: Clock | None, turn_entry: Mapping[str, Any] | None = None) -> None:
    lo = state.node_lo(check.node)
    if lo is None or lo not in vault.learning_objects:
        lo = (state.brief.get("goal") or {}).get("learning_object_ids", [None])[0]
    check_ref = f"c{len(state.minted) + 1}"
    # Idempotent: the item id is the lesson's and the check ref's (a recovered pose rewrites the same file).
    item_id = CK.mint_check_item(Path(vault.root), lesson_id=state.lesson_id, check_ref=check_ref, check=check,
                                 learning_object_id=str(lo), book=state.book, clock=clock)
    data = {"check_ref": check_ref, "item_id": item_id, "learning_object_id": lo, "check": check.model_dump()}
    _append(repository, state, actor="teacher", action="pose_check",
            refs=_effect_refs(turn_entry, "check", {"item": item_id}), payload=data, clock=clock)
    state.minted[check_ref] = item_id
    state.open_check = data
    outcome.vault_changed = True
    outcome.shown.append({"kind": "check", "check_ref": check_ref, "node": check.node, "question": check.question,
                          "form": check.form, "choices": list(check.choices),
                          "unanchored": not bool(check.anchors)})


def _read_action(vault: Any, repository: Any, state: LessonState, request: ActionRequestV1, *,
                 model: str | None) -> dict[str, Any]:
    from learnloop.teacher import actions as A

    try:
        return A.run_read(vault, repository, state, request, model=model)
    except A.ActionRefused as exc:
        return {"refused": exc.code, "message": str(exc)}


def _forecast(vault: Any, repository: Any, state: LessonState, request: ActionRequestV1, *, model: str | None,
              clock: Clock | None, turn_entry: Mapping[str, Any] | None = None, effect: str = "forecast") -> None:
    from learnloop.scheduling.forecast_receipts import (
        LESSON_CHECK_ATTEMPT,
        LESSON_COLD_OUTCOME,
        ForecastReceipt,
        record_receipts,
    )
    from learnloop.teacher.brief import lo_prediction

    kind = str(request.forecast_kind)
    node = str(request.node)
    family = _family_of(model)
    now = utc_now_iso(clock)
    if kind == "lesson_check_correct":
        ref = state.open_check["check_ref"] if state.open_check is not None else node
        lo = (state.open_check or {}).get("learning_object_id") or state.node_lo(node)
        inputs = {"lesson_id": state.lesson_id, "check_ref": ref, "learning_object_id": lo, "family": family}
        scope, binding, event = "lesson_check", LESSON_CHECK_ATTEMPT, "lesson_check_correct"
        node = ref
    else:
        lo = state.node_lo(node)
        p_a, recorded, reference = (lo_prediction(vault, repository, lo).get("p") if lo else None), None, None
        if lo and lo in vault.learning_objects:
            # p_A for the committed cold item at its horizon (§12.2; review F5), from the LO's state now;
            # the state rides with the receipt so the pool scores p_A for the item that resolves it.
            from learnloop.learner.lesson_weight import predicted_success

            reference = CK.cold_reference(vault, repository, lo, lesson_id=state.lesson_id,
                                          exclude=_lesson_shown(vault, state),
                                          lesson_item_ids=[c["minted_item_id"] for c in state.checks
                                                           if c.get("minted_item_id")])
            row = repository.mastery_state(lo)
            if row is not None:
                recorded = {"mu": float(row.logit_mean), "variance": float(row.logit_variance),
                            "last_evidence_at": row.last_evidence_at}
                p_a = predicted_success(recorded["mu"], recorded["variance"], a=reference["a"], b=reference["b"],
                                        drift=float(vault.config.mastery.sigma2_drift), days=reference["days"])
        inputs = {"lesson_id": state.lesson_id, "node_id": node, "learning_object_id": lo, "family": family,
                  "p_a": p_a, "state": recorded, "reference": reference}
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
    data = {"key": key, "kind": kind, "node": node, "p": float(request.p), "learning_object_id": lo,
            "family": family}
    with repository.atomic():
        written = record_receipts(repository, [receipt], vault=vault, clock=clock, created_at=now)
        data["written"] = bool(written)
        _append(repository, state, actor="code", action="forecast", refs=_effect_refs(turn_entry, effect),
                payload=data, clock=clock)
    state.forecasts[key] = data
    if kind == "lesson_step_retained":
        state.landed.append(str(request.node))


# =============================================================================
# Closing
# =============================================================================


def _close(vault: Any, repository: Any, state: LessonState, *, reason: str, recap: str | None, clock: Clock | None,
           outcome: _Outcome, turn_entry: Mapping[str, Any] | None = None, effect: str = "close") -> None:
    """Close the lesson: commit the delayed checks, write the receipt, close the row and append the close
    entry in one transaction (§7 step 7; review F9: never a closed row without its close entry)."""

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
    shown = D.shown_vault_items(loaded, displayed_texts(state, extra=[recap] if recap else []))
    delayed_checks: list[dict[str, Any]] = []
    warnings: list[str] = []
    now = utc_now_iso(clock)
    with repository.atomic():
        if reason in ("goal_reached", "learner_stop", "budget", "teacher_contract_failure", "plan_unavailable"):
            delayed_checks, warnings = D.commit_checks(
                loaded, repository, lesson_id=state.lesson_id, landed=landed,
                goal_learning_object_ids=(state.brief.get("goal") or {}).get("learning_object_ids") or [],
                lesson_items_by_lo=lesson_items_by_lo, shown_items=[*state.minted.values(), *shown],
                taught_learning_objects=[node["lo_id"] for node in landed if node.get("lo_id")], clock=clock)
        receipt = _receipt(loaded, repository, state, reason=reason, recap=recap, delayed_checks=delayed_checks,
                           warnings=warnings, landed=landed, rows=rows, usage=_lesson_tokens(state, outcome),
                           shown_items=shown)
        connection = repository.connection()
        store.insert_receipt(connection, lesson_id=state.lesson_id, version=RECEIPT_VERSION, close_reason=reason,
                             receipt=receipt, created_at=now)
        store.close_lesson(connection, state.lesson_id, reason=reason, closed_at=now)
        _append(repository, state, actor="code", action="close",
                refs=_effect_refs(turn_entry, effect,
                                  {"commitments": [c["commitment_id"] for c in delayed_checks if c.get("commitment_id")]}),
                payload={"reason": reason, "recap": recap, "delayed_checks": delayed_checks}, clock=clock)
    state.lesson["closed_at"], state.lesson["close_reason"] = now, reason
    outcome.shown.append({"kind": "close", "reason": reason, "recap": recap,
                          "delayed_checks": [c for c in delayed_checks if c.get("commitment_id")]})


def _lesson_shown(vault: Any, state: LessonState) -> list[str]:
    """The lesson's own check items and the vault items its displayed text reproduced so far."""

    from learnloop.teacher import delayed as D

    return [*state.minted.values(), *D.shown_vault_items(vault, displayed_texts(state))]


def displayed_texts(state: LessonState, *, extra: Sequence[str] = ()) -> list[str]:
    """Everything the lesson displayed to the learner so far (accepted turns' fields), and ``extra``."""

    out: list[str] = []
    for entry in state.turns:
        if entry["action"] == "teacher_turn" and entry["validation"] == "ok":
            turn = (entry.get("payload") or {}).get("turn")
            if turn:
                out.extend(text for _name, text in _displayed(TeacherTurnV1.model_validate(turn)))
    out.extend(text for text in extra if text)
    return out


def _receipt(vault: Any, repository: Any, state: LessonState, *, reason: str, recap: str | None,
             delayed_checks: Sequence[Mapping[str, Any]], warnings: Sequence[str], landed: Sequence[Mapping[str, Any]],
             rows: Sequence[Mapping[str, Any]], usage: Mapping[str, int],
             shown_items: Sequence[str] = ()) -> dict[str, Any]:
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
                     "passages": sorted(state.book.passages), "shown_items": list(shown_items)},
        "gaps": [],
        "created_los": [],
        "delayed_checks": list(delayed_checks),
        "forecasts": sorted(state.forecasts),
        "weight_inputs": weight_inputs,
        "stability_inputs": stability_inputs,
        "origin": state.lesson.get("origin"),
        # The whole lesson (every action's teacher calls; every metered request's settled cost).
        "cost": {**dict(usage), "route": state.lesson.get("route"), "metered_usd": round(_spent_usd(state), 10),
                 "cap_usd": vault.config.teacher.max_lesson_cost_usd},
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

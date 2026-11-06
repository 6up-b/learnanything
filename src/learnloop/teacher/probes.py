"""Teacher TE2: probes inside a lesson (spec_teacher_v1 rev 5 §11.3, §9 ``serve_probe``, §9.1, §11.9, §18.2).

``serve_probe {node, readings, p}`` asks LearnLoop for one question, written for this learner, served cold:

1. **The request** (:func:`request`), in one transaction with the accepted turn's other effects: a ``serve_probe``
   ledger entry (the readings' words, after the output guards; the probe's ref and the attempt id minted now), the
   ``lesson_probe_correct`` forecast receipt (bound to that attempt id, so written BEFORE the probe can be served),
   FG1's generation job (kind ``lesson``, deduplicated on (lesson, node)) and one ``probe`` episode row (TE2-log's
   log, behind ``teacher.episode_log``).
2. **Generation** is FG1's authoring operation on the frontier route, in the background worker
   (``learnloop.followup_run.lesson_probe``); it reports back through :func:`record_ready` (the item, FG1's
   single-use identity with ``source = 'lesson'``, and its admission receipt) or :func:`record_refused` (why no
   question: a reserved-question match, protection unreadable, not admitted, the route, its two runs failed).
3. **Serving** (:func:`serve`): when the lesson shows a ready probe, FG1's atomic first-serve claim burns it (surface
   ``lesson``) and the question opens like any cold question: no sources, no tutor, the teacher silent (§9.1
   ``cold_attempt``: no teacher call is made and no read action runs until the grade is back).
4. **The answer** (:func:`record_answer`): the blind grader sees the answer only; one ``diagnostic_probe`` attempt
   through the attempts path (full evidence under the existing admissibility rule), its independence read from the
   reveal ledger's topic-wide check (an answer after the lesson showed text on the topic is recorded as not
   independent, as FG1 records an exposed probe answer), then the item is retired so no door ever opens it again.
5. **Retired unused** (:func:`retire`) on "Teach it anyway" or at the lesson's close: its queued job never runs, a
   generated item is retired, a late generator's item is retired when it lands.

A probe's readings are not ``causal_hypotheses`` rows: they live in the lesson's payloads and its episode row, and a
lesson probe never resolves a cause factor. Ids, enums and numbers only in every row.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.stores import lessons as store
from learnloop.ids import new_ulid

#: The ledger's probe steps (``lesson_turns.action``).
REQUEST = "serve_probe"
READY = "probe_ready"
REFUSED = "probe_refused"
SERVED = "probe_served"
ANSWER = "probe_answer"
RESULT = "probe_result"
RETIRED = "probe_retired"
#: Why a probe was not prepared (``lesson_episodes.refusal_reason``, migration 248).
REFUSAL_REASONS: tuple[str, ...] = ("reserved_match", "protection_unavailable", "not_admitted", "generation_failed",
                                    "route_unavailable", "lesson_closed", "switch_off")
ATTEMPT_TYPE = "diagnostic_probe"
ENTRY_SURFACE = "lesson"
EVIDENCE_ORIGIN = "lesson_probe"
#: What the learner reads (code-owned words, no jargon).
PREPARING = "Preparing a question on this…"
NOT_PREPARED = "couldn't prepare that question"


@dataclass
class Probe:
    """One probe of a lesson, read back from its ledger."""

    ref: str
    node: str
    learning_object_id: str | None
    readings: list[str]
    p: float
    attempt_id: str
    forecast_key: str | None
    requested_by: str
    status: str = "preparing"  # preparing | ready | served | answered | refused | retired
    item_id: str | None = None
    reason: str | None = None
    result: dict[str, Any] = field(default_factory=dict)

    @property
    def unanswered(self) -> bool:
        return self.status in ("preparing", "ready", "served")


def probes(turns: Sequence[Mapping[str, Any]]) -> list[Probe]:
    """Every probe of a lesson, in request order, with its current status."""

    out: dict[str, Probe] = {}
    for entry in turns:
        data = entry.get("payload") or {}
        action = entry["action"]
        ref = str(data.get("probe_ref") or "")
        if action == REQUEST and ref:
            out[ref] = Probe(ref=ref, node=str(data.get("node")), learning_object_id=data.get("learning_object_id"),
                             readings=[str(text) for text in data.get("readings") or []], p=float(data.get("p") or 0.0),
                             attempt_id=str(data.get("attempt_id")), forecast_key=data.get("forecast_key"),
                             requested_by=str(entry["id"]))
            continue
        probe = out.get(ref)
        if probe is None:
            continue
        if action == READY and probe.status == "preparing":
            probe.status, probe.item_id = "ready", str(data.get("item_id"))
        elif action == REFUSED and probe.status == "preparing":
            probe.status, probe.reason = "refused", str(data.get("reason") or "not_admitted")
        elif action == SERVED and probe.status in ("ready", "served"):
            probe.status = "served"
        elif action == RESULT:
            probe.status, probe.result = "answered", dict(data)
        elif action == RETIRED and probe.unanswered:
            probe.status, probe.reason = "retired", str(data.get("reason") or "")
    return list(out.values())


def unanswered(turns: Sequence[Mapping[str, Any]]) -> Probe | None:
    return next((probe for probe in probes(turns) if probe.unanswered), None)


def open_probe(turns: Sequence[Mapping[str, Any]]) -> Probe | None:
    """The probe being answered (served, no answer yet): the teacher is silent until its grade is back."""

    return next((probe for probe in probes(turns) if probe.status == "served"), None)


# =============================================================================
# The request (the accepted turn's effect)
# =============================================================================


def contract_problem(vault: Any, state: Any, turn_obj: Any, index: int, request: Any) -> str | None:
    """A correctable problem with a ``serve_probe`` request, named by location (never by text), or None."""

    from learnloop.teacher import episodes as E

    at = f"requests[{index}]"
    readings = [str(text).strip() for text in getattr(request, "readings", None) or []]
    if not request.node or request.p is None or not readings or any(not text for text in readings):
        return f"{at}: serve_probe needs node, one to four readings and p"
    if not E.node_known(state, turn_obj, str(request.node)):
        return f"{at}.node: not a node of your plan; name one of the plan's node ids"
    if E.node_lo(vault.learning_objects, state, turn_obj, str(request.node)) is None:
        return f"{at}.node: a probe needs a node on one of the lesson's topics (its lo_id)"
    if state.open_check is not None or turn_obj.check is not None:
        return f"{at}: a check is open; ask for a question before or after it, not during it"
    known = probes(state.turns)
    if any(probe.unanswered for probe in known) or sum(1 for r in turn_obj.requests if r.action == REQUEST) > 1:
        return f"{at}: a question is already being prepared or answered; wait for it"
    if any(probe.node == str(request.node) for probe in known):
        return f"{at}.node: this node already had its question; one question per node"
    if len(known) >= int(vault.config.teacher.placement.max_probes):
        return f"{at}: this lesson has asked all the questions it may ({vault.config.teacher.placement.max_probes})"
    return None


def logged_fields(turn_obj: Any) -> list[tuple[str, str]]:
    """``(location, text)`` of a TE2 request's words a ledger entry or a row keeps: a probe's readings and node, a
    gap's words and ref. They pass the output guards and the identifier guard before the turn is accepted."""

    out: list[tuple[str, str]] = []
    for index, request in enumerate(getattr(turn_obj, "requests", None) or []):
        at = f"requests[{index}]"
        if request.action == REQUEST:
            out.append((f"{at}.node", str(request.node or "")))
            out.extend((f"{at}.readings[{position}]", str(text or ""))
                       for position, text in enumerate(getattr(request, "readings", None) or []))
        elif request.action == "propose_gap":
            out.append((f"{at}.gap", str(getattr(request, "gap", None) or "")))
            out.append((f"{at}.ref", str(getattr(request, "ref", None) or "")))
    return [(location, text) for location, text in out if text]


def request(vault: Any, repository: Any, state: Any, turn_obj: Any, req: Any, *, append: Callable[..., Any],
            effect_refs: Mapping[str, Any] | None, family: str, prompt: str, doctrine: str, model: str | None,
            clock: Clock | None) -> dict[str, Any]:
    """The probe's request: the ledger entry, the forecast receipt (before any serve), the generation job and the
    episode row, in the caller's transaction. Returns the entry's payload."""

    from learnloop.followup_serve import queue
    from learnloop.scheduling.forecast_receipts import (
        LESSON_PROBE_ATTEMPT,
        LESSON_PROBE_CORRECT,
        ForecastReceipt,
        record_receipts,
    )
    from learnloop.teacher import episodes as E

    node = str(req.node)
    lo = E.node_lo(vault.learning_objects, state, turn_obj, node)
    ref = f"p{len(probes(state.turns)) + 1}"
    attempt_id = new_ulid()
    readings = [" ".join(str(text).split()) for text in req.readings]
    p = float(req.p)
    now = utc_now_iso(clock)
    key = f"{LESSON_PROBE_CORRECT}:{state.lesson_id}:{ref}"
    receipt = ForecastReceipt(
        receipt_key=key, kind=LESSON_PROBE_CORRECT, forecaster="teacher", forecaster_version=family,
        scope="lesson_probe", decision_kind="lesson", binding_kind=LESSON_PROBE_ATTEMPT, event="lesson_probe_correct",
        forecast={"emission_alphabet": ["success", "failure"],
                  "predicted_outcomes": {"success": round(p, 8), "failure": round(1.0 - p, 8)}},
        inputs={"lesson_id": state.lesson_id, "probe_ref": ref, "node_id": node, "learning_object_id": lo,
                "attempt_id": attempt_id, "readings": len(readings), "family": family},
        parameters=[{"name": "p", "value": p, "provenance": "model"}],
        versions={"doctrine": doctrine, "prompt": prompt}, inputs_as_of=now, p=p,
        columns={"decision_ref": state.lesson_id, "learning_object_id": lo})
    written = record_receipts(repository, [receipt], vault=vault, clock=clock, created_at=now)
    job_id = queue.enqueue_lesson(repository, state.lesson_id, node, clock=clock)
    data = {"probe_ref": ref, "node": node, "learning_object_id": lo, "readings": readings, "p": p,
            "attempt_id": attempt_id, "forecast_key": key if written else None, "generation_job_id": job_id,
            "model": model}
    entry = append(actor="teacher", action=REQUEST, refs=effect_refs, payload=data)
    if E.on(vault):
        E.open_episode(repository, lesson=state.lesson, brief=state.brief, kind="probe", opened_by=str(entry["id"]),
                       opened_at=now, node_id=node, learning_object_id=lo, hypotheses=readings,
                       hypothesis_payload_id=str(entry["id"]), teacher_p=p,
                       teacher_forecast_receipt_id=key if written else None, refs={"generation_job_id": job_id})
    return data


# =============================================================================
# The worker's report (followup_run.lesson_probe)
# =============================================================================


def _probe_of(connection: Any, lesson_id: str, node_id: str) -> tuple[dict[str, Any] | None, Probe | None]:
    lesson = store.lesson(connection, lesson_id)
    if lesson is None:
        return None, None
    turns = store.turns(connection, lesson_id)
    return lesson, next((probe for probe in probes(turns) if probe.node == node_id), None)


def pending_request(repository: Any, lesson_id: str, node_id: str) -> tuple[dict[str, Any] | None, Probe | None]:
    """The lesson and its probe on ``node_id`` (the worker's read), or Nones."""

    with repository.connection() as connection:
        return _probe_of(connection, lesson_id, node_id)


def record_ready(vault: Any, repository: Any, *, lesson_id: str, node_id: str, item_id: str,
                 receipt: Mapping[str, Any], clock: Clock | None = None) -> bool:
    """The generated question is admitted: its ``probe_ready`` entry with the admission receipt. A late generator
    (the probe was retired, or its lesson closed, while the model wrote) retires the item at once: it is never
    served. Returns whether the probe can now be served."""

    from learnloop.followup_serve import identity

    with repository.atomic():
        connection = repository.connection()
        lesson, probe = _probe_of(connection, lesson_id, node_id)
        if lesson is None or probe is None or probe.status != "preparing" or lesson.get("closed_at") is not None:
            identity.retire(repository, item_id, reason="lesson_probe_unused", clock=clock)
            return False
        store.append_turn(connection, lesson_id=lesson_id, actor="code", action=READY, validation="ok",
                          refs={"item": item_id}, payload={"probe_ref": probe.ref, "item_id": item_id,
                                                           "admission": dict(receipt)},
                          created_at=utc_now_iso(clock))
    return True


def record_refused(vault: Any, repository: Any, *, lesson_id: str, node_id: str, reason: str,
                   clock: Clock | None = None) -> bool:
    """No question passed: the ``probe_refused`` entry and its episode closed ``refused`` with the reason. The
    teacher is told "couldn't prepare that question"."""

    from learnloop.teacher import episodes as E

    reason = reason if reason in REFUSAL_REASONS else "not_admitted"
    now = utc_now_iso(clock)
    with repository.atomic():
        connection = repository.connection()
        lesson, probe = _probe_of(connection, lesson_id, node_id)
        if lesson is None or probe is None or probe.status != "preparing":
            return False
        store.append_turn(connection, lesson_id=lesson_id, actor="code", action=REFUSED, validation="ok", refs={},
                          payload={"probe_ref": probe.ref, "reason": reason}, created_at=now)
        if E.on(vault):
            _close_episode(repository, lesson_id, probe, closed_at=now, reason="refused",
                           outcome={"refusal_reason": reason})
    return True


def _close_episode(repository: Any, lesson_id: str, probe: Probe, *, closed_at: str, reason: str,
                   outcome: Mapping[str, Any]) -> None:
    """Close the probe's own episode row (opened by its request), once."""

    from learnloop.teacher import episodes as E

    fields = dict(outcome)
    if probe.item_id and "generated_item_id" not in fields:
        fields["generated_item_id"] = probe.item_id
    E.close_one(repository, lesson_id, probe.requested_by, closed_at=closed_at, reason=reason, outcome=fields)


# =============================================================================
# Serving, answering, retiring (the lesson's own steps)
# =============================================================================


def serve(vault: Any, repository: Any, lesson: Mapping[str, Any], turns: Sequence[Mapping[str, Any]], *,
          clock: Clock | None = None) -> dict[str, Any] | None:
    """The question the screen may show now: a served probe again (the same administration), or a ready one served
    now (FG1's atomic first-serve claim, surface ``lesson``, and its ``probe_served`` entry, before any text leaves).
    None when no probe is open or ready, the lesson is closed, or the claim is refused (then the probe is retired).
    Only the question: never its key or rubric."""

    from learnloop.followup_serve import identity
    from learnloop.teacher.te2 import LESSON_SURFACE
    from learnloop.vault.loader import load_vault

    if lesson.get("closed_at") is not None:
        return None
    probe = next((p for p in probes(turns) if p.status in ("served", "ready")), None)
    if probe is None or not probe.item_id:
        return None
    loaded = vault if probe.item_id in vault.practice_items else load_vault(vault.root)
    item = loaded.practice_items.get(probe.item_id)
    claim = identity.claim_serve(repository, probe.item_id, surface=LESSON_SURFACE, presentation_id=None,
                                 reason="lesson_first_serve", clock=clock)
    if item is None or not claim.granted:
        retire(vault, repository, lesson, turns, probe, reason="not_servable", clock=clock)
        return None
    if probe.status == "ready":
        with repository.atomic():
            store.append_turn(repository.connection(), lesson_id=str(lesson["id"]), actor="code", action=SERVED,
                              validation="ok", refs={"item": probe.item_id},
                              payload={"probe_ref": probe.ref, "item_id": probe.item_id, "first": bool(claim.first)},
                              created_at=utc_now_iso(clock))
    return {"probe_ref": probe.ref, "node": probe.node, "question": item.prompt, "item_id": probe.item_id}


def retire(vault: Any, repository: Any, lesson: Mapping[str, Any], turns: Sequence[Mapping[str, Any]],
           probe: Probe, *, reason: str, clock: Clock | None = None) -> None:
    """Retire an unanswered probe unused ("Teach it anyway", the lesson's close, an unservable item): its queued job
    is skipped, a generated item retired (FG1's ledger: no door opens it again), a ``probe_retired`` entry, and its
    episode closed ``retired``."""

    from learnloop.followup_serve import identity, queue
    from learnloop.teacher import episodes as E

    if not probe.unanswered:
        return
    now = utc_now_iso(clock)
    lesson_id = str(lesson["id"])
    queue.skip_lesson_job(repository, lesson_id, probe.node, reason=reason, clock=clock)
    if probe.item_id:
        identity.retire(repository, probe.item_id, reason=f"lesson_{reason}", clock=clock)
    with repository.atomic():
        store.append_turn(repository.connection(), lesson_id=lesson_id, actor="code", action=RETIRED, validation="ok",
                          refs={"item": probe.item_id} if probe.item_id else {},
                          payload={"probe_ref": probe.ref, "reason": reason}, created_at=now)
    if E.on(vault):
        _close_episode(repository, lesson_id, probe, closed_at=now, reason="retired", outcome={})


def record_answer(vault: Any, repository: Any, lesson: Mapping[str, Any], probe: Probe, *, answer: str,
                  tap: int | None, grading_client: Any, grading_source: str,
                  clock: Clock | None = None) -> dict[str, Any]:
    """The learner's answer to the open probe: blind-graded (the answer only), one ``diagnostic_probe`` attempt at
    full evidence through the attempts path, its independence from the reveal ledger's topic-wide check, the item
    retired (never served again), the ``probe_result`` entry and the episode closed ``answered``. Returns the
    result as the teacher and the screen read it."""

    from learnloop.attempts.attempts import ApplyAttemptInput, AttemptDraft, apply_attempt
    from learnloop.attempts.grading import vault_grading_calibration_identity
    from learnloop.attempts.reveal_ledger import production_admissibility
    from learnloop.followup_serve import identity
    from learnloop.teacher import checks as CK
    from learnloop.teacher import episodes as E
    from learnloop.vault.loader import load_vault

    loaded = vault if probe.item_id in vault.practice_items else load_vault(vault.root)
    item = loaded.practice_items[str(probe.item_id)]
    grade, run_id = CK.grade_answer(loaded, repository, grading_client, item=item, attempt_id=probe.attempt_id,
                                    answer=answer, clock=clock)
    now = utc_now_iso(clock)
    # The reveal ledger's topic-wide check, as of this answer (FG1 records an exposed probe answer the same way).
    independence = production_admissibility(repository, practice_item_id=item.id,
                                             learning_object_id=item.learning_object_id, produced_at=now, clock=clock)
    max_points = max(int(getattr(loaded.rubric_for_item(item), "max_points", 1) or 1), 1)
    correctness = max(0.0, min(1.0, float(grade.rubric_score) / max_points))
    with repository.atomic():
        apply_attempt(loaded, repository, ApplyAttemptInput(
            draft=AttemptDraft(practice_item_id=item.id, learner_answer_md=answer, attempt_type=ATTEMPT_TYPE,
                               hints_used=0, answer_confidence=tap, entry_surface=ENTRY_SURFACE,
                               evidence_origin=EVIDENCE_ORIGIN, awaits_completion=False),
            attempt_id=probe.attempt_id, grade=grade, grading_source=grading_source, grading_agent_run_id=run_id,
            grader_identity=vault_grading_calibration_identity(loaded),
        ), clock=clock)
    identity.retire(repository, item.id, reason="lesson_probe_answered", clock=clock)
    result = {"probe_ref": probe.ref, "node": probe.node, "attempt_id": probe.attempt_id, "item_id": item.id,
              "correctness": correctness,
              "result": "right" if correctness >= 1.0 else ("wrong" if correctness <= 0.0 else "partly right"),
              "grader_feedback": grade.feedback_md, "independent": bool(independence.admissible),
              "independence": independence.reason}
    with repository.atomic():
        store.append_turn(repository.connection(), lesson_id=str(lesson["id"]), actor="code", action=RESULT,
                          validation="ok", refs={"attempt": probe.attempt_id, "item": item.id}, payload=result,
                          created_at=now)
    if E.on(vault):
        _close_episode(repository, str(lesson["id"]), probe, closed_at=now, reason="answered",
                       outcome={"outcome_attempt_id": probe.attempt_id, "outcome_correctness": correctness})
    return result


def transcript_entry(entry: Mapping[str, Any]) -> dict[str, Any] | None:
    """A probe step as the teacher reads it (TE2 lessons only), or None: never the question's key or rubric."""

    data = entry.get("payload") or {}
    action = entry["action"]
    if action == REQUEST:
        return {"by": "code", "probe_requested": {k: data.get(k) for k in ("probe_ref", "node", "p")}}
    if action == READY:
        return {"by": "code", "probe_ready": data.get("probe_ref")}
    if action == REFUSED:
        return {"by": "code", "probe_not_prepared": {"probe_ref": data.get("probe_ref"), "why": NOT_PREPARED}}
    if action == SERVED:
        return {"by": "code", "probe_opened": data.get("probe_ref"),
                "note": "the learner is answering it on their own; you are silent until its grade is back"}
    if action == RESULT:
        return {"by": "code", "probe_result": {k: data.get(k) for k in (
            "probe_ref", "node", "result", "correctness", "grader_feedback", "independent")}}
    if action == RETIRED:
        return {"by": "code", "probe_retired": data.get("probe_ref"),
                "why": ("the learner chose to be taught without it" if data.get("reason") == "teach_anyway"
                        else "it was not asked")}
    if action == ANSWER:
        return {"by": "learner", "probe_answer": data.get("answer"), "probe_ref": data.get("probe_ref"),
                "confidence_tap": data.get("tap")}
    return None


__all__ = [
    "ANSWER", "ATTEMPT_TYPE", "NOT_PREPARED", "PREPARING", "Probe", "READY", "REFUSAL_REASONS", "REFUSED", "REQUEST",
    "RESULT", "RETIRED", "SERVED", "contract_problem", "logged_fields", "open_probe", "pending_request", "probes",
    "record_answer", "record_ready", "record_refused", "request", "retire", "serve", "transcript_entry", "unanswered",
]

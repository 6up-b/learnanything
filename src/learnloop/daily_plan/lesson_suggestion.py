"""Teacher TE1b: Today's lesson suggestion card (spec_teacher_v1 §15.1, §19).

The imperative shell around :mod:`learnloop.router.lesson_suggestions` (the
acceptance model and the draw). Three steps, each its own call:

* :func:`today_suggestion`: at Today's open, the day's card. The first call of
  a local day records any earlier shown card left unanswered as ``ignored``,
  builds the ``instruct(lesson)`` candidates (LOs new on an active goal, failing
  their two latest cold checks, or predicted below adaptive difficulty's
  ``calibrate_below``; never one with an open lesson or taught since its last
  attempt), replays the response ledger into the acceptance model, draws, and
  writes ONE ``lesson_suggestion`` router decision for the day (shown or not,
  with its exact propensity; receipt key ``lesson_suggestion:<date>``, so at most
  one a day). Later calls read that decision back: the card while it is shown
  and unanswered, else nothing. No candidate: nothing is written (a later open
  may draw).
* :func:`respond`: the learner's one response (Start = ``accepted``, an
  alternative = ``chose_alternative``, "Not now" = ``declined``), appended to
  ``router_suggestion_responses``. A Start names the lesson id the lesson will
  open under, so the response is recorded before the teacher is called and the
  lesson row carries the decision id (``lessons.origin_ref``, receipt
  ``origin``).
* The lesson itself opens through ``lesson.turn`` (``teacher.service.open_lesson``
  with ``origin = 'router'``), which checks the response.

Suggestions are only this card: never a modal or a notification, and never
during a check (the card lives on Today, not on the practice screen). Off
(``router.lesson_suggestions.enabled``, the router, its decision log or lessons
off), or below the successor's tag, every call returns nothing and writes
nothing, so Today and the plan are the predecessor's byte for byte.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from learnloop.algorithm_versions import LESSON_SUGGESTIONS_VERSIONS, TEACHER_VERSIONS
from learnloop.clock import Clock, parse_utc
from learnloop.daily_plan.engine import PlanEnv, latest_today
from learnloop.db.stores import router_suggestions as store
from learnloop.db.stores.router import ROUTER_LOG_VERSION, insert_router_decision
from learnloop.ids import new_ulid
from learnloop.learner.lesson_weight import COLD_ATTEMPT_TYPES, predicted_success
from learnloop.router import lesson_suggestions as LS
from learnloop.vault.models import learning_object_facet_union

#: Plain words for each reason (the card's honest "why": the planner's reason, router §7.4).
REASON_WORDS: Mapping[str, str] = {
    "new_goal": "It's on your goal and you haven't started it yet.",
    "cold_failing": "Your last two checks on it didn't come out right.",
    "below_band": "LearnLoop expects it to be hard for you right now.",
}
WHY_LABEL = "Suggested by LearnLoop's planner"


class SuggestionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def suggestions_active(vault: Any) -> bool:
    """Today may suggest a lesson: the successor's tag, its switch, the router and its log, and lessons."""

    config = vault.config
    if config.algorithms.algorithm_version not in LESSON_SUGGESTIONS_VERSIONS:
        return False
    if not (config.router.lesson_suggestions.enabled and config.router.enabled and config.router.log_decisions):
        return False
    # Lessons may open (``teacher.service.lessons_active``, read here without importing the teacher, a
    # composition layer nothing below imports; a test pins the two equal).
    return config.algorithms.algorithm_version in TEACHER_VERSIONS and bool(config.teacher.enabled)


# =============================================================================
# Candidates
# =============================================================================


def _goal_learning_objects(vault: Any) -> set[str]:
    out: set[str] = set()
    for goal in vault.goals:
        if goal.status != "active":
            continue
        concepts = set(goal.facet_scope.concepts)
        facets = set(goal.facet_scope.facets)
        for lo_id, learning_object in vault.learning_objects.items():
            if learning_object.concept in concepts or (facets & set(learning_object_facet_union(learning_object))):
                out.add(str(lo_id))
    return out


def _cold(row: Mapping[str, Any]) -> bool:
    return (row["attempt_type"] in COLD_ATTEMPT_TYPES and not row["primed"] and not row["hints_used"]
            and row["correctness"] is not None)


def _predicted(vault: Any, repository: Any, learning_object_id: str, now_iso: str) -> float | None:
    """The mastery model's predicted unassisted success on the LO (its own prior while it has no evidence):
    the number the lesson brief shows (``teacher.brief.lo_prediction``; a test pins the two equal)."""

    from learnloop.learner.mastery import initial_mastery_state_for_learning_object, item_irt_params

    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        return None
    a, b = item_irt_params(None, learning_object, vault.config.mastery)
    state = repository.mastery_state(learning_object_id)
    if state is None:
        state = initial_mastery_state_for_learning_object(vault, repository, learning_object_id, now_iso)
    if state is None:
        return None
    return float(predicted_success(float(state.logit_mean), float(state.logit_variance), a=a, b=b))


def build_candidates(vault: Any, repository: Any, *, now_iso: str) -> tuple[list[LS.Candidate], dict[str, list[str]]]:
    """The ``instruct(lesson)`` candidates (without decline days) and why other LOs were left out."""

    with repository.connection() as connection:
        attempts = store.attempts_by_learning_object(connection)
        open_los = store.open_lesson_learning_objects(connection)
        taught = store.last_lesson_opened_by_learning_object(connection)
    goal_los = _goal_learning_objects(vault)
    cut = float(vault.config.adaptive_difficulty.calibrate_below)
    excluded: dict[str, list[str]] = {"open_lesson": [], "taught_since_last_attempt": []}
    out: list[LS.Candidate] = []
    for lo in sorted(goal_los | set(attempts)):
        learning_object = vault.learning_objects.get(lo)
        if learning_object is None:
            continue
        rows = attempts.get(lo, [])
        if lo in open_los:
            excluded["open_lesson"].append(lo)
            continue
        last_taught = taught.get(lo)
        if last_taught is not None and (not rows or last_taught >= str(rows[-1]["created_at"])):
            excluded["taught_since_last_attempt"].append(lo)
            continue
        cold = [row for row in rows if _cold(row)]
        reason: str | None = None
        predicted: float | None = None
        if len(cold) >= 2 and all(float(row["correctness"]) < 1.0 for row in cold[-2:]):
            reason = "cold_failing"
        elif rows:
            predicted = _predicted(vault, repository, lo, now_iso)
            if predicted is not None and predicted < cut:
                reason = "below_band"
        elif lo in goal_los:
            reason = "new_goal"
        if reason is None:
            continue
        if predicted is None:
            predicted = _predicted(vault, repository, lo, now_iso)
        out.append(LS.Candidate(ref=LS.lesson_ref(lo), learning_object_ids=(lo,), reason=reason,
                                predicted_success=predicted, title=str(learning_object.title)))
    return out, {key: value for key, value in excluded.items() if value}


# =============================================================================
# The ledger, replayed
# =============================================================================


def _shown(decision: Mapping[str, Any]) -> bool:
    return bool((decision.get("detail") or {}).get("shown"))


def _model(connection: Any) -> tuple[LS.AcceptanceState, list[dict[str, Any]], list[dict[str, Any]]]:
    decisions = store.decisions(connection)
    responses = store.responses(connection)
    details = {str(d["id"]): d["detail"] for d in decisions}
    return LS.replay(LS.observations(details, responses)), decisions, responses


def _days(now: datetime, at: str | None) -> float | None:
    when = parse_utc(at) if at else None
    return None if when is None else LS.days_between(now, when)


def _context(env: PlanEnv, decisions: Sequence[Mapping[str, Any]]) -> LS.Context:
    now = env.now()
    local = now.astimezone()
    record = latest_today(env)
    minutes_left = float(record.minutes_left()) if record is not None and record.is_open else None
    shown = [d for d in decisions if _shown(d)]
    if shown:
        since = _days(now, str(shown[-1]["created_at"]))
    elif decisions:
        since = _days(now, str(decisions[0]["created_at"]))
    else:
        since = None
    return LS.Context(local_hour=local.hour + local.minute / 60.0, minutes_left=minutes_left,
                      reentry=bool(env.gap().due), days_since_last=since)


def _sweep_ignored(connection: Any, decisions: Sequence[Mapping[str, Any]], *, today: str, now_iso: str) -> int:
    """Record each earlier day's shown card left unanswered as ``ignored`` (its day has ended)."""

    written = 0
    for decision in decisions:
        if not _shown(decision) or decision["day"] >= today or store.response_for(connection, decision["id"]):
            continue
        primary = ((decision["detail"].get("card") or {}).get("candidates") or [{}])[0]
        written += int(store.insert_response(
            connection, decision_id=decision["id"], response="ignored", candidate_ref=str(primary.get("ref") or ""),
            learning_object_ids=list(primary.get("learning_object_ids") or []), responded_at=now_iso,
            detail={"recorded": "next_suggestion_step", "shown_on": decision["day"]}))
    return written


# =============================================================================
# Today's card
# =============================================================================


def _card_entry(entry: Mapping[str, Any]) -> dict[str, Any]:
    return {"ref": entry["ref"], "title": entry.get("title") or "", "learning_object_ids": list(entry["learning_object_ids"]),
            "reason": entry["reason"], "why": REASON_WORDS.get(str(entry["reason"]), "")}


def card_view(connection: Any, decision: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """The card a decision shows while it is unanswered; None when it showed none or was answered."""

    if decision is None or not _shown(decision) or store.response_for(connection, decision["id"]) is not None:
        return None
    entries = (decision["detail"].get("card") or {}).get("candidates") or []
    if not entries:
        return None
    return {"decision_id": decision["id"], "day": decision["day"], "minutes": LS.CARD_MINUTES,
            "suggestion": _card_entry(entries[0]), "alternatives": [_card_entry(e) for e in entries[1:]],
            "why_label": WHY_LABEL}


def today_suggestion(vault: Any, repository: Any, *, clock: Clock | None = None,
                     session_id: str | None = None) -> dict[str, Any] | None:
    """Today's suggestion card, drawing the day's decision on the first call; None when there is none."""

    if not suggestions_active(vault):
        return None
    env = PlanEnv(vault, repository, clock=clock, session_id=session_id)
    today, now_iso = env.today(), env.now_iso()
    with repository.atomic():
        connection = repository.connection()
        if not store.tables_present(connection):
            return None
        _sweep_ignored(connection, store.decisions(connection), today=today, now_iso=now_iso)
        existing = store.decision_for_day(connection, today)
        if existing is not None:
            return card_view(connection, existing)
    candidates, excluded = build_candidates(vault, repository, now_iso=now_iso)
    if not candidates:
        return None
    with repository.atomic():
        connection = repository.connection()
        existing = store.decision_for_day(connection, today)
        if existing is not None:
            return card_view(connection, existing)
        state, decisions, responses = _model(connection)
        context = _context(env, decisions)
        details = {str(d["id"]): d["detail"] for d in decisions}
        declined = LS.declines_by_learning_object(details, responses)
        now = env.now()
        dated = []
        for candidate in candidates:
            days = [d for lo in candidate.learning_object_ids if (d := _days(now, declined.get(lo))) is not None]
            dated.append(LS.Candidate(ref=candidate.ref, learning_object_ids=candidate.learning_object_ids,
                                      reason=candidate.reason, predicted_success=candidate.predicted_success,
                                      days_since_decline=min(days) if days else None, title=candidate.title))
        config = vault.config.router
        scored = LS.score(state, context, dated, k=config.k)
        ceiling = int(config.lesson_suggestions.ceiling_per_day)
        shown_today = sum(1 for d in decisions if _shown(d) and d["day"] == today)
        inputs = {"version": LS.SUGGESTION_VERSION, "priors_version": LS.PRIORS_VERSION,
                  "context": context.as_dict(), "candidates": [s.candidate.as_dict() for s in scored],
                  "updates": state.updates, "epsilon": config.epsilon_min, "k": config.k, "ceiling": ceiling,
                  "algorithm_version": vault.config.algorithms.algorithm_version}
        snapshot = LS.canonical_hash(inputs)
        seed = LS.seed_for(today, snapshot)
        result = LS.draw(scored, epsilon=config.epsilon_min, seed=seed, ceiling_bound=shown_today >= ceiling)
        card = [result.drawn, *result.alternatives] if result.shown else []
        card_payload = {"candidates": [entry.as_dict() for entry in card]}
        detail = {
            "version": LS.SUGGESTION_VERSION, "context": context.as_dict(), "shown": result.shown,
            "drawn_ref": result.drawn.candidate.ref, "drawn_learning_object_ids": list(result.drawn.candidate.learning_object_ids),
            "p_show_drawn": round(result.drawn.p_accept, 12), "p_no_card": round(result.p_no_card, 12),
            "card": card_payload, "model": state.summary(), "epsilon": config.epsilon_min, "k": config.k,
            "ceiling": {"per_day": ceiling, "shown_today": shown_today, "bound": result.ceiling_bound},
            "candidates_considered": len(candidates),
        }
        row = {
            "id": new_ulid(), "receipt_key": store.receipt_key(today), "decision_kind": LS.DECISION_KIND,
            "surface": LS.SURFACE, "mode": config.mode, "policy": LS.POLICY,
            "algorithm_version": vault.config.algorithms.algorithm_version, "log_version": ROUTER_LOG_VERSION,
            "session_id": session_id, "parent_decision_id": None, "scheduler_slate_id": None,
            "controller_decision_id": None, "snapshot_hash": snapshot, "design": LS.DESIGN, "seed": seed,
            "candidates_json": json.dumps([s.as_dict() for s in result.scored], sort_keys=True),
            "exclusions_json": json.dumps({"named": excluded, "counts": {}}, sort_keys=True),
            "candidate_count": len(result.scored), "chosen_ref": result.chosen_ref,
            "chosen_practice_item_id": None,
            "chosen_learning_object_id": result.drawn.candidate.learning_object_ids[0] if result.shown else None,
            "chosen_scheduler_candidate_id": None, "propensity": result.propensity,
            "propensity_kind": result.propensity_kind, "learner_pick": 0,
            "card_hash": LS.canonical_hash(card_payload) if result.shown else None,
            "detail_json": json.dumps(detail, sort_keys=True), "created_at": now_iso,
        }
        insert_router_decision(connection, row)
        return card_view(connection, store.decision_for_day(connection, today))


# =============================================================================
# The response
# =============================================================================


def respond(vault: Any, repository: Any, *, decision_id: str, response: str, candidate_ref: str | None = None,
            session_id: str | None = None, clock: Clock | None = None) -> dict[str, Any]:
    """Record the learner's one response to a shown card; a Start or an alternative names its lesson id."""

    if not suggestions_active(vault):
        raise SuggestionError("suggestions_disabled", "Lesson suggestions are switched off.")
    if response not in ("accepted", "chose_alternative", "declined"):
        raise SuggestionError("validation_error", f"unknown response {response!r}")
    env = PlanEnv(vault, repository, clock=clock, session_id=session_id)
    now_iso = env.now_iso()
    with repository.atomic():
        connection = repository.connection()
        decision = store.decision(connection, decision_id)
        if decision is None or not _shown(decision):
            raise SuggestionError("not_found", "That suggestion isn't on your Today card.")
        entries = (decision["detail"].get("card") or {}).get("candidates") or []
        primary, alternatives = entries[0], entries[1:]
        if response == "chose_alternative":
            chosen = next((entry for entry in alternatives if entry["ref"] == candidate_ref), None)
            if chosen is None:
                raise SuggestionError("validation_error", "That lesson wasn't one of the card's alternatives.")
        else:
            chosen = primary
        existing = store.response_for(connection, decision_id)
        if existing is not None:
            if existing["response"] != response or existing["candidate_ref"] != chosen["ref"]:
                raise SuggestionError("already_answered", "You already answered this suggestion.")
            return _response_view(existing, chosen)
        lesson_id = f"les_{new_ulid().lower()}" if response in ("accepted", "chose_alternative") else None
        store.insert_response(
            connection, decision_id=decision_id, response=response, candidate_ref=str(chosen["ref"]),
            learning_object_ids=list(chosen["learning_object_ids"]), responded_at=now_iso, lesson_id=lesson_id,
            session_id=session_id, detail={"card_hash": decision.get("card_hash")})
        return _response_view(store.response_for(connection, decision_id), chosen)


def _response_view(row: Mapping[str, Any], chosen: Mapping[str, Any]) -> dict[str, Any]:
    lesson = None
    if row.get("lesson_id"):
        lesson = {"lesson_id": row["lesson_id"], "decision_id": row["decision_id"],
                  "learning_object_ids": json.loads(row["learning_object_ids_json"] or "[]"),
                  "title": chosen.get("title") or ""}
    return {"decision_id": row["decision_id"], "response": row["response"], "candidate_ref": row["candidate_ref"],
            "lesson": lesson}


def acceptance_curve(vault: Any, repository: Any, *, days: Sequence[float], clock: Clock | None = None) -> list[float]:
    """The current model's P(accept) for a goal declined ``d`` days ago, in today's context (a report read)."""

    env = PlanEnv(vault, repository, clock=clock)
    with repository.connection() as connection:
        state, decisions, _responses = _model(connection)
    context = _context(env, decisions)
    probe = LS.Candidate(ref="lesson:probe", learning_object_ids=("probe",), reason="new_goal", predicted_success=None)
    out = []
    for d in days:
        candidate = LS.Candidate(ref=probe.ref, learning_object_ids=probe.learning_object_ids, reason=probe.reason,
                                 predicted_success=None, days_since_decline=None if math.isinf(d) else float(d))
        out.append(state.p_accept(context, candidate))
    return out


__all__ = [
    "REASON_WORDS",
    "SuggestionError",
    "WHY_LABEL",
    "acceptance_curve",
    "build_candidates",
    "card_view",
    "respond",
    "suggestions_active",
    "today_suggestion",
]

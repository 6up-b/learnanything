"""The optional quick check, "Check what I already know" (learner field §5.2, D4).

A learner-initiated calibration session (``start_calibration_session`` with an
explicit LO list and the quick check's budget) that is never prompted. It
serves at most ``placement.quick_check_k`` (4) ordinary cold items within
``placement.quick_check_budget_minutes`` (8), chosen one at a time by the
active predictor's ``conditional_gain`` over the LOs still undecided (with the
incumbent this is the plain per-LO information; a Phase 4 challenger plugs in
through the same interface). It stops early once every LO is decided.

Each item the check serves is persisted as a presentation (at most k per
check). Only the first submission on a presented item, in the check's practice
session, after the presentation and before the check's stop or budget boundary,
is the check's answer: practice outside that window, or on items the check
never presented, stays ordinary practice.

Answers are graded as they are given, but the check withholds every result
until it ends: the progress payload carries only counts while it runs, and the
per-answer results (and their feedback) are released at the end. The results
then feed the same split as fast-track: ``assumed`` LOs get a ``quick_check``
receipt; the rest start (or stay) as learning.

Candidates are ordinary never-seen items that routine serving could offer: the
shared exclusions (exam reservations, pending-variant holds, staged-controller
ownership) apply here exactly as on Today's queue. Because the check picks
outside the scheduler's timing, it also skips what ``find_practice`` skips for
the same reason: an open cold follow-up's reserved item and an item whose
answer was revealed within the cold retrieval delay
(``scheduling.serving_exclusions.out_of_timing_serving_exclusions``). A put-away
LO and a reference-adopted card behind its switched-off sweep are refused by
``vault.lifecycle``, as on every serving door.

The calibration session and the quick-check row are created in one
transaction; a retried start with the same request id recovers the check it
created. No diagnostic episode is opened (``open_episodes=False``) and no
instrument is generated, so no paid call and no opening probe survives the
check.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any

from learnloop.attempts.attempts import COLD_FOLLOWUP_TASK_KINDS
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores.placement import insert_quick_check, insert_quick_check_item
from learnloop.diagnosis.calibration_sessions import (
    CalibrationSessionError,
    calibration_session_progress,
    start_calibration_session,
)
from learnloop.diagnosis.remediation import COLD_RETRIEVAL_DELAY
from learnloop.placement.decisions import (
    bind_quick_check_answers,
    finish_quick_check_split,
    quick_check_answers,
    quick_check_presentations,
    quick_check_record,
    quick_check_split,
    quick_check_window_end,
)
from learnloop.placement.predictor import active_predictor
from learnloop.placement.signals import blocking_signals_by_lo
from learnloop.placement.state import (
    diagnosis_can_arrive,
    load_answers,
    load_placement_state_from_connection,
    placement_active,
)
from learnloop.scheduling.serving_exclusions import out_of_timing_serving_exclusions
from learnloop.substrate.instrument_serving import unservable_reason
from learnloop.vault.lifecycle import practice_item_servable
from learnloop.vault.models import LoadedVault

QUICK_CHECK_SELECTION = "conditional_gain"
#: A quick check serves normal cold items, never single-use diagnostic
#: surfaces or AI conversations.
_EXCLUDED_MODES = frozenset({"diagnostic_probe", "diagnostic_microprobe", "teach_back"})
_DECIDED = frozenset({"assumed", "learning", "already_assumed", "maintenance"})


class QuickCheckError(ValueError):
    pass


def _existing_quick_check(
    repository: Repository, *, session_id: str, scope: list[str], request_id: str | None,
) -> str | None:
    """The check a retried start should recover, if any.

    The same request id returns the check it created. Without one, an active
    quick check over the same scope in the same practice session is the same
    request (a double submit) and is returned too.
    """

    with repository.connection() as connection:
        if request_id:
            row = connection.execute(
                "SELECT calibration_session_id, session_id FROM placement_quick_checks WHERE request_id = ?",
                (request_id,),
            ).fetchone()
            if row is not None:
                if str(row[1]) != session_id:
                    raise QuickCheckError("this quick-check request id belongs to another practice session")
                return str(row[0])
    active = repository.active_probe_calibration_session(session_id)
    if active is None:
        return None
    record = quick_check_record(repository, active.id)
    if record is not None and sorted(json.loads(record["learning_object_ids_json"])) == scope:
        return active.id
    return None


def start_quick_check(
    vault: LoadedVault,
    repository: Repository,
    *,
    session_id: str,
    learning_object_ids: list[str],
    request_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    if not placement_active(vault):
        raise QuickCheckError("the quick check needs placement (mvp-0.11 or later with placement.enabled)")
    scope = sorted({
        lo_id for lo_id in learning_object_ids
        if (lo := vault.learning_objects.get(lo_id)) is not None and lo.status == "active"
    })
    if not scope:
        raise QuickCheckError("the quick check needs at least one active learning object")
    existing = _existing_quick_check(repository, session_id=session_id, scope=scope, request_id=request_id)
    if existing is not None:
        return quick_check_progress(vault, repository, existing, clock=clock)
    placement = vault.config.placement
    now_iso = utc_now_iso(clock)
    predictor = active_predictor(vault, repository, now_iso=now_iso)
    try:
        # One transaction: a calibration session never exists without its
        # quick-check row (no orphan blocks the practice session's next start).
        with repository.atomic():
            progress = start_calibration_session(
                vault,
                repository,
                session_id=session_id,
                learning_object_ids=scope,
                time_budget_minutes=placement.quick_check_budget_minutes,
                generate_missing=False,
                open_episodes=False,
                clock=clock,
            )
            with repository.connection() as connection:
                insert_quick_check(connection, {
                    "calibration_session_id": progress["calibration_session_id"],
                    "session_id": session_id,
                    "learning_object_ids_json": json.dumps(scope),
                    "k": placement.quick_check_k,
                    "budget_minutes": placement.quick_check_budget_minutes,
                    "predictor": predictor.name,
                    "predictor_version": predictor.version_hash,
                    "created_at": now_iso,
                    "request_id": request_id,
                })
    except (CalibrationSessionError, sqlite3.IntegrityError) as error:
        # A concurrent start with the same identity won the race: recover it.
        existing = _existing_quick_check(repository, session_id=session_id, scope=scope, request_id=request_id)
        if existing is not None:
            return quick_check_progress(vault, repository, existing, clock=clock)
        raise QuickCheckError(str(error)) from error
    return quick_check_progress(vault, repository, progress["calibration_session_id"], clock=clock)


def is_quick_check(repository: Repository, calibration_session_id: str) -> bool:
    return quick_check_record(repository, calibration_session_id) is not None


def _candidate_items(
    vault: LoadedVault,
    repository: Repository,
    undecided: set[str],
    attempted: set[str],
    excluded: frozenset[str] = frozenset(),
    *,
    clock: Clock | None = None,
) -> list[str]:
    """Never-seen ordinary items on undecided LOs that routine serving could
    offer (the shared exclusions apply, with the out-of-timing ones), minus
    ``excluded``."""

    from learnloop import serve_eligibility

    item_states = repository.practice_item_states()
    serving_excluded = out_of_timing_serving_exclusions(
        vault, repository, cold_followup_kinds=COLD_FOLLOWUP_TASK_KINDS,
        reveal_window=COLD_RETRIEVAL_DELAY, clock=clock,
    ).out_of_timing_item_ids
    # The one eligibility decision (``serve_eligibility``, QUICK_CHECK; the
    # mvp-0.27 successor, behind ``eligibility.enabled``): never an item
    # submit would prime (a reveal of its answer, at any age, since it has
    # never been attempted). The ledger is read once; an item with no row
    # cannot be primed, so only items with rows are asked. Below the tag, or
    # off, the offers are mvp-0.26's (the serving exclusions alone).
    now_iso = utc_now_iso(clock)
    reveal_rows: dict[str, list[dict[str, Any]]] = {}
    if serve_eligibility.decision_active(vault):
        for row in repository.reveal_events():
            reveal_rows.setdefault(str(row.get("practice_item_id") or ""), []).append(row)
    result = []
    for item in vault.practice_items.values():
        if item.learning_object_id not in undecided or item.status != "active" or item.id in attempted:
            continue
        if item.id in serving_excluded or item.id in excluded:
            continue
        state = item_states.get(item.id)
        if state is not None and (not state.active or state.last_attempt_at is not None):
            continue
        if (
            item.practice_mode in _EXCLUDED_MODES
            or unservable_reason(item) is not None
            or not practice_item_servable(vault, item)
        ):
            continue
        if item.id in reveal_rows:
            decision = serve_eligibility.decide(
                serve_eligibility.gather(
                    repository, practice_item_id=item.id, learning_object_id=None, at=now_iso,
                    reveal_rows=reveal_rows[item.id],
                ),
                serve_eligibility.QUICK_CHECK,
            )
            if not decision.serves:
                serve_eligibility.log_decision(decision, path="quick_check_offer")
                continue
        result.append(item.id)
    return sorted(result)


def _attempted_item_ids(repository: Repository) -> set[str]:
    with repository.connection() as connection:
        return {str(row[0]) for row in connection.execute(
            "SELECT DISTINCT practice_item_id FROM practice_attempts"
        ).fetchall()}


def next_quick_check_item(
    vault: LoadedVault,
    repository: Repository,
    predictor: Any,
    *,
    undecided: set[str],
    excluded: frozenset[str] = frozenset(),
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """The never-seen item with the largest conditional gain; ties by id (G8)."""

    candidates = _candidate_items(
        vault, repository, undecided, _attempted_item_ids(repository), excluded, clock=clock,
    )
    if not candidates:
        return None
    weights = {lo: 1.0 for lo in undecided}
    # The live posterior already includes the check's answers, so nothing is
    # passed as "chosen": that would count them twice.
    ranked = sorted(
        candidates,
        key=lambda item_id: (-predictor.conditional_gain(item_id, [], weights), item_id),
    )
    item_id = ranked[0]
    return {
        "practice_item_id": item_id,
        "learning_object_id": str(vault.practice_items[item_id].learning_object_id),
        "conditional_gain": predictor.conditional_gain(item_id, [], weights),
    }


def _present_next(
    vault: LoadedVault,
    repository: Repository,
    predictor: Any,
    record: dict[str, Any],
    presentations: list[dict[str, Any]],
    *,
    undecided: set[str],
    clock: Clock | None,
) -> dict[str, Any] | None:
    """The check's current presentation, or a new one while fewer than k exist.

    An unanswered presentation stays the target while its LO is undecided and
    its item is still a servable never-seen item. Otherwise a new item is
    presented, persisted with its ordinal, so k holds server-side.
    """

    calibration_id = str(record["calibration_session_id"])
    outstanding = [p for p in presentations if p["attempt_id"] is None]
    if outstanding:
        current = outstanding[-1]
        still_valid = current["learning_object_id"] in undecided and current["practice_item_id"] in set(
            _candidate_items(vault, repository, undecided, _attempted_item_ids(repository), clock=clock)
        )
        if still_valid:
            return {
                "practice_item_id": current["practice_item_id"],
                "learning_object_id": current["learning_object_id"],
            }
    if len(presentations) >= int(record["k"]):
        return None
    presented = frozenset(str(p["practice_item_id"]) for p in presentations)
    chosen = next_quick_check_item(
        vault, repository, predictor, undecided=undecided, excluded=presented, clock=clock,
    )
    if chosen is None:
        return None
    with repository.atomic():
        with repository.connection() as connection:
            if len(quick_check_presentations(connection, calibration_id)) != len(presentations):
                # Another reader presented concurrently: serve what it chose.
                latest = quick_check_presentations(connection, calibration_id)[-1]
                return {
                    "practice_item_id": latest["practice_item_id"],
                    "learning_object_id": latest["learning_object_id"],
                }
            insert_quick_check_item(connection, {
                "calibration_session_id": calibration_id,
                "ordinal": len(presentations) + 1,
                "practice_item_id": chosen["practice_item_id"],
                "learning_object_id": chosen["learning_object_id"],
                "presented_at": utc_now_iso(clock),
            })
    return chosen


def quick_check_progress(
    vault: LoadedVault,
    repository: Repository,
    calibration_session_id: str,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Calibration progress with the quick check's own target and results."""

    progress = calibration_session_progress(vault, repository, calibration_session_id, clock=clock)
    record = quick_check_record(repository, calibration_session_id)
    if record is None:
        return progress
    scope = json.loads(record["learning_object_ids_json"])
    k = int(record["k"])
    outcome = json.loads(record["outcome_json"]) if record["finished_at"] else None
    next_item = None
    if outcome is None:
        calibration = repository.probe_calibration_session(calibration_session_id)
        if calibration is not None:
            with repository.atomic():
                with repository.connection() as connection:
                    bind_quick_check_answers(connection, record, window_end=quick_check_window_end(calibration))
        with repository.connection() as connection:
            presentations = quick_check_presentations(connection, calibration_session_id)
            answers = quick_check_answers(connection, calibration_session_id=calibration_session_id, scope=scope)
            state = load_placement_state_from_connection(
                connection, active=placement_active(vault), diagnosis_live=diagnosis_can_arrive(vault),
                now_iso=utc_now_iso(clock),
            )
            blocking = blocking_signals_by_lo(connection, vault, load_answers(connection))
        predictor = active_predictor(vault, repository, now_iso=utc_now_iso(clock))
        split = quick_check_split(
            vault, predictor, scope=scope, answers_by_lo=answers, blocking=blocking, state=state,
        )
        answered = sum(1 for presentation in presentations if presentation["attempt_id"] is not None)
        undecided = {lo for lo, verdict in split.items() if verdict["verdict"] not in _DECIDED}
        if progress["status"] == "active" and answered < k and undecided:
            next_item = _present_next(
                vault, repository, predictor, record, presentations, undecided=undecided, clock=clock,
            )
        if progress["status"] != "active" or answered >= k or not undecided or next_item is None:
            if progress["status"] == "active":
                repository.end_probe_calibration_session(calibration_session_id, status="completed", clock=clock)
            outcome = finish_quick_check_split(
                vault, repository, calibration_session_id=calibration_session_id, clock=clock,
            )
            progress = calibration_session_progress(vault, repository, calibration_session_id, clock=clock)
            next_item = None
    answered_total = (
        sum(len(ids) for ids in outcome.get("answers", {}).values()) if outcome is not None else answered
    )
    progress["next_target"] = (
        {
            "episode_id": None,
            "learning_object_id": next_item["learning_object_id"],
            "practice_item_id": next_item["practice_item_id"],
            "selection_objective": QUICK_CHECK_SELECTION,
            "entropy": None,
        }
        if next_item is not None
        else None
    )
    progress["quick_check"] = {
        "learning_object_ids": scope,
        "k": k,
        "answered": answered_total,
        "remaining": max(k - answered_total, 0),
        "finished": outcome is not None,
        # Results are withheld until the check ends (answers revealed at the end).
        "results": _results(vault, repository, outcome) if outcome is not None else None,
    }
    return progress


def _results(vault: LoadedVault, repository: Repository, outcome: dict[str, Any]) -> list[dict[str, Any]]:
    attempt_ids = [attempt_id for ids in outcome.get("answers", {}).values() for attempt_id in ids]
    by_id: dict[str, dict[str, Any]] = {}
    if attempt_ids:
        with repository.connection() as connection:
            rows = connection.execute(
                "SELECT id, practice_item_id, learning_object_id, correctness, created_at FROM practice_attempts "
                f"WHERE id IN ({','.join('?' for _ in attempt_ids)})",
                attempt_ids,
            ).fetchall()
        by_id = {str(row[0]): {
            "attempt_id": str(row[0]), "practice_item_id": str(row[1]),
            "learning_object_id": str(row[2]), "correctness": row[3], "created_at": row[4],
        } for row in rows}
    results = []
    for lo_id, verdict in sorted(outcome.get("split", {}).items()):
        learning_object = vault.learning_objects.get(lo_id)
        results.append({
            "learning_object_id": lo_id,
            "learning_object_title": learning_object.title if learning_object is not None else lo_id,
            "verdict": verdict.get("verdict"),
            "assumption_id": verdict.get("assumption_id"),
            "answers": sorted(
                (by_id[attempt_id] for attempt_id in outcome.get("answers", {}).get(lo_id, []) if attempt_id in by_id),
                key=lambda row: (row["created_at"], row["attempt_id"]),
            ),
        })
    return results

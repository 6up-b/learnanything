"""The optional quick check, "Check what I already know" (learner field §5.2, D4).

A learner-initiated calibration session (``start_calibration_session`` with an
explicit LO list and the quick check's budget) that is never prompted. It
serves at most ``placement.quick_check_k`` (4) ordinary cold items within
``placement.quick_check_budget_minutes`` (8), chosen one at a time by the
active predictor's ``conditional_gain`` over the LOs still undecided (with the
incumbent this is the plain per-LO information; a Phase 4 challenger plugs in
through the same interface). It stops early once every LO is decided.

Answers are graded as they are given, but the check withholds every result
until it ends: the progress payload carries only counts while it runs, and the
per-answer results (and their feedback) are released at the end. The results
then feed the same split as fast-track: ``assumed`` LOs get a ``quick_check``
receipt; the rest start (or stay) as learning.

No diagnostic episode is opened (``open_episodes=False``) and no instrument
is generated, so no paid call and no opening probe survives the check.
"""
from __future__ import annotations

import json
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores.placement import insert_quick_check
from learnloop.diagnosis.calibration_sessions import (
    CalibrationSessionError,
    calibration_session_progress,
    start_calibration_session,
)
from learnloop.placement.decisions import (
    finish_quick_check_split,
    quick_check_answers,
    quick_check_record,
    quick_check_split,
)
from learnloop.placement.predictor import active_predictor
from learnloop.placement.signals import blocking_signals_by_lo
from learnloop.placement.state import load_answers, load_placement_state_from_connection, placement_active
from learnloop.substrate.instrument_serving import unservable_reason
from learnloop.vault.lifecycle import practice_item_servable
from learnloop.vault.models import LoadedVault

QUICK_CHECK_SELECTION = "conditional_gain"
#: A quick check serves normal cold items, never single-use diagnostic
#: surfaces or AI conversations.
_EXCLUDED_MODES = frozenset({"diagnostic_probe", "diagnostic_microprobe", "teach_back"})
_DECIDED = frozenset({"assumed", "learning", "already_assumed"})


class QuickCheckError(ValueError):
    pass


def start_quick_check(
    vault: LoadedVault,
    repository: Repository,
    *,
    session_id: str,
    learning_object_ids: list[str],
    clock: Clock | None = None,
) -> dict[str, Any]:
    if not placement_active(vault):
        raise QuickCheckError("the quick check needs placement (mvp-0.10 with placement.enabled)")
    scope = sorted({
        lo_id for lo_id in learning_object_ids
        if (lo := vault.learning_objects.get(lo_id)) is not None and lo.status == "active"
    })
    if not scope:
        raise QuickCheckError("the quick check needs at least one active learning object")
    placement = vault.config.placement
    try:
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
    except CalibrationSessionError as error:
        raise QuickCheckError(str(error)) from error
    now_iso = utc_now_iso(clock)
    predictor = active_predictor(vault, repository, now_iso=now_iso)
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
        })
    return quick_check_progress(vault, repository, progress["calibration_session_id"], clock=clock)


def is_quick_check(repository: Repository, calibration_session_id: str) -> bool:
    return quick_check_record(repository, calibration_session_id) is not None


def _candidate_items(
    vault: LoadedVault,
    repository: Repository,
    undecided: set[str],
    attempted: set[str],
) -> list[str]:
    item_states = repository.practice_item_states()
    result = []
    for item in vault.practice_items.values():
        if item.learning_object_id not in undecided or item.status != "active" or item.id in attempted:
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
        result.append(item.id)
    return sorted(result)


def next_quick_check_item(
    vault: LoadedVault,
    repository: Repository,
    predictor: Any,
    *,
    undecided: set[str],
) -> dict[str, Any] | None:
    """The never-seen item with the largest conditional gain; ties by id (G8)."""

    with repository.connection() as connection:
        attempted = {str(row[0]) for row in connection.execute(
            "SELECT DISTINCT practice_item_id FROM practice_attempts"
        ).fetchall()}
    candidates = _candidate_items(vault, repository, undecided, attempted)
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
        with repository.connection() as connection:
            answers = quick_check_answers(
                connection, session_id=record["session_id"], scope=scope, started_at=record["created_at"],
            )
            state = load_placement_state_from_connection(connection, active=placement_active(vault))
            blocking = blocking_signals_by_lo(connection, vault, load_answers(connection))
        predictor = active_predictor(vault, repository, now_iso=utc_now_iso(clock))
        split = quick_check_split(
            vault, predictor, scope=scope, answers_by_lo=answers, blocking=blocking, state=state,
        )
        answered = sum(len(rows) for rows in answers.values())
        undecided = {lo for lo, verdict in split.items() if verdict["verdict"] not in _DECIDED}
        if progress["status"] == "active" and answered < k and undecided:
            next_item = next_quick_check_item(vault, repository, predictor, undecided=undecided)
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

"""Assumed-known decisions (learner field §5.2): receipts, never evidence.

Four sources mark an LO "assumed known (not tested)":

- ``self_report``: "I know this" on an LO, its chapter or an item, or "too
  easy" on an item. Acts immediately (D5).
- ``fast_track``: the LO's first answers pass the fast-track rule (D6).
- ``predictor``: an activated cross-LO challenger is confident before any
  attempt. The incumbent ``mastery_ekf`` shares nothing across LOs, so this
  source cannot fire until a challenger is activated (field §7.4).
- ``quick_check``: the optional "Check what I already know".

"I don't know this" appends a return. Nothing here writes grading evidence,
mastery, facet state, certification, coldness or FSRS state (F2, G7): the only
writes are ``assumption_decisions``, ``assumption_returns`` and the quick
check's queue row, plus the queue revision so Today refreshes.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import timedelta
import json
from typing import Any

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores.placement import (
    finish_quick_check,
    insert_assumption_decision,
    insert_assumption_return,
)
from learnloop.field.types import LearnerPredictor, RegionEstimate
from learnloop.ids import new_ulid
from learnloop.placement.predictor import active_predictor
from learnloop.placement.rules import (
    RULES_VERSION,
    AnswerFacts,
    fast_track_verdict,
    interval_80,
    known_probability,
    theta_known,
)
from learnloop.placement.signals import blocking_signals_by_lo
from learnloop.placement.state import (
    PlacementState,
    load_answers,
    load_placement_state_from_connection,
    placement_active,
)
from learnloop.vault.models import LoadedVault

SELF_REPORTS = {"know_this": "i_know_this", "too_easy": "too_easy"}
RETURN_REPORTS = {"dont_know_this"}


class PlacementInactive(RuntimeError):
    """Placement is off (pre-mvp-0.10 vault or ``placement.enabled = false``)."""


def _config(vault: LoadedVault) -> dict[str, Any]:
    return {
        "placement": vault.config.placement.model_dump(mode="json"),
        "active_predictor": vault.config.field.active_predictor,
        "rules_version": RULES_VERSION,
    }


def _due(now_iso: str, days: int) -> str:
    moment = parse_utc(now_iso)
    assert moment is not None
    return (moment + timedelta(days=days)).isoformat().replace("+00:00", "Z")


def _region_dict(region: RegionEstimate | None) -> dict[str, Any] | None:
    if region is None:
        return None
    return {"mean": region.mean, "variance": region.variance, "n_eff": region.n_eff, "untested": region.untested}


def _decision_row(
    vault: LoadedVault,
    predictor: LearnerPredictor,
    *,
    learning_object_id: str,
    source: str,
    trigger_kind: str,
    trigger_ref: str | None,
    region: RegionEstimate | None,
    inputs: Mapping[str, Any],
    now_iso: str,
    quick_check_session_id: str | None = None,
) -> dict[str, Any]:
    placement = vault.config.placement
    threshold = theta_known(placement.known_probability)
    interval = interval_80(region)
    return {
        "id": new_ulid(),
        "learning_object_id": learning_object_id,
        "source": source,
        "trigger_kind": trigger_kind,
        "trigger_ref": trigger_ref,
        "p": known_probability(region, threshold),
        "interval_json": json.dumps(interval) if interval is not None else None,
        "q_used": None if source == "self_report" else placement.fast_track_q,
        "theta_known": threshold,
        "predictor": predictor.name,
        "predictor_version": predictor.version_hash,
        "first_review_due": _due(now_iso, placement.assumed_first_interval_days),
        "quick_check_session_id": quick_check_session_id,
        "algorithm_version": vault.config.algorithms.algorithm_version,
        "config_json": json.dumps(_config(vault), sort_keys=True),
        "inputs_json": json.dumps({**inputs, "region": _region_dict(region)}, sort_keys=True),
        "created_at": now_iso,
    }


def _open_assumption_id(connection: Any, learning_object_id: str) -> str | None:
    state = load_placement_state_from_connection(connection, active=True)
    open_ = state.open_by_lo.get(learning_object_id)
    return open_.id if open_ is not None else None


def record_self_report(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_ids: Iterable[str],
    report: str,
    trigger_ref: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """"I know this" / "too easy" (assume known) or "I don't know this" (return)."""

    if not placement_active(vault):
        raise PlacementInactive("starting new material without ceremony is off for this vault")
    if report not in SELF_REPORTS and report not in RETURN_REPORTS:
        raise ValueError(f"unknown self-report {report!r}")
    now_iso = utc_now_iso(clock)
    predictor = active_predictor(vault, repository, now_iso=now_iso)
    results: list[dict[str, Any]] = []
    wrote = False
    with repository.atomic():
        with repository.connection() as connection:
            for lo_id in sorted(set(learning_object_ids)):
                learning_object = vault.learning_objects.get(lo_id)
                if learning_object is None:
                    results.append({"learning_object_id": lo_id, "status": "unknown"})
                    continue
                if learning_object.status != "active":
                    results.append({"learning_object_id": lo_id, "status": f"not_active:{learning_object.status}"})
                    continue
                open_id = _open_assumption_id(connection, lo_id)
                if report in RETURN_REPORTS:
                    insert_assumption_return(connection, {
                        "id": new_ulid(), "assumption_id": open_id, "learning_object_id": lo_id,
                        "reason": report, "trigger_ref": trigger_ref,
                        "algorithm_version": vault.config.algorithms.algorithm_version,
                        "created_at": now_iso,
                    })
                    wrote = True
                    results.append({
                        "learning_object_id": lo_id,
                        "status": "returned_to_learning" if open_id else "learning",
                        "assumption_id": open_id,
                    })
                    continue
                if open_id is not None:
                    results.append({"learning_object_id": lo_id, "status": "already_assumed", "assumption_id": open_id})
                    continue
                region = predictor.region_estimates([lo_id]).get(lo_id)
                row = _decision_row(
                    vault, predictor, learning_object_id=lo_id, source="self_report",
                    trigger_kind=SELF_REPORTS[report], trigger_ref=trigger_ref, region=region,
                    inputs={"report": report, "scope": sorted(set(learning_object_ids))}, now_iso=now_iso,
                )
                insert_assumption_decision(connection, row)
                wrote = True
                results.append({
                    "learning_object_id": lo_id, "status": "assumed", "assumption_id": row["id"],
                    "first_review_due": row["first_review_due"],
                })
    if wrote:
        repository.bump_queue_revision(clock=clock)
    return {"report": report, "results": results}


def _quick_check_scopes(connection: Any) -> set[str]:
    scopes: set[str] = set()
    rows = connection.execute(
        "SELECT learning_object_ids_json FROM placement_quick_checks WHERE finished_at IS NULL"
    ).fetchall()
    for (raw,) in rows:
        scopes.update(json.loads(raw or "[]"))
    return scopes


def fast_track_inputs(
    answers: Sequence[AnswerFacts], blocking: Sequence[str], *, min_correct: int, q: float, known: float,
) -> dict[str, Any]:
    return {
        "answers": [answer.as_dict() for answer in answers],
        "blocking_signal_ids": list(blocking),
        "min_correct": min_correct,
        "q": q,
        "theta_known": known,
    }


def reconcile_fast_track(
    vault: LoadedVault,
    repository: Repository,
    *,
    clock: Clock | None = None,
) -> list[dict[str, Any]]:
    """Mark LOs assumed whose first answers pass the fast-track rule.

    Idempotent: an LO is considered once it has enough answers and only while
    it has never had an assumption or an "I don't know this". Runs on the
    persisting queue path (the one that always follows an attempt).
    """

    if not placement_active(vault):
        return []
    # A quick check the learner walked away from still feeds the split once its
    # budget runs out; until then its LOs wait for it, not for fast-track.
    finalize_stale_quick_checks(vault, repository, clock=clock)
    placement = vault.config.placement
    known = theta_known(placement.known_probability)
    now_iso = utc_now_iso(clock)
    written: list[dict[str, Any]] = []
    with repository.connection() as connection:
        state = load_placement_state_from_connection(connection, active=True)
        answers_by_lo = load_answers(connection)
        excluded = (
            set(state.decided_learning_object_ids)
            | set(state.returned_learning_object_ids)
            | _quick_check_scopes(connection)
        )
        candidates = sorted(
            lo for lo, answers in answers_by_lo.items()
            if lo not in excluded
            and (lo_model := vault.learning_objects.get(lo)) is not None
            and lo_model.status == "active"
            and len(answers) >= placement.fast_track_min_correct
            and all(answer.clean_correct for answer in answers)
        )
        if not candidates:
            return []
        blocking = blocking_signals_by_lo(connection, vault, answers_by_lo)
    predictor = active_predictor(vault, repository, now_iso=now_iso)
    with repository.atomic():
        with repository.connection() as connection:
            for lo in candidates:
                answers = answers_by_lo[lo]
                region = predictor.region_estimates([lo]).get(lo)
                verdict = fast_track_verdict(
                    answers, blocking_signal_ids=blocking.get(lo, ()), region=region,
                    min_correct=placement.fast_track_min_correct, q=placement.fast_track_q,
                    known_threshold=known,
                )
                if not verdict.fires:
                    continue
                if connection.execute(
                    "SELECT 1 FROM assumption_decisions WHERE learning_object_id = ? LIMIT 1", (lo,)
                ).fetchone() is not None:
                    continue  # a concurrent build already decided this LO
                row = _decision_row(
                    vault, predictor, learning_object_id=lo, source="fast_track",
                    trigger_kind="fast_track_rule",
                    trigger_ref=json.dumps([answer.attempt_id for answer in answers]),
                    region=region,
                    inputs=fast_track_inputs(
                        answers, blocking.get(lo, ()), min_correct=placement.fast_track_min_correct,
                        q=placement.fast_track_q, known=known,
                    ),
                    now_iso=now_iso,
                )
                insert_assumption_decision(connection, row)
                written.append(row)
    written.extend(reconcile_predictor_assumptions(vault, repository, predictor, clock=clock))
    if written:
        repository.bump_queue_revision(clock=clock)
    return written


def reconcile_predictor_assumptions(
    vault: LoadedVault,
    repository: Repository,
    predictor: LearnerPredictor,
    *,
    clock: Clock | None = None,
) -> list[dict[str, Any]]:
    """The ``predictor`` source: confident before any attempt.

    Only a predictor with cross-LO sharing can know an untested LO, and only an
    activated challenger has it (field §5.2, §7.4). Under the incumbent
    ``mastery_ekf`` this returns nothing, whatever a claim-seeded prior says.
    """

    if not getattr(predictor, "cross_lo_sharing", False) or not placement_active(vault):
        return []
    placement = vault.config.placement
    known = theta_known(placement.known_probability)
    now_iso = utc_now_iso(clock)
    written: list[dict[str, Any]] = []
    with repository.atomic():
        with repository.connection() as connection:
            state = load_placement_state_from_connection(connection, active=True)
            answered = set(load_answers(connection))
            excluded = set(state.decided_learning_object_ids) | set(state.returned_learning_object_ids)
            for lo_id, learning_object in sorted(vault.learning_objects.items()):
                if learning_object.status != "active" or lo_id in answered or lo_id in excluded:
                    continue
                region = predictor.region_estimates([lo_id]).get(lo_id)
                if region is None:
                    continue
                # A challenger's untested region is still an inference; read
                # its probability without the untested guard.
                tested_view = RegionEstimate(region.mean, region.variance, region.n_eff, False)
                p = known_probability(tested_view, known)
                if p is None or p < placement.fast_track_q:
                    continue
                row = _decision_row(
                    vault, predictor, learning_object_id=lo_id, source="predictor",
                    trigger_kind="predictor_rule", trigger_ref=None, region=tested_view,
                    inputs={"q": placement.fast_track_q, "theta_known": known}, now_iso=now_iso,
                )
                insert_assumption_decision(connection, row)
                written.append(row)
    return written


def quick_check_split(
    vault: LoadedVault,
    predictor: LearnerPredictor,
    *,
    scope: Sequence[str],
    answers_by_lo: Mapping[str, Sequence[AnswerFacts]],
    blocking: Mapping[str, Sequence[str]],
    state: PlacementState,
) -> dict[str, dict[str, Any]]:
    """Per-LO quick-check verdict: ``assumed``, ``learning`` or ``undecided``.

    The same rule as fast-track, over the quick check's own answers.
    """

    placement = vault.config.placement
    known = theta_known(placement.known_probability)
    result: dict[str, dict[str, Any]] = {}
    for lo in sorted(set(scope)):
        answers = tuple(answers_by_lo.get(lo, ()))
        if lo in state.open_by_lo:
            result[lo] = {"verdict": "already_assumed", "answers": len(answers)}
            continue
        region = predictor.region_estimates([lo]).get(lo)
        verdict = fast_track_verdict(
            answers, blocking_signal_ids=blocking.get(lo, ()), region=region,
            min_correct=placement.fast_track_min_correct, q=placement.fast_track_q,
            known_threshold=known,
        )
        if verdict.fires:
            label = "assumed"
        elif verdict.reason in {"non_clean_answer", "blocked_by_signal"}:
            label = "learning"
        else:
            label = "undecided"
        result[lo] = {"verdict": label, "reason": verdict.reason, "answers": len(answers), "p": verdict.p}
    return result


def quick_check_answers(
    connection: Any, *, session_id: str, scope: Sequence[str], started_at: str, until: str | None = None,
) -> dict[str, tuple[AnswerFacts, ...]]:
    """Answers given inside one quick check: its session, scope and window."""

    in_session = {
        str(row[0]) for row in connection.execute(
            "SELECT id FROM practice_attempts WHERE session_id = ? AND created_at >= ?",
            (session_id, started_at),
        ).fetchall()
    }
    answers = load_answers(connection, scope)
    return {
        lo: tuple(
            a for a in rows
            if a.attempt_id in in_session and a.created_at >= started_at and (until is None or a.created_at <= until)
        )
        for lo, rows in answers.items()
    }


def _quick_check_record(connection: Any, calibration_session_id: str) -> dict[str, Any] | None:
    cursor = connection.execute(
        "SELECT * FROM placement_quick_checks WHERE calibration_session_id = ?", (calibration_session_id,)
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return dict(zip([column[0] for column in cursor.description], row, strict=True))


def quick_check_record(repository: Repository, calibration_session_id: str) -> dict[str, Any] | None:
    with repository.connection() as connection:
        return _quick_check_record(connection, calibration_session_id)


def finish_quick_check_split(
    vault: LoadedVault,
    repository: Repository,
    *,
    calibration_session_id: str,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Feed a finished quick check's results into the assumed/learning split.

    Writes one ``quick_check`` decision per assumed LO and records the split on
    the quick check's row, exactly once (the re-check runs inside the write
    transaction). Returns the stored outcome.
    """

    now_iso = utc_now_iso(clock)
    with repository.connection() as connection:
        record = _quick_check_record(connection, calibration_session_id)
        if record is None:
            return None
        if record["finished_at"] is not None:
            return json.loads(record["outcome_json"] or "{}")
        scope = json.loads(record["learning_object_ids_json"])
        answers = quick_check_answers(
            connection, session_id=record["session_id"], scope=scope, started_at=record["created_at"],
        )
        state = load_placement_state_from_connection(connection, active=placement_active(vault))
        blocking = blocking_signals_by_lo(connection, vault, load_answers(connection))
    predictor = active_predictor(vault, repository, now_iso=now_iso)
    split = quick_check_split(vault, predictor, scope=scope, answers_by_lo=answers, blocking=blocking, state=state)
    placement = vault.config.placement
    known = theta_known(placement.known_probability)
    decisions: list[str] = []
    with repository.atomic():
        with repository.connection() as connection:
            current = _quick_check_record(connection, calibration_session_id)
            if current is not None and current["finished_at"] is not None:
                return json.loads(current["outcome_json"] or "{}")
            if placement_active(vault):
                for lo, verdict in split.items():
                    if verdict["verdict"] != "assumed" or _open_assumption_id(connection, lo) is not None:
                        continue
                    region = predictor.region_estimates([lo]).get(lo)
                    decision = _decision_row(
                        vault, predictor, learning_object_id=lo, source="quick_check",
                        trigger_kind="quick_check_result", trigger_ref=calibration_session_id,
                        region=region,
                        inputs=fast_track_inputs(
                            answers.get(lo, ()), blocking.get(lo, ()),
                            min_correct=placement.fast_track_min_correct,
                            q=placement.fast_track_q, known=known,
                        ),
                        now_iso=now_iso, quick_check_session_id=calibration_session_id,
                    )
                    insert_assumption_decision(connection, decision)
                    decisions.append(decision["id"])
                    verdict["assumption_id"] = decision["id"]
            outcome = {
                "split": split,
                "answers": {
                    lo: [answer.attempt_id for answer in rows] for lo, rows in sorted(answers.items()) if rows
                },
                "decisions": decisions,
                "placement_active": placement_active(vault),
            }
            finish_quick_check(
                connection, calibration_session_id, finished_at=now_iso,
                outcome_json=json.dumps(outcome, sort_keys=True),
            )
    if decisions:
        repository.bump_queue_revision(clock=clock)
    return outcome


def finalize_stale_quick_checks(
    vault: LoadedVault,
    repository: Repository,
    *,
    clock: Clock | None = None,
) -> list[str]:
    """Feed the results of quick checks that ended while nobody was looking.

    A quick check ends when its calibration session stops, completes or runs
    past its budget. The split is normally recorded when the calibration screen
    next reads its progress; this records it otherwise, exactly once.
    """

    now = parse_utc(utc_now_iso(clock))
    with repository.connection() as connection:
        pending = [
            str(row[0]) for row in connection.execute(
                "SELECT calibration_session_id FROM placement_quick_checks WHERE finished_at IS NULL"
            ).fetchall()
        ]
    finished: list[str] = []
    for calibration_id in pending:
        record = repository.probe_calibration_session(calibration_id)
        if record is None:
            continue
        if record.status == "active":
            started = parse_utc(record.started_at)
            if started is None or now is None or (now - started).total_seconds() / 60.0 <= record.time_budget_minutes:
                continue  # still running
            repository.end_probe_calibration_session(calibration_id, status="expired", clock=clock)
        finish_quick_check_split(vault, repository, calibration_session_id=calibration_id, clock=clock)
        finished.append(calibration_id)
    return finished

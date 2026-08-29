"""Learning-state changes attributable to one completed practice session."""

from __future__ import annotations

from datetime import datetime

from learnloop.clock import parse_utc
from learnloop.db.repositories import Repository
from learnloop.learner.facet_evidence_timeline import (
    facet_evidence_timelines,
    load_facet_timeline_snapshot,
)
from learnloop.vault.models import LoadedVault


def session_learning_diff(
    vault: LoadedVault, repository: Repository, session_id: str
) -> dict[str, object]:
    session = repository.fetch_session(session_id)
    if session is None or session.get("ended_at") is None:
        return _empty_diff()
    session_row = next(
        (
            row
            for row in repository.review_session_rows()
            if row["id"] == session_id
        ),
        None,
    )
    if session_row is None:
        session_row = session | {
            "attempts": [],
            "predictions_up": 0,
            "predictions_down": 0,
        }
    return session_learning_diffs(vault, repository, [session_row]).get(
        session_id, _empty_diff()
    )


def session_learning_diffs(
    vault: LoadedVault,
    repository: Repository,
    sessions: list[dict],
) -> dict[str, dict[str, object]]:
    """Compute every supplied session diff from one facet-timeline replay."""

    windows: list[tuple[str, datetime, datetime, str, str]] = []
    for session in sessions:
        if session.get("ended_at") is None:
            continue
        started_at = str(session["started_at"])
        ended_at = str(session["ended_at"])
        started = parse_utc(started_at)
        ended = parse_utc(ended_at)
        if started is not None and ended is not None:
            windows.append((str(session["id"]), started, ended, started_at, ended_at))

    facet_ids = {
        vault.canonical_facet_id(str(facet_id))
        for facet_id in vault.evidence_facets
    }
    for item in vault.practice_items.values():
        facet_ids.update(
            vault.canonical_facet_id(str(facet_id))
            for facet_id in item.evidence_facets
        )
    facet_delta_by_session: dict[str, dict[str, float]] = {
        session_id: {} for session_id, _start, _end, _start_raw, _end_raw in windows
    }
    snapshot = load_facet_timeline_snapshot(repository)
    for facet_id, timeline in facet_evidence_timelines(
        vault, repository, facet_ids, snapshot=snapshot
    ).items():
        for point in timeline:
            at = parse_utc(point.t)
            if at is None:
                continue
            # Session windows are normally disjoint, but retain the historical
            # inclusive-window semantics if imported data overlaps them.
            for session_id, started, ended, _start_raw, _end_raw in windows:
                if started <= at <= ended:
                    deltas = facet_delta_by_session[session_id]
                    deltas[facet_id] = deltas.get(facet_id, 0.0) + point.delta

    corrections_by_session = {session_id: 0 for session_id in facet_delta_by_session}
    for records in snapshot.grading_by_attempt.values():
        epochs: dict[str, str] = {}
        for record in records:
            epoch_key = (
                f"revision:{record.grading_revision}"
                if record.grading_revision is not None
                else f"legacy:{record.created_at}"
            )
            epochs.setdefault(epoch_key, record.created_at)
        ordered = sorted(epochs.items(), key=lambda pair: (pair[1], pair[0]))
        for _epoch_key, correction_at in ordered[1:]:
            at = parse_utc(correction_at)
            if at is None:
                continue
            for session_id, started, ended, _start_raw, _end_raw in windows:
                if started <= at <= ended:
                    corrections_by_session[session_id] += 1

    session_by_id = {str(session["id"]): session for session in sessions}
    result: dict[str, dict[str, object]] = {}
    for session_id, _started, _ended, started_at, ended_at in windows:
        session = session_by_id[session_id]
        result[session_id] = {
            "facets_demonstrated": sum(
                delta > 1e-9
                for delta in facet_delta_by_session[session_id].values()
            ),
            "predictions_moved": {
                "up": int(session.get("predictions_up") or 0),
                "down": int(session.get("predictions_down") or 0),
            },
            "corrections": corrections_by_session[session_id],
            "misconceptions_touched": repository.misconception_transition_counts_between(
                started_at, ended_at
            ),
        }
    return result


def _empty_diff() -> dict[str, object]:
    return {
        "facets_demonstrated": 0,
        "predictions_moved": {"up": 0, "down": 0},
        "corrections": 0,
        "misconceptions_touched": {"resolved": 0, "returned": 0},
    }

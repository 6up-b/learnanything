"""Learning-state changes attributable to one completed practice session."""

from __future__ import annotations

from learnloop.clock import parse_utc
from learnloop.db.repositories import Repository
from learnloop.services.facet_evidence_timeline import facet_evidence_timeline
from learnloop.vault.models import LoadedVault


def session_learning_diff(
    vault: LoadedVault, repository: Repository, session_id: str
) -> dict[str, object]:
    session = repository.fetch_session(session_id)
    if session is None or session.get("ended_at") is None:
        return _empty_diff()
    started_at = str(session["started_at"])
    ended_at = str(session["ended_at"])
    started = parse_utc(started_at)
    ended = parse_utc(ended_at)
    if started is None or ended is None:
        return _empty_diff()

    session_row = next(
        (
            row
            for row in repository.review_session_rows()
            if row["id"] == session_id
        ),
        None,
    )
    predictions_up = int(session_row["predictions_up"]) if session_row else 0
    predictions_down = int(session_row["predictions_down"]) if session_row else 0

    facet_ids = {
        vault.canonical_facet_id(str(facet_id))
        for facet_id in vault.evidence_facets
    }
    for item in vault.practice_items.values():
        facet_ids.update(
            vault.canonical_facet_id(str(facet_id))
            for facet_id in item.evidence_facets
        )
    facets_demonstrated = 0
    for facet_id in facet_ids:
        session_delta = 0.0
        for point in facet_evidence_timeline(vault, repository, facet_id):
            at = parse_utc(point.t)
            if at is not None and started <= at <= ended:
                session_delta += point.delta
        if session_delta > 1e-9:
            facets_demonstrated += 1

    return {
        "facets_demonstrated": facets_demonstrated,
        "predictions_moved": {
            "up": predictions_up,
            "down": predictions_down,
        },
        "corrections": repository.grading_correction_count_between(
            started_at, ended_at
        ),
        "misconceptions_touched": repository.misconception_transition_counts_between(
            started_at, ended_at
        ),
    }


def _empty_diff() -> dict[str, object]:
    return {
        "facets_demonstrated": 0,
        "predictions_moved": {"up": 0, "down": 0},
        "corrections": 0,
        "misconceptions_touched": {"resolved": 0, "returned": 0},
    }

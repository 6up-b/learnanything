"""Review-log reconstruction for FSRS fitting.

The live path derives FSRS ratings and elapsed intervals on the fly and never
freezes them per attempt, so a fitting job re-derives them from the raw
``practice_attempts`` stream using the exact live semantics
(``fsrs_rating_for_attempt`` = score binning + hint cap; elapsed = gap between
successive persisted attempts on the item, matching ``_elapsed_days`` reading
``practice_item_state.last_attempt_at``).
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from learnloop.clock import parse_utc
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import fsrs_rating_for_attempt
from learnloop.attempts.evidence import attempt_evidence_mass
from learnloop.scheduling.fsrs import MemoryState, Rating, apply_review, forgetting_curve
from learnloop.vault.models import LoadedVault


@dataclass(frozen=True)
class ReviewObservation:
    practice_item_id: str
    attempt_id: str
    rating: Rating
    elapsed_days: float  # since previous persisted attempt on this item; 0.0 for first
    weight: float  # per-attempt-type evidence mass
    observed_at: datetime
    first_review: bool
    #: False for a grade the proofs route check holds for review (mvp-0.17):
    #: the live schedule applied no review for it, though its time is the
    #: item's last attempt. Only callers that pass ``held_attempt_ids`` set it.
    applies_review: bool = True


@dataclass(frozen=True)
class ReviewLog:
    sequences: dict[str, list[ReviewObservation]]  # per practice_item_id, time-ordered
    total_reviews: int
    data_through: str | None  # max created_at ISO
    skipped_attempts: int  # rows whose item is missing from the vault


def reconstruct_review_log(vault: LoadedVault, repository: Repository) -> ReviewLog:
    return review_log_from_attempts(vault, repository.list_all_attempts())


def review_log_from_attempts(
    vault: LoadedVault,
    rows: Iterable[Mapping[str, Any]],
    *,
    skip_ungraded: bool = False,
    held_attempt_ids: Collection[str] = frozenset(),
) -> ReviewLog:
    """The review log of ``rows`` (``practice_attempts`` rows ordered by item,
    then time, as ``Repository.list_all_attempts`` returns them).

    ``skip_ungraded`` leaves out attempts with no rubric score (an answer still
    waiting for its grade), counted as skipped, instead of failing on them:
    the router's outcome replayer reads the log on every rebuild (R1, D12).
    ``held_attempt_ids`` (mvp-0.17) marks the grades the proofs route check
    holds for review: their observation applies no review
    (``applies_review``), as on the live schedule.
    """

    sequences: dict[str, list[ReviewObservation]] = {}
    total = 0
    skipped = 0
    data_through: str | None = None
    last_seen: dict[str, datetime] = {}

    for row in rows:
        created_at_iso = row["created_at"]
        if data_through is None or created_at_iso > data_through:
            data_through = created_at_iso
        item = vault.practice_items.get(row["practice_item_id"])
        if item is None:
            # Vault content changed since the attempt; rubric/hint policy are
            # unresolvable so live rating semantics can't be reproduced.
            skipped += 1
            continue
        if skip_ungraded and row["rubric_score"] is None:
            skipped += 1
            continue
        observed_at = parse_utc(created_at_iso)
        if observed_at is None:
            skipped += 1
            continue
        rubric = vault.rubric_for_item(item)
        max_points = rubric.max_points if rubric is not None else 4
        rating = fsrs_rating_for_attempt(item, int(row["rubric_score"]), max_points, int(row["hints_used"] or 0))
        previous = last_seen.get(item.id)
        elapsed_days = max(0.0, (observed_at - previous).total_seconds() / 86400) if previous else 0.0
        observation = ReviewObservation(
            practice_item_id=item.id,
            attempt_id=row["id"],
            rating=rating,
            elapsed_days=elapsed_days,
            weight=attempt_evidence_mass(row["attempt_type"], vault.config.evidence),
            observed_at=observed_at,
            first_review=previous is None,
            applies_review=row["id"] not in held_attempt_ids,
        )
        sequences.setdefault(item.id, []).append(observation)
        last_seen[item.id] = observed_at
        total += 1

    return ReviewLog(
        sequences=sequences,
        total_reviews=total,
        data_through=data_through,
        skipped_attempts=skipped,
    )


def predicted_retrievability_by_attempt(
    review_log: ReviewLog, weights: tuple[float, ...]
) -> dict[str, float]:
    """FSRS-predicted retrievability at each reviewed attempt (router R1, D12).

    Chains each item's (rating, elapsed) sequence through ``apply_review``
    exactly as :func:`learnloop.scheduling.fsrs_fitting.review_log_loss` does:
    an attempt's prediction is the forgetting curve of the memory left by the
    item's earlier reviews, after the elapsed days. An item's first review has
    no memory yet, so it has no prediction (absent from the map). An
    observation that applies no review (a grade held for review, mvp-0.17) is
    predicted like any other and leaves the memory as it was; the next one's
    elapsed days still count from it, as the live schedule's
    ``last_attempt_at`` does.
    """

    predictions: dict[str, float] = {}
    for sequence in review_log.sequences.values():
        state: MemoryState | None = None
        for observation in sequence:
            if state is not None:
                predictions[observation.attempt_id] = forgetting_curve(
                    state.stability, observation.elapsed_days, weights
                )
            if observation.applies_review:
                state = apply_review(state, observation.rating, observation.elapsed_days, weights)
    return predictions


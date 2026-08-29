"""Review-log reconstruction for FSRS fitting.

The live path derives FSRS ratings and elapsed intervals on the fly and never
freezes them per attempt, so a fitting job re-derives them from the raw
``practice_attempts`` stream using the exact live semantics
(``fsrs_rating_for_attempt`` = score binning + hint cap; elapsed = gap between
successive persisted attempts on the item, matching ``_elapsed_days`` reading
``practice_item_state.last_attempt_at``).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from learnloop.clock import parse_utc
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import fsrs_rating_for_attempt
from learnloop.attempts.evidence import attempt_evidence_mass
from learnloop.scheduling.fsrs import Rating
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


@dataclass(frozen=True)
class ReviewLog:
    sequences: dict[str, list[ReviewObservation]]  # per practice_item_id, time-ordered
    total_reviews: int
    data_through: str | None  # max created_at ISO
    skipped_attempts: int  # rows whose item is missing from the vault


def reconstruct_review_log(vault: LoadedVault, repository: Repository) -> ReviewLog:
    sequences: dict[str, list[ReviewObservation]] = {}
    total = 0
    skipped = 0
    data_through: str | None = None
    last_seen: dict[str, datetime] = {}

    for row in repository.list_all_attempts():
        created_at_iso = row["created_at"]
        if data_through is None or created_at_iso > data_through:
            data_through = created_at_iso
        item = vault.practice_items.get(row["practice_item_id"])
        if item is None:
            # Vault content changed since the attempt; rubric/hint policy are
            # unresolvable so live rating semantics can't be reproduced.
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

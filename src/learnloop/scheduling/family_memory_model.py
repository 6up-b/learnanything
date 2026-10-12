"""Pure shadow FSRS fold shared by the PF-a projection and the offline memory arms.

Rows are the learner-field outcome rows (``learnloop.field.types.AttemptRow``),
read by attribute only so scheduling never imports the field package. A row
trains this fold only when ``row.memory_eligible``: a graded cold retrieval of
an unfamilied item or a ``same_target``/``isomorph`` family member. Nothing here
reads a store or serves a schedule.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import math

from learnloop.clock import parse_utc
from learnloop.scheduling.fsrs import MemoryState, Rating, apply_review, forgetting_curve

MEMORY_KEYS = ("item", "family", "lo")


def weights_digest(weights: tuple[float, ...]) -> str:
    return hashlib.sha256(json.dumps(list(weights), sort_keys=True).encode()).hexdigest()


def _instant(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    parsed = parse_utc(value)
    if parsed is None:
        raise ValueError("memory replay needs a valid timestamp")
    return parsed


@dataclass
class MemoryHistory:
    state: MemoryState
    last_review_at: datetime
    review_count: int


class FamilyMemory:
    """FSRS state per item, family or LO key; a point predictor, never active."""

    granularity = "attempt"
    uses_graded_memory = True
    calibrated_uncertainty = False

    def __init__(self, key: str, weights: tuple[float, ...], *,
                 weight_label: str = "defaults", distance_discount: bool = False):
        if key not in MEMORY_KEYS:
            raise ValueError("unknown memory key")
        self.key, self.weights, self.distance_discount = key, tuple(weights), distance_discount
        self.weight_label = weight_label
        self.name = f"memory_{key}/{weight_label}" + ("/distance" if distance_discount else "")
        self.version_hash = hashlib.sha256(json.dumps(
            ["fsrs-key-v3", key, list(self.weights), distance_discount, "cold_start=0.5"],
        ).encode()).hexdigest()
        self.history: dict[str, MemoryHistory] = {}

    def key_for(self, features) -> str:
        if self.key == "lo":
            return "lo:" + features.lo_id
        if self.key == "family" and features.family_id:
            return "family:" + features.family_id
        return "item:" + features.item_id

    def predict(self, features) -> float:
        if hasattr(features, "outcome") or hasattr(features, "effective_mass"):
            raise TypeError("predict requires outcome-free ItemFeatures")
        prior = self.history.get(self.key_for(features))
        if prior is None:
            # An explicit cold-start constant, not a fabricated FSRS history.
            return 0.5
        elapsed = (_instant(features.observed_at) - prior.last_review_at).total_seconds() / 86400
        return min(1 - 1e-9, max(1e-9, forgetting_curve(prior.state.stability, elapsed, self.weights)))

    def scores(self, row) -> bool:
        """Memory arms are scored on graded cold retrievals only, never warm rows."""
        return bool(getattr(row, "memory_scored", False))

    def observe(self, row) -> None:
        # Signals carry no review, and a facet row repeats its attempt's review.
        if getattr(row, "facet_id", None) is not None or not getattr(row, "memory_eligible", False):
            return
        f = row.features
        at = _instant(f.observed_at)
        key = self.key_for(f)
        prior = self.history.get(key)
        elapsed = (at - prior.last_review_at).total_seconds() / 86400 if prior else 0
        state = apply_review(prior.state if prior else None, Rating(row.fsrs_rating), elapsed, self.weights)
        if self.distance_discount and f.variant_distance is not None:
            credit = math.exp(-max(0.0, f.variant_distance))
            # Discount only positive stability credit, never a failure.
            baseline = prior.state.stability if prior else 0.001
            if state.stability > baseline:
                state = MemoryState(state.difficulty, baseline + credit * (state.stability - baseline),
                                    state.retrievability)
        self.history[key] = MemoryHistory(state, at, prior.review_count + 1 if prior else 1)

    def rebuild(self, rows) -> None:
        self.history = {}
        for row in sorted(rows, key=lambda r: (r.features.observed_at, getattr(r, "attempt_id", ""))):
            self.observe(row)

    def snapshot_bytes(self) -> bytes:
        return json.dumps({
            key: [h.state.difficulty, h.state.stability, h.state.retrievability,
                  h.last_review_at.isoformat(), h.review_count]
            for key, h in sorted(self.history.items())
        }, sort_keys=True).encode()

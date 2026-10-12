"""Pure shadow FSRS fold shared by rebuilding and offline evaluation, not serving."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math

from learnloop.offline_outcomes import OutcomeRow, PredictionRow, digest
from learnloop.scheduling.fsrs import MemoryState, Rating, apply_review, forgetting_curve


@dataclass
class MemoryHistory:
    state: MemoryState
    last_review_at: datetime
    review_count: int


class FamilyMemory:
    granularity = "attempt"
    uses_graded_memory = True

    def __init__(self, key: str, weights: tuple[float, ...], *,
                 weight_label: str = "defaults", distance_discount: bool = False):
        if key not in {"item", "family", "lo"}:
            raise ValueError("unknown memory key")
        self.key, self.weights, self.distance_discount = key, weights, distance_discount
        self.name = f"memory_{key}/{weight_label}" + ("/distance" if distance_discount else "")
        self.version_hash = digest(["fsrs-key-v2", key, weights, distance_discount, "cold_start=0.5"])
        self.history: dict[str, MemoryHistory] = {}

    def key_for(self, row: PredictionRow) -> str:
        if self.key == "lo":
            return "lo:" + row.lo_id
        if self.key == "family" and row.family_id:
            return "family:" + row.family_id
        return "item:" + row.item_id

    def predict(self, row: PredictionRow) -> float:
        prior = self.history.get(self.key_for(row))
        if prior is None:
            return 0.5
        elapsed = (row.observed_at - prior.last_review_at).total_seconds()/86400
        return min(1-1e-9, max(1e-9, forgetting_curve(prior.state.stability, elapsed, self.weights)))

    def scores(self, row: OutcomeRow) -> bool:
        return row.cold

    def observe(self, row: OutcomeRow) -> None:
        # Near/far are prediction-only transfer probes for EVERY memory key.
        if not row.memory_eligible:
            return
        f = row.features
        key = self.key_for(f)
        prior = self.history.get(key)
        elapsed = (f.observed_at-prior.last_review_at).total_seconds()/86400 if prior else 0
        state = apply_review(prior.state if prior else None, Rating(row.rating), elapsed, self.weights)
        if self.distance_discount and f.variant_distance is not None:
            credit = math.exp(-max(0.0, f.variant_distance))
            # Discount only positive stability credit, never a failure.
            baseline = prior.state.stability if prior else 0.001
            if state.stability > baseline:
                state = MemoryState(state.difficulty, baseline + credit*(state.stability-baseline),
                                    state.retrievability)
        self.history[key] = MemoryHistory(state, f.observed_at, prior.review_count+1 if prior else 1)

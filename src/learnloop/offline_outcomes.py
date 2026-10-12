"""Immutable, text-free offline replay records; no domain/store dependencies."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


@dataclass(frozen=True)
class PredictionRow:
    attempt_id: str
    observed_at: datetime
    item_id: str
    lo_id: str
    family_id: str | None = None
    variant_relation: str | None = None
    subject: str = "unknown"
    topic: str = "unknown"
    serving_origin: str = "unknown"
    revision_status: str = "original"
    grader_model: str = "unknown"
    observation_status: str = "graded"
    discrimination: float = 1.0
    difficulty: float = 0.0
    difficulty_variance: float = 0.0
    effective_mass: float = 1.0
    # Only a past-administered, skeleton-derived measurement may populate this.
    variant_distance: float | None = None
    family_judge_models: tuple[str, ...] = ()


@dataclass(frozen=True)
class OutcomeRow:
    features: PredictionRow
    outcome: float
    rating: int
    exclusion: str | None = None
    cold: bool = True

    @property
    def memory_eligible(self) -> bool:
        """A graded cold retrieval, independent of calibrated ability mass.

        Adapters must exclude ungraded/quarantined records explicitly; a legacy
        grade with no calibration can still be a legitimate FSRS review.
        """
        return (
            self.exclusion is None and self.cold
            and self.features.variant_relation not in {"near", "far"}
            and (self.features.family_id is None
                 or self.features.variant_relation in {"same_target", "isomorph"})
        )

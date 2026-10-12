"""Immutable, store-free inputs to the prequential learner-field models.

Only ``ItemFeatures`` crosses the prediction boundary. Outcomes and reliability
are delivered afterward, in observation rows. Identifiers are opaque strings;
timestamps are UTC ISO strings, normalized by the projection layer.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from math import isfinite
from typing import Iterable, Mapping, Protocol, runtime_checkable


@dataclass(frozen=True)
class ArmConstants:
    general_variance: float = 0.75
    lo_variance: float = 2.25
    practice_gamma: float = 0.2
    offset_variance: float = 0.25
    retrievability_beta: float = 0.5
    hint_step: float = 0.2
    hint_floor: float = 0.2
    early_help_cap: float = 0.3
    signal_scale: float = 1.0
    signal_daily_cap: float = 0.3

    def __post_init__(self) -> None:
        for member in fields(self):
            value = getattr(self, member.name)
            if not isfinite(value) or value < 0:
                raise ValueError(f"{member.name} must be finite and nonnegative")
        if self.general_variance + self.lo_variance <= 0:
            raise ValueError("the total ability prior variance must be positive")
        if any(value > 1 for value in (self.hint_step, self.hint_floor, self.early_help_cap)):
            raise ValueError("hint fractions must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class ItemFeatures:
    item_id: str
    lo_id: str
    observed_at: str
    subject_id: str = "default"
    a: float = 1.0
    b: float = 0.0
    difficulty_source: str = "authored"
    difficulty_variance: float = 0.0
    primed: bool = False
    cold: bool = True
    capability: str | None = None
    variant_relation: str | None = None
    family_id: str | None = None
    retrievability: float | None = None
    facet_id: str | None = None
    facet_share: float = 1.0


@dataclass(frozen=True, slots=True)
class AttemptRow:
    attempt_id: str
    features: ItemFeatures
    outcome: float
    effective_mass: float
    revision_status: str = "exact"
    assisted: bool = False
    hints_used: int = 0
    help_before_work: bool = False
    # Recomputed from the effective-observation factors with ONLY assistance
    # removed. Never recover it by division: the discount can be zero.
    mass_without_assistance: float | None = None
    serving_origin: str = "unknown"
    serving_propensity: float | None = None
    scheduler_candidate_id: str | None = None
    surface_group_id: str | None = None
    item_snapshot_hash: str | None = None
    interpretation_variance: float = 0.0
    preceded_by_question: bool = False

    @property
    def observed_at(self) -> str:
        return self.features.observed_at

    @property
    def lo_id(self) -> str:
        return self.features.lo_id


@dataclass(frozen=True, slots=True)
class FacetRow(AttemptRow):
    facet_id: str = ""
    facet_share: float = 1.0


@dataclass(frozen=True, slots=True)
class SignalRow:
    signal_id: str
    lo_id: str
    observed_at: str
    signal_type: str
    outcome: float | None = None
    effective_mass: float = 0.0
    subject_id: str = "default"
    facet_id: str | None = None
    attempt_id: str | None = None
    help_before_work: bool = False
    leak_suspected: bool = False


ObservationRow = AttemptRow | FacetRow | SignalRow


@dataclass(frozen=True, slots=True)
class ItemPrediction:
    p_success: float
    logit_variance: float
    region_loadings: tuple[tuple[str, float], ...] = ()


@dataclass(frozen=True, slots=True)
class RegionEstimate:
    mean: float
    variance: float
    n_eff: float
    untested: bool


@runtime_checkable
class Predictor(Protocol):
    name: str
    version_hash: str
    granularity: str

    def predict(self, features: ItemFeatures) -> float: ...
    def observe(self, row: ObservationRow) -> None: ...


@runtime_checkable
class LearnerPredictor(Predictor, Protocol):
    calibrated_uncertainty: bool

    def predict_item(self, item: ItemFeatures | str) -> ItemPrediction: ...
    def conditional_gain(
        self,
        item: ItemFeatures | str,
        chosen: Iterable[ItemFeatures | str],
        weights: Mapping[str, float],
    ) -> float: ...
    def region_estimates(
        self, scope: Iterable[str] | None = None
    ) -> dict[str, RegionEstimate]: ...
    def rebuild(self, rows: Iterable[ObservationRow]) -> None: ...

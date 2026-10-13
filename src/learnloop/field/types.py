"""Immutable, store-free inputs to the prequential learner-field models.

Only ``ItemFeatures`` crosses the prediction boundary. Outcomes and reliability
are delivered afterward, in observation rows. Identifiers are opaque strings;
timestamps are UTC ISO strings, normalized by the projection layer.

The same rows feed every offline arm, including the PF-a memory arms: an
``AttemptRow`` also carries the persisted FSRS rating and the strict
retrieval-coldness verdict those arms train on (``memory_eligible``).
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
    # PF-a idea_hier family effect u_F ~ N(0, 0.5), independent in v1.
    family_variance: float = 0.5

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
    # Only a past-administered, skeleton-derived measurement may populate this
    # (PF-b). Authored transfer labels are never substituted for it.
    variant_distance: float | None = None


# Graded cold retrievals of these relations train family memory; ``near`` and
# ``far`` variants are prediction-only transfer probes (PF-a P11 default).
MEMORY_TRAINING_RELATIONS = frozenset({"same_target", "isomorph"})

#: The learner's pre-answer confidence tap (``practice_attempts.answer_confidence``,
#: 1-5) as a probability, the explicit consumption-time mapping of the
#: calibration duel (spec_hypothesis_surfaces §4.6). Stored taps stay 1-5.
ANSWER_CONFIDENCE_PROBABILITY: Mapping[int, float] = {1: 0.10, 2: 0.30, 3: 0.50, 4: 0.70, 5: 0.90}


@dataclass(frozen=True, slots=True)
class AnswerSignals:
    """What the learner's own answer says about its chance, before its grade.

    Only the offline answer-signal arms read this (``uses_answer_signals``);
    it never reaches ``ItemFeatures``, so no other arm or cache key changes.

    * ``confidence``: the pre-answer tap (1-5), taken after the learner
      composed the answer and before submit/reveal; None when skipped.
    * ``hedged_share``: of the criteria the grader read the learner's tone on
      (``grading_evidence.learner_confidence`` = confident or hedged), the
      share it read as hedged; None when it read none. The grader reads the
      answer text in the same call that grades it, so this signal shares that
      call (the report labels it so).
    """

    confidence: int | None = None
    hedged_share: float | None = None
    hedging_read: int = 0

    def __post_init__(self) -> None:
        if self.confidence is not None and self.confidence not in ANSWER_CONFIDENCE_PROBABILITY:
            raise ValueError("answer confidence must be 1-5 or None")
        if self.hedged_share is not None and not (
            isfinite(self.hedged_share) and 0.0 <= self.hedged_share <= 1.0
        ):
            raise ValueError("hedged_share must be in [0, 1] or None")
        if self.hedging_read < 0:
            raise ValueError("hedging_read must be nonnegative")


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
    # Memory-arm inputs. ``fsrs_rating`` is the persisted rounded, capped grade
    # of a graded retrieval (None for anything else, including quarantine).
    # ``retrieval_cold`` is the strict research coldness: unassisted graded
    # retrieval with no reveal in its window and passing coldness receipts.
    fsrs_rating: int | None = None
    retrieval_cold: bool = False
    grader_model: str = "unknown"
    calibration_status: str = "unknown"
    family_judge_models: tuple[str, ...] = ()
    # Offline answer-signal arms only (confidence tap, grader-read hedging).
    # None: no signal was loaded for this row (every arm but those ignores it).
    answer_signals: AnswerSignals | None = None

    @property
    def observed_at(self) -> str:
        return self.features.observed_at

    @property
    def lo_id(self) -> str:
        return self.features.lo_id

    @property
    def memory_scored(self) -> bool:
        """A graded cold retrieval that memory arms predict and are scored on.

        Independent of ability mass: an uncalibrated legacy grade can be an
        FSRS review without becoming invented ability evidence.
        """
        return (
            self.revision_status != "excluded"
            and self.fsrs_rating is not None
            and self.retrieval_cold
        )

    @property
    def memory_eligible(self) -> bool:
        """A scored retrieval that also trains memory (not a transfer probe)."""
        f = self.features
        return self.memory_scored and (
            f.variant_relation in MEMORY_TRAINING_RELATIONS
            if f.family_id is not None
            else f.variant_relation not in {"near", "far"}
        )


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

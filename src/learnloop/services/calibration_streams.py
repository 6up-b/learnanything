"""The three calibration streams + retrospective bootstrap (§4.7).

Never conflated (U-020): error-intake (MNAR, never a denominator), the stratified
calibration stream (logged inclusion probabilities, IPW-reweighted), and
adjudicated anchors (authority-grade single datapoints under bounded trust). All
three append to ``calibration_stream_samples`` with their stream tag; the
denominator rule (only calibration + adjudicated_anchor bear counts) is enforced in
:func:`grader_calibration.denominator_counts_from_samples`.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.activities import _json
from learnloop.services.grade_classifier import bucket_confidence, length_bucket_for_text

# Stratified calibration-stream design (§4.7). Registered heuristic decision
# parameters. Every attempt keeps a KNOWN NONZERO inclusion probability so IPW
# recovers unbiased confusion estimates -- no stratum is ever dropped to zero.
CALIBRATION_BASE_INCLUSION_PROBABILITY = 0.05  # decision parameter: heuristic
OVERSAMPLE_LOW_CONFIDENCE = 5.0  # decision parameter: heuristic
OVERSAMPLE_HIGH_INFLUENCE = 5.0  # decision parameter: heuristic
OVERSAMPLE_PARTIAL_BOUNDARY = 5.0  # decision parameter: heuristic

# The MNAR error-intake tap has an unknown selection probability; a nominal
# positive value is stored (CHECK inclusion_probability > 0) and documented as
# NON-denominator -- it never feeds a confusion count (§4.7, §9.1).
ERROR_INTAKE_NOMINAL_INCLUSION = 1.0  # decision parameter: heuristic (non-denominator)


def _partial_credit_boundary(correctness: float | None) -> bool:
    """A partial-credit-boundary attempt for stratification (§4.7, §10 param 8):
    an outcome strictly between full and zero credit."""

    if correctness is None:
        return False
    return 0.0 < float(correctness) < 1.0  # decision parameter: heuristic


def stratum_for(
    *,
    confidence_bucket: str,
    influence_flag: bool,
    partial_boundary: bool,
    domain: str | None,
    length_bucket: str,
) -> dict[str, Any]:
    return {
        "confidence_bucket": confidence_bucket,
        "influence_flag": bool(influence_flag),
        "partial_boundary": bool(partial_boundary),
        "domain": domain,
        "length_bucket": length_bucket,
    }


def inclusion_probability_for(stratum: Mapping[str, Any]) -> float:
    """The stratified inclusion probability (§4.7). Oversample low-confidence,
    high-influence, and partial-credit-boundary strata; cap at 1.0; never 0."""

    p = CALIBRATION_BASE_INCLUSION_PROBABILITY
    if stratum.get("confidence_bucket") == "low":
        p *= OVERSAMPLE_LOW_CONFIDENCE
    if stratum.get("influence_flag"):
        p *= OVERSAMPLE_HIGH_INFLUENCE
    if stratum.get("partial_boundary"):
        p *= OVERSAMPLE_PARTIAL_BOUNDARY
    return min(1.0, p)


def should_sample(
    stratum: Mapping[str, Any], *, key: str, frame_id: str
) -> tuple[bool, float]:
    """Deterministic stratified draw keyed on (frame_id, key) so the frame is
    reproducible (§4.7 'the sampling frame and probabilities are logged')."""

    p = inclusion_probability_for(stratum)
    rng = random.Random(f"{frame_id}:{key}")
    return rng.random() < p, p


@dataclass
class BootstrapFrame:
    frame_id: str
    total_attempts: int = 0
    selected: int = 0
    stratum_counts: dict[str, int] = field(default_factory=dict)
    samples: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "total_attempts": self.total_attempts,
            "selected": self.selected,
            "stratum_counts": self.stratum_counts,
            "samples": self.samples,
        }


def build_bootstrap_frame(
    repository: Repository,
    *,
    frame_id: str | None = None,
    clock: Clock | None = None,
) -> BootstrapFrame:
    """Draw a stratified sample over existing attempt history (§4.7 bootstrap).

    Read-only over history + append-only sample rows: writes one
    ``calibration_stream_samples`` row (stream='calibration') per SELECTED attempt
    with a shared ``sampling_frame_id`` and its logged inclusion probability, so the
    batch composes with the ongoing stream. The actual owner adjudication happens
    later (those become adjudicated_anchor samples + the first denominator counts)."""

    frame = BootstrapFrame(frame_id=frame_id or new_ulid())
    attempts = repository.list_all_attempts()
    frame.total_attempts = len(attempts)
    for attempt in attempts:
        confidence_bucket = bucket_confidence(attempt.get("grader_confidence"))
        correctness = attempt.get("correctness")
        partial_boundary = _partial_credit_boundary(correctness)
        _, length_bucket = length_bucket_for_text(attempt.get("learner_answer_md"))
        stratum = stratum_for(
            confidence_bucket=confidence_bucket,
            influence_flag=False,
            partial_boundary=partial_boundary,
            domain=attempt.get("learning_object_id"),
            length_bucket=length_bucket,
        )
        selected, p = should_sample(stratum, key=attempt["id"], frame_id=frame.frame_id)
        stratum_key = _json(stratum)
        frame.stratum_counts[stratum_key] = frame.stratum_counts.get(stratum_key, 0) + 1
        if not selected:
            continue
        observation = repository.observation_by_attempt(attempt["id"])
        sample_id = repository.insert_calibration_stream_sample(
            values={
                "observation_id": observation["id"] if observation else None,
                "administration_id": observation["administration_id"] if observation else None,
                "attempt_id": attempt["id"],
                "stream": "calibration",
                "stratum_json": stratum_key,
                "inclusion_probability": p,
                "sampling_frame_id": frame.frame_id,
                "selected": True,
            },
            clock=clock,
        )
        frame.selected += 1
        frame.samples.append(
            {
                "sample_id": sample_id,
                "attempt_id": attempt["id"],
                "inclusion_probability": p,
                "stratum": stratum,
            }
        )
    return frame


def record_error_intake_sample(
    repository: Repository,
    *,
    observation_id: str | None,
    administration_id: str | None,
    raw_grade_event_id: str | None,
    stratum: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> str:
    """Tap a misgraded/ambiguous affect signal into the error-intake stream (§4.7).
    MNAR by construction -- never a calibration denominator."""

    return repository.insert_calibration_stream_sample(
        values={
            "observation_id": observation_id,
            "administration_id": administration_id,
            "raw_grade_event_id": raw_grade_event_id,
            "stream": "error_intake",
            "stratum_json": _json(dict(stratum) if stratum else {}),
            "inclusion_probability": ERROR_INTAKE_NOMINAL_INCLUSION,
            "selected": True,
        },
        clock=clock,
    )


def record_adjudicated_anchor_sample(
    repository: Repository,
    *,
    observation_id: str | None,
    administration_id: str | None,
    raw_grade_event_id: str | None,
    stratum: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> str:
    """Log an adjudicated anchor (§4.7): authority-grade single datapoint,
    inclusion_probability = 1.0."""

    return repository.insert_calibration_stream_sample(
        values={
            "observation_id": observation_id,
            "administration_id": administration_id,
            "raw_grade_event_id": raw_grade_event_id,
            "stream": "adjudicated_anchor",
            "stratum_json": _json(dict(stratum) if stratum else {}),
            "inclusion_probability": 1.0,
            "selected": True,
        },
        clock=clock,
    )

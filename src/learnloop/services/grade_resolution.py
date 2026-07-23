"""Grade resolution pipeline + dual-write (spec_p0_measurement_correctness §4.1,
§4.4). Implements the nine-step pipeline: append raw grade event, classify G,
resolve the calibration model + parent mixture, append a calibrated interpretation
with P(Z|E)/interval/certainty, run review-and-influence checks, and set the
projection head -- WITHOUT touching any legacy posterior or certification (that is
P0.3). The three legacy writers (practice attempts, probe submission, exam answer)
dual-write these append-only rows alongside their existing summary writes.

Dual-write is fail-safe (§7.3): a resolution failure NEVER breaks the legacy path;
it is swallowed by :func:`record_grade_dual_write` and recoverable by P0.3 replay.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.activities import (
    _json,
    append_observation,
    open_administration,
    resolve_legacy_item,
)
from learnloop.services import effective_observation as eo
from learnloop.services import grader_calibration as gc
from learnloop.services.grade_classifier import (
    CRITERION_CLASSIFIER_VERSION,
    RESPONSE_CLASSIFIER_VERSION,
    bucket_confidence,
    classify_criteria,
    classify_response,
    length_bucket_for_text,
    schema_shape_from_row,
)
from learnloop.services.fitted_params import resolve_grader_channel_prior
from learnloop.services.outcome_schemas import COARSE_RESPONSE_SLUG, resolve_schema_id
from learnloop.vault.models import LoadedVault, PracticeItem

_LOGGER = logging.getLogger(__name__)

PROJECTION_ALGORITHM_VERSION = "grade_interpretation_v1"

# The existing 0.40 grader-confidence review threshold (grading.py), now a
# registered heuristic decision parameter (§4.4). The influence tests, not this
# scalar alone, govern consequence.
REVIEW_CONFIDENCE_THRESHOLD = 0.40  # decision parameter: heuristic

# A leading-class posterior below this reads as fragile / high-influence (§4.4).
INFLUENCE_CERTAINTY_FLOOR = 0.50  # decision parameter: heuristic

# Bounded trust for learner-clarification adjudications (§3.3/§4.4/§4.7).
BOUNDED_TRUST_WEIGHT_DEFAULT = 0.5  # decision parameter: heuristic


@dataclass(frozen=True)
class GradeResolution:
    administration_id: str
    observation_id: str
    raw_grade_event_id: str
    interpretation_id: str
    observed_class: str
    confidence_bucket: str
    posterior: dict[str, float]
    certainty: float
    credible_interval: dict[str, float]
    calibration_model_id: str
    calibration_model_hash: str
    review_flag: bool
    influence_flag: bool
    fallback_reason: str | None
    unclassifiable: bool


def resolve_grade(
    vault: LoadedVault,
    repository: Repository,
    *,
    item: PracticeItem,
    purpose: str,
    grading_source: str,
    attempt_id: str,
    response_text: str | None,
    rubric_score: int | None,
    max_points: int,
    grader_confidence: float | None = None,
    has_fatal: bool = False,
    signature_matched: bool = False,
    criterion_points: Mapping[str, float] | None = None,
    criterion_max: Mapping[str, float] | None = None,
    raw_output: Mapping[str, Any] | None = None,
    criterion_evidence: Any = None,
    agent_run_id: str | None = None,
    role: str = "primary",
    domain: str | None = None,
    declared_length_bucket: str | None = None,
    outcome_schema_slug: str = COARSE_RESPONSE_SLUG,
    observed_class_override: str | None = None,
    grader_model_revision: str | None = None,
    administration_id: str | None = None,
    observation_id: str | None = None,
    surface_id: str | None = None,
    feedback_condition: str | None = None,
    clock: Clock | None = None,
) -> GradeResolution:
    """The §4.1 pipeline for one graded response. May raise; callers that dual-write
    from a legacy path use :func:`record_grade_dual_write` (guarded)."""

    # Step 1-2: resolve (or reuse) an administration + observation for this response.
    if administration_id is None or observation_id is None or surface_id is None:
        surface_id, administration_id, observation_id = ensure_administration_identity(
            vault,
            repository,
            item=item,
            purpose=purpose,
            attempt_id=attempt_id,
            feedback_condition=feedback_condition,
            clock=clock,
        )

    # Outcome schema shape + G classification (step 4).
    schema_id, schema_version = resolve_schema_id(repository, outcome_schema_slug, clock=clock)
    schema_row = repository.fetch_outcome_schema_version_by_id(schema_id, schema_version)
    shape = schema_shape_from_row(schema_row)

    response_empty = not (response_text or "").strip()
    if observed_class_override is not None:
        observed_class = observed_class_override
        unclassifiable = observed_class not in shape.observed_classes
        if unclassifiable:
            observed_class = "other"
    else:
        classification = classify_response(
            rubric_score=rubric_score,
            max_points=max_points,
            schema=shape,
            has_fatal=has_fatal,
            response_empty=response_empty,
            signature_matched=signature_matched,
        )
        observed_class = classification.observed_class
        unclassifiable = classification.unclassifiable

    confidence_bucket = bucket_confidence(grader_confidence)
    word_count, observed_length_bucket = length_bucket_for_text(response_text)
    declared_bucket = declared_length_bucket or observed_length_bucket

    criterion_classes: dict[str, str] | None = None
    if criterion_points is not None and criterion_max is not None:
        criterion_classes = classify_criteria(
            criterion_points=criterion_points, criterion_max=criterion_max
        )

    gih = gc.grader_identity_hash(
        provider=grading_source,
        model_revision=grader_model_revision,
        prompt_version=gc.GRADING_PROMPT_VERSION,
        output_schema_version=gc.GRADER_OUTPUT_SCHEMA_VERSION,
    )
    context_features = {
        "grader_identity_hash": gih,
        "outcome_schema_id": schema_id,
        "outcome_schema_version": schema_version,
        "domain": domain,
        "length_bucket": declared_bucket,
        "purpose": purpose,
    }

    # Step 3: append the raw grade event (no posterior touched).
    raw_output_payload = dict(raw_output) if raw_output is not None else {
        "rubric_score": rubric_score,
        "max_points": max_points,
        "grader_confidence": grader_confidence,
        "grading_source": grading_source,
    }
    raw_event_id = repository.insert_raw_grade_event(
        values={
            "administration_id": administration_id,
            "observation_id": observation_id,
            "attempt_id": attempt_id,
            "response_ref": attempt_id,
            "role": role,
            "grader_provider": grading_source,
            "grader_model_revision": grader_model_revision,
            "grading_prompt_version": gc.GRADING_PROMPT_VERSION,
            "grader_output_schema_version": gc.GRADER_OUTPUT_SCHEMA_VERSION,
            "grader_identity_hash": gih,
            "agent_run_id": agent_run_id,
            "raw_output_json": _json(raw_output_payload),
            "criterion_evidence_json": _json(criterion_evidence) if criterion_evidence is not None else None,
            "observed_class": observed_class,
            "model_confidence": grader_confidence,
            "confidence_bucket": confidence_bucket,
            "criterion_observed_classes_json": _json(criterion_classes) if criterion_classes else None,
            "response_classifier_version": RESPONSE_CLASSIFIER_VERSION,
            "criterion_classifier_version": CRITERION_CLASSIFIER_VERSION if criterion_classes else None,
            "context_features_json": _json(context_features),
            "exact_word_count": word_count,
            "declared_length_bucket": declared_bucket,
        },
        clock=clock,
    )
    repository.append_measurement_event(
        administration_id=administration_id,
        kind="raw_grade_appended",
        algorithm_version=PROJECTION_ALGORITHM_VERSION,
        observation_id=observation_id,
        payload_json=_json({"raw_grade_event_id": raw_event_id, "role": role}),
        clock=clock,
    )
    repository.append_measurement_event(
        administration_id=administration_id,
        kind="grade_classified",
        algorithm_version=RESPONSE_CLASSIFIER_VERSION,
        observation_id=observation_id,
        payload_json=_json({"observed_class": observed_class, "unclassifiable": unclassifiable}),
        clock=clock,
    )

    # Step 5: resolve the calibration model + parent mixture.
    resolved_model = gc.resolve_calibration_model(
        repository,
        grader_identity_hash=gih,
        outcome_schema_id=schema_id,
        outcome_schema_version=schema_version,
        domain=domain,
        length_bucket=declared_bucket,
        clock=clock,
    )

    # Step 6: calibrated posterior + interval + certainty.
    posterior = gc.posterior_over_true_class(
        resolved_model, observed_class=observed_class, confidence_bucket=confidence_bucket
    )
    interval = gc.credible_interval(
        resolved_model, observed_class=observed_class, confidence_bucket=confidence_bucket
    )
    certainty = gc.certainty(posterior)

    # H1 (§4.3 final ¶): compute the ONE certainty LCB from the pooled resolved
    # model and persist it. Both the mastery path (response_certainty_lcb) and the
    # certification path (EffectiveObservation) read this exact value, so they can
    # never disagree about grader trust.
    shared_lcb = eo.shared_certainty_lcb(
        joint_alpha=resolved_model.joint_alpha,
        observed_emission=f"{observed_class}|{confidence_bucket}",
        calibration_model_hash=resolved_model.model_hash,
        posterior=posterior,
        projection_algorithm_version=PROJECTION_ALGORITHM_VERSION,
        quantile=resolve_grader_channel_prior(repository).lcb_quantile,
    )

    # Step 7: review + influence checks (§4.4).
    review_flag = unclassifiable
    if grader_confidence is not None and grader_confidence < REVIEW_CONFIDENCE_THRESHOLD:
        review_flag = True
    prior_events = repository.raw_grade_events_for_observation(observation_id)
    coarse_seen = {ev["observed_class"] for ev in prior_events}
    if len(coarse_seen) > 1:
        review_flag = True
    influence_flag = certainty < INFLUENCE_CERTAINTY_FLOOR

    interpretation_id = repository.insert_grade_interpretation(
        values={
            "raw_grade_event_id": raw_event_id,
            "observation_id": observation_id,
            "administration_id": administration_id,
            "calibration_model_id": resolved_model.model_id or _persist_fallback_model(
                repository, resolved_model, schema_id, schema_version, clock=clock
            ),
            "calibration_model_hash": resolved_model.model_hash,
            "projection_algorithm_version": PROJECTION_ALGORITHM_VERSION,
            "channel_posterior_snapshot_id": resolved_model.model_hash,
            "response_posterior_json": _json(posterior),
            "criterion_posteriors_json": None,
            "reference_prior_ids_json": _json(resolved_model.contributing_model_ids),
            "certainty_discount": certainty,
            "shared_certainty_lcb": shared_lcb,
            "credible_interval_json": _json(interval),
            "review_flag": review_flag,
            "influence_flag": influence_flag,
            "quarantine_state": "active",
            "fallback_reason": resolved_model.fallback_reason,
        },
        clock=clock,
    )
    repository.set_active_interpretation(
        observation_id=observation_id, interpretation_id=interpretation_id
    )
    repository.append_measurement_event(
        administration_id=administration_id,
        kind="grade_interpreted",
        algorithm_version=PROJECTION_ALGORITHM_VERSION,
        observation_id=observation_id,
        payload_json=_json(
            {
                "interpretation_id": interpretation_id,
                "calibration_model_hash": resolved_model.model_hash,
                "review_flag": review_flag,
                "fallback_reason": resolved_model.fallback_reason,
            }
        ),
        clock=clock,
    )

    return GradeResolution(
        administration_id=administration_id,
        observation_id=observation_id,
        raw_grade_event_id=raw_event_id,
        interpretation_id=interpretation_id,
        observed_class=observed_class,
        confidence_bucket=confidence_bucket,
        posterior=posterior,
        certainty=certainty,
        credible_interval=interval,
        calibration_model_id=resolved_model.model_id,
        calibration_model_hash=resolved_model.model_hash,
        review_flag=review_flag,
        influence_flag=influence_flag,
        fallback_reason=resolved_model.fallback_reason,
        unclassifiable=unclassifiable,
    )


def response_certainty_lcb(
    vault: LoadedVault,
    repository: Repository,
    *,
    item: PracticeItem,
    grading_source: str,
    rubric_score: int | None,
    max_points: int,
    grader_confidence: float | None,
    has_fatal: bool = False,
    response_text: str | None = None,
    domain: str | None = None,
    grader_model_revision: str | None = None,
    outcome_schema_slug: str = COARSE_RESPONSE_SLUG,
    clock: Clock | None = None,
) -> float:
    """The certainty LCB of this response's calibrated interpretation, computed
    WITHOUT persisting anything (P0.3 §4.4 mastery wiring).

    Mirrors the resolve_grade classification + model-resolution steps so mastery
    consumes the SAME certainty result certification consumes. Used to source the
    grader-confidence factor for new-version (mvp-0.8) mastery writes -- so mastery
    and certification cannot disagree about grader trust. Deterministic (seeded)."""

    schema_id, schema_version = resolve_schema_id(repository, outcome_schema_slug, clock=clock)
    schema_row = repository.fetch_outcome_schema_version_by_id(schema_id, schema_version)
    shape = schema_shape_from_row(schema_row)
    response_empty = not (response_text or "").strip()
    classification = classify_response(
        rubric_score=rubric_score,
        max_points=max_points,
        schema=shape,
        has_fatal=has_fatal,
        response_empty=response_empty,
    )
    observed_class = classification.observed_class
    confidence_bucket = bucket_confidence(grader_confidence)
    _word_count, declared_bucket = length_bucket_for_text(response_text)
    gih = gc.grader_identity_hash(
        provider=grading_source,
        model_revision=grader_model_revision,
        prompt_version=gc.GRADING_PROMPT_VERSION,
        output_schema_version=gc.GRADER_OUTPUT_SCHEMA_VERSION,
    )
    resolved = gc.resolve_calibration_model(
        repository,
        grader_identity_hash=gih,
        outcome_schema_id=schema_id,
        outcome_schema_version=schema_version,
        domain=domain,
        length_bucket=declared_bucket,
        clock=clock,
    )
    posterior = gc.posterior_over_true_class(
        resolved, observed_class=observed_class, confidence_bucket=confidence_bucket
    )
    # H1 (§4.3 final ¶): the SAME shared helper certification persists, so mastery
    # and certification consume an identical certainty LCB.
    return eo.shared_certainty_lcb(
        joint_alpha=resolved.joint_alpha,
        observed_emission=f"{observed_class}|{confidence_bucket}",
        calibration_model_hash=resolved.model_hash,
        posterior=posterior,
        projection_algorithm_version=PROJECTION_ALGORITHM_VERSION,
        quantile=resolve_grader_channel_prior(repository).lcb_quantile,
    )


def response_soft_score(
    vault: LoadedVault,
    repository: Repository,
    *,
    item: PracticeItem,
    grading_source: str,
    rubric_score: int | None,
    max_points: int,
    grader_confidence: float | None,
    has_fatal: bool = False,
    response_text: str | None = None,
    domain: str | None = None,
    grader_model_revision: str | None = None,
    outcome_schema_slug: str = COARSE_RESPONSE_SLUG,
    clock: Clock | None = None,
) -> tuple[float, float]:
    """(E[s(Z)|E], Var[s(Z)|E]) of the calibrated true-score, without persisting.

    The prediction-lane summary of the SAME grade channel certification reads:
    the posterior over the true response class carries both the directional
    information (how well did the learner probably do) and the interpretation
    uncertainty. Consumers feed the mean as the EKF observation and add the
    variance to measurement noise — instead of multiplying the observation
    weight by the conservative certainty LCB, which throws the direction away
    and treats a confident correct answer as a third of an observation.
    """

    import json as _json

    schema_id, schema_version = resolve_schema_id(repository, outcome_schema_slug, clock=clock)
    schema_row = repository.fetch_outcome_schema_version_by_id(schema_id, schema_version)
    shape = schema_shape_from_row(schema_row)
    score_fraction: dict[str, float] = {}
    if schema_row is not None and schema_row.get("score_fraction_json"):
        score_fraction = {
            str(k): float(v) for k, v in _json.loads(schema_row["score_fraction_json"]).items()
        }
    raw_fraction = (
        max(0.0, min(1.0, float(rubric_score) / max(max_points, 1)))
        if rubric_score is not None
        else 0.0
    )
    if not score_fraction:
        return raw_fraction, 0.0
    response_empty = not (response_text or "").strip()
    classification = classify_response(
        rubric_score=rubric_score,
        max_points=max_points,
        schema=shape,
        has_fatal=has_fatal,
        response_empty=response_empty,
    )
    confidence_bucket = bucket_confidence(grader_confidence)
    _word_count, declared_bucket = length_bucket_for_text(response_text)
    gih = gc.grader_identity_hash(
        provider=grading_source,
        model_revision=grader_model_revision,
        prompt_version=gc.GRADING_PROMPT_VERSION,
        output_schema_version=gc.GRADER_OUTPUT_SCHEMA_VERSION,
    )
    resolved = gc.resolve_calibration_model(
        repository,
        grader_identity_hash=gih,
        outcome_schema_id=schema_id,
        outcome_schema_version=schema_version,
        domain=domain,
        length_bucket=declared_bucket,
        clock=clock,
    )
    posterior = gc.posterior_over_true_class(
        resolved,
        observed_class=classification.observed_class,
        confidence_bucket=confidence_bucket,
    )
    mean = sum(float(p) * score_fraction.get(z, 0.0) for z, p in posterior.items())
    second_moment = sum(float(p) * score_fraction.get(z, 0.0) ** 2 for z, p in posterior.items())
    variance = max(0.0, second_moment - mean * mean)
    return mean, variance


def _persist_fallback_model(
    repository: Repository,
    resolved_model: gc.ResolvedModel,
    schema_id: str,
    schema_version: int,
    *,
    clock: Clock | None = None,
) -> str:
    """The uniform fallback has no persisted model row; the interpretation FK still
    needs one. Persist a wide heuristic global prior once and reuse it."""

    existing = repository.find_calibration_model_by_hash(resolved_model.model_hash)
    if existing is not None:
        return existing["id"]
    return repository.insert_calibration_model(
        model={
            "grader_provider": None,
            "grader_model_revision": None,
            "grading_prompt_version": None,
            "grader_output_schema_version": None,
            "grader_identity_hash": None,
            "semver": "0.1.0",
            "parent_model_id": None,
            "content_hash": resolved_model.model_hash,
            "scope_level": "global",
            "outcome_schema_id": schema_id,
            "outcome_schema_version": schema_version,
            "domain": None,
            "length_bucket": None,
            "backoff_chain_json": _json([]),
            "status": "heuristic",
            "count_heuristic_prior": int(gc.PRIOR_CONCENTRATION),
            "prior_concentration": gc.PRIOR_CONCENTRATION,
            "provenance_json": _json({"source": "uniform_fallback"}),
        },
        alphas=resolved_model.joint_alpha,
        clock=clock,
    )


def ensure_administration_identity(
    vault: LoadedVault,
    repository: Repository,
    *,
    item: PracticeItem,
    purpose: str,
    attempt_id: str,
    feedback_condition: str | None = None,
    clock: Clock | None = None,
) -> tuple[str, str, str]:
    """Resolve (or reuse) the surface + administration and append the observation
    for one response (§4.1 steps 1-2). Returns
    ``(surface_id, administration_id, observation_id)``."""

    resolved = resolve_legacy_item(vault, repository, item, purpose=purpose, clock=clock)
    surface_id = resolved.surface_id
    admin = open_administration(
        repository,
        resolved=resolved,
        feedback_condition=feedback_condition,
        clock=clock,
    )
    administration_id = admin.administration_id
    observation_id = append_observation(
        repository,
        administration_id=administration_id,
        surface_id=surface_id,
        purpose=purpose,
        feedback_condition=feedback_condition,
        attempt_id=attempt_id,
        response_ref=attempt_id,
        clock=clock,
    )
    return surface_id, administration_id, observation_id


def record_grade_dual_write(
    vault: LoadedVault,
    repository: Repository,
    **kwargs: Any,
) -> GradeResolution | None:
    """Fail-safe dual-write wrapper (§7.3). A resolution failure is swallowed so
    the legacy summary path is never broken; P0.3 replay recovers the gap.

    Identity is minted FIRST (steps 1-2) when the caller did not supply it, so a
    failure anywhere in the later pipeline always has an administration to anchor
    its degradation telemetry to -- the legacy practice path never passes ids, and
    without this the whole failure slice was an invisible no-op (audit B2)."""

    try:
        if (
            kwargs.get("administration_id") is None
            or kwargs.get("observation_id") is None
            or kwargs.get("surface_id") is None
        ):
            surface_id, administration_id, observation_id = ensure_administration_identity(
                vault,
                repository,
                item=kwargs["item"],
                purpose=kwargs["purpose"],
                attempt_id=kwargs["attempt_id"],
                feedback_condition=kwargs.get("feedback_condition"),
                clock=kwargs.get("clock"),
            )
            kwargs.update(
                surface_id=surface_id,
                administration_id=administration_id,
                observation_id=observation_id,
            )
    except Exception as exc:  # noqa: BLE001 - fail-safe by design (§7.3)
        _record_dual_write_degradation(repository, kwargs, exc)
        return None
    try:
        return resolve_grade(vault, repository, **kwargs)
    except Exception as exc:  # noqa: BLE001 - fail-safe by design (§7.3)
        _record_dual_write_degradation(repository, kwargs, exc)
        return None


def _record_dual_write_degradation(
    repository: Repository, kwargs: Mapping[str, Any], exc: Exception
) -> None:
    admin_id = kwargs.get("administration_id")
    if admin_id is None:
        # No administration exists (the identity mint itself failed) -- nothing to
        # anchor a measurement event to, but the degradation must not be silent.
        _LOGGER.warning(
            "grade dual-write degraded before an administration existed "
            "(attempt %s): %s",
            kwargs.get("attempt_id"),
            exc,
        )
        return
    try:
        repository.append_measurement_event(
            administration_id=admin_id,
            kind="correction_appended",
            algorithm_version=PROJECTION_ALGORITHM_VERSION,
            payload_json=_json({"dual_write_degraded": True, "error": str(exc)}),
        )
    except Exception:  # noqa: BLE001 - telemetry must never raise into the caller.
        _LOGGER.warning(
            "grade dual-write degradation telemetry itself failed for "
            "administration %s: %s",
            admin_id,
            exc,
        )


# ---------------------------------------------------------------------------
# Review, quarantine, adjudication (§4.4)
# ---------------------------------------------------------------------------

def quarantine_observation(
    repository: Repository,
    *,
    observation_id: str,
    surface_id: str | None,
    reason: str,
    clock: Clock | None = None,
) -> str | None:
    """Immediately quarantine the observation's active interpretation (§4.4).

    Append-only: a NEW interpretation row (copying the head) with
    ``quarantine_state='quarantined'`` is appended and made the head; the prior
    row is never mutated. Zero current authority until adjudicated; raw history
    stays visible. Returns the new head interpretation id."""

    head = repository.active_interpretation_for_observation(observation_id)
    if head is None:
        return None
    new_id = repository.insert_grade_interpretation(
        values={
            "raw_grade_event_id": head["raw_grade_event_id"],
            "observation_id": observation_id,
            "administration_id": head["administration_id"],
            "calibration_model_id": head["calibration_model_id"],
            "calibration_model_hash": head["calibration_model_hash"],
            "projection_algorithm_version": head["projection_algorithm_version"],
            "channel_posterior_snapshot_id": head.get("channel_posterior_snapshot_id"),
            "response_posterior_json": head["response_posterior_json"],
            "criterion_posteriors_json": head.get("criterion_posteriors_json"),
            "reference_prior_ids_json": head.get("reference_prior_ids_json"),
            "certainty_discount": head["certainty_discount"],
            "shared_certainty_lcb": head.get("shared_certainty_lcb"),
            "credible_interval_json": head.get("credible_interval_json"),
            "review_flag": 1,
            "influence_flag": head.get("influence_flag", 0),
            "quarantine_state": "quarantined",
            "fallback_reason": head.get("fallback_reason"),
        },
        clock=clock,
    )
    repository.set_active_interpretation(observation_id=observation_id, interpretation_id=new_id)
    if surface_id is not None:
        repository.append_surface_lifecycle_event(
            surface_id=surface_id,
            kind="quarantine",
            administration_id=head["administration_id"],
            reason=reason,
            clock=clock,
        )
    repository.append_measurement_event(
        administration_id=head["administration_id"],
        kind="grade_quarantined",
        algorithm_version=PROJECTION_ALGORITHM_VERSION,
        observation_id=observation_id,
        payload_json=_json({"reason": reason, "interpretation_id": new_id}),
        clock=clock,
    )
    return new_id


def append_adjudication(
    repository: Repository,
    *,
    observation_id: str,
    administration_id: str,
    reviewed_raw_event_ids: Sequence[str],
    adjudicator_source: str,
    resolved_class: str | None = None,
    resolved_distribution: Mapping[str, float] | None = None,
    rationale: str | None = None,
    bounded_trust_weight: float | None = None,
    superseded_adjudication_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, str]:
    """Append an adjudication + a NEW interpretation and repoint the head (§3.3/§4.4).

    Adjudicated anchors carry authority: they narrow the credible interval (a
    deterministic/human anchor to a point). ``learner_clarification`` carries a
    bounded-trust weight < 1. Never overwrites prior rows."""

    head = repository.active_interpretation_for_observation(observation_id)
    reviewed = list(reviewed_raw_event_ids)
    raw_event_id = reviewed[-1] if reviewed else (head["raw_grade_event_id"] if head else None)
    if raw_event_id is None:
        raise ValueError("adjudication requires at least one reviewed raw grade event")

    trust = bounded_trust_weight
    if trust is None:
        trust = BOUNDED_TRUST_WEIGHT_DEFAULT if adjudicator_source == "learner_clarification" else 1.0
    # Clamp trust to [0, 1] (audit F4): a caller-supplied weight can never grant
    # more-than-full authority or negative anti-trust.
    trust = max(0.0, min(1.0, float(trust)))

    import json

    base = json.loads(head["response_posterior_json"]) if head is not None else {}
    base = {z: max(0.0, float(p)) for z, p in base.items()}

    if resolved_distribution is not None:
        # M4: the resolved_distribution branch must apply the SAME bounded-trust
        # blend + renormalization as the resolved_class branch -- a
        # learner_clarification distribution cannot be adopted verbatim with full
        # authority. Normalize the provided distribution, then blend it against the
        # prior head by the trust weight.
        target = {z: max(0.0, float(p)) for z, p in resolved_distribution.items()}
        t_total = sum(target.values()) or 1.0
        target = {z: p / t_total for z, p in target.items()}
        classes = set(base) | set(target)
        posterior = {
            z: trust * target.get(z, 0.0) + (1 - trust) * base.get(z, 0.0)
            for z in classes
        }
    elif resolved_class is not None:
        # Blend a point mass at the resolved class with the prior head posterior by
        # the trust weight (full trust -> a point mass).
        classes = set(base) | {resolved_class}
        posterior = {
            z: trust * (1.0 if z == resolved_class else 0.0) + (1 - trust) * base.get(z, 0.0)
            for z in classes
        }
    else:
        raise ValueError("adjudication requires resolved_class or resolved_distribution")

    total = sum(posterior.values()) or 1.0
    posterior = {z: v / total for z, v in posterior.items()}

    interval_width = (1.0 - trust) * 0.5  # decision parameter: heuristic (bounded trust)
    interval = {
        "leading_class": max(posterior, key=posterior.get),
        "point": max(posterior.values()),
        "low": max(0.0, max(posterior.values()) - interval_width / 2),
        "high": min(1.0, max(posterior.values()) + interval_width / 2),
        "width": interval_width,
    }
    # M4 (audit F3/A3-5): the old blend was the vacuous ``trust*c + (1-trust)*c``.
    # Blend the adjudicated posterior's certainty against the PRIOR head's certainty
    # by the trust weight, so a bounded-trust clarification reflects its incomplete
    # authority. A full-trust anchor is a deterministic authority -> certainty 1.
    base_certainty = gc.certainty(base) if base else 0.0
    certainty_value = trust * gc.certainty(posterior) + (1 - trust) * base_certainty
    if trust >= 1.0:
        certainty_value = 1.0

    interpretation_id = repository.insert_grade_interpretation(
        values={
            "raw_grade_event_id": raw_event_id,
            "observation_id": observation_id,
            "administration_id": administration_id,
            "calibration_model_id": head["calibration_model_id"] if head else "",
            "calibration_model_hash": head["calibration_model_hash"] if head else "",
            "projection_algorithm_version": PROJECTION_ALGORITHM_VERSION,
            "channel_posterior_snapshot_id": None,
            "response_posterior_json": _json(posterior),
            "criterion_posteriors_json": None,
            "reference_prior_ids_json": None,
            "certainty_discount": certainty_value,
            # An adjudicated anchor's certainty is deterministic authority, not a
            # calibration-ensemble draw: persist it as the shared LCB so
            # EffectiveObservation never re-draws the grader Dirichlet (H1).
            "shared_certainty_lcb": certainty_value,
            "credible_interval_json": _json(interval),
            "review_flag": 0,
            "influence_flag": 0,
            "quarantine_state": "active",
            "fallback_reason": None,
        },
        clock=clock,
    )
    adjudication_id = repository.insert_grade_adjudication(
        values={
            "observation_id": observation_id,
            "administration_id": administration_id,
            "reviewed_raw_event_ids_json": _json(reviewed),
            "adjudicator_source": adjudicator_source,
            "resolved_class": resolved_class,
            "resolved_distribution_json": _json(dict(resolved_distribution)) if resolved_distribution else None,
            "rationale": rationale,
            "provenance_json": _json({"bounded_trust_weight": trust}),
            "bounded_trust_weight": trust,
            "resulting_interpretation_id": interpretation_id,
            "superseded_adjudication_id": superseded_adjudication_id,
        },
        clock=clock,
    )
    repository.set_active_interpretation(observation_id=observation_id, interpretation_id=interpretation_id)
    repository.append_measurement_event(
        administration_id=administration_id,
        kind="grade_adjudicated",
        algorithm_version=PROJECTION_ALGORITHM_VERSION,
        observation_id=observation_id,
        payload_json=_json({"adjudication_id": adjudication_id, "source": adjudicator_source}),
        clock=clock,
    )
    repository.append_measurement_event(
        administration_id=administration_id,
        kind="interpretation_activated",
        algorithm_version=PROJECTION_ALGORITHM_VERSION,
        observation_id=observation_id,
        payload_json=_json({"interpretation_id": interpretation_id}),
        clock=clock,
    )
    return {"adjudication_id": adjudication_id, "interpretation_id": interpretation_id}

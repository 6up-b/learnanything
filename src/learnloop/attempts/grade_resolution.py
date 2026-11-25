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
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.held_grades import attempt_grade_held
from learnloop.substrate.activities import (
    canonical_json,
    append_observation,
    open_administration,
    resolve_legacy_item,
)
from learnloop.attempts import effective_observation as eo
from learnloop.attempts import grader_calibration as gc
from learnloop.attempts.grade_classifier import (
    CRITERION_CLASSIFIER_VERSION,
    RESPONSE_CLASSIFIER_VERSION,
    bucket_confidence,
    classify_criteria,
    classify_response,
    length_bucket_for_text,
    schema_shape_from_row,
)
from learnloop.params.fitted_params import resolve_grader_channel_prior
from learnloop.attempts.outcome_schemas import COARSE_RESPONSE_SLUG, resolve_schema_id
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
    grading_prompt_version: str | None = None,
    grader_output_schema_version: str | None = None,
    clock: Clock | None = None,
) -> GradeResolution:
    """The §4.1 pipeline for one graded response. May raise; callers that dual-write
    from a legacy path use :func:`record_grade_dual_write` (guarded).

    ``grading_prompt_version`` / ``grader_output_schema_version`` are the
    calibration identity (Slice 1 §4.3). They default to the joint grader's, so
    every existing caller stamps exactly what it did; the blind grader passes
    its own pair so calibration never pools joint and blind graders."""

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

    reading = read_grade(
        repository,
        purpose=purpose,
        grading_source=grading_source,
        attempt_id=attempt_id,
        response_text=response_text,
        rubric_score=rubric_score,
        max_points=max_points,
        grader_confidence=grader_confidence,
        has_fatal=has_fatal,
        signature_matched=signature_matched,
        criterion_points=criterion_points,
        criterion_max=criterion_max,
        raw_output=raw_output,
        criterion_evidence=criterion_evidence,
        agent_run_id=agent_run_id,
        role=role,
        domain=domain,
        declared_length_bucket=declared_length_bucket,
        outcome_schema_slug=outcome_schema_slug,
        observed_class_override=observed_class_override,
        grader_model_revision=grader_model_revision,
        grading_prompt_version=grading_prompt_version,
        grader_output_schema_version=grader_output_schema_version,
        clock=clock,
    )
    # Step 3: append the raw grade event (no posterior touched).
    raw_event_id = _append_raw_grade_event(
        repository, reading, administration_id=administration_id, observation_id=observation_id, clock=clock
    )
    # Step 7: review + influence checks (§4.4): two graders of this response
    # that disagree on its class also send it to review.
    prior_events = repository.raw_grade_events_for_observation(observation_id)
    coarse_seen = {ev["observed_class"] for ev in prior_events}
    review_flag = reading.review_flag or len(coarse_seen) > 1
    interpretation_id = _append_interpretation(
        repository,
        reading,
        raw_event_id=raw_event_id,
        observation_id=observation_id,
        administration_id=administration_id,
        review_flag=review_flag,
        clock=clock,
    )
    return GradeResolution(
        administration_id=administration_id,
        observation_id=observation_id,
        raw_grade_event_id=raw_event_id,
        interpretation_id=interpretation_id,
        observed_class=reading.observed_class,
        confidence_bucket=reading.confidence_bucket,
        posterior=reading.posterior,
        certainty=reading.certainty,
        credible_interval=reading.interval,
        calibration_model_id=reading.resolved_model.model_id,
        calibration_model_hash=reading.resolved_model.model_hash,
        review_flag=review_flag,
        influence_flag=reading.influence_flag,
        fallback_reason=reading.resolved_model.fallback_reason,
        unclassifiable=reading.unclassifiable,
    )


@dataclass(frozen=True)
class GradeReading:
    """What one graded response reads as before anything is written (§4.1 steps 4-7).

    ``raw_values`` are the raw grade event's columns but its administration and
    observation; ``review_flag`` is the response's own review signal
    (unclassifiable, or a grader confidence under the threshold), before any
    disagreement between graders of one observation is added."""

    raw_values: dict[str, Any]
    observed_class: str
    unclassifiable: bool
    confidence_bucket: str
    schema_id: str
    schema_version: int
    resolved_model: gc.ResolvedModel
    posterior: dict[str, float]
    interval: dict[str, float]
    certainty: float
    shared_lcb: float
    review_flag: bool
    influence_flag: bool


def read_grade(
    repository: Repository,
    *,
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
    grading_prompt_version: str | None = None,
    grader_output_schema_version: str | None = None,
    clock: Clock | None = None,
) -> GradeReading:
    """Classify one graded response and interpret it under the current
    calibration, writing nothing but what resolving the outcome schema writes."""

    prompt_identity = grading_prompt_version or gc.GRADING_PROMPT_VERSION
    schema_identity = grader_output_schema_version or gc.GRADER_OUTPUT_SCHEMA_VERSION

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
        prompt_version=prompt_identity,
        output_schema_version=schema_identity,
    )
    context_features = {
        "grader_identity_hash": gih,
        "outcome_schema_id": schema_id,
        "outcome_schema_version": schema_version,
        "domain": domain,
        "length_bucket": declared_bucket,
        "purpose": purpose,
    }

    # Step 3's row: the raw grade event's columns (no posterior touched).
    raw_output_payload = dict(raw_output) if raw_output is not None else {
        "rubric_score": rubric_score,
        "max_points": max_points,
        "grader_confidence": grader_confidence,
        "grading_source": grading_source,
    }
    raw_values = {
        "attempt_id": attempt_id,
        "response_ref": attempt_id,
        "role": role,
        "grader_provider": grading_source,
        "grader_model_revision": grader_model_revision,
        "grading_prompt_version": prompt_identity,
        "grader_output_schema_version": schema_identity,
        "grader_identity_hash": gih,
        "agent_run_id": agent_run_id,
        "raw_output_json": canonical_json(raw_output_payload),
        "criterion_evidence_json": canonical_json(criterion_evidence) if criterion_evidence is not None else None,
        "observed_class": observed_class,
        "model_confidence": grader_confidence,
        "confidence_bucket": confidence_bucket,
        "criterion_observed_classes_json": canonical_json(criterion_classes) if criterion_classes else None,
        "response_classifier_version": RESPONSE_CLASSIFIER_VERSION,
        "criterion_classifier_version": CRITERION_CLASSIFIER_VERSION if criterion_classes else None,
        "context_features_json": canonical_json(context_features),
        "exact_word_count": word_count,
        "declared_length_bucket": declared_bucket,
    }

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

    # Step 7's own part (§4.4): the response's review signal and influence.
    review_flag = unclassifiable
    if grader_confidence is not None and grader_confidence < REVIEW_CONFIDENCE_THRESHOLD:
        review_flag = True
    return GradeReading(
        raw_values=raw_values,
        observed_class=observed_class,
        unclassifiable=unclassifiable,
        confidence_bucket=confidence_bucket,
        schema_id=schema_id,
        schema_version=schema_version,
        resolved_model=resolved_model,
        posterior=posterior,
        interval=interval,
        certainty=certainty,
        shared_lcb=shared_lcb,
        review_flag=review_flag,
        influence_flag=certainty < INFLUENCE_CERTAINTY_FLOOR,
    )


def _append_raw_grade_event(
    repository: Repository,
    reading: GradeReading,
    *,
    administration_id: str,
    observation_id: str,
    clock: Clock | None,
) -> str:
    """Step 3: the raw grade event and its two measurement events."""

    raw_event_id = repository.insert_raw_grade_event(
        values={"administration_id": administration_id, "observation_id": observation_id, **reading.raw_values},
        clock=clock,
    )
    repository.append_measurement_event(
        administration_id=administration_id,
        kind="raw_grade_appended",
        algorithm_version=PROJECTION_ALGORITHM_VERSION,
        observation_id=observation_id,
        payload_json=canonical_json({"raw_grade_event_id": raw_event_id, "role": reading.raw_values["role"]}),
        clock=clock,
    )
    repository.append_measurement_event(
        administration_id=administration_id,
        kind="grade_classified",
        algorithm_version=RESPONSE_CLASSIFIER_VERSION,
        observation_id=observation_id,
        payload_json=canonical_json(
            {"observed_class": reading.observed_class, "unclassifiable": reading.unclassifiable}
        ),
        clock=clock,
    )
    return raw_event_id


def _interpretation_values(
    repository: Repository,
    reading: GradeReading,
    *,
    raw_event_id: str,
    observation_id: str,
    administration_id: str,
    review_flag: bool,
    clock: Clock | None,
) -> dict[str, Any]:
    resolved_model = reading.resolved_model
    return {
        "raw_grade_event_id": raw_event_id,
        "observation_id": observation_id,
        "administration_id": administration_id,
        "calibration_model_id": resolved_model.model_id or _persist_fallback_model(
            repository, resolved_model, reading.schema_id, reading.schema_version, clock=clock
        ),
        "calibration_model_hash": resolved_model.model_hash,
        "projection_algorithm_version": PROJECTION_ALGORITHM_VERSION,
        "channel_posterior_snapshot_id": resolved_model.model_hash,
        "response_posterior_json": canonical_json(reading.posterior),
        "criterion_posteriors_json": None,
        "reference_prior_ids_json": canonical_json(resolved_model.contributing_model_ids),
        "certainty_discount": reading.certainty,
        "shared_certainty_lcb": reading.shared_lcb,
        "credible_interval_json": canonical_json(reading.interval),
        "review_flag": review_flag,
        "influence_flag": reading.influence_flag,
        "quarantine_state": "active",
        "fallback_reason": resolved_model.fallback_reason,
    }


def _append_interpretation(
    repository: Repository,
    reading: GradeReading,
    *,
    raw_event_id: str,
    observation_id: str,
    administration_id: str,
    review_flag: bool,
    clock: Clock | None,
    values: Mapping[str, Any] | None = None,
) -> str:
    """Steps 8-9: the calibrated interpretation, made the observation's head."""

    if values is None:
        values = _interpretation_values(
            repository, reading, raw_event_id=raw_event_id, observation_id=observation_id,
            administration_id=administration_id, review_flag=review_flag, clock=clock,
        )
    interpretation_id = repository.insert_grade_interpretation(values=values, clock=clock)
    repository.set_active_interpretation(
        observation_id=observation_id, interpretation_id=interpretation_id
    )
    repository.append_measurement_event(
        administration_id=administration_id,
        kind="grade_interpreted",
        algorithm_version=PROJECTION_ALGORITHM_VERSION,
        observation_id=observation_id,
        payload_json=canonical_json(
            {
                "interpretation_id": interpretation_id,
                "calibration_model_hash": reading.resolved_model.model_hash,
                "review_flag": review_flag,
                "fallback_reason": reading.resolved_model.fallback_reason,
            }
        ),
        clock=clock,
    )
    return interpretation_id


#: The exam channel's purpose: an exam answer's grade is read on an assessment administration
#: (``goals.exam_session``'s dual write, and from mvp-0.61 a regraded exam answer's replay).
EXAM_GRADE_PURPOSE = "assessment"


def grade_channel_fixes_on(config: Any) -> bool:
    """The grade channel fixes (mvp-0.60): replay keeps each practice answer's
    observation and appends only what changed. Gated by the vault's tag alone
    (no kill switch); below it a rebuild re-mints the chain as mvp-0.59 does.
    Their only reader, so the tag lives in one place
    (``algorithm_versions.GRADE_CHANNEL_FIX_VERSIONS``)."""

    from learnloop.algorithm_versions import GRADE_CHANNEL_FIX_VERSIONS

    algorithms = getattr(config, "algorithms", None)
    return getattr(algorithms, "algorithm_version", None) in GRADE_CHANNEL_FIX_VERSIONS


#: What a raw grade event says about the grade. ``agent_run_id`` is left out: it
#: names the live model run, and replay re-applies a grade without one, so a
#: live AI grade would otherwise read as regraded at its first rebuild.
_RAW_GRADE_COLUMNS = (
    "role", "grader_provider", "grader_model_revision", "grading_prompt_version",
    "grader_output_schema_version", "grader_identity_hash", "raw_output_json", "criterion_evidence_json",
    "observed_class", "model_confidence", "confidence_bucket", "criterion_observed_classes_json",
    "response_classifier_version", "criterion_classifier_version", "context_features_json",
    "exact_word_count", "declared_length_bucket",
)
#: What an interpretation says (its ids and stamp aside).
_INTERPRETATION_COLUMNS = (
    "calibration_model_id", "calibration_model_hash", "projection_algorithm_version",
    "channel_posterior_snapshot_id", "response_posterior_json", "criterion_posteriors_json",
    "reference_prior_ids_json", "certainty_discount", "shared_certainty_lcb", "credible_interval_json",
    "review_flag", "influence_flag", "quarantine_state", "fallback_reason",
)
_FLAG_COLUMNS = frozenset({"review_flag", "influence_flag"})


def _same_columns(stored: Mapping[str, Any], values: Mapping[str, Any], columns: Sequence[str]) -> bool:
    for column in columns:
        left, right = stored.get(column), values.get(column)
        if column in _FLAG_COLUMNS:
            left, right = bool(left), bool(right)
        if left != right:
            return False
    return True


def record_replayed_grade(
    vault: LoadedVault,
    repository: Repository,
    *,
    observation: Mapping[str, Any],
    **kwargs: Any,
) -> None:
    """Replay's grade channel for an answer that already has an observation
    (the grade channel fixes; fail-safe like :func:`record_grade_dual_write`).

    A rebuild re-applies every answer; minting a fresh observation each time
    grew history by one chain per answer per rebuild and moved the projection
    off the copy an owner had adjudicated or flagged. Here the observation the
    ledger reads (the attempt's newest) is kept, and only what changed is
    appended to it:

    - a raw grade event and its interpretation when the grade differs from the
      one the head interprets (a regrade), whatever the head is;
    - otherwise an interpretation alone when it differs from the head (another
      calibration model or projection version), unless a review wrote the head
      (an adjudication, a review flag or a quarantine), which a re-reading of
      the same grade must not undo;
    - nothing else, and measurement events only beside an append.

    An adjudication that flipped the answer's direction also revised its grade,
    so its own revision is not taken for a regrade of the grade it settled.
    The review flag is the response's own, as on a fresh observation: the
    observation's earlier raw events are grades this one replaced, not a second
    grader disagreeing with it."""

    administration_id = str(observation["administration_id"])
    try:
        _replay_grade(vault, repository, observation=observation, **kwargs)
    except Exception as exc:  # noqa: BLE001 - fail-safe by design (§7.3)
        _record_dual_write_degradation(repository, {**kwargs, "administration_id": administration_id}, exc)


def _replay_grade(
    vault: LoadedVault,
    repository: Repository,
    *,
    observation: Mapping[str, Any],
    item: PracticeItem,
    clock: Clock | None = None,
    **kwargs: Any,
) -> None:
    del vault, item  # the observation names the administration and surface already
    for key in ("administration_id", "observation_id", "surface_id", "feedback_condition"):
        kwargs.pop(key, None)
    reading = read_grade(repository, clock=clock, **kwargs)
    observation_id = str(observation["id"])
    administration_id = str(observation["administration_id"])
    head = repository.active_interpretation_for_observation(observation_id)
    if head is not None:
        basis = repository.raw_grade_event(str(head["raw_grade_event_id"]))
    else:
        events = repository.raw_grade_events_for_observation(observation_id)
        basis = events[-1] if events else None
    review = repository.grade_head_review(observation_id, str(head["id"])) if head is not None else None
    regraded = basis is None or not _same_columns(basis, reading.raw_values, _RAW_GRADE_COLUMNS)
    if regraded and review is not None and review.get("adjudication_id") is not None:
        regraded = not _adjudication_wrote_the_grade(
            repository, str(kwargs["attempt_id"]), str(review["adjudication_id"])
        )
    if regraded:
        raw_event_id = _append_raw_grade_event(
            repository, reading, administration_id=administration_id, observation_id=observation_id, clock=clock
        )
        _append_interpretation(
            repository, reading, raw_event_id=raw_event_id, observation_id=observation_id,
            administration_id=administration_id, review_flag=reading.review_flag, clock=clock,
        )
        return
    if review is not None:
        return
    values = _interpretation_values(
        repository, reading, raw_event_id=str(basis["id"]), observation_id=observation_id,
        administration_id=administration_id, review_flag=reading.review_flag, clock=clock,
    )
    if head is not None and _same_columns(head, values, _INTERPRETATION_COLUMNS):
        return
    _append_interpretation(
        repository, reading, raw_event_id=str(basis["id"]), observation_id=observation_id,
        administration_id=administration_id, review_flag=reading.review_flag, clock=clock, values=values,
    )


def _adjudication_wrote_the_grade(repository: Repository, attempt_id: str, adjudication_id: str) -> bool:
    """Whether the attempt's current grading epoch is the revision this
    adjudication wrote (``append_adjudication_evidence_revision``)."""

    from learnloop.grading_epochs import current_epoch

    epoch = current_epoch(repository.fetch_grading_evidence(attempt_id))
    marker = f"adjudicated:{adjudication_id}"
    return epoch is not None and any(getattr(row, "evidence", None) == marker for row in epoch.rows)


def _another_adjudication_wrote_the_grade(repository: Repository, attempt_id: str | None, adjudication_id: str) -> bool:
    """Whether the attempt's current grade is an earlier adjudication's revision.

    Such a grade has no raw grade event of its own, so replay keeps a later
    ruling as the head only when that ruling wrote the grade it reviewed
    (:func:`_adjudication_wrote_the_grade`). A confirmation that wrote nothing
    would read as a regrade at the next replay and lose the head to an
    automatic interpretation."""

    if attempt_id is None:
        return False
    from learnloop.grading_epochs import current_epoch

    epoch = current_epoch(repository.fetch_grading_evidence(attempt_id))
    own = f"adjudicated:{adjudication_id}"
    return epoch is not None and any(
        str(getattr(row, "evidence", None) or "").startswith("adjudicated:") and row.evidence != own
        for row in epoch.rows
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
    grading_prompt_version: str | None = None,
    grader_output_schema_version: str | None = None,
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
        prompt_version=grading_prompt_version or gc.GRADING_PROMPT_VERSION,
        output_schema_version=grader_output_schema_version or gc.GRADER_OUTPUT_SCHEMA_VERSION,
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
    grading_prompt_version: str | None = None,
    grader_output_schema_version: str | None = None,
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

    import json as canonical_json

    schema_id, schema_version = resolve_schema_id(repository, outcome_schema_slug, clock=clock)
    schema_row = repository.fetch_outcome_schema_version_by_id(schema_id, schema_version)
    shape = schema_shape_from_row(schema_row)
    score_fraction: dict[str, float] = {}
    if schema_row is not None and schema_row.get("score_fraction_json"):
        score_fraction = {
            str(k): float(v) for k, v in canonical_json.loads(schema_row["score_fraction_json"]).items()
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
        prompt_version=grading_prompt_version or gc.GRADING_PROMPT_VERSION,
        output_schema_version=grader_output_schema_version or gc.GRADER_OUTPUT_SCHEMA_VERSION,
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
            "backoff_chain_json": canonical_json([]),
            "status": "heuristic",
            "count_heuristic_prior": int(gc.PRIOR_CONCENTRATION),
            "prior_concentration": gc.PRIOR_CONCENTRATION,
            "provenance_json": canonical_json({"source": "uniform_fallback"}),
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
            payload_json=canonical_json({"dual_write_degraded": True, "error": str(exc)}),
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
        payload_json=canonical_json({"reason": reason, "interpretation_id": new_id}),
        clock=clock,
    )
    return new_id


def flag_observation_for_review(
    repository: Repository,
    *,
    observation_id: str,
    reason: str,
    detail: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> str | None:
    """Queue the observation's active grade for review (§4.4), keeping its authority.

    The intake for a grade someone asked to have looked at (UX Phase 4, Codex
    review F3: a learner's "I think I was right" the regrade did not uphold).
    Append-only like :func:`quarantine_observation`: a NEW interpretation row
    copying the head with ``review_flag=1`` is appended and made the head; the
    prior row is never mutated. Unlike a quarantine it changes nothing the
    head says (the same posterior, certainty and state), so no projection,
    grade or replay moves: the grade simply appears in
    ``Repository.pending_grade_reviews`` (``learnloop grading reviews``) until
    an adjudication (:func:`append_adjudication`) appends the next head.
    Returns the flagged head's id (the current one when it is already
    flagged), or None when the observation has no head.
    """

    head = repository.active_interpretation_for_observation(observation_id)
    if head is None:
        return None
    if int(head.get("review_flag") or 0) == 1 or head.get("quarantine_state") == "quarantined":
        return str(head["id"])
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
            "quarantine_state": head["quarantine_state"],
            "fallback_reason": head.get("fallback_reason"),
        },
        clock=clock,
    )
    repository.set_active_interpretation(observation_id=observation_id, interpretation_id=new_id)
    repository.append_measurement_event(
        administration_id=head["administration_id"],
        kind="interpretation_activated",
        algorithm_version=PROJECTION_ALGORITHM_VERSION,
        observation_id=observation_id,
        payload_json=canonical_json(
            {
                "interpretation_id": new_id,
                "review_requested": reason,
                "supersedes_interpretation_id": head["id"],
                **dict(detail or {}),
            }
        ),
        clock=clock,
    )
    return new_id


def _leading_class(posterior: Mapping[str, float]) -> str | None:
    """The unique argmax of a class posterior; ``None`` on empty or tied.

    A tie is deliberately not broken: dict/set iteration order would decide the
    winner nondeterministically, and ruling A only moves the directional ledger
    on an unambiguous flip."""

    if not posterior:
        return None
    best = max(posterior.values())
    leaders = [z for z, p in posterior.items() if p == best]
    return leaders[0] if len(leaders) == 1 else None


# Ruling A (2026-07-27): grader_tier for adjudication-sourced grading_evidence
# revisions. Tiers 1 (self) and 3 (AI) are the existing occupants of the 0-4
# CHECK range; 4 is the human/deterministic-authority slot, so an adjudicated
# revision outranks every machine grade in the tier vocabulary without a new
# provenance scheme.
ADJUDICATION_GRADER_TIER = 4


def append_adjudication_evidence_revision(
    repository: Repository,
    *,
    attempt_id: str,
    resolved_fraction: float,
    adjudication_id: str,
    adjudicator_source: str,
    rationale: str | None,
    vault: "LoadedVault | None" = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Ruling A (2026-07-27): write the adjudicated DIRECTION into the ledger.

    ``grading_evidence`` (non-superseded revisions) is the single directional
    authority for criterion outcomes; the interpretation channel carries
    confidence/mass only. An adjudication that flips the response class must
    therefore land as a superseding evidence revision through the same door the
    regrade and A8-clarification paths use — otherwise the certainty channel
    says "we are now sure" while the ledger still says "full credit", and
    banked credit RISES on an adjudication that lowered the grade.

    Response-level semantics, matching ``_adjudicated_score_fraction``'s
    existing contract: the adjudication is observation-scoped, so one resolved
    fraction applies to every criterion of the attempt. Returns a typed status
    dict; every skip arm is named rather than silent.

    Every read it decides on (the current epoch, its contract, the next
    grading revision) and the publication run in ONE ``BEGIN IMMEDIATE``
    transaction (review F2): another regrade or adjudication of the attempt
    commits wholly before it or after it, so two epochs never share a
    revision and the revision cites the contract of the grade it revises."""

    with repository.atomic():
        return _append_adjudication_evidence_revision(
            repository,
            attempt_id=attempt_id,
            resolved_fraction=resolved_fraction,
            adjudication_id=adjudication_id,
            adjudicator_source=adjudicator_source,
            rationale=rationale,
            vault=vault,
            clock=clock,
        )


def _append_adjudication_evidence_revision(
    repository: Repository,
    *,
    attempt_id: str,
    resolved_fraction: float,
    adjudication_id: str,
    adjudicator_source: str,
    rationale: str | None,
    vault: "LoadedVault | None",
    clock: Clock | None,
) -> dict[str, Any]:
    """:func:`append_adjudication_evidence_revision` inside its transaction."""

    from learnloop.ids import new_ulid
    from learnloop.clock import utc_now_iso

    live_rows = repository.fetch_grading_evidence(attempt_id)
    if not live_rows:
        return {"status": "skipped_no_evidence_rows", "evidence_ids": []}

    # Regrade contracts (mvp-0.26): the adjudication revises the attempt's
    # CURRENT grading epoch, under the contract that epoch cites (else a
    # snapshot of the item whose rubric scales it, cited on its rows), as the
    # attempt's next grading revision; its correctness is the score over that
    # contract's maximum, exactly what replay computes. Without the vault it
    # revises every live row under the contract they cite, as before
    # contracts: nothing names the item to snapshot.
    regrade_contracts = vault is not None
    snapshot_of: tuple[Any, Any] | None = None
    if regrade_contracts:
        from learnloop.grading_epochs import current_epoch

        epoch = current_epoch(live_rows)
        live_rows = list(epoch.rows) if epoch is not None else []

    # Criterion max points: the immutable assessment contract first (repository
    # -only, present on every mvp-0.8 grading), the live vault rubric as the
    # legacy fallback. All-or-nothing: a revision that rescaled only some
    # criteria would leave the attempt's direction incoherent.
    points_by_criterion: dict[str, float] = {}
    version_ids = {
        row.assessment_contract_version_id
        for row in live_rows
        if row.assessment_contract_version_id
    }
    if regrade_contracts:
        from learnloop.grading_epochs import epoch_contract_version_id

        cited = epoch_contract_version_id(live_rows)
        version_ids = {cited} if cited is not None else set()
    if len(version_ids) == 1:
        from learnloop.learner.assessment_contracts import P0_ALGORITHM_VERSION

        stored = repository.effective_assessment_contract_version(
            next(iter(version_ids)), projection_version=P0_ALGORITHM_VERSION
        )
        contract = stored.get("contract") if stored is not None else None
        for criterion in (contract or {}).get("criteria", []) or []:
            cid = str(criterion.get("id"))
            if cid:
                # Contract criteria carry ``max_points`` (see
                # canonical_projection._contract_criteria) — mirror it exactly.
                points_by_criterion[cid] = float(criterion.get("max_points") or 0.0)
    if not points_by_criterion and vault is not None:
        attempt = repository.fetch_practice_attempt(attempt_id)
        item = (
            vault.practice_items.get(str(attempt.get("practice_item_id")))
            if attempt is not None
            else None
        )
        rubric = vault.rubric_for_item(item) if item is not None else None
        if rubric is not None:
            points_by_criterion = {c.id: float(c.points) for c in rubric.criteria}
            if regrade_contracts:
                # The rubric that scales this revision is the item's now: its
                # snapshot (taken in the revision's transaction, below) is the
                # contract the revision cites.
                snapshot_of = (item, rubric)
    missing = [r.criterion_id for r in live_rows if r.criterion_id not in points_by_criterion]
    if not points_by_criterion or missing:
        return {
            "status": "skipped_no_criterion_points",
            "evidence_ids": [],
            "missing_criteria": missing,
        }

    now = utc_now_iso(clock)
    fraction = max(0.0, min(1.0, float(resolved_fraction)))
    seen: set[str] = set()
    new_rows: list[dict[str, Any]] = []
    if regrade_contracts:
        from learnloop.grading_epochs import next_grading_revision

        next_revision = next_grading_revision(repository.fetch_grading_evidence(attempt_id, include_superseded=True))
    else:
        next_revision = (max((r.grading_revision or 0) for r in live_rows)) + 1
    for row in live_rows:
        if row.criterion_id in seen:
            continue
        seen.add(row.criterion_id)
        new_rows.append(
            {
                "id": new_ulid(),
                "criterion_id": row.criterion_id,
                "points_awarded": fraction * points_by_criterion[row.criterion_id],
                "evidence": f"adjudicated:{adjudication_id}",
                "notes": rationale,
                "agent_run_id": None,
                "local_grader_id": f"adjudication:{adjudicator_source}",
                "grader_tier": ADJUDICATION_GRADER_TIER,
                "created_at": now,
                # Contract lineage rides forward so the projection resolves the
                # same historical criteria; attribution is deliberately None (a
                # response-level verdict asserts no per-facet structure) and
                # observation_id is None (UNIQUE index; lineage lives on the
                # adjudication row).
                "assessment_contract_version_id": (
                    (next(iter(version_ids)) if version_ids else None)
                    if regrade_contracts
                    else row.assessment_contract_version_id
                ),
                "recipe_id": row.recipe_id,
                "correlation_group": row.correlation_group,
                "grading_revision": next_revision,
            }
        )
    # The revision, the attempt's grade and, for a verdict against the key,
    # its C3 binding commit together, in the transaction the reads above ran
    # in (this scope is a savepoint of it).
    with repository.atomic():
        if snapshot_of is not None:
            from learnloop.learner.assessment_contracts import snapshot_for_presentation

            cited = snapshot_for_presentation(repository, vault, snapshot_of[0], rubric=snapshot_of[1], clock=clock,
                                             save_revision=False)
            new_rows = [{**row, "assessment_contract_version_id": cited} for row in new_rows]
        repository.insert_regrade_evidence(
            attempt_id=attempt_id,
            new_evidence_rows=new_rows,
            superseded_by_evidence_id=str(new_rows[0]["id"]),
            # Supersede every live tier: an adjudication is the response-level
            # authority, including over a prior adjudication (re-adjudication).
            supersede_tiers=(0, 1, 2, 3, 4),
            clock=clock,
        )
        # Mirror the regrade door's cache refresh so the attempt summary agrees
        # with the ledger. Review state is preserved: a grade-class adjudication
        # does not answer a pending clarification or manual-review obligation.
        attempt = repository.fetch_practice_attempt(attempt_id)
        if attempt is not None:
            rubric_total = sum(points_by_criterion.values()) or 1.0
            rubric_score = max(0, round(fraction * rubric_total))
            manual_review_reason = attempt.get("manual_review_reason")
            manual_review = bool(attempt.get("manual_review"))
            if regrade_contracts:
                from learnloop.outcome_contract import GRADE_CONTRACT_UNRECORDED

                # Replay's own formula (the cited contract's criteria sum to
                # its maximum), so the attempt row and any rebuild agree.
                correctness = rubric_score / max(int(round(rubric_total)), 1)
                if manual_review_reason == GRADE_CONTRACT_UNRECORDED:
                    # The revision records a contract: the hold it settles ends.
                    manual_review_reason, manual_review = None, False
            else:
                correctness = fraction
            repository.update_attempt_grade(
                attempt_id,
                rubric_score=rubric_score,
                correctness=correctness,
                grader_confidence=float(attempt.get("grader_confidence") or 0.0),
                manual_review=manual_review,
                manual_review_reason=manual_review_reason,
                error_type=attempt.get("error_type"),
                clock=clock,
            )
            _bind_key_adjudication(repository, vault, attempt, adjudicator_source=adjudicator_source, clock=clock)
    return {"status": "revised", "evidence_ids": [str(r["id"]) for r in new_rows]}


#: Adjudicator sources whose verdict is a comparison against the item's stored
#: key. A human or expert verdict, or a learner's clarification, is not read
#: from the key, so C3's binding does not apply to it.
KEY_BASED_ADJUDICATOR_SOURCES = frozenset({"deterministic_key"})


def _bind_key_adjudication(repository: Repository, vault: "LoadedVault | None", attempt: Mapping[str, Any], *,
                           adjudicator_source: str, clock: Clock | None) -> None:
    """C3 (canonical sources §7.3a, "Replacement grades"): a verdict against the
    key binds like a regrade. Without the vault the item is unknown, so
    nothing is bound (every grade adjudication caller passes it)."""

    if adjudicator_source not in KEY_BASED_ADJUDICATOR_SOURCES or vault is None:
        return
    item = vault.practice_items.get(str(attempt.get("practice_item_id")))
    if item is None:
        return
    from learnloop.clock import utc_now_iso
    from learnloop.db.stores.source_service import bind_replacement_grade

    bind_replacement_grade(
        repository.connection(), attempt_id=str(attempt["id"]), item=item,
        grading=f"adjudication:{adjudicator_source}", created_at=utc_now_iso(clock),
    )


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
    vault: "LoadedVault | None" = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Append an adjudication + a NEW interpretation and repoint the head (§3.3/§4.4).

    Adjudicated anchors carry authority: they narrow the credible interval (a
    deterministic/human anchor to a point). ``learner_clarification`` carries a
    bounded-trust weight < 1. Never overwrites prior rows.

    Ruling A (2026-07-27): when the adjudicated leading class FLIPS the
    response-level direction, this also writes a superseding
    ``grading_evidence`` revision (see
    :func:`append_adjudication_evidence_revision`), because the ledger — not
    the interpretation chain — is the directional authority. The returned dict
    carries the typed outcome under ``evidence_revision``. A held grade also
    needs assessed rows when the owner confirms its provisional class, and a
    ruling that confirms an earlier ruling's revised grade writes that grade
    again as its own, so replay keeps it as the head."""

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
            "response_posterior_json": canonical_json(posterior),
            "criterion_posteriors_json": None,
            "reference_prior_ids_json": None,
            "certainty_discount": certainty_value,
            # An adjudicated anchor's certainty is deterministic authority, not a
            # calibration-ensemble draw: persist it as the shared LCB so
            # EffectiveObservation never re-draws the grader Dirichlet (H1).
            "shared_certainty_lcb": certainty_value,
            "credible_interval_json": canonical_json(interval),
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
            "reviewed_raw_event_ids_json": canonical_json(reviewed),
            "adjudicator_source": adjudicator_source,
            "resolved_class": resolved_class,
            "resolved_distribution_json": canonical_json(dict(resolved_distribution)) if resolved_distribution else None,
            "rationale": rationale,
            "provenance_json": canonical_json({"bounded_trust_weight": trust}),
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
        payload_json=canonical_json({"adjudication_id": adjudication_id, "source": adjudicator_source}),
        clock=clock,
    )
    repository.append_measurement_event(
        administration_id=administration_id,
        kind="interpretation_activated",
        algorithm_version=PROJECTION_ALGORITHM_VERSION,
        observation_id=observation_id,
        payload_json=canonical_json({"interpretation_id": interpretation_id}),
        clock=clock,
    )

    # Ruling A: a direction flip lands in the ledger. Fractions come from the
    # same COARSE_RESPONSE score map the projection reads, so the ledger and
    # the unresolved-cause override can never disagree about what a class is
    # worth. A held grade needs assessed rows to release it even when the
    # adjudicated fraction matches its provisional score.
    from learnloop.attempts.outcome_schemas import (
        COARSE_RESPONSE_SLUG,
        ensure_builtin_schemas,
    )
    import json as _json_mod

    evidence_revision: dict[str, Any] = {"status": "skipped_direction_unchanged", "evidence_ids": []}
    ensure_builtin_schemas(repository, clock=clock)
    schema_row = repository.fetch_outcome_schema_version(slug=COARSE_RESPONSE_SLUG)
    score_fraction: dict[str, float] = (
        _json_mod.loads(schema_row["score_fraction_json"]) if schema_row is not None else {}
    )
    leading_new = _leading_class(posterior)
    leading_old = _leading_class(base)
    fraction_new = score_fraction.get(str(leading_new)) if leading_new is not None else None
    fraction_old = score_fraction.get(str(leading_old)) if leading_old is not None else None
    attempt_id = repository.observation_attempt_id(observation_id)
    restates = _another_adjudication_wrote_the_grade(repository, attempt_id, adjudication_id)
    if leading_new is None:
        evidence_revision = {"status": "skipped_ambiguous_leading_class", "evidence_ids": []}
    elif fraction_new is None:
        evidence_revision = {"status": "skipped_class_without_score_fraction", "evidence_ids": []}
    elif fraction_new == fraction_old and not (attempt_grade_held(repository, attempt_id) or restates):
        evidence_revision = {"status": "skipped_direction_unchanged", "evidence_ids": []}
    elif attempt_id is None:
        evidence_revision = {"status": "skipped_no_attempt", "evidence_ids": []}
    else:
        evidence_revision = append_adjudication_evidence_revision(
            repository,
            attempt_id=attempt_id,
            resolved_fraction=float(fraction_new),
            adjudication_id=adjudication_id,
            adjudicator_source=adjudicator_source,
            rationale=rationale,
            vault=vault,
            clock=clock,
        )
    return {
        "adjudication_id": adjudication_id,
        "interpretation_id": interpretation_id,
        "evidence_revision": evidence_revision,
    }

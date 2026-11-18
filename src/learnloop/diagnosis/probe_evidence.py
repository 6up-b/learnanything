"""Record the evidence produced by probe answers and their grades.

A presented answer first writes its observation and associated activity and
calibration facts. The episode posterior is then replayed and its beliefs
persisted. If that answer closes the active block, the block-end hook settles
feedback, evaluates completion, and records the next route.
Held grades consume presentations without updating belief or completion.
Presentationless grades and regrades also write calibration observations.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from learnloop.clock import Clock, parse_utc
from learnloop.db.repositories import (
    ProbeEpisodeRecord,
    ProbePresentationRecord,
    Repository,
)
from learnloop.diagnosis.probe_families import (
    APPROVED_DIAGNOSTIC_GRADING_SOURCES,
    CompiledInstrument,
    InstrumentCard,
    classify_outcome,
    instrument_observation_likelihoods,
    record_real_observation_counts,
)
from learnloop.diagnosis.probes import HypothesisSet
from learnloop.attempts.outcome_schemas import COARSE_RESPONSE_SLUG
from learnloop.vault.models import LoadedVault
from learnloop.diagnosis.probe_episodes import (
    _bayes_update,
    _entropy,
    _fired_error_types,
    _item_max_points,
    _resolved_slot_map_from_snapshot,
    episode_hypothesis_set,
    episode_posterior,
)
from learnloop.diagnosis.probe_blocks import (
    block_complete,
    end_diagnostic_block,
)
from learnloop.diagnosis.probe_completion import (
    close_diagnostic_segment,
    persist_episode_beliefs,
)
from learnloop.diagnosis.probe_presentations import (
    validate_presentation_for_submission,
)


def record_episode_evidence(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_id: str,
    attempt_id: str,
    practice_item_id: str,
    attempt_type: str,
    hints_used: int,
    probe_presentation_id: str | None,
    grading_source: str,
    tutor_contaminated: bool = False,
    ai_client: object | None = None,
    grade_held_for_review: bool = False,
    grader_identity: tuple[str, str] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Post-persist accounting for one attempt on an in-episode LO.

    Belief always updates (via posterior replay + persisted beliefs). Episode
    advancement happens only when the attempt consumes a valid presentation
    with type ``diagnostic_probe``, no contamination, and an approved
    diagnostic grading provider — everything else is incidental evidence.

    Feedback release, misconception normalization, the open-set trigger, the
    completion policy, and routing are BLOCK-boundary semantics (§5.7): they
    run through the block-end hook once the attempt closes the active block,
    never per attempt. Returns the hook payload when the block ended.

    ``grade_held_for_review`` is THE held predicate the attempt step
    evaluated in flight (held-grade-evidence F11): a held answer consumes its
    presentation but records an observation that moves no posterior and
    qualifies nothing, and it is no incidental evidence either.

    ``grader_identity`` is the submission's (prompt, output schema) calibration identity, which the presentation's
    grade dual-write stamps (TE2 landing ruling R1; None is the joint grader's, as before).
    """

    held_now = (attempt_id,) if grade_held_for_review else ()
    episode = repository.open_probe_episode(learning_object_id)
    if episode is None:
        return None
    hypothesis_set = episode_hypothesis_set(repository, episode)
    if hypothesis_set is None:
        return None

    if probe_presentation_id is not None:
        _record_presentation_observation(
            vault,
            repository,
            episode,
            hypothesis_set,
            attempt_id=attempt_id,
            practice_item_id=practice_item_id,
            attempt_type=attempt_type,
            hints_used=hints_used,
            probe_presentation_id=probe_presentation_id,
            grading_source=grading_source,
            tutor_contaminated=tutor_contaminated,
            grade_held_for_review=grade_held_for_review,
            grader_identity=grader_identity,
            clock=clock,
        )

    posterior = episode_posterior(vault, repository, episode, held_attempt_ids=held_now)
    if posterior is not None:
        persist_episode_beliefs(vault, repository, episode, posterior, clock=clock)

    if probe_presentation_id is None:
        return None
    refreshed = repository.probe_episode(episode.id)
    if refreshed is None or refreshed.status != "in_progress":
        return None

    if not block_complete(vault, repository, refreshed, probe_presentation_id):
        return None
    return end_diagnostic_block(vault, repository, refreshed, ai_client=ai_client, clock=clock)


def record_presentation_activity_classification(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    practice_item_id: str,
    attempt_type: str,
    hints_used: int,
    probe_presentation_id: str,
    grading_source: str,
    tutor_contaminated: bool = False,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Persist presentation-derived eligibility before canonical projection.

    The full probe observation is intentionally recorded later, after causal
    materialization. Its activity classification cannot wait that long: the
    canonical projection runs between those phases and must see near-clone and
    instructional-diagnostic disqualifications on the same live attempt. The
    later observation path restates this exact fact idempotently.
    """

    if grading_source not in APPROVED_DIAGNOSTIC_GRADING_SOURCES:
        return None
    validation = validate_presentation_for_submission(
        repository,
        probe_presentation_id,
        practice_item_id=practice_item_id,
        attempt_id=attempt_id,
        clock=clock,
    )
    if (
        not validation.valid
        or validation.presentation is None
        or validation.episode is None
    ):
        return None
    return _record_presentation_activity_fact(
        vault,
        repository,
        validation.episode,
        validation.presentation,
        attempt_id=attempt_id,
        practice_item_id=practice_item_id,
        attempt_type=attempt_type,
        hints_used=hints_used,
        tutor_contaminated=tutor_contaminated,
        clock=clock,
    )


def _presentation_contamination(
    *, attempt_type: str, hints_used: int, tutor_contaminated: bool
) -> dict[str, Any]:
    contamination: dict[str, Any] = {}
    if hints_used > 0:
        contamination["hints_used"] = hints_used
    if tutor_contaminated:
        contamination["tutor_help"] = True
    # The explicit don't-know outcome retains the presentation's
    # ``diagnostic_probe`` type; any other type contaminates the measurement.
    if attempt_type != "diagnostic_probe":
        contamination["attempt_type"] = attempt_type
    return contamination


def _record_presentation_activity_fact(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    presentation: ProbePresentationRecord,
    *,
    attempt_id: str,
    practice_item_id: str,
    attempt_type: str,
    hints_used: int,
    tutor_contaminated: bool,
    clock: Clock | None,
) -> dict[str, Any]:
    from learnloop.diagnosis.causal_activity_policy import (
        near_clone_from_selection_components,
    )

    contamination = _presentation_contamination(
        attempt_type=attempt_type,
        hints_used=hints_used,
        tutor_contaminated=tutor_contaminated,
    )
    contamination_class = (
        "instructional_diagnostic" if contamination else "pure_diagnostic"
    )
    near_clone_assessment = near_clone_from_selection_components(
        vault,
        practice_item_id=practice_item_id,
        selection_components=presentation.selection_components,
    )
    return repository.record_causal_activity_classification(
        attempt_id=attempt_id,
        contamination_class=contamination_class,
        near_clone=near_clone_assessment.near_clone,
        near_clone_basis=near_clone_assessment.basis,
        source="probe_presentation_observation",
        detail={
            "probe_episode_id": episode.id,
            "probe_presentation_id": presentation.id,
            "contamination": contamination or None,
            "near_clone_assessment": near_clone_assessment.as_dict(),
        },
        clock=clock,
    )


def _robust_observation_snapshot(
    repository: Repository,
    episode: ProbeEpisodeRecord,
    instrument: CompiledInstrument,
    slot_map: Mapping[str, str],
    posterior_before: Mapping[str, float],
    *,
    observed_outcome: str,
    grader_confidence: float | None,
) -> dict[str, Any] | None:
    """The mvp-0.8 decision-time posterior snapshot for one observation (§4.2).

    None for legacy episodes (no pinned channel). Deterministic given the pinned
    channel hash + observed emission -- replay reads this, never the current head."""

    if episode.calibration_model_hash is None:
        return None
    from learnloop.diagnosis.probe_robust import load_pinned_channel, pinned_decision_posterior

    channel = load_pinned_channel(repository, episode.calibration_model_hash)
    if channel is None:
        return None
    return pinned_decision_posterior(
        channel,
        instrument,
        dict(slot_map),
        dict(posterior_before),
        observed_outcome=observed_outcome,
        grader_confidence=grader_confidence,
        episode_id=episode.id,
    )


def _dual_write_probe_grade(
    vault: LoadedVault,
    repository: Repository,
    *,
    instrument: CompiledInstrument | None = None,
    practice_item_id: str,
    attempt_id: str,
    grading_source: str,
    observed_outcome: str,
    grader_identity: tuple[str, str] | None = None,
    clock: Clock | None = None,
) -> None:
    """P0.2 dual-write for probe submissions (§4.1, §7.2). Fail-safe (§7.3): appends
    a raw grade event + interpretation on a diagnostic administration alongside the
    unchanged three-key ``grader_channel`` probe observation. The probe posterior
    update is untouched (still ignores grader_confidence). Never raises.

    The versioned probe-outcome -> coarse-class mapping (§3.1) is
    snapshotted into the raw grade event's raw_output and the coarse class is pinned
    as the interpretation's observed class, so replay reproduces the mapping.

    ``grader_identity`` is the grade's (prompt, output schema) calibration identity
    (Slice 1 §4.3); None is the joint grader's, so callers that pass none stamp
    exactly what they did before."""

    try:
        item = vault.practice_items.get(practice_item_id)
        if item is None:
            return
        persisted = repository.fetch_practice_attempt(attempt_id) or {}
        rubric = vault.rubric_for_item(item)
        max_points = rubric.max_points if rubric is not None else 4
        from learnloop.attempts.grade_resolution import record_grade_dual_write

        coarse_override: str | None = None
        mapping_meta: dict[str, Any] = {}
        outcome_schema_slug = COARSE_RESPONSE_SLUG
        if instrument is not None:
            from learnloop.diagnosis.probe_outcome_mapping import (
                coarse_class_for_outcome,
                coarse_schema_slug,
                mapping_snapshot,
            )

            outcome_schema_slug = coarse_schema_slug(instrument)
            from learnloop.attempts.outcome_schemas import BUILTIN_SCHEMAS

            schema = next(s for s in BUILTIN_SCHEMAS if s.slug == outcome_schema_slug)
            coarse_override = coarse_class_for_outcome(
                instrument, observed_outcome, schema_true_classes=set(schema.true_classes)
            )
            mapping_meta = mapping_snapshot(instrument)

        record_grade_dual_write(
            vault,
            repository,
            observed_class_override=coarse_override,
            outcome_schema_slug=outcome_schema_slug,
            item=item,
            purpose="diagnostic",
            grading_source=grading_source,
            attempt_id=attempt_id,
            response_text=persisted.get("learner_answer_md"),
            rubric_score=persisted.get("rubric_score"),
            max_points=max_points,
            grader_confidence=persisted.get("grader_confidence"),
            raw_output={
                "observed_outcome": observed_outcome,
                "grading_source": grading_source,
                "rubric_score": persisted.get("rubric_score"),
                # Deliverable 1: snapshot the versioned probe->coarse mapping on the
                # administration's raw grade event so replay reproduces the class.
                "probe_coarse_mapping": mapping_meta or None,
            },
            domain=getattr(item, "learning_object_id", None),
            grading_prompt_version=grader_identity[0] if grader_identity else None,
            grader_output_schema_version=grader_identity[1] if grader_identity else None,
            clock=clock,
        )
    except Exception:  # noqa: BLE001 - fail-safe dual-write (§7.3)
        pass


def dual_write_presentationless_probe_grade(
    vault: LoadedVault,
    repository: Repository,
    *,
    practice_item_id: str,
    attempt_id: str,
    grading_source: str,
    grader_identity: tuple[str, str] | None = None,
    clock: Clock | None = None,
) -> None:
    """The same fail-safe dual-write for a probe answer with no presentation and no instrument (teacher TE2's
    lesson probe, ``attempts.attempts._record_lesson_probe``): a raw grade event and calibrated interpretation on a
    diagnostic administration, so the canonical projection banks the answer's reliable mass (Codex review F1).
    ``grader_identity`` is the submission's calibration identity, so a blind grade is calibrated as the blind
    grader's, never pooled with the joint grader's (Codex re-review F7)."""

    _dual_write_probe_grade(
        vault,
        repository,
        instrument=None,
        practice_item_id=practice_item_id,
        attempt_id=attempt_id,
        grading_source=grading_source,
        observed_outcome="graded",
        grader_identity=grader_identity,
        clock=clock,
    )


def dual_write_regraded_probe_grade(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    grading_source: str,
    grader_identity: tuple[str, str] | None,
    fired_error_types: Iterable[str],
    held: bool,
    clock: Clock | None = None,
) -> bool:
    """A regrade's probe grade, published under the replacement grade's own identity (TE2 landing ruling R1).

    A probe answer's raw grade event and interpretation are written once, by the submission's probe path
    (:func:`dual_write_presentationless_probe_grade` for a lesson probe, :func:`_record_presentation_observation` for
    FG1's presentation path), and replay never re-mints them (an ordinary practice answer's are written by
    ``attempts._dual_write_grade_channel`` on every application: a changed grade appended to its observation under
    ``replay.grade_channel_fixes``, a fresh chain without). So a regrade that only replays would leave the
    attempt's active interpretation on the original grader's identity and calibration (Codex's final verify, F7
    reopened). The regrade's publication calls this before its replay: the same dual-write the submission made,
    with the replacement grade's (prompt, schema) identity, appended and activated; replay reads it back.

    Written only where the submission wrote one: a lesson probe (no presentation; ``observed_outcome`` "graded" as
    on its first write), or a presentation whose observation recorded an outcome and whose new grade is not held
    for review (the first write's own condition). FG1d's incidental presentationless answer wrote none and gets
    none. The presentation's outcome is reclassified from the new grade: its score and the regrade's attributed
    error types (``fired_error_types``; the replay re-mints the error events after this). The probe observation's
    posterior is the submission's and is not changed here. Returns whether a grade was written.
    """

    persisted = repository.fetch_practice_attempt(attempt_id) or {}
    if persisted.get("attempt_type") != "diagnostic_probe":
        return False
    practice_item_id = str(persisted["practice_item_id"])
    presentation_id = persisted.get("probe_presentation_id")
    if presentation_id is None:
        from learnloop.causal_activity_policy import LESSON_PROBE_EVIDENCE_ORIGIN

        if persisted.get("evidence_origin") != LESSON_PROBE_EVIDENCE_ORIGIN:
            return False
        dual_write_presentationless_probe_grade(
            vault,
            repository,
            practice_item_id=practice_item_id,
            attempt_id=attempt_id,
            grading_source=grading_source,
            grader_identity=grader_identity,
            clock=clock,
        )
        return True
    if held:
        return False
    observation = repository.probe_observation_for_attempt(attempt_id)
    channel = observation.grader_channel if observation is not None else None
    if not channel or channel.get("observed_outcome") is None:
        return False
    presentation = repository.probe_presentation(str(presentation_id))
    snapshot = presentation.instrument_card_snapshot if presentation is not None else None
    if snapshot is None:
        return False
    instrument = CompiledInstrument.from_snapshot(snapshot)
    empty_stuck = bool(persisted.get("declared_stuck")) and not str(persisted.get("learner_answer_md") or "").strip()
    outcome = classify_outcome(
        instrument,
        rubric_score=persisted.get("rubric_score"),
        max_points=_item_max_points(vault, practice_item_id),
        attempt_type="dont_know" if persisted.get("declared_dont_know") or empty_stuck else "diagnostic_probe",
        fired_error_types=[str(error_type) for error_type in fired_error_types if error_type],
    )
    _dual_write_probe_grade(
        vault,
        repository,
        instrument=instrument,
        practice_item_id=practice_item_id,
        attempt_id=attempt_id,
        grading_source=grading_source,
        observed_outcome=outcome,
        grader_identity=grader_identity,
        clock=clock,
    )
    return True


def _record_presentation_observation(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    hypothesis_set: HypothesisSet,
    *,
    attempt_id: str,
    practice_item_id: str,
    attempt_type: str,
    hints_used: int,
    probe_presentation_id: str,
    grading_source: str,
    tutor_contaminated: bool,
    grade_held_for_review: bool = False,
    grader_identity: tuple[str, str] | None = None,
    clock: Clock | None,
) -> None:

    if repository.probe_observation_for_attempt(attempt_id) is not None:
        return  # idempotent retry (§5.1)
    validation = validate_presentation_for_submission(
        repository,
        probe_presentation_id,
        practice_item_id=practice_item_id,
        attempt_id=attempt_id,
        clock=clock,
    )
    if not validation.valid or validation.presentation is None:
        return  # rejected as qualifying evidence; attempt stays incidental
    presentation = validation.presentation

    # §5.8: a manual/self-grading provider cannot produce a qualifying
    # observation. The presentation is invalidated and the episode parks.
    if grading_source not in APPROVED_DIAGNOSTIC_GRADING_SOURCES:
        repository.end_probe_presentation(presentation.id, end_reason="invalidated", clock=clock)
        repository.update_probe_episode_status(episode.id, status="pending_items", clock=clock)
        return

    if not repository.consume_probe_presentation(presentation.id, clock=clock):
        return

    snapshot = presentation.instrument_card_snapshot
    if snapshot is None:
        return
    instrument = CompiledInstrument.from_snapshot(snapshot)
    labels = [hypothesis.label for hypothesis in hypothesis_set.hypotheses]
    slot_map = _resolved_slot_map_from_snapshot(snapshot, instrument, labels)
    if slot_map is None:
        return

    # Posterior before: full replay excluding this attempt (its observation row
    # does not exist yet and presentation-linked attempts are not incidental).
    before = episode_posterior(vault, repository, episode, hypothesis_set=hypothesis_set)
    posterior_before = before.posterior if before is not None else dict(hypothesis_set.prior)

    if grade_held_for_review:
        # held-grade-evidence F11: the answer consumed its presentation, but
        # its grade is held for review (nothing assessed, nothing validated):
        # no outcome is classified from the grader's provisional score, the
        # posterior does not move, nothing qualifies and no probe grade is
        # dual-written. The observation row records that it was answered.
        from learnloop.outcome_contract import GRADE_HELD_FOR_REVIEW

        contamination = _presentation_contamination(
            attempt_type=attempt_type, hints_used=hints_used, tutor_contaminated=tutor_contaminated,
        )
        entropy = _entropy(posterior_before)
        repository.insert_probe_observation(
            attempt_id=attempt_id,
            posterior_before=posterior_before,
            posterior_after=dict(posterior_before),
            entropy_before=entropy,
            entropy_after=entropy,
            realized_information_gain=0.0,
            independent_evidence_discount=0.0,
            contamination=contamination or None,
            grader_channel={
                "grader_policy": instrument.grader_policy,
                "grading_source": grading_source,
                "observed_outcome": None,
                GRADE_HELD_FOR_REVIEW: True,
            },
            updates_belief=False,
            eligible_for_completion=False,
            features={GRADE_HELD_FOR_REVIEW: True},
            clock=clock,
        )
        _record_presentation_activity_fact(
            vault, repository, episode, presentation, attempt_id=attempt_id,
            practice_item_id=practice_item_id, attempt_type=attempt_type, hints_used=hints_used,
            tutor_contaminated=tutor_contaminated, clock=clock,
        )
        if contamination:
            close_diagnostic_segment(repository, episode.id, clock=clock)
        return

    persisted_attempt = repository.fetch_practice_attempt(attempt_id) or {}
    # "I don't know" is an observation outcome, not an attempt channel.  Keep
    # the committed probe type for eligibility, but feed the explicit outcome
    # to the deterministic signature matcher so replay selects `unanswered`.
    # An empty "I'm stuck" answer (mvp-0.13) answered nothing either, so it
    # is the same `unanswered` observation; a stuck answer WITH text is
    # classified from its grade like any other.
    empty_stuck = bool(persisted_attempt.get("declared_stuck")) and not str(
        persisted_attempt.get("learner_answer_md") or ""
    ).strip()
    outcome_attempt_type = (
        "dont_know"
        if persisted_attempt.get("declared_dont_know") or empty_stuck
        else attempt_type
    )
    outcome = classify_outcome(
        instrument,
        rubric_score=_attempt_rubric_score(repository, attempt_id),
        max_points=_item_max_points(vault, practice_item_id),
        attempt_type=outcome_attempt_type,
        fired_error_types=_fired_error_types(repository, attempt_id),
    )

    # §8.2 long-form structured trace: when the card declares ordered
    # obligations, criterion-level grading evidence localizes the first
    # invalid step, preserves the correct prefix, marks dependent downstream
    # obligations unassessable, and bounds the response's evidence mass.
    structured_trace = None
    trace_mass: float | None = None
    trace_result = _assess_longform_trace(
        vault,
        repository,
        presentation,
        instrument,
        attempt_id=attempt_id,
        practice_item_id=practice_item_id,
        attempt_type=attempt_type,
    )
    if trace_result is not None:
        trace, trace_outcome = trace_result
        structured_trace = trace.as_dict()
        trace_mass = trace.assessable_mass
        if trace_outcome is not None:
            outcome = trace_outcome

    likelihoods = instrument_observation_likelihoods(instrument, slot_map, outcome)

    contamination = _presentation_contamination(
        attempt_type=attempt_type,
        hints_used=hints_used,
        tutor_contaminated=tutor_contaminated,
    )
    contaminated = bool(contamination)

    episode_config = vault.config.probe.episode
    weight = episode_config.contaminated_evidence_weight if contaminated else 1.0
    # §7.7 bounded task evidence mass: dialogue microprobe turns within one
    # block share the family's total mass; each turn's likelihood is damped by
    # its committed share so the block cannot exceed one task's evidence.
    task_evidence_share = float(presentation.selection_components.get("task_evidence_share", 1.0))
    weight = min(weight, max(min(task_evidence_share, 1.0), 0.0))
    if trace_mass is not None:
        # §8.2: a multi-obligation response is one instrument — its update is
        # bounded by the assessable share of the task's fixed evidence mass.
        weight = min(weight, max(min(trace_mass, 1.0), 0.0))
    posterior_after = _bayes_update(
        dict(posterior_before), likelihoods, weight=weight, prior_for_marginal=posterior_before
    )
    entropy_before = _entropy(posterior_before)
    entropy_after = _entropy(posterior_after)
    eligible = (
        not contaminated
        and attempt_type == "diagnostic_probe"
        and grading_source in APPROVED_DIAGNOSTIC_GRADING_SOURCES
    )
    features = _observation_features(
        repository, presentation, attempt_id=attempt_id, structured_trace=structured_trace
    )
    # mvp-0.8 robust cutover (§4.2 product 1): snapshot the immutable decision-time
    # posterior from observed_update over the episode-pinned channel, so historical
    # replay is byte-stable and (invariant 3) selection + update share the pin.
    grader_confidence = persisted_attempt.get("grader_confidence")
    robust_snapshot = _robust_observation_snapshot(
        repository,
        episode,
        instrument,
        slot_map,
        posterior_before,
        observed_outcome=outcome,
        grader_confidence=grader_confidence,
    )
    if robust_snapshot is not None:
        features = dict(features or {}, robust=robust_snapshot)
    repository.insert_probe_observation(
        attempt_id=attempt_id,
        posterior_before=posterior_before,
        posterior_after=posterior_after,
        entropy_before=entropy_before,
        entropy_after=entropy_after,
        # Signed: negative realized information (entropy increased) is a §13.2
        # retirement-telemetry signal and must not be clamped away.
        realized_information_gain=entropy_before - entropy_after,
        independent_evidence_discount=weight,
        contamination=contamination or None,
        grader_channel={
            "grader_policy": instrument.grader_policy,
            "grading_source": grading_source,
            "observed_outcome": outcome,
        },
        updates_belief=True,
        eligible_for_completion=eligible,
        features=features,
        clock=clock,
    )
    contamination_class = (
        "instructional_diagnostic"
        if contaminated
        else "pure_diagnostic"
    )
    # Restates the pre-projection fact idempotently. Keeping this call beside
    # the durable observation means direct callers of ``record_episode_evidence``
    # (outside apply_attempt's live pipeline) still get the same audit row.
    _record_presentation_activity_fact(
        vault,
        repository,
        episode,
        presentation,
        attempt_id=attempt_id,
        practice_item_id=practice_item_id,
        attempt_type=attempt_type,
        hints_used=hints_used,
        tutor_contaminated=tutor_contaminated,
        clock=clock,
    )
    _dual_write_probe_grade(
        vault,
        repository,
        instrument=instrument,
        practice_item_id=practice_item_id,
        attempt_id=attempt_id,
        grading_source=grading_source,
        observed_outcome=outcome,
        # TE2 landing ruling R1 (the re-review's open question): the submission's own calibration identity, so a
        # blind grade in a split vault is never stamped and calibrated as the joint grader's.
        grader_identity=grader_identity,
        clock=clock,
    )
    if contamination_class == "instructional_diagnostic":
        close_diagnostic_segment(
            repository,
            episode.id,
            clock=clock,
        )
    if eligible and instrument.family_template_id is not None and instrument.provenance == "instrument_card":
        record_real_observation_counts(
            repository,
            family_template_id=instrument.family_template_id,
            family_template_version=instrument.family_template_version or 1,
            posterior_after=posterior_after,
            slot_map=slot_map,
            observed_outcome=outcome,
            grader_version=instrument.grader_policy,
            practice_item_id=practice_item_id,
            clock=clock,
        )


def _attempt_rubric_score(repository: Repository, attempt_id: str) -> int | None:
    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        return None
    return attempt.get("rubric_score")


def _assess_longform_trace(
    vault: LoadedVault,
    repository: Repository,
    presentation: ProbePresentationRecord,
    instrument: CompiledInstrument,
    *,
    attempt_id: str,
    practice_item_id: str,
    attempt_type: str,
):
    """Assess the §8.2 structured trace for a long-form response, or None when
    the presentation's card declares no obligations (microprobes)."""

    from learnloop.diagnosis.longform_trace import (
        assess_trace,
        classify_trace_outcome,
        obligations_from_bindings,
        outcomes_from_grading_evidence,
    )

    if attempt_type != "diagnostic_probe":
        return None
    if presentation.instrument_card_id is None or presentation.instrument_card_version is None:
        return None
    card_record = repository.probe_instrument_card(
        presentation.instrument_card_id, presentation.instrument_card_version
    )
    if card_record is None:
        return None
    card = InstrumentCard.from_dict(card_record.card)
    obligations = obligations_from_bindings(card.bindings)
    if not obligations:
        return None
    item = vault.practice_items.get(practice_item_id)
    rubric = vault.rubric_for_item(item) if item is not None else None
    criteria_max = {
        criterion.id: float(criterion.points) for criterion in (rubric.criteria if rubric else [])
    }
    outcomes = outcomes_from_grading_evidence(
        obligations, repository.fetch_grading_evidence(attempt_id), criteria_max
    )
    trace = assess_trace(
        obligations, outcomes, total_task_evidence_mass=instrument.total_task_evidence_mass
    )
    trace_outcome = classify_trace_outcome(trace, obligations, instrument.outcome_alphabet)
    return trace, trace_outcome


def _observation_features(
    repository: Repository,
    presentation: ProbePresentationRecord,
    *,
    attempt_id: str,
    structured_trace: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Logged-only observation features (§7.1): answer confidence, latency
    (both submitted and derived from presentation timestamps), and the §8.2
    structured trace. Replay never reads these."""

    features: dict[str, Any] = {}
    attempt = repository.fetch_practice_attempt(attempt_id) or {}
    if attempt.get("answer_confidence") is not None:
        features["answer_confidence"] = int(attempt["answer_confidence"])
    if attempt.get("latency_seconds") is not None:
        features["latency_seconds"] = int(attempt["latency_seconds"])
    served = parse_utc(presentation.served_at)
    submitted = parse_utc(attempt.get("created_at"))
    if served is not None and submitted is not None:
        features["presentation_latency_seconds"] = max(
            0, int((submitted - served).total_seconds())
        )
    if structured_trace is not None:
        features["structured_trace"] = dict(structured_trace)
    return features or None


from __future__ import annotations

from typing import Any

from learnloop.ai.client import make_ai_provider_client
from learnloop.ai.routing import fallback_provider_for, provider_for_task
from learnloop.ai.runtime import check_ai_runtime
from learnloop.codex.client import CodexUnavailable, make_codex_client
from learnloop.codex.runtime import check_codex_runtime
from learnloop.services.attempts import (
    AttemptDraft,
    AttemptValidationError,
    SelfGradeErrorAttribution,
    SelfGradeInput,
    complete_attempt_with_ai_fallback,
    complete_attempt_with_ai_required,
    complete_attempt_with_codex_fallback,
    complete_attempt_with_codex_required,
    complete_self_graded_attempt,
)
from learnloop.services.followups import evaluate_attempt_intervention_followup
from learnloop.services.probes import probe_posterior
from learnloop.services.scheduler import SchedulerSession, build_due_queue
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.queue import PracticeItemInput, _sections
from learnloop_sidecar.handlers.serializers import practice_item_detail, scheduled_item_dto
from learnloop_sidecar.handlers.sessions import SessionCheckpointInput, patch_checkpoint
from learnloop_sidecar.logging import debug_enabled, log_event
from learnloop_sidecar.registry import method


class PracticeDraftCheckpoint(ParamsModel):
    session_id: str
    practice_item_id: str
    answer_md: str
    hints_used: int = 0


class SelfGradeErrorAttributionDto(ParamsModel):
    error_type: str
    criterion_id: str | None = None


class SelfGradeInputDto(ParamsModel):
    criterion_points: dict[str, float]
    confidence: int
    fatal_errors: list[str] | None = None
    error_type: str | None = None
    notes: str | None = None
    error_attributions: list[SelfGradeErrorAttributionDto] | None = None


class SubmitAttemptInput(ParamsModel):
    session_id: str
    practice_item_id: str
    answer_md: str
    attempt_type: str
    hints_used: int = 0
    latency_seconds: int | None = None
    self_grade: SelfGradeInputDto | None = None


class DontKnowInput(ParamsModel):
    session_id: str
    practice_item_id: str
    hints_used: int = 0
    latency_seconds: int | None = None
    self_grade: SelfGradeInputDto | None = None


class SkipInput(ParamsModel):
    session_id: str
    practice_item_id: str


@method("get_practice_item", PracticeItemInput)
def get_practice_item(ctx: SidecarContext, params: PracticeItemInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    return practice_item_detail(vault, repository, params.practice_item_id)


@method("save_practice_draft", PracticeDraftCheckpoint)
def save_practice_draft(ctx: SidecarContext, params: PracticeDraftCheckpoint) -> dict[str, Any]:
    _vault, repository = ctx.require_vault()
    patch_checkpoint(
        repository,
        SessionCheckpointInput(
            session_id=params.session_id,
            current_practice_item_id=params.practice_item_id,
            current_answer=params.answer_md,
            hints_used=params.hints_used,
        ),
    )
    return {"ok": True}


@method("submit_attempt", SubmitAttemptInput)
def submit_attempt(ctx: SidecarContext, params: SubmitAttemptInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    _require_open_session(repository, params.session_id)
    before = _latent_snapshot(vault, repository, params.practice_item_id)
    draft = AttemptDraft(
        practice_item_id=params.practice_item_id,
        learner_answer_md=params.answer_md,
        attempt_type=params.attempt_type,
        hints_used=params.hints_used,
        latency_seconds=params.latency_seconds,
        session_id=params.session_id,
    )
    self_grade = _self_grade(params.self_grade)
    provider_name, runtime, client = _ready_grading_provider(vault)
    unavailable_label = "AI grading"
    try:
        if self_grade is None:
            if not runtime.ready or client is None:
                raise SidecarError(
                    "grading_fallback_required",
                    f"{unavailable_label} is unavailable. Grade your answer to continue.",
                    retryable=True,
                )
            if provider_name != "codex":
                result = complete_attempt_with_ai_required(
                    vault,
                    repository,
                    draft,
                    runtime=runtime,
                    ai_client=client,
                )
            else:
                result = complete_attempt_with_codex_required(
                    vault,
                    repository,
                    draft,
                    runtime=runtime,
                    codex_client=client,
                )
        else:
            if provider_name != "codex":
                result = complete_attempt_with_ai_fallback(
                    vault,
                    repository,
                    draft,
                    self_grade,
                    runtime=runtime,
                    ai_client=client,
                )
            else:
                result = complete_attempt_with_codex_fallback(
                    vault,
                    repository,
                    draft,
                    self_grade,
                    runtime=runtime,
                    codex_client=client,
                )
    except SidecarError:
        raise
    except (CodexUnavailable, TimeoutError):
        raise SidecarError(
            "grading_fallback_required",
            f"{unavailable_label} is unavailable. Grade your answer to continue.",
            retryable=True,
        )
    except (AttemptValidationError, ValueError) as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    _persist_feedback_metadata(repository, result, self_grade)
    _evaluate_followup(vault, repository, params.session_id, result)
    _log_attempt_recorded(repository, params.session_id, params.answer_md, result)
    _log_state_update(vault, repository, "submit_attempt", params.session_id, before, result)
    return _attempt_result(result)


@method("submit_dont_know", DontKnowInput)
def submit_dont_know(ctx: SidecarContext, params: DontKnowInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    _require_open_session(repository, params.session_id)
    before = _latent_snapshot(vault, repository, params.practice_item_id)
    grade = _self_grade(params.self_grade) or SelfGradeInput(criterion_points={}, confidence=3)
    draft = AttemptDraft(
        practice_item_id=params.practice_item_id,
        learner_answer_md="",
        attempt_type="dont_know",
        hints_used=params.hints_used,
        latency_seconds=params.latency_seconds,
        session_id=params.session_id,
    )
    try:
        result = complete_self_graded_attempt(vault, repository, draft, grade)
    except (AttemptValidationError, ValueError) as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    _persist_feedback_metadata(repository, result, None)
    _evaluate_followup(vault, repository, params.session_id, result)
    _log_attempt_recorded(repository, params.session_id, "", result)
    _log_state_update(vault, repository, "submit_dont_know", params.session_id, before, result)
    return _attempt_result(result)


@method("skip_practice_item", SkipInput)
def skip_practice_item(ctx: SidecarContext, params: SkipInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    session = _require_open_session(repository, params.session_id)
    queue = build_due_queue(
        vault,
        repository,
        session=SchedulerSession(
            session_id=params.session_id,
            available_minutes=session.get("available_minutes"),
            energy=session.get("energy"),
        ),
    )
    dtos = [scheduled_item_dto(vault, repository, item) for item in queue if item.practice_item_id != params.practice_item_id]
    return versioned(
        {
            "generated_at": _nowish(),
            "session_id": params.session_id,
            "sections": _sections(dtos),
            "total_items": len(dtos),
        }
    )


def _self_grade(payload: SelfGradeInputDto | None) -> SelfGradeInput | None:
    if payload is None:
        return None
    return SelfGradeInput(
        criterion_points=payload.criterion_points,
        confidence=payload.confidence,
        fatal_errors=payload.fatal_errors,
        error_type=payload.error_type,
        notes=payload.notes,
        error_attributions=[
            SelfGradeErrorAttribution(error_type=attribution.error_type, criterion_id=attribution.criterion_id)
            for attribution in payload.error_attributions
        ]
        if payload.error_attributions
        else None,
    )


def _attempt_result(result) -> dict[str, Any]:
    return versioned(result.as_dict())


def _codex_client(vault):
    try:
        return make_codex_client(vault.config.codex, vault.root)
    except CodexUnavailable:
        return None


def _ai_client(vault, provider_name: str):
    try:
        return make_ai_provider_client(vault.config, vault.root, provider_name=provider_name)
    except CodexUnavailable:
        return None


def _ready_grading_provider(vault):
    selection = provider_for_task(vault.config, "grading")
    provider_name = selection.provider_name
    runtime = _runtime_for_provider(vault, provider_name)
    if runtime.ready:
        return provider_name, runtime, _client_for_provider(vault, provider_name)
    fallback = fallback_provider_for(vault.config, selection)
    if fallback:
        fallback_runtime = _runtime_for_provider(vault, fallback)
        if fallback_runtime.ready:
            return fallback, fallback_runtime, _client_for_provider(vault, fallback)
    return provider_name, runtime, None


def _runtime_for_provider(vault, provider_name: str):
    if provider_name == "codex":
        return check_codex_runtime(vault.root, vault.config.codex)
    return check_ai_runtime(vault.root, vault.config, provider_name=provider_name)


def _client_for_provider(vault, provider_name: str):
    if provider_name == "codex":
        return _codex_client(vault)
    return _ai_client(vault, provider_name)




def _persist_feedback_metadata(repository, result, self_grade: SelfGradeInput | None) -> None:
    feedback_md = result.feedback_md
    if feedback_md is None and self_grade is not None and result.grading_source == "self":
        feedback_md = self_grade.notes
    fatal_errors = result.fatal_errors
    if not fatal_errors and self_grade is not None and result.grading_source == "self":
        fatal_errors = self_grade.fatal_errors or []
    repository.upsert_attempt_feedback_metadata(
        attempt_id=result.attempt_id,
        grading_source=result.grading_source,
        fallback_reason=result.fallback_reason,
        agent_run_id=result.agent_run_id,
        fatal_errors=fatal_errors,
        feedback_md=feedback_md,
        repair_suggestions=result.repair_suggestions,
    )


def _evaluate_followup(vault, repository, session_id: str, result) -> None:
    evaluate_attempt_intervention_followup(
        vault,
        repository,
        result=result,
        session_id=session_id,
    )


def _log_attempt_recorded(repository, session_id: str, answer_md: str, result) -> None:
    attempt = repository.fetch_practice_attempt(result.attempt_id) or {}
    surprise = repository.latest_attempt_surprise(result.attempt_id) or {}
    feedback = repository.fetch_attempt_feedback_metadata(result.attempt_id) or {}
    log_event(
        "attempt_recorded",
        session_id=session_id,
        attempt_id=result.attempt_id,
        practice_item_id=result.practice_item_id,
        learning_object_id=result.learning_object_id,
        scheduler_slate_id=attempt.get("scheduler_slate_id"),
        scheduler_candidate_id=attempt.get("scheduler_candidate_id"),
        learner_answer_md=answer_md,
        rubric_score=result.rubric_score,
        correctness=result.correctness,
        hints_used=attempt.get("hints_used"),
        latency_seconds=attempt.get("latency_seconds"),
        grading_source=result.grading_source,
        grader_confidence=result.grader_confidence,
        feedback_md=feedback.get("feedback_md"),
        triggered_actions=surprise.get("triggered_actions"),
        suppressed_actions=surprise.get("suppressed_actions"),
    )


def _latent_snapshot(vault, repository, practice_item_id: str) -> dict[str, Any] | None:
    """Capture pre-attempt latent state for a practice item, for debug deltas.

    Returns ``None`` (and does no work) unless sidecar debug logging is enabled.
    """

    if not debug_enabled():
        return None
    item = vault.practice_items.get(practice_item_id)
    learning_object = vault.learning_object_for_item(item) if item is not None else None
    if learning_object is None:
        return {"learning_object_id": None}
    mastery = repository.mastery_state(learning_object.id)
    probe = repository.probe_state(learning_object.id)
    explanation = repository.latest_scheduler_explanation(practice_item_id)
    return {
        "learning_object_id": learning_object.id,
        "mastery_mean": _display_mean(mastery),
        "mastery_variance": _display_variance(mastery),
        "evidence_count": mastery.evidence_count if mastery is not None else 0,
        "probe_status": probe.status if probe is not None else None,
        "probe_completed": probe.probe_attempts_completed if probe is not None else None,
        "probe_target": probe.probe_attempts_target if probe is not None else None,
        # The EIG that motivated selecting this probe item, so realized updates
        # can be compared against expected information gain.
        "expected_information_gain": explanation.get("expected_information_gain") if explanation else None,
    }


def _log_state_update(vault, repository, method_name: str, session_id: str, before, result) -> None:
    if not debug_enabled():
        return
    probe_after = repository.probe_state(result.learning_object_id)
    before = before or {}
    before_var = before.get("mastery_variance")
    trace = result.mastery_trace
    # Realized IG over the same hypothesis set probe-EIG is computed on, so the
    # debug stream shows expected vs actual information gain side by side.
    posterior = probe_posterior(vault, repository, result.learning_object_id)
    log_event(
        "state_update",
        method=method_name,
        session_id=session_id,
        attempt_id=result.attempt_id,
        practice_item_id=result.practice_item_id,
        learning_object_id=result.learning_object_id,
        attempt_type="dont_know" if method_name == "submit_dont_know" else None,
        rubric_score=result.rubric_score,
        correctness=result.correctness,
        grading_source=result.grading_source,
        # Latent (mastery) delta: what the user space actually learned.
        mastery_mean_before=before.get("mastery_mean"),
        mastery_mean_after=result.mastery_mean,
        mastery_variance_before=before_var,
        mastery_variance_after=result.mastery_variance,
        mastery_variance_reduction=(
            round(before_var - result.mastery_variance, 6) if before_var is not None else None
        ),
        evidence_count_before=before.get("evidence_count"),
        # IRT 2PL picture of the mastery update (spec_irt_difficulty.md §7.2): the
        # "easy correct vs hard correct" distinction, with the mean/confidence split.
        item_difficulty_b=round(trace.difficulty_b, 4) if trace is not None else None,
        item_discrimination_a=round(trace.discrimination_a, 4) if trace is not None else None,
        expected_correctness=round(trace.expected_correctness, 4) if trace is not None else None,
        predicted_score=round(trace.predicted_score, 4) if trace is not None else None,
        observed_y=round(trace.observed_y, 4) if trace is not None else None,
        innovation=round(trace.innovation, 4) if trace is not None else None,
        sensitivity_h=round(trace.sensitivity_h, 4) if trace is not None else None,
        measurement_noise=round(trace.measurement_noise, 4) if trace is not None else None,
        kalman_gain=round(trace.kalman_gain, 4) if trace is not None else None,
        variance_reduction=round(trace.variance_reduction, 4) if trace is not None else None,
        mu_step=round(trace.mu_step, 4) if trace is not None else None,
        step_capped=trace.step_capped if trace is not None else None,
        mu_clamped=trace.mu_clamped if trace is not None else None,
        # Probe progress + the EIG that justified this elicitation vs realized IG.
        expected_information_gain=before.get("expected_information_gain"),
        realized_information_gain=(
            round(posterior.normalized_information_gain, 4) if posterior is not None else None
        ),
        posterior_top_probability=(round(posterior.top_probability, 4) if posterior is not None else None),
        posterior=(
            {label: round(value, 4) for label, value in posterior.posterior.items()}
            if posterior is not None
            else None
        ),
        probe_status_before=before.get("probe_status"),
        probe_status_after=probe_after.status if probe_after is not None else None,
        probe_completed_after=probe_after.probe_attempts_completed if probe_after is not None else None,
        probe_target=probe_after.probe_attempts_target if probe_after is not None else None,
        families_converged=probe_after.families_converged if probe_after is not None else None,
        # Surprise + downstream effects.
        surprise_direction=result.surprise_direction,
        predictive_surprise=round(result.predictive_surprise, 4),
        bayesian_surprise=round(result.bayesian_surprise, 4),
        due_at=result.due_at,
        fsrs_rating=result.fsrs_rating,
        error_event_ids=result.error_event_ids or None,
    )


def _display_mean(mastery) -> float | None:
    if mastery is None:
        return None
    from learnloop.services.mastery import display_mastery

    return display_mastery(mastery).mastery_mean


def _display_variance(mastery) -> float | None:
    if mastery is None:
        return None
    from learnloop.services.mastery import display_mastery

    return display_mastery(mastery).mastery_variance


def _require_open_session(repository, session_id: str) -> dict[str, Any]:
    session = repository.fetch_session(session_id)
    if session is None:
        raise SidecarError("not_found", f"Session {session_id} was not found.")
    if session["ended_at"] is not None:
        raise SidecarError("validation_error", f"Session {session_id} has ended.")
    return session


def _nowish() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

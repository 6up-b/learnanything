from __future__ import annotations

from typing import Any

from learnloop.codex.client import CodexUnavailable
from learnloop.config import CODEX_PROVIDER_NAMES
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
from learnloop.services.tutor_qa import hint_equivalents_for_submission
from learnloop.services.probe_episodes import (
    commit_item_presentation,
    enter_episode,
    episode_contract,
    episode_hypothesis_set,
    next_probe_item,
    probe_serving_block_reason,
    serve_presentation,
    stop_diagnosing_and_teach,
    validate_presentation_for_submission,
)
from learnloop.services.probes import probe_posterior
from learnloop.services.scheduler import SchedulerSession, build_due_queue
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers.ai_providers import ready_grading_provider
from learnloop_sidecar.handlers.queue import PracticeItemInput, _sections
from learnloop_sidecar.handlers.serializers import practice_item_detail, scheduled_item_dto
from learnloop_sidecar.handlers.sessions import SessionCheckpointInput, patch_checkpoint
from learnloop_sidecar.handlers.teach_back import filter_unready_teach_back_items
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
    primed: bool = False
    # Probe redesign §5.1: the committed presentation this submission consumes.
    probe_presentation_id: str | None = None
    # Probe redesign §7.1: learner answer confidence (1-5), logged-only.
    answer_confidence: int | None = None
    assessment_contract_version_id: str | None = None
    submission_id: str | None = None


class DontKnowInput(ParamsModel):
    session_id: str
    practice_item_id: str
    hints_used: int = 0
    latency_seconds: int | None = None
    self_grade: SelfGradeInputDto | None = None
    probe_presentation_id: str | None = None
    answer_confidence: int | None = None
    assessment_contract_version_id: str | None = None
    submission_id: str | None = None


class SkipInput(ParamsModel):
    session_id: str
    practice_item_id: str


@method("get_practice_item", PracticeItemInput)
def get_practice_item(ctx: SidecarContext, params: PracticeItemInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    return practice_item_detail(vault, repository, params.practice_item_id)


class ProbeContractInput(ParamsModel):
    practice_item_id: str
    session_id: str | None = None


@method("get_probe_contract", ProbeContractInput)
def get_probe_contract(ctx: SidecarContext, params: ProbeContractInput) -> dict[str, Any]:
    """The probe measurement contract for opening one item (§12).

    When the item's LO has an in-progress diagnostic episode and the item
    resolves an executable instrument, this durably commits and serves a
    presentation (§5.1) and returns the enforced interaction contract: forced
    `diagnostic_probe` attempt type, disabled assistance, delayed feedback,
    and the presentation id the submission must consume. Otherwise the item
    serves as ordinary practice (`active: false`).
    """

    vault, repository = ctx.require_vault()
    item = vault.practice_items.get(params.practice_item_id)
    if item is None:
        raise SidecarError("not_found", f"Unknown Practice Item {params.practice_item_id}.")
    episode = repository.open_probe_episode(item.learning_object_id)
    if episode is None or episode.status != "in_progress":
        return versioned({"active": False})

    # §5.9 orchestration gate (shared with the Textual surface): the routine
    # per-session qualifying-observation cap and the fresh-vault onboarding
    # ceiling. An active, in-budget calibration session lifts both — it is an
    # explicit learner opt-in.
    from learnloop.services.calibration_sessions import calibration_cap_lifted

    cap_lifted = params.session_id is not None and calibration_cap_lifted(
        repository, params.session_id
    )
    block_reason = probe_serving_block_reason(
        vault, repository, session_id=params.session_id, cap_lifted=cap_lifted
    )
    if block_reason is not None:
        return versioned({"active": False, "reason": block_reason})

    # §5.8: measurement requires an approved diagnostic grading provider. Under
    # a manual/self-grading provider no qualifying observation may be served:
    # the episode parks and the LO degrades to belief-only ordinary practice.
    _provider, runtime, client = ready_grading_provider(vault, override=ctx.grading_provider_override)
    if not runtime.ready or client is None:
        active = (
            repository.active_probe_presentation_for_session(params.session_id)
            if params.session_id is not None
            else repository.active_probe_presentation(episode.id)
        )
        if active is not None:
            repository.end_probe_presentation(active.id, end_reason="invalidated")
        repository.update_probe_episode_status(episode.id, status="pending_items")
        return versioned({"active": False, "reason": "grading_provider_unavailable"})

    hypothesis_set = episode_hypothesis_set(repository, episode)
    if hypothesis_set is None:
        return versioned({"active": False, "reason": "no_instrument"})
    # Routine scheduling precommits the assignment in the same transaction as
    # its slate candidate. Opening the selected item merely marks that durable
    # presentation served; opening another returned item does not reinterpret
    # it as a probe.
    active = (
        repository.active_probe_presentation_for_session(params.session_id)
        if params.session_id is not None
        else repository.active_probe_presentation(episode.id)
    )
    if active is None and params.session_id is not None:
        other_assignment = repository.active_probe_presentation(episode.id)
        if other_assignment is not None and other_assignment.scheduler_candidate_id is not None:
            return versioned({"active": False, "reason": "probe_assigned_to_other_session"})
    if active is not None:
        validation = validate_presentation_for_submission(
            repository,
            active.id,
            practice_item_id=item.id,
        )
        if validation.valid:
            serve_presentation(repository, active.id)
            contract = episode_contract(vault, repository, item.learning_object_id) or {}
            return versioned({"active": True, "presentation_id": active.id, **contract})
        if validation.reason == "item_mismatch":
            return versioned({"active": False, "reason": "different_probe_assignment"})
        return versioned({"active": False, "reason": validation.reason or "stale_presentation"})

    # §5.9 routine planner, shadow mode (§13.3): log where this episode ranks
    # among all open episodes under plain vs disagreement-boosted information
    # rate. Log-only until held-out predictive gains justify promotion.
    extra_components = None
    if vault.config.probe.shadow.enabled:
        from learnloop.services.calibration_sessions import routine_planner_shadow

        planner = routine_planner_shadow(vault, repository, episode.id)
        if planner is not None:
            extra_components = {"shadow_planner": planner}
    presentation = commit_item_presentation(
        vault, repository, episode, item, hypothesis_set,
        extra_selection_components=extra_components,
    )
    if presentation is None:
        return versioned({"active": False, "reason": "no_instrument"})
    contract = episode_contract(vault, repository, item.learning_object_id) or {}
    return versioned({"active": True, "presentation_id": presentation.id, **contract})


@method("stop_probe_diagnosing", PracticeItemInput)
def stop_probe_diagnosing(ctx: SidecarContext, params: PracticeItemInput) -> dict[str, Any]:
    """`Stop diagnosing and teach me` (§3): end the measurement block, persist
    the typed transition decision, and open a post-intervention state segment."""

    vault, repository = ctx.require_vault()
    item = vault.practice_items.get(params.practice_item_id)
    if item is None:
        raise SidecarError("not_found", f"Unknown Practice Item {params.practice_item_id}.")
    decision = stop_diagnosing_and_teach(vault, repository, item.learning_object_id)
    return versioned({"stopped": decision is not None, "decision": decision})


class NextProbeItemInput(ParamsModel):
    learning_object_id: str


@method("get_next_probe_item", NextProbeItemInput)
def get_next_probe_item(ctx: SidecarContext, params: NextProbeItemInput) -> dict[str, Any]:
    """The item that would continue this LO's open diagnostic block, if any.

    Read-only peek (§5.7 continuity) — never commits a presentation. The Tauri
    UI uses this to jump straight to the next observation within an
    in-progress block instead of round-tripping through the general queue
    between every attempt.
    """

    vault, repository = ctx.require_vault()
    candidate = next_probe_item(vault, repository, params.learning_object_id)
    if candidate is None:
        return versioned({"active": False})
    return versioned({"active": True, "practice_item_id": candidate.item.id})


class OverconfidenceProbeInput(ParamsModel):
    learning_object_id: str
    facet_id: str | None = None


@method("start_overconfidence_probe", OverconfidenceProbeInput)
def start_overconfidence_probe(ctx: SidecarContext, params: OverconfidenceProbeInput) -> dict[str, Any]:
    """Launch a diagnostic episode from the F5 overconfidence list (§4.3).

    Opens (or reuses) the LO's diagnostic episode tagged
    ``origin='overconfidence_list'`` so analytics can separate adversarial
    selection from drift. Idempotent per LO. The follow-up probe item surfaces
    in the ordinary Today queue, so the caller refreshes the queue afterward.
    """

    vault, repository = ctx.require_vault()
    if params.learning_object_id not in vault.learning_objects:
        raise SidecarError("not_found", f"Unknown Learning Object {params.learning_object_id}.")
    episode = enter_episode(
        vault,
        repository,
        params.learning_object_id,
        trigger="goal_diagnostic",
        origin="overconfidence_list",
    )
    return versioned(
        {
            "episode_id": episode.id,
            "learning_object_id": params.learning_object_id,
            "status": episode.status,
        }
    )


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
    submission_id = _submission_id(params.submission_id, params.probe_presentation_id)
    cached = _cached_submission(repository, submission_id, params.practice_item_id)
    if cached is not None:
        return cached
    _require_open_session(repository, params.session_id)
    before = _latent_snapshot(vault, repository, params.practice_item_id)
    # Substantive tutor questions asked mid-attempt count as hints: fold them
    # into hints_used so the existing hint dampening / FSRS rating caps apply.
    question_hints = hint_equivalents_for_submission(
        repository, params.practice_item_id, params.session_id
    )
    hints_used = params.hints_used + question_hints
    item = vault.practice_items.get(params.practice_item_id)
    if item is not None and item.hint_policy.max_useful_hints > 0:
        hints_used = min(hints_used, item.hint_policy.max_useful_hints)
    draft = AttemptDraft(
        practice_item_id=params.practice_item_id,
        learner_answer_md=params.answer_md,
        attempt_type=params.attempt_type,
        hints_used=hints_used,
        latency_seconds=params.latency_seconds,
        session_id=params.session_id,
        primed=params.primed,
        probe_presentation_id=params.probe_presentation_id,
        answer_confidence=params.answer_confidence,
        assessment_contract_version_id=params.assessment_contract_version_id,
        submission_id=submission_id,
    )
    self_grade = _self_grade(params.self_grade)
    provider_name, runtime, client = ready_grading_provider(vault, override=ctx.grading_provider_override)
    unavailable_label = "AI grading"
    try:
        if self_grade is None:
            if not runtime.ready or client is None:
                raise SidecarError(
                    "grading_fallback_required",
                    f"{unavailable_label} is unavailable. Grade your answer to continue.",
                    retryable=True,
                )
            if provider_name not in CODEX_PROVIDER_NAMES:
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
            if provider_name not in CODEX_PROVIDER_NAMES:
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
    _evaluate_followup(
        vault, repository, params.session_id, result, ai_client=client if runtime.ready else None
    )
    # Clear the checkpoint in the same call that records the attempt, so a lost
    # client-side clear can never leave a submitted draft to replay on restart.
    repository.clear_session_checkpoint(params.session_id)
    _log_attempt_recorded(repository, params.session_id, params.answer_md, result)
    _log_state_update(vault, repository, "submit_attempt", params.session_id, before, result)
    payload = _attempt_result(result, repository)
    _store_submission_receipt(repository, submission_id, result.attempt_id, result.practice_item_id, payload)
    return payload


@method("submit_dont_know", DontKnowInput)
def submit_dont_know(ctx: SidecarContext, params: DontKnowInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    submission_id = _submission_id(params.submission_id, params.probe_presentation_id)
    cached = _cached_submission(repository, submission_id, params.practice_item_id)
    if cached is not None:
        return cached
    _require_open_session(repository, params.session_id)
    before = _latent_snapshot(vault, repository, params.practice_item_id)
    grade = _self_grade(params.self_grade) or SelfGradeInput(criterion_points={}, confidence=3)
    draft = AttemptDraft(
        practice_item_id=params.practice_item_id,
        learner_answer_md="",
        attempt_type="diagnostic_probe" if params.probe_presentation_id else "dont_know",
        hints_used=params.hints_used,
        latency_seconds=params.latency_seconds,
        session_id=params.session_id,
        probe_presentation_id=params.probe_presentation_id,
        answer_confidence=params.answer_confidence,
        assessment_contract_version_id=params.assessment_contract_version_id,
        submission_id=submission_id,
        declared_dont_know=True,
    )
    try:
        result = complete_self_graded_attempt(vault, repository, draft, grade)
    except (AttemptValidationError, ValueError) as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    _persist_feedback_metadata(repository, result, None)
    _evaluate_followup(vault, repository, params.session_id, result)
    repository.clear_session_checkpoint(params.session_id)
    _log_attempt_recorded(repository, params.session_id, "", result)
    _log_state_update(vault, repository, "submit_dont_know", params.session_id, before, result)
    payload = _attempt_result(result, repository)
    _store_submission_receipt(repository, submission_id, result.attempt_id, result.practice_item_id, payload)
    return payload


def _submission_id(client_id: str | None, presentation_id: str | None) -> str | None:
    """Return the stable retry key; old probe clients inherit one for free."""

    if client_id and client_id.strip():
        return client_id.strip()
    if presentation_id:
        return f"probe:{presentation_id}"
    return None


def _cached_submission(repository, submission_id: str | None, practice_item_id: str) -> dict[str, Any] | None:
    if submission_id is None:
        return None
    receipt = repository.attempt_submission_receipt(submission_id)
    if receipt is not None:
        if receipt["practice_item_id"] != practice_item_id:
            raise SidecarError("validation_error", "submission id was already used for another item")
        return receipt["result"]
    # A process can stop in the tiny interval after the attempt transaction and
    # before its response receipt. Never grade or write the same submission a
    # second time; the original response can be recovered by reopening feedback.
    existing = repository.practice_attempt_by_submission_id(submission_id)
    if existing is not None:
        if existing["practice_item_id"] != practice_item_id:
            raise SidecarError("validation_error", "submission id was already used for another item")
        raise SidecarError(
            "submission_committed",
            f"Attempt {existing['id']} was recorded; reopen its feedback to continue.",
            retryable=False,
        )
    return None


def _store_submission_receipt(
    repository,
    submission_id: str | None,
    attempt_id: str,
    practice_item_id: str,
    payload: dict[str, Any],
) -> None:
    if submission_id is None:
        return
    repository.insert_attempt_submission_receipt(
        submission_id=submission_id,
        attempt_id=attempt_id,
        practice_item_id=practice_item_id,
        result=payload,
    )


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
    queue = filter_unready_teach_back_items(
        vault, queue, grading_provider_override=ctx.grading_provider_override
    )
    dtos = [scheduled_item_dto(vault, repository, item) for item in queue if item.practice_item_id != params.practice_item_id]
    repository.clear_session_checkpoint(params.session_id)
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


def _attempt_result(result, repository=None) -> dict[str, Any]:
    # `probe_block_end` rides along inside as_dict() (camelized to
    # probeBlockEnd): the §5.7 hook payload with released feedback and route.
    payload = versioned(result.as_dict())
    block_end = getattr(result, "probe_block_end", None)
    if repository is not None:
        # Probe redesign §5.6/§5.7: the client defers feedback while the LO's
        # diagnostic episode is still measuring; the block-end hook releases
        # the block's withheld feedback and routes the learner.
        episode = repository.open_probe_episode(result.learning_object_id)
        payload["probeEpisode"] = (
            {
                "episodeId": episode.id,
                "status": episode.status,
                "feedbackDeferred": episode.status == "in_progress" and block_end is None,
            }
            if episode is not None
            else None
        )
    return payload


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


def _evaluate_followup(vault, repository, session_id: str, result, ai_client=None) -> None:
    evaluate_attempt_intervention_followup(
        vault,
        repository,
        result=result,
        session_id=session_id,
        ai_client=ai_client,
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

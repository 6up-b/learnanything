from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, timedelta
from typing import Any, Iterable

from learnloop.attempt_types import NON_RECORDING_ATTEMPT_TYPES, SUPPORTED_ATTEMPT_TYPES, unsupported_attempt_types
from learnloop.ai.client import AIProviderClient
from learnloop.ai.runtime import AIRuntimeReport
from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.codex.client import CodexClient, CodexUnavailable
from learnloop.codex.prompts import GRADING_PROMPT_VERSION
from learnloop.codex.runtime import CodexRuntimeReport
from learnloop.codex.schemas import GradingProposal
from learnloop.db.repositories import (
    ActiveErrorEvent,
    FacetRecallState,
    MasteryState,
    PracticeItemQualityState,
    PracticeItemState,
    Repository,
)
from learnloop.ids import new_ulid
from learnloop.services.fsrs import MemoryState, Rating, apply_review, interval_for_retention, rating_from_score
from learnloop.services.ability_transition import estimate_ability_transition
from learnloop.services.grading import (
    GradingValidationError,
    ValidatedCodexGrade,
    ValidatedCriterionEvidence,
    ValidatedErrorAttribution,
    build_grading_context,
    confidence_to_grader_confidence,
    evidence_coverage,
    grading_context_hash,
    resolved_rubric,
    validate_codex_grading_proposal,
)
from learnloop.services.error_taxonomy import persist_unknown_error_type_proposals
from learnloop.services.mastery import (
    MasteryObservation,
    MasteryObservationTrace,
    display_mastery,
    initial_mastery_state_for_learning_object,
    item_irt_params,
    update_mastery_traced,
)
from learnloop.services.probes import record_probe_attempt
from learnloop.services.proposals import maybe_promote_self_tagged_fatal_error
from learnloop.services.recall_coverage import (
    build_facet_recall_updates,
    build_facet_recall_updates_from_prior,
    build_quality_state_update,
    build_quality_state_update_from_prior,
    derive_facet_outcomes,
    event_local_severity,
    event_local_severity_from_attempts,
    familiarity_discount,
    familiarity_discount_from_attempts,
    predicted_correctness,
    predicted_correctness_from_prior,
    resolve_coverage,
    resolve_error_impact,
    resolve_reliability,
)
from learnloop.services.surprise import compute_surprise
from learnloop.vault.hashes import practice_item_hash
from learnloop.vault.models import LoadedVault, PracticeItem, Rubric


# Per spec §"Attempt-type handling": a `dont_know` attempt is deterministically
# attributed to a recall failure (score 0, no grading role invoked).
DONT_KNOW_ERROR_TYPE = "recall_failure"
SCAFFOLD_FAILURE_ERROR_TYPE = "scaffold_failure"


@dataclass(frozen=True)
class AttemptDraft:
    practice_item_id: str
    learner_answer_md: str
    attempt_type: str = "independent_attempt"
    hints_used: int = 0
    latency_seconds: int | None = None
    session_id: str | None = None


@dataclass(frozen=True)
class SelfGradeErrorAttribution:
    """One learner-attributed error from the self-grade form (spec §"self-grade").

    Mirrors a Codex ``error_attribution``: ``error_type`` is resolved against the
    vault taxonomy for severity / misconception status. ``criterion_id`` records
    which under-credited rubric criterion the learner tied the error to — surfaced
    in the attribution evidence, not persisted as a separate column (the persisted
    shape stays identical to Codex grading).
    """

    error_type: str
    criterion_id: str | None = None


@dataclass(frozen=True)
class SelfGradeInput:
    criterion_points: dict[str, float]
    confidence: int
    fatal_errors: list[str] | None = None
    error_type: str | None = None
    notes: str | None = None
    error_attributions: list[SelfGradeErrorAttribution] | None = None


@dataclass(frozen=True)
class GradeAttribution:
    error_type: str
    severity: float
    evidence: str | None = None
    is_misconception: bool = False
    target_evidence_families: list[str] = field(default_factory=list)
    target_criterion_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResolvedGrade:
    rubric_score: int
    criterion_points: dict[str, float]
    evidence_rows: list[dict[str, object]]
    error_attributions: list[GradeAttribution]
    grader_confidence: float
    confidence: int | None
    manual_review_reason: str | None
    feedback_md: str | None = None
    repair_suggestions: list[dict[str, Any]] = field(default_factory=list)
    fatal_errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AttemptResult:
    attempt_id: str
    practice_item_id: str
    learning_object_id: str
    rubric_score: int
    correctness: float
    grader_confidence: float
    manual_review_reason: str | None
    fsrs_rating: str
    due_at: str
    mastery_mean: float
    mastery_variance: float
    surprise_direction: str
    predictive_surprise: float
    bayesian_surprise: float
    error_event_ids: list[str]
    grading_source: str = "self"
    fallback_reason: str | None = None
    agent_run_id: str | None = None
    feedback_md: str | None = None
    repair_suggestions: list[dict[str, Any]] = field(default_factory=list)
    fatal_errors: list[str] = field(default_factory=list)
    # IRT picture of the mastery update (spec §7.1); debug-only, excluded from as_dict.
    mastery_trace: MasteryObservationTrace | None = None
    debug_payload: dict[str, object] | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "attempt_id": self.attempt_id,
            "practice_item_id": self.practice_item_id,
            "learning_object_id": self.learning_object_id,
            "rubric_score": self.rubric_score,
            "correctness": self.correctness,
            "grader_confidence": self.grader_confidence,
            "manual_review_reason": self.manual_review_reason,
            "fsrs_rating": self.fsrs_rating,
            "due_at": self.due_at,
            "mastery_mean": self.mastery_mean,
            "mastery_variance": self.mastery_variance,
            "surprise_direction": self.surprise_direction,
            "predictive_surprise": self.predictive_surprise,
            "bayesian_surprise": self.bayesian_surprise,
            "error_event_ids": self.error_event_ids,
            "grading_source": self.grading_source,
            "fallback_reason": self.fallback_reason,
            "agent_run_id": self.agent_run_id,
            "feedback_md": self.feedback_md,
            "repair_suggestions": self.repair_suggestions,
            "fatal_errors": self.fatal_errors,
            "debug": self.debug_payload or {},
        }


@dataclass(frozen=True)
class ApplyAttemptInput:
    """Resolved attempt payload consumed by the shared attempt step.

    Grading is deliberately outside this shape. Live self-grade, AI/Codex
    grading, replay, and regrade all hand an already-resolved grade to the same
    step so derived learner state is computed in one place.
    """

    draft: AttemptDraft
    attempt_id: str
    grade: ResolvedGrade
    replace_existing: bool = False
    record_probe_update: bool = True
    error_event_ids_override: list[str] | None = None


@dataclass(frozen=True)
class AttemptPriorState:
    """Prior learner/item state read once before computing one attempt."""

    mastery: MasteryState
    active_errors: list[ActiveErrorEvent]
    practice_item_state: PracticeItemState | None
    practice_item_quality_state: PracticeItemQualityState | None
    recent_learning_object_attempts: list[dict[str, Any]]
    recent_practice_item_attempts: list[dict[str, Any]]
    aggregate_facet_recall: dict[str, FacetRecallState | None]
    item_facet_recall: dict[str, FacetRecallState | None]

    def facet_recall_state(self, facet_id: str, practice_item_id: str | None = None) -> FacetRecallState | None:
        if practice_item_id is None:
            return self.aggregate_facet_recall.get(facet_id)
        return self.item_facet_recall.get(facet_id)

    def facet_recall_by_scope(self, facets: Iterable[str], practice_item_id: str) -> dict[tuple[str, str | None], FacetRecallState | None]:
        return {
            (facet, item_scope): self.facet_recall_state(facet, item_scope)
            for facet in facets
            for item_scope in (None, practice_item_id)
        }


@dataclass(frozen=True)
class AttemptApplication:
    """Computed attempt outputs before they are persisted.

    This is the state-output boundary for the attempt pipeline. The computation
    still loads its prior snapshot through Repository today, but every row the
    attempt will write is materialized here before the persistence step runs.
    """

    attempt_record: dict[str, Any]
    evidence_rows: list[dict[str, object]]
    error_events: list[dict[str, Any]]
    surprise_record: dict[str, object]
    practice_item_state: PracticeItemState
    mastery_state: MasteryState
    facet_recall_states: list[dict[str, Any]]
    quality_state: dict[str, Any]
    ability_transition: dict[str, Any]
    attempt_debug_payload: dict[str, object]
    result: AttemptResult


class AttemptServiceNotReady(RuntimeError):
    pass


class AttemptValidationError(ValueError):
    pass


def complete_attempt_with_codex_fallback(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    fallback_grade: SelfGradeInput,
    *,
    runtime: CodexRuntimeReport,
    codex_client: CodexClient | None = None,
    clock: Clock | None = None,
) -> AttemptResult:
    return _complete_attempt_with_agent_fallback(
        vault,
        repository,
        draft,
        fallback_grade,
        runtime=runtime,
        ai_client=codex_client,
        grading_source="codex",
        missing_client_reason="codex_client_missing",
        failure_prefix="codex_failed",
        clock=clock,
    )


def complete_attempt_with_ai_fallback(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    fallback_grade: SelfGradeInput,
    *,
    runtime: AIRuntimeReport,
    ai_client: AIProviderClient | None = None,
    clock: Clock | None = None,
) -> AttemptResult:
    return _complete_attempt_with_agent_fallback(
        vault,
        repository,
        draft,
        fallback_grade,
        runtime=runtime,
        ai_client=ai_client,
        grading_source="ai",
        missing_client_reason="ai_client_missing",
        failure_prefix="ai_failed",
        clock=clock,
    )


def _complete_attempt_with_agent_fallback(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    fallback_grade: SelfGradeInput,
    *,
    runtime,
    ai_client: AIProviderClient | CodexClient | None = None,
    grading_source: str,
    missing_client_reason: str,
    failure_prefix: str,
    clock: Clock | None = None,
) -> AttemptResult:
    item, _learning_object, _rubric = _resolve_attempt_target(vault, draft)
    if not runtime.ready or ai_client is None:
        reason = runtime.status if not runtime.ready else missing_client_reason
        result = complete_self_graded_attempt(vault, repository, draft, fallback_grade, clock=clock)
        return _with_fallback(result, reason)

    attempt_id = new_ulid()
    context = build_grading_context(
        vault,
        item,
        attempt_id=attempt_id,
        learner_answer_md=draft.learner_answer_md,
    )
    now = utc_now_iso(clock)
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": "grading",
            **_agent_run_provider_fields(ai_client, runtime),
            "prompt_template": "grading",
            "prompt_version": GRADING_PROMPT_VERSION,
            "input_context_hash": grading_context_hash(context),
            "output_schema": "GradingProposal",
            "started_at": now,
            "status": "running",
        }
    )
    try:
        proposal = ai_client.run_grading_proposal(context)
        result = complete_codex_graded_attempt(
            vault,
            repository,
            draft,
            proposal,
            attempt_id=attempt_id,
            agent_run_id=agent_run_id,
            grading_source=grading_source,
            clock=clock,
        )
    except (CodexUnavailable, TimeoutError, GradingValidationError, AttemptValidationError, ValueError) as exc:
        repository.complete_agent_run(agent_run_id, status="failed", error_message=str(exc), clock=clock)
        result = complete_self_graded_attempt(vault, repository, draft, fallback_grade, clock=clock)
        return _with_fallback(result, f"{failure_prefix}:{type(exc).__name__}", agent_run_id=agent_run_id)
    repository.complete_agent_run(agent_run_id, status="completed", clock=clock)
    return _with_source(result, grading_source=grading_source, agent_run_id=agent_run_id)


def complete_attempt_with_codex_required(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    *,
    runtime: CodexRuntimeReport,
    codex_client: CodexClient | None = None,
    clock: Clock | None = None,
) -> AttemptResult:
    return _complete_attempt_with_agent_required(
        vault,
        repository,
        draft,
        runtime=runtime,
        ai_client=codex_client,
        grading_source="codex",
        missing_client_reason="codex_client_missing",
        clock=clock,
    )


def complete_attempt_with_ai_required(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    *,
    runtime: AIRuntimeReport,
    ai_client: AIProviderClient | None = None,
    clock: Clock | None = None,
) -> AttemptResult:
    return _complete_attempt_with_agent_required(
        vault,
        repository,
        draft,
        runtime=runtime,
        ai_client=ai_client,
        grading_source="ai",
        missing_client_reason="ai_client_missing",
        clock=clock,
    )


def _complete_attempt_with_agent_required(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    *,
    runtime,
    ai_client: AIProviderClient | CodexClient | None = None,
    grading_source: str,
    missing_client_reason: str,
    clock: Clock | None = None,
) -> AttemptResult:
    if not runtime.ready or ai_client is None:
        reason = runtime.status if not runtime.ready else missing_client_reason
        raise CodexUnavailable(reason)

    item, _learning_object, _rubric = _resolve_attempt_target(vault, draft)
    attempt_id = new_ulid()
    context = build_grading_context(
        vault,
        item,
        attempt_id=attempt_id,
        learner_answer_md=draft.learner_answer_md,
    )
    now = utc_now_iso(clock)
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": "grading",
            **_agent_run_provider_fields(ai_client, runtime),
            "prompt_template": "grading",
            "prompt_version": GRADING_PROMPT_VERSION,
            "input_context_hash": grading_context_hash(context),
            "output_schema": "GradingProposal",
            "started_at": now,
            "status": "running",
        }
    )
    try:
        proposal = ai_client.run_grading_proposal(context)
        result = complete_codex_graded_attempt(
            vault,
            repository,
            draft,
            proposal,
            attempt_id=attempt_id,
            agent_run_id=agent_run_id,
            grading_source=grading_source,
            clock=clock,
        )
    except (CodexUnavailable, TimeoutError, GradingValidationError, AttemptValidationError, ValueError) as exc:
        repository.complete_agent_run(agent_run_id, status="failed", error_message=str(exc), clock=clock)
        raise
    repository.complete_agent_run(agent_run_id, status="completed", clock=clock)
    return _with_source(result, grading_source=grading_source, agent_run_id=agent_run_id)


def complete_self_graded_attempt(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    grade: SelfGradeInput,
    *,
    clock: Clock | None = None,
) -> AttemptResult:
    now_iso = utc_now_iso(clock)
    attempt_id = new_ulid()
    item, _learning_object, rubric = _resolve_attempt_target(vault, draft)
    grader_confidence = confidence_to_grader_confidence(grade.confidence)
    manual_review_reason = "low_self_confidence" if grader_confidence < 0.4 else None
    manual_review_reason = _attempt_manual_review_reason(manual_review_reason, draft)
    criterion_points = _validated_criterion_points(rubric, grade.criterion_points)
    fatal_errors = grade.fatal_errors or []
    _validate_fatal_errors(rubric, fatal_errors)
    attribution_error_type = grade.error_type
    per_criterion_attributions = _validated_self_grade_attributions(rubric, grade.error_attributions)
    if draft.attempt_type == "dont_know":
        criterion_points = {criterion.id: 0.0 for criterion in rubric.criteria}
        fatal_errors = []
        per_criterion_attributions = []
        # A don't-know is deterministically attributed to recall_failure so it
        # writes an error event and feeds surprise / cross-LO propagation through
        # the standard pipeline (spec §"Attempt-type handling").
        attribution_error_type = _dont_know_error_type(draft.hints_used)
    error_attributions = _self_grade_attributions(
        vault, fatal_errors, attribution_error_type, per_criterion_attributions
    )
    rubric_score = _rubric_score(rubric, criterion_points, fatal_errors)
    evidence_rows = [
        {
            "id": new_ulid(),
            "criterion_id": criterion.id,
            "points_awarded": criterion_points[criterion.id],
            "evidence": f"Self-grade awarded {criterion_points[criterion.id]:g}/{criterion.points:g}.",
            "notes": grade.notes,
            "local_grader_id": "self",
            "grader_tier": 1,
            "created_at": now_iso,
        }
        for criterion in rubric.criteria
    ]
    result = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=draft,
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=rubric_score,
                criterion_points=criterion_points,
                evidence_rows=evidence_rows,
                error_attributions=error_attributions,
                grader_confidence=grader_confidence,
                confidence=grade.confidence,
                manual_review_reason=manual_review_reason,
                feedback_md=grade.notes,
                fatal_errors=fatal_errors,
            ),
        ),
        clock=clock,
    )
    # Durable-probe promotion (spec §12.4): a misconception the learner self-attached
    # often enough becomes a candidate rubric fatal error, queued for review only.
    # Runs across every distinct attributed error (legacy single tag, fatal errors,
    # and the per-criterion picks); the promotion gate itself ignores non-misconceptions.
    if draft.attempt_type != "dont_know":
        for promoted_error_type in dict.fromkeys(
            attribution.error_type for attribution in error_attributions
        ):
            maybe_promote_self_tagged_fatal_error(
                vault, repository, item=item, error_type=promoted_error_type, clock=clock
            )
    return result


def complete_codex_graded_attempt(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    proposal: GradingProposal,
    *,
    attempt_id: str | None = None,
    agent_run_id: str | None = None,
    grading_source: str = "codex",
    clock: Clock | None = None,
) -> AttemptResult:
    item, _learning_object, _rubric = _resolve_attempt_target(vault, draft)
    expected_attempt_id = attempt_id or proposal.attempt_id
    try:
        validated = validate_codex_grading_proposal(
            proposal,
            attempt_id=expected_attempt_id,
            item=item,
            vault=vault,
            learner_answer_md=draft.learner_answer_md,
        )
    except GradingValidationError as exc:
        raise AttemptValidationError(str(exc)) from exc
    result = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=draft,
            attempt_id=expected_attempt_id,
            grade=_resolved_codex_grade(
                validated,
                agent_run_id=agent_run_id,
                clock=clock,
                manual_review_reason=_attempt_manual_review_reason(validated.manual_review_reason, draft),
            ),
        ),
        clock=clock,
    )
    learning_object = vault.learning_object_for_item(item)
    persist_unknown_error_type_proposals(
        vault,
        repository,
        attributions=validated.error_attributions,
        attempt_id=expected_attempt_id,
        agent_run_id=agent_run_id,
        related_concept_id=learning_object.concept if learning_object is not None else None,
        clock=clock,
    )
    return _with_source(result, grading_source=grading_source, agent_run_id=agent_run_id)


def replay_existing_attempt(
    vault: LoadedVault,
    repository: Repository,
    attempt: dict,
    *,
    clock: Clock | None = None,
    error_event_ids: list[str] | None = None,
    error_events: list[dict[str, Any]] | None = None,
    error_attributions: list[GradeAttribution] | None = None,
) -> AttemptResult:
    """Recompute derived state for a persisted attempt without re-grading it."""

    evidence = repository.fetch_grading_evidence(attempt["id"])
    criterion_points = {row.criterion_id: row.points_awarded for row in evidence}
    draft = AttemptDraft(
        practice_item_id=attempt["practice_item_id"],
        learner_answer_md=attempt.get("learner_answer_md") or "",
        attempt_type=attempt.get("attempt_type") or "independent_attempt",
        hints_used=int(attempt.get("hints_used") or 0),
        latency_seconds=attempt.get("latency_seconds"),
        session_id=attempt.get("session_id"),
    )
    error_type = attempt.get("error_type")
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=draft,
            attempt_id=attempt["id"],
            grade=ResolvedGrade(
                rubric_score=int(attempt.get("rubric_score") or 0),
                criterion_points=criterion_points,
                evidence_rows=[],
                error_attributions=error_attributions
                if error_attributions is not None
                else _replay_error_attributions(vault, error_type, error_events=error_events),
                grader_confidence=float(attempt.get("grader_confidence") or 1.0),
                confidence=attempt.get("confidence"),
                manual_review_reason=attempt.get("manual_review_reason"),
            ),
            replace_existing=True,
            record_probe_update=False,
            error_event_ids_override=error_event_ids,
        ),
        clock=clock,
    )


def _agent_run_provider_fields(client: AIProviderClient | CodexClient, runtime) -> dict[str, str | None]:
    provider = getattr(client, "provider_name", None) or getattr(runtime, "active_provider", None) or "codex"
    provider_type = getattr(client, "provider_type", None) or getattr(runtime, "provider_type", None)
    model = getattr(client, "model", None) or getattr(runtime, "model", None)
    provider_revision = getattr(runtime, "provider_revision", None) or getattr(runtime, "actual_revision", None)
    fields = {
        "provider": provider,
        "provider_type": provider_type,
        "model": model,
        "provider_revision": provider_revision,
    }
    if provider == "codex" or provider_type == "codex_sdk":
        fields["codex_revision"] = provider_revision
    return fields


def _with_source(result: AttemptResult, *, grading_source: str, agent_run_id: str | None = None) -> AttemptResult:
    return replace(result, grading_source=grading_source, agent_run_id=agent_run_id)


def _with_fallback(result: AttemptResult, reason: str, *, agent_run_id: str | None = None) -> AttemptResult:
    return replace(result, grading_source="self", fallback_reason=reason, agent_run_id=agent_run_id)


def _resolve_attempt_target(vault: LoadedVault, draft: AttemptDraft):
    unsupported = unsupported_attempt_types([draft.attempt_type])
    if unsupported:
        supported = ", ".join(SUPPORTED_ATTEMPT_TYPES)
        raise AttemptValidationError(f"Unsupported attempt_type {draft.attempt_type}. Supported: {supported}")
    if draft.attempt_type in NON_RECORDING_ATTEMPT_TYPES:
        raise AttemptValidationError(f"{draft.attempt_type} does not write a formal attempt")
    item = vault.practice_items.get(draft.practice_item_id)
    if item is None:
        raise AttemptValidationError(f"Unknown Practice Item {draft.practice_item_id}")
    learning_object = vault.learning_object_for_item(item)
    if learning_object is None:
        raise AttemptValidationError(f"{item.id} references missing Learning Object {item.learning_object_id}")
    # "dont_know" is a universal escape hatch: a learner can always declare they
    # don't know an item regardless of its configured attempt_types_allowed. It
    # is graded deterministically (all criteria zeroed) rather than via Codex, so
    # it never depends on the item's allowed content attempt types.
    if (
        item.attempt_types_allowed
        and draft.attempt_type != "dont_know"
        and draft.attempt_type not in item.attempt_types_allowed
    ):
        raise AttemptValidationError(f"{draft.attempt_type} is not allowed for {item.id}")
    try:
        rubric = resolved_rubric(vault, item)
    except GradingValidationError as exc:
        raise AttemptValidationError(str(exc)) from exc
    if draft.hints_used < 0:
        raise AttemptValidationError("hints_used must be non-negative")
    if draft.latency_seconds is not None and draft.latency_seconds < 0:
        raise AttemptValidationError("latency_seconds must be non-negative")
    return item, learning_object, rubric


def apply_attempt(
    vault: LoadedVault,
    repository: Repository,
    attempt: ApplyAttemptInput,
    *,
    clock: Clock | None = None,
) -> AttemptResult:
    """Apply one resolved attempt through the shared learner-state pipeline.

    This is the single step used by live recording and deterministic replay. It
    expects grading to have already happened, computes all output rows, then
    persists attempt, mastery, facet recall, item quality, surprise, error
    events, ability transition audit, and debug trace.
    """

    application = compute_attempt_application(vault, repository, attempt, clock=clock)
    _persist_attempt_application(repository, application, replace_existing=attempt.replace_existing)
    if attempt.record_probe_update:
        record_probe_attempt(vault, repository, application.result.learning_object_id, clock=clock)
    return application.result


def compute_attempt_application(
    vault: LoadedVault,
    repository: Repository,
    attempt: ApplyAttemptInput,
    *,
    clock: Clock | None = None,
    prior_state: AttemptPriorState | None = None,
) -> AttemptApplication:
    """Compute the rows and result for one resolved attempt without persisting.

    This is the testable state-output boundary for live recording, replay, and
    calibration. It reads the current prior state but does not write to storage.
    """

    return _compute_resolved_grade_application(
        vault,
        repository,
        attempt.draft,
        attempt_id=attempt.attempt_id,
        grade=attempt.grade,
        clock=clock,
        error_event_ids_override=attempt.error_event_ids_override,
        prior_state=prior_state,
    )


def _persist_attempt_application(
    repository: Repository,
    application: AttemptApplication,
    *,
    replace_existing: bool,
) -> None:
    if replace_existing:
        repository.replace_attempt_derived_outcome(
            attempt=application.attempt_record,
            error_events=application.error_events,
            surprise=application.surprise_record,
            practice_item_state=application.practice_item_state,
            mastery_state=application.mastery_state,
            facet_recall_states=application.facet_recall_states,
            quality_state=application.quality_state,
            ability_transition=application.ability_transition,
            attempt_debug_payload=application.attempt_debug_payload,
        )
    else:
        repository.record_attempt_outcome(
            attempt=application.attempt_record,
            evidence_rows=application.evidence_rows,
            error_events=application.error_events,
            surprise=application.surprise_record,
            practice_item_state=application.practice_item_state,
            mastery_state=application.mastery_state,
            facet_recall_states=application.facet_recall_states,
            quality_state=application.quality_state,
            ability_transition=application.ability_transition,
            attempt_debug_payload=application.attempt_debug_payload,
        )


def load_attempt_prior_state(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_id: str,
    practice_item_id: str,
    facets: Iterable[str],
    now_iso: str,
) -> AttemptPriorState:
    """Read the prior-state snapshot used by one attempt computation."""

    facet_ids = list(dict.fromkeys(facets))
    mastery = repository.mastery_state(learning_object_id) or initial_mastery_state_for_learning_object(
        vault,
        repository,
        learning_object_id,
        now_iso,
    )
    return AttemptPriorState(
        mastery=mastery,
        active_errors=repository.active_errors_by_learning_object(learning_object_id),
        practice_item_state=repository.practice_item_state(practice_item_id),
        practice_item_quality_state=repository.practice_item_quality_state(practice_item_id),
        recent_learning_object_attempts=repository.list_recent_attempts_by_learning_object(
            learning_object_id,
            limit=max(vault.config.recall_coverage.familiarity_recent_attempt_window, 20),
        ),
        recent_practice_item_attempts=repository.list_recent_attempts_by_practice_item(practice_item_id, limit=5),
        aggregate_facet_recall={
            facet: repository.facet_recall_state(learning_object_id, facet)
            for facet in facet_ids
        },
        item_facet_recall={
            facet: repository.facet_recall_state(learning_object_id, facet, practice_item_id)
            for facet in facet_ids
        },
    )


def _compute_resolved_grade_application(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    *,
    attempt_id: str,
    grade: ResolvedGrade,
    clock: Clock | None = None,
    error_event_ids_override: list[str] | None = None,
    prior_state: AttemptPriorState | None = None,
) -> AttemptApplication:
    item, learning_object, rubric = _resolve_attempt_target(vault, draft)
    observed_at = (clock or SystemClock()).now().astimezone(UTC)
    now_iso = utc_now_iso(clock)
    correctness = grade.rubric_score / max(rubric.max_points, 1)
    subjects = vault.subjects_for_item(item)
    subject = subjects[0] if subjects else None
    coverage = resolve_coverage(
        item,
        rubric,
        attempt_type=draft.attempt_type,
        hints_used=draft.hints_used,
        learner_answer_md=draft.learner_answer_md,
    )
    if prior_state is None:
        prior_state = load_attempt_prior_state(
            vault,
            repository,
            learning_object_id=learning_object.id,
            practice_item_id=item.id,
            facets=[*item.evidence_facets, *coverage.covered_facets],
            now_iso=now_iso,
        )
    prior_mastery = prior_state.mastery
    grade_attributions = _canonicalized_grade_attributions(vault, grade.error_attributions)
    primary_error_type = _primary_error_type(grade_attributions)
    item_a, item_b = item_irt_params(item, learning_object, vault.config.mastery)
    expected_correctness, prediction_trace = predicted_correctness_from_prior(
        prior_state.aggregate_facet_recall,
        item,
        prior_mastery=prior_mastery,
        item_a=item_a,
        item_b=item_b,
        config=vault.config,
    )
    facet_outcomes = derive_facet_outcomes(
        item,
        rubric,
        criterion_points=grade.criterion_points,
        covered_facets=coverage.covered_facets,
        correctness=correctness,
        attempt_type=draft.attempt_type,
        error_attributions=grade_attributions,
    )
    reliability = resolve_reliability(
        item,
        attempt_type=draft.attempt_type,
        hints_used=draft.hints_used,
        grader_confidence=grade.grader_confidence,
    )
    familiarity = familiarity_discount_from_attempts(
        prior_state.recent_learning_object_attempts,
        item,
        covered_facets=coverage.covered_facets,
        config=vault.config,
        exclude_attempt_id=attempt_id,
    )
    prior_quality = prior_state.practice_item_quality_state
    prior_bad_item_suspicion = prior_quality.bad_item_suspicion if prior_quality is not None else 0.0
    severity_traces: dict[str, dict[str, object]] = {}
    resolved_attributions: list[GradeAttribution] = []
    for attribution in grade_attributions:
        severity, trace = event_local_severity_from_attempts(
            vault,
            prior_state.recent_learning_object_attempts,
            item,
            error_type=attribution.error_type,
            attempt_type=draft.attempt_type,
            hints_used=draft.hints_used,
            correctness=correctness,
            expected_correctness=expected_correctness,
            effective_coverage=coverage.effective_coverage,
            covered_facets=coverage.covered_facets,
            facet_outcomes=facet_outcomes,
            prior_bad_item_suspicion=prior_bad_item_suspicion,
            base_severity=attribution.severity,
            exclude_attempt_id=attempt_id,
        )
        severity_traces[attribution.error_type] = trace
        resolved_attributions.append(replace(attribution, severity=severity))
    primary_error_type = _primary_error_type(resolved_attributions)
    max_event_severity = max((attribution.severity for attribution in resolved_attributions), default=0.0)
    error_impact = resolve_error_impact(
        vault.config,
        error_type=primary_error_type,
        max_event_severity=max_event_severity,
        effective_coverage=coverage.effective_coverage,
        observation_reliability=reliability.observation_reliability,
        independent_evidence_discount=familiarity.independent_evidence_discount,
    )
    mastery_observation = MasteryObservation(
        rubric_score=grade.rubric_score,
        max_points=rubric.max_points,
        evidence_coverage=coverage.effective_coverage,
        hint_dampening=1.0,
        grader_confidence=1.0,
        attempt_type=draft.attempt_type,
        observed_at=observed_at,
        item_coverage=coverage.item_coverage,
        effective_coverage=coverage.effective_coverage,
        covered_facets=coverage.covered_facets,
        facet_outcomes=facet_outcomes,
        independent_evidence_discount=familiarity.independent_evidence_discount,
        attempt_modifiers=coverage.trace["coverage_modifiers"],
        coverage_trace=coverage.trace,
        reliability_trace=reliability.trace,
        familiarity_trace=familiarity.trace,
        error_sharpening=error_impact.error_sharpening,
        observation_reliability=reliability.observation_reliability,
        observation_weight_override=error_impact.observation_weight,
    )
    # IRT (a, b) resolved once from static authored/LLM fields and shared by the
    # mastery EKF and the probability-space surprise (spec §4.3 / §8).
    posterior_mastery, mastery_trace = update_mastery_traced(
        prior_mastery,
        mastery_observation,
        vault.config.mastery,
        vault.config.algorithms.algorithm_version,
        item_a=item_a,
        item_b=item_b,
        item_id=item.id,
    )
    surprise = compute_surprise(
        prior=prior_mastery,
        posterior=posterior_mastery,
        observation=mastery_observation,
        observed_error_type=primary_error_type,
        prior_active_errors=prior_state.active_errors,
        config=vault.config,
        item_a=item_a,
        item_b=item_b,
    )

    previous_state = prior_state.practice_item_state
    fsrs_rating = _capped_rating(
        rating_from_score(grade.rubric_score, rubric.max_points),
        item,
        draft.hints_used,
    )
    elapsed_days = _elapsed_days(previous_state, observed_at)
    previous_memory = _memory_state(previous_state)
    next_memory = apply_review(previous_memory, fsrs_rating, elapsed_days)
    interval_days = interval_for_retention(next_memory.stability) * surprise.fsrs_interval_factor
    due_at = (observed_at + timedelta(days=interval_days)).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    attempt_record = {
        "id": attempt_id,
        "practice_item_id": item.id,
        "learning_object_id": learning_object.id,
        "subject": subject,
        "concept": learning_object.concept,
        "practice_mode": item.practice_mode,
        "attempt_type": draft.attempt_type,
        "learner_answer_md": draft.learner_answer_md,
        "evidence_facets": item.evidence_facets,
        "evidence_weights": item.evidence_weights,
        "rubric_score": grade.rubric_score,
        "correctness": correctness,
        "confidence": grade.confidence,
        "latency_seconds": draft.latency_seconds,
        "hints_used": draft.hints_used,
        "error_type": primary_error_type,
        "grader_confidence": grade.grader_confidence,
        "manual_review": grade.manual_review_reason is not None,
        "manual_review_reason": grade.manual_review_reason,
        "created_at": now_iso,
        "updated_at": now_iso,
        "session_id": draft.session_id,
    }
    error_event_ids = [
        error_event_ids_override[index]
        if error_event_ids_override is not None and index < len(error_event_ids_override)
        else new_ulid()
        for index, _attribution in enumerate(resolved_attributions)
    ]
    error_events = []
    for event_id, base_attribution, attribution in zip(error_event_ids, grade_attributions, resolved_attributions, strict=True):
        error_events.append(
            {
                "id": event_id,
                "attempt_id": attempt_id,
                "learning_object_id": learning_object.id,
                "error_type": attribution.error_type,
                "severity": attribution.severity,
                "is_misconception": attribution.is_misconception,
                "repair_plan": _error_event_repair_plan(vault, base_attribution),
                "status": "active",
                "created_at": now_iso,
                "updated_at": now_iso,
            }
        )
    facet_recall_updates = build_facet_recall_updates_from_prior(
        prior_state.facet_recall_by_scope(coverage.covered_facets, item.id),
        learning_object_id=learning_object.id,
        practice_item_id=item.id,
        covered_facets=coverage.covered_facets,
        facet_outcomes=facet_outcomes,
        independent_evidence_discount=familiarity.independent_evidence_discount,
        attempt_type=draft.attempt_type,
        error_event_written=bool(error_events),
        algorithm_version=vault.config.algorithms.algorithm_version,
        now_iso=now_iso,
    )
    recent_item_failures = sum(
        1
        for attempt in prior_state.recent_practice_item_attempts
        if attempt.get("id") != attempt_id
        if attempt.get("attempt_type") == "dont_know" or float(attempt.get("correctness") or 0.0) <= 0.40
    )
    quality_state = build_quality_state_update_from_prior(
        prior_state.practice_item_quality_state,
        recent_failures=recent_item_failures,
        item_id=item.id,
        prior_mastery=prior_mastery,
        correctness=correctness,
        grader_confidence=grade.grader_confidence,
        now_iso=now_iso,
        algorithm_version=vault.config.algorithms.algorithm_version,
    )
    ability_transition = estimate_ability_transition(
        item,
        correctness=correctness,
        attempt_type=draft.attempt_type,
        target_facets=list(coverage.covered_facets),
        error_event_written=bool(error_events),
    )
    ability_transition_event = {
        "attempt_id": attempt_id,
        "learning_object_id": learning_object.id,
        "practice_item_id": item.id,
        "transition_type": ability_transition["transition_type"],
        "expected_skill_gain": ability_transition["expected_skill_gain"],
        "target_facets": ability_transition["target_facets"],
        "reason": ability_transition["reason"],
        "applied_to_belief_counts": ability_transition["applied_to_belief_counts"],
        "applied_to_mastery": ability_transition["applied_to_mastery"],
        "applied_to_facet_recall": ability_transition["applied_to_facet_recall"],
        "process_noise": None,
        "algorithm_version": vault.config.algorithms.algorithm_version,
        "created_at": now_iso,
    }
    debug_payload = {
        "item_coverage": coverage.item_coverage,
        "effective_coverage": coverage.effective_coverage,
        "coverage_trace": coverage.trace,
        "reliability_trace": reliability.trace,
        "familiarity_trace": familiarity.trace,
        "error_impact_trace": error_impact.trace,
        "observation_weight": error_impact.observation_weight,
        "covered_facets": coverage.covered_facets,
        "facet_outcomes": facet_outcomes,
        "max_error_severity": max_event_severity,
        "primary_error_type": primary_error_type,
        "prior_bad_item_suspicion": prior_bad_item_suspicion,
        "bad_item_suspicion": quality_state["bad_item_suspicion"],
        "severity_traces": severity_traces,
        "predicted_correctness": expected_correctness,
        "prediction_trace": prediction_trace,
        "facet_recall_updates": facet_recall_updates,
        "ability_transition": ability_transition,
        "algorithm_version": vault.config.algorithms.algorithm_version,
        "created_at": now_iso,
    }
    practice_state = PracticeItemState(
        practice_item_id=item.id,
        difficulty=next_memory.difficulty,
        stability=next_memory.stability,
        retrievability=next_memory.retrievability,
        due_at=due_at,
        active=True,
        content_hash=practice_item_hash(item),
        last_attempt_at=now_iso,
        updated_at=now_iso,
    )
    surprise_record = surprise.as_record(attempt_id, vault.config.algorithms.algorithm_version, now_iso)
    mastery_display = display_mastery(posterior_mastery)
    result = AttemptResult(
        attempt_id=attempt_id,
        practice_item_id=item.id,
        learning_object_id=learning_object.id,
        rubric_score=grade.rubric_score,
        correctness=correctness,
        grader_confidence=grade.grader_confidence,
        manual_review_reason=grade.manual_review_reason,
        fsrs_rating=fsrs_rating.name.lower(),
        due_at=due_at,
        mastery_mean=mastery_display.mastery_mean,
        mastery_variance=mastery_display.mastery_variance,
        surprise_direction=surprise.surprise_direction,
        predictive_surprise=surprise.predictive_surprise,
        bayesian_surprise=surprise.bayesian_surprise,
        error_event_ids=error_event_ids,
        feedback_md=grade.feedback_md,
        repair_suggestions=list(grade.repair_suggestions),
        fatal_errors=list(grade.fatal_errors),
        mastery_trace=mastery_trace,
        debug_payload=debug_payload,
    )
    return AttemptApplication(
        attempt_record=attempt_record,
        evidence_rows=grade.evidence_rows,
        error_events=error_events,
        surprise_record=surprise_record,
        practice_item_state=practice_state,
        mastery_state=posterior_mastery,
        facet_recall_states=facet_recall_updates,
        quality_state=quality_state,
        ability_transition=ability_transition_event,
        attempt_debug_payload=debug_payload,
        result=result,
    )


def _self_grade_attributions(
    vault: LoadedVault,
    fatal_errors: list[str],
    error_type: str | None,
    error_attributions: list[SelfGradeErrorAttribution] | None = None,
) -> list[GradeAttribution]:
    """Resolve the learner's self-grade selections into the same flat
    ``GradeAttribution`` list Codex grading produces.

    Sources are merged in priority order — rubric fatal errors, the legacy single
    ``error_type``, then the per-criterion picks — and de-duplicated by error type.
    Severity and misconception status come from the vault taxonomy (falling back to
    neutral defaults for unknown types, as elsewhere). When the learner tied an
    error to specific rubric criteria, those ids are recorded in the attribution
    ``evidence`` so the provenance mirrors a Codex grader's per-error note.
    """

    criteria_by_error: dict[str, list[str]] = {}
    order: list[str] = []

    def _register(selected_error_type: str | None, criterion_id: str | None) -> None:
        if not selected_error_type:
            return
        if selected_error_type not in criteria_by_error:
            criteria_by_error[selected_error_type] = []
            order.append(selected_error_type)
        if criterion_id and criterion_id not in criteria_by_error[selected_error_type]:
            criteria_by_error[selected_error_type].append(criterion_id)

    for fatal_error in fatal_errors:
        _register(fatal_error, None)
    _register(error_type, None)
    for attribution in error_attributions or []:
        _register(attribution.error_type, attribution.criterion_id)

    resolved: list[GradeAttribution] = []
    for selected_error_type in order:
        criteria = criteria_by_error[selected_error_type]
        evidence = (
            f"Self-attributed on criterion {', '.join(criteria)}." if criteria else None
        )
        resolved.append(
            GradeAttribution(
                error_type=selected_error_type,
                severity=_error_severity(vault, selected_error_type),
                is_misconception=_is_misconception(vault, selected_error_type),
                evidence=evidence,
            )
        )
    return resolved


def _canonicalized_grade_attributions(
    vault: LoadedVault,
    attributions: list[GradeAttribution],
) -> list[GradeAttribution]:
    if not vault.facet_aliases:
        return attributions
    canonicalized: list[GradeAttribution] = []
    for attribution in attributions:
        target_evidence_families = list(
            dict.fromkeys(vault.canonical_facet_id(facet) for facet in attribution.target_evidence_families)
        )
        canonicalized.append(replace(attribution, target_evidence_families=target_evidence_families))
    return canonicalized


def _primary_error_type(attributions: list[GradeAttribution]) -> str | None:
    if not attributions:
        return None
    return max(attributions, key=lambda attribution: attribution.severity).error_type


def _attempt_manual_review_reason(existing: str | None, draft: AttemptDraft) -> str | None:
    if existing is not None:
        return existing
    if draft.attempt_type != "dont_know" and not draft.learner_answer_md.strip():
        return "blank_answer"
    return None


def _dont_know_error_type(hints_used: int) -> str:
    return SCAFFOLD_FAILURE_ERROR_TYPE if hints_used > 0 else DONT_KNOW_ERROR_TYPE


def _error_event_repair_plan(vault: LoadedVault, attribution: GradeAttribution) -> dict[str, object] | None:
    repair_plan: dict[str, object] = {}
    if attribution.evidence:
        repair_plan["evidence"] = attribution.evidence
    if attribution.target_evidence_families:
        repair_plan["target_evidence_families"] = list(attribution.target_evidence_families)
    if attribution.target_criterion_ids:
        repair_plan["target_criterion_ids"] = list(attribution.target_criterion_ids)
    if abs(attribution.severity - _error_severity(vault, attribution.error_type)) > 1e-9:
        repair_plan["base_severity"] = attribution.severity
    return repair_plan or None


def _replay_error_attributions(
    vault: LoadedVault,
    error_type: str | None,
    *,
    error_events: list[dict[str, Any]] | None = None,
) -> list[GradeAttribution]:
    if error_events:
        attributions: list[GradeAttribution] = []
        for event in error_events:
            event_error_type = event.get("error_type")
            if not event_error_type:
                continue
            repair_plan = event.get("repair_plan")
            if not isinstance(repair_plan, dict):
                repair_plan = {}
            raw_targets = repair_plan.get("target_evidence_families")
            target_evidence_families = raw_targets if isinstance(raw_targets, list) else []
            raw_criteria = repair_plan.get("target_criterion_ids")
            target_criterion_ids = raw_criteria if isinstance(raw_criteria, list) else []
            base_severity = repair_plan.get("base_severity")
            attributions.append(
                GradeAttribution(
                    error_type=str(event_error_type),
                    severity=float(base_severity) if isinstance(base_severity, (int, float)) else _error_severity(vault, str(event_error_type)),
                    evidence=repair_plan.get("evidence") if isinstance(repair_plan.get("evidence"), str) else None,
                    is_misconception=bool(event.get("is_misconception", _is_misconception(vault, str(event_error_type)))),
                    target_evidence_families=[str(facet) for facet in target_evidence_families],
                    target_criterion_ids=[str(criterion_id) for criterion_id in target_criterion_ids],
                )
            )
        if attributions:
            return attributions
    if not error_type:
        return []
    return [
        GradeAttribution(
            error_type=error_type,
            severity=_error_severity(vault, error_type),
            evidence=None,
            is_misconception=_is_misconception(vault, error_type),
        )
    ]


def _resolved_codex_grade(
    validated: ValidatedCodexGrade,
    *,
    agent_run_id: str | None,
    clock: Clock | None,
    manual_review_reason: str | None = None,
) -> ResolvedGrade:
    now_iso = utc_now_iso(clock)
    criterion_points = {evidence.criterion_id: evidence.points_awarded for evidence in validated.criterion_evidence}
    evidence_rows = [
        {
            "id": new_ulid(),
            "criterion_id": evidence.criterion_id,
            "points_awarded": evidence.points_awarded,
            "evidence": evidence.evidence,
            "notes": evidence.notes,
            "agent_run_id": agent_run_id,
            "local_grader_id": None,
            "grader_tier": 3,
            "created_at": now_iso,
        }
        for evidence in validated.criterion_evidence
    ]
    return ResolvedGrade(
        rubric_score=validated.rubric_score,
        criterion_points=criterion_points,
        evidence_rows=evidence_rows,
        error_attributions=[
            GradeAttribution(
                error_type=attribution.error_type,
                severity=attribution.severity,
                evidence=attribution.evidence,
                is_misconception=attribution.is_misconception,
                target_evidence_families=list(attribution.target_evidence_families or []),
                target_criterion_ids=list(attribution.target_criterion_ids or []),
            )
            for attribution in validated.error_attributions
        ],
        grader_confidence=validated.grader_confidence,
        confidence=None,
        manual_review_reason=manual_review_reason if manual_review_reason is not None else validated.manual_review_reason,
        feedback_md=validated.feedback_md,
        repair_suggestions=list(validated.repair_suggestions or []),
        fatal_errors=list(validated.fatal_errors),
    )


def _validated_criterion_points(rubric: Rubric, points: dict[str, float]) -> dict[str, float]:
    criteria = {criterion.id: criterion for criterion in rubric.criteria}
    unknown = sorted(set(points) - set(criteria))
    if unknown:
        raise AttemptValidationError(f"Unknown rubric criteria: {', '.join(unknown)}")
    validated: dict[str, float] = {}
    for criterion in rubric.criteria:
        value = float(points.get(criterion.id, 0.0))
        if value < 0:
            raise AttemptValidationError(f"{criterion.id} points cannot be negative")
        if value > criterion.points:
            raise AttemptValidationError(f"{criterion.id} points exceed max {criterion.points:g}")
        validated[criterion.id] = value
    return validated


def _validated_self_grade_attributions(
    rubric: Rubric, attributions: list[SelfGradeErrorAttribution] | None
) -> list[SelfGradeErrorAttribution]:
    """Validate per-criterion self-grade error picks before they are resolved.

    Only the ``criterion_id`` link is checked (it must name a real rubric
    criterion); the ``error_type`` is intentionally left open — like Codex
    attributions, an unknown type resolves to neutral taxonomy defaults rather
    than failing the attempt.
    """

    if not attributions:
        return []
    known_criteria = {criterion.id for criterion in rubric.criteria}
    for attribution in attributions:
        if not attribution.error_type:
            raise AttemptValidationError("error attribution requires an error_type")
        if attribution.criterion_id is not None and attribution.criterion_id not in known_criteria:
            raise AttemptValidationError(
                f"Unknown rubric criterion {attribution.criterion_id} in error attribution"
            )
    return list(attributions)


def _validate_fatal_errors(rubric: Rubric, fatal_errors: list[str]) -> None:
    known = {fatal_error.id for fatal_error in rubric.fatal_errors}
    unknown = sorted(set(fatal_errors) - known)
    if unknown:
        raise AttemptValidationError(f"Unknown fatal errors: {', '.join(unknown)}")


def _rubric_score(rubric: Rubric, criterion_points: dict[str, float], fatal_errors: list[str]) -> int:
    score = int(round(sum(criterion_points.values())))
    score = max(0, min(int(rubric.max_points), score, 4))
    fatal_by_id = {fatal_error.id: fatal_error for fatal_error in rubric.fatal_errors}
    for fatal_error_id in fatal_errors:
        score = min(score, fatal_by_id[fatal_error_id].max_grade)
    return max(0, min(score, 4))


def _evidence_coverage(item: PracticeItem, criterion_points: dict[str, float]) -> float:
    return evidence_coverage(item, criterion_points)


def _hint_dampening(item: PracticeItem, hints_used: int) -> float:
    value = _hint_policy_value(item.hint_policy.mastery_alpha_dampening_by_hint, hints_used)
    return float(value) if value is not None else 1.0


def _capped_rating(rating: Rating, item: PracticeItem, hints_used: int) -> Rating:
    cap_value = _hint_policy_value(item.hint_policy.fsrs_rating_cap_by_hint, hints_used)
    if cap_value is None:
        return rating
    cap = _rating_from_cap(cap_value)
    return Rating(min(int(rating), int(cap)))


def _hint_policy_value(mapping: dict[int | str, object], hints_used: int) -> object | None:
    if hints_used in mapping:
        return mapping[hints_used]
    string_key = str(hints_used)
    if string_key in mapping:
        return mapping[string_key]
    numeric_keys: list[int] = []
    for key in mapping:
        try:
            numeric_keys.append(int(key))
        except (TypeError, ValueError):
            continue
    eligible = [key for key in numeric_keys if key <= hints_used]
    if not eligible:
        return None
    return mapping.get(max(eligible)) or mapping.get(str(max(eligible)))


def _rating_from_cap(value: object) -> Rating:
    if isinstance(value, int):
        return Rating(max(1, min(4, value)))
    normalized = str(value).strip().lower()
    names = {
        "again": Rating.AGAIN,
        "hard": Rating.HARD,
        "good": Rating.GOOD,
        "easy": Rating.EASY,
        "1": Rating.AGAIN,
        "2": Rating.HARD,
        "3": Rating.GOOD,
        "4": Rating.EASY,
    }
    if normalized not in names:
        raise AttemptValidationError(f"Unknown FSRS rating cap {value!r}")
    return names[normalized]


def _memory_state(state: PracticeItemState | None) -> MemoryState | None:
    if state is None or state.difficulty is None or state.stability is None:
        return None
    retrievability = state.retrievability if state.retrievability is not None else 1.0
    return MemoryState(
        difficulty=state.difficulty,
        stability=state.stability,
        retrievability=retrievability,
    )


def _elapsed_days(state: PracticeItemState | None, observed_at) -> float:
    if state is None:
        return 0.0
    last_attempt_at = parse_utc(state.last_attempt_at)
    if last_attempt_at is None:
        return 0.0
    return max(0.0, (observed_at - last_attempt_at).total_seconds() / 86400)


def _error_severity(vault: LoadedVault, error_type: str) -> float:
    taxonomy = vault.error_types.get(error_type)
    return taxonomy.severity_default if taxonomy is not None else 0.5


def _is_misconception(vault: LoadedVault, error_type: str) -> bool:
    taxonomy = vault.error_types.get(error_type)
    return taxonomy.is_misconception if taxonomy is not None else False

from __future__ import annotations

import json
import logging
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
    FacetUncertaintyState,
    ItemParameterState,
    MasteryState,
    PracticeItemQualityState,
    PracticeItemState,
    Repository,
)
from learnloop.ids import new_ulid
from learnloop.services.fitted_params import resolve_fsrs_weights
from learnloop.services.fsrs import (
    FSRS6_DEFAULT_WEIGHTS,
    MemoryState,
    Rating,
    apply_review,
    interval_for_retention,
    rating_from_score,
)
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
from learnloop.services.error_taxonomy_map import map_legacy_error_type
from learnloop.services.facet_diagnostics import (
    apply_mastery_variance_floor,
    build_facet_uncertainty_updates,
    covered_required_fraction,
    lo_relative_coverage,
)
from learnloop.services.mastery import (
    MasteryObservation,
    MasteryObservationTrace,
    display_mastery,
    initial_mastery_state_for_learning_object,
    item_irt_params,
    resolve_item_irt_params,
    update_item_difficulty,
    update_mastery_traced,
)
from learnloop.services.evidence import attempt_evidence_mass
from learnloop.services.assessment_contracts import (
    CANONICAL_STATE_VERSIONS,
    KM_ALGORITHM_VERSION,
    P0_ALGORITHM_VERSION,
)
from learnloop.services.facet_state_reader import (
    CanonicalFacetStateReader,
    is_canonical_state_vault,
)
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
    scale_coverage_for_graded_criteria,
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
    # Retry launched from the feedback screen's source-review panel: the
    # canonical source was just re-read, so the mastery update applies an IRT
    # easiness shift and the attempt does not advance last_evidence_at.
    primed: bool = False
    # Probe redesign §5.1: the committed presentation this submission consumes.
    # Required for qualifying diagnostic observations; an invalid or already
    # consumed reference downgrades the attempt to incidental evidence.
    probe_presentation_id: str | None = None
    # Probe redesign §7.1: the learner's committed answer confidence (1-5).
    # Logged-only observation feature — never consumed by grading or scheduling.
    answer_confidence: int | None = None
    # Immutable item/rubric contract captured when the item was presented. UI
    # callers round-trip this opaque id; non-interactive callers snapshot at the
    # attempt boundary as a compatibility fallback.
    assessment_contract_version_id: str | None = None
    # Client-generated retry identity. Persisted on the attempt under a unique
    # index so one submission cannot create two formal attempts.
    submission_id: str | None = None
    # A diagnostic presentation keeps its measurement attempt type while this
    # flag records the learner's explicit "I don't know" outcome.
    declared_dont_know: bool = False


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
    # spec §2.1: structured belief captured by the grader; persisted on the
    # error event so the registry (Phase 2) and replay can read it losslessly.
    misconception_statement: str | None = None
    misconception_consistent_answer: str | None = None
    # spec §2.2: registry link written by normalization after persistence; carried
    # through replay (from the persisted error event) so the link survives rebuilds.
    misconception_id: str | None = None
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
    # §5.7 block-end hook payload when this attempt closed a diagnostic block:
    # released feedback, open-set/completion outcome, and the route.
    probe_block_end: dict[str, Any] | None = None

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
            "probe_block_end": self.probe_block_end,
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
    # Probe redesign §5.8: the grading provider that produced this grade.
    # Qualifying diagnostic observations require an approved provider; a
    # self-graded submission can never advance an episode.
    grading_source: str = "self"


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
    facet_uncertainty: dict[str, FacetUncertaintyState | None]
    item_parameter_state: ItemParameterState | None = None

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
    facet_uncertainty_states: list[dict[str, Any]]
    quality_state: dict[str, Any]
    ability_transition: dict[str, Any]
    attempt_debug_payload: dict[str, object]
    result: AttemptResult
    item_parameter_state: ItemParameterState | None = None


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
    item, _learning_object, rubric = _resolve_attempt_target(vault, repository, draft)
    contract = _assessment_contract(repository, draft)
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
        rubric=rubric,
        assessment_contract=contract,
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

    item, _learning_object, rubric = _resolve_attempt_target(vault, repository, draft)
    contract = _assessment_contract(repository, draft)
    attempt_id = new_ulid()
    context = build_grading_context(
        vault,
        item,
        attempt_id=attempt_id,
        learner_answer_md=draft.learner_answer_md,
        rubric=rubric,
        assessment_contract=contract,
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
    item, _learning_object, rubric = _resolve_attempt_target(vault, repository, draft)
    grader_confidence = confidence_to_grader_confidence(grade.confidence)
    manual_review_reason = "low_self_confidence" if grader_confidence < 0.4 else None
    manual_review_reason = _attempt_manual_review_reason(manual_review_reason, draft)
    criterion_points = _validated_criterion_points(rubric, grade.criterion_points)
    fatal_errors = grade.fatal_errors or []
    _validate_fatal_errors(rubric, fatal_errors)
    attribution_error_type = grade.error_type
    per_criterion_attributions = _validated_self_grade_attributions(rubric, grade.error_attributions)
    if draft.attempt_type == "dont_know" or draft.declared_dont_know:
        criterion_points = {criterion.id: 0.0 for criterion in rubric.criteria}
        fatal_errors = []
        per_criterion_attributions = []
        # A don't-know is deterministically attributed to recall_failure so it
        # writes an error event and feeds surprise / cross-LO propagation through
        # the standard pipeline (spec §"Attempt-type handling").
        attribution_error_type = _dont_know_error_type(vault, draft.hints_used)
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
            "learner_confidence": "hedged" if grade.confidence <= 2 else "confident",
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
    if draft.attempt_type != "dont_know" and not draft.declared_dont_know:
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
    item, _learning_object, rubric = _resolve_attempt_target(vault, repository, draft)
    expected_attempt_id = attempt_id or proposal.attempt_id
    try:
        validated = validate_codex_grading_proposal(
            proposal,
            attempt_id=expected_attempt_id,
            item=item,
            vault=vault,
            learner_answer_md=draft.learner_answer_md,
            rubric=rubric,
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
            grading_source=grading_source,
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
        probe_presentation_id=attempt.get("probe_presentation_id"),
        answer_confidence=attempt.get("answer_confidence"),
        assessment_contract_version_id=next(
            (
                row.assessment_contract_version_id
                for row in evidence
                if row.assessment_contract_version_id is not None
            ),
            None,
        ),
        submission_id=attempt.get("submission_id"),
        declared_dont_know=bool(attempt.get("declared_dont_know")),
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


def _assessment_contract(
    repository: Repository, draft: AttemptDraft
) -> dict[str, Any] | None:
    if draft.assessment_contract_version_id is None:
        return None
    stored = repository.fetch_assessment_contract_version(
        draft.assessment_contract_version_id
    )
    if stored is None or stored.get("practice_item_id") != draft.practice_item_id:
        raise AttemptValidationError(
            "assessment contract is missing or does not belong to the presented item"
        )
    return stored.get("contract") or {}


def _resolve_attempt_target(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    *,
    replay: bool = False,
    clock: Clock | None = None,
):
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
    # "exam_evidence" is likewise exempt: it is an import path (exam seeding),
    # not a learner-chosen mode, and replay must be able to re-apply seeded
    # attempts on items that only list live attempt types.
    # "teach_back" is implied by the item's practice mode: the conversation
    # service records it on teach_back items regardless of the authored
    # attempt_types_allowed list. At replay time the exemption is unconditional
    # on the attempt_type — an attempt that was valid when recorded must always
    # replay, even after the item was edited to another practice mode.
    # "exam_attempt" is a held-out practice-exam answer applied at exam finish.
    # The pooled item is a regular practice item that only lists its live
    # attempt types, so the exam attempt type is exempt (like exam_evidence).
    # "self_report" is a mode-agnostic learner self-assessment (e.g. the
    # rung-variant request evidence write) — it never depends on the item's
    # live attempt-type list, so it is exempt like the other recording types.
    exempt_attempt_types = {"dont_know", "exam_evidence", "exam_attempt", "self_report"}
    if draft.attempt_type == "teach_back" and (replay or item.practice_mode == "teach_back"):
        exempt_attempt_types.add("teach_back")
    # Probe redesign §12: an active diagnostic episode forces the recording
    # attempt type to diagnostic_probe on whatever item was committed, so the
    # type is exempt whenever the submission consumes a presentation (and at
    # replay, where a recorded attempt must always re-apply).
    if draft.attempt_type == "diagnostic_probe" and (replay or draft.probe_presentation_id is not None):
        exempt_attempt_types.add("diagnostic_probe")
    if (
        item.attempt_types_allowed
        and draft.attempt_type not in exempt_attempt_types
        and draft.attempt_type not in item.attempt_types_allowed
    ):
        raise AttemptValidationError(f"{draft.attempt_type} is not allowed for {item.id}")
    try:
        contract = _assessment_contract(repository, draft)
        if contract is not None:
            from learnloop.services.assessment_contracts import rubric_from_contract

            rubric = rubric_from_contract(contract)
        else:
            rubric = resolved_rubric(vault, item)
    except GradingValidationError as exc:
        raise AttemptValidationError(str(exc)) from exc
    if draft.hints_used < 0:
        raise AttemptValidationError("hints_used must be non-negative")
    if draft.latency_seconds is not None and draft.latency_seconds < 0:
        raise AttemptValidationError("latency_seconds must be non-negative")
    if draft.answer_confidence is not None and not 1 <= draft.answer_confidence <= 5:
        raise AttemptValidationError("answer_confidence must be between 1 and 5")
    if not replay:
        cold_task = repository.active_followup_task_for_item(
            draft.practice_item_id, at=utc_now_iso(clock)
        )
        if cold_task is not None and cold_task.get("kind") == "cold_retry":
            if draft.primed or draft.hints_used > 0 or draft.attempt_type == "hinted_attempt":
                raise AttemptValidationError("a cold retry must be unassisted and unprimed")
    return item, learning_object, rubric


def _dual_write_grade_channel(
    vault: LoadedVault,
    repository: Repository,
    attempt: ApplyAttemptInput,
    application: "AttemptApplication",
    *,
    clock: Clock | None = None,
) -> None:
    """P0.2 dual-write (spec_p0_measurement_correctness §4.1, §7.2): append a raw
    grade event + calibrated interpretation alongside the legacy attempt summary.

    Fail-safe: never raises into the legacy path (§7.3). Ordinary practice attempts
    only -- diagnostic-probe attempts (record_probe_update) and exam attempts are
    dual-written by their own entry points (probe_episodes / exam_session)."""

    try:
        attempt_type = attempt.draft.attempt_type
        # Diagnostic-probe attempts are dual-written by the probe-episode path when
        # they carry a presentation; exam attempts by exam_session. Everything else
        # routed through apply_attempt is an ordinary practice attempt.
        if attempt_type == "diagnostic_probe" or "exam" in attempt_type:
            return
        item = vault.practice_items.get(attempt.draft.practice_item_id)
        if item is None:
            return
        grade = attempt.grade
        rubric = vault.rubric_for_item(item)
        max_points = rubric.max_points if rubric is not None else 4
        criterion_max = (
            {c.id: c.points for c in rubric.criteria} if rubric is not None else None
        )
        from learnloop.services.grade_resolution import record_grade_dual_write

        record_grade_dual_write(
            vault,
            repository,
            item=item,
            purpose="practice",
            grading_source=attempt.grading_source or application.result.grading_source,
            attempt_id=application.result.attempt_id,
            response_text=attempt.draft.learner_answer_md,
            rubric_score=grade.rubric_score,
            max_points=max_points,
            grader_confidence=grade.grader_confidence,
            has_fatal=bool(grade.fatal_errors),
            signature_matched=any(
                getattr(a, "is_misconception", False)
                for a in (grade.error_attributions or [])
            ),
            criterion_points=grade.criterion_points,
            criterion_max=criterion_max,
            agent_run_id=application.result.agent_run_id,
            domain=application.result.learning_object_id,
            clock=clock,
        )
    except Exception:  # noqa: BLE001 - fail-safe dual-write (§7.3)
        # record_grade_dual_write anchors its own degradation telemetry; this outer
        # guard only catches failures BEFORE it is reached (item/rubric lookup).
        # Never silent: degradation is visible, recoverable debt (audit B2).
        logging.getLogger(__name__).warning(
            "grade dual-write channel degraded before resolution for attempt %s",
            getattr(getattr(attempt, "draft", None), "practice_item_id", None),
            exc_info=True,
        )


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

    # Reading-signal firewall (§8.2, design §C.2): the evidence-ingestion chokepoint
    # hard-rejects any input carrying salience-only authority. Reading is never
    # evidence -- a salience signal can never reach the belief pipeline.
    from learnloop.services.salience_firewall import reject_salience

    reject_salience(attempt, context="apply_attempt")

    application = compute_attempt_application(vault, repository, attempt, clock=clock)
    application = _validate_probe_presentation(repository, application, attempt, clock=clock)
    _stamp_observation_lineage(vault, repository, application, attempt, clock=clock)
    # KM2b item 2: under mvp-0.7 the canonical projection is the only facet-state
    # write mechanism; the legacy per-LO recall/uncertainty bridge is retired.
    _persist_attempt_application(
        repository,
        application,
        replace_existing=attempt.replace_existing,
        write_legacy_facet_state=not is_canonical_state_vault(vault),
    )
    _dual_write_grade_channel(vault, repository, attempt, application, clock=clock)

    from learnloop.services.remediation import record_remediation_attempt

    record_remediation_attempt(repository, application.attempt_record, clock=clock)
    _auto_resolve_clean_error_events(vault, repository, application, clock=clock)
    _project_canonical_belief(vault, repository, clock=clock)
    if attempt.record_probe_update:
        # Probe redesign Checkpoint 0/1: episode accounting replaces the legacy
        # lo_probe_state advancement (`record_probe_attempt` is frozen for
        # pre-redesign replay only). Belief updates and episode advancement are
        # separated inside `record_episode_evidence`.
        from learnloop.services.probe_episodes import record_episode_evidence

        grading_source = (
            "deterministic"
            if attempt.draft.attempt_type == "dont_know" or attempt.draft.declared_dont_know
            else attempt.grading_source
        )
        block_end = record_episode_evidence(
            vault,
            repository,
            learning_object_id=application.result.learning_object_id,
            attempt_id=application.result.attempt_id,
            practice_item_id=attempt.draft.practice_item_id,
            attempt_type=attempt.draft.attempt_type,
            hints_used=attempt.draft.hints_used,
            probe_presentation_id=application.attempt_record.get("probe_presentation_id"),
            grading_source=grading_source,
            clock=clock,
        )
        if block_end is not None:
            return replace(application.result, probe_block_end=block_end)
    return application.result


def _project_canonical_belief(
    vault: LoadedVault, repository: Repository, *, clock: Clock | None = None
) -> None:
    """Recompute the canonical shared belief cache after an attempt (mvp-0.7).

    A no-op on legacy vaults (the projection early-returns), so mvp-0.6 replay is
    byte-identical. The recompute is a deterministic fold over the immutable
    observation ledger, so live state and replayed state coincide by construction.
    """

    if vault.config.algorithms.algorithm_version not in CANONICAL_STATE_VERSIONS:
        return
    from learnloop.services.canonical_projection import project_canonical_facet_state

    project_canonical_facet_state(vault, repository, clock=clock)


def _validate_probe_presentation(
    repository: Repository,
    application: AttemptApplication,
    attempt: ApplyAttemptInput,
    *,
    clock: Clock | None = None,
) -> AttemptApplication:
    """Pre-persist §5.4 validation: an invalid, mismatched, ended, or already
    consumed presentation reference is stripped so the attempt records as
    incidental evidence (and the unique presentation index never rejects the
    row). A retried submission of the same attempt keeps its link (idempotent)."""

    presentation_id = application.attempt_record.get("probe_presentation_id")
    if not presentation_id:
        return application
    from learnloop.services.probe_episodes import validate_presentation_for_submission

    validation = validate_presentation_for_submission(
        repository,
        str(presentation_id),
        practice_item_id=attempt.draft.practice_item_id,
        attempt_id=attempt.attempt_id,
        clock=clock,
    )
    if validation.valid:
        return application
    stripped = dict(application.attempt_record)
    stripped["probe_presentation_id"] = None
    return replace(application, attempt_record=stripped)


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
        replay=attempt.replace_existing,
    )


def _stamp_observation_lineage(
    vault: LoadedVault,
    repository: Repository,
    application: AttemptApplication,
    attempt: ApplyAttemptInput,
    *,
    clock: Clock | None = None,
) -> None:
    """Snapshot the assessment contract and stamp observation ids (KM §5.2).

    Only runs on mvp-0.7 vaults, and only for freshly recorded grading evidence
    (not the replace/replay path, which reuses stored rows). Legacy vaults skip
    this entirely, so mvp-0.6 replay reproduces byte-identical derived state.
    """

    from learnloop.services.assessment_contracts import (
        KM_ALGORITHM_VERSION,
        snapshot_for_presentation,
    )

    if vault.config.algorithms.algorithm_version not in CANONICAL_STATE_VERSIONS:
        return
    if attempt.replace_existing or not application.evidence_rows:
        return
    item = vault.practice_items.get(attempt.draft.practice_item_id)
    if item is None:
        return
    version_id = attempt.draft.assessment_contract_version_id
    if version_id is not None:
        stored = repository.fetch_assessment_contract_version(version_id)
        if (
            stored is None
            or stored.get("practice_item_id") != item.id
        ):
            raise AttemptValidationError(
                "assessment contract is missing or does not belong to the presented item"
            )
    else:
        version_id = snapshot_for_presentation(repository, vault, item, clock=clock)
    stored = repository.fetch_assessment_contract_version(version_id)
    contract = stored.get("contract") if stored is not None else {}
    criteria = {
        str(criterion.get("id")): criterion
        for criterion in contract.get("criteria") or []
    }
    attempt_id = application.result.attempt_id
    revision = 0
    for row in application.evidence_rows:
        criterion_id = row.get("criterion_id")
        if criterion_id is None:
            continue
        row.setdefault("assessment_contract_version_id", version_id)
        row.setdefault("grading_revision", revision)
        row.setdefault("observation_id", f"{attempt_id}:{criterion_id}:{revision}")
        if row.get("correlation_group") is None:
            historical = criteria.get(str(criterion_id)) or {}
            row["correlation_group"] = historical.get("correlation_group")
            if row["correlation_group"] is None:
                row["correlation_group"] = _criterion_correlation_group(item, str(criterion_id))
        if row.get("attribution_json") is None:
            criterion = criteria.get(str(criterion_id)) or {}
            targets = criterion.get("targets") or []
            target_keys = {
                (str(target.get("facet") or ""), str(target.get("capability") or ""))
                for target in targets
            }
            selected: set[tuple[str, str]] = set()
            for attribution in attempt.grade.error_attributions:
                if (
                    attribution.target_criterion_ids
                    and str(criterion_id) not in attribution.target_criterion_ids
                ):
                    continue
                for facet in attribution.target_evidence_families:
                    selected.update(key for key in target_keys if key[0] == facet)
            if selected:
                weight = 1.0 / len(selected)
                row["attribution_json"] = json.dumps(
                    {
                        "targets": [
                            {"facet": facet, "capability": capability, "weight": weight}
                            for facet, capability in sorted(selected)
                        ]
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )


def _criterion_correlation_group(item: PracticeItem, criterion_id: str) -> str | None:
    rubric = item.grading_rubric
    if rubric is None:
        return None
    for criterion in rubric.criteria:
        if criterion.id == criterion_id:
            return criterion.correlation_group
    return None


def _persist_attempt_application(
    repository: Repository,
    application: AttemptApplication,
    *,
    replace_existing: bool,
    write_legacy_facet_state: bool = True,
) -> None:
    # mvp-0.7 retires the legacy per-LO facet-state bridge: the derived updates
    # are still computed (surprise/breadth/debug read them in memory) but never
    # persisted — the canonical projection owns that state. The empty iterables
    # also keep the repository hard-stop guard from ever tripping in normal flow.
    facet_recall_states = application.facet_recall_states if write_legacy_facet_state else ()
    facet_uncertainty_states = (
        application.facet_uncertainty_states if write_legacy_facet_state else ()
    )
    if replace_existing:
        repository.replace_attempt_derived_outcome(
            attempt=application.attempt_record,
            error_events=application.error_events,
            surprise=application.surprise_record,
            practice_item_state=application.practice_item_state,
            mastery_state=application.mastery_state,
            facet_recall_states=facet_recall_states,
            facet_uncertainty_states=facet_uncertainty_states,
            quality_state=application.quality_state,
            ability_transition=application.ability_transition,
            attempt_debug_payload=application.attempt_debug_payload,
            item_parameter_state=application.item_parameter_state,
        )
    else:
        repository.record_attempt_outcome(
            attempt=application.attempt_record,
            evidence_rows=application.evidence_rows,
            error_events=application.error_events,
            surprise=application.surprise_record,
            practice_item_state=application.practice_item_state,
            mastery_state=application.mastery_state,
            facet_recall_states=facet_recall_states,
            facet_uncertainty_states=facet_uncertainty_states,
            quality_state=application.quality_state,
            ability_transition=application.ability_transition,
            attempt_debug_payload=application.attempt_debug_payload,
            item_parameter_state=application.item_parameter_state,
        )


def _auto_resolve_clean_error_events(
    vault: LoadedVault,
    repository: Repository,
    application: AttemptApplication,
    *,
    clock: Clock | None = None,
) -> list[str]:
    """Close the loop on stale error events (config ``[misconceptions]``).

    A "clean" attempt is one whose graded correctness is at or above
    ``auto_resolve_min_correctness``, that wrote no error events (equivalently
    ``error_type IS NULL`` on the attempt row), and that is not a
    ``dont_know``/``skip`` self-diagnosis. When an attempt completes clean, any
    active error event on the same learning object that has accumulated
    ``auto_resolve_clean_attempts`` clean attempts since its ``created_at`` is
    resolved. The hook runs inside ``apply_attempt`` after persistence, so live
    recording and deterministic replay (which resets error events to active and
    re-applies attempts in ``created_at`` order) reproduce the same resolutions.
    """

    config = vault.config.misconceptions
    if config.auto_resolve_clean_attempts <= 0:
        return []
    record = application.attempt_record
    if record.get("attempt_type") in ("dont_know", "skip"):
        return []
    if application.error_events:
        return []
    if float(record.get("correctness") or 0.0) < config.auto_resolve_min_correctness:
        return []
    resolved: list[str] = []
    for event in repository.active_errors_by_learning_object(record["learning_object_id"]):
        clean_count = repository.count_clean_attempts_since(
            record["learning_object_id"],
            since=event.created_at,
            until=record["created_at"],
            min_correctness=config.auto_resolve_min_correctness,
        )
        if clean_count >= config.auto_resolve_clean_attempts and repository.resolve_error_event(
            event.id, clock=clock
        ):
            resolved.append(event.id)
    return resolved


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
    # KM2b: the belief priors this attempt reads come from the canonical shared
    # state under mvp-0.7 (folded through aliases + merges) and from the legacy
    # per-LO table under mvp-0.6 (byte-identical). One reader build per attempt.
    if is_canonical_state_vault(vault):
        reader = CanonicalFacetStateReader(vault, repository)

        def _recall(facet: str, scope: str | None = None) -> FacetRecallState | None:
            return reader.state_for_facet(learning_object_id, facet, scope)

    else:

        def _recall(facet: str, scope: str | None = None) -> FacetRecallState | None:
            return repository.facet_recall_state(learning_object_id, facet, scope)

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
        aggregate_facet_recall={facet: _recall(facet) for facet in facet_ids},
        item_facet_recall={
            facet: _recall(facet, practice_item_id) for facet in facet_ids
        },
        facet_uncertainty={
            facet: repository.facet_uncertainty_state(learning_object_id, facet)
            for facet in facet_ids
        },
        item_parameter_state=(
            repository.item_parameter_state(practice_item_id)
            if vault.config.mastery.irt.eb_difficulty_enabled
            else None
        ),
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
    replay: bool = False,
) -> AttemptApplication:
    item, learning_object, rubric = _resolve_attempt_target(
        vault, repository, draft, replay=replay, clock=clock
    )
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
        evidence=vault.config.evidence,
    )
    # Asked-criteria evidence scaling: ungraded criteria certify no facet mass
    # (teach_back partial grading) and transfer-tier criterion evidence carries
    # the config multiplier. Both are symmetric mass effects, config-read at
    # apply time, so replay reproduces them. No-op for grades covering every
    # criterion of a core-only rubric (all existing modes).
    if draft.attempt_type != "dont_know":
        coverage = scale_coverage_for_graded_criteria(
            coverage,
            item,
            rubric,
            criterion_points=grade.criterion_points,
            transfer_evidence_multiplier=vault.config.teach_back.transfer_evidence_multiplier,
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
    item_a, item_b = resolve_item_irt_params(
        item, learning_object, vault.config.mastery, prior_state.item_parameter_state
    )
    if draft.primed:
        # Source just re-read: the item is effectively easier. Shifting b (rather
        # than dampening the observation weight) keeps the evidence asymmetric —
        # a primed success barely moves mu, a primed failure moves it strongly.
        # Prediction and surprise read the same shifted b, staying consistent.
        item_b -= vault.config.mastery.irt.priming_b_offset
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
    # P0.3 (§4.3/§4.4): for new-version (mvp-0.8) writes the grader-confidence
    # FACTOR is sourced from the calibrated interpretation's certainty LCB -- the
    # SAME certainty certification consumes -- so mastery and certification cannot
    # disagree about grader trust. The product SHAPE (clamp x hint x attempt_mass)
    # is unchanged (pinned by test_characterization_mastery_reliability). Legacy
    # versions keep the raw grader_confidence. Fail-safe: any resolution failure
    # falls back to the legacy source (§7.3).
    grader_confidence_source = grade.grader_confidence
    if (
        vault.config.algorithms.algorithm_version == P0_ALGORITHM_VERSION
        and draft.attempt_type != "dont_know"
    ):
        try:
            from learnloop.services.grade_resolution import response_certainty_lcb

            grader_confidence_source = response_certainty_lcb(
                vault,
                repository,
                item=item,
                grading_source="ai",
                rubric_score=grade.rubric_score,
                max_points=rubric.max_points,
                grader_confidence=grade.grader_confidence,
                has_fatal=bool(grade.error_attributions),
                response_text=draft.learner_answer_md,
                domain=learning_object.id,
                clock=clock,
            )
        except Exception:  # noqa: BLE001 - fail-safe reliability source (§7.3)
            grader_confidence_source = grade.grader_confidence
    reliability = resolve_reliability(
        item,
        attempt_type=draft.attempt_type,
        hints_used=draft.hints_used,
        grader_confidence=grader_confidence_source,
        evidence=vault.config.evidence,
    )
    familiarity = familiarity_discount_from_attempts(
        prior_state.recent_learning_object_attempts,
        item,
        covered_facets=coverage.covered_facets,
        config=vault.config,
        exclude_attempt_id=attempt_id,
    )
    lo_coverage, lo_coverage_trace = lo_relative_coverage(
        vault,
        repository,
        learning_object_id=learning_object.id,
        normalized_facet_weights=coverage.normalized_facet_weights,
        effective_item_coverage=coverage.effective_coverage,
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
    facet_recall_updates = build_facet_recall_updates_from_prior(
        prior_state.facet_recall_by_scope(coverage.covered_facets, item.id),
        learning_object_id=learning_object.id,
        practice_item_id=item.id,
        covered_facets=coverage.covered_facets,
        facet_outcomes=facet_outcomes,
        independent_evidence_discount=familiarity.independent_evidence_discount,
        attempt_type=draft.attempt_type,
        error_event_written=bool(resolved_attributions),
        algorithm_version=vault.config.algorithms.algorithm_version,
        now_iso=now_iso,
    )
    post_aggregate_facet_recall: dict[str, FacetRecallState | dict[str, Any] | None] = dict(
        prior_state.aggregate_facet_recall
    )
    for state in facet_recall_updates:
        if state.get("practice_item_id") is None:
            post_aggregate_facet_recall[str(state["facet_id"])] = state
    breadth_fraction, breadth_trace = covered_required_fraction(
        vault,
        repository,
        learning_object_id=learning_object.id,
        aggregate_facet_recall=post_aggregate_facet_recall,
    )
    error_impact = resolve_error_impact(
        vault.config,
        error_type=primary_error_type,
        max_event_severity=max_event_severity,
        effective_coverage=lo_coverage,
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
        attempt_evidence_mass=attempt_evidence_mass(draft.attempt_type, vault.config.evidence),
        primed=draft.primed,
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
    posterior_mastery, mastery_variance_floor = apply_mastery_variance_floor(
        posterior_mastery,
        vault.config,
        covered_fraction=breadth_fraction,
    )
    # Empirical-Bayes per-item difficulty: alternating conditional update on b
    # using the learner's fresh posterior mean (dark unless eb_difficulty_enabled).
    next_item_parameters: ItemParameterState | None = None
    # Primed outcomes are conditioned on the source being fresh in working
    # memory — they must not move the fitted *cold* difficulty.
    if vault.config.mastery.irt.eb_difficulty_enabled and not draft.primed:
        _authored_a, authored_b = item_irt_params(item, learning_object, vault.config.mastery)
        next_item_parameters = update_item_difficulty(
            prior_state.item_parameter_state,
            practice_item_id=item.id,
            authored_b=authored_b,
            item_a=item_a,
            learner_mu_posterior=posterior_mastery.logit_mean,
            observation=mastery_observation,
            config=vault.config.mastery,
            algorithm_version=vault.config.algorithms.algorithm_version,
            updated_at=now_iso,
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
    fsrs_rating = fsrs_rating_for_attempt(item, grade.rubric_score, rubric.max_points, draft.hints_used)
    fsrs_weights = resolve_fsrs_weights(repository)
    fsrs_weights_fitted = fsrs_weights is not FSRS6_DEFAULT_WEIGHTS
    elapsed_days = _elapsed_days(previous_state, observed_at)
    previous_memory = _memory_state(previous_state)
    # P1 step 5/9 (§3.10, §7.4): purpose-specific administration adapter seam. The
    # purpose-adapter path is the LIVE scheduling authority for mvp-0.8 vaults (the
    # step-9 cutover); legacy vaults keep the purpose-blind path byte-identical.
    #
    # The REAL evidence eligibility of the practice observation is threaded into the
    # decision (§3.8): a practice administration is scheduling-eligible unless its
    # evidence is ineligible (feedback revealed before response, quarantined /
    # out-of-band). For an eligible practice attempt -- the common case that reaches
    # apply_attempt -- the review still applies, so both paths are byte-identical; on a
    # LIVE mvp-0.8 vault an INELIGIBLE observation now correctly leaves card scheduling
    # state EXACTLY as it was (no memory rewrite, no due-date recompute). A legacy vault
    # bypasses the decision entirely (unconditional write, characterization-pinned).
    from learnloop.services.activities import evidence_eligibility_for
    from learnloop.services.administration_adapters import hot_path_applies_practice_review

    evidence_eligibility, _eligibility_reason = evidence_eligibility_for(
        purpose="practice", feedback_condition=None
    )
    observation_eligible = evidence_eligibility == "practice"
    if hot_path_applies_practice_review(
        attempt_type=draft.attempt_type,
        eligible=observation_eligible,
        algorithm_version=vault.config.algorithms.algorithm_version,
    ):
        next_memory = apply_review(previous_memory, fsrs_rating, elapsed_days, fsrs_weights)
        interval_days = (
            interval_for_retention(next_memory.stability, weights=fsrs_weights)
            * surprise.fsrs_interval_factor
        )
        due_at = (observed_at + timedelta(days=interval_days)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    else:
        # LIVE mvp-0.8 + ineligible observation: scheduling state is left EXACTLY as it
        # was (§3.8). A first-ever ineligible observation creates NO memory state
        # (never apply_review(None, ...)); a retained prior memory keeps its stored
        # interval / due_at unchanged (never a rewritten due-date).
        next_memory = previous_memory
        interval_days = None
        due_at = previous_state.due_at if previous_state is not None else None

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
        "primed": draft.primed,
        "probe_presentation_id": draft.probe_presentation_id,
        "answer_confidence": draft.answer_confidence,
        "submission_id": draft.submission_id,
        "declared_dont_know": draft.declared_dont_know,
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
                "misconception_statement": attribution.misconception_statement,
                "misconception_consistent_answer": attribution.misconception_consistent_answer,
                "misconception_id": attribution.misconception_id,
                "repair_plan": _error_event_repair_plan(vault, base_attribution),
                "status": "active",
                "created_at": now_iso,
                "updated_at": now_iso,
            }
        )
    facet_evidence_rows: Iterable[Any] = grade.evidence_rows
    if not grade.evidence_rows:
        facet_evidence_rows = repository.fetch_grading_evidence(attempt_id)
    facet_uncertainty_updates, facet_uncertainty_trace = build_facet_uncertainty_updates(
        vault,
        item=item,
        rubric=rubric,
        learning_object_id=learning_object.id,
        attempt_id=attempt_id,
        facet_outcomes=facet_outcomes,
        normalized_facet_weights=coverage.normalized_facet_weights,
        evidence_rows=facet_evidence_rows,
        error_attributions=resolved_attributions,
        prior_uncertainties=prior_state.facet_uncertainty,
        prior_facet_recall=prior_state.aggregate_facet_recall,
        observed_error_type=primary_error_type,
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
        "lo_relative_coverage": lo_coverage,
        "lo_relative_coverage_trace": lo_coverage_trace,
        "covered_required_fraction": breadth_fraction,
        "covered_required_fraction_trace": breadth_trace,
        "mastery_variance_floor": mastery_variance_floor,
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
        "facet_uncertainty_updates": facet_uncertainty_updates,
        "facet_uncertainty_trace": facet_uncertainty_trace,
        "ability_transition": ability_transition,
        "primed": draft.primed,
        "priming_b_offset": vault.config.mastery.irt.priming_b_offset if draft.primed else None,
        "fsrs_weights_fitted": fsrs_weights_fitted,
        "algorithm_version": vault.config.algorithms.algorithm_version,
        "created_at": now_iso,
    }
    practice_state = PracticeItemState(
        practice_item_id=item.id,
        difficulty=next_memory.difficulty if next_memory is not None else None,
        stability=next_memory.stability if next_memory is not None else None,
        retrievability=next_memory.retrievability if next_memory is not None else None,
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
        facet_uncertainty_states=facet_uncertainty_updates,
        quality_state=quality_state,
        ability_transition=ability_transition_event,
        attempt_debug_payload=debug_payload,
        result=result,
        item_parameter_state=next_item_parameters,
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
                target_criterion_ids=list(criteria),
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


def _dont_know_error_type(vault: LoadedVault, hints_used: int) -> str:
    legacy = SCAFFOLD_FAILURE_ERROR_TYPE if hints_used > 0 else DONT_KNOW_ERROR_TYPE
    # KM4 §10.1: under mvp-0.7 the deterministic attribution speaks the canonical
    # mechanism vocabulary (both recall_failure and scaffold_failure resolve to
    # retrieval_failure). mvp-0.6 keeps the legacy names, so replay is unchanged.
    if is_canonical_state_vault(vault):
        return map_legacy_error_type(legacy)
    return legacy


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
                    misconception_statement=event.get("misconception_statement"),
                    misconception_consistent_answer=event.get("misconception_consistent_answer"),
                    misconception_id=event.get("misconception_id"),
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
            "learner_confidence": evidence.learner_confidence,
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
                misconception_statement=attribution.misconception_statement,
                misconception_consistent_answer=attribution.misconception_consistent_answer,
                misconception_id=getattr(attribution, "misconception_id", None),
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


def fsrs_rating_for_attempt(item: PracticeItem, rubric_score: int, max_points: int, hints_used: int) -> Rating:
    """FSRS rating for a graded attempt: score binning + the item's hint cap.

    Single source of truth shared by the live attempt path and offline fitting
    (review-log reconstruction must reproduce live semantics exactly).
    """

    return _capped_rating(rating_from_score(rubric_score, max_points), item, hints_used)


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

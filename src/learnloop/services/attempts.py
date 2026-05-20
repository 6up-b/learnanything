from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, timedelta

from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.codex.client import CodexClient, CodexUnavailable
from learnloop.codex.prompts import GRADING_PROMPT_VERSION
from learnloop.codex.runtime import CodexRuntimeReport
from learnloop.codex.schemas import GradingProposal
from learnloop.db.repositories import MasteryState, PracticeItemState, Repository
from learnloop.ids import new_ulid
from learnloop.services.fsrs import MemoryState, Rating, apply_review, interval_for_retention, rating_from_score
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
from learnloop.services.mastery import MasteryObservation, display_mastery, initial_mastery_state, update_mastery
from learnloop.services.probes import record_probe_attempt
from learnloop.services.surprise import compute_surprise
from learnloop.vault.hashes import practice_item_hash
from learnloop.vault.models import LoadedVault, PracticeItem, Rubric


@dataclass(frozen=True)
class AttemptDraft:
    practice_item_id: str
    learner_answer_md: str
    attempt_type: str = "independent_attempt"
    hints_used: int = 0
    latency_seconds: int | None = None


@dataclass(frozen=True)
class SelfGradeInput:
    criterion_points: dict[str, float]
    confidence: int
    fatal_errors: list[str] | None = None
    error_type: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class GradeAttribution:
    error_type: str
    severity: float
    evidence: str | None = None
    is_misconception: bool = False


@dataclass(frozen=True)
class ResolvedGrade:
    rubric_score: int
    criterion_points: dict[str, float]
    evidence_rows: list[dict[str, object]]
    error_attributions: list[GradeAttribution]
    grader_confidence: float
    confidence: int | None
    manual_review_reason: str | None


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
        }


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
    item, _learning_object, _rubric = _resolve_attempt_target(vault, draft)
    if not runtime.ready or codex_client is None:
        reason = runtime.status if not runtime.ready else "codex_client_missing"
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
            "provider": "codex",
            "prompt_template": "grading",
            "prompt_version": GRADING_PROMPT_VERSION,
            "codex_revision": runtime.actual_revision,
            "input_context_hash": grading_context_hash(context),
            "output_schema": "GradingProposal",
            "started_at": now,
            "status": "running",
        }
    )
    try:
        proposal = codex_client.run_grading_proposal(context)
        result = complete_codex_graded_attempt(
            vault,
            repository,
            draft,
            proposal,
            attempt_id=attempt_id,
            agent_run_id=agent_run_id,
            clock=clock,
        )
    except (CodexUnavailable, TimeoutError, GradingValidationError, AttemptValidationError, ValueError) as exc:
        repository.complete_agent_run(agent_run_id, status="failed", error_message=str(exc), clock=clock)
        result = complete_self_graded_attempt(vault, repository, draft, fallback_grade, clock=clock)
        return _with_fallback(result, f"codex_failed:{type(exc).__name__}", agent_run_id=agent_run_id)
    repository.complete_agent_run(agent_run_id, status="completed", clock=clock)
    return _with_source(result, grading_source="codex", agent_run_id=agent_run_id)


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
    criterion_points = _validated_criterion_points(rubric, grade.criterion_points)
    fatal_errors = grade.fatal_errors or []
    _validate_fatal_errors(rubric, fatal_errors)
    if draft.attempt_type == "dont_know":
        criterion_points = {criterion.id: 0.0 for criterion in rubric.criteria}
        fatal_errors = []
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
    return _complete_resolved_grade(
        vault,
        repository,
        draft,
        attempt_id=attempt_id,
        grade=ResolvedGrade(
            rubric_score=rubric_score,
            criterion_points=criterion_points,
            evidence_rows=evidence_rows,
            error_attributions=_self_grade_attributions(vault, fatal_errors, grade.error_type),
            grader_confidence=grader_confidence,
            confidence=grade.confidence,
            manual_review_reason=manual_review_reason,
        ),
        clock=clock,
    )


def complete_codex_graded_attempt(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    proposal: GradingProposal,
    *,
    attempt_id: str | None = None,
    agent_run_id: str | None = None,
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
        )
    except GradingValidationError as exc:
        raise AttemptValidationError(str(exc)) from exc
    result = _complete_resolved_grade(
        vault,
        repository,
        draft,
        attempt_id=expected_attempt_id,
        grade=_resolved_codex_grade(validated, agent_run_id=agent_run_id, clock=clock),
        clock=clock,
    )
    return _with_source(result, grading_source="codex", agent_run_id=agent_run_id)


def _with_source(result: AttemptResult, *, grading_source: str, agent_run_id: str | None = None) -> AttemptResult:
    return replace(result, grading_source=grading_source, agent_run_id=agent_run_id)


def _with_fallback(result: AttemptResult, reason: str, *, agent_run_id: str | None = None) -> AttemptResult:
    return replace(result, grading_source="self", fallback_reason=reason, agent_run_id=agent_run_id)


def _resolve_attempt_target(vault: LoadedVault, draft: AttemptDraft):
    if draft.attempt_type in {"guided_walkthrough", "skip"}:
        raise AttemptValidationError(f"{draft.attempt_type} does not write a formal attempt")
    item = vault.practice_items.get(draft.practice_item_id)
    if item is None:
        raise AttemptValidationError(f"Unknown Practice Item {draft.practice_item_id}")
    learning_object = vault.learning_object_for_item(item)
    if learning_object is None:
        raise AttemptValidationError(f"{item.id} references missing Learning Object {item.learning_object_id}")
    if item.attempt_types_allowed and draft.attempt_type not in item.attempt_types_allowed:
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


def _complete_resolved_grade(
    vault: LoadedVault,
    repository: Repository,
    draft: AttemptDraft,
    *,
    attempt_id: str,
    grade: ResolvedGrade,
    clock: Clock | None = None,
) -> AttemptResult:
    item, learning_object, rubric = _resolve_attempt_target(vault, draft)
    observed_at = (clock or SystemClock()).now().astimezone(UTC)
    now_iso = utc_now_iso(clock)
    correctness = grade.rubric_score / max(rubric.max_points, 1)
    subjects = vault.subjects_for_item(item)
    subject = subjects[0] if subjects else None
    primary_error_type = grade.error_attributions[0].error_type if grade.error_attributions else None
    prior_active_errors = repository.active_errors_by_learning_object(learning_object.id)

    prior_mastery = repository.mastery_state(learning_object.id) or initial_mastery_state(
        learning_object.id,
        vault.config.algorithms.algorithm_version,
        now_iso,
    )
    mastery_observation = MasteryObservation(
        rubric_score=grade.rubric_score,
        max_points=rubric.max_points,
        evidence_coverage=_evidence_coverage(item, grade.criterion_points),
        hint_dampening=_hint_dampening(item, draft.hints_used),
        grader_confidence=grade.grader_confidence,
        attempt_type=draft.attempt_type,
        observed_at=observed_at,
    )
    posterior_mastery = update_mastery(
        prior_mastery,
        mastery_observation,
        vault.config.mastery,
        vault.config.algorithms.algorithm_version,
    )
    surprise = compute_surprise(
        prior=prior_mastery,
        posterior=posterior_mastery,
        observation=mastery_observation,
        observed_error_type=primary_error_type,
        prior_active_errors=prior_active_errors,
        config=vault.config,
    )

    previous_state = repository.practice_item_state(item.id)
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
    }
    error_event_ids = [new_ulid() for _ in grade.error_attributions]
    error_events = [
        {
            "id": event_id,
            "attempt_id": attempt_id,
            "learning_object_id": learning_object.id,
            "error_type": attribution.error_type,
            "severity": attribution.severity,
            "is_misconception": attribution.is_misconception,
            "repair_plan": {"evidence": attribution.evidence} if attribution.evidence else None,
            "status": "active",
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        for event_id, attribution in zip(error_event_ids, grade.error_attributions, strict=True)
    ]
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
    repository.record_attempt_outcome(
        attempt=attempt_record,
        evidence_rows=grade.evidence_rows,
        error_events=error_events,
        surprise=surprise.as_record(attempt_id, vault.config.algorithms.algorithm_version, now_iso),
        practice_item_state=practice_state,
        mastery_state=posterior_mastery,
    )
    record_probe_attempt(vault, repository, learning_object.id, clock=clock)

    mastery_display = display_mastery(posterior_mastery)
    return AttemptResult(
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
    )


def _self_grade_attributions(vault: LoadedVault, fatal_errors: list[str], error_type: str | None) -> list[GradeAttribution]:
    return [
        GradeAttribution(
            error_type=selected_error_type,
            severity=_error_severity(vault, selected_error_type),
            is_misconception=_is_misconception(vault, selected_error_type),
        )
        for selected_error_type in _selected_error_types(fatal_errors, error_type)
    ]


def _resolved_codex_grade(validated: ValidatedCodexGrade, *, agent_run_id: str | None, clock: Clock | None) -> ResolvedGrade:
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
            )
            for attribution in validated.error_attributions
        ],
        grader_confidence=validated.grader_confidence,
        confidence=None,
        manual_review_reason=validated.manual_review_reason,
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


def _selected_error_types(fatal_errors: list[str], error_type: str | None) -> list[str]:
    selected: list[str] = []
    for candidate in [*fatal_errors, error_type]:
        if candidate and candidate not in selected:
            selected.append(candidate)
    return selected


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

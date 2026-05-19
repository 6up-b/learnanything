from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from learnloop.codex.client import GradingContext
from learnloop.codex.schemas import GradingProposal
from learnloop.vault.models import LoadedVault, PracticeItem, Rubric


def confidence_to_grader_confidence(confidence: int) -> float:
    mapping = {1: 0.2, 2: 0.4, 3: 0.6, 4: 0.8, 5: 1.0}
    if confidence not in mapping:
        raise ValueError("confidence must be between 1 and 5")
    return mapping[confidence]


class GradingValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ValidatedCriterionEvidence:
    criterion_id: str
    points_awarded: float
    evidence: str
    notes: str | None = None


@dataclass(frozen=True)
class ValidatedErrorAttribution:
    error_type: str
    severity: float
    evidence: str
    is_misconception: bool = False


@dataclass(frozen=True)
class ValidatedCodexGrade:
    rubric_score: int
    criterion_evidence: list[ValidatedCriterionEvidence]
    fatal_errors: list[str]
    error_attributions: list[ValidatedErrorAttribution]
    grader_confidence: float
    manual_review_reason: str | None


def build_grading_context(
    vault: LoadedVault,
    item: PracticeItem,
    *,
    attempt_id: str,
    learner_answer_md: str,
) -> GradingContext:
    rubric = _resolved_rubric(item)
    expected_answer = item.expected_answer if isinstance(item.expected_answer, str) else json.dumps(item.expected_answer, sort_keys=True)
    return GradingContext(
        attempt_id=attempt_id,
        practice_item_id=item.id,
        prompt=item.prompt,
        expected_answer=expected_answer,
        learner_answer_md=learner_answer_md,
        rubric=rubric.model_dump(mode="json", exclude_none=False),
    )


def evidence_coverage(item: PracticeItem, criterion_points: dict[str, float]) -> float:
    if not any(points >= 1 for points in criterion_points.values()):
        return 0.0
    if not item.evidence_weights:
        return 1.0
    if item.evidence_facets:
        return min(1.0, sum(float(item.evidence_weights.get(facet, 0.0)) for facet in item.evidence_facets))
    return min(1.0, sum(float(weight) for weight in item.evidence_weights.values()))


def grading_context_hash(context: GradingContext) -> str:
    payload = {
        "attempt_id": context.attempt_id,
        "practice_item_id": context.practice_item_id,
        "prompt": context.prompt,
        "expected_answer": context.expected_answer,
        "learner_answer_md": context.learner_answer_md,
        "rubric": context.rubric,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def validate_codex_grading_proposal(
    proposal: GradingProposal,
    *,
    attempt_id: str,
    item: PracticeItem,
    vault: LoadedVault,
) -> ValidatedCodexGrade:
    rubric = _resolved_rubric(item)
    if proposal.attempt_id != attempt_id:
        raise GradingValidationError(f"Grading attempt_id {proposal.attempt_id} does not match {attempt_id}")
    if proposal.practice_item_id != item.id:
        raise GradingValidationError(f"Grading practice_item_id {proposal.practice_item_id} does not match {item.id}")

    criteria = {criterion.id: criterion for criterion in rubric.criteria}
    seen: set[str] = set()
    validated_evidence: list[ValidatedCriterionEvidence] = []
    for evidence in proposal.criterion_evidence:
        if evidence.criterion_id not in criteria:
            raise GradingValidationError(f"Unknown rubric criterion {evidence.criterion_id}")
        if evidence.criterion_id in seen:
            raise GradingValidationError(f"Duplicate rubric criterion {evidence.criterion_id}")
        seen.add(evidence.criterion_id)
        if evidence.points_awarded < 0:
            raise GradingValidationError(f"{evidence.criterion_id} points cannot be negative")
        if evidence.points_awarded > criteria[evidence.criterion_id].points:
            raise GradingValidationError(
                f"{evidence.criterion_id} points exceed max {criteria[evidence.criterion_id].points:g}"
            )
        validated_evidence.append(
            ValidatedCriterionEvidence(
                criterion_id=evidence.criterion_id,
                points_awarded=evidence.points_awarded,
                evidence=evidence.evidence,
                notes=evidence.notes,
            )
        )

    fatal_by_id = {fatal_error.id: fatal_error for fatal_error in rubric.fatal_errors}
    unknown_fatal = sorted(set(proposal.fatal_errors) - set(fatal_by_id))
    if unknown_fatal:
        raise GradingValidationError(f"Unknown fatal errors: {', '.join(unknown_fatal)}")
    capped_score = proposal.rubric_score
    for fatal_error_id in proposal.fatal_errors:
        capped_score = min(capped_score, fatal_by_id[fatal_error_id].max_grade)
    if capped_score != proposal.rubric_score:
        raise GradingValidationError("Fatal errors must cap rubric_score")

    validated_errors = [
        ValidatedErrorAttribution(
            error_type=attribution.error_type,
            severity=attribution.severity,
            evidence=attribution.evidence,
            is_misconception=attribution.is_misconception,
        )
        for attribution in proposal.error_attributions
    ]
    manual_review_reason = "codex_manual_review" if proposal.manual_review_recommended else None
    unknown_error_types = sorted(
        {attribution.error_type for attribution in proposal.error_attributions if attribution.error_type not in vault.error_types}
    )
    if unknown_error_types:
        manual_review_reason = "unknown_error_type:" + ",".join(unknown_error_types)

    return ValidatedCodexGrade(
        rubric_score=proposal.rubric_score,
        criterion_evidence=validated_evidence,
        fatal_errors=proposal.fatal_errors,
        error_attributions=validated_errors,
        grader_confidence=proposal.grader_confidence,
        manual_review_reason=manual_review_reason,
    )


def _resolved_rubric(item: PracticeItem) -> Rubric:
    if item.grading_rubric is None:
        raise GradingValidationError(f"{item.id} has no inline grading_rubric")
    return item.grading_rubric

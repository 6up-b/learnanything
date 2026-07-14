from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

from learnloop.codex.client import GradingContext
from learnloop.codex.schemas import GradingProposal
from learnloop.config import EvidenceConfig
from learnloop.services.error_taxonomy_map import (
    MECHANISM_SEVERITY_DEFAULT,
    MECHANISM_TAXONOMY_CARD_JSON,
    map_legacy_error_type,
)
from learnloop.services.recall_coverage import criterion_facet_weights_for_item, resolve_coverage
from learnloop.vault.models import LoadedVault, PracticeItem, Rubric


def is_canonical_state_vault(vault: LoadedVault) -> bool:
    """Whether the vault reads/writes canonical (mvp-0.7) state.

    Lazy indirection to ``facet_state_reader`` avoids a grading↔assessment_contracts
    import cycle at module load (the reader pulls in assessment_contracts, which
    imports ``resolved_rubric`` from this module).
    """

    from learnloop.services.facet_state_reader import (
        is_canonical_state_vault as _impl,
    )

    return _impl(vault)


CANONICAL_ERROR_TYPES: tuple[dict[str, object], ...] = (
    {
        "id": "recall_failure",
        "title": "Recall failure",
        "severity_default": 0.4,
        "is_misconception": False,
        "use_when": "The learner explicitly cannot retrieve the requested fact, formula, step, or facet.",
        "avoid_when": "The answer gives a wrong model or wrong rule; use conceptual_slip or procedure_misapplication instead.",
    },
    {
        "id": "conceptual_slip",
        "title": "Conceptual slip",
        "severity_default": 0.7,
        "is_misconception": True,
        "use_when": "The learner's answer reveals a wrong definition, relationship, interpretation, or mental model.",
        "avoid_when": "The concept is right but execution is wrong; use procedure_misapplication or arithmetic_slip.",
    },
    {
        "id": "procedure_misapplication",
        "title": "Procedure misapplication",
        "severity_default": 0.65,
        "is_misconception": True,
        "use_when": "The learner chooses the wrong rule, formula, algorithm step, retained/discarded case, or condition.",
        "avoid_when": "The rule is correct but a local numeric manipulation is wrong; use arithmetic_slip.",
    },
    {
        "id": "arithmetic_slip",
        "title": "Arithmetic slip",
        "severity_default": 0.15,
        "is_misconception": False,
        "use_when": "The setup and concept are correct, but arithmetic, algebra, sign, indexing, or simplification is locally wrong.",
        "avoid_when": "The calculation follows from choosing the wrong method; use procedure_misapplication.",
    },
    {
        "id": "incomplete_answer",
        "title": "Incomplete answer",
        "severity_default": 0.35,
        "is_misconception": False,
        "use_when": "The answer is partially correct but omits a required value, justification, condition, unit, or explanation.",
        "avoid_when": "The omitted part is explicitly unknown to the learner; use recall_failure for that facet.",
    },
)

BUILTIN_ERROR_TYPE_DEFAULTS = {
    str(error["id"]): float(error["severity_default"])
    for error in CANONICAL_ERROR_TYPES
} | {"scaffold_failure": 0.65}

# mvp-0.7 grader contract (§10.1): the canonical builtins are the nine mechanism
# taxonomy values, not the legacy five. The legacy names remain resolvable via
# ``map_legacy_error_type`` so config/back-compat keep working, but a mvp-0.7
# grader emits (and the validator accepts) the mechanism vocabulary directly.
MECHANISM_ERROR_TYPE_DEFAULTS = dict(MECHANISM_SEVERITY_DEFAULT)


def builtin_error_type_defaults(vault: LoadedVault) -> dict[str, float]:
    """Version-branched builtin error-type severity defaults.

    mvp-0.6 vaults keep the legacy five (+scaffold_failure); mvp-0.7 vaults use
    the nine-mechanism taxonomy. Legacy replay is byte-identical because a
    mvp-0.6 vault never reaches the mechanism branch.
    """

    if is_canonical_state_vault(vault):
        return MECHANISM_ERROR_TYPE_DEFAULTS
    return BUILTIN_ERROR_TYPE_DEFAULTS


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
    learner_confidence: str | None = None


@dataclass(frozen=True)
class ValidatedErrorAttribution:
    error_type: str
    severity: float
    evidence: str
    is_misconception: bool = False
    # spec §2.1: passed through, not enforced (None for legacy providers).
    misconception_statement: str | None = None
    misconception_consistent_answer: str | None = None
    target_evidence_families: list[str] | None = None
    target_criterion_ids: list[str] | None = None


@dataclass(frozen=True)
class ValidatedCodexGrade:
    rubric_score: int
    criterion_evidence: list[ValidatedCriterionEvidence]
    fatal_errors: list[str]
    error_attributions: list[ValidatedErrorAttribution]
    grader_confidence: float
    manual_review_reason: str | None
    feedback_md: str | None = None
    repair_suggestions: list[dict[str, Any]] | None = None


def build_grading_context(
    vault: LoadedVault,
    item: PracticeItem,
    *,
    attempt_id: str,
    learner_answer_md: str,
    rubric: Rubric | None = None,
    assessment_contract: dict[str, Any] | None = None,
) -> GradingContext:
    rubric = rubric or resolved_rubric(vault, item)
    prompt = (
        assessment_contract.get("prompt", item.prompt)
        if assessment_contract is not None
        else item.prompt
    )
    expected_value = (
        assessment_contract.get("expected_answer", item.expected_answer)
        if assessment_contract is not None
        else item.expected_answer
    )
    expected_answer = expected_value if isinstance(expected_value, str) else json.dumps(expected_value, sort_keys=True)
    return GradingContext(
        attempt_id=attempt_id,
        practice_item_id=item.id,
        prompt=prompt,
        expected_answer=expected_answer,
        learner_answer_md=learner_answer_md,
        rubric=rubric.model_dump(mode="json", exclude_none=False),
        evidence_facets=list(item.evidence_facets),
        evidence_weights=dict(item.evidence_weights),
        criterion_facet_weights=criterion_facet_weights_for_item(item, rubric),
        error_taxonomy=_grading_error_taxonomy(vault),
    )


def evidence_coverage(
    item: PracticeItem,
    criterion_points: dict[str, float],
    *,
    rubric: Rubric | None = None,
    attempt_type: str = "independent_attempt",
    hints_used: int = 0,
    learner_answer_md: str = "__engaged_answer__",
    evidence: EvidenceConfig | None = None,
) -> float:
    """Compatibility wrapper for score-independent coverage resolution.

    ``criterion_points`` is retained for older callers, but coverage no longer
    depends on awarded points. Use ``resolve_coverage`` for new code that also
    needs traces and facet allocation.
    """

    _ = criterion_points
    return resolve_coverage(
        item,
        rubric or item.grading_rubric,
        attempt_type=attempt_type,
        hints_used=hints_used,
        learner_answer_md=learner_answer_md,
        evidence=evidence,
    ).effective_coverage


def grading_context_hash(context: GradingContext) -> str:
    payload = {
        "attempt_id": context.attempt_id,
        "practice_item_id": context.practice_item_id,
        "prompt": context.prompt,
        "expected_answer": context.expected_answer,
        "learner_answer_md": context.learner_answer_md,
        "rubric": context.rubric,
        "evidence_facets": context.evidence_facets,
        "evidence_weights": context.evidence_weights,
        "criterion_facet_weights": context.criterion_facet_weights,
        "error_taxonomy": context.error_taxonomy,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def validate_codex_grading_proposal(
    proposal: GradingProposal,
    *,
    attempt_id: str,
    item: PracticeItem,
    vault: LoadedVault,
    learner_answer_md: str | None = None,
    rubric: Rubric | None = None,
) -> ValidatedCodexGrade:
    rubric = rubric or resolved_rubric(vault, item)
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
                learner_confidence=_canonical_learner_confidence(evidence.learner_confidence),
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

    known_facets = set(item.evidence_facets)
    known_facets.update(
        target.facet for criterion in rubric.criteria for target in criterion.targets
    )
    unknown_target_families: set[str] = set()
    unknown_target_criteria: set[str] = set()
    criterion_facet_weights = criterion_facet_weights_for_item(item, rubric)
    validated_errors: list[ValidatedErrorAttribution] = []
    for attribution in proposal.error_attributions:
        error_type = _normalized_recall_error_type(
            vault,
            attribution.error_type,
            evidence=attribution.evidence,
            learner_answer_md=learner_answer_md,
            is_misconception=attribution.is_misconception,
        )
        target_evidence_families: list[str] = []
        for raw_target in attribution.target_evidence_families:
            target = vault.canonical_facet_id(raw_target)
            if target in known_facets:
                if target not in target_evidence_families:
                    target_evidence_families.append(target)
            else:
                unknown_target_families.add(raw_target)
        target_criterion_ids: list[str] = []
        for raw_criterion_id in attribution.target_criterion_ids:
            if raw_criterion_id not in criteria:
                unknown_target_criteria.add(raw_criterion_id)
                continue
            if raw_criterion_id not in target_criterion_ids:
                target_criterion_ids.append(raw_criterion_id)
            for facet in criterion_facet_weights.get(raw_criterion_id, {}):
                target = vault.canonical_facet_id(facet)
                if target in known_facets and target not in target_evidence_families:
                    target_evidence_families.append(target)
        validated_errors.append(
            ValidatedErrorAttribution(
                error_type=error_type,
                severity=_resolved_error_severity(vault, error_type, attribution.severity),
                evidence=attribution.evidence,
                is_misconception=attribution.is_misconception,
                misconception_statement=attribution.misconception_statement,
                misconception_consistent_answer=attribution.misconception_consistent_answer,
                target_evidence_families=target_evidence_families,
                target_criterion_ids=target_criterion_ids,
            )
        )
    validated_repair_suggestions: list[dict[str, Any]] = []
    for suggestion in proposal.repair_suggestions:
        target_evidence_families: list[str] = []
        for raw_target in suggestion.target_evidence_families:
            target = vault.canonical_facet_id(raw_target)
            if target in known_facets:
                if target not in target_evidence_families:
                    target_evidence_families.append(target)
            else:
                unknown_target_families.add(raw_target)
        payload = suggestion.model_dump(mode="json")
        payload["target_evidence_families"] = target_evidence_families
        validated_repair_suggestions.append(payload)
    manual_review_reason = "codex_manual_review" if proposal.manual_review_recommended else None
    if manual_review_reason is None and proposal.grader_confidence < 0.4:
        manual_review_reason = "low_grader_confidence"
    if manual_review_reason is None and unknown_target_families:
        manual_review_reason = "unknown_target_evidence_family:" + ",".join(sorted(unknown_target_families))
    if manual_review_reason is None and unknown_target_criteria:
        manual_review_reason = "unknown_target_criterion:" + ",".join(sorted(unknown_target_criteria))
    builtin_defaults = builtin_error_type_defaults(vault)
    unknown_error_types = sorted(
        {
            attribution.error_type
            for attribution in validated_errors
            if attribution.error_type not in vault.error_types
            and attribution.error_type not in builtin_defaults
        }
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
        feedback_md=proposal.feedback_md,
        repair_suggestions=validated_repair_suggestions,
    )


def resolved_rubric(vault: LoadedVault, item: PracticeItem) -> Rubric:
    rubric = vault.rubric_for_item(item)
    if rubric is None:
        raise GradingValidationError(
            f"{item.id} has no grading_rubric and no default rubric for practice mode {item.practice_mode}"
        )
    return rubric


def _resolved_error_severity(vault: LoadedVault, error_type: str, severity: float | None) -> float:
    if severity is not None:
        return severity
    taxonomy = vault.error_types.get(error_type)
    if taxonomy is not None:
        return taxonomy.severity_default
    return builtin_error_type_defaults(vault).get(error_type, 0.5)


def _canonical_learner_confidence(value: str | None) -> str | None:
    if value == "unknown":
        return "absent"
    return value


def _grading_error_taxonomy(vault: LoadedVault) -> dict[str, object]:
    canonical_vault = is_canonical_state_vault(vault)
    builtin_defaults = builtin_error_type_defaults(vault)
    custom = [
        {
            "id": error.id,
            "title": error.title,
            "description": error.description,
            "severity_default": error.severity_default,
            "is_misconception": error.is_misconception,
            "tags": error.tags,
            "related_concepts": error.related_concepts,
        }
        for error in sorted(vault.error_types.values(), key=lambda entry: entry.id)
        # Exclude the version's builtins. Under mvp-0.7 also exclude any legacy
        # seed name that already resolves to a canonical mechanism, so a mvp-0.7
        # grader is not offered the retired recall_failure/scaffold_failure/
        # arithmetic_slip seeds. mvp-0.6 keeps the exact legacy filter.
        if error.id not in builtin_defaults
        and (not canonical_vault or map_legacy_error_type(error.id) == error.id)
    ]
    if is_canonical_state_vault(vault):
        canonical = [dict(error) for error in MECHANISM_TAXONOMY_CARD_JSON]
        selection_policy = (
            "Pick the mechanism error_type id (§10.1 stable taxonomy) whose use_when fits and whose "
            "avoid_when does not. Use rubric fatal error ids when they exactly match the observed failure. "
            "Only propose a new error_type when the failure is a durable, specific misconception that none "
            "of the mechanism ids or rubric fatal ids cover."
        )
    else:
        canonical = [dict(error) for error in CANONICAL_ERROR_TYPES]
        selection_policy = (
            "Prefer the five canonical error_type ids for ordinary grading. Use rubric fatal error ids "
            "when they exactly match the observed failure. Only propose a new error_type when the failure "
            "is a durable, specific misconception that none of the canonical ids or rubric fatal ids cover."
        )
    return {
        "canonical_error_types": canonical,
        "vault_error_types": custom,
        "selection_policy": selection_policy,
        "targeting_policy": (
            "Every error_attribution should point to the affected target_criterion_ids and/or "
            "target_evidence_families. Use the narrowest target that explains the lost rubric points."
        ),
    }


def _normalized_recall_error_type(
    vault: LoadedVault,
    error_type: str,
    *,
    evidence: str,
    learner_answer_md: str | None,
    is_misconception: bool,
) -> str:
    canonical_vault = is_canonical_state_vault(vault)

    def _finalize(value: str) -> str:
        # Under mvp-0.7 the grader may still emit a legacy name (legacy provider
        # or heuristic branch above): resolve it onto the canonical mechanism so
        # a single vocabulary reaches the state model. mvp-0.6 is untouched.
        return map_legacy_error_type(value) if canonical_vault else value

    if is_misconception:
        return _finalize(error_type)
    text = f"{error_type} {evidence} {learner_answer_md or ''}".lower()
    if _RECALL_FAILURE_PATTERN.search(text):
        return _finalize("recall_failure")
    if error_type in vault.error_types or error_type in builtin_error_type_defaults(vault):
        return _finalize(error_type)
    if re.search(r"\b(arithmetic|calculation|numeric)_?(error|slip|mistake)\b", error_type.lower()):
        return _finalize("arithmetic_slip")
    if re.search(r"\b(missing|omitted|incomplete|partial)\b", error_type.lower()):
        return _finalize("incomplete_answer")
    return _finalize(error_type)


_RECALL_FAILURE_PATTERN = re.compile(
    r"\b("
    r"i\s+(do\s+not|don'?t)\s+(know|remember|recall)|"
    r"(do\s+not|don'?t)\s+(know|remember|recall)|"
    r"cannot\s+(remember|recall)|"
    r"can'?t\s+(remember|recall)|"
    r"not\s+sure\s+how"
    r")\b"
)

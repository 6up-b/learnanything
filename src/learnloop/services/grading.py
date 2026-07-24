from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from typing import Any, Iterable, Mapping

from learnloop.codex.client import GradingContext
from learnloop.codex.schemas import CriterionEvidence, GradingProposal
from learnloop.config import EvidenceConfig
from learnloop.services.error_taxonomy_map import (
    MECHANISM_SEVERITY_DEFAULT,
    MECHANISM_TAXONOMY_CARD_JSON,
    map_legacy_error_type,
)
from learnloop.services.capability_mapping import CriterionOutcome, localize_criterion_outcomes
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


_OPTION_LETTER = re.compile(r"^\s*\(?([A-H])\)?\s*[\.\):—-]?\s*", re.IGNORECASE)
_OPTION_LINE = re.compile(r"^\s*\(?([A-H])\)?\s*[\.\)]\s+\S", re.MULTILINE)


def _option_letter(text: str | None) -> str | None:
    if not text:
        return None
    match = _OPTION_LETTER.match(text.strip())
    return match.group(1).upper() if match else None


def deterministic_recognition_grade(
    item,
    rubric,
    learner_answer_md: str,
    *,
    attempt_id: str,
) -> GradingProposal | None:
    """Exact option-letter grading for recognition/multiple-choice items.

    Returns a full-confidence proposal when BOTH the authored expected answer
    and the learner answer unambiguously name one of the prompt's option
    letters; returns None (defer to the model grader) otherwise. Grading a
    constrained selection by string comparison costs nothing and — unlike an
    LLM grade — carries no calibration-channel uncertainty, so a correct pick
    is a certainty-1.0 observation instead of a cold-channel-discounted one.
    """

    mode = (getattr(item, "practice_mode", None) or "").lower()
    if mode not in ("recognition", "multiple_choice"):
        return None
    if rubric is None or len(rubric.criteria) != 1:
        return None
    prompt_options = {m.group(1).upper() for m in _OPTION_LINE.finditer(item.prompt or "")}
    if len(prompt_options) < 2:
        return None
    expected = _option_letter(getattr(item, "expected_answer", None))
    chosen = _option_letter(learner_answer_md)
    if expected is None or expected not in prompt_options:
        return None
    if chosen is None or chosen not in prompt_options:
        return None  # free-text response: the model grader must interpret it
    criterion = rubric.criteria[0]
    correct = chosen == expected
    points = float(criterion.points) if correct else 0.0
    score = 4 if correct else 0
    evidence = (
        f"Selected option {chosen}; expected option {expected}."
        + (" Exact match." if correct else " Mismatch.")
    )
    return GradingProposal(
        attempt_id=attempt_id,
        practice_item_id=item.id,
        rubric_score=score,
        criterion_evidence=[
            CriterionEvidence(
                criterion_id=criterion.id,
                points_awarded=points,
                evidence=evidence,
            )
        ],
        grader_confidence=1.0,
        feedback_md=(
            f"Correct — option {expected}." if correct else f"The expected answer is option {expected}."
        ),
    )


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
    resolution_status: str | None = None
    abstention_reason: str | None = None
    cause_scope: str | None = None
    target_ref: dict[str, Any] | None = None
    operation: str | None = None
    first_divergence: dict[str, Any] | None = None
    model_reported_localization_confidence: float | None = None
    model_reported_causal_confidence: float | None = None
    facet_contrast: dict[str, Any] | None = None
    candidate_causes: list[dict[str, Any]] | None = None
    postdictive_claims: list[dict[str, Any]] | None = None
    soft_postdictive_claims: list[str] | None = None


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
    diagnosis_md: str | None = None
    attribution_audit_events: list[dict[str, Any]] | None = None


# Deliberately stricter than canonical_projection.FAILURE_THRESHOLD (0.40).
# That threshold classifies the direction of evidence mass; this write barrier
# grants protection only after a clean, full-credit direct demonstration. Thus
# a 0.9 criterion contributes positive projection evidence but does not shield
# its facet from a simultaneously observed, specifically attributed failure.
FIREWALL_CLEAN_PASS_FRACTION = 1.0
FIREWALL_FRACTION_EPSILON = 1e-9


def _criterion_outcome_state(
    rubric: Rubric,
    criterion_points: Mapping[str, float],
) -> tuple[set[str], set[str]]:
    """Raw, dependency-localized criterion outcomes used by the P0 firewall."""

    outcomes = [
        CriterionOutcome(
            criterion_id=criterion.id,
            passed=(
                max(0.0, min(1.0, float(criterion_points.get(criterion.id, 0.0)) / criterion.points))
                >= FIREWALL_CLEAN_PASS_FRACTION - FIREWALL_FRACTION_EPSILON
                if criterion.points > 0
                else False
            ),
            depends_on=tuple(criterion.depends_on),
        )
        for criterion in rubric.criteria
        if criterion.id in criterion_points
    ]
    localized = localize_criterion_outcomes(outcomes)
    passed = {row.criterion_id for row in localized if row.assessable and row.passed}
    failed = {row.criterion_id for row in localized if row.assessable and not row.passed}
    return passed, failed


def _direct_criteria_by_facet(
    item: PracticeItem,
    rubric: Rubric,
    *,
    vault: LoadedVault | None = None,
) -> dict[str, set[str]]:
    """Criterion links eligible to protect a facet at the write barrier."""

    mapped = criterion_facet_weights_for_item(item, rubric)
    direct: dict[str, set[str]] = {}
    for criterion in rubric.criteria:
        status = getattr(criterion, "measurement_status", None)
        if status in {"supporting", "item_local", "no_canonical_facet"}:
            continue
        if criterion.targets:
            facets = [
                target.facet
                for target in criterion.targets
                if getattr(target, "role", "primary") == "primary"
            ]
        else:
            facets = [
                facet
                for facet, weight in (mapped.get(criterion.id) or {}).items()
                if float(weight) > 0
            ]
        for facet in facets:
            facet_id = (
                vault.canonical_facet_id(str(facet))
                if vault is not None
                else str(facet)
            )
            direct.setdefault(facet_id, set()).add(criterion.id)
    return direct


def enforce_passed_target_firewall(
    item: PracticeItem,
    rubric: Rubric,
    *,
    criterion_points: Mapping[str, float],
    error_attributions: Iterable[Any],
    repair_suggestions: Iterable[Mapping[str, Any]] = (),
    vault: LoadedVault | None = None,
) -> tuple[list[Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Strip negative/repair targets protected by raw criterion outcomes.

    This is deliberately called again at the attempt write boundary even when
    Codex validation already called it. That makes the safety invariant hold
    for self grades, replay inputs, and hand-constructed ResolvedGrade objects.
    """

    passed, failed = _criterion_outcome_state(rubric, criterion_points)
    direct = _direct_criteria_by_facet(item, rubric, vault=vault)
    protected_facets = {
        facet
        for facet, criterion_ids in direct.items()
        if criterion_ids and criterion_ids <= passed
    }
    audit: list[dict[str, Any]] = []
    filtered_attributions: list[Any] = []
    for index, attribution in enumerate(error_attributions):
        raw_facets = list(getattr(attribution, "target_evidence_families", None) or [])
        raw_criteria = list(getattr(attribution, "target_criterion_ids", None) or [])
        facets = [facet for facet in raw_facets if facet not in protected_facets]
        criteria = [criterion for criterion in raw_criteria if criterion not in passed]
        target_ref = getattr(attribution, "target_ref", None)
        facet_contrast = getattr(attribution, "facet_contrast", None)
        blocked_ref_target: str | None = None
        if isinstance(target_ref, Mapping):
            ref_kind = target_ref.get("kind")
            if (
                ref_kind == "facet_capability"
                and str(target_ref.get("facet_id") or "") in protected_facets
            ):
                blocked_ref_target = str(target_ref.get("facet_id"))
                target_ref = {"kind": "none"}
            elif (
                ref_kind == "criterion"
                and str(target_ref.get("criterion_id") or "") in passed
            ):
                blocked_ref_target = str(target_ref.get("criterion_id"))
                target_ref = {"kind": "none"}
        blocked_contrast_targets: list[str] = []
        if isinstance(facet_contrast, Mapping):
            blocked_contrast_targets = [
                str(facet_contrast.get(key) or "")
                for key in ("target_facet", "confused_with_facet")
                if str(facet_contrast.get(key) or "") in protected_facets
            ]
            if blocked_contrast_targets:
                facet_contrast = None
        for facet in raw_facets:
            if facet in protected_facets:
                audit.append(
                    {
                        "kind": "passed_facet_write_blocked",
                        "source": "error_attribution",
                        "attribution_index": index,
                        "target": facet,
                        "passed_criteria": sorted(direct.get(facet, set()) & passed),
                    }
                )
        for criterion in raw_criteria:
            if criterion in passed:
                audit.append(
                    {
                        "kind": "passed_criterion_write_blocked",
                        "source": "error_attribution",
                        "attribution_index": index,
                        "target": criterion,
                    }
                )
        if blocked_ref_target is not None:
            audit.append(
                {
                    "kind": "passed_typed_target_write_blocked",
                    "source": "error_attribution",
                    "attribution_index": index,
                    "target": blocked_ref_target,
                }
            )
        for target in blocked_contrast_targets:
            audit.append(
                {
                    "kind": "passed_facet_write_blocked",
                    "source": "facet_contrast",
                    "attribution_index": index,
                    "target": target,
                    "passed_criteria": sorted(direct.get(target, set()) & passed),
                }
            )
        resolution_status = getattr(attribution, "resolution_status", None)
        if (
            resolution_status == "resolved"
            and not facets
            and not criteria
            and (
                not isinstance(target_ref, Mapping)
                or target_ref.get("kind") == "none"
            )
        ):
            resolution_status = "unresolved"
        filtered_attributions.append(
            replace(
                attribution,
                target_evidence_families=facets,
                target_criterion_ids=criteria,
                target_ref=target_ref,
                facet_contrast=facet_contrast,
                resolution_status=resolution_status,
            )
        )

    filtered_repairs: list[dict[str, Any]] = []
    for index, raw in enumerate(repair_suggestions):
        suggestion = dict(raw)
        raw_facets = [
            (
                vault.canonical_facet_id(str(value))
                if vault is not None
                else str(value)
            )
            for value in suggestion.get("target_evidence_families") or []
        ]
        raw_criteria = [str(value) for value in suggestion.get("target_criterion_ids") or []]
        suggestion["target_evidence_families"] = [
            facet for facet in raw_facets if facet not in protected_facets
        ]
        if "target_criterion_ids" in suggestion or raw_criteria:
            suggestion["target_criterion_ids"] = [
                criterion for criterion in raw_criteria if criterion not in passed
            ]
        for facet in raw_facets:
            if facet in protected_facets:
                audit.append(
                    {
                        "kind": "passed_facet_write_blocked",
                        "source": "repair_suggestion",
                        "suggestion_index": index,
                        "target": facet,
                        "passed_criteria": sorted(direct.get(facet, set()) & passed),
                    }
                )
        for criterion in raw_criteria:
            if criterion in passed:
                audit.append(
                    {
                        "kind": "passed_criterion_write_blocked",
                        "source": "repair_suggestion",
                        "suggestion_index": index,
                        "target": criterion,
                    }
                )
        filtered_repairs.append(suggestion)
    return filtered_attributions, filtered_repairs, audit


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
        trace_contract=(
            item.trace_contract.model_dump(mode="json", exclude_none=True)
            if item.trace_contract is not None
            else None
        ),
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
        "trace_contract": context.trace_contract,
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
    machine_review_scopes: set[str] = set()
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

        target_ref = (
            attribution.target_ref.model_dump(mode="json", exclude_none=True)
            if attribution.target_ref is not None
            else None
        )
        if target_ref and target_ref.get("kind") == "facet_capability":
            raw_facet = str(target_ref.get("facet_id") or "")
            canonical = vault.canonical_facet_id(raw_facet)
            if canonical not in known_facets:
                unknown_target_families.add(raw_facet)
                target_ref = {"kind": "none"}
            else:
                target_ref["facet_id"] = canonical
        elif target_ref and target_ref.get("kind") == "criterion":
            criterion_id = str(target_ref.get("criterion_id") or "")
            if criterion_id not in criteria:
                unknown_target_criteria.add(criterion_id)
                target_ref = {"kind": "none"}
        elif target_ref and target_ref.get("kind") == "item_step":
            checkpoint_id = str(target_ref.get("checkpoint_id") or "")
            recipe_id = target_ref.get("recipe_id")
            recipes = (
                {
                    recipe.id: set(recipe.checkpoints)
                    for recipe in item.trace_contract.recipes
                }
                if item.trace_contract is not None
                and item.trace_contract.status == "available"
                else {}
            )
            if not recipes:
                raise GradingValidationError(
                    "item-step target requires an available item trace contract"
                )
            if recipe_id is not None:
                if str(recipe_id) not in recipes:
                    raise GradingValidationError(
                        f"Unknown item-step recipe {recipe_id}"
                    )
                checkpoint_known = checkpoint_id in recipes[str(recipe_id)]
            else:
                checkpoint_known = any(
                    checkpoint_id in checkpoints
                    for checkpoints in recipes.values()
                )
            if not checkpoint_known:
                raise GradingValidationError(
                    f"Unknown item-step checkpoint {checkpoint_id}"
                )
        elif target_ref and target_ref.get("kind") == "answer_span":
            quote = str(target_ref.get("quote") or "")
            answer = learner_answer_md or ""
            normalized_quote = " ".join(quote.split())
            normalized_answer = " ".join(answer.split())
            if quote not in answer and normalized_quote not in normalized_answer:
                raise GradingValidationError(
                    "answer-span target quote does not anchor in learner answer"
                )
            start = target_ref.get("char_start")
            end = target_ref.get("char_end")
            if (
                start is not None
                and end is not None
                and answer[int(start) : int(end)] != quote
            ):
                raise GradingValidationError(
                    "answer-span target offsets do not match learner answer"
                )

        first_divergence = (
            attribution.first_divergence.model_dump(mode="json", exclude_none=True)
            if attribution.first_divergence is not None
            else None
        )
        if first_divergence is not None:
            criterion_id = str(first_divergence.get("criterion_id") or "")
            if criterion_id not in criteria:
                raise GradingValidationError(
                    f"Unknown first_divergence criterion {criterion_id}"
                )
            anchor_kind = first_divergence.get("anchor_kind")
            quote = first_divergence.get("quote")
            answer = learner_answer_md or ""
            if anchor_kind == "span" and not quote:
                raise GradingValidationError("span first_divergence requires quote")
            if anchor_kind == "missing_required_step":
                checkpoint_id = str(first_divergence.get("checkpoint_id") or "")
                known_checkpoints = {
                    checkpoint
                    for recipe in (item.trace_contract.recipes if item.trace_contract else [])
                    for checkpoint in recipe.checkpoints
                }
                if not known_checkpoints:
                    raise GradingValidationError(
                        "missing_required_step requires an available item trace contract"
                    )
                if checkpoint_id not in known_checkpoints:
                    raise GradingValidationError(
                        f"Unknown first-divergence checkpoint {checkpoint_id}"
                    )
            if quote:
                normalized_quote = " ".join(str(quote).split())
                normalized_answer = " ".join(answer.split())
                if str(quote) not in answer and normalized_quote not in normalized_answer:
                    raise GradingValidationError(
                        "first_divergence quote does not anchor in learner answer"
                    )
                first_divergence["normalized_quote"] = normalized_quote
                first_divergence["quote_hash"] = hashlib.sha256(
                    str(quote).encode("utf-8")
                ).hexdigest()
                start = first_divergence.get("char_start")
                end = first_divergence.get("char_end")
                if start is not None and end is not None and answer[int(start) : int(end)] != quote:
                    raise GradingValidationError(
                        "first_divergence offsets do not match learner answer"
                    )

        facet_contrast = (
            attribution.facet_contrast.model_dump(mode="json", exclude_none=True)
            if attribution.facet_contrast is not None
            else None
        )
        if facet_contrast is not None:
            for key in ("target_facet", "confused_with_facet"):
                raw_facet = str(facet_contrast[key])
                canonical = vault.canonical_facet_id(raw_facet)
                if canonical not in known_facets:
                    unknown_target_families.add(raw_facet)
                facet_contrast[key] = canonical

        candidate_causes: list[dict[str, Any]] = []
        for cause in attribution.candidate_causes:
            payload = cause.model_dump(mode="json", exclude_none=True)
            ref = payload.get("target_ref")
            if isinstance(ref, dict) and ref.get("kind") == "facet_capability":
                raw_facet = str(ref.get("facet_id") or "")
                canonical = vault.canonical_facet_id(raw_facet)
                if canonical not in known_facets:
                    unknown_target_families.add(raw_facet)
                    ref = {"kind": "none"}
                    payload["target_ref"] = ref
                else:
                    ref["facet_id"] = canonical
            candidate_causes.append(payload)
        postdictive_claims = [
            claim.model_dump(mode="json", exclude_none=True)
            for claim in attribution.postdictive_claims
        ]
        unknown_claim_criteria = sorted(
            {
                str(claim.get("criterion_id") or "")
                for claim in postdictive_claims
                if claim.get("criterion_id") not in criteria
            }
        )
        if unknown_claim_criteria:
            raise GradingValidationError(
                "Unknown postdictive criterion " + ", ".join(unknown_claim_criteria)
            )

        resolution_status = attribution.resolution_status
        if resolution_status is None:
            # Compatibility for stored/provider payloads predating P0b. New
            # strict-schema responses always carry the explicit field.
            resolution_status = (
                "resolved"
                if target_evidence_families
                or target_criterion_ids
                or (target_ref is not None and target_ref.get("kind") != "none")
                else "unresolved"
            )
        if (
            resolution_status == "resolved"
            and not target_evidence_families
            and not target_criterion_ids
            and (target_ref is None or target_ref.get("kind") == "none")
        ):
            raise GradingValidationError("resolved attribution requires a target")

        named_facets = set(target_evidence_families)
        if target_ref and target_ref.get("kind") == "facet_capability":
            named_facets.add(str(target_ref.get("facet_id") or ""))
        if facet_contrast is not None:
            named_facets.update(
                {
                    str(facet_contrast["target_facet"]),
                    str(facet_contrast["confused_with_facet"]),
                }
            )
        for cause in candidate_causes:
            cause_ref = cause.get("target_ref")
            if isinstance(cause_ref, dict) and cause_ref.get("kind") == "facet_capability":
                named_facets.add(str(cause_ref.get("facet_id") or ""))
        if named_facets:
            diagnosis = (proposal.diagnosis_md or "").casefold()
            for facet in named_facets:
                record = vault.evidence_facets.get(facet)
                anchors = [
                    facet,
                    getattr(record, "title", None),
                    getattr(record, "claim", None),
                ]
                if not any(
                    str(anchor).casefold() in diagnosis
                    for anchor in anchors
                    if anchor
                ):
                    raise GradingValidationError(
                        f"facet {facet} is not anchored in diagnosis_md"
                    )

        cause_scope = attribution.cause_scope or "unknown"
        if cause_scope in {"item_contract", "grader_interpretation"}:
            machine_review_scopes.add(cause_scope)
        learner_state_write = (
            attribution.is_misconception
            and cause_scope not in {"item_contract", "grader_interpretation"}
        )
        validated_errors.append(
            ValidatedErrorAttribution(
                error_type=error_type,
                severity=_resolved_error_severity(vault, error_type, attribution.severity),
                evidence=attribution.evidence,
                is_misconception=learner_state_write,
                misconception_statement=attribution.misconception_statement,
                misconception_consistent_answer=attribution.misconception_consistent_answer,
                target_evidence_families=target_evidence_families,
                target_criterion_ids=target_criterion_ids,
                resolution_status=resolution_status,
                abstention_reason=attribution.abstention_reason,
                cause_scope=cause_scope,
                target_ref=target_ref,
                operation=attribution.operation,
                first_divergence=first_divergence,
                model_reported_localization_confidence=attribution.localization_confidence,
                model_reported_causal_confidence=attribution.causal_confidence,
                facet_contrast=facet_contrast,
                candidate_causes=candidate_causes,
                postdictive_claims=postdictive_claims,
                soft_postdictive_claims=list(attribution.soft_postdictive_claims),
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
        target_criterion_ids: list[str] = []
        for raw_criterion_id in suggestion.target_criterion_ids:
            if raw_criterion_id not in criteria:
                unknown_target_criteria.add(raw_criterion_id)
            elif raw_criterion_id not in target_criterion_ids:
                target_criterion_ids.append(raw_criterion_id)
        payload = suggestion.model_dump(mode="json")
        payload["target_evidence_families"] = target_evidence_families
        if target_criterion_ids or "target_criterion_ids" in suggestion.model_fields_set:
            payload["target_criterion_ids"] = target_criterion_ids
        else:
            payload.pop("target_criterion_ids", None)
        validated_repair_suggestions.append(payload)

    criterion_points = {
        evidence.criterion_id: evidence.points_awarded for evidence in validated_evidence
    }
    validated_errors, validated_repair_suggestions, attribution_audit_events = (
        enforce_passed_target_firewall(
            item,
            rubric,
            criterion_points=criterion_points,
            error_attributions=validated_errors,
            repair_suggestions=validated_repair_suggestions,
            vault=vault,
        )
    )
    manual_review_reason = "codex_manual_review" if proposal.manual_review_recommended else None
    if manual_review_reason is None and proposal.grader_confidence < 0.4:
        manual_review_reason = "low_grader_confidence"
    if manual_review_reason is None and unknown_target_families:
        manual_review_reason = "unknown_target_evidence_family:" + ",".join(sorted(unknown_target_families))
    if manual_review_reason is None and unknown_target_criteria:
        manual_review_reason = "unknown_target_criterion:" + ",".join(sorted(unknown_target_criteria))
    if manual_review_reason is None and machine_review_scopes:
        manual_review_reason = "attribution_scope:" + ",".join(sorted(machine_review_scopes))
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
        diagnosis_md=proposal.diagnosis_md,
        attribution_audit_events=attribution_audit_events,
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


def causal_attribution_audit_report(repository: Any) -> dict[str, Any]:
    """CLI-facing fill/abstention/firewall telemetry grouped by prompt+model."""

    groups: dict[tuple[str, str], dict[str, Any]] = {}
    for attempt in repository.list_all_attempts():
        debug = repository.attempt_debug_payload(str(attempt["id"])) or {}
        telemetry = debug.get("causal_attribution")
        if not isinstance(telemetry, dict):
            continue
        metadata = repository.fetch_attempt_feedback_metadata(str(attempt["id"])) or {}
        run = (
            repository.agent_run(str(metadata["agent_run_id"]))
            if metadata.get("agent_run_id")
            else None
        )
        prompt_version = str(telemetry.get("prompt_version") or "unknown")
        model = str((run or {}).get("model") or "unknown")
        group = groups.setdefault(
            (prompt_version, model),
            {
                "prompt_version": prompt_version,
                "model": model,
                "attempts": 0,
                "attributions": 0,
                "resolution_counts": {
                    "resolved": 0,
                    "unresolved": 0,
                    "abstained": 0,
                },
                "facet_target_fill_count": 0,
                "criterion_target_fill_count": 0,
                "firewall_trigger_count": 0,
                "judgment_fill_counts": {},
            },
        )
        group["attempts"] += 1
        group["attributions"] += int(telemetry.get("attribution_count") or 0)
        for status in group["resolution_counts"]:
            group["resolution_counts"][status] += int(
                (telemetry.get("resolution_counts") or {}).get(status) or 0
            )
        group["facet_target_fill_count"] += int(
            telemetry.get("facet_target_fill_count") or 0
        )
        group["criterion_target_fill_count"] += int(
            telemetry.get("criterion_target_fill_count") or 0
        )
        group["firewall_trigger_count"] += len(telemetry.get("firewall_events") or [])
        for field, count in (telemetry.get("judgment_fill_counts") or {}).items():
            fills = group["judgment_fill_counts"]
            fills[str(field)] = int(fills.get(str(field)) or 0) + int(count or 0)
    return {"groups": [groups[key] for key in sorted(groups)]}


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
            "Name a facet only when the failed step exercises that facet's claim. "
            "Prefer a failed criterion, item step, answer span, unresolved attribution, "
            "or reasoned abstention over stretching to the nearest listed facet. Passing "
            "criteria are positive evidence and cannot be negative or repair targets."
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

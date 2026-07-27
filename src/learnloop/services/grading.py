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
from learnloop.services.discrimination_profiles import (
    item_profiles,
    profile_prior_payload,
    validate_profile_match,
)
from learnloop.services.error_hunt import (
    suppress_facet_failures_on_clean_solution,
    validate_error_hunt_report,
)
from learnloop.services.recall_coverage import criterion_facet_weights_for_item, resolve_coverage
from learnloop.vault.models import (
    LoadedVault,
    PracticeItem,
    Rubric,
    learning_object_facet_union,
)


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
    # Aug C3: harness-owned agreement across independent diagnosis calls.
    # This is never a GradingProposal field, so the model cannot award itself
    # support.  The attempt service attaches it after proposal validation.
    diagnostic_sample_support: float | None = None
    facet_contrast: dict[str, Any] | None = None
    candidate_causes: list[dict[str, Any]] | None = None
    postdictive_claims: list[dict[str, Any]] | None = None
    soft_postdictive_claims: list[str] | None = None
    # Meas §3.A3 / §10: why this attribution's facet targets were cleared, when
    # they were. An emptied target list is indistinguishable from a list the
    # grader never filled, and the projection's single-target fallback reads that
    # silence as "attribute the whole failure to the criterion's own target" —
    # which is exactly the facet failure the clean-solution guard exists to
    # prevent. The reason has to travel with the attribution or the guard stops
    # at the attribution channel and never reaches the ledger.
    facet_write_blocked: str | None = None


@dataclass(frozen=True)
class ValidatedExercisedFacet:
    """One accepted A6 trace observation (Meas §3.A6).

    ``observation_scope`` is derived, never reported: ``declared`` when the facet
    is already in the item's contract (the grader confirming what the item meant
    to measure) and ``opportunistic`` when it is not. A6's revert criterion —
    "opportunistic credit concentrates on a few facets" — is a statement about
    the second population only, so the two must stay separable.
    """

    facet: str
    evidence: str
    observation_scope: str
    criterion_id: str | None = None


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
    exercised_facets: list[ValidatedExercisedFacet] | None = None
    clarification: dict[str, Any] | None = None
    # Meas §3.A5: which authored candidate profile the trace matched, or the
    # first-class rejection. Always present on a graded attempt (the harness
    # supplies the `no_profiles_offered` arm itself), because the revert
    # criterion needs a denominator that includes the items nobody profiled.
    discrimination_profile_match: dict[str, Any] | None = None
    # Meas §3.A3: what the learner repaired in a worked solution, and — on the
    # clean rotation — whether a facet write was suppressed. `None` on every item
    # that is not an error hunt, so the A3 population stays countable.
    error_hunt: dict[str, Any] | None = None


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
        facet_registry=_grading_facet_registry(vault, item),
        # Meas §3.A5: the item's authored candidate causes, as a PRIOR. Empty for
        # an item that authors none, and the prompt's profile paragraph is
        # conditioned on the list being non-empty, so a grader is never shown a
        # candidate set that does not exist.
        discrimination_profiles=profile_prior_payload(item_profiles(item)),
        # Meas §3.A3: the worked solution the learner was asked to repair. The
        # plants are deliberately withheld — see the field's note on
        # `codex.client.GradingContext`.
        error_hunt_solution=(
            item.error_hunt.worked_solution_md if item.error_hunt is not None else None
        ),
    )


def _grading_facet_registry(vault: LoadedVault, item: PracticeItem) -> list[dict[str, str]]:
    """Facets A6 may report as exercised, with the claim each one names.

    Scoped to the item's learning object: the union of every facet its
    blueprints reference, which is the set whose cells the LO's contract can
    actually close. Offering the grader the whole subject vocabulary would be
    unbounded token cost per grading call and an invitation to pattern-match,
    which is exactly the behaviour A6's revert criterion watches for.

    The claim text travels with the id because a bare slug is not enough to
    decide whether a trace exercises a facet — the whole point of the channel is
    that the model is reading work against a claim, not matching a name.
    """

    learning_object = vault.learning_objects.get(item.learning_object_id)
    if learning_object is None:
        return []
    registry: list[dict[str, str]] = []
    for facet_id in learning_object_facet_union(learning_object):
        canonical = vault.canonical_facet_id(str(facet_id))
        facet = (vault.evidence_facets or {}).get(canonical)
        if facet is None:
            continue
        registry.append(
            {"id": canonical, "claim": str(getattr(facet, "claim", "") or "")}
        )
    return registry


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
        "facet_registry": context.facet_registry,
        "discrimination_profiles": context.discrimination_profiles,
        "clarification_exchange": context.clarification_exchange,
        "error_hunt_solution": context.error_hunt_solution,
        "verifier_observations": context.verifier_observations,
        "diagnostic_history": context.diagnostic_history,
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
        structural_refs: dict[str, list[dict[str, Any]]] = {
            "target_refs": [],
            "preserve_refs": [],
        }
        for field_name, raw_refs in (
            ("target_refs", suggestion.target_refs),
            ("preserve_refs", suggestion.preserve_refs),
        ):
            for raw_ref in raw_refs:
                ref = raw_ref.model_dump(mode="json", exclude_none=True)
                if ref.get("kind") == "facet_capability":
                    raw_facet = str(ref.get("facet_id") or "")
                    canonical = vault.canonical_facet_id(raw_facet)
                    if canonical not in known_facets:
                        unknown_target_families.add(raw_facet)
                        continue
                    ref["facet_id"] = canonical
                elif ref.get("kind") == "criterion":
                    criterion_id = str(ref.get("criterion_id") or "")
                    if criterion_id not in criteria:
                        unknown_target_criteria.add(criterion_id)
                        continue
                structural_refs[field_name].append(ref)
        for field_name, refs in structural_refs.items():
            if refs or field_name in suggestion.model_fields_set:
                payload[field_name] = refs
            else:
                payload.pop(field_name, None)
        for field_name in (
            "operator",
            "expected_minutes",
            "answer_reveal_budget",
            "repaired_trace",
            "verification_request",
        ):
            if field_name not in suggestion.model_fields_set:
                payload.pop(field_name, None)
        repaired_trace = payload.get("repaired_trace")
        if isinstance(repaired_trace, dict):
            learner_prefix = str(
                repaired_trace.get("learner_work_prefix") or ""
            )
            answer = learner_answer_md or ""
            if learner_prefix and not answer.startswith(learner_prefix):
                raise GradingValidationError(
                    "repaired-trace learner_work_prefix is not verbatim learner work"
                )
            repaired_answer = str(
                repaired_trace.get("repaired_answer_md") or ""
            )
            if learner_prefix and not repaired_answer.startswith(learner_prefix):
                raise GradingValidationError(
                    "repaired trace does not preserve learner_work_prefix"
                )
            known_checkpoints = {
                checkpoint
                for recipe in (
                    item.trace_contract.recipes
                    if item.trace_contract is not None
                    and item.trace_contract.status == "available"
                    else []
                )
                for checkpoint in recipe.checkpoints
            }
            unknown_changed = sorted(
                {
                    str(value)
                    for value in repaired_trace.get(
                        "changed_checkpoint_ids"
                    )
                    or []
                    if str(value) not in known_checkpoints
                }
            )
            if unknown_changed:
                raise GradingValidationError(
                    "Unknown repaired-trace checkpoint "
                    + ", ".join(unknown_changed)
                )
            insertion = repaired_trace.get("repair_insertion_point")
            if isinstance(insertion, dict):
                criterion_id = str(insertion.get("criterion_id") or "")
                if criterion_id not in criteria:
                    raise GradingValidationError(
                        f"Unknown repaired-trace criterion {criterion_id}"
                    )
                quote = insertion.get("quote")
                answer = learner_answer_md or ""
                if quote and str(quote) not in answer and " ".join(
                    str(quote).split()
                ) not in " ".join(answer.split()):
                    raise GradingValidationError(
                        "repaired-trace insertion quote does not anchor in learner answer"
                    )
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
    from learnloop.services.causal_attribution import (
        validate_repair_candidate,
    )

    for suggestion in validated_repair_suggestions:
        # The item's authored decomposition travels with the validation so a
        # `changed_checkpoint_ids` entry naming no real recipe step is rejected
        # as `unverifiable_checkpoint_claim` where it enters the system, rather
        # than silently degrading the backtracking-depth term downstream.
        suggestion["repair_validation"] = validate_repair_candidate(
            suggestion,
            expected_answer=item.expected_answer,
            trace_contract=item.trace_contract,
        ).as_dict()
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

    validated_exercised = _validated_exercised_facets(vault, item, rubric, proposal)
    clarification = _validated_clarification(
        proposal, validated_evidence, validated_errors, rubric
    )
    if clarification is not None and manual_review_reason is None:
        # Meas §3.A8: the grade is `provisional_pending_clarification` until the
        # learner answers or the question times out. There is no separate grade
        # -state column and adding one would put the state where the existing
        # review surfaces cannot see it; `manual_review_reason` is already how
        # every other "this grade is not final" state is expressed
        # (`codex_manual_review`, `low_grader_confidence`, `attribution_scope:*`),
        # so this joins that vocabulary rather than starting a second one.
        # Deliberately does NOT override an existing reason: a grade that already
        # needs a human is not made less so by also asking the learner.
        manual_review_reason = PROVISIONAL_PENDING_CLARIFICATION

    # Meas §3.A5. Always resolved, never conditional on the item authoring
    # profiles: the harness supplies the `no_profiles_offered` arm itself, and a
    # rejection rate whose denominator silently excluded unprofiled items would
    # be measuring authoring coverage rather than the diagnostician's behaviour.
    profile_match = validate_profile_match(item, proposal)
    # Meas §3.A3. `None` for every item that is not an error hunt.
    hunt = validate_error_hunt_report(item, proposal)
    # §10: "a clean-solution error-hunt on which the learner reports an error
    # writes a misconception candidate, not a facet failure." Runs AFTER the
    # passed-facet firewall above, deliberately: the two guards block different
    # writes for different reasons (that one protects a facet the learner
    # demonstrated; this one protects a facet they were never observed
    # exercising), and running this first would leave the firewall auditing
    # attributions this had already emptied.
    validated_errors, validated_repair_suggestions, hunt = (
        suppress_facet_failures_on_clean_solution(
            hunt, validated_errors, validated_repair_suggestions
        )
    )
    if hunt is not None:
        attribution_audit_events = list(attribution_audit_events or []) + [
            dict(event) for event in hunt.suppression_events
        ]

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
        exercised_facets=validated_exercised,
        clarification=clarification,
        discrimination_profile_match=profile_match.as_dict(),
        error_hunt=hunt.as_dict() if hunt is not None else None,
    )


#: Meas §3.A6 revert criterion: "opportunistic credit concentrates on a few
#: facets, which indicates the grader is pattern-matching the vocabulary rather
#: than reading the work." A per-attempt cap is the cheap half of that watch —
#: an attempt reporting a dozen exercised facets is describing the syllabus, not
#: the trace. Excess observations are dropped in the grader's own order, which
#: is the only ranking available; the drop is not recorded, because the standing
#: watch is `trace_evidence_report`'s concentration statistic over what WAS
#: accepted, and a grader that reports a dozen facets an attempt shows up there
#: regardless of where the list was cut.
MAX_EXERCISED_FACETS_PER_ATTEMPT = 6


def _validated_exercised_facets(
    vault: LoadedVault,
    item: PracticeItem,
    rubric: Rubric,
    proposal: Any,
) -> list[ValidatedExercisedFacet]:
    """Accept A6 trace observations that name a registered facet with a citation.

    Deliberately *stricter* than the attribution channel's known-facet set. An
    attribution target must already be in the item's contract; an A6 observation
    is by definition allowed to name a facet the item never declared — that is
    the whole channel. The gate that replaces it is registry membership: the
    facet must exist in the vault's canonical vocabulary, because crediting an
    id nothing else in the system knows about would file evidence into a cell no
    contract, report or grid ever reads.

    An observation naming an unregistered facet is dropped rather than raised,
    and deliberately leaves no record. It is a *bonus* channel — taking a graded
    attempt down because the grader invented a facet id would trade a real
    measurement for a cosmetic one — and it is not a missing-vocabulary signal
    either: the grader is handed ``context.facet_registry`` and told to pick from
    it, so naming something outside is a model error against a closed list, not
    the vocabulary failing to name what the learner did. A5's note store exists
    for the latter and would be diluted by the former.
    """

    raw = list(getattr(proposal, "exercised_facets", None) or [])
    if not raw:
        return []
    declared = {vault.canonical_facet_id(str(facet)) for facet in item.evidence_facets}
    declared.update(
        vault.canonical_facet_id(str(target.facet))
        for criterion in rubric.criteria
        for target in criterion.targets
    )
    registered = set(vault.evidence_facets or ())
    criterion_ids = {criterion.id for criterion in rubric.criteria}
    accepted: list[ValidatedExercisedFacet] = []
    seen: set[str] = set()
    for observation in raw:
        facet = vault.canonical_facet_id(str(getattr(observation, "facet", "") or ""))
        evidence = str(getattr(observation, "evidence", "") or "").strip()
        if not facet or not evidence:
            continue
        # On a vault with no facet registry at all (legacy content) there is
        # nothing to check against, so registry membership cannot be required —
        # the same abstention `unregistered_facet_errors` callers already make.
        if registered and facet not in registered:
            continue
        if facet in seen:
            continue
        seen.add(facet)
        criterion_id = getattr(observation, "criterion_id", None)
        accepted.append(
            ValidatedExercisedFacet(
                facet=facet,
                evidence=evidence,
                observation_scope="declared" if facet in declared else "opportunistic",
                criterion_id=(
                    str(criterion_id) if criterion_id and str(criterion_id) in criterion_ids else None
                ),
            )
        )
    return accepted[:MAX_EXERCISED_FACETS_PER_ATTEMPT]


#: The `manual_review_reason` tag that means "this grade is provisional until a
#: clarification resolves or times out" (Meas §3.A8's `provisional_pending_clarification`
#: grade state). Joins the existing string vocabulary in that field rather than
#: introducing a second state channel the review surfaces cannot see.
PROVISIONAL_PENDING_CLARIFICATION = "provisional_pending_clarification"

#: Grader confidence at or above which no clarification may be asked. Shares the
#: 0.40 hedge threshold every other surface uses (`grade_resolution`,
#: `grade_classifier`, the `low_grader_confidence` review tag) so "hedged" means
#: one thing in this vault.
CLARIFICATION_CONFIDENCE_CEILING = 0.40


def _validated_clarification(
    proposal: Any,
    validated_evidence: list[ValidatedCriterionEvidence],
    validated_errors: list[ValidatedErrorAttribution],
    rubric: Rubric | None = None,
) -> dict[str, Any] | None:
    """Accept a clarification request only against a grade that is already unsure.

    §3.A8's bound, and the one that keeps the channel from becoming an
    interrogation: *never on a confident grade*. Three licensing signals, each
    recorded as the ``trigger`` so the rate can later be decomposed by which kind
    of uncertainty is actually driving it:

    * ``hedged_criterion`` — the named criterion carries
      ``learner_confidence='hedged'`` **and the grade on it is not confident**.
      That conjunction is §10's line ("a confidently-graded criterion never
      triggers a clarification") and it is not redundant:
      ``learner_confidence`` describes how confident the *learner* sounded, not
      how sure the *grader* is, so on its own it would license a question about
      a criterion awarded full credit at grader confidence 0.99 — an
      interrogation, which is exactly what §3.A8's bound forbids. "Not
      confident" is read two ways, either of which suffices: overall grader
      confidence below the shared hedge threshold, or the criterion itself short
      of full credit (a partially-credited step is a grade with something left
      unresolved, which is the "correct answer possibly reached by invalid
      reasoning" shape A8 exists for);
    * ``abstained_attribution`` — some attribution is ``abstained`` with a
      reason (the case A8 exists for: an abstention repairable by one question);
    * ``low_grader_confidence`` — overall grader confidence below the shared
      0.40 hedge threshold.

    A request with none of these is dropped, silently and deliberately: raising
    would fail an otherwise valid grade over a bonus channel, and the model
    asking an unlicensed question is a prompt problem, not a data problem. The
    drop is observable — ``clarification_rate`` counts what was *accepted*, so a
    model that over-asks shows up as a flat rate rather than an inflated one.
    """

    request = getattr(proposal, "clarification_request", None)
    if request is None:
        return None
    question = str(getattr(request, "question_md", "") or "").strip()
    if not question:
        return None
    criterion_id = getattr(request, "criterion_id", None)
    criterion_id = str(criterion_id) if criterion_id else None
    grader_confidence = float(getattr(proposal, "grader_confidence", 1.0))
    max_points = {
        criterion.id: float(criterion.points)
        for criterion in (rubric.criteria if rubric is not None else ())
    }

    def _grade_is_unsure(evidence: ValidatedCriterionEvidence) -> bool:
        if grader_confidence < CLARIFICATION_CONFIDENCE_CEILING:
            return True
        ceiling = max_points.get(evidence.criterion_id)
        return ceiling is not None and evidence.points_awarded < ceiling - 1e-9

    hedged = {
        evidence.criterion_id
        for evidence in validated_evidence
        if evidence.learner_confidence == "hedged" and _grade_is_unsure(evidence)
    }
    abstained = any(
        attribution.resolution_status == "abstained" and attribution.abstention_reason
        for attribution in validated_errors
    )
    if criterion_id is not None and criterion_id in hedged:
        trigger = "hedged_criterion"
    elif abstained:
        trigger = "abstained_attribution"
        # An attribution-level abstention is not scoped to one criterion, so a
        # criterion id offered alongside it is dropped rather than trusted:
        # attaching the question to a criterion the grader did not hedge would
        # invent the scope.
        if criterion_id is not None and criterion_id not in hedged:
            criterion_id = None
    elif grader_confidence < CLARIFICATION_CONFIDENCE_CEILING:
        trigger = "low_grader_confidence"
    else:
        return None
    return {
        "question_md": question,
        "reason": str(getattr(request, "reason", "other") or "other"),
        "criterion_id": criterion_id,
        "trigger": trigger,
    }


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
                # Meas §3.A5. The profile channel is a fill/abstention channel of
                # exactly the kind this report already watches, so it is grouped
                # by the same (prompt_version, model) key rather than reported
                # somewhere else — `no_profile_applies` is this channel's
                # abstention arm, and standing constraint 2 says watch both tails
                # of it. `discrimination_profile_rejection_rate` computes the rate
                # itself off the durable store; these are the raw counts, visible
                # from the CLI a reader already runs.
                "discrimination_profile_counts": {},
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
        # Read from the DURABLE store, not from the debug payload beside it.
        # `rebuild-derived-state` re-derives the payload from the persisted grade,
        # which carries no profile report (there is no provider on the replay
        # path), so a payload-sourced count would silently zero itself on the next
        # rebuild — exactly the failure migration 141 called out for A6's raw log.
        # The debug payload keeps its per-attempt copy for readability; this is
        # the one that has to survive.
        profile_row = repository.discrimination_profile_match(str(attempt["id"]))
        if profile_row is not None:
            tally = group["discrimination_profile_counts"]
            arm = str(profile_row.get("outcome") or "")
            tally[arm] = int(tally.get(arm) or 0) + 1
    # Present every arm on every group, at zero when unseen: a tail that vanishes
    # from the report when it is empty cannot be watched, and "collapsed toward
    # zero" is precisely the tail §3.A5 asks readers to watch.
    from learnloop.services.discrimination_profiles import ProfileMatchOutcome

    for group in groups.values():
        for arm in ProfileMatchOutcome:
            group["discrimination_profile_counts"].setdefault(str(arm), 0)
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

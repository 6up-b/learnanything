from __future__ import annotations

import re
from dataclasses import dataclass
from math import exp
from typing import Any, Iterable, Mapping

from learnloop.config import EvidenceConfig, LearnLoopConfig
from learnloop.db.repositories import MasteryState, Repository
from learnloop.numeric import clamp
from learnloop.services.error_taxonomy_map import map_legacy_error_type
from learnloop.services.evidence import (
    attempt_evidence_mass,
    attempt_surface_exposure,
    practice_mode_item_coverage,
)
from learnloop.services.mastery import display_mastery
from learnloop.vault.models import LoadedVault, PracticeItem, Rubric


@dataclass(frozen=True)
class CoverageResult:
    item_coverage: float
    effective_coverage: float
    covered_facets: dict[str, float]
    normalized_facet_weights: dict[str, float]
    trace: dict[str, Any]


@dataclass(frozen=True)
class ReliabilityResult:
    observation_reliability: float
    trace: dict[str, float]


@dataclass(frozen=True)
class FamiliarityResult:
    independent_evidence_discount: float
    trace: dict[str, float]


@dataclass(frozen=True)
class ErrorImpactResult:
    error_sharpening: float
    observation_weight: float
    trace: dict[str, float]


def resolve_coverage(
    item: PracticeItem,
    rubric: Rubric | None,
    *,
    attempt_type: str,
    hints_used: int,
    learner_answer_md: str,
    evidence: EvidenceConfig | None = None,
) -> CoverageResult:
    raw_facet_weights, item_coverage, source = _raw_coverage(item, rubric, evidence)
    normalized = _normalize(raw_facet_weights)
    hint_surface_factor = _hint_policy_product(
        item.hint_policy.coverage_surface_dampening_by_hint,
        hints_used,
        default=1.0,
    )
    response_engagement_factor = _response_engagement_factor(attempt_type, learner_answer_md)
    attempt_type_coverage_factor = attempt_surface_exposure(attempt_type, evidence)
    effective_item_coverage = clamp(
        item_coverage * hint_surface_factor * response_engagement_factor * attempt_type_coverage_factor
    )
    covered_facets = {
        facet: round(effective_item_coverage * weight, 12)
        for facet, weight in normalized.items()
        if weight > 0
    }
    effective_coverage = clamp(sum(covered_facets.values()))
    trace = {
        "source": source,
        "raw_item_coverage": item_coverage,
        "raw_facet_weights": raw_facet_weights,
        "normalized_facet_weights": normalized,
        "coverage_modifiers": {
            "hint_surface_factor": hint_surface_factor,
            "response_engagement_factor": response_engagement_factor,
            "attempt_type_coverage_factor": attempt_type_coverage_factor,
            "attempt_surface_exposure": attempt_type_coverage_factor,
        },
        "covered_facets": covered_facets,
        "effective_coverage": effective_coverage,
    }
    return CoverageResult(
        item_coverage=item_coverage,
        effective_coverage=effective_coverage,
        covered_facets=covered_facets,
        normalized_facet_weights=normalized,
        trace=trace,
    )


def scale_coverage_for_graded_criteria(
    coverage: CoverageResult,
    item: PracticeItem,
    rubric: Rubric | None,
    *,
    criterion_points: Mapping[str, float],
    transfer_evidence_multiplier: float = 1.0,
) -> CoverageResult:
    """Scale per-facet evidence mass by the graded (asked) criterion share.

    Two effects, both symmetric (they scale the facet evidence *mass*, so
    success and failure are discounted equally):

    - Criteria absent from ``criterion_points`` were never assessed (teach_back
      asks a subset of the rubric); the facet mass they would have certified is
      removed. A facet reachable only through ungraded criteria drops out of
      ``covered_facets`` entirely and contributes no evidence.
    - Graded criteria with rubric ``tier == "transfer"`` contribute their facet
      mass multiplied by ``transfer_evidence_multiplier`` (config, read at
      apply time so replay reproduces it).

    No-ops (bit-for-bit) when the rubric has no criteria, no criterion→facet
    mapping exists, ``criterion_points`` is empty (no criterion information:
    legacy behavior kept), or every criterion is graded and core-tier.
    """

    if rubric is None or not rubric.criteria or not criterion_points:
        return coverage
    mapping = criterion_facet_weights_for_item(item, rubric)
    if not mapping:
        return coverage
    graded = set(criterion_points)
    tiers = {criterion.id: getattr(criterion, "tier", "core") or "core" for criterion in rubric.criteria}
    all_graded = graded >= set(tiers)
    graded_has_transfer = any(tiers.get(criterion_id) == "transfer" for criterion_id in graded)
    if all_graded and not graded_has_transfer:
        return coverage

    max_points = max(float(rubric.max_points), 1.0)
    criteria = {criterion.id: criterion for criterion in rubric.criteria}
    numerator: dict[str, float] = {}
    denominator: dict[str, float] = {}
    for criterion_id, raw_map in mapping.items():
        criterion = criteria.get(criterion_id)
        if criterion is None:
            continue
        weights = {
            facet: max(0.0, float(weight))
            for facet, weight in raw_map.items()
            if facet in item.evidence_facets
        }
        total = sum(weights.values())
        if total <= 0:
            continue
        criterion_weight = float(criterion.points) / max_points
        multiplier = (
            clamp(transfer_evidence_multiplier) if tiers.get(criterion_id) == "transfer" else 1.0
        )
        for facet, weight in weights.items():
            share = weight / total
            denominator[facet] = denominator.get(facet, 0.0) + criterion_weight * share
            if criterion_id in graded:
                numerator[facet] = numerator.get(facet, 0.0) + criterion_weight * share * multiplier

    scales: dict[str, float] = {}
    for facet in coverage.covered_facets:
        den = denominator.get(facet, 0.0)
        if den <= 0:
            # Facet not reachable through any mapped criterion: no criterion
            # information, keep legacy full mass.
            scales[facet] = 1.0
        else:
            scales[facet] = max(0.0, numerator.get(facet, 0.0)) / den
    scaled_covered = {
        facet: round(mass * scales[facet], 12)
        for facet, mass in coverage.covered_facets.items()
        if mass * scales[facet] > 0
    }
    effective_coverage = clamp(sum(scaled_covered.values()))
    trace = dict(coverage.trace)
    trace["graded_criterion_scaling"] = {
        "graded_criteria": sorted(graded),
        "ungraded_criteria": sorted(set(tiers) - graded),
        "transfer_evidence_multiplier": clamp(transfer_evidence_multiplier),
        "facet_scales": {facet: scales[facet] for facet in sorted(scales)},
    }
    trace["covered_facets"] = scaled_covered
    trace["effective_coverage"] = effective_coverage
    return CoverageResult(
        item_coverage=coverage.item_coverage,
        effective_coverage=effective_coverage,
        covered_facets=scaled_covered,
        normalized_facet_weights=coverage.normalized_facet_weights,
        trace=trace,
    )


def resolve_reliability(
    item: PracticeItem,
    *,
    attempt_type: str,
    hints_used: int,
    grader_confidence: float,
    evidence: EvidenceConfig | None = None,
) -> ReliabilityResult:
    grader_confidence_factor = clamp(grader_confidence)
    hint_mastery_factor = _hint_policy_product(item.hint_policy.mastery_alpha_dampening_by_hint, hints_used, default=1.0)
    attempt_type_mastery_factor = attempt_evidence_mass(attempt_type, evidence)
    reliability = clamp(grader_confidence_factor * hint_mastery_factor * attempt_type_mastery_factor)
    trace = {
        "grader_confidence_factor": grader_confidence_factor,
        "hint_mastery_factor": hint_mastery_factor,
        "attempt_type_mastery_factor": attempt_type_mastery_factor,
        "attempt_evidence_mass": attempt_type_mastery_factor,
        "observation_reliability": reliability,
    }
    return ReliabilityResult(observation_reliability=reliability, trace=trace)


def derive_facet_outcomes(
    item: PracticeItem,
    rubric: Rubric,
    *,
    criterion_points: Mapping[str, float],
    covered_facets: Mapping[str, float],
    correctness: float,
    attempt_type: str,
    error_attributions: Iterable[Any] = (),
) -> dict[str, float]:
    if attempt_type == "dont_know":
        return {facet: 0.0 for facet in covered_facets}
    criteria = {criterion.id: criterion for criterion in rubric.criteria}
    max_points = max(float(rubric.max_points), 1.0)
    attributed_failed_facets = _error_attributed_facets(error_attributions)
    criterion_facet_weights = criterion_facet_weights_for_item(item, rubric)
    # Partial grading (teach_back asked-criteria-only; graders that omit a
    # criterion): a criterion absent from criterion_points was never assessed,
    # so it contributes nothing — it must not be scored as a zero-point
    # failure. When criterion_points is empty we keep the legacy all-zero
    # behavior (no criterion information at all).
    graded_criteria = set(criterion_points) if criterion_points else set(criteria)
    outcomes: dict[str, float] = {}
    for facet in covered_facets:
        num = 0.0
        den = 0.0
        for criterion_id, raw_map in criterion_facet_weights.items():
            criterion = criteria.get(criterion_id)
            if criterion is None:
                continue
            if criterion_id not in graded_criteria:
                continue
            weights = {
                mapped_facet: max(0.0, float(weight))
                for mapped_facet, weight in raw_map.items()
                if mapped_facet in item.evidence_facets
            }
            total = sum(weights.values())
            if total <= 0:
                continue
            facet_share = weights.get(facet, 0.0) / total
            if facet_share <= 0:
                continue
            criterion_weight = float(criterion.points) / max_points
            criterion_correctness = clamp(float(criterion_points.get(criterion_id, 0.0)) / max(float(criterion.points), 1.0))
            num += criterion_weight * facet_share * criterion_correctness
            den += criterion_weight * facet_share
        if den > 0:
            outcomes[facet] = clamp(num / den)
        elif facet in attributed_failed_facets:
            outcomes[facet] = 0.0
        else:
            outcomes[facet] = clamp(correctness)
    return outcomes


def familiarity_discount(
    repository: Repository,
    item: PracticeItem,
    *,
    learning_object_id: str,
    covered_facets: Mapping[str, float],
    config: LearnLoopConfig,
    exclude_attempt_id: str | None = None,
) -> FamiliarityResult:
    recent = repository.list_recent_attempts_by_learning_object(
        learning_object_id,
        limit=config.recall_coverage.familiarity_recent_attempt_window,
    )
    return familiarity_discount_from_attempts(
        recent,
        item,
        covered_facets=covered_facets,
        config=config,
        exclude_attempt_id=exclude_attempt_id,
    )


def familiarity_discount_from_attempts(
    recent: list[dict[str, Any]],
    item: PracticeItem,
    *,
    covered_facets: Mapping[str, float],
    config: LearnLoopConfig,
    exclude_attempt_id: str | None = None,
) -> FamiliarityResult:
    same_item_mass = 0.0
    same_surface_mass = 0.0
    same_facet_mass = 0.0
    target_facets = set(covered_facets)
    target_surface = item.surface_family or item.id
    for attempt in recent:
        if attempt.get("id") == exclude_attempt_id:
            continue
        attempt_weight = clamp(float(attempt.get("correctness") if attempt.get("correctness") is not None else 1.0))
        attempt_mass = 1.0 if attempt.get("attempt_type") == "dont_know" else max(0.25, attempt_weight)
        if attempt.get("practice_item_id") == item.id:
            same_item_mass += attempt_mass
        if (attempt.get("surface_family") or attempt.get("practice_item_id")) == target_surface:
            same_surface_mass += attempt_mass
        prior_facets = set(attempt.get("evidence_facets", []))
        if target_facets and prior_facets:
            overlap = len(target_facets & prior_facets) / len(target_facets | prior_facets)
            same_facet_mass += attempt_mass * overlap
    same_item_discount = _component_discount(config.recall_coverage.same_item_evidence_discount, same_item_mass)
    same_surface_discount = _component_discount(config.recall_coverage.same_surface_family_evidence_discount, same_surface_mass)
    same_facet_discount = _component_discount(config.recall_coverage.same_facet_surface_evidence_discount, same_facet_mass)
    final = clamp(
        same_item_discount * same_surface_discount * same_facet_discount,
        config.recall_coverage.min_independent_evidence_discount,
        1.0,
    )
    trace = {
        "same_item_recent_mass": min(same_item_mass, 1.0),
        "same_surface_family_recent_mass": min(same_surface_mass, 1.0),
        "same_facet_surface_recent_mass": min(same_facet_mass, 1.0),
        "same_item_discount": same_item_discount,
        "same_surface_family_discount": same_surface_discount,
        "same_facet_surface_discount": same_facet_discount,
        "independent_evidence_discount": final,
    }
    return FamiliarityResult(independent_evidence_discount=final, trace=trace)


def _resolve_error_impact_config(config: LearnLoopConfig, error_type: str):
    """Look up an ``[error_impacts]`` entry, resolving legacy keys via §10.1.

    A direct hit wins (mvp-0.6 legacy names and new-vocab TOMLs alike), so legacy
    behavior is byte-identical. Under mvp-0.7 the grader emits canonical mechanism
    values (e.g. ``retrieval_failure``) that no legacy TOML keys directly; those
    fall back to a view of the config re-keyed through ``map_legacy_error_type``.
    Collisions (recall_failure and scaffold_failure both map to retrieval_failure)
    resolve deterministically to the first legacy key in sorted order.
    """

    impact = config.error_impacts.get(error_type)
    if impact is not None:
        return impact
    resolved: dict[str, Any] = {}
    for legacy_key in sorted(config.error_impacts):
        mechanism = map_legacy_error_type(legacy_key)
        resolved.setdefault(mechanism, config.error_impacts[legacy_key])
    return resolved.get(error_type)


def resolve_error_impact(
    config: LearnLoopConfig,
    *,
    error_type: str | None,
    max_event_severity: float,
    effective_coverage: float,
    observation_reliability: float,
    independent_evidence_discount: float,
) -> ErrorImpactResult:
    before_sharpening = effective_coverage * observation_reliability
    if error_type is None or max_event_severity <= 0:
        sharpening = 1.0
    else:
        impact = _resolve_error_impact_config(config, error_type)
        local_gain = impact.local_severity_gain if impact is not None else 0.8
        sharpening = clamp(
            1.0 + local_gain * max_event_severity * effective_coverage,
            1.0,
            config.recall_coverage.max_error_sharpening,
        )
    before_familiarity = before_sharpening * sharpening
    observation_weight = before_familiarity * independent_evidence_discount
    return ErrorImpactResult(
        error_sharpening=sharpening,
        observation_weight=observation_weight,
        trace={
            "max_event_severity": max_event_severity,
            "local_severity_gain": sharpening - 1.0,
            "error_sharpening": sharpening,
            "observation_weight_before_sharpening": before_sharpening,
            "observation_weight_before_familiarity_discount": before_familiarity,
        },
    )


def event_local_severity(
    vault: LoadedVault,
    repository: Repository,
    item: PracticeItem,
    *,
    error_type: str,
    learning_object_id: str,
    attempt_type: str,
    hints_used: int,
    correctness: float,
    expected_correctness: float,
    effective_coverage: float,
    covered_facets: Mapping[str, float],
    facet_outcomes: Mapping[str, float],
    prior_bad_item_suspicion: float,
    base_severity: float | None = None,
    exclude_attempt_id: str | None = None,
) -> tuple[float, dict[str, Any]]:
    recent = repository.list_recent_attempts_by_learning_object(learning_object_id, limit=20)
    return event_local_severity_from_attempts(
        vault,
        recent,
        item,
        error_type=error_type,
        attempt_type=attempt_type,
        hints_used=hints_used,
        correctness=correctness,
        expected_correctness=expected_correctness,
        effective_coverage=effective_coverage,
        covered_facets=covered_facets,
        facet_outcomes=facet_outcomes,
        prior_bad_item_suspicion=prior_bad_item_suspicion,
        base_severity=base_severity,
        exclude_attempt_id=exclude_attempt_id,
    )


def event_local_severity_from_attempts(
    vault: LoadedVault,
    recent: list[dict[str, Any]],
    item: PracticeItem,
    *,
    error_type: str,
    attempt_type: str,
    hints_used: int,
    correctness: float,
    expected_correctness: float,
    effective_coverage: float,
    covered_facets: Mapping[str, float],
    facet_outcomes: Mapping[str, float],
    prior_bad_item_suspicion: float,
    base_severity: float | None = None,
    exclude_attempt_id: str | None = None,
) -> tuple[float, dict[str, Any]]:
    taxonomy = vault.error_types.get(error_type)
    taxonomy_default = base_severity if base_severity is not None else (taxonomy.severity_default if taxonomy is not None else 0.5)
    recent_same_item_failures = 0
    recent_same_facet_failures = 0
    recent_same_error_events = 0
    target_facets = set(covered_facets)
    for attempt in recent:
        if attempt.get("id") == exclude_attempt_id:
            continue
        failed = attempt.get("attempt_type") == "dont_know" or float(attempt.get("correctness") or 0.0) <= 0.40 or bool(attempt.get("error_type"))
        if not failed:
            continue
        if attempt.get("practice_item_id") == item.id:
            recent_same_item_failures += 1
        if target_facets and set(attempt.get("evidence_facets", [])) & target_facets:
            recent_same_facet_failures += 1
        if attempt.get("error_type") == error_type:
            recent_same_error_events += 1
    failed_facet_mass = sum(
        float(covered_facets.get(facet, 0.0))
        for facet, outcome in facet_outcomes.items()
        if outcome < 0.40
    )
    components = {
        "taxonomy_default": taxonomy_default,
        "incorrectness_bonus": 0.12 * (1.0 - correctness),
        "expected_correctness_bonus": 0.10 * expected_correctness,
        "coverage_bonus": 0.08 * effective_coverage,
        "repeated_same_item_bonus": min(0.25, 0.15 * recent_same_item_failures),
        "repeated_same_facet_bonus": min(0.20, 0.10 * recent_same_facet_failures),
        "repeated_same_error_bonus": min(0.10, 0.05 * recent_same_error_events),
        "dont_know_bonus": 0.05 if attempt_type == "dont_know" else 0.0,
        "facet_outcome_bonus": 0.08 * failed_facet_mass,
        "hint_mitigation": 0.04 * hints_used,
        "bad_item_suspicion_mitigation": min(
            0.20 * prior_bad_item_suspicion,
            vault.config.recall_coverage.bad_item_suspicion_damage_mitigation_cap,
        ),
        "recent_same_item_failures": recent_same_item_failures,
        "recent_same_facet_failures": recent_same_facet_failures,
        "recent_same_error_events": recent_same_error_events,
    }
    severity = clamp(
        components["taxonomy_default"]
        + components["incorrectness_bonus"]
        + components["expected_correctness_bonus"]
        + components["coverage_bonus"]
        + components["repeated_same_item_bonus"]
        + components["repeated_same_facet_bonus"]
        + components["repeated_same_error_bonus"]
        + components["dont_know_bonus"]
        + components["facet_outcome_bonus"]
        - components["hint_mitigation"]
        - components["bad_item_suspicion_mitigation"]
    )
    return severity, components


def build_facet_recall_updates(
    repository: Repository,
    *,
    learning_object_id: str,
    practice_item_id: str,
    covered_facets: Mapping[str, float],
    facet_outcomes: Mapping[str, float],
    independent_evidence_discount: float,
    attempt_type: str,
    error_event_written: bool,
    algorithm_version: str,
    now_iso: str,
) -> list[dict[str, Any]]:
    prior_states: dict[tuple[str, str | None], Any] = {}
    for facet_id in covered_facets:
        for item_scope in (None, practice_item_id):
            prior_states[(facet_id, item_scope)] = repository.facet_recall_state(
                learning_object_id, facet_id, item_scope
            )
    return build_facet_recall_updates_from_prior(
        prior_states,
        learning_object_id=learning_object_id,
        practice_item_id=practice_item_id,
        covered_facets=covered_facets,
        facet_outcomes=facet_outcomes,
        independent_evidence_discount=independent_evidence_discount,
        attempt_type=attempt_type,
        error_event_written=error_event_written,
        algorithm_version=algorithm_version,
        now_iso=now_iso,
    )


def build_facet_recall_updates_from_prior(
    prior_states: Mapping[tuple[str, str | None], Any],
    *,
    learning_object_id: str,
    practice_item_id: str,
    covered_facets: Mapping[str, float],
    facet_outcomes: Mapping[str, float],
    independent_evidence_discount: float,
    attempt_type: str,
    error_event_written: bool,
    algorithm_version: str,
    now_iso: str,
) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    for facet_id, raw_weight in covered_facets.items():
        outcome = 0.0 if attempt_type == "dont_know" else clamp(float(facet_outcomes.get(facet_id, 0.0)))
        discounted_weight = float(raw_weight) * independent_evidence_discount
        for item_scope in (None, practice_item_id):
            prior = prior_states.get((facet_id, item_scope))
            alpha = prior.recall_alpha if prior is not None else 1.0
            beta = prior.recall_beta if prior is not None else 1.0
            independent_mass = prior.independent_evidence_mass if prior is not None else 0.0
            raw_mass = prior.raw_coverage_mass if prior is not None else 0.0
            consecutive = prior.consecutive_failures if prior is not None else 0
            alpha += discounted_weight * outcome
            beta += discounted_weight * (1.0 - outcome)
            independent_mass += discounted_weight
            raw_mass += float(raw_weight)
            consecutive = consecutive + 1 if outcome < 0.40 else 0
            mean = alpha / (alpha + beta)
            variance = alpha * beta / ((alpha + beta) ** 2 * (alpha + beta + 1.0))
            updates.append(
                {
                    "learning_object_id": learning_object_id,
                    "facet_id": facet_id,
                    "practice_item_id": item_scope,
                    "recall_alpha": alpha,
                    "recall_beta": beta,
                    "recall_mean": mean,
                    "recall_variance": variance,
                    "independent_evidence_mass": independent_mass,
                    "raw_coverage_mass": raw_mass,
                    "last_attempt_at": now_iso,
                    "last_error_at": now_iso if error_event_written and outcome < 0.40 else (prior.last_error_at if prior is not None else None),
                    "consecutive_failures": consecutive,
                    "algorithm_version": algorithm_version,
                    "created_at": prior.created_at if prior is not None else now_iso,
                    "updated_at": now_iso,
                }
            )
    return updates


def build_quality_state_update(
    repository: Repository,
    *,
    item: PracticeItem,
    prior_mastery: MasteryState,
    correctness: float,
    grader_confidence: float,
    now_iso: str,
    algorithm_version: str,
    exclude_attempt_id: str | None = None,
) -> dict[str, Any]:
    prior = repository.practice_item_quality_state(item.id)
    recent_failures = sum(
        1
        for attempt in repository.list_recent_attempts_by_practice_item(item.id, limit=5)
        if attempt.get("id") != exclude_attempt_id
        if attempt.get("attempt_type") == "dont_know" or float(attempt.get("correctness") or 0.0) <= 0.40
    )
    return build_quality_state_update_from_prior(
        prior,
        recent_failures=recent_failures,
        item_id=item.id,
        prior_mastery=prior_mastery,
        correctness=correctness,
        grader_confidence=grader_confidence,
        now_iso=now_iso,
        algorithm_version=algorithm_version,
    )


def build_quality_state_update_from_prior(
    prior: Any,
    *,
    recent_failures: int,
    item_id: str,
    prior_mastery: MasteryState,
    correctness: float,
    grader_confidence: float,
    now_iso: str,
    algorithm_version: str,
    assessment_side_error: bool = False,
) -> dict[str, Any]:
    suspicion = prior.bad_item_suspicion if prior is not None else 0.0
    evidence_count = prior.evidence_count if prior is not None else 0
    reasons = list(prior.suspicion_reasons if prior is not None else [])
    prior_mastery_mean = display_mastery(prior_mastery).mastery_mean
    delta = 0.0
    if grader_confidence < 0.5:
        delta += 0.08
        reasons.append("low_grader_confidence")
    if assessment_side_error:
        # The grader attributed the outcome to the item/assessment (e.g.
        # assessment_ambiguity), not the learner. Scheduler repair boosts
        # exclude these events; the item pays instead.
        delta += 0.08
        reasons.append("assessment_side_error")
    if correctness <= 0.40 and recent_failures >= 1:
        delta += 0.06
        reasons.append("repeated_failure_on_same_item")
    if correctness <= 0.40 and prior_mastery_mean >= 0.75:
        delta += 0.06
        reasons.append("failure_despite_high_lo_state")
    if correctness >= 0.90:
        delta -= 0.04
        reasons.append("clean_success_on_item")
    suspicion = clamp(suspicion + delta)
    evidence_count += 1
    last_flagged_at = prior.last_flagged_at if prior is not None else None
    if (
        suspicion >= 0.65
        and evidence_count >= 3
        and last_flagged_at is None
    ):
        last_flagged_at = now_iso
    return {
        "practice_item_id": item_id,
        "bad_item_suspicion": suspicion,
        "evidence_count": evidence_count,
        "suspicion_reasons": sorted(set(reasons)),
        "last_flagged_at": last_flagged_at,
        "algorithm_version": algorithm_version,
        "updated_at": now_iso,
    }


def predicted_correctness(
    repository: Repository,
    item: PracticeItem,
    *,
    learning_object_id: str,
    prior_mastery: MasteryState,
    item_a: float,
    item_b: float,
    config: LearnLoopConfig,
    vault: LoadedVault | None = None,
) -> tuple[float, dict[str, float]]:
    # KM2b: when a vault is supplied, read facet priors through the canonical
    # adapter (mvp-0.7) / legacy per-LO table (mvp-0.6). Vault-less callers keep
    # the legacy read for backward compatibility.
    if vault is not None:
        from learnloop.services.facet_state_reader import facet_recall_state_for_lo

        facet_states = {
            facet: facet_recall_state_for_lo(vault, repository, learning_object_id, facet)
            for facet in item.evidence_facets
        }
    else:
        facet_states = {
            facet: repository.facet_recall_state(learning_object_id, facet)
            for facet in item.evidence_facets
        }
    return predicted_correctness_from_prior(
        facet_states,
        item,
        prior_mastery=prior_mastery,
        item_a=item_a,
        item_b=item_b,
        config=config,
    )


def predicted_correctness_from_prior(
    facet_states: Mapping[str, Any],
    item: PracticeItem,
    *,
    prior_mastery: MasteryState,
    item_a: float,
    item_b: float,
    config: LearnLoopConfig,
) -> tuple[float, dict[str, float]]:
    irt = 1.0 / (1.0 + exp(-(item_a * (prior_mastery.logit_mean - item_b))))
    weights = _normalize({facet: max(0.0, float(item.evidence_weights.get(facet, 1.0))) for facet in item.evidence_facets})
    facet_num = 0.0
    facet_den = 0.0
    evidence_mass = 0.0
    for facet, weight in weights.items():
        state = facet_states.get(facet)
        if state is None:
            continue
        facet_num += weight * state.recall_mean
        facet_den += weight
        evidence_mass += state.independent_evidence_mass
    facet_readiness = facet_num / facet_den if facet_den > 0 else 0.5
    blend = clamp(evidence_mass / max(config.recall_coverage.facet_blend_evidence_count, 0.1))
    base = (1.0 - blend) * irt + blend * facet_readiness
    scaffold_adjustment = 0.10 * float(item.scaffold_level or 0.0)
    retrieval_adjustment = -0.10 * float(item.retrieval_demand or 0.0) * (1.0 - facet_readiness)
    value = clamp(base + scaffold_adjustment + retrieval_adjustment)
    return value, {
        "irt_predicted_correctness": irt,
        "facet_readiness": facet_readiness,
        "facet_blend_weight": blend,
        "scaffold_adjustment": scaffold_adjustment,
        "retrieval_demand_adjustment": retrieval_adjustment,
    }


def _raw_coverage(
    item: PracticeItem, rubric: Rubric | None, evidence: EvidenceConfig | None = None
) -> tuple[dict[str, float], float, str]:
    if item.evidence_weights:
        raw = {
            facet: max(0.0, float(item.evidence_weights.get(facet, 0.0)))
            for facet in item.evidence_facets
        }
        for facet, weight in item.evidence_weights.items():
            if facet not in raw and facet in item.evidence_facets:
                raw[facet] = max(0.0, float(weight))
        total = sum(raw.values())
        return raw, clamp(total), "evidence_weights"
    if rubric is not None and rubric.criteria:
        facets = item.evidence_facets or ["whole-item"]
        if item.criterion_facet_weights:
            raw: dict[str, float] = {facet: 0.0 for facet in facets}
            max_points = max(float(rubric.max_points), 1.0)
            for criterion in rubric.criteria:
                raw_map = item.criterion_facet_weights.get(criterion.id)
                if raw_map:
                    norm = _normalize({facet: max(0.0, float(raw_map.get(facet, 0.0))) for facet in facets})
                else:
                    norm = {facet: 1.0 / len(facets) for facet in facets}
                for facet, weight in norm.items():
                    raw[facet] += (float(criterion.points) / max_points) * weight
            return raw, _practice_mode_default(item, evidence), "rubric"
        return {facet: 1.0 / len(facets) for facet in facets}, _practice_mode_default(item, evidence), "rubric"
    facets = item.evidence_facets or ["whole-item"]
    return {facet: 1.0 / len(facets) for facet in facets}, _practice_mode_default(item, evidence), "practice_mode"


def expected_facet_mass_gain(
    item: PracticeItem, rubric: Rubric | None, evidence: EvidenceConfig | None = None
) -> dict[str, float]:
    """Nominal per-facet evidence mass one fresh attempt on ``item`` would add.

    ``item_coverage × normalized facet weight`` — the pre-modifier core of
    ``resolve_coverage`` (no hint/engagement/attempt-type dampening and no
    familiarity discount, which depend on the eventual attempt). Used to invert
    the mass equation into "attempts to certify" estimates for goal reporting.
    """

    raw_facet_weights, item_coverage, _ = _raw_coverage(item, rubric, evidence)
    return {
        facet: item_coverage * weight
        for facet, weight in _normalize(raw_facet_weights).items()
    }


def _error_attributed_facets(error_attributions: Iterable[Any]) -> set[str]:
    facets: set[str] = set()
    for attribution in error_attributions:
        targets = getattr(attribution, "target_evidence_families", None)
        if not targets:
            continue
        facets.update(str(target) for target in targets if target)
    return facets


def criterion_facet_weights_for_item(item: PracticeItem, rubric: Rubric) -> dict[str, dict[str, float]]:
    if item.criterion_facet_weights:
        return dict(item.criterion_facet_weights)
    return _inferred_criterion_facet_weights(item, rubric)


def _inferred_criterion_facet_weights(item: PracticeItem, rubric: Rubric) -> dict[str, dict[str, float]]:
    """Best-effort fallback for older/generated items missing facet metadata.

    Author-provided ``criterion_facet_weights`` remains authoritative. This
    fallback only handles obvious lexical matches between rubric criteria and
    item facets so a single failed criterion does not get smeared across every
    facet as whole-item correctness.
    """

    facets = list(item.evidence_facets)
    if not facets:
        return {}
    if len(facets) == 1:
        return {criterion.id: {facets[0]: 1.0} for criterion in rubric.criteria}
    facet_tokens = {facet: _facet_tokens(facet) for facet in facets}
    inferred: dict[str, dict[str, float]] = {}
    for criterion in rubric.criteria:
        criterion_tokens = _facet_tokens(f"{criterion.id} {criterion.description}")
        scores: dict[str, float] = {}
        for facet, tokens in facet_tokens.items():
            overlap = tokens & criterion_tokens
            if not overlap:
                continue
            # Strongly prefer distinctive content tokens; keep a small fallback
            # for generic verbs like "identify" or "justify".
            scores[facet] = sum(3.0 if token not in _GENERIC_FACET_TOKENS else 1.0 for token in overlap)
        if not scores:
            continue
        best = max(scores.values())
        winners = {facet: score for facet, score in scores.items() if score == best}
        if best <= 1.0 and len(winners) > 1:
            continue
        inferred[criterion.id] = {facet: 1.0 for facet in winners}
    return inferred


_GENERIC_FACET_TOKENS = {
    "answer",
    "compute",
    "correct",
    "correctly",
    "error",
    "from",
    "identify",
    "justifies",
    "justify",
    "state",
    "states",
    "value",
    "values",
    "with",
}


def _facet_tokens(value: str) -> set[str]:
    aliases = {
        "frobenius": "frobenius",
        "frobenius-norm": "frobenius",
        "norm": "norm",
        "singular": "singular",
        "singular-value": "singular",
        "spectral": "spectral",
        "spectral-norm": "spectral",
    }
    tokens = {
        aliases.get(token, token)
        for token in re.findall(r"[a-z0-9]+", value.lower().replace("_", " ").replace("-", " "))
        if token
    }
    return tokens - {"a", "an", "and", "by", "is", "of", "or", "that", "the", "to"}


def _practice_mode_default(item: PracticeItem, evidence: EvidenceConfig | None = None) -> float:
    return practice_mode_item_coverage(item.practice_mode, evidence)


def _normalize(weights: Mapping[str, float]) -> dict[str, float]:
    positive = {key: max(0.0, float(value)) for key, value in weights.items()}
    total = sum(positive.values())
    if total <= 0:
        return {}
    return {key: value / total for key, value in positive.items() if value > 0}


def _response_engagement_factor(attempt_type: str, learner_answer_md: str) -> float:
    if attempt_type == "skip":
        return 0.0
    if attempt_type == "dont_know":
        return 1.0
    if learner_answer_md.strip():
        return 1.0
    return 0.50


def _component_discount(target_discount: float, recent_overlap_mass: float) -> float:
    return 1.0 - (1.0 - target_discount) * clamp(recent_overlap_mass, 0.0, 1.0)


def _hint_policy_product(mapping: Mapping[int | str, float], hints_used: int, *, default: float) -> float:
    value = 1.0
    for hint_number in range(1, hints_used + 1):
        if hint_number in mapping:
            value *= float(mapping[hint_number])
        elif str(hint_number) in mapping:
            value *= float(mapping[str(hint_number)])
        else:
            value *= default
    return clamp(value)

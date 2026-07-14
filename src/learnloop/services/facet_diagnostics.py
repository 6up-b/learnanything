from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from math import log
from typing import Any, Iterable, Mapping

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import FacetRecallState, FacetUncertaintyState, MasteryState, Repository
from learnloop.services.facet_state_reader import (
    facet_recall_states_for_lo,
    facet_uncertainty_states_for_lo,
)
from learnloop.services.mastery import display_mastery
from learnloop.services.probes import apply_facet_observation
from learnloop.numeric import clamp
from learnloop.services.recall_coverage import criterion_facet_weights_for_item
from learnloop.vault.models import LoadedVault, PracticeItem, Rubric


def entropy(distribution: Mapping[str, float]) -> float:
    return -sum(float(p) * log(float(p)) for p in distribution.values() if float(p) > 0)


def normalize_distribution(distribution: Mapping[str, float]) -> dict[str, float]:
    cleaned = {str(label): max(float(probability), 0.0) for label, probability in distribution.items()}
    total = sum(cleaned.values())
    if total <= 0:
        return {}
    return {label: probability / total for label, probability in cleaned.items()}


def candidate_facet_support(item: PracticeItem) -> set[str]:
    return {str(facet) for facet in (item.repair_targets or item.evidence_facets)}


def required_facets(
    vault: LoadedVault,
    learning_object_id: str,
    repository: Repository | None = None,
) -> set[str]:
    facets: set[str] = set()
    item_states = repository.practice_item_states() if repository is not None else {}
    for item in vault.practice_items.values():
        if item.learning_object_id != learning_object_id:
            continue
        state = item_states.get(item.id)
        if state is not None and not state.active:
            continue
        facets.update(str(facet) for facet in item.evidence_facets)
    return facets


def lo_relative_coverage(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_id: str,
    normalized_facet_weights: Mapping[str, float],
    effective_item_coverage: float,
) -> tuple[float, dict[str, Any]]:
    required = required_facets(vault, learning_object_id, repository)
    open_uncertainties = {
        state.facet_id: state
        for state in facet_uncertainty_states_for_lo(
            vault, repository, learning_object_id, statuses=("open", "resolving")
        )
    }
    measured_required = set(open_uncertainties) if open_uncertainties else required
    if not measured_required:
        return 1.0, {
            "required_facets": [],
            "open_facet_restriction": False,
            "measured_facets": [],
            "facet_importance": {},
            "per_facet_coverage": {},
            "lo_relative_coverage": 1.0,
        }
    config = vault.config.recall_coverage
    importance = {
        facet: 1.0 + config.kappa_uncertain * max(open_uncertainties.get(facet).uncertainty, 0.0)
        if facet in open_uncertainties
        else 1.0
        for facet in measured_required
    }
    per_facet = {
        facet: clamp(effective_item_coverage)
        if float(normalized_facet_weights.get(facet, 0.0)) >= config.tau_facet_share
        else 0.0
        for facet in measured_required
    }
    denominator = sum(importance.values())
    value = 0.0 if denominator <= 0 else sum(importance[f] * per_facet[f] for f in measured_required) / denominator
    trace = {
        "required_facets": sorted(required),
        "open_facet_restriction": bool(open_uncertainties),
        "measured_facets": sorted(measured_required),
        "facet_importance": {facet: importance[facet] for facet in sorted(importance)},
        "per_facet_coverage": {facet: per_facet[facet] for facet in sorted(per_facet)},
        "tau_facet_share": config.tau_facet_share,
        "lo_relative_coverage": clamp(value),
    }
    return clamp(value), trace


def covered_required_fraction(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_id: str,
    aggregate_facet_recall: Mapping[str, FacetRecallState | Mapping[str, Any] | None] | None = None,
) -> tuple[float, dict[str, Any]]:
    required = required_facets(vault, learning_object_id, repository)
    if not required:
        return 1.0, {
            "required_facets": [],
            "covered_required_facets": [],
            "min_facet_evidence_mass": vault.config.recall_coverage.min_facet_evidence_mass,
            "covered_required_fraction": 1.0,
        }
    state_by_facet: dict[str, Any] = {
        state.facet_id: state
        for state in facet_recall_states_for_lo(vault, repository, learning_object_id)
        if state.practice_item_id is None
    }
    for facet, state in dict(aggregate_facet_recall or {}).items():
        if state is not None:
            state_by_facet[str(facet)] = state
    threshold = vault.config.recall_coverage.min_facet_evidence_mass

    def mass(state: Any) -> float:
        if isinstance(state, Mapping):
            return float(state.get("independent_evidence_mass", 0.0))
        return float(getattr(state, "independent_evidence_mass", 0.0))

    covered = sorted(
        facet
        for facet in required
        if mass(state_by_facet.get(facet)) > threshold
    )
    value = len(covered) / len(required)
    return value, {
        "required_facets": sorted(required),
        "covered_required_facets": covered,
        "min_facet_evidence_mass": threshold,
        "covered_required_fraction": value,
    }


def variance_floor(config: LearnLoopConfig, covered_fraction: float) -> float:
    recall = config.recall_coverage
    c = clamp(covered_fraction)
    return recall.variance_floor_at_full_coverage + (
        recall.variance_floor_at_zero_coverage - recall.variance_floor_at_full_coverage
    ) * (1.0 - c)


def apply_mastery_variance_floor(
    state: MasteryState,
    config: LearnLoopConfig,
    *,
    covered_fraction: float,
) -> tuple[MasteryState, float]:
    floor = variance_floor(config, covered_fraction)
    if state.logit_variance >= floor:
        return state, floor
    return replace(state, logit_variance=floor), floor


def build_facet_uncertainty_updates(
    vault: LoadedVault,
    *,
    item: PracticeItem,
    rubric: Rubric,
    learning_object_id: str,
    attempt_id: str,
    facet_outcomes: Mapping[str, float],
    normalized_facet_weights: Mapping[str, float],
    evidence_rows: Iterable[Mapping[str, Any] | Any],
    error_attributions: Iterable[Any],
    prior_uncertainties: Mapping[str, FacetUncertaintyState | None],
    prior_facet_recall: Mapping[str, FacetRecallState | None],
    observed_error_type: str | None,
    algorithm_version: str,
    now_iso: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    config = vault.config.facet_diagnostic
    support = candidate_facet_support(item)
    fatal_error_ids = {fatal_error.id for fatal_error in rubric.fatal_errors}
    criterion_facets = criterion_facet_weights_for_item(item, rubric)
    hedged_facets = _hedged_facets(evidence_rows, criterion_facets, item.evidence_facets)
    updates: list[dict[str, Any]] = []
    update_trace: dict[str, Any] = {"updates": {}, "hedged_facets": sorted(hedged_facets)}
    observed_buckets = {
        facet: _facet_outcome_bucket(float(outcome))
        for facet, outcome in facet_outcomes.items()
    }
    for facet in sorted(set(facet_outcomes) | hedged_facets):
        if float(normalized_facet_weights.get(facet, 0.0)) < vault.config.recall_coverage.tau_facet_share:
            continue
        outcome = clamp(float(facet_outcomes.get(facet, 0.5)))
        prior = prior_uncertainties.get(facet)
        prior_recall = prior_facet_recall.get(facet)
        reason = _open_reason(
            outcome,
            hedged=facet in hedged_facets,
            prior_recall=prior_recall,
            config=config,
        )
        if prior is None and reason is None:
            continue
        marginal_before = (
            dict(prior.hypothesis_marginal)
            if prior is not None
            else _initial_hypothesis_marginal(vault, learning_object_id, facet, error_attributions)
        )
        posterior = apply_facet_observation(
            marginal_before,
            facet_id=facet,
            candidate_facet_support=support,
            fatal_error_ids=fatal_error_ids,
            observed_bucket=observed_buckets.get(facet, "mid"),
            observed_error_type=observed_error_type if observed_error_type in fatal_error_ids else None,
        )
        if facet in hedged_facets:
            posterior = _raise_entropy_floor(posterior, config.hedge_uncertainty_floor)
        posterior = normalize_distribution(posterior)
        uncertainty = entropy(posterior)
        status = "resolved" if uncertainty <= config.facet_resolved_threshold else ("resolving" if prior is not None else "open")
        opened_reason = prior.opened_reason if prior is not None else str(reason or "low_facet_outcome")
        opened_by_attempt_id = prior.opened_by_attempt_id if prior is not None else attempt_id
        created_at = prior.created_at if prior is not None else now_iso
        updates.append(
            {
                "id": prior.id if prior is not None else _facet_uncertainty_id(learning_object_id, facet),
                "learning_object_id": learning_object_id,
                "facet_id": facet,
                "hypothesis_marginal": posterior,
                "uncertainty": uncertainty,
                "status": status,
                "opened_by_attempt_id": opened_by_attempt_id,
                "opened_reason": opened_reason,
                "last_evidence_at": now_iso,
                "algorithm_version": algorithm_version,
                "created_at": created_at,
                "updated_at": now_iso,
            }
        )
        update_trace["updates"][facet] = {
            "before": marginal_before,
            "after": posterior,
            "uncertainty_before": entropy(marginal_before),
            "uncertainty_after": uncertainty,
            "uncertainty_drop": entropy(marginal_before) - uncertainty,
            "status": status,
            "opened_reason": opened_reason,
        }
    return updates, update_trace


def facet_state_label(
    facet_id: str,
    uncertainty: FacetUncertaintyState | None,
    recall: FacetRecallState | None,
    min_evidence_mass: float,
) -> str:
    """Diagnostic bucket for one required facet.

    Returns one of ``unexamined`` / ``uncertain`` / ``known_gap`` / ``solid``,
    the same classification ``mastery_diagnostic_view`` renders. ``recall`` is
    the aggregate (``practice_item_id is None``) facet recall state.
    """

    if uncertainty is not None:
        top_label = max(uncertainty.hypothesis_marginal, key=uncertainty.hypothesis_marginal.get)
        if uncertainty.status in {"open", "resolving"}:
            return "uncertain"
        if top_label != f"facet_solid:{facet_id}":
            return "known_gap"
        if recall is not None and recall.independent_evidence_mass > min_evidence_mass:
            return "solid"
        return "unexamined"
    if recall is not None and recall.independent_evidence_mass > min_evidence_mass:
        return "solid"
    return "unexamined"


# Tutor Q&A read-side uncertainty adjustment (design decision, see the tutor_qa
# service): asking about a facet raises the *displayed* diagnostic uncertainty
# instead of writing a facet_uncertainty row. question_events persist, so this
# view is automatically replay-consistent — rebuilding derived state can never
# disagree with it — and the mastery mean is untouched by construction. The
# bump is bounded: at most _QUESTION_BUMP_MAX_COUNT recent unresolved questions
# count, each adding config.tutor_qa.uncertainty_evidence_mass nats.
_QUESTION_BUMP_WINDOW_DAYS = 7
_QUESTION_BUMP_MAX_COUNT = 3


def unresolved_question_facet_counts(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    recall_states: Mapping[str, FacetRecallState] | None = None,
    clock: Clock | None = None,
) -> dict[str, int]:
    """Recent unresolved tutor questions per facet for one LO.

    A question is *unresolved* while no attempt evidence on that facet has
    landed after it (aggregate recall's last_attempt_at). Question events map
    to the LO through their practice item (practice/feedback contexts) or the
    note's related_los (library context)."""

    now = parse_utc(utc_now_iso(clock))
    since = (now - timedelta(days=_QUESTION_BUMP_WINDOW_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    if recall_states is None:
        recall_states = {
            state.facet_id: state
            for state in facet_recall_states_for_lo(vault, repository, learning_object_id)
            if state.practice_item_id is None
        }
    counts: dict[str, int] = {}
    for event in repository.question_events(since=since):
        item_id = event.get("practice_item_id")
        note_id = event.get("note_id")
        if item_id is not None:
            item = vault.practice_items.get(item_id)
            if item is None or item.learning_object_id != learning_object_id:
                continue
        elif note_id is not None:
            note = vault.notes.get(note_id)
            if note is None or learning_object_id not in note.related_los:
                continue
        else:
            continue
        for facet in event.get("facets", []):
            facet_id = vault.canonical_facet_id(str(facet))
            recall = recall_states.get(facet_id)
            if (
                recall is not None
                and recall.last_attempt_at is not None
                and recall.last_attempt_at > event["created_at"]
            ):
                continue  # answered by later attempt evidence: resolved
            counts[facet_id] = counts.get(facet_id, 0) + 1
    return counts


def mastery_diagnostic_view(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    mastery = repository.mastery_state(learning_object_id)
    display = display_mastery(mastery) if mastery is not None else None
    recall_states = {
        state.facet_id: state
        for state in facet_recall_states_for_lo(vault, repository, learning_object_id)
        if state.practice_item_id is None
    }
    uncertainty_states = {
        state.facet_id: state
        for state in facet_uncertainty_states_for_lo(vault, repository, learning_object_id)
    }
    required = required_facets(vault, learning_object_id, repository)
    question_counts: dict[str, int] = {}
    if vault.config.tutor_qa.apply_uncertainty_effect:
        question_counts = unresolved_question_facet_counts(
            vault,
            repository,
            learning_object_id,
            recall_states=recall_states,
            clock=clock,
        )
    facets: list[dict[str, Any]] = []
    min_mass = vault.config.recall_coverage.min_facet_evidence_mass
    for facet in sorted(required | set(uncertainty_states)):
        uncertainty = uncertainty_states.get(facet)
        recall = recall_states.get(facet)
        state = facet_state_label(facet, uncertainty, recall, min_mass)
        known_gap_label = (
            max(uncertainty.hypothesis_marginal, key=uncertainty.hypothesis_marginal.get)
            if state == "known_gap" and uncertainty is not None
            else None
        )
        question_count = question_counts.get(facet, 0)
        question_bump = (
            min(question_count, _QUESTION_BUMP_MAX_COUNT)
            * vault.config.tutor_qa.uncertainty_evidence_mass
        )
        displayed_uncertainty = uncertainty.uncertainty if uncertainty is not None else None
        if question_bump > 0:
            displayed_uncertainty = (displayed_uncertainty or 0.0) + question_bump
            # Asking about a facet the diagnostics call solid/unexamined marks
            # it uncertain in the view; known gaps stay known gaps.
            if state in {"solid", "unexamined"}:
                state = "uncertain"
        facets.append(
            {
                "facet_id": facet,
                "state": state,
                "known_gap": known_gap_label,
                "independent_evidence_mass": recall.independent_evidence_mass if recall is not None else 0.0,
                "uncertainty": displayed_uncertainty,
                "question_uncertainty_bump": question_bump,
                "recent_question_count": question_count,
                "hypothesis_marginal": uncertainty.hypothesis_marginal if uncertainty is not None else None,
            }
        )
    return {
        "learning_object_id": learning_object_id,
        "mastery_mean": display.mastery_mean if display is not None else None,
        "mastery_variance": display.mastery_variance if display is not None else None,
        "required_facets": sorted(required),
        "facets": facets,
    }


def _open_reason(
    outcome: float,
    *,
    hedged: bool,
    prior_recall: FacetRecallState | None,
    config: Any,
) -> str | None:
    if outcome < config.tau_facet_failed:
        if prior_recall is not None and prior_recall.consecutive_failures >= 1:
            return "repeated_facet_failure"
        return "low_facet_outcome"
    if hedged:
        return "hedged_confidence"
    if prior_recall is not None and prior_recall.recall_variance > config.tau_facet_uncertain_variance:
        return "low_facet_outcome"
    return None


def _facet_uncertainty_id(learning_object_id: str, facet_id: str) -> str:
    safe_lo = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in learning_object_id)
    safe_facet = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in facet_id)
    return f"facet_uncertainty_{safe_lo}_{safe_facet}"


def _initial_hypothesis_marginal(
    vault: LoadedVault,
    learning_object_id: str,
    facet_id: str,
    error_attributions: Iterable[Any],
) -> dict[str, float]:
    labels = [f"facet_solid:{facet_id}", f"facet_absent:{facet_id}"]
    for attribution in error_attributions:
        if not _attribution_targets_facet(vault, learning_object_id, attribution, facet_id):
            continue
        label = f"misconception:{getattr(attribution, 'error_type', '')}"
        if label not in labels:
            labels.append(label)
    if len(labels) == 2:
        return {labels[0]: 0.35, labels[1]: 0.65}
    misconception_share = 0.30 / max(len(labels) - 2, 1)
    marginal = {labels[0]: 0.25, labels[1]: 0.45}
    for label in labels[2:]:
        marginal[label] = misconception_share
    return normalize_distribution(marginal)


def _attribution_targets_facet(
    vault: LoadedVault,
    learning_object_id: str,
    attribution: Any,
    facet_id: str,
) -> bool:
    targets = {str(facet) for facet in getattr(attribution, "target_evidence_families", [])}
    if facet_id in targets:
        return True
    error_type = vault.error_types.get(str(getattr(attribution, "error_type", "")))
    learning_object = vault.learning_objects.get(learning_object_id)
    if error_type is None or learning_object is None:
        return not targets
    return learning_object.concept in set(error_type.related_concepts) and not targets


def _hedged_facets(
    evidence_rows: Iterable[Mapping[str, Any] | Any],
    criterion_facets: Mapping[str, Mapping[str, float]],
    item_facets: Iterable[str],
) -> set[str]:
    fallback = set(str(facet) for facet in item_facets)
    hedged: set[str] = set()
    for row in evidence_rows:
        confidence = _row_value(row, "learner_confidence")
        if confidence != "hedged":
            continue
        criterion_id = _row_value(row, "criterion_id")
        mapped = criterion_facets.get(str(criterion_id), {})
        hedged.update(str(facet) for facet, weight in mapped.items() if float(weight) > 0)
        if not mapped:
            hedged.update(fallback)
    return hedged


def _row_value(row: Mapping[str, Any] | Any, key: str) -> Any:
    if isinstance(row, Mapping):
        return row.get(key)
    return getattr(row, key, None)


def _facet_outcome_bucket(outcome: float) -> str:
    if outcome < 0.40:
        return "low"
    if outcome < 0.75:
        return "mid"
    return "high"


def _raise_entropy_floor(distribution: Mapping[str, float], floor: float) -> dict[str, float]:
    posterior = normalize_distribution(distribution)
    if entropy(posterior) >= floor or len(posterior) <= 1:
        return posterior
    uniform = {label: 1.0 / len(posterior) for label in posterior}
    for step in range(1, 21):
        alpha = step / 20
        mixed = {
            label: (1.0 - alpha) * posterior[label] + alpha * uniform[label]
            for label in posterior
        }
        if entropy(mixed) >= floor:
            return normalize_distribution(mixed)
    return uniform

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import exp, log

from learnloop.db.repositories import ActiveErrorEvent, FacetRecallState, MasteryState, PracticeItemQualityState
from learnloop.services.ability_transition import estimate_ability_transition
from learnloop.numeric import clamp
from learnloop.services.blueprint_projection import predict_item_success
from learnloop.services.facet_state_reader import is_canonical_state_vault
from learnloop.services.mastery import item_irt_params
from learnloop.vault.models import LearningObject, LoadedVault, PracticeItem


# Reward floor for teach_back items under the PROBE intent (see
# score_selection_reward): keeps solid items weakly schedulable so transfer
# escalation still gets served, without adding a scheduler weight knob.
TEACH_BACK_REWARD_FLOOR = 0.05


class SchedulerIntent(str, Enum):
    PROBE = "probe"
    PRACTICE = "practice"
    REPAIR = "repair"
    REVIEW = "review"
    TRANSFER = "transfer"


@dataclass(frozen=True)
class LearnerAbilityVector:
    learning_object_id: str
    lo_mastery: float
    lo_mastery_variance: float
    facet_recall_mean_by_facet: dict[str, float]
    facet_recall_variance_by_facet: dict[str, float]
    facet_independent_evidence_mass_by_facet: dict[str, float]
    misconception_posterior_by_error_type: dict[str, float]

    def as_dict(self) -> dict[str, object]:
        return {
            "learning_object_id": self.learning_object_id,
            "lo_mastery": self.lo_mastery,
            "lo_mastery_variance": self.lo_mastery_variance,
            "facet_recall_mean_by_facet": self.facet_recall_mean_by_facet,
            "facet_recall_variance_by_facet": self.facet_recall_variance_by_facet,
            "facet_independent_evidence_mass_by_facet": self.facet_independent_evidence_mass_by_facet,
            "misconception_posterior_by_error_type": self.misconception_posterior_by_error_type,
        }


@dataclass(frozen=True)
class ItemDemandVector:
    learning_object_id: str
    evidence_weights: dict[str, float]
    difficulty_b: float
    discrimination_a: float
    retrieval_demand: float
    transfer_distance: float
    scaffold_level: float
    surface_family: str | None
    misconception_targets: list[str]
    repair_targets: list[str]
    bad_item_suspicion: float

    def as_dict(self) -> dict[str, object]:
        return {
            "learning_object_id": self.learning_object_id,
            "evidence_weights": self.evidence_weights,
            "difficulty_b": self.difficulty_b,
            "discrimination_a": self.discrimination_a,
            "retrieval_demand": self.retrieval_demand,
            "transfer_distance": self.transfer_distance,
            "scaffold_level": self.scaffold_level,
            "surface_family": self.surface_family,
            "misconception_targets": self.misconception_targets,
            "repair_targets": self.repair_targets,
            "bad_item_suspicion": self.bad_item_suspicion,
        }


@dataclass(frozen=True)
class SelectionReward:
    intent: SchedulerIntent
    selection_reward: float
    components: dict[str, float]
    predicted_correctness: float
    ability_vector: LearnerAbilityVector
    item_demand_vector: ItemDemandVector
    ability_transition: dict[str, object]
    probe_eig_debug: dict[str, object]

    def as_components(self) -> dict[str, float]:
        return {
            **self.components,
            "predicted_correctness": self.predicted_correctness,
            "selection_reward": self.selection_reward,
        }

    def as_debug(self) -> dict[str, object]:
        return {
            "intent": self.intent.value,
            "selection_reward": self.selection_reward,
            "components": self.components,
            "predicted_correctness": self.predicted_correctness,
            "ability_vector": self.ability_vector.as_dict(),
            "item_demand_vector": self.item_demand_vector.as_dict(),
            "ability_transition": self.ability_transition,
            "probe_eig": self.probe_eig_debug,
        }


def score_selection_reward(
    vault: LoadedVault,
    item: PracticeItem,
    learning_object: LearningObject,
    *,
    mastery: MasteryState | None,
    facet_states: list[FacetRecallState],
    quality_state: PracticeItemQualityState | None,
    active_errors: list[ActiveErrorEvent],
    base_components: dict[str, float],
    probe_eig: float,
    probe_familiarity_discount: float = 1.0,
    intent: SchedulerIntent,
) -> SelectionReward:
    ability = ability_vector(
        learning_object.id,
        mastery,
        facet_states,
        active_errors,
        facet_aliases=vault.facet_aliases,
    )
    demand = item_demand_vector(vault, item, learning_object, quality_state)
    predicted = _predicted_correctness(vault, item, learning_object, ability, demand, mastery)
    facet_weakness = _facet_weakness(ability, demand)
    gradient_fit = _gradient_fit(predicted, intent)
    targeted_boundary_fit = _targeted_boundary_fit(ability, demand, gradient_fit)
    repair_value = _repair_value(demand, ability, active_errors)
    probe_eig_debug = probe_information_gain_components(
        ability,
        demand,
        hypothesis_eig=probe_eig,
        independent_evidence_discount=probe_familiarity_discount,
    )
    expected_gain = estimate_ability_transition(
        item,
        correctness=predicted,
        attempt_type=_default_attempt_type_for_reward(item, intent),
        target_facets=list(demand.evidence_weights),
        error_event_written=bool(active_errors),
    )
    expected_skill_gain = float(expected_gain.get("expected_skill_gain") or 0.0)
    repetition_fatigue = 0.25 if demand.bad_item_suspicion >= 0.65 and intent != SchedulerIntent.REPAIR else 0.0
    overload_penalty = _overload_penalty(predicted, intent)
    is_teach_back = item.practice_mode == "teach_back"
    # Teach-back rides the PROBE intent without a hypothesis set, so a zero
    # hypothesis EIG is expected, not a duplicate probe.
    duplicate_probe_penalty = (
        0.10 if intent == SchedulerIntent.PROBE and probe_eig <= 0 and not is_teach_back else 0.0
    )

    if intent == SchedulerIntent.PROBE:
        reward = (
            0.70 * float(probe_eig_debug["normalized_total"])
            + 0.10 * clamp(ability.lo_mastery_variance)
            + 0.10 * _facet_uncertainty(ability, demand)
            # Goal frontier now spans unexamined/known-gap AND solid-but-projected-
            # to-decay-below-target-by-due-date facets.
            + 0.10 * clamp(base_components.get("goal_frontier", 0.0))
            - duplicate_probe_penalty
        )
        if is_teach_back:
            # Small floor, not a new tunable weight (the priority-weight sweep
            # showed those are decision-inert): transfer escalation keeps
            # solid, low-EIG items weakly schedulable at low priority.
            reward = max(reward, TEACH_BACK_REWARD_FLOOR)
    elif intent == SchedulerIntent.REPAIR:
        reward = (
            0.30 * repair_value
            + 0.25 * gradient_fit
            + 0.20 * facet_weakness
            + 0.10 * targeted_boundary_fit
            + 0.15 * expected_skill_gain / 0.08
            + 0.10 * clamp(base_components.get("recent_error", 0.0))
            # Repairing gaps on goal-relevant facets ranks above off-goal repairs.
            + 0.15 * clamp(base_components.get("goal_frontier", 0.0))
            - overload_penalty
            - repetition_fatigue
        )
    else:
        reward = (
            0.20 * clamp(base_components.get("forgetting_risk", 0.0))
            # Goal frontier now spans unexamined/known-gap AND solid-but-projected-
            # to-decay-below-target-by-due-date facets.
            + 0.15 * clamp(base_components.get("goal_frontier", 0.0))
            + 0.20 * facet_weakness
            + 0.20 * gradient_fit
            + 0.15 * targeted_boundary_fit
            + 0.10 * expected_skill_gain / 0.08
            + 0.05 * clamp(demand.transfer_distance)
            - overload_penalty
            - repetition_fatigue
        )

    bounded_reward = clamp(reward, -1.0, 1.0)
    return SelectionReward(
        intent=intent,
        selection_reward=bounded_reward,
        components={
            "facet_weakness": facet_weakness,
            "gradient_fit": gradient_fit,
            "targeted_boundary_fit": targeted_boundary_fit,
            "repair_value": repair_value,
            "expected_skill_gain": expected_skill_gain,
            "overload_penalty": overload_penalty,
            "repetition_fatigue": repetition_fatigue,
            "duplicate_probe_penalty": duplicate_probe_penalty,
            "probe_eig_hypothesis": float(probe_eig_debug["hypothesis"]["reduction"]),
            "probe_eig_lo_mastery": float(probe_eig_debug["lo_mastery"]["reduction"]),
            "probe_eig_facet_recall": float(probe_eig_debug["facet_recall"]["reduction"]),
            "probe_eig_total": float(probe_eig_debug["total_reduction"]),
        },
        predicted_correctness=predicted,
        ability_vector=ability,
        item_demand_vector=demand,
        ability_transition=expected_gain,
        probe_eig_debug=probe_eig_debug,
    )


def ability_vector(
    learning_object_id: str,
    mastery: MasteryState | None,
    facet_states: list[FacetRecallState],
    active_errors: list[ActiveErrorEvent],
    *,
    facet_aliases: dict[str, str] | None = None,
) -> LearnerAbilityVector:
    lo_mastery = _sigmoid(mastery.logit_mean) if mastery is not None else 0.5
    lo_variance = clamp(mastery.logit_variance if mastery is not None else 1.0)
    aggregate_facets = _aggregate_facet_states(facet_states, facet_aliases or {})
    total_error = sum(max(error.severity, 0.0) for error in active_errors)
    misconception_posterior = {
        error.error_type: clamp(error.severity / total_error) if total_error > 0 else 0.0
        for error in active_errors
        if error.is_misconception
    }
    return LearnerAbilityVector(
        learning_object_id=learning_object_id,
        lo_mastery=lo_mastery,
        lo_mastery_variance=lo_variance,
        facet_recall_mean_by_facet={facet: clamp(state["mean"]) for facet, state in aggregate_facets.items()},
        facet_recall_variance_by_facet={facet: clamp(state["variance"]) for facet, state in aggregate_facets.items()},
        facet_independent_evidence_mass_by_facet={facet: max(state["mass"], 0.0) for facet, state in aggregate_facets.items()},
        misconception_posterior_by_error_type=misconception_posterior,
    )


def probe_information_gain_components(
    ability: LearnerAbilityVector,
    demand: ItemDemandVector,
    *,
    hypothesis_eig: float,
    independent_evidence_discount: float = 1.0,
) -> dict[str, object]:
    """MVP entropy-reduction decomposition for probe reward.

    Hypothesis EIG is the categorical component from the existing probe model.
    Continuous components use the same debug shape the full model needs:
    ``prior_entropy``, ``expected_posterior_entropy``, and ``reduction``. LO
    mastery uses the one-dimensional Gaussian entropy difference
    ``0.5 * log(prior_var / posterior_var)``. Facet recall uses stored beta
    variance as a documented approximation, with item evidence weights as the
    prospective observation surface.
    """

    lo_prior_variance = max(ability.lo_mastery_variance, 1e-6)
    discount = clamp(independent_evidence_discount)
    discounted_hypothesis_eig = max(hypothesis_eig, 0.0) * discount
    lo_information_fraction = clamp(sum(demand.evidence_weights.values()) * 0.35 * discount)
    lo_posterior_variance = max(lo_prior_variance * (1.0 - lo_information_fraction), 1e-6)
    lo_reduction = max(0.0, 0.5 * log(lo_prior_variance / lo_posterior_variance))

    facet_prior_entropy = 0.0
    facet_expected_entropy = 0.0
    for facet, raw_weight in demand.evidence_weights.items():
        weight = max(raw_weight, 0.0)
        if weight <= 0:
            continue
        variance = max(ability.facet_recall_variance_by_facet.get(facet, 0.25), 1e-6)
        evidence_mass = ability.facet_independent_evidence_mass_by_facet.get(facet, 0.0)
        information_fraction = clamp((weight * discount) / (evidence_mass + 2.0))
        posterior_variance = max(variance * (1.0 - information_fraction), 1e-6)
        facet_prior_entropy += weight * 0.5 * log(variance)
        facet_expected_entropy += weight * 0.5 * log(posterior_variance)
    facet_reduction = max(0.0, facet_prior_entropy - facet_expected_entropy)
    total = max(0.0, discounted_hypothesis_eig + lo_reduction + facet_reduction)
    normalized_total = clamp(total / 3.0)
    return {
        "hypothesis": {
            "prior_entropy": None,
            "expected_posterior_entropy": None,
            "reduction": discounted_hypothesis_eig,
            "raw_reduction": max(hypothesis_eig, 0.0),
        },
        "lo_mastery": {
            "prior_entropy": 0.5 * log(lo_prior_variance),
            "expected_posterior_entropy": 0.5 * log(lo_posterior_variance),
            "reduction": lo_reduction,
        },
        "facet_recall": {
            "prior_entropy": facet_prior_entropy,
            "expected_posterior_entropy": facet_expected_entropy,
            "reduction": facet_reduction,
        },
        "total_reduction": total,
        "normalized_total": normalized_total,
        "independent_evidence_discount": discount,
    }


def _aggregate_facet_states(
    facet_states: list[FacetRecallState],
    facet_aliases: dict[str, str],
) -> dict[str, dict[str, float]]:
    combined: dict[str, dict[str, float]] = {}
    for state in facet_states:
        if state.practice_item_id is not None:
            continue
        facet = facet_aliases.get(state.facet_id, state.facet_id)
        current = combined.setdefault(
            facet,
            {
                "alpha": 0.0,
                "beta": 0.0,
                "mass": 0.0,
            },
        )
        current["alpha"] += max(float(state.recall_alpha), 0.0)
        current["beta"] += max(float(state.recall_beta), 0.0)
        current["mass"] += max(float(state.independent_evidence_mass), 0.0)
    for state in combined.values():
        alpha = state["alpha"]
        beta = state["beta"]
        total = alpha + beta
        if total <= 0:
            state["mean"] = 0.5
            state["variance"] = 0.25
            continue
        state["mean"] = alpha / total
        state["variance"] = alpha * beta / ((total**2) * (total + 1.0))
    return combined


def item_demand_vector(
    vault: LoadedVault,
    item: PracticeItem,
    learning_object: LearningObject,
    quality_state: PracticeItemQualityState | None,
) -> ItemDemandVector:
    item_a, item_b = item_irt_params(item, learning_object, vault.config.mastery)
    rubric = vault.rubric_for_item(item)
    fatal_errors = [fatal.id for fatal in rubric.fatal_errors] if rubric is not None else []
    evidence_weights = item.evidence_weights or {facet: 1.0 for facet in item.evidence_facets}
    return ItemDemandVector(
        learning_object_id=learning_object.id,
        evidence_weights={facet: max(float(weight), 0.0) for facet, weight in evidence_weights.items()},
        difficulty_b=item_b,
        discrimination_a=item_a,
        retrieval_demand=item.retrieval_demand if item.retrieval_demand is not None else _mode_retrieval_demand(item.practice_mode),
        transfer_distance=item.transfer_distance if item.transfer_distance is not None else 0.0,
        scaffold_level=item.scaffold_level if item.scaffold_level is not None else _inferred_scaffold_level(item),
        surface_family=item.surface_family,
        misconception_targets=fatal_errors,
        repair_targets=item.repair_targets or list(evidence_weights),
        bad_item_suspicion=quality_state.bad_item_suspicion if quality_state is not None else 0.0,
    )


def _predicted_correctness(
    vault: LoadedVault,
    item: PracticeItem,
    learning_object: LearningObject,
    ability: LearnerAbilityVector,
    demand: ItemDemandVector,
    mastery: MasteryState | None,
) -> float:
    """Item predicted correctness — blueprint likelihood under mvp-0.7, else legacy.

    For a blueprint-bearing LO on an mvp-0.7 vault, the noisy-AND / guess-floor /
    max-over-recipes projection (§9.2) is the expected-performance source. The
    per-component recall is the mastery-blended ``predicted_facet_recall`` (the
    LO EKF as a prediction-only calibration residual, §9.2). Every other case —
    legacy vaults, and blueprint-less LOs (their flat ``evidence_facets`` union
    is a non-certifying compatibility blueprint, §15) — keeps the existing blend.
    """

    blend_count = vault.config.recall_coverage.facet_blend_evidence_count
    if is_canonical_state_vault(vault) and learning_object.blueprints:
        mastery_logit = mastery.logit_mean if mastery is not None else None
        mastery_evidence = mastery.evidence_count if mastery is not None else 0

        def component_recall(facet: str, _capability: str) -> float:
            canonical = vault.canonical_facet_id(facet)
            facet_mean = ability.facet_recall_mean_by_facet.get(canonical)
            facet_mass = ability.facet_independent_evidence_mass_by_facet.get(canonical, 0.0)
            return predicted_facet_recall(
                mastery_logit,
                mastery_evidence,
                facet_mean,
                facet_mass,
                blend_count,
            )

        success = predict_item_success(vault, item, learning_object, component_recall)
        if success is not None:
            return success
    return predicted_correctness_from_vectors(ability, demand, blend_count)


def predicted_correctness_from_vectors(
    ability: LearnerAbilityVector,
    demand: ItemDemandVector,
    facet_blend_evidence_count: float,
) -> float:
    irt = _sigmoid(demand.discrimination_a * (_logit(ability.lo_mastery) - demand.difficulty_b))
    facet_readiness = _weighted_facet_value(ability.facet_recall_mean_by_facet, demand.evidence_weights, default=ability.lo_mastery)
    facet_variance = _weighted_facet_value(ability.facet_recall_variance_by_facet, demand.evidence_weights, default=0.0)
    facet_weight = clamp(facet_variance / max(facet_blend_evidence_count, 0.1))
    base = (1.0 - facet_weight) * irt + facet_weight * facet_readiness
    scaffold_adjustment = 0.12 * demand.scaffold_level
    retrieval_penalty = 0.15 * demand.retrieval_demand * max(0.0, 0.55 - facet_readiness)
    bad_item_penalty = 0.10 * demand.bad_item_suspicion
    return clamp(base + scaffold_adjustment - retrieval_penalty - bad_item_penalty)


def predicted_facet_recall(
    mastery_logit_mean: float | None,
    mastery_evidence_count: int,
    facet_mean: float | None,
    facet_mass: float,
    blend_evidence_count: float,
) -> float:
    """Facet-level predicted recall: LO-mastery backbone, facet evidence overlay.

    One of the two sanctioned prediction blends (the other is the item-level
    ``predicted_correctness_from_vectors`` above); a future calibration pass
    must adjust both together. Unlike the item blend's variance weight (bounded
    near 0.06), the blend weight here is evidence-mass-based so accumulated
    facet evidence genuinely takes over from the mastery prior: the facet beta
    posterior is prior-dominated (mean pinned near 0.5) until several attempts
    land, while the mastery EKF moves quickly — so low-mass facets read as the
    LO mastery and high-mass facets read as their own recall evidence.

    The backbone only deserves the full ``blend_evidence_count`` pseudo-count
    when the mastery state is itself well-evidenced: its pseudo-count is capped
    at ``mastery_evidence_count`` so a one-attempt EKF cannot suppress strong
    facet evidence. An absent (or zero-evidence) mastery row carries no
    information; blending toward an arbitrary 0.5 would double-count the
    ignorance the beta variance already expresses, so we fall back to the facet
    mean alone (and 0.5 only when neither exists).
    """

    prior_count = min(max(blend_evidence_count, 0.0), float(max(mastery_evidence_count, 0)))
    if mastery_logit_mean is None or prior_count <= 0.0:
        if facet_mean is not None and facet_mass > 0.0:
            return clamp(facet_mean)
        return 0.5 if mastery_logit_mean is None else clamp(_sigmoid(mastery_logit_mean))
    lo_mastery = _sigmoid(mastery_logit_mean)
    if facet_mean is None:
        return clamp(lo_mastery)
    mass = max(facet_mass, 0.0)
    weight = mass / (mass + max(prior_count, 0.1))
    return clamp((1.0 - weight) * lo_mastery + weight * facet_mean)


def _gradient_fit(predicted_correctness: float, intent: SchedulerIntent) -> float:
    low, high = {
        SchedulerIntent.PROBE: (0.40, 0.60),
        SchedulerIntent.REPAIR: (0.75, 0.90),
        SchedulerIntent.TRANSFER: (0.60, 0.80),
    }.get(intent, (0.55, 0.75))
    if low <= predicted_correctness <= high:
        return 1.0
    distance = low - predicted_correctness if predicted_correctness < low else predicted_correctness - high
    return clamp(1.0 - distance / 0.40)


def _facet_weakness(ability: LearnerAbilityVector, demand: ItemDemandVector) -> float:
    means = {facet: 1.0 - value for facet, value in ability.facet_recall_mean_by_facet.items()}
    return _weighted_facet_value(means, demand.evidence_weights, default=1.0 - ability.lo_mastery)


def _facet_uncertainty(ability: LearnerAbilityVector, demand: ItemDemandVector) -> float:
    return _weighted_facet_value(ability.facet_recall_variance_by_facet, demand.evidence_weights, default=ability.lo_mastery_variance)


def _targeted_boundary_fit(
    ability: LearnerAbilityVector,
    demand: ItemDemandVector,
    gradient_fit: float,
) -> float:
    known_weights = {
        facet: max(weight, 0.0)
        for facet, weight in demand.evidence_weights.items()
        if weight > 0 and facet in ability.facet_recall_mean_by_facet
    }
    if not known_weights:
        return 0.0
    weakness = _weighted_facet_value(
        {
            facet: 1.0 - ability.facet_recall_mean_by_facet[facet]
            for facet in known_weights
        },
        known_weights,
        default=0.0,
    )
    return weakness * gradient_fit


def _repair_value(
    demand: ItemDemandVector,
    ability: LearnerAbilityVector,
    active_errors: list[ActiveErrorEvent],
) -> float:
    repair_targets = set(demand.repair_targets)
    error_targets = {error.error_type for error in active_errors if error.severity >= 0.5}
    weak_facets = {facet for facet, mean in ability.facet_recall_mean_by_facet.items() if mean < 0.55}
    overlap = repair_targets & (error_targets | weak_facets)
    if not repair_targets:
        return 0.0
    return clamp(len(overlap) / len(repair_targets))


def _overload_penalty(predicted_correctness: float, intent: SchedulerIntent) -> float:
    low = {
        SchedulerIntent.PROBE: 0.25,
        SchedulerIntent.REPAIR: 0.55,
    }.get(intent, 0.45)
    return clamp((low - predicted_correctness) / low) if predicted_correctness < low else 0.0


def _weighted_facet_value(values: dict[str, float], weights: dict[str, float], *, default: float) -> float:
    positive = {facet: max(weight, 0.0) for facet, weight in weights.items() if weight > 0}
    total = sum(positive.values())
    if total <= 0:
        return clamp(default)
    return clamp(sum((values.get(facet, default) * weight) for facet, weight in positive.items()) / total)


def _mode_retrieval_demand(practice_mode: str) -> float:
    return {
        "diagnostic_probe": 0.75,
        "short_answer": 0.80,
        "open_text": 0.85,
        "constructed_response": 0.90,
        "multiple_choice": 0.35,
        "self_report": 0.10,
        "teach_back": 0.9,
    }.get(practice_mode, 0.65)


def _inferred_scaffold_level(item: PracticeItem) -> float:
    if item.hints:
        return clamp(len(item.hints) / max(item.hint_policy.max_useful_hints or len(item.hints), 1))
    return 0.0


def _default_attempt_type_for_reward(item: PracticeItem, intent: SchedulerIntent) -> str:
    if intent == SchedulerIntent.REPAIR and "hinted_attempt" in item.attempt_types_allowed:
        return "hinted_attempt"
    return item.attempt_types_allowed[0] if item.attempt_types_allowed else "independent_attempt"


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = exp(-value)
        return 1 / (1 + z)
    z = exp(value)
    return z / (1 + z)


def _logit(value: float) -> float:
    clipped = clamp(value, 0.02, 0.98)
    return log(clipped / (1.0 - clipped))

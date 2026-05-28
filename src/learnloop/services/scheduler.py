from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from math import exp

from learnloop.clock import Clock, SystemClock, parse_utc
from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import ActiveErrorEvent, PracticeItemState, Repository
from learnloop.services.fsrs import forgetting_curve
from learnloop.services.probes import (
    HypothesisSet,
    current_hypothesis_set,
    probe_eig_component,
    resolve_item_irt,
)
from learnloop.services.recall_coverage import clamp, familiarity_discount, resolve_coverage
from learnloop.services.selection_rewards import SchedulerIntent, score_selection_reward
from learnloop.vault.models import ConceptEdge, Goal, LoadedVault, PracticeItem


@dataclass(frozen=True)
class SchedulerSession:
    session_id: str | None = None
    available_minutes: int | None = None
    energy: str | None = None


@dataclass(frozen=True)
class ScheduledItem:
    practice_item_id: str
    learning_object_id: str
    priority: float
    components: dict[str, float]
    readiness_factor: float | None
    selected_mode: str
    plain_english: list[str]
    reward_debug: dict[str, object] | None = None


def build_due_queue(
    vault: LoadedVault,
    repository: Repository,
    *,
    clock: Clock | None = None,
    session: SchedulerSession | None = None,
    limit: int | None = None,
    persist_explanations: bool = True,
) -> list[ScheduledItem]:
    now = (clock or SystemClock()).now().astimezone(UTC)
    session = session or SchedulerSession()
    config = vault.config
    item_states = repository.practice_item_states()
    mastery_states = repository.mastery_states()
    probe_states = repository.probe_states()
    errors_by_lo = _errors_by_learning_object(repository.active_error_events())
    goal_reachable = _goal_reachable_concepts(vault.goals, vault.edges)
    short_session = (
        session.available_minutes is not None
        and session.available_minutes <= config.scheduler.short_session_minutes
    )
    readiness_factor = _readiness_factor(session, config)
    hypothesis_set_cache: dict[str, HypothesisSet | None] = {}
    pending_followups = repository.pending_followup_practice_items()
    facet_states_by_lo = {
        learning_object_id: repository.facet_recall_states(learning_object_id)
        for learning_object_id in vault.learning_objects
    }

    queue: list[ScheduledItem] = []
    probe_item_ids: dict[str, str] = {}
    for item in vault.practice_items.values():
        state = item_states.get(item.id)
        if state is not None and not state.active:
            continue
        learning_object = vault.learning_object_for_item(item)
        if learning_object is None:
            continue
        mastery = mastery_states.get(learning_object.id)
        probe_state = probe_states.get(learning_object.id)
        in_probe = probe_state is not None and probe_state.status == "in_progress"
        if (mastery is None or mastery.last_evidence_at is None) and not in_probe:
            continue

        components: dict[str, float] = {
            "forgetting_risk": _forgetting_risk(state, now),
            "active_goal": _active_goal(learning_object.concept, vault.goals, goal_reachable),
            "recent_error": _recent_error(errors_by_lo.get(learning_object.id, []), now),
            "probe_eig": 0.0,
        }
        probe_familiarity_discount = 1.0

        if in_probe and probe_state.hypothesis_set_id is not None:
            hypothesis_set = _load_hypothesis_set(
                vault, repository, learning_object.id, probe_state, hypothesis_set_cache
            )
            if hypothesis_set is not None:
                item_a, item_b, probe_irt = resolve_item_irt(vault, item)
                rubric = vault.rubric_for_item(item)
                prospective_coverage = resolve_coverage(
                    item,
                    rubric,
                    attempt_type="diagnostic_probe",
                    hints_used=0,
                    learner_answer_md="prospective_probe",
                )
                prospective_familiarity = familiarity_discount(
                    repository,
                    item,
                    learning_object_id=learning_object.id,
                    covered_facets=prospective_coverage.covered_facets,
                    config=config,
                )
                candidate_probe_eig_raw = probe_eig_component(
                    hypothesis_set,
                    item,
                    rubric,
                    item_a=item_a,
                    item_b=item_b,
                    irt=probe_irt,
                )
                probe_familiarity_discount = prospective_familiarity.independent_evidence_discount
                candidate_probe_eig = candidate_probe_eig_raw * probe_familiarity_discount
                if not short_session or _priority(components, config) <= 0:
                    components["probe_eig"] = candidate_probe_eig
                    components["probe_eig_raw"] = candidate_probe_eig_raw
                    components["probe_eig_familiarity_discount"] = probe_familiarity_discount
                    probe_item_ids[item.id] = probe_state.hypothesis_set_id

        legacy_priority = _priority(components, config)
        intent = _intent_for_item(item, in_probe=in_probe, components=components)
        reward = score_selection_reward(
            vault,
            item,
            learning_object,
            mastery=mastery,
            facet_states=facet_states_by_lo.get(learning_object.id, []),
            quality_state=repository.practice_item_quality_state(item.id),
            active_errors=errors_by_lo.get(learning_object.id, []),
            base_components=components,
            probe_eig=components.get("probe_eig_raw", components["probe_eig"]),
            probe_familiarity_discount=probe_familiarity_discount,
            intent=intent,
        )
        components.update(reward.as_components())
        boundary_priority = 0.20 * max(0.0, components.get("targeted_boundary_fit", 0.0))
        components["boundary_target"] = boundary_priority
        components["legacy_priority"] = legacy_priority
        priority = max(legacy_priority, boundary_priority)
        if priority <= 0:
            continue
        queue.append(
            ScheduledItem(
                practice_item_id=item.id,
                learning_object_id=learning_object.id,
                priority=priority,
                components=components,
                readiness_factor=readiness_factor,
                selected_mode=item.practice_mode,
                plain_english=_plain_english(item, components),
                reward_debug=reward.as_debug(),
            )
        )

    queue.sort(
        key=lambda scheduled: (
            -scheduled.components.get("selection_reward", 0.0),
            -scheduled.priority,
            scheduled.practice_item_id,
        )
    )
    queue = _apply_seeded_exploration(queue, session, config, now)
    queue = _insert_pending_followups(vault, queue, pending_followups, readiness_factor)
    considered_queue = list(queue)
    if limit is not None:
        queue = queue[:limit]
    if persist_explanations and session.session_id is not None:
        selected_ids = {item.practice_item_id for item in queue}
        explanations = [
            _explanation_payload(item, selected=item.practice_item_id in selected_ids)
            for item in considered_queue
        ]
        repository.record_scheduler_slate(
            explanations,
            session_id=session.session_id,
            algorithm_version=config.algorithms.algorithm_version,
            requested_limit=limit,
            session_context=_session_context(session, short_session=short_session, readiness_factor=readiness_factor),
            config_snapshot=_scheduler_config_snapshot(config),
            selection_policy="selection_reward_v1",
            clock=clock,
        )
        repository.insert_scheduler_explanations(
            explanations,
            session_id=session.session_id,
            algorithm_version=config.algorithms.algorithm_version,
            retention_limit=config.scheduler.candidate_log_retention_limit,
            clock=clock,
        )
        _record_probe_elicitation(repository, queue, probe_item_ids, session, clock=clock)
    return queue


def _insert_pending_followups(
    vault: LoadedVault,
    queue: list[ScheduledItem],
    pending_followups: list[dict[str, str]],
    readiness_factor: float | None,
) -> list[ScheduledItem]:
    if not pending_followups:
        return queue

    max_priority = max((item.priority for item in queue), default=0.0)
    by_id = {item.practice_item_id: item for item in queue}
    followups: list[ScheduledItem] = []
    inserted_ids: set[str] = set()
    for index, pending in enumerate(pending_followups):
        practice_item_id = pending["practice_item_id"]
        if practice_item_id in inserted_ids:
            continue
        scheduled = by_id.get(practice_item_id)
        if scheduled is None:
            practice_item = vault.practice_items.get(practice_item_id)
            learning_object = vault.learning_object_for_item(practice_item) if practice_item is not None else None
            if practice_item is None or learning_object is None:
                continue
            scheduled = ScheduledItem(
                practice_item_id=practice_item.id,
                learning_object_id=learning_object.id,
                priority=0.0,
                components={
                    "forgetting_risk": 0.0,
                    "active_goal": 0.0,
                    "recent_error": 0.0,
                    "probe_eig": 0.0,
                },
                readiness_factor=readiness_factor,
                selected_mode=practice_item.practice_mode,
                plain_english=[],
                reward_debug=None,
            )
        components = dict(scheduled.components)
        action_type = pending.get("action_type") or "negative_surprise_followup"
        component = "intervention_followup" if action_type == "intervention_followup" else "negative_surprise_followup"
        reason = "intervention follow-up"
        components[component] = 1.0
        reasons = [reason] + [existing for existing in scheduled.plain_english if existing != reason]
        followups.append(
            replace(
                scheduled,
                priority=max_priority + len(pending_followups) - index,
                components=components,
                plain_english=reasons,
            )
        )
        inserted_ids.add(practice_item_id)

    if not followups:
        return queue
    return followups + [item for item in queue if item.practice_item_id not in inserted_ids]


def _load_hypothesis_set(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    probe_state,
    cache: dict[str, HypothesisSet | None],
) -> HypothesisSet | None:
    # The locked entry prior is updated with observed probe attempts so probe-EIG
    # is computed against the live posterior, not the entry prior. One hypothesis
    # set per LO probe phase, so the set id is a stable cache key.
    hypothesis_set_id = probe_state.hypothesis_set_id
    if hypothesis_set_id not in cache:
        cache[hypothesis_set_id] = current_hypothesis_set(vault, repository, learning_object_id)
    return cache[hypothesis_set_id]


def _record_probe_elicitation(
    repository: Repository,
    queue: list[ScheduledItem],
    probe_item_ids: dict[str, str],
    session: SchedulerSession,
    *,
    clock: Clock | None,
) -> None:
    probe_items = [item for item in queue if item.practice_item_id in probe_item_ids]
    if not probe_items:
        return
    selected = probe_items[0]
    repository.insert_elicitation_event(
        {
            "session_id": session.session_id,
            "selected_practice_item_id": selected.practice_item_id,
            "target_scope": {"learning_object_id": selected.learning_object_id},
            "policy": "probe_eig",
            "candidate_scores": {
                item.practice_item_id: item.components.get("probe_eig", 0.0) for item in probe_items
            },
            "expected_information_gain": selected.components.get("probe_eig", 0.0),
            "selected_reason": "highest probe expected information gain",
            "hypothesis_set_id": probe_item_ids[selected.practice_item_id],
            "trigger": "probe_phase_routine",
            "fallback_outcome": "existing_pi",
        },
        clock=clock,
    )


def explain_practice_item(vault: LoadedVault, repository: Repository, practice_item_id: str) -> ScheduledItem | None:
    queue = build_due_queue(vault, repository, persist_explanations=False)
    for item in queue:
        if item.practice_item_id == practice_item_id:
            return item
    return None


def _priority(components: dict[str, float], config: LearnLoopConfig) -> float:
    return (
        config.scheduler.forgetting_risk_weight * components["forgetting_risk"]
        + config.scheduler.active_goal_weight * components["active_goal"]
        + config.scheduler.recent_error_weight * components["recent_error"]
        + config.scheduler.probe_eig_weight * components["probe_eig"]
    )


def _apply_seeded_exploration(
    queue: list[ScheduledItem],
    session: SchedulerSession,
    config: LearnLoopConfig,
    now: datetime,
) -> list[ScheduledItem]:
    rate = clamp(config.scheduler.selection_exploration_rate)
    if rate <= 0 or session.session_id is None or len(queue) < 2:
        return queue
    if _stable_fraction("roll", session.session_id, now, [item.practice_item_id for item in queue]) >= rate:
        return queue
    best = queue[0]
    best_intent = (best.reward_debug or {}).get("intent")
    if best_intent == SchedulerIntent.PROBE.value:
        return queue
    best_reward = best.components.get("selection_reward", 0.0)
    window = max(config.scheduler.selection_exploration_reward_window, 0.0)
    alternatives = [
        item
        for item in queue[1:]
        if (item.reward_debug or {}).get("intent") != SchedulerIntent.PROBE.value
        and best_reward - item.components.get("selection_reward", 0.0) <= window
    ]
    if not alternatives:
        return queue
    index = int(
        _stable_fraction("choice", session.session_id, now, [item.practice_item_id for item in alternatives])
        * len(alternatives)
    )
    selected = alternatives[min(index, len(alternatives) - 1)]
    selected = replace(
        selected,
        components={
            **selected.components,
            "exploration_selected": 1.0,
            "exploration_rate": rate,
        },
        plain_english=[
            "seeded exploration"
        ] + [reason for reason in selected.plain_english if reason != "seeded exploration"],
    )
    return [selected] + [
        item
        for item in queue
        if item.practice_item_id != selected.practice_item_id
    ]


def _stable_fraction(label: str, session_id: str, now: datetime, candidate_ids: list[str]) -> float:
    seed = "|".join([label, session_id, now.date().isoformat(), *sorted(candidate_ids)])
    value = int.from_bytes(hashlib.sha256(seed.encode("utf-8")).digest()[:8], "big")
    return value / float(2**64 - 1)


def _intent_for_item(item: PracticeItem, *, in_probe: bool, components: dict[str, float]) -> SchedulerIntent:
    if in_probe and components.get("probe_eig", 0.0) > 0:
        return SchedulerIntent.PROBE
    if item.practice_mode == "diagnostic_probe":
        if components.get("recent_error", 0.0) > 0 and item.repair_targets:
            return SchedulerIntent.REPAIR
        return SchedulerIntent.PRACTICE
    if components.get("recent_error", 0.0) > 0 and item.repair_targets:
        return SchedulerIntent.REPAIR
    if (item.transfer_distance or 0.0) > 0.0:
        return SchedulerIntent.TRANSFER
    return SchedulerIntent.PRACTICE


def _readiness_factor(session: SchedulerSession, config: LearnLoopConfig) -> float | None:
    factors: list[float] = []
    if session.energy is not None:
        energy = session.energy.strip().lower()
        factors.append(
            {
                "low": 0.5,
                "medium": 0.75,
                "normal": 0.75,
                "high": 1.0,
            }.get(energy, 0.75)
        )
    if session.available_minutes is not None:
        short_minutes = max(1, config.scheduler.short_session_minutes)
        factors.append(max(0.0, min(1.0, session.available_minutes / short_minutes)))
    if not factors:
        return None
    return sum(factors) / len(factors)


def _session_context(
    session: SchedulerSession,
    *,
    short_session: bool,
    readiness_factor: float | None,
) -> dict[str, object]:
    return {
        "session_id": session.session_id,
        "available_minutes": session.available_minutes,
        "energy": session.energy,
        "short_session": short_session,
        "readiness_factor": readiness_factor,
    }


def _scheduler_config_snapshot(config: LearnLoopConfig) -> dict[str, object]:
    scheduler = config.scheduler
    return {
        "forgetting_risk_weight": scheduler.forgetting_risk_weight,
        "active_goal_weight": scheduler.active_goal_weight,
        "recent_error_weight": scheduler.recent_error_weight,
        "probe_eig_weight": scheduler.probe_eig_weight,
        "short_session_minutes": scheduler.short_session_minutes,
        "selection_exploration_rate": scheduler.selection_exploration_rate,
        "selection_exploration_reward_window": scheduler.selection_exploration_reward_window,
        "algorithm_version": config.algorithms.algorithm_version,
    }


def _forgetting_risk(state: PracticeItemState | None, now: datetime) -> float:
    if state is None or state.due_at is None:
        return 0.0
    due_at = parse_utc(state.due_at)
    if due_at is None or due_at > now:
        return 0.0
    if state.stability is None:
        return 1.0
    last_attempt_at = parse_utc(state.last_attempt_at) or due_at
    elapsed_days = max(0.0, (now - last_attempt_at).total_seconds() / 86400)
    return 1 - forgetting_curve(state.stability, elapsed_days)


def _active_goal(concept_id: str, goals: list[Goal], reachable_by_goal: dict[str, set[str]]) -> float:
    score = 0.0
    for goal in goals:
        if goal.status != "active":
            continue
        if concept_id in reachable_by_goal.get(goal.id, set()):
            score = max(score, goal.priority)
    return score


def _recent_error(errors: list[ActiveErrorEvent], now: datetime) -> float:
    score = 0.0
    for error in errors:
        created_at = parse_utc(error.created_at)
        if created_at is None:
            continue
        days_since = max(0.0, (now - created_at).total_seconds() / 86400)
        score = max(score, error.severity * exp(-days_since / 7))
    return score


def _errors_by_learning_object(errors: list[ActiveErrorEvent]) -> dict[str, list[ActiveErrorEvent]]:
    grouped: dict[str, list[ActiveErrorEvent]] = {}
    for error in errors:
        grouped.setdefault(error.learning_object_id, []).append(error)
    return grouped


def _goal_reachable_concepts(goals: list[Goal], edges: list[ConceptEdge]) -> dict[str, set[str]]:
    allowed_relations = {"prerequisite", "part_of"}
    reachable: dict[str, set[str]] = {}
    for goal in goals:
        concepts = set(goal.concept_anchors)
        for edge in edges:
            if edge.relation_type in allowed_relations and edge.source in goal.concept_anchors:
                concepts.add(edge.target)
        reachable[goal.id] = concepts
    return reachable


def _plain_english(item: PracticeItem, components: dict[str, float]) -> list[str]:
    reasons: list[str] = []
    if components["forgetting_risk"] > 0:
        reasons.append(f"forgetting risk {components['forgetting_risk']:.2f}")
    if components["active_goal"] > 0:
        reasons.append(f"active goal weight {components['active_goal']:.2f}")
    if components["recent_error"] > 0:
        reasons.append(f"recent error boost {components['recent_error']:.2f}")
    if components["probe_eig"] > 0:
        reasons.append(f"probe information gain {components['probe_eig']:.2f}")
    if components.get("boundary_target", 0.0) > 0:
        reasons.append(f"facet boundary fit {components['boundary_target']:.2f}")
    if components.get("selection_reward", 0.0) > 0:
        reasons.append(f"selection reward {components['selection_reward']:.2f}")
    if not reasons:
        reasons.append(f"{item.practice_mode} item is available")
    return reasons


def _explanation_payload(item: ScheduledItem, *, selected: bool = True) -> dict[str, object]:
    components = dict(item.components)
    components["selected"] = 1.0 if selected else 0.0
    return {
        "practice_item_id": item.practice_item_id,
        "selected_mode": item.selected_mode,
        "priority": item.priority,
        "components": components,
        "readiness_factor": item.readiness_factor,
        "plain_english": {"reasons": item.plain_english},
        "expected_information_gain": item.components.get("probe_eig", 0.0),
        "target_scope": {
            "learning_object_id": item.learning_object_id,
            "selection_reward": item.reward_debug,
        },
    }

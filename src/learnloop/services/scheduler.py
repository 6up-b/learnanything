from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from math import exp
from typing import Any

from learnloop.clock import Clock, SystemClock, parse_utc
from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import ActiveErrorEvent, PracticeItemState, Repository
from learnloop.services.fitted_params import resolve_fsrs_weights
from learnloop.services.fsrs import FSRS6_DEFAULT_WEIGHTS, forgetting_curve
from learnloop.services.probes import (
    HypothesisSet,
    current_hypothesis_set,
    probe_eig_component,
    resolve_item_irt,
)
from learnloop.numeric import clamp
from learnloop.services.goal_projection import build_goal_frontier
from learnloop.services.exam_pool import reserved_item_ids as reserved_exam_pool_item_ids
from learnloop.services.recall_coverage import (
    familiarity_discount,
    familiarity_discount_from_attempts,
    resolve_coverage,
)
from learnloop.services.selection_rewards import SchedulerIntent, score_selection_reward
from learnloop.vault.models import LoadedVault, PracticeItem


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
    # Items reserved for a goal's held-out exam are quarantined from practice so
    # the exam stays an honest, uncontaminated test (fetched once per build).
    reserved_item_ids = reserved_exam_pool_item_ids(repository)
    mastery_states = repository.mastery_states()
    probe_states = repository.probe_states()
    errors_by_lo = _errors_by_learning_object(repository.active_error_events())
    short_session = (
        session.available_minutes is not None
        and session.available_minutes <= config.scheduler.short_session_minutes
    )
    readiness_factor = _readiness_factor(session, config)
    fsrs_weights = resolve_fsrs_weights(repository)
    hypothesis_set_cache: dict[str, HypothesisSet | None] = {}
    pending_followups = repository.pending_followup_practice_items()
    facet_states_by_lo = {
        learning_object_id: repository.facet_recall_states(learning_object_id)
        for learning_object_id in vault.learning_objects
    }
    frontier = build_goal_frontier(
        vault,
        repository,
        clock=clock,
        item_states=item_states,
        facet_states_by_lo=facet_states_by_lo,
    )

    queue: list[ScheduledItem] = []
    probe_item_ids: dict[str, str] = {}
    recent_attempts_by_lo: dict[str, list[dict[str, Any]]] = {}
    for item in vault.practice_items.values():
        state = item_states.get(item.id)
        if state is not None and not state.active:
            continue
        if item.id in reserved_item_ids:
            continue
        learning_object = vault.learning_object_for_item(item)
        if learning_object is None:
            continue
        mastery = mastery_states.get(learning_object.id)
        probe_state = probe_states.get(learning_object.id)
        in_probe = probe_state is not None and probe_state.status == "in_progress"
        frontier_entry = frontier.by_lo.get(learning_object.id)
        # Cold-start gate: never-attempted LOs stay out of the routine queue —
        # EXCEPT when the LO is on an active goal's at-risk frontier. The
        # frontier's widened semantics put unexamined facets at risk precisely
        # so the goal's untouched material gets scheduled before the due date;
        # skipping those items here would leave "practice at-risk facets"
        # re-serving the goal's only attempted item.
        if (mastery is None or mastery.last_evidence_at is None) and not in_probe and frontier_entry is None:
            continue

        goal_frontier_component = _goal_frontier(vault, item, frontier_entry)
        components: dict[str, float] = {
            "forgetting_risk": _forgetting_risk(state, now, fsrs_weights),
            "recent_error": _recent_error(errors_by_lo.get(learning_object.id, []), now),
            "probe_eig": 0.0,
        }
        if goal_frontier_component > 0:
            # Exposure discount: evidence from re-serving a just-attempted item
            # (or its surface family) is dependent evidence, worth less toward
            # the goal — and without this the argmax re-serves the same frontier
            # item after every failure. Reuses the follow-up/probe familiarity
            # machinery; no new constants.
            recent = recent_attempts_by_lo.get(learning_object.id)
            if recent is None:
                recent = repository.list_recent_attempts_by_learning_object(
                    learning_object.id,
                    limit=config.recall_coverage.familiarity_recent_attempt_window,
                )
                recent_attempts_by_lo[learning_object.id] = recent
            exposure = familiarity_discount_from_attempts(
                recent,
                item,
                covered_facets={str(facet): 1.0 for facet in item.evidence_facets},
                config=config,
            ).independent_evidence_discount
            components["goal_frontier_exposure_discount"] = exposure
            goal_frontier_component *= exposure
        components["goal_frontier"] = goal_frontier_component
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
                    evidence=vault.config.evidence,
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
        if item.practice_mode == "teach_back":
            # Small floor (not a new weight): transfer escalation keeps solid
            # items weakly schedulable, so a teach_back item must survive the
            # zero-priority filter and rank by its selection reward.
            priority = max(priority, _TEACH_BACK_PRIORITY_FLOOR)
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
    # Propensity is computed on the greedy-sorted order, before exploration reorders
    # it: it is P(this candidate is served | slate) under the seeded exploration
    # policy, which is what off-policy estimation reweights by.
    propensity_by_id = _selection_propensities(queue, session, config)
    queue = _apply_seeded_exploration(queue, session, config, now)
    queue = _enforce_teach_back_session_cap(queue, config.teach_back.session_cap)
    # Goal-composition quota: guarantee a floor share of goal-frontier items in the
    # ordered queue while a goal has at-risk facets. Applied before the limit slice
    # so the floor holds even in short sessions, and before follow-up insertion
    # (force-inserted follow-ups are a separate triggered decision).
    queue = _apply_goal_quota(queue, frontier.quota_floor)
    queue = _rotate_same_day_frontier_repeats(queue, item_states, now)
    queue = _insert_pending_followups(vault, queue, pending_followups, readiness_factor)
    considered_queue = list(queue)
    if limit is not None:
        queue = queue[:limit]
    if persist_explanations and session.session_id is not None:
        selected_ids = {item.practice_item_id for item in queue}
        explanations = [
            _explanation_payload(
                item,
                selected=item.practice_item_id in selected_ids,
                selection_propensity=propensity_by_id.get(item.practice_item_id),
            )
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
                    "goal_frontier": 0.0,
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


# Floor keeping teach_back items schedulable at low priority (transfer
# escalation on solid items). A constant, not a config weight: the scheduler
# priority-weight sweep showed those knobs are decision-inert.
_TEACH_BACK_PRIORITY_FLOOR = 0.05


def _rotate_same_day_frontier_repeats(
    queue: list[ScheduledItem],
    item_states: dict[str, PracticeItemState],
    now: datetime,
) -> list[ScheduledItem]:
    """Within goal-frontier queue slots, serve items not yet attempted today first.

    The at-risk treadmill: with no exposure term a failed frontier item stays
    argmax, so "practice at-risk facets" re-serves the same problem all day.
    Frontier items keep their queue slots as a group (non-frontier positions
    are untouched); within those slots, items attempted on the current UTC day
    sort after fresh ones, preserving reward order inside each half. If every
    frontier item was already attempted today the order is unchanged — the
    pool is genuinely exhausted and generation, not rotation, is the fix.
    """

    slots = [
        index
        for index, scheduled in enumerate(queue)
        if scheduled.components.get("goal_frontier", 0.0) > 0
    ]
    if len(slots) < 2:
        return queue
    today = now.strftime("%Y-%m-%d")

    def attempted_today(scheduled: ScheduledItem) -> int:
        state = item_states.get(scheduled.practice_item_id)
        last = state.last_attempt_at if state is not None else None
        return 1 if last is not None and last[:10] == today else 0

    rotated = sorted((queue[index] for index in slots), key=attempted_today)
    reordered = list(queue)
    for index, scheduled in zip(slots, rotated):
        reordered[index] = scheduled
    return reordered


def _enforce_teach_back_session_cap(queue: list[ScheduledItem], cap: int) -> list[ScheduledItem]:
    """Keep at most ``cap`` teach_back items per built queue (config
    ``teach_back.session_cap``), preserving order for everything else."""

    capped: list[ScheduledItem] = []
    teach_back_count = 0
    for scheduled in queue:
        if scheduled.selected_mode == "teach_back":
            if teach_back_count >= cap:
                continue
            teach_back_count += 1
        capped.append(scheduled)
    return capped


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
        + config.scheduler.goal_frontier_weight * components.get("goal_frontier", 0.0)
        + config.scheduler.recent_error_weight * components["recent_error"]
        + config.scheduler.probe_eig_weight * components["probe_eig"]
    )


def _selection_propensities(
    queue: list[ScheduledItem],
    session: SchedulerSession,
    config: LearnLoopConfig,
) -> dict[str, float]:
    """``P(item is served as the top candidate | slate)`` under seeded exploration.

    Mirrors the gating of `_apply_seeded_exploration` exactly so the logged
    propensity is the true probability the (stochastic) selection policy serves each
    candidate. The seeded hash is the policy's *randomization source*, so the
    propensity is the design probability — ``1 - rate`` on the greedy best and
    ``rate`` split uniformly over the eligible near-tie alternatives — not the
    realized deterministic outcome. Logging the design probability (rather than a
    degenerate 1.0/0.0) is what makes IPS / doubly-robust off-policy estimation
    identifiable across the logged dataset.

    Scope is the selection-reward policy over its candidates; force-inserted pending
    follow-ups (a separate, triggered decision) are not in this map and are logged
    with a NULL propensity by the caller.
    """

    if not queue:
        return {}
    propensity = {item.practice_item_id: 0.0 for item in queue}
    best = queue[0]

    def greedy() -> dict[str, float]:
        propensity[best.practice_item_id] = 1.0
        return propensity

    rate = clamp(config.scheduler.selection_exploration_rate)
    if rate <= 0 or session.session_id is None or len(queue) < 2:
        return greedy()
    if (best.reward_debug or {}).get("intent") == SchedulerIntent.PROBE.value:
        return greedy()
    best_reward = best.components.get("selection_reward", 0.0)
    window = max(config.scheduler.selection_exploration_reward_window, 0.0)
    alternatives = [
        item
        for item in queue[1:]
        if (item.reward_debug or {}).get("intent") != SchedulerIntent.PROBE.value
        and best_reward - item.components.get("selection_reward", 0.0) <= window
    ]
    if not alternatives:
        return greedy()
    propensity[best.practice_item_id] = 1.0 - rate
    share = rate / len(alternatives)
    for item in alternatives:
        propensity[item.practice_item_id] = share
    return propensity


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
    # Teach-back is elicitation, not retrieval practice: its reward is the
    # probe-EIG-style expected information gain over the item's facet pool
    # (existing PROBE machinery, no new priority weights).
    if item.practice_mode == "teach_back":
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
        "goal_frontier_weight": scheduler.goal_frontier_weight,
        "goal_quota_floor_min": scheduler.goal_quota_floor_min,
        "goal_quota_floor_max": scheduler.goal_quota_floor_max,
        "goal_quota_ramp_days": scheduler.goal_quota_ramp_days,
        "recent_error_weight": scheduler.recent_error_weight,
        "probe_eig_weight": scheduler.probe_eig_weight,
        "short_session_minutes": scheduler.short_session_minutes,
        "selection_exploration_rate": scheduler.selection_exploration_rate,
        "selection_exploration_reward_window": scheduler.selection_exploration_reward_window,
        "algorithm_version": config.algorithms.algorithm_version,
    }


def _forgetting_risk(
    state: PracticeItemState | None,
    now: datetime,
    weights: tuple[float, ...] = FSRS6_DEFAULT_WEIGHTS,
) -> float:
    if state is None or state.due_at is None:
        return 0.0
    due_at = parse_utc(state.due_at)
    if due_at is None or due_at > now:
        return 0.0
    if state.stability is None:
        return 1.0
    last_attempt_at = parse_utc(state.last_attempt_at) or due_at
    elapsed_days = max(0.0, (now - last_attempt_at).total_seconds() / 86400)
    return 1 - forgetting_curve(state.stability, elapsed_days, weights)


def _goal_frontier(vault: LoadedVault, item: PracticeItem, entry) -> float:
    """Fraction of the item's evidence facets on its LO's goal frontier, scaled by goal priority.

    ``entry`` is the ``FrontierEntry`` for the item's LO (or ``None``). The frontier
    now spans unexamined/known-gap facets AND solid facets projected to decay below
    the goal's target_recall by its due date. The frontier's facet ids are canonical,
    so item evidence facets are canonicalized before the overlap.
    """

    if entry is None or not entry.facets or entry.goal_priority <= 0:
        return 0.0
    facets = [vault.canonical_facet_id(str(facet)) for facet in item.evidence_facets]
    if not facets:
        return 0.0
    overlap = sum(1 for facet in facets if facet in entry.facets) / len(facets)
    return entry.goal_priority * overlap


def _apply_goal_quota(queue: list[ScheduledItem], floor: float) -> list[ScheduledItem]:
    """Reorder-only greedy quota guaranteeing a floor share of goal-frontier items.

    Composition gating (not a score weight): walk output positions ``k = 1..n``
    maintaining the running goal share; whenever it would fall below ``floor`` and a
    goal item remains, pull the highest-ranked remaining goal item forward, else emit
    the highest-ranked remaining item. Relative order is otherwise preserved (stable).
    """

    if floor <= 0:
        return queue

    def is_goal(item: ScheduledItem) -> bool:
        return item.components.get("goal_frontier", 0.0) > 0

    if not any(is_goal(item) for item in queue):
        return queue

    remaining = list(queue)
    result: list[ScheduledItem] = []
    goal_count = 0
    reason = f"goal quota: pulled forward (floor {floor:.2f})"
    while remaining:
        k = len(result) + 1
        if goal_count < floor * k and any(is_goal(item) for item in remaining):
            index = next(i for i, item in enumerate(remaining) if is_goal(item))
        else:
            index = 0
        chosen = remaining.pop(index)
        if index > 0:
            # Pulled ahead of higher-ranked non-goal items it would otherwise trail.
            chosen = replace(
                chosen,
                plain_english=[reason] + [existing for existing in chosen.plain_english if existing != reason],
            )
        if is_goal(chosen):
            goal_count += 1
        result.append(chosen)
    return result


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


def _plain_english(item: PracticeItem, components: dict[str, float]) -> list[str]:
    reasons: list[str] = []
    if components["forgetting_risk"] > 0:
        reasons.append(f"forgetting risk {components['forgetting_risk']:.2f}")
    if components.get("goal_frontier", 0.0) > 0:
        reasons.append(f"goal frontier weight {components['goal_frontier']:.2f}")
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


def _explanation_payload(
    item: ScheduledItem,
    *,
    selected: bool = True,
    selection_propensity: float | None = None,
) -> dict[str, object]:
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
        "selection_propensity": selection_propensity,
        # Realized flag: set only on the candidate actually promoted by exploration
        # (`_apply_seeded_exploration` tags it `exploration_selected`).
        "exploration_flag": 1 if float(item.components.get("exploration_selected") or 0.0) > 0.0 else 0,
        "target_scope": {
            "learning_object_id": item.learning_object_id,
            "selection_reward": item.reward_debug,
        },
    }

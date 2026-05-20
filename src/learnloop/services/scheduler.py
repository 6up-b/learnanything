from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from math import exp

from learnloop.clock import Clock, SystemClock, parse_utc
from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import ActiveErrorEvent, PracticeItemState, Repository
from learnloop.services.fsrs import forgetting_curve
from learnloop.services.probes import HypothesisSet, probe_eig_component
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
    selected_mode: str
    plain_english: list[str]


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
    hypothesis_set_cache: dict[str, HypothesisSet | None] = {}
    pending_followup_ids = repository.pending_followup_practice_item_ids()

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

        probe_eig = 0.0
        if in_probe and not short_session and probe_state.hypothesis_set_id is not None:
            hypothesis_set = _load_hypothesis_set(
                repository, probe_state.hypothesis_set_id, hypothesis_set_cache
            )
            if hypothesis_set is not None:
                probe_eig = probe_eig_component(hypothesis_set, item, vault.rubric_for_item(item))
                probe_item_ids[item.id] = probe_state.hypothesis_set_id

        components = {
            "forgetting_risk": _forgetting_risk(state, now),
            "active_goal": _active_goal(learning_object.concept, vault.goals, goal_reachable),
            "recent_error": _recent_error(errors_by_lo.get(learning_object.id, []), now),
            "probe_eig": probe_eig,
        }

        priority = _priority(components, config)
        if priority <= 0:
            continue
        queue.append(
            ScheduledItem(
                practice_item_id=item.id,
                learning_object_id=learning_object.id,
                priority=priority,
                components=components,
                selected_mode=item.practice_mode,
                plain_english=_plain_english(item, components),
            )
        )

    queue.sort(key=lambda scheduled: (-scheduled.priority, scheduled.practice_item_id))
    queue = _insert_pending_followups(vault, queue, pending_followup_ids)
    if limit is not None:
        queue = queue[:limit]
    if persist_explanations:
        repository.insert_scheduler_explanations(
            [_explanation_payload(item) for item in queue],
            session_id=session.session_id,
            algorithm_version=config.algorithms.algorithm_version,
            clock=clock,
        )
        _record_probe_elicitation(repository, queue, probe_item_ids, session, clock=clock)
    return queue


def _insert_pending_followups(
    vault: LoadedVault,
    queue: list[ScheduledItem],
    pending_followup_ids: list[str],
) -> list[ScheduledItem]:
    if not pending_followup_ids:
        return queue

    max_priority = max((item.priority for item in queue), default=0.0)
    by_id = {item.practice_item_id: item for item in queue}
    followups: list[ScheduledItem] = []
    inserted_ids: set[str] = set()
    for index, practice_item_id in enumerate(pending_followup_ids):
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
                selected_mode=practice_item.practice_mode,
                plain_english=[],
            )
        components = dict(scheduled.components)
        components["negative_surprise_followup"] = 1.0
        reasons = ["negative surprise follow-up"] + [
            reason for reason in scheduled.plain_english if reason != "negative surprise follow-up"
        ]
        followups.append(
            replace(
                scheduled,
                priority=max_priority + len(pending_followup_ids) - index,
                components=components,
                plain_english=reasons,
            )
        )
        inserted_ids.add(practice_item_id)

    if not followups:
        return queue
    return followups + [item for item in queue if item.practice_item_id not in inserted_ids]


def _load_hypothesis_set(
    repository: Repository,
    hypothesis_set_id: str,
    cache: dict[str, HypothesisSet | None],
) -> HypothesisSet | None:
    if hypothesis_set_id not in cache:
        record = repository.fetch_hypothesis_set(hypothesis_set_id)
        cache[hypothesis_set_id] = HypothesisSet.from_record(record) if record is not None else None
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
    if not reasons:
        reasons.append(f"{item.practice_mode} item is available")
    return reasons


def _explanation_payload(item: ScheduledItem) -> dict[str, object]:
    return {
        "practice_item_id": item.practice_item_id,
        "selected_mode": item.selected_mode,
        "priority": item.priority,
        "components": item.components,
        "plain_english": {"reasons": item.plain_english},
        "expected_information_gain": item.components.get("probe_eig", 0.0),
    }

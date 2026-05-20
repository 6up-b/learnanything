from __future__ import annotations

from dataclasses import dataclass

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import MasteryState, Repository
from learnloop.services.mastery import initial_mastery_state
from learnloop.vault.hashes import practice_item_hash
from learnloop.vault.models import ConceptEdge, Goal, LoadedVault


@dataclass(frozen=True)
class StateSyncResult:
    practice_item_states_created: int = 0
    practice_item_states_updated: int = 0
    practice_item_states_deactivated: int = 0
    mastery_states_created: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "practice_item_states_created": self.practice_item_states_created,
            "practice_item_states_updated": self.practice_item_states_updated,
            "practice_item_states_deactivated": self.practice_item_states_deactivated,
            "mastery_states_created": self.mastery_states_created,
        }


def sync_vault_state(
    vault: LoadedVault,
    repository: Repository,
    *,
    clock: Clock | None = None,
) -> StateSyncResult:
    """Reconcile YAML-owned entities with derived SQLite rows.

    The MVP policy for Practice Item content-hash changes is conservative:
    refresh the hash and reactivate the item, while preserving existing FSRS
    memory state until replay/content-event machinery exists.
    """

    created_items = 0
    updated_items = 0
    deactivated_items = 0
    created_mastery = 0

    item_states = repository.practice_item_states()
    now = utc_now_iso(clock)
    live_item_ids = set(vault.practice_items)

    for item_id, item in vault.practice_items.items():
        content_hash = practice_item_hash(item)
        state = item_states.get(item_id)
        if state is None:
            repository.upsert_practice_item_state(
                item_id,
                active=True,
                content_hash=content_hash,
                clock=clock,
            )
            created_items += 1
            continue

        if (not state.active) or state.content_hash != content_hash:
            repository.upsert_practice_item_state(
                item_id,
                difficulty=state.difficulty,
                stability=state.stability,
                retrievability=state.retrievability,
                due_at=state.due_at,
                active=True,
                content_hash=content_hash,
                last_attempt_at=state.last_attempt_at,
                clock=clock,
            )
            updated_items += 1

    for item_id, state in item_states.items():
        if item_id in live_item_ids or not state.active:
            continue
        repository.upsert_practice_item_state(
            item_id,
            difficulty=state.difficulty,
            stability=state.stability,
            retrievability=state.retrievability,
            due_at=state.due_at,
            active=False,
            content_hash=state.content_hash,
            last_attempt_at=state.last_attempt_at,
            clock=clock,
        )
        deactivated_items += 1

    mastery_states = repository.mastery_states()
    for learning_object_id, learning_object in vault.learning_objects.items():
        if learning_object_id in mastery_states:
            continue
        repository.upsert_mastery_state(
            initial_mastery_state(
                learning_object_id,
                vault.config.algorithms.algorithm_version,
                now,
            )
        )
        created_mastery += 1
        if learning_object.status == "active" and _active_goal_score(
            learning_object.concept,
            vault.goals,
            vault.edges,
        ) > 0:
            _enter_initial_probe_if_possible(vault, repository, learning_object_id, clock=clock)

    return StateSyncResult(
        practice_item_states_created=created_items,
        practice_item_states_updated=updated_items,
        practice_item_states_deactivated=deactivated_items,
        mastery_states_created=created_mastery,
    )


def _enter_initial_probe_if_possible(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    clock: Clock | None,
) -> None:
    if repository.probe_state(learning_object_id) is not None:
        return
    has_local_item = any(item.learning_object_id == learning_object_id for item in vault.practice_items.values())
    if has_local_item:
        from learnloop.services.probes import enter_probe

        enter_probe(vault, repository, learning_object_id, clock=clock)
        return
    repository.insert_elicitation_event(
        {
            "session_id": None,
            "selected_practice_item_id": None,
            "target_scope": {"learning_object_id": learning_object_id},
            "policy": "probe_eig",
            "candidate_scores": {},
            "expected_information_gain": 0.0,
            "selected_reason": "no existing Practice Item can probe this new active-goal Learning Object",
            "hypothesis_set_id": None,
            "trigger": "probe_phase_local_pi_inadequate",
            "fallback_outcome": "existing_pi_inadequate",
        },
        clock=clock,
    )


def _active_goal_score(concept_id: str, goals: list[Goal], edges: list[ConceptEdge]) -> float:
    reachable = _goal_reachable_concepts(goals, edges)
    score = 0.0
    for goal in goals:
        if goal.status == "active" and concept_id in reachable.get(goal.id, set()):
            score = max(score, goal.priority)
    return score


def _goal_reachable_concepts(goals: list[Goal], edges: list[ConceptEdge]) -> dict[str, set[str]]:
    reachable: dict[str, set[str]] = {}
    for goal in goals:
        concepts = set(goal.concept_anchors)
        for edge in edges:
            if edge.relation_type in {"prerequisite", "part_of"} and edge.source in goal.concept_anchors:
                concepts.add(edge.target)
        reachable[goal.id] = concepts
    return reachable

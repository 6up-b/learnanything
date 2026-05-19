from __future__ import annotations

from dataclasses import dataclass

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import MasteryState, Repository
from learnloop.services.mastery import initial_mastery_state
from learnloop.vault.hashes import practice_item_hash
from learnloop.vault.models import LoadedVault


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
    for learning_object_id in vault.learning_objects:
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

    return StateSyncResult(
        practice_item_states_created=created_items,
        practice_item_states_updated=updated_items,
        practice_item_states_deactivated=deactivated_items,
        mastery_states_created=created_mastery,
    )

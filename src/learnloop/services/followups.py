from __future__ import annotations

from dataclasses import dataclass

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.probes import HypothesisSet, probe_eig_component
from learnloop.vault.models import LoadedVault, PracticeItem

FOLLOWUP_ACTION = "negative_surprise_followup"


@dataclass(frozen=True)
class FollowupDecision:
    triggered: bool
    practice_item_id: str | None
    reason: str
    triggered_actions: list[str]
    suppressed_actions: list[str]


def evaluate_negative_surprise_followup(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    learning_object_id: str,
    practice_item_id: str,
    surprise_direction: str,
    bayesian_surprise: float,
    grader_confidence: float | None,
    error_event_written: bool,
    available_minutes: int | None = None,
    clock: Clock | None = None,
) -> FollowupDecision:
    """Decide whether a negative-surprise follow-up Practice Item should fire.

    Implements the §10 gate. When a follow-up fires, the chosen item id is
    recorded in ``attempt_surprise.triggered_actions_json``; when blocked, the
    reason is recorded in ``attempt_surprise.suppressed_actions_json``.
    """

    config = vault.config.scheduler.followup

    if surprise_direction != "negative":
        return _decision(False, None, "not_negative", [], [])
    if bayesian_surprise <= config.tau_followup_nats:
        return _decision(False, None, "below_threshold", [], [])
    if not error_event_written:
        return _decision(False, None, "no_error_event", [], [])
    if grader_confidence is None or grader_confidence < config.gamma_min:
        return _decision(False, None, "low_grader_confidence", [], [])

    if available_minutes is not None and available_minutes <= 0:
        suppressed = [f"{FOLLOWUP_ACTION}:no_time"]
        repository.update_attempt_surprise_actions(attempt_id, suppressed_actions=suppressed)
        return _decision(False, None, f"{FOLLOWUP_ACTION}:no_time", [], suppressed)

    candidate = _choose_followup_item(
        vault,
        repository,
        learning_object_id=learning_object_id,
        exclude_practice_item_id=practice_item_id,
    )
    if candidate is None:
        suppressed = [f"{FOLLOWUP_ACTION}:no_suitable_item"]
        repository.update_attempt_surprise_actions(attempt_id, suppressed_actions=suppressed)
        return _decision(False, None, f"{FOLLOWUP_ACTION}:no_suitable_item", [], suppressed)

    triggered = [f"{FOLLOWUP_ACTION}:{candidate.id}"]
    repository.update_attempt_surprise_actions(attempt_id, triggered_actions=triggered)
    return _decision(True, candidate.id, FOLLOWUP_ACTION, triggered, [])


def _choose_followup_item(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_id: str,
    exclude_practice_item_id: str,
) -> PracticeItem | None:
    candidates = [
        item
        for item in vault.practice_items.values()
        if item.learning_object_id == learning_object_id and item.id != exclude_practice_item_id
    ]
    if not candidates:
        return None

    probe_state = repository.probe_state(learning_object_id)
    if probe_state is not None and probe_state.status == "in_progress" and probe_state.hypothesis_set_id:
        record = repository.fetch_hypothesis_set(probe_state.hypothesis_set_id)
        if record is not None:
            hypothesis_set = HypothesisSet.from_record(record)
            candidates.sort(
                key=lambda item: (
                    -probe_eig_component(hypothesis_set, item, vault.rubric_for_item(item)),
                    item.id,
                )
            )
            return candidates[0]

    candidates.sort(key=lambda item: item.id)
    return candidates[0]


def _decision(
    triggered: bool,
    practice_item_id: str | None,
    reason: str,
    triggered_actions: list[str],
    suppressed_actions: list[str],
) -> FollowupDecision:
    return FollowupDecision(
        triggered=triggered,
        practice_item_id=practice_item_id,
        reason=reason,
        triggered_actions=triggered_actions,
        suppressed_actions=suppressed_actions,
    )

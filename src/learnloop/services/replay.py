from __future__ import annotations

from dataclasses import dataclass

from learnloop.clock import Clock, FrozenClock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptResult, GradeAttribution, replay_existing_attempt
from learnloop.vault.models import LoadedVault


@dataclass(frozen=True)
class ReplayResult:
    learning_object_id: str
    replayed_attempts: int
    attempt_ids: list[str]

    def as_dict(self) -> dict[str, object]:
        return {
            "learning_object_id": self.learning_object_id,
            "replayed_attempts": self.replayed_attempts,
            "attempt_ids": self.attempt_ids,
        }


@dataclass(frozen=True)
class RebuildResult:
    algorithm_version: str
    rebuilt_learning_objects: int
    replayed_attempts: int
    learning_object_ids: list[str]
    marker_id: str | None = None

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "algorithm_version": self.algorithm_version,
            "rebuilt_learning_objects": self.rebuilt_learning_objects,
            "replayed_attempts": self.replayed_attempts,
            "learning_object_ids": self.learning_object_ids,
        }
        if self.marker_id is not None:
            payload["marker_id"] = self.marker_id
        return payload


def replay_learning_object(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    error_attribution_overrides: dict[str, list[GradeAttribution]] | None = None,
) -> ReplayResult:
    """Rebuild attempt-derived state for one learning object from persisted grades.

    Replay intentionally does not call Codex or any AI provider. It treats
    `practice_attempts` plus current non-superseded `grading_evidence` as the raw
    log, clears derived state for the learning object, then runs each attempt
    through the same computation path used by live attempts.
    """

    attempts = repository.list_attempts_by_learning_object(learning_object_id)
    existing_error_events = {
        attempt["id"]: repository.error_events_for_attempt(attempt["id"])
        for attempt in attempts
    }
    repository.reset_learning_object_derived_state(learning_object_id)
    replayed: list[AttemptResult] = []
    for attempt in attempts:
        observed_at = parse_utc(attempt.get("created_at"))
        clock = FrozenClock(observed_at) if observed_at is not None else None
        override_attributions = (error_attribution_overrides or {}).get(attempt["id"])
        event_snapshot = existing_error_events.get(attempt["id"], [])
        replayed.append(
            replay_existing_attempt(
                vault,
                repository,
                attempt,
                clock=clock,
                error_event_ids=None if override_attributions is not None else [event["id"] for event in event_snapshot],
                error_events=event_snapshot,
                error_attributions=override_attributions,
            )
        )
    # spec §7: registry links survive replay (persisted misconception_id on the
    # error events is re-threaded through GradeAttribution). Replay never
    # re-normalizes, but it re-derives resolution status deterministically from
    # the replayed attempts so a rebuilt vault matches the live one.
    from learnloop.services.misconceptions import update_misconception_posteriors_and_resolve

    update_misconception_posteriors_and_resolve(
        vault, repository, learning_object_id=learning_object_id
    )
    # KM2 §7.1: canonical shared belief is vault-level, so it is recomputed as a
    # whole-ledger projection (no-op under mvp-0.6). Idempotent and deterministic,
    # so replaying any subset of LOs reproduces byte-identical canonical state.
    from learnloop.services.canonical_projection import project_canonical_facet_state

    project_canonical_facet_state(vault, repository)
    return ReplayResult(
        learning_object_id=learning_object_id,
        replayed_attempts=len(replayed),
        attempt_ids=[result.attempt_id for result in replayed],
    )


def rebuild_derived_state(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_ids: list[str] | None = None,
    clock: Clock | None = None,
) -> RebuildResult:
    """Replay all requested learning objects that have persisted attempts."""

    requested_ids = learning_object_ids or repository.learning_object_ids_with_attempts()
    rebuilt: list[str] = []
    replayed_attempts = 0
    for learning_object_id in requested_ids:
        if learning_object_id not in vault.learning_objects:
            continue
        result = replay_learning_object(vault, repository, learning_object_id)
        rebuilt.append(learning_object_id)
        replayed_attempts += result.replayed_attempts
    scope = "learning_object" if learning_object_ids else "all"
    marker_id = repository.record_derived_state_rebuild(
        scope=scope,
        learning_object_ids=rebuilt,
        algorithm_version=vault.config.algorithms.algorithm_version,
        rebuilt_learning_objects=len(rebuilt),
        replayed_attempts=replayed_attempts,
        clock=clock,
    )
    return RebuildResult(
        algorithm_version=vault.config.algorithms.algorithm_version,
        rebuilt_learning_objects=len(rebuilt),
        replayed_attempts=replayed_attempts,
        learning_object_ids=rebuilt,
        marker_id=marker_id,
    )

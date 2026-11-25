"""Learner controls and the shared diagnostic client contract.

"Stop diagnosing and teach me" settles committed answers and releases their
feedback, invalidates the active presentation, records a typed transition,
converts the episode to tutoring, and opens a post-intervention segment.
The client contract exposes the next observation number, assistance
restrictions, delayed-feedback message, and available learner actions.
A read-only next-item peek supports continuing an active diagnostic block.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.vault.models import LoadedVault
from learnloop.diagnosis.probe_episodes import (
    EligibleInstrument,
    eligible_instruments,
    episode_hypothesis_set,
    episode_posterior,
)
from learnloop.diagnosis.probe_blocks import (
    first_error_from_block,
    block_observation_rows,
    build_typed_transition_decision,
    settle_block_answers,
)
from learnloop.diagnosis.probe_completion import (
    set_target_decision,
    voi_probe_site_active,
)


PROBE_ASSISTANCE_RESTRICTIONS = {
    "hints_disabled": True,
    "ask_tutor_disabled": True,
    "worked_example_disabled": True,
    "answer_reveal_disabled": True,
    "feedback_deferred": True,
}


@dataclass(frozen=True)
class StoppedCheck:
    """What `Stop diagnosing and teach me` did: the typed transition decision it
    persisted, and the block's committed answers' feedback it released."""

    decision: dict[str, Any]
    released_feedback: list[dict[str, Any]]


def stop_diagnosing_and_teach(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    clock: Clock | None = None,
) -> StoppedCheck | None:
    """`Stop diagnosing and teach me`: settle the block's committed answers, end
    measurement, open a post-intervention state segment, and persist a typed
    transition decision (§12.1)."""

    episode = repository.open_probe_episode(learning_object_id)
    if episode is None:
        return None

    # The attempt pipeline deferred these answers' normalization, diagnosis and
    # feedback to a block end that the conversion below means never runs. No
    # model client, as the attempt step's block end: normalization then asks no
    # model. Before the posterior, which the block end also reads after it.
    released_feedback, _ = settle_block_answers(vault, repository, episode, ai_client=None, clock=clock)
    # One transaction from the reread to the conversion: the probe router's continuation job decides inside its own
    # transaction against the episode as it then stands, so it either sees the episode converted and records nothing,
    # or it committed first and its pin is ended here.
    with repository.atomic():
        episode = repository.probe_episode(episode.id)
        if episode is None or repository.open_probe_episode(learning_object_id) is None:
            return None
        posterior = episode_posterior(vault, repository, episode)
        active = repository.active_probe_presentation(episode.id)
        if active is not None:
            repository.end_probe_presentation(active.id, end_reason="invalidated", clock=clock)

        decision = build_typed_transition_decision(
            vault,
            repository,
            episode,
            posterior,
            first_error_step_or_claim=first_error_from_block(
                block_observation_rows(repository, episode)
            ),
        )
        repository.update_probe_episode_status(
            episode.id,
            status="converted_to_tutoring",
            completion_reason="converted_to_tutoring",
            completed_at=utc_now_iso(clock),
            clock=clock,
        )
        set_target_decision(repository, episode.id, decision, clock=clock)
        repository.open_state_segment(
            learning_object_id=learning_object_id,
            probe_episode_id=episode.id,
            reason="tutoring_transition",
            clock=clock,
        )
    return StoppedCheck(decision=decision, released_feedback=released_feedback)


def episode_contract(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
) -> dict[str, Any] | None:
    """The probe UX contract for one LO, or None when no episode is active.

    Shared by the Tauri sidecar and the Textual UI so both surfaces enforce
    the same measurement conditions (§12).
    """

    episode = repository.open_probe_episode(learning_object_id)
    if episode is None or episode.status != "in_progress":
        return None
    posterior = episode_posterior(vault, repository, episode)
    qualifying = posterior.qualifying_observations if posterior is not None else 0
    contract = {
        "episode_id": episode.id,
        "status": episode.status,
        "observation_number": qualifying + 1,
        "maximum_observations": episode.maximum_observations,
        "forced_attempt_type": "diagnostic_probe",
        "restrictions": dict(PROBE_ASSISTANCE_RESTRICTIONS),
        "capability_summary": "Checking what you already know so practice can target the right gap.",
        "feedback_note": "Feedback is delayed until this short diagnostic block completes.",
        "actions": {"stop_and_teach": True, "leave_and_resume": True},
    }
    if voi_probe_site_active(vault):
        # mvp-0.21: the episode asks while the next question is worth its
        # minutes, not up to ``maximum_observations`` (outside a calibration
        # session), so a surface must not say "of up to N".
        contract["value_stopping"] = True
    return contract


def next_probe_item(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
) -> EligibleInstrument | None:
    """The item that would be served next for this LO's open episode, or None.

    Read-only peek (§5.7 continuity) — unlike `commit_item_presentation`, this
    never writes a presentation. The Tauri UI uses it to jump straight to the
    next observation within an in-progress block instead of round-tripping
    through the general queue between every attempt.
    """

    episode = repository.open_probe_episode(learning_object_id)
    if episode is None or episode.status != "in_progress":
        return None
    hypothesis_set = episode_hypothesis_set(repository, episode)
    if hypothesis_set is None:
        return None
    posterior = episode_posterior(vault, repository, episode, hypothesis_set=hypothesis_set)
    candidates = eligible_instruments(
        vault,
        repository,
        episode,
        hypothesis_set=hypothesis_set,
        posterior=posterior.posterior if posterior is not None else None,
    )
    if not candidates:
        return None
    # §11.1 priority 1: when this LO carries an open, repair-divergent cause set,
    # serve the instrument that DISCRIMINATES the candidate causes (KM4 contrast
    # bindings) instead of the plain top-EIG pick. Gated on a cause set existing,
    # so ordinary diagnostic serving is unchanged.
    from learnloop.diagnosis.probe_targeting import (
        open_cause_sets_for_learning_object,
        select_discriminating_instrument,
    )

    cause_sets = open_cause_sets_for_learning_object(vault, repository, learning_object_id)
    if cause_sets:
        discriminating = select_discriminating_instrument(cause_sets[0], candidates)
        if discriminating is not None:
            return discriminating
    return candidates[0]


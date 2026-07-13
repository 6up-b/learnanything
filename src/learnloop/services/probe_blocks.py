"""Diagnostic block boundary semantics (spec_probe_eig_redesign.md §5.7).

During an active diagnostic block, per-attempt side effects that could leak
feedback or duplicate diagnosis are DEFERRED, not skipped: intervention
follow-up evaluation, follow-up queue insertion, and misconception
normalization do not run per attempt (services/followups.py defers them for
in-block diagnostic attempts). At block end, one hook runs in order:

1. release withheld feedback;
2. run misconception normalization over the block's attempts;
3. evaluate the open-set trigger (§6.3);
4. evaluate the completion policy (§11);
5. route to the typed transition (§12.1), the next block, or ordinary practice.

Every modality funnels here: dialogue blocks end through
``end_dialogue_block`` (probe_dialogue.py), sequential and precommitted
microprobe blocks end from ``record_episode_evidence`` once the block's
observation target is reached (probe_episodes.py).
"""

from __future__ import annotations

from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import ProbeEpisodeRecord, Repository
from learnloop.services.probe_episodes import (
    EpisodePosterior,
    _evaluate_completion,
    _set_target_decision,
    episode_posterior,
    persist_episode_beliefs,
)
from learnloop.services.probe_hypotheses import H_OTHER
from learnloop.vault.models import LoadedVault

# Deduplicated open-set generation-need capability (§6.3): the review path
# picks it up as a misconception generate-retrieve-rerank / review proposal
# target rather than a missing instrument family.
OPEN_SET_REVIEW_CAPABILITY = "open_set_misconception_review"


def block_observation_rows(repository: Repository, episode: ProbeEpisodeRecord) -> list[dict[str, Any]]:
    """The active block's observation rows: observations whose committed
    presentation belongs to the episode's active state segment."""

    segment_id = episode.active_state_segment_id
    if segment_id is None:
        return []
    return [
        row
        for row in repository.probe_observations_for_episode(episode.id)
        if row.get("state_segment_id") == segment_id
    ]


def block_complete(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    probe_presentation_id: str,
) -> bool:
    """Whether recording this presentation's observation closed the block.

    Dialogue blocks never auto-close here — their explicit endpoint
    (``end_dialogue_block``) owns the boundary. A precommitted joint block
    closes when its committed size is consumed; sequential probes close after
    the configured default block size. Exhausting the episode's qualifying
    budget always closes the block so the completion policy can run.
    """

    presentation = repository.probe_presentation(probe_presentation_id)
    components = dict(presentation.selection_components or {}) if presentation is not None else {}
    if components.get("dialogue_block_id"):
        return False

    rows = repository.probe_observations_for_episode(episode.id)
    qualifying = sum(1 for row in rows if row["observation"].eligible_for_completion)
    if qualifying >= episode.maximum_observations:
        return True

    segment_rows = [
        row for row in rows if row.get("state_segment_id") == episode.active_state_segment_id
    ]
    if components.get("joint_block"):
        target = int(components.get("block_size") or 0)
        if target <= 0:
            target = vault.config.probe.block.default_block_observations
        return len(segment_rows) >= target
    target = min(
        vault.config.probe.block.default_block_observations,
        episode.maximum_observations,
    )
    return len(segment_rows) >= target


def evaluate_open_set_trigger(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    posterior: EpisodePosterior,
    *,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """§6.3: when ``other_or_unknown`` becomes competitive, trigger the
    misconception review path — evaluated at block end, never per attempt.

    The episode's hypothesis set stays locked (§6.3); the trigger records one
    deduplicated review need (keyed by episode + open-set capability) that the
    diagnostic-proposal pipeline resolves into a generate-retrieve-rerank
    misconception review or an authoring proposal. Firing is idempotent per
    episode by the need's dedup key.
    """

    threshold = vault.config.probe.episode.open_set_trigger_threshold
    if threshold <= 0:
        return None
    open_set_mass = posterior.posterior.get(H_OTHER, 0.0)
    top_label, top_probability = posterior.top
    competitive = open_set_mass >= threshold or (
        top_label == H_OTHER and open_set_mass > 0.0
    )
    if not competitive:
        return None
    need_id = repository.upsert_probe_generation_need(
        probe_episode_id=episode.id,
        learning_object_id=episode.learning_object_id,
        target_key=H_OTHER,
        missing_capability=OPEN_SET_REVIEW_CAPABILITY,
        clock=clock,
    )
    return {
        "fired": True,
        "open_set_mass": open_set_mass,
        "threshold": threshold,
        "top_label": top_label,
        "top_probability": top_probability,
        "action": "misconception_review_need",
        "need_id": need_id,
    }


# §12.1 stable tutor-move taxonomy, keyed by the card's instructional action
# for the diagnosed state. Falls back to the diagnosed-label mapping below.
_TUTOR_MOVE_BY_ACTION: dict[str, str] = {
    "contrastive_repair": "contrast_cases",
    "misconception_repair": "counterexample",
    "foundational_instruction": "explanation",
    "mechanism_instruction": "explanation",
    "varied_surface_practice": "transfer_question",
    "shifted_surface_practice": "transfer_question",
    "transfer_practice": "transfer_question",
    "procedure_selection_practice": "state_subgoal",
    "diagnostic_followup": "elicit_reasoning",
}

_TUTOR_MOVE_BY_LABEL: dict[str, str] = {
    "unfamiliar": "explanation",
    "surface_only": "transfer_question",
    "recall_without_mechanism": "explanation",
    "procedure_without_selection": "state_subgoal",
    "schema_without_transfer": "transfer_question",
    "confuses_with_neighbor": "contrast_cases",
}


def _derive_tutor_move(
    top_label: str,
    top_probability: float,
    first_error: str | None,
    instructional_action: str | None,
) -> str:
    # Low diagnostic confidence: gather the learner's reasoning before
    # committing to an instructional move.
    if top_probability < 0.5:
        return "elicit_reasoning"
    # A concrete first divergent step is the highest-precision target.
    if first_error:
        return "localize_error"
    if instructional_action in _TUTOR_MOVE_BY_ACTION:
        return _TUTOR_MOVE_BY_ACTION[instructional_action]
    if top_label.startswith(("misconception:", "confuses_with")):
        return "counterexample"
    return _TUTOR_MOVE_BY_LABEL.get(top_label, "localize_error")


def build_typed_transition_decision(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    posterior: EpisodePosterior | None,
    *,
    first_error_step_or_claim: str | None = None,
) -> dict[str, Any]:
    """The §12.1 typed transition decision, persisted before tutor prose."""

    top_label, top_probability = posterior.top if posterior is not None else ("", 0.0)
    misconception_id = None
    if top_label.startswith("misconception:"):
        misconception_id = top_label.split(":", 1)[1]
    instructional_action = None
    for row in reversed(repository.probe_observations_for_episode(episode.id)):
        snapshot = row.get("instrument_card_snapshot")
        if isinstance(snapshot, dict):
            actions = snapshot.get("instructional_actions") or {}
            if top_label in actions:
                instructional_action = actions[top_label]
                break
    tutor_move = _derive_tutor_move(
        top_label, top_probability, first_error_step_or_claim, instructional_action
    )
    instructional_intent = (
        "repair" if top_label.startswith(("misconception:", "confuses_with:")) else "instruct"
    )
    # Scaffolding scales with remaining uncertainty and instructional intent:
    # instruction for an unfamiliar learner scaffolds high; repair of a
    # confidently diagnosed belief scaffolds mid so the learner does the work.
    base_scaffold = 0.7 if instructional_intent == "instruct" else 0.5
    scaffold_level = round(min(0.9, max(0.2, base_scaffold + (0.5 - top_probability) * 0.4)), 2)
    # Eliciting moves must not reveal answers; explanatory moves may.
    answer_reveal_budget = (
        0
        if tutor_move in ("elicit_reasoning", "transfer_question")
        else 2 if tutor_move in ("explanation", "worked_example") else 1
    )
    learning_object = vault.learning_objects.get(episode.learning_object_id)
    source_ref_ids = (
        [ref.ref_id for ref in learning_object.provenance.source_refs]
        if learning_object is not None
        else []
    )
    return {
        "target_facets": list(episode.required_facets),
        "diagnosed_gap": top_label or None,
        "first_error_step_or_claim": first_error_step_or_claim,
        "misconception_id": misconception_id,
        "diagnostic_confidence": top_probability,
        "tutor_move": tutor_move,
        "instructional_intent": instructional_intent,
        "instructional_action": instructional_action,
        "scaffold_level": scaffold_level,
        "answer_reveal_budget": answer_reveal_budget,
        "expected_learner_action": "attempt_targeted_practice",
        "source_ref_ids": source_ref_ids,
        "posterior": posterior.posterior if posterior is not None else {},
    }


def _first_error_from_block(rows: list[dict[str, Any]]) -> str | None:
    """First divergent step/claim from the block's structured traces (§8.2)."""

    for row in rows:
        features = row["observation"].features or {}
        trace = features.get("structured_trace") or {}
        first_invalid = trace.get("first_invalid_id")
        if first_invalid:
            return str(first_invalid)
    return None


def end_diagnostic_block(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord | str,
    *,
    ai_client: object | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """The §5.7 block-end hook. Runs the ordered sequence and returns what the
    client needs to reveal feedback and route the learner."""

    from learnloop.services.misconceptions import normalize_and_resolve_attempt

    if isinstance(episode, str):
        fetched = repository.probe_episode(episode)
        if fetched is None:
            return {}
        episode = fetched
    if episode.status != "in_progress":
        return {"episode_id": episode.id, "status": episode.status, "route": None}

    rows = block_observation_rows(repository, episode)

    # 1. Release withheld feedback: feedback is persisted at grading time and
    # withheld by the client contract (§5.6); the hook returns it for reveal.
    released_feedback: list[dict[str, Any]] = []
    for row in rows:
        attempt_id = str(row["attempt_id"])
        metadata = repository.fetch_attempt_feedback_metadata(attempt_id) or {}
        released_feedback.append(
            {
                "attempt_id": attempt_id,
                "practice_item_id": row.get("practice_item_id"),
                "rubric_score": row.get("rubric_score"),
                "feedback_md": metadata.get("feedback_md"),
                "fatal_errors": metadata.get("fatal_errors") or [],
            }
        )

    # 2. Misconception normalization over the block's attempts — deferred from
    # the per-attempt path (§5.7), idempotent per error event.
    normalized_misconception_ids: list[str] = []
    for row in rows:
        normalized_misconception_ids.extend(
            normalize_and_resolve_attempt(
                vault,
                repository,
                attempt_id=str(row["attempt_id"]),
                learning_object_id=episode.learning_object_id,
                ai_client=ai_client,
                clock=clock,
            )
        )

    # 3+4. Open-set trigger and completion policy run on the
    # post-normalization posterior.
    posterior = episode_posterior(vault, repository, episode)
    open_set = None
    completion_reason = None
    if posterior is not None:
        persist_episode_beliefs(vault, repository, episode, posterior, clock=clock)
        open_set = evaluate_open_set_trigger(vault, repository, episode, posterior, clock=clock)
        completion_reason = _evaluate_completion(vault, repository, episode, posterior, clock=clock)

    refreshed = repository.probe_episode(episode.id) or episode
    first_error = _first_error_from_block(rows)

    # 5. Route: typed transition, the next block, or ordinary practice.
    route = "ordinary_practice"
    decision: dict[str, Any] | None = None
    if refreshed.status == "in_progress":
        route = "next_block"
    elif refreshed.status == "complete":
        top_label, top_probability = posterior.top if posterior is not None else ("", 0.0)
        diagnosed_gap = bool(top_label) and top_label not in ("robust_initial_grasp",)
        if diagnosed_gap:
            route = "tutoring"
            decision = build_typed_transition_decision(
                vault, repository, refreshed, posterior, first_error_step_or_claim=first_error
            )
            _set_target_decision(repository, refreshed.id, decision, clock=clock)

    # Segment boundary (§5.1): revealing feedback is an intervention boundary;
    # a continuing (or parked) episode measures its next block in a fresh
    # segment. Any uncommitted presentation from the closing segment is stale
    # (§5.1 `invalidated`) — it was selected against a pre-reveal learner state.
    if refreshed.status in ("in_progress", "pending_items"):
        active = repository.active_probe_presentation(episode.id)
        if active is not None and active.status in ("selected", "served"):
            repository.end_probe_presentation(active.id, end_reason="invalidated", clock=clock)
        repository.open_state_segment(
            learning_object_id=episode.learning_object_id,
            probe_episode_id=episode.id,
            reason="feedback_reveal" if released_feedback else "block_end",
            clock=clock,
        )
    elif route == "tutoring":
        repository.open_state_segment(
            learning_object_id=episode.learning_object_id,
            probe_episode_id=episode.id,
            reason="tutoring_transition",
            clock=clock,
        )

    return {
        "episode_id": episode.id,
        "status": refreshed.status,
        "released_feedback": released_feedback,
        "normalized_misconception_ids": normalized_misconception_ids,
        "open_set": open_set,
        "completion_reason": completion_reason or refreshed.completion_reason,
        "first_error_step_or_claim": first_error,
        "route": route,
        "decision": decision,
    }

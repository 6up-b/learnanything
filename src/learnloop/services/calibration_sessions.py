"""Learner-initiated calibration sessions (spec_probe_eig_redesign.md §5.9).

A calibration session is an explicit wrapper (goal wizard, command palette)
that batches multiple diagnostic-episode blocks across a goal's facet scope in
one sitting, ordered adaptively by cross-LO predictive information rate, with
its own time budget, progress display, and stop control. It is belief-feeding
and adaptive — the opposite of a held-out exam — and reuses the same episode,
presentation, and observation machinery and integrity rules; it lifts only the
per-session qualifying-observation cap within its declared budget.
"""

from __future__ import annotations

from typing import Any

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.repositories import ProbeCalibrationSessionRecord, Repository
from learnloop.services.goal_projection import resolve_goal_scope
from learnloop.services.probe_episodes import eligible_instruments, enter_episode, episode_posterior
from learnloop.services.probe_instance_generation import generate_instances_for_episode
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault


class CalibrationSessionError(ValueError):
    pass


def graph_propagated_prior(
    vault: LoadedVault, repository: Repository, learning_object_id: str
) -> float | None:
    """Conservative graph-propagated mastery prior for one LO (§6.4).

    Relation- and direction-specific: prerequisite evidence moves the prior
    weakly (weight 1.0 within one hop), ``part_of``/``related`` more weakly
    (0.5), and ``confusable_with`` never propagates mastery as equivalence.
    Only neighbors with direct behavioral evidence contribute. Returns None
    when the graph offers no evidence-bearing neighbor.
    """

    from learnloop.services.mastery import display_mastery

    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None or not learning_object.concept:
        return None
    concept = learning_object.concept
    neighbor_weights: dict[str, float] = {}
    for edge in vault.edges:
        if edge.relation_type == "confusable_with":
            continue  # §6.4: confusion is not equivalence
        weight = 1.0 if edge.relation_type == "prerequisite" else 0.5
        if edge.source == concept and edge.target != concept:
            neighbor_weights[edge.target] = max(neighbor_weights.get(edge.target, 0.0), weight)
        elif edge.target == concept and edge.source != concept:
            neighbor_weights[edge.source] = max(neighbor_weights.get(edge.source, 0.0), weight)
    if not neighbor_weights:
        return None
    weighted_sum = 0.0
    total_weight = 0.0
    for other_id, other in vault.learning_objects.items():
        if other_id == learning_object_id or other.concept not in neighbor_weights:
            continue
        mastery = repository.mastery_state(other_id)
        if mastery is None or mastery.evidence_count <= 0:
            continue
        weight = neighbor_weights[other.concept]
        weighted_sum += weight * display_mastery(mastery).mastery_mean
        total_weight += weight
    if total_weight <= 0:
        return None
    return weighted_sum / total_weight


def episode_priority_disagreement(
    vault: LoadedVault, repository: Repository, learning_object_id: str
) -> float:
    """§5.9/§6.4 planner priority signal: disagreement among the
    graph-propagated prior, the learner's covering claim, and observed
    evidence — the spread of whichever of the three signals exist, in [0, 1].
    High-disagreement, high-consequence episodes run first.
    """

    from learnloop.services.mastery import covering_learner_claim, display_mastery

    signals: list[float] = []
    graph_prior = graph_propagated_prior(vault, repository, learning_object_id)
    if graph_prior is not None:
        signals.append(graph_prior)
    claim = covering_learner_claim(vault, repository, learning_object_id)
    if claim is not None and claim.get("claimed_level") is not None:
        signals.append(max(0.0, min(1.0, float(claim["claimed_level"]))))
    mastery = repository.mastery_state(learning_object_id)
    if mastery is not None and mastery.evidence_count > 0:
        signals.append(display_mastery(mastery).mastery_mean)
    if len(signals) < 2:
        return 0.0
    return max(signals) - min(signals)


def routine_planner_shadow(
    vault: LoadedVault,
    repository: Repository,
    episode_id: str,
) -> dict[str, Any] | None:
    """§5.9 routine-session diagnostic planner, run in SHADOW mode (§13.3).

    Ranks every open in-progress episode by its best instrument's information
    rate, plain and disagreement-boosted, and reports where the episode being
    served ranks under each. Log-only: promoting the boosted ordering to a
    live policy requires held-out predictive gains first, and sim sweeps found
    scheduler ranking knobs decision-inert — this log is the evidence either
    way. Returns None when fewer than two episodes are rankable.
    """

    disagreement_weight = vault.config.probe.calibration.disagreement_weight
    plain: list[tuple[float, str]] = []
    boosted: list[tuple[float, str]] = []
    target_disagreement = 0.0
    for lo_id, episode in sorted(repository.open_probe_episodes().items()):
        if episode.status != "in_progress":
            continue
        entries = eligible_instruments(vault, repository, episode)
        if not entries:
            continue
        best = entries[0]
        rate = (
            best.predictive_information_rate
            if best.selection_objective == "predictive_eig"
            else best.expected_information_gain
        )
        disagreement = episode_priority_disagreement(vault, repository, lo_id)
        if episode.id == episode_id:
            target_disagreement = disagreement
        plain.append((-rate, episode.id))
        boosted.append((-rate * (1.0 + disagreement_weight * disagreement), episode.id))
    if len(plain) < 2 or all(episode_id != entry[1] for entry in plain):
        return None
    plain.sort()
    boosted.sort()
    return {
        "episode_rank_plain": next(i for i, entry in enumerate(plain, 1) if entry[1] == episode_id),
        "episode_rank_boosted": next(i for i, entry in enumerate(boosted, 1) if entry[1] == episode_id),
        "disagreement": round(target_disagreement, 4),
        "disagreement_weight": disagreement_weight,
        "open_in_progress_episodes": len(plain),
    }


def start_calibration_session(
    vault: LoadedVault,
    repository: Repository,
    *,
    session_id: str,
    goal_id: str | None = None,
    learning_object_ids: list[str] | None = None,
    time_budget_minutes: int | None = None,
    generate_missing: bool = True,
    clock: Clock | None = None,
    ai_client: object | None = None,
) -> dict[str, Any]:
    """Open a calibration session over a goal scope or an explicit LO list.

    Ensures an episode per in-scope LO, optionally resolves `pending_items`
    episodes through parameterized generation (§10), orders episodes by the
    best available cross-LO predictive information rate, and persists the plan.
    """

    if repository.active_probe_calibration_session(session_id) is not None:
        raise CalibrationSessionError(f"session {session_id} already has an active calibration session")

    calibration_config = vault.config.probe.calibration
    budget = time_budget_minutes or calibration_config.default_time_budget_minutes

    scope_los: list[str]
    if learning_object_ids:
        scope_los = [lo_id for lo_id in learning_object_ids if lo_id in vault.learning_objects]
    elif goal_id is not None:
        goal = next((entry for entry in vault.goals if entry.id == goal_id), None)
        if goal is None:
            raise CalibrationSessionError(f"unknown goal {goal_id}")
        scope_los = sorted(resolve_goal_scope(vault, goal, repository))
    else:
        scope_los = sorted(
            episode.learning_object_id for episode in repository.open_probe_episodes().values()
        )
    if not scope_los:
        raise CalibrationSessionError("calibration session scope resolved to zero Learning Objects")

    working_vault = vault
    episode_ids: dict[str, str] = {}
    for lo_id in scope_los:
        episode = repository.open_probe_episode(lo_id)
        if episode is None:
            trigger = "goal_diagnostic" if goal_id is not None else "manual"
            episode = enter_episode(
                working_vault, repository, lo_id, trigger=trigger, clock=clock, ai_client=ai_client
            )
        if episode.status == "pending_items" and generate_missing:
            summary = generate_instances_for_episode(
                repository, working_vault, episode.id, clock=clock, ai_client=ai_client
            )
            if summary.generated:
                working_vault = load_vault(working_vault.root)
                working_vault.config = vault.config
                refreshed = repository.probe_episode(episode.id)
                if refreshed is not None:
                    episode = refreshed
        episode_ids[lo_id] = episode.id

    # Cross-LO adaptive ordering (§5.9): the episode whose best instrument has
    # the highest predictive information rate runs first, scaled up by the
    # §6.4 disagreement among graph prior, learner claims, and observed
    # evidence — high-disagreement, high-consequence episodes run first.
    # Parked episodes rank last.
    disagreement_weight = calibration_config.disagreement_weight
    ranked: list[tuple[float, str]] = []
    for lo_id, episode_id in episode_ids.items():
        episode = repository.probe_episode(episode_id)
        rate = 0.0
        if episode is not None and episode.status == "in_progress":
            entries = eligible_instruments(working_vault, repository, episode)
            if entries:
                best = entries[0]
                rate = (
                    best.predictive_information_rate
                    if best.selection_objective == "predictive_eig"
                    else best.expected_information_gain
                )
        if rate > 0 and disagreement_weight > 0:
            disagreement = episode_priority_disagreement(working_vault, repository, lo_id)
            rate *= 1.0 + disagreement_weight * disagreement
        ranked.append((-rate, episode_id))
    ranked.sort()
    planned = [episode_id for _negative_rate, episode_id in ranked][
        : calibration_config.max_planned_episodes
    ]

    calibration_id = repository.insert_probe_calibration_session(
        session_id=session_id,
        goal_id=goal_id,
        learning_object_ids=list(scope_los),
        planned_episode_ids=planned,
        time_budget_minutes=budget,
        clock=clock,
    )
    return calibration_session_progress(working_vault, repository, calibration_id, clock=clock)


def calibration_session_progress(
    vault: LoadedVault,
    repository: Repository,
    calibration_id: str,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Progress payload for the calibration UI: per-episode status, blocks
    completed, elapsed versus budget, and the next target item."""

    record = repository.probe_calibration_session(calibration_id)
    if record is None:
        raise CalibrationSessionError(f"unknown calibration session {calibration_id}")
    record = _expire_if_over_budget(repository, record, clock=clock)

    episodes: list[dict[str, Any]] = []
    completed = 0
    next_target: dict[str, Any] | None = None
    for episode_id in record.planned_episode_ids:
        episode = repository.probe_episode(episode_id)
        if episode is None:
            continue
        qualifying = sum(
            1
            for row in repository.probe_observations_for_episode(episode_id)
            if row["observation"].eligible_for_completion
        )
        done = episode.status in ("complete", "converted_to_tutoring", "abandoned")
        if done:
            completed += 1
        entry = {
            "episode_id": episode_id,
            "learning_object_id": episode.learning_object_id,
            "status": episode.status,
            "qualifying_observations": qualifying,
            "maximum_observations": episode.maximum_observations,
        }
        episodes.append(entry)
        if next_target is None and record.status == "active" and episode.status == "in_progress":
            entries = eligible_instruments(vault, repository, episode)
            if entries:
                posterior = episode_posterior(vault, repository, episode)
                next_target = {
                    "episode_id": episode_id,
                    "learning_object_id": episode.learning_object_id,
                    "practice_item_id": entries[0].item.id,
                    "selection_objective": entries[0].selection_objective,
                    "entropy": posterior.entropy if posterior is not None else None,
                }

    if (
        record.status == "active"
        and record.planned_episode_ids
        and completed == len(record.planned_episode_ids)
    ):
        repository.end_probe_calibration_session(record.id, status="completed", clock=clock)
        refreshed = repository.probe_calibration_session(record.id)
        record = refreshed if refreshed is not None else record

    elapsed_minutes = _elapsed_minutes(record, clock=clock)
    return {
        "calibration_session_id": record.id,
        "session_id": record.session_id,
        "goal_id": record.goal_id,
        "status": record.status,
        "time_budget_minutes": record.time_budget_minutes,
        "elapsed_minutes": elapsed_minutes,
        "remaining_minutes": max(record.time_budget_minutes - elapsed_minutes, 0.0),
        "blocks_completed": completed,
        "blocks_planned": len(record.planned_episode_ids),
        "episodes": episodes,
        "next_target": next_target,
    }


def stop_calibration_session(
    repository: Repository, calibration_id: str, *, clock: Clock | None = None
) -> None:
    repository.end_probe_calibration_session(calibration_id, status="stopped", clock=clock)


def calibration_cap_lifted(
    repository: Repository, session_id: str | None, *, clock: Clock | None = None
) -> bool:
    """Whether the per-session qualifying-observation cap is lifted for this
    client session (§5.9) — true only inside an active, in-budget calibration
    session. An over-budget session expires here as a side effect."""

    if not session_id:
        return False
    record = repository.active_probe_calibration_session(session_id)
    if record is None:
        return False
    record = _expire_if_over_budget(repository, record, clock=clock)
    return record.status == "active"


def _elapsed_minutes(record: ProbeCalibrationSessionRecord, *, clock: Clock | None) -> float:
    started = parse_utc(record.started_at)
    now = parse_utc(utc_now_iso(clock))
    if started is None or now is None:
        return 0.0
    return max((now - started).total_seconds() / 60.0, 0.0)


def _expire_if_over_budget(
    repository: Repository,
    record: ProbeCalibrationSessionRecord,
    *,
    clock: Clock | None,
) -> ProbeCalibrationSessionRecord:
    if record.status != "active":
        return record
    if _elapsed_minutes(record, clock=clock) <= record.time_budget_minutes:
        return record
    repository.end_probe_calibration_session(record.id, status="expired", clock=clock)
    refreshed = repository.probe_calibration_session(record.id)
    return refreshed if refreshed is not None else record

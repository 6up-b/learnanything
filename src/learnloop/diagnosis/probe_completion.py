"""Completion policy for diagnostic episodes: decide when measurement ends.

Rules in order: observation_budget_exhausted; action_equivalent (unstable);
couldnt_reliably_distinguish (robust abstention); value_of_information_stop
(unstable); decision_stable; fast_path_strong_claim; action_equivalent
(stable, breadth-short); value_of_information_stop (stable, breadth-short).
Value decides while its probe site is active outside calibration sessions;
the robust gate decides otherwise or when robust_gate_with_value is enabled.
A value stop records the robust verdict as a counterfactual when applicable.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import ProbeEpisodeRecord, Repository
from learnloop.diagnosis.probe_episodes import (
    EligibleInstrument,
    EpisodePosterior,
    _record_generation_need,
    eligible_instruments,
)
from learnloop.diagnosis.probe_hypotheses import strong_prior_claim
from learnloop.substrate.canonical_projection import surface_group_id
from learnloop.vault.models import LoadedVault


def persist_episode_beliefs(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    posterior: EpisodePosterior,
    *,
    clock: Clock | None = None,
) -> None:
    """Persist registry-misconception marginals to `learner_state_beliefs`."""

    now = utc_now_iso(clock)
    learning_object = vault.learning_objects.get(episode.learning_object_id)
    subject = learning_object.subjects[0] if learning_object is not None and learning_object.subjects else None
    algorithm_version = vault.config.algorithms.algorithm_version
    for hypothesis in posterior.hypothesis_set.hypotheses:
        scope_id = hypothesis.channel_key
        if scope_id is None:
            continue
        probability = posterior.posterior.get(hypothesis.label, 0.0)
        prior_probability = posterior.prior.get(hypothesis.label, 0.0)
        repository.upsert_state_belief(
            scope_type="misconception",
            scope_id=scope_id,
            belief_key=episode.learning_object_id,
            mean=probability,
            variance=max(probability * (1.0 - probability), 0.0),
            evidence_count=posterior.total_observations,
            subject=subject,
            last_surprise=probability - prior_probability,
            last_evidence_at=now,
            algorithm_version=algorithm_version,
            clock=clock,
        )


def evaluate_completion(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    posterior: EpisodePosterior,
    *,
    clock: Clock | None = None,
) -> str | None:
    if episode.status != "in_progress":
        return None
    episode_config = vault.config.probe.episode
    rows = repository.probe_observations_for_episode(episode.id)
    qualifying = [row for row in rows if row["observation"].eligible_for_completion]

    # mvp-0.21 (voi_stopping): the episode's own count is lifted with the
    # session cap (reader spec §18, §20.7); while value decides, an episode
    # keeps asking past it and ends on its value stop instead.
    # observation_budget_exhausted: the episode count cap still binds.
    if len(qualifying) >= episode.maximum_observations and episode_maximum_binds(
        vault, repository, qualifying
    ):
        return _complete(repository, episode, "observation_budget_exhausted", posterior=posterior, clock=clock)

    # Decision-equivalence early stop (evsi.shared_optimal_action semantics on
    # the episode posterior): once every plausible hypothesis routes to the
    # same first intervention, remaining posterior spread has no action value.
    # One qualifying observation suffices — a routing conclusion, not a
    # demonstration claim, so the breadth contract does not apply. Checked
    # only where the episode would otherwise CONTINUE: a posterior that also
    # reaches full decision stability with breadth keeps the stronger
    # 'decision_stable' outcome.
    def _action_equivalent() -> bool:
        return (
            episode_config.action_equivalence_enabled
            and bool(qualifying)
            and _plausible_actions_agree(repository, posterior, episode_config)
        )

    top_label, top_probability = posterior.top
    sorted_probabilities = sorted(posterior.posterior.values(), reverse=True)
    second_probability = sorted_probabilities[1] if len(sorted_probabilities) > 1 else 0.0
    decision_stable = (
        top_probability >= episode_config.posterior_stop_threshold
        and (top_probability <= 0 or second_probability / top_probability <= episode_config.ambiguity_threshold)
    )
    if not decision_stable:
        # mvp-0.8 robust cutover (§4.2/§3.2): before parking on an unstable
        # posterior, ask the robust selector whether the remaining instruments can
        # reliably distinguish the hypotheses on the episode-pinned channel. When
        # the winner is fragile (10th-pct advantage <= 0 or the <90% agreement gate
        # fails) the episode completes with the explicit abstention outcome instead
        # of grinding through non-discriminating instruments (U-021); with the
        # robust gate fixes only where the stop rule also says nothing left pays
        # (robust_gate_completion).
        # An unstable posterior whose plausible hypotheses all imply the same
        # repair needs no further probing — stop before spending instruments.
        # action_equivalent: an unstable posterior already routes to one repair.
        if _action_equivalent():
            return _complete(repository, episode, "action_equivalent", posterior=posterior, clock=clock)
        # mvp-0.21 (the multi-family EVSI study's rank 1,
        # voi_stopping.robust_gate_with_value): while value decides the
        # episode the gate no longer ends it; the value stop below records the
        # gate's verdict as a counterfactual. Where value does not decide (the
        # site off, below the successor, a calibration session) or with the
        # switch on, the gate serves exactly as before.
        gate_decides = robust_gate_applies(vault, repository, qualifying)
        if gate_decides:
            abstain_reason = _robust_completion_override(vault, repository, episode, posterior)
            # couldnt_reliably_distinguish: the deciding robust gate abstains.
            if abstain_reason is not None:
                return _complete(repository, episode, abstain_reason, posterior=posterior, clock=clock)
        # §10: an unstable episode with no unconsumed instrument left (§5.4
        # forbids surface repeats) parks in pending_items with one deduplicated
        # generation need — never blocking ordinary practice on the LO.
        # `no_suitable_candidate` completion is reserved for generation being
        # declined or failing.
        remaining = (
            eligible_instruments(vault, repository, episode, posterior=posterior.posterior)
            if qualifying
            else []
        )
        if qualifying and not remaining:
            repository.update_probe_episode_status(episode.id, status="pending_items", clock=clock)
            _record_generation_need(vault, repository, episode, posterior.hypothesis_set, clock=clock)
            return None
        # mvp-0.21: the episode keeps asking only while the next observation's
        # value pays for its minutes.
        value_stop = _value_of_information_stop(
            vault,
            repository,
            episode,
            posterior,
            qualifying,
            remaining,
            gate_counterfactual=(
                None
                if gate_decides
                else (
                    lambda: _robust_completion_override(
                        vault, repository, episode, posterior, record_forecast=False
                    )
                )
            ),
        )
        # value_of_information_stop: another observation no longer pays while unstable.
        if value_stop is not None:
            return _complete_on_value_stop(vault, repository, episode, posterior, value_stop, clock=clock)
        return None

    # §7.7: dialogue microprobe turns within one block are correlated
    # observations of one task — they satisfy independence and surface
    # diversity as ONE unit, however many turns the block contained.
    units: dict[str, str] = {}
    for row in qualifying:
        block_id = (row.get("selection_components") or {}).get("dialogue_block_id")
        if block_id:
            units[f"block:{block_id}"] = f"block:{block_id}"
        else:
            units[f"row:{row['attempt_id']}"] = _surface_key(vault, str(row["practice_item_id"]))
    surfaces = set(units.values())
    required = set(episode.required_facets)
    covered = {str(facet) for row in qualifying for facet in (row.get("target_facets") or [])}
    breadth_ok = (
        len(units) >= episode.minimum_independent_observations
        and len(surfaces) >= min(2, episode.minimum_independent_observations)
        and required <= covered
    )
    # decision_stable: the stable posterior also meets the breadth contract.
    if breadth_ok:
        return _complete(repository, episode, "decision_stable", posterior=posterior, clock=clock)

    # §11 fast path: an explicit strong prior claim plus one highly
    # discriminating cross-facet instrument may complete early. This replaces
    # the legacy claim_skip_threshold (Checkpoint 0.4 mapping).
    # fast_path_strong_claim: a strong prior has cross-facet corroboration.
    if (
        len(qualifying) >= 1
        and strong_prior_claim(vault, repository, episode.learning_object_id)
        and any(len(row.get("target_facets") or []) >= 2 for row in qualifying)
    ):
        return _complete(repository, episode, "fast_path_strong_claim", posterior=posterior, clock=clock)
    # Stable but breadth-short: if the plausible hypotheses already agree on
    # the repair, the missing breadth buys nothing for routing — stop.
    # action_equivalent: the stable posterior needs no more breadth for routing.
    if _action_equivalent():
        return _complete(repository, episode, "action_equivalent", posterior=posterior, clock=clock)
    # mvp-0.21: breadth is asked for only while its value pays for its minutes.
    value_stop = _value_of_information_stop(
        vault,
        repository,
        episode,
        posterior,
        qualifying,
        eligible_instruments(vault, repository, episode, posterior=posterior.posterior)
        if qualifying and voi_probe_site_active(vault)
        else [],
    )
    # value_of_information_stop: more breadth no longer pays for its minutes.
    if value_stop is not None:
        return _complete_on_value_stop(vault, repository, episode, posterior, value_stop, clock=clock)
    return None


def voi_probe_site_active(vault: LoadedVault) -> bool:
    from learnloop.diagnosis.voi_stopping import SITE_PROBE_EPISODE, voi_stopping_active

    return voi_stopping_active(vault.config, SITE_PROBE_EPISODE)


def value_decides_episode(
    vault: LoadedVault, repository: Repository, qualifying: Sequence[Mapping[str, Any]]
) -> bool:
    """Does value of information decide this episode's next observation?

    Yes at mvp-0.21 with the probe-episode site on, unless the latest
    observation was made in a calibration session (the learner's opt-in lifts
    the value rule, as it lifted the session cap)."""

    if not voi_probe_site_active(vault):
        return False
    session_id = _latest_observation_session(repository, qualifying)
    if session_id is not None:
        from learnloop.diagnosis.calibration_sessions import calibration_cap_lifted

        if calibration_cap_lifted(repository, str(session_id)):
            return False
    return True


def robust_gate_applies(
    vault: LoadedVault, repository: Repository, qualifying: Sequence[Mapping[str, Any]]
) -> bool:
    """May the mvp-0.8 robust completion gate end this unstable episode?

    Always where value does not decide (the kill-switch path, below the
    successor, a calibration session: today's gate exactly). Where value
    decides, only with ``voi_stopping.robust_gate_with_value`` on (the
    multi-family EVSI study's rank 1: off by default, so a value-decided
    episode ends on its value stop and that stop records the gate's verdict).
    """

    if not value_decides_episode(vault, repository, qualifying):
        return True
    from learnloop.diagnosis.voi_stopping import VoiSettings

    return VoiSettings.from_config(vault.config).robust_gate_with_value


def _latest_observation_session(repository: Repository, qualifying: Sequence[Mapping[str, Any]]) -> str | None:
    """The session of the episode's latest qualifying observation (oldest first)."""

    if not qualifying:
        return None
    latest = qualifying[-1]
    attempt = repository.fetch_practice_attempt(str(latest.get("attempt_id"))) if latest.get("attempt_id") else None
    session_id = attempt.get("session_id") if attempt else None
    return str(session_id) if session_id is not None else None


def episode_maximum_binds(
    vault: LoadedVault, repository: Repository, qualifying: Sequence[Mapping[str, Any]]
) -> bool:
    """Does ``probe.episode.maximum_observations`` (stamped on the episode at
    entry) end the episode by count?

    Yes below mvp-0.21 or with the probe-episode site switched off (the
    kill-switch path, exactly), and in a calibration session (the learner's
    opt-in lifts the value rule as it lifted the session cap, so the count is
    what ends that measurement). Otherwise value decides: the episode asks
    while its next observation pays for its minutes, and the count is only the
    receipt's counterfactual (``voi_stopping.EPISODE_MAXIMUM_CAP``).
    """

    return not value_decides_episode(vault, repository, qualifying)


def _plausible_actions_agree(
    repository: Repository,
    posterior: EpisodePosterior,
    episode_config,
) -> bool:
    """True when every plausible hypothesis routes to one first intervention.

    Reads the authored failure_triage_routes rows through the hypothesis-label
    -> triage-reason bridge. Fails closed (False) when routes are missing or a
    plausible hypothesis maps to a reason without an active route: an unroutable
    hypothesis means measurement can still change the action.
    """

    from learnloop.diagnosis.probe_hypotheses import triage_reason_for_label

    threshold = float(episode_config.action_equivalence_plausible_threshold)
    plausible = [
        label
        for label, probability in posterior.posterior.items()
        if float(probability) >= threshold
    ]
    # A singleton is posterior concentration, not action equivalence.  Let the
    # ordinary posterior-stop threshold decide whether that concentration is
    # strong enough; otherwise this path becomes a second, weaker confidence
    # stop whenever every runner-up falls just below the plausibility cutoff.
    if len(plausible) < 2:
        return False
    interventions: set[str] = set()
    for label in plausible:
        reason = triage_reason_for_label(label)
        route = repository.failure_triage_route_for_reason(reason)
        if route is None or not route.get("active", True):
            return False
        first = route.get("first_intervention")
        if not first:
            return False
        interventions.add(str(first))
        if len(interventions) > 1:
            return False
    return len(interventions) == 1


def robust_gate_counterfactual(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    posterior: Mapping[str, float],
) -> tuple[bool, str | None]:
    """The robust completion gate's verdict for a value CONTINUE receipt (the
    multi-family EVSI study's rank 1): ``(applies, verdict)``.

    ``applies`` is true only where the gate was skipped because value decides
    (``robust_gate_applies`` false) and the posterior is unstable (the gate's
    own branch of the completion policy); ``verdict`` is then what the gate
    would have said (``couldnt_reliably_distinguish``) or None. Elsewhere the
    gate either ran (and did not stop the episode) or never applies, and the
    receipt carries no counterfactual."""

    rows = repository.probe_observations_for_episode(episode.id)
    qualifying = [row for row in rows if row["observation"].eligible_for_completion]
    if not qualifying or robust_gate_applies(vault, repository, qualifying):
        return False, None
    episode_config = vault.config.probe.episode
    ordered = sorted((float(value) for value in posterior.values()), reverse=True)
    top = ordered[0] if ordered else 0.0
    second = ordered[1] if len(ordered) > 1 else 0.0
    stable = top >= episode_config.posterior_stop_threshold and (
        top <= 0 or second / top <= episode_config.ambiguity_threshold
    )
    if stable:
        return False, None
    return True, _robust_gate_verdict(vault, repository, episode, posterior)


def _robust_completion_override(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    posterior: EpisodePosterior,
    *,
    record_forecast: bool = True,
) -> str | None:
    """The mvp-0.8 robust stop/abstain gate (§4.2). Returns
    ``'couldnt_reliably_distinguish'`` when, after at least the minimum independent
    observations, the remaining instruments cannot robustly distinguish the
    hypotheses on the episode-pinned channel; otherwise None (defer to legacy park).

    Legacy episodes (no pinned channel) always return None -- byte-identical path.

    ``record_forecast``: where the gate decides, its forecast is logged
    (EVSI calibration Part B, site ``probe_robust_selection``). A
    counterfactual evaluation (rank 1: value decides the episode and the
    receipt only says what the gate would have done) passes False, so
    ``voi_forecasts`` never holds a gate decision that was not taken; the
    counterfactual lives on the value decision's own forecast instead."""

    return _robust_gate_verdict(
        vault, repository, episode, posterior.posterior, record_forecast=record_forecast
    )


def _robust_gate_verdict(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    belief: Mapping[str, float],
    *,
    record_forecast: bool = False,
) -> str | None:
    """:func:`_robust_completion_override` on a posterior mapping (a
    counterfactual by default: nothing is logged unless ``record_forecast``)."""

    if episode.calibration_model_hash is None:
        return None
    qualifying = sum(
        1 for row in repository.probe_observations_for_episode(episode.id)
        if row["observation"].eligible_for_completion
    )
    if qualifying < episode.minimum_independent_observations:
        return None
    from learnloop.diagnosis.probe_robust import (
        RobustCandidate,
        load_pinned_channel,
        robust_gate_fixes_on,
        robust_selection,
    )

    channel = load_pinned_channel(repository, episode.calibration_model_hash)
    if channel is None:
        return None
    candidates = eligible_instruments(vault, repository, episode, posterior=belief)
    if not candidates:
        # Out of instruments AND undecided is a genuine abstention only when the
        # legacy park would already fire; keep the legacy park semantics here so
        # the pending_items/generation-need path is unchanged.
        return None
    robust_candidates = [
        RobustCandidate(
            identifier=candidate.item.id,
            instrument=candidate.instrument,
            slot_map=dict(candidate.slot_map),
            expected_seconds=float(candidate.instrument.expected_seconds),
        )
        for candidate in candidates
    ]
    fixes_on = robust_gate_fixes_on(vault.config)
    decision = robust_selection(
        channel, robust_candidates, belief, episode_id=episode.id, distinct_instruments=fixes_on
    )
    if record_forecast:
        _record_robust_selection_forecast(
            vault, repository, episode, channel, decision, robust_candidates, belief, qualifying
        )
    return robust_gate_completion(decision, stop_only=fixes_on)


def robust_gate_completion(decision: Any, *, stop_only: bool) -> str | None:
    """The completion the robust gate's decision asks for: ``couldnt_reliably_distinguish`` or None.

    ``stop_only`` (the robust gate fixes, mvp-0.59): only a fragile *stop* ends the episode, i.e. the stop rule
    fires (nothing left is worth its minutes) and the winner is not robust. A fragile *pick* (``abstained`` while
    ``should_stop`` is false) means the next probe still pays and the ranking among the probes is uncertain;
    ending there threw away observations the stop rule priced as worth many times their minutes, and the value
    path reads the same situation as "keep measuring". Without ``stop_only`` every abstention ends the episode,
    as mvp-0.58 did."""

    if not decision.abstained:
        return None
    if stop_only and not decision.should_stop:
        return None
    return "couldnt_reliably_distinguish"


def _record_robust_selection_forecast(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    channel: Any,
    decision: Any,
    robust_candidates: Sequence[Any],
    posterior: Mapping[str, float],
    observations: int,
) -> None:
    """EVSI calibration Part B: log the robust gate's forecast (logging only).

    The chosen candidate's ensemble is rebuilt from the same pinned channel
    and decision-context hash ``robust_selection`` used, so it is the same
    ensemble; a failure here never touches the gate's verdict."""

    try:
        from learnloop.diagnosis.probe_robust import instrument_ensemble
        from learnloop.diagnosis.voi_forecasting import record_robust_selection_forecast

        ensembles = {}
        chosen = next((c for c in robust_candidates if c.identifier == decision.chosen_slot), None)
        if chosen is not None:
            ensemble, _dch = instrument_ensemble(
                channel, chosen.instrument, chosen.slot_map, dict(posterior), episode_id=episode.id
            )
            ensembles[chosen.identifier] = ensemble
        record_robust_selection_forecast(
            vault,
            repository,
            episode=episode,
            decision=decision,
            candidates=robust_candidates,
            ensembles=ensembles,
            posterior=posterior,
            observations=observations,
        )
    except Exception:  # noqa: BLE001 - logging must never change the gate
        logging.getLogger(__name__).warning("robust selection forecast not recorded", exc_info=True)


def _surface_key(vault: LoadedVault, practice_item_id: str) -> str:
    """The independent-group key for a probe observation (augmentation §8).

    ``surface_group_id`` rather than the raw ``surface_family``: this key decides
    how many DISTINCT surfaces an episode has covered, so reading the authored
    string let two near-clones sharing a stimulus, a source example or a solution
    template count as two — the episode would then believe it had corroborated a
    hypothesis across surfaces when it had asked one question twice.

    An unresolvable item falls back to its own id, which is the conservative
    direction here and the opposite of the promotion arm's: there, an unknown
    item must not manufacture independence, so the arm fails closed; here, a
    missing item that collapsed into some other group would make an episode look
    MORE covered than it is. Distinct-by-default is the safe reading.
    """

    item = vault.practice_items.get(practice_item_id)
    if item is None:
        return practice_item_id
    return surface_group_id(item)


def _complete(
    repository: Repository,
    episode: ProbeEpisodeRecord,
    reason: str,
    *,
    posterior: EpisodePosterior | None = None,
    detail: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> str:
    active = repository.active_probe_presentation(episode.id)
    if active is not None:
        repository.end_probe_presentation(active.id, end_reason="invalidated", clock=clock)
    repository.update_probe_episode_status(
        episode.id,
        status="complete",
        completion_reason=reason,
        completed_at=utc_now_iso(clock),
        completion_posterior_json=(
            json.dumps(posterior.posterior, sort_keys=True) if posterior is not None else None
        ),
        completion_detail_json=(
            json.dumps(dict(detail), sort_keys=True, default=str) if detail is not None else None
        ),
        clock=clock,
    )
    return reason


def _complete_on_value_stop(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    posterior: EpisodePosterior,
    value_stop: Mapping[str, Any],
    *,
    clock: Clock | None = None,
) -> str:
    """Complete the episode on its value stop (the decision kept in
    ``completion_detail_json``) and log that stop as a forecast
    (``probe_episode_value_decision``, once per episode; EVSI calibration's
    ``voi_forecasts`` behind ``evsi.forecast_logging``, logging only)."""

    reason = _complete(
        repository, episode, "value_of_information_stop", posterior=posterior, detail=value_stop, clock=clock
    )
    from learnloop.diagnosis.voi_forecasting import record_value_decision_forecast

    record_value_decision_forecast(
        vault,
        repository,
        value_stop,
        receipt_key=f"probe_episode_value_decision:{episode.id}:value_of_information_stop",
        clock=clock,
        decision_ref=episode.id,
        probe_episode_id=episode.id,
    )
    return reason


def _value_of_information_stop(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    posterior: EpisodePosterior,
    qualifying: list[dict[str, Any]],
    candidates: list[EligibleInstrument],
    *,
    gate_counterfactual: Any = None,
) -> dict[str, Any] | None:
    """mvp-0.21 (voi_stopping, site ``probe_episode``): the logged stop
    decision when the episode's next observation no longer pays for its
    minutes, or None (keep asking, or the site is off).

    Checked where the episode would otherwise continue, after at least one
    qualifying observation (as the decision-equivalence stop is) and with an
    eligible instrument to value (an empty pool keeps its own park). A
    calibration session the observation was made in lifts the rule, as it
    lifted the session cap. ``gate_counterfactual`` (the study's rank 1) is
    the robust completion gate, called only on a stop, whose verdict the stop
    records in ``former_cap.robust_completion_gate``.
    """

    from learnloop.diagnosis import voi_stopping as voi

    if not qualifying or not candidates or not value_decides_episode(vault, repository, qualifying):
        return None
    session_id = _latest_observation_session(repository, qualifying)
    decision = voi.probe_episode_decision(
        voi.VoiContext(vault, repository), episode, candidates, posterior.posterior, session_id=session_id
    )
    if decision.decision == voi.CONTINUE:
        return None
    if gate_counterfactual is not None:
        decision = voi.with_robust_gate_counterfactual(decision, gate_counterfactual())
    return decision.as_dict()


def close_diagnostic_segment(
    repository: Repository,
    episode_id: str,
    *,
    reason: str = "converted_to_tutoring",
    clock: Clock | None = None,
) -> ProbeEpisodeRecord | None:
    """Close a still-open diagnostic episode when instruction/repair begins (P0
    invariant 7 / §12.2 "starting instruction closes the measurement segment").

    Repository-only (no vault): ends any active presentation, marks the episode
    ``converted_to_tutoring``, and opens a post-intervention state segment so no later
    attempt updates the pre-intervention posterior. A subsequent :func:`enter_episode`
    on the same LO then mints a FRESH episode -- the closed segment never re-opens.
    Idempotent: an already-terminal episode returns None (nothing to close)."""

    episode = repository.probe_episode(episode_id)
    if episode is None or episode.status not in ("in_progress", "pending_items"):
        return None
    active = repository.active_probe_presentation(episode.id)
    if active is not None:
        repository.end_probe_presentation(active.id, end_reason="invalidated", clock=clock)
    repository.update_probe_episode_status(
        episode.id,
        status="converted_to_tutoring",
        completion_reason=reason,
        completed_at=utc_now_iso(clock),
        clock=clock,
    )
    repository.open_state_segment(
        learning_object_id=episode.learning_object_id,
        probe_episode_id=episode.id,
        reason="tutoring_transition",
        clock=clock,
    )
    return repository.probe_episode(episode.id)


def set_target_decision(
    repository: Repository, episode_id: str, decision: Mapping[str, Any], *, clock: Clock | None
) -> None:
    import json as _json_module

    now = utc_now_iso(clock)
    with repository.connection() as connection:
        connection.execute(
            "UPDATE probe_episodes SET target_decision_json = ?, updated_at = ? WHERE id = ?",
            (_json_module.dumps(decision), now, episode_id),
        )
        connection.commit()

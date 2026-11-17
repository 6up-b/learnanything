"""Adaptive diagnostic episode lifecycle, instruments, and posterior replay.

Episodes lock a hypothesis set and record the measurement contract at opening.
Instrument selection ranks eligible items using the episode's hypotheses,
exposure exclusions, calibration, and observed evidence.
Posterior replay uses relevant attempts with contamination-adjusted likelihoods;
only qualifying selected observations count toward diagnostic coverage.
Legacy probe phases replay through their recorded algorithm version.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import log
import json
from typing import Any, Iterable, Mapping

from learnloop.followup_serve.gates import generate_and_serve_on
from learnloop.followup_serve.queue import enqueue_entry
from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.repositories import (
    ProbeEpisodeRecord,
    Repository,
)
from learnloop.ids import new_ulid
from learnloop.substrate.canonical_projection import surface_group_id
from learnloop.substrate.instrument_serving import unservable_reason
from learnloop.diagnosis.probe_families import (
    CompiledInstrument,
    InstrumentCard,
    ProbeFamilyTemplate,
    classify_outcome,
    ensure_builtin_families,
    information_rate,
    instrument_expected_information_gain,
    instrument_observation_likelihoods,
    instrument_predictive_information_gain,
    map_episode_labels_to_slots,
    shrunk_item_calibration_counts,
    validate_and_compile_card,
)
from learnloop.diagnosis.probe_hypotheses import (
    H_OTHER,
    build_episode_hypothesis_set,
    generic_bucket_marginals,
    item_observation_context,
)
from learnloop.diagnosis.probes import (
    HypothesisSet,
    item_registry_discrimination,
    resolve_item_irt,
    score_bucket,
)
from learnloop.vault.lifecycle import learning_object_servable
from learnloop.vault.models import LoadedVault, PracticeItem

FALLBACK_FAMILY_ID = "registry_discrimination_fallback"
FALLBACK_FAMILY_VERSION = 1


@dataclass(frozen=True)
class EligibleInstrument:
    """One (item, compiled instrument) pair usable by the open episode.

    ``expected_information_gain`` is the actual hypothesis EIG (§7.2);
    ``predictive_eig`` and ``predictive_information_rate`` implement the §7.4
    predictive objective over the episode's held-out target instruments. The
    two are never added (§7.4): ``selection_objective`` names which one ranked
    this candidate.
    """

    item: PracticeItem
    instrument: CompiledInstrument
    slot_map: dict[str, str]
    expected_information_gain: float
    predictive_eig: float = 0.0
    predictive_prior_entropy: float = 0.0
    predictive_target_count: int = 0
    predictive_information_rate: float = 0.0
    selection_objective: str = "hypothesis_eig"
    # §7.3/Checkpoint 5.2: a separate ranking multiplier (< 1 when this
    # candidate's family already produced an observation this episode). Never
    # folded into the EIG values themselves — only the ranking uses it.
    redundancy_penalty: float = 1.0
    # §7.4: the held-out (instrument, slot map) targets ``predictive_eig`` was
    # computed over, so a conditional valuation (voi_stopping, final verify
    # F2) recomputes the same objective on each posterior branch. Not logged.
    predictive_targets: tuple[tuple[CompiledInstrument, dict[str, str]], ...] = field(
        default=(), compare=False, repr=False
    )
    # §5.4: the item's canonical surface group (``surface_group_id``), the key
    # the exposure rule excludes by once one item of the group is observed. A
    # lookahead batch holds at most one check per group (voi_stopping, Codex
    # review of voi-v2 F13). Not logged.
    surface_group: str | None = field(default=None, compare=False, repr=False)

    def selection_components(self) -> dict[str, Any]:
        """§7.3 separately-inspectable utility components for telemetry."""

        return {
            "actual_hypothesis_eig": self.expected_information_gain,
            "predictive_eig": self.predictive_eig,
            "predictive_prior_entropy": self.predictive_prior_entropy,
            "predictive_target_count": self.predictive_target_count,
            "predictive_information_rate": self.predictive_information_rate,
            "expected_seconds": self.instrument.expected_seconds,
            "selection_objective": self.selection_objective,
            "redundancy_penalty": self.redundancy_penalty,
        }


@dataclass(frozen=True)
class EpisodePosterior:
    hypothesis_set: HypothesisSet
    prior: dict[str, float]
    posterior: dict[str, float]
    qualifying_observations: int
    total_observations: int
    entropy: float

    @property
    def top(self) -> tuple[str, float]:
        if not self.posterior:
            return ("", 0.0)
        label = max(self.posterior, key=lambda key: self.posterior[key])
        return (label, self.posterior[label])


def _entropy(distribution: Mapping[str, float]) -> float:
    return -sum(p * log(p) for p in distribution.values() if p > 0)


# --- Episode lifecycle (§5.1/§5.2) ------------------------------------------------


def episode_open_contract(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    trigger: str,
    goal_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """What an episode opened now for ``trigger`` is held to: its observation
    budget, required facets, terminal-contract pin, calibration channel pin
    and algorithm version (the ``probe_episodes`` columns set at open).

    :func:`enter_episode` stamps these on a new episode, and
    :func:`adopt_ignored_opening_episode` re-stamps them on the opening episode
    it adopts, so an adopted episode is held to the contract of the request it
    stands in for (Codex re-review F1).
    """

    from learnloop.learner.facet_diagnostics import required_facets

    episode_config = vault.config.probe.episode
    # Pin the exact confirmed terminal-contract version at episode open (§3.4).
    # Ungoal-conditioned probes leave the pin NULL (not a terminal claim).
    target_contract_version_id: str | None = None
    target_support_hash: str | None = None
    if goal_id is not None:
        from learnloop.goals.goal_contracts import resolve_head

        head = resolve_head(repository, goal_id)
        if head is not None:
            target_contract_version_id = head.id
            target_support_hash = head.support_hash

    # The robust cutover (§4.2, invariant 3): resolve + pin the calibration
    # channel at episode open. Both robust selection and the decision-time
    # observed_update consume this pinned model hash (an episode opened before
    # the cutover holds NULL and keeps the point path).
    from learnloop.diagnosis.probe_robust import resolve_episode_channel

    channel = resolve_episode_channel(
        repository, learning_object_id=learning_object_id, clock=clock
    )
    calibration_model_id = channel.model_id or None
    calibration_model_hash = channel.model_hash
    probe_mapping_version = channel.mapping_version
    return {
        "algorithm_version": vault.config.algorithms.algorithm_version,
        "required_facets": sorted(required_facets(vault, learning_object_id, repository)),
        # Purpose-specific minimum: initial/goal placement is a routing
        # conclusion, so one qualifying observation may complete it; the
        # 2-observation breadth contract stays for diagnostic re-entries
        # (misconception / stale-uncertainty triggers), whose conclusions feed
        # stronger claims.
        "minimum_independent_observations": (
            episode_config.placement_minimum_observations
            if trigger in ("initial", "goal_diagnostic")
            else episode_config.minimum_independent_observations
        ),
        "maximum_observations": episode_config.maximum_observations,
        "target_contract_version_id": target_contract_version_id,
        "target_support_hash": target_support_hash,
        "calibration_model_id": calibration_model_id,
        "calibration_model_hash": calibration_model_hash,
        "probe_mapping_version": probe_mapping_version,
    }


def enter_episode(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    trigger: str = "initial",
    origin: str | None = None,
    goal_id: str | None = None,
    causal_factor_id: str | None = None,
    clock: Clock | None = None,
    ai_client: object | None = None,
    reserved_for: str | None = None,
) -> ProbeEpisodeRecord:
    """Open a diagnostic episode with a fresh ULID and locked hypothesis set.

    ``reserved_for`` (FG1): the generated probe this episode is opened to serve, which
    no other selector may read.

    Idempotent per LO: an already-open episode is returned unchanged. The
    episode enters ``in_progress`` when an eligible instrument exists locally,
    otherwise ``pending_items`` with one deduplicated generation need (§10) —
    which never blocks ordinary practice on the LO.

    ``origin`` records how the episode was launched (e.g.
    ``'overconfidence_list'``, spec §4.3) so analytics can separate adversarial
    selection from drift. It is persisted into the dedicated ``origin`` column
    (migration 059) at creation, so it survives target selection — which
    overwrites ``target_decision_json`` and previously erased the origin.

    Under placement an unanswered opening episode an earlier version opened is
    ignored (owner decision 2026-10-12); a door that opens an episode on its LO
    adopts it (:func:`adopt_ignored_opening_episode`) instead of returning it
    unchanged, so the request is served.
    """

    existing = repository.open_probe_episode(learning_object_id)
    if existing is not None and causal_factor_id is None:
        from learnloop.placement.state import episode_ignored

        if episode_ignored(vault, repository, existing):
            existing = adopt_ignored_opening_episode(
                vault, repository, existing, trigger=trigger, origin=origin, goal_id=goal_id, clock=clock,
            )
    if existing is not None:
        if existing.status == "pending_items" and generate_and_serve_on(vault.config):
            # FG1 §4.3: deduplicated work for the worker, so an entry can't stall or burst.
            enqueue_entry(repository, existing.id, clock=clock)
            return existing
        if (
            existing.status == "pending_items"
            and vault.config.probe.generation.auto_generate_on_entry
        ):
            from learnloop.diagnosis.probe_instance_generation import generate_instances_for_episode

            generate_instances_for_episode(
                repository, vault, existing.id, clock=clock, ai_client=ai_client
            )
            return repository.probe_episode(existing.id) or existing
        return existing

    ensure_builtin_families(repository, clock=clock)
    algorithm_version = vault.config.algorithms.algorithm_version
    episode_id = new_ulid()
    if causal_factor_id is not None:
        from learnloop.diagnosis.causal_probe_coherence import (
            lock_causal_hypothesis_set,
        )

        hypothesis_set = lock_causal_hypothesis_set(
            repository,
            causal_factor_id,
            probe_phase_id=episode_id,
            algorithm_version=algorithm_version,
            clock=clock,
        )
        if hypothesis_set.learning_object_id != learning_object_id:
            raise ValueError(
                "causal factor belongs to a different learning object"
            )
        hypothesis_set_id = str(hypothesis_set.id)
    else:
        hypothesis_set = build_episode_hypothesis_set(
            vault, repository, learning_object_id, clock=clock
        )
        hypothesis_set_id = repository.insert_hypothesis_set(
            learning_object_id=learning_object_id,
            probe_phase_id=episode_id,
            hypotheses=[
                hypothesis.as_record()
                for hypothesis in hypothesis_set.hypotheses
            ],
            prior=hypothesis_set.prior,
            algorithm_version=algorithm_version,
            clock=clock,
        )
    locked = HypothesisSet(
        learning_object_id=learning_object_id,
        hypotheses=hypothesis_set.hypotheses,
        prior=hypothesis_set.prior,
        id=hypothesis_set_id,
    )
    now = utc_now_iso(clock)
    repository.insert_probe_episode(
        episode_id=episode_id,
        learning_object_id=learning_object_id,
        status="pending_items",
        trigger=trigger,
        hypothesis_set_id=hypothesis_set_id,
        active_state_segment_id=None,
        target_decision=(
            {
                "kind": "causal_repair_class_divergence",
                "causal_factor_id": causal_factor_id,
            }
            if causal_factor_id is not None
            else None
        ),
        origin=origin,
        entered_at=now,
        clock=clock,
        **episode_open_contract(
            vault, repository, learning_object_id, trigger=trigger, goal_id=goal_id, clock=clock,
        ),
    )
    repository.open_state_segment(
        learning_object_id=learning_object_id,
        probe_episode_id=episode_id,
        reason="episode_entry",
        clock=clock,
    )
    episode = repository.probe_episode(episode_id)
    assert episode is not None
    instruments = eligible_instruments(
        vault, repository, episode, hypothesis_set=locked, reserved_for=reserved_for
    )
    if instruments:
        repository.update_probe_episode_status(episode_id, status="in_progress", clock=clock)
    elif learning_object_servable(vault, learning_object_id):
        # A dormant/resolved LO has no eligible pool by lifecycle, not by a
        # missing surface: commission nothing for it (vault.lifecycle).
        _record_generation_need(vault, repository, episode, locked, clock=clock)
        if generate_and_serve_on(vault.config):
            # FG1 §4.3: every entry point enqueues; the worker chooses the contract.
            enqueue_entry(repository, episode_id, clock=clock)
        elif vault.config.probe.generation.auto_generate_on_entry:
            from learnloop.diagnosis.probe_instance_generation import generate_instances_for_episode

            generate_instances_for_episode(
                repository, vault, episode_id, clock=clock, ai_client=ai_client
            )
    refreshed = repository.probe_episode(episode_id)
    assert refreshed is not None
    return refreshed


def episode_has_observations(repository: Repository, episode_id: str) -> bool:
    """True when this episode's locked hypothesis set has interpreted evidence.

    Both channels count: a recorded probe observation, and a presentation the
    learner already consumed (a submission whose observation was not qualifying
    still happened under the locked set). An episode that has neither has
    measured nothing, so nothing can be *re*interpreted by relocking it.
    """

    if repository.probe_observations_for_episode(episode_id):
        return True
    return any(
        presentation.status == "submitted"
        for presentation in repository.probe_presentations_for_episode(episode_id)
    )


#: The ``probe_episodes`` columns :func:`episode_open_contract` sets, as a
#: relock may re-stamp them (column name -> how it is stored).
_CONTRACT_COLUMNS = (
    "algorithm_version",
    "required_facets_json",
    "minimum_independent_observations",
    "maximum_observations",
    "target_contract_version_id",
    "target_support_hash",
    "calibration_model_id",
    "calibration_model_hash",
    "probe_mapping_version",
)


def _relock_episode_row(
    repository: Repository,
    episode_id: str,
    *,
    hypothesis_set_id: str,
    origin: str | None,
    target_decision: Mapping[str, Any],
    clock: Clock | None,
    contract: Mapping[str, Any] | None = None,
) -> None:
    """Point the row at the new set. ``contract`` (an
    :func:`episode_open_contract`) also re-stamps the open-time contract; the
    causal relock leaves it as the episode was opened."""

    now = utc_now_iso(clock)
    contract_values: list[Any] = []
    if contract is not None:
        stored = {
            **{key: value for key, value in contract.items() if key != "required_facets"},
            "required_facets_json": json.dumps(list(contract["required_facets"]), sort_keys=True, separators=(",", ":")),
        }
        contract_values = [stored[column] for column in _CONTRACT_COLUMNS]
    contract_sql = "".join(f", {column} = ?" for column in _CONTRACT_COLUMNS) if contract is not None else ""
    with repository.connection() as connection:
        connection.execute(
            f"""
            UPDATE probe_episodes
               SET hypothesis_set_id = ?, origin = ?, target_decision_json = ?,
                   entered_at = ?, updated_at = ?{contract_sql}
             WHERE id = ?
            """,
            (
                hypothesis_set_id,
                origin,
                json.dumps(dict(target_decision)),
                # `entered_at` moves with the lock. `episode_posterior` scopes
                # replay by it (not by state segment), so leaving it behind
                # would replay evidence recorded under the PREVIOUS set into the
                # new one — including the very attempt the cause hypotheses were
                # derived from, which would then be scored as independent
                # evidence for itself. A freshly entered episode excludes that
                # evidence by construction; so does this one.
                now,
                now,
                *contract_values,
                episode_id,
            ),
        )
        connection.commit()


def retarget_episode_to_causal_factor(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    causal_factor_id: str,
    *,
    origin: str,
    clock: Clock | None = None,
    reserved_for: str | None = None,
) -> ProbeEpisodeRecord:
    """Point an OBSERVATION-FREE open episode at a causal cause set.

    At most one episode may be open per Learning Object (unique index
    ``idx_probe_episodes_open``), and vault state sync cold-starts a plain
    ``initial`` episode for every active LO. Without this, the causal
    disambiguation probe could never be served in the running app: the placement
    episode owns the LO and ``accept_probe_offer`` refuses.

    The refusal it replaces is still correct where it bites — locking a second
    hypothesis set over an episode that has already recorded observations would
    reinterpret those observations under a set that did not exist when they were
    made. So this is precondition-guarded rather than removed: an episode with
    ANY observation (see :func:`episode_has_observations`) is refused, and only
    an episode that has measured nothing is relocked.

    The episode keeps its entry ``trigger`` and observation budget — they
    describe how the block was opened and are not retro-written. The causal
    provenance rides on ``origin`` and ``target_decision``, which is the same
    place :func:`enter_episode` puts it. ``entered_at`` DOES move: it is what
    :func:`episode_posterior` scopes replay by, so the measurement block under
    the new set has to start at the relock or the new set would inherit evidence
    gathered under the old one.
    """

    if episode.status not in ("pending_items", "in_progress"):
        raise ValueError("only an open probe episode can be retargeted")
    if episode_has_observations(repository, episode.id):
        raise ValueError(
            "a probe episode with observations cannot be relocked onto a new "
            "hypothesis set"
        )

    from learnloop.diagnosis.causal_probe_coherence import lock_causal_hypothesis_set

    hypothesis_set = lock_causal_hypothesis_set(
        repository,
        causal_factor_id,
        probe_phase_id=episode.id,
        algorithm_version=vault.config.algorithms.algorithm_version,
        clock=clock,
    )
    if hypothesis_set.learning_object_id != episode.learning_object_id:
        raise ValueError("causal factor belongs to a different learning object")

    # Anything committed under the old set is not an assignment under the new
    # one; it must not stay consumable.
    active = repository.active_probe_presentation(episode.id)
    if active is not None:
        repository.end_probe_presentation(
            active.id, end_reason="invalidated", clock=clock
        )

    _relock_episode_row(
        repository,
        episode.id,
        hypothesis_set_id=str(hypothesis_set.id),
        origin=origin,
        target_decision={
            "kind": "causal_repair_class_divergence",
            "causal_factor_id": causal_factor_id,
            "relocked_from_hypothesis_set_id": episode.hypothesis_set_id,
        },
        clock=clock,
    )
    relocked = repository.probe_episode(episode.id)
    assert relocked is not None
    instruments = eligible_instruments(
        vault, repository, relocked, hypothesis_set=hypothesis_set, reserved_for=reserved_for
    )
    repository.update_probe_episode_status(
        episode.id,
        status="in_progress" if instruments else "pending_items",
        clock=clock,
    )
    if not instruments:
        _record_generation_need(vault, repository, relocked, hypothesis_set, clock=clock)
    refreshed = repository.probe_episode(episode.id)
    assert refreshed is not None
    return refreshed


#: ``target_decision.kind`` of an opening episode a door adopted under placement.
ADOPTED_OPENING_EPISODE_KIND = "adopted_opening_episode"


def adopt_ignored_opening_episode(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    *,
    trigger: str,
    origin: str | None,
    goal_id: str | None = None,
    clock: Clock | None = None,
) -> ProbeEpisodeRecord:
    """Adopt an unanswered opening episode placement ignores (owner decision 2026-10-12).

    At most one episode may be open per LO, so a door that opens one (an
    error-driven re-probe, the overconfidence list, a calibration, a
    golden-path baseline) would otherwise get the ignored episode back
    unchanged and nothing would be served. It is relocked the way the causal
    quick check relocks an observation-free episode
    (:func:`retarget_episode_to_causal_factor`): a fresh hypothesis set locked
    now, any committed presentation invalidated, ``entered_at`` moved with the
    lock, and the request stamped on ``origin`` and ``target_decision``. That
    stamp is what stops placement ignoring it. The episode keeps its id and its
    ``initial`` trigger (the requested trigger rides on ``target_decision``),
    but unlike the causal relock it is held to the contract of the request it
    stands in for (Codex re-review F1): its observation budget, required
    facets, terminal-contract pin, calibration channel pin and algorithm
    version are re-stamped as :func:`enter_episode` would set them for the
    requested trigger now (:func:`episode_open_contract`). An error-driven
    re-probe therefore keeps the two-observation breadth contract, and no
    adopted episode decides on a channel pinned when an earlier version opened
    it.

    Nothing changes until the learner or an error acts, so the kill switches
    stay exact for every episode no door touched.
    """

    if episode.status not in ("pending_items", "in_progress"):
        raise ValueError("only an open probe episode can be adopted")
    if episode_has_observations(repository, episode.id):
        raise ValueError("an answered opening episode is not ignored, so it is never adopted")
    learning_object_id = episode.learning_object_id
    hypothesis_set = build_episode_hypothesis_set(vault, repository, learning_object_id, clock=clock)
    hypothesis_set_id = repository.insert_hypothesis_set(
        learning_object_id=learning_object_id,
        probe_phase_id=episode.id,
        hypotheses=[hypothesis.as_record() for hypothesis in hypothesis_set.hypotheses],
        prior=hypothesis_set.prior,
        algorithm_version=vault.config.algorithms.algorithm_version,
        clock=clock,
    )
    locked = HypothesisSet(
        learning_object_id=learning_object_id,
        hypotheses=hypothesis_set.hypotheses,
        prior=hypothesis_set.prior,
        id=hypothesis_set_id,
    )
    active = repository.active_probe_presentation(episode.id)
    if active is not None:
        repository.end_probe_presentation(active.id, end_reason="invalidated", clock=clock)
    _relock_episode_row(
        repository,
        episode.id,
        hypothesis_set_id=str(hypothesis_set_id),
        origin=origin,
        target_decision={
            "kind": ADOPTED_OPENING_EPISODE_KIND,
            "requested_trigger": trigger,
            "requested_origin": origin,
            "goal_id": goal_id,
            "relocked_from_hypothesis_set_id": episode.hypothesis_set_id,
        },
        clock=clock,
        contract=episode_open_contract(
            vault, repository, learning_object_id, trigger=trigger, goal_id=goal_id, clock=clock,
        ),
    )
    relocked = repository.probe_episode(episode.id)
    assert relocked is not None
    instruments = eligible_instruments(vault, repository, relocked, hypothesis_set=locked)
    repository.update_probe_episode_status(
        episode.id,
        status="in_progress" if instruments else "pending_items",
        clock=clock,
    )
    if not instruments and learning_object_servable(vault, learning_object_id):
        _record_generation_need(vault, repository, relocked, locked, clock=clock)
    refreshed = repository.probe_episode(episode.id)
    assert refreshed is not None
    return refreshed


def _open_episode_blocks(vault: LoadedVault, repository: Repository, learning_object_id: str) -> bool:
    """Whether an open episode already owns the LO for a re-probe trigger.

    An unanswered opening episode placement ignores does not: the re-probe
    adopts it (owner decision 2026-10-12; field §5.2, a diagnostic episode
    still opens when a wrong answer leaves a real choice of repair).
    """

    existing = repository.open_probe_episode(learning_object_id)
    if existing is None:
        return False
    from learnloop.placement.state import episode_ignored

    return not episode_ignored(vault, repository, existing)


def maybe_reprobe_for_misconception(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    severity: float,
    clock: Clock | None = None,
) -> ProbeEpisodeRecord | None:
    """Re-probe trigger (§6.5): a new high-severity misconception opens a new
    episode with a new locked hypothesis-set snapshot."""

    if severity < 0.6:
        return None
    if _open_episode_blocks(vault, repository, learning_object_id):
        return None
    return enter_episode(
        vault, repository, learning_object_id, trigger="misconception", clock=clock
    )


def maybe_reprobe_for_predictive_failure(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    clock: Clock | None = None,
) -> ProbeEpisodeRecord | None:
    """Re-probe trigger (§6.5/Checkpoint 2.7): repeated prediction errors
    indicate model misspecification.

    When at least ``reprobe_prediction_error_count`` of the LO's last
    ``reprobe_prediction_error_window`` attempts carried a negative surprise
    above ``reprobe_predictive_surprise_threshold`` nats, the LO re-enters
    probing with trigger ``stale_uncertainty`` — but only once the LO has been
    probed before (a never-probed LO enters through §5.9 orchestration) and no
    episode is currently open.
    """

    episode_config = vault.config.probe.episode
    threshold = episode_config.reprobe_predictive_surprise_threshold
    needed = episode_config.reprobe_prediction_error_count
    window = episode_config.reprobe_prediction_error_window
    if needed <= 0 or window <= 0:
        return None
    if _open_episode_blocks(vault, repository, learning_object_id):
        return None
    if not any(
        entry.learning_object_id == learning_object_id
        and entry.status in ("complete", "converted_to_tutoring", "abandoned")
        for entry in repository.list_probe_episodes()
    ):
        return None
    recent = repository.list_recent_attempts_by_learning_object(learning_object_id, limit=window)
    failures = 0
    for attempt in recent:
        surprise = repository.latest_attempt_surprise(str(attempt.get("id"))) or {}
        if (
            surprise.get("surprise_direction") == "negative"
            and float(surprise.get("predictive_surprise") or 0.0) >= threshold
        ):
            failures += 1
    if failures < needed:
        return None
    return enter_episode(
        vault, repository, learning_object_id, trigger="stale_uncertainty", clock=clock
    )


def enter_stale_uncertainty_reprobes(
    vault: LoadedVault,
    repository: Repository,
    *,
    clock: Clock | None = None,
) -> list[ProbeEpisodeRecord]:
    """Periodic re-probe producer (§6.5): high uncertainty that persists after
    a completed episode re-enters probing with trigger ``stale_uncertainty``.

    Runs from vault state sync. An LO qualifies when its newest episode is
    terminal and older than ``reprobe_stale_uncertainty_days``, and its mastery
    logit variance is at/above ``reprobe_stale_uncertainty_variance``.
    """

    episode_config = vault.config.probe.episode
    if episode_config.reprobe_stale_uncertainty_days <= 0:
        return []
    now = parse_utc(utc_now_iso(clock))
    if now is None:
        return []
    latest_terminal: dict[str, ProbeEpisodeRecord] = {}
    open_los: set[str] = set()
    for entry in repository.list_probe_episodes():
        if entry.status in ("in_progress", "pending_items"):
            open_los.add(entry.learning_object_id)
        elif entry.status in ("complete", "converted_to_tutoring", "abandoned"):
            latest_terminal[entry.learning_object_id] = entry
    opened: list[ProbeEpisodeRecord] = []
    for lo_id, last_episode in sorted(latest_terminal.items()):
        if lo_id in open_los or lo_id not in vault.learning_objects:
            continue
        # A dormant/resolved LO is put away by the learner: never re-open probing.
        if not learning_object_servable(vault, lo_id):
            continue
        completed = parse_utc(last_episode.completed_at)
        if completed is None:
            continue
        if (now - completed).days < episode_config.reprobe_stale_uncertainty_days:
            continue
        mastery = repository.mastery_state(lo_id)
        if mastery is None:
            continue
        if mastery.logit_variance < episode_config.reprobe_stale_uncertainty_variance:
            continue
        opened.append(
            enter_episode(vault, repository, lo_id, trigger="stale_uncertainty", clock=clock)
        )
    return opened


def _record_generation_need(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    hypothesis_set: HypothesisSet,
    *,
    clock: Clock | None = None,
) -> None:
    from learnloop.diagnosis.probe_instance_generation import applicable_families

    # A parked (dormant/resolved) LO's pool is empty by lifecycle, not for want
    # of a surface: no generation is commissioned for it (vault.lifecycle).
    if not learning_object_servable(vault, episode.learning_object_id):
        return
    labels = sorted(hypothesis.label for hypothesis in hypothesis_set.hypotheses if hypothesis.label != H_OTHER)
    target_key = "|".join(labels[:2]) if len(labels) >= 2 else "|".join(labels)
    learning_object = vault.learning_objects.get(episode.learning_object_id)
    families = applicable_families(vault, learning_object, repository) if learning_object is not None else []
    missing_capability = families[0].id if families else "contrast_confusable"
    repository.upsert_probe_generation_need(
        probe_episode_id=episode.id,
        learning_object_id=episode.learning_object_id,
        target_key=target_key,
        missing_capability=missing_capability,
        clock=clock,
    )


def episode_hypothesis_set(
    repository: Repository, episode: ProbeEpisodeRecord
) -> HypothesisSet | None:
    if episode.hypothesis_set_id is None:
        return None
    record = repository.fetch_hypothesis_set(episode.hypothesis_set_id)
    if record is None:
        return None
    return HypothesisSet.from_record(record)


# --- Instrument resolution (§9, §7.2) ----------------------------------------------


def administered_surface_exclusions(
    vault: LoadedVault, repository: Repository
) -> tuple[set[str], set[str]]:
    """Surfaces the learner has already seen in ANY administration.

    Returns ``(attempted_item_ids, attempted_surface_group_ids)``. Attempted
    items no longer present in the vault still exclude by id (their surface
    group cannot be resolved, but the exact item is certainly familiar).
    """

    attempted_ids = repository.attempted_practice_item_ids()
    attempted_surfaces: set[str] = set()
    for item_id in attempted_ids:
        attempted_item = vault.practice_items.get(item_id)
        if attempted_item is not None:
            attempted_surfaces.add(surface_group_id(attempted_item))
    return attempted_ids, attempted_surfaces


def eligible_instruments(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    *,
    hypothesis_set: HypothesisSet | None = None,
    posterior: Mapping[str, float] | None = None,
    reserved_for: str | None = None,
) -> list[EligibleInstrument]:
    """Instruments admitted for this episode's locked set, ranked by EIG.

    Card-bound items compile through their admitted family/card version; items
    that discriminate a registry misconception in the set compile through the
    explicitly-logged legacy fallback (§7.2). Items with neither are not probe
    candidates (§4.2 fix) — they remain ordinary practice.
    """

    hypothesis_set = hypothesis_set or episode_hypothesis_set(repository, episode)
    if hypothesis_set is None:
        return []
    # FG1 §5: a workflow's pinned probe holds this episode until it is answered or closed: a
    # routine selection committing another presentation would supersede the pin.
    standing = repository.active_probe_presentation(episode.id)
    if standing is not None and standing.practice_item_id != reserved_for:
        pin = dict(standing.selection_components or {}).get("causal_probe")
        if isinstance(pin, Mapping) and pin.get("followup_workflow_id"):
            return []
    # Learner-set LO lifecycle: no item of a dormant/resolved LO is administered,
    # as a probe or otherwise (vault.lifecycle).
    if not learning_object_servable(vault, episode.learning_object_id):
        return []
    # P4 §14.2 step 3 dual-authority (design §A.2 rule 3): the probe path is an
    # administration surface too. A staged-owned P2 commitment's items are the staged
    # policy's to administer, never the legacy sidecar probe path. Refuse outright when
    # the episode's whole learning object is staged-owned; otherwise drop just the owned
    # items from the eligible slate. Empty exclusion set -> byte-identical legacy behavior
    # for a vault with no ownership rows.
    from learnloop.scheduling import controller_ownership as _ownership

    if _ownership.is_learning_object_staged_owned(repository, episode.learning_object_id):
        raise _ownership.StagedOwnedAdministrationRefused(episode.learning_object_id)
    staged_owned_item_ids = _ownership.staged_owned_practice_item_ids(vault, repository)
    if posterior is None:
        # Sequential selection conditions on the observed posterior (§8.3), not
        # the locked entry prior — a second observation must not be ranked as
        # if the first never happened.
        live = episode_posterior(vault, repository, episode, hypothesis_set=hypothesis_set)
        posterior = live.posterior if live is not None else hypothesis_set.prior
    belief = dict(posterior)
    item_states = repository.practice_item_states()

    # §5.4 exposure rule: an item already observed in this episode — or another
    # item of an already-observed surface group — is a disallowed repeat.
    # Family observation counts feed the Checkpoint 5.2 redundancy penalty.
    #
    # The group is `surface_group_id`, the ONE exact independence primitive
    # (augmentation §8), not the raw `surface_family` string this rule used to
    # read. The difference is the whole point of the exposure rule: a near-clone
    # sharing a stimulus, a source example or a solution template is the same
    # observation, and comparing authored family strings let it through whenever
    # the two happened to be named differently. A laddered stem (Meas §3.A2) is
    # the sharpest case — its parts share one stimulus by construction and each
    # part is free to carry its own family string — so without this the probe
    # could spend several administrations re-observing one setup.
    used_item_ids: set[str] = set()
    # FG1 §4.2: the ledger closes a generated probe for every selector, and one reserved
    # for its workflow is that workflow's alone (its pin names it here).
    from learnloop.followup_serve.identity import door_sets

    closed_generated, reserved_generated = door_sets(repository)
    used_item_ids |= closed_generated | (reserved_generated - ({reserved_for} if reserved_for else set()))
    used_surfaces: set[str] = set()
    observed_family_counts: dict[str, int] = {}
    for row in repository.probe_observations_for_episode(episode.id):
        item_id = str(row["practice_item_id"])
        used_item_ids.add(item_id)
        observed_item = vault.practice_items.get(item_id)
        if observed_item is not None:
            used_surfaces.add(surface_group_id(observed_item))
        family_id = row.get("probe_family_template_id")
        if family_id:
            observed_family_counts[str(family_id)] = observed_family_counts.get(str(family_id), 0) + 1
    # Never-before-seen rule (owner design intent): a probe measures
    # understanding only on a fresh surface — an item the learner has already
    # answered in ANY administration (ordinary practice, exam, or a past
    # episode), or a near-clone in an attempted item's surface group, would
    # conflate memorization of the question with the capability under test.
    # This widens the §5.4 within-episode exposure rule to the whole attempt
    # history: familiarity DISCOUNTS ordinary-practice priority, but for probe
    # candidacy it is a hard exclusion. The scheduler annotates the exclusion
    # (`probe_surface_repeat_excluded`) so it never fails silently.
    attempted_ids, attempted_surfaces = administered_surface_exclusions(vault, repository)
    used_item_ids |= attempted_ids
    used_surfaces |= attempted_surfaces

    resolved: list[tuple[PracticeItem, CompiledInstrument, dict[str, str]]] = []
    for item in vault.practice_items.values():
        if item.status != "active":
            continue
        if item.learning_object_id != episode.learning_object_id:
            continue
        if item.id in staged_owned_item_ids:
            continue
        if item.id in used_item_ids:
            continue
        if surface_group_id(item) in used_surfaces:
            continue
        state = item_states.get(item.id)
        if state is not None and not state.active:
            continue
        # Meas §3.A2/§3.A3: an item whose stimulus the surface cannot render is
        # not administrable. A probe is the worst place to miss this — its
        # outcome updates a hypothesis posterior, so serving an unanswerable
        # instrument does not merely waste an administration, it moves belief
        # toward the hypothesis whose predicted failure the learner was
        # structurally unable to avoid.
        if unservable_reason(item) is not None:
            continue
        instrument_and_map = resolve_instrument(vault, repository, item, hypothesis_set)
        if instrument_and_map is None:
            continue
        resolved.append((item, *instrument_and_map))

    episode_config = vault.config.probe.episode
    # §7.4 held-out target set: the episode's other eligible instruments,
    # deterministic order, capped. Predictive EIG becomes the primary objective
    # only when this set is adequate; otherwise hypothesis EIG ranks.
    resolved.sort(key=lambda entry: entry[0].id)
    target_pool = [
        (instrument, slot_map) for _item, instrument, slot_map in resolved
    ][: episode_config.predictive_target_cap + 1]

    results: list[EligibleInstrument] = []
    for item, instrument, slot_map in resolved:
        eig = instrument_expected_information_gain(belief, instrument, slot_map)
        targets = [
            (target_instrument, target_slot_map)
            for target_instrument, target_slot_map in target_pool
            if target_instrument is not instrument
        ][: episode_config.predictive_target_cap]
        predictive = instrument_predictive_information_gain(belief, instrument, slot_map, targets)
        predictive_adequate = (
            episode_config.predictive_selection_enabled
            and predictive.target_count >= episode_config.predictive_target_minimum
        )
        rate = information_rate(
            predictive.eig_nats,
            instrument.expected_seconds,
            overhead_seconds=episode_config.selection_overhead_seconds,
        )
        # Checkpoint 5.2: a family that already produced an observation this
        # episode is likely redundant with what was measured; each prior
        # observation multiplies the ranking score by the configured penalty.
        # Logged as its own component — the EIG values stay unpenalized.
        family_id = instrument.family_template_id
        prior_observations = observed_family_counts.get(str(family_id), 0) if family_id else 0
        penalty = vault.config.probe.block.family_redundancy_penalty ** prior_observations
        results.append(
            EligibleInstrument(
                item=item,
                instrument=instrument,
                slot_map=slot_map,
                expected_information_gain=eig,
                predictive_eig=predictive.eig_nats,
                predictive_prior_entropy=predictive.prior_predictive_entropy,
                predictive_target_count=predictive.target_count,
                predictive_information_rate=rate,
                selection_objective="predictive_eig" if predictive_adequate else "hypothesis_eig",
                redundancy_penalty=penalty,
                predictive_targets=tuple((target, dict(target_map)) for target, target_map in targets),
                surface_group=surface_group_id(item),
            )
        )
    # §7.5: within the feasible set, predictive candidates rank by information
    # per expected second; hypothesis-EIG fallback candidates rank below any
    # adequate predictive candidate only by their own objective. The redundancy
    # penalty scales the ranking score, never the logged EIG.
    results.sort(
        key=lambda entry: (
            -(
                entry.predictive_information_rate * entry.redundancy_penalty
                if entry.selection_objective == "predictive_eig"
                else 0.0
            ),
            -entry.expected_information_gain * entry.redundancy_penalty,
            entry.item.id,
        )
    )
    return results


def resolve_instrument(
    vault: LoadedVault,
    repository: Repository,
    item: PracticeItem,
    hypothesis_set: HypothesisSet,
) -> tuple[CompiledInstrument, dict[str, str]] | None:
    """The executable instrument binding this item to the locked set, if any."""

    labels = [hypothesis.label for hypothesis in hypothesis_set.hypotheses]
    for link in repository.probe_item_family_links(item.id):
        card_record = repository.probe_instrument_card(link.instrument_card_id, link.instrument_card_version)
        if card_record is None or card_record.retired_at is not None:
            continue
        family_record = repository.probe_family_template(
            card_record.probe_family_template_id, card_record.probe_family_template_version
        )
        if family_record is None or family_record.status not in ("provisional", "trusted"):
            continue
        template = ProbeFamilyTemplate.from_dict(family_record.template)
        card = InstrumentCard.from_dict(card_record.card)
        # §9.7 hierarchical read path: the item's rows are the family posterior
        # (keyed by the same grader_version the write path records under) plus
        # the item's own residual counts, shrunk strongly toward the family.
        counts = shrunk_item_calibration_counts(
            repository,
            template.id,
            template.version,
            practice_item_id=item.id,
            grader_version=template.grader_policy,
            item_shrinkage_pseudo_count=vault.config.probe.hierarchy.item_shrinkage_pseudo_count,
        )
        instrument = validate_and_compile_card(card, template, calibration_counts=counts)
        slot_map = map_episode_labels_to_slots(instrument, labels, bindings=card.bindings)
        if slot_map is not None:
            return instrument, slot_map

    fallback = compile_fallback_instrument(vault, repository, item, hypothesis_set)
    if fallback is not None:
        return fallback, {label: label for label in labels}
    return None


def _resolved_slot_map_from_snapshot(
    snapshot: Mapping[str, Any],
    instrument: CompiledInstrument,
    labels: list[str],
) -> dict[str, str] | None:
    """Return the frozen selection-time label mapping for this presentation.

    Presentations created before the resolved map was persisted retain the
    legacy reconstruction fallback. New presentations never reinterpret card
    bindings during submission or replay.
    """

    if "resolved_slot_map" in snapshot:
        frozen = snapshot.get("resolved_slot_map")
        if not isinstance(frozen, Mapping):
            return None
        slot_map = {
            str(label): str(slot)
            for label, slot in frozen.items()
            if str(label) in labels and str(slot) in instrument.rows
        }
        if all(label in slot_map for label in labels):
            return slot_map
        return None
    return map_episode_labels_to_slots(instrument, labels) or {
        label: label for label in labels if label in instrument.rows
    }


def compile_fallback_instrument(
    vault: LoadedVault,
    repository: Repository,
    item: PracticeItem,
    hypothesis_set: HypothesisSet,
) -> CompiledInstrument | None:
    """Legacy fallback instrument (§7.2): registry discrimination + IRT model.

    Only items that discriminate at least one registry misconception in the
    locked set qualify — the fire channel is what separates hypotheses beyond
    marginal difficulty. Provenance is explicitly ``legacy_fallback``.
    """

    rubric = vault.rubric_for_item(item)
    discrimination, discriminated_ids = item_registry_discrimination(
        repository, vault, item, rubric, hypothesis_set
    )
    if not discriminated_ids:
        return None
    fire_channel = sorted(discriminated_ids)[0]
    row_data = discrimination.get(fire_channel)
    sensitivity = row_data.sensitivity_mean if row_data is not None else 0.6
    specificity = row_data.specificity_mean if row_data is not None else 0.9

    item_a, item_b, irt = resolve_item_irt(vault, item)
    context = item_observation_context(item)
    fire_outcome = f"fire:{fire_channel}"
    alphabet = ("low", "mid", "high", fire_outcome)
    rows: dict[str, dict[str, float]] = {}
    for hypothesis in hypothesis_set.hypotheses:
        marginals = generic_bucket_marginals(
            hypothesis.label, context, item_a=item_a, item_b=item_b, irt=irt
        )
        p_fire = sensitivity if hypothesis.misconception_id == fire_channel else 1.0 - specificity
        scale = 1.0 - p_fire
        rows[hypothesis.label] = {
            "low": marginals["low"] * scale,
            "mid": marginals["mid"] * scale,
            "high": marginals["high"] * scale,
            fire_outcome: p_fire,
        }
    return CompiledInstrument(
        outcome_alphabet=alphabet,
        rows=rows,
        pseudo_count=1.0,
        grader_policy="diagnostic_microprobe_v1",
        provenance="legacy_fallback",
        family_template_id=FALLBACK_FAMILY_ID,
        family_template_version=FALLBACK_FAMILY_VERSION,
        target_facets=tuple(str(facet) for facet in item.evidence_facets),
        signature_error_types={fire_outcome: (fire_channel,)},
        expected_seconds=45.0,
    )


# --- Posterior replay (§5.3, Checkpoint 0.1) ----------------------------------------


def episode_posterior(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    *,
    hypothesis_set: HypothesisSet | None = None,
    held_attempt_ids: Iterable[str] = (),
) -> EpisodePosterior | None:
    """Replay the episode's evidence into the locked-set posterior.

    Two channels, one chronological pass:

    - probe observations replay through their presentation's persisted card
      snapshot (the same grader-composed conditionals selection scored with);
    - incidental attempts (no presentation) replay through the generic
      observation model with contamination-damped likelihoods (§5.3).

    Attempts recorded after an intervention boundary (tutoring transition or
    feedback reveal) belong to a post-intervention state segment and never
    update the pre-intervention diagnostic posterior.

    held-grade-evidence F11: an attempt whose grade is held for review (THE
    predicate, ``canonical_projection.held_for_review_attempts``, plus
    ``held_attempt_ids``: the attempt step's in-flight grade, whose blind
    record is not written yet) moves no posterior, through either channel.
    """

    hypothesis_set = hypothesis_set or episode_hypothesis_set(repository, episode)
    if hypothesis_set is None or not hypothesis_set.hypotheses:
        return None
    prior = dict(hypothesis_set.prior)
    posterior = dict(prior)

    intervention_at = _first_intervention_at(repository, episode)
    observation_rows = repository.probe_observations_for_episode(episode.id)
    observations_by_attempt = {row["attempt_id"]: row for row in observation_rows}

    attempts = repository.list_attempts_by_learning_object(episode.learning_object_id)
    from learnloop.held_grades import held_attempt_ids as _held_attempt_ids

    held = set(_held_attempt_ids(repository, (attempt.get("id") for attempt in attempts)))
    held.update(str(value) for value in held_attempt_ids)
    qualifying = 0
    total_observations = 0
    entered = parse_utc(episode.entered_at)
    episode_config = vault.config.probe.episode
    for attempt in attempts:
        created = parse_utc(attempt.get("created_at"))
        if entered is not None and created is not None and created < entered:
            continue
        attempt_id = str(attempt.get("id"))
        observation_row = observations_by_attempt.get(attempt_id)
        if observation_row is not None:
            observation = observation_row["observation"]
            total_observations += 1
            if observation.eligible_for_completion and attempt_id not in held:
                qualifying += 1
            if not observation.updates_belief or attempt_id in held:
                continue
            likelihoods = _observation_likelihoods_from_row(vault, repository, episode, attempt, observation_row)
            if likelihoods is not None:
                weight = (
                    float(observation.independent_evidence_discount)
                    if observation.independent_evidence_discount is not None
                    else 1.0
                )
                posterior = _bayes_update(
                    posterior,
                    likelihoods,
                    weight=weight,
                    prior_for_marginal=posterior,
                )
            continue
        if attempt.get("probe_presentation_id"):
            presentation = repository.probe_presentation(
                str(attempt["probe_presentation_id"])
            )
            if presentation is not None and presentation.status in (
                "selected",
                "served",
                "submitted",
            ):
                # While recording an accepted observation the attempt already
                # exists and its presentation may already be consumed, but the
                # observation row does not yet. Exclude that in-flight response
                # from posterior_before instead of counting it once as generic
                # incidental evidence and again through the instrument.
                continue
            # A diagnostic attempt whose presentation was explicitly ended
            # without an observation (for example an unapproved grader) falls
            # through as damped belief-only incidental evidence.
        if intervention_at is not None and created is not None and created >= intervention_at:
            continue
        if attempt_id in held:
            continue
        likelihoods = _incidental_likelihoods(vault, repository, attempt, hypothesis_set)
        if likelihoods is None:
            continue
        weight = 1.0
        if int(attempt.get("hints_used") or 0) > 0:
            weight = episode_config.hinted_evidence_weight
        if attempt.get("attempt_type") in ("exam_attempt", "exam_evidence"):
            weight = min(weight, episode_config.hinted_evidence_weight)
        posterior = _bayes_update(posterior, likelihoods, weight=weight, prior_for_marginal=posterior)

    return EpisodePosterior(
        hypothesis_set=hypothesis_set,
        prior=prior,
        posterior=posterior,
        qualifying_observations=qualifying,
        total_observations=total_observations,
        entropy=_entropy(posterior),
    )


def _first_intervention_at(repository: Repository, episode: ProbeEpisodeRecord) -> Any:
    for segment in repository.state_segments_for_learning_object(episode.learning_object_id):
        if segment.probe_episode_id != episode.id:
            continue
        if segment.reason in ("tutoring_transition", "feedback_reveal"):
            return parse_utc(segment.created_at)
    return None


def _observation_likelihoods_from_row(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    attempt: Mapping[str, Any],
    observation_row: Mapping[str, Any],
) -> dict[str, float] | None:
    snapshot = None
    presentation = repository.probe_presentation(str(observation_row["presentation_id"]))
    if presentation is not None:
        snapshot = presentation.instrument_card_snapshot
    if snapshot is None:
        return None
    instrument = CompiledInstrument.from_snapshot(snapshot)
    hypothesis_set = episode_hypothesis_set(repository, episode)
    if hypothesis_set is None:
        return None
    labels = [hypothesis.label for hypothesis in hypothesis_set.hypotheses]
    slot_map = _resolved_slot_map_from_snapshot(snapshot, instrument, labels)
    if slot_map is None:
        return None
    observation = observation_row["observation"]
    outcome = str((observation.grader_channel or {}).get("observed_outcome") or "")
    if not outcome:
        # Backward-compatible replay for observations written before the
        # classified outcome became part of the authoritative observation.
        outcome = classify_outcome(
            instrument,
            rubric_score=attempt.get("rubric_score"),
            max_points=_item_max_points(vault, str(attempt.get("practice_item_id") or "")),
            attempt_type=str(attempt.get("attempt_type") or ""),
            fired_error_types=_fired_error_types(repository, str(attempt.get("id"))),
        )
    return instrument_observation_likelihoods(instrument, slot_map, outcome)


def _fired_error_types(repository: Repository, attempt_id: str) -> list[str]:
    fired: list[str] = []
    for event in repository.error_events_for_attempt(attempt_id):
        error_type = event.get("error_type")
        if error_type:
            fired.append(str(error_type))
        misconception_id = event.get("misconception_id")
        if misconception_id:
            fired.append(str(misconception_id))
    return fired


def _item_max_points(vault: LoadedVault, practice_item_id: str) -> int:
    item = vault.practice_items.get(practice_item_id)
    if item is None:
        return 4
    rubric = vault.rubric_for_item(item)
    return rubric.max_points if rubric is not None else 4


def _incidental_likelihoods(
    vault: LoadedVault,
    repository: Repository,
    attempt: Mapping[str, Any],
    hypothesis_set: HypothesisSet,
) -> dict[str, float] | None:
    item = vault.practice_items.get(str(attempt.get("practice_item_id")))
    if item is None:
        return None
    item_a, item_b, irt = resolve_item_irt(vault, item)
    context = item_observation_context(item)
    rubric = vault.rubric_for_item(item)
    bucket = score_bucket(
        int(attempt.get("rubric_score") or 0),
        rubric.max_points if rubric is not None else 4,
    )
    likelihoods: dict[str, float] = {}
    for hypothesis in hypothesis_set.hypotheses:
        marginals = generic_bucket_marginals(
            hypothesis.label, context, item_a=item_a, item_b=item_b, irt=irt
        )
        likelihoods[hypothesis.label] = marginals.get(bucket, 0.0)
    return likelihoods


def _bayes_update(
    posterior: dict[str, float],
    likelihoods: Mapping[str, float],
    *,
    weight: float = 1.0,
    prior_for_marginal: Mapping[str, float] | None = None,
) -> dict[str, float]:
    """Weighted Bayes step: ``L_w = w·L + (1−w)·marginal`` dampens partially
    trusted evidence toward the mixture marginal (no update at w=0)."""

    if weight < 1.0:
        reference = prior_for_marginal or posterior
        marginal = sum(reference.get(label, 0.0) * likelihoods.get(label, 0.0) for label in posterior)
        likelihoods = {
            label: weight * likelihoods.get(label, 0.0) + (1.0 - weight) * marginal for label in posterior
        }
    updated = {label: posterior[label] * likelihoods.get(label, 0.0) for label in posterior}
    total = sum(updated.values())
    if total <= 0:
        return posterior
    return {label: value / total for label, value in updated.items()}

"""Committed diagnostic presentations and the gates that admit them.

A presentation assigns an eligible instrument's item to an episode and segment.
Committing fixes the card, posterior, entropy, selection policy and components
before the item is returned; forecasts retain the selection-time decision.
Answer-disclosure eligibility can refuse both commitment and serving.
Session observation caps, the onboarding ceiling and the value-of-information
gate can refuse to serve the next probe item. Submission validation checks the
presentation's item, episode, segment, expiry and consumption state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.repositories import ProbePresentationRecord, Repository
from learnloop.db.stores.probes import ProbeEpisodeRecord
from learnloop.diagnosis.probe_completion import robust_gate_counterfactual
from learnloop.diagnosis.probe_episodes import (
    EligibleInstrument,
    _entropy,
    eligible_instruments,
    episode_hypothesis_set,
    episode_posterior,
    effective_qualifying_total,
    qualifying_observation_count,
    session_qualifying_total,
)
from learnloop.diagnosis.probe_families import (
    SELECTION_POLICY_VERSION,
    instrument_expected_information_gain,
)
from learnloop.vault.models import LoadedVault


def shadow_selection_rankings(
    candidates: list[EligibleInstrument], *, top_k: int = 3
) -> dict[str, list[str]]:
    """Alternative selection-policy rankings for shadow logging (§13.3).

    Log-only: the executed policy stays whatever ranked the slate; these
    rankings ride along on the committed presentation so held-out prediction
    can later compare policies. Never combined into the live objective.
    """

    def ranked(key) -> list[str]:
        return [entry.item.id for entry in sorted(candidates, key=key)][:top_k]

    return {
        # The production default: predictive information per expected second,
        # hypothesis EIG as fallback (§7.5), redundancy-penalized.
        "predictive_rate": ranked(
            lambda entry: (
                -(
                    entry.predictive_information_rate * entry.redundancy_penalty
                    if entry.selection_objective == "predictive_eig"
                    else 0.0
                ),
                -entry.expected_information_gain * entry.redundancy_penalty,
                entry.item.id,
            )
        ),
        # Pure hypothesis EIG, ignoring time cost and predictive targets.
        "hypothesis_eig": ranked(
            lambda entry: (-entry.expected_information_gain, entry.item.id)
        ),
        # Raw predictive EIG without the time denominator.
        "predictive_eig": ranked(lambda entry: (-entry.predictive_eig, entry.item.id)),
    }


class RoutineDisplayCovered(Exception):
    """A probe or placement presentation refused: the item's answer was shown,
    so it cannot test the learner (the one eligibility decision,
    ``serve_eligibility.decide(..., PROBE)``). Either a routine display still
    covers it (UX Phase 4 round 6; time alone clears it, within D + G), or
    submit would prime an answer to it (a non-routine reveal since its last
    attempt; only an attempt absorbs it). The name is kept from round 6."""

    def __init__(self, practice_item_id: str, *, decision: object | None = None) -> None:
        super().__init__(f"{practice_item_id}: its answer was shown, so it cannot test the learner yet")
        self.practice_item_id = practice_item_id
        self.decision = decision


#: Why a probe was not administered: its item's answer was shown (the causal
#: offer and ``get_probe_contract``).
PROBE_ITEM_ANSWER_SHOWN = "probe_item_answer_shown"


def probe_eligibility(repository: Repository, practice_item_id: str, *, clock: Clock | None = None):
    """The one eligibility decision for a probe or placement presentation of
    the item now (``serve_eligibility``, request ``PROBE``). The successor's
    reading (``mvp-0.27``), which the guards below ask."""

    from learnloop import serve_eligibility

    inputs = serve_eligibility.gather(
        repository, practice_item_id=practice_item_id, learning_object_id=None, at=utc_now_iso(clock),
    )
    return serve_eligibility.decide(inputs, serve_eligibility.PROBE)


def routine_display_covers_item(
    repository: Repository,
    practice_item_id: str,
    *,
    clock: Clock | None = None,
) -> bool:
    """Was the item's answer shown, so that no probe may test it now? The name
    is kept from round 6; the question is the one eligibility decision's: a
    routine display covering it, or a reveal submit would count."""

    return not probe_eligibility(repository, practice_item_id, clock=clock).serves


def refuse_routine_display_covered(
    repository: Repository,
    practice_item_id: str,
    *,
    clock: Clock | None = None,
) -> None:
    """Raise :class:`RoutineDisplayCovered` when a probe of the item cannot
    test the learner now (the one eligibility decision refuses it): the one
    guard every presentation commit (and serve) passes through."""

    from learnloop import serve_eligibility

    decision = probe_eligibility(repository, practice_item_id, clock=clock)
    if not decision.serves:
        serve_eligibility.log_decision(decision, path="probe_commit")
        raise RoutineDisplayCovered(practice_item_id, decision=decision)


def commit_presentation(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    eligible: EligibleInstrument,
    *,
    scheduler_candidate_id: str | None = None,
    extra_selection_components: Mapping[str, Any] | None = None,
    candidates: list[EligibleInstrument] | None = None,
    supersede_active: bool = True,
    clock: Clock | None = None,
) -> ProbePresentationRecord:
    """Durably commit the selection before the item is returned to the client.

    Persists the selection-time posterior/entropy snapshot and the resolved
    card snapshot (compiled values + pseudo-counts) the observation will replay
    against (§9.3). Any previously active presentation for the episode is
    superseded (`ended`/`abandoned`) unless ``supersede_active`` is False
    (precommitted block siblings, Checkpoint 5.3). When the full candidate
    slate is supplied, shadow-policy rankings are logged onto the presentation
    (§13.3, Checkpoint 5.1).

    An item whose answer a routine display still covers is never committed
    (UX Phase 4 rounds 6 and 7): the payload builder refuses it
    (:class:`RoutineDisplayCovered`) before anything is written.
    """

    payload = presentation_commit_payload(
        vault,
        repository,
        episode,
        eligible,
        scheduler_candidate_id=scheduler_candidate_id,
        extra_selection_components=extra_selection_components,
        candidates=candidates,
        clock=clock,
    )

    if supersede_active:
        previous = repository.active_probe_presentation(episode.id)
        if previous is not None:
            repository.end_probe_presentation(previous.id, end_reason="abandoned", clock=clock)

    presentation_id = repository.insert_probe_presentation(**payload, clock=clock)
    record = repository.probe_presentation(presentation_id)
    assert record is not None
    record_presentation_forecast(
        vault,
        repository,
        record,
        learning_object_id=episode.learning_object_id,
        candidate_count=len(candidates) if candidates is not None else None,
        clock=clock,
    )
    return record


def record_presentation_forecast(
    vault: LoadedVault,
    repository: Repository,
    presentation: ProbePresentationRecord,
    *,
    learning_object_id: str | None = None,
    candidate_count: int | None = None,
    clock: Clock | None = None,
) -> None:
    """EVSI calibration Part B: log the forecast this probe selection ran on.

    Logging only (``voi_forecasts``): it never changes the presentation, and
    a failure to log is swallowed. Idempotent per presentation.

    At mvp-0.21 the presentation also carries the value-of-information
    continue decision that admitted it (``selection_components.voi_stopping``,
    every commit door: the scheduler's, the sidecar's and the TUI's); it is
    logged here too, once per presentation, at its own site
    (``probe_episode_value_decision``), describing the committed check with
    router R1's exploration marker when the seeded exploration drew it."""

    from learnloop.diagnosis.voi_forecasting import (
        record_probe_presentation_forecast,
        record_value_decision_forecast,
    )

    record_probe_presentation_forecast(
        vault,
        repository,
        presentation,
        learning_object_id=learning_object_id,
        candidate_count=candidate_count,
        clock=clock,
    )
    components = dict(presentation.selection_components or {})
    value_decision = components.get("voi_stopping")
    if isinstance(value_decision, Mapping):
        record_value_decision_forecast(
            vault,
            repository,
            value_decision,
            receipt_key=f"probe_episode_value_decision:{presentation.id}",
            scheduler_exploration=components.get("scheduler_exploration"),
            clock=clock,
            decision_ref=presentation.id,
            probe_episode_id=presentation.probe_episode_id,
            presentation_id=presentation.id,
            chosen_practice_item_id=presentation.practice_item_id,
            scheduler_candidate_id=presentation.scheduler_candidate_id,
        )


def presentation_commit_payload(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    eligible: EligibleInstrument,
    *,
    scheduler_candidate_id: str | None = None,
    extra_selection_components: Mapping[str, Any] | None = None,
    candidates: list[EligibleInstrument] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Build the frozen presentation row before its owning transaction.

    The routine scheduler passes this payload into ``record_scheduler_slate``
    so the candidate and presentation are committed atomically. Dialogue and
    direct/TUI selections use ``commit_presentation`` with the same builder.

    So this is the one guard every new probe presentation row passes (UX
    Phase 4 round 7): an item whose answer a routine display still covers
    raises :class:`RoutineDisplayCovered` before any row exists.
    """

    refuse_routine_display_covered(repository, eligible.item.id, clock=clock)
    if episode.status != "in_progress":
        raise ValueError(f"episode {episode.id} is {episode.status}; cannot commit a presentation")
    if episode.active_state_segment_id is None:
        raise ValueError(f"episode {episode.id} has no active state segment")

    posterior = episode_posterior(vault, repository, episode)
    belief = posterior.posterior if posterior is not None else {}
    eig = instrument_expected_information_gain(belief, eligible.instrument, eligible.slot_map)
    expires_at = None
    ttl_minutes = vault.config.probe.episode.presentation_ttl_minutes
    causal_pin = (extra_selection_components or {}).get("causal_probe")
    if isinstance(causal_pin, Mapping) and causal_pin.get("followup_workflow_id"):
        # FG1 §4.2: a follow-up's probe waits for its workflow, a wait included. Abandonment
        # or a skip closes it, not a clock, or a submission could fail after its one burn.
        ttl_minutes = 0
    if ttl_minutes > 0:
        from datetime import timedelta

        now_dt = parse_utc(utc_now_iso(clock))
        if now_dt is not None:
            expires_at = (
                (now_dt + timedelta(minutes=ttl_minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")
            )

    snapshot = eligible.instrument.snapshot()
    # The card binding is presentation-specific: two cards compiled from the
    # same family can map a concrete episode label to different abstract slots.
    # Freeze the exact map used by EIG so grading and replay cannot reinterpret
    # it later (§7.2 selection/replay identity).
    snapshot["resolved_slot_map"] = dict(eligible.slot_map)
    labels = sorted(belief, key=lambda label: -belief.get(label, 0.0))
    target_pairs = [[labels[i], labels[j]] for i in range(min(2, len(labels))) for j in range(i + 1, min(3, len(labels)))]
    selection_components = dict(eligible.selection_components(), **(extra_selection_components or {}))
    shadow_config = vault.config.probe.shadow
    if candidates and shadow_config.enabled and len(candidates) > 1:
        selection_components["shadow_rankings"] = shadow_selection_rankings(
            candidates, top_k=shadow_config.top_k
        )
    # mvp-0.8 robust cutover (§4.2, §1.5): snapshot the pinned channel + the
    # decision-time robust EIG-per-second product for the served candidate so the
    # historical decision is byte-stable without re-running the ensemble on replay.
    robust_pin = _robust_channel_pin(repository, episode, eligible, belief)
    if robust_pin is not None:
        selection_components["channel_pin"] = robust_pin
    return {
        "probe_episode_id": episode.id,
        "practice_item_id": eligible.item.id,
        "state_segment_id": episode.active_state_segment_id,
        "scheduler_candidate_id": scheduler_candidate_id,
        "probe_family_template_id": eligible.instrument.family_template_id,
        "probe_family_template_version": eligible.instrument.family_template_version,
        "instrument_card_id": eligible.instrument.card_id,
        "instrument_card_version": eligible.instrument.card_version,
        "instrument_card_snapshot": snapshot,
        "target_hypothesis_pairs": target_pairs,
        "target_facets": list(eligible.instrument.target_facets),
        "posterior_at_selection": belief,
        "entropy_at_selection": _entropy(belief),
        "expected_information_gain": eig,
        "selection_policy_version": SELECTION_POLICY_VERSION,
        "selection_components": selection_components,
        "expires_at": expires_at,
    }


def _robust_channel_pin(
    repository: Repository,
    episode: ProbeEpisodeRecord,
    eligible: EligibleInstrument,
    belief: Mapping[str, float],
) -> dict[str, Any] | None:
    """The mvp-0.8 decision-time channel pin + robust product for the chosen
    candidate (§1.5/§2.1). Returns None for legacy episodes (no pinned channel)."""

    if episode.calibration_model_hash is None:
        return None
    from learnloop.diagnosis.probe_robust import (
        instrument_ensemble,
        load_pinned_channel,
    )
    from learnloop.diagnosis.robust_composition import robust_eig_per_second

    channel = load_pinned_channel(repository, episode.calibration_model_hash)
    if channel is None:
        return None
    ensemble, dch = instrument_ensemble(
        channel, eligible.instrument, eligible.slot_map, dict(belief), episode_id=episode.id
    )
    expected_seconds = max(float(eligible.instrument.expected_seconds), 1e-6)
    return {
        "calibration_model_id": channel.model_id,
        "calibration_model_hash": channel.model_hash,
        "mapping_version": channel.mapping_version,
        "decision_context_hash": dch,
        "ensemble_seed": ensemble.seed,
        "robust_eig_per_second": robust_eig_per_second(ensemble, dict(belief), expected_seconds),
        "projection_algorithm_version": episode.algorithm_version,
    }


#: Why a learner-lane pin was not shown: its learner refused after it was pinned (:func:`learner_refused_pin`).
LEARNER_REFUSED_PROBE = "learner_refused_probe"


class LearnerRefusedPin(Exception):
    """The probe router's learner lane: the learner said "Not now", "Teach me now" or no more diagnostics after
    accepting the quick check, so its pin was retired before it was ever shown."""

    def __init__(self, presentation_id: str, preference: str) -> None:
        super().__init__(f"{presentation_id}: the learner refused the quick check after it was pinned ({preference})")
        self.presentation_id = presentation_id
        self.preference = preference


def learner_refused_pin(repository: Repository, presentation: ProbePresentationRecord) -> str | None:
    """The refusal that retires a learner-lane router pin before its first display, or None: the learner's current
    preference on the pin's factor, read with the scope the status reads it (the factor, its learning object, the
    pin's session), when it refuses. Acceptance read the same preference and found none, so a refusing one came after
    the pin. Only a pin still unshown (``selected``) that names a router decision, no follow-up workflow and no
    continuation is the learner lane's: the automatic lane's pin is its own decision's, and a shown probe is being answered."""

    from learnloop.diagnosis.probe_facts import REFUSING_PREFERENCES
    from learnloop.diagnosis.probe_hard_stops import learner_preference

    if presentation.status != "selected":
        return None
    pin = (presentation.selection_components or {}).get("causal_probe")
    if not isinstance(pin, Mapping) or not pin.get("router_decision_id") or pin.get("followup_workflow_id"):
        return None
    if pin.get("continuation_of_episode"):
        # The router's continuation of an episode the learner is already answering: the offer's refusal does not
        # reach it (the episode ends on its evidence, its count or the router's stop).
        return None
    episode = repository.probe_episode(presentation.probe_episode_id)
    preference = learner_preference(
        repository, factor_id=str(pin.get("causal_factor_id") or "") or None,
        learning_object_id=episode.learning_object_id if episode is not None else None,
        session_id=pin.get("session_id"))
    return preference if preference in REFUSING_PREFERENCES else None


class ProtectedInstrument(Exception):
    """A committed presentation's item became exam material the session serve refuses (reserved for a goal's
    held-out exam, or made from held-out material) after it was committed: ended unshown, never served."""

    def __init__(self, presentation_id: str, practice_item_id: str, reason: str) -> None:
        super().__init__(f"{presentation_id}: {practice_item_id} is protected exam material ({reason})")
        self.presentation_id = presentation_id
        self.practice_item_id = practice_item_id
        self.reason = reason


def serve_presentation(
    repository: Repository,
    presentation_id: str,
    *,
    vault: LoadedVault,
    clock: Clock | None = None,
) -> None:
    """Mark a committed presentation served: the administration itself, and
    the only path to ``served``. A presentation whose item the session serve
    now refuses as exam material (``probe_episodes.item_refusals``: reserved for
    a held-out exam, or made from held-out material) is ended (``invalidated``)
    instead, and :class:`ProtectedInstrument` raised: a router pin that became
    protected is retired, so its episode's next observation is decided again. A
    presentation committed before its item's answer was shown on a routine
    display that still covers now is ended (``invalidated``) instead, and
    :class:`RoutineDisplayCovered` raised (UX Phase 4 round 7). A learner-lane
    pin its learner refused after pinning is ended (``abandoned``) instead, and
    :class:`LearnerRefusedPin` raised."""

    from learnloop.diagnosis.probe_episodes import PROBE_ITEM_PROTECTED, item_refusals

    presentation = repository.probe_presentation(presentation_id)
    if presentation is not None:
        item = vault.practice_items.get(str(presentation.practice_item_id))
        if item is not None and item_refusals(vault, repository, [item]).get(item.id) == PROBE_ITEM_PROTECTED:
            repository.end_probe_presentation(presentation_id, end_reason="invalidated", clock=clock)
            raise ProtectedInstrument(presentation_id, item.id, PROBE_ITEM_PROTECTED)
        refused = learner_refused_pin(repository, presentation)
        if refused is not None:
            repository.end_probe_presentation(presentation_id, end_reason="abandoned", clock=clock)
            raise LearnerRefusedPin(presentation_id, refused)
        try:
            refuse_routine_display_covered(repository, presentation.practice_item_id, clock=clock)
        except RoutineDisplayCovered:
            repository.end_probe_presentation(presentation_id, end_reason="invalidated", clock=clock)
            raise
    repository.mark_probe_presentation_served(presentation_id, clock=clock)


def probe_serving_block_reason(
    vault: LoadedVault,
    repository: Repository,
    *,
    session_id: str | None = None,
    cap_lifted: bool = False,
) -> str | None:
    """The §5.9 orchestration gate shared by every serving surface.

    Returns the blocking reason (``session_cap_reached`` when the routine
    session's qualifying-observation cap is spent, ``onboarding_practice_ceiling``
    while a fresh vault has produced no ordinary practice yet) or None when a
    qualifying observation may be served. An active, in-budget calibration
    session lifts both (``cap_lifted`` — an explicit learner opt-in).
    """

    if cap_lifted:
        return None
    from learnloop.diagnosis.voi_stopping import SITE_PROBE_EPISODE, voi_stopping_active

    cap = vault.config.probe.episode.session_qualifying_observation_cap
    # mvp-0.21 (voi_stopping): the session cap is lifted onto value of
    # information; each episode's next observation is valued instead
    # (``probe_value_block_reason``). Off, the count cap serves exactly.
    if session_id is not None and cap > 0 and not voi_stopping_active(vault.config, SITE_PROBE_EPISODE):
        if effective_qualifying_total(vault, repository, session_id=session_id) >= cap:
            return "session_cap_reached"
    ceiling = vault.config.probe.episode.onboarding_practice_ceiling_observations
    if ceiling > 0:
        if (
            repository.ordinary_practice_attempt_count() == 0
            and effective_qualifying_total(vault, repository) >= ceiling
        ):
            return "onboarding_practice_ceiling"
    return None


def probe_value_block_reason(
    vault: LoadedVault,
    repository: Repository,
    episode: "ProbeEpisodeRecord",
    practice_item_id: str,
    *,
    session_id: str | None = None,
    cap_lifted: bool = False,
) -> tuple[str | None, dict[str, Any] | None]:
    """mvp-0.21 (voi_stopping, site ``probe_episode``): may this item be the
    episode's next observation?

    Returns ``(reason, decision)``: ``reason`` is
    ``"value_below_minutes_cost"`` when the item's value of information does
    not pay for its minutes (``None`` otherwise), and ``decision`` is the
    logged forecast. ``(None, None)`` below mvp-0.21, with the site off, under
    a calibration session's lift, or when the item is not an eligible
    instrument (the caller's own path decides that).
    """

    from learnloop.diagnosis import voi_stopping as voi

    if cap_lifted or not voi.voi_stopping_active(vault.config, voi.SITE_PROBE_EPISODE):
        return None, None
    from learnloop.diagnosis.probe_episodes import router_selected_episode

    if router_selected_episode(vault, repository, episode):
        # The probe router's tag: the router selected this episode's probe; no value decision vetoes it again.
        return None, None
    hypothesis_set = episode_hypothesis_set(repository, episode)
    if hypothesis_set is None:
        return None, None
    live = episode_posterior(vault, repository, episode, hypothesis_set=hypothesis_set)
    if live is None:
        return None, None
    candidates = eligible_instruments(
        vault, repository, episode, hypothesis_set=hypothesis_set, posterior=live.posterior
    )
    if not any(entry.item.id == practice_item_id for entry in candidates):
        return None, None
    decision = voi.probe_episode_decision(
        voi.VoiContext(vault, repository), episode, candidates, live.posterior, session_id=session_id,
        qualifying_observations=qualifying_observation_count(vault, repository, episode.id),
        session_qualifying_observations=session_qualifying_total(vault, repository, session_id),
    )
    if decision.admits(practice_item_id):
        # The item the learner opened is the one this door commits: the
        # receipt carries ITS forecast (``served``), beside value's own pick,
        # and (rank 1) the robust gate's verdict where value outranked it.
        applies, verdict = robust_gate_counterfactual(vault, repository, episode, live.posterior)
        if applies:
            decision = voi.with_robust_gate_counterfactual(decision, verdict)
        return None, decision.as_dict(served_ref=practice_item_id, served_by={"mechanism": "learner_opened_item"})
    return "value_below_minutes_cost", decision.as_dict(subject_ref=practice_item_id)


def commit_item_presentation(
    vault: LoadedVault,
    repository: Repository,
    episode: "ProbeEpisodeRecord",
    item,
    hypothesis_set,
    *,
    extra_selection_components: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
):
    """Commit and serve a presentation for one specific item.

    Uses the live eligible slate so the committed presentation carries real
    §7.3 selection components and §13.3 shadow-policy rankings. An item outside
    that slate is not a diagnostic assignment; it remains ordinary practice.
    """

    from learnloop.diagnosis.probe_episodes import router_selected_episode

    if router_selected_episode(vault, repository, episode):
        # The probe router's tag: a router-owned episode's next observation is the router's decision, committed by
        # it as a pinned presentation (``daily_plan.probe_continuation``); opening an item never commits one.
        return None
    candidates = eligible_instruments(vault, repository, episode, hypothesis_set=hypothesis_set)
    eligible = next((entry for entry in candidates if entry.item.id == item.id), None)
    if eligible is None:
        return None
    try:
        presentation = commit_presentation(
            vault,
            repository,
            episode,
            eligible,
            candidates=candidates or None,
            extra_selection_components=extra_selection_components,
            clock=clock,
        )
        serve_presentation(repository, presentation.id, vault=vault, clock=clock)
    except (RoutineDisplayCovered, ProtectedInstrument):
        # Its answer was just shown: ordinary practice, not a probe (rounds 6, 7). Protected exam material is never
        # selected (``item_refusals``); one protected between the selection and the serve is ended unshown.
        return None
    return presentation


@dataclass(frozen=True)
class PresentationValidation:
    valid: bool
    reason: str | None = None
    presentation: ProbePresentationRecord | None = None
    episode: ProbeEpisodeRecord | None = None


def validate_presentation_for_submission(
    repository: Repository,
    presentation_id: str,
    *,
    practice_item_id: str,
    attempt_id: str | None = None,
    clock: Clock | None = None,
) -> PresentationValidation:
    """§5.4/§5.1 submission validation: active, same episode/item/segment,
    unexpired, unconsumed. Idempotent for a retried submission of the same
    attempt."""

    presentation = repository.probe_presentation(presentation_id)
    if presentation is None:
        return PresentationValidation(False, "unknown_presentation")
    episode = repository.probe_episode(presentation.probe_episode_id)
    if episode is None:
        return PresentationValidation(False, "unknown_episode", presentation)
    if presentation.status == "submitted":
        if attempt_id is not None:
            existing = repository.probe_observation_for_attempt(attempt_id)
            if existing is not None:
                return PresentationValidation(True, "already_submitted", presentation, episode)
        return PresentationValidation(False, "already_consumed", presentation, episode)
    if presentation.status == "ended":
        return PresentationValidation(False, f"ended_{presentation.end_reason}", presentation, episode)
    if presentation.practice_item_id != practice_item_id:
        return PresentationValidation(False, "item_mismatch", presentation, episode)
    if episode.status != "in_progress":
        return PresentationValidation(False, f"episode_{episode.status}", presentation, episode)
    if presentation.state_segment_id != episode.active_state_segment_id:
        return PresentationValidation(False, "stale_state_segment", presentation, episode)
    if presentation.expires_at is not None:
        now = parse_utc(utc_now_iso(clock))
        expires = parse_utc(presentation.expires_at)
        if now is not None and expires is not None and now > expires:
            repository.end_probe_presentation(presentation.id, end_reason="expired", clock=clock)
            return PresentationValidation(False, "expired", presentation, episode)
    return PresentationValidation(True, None, presentation, episode)

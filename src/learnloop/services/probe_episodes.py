"""Adaptive diagnostic episodes (spec_probe_eig_redesign.md §5/§7/§10/§11).

An episode is the first-class measurement unit: a locked hypothesis set, a
sequence of committed presentations, and probe observations whose eligibility
is strictly separated from belief updates. Belief updates use every relevant
attempt (with contamination-adjusted likelihoods); episode budget, coverage,
and stopping are advanced only by qualifying selected observations.

Legacy ``probe_<lo_id>`` phases (services/probes.py, ``lo_probe_state``) are
frozen: they replay through the legacy path keyed by their recorded
``algorithm_version`` and receive no new writes (Checkpoint 0).
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log
import json
from typing import Any, Mapping

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.repositories import (
    ProbeEpisodeRecord,
    ProbePresentationRecord,
    Repository,
)
from learnloop.ids import new_ulid
from learnloop.services.probe_families import (
    APPROVED_DIAGNOSTIC_GRADING_SOURCES,
    SELECTION_POLICY_VERSION,
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
    record_real_observation_counts,
    shrunk_item_calibration_counts,
    validate_and_compile_card,
)
from learnloop.services.probe_hypotheses import (
    H_OTHER,
    build_episode_hypothesis_set,
    generic_bucket_marginals,
    item_observation_context,
    strong_prior_claim,
)
from learnloop.services.probes import (
    HypothesisSet,
    item_registry_discrimination,
    resolve_item_irt,
    score_bucket,
)
from learnloop.services.outcome_schemas import COARSE_RESPONSE_SLUG
from learnloop.services.probe_robust import use_robust_probe
from learnloop.vault.models import LoadedVault, PracticeItem

FALLBACK_FAMILY_ID = "registry_discrimination_fallback"
FALLBACK_FAMILY_VERSION = 1

# Interaction contract during an active diagnostic block (§5.5/§12).
PROBE_ASSISTANCE_RESTRICTIONS = {
    "hints_disabled": True,
    "ask_tutor_disabled": True,
    "worked_example_disabled": True,
    "answer_reveal_disabled": True,
    "feedback_deferred": True,
}


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


def enter_episode(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    trigger: str = "initial",
    origin: str | None = None,
    goal_id: str | None = None,
    clock: Clock | None = None,
    ai_client: object | None = None,
) -> ProbeEpisodeRecord:
    """Open a diagnostic episode with a fresh ULID and locked hypothesis set.

    Idempotent per LO: an already-open episode is returned unchanged. The
    episode enters ``in_progress`` when an eligible instrument exists locally,
    otherwise ``pending_items`` with one deduplicated generation need (§10) —
    which never blocks ordinary practice on the LO.

    ``origin`` records how the episode was launched (e.g.
    ``'overconfidence_list'``, spec §4.3) so analytics can separate adversarial
    selection from drift. It is persisted into the dedicated ``origin`` column
    (migration 059) at creation, so it survives target selection — which
    overwrites ``target_decision_json`` and previously erased the origin.
    """

    existing = repository.open_probe_episode(learning_object_id)
    if existing is not None:
        if (
            existing.status == "pending_items"
            and vault.config.probe.generation.auto_generate_on_entry
        ):
            from learnloop.services.probe_instance_generation import generate_instances_for_episode

            generate_instances_for_episode(
                repository, vault, existing.id, clock=clock, ai_client=ai_client
            )
            return repository.probe_episode(existing.id) or existing
        return existing

    ensure_builtin_families(repository, clock=clock)
    algorithm_version = vault.config.algorithms.algorithm_version
    episode_config = vault.config.probe.episode
    episode_id = new_ulid()
    hypothesis_set = build_episode_hypothesis_set(vault, repository, learning_object_id, clock=clock)
    hypothesis_set_id = repository.insert_hypothesis_set(
        learning_object_id=learning_object_id,
        probe_phase_id=episode_id,
        hypotheses=[hypothesis.as_record() for hypothesis in hypothesis_set.hypotheses],
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
    from learnloop.services.facet_diagnostics import required_facets

    # Pin the exact confirmed terminal-contract version at episode open (§3.4).
    # Ungoal-conditioned probes leave the pin NULL (not a terminal claim).
    target_contract_version_id: str | None = None
    target_support_hash: str | None = None
    if goal_id is not None:
        from learnloop.services.goal_contracts import resolve_head

        head = resolve_head(repository, goal_id)
        if head is not None:
            target_contract_version_id = head.id
            target_support_hash = head.support_hash

    # mvp-0.8 robust cutover (§4.2, invariant 3): resolve + pin the calibration
    # channel at episode open. Both robust selection and the decision-time
    # observed_update consume this pinned model hash. Legacy vaults leave it NULL.
    calibration_model_id: str | None = None
    calibration_model_hash: str | None = None
    probe_mapping_version: str | None = None
    from learnloop.services.probe_robust import resolve_episode_channel, use_robust_probe

    if use_robust_probe(vault):
        channel = resolve_episode_channel(
            repository, learning_object_id=learning_object_id, clock=clock
        )
        calibration_model_id = channel.model_id or None
        calibration_model_hash = channel.model_hash
        probe_mapping_version = channel.mapping_version

    repository.insert_probe_episode(
        episode_id=episode_id,
        learning_object_id=learning_object_id,
        status="pending_items",
        trigger=trigger,
        hypothesis_set_id=hypothesis_set_id,
        active_state_segment_id=None,
        target_decision=None,
        origin=origin,
        algorithm_version=algorithm_version,
        required_facets=sorted(required_facets(vault, learning_object_id, repository)),
        # Purpose-specific minimum: initial/goal placement is a routing
        # conclusion, so one qualifying observation may complete it; the
        # 2-observation breadth contract stays for diagnostic re-entries
        # (misconception / stale-uncertainty triggers), whose conclusions feed
        # stronger claims.
        minimum_independent_observations=(
            episode_config.placement_minimum_observations
            if trigger in ("initial", "goal_diagnostic")
            else episode_config.minimum_independent_observations
        ),
        maximum_observations=episode_config.maximum_observations,
        entered_at=now,
        target_contract_version_id=target_contract_version_id,
        target_support_hash=target_support_hash,
        calibration_model_id=calibration_model_id,
        calibration_model_hash=calibration_model_hash,
        probe_mapping_version=probe_mapping_version,
        clock=clock,
    )
    repository.open_state_segment(
        learning_object_id=learning_object_id,
        probe_episode_id=episode_id,
        reason="episode_entry",
        clock=clock,
    )
    episode = repository.probe_episode(episode_id)
    assert episode is not None
    instruments = eligible_instruments(vault, repository, episode, hypothesis_set=locked)
    if instruments:
        repository.update_probe_episode_status(episode_id, status="in_progress", clock=clock)
    else:
        _record_generation_need(vault, repository, episode, locked, clock=clock)
        if vault.config.probe.generation.auto_generate_on_entry:
            from learnloop.services.probe_instance_generation import generate_instances_for_episode

            generate_instances_for_episode(
                repository, vault, episode_id, clock=clock, ai_client=ai_client
            )
    refreshed = repository.probe_episode(episode_id)
    assert refreshed is not None
    return refreshed


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
    if repository.open_probe_episode(learning_object_id) is not None:
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
    if repository.open_probe_episode(learning_object_id) is not None:
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
    from learnloop.services.probe_instance_generation import applicable_families

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


def eligible_instruments(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    *,
    hypothesis_set: HypothesisSet | None = None,
    posterior: Mapping[str, float] | None = None,
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
    # P4 §14.2 step 3 dual-authority (design §A.2 rule 3): the probe path is an
    # administration surface too. A staged-owned P2 commitment's items are the staged
    # policy's to administer, never the legacy sidecar probe path. Refuse outright when
    # the episode's whole learning object is staged-owned; otherwise drop just the owned
    # items from the eligible slate. Empty exclusion set -> byte-identical legacy behavior
    # for a vault with no ownership rows.
    from learnloop.services import controller_ownership as _ownership

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
    # item of an already-observed surface family — is a disallowed repeat.
    # Family observation counts feed the Checkpoint 5.2 redundancy penalty.
    used_item_ids: set[str] = set()
    used_surfaces: set[str] = set()
    observed_family_counts: dict[str, int] = {}
    for row in repository.probe_observations_for_episode(episode.id):
        item_id = str(row["practice_item_id"])
        used_item_ids.add(item_id)
        observed_item = vault.practice_items.get(item_id)
        if observed_item is not None and observed_item.surface_family:
            used_surfaces.add(observed_item.surface_family)
        family_id = row.get("probe_family_template_id")
        if family_id:
            observed_family_counts[str(family_id)] = observed_family_counts.get(str(family_id), 0) + 1

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
        if item.surface_family and item.surface_family in used_surfaces:
            continue
        state = item_states.get(item.id)
        if state is not None and not state.active:
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


# --- Presentations (§5.1) -----------------------------------------------------------


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
    return record


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
    """

    if episode.status != "in_progress":
        raise ValueError(f"episode {episode.id} is {episode.status}; cannot commit a presentation")
    if episode.active_state_segment_id is None:
        raise ValueError(f"episode {episode.id} has no active state segment")

    posterior = episode_posterior(vault, repository, episode)
    belief = posterior.posterior if posterior is not None else {}
    eig = instrument_expected_information_gain(belief, eligible.instrument, eligible.slot_map)
    expires_at = None
    ttl_minutes = vault.config.probe.episode.presentation_ttl_minutes
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
    from learnloop.services.probe_robust import (
        instrument_ensemble,
        load_pinned_channel,
    )
    from learnloop.services.robust_composition import robust_eig_per_second

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


def serve_presentation(repository: Repository, presentation_id: str, *, clock: Clock | None = None) -> None:
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
    cap = vault.config.probe.episode.session_qualifying_observation_cap
    if session_id is not None and cap > 0:
        if repository.qualifying_probe_observation_count_for_session(session_id) >= cap:
            return "session_cap_reached"
    ceiling = vault.config.probe.episode.onboarding_practice_ceiling_observations
    if ceiling > 0:
        if (
            repository.ordinary_practice_attempt_count() == 0
            and repository.qualifying_probe_observation_count() >= ceiling
        ):
            return "onboarding_practice_ceiling"
    return None


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

    candidates = eligible_instruments(vault, repository, episode, hypothesis_set=hypothesis_set)
    eligible = next((entry for entry in candidates if entry.item.id == item.id), None)
    if eligible is None:
        return None
    presentation = commit_presentation(
        vault,
        repository,
        episode,
        eligible,
        candidates=candidates or None,
        extra_selection_components=extra_selection_components,
        clock=clock,
    )
    serve_presentation(repository, presentation.id, clock=clock)
    return presentation


def plan_precommitted_block(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    *,
    block_size: int | None = None,
    clock: Clock | None = None,
) -> list[ProbePresentationRecord]:
    """Greedy conditional/joint EIG for one precommitted block (Checkpoint 5.3).

    Joint selection applies ONLY here — a block whose items are all committed
    before any answer is observed (§16 test 29). The first pick maximizes EIG
    on the live posterior; each later pick maximizes its EIG in expectation
    over the predicted outcomes of the already-picked instruments (a greedy
    BatchBALD-style step over a truncated branch tree). Sequential selection
    elsewhere keeps conditioning on the observed posterior instead.

    All block presentations are committed transactionally-in-order before the
    first item is served; the presentations carry ``joint_block`` telemetry
    with each pick's conditional EIG.
    """

    block_config = vault.config.probe.block
    size = block_size or vault.config.probe.dialogue.planned_turns
    size = max(2, min(size, block_config.max_block_size))

    candidates = eligible_instruments(vault, repository, episode)
    if not candidates:
        return []
    live = episode_posterior(vault, repository, episode)
    base_posterior = dict(live.posterior) if live is not None else {}
    if not base_posterior:
        return []

    # Branches: (posterior, weight) over predicted outcomes of prior picks.
    branches: list[tuple[dict[str, float], float]] = [(base_posterior, 1.0)]
    picked: list[tuple[EligibleInstrument, float]] = []
    picked_items: set[str] = set()
    picked_surfaces: set[str] = set()
    picked_families: dict[str, int] = {}

    for _position in range(size):
        best: EligibleInstrument | None = None
        best_score = 0.0
        best_conditional = 0.0
        for candidate in candidates:
            if candidate.item.id in picked_items:
                continue
            surface = candidate.item.surface_family
            if surface and surface in picked_surfaces:
                continue
            conditional_eig = sum(
                weight
                * instrument_expected_information_gain(
                    posterior, candidate.instrument, candidate.slot_map
                )
                for posterior, weight in branches
            )
            family_id = str(candidate.instrument.family_template_id or "")
            within_block_penalty = (
                block_config.family_redundancy_penalty ** picked_families.get(family_id, 0)
                if family_id
                else 1.0
            )
            score = conditional_eig * candidate.redundancy_penalty * within_block_penalty
            if best is None or score > best_score or (score == best_score and candidate.item.id < best.item.id):
                best = candidate
                best_score = score
                best_conditional = conditional_eig
        if best is None or best_conditional <= 0.0:
            break
        picked.append((best, best_conditional))
        picked_items.add(best.item.id)
        if best.item.surface_family:
            picked_surfaces.add(best.item.surface_family)
        family_id = str(best.instrument.family_template_id or "")
        if family_id:
            picked_families[family_id] = picked_families.get(family_id, 0) + 1

        # Expand the branch tree over the pick's predicted outcomes, keeping
        # the most probable branches (conditional_branch_cap per branch).
        expanded: list[tuple[dict[str, float], float]] = []
        for posterior, weight in branches:
            outcome_marginals: list[tuple[str, float]] = []
            for outcome in best.instrument.outcome_alphabet:
                likelihoods = instrument_observation_likelihoods(
                    best.instrument, best.slot_map, outcome
                )
                marginal = sum(
                    posterior.get(label, 0.0) * likelihoods.get(label, 0.0) for label in posterior
                )
                if marginal > 0:
                    outcome_marginals.append((outcome, marginal))
            outcome_marginals.sort(key=lambda pair: (-pair[1], pair[0]))
            kept = outcome_marginals[: block_config.conditional_branch_cap]
            kept_total = sum(marginal for _outcome, marginal in kept)
            if kept_total <= 0:
                expanded.append((posterior, weight))
                continue
            for outcome, marginal in kept:
                likelihoods = instrument_observation_likelihoods(
                    best.instrument, best.slot_map, outcome
                )
                expanded.append(
                    (
                        _bayes_update(dict(posterior), likelihoods),
                        weight * marginal / kept_total,
                    )
                )
        # Prune globally so the tree stays bounded across picks.
        expanded.sort(key=lambda pair: -pair[1])
        kept_branches = expanded[: block_config.conditional_branch_cap**2]
        total_weight = sum(weight for _posterior, weight in kept_branches)
        branches = [
            (posterior, weight / total_weight) for posterior, weight in kept_branches
        ] if total_weight > 0 else branches

    presentations: list[ProbePresentationRecord] = []
    for index, (candidate, conditional_eig) in enumerate(picked):
        presentation = commit_presentation(
            vault,
            repository,
            episode,
            candidate,
            candidates=candidates,
            supersede_active=index == 0,
            extra_selection_components={
                "joint_block": True,
                "block_index": index,
                "block_size": len(picked),
                "conditional_eig": conditional_eig,
            },
            clock=clock,
        )
        presentations.append(presentation)
    return presentations


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


# --- Posterior replay (§5.3, Checkpoint 0.1) ----------------------------------------


def episode_posterior(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    *,
    hypothesis_set: HypothesisSet | None = None,
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
            if observation.eligible_for_completion:
                qualifying += 1
            if not observation.updates_belief:
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
    bucket = score_bucket(int(attempt.get("rubric_score") or 0))
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


# --- Evidence recording (§5.3/§5.4/§5.8) --------------------------------------------


def record_episode_evidence(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_id: str,
    attempt_id: str,
    practice_item_id: str,
    attempt_type: str,
    hints_used: int,
    probe_presentation_id: str | None,
    grading_source: str,
    tutor_contaminated: bool = False,
    ai_client: object | None = None,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Post-persist accounting for one attempt on an in-episode LO.

    Belief always updates (via posterior replay + persisted beliefs). Episode
    advancement happens only when the attempt consumes a valid presentation
    with type ``diagnostic_probe``, no contamination, and an approved
    diagnostic grading provider — everything else is incidental evidence.

    Feedback release, misconception normalization, the open-set trigger, the
    completion policy, and routing are BLOCK-boundary semantics (§5.7): they
    run through the block-end hook once the attempt closes the active block,
    never per attempt. Returns the hook payload when the block ended.
    """

    episode = repository.open_probe_episode(learning_object_id)
    if episode is None:
        return None
    hypothesis_set = episode_hypothesis_set(repository, episode)
    if hypothesis_set is None:
        return None

    if probe_presentation_id is not None:
        _record_presentation_observation(
            vault,
            repository,
            episode,
            hypothesis_set,
            attempt_id=attempt_id,
            practice_item_id=practice_item_id,
            attempt_type=attempt_type,
            hints_used=hints_used,
            probe_presentation_id=probe_presentation_id,
            grading_source=grading_source,
            tutor_contaminated=tutor_contaminated,
            clock=clock,
        )

    posterior = episode_posterior(vault, repository, episode)
    if posterior is not None:
        persist_episode_beliefs(vault, repository, episode, posterior, clock=clock)

    if probe_presentation_id is None:
        return None
    refreshed = repository.probe_episode(episode.id)
    if refreshed is None or refreshed.status != "in_progress":
        return None
    from learnloop.services.probe_blocks import block_complete, end_diagnostic_block

    if not block_complete(vault, repository, refreshed, probe_presentation_id):
        return None
    return end_diagnostic_block(vault, repository, refreshed, ai_client=ai_client, clock=clock)


def _robust_observation_snapshot(
    repository: Repository,
    episode: ProbeEpisodeRecord,
    instrument: CompiledInstrument,
    slot_map: Mapping[str, str],
    posterior_before: Mapping[str, float],
    *,
    observed_outcome: str,
    grader_confidence: float | None,
) -> dict[str, Any] | None:
    """The mvp-0.8 decision-time posterior snapshot for one observation (§4.2).

    None for legacy episodes (no pinned channel). Deterministic given the pinned
    channel hash + observed emission -- replay reads this, never the current head."""

    if episode.calibration_model_hash is None:
        return None
    from learnloop.services.probe_robust import load_pinned_channel, pinned_decision_posterior

    channel = load_pinned_channel(repository, episode.calibration_model_hash)
    if channel is None:
        return None
    return pinned_decision_posterior(
        channel,
        instrument,
        dict(slot_map),
        dict(posterior_before),
        observed_outcome=observed_outcome,
        grader_confidence=grader_confidence,
        episode_id=episode.id,
    )


def _dual_write_probe_grade(
    vault: LoadedVault,
    repository: Repository,
    *,
    instrument: CompiledInstrument | None = None,
    practice_item_id: str,
    attempt_id: str,
    grading_source: str,
    observed_outcome: str,
    clock: Clock | None = None,
) -> None:
    """P0.2 dual-write for probe submissions (§4.1, §7.2). Fail-safe (§7.3): appends
    a raw grade event + interpretation on a diagnostic administration alongside the
    unchanged three-key ``grader_channel`` probe observation. The probe posterior
    update is untouched (still ignores grader_confidence). Never raises.

    Under mvp-0.8 the versioned probe-outcome -> coarse-class mapping (§3.1) is
    snapshotted into the raw grade event's raw_output and the coarse class is pinned
    as the interpretation's observed class, so replay reproduces the mapping."""

    try:
        item = vault.practice_items.get(practice_item_id)
        if item is None:
            return
        persisted = repository.fetch_practice_attempt(attempt_id) or {}
        rubric = vault.rubric_for_item(item)
        max_points = rubric.max_points if rubric is not None else 4
        from learnloop.services.grade_resolution import record_grade_dual_write

        coarse_override: str | None = None
        mapping_meta: dict[str, Any] = {}
        outcome_schema_slug = COARSE_RESPONSE_SLUG
        if instrument is not None and use_robust_probe(vault):
            from learnloop.services.probe_outcome_mapping import (
                coarse_class_for_outcome,
                coarse_schema_slug,
                mapping_snapshot,
            )

            outcome_schema_slug = coarse_schema_slug(instrument)
            from learnloop.services.outcome_schemas import BUILTIN_SCHEMAS

            schema = next(s for s in BUILTIN_SCHEMAS if s.slug == outcome_schema_slug)
            coarse_override = coarse_class_for_outcome(
                instrument, observed_outcome, schema_true_classes=set(schema.true_classes)
            )
            mapping_meta = mapping_snapshot(instrument)

        record_grade_dual_write(
            vault,
            repository,
            observed_class_override=coarse_override,
            outcome_schema_slug=outcome_schema_slug,
            item=item,
            purpose="diagnostic",
            grading_source=grading_source,
            attempt_id=attempt_id,
            response_text=persisted.get("learner_answer_md"),
            rubric_score=persisted.get("rubric_score"),
            max_points=max_points,
            grader_confidence=persisted.get("grader_confidence"),
            raw_output={
                "observed_outcome": observed_outcome,
                "grading_source": grading_source,
                "rubric_score": persisted.get("rubric_score"),
                # Deliverable 1: snapshot the versioned probe->coarse mapping on the
                # administration's raw grade event so replay reproduces the class.
                "probe_coarse_mapping": mapping_meta or None,
            },
            domain=getattr(item, "learning_object_id", None),
            clock=clock,
        )
    except Exception:  # noqa: BLE001 - fail-safe dual-write (§7.3)
        pass


def _record_presentation_observation(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    hypothesis_set: HypothesisSet,
    *,
    attempt_id: str,
    practice_item_id: str,
    attempt_type: str,
    hints_used: int,
    probe_presentation_id: str,
    grading_source: str,
    tutor_contaminated: bool,
    clock: Clock | None,
) -> None:
    if repository.probe_observation_for_attempt(attempt_id) is not None:
        return  # idempotent retry (§5.1)
    validation = validate_presentation_for_submission(
        repository,
        probe_presentation_id,
        practice_item_id=practice_item_id,
        attempt_id=attempt_id,
        clock=clock,
    )
    if not validation.valid or validation.presentation is None:
        return  # rejected as qualifying evidence; attempt stays incidental
    presentation = validation.presentation

    # §5.8: a manual/self-grading provider cannot produce a qualifying
    # observation. The presentation is invalidated and the episode parks.
    if grading_source not in APPROVED_DIAGNOSTIC_GRADING_SOURCES:
        repository.end_probe_presentation(presentation.id, end_reason="invalidated", clock=clock)
        repository.update_probe_episode_status(episode.id, status="pending_items", clock=clock)
        return

    if not repository.consume_probe_presentation(presentation.id, clock=clock):
        return

    snapshot = presentation.instrument_card_snapshot
    if snapshot is None:
        return
    instrument = CompiledInstrument.from_snapshot(snapshot)
    labels = [hypothesis.label for hypothesis in hypothesis_set.hypotheses]
    slot_map = _resolved_slot_map_from_snapshot(snapshot, instrument, labels)
    if slot_map is None:
        return

    # Posterior before: full replay excluding this attempt (its observation row
    # does not exist yet and presentation-linked attempts are not incidental).
    before = episode_posterior(vault, repository, episode, hypothesis_set=hypothesis_set)
    posterior_before = before.posterior if before is not None else dict(hypothesis_set.prior)

    persisted_attempt = repository.fetch_practice_attempt(attempt_id) or {}
    # "I don't know" is an observation outcome, not an attempt channel.  Keep
    # the committed probe type for eligibility, but feed the explicit outcome
    # to the deterministic signature matcher so replay selects `unanswered`.
    outcome_attempt_type = (
        "dont_know" if persisted_attempt.get("declared_dont_know") else attempt_type
    )
    outcome = classify_outcome(
        instrument,
        rubric_score=_attempt_rubric_score(repository, attempt_id),
        attempt_type=outcome_attempt_type,
        fired_error_types=_fired_error_types(repository, attempt_id),
    )

    # §8.2 long-form structured trace: when the card declares ordered
    # obligations, criterion-level grading evidence localizes the first
    # invalid step, preserves the correct prefix, marks dependent downstream
    # obligations unassessable, and bounds the response's evidence mass.
    structured_trace = None
    trace_mass: float | None = None
    trace_result = _assess_longform_trace(
        vault,
        repository,
        presentation,
        instrument,
        attempt_id=attempt_id,
        practice_item_id=practice_item_id,
        attempt_type=attempt_type,
    )
    if trace_result is not None:
        trace, trace_outcome = trace_result
        structured_trace = trace.as_dict()
        trace_mass = trace.assessable_mass
        if trace_outcome is not None:
            outcome = trace_outcome

    likelihoods = instrument_observation_likelihoods(instrument, slot_map, outcome)

    contamination: dict[str, Any] = {}
    if hints_used > 0:
        contamination["hints_used"] = hints_used
    if tutor_contaminated:
        contamination["tutor_help"] = True
    # The explicit don't-know outcome retains the presentation's
    # `diagnostic_probe` type; any other type contaminates the measurement.
    if attempt_type != "diagnostic_probe":
        contamination["attempt_type"] = attempt_type
    contaminated = bool(contamination)

    episode_config = vault.config.probe.episode
    weight = episode_config.contaminated_evidence_weight if contaminated else 1.0
    # §7.7 bounded task evidence mass: dialogue microprobe turns within one
    # block share the family's total mass; each turn's likelihood is damped by
    # its committed share so the block cannot exceed one task's evidence.
    task_evidence_share = float(presentation.selection_components.get("task_evidence_share", 1.0))
    weight = min(weight, max(min(task_evidence_share, 1.0), 0.0))
    if trace_mass is not None:
        # §8.2: a multi-obligation response is one instrument — its update is
        # bounded by the assessable share of the task's fixed evidence mass.
        weight = min(weight, max(min(trace_mass, 1.0), 0.0))
    posterior_after = _bayes_update(
        dict(posterior_before), likelihoods, weight=weight, prior_for_marginal=posterior_before
    )
    entropy_before = _entropy(posterior_before)
    entropy_after = _entropy(posterior_after)
    eligible = (
        not contaminated
        and attempt_type == "diagnostic_probe"
        and grading_source in APPROVED_DIAGNOSTIC_GRADING_SOURCES
    )
    features = _observation_features(
        repository, presentation, attempt_id=attempt_id, structured_trace=structured_trace
    )
    # mvp-0.8 robust cutover (§4.2 product 1): snapshot the immutable decision-time
    # posterior from observed_update over the episode-pinned channel, so historical
    # replay is byte-stable and (invariant 3) selection + update share the pin.
    grader_confidence = persisted_attempt.get("grader_confidence")
    robust_snapshot = _robust_observation_snapshot(
        repository,
        episode,
        instrument,
        slot_map,
        posterior_before,
        observed_outcome=outcome,
        grader_confidence=grader_confidence,
    )
    if robust_snapshot is not None:
        features = dict(features or {}, robust=robust_snapshot)
    repository.insert_probe_observation(
        attempt_id=attempt_id,
        posterior_before=posterior_before,
        posterior_after=posterior_after,
        entropy_before=entropy_before,
        entropy_after=entropy_after,
        # Signed: negative realized information (entropy increased) is a §13.2
        # retirement-telemetry signal and must not be clamped away.
        realized_information_gain=entropy_before - entropy_after,
        independent_evidence_discount=weight,
        contamination=contamination or None,
        grader_channel={
            "grader_policy": instrument.grader_policy,
            "grading_source": grading_source,
            "observed_outcome": outcome,
        },
        updates_belief=True,
        eligible_for_completion=eligible,
        features=features,
        clock=clock,
    )
    _dual_write_probe_grade(
        vault,
        repository,
        instrument=instrument,
        practice_item_id=practice_item_id,
        attempt_id=attempt_id,
        grading_source=grading_source,
        observed_outcome=outcome,
        clock=clock,
    )
    if eligible and instrument.family_template_id is not None and instrument.provenance == "instrument_card":
        record_real_observation_counts(
            repository,
            family_template_id=instrument.family_template_id,
            family_template_version=instrument.family_template_version or 1,
            posterior_after=posterior_after,
            slot_map=slot_map,
            observed_outcome=outcome,
            grader_version=instrument.grader_policy,
            practice_item_id=practice_item_id,
            clock=clock,
        )


def _attempt_rubric_score(repository: Repository, attempt_id: str) -> int | None:
    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        return None
    return attempt.get("rubric_score")


def _assess_longform_trace(
    vault: LoadedVault,
    repository: Repository,
    presentation: ProbePresentationRecord,
    instrument: CompiledInstrument,
    *,
    attempt_id: str,
    practice_item_id: str,
    attempt_type: str,
):
    """Assess the §8.2 structured trace for a long-form response, or None when
    the presentation's card declares no obligations (microprobes)."""

    from learnloop.services.longform_trace import (
        assess_trace,
        classify_trace_outcome,
        obligations_from_bindings,
        outcomes_from_grading_evidence,
    )

    if attempt_type != "diagnostic_probe":
        return None
    if presentation.instrument_card_id is None or presentation.instrument_card_version is None:
        return None
    card_record = repository.probe_instrument_card(
        presentation.instrument_card_id, presentation.instrument_card_version
    )
    if card_record is None:
        return None
    card = InstrumentCard.from_dict(card_record.card)
    obligations = obligations_from_bindings(card.bindings)
    if not obligations:
        return None
    item = vault.practice_items.get(practice_item_id)
    rubric = vault.rubric_for_item(item) if item is not None else None
    criteria_max = {
        criterion.id: float(criterion.points) for criterion in (rubric.criteria if rubric else [])
    }
    outcomes = outcomes_from_grading_evidence(
        obligations, repository.fetch_grading_evidence(attempt_id), criteria_max
    )
    trace = assess_trace(
        obligations, outcomes, total_task_evidence_mass=instrument.total_task_evidence_mass
    )
    trace_outcome = classify_trace_outcome(trace, obligations, instrument.outcome_alphabet)
    return trace, trace_outcome


def _observation_features(
    repository: Repository,
    presentation: ProbePresentationRecord,
    *,
    attempt_id: str,
    structured_trace: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Logged-only observation features (§7.1): answer confidence, latency
    (both submitted and derived from presentation timestamps), and the §8.2
    structured trace. Replay never reads these."""

    features: dict[str, Any] = {}
    attempt = repository.fetch_practice_attempt(attempt_id) or {}
    if attempt.get("answer_confidence") is not None:
        features["answer_confidence"] = int(attempt["answer_confidence"])
    if attempt.get("latency_seconds") is not None:
        features["latency_seconds"] = int(attempt["latency_seconds"])
    served = parse_utc(presentation.served_at)
    submitted = parse_utc(attempt.get("created_at"))
    if served is not None and submitted is not None:
        features["presentation_latency_seconds"] = max(
            0, int((submitted - served).total_seconds())
        )
    if structured_trace is not None:
        features["structured_trace"] = dict(structured_trace)
    return features or None


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


# --- Completion policy (§11) ---------------------------------------------------------


def _evaluate_completion(
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

    if len(qualifying) >= episode.maximum_observations:
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
        # of grinding through non-discriminating instruments (U-021).
        # An unstable posterior whose plausible hypotheses all imply the same
        # repair needs no further probing — stop before spending instruments.
        if _action_equivalent():
            return _complete(repository, episode, "action_equivalent", posterior=posterior, clock=clock)
        abstain_reason = _robust_completion_override(vault, repository, episode, posterior)
        if abstain_reason is not None:
            return _complete(repository, episode, abstain_reason, posterior=posterior, clock=clock)
        # §10: an unstable episode with no unconsumed instrument left (§5.4
        # forbids surface repeats) parks in pending_items with one deduplicated
        # generation need — never blocking ordinary practice on the LO.
        # `no_suitable_candidate` completion is reserved for generation being
        # declined or failing.
        if qualifying and not eligible_instruments(vault, repository, episode, posterior=posterior.posterior):
            repository.update_probe_episode_status(episode.id, status="pending_items", clock=clock)
            _record_generation_need(vault, repository, episode, posterior.hypothesis_set, clock=clock)
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
    if breadth_ok:
        return _complete(repository, episode, "decision_stable", posterior=posterior, clock=clock)

    # §11 fast path: an explicit strong prior claim plus one highly
    # discriminating cross-facet instrument may complete early. This replaces
    # the legacy claim_skip_threshold (Checkpoint 0.4 mapping).
    if (
        len(qualifying) >= 1
        and strong_prior_claim(vault, repository, episode.learning_object_id)
        and any(len(row.get("target_facets") or []) >= 2 for row in qualifying)
    ):
        return _complete(repository, episode, "fast_path_strong_claim", posterior=posterior, clock=clock)
    # Stable but breadth-short: if the plausible hypotheses already agree on
    # the repair, the missing breadth buys nothing for routing — stop.
    if _action_equivalent():
        return _complete(repository, episode, "action_equivalent", posterior=posterior, clock=clock)
    return None


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

    from learnloop.services.probe_hypotheses import triage_reason_for_label

    threshold = float(episode_config.action_equivalence_plausible_threshold)
    plausible = [
        label
        for label, probability in posterior.posterior.items()
        if float(probability) >= threshold
    ]
    if not plausible:
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


def _robust_completion_override(
    vault: LoadedVault,
    repository: Repository,
    episode: ProbeEpisodeRecord,
    posterior: EpisodePosterior,
) -> str | None:
    """The mvp-0.8 robust stop/abstain gate (§4.2). Returns
    ``'couldnt_reliably_distinguish'`` when, after at least the minimum independent
    observations, the remaining instruments cannot robustly distinguish the
    hypotheses on the episode-pinned channel; otherwise None (defer to legacy park).

    Legacy episodes (no pinned channel) always return None -- byte-identical path."""

    if episode.calibration_model_hash is None:
        return None
    qualifying = sum(
        1 for row in repository.probe_observations_for_episode(episode.id)
        if row["observation"].eligible_for_completion
    )
    if qualifying < episode.minimum_independent_observations:
        return None
    from learnloop.services.probe_robust import (
        RobustCandidate,
        load_pinned_channel,
        robust_selection,
    )

    channel = load_pinned_channel(repository, episode.calibration_model_hash)
    if channel is None:
        return None
    candidates = eligible_instruments(vault, repository, episode, posterior=posterior.posterior)
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
    decision = robust_selection(
        channel, robust_candidates, posterior.posterior, episode_id=episode.id
    )
    if decision.abstained:
        return "couldnt_reliably_distinguish"
    return None


def _surface_key(vault: LoadedVault, practice_item_id: str) -> str:
    item = vault.practice_items.get(practice_item_id)
    if item is None:
        return practice_item_id
    return item.surface_family or item.id


def _complete(
    repository: Repository,
    episode: ProbeEpisodeRecord,
    reason: str,
    *,
    posterior: EpisodePosterior | None = None,
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
        clock=clock,
    )
    return reason


# --- Learner controls (§3, §12.1) -----------------------------------------------------


def stop_diagnosing_and_teach(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """`Stop diagnosing and teach me`: end measurement, open a post-intervention
    state segment, and persist a typed transition decision (§12.1)."""

    episode = repository.open_probe_episode(learning_object_id)
    if episode is None:
        return None
    posterior = episode_posterior(vault, repository, episode)
    active = repository.active_probe_presentation(episode.id)
    if active is not None:
        repository.end_probe_presentation(active.id, end_reason="invalidated", clock=clock)

    from learnloop.services.probe_blocks import (
        _first_error_from_block,
        block_observation_rows,
        build_typed_transition_decision,
    )

    decision = build_typed_transition_decision(
        vault,
        repository,
        episode,
        posterior,
        first_error_step_or_claim=_first_error_from_block(
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
    _set_target_decision(repository, episode.id, decision, clock=clock)
    repository.open_state_segment(
        learning_object_id=learning_object_id,
        probe_episode_id=episode.id,
        reason="tutoring_transition",
        clock=clock,
    )
    return decision


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


def _set_target_decision(
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


def abandon_episode(
    repository: Repository,
    learning_object_id: str,
    *,
    clock: Clock | None = None,
) -> None:
    episode = repository.open_probe_episode(learning_object_id)
    if episode is None:
        return
    active = repository.active_probe_presentation(episode.id)
    if active is not None:
        repository.end_probe_presentation(active.id, end_reason="abandoned", clock=clock)
    repository.update_probe_episode_status(
        episode.id,
        status="abandoned",
        completion_reason="learner_abandoned",
        completed_at=utc_now_iso(clock),
        clock=clock,
    )


# --- Client contract (§12) --------------------------------------------------------------


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
    return {
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
    from learnloop.services.probe_targeting import (
        open_cause_sets_for_learning_object,
        select_discriminating_instrument,
    )

    cause_sets = open_cause_sets_for_learning_object(vault, repository, learning_object_id)
    if cause_sets:
        discriminating = select_discriminating_instrument(cause_sets[0], candidates)
        if discriminating is not None:
            return discriminating
    return candidates[0]

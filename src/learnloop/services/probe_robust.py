"""mvp-0.8 probe-episode robust cutover glue (spec_p0_measurement_correctness §4.2,
change-log entry b').

This module wires the tested robust-composition library
(:mod:`learnloop.services.robust_composition`) into the probe episode loop **under
mvp-0.8 vaults only**. It resolves and pins the calibration channel at episode open,
builds the deterministic composition ensemble on the pinned channel, and exposes the
robust products (candidate ranking / stop / abstain, decision-time observed_update
posterior) the episode loop consumes.

Invariant 3 (§1.1): selection and update use the **same** pinned channel. Both the
candidate ranking ensemble and the decision-time ``observed_update`` seed from the
episode-pinned ``calibration_model_hash``; a change of the active head model can never
silently reinterpret a historical episode decision -- that is the separate named
reinterpretation projection (:func:`p0_projection.record_reinterpretation_if_changed`).

The legacy mvp-0.6/0.7 point path (``probe_families.instrument_*`` +
``probe_episodes.episode_posterior``) is untouched and stays byte-identical; nothing
here runs unless :func:`use_robust_probe` is true.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services import grader_calibration as gc
from learnloop.services import robust_composition as rc
from learnloop.services.assessment_contracts import P0_ALGORITHM_VERSION
from learnloop.services.grade_classifier import bucket_confidence
from learnloop.services.outcome_schemas import SIGNATURE_ERROR_SLUG, resolve_schema_id
from learnloop.services.probe_families import CompiledInstrument
from learnloop.services.probe_outcome_mapping import (
    PROBE_COARSE_MAPPING_VERSION,
    coarse_class_for_outcome,
    coarse_instrument_rows,
)
from learnloop.vault.models import LoadedVault

# The episode pins one coarse channel. Diagnostic probe cards recognize a specific
# misconception (§3.1), so the episode-level pinned schema is the three-class
# signature-error schema; per-instrument coarse rows aggregate onto its true classes.
EPISODE_COARSE_SCHEMA_SLUG = SIGNATURE_ERROR_SLUG


def use_robust_probe(vault: LoadedVault) -> bool:
    """True iff this vault runs the mvp-0.8 authority-propagation probe path.

    Mirrors the ``project_canonical_facet_state`` version gate (canonical_projection):
    the robust cutover is strictly mvp-0.8; mvp-0.6/0.7 keep the legacy point path.
    """

    return vault.config.algorithms.algorithm_version == P0_ALGORITHM_VERSION


@dataclass(frozen=True)
class EpisodeChannel:
    """The calibration channel pinned on an episode at open (§4.2, invariant 3)."""

    model_id: str
    model_hash: str
    joint_alpha: dict[str, dict[str, float]]
    true_classes: tuple[str, ...]
    mapping_version: str
    fallback_reason: str | None


def resolve_episode_channel(
    repository: Repository,
    *,
    learning_object_id: str,
    clock: Clock | None = None,
) -> EpisodeChannel:
    """Resolve + freeze the coarse calibration channel for an episode (§4.2).

    Resolves the global-pooled signature-error channel scoped to the LO domain. The
    returned ``model_hash`` is pinned on the episode; both the robust selection
    ensemble and the decision-time ``observed_update`` seed from it.
    """

    schema_id, schema_version = resolve_schema_id(
        repository, EPISODE_COARSE_SCHEMA_SLUG, clock=clock
    )
    resolved = gc.resolve_calibration_model(
        repository,
        grader_identity_hash=None,
        outcome_schema_id=schema_id,
        outcome_schema_version=schema_version,
        domain=learning_object_id,
        clock=clock,
    )
    # The resolved model_hash is a COMPOSITE over the pooled backoff chain, not any
    # single stored row's content_hash. Persist a content-addressed pinned-channel
    # snapshot row keyed by that composite so replay rehydrates the exact pooled
    # joint alpha byte-stably (§4.2 "immutable decision-time snapshot ... pinned
    # grader channel"; §7.2 pinned channel snapshot/hash). Idempotent.
    pinned_id = _persist_pinned_channel(
        repository, resolved, schema_id, schema_version, clock=clock
    )
    return EpisodeChannel(
        model_id=pinned_id,
        model_hash=resolved.model_hash,
        joint_alpha=resolved.joint_alpha,
        true_classes=resolved.true_classes,
        mapping_version=PROBE_COARSE_MAPPING_VERSION,
        fallback_reason=resolved.fallback_reason,
    )


def _persist_pinned_channel(
    repository: Repository,
    resolved: gc.ResolvedModel,
    schema_id: str,
    schema_version: int,
    *,
    clock: Clock | None = None,
) -> str:
    """Content-address the pooled channel by its composite hash so
    :func:`load_pinned_channel` can rehydrate it for replay. Append-only + idempotent
    (content_hash UNIQUE backstop, migration 070)."""

    existing = repository.find_calibration_model_by_hash(resolved.model_hash)
    if existing is not None:
        return existing["id"]
    import json as _json_module

    return repository.insert_calibration_model(
        model={
            "grader_provider": None,
            "grader_model_revision": None,
            "grading_prompt_version": None,
            "grader_output_schema_version": None,
            "grader_identity_hash": None,
            "semver": "0.1.0",
            "parent_model_id": resolved.model_id or None,
            "content_hash": resolved.model_hash,
            "scope_level": "global",
            "outcome_schema_id": schema_id,
            "outcome_schema_version": schema_version,
            "domain": None,
            "length_bucket": None,
            "backoff_chain_json": _json_module.dumps(resolved.contributing_model_ids),
            "status": resolved.status,
            "count_heuristic_prior": int(gc.PRIOR_CONCENTRATION),
            "prior_concentration": gc.PRIOR_CONCENTRATION,
            "provenance_json": _json_module.dumps(
                {"source": "probe_episode_pinned_channel", "pooled": resolved.contributing_model_ids}
            ),
        },
        alphas=resolved.joint_alpha,
        clock=clock,
    )


def load_pinned_channel(repository: Repository, model_hash: str) -> EpisodeChannel | None:
    """Rehydrate the pinned channel from its stored hash for replay (§2.2).

    Replay reads the snapshot, never the current active head, so a later model
    activation leaves a historical decision byte-stable.
    """

    row = repository.find_calibration_model_by_hash(model_hash)
    if row is None:
        return None
    alpha = repository.fetch_calibration_alphas(row["id"])
    return EpisodeChannel(
        model_id=row["id"],
        model_hash=model_hash,
        joint_alpha=alpha,
        true_classes=tuple(sorted(alpha.keys())),
        mapping_version=PROBE_COARSE_MAPPING_VERSION,
        fallback_reason=None,
    )


def _decision_context_hash(
    *,
    episode_id: str | None,
    candidate_card_version: str | None,
    slot_map: Mapping[str, str],
    posterior: Mapping[str, float],
) -> str:
    return rc.decision_context_hash(
        episode_id=episode_id,
        candidate_card_version=candidate_card_version,
        resolved_slot_map=dict(slot_map),
        posterior_at_selection=dict(posterior),
        projection_algorithm_version=P0_ALGORITHM_VERSION,
    )


def instrument_ensemble(
    channel: EpisodeChannel,
    instrument: CompiledInstrument,
    slot_map: Mapping[str, str],
    posterior: Mapping[str, float],
    *,
    episode_id: str | None,
) -> tuple[rc.Ensemble, str]:
    """Build the deterministic composition ensemble for one candidate on the pinned
    channel. Returns ``(ensemble, decision_context_hash)``."""

    rows = coarse_instrument_rows(instrument, slot_map, channel.true_classes)
    candidate_card_version = (
        f"{instrument.card_id}:{instrument.card_version}" if instrument.card_id else None
    )
    dch = _decision_context_hash(
        episode_id=episode_id,
        candidate_card_version=candidate_card_version,
        slot_map=slot_map,
        posterior=posterior,
    )
    ensemble = rc.build_ensemble(
        joint_alpha=channel.joint_alpha,
        instrument_rows=rows,
        calibration_model_hash=channel.model_hash,
        decision_context_hash=dch,
    )
    return ensemble, dch


def coarse_emission(
    channel: EpisodeChannel,
    instrument: CompiledInstrument,
    *,
    observed_outcome: str,
    grader_confidence: float | None,
) -> str:
    """The observed joint emission ``E = (coarse_G, confidence_bucket)`` (§3.2)."""

    coarse_g = coarse_class_for_outcome(
        instrument, observed_outcome, schema_true_classes=set(channel.true_classes)
    )
    return f"{coarse_g}|{bucket_confidence(grader_confidence)}"


def pinned_decision_posterior(
    channel: EpisodeChannel,
    instrument: CompiledInstrument,
    slot_map: Mapping[str, str],
    posterior_before: Mapping[str, float],
    *,
    observed_outcome: str,
    grader_confidence: float | None,
    episode_id: str | None,
) -> dict[str, object]:
    """The immutable decision-time posterior snapshot (§4.2 product 1).

    ``observed_update`` over the pinned channel's posterior-mean member, conditioned
    on the realized coarse emission. Snapshotted so historical replay is byte-stable
    without re-running the ensemble.
    """

    ensemble, dch = instrument_ensemble(
        channel, instrument, slot_map, posterior_before, episode_id=episode_id
    )
    emission = coarse_emission(
        channel, instrument, observed_outcome=observed_outcome, grader_confidence=grader_confidence
    )
    updated = rc.observed_update(ensemble.mean_member, dict(posterior_before), emission)
    return {
        "posterior_after": {k: round(float(v), 12) for k, v in updated.items()},
        "observed_emission": emission,
        "calibration_model_hash": channel.model_hash,
        "calibration_model_id": channel.model_id,
        "decision_context_hash": dch,
        "ensemble_seed": ensemble.seed,
        "mapping_version": channel.mapping_version,
        "projection_algorithm_version": P0_ALGORITHM_VERSION,
    }


@dataclass(frozen=True)
class RobustCandidate:
    identifier: str
    instrument: CompiledInstrument
    slot_map: dict[str, str]
    expected_seconds: float


def robust_selection(
    channel: EpisodeChannel,
    candidates: Sequence[RobustCandidate],
    posterior: Mapping[str, float],
    *,
    episode_id: str | None,
) -> rc.RobustDecision:
    """Robust candidate ranking + stop rule + agreement gate + abstention (§4.2).

    Ranks candidates by robust EIG-per-second on the pinned channel and returns the
    :class:`robust_composition.RobustDecision` -- ``verdict`` is ``'act'``,
    ``'stop'`` (decision resolved / nothing worth running) or
    ``'couldnt_reliably_distinguish'`` (the explicit abstention outcome).
    """

    triples: list[tuple[str, rc.Ensemble, float]] = []
    for candidate in candidates:
        ensemble, _dch = instrument_ensemble(
            channel, candidate.instrument, candidate.slot_map, posterior, episode_id=episode_id
        )
        triples.append((candidate.identifier, ensemble, candidate.expected_seconds))
    return rc.evaluate_selection(candidates=triples, posterior=dict(posterior))

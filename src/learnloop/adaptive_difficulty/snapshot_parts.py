"""What adaptive difficulty's serve-time forecasts state in their prediction snapshots (EP spec §7.7.3).

The writer (:mod:`learnloop.scheduling.prediction_snapshots`) derives what it can from a receipt's columns; a
serve-time forecast knows more: the item revision it was served at, its facets and surface group, the read it
was computed from and the artifacts behind its numbers. These are evaluation-only: nothing here is read back by
a decision, enters ``inputs_json`` or mints an id. Everything below is read off the item and the values the
forecaster already holds; no database read.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from learnloop.db.evidence_cutoff import Cutoff
from learnloop.db.prediction_target import (
    MEMBER_FACET,
    MEMBER_ITEM,
    MEMBER_LEARNING_OBJECT,
    MEMBER_SURFACE_GROUP,
    PredictionTarget,
    TargetMember,
)
from learnloop.scheduling.prediction_snapshots import UNIT_BINARY, SnapshotParts, categorical_distribution

from learnloop.adaptive_difficulty import priors as P
from learnloop.adaptive_difficulty.logs import warn_failure

LOG = logging.getLogger(__name__)

#: The graded response's three categories (§5.3): the receipt's binary event is category 2.
UNIT_CATEGORIES = "ad_category3"
CATEGORIES = ("0", "1", "2")
EVENT_CATEGORIES = ("2",)

#: The resolver that scores these forecasts: ``scoring.SCORE_VERSION``, restated here because this module imports
#: nothing of AD's serving or scoring (both import it; the import would close a cycle). A test pins the two equal.
RESOLVER_VERSION = "ad_forecast_scores_v1"

#: Where an item's surface-group key comes from, in :func:`replay.surface_group`'s order.
_SURFACE_SOURCES = (("evidence_fingerprint.shared_stimulus_id", "shared_stimulus_id"),
                    ("evidence_fingerprint.source_family", "source_family"),
                    ("evidence_fingerprint.solution_recipe_family", "solution_recipe_family"))


@dataclass(frozen=True)
class ServedItem:
    """The served revision's identity, as the serve read it: the item, its content hash, its learning object,
    its canonical facets and its surface group with the field that key came from."""

    item_id: str
    content_hash: str
    learning_object_id: str
    facets: tuple[str, ...]
    surface_key: str
    surface_source: str


def surface_source(item: Any, key: str) -> str:
    """The field :func:`~learnloop.adaptive_difficulty.replay.surface_group`'s ``key`` came from (``item`` when
    the item is its own group)."""

    fingerprint = getattr(item, "evidence_fingerprint", None)
    for source, name in _SURFACE_SOURCES:
        if getattr(fingerprint, name, None) and str(getattr(fingerprint, name)) == key:
            return source
    if getattr(item, "surface_family", None) and str(item.surface_family) == key:
        return "surface_family"
    return "item"


def item_target(served: ServedItem, *, unit: str, presentation_kind: str, presentation_id: str) -> PredictionTarget:
    """A serve-time forecast's target: the item at its served revision, its learning object, its facets and
    its surface group, conditional on serving it at this presentation, resolved by AD's scorer."""

    members = [TargetMember(MEMBER_ITEM, served.item_id, served.content_hash),
               TargetMember(MEMBER_LEARNING_OBJECT, served.learning_object_id),
               TargetMember(MEMBER_SURFACE_GROUP, served.surface_key, source=served.surface_source)]
    members += [TargetMember(MEMBER_FACET, facet) for facet in sorted(set(served.facets))]
    return PredictionTarget(
        kind="item_unassisted_success", members=tuple(members), unit=unit,
        # The category definition (§5.3's thresholds) lives in the priors module and moves with its version.
        event_version=f"ad_category:{P.PRIORS_VERSION}", resolver_version=RESOLVER_VERSION,
        action_kind="serve", action_id=served.item_id, horizon_kind="presentation",
        anchor_kind=presentation_kind, anchor_id=presentation_id)


def threshold_parts(served: ServedItem, *, name: str, categories: tuple[float, float, float],
                    state_hash: str, mixture: str, presentation_kind: str, presentation_id: str,
                    served_at: str, epoch: Any, threshold_version: str, replay_version: str) -> SnapshotParts:
    """An ``ad_threshold@*`` receipt's snapshot: the replayed state it read (every readable event at the
    serve, through the serve's material view), the three category probabilities, and its artifacts."""

    return SnapshotParts(
        cutoff=Cutoff.ad_replay(None),
        source={"ad_state_hash": state_hash, "replay_version": replay_version,
                # The frozen serve inputs of the same presentation (``item_serve_inputs.receipt_key``).
                "item_serve_inputs": f"{presentation_kind}:{presentation_id}",
                "spec_and_warmth_read_at": served_at, "protection_epoch": epoch},
        target=item_target(served, unit=UNIT_CATEGORIES, presentation_kind=presentation_kind,
                           presentation_id=presentation_id),
        distribution=categorical_distribution(dict(zip(CATEGORIES, categories, strict=True)),
                                              unit=UNIT_CATEGORIES, event="unassisted_success",
                                              event_outcomes=EVENT_CATEGORIES),
        provenance={
            "prior": {"version": P.PRIORS_VERSION, "hyper": P.HYPER_VERSION, "source": "code"},
            "likelihood": {"name": "graded_response", "version": threshold_version,
                           "source": "adaptive_difficulty.model.category_probabilities",
                           "constants": {"A": P.A, "LAPSE": P.LAPSE, "KAPPA": P.KAPPA, "TAU0": P.TAU0}},
            "fitted_artifact": {"kind": "ad_state", "state_hash": state_hash, "replay_version": replay_version},
            "training_cutoff": {"preset": "ad_replay", "as_of": None,
                                "note": "the state replays every readable event at the serve"},
            "mixture": mixture, "forecaster": name, "model_call": None,
        })


def threshold_snapshot(served: ServedItem | None, *, name: str, categories_of: Callable[[], tuple[float, float, float]],
                       mixture: str, state_hash: str, presentation_kind: str, presentation_id: str,
                       served_at: str, epoch: Any, threshold_version: str, replay_version: str
                       ) -> tuple[dict[str, float] | None, SnapshotParts | None]:
    """A threshold forecast's ``p_categories`` (by category, ``categories_of()``: the caller's
    :func:`~learnloop.adaptive_difficulty.predict.category_mixture` at the view, spec, warmth and weights its
    ``p̄`` was computed with) and its snapshot parts. Never raises: metadata that cannot be computed is left out
    (``None``, as before), and the receipt is written as it was."""

    try:
        categories = categories_of()
    except Exception:  # noqa: BLE001 - a snapshot must never cost the serve its receipts
        warn_failure(LOG, "category probabilities of %s for %s not computed", name, presentation_id)
        return None, None
    if served is None:
        return dict(zip(CATEGORIES, categories, strict=True)), None
    parts: SnapshotParts | None
    try:
        parts = threshold_parts(served, name=name, categories=categories, state_hash=state_hash,
                                mixture=mixture, presentation_kind=presentation_kind,
                                presentation_id=presentation_id, served_at=served_at, epoch=epoch,
                                threshold_version=threshold_version, replay_version=replay_version)
    except Exception:  # noqa: BLE001 - a snapshot must never cost the serve its receipts
        warn_failure(LOG, "prediction snapshot of %s for %s not built", name, presentation_id)
        parts = None
    return dict(zip(CATEGORIES, categories, strict=True)), parts


def in_process_snapshot(served: ServedItem | None, **kwargs: Any) -> SnapshotParts | None:
    """:func:`in_process_parts`, or None (the writer derives what it can) when the serve passed no identity or
    it cannot be built."""

    if served is None:
        return None
    try:
        return in_process_parts(served, **kwargs)
    except Exception:  # noqa: BLE001 - a snapshot must never cost the serve its receipts
        warn_failure(LOG, "prediction snapshot of an in-process forecast for %s not built",
                     kwargs.get("presentation_id"))
        return None


def in_process_parts(served: ServedItem, *, incumbent: bool, version_hash: str, inputs: Mapping[str, Any],
                     presentation_kind: str, presentation_id: str, served_at: str) -> SnapshotParts:
    """``mastery_ekf``'s and ``lo_general+composite``'s snapshot: the incumbent reads the mastery states as
    they stand (current); the challenger refits on attempt rows completed by the serve (the field's
    ``completed_by``)."""

    cutoff = Cutoff.current() if incumbent else Cutoff.completed_by(served_at)
    source: dict[str, Any] = {"read": "mastery_states" if incumbent else "field attempt rows"}
    if not incumbent:
        source.update(attempt_rows=inputs.get("attempt_rows"), rows_digest=inputs.get("rows_digest"),
                      latest_attempt_at=inputs.get("latest_attempt_at"))
    return SnapshotParts(
        cutoff=cutoff, source=source,
        target=item_target(served, unit=UNIT_BINARY, presentation_kind=presentation_kind,
                           presentation_id=presentation_id),
        provenance={
            "fitted_artifact": {"kind": "mastery_states" if incumbent else "refit_at_serve",
                                "version_hash": version_hash},
            "likelihood": {"version": version_hash, "source": "code+config (the forecaster's version hash)"},
            "training_cutoff": {"absent": "the persisted mastery states keep no cutoff of the evidence they fold"}
            if incumbent else {"preset": "completed_by", "as_of": served_at},
            "model_call": None,
        })


__all__ = ["CATEGORIES", "EVENT_CATEGORIES", "RESOLVER_VERSION", "ServedItem", "UNIT_CATEGORIES", "in_process_parts",
           "in_process_snapshot", "item_target", "surface_source", "threshold_parts", "threshold_snapshot"]

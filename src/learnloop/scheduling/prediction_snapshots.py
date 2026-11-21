"""Prediction snapshots: what a forecast receipt needs to be scored later without reconstruction (EP spec §7.7).

A forecast receipt already says who forecast, with what inputs, and what it said about a binary event. A
snapshot adds, inside the receipt's existing JSON bodies, what makes it scorable months later without replaying
the state it came from:

* ``versions_json.snapshot.cutoff``: the evidence cutoff the forecast honoured (a serialized
  :class:`~learnloop.db.evidence_cutoff.Cutoff`, its approximation list inside it), a reference to what was read,
  and the original ``inputs_as_of`` with its validity (``exact``, ``unknown``, ``invalid``) beside the clamped
  value the receipt keeps: the clamp replaces a missing or future time with the issue time, and without the
  status a reader could not tell a replaced time from a stated one.
* ``versions_json.snapshot.target``: the pinned identity of what was predicted
  (:class:`~learnloop.db.prediction_target.PredictionTarget` and its ``target_hash``).
* ``versions_json.snapshot.provenance``: where the numbers came from (prior or fitted artifact, likelihood,
  training cutoff, the model call's prompt and schema where a model forecast).
* ``forecast_json.distribution``: the forecast as probabilities over named outcomes at the precision the
  producer had, and ``forecast_json.reason`` where no forecast was issued.

Evaluation-only metadata: nothing here enters ``inputs_json`` (whose digest may key reuse), the receipt key, the
binary ``p``, a cache key, a seed or a decision, and building it mints no id. A producer states what only it knows
(:class:`SnapshotParts`); the writer derives the rest from the receipt's own fields and says which fields it
derived. Where a field would need data the writer does not have, it is recorded absent with its reason, never
guessed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from learnloop.clock import parse_utc
from learnloop.db.evidence_cutoff import Cutoff
from learnloop.db.prediction_target import (
    MEMBER_FACET,
    MEMBER_ITEM,
    MEMBER_LEARNING_OBJECT,
    PredictionTarget,
    TargetMember,
)

logger = logging.getLogger(__name__)

SNAPSHOT_SCHEMA = "prediction_snapshot/1"

#: The original ``inputs_as_of``: a readable time no later than the receipt, absent (or empty), or replaced by the
#: issue time because it was after it.
AS_OF_EXACT = "exact"
AS_OF_UNKNOWN = "unknown"
AS_OF_INVALID = "invalid"

#: A target version the producer does not state: the writer names the field rather than invent a version.
UNVERSIONED = "unversioned"

#: The binary unit: ``p`` is the event's probability, the outcomes the event and its complement.
UNIT_BINARY = "binary"
EVENT_OUTCOME = "event"
NOT_EVENT_OUTCOME = "not_event"

_BOUND_COLUMNS = ("plan_presentation_id", "probe_presentation_id", "followup_task_id", "scheduler_candidate_id",
                  "source_attempt_id")


@dataclass(frozen=True)
class SnapshotParts:
    """What a producer knows that the receipt's own fields do not say.

    ``cutoff`` and ``target`` are the producer's own; a producer that cannot state one gives the reason in
    ``cutoff_absent`` / ``target_absent`` instead (with neither, the writer records the cutoff absent and
    derives the target from the receipt's columns). ``source`` names what was read (an ``item_serve_inputs``
    row, a state hash). ``distribution`` is the forecast over named outcomes where the producer computed more
    than the binary event (:func:`categorical_distribution`). ``provenance`` is merged over the writer's own.
    """

    cutoff: Cutoff | None = None
    cutoff_absent: str | None = None
    source: Mapping[str, Any] | None = None
    target: PredictionTarget | None = None
    target_absent: str | None = None
    distribution: Mapping[str, Any] | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)


def as_of_status(value: Any, issued: str) -> str:
    """The validity of a receipt's original ``inputs_as_of`` against its issue time."""

    if value is None or str(value) == "":
        return AS_OF_UNKNOWN
    try:
        parsed = parse_utc(str(value))
        created = parse_utc(str(issued))
    except (TypeError, ValueError):
        return AS_OF_INVALID
    if parsed is None or created is None or parsed > created:
        return AS_OF_INVALID
    return AS_OF_EXACT


def binary_distribution(p: float, *, event: str) -> dict[str, Any]:
    """A binary forecast as named outcomes: ``p`` itself for the event, its complement for the rest."""

    return {"unit": UNIT_BINARY, "event": event, "outcomes": {EVENT_OUTCOME: p, NOT_EVENT_OUTCOME: 1.0 - p},
            "event_outcomes": [EVENT_OUTCOME], "reason": None}


def categorical_distribution(probabilities: Mapping[str, float], *, unit: str, event: str,
                             event_outcomes: Sequence[str]) -> dict[str, Any]:
    """A forecast over named categories; the binary ``p`` is the sum over ``event_outcomes``."""

    return {"unit": unit, "event": event, "outcomes": {str(k): float(v) for k, v in probabilities.items()},
            "event_outcomes": [str(name) for name in event_outcomes], "reason": None}


def not_issued_distribution(reason: str, *, unit: str = UNIT_BINARY, event: str | None = None) -> dict[str, Any]:
    return {"unit": unit, "event": event, "outcomes": None, "event_outcomes": [], "reason": reason}


def _not_issued_reason(receipt: Any) -> str | None:
    status = str(receipt.columns.get("status") or "ok")
    if status != "ok":
        return status
    if receipt.p is None and receipt.forecast.get("p") is None:
        return "no_forecast"
    return None


def receipt_target(receipt: Any) -> tuple[PredictionTarget | None, list[str], str | None]:
    """The target the writer can read off the receipt's columns: ``(target, unversioned fields, absent reason)``.

    Members are the item (at ``item_content_hash`` where the receipt names one), the learning object and the
    facet the receipt's columns name; the action is its deciding decision, the horizon its binding, the anchor
    the bound row. The receipt's event names its event definition, which has no version of its own, and no
    resolver version is stated by such a producer: both are recorded as unversioned and listed."""

    columns = receipt.columns
    members = []
    if columns.get("practice_item_id"):
        revision = columns.get("item_content_hash")
        members.append(TargetMember(MEMBER_ITEM, str(columns["practice_item_id"]),
                                    None if revision is None else str(revision)))
    if columns.get("learning_object_id"):
        members.append(TargetMember(MEMBER_LEARNING_OBJECT, str(columns["learning_object_id"])))
    if columns.get("facet_id"):
        members.append(TargetMember(MEMBER_FACET, str(columns["facet_id"])))
    if not members:
        return None, [], "the receipt names no item, learning object or facet"
    anchor = next(((name[: -len("_id")], str(columns[name])) for name in _BOUND_COLUMNS if columns.get(name)),
                  (None, None))
    target = PredictionTarget(
        kind=receipt.kind, members=tuple(members), unit=UNIT_BINARY,
        event_version=f"{receipt.event}@{UNVERSIONED}", resolver_version=f"{receipt.binding_kind}@{UNVERSIONED}",
        action_kind=receipt.decision_kind,
        action_id=None if columns.get("decision_ref") is None else str(columns["decision_ref"]),
        horizon_kind="binding", horizon=receipt.binding_kind, anchor_kind=anchor[0], anchor_id=anchor[1])
    return target, ["event_version", "resolver_version"], None


def _target_block(receipt: Any, parts: SnapshotParts) -> dict[str, Any]:
    if parts.target is not None:
        target, stated_by, unversioned, absent = parts.target, "producer", [], None
    elif parts.target_absent:
        target, stated_by, unversioned, absent = None, None, [], parts.target_absent
    else:
        target, unversioned, absent = receipt_target(receipt)
        stated_by = "writer" if target is not None else None
    return {"target": None if target is None else target.to_dict(),
            "target_hash": None if target is None else target.target_hash(),
            "stated_by": stated_by, "unversioned": unversioned, "absent": absent}


def _cutoff_block(receipt: Any, parts: SnapshotParts, issued: str, recorded_as_of: str) -> dict[str, Any]:
    original = receipt.inputs_as_of
    return {
        "cutoff": None if parts.cutoff is None else parts.cutoff.to_dict(),
        "absent": None if parts.cutoff is not None else (
            parts.cutoff_absent or "the producer does not state the evidence cutoff it read under"),
        "source": None if parts.source is None else dict(parts.source),
        "inputs_as_of": {"original": None if original is None else str(original), "recorded": recorded_as_of,
                         "status": as_of_status(original, issued)},
    }


def _provenance_block(receipt: Any, parts: SnapshotParts) -> dict[str, Any]:
    versions = receipt.versions or {}
    block: dict[str, Any] = {"forecaster": receipt.forecaster, "forecaster_version": receipt.forecaster_version}
    if versions.get("prompt") is not None or versions.get("model") is not None:
        # A model forecast: what the receipt's versions say of the call; the call's own receipt id is not
        # passed to this writer, so it is named absent rather than looked up.
        block["model_call"] = {"model": versions.get("model"), "prompt_version": versions.get("prompt"),
                               "call_receipt_id": None,
                               "call_receipt_absent": "the forecast writer is not given the model call's receipt"}
    block.update(dict(parts.provenance))
    return block


def snapshot(receipt: Any, issued: str, recorded_as_of: str) -> dict[str, Any]:
    """``versions_json.snapshot`` of one receipt (module docstring)."""

    parts = receipt.snapshot if receipt.snapshot is not None else SnapshotParts()
    return {
        "schema": SNAPSHOT_SCHEMA,
        "cutoff": _cutoff_block(receipt, parts, issued, recorded_as_of),
        "target": _target_block(receipt, parts),
        "provenance": _provenance_block(receipt, parts),
        "binding": {"kind": receipt.binding_kind, "censor_reason": receipt.columns.get("censor_reason")},
    }


def distribution(receipt: Any) -> tuple[dict[str, Any], str | None]:
    """``forecast_json.distribution`` and the reason no forecast was issued (None when one was)."""

    reason = _not_issued_reason(receipt)
    if reason is not None:
        return not_issued_distribution(reason, event=receipt.event), reason
    parts = receipt.snapshot
    if parts is not None and parts.distribution is not None:
        return dict(parts.distribution), None
    p = receipt.forecast.get("p")
    return binary_distribution(float(p if p is not None else receipt.p), event=receipt.event), None


def receipt_bodies(receipt: Any, issued: str, recorded_as_of: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """The receipt's ``forecast`` and ``versions`` bodies with the snapshot added.

    Never raises: a snapshot that cannot be built leaves the bodies as the producer wrote them, with an
    ``error`` marker in place of the snapshot, so an enrichment failure can never cost the receipt itself.
    Keys the producer already wrote are never replaced."""

    forecast = dict(receipt.forecast)
    versions = dict(receipt.versions or {})
    try:
        built = snapshot(receipt, issued, recorded_as_of)
        named, reason = distribution(receipt)
    except Exception as exc:  # noqa: BLE001 - metadata must never cost the receipt
        logger.warning("prediction snapshot not built for %s", receipt.receipt_key, exc_info=True)
        versions.setdefault("snapshot", {"schema": SNAPSHOT_SCHEMA, "error": type(exc).__name__})
        return forecast, versions
    forecast.setdefault("distribution", named)
    if reason is not None:
        forecast.setdefault("reason", reason)
    versions.setdefault("snapshot", built)
    return forecast, versions


def voi_snapshot(*, site: str, forecast: Mapping[str, Any], columns: Mapping[str, Any],
                 forecast_version: str) -> dict[str, Any]:
    """``versions_json.snapshot`` of a native ``voi_forecasts`` body (it has no ``inputs_as_of``).

    The target is the chosen check's next emission: its item, learning object and anchor (the presentation or
    the probe episode); the distribution is the body's ``predicted_outcomes`` over its emission alphabet,
    marked as never administered when the body describes the ranking's nominal best rather than a committed
    check (a stop, an abstention)."""

    members = []
    if columns.get("chosen_practice_item_id"):
        members.append(TargetMember(MEMBER_ITEM, str(columns["chosen_practice_item_id"])))
    if columns.get("learning_object_id"):
        members.append(TargetMember(MEMBER_LEARNING_OBJECT, str(columns["learning_object_id"])))
    target_block: dict[str, Any]
    if members:
        anchor = next(((kind, str(columns[name])) for kind, name in (
            ("presentation", "presentation_id"), ("probe_episode", "probe_episode_id"),
            ("scheduler_candidate", "scheduler_candidate_id"), ("source_attempt", "source_attempt_id"))
            if columns.get(name)), (None, None))
        target = PredictionTarget(
            kind="check_outcome", members=tuple(members), unit="emission",
            event_version=forecast_version, resolver_version=f"voi_forecast_report@{UNVERSIONED}",
            action_kind=site, action_id=None if forecast.get("chosen_ref") is None else str(forecast["chosen_ref"]),
            horizon_kind="next_observation", anchor_kind=anchor[0], anchor_id=anchor[1])
        target_block = {"target": target.to_dict(), "target_hash": target.target_hash(), "stated_by": "writer",
                        "unversioned": ["resolver_version"], "absent": None}
    else:
        target_block = {"target": None, "target_hash": None, "stated_by": None, "unversioned": [],
                        "absent": "the forecast names no item or learning object"}
    predicted = forecast.get("predicted_outcomes")
    administered = forecast.get("forecast_of") == "committed"
    if isinstance(predicted, Mapping) and predicted:
        named: dict[str, Any] = {"unit": "emission", "outcomes": {str(k): v for k, v in predicted.items()},
                                 "source": "forecast.predicted_outcomes", "administered": administered,
                                 "reason": None}
    else:
        named = {"unit": "emission", "outcomes": None, "source": None, "administered": administered,
                 "reason": str(forecast.get("reason") or forecast.get("verdict") or "no_forecast")}
    return {
        "schema": SNAPSHOT_SCHEMA,
        "cutoff": {"cutoff": None,
                   "absent": "a value-of-information site does not state the evidence cutoff it read under",
                   "source": None, "inputs_as_of": {"original": None, "recorded": None, "status": AS_OF_UNKNOWN}},
        "target": target_block,
        "distribution": named,
        "provenance": {"site": site, "forecast_version": forecast_version,
                       "parameters": "parameters_json (each with its provenance)"},
    }


__all__ = [
    "AS_OF_EXACT",
    "AS_OF_INVALID",
    "AS_OF_UNKNOWN",
    "SNAPSHOT_SCHEMA",
    "SnapshotParts",
    "UNIT_BINARY",
    "UNVERSIONED",
    "as_of_status",
    "binary_distribution",
    "categorical_distribution",
    "distribution",
    "not_issued_distribution",
    "receipt_bodies",
    "receipt_target",
    "snapshot",
    "voi_snapshot",
]

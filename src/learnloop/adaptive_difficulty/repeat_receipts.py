"""The predecessor's prediction on a repeat presentation (evidence packets spec §7.7.3 item 1, §7.7.5).

AD's serve hook (:mod:`learnloop.adaptive_difficulty.serve`) writes the ``ad_threshold@*`` receipts and the frozen
``item_serve_inputs`` row only for a never-attempted item. When an item is served again nothing recorded what the
model would have predicted, so the memory successor (``spec_ad_memory_v1.md``, ADM2a) would have no predecessor
predictions on repeats to be compared with. At every eligible plan presentation of an item that WAS attempted
before (the hook's own freshness test, ``serve_inputs.never_attempted``, false), this module states:

* ``ad_threshold_repeat@subject``: the subject view's prediction, the bank's mixture (``ad_threshold@subject``'s
  computation);
* ``ad_threshold_repeat@lo``: the item's learning-object view (``ad_threshold@lo``'s computation),

each with the three category probabilities (``predict.category_mixture``: category 2 is ``p̄`` to the bit) and the
inputs the predecessor read, in ``inputs_json`` (:data:`INPUTS_SCHEMA`): the resolved features, every signal with
its availability and reason (an unavailable signal is recorded unavailable, never as a default), whether the
prediction read it, the loadings, warmth and the exposure it came from, the state hash, pre-exposure, the item
revision and its surface group with the field the key came from as served, the item's and its surface group's
earlier attempts (the last of each, with ids and times), the delay's kind and what is known of its assignment,
and the predecessor's memory assumptions (:data:`PREDECESSOR_MEMORY`).

**Evaluation-only.** Nothing reads these receipts to decide anything: the names keep them out of ``z_v1``'s filter
(item scope, ``llm_v1``), the inputs stay out of ``item_serve_inputs`` (which replay and the scorer read), and
:func:`repeat_receipts` writes nothing (``serve_inputs.build_row`` writes a revision snapshot and is not called
here; its pure parts, ``signal_vector``, ``feature_inputs`` and ``pre_exposed``, are). The scorer reads every
``item_unassisted_success`` receipt, so these get the row the presentation's attempt gets under the existing
rules (``excluded`` for a repeat surface), as the in-process forecasters' repeat receipts already do.

**Ids** come from :func:`new_receipt_id`, a stream of their own (``ids.UlidStream``): the router's decision id,
and so its draw's seed, is the next ``ids.new_ulid``, which every row drawn from that stream would shift.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from learnloop.clock import parse_utc
from learnloop.ids import UlidStream
from learnloop.scheduling.forecast_receipts import ITEM_UNASSISTED_SUCCESS, ForecastReceipt
from learnloop.scheduling.voi_forecasts import parameter

from learnloop.adaptive_difficulty import predict as PR
from learnloop.adaptive_difficulty import priors as P
from learnloop.adaptive_difficulty import replay as RP
from learnloop.adaptive_difficulty import selection as S
from learnloop.adaptive_difficulty.logs import warn_failure

LOG = logging.getLogger(__name__)

REPEAT_SUBJECT = "ad_threshold_repeat@subject"
REPEAT_LO = "ad_threshold_repeat@lo"
REPEAT_FORECASTERS = (REPEAT_SUBJECT, REPEAT_LO)
REPEAT_VERSION = "ad-threshold-repeat-v1"
INPUTS_SCHEMA = "ad_repeat_inputs_v1"
#: ``router_objective.checks.ORIGIN``, restated (an AD module imports nothing of the router's; a test pins the two).
RANDOMIZED_CHECK_ORIGIN = "randomized_check"

#: What the predecessor assumes about memory, so a comparison names what it compares against. Versioned with the
#: receipt: a change to the predecessor's treatment of repeats is a new version here.
PREDECESSOR_MEMORY: Mapping[str, Any] = {
    "version": "ad_predecessor_memory_v1",
    "item_memory": "none: no item or surface-group memory term; the item residual is integrated out as "
                   "(A*TAU0)^2 at every presentation, a repeat's included",
    "residual_variance": (P.A * P.TAU0) ** 2,
    "repeat_measurement": "none: a repeat of a surface group is excluded from the update (repeat_surface, D10)",
    "transfer_increment": "gamma once per surface group, at its first graded attempt",
    "forgetting": "no decay of the mean; cell variance drifts per day",
    "warmth": {"form": "exp(-hours since the learning object's last exposure / WARMTH_HOURS)",
               "hours": P.WARMTH_HOURS},
}

_RECEIPT_IDS = UlidStream()


def new_receipt_id() -> str:
    """A repeat receipt's id, from this module's own stream (never ``ids.new_ulid``: module docstring)."""

    return _RECEIPT_IDS()


def _at_or_before(value: Any, served_at: str) -> bool:
    # The freshness test's boundary (``serve_inputs._before``): an attempt at the serve's own instant makes the
    # item a repeat, so it is one of the repeat's earlier attempts too.
    stamp = parse_utc(str(value)) if value else None
    served = parse_utc(served_at)
    return stamp is not None and served is not None and stamp <= served


def _hours(earlier: Any, served_at: str) -> float | None:
    try:
        return round((RP.days(served_at) - RP.days(earlier)) * 24.0, 8)
    except (TypeError, ValueError):
        return None


def _attempt_entry(row: Mapping[str, Any], served_at: str) -> dict[str, Any]:
    return {"attempt_id": str(row["id"]), "at": row.get("created_at"), "hours_before_serve": _hours(
        row.get("created_at"), served_at), "practice_item_id": str(row.get("practice_item_id")),
        "attempt_type": row.get("attempt_type"), "plan_presentation_id": row.get("plan_presentation_id"),
        "correctness": row.get("correctness"), "hints_used": row.get("hints_used"), "primed": row.get("primed")}


def memory_context(connection: Any, view: Any, item: Any, served: Any, served_at: str) -> dict[str, Any]:
    """The item's and its surface group's earlier attempts, read through the serve's material view.

    The served item's group is its group AS SERVED (``served``: the key and the field it came from); another
    item's group is read off that item as it stands at the serve (the replay's ``surface_group``; an item no
    longer in the vault is its own group, ``item:<id>``)."""

    groups: dict[str, str] = {}

    def group_of(item_id: str) -> str:
        if item_id not in groups:
            found = view.item(item_id)
            groups[item_id] = RP.surface_group(found) if found is not None else f"item:{item_id}"
        return groups[item_id]

    item_id = str(item.id)
    key = served.surface_key if served is not None else RP.surface_group(item)
    groups[item_id] = key
    own: list[Mapping[str, Any]] = []
    group: list[Mapping[str, Any]] = []
    for row in view.attempts(connection):
        if not _at_or_before(row.get("created_at"), served_at):
            continue
        other = str(row.get("practice_item_id"))
        if other == item_id:
            own.append(row)
            group.append(row)
        elif group_of(other) == key:
            group.append(row)
    siblings = [row for row in group if str(row.get("practice_item_id")) != item_id]
    reveals = [row for row in view.reveals(connection) if str(row.get("practice_item_id") or "") == item_id
               and _at_or_before(row.get("created_at"), served_at)]
    singleton = (served.surface_source if served is not None else None) == "item" or key == f"item:{item_id}"
    return {
        "boundary": "attempts at or before the serve (the freshness test's boundary)",
        "item": {"attempts": len(own), "last": _attempt_entry(own[-1], served_at) if own else None},
        "surface_group": {
            "key": key, "source": served.surface_source if served is not None else None, "singleton": singleton,
            "attempts": len(group), "items_attempted": len({str(r.get("practice_item_id")) for r in group}),
            "sibling_attempts": len(siblings),
            "last": _attempt_entry(group[-1], served_at) if group else None,
            "last_sibling": _attempt_entry(siblings[-1], served_at) if siblings else None,
        },
        "item_reveals": {"count": len(reveals), "last": {"reveal_id": str(reveals[-1]["id"]),
                                                         "at": reveals[-1].get("created_at"),
                                                         "amount": reveals[-1].get("amount")} if reveals else None},
        # The cases a memory comparison stratifies by (spec_ad_memory_v1 §9): a repeat is always the same item;
        # its group is the item alone, a family whose other items were practised, or a family met only here.
        "case": {"item": "practised",
                 "group": "singleton" if singleton else (
                     "family_siblings_practised" if siblings else "family_item_only")},
    }


def last_exposure(connection: Any, view: Any, learning_object_id: str, served_at: str) -> dict[str, Any]:
    """The exposure warmth is computed from: the learning object's latest attempt, reveal or reading opportunity
    strictly before the serve, in ``serving._warmth``'s order and comparison (the first of equal times wins)."""

    served = RP.days(served_at)
    latest: tuple[float, dict[str, Any]] | None = None
    candidates: list[tuple[Any, str, Any]] = []
    candidates += [(row.get("created_at"), "attempt", row.get("id")) for row in view.attempts(connection)
                   if str(row.get("learning_object_id")) == str(learning_object_id)]
    candidates += [(row.get("created_at"), "reveal", row.get("id")) for row in view.reveals(connection)
                   if str(row.get("learning_object_id")) == str(learning_object_id)]
    candidates += [(row.get("source_written_at"), f"reading:{row.get('kind')}", row.get("id"))
                   for row in view.reading_opportunities(connection, learning_object_ids=[learning_object_id])]
    for stamp, kind, ref in candidates:
        try:
            value = RP.days(stamp)
        except (TypeError, ValueError):
            continue
        if value < served and (latest is None or value > latest[0]):
            latest = (value, {"id": None if ref is None else str(ref), "at": stamp, "kind": kind})
    if latest is None:
        return {"available": False, "why": "no_exposure_before_serve"}
    return {"available": True, **latest[1], "hours_before_serve": round((served - latest[0]) * 24.0, 8)}


def delay_context(connection: Any, view: Any, presentation_id: str, memory: Mapping[str, Any],
                  served_at: str) -> dict[str, Any]:
    """Whether the repeat's delay was chosen by the plan's policy (natural) or by a randomized check, and what
    is known at the serve of the probability of its assignment."""

    row = view.presentation(connection, presentation_id) or {}
    origin = row.get("origin")
    randomized = origin == RANDOMIZED_CHECK_ORIGIN
    decision = row.get("router_decision_id")
    item_last = (memory.get("item") or {}).get("last") or {}
    group_last = (memory.get("surface_group") or {}).get("last") or {}
    return {
        "kind": "randomized_check" if randomized else "natural",
        "origin": origin, "block_id": row.get("block_id"), "router_decision_id": decision,
        "scheduler_candidate_id": row.get("scheduler_candidate_id"),
        "hours_since_item_attempt": item_last.get("hours_before_serve"),
        "hours_since_group_attempt": group_last.get("hours_before_serve"),
        # The router's propensities live in ``router_decisions`` (and a check's in its assignment), tables outside
        # AD's protection registry: the serve's AD operation may not read them, so they are named, not copied.
        "assignment_propensity": {
            "value": None, "available": False,
            "why": ("not_readable_in_ad_operation: the router decision's propensity is in router_decisions"
                    if decision else "no_router_decision: no router decision placed this presentation")},
        "redraw_probability": {
            "value": None, "available": False,
            "why": ("not_recorded_at_serve: a check's redraw is in its assignment" if randomized
                    else "not_applicable: only a randomized check is redrawn")},
    }


def _signals(vector: Mapping[str, Any], read: Mapping[str, float]) -> dict[str, Any]:
    out = {}
    for name, entry in vector.items():
        record = dict(entry) if isinstance(entry, Mapping) else {"value": entry}
        record["read_by_prediction"] = name in read
        if name not in read and record.get("available"):
            # Available but not in the predecessor's served prediction: z_v1 enters only the outside arm.
            record["not_read_because"] = "outside_arm_only" if name == "z_v1" else "not_in_spec"
        out[name] = record
    return out


def shared_inputs(item: Any, *, content_hash: str, state_hash: str, features: Mapping[str, Any],
                  recalibration: str, warmth: float, exposure: Mapping[str, Any], pre_exposed: bool,
                  memory: Mapping[str, Any], delay: Mapping[str, Any], coupling: Mapping[str, Any]) -> dict[str, Any]:
    """The part of a repeat receipt's ``inputs_json`` both views share, from values already read (no read, no
    write): the assembly is apart from every read so the shape is testable, and pinned, with plain values."""

    from learnloop.adaptive_difficulty.serve_inputs import RESOLUTION_VERSION

    surface = memory["surface_group"]
    return {
        "schema": INPUTS_SCHEMA,
        # Read at the serve and written with it: unlike a repeat replay resolves later from history.
        "inputs_kind": "frozen_at_serve",
        "practice_item_id": str(item.id), "learning_object_id": item.learning_object_id,
        "item_revision": content_hash,
        "surface": {"key": surface["key"], "source": surface["source"], "singleton": surface["singleton"]},
        "state_hash": state_hash, "replay_version": RP.REPLAY_VERSION,
        "features": {**dict(features), "resolution_version": RESOLUTION_VERSION},
        "z_v1_recalibration": recalibration,
        "warmth": {"value": warmth, "last_exposure": dict(exposure)},
        "pre_exposed": bool(pre_exposed),
        "memory": dict(memory),
        "delay": dict(delay),
        "predecessor_memory": dict(PREDECESSOR_MEMORY),
        "coupling_versions": dict(coupling),
    }


def view_inputs(shared: Mapping[str, Any], *, view: str, mixture: str, vector: Mapping[str, Any],
                spec: Any) -> dict[str, Any]:
    """One view's ``inputs_json``: the shared part, every signal with its availability and whether this view's
    prediction read it, the values it read, and the loadings it used (none in a learning-object view)."""

    return {**dict(shared), "view": view, "mixture": mixture, "signals": _signals(vector, spec.signals),
            "signals_read": dict(spec.signals), "loadings": dict(spec.loadings)}


def build_receipt(name: str, *, item: Any, presentation_kind: str, presentation_id: str, served_at: str,
                  forecast: Mapping[str, Any], inputs: Mapping[str, Any], p: float | None, status: str,
                  parts: Any) -> ForecastReceipt:
    """One repeat receipt: kind ``item_unassisted_success``, bound to the presentation, keyed as AD's other
    serve-time receipts are (``forecasters.receipt_key``), so a second write of it is ignored."""

    from learnloop.adaptive_difficulty.forecasters import EVENT, receipt_key
    from learnloop.adaptive_difficulty.serving import THRESHOLD_VERSION

    return ForecastReceipt(
        receipt_key=receipt_key(presentation_kind, presentation_id, name), kind=ITEM_UNASSISTED_SUCCESS,
        forecaster=name, forecaster_version=f"{REPEAT_VERSION}:{P.PRIORS_VERSION}:{P.HYPER_VERSION}",
        scope="presentation", decision_kind="serve", binding_kind=presentation_kind, event=EVENT,
        forecast=forecast, inputs=inputs,
        parameters=[parameter("priors", P.PRIORS_VERSION, "structural", source="code")],
        versions={"forecaster": REPEAT_VERSION, "threshold": THRESHOLD_VERSION, "replay": RP.REPLAY_VERSION,
                  "memory_assumptions": PREDECESSOR_MEMORY["version"], **P.versions()},
        inputs_as_of=served_at, p=p,
        columns={"decision_ref": presentation_id, "practice_item_id": str(item.id),
                 "learning_object_id": item.learning_object_id, f"{presentation_kind}_id": presentation_id,
                 "status": status},
        snapshot=parts)


def _repeat_parts(parts: Any, *, inputs_ref: str, epoch: Any) -> Any:
    # ``threshold_parts`` names the presentation's ``item_serve_inputs`` row as its source; a repeat has none.
    source = {key: value for key, value in dict(parts.source or {}).items() if key != "item_serve_inputs"}
    source.update(repeat_inputs=inputs_ref, protection_epoch=epoch)
    provenance = {**dict(parts.provenance), "memory_assumptions": PREDECESSOR_MEMORY["version"],
                  "label_closure": "the presentation's bound attempt (AD's scorer); unanswered stays pending"}
    return replace(parts, source=source, provenance=provenance)


def _computed(vault: Any, repository: Any, connection: Any, item: Any, *, presentation_kind: str,
              presentation_id: str, served_at: str, view: Any) -> list[ForecastReceipt]:
    from learnloop.adaptive_difficulty.feature_audit import item_revision
    from learnloop.adaptive_difficulty.serve_inputs import feature_inputs, pre_exposed, signal_vector
    from learnloop.adaptive_difficulty.serving import THRESHOLD_VERSION, _no_loadings, _spec, _warmth, served_item
    from learnloop.adaptive_difficulty.snapshot_parts import threshold_snapshot

    lo = str(item.learning_object_id)
    snapshot = RP.snapshot(vault, repository, connection=connection, view=view)
    state_hash = snapshot.state_hash()
    spec = _spec(vault, connection, snapshot, item, served_at, view)
    warmth = _warmth(connection, view, lo, served_at)
    constants = S.constants_from_config(vault.config)
    served = served_item(vault, item)
    content_hash = item_revision(item)[0]
    vector, recalibration = signal_vector(connection, item, content_hash, served_at, view=view)
    memory = memory_context(connection, view, item, served, served_at)
    shared = shared_inputs(
        item, content_hash=content_hash, state_hash=state_hash,
        features=feature_inputs(connection, item, content_hash, served_at), recalibration=recalibration,
        warmth=warmth, exposure=last_exposure(connection, view, lo, served_at),
        pre_exposed=pre_exposed(repository, item, served_at, view=view, connection=connection), memory=memory,
        delay=delay_context(connection, view, presentation_id, memory, served_at),
        coupling=snapshot.events.structure.versions)
    out = []
    for name, state, mixture in ((REPEAT_SUBJECT, snapshot.subject, "bank"),
                                 (REPEAT_LO, snapshot.lo_view(lo), "lo_view")):
        item_spec = spec if state.subject_view else _no_loadings(spec)
        prediction = PR.predict(state, item_spec, warmth=warmth, band=constants.band)
        categories, parts = threshold_snapshot(
            served, name=name, mixture=mixture, state_hash=state_hash,
            categories_of=lambda state=state, item_spec=item_spec: PR.category_mixture(state, item_spec,
                                                                                         warmth=warmth),
            presentation_kind=presentation_kind, presentation_id=presentation_id, served_at=served_at,
            epoch=view.epoch, threshold_version=THRESHOLD_VERSION, replay_version=RP.REPLAY_VERSION)
        if parts is not None:
            parts = _repeat_parts(parts, inputs_ref="inputs_json", epoch=view.epoch)
        inputs = view_inputs(shared, view="subject" if state.subject_view else RP.lo_view_name(lo),
                             mixture=mixture, vector=vector, spec=item_spec)
        out.append(build_receipt(
            name, item=item, presentation_kind=presentation_kind, presentation_id=presentation_id,
            served_at=served_at, inputs=inputs, p=prediction.p_bar, status="ok", parts=parts,
            forecast={"p": round(prediction.p_bar, 8), "event": "unassisted_success", "p_categories": categories,
                      "p_band": round(prediction.p_band, 8)}))
    return out


def _failed(item: Any, error: BaseException, *, presentation_kind: str, presentation_id: str, served_at: str,
            epoch: Any) -> list[ForecastReceipt]:
    """The two receipts as failed forecasts: issued at the serve, no ``p``, the error's type as the reason."""

    from learnloop.db.evidence_cutoff import Cutoff
    from learnloop.scheduling.prediction_snapshots import SnapshotParts

    reason = f"compute_failed:{type(error).__name__}"
    parts = SnapshotParts(cutoff=Cutoff.ad_replay(None),
                          source={"protection_epoch": epoch, "failure": reason},
                          provenance={"memory_assumptions": PREDECESSOR_MEMORY["version"], "model_call": None})
    return [build_receipt(name, item=item, presentation_kind=presentation_kind, presentation_id=presentation_id,
                     served_at=served_at, p=None, status="failed", parts=parts,
                     forecast={"p": None, "event": "unassisted_success", "p_categories": None, "reason": reason},
                     inputs={"schema": INPUTS_SCHEMA, "practice_item_id": str(item.id),
                             "learning_object_id": item.learning_object_id, "failure": reason})
            for name in REPEAT_FORECASTERS]


def repeat_receipts(vault: Any, repository: Any, connection: Any, item: Any, *, presentation_kind: str,
                    presentation_id: str, served_at: str, view: Any) -> tuple[list[ForecastReceipt], str | None]:
    """The two repeat receipts of one presentation, and why none when there are none. Writes nothing.

    Below AD's successor (where no threshold forecast is made either) there are none (``below_successor``). A
    computation that fails yields the two receipts as failed forecasts with the reason; a refusal of AD's guard
    is raised (the serve's whole AD record then rolls back, as for any refusal in it: a receipt is never forced
    past the guard)."""

    from learnloop.adaptive_difficulty.operation import is_denial
    from learnloop.adaptive_difficulty.successor import successor_active

    if not successor_active(vault.config):
        return [], "below_successor"
    try:
        return _computed(vault, repository, connection, item, presentation_kind=presentation_kind,
                         presentation_id=presentation_id, served_at=served_at, view=view), None
    except Exception as exc:  # noqa: BLE001 - an evaluation receipt never costs the serve
        if is_denial(exc):
            raise
        warn_failure(LOG, "repeat receipts for presentation %s not computed", presentation_id)
        return _failed(item, exc, presentation_kind=presentation_kind, presentation_id=presentation_id,
                       served_at=served_at, epoch=view.epoch), None


__all__ = [
    "INPUTS_SCHEMA",
    "PREDECESSOR_MEMORY",
    "RANDOMIZED_CHECK_ORIGIN",
    "REPEAT_FORECASTERS",
    "REPEAT_LO",
    "REPEAT_SUBJECT",
    "REPEAT_VERSION",
    "build_receipt",
    "delay_context",
    "last_exposure",
    "memory_context",
    "new_receipt_id",
    "repeat_receipts",
    "shared_inputs",
    "view_inputs",
]

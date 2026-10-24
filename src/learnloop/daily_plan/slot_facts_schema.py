"""The facts the plan hands adaptive difficulty's slot, and their wire format (the final round: inversion).

A neutral module (it imports only the standard library). The plan computes its verdicts about a
slot BEFORE AD decides, outside any AD operation, exactly as it would with AD off
(``daily_plan.slot_facts``), and hands AD only this record, JSON-encoded: item ids, reason codes
from a closed vocabulary, numbers and timestamps. AD decodes it here against the schema
(:func:`decode`): an unknown or missing key, a wrong type, a non-finite number or a bad timestamp is
refused; every item id is projected onto the items AD's own view shows; every reason maps onto
:data:`CONSTRAINT_CODES` / :data:`POOL_CODES` (an unknown one becomes ``…:other``, still a refusal).
No free text, no object and no exception can cross, whatever the plan computes.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

VERSION = "slot_facts_v1"

#: The staged frame's constraint keys (``scheduling.constraint_engine``'s registered constraints and
#: the frame's own fail-closed keys); ``tests/test_ad23_inversion.py`` checks it against the code.
CONSTRAINT_CODES: frozenset[str] = frozenset({
    "active_status", "stimulus_renderable", "purpose_compatibility", "hard_exposure_collision",
    "assessment_reservation", "fatigue_budget", "same_facet_dispersion", "stage_interleaving",
    "controller_ownership", "constraints_unavailable", "build_admission", "refused", "other",
})
#: The plan pool's per-item predicate's reasons (``serving_exclusions.ADMISSION_GATES``, DL2's intent
#: gate's ``intent_*`` codes, the probe gates); checked against the code by the same test.
POOL_CODES: frozenset[str] = frozenset({
    "retired", "inactive_state", "reserved_exam", "held_out_material", "rung_variant_hold", "staged_owned",
    "diagnostic_microprobe", "diagnostic_probe_administered", "unservable_stimulus", "no_learning_object",
    "lifecycle_put_away", "diagnostic_freshness_reserve", "placement_assumed_withheld",
    "placement_maintained_withheld", "cold_start_unattempted", "voi_value_below_minutes_cost",
    "diagnostic_reserved", "intent_paused", "intent_reference_only", "intent_stopped", "intent_satisfied",
    "intent_check_waiting", "intent_check_reserved", "intent_check_held", "intent_check_refused",
    "probe_not_selected", "unknown_item", "other",
})
#: The routine exclusions AD's check 0 honours (``serving_exclusions.ServingExclusions``' sets).
EXCLUSION_NAMES: tuple[str, ...] = (
    "reserved_exam_item_ids", "held_out_item_ids", "rung_variant_hold_ids", "staged_owned_item_ids",
    "cold_check_reserved_item_ids", "revealed_recently_item_ids",
)
#: The plan's budget numbers AD's checks 3 and 4 use.
BUDGET_FIELDS: tuple[str, ...] = (
    "slack_minutes", "horizon_days", "reviews_per_new_item", "ceiling_minutes", "load_per_day",
    "floor_or_override",
)
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:\-]{0,127}$")


class SlotFactsError(ValueError):
    """The wire record does not satisfy the schema (AD is unavailable for the slot)."""


@dataclass(frozen=True)
class SlotInputs:
    """What AD's phase 1 hands the plan (AD to the incumbent): the candidates AD's view shows (the
    slot item and its never-attempted visible siblings at its capability, or the deferred items),
    their learning objects and AD's estimates, the item states as AD's view reads them and the
    reveals the view withholds."""

    candidate_ids: tuple[str, ...]
    learning_objects: Mapping[str, str]
    est_minutes: Mapping[str, float]
    item_states: Mapping[str, Any]
    withheld_reveal_ids: frozenset[str]
    slot_visible: bool = True


@dataclass(frozen=True)
class SlotFacts:
    """The plan's verdicts on one slot (``kind = "slot"``) or on the boundary's AD deferrals
    (``kind = "deferrals"``, the slot fields None)."""

    kind: str
    now: str
    plan_id: str
    members: tuple[str, ...]
    refusals: Mapping[str, tuple[str, ...]]
    cold_items: tuple[str, ...] | None
    reserved_items: tuple[str, ...]
    exclusions: Mapping[str, tuple[str, ...]]
    slot_admitted: bool = True
    block_id: str | None = None
    position: int | None = None
    slot_item_id: str | None = None
    slot_learning_object_id: str | None = None
    slot_est_minutes: float | None = None
    planned_counts: Mapping[str, int] = field(default_factory=dict)
    budget: Mapping[str, Any] = field(default_factory=dict)
    router_decision_id: str | None = None
    router_propensity: float = 1.0
    version: str = VERSION


_KEYS = ("kind", "now", "plan_id", "members", "refusals", "cold_items", "reserved_items", "exclusions",
         "slot_admitted", "block_id", "position", "slot_item_id", "slot_learning_object_id", "slot_est_minutes",
         "planned_counts", "budget", "router_decision_id", "router_propensity", "version")


def code_for(prefix: str, raw: Any) -> str:
    """A refusal's code in the closed vocabulary (``constraint:<key>`` or ``pool:<reason>``)."""

    vocabulary = CONSTRAINT_CODES if prefix == "constraint" else POOL_CODES
    name = str(raw) if isinstance(raw, str) else "other"
    return f"{prefix}:{name if name in vocabulary else 'other'}"


def encode(facts: SlotFacts) -> str:
    """Canonical JSON (sorted keys)."""

    body = {
        "kind": facts.kind, "now": facts.now, "plan_id": facts.plan_id, "members": list(facts.members),
        "refusals": {k: list(v) for k, v in facts.refusals.items()},
        "cold_items": None if facts.cold_items is None else list(facts.cold_items),
        "reserved_items": list(facts.reserved_items),
        "exclusions": {k: list(v) for k, v in facts.exclusions.items()},
        "slot_admitted": bool(facts.slot_admitted), "block_id": facts.block_id, "position": facts.position,
        "slot_item_id": facts.slot_item_id, "slot_learning_object_id": facts.slot_learning_object_id,
        "slot_est_minutes": facts.slot_est_minutes, "planned_counts": dict(facts.planned_counts),
        "budget": dict(facts.budget), "router_decision_id": facts.router_decision_id,
        "router_propensity": facts.router_propensity, "version": facts.version,
    }
    return json.dumps(body, sort_keys=True, allow_nan=False, separators=(",", ":"))


def _id(value: Any, what: str) -> str:
    if not isinstance(value, str) or not _ID.match(value):
        raise SlotFactsError(f"{what}: not an id")
    return value


def _optional_id(value: Any, what: str) -> str | None:
    return None if value is None else _id(value, what)


def _number(value: Any, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(float(value)):
        raise SlotFactsError(f"{what}: not a finite number")
    return float(value)


def _items(value: Any, what: str, visible: frozenset[str]) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise SlotFactsError(f"{what}: not a list")
    return tuple(sorted({_id(item, what) for item in value} & visible))


def decode(wire: str, *, visible: Iterable[str], learning_objects: Iterable[str] = ()) -> SlotFacts:
    """The facts as AD may read them: schema-checked, every item id projected onto ``visible`` (the
    items AD's own view shows), the slot's LO id onto ``learning_objects`` (those AD's own phase 1
    saw), every reason in the closed vocabulary."""

    visible_ids = frozenset(str(item) for item in visible)
    known_los = frozenset(str(lo) for lo in learning_objects)
    try:
        body = json.loads(wire, parse_constant=lambda name: (_ for _ in ()).throw(SlotFactsError(name)))
    except SlotFactsError:
        raise
    except Exception:  # noqa: BLE001 - not JSON: refused, with no detail carried
        body = None
    if not isinstance(body, dict):
        raise SlotFactsError("not a facts record")
    if set(body) != set(_KEYS):
        raise SlotFactsError("unknown or missing keys")
    if body["version"] != VERSION or body["kind"] not in ("slot", "deferrals"):
        raise SlotFactsError("version or kind")
    now = body["now"]
    if not isinstance(now, str) or len(now) > 40:
        raise SlotFactsError("now: not an ISO timestamp")
    valid_now = True
    try:
        datetime.fromisoformat(now.replace("Z", "+00:00"))
    except ValueError:
        valid_now = False
    if not valid_now:
        raise SlotFactsError("now: not an ISO timestamp")
    refusals_raw = body["refusals"]
    if not isinstance(refusals_raw, dict):
        raise SlotFactsError("refusals: not a mapping")
    refusals: dict[str, tuple[str, ...]] = {}
    for item_id, codes in refusals_raw.items():
        _id(item_id, "refusals")
        if not isinstance(codes, list):
            raise SlotFactsError("refusals: not a list")
        mapped = []
        for code in codes:
            prefix, _sep, name = str(code).partition(":") if isinstance(code, str) else ("pool", "", "other")
            mapped.append(code_for("constraint" if prefix == "constraint" else "pool", name))
        if item_id in visible_ids:
            refusals[item_id] = tuple(mapped)
    cold_raw = body["cold_items"]
    exclusions_raw = body["exclusions"]
    if not isinstance(exclusions_raw, dict) or set(exclusions_raw) - set(EXCLUSION_NAMES):
        raise SlotFactsError("exclusions: unknown sets")
    planned_raw = body["planned_counts"]
    if not isinstance(planned_raw, dict):
        raise SlotFactsError("planned_counts: not a mapping")
    planned = {}
    for item_id, count in planned_raw.items():
        _id(item_id, "planned_counts")
        if isinstance(count, bool) or not isinstance(count, int):
            raise SlotFactsError("planned_counts: not a count")
        if item_id in visible_ids:
            planned[item_id] = int(count)
    budget_raw = body["budget"]
    if not isinstance(budget_raw, dict) or set(budget_raw) - set(BUDGET_FIELDS):
        raise SlotFactsError("budget: unknown fields")
    budget: dict[str, Any] = {}
    for name, value in budget_raw.items():
        budget[name] = bool(value) if name == "floor_or_override" and isinstance(value, bool) else _number(value, name)
    position = body["position"]
    if position is not None and (isinstance(position, bool) or not isinstance(position, int)):
        raise SlotFactsError("position: not an integer")
    slot_est = body["slot_est_minutes"]
    if not isinstance(body["slot_admitted"], bool):
        raise SlotFactsError("slot_admitted: not a boolean")
    slot_item = _optional_id(body["slot_item_id"], "slot_item_id")
    return SlotFacts(
        kind=body["kind"],
        now=now,
        plan_id=_id(body["plan_id"], "plan_id"),
        members=_items(body["members"], "members", visible_ids),
        refusals=refusals,
        cold_items=None if cold_raw is None else _items(cold_raw, "cold_items", visible_ids),
        reserved_items=_items(body["reserved_items"], "reserved_items", visible_ids),
        exclusions={name: _items(exclusions_raw.get(name, []), name, visible_ids) for name in EXCLUSION_NAMES},
        slot_admitted=body["slot_admitted"],
        block_id=_optional_id(body["block_id"], "block_id"),
        position=position,
        slot_item_id=slot_item if slot_item is None or slot_item in visible_ids else None,
        slot_learning_object_id=(lo if (lo := _optional_id(body["slot_learning_object_id"], "slot_learning_object_id"))
                                 in known_los else None),
        slot_est_minutes=None if slot_est is None else _number(slot_est, "slot_est_minutes"),
        planned_counts=planned,
        budget=budget,
        router_decision_id=_optional_id(body["router_decision_id"], "router_decision_id"),
        router_propensity=_number(body["router_propensity"], "router_propensity"),
    )


def exclusion_sets(facts: SlotFacts) -> Any:
    """The routine exclusions as AD's check 0 reads them (``ServingExclusions``' attribute names)."""

    from types import SimpleNamespace

    return SimpleNamespace(**{name: frozenset(facts.exclusions.get(name, ())) for name in EXCLUSION_NAMES})


__all__ = ["BUDGET_FIELDS", "CONSTRAINT_CODES", "EXCLUSION_NAMES", "POOL_CODES", "SlotFacts", "SlotFactsError",
           "SlotInputs", "VERSION", "code_for", "decode", "encode", "exclusion_sets"]

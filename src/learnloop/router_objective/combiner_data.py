"""The follow-up batch, item 2 (RO4's item 6): the memory combiner's outcomes from the traces.

RO4 froze each candidate topic's sensors in its decision's trace (AD's predictive ``η`` on the logit scale, the FSRS
stability and days since the last review of its practised items, whether it was practised) and fed the combiner
nothing; RO5 fed it its randomized checks. Here each traced ``plan_block`` decision's frozen sensors are joined to the
first resolved cold outcome on the topic after the decision's block, by RO2's versioned resolver
(``adaptive_difficulty.history_resolve.resolve_curves``, handed in: this package sits below adaptive difficulty's
importers), so the combiner is refitted, with its labelled prior, on every outcome the log holds.

**The join** (:data:`JOIN_VERSION`):

* a decision whose drawn option served a block (its first plan presentation names the block; a drawn stop serves
  none, so it joins nothing);
* every topic whose sensors the trace froze **except the drawn option's own topics**: the block acted on those, so
  their later outcome measures the action's effect (``γ``, the effect slopes), not the memory forecast the combiner
  calibrates. On every other topic nothing happened between the sensors and the block's end;
* RO2's **per-protocol** binding only (the first qualifying outcome with no exposure to the topic in between, the
  event the forecast describes; RO2's label, so help or a primed reveal is a failure, an ungraded answer is passed
  over); natural checks are selected, so the rows are conditional on observation, which a forecast's calibration may
  use (§8.4: "forecast slopes can use resolved outcomes") and ``w`` never does;
* the row is ``(η, R, y)`` with ``R`` FSRS's retrievability at the realized lag (the stability frozen, the days since
  the last review plus the days from the decision to the outcome), ``None`` for an unpractised topic;
* one outcome counts once: an answer that is the first qualifying outcome after several decisions joins the latest
  of them (the freshest sensors), and an answer that is also a randomized check's is left to the check's row;
* **as of the decision** through the availability predicate: a trace written by then, its block served by then, an
  outcome known by then (``known_at``: received time at RO1's tag), so a backdated import is out until it arrived.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Collection, Mapping, Sequence
from datetime import datetime
import hashlib
import json
import threading
from typing import Any

from learnloop.clock import parse_utc

#: v1: the drawn block's untouched topics, RO2's per-protocol binding, one outcome once (latest decision).
JOIN_VERSION = "combiner_trace_join_v1"
FORECASTER = "memory_combiner_join"
_PER_PROTOCOL = "per_protocol"
#: The resolver scores a forecast curve; the join needs only the outcome and its lag, so it hands a flat curve.
_FLAT_CURVE = {"1": 0.5, "7": 0.5, "30": 0.5}


def _days(later: datetime, earlier: datetime) -> float:
    return max((later - earlier).total_seconds() / 86400.0, 0.0)


#: Router speed, item 2: each trace's untouched topics and their frozen sensors, parsed once per trace content
#: (:func:`_untouched`), keyed by a digest of the drawn option and the trace's whole JSON text, so a trace rewritten in
#: any byte is parsed again. Its bound is a keep bound (memory only: past it the oldest entry is parsed again on its
#: next read, never a different value).
_PARSED: dict[bytes, tuple[tuple[str, dict[str, Any]], ...]] = {}
_PARSED_LOCK = threading.Lock()
_PARSED_LIMIT = 4096


def _untouched(chosen: str, trace_json: str) -> tuple[tuple[str, dict[str, Any]], ...]:
    """The trace's topics with sensors frozen, except the drawn option's own, in id order with their sensor values
    (``eta``, ``stability``, ``elapsed``, ``practiced``): a pure function of the drawn option and the trace's text,
    held per content digest (router speed, item 2: the join parsed every plan-block trace's 13-31 KB at every call,
    about 2.4 calls a decision). The outcome side (presentations, resolution, received time, regrades, holds) is never
    held: :func:`groups` and :func:`rows` read it at every call."""

    key = hashlib.blake2b(f"{len(chosen)}:{chosen}:".encode("utf-8") + trace_json.encode("utf-8"),
                          digest_size=20).digest()
    with _PARSED_LOCK:
        held = _PARSED.get(key)
    if held is not None:
        return held
    candidates = json.loads(trace_json).get("candidates") or {}
    drawn = set(((candidates.get(chosen) or {}).get("sensors") or {}))
    sensors: dict[str, Mapping[str, Any]] = {}
    for entry in candidates.values():
        for lo, values in ((entry or {}).get("sensors") or {}).items():
            if lo == "llm_forecast" or lo in drawn or not isinstance(values, Mapping):
                continue
            if values.get("ad_eta") is None:
                continue
            sensors.setdefault(str(lo), values)
    parsed = tuple((lo, {"eta": float(values["ad_eta"]), "stability": float(values.get("fsrs_stability") or 0.0),
                         "elapsed": float(values.get("fsrs_elapsed_days") or 0.0),
                         "practiced": bool(values.get("practiced"))})
                   for lo, values in sorted(sensors.items()))
    with _PARSED_LOCK:
        while len(_PARSED) >= _PARSED_LIMIT:
            _PARSED.pop(next(iter(_PARSED)))
        _PARSED[key] = parsed
    return parsed


def groups(connection: Any, *, now: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """One resolvable group per (decision, untouched topic) as of ``now``, and the decisions joined nothing, by
    reason."""

    from learnloop.db.stores import router_objective as store

    if not store.table_present(connection, store.TRACES):
        return [], {}
    skipped: dict[str, int] = {}
    found: list[dict[str, Any]] = []
    # Router speed, item 2: each decision's first presentation served by ``now`` in one read (it was one query per
    # trace): the first row per decision in (served_at, id) order, as each query's ORDER BY ... LIMIT 1 took it.
    first_served: dict[str, str] = {}
    for served in connection.execute(
            "SELECT router_decision_id, id FROM plan_presentations WHERE router_decision_id IS NOT NULL "
            "AND served_at <= ? ORDER BY served_at, id", (now,)):
        first_served.setdefault(str(served[0]), str(served[1]))
    for row in connection.execute(
            "SELECT decision_id, chosen_ref, trace_json, created_at FROM router_objective_traces "
            "WHERE decision_kind = 'plan_block' AND created_at <= ? ORDER BY created_at, id", (now,)):
        untouched = _untouched(str(row["chosen_ref"]), str(row["trace_json"]))
        served_id = first_served.get(str(row["decision_id"]))
        if served_id is None:
            skipped["no_block_served"] = skipped.get("no_block_served", 0) + 1
            continue
        if not untouched:
            skipped["no_untouched_topic"] = skipped.get("no_untouched_topic", 0) + 1
            continue
        for lo, values in untouched:
            found.append({"plan_presentation_id": served_id, "learning_object_id": lo, "forecaster": FORECASTER,
                          "curve": dict(_FLAT_CURVE), "decision_id": str(row["decision_id"]),
                          "decided_at": str(row["created_at"]), "sensors": dict(values)})
    return found, skipped


def rows(connection: Any, resolved: Sequence[Mapping[str, Any]], *, now: str, known_at: Callable[[Mapping[str, Any]], Any],
         retrievability: Callable[[float, float], float], exclude: Collection[str] = ()) -> tuple[
             list[tuple[float, float | None, int]], dict[str, Any]]:
    """The combiner's ``(η, R or None, y)`` rows from the resolver's rows (``resolved``), as of ``now``; ``exclude``:
    attempt ids already counted (a randomized check's). Returns the rows and the join's counts."""

    scored = [row for row in resolved if row.get("binding") == _PER_PROTOCOL and row.get("status") == "scored"
              and row.get("attempt_id") and row.get("y") is not None]
    counts: dict[str, Any] = {"version": JOIN_VERSION, "groups": len({(row.get("decision_id"), row.get("learning_object_id"))
                                                                       for row in resolved
                                                                       if row.get("binding") == _PER_PROTOCOL}),
                              "scored": len(scored), "not_known_by_now": 0, "check_answers": 0, "duplicates": 0,
                              # every per-protocol row by its status and reason (why most natural outcomes join
                              # nothing: pending, or an intervening exposure)
                              "per_protocol": dict(sorted(Counter(
                                  f"{row.get('status')}:{row.get('reason') or ''}".rstrip(":") for row in resolved
                                  if row.get("binding") == _PER_PROTOCOL).items()))}
    ids = sorted({str(row["attempt_id"]) for row in scored})
    times: dict[str, Mapping[str, Any]] = {}
    for start in range(0, len(ids), 500):
        part = ids[start:start + 500]
        marks = ",".join("?" for _ in part)
        has_received = any(info[1] == "received_at" for info in connection.execute("PRAGMA table_info(practice_attempts)"))
        columns = "id, created_at" + (", received_at" if has_received else "")
        for found in connection.execute(f"SELECT {columns} FROM practice_attempts WHERE id IN ({marks})", part):
            times[str(found["id"])] = dict(found)
    moment = parse_utc(now)
    latest: dict[str, Mapping[str, Any]] = {}
    for row in scored:
        attempt_id = str(row["attempt_id"])
        attempt = times.get(attempt_id)
        known = known_at(attempt) if attempt is not None else None
        if attempt is None or not known or (moment is not None and (parse_utc(str(known)) or moment) > moment):
            counts["not_known_by_now"] += 1
            continue
        if attempt_id in exclude:
            counts["check_answers"] += 1
            continue
        held = latest.get(attempt_id)
        if held is not None:
            counts["duplicates"] += 1
            if str(held.get("decided_at")) >= str(row.get("decided_at")):
                continue
        latest[attempt_id] = {**row, "outcome_at": attempt["created_at"]}
    out: list[tuple[float, float | None, int]] = []
    for attempt_id in sorted(latest):
        row = latest[attempt_id]
        sensors = row.get("sensors") or {}
        decided, answered = parse_utc(str(row.get("decided_at"))), parse_utc(str(row.get("outcome_at")))
        lag = _days(answered, decided) if decided is not None and answered is not None else float(row.get("lag_days") or 0.0)
        r = (retrievability(float(sensors.get("stability") or 0.0), float(sensors.get("elapsed") or 0.0) + lag)
             if sensors.get("practiced") else None)
        out.append((float(sensors["eta"]), r, int(float(row["y"]) >= 0.5)))
    counts["rows"] = len(out)
    return out, counts


__all__ = ["FORECASTER", "JOIN_VERSION", "groups", "rows"]

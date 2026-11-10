"""Router objective RO2's versioned resolver for ``lo_cold_success`` (spec_router_objective_v1 §6.2).

One ``llm_history_v1`` call states ``p_cold_L`` for L in 1, 7, 30 days after its block: the probability
of a completed, unassisted attempt on an **unseen** item of the presentation's LO, at the board's
existing success threshold (AD §5.3's ``Y = 2``), had the learner no exposure to the LO in between.
The resolver gives two bindings of the same receipts:

* **per protocol** (``per_protocol``): the first qualifying outcome after the block, only if no
  exposure to the LO fell between the block and it; otherwise censored ``intervening_exposure``. The
  event the forecast describes: read for calibration;
* **intention to treat** (``intention_to_treat``): the first qualifying outcome after the block,
  whatever happened in between, with the intervening exposures, the outcome's help state and the
  attempts passed over recorded. Read for the paired comparison between forecasters on the same
  outcomes.

**The block** is the presentation's: it starts at the serve and ends at the latest attempt answering
any presentation of its block (the serve when none did). **A qualifying outcome** is an attempt on an
item of the LO the learner never attempted before, after the block, outside it, that AD's outcome
categories grade (``outcomes.category`` not None), scored by AD's binary event
(``outcomes.unassisted_success``): help, a reveal during it or an empty "stuck" answer make it a
failure, AD's censored category included (a correct answer whose help timing is unknown, a primed
answer revealed during its presentation: neither is an unassisted success; Codex review F4), its state
recorded (``outcome_state``); an excluded attempt (not graded, exposed before it was served) is passed
over and recorded. **An exposure to the LO** is any visible attempt on the LO, any reveal on it (a
lesson's or a tutor's teaching text reaches the ledger as reveals: the "intervening lesson" case) and
any learning opportunity on it from its **uncapped source events** (``reading_sources.listed_events``
through the material view, every one whether or not AD's sweep recorded a receipt for it: AD's dose caps,
one passage view per LO per day, bound a dose, never what coldness sees; Codex review F3), with AD's
reading receipts kept beside them (a receipt whose source was since deleted still stands).

**Scored at the realized lag** by interpolating the curve linearly in log time between the stated lags
(below the first lag the 1-day forecast stands). Past the last lag (30 days) the outcome is censored
``beyond_measured_lag`` until a longer lag is added; a block with no qualifying outcome yet is
``pending`` until then. **The two clocks**: time since the block, and delay since the latest exposure
to the LO before the outcome (the block's own attempt included).

Natural first checks are selected (whether and when one happens depends on the policy, the learner and
returning at all), so every row carries ``conditional_on_observation``: the intended lag estimand comes
from RO5's randomized checks. Pure reads through AD's material view; nothing is written.
"""

from __future__ import annotations

from learnloop.adaptive_difficulty.operation import entry

import math
from collections.abc import Mapping, Sequence
from typing import Any

from learnloop.clock import parse_utc, utc_now_iso
from learnloop.scheduling.forecast_receipts import LO_COLD_SUCCESS

from learnloop.adaptive_difficulty import outcomes as O
from learnloop.adaptive_difficulty.model import CENSORED

#: v2 (Codex review F3, F4): exposures from the uncapped source events; AD's censored category scored
#: by AD's binary event (a failure), not censored.
RESOLVER_VERSION = "ad-history-resolver-v2"
PER_PROTOCOL = "per_protocol"
INTENTION_TO_TREAT = "intention_to_treat"
BINDINGS = (PER_PROTOCOL, INTENTION_TO_TREAT)
#: The last lag asked (days): past it an outcome is censored ``beyond_measured_lag`` (structural: the
#: forecaster's own lags, ``history_forecast.LAGS``).
MAX_LAG_DAYS = 30.0


def _days(later: Any, earlier: Any) -> float | None:
    a, b = parse_utc(str(later)) if later else None, parse_utc(str(earlier)) if earlier else None
    if a is None or b is None:
        return None
    return (a - b).total_seconds() / 86400.0


def interpolate(curve: Mapping[str, Any], lag_days: float) -> float | None:
    """The curve's probability at ``lag_days``: linear in log time between the stated lags; the first
    lag's value below it; None past the last (censored ``beyond_measured_lag``)."""

    points = sorted((float(lag), float(p)) for lag, p in curve.items() if p is not None)
    if not points or lag_days > points[-1][0]:
        return None
    if lag_days <= points[0][0]:
        return points[0][1]
    for (lag0, p0), (lag1, p1) in zip(points, points[1:], strict=False):
        if lag0 <= lag_days <= lag1:
            weight = (math.log(lag_days) - math.log(lag0)) / (math.log(lag1) - math.log(lag0))
            return p0 + weight * (p1 - p0)
    return None  # pragma: no cover - the points cover the range


def _groups(receipts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """One forecast curve per presentation and forecaster (the receipts of one call)."""

    groups: dict[tuple[str, str], dict[str, Any]] = {}
    for receipt in receipts:
        if receipt.get("status") not in (None, "ok") or receipt.get("p") is None:
            continue
        forecast = receipt.get("forecast") or {}
        curve = forecast.get("curve")
        pid = receipt.get("plan_presentation_id")
        if not isinstance(curve, Mapping) or not pid:
            continue
        key = (str(pid), str(receipt["forecaster"]))
        groups.setdefault(key, {"plan_presentation_id": str(pid), "forecaster": str(receipt["forecaster"]),
                                "rung": forecast.get("rung"), "learning_object_id": receipt.get("learning_object_id"),
                                "curve": dict(curve), "receipt_ids": [],
                                "model": (receipt.get("versions") or {}).get("model"),
                                "prompt_version": (receipt.get("versions") or {}).get("prompt")})
        groups[key]["receipt_ids"].append(str(receipt["id"]))
    return list(groups.values())


class _Uncapped:
    """The material view as the reading collectors see it, with nothing on record: each source event is
    listed whether or not a sweep recorded (or a cap refused) its receipt. Every protection rule is the
    view's own (``rows``, ``question``, ``administration_item``...); only the receipt lookup differs."""

    def __init__(self, view: Any) -> None:
        self._view = view

    def __getattr__(self, name: str) -> Any:
        return getattr(self._view, name)

    def lookup(self, connection: Any, table: str, where: str, args: Any = (), *,
               stale_as_missing: bool = False) -> tuple[str, Any]:
        from learnloop.db.stores import ad_receipts as store

        if table == store.READING:
            return "missing", None
        return self._view.lookup(connection, table, where, args, stale_as_missing=stale_as_missing)


def _opportunities(connection: Any, vault: Any, repository: Any, view: Any, *, now: str) -> list[dict[str, Any]]:
    """Every learning opportunity on any LO up to ``now`` (``id``, ``learning_object_id``, ``at``): the
    uncapped source events and AD's receipts, one per source row and LO."""

    from learnloop.adaptive_difficulty.reading import VaultReadingMap
    from learnloop.reading_sources import listed_events, source_stamp

    upper = source_stamp(now) or now
    found: dict[tuple[str, str], dict[str, Any]] = {}
    for event in listed_events(connection, VaultReadingMap(vault, repository, view), None, upper, view=_Uncapped(view)):
        for lo in event.learning_object_ids:
            ref = f"{event.source_table}:{event.source_id}"
            found.setdefault((ref, str(lo)), {"id": ref, "learning_object_id": str(lo), "at": str(event.written_at),
                                              "subkind": event.subkind})
    for receipt in view.reading_opportunities(connection):
        ref = f"{receipt.get('source_table')}:{receipt.get('source_id')}"
        found.setdefault((ref, str(receipt.get("learning_object_id") or "")), {
            "id": ref, "learning_object_id": str(receipt.get("learning_object_id") or ""),
            "at": source_stamp(receipt.get("source_written_at")) or str(receipt.get("source_written_at") or ""),
            "subkind": receipt.get("subkind")})
    return list(found.values())


def _outcome_state(row: Mapping[str, Any], category: int) -> str:
    """The outcome's help state beside its binary label (spec §6.2: A4's states stay distinct)."""

    if category != CENSORED:
        return {2: "unassisted_success", 1: "partial_or_helped", 0: "failure"}.get(category, "failure")
    return "primed_revealed" if row.get("primed") else "help_timing_unknown"


@entry(read_only=True)
def resolve(connection: Any, vault: Any, repository: Any, *, now: str | None = None) -> list[dict[str, Any]]:
    """Every ``lo_cold_success`` curve resolved under both bindings (pure reads; zero model calls)."""

    from learnloop.adaptive_difficulty.material_view import material_view

    view = material_view(vault, repository)
    groups = _groups(view.forecast_receipts(connection, kind=LO_COLD_SUCCESS))
    return _resolve_groups(connection, vault, repository, view, groups, now=now or utc_now_iso())


@entry(read_only=True)
def resolve_curves(connection: Any, vault: Any, repository: Any, groups: Sequence[Mapping[str, Any]], *,
                   now: str | None = None) -> list[dict[str, Any]]:
    """The same event's curves stated outside ``forecast_receipts`` (router objective RO4's per-option policy
    forecasts on its traces, Codex review F9), resolved by exactly these bindings: each group names its
    ``plan_presentation_id`` (the block's), ``learning_object_id``, ``forecaster`` and ``curve`` (lag in days to
    probability); every other key is carried onto its rows. Pure reads through the material view.

    Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): a group may instead name ``anchor_at``, the moment its action
    ended (an accepted lesson offer's lesson closing), with no plan presentation: its first qualifying cold outcome
    on the LO is the first one after that moment, by the same bindings."""

    from learnloop.adaptive_difficulty.material_view import material_view

    view = material_view(vault, repository)
    usable = [dict(group) for group in groups if isinstance(group.get("curve"), Mapping)
              and (group.get("plan_presentation_id") or group.get("anchor_at"))]
    return _resolve_groups(connection, vault, repository, view, usable, now=now or utc_now_iso())


def _resolve_groups(connection: Any, vault: Any, repository: Any, view: Any, groups: Sequence[Mapping[str, Any]], *,
                    now: str) -> list[dict[str, Any]]:
    from learnloop.adaptive_difficulty import replay as RP

    if not groups:
        return []
    presentations = view.presentations(connection)
    attempts = view.attempts(connection)
    events = {event.attempt_id: event for event in RP.load_events(connection, vault, repository, view=view).attempts}
    reveals = view.reveals(connection)
    readings = _opportunities(connection, vault, repository, view, now=now)
    first_seen: dict[str, str] = {}
    for row in attempts:
        first_seen.setdefault(str(row["practice_item_id"]), str(row["id"]))
    by_block: dict[str, set[str]] = {}
    for pid, row in presentations.items():
        by_block.setdefault(str(row.get("block_id")), set()).add(pid)
    # Router speed, item 2: the rows indexed once by presentation and by LO, each list in the rows' own order, so a
    # group reads its block's and its LO's rows alone (every group scanned every row: the join grew with the log's
    # square). The same rows, in the same order, as each filter below took them.
    by_presentation: dict[str, list[Mapping[str, Any]]] = {}
    attempts_on: dict[str, list[Mapping[str, Any]]] = {}
    for row in attempts:
        by_presentation.setdefault(str(row.get("plan_presentation_id") or ""), []).append(row)
        attempts_on.setdefault(str(row.get("learning_object_id")), []).append(row)
    reveals_on: dict[str, list[Mapping[str, Any]]] = {}
    for reveal in reveals:
        reveals_on.setdefault(str(reveal.get("learning_object_id") or ""), []).append(reveal)
    readings_on: dict[Any, list[Mapping[str, Any]]] = {}
    for reading in readings:
        readings_on.setdefault(reading["learning_object_id"], []).append(reading)
    out: list[dict[str, Any]] = []
    for group in groups:
        base = {"resolver_version": RESOLVER_VERSION, **{k: v for k, v in group.items() if k != "curve"},
                "conditional_on_observation": True}
        lo = str(group["learning_object_id"] or "")
        if group.get("anchor_at") and not group.get("plan_presentation_id"):
            # TE3b: an accepted lesson offer, anchored at its lesson's close (no plan presentation of its own).
            block_end, block_ids = str(group["anchor_at"]), set()
        else:
            presentation = presentations.get(group["plan_presentation_id"])
            if presentation is None:
                out += [{**base, "binding": binding, "status": "pending", "reason": "no_presentation"}
                        for binding in BINDINGS]
                continue
            block = by_block.get(str(presentation.get("block_id")), {group["plan_presentation_id"]})
            # The block's attempts (their order is not read: a latest time and a set of ids).
            block_attempts = [row for pid in block for row in by_presentation.get(str(pid), ())]
            block_end = max([str(presentation["served_at"])] + [str(row["created_at"]) for row in block_attempts])
            block_ids = {str(row["id"]) for row in block_attempts}
        on_lo = attempts_on.get(lo, [])
        candidate, passed = None, []
        for row in on_lo:
            if str(row["id"]) in block_ids or str(row["created_at"]) <= block_end:
                continue
            if first_seen.get(str(row["practice_item_id"])) != str(row["id"]):
                continue  # a seen item: not a cold check of the LO
            event = events.get(str(row["id"]))
            category = event.category if event is not None else None
            if event is None or not event.eligible or category is None:
                passed.append({"attempt_id": str(row["id"]), "why": (event.reason if event is not None else "no_event")
                               or "not_graded"})
                continue
            candidate = (row, category)
            break
        if candidate is None:
            waited = _days(now, block_end)
            beyond = waited is not None and waited > MAX_LAG_DAYS
            out += [{**base, "binding": binding, "status": "censored" if beyond else "pending",
                     "reason": "beyond_measured_lag" if beyond else "no_qualifying_outcome",
                     "passed_over": passed} for binding in BINDINGS]
            continue
        row, category = candidate
        at = str(row["created_at"])
        # Every exposure to the LO, with its time (compared as instants: the sources stamp differently).
        touches = (
            [{"kind": "attempt", "id": str(other["id"]), "at": str(other["created_at"]),
              "in_block": str(other["id"]) in block_ids} for other in on_lo]
            + [{"kind": "reveal", "id": str(reveal["id"]), "at": str(reveal["created_at"]),
                "source_kind": reveal.get("source_kind")} for reveal in reveals_on.get(lo, ())]
            + [{"kind": "reading", "id": str(reading["id"]), "at": str(reading["at"]), "subkind": reading.get("subkind")}
               for reading in readings_on.get(lo, ())])
        before = [touch for touch in touches if (_days(at, touch["at"]) or 0.0) > 0.0]
        exposures = [{k: v for k, v in touch.items() if k != "in_block"} for touch in before
                     if not touch.get("in_block") and (_days(touch["at"], block_end) or 0.0) > 0.0]
        lag = _days(at, block_end) or 0.0
        latest = max(before, key=lambda touch: parse_utc(touch["at"])) if before else None
        delay = _days(at, latest["at"]) if latest is not None else None
        found = {**base, "attempt_id": str(row["id"]), "lag_days": round(lag, 6),
                 "delay_since_exposure_days": None if delay is None else round(delay, 6),
                 "category": category, "outcome_state": _outcome_state(row, category),
                 "exposures": sorted(exposures, key=lambda e: (parse_utc(e["at"]), e["id"])),
                 "passed_over": passed}
        for binding in BINDINGS:
            if lag > MAX_LAG_DAYS:
                out.append({**found, "binding": binding, "status": "censored", "reason": "beyond_measured_lag"})
                continue
            if binding == PER_PROTOCOL and exposures:
                out.append({**found, "binding": binding, "status": "censored", "reason": "intervening_exposure"})
                continue
            p = interpolate(group["curve"], max(lag, 1e-9))
            y = O.unassisted_success(category)
            out.append({**found, "binding": binding, "status": "scored", "p": p, "y": y,
                        "log_loss": _log_loss(p, y), "brier": None if p is None or y is None else (p - y) ** 2})
    return out


def _log_loss(p: float | None, y: float | None) -> float | None:
    from learnloop.adaptive_difficulty.scoring import log_loss

    return None if p is None or y is None else log_loss(p, y)


__all__ = ["BINDINGS", "INTENTION_TO_TREAT", "MAX_LAG_DAYS", "PER_PROTOCOL", "RESOLVER_VERSION", "interpolate", "resolve_curves",
           "resolve"]

"""RO0 rows 7 and 8 (spec_router_objective_v1 §4): what a session had available, and how it ended.

**Availability** (row 8) is stamped before the session's first block: minutes offered and their source, local time and
time zone, device, and a nullable external window a later m1nty bridge may fill (no integration exists in this repo).
Missing is recorded as missing (``minutes_source = 'missing'``), since it is the main confounder of session length and
gone afterward. A later stop decision reads the row plus its own snapshot.

**The end** (row 7) holds the plan, block and stop decision in force, marked ``explicit`` or ``inferred``. A process
can't report its own crash, so a session that ended with no report is inferred at recovery (:func:`sweep_unreported`,
when the next session starts). An offered stop the learner overrode is a ``stop_response`` row: the session goes on.
A stop a device drew past work held for the desktop, taken while the plan stays open, is a ``stop_response`` row too,
accepted (mobile v2 landing ruling R2), and the session's end is that accepted stop.

Never raises: a receipt never blocks a session.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from learnloop.clock import Clock, SystemClock, utc_now_iso
from learnloop.data_capture.gates import objective_receipts_on
from learnloop.db.stores import router_objective as store
from learnloop.ids import new_ulid

logger = logging.getLogger(__name__)

RECEIPT_VERSION = "session_receipts_v1"
AVAILABILITY = "availability"
END = "end"
STOP_RESPONSE = "stop_response"
EXPLICIT = "explicit"
INFERRED = "inferred"
OFFERED_STOP_ACCEPTED = "offered_stop_accepted"
OFFERED_STOP_OVERRIDDEN = "offered_stop_overridden"
UNPROMPTED_STOP = "unprompted_stop"
APP_CLOSED = "app_closed"
FOREGROUND_LOST = "foreground_lost"
EXTERNAL_INTERRUPTION = "external_interruption"
RULE = "rule"
UNKNOWN = "unknown"
#: What only a client can report about the end of a session.
CLIENT_END_REASONS: frozenset[str] = frozenset({
    OFFERED_STOP_ACCEPTED, UNPROMPTED_STOP, APP_CLOSED, FOREGROUND_LOST, EXTERNAL_INTERRUPTION, UNKNOWN,
})
MISSING = "missing"
#: A plan block the plan itself numbered: a stop's receipt row has no ordinal.
_STOP_ACTION = "stop_for_today"


def _dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _base(*, session_id: str | None, kind: str, at: str) -> dict[str, Any]:
    return {"id": new_ulid(), "session_id": session_id, "kind": kind, "detail_json": "{}",
            "receipt_version": RECEIPT_VERSION, "created_at": at}


def _today(clock: Clock | None) -> str:
    return (clock or SystemClock()).now().astimezone().date().isoformat()  # the plan's day (``engine.local_date``)


def _todays_plan(connection: Any, clock: Clock | None) -> dict[str, Any] | None:
    if not store.table_present(connection, "daily_plans"):
        return None
    row = connection.execute(
        "SELECT id, status, stop_reason, minutes_budget, remembered_minutes, minutes_source FROM daily_plans "
        "WHERE local_date = ? ORDER BY created_at DESC, id DESC LIMIT 1", (_today(clock),)).fetchone()
    return dict(row) if row is not None else None


def _session_plan(connection: Any, session_id: str | None, clock: Clock | None) -> dict[str, Any] | None:
    """The plan this session's newest block belongs to, else today's."""

    if session_id and store.table_present(connection, "daily_plans"):
        row = connection.execute(
            "SELECT p.id, p.status, p.stop_reason, p.minutes_budget, p.remembered_minutes, p.minutes_source "
            "FROM attention_blocks b JOIN daily_plans p ON p.id = b.daily_plan_id WHERE b.session_id = ? "
            "ORDER BY b.created_at DESC, b.id DESC LIMIT 1", (session_id,)).fetchone()
        if row is not None:
            return dict(row)
    return _todays_plan(connection, clock)


def _in_force(connection: Any, plan: dict[str, Any] | None) -> dict[str, Any]:
    """The plan, its newest numbered block and its newest stop decision."""

    if plan is None:
        return {"plan_id": None, "block_id": None, "stop_decision_id": None}
    block = connection.execute(
        "SELECT id FROM attention_blocks WHERE daily_plan_id = ? AND plan_ordinal IS NOT NULL "
        "ORDER BY created_at DESC, id DESC LIMIT 1", (plan["id"],)).fetchone()
    stop = connection.execute(
        "SELECT decision_ref FROM attention_blocks WHERE daily_plan_id = ? AND action = ? "
        "ORDER BY created_at DESC, id DESC LIMIT 1", (plan["id"], _STOP_ACTION)).fetchone()
    return {"plan_id": plan["id"], "block_id": block[0] if block is not None else None,
            "stop_decision_id": stop[0] if stop is not None else None}


def _ready(vault: Any, connection: Any) -> bool:
    return objective_receipts_on(vault.config) and store.table_present(connection, store.SESSION_RECEIPTS)


def record_availability(vault: Any, repository: Any, session_id: str, *, available_minutes: float | None = None,
                        device: str | None = None, clock: Clock | None = None) -> bool:
    """Row 8, stamped at the session's start, before its first block is served."""

    try:
        with repository.atomic(), repository.connection() as connection:
            if not _ready(vault, connection):
                return False
            plan = _todays_plan(connection, clock)
            if available_minutes is not None:
                minutes, source = float(available_minutes), "session_start"
            elif plan is not None:
                minutes, source = float(plan["minutes_budget"]), f"plan:{plan['minutes_source']}"
            else:
                minutes, source = None, MISSING
            now = (clock or SystemClock()).now()
            local = now.astimezone()
            offset = local.utcoffset()
            return store.insert_session_receipt(connection, {
                **_base(session_id=session_id, kind=AVAILABILITY, at=utc_now_iso(clock)),
                "minutes_offered": minutes, "minutes_source": source, "local_time": local.isoformat(timespec="seconds"),
                "time_zone": local.tzname() or MISSING,
                "utc_offset_minutes": int(offset.total_seconds() // 60) if offset is not None else None,
                "device": device or MISSING, "external_window_json": None,
                "plan_id": plan["id"] if plan is not None else None,
            })
    except Exception:  # noqa: BLE001 - a receipt never blocks a session
        logger.warning("router objective: the availability of %s was not recorded", session_id, exc_info=True)
        return False


def _derived_reason(plan: dict[str, Any] | None, *, stop_accepted: bool = False) -> str:
    """The plan's own state, when no client said: a finished plan had offered the stop the learner took,
    and so had an open one whose pending stop this session accepted (``stop_accepted``)."""

    if stop_accepted or (plan is not None and plan.get("status") == "complete"):
        return OFFERED_STOP_ACCEPTED
    return UNPROMPTED_STOP


def _accepted_here(connection: Any, session_id: str, stop_decision_id: str | None) -> bool:
    """This session accepted the stop in force (a ``stop_response`` naming it, accepted) and nothing
    overrode it since."""

    if not stop_decision_id:
        return False
    last = connection.execute(
        "SELECT session_id, end_reason FROM session_receipts WHERE kind = ? AND stop_decision_id = ? "
        "ORDER BY created_at DESC, id DESC LIMIT 1", (STOP_RESPONSE, stop_decision_id)).fetchone()
    return last is not None and last[0] == session_id and last[1] == OFFERED_STOP_ACCEPTED


def record_end(vault: Any, repository: Any, session_id: str, *, reason: str | None = None, ended_at: str | None = None,
               clock: Clock | None = None) -> bool:
    """Row 7, explicit: the learner's own ending. A client's word stands when it is one of ours. Once per session."""

    try:
        with repository.atomic(), repository.connection() as connection:
            if not _ready(vault, connection):
                return False
            plan = _session_plan(connection, session_id, clock)
            stated = reason if reason in CLIENT_END_REASONS else None
            in_force = _in_force(connection, plan)
            # Landing ruling R2 (mobile v2, F8): a session that accepted its plan's pending stop (Done for
            # today on a stop drawn past held work) ended on that stop, although the plan stays open.
            accepted = _accepted_here(connection, session_id, in_force["stop_decision_id"])
            if accepted and stated == UNPROMPTED_STOP:
                stated = None
            return store.insert_session_receipt(connection, {
                **_base(session_id=session_id, kind=END, at=utc_now_iso(clock)),
                "end_reason": stated or _derived_reason(plan, stop_accepted=accepted), "end_basis": EXPLICIT,
                "ended_at": ended_at, **in_force,
                "detail_json": _dumps({"stated_by": "client" if stated else "server",
                                       **({"plan_status": plan["status"], "plan_stop_reason": plan["stop_reason"]}
                                          if plan is not None else {})}),
            })
    except Exception:  # noqa: BLE001 - a receipt never blocks a session
        logger.warning("router objective: the end of %s was not recorded", session_id, exc_info=True)
        return False


def record_stop_override(vault: Any, repository: Any, *, session_id: str | None, plan_id: str, via: str,
                         clock: Clock | None = None) -> bool:
    """The learner went on past a finished plan: the offered stop, overridden. The session is not over."""

    try:
        with repository.atomic(), repository.connection() as connection:
            if not _ready(vault, connection):
                return False
            plan = connection.execute(
                "SELECT id, status, stop_reason FROM daily_plans WHERE id = ?", (plan_id,)).fetchone()
            return store.insert_session_receipt(connection, {
                **_base(session_id=session_id, kind=STOP_RESPONSE, at=utc_now_iso(clock)),
                "end_reason": OFFERED_STOP_OVERRIDDEN, "end_basis": EXPLICIT, **_in_force(connection, dict(plan) if plan else None),
                "detail_json": _dumps({"via": via}),
            })
    except Exception:  # noqa: BLE001 - a receipt never blocks a session
        logger.warning("router objective: a stop override of plan %s was not recorded", plan_id, exc_info=True)
        return False


def record_stop_acceptance(vault: Any, repository: Any, *, session_id: str | None, plan_id: str,
                           stop_decision_id: str, via: str, clock: Clock | None = None) -> bool:
    """Landing ruling R2 (mobile v2, F8): the learner took a stop a device was offered while the plan stays open
    for work held for the desktop (*Done for today* on a pending stop). The response names that stop's decision;
    the session's end, when it comes, is the accepted stop. Once per stop while it stands accepted."""

    try:
        with repository.atomic(), repository.connection() as connection:
            if not _ready(vault, connection):
                return False
            last = connection.execute(
                "SELECT end_reason FROM session_receipts WHERE kind = ? AND stop_decision_id = ? "
                "ORDER BY created_at DESC, id DESC LIMIT 1", (STOP_RESPONSE, stop_decision_id)).fetchone()
            if last is not None and last[0] == OFFERED_STOP_ACCEPTED:
                return False
            plan = connection.execute(
                "SELECT id, status, stop_reason FROM daily_plans WHERE id = ?", (plan_id,)).fetchone()
            block = _in_force(connection, dict(plan) if plan else None)["block_id"]
            return store.insert_session_receipt(connection, {
                **_base(session_id=session_id, kind=STOP_RESPONSE, at=utc_now_iso(clock)),
                "end_reason": OFFERED_STOP_ACCEPTED, "end_basis": EXPLICIT, "plan_id": plan_id, "block_id": block,
                "stop_decision_id": stop_decision_id, "detail_json": _dumps({"via": via, "plan_open": True}),
            })
    except Exception:  # noqa: BLE001 - a receipt never blocks a session
        logger.warning("router objective: the acceptance of stop %s was not recorded", stop_decision_id, exc_info=True)
        return False


def sweep_unreported(vault: Any, repository: Any, *, trigger: str, clock: Clock | None = None) -> int:
    """Recovery: every session with an availability row that has ended with no end row gets one, inferred. A process
    can't report its own crash. A session another device replaced ended by the one-open-session rule, and says so.
    Only sessions stamped since RO0: nothing is backfilled. Returns how many it wrote."""

    written = 0
    try:
        with repository.atomic(), repository.connection() as connection:
            if not _ready(vault, connection):
                return 0
            rows = connection.execute(
                "SELECT s.id, s.ended_at, a.plan_id FROM session_receipts a JOIN sessions s ON s.id = a.session_id "
                "WHERE a.kind = 'availability' AND s.ended_at IS NOT NULL AND NOT EXISTS ("
                "SELECT 1 FROM session_receipts e WHERE e.session_id = s.id AND e.kind = 'end')").fetchall()
            for row in rows:
                session_id = str(row[0])
                replaced = connection.execute(
                    "SELECT 1 FROM session_handoffs WHERE session_id = ? AND kind = 'replace' LIMIT 1", (session_id,)
                ).fetchone() is not None if store.table_present(connection, "session_handoffs") else False
                plan = _session_plan(connection, session_id, clock)
                written += 1 if store.insert_session_receipt(connection, {
                    **_base(session_id=session_id, kind=END, at=utc_now_iso(clock)),
                    "end_reason": RULE if replaced else APP_CLOSED, "end_basis": EXPLICIT if replaced else INFERRED,
                    "ended_at": row[1], **_in_force(connection, plan),
                    "detail_json": _dumps({"recovered_by": trigger, **({"replaced": True} if replaced else {})}),
                }) else 0
    except Exception:  # noqa: BLE001 - a receipt never blocks a session
        logger.warning("router objective: the sessions' ends were not swept", exc_info=True)
    return written


__all__ = [
    "APP_CLOSED", "AVAILABILITY", "CLIENT_END_REASONS", "END", "EXPLICIT", "EXTERNAL_INTERRUPTION", "FOREGROUND_LOST",
    "INFERRED", "MISSING", "OFFERED_STOP_ACCEPTED", "OFFERED_STOP_OVERRIDDEN", "RECEIPT_VERSION", "RULE", "STOP_RESPONSE",
    "UNKNOWN", "UNPROMPTED_STOP", "record_availability", "record_end", "record_stop_acceptance", "record_stop_override",
    "sweep_unreported",
]

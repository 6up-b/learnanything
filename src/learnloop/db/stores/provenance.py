"""The decision records' store (migration 253, ADR-017): a write with its own short transaction, and a trace's calls.

``learnloop.provenance`` holds the record, the trace and the read; this module
adds what needs a ``Repository``: :func:`write_decision` for a shell that holds
no connection (it joins the repository's pinned or atomic connection when one
is active, and takes a short transaction of its own otherwise), and
:func:`trace_model_calls`, the join from a trace to its model calls by
``model_call_receipts.trace_id`` (metadata only: never the prompt or the output), and
:func:`discarded_calls`, the calls that answered after their decision was taken.
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from learnloop import provenance

LOG = logging.getLogger(__name__)

#: The receipt columns ``why`` shows for a trace's calls: ids, times, statuses and
#: accounting. ``input_text``, ``schema_json`` and ``output_text`` are payloads.
TRACE_CALL_COLUMNS = (
    "id", "trace_id", "parent_call_id", "owner_kind", "owner_id", "purpose", "provider", "model", "status",
    "error_type", "started_at", "finished_at", "input_tokens", "output_tokens", "cost",
)


def write_decision(repository: Any, record: provenance.DecisionRecord) -> str | None:
    """Write ``record`` through ``repository``; its id, or ``None`` when it was not written. Never raises."""

    try:
        with repository.connection() as connection:
            return provenance.write(connection, record)
    except Exception as exc:  # noqa: BLE001 - a record never changes the decision it describes
        LOG.warning("decision record %r not written (trace %s): %s", record.kind,
                    record.trace_id or provenance.current_trace(), type(exc).__name__)
        return None


def trace_model_calls(connection: Any, trace_ids: Iterable[str]) -> list[dict[str, Any]]:
    """Model calls made under any of ``trace_ids``, oldest first (empty below migration 253)."""

    traces = sorted({str(trace) for trace in trace_ids if trace})
    if not traces:
        return []
    try:
        rows = connection.execute(
            f"SELECT {', '.join(TRACE_CALL_COLUMNS)} FROM model_call_receipts "
            f"WHERE trace_id IN ({', '.join('?' for _ in traces)}) ORDER BY started_at, id",
            traces,
        ).fetchall()
    except sqlite3.OperationalError as exc:
        if "no such column" in str(exc) or "no such table" in str(exc):
            return []
        raise
    return [dict(zip(TRACE_CALL_COLUMNS, row, strict=True)) for row in rows]


#: Record kinds whose ``created_at`` is the moment the decision took its models' answers, so a call of its traces
#: that finished later answered too late and was discarded. A kind joins only when its writer stamps that moment.
LATE_ANSWER_KINDS = frozenset({"plan_block"})


def _moment(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


def discarded_calls(records: Iterable[provenance.DecisionRecord],
                    calls: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """The calls each decision discarded: started before it under its own or its prefetch's trace, for its boundary
    key when it names one, and finished after it (``late_ms``) or not at all (``late_ms`` None). Derived at read time,
    with no write: a late answer comes after its decision's record by definition."""

    calls = list(calls)
    out: list[dict[str, Any]] = []
    for record in records:
        decided = _moment(record.created_at)
        if record.kind not in LATE_ANSWER_KINDS or record.parent_id is not None or decided is None:
            continue
        traces = {record.trace_id, record.facts.get("prefetch_trace")} - {None}
        key = record.facts.get("boundary_key")
        for call in calls:
            started, finished = _moment(call.get("started_at")), _moment(call.get("finished_at"))
            if call.get("trace_id") not in traces or (key and call.get("owner_id") != key):
                continue
            if started is None or started > decided or (finished is not None and finished <= decided):
                continue
            out.append({
                "record_id": record.id, "call_id": call.get("id"), "trace_id": call.get("trace_id"),
                "purpose": call.get("purpose"), "model": call.get("model"), "status": call.get("status"),
                "finished_at": call.get("finished_at"),
                "late_ms": None if finished is None else int(round((finished - decided).total_seconds() * 1000)),
            })
    return out


#: ``daily_plan.router_runtime.RECEIPT_OWNER``: the owner kind of a router model call, whose ``owner_id`` is the
#: decision's boundary key (named here, not imported: a store doesn't import the planner).
ROUTER_OWNER = "router_decision"


def unclaimed_calls(connection: Any, records: Iterable[provenance.DecisionRecord],
                    calls: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Router calls whose boundary key no decision names: neither a shown record nor any logged router decision. Their
    decision was never made (its key changed before the serve, or its prefetch was evicted), so whatever they answered
    or failed with went nowhere. Derived at read time, with no write."""

    router = [call for call in calls if call.get("owner_kind") == ROUTER_OWNER and call.get("owner_id")]
    keys = {str(call["owner_id"]) for call in router}
    claimed = {record.facts.get("boundary_key") for record in records} & keys
    rest = sorted(keys - claimed)
    if rest:
        try:
            found = connection.execute(
                "SELECT DISTINCT json_extract(detail_json, '$.mixture.boundary_key') FROM router_decisions "
                f"WHERE json_extract(detail_json, '$.mixture.boundary_key') IN ({', '.join('?' for _ in rest)})", rest,
            ).fetchall()
            claimed |= {row[0] for row in found}
        except sqlite3.Error:
            return []  # no ledger to check against: say nothing rather than call everything unclaimed
    return [{"call_id": call.get("id"), "trace_id": call.get("trace_id"), "boundary_key": call.get("owner_id"),
             "purpose": call.get("purpose"), "model": call.get("model"), "status": call.get("status"),
             "error_type": call.get("error_type")}
            for call in router if call["owner_id"] not in claimed]

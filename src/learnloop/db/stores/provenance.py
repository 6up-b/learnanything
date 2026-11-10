"""The decision records' store (migration 253, ADR-017): a write with its own short transaction, and a trace's calls.

``learnloop.provenance`` holds the record, the trace and the read; this module
adds what needs a ``Repository``: :func:`write_decision` for a shell that holds
no connection (it joins the repository's pinned or atomic connection when one
is active, and takes a short transaction of its own otherwise), and
:func:`trace_model_calls`, the join from a trace to its model calls by
``model_call_receipts.trace_id`` (metadata only: never the prompt or the output).
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Iterable
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

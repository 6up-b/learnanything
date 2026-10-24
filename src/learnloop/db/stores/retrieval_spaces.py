"""Embedding spaces, retrieval feedback and the fusion posterior (migration 219).

The one SQL owner of ``embedding_spaces`` (WORKFLOW), ``retrieval_feedback``
(RECEIPT, append-only by trigger) and ``retrieval_fusion_posteriors``
(DERIVED; written only by its replayer and the refit, which replace the whole
table). Every function takes an open connection; the caller owns the
transaction. A database before migration 219 reads as empty and writes
nothing (``has_tables``).
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timezone
import json
import sqlite3
from typing import Any
from uuid import uuid4

SPACE_STATUSES = ("active", "fallback", "incumbent", "retired", "epoch_drift")
FEEDBACK_EVENTS = ("query", "delivered", "cited", "opened", "anchored")
SIGNAL_EVENTS = ("cited", "opened", "anchored")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def has_tables(connection: sqlite3.Connection) -> bool:
    return connection.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name IN "
        "('embedding_spaces', 'retrieval_feedback', 'retrieval_fusion_posteriors')").fetchone()[0] == 3


# -- embedding_spaces ----------------------------------------------------------------------
def register_space(connection: sqlite3.Connection, *, space_id: str, name: str, kind: str,
                   pins: Mapping[str, Any], status: str, reason: str | None = None,
                   now: str | None = None) -> None:
    """Insert a space once; a known space keeps its row (its status changes
    only through :func:`set_space_status`)."""

    if status not in SPACE_STATUSES:
        raise ValueError(f"unknown space status {status!r}")
    stamp = now or _now()
    connection.execute(
        "INSERT INTO embedding_spaces (space_id, name, kind, pins_json, status, status_reason, created_at, "
        "updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(space_id) DO NOTHING",
        (space_id, name, kind, _json(dict(pins)), status, reason, stamp, stamp))


def set_space_status(connection: sqlite3.Connection, space_id: str, status: str, *,
                     reason: str | None = None, now: str | None = None) -> None:
    if status not in SPACE_STATUSES:
        raise ValueError(f"unknown space status {status!r}")
    stamp = now or _now()
    connection.execute(
        "UPDATE embedding_spaces SET status = ?, status_reason = ?, updated_at = ?, "
        "retired_at = CASE WHEN ? = 'retired' THEN ? ELSE retired_at END WHERE space_id = ?",
        (status, reason, stamp, status, stamp, space_id))


def set_space_canaries(connection: sqlite3.Connection, space_id: str, canaries: Mapping[str, Any], *,
                       now: str | None = None) -> None:
    """Store a space's canary vectors once (the first healthy batch's)."""

    connection.execute(
        "UPDATE embedding_spaces SET canaries_json = ?, updated_at = ? WHERE space_id = ? AND canaries_json IS NULL",
        (_json(dict(canaries)), now or _now(), space_id))


def spaces(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    if not has_tables(connection):
        return {}
    rows = connection.execute(
        "SELECT space_id, name, kind, pins_json, status, status_reason, canaries_json, created_at, updated_at, "
        "retired_at FROM embedding_spaces ORDER BY created_at, space_id").fetchall()
    return {str(row[0]): {"space_id": row[0], "name": row[1], "kind": row[2], "pins": json.loads(row[3]),
                          "status": row[4], "status_reason": row[5],
                          "canaries": json.loads(row[6]) if row[6] else None, "created_at": row[7],
                          "updated_at": row[8], "retired_at": row[9]} for row in rows}


# -- retrieval_feedback ---------------------------------------------------------------------
def append_feedback(connection: sqlite3.Connection, rows: Iterable[Mapping[str, Any]], *,
                    now: str | None = None) -> int:
    stamp = now or _now()
    written = 0
    for row in rows:
        event = str(row["event"])
        if event not in FEEDBACK_EVENTS:
            raise ValueError(f"unknown retrieval feedback event {event!r}")
        connection.execute(
            "INSERT INTO retrieval_feedback (id, receipt_id, event, consumer, query_kind, owner_id, extraction_id, "
            "span_id, position, payload_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (str(row.get("id") or uuid4()), str(row["receipt_id"]), event, str(row["consumer"]),
             str(row["query_kind"]), str(row.get("owner_id") or ""), row.get("extraction_id"), row.get("span_id"),
             row.get("position"), _json(dict(row.get("payload") or {})), str(row.get("created_at") or stamp)))
        written += 1
    return written


def feedback_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Every feedback row in insertion order (the replayer's input)."""

    if not has_tables(connection):
        return []
    return [{"id": row[0], "receipt_id": row[1], "event": row[2], "consumer": row[3], "query_kind": row[4],
             "owner_id": row[5], "extraction_id": row[6], "span_id": row[7], "position": row[8],
             "payload": json.loads(row[9] or "{}"), "created_at": row[10]}
            for row in connection.execute(
                "SELECT id, receipt_id, event, consumer, query_kind, owner_id, extraction_id, span_id, position, "
                "payload_json, created_at FROM retrieval_feedback ORDER BY rowid")]


def deliveries_for_owner(connection: sqlite3.Connection, *, consumer: str, owner_id: str,
                         keys: Sequence[tuple[str, str]]) -> dict[tuple[str, str], dict[str, Any]]:
    """The newest delivery row of each span key for one consumer's owner id."""

    if not has_tables(connection) or not owner_id or not keys:
        return {}
    wanted = {(str(a), str(b)) for a, b in keys}
    found: dict[tuple[str, str], dict[str, Any]] = {}
    for receipt_id, query_kind, extraction_id, span_id, position in connection.execute(
        "SELECT receipt_id, query_kind, extraction_id, span_id, position FROM retrieval_feedback "
        "WHERE consumer = ? AND owner_id = ? AND event = 'delivered' ORDER BY rowid",
        (consumer, owner_id),
    ):
        key = (str(extraction_id), str(span_id))
        if key in wanted:
            found[key] = {"receipt_id": receipt_id, "query_kind": query_kind, "position": position}
    return found


def delivery_for_receipt(connection: sqlite3.Connection, receipt_id: str,
                         key: tuple[str, str]) -> dict[str, Any] | None:
    if not has_tables(connection):
        return None
    row = connection.execute(
        "SELECT consumer, query_kind, owner_id, position FROM retrieval_feedback WHERE receipt_id = ? AND "
        "event = 'delivered' AND extraction_id = ? AND span_id = ? ORDER BY rowid DESC LIMIT 1",
        (receipt_id, key[0], key[1])).fetchone()
    return None if row is None else {"consumer": row[0], "query_kind": row[1], "owner_id": row[2],
                                     "position": row[3]}


# -- retrieval_fusion_posteriors (DERIVED) ---------------------------------------------------
def replace_fusion_posteriors(connection: sqlite3.Connection, rows: Sequence[Mapping[str, Any]]) -> int:
    """Replace the whole projection (the replayer's and the refit's only write)."""

    connection.execute("DELETE FROM retrieval_fusion_posteriors")
    for row in rows:
        connection.execute(
            "INSERT INTO retrieval_fusion_posteriors (context_key, consumer, query_kind, lists_json, mean_json, "
            "covariance_json, intercepts_json, examination_json, rrf_k, observations, signals, prior_basis_json, "
            "fit_version, input_digest, fitted_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (row["context_key"], row["consumer"], row["query_kind"], _json(row["lists"]), _json(row["mean"]),
             _json(row["covariance"]), _json(row["intercepts"]), _json(row["examination"]), float(row["rrf_k"]),
             int(row["observations"]), int(row["signals"]), _json(row["prior_basis"]), row["fit_version"],
             row["input_digest"], row["fitted_at"]))
    return len(rows)


def fusion_posteriors(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    if not has_tables(connection):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for row in connection.execute(
        "SELECT context_key, consumer, query_kind, lists_json, mean_json, covariance_json, intercepts_json, "
        "examination_json, rrf_k, observations, signals, prior_basis_json, fit_version, input_digest, fitted_at "
        "FROM retrieval_fusion_posteriors ORDER BY context_key"):
        out[str(row[0])] = {"context_key": row[0], "consumer": row[1], "query_kind": row[2],
                            "lists": json.loads(row[3]), "mean": json.loads(row[4]),
                            "covariance": json.loads(row[5]), "intercepts": json.loads(row[6]),
                            "examination": json.loads(row[7]), "rrf_k": row[8], "observations": row[9],
                            "signals": row[10], "prior_basis": json.loads(row[11]), "fit_version": row[12],
                            "input_digest": row[13], "fitted_at": row[14]}
    return out


__all__ = [
    "FEEDBACK_EVENTS",
    "SIGNAL_EVENTS",
    "SPACE_STATUSES",
    "append_feedback",
    "deliveries_for_owner",
    "delivery_for_receipt",
    "feedback_rows",
    "fusion_posteriors",
    "has_tables",
    "register_space",
    "replace_fusion_posteriors",
    "set_space_canaries",
    "set_space_status",
    "spaces",
]

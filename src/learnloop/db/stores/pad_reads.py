"""Reads of the workbench's scratchpads (migration 262): ``pads``, ``pad_block_versions`` and
``pad_block_anchors``. No write: the one writer is ``db.stores.pads``, and the read-only union imports only
this module (the passage-projections import fence).

A block's head is its one version that no other version supersedes.
"""
from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from typing import Any

_HEADS = (
    "SELECT v.* FROM pad_block_versions AS v WHERE {where} AND NOT EXISTS "
    "(SELECT 1 FROM pad_block_versions AS c WHERE c.supersedes_id = v.version_id)"
)


def _rows(connection: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, tuple(params))
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def _decoded(row: dict[str, Any]) -> dict[str, Any]:
    row = dict(row)
    row["payload"] = json.loads(row.pop("payload_json") or "{}")
    row["tombstone"] = bool(row["tombstone"])
    return row


def pad(connection: sqlite3.Connection, pad_id: str) -> dict[str, Any] | None:
    found = _rows(connection, "SELECT * FROM pads WHERE pad_id = ?", (pad_id,))
    return found[0] if found else None


def running_pad_ids(connection: sqlite3.Connection, desk_id: str) -> list[str]:
    return [str(row[0]) for row in connection.execute(
        "SELECT pad_id FROM pads WHERE home_desk_id = ? AND kind = 'running' AND archived_at IS NULL "
        "ORDER BY created_at, pad_id", (desk_id,))]

def list_pads(connection: sqlite3.Connection, *, desk_id: str | None, kept: bool | None, query: str | None,
              after: tuple[str, str] | None, page_size: int) -> list[dict[str, Any]]:
    """Pads, most recently changed first; ``query`` matches the title or a standing block's text."""

    clauses, params = ["p.archived_at IS NULL"], []
    if desk_id is not None:
        clauses.append("p.home_desk_id = ?")
        params.append(desk_id)
    if kept is not None:
        clauses.append("p.kept = ?")
        params.append(1 if kept else 0)
    if query:
        like = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        clauses.append(
            "(p.title LIKE ? ESCAPE '\\' OR EXISTS (" + _HEADS.format(where="v.pad_id = p.pad_id AND v.tombstone = 0")
            + " AND v.body_md LIKE ? ESCAPE '\\'))")
        params.extend([like, like])
    if after is not None:
        clauses.append("(p.updated_at < ? OR (p.updated_at = ? AND p.pad_id > ?))")
        params.extend([after[0], after[0], after[1]])
    sql = f"SELECT p.* FROM pads AS p WHERE {' AND '.join(clauses)} ORDER BY p.updated_at DESC, p.pad_id LIMIT ?"
    return _rows(connection, sql, [*params, page_size])


def lesson_additions_pads(connection: sqlite3.Connection, lesson_ids: Iterable[str]) -> dict[str, list[str]]:
    """Each lesson's additions pads (spec §11.1, "your additions"), oldest first: the first is where new notes go
    (a second is refused since); pads two windows made before that rule are all kept and all named."""

    wanted = list(dict.fromkeys(lesson_ids))
    if not wanted:
        return {}
    marks = ",".join("?" * len(wanted))
    rows = _rows(connection, f"SELECT pad_id, lesson_id FROM pads WHERE kind = 'lesson_additions' AND archived_at IS NULL "
                             f"AND lesson_id IN ({marks}) ORDER BY created_at, pad_id", wanted)
    out: dict[str, list[str]] = {}
    for row in rows:
        out.setdefault(str(row["lesson_id"]), []).append(str(row["pad_id"]))
    return out


def head(connection: sqlite3.Connection, block_id: str) -> dict[str, Any] | None:
    found = _rows(connection, _HEADS.format(where="v.block_id = ?"), (block_id,))
    return _decoded(found[0]) if found else None


def heads(connection: sqlite3.Connection, pad_id: str) -> list[dict[str, Any]]:
    """Every block head of one pad (tombstones included), ordered by position, then block id."""

    rows = _rows(connection, _HEADS.format(where="v.pad_id = ?") + " ORDER BY v.position_key, v.block_id", (pad_id,))
    return [_decoded(row) for row in rows]


def first_versions(connection: sqlite3.Connection, block_ids: Iterable[str]) -> dict[str, str]:
    wanted = sorted(set(block_ids))
    if not wanted:
        return {}
    marks = ",".join("?" for _ in wanted)
    return {str(row[0]): str(row[1]) for row in connection.execute(
        f"SELECT block_id, created_at FROM pad_block_versions WHERE supersedes_id IS NULL AND block_id IN ({marks})",
        wanted)}


def chain(connection: sqlite3.Connection, block_id: str) -> list[dict[str, Any]]:
    """One block's versions, oldest first, by following its supersession links from its first version."""

    rows = [_decoded(row) for row in _rows(connection, "SELECT * FROM pad_block_versions WHERE block_id = ?",
                                           (block_id,))]
    child = {row["supersedes_id"]: row for row in rows}
    ordered: list[dict[str, Any]] = []
    current = child.get(None)
    while current is not None and len(ordered) < len(rows):
        ordered.append(current)
        current = child.get(current["version_id"])
    return ordered


def version(connection: sqlite3.Connection, version_id: str) -> dict[str, Any] | None:
    found = _rows(connection, "SELECT * FROM pad_block_versions WHERE version_id = ?", (version_id,))
    return _decoded(found[0]) if found else None


def lift_stub_for(connection: sqlite3.Connection, block_id: str) -> dict[str, Any] | None:
    """The stub version a lift-out left in the block a lifted block came from, or None."""

    found = _rows(connection, "SELECT * FROM pad_block_versions WHERE kind = 'lifted' AND "
                              "json_extract(payload_json, '$.lifted_block_id') = ? ORDER BY rowid LIMIT 1", (block_id,))
    return _decoded(found[0]) if found else None


def block_ids(connection: sqlite3.Connection) -> list[str]:
    """Every block with a version, in a stable order."""

    return [str(row[0]) for row in connection.execute("SELECT DISTINCT block_id FROM pad_block_versions ORDER BY 1")]


def version_exists(connection: sqlite3.Connection, version_id: str) -> bool:
    return connection.execute("SELECT 1 FROM pad_block_versions WHERE version_id = ?", (version_id,)).fetchone() is not None


_STANDING = (
    "SELECT a.* FROM pad_block_anchors AS a WHERE {where} AND a.action = 'link' AND a.rowid = ("
    "SELECT b.rowid FROM pad_block_anchors AS b WHERE b.block_id = a.block_id AND b.extraction_id = a.extraction_id "
    "AND b.span_id = a.span_id ORDER BY b.rowid DESC LIMIT 1)"
)


def standing_anchors_for_blocks(connection: sqlite3.Connection, block_ids: Iterable[str]) -> list[dict[str, Any]]:
    """The links that stand (the latest event per block and passage is a link), in written order."""

    wanted = sorted(set(block_ids))
    if not wanted:
        return []
    marks = ",".join("?" for _ in wanted)
    rows = _rows(connection, _STANDING.format(where=f"a.block_id IN ({marks})") + " ORDER BY a.rowid", wanted)
    return [{**row, "anchor": json.loads(row.pop("anchor_json") or "{}")} for row in rows]


def standing_anchors_for_spans(connection: sqlite3.Connection, extraction_ids: Iterable[str]) -> list[dict[str, Any]]:
    """Every standing link onto the given readings, each with its block's head (pad and kind)."""

    wanted = sorted(set(extraction_ids))
    if not wanted:
        return []
    marks = ",".join("?" for _ in wanted)
    rows = _rows(connection, _STANDING.format(where=f"a.extraction_id IN ({marks})") + " ORDER BY a.rowid", wanted)
    return [{**row, "anchor": json.loads(row.pop("anchor_json") or "{}")} for row in rows]


def latest_anchor_event(connection: sqlite3.Connection, block_id: str, extraction_id: str,
                        span_id: str) -> dict[str, Any] | None:
    """The newest link or unlink event between one block and one passage (the anchor's head), or None."""

    found = _rows(connection, "SELECT * FROM pad_block_anchors WHERE block_id = ? AND extraction_id = ? AND span_id = ? "
                              "ORDER BY rowid DESC LIMIT 1", (block_id, extraction_id, span_id))
    return found[0] if found else None


def anchor_event_exists(connection: sqlite3.Connection, event_id: str) -> bool:
    return connection.execute("SELECT 1 FROM pad_block_anchors WHERE event_id = ?", (event_id,)).fetchone() is not None


# -- migration 266: submissions, carried questions, proposals and their labels ---------------------------


def _table(connection: sqlite3.Connection, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                              (name,)).fetchone() is not None


def submission(connection: sqlite3.Connection, submission_id: str) -> dict[str, Any] | None:
    found = _rows(connection, "SELECT * FROM pad_block_submissions WHERE submission_id = ?", (submission_id,))
    return found[0] if found else None


def submissions_for_blocks(connection: sqlite3.Connection, block_ids: Iterable[str]) -> list[dict[str, Any]]:
    wanted = sorted(set(block_ids))
    if not wanted or not _table(connection, "pad_block_submissions"):
        return []
    marks = ",".join("?" for _ in wanted)
    return _rows(connection, f"SELECT * FROM pad_block_submissions WHERE block_id IN ({marks}) "
                             "ORDER BY created_at, submission_id", wanted)


def _carried_out(row: dict[str, Any]) -> dict[str, Any]:
    row = dict(row)
    anchor = row.pop("anchor_json")
    row["anchor"] = json.loads(anchor) if anchor else None
    return row


def carried(connection: sqlite3.Connection, carried_id: str) -> dict[str, Any] | None:
    found = _rows(connection, "SELECT * FROM carried_questions WHERE carried_id = ?", (carried_id,))
    return _carried_out(found[0]) if found else None


def list_carried(connection: sqlite3.Connection, *, states: Iterable[str], desk_id: str | None,
                 after: tuple[str, str] | None, page_size: int) -> list[dict[str, Any]]:
    """Carried questions in the given states, longest carried first (then by id)."""

    wanted = sorted(set(states))
    clauses, params = [f"state IN ({','.join('?' for _ in wanted)})"], list(wanted)
    if desk_id is not None:
        clauses.append("desk_id = ?")
        params.append(desk_id)
    if after is not None:
        clauses.append("(since > ? OR (since = ? AND carried_id > ?))")
        params.extend([after[0], after[0], after[1]])
    sql = f"SELECT * FROM carried_questions WHERE {' AND '.join(clauses)} ORDER BY since, carried_id LIMIT ?"
    return [_carried_out(row) for row in _rows(connection, sql, [*params, page_size])]


def carried_on_readings(connection: sqlite3.Connection, extraction_ids: Iterable[str],
                        states: Iterable[str]) -> list[dict[str, Any]]:
    """Carried questions in the given states whose anchor is on one of the readings."""

    wanted = sorted(set(extraction_ids))
    if not wanted or not _table(connection, "carried_questions"):
        return []
    marks = ",".join("?" for _ in wanted)
    state_marks = ",".join("?" for _ in sorted(set(states)))
    rows = _rows(connection, f"SELECT * FROM carried_questions WHERE anchor_json IS NOT NULL AND "
                             f"json_extract(anchor_json, '$.extraction_id') IN ({marks}) AND state IN ({state_marks}) "
                             "ORDER BY since, carried_id", [*wanted, *sorted(set(states))])
    return [_carried_out(row) for row in rows]


def carried_event_exists(connection: sqlite3.Connection, event_id: str) -> dict[str, Any] | None:
    found = _rows(connection, "SELECT * FROM carried_question_events WHERE event_id = ?", (event_id,))
    return found[0] if found else None


def carried_events(connection: sqlite3.Connection, carried_id: str) -> list[dict[str, Any]]:
    return _rows(connection, "SELECT * FROM carried_question_events WHERE carried_id = ? ORDER BY at, rowid",
                 (carried_id,))


def _proposal_out(row: dict[str, Any]) -> dict[str, Any]:
    row = dict(row)
    row["target_spec"] = json.loads(row.pop("target_spec_json") or "{}")
    return row


def proposal(connection: sqlite3.Connection, proposal_id: str) -> dict[str, Any] | None:
    found = _rows(connection, "SELECT * FROM pad_proposals WHERE proposal_id = ?", (proposal_id,))
    return _proposal_out(found[0]) if found else None


def proposal_for_version(connection: sqlite3.Connection, version_id: str) -> dict[str, Any] | None:
    found = _rows(connection, "SELECT * FROM pad_proposals WHERE block_version_id = ?", (version_id,))
    return _proposal_out(found[0]) if found else None


def proposals_for_versions(connection: sqlite3.Connection, version_ids: Iterable[str]) -> list[dict[str, Any]]:
    wanted = sorted(set(version_ids))
    if not wanted or not _table(connection, "pad_proposals"):
        return []
    marks = ",".join("?" for _ in wanted)
    return [_proposal_out(row) for row in _rows(
        connection, f"SELECT * FROM pad_proposals WHERE block_version_id IN ({marks}) ORDER BY created_at, proposal_id",
        wanted)]


def label(connection: sqlite3.Connection, label_id: str) -> dict[str, Any] | None:
    found = _rows(connection, "SELECT * FROM proposal_labels WHERE label_id = ?", (label_id,))
    return found[0] if found else None


def labels_for(connection: sqlite3.Connection, proposal_kind: str, proposal_ids: Iterable[str]) -> list[dict[str, Any]]:
    wanted = sorted(set(proposal_ids))
    if not wanted or not _table(connection, "proposal_labels"):
        return []
    marks = ",".join("?" for _ in wanted)
    return _rows(connection, f"SELECT * FROM proposal_labels WHERE proposal_kind = ? AND proposal_id IN ({marks}) "
                             "ORDER BY at, rowid", [proposal_kind, *wanted])


__all__ = [
    "anchor_event_exists", "block_ids", "carried", "carried_event_exists", "carried_events", "carried_on_readings",
    "chain", "first_versions", "head", "heads", "label", "labels_for", "latest_anchor_event", "lift_stub_for",
    "list_carried", "list_pads", "pad", "proposal", "proposal_for_version", "proposals_for_versions",
    "running_pad_ids", "standing_anchors_for_blocks", "standing_anchors_for_spans", "submission",
    "submissions_for_blocks", "version", "version_exists",
]

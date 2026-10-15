"""The held-out signal ledger's exam qualification (migration 225; Codex review
of exam protection by extraction identity, F3).

A held-out signal counts as exam protection when it was made under an exam
role (``made_as_role``), or, for a row whose role was not recorded (a signal
backfilled by migration 225 from an inventory made under neither the exam
role's profile nor on a book with an outline exam pick), while its book is
exam material (``content.sources.exam_material._signal_counts``). Such a row
would stop protecting once its book stopped being exam material, with no
decision to release it. So whatever ends a book's exam membership records its
role-unrecorded rows as exam material first: an appended copy
(``hos_q_<row id>``, ``made_as_role = 'exam'``), never an update of the
append-only ledger. The vault writer calls it before it writes a source set
that ends a book's exam membership in that set, and the repository before an
outline exam pick is changed.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable

#: The roles whose material is exam material (``content.sources.role_authority.
#: ASSESSMENT_ONLY_ROLES``, which this infrastructure layer may not import;
#: pinned equal by a test).
EXAM_ROLES: frozenset[str] = frozenset({"exam"})
#: The role a qualified copy records.
QUALIFIED_ROLE = "exam"

_LEDGER = "source_held_out_signal_marks"


def is_exam_role(role: object) -> bool:
    return str(role or "").strip() in EXAM_ROLES


def _has_ledger(connection: sqlite3.Connection) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (_LEDGER,)).fetchone() is not None


def unqualified_signal_count(connection: sqlite3.Connection, source_ids: Iterable[str]) -> int:
    """How many role-unrecorded held-out signals these books have (0 before migration 225)."""

    ids = sorted({str(source_id) for source_id in source_ids if source_id})
    if not ids or not _has_ledger(connection):
        return 0
    marks = ",".join("?" for _ in ids)
    return int(connection.execute(
        f"SELECT COUNT(*) FROM {_LEDGER} AS m JOIN source_revisions AS r ON r.id = m.revision_id "
        f"WHERE m.made_as_role IS NULL AND r.source_id IN ({marks})", ids).fetchone()[0])


def qualify_unrecorded_signals(connection: sqlite3.Connection, source_ids: Iterable[str], *,
                               created_at: str) -> int:
    """Record these books' role-unrecorded held-out signals as made as exam
    material (an appended copy each, idempotent), in the caller's
    transaction; the number of rows appended."""

    ids = sorted({str(source_id) for source_id in source_ids if source_id})
    if not ids or not _has_ledger(connection):
        return 0
    marks = ",".join("?" for _ in ids)
    cursor = connection.execute(
        f"INSERT OR IGNORE INTO {_LEDGER}(id, revision_id, extraction_id, unit_id, inventory_id, made_as_role, "
        "span_ids_json, created_at) "
        "SELECT 'hos_q_' || m.id, m.revision_id, m.extraction_id, m.unit_id, m.inventory_id, ?, m.span_ids_json, ? "
        f"FROM {_LEDGER} AS m JOIN source_revisions AS r ON r.id = m.revision_id "
        f"WHERE m.made_as_role IS NULL AND r.source_id IN ({marks})",
        [QUALIFIED_ROLE, created_at, *ids])
    return max(int(cursor.rowcount or 0), 0)


__all__ = ["EXAM_ROLES", "QUALIFIED_ROLE", "is_exam_role", "qualify_unrecorded_signals", "unqualified_signal_count"]

"""The held-out signal ledger's exam qualification (migration 225; Codex review
of exam protection by extraction identity, F3).

A held-out signal counts as exam protection when it was made under an exam
role (``made_as_role``), or, for a row whose role was not recorded (a signal
migration 225 backfilled on a book with no outline exam pick: the cache never
recorded the role an inventory was made under, and its profile is not one,
Codex re-review F7), while its book is exam material
(``content.sources.exam_material._signal_counts``). Such a row would stop
protecting once its book stopped being exam material, with no decision to
release it. So the role-unrecorded rows of a book that is exam material are
recorded as exam material: an appended copy (``hos_q_<row id>``,
``made_as_role = 'exam'``), never an update of the append-only ledger.

* The app records them whenever it migrates or opens the vault
  (``learnloop.migration_coordinator``; the upgrade to 225 first), for the
  books ``source_sets.yaml`` makes exam material then, so a later hand edit of
  that file releases nothing (Codex re-review F3).
* The vault writer records them before it writes a source set that ends a
  book's exam membership in that set, and the repository before an outline
  exam pick is changed.
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


def exam_member_sources(members: Iterable[object]) -> set[str]:
    """The books a source set's members (``source_sets.yaml`` entries, as
    read) make exam material: an exam default role, or a scope entry
    overridden to an exam role (``content.sources.exam_material``'s rule 1 and
    rule 2, read the same way)."""

    found: set[str] = set()
    for member in members if isinstance(members, (list, tuple)) else ():
        if not isinstance(member, dict) or not member.get("source_id"):
            continue
        scope = member.get("scope") if isinstance(member.get("scope"), list) else []
        if is_exam_role(member.get("default_role")) or any(
                isinstance(entry, dict) and is_exam_role(entry.get("role_override")) for entry in scope):
            found.add(str(member["source_id"]))
    return found


def pending_unrecorded_sources(connection: sqlite3.Connection) -> set[str]:
    """The books with a role-unrecorded held-out signal not yet recorded as
    exam material (none before migration 225)."""

    if not _has_ledger(connection):
        return set()
    return {str(row[0]) for row in connection.execute(
        f"SELECT DISTINCT r.source_id FROM {_LEDGER} AS m JOIN source_revisions AS r ON r.id = m.revision_id "
        f"WHERE m.made_as_role IS NULL AND r.source_id IS NOT NULL AND NOT EXISTS ("
        f"SELECT 1 FROM {_LEDGER} AS q WHERE q.id = 'hos_q_' || m.id)")}


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


__all__ = [
    "EXAM_ROLES",
    "QUALIFIED_ROLE",
    "exam_member_sources",
    "is_exam_role",
    "pending_unrecorded_sources",
    "qualify_unrecorded_signals",
    "unqualified_signal_count",
]

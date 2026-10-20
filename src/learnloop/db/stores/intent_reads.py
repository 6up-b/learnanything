"""Read-only queries for daily-loop DL2's intent resolution (spec §5.3).

Bulk reads over the commitment tables (migration 072) and the attempt
ledger. Nothing here writes: the control writes through
``learnloop.curriculum.commitments`` only (§5.1, §10).
"""

from __future__ import annotations

import sqlite3
from typing import Any


def commitment_tables_present(connection: sqlite3.Connection) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'commitment_target_versions'"
    ).fetchone()
    return row is not None


def commitments_covering_items(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Every commitment whose HEAD version targets an LO or a practice item.

    A commitment whose head targets only source locators, facets or exemplars
    covers no item (§5.3 step 1), so it is left out here.
    """

    rows = connection.execute(
        """
        WITH heads AS (
          SELECT version.commitment_id, MAX(version.version) AS version
          FROM commitment_versions version
          GROUP BY version.commitment_id
        )
        SELECT DISTINCT commitment.id, commitment.created_action, commitment.created_at
        FROM commitments commitment
        JOIN heads ON heads.commitment_id = commitment.id
        JOIN commitment_versions head
          ON head.commitment_id = heads.commitment_id AND head.version = heads.version
        JOIN commitment_target_versions target ON target.commitment_version_id = head.id
        WHERE target.target_kind IN ('learning_object', 'legacy_practice_item')
        ORDER BY commitment.created_at, commitment.id
        """
    ).fetchall()
    return [dict(row) for row in rows]


def _in_clause(ids: list[str]) -> str:
    return ",".join("?" for _ in ids)


def versions_for(connection: sqlite3.Connection, commitment_ids: list[str]) -> list[dict[str, Any]]:
    if not commitment_ids:
        return []
    out: list[dict[str, Any]] = []
    for start in range(0, len(commitment_ids), 500):
        chunk = commitment_ids[start : start + 500]
        out.extend(
            dict(row)
            for row in connection.execute(
                f"""
                SELECT id, commitment_id, version, goal_id, depth_preset, due_hint,
                       provenance_json, change_reason, created_at
                FROM commitment_versions
                WHERE commitment_id IN ({_in_clause(chunk)})
                ORDER BY commitment_id, version
                """,
                chunk,
            ).fetchall()
        )
    return out


def head_targets_for(connection: sqlite3.Connection, version_ids: list[str]) -> list[dict[str, Any]]:
    if not version_ids:
        return []
    out: list[dict[str, Any]] = []
    for start in range(0, len(version_ids), 500):
        chunk = version_ids[start : start + 500]
        out.extend(
            dict(row)
            for row in connection.execute(
                f"""
                SELECT commitment_version_id, target_kind, target_ref
                FROM commitment_target_versions
                WHERE commitment_version_id IN ({_in_clause(chunk)})
                ORDER BY commitment_version_id, id
                """,
                chunk,
            ).fetchall()
        )
    return out


def events_for(connection: sqlite3.Connection, commitment_ids: list[str]) -> list[dict[str, Any]]:
    if not commitment_ids:
        return []
    out: list[dict[str, Any]] = []
    for start in range(0, len(commitment_ids), 500):
        chunk = commitment_ids[start : start + 500]
        out.extend(
            dict(row)
            for row in connection.execute(
                f"""
                SELECT id, commitment_id, kind, detail_json, created_at
                FROM commitment_events
                WHERE commitment_id IN ({_in_clause(chunk)})
                ORDER BY commitment_id, created_at, id
                """,
                chunk,
            ).fetchall()
        )
    return out


def attempts_for_anchor(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Every attempt's FSRS-eligibility inputs, newest last per item (§5.3 anchor)."""

    rows = connection.execute(
        """
        SELECT id, practice_item_id, created_at, attempt_type, primed, hints_used
        FROM practice_attempts
        ORDER BY practice_item_id, created_at, id
        """
    ).fetchall()
    return [dict(row) for row in rows]


def attempts_since(connection: sqlite3.Connection, item_ids: list[str], since: str) -> list[dict[str, Any]]:
    """Attempts on these items at or after ``since`` (a check's date), oldest first."""

    if not item_ids:
        return []
    out: list[dict[str, Any]] = []
    for start in range(0, len(item_ids), 500):
        chunk = item_ids[start : start + 500]
        out.extend(
            dict(row)
            for row in connection.execute(
                f"""
                SELECT id, practice_item_id, created_at
                FROM practice_attempts
                WHERE practice_item_id IN ({_in_clause(chunk)}) AND created_at >= ?
                ORDER BY created_at, id
                """,
                [*chunk, since],
            ).fetchall()
        )
    return out


def surprise_factors(connection: sqlite3.Connection) -> dict[str, float]:
    """Each attempt's recorded FSRS interval factor (the fixture reproduction test)."""

    present = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'attempt_surprise'"
    ).fetchone()
    if present is None:
        return {}
    return {
        str(row["attempt_id"]): float(row["fsrs_interval_factor"])
        for row in connection.execute(
            "SELECT attempt_id, fsrs_interval_factor FROM attempt_surprise WHERE fsrs_interval_factor IS NOT NULL"
        ).fetchall()
    }


__all__ = [
    "attempts_for_anchor",
    "attempts_since",
    "commitment_tables_present",
    "commitments_covering_items",
    "events_for",
    "head_targets_for",
    "surprise_factors",
    "versions_for",
]

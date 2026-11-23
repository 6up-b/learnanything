"""A read of the cue judge's ``passage_links`` (migration 215) shared by the scratchpads' proposals and the menus'
promoted rows (spec §9.1, §10.6: "from the same machinery"): the other passages a link ties to the same learner
problem as these passages. No write: its writers are the cue judge's (``db.stores.reader_cue_links``).
"""
from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from typing import Any


def _present(connection: sqlite3.Connection) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'passage_links'"
                              ).fetchone() is not None


def links_elsewhere(connection: sqlite3.Connection, places: Iterable[tuple[str, str]]) -> list[dict[str, Any]]:
    """Every passage link to a passage other than ``places`` tied to a problem (a misconception, a hypothesis, a
    named gap, a recurrence group, a demonstrated facet, an unchecked claim) a link on ``places`` names, best first:
    by the link's own ``pick_rank`` (the cue judge's rank for this learner), then when it was made, then its id."""

    here = {(str(extraction_id), str(span_id)) for extraction_id, span_id in places}
    if not here or not _present(connection):
        return []
    targets: set[tuple[str, str]] = set()
    for extraction_id, span_id in sorted(here):
        targets.update((str(row[0]), str(row[1])) for row in connection.execute(
            "SELECT target_kind, target_id FROM passage_links WHERE extraction_id = ? AND span_id = ?",
            (extraction_id, span_id)))
    found: dict[str, dict[str, Any]] = {}
    for target_kind, target_id in sorted(targets):
        cursor = connection.execute(
            "SELECT id, extraction_id, span_id, target_kind, target_id, relation, quote, pick_rank, ledger_id, "
            "created_at FROM passage_links WHERE target_kind = ? AND target_id = ?", (target_kind, target_id))
        names = [column[0] for column in cursor.description]
        for raw in cursor.fetchall():
            row = dict(zip(names, raw, strict=True))
            if (str(row["extraction_id"]), str(row["span_id"])) not in here:
                found[str(row["id"])] = row
    return sorted(found.values(), key=lambda row: (int(row["pick_rank"]), str(row["created_at"]), str(row["id"])))


__all__ = ["links_elsewhere"]

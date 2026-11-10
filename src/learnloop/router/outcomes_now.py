"""Every logged router decision's outcome as of now, derived from the ledgers at read time (read-only).

``router_outcomes`` is a rebuild cache: it holds what the last rebuild derived, so a decision made since, or one
whose attempt completed since, reads stale there. The readers that answer "what happened next"
(``learnloop router decisions``, ``learnloop router report`` and ``learnloop why``) derive it here instead, from
the same ledgers and with the same inputs a rebuild uses.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def outcomes_now(connection: sqlite3.Connection, loaded: Any, sqlite_path: Path) -> dict[str, dict[str, Any]]:
    """``{decision_id: outcome row}`` for every logged router decision, as :func:`derive_router_outcomes` derives it
    now for ``loaded``'s vault (its servable items, its outcome version, its Reader exposures)."""

    from learnloop.data_capture import reading_exposures
    from learnloop.db.repositories import Repository
    from learnloop.router.outcomes import derive_router_outcomes, outcome_version_for, servable_items_by_learning_object
    from learnloop.substrate.canonical_projection import held_for_review_attempts, pfc_assessments

    attempt_ids = [row[0] for row in connection.execute("SELECT id FROM practice_attempts")]
    version = outcome_version_for(loaded.config)
    rows = derive_router_outcomes(
        connection,
        pfc_states=pfc_assessments(connection, attempt_ids),
        servable_items_by_lo=servable_items_by_learning_object(loaded),
        held_attempt_ids=held_for_review_attempts(connection),
        outcome_version=version,
        reader_exposures=reading_exposures.for_version(connection, loaded, Repository.attach(sqlite_path,
                                                                                             read_only=True), version),
    )
    return {str(row["decision_id"]): row for row in rows}

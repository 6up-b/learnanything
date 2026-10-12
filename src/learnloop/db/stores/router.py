"""The only SQL writer for router R1's tables (migration 176).

``router_decisions`` is a RAW_LEDGER: append-only (triggers refuse UPDATE and
DELETE), idempotent on ``receipt_key``, never cleared by replay.
``router_outcomes`` is DERIVED: its one replayer replaces it whole. Callers own
the transaction (``with repository.atomic(), repository.connection() as
connection``), except :func:`record_learner_pick`, which runs inside the offer
bind's own transaction.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
import sqlite3
from typing import Any

from learnloop.ids import new_ulid

#: Shape version of a ``router_decisions`` row (its JSON columns included).
ROUTER_LOG_VERSION = "router_decisions_v1"

DECISION_COLUMNS: tuple[str, ...] = (
    "id", "receipt_key", "decision_kind", "surface", "mode", "policy",
    "algorithm_version", "log_version", "session_id", "parent_decision_id",
    "scheduler_slate_id", "controller_decision_id", "snapshot_hash", "design",
    "seed", "candidates_json", "exclusions_json", "candidate_count", "chosen_ref",
    "chosen_practice_item_id", "chosen_learning_object_id",
    "chosen_scheduler_candidate_id", "propensity", "propensity_kind",
    "learner_pick", "fallback", "mixture_weights_json", "model_distributions_json",
    "sensor_answers_json", "question_set_version", "model_ids_json", "card_hash",
    "similar_decision_ids_json", "latency_ms", "cost_usd", "detail_json",
    "created_at",
)

OUTCOME_COLUMNS: tuple[str, ...] = (
    "decision_id", "outcome_version", "target_practice_item_id",
    "target_learning_object_id", "action_status", "action_attempt_id",
    "r_next_status", "r_next_value", "r_next_attempt_id", "r_next_elapsed_seconds",
    "r_next_skipped", "r_cold_status", "r_cold_value", "r_cold_attempt_id",
    "r_cold_gap_seconds", "r_cold_skipped", "s_status", "s_value", "s_alpha",
    "observed_through", "detail_json",
)


def insert_router_decision(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool:
    """Append one decision; a repeated ``receipt_key`` is a no-op (returns False)."""

    cursor = connection.execute(
        f"INSERT OR IGNORE INTO router_decisions ({','.join(DECISION_COLUMNS)}) "
        f"VALUES ({','.join('?' for _ in DECISION_COLUMNS)})",
        tuple(row.get(column) for column in DECISION_COLUMNS),
    )
    return cursor.rowcount > 0


def record_learner_pick(
    connection: sqlite3.Connection,
    *,
    scheduler_candidate_id: str,
    practice_item_id: str,
    session_id: str,
    entry_surface: str,
    submission_id: str | None,
    created_at: str,
) -> str | None:
    """Log a learner pick that overrides a logged Today offer's choice.

    Called when a submission first binds to an offered candidate. Taking the
    offer's own head is the logged decision being served, so it writes nothing;
    neither does a candidate whose offer was never logged. The pick has no
    propensity (it was not sampled); ``detail_json`` keeps the offer policy's
    probability of the picked item for later analysis. Returns the new id.
    """

    parent = connection.execute(
        """SELECT d.* FROM router_decisions d
           JOIN scheduler_slate_candidates c ON c.slate_id = d.scheduler_slate_id
           WHERE c.id = ? AND d.decision_kind = 'today_offer'""",
        (scheduler_candidate_id,),
    ).fetchone()
    if parent is None or parent["chosen_scheduler_candidate_id"] == scheduler_candidate_id:
        return None
    candidate = connection.execute(
        "SELECT learning_object_id FROM scheduler_slate_candidates WHERE id = ?",
        (scheduler_candidate_id,),
    ).fetchone()
    offered_probability = None
    try:
        for entry in json.loads(parent["candidates_json"] or "[]"):
            if entry.get("ref") == practice_item_id and entry.get("kind") == "item":
                offered_probability = entry.get("propensity")
                break
    except (TypeError, ValueError):  # pragma: no cover - the parent row is ours
        offered_probability = None
    decision_id = new_ulid()
    inserted = insert_router_decision(
        connection,
        {
            "id": decision_id,
            "receipt_key": f"learner_pick:{scheduler_candidate_id}",
            "decision_kind": "learner_pick",
            "surface": entry_surface,
            "mode": parent["mode"],
            "policy": "learner",
            "algorithm_version": parent["algorithm_version"],
            "log_version": ROUTER_LOG_VERSION,
            "session_id": session_id,
            "parent_decision_id": parent["id"],
            "scheduler_slate_id": parent["scheduler_slate_id"],
            "controller_decision_id": None,
            "snapshot_hash": parent["snapshot_hash"],
            "design": None,
            "seed": None,
            # The candidate set is the parent offer's; it is not copied.
            "candidates_json": "[]",
            "exclusions_json": "{}",
            "candidate_count": parent["candidate_count"],
            "chosen_ref": practice_item_id,
            "chosen_practice_item_id": practice_item_id,
            "chosen_learning_object_id": candidate["learning_object_id"] if candidate else None,
            "chosen_scheduler_candidate_id": scheduler_candidate_id,
            "propensity": None,
            "propensity_kind": "none",
            "learner_pick": 1,
            "detail_json": json.dumps(
                {
                    "overrode_ref": parent["chosen_ref"],
                    "overrode_scheduler_candidate_id": parent["chosen_scheduler_candidate_id"],
                    "offer_probability_of_pick": offered_probability,
                    "submission_id": submission_id,
                },
                sort_keys=True,
            ),
            "created_at": created_at,
        },
    )
    return decision_id if inserted else None


def replace_router_outcomes(connection: sqlite3.Connection, rows: Iterable[Mapping[str, Any]]) -> int:
    """Replace the derived outcome cache whole (its one replayer only)."""

    connection.execute("DELETE FROM router_outcomes")
    values = [tuple(row.get(column) for column in OUTCOME_COLUMNS) for row in rows]
    connection.executemany(
        f"INSERT INTO router_outcomes ({','.join(OUTCOME_COLUMNS)}) "
        f"VALUES ({','.join('?' for _ in OUTCOME_COLUMNS)})",
        values,
    )
    return len(values)


def router_decision_rows(
    connection: sqlite3.Connection, *, limit: int | None = None
) -> list[dict[str, Any]]:
    """Decisions oldest first (the newest ``limit`` when given)."""

    if limit is None:
        rows = connection.execute("SELECT * FROM router_decisions ORDER BY created_at, id").fetchall()
        return [dict(row) for row in rows]
    rows = connection.execute(
        "SELECT * FROM router_decisions ORDER BY created_at DESC, id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [dict(row) for row in reversed(rows)]


def router_outcome_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute("SELECT * FROM router_outcomes ORDER BY decision_id").fetchall()
    return [dict(row) for row in rows]

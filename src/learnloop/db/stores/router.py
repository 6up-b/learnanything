"""The only SQL writer for router R1's tables (migration 181).

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
import logging
import sqlite3
from typing import Any

from learnloop.ids import new_ulid

logger = logging.getLogger(__name__)

#: Shape version of a ``router_decisions`` row (its JSON columns included).
ROUTER_LOG_VERSION = "router_decisions_v1"

#: The assignment mechanisms a decision row may name in ``design`` (NULL when
#: the choice was not drawn). Registered here, where every row is written, so
#: two mechanisms never share a name (R2 adds ``model_mixture``):
#:
#: * ``scheduler_seeded_exploration``: the legacy Today queue's own epsilon
#:   exploration. With probability ``selection_exploration_rate`` one near-tie
#:   within ``selection_exploration_reward_window`` of the best reward, chosen
#:   uniformly, moves to the front; the roll and the choice are hashes of
#:   (session, UTC date, candidate ids). It runs inside the build and is logged
#:   with the offer, after selection.
#: * ``epsilon_tiebreak``: ``randomization_layer.epsilon_tiebreak`` (P4 §9.3):
#:   uniform over the 5 % relative tie set, seeded per decision and persisted in
#:   ``policy_experiment_assignments`` before selection. The staged P2 path's
#:   within-block EVSI choice uses it.
#: * ``model_mixture`` (router R2b, mvp-0.24; ``randomization_layer``'s fourth
#:   design): a two-stage draw from the staged rule, the Decider and the router
#:   LLM over the top-k reversible candidates, each kept at ``epsilon_min`` or
#:   above; the seed, the weights, every component's distribution and the
#:   propensity are on the row, written in the block's transaction.
ROUTER_DESIGNS: dict[str, str] = {
    "scheduler_seeded_exploration": "legacy Today queue epsilon exploration (seeded hash, logged with the offer)",
    "epsilon_tiebreak": "randomization_layer epsilon tie-break (P4 §9.3, persisted before selection)",
    "model_mixture": "randomization_layer model mixture (router R2b: staged, Decider, LLM; eps floor; exact)",
}

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
    "observed_through",
    # Owner decision D12: the coldness covariates of the R_next and R_cold
    # attempts, and of every later attempt the one-day rule considered.
    "r_next_since_item_seconds", "r_next_since_facet_seconds", "r_next_since_lo_seconds",
    "r_next_intervening_attempts", "r_next_predicted_retrievability", "r_next_reveal_amount",
    "r_cold_since_item_seconds", "r_cold_since_facet_seconds", "r_cold_since_lo_seconds",
    "r_cold_intervening_attempts", "r_cold_predicted_retrievability", "r_cold_reveal_amount",
    "coldness_candidates_json", "detail_json",
    # Router R2a (migration 202): how the action was bound (presentation |
    # candidate | session_rule) and the R_next / R_cold attempts' answer-key
    # status (owner Q13: a covariate, never an exclusion).
    "action_binding", "r_next_reference_status", "r_cold_reference_status",
)

#: Router R2a (migration 202): one stored payload per decision and kind.
PAYLOAD_COLUMNS: tuple[str, ...] = (
    "id", "decision_id", "kind", "format_version", "content_hash", "content_json", "content_text", "created_at",
)


def insert_router_decision(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool:
    """Append one decision; a repeated ``receipt_key`` is a no-op (returns False).

    Only the receipt key's uniqueness is ignored: a row that breaks a CHECK or
    NOT NULL constraint raises (``sqlite3.IntegrityError``), and so does an
    unregistered ``design`` (``ValueError``), so a malformed decision is never
    mistaken for a duplicate. Callers inside another transaction use
    :func:`append_router_decision`, which isolates and reports the refusal.
    """

    design = row.get("design")
    if design is not None and design not in ROUTER_DESIGNS:
        raise ValueError(f"unregistered router decision design {design!r}")
    cursor = connection.execute(
        f"INSERT INTO router_decisions ({','.join(DECISION_COLUMNS)}) "
        f"VALUES ({','.join('?' for _ in DECISION_COLUMNS)}) "
        "ON CONFLICT(receipt_key) DO NOTHING",
        tuple(row.get(column) for column in DECISION_COLUMNS),
    )
    return cursor.rowcount > 0


def append_router_decision(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool:
    """Append one decision inside the caller's transaction, never failing it.

    A savepoint isolates the insert: a refused row rolls back alone and is
    logged as a warning (it is not a duplicate), and the caller's own writes
    (an offer receipt) commit as usual. Returns whether a row was written.
    """

    connection.execute("SAVEPOINT router_decision_append")
    try:
        inserted = insert_router_decision(connection, row)
    except (sqlite3.Error, ValueError):
        connection.execute("ROLLBACK TO router_decision_append")
        connection.execute("RELEASE router_decision_append")
        logger.warning(
            "router R1: the decision ledger refused %s row %s; not logged",
            row.get("decision_kind"), row.get("receipt_key"), exc_info=True,
        )
        return False
    connection.execute("RELEASE router_decision_append")
    return inserted


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

    Called when a submission (or a teach-back conversation) first binds to an
    offered candidate. Taking the offer's own head is the logged decision being
    served, so it writes nothing; neither does a candidate whose offer was never
    logged. An offer that served no head (the full list while the daily plan
    serves Today, ``propensity_kind = 'not_served'``) has no head to take, so
    every bind from it, its first item included, is a pick. The pick has no
    propensity (it was not sampled); ``detail_json`` keeps the offer policy's
    probability of the picked item for later analysis. Returns the new id.
    Raises on a database error: the caller isolates it (the bind never fails
    because logging did).
    """

    if connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='router_decisions'"
    ).fetchone() is None:
        # A database attached without migrations (a historical copy) has no
        # decision ledger, so nothing it offered was logged.
        return None
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
        entries = json.loads(parent["candidates_json"] or "[]")
        by_ref = {entry.get("ref"): entry for entry in entries}
        entry = by_ref.get(practice_item_id)
        if entry is not None and entry.get("kind") == "item":
            # A pinned presentation's mass is logged on "continue" (one
            # distribution, continue counted once).
            source = by_ref.get(entry["served_as"]) if entry.get("served_as") else entry
            offered_probability = (source or entry).get("propensity")
    except (TypeError, ValueError, AttributeError):  # pragma: no cover - the parent row is ours
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
                    "offer_served_head": parent["propensity_kind"] != "not_served",
                    "submission_id": submission_id,
                },
                sort_keys=True,
            ),
            "created_at": created_at,
        },
    )
    return decision_id if inserted else None


def router_payloads_present(connection: sqlite3.Connection) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='router_decision_payloads'"
    ).fetchone() is not None


def append_router_payload(connection: sqlite3.Connection, row: Mapping[str, Any]) -> bool:
    """Store one decision payload (router R2a: its learner-state card) inside
    the caller's transaction, never failing it: a refused row rolls back alone
    with a warning. Idempotent on ``(decision_id, kind)``."""

    if not router_payloads_present(connection):
        return False
    connection.execute("SAVEPOINT router_payload_append")
    try:
        cursor = connection.execute(
            f"INSERT INTO router_decision_payloads ({','.join(PAYLOAD_COLUMNS)}) "
            f"VALUES ({','.join('?' for _ in PAYLOAD_COLUMNS)}) "
            "ON CONFLICT(decision_id, kind) DO NOTHING",
            tuple(row.get(column) for column in PAYLOAD_COLUMNS),
        )
    except sqlite3.Error:
        connection.execute("ROLLBACK TO router_payload_append")
        connection.execute("RELEASE router_payload_append")
        logger.warning("router R2a: payload %s of decision %s not stored", row.get("kind"), row.get("decision_id"),
                       exc_info=True)
        return False
    connection.execute("RELEASE router_payload_append")
    return cursor.rowcount > 0


def prune_router_payloads(connection: sqlite3.Connection, *, before: str) -> int:
    """Delete payloads stored before ``before`` (``router.payload_retention_days``).

    The payload table is workflow state: the card's hash stays on its decision
    row, and replay never reads a payload."""

    if not router_payloads_present(connection):
        return 0
    return connection.execute("DELETE FROM router_decision_payloads WHERE created_at < ?", (before,)).rowcount


def router_payload(connection: sqlite3.Connection, decision_id: str, kind: str) -> dict[str, Any] | None:
    if not router_payloads_present(connection):
        return None
    row = connection.execute(
        "SELECT * FROM router_decision_payloads WHERE decision_id = ? AND kind = ?", (decision_id, kind)
    ).fetchone()
    return dict(row) if row is not None else None


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

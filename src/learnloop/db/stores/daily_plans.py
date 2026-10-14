"""The only SQL writer for daily-loop DL1 plan rows (migration 180; built as 174).

``daily_plans`` is WORKFLOW state (status, budget, the remembered minutes).
A plan's blocks are ``attention_blocks`` rows carrying the DL1 columns
(``daily_plan_id``, ``plan_ordinal``, ``lane``, ``chosen_by``, ``decision_ref``,
``reading_json``); every decision about them is an append-only
``attention_block_events`` receipt. A decision that is not a block (a stop,
a pick served after the plan closed) is a receipt row: an ``attention_blocks``
row of the plan with a NULL ``plan_ordinal`` and its own events. Nothing here is evidence, and replay never
reads these rows: the only rebuild reader is the learner field's outcome view
(an analysis read model, not evidence), which labels a plan-served attempt's
serving kind from its ``item_served`` receipt (owner decision 2026-10-12,
:func:`plan_served_origins`). Callers own the transaction (``with
repository.atomic(), repository.connection() as connection``).

Two read helpers serve the owner's decisions of 2026-10-12:
:func:`open_diagnosed_problem_learning_object_ids` (what the repair lane means)
and :func:`plan_served_origins` (the field's ``daily_plan`` serving kind).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
import sqlite3
from typing import Any

_PLAN_COLUMNS = (
    "id", "local_date", "kind", "parent_plan_id", "minutes_budget", "remembered_minutes",
    "minutes_source", "split_json", "admission_json", "estimator_version", "source",
    "chooser", "status", "stop_reason", "algorithm_version", "config_hash", "created_at",
    "updated_at", "completed_at",
)
_PLAN_UPDATABLE = frozenset(
    {
        "minutes_budget", "remembered_minutes", "minutes_source", "split_json", "status",
        "stop_reason", "updated_at", "completed_at",
    }
)


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _loads(value: str | None) -> Any:
    return json.loads(value) if value else None


def insert_plan(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    values = dict(row)
    for key in ("split_json", "admission_json"):
        if not isinstance(values.get(key), str):
            values[key] = _json(values.get(key) or {})
    connection.execute(
        f"INSERT INTO daily_plans ({','.join(_PLAN_COLUMNS)}) "
        f"VALUES ({','.join('?' for _ in _PLAN_COLUMNS)})",
        tuple(values.get(column) for column in _PLAN_COLUMNS),
    )


def update_plan(connection: sqlite3.Connection, plan_id: str, **fields: Any) -> None:
    unknown = set(fields) - _PLAN_UPDATABLE
    if unknown:
        raise ValueError(f"daily_plans columns not updatable: {sorted(unknown)}")
    if not fields:
        return
    values = dict(fields)
    if "split_json" in values and not isinstance(values["split_json"], str):
        values["split_json"] = _json(values["split_json"])
    assignments = ", ".join(f"{column} = ?" for column in values)
    connection.execute(
        f"UPDATE daily_plans SET {assignments} WHERE id = ?",
        (*values.values(), plan_id),
    )


def abandon_open_plans_before(
    connection: sqlite3.Connection, local_date: str, *, now: str
) -> int:
    """An open plan from an earlier day is abandoned (§6.10): progress is kept elsewhere."""

    cursor = connection.execute(
        "UPDATE daily_plans SET status = 'abandoned', stop_reason = 'day_ended', "
        "updated_at = ?, completed_at = COALESCE(completed_at, ?) "
        "WHERE status = 'open' AND local_date < ?",
        (now, now, local_date),
    )
    return cursor.rowcount


def insert_plan_block(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    connection.execute(
        "INSERT INTO attention_blocks(id, session_id, commitment_id, action, subtype, "
        "budget_minutes, neighborhood_json, exit_rules_json, short_circuit_reason, "
        "content_hash, created_at, daily_plan_id, plan_ordinal, lane, chosen_by, "
        "decision_ref, reading_json) VALUES (?, ?, NULL, ?, ?, ?, ?, '[]', ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            row["id"], row.get("session_id"), row["action"], row.get("subtype"),
            float(row["budget_minutes"]), _json(dict(row.get("neighborhood") or {})),
            row.get("short_circuit_reason"), row["content_hash"], row["created_at"],
            row["daily_plan_id"],
            # NULL for a plan-level receipt row (a stop decision, a pick after
            # the plan closed): it is not one of the plan's numbered blocks.
            int(row["plan_ordinal"]) if row.get("plan_ordinal") is not None else None,
            row.get("lane"), row["chosen_by"],
            row.get("decision_ref"),
            _json(row["reading"]) if row.get("reading") is not None else None,
        ),
    )


def append_block_event(
    connection: sqlite3.Connection,
    *,
    event_id: str,
    block_id: str,
    kind: str,
    detail: Mapping[str, Any] | None,
    created_at: str,
) -> int:
    row = connection.execute(
        "SELECT COALESCE(MAX(event_ordinal), 0) AS m FROM attention_block_events WHERE block_id = ?",
        (block_id,),
    ).fetchone()
    ordinal = int(row[0]) + 1
    connection.execute(
        "INSERT INTO attention_block_events(id, block_id, event_ordinal, kind, detail_json, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (event_id, block_id, ordinal, kind, _json(dict(detail)) if detail is not None else None, created_at),
    )
    return ordinal


# -- reads -----------------------------------------------------------------


def _plan_dict(row: sqlite3.Row | Mapping[str, Any]) -> dict[str, Any]:
    plan = dict(row)
    plan["split"] = _loads(plan.pop("split_json", None)) or {}
    plan["admission"] = _loads(plan.pop("admission_json", None)) or {}
    return plan


def plan_by_id(connection: sqlite3.Connection, plan_id: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT * FROM daily_plans WHERE id = ?", (plan_id,)).fetchone()
    return _plan_dict(row) if row is not None else None


def plans_for_date(connection: sqlite3.Connection, local_date: str) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT * FROM daily_plans WHERE local_date = ? ORDER BY created_at, id", (local_date,)
    ).fetchall()
    return [_plan_dict(row) for row in rows]


def latest_plan(connection: sqlite3.Connection) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM daily_plans ORDER BY created_at DESC, id DESC LIMIT 1"
    ).fetchone()
    return _plan_dict(row) if row is not None else None


def all_plans(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = connection.execute("SELECT * FROM daily_plans ORDER BY created_at, id").fetchall()
    return [_plan_dict(row) for row in rows]


def plan_blocks(connection: sqlite3.Connection, plan_ids: Iterable[str]) -> list[dict[str, Any]]:
    ids = list(plan_ids)
    if not ids:
        return []
    marks = ",".join("?" for _ in ids)
    rows = connection.execute(
        f"SELECT * FROM attention_blocks WHERE daily_plan_id IN ({marks}) "
        "ORDER BY daily_plan_id, plan_ordinal",
        ids,
    ).fetchall()
    blocks = []
    for row in rows:
        block = dict(row)
        block["neighborhood"] = _loads(block.pop("neighborhood_json", None)) or {}
        block["reading"] = _loads(block.pop("reading_json", None))
        blocks.append(block)
    return blocks


def block_events_for(connection: sqlite3.Connection, block_ids: Iterable[str]) -> list[dict[str, Any]]:
    ids = list(block_ids)
    if not ids:
        return []
    marks = ",".join("?" for _ in ids)
    rows = connection.execute(
        f"SELECT * FROM attention_block_events WHERE block_id IN ({marks}) "
        "ORDER BY block_id, event_ordinal",
        ids,
    ).fetchall()
    events = []
    for row in rows:
        event = dict(row)
        event["detail"] = _loads(event.pop("detail_json", None)) or {}
        events.append(event)
    return events


def daily_plan_tables_present(connection: sqlite3.Connection) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'daily_plans'"
    ).fetchone()
    return row is not None


#: Hypothesis head statuses that are still an open problem: a candidate (the
#: holding pen) or a validated (promoted) cause. ``retired`` (withdrawn, e.g.
#: by a confirmed repair) and ``demoted`` (refuted) heads are resolved.
OPEN_HYPOTHESIS_STATUSES = ("candidate", "validated")


def open_learner_state_hypotheses(
    connection: sqlite3.Connection, learning_object_ids: Iterable[str] | None = None
) -> list[dict[str, Any]]:
    """The unresolved causal hypotheses: THE resolution predicate (owner decision 2026-10-12).

    The latest version of each ``learner_state`` episode whose status is still
    ``candidate`` or ``validated``, unless it is a validated cause whose
    promoted misconception has since been resolved. Newest first; each row
    carries its id, LO, status, statement, ``created_at``, the evidence it
    rests on (``attempt_id``, ``error_event_id``) and any
    ``promoted_misconception_id``. ``learning_object_ids`` limits the LOs
    (router R2a's card, review F8, reads the same predicate). Read-only.
    """

    wanted = None if learning_object_ids is None else sorted({str(lo) for lo in learning_object_ids})
    if wanted is not None and not wanted:
        return []
    scope = "" if wanted is None else f" AND h.learning_object_id IN ({','.join('?' for _ in wanted)})"
    rows = connection.execute(
        f"""
        SELECT h.id, h.learning_object_id, h.status, h.statement, h.created_at, h.attempt_id,
               h.error_event_id, h.evidence_json
          FROM causal_hypotheses h
         WHERE h.cause_scope = 'learner_state'
           AND h.status IN ('candidate', 'validated'){scope}
           AND h.version = (
             SELECT MAX(head.version) FROM causal_hypotheses head
              WHERE head.episode_key = h.episode_key
           )
         ORDER BY h.created_at DESC, h.id DESC
        """,
        wanted or (),
    ).fetchall()
    resolved_misconceptions: set[str] | None = None
    open_rows: list[dict[str, Any]] = []
    for row in rows:
        if not row[1]:
            continue
        evidence = _loads(row[7])
        promoted = evidence.get("promoted_misconception_id") if isinstance(evidence, dict) else None
        if row[2] == "validated" and promoted:
            if resolved_misconceptions is None:
                resolved_misconceptions = {
                    str(value[0])
                    for value in connection.execute("SELECT id FROM misconceptions WHERE status = 'resolved'")
                }
            if str(promoted) in resolved_misconceptions:
                continue
        open_rows.append({
            "id": str(row[0]), "learning_object_id": str(row[1]), "status": str(row[2]), "statement": row[3],
            "created_at": row[4], "attempt_id": row[5], "error_event_id": row[6],
            "promoted_misconception_id": str(promoted) if promoted else None,
        })
    return open_rows


def open_diagnosed_problem_learning_object_ids(connection: sqlite3.Connection) -> frozenset[str]:
    """LOs with an open diagnosed problem: what "repair" means (owner decision 2026-10-12).

    An open diagnosed problem is either

    * an unresolved causal hypothesis (:func:`open_learner_state_hypotheses`):
      the latest version of a ``learner_state`` episode whose status is still
      ``candidate`` or ``validated``, unless it is a validated cause whose
      promoted misconception has since been resolved; or
    * an ``open`` unresolved-cause factor (on the LO of its attempt).

    Slice 1 M2's diagnoses and Slice 2 T1's recurrence groups write both
    through the shared normalizer; a confirmed repair closes the factor and
    withdraws its candidate hypotheses, so a fixed problem leaves the lane. A
    diagnosed slip (``transient_execution``) or an item, grader or interaction
    cause is not the learner's problem to repair. Read-only.
    """

    open_los = {row["learning_object_id"] for row in open_learner_state_hypotheses(connection)}
    for row in connection.execute(
        "SELECT DISTINCT a.learning_object_id FROM unresolved_cause_factors f "
        "JOIN practice_attempts a ON a.id = f.attempt_id WHERE f.status = 'open'"
    ):
        if row[0]:
            open_los.add(str(row[0]))
    return frozenset(open_los)


def plan_served_origins(connection: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    """Every plan ``item_served`` receipt, by practice item, oldest first.

    Each entry: ``served_at``, ``session_id``, ``scheduler_candidate_id`` and
    ``serving_origin`` (``daily_plan``, or ``learner_pick`` for a pick the plan
    served). The learner field reads these so a plan-served attempt is labelled
    ``daily_plan`` rather than ``unknown`` (owner decision 2026-10-12). Empty
    on a database without the plan tables. Read-only.
    """

    if not daily_plan_tables_present(connection):
        return {}
    rows = connection.execute(
        "SELECT e.detail_json, e.created_at FROM attention_block_events e "
        "JOIN attention_blocks b ON b.id = e.block_id "
        "WHERE e.kind = 'item_served' AND b.daily_plan_id IS NOT NULL "
        "ORDER BY e.created_at, e.id"
    ).fetchall()
    served: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        detail = _loads(row[0]) or {}
        item_id = detail.get("practice_item_id")
        if not item_id:
            continue
        served.setdefault(str(item_id), []).append(
            {
                "served_at": str(row[1]),
                "session_id": detail.get("session_id"),
                "scheduler_candidate_id": detail.get("scheduler_candidate_id"),
                "serving_origin": str(detail.get("serving_origin") or "daily_plan"),
            }
        )
    return served


__all__ = [
    "abandon_open_plans_before",
    "all_plans",
    "append_block_event",
    "block_events_for",
    "daily_plan_tables_present",
    "OPEN_HYPOTHESIS_STATUSES",
    "open_learner_state_hypotheses",
    "insert_plan",
    "insert_plan_block",
    "latest_plan",
    "open_diagnosed_problem_learning_object_ids",
    "plan_blocks",
    "plan_by_id",
    "plan_served_origins",
    "plans_for_date",
    "update_plan",
]

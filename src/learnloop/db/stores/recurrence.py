"""Slice 2 T1 persistence: recurrence groups (DERIVED) and escalation receipts.

The three ``hypothesis_recurrence_*`` tables are a projection: their only
writer is :func:`replace_recurrence_projection`, called by the recurrence
group builder (``learnloop.substrate.recurrence_groups``), which recomputes
them from raw ledgers. ``recurrence_escalations`` is an append-only receipt of
what an escalated repair showed.

The reads also serve the inputs the builder needs (diagnoses in force with
their validated citations, card taps, ``same_cause`` verdicts), so the
builder never writes SQL of its own.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.ids import new_ulid

DERIVED_TABLES = (
    "hypothesis_recurrence_groups",
    "hypothesis_recurrence_review",
    "hypothesis_recurrence_state",
)
ESCALATION_RESPONSES = ("escalation:helped", "escalation:didnt_help", "escalation:not_sure")


def _dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _loads(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _has_table(connection: sqlite3.Connection, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone() is not None


# -- the projection -------------------------------------------------------------------


def replace_recurrence_projection(
    connection: sqlite3.Connection,
    *,
    members: Sequence[Mapping[str, Any]],
    reviews: Sequence[Mapping[str, Any]],
    state: Mapping[str, Any],
) -> None:
    """Replace the whole projection inside the caller's transaction."""

    for table in DERIVED_TABLES:
        connection.execute(f'DELETE FROM "{table}"')
    connection.executemany(
        "INSERT INTO hypothesis_recurrence_groups(episode_key, statement_normalized, group_key, "
        "root_episode_key, class_count, joined_by, joined_by_ref, judge, builder_version) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                row["episode_key"], row["statement_normalized"], row["group_key"],
                row["root_episode_key"], int(row["class_count"]), row["joined_by"],
                row.get("joined_by_ref"), row.get("judge"), row["builder_version"],
            )
            for row in members
        ],
    )
    connection.executemany(
        "INSERT INTO hypothesis_recurrence_review(id, case_kind, left_ref, right_ref, "
        "blocking_left_ref, blocking_right_ref, source_ref, occurred_at, detail_json, builder_version) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                row["id"], row["case_kind"], row.get("left_ref"), row.get("right_ref"),
                row.get("blocking_left_ref"), row.get("blocking_right_ref"), row.get("source_ref"),
                row.get("occurred_at"), _dumps(row.get("detail") or {}), row["builder_version"],
            )
            for row in reviews
        ],
    )
    connection.execute(
        "INSERT INTO hypothesis_recurrence_state(scope, input_fingerprint, builder_version, active, "
        "group_count, member_count, review_count) VALUES ('vault', ?, ?, ?, ?, ?, ?)",
        (
            state["input_fingerprint"], state["builder_version"], 1 if state.get("active") else 0,
            int(state.get("group_count") or 0), int(state.get("member_count") or 0),
            int(state.get("review_count") or 0),
        ),
    )


def clear_recurrence_projection(connection: sqlite3.Connection) -> bool:
    """Empty the projection (the successor is off); True when rows were removed."""

    present = any(
        connection.execute(f'SELECT 1 FROM "{table}" LIMIT 1').fetchone() is not None
        for table in DERIVED_TABLES
    )
    if present:
        for table in DERIVED_TABLES:
            connection.execute(f'DELETE FROM "{table}"')
    return present


def recurrence_state(connection: sqlite3.Connection) -> dict[str, Any] | None:
    if not _has_table(connection, "hypothesis_recurrence_state"):
        return None
    cursor = connection.execute("SELECT * FROM hypothesis_recurrence_state WHERE scope = 'vault'")
    names = [column[0] for column in cursor.description]
    row = cursor.fetchone()
    if row is None:
        return None
    value = dict(zip(names, row))
    value["active"] = bool(value["active"])
    return value


def recurrence_group_map(connection: sqlite3.Connection) -> dict[str, str]:
    """normalized statement -> group key, for merged classes only."""

    try:
        rows = connection.execute(
            "SELECT DISTINCT statement_normalized, group_key FROM hypothesis_recurrence_groups"
        ).fetchall()
    except sqlite3.OperationalError:
        # A historical schema attached without migrations has no projection.
        return {}
    return {str(row[0]): str(row[1]) for row in rows}


def recurrence_group_rows(connection: sqlite3.Connection, group_key: str | None = None) -> list[dict[str, Any]]:
    if not _has_table(connection, "hypothesis_recurrence_groups"):
        return []
    query = "SELECT * FROM hypothesis_recurrence_groups"
    params: tuple[Any, ...] = ()
    if group_key is not None:
        query += " WHERE group_key = ?"
        params = (group_key,)
    cursor = connection.execute(query + " ORDER BY group_key, episode_key", params)
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def recurrence_review_rows(connection: sqlite3.Connection, case_kind: str | None = None) -> list[dict[str, Any]]:
    if not _has_table(connection, "hypothesis_recurrence_review"):
        return []
    query = "SELECT * FROM hypothesis_recurrence_review"
    params: tuple[Any, ...] = ()
    if case_kind is not None:
        query += " WHERE case_kind = ?"
        params = (case_kind,)
    cursor = connection.execute(query + " ORDER BY case_kind, occurred_at, id", params)
    names = [column[0] for column in cursor.description]
    rows = [dict(zip(names, row)) for row in cursor.fetchall()]
    for row in rows:
        row["detail"] = _loads(row.pop("detail_json"), {})
    return rows


# -- builder inputs (raw ledgers; read only) --------------------------------------------


def input_fingerprint_parts(connection: sqlite3.Connection) -> list[Any]:
    """Cheap counters over every ledger the builder reads (no JSON parsing)."""

    parts: list[Any] = []
    for table, where in (
        ("causal_hypotheses", ""),
        ("judgment_ledger", " WHERE task = 'same_cause'"),
        ("attempt_diagnoses", ""),
        ("diagnosis_context_receipts", ""),
        ("diagnosis_feedback", ""),
        ("blind_grade_records", ""),
    ):
        if not _has_table(connection, table):
            parts.append([table, None])
            continue
        row = connection.execute(f'SELECT COUNT(*), COALESCE(MAX(rowid), 0) FROM "{table}"{where}').fetchone()
        parts.append([table, int(row[0]), int(row[1])])
    return parts


def hypothesis_episode_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """One row per concrete episode: its FIRST version's identity fields.

    The normalized statement is stable across an episode's versions, so the
    first version (by created_at, id) defines the episode's statement class
    and its age. ``status`` and ``target_ref`` come from the episode's head.
    """

    if not _has_table(connection, "causal_hypotheses"):
        return []
    cursor = connection.execute(
        """
        SELECT h.episode_key, h.attempt_id, h.learning_object_id, h.statement,
               h.statement_normalized, h.cause_scope, h.status, h.target_ref_json,
               h.operation, h.created_at, h.id, h.version, h.evidence_json
          FROM causal_hypotheses h
         ORDER BY h.episode_key, h.version, h.created_at, h.id
        """
    )
    names = [column[0] for column in cursor.description]
    by_episode: dict[str, dict[str, Any]] = {}
    for raw in cursor.fetchall():
        row = dict(zip(names, raw))
        key = str(row["episode_key"])
        current = by_episode.get(key)
        if current is None:
            row["first_created_at"] = row["created_at"]
            row["first_id"] = row["id"]
            by_episode[key] = row
        else:
            # Head fields follow later versions; identity stays the first's.
            current.update(
                status=row["status"],
                target_ref_json=row["target_ref_json"],
                operation=row["operation"] or current.get("operation"),
                evidence_json=row["evidence_json"],
                id=row["id"],
                version=row["version"],
            )
    episodes = []
    for row in by_episode.values():
        if row.get("status") == "open_set":
            continue
        row["target_ref"] = _loads(row.pop("target_ref_json"), None)
        row["evidence"] = _loads(row.pop("evidence_json"), {})
        episodes.append(row)
    return sorted(episodes, key=lambda row: (str(row["first_created_at"]), str(row["episode_key"])))


def diagnoses_in_force(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Each attempt's live diagnosis in force, with its proposal and citations.

    The same eligibility rule as ``DiagnosisStoreMixin._diagnosis_in_force``:
    the attempt's latest live diagnosis, completed, for the attempt's current
    blind grade.
    """

    if not _has_table(connection, "attempt_diagnoses"):
        return []
    latest: dict[str, Any] = {}
    for row in connection.execute(
        "SELECT id, attempt_id, status, blind_grade_record_id, proposal_json, model, "
        "diagnosis_prompt_version, created_at FROM attempt_diagnoses WHERE mode = 'live' "
        "ORDER BY attempt_id, created_at, id"
    ):
        latest[str(row[1])] = row
    current: dict[str, str] = {}
    for row in connection.execute(
        "SELECT attempt_id, id FROM blind_grade_records ORDER BY attempt_id, created_at, id"
    ):
        current[str(row[0])] = str(row[1])
    receipts: dict[str, Any] = {}
    for row in connection.execute(
        "SELECT diagnosis_id, validated_citations_json, retrieval_json FROM diagnosis_context_receipts"
    ):
        receipts[str(row[0])] = row
    out: list[dict[str, Any]] = []
    for attempt_id, row in latest.items():
        if row[2] != "completed":
            continue
        record_id = row[3]
        if record_id is not None and current.get(attempt_id) not in (None, str(record_id)):
            continue
        receipt = receipts.get(str(row[0]))
        out.append(
            {
                "id": str(row[0]),
                "attempt_id": attempt_id,
                "proposal": _loads(row[4], {}) or {},
                "model": row[5],
                "prompt_version": row[6],
                "created_at": row[7],
                "validated_citations": _loads(receipt[1], []) if receipt is not None else [],
                "retrieval": _loads(receipt[2], {}) if receipt is not None else {},
            }
        )
    return sorted(out, key=lambda row: (str(row["created_at"]), row["id"]))


def diagnosis_with_citations(connection: sqlite3.Connection, diagnosis_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT id, attempt_id, proposal_json, created_at FROM attempt_diagnoses WHERE id = ?",
        (diagnosis_id,),
    ).fetchone()
    if row is None:
        return None
    receipt = connection.execute(
        "SELECT validated_citations_json FROM diagnosis_context_receipts WHERE diagnosis_id = ?",
        (diagnosis_id,),
    ).fetchone()
    return {
        "id": str(row[0]),
        "attempt_id": str(row[1]),
        "proposal": _loads(row[2], {}) or {},
        "created_at": row[3],
        "validated_citations": _loads(receipt[0], []) if receipt is not None else [],
    }


def not_same_mistake_taps(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    if not _has_table(connection, "diagnosis_feedback"):
        return []
    cursor = connection.execute(
        "SELECT id, diagnosis_id, attempt_id, cited_attempt_id, responded_at FROM diagnosis_feedback "
        "WHERE response = 'not_same_mistake' ORDER BY responded_at, id"
    )
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def same_cause_judgments(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    if not _has_table(connection, "judgment_ledger"):
        return []
    cursor = connection.execute(
        "SELECT * FROM judgment_ledger WHERE task = 'same_cause' ORDER BY created_at, id"
    )
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


# -- escalation receipts ----------------------------------------------------------------


def insert_escalation(
    connection: sqlite3.Connection,
    *,
    attempt_id: str,
    diagnosis_id: str,
    group_key: str,
    recurrence_count: int,
    earlier_attempt_ids: Iterable[str],
    repair_suggestion_id: str | None,
    repair_operator: str | None,
    prior_operators: Iterable[str],
    different_approach: bool,
    algorithm_version: str,
    clock: Clock | None = None,
) -> str | None:
    """Append once per (attempt, diagnosis); returns the id, or None if present."""

    existing = connection.execute(
        "SELECT id FROM recurrence_escalations WHERE attempt_id = ? AND diagnosis_id = ?",
        (attempt_id, diagnosis_id),
    ).fetchone()
    if existing is not None:
        return None
    escalation_id = new_ulid()
    connection.execute(
        "INSERT INTO recurrence_escalations(id, attempt_id, diagnosis_id, group_key, recurrence_count, "
        "earlier_attempt_ids_json, repair_suggestion_id, repair_operator, prior_operators_json, "
        "different_approach, algorithm_version, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            escalation_id, attempt_id, diagnosis_id, group_key, int(recurrence_count),
            _dumps(list(earlier_attempt_ids)), repair_suggestion_id, repair_operator,
            _dumps(sorted(set(prior_operators))), 1 if different_approach else 0,
            algorithm_version, utc_now_iso(clock),
        ),
    )
    return escalation_id


def _decode_escalation(names: Sequence[str], raw: Sequence[Any]) -> dict[str, Any]:
    row = dict(zip(names, raw))
    row["earlier_attempt_ids"] = _loads(row.pop("earlier_attempt_ids_json"), [])
    row["prior_operators"] = _loads(row.pop("prior_operators_json"), [])
    row["different_approach"] = bool(row["different_approach"])
    return row


def escalation_for_diagnosis(connection: sqlite3.Connection, diagnosis_id: str) -> dict[str, Any] | None:
    if not _has_table(connection, "recurrence_escalations"):
        return None
    cursor = connection.execute(
        "SELECT * FROM recurrence_escalations WHERE diagnosis_id = ? ORDER BY created_at, id LIMIT 1",
        (diagnosis_id,),
    )
    names = [column[0] for column in cursor.description]
    raw = cursor.fetchone()
    return _decode_escalation(names, raw) if raw is not None else None


def escalation_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    if not _has_table(connection, "recurrence_escalations"):
        return []
    cursor = connection.execute("SELECT * FROM recurrence_escalations ORDER BY created_at, id")
    names = [column[0] for column in cursor.description]
    return [_decode_escalation(names, raw) for raw in cursor.fetchall()]


class RecurrenceStoreMixin:
    """Repository conveniences over the module functions above."""

    def recurrence_group_map(self) -> dict[str, str]:
        with self.connection() as connection:  # type: ignore[attr-defined]
            return recurrence_group_map(connection)

    def recurrence_groups(self, group_key: str | None = None) -> list[dict[str, Any]]:
        with self.connection() as connection:  # type: ignore[attr-defined]
            return recurrence_group_rows(connection, group_key)

    def recurrence_review(self, case_kind: str | None = None) -> list[dict[str, Any]]:
        with self.connection() as connection:  # type: ignore[attr-defined]
            return recurrence_review_rows(connection, case_kind)

    def recurrence_state(self) -> dict[str, Any] | None:
        with self.connection() as connection:  # type: ignore[attr-defined]
            return recurrence_state(connection)

    def recurrence_escalation(self, diagnosis_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:  # type: ignore[attr-defined]
            return escalation_for_diagnosis(connection, diagnosis_id)

    def recurrence_escalations(self) -> list[dict[str, Any]]:
        with self.connection() as connection:  # type: ignore[attr-defined]
            return escalation_rows(connection)


__all__ = [
    "DERIVED_TABLES",
    "clear_recurrence_projection",
    "ESCALATION_RESPONSES",
    "RecurrenceStoreMixin",
    "diagnoses_in_force",
    "diagnosis_with_citations",
    "escalation_for_diagnosis",
    "escalation_rows",
    "hypothesis_episode_rows",
    "input_fingerprint_parts",
    "insert_escalation",
    "not_same_mistake_taps",
    "recurrence_group_map",
    "recurrence_group_rows",
    "recurrence_review_rows",
    "recurrence_state",
    "replace_recurrence_projection",
    "same_cause_judgments",
]

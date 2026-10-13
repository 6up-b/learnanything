"""The only SQL writer for the learner-text gap tables (migration 177).

``learner_text_gaps`` and ``learner_text_gap_reversals`` are RAW_LEDGER
(append-only, enforced by triggers): what a learner text was read as, what was
done with it, and the learner's one-tap reversals. ``learner_gap_check_advances``
and ``learner_gap_commitments`` are RECEIPT rows placement reads.
``learner_text_gap_jobs`` is the lease-fenced WORKFLOW queue. Callers own the
transaction.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import timedelta
import json
import sqlite3
from typing import Any

from learnloop.clock import parse_utc
from learnloop.ids import new_ulid

GAP_COLUMNS = (
    "id", "source_kind", "source_id", "attempt_id", "practice_item_id", "anchor_learning_object_id",
    "subject_id", "learner_text", "chooser", "context_judge", "context_kind", "decider_kind",
    "decider_json", "kind", "named_json", "action", "target_kind", "target_id", "target_subject_id",
    "match_basis", "edge_id", "created_concept_id", "created_learning_object_id", "seed_practice_item_id",
    "seed_status", "detail_json", "algorithm_version", "pipeline_version", "created_at",
)
_JSON_COLUMNS = ("decider_json", "named_json", "detail_json")


def _table_present(connection: sqlite3.Connection, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
    ).fetchone() is not None


def gap_tables_present(connection: sqlite3.Connection) -> bool:
    return _table_present(connection, "learner_text_gaps")


def _dumps(value: Any) -> str:
    return json.dumps(value if value is not None else {}, sort_keys=True, ensure_ascii=False)


def _decode(row: sqlite3.Row | Mapping[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    data = dict(row)
    for column in _JSON_COLUMNS + ("payload_json",):
        if column in data:
            try:
                data[column.removesuffix("_json")] = json.loads(data[column] or "{}")
            except (TypeError, ValueError):
                data[column.removesuffix("_json")] = {}
    return data


def _rows(connection: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, tuple(params))
    names = [column[0] for column in cursor.description]
    return [_decode(dict(zip(names, row, strict=True))) for row in cursor.fetchall()]  # type: ignore[misc]


# -- the ledger ----------------------------------------------------------------------


def insert_gap(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str:
    """Append one read learner text (``id`` minted when absent)."""

    values = dict(row)
    values.setdefault("id", new_ulid())
    for column in _JSON_COLUMNS:
        if not isinstance(values.get(column), str):
            values[column] = _dumps(values.get(column))
    connection.execute(
        f"INSERT INTO learner_text_gaps ({','.join(GAP_COLUMNS)}) VALUES ({','.join('?' for _ in GAP_COLUMNS)})",
        tuple(values.get(column) for column in GAP_COLUMNS),
    )
    return str(values["id"])


def gap(connection: sqlite3.Connection, gap_id: str) -> dict[str, Any] | None:
    found = _rows(connection, "SELECT * FROM learner_text_gaps WHERE id = ?", (gap_id,))
    return found[0] if found else None


def gap_for_source(connection: sqlite3.Connection, source_kind: str, source_id: str) -> dict[str, Any] | None:
    if not gap_tables_present(connection):
        return None
    found = _rows(
        connection, "SELECT * FROM learner_text_gaps WHERE source_kind = ? AND source_id = ?",
        (source_kind, source_id),
    )
    return found[0] if found else None


def gaps(
    connection: sqlite3.Connection,
    *,
    since: str | None = None,
    before: str | None = None,
    source_kind: str | None = None,
    learning_object_ids: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Gaps in written order, optionally windowed and scoped to target/anchor LOs."""

    if not gap_tables_present(connection):
        return []
    clauses, params = [], []
    if since is not None:
        clauses.append("created_at >= ?")
        params.append(since)
    if before is not None:
        clauses.append("created_at < ?")
        params.append(before)
    if source_kind is not None:
        clauses.append("source_kind = ?")
        params.append(source_kind)
    wanted = sorted(set(learning_object_ids)) if learning_object_ids is not None else None
    if wanted is not None:
        if not wanted:
            return []
        marks = ",".join("?" for _ in wanted)
        clauses.append(
            f"((target_kind = 'learning_object' AND target_id IN ({marks})) "
            f"OR anchor_learning_object_id IN ({marks}) OR created_learning_object_id IN ({marks}))"
        )
        params.extend([*wanted, *wanted, *wanted])
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    return _rows(connection, f"SELECT * FROM learner_text_gaps{where} ORDER BY created_at, id", params)


# -- reversals --------------------------------------------------------------------------


def insert_reversal(
    connection: sqlite3.Connection, *, gap_id: str, reversal: str, actor: str, created_at: str,
    detail: Mapping[str, Any] | None = None,
) -> str | None:
    """Append one reversal; None when this gap already has it (a repeated tap)."""

    if connection.execute(
        "SELECT 1 FROM learner_text_gap_reversals WHERE gap_id = ? AND reversal = ?", (gap_id, reversal)
    ).fetchone() is not None:
        return None
    reversal_id = new_ulid()
    connection.execute(
        "INSERT INTO learner_text_gap_reversals (id, gap_id, reversal, actor, detail_json, created_at) "
        "VALUES (?,?,?,?,?,?)",
        (reversal_id, gap_id, reversal, actor, _dumps(detail), created_at),
    )
    return reversal_id


def reversals(connection: sqlite3.Connection, gap_ids: Iterable[str] | None = None) -> list[dict[str, Any]]:
    if not _table_present(connection, "learner_text_gap_reversals"):
        return []
    if gap_ids is None:
        return _rows(connection, "SELECT * FROM learner_text_gap_reversals ORDER BY created_at, id")
    wanted = sorted(set(gap_ids))
    if not wanted:
        return []
    marks = ",".join("?" for _ in wanted)
    return _rows(
        connection,
        f"SELECT * FROM learner_text_gap_reversals WHERE gap_id IN ({marks}) ORDER BY created_at, id",
        wanted,
    )


# -- placement receipts ----------------------------------------------------------------


def insert_check_advance(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str:
    advance_id = str(row.get("id") or new_ulid())
    connection.execute(
        "INSERT INTO learner_gap_check_advances (id, gap_id, learning_object_id, intent, assumption_id, "
        "original_due, advanced_due, algorithm_version, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (
            advance_id, row["gap_id"], row["learning_object_id"], row["intent"], row.get("assumption_id"),
            row.get("original_due"), row["advanced_due"], row["algorithm_version"], row["created_at"],
        ),
    )
    return advance_id


def check_advances(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    if not _table_present(connection, "learner_gap_check_advances"):
        return []
    return _rows(connection, "SELECT * FROM learner_gap_check_advances ORDER BY created_at, id")


def insert_commitment(connection: sqlite3.Connection, row: Mapping[str, Any]) -> str:
    commitment_id = str(row.get("id") or new_ulid())
    connection.execute(
        "INSERT INTO learner_gap_commitments (id, gap_id, learning_object_id, practice_item_id, "
        "first_review_due, algorithm_version, created_at) VALUES (?,?,?,?,?,?,?)",
        (
            commitment_id, row["gap_id"], row["learning_object_id"], row.get("practice_item_id"),
            row["first_review_due"], row["algorithm_version"], row["created_at"],
        ),
    )
    return commitment_id


def commitments(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Light commitments whose creation the learner has not undone."""

    if not _table_present(connection, "learner_gap_commitments"):
        return []
    return _rows(
        connection,
        "SELECT c.* FROM learner_gap_commitments c WHERE NOT EXISTS ("
        " SELECT 1 FROM learner_text_gap_reversals r"
        " WHERE r.gap_id = c.gap_id AND r.reversal = 'undo_creation') ORDER BY c.created_at, c.id",
    )


# -- the job queue -------------------------------------------------------------------


def enqueue_job(
    connection: sqlite3.Connection, *, source_kind: str, source_id: str, now: str,
    payload: Mapping[str, Any] | None = None,
) -> str | None:
    """Queue one learner text; None when it is already queued or read."""

    if connection.execute(
        "SELECT 1 FROM learner_text_gap_jobs WHERE source_kind = ? AND source_id = ?", (source_kind, source_id)
    ).fetchone() is not None:
        return None
    job_id = new_ulid()
    connection.execute(
        "INSERT INTO learner_text_gap_jobs (id, source_kind, source_id, state, payload_json, created_at, updated_at) "
        "VALUES (?,?,?,'queued',?,?,?)",
        (job_id, source_kind, source_id, _dumps(payload), now, now),
    )
    return job_id


def jobs(connection: sqlite3.Connection, *, states: Iterable[str] | None = None) -> list[dict[str, Any]]:
    if not _table_present(connection, "learner_text_gap_jobs"):
        return []
    if states is None:
        return _rows(connection, "SELECT * FROM learner_text_gap_jobs ORDER BY created_at, id")
    wanted = sorted(set(states))
    marks = ",".join("?" for _ in wanted)
    return _rows(
        connection, f"SELECT * FROM learner_text_gap_jobs WHERE state IN ({marks}) ORDER BY created_at, id", wanted
    )


def job_for_source(connection: sqlite3.Connection, source_kind: str, source_id: str) -> dict[str, Any] | None:
    if not _table_present(connection, "learner_text_gap_jobs"):
        return None
    found = _rows(
        connection, "SELECT * FROM learner_text_gap_jobs WHERE source_kind = ? AND source_id = ?",
        (source_kind, source_id),
    )
    return found[0] if found else None


def lease_next_job(
    connection: sqlite3.Connection, *, owner: str, now: str, lease_seconds: float,
    source: tuple[str, str] | None = None,
) -> dict[str, Any] | None:
    """Claim the oldest runnable job (or the one for ``source``), or None."""

    current = parse_utc(now)
    params: list[Any] = []
    scope = ""
    if source is not None:
        scope = " AND source_kind = ? AND source_id = ?"
        params.extend(source)
    for row in _rows(
        connection,
        f"SELECT * FROM learner_text_gap_jobs WHERE state IN ('queued', 'leased'){scope} ORDER BY created_at, id",
        params,
    ):
        expires = parse_utc(row["lease_expires_at"]) if row.get("lease_expires_at") else None
        not_before = parse_utc(row["not_before"]) if row.get("not_before") else None
        runnable = (row["state"] == "queued" and (not_before is None or not_before <= current)) or (
            row["state"] == "leased" and (expires is None or expires <= current)
        )
        if not runnable:
            continue
        until = (current + timedelta(seconds=float(lease_seconds))).isoformat().replace("+00:00", "Z")
        cursor = connection.execute(
            "UPDATE learner_text_gap_jobs SET state = 'leased', lease_owner = ?, lease_expires_at = ?, "
            "lease_epoch = lease_epoch + 1, attempt_count = attempt_count + 1, updated_at = ? "
            "WHERE id = ? AND lease_epoch = ?",
            (owner, until, now, row["id"], row["lease_epoch"]),
        )
        if cursor.rowcount != 1:
            continue
        return job(connection, str(row["id"]))
    return None


def job(connection: sqlite3.Connection, job_id: str) -> dict[str, Any] | None:
    found = _rows(connection, "SELECT * FROM learner_text_gap_jobs WHERE id = ?", (job_id,))
    return found[0] if found else None


def holds_job(connection: sqlite3.Connection, job_id: str, *, owner: str, epoch: int) -> bool:
    return connection.execute(
        "SELECT 1 FROM learner_text_gap_jobs WHERE id = ? AND lease_owner = ? AND lease_epoch = ? AND state = 'leased'",
        (job_id, owner, epoch),
    ).fetchone() is not None


def save_job_payload(
    connection: sqlite3.Connection, job_id: str, payload: Mapping[str, Any], *, owner: str, epoch: int, now: str,
) -> bool:
    cursor = connection.execute(
        "UPDATE learner_text_gap_jobs SET payload_json = ?, updated_at = ? "
        "WHERE id = ? AND lease_owner = ? AND lease_epoch = ?",
        (_dumps(payload), now, job_id, owner, epoch),
    )
    return cursor.rowcount == 1


def finish_job(
    connection: sqlite3.Connection, job_id: str, *, state: str, owner: str, epoch: int, now: str,
    error: str | None = None,
) -> bool:
    cursor = connection.execute(
        "UPDATE learner_text_gap_jobs SET state = ?, last_error = ?, lease_owner = NULL, lease_expires_at = NULL, "
        "updated_at = ? WHERE id = ? AND lease_owner = ? AND lease_epoch = ?",
        (state, error, now, job_id, owner, epoch),
    )
    return cursor.rowcount == 1


def release_job(
    connection: sqlite3.Connection, job_id: str, *, owner: str, epoch: int, now: str, not_before: str | None,
    error: str | None,
) -> bool:
    cursor = connection.execute(
        "UPDATE learner_text_gap_jobs SET state = 'queued', lease_owner = NULL, lease_expires_at = NULL, "
        "not_before = ?, last_error = ?, updated_at = ? WHERE id = ? AND lease_owner = ? AND lease_epoch = ?",
        (not_before, error, now, job_id, owner, epoch),
    )
    return cursor.rowcount == 1


__all__ = [
    "GAP_COLUMNS",
    "check_advances",
    "commitments",
    "enqueue_job",
    "finish_job",
    "gap",
    "gap_for_source",
    "gap_tables_present",
    "gaps",
    "holds_job",
    "insert_check_advance",
    "insert_commitment",
    "insert_gap",
    "insert_reversal",
    "job",
    "job_for_source",
    "jobs",
    "lease_next_job",
    "release_job",
    "reversals",
    "save_job_payload",
]

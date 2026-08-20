"""Durable ingest queue persistence.

This module is the sole SQL owner for ``ingest_batches``, ``ingest_jobs``, and
``ingest_job_dependencies``.  :class:`learnloop.db.repositories.Repository`
inherits the mixin to preserve its public API while the queue remains a
self-contained persistence family.

The mixin expects its concrete repository to provide ``connection()``.  Keeping
that seam preserves Repository's pinned-connection behavior and the explicit
``BEGIN IMMEDIATE`` claim transaction verbatim.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Iterable, Mapping, Sequence

from learnloop.clock import Clock, utc_now_iso


def _json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _decode_ingest_batch(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["cancel_requested"] = bool(data.get("cancel_requested"))
    return data


def _decode_ingest_job(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["cancel_requested"] = bool(data.get("cancel_requested"))
    for key in ("payload", "result", "error", "usage"):
        raw = data.pop(f"{key}_json", None)
        data[key] = json.loads(raw) if raw else None
    return data


class IngestQueueStoreMixin:
    """Repository-compatible methods for the durable ingest queue family."""

    def connection(self) -> sqlite3.Connection:
        """Return a configured SQLite connection from the concrete repository."""

        raise NotImplementedError

    def insert_ingest_batch(
        self,
        *,
        id: str,
        workflow_type: str,
        subject_id: str | None = None,
        source_set_id: str | None = None,
        payload_schema_version: int = 1,
        status: str = "queued",
        priority: int = 0,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO ingest_batches(
                  id, workflow_type, payload_schema_version, subject_id,
                  source_set_id, status, priority, created_at, cancel_requested
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    id,
                    workflow_type,
                    payload_schema_version,
                    subject_id,
                    source_set_id,
                    status,
                    priority,
                    now,
                ),
            )
            connection.commit()

    def get_ingest_batch(self, batch_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM ingest_batches WHERE id = ?", (batch_id,)
            ).fetchone()
        return _decode_ingest_batch(row) if row is not None else None

    def list_ingest_batches(self, limit: int | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM ingest_batches ORDER BY created_at DESC, id DESC"
        params: tuple[Any, ...] = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (limit,)
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [_decode_ingest_batch(row) for row in rows]

    def update_ingest_batch_status(
        self,
        batch_id: str,
        status: str,
        *,
        mark_started: bool = False,
        mark_finished: bool = False,
        clear_finished: bool = False,
        clock: Clock | None = None,
    ) -> None:
        """Update status timestamps without retaining stale terminal state."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE ingest_batches
                   SET status = ?,
                       started_at = CASE WHEN ? AND started_at IS NULL THEN ? ELSE started_at END,
                       finished_at = CASE WHEN ? THEN ? WHEN ? THEN NULL ELSE finished_at END
                 WHERE id = ?
                """,
                (
                    status,
                    1 if mark_started else 0,
                    now,
                    1 if mark_finished else 0,
                    now,
                    1 if clear_finished else 0,
                    batch_id,
                ),
            )
            connection.commit()

    def request_ingest_batch_cancel(self, batch_id: str) -> None:
        """Flag the batch and every not-yet-terminal job for cancellation."""

        with self.connection() as connection:
            connection.execute(
                "UPDATE ingest_batches SET cancel_requested = 1 WHERE id = ?",
                (batch_id,),
            )
            connection.execute(
                """
                UPDATE ingest_jobs
                   SET cancel_requested = 1
                 WHERE batch_id = ?
                   AND status IN ('queued', 'running', 'waiting_for_input', 'blocked')
                """,
                (batch_id,),
            )
            connection.commit()

    def clear_ingest_batch_cancel_requested(self, batch_id: str) -> None:
        """Clear the batch cancellation latch before an explicit resume."""

        with self.connection() as connection:
            connection.execute(
                "UPDATE ingest_batches SET cancel_requested = 0 WHERE id = ?",
                (batch_id,),
            )
            connection.commit()

    def insert_ingest_job(
        self,
        *,
        id: str,
        batch_id: str,
        ordinal: int,
        job_type: str,
        payload: Mapping[str, Any] | None = None,
        payload_schema_version: int = 1,
        clock: Clock | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO ingest_jobs(
                  id, batch_id, ordinal, job_type, payload_schema_version,
                  payload_json, status, phase, message, attempt_count,
                  cancel_requested, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'queued', 'queued', 'Waiting to start', 0, 0, ?)
                """,
                (
                    id,
                    batch_id,
                    ordinal,
                    job_type,
                    payload_schema_version,
                    _json(dict(payload)) if payload is not None else None,
                    utc_now_iso(clock),
                ),
            )
            connection.commit()

    def add_ingest_job_dependency(self, job_id: str, depends_on_job_id: str) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO ingest_job_dependencies(job_id, depends_on_job_id)
                VALUES (?, ?)
                """,
                (job_id, depends_on_job_id),
            )
            connection.commit()

    def get_ingest_job(self, job_id: str) -> dict[str, Any] | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM ingest_jobs WHERE id = ?", (job_id,)
            ).fetchone()
        return _decode_ingest_job(row) if row is not None else None

    def ingest_jobs_for_batch(self, batch_id: str) -> list[dict[str, Any]]:
        return self.ingest_jobs_for_batches((batch_id,)).get(batch_id, [])

    def ingest_jobs_for_batches(
        self, batch_ids: Iterable[str]
    ) -> dict[str, list[dict[str, Any]]]:
        """Bulk-load ordered jobs, including requested empty batches."""

        ids = sorted({str(batch_id) for batch_id in batch_ids if batch_id})
        grouped: dict[str, list[dict[str, Any]]] = {batch_id: [] for batch_id in ids}
        if not ids:
            return grouped
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM ingest_jobs
                WHERE batch_id IN ({placeholders})
                ORDER BY batch_id, ordinal, id
                """,
                ids,
            ).fetchall()
        for row in rows:
            grouped[str(row["batch_id"])].append(_decode_ingest_job(row))
        return grouped

    def ingest_job_dependency_ids(self, job_id: str) -> list[str]:
        return self.ingest_job_dependencies_for_jobs((job_id,)).get(job_id, [])

    def ingest_job_dependencies_for_jobs(
        self, job_ids: Iterable[str]
    ) -> dict[str, list[str]]:
        """Bulk-load dependency ids for job progress views."""

        ids = sorted({str(job_id) for job_id in job_ids if job_id})
        grouped: dict[str, list[str]] = {job_id: [] for job_id in ids}
        if not ids:
            return grouped
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as connection:
            rows = connection.execute(
                f"""
                SELECT job_id, depends_on_job_id
                FROM ingest_job_dependencies
                WHERE job_id IN ({placeholders})
                ORDER BY job_id, depends_on_job_id
                """,
                ids,
            ).fetchall()
        for row in rows:
            grouped[str(row["job_id"])].append(str(row["depends_on_job_id"]))
        return grouped

    def ingest_job_dependents(self, job_id: str) -> list[str]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT job_id FROM ingest_job_dependencies
                WHERE depends_on_job_id = ? ORDER BY job_id
                """,
                (job_id,),
            ).fetchall()
        return [str(row["job_id"]) for row in rows]

    def claim_next_ingest_job(
        self,
        *,
        worker_id: str,
        now_iso: str,
        lease_cutoff_iso: str,
        eligible_job_types: Sequence[str] | None = None,
        compatible_running_job_types: Sequence[str] = (),
        allow_parallel: bool = False,
        max_parallel: int | None = None,
    ) -> dict[str, Any] | None:
        """Atomically claim the next eligible queued job for ``worker_id``.

        The default preserves the single-writer ingest lease. Callers may opt a
        read/DB-only job lane into bounded parallelism and identify job types
        that are safe to coexist with the single vault-writing lane. A
        ``running`` job whose heartbeat predates ``lease_cutoff_iso`` is treated
        as dead; startup recovery converts it to failed(interrupted).
        """

        eligible = tuple(
            dict.fromkeys(str(job_type) for job_type in (eligible_job_types or ()))
        )
        compatible = tuple(
            dict.fromkeys(str(job_type) for job_type in compatible_running_job_types)
        )
        connection = self.connection()
        connection.isolation_level = None
        try:
            connection.execute("BEGIN IMMEDIATE")
            if not allow_parallel:
                compatible_clause = ""
                live_params: list[Any] = [lease_cutoff_iso]
                if compatible:
                    placeholders = ",".join("?" for _ in compatible)
                    compatible_clause = f" AND job_type NOT IN ({placeholders})"
                    live_params.extend(compatible)
                live = connection.execute(
                    f"""
                    SELECT 1 FROM ingest_jobs
                     WHERE status = 'running'
                       AND heartbeat_at IS NOT NULL
                       AND heartbeat_at >= ?{compatible_clause}
                     LIMIT 1
                    """,
                    live_params,
                ).fetchone()
                if live is not None:
                    connection.execute("ROLLBACK")
                    return None
            if max_parallel is not None and eligible:
                placeholders = ",".join("?" for _ in eligible)
                live_count = connection.execute(
                    f"""
                    SELECT COUNT(*) AS count FROM ingest_jobs
                     WHERE status = 'running'
                       AND heartbeat_at IS NOT NULL
                       AND heartbeat_at >= ?
                       AND job_type IN ({placeholders})
                    """,
                    (lease_cutoff_iso, *eligible),
                ).fetchone()["count"]
                if int(live_count) >= max(1, int(max_parallel)):
                    connection.execute("ROLLBACK")
                    return None
            eligible_clause = ""
            candidate_params: list[Any] = []
            if eligible:
                placeholders = ",".join("?" for _ in eligible)
                eligible_clause = f" AND j.job_type IN ({placeholders})"
                candidate_params.extend(eligible)
            candidate = connection.execute(
                f"""
                SELECT j.* FROM ingest_jobs j
                 JOIN ingest_batches b ON b.id = j.batch_id
                 WHERE j.status = 'queued'
                   AND b.cancel_requested = 0
                   {eligible_clause}
                   AND NOT EXISTS (
                     SELECT 1 FROM ingest_job_dependencies d
                      JOIN ingest_jobs dep ON dep.id = d.depends_on_job_id
                      WHERE d.job_id = j.id AND dep.status != 'completed'
                   )
                 ORDER BY b.priority DESC, b.created_at, j.ordinal, j.id
                 LIMIT 1
                """,
                candidate_params,
            ).fetchone()
            if candidate is None:
                connection.execute("ROLLBACK")
                return None
            connection.execute(
                """
                UPDATE ingest_jobs
                   SET status = 'running',
                       worker_id = ?,
                       heartbeat_at = ?,
                       started_at = COALESCE(started_at, ?),
                       attempt_count = attempt_count + 1,
                       phase = COALESCE(phase, 'acquired'),
                       error_json = NULL
                 WHERE id = ? AND status = 'queued'
                """,
                (worker_id, now_iso, now_iso, candidate["id"]),
            )
            claimed = connection.execute(
                "SELECT * FROM ingest_jobs WHERE id = ?", (candidate["id"],)
            ).fetchone()
            connection.execute("COMMIT")
            return _decode_ingest_job(claimed) if claimed is not None else None
        finally:
            connection.close()

    def heartbeat_ingest_job(
        self,
        job_id: str,
        *,
        worker_id: str,
        phase: str | None = None,
        message: str | None = None,
        current_window: int | None = None,
        total_windows: int | None = None,
        clock: Clock | None = None,
    ) -> None:
        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE ingest_jobs
                   SET heartbeat_at = ?,
                       phase = COALESCE(?, phase),
                       message = COALESCE(?, message),
                       current_window = COALESCE(?, current_window),
                       total_windows = COALESCE(?, total_windows)
                 WHERE id = ? AND worker_id = ?
                """,
                (now, phase, message, current_window, total_windows, job_id, worker_id),
            )
            connection.commit()

    def finish_ingest_job(
        self,
        job_id: str,
        *,
        status: str,
        phase: str | None = None,
        message: str | None = None,
        result: Mapping[str, Any] | None = None,
        error: Mapping[str, Any] | None = None,
        usage: Mapping[str, Any] | None = None,
        release_lease: bool = True,
        clear_finished: bool = False,
        current_window: int | None = None,
        total_windows: int | None = None,
        clock: Clock | None = None,
    ) -> None:
        """Move a job to a new state and optionally release its lease."""

        now = utc_now_iso(clock)
        finished_at = None if clear_finished else now
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE ingest_jobs
                   SET status = ?,
                       phase = COALESCE(?, phase),
                       message = COALESCE(?, message),
                       result_json = COALESCE(?, result_json),
                       error_json = ?,
                       usage_json = COALESCE(?, usage_json),
                       current_window = COALESCE(?, current_window),
                       total_windows = COALESCE(?, total_windows),
                       worker_id = CASE WHEN ? THEN NULL ELSE worker_id END,
                       heartbeat_at = CASE WHEN ? THEN NULL ELSE heartbeat_at END,
                       finished_at = ?
                 WHERE id = ?
                """,
                (
                    status,
                    phase,
                    message,
                    _json(dict(result)) if result is not None else None,
                    _json(dict(error)) if error is not None else None,
                    _json(dict(usage)) if usage is not None else None,
                    current_window,
                    total_windows,
                    1 if release_lease else 0,
                    1 if release_lease else 0,
                    finished_at,
                    job_id,
                ),
            )
            connection.commit()

    def requeue_ingest_job(
        self,
        job_id: str,
        *,
        message: str = "Waiting to start",
        clock: Clock | None = None,
    ) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                UPDATE ingest_jobs
                   SET status = 'queued', phase = 'queued', message = ?,
                       worker_id = NULL, heartbeat_at = NULL,
                       error_json = NULL, finished_at = NULL,
                       cancel_requested = 0
                 WHERE id = ?
                """,
                (message, job_id),
            )
            connection.commit()

    def delete_finished_ingest_batches(
        self, batch_ids: Sequence[str]
    ) -> dict[str, int]:
        """Delete finished queue history without touching source artifacts."""

        ids = list(dict.fromkeys(str(batch_id) for batch_id in batch_ids if batch_id))
        if not ids:
            return {"batches": 0, "jobs": 0, "dependencies": 0}
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as connection:
            active = connection.execute(
                f"""
                SELECT id FROM ingest_batches
                 WHERE id IN ({placeholders})
                   AND status IN ('queued','running','waiting_for_input')
                """,
                ids,
            ).fetchall()
            if active:
                raise ValueError("active ingest batches cannot be deleted")
            job_rows = connection.execute(
                f"SELECT id FROM ingest_jobs WHERE batch_id IN ({placeholders})", ids
            ).fetchall()
            job_ids = [row["id"] for row in job_rows]
            dependencies = 0
            if job_ids:
                job_placeholders = ",".join("?" for _ in job_ids)
                cursor = connection.execute(
                    f"""
                    DELETE FROM ingest_job_dependencies
                     WHERE job_id IN ({job_placeholders})
                        OR depends_on_job_id IN ({job_placeholders})
                    """,
                    [*job_ids, *job_ids],
                )
                dependencies = cursor.rowcount
                connection.execute(
                    f"DELETE FROM ingest_jobs WHERE id IN ({job_placeholders})",
                    job_ids,
                )
            cursor = connection.execute(
                f"DELETE FROM ingest_batches WHERE id IN ({placeholders})", ids
            )
            batches = cursor.rowcount
            connection.commit()
        return {
            "batches": batches,
            "jobs": len(job_ids),
            "dependencies": dependencies,
        }

    def update_ingest_job_payload(
        self, job_id: str, payload: Mapping[str, Any]
    ) -> None:
        """Replace a durable job payload before an explicit retry."""

        with self.connection() as connection:
            connection.execute(
                "UPDATE ingest_jobs SET payload_json = ? WHERE id = ?",
                (_json(dict(payload)), job_id),
            )
            connection.commit()

    def set_ingest_job_cancel_requested(self, job_id: str) -> None:
        with self.connection() as connection:
            connection.execute(
                "UPDATE ingest_jobs SET cancel_requested = 1 WHERE id = ?", (job_id,)
            )
            connection.commit()

    def ingest_jobs_by_types(
        self, job_types: Sequence[str], *, limit: int | None = None
    ) -> list[dict[str, Any]]:
        placeholders = ",".join("?" for _ in job_types)
        query = (
            f"SELECT * FROM ingest_jobs WHERE job_type IN ({placeholders}) "
            "ORDER BY created_at DESC, id DESC"
        )
        params: list[Any] = list(job_types)
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        with self.connection() as connection:
            rows = connection.execute(query, params).fetchall()
        return [_decode_ingest_job(row) for row in rows]

    def active_ingest_jobs(self) -> list[dict[str, Any]]:
        """Return every job that has not reached a terminal state."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM ingest_jobs
                 WHERE status IN ('queued', 'running', 'waiting_for_input')
                 ORDER BY created_at, id
                """
            ).fetchall()
        return [_decode_ingest_job(row) for row in rows]

    def expired_running_ingest_jobs(
        self, lease_cutoff_iso: str
    ) -> list[dict[str, Any]]:
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM ingest_jobs
                 WHERE status = 'running'
                   AND (heartbeat_at IS NULL OR heartbeat_at < ?)
                 ORDER BY ordinal, id
                """,
                (lease_cutoff_iso,),
            ).fetchall()
        return [_decode_ingest_job(row) for row in rows]

    def rung_variant_batch_dead(self, batch_id: str | None) -> bool:
        """Whether a rung-variant batch is absent or wholly terminal."""

        return self._ingest_batch_dead(batch_id, job_type="rung_variant")

    def concept_animation_batch_dead(self, batch_id: str | None) -> bool:
        """Whether a concept-animation batch is absent or wholly terminal."""

        return self._ingest_batch_dead(batch_id, job_type="concept_animation")

    def _ingest_batch_dead(self, batch_id: str | None, *, job_type: str) -> bool:
        if not batch_id:
            return True
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT status FROM ingest_jobs WHERE batch_id = ? AND job_type = ?",
                (batch_id, job_type),
            ).fetchall()
        if not rows:
            return True
        return all(
            row["status"] in ("failed", "cancelled", "completed") for row in rows
        )

    def rung_variant_pending_source_ids(self) -> set[str]:
        """Source item ids held by live durable rung-variant work."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT r.source_practice_item_id
                FROM rung_variant_requests r
                WHERE r.status IN ('pending', 'generating')
                  AND EXISTS (
                    SELECT 1 FROM ingest_jobs j
                    WHERE j.batch_id = r.batch_id AND j.job_type = 'rung_variant'
                      AND j.status NOT IN ('failed', 'cancelled', 'completed')
                  )
                """
            ).fetchall()
        return {str(row["source_practice_item_id"]) for row in rows}

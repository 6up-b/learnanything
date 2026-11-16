"""The Reader's newest position to keep one chapter ahead, with revisioned retries.

Owns reading-request fields in ``source_auto_build_state``; joins
``source_extraction_runs`` and ``source_revisions`` to find an extraction's book.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from learnloop.clock import Clock, utc_now_iso


def _reading_request(row: sqlite3.Row) -> dict[str, Any]:
    """A book's pending reading request (``source_auto_build_state``, migration 199)."""

    return {
        "source_id": row["source_id"],
        "extraction_id": row["wanted_extraction_id"],
        "section_id": row["wanted_section_id"],
        "wanted_at": row["wanted_at"],
        "revision": int(row["wanted_revision"]),
        "attempts": int(row["wanted_attempts"]),
        "retry_at": row["wanted_retry_at"],
    }


class ReadingRequestStoreMixin:
    # The book's reading request (UX Phase 1 finishing pass, Codex F8/F9;
    # migration 199): the Reader's newest position for "keep one chapter
    # ahead", the one state that path keeps. Recording a request advances its
    # revision; whoever acts on it settles or fails exactly that revision, so a
    # newer request recorded meanwhile survives.

    _READING_REQUEST_UPSERT = """
        ON CONFLICT(source_id) DO UPDATE SET
          wanted_extraction_id = excluded.wanted_extraction_id,
          wanted_section_id = excluded.wanted_section_id,
          wanted_at = excluded.wanted_at,
          wanted_revision = source_auto_build_state.wanted_revision + 1,
          wanted_attempts = 0,
          wanted_retry_at = excluded.wanted_retry_at,
          updated_at = excluded.updated_at
    """

    def record_reading_request(
        self, source_id: str, extraction_id: str, section_id: str, *, clock: Clock | None = None
    ) -> int:
        """Record the Reader's newest position as the book's reading request
        (it replaces a pending one: a new revision, no failed attempts, due at
        once). Returns the request's revision."""

        now = utc_now_iso(clock)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO source_auto_build_state(
                  source_id, generation, wanted_extraction_id, wanted_section_id, wanted_at,
                  wanted_revision, wanted_attempts, wanted_retry_at, updated_at
                )
                VALUES (?, 0, ?, ?, ?, 1, 0, ?, ?)
                """
                + self._READING_REQUEST_UPSERT,
                (source_id, extraction_id, section_id, now, now, now),
            )
            row = connection.execute(
                "SELECT wanted_revision FROM source_auto_build_state WHERE source_id = ?", (source_id,)
            ).fetchone()
            connection.commit()
        return int(row["wanted_revision"])

    # The name the earlier rounds used (tests seed a waiting position with it).
    set_source_wanted_reading = record_reading_request

    @classmethod
    def _record_reading_request_for_extraction(
        cls, connection: sqlite3.Connection, extraction_id: str, section_id: str, now: str
    ) -> None:
        """The same request, recorded inside the caller's transaction for the
        source an extraction belongs to (nothing when it has none)."""

        connection.execute(
            """
            INSERT INTO source_auto_build_state(
              source_id, generation, wanted_extraction_id, wanted_section_id, wanted_at,
              wanted_revision, wanted_attempts, wanted_retry_at, updated_at
            )
            SELECT revision.source_id, 0, ?, ?, ?, 1, 0, ?, ?
            FROM source_extraction_runs AS run
            JOIN source_revisions AS revision ON revision.id = run.revision_id
            WHERE run.id = ?
            """
            + cls._READING_REQUEST_UPSERT,
            (extraction_id, section_id, now, now, now, extraction_id),
        )

    def pending_reading_request(self, source_id: str) -> dict[str, Any] | None:
        """The book's reading request still to act on, or ``None``."""

        with self.connection() as connection:
            row = connection.execute(
                "SELECT * FROM source_auto_build_state WHERE source_id = ? AND wanted_section_id IS NOT NULL",
                (source_id,),
            ).fetchone()
        return _reading_request(row) if row is not None else None

    def settle_reading_request(self, source_id: str, revision: int, *, clock: Clock | None = None) -> bool:
        """The request at ``revision`` was acted on (a build queued, or nothing
        to do): forget it, unless a newer one replaced it. Returns whether it
        was settled."""

        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE source_auto_build_state
                SET wanted_extraction_id = NULL, wanted_section_id = NULL, wanted_at = NULL,
                    wanted_attempts = 0, wanted_retry_at = NULL, updated_at = ?
                WHERE source_id = ? AND wanted_revision = ? AND wanted_section_id IS NOT NULL
                """,
                (utc_now_iso(clock), source_id, int(revision)),
            )
            connection.commit()
        return cursor.rowcount > 0

    def fail_reading_request(
        self, source_id: str, revision: int, *, attempts: int, retry_at: str | None, clock: Clock | None = None
    ) -> bool:
        """Acting on the request at ``revision`` failed: count it and set when
        the reading sweep acts on it next (``None``: due at once). A newer
        request is left alone. Returns whether it was marked."""

        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE source_auto_build_state
                SET wanted_attempts = ?, wanted_retry_at = ?, updated_at = ?
                WHERE source_id = ? AND wanted_revision = ? AND wanted_section_id IS NOT NULL
                """,
                (int(attempts), retry_at, utc_now_iso(clock), source_id, int(revision)),
            )
            connection.commit()
        return cursor.rowcount > 0

    def defer_reading_request(self, source_id: str, revision: int, *, retry_at: str,
                              clock: Clock | None = None) -> bool:
        """The request at ``revision`` waits behind its book's own work: not a
        failure, so its failed attempts are forgotten (the Reader stops asking
        again) and it is due from ``retry_at``, for the reading sweep to act on
        once that work ends. A newer request is left alone."""

        with self.connection() as connection:
            cursor = connection.execute(
                """
                UPDATE source_auto_build_state
                SET wanted_attempts = 0, wanted_retry_at = ?, updated_at = ?
                WHERE source_id = ? AND wanted_revision = ? AND wanted_section_id IS NOT NULL
                """,
                (retry_at, utc_now_iso(clock), source_id, int(revision)),
            )
            connection.commit()
        return cursor.rowcount > 0

    def pending_reading_requests(self) -> list[dict[str, Any]]:
        """Every book's pending reading request, due first (reading-hardening,
        part 1): the reading sweep's one query per pass. A request with no
        retry time is due now (one whose worker retries ran out before the
        sweep existed), so every pending request is due now or at its retry
        time."""

        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM source_auto_build_state
                WHERE wanted_section_id IS NOT NULL
                ORDER BY wanted_retry_at IS NOT NULL, wanted_retry_at, source_id
                """
            ).fetchall()
        return [_reading_request(row) for row in rows]

    def due_reading_requests(self, now: str) -> list[dict[str, Any]]:
        """The pending requests due at ``now`` (ISO UTC): a retry time passed,
        or none."""

        return [
            request for request in self.pending_reading_requests()
            if request["retry_at"] is None or request["retry_at"] <= now
        ]

    def reading_request_unsettled(self, extraction_id: str) -> bool:
        """Whether the book this extraction belongs to has a request whose
        last attempt failed: the Reader's next report asks again (F8)."""

        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM source_extraction_runs AS run
                JOIN source_revisions AS revision ON revision.id = run.revision_id
                JOIN source_auto_build_state AS state ON state.source_id = revision.source_id
                WHERE run.id = ? AND state.wanted_section_id IS NOT NULL AND state.wanted_attempts > 0
                LIMIT 1
                """,
                (extraction_id,),
            ).fetchone()
        return row is not None

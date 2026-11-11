"""What other test files use from ``tests/test_te3b_value.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta



def _lesson_db(tmp_path):
    import sqlite3

    connection = sqlite3.connect(str(tmp_path / "lessons.sqlite"))
    connection.executescript(
        "CREATE TABLE lessons (id TEXT PRIMARY KEY, opened_at TEXT, closed_at TEXT);"
        # Migration 247's columns (the receipt's occurred_at, received_at and version included: Codex review F4).
        "CREATE TABLE lesson_activity_intervals (id TEXT PRIMARY KEY, lesson_id TEXT NOT NULL, "
        "screen_session TEXT NOT NULL, seq INTEGER NOT NULL, started_at TEXT NOT NULL, ended_at TEXT NOT NULL, "
        "seconds REAL NOT NULL, foreground INTEGER NOT NULL, occurred_at TEXT NOT NULL, received_at TEXT NOT NULL, "
        "receipt_version TEXT NOT NULL);"
        "CREATE TABLE practice_attempts (id TEXT, created_at TEXT, latency_seconds REAL);"
        "CREATE TABLE interaction_events (kind TEXT, occurred_at TEXT, created_at TEXT, payload_json TEXT);")
    return connection


def _stamp(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


T0 = datetime(2026, 11, 6, 9, 0, tzinfo=UTC)


def _lesson(connection, lesson_id: str, start: datetime, active_minutes: list[tuple[float, float]], *,
            closed: bool = True, received: datetime | None = None) -> None:
    """A lesson with foreground intervals ``(offset, length)`` in minutes from ``start``, each received when it ended
    (or at ``received``: a late upload)."""

    end = start + timedelta(minutes=max(o + n for o, n in active_minutes) + 1)
    connection.execute("INSERT INTO lessons VALUES (?, ?, ?)", (lesson_id, _stamp(start),
                                                                _stamp(end) if closed else None))
    for seq, (offset, length) in enumerate(active_minutes, start=1):
        began = start + timedelta(minutes=offset)
        ended = began + timedelta(minutes=length)
        connection.execute(
            "INSERT INTO lesson_activity_intervals (id, lesson_id, screen_session, seq, started_at, ended_at, seconds, "
            "foreground, occurred_at, received_at, receipt_version) VALUES (?, ?, 's', ?, ?, ?, ?, 1, ?, ?, 'v1')",
            (f"{lesson_id}:{seq}", lesson_id, seq, _stamp(began), _stamp(ended), length * 60.0, _stamp(ended),
             _stamp(received if received is not None else ended)))

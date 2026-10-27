"""Mobile PR-4: migration 225 (spec_mobile_tailnet_v1 §6.5, §8).

``sessions`` gains ``owner_device_id`` (NULL is the desktop) and
``owner_generation`` (0); every existing row keeps its values and reads as a
desktop session that was never handed off. ``session_handoffs`` is new
(RECEIPT, append-only by trigger). No DERIVED table, so no replayer.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.migrate import discover_migrations
from learnloop.db.table_roles import TableRole, role_for_table

MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"
HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_225" / "state.sqlite"
#: Every schema object 225 adds, and the table it alters: the earlier
#: migrations' "nothing else changed" diffs on the way to head read these.
PR4_ADDED_OBJECTS = frozenset({
    "session_handoffs", "sqlite_autoindex_session_handoffs_1", "idx_session_handoffs_session",
    "session_handoffs_no_update", "session_handoffs_no_delete",
})
PR4_ALTERED_TABLES = frozenset({"sessions"})

_SESSIONS_BEFORE = """
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  energy TEXT,
  sleep_quality REAL CHECK (sleep_quality IS NULL OR (sleep_quality >= 0.0 AND sleep_quality <= 1.0)),
  available_minutes INTEGER CHECK (available_minutes IS NULL OR available_minutes >= 0),
  notes_md_path TEXT,
  updated_at TEXT
);
"""


def test_225_is_the_session_ownership_migration_and_the_handoffs_are_receipts():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[225] == "225_session_ownership.sql"
    assert role_for_table("session_handoffs") == TableRole.RECEIPT
    assert role_for_table("sessions") == TableRole.WORKFLOW


def test_existing_sessions_keep_their_rows_and_read_as_desktop_sessions(tmp_path):
    with closing(sqlite3.connect(tmp_path / "state.sqlite")) as connection:
        connection.executescript(_SESSIONS_BEFORE)
        rows = [
            ("s1", "2026-10-01T10:00:00Z", "2026-10-01T10:30:00Z", None, None, 25, None, "2026-10-01T10:30:00Z"),
            ("s2", "2026-10-02T10:00:00Z", None, "high", 0.5, None, "notes/x.md", None),
        ]
        connection.executemany("INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rows)
        connection.commit()
        connection.executescript((MIGRATIONS / "225_session_ownership.sql").read_text(encoding="utf-8"))
        after = connection.execute("SELECT * FROM sessions ORDER BY id").fetchall()
        assert [row[:8] for row in after] == rows
        assert {row[8:] for row in after} == {(None, 0)}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_the_handoff_receipt_is_append_only_and_checked(tmp_path):
    with closing(sqlite3.connect(tmp_path / "state.sqlite")) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(_SESSIONS_BEFORE)
        connection.executescript((MIGRATIONS / "225_session_ownership.sql").read_text(encoding="utf-8"))
        connection.execute("INSERT INTO sessions (id, started_at) VALUES ('s1', '2026-10-27T00:00:00Z')")
        insert = ("INSERT INTO session_handoffs (id, session_id, kind, from_device_id, to_device_id, generation, "
                  "checkpoint_json, at) VALUES (?, ?, ?, NULL, 'dev_phone', ?, NULL, '2026-10-27T00:00:01Z')")
        connection.execute(insert, ("h1", "s1", "adopt", 1))
        for bad in (("h2", "s1", "steal", 1), ("h3", "s1", "adopt", -1), ("h4", "no-session", "adopt", 1)):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(insert, bad)
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("UPDATE session_handoffs SET generation = 2")
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM session_handoffs")


def test_the_head_fixture_holds_exactly_225s_objects_in_rollback_mode():
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
        assert PR4_ADDED_OBJECTS <= names
        columns = [row[1] for row in connection.execute("PRAGMA table_info(sessions)")]
        assert columns[-2:] == ["owner_device_id", "owner_generation"]
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 225
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        assert connection.execute("SELECT COUNT(*) FROM session_handoffs").fetchone()[0] == 0

"""Schema facts the code states as constants (refactor step F1).

A reader that used to ask the database whether a column exists now names it. What stays a stated fact (which of the
history card's tables carry ``received_at``) is pinned to the migrated schema here, so a migration that changes it
fails this test instead of silently changing a read.
"""

from __future__ import annotations

from contextlib import closing
from typing import Any

from learnloop.adaptive_difficulty import history_card
from learnloop.db.connection import connect

from tests.helpers import create_basic_vault

_READ_BY_THE_CARD = ("practice_attempts", "interaction_events", "question_events", "reader_session_digests",
                     "learner_text_gaps", "reader_authored_questions", "source_exposure_events")


def test_the_history_cards_received_at_tables_are_the_migrated_schemas(tmp_path):
    paths = create_basic_vault(tmp_path)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        carrying = {
            table for table in _READ_BY_THE_CARD
            if any(column[1] == "received_at" for column in connection.execute(f'PRAGMA table_info("{table}")'))
        }
    assert carrying == set(history_card._RECEIVED_AT_TABLES)
    for table in _READ_BY_THE_CARD:
        expected = "COALESCE(received_at, created_at)" if table in carrying else "created_at"
        assert history_card.available_sql(table) == expected


def test_a_prefetch_job_asks_the_schema_nothing_and_opens_few_connections(tmp_path, monkeypatch):
    """A column check (``PRAGMA table_info(t)``) marks the pooled connection, which then closes at release
    instead of serving the next reader (``db.connection._PooledSqlite``). Across a journey's prefetch jobs no
    checkout runs one, and a job opens a handful of connections (it opened about 15 with the checks)."""

    import sqlite3
    import weakref

    from learnloop.db import connection as DBC

    from tests.rospeed_join_helpers import _journey

    asked: list[tuple[Any, Any]] = []
    opened: list[int] = []
    real_close = DBC._ConnectionPool.close

    def close(self):
        if not self.closed:
            opened.append(self.opened)
        return real_close(self)

    def wrapped(self, inner):
        reference = weakref.ref(self)

        def authorizer(action, arg1, arg2, database, trigger):
            connection = reference()
            if connection is not None and connection._watching and action == sqlite3.SQLITE_PRAGMA \
                    and str(arg1).lower() in {"table_info", "table_xinfo"}:
                asked.append((arg1, arg2))
            return sqlite3.SQLITE_OK if inner is None else inner(action, arg1, arg2, database, trigger)

        return authorizer

    monkeypatch.setattr(DBC._ConnectionPool, "close", close)
    monkeypatch.setattr(DBC._PooledSqlite, "_wrapped", wrapped)
    _journey(tmp_path, steps=6)
    assert opened, "the journey ran no pooled job"
    assert asked == []
    assert max(opened) <= 10, opened

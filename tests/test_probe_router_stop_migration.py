"""The probe router's continuation: a router-owned episode the router decides not to continue completes with its own
reason. ``probe_episodes.completion_reason`` gains ``router_stop`` (migration ``probe_episode_router_stop``); the table
is rebuilt with every row and its indexes kept, and nothing else changes."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.diagnosis.probe_completion import ROUTER_STOP
from tests.helpers import MIGRATION_HEAD_FIXTURE

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
MIGRATION = next(m for m in discover_migrations() if m.name == "probe_episode_router_stop")
_REASONS = "'value_of_information_stop'"
_INDEXES = (
    "CREATE INDEX idx_probe_episodes_lo ON probe_episodes(learning_object_id, created_at)",
    "CREATE UNIQUE INDEX idx_probe_episodes_open\n  ON probe_episodes(learning_object_id)\n"
    "  WHERE status IN ('pending_items', 'in_progress')",
    "CREATE INDEX idx_probe_episodes_target_version\n  ON probe_episodes(target_contract_version_id)",
)


def _sql(connection: sqlite3.Connection) -> dict[str, str]:
    return {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}


def test_the_head_fixture_holds_it_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert MIGRATION.version in applied_versions(HEAD)
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert f"'{ROUTER_STOP}'" in _sql(connection)["probe_episodes"]


def _downgraded(database: Path) -> None:
    """A head copy with probe_episodes as 200 made it (the CHECK without 'router_stop'), its indexes kept, and two
    episodes in it, one of them complete, with a presentation naming it."""

    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        sql = _sql(connection)["probe_episodes"]
        old = sql.replace(f"{_REASONS},\n      'router_stop'", _REASONS)
        assert old != sql
        connection.execute(old.replace('CREATE TABLE "probe_episodes"', "CREATE TABLE probe_episodes__undo", 1))
        connection.execute("INSERT INTO probe_episodes__undo SELECT * FROM probe_episodes")
        connection.execute("DROP TABLE probe_episodes")
        connection.execute("ALTER TABLE probe_episodes__undo RENAME TO probe_episodes")
        for index in _INDEXES:
            connection.execute(index)
        connection.execute("DELETE FROM schema_migrations WHERE version = ?", (MIGRATION.version,))
        for episode_id, status, reason in (("ep1", "complete", "value_of_information_stop"),
                                           ("ep2", "in_progress", None)):
            connection.execute(
                "INSERT INTO probe_episodes(id, learning_object_id, status, trigger, completion_reason, "
                "algorithm_version, created_at, updated_at) VALUES (?, ?, ?, 'misconception', ?, 'v', 't', 't')",
                (episode_id, f"lo_{episode_id}", status, reason))
        connection.commit()


def test_it_rebuilds_probe_episodes_alone_and_keeps_every_row(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        before = _sql(connection)
        kept = sorted(tuple(row) for row in connection.execute("SELECT * FROM probe_episodes"))
        with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
            connection.execute("UPDATE probe_episodes SET status = 'complete', completion_reason = ? WHERE id = 'ep2'",
                               (ROUTER_STOP,))
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(database)] == [MIGRATION.version]
    with closing(sqlite3.connect(database)) as connection:
        after = _sql(connection)
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert sorted(tuple(row) for row in connection.execute("SELECT * FROM probe_episodes")) == kept
        connection.execute("UPDATE probe_episodes SET status = 'complete', completion_reason = ? WHERE id = 'ep2'",
                           (ROUTER_STOP,))
        # The open-episode index is still the table's: a second open episode on one learning object is refused.
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO probe_episodes(id, learning_object_id, status, trigger, algorithm_version, "
                               "created_at, updated_at) VALUES ('ep3', 'lo_x', 'in_progress', 'manual', 'v', 't', 't'),"
                               " ('ep4', 'lo_x', 'pending_items', 'manual', 'v', 't', 't')")
    assert set(after) == set(before)
    assert {name for name in before if before[name] != after[name]} == {"probe_episodes"}
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as head:
        assert after == _sql(head)

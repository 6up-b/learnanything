"""Teacher TE2-log, migration 247: ``lesson_episodes`` and ``lesson_activity_intervals``
(spec_teacher_v1 §11.6, §11.9, §18.1).

Two RECEIPT tables, empty at the head; nothing else changes. An episode row is
inserted at its opening and its closing fields are set once; an interval is
append-only and written once per (lesson, screen session, seq).
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.adaptive_difficulty.protected_tables import DENIED, ROLES
from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES, TableRole

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_247" / "state.sqlite"
EPISODES = "lesson_episodes"
INTERVALS = "lesson_activity_intervals"
#: What 247 adds: earlier migrations' "nothing else changed" diffs on the way to head read this.
TE2LOG_ADDED_OBJECTS = frozenset({
    EPISODES, "idx_lesson_episodes_lesson", "idx_lesson_episodes_lo", f"{EPISODES}_close_once",
    f"{EPISODES}_no_delete", f"sqlite_autoindex_{EPISODES}_1", f"sqlite_autoindex_{EPISODES}_2",
    INTERVALS, "idx_lesson_activity_intervals_lesson", f"{INTERVALS}_no_update", f"{INTERVALS}_no_delete",
    f"sqlite_autoindex_{INTERVALS}_1", f"sqlite_autoindex_{INTERVALS}_2",
})
_LESSON = ("INSERT INTO lessons(id, driver, origin, entry, goal_text, goal_json, learning_object_ids_json, "
           "doctrine_version, brief_version, algorithm_version, opened_at) VALUES ('les_1', 'desktop', 'learner_pick', "
           "'learning_object', 'g', '{}', '[]', 'd', 'b', 'mvp-0.49', '2026-11-05T10:00:00Z')")
_EPISODE = ("INSERT INTO lesson_episodes(id, lesson_id, kind, opened_by, node_id, opened_at, repair_class, origin, "
            "episode_version, created_at) VALUES (?, 'les_1', ?, ?, 'n1', '2026-11-05T10:01:00Z', ?, 'learner_pick', "
            "'v', '2026-11-05T10:01:00Z')")
_INTERVAL = ("INSERT INTO lesson_activity_intervals(id, lesson_id, screen_session, seq, started_at, ended_at, seconds, "
             "foreground, occurred_at, received_at, receipt_version) VALUES (?, 'les_1', 's', ?, "
             "'2026-11-05T10:00:00Z', '2026-11-05T10:01:00Z', 60, 1, 't', 't', 'v')")


def test_247_is_the_head_and_its_tables_receipts_denied_to_ad():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[247] == "247_lesson_episodes.sql" and max(names) == 247
    assert TABLE_ROLES[EPISODES] is TableRole.RECEIPT
    assert TABLE_ROLES[INTERVALS] is TableRole.RECEIPT
    assert ROLES[EPISODES] == DENIED and ROLES[INTERVALS] == DENIED


def test_the_head_fixture_holds_247_in_rollback_mode_with_empty_tables():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert max(applied_versions(HEAD)) == 247
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
        assert TE2LOG_ADDED_OBJECTS <= names
        assert connection.execute(f"SELECT COUNT(*) FROM {EPISODES}").fetchone()[0] == 0
        assert connection.execute(f"SELECT COUNT(*) FROM {INTERVALS}").fetchone()[0] == 0


def _downgraded(database: Path) -> None:
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(f"DROP TABLE {EPISODES}")
        connection.execute(f"DROP TABLE {INTERVALS}")
        connection.execute("DELETE FROM schema_migrations WHERE version = 247")
        connection.commit()


def test_247_adds_exactly_its_objects(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == [247]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert set(after) - set(before) == TE2LOG_ADDED_OBJECTS
        assert {name for name in before if after.get(name) != before[name]} == set()


def _head_copy(tmp_path: Path) -> sqlite3.Connection:
    database = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(_LESSON)
    return connection


def test_an_episode_closes_once_and_nothing_else_moves(tmp_path):
    with closing(_head_copy(tmp_path)) as connection:
        connection.execute(_EPISODE, ("e1", "detour", "lt_1", "reteach"))
        with pytest.raises(sqlite3.IntegrityError):  # an opening field never moves
            connection.execute("UPDATE lesson_episodes SET repair_class = 'insert_foundation' WHERE id = 'e1'")
        with pytest.raises(sqlite3.IntegrityError):  # closing fields only together with closed_at
            connection.execute("UPDATE lesson_episodes SET active_seconds = 3 WHERE id = 'e1'")
        connection.execute("UPDATE lesson_episodes SET closed_at = 't2', close_reason = 'rechecked', "
                           "active_seconds = 30, elapsed_seconds = 60 WHERE id = 'e1'")
        with pytest.raises(sqlite3.IntegrityError):  # closed once
            connection.execute("UPDATE lesson_episodes SET active_seconds = 31 WHERE id = 'e1'")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("DELETE FROM lesson_episodes")
        with pytest.raises(sqlite3.IntegrityError):  # one episode per opening action
            connection.execute(_EPISODE, ("e2", "detour", "lt_1", "reteach"))


@pytest.mark.parametrize(("kind", "repair", "ok"), [
    ("detour", "repair_in_place", True), ("detour", "unlogged", True), ("detour", None, False),
    ("detour", "prerequisite", False), ("gap", "misconception", True), ("gap", None, True),
    ("gap", "reteach", False), ("probe", None, True), ("probe", "reteach", False), ("goal_lo", None, True),
    ("goal_lo", "prerequisite", False), ("calibration", None, False),
])
def test_the_repair_class_matches_the_kind(tmp_path, kind, repair, ok):
    with closing(_head_copy(tmp_path)) as connection:
        if ok:
            connection.execute(_EPISODE, ("e1", kind, "lt_1", repair))
        else:
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(_EPISODE, ("e1", kind, "lt_1", repair))


def test_intervals_are_append_only_and_written_once_per_seq(tmp_path):
    with closing(_head_copy(tmp_path)) as connection:
        connection.execute(_INTERVAL, ("i1", 1))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(_INTERVAL, ("i2", 1))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE lesson_activity_intervals SET seconds = 1")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("DELETE FROM lesson_activity_intervals")
        with pytest.raises(sqlite3.IntegrityError):  # an interval ending before it starts
            connection.execute(
                "INSERT INTO lesson_activity_intervals(id, lesson_id, screen_session, seq, started_at, ended_at, "
                "seconds, foreground, occurred_at, received_at, receipt_version) VALUES ('i3', 'les_1', 's', 2, "
                "'2026-11-05T10:01:00Z', '2026-11-05T10:00:00Z', 0, 1, 't', 't', 'v')")
        with pytest.raises(sqlite3.IntegrityError):  # its lesson must exist
            connection.execute(
                "INSERT INTO lesson_activity_intervals(id, lesson_id, screen_session, seq, started_at, ended_at, "
                "seconds, foreground, occurred_at, received_at, receipt_version) VALUES ('i4', 'les_x', 's', 1, "
                "'a', 'b', 0, 1, 't', 't', 'v')")


@pytest.mark.durability
def test_247_on_the_durability_lane(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == [247]
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        connection.execute(_LESSON)
        connection.execute(_EPISODE, ("e1", "detour", "lt_1", "reteach"))
        connection.commit()
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"

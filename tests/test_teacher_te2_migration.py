"""Teacher TE2, migration 248 (spec_teacher_v1 rev 5 §11.3, §11.7, §11.9, §18.2, §24 row TE2).

Four CHECK rebuilds (every row and id kept), and ``lesson_episodes.refusal_reason`` with its close-once trigger
recreated so a probe's generated item id may be set once with the close. No new table.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.table_roles import TABLE_ROLES, TableRole

HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_248" / "state.sqlite"
PREVIOUS = Path(__file__).resolve().parents[1] / "migrations" / "247_lesson_episodes.sql"
REBUILT = ("followup_generation_jobs", "generated_probe_items", "learner_text_gaps", "learner_text_gap_jobs")
#: What 248 alters (earlier migrations' "nothing else changed" diffs on the way to head read this): the four rebuilt
#: tables, lesson_episodes (its new column) and its close-once trigger. It adds no object.
TE2_ALTERED_TABLES = frozenset({*REBUILT, "lesson_episodes", "lesson_episodes_close_once"})
_LESSON = ("INSERT INTO lessons(id, driver, origin, entry, goal_text, goal_json, learning_object_ids_json, "
           "doctrine_version, brief_version, algorithm_version, opened_at) VALUES ('les_1', 'desktop', 'learner_pick', "
           "'learning_object', 'g', '{}', '[]', 'd', 'b', 'mvp-0.50', '2026-11-06T10:00:00Z')")
_PROBE = ("INSERT INTO lesson_episodes(id, lesson_id, kind, opened_by, node_id, opened_at, origin, generation_job_id, "
          "episode_version, created_at) VALUES ('e1', 'les_1', 'probe', 'lt_1', 'n1', '2026-11-06T10:01:00Z', "
          "'learner_pick', 'job_1', 'v', '2026-11-06T10:01:00Z')")


def test_248_is_the_head_and_adds_no_table():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[248] == "248_teacher_te2_sources.sql" and max(names) == 248
    for table in REBUILT:
        assert table in TABLE_ROLES
    assert TABLE_ROLES["lesson_episodes"] is TableRole.RECEIPT


def test_the_head_fixture_holds_248_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert max(applied_versions(HEAD)) == 248
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        sql = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert "'lesson')" in sql["followup_generation_jobs"]
        assert "'manual', 'lesson')" in sql["generated_probe_items"]
        assert "'lesson', 'external_chat'" in sql["learner_text_gaps"]
        assert "'lesson', 'external_chat'" in sql["learner_text_gap_jobs"]
        assert "refusal_reason" in sql["lesson_episodes"]


def _downgraded(database: Path) -> None:
    """The head with 248 undone (each rebuilt table back to its 247 CHECK, the column dropped, the trigger as 247
    wrote it): what 248 then applies to."""

    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        rows = {name: sql for name, sql in connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'table' AND name IN (?, ?, ?, ?)", REBUILT)}
        for table, sql in rows.items():
            old = (sql.replace(", 'lesson')", ")").replace(",\n    'lesson', 'external_chat'", "")
                   .replace(f'"{table}"', table))
            assert old != sql
            dependents = [row[0] for row in connection.execute(
                "SELECT sql FROM sqlite_master WHERE tbl_name = ? AND type IN ('index', 'trigger') AND sql IS NOT NULL",
                (table,))]
            connection.execute(f"ALTER TABLE {table} RENAME TO {table}__old")
            connection.execute(old)
            connection.execute(f"INSERT INTO {table} SELECT * FROM {table}__old")
            connection.execute(f"DROP TABLE {table}__old")
            for statement in dependents:
                connection.execute(statement)
        connection.execute("DROP TRIGGER lesson_episodes_close_once")
        connection.execute("ALTER TABLE lesson_episodes DROP COLUMN refusal_reason")
        text = PREVIOUS.read_text(encoding="utf-8")
        start = text.index("CREATE TRIGGER lesson_episodes_close_once")
        connection.execute(text[start:text.index("END;", start) + 4])
        connection.execute("DELETE FROM schema_migrations WHERE version = 248")
        connection.commit()


def test_248_changes_exactly_its_objects_and_keeps_every_row(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        before = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        counts = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in REBUILT}
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == [248]
    with closing(sqlite3.connect(database)) as connection:
        after = {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert set(after) == set(before)
        changed = {name for name in before if after.get(name) != before[name]}
        assert changed == {*REBUILT, "lesson_episodes", "lesson_episodes_close_once"}
        for table in REBUILT:
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == counts[table]
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as head:
        expected = {row[0]: row[1] for row in head.execute("SELECT name, sql FROM sqlite_master")}
    for name in changed:
        assert after[name] == expected[name]


def _head_copy(tmp_path: Path) -> sqlite3.Connection:
    database = tmp_path / "state.sqlite"
    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(_LESSON)
    return connection


def test_the_new_kinds_and_sources_are_admitted(tmp_path):
    with closing(_head_copy(tmp_path)) as connection:
        connection.execute("INSERT INTO followup_generation_jobs(id, kind, dedupe_key, created_at, updated_at) "
                           "VALUES ('j1', 'lesson', 'lesson:les_1:n1', 't', 't')")
        connection.execute("INSERT INTO generated_probe_items(practice_item_id, item_revision, source, created_at) "
                           "VALUES ('pi_1', 'r', 'lesson', 't')")
        for kind in ("lesson", "external_chat"):
            connection.execute("INSERT INTO learner_text_gap_jobs(id, source_kind, source_id, created_at, updated_at) "
                               "VALUES (?, ?, 's', 't', 't')", (f"g_{kind}", kind))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO followup_generation_jobs(id, kind, dedupe_key, created_at, updated_at) "
                               "VALUES ('j2', 'chat', 'x', 't', 't')")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO generated_probe_items(practice_item_id, item_revision, source, created_at) "
                               "VALUES ('pi_2', 'r', 'teacher', 't')")
        with pytest.raises(sqlite3.IntegrityError):  # still append-only
            connection.execute("UPDATE generated_probe_items SET source = 'mint'")


def test_a_probe_episode_closes_once_with_its_item_and_refusal_reason(tmp_path):
    with closing(_head_copy(tmp_path)) as connection:
        connection.execute(_PROBE)
        with pytest.raises(sqlite3.IntegrityError):  # the item id only with the close
            connection.execute("UPDATE lesson_episodes SET generated_item_id = 'pi_1' WHERE id = 'e1'")
        with pytest.raises(sqlite3.IntegrityError):  # an unknown reason
            connection.execute("UPDATE lesson_episodes SET closed_at = 't2', close_reason = 'refused', "
                               "refusal_reason = 'bored' WHERE id = 'e1'")
        connection.execute("UPDATE lesson_episodes SET closed_at = 't2', close_reason = 'answered', "
                           "generated_item_id = 'pi_1', outcome_correctness = 1.0 WHERE id = 'e1'")
        with pytest.raises(sqlite3.IntegrityError):  # closed once
            connection.execute("UPDATE lesson_episodes SET generated_item_id = 'pi_2' WHERE id = 'e1'")
        connection.execute(_PROBE.replace("'e1'", "'e2'").replace("'lt_1'", "'lt_2'").replace("'job_1'", "'job_2'"))
        connection.execute("UPDATE lesson_episodes SET closed_at = 't2', close_reason = 'refused', "
                           "refusal_reason = 'reserved_match' WHERE id = 'e2'")
        with pytest.raises(sqlite3.IntegrityError):  # an opening field never moves
            connection.execute(_PROBE.replace("'e1'", "'e3'").replace("'lt_1'", "'lt_3'"))
            connection.execute("UPDATE lesson_episodes SET generation_job_id = 'job_9', closed_at = 't3', "
                               "close_reason = 'retired' WHERE id = 'e3'")


@pytest.mark.durability
def test_248_applies_under_production_pragmas(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == [248]
    assert max(applied_versions(database)) == 248

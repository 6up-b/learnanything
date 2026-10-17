"""RW4a's migration 209 (spec_reader_workbench_v1 §7.5, §11): ``library_asks``.

One WORKFLOW table (paid outputs, never re-run on rebuild) with every column
§7.5 names, RW4d's ``kept_json`` and ``kept_at`` included so RW4d adds no
migration; ``comparison_id`` references the sources spec's
``source_comparisons``. The upgrade from 208 adds only this table and leaves
every other table's schema as it was. The durability lane runs it with
production pragmas (WAL, ``synchronous=FULL``).
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.db.connection import connect
from learnloop.db.migrate import (
    UPGRADE_TEST_HELPER,
    applied_versions,
    apply_migrations,
    discover_migrations,
    upgrade_allowance,
)
from learnloop.db.table_roles import TableRole, role_for_table

NOW = "2026-10-17T10:00:00Z"
SECTION_7_5 = {
    "id", "caller", "query_md", "query_hash", "personalized", "requested_perspectives_json", "manifest_json",
    "organizer_json", "comparison_id", "kept_json", "kept_at", "question_event_id", "model", "prompt_version",
    "created_at",
}


def _database_at_208(tmp_path: Path) -> Path:
    through = tmp_path / "through_208"
    through.mkdir()
    for migration in discover_migrations():
        if migration.version <= 208:
            (through / migration.path.name).write_text(migration.path.read_text(encoding="utf-8"), encoding="utf-8")
    database = tmp_path / "state.sqlite"
    apply_migrations(database, migrations_dir=through)
    assert max(applied_versions(database)) == 208
    return database


def _schema(database: Path) -> dict[str, str]:
    with closing(sqlite3.connect(database)) as connection:
        return {name: sql for name, sql in connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'")}


def _upgrade(tmp_path: Path) -> Path:
    database = _database_at_208(tmp_path)
    before = _schema(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        applied = apply_migrations(database)
    assert [migration.version for migration in applied][0] == 209
    after = _schema(database)
    added = set(after) - set(before)
    assert added == {"library_asks", "idx_library_asks_created", "idx_library_asks_extraction"}
    assert {name: sql for name, sql in after.items() if name in before} == before  # nothing else changed
    return database


def _check(database: Path) -> None:
    with closing(connect(database)) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(library_asks)")}
        assert SECTION_7_5 <= columns
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            "INSERT INTO library_asks (id, caller, entry, query_md, query_hash, personalized, created_at) "
            "VALUES ('la_1', 'learner', 'reader', 'why?', 'h', 1, ?)", (NOW,))
        row = connection.execute(
            "SELECT anchor_json, manifest_json, organizer_json, requested_perspectives_json, kept_json, comparison_id "
            "FROM library_asks WHERE id = 'la_1'").fetchone()
        assert tuple(row) == ("{}", "{}", "{}", "[]", None, None)
        for bad in ("INSERT INTO library_asks (id, caller, entry, query_md, query_hash, personalized, created_at) "
                    "VALUES ('la_2', 'model', 'reader', 'q', 'h', 1, '" + NOW + "')",
                    "INSERT INTO library_asks (id, caller, entry, query_md, query_hash, personalized, created_at) "
                    "VALUES ('la_3', 'learner', 'nowhere', 'q', 'h', 1, '" + NOW + "')",
                    "UPDATE library_asks SET comparison_id = 'scmp_missing' WHERE id = 'la_1'"):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(bad)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_209_adds_library_asks_and_nothing_else(tmp_path):
    _check(_upgrade(tmp_path))


@pytest.mark.durability
def test_209_on_the_durability_lane(tmp_path):
    database = _upgrade(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    _check(database)


def test_library_asks_is_workflow():
    assert role_for_table("library_asks") is TableRole.WORKFLOW


def test_the_head_fixture_is_at_209_in_rollback_mode():
    head = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_209" / "state.sqlite"
    assert head.read_bytes()[18:20] == b"\x01\x01"
    assert max(applied_versions(head)) == max(m.version for m in discover_migrations()) == 209

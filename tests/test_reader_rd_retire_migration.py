"""The Reader's retirement (phase 2 step 2): a desk window for a book still being prepared. ``desk_windows.kind``
gains ``preparing`` (migration ``reader_workbench_preparing_windows``); the table is rebuilt with every row kept and
nothing else changes. The content reference names the source alone (``desks/content_ref.py``)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations, upgrade_allowance
from learnloop.db.repositories import Repository
from learnloop.desks.content_ref import ContentRef
from learnloop.desks.workspace import desk_state
from tests.desk_helpers import Batches
from tests.helpers import MIGRATION_HEAD_FIXTURE, create_basic_vault

HEAD = MIGRATION_HEAD_FIXTURE / "state.sqlite"
MIGRATION = next(m for m in discover_migrations() if m.name == "reader_workbench_preparing_windows")
_KINDS = "'compare', 'panel', 'figure_notebook'"


def _sql(connection: sqlite3.Connection) -> dict[str, str]:
    return {row[0]: row[1] for row in connection.execute("SELECT name, sql FROM sqlite_master")}


def test_the_head_fixture_holds_it_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    assert MIGRATION.version in applied_versions(HEAD)
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        assert f"{_KINDS}, 'preparing'" in _sql(connection)["desk_windows"]


def _downgraded(database: Path) -> None:
    """A head copy with desk_windows as 262 made it (the CHECK without 'preparing'), rows and index kept."""

    with closing(sqlite3.connect(HEAD)) as source, closing(sqlite3.connect(database)) as target:
        source.backup(target)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        sql = _sql(connection)["desk_windows"]
        old = sql.replace(f"{_KINDS}, 'preparing'", _KINDS)
        assert old != sql
        connection.execute(old.replace('CREATE TABLE "desk_windows"', "CREATE TABLE desk_windows__undo", 1))
        connection.execute("INSERT INTO desk_windows__undo SELECT * FROM desk_windows")
        connection.execute("DROP TABLE desk_windows")
        connection.execute("ALTER TABLE desk_windows__undo RENAME TO desk_windows")
        connection.execute("CREATE INDEX idx_desk_windows_desk ON desk_windows(desk_id, closed_at, slot, pane)")
        connection.execute("DELETE FROM schema_migrations WHERE version = ?", (MIGRATION.version,))
        connection.execute("INSERT INTO desks(desk_id, title, position, created_at, updated_at) "
                           "VALUES ('d1', 'linear maps', 'a0', 't', 't')")
        for window_id, slot, kind, spec in (
            ("w1", 0, "source", '{"content": {"kind": "source", "source_id": "s", "extraction_id": "e"}}'),
            ("w2", 1, "panel", '{"content": {"kind": "panel", "panel": "path", "extraction_id": "e"}}'),
        ):
            connection.execute("INSERT INTO desk_windows(window_id, desk_id, slot, kind, spec_json, opened_at) "
                               "VALUES (?, 'd1', ?, ?, ?, 't')", (window_id, slot, kind, spec))
        connection.commit()


def test_it_rebuilds_desk_windows_alone_and_keeps_every_row(tmp_path):
    database = tmp_path / "state.sqlite"
    _downgraded(database)
    with closing(sqlite3.connect(database)) as connection:
        before = _sql(connection)
        kept = sorted(tuple(row) for row in connection.execute("SELECT * FROM desk_windows"))
        with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
            connection.execute("INSERT INTO desk_windows(window_id, desk_id, slot, kind, spec_json, opened_at) "
                               "VALUES ('w3', 'd1', 2, 'preparing', '{}', 't')")
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [m.version for m in apply_migrations(database)] == [MIGRATION.version]
    with closing(sqlite3.connect(database)) as connection:
        after = _sql(connection)
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert sorted(tuple(row) for row in connection.execute("SELECT * FROM desk_windows")) == kept
    assert set(after) == set(before)
    assert {name for name in before if before[name] != after[name]} == {"desk_windows"}
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as head:
        assert after == _sql(head)


def test_a_preparing_window_names_its_source_alone(tmp_path):
    adapter = TypeAdapter(ContentRef)
    ref = adapter.validate_python({"kind": "preparing", "sourceId": "src_book"})
    assert ref.wire() == {"kind": "preparing", "source_id": "src_book"}
    for bad in ({"kind": "preparing"}, {"kind": "preparing", "source_id": ""},
                {"kind": "preparing", "source_id": "s", "extraction_id": "e"}):
        with pytest.raises(ValidationError):
            adapter.validate_python(bad)
    repository = Repository(create_basic_vault(tmp_path / "vault").sqlite_path)
    batches = Batches(repository)
    batches.desk({"op": "create_desk", "desk_id": "d1", "title": "a book", "position": "a0"})
    reply = batches.desk({"op": "open_window", "desk_id": "d1", "window_id": "w1", "expected_version": 1,
                          "content": {"kind": "preparing", "source_id": "src_book"}})
    assert reply["results"] == [{"status": "ok"}]
    window = desk_state(repository)["desks"][0]["slots"][0]["windows"][0]
    assert window["kind"] == "preparing" and window["content"] == {"kind": "preparing", "source_id": "src_book"}

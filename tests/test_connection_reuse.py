"""The fast lane's connection reuse (``tests/connection_reuse.py``) must look like fresh connections to the test.

A reused connection that leaked a setting, a transaction or a stale view would let a test pass that production fails,
so each way a fresh connection differs from an idle one is pinned here, against a real file. The last tests pin that
the lanes which must exercise production's open path still do.
"""

from __future__ import annotations

from contextlib import closing
import os
from pathlib import Path
import sqlite3

import pytest

from learnloop.db import connection as DBC
from learnloop.db.connection import connect
from learnloop.db.copies import backup_database
from tests.connection_reuse import TestLanePool


def _database(tmp_path: Path, name: str = "reuse.sqlite", rows: int = 1) -> Path:
    path = tmp_path / name
    with closing(sqlite3.connect(path)) as raw:
        raw.execute("CREATE TABLE t(n INTEGER)")
        raw.executemany("INSERT INTO t VALUES (?)", [(n,) for n in range(rows)])
        raw.commit()
    return path


def _raw_of(connection):
    return connection._connection


def test_a_test_runs_inside_the_pool_and_reuses_one_connection_after_a_read_and_after_dml(tmp_path):
    database = _database(tmp_path)
    assert isinstance(DBC._REUSED.get(), TestLanePool)
    seen = set()
    for n in range(5):
        with closing(connect(database)) as connection:
            seen.add(id(_raw_of(connection)))
            connection.execute("INSERT INTO t VALUES (?)", (n,))
            connection.commit()
        with closing(connect(database)) as connection:
            seen.add(id(_raw_of(connection)))
            assert connection.execute("SELECT COUNT(*) FROM t").fetchone()[0] == n + 2
    assert len(seen) == 1


@pytest.mark.parametrize("statement", [
    "PRAGMA foreign_keys = OFF",
    "PRAGMA busy_timeout = 1",
    "CREATE TEMP TABLE scratch(n)",
    "CREATE TABLE made_here(n)",
    "ATTACH DATABASE ':memory:' AS other",
])
def test_a_connection_that_changed_any_setting_or_schema_is_never_handed_out_again(tmp_path, statement):
    database = _database(tmp_path)
    with closing(connect(database)) as connection:
        before = _raw_of(connection)
        connection.execute(statement)
    with closing(connect(database)) as connection:
        assert _raw_of(connection) is not before
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == DBC.BUSY_TIMEOUT_MS
        assert connection.execute("SELECT COUNT(*) FROM sqlite_temp_master").fetchone()[0] == 0
        assert "other" not in [row[1] for row in connection.execute("PRAGMA database_list")]


def test_a_connection_api_call_that_changes_state_is_not_kept(tmp_path):
    database = _database(tmp_path)
    with closing(connect(database)) as connection:
        before = _raw_of(connection)
        connection.create_function("probe", 0, lambda: 1)
    with closing(connect(database)) as connection:
        assert _raw_of(connection) is not before
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("SELECT probe()")


def test_an_uncommitted_write_is_discarded_at_close_and_holds_no_lock(tmp_path):
    database = _database(tmp_path)
    with closing(connect(database)) as connection:
        connection.execute("INSERT INTO t VALUES (99)")
        assert connection.in_transaction
    with closing(sqlite3.connect(database, timeout=0)) as other:
        other.execute("INSERT INTO t VALUES (100)")
        other.commit()
    with closing(connect(database)) as connection:
        assert not connection.in_transaction
        assert sorted(row[0] for row in connection.execute("SELECT n FROM t")) == [0, 100]


def test_a_cursor_left_mid_read_keeps_no_snapshot_or_lock(tmp_path):
    database = _database(tmp_path, rows=1000)
    with closing(connect(database)) as connection:
        cursor = connection.execute("SELECT n FROM t")
        cursor.fetchone()
    with closing(sqlite3.connect(database, timeout=0)) as other:
        other.execute("DELETE FROM t")
        other.commit()
    with closing(connect(database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 0


def test_two_users_at_once_get_two_connections_and_a_closed_handle_stays_closed(tmp_path):
    database = _database(tmp_path)
    first = connect(database)
    second = connect(database)
    assert _raw_of(first) is not _raw_of(second)
    first.close()
    with pytest.raises(sqlite3.ProgrammingError):
        first.execute("SELECT 1")
    third = connect(database)  # the raw connection first gave back: the old handle must stay closed
    with pytest.raises(sqlite3.ProgrammingError):
        first.execute("SELECT 1")
    third.close()
    second.close()


def test_a_commit_by_another_connection_is_seen(tmp_path):
    database = _database(tmp_path)
    with closing(connect(database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 1
    with closing(sqlite3.connect(database)) as other:
        other.execute("INSERT INTO t VALUES (2)")
        other.commit()
    with closing(connect(database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 2


def test_a_database_replaced_by_rename_is_read_afresh(tmp_path):
    database = _database(tmp_path)
    replacement = _database(tmp_path, "new.sqlite", rows=7)
    with closing(connect(database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 1
    os.replace(replacement, database)
    with closing(connect(database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 7


def test_a_database_deleted_is_gone_for_a_read_only_open(tmp_path):
    database = _database(tmp_path)
    with closing(connect(database, read_only=True)) as connection:
        connection.execute("SELECT 1 FROM t")
    database.unlink()
    with pytest.raises(sqlite3.OperationalError):
        connect(database, read_only=True)


def test_bytes_edited_in_place_are_read_afresh_even_with_the_change_counter_untouched(tmp_path):
    """What only the file check can catch: SQLite trusts its page cache while the header's change counter stands."""

    database = _database(tmp_path)
    with closing(connect(database)) as connection:
        assert connection.execute("SELECT n FROM t").fetchone()[0] == 0
        kept = _raw_of(connection)
    original = database.read_bytes()
    other = _database(tmp_path, "edited.sqlite")
    with closing(sqlite3.connect(other)) as raw:
        raw.execute("UPDATE t SET n = 41")
        raw.commit()
    edited = other.read_bytes()
    assert len(edited) == len(original)
    # The same counter as the original's, so only the bytes of the row differ to a connection that cached the page.
    edited = edited[:24] + original[24:28] + edited[28:92] + original[92:100] + edited[100:]
    database.write_bytes(edited)
    with closing(connect(database)) as connection:
        assert _raw_of(connection) is not kept
        assert connection.execute("SELECT n FROM t").fetchone()[0] == 41


def test_a_wal_database_is_never_kept(tmp_path):
    database = _database(tmp_path)
    with closing(sqlite3.connect(database)) as raw:
        assert raw.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
    with closing(connect(database)) as connection:
        connection.execute("INSERT INTO t VALUES (5)")
        connection.commit()
    # Closing the last connection checkpointed the database and removed its companions, as production's close does.
    assert not database.with_name(database.name + "-wal").exists()
    assert not database.with_name(database.name + "-shm").exists()
    assert not DBC._REUSED.get().idle.get((str(database.resolve()), False))


def test_a_backup_onto_a_pooled_target_works_and_the_target_is_not_kept(tmp_path):
    source = _database(tmp_path, rows=3)
    target_path = tmp_path / "target.sqlite"
    with closing(connect(source, read_only=True)) as origin, closing(connect(target_path)) as target:
        kept = _raw_of(target)
        origin.backup(target)
    with closing(connect(target_path)) as target:
        assert _raw_of(target) is not kept
        assert target.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 3


def test_another_thread_opens_its_own_and_the_pool_closes_with_the_test(tmp_path):
    import threading

    database = _database(tmp_path)
    types = []

    def read():
        with closing(connect(database)) as connection:
            types.append(type(connection))
            connection.execute("SELECT 1").fetchone()

    thread = threading.Thread(target=read)
    thread.start()
    thread.join()
    assert types == [sqlite3.Connection]


def test_a_test_that_forbids_opening_a_connection_is_not_satisfied_by_an_idle_one(tmp_path, monkeypatch):
    database = _database(tmp_path)
    with closing(connect(database, read_only=True)) as connection:
        connection.execute("SELECT 1 FROM t").fetchone()

    def forbidden(*args, **kwargs):
        raise AssertionError("store access")

    monkeypatch.setattr(sqlite3, "connect", forbidden)
    with pytest.raises(AssertionError, match="store access"):
        connect(database, read_only=True)


def test_a_shortened_busy_timeout_reaches_the_next_connection(tmp_path, monkeypatch):
    database = _database(tmp_path)
    with closing(connect(database)) as connection:
        connection.execute("SELECT 1 FROM t").fetchone()
    monkeypatch.setattr(DBC, "BUSY_TIMEOUT_MS", 50)
    with closing(connect(database)) as connection:
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 50


@pytest.mark.fresh_connections
def test_the_marker_opens_real_connections(tmp_path):
    database = _database(tmp_path)
    assert DBC._REUSED.get() is None
    with closing(connect(database)) as connection:
        assert type(connection) is sqlite3.Connection


@pytest.mark.durability
def test_the_durability_lane_runs_production_connections_copies_and_fsync(tmp_path, monkeypatch):
    from tests.helpers import create_basic_vault

    assert DBC._REUSED.get() is None
    database = Path(create_basic_vault(tmp_path / "vault").sqlite_path)
    with closing(connect(database)) as connection:
        assert type(connection) is sqlite3.Connection
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert connection.execute("PRAGMA synchronous").fetchone()[0] == 2  # FULL
    synced: list[int] = []
    import tests.conftest as lane

    real_fsync = lane._real_fsync
    monkeypatch.setattr(lane, "_real_fsync", lambda fd: (synced.append(fd), real_fsync(fd))[1])
    with open(tmp_path / "file", "wb") as handle:
        os.fsync(handle.fileno())
    assert synced, "os.fsync must reach the disk in the durability lane"
    seen_synchronous: list[int] = []
    real_connect = sqlite3.connect

    def watching(*args, **kwargs):
        connection = real_connect(*args, **kwargs)
        seen_synchronous.append(connection.execute("PRAGMA synchronous").fetchone()[0])
        return connection

    monkeypatch.setattr(sqlite3, "connect", watching)
    backup_database(database, tmp_path / "copy.sqlite")
    assert 2 in seen_synchronous  # the copy's target is written at the default FULL, as in production


def test_the_fast_lanes_copy_target_and_fsync_skip_the_disk(tmp_path, monkeypatch):
    calls: list[int] = []
    import tests.conftest as lane

    monkeypatch.setattr(lane, "_real_fsync", lambda fd: calls.append(fd))
    with open(tmp_path / "file", "wb") as handle:
        os.fsync(handle.fileno())
    assert calls == []
    with pytest.raises(OSError):
        os.fsync(987654)  # a bad descriptor still fails, as it would
    copy = lane._db_copies.sqlite3.connect(tmp_path / "copy.sqlite")
    assert copy.execute("PRAGMA synchronous").fetchone()[0] == 0
    copy.close()


def _schema_and_migrations(path: Path):
    with closing(sqlite3.connect(path)) as connection:
        return (
            connection.execute("SELECT type, name, tbl_name, sql FROM sqlite_master ORDER BY type, name").fetchall(),
            connection.execute("SELECT version, name, applied_at FROM schema_migrations ORDER BY version").fetchall(),
            connection.execute("PRAGMA journal_mode").fetchone()[0],
        )


def test_a_copied_fresh_schema_matches_a_built_one_and_stamps_this_builds_clock(tmp_path, monkeypatch):
    """The lane's fresh-schema shortcut against the real build, on the same migrations and the same clock."""

    from datetime import UTC, datetime

    from learnloop.clock import FrozenClock
    from learnloop.db import migrate
    import tests.conftest as lane

    clock = FrozenClock(datetime(2031, 2, 3, 4, 5, tzinfo=UTC))
    migrate.create_or_attach_current(tmp_path / "first.sqlite", clock=clock)  # may itself be the process's real build
    migrate.create_or_attach_current(tmp_path / "copied.sqlite", clock=clock)
    assert lane._built_schemas, "the second build must have a schema to copy"
    copied = _schema_and_migrations(tmp_path / "copied.sqlite")
    monkeypatch.setattr(lane, "_real_open_paths", True)
    migrate.create_or_attach_current(tmp_path / "built.sqlite", clock=clock)
    assert copied == _schema_and_migrations(tmp_path / "built.sqlite")
    assert {row[2] for row in copied[1]} == {"2031-02-03T04:05:00Z"}
    assert not (tmp_path / "copied.sqlite.tmp").exists()
    assert sorted(path.name for path in tmp_path.iterdir()) == ["built.sqlite", "copied.sqlite", "first.sqlite"]


@pytest.mark.durability
def test_the_durability_lane_builds_every_fresh_schema_for_real(tmp_path, monkeypatch):
    from learnloop.db import migrate
    import tests.conftest as lane

    calls: list[Path] = []
    production = lane._production_apply_fresh

    def counted(path, migrations, clock):
        calls.append(path)
        return production(path, migrations, clock)

    monkeypatch.setattr(lane, "_production_apply_fresh", counted)
    migrate.create_or_attach_current(tmp_path / "a.sqlite")
    migrate.create_or_attach_current(tmp_path / "b.sqlite")
    assert len(calls) == 2
    with closing(sqlite3.connect(tmp_path / "b.sqlite")) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_remembered_yaml_is_the_real_dump_and_comments_and_order_are_never_mixed_up():
    from learnloop.vault import yaml_io
    import tests.conftest as lane

    plain = {"b": 1, "a": [True, None, 1.5, "x: y"]}
    assert yaml_io._dumped(plain) == lane._production_dumped(plain) == yaml_io._dumped(dict(plain))
    # Key order is part of the text, and 1 is not True or "1".
    assert yaml_io._dumped({"a": 1, "b": 2}) != yaml_io._dumped({"b": 2, "a": 1})
    assert yaml_io._dumped({"a": 1}) != yaml_io._dumped({"a": True}) != yaml_io._dumped({"a": "1"})
    # A round-trip mapping keeps the comment a plain mapping with the same repr doesn't have.
    commented = yaml_io.yaml_from_string("a: 1  # keep me\n")
    assert "keep me" in yaml_io._dumped(commented)
    assert "keep me" not in yaml_io._dumped({"a": 1})
    # A key too long to fold still comes back readable (the reason _dumped re-parses).
    long_key = {"k" * 300 + " " + "k" * 300: 1}
    assert yaml_io.yaml_from_string(yaml_io._dumped(long_key)) == long_key


def test_a_remembered_json_schema_is_the_real_one_and_a_caller_cannot_change_it():
    import pydantic

    import tests.conftest as lane

    class Model(pydantic.BaseModel):
        n: int

    first = Model.model_json_schema()
    assert first == lane._production_json_schema(Model)
    first["properties"]["n"]["type"] = "changed"
    assert Model.model_json_schema()["properties"]["n"]["type"] == "integer"
    assert Model.model_json_schema(by_alias=False) == lane._production_json_schema(Model, by_alias=False)


# -- what can escape a checkout (Codex review F4) ------------------------------------------------------------------


def test_a_cursors_connection_is_the_proxy_not_the_raw_handle(tmp_path):
    database = _database(tmp_path)
    connection = connect(database)
    for cursor in (connection.execute("SELECT 1"), connection.cursor()):
        assert cursor.connection is connection
    connection.close()
    with pytest.raises(sqlite3.ProgrammingError):
        cursor.connection.execute("SELECT 1")


def test_a_raw_handles_cursor_cant_keep_a_lock_past_release(tmp_path):
    database = _database(tmp_path, rows=1000)
    connection = connect(database)
    raw_cursor = _raw_of(connection).cursor()
    raw_cursor.execute("SELECT n FROM t").fetchone()
    direct = _raw_of(connection).execute("SELECT n FROM t")
    direct.fetchone()
    connection.close()
    with pytest.raises(sqlite3.ProgrammingError):
        raw_cursor.fetchone()
    with pytest.raises(sqlite3.ProgrammingError):
        direct.fetchone()
    with closing(sqlite3.connect(database, timeout=0)) as other:
        other.execute("DELETE FROM t")  # no reader's lock is left to block this commit
        other.commit()


@pytest.mark.parametrize("register", [
    lambda raw: raw.create_function("probe", 0, lambda: 1),
    lambda raw: raw.create_aggregate("probe", 0, type("A", (), {"step": lambda self: None, "finalize": lambda self: 1})),
    lambda raw: raw.create_collation("probe", lambda a, b: 0),
    lambda raw: raw.set_progress_handler(lambda: 0, 100),
    lambda raw: raw.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 100_000),
], ids=["function", "aggregate", "collation", "progress", "limit"])
def test_a_raw_registered_state_never_reaches_the_next_user(tmp_path, register):
    database = _database(tmp_path)
    with closing(connect(database)) as connection:
        before = _raw_of(connection)
        register(before)
    with closing(connect(database)) as connection:
        assert _raw_of(connection) is not before
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("SELECT probe()")


def test_state_registered_on_a_kept_raw_handle_while_idle_ends_its_reuse(tmp_path):
    database = _database(tmp_path)
    with closing(connect(database)) as connection:
        kept = _raw_of(connection)
    kept.create_function("probe", 0, lambda: 1)
    with closing(connect(database)) as connection:
        assert _raw_of(connection) is not kept


def test_a_blob_handle_cant_survive_release(tmp_path):
    database = _database(tmp_path)
    with closing(sqlite3.connect(database)) as setup:
        setup.execute("CREATE TABLE b(data BLOB)")
        setup.execute("INSERT INTO b VALUES (zeroblob(8))")
        setup.commit()
    connection = connect(database, read_only=True)
    raw = _raw_of(connection)
    blob = connection.blobopen("b", "data", 1, readonly=True)
    connection.close()
    with pytest.raises(sqlite3.ProgrammingError):
        blob.read()
    with closing(connect(database, read_only=True)) as again:
        assert _raw_of(again) is not raw


#: Files allowed to read these counters, because they don't use a pooled connection.
_OWN_CONNECTION_FILES = {"src/learnloop_sidecar/handlers/sqlite_admin.py"}  # sqlite3.connect, closed in one request


def _connection_scoped_counter_reads(source: str) -> list[str]:
    import ast

    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Attribute) and node.attr == "lastrowid":
            found.append(f"line {node.lineno}: .lastrowid")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and "last_insert_rowid" in node.value.lower():
            found.append(f"line {node.lineno}: last_insert_rowid()")
    return found


def test_src_reads_no_rowid_counter_a_kept_connection_would_carry_over():
    """A kept connection keeps these from its last user's DML, where production's fresh one has none. Code reading them
    across checkouts would pass here and fail in production, or the reverse. Today nothing does."""

    root = Path(__file__).resolve().parents[1]
    readers = {}
    for path in (root / "src").rglob("*.py"):
        relative = path.relative_to(root).as_posix()
        found = _connection_scoped_counter_reads(path.read_text(encoding="utf-8"))
        if found and relative not in _OWN_CONNECTION_FILES:
            readers[relative] = found
    assert not readers, f"see tests/connection_reuse.py's limits before using these: {readers}"
    # The scan itself sees both forms.
    assert _connection_scoped_counter_reads("x = cursor.lastrowid\ny = 'SELECT last_insert_rowid()'\n") == [
        "line 1: .lastrowid", "line 2: last_insert_rowid()"]
    own = (root / next(iter(_OWN_CONNECTION_FILES))).read_text(encoding="utf-8")
    assert "sqlite3.connect(" in own and "learnloop.db.connection" not in own


def test_shared_containers_are_never_served_a_plain_copys_yaml():
    """YAML writes a repeated container as an anchor and an alias, and its repr can't show that."""

    from learnloop.vault import yaml_io

    separate = {"a": [1], "b": [1]}
    assert "&" not in yaml_io._dumped(separate)
    shared_list = [1]
    aliased = yaml_io._dumped({"a": shared_list, "b": shared_list})
    assert "&" in aliased and "*" in aliased
    assert yaml_io._dumped({"a": [1], "b": [1]}) == yaml_io._dumped(separate) != aliased
    shared_map = {"k": 1}
    assert "&" in yaml_io._dumped({"a": shared_map, "b": [shared_map]})


def test_a_cycle_goes_to_the_real_dump():
    from learnloop.vault import yaml_io
    import tests.conftest as lane

    cycle: dict = {"a": 1}
    cycle["self"] = cycle
    assert lane._is_plain({"ok": [1, 2]}) is True
    assert lane._is_plain(cycle) is False  # no recursion error before the real function runs
    assert "&" in yaml_io._dumped(cycle)

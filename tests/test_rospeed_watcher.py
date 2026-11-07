"""Router speed, landing ruling R2: the decision scope's commit-version watcher (``objective_inputs.decision_reads``;
Codex review F2) is a read-only connection that never writes. Under the durability lane (WAL, ``synchronous=FULL``,
a freshly initialised vault) it leaves no -wal frames of its own, never changes the journal header and holds no lock
that blocks a writer: a writer commits (``BEGIN IMMEDIATE`` and ``BEGIN EXCLUSIVE``, with no busy wait) while the
watcher is open, and a ``TRUNCATE`` checkpoint completes while it is open (it pins no snapshot).

As with every other open connection, the app's own read-only watchers included (``reading_choice.fingerprint``,
``canonical_projection_rollout``), a writer that closes while the watcher is still open does not checkpoint on close;
the -wal then holds that writer's committed frames, and only those, until the next read-write connection checkpoints
them (the last test).
"""

from __future__ import annotations

from contextlib import closing
import os
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest

from learnloop.daily_plan import objective_inputs as OI
from learnloop.db.connection import connect
from learnloop.db.storage import header_journal_mode

pytestmark = pytest.mark.durability

_PROBE = "rospeed_watcher_probe"


def _wal_vault(tmp_path) -> Path:
    from tests.helpers import create_basic_vault

    database = Path(create_basic_vault(tmp_path / "vault").sqlite_path)
    assert header_journal_mode(database) == "wal"
    with closing(connect(database)) as connection:
        connection.execute(f"CREATE TABLE {_PROBE}(n INTEGER)")
        connection.commit()
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    assert _wal_bytes(database) == 0
    return database


def _wal_bytes(database: Path) -> int:
    wal = Path(f"{database}-wal")
    return wal.stat().st_size if wal.exists() else 0


def _header(database: Path) -> bytes:
    with database.open("rb") as handle:
        return handle.read(100)


def _writer(database: Path) -> sqlite3.Connection:
    writer = connect(database)
    writer.execute("PRAGMA busy_timeout = 0")  # a lock held by the watcher fails at once, never waits
    return writer


def _commit(writer: sqlite3.Connection, n: int, begin: str = "IMMEDIATE") -> None:
    writer.execute(f"BEGIN {begin}")
    writer.execute(f"INSERT INTO {_PROBE}(n) VALUES (?)", (n,))
    writer.commit()


def _watcher(reads: OI._DecisionReads, database: Path) -> sqlite3.Connection:
    return reads._watchers[str(database.resolve())][1]


def test_a_writer_commits_while_the_watcher_is_open_and_the_watcher_never_writes(tmp_path):
    database = _wal_vault(tmp_path)
    header = _header(database)
    repository = SimpleNamespace(sqlite_path=database)
    writer = _writer(database)
    try:
        with OI.decision_reads():
            reads = OI._DECISION_READS.get()
            first = reads.version(repository)
            watcher = _watcher(reads, database)
            # the watcher's reads alone add nothing to the WAL and leave no transaction open
            for _ in range(5):
                assert reads.version(repository) == first
            assert _wal_bytes(database) == 0
            assert not watcher.in_transaction
            # a writer commits while the watcher is open, at once, in both write modes
            _commit(writer, 1, "IMMEDIATE")
            second = reads.version(repository)
            assert second is not None and second[2] != first[2]  # the commit moved the version
            _commit(writer, 2, "EXCLUSIVE")  # right after a version read too
            third = reads.version(repository)
            assert third is not None and third[2] != second[2]
            # the watcher pins no snapshot: a TRUNCATE checkpoint completes with it open and empties the WAL
            busy, _log, _done = writer.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            assert busy == 0
            assert _wal_bytes(database) == 0
            # read-only: it never wrote and cannot (a checkpoint's WAL reset moves the version too: a read again)
            assert watcher.total_changes == 0
            settled = reads.version(repository)
            with pytest.raises(sqlite3.OperationalError, match="readonly"):
                watcher.execute(f"INSERT INTO {_PROBE}(n) VALUES (0)")
            assert reads.version(repository) == settled  # its own refused write moved nothing
            assert _wal_bytes(database) == 0
        assert reads._watchers == {}  # closed with the scope
        _commit(writer, 3)
    finally:
        writer.close()
    # the writer closed last: checkpointed and no -wal frames; the header is the one it had
    assert _wal_bytes(database) == 0
    assert _header(database)[18:20] == header[18:20] == b"\x02\x02"
    assert header_journal_mode(database) == "wal"
    with closing(connect(database, read_only=True)) as check:
        assert [row[0] for row in check.execute(f"SELECT n FROM {_PROBE} ORDER BY n")] == [1, 2, 3]


def test_a_writer_closing_before_the_watcher_leaves_only_its_own_frames(tmp_path):
    """A writer that commits and closes while the watcher is open does not checkpoint on close (another connection is
    open), so the -wal holds that writer's frames after the scope ends, exactly what a writer closing while any
    other connection is open leaves. None is the watcher's: an equal commit with no watcher open, on an equal
    database whose other connection is a plain read-only one, leaves the same frames, and the next read-write
    connection's close checkpoints them all."""

    def frames_left(database: Path, *, watcher: bool) -> int:
        repository = SimpleNamespace(sqlite_path=database)
        if watcher:
            scope = OI.decision_reads()
            scope.__enter__()
            OI._DECISION_READS.get().version(repository)
        else:
            reader = sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)
            reader.execute("PRAGMA data_version").fetchone()
        writer = _writer(database)
        _commit(writer, 1)
        writer.close()
        if watcher:
            scope.__exit__(None, None, None)
        else:
            reader.close()
        return _wal_bytes(database)

    with_watcher = _wal_vault(tmp_path / "with")
    plain = _wal_vault(tmp_path / "plain")
    header = _header(with_watcher)
    left = frames_left(with_watcher, watcher=True)
    assert left > 0
    assert left == frames_left(plain, watcher=False)
    assert _header(with_watcher)[18:20] == header[18:20]
    # the next read-write connection checkpoints them all on close
    connect(with_watcher).close()
    assert _wal_bytes(with_watcher) == 0
    assert header_journal_mode(with_watcher) == "wal"
    with closing(connect(with_watcher, read_only=True)) as check:
        assert [row[0] for row in check.execute(f"SELECT n FROM {_PROBE}")] == [1]


def test_a_rollback_header_database_is_watched_without_blocking_a_writer(tmp_path):
    """A vault still in rollback mode (one the owner has not opened since WAL): the same, with no -wal at all."""

    database = tmp_path / "rollback.sqlite"
    with closing(sqlite3.connect(database)) as setup:
        setup.execute("PRAGMA journal_mode = DELETE")
        setup.execute(f"CREATE TABLE {_PROBE}(n INTEGER)")
        setup.commit()
    header = _header(database)
    assert header_journal_mode(database) == "rollback"
    repository = SimpleNamespace(sqlite_path=database)
    writer = sqlite3.connect(database, isolation_level=None)
    writer.execute("PRAGMA busy_timeout = 0")
    try:
        with OI.decision_reads():
            reads = OI._DECISION_READS.get()
            first = reads.version(repository)
            for begin in ("IMMEDIATE", "EXCLUSIVE"):
                writer.execute(f"BEGIN {begin}")
                writer.execute(f"INSERT INTO {_PROBE}(n) VALUES (1)")
                writer.execute("COMMIT")
            assert reads.version(repository)[2] != first[2]
            assert _watcher(reads, database).total_changes == 0
    finally:
        writer.close()
    assert not os.path.exists(f"{database}-wal")
    assert _header(database)[18:20] == header[18:20]

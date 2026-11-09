"""The fast lane's connection reuse: one test's ``connect()`` calls share idle connections.

Why: a SQLite connection parses the whole schema at its first statement and frees it at close. At 396 tables that is
about 3 ms, and the code opens a connection per repository call, so a random sample of 120 mid-length tests spent 50%
of its wall clock there and a chain-walking upgrade test 96% (docs/reviews/test-suite-audit.md). Nothing about a test
depends on paying that again.

It plugs into production's own pool seam (``db.connection._REUSED``, router speed stage 2) with no source change, so a
connection handed out here has the guarantees that pool was reviewed for: the caller's thread only; never two users at
once; on release its cursors are closed, an open transaction is rolled back and its factories are reset; an AD guard
installs and leaves through the same connection hook. It differs from production's pool in two ways, both test-only:

* It keeps a connection after plain DML (INSERT, UPDATE, DELETE), which production's closes. DML leaves no connection
  state, and alternating reads and writes is what the code does most. A PRAGMA with an argument, DDL, ATTACH or a
  connection API call that changes state still closes the connection at release (production's rule R4), so no setting
  reaches the next user.
* It notices what no SQLite connection can: a database file replaced or edited behind its back. The file's identity,
  size and mtime are recorded at each release, and a mismatch at the next checkout closes that path's idle connections.

A test that patches the open path (``sqlite3.connect``, ``BUSY_TIMEOUT_MS``...) gets real opens while its patch stands.

A WAL database is never kept (closing the last connection checkpoints it, which tests may observe). The durability
lane, the owner lane, ``--fresh-connections`` and the ``fresh_connections`` marker open every connection for real, so
production's open path keeps running in the gate.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from learnloop.db import connection as _db_connection
from learnloop.db.scopes import apply_connection_hook, current_ingest_job_id

_DML_ACTIONS = frozenset({sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE})


class _KeptAfterDml(_db_connection._PooledSqlite):
    def _wrapped(self, inner):
        production = super()._wrapped(inner)

        def authorizer(action, arg1, arg2, database, trigger):
            if action in _DML_ACTIONS:
                return sqlite3.SQLITE_OK if inner is None else inner(action, arg1, arg2, database, trigger)
            return production(action, arg1, arg2, database, trigger)

        return authorizer


def _signature(path: str) -> tuple[int, int, int, int] | None:
    try:
        stat = os.stat(path)
    except OSError:
        return None
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)


_PRODUCTION_OPEN = (sqlite3.connect, _db_connection._open_read_only, _db_connection._open_writable,
                    _db_connection._configure, _db_connection.BUSY_TIMEOUT_MS)


def _open_path_patched() -> bool:
    """A test has changed what opening a connection does: it spies on it, forbids it ("this code touches no store") or
    shortens the busy timeout. Reusing an idle connection would skip that, and such a test could pass for the wrong
    reason, so while the patch stands every connect takes production's open path."""

    current = (sqlite3.connect, _db_connection._open_read_only, _db_connection._open_writable,
               _db_connection._configure, _db_connection.BUSY_TIMEOUT_MS)
    return any(now is not original and now != original for now, original in zip(current, _PRODUCTION_OPEN))


class _Reused(_db_connection._ReusedConnection):
    __slots__ = ()

    def backup(self, target, **kwargs):
        """SQLite's backup takes a real connection as its target; a pooled one is its raw connection, not kept after."""

        if isinstance(target, _db_connection._ReusedConnection):
            object.__setattr__(target, "_changed", True)
            target = target._connection
        return self._raw().backup(target, **kwargs)


class TestLanePool(_db_connection._ConnectionPool):
    """One test's idle connections (see the module docstring)."""

    __test__ = False  # not a test class, whatever its name

    def __init__(self) -> None:
        super().__init__()
        self._file_at_release: dict[str, tuple[int, int, int, int] | None] = {}

    def connect(self, sqlite_path: Path, *, read_only: bool):
        if self.closed or (not read_only and current_ingest_job_id(sqlite_path) is not None):
            return None
        if _open_path_patched():
            self._forget_all()
            return None
        resolved = str(sqlite_path.resolve())
        key = (resolved, bool(read_only))
        if resolved in self._file_at_release and _signature(resolved) != self._file_at_release[resolved]:
            self._forget(resolved)
        idle = self.idle.get(key)
        if idle:
            raw = idle.pop()
        else:
            if read_only:
                raw = _db_connection._open_read_only(sqlite_path, factory=_KeptAfterDml)
            else:
                sqlite_path.parent.mkdir(parents=True, exist_ok=True)
                raw = _db_connection._open_writable(sqlite_path, factory=_KeptAfterDml)
            self.opened += 1
        self.handed += 1
        raw.set_authorizer(None)
        raw.set_trace_callback(None)
        apply_connection_hook(raw, sqlite_path)
        raw.watch()
        return _Reused(raw, self, key)

    def give(self, key: tuple[str, bool], raw: sqlite3.Connection) -> None:
        if not self.closed and raw.execute("PRAGMA journal_mode").fetchone()[0] == "wal":
            raw.close()
            return
        super().give(key, raw)
        if not self.closed:
            self._file_at_release[key[0]] = _signature(key[0])

    def _forget_all(self) -> None:
        for resolved, _mode in list(self.idle):
            self.idle[(resolved, _mode)], closing = [], self.idle[(resolved, _mode)]
            for raw in closing:
                raw.close()

    def _forget(self, resolved: str) -> None:
        for mode in (False, True):
            for raw in self.idle.pop((resolved, mode), []):
                raw.close()
        del self._file_at_release[resolved]

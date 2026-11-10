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

**A limit of keeping a connection after DML:** the connection-scoped counters (``last_insert_rowid()``, ``.lastrowid``,
``total_changes``, ``changes()``) carry over from the last user, where production's fresh connection starts at nothing. A
reader across checkouts would see a different value here. ``tests/test_connection_reuse.py`` fails if ``src`` starts
reading the rowid counters on a pooled connection. Otherwise this difference, and any other a fresh connection would
show, is covered only by a full ``--fresh-connections`` run, due at each refactor arc's close.

A WAL database is never kept (closing the last connection checkpoints it, which tests may observe). The durability
lane, the owner lane, ``--fresh-connections`` and the ``fresh_connections`` marker open every connection for real, so
production's open path keeps running in the gate.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
import weakref

from learnloop.db import connection as _db_connection
from learnloop.db.scopes import apply_connection_hook, current_ingest_job_id

_DML_ACTIONS = frozenset({sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE})


#: What outlives a checkout on the raw connection: production's list, plus a blob, which holds a statement open.
_STATE_CALLS = _db_connection._CONNECTION_STATE_CALLS | {"blobopen"}


class _ProxiedCursor(sqlite3.Cursor):
    """``cursor.connection`` is the checkout's proxy, so user code can't reach the raw connection through a cursor."""

    @property
    def connection(self):
        raw = super().connection
        proxy = raw._proxy() if raw._proxy is not None else None
        return raw if proxy is None else proxy


class _KeptAfterDml(_db_connection._PooledSqlite):
    """A kept connection. Every cursor is recorded here, whoever made it, so release closes all of them. A call that
    changes the connection's own state marks it for good, even made directly on this object, so it's never reused."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._live_cursors = weakref.WeakSet()
        self._state_changed = False
        self._proxy = None

    def _wrapped(self, inner):
        production = super()._wrapped(inner)

        def authorizer(action, arg1, arg2, database, trigger):
            if action in _DML_ACTIONS:
                return sqlite3.SQLITE_OK if inner is None else inner(action, arg1, arg2, database, trigger)
            return production(action, arg1, arg2, database, trigger)

        return authorizer

    def cursor(self, factory=_ProxiedCursor):
        cursor = super().cursor(factory)
        if not isinstance(cursor, _ProxiedCursor):
            self._state_changed = True  # its .connection is this raw object: never hand this connection out again
        self._live_cursors.add(cursor)
        return cursor

    # sqlite3's own execute methods make their cursor in C, past cursor() above.
    def execute(self, sql, parameters=(), /):
        return self.cursor().execute(sql, parameters)

    def executemany(self, sql, parameters, /):
        return self.cursor().executemany(sql, parameters)

    def executescript(self, script, /):
        return self.cursor().executescript(script)

    def unwatch(self) -> bool:
        return super().unwatch() or self._state_changed

    def close_cursors(self) -> None:
        for cursor in list(self._live_cursors):
            cursor.close()


def _marks_state(name: str):
    production = getattr(sqlite3.Connection, name)

    def call(self, *args, **kwargs):
        self._state_changed = True
        return production(self, *args, **kwargs)

    call.__name__ = name
    return call


for _name in _STATE_CALLS:
    if hasattr(sqlite3.Connection, _name):
        setattr(_KeptAfterDml, _name, _marks_state(_name))
del _name


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
    return any(now is not original and now != original for now, original in zip(current, _PRODUCTION_OPEN, strict=True))


class _Reused(_db_connection._ReusedConnection):
    __slots__ = ("__weakref__",)

    def close(self):
        if not self._released:
            self._connection.close_cursors()
        super().close()

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
        while idle and idle[-1]._state_changed:  # changed on a kept raw handle while it was idle
            idle.pop().close()
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
        proxy = _Reused(raw, self, key)
        raw._proxy = weakref.ref(proxy)
        return proxy

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

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
import sqlite3
import threading
from functools import cache
from pathlib import Path
from typing import Any
import weakref

# WAL itself needs SQLite 3.7.0.  A read-only connection can open a WAL
# database whose ``-shm`` it cannot write, or that has no ``-shm`` yet in a
# directory it can write, only from 3.22.0; the read-only doctor,
# data-quality and usage paths depend on that.
MINIMUM_SQLITE_VERSION = (3, 22, 0)
BUSY_TIMEOUT_MS = 5000

# The WAL-reset bug (https://www.sqlite.org/wal.html#walresetbug) can leave
# part of a committed transaction out of the database file when two
# connections write or checkpoint at the same instant.  It is present from
# 3.7.0 through 3.51.2 and fixed in 3.51.3; the fix is backported to 3.50.7
# and 3.44.6.  Each entry is the first fixed release of its line; ``None`` as
# the line means every later line.
WAL_RESET_FIX_RELEASES: tuple[tuple[tuple[int, int] | None, tuple[int, int, int]], ...] = (
    ((3, 44), (3, 44, 6)),
    ((3, 50), (3, 50, 7)),
    (None, (3, 51, 3)),
)
WAL_RESET_FIXED_VERSIONS_TEXT = "3.51.3 or newer, 3.50.7 or a later 3.50 release, or 3.44.6 or a later 3.44 release"
WAL_RESET_ADVISORY_URL = "https://www.sqlite.org/wal.html#walresetbug"

# SQLite reports these when a read-only connection cannot create the ``-shm``
# and ``-wal`` files a WAL database needs.
_READ_ONLY_OPEN_FAILURES = frozenset({"SQLITE_READONLY_DIRECTORY", "SQLITE_CANTOPEN"})


class UnsupportedSQLiteVersion(RuntimeError):
    """The SQLite library linked into Python is too old for WAL vaults."""


@cache
def require_supported_sqlite() -> None:
    """Fail once, clearly, when the runtime SQLite cannot open WAL vaults."""

    if sqlite3.sqlite_version_info < MINIMUM_SQLITE_VERSION:
        required = ".".join(str(part) for part in MINIMUM_SQLITE_VERSION)
        raise UnsupportedSQLiteVersion(
            f"LearnLoop needs SQLite {required} or newer to open WAL-mode vault "
            f"databases; this Python links SQLite {sqlite3.sqlite_version}."
        )


def linked_sqlite_version() -> tuple[int, int, int]:
    return tuple(sqlite3.sqlite_version_info)[:3]  # type: ignore[return-value]


def wal_reset_bug_fixed(version: tuple[int, int, int] | None = None) -> bool:
    """Whether ``version`` (default: the linked SQLite) has the WAL-reset fix."""

    version = tuple(version or linked_sqlite_version())[:3]
    for release_line, first_fixed in WAL_RESET_FIX_RELEASES:
        if release_line is None:
            if version >= first_fixed:
                return True
        elif version[:2] == release_line and version >= first_fixed:
            return True
    return False


def wal_unavailable_reason(version: tuple[int, int, int] | None = None) -> str | None:
    """Why WAL must not be enabled with ``version``, or ``None`` when it may be."""

    version = tuple(version or linked_sqlite_version())[:3]
    if wal_reset_bug_fixed(version):
        return None
    linked = ".".join(str(part) for part in version)
    return (
        f"the linked SQLite {linked} has the WAL-reset bug ({WAL_RESET_ADVISORY_URL}), "
        f"fixed in {WAL_RESET_FIXED_VERSIONS_TEXT}. uv-managed Python builds bundle "
        "their own SQLite: run `uv python install <latest patch of the pinned minor>`, "
        "`uv python pin <that version>` if the pin names a patch, and `uv sync`, or "
        "use a system Python that links a fixed SQLite"
    )


def connect(sqlite_path: Path, *, read_only: bool = False) -> sqlite3.Connection:
    """Open a configured SQLite connection.

    Read-only callers use SQLite's URI mode so opening a missing database fails
    instead of creating it.  This is intentionally a connection property rather
    than a repository convention: it makes accidental writes from diagnostic
    code fail at the database boundary.

    The journal mode is persistent in the database header and is set once by
    the migration path (:func:`learnloop.db.migrate.switch_to_wal`), so this
    function never changes it and works on WAL and rollback databases alike.  Writable connections set ``synchronous=FULL``
    explicitly: in WAL mode every commit is then fsynced before it is
    acknowledged, which ``NORMAL`` would give up for the most recent commits on
    power loss.
    """

    require_supported_sqlite()
    sqlite_path = Path(sqlite_path)
    pool = _REUSED.get()
    if pool is not None and pool.thread == threading.get_ident():
        reused = pool.connect(sqlite_path, read_only=read_only)
        if reused is not None:
            return reused  # type: ignore[return-value]
    if read_only:
        from learnloop.db.scopes import apply_connection_hook

        return apply_connection_hook(_open_read_only(sqlite_path), sqlite_path)
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    connection = _open_writable(sqlite_path)
    from learnloop.db.scopes import guarded_connection

    return guarded_connection(connection, sqlite_path)


def _open_writable(sqlite_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(sqlite_path)
    _configure(connection)
    connection.execute("PRAGMA synchronous = FULL")
    return connection


# -- Router speed stage 2, item 4: connections reused within one objective job -------------------------------------

#: The open scope's pool (:func:`reused_connections`); None outside one.
_REUSED: ContextVar["_ConnectionPool | None"] = ContextVar("learnloop_reused_connections", default=None)


@contextmanager
def reused_connections() -> Iterator[None]:
    """Router speed stage 2, item 4: inside, every :func:`connect` made **on the thread that opened the scope** hands
    out a connection of this scope's pool instead of opening one (SQLite parses the whole schema at a connection's
    first statement: about 2 ms here, hundreds of times in one objective job). Other threads (the job's model calls,
    which copy its context) open their own as before, so no connection ever crosses a thread.

    A connection given back (``close()``, or the end of a repository's ``with`` block, which closes it) is returned
    exactly as a fresh one would be next: its cursors closed (their statements finalized, so no read snapshot
    outlives its user), any transaction its user left open rolled back (as closing discards it: no write lock is
    ever kept), the AD guard's authorizer and trace hook removed (the next user's operation installs its own, through
    the connection hook, as at an open) and its settings restored (row factory, isolation level, ``foreign_keys``,
    ``busy_timeout``, and ``synchronous = FULL`` for a writable one). Each user holds its own: a connection in use is
    never handed out again until given back. An ingest job's guarded connections are never pooled. Every idle
    connection is closed when the scope ends. Nothing a reader computes changes: each statement reads what a fresh
    connection would."""

    pool = _ConnectionPool()
    token = _REUSED.set(pool)
    try:
        yield
    finally:
        _REUSED.reset(token)
        pool.close()


class _ConnectionPool:
    """One scope's idle connections, by database and mode, for its own thread only."""

    def __init__(self) -> None:
        self.thread = threading.get_ident()
        self.idle: dict[tuple[str, bool], list[sqlite3.Connection]] = {}
        self.opened = 0
        self.handed = 0
        self.closed = False

    def connect(self, sqlite_path: Path, *, read_only: bool) -> "_ReusedConnection | None":
        from learnloop.db.scopes import apply_connection_hook, current_ingest_job_id

        if self.closed or (not read_only and current_ingest_job_id(sqlite_path) is not None):
            return None  # an ingest job's writes are fenced by its own guarded connection
        key = (str(sqlite_path.resolve()), bool(read_only))
        idle = self.idle.get(key)
        if idle:
            raw = idle.pop()
        else:
            if read_only:
                raw = _open_read_only(sqlite_path)
            else:
                sqlite_path.parent.mkdir(parents=True, exist_ok=True)
                raw = _open_writable(sqlite_path)
            self.opened += 1
        self.handed += 1
        # As at an open: no authorizer but the current operation's (installed by the hook, which expires every
        # statement prepared before, so nothing prepared outside it runs unchecked inside it).
        raw.set_authorizer(None)
        raw.set_trace_callback(None)
        apply_connection_hook(raw, sqlite_path)
        return _ReusedConnection(raw, self, key)

    def give(self, key: tuple[str, bool], raw: sqlite3.Connection) -> None:
        if self.closed or self.thread != threading.get_ident():
            raw.close()
            return
        self.idle.setdefault(key, []).append(raw)

    def close(self) -> None:
        self.closed = True
        for connections in self.idle.values():
            for raw in connections:
                try:
                    raw.close()
                except sqlite3.Error:  # pragma: no cover - closing never fails the scope
                    pass
        self.idle.clear()


class _ReusedConnection:
    """A pooled connection as its user sees it: a raw connection's methods, whose ``close()`` gives it back to the
    pool reset (:func:`reused_connections`). The cursors it hands out are tracked so that giving it back finalizes
    them, as closing a connection does."""

    __slots__ = ("_connection", "_pool", "_key", "_cursors", "_released")

    def __init__(self, connection: sqlite3.Connection, pool: _ConnectionPool, key: tuple[str, bool]) -> None:
        object.__setattr__(self, "_connection", connection)
        object.__setattr__(self, "_pool", pool)
        object.__setattr__(self, "_key", key)
        object.__setattr__(self, "_cursors", weakref.WeakSet())
        object.__setattr__(self, "_released", False)

    def _raw(self) -> sqlite3.Connection:
        if self._released:
            raise sqlite3.ProgrammingError("Cannot operate on a closed database.")
        return self._connection

    def __getattr__(self, name: str) -> Any:
        return getattr(self._raw(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(self._raw(), name, value)

    def _track(self, cursor: sqlite3.Cursor) -> sqlite3.Cursor:
        self._cursors.add(cursor)
        return cursor

    def cursor(self, *args: Any, **kwargs: Any) -> sqlite3.Cursor:
        return self._track(self._raw().cursor(*args, **kwargs))

    def execute(self, sql: str, parameters: Any = ()) -> sqlite3.Cursor:
        return self._track(self._raw().execute(sql, parameters))

    def executemany(self, sql: str, parameters: Any) -> sqlite3.Cursor:
        return self._track(self._raw().executemany(sql, parameters))

    def executescript(self, script: str) -> sqlite3.Cursor:
        return self._track(self._raw().executescript(script))

    def __enter__(self) -> "_ReusedConnection":
        self._raw().__enter__()
        return self

    def __exit__(self, *exc: Any) -> Any:
        return self._raw().__exit__(*exc)

    def close(self) -> None:
        if self._released:
            return
        object.__setattr__(self, "_released", True)
        raw = self._connection
        try:
            for cursor in list(self._cursors):
                cursor.close()
            if raw.in_transaction:
                raw.rollback()  # what closing does to a transaction its user left open
            raw.set_authorizer(None)
            raw.set_trace_callback(None)
            raw.isolation_level = ""
            raw.row_factory = sqlite3.Row
            raw.text_factory = str
            _configure(raw)
            if not self._key[1]:
                raw.execute("PRAGMA synchronous = FULL")
        except sqlite3.Error:
            raw.close()  # anything that cannot be reset is closed, never handed out again
            return
        self._pool.give(self._key, raw)


def _configure(connection: sqlite3.Connection) -> None:
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")


def _open_read_only(sqlite_path: Path) -> sqlite3.Connection:
    """Open with ``mode=ro`` and surface a WAL open failure here.

    A WAL database opens its ``-wal`` and ``-shm`` lazily on the first read.
    Since SQLite 3.22.0 a read-only connection works when those files exist or
    can be created; in a directory the process cannot write, with no ``-shm``
    yet, the first read fails, and the probe below turns that into a message
    that says what to do.  ``immutable=1`` is never used: it is correct only
    if no process at all can change the file, which this process cannot
    establish from its own permissions.
    """

    uri = sqlite_path.resolve().as_uri()
    connection = sqlite3.connect(f"{uri}?mode=ro", uri=True)
    _configure(connection)
    try:
        connection.execute("SELECT 1 FROM sqlite_master LIMIT 1").fetchone()
    except sqlite3.OperationalError as error:
        connection.close()
        if getattr(error, "sqlite_errorname", None) not in _READ_ONLY_OPEN_FAILURES:
            raise
        raise sqlite3.OperationalError(
            f"cannot open {sqlite_path} read-only: it is a WAL database and SQLite "
            f"must create {sqlite_path.name}-shm beside it, but the directory "
            f"{sqlite_path.parent} does not allow creating files ({error}). Allow "
            "creating files in the vault directory, or make a consistent copy with "
            "LearnLoop's backup copier (learnloop.db.copies.backup_database) from an "
            "account that can, and open the copy."
        ) from error
    return connection

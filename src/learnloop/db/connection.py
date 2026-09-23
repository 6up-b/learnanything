from __future__ import annotations

import os
import sqlite3
from functools import cache
from pathlib import Path

# WAL itself needs SQLite 3.7.0.  A read-only connection can open a WAL
# database whose ``-shm`` it cannot create or write only from 3.22.0, and the
# read-only doctor, data-quality and usage paths depend on that for vaults on
# read-only media or in permission-restricted directories.
MINIMUM_SQLITE_VERSION = (3, 22, 0)
BUSY_TIMEOUT_MS = 5000

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


def connect(sqlite_path: Path, *, read_only: bool = False) -> sqlite3.Connection:
    """Open a configured SQLite connection.

    Read-only callers use SQLite's URI mode so opening a missing database fails
    instead of creating it.  This is intentionally a connection property rather
    than a repository convention: it makes accidental writes from diagnostic
    code fail at the database boundary.

    The journal mode is persistent in the database header and is set once by
    the migration path (:func:`learnloop.db.migrate.switch_to_wal`), so this
    function never changes it.  Writable connections set ``synchronous=FULL``
    explicitly: in WAL mode every commit is then fsynced before it is
    acknowledged, which ``NORMAL`` would give up for the most recent commits on
    power loss.
    """

    require_supported_sqlite()
    sqlite_path = Path(sqlite_path)
    if read_only:
        return _open_read_only(sqlite_path)
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(sqlite_path)
    _configure(connection)
    connection.execute("PRAGMA synchronous = FULL")
    from learnloop.db.scopes import guarded_connection

    return guarded_connection(connection, sqlite_path)


def _configure(connection: sqlite3.Connection) -> None:
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")


def _open_read_only(sqlite_path: Path) -> sqlite3.Connection:
    """Open ``mode=ro``, falling back to ``immutable=1`` only when that is exact.

    A WAL database opens its ``-wal`` and ``-shm`` lazily on the first read, so
    a directory the process cannot write fails there rather than in
    ``sqlite3.connect``; the probe read below surfaces it.  ``immutable=1``
    skips locking and the WAL entirely, which is correct only when the database
    cannot change and has no committed pages outside the main file: the
    directory is not writable (so no writer can create a ``-wal`` or rollback
    journal beside it) and no non-empty ``-wal`` exists.
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
        if not _directory_is_read_only(sqlite_path):
            raise
        if _has_uncheckpointed_wal(sqlite_path):
            raise sqlite3.OperationalError(
                f"{sqlite_path} has committed changes in its -wal file but its "
                "directory is read-only, so SQLite cannot build the shared WAL "
                "index to read them; open it from a writable copy"
            ) from error
        immutable = sqlite3.connect(f"{uri}?mode=ro&immutable=1", uri=True)
        _configure(immutable)
        return immutable
    return connection


def _directory_is_read_only(sqlite_path: Path) -> bool:
    return not os.access(sqlite_path.resolve().parent, os.W_OK)


def _has_uncheckpointed_wal(sqlite_path: Path) -> bool:
    wal_path = sqlite_path.with_name(sqlite_path.name + "-wal")
    try:
        return wal_path.stat().st_size > 0
    except FileNotFoundError:
        return False

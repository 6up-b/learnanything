from __future__ import annotations

import sqlite3
from functools import cache
from pathlib import Path

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

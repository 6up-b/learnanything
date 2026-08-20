from __future__ import annotations

import sqlite3
from pathlib import Path


def connect(sqlite_path: Path, *, read_only: bool = False) -> sqlite3.Connection:
    """Open a configured SQLite connection.

    Read-only callers use SQLite's URI mode so opening a missing database fails
    instead of creating it.  This is intentionally a connection property rather
    than a repository convention: it makes accidental writes from diagnostic
    code fail at the database boundary.
    """

    sqlite_path = Path(sqlite_path)
    if read_only:
        uri = f"{sqlite_path.resolve().as_uri()}?mode=ro"
        connection = sqlite3.connect(uri, uri=True)
    else:
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(sqlite_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection

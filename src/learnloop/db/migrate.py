from __future__ import annotations

import os
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.connection import connect

_MIGRATION_RE = re.compile(r"^(?P<version>\d+)_(?P<name>.+)\.sql$")
_FOREIGN_KEYS_OFF_RE = re.compile(
    r"^\s*PRAGMA\s+foreign_keys\s*=\s*OFF\s*;?\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# SQLite files that belong to a database named ``<name>``.  Beside a missing
# database they are orphans, and SQLite would replay an orphaned ``-wal`` or
# hot ``-journal`` into a new database created under the same name.
_COMPANION_SUFFIXES = ("-wal", "-shm", "-journal")


class JournalModeSwitchError(RuntimeError):
    """The database could not be moved to WAL, so its journal mode is unchanged."""


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    path: Path


def default_migrations_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "migrations"


def discover_migrations(migrations_dir: Path | None = None) -> list[Migration]:
    root = migrations_dir or default_migrations_dir()
    migrations: list[Migration] = []
    for path in sorted(root.glob("*.sql")):
        match = _MIGRATION_RE.match(path.name)
        if not match:
            continue
        migrations.append(Migration(int(match.group("version")), match.group("name"), path))
    return migrations


def applied_versions(sqlite_path: Path) -> set[int]:
    sqlite_path = Path(sqlite_path)
    if not sqlite_path.exists():
        return set()
    with closing(connect(sqlite_path, read_only=True)) as connection:
        exists = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'schema_migrations'"
        ).fetchone()
        if not exists:
            return set()
        return {int(row["version"]) for row in connection.execute("SELECT version FROM schema_migrations")}


def apply_migrations(
    sqlite_path: Path,
    migrations_dir: Path | None = None,
    clock: Clock | None = None,
) -> list[Migration]:
    sqlite_path = Path(sqlite_path)
    migrations = discover_migrations(migrations_dir)
    if not sqlite_path.exists():
        return _apply_fresh(sqlite_path, migrations, clock)
    already_applied = applied_versions(sqlite_path)
    applied: list[Migration] = []
    # Closed explicitly: an open WAL connection holds the database open, and a
    # later exclusive operation in this process must not wait for the garbage
    # collector to release it.
    with closing(connect(sqlite_path)) as connection:
        switch_to_wal(connection, sqlite_path)
        for migration in migrations:
            if migration.version in already_applied:
                continue
            if _apply_incremental_migration(connection, migration, clock):
                applied.append(migration)
    return applied


def switch_to_wal(connection: sqlite3.Connection, sqlite_path: Path) -> None:
    """Move a database to WAL journal mode once; a no-op when it is already WAL.

    The journal mode lives in the database header, so this is a one-way upgrade
    of the file rather than a connection setting.  Leaving a rollback journal
    needs an exclusive lock: an idle connection elsewhere does not prevent it,
    but one holding a read or write transaction does, and SQLite then reports
    "database is locked" after the busy timeout.  Either failure raises with
    the header unchanged, so the file is never left in an ambiguous mode.
    """

    current = str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower()
    if current == "wal":
        return
    if connection.in_transaction:
        raise JournalModeSwitchError(
            f"cannot switch {sqlite_path} to WAL inside an open transaction"
        )
    try:
        reported = str(connection.execute("PRAGMA journal_mode = WAL").fetchone()[0]).lower()
    except sqlite3.OperationalError as error:
        raise JournalModeSwitchError(
            f"could not switch {sqlite_path} from {current} to WAL journal mode: "
            f"another connection holds a transaction on it ({error}). Close other "
            "LearnLoop processes using this vault and retry."
        ) from error
    if reported != "wal":
        raise JournalModeSwitchError(
            f"SQLite kept {sqlite_path} in {reported} journal mode; WAL needs a "
            "local filesystem with shared-memory support"
        )


def _apply_incremental_migration(
    connection: sqlite3.Connection,
    migration: Migration,
    clock: Clock | None,
) -> bool:
    """Apply one existing-database migration as one durable transaction.

    ``sqlite3.Connection.executescript`` commits any active transaction before
    executing its input, so an outer ``BEGIN`` does not make it atomic.  Execute
    complete SQLite statements individually instead.  Trigger bodies remain one
    statement because :func:`sqlite3.complete_statement` understands their
    internal semicolons.

    Table-rebuild migrations disable foreign-key enforcement.  The pragma must
    take effect before ``BEGIN``; the matching in-script pragmas then harmlessly
    no-op inside the transaction.  An explicit integrity check runs before the
    migration and its ledger receipt commit together.
    """

    sql = migration.path.read_text(encoding="utf-8")
    foreign_keys_off = bool(_FOREIGN_KEYS_OFF_RE.search(sql))
    if connection.in_transaction:
        raise RuntimeError("incremental migration requires an idle connection")
    if foreign_keys_off:
        connection.execute("PRAGMA foreign_keys = OFF")
        if int(connection.execute("PRAGMA foreign_keys").fetchone()[0]) != 0:
            raise RuntimeError(
                f"migration {migration.version} requires foreign_keys=OFF before BEGIN"
            )
    try:
        connection.execute("BEGIN IMMEDIATE")
        if _migration_is_applied(connection, migration.version):
            connection.rollback()
            return False
        for statement in _iter_sql_statements(sql):
            connection.execute(statement)
        if foreign_keys_off:
            violations = connection.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                detail = ", ".join(
                    f"{row[0]} rowid={row[1]} parent={row[2]} fk={row[3]}"
                    for row in violations[:10]
                )
                raise RuntimeError(
                    f"migration {migration.version} failed foreign_key_check: {detail}"
                )
        connection.execute(
            "INSERT INTO schema_migrations(version, name, applied_at) VALUES (?, ?, ?)",
            (migration.version, migration.name, utc_now_iso(clock)),
        )
        connection.commit()
        return True
    except BaseException:
        if connection.in_transaction:
            connection.rollback()
        raise
    finally:
        if foreign_keys_off:
            connection.execute("PRAGMA foreign_keys = ON")
            if int(connection.execute("PRAGMA foreign_keys").fetchone()[0]) != 1:
                raise RuntimeError(
                    f"migration {migration.version} did not restore foreign_keys=ON"
                )


def _migration_is_applied(connection: sqlite3.Connection, version: int) -> bool:
    ledger_exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'schema_migrations'"
    ).fetchone()
    if ledger_exists is None:
        return False
    return (
        connection.execute(
            "SELECT 1 FROM schema_migrations WHERE version = ?",
            (version,),
        ).fetchone()
        is not None
    )


def _iter_sql_statements(sql: str) -> Iterator[str]:
    """Yield executable statements without splitting trigger bodies."""

    buffer: list[str] = []
    for character in sql:
        buffer.append(character)
        if character != ";":
            continue
        candidate = "".join(buffer)
        if not sqlite3.complete_statement(candidate):
            continue
        if candidate.strip():
            yield candidate
        buffer.clear()
    trailing = "".join(buffer).strip()
    if trailing:
        yield trailing


def _apply_fresh(sqlite_path: Path, migrations: list[Migration], clock: Clock | None) -> list[Migration]:
    """Create a brand-new database with every migration, fast and atomically.

    ``executescript`` autocommits statement groups, so building a fresh schema
    the durable way pays a journal write and an fsync per migration.  On
    Windows, where fsync is slow and on-access antivirus scans every file
    operation, that made each vault creation take about 17 s against 0.3 s on
    Linux.  A fresh database needs none of that durability: it is built under
    a temporary name with the journal in memory and syncing off, and a crash
    mid-creation leaves only a ``.tmp`` that the next attempt replaces.

    The finished build is switched to WAL on the same connection and that
    connection is closed before the rename.  Closing the only connection of a
    WAL database checkpoints it and deletes its ``-wal`` and ``-shm``, so the
    renamed file is a complete WAL-mode database with no companion files and
    there is no moment at which a WAL header and a ``-wal`` from different
    files sit side by side.  The file is fsynced once and renamed into place.
    """

    tmp_path = sqlite_path.with_name(sqlite_path.name + ".tmp")
    _remove_companion_files(tmp_path, include_database=True)
    applied: list[Migration] = []
    connection = connect(tmp_path)
    try:
        connection.execute("PRAGMA journal_mode=MEMORY")
        connection.execute("PRAGMA synchronous=OFF")
        for migration in migrations:
            connection.executescript(migration.path.read_text(encoding="utf-8"))
            connection.execute(
                "INSERT INTO schema_migrations(version, name, applied_at) VALUES (?, ?, ?)",
                (migration.version, migration.name, utc_now_iso(clock)),
            )
            applied.append(migration)
        connection.commit()
        switch_to_wal(connection, tmp_path)
    finally:
        connection.close()
    live_companions = _existing_companion_files(tmp_path)
    if live_companions:
        names = ", ".join(path.name for path in live_companions)
        raise RuntimeError(f"fresh database {tmp_path} still has companion files after close: {names}")
    with open(tmp_path, "rb+") as handle:
        os.fsync(handle.fileno())
    _remove_companion_files(sqlite_path, include_database=False)
    tmp_path.replace(sqlite_path)
    return applied


def _existing_companion_files(sqlite_path: Path) -> list[Path]:
    candidates = (sqlite_path.with_name(sqlite_path.name + suffix) for suffix in _COMPANION_SUFFIXES)
    return [path for path in candidates if path.exists()]


def _remove_companion_files(sqlite_path: Path, *, include_database: bool) -> None:
    """Delete companions of a database that does not exist (or is being replaced)."""

    if include_database and sqlite_path.exists():
        sqlite_path.unlink()
    for companion in _existing_companion_files(sqlite_path):
        companion.unlink()

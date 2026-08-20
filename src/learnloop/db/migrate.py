from __future__ import annotations

import os
import re
import sqlite3
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
    with connect(sqlite_path, read_only=True) as connection:
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
    with connect(sqlite_path) as connection:
        for migration in migrations:
            if migration.version in already_applied:
                continue
            if _apply_incremental_migration(connection, migration, clock):
                applied.append(migration)
    return applied


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
    the durable way pays a rollback-journal create/delete plus an fsync per
    migration — on Windows (where fsync is slow and on-access antivirus scans
    every file operation) that made each vault creation take ~17s vs ~0.3s on
    Linux. A FRESH database needs none of that durability: build it under a
    temp name with the journal in memory and syncing off, fsync the finished
    file once, and atomically rename into place. Existing databases (real
    vault upgrades) keep the fully durable incremental path above; a crash
    mid-creation leaves only a ``.tmp`` that the next attempt replaces."""

    tmp_path = sqlite_path.with_name(sqlite_path.name + ".tmp")
    if tmp_path.exists():
        tmp_path.unlink()
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
    finally:
        connection.close()
    with open(tmp_path, "rb+") as handle:
        os.fsync(handle.fileno())
    tmp_path.replace(sqlite_path)
    return applied

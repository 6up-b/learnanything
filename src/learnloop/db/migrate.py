from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.connection import connect

_MIGRATION_RE = re.compile(r"^(?P<version>\d+)_(?P<name>.+)\.sql$")


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
    if not sqlite_path.exists():
        return set()
    with connect(sqlite_path) as connection:
        exists = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'schema_migrations'"
        ).fetchone()
        if not exists:
            return set()
        return {int(row["version"]) for row in connection.execute("SELECT version FROM schema_migrations")}


def apply_migrations(sqlite_path: Path, migrations_dir: Path | None = None, clock: Clock | None = None) -> list[Migration]:
    migrations = discover_migrations(migrations_dir)
    if not sqlite_path.exists():
        return _apply_fresh(sqlite_path, migrations, clock)
    already_applied = applied_versions(sqlite_path)
    applied: list[Migration] = []
    with connect(sqlite_path) as connection:
        for migration in migrations:
            if migration.version in already_applied:
                continue
            sql = migration.path.read_text(encoding="utf-8")
            connection.executescript(sql)
            connection.execute(
                "INSERT INTO schema_migrations(version, name, applied_at) VALUES (?, ?, ?)",
                (migration.version, migration.name, utc_now_iso(clock)),
            )
            applied.append(migration)
        connection.commit()
    return applied


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

from __future__ import annotations

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

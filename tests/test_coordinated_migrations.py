"""Only the vault's migration coordinator upgrades a vault's database
(docs/reviews/exam-protection-identity.md, "F3 final").

Upgrading a vault has a vault-level step: under the vault mutation lock,
``learnloop.migration_coordinator.migrate_vault`` applies the migrations and
then records the held-out signals the vault's exam membership qualifies
(migration 204). A bare ``Repository(path)`` knows no vault, so it creates a
database or attaches to a current one and refuses to upgrade one. Entry points
open the vault with ``open_vault_repository``; code below them that has the
vault uses ``vault_repository``, which goes through the coordinator whenever an
upgrade is due. The guard below pins that nothing else in ``src/`` or
``scripts/`` constructs a ``Repository`` or upgrades a database.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest

from learnloop.db.migrate import (
    UncoordinatedMigrationError,
    apply_migrations,
    applied_versions,
    discover_migrations,
)
from learnloop.db.repositories import Repository

from tests.helpers import create_basic_vault

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCANNED = [_REPO_ROOT / "src", _REPO_ROOT / "scripts"]

#: The one module that constructs ``Repository(path)``: ``vault_repository``
#: attaches a current vault database with it.
_CONSTRUCTS_REPOSITORY = {"src/learnloop/vault/repository.py"}
#: The callers of ``apply_migrations`` (the upgrade itself), each with why.
_UPGRADES_A_DATABASE = {
    # The vault's coordinator: applies, then records what the vault qualifies, under the lock.
    "src/learnloop/migration_coordinator.py",
    # A scratch copy of the vault's database that an offline review reads; never the vault.
    "src/learnloop/diagnosis/offline_review/runner.py",
}


def _python_files() -> list[Path]:
    return sorted(path for root in _SCANNED for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def _called_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _scan(names: set[str]) -> dict[str, list[str]]:
    """Every call of a function named in ``names``, by file (relative to the
    repository), plus any import that renames one of them."""

    found: dict[str, list[str]] = {}
    for path in _python_files():
        relative = path.relative_to(_REPO_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _called_name(node) in names:
                found.setdefault(relative, []).append(f"{_called_name(node)}() at line {node.lineno}")
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name in names and alias.asname not in (None, alias.name):
                        found.setdefault(relative, []).append(f"{alias.name} imported as {alias.asname}")
    return found


def test_only_the_vault_opener_constructs_a_repository():
    """Every vault-aware path in the CLI, the sidecar, the TUI, the mobile
    host, the library and the scripts opens its database through
    ``learnloop.vault.repository`` (or attaches without migrating:
    ``Repository.attach``). A new ``Repository(path)`` construction fails
    here: open the vault with ``open_vault_repository`` (an entry point) or
    ``vault_repository`` (code below one)."""

    found = _scan({"Repository"})
    assert set(found) <= _CONSTRUCTS_REPOSITORY, {
        path: calls for path, calls in found.items() if path not in _CONSTRUCTS_REPOSITORY}
    assert set(found) == _CONSTRUCTS_REPOSITORY, "the guard's allowlist names a module that no longer constructs one"


def test_only_the_coordinator_upgrades_a_vault_database():
    """``apply_migrations`` is called by the coordinator, and by an offline
    review on its own scratch copy; ``create_or_attach_current`` (which
    refuses to upgrade) only by ``Repository``."""

    upgrades = _scan({"apply_migrations"})
    assert set(upgrades) == _UPGRADES_A_DATABASE, upgrades
    creates = _scan({"create_or_attach_current"})
    assert set(creates) == {"src/learnloop/db/repositories.py"}, creates


def _database_before_head(sqlite_path: Path) -> int:
    """Create a database at every migration but the newest (an older
    LearnLoop's); the migration it is at."""

    migrations = discover_migrations()
    older = sqlite_path.parent / "older_migrations"
    older.mkdir()
    for migration in migrations[:-1]:
        (older / migration.path.name).write_text(migration.path.read_text(encoding="utf-8"), encoding="utf-8")
    apply_migrations(sqlite_path, migrations_dir=older)
    return migrations[-2].version


@pytest.mark.durability  # under production pragmas (WAL, synchronous=FULL) too
def test_a_bare_repository_refuses_to_upgrade_and_leaves_the_database_as_it_was(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"
    current = _database_before_head(sqlite_path)
    before = hashlib.sha256(sqlite_path.read_bytes()).hexdigest()
    versions = applied_versions(sqlite_path)

    with pytest.raises(UncoordinatedMigrationError) as refused:
        Repository(sqlite_path)

    assert refused.value.current == current
    assert refused.value.pending == (discover_migrations()[-1].version,)
    assert "learnloop doctor --fix-state" in str(refused.value)
    assert applied_versions(sqlite_path) == versions
    assert hashlib.sha256(sqlite_path.read_bytes()).hexdigest() == before, "the database is unchanged"
    assert not sqlite_path.with_name(sqlite_path.name + "-wal").exists() or not sqlite_path.with_name(
        sqlite_path.name + "-wal").stat().st_size


def test_a_bare_repository_still_creates_a_database_and_attaches_a_current_one(tmp_path):
    """Creating a database upgrades nothing (no vault data to qualify), and a
    current database is attached as before: tests and path-only tools keep
    working."""

    head = {migration.version for migration in discover_migrations()}
    sqlite_path = tmp_path / "new.sqlite"
    Repository(sqlite_path)
    assert applied_versions(sqlite_path) == head
    Repository(sqlite_path).practice_item_states()
    assert applied_versions(sqlite_path) == head


def test_vault_repository_attaches_a_current_vault_without_the_coordinator(tmp_path, monkeypatch):
    """No behaviour change for a vault upgraded normally: below an entry point,
    a current database is attached without the vault lock or a record."""

    import learnloop.vault.repository as vault_repository_module
    from learnloop.vault.repository import vault_repository

    paths = create_basic_vault(tmp_path / "vault")

    def coordinated(*_args, **_kwargs):
        raise AssertionError("a current vault database was opened through the coordinator")

    monkeypatch.setattr(vault_repository_module, "migrate_vault", coordinated)
    repository = vault_repository(paths)
    assert repository.sqlite_path == paths.sqlite_path
    assert applied_versions(paths.sqlite_path) == {migration.version for migration in discover_migrations()}


def test_vault_repository_upgrades_a_vault_that_is_behind_through_the_coordinator(tmp_path, monkeypatch):
    """Below an entry point, a vault database an older LearnLoop left behind
    is upgraded by the coordinator (under the lock, with its record), never
    by a bare construction."""

    import learnloop.vault.repository as vault_repository_module
    from learnloop.vault.repository import vault_repository

    paths = create_basic_vault(tmp_path / "vault")
    for path in (paths.sqlite_path, *(paths.sqlite_path.with_name(paths.sqlite_path.name + suffix)
                                      for suffix in ("-wal", "-shm", "-journal"))):
        path.unlink(missing_ok=True)
    _database_before_head(paths.sqlite_path)  # the database an older LearnLoop left
    newest = discover_migrations()[-1]

    calls: list[tuple[Path, Path]] = []
    coordinator = vault_repository_module.migrate_vault

    def spy(vault_root, sqlite_path, **kwargs):
        calls.append((Path(vault_root), Path(sqlite_path)))
        return coordinator(vault_root, sqlite_path, **kwargs)

    monkeypatch.setattr(vault_repository_module, "migrate_vault", spy)
    vault_repository(paths)
    assert calls == [(paths.root, paths.sqlite_path)]
    assert newest.version in applied_versions(paths.sqlite_path)

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
import sqlite3
from contextlib import closing
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
from tests.test_reread_safety import exam_book  # noqa: F401 -- a fixture

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


# --- F8: the rule enforced at run time ----------------------------------------------------
#
# Codex verify of the coordinated-migration rule, F8 [Medium]: the source scan
# above misses indirect calls (an assignment alias, getattr, a wrapper, a
# subclass). So the upgrade itself refuses unless it runs under a named
# allowance (``db.migrate.upgrade_allowance``): the coordinator's, an offline
# review's scratch copy, or the test suite's fixture. The scan stays as the
# fast check, and pins who enters which allowance.

#: The modules that enter each allowance, by the allowance's constant name.
_ENTERS_AN_ALLOWANCE = {
    "UPGRADE_BY_COORDINATOR": {"src/learnloop/migration_coordinator.py"},
    "UPGRADE_SCRATCH_COPY": {"src/learnloop/diagnosis/offline_review/runner.py"},
}
_ALLOWANCE_NAMES = {"upgrade_allowance", "UPGRADE_BY_COORDINATOR", "UPGRADE_SCRATCH_COPY", "UPGRADE_TEST_HELPER",
                    "_UPGRADE_AUTHORITY", "_CREATING"}


def _sealed(sqlite_path: Path) -> tuple[str, int]:
    """The database file's hash and its ``-wal`` size (0 when absent)."""

    wal = sqlite_path.with_name(sqlite_path.name + "-wal")
    return hashlib.sha256(sqlite_path.read_bytes()).hexdigest(), wal.stat().st_size if wal.exists() else 0


def _references(names: set[str]) -> dict[str, list[str]]:
    """Every reference to one of ``names`` (a name, an attribute, an import or
    a string constant) in ``src/`` and ``scripts/``, by file."""

    found: dict[str, list[str]] = {}
    for path in _python_files():
        relative = path.relative_to(_REPO_ROOT).as_posix()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=relative)):
            if isinstance(node, ast.Name) and node.id in names:
                found.setdefault(relative, []).append(node.id)
            elif isinstance(node, ast.Attribute) and node.attr in names:
                found.setdefault(relative, []).append(node.attr)
            elif isinstance(node, ast.alias) and node.name in names:
                found.setdefault(relative, []).append(node.name)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in names:
                found.setdefault(relative, []).append(repr(node.value))
    return found


def test_f8_only_the_coordinator_and_the_scratch_copy_enter_an_allowance():
    """Who may upgrade, pinned by name: the coordinator enters its allowance,
    the offline review its scratch-copy one, and nothing else in ``src/`` or
    ``scripts/`` names an allowance (or the test suite's) at all."""

    found = _references(_ALLOWANCE_NAMES)
    migrate = "src/learnloop/db/migrate.py"
    entrants = {path for path in found if path != migrate}
    assert entrants == set().union(*_ENTERS_AN_ALLOWANCE.values()), found
    for constant, modules in _ENTERS_AN_ALLOWANCE.items():
        for module in modules:
            assert constant in found[module] and "upgrade_allowance" in found[module], (module, found[module])
            others = {name for name in found[module] if name.startswith("UPGRADE_")} - {constant}
            assert not others, (module, others)


def _alias(path: Path):
    upgrade = apply_migrations
    return upgrade(path)


def _getattr(path: Path):
    import learnloop.db.migrate as migrate_module

    return getattr(migrate_module, "apply_" + "migrations")(path)


def _partial(path: Path):
    import functools

    return functools.partial(apply_migrations, migrations_dir=None)(path)


def _wrapper(path: Path):
    def factory():
        return lambda target: apply_migrations(target)

    return factory()(path)


def _incremental_step(path: Path):
    import learnloop.db.migrate as migrate_module
    from learnloop.db.connection import connect

    step = migrate_module._apply_incremental_migration
    with closing(connect(path)) as connection:
        return step(connection, discover_migrations()[-1], None)


@pytest.mark.parametrize("route", [_alias, _getattr, _partial, _wrapper, _incremental_step],
                         ids=["assignment_alias", "getattr", "partial", "factory", "incremental_step"])
def test_f8_an_indirect_upgrade_outside_the_coordinator_raises_and_leaves_the_file_byte_identical(tmp_path, route):
    """The reproduction: ``upgrade = apply_migrations; upgrade(path)`` (and
    getattr, a partial, a factory's lambda, the private incremental step)
    outside every allowance raises, and the database file is byte-identical."""

    from learnloop.db.migrate import upgrade_authority

    sqlite_path = tmp_path / "state.sqlite"
    current = _database_before_head(sqlite_path)
    before, versions = _sealed(sqlite_path), applied_versions(sqlite_path)

    with pytest.raises(UncoordinatedMigrationError) as refused:
        route(sqlite_path)

    assert refused.value.current == current
    assert applied_versions(sqlite_path) == versions
    assert _sealed(sqlite_path) == (before[0], 0), "the database is byte-identical"
    assert upgrade_authority() is None


@pytest.mark.parametrize("route", ["assignment_alias", "getattr", "subclass"])
def test_f8_a_repository_reached_indirectly_never_upgrades(tmp_path, route):
    """``Repository(path)`` refuses at run time too, whatever name it is reached by."""

    import learnloop.db.repositories as repositories_module

    class Inherited(Repository):
        pass

    construct = {"assignment_alias": Repository, "getattr": getattr(repositories_module, "Repo" + "sitory"),
                 "subclass": Inherited}[route]
    sqlite_path = tmp_path / "state.sqlite"
    _database_before_head(sqlite_path)
    before = _sealed(sqlite_path)
    with pytest.raises(UncoordinatedMigrationError):
        construct(sqlite_path)
    assert _sealed(sqlite_path) == (before[0], 0)


def test_f8_creating_or_attaching_needs_no_allowance(tmp_path):
    """Creating a database (a missing file, or an existing one with no
    migration applied yet) is not an upgrade, and attaching a current one
    applies nothing: ``apply_migrations`` does both outside any allowance."""

    head = {migration.version for migration in discover_migrations()}
    created = tmp_path / "created.sqlite"
    assert {migration.version for migration in apply_migrations(created)} == head
    assert apply_migrations(created) == []
    empty = tmp_path / "empty.sqlite"
    with closing(sqlite3.connect(empty)) as connection:
        connection.execute("CREATE TABLE placeholder (id INTEGER)")
        connection.commit()
    assert {migration.version for migration in apply_migrations(empty)} == head


@pytest.mark.durability  # under production pragmas (WAL, synchronous=FULL) too
def test_f8_the_coordinator_upgrades_under_its_allowance_and_qualifies(exam_book):
    """The coordinator path: outside it the same upgrade is refused; through
    it the vault is upgraded under the coordinator's allowance and, under the
    same allowance and lock, the held-out signal its exam membership
    qualifies is recorded (``hos_q_``, ``made_as_role = 'exam'``). The
    allowance ends with the coordinator's step."""

    import learnloop.migration_coordinator as coordinator_module
    from learnloop.db.migrate import UPGRADE_BY_COORDINATOR, upgrade_authority
    from tests.test_exam_protection_identity import _EXAM_MEMBER, _older_build_with_membership

    repo, root = exam_book["repo"], exam_book["root"]
    _older_build_with_membership(exam_book, _EXAM_MEMBER)
    # The older build lacks the ledger's migration (204), not the newest one
    # (205, diagnosis input provenance, landed after it).
    newest = next(migration.version for migration in discover_migrations()
                  if migration.name == "source_held_out_signal_marks")
    sealed = _sealed(repo.sqlite_path)
    with pytest.raises(UncoordinatedMigrationError):
        _alias(repo.sqlite_path)
    assert _sealed(repo.sqlite_path)[0] == sealed[0]

    seen: dict[str, object] = {}
    record = coordinator_module.record_member_exam_signals

    def recording(*args, **kwargs):
        seen["record"] = (upgrade_authority(), newest in applied_versions(repo.sqlite_path))
        return record(*args, **kwargs)

    original = coordinator_module.record_member_exam_signals
    coordinator_module.record_member_exam_signals = recording
    try:
        applied = coordinator_module.migrate_vault(root, repo.sqlite_path)
    finally:
        coordinator_module.record_member_exam_signals = original
    assert [migration.version for migration in applied] == [newest]
    assert seen["record"] == (UPGRADE_BY_COORDINATOR, True)
    assert upgrade_authority() is None
    qualified = [row for row in repo.held_out_signal_marks() if str(row["id"]).startswith("hos_q_")]
    assert qualified and all(row["made_as_role"] == "exam" for row in qualified)


def test_f8_the_offline_reviews_scratch_copy_is_upgraded_under_its_own_allowance(tmp_path, monkeypatch):
    """An offline review brings its scratch copy of an older vault database to
    head under ``UPGRADE_SCRATCH_COPY``; the vault's own file is untouched."""

    from types import SimpleNamespace

    import learnloop.diagnosis.offline_review.runner as runner_module
    from learnloop.db.migrate import UPGRADE_SCRATCH_COPY, upgrade_authority

    older = tmp_path / "vault" / "state.sqlite"
    older.parent.mkdir()
    _database_before_tables(older, "judgment_ledger")
    sealed = _sealed(older)
    seen: list[str | None] = []
    real = runner_module.apply_migrations

    def spy(path, *args, **kwargs):
        seen.append(upgrade_authority())
        return real(path, *args, **kwargs)

    monkeypatch.setattr(runner_module, "apply_migrations", spy)
    run = runner_module.ReviewRun(SimpleNamespace(root=tmp_path / "vault"), tmp_path / "run",
                                  runner_module.ReviewOptions(), clients=None, spend=None)
    run.open(older)
    assert seen == [UPGRADE_SCRATCH_COPY]
    assert applied_versions(run.scratch_path) == {migration.version for migration in discover_migrations()}
    assert _sealed(older)[0] == sealed[0], "the vault's database is never upgraded by a review"
    assert upgrade_authority() is None


def _database_before_tables(sqlite_path: Path, table: str) -> int:
    """A database at every migration before the first that creates ``table``."""

    migrations = discover_migrations()
    first = next(index for index, migration in enumerate(migrations)
                 if f"CREATE TABLE {table}" in migration.path.read_text(encoding="utf-8"))
    older = sqlite_path.parent / f"before_{table}"
    older.mkdir()
    for migration in migrations[:first]:
        (older / migration.path.name).write_text(migration.path.read_text(encoding="utf-8"), encoding="utf-8")
    apply_migrations(sqlite_path, migrations_dir=older)
    return migrations[first - 1].version


def test_f8_the_test_suites_allowance_is_its_fixture(tmp_path, migration_upgrade_allowed):
    """The test suite's named allowance (``migration_upgrade_allowed``) lets a
    test upgrade an older database directly, and only while the test runs."""

    from learnloop.db.migrate import UPGRADE_TEST_HELPER, upgrade_authority

    assert upgrade_authority() == UPGRADE_TEST_HELPER
    sqlite_path = tmp_path / "state.sqlite"
    _database_before_head(sqlite_path)
    newest = discover_migrations()[-1].version
    assert [migration.version for migration in _alias(sqlite_path)] == [newest]


def test_f8_an_unknown_allowance_is_refused():
    from learnloop.db.migrate import upgrade_allowance

    with pytest.raises(ValueError, match="unknown migration upgrade allowance"):
        with upgrade_allowance("anything_else"):
            pass

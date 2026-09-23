import sqlite3
from pathlib import Path

from learnloop.db.repositories import Repository
from tests import helpers


def test_template_copies_have_independent_database_files_and_configuration(tmp_path):
    first = helpers.create_basic_vault(tmp_path / "first")
    second = helpers.create_basic_vault(tmp_path / "second")
    before = second.sqlite_path.read_bytes()
    with Repository(first.sqlite_path).connection() as connection:
        connection.execute("CREATE TABLE isolation_sentinel (value TEXT)")
        connection.commit()
    first.config.algorithms.algorithm_version = "mutated-test"
    assert second.sqlite_path.read_bytes() == before
    assert second.config.algorithms.algorithm_version != "mutated-test"
    assert helpers._BASIC_VAULT_TEMPLATE.config.algorithms.algorithm_version != "mutated-test"
    assert first.sqlite_path.stat().st_ino != second.sqlite_path.stat().st_ino


def test_explicit_fresh_construction_still_runs_initializer(tmp_path, monkeypatch):
    calls = []
    original = helpers.init_vault
    def initialize(*args, **kwargs):
        calls.append(args[0])
        return original(*args, **kwargs)
    monkeypatch.setattr(helpers, "init_vault", initialize)
    helpers.create_basic_vault(tmp_path / "fresh", fresh=True)
    assert calls == [tmp_path / "fresh"]


def _vault_files(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "state.sqlite"
    }


def _database_dump(sqlite_path: Path) -> list[str]:
    connection = sqlite3.connect(sqlite_path)
    try:
        # Migration bookkeeping stamps wall-clock time; blank it so the dump
        # compares schema and seeded rows only.
        connection.execute("UPDATE schema_migrations SET applied_at = ''")
        return list(connection.iterdump())
    finally:
        connection.close()


def test_template_copy_matches_a_fresh_build(tmp_path, monkeypatch):
    # Compare against a real copy even when the durability lane is active.
    monkeypatch.setattr(helpers, "_FRESH_VAULTS", False)
    copied = helpers.create_basic_vault(tmp_path / "copied")
    fresh = helpers.create_basic_vault(tmp_path / "fresh", fresh=True)

    assert _vault_files(copied.root) == _vault_files(fresh.root)
    assert _database_dump(copied.sqlite_path) == _database_dump(fresh.sqlite_path)
    assert copied.config == fresh.config

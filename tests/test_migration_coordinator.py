from __future__ import annotations

import multiprocessing
from pathlib import Path
from typing import Any

from learnloop.db.connection import connect
from learnloop.db.migrate import applied_versions
from learnloop.migration_coordinator import migrate_vault
from learnloop.ops.vault_lock import vault_lock_path, vault_mutation_lock
from learnloop.vault.repository import open_vault_repository


def _write_migrations(root: Path) -> Path:
    migrations_dir = root / "migrations"
    migrations_dir.mkdir()
    (migrations_dir / "001_initial.sql").write_text(
        "CREATE TABLE schema_migrations ("
        "version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL);\n"
        "CREATE TABLE one (id TEXT PRIMARY KEY);\n",
        encoding="utf-8",
    )
    (migrations_dir / "002_second.sql").write_text(
        "CREATE TABLE two (id TEXT PRIMARY KEY);\n",
        encoding="utf-8",
    )
    return migrations_dir


def _migrate_in_child(
    root: str,
    sqlite_path: str,
    migrations_dir: str,
    ready: Any,
    start: Any,
    results: Any,
) -> None:
    ready.set()
    if not start.wait(timeout=5):
        results.put(("error", "start timeout"))
        return
    try:
        applied = migrate_vault(
            Path(root),
            Path(sqlite_path),
            migrations_dir=Path(migrations_dir),
            timeout_s=5,
        )
    except Exception as exc:  # pragma: no cover - asserted through child result
        results.put(("error", repr(exc)))
    else:
        results.put(("ok", [migration.version for migration in applied]))


def _open_repository_in_child(
    root: str,
    sqlite_path: str,
    migrations_dir: str,
    ready: Any,
    start: Any,
    results: Any,
) -> None:
    ready.set()
    if not start.wait(timeout=5):
        results.put(("error", "start timeout"))
        return
    try:
        repository = open_vault_repository(
            Path(root),
            Path(sqlite_path),
            migrations_dir=Path(migrations_dir),
            timeout_s=5,
        )
        with repository.connection() as connection:
            tables = {
                row["name"]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
    except Exception as exc:  # pragma: no cover - asserted through child result
        results.put(("error", repr(exc)))
    else:
        results.put(("ok", sorted(tables)))


def _pause_after_first_statement(
    sqlite_path: str,
    migrations_dir: str,
    first_statement_applied: Any,
    release: Any,
) -> None:
    import learnloop.db.migrate as migration_module

    original_iterator = migration_module._iter_sql_statements

    def pausing_iterator(sql: str):
        for index, statement in enumerate(original_iterator(sql)):
            yield statement
            if index == 0:
                # The caller executed the yielded statement before asking this
                # generator for the next one, so the transaction is mid-body.
                first_statement_applied.set()
                release.wait(timeout=30)

    migration_module._iter_sql_statements = pausing_iterator
    migration_module.apply_migrations(
        Path(sqlite_path),
        migrations_dir=Path(migrations_dir),
    )


def test_coordinator_locks_the_vault_for_a_relocated_database(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    migrations_dir = _write_migrations(tmp_path)
    sqlite_path = tmp_path / "relocated" / "state.sqlite"

    migrate_vault(root, sqlite_path, migrations_dir=migrations_dir)

    assert applied_versions(sqlite_path) == {1, 2}
    assert vault_lock_path(root).exists()
    assert not vault_lock_path(sqlite_path.parent).exists()


def test_two_processes_racing_to_migrate_share_one_consistent_ledger(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    migrations_dir = _write_migrations(tmp_path)
    sqlite_path = tmp_path / "relocated" / "state.sqlite"
    context = multiprocessing.get_context("fork")
    ready = [context.Event(), context.Event()]
    start = context.Event()
    results = context.Queue()
    processes = [
        context.Process(
            target=_migrate_in_child,
            args=(
                str(root),
                str(sqlite_path),
                str(migrations_dir),
                ready[index],
                start,
                results,
            ),
        )
        for index in range(2)
    ]

    with vault_mutation_lock(root, purpose="test-start-barrier"):
        for process in processes:
            process.start()
        assert all(event.wait(timeout=5) for event in ready)
        start.set()

    outcomes = [results.get(timeout=10) for _ in processes]
    for process in processes:
        process.join(timeout=10)
        assert process.exitcode == 0

    assert sorted(outcomes) == [("ok", []), ("ok", [1, 2])]
    assert applied_versions(sqlite_path) == {1, 2}


def test_two_normal_repository_opens_serialize_migration(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    migrations_dir = _write_migrations(tmp_path)
    sqlite_path = tmp_path / "relocated" / "state.sqlite"
    context = multiprocessing.get_context("fork")
    ready = [context.Event(), context.Event()]
    start = context.Event()
    results = context.Queue()
    processes = [
        context.Process(
            target=_open_repository_in_child,
            args=(
                str(root),
                str(sqlite_path),
                str(migrations_dir),
                ready[index],
                start,
                results,
            ),
        )
        for index in range(2)
    ]

    with vault_mutation_lock(root, purpose="test-open-start-barrier"):
        for process in processes:
            process.start()
        assert all(event.wait(timeout=5) for event in ready)
        start.set()

    outcomes = [results.get(timeout=10) for _ in processes]
    for process in processes:
        process.join(timeout=10)
        assert process.exitcode == 0

    assert outcomes == [
        ("ok", ["one", "schema_migrations", "two"]),
        ("ok", ["one", "schema_migrations", "two"]),
    ]
    assert applied_versions(sqlite_path) == {1, 2}


def test_process_death_mid_migration_leaves_body_and_receipt_fully_absent(tmp_path):
    root = tmp_path / "seed"
    root.mkdir()
    migrations_dir = _write_migrations(root)
    sqlite_path = tmp_path / "state.sqlite"
    migrate_vault(root, sqlite_path, migrations_dir=migrations_dir)
    (migrations_dir / "003_interrupted.sql").write_text(
        "CREATE TABLE first_statement (id TEXT PRIMARY KEY);\n"
        "CREATE TABLE second_statement (id TEXT PRIMARY KEY);\n",
        encoding="utf-8",
    )
    context = multiprocessing.get_context("fork")
    first_statement_applied = context.Event()
    release = context.Event()
    process = context.Process(
        target=_pause_after_first_statement,
        args=(
            str(sqlite_path),
            str(migrations_dir),
            first_statement_applied,
            release,
        ),
    )

    process.start()
    try:
        assert first_statement_applied.wait(timeout=5)
    finally:
        if process.is_alive():
            process.terminate()
        process.join(timeout=5)
    assert process.exitcode is not None

    assert applied_versions(sqlite_path) == {1, 2}
    with connect(sqlite_path) as connection:
        names = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert "first_statement" not in names
    assert "second_statement" not in names

    assert [
        migration.version
        for migration in migrate_vault(root, sqlite_path, migrations_dir=migrations_dir)
    ] == [3]

"""Production SQLite runs in WAL mode with synchronous=FULL (ADR-015).

The fast test lane keeps the in-memory journal, so every test here that
depends on the production journal mode carries the ``durability`` marker.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import stat
from contextlib import closing, contextmanager
from pathlib import Path

import pytest

import learnloop.db.connection as connection_module
from learnloop.db.checkpoint import checkpoint_wal
from learnloop.db.connection import UnsupportedSQLiteVersion, connect, require_supported_sqlite
from learnloop.db.migrate import JournalModeSwitchError, apply_migrations
from learnloop.db.storage import header_journal_mode, wal_size_bytes
from learnloop.migration_coordinator import migrate_vault

pytestmark = pytest.mark.durability

_COMPANIONS = ("-wal", "-shm", "-journal")


def _minimal_migrations(root: Path) -> Path:
    migrations_dir = root / "migrations"
    migrations_dir.mkdir()
    (migrations_dir / "001_initial.sql").write_text(
        "CREATE TABLE schema_migrations ("
        "version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL);\n"
        "CREATE TABLE records (id INTEGER PRIMARY KEY, payload TEXT NOT NULL);\n",
        encoding="utf-8",
    )
    return migrations_dir


def _second_migration(migrations_dir: Path) -> None:
    (migrations_dir / "002_second.sql").write_text(
        "CREATE TABLE second (id TEXT PRIMARY KEY);\n",
        encoding="utf-8",
    )


def _companions(sqlite_path: Path) -> list[str]:
    return [
        sqlite_path.name + suffix
        for suffix in _COMPANIONS
        if sqlite_path.with_name(sqlite_path.name + suffix).exists()
    ]


def _rollback_database(sqlite_path: Path, migrations_dir: Path) -> None:
    """A database as an older build left it: rollback journal, first migration applied."""

    with closing(sqlite3.connect(sqlite_path)) as connection:
        connection.executescript((migrations_dir / "001_initial.sql").read_text(encoding="utf-8"))
        connection.execute(
            "INSERT INTO schema_migrations(version, name, applied_at) VALUES (1, 'initial', 'then')"
        )
        connection.commit()
    assert header_journal_mode(sqlite_path) == "rollback"


@contextmanager
def _read_only_directory(directory: Path):
    original = stat.S_IMODE(directory.stat().st_mode)
    directory.chmod(0o555)
    try:
        yield
    finally:
        directory.chmod(original)


def _skip_if_permissions_are_not_enforced(directory: Path) -> None:
    with _read_only_directory(directory):
        writable = os.access(directory, os.W_OK)
    if writable:
        pytest.skip("directory permissions are not enforced for this user")


# -- mode switch -----------------------------------------------------------


def test_fresh_database_is_created_in_wal_mode_without_companion_files(tmp_path):
    sqlite_path = tmp_path / "state.sqlite"

    apply_migrations(sqlite_path, _minimal_migrations(tmp_path))

    assert header_journal_mode(sqlite_path) == "wal"
    assert _companions(sqlite_path) == []
    assert not (tmp_path / "state.sqlite.tmp").exists()


def test_fresh_creation_discards_an_orphaned_wal_from_a_deleted_database(tmp_path):
    migrations_dir = _minimal_migrations(tmp_path)
    sqlite_path = tmp_path / "state.sqlite"
    # A -wal left behind by a deleted database of the same name. Its frames
    # are self-consistent, so SQLite would replay them into the new file.
    other = tmp_path / "other" / "state.sqlite"
    other.parent.mkdir()
    writer = sqlite3.connect(other)
    writer.execute("PRAGMA journal_mode=WAL")
    writer.execute("CREATE TABLE intruder (value TEXT)")
    writer.execute("INSERT INTO intruder VALUES ('stale')")
    writer.commit()
    shutil.copyfile(other.with_name("state.sqlite-wal"), tmp_path / "state.sqlite-wal")
    writer.close()

    apply_migrations(sqlite_path, migrations_dir)

    with closing(connect(sqlite_path, read_only=True)) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert tables == {"schema_migrations", "records"}


def test_migration_switches_an_existing_rollback_database_to_wal(tmp_path):
    migrations_dir = _minimal_migrations(tmp_path)
    sqlite_path = tmp_path / "state.sqlite"
    _rollback_database(sqlite_path, migrations_dir)
    _second_migration(migrations_dir)

    applied = migrate_vault(tmp_path, sqlite_path, migrations_dir=migrations_dir)

    assert [migration.version for migration in applied] == [2]
    assert header_journal_mode(sqlite_path) == "wal"
    # The switch is persistent: a plain connection opens it in WAL mode.
    with closing(sqlite3.connect(sqlite_path)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_idle_connection_elsewhere_does_not_block_the_switch(tmp_path):
    migrations_dir = _minimal_migrations(tmp_path)
    sqlite_path = tmp_path / "state.sqlite"
    _rollback_database(sqlite_path, migrations_dir)
    idle = sqlite3.connect(sqlite_path)
    try:
        idle.execute("SELECT COUNT(*) FROM records").fetchone()
        apply_migrations(sqlite_path, migrations_dir)
        assert header_journal_mode(sqlite_path) == "wal"
        idle.execute("INSERT INTO records(payload) VALUES ('after switch')")
        idle.commit()
    finally:
        idle.close()


def test_switch_fails_clearly_and_leaves_the_mode_unchanged_while_a_reader_is_open(tmp_path, monkeypatch):
    monkeypatch.setattr(connection_module, "BUSY_TIMEOUT_MS", 100)
    migrations_dir = _minimal_migrations(tmp_path)
    sqlite_path = tmp_path / "state.sqlite"
    _rollback_database(sqlite_path, migrations_dir)
    _second_migration(migrations_dir)
    reader = sqlite3.connect(sqlite_path, isolation_level=None)
    try:
        reader.execute("BEGIN")
        reader.execute("SELECT COUNT(*) FROM records").fetchone()
        with pytest.raises(JournalModeSwitchError, match="another connection holds a transaction"):
            migrate_vault(tmp_path, sqlite_path, migrations_dir=migrations_dir)
    finally:
        reader.close()

    assert header_journal_mode(sqlite_path) == "rollback"
    with closing(sqlite3.connect(sqlite_path)) as connection:
        versions = {row[0] for row in connection.execute("SELECT version FROM schema_migrations")}
    assert versions == {1}


def test_connect_sets_production_pragmas_and_never_changes_the_journal_mode(tmp_path):
    migrations_dir = _minimal_migrations(tmp_path)
    sqlite_path = tmp_path / "state.sqlite"
    _rollback_database(sqlite_path, migrations_dir)

    with closing(connect(sqlite_path)) as connection:
        assert connection.execute("PRAGMA synchronous").fetchone()[0] == 2
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    assert header_journal_mode(sqlite_path) == "rollback"


def test_runtime_sqlite_below_the_minimum_fails_with_a_clear_message(monkeypatch):
    require_supported_sqlite.cache_clear()
    monkeypatch.setattr(connection_module.sqlite3, "sqlite_version_info", (3, 21, 0))
    monkeypatch.setattr(connection_module.sqlite3, "sqlite_version", "3.21.0")
    try:
        with pytest.raises(UnsupportedSQLiteVersion, match="SQLite 3.22.0 or newer"):
            require_supported_sqlite()
    finally:
        require_supported_sqlite.cache_clear()
        monkeypatch.undo()
        require_supported_sqlite()


# -- read-only opens -----------------------------------------------------------


def _wal_database(tmp_path: Path) -> Path:
    directory = tmp_path / "vault"
    directory.mkdir()
    sqlite_path = directory / "state.sqlite"
    apply_migrations(sqlite_path, _minimal_migrations(tmp_path))
    with closing(connect(sqlite_path)) as connection:
        connection.execute("INSERT INTO records(payload) VALUES ('committed')")
        connection.commit()
    assert header_journal_mode(sqlite_path) == "wal"
    assert _companions(sqlite_path) == []
    return sqlite_path


def test_read_only_open_of_a_wal_database_in_a_read_only_directory_without_companions(tmp_path):
    sqlite_path = _wal_database(tmp_path)
    _skip_if_permissions_are_not_enforced(sqlite_path.parent)

    with _read_only_directory(sqlite_path.parent):
        with closing(connect(sqlite_path, read_only=True)) as connection:
            assert connection.execute("SELECT payload FROM records").fetchall()[0][0] == "committed"
            with pytest.raises(sqlite3.OperationalError):
                connection.execute("INSERT INTO records(payload) VALUES ('write')")
    assert _companions(sqlite_path) == []


def test_read_only_open_in_a_read_only_directory_reads_commits_still_in_the_wal(tmp_path):
    sqlite_path = _wal_database(tmp_path)
    _skip_if_permissions_are_not_enforced(sqlite_path.parent)
    writer = connect(sqlite_path)
    try:
        writer.execute("INSERT INTO records(payload) VALUES ('in the wal')")
        writer.commit()
        assert wal_size_bytes(sqlite_path) > 0
        with _read_only_directory(sqlite_path.parent):
            with closing(connect(sqlite_path, read_only=True)) as connection:
                payloads = [row[0] for row in connection.execute("SELECT payload FROM records ORDER BY id")]
        assert payloads == ["committed", "in the wal"]
    finally:
        writer.close()


def test_read_only_open_refuses_a_wal_it_cannot_index(tmp_path):
    sqlite_path = _wal_database(tmp_path)
    _skip_if_permissions_are_not_enforced(sqlite_path.parent)
    wal_path = sqlite_path.with_name("state.sqlite-wal")
    wal_path.write_bytes(b"\0" * 32)

    with _read_only_directory(sqlite_path.parent):
        with pytest.raises(sqlite3.OperationalError, match="open it from a writable copy"):
            connect(sqlite_path, read_only=True)


def test_read_only_reports_work_in_a_read_only_vault(tmp_path):
    from learnloop.ops.doctor import run_doctor
    from learnloop.substrate.data_quality import data_quality_report
    from learnloop.substrate.model_usage import model_usage_report
    from learnloop.vault.paths import VaultPaths
    from learnloop.vault.loader import load_vault
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    root = paths.root
    sqlite_path = VaultPaths(root, load_vault(root).config).sqlite_path
    assert header_journal_mode(sqlite_path) == "wal"
    assert _companions(sqlite_path) == []
    _skip_if_permissions_are_not_enforced(root)

    with _read_only_directory(root):
        report = run_doctor(root)
        quality = data_quality_report(sqlite_path)
        usage = model_usage_report(sqlite_path, budgets={})

    codes = {issue.code for issue in report.issues}
    assert "sqlite:unreadable" not in codes
    assert "sqlite:missing" not in codes
    assert report.storage is not None and report.storage.journal_mode == "wal"
    assert isinstance(quality, dict) and quality
    assert usage["totals"]["receipts"] == 0
    assert _companions(sqlite_path) == []


def test_sidecar_needs_a_writable_vault_and_says_so(tmp_path):
    from learnloop_sidecar.context import SidecarContext
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    _skip_if_permissions_are_not_enforced(paths.root)

    with _read_only_directory(paths.root):
        with pytest.raises((sqlite3.OperationalError, PermissionError, OSError)):
            SidecarContext().load(paths.root, maintenance=False)


# -- checkpoints -----------------------------------------------------------------


def test_a_long_read_transaction_delays_checkpoints_only_until_it_ends(tmp_path):
    sqlite_path = _wal_database(tmp_path)
    writer = connect(sqlite_path)
    reader = sqlite3.connect(sqlite_path, isolation_level=None)
    try:
        # Keep one connection open so closing the others does not checkpoint.
        reader.execute("SELECT COUNT(*) FROM records").fetchone()
        reader.execute("BEGIN")
        reader.execute("SELECT COUNT(*) FROM records").fetchone()
        for ordinal in range(200):
            writer.execute("INSERT INTO records(payload) VALUES (?)", ("x" * 2048 + str(ordinal),))
            writer.commit()
        grown = wal_size_bytes(sqlite_path)

        blocked = checkpoint_wal(sqlite_path, reason="test while reading")
        assert blocked is not None and blocked.busy
        assert wal_size_bytes(sqlite_path) >= grown

        reader.execute("COMMIT")
        writer.execute("INSERT INTO records(payload) VALUES ('after reader ended')")
        writer.commit()
        released = checkpoint_wal(sqlite_path, reason="test after reading")
        assert released is not None and not released.busy
        assert wal_size_bytes(sqlite_path) == 0
    finally:
        reader.close()
        writer.close()
    with closing(connect(sqlite_path, read_only=True)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM records").fetchone()[0] == 202


def test_checkpoint_is_a_no_op_for_a_rollback_database(tmp_path):
    migrations_dir = _minimal_migrations(tmp_path)
    sqlite_path = tmp_path / "state.sqlite"
    _rollback_database(sqlite_path, migrations_dir)

    assert checkpoint_wal(sqlite_path, reason="test") is None
    assert header_journal_mode(sqlite_path) == "rollback"

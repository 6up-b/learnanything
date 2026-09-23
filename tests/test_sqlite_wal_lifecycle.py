"""WAL copy, checkpoint and storage-reporting lifecycle (ADR-015)."""

from __future__ import annotations

import shutil
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from functools import partial
from pathlib import Path

import pytest
from typer.testing import CliRunner

from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.copies import (
    backup_database,
    copy_tree_with_databases,
    copy_tree_without_databases,
)
from learnloop.db.storage import (
    header_journal_mode,
    inspect_database_storage,
    is_network_or_fuse_filesystem,
    mount_for_path,
    read_mount_table,
    wal_size_bytes,
)
from tests.helpers import create_basic_vault

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _wal_database_with_uncheckpointed_commit(directory: Path) -> tuple[Path, sqlite3.Connection]:
    """A WAL database whose latest commit is only in ``-wal``; the writer stays open."""

    directory.mkdir(parents=True, exist_ok=True)
    sqlite_path = directory / "state.sqlite"
    writer = sqlite3.connect(sqlite_path)
    writer.execute("PRAGMA journal_mode=WAL")
    writer.execute("PRAGMA wal_autocheckpoint=0")
    writer.execute("CREATE TABLE records (payload TEXT)")
    writer.execute("INSERT INTO records VALUES ('only in the wal')")
    writer.commit()
    assert wal_size_bytes(sqlite_path) > 0
    return sqlite_path, writer


def _payloads(sqlite_path: Path) -> list[str]:
    with closing(sqlite3.connect(sqlite_path)) as connection:
        try:
            return [row[0] for row in connection.execute("SELECT payload FROM records")]
        except sqlite3.OperationalError:
            return []


# -- copies ----------------------------------------------------------------------


def test_backup_copies_commits_that_a_byte_copy_of_the_main_file_loses(tmp_path):
    sqlite_path, writer = _wal_database_with_uncheckpointed_commit(tmp_path / "live")
    try:
        byte_copy = tmp_path / "byte-copy.sqlite"
        shutil.copyfile(sqlite_path, byte_copy)
        backup = tmp_path / "backup" / "state.sqlite"
        backup_database(sqlite_path, backup)
    finally:
        writer.close()

    assert _payloads(byte_copy) == []
    assert _payloads(backup) == ["only in the wal"]
    assert not backup.with_name("state.sqlite-wal").exists()


def test_backup_refuses_to_overwrite_an_existing_file(tmp_path):
    sqlite_path, writer = _wal_database_with_uncheckpointed_commit(tmp_path / "live")
    writer.close()
    existing = tmp_path / "existing.sqlite"
    existing.write_bytes(b"")
    with pytest.raises(FileExistsError):
        backup_database(sqlite_path, existing)


def test_tree_copy_backs_up_databases_and_never_copies_companions(tmp_path):
    source = tmp_path / "vault"
    sqlite_path, writer = _wal_database_with_uncheckpointed_commit(source)
    (source / "notes.md").write_text("content", encoding="utf-8")
    try:
        copied = copy_tree_with_databases(source, tmp_path / "copy")
    finally:
        writer.close()

    destination = tmp_path / "copy"
    assert copied == [destination / "state.sqlite"]
    assert sorted(path.name for path in destination.iterdir()) == ["notes.md", "state.sqlite"]
    assert _payloads(destination / "state.sqlite") == ["only in the wal"]


def test_tree_copy_without_databases_leaves_out_configured_names(tmp_path):
    source = tmp_path / "vault"
    source.mkdir()
    (source / "learner.db").write_bytes(b"database")
    (source / "learner.db-wal").write_bytes(b"wal")
    (source / "cache.sqlite-journal").write_bytes(b"journal")
    (source / "notes.md").write_text("content", encoding="utf-8")

    omitted = copy_tree_without_databases(source, tmp_path / "copy", database_names={"learner.db"})

    assert omitted == [source / "learner.db"]
    assert [path.name for path in (tmp_path / "copy").iterdir()] == ["notes.md"]


@pytest.mark.durability
def test_sim_run_vault_keeps_commits_still_in_the_source_wal(tmp_path):
    from learnloop.sim.runner import prepare_run_vault

    paths = create_basic_vault(tmp_path / "vault")
    writer = connect(paths.sqlite_path)
    try:
        writer.execute("PRAGMA wal_autocheckpoint=0")
        writer.execute("CREATE TABLE sim_marker (payload TEXT)")
        writer.execute("INSERT INTO sim_marker VALUES ('recent')")
        writer.commit()
        assert wal_size_bytes(paths.sqlite_path) > 0
        kept = prepare_run_vault(paths.root, tmp_path / "kept", reset_state=False)
        reset = prepare_run_vault(paths.root, tmp_path / "reset", reset_state=True)
    finally:
        writer.close()

    with closing(sqlite3.connect(kept / "state.sqlite")) as connection:
        assert connection.execute("SELECT payload FROM sim_marker").fetchall() == [("recent",)]
    assert not (kept / "state.sqlite-wal").exists()
    assert not any(path.name.startswith("state.sqlite") for path in reset.iterdir())


# -- checkpoints -----------------------------------------------------------------


@pytest.mark.durability
def test_live_rebuild_truncates_the_wal_it_grew(tmp_path):
    from learnloop.substrate.rebuild_orchestrator import rebuild_live_derived_state
    from learnloop.vault.loader import load_vault
    from learnloop.vault.repository import open_vault_repository

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = open_vault_repository(paths.root, paths.sqlite_path)
    # An idle connection keeps the WAL from being removed on close, so only
    # the explicit checkpoint can empty it.
    idle = connect(paths.sqlite_path)
    try:
        idle.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()
        idle.commit()
        rebuild_live_derived_state(vault, repository, clock=FrozenClock(datetime(2026, 9, 1, tzinfo=UTC)))
        assert paths.sqlite_path.with_name("state.sqlite-wal").exists()
        assert wal_size_bytes(paths.sqlite_path) == 0
    finally:
        idle.close()


@pytest.mark.durability
def test_finished_ingest_batch_truncates_the_wal(tmp_path):
    from learnloop.content.pipeline.runner import IngestRunner, JobSpec
    from learnloop.db.repositories import Repository

    sqlite_path = tmp_path / "state.sqlite"
    runner = IngestRunner(
        Repository(sqlite_path),
        vault_root=tmp_path,
        worker_id="w1",
        clock=FrozenClock(datetime(2026, 9, 1, tzinfo=UTC)),
        handlers={"fake": lambda ctx: {"ok": True}},
    )
    idle = connect(sqlite_path)
    try:
        idle.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()
        idle.commit()
        batch_id = runner.enqueue_batch("import", [JobSpec("fake"), JobSpec("fake")])
        assert runner.drain() == 2
        assert runner.repo.get_ingest_batch(batch_id)["status"] == "completed"
        assert wal_size_bytes(sqlite_path) == 0
    finally:
        idle.close()


def test_ingest_batch_checkpoints_once_when_it_becomes_terminal(tmp_path, monkeypatch):
    import learnloop.content.pipeline.runner as runner_module
    from learnloop.content.pipeline.runner import IngestRunner, JobSpec
    from learnloop.db.repositories import Repository

    reasons: list[str] = []
    monkeypatch.setattr(runner_module, "checkpoint_wal", lambda path, *, reason: reasons.append(reason))
    runner = IngestRunner(
        Repository(tmp_path / "state.sqlite"),
        vault_root=tmp_path,
        worker_id="w1",
        clock=FrozenClock(datetime(2026, 9, 1, tzinfo=UTC)),
        handlers={"fake": lambda ctx: {"ok": True}},
    )
    batch_id = runner.enqueue_batch("import", [JobSpec("fake"), JobSpec("fake")])
    runner.drain()
    runner._refresh_batch(batch_id)

    assert reasons == [f"ingest batch {batch_id}"]


# -- storage report ----------------------------------------------------------------


def _mounts_file(tmp_path: Path, lines: list[str]) -> Path:
    mounts = tmp_path / "mounts"
    mounts.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return mounts


def test_mount_table_parsing_picks_the_deepest_mount_and_unescapes_spaces(tmp_path):
    mounts = read_mount_table(
        _mounts_file(
            tmp_path,
            [
                "/dev/sda1 / ext4 rw 0 0",
                "server:/export /mnt/shared\\040drive nfs4 rw 0 0",
                "sshfs#me@host: /mnt/shared\\040drive/sub fuse.sshfs rw 0 0",
            ],
        )
    )
    assert mounts is not None
    assert mount_for_path(Path("/mnt/shared drive/vault"), mounts).filesystem_type == "nfs4"
    assert mount_for_path(Path("/mnt/shared drive/sub/vault"), mounts).filesystem_type == "fuse.sshfs"
    assert mount_for_path(Path("/home/vault"), mounts).filesystem_type == "ext4"


@pytest.mark.parametrize(
    ("filesystem", "remote"),
    [("nfs4", True), ("cifs", True), ("fuse.sshfs", True), ("fuseblk", True), ("fuse", True),
     ("ext4", False), ("btrfs", False), ("tmpfs", False), ("apfs", False)],
)
def test_network_and_fuse_filesystems_are_recognised(filesystem, remote):
    assert is_network_or_fuse_filesystem(filesystem) is remote


def test_header_journal_mode_reads_the_file_format_bytes(tmp_path):
    rollback = tmp_path / "rollback.sqlite"
    with closing(sqlite3.connect(rollback)) as connection:
        connection.execute("CREATE TABLE t (x)")
        connection.commit()
    wal = tmp_path / "wal.sqlite"
    with closing(sqlite3.connect(wal)) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("CREATE TABLE t (x)")
        connection.commit()
    (tmp_path / "text.sqlite").write_text("not a database", encoding="utf-8")

    assert header_journal_mode(rollback) == "rollback"
    assert header_journal_mode(wal) == "wal"
    assert header_journal_mode(tmp_path / "text.sqlite") == "unknown"
    assert header_journal_mode(tmp_path / "missing.sqlite") == "unknown"


def test_doctor_warns_when_the_vault_is_on_a_network_mount(tmp_path, monkeypatch):
    import learnloop.ops.doctor as doctor_module

    paths = create_basic_vault(tmp_path / "vault")
    mounts = _mounts_file(tmp_path, ["/dev/sda1 / ext4 rw 0 0", f"server:/export {paths.root} nfs4 rw 0 0"])
    monkeypatch.setattr(doctor_module, "inspect_database_storage", partial(inspect_database_storage, mounts_file=mounts))

    report = doctor_module.run_doctor(paths.root)

    warnings = [issue for issue in report.issues if issue.code == "storage:network_filesystem"]
    assert len(warnings) == 1 and warnings[0].severity == "warning"
    assert report.as_dict()["storage"]["filesystem_type"] == "nfs4"
    assert report.as_dict()["storage"]["network_or_fuse"] is True


@pytest.mark.durability
def test_doctor_reports_wal_size_and_warns_when_it_is_large(tmp_path, monkeypatch):
    import learnloop.ops.doctor as doctor_module

    paths = create_basic_vault(tmp_path / "vault")
    monkeypatch.setattr(doctor_module, "WAL_SIZE_WARNING_BYTES", 1)
    writer = connect(paths.sqlite_path)
    try:
        writer.execute("PRAGMA wal_autocheckpoint=0")
        writer.execute("CREATE TABLE doctor_marker (payload TEXT)")
        writer.commit()
        report = doctor_module.run_doctor(paths.root)
        result = CliRunner().invoke(_cli_app(), ["doctor", "--vault", str(paths.root)])
    finally:
        writer.close()

    storage = report.as_dict()["storage"]
    assert storage["journal_mode"] == "wal"
    assert storage["wal_bytes"] > 0
    assert "sqlite:wal_large" in {issue.code for issue in report.issues}
    assert "storage: journal_mode=wal wal_bytes=" in result.output


def _cli_app():
    from learnloop.cli import app

    return app


@pytest.mark.durability
@pytest.mark.skipif(not (FIXTURES / "linear_algebra").exists(), reason="linear_algebra fixture absent")
def test_wal_stays_bounded_across_twenty_queue_builds_on_a_fixture_copy(tmp_path):
    from learnloop.db.checkpoint import checkpoint_wal
    from learnloop.scheduling.scheduler import build_due_queue
    from learnloop.substrate.state_sync import sync_vault_state
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths
    from learnloop.vault.repository import open_vault_repository

    root = tmp_path / "linear_algebra"
    copy_tree_with_databases(FIXTURES / "linear_algebra", root)
    vault = load_vault(root)
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    repository = open_vault_repository(vault.root, sqlite_path)
    sync_vault_state(vault, repository)
    assert header_journal_mode(sqlite_path) == "wal"
    idle_reader = connect(sqlite_path, read_only=True)
    try:
        idle_reader.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()
        sizes = []
        for _ in range(20):
            build_due_queue(vault, repository, persist_explanations=True)
            sizes.append(wal_size_bytes(sqlite_path))
        # Measured 2026-09-23: about 12 KB per persisted build, 288 KB after
        # twenty. SQLite's automatic checkpoint engages at 1000 pages (4 MiB).
        assert 0 < max(sizes) < 4 * 1024 * 1024
        result = checkpoint_wal(sqlite_path, reason="test")
        assert result is not None and not result.busy
        assert wal_size_bytes(sqlite_path) == 0
    finally:
        idle_reader.close()

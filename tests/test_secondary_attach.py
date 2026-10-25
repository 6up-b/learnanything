"""Mobile PR-1: ``SidecarContext.load_secondary`` and content-fingerprint reload.

spec_mobile_tailnet_v1 §3.1 and §3.3 (PR-1), §10 G12; storage spec §6.2 (the
primary duties a secondary never runs, on first attach, reload and switch).
"Writes nothing" is checked three ways: every table's rows before and after,
every vault file's bytes before and after, and an SQLite authorizer that
refuses (and records) any write statement on a connection opened during the
attach. The durability test runs the attach in a second process on a WAL vault
while the primary holds the write lock: an attach that tried to write would
wait out ``busy_timeout`` and fail.
"""

from __future__ import annotations

import hashlib
import multiprocessing
import os
import sqlite3
import sys
import time
import traceback
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path

import pytest

from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.db.scopes import connection_hook
from learnloop.vault.loader import (
    CONTENT_FINGERPRINT_TTL_SECONDS,
    content_files,
    load_vault,
    vault_content_fingerprint,
)
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml_data, write_yaml
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.errors import SidecarError
from tests.helpers import create_basic_vault

_ITEM = ("linear-algebra", "pi_svd_define_001")
_BUMP = (
    "INSERT INTO queue_state(singleton, revision, updated_at) VALUES (1, 1, '2026-10-25T00:00:00Z') "
    "ON CONFLICT(singleton) DO UPDATE SET revision = queue_state.revision + 1"
)

_WRITE_ACTIONS = {
    getattr(sqlite3, name)
    for name in dir(sqlite3)
    if name.startswith(("SQLITE_INSERT", "SQLITE_UPDATE", "SQLITE_DELETE", "SQLITE_CREATE_", "SQLITE_DROP_",
                        "SQLITE_ALTER_TABLE", "SQLITE_ANALYZE", "SQLITE_REINDEX"))
}


def _db_snapshot(database: Path) -> dict:
    with closing(connect(database, read_only=True)) as connection:
        tables = [
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        return {
            "schema": [tuple(row) for row in connection.execute("SELECT type, name, sql FROM sqlite_master ORDER BY name")],
            "rows": {
                table: sorted((tuple(row) for row in connection.execute(f'SELECT * FROM "{table}"')), key=repr)
                for table in tables
            },
        }


def _file_snapshot(root: Path, database: Path) -> dict[str, str]:
    """Every file under the vault by content hash, except the database and its WAL companions."""

    skip = {database.name, database.name + "-wal", database.name + "-shm", database.name + "-journal"}
    files: dict[str, str] = {}
    for directory, _subdirectories, names in os.walk(root):
        for name in names:
            path = Path(directory) / name
            if path.parent == database.parent and name in skip:
                continue
            files[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


@contextmanager
def _writes_refused():
    """Refuse and record every write statement on connections opened in this context."""

    attempted: list[tuple] = []

    def authorizer(action, arg1, arg2, _database, _trigger):
        if action in _WRITE_ACTIONS:
            attempted.append((action, arg1, arg2))
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    def hook(connection, _path):
        connection.set_authorizer(authorizer)

    with connection_hook(hook):
        yield attempted


def _seed_primary_work(paths: VaultPaths) -> str:
    """State a primary load acts on: a leaseless synchronous synthesis run older
    than the lease cutoff (the abandoned-run sweep), a leased ingest job (lease
    recovery), and item state that content sync has not written yet."""

    from learnloop.clock import FrozenClock
    from learnloop.content.pipeline.runner import IngestRunner, JobSpec
    from learnloop.content.synthesis.synthesis_manifests import build_manifest, persist_manifest

    repository = Repository.attach(paths.sqlite_path)
    old = FrozenClock(datetime(2020, 1, 1, tzinfo=UTC))
    manifest = persist_manifest(repository, build_manifest(load_vault(paths.root), source_set_id="ss1"))
    run_id = repository.insert_synthesis_run(manifest_id=manifest, mode="bootstrap", clock=old)
    IngestRunner(repository, vault_root=paths.root, worker_id="desktop", clock=old).enqueue_batch(
        "legacy_ingest", [JobSpec("fake")]
    )
    lease = repository.claim_next_ingest_job(
        worker_id="desktop", now_iso="2099-01-01T00:00:00Z", lease_cutoff_iso="2098-12-31T23:58:00Z",
    )
    assert lease is not None
    return run_id


def _edit_item_prompt(paths: VaultPaths, prompt: str) -> None:
    path = paths.practice_item_path(*_ITEM)
    data = read_yaml_data(path)
    data["prompt"] = prompt
    write_yaml(path, data)


def test_load_secondary_writes_nothing_where_load_writes(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    control = tmp_path / "control"
    copy_tree_with_databases(paths.root, control)
    run_id = _seed_primary_work(paths)
    db_before = _db_snapshot(paths.sqlite_path)
    files_before = _file_snapshot(paths.root, paths.sqlite_path)

    ctx = SidecarContext()
    with _writes_refused() as attempted:
        ctx.load_secondary(paths.root)

    assert attempted == []
    assert _db_snapshot(paths.sqlite_path) == db_before
    assert _file_snapshot(paths.root, paths.sqlite_path) == files_before
    assert Repository.attach(paths.sqlite_path).synthesis_run(run_id)["status"] == "created"
    assert ctx.secondary is True
    assert ctx.vault is not None and "pi_svd_define_001" in ctx.vault.practice_items
    assert ctx.repository is not None and ctx.repository.sqlite_path == paths.sqlite_path
    # No primary machinery is bound: queued work stays durable for the primary.
    assert ctx.ingest_jobs._runner is None
    assert ctx.post_attempt_worker._supplier is None
    assert not ctx.post_attempt_worker.running

    # The control: the same vault loaded as a primary does write (content sync).
    control_paths = VaultPaths(control.resolve(), paths.config)
    control_before = _db_snapshot(control_paths.sqlite_path)
    primary = SidecarContext()
    try:
        primary.load(control_paths.root, maintenance=False)
        assert _db_snapshot(control_paths.sqlite_path)["rows"]["practice_item_state"] != (
            control_before["rows"]["practice_item_state"]
        )
    finally:
        primary.ingest_jobs.shutdown()
        primary.close_background_builds()


def test_reload_and_switch_of_a_secondary_stay_secondary(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    other = create_basic_vault(tmp_path / "other")
    _seed_primary_work(paths)
    before = {root: _db_snapshot(p.sqlite_path) for root, p in ((paths.root, paths), (other.root, other))}

    ctx = SidecarContext()
    ctx.load_secondary(paths.root)
    generation = ctx.vault_generation
    with _writes_refused() as attempted:
        ctx.reload()  # handlers reload after their writes; a primary reload migrates and syncs
        ctx.reload(maintenance=False)
        ctx.load_secondary(other.root)  # a vault switch
    assert attempted == []
    assert ctx.secondary is True and ctx.vault_root == other.root
    assert ctx.vault_generation == generation + 3
    assert ctx.ingest_jobs._runner is None
    for root, p in ((paths.root, paths), (other.root, other)):
        assert _db_snapshot(p.sqlite_path) == before[root]


def test_secondary_handlers_still_write(tmp_path):
    """Not a read-only mode: only the attach is write-free (spec §3.1)."""

    paths = create_basic_vault(tmp_path / "vault")
    ctx = SidecarContext()
    ctx.load_secondary(paths.root)
    _vault, repository = ctx.require_vault()
    revision = repository.queue_revision()["revision"]
    assert repository.bump_queue_revision() == revision + 1
    assert Repository.attach(paths.sqlite_path, read_only=True).queue_revision()["revision"] == revision + 1


def test_secondary_refuses_a_schema_it_would_have_to_migrate(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    with closing(connect(paths.sqlite_path)) as connection:
        connection.execute("DELETE FROM schema_migrations WHERE version = (SELECT MAX(version) FROM schema_migrations)")
        connection.commit()
    before = _db_snapshot(paths.sqlite_path)

    ctx = SidecarContext()
    with pytest.raises(SidecarError) as refused:
        ctx.load_secondary(paths.root)
    assert refused.value.code == "schema_mismatch"
    assert "--fix-state" in refused.value.message
    assert _db_snapshot(paths.sqlite_path) == before
    assert ctx.vault_root is None and ctx.vault is None and ctx.repository is None


def test_secondary_never_creates_a_missing_database(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    for suffix in ("", "-wal", "-shm", "-journal"):
        Path(str(paths.sqlite_path) + suffix).unlink(missing_ok=True)

    with pytest.raises(SidecarError) as refused:
        SidecarContext().load_secondary(paths.root)
    assert refused.value.code == "schema_mismatch"
    assert not paths.sqlite_path.exists()


def test_secondary_refusals_for_unbuilt_modes(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    with pytest.raises(SidecarError) as ingest:
        SidecarContext().load_secondary(paths.root, bind_ingest=True)
    assert ingest.value.code == "secondary_ingest_unavailable"

    primary = SidecarContext()
    try:
        primary.load(paths.root, maintenance=False)
        with pytest.raises(SidecarError) as demote:
            primary.load_secondary(paths.root)
        assert demote.value.code == "vault_loaded_as_primary"
        with pytest.raises(SidecarError):
            primary.refresh_if_content_changed()
    finally:
        primary.ingest_jobs.shutdown()
        primary.close_background_builds()


def test_content_fingerprint_reload_within_the_freshness_bound(tmp_path):
    """G12: a YAML change another process made is loaded by the first request at
    most ``CONTENT_FINGERPRINT_TTL_SECONDS`` after it, as a secondary, writing nothing."""

    assert CONTENT_FINGERPRINT_TTL_SECONDS <= 2.0
    paths = create_basic_vault(tmp_path / "vault")
    ctx = SidecarContext()
    ctx.load_secondary(paths.root)
    db_before = _db_snapshot(paths.sqlite_path)
    ctx._fingerprint_checked_at = 100.0
    loaded = ctx.vault

    _edit_item_prompt(paths, "Define the singular value decomposition.")
    assert ctx.refresh_if_content_changed(now=100.5) is False  # inside the bound: the cached comparison
    assert ctx.vault is loaded
    with _writes_refused() as attempted:
        assert ctx.refresh_if_content_changed(now=100.0 + CONTENT_FINGERPRINT_TTL_SECONDS) is True
    assert attempted == []
    assert ctx.vault is not loaded and ctx.secondary is True
    assert ctx.vault.practice_items["pi_svd_define_001"].prompt == "Define the singular value decomposition."
    assert _db_snapshot(paths.sqlite_path) == db_before

    reloaded = ctx.vault
    assert ctx.refresh_if_content_changed(now=200.0) is False  # nothing changed: no reload
    assert ctx.vault is reloaded


def test_a_change_during_the_load_is_loaded_at_the_next_comparison(tmp_path, monkeypatch):
    """The fingerprint is taken before the load, so a write the load raced is never missed."""

    import learnloop_sidecar.context as context_module

    paths = create_basic_vault(tmp_path / "vault")
    real_load = context_module.load_vault
    raced = {"done": False}

    def racing_load(root, *args, **kwargs):
        vault = real_load(root, *args, **kwargs)
        if not raced["done"]:
            raced["done"] = True
            _edit_item_prompt(paths, "Written while the secondary was loading.")
        return vault

    monkeypatch.setattr(context_module, "load_vault", racing_load)
    ctx = SidecarContext()
    ctx.load_secondary(paths.root)
    assert ctx.vault.practice_items["pi_svd_define_001"].prompt == "Define SVD."
    assert ctx.refresh_if_content_changed(now=time.monotonic() + CONTENT_FINGERPRINT_TTL_SECONDS) is True
    assert ctx.vault.practice_items["pi_svd_define_001"].prompt == "Written while the secondary was loading."


def test_fingerprint_sees_renames_and_older_mtimes(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    notes = paths.subject_dir("linear-algebra") / "notes"
    notes.mkdir(parents=True, exist_ok=True)
    note = notes / "first.md"
    note.write_text("A note.\n", encoding="utf-8")
    os.utime(note, ns=(1_000_000_000, 1_000_000_000))
    before = vault_content_fingerprint(paths.root)

    renamed = notes / "second.md"
    note.rename(renamed)  # same size, same (old) mtime, same file count
    after_rename = vault_content_fingerprint(paths.root)
    assert after_rename != before

    renamed.write_text("A longer note.\n", encoding="utf-8")
    os.utime(renamed, ns=(1_000_000_000, 1_000_000_000))  # a copy that keeps an older mtime
    assert vault_content_fingerprint(paths.root) != after_rename


def test_fingerprint_covers_every_file_the_loader_reads(tmp_path):
    """The file set cannot drift from the loader's (spec §3.1): every file a load opens is fingerprinted."""

    paths = create_basic_vault(tmp_path / "vault")
    subject = paths.subject_dir("linear-algebra")
    (subject / "notes").mkdir(parents=True, exist_ok=True)
    (subject / "notes" / "svd.md").write_text("---\nid: note_svd\n---\nSVD notes.\n", encoding="utf-8")
    root = str(paths.root)
    opened: list[str] = []
    recording = {"on": False}

    def audit(event, args):
        if recording["on"] and event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            path = os.path.realpath(os.fsdecode(args[0]))
            if path.startswith(root + os.sep) and os.path.isfile(path):
                opened.append(os.path.relpath(path, root))

    sys.addaudithook(audit)
    recording["on"] = True
    try:
        vault = load_vault(paths.root)
    finally:
        recording["on"] = False
    assert vault.notes  # the walk reached a note, so notes are among the files checked
    assert opened, "the audit hook saw no vault file open"
    covered = content_files(paths.root)
    missing = sorted(set(opened) - set(covered))
    assert missing == [], f"load_vault read files the content fingerprint does not cover: {missing}"


# -- durability lane: a real second process on a WAL vault -------------------------------


def _secondary_process(root: str, pipe) -> None:
    try:
        from learnloop.db.connection import BUSY_TIMEOUT_MS, connect as child_connect
        from learnloop_sidecar.context import SidecarContext as ChildContext

        ctx = ChildContext()
        started = time.monotonic()
        ctx.load_secondary(root)
        elapsed = time.monotonic() - started
        _vault, repository = ctx.require_vault()
        with closing(child_connect(repository.sqlite_path, read_only=True)) as connection:
            mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
        pipe.send(("attached", elapsed, BUSY_TIMEOUT_MS / 1000.0, mode, repository.queue_revision()["revision"]))
        while True:
            command = pipe.recv()
            if command == "stop":
                break
            if command == "read":
                reloaded = ctx.refresh_if_content_changed(now=time.monotonic() + 2.0)
                pipe.send(("read", repository.queue_revision()["revision"], reloaded,
                           ctx.vault.practice_items["pi_svd_define_001"].prompt))
        pipe.send(("stopped",))
    except BaseException:
        pipe.send(("error", traceback.format_exc()))
    finally:
        pipe.close()


def _receive(pipe):
    assert pipe.poll(60), "the secondary process did not reply within 60 seconds"
    message = pipe.recv()
    assert message[0] != "error", message[1]
    return message


@pytest.mark.durability
def test_second_process_attaches_beside_a_writing_primary_on_wal(tmp_path):
    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    run_id = _seed_primary_work(paths)
    primary = Repository.attach(paths.sqlite_path)
    revision = primary.queue_revision()["revision"]
    before = _db_snapshot(paths.sqlite_path)
    files_before = _file_snapshot(paths.root, paths.sqlite_path)

    # The primary holds the write lock, with an uncommitted write, for the whole attach.
    writer = connect(paths.sqlite_path)
    writer.execute("BEGIN IMMEDIATE")
    writer.execute(_BUMP)
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe()
    process = context.Process(target=_secondary_process, args=(str(paths.root), child))
    process.start()
    child.close()
    try:
        _tag, elapsed, busy_timeout, mode, seen = _receive(parent)
        assert mode == "wal"
        # An attach that tried to write would have waited out busy_timeout and failed.
        assert elapsed < busy_timeout
        assert seen == revision  # the uncommitted write is not visible
        writer.rollback()
        assert _db_snapshot(paths.sqlite_path) == before
        assert _file_snapshot(paths.root, paths.sqlite_path) == files_before

        # Committed database state is read fresh on every connection (no reload);
        # a YAML change is loaded at the next request past the freshness bound.
        writer.execute("BEGIN IMMEDIATE")
        writer.execute(_BUMP)
        writer.commit()
        _edit_item_prompt(paths, "Edited by the primary.")
        parent.send("read")
        assert _receive(parent) == ("read", revision + 1, True, "Edited by the primary.")
        parent.send("stop")
        assert _receive(parent) == ("stopped",)
        process.join(timeout=30)
        assert process.exitcode == 0
        assert Repository.attach(paths.sqlite_path).synthesis_run(run_id)["status"] == "created"
    finally:
        writer.close()
        if process.is_alive():
            process.terminate()
            process.join(timeout=10)
        parent.close()

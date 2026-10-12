"""The standalone store (spec §6.1) and gate G6: M1 writes nothing to state.sqlite."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.cli import project as project_cli
from learnloop.projects.experiment_store import STORE_SCHEMA_VERSION, ProjectStore, StoreSchemaError, store_path
from tests.helpers import create_basic_vault
from tests.project_support import clock_at, isolated_git, make_model_repo, project_fake  # noqa: F401


def _state_fingerprint(sqlite_path):
    raw = sqlite_path.read_bytes()
    with closing(sqlite3.connect(f"{sqlite_path.resolve().as_uri()}?mode=ro", uri=True)) as connection:
        schema = connection.execute("SELECT type, name, sql FROM sqlite_master ORDER BY type, name").fetchall()
        counts = {
            name: connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
            for (kind, name, _sql) in schema
            if kind == "table" and not name.startswith("sqlite_")
        }
    return hashlib.sha256(raw).hexdigest(), hashlib.sha256(repr(schema).encode()).hexdigest(), counts


def test_m1_never_writes_state_sqlite(isolated_git, project_fake, tmp_path, monkeypatch):
    paths = create_basic_vault(tmp_path / "vault")
    repo = make_model_repo(tmp_path / "repo")
    before = _state_fingerprint(paths.sqlite_path)
    runner = CliRunner()
    vault = ["--vault", str(paths.root)]

    def run(args, day, input_text=None):
        monkeypatch.setattr(project_cli, "_clock", lambda: clock_at(day))
        result = runner.invoke(app, ["project", *args, *vault], input=input_text)
        assert result.exit_code == 0, result.output
        return result

    run(["enroll", str(repo.path), "--install-hook"], 0)
    run(["sweep"], 0)
    run(["status", "--disclosure", "--diffs"], 1)
    listed = json.loads(run(["probes", "--list", "--json"], 8).output)
    probe_id = listed["due"][0]["probe_id"]
    answered = json.loads(run(["answer", probe_id, "--text", "It scales x and applies relu.", "--json"], 8).output)
    response_id = answered["response"]["response_id"]
    run(["contest", response_id, "--score", "0.5"], 9)
    diff_id = json.loads(run(["status", "--diffs", "--json"], 9).output)["diffs"][0]["diff_id"]
    run(["provenance", diff_id, "--accept-style", "all_at_once"], 9)
    run(["probes"], 9, input_text="/skip\n")
    run(["grade"], 9)
    run(["report"], 9)
    run(["unenroll", str(repo.path)], 9)

    assert store_path(paths.root).is_file()
    assert _state_fingerprint(paths.sqlite_path) == before


def test_store_schema_is_versioned(tmp_path):
    store = ProjectStore.for_vault(tmp_path)
    with closing(sqlite3.connect(store.path)) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == STORE_SCHEMA_VERSION
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"repos", "diffs", "provenance_reports", "probes", "probe_responses", "judgments", "call_receipts"} <= tables
    with closing(sqlite3.connect(store.path)) as connection:
        connection.execute(f"PRAGMA user_version = {STORE_SCHEMA_VERSION + 1}")
        connection.commit()
    with pytest.raises(StoreSchemaError):
        ProjectStore.for_vault(tmp_path)


def test_existing_never_creates_the_store(tmp_path):
    assert ProjectStore.existing(tmp_path) is None
    assert not (tmp_path / "projects").exists()


def test_responses_are_practice_only(tmp_path):
    store = ProjectStore.for_vault(tmp_path)
    with closing(sqlite3.connect(store.path)) as connection:
        sql = connection.execute("SELECT sql FROM sqlite_master WHERE name='probe_responses'").fetchone()[0]
    assert "CHECK(evidence_class = 'practice')" in sql
    assert "CHECK(exposure_isolation = 'unknown')" in sql


def test_replay_and_rebuild_make_no_git_model_or_subprocess_calls(isolated_git, project_fake, tmp_path, monkeypatch):
    """Gate G7: rebuild reads persisted state only, even with a populated project store."""

    import subprocess

    from learnloop.projects import ai_runtime, capture

    paths = create_basic_vault(tmp_path / "vault")
    repo = make_model_repo(tmp_path / "repo")
    runner = CliRunner()
    monkeypatch.setattr(project_cli, "_clock", lambda: clock_at(0))
    assert runner.invoke(app, ["project", "enroll", str(repo.path), "--vault", str(paths.root)]).exit_code == 0
    assert runner.invoke(app, ["project", "sweep", "--vault", str(paths.root)]).exit_code == 0
    store_bytes = store_path(paths.root).read_bytes()

    def forbidden(*_args, **_kwargs):
        raise AssertionError("replay must not call git, a model or a subprocess")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(capture, "sweep", forbidden)
    monkeypatch.setattr(ai_runtime.PaidCalls, "call", forbidden)
    for args in (["rebuild", "--shadow", "--json"], ["rebuild-derived-state", "--json"]):
        result = runner.invoke(app, [*args, "--vault", str(paths.root)])
        assert result.exit_code == 0, result.output
    assert project_fake.calls == {"authoring": 1, "closed_book": 1, "grading": 1}  # only the sweep's
    assert store_path(paths.root).read_bytes() == store_bytes


@pytest.mark.durability
def test_store_runs_in_wal_with_full_sync_in_production(tmp_path):
    from learnloop.db.connection import wal_unavailable_reason

    store = ProjectStore.for_vault(tmp_path)
    with store.connection() as connection:
        mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
        synchronous = connection.execute("PRAGMA synchronous").fetchone()[0]
    assert mode == ("wal" if wal_unavailable_reason() is None else mode)
    assert synchronous == 2  # FULL
    # Reopening is idempotent and keeps the mode.
    ProjectStore.for_vault(tmp_path)
    with store.connection() as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == mode


def test_a_version_1_store_gains_the_pending_queue(tmp_path):
    store = ProjectStore.for_vault(tmp_path)
    with closing(sqlite3.connect(store.path)) as connection:
        connection.execute("DROP TABLE pending_commits")
        connection.execute("PRAGMA user_version = 1")
        connection.commit()
    reopened = ProjectStore.for_vault(tmp_path)
    assert reopened.pending_commits() == []
    with closing(sqlite3.connect(store.path)) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 2


def test_a_read_only_open_neither_upgrades_nor_writes_an_older_store(tmp_path):
    store = ProjectStore.for_vault(tmp_path)
    store.set_meta("pending_offset", "7")
    with closing(sqlite3.connect(store.path)) as connection:
        connection.execute("DROP TABLE pending_commits")
        connection.execute("PRAGMA user_version = 1")
        connection.commit()
    before = store.path.read_bytes()
    reader = ProjectStore.existing(tmp_path, read_only=True)
    assert reader.schema_version == 1
    assert reader.pending_commits() == [] and reader.meta("pending_offset") == "7"
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        reader.set_meta("pending_offset", "8")
    assert store.path.read_bytes() == before
    assert ProjectStore.existing(tmp_path / "elsewhere", read_only=True) is None


def test_a_read_only_open_still_refuses_a_newer_store(tmp_path):
    store = ProjectStore.for_vault(tmp_path)
    with closing(sqlite3.connect(store.path)) as connection:
        connection.execute(f"PRAGMA user_version = {STORE_SCHEMA_VERSION + 1}")
        connection.commit()
    with pytest.raises(StoreSchemaError):
        ProjectStore.existing(tmp_path, read_only=True)

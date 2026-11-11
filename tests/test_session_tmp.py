"""A run's scratch directory goes when the run ends; a killed run's goes on the next run (tests/session_tmp.py)."""

from __future__ import annotations

import os

from tests import session_tmp


def _isolated_env(monkeypatch):
    for name in (session_tmp.SESSION_ENV, session_tmp.OWNER_ENV, session_tmp.KEEP_ENV):
        monkeypatch.delenv(name, raising=False)


def test_a_new_run_removes_dead_runs_and_legacy_entries_but_not_live_runs(tmp_path, monkeypatch):
    _isolated_env(monkeypatch)
    dead = tmp_path / "run-999999991-abc"
    live = tmp_path / f"run-{os.getppid()}-def"
    legacy = [tmp_path / "pytest-of-someone", tmp_path / "global_settings_isolated", tmp_path / "fresh-schema-x1"]
    unrelated = tmp_path / "notes"
    for directory in (dead, live, unrelated, *legacy):
        (directory / "vault").mkdir(parents=True)
    monkeypatch.setattr(session_tmp, "pid_alive", lambda pid: pid != 999999991)

    root = session_tmp.session_root(tmp_path)

    assert root.parent == tmp_path and root.name.startswith(f"run-{os.getpid()}-")
    assert not dead.exists() and not any(path.exists() for path in legacy)
    assert live.exists() and unrelated.exists()
    assert os.environ[session_tmp.SESSION_ENV] == str(root)
    assert os.environ[session_tmp.OWNER_ENV] == str(os.getpid())


def test_a_worker_reuses_its_live_owners_directory_and_never_deletes_it(tmp_path, monkeypatch):
    _isolated_env(monkeypatch)
    owned = tmp_path / "run-1-x"
    owned.mkdir()
    monkeypatch.setenv(session_tmp.SESSION_ENV, str(owned))
    monkeypatch.setenv(session_tmp.OWNER_ENV, str(os.getppid()))

    assert session_tmp.session_root(tmp_path) == owned
    assert session_tmp.finish(owned) is None
    assert owned.exists()


def test_a_dead_owners_directory_is_not_inherited(tmp_path, monkeypatch):
    _isolated_env(monkeypatch)
    orphan = tmp_path / "run-999999992-x"
    orphan.mkdir()
    monkeypatch.setenv(session_tmp.SESSION_ENV, str(orphan))
    monkeypatch.setenv(session_tmp.OWNER_ENV, "999999992")
    monkeypatch.setattr(session_tmp, "pid_alive", lambda pid: pid != 999999992)

    root = session_tmp.session_root(tmp_path)

    assert root != orphan and not orphan.exists()


def test_the_owner_deletes_its_directory_unless_asked_to_keep_it(tmp_path, monkeypatch):
    _isolated_env(monkeypatch)
    root = session_tmp.session_root(tmp_path)
    (root / "vault" / "state.sqlite").parent.mkdir(parents=True)

    monkeypatch.setenv(session_tmp.KEEP_ENV, "1")
    assert str(root) in session_tmp.finish(root)
    assert root.exists()

    monkeypatch.setenv(session_tmp.KEEP_ENV, "0")
    assert session_tmp.finish(root) is None
    assert not root.exists()

"""A run's scratch directory goes when the run ends; a killed run's goes on the next run (tests/session_tmp.py).

Every test isolates the module's state and the environment with monkeypatch, so the real session's own directory,
owner and claimant come back untouched at teardown.
"""

from __future__ import annotations

import os
import time

import pytest

from tests import session_tmp

DEAD = 999999991


@pytest.fixture(autouse=True)
def _isolated(monkeypatch):
    for name in (session_tmp.SESSION_ENV, session_tmp.OWNER_ENV, session_tmp.KEEP_ENV):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(session_tmp, "_made", None)
    monkeypatch.setattr(session_tmp, "_claimant", None)
    monkeypatch.setattr(session_tmp, "pid_alive", lambda pid: pid != DEAD)


def _age(path, seconds):
    then = time.time() - seconds
    os.utime(path, (then, then))


def test_a_new_run_removes_dead_runs_and_old_leftovers_but_not_live_or_recent_ones(tmp_path):
    dead = tmp_path / f"run-{DEAD}-abc"
    live = tmp_path / f"run-{os.getppid()}-def"
    old = [tmp_path / "pytest-of-someone", tmp_path / "global_settings_isolated", tmp_path / "fresh-schema-x1"]
    recent = tmp_path / "pytest-of-current"
    unrelated = tmp_path / "notes"
    for directory in (dead, live, recent, unrelated, *old):
        (directory / "vault").mkdir(parents=True)
    for directory in old:
        _age(directory, session_tmp.LEGACY_MIN_AGE_SECONDS + 60)

    root = session_tmp.session_root(tmp_path)

    assert root.parent == tmp_path and root.name.startswith(f"run-{os.getpid()}-")
    assert not dead.exists() and not any(path.exists() for path in old)
    # A leftover touched within the day may belong to a run still on the old conftest, or to a run whose
    # PYTEST_DEBUG_TEMPROOT points at the shared root.
    assert live.exists() and recent.exists() and unrelated.exists()
    assert os.environ[session_tmp.SESSION_ENV] == str(root)
    assert os.environ[session_tmp.OWNER_ENV] == str(os.getpid())


def test_a_worker_reuses_its_live_owners_directory_and_never_deletes_it(tmp_path, monkeypatch):
    owned = tmp_path / "run-1-x"
    owned.mkdir()
    monkeypatch.setenv(session_tmp.SESSION_ENV, str(owned))
    monkeypatch.setenv(session_tmp.OWNER_ENV, str(os.getppid()))

    assert session_tmp.session_root(tmp_path) == owned
    session_tmp.claim("worker-session")
    assert session_tmp.finish(owned, "worker-session") is None
    assert owned.exists()


@pytest.mark.parametrize("name", ["outside", "run-1-x"])
def test_an_inherited_directory_outside_the_root_is_never_adopted_or_deleted(tmp_path, monkeypatch, name):
    elsewhere = tmp_path / "elsewhere" / name
    (elsewhere / "precious").mkdir(parents=True)
    root_dir = tmp_path / "root"
    monkeypatch.setenv(session_tmp.SESSION_ENV, str(elsewhere))
    monkeypatch.setenv(session_tmp.OWNER_ENV, str(os.getpid()))

    root = session_tmp.session_root(root_dir)
    session_tmp.claim("session")
    session_tmp.finish(elsewhere, "session")

    assert root != elsewhere and root.parent == root_dir
    assert (elsewhere / "precious").exists()


def test_a_symlinked_run_name_is_not_adopted(tmp_path, monkeypatch):
    target = tmp_path / "target"
    (target / "precious").mkdir(parents=True)
    root_dir = tmp_path / "root"
    root_dir.mkdir()
    link = root_dir / "run-1-link"
    link.symlink_to(target)
    monkeypatch.setenv(session_tmp.SESSION_ENV, str(link))
    monkeypatch.setenv(session_tmp.OWNER_ENV, str(os.getpid()))

    assert session_tmp.session_root(root_dir) != link
    assert (target / "precious").exists()


def test_a_dead_owners_directory_is_not_inherited(tmp_path, monkeypatch):
    orphan = tmp_path / f"run-{DEAD}-x"
    orphan.mkdir()
    monkeypatch.setenv(session_tmp.SESSION_ENV, str(orphan))
    monkeypatch.setenv(session_tmp.OWNER_ENV, str(DEAD))

    root = session_tmp.session_root(tmp_path)

    assert root != orphan and not orphan.exists()


def test_only_the_first_session_deletes_so_a_nested_pytest_main_leaves_it(tmp_path):
    root = session_tmp.session_root(tmp_path)
    session_tmp.claim("outer")
    assert session_tmp.session_root(tmp_path) == root  # the nested run's conftest, same process and environment
    session_tmp.claim("nested")

    assert session_tmp.finish(root, "nested") is None
    assert root.exists()
    assert session_tmp.finish(root, "outer") is None
    assert not root.exists()


def test_a_kept_directory_survives_later_runs_too(tmp_path, monkeypatch):
    root = session_tmp.session_root(tmp_path)
    session_tmp.claim("session")
    (root / "vault" / "state.sqlite").parent.mkdir(parents=True)
    monkeypatch.setenv(session_tmp.KEEP_ENV, "1")

    assert str(root) in session_tmp.finish(root, "session")
    assert root.exists()

    # The run that kept it ends; the next run, without KEEP, sweeps dead runs but not a kept one.
    kept = root.rename(tmp_path / f"run-{DEAD}-kept")
    monkeypatch.delenv(session_tmp.KEEP_ENV)
    monkeypatch.delenv(session_tmp.SESSION_ENV)
    monkeypatch.setattr(session_tmp, "_made", None)
    session_tmp.session_root(tmp_path)
    assert (kept / "vault").exists()


def test_the_owner_deletes_its_directory_at_the_end(tmp_path):
    root = session_tmp.session_root(tmp_path)
    session_tmp.claim("session")
    (root / "vault" / "state.sqlite").parent.mkdir(parents=True)

    assert session_tmp.finish(root, "session") is None
    assert not root.exists()

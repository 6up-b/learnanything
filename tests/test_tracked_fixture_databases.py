"""Tracked fixture databases carry no un-checkpointed WAL frames.

A tracked database may be in either journal mode. Since storage S0 the only
tracked databases are the historical fixtures (the migration head and
``mvp017_route_check_replay``, both in rollback mode); the owner's vaults left
the tip, and their owner-lane copies are guarded by ``tests/conftest.py``. A read-only
open of a WAL database leaves an empty ``-wal`` and a ``-shm`` behind, which
is harmless. What must never exist beside a tracked database is a non-empty
``-wal`` (a byte copy of the main file would miss its committed pages) or a
``-journal``, and no companion may be tracked by git. Tests and tools copy a
fixture before opening it writable. ``tests/conftest.py`` repeats the
header-and-frames check when the session finishes.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from learnloop.db.copies import COMPANION_SUFFIXES
from tests.owner_vaults import tracked_fixture_files

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_tracked_fixture_databases_have_no_pending_wal_frames():
    # Only what git tracks: an untracked leftover in a checkout is not the tip's.
    databases = tracked_fixture_files("*.sqlite")
    assert databases, "expected tracked fixture databases under fixtures/ (S3 turns them into text dumps)"
    pending = [
        str(companion.relative_to(FIXTURES))
        for database in databases
        for companion in (database.with_name(database.name + suffix) for suffix in COMPANION_SUFFIXES)
        if companion.exists() and companion.stat().st_size > 0 and not companion.name.endswith("-shm")
    ]
    assert pending == [], f"un-checkpointed fixture companions present; checkpoint or delete them: {pending}"


def test_no_fixture_companion_file_is_tracked_by_git():
    tracked = subprocess.run(
        ["git", "ls-files", "--", "fixtures"], capture_output=True, text=True, check=True,
        cwd=FIXTURES.parent,
    ).stdout.splitlines()
    companions = [path for path in tracked if path.endswith(COMPANION_SUFFIXES)]
    assert companions == [], f"companion files must never be committed: {companions}"


def test_the_session_guard_reads_only_the_databases_git_tracks(monkeypatch):
    """Codex review of S0, F6: an untracked vault left under ``fixtures/`` (or the
    worktree's ignored ``migration_head_219/`` leftover) is not the tip's, so the
    session guard never opens it; only git's list (and the owner lane's root) count."""

    import tests.conftest as conftest
    import tests.owner_vaults as owner_vaults

    tracked = {str(path.relative_to(FIXTURES)) for path in tracked_fixture_files("*.sqlite")}
    monkeypatch.delenv(owner_vaults.OWNER_VAULTS_ENV, raising=False)
    assert set(conftest._fixture_database_state()) == tracked
    # Were git to track none of them, the guard would read none.
    monkeypatch.setattr(owner_vaults, "_tracked_fixture_paths", lambda: [])
    assert conftest._fixture_database_state() == {}

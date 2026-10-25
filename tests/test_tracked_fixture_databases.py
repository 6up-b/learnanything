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

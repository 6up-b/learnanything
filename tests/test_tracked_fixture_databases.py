"""Tracked fixture databases stay in rollback mode with no companion files.

Tests and tools copy a fixture before opening it writable; migrating the copy
converts the copy to WAL.  Opening a tracked fixture writable in place would
switch its header to WAL and leave ``-wal``/``-shm`` files in the working tree,
and a byte copy of such a fixture could then miss committed pages.
``tests/conftest.py`` repeats this check when the session finishes, so a test
that opens a fixture in place fails the run even if it sorts after this file.
"""

from __future__ import annotations

from pathlib import Path

from learnloop.db.copies import COMPANION_SUFFIXES
from learnloop.db.storage import header_journal_mode

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_tracked_fixture_databases_are_rollback_mode_without_companions():
    databases = sorted(FIXTURES.rglob("*.sqlite"))
    assert databases, "expected tracked fixture databases under fixtures/"
    wal_headers = [
        str(database.relative_to(FIXTURES))
        for database in databases
        if header_journal_mode(database) == "wal"
    ]
    companions = [
        str(companion.relative_to(FIXTURES))
        for database in databases
        for companion in (database.with_name(database.name + suffix) for suffix in COMPANION_SUFFIXES)
        if companion.exists()
    ]
    assert wal_headers == [], f"fixtures opened writable in place (WAL header): {wal_headers}"
    assert companions == [], f"fixture companion files present; delete them: {companions}"

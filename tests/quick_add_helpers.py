"""What other test files use from ``tests/test_quick_add.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository


_CLOCK = FrozenClock(datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC))


def _register_source(repo: Repository, *, source_id: str, revision_id: str, category: str, uri: str) -> None:
    now = _CLOCK.now().isoformat()
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, current_revision_id, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (source_id, category, uri, revision_id, now, now),
        )
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            (revision_id, source_id, f"sha256:{source_id}", uri, now),
        )
        connection.commit()

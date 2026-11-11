"""What other test files use from ``tests/test_reader_inquiry_status.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.db.repositories import Repository


# The tables RW1a may write: the event envelope and the questions it already
# writes for every Ask. Nothing else changes when a status flips (G2).
_ALLOWED = {"interaction_events", "question_events", "schema_migrations"}


def table_counts(repo: Repository) -> dict[str, int]:
    with repo.connection() as connection:
        names = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )]
        return {
            name: connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
            for name in names if name not in _ALLOWED and not name.startswith("source_block_fts")
        }

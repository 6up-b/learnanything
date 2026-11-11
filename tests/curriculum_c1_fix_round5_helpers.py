"""What other test files use from ``tests/test_curriculum_c1_fix_round5.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from tests.deliverable_fixtures import DeliverableFake


class MeteredFake(DeliverableFake):
    """A metered path-judge route (an API key billed per token)."""

    provider_name = "fake_metered_deliverable"
    provider_type = "openai_compatible"


def _rows(c1) -> int:
    with c1.repository.connection() as connection:
        return connection.execute("SELECT COUNT(*) FROM deliverable_path_sections").fetchone()[0]

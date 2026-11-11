"""What other test files use from ``tests/test_required_method_round3.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


def _family_rows(repository):
    from tests.pf_generation_helpers import rows

    return [row for row in rows(repository) if row["generation_path"] != "single_shot"]

"""What other test files use from ``tests/test_workbench_discriminate.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from tests.workbench_help_fakes import CheckFake


def _rival_check() -> CheckFake:
    """The default check: step 2 questionable with two rival readings."""

    return CheckFake()

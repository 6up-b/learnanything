"""What other test files use from ``tests/test_curriculum_c1_fix_round2.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.daily_plan import engine as E


def _no_refresh(ctx) -> None:
    """Today's daily refresh already ran in this sidecar (nothing runs in the background)."""

    from learnloop_sidecar.handlers.deliverables import _work

    _work(ctx).refresh_day = E.local_date()

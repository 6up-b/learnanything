"""What other test files use from ``tests/test_ro2_history_resolve.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock


def _iso(moment) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _attempt(paths, attempt_id, item, created_at, *, correctness=1.0, presentation=None, hints=0):
    """A graded attempt through the real pipeline (AD reads only graded answers), at ``created_at``;
    returns its id (``attempt_id`` names it in the test only)."""

    from learnloop.clock import parse_utc
    from tests.ad23_fakes import answer

    return answer(paths, item, correct=correctness >= 0.8, presentation_id=presentation, hints=hints,
                  clock=FrozenClock(parse_utc(created_at)))

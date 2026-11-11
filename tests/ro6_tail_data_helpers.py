"""What other test files use from ``tests/test_ro6_tail_data.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from tests.ro5_calibration_helpers import _end_session, _grade_answers, _new_session
from tests.router_mixture_helpers import run


def _days(env, runtime, days: range, *, skip: frozenset[int] = frozenset(), steps: int = 60) -> None:
    for day in days:
        if day not in skip:
            session_id = _new_session(env, runtime, day)
            run(env, steps=steps)
            _grade_answers(env, day)
            _end_session(env, session_id)
        env.clock.advance(24 * 60)

"""What other test files use from ``tests/test_mobile_v2_rereview_fixes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import pytest

from learnloop.daily_plan import engine

from tests.mobile_v2_plan_helpers import _dont_know, _next


def _phone_to_pending_stop(phone, session_id: str, drawn: list) -> dict:
    for index in range(12):
        reply = _next(phone, session_id, f"f7_next_{index}")
        step = reply["step"]
        if step is None or step["kind"] != "item":
            break
        _dont_know(phone, session_id, step, f"f7_dk_{index}")
    if not drawn:
        pytest.skip("the phone never crossed a boundary past held work")  # pragma: no cover
    return reply


def _record(repository):
    return engine.latest_today(engine.PlanEnv(vault=None, repository=repository))

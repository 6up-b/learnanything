"""What other test files use from ``tests/test_quick_check.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.diagnosis.quick_check import quick_check_progress, start_quick_check
from learnloop.placement.predictor import active_predictor

from tests.assumed_known_helpers import _answer, _at


def _start(vault, repository, los, *, minutes=1):
    session_id = repository.create_session(available_minutes=25, clock=_at(0))
    progress = start_quick_check(
        vault, repository, session_id=session_id, learning_object_ids=los, clock=_at(minutes),
    )
    return session_id, progress


def _progress(vault, repository, progress, minutes):
    return quick_check_progress(vault, repository, progress["calibration_session_id"], clock=_at(minutes))


def _answer_target(vault, repository, session_id, progress, minutes, points=4.0):
    """Answer the item the check presented (only presented items are its answers)."""

    item_id = progress["next_target"]["practice_item_id"]
    _answer(vault, repository, item_id, points, minutes=minutes, session_id=session_id)
    return item_id


def _best_item(vault, repository, los):
    predictor = active_predictor(vault, repository)
    weights = {lo: 1.0 for lo in los}
    candidates = sorted(i for i, item in vault.practice_items.items() if item.learning_object_id in weights)
    return sorted(candidates, key=lambda i: (-predictor.conditional_gain(i, [], weights), i))[0]

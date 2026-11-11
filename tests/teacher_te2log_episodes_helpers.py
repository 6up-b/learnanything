"""What other test files use from ``tests/test_teacher_te2log_episodes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


HYPOTHESIS = "WOMBATHYPOTHESIS treats the eigenvalue as the eigenvector"


def detour_turn(node="n1", repair="reteach", p=0.7, hypothesis=HYPOTHESIS, message="Let's look at it another way."):
    return {"message": message, "requests": [
        {"action": "note_detour", "node": node, "hypothesis": hypothesis, "repair": repair, "p": p}]}

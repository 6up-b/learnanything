"""What other test files use from ``tests/test_teacher_te2log_node_held.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from tests.teacher_fakes import plan_turn


def held_plan(context):
    turn = plan_turn(context)
    nodes = turn["requests"][0]["plan"]
    nodes[0]["p_held"] = 0.35
    nodes.insert(0, {"id": "n0", "statement": "Determinants detect invertibility.", "lo_id": "lo_det",
                     "anchors": nodes[0]["anchors"], "premises": [], "p_held": 0.8})
    nodes.append({"id": "nx", "statement": "Something with no topic.", "anchors": [], "premises": [], "p_held": 0.5})
    return turn

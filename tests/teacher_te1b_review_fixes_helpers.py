"""What other test files use from ``tests/test_teacher_te1b_review_fixes.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.vault.loader import load_vault


def _card(paths, repository, now_iso: str):
    from learnloop.daily_plan.router_card import CardGatherer
    from learnloop.daily_plan.types import BlockCandidate, PlanState
    from learnloop.router.card import build_card

    state = PlanState(plan_id="p", kind="normal", minutes_budget=25.0, minutes_left=25.0,
                      lane_minutes_left={"maintain": 10.0}, days_since_last_activity=0, streak_days=1,
                      current_block_id=None)
    feasible = [BlockCandidate(
        candidate_id="maintain:x", lane="maintain", action="maintain", subtype=None,
        learning_object_ids=("lo_det",), item_ids=("pi_det_1",), reading=None, est_minutes=4.0,
        planner_value=1.0, reason="review", annotations={"reason_code": "review", "reversible": True},
    )]
    inputs = CardGatherer(load_vault(paths.root), repository, session_id="s1").inputs(state, feasible, now_iso=now_iso)
    return build_card(inputs)

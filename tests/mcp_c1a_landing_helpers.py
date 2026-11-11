"""What other test files use from ``tests/test_mcp_c1a_landing.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.daily_plan.policy import policy_for
from learnloop.daily_plan.router_card import CardGatherer
from learnloop.daily_plan.types import BlockCandidate, PlanState

from tests.daily_plan_fakes import MovableClock, iso, make_env, scheduled, seed_due
from tests.helpers import create_daily_plan_vault
from tests.router_card_helpers import A, LAST, PAST, _item


NOW = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
NOW_ISO = iso(NOW)


def _world(tmp_path, monkeypatch):
    """Two topics: lo_m1 (pi_a) and lo_m2 (pi_b, and pi_cold, held by an open cold retry)."""

    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_m1": [], "lo_m2": []}, version=A)
    _item(paths, "pi_a", "lo_m1", prompt="Compute the determinant of A.", expected="kept")
    _item(paths, "pi_b", "lo_m2", prompt="Name a basis of R^2.", expected="e1, e2")
    _item(paths, "pi_cold", "lo_m2", prompt="Is this set a basis?", expected="no")
    clock = MovableClock()
    env = make_env(paths.root, [scheduled("pi_a", "lo_m1", forgetting_risk=0.6),
                                scheduled("pi_b", "lo_m2", forgetting_risk=0.6)], clock=clock, session_id="s1")
    for item in ("pi_a", "pi_b"):
        seed_due(env.repository, item, due=PAST, last=LAST)
    from learnloop.content.sources import exam_material as EM

    monkeypatch.setattr(EM, "exam_material",
                        lambda _vault, _repo: EM.ExamMaterial(material=EM.Material(), held_out=EM.Material()))
    env.policy = policy_for(env.vault, env.repository, session_id="s1", clock=clock)
    return env


def _card_inputs(env):
    state = PlanState(plan_id="p", kind="normal", minutes_budget=25.0, minutes_left=25.0,
                      lane_minutes_left={"maintain": 10.0}, days_since_last_activity=0, streak_days=1,
                      current_block_id=None)
    feasible = [BlockCandidate(
        candidate_id="maintain:x", lane="maintain", action="maintain", subtype=None,
        learning_object_ids=("lo_m1", "lo_m2"), item_ids=("pi_a", "pi_b"), reading=None, est_minutes=4.0,
        planner_value=1.0, reason="review", annotations={"reason_code": "review", "reversible": True},
    )]
    return CardGatherer(env.vault, env.repository, clock=env.clock, session_id="s1").inputs(
        state, feasible, now_iso=NOW_ISO)

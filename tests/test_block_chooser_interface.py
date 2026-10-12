"""Daily-loop DL1 gate G13: the §6.8 chooser interface.

A candidate larger than ``minutes_left`` or than its lane's remaining minutes is
never offered. A chooser that names an unknown or infeasible id, or tries to
overspend a lane, cannot: the container falls back to ``lane_quota_v1`` and
flags it. Released lane minutes follow §6.2's flow-on order. Every block
decision is logged with its candidate set. These are the container's rules,
the same whichever source and chooser fill the plan (router R2's included).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from learnloop.daily_plan.chooser import LaneQuotaChooser
from learnloop.daily_plan.engine import PlanPolicy, PoolContext, build_plan, decide
from learnloop.daily_plan.reentry import ReentryGap
from learnloop.daily_plan.records import PlanRecord
from learnloop.daily_plan.types import (
    CONTINUE_CURRENT,
    LANES,
    STOP_FOR_TODAY,
    BlockCandidate,
    BlockChoice,
    PlanState,
)
from tests.daily_plan_fakes import make_env, scheduled
from tests.helpers import create_daily_plan_vault


def _candidate(candidate_id, lane, minutes, value=0.5):
    return BlockCandidate(
        candidate_id=candidate_id, lane=lane, action="maintain", subtype=None,
        learning_object_ids=(), item_ids=(), reading=None, est_minutes=minutes,
        planner_value=value, reason=f"{lane}: {candidate_id}",
    )


@dataclass
class FakeSource:
    offered: list[BlockCandidate]
    name: str = "fake_source"
    seen: list[PlanState] = field(default_factory=list)

    def candidates(self, state: PlanState) -> list[BlockCandidate]:
        self.seen.append(state)
        # A source may propose anything; the container decides feasibility.
        return list(self.offered)


@dataclass
class FakeChooser:
    answer: str
    name: str = "fake_router"
    feasible_seen: list[list[str]] = field(default_factory=list)

    def choose(self, state, feasible):
        self.feasible_seen.append([c.candidate_id for c in feasible])
        return BlockChoice(candidate_id=self.answer, chosen_by="mixture", propensity=0.25, why="model", why_kind="model_written", decision_ref="router_decision_1")


def _record(budget, lanes):
    row = {
        "id": "plan_1", "kind": "normal", "status": "open", "minutes_budget": budget,
        "remembered_minutes": int(budget), "local_date": "2026-10-12",
        "split": {"lanes": {lane: {"minutes": lanes.get(lane, 0.0)} for lane in LANES}, "lanes_allowed": list(LANES)},
        "admission": {},
    }
    return PlanRecord(row=row, blocks=[])


def _context(admitted_new=0.0):
    return PoolContext(
        pool=(), lanes_allowed=LANES, admitted_new_ids=frozenset(), admitted_new_minutes=admitted_new,
        reading=None, reading_full_minutes=None, titles={}, gap=ReentryGap(False, 0, 7, None), streak_days=0,
    )


def _policy(source, chooser):
    return PlanPolicy(source_name=source.name, chooser=chooser, make_source=lambda _ctx: source)


def test_a_candidate_larger_than_the_minutes_left_is_never_offered():
    source = FakeSource([_candidate("big", "maintain", 7.0), _candidate("fits", "maintain", 3.0)])
    chooser = FakeChooser("big")
    decision = decide(_record(5.0, {"maintain": 5.0}), _context(), _policy(source, chooser))
    assert chooser.feasible_seen[-1] == ["fits"]
    assert decision.fallback and decision.fallback_from == "big"
    assert decision.candidate.candidate_id == "fits"
    assert decision.choice.chosen_by == "lane_quota"


def test_a_candidate_larger_than_its_lanes_minutes_is_never_offered():
    source = FakeSource([_candidate("ten", "push", 10.0), _candidate("small", "maintain", 2.0)])
    chooser = FakeChooser("ten")
    decision = decide(_record(25.0, {"push": 1.0, "maintain": 10.0}), _context(), _policy(source, chooser))
    assert "ten" not in chooser.feasible_seen[-1]
    assert decision.fallback and decision.candidate.candidate_id == "small"


@pytest.mark.parametrize("answer", ["no_such_block", CONTINUE_CURRENT])
def test_unknown_ids_and_continue_at_a_boundary_fall_back_and_are_flagged(answer):
    source = FakeSource([_candidate("a", "maintain", 3.0)])
    decision = decide(_record(25.0, {"maintain": 10.0}), _context(), _policy(source, FakeChooser(answer)))
    assert decision.fallback and decision.fallback_from == answer
    assert decision.candidate.candidate_id == "a"


def test_stopping_is_only_allowed_when_offered():
    source = FakeSource([_candidate("a", "maintain", 3.0)])
    decision = decide(_record(25.0, {"maintain": 10.0}), _context(), _policy(source, FakeChooser(STOP_FOR_TODAY)))
    assert decision.fallback and decision.candidate is not None
    # Below five minutes left it is offered, and a router may take it.
    low = decide(_record(4.0, {"maintain": 4.0}), _context(), _policy(source, FakeChooser(STOP_FOR_TODAY)))
    assert low.stop_offered and not low.fallback and low.candidate is None


def test_a_valid_router_choice_is_kept_with_its_propensity():
    source = FakeSource([_candidate("a", "maintain", 3.0), _candidate("b", "repair", 3.0)])
    decision = decide(_record(25.0, {"maintain": 10.0, "repair": 5.0}), _context(), _policy(source, FakeChooser("a")))
    assert not decision.fallback
    assert decision.choice.propensity == 0.25 and decision.choice.decision_ref == "router_decision_1"


def test_released_minutes_follow_the_flow_on_order():
    # repair has no candidate and maintain's 6-minute block does not fit its 3
    # minutes: both release, and the pooled 7 minutes flow maintain -> repair
    # -> push to the first lane they make feasible, maintain.
    source = FakeSource([_candidate("m", "maintain", 6.0), _candidate("p", "push", 2.0)])
    decision = decide(
        _record(25.0, {"repair": 4.0, "maintain": 3.0, "push": 2.0}), _context(), _policy(source, LaneQuotaChooser())
    )
    assert decision.redistribution == {
        "released": [{"from": "repair", "minutes": 4.0}, {"from": "maintain", "minutes": 3.0}],
        "to": "maintain",
        "given": 7.0,
    }
    assert decision.state.lane_minutes_left["maintain"] == pytest.approx(7.0)
    assert "m" in [c.candidate_id for c in decision.feasible]


def test_lane_quota_prefers_the_largest_unspent_share_then_repair_first():
    source = FakeSource([
        _candidate("m", "maintain", 3.0), _candidate("r", "repair", 3.0),
        _candidate("n", "new", 3.0), _candidate("p", "push", 3.0),
    ])
    decision = decide(
        _record(25.0, {"repair": 4.0, "maintain": 10.0, "new": 5.0, "push": 6.0}),
        _context(admitted_new=5.0),
        _policy(source, LaneQuotaChooser()),
    )
    # Every lane is fully unspent: ties go repair, maintain, new, push.
    assert decision.candidate.candidate_id == "r"
    assert decision.choice.why_kind == "computed" and decision.choice.propensity == 1.0


def test_every_decision_is_logged_with_its_candidate_set(tmp_path):
    paths = create_daily_plan_vault(tmp_path / "vault", learning_objects={"lo_x": [("pi_x1", 2.0)]})

    env = make_env(paths.root, [scheduled("pi_x1", "lo_x", new_material=1.0)])
    env.policy = PlanPolicy(source_name="legacy_lanes_v1", chooser=FakeChooser("no_such_block"), make_source=env.policy.make_source)
    record = build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    (block,) = record.blocks
    chosen = block.chosen
    assert chosen["fallback"] is True and chosen["fallback_from"] == "no_such_block"
    assert chosen["chosen_by"] == "lane_quota" and chosen["chooser"] == "fake_router"
    assert [row["candidate_id"] for row in chosen["candidate_set"]]
    assert {"lane", "est_minutes", "planner_value"} <= set(chosen["candidate_set"][0])
    assert chosen["state"]["minutes_left"] == pytest.approx(25.0)
    assert record.row["chooser"] == "fake_router"

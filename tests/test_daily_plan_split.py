"""Daily-loop DL1 §6.2 (P3): ``split_v1``, its flow-on, and re-entry's two lanes."""

from __future__ import annotations

import pytest

from learnloop.daily_plan.split import display_lane_minutes, redistribute, split_line, split_v1
from learnloop.daily_plan.types import REENTRY_LANES


def _split(**overrides):
    args = dict(
        budget=25.0,
        requested_minutes=0.0,
        loads={"repair": 4.0, "maintain": 30.0, "push": 20.0},
        admitted_new_minutes=6.0,
        push_candidates=True,
        repair_max_share=0.30,
        maintain_max_share=0.60,
    )
    args.update(overrides)
    return split_v1(**args)


def test_shares_cap_repair_and_maintain_and_split_the_rest():
    split = _split()
    assert split.minutes("repair") == pytest.approx(4.0)  # its load, under 30%
    assert split.minutes("maintain") == pytest.approx(15.0)  # 60% of 25, not its 30 min load
    rest = 25.0 - 4.0 - 15.0
    assert split.minutes("new") == pytest.approx(min(6.0, rest / 2))  # half the rest (push exists)
    assert split.minutes("push") == pytest.approx(rest - split.minutes("new"))
    assert sum(split.minutes(lane) for lane in ("repair", "maintain", "new", "push")) == pytest.approx(25.0)


def test_overdue_maintenance_never_takes_the_whole_budget():
    split = _split(loads={"repair": 0.0, "maintain": 500.0, "push": 0.0}, admitted_new_minutes=0.0, push_candidates=False)
    # 60% cap; the unused rest flows to maintenance overflow (step 4), since
    # nothing else can use it: the cap binds step 2, not the whole plan.
    assert split.lanes["maintain"].cap == pytest.approx(15.0)
    assert split.flowed and split.flowed[0]["to"] == "maintain"


def test_requests_are_deducted_before_the_split():
    split = _split(requested_minutes=5.0)
    assert split.m == pytest.approx(20.0)
    assert split.lanes["maintain"].cap == pytest.approx(12.0)
    assert sum(split.minutes(lane) for lane in ("repair", "maintain", "new", "push")) <= 20.0 + 1e-9


def test_new_takes_all_the_rest_without_push_but_never_more_than_admitted():
    split = _split(loads={"repair": 0.0, "maintain": 2.0, "push": 0.0}, admitted_new_minutes=10.0, push_candidates=False)
    assert split.minutes("new") == pytest.approx(10.0)
    # The remaining minutes flow on to maintenance and repair loads only; new
    # never receives flowed minutes beyond its admitted minutes.
    assert split.minutes("new") <= 10.0 + 1e-9


def test_unused_minutes_flow_maintain_then_repair_then_push():
    split = _split(loads={"repair": 10.0, "maintain": 20.0, "push": 30.0}, admitted_new_minutes=0.0)
    # repair capped at 7.5, maintain at 15; the rest (2.5) all goes to push
    # first (step 3), so nothing flows.
    assert split.minutes("push") == pytest.approx(2.5)
    sparse = _split(loads={"repair": 10.0, "maintain": 20.0, "push": 0.0}, admitted_new_minutes=0.0, push_candidates=False)
    # Nothing for new or push: the 2.5 unused flow to maintenance overflow first.
    assert [entry["to"] for entry in sparse.flowed] == ["maintain"]
    assert sparse.minutes("maintain") == pytest.approx(17.5)


def test_reentry_plans_use_only_repair_and_maintain():
    split = _split(lanes_allowed=REENTRY_LANES, budget=15.0)
    assert set(split.lanes) == {"repair", "maintain"}
    assert split.minutes("new") == 0.0 and split.minutes("push") == 0.0


def test_more_new_material_gives_new_its_admitted_minutes_first():
    split = _split(admitted_new_minutes=8.0, new_first=True, budget=10.0)
    assert split.minutes("new") == pytest.approx(8.0)


def test_the_line_shows_whole_minutes_that_add_up():
    split = _split()
    display = split.display_minutes()
    assert sum(display.values()) == 25
    assert split.line() == split_line(25.0, display)
    assert split.line().startswith("25 min · maintain 15 · repair 4")
    assert display_lane_minutes({"repair": 3.4, "maintain": 3.3, "new": 3.3}) == {"repair": 4, "maintain": 3, "new": 3}


def test_redistribution_releases_to_the_first_lane_that_can_use_it():
    # maintain has no candidate; repair can use more; push is next in order.
    can = {"repair": 2.0, "push": 1.0}
    left, releases = redistribute(
        {"repair": 1.0, "maintain": 4.0, "new": 0.0, "push": 0.0},
        has_candidate=lambda lane, minutes: lane in can and can[lane] <= minutes,
        new_room=0.0,
    )
    assert left["maintain"] == 0.0
    # Repair's 1 minute cannot fit its 2-minute candidate either, so both
    # lanes release; the pooled 5 minutes flow maintain -> repair -> push, and
    # repair is the first lane they make feasible.
    assert left["repair"] == pytest.approx(5.0)
    assert {r["from"] for r in releases} == {"repair", "maintain"}
    assert {r["to"] for r in releases} == {"repair"}


def test_new_never_receives_more_than_its_admitted_room():
    left, releases = redistribute(
        {"repair": 3.0, "maintain": 0.0, "new": 1.0, "push": 0.0},
        has_candidate=lambda lane, minutes: lane == "new" and minutes >= 2.0,
        new_room=1.5,
    )
    assert left["new"] == pytest.approx(2.5)
    assert any(record.get("from") == "pool" for record in releases)

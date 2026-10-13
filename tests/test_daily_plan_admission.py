"""Daily-loop DL1 §6.3 (Q11): load-based admission with a ceiling, a cap and a floor."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from learnloop.daily_plan.admission import (
    NewCandidate,
    ReviewItem,
    admit_new_material,
    more_new_tradeoff,
    new_item_daily_cost,
    projected_review_load,
)

NOW = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)


def _admit(candidates, **overrides):
    args = dict(
        review_load_per_day=0.0,
        m=25.0,
        load_ceiling=0.80,
        horizon_days=14,
        reviews_per_new_item=4,
        cap_per_day=10,
        floor_per_day=1,
        planned_today=0,
    )
    args.update(overrides)
    return admit_new_material(candidates, **args)


def _new(n, minutes=3.5, requested=False):
    return [NewCandidate(f"pi_{i}", minutes, requested=requested) for i in range(n)]


def test_review_load_counts_reviews_in_the_horizon():
    items = [
        # due tomorrow on a 2-day interval: ceil(14 / 2) = 7 reviews of 3 minutes
        ReviewItem("pi_a", "2026-10-13T09:00:00Z", "2026-10-11T09:00:00Z", 3.0),
        # due beyond the horizon: no load
        ReviewItem("pi_b", "2026-11-30T09:00:00Z", "2026-10-01T09:00:00Z", 3.0),
        # no due date: no load
        ReviewItem("pi_c", None, None, 3.0),
    ]
    assert projected_review_load(items, now=NOW, horizon_days=14) == pytest.approx(7 * 3.0 / 14)


def test_admission_stops_at_the_load_ceiling():
    # ceiling 0.8 x 25 = 20 min/day; each new item costs 3.5 x 5 / 14 = 1.25.
    cost = new_item_daily_cost(3.5, reviews=4, horizon_days=14)
    admission = _admit(_new(20), review_load_per_day=18.0)
    assert len(admission.admitted) == int((20.0 - 18.0) // cost)
    assert admission.stopped_by == "load_ceiling"


def test_the_daily_cap_counts_new_items_already_planned_today():
    admission = _admit(_new(20), planned_today=7)
    assert len(admission.admitted) == 3
    assert admission.stopped_by == "daily_cap"
    assert _admit(_new(20), planned_today=10).admitted == ()


def test_the_floor_admits_one_when_new_material_exists():
    admission = _admit(_new(3), review_load_per_day=100.0)
    assert [c.practice_item_id for c in admission.admitted] == ["pi_0"]
    assert admission.floor_applied
    # ... but not past the cap, not in re-entry, and not with admission off.
    assert _admit(_new(3), review_load_per_day=100.0, planned_today=10).admitted == ()
    assert _admit(_new(3), review_load_per_day=100.0, reentry=True).admitted == ()
    assert _admit(_new(3), review_load_per_day=100.0, enabled=False).admitted == ()
    # The floor is per day: a second plan with one already planned adds none.
    assert _admit(_new(3), review_load_per_day=100.0, planned_today=1).admitted == ()


def test_learner_requests_are_exempt_and_take_the_first_slots():
    candidates = [NewCandidate(f"req_{i}", 3.5, requested=True) for i in range(2)] + _new(2)
    admission = _admit(candidates, review_load_per_day=100.0, planned_today=10)
    assert [c.practice_item_id for c in admission.exempt] == ["req_0", "req_1"]
    assert admission.admitted == ()
    assert admission.admitted_ids[:2] == ("req_0", "req_1")


def test_more_new_material_bypasses_the_ceiling_and_the_cap_once():
    admission = _admit(_new(12), review_load_per_day=100.0, planned_today=10, override="more_new")
    assert len(admission.admitted) == 12
    trade = more_new_tradeoff(admission.admitted, reviews_per_new_item=4, horizon_days=14)
    assert trade == pytest.approx(12 * 3.5 * 5 / 14)


def test_admission_keeps_the_schedulers_order():
    admission = _admit(_new(5))
    assert [c.practice_item_id for c in admission.admitted] == [f"pi_{i}" for i in range(5)]

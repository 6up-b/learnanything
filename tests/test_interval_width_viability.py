"""P4 step 3 -- interval-width viability of robust EVSI (spec_p4 §16.3, U-021/U-023).

Ties the Step-3 EVSI selector to the P0 abstention budget: with heuristic-width channels
the measure-mode abstention rate stays inside the registered budget; a breach raises the
budget alarm rather than silently widening tolerances.
"""

from __future__ import annotations

from learnloop.services import robust_composition as rc
from learnloop.sim.interval_width_viability import run_interval_width_viability


def test_heuristic_width_keeps_abstention_within_budget():
    report = run_interval_width_viability()
    assert report.budget == rc.ABSTENTION_BUDGET_FRACTION
    # At the shipped heuristic channel width, robust EVSI stays usable on genuinely
    # separating questions: abstention stays inside the P0 budget, no alarm.
    assert report.heuristic_within_budget is True
    heuristic = next(w for w in report.per_width if w.concentration == report.heuristic_concentration)
    assert heuristic.abstention_rate <= report.budget


def test_pathological_width_breach_raises_the_alarm():
    # A pathologically wide channel drives measure-mode abstention past the budget; the
    # sim must SURFACE that as an alarm, never silently widen tolerances (§16.3).
    report = run_interval_width_viability(concentrations=(30.0, 0.3))
    breached = [w for w in report.per_width if not w.within_budget]
    assert breached, "expected a pathological width to breach the budget"
    assert all(w.abstention_rate > report.budget for w in breached)
    assert report.alarm is True
    # The heuristic width itself still holds.
    assert report.heuristic_within_budget is True


def test_report_is_deterministic():
    a = run_interval_width_viability()
    b = run_interval_width_viability()
    assert a.as_dict() == b.as_dict()

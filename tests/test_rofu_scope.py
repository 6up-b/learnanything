"""The follow-up batch, item 5 (RO6's landing open item 2, on its ruling R11): a growing retention scope is a scope
extension, not an objective change. Fakes only.

§3.3's undated uses run "from enrollment on": a topic the learner starts practising enters the retention scope at
the density every retention topic has, which is a change of state the transition caused, not of the objective. At
the tag with ``[router_objective] scope_extension`` the objective's definition reads the retention scope by its
density alone, so such a transition keeps its backup (the same one as with no growth) and one generator version;
a density that changes (Codex's 0.1 -> 0.9), a goal, a weight or the horizon is still a change point.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from learnloop.algorithm_versions import ROUTER_FOLLOWUPS_ALGORITHM_VERSION, ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
from learnloop.router_objective import learned_tail as LT
from learnloop.router_objective import tail_data as TD

from tests.ro6_codex_review_helpers import FAR, STOP, _quiet, _row, _trace


def _config(version: str = ROUTER_FOLLOWUPS_ALGORITHM_VERSION, *, on: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        algorithms=SimpleNamespace(algorithm_version=version),
        router_objective=SimpleNamespace(enabled=True, scope_extension=on, session_gap_minutes=30.0,
                                         residual_prior_sd=0.01, residual_weight_prior_sd=1.0,
                                         evaluation_window_days=14))


def _traced(population: dict[str, float], *, goals: dict | None = None, previous: dict | None = None,
            q: float = 0.0) -> dict:
    width = len(LT.NAMES)
    trace = _trace(q={STOP: q, "a": q}, cutoff_days=6.0, previous=previous)
    trace["versions"] = {"horizon_days": 6.0}
    trace["inputs_sources"] = {"goals": goals or {}}
    trace["residual"]["candidates"] = {ref: {"features": [0.1 * (k + 1) for k in range(width)], "v_residual": 0.0}
                                       for ref in (STOP, "a")}
    trace["evaluation"] = {"window_days": 14, "uses": {"topics": [{"lo": lo, "c": c, "m0": None}
                                                                 for lo, c in population.items()], "dated": []}}
    return trace


def _pair(config, first_population, second_population, *, goals=None):
    width = len(LT.NAMES)
    carried = {"decision_id": "d1", "cutoff_days": repr(5.0), "status": "carried", "q_status": "valued",
               "q": {STOP: 0.7, "a": 0.9}, "features": {STOP: [0.2] * width, "a": [0.3] * width}}
    version = config.algorithms.algorithm_version
    first = TD._logged(None, {**_row("d1", "2026-10-01T10:00:00Z"), "algorithm_version": version},
                       _traced(first_population, goals=goals), config, FAR, False)
    second = TD._logged(None, {**_row("d2", "2026-10-01T11:00:00Z"), "algorithm_version": version},
                        _traced(second_population, goals=goals, previous=carried), config, FAR, False)
    return first, second


C = 1.0 / 90.0


def test_a_topic_entering_the_retention_scope_at_its_density_keeps_the_backup(monkeypatch, utc):
    _quiet(monkeypatch, {"d1": "d2"})
    on = _config()
    first, second = _pair(on, {"lo_a": C}, {"lo_a": C, "lo_new": C})
    steps = TD.transitions(None, on, [first, second], at=FAR)
    assert len(steps.transitions) == 1 and steps.censored == {TD.NO_LATER_DECISION: 1}
    assert first.objective == second.objective
    # The backup is the one the same two decisions give with no growth at all.
    same_first, same_second = _pair(on, {"lo_a": C}, {"lo_a": C})
    reference = TD.transitions(None, on, [same_first, same_second], at=FAR).transitions[0]
    kept = steps.transitions[0]
    assert (kept.reward, kept.next_v_tail, kept.next_phi, kept.phi, kept.q_taken) == (
        reference.reward, reference.next_v_tail, reference.next_phi, reference.phi, reference.q_taken)


def test_switched_off_or_below_the_tag_the_growth_is_a_change_point(monkeypatch, utc):
    _quiet(monkeypatch, {"d1": "d2"})
    for config in (_config(on=False), _config(ROUTER_LEARNED_TAIL_ALGORITHM_VERSION)):
        first, second = _pair(config, {"lo_a": C}, {"lo_a": C, "lo_new": C})
        steps = TD.transitions(None, config, [first, second], at=FAR)
        assert steps.transitions == () and steps.censored == {TD.OBJECTIVE_CHANGED: 1, TD.NO_LATER_DECISION: 1}


def test_codex_density_change_stays_censored_at_the_tag(monkeypatch, utc):
    """RO6's ruling R11: with no goals, a retention topic's density 0.1 -> 0.9 between two decisions."""

    _quiet(monkeypatch, {"d1": "d2"})
    on = _config()
    first, second = _pair(on, {"lo_r": 0.1}, {"lo_r": 0.9})
    steps = TD.transitions(None, on, [first, second], at=FAR)
    assert steps.transitions == () and steps.censored == {TD.OBJECTIVE_CHANGED: 1, TD.NO_LATER_DECISION: 1}
    # A new topic at another density than the scope's is a change too.
    first, second = _pair(on, {"lo_r": 0.1}, {"lo_r": 0.1, "lo_new": 0.5})
    assert TD.transitions(None, on, [first, second], at=FAR).transitions == ()


def test_goal_changes_stay_change_points_at_the_tag(monkeypatch, utc):
    _quiet(monkeypatch, {"d1": "d2"})
    on = _config()
    goal = {"g": {"dated": 10.0, "undated_density": 0.05, "per_lo": {}, "due_at": "2026-10-05T10:00:00Z",
                  "los": ["lo_g"]}}
    first, second = _pair(on, {"lo_a": C}, {"lo_a": C, "lo_g": 0.05})
    second_goal = TD._logged(None, {**_row("d2", "2026-10-01T11:00:00Z"), "algorithm_version": "mvp-0.50"},
                             _traced({"lo_a": C, "lo_g": 0.05}, goals=goal), on, FAR, False)
    assert first.objective != second_goal.objective
    # A goal's topic is the goal's, never a retention extension: the same populations without the goal differ too.
    assert first.objective != second.objective
    assert TD.objective_hash({}, 6.0, {"lo_a": C}, scope_extension=True) == TD.objective_hash(
        {}, 6.0, {"lo_a": C, "lo_b": C}, scope_extension=True)
    assert TD.objective_hash({}, 7.0, {"lo_a": C}, scope_extension=True) != TD.objective_hash(
        {}, 6.0, {"lo_a": C}, scope_extension=True)


def test_one_generator_version_across_a_growing_scope(monkeypatch, utc):
    on = _config()
    first, second = _pair(on, {"lo_a": C}, {"lo_a": C, "lo_b": C, "lo_c": C})
    assert first.generator == second.generator


@pytest.fixture
def utc(monkeypatch):
    import time

    monkeypatch.setenv("TZ", "UTC")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()

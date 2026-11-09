"""Each AD2+AD3 simulation scenario, run small: the model, the selection rule and the gate's figures work.

A gate's pass conditions are only meaningful at its pre-registered size, so they're not asserted here. They stay in
``tests/test_ad23_sim.py`` (the ``slow`` lane), which runs in every landing gate. This file catches a broken scenario
in seconds while iterating; each case seeds several learners so the figures are computed, not vacuous.
"""

from __future__ import annotations

import math

import pytest

from learnloop.adaptive_difficulty import priors as P
from learnloop.sim import ad_gates as G

_N = 12
_CASES = {
    "AD2-7": lambda: G.g_ad2_7(n=_N),
    "AD2-8": lambda: G.g_ad2_8(n=_N),
    "AD2-14": lambda: G.g_ad2_14(n=_N),
    "AD2-18 one_cell": lambda: G.g_ad2_18("one_cell", n=_N),
    "AD2-18 wrong_prior": lambda: G.g_ad2_18("wrong_prior", n=_N),
    "AD2-18 plan_flow": lambda: G.g_ad2_18("plan_flow", n=_N),
    "AD3-6": lambda: G.g_ad3_6(P.hyper_grid()[0], seeds=2),
    "AD3-7 practice": lambda: G.g_ad3_7("practice", "correct", n=_N),
    "AD3-7 reading": lambda: G.g_ad3_7("reading", "correct", n=_N),
    "AD3-7 shrink": lambda: G.g_ad3_7_shrink("wrong", n=_N),
    "AD3-8": lambda: G.g_ad3_8(n=_N),
    "AD3-9": lambda: G.g_ad3_9(seeds=_N, attempts=60),
    "AD3-11 base": lambda: G.g_ad3_11("base", n=_N),
    "AD3-11 confounding": lambda: G.g_ad3_11("confounding", n=_N),
    "AD3-15": lambda: G.g_ad3_15(n=_N),
}


def _numbers(value):
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        yield float(value)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _numbers(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _numbers(item)


@pytest.mark.parametrize("gate", _CASES, ids=str)
def test_the_scenario_runs_and_reports_its_conditions_and_finite_figures(gate):
    result = _CASES[gate]()
    conditions = result["pass"]
    assert conditions and all(type(value) is bool for value in conditions.values())
    figures = [number for key, value in result.items() if key != "pass" for number in _numbers(value)]
    assert figures, "a gate with no figures proves nothing"
    assert any(math.isfinite(number) for number in figures)

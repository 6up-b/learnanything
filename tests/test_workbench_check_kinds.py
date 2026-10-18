"""Reader workbench RW2b: each declared symbolic kind with its controls (spec_reader_workbench_v1 §5.3, G9, G38).

The fixed sympy harness runs in the real PF-b sandbox (skipped where
bubblewrap is missing; that path is ``test_workbench_check.py``'s). For every
declared kind a true claim is ``checked`` and holds, the same claim with a
wrong result is ``checked`` and does not hold (``≠``), and the result is
never trusted when its controls misbehave. Inequalities are sampled and
labelled ``checked_numerically``. Fakes only: no model.
"""

from __future__ import annotations

import pytest

from learnloop.content.authoring.pf_sandbox import sandbox_available
from learnloop.workbench.symbolic import CHECKED, CHECKED_NUMERICALLY, MODEL, SymbolicClaim, run_checks

needs_bwrap = pytest.mark.skipif(not sandbox_available(), reason="bubblewrap is not installed")

# (kind, true claim kwargs, the same claim with a wrong result)
CASES = [
    ("equivalence", dict(expression="(x+1)^2", result="x^2 + 2x + 1"), "x^2 + 2x"),
    ("differentiation", dict(expression="x**3", result="3*x**2", variable="x"), "3*x"),
    ("integration", dict(expression="exp(-t)", result="-exp(-t)", variable="t"), "exp(-t)"),
    ("integration", dict(expression="exp(-t)", result="1 - exp(-x)", variable="t", lower="0", upper="x"), "-exp(-x)"),
    ("substitution", dict(expression="1 - exp(-x)", result="0", variable="x", value="0"), "1"),
    ("solving", dict(expression="2*x + 4 = 0", result="-2", variable="x"), "2"),
    ("limit", dict(expression="sin(x)/x", result="1", variable="x", value="0"), "0"),
    ("sum", dict(expression="k", result="n*(n+1)/2", variable="k", lower="1", upper="n"), "n**2/2"),
    ("boundary", dict(expression="1 - exp(-x)", result="0", variable="x", value="0"), "-1"),
]


@needs_bwrap
@pytest.mark.parametrize("kind,claim,wrong", CASES)
def test_each_declared_kind_checks_a_true_claim_and_catches_a_wrong_one(kind, claim, wrong):
    good = SymbolicClaim(1, kind, **claim)
    bad = SymbolicClaim(2, kind, **{**claim, "result": wrong})
    outcomes, problem = run_checks([good, bad])
    assert problem is None
    assert [(o.method, o.holds) for o in outcomes] == [(CHECKED, True), (CHECKED, False)]


@needs_bwrap
def test_normalization_checks_a_density_integrating_to_one():
    outcomes, _problem = run_checks([
        SymbolicClaim(1, "normalization", "exp(-x)", "1", "x", lower="0", upper="oo"),
        SymbolicClaim(2, "normalization", "2*exp(-x)", "1", "x", lower="0", upper="oo"),
    ])
    assert [(o.method, o.holds) for o in outcomes] == [(CHECKED, True), (CHECKED, False)]


@needs_bwrap
def test_an_inequality_is_checked_numerically_and_labelled_so():
    outcomes, _problem = run_checks([
        SymbolicClaim(1, "inequality", "x**2", "0", "x", relation=">="),
        SymbolicClaim(2, "inequality", "x**2", "1", "x", relation=">="),
        SymbolicClaim(3, "inequality", "x**2", "0", "x", relation=""),
    ])
    assert [(o.method, o.holds) for o in outcomes] == [
        (CHECKED_NUMERICALLY, True), (CHECKED_NUMERICALLY, False), (MODEL, None)]


@needs_bwrap
def test_an_unparseable_claim_stays_the_models_reading():
    outcomes, _problem = run_checks([SymbolicClaim(1, "equivalence", "foo(", "x")])
    assert [(o.method, o.holds) for o in outcomes] == [(MODEL, None)]


@needs_bwrap
def test_an_indefinite_integral_is_checked_up_to_a_constant_with_a_negative_control_that_bites():
    # The antiderivative plus a constant still holds; the perturbed control
    # (one more times the variable) must be rejected, or nothing is trusted.
    outcomes, _problem = run_checks([SymbolicClaim(1, "integration", "2*x", "x**2 + 7", "x")])
    assert [(o.method, o.holds) for o in outcomes] == [(CHECKED, True)]


def test_without_bubblewrap_nothing_runs_and_every_claim_is_the_models_reading(monkeypatch):
    import learnloop.content.authoring.pf_sandbox as pf

    monkeypatch.setattr(pf, "_sandbox_bwrap_path", lambda: None)
    outcomes, problem = run_checks([SymbolicClaim(1, "equivalence", "x", "x")])
    assert problem == "sandbox_unavailable" and [(o.method, o.holds) for o in outcomes] == [(MODEL, None)]

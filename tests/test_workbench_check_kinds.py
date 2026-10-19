"""Reader workbench RW2b: each supported kind, checked on the learner's own LaTeX (spec_reader_workbench_v1 §5.3, G9, G38).

Fix round 3 (the orchestrator's ruling on F3): "checked" comes only from the
learner's written step, parsed by code from its LaTeX (sympy's ``lark``
backend). The declaration only picks the kind; its fields are compared with
the parse. The fixed sympy harness runs in the real PF-b sandbox (skipped
where bubblewrap is missing; that path is ``test_workbench_check.py``'s). For
every supported kind a correct written step is ``checked`` and holds, the
same step with a wrong right side is ``checked`` and does not hold (``≠``),
and the result is never trusted when its controls misbehave. Fakes only: no
model.
"""

from __future__ import annotations

import pytest

from learnloop.content.authoring.pf_sandbox import sandbox_available
from learnloop.workbench.symbolic import CHECKED, CHECKED_NUMERICALLY, MODEL, SymbolicClaim, run_checks

needs_bwrap = pytest.mark.skipif(not sandbox_available(), reason="bubblewrap is not installed")

# (kind, declaration, the learner's correct step, the same step with a wrong right side, context)
CASES = [
    ("equivalence", dict(expression="(x+1)^2", result="x^2 + 2x + 1"),
     r"(x+1)^2 = x^2 + 2x + 1", r"(x+1)^2 = x^2 + 2x", {}),
    ("differentiation", dict(expression="x**3", result="3*x**2", variable="x"),
     r"\frac{d}{dx}\left(x^3\right) = 3x^2", r"\frac{d}{dx}\left(x^3\right) = 3x^2 + 1", {}),
    ("integration", dict(expression="exp(-t)", result="-exp(-t)", variable="t"),
     r"\int \exp(-t)  dt = -\exp(-t)", r"\int \exp(-t)  dt = t - \exp(-t)", {}),
    ("integration", dict(expression="2*x", result="1", variable="x", lower="0", upper="1"),
     r"\int_0^1 2x  dx = 1", r"\int_0^1 2x  dx = 2", {}),
    ("normalization", dict(expression="2*x", result="1", variable="x", lower="0", upper="1"),
     r"\int_{0}^{1} 2x  dx = 1", None, {}),
    ("limit", dict(expression="x^2 + 1", result="5", variable="x", value="2"),
     r"\lim_{x \to 2} (x^2 + 1) = 5", r"\lim_{x \to 2} (x^2 + 1) = 4", {}),
    ("sum", dict(expression="k", result="n*(n+1)/2", variable="k", lower="1", upper="n"),
     r"\sum_{k=1}^{n} k = \frac{n \cdot (n+1)}{2}", r"\sum_{k=1}^{n} k = \frac{n \cdot (n+1)}{2} + 1", {}),
    ("solving", dict(expression="2*x + 4 = 0", result="-2", variable="x"),
     "x = -2", "x = 2", {"earlier": ("2x + 4 = 0",)}),
]


@needs_bwrap
@pytest.mark.parametrize("kind,declared,right,wrong,context", CASES)
def test_each_supported_kind_checks_a_correct_written_step_and_catches_a_wrong_one(kind, declared, right, wrong,
                                                                                   context):
    claims = [SymbolicClaim(1, kind, text=right, **declared, **context)]
    if wrong is not None:
        # The declaration's result is unset for the wrong step, so it agrees
        # with it too: only what the learner wrote decides.
        claims.append(SymbolicClaim(2, kind, text=wrong, **{**declared, "result": ""}, **context))
    outcomes, problem = run_checks(claims)
    assert problem is None
    expected = [(CHECKED, True)] + ([(CHECKED, False)] if wrong is not None else [])
    assert [(o.method, o.holds) for o in outcomes] == expected, [o.reason for o in outcomes]
    assert all(o.bound for o in outcomes)


@needs_bwrap
def test_a_definite_integral_with_other_declared_bounds_is_never_checked():
    outcomes, _problem = run_checks([
        SymbolicClaim(1, "integration", "2*x", "1", "x", lower="0", upper="2", text=r"\int_0^1 2x  dx = 1"),
        # A normalization must equal one; otherwise it is an integration.
        SymbolicClaim(2, "normalization", "2*x", "", "x", lower="0", upper="1", text=r"\int_0^1 2x  dx = 2"),
    ])
    assert [(o.method, o.holds, o.bound) for o in outcomes] == [(MODEL, None, False), (MODEL, None, False)]


@needs_bwrap
def test_substitution_and_a_primed_derivative_are_never_checked():
    # Fix round 6: names are never resolved (they stay the model's reading kinds).
    outcomes, _problem = run_checks([
        SymbolicClaim(1, "substitution", "x^2 + 1", "5", "x", value="2", text="f(2) = 5",
                      problem="Let $f(x) = x^2 + 1$."),
        SymbolicClaim(2, "differentiation", "x**3", "3*x**2", "x", text="f'(x) = 3x^2", earlier=("f(x) = x^3",)),
    ])
    assert [(o.method, o.holds, o.bound) for o in outcomes] == [(MODEL, None, False)] * 2


@needs_bwrap
def test_inequalities_and_boundaries_are_never_checked():
    outcomes, _problem = run_checks([
        SymbolicClaim(1, "inequality", "x**2", "0", "x", relation=">=", text="x^2 \\ge 0"),
        SymbolicClaim(2, "boundary", "x**2", "1", "x", value="1", text=r"\left. x^2 \right|_{x=1} = 1"),
    ])
    assert [(o.method, o.holds) for o in outcomes] == [(MODEL, None), (MODEL, None)]


@needs_bwrap
def test_an_unparseable_wordy_chained_or_bare_step_stays_the_models_reading():
    outcomes, _problem = run_checks([
        SymbolicClaim(1, "equivalence", "x", "x", text="x = (x"),
        SymbolicClaim(2, "equivalence", "x+x", "2*x", text="so x + x = 2x"),
        SymbolicClaim(3, "equivalence", "x+x", "2*x", text="x + x = 2x = 2x"),
        SymbolicClaim(4, "equivalence", "x+x", "2*x", text="x + x"),
    ])
    assert [(o.method, o.holds, o.bound) for o in outcomes] == [(MODEL, None, False)] * 4


@needs_bwrap
def test_an_antiderivative_is_checked_up_to_a_constant_with_a_negative_control_that_bites():
    # The antiderivative plus a constant still holds; the perturbed control
    # (one more times the variable) must be rejected, or nothing is trusted.
    outcomes, _problem = run_checks([
        SymbolicClaim(1, "integration", "2*x", "x**2 + 7", "x", text=r"\int 2x  dx = x^2 + 7"),
        SymbolicClaim(2, "integration", "2*x", "x**2 + C", "x", text=r"\int 2x  dx = x^2 + C"),
    ])
    assert [(o.method, o.holds) for o in outcomes] == [(CHECKED, True), (CHECKED, True)]


@needs_bwrap
def test_a_wrong_step_that_still_has_unknowns_is_never_said_not_to_follow():
    # (x - 2)(x + 2) = 0 is an equation to solve, not a false identity.
    outcomes, _problem = run_checks([
        SymbolicClaim(1, "equivalence", "(x-2)*(x+2)", "0", text="(x-2)(x+2) = 0"),
        SymbolicClaim(2, "equivalence", "0.1 + 0.2", "0.3", text="0.1 + 0.2 = 0.3"),
    ])
    assert [(o.method, o.holds) for o in outcomes] == [(MODEL, None), (CHECKED_NUMERICALLY, True)]


def test_without_bubblewrap_nothing_runs_and_every_claim_is_the_models_reading(monkeypatch):
    import learnloop.content.authoring.pf_sandbox as pf

    monkeypatch.setattr(pf, "_sandbox_bwrap_path", lambda: None)
    outcomes, problem = run_checks([SymbolicClaim(1, "equivalence", "x", "x", text="x = x")])
    assert problem == "sandbox_unavailable" and [(o.method, o.holds) for o in outcomes] == [(MODEL, None)]


@needs_bwrap
def test_a_root_of_an_equation_with_two_roots_is_checked_with_a_control_that_is_not_a_root():
    # The negative control skips the other root (x = 2 + 1 would not be one,
    # but x = 1 + 1 is), so a correct root is never refused by its control.
    outcomes, _problem = run_checks([
        SymbolicClaim(1, "solving", "x^2 - 3x + 2 = 0", "1", "x", text="x = 1", earlier=("x^2 - 3x + 2 = 0",)),
        SymbolicClaim(2, "solving", "x^2 - 3x + 2 = 0", "", "x", text="x = 3", earlier=("x^2 - 3x + 2 = 0",)),
        # Not the step before's equation: the declaration disagrees.
        SymbolicClaim(3, "solving", "x^2 - 4 = 0", "2", "x", text="x = 2", earlier=("x^2 - 3x + 2 = 0",)),
    ])
    assert [(o.method, o.holds) for o in outcomes] == [(CHECKED, True), (CHECKED, False), (MODEL, None)]

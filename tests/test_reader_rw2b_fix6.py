"""Reader workbench RW2b + hints H3, fix round 6: defined names are never resolved.

``docs/reviews/reader-rw2b-h3-codex-review.md``, "Fix round 6 (orchestrator)":
the ruling removes defined-name resolution from every "checked" path. A step
or a hint claim that applies a name as a function (``f(...)``, ``\\phi(...)``,
``g'(x)``) or writes a name the problem or an earlier step defines is the
model's reading, read from the syntax (``\\alpha`` and ``alpha`` one
identifier). A solve with any restriction token in its text or its equation
is the model's reading. Name-free steps of every remaining kind still check.

The real PF-b sandbox (skipped without bubblewrap); fakes only, no model.
"""

from __future__ import annotations

import pytest

from learnloop.content.authoring.pf_sandbox import sandbox_available
from learnloop.workbench.symbolic import CHECKED, MODEL, SymbolicClaim, run_checks
from tests.hint_fakes import ChooserFake, WriterFake, prefer
from tests.workbench_help_fakes import FUNCTION_FREE_PROMPT, call, open_problem, run_job, sidecar, wb_answer

pytestmark = pytest.mark.skipif(not sandbox_available(), reason="bubblewrap is not installed")


def _outcomes(*claims):
    outcomes, problem = run_checks(list(claims))
    assert problem is None
    return [(o.method, o.holds) for o in outcomes]


# -- The verify's four reproductions (Codex job 20261018-191835-vPxfGb) --------------------------


def test_a_greek_parameter_never_lets_a_restricted_definition_through():
    assert _outcomes(SymbolicClaim(1, "substitution", "alpha-1", "0", "alpha", value="1", text="f(1)=0",
                                   earlier=(r"f(\alpha)=\frac{(\alpha-1)^2}{\alpha-1}",))) == [(MODEL, None)]


def test_a_greek_function_name_is_a_name_too():
    assert _outcomes(
        SymbolicClaim(1, "substitution", "x-1", "0", "x", value="1", text=r"\phi(1)=0",
                      earlier=(r"\phi(x)=\frac{(x-1)^2}{x-1}",)),
        SymbolicClaim(2, "equivalence", "x-1", "x-1", text=r"\phi(x) = x - 1", earlier=(r"\phi(x)=x-1",)),
        # Written without its argument, a defined name is still a name.
        SymbolicClaim(3, "equivalence", "phi + 1", "phi + 1", text=r"\phi + 1 = 1 + \phi", earlier=(r"\phi(x)=x-1",)),
    ) == [(MODEL, None)] * 3


def test_a_fractional_power_redefinition_leaves_no_definition_in_force():
    assert _outcomes(SymbolicClaim(1, "substitution", "x", "4", "x", value="4", text="f(4)=4",
                                   earlier=("f(x)=x", r"f(x)=x^{\frac{1}{2}}"))) == [(MODEL, None)]


def test_a_nested_redefinition_leaves_no_definition_in_force():
    assert _outcomes(SymbolicClaim(1, "substitution", "x", "4", "x", value="4", text="f(4)=4",
                                   earlier=("g(x)=1/x", "f(x)=x", "f(x)=g(x)"))) == [(MODEL, None)]


def test_a_solve_with_any_restriction_token_is_never_checked_greek_included():
    assert _outcomes(
        SymbolicClaim(1, "solving", "alpha**2/alpha = 1", "1", "alpha", text=r"\alpha = 1",
                      earlier=(r"\frac{\alpha^2}{\alpha} = 1",)),
        # A restriction that involves no letter at all counts too (fix round 6).
        SymbolicClaim(2, "solving", "x/2 = 3", "6", "x", text="x = 6", earlier=(r"\frac{x}{2} = 3",)),
        SymbolicClaim(3, "solving", "x = 1/2", "1/2", "x", text=r"x = \frac{1}{2}", earlier=("2x = 1",)),
    ) == [(MODEL, None)] * 3


# -- Name-free steps of each remaining kind still check ------------------------------------------


def test_a_name_free_correct_step_of_each_remaining_kind_still_checks():
    assert _outcomes(
        SymbolicClaim(1, "equivalence", "alpha + alpha", "2*alpha", text=r"\alpha + \alpha = 2\alpha"),
        SymbolicClaim(2, "differentiation", "x**3", "3*x**2", "x", text=r"\frac{d}{dx}\left(x^3\right) = 3x^2"),
        SymbolicClaim(3, "integration", "2*x", "1", "x", lower="0", upper="1", text=r"\int_0^1 2x  dx = 1"),
        SymbolicClaim(4, "integration", "2*x", "x**2 + C", "x", text=r"\int 2x  dx = x^2 + C"),
        SymbolicClaim(5, "normalization", "3*x**2", "1", "x", lower="0", upper="1", text=r"\int_0^1 3x^2  dx = 1"),
        SymbolicClaim(6, "limit", "x^2 + 1", "5", "x", value="2", text=r"\lim_{x \to 2} (x^2 + 1) = 5"),
        SymbolicClaim(7, "sum", "k", "6", "k", lower="1", upper="3", text=r"\sum_{k=1}^{3} k = 6"),
        SymbolicClaim(8, "solving", "3*x - 6 = 12", "6", "x", text="x = 6", earlier=("3x - 6 = 12",)),
    ) == [(CHECKED, True)] * 8


# -- The hint-claim path: the same rules -----------------------------------------------------------


def _claim(step, statement, **values):
    base = {"kind": "", "expression": "", "result": "", "variable": "", "value": "", "lower": "", "upper": "",
            "relation": ""}
    return {"step": step, "statement": statement, **base, **values}


def _hint_claims(tmp_path, steps, claim):
    writer = WriterFake([lambda context: {**wb_answer(context), "claims": [claim]}, wb_answer])
    _paths, ctx, _session = sidecar(tmp_path, prompt=FUNCTION_FREE_PROMPT, symbolic=True,
                                    writer=writer, chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    wb, _chains = open_problem(ctx, steps=tuple(steps))
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    return [entry["status"] for entry in hint["claims"]]


def test_a_hints_claim_through_a_greek_function_name_is_never_checked(tmp_path):
    claim = _claim(1, r"\phi(1) = 0", kind="substitution", expression="x-1", result="0", variable="x", value="1")
    assert _hint_claims(tmp_path, [r"\phi(x)=\frac{(x-1)^2}{x-1}"], claim) == ["model"]


def test_a_hints_claim_through_a_redefined_name_is_never_checked(tmp_path):
    claim = _claim(2, "f(4) = 4", kind="substitution", expression="x", result="4", variable="x", value="4")
    assert _hint_claims(tmp_path, ["f(x)=x", r"f(x)=x^{\frac{1}{2}}"], claim) == ["model"]


def test_a_hints_name_free_claim_still_checks(tmp_path):
    claim = _claim(1, r"\int_0^1 2x  dx = 1", kind="integration", expression="2*x", result="1", variable="x",
                   lower="0", upper="1")
    assert _hint_claims(tmp_path, [r"\int_0^1 2x  dx = 1"], claim) == ["checked"]

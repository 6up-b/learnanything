"""Reader workbench RW2b + hints H3, fix round 8: function notation disables the problem; strict step text.

``docs/reviews/reader-rw2b-h3-codex-review.md``, "Fix round 8 (orchestrator)":

1. the problem's full text (prose included) and every earlier step are
   normalised (whitespace, spacing commands, ``~``, braces, formatting
   commands, ``\\left.``/``\\right.`` out); if any letter (Unicode) or command
   other than the parser's built-ins is then followed by ``(``, ``[``, ``'``,
   ``\\prime`` or ``^\\prime``, every step and hint claim on the problem is the
   model's reading;
2. the checked text itself is ASCII and writes only allow-listed commands
   (spacing commands refuse);
3. a solve is checked only against the immediately preceding LEARNER step: a
   first step that solves is the model's reading.

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


def _derivative_of(name, *, earlier=(), problem=""):
    command = "\\" + name if len(name) > 1 else name
    return SymbolicClaim(1, "differentiation", name, "0", "x", text=r"\frac{d}{dx}(" + command + ")=0",
                         earlier=tuple(earlier), problem=problem)


# -- Rule 1: the verify's reproductions (Codex job 20261018-201040-6YibdJ) ------------------------


@pytest.mark.parametrize("definition", [r"f\!(x)=x", r"f\,(x)=x", r"f\;(x)=x", "{f}(x)=x", r"f\left.(x)=x"])
def test_a_spaced_grouped_or_left_dotted_definition_disables_the_problem(definition):
    assert _outcomes(_derivative_of("f", earlier=[definition])) == [(MODEL, None)]


def test_a_unicode_or_prose_function_disables_the_problem():
    assert _outcomes(
        _derivative_of("alpha", earlier=["α(x)=x"]),
        _derivative_of("alpha", problem="Let alpha(x)=x."),
        # Prose before a bracket counts too (over-matching is intended).
        _derivative_of("g", problem="The density is g (x) on the unit interval."),
        _derivative_of("g", problem="Work on [0, 1]."),
    ) == [(MODEL, None)] * 4


# -- Rule 3: no first-step solve against the problem --------------------------------------------


@pytest.mark.parametrize("problem", [r"Solve $2x=0$ and $\frac{x^2}{x}=0$.", "Solve $2x=0$ subject to $x>0$.",
                                     "Solve $2x = 0$."])
def test_a_first_step_that_solves_is_never_checked_against_the_problem(problem):
    assert _outcomes(SymbolicClaim(1, "solving", "2*x", "0", "x", text="x=0", problem=problem)) == [(MODEL, None)]


# -- Rule 2: the checked text itself is strict ------------------------------------------------------


def test_a_step_with_a_spacing_command_or_non_ascii_text_is_never_checked():
    assert _outcomes(
        SymbolicClaim(1, "integration", "2*x", "1", "x", lower="0", upper="1", text=r"\int_0^1 2x \, dx = 1"),
        SymbolicClaim(2, "equivalence", "x + x", "2*x", text=r"x \! + x = 2x"),
        SymbolicClaim(3, "equivalence", "alpha + alpha", "2*alpha", text="α + α = 2α"),
        SymbolicClaim(4, "equivalence", "x + x", "2*x", text="x + x = 2x~"),
    ) == [(MODEL, None)] * 4


# -- Positive controls: a function-free problem still checks -----------------------------------------


def test_name_free_steps_on_a_function_free_problem_still_check():
    problem = FUNCTION_FREE_PROMPT
    assert _outcomes(
        SymbolicClaim(1, "equivalence", "(x+1)**2", "x**2 + 2*x + 1", text="(x+1)^2 = x^2 + 2x + 1", problem=problem),
        SymbolicClaim(2, "differentiation", "x**3", "3*x**2", "x", text=r"\frac{d}{dx}\left(x^3\right) = 3x^2",
                      problem=problem),
        SymbolicClaim(3, "integration", "2*x", "1", "x", lower="0", upper="1", text=r"\int_0^1 2x dx = 1",
                      problem=problem),
        SymbolicClaim(4, "integration", "2*x", "x**2 + C", "x", text=r"\int 2x dx = x^2 + C", problem=problem),
        SymbolicClaim(5, "normalization", "3*x**2", "1", "x", lower="0", upper="1", text=r"\int_0^1 3x^2 dx = 1",
                      problem=problem),
        SymbolicClaim(6, "limit", "x^2 + 1", "5", "x", value="2", text=r"\lim_{x \to 2} (x^2 + 1) = 5",
                      problem=problem),
        SymbolicClaim(7, "sum", "k", "6", "k", lower="1", upper="3", text=r"\sum_{k=1}^{3} k = 6", problem=problem),
        SymbolicClaim(8, "solving", "3*x - 6 = 12", "6", "x", text="x = 6", earlier=("3x - 6 = 12",),
                      problem=problem),
    ) == [(CHECKED, True)] * 8


# -- The hint-claim path: the same rules -------------------------------------------------------------


def _wire(step, statement, **values):
    base = {"kind": "", "expression": "", "result": "", "variable": "", "value": "", "lower": "", "upper": "",
            "relation": ""}
    return {"step": step, "statement": statement, **base, **values}


def _hint_claims(tmp_path, steps, claim, *, prompt=FUNCTION_FREE_PROMPT):
    writer = WriterFake([lambda context: {**wb_answer(context), "claims": [claim]}, wb_answer])
    _paths, ctx, _session = sidecar(tmp_path, prompt=prompt, writer=writer,
                                    chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    wb, _chains = open_problem(ctx, steps=tuple(steps))
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    return [entry["status"] for entry in hint["claims"]]


INTEGRAL = _wire(2, r"\int_0^1 2x dx = 1", kind="integration", expression="2*x", result="1", variable="x",
                 lower="0", upper="1")


def test_a_hints_claim_after_a_spaced_definition_is_never_checked(tmp_path):
    claim = _wire(2, r"\frac{d}{dx}(g)=0", kind="differentiation", expression="g", result="0", variable="x")
    assert _hint_claims(tmp_path, [r"g\!(x)=x", "x = x"], claim) == ["model"]


def test_a_hints_claim_on_a_problem_with_function_notation_is_never_checked(tmp_path):
    # The CDF item's problem writes f(x) and P(X <= 1/2).
    assert _hint_claims(tmp_path, ["x^2 = x^2", "2x = 2x"], INTEGRAL, prompt=None) == ["model"]


def test_a_hints_first_step_solve_claim_is_never_checked(tmp_path):
    claim = _wire(1, "x = 6", kind="solving", expression="2*x = 12", result="6", variable="x")
    assert _hint_claims(tmp_path, ["x = 6", "x = x"], claim, prompt="Solve $2x = 12$ for the unknown.") == ["model"]


def test_a_hints_name_free_claim_on_a_function_free_problem_still_checks(tmp_path):
    assert _hint_claims(tmp_path, ["x^2 = x^2", "2x = 2x"], INTEGRAL) == ["checked"]

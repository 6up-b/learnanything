"""Reader workbench RW2b + hints H3, fix round 7: blunt, syntactic name and solve rules.

``docs/reviews/reader-rw2b-h3-codex-review.md``, "Fix round 7 (orchestrator)":

1. a step or hint claim is the model's reading if its own text writes a
   formatting (or any unlisted) command or a subscript on an identifier, or
   if any identifier it writes is a NAME: one written before ``(`` (allowing
   whitespace, ``\\left``, a subscript or primes) or with a prime, anywhere
   in the problem, an earlier step or the text itself, canonical (formatting
   off, ``\\alpha`` is ``alpha``, a subscript dropped to its base letter);
2. a solve step is checked only against the IMMEDIATELY preceding step's one
   relation, with no restriction token there (or, for a first step, the
   problem's single equation), never an older one.

The real PF-b sandbox (skipped without bubblewrap); fakes only, no model.
"""

from __future__ import annotations

import pytest

from learnloop.content.authoring.pf_sandbox import sandbox_available
from learnloop.workbench.symbolic import CHECKED, MODEL, SymbolicClaim, run_checks
from tests.hint_fakes import ChooserFake, WriterFake, prefer
from tests.workbench_help_fakes import call, open_problem, run_job, sidecar, wb_answer

pytestmark = pytest.mark.skipif(not sandbox_available(), reason="bubblewrap is not installed")

DERIVATIVE_OF_F = dict(kind="differentiation", expression="f", result="0", variable="x", text=r"\frac{d}{dx}(f)=0")


def _outcomes(*claims):
    outcomes, problem = run_checks(list(claims))
    assert problem is None
    return [(o.method, o.holds) for o in outcomes]


def _claim(index, earlier=(), **values):
    return SymbolicClaim(index, values.pop("kind"), values.pop("expression"), values.pop("result"),
                         earlier=tuple(earlier), **values)


# -- Rule 1: names (the verify's reproductions, Codex job 20261018-193340-5s348l) ---------------


@pytest.mark.parametrize("definition", ["f(x_1)=x_1", "f_1(x)=x", r"\mathrm{f}(x)=x", r"\operatorname{f}(x)=x"])
def test_a_subscripted_or_formatted_definition_still_makes_its_name_a_name(definition):
    assert _outcomes(_claim(1, [definition], **DERIVATIVE_OF_F)) == [(MODEL, None)]


def test_a_text_that_formats_or_subscripts_is_never_checked():
    assert _outcomes(
        _claim(1, kind="equivalence", expression="x + 1", result="1 + x", text=r"\mathrm{x} + 1 = 1 + x"),
        _claim(2, kind="equivalence", expression="x_1 + x_1", result="2*x_1", text="x_1 + x_1 = 2x_1"),
        _claim(3, kind="equivalence", expression="x + 1", result="1 + x", text=r"\mathbf{x} + 1 = 1 + \mathbf{x}"),
        _claim(4, kind="equivalence", expression="alpha_1", result="alpha_1", text=r"\alpha_1 = \alpha_1"),
    ) == [(MODEL, None)] * 4


def test_a_primed_or_applied_identifier_anywhere_is_a_name():
    assert _outcomes(
        # A prime in an earlier step.
        _claim(1, ["g' = 2"], kind="differentiation", expression="g", result="0", variable="x",
               text=r"\frac{d}{dx}(g)=0"),
        # Applied in the problem's prose.
        _claim(2, kind="differentiation", expression="h", result="0", variable="x", text=r"\frac{d}{dx}(h)=0",
               problem="Let h (x) be the height."),
        # Applied with \left( in an earlier step.
        _claim(3, [r"F\left(x\right) = x"], kind="equivalence", expression="F + 1", result="1 + F",
               text="F + 1 = 1 + F"),
    ) == [(MODEL, None)] * 3


# -- Rule 2: solve against the immediately preceding step only -------------------------------------


@pytest.mark.parametrize("fraction", ["frac", "dfrac", "tfrac"])
def test_a_solve_never_skips_a_restricted_preceding_equation(fraction):
    # The verify's reproduction: 2x=0, \frac{x^2}{x}=0, x=0 (undefined at 0).
    steps = ["2x=0", "\\" + fraction + "{x^2}{x}=0"]
    assert _outcomes(_claim(1, steps, kind="solving", expression="2*x", result="0", variable="x",
                            text="x=0")) == [(MODEL, None)]


def test_a_solve_checks_only_against_the_immediately_preceding_step():
    assert _outcomes(
        _claim(1, ["2x = 12", "y = 1"], kind="solving", expression="2*x = 12", result="6", variable="x",
               text="x = 6"),
        _claim(2, ["y = 1", "2x = 12"], kind="solving", expression="2*x = 12", result="6", variable="x",
               text="x = 6"),
        _claim(3, [], kind="solving", expression="2*x = 12", result="6", variable="x", text="x = 6",
               problem="Solve $2x = 12$."),
    ) == [(MODEL, None), (CHECKED, True), (CHECKED, True)]


# -- Positive controls: name-free steps of each kind still check -------------------------------------


def test_name_free_steps_of_each_kind_still_check():
    assert _outcomes(
        _claim(1, kind="equivalence", expression="(x+1)**2", result="x**2 + 2*x + 1", text="(x+1)^2 = x^2 + 2x + 1"),
        _claim(2, kind="differentiation", expression="x**3", result="3*x**2", variable="x",
               text=r"\frac{d}{dx}\left(x^3\right) = 3x^2"),
        _claim(3, kind="integration", expression="2*x", result="1", variable="x", lower="0", upper="1",
               text=r"\int_0^1 2x \, dx = 1"),
        _claim(4, kind="integration", expression="2*x", result="x**2 + C", variable="x", text=r"\int 2x \, dx = x^2 + C"),
        _claim(5, kind="normalization", expression="3*x**2", result="1", variable="x", lower="0", upper="1",
               text=r"\int_0^1 3x^2 \, dx = 1"),
        _claim(6, kind="limit", expression="x^2 + 1", result="5", variable="x", value="2",
               text=r"\lim_{x \to 2} (x^2 + 1) = 5"),
        _claim(7, kind="sum", expression="k", result="6", variable="k", lower="1", upper="3", text=r"\sum_{k=1}^{3} k = 6"),
        _claim(8, ["3x - 6 = 12"], kind="solving", expression="3*x - 6 = 12", result="6", variable="x", text="x = 6"),
    ) == [(CHECKED, True)] * 8


# -- The hint-claim path: the same rules -----------------------------------------------------------


def _hint_claims(tmp_path, steps, claim):
    writer = WriterFake([lambda context: {**wb_answer(context), "claims": [claim]}, wb_answer])
    _paths, ctx, _session = sidecar(tmp_path, writer=writer, chooser=ChooserFake(prefer("next_step@L3", 0.9)))
    wb, _chains = open_problem(ctx, steps=tuple(steps))
    hint = run_job(ctx, call(ctx, "workbench.request_help", {"sessionId": wb, "takenLevel": 3}))
    return [entry["status"] for entry in hint["claims"]]


def _wire(step, statement, **values):
    base = {"kind": "", "expression": "", "result": "", "variable": "", "value": "", "lower": "", "upper": "",
            "relation": ""}
    return {"step": step, "statement": statement, **base, **values}


@pytest.mark.parametrize("definition", ["g_1(x)=x", r"\operatorname{g}(x)=x"])
def test_a_hints_claim_about_a_formatted_or_subscripted_name_is_never_checked(tmp_path, definition):
    # g, not f: the fixture's problem already applies f ("density f(x) = 2x").
    claim = _wire(1, r"\frac{d}{dx}(g)=0", kind="differentiation", expression="g", result="0", variable="x")
    assert _hint_claims(tmp_path, [definition], claim) == ["model"]


def test_a_hints_solve_claim_uses_the_step_just_before_its_step(tmp_path):
    claim = _wire(2, "x = 6", kind="solving", expression="2*x = 12", result="6", variable="x")
    assert _hint_claims(tmp_path / "a", ["2x = 12", "x = 6"], claim) == ["checked"]
    restricted = _wire(3, "x = 0", kind="solving", expression="2*x", result="0", variable="x")
    assert _hint_claims(tmp_path / "b", ["2x=0", r"\tfrac{x^2}{x}=0", "x = 0"], restricted) == ["model"]

"""Reader RW5c: the exact check (spec §5.1-§5.2, §6; G23a-G23c, G23f, the planted-wrong corpus of §14).

The check runs in the real sandbox here (skipped without bubblewrap); a fake-sandbox twin at the end
tests the fail-closed paths. Every model is a fake, and the check itself never calls one.
"""

from __future__ import annotations

from typing import Any

import pytest

from learnloop.content.authoring import pf_sandbox
from learnloop.figures import service as FS
from learnloop.figures import source_check as SC
from learnloop.figures import spec as S
from learnloop.vault.loader import load_vault
from tests.figure_fixtures import AuthorFake, build, call, context, rows, set_config
from tests.rw5c_fixtures import EXTRACTION, FLAGSHIP_EXPR, FLAGSHIP_TEX, HALF_EXPR, PARAMETERS, build_check_vault, plot

sandboxed = pytest.mark.skipif(not pf_sandbox.sandbox_available(), reason="needs bubblewrap")
BLOCKS = [
    ("s1", "Text", f"The density is $${FLAGSHIP_TEX}$$ for a mixture."),
    ("s2", "Text", r"Then $f(x)=x$ and $g(x)=2x$ both hold here."),
    ("s3", "Text", r"Cancelled: $f(x)=\frac{x^2 - \frac{1}{16384}}{x - \frac{1}{128}}$."),
    ("s4", "Text", r"Computed exponent: $f(x)=x + (x - \frac{1}{128})^{1+1}$."),
    ("s5", "Text", r"Plain: $f(x)=x$."),
    ("s6", "Text", r"Cube root: $f(x)=x^{1/3}$."),
    ("s7", "Text", r"Power: $f(x)=x^{n}$."),
    ("s8", "Text", r"Positive base: $f(k)=\lambda^{k}$."),
    ("s9", "Text", r"Scale: $f(x)=\frac{x}{\sigma}$."),
    ("s10", "Text", r"Ratio: $f(x)=\frac{1-\cos(x)}{x^2}$."),
    ("s11", "Text", r"Zero: $f(x)=0 \cdot x$."),
    ("s12", "Text", r"Cancels: $f(x)=1 + x - x$."),
    ("s13", "Text", r"Rates: $f(x)=p \lambda x$."),
    ("s14", "Text", r"Unreadable: $f(x)=\Phi(x)$ and $g(x)=\binom{n}{x}$."),
    ("s15", "Text", "Unicode: 𝑓(𝑥) = 𝜆𝑥."),
    ("s16", "Text", r"A parameter's scale: $f(x)=\frac{x}{a}$."),
    ("s17", "Text", r"Half first: "),
    ("s18", "Text", r"then half second $f(x)=x$ continues."),
    ("s19", "Text", r"Sum body: $f(k)=\frac{1}{k+1}$."),
    ("s20", "Text", r"A condition on a parameter: $f(x)=\begin{cases} x & p < 0.5 \\ 1 & \text{otherwise} \end{cases}$."),
    ("s21", "Text", r"Half: $f(x)=x + \frac{1}{4}$."),
]


@pytest.fixture(scope="module")
def book(tmp_path_factory) -> tuple[Any, Any]:
    paths, repository = build_check_vault(tmp_path_factory.mktemp("rw5c") / "vault", BLOCKS)
    return load_vault(paths.root), repository


def check(book: tuple[Any, Any], spec: dict[str, Any], *spans: str, grounding: str = "anchor", **kwargs: Any) -> SC.Check:
    vault, repository = book
    return SC.check_figure(vault, repository, S.parse_spec(spec),
                           spans=[(EXTRACTION, span, span) for span in spans], grounding=grounding, **kwargs)


def entry(result: SC.Check, name: str = "f") -> dict[str, Any]:
    return next(item for item in result.definitions if item["name"] == name)


def roles(result: SC.Check) -> dict[str, str]:
    return {element["id"]: element["role"] for element in result.elements}


# -- G45, the flagship ----------------------------------------------------------------------------

@sandboxed
def test_the_flagship_density_is_checked_with_display_agreement_over_its_grid(book):
    result = check(book, plot(FLAGSHIP_EXPR, parameters=PARAMETERS, low=-3, high=3), "s1")
    assert result.outcome == SC.CHECKED and result.reasons == {}
    found = entry(result)
    assert found["candidate"]["lhs"] == "f(x)" and found["candidate"]["page"] == 87
    assert found["candidate"]["block_health"]["status"] == "ok"
    assert found["display"]["panels.0.series.0"] == {"samples": 9 * 121, "agreed": True}
    assert set(found["controls"]) <= {"different", "undecided"} and len(found["controls"]) == 5
    assert roles(result)["panels.0.series.0"] == "book"
    assert roles(result)["parameters.1"] == "symbol"
    assert result.sympy_version


@sandboxed
def test_the_half_density_with_a_stated_claim_differs_and_names_where(book):
    result = check(book, plot(HALF_EXPR, parameters=PARAMETERS, low=-3, high=3, stated="f(x)", span="s1"), "s1")
    assert result.outcome == SC.DIFFERS and not result.book_elements and result.elements == []
    assert "your definition f differs from the quoted equation at" in result.problems[0]
    assert "x = -3" in result.problems[0]


def test_with_its_invariant_the_half_density_is_still_refused_at_step_two():
    from learnloop.figures import verify as V

    declared = {"kind": "integrates_to_one", "expr": "f", "var": "x", "from": -40, "to": 40}
    spec = plot(HALF_EXPR, parameters=PARAMETERS, low=-3, high=3, invariants=[declared])
    assert V.verify_numerics(S.parse_spec(spec)).outcome == V.FAILED


# -- the controls ------------------------------------------------------------------------------------

@sandboxed
@pytest.mark.parametrize("expr, span", [("0*x", "s11"), ("1 + x - x", "s12")])
def test_a_degenerate_definition_or_a_symbol_that_cancels_breaks_the_controls(book, expr, span):
    result = check(book, plot(expr), span)
    assert result.outcome == SC.UNDECIDED and entry(result)["reason"] == "control_accepted"
    assert "control_accepted" in result.reasons and not result.book_elements


# -- each prerequisite on its own ---------------------------------------------------------------------

@sandboxed
def test_a_renamed_parameter_is_names_and_the_sandbox_is_not_asked(book):
    def never(*_args: Any, **_kwargs: Any):
        raise AssertionError("the sandbox is not asked")

    renamed = [{**PARAMETERS[0], "name": "w"}, PARAMETERS[1]]
    expr = FLAGSHIP_EXPR.replace("p*", "w*").replace("(1 - p)", "(1 - w)")
    result = check(book, plot(expr, parameters=renamed, low=-3, high=3), "s1", sandbox=never)
    assert result.outcome == SC.NOT_CHECKABLE and entry(result)["reason"] == "names"


def test_an_inline_copy_is_not_a_bare_reference_and_gets_role_ai(book):
    spec = plot("x")
    spec["panels"][0]["series"][0]["expr"] = "x"
    result = check(book, spec, "s5")
    assert result.outcome == SC.NOT_CHECKABLE and entry(result)["reason"] == "not_bare"


@sandboxed
def test_twice_the_checked_definition_under_its_label_is_ai(book):
    spec = plot("x")
    spec["panels"][0]["series"] = [{"expr": "f", "label": "f(x)"}, {"expr": "2*f", "label": "f(x) again"}]
    result = check(book, spec, "s5")
    assert roles(result)["panels.0.series.0"] == "book"
    other = next(element for element in result.elements if element["id"] == "panels.0.series.1")
    assert other["role"] == "ai" and other["voice"] == "model" and "f(x)" not in other["tex"]


@pytest.mark.parametrize("expr", ["sin(10000000000000001*x)", "0.3*x", "1234567890123456789012345678901*x"])
def test_an_inexact_literal_is_not_checkable(book, expr):
    result = check(book, plot(expr), "s5")
    assert result.outcome == SC.NOT_CHECKABLE and entry(result)["reason"] == "inexact_literal"


def test_a_computed_condition_is_not_checkable(book):
    result = check(book, plot("piecewise((p*10 < 3, x), 1)", parameters=[PARAMETERS[0]]), "s5")
    assert entry(result)["reason"] == "inexact_condition"


@sandboxed
def test_an_exact_condition_passes_and_name_against_name_is_undecided(book):
    passes = check(book, plot("piecewise((x < 0.5, x), x)"), "s5")
    assert passes.outcome == SC.CHECKED
    against = check(book, plot("piecewise((x < p, x), x)", parameters=[PARAMETERS[0]]), "s5")
    assert entry(against)["reason"] in ("names", "parametric_breakpoint")
    named = check(book, plot(r"piecewise((x < p, p*lambda*x), p*lambda*x)", parameters=PARAMETERS), "s13")
    assert named.outcome == SC.UNDECIDED and entry(named)["reason"] == "parametric_breakpoint"


@sandboxed
def test_a_book_condition_on_a_parameter_is_undecided(book):
    result = check(book, plot("piecewise((p < 0.5, x), 1)", parameters=[PARAMETERS[0]]), "s20")
    assert result.outcome == SC.UNDECIDED and entry(result)["reason"] == "parametric_breakpoint"


@pytest.mark.parametrize("expr", ["integral(t, t, 0, x)", "floor(x)", "piecewise((x == 0, 1), x)", "piecewise((x != 0, 1), x)",
                                  "sum(k, k, 0, 2)*x"])
def test_integral_floor_equality_and_sum_are_not_checkable(book, expr):
    result = check(book, plot(expr), "s5")
    assert entry(result)["reason"] == "inexact_construct"


# -- which blocks may be read -------------------------------------------------------------------------

def test_a_block_that_is_not_ok_is_refused_with_its_reason(tmp_path):
    paths, repository = build_check_vault(tmp_path / "vault", [("a", "Text", "$f(x)=x$")], geometry=False)
    vault = load_vault(paths.root)
    result = SC.check_figure(vault, repository, S.parse_spec(plot("x")), spans=[(EXTRACTION, "a", "a")], grounding="anchor")
    assert result.outcome == SC.NOT_CHECKABLE and result.reasons.get("block_health") == 1
    # Computed at check time and stored, as reader.block_health does; never assumed ok.
    assert repository.block_health(EXTRACTION, "a")["status"] == "suspect"


def test_an_unbraced_radical_never_certifies_the_meaning_the_page_does_not_show(tmp_path):
    """Codex review F1: KaTeX shows \\sqrt16 x as sqrt(1)*6x. Read whole, it would prove 4*x "checked"."""

    paths, repository = build_check_vault(tmp_path / "vault", [("a", "Text", r"$f(x)=\sqrt16 x$")])
    result = check((load_vault(paths.root), repository), plot("4*x", stated="f(x)", span="a"), "a")
    assert not result.book_elements and result.outcome == SC.NOT_CHECKABLE
    assert result.reasons.get("function_arg") == 1


def test_a_withheld_span_is_never_read(tmp_path):
    paths, repository = build_check_vault(tmp_path / "vault", [("a", "Text", "$f(x)=x$")], source="src_exam2", revision="rev_exam2",
                                          extra_members=())
    from learnloop.vault.writer import upsert_source_set

    upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra", "title": "x", "members": [
        {"source_id": "src_exam2", "revision_id": "rev_exam2", "default_role": "exam"}]})
    vault = load_vault(paths.root)
    result = SC.check_figure(vault, repository, S.parse_spec(plot("x")), spans=[(EXTRACTION, "a", "a")], grounding="anchor")
    assert result.outcome == SC.NOT_CHECKABLE and result.reasons.get("block_withheld") == 1


def test_a_quote_across_two_blocks_points_at_no_candidate(book):
    # The quote is in neither block alone: no stated candidate, and the reason is recorded.
    spec = plot("x", stated="Half first: then half second", span="s17")
    result = check(book, spec, "s17", "s18", sandbox=lambda *a, **k: pf_sandbox.SandboxResult(False, error="off"))
    assert result.reasons.get("quote_across_blocks") == 1 and not result.book_elements


def test_unicode_math_is_never_a_candidate(book):
    result = check(book, plot("x"), "s15")
    assert result.outcome == SC.NOT_CHECKABLE and result.reasons.get("unicode_math") == 1


def test_an_unreadable_candidate_counts_its_reason(book):
    result = check(book, plot("x"), "s14")
    assert result.reasons.get("phi") == 1 and result.reasons.get("binom") == 1


# -- the fail-closed paths: fake sandboxes ------------------------------------------------------------------

def _fake(output: Any = None, **result: Any):
    def run(_harness: str, payload: dict[str, Any], **_kwargs: Any) -> pf_sandbox.SandboxResult:
        built = output(payload) if callable(output) else output
        return pf_sandbox.SandboxResult(result.get("ok", True), output=built, timed_out=result.get("timed_out", False),
                                        error=result.get("error"))

    return run


def _answer(payload: dict[str, Any], **fields: Any) -> dict[str, Any]:
    definition = payload["definitions"][0]
    pair = definition["pairs"][0]
    return {"sympy_version": "fake", "results": [{"definition": definition["name"], "candidate": pair["candidate"], **fields}]}


def test_no_bubblewrap_checks_nothing(book):
    result = check(book, plot("x"), "s5", sandbox_ready=lambda: False)
    assert result.outcome == SC.NOT_CHECKABLE and result.reasons == {"sandbox_unavailable": 1} and not result.book_elements


def test_a_sandbox_that_raises_unavailable_checks_nothing(book):
    def missing(*_args: Any, **_kwargs: Any):
        raise pf_sandbox.SandboxUnavailable("no bwrap")

    result = check(book, plot("x"), "s5", sandbox=missing)
    assert result.outcome == SC.NOT_CHECKABLE and result.reasons == {"sandbox_unavailable": 1}


def test_a_timeout_or_a_failed_run_checks_nothing(book):
    timed = check(book, plot("x"), "s5", sandbox=_fake(ok=False, timed_out=True, error="timed out"))
    assert timed.outcome == SC.UNDECIDED and timed.reasons == {"timeout": 1} and not timed.book_elements
    failed = check(book, plot("x"), "s5", sandbox=_fake(ok=False, error="exit 1"))
    assert failed.outcome == SC.UNDECIDED and failed.reasons == {"sandbox_failed": 1}
    junk = check(book, plot("x"), "s5", sandbox=_fake(output=["not a mapping"]))
    assert junk.outcome == SC.UNDECIDED and not junk.book_elements


@pytest.mark.parametrize("controls", [None, [], [None], [0], [""], ["different", True]])
def test_an_inconclusive_control_is_never_checked(book, controls):
    display = {"panels.0.series.0": {"samples": 1, "agreed": True}}
    result = check(book, plot("x"), "s5", sandbox=_fake(lambda payload: _answer(
        payload, result="equal", controls=controls, display=display)))
    assert result.outcome == SC.UNDECIDED and "control_inconclusive" in result.reasons and not result.book_elements


@pytest.mark.parametrize("answer", ["EQUAL", True, 1, None, ""])
def test_an_answer_outside_the_closed_results_is_undecided(book, answer):
    display = {"panels.0.series.0": {"samples": 1, "agreed": True}}
    result = check(book, plot("x"), "s5", sandbox=_fake(lambda payload: _answer(
        payload, result=answer, controls=["different"], display=display)))
    assert result.outcome == SC.UNDECIDED and not result.book_elements


@pytest.mark.parametrize("agreement", [None, {"agreed": "yes"}, {"agreed": 1}, {"agreed": False, "samples": 3}])
def test_only_a_real_true_counts_as_display_agreement(book, agreement):
    display = {} if agreement is None else {"panels.0.series.0": agreement}
    result = check(book, plot("x"), "s5", sandbox=_fake(lambda payload: _answer(
        payload, result="equal", controls=["different"], display=display)))
    assert not result.book_elements and "display_disagrees" in result.reasons


# -- display agreement ---------------------------------------------------------------------------------

@sandboxed
def test_catastrophic_floating_point_near_zero_is_display_disagrees(book):
    result = check(book, plot("(1 - cos(x))/x^2", low=1e-9, high=1e-8), "s10")
    assert result.outcome == SC.CHECKED and result.reasons.get("display_disagrees") == 1
    assert not result.book_elements and roles(result) == {}


@sandboxed
def test_two_definitions_get_per_element_roles(book):
    spec = plot("", definitions=[{"name": "f", "expr": "x"}, {"name": "h", "expr": "2*x"}, {"name": "m", "expr": "x^3"}])
    spec["panels"][0]["series"] = [{"expr": "f", "label": "one"}, {"expr": "h", "label": "two"}, {"expr": "m", "label": "three"}]
    result = check(book, spec, "s2")
    # f and h each match a candidate; m matches none and stays the model's.
    assert entry(result, "f")["outcome"] == SC.CHECKED and entry(result, "h")["outcome"] == SC.CHECKED
    assert entry(result, "m")["outcome"] == SC.UNDECIDED
    assert roles(result) == {"panels.0.series.0": "book", "panels.0.series.1": "book", "panels.0.series.2": "ai"}
    labels = {element["id"]: element for element in result.elements}
    assert labels["panels.0.series.1"]["tex"] == "g(x)"
    assert labels["panels.0.series.2"]["tag"] == "ai_defined"


# -- the planted-wrong corpus: domains (F1, F8) ----------------------------------------------------------

@sandboxed
def test_a_cancelled_factor_is_never_checked_and_a_stated_one_differs_at_the_hole(book):
    figure = plot("x + 0.0078125")
    assert check(book, figure, "s3").outcome == SC.UNDECIDED
    stated = check(book, plot("x + 0.0078125", stated="f(x)", span="s3"), "s3")
    assert stated.outcome == SC.DIFFERS
    assert stated.problems == ["your definition f has a value at x = 1/128, where the quoted equation has none"]


@sandboxed
def test_the_reverse_cancellation_differs_too(book):
    figure = plot("(x^2 - 0.00006103515625)/(x - 0.0078125)", low=0.5, high=1, stated="f(x)", span="s21")
    # Against a book with no factor: the figure has no value at the hole.
    result = check(book, figure, "s21")
    assert result.outcome != SC.CHECKED and not result.book_elements


@sandboxed
def test_a_square_of_a_root_against_x_is_never_checked(book):
    assert not check(book, plot("sqrt(x)^2"), "s5").book_elements
    stated = check(book, plot("sqrt(x)^2", stated="f(x)", span="s5"), "s5")
    assert stated.outcome == SC.DIFFERS and "x" in stated.problems[0]


@sandboxed
@pytest.mark.parametrize("low, high", [(0.0, 1.0), (0.5, 1.0)])
def test_a_computed_exponent_never_hides_a_cancellation(book, low, high):
    definitions = [{"name": "t", "expr": "x - 0.0078125"}, {"name": "f", "expr": "x + t^(1+1) + (t/t - 1)"}]
    plain = plot("", definitions=definitions, low=low, high=high)
    assert not check(book, plain, "s4").book_elements
    stated = plot("", definitions=definitions, low=low, high=high, stated="f(x)", span="s4")
    result = check(book, stated, "s4")
    assert result.outcome == SC.DIFFERS and "x = 1/128" in result.problems[0]


@sandboxed
def test_odd_denominators_and_slider_exponents_are_undecided_by_domain(book):
    assert entry(check(book, plot("x^(1/3)", low=0.25), "s6"))["reason"] == "domain"
    slider = [{"name": "n", "label": "n", "min": -2.0, "max": 2.0, "step": 0.5, "default": 1.0}]
    assert entry(check(book, plot("x^n", parameters=slider, low=0.25), "s7"))["reason"] == "domain"


@sandboxed
def test_a_positive_base_needs_no_condition(book):
    spec = plot("lambda^k", parameters=[PARAMETERS[1]], variable="k", low=0, high=3)
    spec["panels"][0] = {"kind": "pmf_bars", "k": {"var": "k", "min": 0, "max": 3}, "series": [{"expr": "f", "label": "m"}]}
    result = check(book, spec, "s8")
    assert result.outcome == SC.CHECKED and roles(result)["panels.0.series.0"] == "book"


@sandboxed
def test_a_parameter_dependent_condition_that_differs_is_undecided_by_domain(book):
    slider = [{"name": "a", "label": "a", "min": -1.0, "max": 1.0, "step": 0.5, "default": 0.5}]
    result = check(book, plot("x/a + (a^2/a^2 - 1)", parameters=slider), "s16")
    assert result.outcome == SC.UNDECIDED and entry(result)["reason"] == "domain" and not result.book_elements


@sandboxed
def test_sigma_in_a_denominator_with_a_positive_slider_passes(book):
    sigma = [{"name": "sigma", "label": "spread", "min": 0.5, "max": 2.0, "step": 0.5, "default": 1.0}]
    result = check(book, plot("x/sigma", parameters=sigma), "s9")
    assert result.outcome == SC.CHECKED and result.book_elements


# -- mixed candidates (F4) --------------------------------------------------------------------------------

@sandboxed
def test_a_stated_claim_proved_different_wins_over_an_unstated_match(book):
    result = check(book, plot("2*x", stated="f(x)=x", span="s2"), "s2")
    assert result.outcome == SC.DIFFERS and "differs from the quoted equation" in result.problems[0]
    assert not result.book_elements


@sandboxed
def test_a_stated_match_names_its_equation_and_an_unstated_match_needs_no_claim(book):
    stated = check(book, plot("2*x", stated="g(x)=2x", span="s2"), "s2")
    assert stated.outcome == SC.CHECKED and entry(stated)["candidate"]["lhs"] == "g(x)"
    unstated = check(book, plot("2*x"), "s2")
    assert unstated.outcome == SC.CHECKED and entry(unstated)["candidate"]["lhs"] == "g(x)"


@sandboxed
def test_one_definition_differing_withholds_every_book_role_on_the_figure(book):
    spec = plot("", definitions=[{"name": "f", "expr": "x"}, {"name": "h", "expr": "3*x"}])
    spec["panels"][0]["series"] = [{"expr": "f", "label": "one"}, {"expr": "h", "label": "two"}]
    spec["source_claims"] = [{"span_id": "s2", "quote": "g(x)=2x"}]
    spec["invariants"] = [{"kind": "equals_source", "name": "h"}]
    result = check(book, spec, "s2")
    assert entry(result, "f")["outcome"] == SC.CHECKED and entry(result, "h")["outcome"] == SC.DIFFERS
    assert result.outcome == SC.DIFFERS and result.elements == []


# -- what the author can and cannot do (G23b) ---------------------------------------------------------------

@sandboxed
def test_kind_illustrative_with_an_exact_match_is_book(book):
    assert check(book, plot("x", kind="illustrative"), "s5").book_elements


def test_grounding_none_is_never_checked(book):
    result = check(book, plot("x"), "s5", grounding="none")
    assert result.outcome == SC.NOT_CHECKABLE and result.reasons == {"no_book_source": 1}


def test_a_sketch_tier_is_never_checked():
    assert SC.grammar_row({"tier": "grammar", "spec_version": S.SPEC_VERSION})
    for tier, version in (("sketch", "sketch-v1"), ("manim", "manim-fig-v1"), ("js_animation", "x")):
        assert not SC.grammar_row({"tier": tier, "spec_version": version})


@sandboxed
def test_a_model_quote_of_a_wrong_equation_widens_nothing(book):
    # A quote the book does not hold is no pointer: the check reads only the book.
    result = check(book, plot("3*x", stated="f(x)=3x", span="s5"), "s5")
    assert result.outcome == SC.UNDECIDED and not result.book_elements


# -- at build: inside the attempt loop, under the gate (F5) -------------------------------------------------

def _context(tmp_path, answers: list[Any], blocks: list[tuple[str, str, str]] | None = None):
    paths, repository = build_check_vault(tmp_path / "vault", blocks or BLOCKS)
    author = AuthorFake(answers)
    return paths, repository, author, context(paths.root, author=author)


def _request(span: str = "s1") -> dict[str, Any]:
    return {"extractionId": EXTRACTION, "spanIds": [span]}


@sandboxed
def test_a_build_checks_inside_the_loop_and_the_second_attempt_is_told_where(tmp_path):
    half = plot(HALF_EXPR, parameters=PARAMETERS, low=-3, high=3, stated="f(x)", span="s1")
    right = plot(FLAGSHIP_EXPR, parameters=PARAMETERS, low=-3, high=3, stated="f(x)", span="s1")
    paths, repository, author, ctx = _context(tmp_path, [half, right])
    figure = build(ctx, _request())["figure"]
    assert author.calls == 2
    assert "your definition f differs" in author.contexts[1]["problems_with_the_last_attempt"][0]
    assert figure["sourceCheck"]["status"] == "checked" and figure["verification"] == "illustrative"
    stored = rows(repository, "figure_source_checks")
    assert [row["outcome"] for row in stored] == ["checked"] and stored[0]["trigger"] == "build"


@sandboxed
def test_a_second_difference_is_not_shown(tmp_path):
    half = plot(HALF_EXPR, parameters=PARAMETERS, low=-3, high=3, stated="f(x)", span="s1")
    paths, repository, author, ctx = _context(tmp_path, [half, half])
    figure = build(ctx, _request())["figure"]
    assert author.calls == 2
    assert figure["verification"] == "failed" and figure["specJson"] is None
    assert figure["sourceCheck"]["status"] == "differs" and figure["sourceCheck"]["rebuild"] is True
    assert figure["reason"] == SC.REJECTED_REASON
    # interactive_figures keeps steps 1-2's result; the state comes from the ledger.
    stored = rows(repository, "interactive_figures")[-1]
    assert stored["verification"] == "illustrative"
    assert rows(repository, "figure_source_checks")[-1]["outcome"] == "differs"


class _GatedAuthor(AuthorFake):
    """An author behind the installed gate, as a real client is (and a transport retrying what it refused)."""

    def __init__(self, answers: list[Any]) -> None:
        super().__init__(answers)
        self.refused = 0

    def complete(self, request: Any) -> Any:
        from learnloop.ai.execution import active_request_gate
        from learnloop.figure_admission import FiguresChanged

        gate = active_request_gate()
        try:
            gate.check("author")
        except FiguresChanged:
            self.refused += 1
            try:
                gate.check("transport retry")
            except FiguresChanged:
                self.refused += 1
            raise
        return super().complete(request)


class _FlipAfterCheck:
    """The fake sandbox's ``differs``, then the switch off before the second attempt."""

    def __init__(self, paths: Any) -> None:
        self.paths = paths
        self.calls = 0

    def __call__(self, _harness: str, payload: dict[str, Any], **_kwargs: Any) -> pf_sandbox.SandboxResult:
        self.calls += 1
        set_config(self.paths, "figures", checked_labels_enabled=False)
        definition = payload["definitions"][0]
        pair = definition["pairs"][0]
        return pf_sandbox.SandboxResult(True, output={"sympy_version": "fake", "results": [
            {"definition": definition["name"], "candidate": pair["candidate"], "result": "different",
             "witness": {"kind": "value", "at": {"x": "1"}}}]})


def test_the_switch_off_between_the_sandbox_and_the_second_attempt_stops_the_build(tmp_path, monkeypatch):
    half = plot(HALF_EXPR, parameters=PARAMETERS, low=-3, high=3, stated="f(x)", span="s1")
    paths, repository = build_check_vault(tmp_path / "vault", BLOCKS)
    flip = _FlipAfterCheck(paths)
    monkeypatch.setattr(SC, "_run_sandbox", lambda payload, sandbox: flip("", payload))
    monkeypatch.setattr(pf_sandbox, "sandbox_available", lambda: True)
    author = _GatedAuthor([half, half])
    vault = load_vault(paths.root)
    request = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["s1"])
    with pytest.raises(FS.FigureRefused) as caught:
        FS.build_figure(vault, repository, request, author_client=author, live_vault=lambda: load_vault(paths.root))
    assert caught.value.code == "figures_changed"
    # The second attempt was refused before it was sent, and so was its transport's retry.
    assert author.calls == 1 and flip.calls == 1 and author.refused == 2
    for table in ("interactive_figures", "figure_source_checks"):
        assert rows(repository, table) == []
    assert not [row for row in rows(repository, "judgment_ledger") if row["task"] == SC.LEDGER_TASK]


def test_the_switch_off_at_the_store_writes_nothing(tmp_path, monkeypatch):
    paths, repository = build_check_vault(tmp_path / "vault", BLOCKS)

    def flip_and_answer(_payload: dict[str, Any], _sandbox: Any) -> pf_sandbox.SandboxResult:
        set_config(paths, "figures", checked_labels_enabled=False)
        return pf_sandbox.SandboxResult(True, output={"sympy_version": "fake", "results": []})

    monkeypatch.setattr(SC, "_run_sandbox", flip_and_answer)
    monkeypatch.setattr(pf_sandbox, "sandbox_available", lambda: True)
    author = AuthorFake([plot("x")])
    vault = load_vault(paths.root)
    with pytest.raises(FS.FigureRefused) as caught:
        FS.build_figure(vault, repository, FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["s5"]),
                        author_client=author, live_vault=lambda: load_vault(paths.root))
    assert caught.value.code == "figures_changed" and author.calls == 1
    assert rows(repository, "figure_source_checks") == [] and rows(repository, "interactive_figures") == []


def test_build_key_holds_the_switch_and_the_reuse_key_does_not(tmp_path):
    paths, repository = build_check_vault(tmp_path / "vault", BLOCKS)
    vault = load_vault(paths.root)
    on = FS.build_key(vault)
    context_ = FS.SourceContext(passage=[{"span_id": "s1", "type": "Text", "text": "x"}])
    request = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["s1"])
    hashed = FS.request_hash(request, context_, None)
    set_config(paths, "figures", checked_labels_enabled=False)
    off = load_vault(paths.root)
    assert FS.build_key(off) != on and on[-1] is True and FS.build_key(off)[-1] is False
    assert FS.offer_build_key(off) != FS.offer_build_key(vault)
    assert FS.request_hash(request, context_, None) == hashed


def test_a_fake_author_sending_sympy_text_or_a_verified_field_changes_nothing(tmp_path):
    spec = plot("x")
    # The schema has no field for any of it (its validation refuses them), so no model output can be a check input.
    for extra in ({"verified": True}, {"check_program": "def check(r, a): return True"},
                  {"source_expression": "x"}, {"checked": True}):
        with pytest.raises(S.SpecError):
            S.parse_spec({**spec, **extra})
    assert "verified" not in S.InteractiveFigureSpecV1.model_fields


def test_a_check_that_blows_up_costs_the_figure_nothing_and_certifies_nothing(tmp_path, monkeypatch):
    paths, repository, _author, ctx = _context(tmp_path, [plot("x")])

    def boom(*_args: Any, **_kwargs: Any):
        raise RuntimeError("no")

    monkeypatch.setattr(SC, "check_figure", boom)
    figure = build(ctx, _request("s5"))["figure"]
    assert figure["verification"] == "illustrative" and figure["sourceCheck"]["status"] == "none"
    assert figure["sourceCheck"]["reasons"] == ["sandbox_failed"]
    assert rows(repository, "figure_source_checks")[0]["outcome"] == "undecided"
    assert call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"][0]["elements"] == []


def test_a_held_out_block_later_withholds_the_figure_and_its_check(tmp_path, monkeypatch):
    from learnloop.vault.writer import upsert_source_set

    paths, repository, _author, ctx = _context(tmp_path, [plot("x")])
    monkeypatch.setattr(SC, "_run_sandbox", lambda payload, sandbox: pf_sandbox.SandboxResult(True, output={"results": []}))
    monkeypatch.setattr(pf_sandbox, "sandbox_available", lambda: True)
    assert build(ctx, _request("s5"))["figure"]
    upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra", "title": "x", "members": [
        {"source_id": "src_math", "revision_id": "rev_math", "default_role": "exam"}]})
    ctx = context(paths.root, author=AuthorFake())
    assert call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"] == []

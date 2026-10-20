"""Reader RW5a: verification before a figure shows (spec §8.3; G23, G45).

Structure and invariants decide whether a figure is shown at all; the source
match (the verifier's sympy check, run in the PF-b sandbox with negative
controls) decides whether a reconstruction is labelled as matching the book.
All model calls are fakes; the sandbox runs for real where bubblewrap exists.
"""

from __future__ import annotations

import json

import pytest

from learnloop.figures import spec as S
from learnloop.figures import verify as V
from tests import figure_corpus as FC
from tests.figure_fixtures import (
    EXTRACTION,
    AuthorFake,
    VerifierFake,
    build,
    build_figure_vault,
    context,
    flagship,
    half_density,
    rows,
    sandbox_ready,
)

needs_sandbox = pytest.mark.skipif(not sandbox_ready(), reason="bubblewrap is not available here")


def test_numeric_checks_pass_the_flagship_and_reject_the_half_negative_control():
    report = V.verify_numerics(S.parse_spec(FC.flagship_spec()))
    assert report.outcome == V.ILLUSTRATIVE and report.grid_points == 9
    assert all(shade["worst_gap"] < 1e-6 for shade in report.shades)
    half = V.verify_numerics(S.parse_spec(FC.flagship_spec(FC.TWO_SIDED_HALF)))
    assert half.outcome == V.FAILED
    assert "integrates_to_one" in half.reason and "0.5" in half.reason


def test_each_invariant_kind_holds_or_fails():
    compiled = S.parse_spec(FC.pmf_spec())
    assert V.verify_numerics(compiled).outcome == V.ILLUSTRATIVE
    broken = FC.pmf_spec()
    broken["invariants"] = [{"kind": "sums_to_one", "expr": "pmf", "var": "k", "from": 1, "to": 3}]
    assert V.verify_numerics(S.parse_spec(broken)).outcome == V.FAILED
    for kind, expr, outcome in (
        ("nonnegative", "x - 1", V.FAILED), ("nonnegative", "x^2", V.ILLUSTRATIVE),
        ("bounded", "exp(x)", V.FAILED), ("monotone_nondecreasing", "x^3", V.ILLUSTRATIVE),
        ("monotone_nondecreasing", "sin(x)", V.FAILED), ("finite", "log(x)", V.FAILED),
    ):
        spec = FC.linear_map_spec()
        spec["invariants"] = [{"kind": kind, "expr": expr, "var": "x", "from": -20, "to": 20, "bound": 1000}]
        assert V.verify_numerics(S.parse_spec(spec)).outcome == outcome, (kind, expr)


def test_a_value_that_is_not_finite_on_the_grid_fails_structure():
    spec = FC.linear_map_spec()
    spec["panels"][1]["expr"] = "1/(s - 0.1)"
    report = V.verify_numerics(S.parse_spec(spec))
    assert report.outcome == V.FAILED and "not finite" in report.reason


def test_a_shaded_area_is_checked_against_an_independent_integration():
    compiled = S.parse_spec(FC.normal_cdf_spec())
    env = compiled.defaults
    node = compiled.panels[0].nodes["series"][0]
    reference = V.independent_integral(compiled, node, "x", -1, 1, env)
    assert abs(reference - 0.6826894921370859) < 1e-12
    # A jump inside the range is split at its breakpoint.
    flag = S.parse_spec(FC.flagship_spec())
    whole = V.independent_integral(flag, flag.panels[0].nodes["series"][0], "x", -40, 40, flag.defaults)
    assert abs(whole - 1.0) < 1e-12


def test_quotes_must_be_verbatim():
    compiled = S.parse_spec(flagship())
    texts = {"p2": "with 0 < p < 1 and \\lambda > 0.", "p3": "f_X(x) = p\\lambda e^{\\lambda x}   for x < 0"}
    assert V.check_claims(compiled, texts) == [{"span_id": "p3", "quote": compiled.spec.source_claims[0].quote,
                                                "verified": True}]
    shown = V.verified_assumptions(compiled, texts)
    assert shown[0]["quote"] == "0 < p < 1 and \\lambda > 0" and shown[1]["quote"] is None


@needs_sandbox
def test_source_match_runs_the_verifiers_check_in_the_sandbox_with_negative_controls():
    from learnloop.figures import grammar as G
    from tests.figure_fixtures import GOOD_CHECK, SOURCE_EXPRESSION

    compiled = S.parse_spec(flagship())
    answer = G.to_sympy(compiled.definitions["f"], compiled.definitions)
    good = V.run_source_match(answer, V.SourceCheck(SOURCE_EXPRESSION, GOOD_CHECK))
    assert good["matched"] is True and good["checks"] == [True, False, False]
    always = V.run_source_match(answer, V.SourceCheck(SOURCE_EXPRESSION, "def check(r, a):\n    return True\n"))
    assert always["matched"] is False and "negative control" in always["reason"]
    wrong = V.run_source_match(answer, V.SourceCheck(SOURCE_EXPRESSION.replace("(1 - p)", "p"), GOOD_CHECK))
    assert wrong["matched"] is False and "does not equal" in wrong["reason"]


def test_the_check_never_runs_in_process(monkeypatch):
    """No sandbox: the source match cannot run, so a reconstruction is an
    illustration (the verifier's text is never executed here)."""

    from learnloop.content.authoring import pf_sandbox

    def unavailable(*_args, **_kwargs):
        raise pf_sandbox.SandboxUnavailable("no bubblewrap")

    monkeypatch.setattr(pf_sandbox, "run_sandboxed_python", unavailable)
    from tests.figure_fixtures import GOOD_CHECK, SOURCE_EXPRESSION

    result = V.run_source_match("x", V.SourceCheck(SOURCE_EXPRESSION, GOOD_CHECK))
    assert result == {"matched": False, "reason": "sandbox_unavailable"}


@needs_sandbox
def test_g23_a_verified_reconstruction_is_labelled_as_matching_the_book(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    author, verifier = AuthorFake(), VerifierFake()
    result = build(context(paths.root, author=author, verifier=verifier))
    figure = result["figure"]
    assert figure["verification"] == "verified"
    assert figure["label"] == "AI-built · matches the book's equation (checked)"
    assert json.loads(figure["specJson"])["kind"] == "reconstructed"
    assert author.calls == 1 and verifier.calls == 1
    (row,) = rows(repository, "interactive_figures")
    report = json.loads(row["verification_report_json"])
    assert report["source_match"]["matched"] is True and report["claims"][0]["verified"] is True
    (ledger,) = [r for r in rows(repository, "judgment_ledger") if r["task"] == "figure_verified"]
    assert ledger["judge"] == "verifier" and ledger["verdict"] == "verified" and ledger["left_id"] == row["id"]
    # The assumption whose quote is not the book's keeps its text, unquoted.
    assert [a["quote"] for a in figure["assumptions"]] == ["0 < p < 1 and \\lambda > 0", None]


@pytest.mark.parametrize("verifier_kwargs, reason", [
    ({"program": "def check(r, a):\n    return True\n"}, "negative control"),
    ({"quote": "a quote the figure never claimed"}, "not the figure's source claim"),
    ({"fail": RuntimeError("down")}, "verifier_failed"),
])
def test_failing_the_source_match_alone_downgrades_to_an_illustration(tmp_path, monkeypatch, verifier_kwargs, reason):
    if "program" in verifier_kwargs and not sandbox_ready():
        pytest.skip("bubblewrap is not available here")
    paths, _repository = build_figure_vault(tmp_path / "vault")
    figure = build(context(paths.root, author=AuthorFake(), verifier=VerifierFake(**verifier_kwargs)))["figure"]
    assert figure["verification"] == "illustrative"
    assert figure["label"] == "AI-built illustration of an interpretation · not checked against the book"
    assert reason in (figure["reason"] or "")
    assert figure["specJson"] is not None


def test_no_quote_in_the_passage_means_no_source_match_and_no_verifier_call(tmp_path):
    paths, _repository = build_figure_vault(tmp_path / "vault")
    verifier = VerifierFake()
    spec = flagship(source_claims=[{"span_id": "p3", "quote": "an equation the book never wrote"}])
    figure = build(context(paths.root, author=AuthorFake([spec]), verifier=verifier))["figure"]
    assert figure["verification"] == "illustrative" and verifier.calls == 0
    assert "no quote" in figure["reason"]


def test_an_illustration_is_never_sent_to_the_verifier(tmp_path):
    paths, _repository = build_figure_vault(tmp_path / "vault")
    verifier = VerifierFake()
    figure = build(context(paths.root, author=AuthorFake([flagship(kind="illustrative")]), verifier=verifier))["figure"]
    assert figure["verification"] == "illustrative" and verifier.calls == 0


def test_g45_the_half_density_is_never_shown(tmp_path):
    """The UX's first W11 draft (total mass ½): integrates_to_one rejects it on
    both attempts, so the figure is stored failed and never shown."""

    paths, repository = build_figure_vault(tmp_path / "vault")
    author = AuthorFake([half_density(), half_density()])
    figure = build(context(paths.root, author=author, verifier=VerifierFake()))["figure"]
    assert figure["verification"] == "failed" and figure["specJson"] is None
    assert figure["label"].startswith("couldn't build a reliable version of this (integrates_to_one")
    assert author.calls == 2
    assert "integrates to 0.5" in json.dumps(author.contexts[1]["problems_with_the_last_attempt"])
    (row,) = rows(repository, "interactive_figures")
    assert row["verification"] == "failed" and row["spec_json"] is None


def test_the_second_attempt_sees_the_first_attempts_problems(tmp_path):
    paths, _repository = build_figure_vault(tmp_path / "vault")
    author = AuthorFake(["{not json", flagship(kind="illustrative")])
    figure = build(context(paths.root, author=author))["figure"]
    assert figure["verification"] == "illustrative" and author.calls == 2
    assert "problems_with_the_last_attempt" not in author.contexts[0]
    assert author.contexts[1]["problems_with_the_last_attempt"][0].startswith("not JSON")


def test_unsupported_requests_are_recorded_with_their_kind(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    figure = build(context(paths.root, author=AuthorFake([("unsupported", "a 3-D surface")])))["figure"]
    assert figure["verification"] == "unsupported" and figure["unsupportedKind"] == "a 3-D surface"
    assert figure["label"] == "can't draw this yet — needs a 3-D surface · noted"
    (row,) = rows(repository, "interactive_figures")
    assert row["unsupported_kind"] == "a 3-D surface" and row["spec_json"] is None


def test_an_undecidable_prediction_is_dropped_not_failed(tmp_path):
    paths, _repository = build_figure_vault(tmp_path / "vault")
    spec = flagship(kind="illustrative")
    spec["predictions"].append({"prompt": "which area is 42?", "change": {}, "observe": {"kind": "area", "expr": "42"}})
    figure = build(context(paths.root, author=AuthorFake([spec])))["figure"]
    assert figure["verification"] == "illustrative"
    assert [p["index"] for p in figure["predictions"]] == [0, 1]
    assert json.loads(rows(_repository, "interactive_figures")[0]["verification_report_json"])["dropped_predictions"] == [2]


def test_the_answer_is_not_sent_before_the_learner_answers(tmp_path):
    paths, _repository = build_figure_vault(tmp_path / "vault")
    figure = build(context(paths.root, author=AuthorFake([flagship(kind="illustrative")])))["figure"]
    prediction = figure["predictions"][0]
    assert prediction["answered"] is None and "answer" not in prediction
    assert [choice["value"] for choice in prediction["choices"]] == ["rises", "falls", "same"]
    assert figure["predictions"][1]["choices"] == [{"value": "P(X ≤ 0)", "label": "P(X ≤ 0)"},
                                                   {"value": "P(X > 0)", "label": "P(X > 0)"}]
    assert figure["extractionId"] == EXTRACTION and figure["anchorSpanId"] == "p3"

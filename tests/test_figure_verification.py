"""Reader RW5a: verification before a figure shows (spec §8.3 steps 1-2; G23 vacuous, G45).

Structure and invariants decide whether a figure is shown at all. RW5a has no
source match (§8.3 step 3 is RW5c's): every shown figure is an illustration.
All model calls are fakes.
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
)



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


def test_g23_holds_vacuously_a_reconstruction_is_an_illustration(tmp_path):
    """RW5a makes no "matches the book" claim (owner scope decision
    2026-10-21; the source check is RW5c's): G23 ("only after step 3 passed")
    holds vacuously. A reconstruction is stored and shown as an illustration,
    and an injected verifier is never asked."""

    from learnloop.figures import service as FS

    paths, repository = build_figure_vault(tmp_path / "vault")
    author, verifier = AuthorFake(), VerifierFake()
    figure = build(context(paths.root, author=author, verifier=verifier))["figure"]
    assert figure["verification"] == "illustrative"
    assert figure["label"] == "AI-built illustration of an interpretation · not checked against the book"
    assert figure["reason"] == FS.RECONSTRUCTION_REASON
    assert json.loads(figure["specJson"])["kind"] == "reconstructed"
    assert author.calls == 1 and verifier.calls == 0
    (row,) = rows(repository, "interactive_figures")
    report = json.loads(row["verification_report_json"])
    assert "source_match" not in report and report["claims"][0]["verified"] is True
    (ledger,) = [r for r in rows(repository, "judgment_ledger") if r["task"] == "figure_verified"]
    assert ledger["verdict"] == "illustrative" and ledger["left_id"] == row["id"]
    # The assumption whose quote is not the book's keeps its text, unquoted.
    assert [a["quote"] for a in figure["assumptions"]] == ["0 < p < 1 and \\lambda > 0", None]


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

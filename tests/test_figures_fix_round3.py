"""Reader RW5a fix round 3 (orchestrator): the verify's findings, each reproduced.

The source-check (spec §8.3 step 3) and admission tests these rounds added were removed
with that machinery by the owner's scope decision of 2026-10-21; their successors
are in tests/test_figures_scope_redesign.py. What stays here still holds.

See docs/reviews/reader-rw5a-codex-review.md, "Fix round 3 (orchestrator)".

Parity by construction: names are letters and digits (no ``__proto__``, no
Object.prototype name), every value is canonical (no -0), a sum's bounds
follow one rule in both evaluators and in the SymPy translation, and a
definition SymPy cannot read exactly is not source-verifiable. The
differential property test (tests/test_figure_property.py and its vitest
twin) is the contract; the cases here pin the verify's reproductions.

Also: structural verification covers every displayed derived value (a map's
determinant and corners, the renderer's scales), and the backlog reconciles a
late explanation by a marker on the job, never by searching the text. The
report's switch-off is in tests/test_figures_switch_off.py.
"""

from __future__ import annotations

import math

import pytest

from learnloop.content.authoring import pf_sandbox
from learnloop.diagnosis.text_gaps import sources as gap_sources
from learnloop.diagnosis.text_gaps.jobs import sweep_backlog
from learnloop.figures import grammar as G
from learnloop.figures import spec as S
from learnloop.figures import verify as V
from learnloop.vault.loader import load_vault
from tests.figure_fixtures import (
    EQUATION_TEXT,
    AuthorFake,
    VerifierFake,
    build,
    build_figure_vault,
    call,
    context,
    flagship,
    sandbox_ready,
)
from tests.test_figures_codex_review import _clients, _equivalence, _gap_jobs, _missed_prediction
from tests.test_figures_fix_round2 import _drain, _gaps_switch, _job_rows

needs_sandbox = pytest.mark.skipif(not sandbox_ready(), reason="bubblewrap is not available here")

#: An honest equality check: exact, symbolic, every Sum and Piecewise done.
# ---------------------------------------------------------------------------
# High 1: SymPy reads a sum as the renderer evaluates it
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Medium 4 and 5: signed zero and prototype names, by construction
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("expr, value", [("piecewise((1/min(0, -0) < 0, 1), 2)", 2.0), ("1/min(-0, 0)", math.inf),
                                         ("1/floor(-0)", math.inf), ("-0", 0.0), ("0*-1", 0.0)])
def test_no_value_is_negative_zero(expr, value):
    result = G.evaluate(G.parse(expr), {})
    assert result == value and math.copysign(1.0, result) > 0


@pytest.mark.parametrize("expr", ["__proto__", "sum(__proto__, __proto__, 1, 3)", "constructor", "toString + 1",
                                  "valueOf", "x_1", "_x", "hasOwnProperty"])
def test_prototype_and_underscore_names_are_refused_when_parsed(expr):
    with pytest.raises(G.GrammarError):
        G.parse(expr)


def test_a_parameter_named_like_the_prototype_is_refused():
    spec = flagship()
    spec["parameters"][0]["name"] = "constructor"
    with pytest.raises(S.SpecError):
        S.parse_spec(spec)
    assert not G.is_name("__proto__") and not G.is_name("valueOf") and G.is_name("lam2")


# ---------------------------------------------------------------------------
# Medium 6: every displayed derived value is finite
# ---------------------------------------------------------------------------

def _map(matrix: list[list[str]]) -> dict:
    return {"spec_version": "ifs-v1", "kind": "illustrative", "demonstrates": "a map",
            "panels": [{"kind": "linear_map_2d", "matrix": matrix}]}


@pytest.mark.parametrize("matrix", [[["1e200", "0"], ["0", "1e200"]],        # determinant 1e400
                                    [["1e308", "1e308"], ["0", "1"]],         # a corner at 2e308
                                    [["1.7e308", "0"], ["0", "1"]]])          # the renderer's reach, padded
def test_a_map_whose_shown_values_overflow_fails_structure(matrix):
    report = V.verify_numerics(S.parse_spec(_map(matrix)))
    assert report.outcome == V.FAILED and "not finite" in report.reason


def test_a_finite_map_and_the_flagship_still_pass_structure():
    assert V.verify_numerics(S.parse_spec(_map([["2", "1"], ["0", "1"]]))).outcome == V.ILLUSTRATIVE
    assert V.verify_numerics(S.parse_spec(flagship())).outcome == V.ILLUSTRATIVE


# ---------------------------------------------------------------------------
# Medium 3 (F5): the explanation a reading read is a marker, not a substring
# ---------------------------------------------------------------------------

def test_f5_an_explanation_repeating_the_answer_is_still_read(tmp_path):
    """The verify's case: the reading's text is "it rises", and the late
    explanation is "it rises" too. A substring search took it as read."""

    paths, repository, _ctx, found = _missed_prediction(tmp_path)
    prediction_id = found["predictionId"]
    _llm, clients = _clients()
    assert [outcome.state for outcome in _drain(paths.root, repository, clients)] == ["done"]
    _gaps_switch(paths, False)
    call(context(paths.root), "reader.figure_explain", {"predictionId": prediction_id, "text": "it rises"})
    _gaps_switch(paths, True)
    assert sweep_backlog(load_vault(paths.root), repository)["reader_formative"] == 1
    explained = prediction_id + gap_sources.FIGURE_EXPLANATION_SUFFIX
    assert ("reader_formative", explained, "queued") in _gap_jobs(repository)


def test_f5_the_reading_records_whether_it_read_the_explanation(tmp_path):
    paths, repository, ctx, found = _missed_prediction(tmp_path)
    call(ctx, "reader.figure_explain", {"predictionId": found["predictionId"], "text": "p sets the split"})
    _llm, clients = _clients()
    assert [outcome.state for outcome in _drain(paths.root, repository, clients)] == ["done"]
    with repository.connection() as connection:
        (payload,) = [row[0] for row in connection.execute("SELECT payload_json FROM learner_text_gap_jobs")]
    assert '"explanation_read": true' in payload
    assert [job["state"] for job in _job_rows(repository)] == ["done"]
    assert sweep_backlog(load_vault(paths.root), repository)["reader_formative"] == 0

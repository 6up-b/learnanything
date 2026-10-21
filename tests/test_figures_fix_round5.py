"""Reader RW5a fix round 5 (orchestrator): the verify's findings under the scope ruling.

See docs/reviews/reader-rw5a-codex-review.md, "Fix round 5 (orchestrator)".

"Checked" certifies that the figure's definition equals the source equation
exactly and that the displayed, source-labelled content IS that definition;
not that every float pixel is exact real arithmetic. So the branch case is
closed by construction (a checked definition's piecewise conditions compare
a bare variable or parameter with a binary64-exact literal); the switch and
the routes are reread before every author and verifier call; a stored
"verified" carries its certification version and an older one shows, and is
reused, as an illustration; and a percent readout's scaled value is checked.
"""

from __future__ import annotations

import json
import threading

import pytest

from learnloop.content.authoring import pf_sandbox
from learnloop.db.repositories import Repository
from learnloop.figures import grammar as G
from learnloop.figures import routes as R
from learnloop.figures import service as FS
from learnloop.figures import spec as S
from learnloop.figures import verify as V
from learnloop.vault.loader import load_vault
from tests.figure_fixtures import (
    EQUATION_TEXT,
    EXTRACTION,
    AuthorFake,
    VerifierFake,
    build,
    build_figure_vault,
    call,
    context,
    flagship,
    rows,
    sandbox_ready,
)
from tests.test_figures_codex_review import _equivalence
from tests.test_figures_switch_off import _switch

needs_sandbox = pytest.mark.skipif(not sandbox_ready(), reason="bubblewrap is not available here")


def _with_parameter(definition: str) -> dict:
    return {
        "spec_version": "ifs-v1", "kind": "reconstructed",
        "source_claims": [{"span_id": "p3", "quote": EQUATION_TEXT}],
        "demonstrates": "the book's f",
        "parameters": [{"name": "p", "label": "p", "min": 0, "max": 1, "step": 0.1, "default": 0.5}],
        "definitions": [{"name": "f", "expr": definition}],
        "panels": [{"kind": "function_plot", "x": {"var": "x", "min": -1, "max": 1},
                    "series": [{"expr": "f", "label": "f(x)"}]}],
        "invariants": [{"kind": "equals_source", "name": "f"}],
    }


def _certify(tmp_path, monkeypatch, spec):
    monkeypatch.setattr(pf_sandbox, "run_equivalence_checks", _equivalence([True, False, False]))
    paths, _repository = build_figure_vault(tmp_path / "vault")
    verifier = VerifierFake()
    figure = build(context(paths.root, author=AuthorFake([spec]), verifier=verifier))["figure"]
    return figure, verifier


# ---------------------------------------------------------------------------
# Finding 1 (branch case): exact conditions by construction
# ---------------------------------------------------------------------------

def test_a_computed_condition_is_never_checked(tmp_path, monkeypatch):
    """The verify's case: p*10 < 3 at the reachable p = 0.3 is 2 in floating
    point and 1 exactly, and the grid (0, 0.5, 1) never visits it."""

    figure, verifier = _certify(tmp_path, monkeypatch, _with_parameter("piecewise((p*10 < 3, 1), 2)"))
    assert figure["verification"] == "illustrative" and "piecewise condition" in figure["reason"]
    assert verifier.calls == 0


@needs_sandbox
def test_a_bare_variable_against_a_dyadic_literal_is_checked(tmp_path, monkeypatch):
    figure, verifier = _certify(tmp_path, monkeypatch, _with_parameter("piecewise((x < 0.5, 1), 2)"))
    assert figure["verification"] == "verified" and verifier.calls == 1


@pytest.mark.parametrize("definition, exact", [
    ("piecewise((x < 0, 1), 2)", True), ("piecewise((0.5 > x, 1), 2)", True), ("piecewise((x < -2, 1), 2)", True),
    ("piecewise((p >= 0.375 and x != 1, 1), 2)", True),
    ("piecewise((x < 0.3, 1), 2)", False), ("piecewise((p*10 < 3, 1), 2)", False),
    ("piecewise((x + 0 < 1, 1), 2)", False), ("piecewise((x < pi, 1), 2)", False),
    ("piecewise((x < 0 or p < 0.1, 1), 2)", False), ("piecewise((g < 0, 1), 2)", False),
])
def test_the_branch_rule(definition, exact):
    definitions = {"g": G.parse("x*2")}
    assert (V.condition_problem(G.parse(definition), definitions) is None) is exact


def test_the_flagship_conditions_are_exact():
    compiled = S.parse_spec(flagship())
    assert V.condition_problem(compiled.definitions["f"], compiled.definitions) is None


# ---------------------------------------------------------------------------
# High 3: the switch and the routes, reread before every call
# ---------------------------------------------------------------------------

def test_figure_route_refuses_when_figures_are_off_now(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    route = R.FigureRoute(vault, repository, R.AUTHOR_TASK, client=AuthorFake(), envelope=None,
                          owner_id="figure:t", max_calls=2)
    assert route.problem() is None
    _switch(paths.root, "figures", False)
    assert route.problem().reason == "disabled"  # the captured vault still says on


@pytest.mark.parametrize("first", ["not a spec", "flagship"])
def test_switching_off_during_the_first_author_call_stops_the_build(tmp_path, first):
    """No retry after an unusable first answer, no verifier call after a
    reconstruction, and nothing stored."""

    paths, repository = build_figure_vault(tmp_path / "vault")
    vault = load_vault(paths.root)

    def switch_off_while_answering(_context):
        _switch(paths.root, "figures", False)
        return "not a spec" if first == "not a spec" else flagship()

    author, verifier = AuthorFake([switch_off_while_answering, flagship()]), VerifierFake()
    with pytest.raises(FS.FigureRefused) as caught:
        FS.build_figure(vault, repository, FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"]),
                        author_client=author, verifier_client=verifier)
    assert caught.value.code == "disabled"
    assert author.calls == 1 and verifier.calls == 0
    assert rows(repository, "interactive_figures") == []


def test_a_sidecar_reload_turning_figures_off_stops_a_running_build(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    ctx = context(paths.root, author=None, verifier=VerifierFake())
    ctx.library_ask_inline = False  # the build runs as a job, as in the app
    entered, release = threading.Event(), threading.Event()

    def answer(_context):
        entered.set()
        assert release.wait(30)
        return flagship()

    author = AuthorFake([answer, flagship()])
    ctx.figure_author_client = author
    job = call(ctx, "reader.figure_request", {"extractionId": EXTRACTION, "spanIds": ["p3"]})
    assert entered.wait(30)
    _switch(paths.root, "figures", False)
    ctx.reload(maintenance=False)  # the app reloads: the job's captured vault still says on
    release.set()
    kept = ctx.figure_jobs.get(job["jobId"])
    assert kept is not None and kept.done.wait(60)
    assert author.calls == 1 and ctx.figure_verifier_client.calls == 0
    assert rows(repository, "interactive_figures") == []


# ---------------------------------------------------------------------------
# High 4: the certification version
# ---------------------------------------------------------------------------

@needs_sandbox
def test_a_verified_figure_from_an_older_certification_shows_and_reuses_as_an_illustration(tmp_path, monkeypatch):
    paths, repository = build_figure_vault(tmp_path / "vault")
    monkeypatch.setattr(V, "CERTIFICATION_VERSION", V.CERTIFICATION_VERSION - 1)
    author = AuthorFake([flagship(), flagship()])
    ctx = context(paths.root, author=author, verifier=VerifierFake())
    old = build(ctx)["figure"]
    assert old["verification"] == "verified"
    monkeypatch.undo()  # the current rules
    (listed,) = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert listed["figureId"] == old["figureId"] and listed["verification"] == "illustrative"
    assert listed["label"] == "AI-built illustration of an interpretation · not checked against the book"
    assert "earlier rule" in listed["reason"]
    assert FS.figure_view(load_vault(paths.root), repository, rows_with_report(repository)[0])["verification"] \
        == "illustrative"
    # Reuse is a cache miss: the same request is built and certified again.
    again = build(ctx)["figure"]
    assert author.calls == 2 and again["figureId"] != old["figureId"] and again["verification"] == "verified"
    stored = {row["id"]: json.loads(row["verification_report_json"]) for row in rows(repository, "interactive_figures")}
    assert stored[again["figureId"]]["certification_version"] == V.CERTIFICATION_VERSION


def rows_with_report(repository):
    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.db.stores import figures as store

    with closing(connect(Repository.attach(repository.sqlite_path).sqlite_path, read_only=True)) as connection:
        return [store.figure(connection, row["id"]) for row in rows(repository, "interactive_figures")]


def test_every_new_report_carries_the_certification_version(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    build(context(paths.root, author=AuthorFake([flagship(kind="illustrative")])))
    (row,) = rows(repository, "interactive_figures")
    assert json.loads(row["verification_report_json"])["certification_version"] == V.CERTIFICATION_VERSION == 3


# ---------------------------------------------------------------------------
# Medium 5: formatting-derived numbers
# ---------------------------------------------------------------------------

def test_a_percent_readout_that_overflows_when_scaled_fails_structure():
    spec = {"spec_version": "ifs-v1", "kind": "illustrative", "demonstrates": "a big share",
            "panels": [{"kind": "readout", "label": "share", "expr": "10^307", "format": "percent"}]}
    report = V.verify_numerics(S.parse_spec(spec))
    assert report.outcome == V.FAILED and "as a percent" in report.reason
    spec["panels"][0]["format"] = "number"
    assert V.verify_numerics(S.parse_spec(spec)).outcome == V.ILLUSTRATIVE

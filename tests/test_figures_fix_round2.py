"""Reader RW5a fix round 2 (orchestrator): the pre-landing verify's findings, each reproduced.

See docs/reviews/reader-rw5a-codex-review.md, "Fix round 2 (orchestrator)".

F1 a missed prediction whose figure's manifest is held out now reaches no gap reader;
F4 the sandbox reports a check's answer as given (None, 0 and "" are inconclusive),
   through the real harness into the figure's verdict, and the PF callers keep
   counting inconclusive as not passing;
F3 "matches the book's equation (checked)" is bound to what is drawn;
bounds: sum limits and PMF supports past the safe integers, the counted loops;
F7 a build that committed between the two reads before the lock is reused, not rebuilt;
F5 the backlog sweep reads an explanation saved while gap reading was off.

Every model is a fake. The F4 composition runs the real PF-b harness in the
bubblewrap sandbox (skipped where bubblewrap is unavailable).
"""

from __future__ import annotations

import re

import pytest

from learnloop.content.authoring import pf_sandbox
from learnloop.db.repositories import Repository
from learnloop.db.stores import figures as figure_store
from learnloop.diagnosis.text_gaps import sources as gap_sources
from learnloop.diagnosis.text_gaps.jobs import process_next_gap_job, sweep_backlog
from learnloop.figures import grammar as G
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
from tests.test_figures_codex_review import _clients, _equivalence, _gap_jobs, _gap_rows, _hold_out, _missed_prediction

needs_sandbox = pytest.mark.skipif(not sandbox_ready(), reason="bubblewrap is not available here")


def _job_rows(repository):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT source_kind, source_id, state, last_error FROM learner_text_gap_jobs ORDER BY created_at, id")]


def _drain(root, repository, clients):
    outcomes = []
    while (outcome := process_next_gap_job(root, repository, owner="t", clients=clients)) is not None:
        outcomes.append(outcome)
    return outcomes


# ---------------------------------------------------------------------------
# F1: held-out material never reaches the gap reader
# ---------------------------------------------------------------------------

def test_f1_a_held_out_neighbour_keeps_a_missed_prediction_from_the_gap_reader(tmp_path, monkeypatch):
    paths, repository, _ctx, found = _missed_prediction(tmp_path)
    prediction_id = found["predictionId"]
    # p4 (the figure block) was sent to the author as context of p3's figure.
    _hold_out(monkeypatch, "p4")
    llm, clients = _clients()
    outcomes = _drain(paths.root, repository, clients)
    assert [outcome.state for outcome in outcomes] == ["skipped"]
    assert llm.calls == []  # nothing of the passage, question or readout was sent
    (job,) = _job_rows(repository)
    assert (job["source_id"], job["state"]) == (prediction_id, "skipped")
    assert job["last_error"].startswith("held out:")
    assert _gap_rows(repository) == []
    # Marked: a later sweep does not queue it again.
    vault = load_vault(paths.root)
    assert sweep_backlog(vault, repository)["reader_formative"] == 0
    assert _drain(paths.root, repository, clients) == [] and llm.calls == []


def test_f1_a_later_explanation_of_a_held_out_figure_is_skipped_too(tmp_path, monkeypatch):
    paths, repository, ctx, found = _missed_prediction(tmp_path)
    prediction_id = found["predictionId"]
    llm, clients = _clients()
    assert [outcome.state for outcome in _drain(paths.root, repository, clients)] == ["done"]
    sent = len(llm.calls)
    call(ctx, "reader.figure_explain", {"predictionId": prediction_id, "text": "p sets the split"})
    explained = prediction_id + gap_sources.FIGURE_EXPLANATION_SUFFIX
    assert ("reader_formative", explained, "queued") in _gap_jobs(repository)
    _hold_out(monkeypatch, "p5")  # the caption paragraph after the figure: context only
    outcomes = _drain(paths.root, repository, clients)
    assert [(outcome.source_id, outcome.state) for outcome in outcomes] == [(explained, "skipped")]
    assert len(llm.calls) == sent


def test_f1_an_unreadable_manifest_fails_closed(tmp_path):
    paths, repository, _ctx, found = _missed_prediction(tmp_path)
    with repository.connection() as connection:
        connection.execute("UPDATE interactive_figures SET input_span_ids_json = '{not json'")
        connection.commit()
    llm, clients = _clients()
    assert [outcome.state for outcome in _drain(paths.root, repository, clients)] == ["skipped"]
    assert llm.calls == []


def test_f1_an_open_manifest_still_reads(tmp_path, monkeypatch):
    paths, repository, _ctx, _found = _missed_prediction(tmp_path)
    _hold_out(monkeypatch, "p6")  # never sent to the author of p3's figure
    llm, clients = _clients()
    assert [outcome.state for outcome in _drain(paths.root, repository, clients)] == ["done"]
    assert any(purpose == "learner_gap_reading" for purpose, _payload in llm.calls)


# ---------------------------------------------------------------------------
# F4: the harness never coerces a check's answer
# ---------------------------------------------------------------------------

def _answering(value: str) -> str:
    """The flagship's right check, except that a wrong answer (and one it
    cannot parse) is answered with ``value`` instead of False."""

    return f'''
import sympy as sp

def check(reference, answer):
    x, p, lam = sp.symbols("x p lam", real=True)
    names = {{"x": x, "p": p, "lam": lam}}
    try:
        r = sp.sympify(reference, locals=names)
        a = sp.sympify(answer, locals=names)
    except Exception:
        return {value}
    for xv in (-3, -sp.Rational(1, 2), sp.Rational(1, 4), 2):
        for pv in (sp.Rational(1, 10), sp.Rational(1, 2)):
            for lv in (sp.Rational(1, 2), 2):
                try:
                    if abs(sp.N((r - a).subs({{x: xv, p: pv, lam: lv}}))) > 1e-12:
                        return {value}
                except Exception:
                    return {value}
    return True
'''


@needs_sandbox
@pytest.mark.parametrize("value", ["None", "0", '""'])
def test_f4_controls_answered_with_no_boolean_never_verify_a_figure(tmp_path, value):
    """The real harness, the real sandbox and the figure service: a check
    that accepts the definition and answers its controls with None, 0 or ""
    decided nothing, so the figure is an illustration."""

    paths, _repository = build_figure_vault(tmp_path / "vault")
    verifier = VerifierFake(program=_answering(value))
    figure = build(context(paths.root, author=AuthorFake(), verifier=verifier))["figure"]
    assert verifier.calls == 1
    assert figure["verification"] == "illustrative"
    assert "inconclusive" in figure["reason"]


@needs_sandbox
def test_f4_controls_answered_false_still_verify_through_the_same_harness(tmp_path):
    paths, _repository = build_figure_vault(tmp_path / "vault")
    figure = build(context(paths.root, author=AuthorFake(), verifier=VerifierFake(program=_answering("False"))))[
        "figure"]
    assert figure["verification"] == "verified"


@needs_sandbox
@pytest.mark.parametrize("value", ["None", "0", '""'])
def test_f4_the_harness_reports_each_answer_as_given(value):
    from tests.figure_fixtures import SOURCE_EXPRESSION

    compiled = S.parse_spec(flagship())
    answer = G.to_sympy(compiled.definitions["f"], compiled.definitions)
    result = V.run_source_match(answer, V.SourceCheck(SOURCE_EXPRESSION, _answering(value)))
    assert result["matched"] is False
    assert result["checks"] == [True, None, None]
    assert "inconclusive" in result["reason"]


_GENERATOR = '''
def generate(seed):
    return {"parameters": {"n": 2}, "stem": "What is 1 + 1? (" + str(seed) + ")", "solution": "2",
            "final_answer": "2", "checkpoints": []}

def check(draw, answer):
    if str(answer).strip() == draw["final_answer"]:
        return %s
    return %s
'''


@needs_sandbox
def test_f4_pf_generator_tests_count_an_inconclusive_answer_as_not_passing():
    inconclusive = pf_sandbox.run_generator_tests(_GENERATOR % ("True", "None"), seeds=[1])
    (entry,) = inconclusive.output["draws"]
    assert entry["self_check"] is True
    assert entry["negative_controls_rejected"] is False and entry["negative_controls_inconclusive"] is True
    unanswered = pf_sandbox.run_generator_tests(_GENERATOR % ("1", "False"), seeds=[1])
    (entry,) = unanswered.output["draws"]
    assert entry["self_check"] is None and entry["negative_controls_rejected"] is True
    # Booleans keep their meaning, sympy's included.
    typed = pf_sandbox.run_generator_tests(
        "import sympy\n" + _GENERATOR % ("sympy.true", "sympy.false"), seeds=[1])
    (entry,) = typed.output["draws"]
    assert entry["self_check"] is True and entry["negative_controls_rejected"] is True
    checked = pf_sandbox.check_generator_answers(_GENERATOR % ("True", "None"), [
        {"draw": entry["draw"], "answer": "2"}, {"draw": entry["draw"], "answer": "3"}])
    assert checked.output["checks"] == [True, None]


_EQUIVALENCE = '''
def check(reference, answer):
    if str(reference).strip() == str(answer).strip():
        return True
    return %s
'''


@needs_sandbox
def test_f4_pf_equivalence_confirms_nothing_when_a_control_is_answered_with_no_boolean():
    pairs = [{"program": "check", "reference": "2", "answer": "2"}, {"program": "check", "reference": "2",
                                                                     "answer": "3"}]
    unclear = pf_sandbox.run_equivalence_checks({"check": _EQUIVALENCE % "None"}, pairs)
    assert unclear.output["checks"] == [True, None]
    assert unclear.output["inconclusive_controls"] == {"check": True}
    assert pf_sandbox.equivalence_confirmations(unclear, 2) == ([None, None], False)
    plain = pf_sandbox.run_equivalence_checks({"check": _EQUIVALENCE % "False"}, pairs)
    assert plain.output["inconclusive_controls"] == {"check": False}
    assert pf_sandbox.equivalence_confirmations(plain, 2) == ([True, False], False)


# ---------------------------------------------------------------------------
# F3: the checked definition is what is drawn as the book's equation
# ---------------------------------------------------------------------------

def _plotting(*series: tuple[str, str], readouts: tuple[tuple[str, str], ...] = ()) -> dict:
    """A reconstruction of f(x) = x: one parameter, the given series and readouts."""

    return {
        "spec_version": "ifs-v1", "kind": "reconstructed",
        "source_claims": [{"span_id": "p3", "quote": EQUATION_TEXT}],
        "demonstrates": "the book's f",
        "parameters": [{"name": "p", "label": "p", "min": 0.1, "max": 0.9, "step": 0.1, "default": 0.5}],
        "definitions": [{"name": "f", "expr": "x"}],
        "panels": [
            {"kind": "function_plot", "x": {"var": "x", "min": -1, "max": 1},
             "series": [{"expr": expr, "label": label} for expr, label in series]},
            *({"kind": "readout", "label": label, "expr": expr} for expr, label in readouts),
        ],
        "invariants": [{"kind": "equals_source", "name": "f"}],
    }


def _verdict(tmp_path, monkeypatch, spec):
    # The verifier and the sandbox both say "matches": only the binding decides.
    monkeypatch.setattr(pf_sandbox, "run_equivalence_checks", _equivalence([True, False, False]))
    paths, _repository = build_figure_vault(tmp_path / "vault")
    verifier = VerifierFake()
    figure = build(context(paths.root, author=AuthorFake([spec]), verifier=verifier))["figure"]
    return figure, verifier


def test_f3_a_transformed_series_labelled_as_the_book_equation_is_an_illustration(tmp_path, monkeypatch):
    figure, verifier = _verdict(tmp_path, monkeypatch, _plotting(("2*f", "f(x)")))
    assert figure["verification"] == "illustrative"
    assert figure["label"] == "AI-built illustration of an interpretation · not checked against the book"
    assert "'f(x)' is labelled as the book's equation" in figure["reason"]
    assert verifier.calls == 0  # decided by structure: no verifier call is spent on it


@pytest.mark.parametrize("series, readouts", [
    ((("f", "density"), ("2*f", "f_X(x)")), ()),          # the quote's left-hand side names it
    ((("f", "f(x)"),), (("2*p", "f(p)"),)),                  # a readout under the definition's name
    ((("2*f", "density"),), ()),                             # nothing drawn is the checked definition
    ((("x", "f(x)"),), ()),                                  # the same values, not by reference
])
def test_f3_every_source_labelled_series_and_readout_must_be_the_checked_definition(
        tmp_path, monkeypatch, series, readouts):
    figure, _verifier = _verdict(tmp_path, monkeypatch, _plotting(*series, readouts=readouts))
    assert figure["verification"] == "illustrative"


@pytest.mark.parametrize("series", [
    (("f", "f(x)"),),
    (("f", "density"), ("2*f", "twice the density")),
])
def test_f3_the_checked_definition_drawn_by_reference_verifies(tmp_path, monkeypatch, series):
    figure, verifier = _verdict(tmp_path, monkeypatch, _plotting(*series))
    assert figure["verification"] == "verified" and verifier.calls == 1


def test_f3_the_flagship_is_bound():
    compiled = S.parse_spec(flagship())
    claims = [{"quote": EQUATION_TEXT, "verified": True}]
    assert V.displayed_source_problem(compiled, "f", claims) is None


# ---------------------------------------------------------------------------
# Integer bounds: counted loops (the golden corpus holds the shared cases)
# ---------------------------------------------------------------------------

def test_a_sum_near_the_safe_integers_counts_its_terms():
    seen: list[float] = []

    def term(k: float) -> float:
        seen.append(k)
        return 1.0

    top = float(G.MAX_SAFE_INTEGER)
    assert G.exact_sum(term, top - 2, top) == 3.0 and seen == [top - 2, top - 1, top]
    assert G.exact_sum(term, 1e20, 1e20 + 2) != G.exact_sum(term, 1e20, 1e20 + 2)  # NaN
    with pytest.raises(G.GrammarError, match="bounds"):
        G.parse("sum(1, k, -(1e20), 0)")


def test_pmf_supports_past_the_safe_integers_are_refused():
    from tests.figure_corpus import pmf_spec

    spec = pmf_spec()
    spec["panels"][0]["k"] = {"var": "k", "min": 9007199254740992, "max": 9007199254741000}
    with pytest.raises(S.SpecError, match="within"):
        S.parse_spec(spec)
    assert len(S.bar_ks(S.Axis(var="k", min=0, max=10_000))) == S.MAX_BARS


# ---------------------------------------------------------------------------
# F7: the reusable rows are reread inside the build lock
# ---------------------------------------------------------------------------

def test_f7_a_build_committed_between_the_reads_is_reused_inside_the_lock(tmp_path, monkeypatch):
    paths, repository = build_figure_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    request = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"])
    first = FS.build_figure(vault, repository, request, author_client=AuthorFake([flagship(kind="illustrative")]))
    assert first.reused is False
    # The interleaving: this build's first `reusable` read ran before the
    # other build committed (empty), its `latest_for_input` read after (the
    # committed row), so `seen` is that row and `latest == seen` in the lock.
    real = figure_store.reusable
    reads: list[bool] = []

    def before_the_commit(connection, input_hash, spec_version):
        reads.append(True)
        return None if len(reads) == 1 else real(connection, input_hash, spec_version)

    monkeypatch.setattr(figure_store, "reusable", before_the_commit)
    author = AuthorFake([flagship(kind="illustrative")])
    second = FS.build_figure(vault, Repository.attach(repository.sqlite_path), request, author_client=author)
    assert author.calls == 0  # no second paid generation
    assert second.reused is True and second.view["figure_id"] == first.view["figure_id"]
    assert len(reads) == 2 and len(rows(repository, "interactive_figures")) == 1


# ---------------------------------------------------------------------------
# F5: the backlog reconciles an explanation saved while gap reading was off
# ---------------------------------------------------------------------------

def _gaps_switch(paths, enabled: bool) -> None:
    config = paths.root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    value = "true" if enabled else "false"
    section = re.search(r"(?ms)^\[learner_text_gaps\]\n(.*?)(?=^\[|\Z)", text)
    if section is None:
        text = text.rstrip("\n") + f"\n\n[learner_text_gaps]\nenabled = {value}\n"
    elif re.search(r"(?m)^enabled = ", section.group(1)):
        body = re.sub(r"(?m)^enabled = \w+", f"enabled = {value}", section.group(1), count=1)
        text = text[:section.start(1)] + body + text[section.end(1):]
    else:
        text = text[:section.start(1)] + f"enabled = {value}\n" + text[section.start(1):]
    config.write_text(text, encoding="utf-8")


def test_f5_off_save_on_sweep_reads_the_explanation_once(tmp_path):
    paths, repository, ctx, found = _missed_prediction(tmp_path)
    prediction_id = found["predictionId"]
    explained = prediction_id + gap_sources.FIGURE_EXPLANATION_SUFFIX
    _llm, clients = _clients()
    assert [outcome.state for outcome in _drain(paths.root, repository, clients)] == ["done"]
    _gaps_switch(paths, False)
    ctx = context(paths.root)  # the app reloads the vault with gap reading off
    call(ctx, "reader.figure_explain", {"predictionId": prediction_id, "text": "p sets the split, not λ"})
    assert _gap_jobs(repository) == [("reader_formative", prediction_id, "done")]  # off: nothing queued
    _gaps_switch(paths, True)
    vault = load_vault(paths.root)
    assert sweep_backlog(vault, repository, dry_run=True)["reader_formative"] == 1
    assert sweep_backlog(vault, repository)["reader_formative"] == 1
    assert _gap_jobs(repository) == [("reader_formative", prediction_id, "done"),
                                     ("reader_formative", explained, "queued")]
    assert [outcome.source_id for outcome in _drain(paths.root, repository, clients)] == [explained]
    earlier, later = _gap_rows(repository)
    assert earlier["learner_text"] == "it rises"
    assert later["learner_text"] == "it rises. What changed, in my words: p sets the split, not λ"
    assert sweep_backlog(load_vault(paths.root), repository)["reader_formative"] == 0


def test_f5_an_explanation_the_first_reading_read_is_not_swept_again(tmp_path):
    paths, repository, ctx, found = _missed_prediction(tmp_path)
    call(ctx, "reader.figure_explain", {"predictionId": found["predictionId"], "text": "p sets the split"})
    _llm, clients = _clients()
    assert [outcome.state for outcome in _drain(paths.root, repository, clients)] == ["done"]
    (only,) = _gap_rows(repository)
    assert only["learner_text"] == "it rises. What changed, in my words: p sets the split"
    assert sweep_backlog(load_vault(paths.root), repository)["reader_formative"] == 0


def test_f5_a_prediction_never_read_is_swept_once_with_its_explanation(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    _gaps_switch(paths, False)
    ctx = context(paths.root, author=AuthorFake([flagship(kind="illustrative")]))
    figure = build(ctx)["figure"]
    found = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0,
                                                 "answer": "rises"})
    call(ctx, "reader.figure_explain", {"predictionId": found["predictionId"], "text": "p sets the split"})
    assert _gap_jobs(repository) == []
    _gaps_switch(paths, True)
    assert sweep_backlog(load_vault(paths.root), repository)["reader_formative"] == 1
    assert _gap_jobs(repository) == [("reader_formative", found["predictionId"], "queued")]

"""Reader RW5a: predictions are formative (spec §8.4, W1 tier 2; G24, G36).

A prediction writes ``figure_predictions`` only: no attempt, no evidence
observation, no field signal, nothing a scheduler or a mastery estimate
reads. Code decides whether it matched from the observed readout before and
after the prediction's change. A missed one (with its "what changed?" line
when written) becomes a ``reader_formative`` learner text through the existing
adapter, only while learner-text gaps and the Reader's formative switch are on.
"""

from __future__ import annotations

import json
import sqlite3

import pytest

from learnloop.diagnosis.text_gaps import jobs as gap_jobs
from learnloop.diagnosis.text_gaps import sources as gap_sources
from learnloop.diagnosis.text_gaps.provenance import formative_record
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from tests.figure_fixtures import (
    EXTRACTION,
    LEARNING_STATE_TABLES,
    AuthorFake,
    build,
    build_figure_vault,
    call,
    context,
    counts,
    flagship,
    rows,
    set_config,
)

FORMATIVE_TABLES = [*LEARNING_STATE_TABLES, "learner_text_gaps", "question_events", "reader_authored_questions",
                    "help_assists", "ad_reading_opportunities", "forecast_receipts", "router_decisions"]


def _figure(tmp_path, *, config: dict | None = None):
    paths, repository = build_figure_vault(tmp_path / "vault")
    for section, values in (config or {}).items():
        set_config(paths, section, **values)
    ctx = context(paths.root, author=AuthorFake([flagship(kind="illustrative")]))
    figure = build(ctx)["figure"]
    return paths, repository, ctx, figure


def _gap_jobs(repository):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT source_kind, source_id FROM learner_text_gap_jobs ORDER BY created_at")]


def test_g24_a_missed_prediction_writes_no_evidence_and_queues_a_formative_text(tmp_path):
    paths, repository, ctx, figure = _figure(tmp_path)
    before = counts(repository, FORMATIVE_TABLES)
    found = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0,
                                                 "answer": "rises"})
    # "If λ doubles, what happens to P(X ≤ 0)?" It stays at p.
    assert found["matched"] is False and found["answer"] == "same"
    assert abs(found["before"] - 0.3) < 1e-6 and abs(found["after"] - 0.3) < 1e-6
    assert counts(repository, FORMATIVE_TABLES) == before
    (row,) = rows(repository, "figure_predictions")
    assert row["matched"] == 0 and row["learner_answer"] == "rises" and row["extraction_id"] == EXTRACTION
    assert json.loads(row["observed_json"])["answer"] == "same"
    assert _gap_jobs(repository) == [{"source_kind": "reader_formative", "source_id": found["predictionId"]}]


def test_a_matched_prediction_queues_nothing(tmp_path):
    _paths, repository, ctx, figure = _figure(tmp_path)
    found = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 1,
                                                 "answer": "P(X ≤ 0)"})
    assert found["matched"] is True
    assert _gap_jobs(repository) == []


def test_the_formative_switches_keep_predictions_out_of_learner_text(tmp_path):
    _paths, repository, ctx, figure = _figure(tmp_path, config={"reader_formative": {"enabled": False}})
    call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0, "answer": "rises"})
    assert rows(repository, "figure_predictions") and _gap_jobs(repository) == []


def test_predictions_switch_off(tmp_path):
    _paths, repository, ctx, figure = _figure(tmp_path, config={"figures": {"predictions_enabled": False}})
    assert figure["predictions"] == []
    assert call(ctx, "reader.prompt_contract", {})["figures"]["predictions"] is False
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0, "answer": "rises"})
    assert caught.value.code == "predictions_disabled" and not rows(repository, "figure_predictions")


def test_a_prediction_is_answered_once_and_validated(tmp_path):
    _paths, repository, ctx, figure = _figure(tmp_path)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0, "answer": "maybe"})
    assert caught.value.code == "validation_error"
    with pytest.raises(SidecarError):
        call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 5, "answer": "same"})
    first = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0, "answer": "rises"})
    again = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0, "answer": "same"})
    assert again["predictionId"] == first["predictionId"] and again["learnerAnswer"] == "rises"
    assert len(rows(repository, "figure_predictions")) == 1
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"][0]
    assert listed["predictions"][0]["answered"]["predictionId"] == first["predictionId"]


def test_what_changed_is_kept_once_and_read_with_the_missed_prediction(tmp_path):
    paths, repository, ctx, figure = _figure(tmp_path)
    found = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0, "answer": "rises"})
    explained = call(ctx, "reader.figure_explain", {"predictionId": found["predictionId"],
                                                     "text": "λ squeezes both sides toward 0, but p sets the split"})
    assert explained["explanationText"] == "λ squeezes both sides toward 0, but p sets the split"
    again = call(ctx, "reader.figure_explain", {"predictionId": found["predictionId"], "text": "something else"})
    assert again["explanationText"] == explained["explanationText"]
    assert len(_gap_jobs(repository)) == 1
    vault = load_vault(paths.root)
    text = gap_sources.learner_text(vault, repository, "reader_formative", found["predictionId"])
    assert text is not None and text.source_kind == "reader_formative"
    assert text.text == "it rises. What changed, in my words: λ squeezes both sides toward 0, but p sets the split"
    assert text.context["question"] == "If λ doubles, what happens to P(X ≤ 0)?"
    assert text.context["style"] == "figure_prediction"
    assert "it stays the same" in text.context["expected_answer"]
    assert text.context["passage"] == "f_X(x) = p\\lambda e^{\\lambda x} for x < 0"  # the figure's own passage
    with repository.connection() as connection:
        record = formative_record(connection, found["predictionId"])
    assert record.inputs.sources and record.inputs.sources[0]["extraction_id"] == EXTRACTION
    assert gap_sources.missed_formative_ids(repository)[-1] == found["predictionId"]


def test_the_table_is_append_only_except_the_one_explanation(tmp_path):
    _paths, repository, ctx, figure = _figure(tmp_path)
    found = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0, "answer": "rises"})
    with repository.connection() as connection:
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute("UPDATE figure_predictions SET matched = 1 WHERE id = ?", (found["predictionId"],))
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute("DELETE FROM figure_predictions WHERE id = ?", (found["predictionId"],))
        connection.execute("UPDATE figure_predictions SET explanation_text = 'x' WHERE id = ?", (found["predictionId"],))
        with pytest.raises(sqlite3.DatabaseError):
            connection.execute("UPDATE figure_predictions SET explanation_text = 'y' WHERE id = ?",
                               (found["predictionId"],))


def test_the_backlog_sweep_queues_missed_predictions(tmp_path):
    paths, repository, ctx, figure = _figure(tmp_path, config={"reader_formative": {"enabled": False}})
    found = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0, "answer": "rises"})
    config = paths.root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    config.write_text(text.replace("[reader_formative]\nenabled = false", "[reader_formative]\nenabled = true"),
                      encoding="utf-8")
    vault = load_vault(paths.root)
    assert vault.config.reader_formative.enabled
    counts_ = gap_jobs.sweep_backlog(vault, repository, kinds=("reader_formative",))
    assert counts_["reader_formative"] == 1
    assert _gap_jobs(repository) == [{"source_kind": "reader_formative", "source_id": found["predictionId"]}]


def test_rw6a_lists_a_missed_prediction_as_worth_a_second_look(tmp_path):
    from learnloop.reader import reader_observations as RO
    from learnloop.reader.reader_sessions import ReaderSession

    _paths, repository, ctx, figure = _figure(tmp_path)
    found = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0, "answer": "rises"})
    session = ReaderSession(extraction_id=EXTRACTION, visit_ids=("v1",), started_at="2000-01-01T00:00:00+00:00",
                            ended_at="2999-01-01T00:00:00+00:00")
    observed = RO.prediction_observations(repository, extraction_id=EXTRACTION, session=session)
    assert [record.source_event_ids for record in observed] == [(found["predictionId"],)]
    assert observed[0].kind == "prediction_missed"


def test_the_reader_report_counts_figures_and_unsupported_kinds(tmp_path):
    from learnloop.reader.reader_report import build_reader_report

    paths, repository, ctx, figure = _figure(tmp_path)
    build(context(paths.root, author=AuthorFake([("unsupported", "a 3-D surface")])),
          {"extractionId": EXTRACTION, "spanIds": ["p2"]})
    call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0, "answer": "rises"})
    report = build_reader_report(repository.sqlite_path, figures_enabled=True)["figures"]
    assert report["built"] == {"illustrative": 1, "unsupported": 1}
    assert report["unsupported_by_kind"] == {"a 3-D surface": 1}
    assert report["predictions"] == 1 and report["predictions_missed"] == 1 and report["what_changed"] == 0
    assert "rises" not in json.dumps(report)

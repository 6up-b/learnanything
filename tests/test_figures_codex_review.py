"""Reader RW5a: the Codex review's findings, each reproduced (docs/reviews/reader-rw5a-codex-review.md).

The source-check (spec §8.3 step 3) and admission tests these rounds added were removed
with that machinery by the owner's scope decision of 2026-10-21; their successors
are in tests/test_figures_scope_redesign.py. What stays here still holds.

F1 a context neighbour held out after authoring withholds the figure everywhere;
F2 a region-built figure is anchored under its region's block;
F3 every ``equals_source`` definition must be checked before "matches the book";
F4 an inconclusive negative control is never a rejection;
F5 a later "what changed?" is read as its own text, the earlier reading kept;
F6 a missed prediction wakes the stopped gap worker;
F7 identical concurrent builds join one build, and a paid answer survives a crash.

Every model is a fake; the sandbox's equivalence runner is a fake here too
(its documented result shape), so nothing runs a verifier's program.
"""

from __future__ import annotations

import json
import threading
from types import SimpleNamespace

import pytest

from learnloop.content.authoring import pf_sandbox
from learnloop.db.repositories import Repository
from learnloop.diagnosis.text_gaps import sources as gap_sources
from learnloop.diagnosis.text_gaps.jobs import process_next_gap_job
from learnloop.diagnosis.text_gaps.pipeline import PipelineClients
from learnloop.diagnosis.text_gaps.provenance import formative_record
from learnloop.figures import service as FS
from learnloop.figures import verify as V
from learnloop.tutor.ai_contracts import LearnerGap
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers import figures as FH
from tests.figure_fixtures import (
    EXTRACTION,
    AuthorFake,
    VerifierFake,
    build,
    build_figure_vault,
    call,
    context,
    flagship,
    rows,
)
from tests.test_figure_region import REGION, crops  # noqa: F401 - the crop recorder fixture
from tests.text_gap_fakes import GapLLMFake


# ---------------------------------------------------------------------------
# F1: the complete input-span manifest
# ---------------------------------------------------------------------------

class _HeldSpans:
    """Exam material that holds out exactly these (extraction, span) keys."""

    def __init__(self, held: set[tuple[str, str]]) -> None:
        self.held = held
        self.material = SimpleNamespace(reasons={})

    def covers(self, extraction_id: str, span_id: str | None = None) -> bool:
        return span_id is not None and (str(extraction_id), str(span_id)) in self.held

    def withheld(self, keys):
        return frozenset(tuple(key) for key in keys if tuple(key) in self.held)


def _hold_out(monkeypatch, *spans: str) -> None:
    from learnloop.content.sources import exam_material as EM

    held = {(EXTRACTION, span) for span in spans}
    monkeypatch.setattr(EM, "exam_material", lambda _vault, _repository: _HeldSpans(held))


def test_f1_a_context_neighbour_held_out_after_authoring_withholds_the_figure(tmp_path, monkeypatch):
    paths, repository = build_figure_vault(tmp_path / "vault")
    author = AuthorFake([flagship(kind="illustrative")])
    ctx = context(paths.root, author=author)
    result = build(ctx)  # the selection is p3; p1, p2, p4 and p5 go as context
    figure = result["figure"]
    assert [block["span_id"] for block in author.contexts[0]["around"]] == ["p1", "p2", "p4", "p5"]
    (row,) = rows(repository, "interactive_figures")
    assert json.loads(row["input_span_ids_json"]) == ["p3", "p1", "p2", "p4", "p5"]
    found = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0,
                                                 "answer": "rises"})
    with repository.connection() as connection:
        record = formative_record(connection, found["predictionId"])
    assert record.inputs.sources[0]["span_ids"] == ["p1", "p2", "p3", "p4", "p5"]

    _hold_out(monkeypatch, "p4")  # a neighbour only: the selection itself is open
    assert call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"] == []
    assert FH.deliver_figure(ctx, result) == {"figure": None, "reused": False, "withheld": True}
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 1,
                                            "answer": "P(X ≤ 0)"})
    assert caught.value.code == "exam_material"
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_explain", {"predictionId": found["predictionId"], "text": "p sets it"})
    assert caught.value.code == "exam_material"
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_revise", {"figureId": figure["figureId"], "note": "start at 0.1"})
    assert caught.value.code == "exam_material"


def test_f1_a_neighbour_left_out_at_build_time_does_not_withhold_later(tmp_path, monkeypatch):
    """The manifest is what was sent: p6 was never context of p3's figure."""

    paths, _repository = build_figure_vault(tmp_path / "vault")
    ctx = context(paths.root, author=AuthorFake([flagship(kind="illustrative")]))
    figure = build(ctx)["figure"]
    _hold_out(monkeypatch, "p6")
    assert [f["figureId"] for f in call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]] == [
        figure["figureId"]]


# ---------------------------------------------------------------------------
# F2: a region's figure lands under the region's block
# ---------------------------------------------------------------------------

def test_f2_a_region_built_figure_is_anchored_under_its_region(tmp_path, crops):  # noqa: F811
    paths, _repository = build_figure_vault(tmp_path / "vault")
    ctx = context(paths.root, author=AuthorFake([flagship(kind="illustrative"), ("unsupported", "a 3-D surface")],
                                               images=True))
    figure = build(ctx, {"extractionId": EXTRACTION, "spanIds": [], "region": REGION})["figure"]
    assert figure["spanIds"] == [] and figure["anchorSpanId"] == "p4"
    (listed,) = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert listed["anchorSpanId"] == "p4"
    other = {"spanId": "p4", "bbox": [110.0, 110.0, 200.0, 200.0]}
    unsupported = build(ctx, {"extractionId": EXTRACTION, "spanIds": [], "region": other})["figure"]
    assert unsupported["verification"] == "unsupported" and unsupported["anchorSpanId"] == "p4"


# ---------------------------------------------------------------------------
# F3 and F4: complete source coverage; inconclusive controls
# ---------------------------------------------------------------------------

def _equivalence(checks):
    calls: list[list[dict]] = []

    def run(programs, pairs, **_kwargs):
        calls.append(pairs)
        return pf_sandbox.SandboxResult(True, output={"checks": list(checks), "degenerate": {}})

    run.calls = calls  # type: ignore[attr-defined]
    return run


# ---------------------------------------------------------------------------
# F5 and F6: the formative reading of a later "what changed?"; the worker
# ---------------------------------------------------------------------------

def _clients():
    llm = GapLLMFake(reading=LearnerGap(kind="wording", prerequisite_name=None, prerequisite_line=None))
    return llm, PipelineClients(judge=lambda: llm, reader=lambda: llm, decider=None, drafter=lambda: llm,
                                tutor=None, embedder=None)


def _gap_rows(repository):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT source_kind, source_id, learner_text FROM learner_text_gaps ORDER BY created_at, id")]


def _gap_jobs(repository):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(
            "SELECT source_kind, source_id, state FROM learner_text_gap_jobs ORDER BY created_at, id")]


def _missed_prediction(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    ctx = context(paths.root, author=AuthorFake([flagship(kind="illustrative")]))
    figure = build(ctx)["figure"]
    found = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0,
                                                 "answer": "rises"})
    return paths, repository, ctx, found


def test_f5_an_explanation_after_the_reading_is_read_as_its_own_text(tmp_path):
    paths, repository, ctx, found = _missed_prediction(tmp_path)
    prediction_id = found["predictionId"]
    _llm, clients = _clients()
    first = process_next_gap_job(paths.root, repository, owner="t", clients=clients)
    assert first.state == "done" and first.source_id == prediction_id
    call(ctx, "reader.figure_explain", {"predictionId": prediction_id, "text": "p sets the split, not λ"})
    explained = prediction_id + gap_sources.FIGURE_EXPLANATION_SUFFIX
    assert _gap_jobs(repository) == [("reader_formative", prediction_id, "done"),
                                     ("reader_formative", explained, "queued")]
    second = process_next_gap_job(paths.root, repository, owner="t", clients=clients)
    assert second.state == "done" and second.source_id == explained
    (earlier, later) = _gap_rows(repository)
    # The earlier judgment is kept as it was read; the later one reads the explanation.
    assert (earlier["source_id"], earlier["learner_text"]) == (prediction_id, "it rises")
    assert later["source_id"] == explained
    assert later["learner_text"] == "it rises. What changed, in my words: p sets the split, not λ"
    with repository.connection() as connection:
        record = formative_record(connection, explained)
    assert record.inputs.sources and record.inputs.sources[0]["extraction_id"] == EXTRACTION


def test_f5_an_explanation_before_the_reading_is_read_with_it_once(tmp_path):
    paths, repository, ctx, found = _missed_prediction(tmp_path)
    call(ctx, "reader.figure_explain", {"predictionId": found["predictionId"], "text": "p sets the split"})
    assert _gap_jobs(repository) == [("reader_formative", found["predictionId"], "queued")]
    _llm, clients = _clients()
    assert process_next_gap_job(paths.root, repository, owner="t", clients=clients).state == "done"
    assert process_next_gap_job(paths.root, repository, owner="t", clients=clients) is None
    (only,) = _gap_rows(repository)
    assert only["learner_text"] == "it rises. What changed, in my words: p sets the split"


def test_f5_an_explained_source_with_no_explanation_reads_nothing(tmp_path):
    paths, repository, _ctx, found = _missed_prediction(tmp_path)
    vault = load_vault(paths.root)
    explained = found["predictionId"] + gap_sources.FIGURE_EXPLANATION_SUFFIX
    assert gap_sources.learner_text(vault, repository, "reader_formative", explained) is None


def test_f6_a_missed_prediction_and_its_explanation_wake_the_worker(tmp_path, monkeypatch):
    paths, repository = build_figure_vault(tmp_path / "vault")
    ctx = context(paths.root, author=AuthorFake([flagship(kind="illustrative")]))
    woken: list[bool] = []
    monkeypatch.setattr(ctx.post_attempt_worker, "notify", lambda: woken.append(True))
    figure = build(ctx)["figure"]
    call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 1, "answer": "P(X ≤ 0)"})
    assert woken == []  # matched: nothing queued, nothing woken
    found = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0,
                                                 "answer": "rises"})
    assert woken == [True]
    call(ctx, "reader.figure_explain", {"predictionId": found["predictionId"], "text": "p sets the split"})
    assert woken == [True]  # its job is still queued: the one reading reads the explanation
    _llm, clients = _clients()
    process_next_gap_job(paths.root, repository, owner="t", clients=clients)
    other = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0,
                                                 "answer": "falls"})
    assert other["predictionId"] == found["predictionId"]  # answered once


def test_f6_the_stopped_worker_starts_and_reads_the_prediction(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    ctx = context(paths.root, author=AuthorFake([flagship(kind="illustrative")]))
    worker = ctx.post_attempt_worker
    worker.autostart = True
    _llm, clients = _clients()
    worker.gap_clients = lambda _vault: clients
    worker.client_factory = lambda _vault: None
    worker.embedding_factory = lambda _vault: None
    assert worker.running is False
    try:
        figure = build(ctx)["figure"]
        call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0, "answer": "rises"})
        assert worker.running is True
        remaining, _waited = worker.wait_for(
            lambda: [job[1] for job in _gap_jobs(repository) if job[2] in ("queued", "leased")], timeout=60)
    finally:
        worker.shutdown()
    assert remaining == []
    assert [row["source_kind"] for row in _gap_rows(repository)] == ["reader_formative"]


# ---------------------------------------------------------------------------
# F7: identical concurrent builds; a crash between the receipt and the row
# ---------------------------------------------------------------------------

def test_f7_identical_concurrent_builds_join_one_build(tmp_path):
    paths, repository = build_figure_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    entered, release = threading.Event(), threading.Event()

    def slow(_context):
        entered.set()
        assert release.wait(30)
        return flagship(kind="illustrative")

    author = AuthorFake([slow])
    request = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"])
    outcomes: list[FS.BuildOutcome] = []
    errors: list[BaseException] = []

    def run():
        try:
            outcomes.append(FS.build_figure(vault, Repository.attach(repository.sqlite_path), request,
                                            author_client=author))
        except BaseException as exc:  # noqa: BLE001 - reported below
            errors.append(exc)

    first = threading.Thread(target=run)
    first.start()
    assert entered.wait(30)
    second = threading.Thread(target=run)
    second.start()
    second.join(0.5)
    assert second.is_alive()  # it waits on the first build, it does not call the model
    release.set()
    first.join(30)
    second.join(30)
    assert not errors, errors
    assert author.calls == 1 and len(rows(repository, "interactive_figures")) == 1
    assert sorted(outcome.reused for outcome in outcomes) == [False, True]
    assert len({outcome.view["figure_id"] for outcome in outcomes}) == 1


def test_f7_a_paid_answer_survives_a_crash_before_the_row(tmp_path, monkeypatch):
    from learnloop.db.stores import figures as store

    paths, repository = build_figure_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    author = AuthorFake([flagship(kind="illustrative"), flagship(kind="illustrative")])
    request = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"])
    real_insert = store.insert_figure

    def crash(*_args, **_kwargs):
        raise RuntimeError("the process stopped")

    monkeypatch.setattr(store, "insert_figure", crash)
    with pytest.raises(RuntimeError):
        FS.build_figure(vault, repository, request, author_client=author)
    assert author.calls == 1 and not rows(repository, "interactive_figures")
    monkeypatch.setattr(store, "insert_figure", real_insert)
    outcome = FS.build_figure(vault, repository, request, author_client=author)
    # The same request is the same paid answer: recovered, not asked again.
    assert author.calls == 1 and outcome.reused is False
    assert outcome.view["verification"] == "illustrative" and len(rows(repository, "interactive_figures")) == 1


def test_f7_a_stored_failure_is_a_new_generation_that_asks_afresh(tmp_path):
    from tests.figure_fixtures import half_density

    paths, repository = build_figure_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    author = AuthorFake([half_density(), half_density(), flagship(kind="illustrative")])
    request = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"])
    assert FS.build_figure(vault, repository, request, author_client=author).view["verification"] == "failed"
    again = FS.build_figure(vault, repository, request, author_client=author)
    assert again.view["verification"] == "illustrative" and author.calls == 3
    ids = [context["request_id"] for context in author.contexts]
    assert ids[0] == ids[1] != ids[2]


def test_f7_a_second_shown_row_for_one_input_is_refused_by_the_schema(tmp_path):
    import sqlite3

    paths, repository = build_figure_vault(tmp_path / "vault")
    build(context(paths.root, author=AuthorFake([flagship(kind="illustrative")])))
    (row,) = rows(repository, "interactive_figures")
    with repository.connection() as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO interactive_figures (id, extraction_id, origin, spec_json, spec_version, kind, "
                "verification, prompt_version, input_hash, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                ("fig_dup", EXTRACTION, "selection", row["spec_json"], row["spec_version"], "illustrative",
                 "illustrative", row["prompt_version"], row["input_hash"], row["created_at"]))

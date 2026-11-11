"""What other test files use from ``tests/test_figures_codex_review.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from types import SimpleNamespace

from learnloop.diagnosis.text_gaps.pipeline import PipelineClients
from learnloop.tutor.ai_contracts import LearnerGap

from tests.figure_fixtures import EXTRACTION, AuthorFake, build, build_figure_vault, call, context, flagship
from tests.text_gap_fakes import GapLLMFake


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

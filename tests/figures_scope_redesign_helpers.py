"""What other test files use from ``tests/test_figures_scope_redesign.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from contextlib import contextmanager

from learnloop.ai.execution import model_call
from learnloop.tutor.ai_contracts import LearnerGap

from tests.text_gap_fakes import ChoiceDecider, GapLLMFake


class _Counter:
    def __init__(self, flip=None, after: int | None = None) -> None:
        self.flip, self.after, self.admitted = flip, after, 0

    def entered(self) -> None:
        self.admitted += 1
        if self.after is not None and self.admitted == self.after and self.flip is not None:
            self.flip()


class _GatedReader(GapLLMFake):
    def __init__(self, counter: _Counter, **kwargs) -> None:
        super().__init__(**kwargs)
        self.counter = counter

    def complete(self, request):
        with model_call(self, purpose=request.purpose, prompt=request.prompt):
            self.counter.entered()
            return super().complete(request)


class _GatedDecider(ChoiceDecider):
    """The in-process Decider double, its ``model_call`` counted."""

    def __init__(self, counter: _Counter, **kwargs) -> None:
        super().__init__(**kwargs)
        original = self._model_call

        @contextmanager
        def counted(client, **call):
            with original(client, **call) as metadata:
                counter.entered()
                yield metadata

        self._model_call = counted


def _gap_clients(counter: _Counter):
    from learnloop.diagnosis.text_gaps.pipeline import PipelineClients

    reading = LearnerGap(kind="prerequisite", prerequisite_name="Eigenvectors",
                         prerequisite_line="Vectors a matrix only scales.")
    llm = _GatedReader(counter, reading=reading)
    decider = _GatedDecider(counter, kind="prerequisite")
    return PipelineClients(judge=lambda: llm, reader=lambda: llm, decider=lambda: decider, drafter=lambda: llm,
                           tutor=None, embedder=None)


def _gap_job(tmp_path):
    from tests.figures_codex_review_helpers import _missed_prediction

    return _missed_prediction(tmp_path)

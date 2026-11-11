"""What other test files use from ``tests/test_reader_reconnect.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.reader import reader_dialogue as RD
from learnloop.reader.ai_contracts import ReadingQuickCheck

from tests.structured_ai import StructuredClientFake
from tests.reader_dialogue_helpers import _CLOCK
from tests.reader_guidance_helpers import _setup as _guide_setup


class FakeClient(StructuredClientFake):
    # Billed like Codex on the subscription (no price needed): these tests are
    # about authoring; the passage check's spend admission, isolation and
    # claim are tests/test_reader_passage_check.py's.
    provider_type = "codex_sdk"

    def __init__(self, span_ids=("s1",)) -> None:
        self.calls: list = []
        self.span_ids = list(span_ids)

    def run_reading_quick_check(self, context):
        self.calls.append(context)
        return ReadingQuickCheck(
            question_md="Why is A's eigenbasis orthonormal?",
            expected_answer_md="Because A is symmetric; the spectral theorem gives an orthonormal eigenbasis.",
            span_ids=self.span_ids,
        )


def _setup(tmp_path):
    vault, repository = _guide_setup(tmp_path)
    return vault, repository


def _ask(vault, repo, question, parent=None, *, extraction_id="ext1", span_id="s1", **kwargs):
    return RD.ask(vault, repo, RD.StubReaderClient(), extraction_id=extraction_id, span_id=span_id,
                  question_md=question, parent_exchange_id=parent, clock=_CLOCK, **kwargs)

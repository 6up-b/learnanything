"""What other test files use from ``tests/test_reader_active_reading.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.ai.transport import ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop.reader.ai_contracts import ReadingActiveCheck

from tests.structured_ai import StructuredClientFake


EVIDENCE_TABLES = ("practice_attempts", "grading_evidence", "facet_recall_state", "facet_capability_evidence",
                   "probe_observations", "fsrs_states")


class ActiveClient(StructuredClientFake):
    provider_name = "fake"
    provider_type = "codex_sdk"
    model = "fake-model"

    def __init__(self, result: ReadingActiveCheck | None = None, *, isolates: bool = True) -> None:
        self.result = result or ReadingActiveCheck(question_md="What comes next after this line?",
                                                   next_step_span_ids=["s2"], span_ids=["s2"])
        self.isolates = isolates
        self.requests: list = []

    def supports(self, capability: str) -> bool:
        return self.isolates if capability == ISOLATED_TURN else capability == STRUCTURED_COMPLETION

    def complete(self, request):
        self.requests.append(request)
        return self.result

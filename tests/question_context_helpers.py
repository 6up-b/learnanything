"""What other test files use from ``tests/test_question_context.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.tutor.ai_contracts import TutorAnswer

from tests.structured_ai import StructuredClientFake


class FakeTutorClient(StructuredClientFake):
    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-model"

    def __init__(self, *, question_channel="epistemic", question_type="mechanism"):
        self.question_channel = question_channel
        self.question_type = question_type

    def run_tutor_qa(self, context):
        return TutorAnswer(
            answer_md="Think about the factor shapes.",
            question_type=self.question_type,
            facets=list(context.candidate_facets),
            question_channel=self.question_channel,
        )

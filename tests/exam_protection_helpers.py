"""What other test files use from ``tests/test_exam_protection.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


class _RecordingReaderTutor:
    """A reader tutor that records every request's manifest spans."""

    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-tutor"

    def __init__(self) -> None:
        self.contexts: list = []
        self._fake = None

    def supports(self, capability: str) -> bool:
        from tests.structured_ai import StructuredClientFake

        return StructuredClientFake().supports(capability)

    def complete(self, request):
        from tests.structured_ai import StructuredClientFake
        from learnloop.tutor.ai_contracts import TutorAnswer

        owner = self

        class _Answer(StructuredClientFake):
            def run_tutor_qa(self, context):
                owner.contexts.append(context)
                return TutorAnswer(answer_md="Read the worked example again.", question_type="clarification",
                                   facets=[])

        return _Answer().complete(request)

    def consume_usage(self):
        from tests.structured_ai import StructuredClientFake

        return StructuredClientFake().consume_usage()

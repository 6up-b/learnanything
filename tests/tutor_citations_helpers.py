"""What other test files use from ``tests/test_tutor_citations.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.tutor.ai_contracts import TutorAnswer
from learnloop.content.synthesis.source_set_synthesis import create_study_map
from learnloop.vault.loader import load_vault

from tests.structured_ai import StructuredClientFake
from tests.source_set_synthesis_helpers import FakeSynthesisClient, _setup


_CLOCK = FrozenClock(datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC))
_ITEM_ID = "pi_identify_symmetry"


class _CitingTutorClient(StructuredClientFake):
    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-model"

    def __init__(self, citations):
        self._citations = citations
        self.contexts = []

    def run_tutor_qa(self, context):
        self.contexts.append(context)
        return TutorAnswer(
            answer_md="A symmetric matrix satisfies A^T = A.",
            question_type="mechanism",
            facets=list(context.candidate_facets),
            citations=self._citations,
        )


def _mapped_vault(tmp_path, *, with_exam=True):
    root, repo = _setup(tmp_path, with_exam=with_exam)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo,
                     clock=_CLOCK, apply=True, brief={"outcome": "exam prep"})
    return load_vault(root), repo

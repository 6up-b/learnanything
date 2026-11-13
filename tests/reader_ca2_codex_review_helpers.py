"""What other test files use from ``tests/test_reader_ca2_codex_review.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import pytest

from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.db.repositories import Repository
from learnloop.tutor.ai_contracts import TutorAnswer, TutorCitation
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.helpers import create_basic_vault
from tests.structured_ai import StructuredClientFake
from tests.ux_phase1_support import set_config


ITEM = "pi_svd_define_001"
TAG = LATEST_ALGORITHM_VERSION


class FakeTutor(StructuredClientFake):
    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-model"

    def __init__(self, question_type: str = "mechanism", answer_md: str = "Think about the shapes.",
                 cite_first: bool = False) -> None:
        self.question_type = question_type
        self.answer_md = answer_md
        self.cite_first = cite_first
        self.contexts: list = []

    def run_tutor_qa(self, context):
        self.contexts.append(context)
        citations = []
        if self.cite_first and context.source_spans:
            span = context.source_spans[0]
            citations = [TutorCitation(extraction_id=str(span["extraction_id"]), span_id=str(span["span_id"]))]
        return TutorAnswer(answer_md=self.answer_md, question_type=self.question_type,
                           facets=list(context.candidate_facets), citations=citations)


class PlanTutor(FakeTutor):
    """The ChatGPT plan's transport, as the spend module recognises it."""

    provider_type = "chatgpt_plan"


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _vault(tmp_path, updates: dict | None = None):
    paths = create_basic_vault(tmp_path / "vault")
    set_config(paths.root, {("algorithms", "algorithm_version"): TAG, **(updates or {})})
    return paths, load_vault(paths.root), Repository(paths.sqlite_path)


@pytest.fixture
def sidecar(tmp_path, monkeypatch):
    import learnloop_sidecar.handlers.tutor_qa as handler

    holder: dict = {"tutor": FakeTutor(question_type="clarification")}

    class Ready:
        ready = True

    monkeypatch.setattr(handler, "ready_tutor_qa_provider", lambda vault: ("fake", Ready(), holder["tutor"]))

    def build(updates: dict | None = None, tutor: FakeTutor | None = None, name: str = "vault"):
        if tutor is not None:
            holder["tutor"] = tutor
        paths, _vault_, _repository = _vault(tmp_path / name, updates)
        ctx = SidecarContext()
        ctx.load(paths.root)
        return paths, ctx, holder["tutor"]

    return build


def _expected(vault) -> str:
    expected = vault.practice_items[ITEM].expected_answer
    return expected if isinstance(expected, str) else str(expected)

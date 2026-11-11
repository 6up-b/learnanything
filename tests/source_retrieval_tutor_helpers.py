"""What other test files use from ``tests/test_source_retrieval_tutor.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.ai.spend import SpendCaps
from learnloop.clock import FrozenClock
from learnloop.ops.embedding_backfill import backfill_embeddings
from learnloop.source_retrieval.recipes import SOURCE_RETRIEVAL_RECIPES
from learnloop.source_retrieval.tutor import TutorSpanProvider
from learnloop.tutor.ai_contracts import PromotionAnalysis, TutorAnswer, TutorCitation
from learnloop.tutor.tutor_qa import ask_question
from learnloop.vault.embedding_recipes import EMBEDDING_RECIPES

from tests.source_retrieval_fakes import FakeSourceLLM, HashingEmbedder, build_retrieval_vault, loaded
from tests.structured_ai import StructuredClientFake


CLOCK = FrozenClock(datetime(2026, 10, 12, 12, 0, 0, tzinfo=UTC))
CAPS = SpendCaps(max_candidates=10_000, max_pairs=0, max_calls=100, max_total_tokens=10**8,
                 max_estimated_usd=10.0)
QUESTION = "Why are the eigenvalues the roots of the characteristic polynomial?"


class CitingTutor(StructuredClientFake):
    """Cites every span it was given, so the allowlist is what keeps citations honest."""

    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-tutor"

    def __init__(self):
        self.contexts = []

    def run_tutor_qa(self, context):
        self.contexts.append(context)
        return TutorAnswer(
            answer_md="Think about det(A - tI).", question_type="mechanism",
            facets=list(context.candidate_facets),
            citations=[TutorCitation(extraction_id=span["extraction_id"], span_id=span["span_id"])
                       for span in context.source_spans]
            + [TutorCitation(extraction_id="ext_exam", span_id="s2")],
        )


def setup(tmp_path, *, embed=True):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    repository.insert_entity_source_link(
        entity_type="learning_object", entity_id="lo_matrices", locator="span:ext_book/s7",
        relation="primary", source_id="src_book", revision_id="rev_book", extraction_id="ext_book")
    if embed:
        for registry, recipes in ((SOURCE_RETRIEVAL_RECIPES, ("source_block",)),
                                  (EMBEDDING_RECIPES, ("facet/definition",))):
            report = backfill_embeddings(loaded(paths), caps=CAPS, recipes=recipes, registry=registry,
                                         client_factory=HashingEmbedder)
            assert report["status"] == "complete", report
    return paths, repository


def provider(llm=None):
    llm = llm or FakeSourceLLM()
    return TutorSpanProvider(embedder=HashingEmbedder(), rewrite_client=llm, rerank_client=llm, clock=CLOCK), llm


def ask(paths, repository, tutor, *, span_provider=None, question=QUESTION, session="s1"):
    return ask_question(loaded(paths), repository, tutor, context="practice", question_md=question,
                        practice_item_id="pi_eigen_1", session_id=session,
                        source_span_provider=span_provider, clock=CLOCK)


class ReaderTutor(StructuredClientFake):
    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-tutor"

    def run_tutor_qa(self, context):
        return TutorAnswer(answer_md="Look at the dot product.", question_type="clarification", facets=[])

    def run_promotion_analysis(self, _context):
        return PromotionAnalysis()

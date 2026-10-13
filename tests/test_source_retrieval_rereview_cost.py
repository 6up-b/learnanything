"""Slice 2 T6 Codex re-review: the retrieval time box, typing cost and honest hints.

F15: the query embedding request carries the time left. F16: typing searches
reuse the meaning-search coverage until the library changes. F18: the "Enter
also searches by meaning" state checks the embedding route.
"""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from learnloop.ai.embedding import current_embedding_timeout, embedding_request_timeout
from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.spend import SpendCaps
from learnloop.clock import FrozenClock
from learnloop.ops.embedding_backfill import backfill_embeddings
from learnloop.source_retrieval import dense as dense_module
from learnloop.source_retrieval import recipes as recipes_module
from learnloop.source_retrieval.dense import clear_cache
from learnloop.source_retrieval.library import search_library
from learnloop.source_retrieval.recipes import SOURCE_RETRIEVAL_RECIPES
from learnloop.source_retrieval.tutor import TutorSpanProvider
from learnloop.tutor.ai_contracts import TutorAnswer, TutorCitation
from learnloop.tutor.tutor_qa import ask_question
from tests.helpers import append_config_toml
from tests.source_retrieval_fakes import (
    FakeSourceLLM,
    HashingEmbedder,
    build_retrieval_vault,
    loaded,
    seed_source,
)
from tests.structured_ai import StructuredClientFake

CLOCK = FrozenClock(datetime(2026, 10, 12, 12, 0, 0, tzinfo=UTC))
CAPS = SpendCaps(max_candidates=10_000, max_pairs=0, max_calls=100, max_total_tokens=10**8,
                 max_estimated_usd=10.0)
QUESTION = "What does it mean to compute eigenvalues of a diagonal matrix?"


@pytest.fixture(autouse=True)
def _fresh_dense_cache():
    clear_cache()
    yield
    clear_cache()


class CitingTutor(StructuredClientFake):
    provider_name = "fake_tutor"
    provider_type = "fake"
    model = "fake-tutor"

    def __init__(self):
        self.contexts = []

    def run_tutor_qa(self, context):
        self.contexts.append(context)
        return TutorAnswer(
            answer_md="Think about what an eigenvalue is.", question_type="clarification",
            facets=list(context.candidate_facets),
            citations=[TutorCitation(extraction_id=span["extraction_id"], span_id=span["span_id"])
                       for span in context.source_spans],
        )


def _backfill(paths, embedder=None) -> None:
    embedder = embedder or HashingEmbedder()
    report = backfill_embeddings(loaded(paths), caps=CAPS, recipes=("source_block",),
                                 registry=SOURCE_RETRIEVAL_RECIPES, client_factory=lambda: embedder)
    assert report["status"] == "complete", report


def _provider(llm=None, embedder=None):
    llm = llm or FakeSourceLLM()
    return TutorSpanProvider(embedder=embedder or HashingEmbedder(), rewrite_client=llm, rerank_client=llm,
                             clock=CLOCK), llm


def _ask(paths, repository, tutor, provider, *, context="practice", question=QUESTION, session="s1"):
    return ask_question(loaded(paths), repository, tutor, context=context, question_md=question,
                        practice_item_id="pi_eigen_1", session_id=session, source_span_provider=provider,
                        clock=CLOCK)


# --- F15 ------------------------------------------------------------------------------------


class TimeoutRecordingEmbedder(HashingEmbedder):
    def __init__(self, *, fail_with: str | None = None) -> None:
        super().__init__()
        self.timeouts: list[float | None] = []
        self.fail_with = fail_with

    def embed(self, inputs, task_prefix):
        self.timeouts.append(current_embedding_timeout())
        if self.fail_with is not None and task_prefix == "retrieval-query":
            error = AIProviderUnavailable(f"Embedding request failed ({self.fail_with})")
            error.provider_error = self.fail_with
            raise error
        return super().embed(inputs, task_prefix)


def test_the_tutors_query_embedding_request_carries_the_time_left_when_the_time_box_is_restored(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    _backfill(paths)
    append_config_toml(paths.root, "[source_retrieval]\nretrieval_timeout_seconds = 7\n"
                                   "tutor_deadline_cancels = true\n")
    embedder = TimeoutRecordingEmbedder()
    _ask(paths, repository, CitingTutor(), _provider(embedder=embedder)[0],
         question="Why are eigenvalues the roots of the characteristic polynomial?")
    assert embedder.timeouts and all(timeout is not None and 0 < timeout <= 7 for timeout in embedder.timeouts)
    assert current_embedding_timeout() is None  # restored after the request


def test_by_default_the_tutors_query_embedding_has_no_time_box(tmp_path):
    # Owner, 2026-10-12: no deadline cancellation for the tutor; the time is logged.
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    _backfill(paths)
    append_config_toml(paths.root, "[source_retrieval]\nretrieval_timeout_seconds = 7\n")
    embedder = TimeoutRecordingEmbedder()
    _ask(paths, repository, CitingTutor(), _provider(embedder=embedder)[0],
         question="Why are eigenvalues the roots of the characteristic polynomial?")
    assert embedder.timeouts == [None]


def test_the_deep_library_search_query_embedding_carries_the_time_left(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    _backfill(paths)
    append_config_toml(paths.root, "[source_retrieval]\nretrieval_timeout_seconds = 9\nquery_rewrite = false\n")
    embedder = TimeoutRecordingEmbedder()
    result = search_library(loaded(paths), repository, query="orthogonal vectors", deep=True, embedder=embedder)
    assert embedder.timeouts and all(timeout is not None and 0 < timeout <= 9 for timeout in embedder.timeouts)
    assert result["retrieval"]["query_embedding"]["status"] == "embedded"


def test_a_query_embedding_that_runs_out_of_time_is_labelled_timed_out(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    _backfill(paths)
    embedder = TimeoutRecordingEmbedder(fail_with="APITimeoutError")
    result = search_library(loaded(paths), repository, query="orthogonal vectors", deep=True, embedder=embedder)
    embedding = result["retrieval"]["query_embedding"]
    assert embedding["status"] == "timed_out" and "meaning" not in result["retrieval"]["lists"]
    assert result["hits"]  # keyword search still answers


def test_the_openai_embedding_client_sends_the_request_timeout(monkeypatch):
    from learnloop.ai.providers.openai_embedding import OpenAIEmbeddingProviderClient
    from learnloop.config import OpenAIEmbeddingProviderConfig
    from tests.openai_fakes import install_fake_openai
    from tests.test_openai_embedding_client import response

    module = install_fake_openai(monkeypatch, embeddings=[response([3, 4]), response([0, 1])])
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    built = OpenAIEmbeddingProviderClient("embed", OpenAIEmbeddingProviderConfig(dimensions=2))
    sdk = module.instances[0]
    with embedding_request_timeout(2.5):
        built.embed(["a query"], "retrieval-query")
    built.embed(["a passage"], "retrieval-document")
    assert sdk.embedding_requests[0]["timeout"] == 2.5
    assert "timeout" not in sdk.embedding_requests[1]  # the client default otherwise


# --- F16 ------------------------------------------------------------------------------------


def test_typing_searches_reuse_the_coverage_until_the_library_changes(tmp_path, monkeypatch):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    _backfill(paths)
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    # A library larger than the per-extraction manifest cache.
    monkeypatch.setattr(recipes_module, "_MANIFEST_CACHE_SIZE", 1)
    built = []
    original = dense_module.extraction_manifest

    def counting(connection, sqlite_path, extraction_id, *args, **kwargs):
        built.append(extraction_id)
        return original(connection, sqlite_path, extraction_id, *args, **kwargs)

    monkeypatch.setattr(dense_module, "extraction_manifest", counting)
    vault = loaded(paths)
    first = search_library(vault, repository, query="orth")
    assert built  # the first keystroke computes the coverage
    built.clear()
    for query in ("ortho", "orthog", "orthogo"):
        again = search_library(vault, repository, query=query)
        assert again["meaning_search"] == first["meaning_search"]
    assert built == []  # nothing re-read or re-hashed while the library is unchanged
    seed_source(repository, source_id="src_new", revision_id="rev_new", extraction_id="ext_new",
                title="Freshly imported", units={"new": ("Chapter 9 Projections", [
                    ("Orthogonal projection onto a subspace minimizes the distance to it.", 1)])},
                furniture=False)
    changed = search_library(vault, repository, query="orthogonal")
    assert built and changed["meaning_search"]["status"] == "partial"
    assert changed["meaning_search"]["sources"] == first["meaning_search"]["sources"] + 1


# --- F18 ------------------------------------------------------------------------------------


def test_meaning_search_is_unavailable_when_the_embedding_route_is_not_ready(tmp_path, monkeypatch):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    _backfill(paths)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    vault = loaded(paths)
    typed = search_library(vault, repository, query="determinant")
    assert typed["meaning_search"]["status"] == "unavailable"
    assert "OPENROUTER_API_KEY" in typed["meaning_search"]["reason"]
    assert typed["meaning_search"]["sources_covered"] == typed["meaning_search"]["sources"]  # counts kept
    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-test-key")
    assert search_library(vault, repository, query="determinant")["meaning_search"]["status"] == "ready"
    # An injected embedder (tests, benchmarks) is its own route.
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    injected = search_library(vault, repository, query="determinant", embedder=HashingEmbedder())
    assert injected["meaning_search"]["status"] == "ready"

"""Slice 2 T6 at its merge: retrieval degrades when Codex is out.

T6's four routes are unset by default, so the live rewrite (``source_query_rewrite``)
and the tutor-span verification (``source_rerank``) follow ``ai.active_provider``,
which is Codex. When Codex is exhausted (every turn raises ``CodexUnavailable``)
or not ready at all, the design is: the library search keeps its keyword and
meaning hits (no rewrite), the tutor keeps the learning object's linked spans
(verification skipped or failed, nothing picked), and neither crashes nor loses
the learner's question. Nothing here calls a real provider: the Codex client is
a fake routed through the real route planning (``plan_route``/``resolve_client``).
"""
from __future__ import annotations

from contextlib import closing
from types import SimpleNamespace

import pytest

from learnloop.ai.errors import CodexUnavailable
from learnloop.db.connection import connect
from learnloop.source_retrieval.library import search_library
from learnloop.source_retrieval.tutor import TutorSpanProvider
from tests.helpers import append_config_toml
from tests.source_retrieval_fakes import HashingEmbedder, loaded
from tests.test_source_retrieval_tutor import CLOCK, QUESTION, CitingTutor, ask, setup

T6_LLM_ROUTES = ("source_query_rewrite", "source_rerank")


class ExhaustedCodex:
    """The active Codex profile once the subscription's usage limit is hit."""

    provider_name = "codex"
    provider_type = "codex_sdk"
    model = None

    def __init__(self) -> None:
        self.purposes: list[str] = []

    def supports(self, capability: str) -> bool:
        return capability in {"structured_completion", "bounded_structured_completion", "isolated_turn"}

    def complete(self, request):
        self.purposes.append(request.purpose)
        raise CodexUnavailable("You've hit your usage limit. Try again on Oct 18th, 2026.")


@pytest.fixture
def codex(monkeypatch):
    """Route T6's unset LLM routes to a fake Codex; ``codex.ready`` toggles readiness."""

    import learnloop.practice_index.paid as paid

    real = paid.ready_client_for_task
    state = SimpleNamespace(client=ExhaustedCodex(), ready=True, tasks=[])

    def fake_ready(vault_root, config, task, *, explicit=None, **kwargs):
        if task not in T6_LLM_ROUTES:
            return real(vault_root, config, task, explicit=explicit, **kwargs)
        state.tasks.append((task, explicit))
        if not state.ready:
            return SimpleNamespace(ready=False, client=None,
                                   runtime=SimpleNamespace(message="Codex is not signed in"))
        return SimpleNamespace(ready=True, client=state.client, runtime=SimpleNamespace(message=None))

    monkeypatch.setattr(paid, "ready_client_for_task", fake_ready)
    return state


def _source_relevance_rows(repository) -> int:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM judgment_ledger WHERE task = 'source_relevance'").fetchone()[0]


def test_the_unset_t6_routes_follow_the_active_plan_profile(tmp_path):
    from learnloop.practice_index.paid import plan_route

    paths, _repository = setup(tmp_path, embed=False)
    vault = loaded(paths)
    # Plan-first transport T1: the active profile is the tool-free ChatGPT plan.
    assert vault.config.ai.active_provider == "chatgpt"
    for task in T6_LLM_ROUTES:
        assert getattr(vault.config.ai.routing, task) is None
        route = plan_route(vault, task)
        assert route.provider == "chatgpt" and route.billing == "subscription"


def test_an_exhausted_codex_leaves_the_tutor_on_its_linked_spans(tmp_path, codex):
    paths, repository = setup(tmp_path)
    append_config_toml(paths.root, "[source_retrieval]\ntutor_query_rewrite = true\n")
    linked = CitingTutor()
    ask(paths, repository, linked, session="s1")
    tutor = CitingTutor()
    # As the sidecar builds it: no injected clients, so the routes resolve.
    span_provider = TutorSpanProvider(embedder=HashingEmbedder(), clock=CLOCK)
    result = ask(paths, repository, tutor, span_provider=span_provider, question=QUESTION, session="s2")

    assert result["answer_md"]
    assert tutor.contexts[0].source_spans == linked.contexts[0].source_spans
    event = repository.question_event(result["event_id"])
    assert event["answer_status"] == "answered"
    manifest = event["source_context"]["source_retrieval"]
    assert manifest["basis"] == "lo_provenance"
    assert manifest["verification"]["status"] == "failed"
    assert manifest["verification"]["reason"] == "AIProviderUnavailable"
    assert manifest["search"]["rewrite"]["status"] == "failed"
    # Both routes really were tried on Codex, and nothing was judged.
    # One capped call and its one retry each, all refused.
    assert sorted(codex.client.purposes) == ["source_query_rewrite"] * 2 + ["source_rerank"] * 2
    assert {task for task, _explicit in codex.tasks} == set(T6_LLM_ROUTES)
    assert _source_relevance_rows(repository) == 0


def test_a_codex_that_is_not_ready_buys_no_retrieval_for_the_tutor(tmp_path, codex):
    paths, repository = setup(tmp_path, embed=False)
    codex.ready = False
    tutor = CitingTutor()
    span_provider = TutorSpanProvider(clock=CLOCK)
    result = ask(paths, repository, tutor, span_provider=span_provider)

    assert result["answer_md"] and tutor.contexts[0].source_spans[0]["span_id"] == "s7"
    manifest = repository.question_event(result["event_id"])["source_context"]["source_retrieval"]
    assert manifest["basis"] == "lo_provenance"
    assert manifest["verification"] == {"status": "unavailable", "reason": "Codex is not signed in"}
    assert "search" not in manifest  # nothing was retrieved when verification could not run
    assert codex.client.purposes == []
    assert _source_relevance_rows(repository) == 0


@pytest.mark.parametrize("ready", [True, False])
def test_the_deep_library_search_keeps_keyword_and_meaning_hits_without_codex(tmp_path, codex, ready):
    paths, repository = setup(tmp_path)
    codex.ready = ready
    vault = loaded(paths)
    result = search_library(vault, repository, query="Why is the determinant zero?", deep=True,
                            embedder=HashingEmbedder())

    assert result["hits"] and result["deep"] is True
    assert result["basis"] == "keyword+meaning"
    assert result["retrieval"]["rewrite"]["status"] == ("failed" if ready else "unavailable")
    assert all("rewrite" not in name for hit in result["hits"] for name in hit["matched_by"])
    # One capped call and its one retry, both refused; none when Codex is not ready.
    assert codex.client.purposes == (["source_query_rewrite"] * 2 if ready else [])
    # Typing (no Enter) never routes to Codex at all.
    codex.client.purposes.clear()
    typed = search_library(vault, repository, query="determinant")
    assert typed["hits"] and typed["basis"] == "keyword" and codex.client.purposes == []

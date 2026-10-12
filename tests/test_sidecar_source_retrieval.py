"""Slice 2 T6 over the real sidecar: library search, span -> LO suggestions, tutor wiring."""
from __future__ import annotations

import io
import json

from learnloop_sidecar.server import serve
from tests.source_retrieval_fakes import build_retrieval_vault


def _rpc(messages: list[dict]) -> list[dict]:
    stdin = io.StringIO("".join(json.dumps(message) + "\n" for message in messages))
    stdout = io.StringIO()
    serve(stdin, stdout)
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


def _init(root) -> dict:
    return {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(root)}}


def test_library_search_rpc_ranks_by_keyword_and_says_so(tmp_path):
    paths, _repository = build_retrieval_vault(tmp_path / "vault")
    responses = _rpc([
        _init(paths.root),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.search_sources", "params": {"query": "determinants"}},
        {"jsonrpc": "2.0", "id": 3, "method": "reader.search_sources",
         "params": {"query": "Why does swapping rows change a determinant?", "deep": True}},
    ])
    typed, deep = responses[1]["result"], responses[2]["result"]
    assert typed["basis"] == "keyword" and typed["deep"] is False
    assert {hit["spanId"] for hit in typed["hits"]} >= {"s6", "s7"}
    assert typed["searchedSources"] == 2
    # Deep, but no source-block vectors and no rewrite route: honestly keyword only.
    assert deep["deep"] is True and deep["basis"] == "keyword"
    assert deep["hits"][0]["spanId"] == "s7"
    # Review F3: the typing response says Enter would not search by meaning here.
    assert typed["meaningSearch"]["status"] == "incomplete"
    assert set(typed["meaningSearch"]) >= {"sources", "sourcesCovered", "blocks", "blocksCovered"}


def test_span_learning_objects_rpc_labels_suggestions(tmp_path):
    paths, _repository = build_retrieval_vault(tmp_path / "vault")
    responses = _rpc([
        _init(paths.root),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.span_learning_objects",
         "params": {"extractionId": "ext_book", "spanId": "s12"}},
    ])
    result = responses[1]["result"]
    assert result["provenance"] == [] and result["status"] == "suggested"
    assert result["suggestions"][0]["learningObjectId"] == "lo_inner"
    assert result["suggestions"][0]["label"] == "suggestion"


def test_ask_tutor_question_injects_the_source_span_provider(monkeypatch, tmp_path):
    from learnloop.source_retrieval.tutor import TutorSpanProvider
    from learnloop_sidecar.handlers import tutor_qa as handler

    paths, _repository = build_retrieval_vault(tmp_path / "vault")
    seen = {}

    class Runtime:
        ready = True

    def fake_ask(*args, **kwargs):
        seen.update(kwargs)
        return {"event_id": "qe_1", "answer_md": "ok", "question_type": "mechanism", "facets": [],
                "hint_equivalent": True, "leak_suspected": False, "citations": [], "remaining": 2}

    monkeypatch.setattr(handler, "ready_tutor_qa_provider", lambda vault: ("codex", Runtime(), object()))
    monkeypatch.setattr(handler, "ask_question", fake_ask)
    responses = _rpc([
        _init(paths.root),
        {"jsonrpc": "2.0", "id": 2, "method": "ask_tutor_question",
         "params": {"context": "practice", "question": "Why?", "practiceItemId": "pi_eigen_1",
                    "sessionId": "s1"}},
    ])
    assert "result" in responses[1], responses[1]
    assert isinstance(seen["source_span_provider"], TutorSpanProvider)

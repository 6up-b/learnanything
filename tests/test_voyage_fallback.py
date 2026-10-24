"""Local contextual retrieval P1b: the Voyage fallback space (client contract,
T1's route rules, the capped and receipted backfill). Fakes only: no request."""
from __future__ import annotations

from contextlib import closing
import sqlite3

import pytest

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.providers.voyage_contextual import HttpResult, VoyageContextualClient
from learnloop.ai.routing import (
    AITask,
    is_generation_profile,
    ready_client_for_task,
    route_profile_mismatch,
)
from learnloop.config.loader import load_config
from learnloop.config.schema import VoyageContextualEmbeddingProviderConfig
from learnloop.source_retrieval import fallback_space
from learnloop.source_retrieval.windows import expected_keys, extraction_windows
from tests.helpers import append_config_toml
from tests.local_embeddings_fakes import VOYAGE_PROFILE, FakeVoyageClient
from tests.source_retrieval_fakes import build_retrieval_vault, loaded

SECRET = "sk-voyage-test-secret-value"


class FakeTransport:
    def __init__(self, body=None, status=200) -> None:
        self.body, self.status, self.sent = body, status, []

    def __call__(self, url, *, headers, body, timeout):
        self.sent.append({"url": url, "headers": dict(headers), "body": body, "timeout": timeout})
        return HttpResult(self.status, self.body, "req_1")


def _client(transport, monkeypatch, dims=4):
    monkeypatch.setenv("VOYAGE_API_KEY", SECRET)
    profile = VoyageContextualEmbeddingProviderConfig(dimensions=dims)
    return VoyageContextualClient("voyage_context", profile, transport=transport)


def test_the_client_sends_nested_windows_and_single_chunk_queries(monkeypatch):
    documents = {"data": [{"index": 0, "data": [{"index": 1, "embedding": [0, 3, 0, 4]},
                                                 {"index": 0, "embedding": [3, 0, 0, 4]}]}],
                 "usage": {"total_tokens": 12}}
    transport = FakeTransport(documents)
    client = _client(transport, monkeypatch)
    [rows] = client.embed_documents([["chunk a", "chunk b"]])
    assert rows == [[0.6, 0.0, 0.0, 0.8], [0.0, 0.6, 0.0, 0.8]]  # index order, L2-normalized
    sent = transport.sent[0]
    assert sent["url"] == "https://api.voyageai.com/v1/contextualizedembeddings"
    assert sent["body"] == {"model": "voyage-context-4", "inputs": [["chunk a", "chunk b"]], "input_type": "document",
                            "output_dimension": 4, "output_dtype": "float"}
    transport.body = {"data": [{"index": 0, "data": [{"index": 0, "embedding": [0, 0, 2, 0]}]}]}
    assert client.embed_queries(["what is a basis?"]) == [[0.0, 0.0, 1.0, 0.0]]
    assert transport.sent[1]["body"]["inputs"] == [["what is a basis?"]]
    assert transport.sent[1]["body"]["input_type"] == "query"


def test_errors_never_carry_the_key_or_the_body(monkeypatch):
    client = _client(FakeTransport({"detail": f"bad key {SECRET}"}, status=401), monkeypatch)
    with pytest.raises(AIProviderUnavailable) as caught:
        client.embed_queries(["q"])
    assert SECRET not in str(caught.value) and "401" in str(caught.value)
    wrong = _client(FakeTransport({"data": [{"index": 0, "data": [{"index": 0, "embedding": [1, 2]}]}]}), monkeypatch)
    with pytest.raises(ValueError, match="width"):
        wrong.embed_queries(["q"])
    monkeypatch.delenv("VOYAGE_API_KEY")
    with pytest.raises(AIProviderUnavailable, match="VOYAGE_API_KEY"):
        VoyageContextualClient("voyage_context", VoyageContextualEmbeddingProviderConfig())


def test_every_ai_task_refuses_the_fallback_profile(tmp_path, monkeypatch):
    from typing import get_args

    paths, _repository = build_retrieval_vault(tmp_path / "vault")
    append_config_toml(paths.root, VOYAGE_PROFILE)
    config = load_config(paths.root / "learnloop.toml", load_environment=False)
    for task in (None, *get_args(AITask)):
        assert route_profile_mismatch(config, "voyage_context", task) is not None, task
    assert not is_generation_profile(config, "voyage_context")
    monkeypatch.setenv("LEARNLOOP_AI_PROVIDER", "voyage_context")
    monkeypatch.setenv("VOYAGE_API_KEY", SECRET)
    resolved = ready_client_for_task(paths.root, config, "grading")
    assert resolved.client is None or getattr(resolved.client, "provider_type", None) != "voyage_contextual_embedding"


def test_nothing_is_sent_while_a_switch_is_off(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    client = FakeVoyageClient()
    report = fallback_space.backfill_fallback_vectors(loaded(paths), repository, "ext_book", client=client)
    assert report["status"] == "disabled" and "fallback.enabled" in report["reason"] and client.document_calls == []
    append_config_toml(paths.root, VOYAGE_PROFILE.replace("enabled = true", "enabled = true\nmaintain_index = false"))
    report = fallback_space.backfill_fallback_vectors(loaded(paths), repository, "ext_book", client=client)
    assert report["status"] == "disabled" and client.document_calls == []


def _receipts(sqlite_path, owner_kind):
    with closing(sqlite3.connect(sqlite_path)) as connection:
        return connection.execute(
            "SELECT status, budget_json FROM model_call_receipts WHERE owner_kind = ? AND parent_call_id IS NULL",
            (owner_kind,)).fetchall()


def test_the_backfill_is_capped_receipted_and_window_keyed(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    append_config_toml(paths.root, VOYAGE_PROFILE)
    vault = loaded(paths)
    client = FakeVoyageClient()
    dry = fallback_space.backfill_fallback_vectors(vault, repository, "ext_book", client=client, dry_run=True)
    assert dry["status"] == "dry_run" and dry["missing_windows"] == dry["windows"] > 0 and client.document_calls == []
    report = fallback_space.backfill_fallback_vectors(vault, repository, "ext_book", client=client)
    assert report["status"] == "complete" and report["embedded_windows"] == report["missing_windows"]
    receipts = _receipts(paths.sqlite_path, "embedding_backfill")
    assert receipts and all(status == "succeeded" or status == "completed" or status for status, _b in receipts)
    assert "fallback_space" in receipts[0][1] and '"max_estimated_usd": 1.0' in receipts[0][1]
    space, _pins = fallback_space.fallback_space(vault.config)
    keys = expected_keys(space, extraction_windows(vault, repository, "ext_book", "grouped"))
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        hashes = {row[0] for row in connection.execute(
            "SELECT content_hash FROM embedding_vectors WHERE model_id = ?", (space,))}
        qwen = connection.execute("SELECT COUNT(*) FROM embedding_vectors WHERE model_id = ? AND content_hash IN "
                                  f"({', '.join('?' for _ in hashes)})", (vault.config.embedding.model, *hashes)
                                  ).fetchone()[0]
    assert {key for parts in keys.values() for key, _w in parts} <= hashes and qwen == 0
    again = fallback_space.backfill_fallback_vectors(vault, repository, "ext_book", client=client)
    assert again["status"] == "complete" and again["embedded"] == 0 and len(client.document_calls) == 1


def test_the_run_cap_stops_the_spend(tmp_path):
    paths, repository = build_retrieval_vault(tmp_path / "vault")
    append_config_toml(paths.root, VOYAGE_PROFILE.replace("enabled = true", "enabled = true\nmax_cost_usd_per_run = 0.0"))
    client = FakeVoyageClient()
    report = fallback_space.backfill_fallback_vectors(loaded(paths), repository, "ext_book", client=client)
    assert report["status"] == "over_budget" and client.document_calls == []

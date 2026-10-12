"""Paid calls through the REAL chat-provider adapter: every physical request is admitted.

A metered route (OpenRouter, OpenAI-compatible keys) must not send a request
the caps did not admit: no hidden transport retry and no hidden JSON repair.
A repair or retry happens only as a new, separately admitted request under the
retry cap. Codex (subscription) keeps its documented exception.
"""
from __future__ import annotations

import json

import pytest

from learnloop.ai.providers.openrouter import OpenRouterProviderClient
from learnloop.ai.spend import SpendCaps
from learnloop.config import AIProviderConfig
from learnloop.db.repositories import Repository
from learnloop.practice_index.dossiers import generate_dossiers
from learnloop.vault.loader import load_vault
from learnloop.vault.repository import open_vault_repository
from tests.openai_fakes import FakeAPIConnectionError, install_fake_openai
from tests.practice_index_fakes import build_practice_vault, enable_practice_index

DOSSIER = json.dumps({
    "covers": ["eigenvalues"], "excludes": [], "moves": ["solve det(A - tI) = 0"],
    "errors": ["sign slips"], "contrast": [],
})


@pytest.fixture
def practice(tmp_path, monkeypatch):
    paths = build_practice_vault(tmp_path / "vault")
    enable_practice_index(paths, embeddings=False)
    open_vault_repository(paths.root, paths.sqlite_path)
    monkeypatch.setenv("TEST_ROUTER_KEY", "fake")
    monkeypatch.setattr("learnloop.ai.providers.openai_chat._sleep", lambda _: None)
    return paths


def _router(monkeypatch, *responses):
    fake = install_fake_openai(monkeypatch, *responses)
    client = OpenRouterProviderClient("router", AIProviderConfig(
        type="openrouter", model="vendor/model", api_key_env="TEST_ROUTER_KEY",
    ))
    return fake, client


def _caps(*, calls: int, retries: int) -> SpendCaps:
    return SpendCaps(max_candidates=100, max_calls=calls, max_retries=retries,
                     max_total_tokens=1_000_000, max_estimated_usd=1.0)


def _physical_receipts(paths) -> int:
    with Repository(paths.sqlite_path).connection() as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM model_call_receipts WHERE owner_kind='practice_dossiers' "
            "AND purpose='chat_request'").fetchone()[0]


def test_a_metered_timeout_sends_no_request_the_caps_did_not_admit(practice, monkeypatch):
    fake, client = _router(monkeypatch, FakeAPIConnectionError("t1"),
                           FakeAPIConnectionError("t2"), DOSSIER)
    report = generate_dossiers(load_vault(practice.root), caps=_caps(calls=1, retries=0),
                               client=client, price_per_million=1.0, facet_ids=["facet_eigen"])
    assert len(fake.instances[0].requests) == 1
    assert report["charged"]["calls"] == 1 and report["charged"]["retries"] == 0
    assert report["status"] == "provider_failed"
    assert _physical_receipts(practice) == 1


def test_each_metered_retry_is_admitted_and_charged_separately(practice, monkeypatch):
    fake, client = _router(monkeypatch, FakeAPIConnectionError("t1"),
                           FakeAPIConnectionError("t2"), DOSSIER)
    report = generate_dossiers(load_vault(practice.root), caps=_caps(calls=3, retries=2),
                               client=client, price_per_million=1.0, facet_ids=["facet_eigen"])
    assert report["status"] == "complete", report
    assert len(fake.instances[0].requests) == 3
    assert report["charged"]["calls"] == 3 and report["charged"]["retries"] == 2
    assert _physical_receipts(practice) == 3


def test_a_metered_invalid_answer_gets_no_hidden_repair_request(practice, monkeypatch):
    fake, client = _router(monkeypatch, "not json", DOSSIER)
    capped = generate_dossiers(load_vault(practice.root), caps=_caps(calls=1, retries=0),
                               client=client, price_per_million=1.0, facet_ids=["facet_eigen"])
    assert len(fake.instances[0].requests) == 1
    assert capped["charged"]["calls"] == 1 and capped["generated"] == 0
    # A repair is a new attempt, admitted and charged under the retry cap.
    fake, client = _router(monkeypatch, "not json", DOSSIER)
    report = generate_dossiers(load_vault(practice.root), caps=_caps(calls=2, retries=1),
                               client=client, price_per_million=1.0, facet_ids=["facet_eigen"])
    assert report["status"] == "complete", report
    assert len(fake.instances[0].requests) == 2
    assert report["charged"]["calls"] == 2 and report["charged"]["retries"] == 1


def test_a_metered_transport_that_cannot_bound_requests_fails_closed(practice):
    class Unbounded:
        provider_name = "unbounded"
        provider_type = "openrouter"
        model = "vendor/model"
        calls = 0

        def supports(self, capability):
            return capability == "structured_completion"

        def complete(self, request):
            type(self).calls += 1
            raise AssertionError("an unbounded metered transport must not be called")

    report = generate_dossiers(load_vault(practice.root), caps=_caps(calls=10, retries=2),
                               client=Unbounded(), price_per_million=1.0,
                               facet_ids=["facet_eigen"])
    assert report["status"] == "unavailable", report
    assert "physical requests" in report["reason"]
    assert Unbounded.calls == 0

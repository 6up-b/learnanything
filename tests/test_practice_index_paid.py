"""Paid calls through the REAL chat-provider adapter: every physical request is admitted.

A metered route (OpenRouter, OpenAI-compatible keys) must not send a request
the caps did not admit: no hidden transport retry and no hidden JSON repair.
A repair or retry happens only as a new, separately admitted request under the
retry cap. Codex (subscription) keeps its documented exception.
"""
from __future__ import annotations

import json

import pytest

from learnloop.ai.execution import record_model_calls, single_request
from learnloop.ai.providers.openrouter import OpenRouterProviderClient
from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import SpendBudget, SpendCaps, SpendEstimate
from learnloop.ai.structured_contracts import (
    Predicate,
    RecoveryAllowance,
    checked_structured_answer,
    contract_of,
    correction_prompt,
    recover_from_receipts,
    recovery_note,
)
from learnloop.ai.transport import execute_structured_operation
from learnloop.config import AIProviderConfig
from learnloop.db.repositories import Repository
from learnloop.db.stores.practice_index import completed_root_receipts
from learnloop.practice_index.dossiers import generate_dossiers
from learnloop.vault.loader import load_vault
from learnloop.vault.repository import open_vault_repository
from tests.openai_fakes import FakeAPIConnectionError, install_fake_openai
from tests.practice_index_fakes import build_practice_vault, enable_practice_index
from tests.structured_contracts_helpers import Refused, refused

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


# -- the shared contract step on a metered route (learnloop.ai.structured_contracts) -----------------------------

class _Covers(WireModel):
    covers: list[str]


_COVERED = contract_of(Predicate("no_covers", lambda answer: bool(answer.covers), "Name at least one covered idea."))
_KEY = "practice_index:checked"
_PROMPT = "Name the ideas this facet covers."


def _metered_checked(paths, client, budget):
    """A checked call whose every attempt is admitted and charged by ``budget``; the correction as a retry."""

    repository = Repository(paths.sqlite_path)

    def send(attempt, check):
        estimate = SpendEstimate(calls=1, retries=1 if attempt.ordinal else 0, total_tokens=100, estimated_usd=0.0001)
        with record_model_calls(repository, owner_kind="contract_check", owner_id="run"), \
                budget.request(estimate), single_request():
            return execute_structured_operation(client, purpose="cover_check", prompt=attempt.prompt,
                                                result_model=_Covers, check=check)

    def admit():
        used, caps = budget.used, budget.caps
        return used.retries < caps.max_retries and used.calls < caps.max_calls

    return checked_structured_answer(first_prompt=_PROMPT, contract=_COVERED, send=send,
                                     recovery=RecoveryAllowance(admit=admit), checkpoint=None,
                                     failure=refused, request_key=_KEY)


def _roots(paths):
    with Repository(paths.sqlite_path).connection() as connection:
        rows = connection.execute(
            "SELECT status, error_type, prompt_hash, output_text, budget_json FROM model_call_receipts "
            "WHERE purpose='cover_check' AND parent_call_id IS NULL ORDER BY started_at DESC, id DESC").fetchall()
    columns = ("status", "error_type", "prompt_hash", "output_text", "budget_json")
    return [dict(zip(columns, row, strict=True)) for row in rows]


def test_a_metered_contract_correction_is_admitted_and_charged_as_a_retry(practice, monkeypatch):
    fake, client = _router(monkeypatch, '{"covers": []}', '{"covers": ["eigenvalues"]}')
    budget = SpendBudget(_caps(calls=2, retries=1))
    result = _metered_checked(practice, client, budget)
    assert result.answer.covers == ["eigenvalues"]
    assert len(fake.instances[0].requests) == 2
    assert (budget.used.calls, budget.used.retries) == (2, 1)
    assert fake.instances[0].requests[1]["messages"][-1]["content"] == correction_prompt(_PROMPT, _COVERED[0])


def test_with_no_retry_left_a_metered_contract_failure_sends_nothing_more(practice, monkeypatch):
    fake, client = _router(monkeypatch, '{"covers": []}', '{"covers": ["eigenvalues"]}')
    budget = SpendBudget(_caps(calls=2, retries=0))
    with pytest.raises(Refused) as raised:
        _metered_checked(practice, client, budget)
    assert len(fake.instances[0].requests) == 1
    assert (budget.used.calls, budget.used.retries) == (1, 0)
    assert raised.value.info.reason == "recovery_refused"


def test_a_rejected_answer_stays_on_a_failed_receipt_and_only_the_correction_is_recoverable(practice, monkeypatch):
    _fake, client = _router(monkeypatch, '{"covers": []}', '{"covers": ["eigenvalues"]}')
    _metered_checked(practice, client, SpendBudget(_caps(calls=2, retries=1)))
    correction, rejected = _roots(practice)
    assert (rejected["status"], rejected["error_type"], rejected["output_text"]) == (
        "failed", "ContractRejected", '{"covers":[]}')
    assert recovery_note(rejected["budget_json"]) is None
    assert recovery_note(correction["budget_json"]) == {"request_key": _KEY, "failed": "no_covers", "ordinal": 1}
    with Repository(practice.sqlite_path).connection() as connection:
        completed = completed_root_receipts(connection, purpose="cover_check")
    assert [receipt["output_text"] for receipt in completed] == ['{"covers":["eigenvalues"]}']
    recovered = recover_from_receipts(_roots(practice), first_prompt=_PROMPT, request_key=_KEY,
                                      contract=_COVERED, read=_Covers.model_validate_json)
    assert recovered is not None and recovered[0].covers == ["eigenvalues"]
    # Under any other original key the correction is not this call's answer.
    assert recover_from_receipts(_roots(practice), first_prompt=_PROMPT, request_key="practice_index:other",
                                 contract=_COVERED, read=_Covers.model_validate_json) is None

"""Slice 1 M1 spend admission per PHYSICAL request (Codex review F3 / F16).

Metered routes admit every physical request (transport retries and JSON
repairs included) and hand the transport the admitted output limit.
Subscription routes (Codex on the owner's ChatGPT subscription, Slice A §5
rule 6) count one call per logical request against the call cap and are not
bounded per physical request; cancellation still stops them.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import BaseModel

from learnloop.ai.execution import model_call, report_call_usage
from learnloop.ai.providers.openai_chat import OpenAIChatProviderClient
from learnloop.ai.spend import SpendCancelled, SpendCaps, SpendLimitExceeded
from learnloop.ai.transport import STRUCTURED_COMPLETION, StructuredRequest, execute_structured_operation
from learnloop.config import AIProviderConfig
from learnloop.diagnosis.offline_review.spend import OUTPUT_ALLOWANCE, ReviewSpend

from tests.openai_fakes import install_fake_openai


class Answer(BaseModel):
    answer: str


def _metered(monkeypatch, *, max_tokens: int | None, contents: list[str]):
    install_fake_openai(monkeypatch)
    monkeypatch.setenv("TEST_KEY", "unused")
    client = OpenAIChatProviderClient(
        "metered", AIProviderConfig(type="openai_chat", base_url="https://unused.invalid", api_key_env="TEST_KEY", model="fake", max_tokens=max_tokens)
    )
    requests: list[dict[str, Any]] = []
    queue = list(contents)

    def create(**kwargs):
        requests.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content=queue.pop(0)))],
            usage={"prompt_tokens": 100, "completion_tokens": 50},
        )

    client._client.chat.completions.create = create
    return client, requests


def _spend(client, caps: SpendCaps, *, route: str = "diagnosis", cancelled=None) -> ReviewSpend:
    spend = ReviewSpend(caps, price_per_million=1.0, cancelled=cancelled)
    spend.register(route, client)
    return spend


def test_a_json_repair_is_a_second_admitted_request_on_a_metered_route(monkeypatch):
    client, requests = _metered(monkeypatch, max_tokens=9_000, contents=["not json", '{"answer": "x"}'])
    spend = _spend(client, SpendCaps(max_calls=1, max_retries=0, max_total_tokens=10**6, max_estimated_usd=10.0))
    with spend.collector.observing(), pytest.raises(SpendLimitExceeded):
        with spend.request("diagnosis", "diagnosis", input_tokens=1_000):
            execute_structured_operation(client, purpose="diagnosis", prompt="p", result_model=Answer)
    # The repair was refused BEFORE it was sent.
    assert len(requests) == 1
    assert (spend.budget.used.calls, spend.budget.used.retries) == (1, 0)


def test_admitted_repairs_are_charged_and_capped_by_the_admitted_output(monkeypatch):
    client, requests = _metered(monkeypatch, max_tokens=9_000, contents=["not json", '{"answer": "x"}'])
    spend = _spend(client, SpendCaps(max_calls=2, max_retries=1, max_total_tokens=10**6, max_estimated_usd=10.0))
    with spend.collector.observing(), spend.request("diagnosis", "diagnosis", input_tokens=1_000):
        assert execute_structured_operation(client, purpose="diagnosis", prompt="p", result_model=Answer).answer == "x"
    assert len(requests) == 2
    assert (spend.budget.used.calls, spend.budget.used.retries) == (2, 1)
    admitted = spend.routes["diagnosis"].output_limit
    assert admitted == 9_000  # the profile's larger limit is what the estimate admits
    assert requests[0]["max_tokens"] == admitted
    assert requests[1]["max_tokens"] == admitted - 50  # the remaining admitted output


def test_the_route_allowance_is_enforced_when_the_profile_sets_no_limit(monkeypatch):
    client, requests = _metered(monkeypatch, max_tokens=None, contents=['{"answer": "x"}'])
    spend = _spend(client, SpendCaps(max_calls=5, max_total_tokens=10**6, max_estimated_usd=10.0))
    with spend.collector.observing(), spend.request("diagnosis", "diagnosis", input_tokens=1_000):
        execute_structured_operation(client, purpose="diagnosis", prompt="p", result_model=Answer)
    assert requests[0]["max_tokens"] == OUTPUT_ALLOWANCE["diagnosis"]


def test_transport_retries_are_admitted_too(monkeypatch):
    install_fake_openai(monkeypatch)
    monkeypatch.setenv("TEST_KEY", "unused")
    monkeypatch.setattr("learnloop.ai.providers.openai_chat._sleep", lambda _: None)
    client = OpenAIChatProviderClient(
        "metered", AIProviderConfig(type="openai_chat", base_url="https://unused.invalid", api_key_env="TEST_KEY", model="fake")
    )
    sent = []

    def create(**kwargs):
        sent.append(kwargs)
        error = RuntimeError("transient")
        error.status_code = 503
        raise error

    client._client.chat.completions.create = create
    spend = _spend(client, SpendCaps(max_calls=1, max_retries=0, max_total_tokens=10**6, max_estimated_usd=10.0))
    with spend.collector.observing(), pytest.raises(SpendLimitExceeded):
        with spend.request("diagnosis", "diagnosis", input_tokens=1_000):
            execute_structured_operation(client, purpose="diagnosis", prompt="p", result_model=Answer)
    assert len(sent) == 1


class SubscriptionTurns:
    """A Codex-like transport whose one logical request makes several SDK turns."""

    provider_name = "codex"
    provider_type = "codex_sdk"
    model = "gpt-test"

    def __init__(self, turns: int) -> None:
        self.turns = turns
        self.sent = 0

    def supports(self, capability: str) -> bool:
        return capability == STRUCTURED_COMPLETION

    def complete(self, request: StructuredRequest[Any]) -> Any:
        for _ in range(self.turns):
            with model_call(self, purpose=f"{request.purpose}:sdk_turn", prompt=request.prompt):
                self.sent += 1
                report_call_usage({"input_tokens": 10, "output_tokens": 5})
        return request.result_model.model_validate({"answer": "x"})


def test_subscription_routes_have_no_physical_request_bound(monkeypatch):
    client = SubscriptionTurns(turns=3)
    spend = _spend(client, SpendCaps(max_calls=1, max_retries=0, max_total_tokens=0, max_estimated_usd=0.0))
    with spend.collector.observing(), spend.request("diagnosis", "diagnosis", input_tokens=1_000):
        execute_structured_operation(client, purpose="diagnosis", prompt="p", result_model=Answer)
    assert client.sent == 3
    # One logical call against the call-count cap (rule 6 keeps it); no retries.
    assert (spend.budget.used.calls, spend.budget.used.retries) == (1, 0)
    assert spend.summary()["routes"]["diagnosis"]["input_tokens"] == 30


def test_subscription_requests_still_stop_on_cancellation(monkeypatch):
    client = SubscriptionTurns(turns=3)
    stop = {"now": False}
    spend = _spend(client, SpendCaps(max_calls=5), cancelled=lambda: stop["now"])

    original = client.complete

    def complete(request):
        stop["now"] = True  # cancelled after the logical call was admitted
        return original(request)

    client.complete = complete
    with spend.collector.observing(), pytest.raises(SpendCancelled):
        with spend.request("diagnosis", "diagnosis", input_tokens=1_000):
            execute_structured_operation(client, purpose="diagnosis", prompt="p", result_model=Answer)
    assert client.sent == 1

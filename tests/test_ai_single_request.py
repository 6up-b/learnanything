from contextvars import Context

import pytest

from learnloop.ai.errors import AIInvalidOutput, CodexUnavailable
from learnloop.ai.execution import single_request, single_request_active
from learnloop.ai.providers.codex import CodexSDKProviderClient
from learnloop.ai.providers.openai_chat import OpenAIChatProviderClient
from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import StructuredRequest
from learnloop.config import AIProviderConfig
from tests.openai_fakes import FakeAPIConnectionError, install_fake_openai


class Result(WireModel):
    value: str


def _request():
    return StructuredRequest(prompt="Return a value.", result_model=Result, purpose="test")


def test_single_request_is_nested_context_local_and_restored_after_failure():
    assert not single_request_active()
    with pytest.raises(ValueError), single_request():
        assert single_request_active()
        with single_request():
            assert single_request_active()
        assert single_request_active()
        assert not Context().run(single_request_active)
        raise ValueError("failure")
    assert not single_request_active()


@pytest.mark.parametrize(
    "failure, expected",
    [
        (FakeAPIConnectionError("connection reset"), CodexUnavailable),
        ("not json", AIInvalidOutput),
        ('{"value":42}', AIInvalidOutput),
    ],
)
def test_openai_single_request_disables_retry_and_repair_only_in_scope(monkeypatch, failure, expected):
    fake = install_fake_openai(monkeypatch, failure, failure, '{"value":"ok"}')
    monkeypatch.setenv("TEST_AI_KEY", "fake")
    monkeypatch.setattr("learnloop.ai.providers.openai_chat._sleep", lambda _: None)
    client = OpenAIChatProviderClient(
        "test",
        AIProviderConfig(
            type="openai_chat", model="test", base_url="https://example.invalid",
            api_key_env="TEST_AI_KEY",
        ),
    )
    with single_request(), pytest.raises(expected):
        client.complete(_request())
    assert len(fake.instances[0].requests) == 1
    assert fake.instances[0].kwargs["max_retries"] == 0

    # Same client, outside the policy: retry/repair still consumes two attempts.
    assert client.complete(_request()).value == "ok"
    assert len(fake.instances[0].requests) == 3


@pytest.mark.parametrize(
    "failure, expected, suffix",
    [
        (CodexUnavailable("unexpected end of hex escape at line 1 column 1024"), CodexUnavailable, "json_regenerate"),
        ("not json", AIInvalidOutput, "json_repair"),
        ('{"value":42}', AIInvalidOutput, "json_repair"),
    ],
)
def test_codex_single_request_disables_regeneration_and_repair_only_in_scope(
    monkeypatch, tmp_path, failure, expected, suffix,
):
    client = CodexSDKProviderClient(
        "test", AIProviderConfig(type="codex_sdk", model="test"), tmp_path,
    )
    calls = []
    responses = iter([failure, failure, '{"value":"ok"}'])

    def run(prompt, output_schema, *, purpose):
        calls.append(purpose)
        response = next(responses)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(client, "_run_structured", run)
    with single_request(), pytest.raises(expected):
        client.complete(_request())
    assert calls == ["test"]

    assert client.complete(_request()).value == "ok"
    assert calls == ["test", "test", f"test_{suffix}"]


def test_codex_single_request_fails_closed_before_sdk_startup(monkeypatch, tmp_path):
    client = CodexSDKProviderClient(
        "test", AIProviderConfig(type="codex_sdk", model="test"), tmp_path,
    )

    def unexpected_startup(*args):
        pytest.fail("must reject unbounded app-server turns before SDK startup")

    monkeypatch.setattr("learnloop.ai.providers.codex._ensure_sdk_importable", unexpected_startup)
    with single_request(), pytest.raises(CodexUnavailable, match="single physical model request"):
        client.complete(_request())

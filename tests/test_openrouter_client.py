from __future__ import annotations

import pytest

from learnloop.ai.client import make_ai_provider_client_from_profile
from learnloop.ai.openrouter import OpenRouterProviderClient
from learnloop.codex.client import CodexUnavailable, GradingContext
from learnloop.config import AIProviderConfig

from tests.openai_fakes import grading_json, install_fake_openai


def _openrouter_profile(**overrides) -> AIProviderConfig:
    settings = {
        "type": "openrouter",
        "model": "anthropic/claude-sonnet-4.5",
        "response_format": "json_object",
    }
    settings.update(overrides)
    return AIProviderConfig(**settings)


def _grading_context() -> GradingContext:
    return GradingContext(
        attempt_id="attempt_1",
        practice_item_id="pi_1",
        prompt="Define SVD.",
        expected_answer="U Sigma V^T.",
        learner_answer_md="U Sigma V transpose.",
        rubric={},
    )


def test_openrouter_defaults_base_url_key_env_and_title_header(monkeypatch):
    fake_openai = install_fake_openai(monkeypatch, grading_json())
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-secret")
    client = OpenRouterProviderClient("openrouter", _openrouter_profile())

    proposal = client.run_grading_proposal(_grading_context())

    assert proposal.rubric_score == 4
    kwargs = fake_openai.instances[0].kwargs
    assert kwargs["api_key"] == "or-secret"
    assert kwargs["base_url"] == "https://openrouter.ai/api/v1"
    assert kwargs["default_headers"] == {"X-Title": "LearnLoop"}
    request = fake_openai.instances[0].requests[0]
    assert request["model"] == "anthropic/claude-sonnet-4.5"
    assert request["response_format"] == {"type": "json_object"}


def test_openrouter_profile_base_url_overrides_default(monkeypatch):
    fake_openai = install_fake_openai(monkeypatch, grading_json())
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-secret")
    client = OpenRouterProviderClient("openrouter", _openrouter_profile(base_url="https://proxy.example/v1"))

    client.run_grading_proposal(_grading_context())

    assert fake_openai.instances[0].kwargs["base_url"] == "https://proxy.example/v1"


def test_openrouter_attribution_headers_configurable(monkeypatch):
    fake_openai = install_fake_openai(monkeypatch, grading_json())
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-secret")
    client = OpenRouterProviderClient(
        "openrouter",
        _openrouter_profile(http_referer="https://example.com/app", x_title="My App"),
    )

    client.run_grading_proposal(_grading_context())

    assert fake_openai.instances[0].kwargs["default_headers"] == {
        "X-Title": "My App",
        "HTTP-Referer": "https://example.com/app",
    }


def test_openrouter_reasoning_effort_maps_to_unified_body(monkeypatch):
    fake_openai = install_fake_openai(monkeypatch, grading_json())
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-secret")
    client = OpenRouterProviderClient("openrouter", _openrouter_profile(reasoning_effort="high"))

    client.run_grading_proposal(_grading_context())

    request = fake_openai.instances[0].requests[0]
    assert request["extra_body"] == {"reasoning": {"effort": "high"}}
    assert "reasoning_effort" not in request


def test_openrouter_thinking_disabled_sends_no_reasoning(monkeypatch):
    fake_openai = install_fake_openai(monkeypatch, grading_json())
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-secret")
    client = OpenRouterProviderClient(
        "openrouter",
        _openrouter_profile(thinking="disabled", reasoning_effort="high"),
    )

    client.run_grading_proposal(_grading_context())

    request = fake_openai.instances[0].requests[0]
    assert "extra_body" not in request
    assert "reasoning_effort" not in request


def test_openrouter_missing_key_raises(monkeypatch):
    install_fake_openai(monkeypatch, grading_json())
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(CodexUnavailable, match="OPENROUTER_API_KEY"):
        OpenRouterProviderClient("openrouter", _openrouter_profile())


def test_make_ai_provider_client_dispatches_openrouter(tmp_path, monkeypatch):
    install_fake_openai(monkeypatch, grading_json())
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-secret")

    client = make_ai_provider_client_from_profile("openrouter", _openrouter_profile(), tmp_path)

    assert isinstance(client, OpenRouterProviderClient)
    assert client.provider_type == "openrouter"
    assert client.model == "anthropic/claude-sonnet-4.5"

from __future__ import annotations

import json
import sys
import types

import pytest

import learnloop.ai.openai_chat as openai_chat
from learnloop.ai.client import make_ai_provider_client_from_profile
from learnloop.ai.openrouter import OpenRouterProviderClient
from learnloop.codex.client import CodexUnavailable, ExerciseAuthoringContext, GradingContext
from learnloop.config import AIProviderConfig
from learnloop.services.ingest_runner import (
    default_exercise_import_client,
    default_inventory_client,
)
from learnloop.vault.loader import init_vault


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


def _grading_json() -> str:
    return json.dumps(
        {
            "attempt_id": "attempt_1",
            "practice_item_id": "pi_1",
            "rubric_score": 4,
            "criterion_evidence": [],
            "fatal_errors": [],
            "error_attributions": [],
            "grader_confidence": 0.95,
            "manual_review_recommended": False,
            "repair_suggestions": [],
        }
    )


def _install_fake_openai(monkeypatch, *responses: str | Exception):
    module = types.SimpleNamespace(instances=[])

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.requests = []
            self._responses = list(responses)
            self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self._create))
            module.instances.append(self)

        def _create(self, **kwargs):
            self.requests.append(kwargs)
            content = self._responses.pop(0)
            if isinstance(content, Exception):
                raise content
            message = types.SimpleNamespace(content=content)
            choice = types.SimpleNamespace(message=message)
            return types.SimpleNamespace(choices=[choice])

    module.OpenAI = FakeOpenAI
    monkeypatch.setitem(sys.modules, "openai", module)
    return module


def test_openrouter_defaults_endpoint_key_and_title(monkeypatch):
    fake_openai = _install_fake_openai(monkeypatch, _grading_json())
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-secret")
    client = OpenRouterProviderClient("openrouter", _openrouter_profile())

    proposal = client.run_grading_proposal(_grading_context())

    assert proposal.rubric_score == 4
    kwargs = fake_openai.instances[0].kwargs
    assert kwargs["api_key"] == "or-secret"
    assert kwargs["base_url"] == "https://openrouter.ai/api/v1"
    assert kwargs["default_headers"] == {"X-Title": "LearnLoop"}
    assert fake_openai.instances[0].requests[0]["response_format"] == {
        "type": "json_object"
    }


def test_openrouter_supports_exercise_authoring(monkeypatch):
    response = json.dumps(
        {
            "items": [
                {
                    "statement_md": "Compute the SVD of A.",
                    "expected_answer_md": "A = U Sigma V^T.",
                }
            ],
            "warnings": [],
        }
    )
    fake_openai = _install_fake_openai(monkeypatch, response)
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-secret")
    client = OpenRouterProviderClient("openrouter", _openrouter_profile())

    authored = client.run_exercise_authoring(
        ExerciseAuthoringContext(
            extraction_id="ext_1",
            exercise_text="Compute the SVD of A.",
        )
    )

    assert authored.items[0].statement_md == "Compute the SVD of A."
    request = fake_openai.instances[0].requests[0]
    assert "learnloop exercise import" in request["messages"][1]["content"]


def test_openrouter_routes_inventory_and_exercise_authoring(tmp_path, monkeypatch):
    vault_root = init_vault(tmp_path / "vault")
    config_path = vault_root / "learnloop.toml"
    text = config_path.read_text(encoding="utf-8")
    text = text.replace(
        'canonical_ingest = "codex_medium"',
        'canonical_ingest = "openrouter"',
    )
    text = text.replace('authoring = "codex_medium"', 'authoring = "openrouter"')
    config_path.write_text(text, encoding="utf-8")
    _install_fake_openai(monkeypatch)
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-secret")
    context = types.SimpleNamespace(vault_root=vault_root)

    inventory_client = default_inventory_client(context)
    exercise_client = default_exercise_import_client(context)

    assert inventory_client.provider_type == "openrouter"
    assert exercise_client.provider_type == "openrouter"


def test_openrouter_profile_overrides_and_reasoning(monkeypatch):
    fake_openai = _install_fake_openai(monkeypatch, _grading_json())
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-secret")
    client = OpenRouterProviderClient(
        "openrouter",
        _openrouter_profile(
            base_url="https://proxy.example/v1",
            http_referer="https://example.com/app",
            x_title="My App",
            reasoning_effort="high",
        ),
    )

    client.run_grading_proposal(_grading_context())

    kwargs = fake_openai.instances[0].kwargs
    assert kwargs["base_url"] == "https://proxy.example/v1"
    assert kwargs["default_headers"] == {
        "X-Title": "My App",
        "HTTP-Referer": "https://example.com/app",
    }
    request = fake_openai.instances[0].requests[0]
    assert request["extra_body"] == {"reasoning": {"effort": "high"}}
    assert "reasoning_effort" not in request


def test_openrouter_json_schema_response_format(monkeypatch):
    fake_openai = _install_fake_openai(monkeypatch, _grading_json())
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-secret")
    client = OpenRouterProviderClient(
        "openrouter",
        _openrouter_profile(response_format="json_schema"),
    )

    client.run_grading_proposal(_grading_context())

    response_format = fake_openai.instances[0].requests[0]["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["name"] == "GradingProposal"
    assert response_format["json_schema"]["strict"] is True


def test_openrouter_retries_rate_limits(monkeypatch):
    class RateLimited(Exception):
        status_code = 429

    fake_openai = _install_fake_openai(monkeypatch, RateLimited("slow down"), _grading_json())
    monkeypatch.setattr(openai_chat, "_sleep", lambda _seconds: None)
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-secret")
    client = OpenRouterProviderClient("openrouter", _openrouter_profile())

    proposal = client.run_grading_proposal(_grading_context())

    assert proposal.rubric_score == 4
    assert len(fake_openai.instances[0].requests) == 2


def test_openrouter_thinking_disabled_sends_no_reasoning(monkeypatch):
    fake_openai = _install_fake_openai(monkeypatch, _grading_json())
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
    _install_fake_openai(monkeypatch, _grading_json())
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(CodexUnavailable, match="OPENROUTER_API_KEY"):
        OpenRouterProviderClient("openrouter", _openrouter_profile())


def test_make_ai_provider_client_dispatches_openrouter(tmp_path, monkeypatch):
    _install_fake_openai(monkeypatch, _grading_json())
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-secret")

    client = make_ai_provider_client_from_profile("openrouter", _openrouter_profile(), tmp_path)

    assert isinstance(client, OpenRouterProviderClient)
    assert client.provider_type == "openrouter"

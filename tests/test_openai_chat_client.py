from __future__ import annotations

import json
import sys
import types

from learnloop.ai.openai_chat import OpenAIChatProviderClient
from learnloop.codex.client import GradingContext
from learnloop.config import AIProviderConfig


def test_openai_chat_client_sends_deepseek_json_request(monkeypatch):
    fake_openai = _install_fake_openai(monkeypatch, _grading_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    client = OpenAIChatProviderClient(
        "deepseek_flash",
        AIProviderConfig(
            type="openai_chat",
            base_url="https://api.deepseek.com",
            api_key_env="DEEPSEEK_API_KEY",
            model="deepseek-v4-flash",
            response_format="json_object",
            thinking="disabled",
            max_tokens=8192,
            timeout_seconds=90,
        ),
    )

    proposal = client.run_grading_proposal(
        GradingContext(
            attempt_id="attempt_1",
            practice_item_id="pi_1",
            prompt="Define SVD.",
            expected_answer="U Sigma V^T.",
            learner_answer_md="U Sigma V transpose.",
            rubric={"max_points": 4, "criteria": [{"id": "correctness", "points": 4}]},
        )
    )

    assert proposal.rubric_score == 4
    assert fake_openai.instances[0].kwargs["api_key"] == "secret"
    assert fake_openai.instances[0].kwargs["base_url"] == "https://api.deepseek.com"
    request = fake_openai.instances[0].requests[0]
    assert request["model"] == "deepseek-v4-flash"
    assert request["response_format"] == {"type": "json_object"}
    assert request["extra_body"] == {"thinking": {"type": "disabled"}}
    assert request["max_tokens"] == 8192
    assert "JSON" in request["messages"][0]["content"]


def test_openai_chat_client_repairs_invalid_json_once(monkeypatch):
    fake_openai = _install_fake_openai(monkeypatch, "not json", _grading_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    client = OpenAIChatProviderClient(
        "deepseek_flash",
        AIProviderConfig(
            type="openai_chat",
            base_url="https://api.deepseek.com",
            api_key_env="DEEPSEEK_API_KEY",
            model="deepseek-v4-flash",
            response_format="json_object",
        ),
    )

    proposal = client.run_grading_proposal(
        GradingContext(
            attempt_id="attempt_1",
            practice_item_id="pi_1",
            prompt="Prompt",
            expected_answer="Expected",
            learner_answer_md="Answer",
            rubric={},
        )
    )

    assert proposal.rubric_score == 4
    assert len(fake_openai.instances[0].requests) == 2
    assert "Repair the following model output" in fake_openai.instances[0].requests[1]["messages"][1]["content"]


def _grading_json() -> str:
    return json.dumps(
        {
            "attempt_id": "attempt_1",
            "practice_item_id": "pi_1",
            "rubric_score": 4,
            "criterion_evidence": [{"criterion_id": "correctness", "points_awarded": 4, "evidence": "Correct."}],
            "fatal_errors": [],
            "error_attributions": [],
            "grader_confidence": 0.95,
            "manual_review_recommended": False,
            "feedback_md": None,
            "repair_suggestions": [],
        }
    )


def _install_fake_openai(monkeypatch, *responses: str):
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
            message = types.SimpleNamespace(content=content)
            choice = types.SimpleNamespace(message=message)
            return types.SimpleNamespace(choices=[choice])

    module.OpenAI = FakeOpenAI
    monkeypatch.setitem(sys.modules, "openai", module)
    return module

"""Shared fake ``openai`` module for offline chat-provider tests.

``install_fake_openai`` injects a stand-in for the ``openai`` package into
``sys.modules`` (the real client imports it lazily inside ``__init__``). Each
``FakeOpenAI`` instance records its constructor kwargs and every
``chat.completions.create(**kwargs)`` request, replaying the queued responses
in order. A queued response may be an ``Exception`` instance, which is raised
instead of returned — used to exercise the retry path.
"""

from __future__ import annotations

import json
import sys
import types


def install_fake_openai(monkeypatch, *responses: str | Exception):
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


def grading_json() -> str:
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

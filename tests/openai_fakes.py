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


def install_fake_openai(monkeypatch, *responses: str | Exception, transcriptions=()):
    module = types.SimpleNamespace(instances=[])

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.requests = []
            self.transcription_requests = []
            self._responses = list(responses)
            self._transcriptions = list(transcriptions)
            self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self._create))
            self.audio = types.SimpleNamespace(transcriptions=types.SimpleNamespace(create=self._transcribe))
            module.instances.append(self)

        def _create(self, **kwargs):
            self.requests.append(kwargs)
            content = self._responses.pop(0)
            if isinstance(content, Exception):
                raise content
            message = types.SimpleNamespace(content=content)
            choice = types.SimpleNamespace(message=message)
            return types.SimpleNamespace(choices=[choice])

        def _transcribe(self, **kwargs):
            self.transcription_requests.append(kwargs)
            result = self._transcriptions.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

    module.OpenAI = FakeOpenAI
    monkeypatch.setitem(sys.modules, "openai", module)
    return module


def fake_verbose_transcription(*segments, language="en", duration=None, text=None):
    """A verbose_json-shaped transcription response. ``segments`` are
    (start, end, text) tuples; pass dicts instead to mimic Groq's dict-shaped
    segments."""

    built = [
        segment
        if isinstance(segment, dict)
        else types.SimpleNamespace(start=segment[0], end=segment[1], text=segment[2])
        for segment in segments
    ]
    if duration is None and built:
        last = built[-1]
        duration = last["end"] if isinstance(last, dict) else last.end
    return types.SimpleNamespace(
        segments=built,
        language=language,
        duration=duration,
        text=text if text is not None else " ".join(
            (s["text"] if isinstance(s, dict) else s.text) for s in built
        ),
    )


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

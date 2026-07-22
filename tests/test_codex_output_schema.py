from __future__ import annotations

import logging
import sys
from enum import Enum
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError

from learnloop.codex.client import AuthoringContext, SdkCodexClient, _codex_output_schema
from learnloop.codex.schemas import AuthoringProposal, GradingProposal, PracticeItemPatchPayload
from learnloop.config import CodexConfig


def test_codex_authoring_schema_is_strict_response_format_compatible():
    schema = _codex_output_schema(AuthoringProposal)

    assert schema["additionalProperties"] is False
    assert "default" not in _schema_keys(schema)
    assert "title" not in _schema_keys(schema)
    assert "minimum" not in _schema_keys(schema)
    assert "maximum" not in _schema_keys(schema)
    assert "title" in schema["$defs"]["LearningObjectPatchPayload"]["properties"]
    assert not _non_strict_objects(schema)


def test_codex_grading_schema_is_strict_response_format_compatible():
    schema = _codex_output_schema(GradingProposal)

    assert schema["additionalProperties"] is False
    assert "default" not in _schema_keys(schema)
    assert not _non_strict_objects(schema)


def test_sdk_authoring_path_passes_strict_schema_to_codex(tmp_path):
    checkout = tmp_path / "codex"
    client = SdkCodexClient(CodexConfig(checkout_path=str(checkout)), tmp_path)
    captured: dict[str, Any] = {}

    def fake_run_structured(prompt: str, output_schema: dict[str, Any], *, purpose: str) -> str:
        captured["prompt"] = prompt
        captured["output_schema"] = output_schema
        captured["purpose"] = purpose
        return '{"summary": "ok"}'

    client._run_structured = fake_run_structured  # type: ignore[method-assign]

    proposal = client.run_authoring_proposal(AuthoringContext(vault_root=str(tmp_path), source_ids=[]))

    assert proposal.summary == "ok"
    assert captured["purpose"] == "authoring"
    assert "retrieval_demand" in captured["prompt"]
    assert "repair_targets" in captured["prompt"]
    assert not _non_strict_objects(captured["output_schema"])


def test_sdk_codex_client_logs_full_prompt_and_response(tmp_path, monkeypatch, caplog):
    captured: dict[str, Any] = {}

    class FakeCodex:
        def __init__(self, config):
            captured["app_config"] = config

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def thread_start(self, **kwargs):
            captured["thread_start"] = kwargs
            return FakeThread()

    class FakeThread:
        def run(self, prompt: str, **kwargs):
            captured["run"] = {"prompt": prompt, **kwargs}
            return SimpleNamespace(final_response='{"summary": "ok"}')

    class SdkAppConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class ReasoningEffort(Enum):
        low = "low"
        medium = "medium"

    class ReasoningSummary:
        @classmethod
        def model_validate(cls, value):
            return value

    openai_codex = ModuleType("openai_codex")
    openai_codex.Codex = FakeCodex
    openai_codex.CodexConfig = SdkAppConfig
    openai_codex_types = ModuleType("openai_codex.types")
    openai_codex_types.Personality = SimpleNamespace(pragmatic="pragmatic")
    openai_codex_types.ReasoningEffort = ReasoningEffort
    openai_codex_types.ReasoningSummary = ReasoningSummary
    monkeypatch.setitem(sys.modules, "openai_codex", openai_codex)
    monkeypatch.setitem(sys.modules, "openai_codex.types", openai_codex_types)
    caplog.set_level(logging.DEBUG, logger="learnloop.codex.client")

    client = SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex")), tmp_path)
    response = client._run_structured("full prompt body", {"type": "object"}, purpose="grading")

    assert response == '{"summary": "ok"}'
    assert captured["run"]["prompt"] == "full prompt body"
    prompt_log = _logged_event(caplog.records, "codex.prompt")
    response_log = _logged_event(caplog.records, "codex.response")
    assert prompt_log["purpose"] == "grading"
    assert prompt_log["prompt"] == "full prompt body"
    assert prompt_log["output_schema"] == {"type": "object"}
    assert response_log["response"] == '{"summary": "ok"}'


def test_authoring_payload_rejects_unknown_attempt_type():
    with pytest.raises(ValidationError):
        PracticeItemPatchPayload.model_validate(
            {
                "learning_object_id": "lo_svd",
                "practice_mode": "constructed_response",
                "attempt_types_allowed": ["freeform_answer"],
                "prompt": "Explain SVD.",
                "expected_answer": "U Sigma V transpose.",
            }
        )


def _schema_keys(value: Any) -> set[str]:
    if isinstance(value, list):
        return {key for item in value for key in _schema_keys(item)}
    if not isinstance(value, dict):
        return set()
    keys = set(value)
    for key, child in value.items():
        if key in {"$defs", "properties"} and isinstance(child, dict):
            for schema in child.values():
                keys.update(_schema_keys(schema))
            continue
        keys.update(_schema_keys(child))
    return keys


def _non_strict_objects(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for child in value for item in _non_strict_objects(child)]
    if not isinstance(value, dict):
        return []

    failures: list[dict[str, Any]] = []
    if value.get("type") == "object" or "properties" in value:
        properties = value.get("properties", {})
        if value.get("additionalProperties") is not False:
            failures.append(value)
        if set(value.get("required", [])) != set(properties):
            failures.append(value)
    for child in value.values():
        failures.extend(_non_strict_objects(child))
    return failures


def _logged_event(records, event: str) -> dict:
    for record in records:
        if record.getMessage() == event:
            fields = getattr(record, "event_fields", None)
            if isinstance(fields, dict):
                return fields
    raise AssertionError(f"missing log event {event}")

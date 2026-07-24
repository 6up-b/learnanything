from __future__ import annotations

import json
import logging
import sys
import threading
import time
from enum import Enum
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError

from learnloop.codex.client import (
    AuthoringContext,
    CodexUnavailable,
    CodexTurnTimeout,
    ReaderPresetSynthesisContext,
    SdkCodexClient,
    TeachBackAuthoringContext,
    _codex_output_schema,
    _resolved_sdk_codex_bin,
)
from learnloop.codex.schemas import (
    AuthoringProposal,
    GradingProposal,
    PracticeItemPatchPayload,
    ReaderPresetSynthesis,
    TeachBackAuthoring,
)
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


def test_codex_teach_back_authoring_schema_is_strict_response_format_compatible():
    schema = _codex_output_schema(TeachBackAuthoring)

    assert schema["additionalProperties"] is False
    assert "default" not in _schema_keys(schema)
    assert not _non_strict_objects(schema)


def test_sdk_teach_back_authoring_passes_source_and_quest_to_prompt(tmp_path):
    client = SdkCodexClient(
        CodexConfig(checkout_path=str(tmp_path / "codex")),
        tmp_path,
    )
    captured: dict[str, Any] = {}

    def fake_run_structured(prompt: str, output_schema: dict[str, Any], *, purpose: str) -> str:
        captured.update(prompt=prompt, output_schema=output_schema, purpose=purpose)
        return json.dumps(
            {
                "prompt_md": "Teach how to find both square roots of i.",
                "expected_answer_md": "Explain the Cartesian method.",
                "core_criteria": [
                    {
                        "description": "Explains the Cartesian method.",
                        "source_criterion_ids": ["solve"],
                        "measurement_status": "item_local",
                        "facet_ids": [],
                    }
                ],
                "transfer_criterion": {
                    "description": "Uses the reasoning in signal processing.",
                    "source_criterion_ids": ["solve"],
                    "measurement_status": "supporting",
                    "facet_ids": ["complex_multiplication"],
                },
                "transfer_scenario": "Interpret a phase rotation in signal processing.",
                "quest_connection": "connected",
                "trace_contract": None,
            }
        )

    client._run_structured = fake_run_structured  # type: ignore[method-assign]
    context = TeachBackAuthoringContext(
        source_practice_item_id="pi_roots",
        source_prompt="Find two distinct square roots of i.",
        source_expected_answer="±(1+i)/sqrt(2)",
        source_criteria=[{"id": "solve", "description": "Solves both sign branches."}],
        allowed_facets=[{"id": "complex_multiplication"}],
        learning_object_title="Compute with Complex Numbers",
        quest_sentence="I want to learn complex numbers for signal processing.",
    )

    result = client.run_teach_back_authoring(context)

    assert result.quest_connection == "connected"
    assert captured["purpose"] == "teach_back_authoring"
    payload = json.loads(captured["prompt"].rsplit("\n\n", 1)[1])
    assert payload["context"]["source_prompt"] == context.source_prompt
    assert payload["context"]["quest_sentence"] == context.quest_sentence
    assert "quest may shape ONLY this transfer criterion" in payload["task"]
    assert not _non_strict_objects(captured["output_schema"])


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


def test_sdk_reader_preset_repairs_invalid_unicode_json_once(tmp_path):
    client = SdkCodexClient(
        CodexConfig(checkout_path=str(tmp_path / "codex")),
        tmp_path,
    )
    calls: list[dict[str, Any]] = []
    malformed = (
        '{"content_md":"'
        + ("x" * 990)
        + '\\ud800","span_ids":["s1"]}'
    )
    responses = iter(
        [
            malformed,
            '{"content_md":"Use coordinatewise distributivity.","span_ids":["s1"]}',
        ]
    )

    def fake_run_structured(prompt: str, output_schema: dict[str, Any], *, purpose: str) -> str:
        calls.append({"prompt": prompt, "output_schema": output_schema, "purpose": purpose})
        return next(responses)

    client._run_structured = fake_run_structured  # type: ignore[method-assign]
    selected = r"Show that $(a+b)x = ax + bx$ for all $a,b \in F$ and all $x \in F^n$"

    result = client.run_reader_preset_synthesis(
        ReaderPresetSynthesisContext(
            preset="worked_example",
            selected_text=selected,
            selection_edited=True,
            blocks=[{"span_id": "s1", "text": selected}],
        )
    )

    assert result == ReaderPresetSynthesis(
        content_md="Use coordinatewise distributivity.", span_ids=["s1"]
    )
    assert [call["purpose"] for call in calls] == [
        "reader_preset_synthesis",
        "reader_preset_synthesis_json_repair",
    ]
    payload = json.loads(calls[0]["prompt"].rsplit("\n\n", 1)[1])
    assert payload["context"]["selected_text"] == selected
    assert "escape backslashes" in calls[1]["prompt"]


def test_sdk_reader_preset_regenerates_when_app_server_rejects_hex_escape(tmp_path):
    client = SdkCodexClient(
        CodexConfig(checkout_path=str(tmp_path / "codex")),
        tmp_path,
    )
    calls: list[dict[str, Any]] = []
    responses: list[str | BaseException] = [
        CodexUnavailable("unexpected end of hex escape at line 1 column 1024"),
        '{"content_md":"Apply distributivity coordinatewise.","span_ids":["s1"]}',
    ]

    def fake_run_structured(prompt: str, output_schema: dict[str, Any], *, purpose: str) -> str:
        calls.append({"prompt": prompt, "output_schema": output_schema, "purpose": purpose})
        response = responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response

    client._run_structured = fake_run_structured  # type: ignore[method-assign]
    selected = r"Show that $(a+b)x = ax + bx$ for all $a,b \in F$ and all $x \in F^n$"

    result = client.run_reader_preset_synthesis(
        ReaderPresetSynthesisContext(
            preset="worked_example",
            selected_text=selected,
            selection_edited=True,
            blocks=[{"span_id": "s1", "text": selected}],
        )
    )

    assert result.content_md == "Apply distributivity coordinatewise."
    assert [call["purpose"] for call in calls] == [
        "reader_preset_synthesis",
        "reader_preset_synthesis_json_regenerate",
    ]
    assert r"emit `\\in`" in calls[1]["prompt"]


def test_sdk_runtime_prefers_bundle_and_falls_back_for_source_checkout(
    monkeypatch,
):
    bundled = ModuleType("codex_cli_bin")
    bundled.bundled_codex_path = lambda: "/pinned/codex"  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "codex_cli_bin", bundled)
    assert _resolved_sdk_codex_bin("") is None

    bundled.bundled_codex_path = lambda: (_ for _ in ()).throw(  # type: ignore[attr-defined]
        FileNotFoundError("package metadata absent")
    )
    monkeypatch.setattr("learnloop.codex.client.shutil.which", lambda _name: "/usr/bin/codex")
    assert _resolved_sdk_codex_bin("") == "/usr/bin/codex"
    assert _resolved_sdk_codex_bin("/configured/codex") == "/configured/codex"


def test_sdk_codex_client_logs_full_prompt_and_response(tmp_path, monkeypatch, caplog):
    captured: dict[str, Any] = {}

    class FakeCodex:
        def __init__(self, config):
            captured["app_config"] = config

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def close(self):
            return None

        def thread_start(self, **kwargs):
            captured["thread_start"] = kwargs
            return FakeThread()

    class FakeThread:
        def turn(self, prompt: str, **kwargs):
            captured["run"] = {"prompt": prompt, **kwargs}
            return FakeTurn()

    class FakeTurn:
        def run(self):
            return SimpleNamespace(final_response='{"summary": "ok"}')

        def interrupt(self):
            return None

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


def test_sdk_codex_turn_timeout_interrupts_and_returns(tmp_path, monkeypatch):
    interrupted = threading.Event()

    class FakeCodex:
        def __init__(self, config):
            self.config = config

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.close()

        def close(self):
            interrupted.set()

        def thread_start(self, **_kwargs):
            return FakeThread()

    class FakeThread:
        def turn(self, _prompt: str, **_kwargs):
            return FakeTurn()

    class FakeTurn:
        def run(self):
            interrupted.wait(timeout=2)
            raise RuntimeError("turn stopped")

        def interrupt(self):
            # Simulate an app-server that never answers turn/interrupt. The
            # client's force-close fallback must still release turn.run().
            threading.Event().wait(timeout=2)

    class SdkAppConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class ReasoningEffort(Enum):
        low = "low"

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

    client = SdkCodexClient(
        CodexConfig(checkout_path=str(tmp_path / "codex"), timeout_seconds=0.05),
        tmp_path,
    )
    started = time.monotonic()

    with pytest.raises(CodexTurnTimeout, match="0.05-second deadline"):
        client._run_structured("prompt", {"type": "object"}, purpose="authoring")

    assert interrupted.is_set()
    assert time.monotonic() - started < 1


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

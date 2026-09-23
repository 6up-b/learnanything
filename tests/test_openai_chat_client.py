from __future__ import annotations

import types

import pytest

import learnloop.ai.providers.openai_chat as openai_chat_module
from learnloop.ai.providers.openai_chat import OpenAIChatProviderClient
from learnloop.attempts.ai_contracts import GradingContext
from learnloop.content.authoring.ai_contracts import (
    ConceptAnimationContext,
    ManimAnimation,
    concept_animation_prompt,
)
from learnloop.content.synthesis.ai_contracts import (
    AppendReconciliationContext,
    AppendReconciliation,
    append_reconciliation_prompt,
    ConceptGraphContext,
    ConceptGraphStructuring,
    concept_graph_structuring_prompt,
    SourceSetSynthesis,
    SourceSetSynthesisContext,
    source_set_synthesis_prompt,
    SourceUnitInventory,
    SourceUnitInventoryContext,
    source_unit_inventory_prompt,
)
from learnloop.curriculum.ai_contracts import (
    DepthEdgeInstanceContext,
    DepthEdgeInstanceBatch,
    depth_edge_instance_prompt,
    RungBackfillClassification,
    RungBackfillContext,
    rung_backfill_prompt,
)
from learnloop.diagnosis.ai_contracts import (
    DiagnosticTrials,
    diagnostic_trials_prompt,
    MisconceptionMatch,
    misconception_match_prompt,
    ProbeDialogueTurnContext,
    ProbeDialogueTurn,
    probe_dialogue_turn_prompt,
    ProbeFamilyTrialsContext,
    ProbeFamilyTrials,
    probe_family_trials_prompt,
    ProbeInstanceContext,
    ProbeInstanceSurfaces,
    probe_instance_surfaces_prompt,
)
from learnloop.reader.ai_contracts import (
    ReaderPresetSynthesisContext,
    ReaderPresetSynthesis,
    reader_preset_synthesis_prompt,
    ReadingQuickCheckContext,
    ReadingQuickCheck,
    reading_quick_check_prompt,
)
from learnloop.tutor.ai_contracts import (
    PromotionAnalysis,
    PromotionAnalysisContext,
    promotion_analysis_prompt,
)
from learnloop.ai.errors import CodexUnavailable
from learnloop.ai.providers.codex import SdkCodexClient
from learnloop.ai.transport import STRUCTURED_COMPLETION, StructuredRequest
from learnloop.attempts.grading import request_grading_proposal
from learnloop.config import AIProviderConfig

from tests.openai_fakes import FakeAPIConnectionError, grading_json, install_fake_openai


def _deepseek_profile(**overrides) -> AIProviderConfig:
    settings = {
        "type": "openai_chat",
        "base_url": "https://api.deepseek.com",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model": "deepseek-v4-flash",
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
        rubric={"max_points": 4, "criteria": [{"id": "correctness", "points": 4}]},
    )


def test_openai_chat_client_sends_deepseek_json_request(monkeypatch):
    fake_openai = install_fake_openai(monkeypatch, grading_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    client = OpenAIChatProviderClient(
        "deepseek_flash",
        _deepseek_profile(thinking="disabled", max_tokens=8192, timeout_seconds=90),
    )

    proposal = request_grading_proposal(client, _grading_context())

    assert proposal.rubric_score == 4
    assert fake_openai.instances[0].kwargs["api_key"] == "secret"
    assert fake_openai.instances[0].kwargs["base_url"] == "https://api.deepseek.com"
    assert "default_headers" not in fake_openai.instances[0].kwargs
    request = fake_openai.instances[0].requests[0]
    assert request["model"] == "deepseek-v4-flash"
    assert request["response_format"] == {"type": "json_object"}
    assert request["extra_body"] == {"thinking": {"type": "disabled"}}
    assert request["max_tokens"] == 8192
    assert "JSON" in request["messages"][0]["content"]


def test_openai_chat_client_repairs_invalid_json_once(monkeypatch):
    fake_openai = install_fake_openai(monkeypatch, "not json", grading_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile())

    proposal = request_grading_proposal(client, _grading_context())

    assert proposal.rubric_score == 4
    assert len(fake_openai.instances[0].requests) == 2
    assert "Repair the following model output" in fake_openai.instances[0].requests[1]["messages"][1]["content"]


def test_structured_providers_share_one_transport_surface():
    sdk_methods = {name for name in dir(SdkCodexClient) if name.startswith("run_")}
    chat_methods = {name for name in dir(OpenAIChatProviderClient) if name.startswith("run_")}

    assert sdk_methods == set()
    assert chat_methods == {"run_media_markdown", "run_media_transcription"}
    assert {"complete", "supports", "consume_usage"} <= set(dir(SdkCodexClient))
    assert {"complete", "supports", "consume_usage"} <= set(dir(OpenAIChatProviderClient))


EXTENDED_METHOD_CASES = [
    (
        "misconception_match",
        types.SimpleNamespace(statement="Belief.", learning_object_id="lo_1", candidates=[]),
        MisconceptionMatch(decision="new"),
        "learnloop misconception match",
    ),
    (
        "promotion_analysis",
        PromotionAnalysisContext(intent="practice"),
        PromotionAnalysis(),
        "learnloop promotion analysis",
    ),
    (
        "diagnostic_trials",
        {"n_trials": 2, "item_prompt": "Prompt", "misconception_statement": "Belief."},
        DiagnosticTrials(),
        "learnloop diagnostic trials",
    ),
    (
        "probe_instance_surfaces",
        ProbeInstanceContext(
            family_template_id="fam_1",
            family_template_version=1,
            instrument_kind="worked_example",
            measurement_intent="Measure X.",
            learning_object_id="lo_1",
            learning_object_title="Title",
            learning_object_concept="Concept",
            learning_object_summary="Summary",
        ),
        ProbeInstanceSurfaces(),
        "learnloop probe instance surfaces",
    ),
    (
        "probe_dialogue_turn",
        ProbeDialogueTurnContext(
            turn_kind="commit",
            turn_number=1,
            planned_turns=3,
            learning_object_id="lo_1",
            learning_object_title="Title",
            learning_object_concept="Concept",
            learning_object_summary="Summary",
        ),
        ProbeDialogueTurn(prompt_md="Prompt?", expected_answer_md="Answer."),
        "learnloop probe dialogue turn",
    ),
    (
        "probe_family_trials",
        ProbeFamilyTrialsContext(
            family_template_id="fam_1",
            family_template_version=1,
            instrument_kind="worked_example",
            measurement_intent="Measure X.",
            learning_object_title="Title",
            learning_object_summary="Summary",
        ),
        ProbeFamilyTrials(),
        "learnloop probe family trials",
    ),
    (
        "source_unit_inventory",
        SourceUnitInventoryContext(
            unit_id="unit_1",
            semantic_hash="hash",
            role="reference",
            inventory_profile="semantic",
        ),
        SourceUnitInventory(),
        "learnloop source unit inventory",
    ),
    (
        "source_set_synthesis",
        SourceSetSynthesisContext(source_set_id="set_1", subject_id="subj_1", mode="bootstrap"),
        SourceSetSynthesis(),
        "learnloop source set synthesis",
    ),
    (
        "append_reconciliation",
        AppendReconciliationContext(source_set_id="set_1", subject_id="subj_1", change_kind="source_added"),
        AppendReconciliation(),
        "learnloop append reconciliation",
    ),
    (
        "reader_preset_synthesis",
        ReaderPresetSynthesisContext(preset="explain"),
        ReaderPresetSynthesis(),
        "learnloop reader preset synthesis",
    ),
    (
        "reading_quick_check",
        ReadingQuickCheckContext(extraction_id="ex_1"),
        ReadingQuickCheck(),
        "learnloop reading quick check",
    ),
    (
        "rung_backfill",
        RungBackfillContext(),
        RungBackfillClassification(),
        "learnloop rung backfill",
    ),
    (
        "depth_edge_instances",
        DepthEdgeInstanceContext(commitment_id="commit_1"),
        DepthEdgeInstanceBatch(),
        "learnloop depth edge instances",
    ),
    (
        "concept_graph_structuring",
        ConceptGraphContext(source_set_id="set_1", subject_id="subj_1"),
        ConceptGraphStructuring(),
        "learnloop concept graph structuring",
    ),
    (
        "concept_animation",
        ConceptAnimationContext(concept_id="singular_value_decomposition", concept_title="SVD"),
        ManimAnimation(),
        "learnloop concept animation",
    ),
]

_PROMPT_BUILDERS = {
    "misconception_match": misconception_match_prompt,
    "promotion_analysis": promotion_analysis_prompt,
    "diagnostic_trials": diagnostic_trials_prompt,
    "probe_instance_surfaces": probe_instance_surfaces_prompt,
    "probe_dialogue_turn": probe_dialogue_turn_prompt,
    "probe_family_trials": probe_family_trials_prompt,
    "source_unit_inventory": source_unit_inventory_prompt,
    "source_set_synthesis": source_set_synthesis_prompt,
    "append_reconciliation": append_reconciliation_prompt,
    "reader_preset_synthesis": reader_preset_synthesis_prompt,
    "reading_quick_check": reading_quick_check_prompt,
    "rung_backfill": rung_backfill_prompt,
    "depth_edge_instances": depth_edge_instance_prompt,
    "concept_graph_structuring": concept_graph_structuring_prompt,
    "concept_animation": concept_animation_prompt,
}


@pytest.mark.parametrize(
    "purpose, context, expected, prompt_title",
    EXTENDED_METHOD_CASES,
    ids=[case[0] for case in EXTENDED_METHOD_CASES],
)
def test_openai_chat_transport_runs_extended_requests(monkeypatch, purpose, context, expected, prompt_title):
    fake_openai = install_fake_openai(monkeypatch, expected.model_dump_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile())

    result = client.complete(
        StructuredRequest(
            purpose=purpose,
            prompt=_PROMPT_BUILDERS[purpose](context),
            result_model=type(expected),
        )
    )

    assert result == expected
    requests = fake_openai.instances[0].requests
    assert len(requests) == 1
    assert prompt_title in requests[0]["messages"][1]["content"]


def test_extended_method_repairs_invalid_json_once(monkeypatch):
    fake_openai = install_fake_openai(monkeypatch, "not json", SourceUnitInventory().model_dump_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile())

    context = SourceUnitInventoryContext(
        unit_id="unit_1", semantic_hash="hash", role="reference", inventory_profile="semantic"
    )
    result = client.complete(
        StructuredRequest(
            purpose="source_unit_inventory",
            prompt=source_unit_inventory_prompt(context),
            result_model=SourceUnitInventory,
        )
    )

    assert result == SourceUnitInventory()
    requests = fake_openai.instances[0].requests
    assert len(requests) == 2
    assert "Repair the following model output" in requests[1]["messages"][1]["content"]


def test_json_schema_response_format_sends_strict_per_request_schema(monkeypatch):
    fake_openai = install_fake_openai(monkeypatch, grading_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile(response_format="json_schema"))

    proposal = request_grading_proposal(client, _grading_context())

    assert proposal.rubric_score == 4
    response_format = fake_openai.instances[0].requests[0]["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["name"] == "GradingProposal"
    assert response_format["json_schema"]["strict"] is True
    schema = response_format["json_schema"]["schema"]
    assert schema["additionalProperties"] is False
    assert "rubric_score" in schema["properties"]


class _FakeStatusError(Exception):
    def __init__(self, status_code: int, headers: dict[str, str] | None = None):
        super().__init__(f"status {status_code}")
        self.status_code = status_code
        self.response = types.SimpleNamespace(headers=headers or {})


class _FakeClock:
    """Drives the retry loop's monotonic clock; sleeping advances it."""

    def __init__(self):
        self.now = 0.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def _install_clock(monkeypatch, *, jitter: float = 0.0) -> _FakeClock:
    clock = _FakeClock()
    monkeypatch.setattr(openai_chat_module, "_monotonic", clock.monotonic)
    monkeypatch.setattr(openai_chat_module, "_sleep", clock.sleep)
    monkeypatch.setattr(openai_chat_module, "_random", lambda: jitter)
    return clock


def test_chat_retries_rate_limited_requests_with_jittered_backoff(monkeypatch):
    fake_openai = install_fake_openai(monkeypatch, _FakeStatusError(429), _FakeStatusError(503), grading_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    clock = _install_clock(monkeypatch, jitter=1.0)
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile())

    proposal = request_grading_proposal(client, _grading_context())

    assert proposal.rubric_score == 4
    assert len(fake_openai.instances[0].requests) == 3
    # Exponential ceilings of 1 s and 2 s; jitter scales each into [50%, 100%].
    assert clock.sleeps == [1.0, 2.0]


def test_chat_jitter_spreads_retry_delays_below_the_ceiling(monkeypatch):
    install_fake_openai(monkeypatch, _FakeStatusError(429), grading_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    clock = _install_clock(monkeypatch, jitter=0.0)
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile())

    request_grading_proposal(client, _grading_context())

    assert clock.sleeps == [0.5]


def test_chat_does_not_retry_non_retryable_errors(monkeypatch):
    fake_openai = install_fake_openai(monkeypatch, _FakeStatusError(401))
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    clock = _install_clock(monkeypatch)
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile())

    with pytest.raises(CodexUnavailable):
        request_grading_proposal(client, _grading_context())

    assert len(fake_openai.instances[0].requests) == 1
    assert clock.sleeps == []


@pytest.mark.parametrize("error_kind", ["sdk_connection", "reset", "timeout"])
def test_chat_retries_connection_failures_and_timeouts(monkeypatch, error_kind):
    errors = {
        "sdk_connection": FakeAPIConnectionError("connection dropped"),
        "reset": ConnectionResetError("reset by peer"),
        "timeout": TimeoutError("read timed out"),
    }
    fake_openai = install_fake_openai(monkeypatch, errors[error_kind], grading_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    _install_clock(monkeypatch)
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile())

    proposal = request_grading_proposal(client, _grading_context())

    assert proposal.rubric_score == 4
    assert len(fake_openai.instances[0].requests) == 2


def test_chat_retry_count_stays_bounded(monkeypatch):
    fake_openai = install_fake_openai(monkeypatch, *[_FakeStatusError(503) for _ in range(5)])
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    _install_clock(monkeypatch)
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile())

    with pytest.raises(CodexUnavailable, match="status 503"):
        request_grading_proposal(client, _grading_context())

    assert len(fake_openai.instances[0].requests) == openai_chat_module._MAX_ATTEMPTS


@pytest.mark.parametrize(
    ("headers", "expected_sleep"),
    [({"retry-after": "7"}, 7.0), ({"retry-after-ms": "2500"}, 2.5)],
)
def test_chat_honours_retry_after(monkeypatch, headers, expected_sleep):
    install_fake_openai(monkeypatch, _FakeStatusError(429, headers), grading_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    clock = _install_clock(monkeypatch)
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile())

    request_grading_proposal(client, _grading_context())

    assert clock.sleeps == [expected_sleep]


def test_chat_gives_up_when_retry_after_outlasts_the_deadline(monkeypatch):
    fake_openai = install_fake_openai(monkeypatch, _FakeStatusError(429, {"retry-after": "30"}), grading_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    clock = _install_clock(monkeypatch)
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile(timeout_seconds=20))

    with pytest.raises(CodexUnavailable, match="status 429"):
        request_grading_proposal(client, _grading_context())

    assert len(fake_openai.instances[0].requests) == 1
    assert clock.sleeps == []


def test_chat_retries_share_one_deadline(monkeypatch):
    """Each attempt gets only the time left, and the loop stops before the
    configured timeout rather than starting an attempt it cannot finish."""

    install_fake_openai(monkeypatch)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    clock = _install_clock(monkeypatch)
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile(timeout_seconds=10))
    attempts: list[tuple[float, float]] = []

    def slow_failure(**kwargs):
        attempts.append((clock.now, kwargs["timeout"]))
        clock.now += 6.0
        raise _FakeStatusError(503)

    client._client.chat.completions.create = slow_failure

    with pytest.raises(CodexUnavailable):
        request_grading_proposal(client, _grading_context())

    # (start, timeout): the first attempt fails after 6 s, the 0.5 s backoff
    # leaves 3.5 s for the second, and no third attempt starts past the deadline.
    assert attempts == [(0.0, 10.0), (6.5, 3.5)]


def test_observer_control_exceptions_propagate_unchanged(monkeypatch):
    """A fenced receipt start that refuses the call (lost lease, cancelled job)
    must reach the caller as itself, not as a provider failure."""

    from learnloop.ai.execution import observe_model_calls
    from learnloop.db.scopes import JobOwnershipLost

    fake_openai = install_fake_openai(monkeypatch, grading_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    _install_clock(monkeypatch)
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile())

    def observer(action, event):
        if action == "start" and event["purpose"] == "chat_request":
            raise JobOwnershipLost("job moved to another worker")

    with observe_model_calls(observer), pytest.raises(JobOwnershipLost):
        request_grading_proposal(client, _grading_context())

    assert fake_openai.instances[0].requests == []


def test_failed_receipt_finish_keeps_the_paid_response(monkeypatch, caplog):
    import sqlite3

    from learnloop.ai.execution import observe_model_calls

    fake_openai = install_fake_openai(monkeypatch, grading_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    _install_clock(monkeypatch)
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile())
    events: list[tuple[str, str]] = []

    def observer(action, event):
        events.append((action, event["id"]))
        if action == "finish":
            raise sqlite3.OperationalError("database is locked")

    with observe_model_calls(observer):
        proposal = request_grading_proposal(client, _grading_context())

    assert proposal.rubric_score == 4
    assert len(fake_openai.instances[0].requests) == 1
    assert [action for action, _ in events].count("finish") == 2
    assert "stays 'started'" in caplog.text


def test_json_object_route_carries_the_output_schema_in_the_system_turn(monkeypatch):
    """A ``json_object`` profile puts no schema on the wire, and the feature
    prompt only says "match the provided output schema". Without one in the
    prompt the model guesses field names; every miss defaults at validation
    (a blank provenance ``span``), which the synthesis gates then reject."""

    fake_openai = install_fake_openai(monkeypatch, "not json", grading_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile())

    proposal = request_grading_proposal(client, _grading_context())

    assert proposal.rubric_score == 4
    first, repair = fake_openai.instances[0].requests
    system = first["messages"][0]["content"]
    assert system.startswith("Return only valid JSON.")
    assert "Schema:" in system
    assert '"rubric_score"' in system
    assert '"additionalProperties": false' in system
    # The repair turn already carries the schema in its user message.
    assert "Schema:" not in repair["messages"][0]["content"]


def test_json_schema_route_does_not_duplicate_the_schema_in_the_prompt(monkeypatch):
    fake_openai = install_fake_openai(monkeypatch, grading_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile(response_format="json_schema"))

    request_grading_proposal(client, _grading_context())

    system = fake_openai.instances[0].requests[0]["messages"][0]["content"]
    assert system == "Return only valid JSON. Do not include Markdown fences."

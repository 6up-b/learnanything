from __future__ import annotations

import types

import pytest

import learnloop.ai.openai_chat as openai_chat_module
from learnloop.ai.openai_chat import OpenAIChatProviderClient
from learnloop.codex.client import (
    AppendReconciliationContext,
    CodexUnavailable,
    ConceptAnimationContext,
    ConceptGraphContext,
    DepthEdgeInstanceContext,
    GradingContext,
    ProbeDialogueTurnContext,
    ProbeFamilyTrialsContext,
    ProbeInstanceContext,
    ReaderPresetSynthesisContext,
    ReadingQuickCheckContext,
    RungBackfillContext,
    SdkCodexClient,
    SourceSetSynthesisContext,
    SourceUnitInventoryContext,
)
from learnloop.codex.schemas import (
    AppendReconciliation,
    ConceptGraphStructuring,
    ManimAnimation,
    DepthEdgeInstanceBatch,
    DiagnosticTrials,
    MisconceptionMatch,
    ProbeDialogueTurn,
    ProbeFamilyTrials,
    ProbeInstanceSurfaces,
    PromotionAnalysis,
    ReaderPresetSynthesis,
    ReadingQuickCheck,
    RungBackfillClassification,
    SourceSetSynthesis,
    SourceUnitInventory,
)
from learnloop.config import AIProviderConfig

from tests.openai_fakes import grading_json, install_fake_openai


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

    proposal = client.run_grading_proposal(_grading_context())

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

    proposal = client.run_grading_proposal(_grading_context())

    assert proposal.rubric_score == 4
    assert len(fake_openai.instances[0].requests) == 2
    assert "Repair the following model output" in fake_openai.instances[0].requests[1]["messages"][1]["content"]


def test_openai_chat_client_covers_all_sdk_run_methods():
    sdk_methods = {name for name in dir(SdkCodexClient) if name.startswith("run_")}
    chat_methods = {name for name in dir(OpenAIChatProviderClient) if name.startswith("run_")}

    assert sdk_methods, "expected SdkCodexClient to expose run_* methods"
    assert sdk_methods <= chat_methods, f"missing on chat client: {sorted(sdk_methods - chat_methods)}"


EXTENDED_METHOD_CASES = [
    (
        "run_misconception_match",
        types.SimpleNamespace(statement="Belief.", learning_object_id="lo_1", candidates=[]),
        MisconceptionMatch(decision="new"),
        "learnloop misconception match",
    ),
    (
        "run_promotion_analysis",
        {"intent": "practice", "thread": []},
        PromotionAnalysis(),
        "learnloop promotion analysis",
    ),
    (
        "run_diagnostic_trials",
        {"n_trials": 2, "item_prompt": "Prompt", "misconception_statement": "Belief."},
        DiagnosticTrials(),
        "learnloop diagnostic trials",
    ),
    (
        "run_probe_instance_surfaces",
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
        "run_probe_dialogue_turn",
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
        "run_probe_family_trials",
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
        "run_source_unit_inventory",
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
        "run_source_set_synthesis",
        SourceSetSynthesisContext(source_set_id="set_1", subject_id="subj_1", mode="bootstrap"),
        SourceSetSynthesis(),
        "learnloop source set synthesis",
    ),
    (
        "run_append_reconciliation",
        AppendReconciliationContext(source_set_id="set_1", subject_id="subj_1", change_kind="source_added"),
        AppendReconciliation(),
        "learnloop append reconciliation",
    ),
    (
        "run_reader_preset_synthesis",
        ReaderPresetSynthesisContext(preset="explain"),
        ReaderPresetSynthesis(),
        "learnloop reader preset synthesis",
    ),
    (
        "run_reading_quick_check",
        ReadingQuickCheckContext(extraction_id="ex_1"),
        ReadingQuickCheck(),
        "learnloop reading quick check",
    ),
    (
        "run_rung_backfill",
        RungBackfillContext(),
        RungBackfillClassification(),
        "learnloop rung backfill",
    ),
    (
        "run_depth_edge_instances",
        DepthEdgeInstanceContext(commitment_id="commit_1"),
        DepthEdgeInstanceBatch(),
        "learnloop depth edge instances",
    ),
    (
        "run_concept_graph_structuring",
        ConceptGraphContext(source_set_id="set_1", subject_id="subj_1"),
        ConceptGraphStructuring(),
        "learnloop concept graph structuring",
    ),
    (
        "run_concept_animation",
        ConceptAnimationContext(concept_id="singular_value_decomposition", concept_title="SVD"),
        ManimAnimation(),
        "learnloop concept animation",
    ),
]


@pytest.mark.parametrize(
    "method_name, context, expected, prompt_title",
    EXTENDED_METHOD_CASES,
    ids=[case[0] for case in EXTENDED_METHOD_CASES],
)
def test_openai_chat_client_runs_extended_methods(monkeypatch, method_name, context, expected, prompt_title):
    fake_openai = install_fake_openai(monkeypatch, expected.model_dump_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile())

    result = getattr(client, method_name)(context)

    assert result == expected
    requests = fake_openai.instances[0].requests
    assert len(requests) == 1
    assert prompt_title in requests[0]["messages"][1]["content"]


def test_extended_method_repairs_invalid_json_once(monkeypatch):
    fake_openai = install_fake_openai(monkeypatch, "not json", SourceUnitInventory().model_dump_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile())

    result = client.run_source_unit_inventory(
        SourceUnitInventoryContext(unit_id="unit_1", semantic_hash="hash", role="reference", inventory_profile="semantic")
    )

    assert result == SourceUnitInventory()
    requests = fake_openai.instances[0].requests
    assert len(requests) == 2
    assert "Repair the following model output" in requests[1]["messages"][1]["content"]


def test_json_schema_response_format_sends_strict_per_request_schema(monkeypatch):
    fake_openai = install_fake_openai(monkeypatch, grading_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile(response_format="json_schema"))

    proposal = client.run_grading_proposal(_grading_context())

    assert proposal.rubric_score == 4
    response_format = fake_openai.instances[0].requests[0]["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["name"] == "GradingProposal"
    assert response_format["json_schema"]["strict"] is True
    schema = response_format["json_schema"]["schema"]
    assert schema["additionalProperties"] is False
    assert "rubric_score" in schema["properties"]


class _FakeStatusError(Exception):
    def __init__(self, status_code: int):
        super().__init__(f"status {status_code}")
        self.status_code = status_code


def test_chat_retries_rate_limited_requests_with_backoff(monkeypatch):
    fake_openai = install_fake_openai(monkeypatch, _FakeStatusError(429), grading_json())
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    sleeps: list[float] = []
    monkeypatch.setattr(openai_chat_module, "_sleep", sleeps.append)
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile())

    proposal = client.run_grading_proposal(_grading_context())

    assert proposal.rubric_score == 4
    assert len(fake_openai.instances[0].requests) == 2
    assert sleeps == [openai_chat_module._RETRY_DELAYS_SECONDS[0]]


def test_chat_does_not_retry_non_retryable_errors(monkeypatch):
    fake_openai = install_fake_openai(monkeypatch, _FakeStatusError(401))
    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret")
    sleeps: list[float] = []
    monkeypatch.setattr(openai_chat_module, "_sleep", sleeps.append)
    client = OpenAIChatProviderClient("deepseek_flash", _deepseek_profile())

    with pytest.raises(CodexUnavailable):
        client.run_grading_proposal(_grading_context())

    assert len(fake_openai.instances[0].requests) == 1
    assert sleeps == []

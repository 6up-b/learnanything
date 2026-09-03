"""§N parity oracle for every feature-owned structured AI operation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import pytest

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.providers.codex import SdkCodexClient
from learnloop.ai.providers.codex_http import LegacyHttpOperations
from learnloop.ai.providers.openai_chat import OpenAIChatProviderClient
from learnloop.ai.schemas import WireModel
from learnloop.attempts.ai_contracts import GradingContext, GradingProposal
from learnloop.content.authoring.ai_contracts import (
    ConceptAnimationContext,
    VideoStoryboardContext,
    ExerciseAuthoring,
    ExerciseAuthoringContext,
    ManimAnimation,
    VideoStoryboard,
)
from learnloop.content.pipeline.ai_contracts import CanonicalIngestContext
from learnloop.content.proposals.ai_contracts import AuthoringContext, AuthoringProposal
from learnloop.content.synthesis.ai_contracts import (
    AppendReconciliation,
    AppendReconciliationContext,
    ConceptGraphContext,
    ConceptGraphStructuring,
    SourceSetSynthesis,
    SourceSetSynthesisContext,
    SourceUnitInventory,
    SourceUnitInventoryContext,
)
from learnloop.curriculum.ai_contracts import (
    DepthEdgeInstanceBatch,
    DepthEdgeInstanceContext,
    RungBackfillClassification,
    RungBackfillContext,
)
from learnloop.diagnosis.ai_contracts import (
    DiagnosticFireJudgment,
    DiagnosticTrials,
    MisconceptionMatch,
    ProbeDialogueTurn,
    ProbeDialogueTurnContext,
    ProbeFamilyTrials,
    ProbeFamilyTrialsContext,
    ProbeInstanceContext,
    ProbeInstanceSurfaces,
)
from learnloop.reader.ai_contracts import (
    ReaderPresetSynthesis,
    ReaderPresetSynthesisContext,
    ReadingQuickCheck,
    ReadingQuickCheckContext,
)
from learnloop.tutor.ai_contracts import (
    PromotionAnalysis,
    TeachBackAuthoring,
    TeachBackAuthoringContext,
    TeachBackQuestion,
    TeachBackQuestionContext,
    TutorAnswer,
    TutorQAContext,
    PromotionAnalysisContext,
)
from learnloop.ai.transport import STRUCTURED_COMPLETION
from learnloop.attempts.grading import request_grading_proposal
from learnloop.content.authoring.concept_animation import author_concept_animation, author_video_storyboard
from learnloop.content.authoring.exercise_authoring import request_exercise_authoring
from learnloop.content.pipeline.source_ingestion import request_canonical_ingest
from learnloop.content.proposals.proposals import request_authoring_proposal
from learnloop.content.synthesis.source_append import request_append_reconciliation
from learnloop.content.synthesis.source_set_synthesis import (
    request_concept_graph_structuring,
    request_source_set_synthesis,
)
from learnloop.content.synthesis.source_unit_inventory import request_source_unit_inventory
from learnloop.curriculum.depth_edge_authoring import request_depth_edge_instances
from learnloop.curriculum.rung_backfill import request_rung_backfill
from learnloop.diagnosis.diagnostic_gate import (
    request_diagnostic_fire,
    request_diagnostic_trials,
)
from learnloop.diagnosis.misconceptions import (
    MisconceptionMatchContext,
    request_misconception_match,
)
from learnloop.diagnosis.probe_dialogue import request_probe_dialogue_turn
from learnloop.diagnosis.probe_instance_generation import (
    request_probe_family_trials,
    request_probe_instance_surfaces,
)
from learnloop.reader.reader_quick_check import request_reading_quick_check
from learnloop.reader.reader_requests import request_reader_preset_synthesis
from learnloop.tutor.promotions import request_promotion_analysis
from learnloop.tutor.teach_back import (
    request_teach_back_authoring,
    request_teach_back_question,
)
from learnloop.tutor.tutor_qa import request_tutor_answer
from learnloop.config import AIProviderConfig, CodexConfig

from tests.openai_fakes import install_fake_openai


@dataclass(frozen=True)
class OperationCase:
    name: str
    purpose: str
    invoke: Callable[[Any], Any]
    wire_result: WireModel
    legacy_method: str | None = None

    @property
    def expected_result(self) -> Any:
        if isinstance(self.wire_result, DiagnosticFireJudgment):
            return self.wire_result.fires
        return self.wire_result


_AUTHORING = AuthoringContext(vault_root="/vault", source_ids=[])
_CANONICAL = CanonicalIngestContext(
    vault_root="/vault",
    source_kind="website_page",
    canonical_source={"id": "src_1", "path": "sources/one.md"},
    chunks=[],
)
_GRADING = GradingContext(
    attempt_id="attempt_1",
    practice_item_id="pi_1",
    prompt="What is SVD?",
    expected_answer="U Sigma V transpose.",
    learner_answer_md="U Sigma V transpose.",
    rubric={"max_points": 4, "criteria": []},
)
_TUTOR = TutorQAContext(context="practice", question_md="Why?")
_TEACH_QUESTION = TeachBackQuestionContext(
    practice_item_id="pi_1",
    practice_item_prompt="Explain SVD.",
    criterion_id="correctness",
    criterion_description="Explains the factorization.",
    criterion_tier="core",
)
_TEACH_AUTHORING = TeachBackAuthoringContext(
    source_practice_item_id="pi_1",
    source_prompt="Explain SVD.",
    source_expected_answer="U Sigma V transpose.",
)
_MISCONCEPTION = MisconceptionMatchContext(
    statement="SVD has only two factors.", learning_object_id="lo_1", candidates=[]
)
_PROMOTION = PromotionAnalysisContext(intent="practice")
_PROBE_SURFACES = ProbeInstanceContext(
    family_template_id="family_1",
    family_template_version=1,
    instrument_kind="recall",
    measurement_intent="Measure recall.",
    learning_object_id="lo_1",
    learning_object_title="SVD",
    learning_object_concept="svd",
    learning_object_summary="A matrix factorization.",
)
_PROBE_DIALOGUE = ProbeDialogueTurnContext(
    turn_kind="commit",
    turn_number=1,
    planned_turns=3,
    learning_object_id="lo_1",
    learning_object_title="SVD",
    learning_object_concept="svd",
    learning_object_summary="A matrix factorization.",
)
_PROBE_TRIALS = ProbeFamilyTrialsContext(
    family_template_id="family_1",
    family_template_version=1,
    instrument_kind="recall",
    measurement_intent="Measure recall.",
    learning_object_title="SVD",
    learning_object_summary="A matrix factorization.",
)
_READER_PRESET = ReaderPresetSynthesisContext(preset="worked_example")
_QUICK_CHECK = ReadingQuickCheckContext(extraction_id="extraction_1")
_RUNG = RungBackfillContext()
_EXERCISE = ExerciseAuthoringContext(extraction_id="extraction_1", exercise_text="Compute SVD.")
_DEPTH = DepthEdgeInstanceContext(commitment_id="commitment_1")
_INVENTORY = SourceUnitInventoryContext(
    unit_id="unit_1", semantic_hash="hash", role="reference", inventory_profile="semantic"
)
_SYNTHESIS = SourceSetSynthesisContext(
    source_set_id="set_1", subject_id="subject_1", mode="bootstrap"
)
_GRAPH = ConceptGraphContext(source_set_id="set_1", subject_id="subject_1")
_ANIMATION = ConceptAnimationContext(concept_id="svd", concept_title="SVD")
_STORYBOARD = VideoStoryboardContext(concept_id="svd", concept_title="SVD")
_APPEND = AppendReconciliationContext(
    source_set_id="set_1", subject_id="subject_1", change_kind="source_added"
)


OPERATIONS = (
    OperationCase(
        "authoring_proposal", "authoring",
        lambda client: request_authoring_proposal(client, _AUTHORING),
        AuthoringProposal(summary="ok"), "run_authoring_proposal",
    ),
    OperationCase(
        "canonical_ingest", "canonical_ingest",
        lambda client: request_canonical_ingest(client, _CANONICAL),
        AuthoringProposal(summary="ok"), "run_canonical_ingest",
    ),
    OperationCase(
        "grading_proposal", "grading",
        lambda client: request_grading_proposal(client, _GRADING),
        GradingProposal(
            attempt_id="attempt_1", practice_item_id="pi_1", rubric_score=4,
            grader_confidence=0.9,
        ),
        "run_grading_proposal",
    ),
    OperationCase(
        "tutor_qa", "tutor_qa", lambda client: request_tutor_answer(client, _TUTOR),
        TutorAnswer(answer_md="Consider the dimensions."), "run_tutor_qa",
    ),
    OperationCase(
        "teach_back_question", "teach_back",
        lambda client: request_teach_back_question(client, _TEACH_QUESTION),
        TeachBackQuestion(question_md="Why does that step follow?"),
        "run_teach_back_question",
    ),
    OperationCase(
        "teach_back_authoring", "teach_back_authoring",
        lambda client: request_teach_back_authoring(client, _TEACH_AUTHORING),
        TeachBackAuthoring(prompt_md="Teach SVD."), "run_teach_back_authoring",
    ),
    OperationCase(
        "misconception_match", "misconception_match",
        lambda client: request_misconception_match(client, _MISCONCEPTION),
        MisconceptionMatch(decision="new"), "run_misconception_match",
    ),
    OperationCase(
        "promotion_analysis", "promotion_analysis",
        lambda client: request_promotion_analysis(client, _PROMOTION),
        PromotionAnalysis(), "run_promotion_analysis",
    ),
    OperationCase(
        "diagnostic_trials", "diagnostic_trials",
        lambda client: request_diagnostic_trials(client, {"n_trials": 1}),
        DiagnosticTrials(),
    ),
    OperationCase(
        "diagnostic_fire", "grade_diagnostic_fire",
        lambda client: request_diagnostic_fire(client, answer="wrong", expected="right"),
        DiagnosticFireJudgment(fires=True),
    ),
    OperationCase(
        "probe_instance_surfaces", "probe_instance_surfaces",
        lambda client: request_probe_instance_surfaces(client, _PROBE_SURFACES),
        ProbeInstanceSurfaces(),
    ),
    OperationCase(
        "probe_dialogue_turn", "probe_dialogue_turn",
        lambda client: request_probe_dialogue_turn(client, _PROBE_DIALOGUE),
        ProbeDialogueTurn(prompt_md="Why?", expected_answer_md="Because."),
    ),
    OperationCase(
        "probe_family_trials", "probe_family_trials",
        lambda client: request_probe_family_trials(client, _PROBE_TRIALS),
        ProbeFamilyTrials(),
    ),
    OperationCase(
        "reader_preset_synthesis", "reader_preset_synthesis",
        lambda client: request_reader_preset_synthesis(client, _READER_PRESET),
        ReaderPresetSynthesis(),
    ),
    OperationCase(
        "reading_quick_check", "reading_quick_check",
        lambda client: request_reading_quick_check(client, _QUICK_CHECK),
        ReadingQuickCheck(),
    ),
    OperationCase(
        "rung_backfill", "rung_backfill",
        lambda client: request_rung_backfill(client, _RUNG),
        RungBackfillClassification(),
    ),
    OperationCase(
        "exercise_authoring", "exercise_authoring",
        lambda client: request_exercise_authoring(client, _EXERCISE),
        ExerciseAuthoring(),
    ),
    OperationCase(
        "depth_edge_instances", "depth_edge_instances",
        lambda client: request_depth_edge_instances(client, _DEPTH),
        DepthEdgeInstanceBatch(),
    ),
    OperationCase(
        "source_unit_inventory", "source_unit_inventory",
        lambda client: request_source_unit_inventory(client, _INVENTORY),
        SourceUnitInventory(),
    ),
    OperationCase(
        "source_set_synthesis", "source_set_synthesis",
        lambda client: request_source_set_synthesis(client, _SYNTHESIS),
        SourceSetSynthesis(),
    ),
    OperationCase(
        "concept_graph_structuring", "concept_graph_structuring",
        lambda client: request_concept_graph_structuring(client, _GRAPH),
        ConceptGraphStructuring(),
    ),
    OperationCase(
        "concept_animation", "concept_animation",
        lambda client: author_concept_animation(client, _ANIMATION),
        ManimAnimation(),
    ),
    OperationCase(
        "video_storyboard", "video_storyboard",
        lambda client: author_video_storyboard(client, _STORYBOARD),
        VideoStoryboard(),
    ),
    OperationCase(
        "append_reconciliation", "append_reconciliation",
        lambda client: request_append_reconciliation(client, _APPEND),
        AppendReconciliation(),
    ),
)

assert len(OPERATIONS) == 24
assert len({case.name for case in OPERATIONS}) == 24


@pytest.mark.parametrize("case", OPERATIONS, ids=lambda case: case.name)
def test_sdk_transport_executes_every_feature_operation(case, tmp_path):
    client = SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex")), tmp_path)
    calls: list[tuple[str, dict[str, Any]]] = []

    def run(prompt: str, output_schema: dict[str, Any], *, purpose: str) -> str:
        assert prompt
        calls.append((purpose, output_schema))
        return case.wire_result.model_dump_json()

    client._run_structured = run  # type: ignore[method-assign]

    assert case.invoke(client) == case.expected_result
    assert calls[0][0] == case.purpose
    assert calls[0][1]["additionalProperties"] is False


@pytest.mark.parametrize("case", OPERATIONS, ids=lambda case: case.name)
def test_chat_transport_executes_every_feature_operation(case, monkeypatch):
    fake_openai = install_fake_openai(monkeypatch, case.wire_result.model_dump_json())
    monkeypatch.setenv("TEST_CHAT_API_KEY", "secret")
    client = OpenAIChatProviderClient(
        "chat",
        AIProviderConfig(
            type="openai_chat",
            base_url="https://chat.example/v1",
            api_key_env="TEST_CHAT_API_KEY",
            model="test-model",
            response_format="json_schema",
        ),
    )

    assert case.invoke(client) == case.expected_result
    request = fake_openai.instances[0].requests[0]
    assert request["response_format"]["json_schema"]["name"] == type(case.wire_result).__name__


def test_structured_providers_expose_no_feature_named_methods():
    assert {name for name in dir(SdkCodexClient) if name.startswith("run_")} == set()
    assert {
        name for name in dir(OpenAIChatProviderClient) if name.startswith("run_")
    } == {"run_media_markdown", "run_media_transcription"}


def test_legacy_http_supports_exactly_eight_operations_and_degrades_the_rest(monkeypatch):
    client = LegacyHttpOperations(CodexConfig(base_url="http://127.0.0.1:1"))
    expected_supported = {case.purpose for case in OPERATIONS if case.legacy_method is not None}

    assert expected_supported == {
        "authoring",
        "canonical_ingest",
        "grading",
        "tutor_qa",
        "teach_back",
        "teach_back_authoring",
        "misconception_match",
        "promotion_analysis",
    }
    assert not client.supports(STRUCTURED_COMPLETION)
    assert {case.purpose for case in OPERATIONS if client.supports(case.purpose)} == expected_supported

    for case in OPERATIONS:
        if case.legacy_method is not None:
            monkeypatch.setattr(
                client,
                "_post",
                lambda *_args, result=case.wire_result, **_kwargs: {
                    "proposal": result.model_dump(mode="json")
                },
            )
            assert case.invoke(client) == case.expected_result
        else:
            monkeypatch.setattr(
                client,
                "_post",
                lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    AssertionError("degradation must not make an HTTP request")
                ),
            )
            with pytest.raises(AIProviderUnavailable, match=case.purpose):
                case.invoke(client)

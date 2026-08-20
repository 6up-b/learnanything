"""Compatibility fixture for tests migrating to the structured AI transport.

Production providers intentionally expose no feature-named methods.  Existing
test doubles may keep their compact, feature-named result builders while this
mixin presents the transport contract exercised by production call sites.
"""

from __future__ import annotations

import json
from typing import Any

from learnloop.ai.transport import STRUCTURED_COMPLETION, StructuredRequest
from learnloop.ai.usage import TokenUsage
from learnloop.attempts.ai_contracts import GradingContext
from learnloop.content.authoring.ai_contracts import ConceptAnimationContext, ExerciseAuthoringContext
from learnloop.content.pipeline.ai_contracts import (
    CanonicalIngestContext,
    ExtractionPlan,
    SourceChunk,
)
from learnloop.content.proposals.ai_contracts import AuthoringContext
from learnloop.content.synthesis.ai_contracts import (
    AppendReconciliationContext,
    ConceptGraphContext,
    SourceSetSynthesisContext,
    SourceUnitInventoryContext,
)
from learnloop.curriculum.ai_contracts import DepthEdgeInstanceContext, RungBackfillContext
from learnloop.diagnosis.ai_contracts import (
    ProbeDialogueTurnContext,
    ProbeFamilyTrialsContext,
    ProbeInstanceContext,
)
from learnloop.reader.ai_contracts import ReaderPresetSynthesisContext, ReadingQuickCheckContext
from learnloop.tutor.ai_contracts import (
    PromotionAnalysisContext,
    TeachBackAuthoringContext,
    TeachBackQuestionContext,
    TutorQAContext,
)


_HANDLER_FOR_PURPOSE = {
    "authoring": "run_authoring_proposal",
    "canonical_ingest": "run_canonical_ingest",
    "grading": "run_grading_proposal",
    "tutor_qa": "run_tutor_qa",
    "teach_back": "run_teach_back_question",
    "teach_back_authoring": "run_teach_back_authoring",
    "misconception_match": "run_misconception_match",
    "promotion_analysis": "run_promotion_analysis",
    "diagnostic_trials": "run_diagnostic_trials",
    "grade_diagnostic_fire": "grade_diagnostic_fire",
    "probe_instance_surfaces": "run_probe_instance_surfaces",
    "probe_dialogue_turn": "run_probe_dialogue_turn",
    "probe_family_trials": "run_probe_family_trials",
    "reader_preset_synthesis": "run_reader_preset_synthesis",
    "reading_quick_check": "run_reading_quick_check",
    "rung_backfill": "run_rung_backfill",
    "exercise_authoring": "run_exercise_authoring",
    "depth_edge_instances": "run_depth_edge_instances",
    "source_unit_inventory": "run_source_unit_inventory",
    "source_set_synthesis": "run_source_set_synthesis",
    "concept_graph_structuring": "run_concept_graph_structuring",
    "concept_animation": "run_concept_animation",
    "append_reconciliation": "run_append_reconciliation",
}

_CONTEXT_FOR_PURPOSE = {
    "authoring": AuthoringContext,
    "canonical_ingest": CanonicalIngestContext,
    "grading": GradingContext,
    "tutor_qa": TutorQAContext,
    "teach_back": TeachBackQuestionContext,
    "teach_back_authoring": TeachBackAuthoringContext,
    "promotion_analysis": PromotionAnalysisContext,
    "probe_instance_surfaces": ProbeInstanceContext,
    "probe_dialogue_turn": ProbeDialogueTurnContext,
    "probe_family_trials": ProbeFamilyTrialsContext,
    "reader_preset_synthesis": ReaderPresetSynthesisContext,
    "reading_quick_check": ReadingQuickCheckContext,
    "rung_backfill": RungBackfillContext,
    "exercise_authoring": ExerciseAuthoringContext,
    "depth_edge_instances": DepthEdgeInstanceContext,
    "source_unit_inventory": SourceUnitInventoryContext,
    "source_set_synthesis": SourceSetSynthesisContext,
    "concept_graph_structuring": ConceptGraphContext,
    "concept_animation": ConceptAnimationContext,
    "append_reconciliation": AppendReconciliationContext,
}


class _AttributeMapping(dict):
    """JSON mapping that supports both context.foo and context["foo"]."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:  # pragma: no cover - normal AttributeError contract
            raise AttributeError(name) from exc


def _attribute_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _AttributeMapping({key: _attribute_value(item) for key, item in value.items()})
    if isinstance(value, list):
        return [_attribute_value(item) for item in value]
    return value


def _request_context(prompt: str, purpose: str) -> Any:
    """Decode the JSON payload appended by every structured prompt builder."""

    candidates = prompt.split("\n\n")
    for candidate in reversed(candidates):
        try:
            payload = json.loads(candidate)
        except (TypeError, ValueError):
            continue
        if isinstance(payload, dict):
            context = payload.get("context", payload)
            if isinstance(context, dict):
                context_type = _CONTEXT_FOR_PURPOSE.get(purpose)
                if context_type is not None:
                    if purpose == "canonical_ingest":
                        context = {
                            **context,
                            "chunks": [
                                SourceChunk(**chunk)
                                for chunk in context.get("chunks", [])
                            ],
                            "extraction_plan": ExtractionPlan(
                                **context.get("extraction_plan", {})
                            ),
                        }
                    return context_type(**context)
                return _attribute_value(context)
    raise AssertionError("structured test request contained no JSON context payload")


class StructuredClientFake:
    """Expose ``complete/supports`` around a legacy-shaped test result builder."""

    provider_name = "fake"
    provider_type = "fake"
    model = "fake-model"

    def supports(self, capability: str) -> bool:
        return capability == STRUCTURED_COMPLETION

    def complete(self, request: StructuredRequest[Any]) -> Any:
        context = _request_context(request.prompt, request.purpose)
        handler_name = _HANDLER_FOR_PURPOSE[request.purpose]
        if request.purpose == "grade_diagnostic_fire":
            from learnloop.diagnosis.ai_contracts import DiagnosticFireJudgment
            from learnloop.diagnosis.diagnostic_gate import normalize_answer

            try:
                handler = object.__getattribute__(self, handler_name)
            except AttributeError:
                fires = normalize_answer(context.get("answer")) != normalize_answer(
                    context.get("expected")
                )
            else:
                fires = bool(handler(**context))
            return DiagnosticFireJudgment(fires=fires)
        handler = object.__getattribute__(self, handler_name)
        return handler(context)

    def consume_usage(self) -> TokenUsage:
        return TokenUsage()

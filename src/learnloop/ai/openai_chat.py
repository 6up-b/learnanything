from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from pydantic import BaseModel, ValidationError

from learnloop.config import AIProviderConfig
from learnloop.ai.multimodal import (
    MediaTranscript,
    MediaTranscriptionContext,
    PdfExtractionContextNative,
    audio_content_parts,
    media_transcription_prompt,
    pdf_content_parts,
    pdf_markdown_prompt,
    strip_markdown_fences,
)
from learnloop.codex.client import (
    AppendReconciliationContext,
    AuthoringContext,
    CanonicalIngestContext,
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
    SourceSetSynthesisContext,
    SourceUnitInventoryContext,
    TeachBackQuestionContext,
    TutorQAContext,
    _append_reconciliation_prompt,
    _authoring_prompt,
    _canonical_ingest_prompt,
    _codex_output_schema,
    _concept_animation_prompt,
    _concept_graph_structuring_prompt,
    _depth_edge_instance_prompt,
    _diagnostic_trials_prompt,
    _grading_prompt,
    _misconception_match_prompt,
    _probe_dialogue_turn_prompt,
    _probe_family_trials_prompt,
    _probe_instance_surfaces_prompt,
    _promotion_analysis_prompt,
    _reader_preset_synthesis_prompt,
    _reading_quick_check_prompt,
    _rung_backfill_prompt,
    _source_set_synthesis_prompt,
    _source_unit_inventory_prompt,
    _teach_back_question_prompt,
    _tutor_qa_prompt,
)
from learnloop.codex.schemas import (
    AppendReconciliation,
    AuthoringProposal,
    ConceptGraphStructuring,
    ManimAnimation,
    DepthEdgeInstanceBatch,
    DiagnosticTrials,
    GradingProposal,
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
    TeachBackQuestion,
    TutorAnswer,
)

logger = logging.getLogger(__name__)

# Module-level so tests can monkeypatch the backoff away.
_sleep = time.sleep
_RETRY_DELAYS_SECONDS = (1.0, 4.0)


class OpenAIChatProviderClient:
    provider_type = "openai_chat"
    # Subclass hooks: a provider type with a fixed endpoint (e.g. openrouter)
    # overrides these so profiles only need a model slug.
    default_base_url: str | None = None
    default_api_key_env = "OPENAI_API_KEY"

    def __init__(self, provider_name: str, profile: AIProviderConfig):
        self.provider_name = provider_name
        self.profile = profile
        self.model = profile.model
        if not self.model:
            raise CodexUnavailable(f"AI provider {provider_name!r} is missing model")
        base_url = profile.base_url or self.default_base_url
        if not base_url:
            raise CodexUnavailable(f"AI provider {provider_name!r} is missing base_url")
        api_key_env = profile.api_key_env or self.default_api_key_env
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise CodexUnavailable(f"Environment variable {api_key_env} is required for {provider_name}")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise CodexUnavailable("The openai package is required for openai_chat providers.") from exc
        client_kwargs: dict[str, Any] = {
            "api_key": api_key,
            "base_url": base_url,
            "timeout": profile.timeout_seconds,
        }
        headers = self._default_headers()
        if headers:
            client_kwargs["default_headers"] = headers
        self._client = OpenAI(**client_kwargs)

    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal:
        return self._run_json_model(_authoring_prompt(context), AuthoringProposal)

    def run_canonical_ingest(self, context: CanonicalIngestContext) -> AuthoringProposal:
        return self._run_json_model(_canonical_ingest_prompt(context), AuthoringProposal)

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        return self._run_json_model(_grading_prompt(context), GradingProposal)

    def run_tutor_qa(self, context: TutorQAContext) -> TutorAnswer:
        return self._run_json_model(_tutor_qa_prompt(context), TutorAnswer)

    def run_teach_back_question(self, context: TeachBackQuestionContext) -> TeachBackQuestion:
        return self._run_json_model(_teach_back_question_prompt(context), TeachBackQuestion)

    def run_misconception_match(self, context: Any) -> MisconceptionMatch:
        return self._run_json_model(_misconception_match_prompt(context), MisconceptionMatch)

    def run_promotion_analysis(self, context: Any) -> PromotionAnalysis:
        return self._run_json_model(_promotion_analysis_prompt(context), PromotionAnalysis)

    def run_diagnostic_trials(self, context: Any) -> DiagnosticTrials:
        return self._run_json_model(_diagnostic_trials_prompt(context), DiagnosticTrials)

    def run_probe_instance_surfaces(self, context: ProbeInstanceContext) -> ProbeInstanceSurfaces:
        return self._run_json_model(_probe_instance_surfaces_prompt(context), ProbeInstanceSurfaces)

    def run_probe_dialogue_turn(self, context: ProbeDialogueTurnContext) -> ProbeDialogueTurn:
        return self._run_json_model(_probe_dialogue_turn_prompt(context), ProbeDialogueTurn)

    def run_probe_family_trials(self, context: ProbeFamilyTrialsContext) -> ProbeFamilyTrials:
        return self._run_json_model(_probe_family_trials_prompt(context), ProbeFamilyTrials)

    def run_source_unit_inventory(self, context: SourceUnitInventoryContext) -> SourceUnitInventory:
        return self._run_json_model(_source_unit_inventory_prompt(context), SourceUnitInventory)

    def run_source_set_synthesis(self, context: SourceSetSynthesisContext) -> SourceSetSynthesis:
        return self._run_json_model(_source_set_synthesis_prompt(context), SourceSetSynthesis)

    def run_append_reconciliation(self, context: AppendReconciliationContext) -> AppendReconciliation:
        return self._run_json_model(_append_reconciliation_prompt(context), AppendReconciliation)

    def run_reader_preset_synthesis(self, context: ReaderPresetSynthesisContext) -> ReaderPresetSynthesis:
        return self._run_json_model(_reader_preset_synthesis_prompt(context), ReaderPresetSynthesis)

    def run_reading_quick_check(self, context: ReadingQuickCheckContext) -> ReadingQuickCheck:
        return self._run_json_model(_reading_quick_check_prompt(context), ReadingQuickCheck)

    def run_rung_backfill(self, context: RungBackfillContext) -> RungBackfillClassification:
        return self._run_json_model(_rung_backfill_prompt(context), RungBackfillClassification)

    def run_depth_edge_instances(self, context: DepthEdgeInstanceContext) -> DepthEdgeInstanceBatch:
        return self._run_json_model(_depth_edge_instance_prompt(context), DepthEdgeInstanceBatch)

    def run_concept_graph_structuring(self, context: ConceptGraphContext) -> ConceptGraphStructuring:
        return self._run_json_model(_concept_graph_structuring_prompt(context), ConceptGraphStructuring)

    def run_concept_animation(self, context: ConceptAnimationContext) -> ManimAnimation:
        return self._run_json_model(_concept_animation_prompt(context), ManimAnimation)

    def run_media_transcription(self, context: MediaTranscriptionContext) -> MediaTranscript:
        """Native-multimodal audio → timestamped transcript ([ingest.native]).

        The user content carries an ``input_audio`` part; the output contract is
        a transcript, never a study map, so downstream IR matches the endpoint
        transcription path exactly. The JSON-repair round is text-only — the
        audio is never re-uploaded."""

        parts = audio_content_parts(
            media_transcription_prompt(context), context.media_bytes, context.media_format
        )
        return self._run_json_messages(
            [
                {"role": "system", "content": "Return only valid JSON. Do not include Markdown fences."},
                {"role": "user", "content": parts},
            ],
            MediaTranscript,
        )

    def run_media_markdown(self, context: PdfExtractionContextNative) -> str:
        """Native-multimodal PDF → GitHub-flavored Markdown ([ingest.pdf] engine
        "native"). Suppresses the profile's JSON response_format — the output is
        a document, not JSON."""

        parts = pdf_content_parts(
            pdf_markdown_prompt(context), context.media_bytes, context.filename
        )
        text = self._chat_messages(
            [
                {
                    "role": "system",
                    "content": "Convert documents to complete GitHub-flavored Markdown. Do not wrap the whole output in code fences.",
                },
                {"role": "user", "content": parts},
            ],
            None,
            use_response_format=False,
        )
        markdown = strip_markdown_fences(text)
        if not markdown:
            raise CodexUnavailable(f"{self.provider_name} returned an empty document")
        return markdown

    def _run_json_model(self, prompt: str, model_type: type[BaseModel]) -> Any:
        return self._run_json_messages(
            [
                {"role": "system", "content": "Return only valid JSON. Do not include Markdown fences."},
                {"role": "user", "content": prompt},
            ],
            model_type,
        )

    def _run_json_messages(self, messages: list[dict[str, Any]], model_type: type[BaseModel]) -> Any:
        text = self._chat_messages(messages, model_type)
        try:
            return model_type.model_validate_json(text)
        except (ValidationError, ValueError, json.JSONDecodeError):
            repaired = self._chat(_repair_prompt(text, model_type), model_type)
            try:
                return model_type.model_validate_json(repaired)
            except (ValidationError, ValueError, json.JSONDecodeError) as second_exc:
                raise CodexUnavailable(f"{self.provider_name} returned invalid {model_type.__name__} JSON") from second_exc

    def _chat(self, prompt: str, model_type: type[BaseModel] | None = None) -> str:
        return self._chat_messages(
            [
                {"role": "system", "content": "Return only valid JSON. Do not include Markdown fences."},
                {"role": "user", "content": prompt},
            ],
            model_type,
        )

    def _chat_messages(
        self,
        messages: list[dict[str, Any]],
        model_type: type[BaseModel] | None = None,
        *,
        use_response_format: bool = True,
    ) -> str:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if use_response_format:
            response_format = self._response_format(model_type)
            if response_format:
                kwargs["response_format"] = response_format
        if self.profile.max_tokens is not None:
            kwargs["max_tokens"] = self.profile.max_tokens
        kwargs.update(self._reasoning_kwargs())
        response = self._create_with_retry(kwargs)
        content = response.choices[0].message.content
        if not isinstance(content, str) or not content.strip():
            raise CodexUnavailable(f"{self.provider_name} returned an empty response")
        return content.strip()

    def _create_with_retry(self, kwargs: dict[str, Any]) -> Any:
        for attempt in range(len(_RETRY_DELAYS_SECONDS) + 1):
            try:
                return self._client.chat.completions.create(**kwargs)
            except Exception as exc:
                if attempt < len(_RETRY_DELAYS_SECONDS) and _is_retryable(exc):
                    logger.warning(
                        "AI provider %s (%s) request failed with retryable error, retrying: %s",
                        self.provider_name,
                        self.model,
                        exc,
                    )
                    _sleep(_RETRY_DELAYS_SECONDS[attempt])
                    continue
                logger.warning(
                    "AI provider %s (%s) request failed: %s", self.provider_name, self.model, exc
                )
                raise CodexUnavailable(str(exc)) from exc
        raise CodexUnavailable(f"{self.provider_name} request retries exhausted")

    def _response_format(self, model_type: type[BaseModel] | None) -> dict[str, Any] | None:
        configured = (self.profile.response_format or "").strip()
        if not configured:
            return None
        if configured == "json_schema":
            if model_type is None:
                return {"type": "json_object"}
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": model_type.__name__,
                    "strict": True,
                    "schema": _codex_output_schema(model_type),
                },
            }
        return {"type": configured}

    def _reasoning_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        extra_body: dict[str, Any] = {}
        thinking = (self.profile.thinking or "").strip()
        if thinking:
            extra_body["thinking"] = {"type": thinking}
            if thinking != "disabled" and self.profile.reasoning_effort:
                kwargs["reasoning_effort"] = self.profile.reasoning_effort
        if extra_body:
            kwargs["extra_body"] = extra_body
        return kwargs

    def _default_headers(self) -> dict[str, str] | None:
        return None


def _is_retryable(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if not isinstance(status_code, int):
        return False
    return status_code == 429 or status_code >= 500


def _repair_prompt(text: str, model_type: type[BaseModel]) -> str:
    schema = json.dumps(model_type.model_json_schema(), sort_keys=True, ensure_ascii=False)
    return (
        "Repair the following model output into a JSON object that validates against "
        f"this JSON schema. Return only JSON.\n\nSchema:\n{schema}\n\nOutput:\n{text}"
    )

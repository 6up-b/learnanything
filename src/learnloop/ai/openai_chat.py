from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from pydantic import BaseModel, ValidationError

from learnloop.config import AIProviderConfig
from learnloop.codex.client import (
    AppendReconciliationContext,
    AuthoringContext,
    CanonicalIngestContext,
    CodexUnavailable,
    GradingContext,
    ProbeDialogueTurnContext,
    ProbeFamilyTrialsContext,
    ProbeInstanceContext,
    SourceSetSynthesisContext,
    SourceUnitInventoryContext,
    TeachBackQuestionContext,
    TutorQAContext,
    _append_reconciliation_prompt,
    _authoring_prompt,
    _canonical_ingest_prompt,
    _codex_output_schema,
    _diagnostic_trials_prompt,
    _grading_prompt,
    _misconception_match_prompt,
    _probe_dialogue_turn_prompt,
    _probe_family_trials_prompt,
    _probe_instance_surfaces_prompt,
    _promotion_analysis_prompt,
    _source_set_synthesis_prompt,
    _source_unit_inventory_prompt,
    _teach_back_question_prompt,
    _tutor_qa_prompt,
)
from learnloop.codex.schemas import (
    AppendReconciliation,
    AuthoringProposal,
    DiagnosticTrials,
    GradingProposal,
    MisconceptionMatch,
    ProbeDialogueTurn,
    ProbeFamilyTrials,
    ProbeInstanceSurfaces,
    PromotionAnalysis,
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

    def _run_json_model(self, prompt: str, model_type: type[BaseModel]) -> Any:
        text = self._chat(prompt, model_type)
        try:
            return model_type.model_validate_json(text)
        except (ValidationError, ValueError, json.JSONDecodeError):
            repaired = self._chat(_repair_prompt(text, model_type), model_type)
            try:
                return model_type.model_validate_json(repaired)
            except (ValidationError, ValueError, json.JSONDecodeError) as second_exc:
                raise CodexUnavailable(f"{self.provider_name} returned invalid {model_type.__name__} JSON") from second_exc

    def _chat(self, prompt: str, model_type: type[BaseModel] | None = None) -> str:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Return only valid JSON. Do not include Markdown fences."},
                {"role": "user", "content": prompt},
            ],
        }
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

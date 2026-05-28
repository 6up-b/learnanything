from __future__ import annotations

import json
import os
from typing import Any

from pydantic import BaseModel, ValidationError

from learnloop.config import AIProviderConfig
from learnloop.codex.client import (
    AuthoringContext,
    CanonicalIngestContext,
    CodexUnavailable,
    GradingContext,
    _authoring_prompt,
    _canonical_ingest_prompt,
    _grading_prompt,
)
from learnloop.codex.schemas import AuthoringProposal, GradingProposal


class OpenAIChatProviderClient:
    provider_type = "openai_chat"

    def __init__(self, provider_name: str, profile: AIProviderConfig):
        self.provider_name = provider_name
        self.profile = profile
        self.model = profile.model
        if not self.model:
            raise CodexUnavailable(f"AI provider {provider_name!r} is missing model")
        if not profile.base_url:
            raise CodexUnavailable(f"AI provider {provider_name!r} is missing base_url")
        api_key_env = profile.api_key_env or "OPENAI_API_KEY"
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise CodexUnavailable(f"Environment variable {api_key_env} is required for {provider_name}")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise CodexUnavailable("The openai package is required for openai_chat providers.") from exc
        self._client = OpenAI(api_key=api_key, base_url=profile.base_url, timeout=profile.timeout_seconds)

    def run_authoring_proposal(self, context: AuthoringContext) -> AuthoringProposal:
        return self._run_json_model(_authoring_prompt(context), AuthoringProposal)

    def run_canonical_ingest(self, context: CanonicalIngestContext) -> AuthoringProposal:
        return self._run_json_model(_canonical_ingest_prompt(context), AuthoringProposal)

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        return self._run_json_model(_grading_prompt(context), GradingProposal)

    def _run_json_model(self, prompt: str, model_type: type[BaseModel]) -> Any:
        text = self._chat(prompt)
        try:
            return model_type.model_validate_json(text)
        except (ValidationError, ValueError, json.JSONDecodeError) as first_exc:
            repaired = self._chat(_repair_prompt(text, model_type))
            try:
                return model_type.model_validate_json(repaired)
            except (ValidationError, ValueError, json.JSONDecodeError) as second_exc:
                raise CodexUnavailable(f"{self.provider_name} returned invalid {model_type.__name__} JSON") from second_exc

    def _chat(self, prompt: str) -> str:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Return only valid JSON. Do not include Markdown fences."},
                {"role": "user", "content": prompt},
            ],
        }
        if self.profile.response_format:
            kwargs["response_format"] = {"type": self.profile.response_format}
        if self.profile.max_tokens is not None:
            kwargs["max_tokens"] = self.profile.max_tokens
        extra_body: dict[str, Any] = {}
        thinking = (self.profile.thinking or "").strip()
        if thinking:
            extra_body["thinking"] = {"type": thinking}
            if thinking != "disabled" and self.profile.reasoning_effort:
                kwargs["reasoning_effort"] = self.profile.reasoning_effort
        if extra_body:
            kwargs["extra_body"] = extra_body
        try:
            response = self._client.chat.completions.create(**kwargs)
        except Exception as exc:
            raise CodexUnavailable(str(exc)) from exc
        content = response.choices[0].message.content
        if not isinstance(content, str) or not content.strip():
            raise CodexUnavailable(f"{self.provider_name} returned an empty response")
        return content.strip()


def _repair_prompt(text: str, model_type: type[BaseModel]) -> str:
    schema = json.dumps(model_type.model_json_schema(), sort_keys=True, ensure_ascii=False)
    return (
        "Repair the following model output into a JSON object that validates against "
        f"this JSON schema. Return only JSON.\n\nSchema:\n{schema}\n\nOutput:\n{text}"
    )

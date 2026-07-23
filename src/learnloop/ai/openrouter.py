from __future__ import annotations

from typing import Any

from learnloop.ai.openai_chat import OpenAIChatProviderClient

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY_ENV = "OPENROUTER_API_KEY"


class OpenRouterProviderClient(OpenAIChatProviderClient):
    """OpenAI-compatible provider client configured for OpenRouter."""

    provider_type = "openrouter"
    default_base_url = OPENROUTER_BASE_URL
    default_api_key_env = OPENROUTER_API_KEY_ENV

    def _default_headers(self) -> dict[str, str] | None:
        headers = {"X-Title": self.profile.x_title or "LearnLoop"}
        if self.profile.http_referer:
            headers["HTTP-Referer"] = self.profile.http_referer
        return headers

    def _reasoning_kwargs(self) -> dict[str, Any]:
        thinking = (self.profile.thinking or "").strip().lower()
        effort = (self.profile.reasoning_effort or "").strip().lower()
        if thinking == "disabled" or not effort:
            return {}
        return {"extra_body": {"reasoning": {"effort": effort}}}

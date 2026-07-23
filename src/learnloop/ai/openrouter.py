from __future__ import annotations

from typing import Any

from learnloop.ai.openai_chat import OpenAIChatProviderClient

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY_ENV = "OPENROUTER_API_KEY"


class OpenRouterProviderClient(OpenAIChatProviderClient):
    """OpenAI-compatible chat client pointed at OpenRouter.

    Any OpenRouter model slug works as ``profile.model`` (e.g.
    ``anthropic/claude-sonnet-4.5``, ``deepseek/deepseek-chat``). Differences
    from the generic openai_chat type: the endpoint and key env var have
    defaults, requests carry OpenRouter's attribution headers, and reasoning is
    requested via OpenRouter's unified ``reasoning`` body instead of the
    DeepSeek-dialect ``thinking`` body (which 400s on strict providers).
    """

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

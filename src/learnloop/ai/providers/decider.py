"""The ``decider`` transport: Perplexity's Decider over OpenRouter or direct.

Pinned from the providers' documentation (checked 2026-10-12, recorded in
``docs/reviews/router-r0.md``):

* **OpenRouter** (the owner's route, ``api = "openrouter"``): ``POST
  https://openrouter.ai/api/alpha/decisions`` ("Submit a Decisions request to
  the Decisions router"), ``Authorization: Bearer $OPENROUTER_API_KEY``. The
  model is ``perplexity/pplx-decider-v1.1-27b`` (modality
  ``text+image->decisions``, one provider: Perplexity). The response adds
  ``id``, ``provider`` and ``usage.cost`` to Perplexity's shape, and ``model``
  is the dated slug that answered.
* **Perplexity direct** (``api = "perplexity"``): ``POST
  https://api.perplexity.ai/v1/decisions``, ``Authorization: Bearer
  $PERPLEXITY_API_KEY``, model ``pplx-decider-v1.1-27b``. Unknown top-level
  fields return 400; the body here never has any.

One ``decide`` is one physical request: no SDK, no hidden retries, no
splitting. A 429 or 5xx surfaces to the caller, who owns any retry and its
spend reservation. Each call is a ``model_call`` whose receipt records the
request body, usage, the provider's cost and the model that answered.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import http.client
import json
import math
import os
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

from learnloop.ai.decisions import (
    DecisionResult, DecisionState, Question, parse_response, request_body, validate_questions,
)
from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.execution import model_call, report_call_usage
from learnloop.config import AIProviderConfig
from learnloop.config.schema import DEFAULT_DECIDER_MODEL, DEFAULT_DECIDER_PRICE_PER_MILLION_INPUT

#: The capability a decision transport declares (it has no chat completion).
DECISIONS = "decisions"

_DIALECTS: dict[str, dict[str, str]] = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api",
        "path": "/alpha/decisions",
        "api_key_env": "OPENROUTER_API_KEY",
        "model": DEFAULT_DECIDER_MODEL,
    },
    "perplexity": {
        "base_url": "https://api.perplexity.ai",
        "path": "/v1/decisions",
        "api_key_env": "PERPLEXITY_API_KEY",
        "model": "pplx-decider-v1.1-27b",
    },
}
DEFAULT_TIMEOUT_SECONDS = 30.0
#: Conservative token estimate for budgeting: UTF-8 bytes / 3, rounded up.
#: The Decider's tokenizer is unpublished; bytes/3 over-counts English text.
BYTES_PER_TOKEN_ESTIMATE = 3
#: Error text kept on an exception: enough to read the reason, never a body.
_ERROR_TEXT_LIMIT = 300

#: (method, url, headers, body, timeout) -> (status, headers, body)
HttpTransport = Callable[[str, str, Mapping[str, str], bytes | None, float], tuple[int, Mapping[str, str], bytes]]


class DecisionRequestFailed(AIProviderUnavailable):
    """The provider answered with an error status; nothing was parsed."""

    def __init__(self, message: str, *, status: int, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.retry_after = retry_after


@dataclass(frozen=True)
class DeciderSettings:
    """A profile's effective, non-secret settings (``api`` fills the gaps)."""

    api: str
    base_url: str
    url: str
    api_key_env: str
    model: str
    timeout_seconds: float
    price_per_million_input: float
    max_input_tokens: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "api": self.api, "base_url": self.base_url, "url": self.url,
            "api_key_env": self.api_key_env, "model": self.model,
            "timeout_seconds": self.timeout_seconds,
            "price_per_million_input": self.price_per_million_input,
            "max_input_tokens": self.max_input_tokens,
        }


def resolved_decider_settings(profile: AIProviderConfig) -> DeciderSettings:
    api = getattr(profile, "api", None) or "openrouter"
    if api not in _DIALECTS:
        raise AIProviderUnavailable(f"Unknown decider api {api!r}; use openrouter or perplexity")
    dialect = _DIALECTS[api]
    base_url = (profile.base_url or dialect["base_url"]).rstrip("/")
    price = getattr(profile, "price_per_million_input", None)
    max_input = getattr(profile, "max_input_tokens", None)
    return DeciderSettings(
        api=api,
        base_url=base_url,
        url=base_url + dialect["path"],
        api_key_env=getattr(profile, "api_key_env", None) or dialect["api_key_env"],
        model=profile.model or dialect["model"],
        timeout_seconds=float(profile.timeout_seconds or DEFAULT_TIMEOUT_SECONDS),
        price_per_million_input=float(DEFAULT_DECIDER_PRICE_PER_MILLION_INPUT if price is None else price),
        max_input_tokens=int(max_input or 262_144),
    )


def encode_body(body: Mapping[str, Any]) -> bytes:
    """Deterministic bytes that keep insertion order.

    Keys are not sorted: the order of ``choice`` options and of the state's
    sections is the caller's, and it can matter to the model.
    """

    return json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def estimate_input_tokens(body: Mapping[str, Any]) -> int:
    return math.ceil(len(encode_body(body)) / BYTES_PER_TOKEN_ESTIMATE)


def _urllib_transport(
    method: str, url: str, headers: Mapping[str, str], body: bytes | None, timeout: float,
) -> tuple[int, Mapping[str, str], bytes]:
    request = urllib.request.Request(url, data=body, headers=dict(headers), method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - https API
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers or {}), exc.read()
    except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
        # Only the exception class travels: a reason can echo the URL.
        raise AIProviderUnavailable(f"Decision endpoint unreachable ({type(exc).__name__})") from None


def _error_message(raw: bytes) -> str:
    try:
        payload = json.loads(raw.decode("utf-8")) if raw else {}
    except (UnicodeDecodeError, ValueError):
        return "no JSON error body"
    error = payload.get("error") if isinstance(payload, Mapping) else None
    if isinstance(error, Mapping):
        message = error.get("message")
        kind = error.get("type")
        text = f"{kind}: {message}" if kind else str(message)
    else:
        text = str(error or "no error object")
    return text[:_ERROR_TEXT_LIMIT]


def _retry_after(headers: Mapping[str, str]) -> float | None:
    for key, value in headers.items():
        if key.lower() == "retry-after":
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
    return None


class DeciderProviderClient:
    """``DecisionClient`` over HTTP; never a chat or structured-completion transport."""

    provider_type = "decider"

    def __init__(
        self, provider_name: str, profile: AIProviderConfig, *, http: HttpTransport | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.profile = profile
        self.settings = resolved_decider_settings(profile)
        self.model = self.settings.model
        self.model_id = self.settings.model
        self.default_base_url = self.settings.base_url
        key = os.environ.get(self.settings.api_key_env)
        if not key:
            raise AIProviderUnavailable(f"Environment variable {self.settings.api_key_env} is required.")
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.settings.api == "openrouter":
            # OpenRouter attribution headers, as the chat client sends them.
            headers["X-Title"] = getattr(profile, "x_title", None) or "LearnLoop"
            referer = getattr(profile, "http_referer", None)
            if referer:
                headers["HTTP-Referer"] = referer
        self._headers = headers
        self._http: HttpTransport = http or _urllib_transport

    def supports(self, capability: str) -> bool:
        return capability == DECISIONS

    def estimated_cost(self, input_tokens: int) -> float:
        """Input-only price; the Decider's output tokens are free."""

        return input_tokens * self.settings.price_per_million_input / 1_000_000

    def decide(
        self, state: DecisionState, questions: Mapping[str, Question], *, purpose: str,
    ) -> DecisionResult:
        checked = validate_questions(questions)
        body = request_body(self.model, state, checked)
        encoded = encode_body(body)
        if math.ceil(len(encoded) / BYTES_PER_TOKEN_ESTIMATE) > self.settings.max_input_tokens:
            raise ValueError("Decision state exceeds the model's input limit; shorten it before paying")
        with model_call(
            self, purpose=purpose, prompt=encoded.decode("utf-8"),
            schema={name: question.wire() for name, question in checked.items()},
        ) as metadata:
            status, headers, raw = self._http(
                "POST", self.settings.url, self._headers, encoded, self.settings.timeout_seconds,
            )
            if status != 200:
                # A rejected request is normally free, but its usage is
                # unknown: the receipt keeps NULL usage rather than zero.
                raise DecisionRequestFailed(
                    f"Decision request failed: HTTP {status}: {_error_message(raw)}",
                    status=status, retry_after=_retry_after(headers),
                )
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                payload = None
            metadata["output_text"] = raw.decode("utf-8", errors="replace")
            # Usage is recorded before parsing so a malformed paid answer
            # still leaves an honest receipt.
            usage = payload.get("usage") if isinstance(payload, Mapping) else None
            if isinstance(usage, Mapping):
                report_call_usage({
                    "input_tokens": usage.get("input_tokens") if isinstance(usage.get("input_tokens"), int) else None,
                    "output_tokens": usage.get("output_tokens") if isinstance(usage.get("output_tokens"), int) else None,
                    "cost": usage.get("cost") if isinstance(usage.get("cost"), (int, float)) else None,
                })
            if isinstance(payload, Mapping):
                report_call_usage({
                    "provider_response_id": payload.get("id") if isinstance(payload.get("id"), str) else None,
                    "resolved_model": payload.get("model") if isinstance(payload.get("model"), str) else None,
                })
            return parse_response(payload, checked)


def probe_decider_endpoint(
    profile: AIProviderConfig, *, http: HttpTransport | None = None, timeout: float = 10.0,
) -> dict[str, Any]:
    """Free reachability check: OpenRouter's public endpoint listing for the model.

    No key and no learner text are sent, and nothing is billed. Perplexity's
    direct API has no free listing, so only a paid call could confirm it.
    """

    settings = resolved_decider_settings(profile)
    if settings.api != "openrouter":
        return {"reachable": None, "checked": False,
                "message": "Perplexity's direct API has no free model listing; only a paid call confirms it."}
    url = f"{settings.base_url}/v1/models/{urllib.parse.quote(settings.model, safe='/.-_')}/endpoints"
    status, _headers, raw = (http or _urllib_transport)("GET", url, {"Accept": "application/json"}, None, timeout)
    if status != 200:
        return {"reachable": False, "checked": True, "status": status,
                "message": f"Model listing returned HTTP {status}"}
    try:
        data = json.loads(raw.decode("utf-8")).get("data") or {}
    except (UnicodeDecodeError, ValueError, AttributeError):
        return {"reachable": False, "checked": True, "status": status, "message": "Unreadable model listing"}
    modalities = list((data.get("architecture") or {}).get("output_modalities") or [])
    endpoints = [
        {
            "provider": endpoint.get("provider_name"),
            "name": endpoint.get("name"),
            "status": endpoint.get("status"),
            "context_length": endpoint.get("context_length"),
            "prompt_price_per_token": (endpoint.get("pricing") or {}).get("prompt"),
            "completion_price_per_token": (endpoint.get("pricing") or {}).get("completion"),
        }
        for endpoint in data.get("endpoints") or []
        if isinstance(endpoint, Mapping)
    ]
    serves = "decisions" in modalities and bool(endpoints)
    return {
        "reachable": serves, "checked": True, "status": status, "model": data.get("id"),
        "output_modalities": modalities, "endpoints": endpoints,
        "message": "Listed with a decisions endpoint." if serves else "Not listed as a decision model.",
    }


__all__ = [
    "DECISIONS",
    "DeciderProviderClient",
    "DeciderSettings",
    "DecisionRequestFailed",
    "HttpTransport",
    "encode_body",
    "estimate_input_tokens",
    "probe_decider_endpoint",
    "resolved_decider_settings",
]

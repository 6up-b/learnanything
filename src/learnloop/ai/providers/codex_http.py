"""Legacy endpoint-per-operation Codex HTTP adapter."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from pydantic import BaseModel, ValidationError

from learnloop.ai.errors import AIInvalidOutput, AIProviderUnavailable, CodexUnavailable
from learnloop.ai.providers.codex import _log_codex_debug, codex_config_from_ai_profile
from learnloop.ai.schemas import describe_wire_validation_error
from learnloop.ai.transport import StructuredRequest, WireResult, prompt_safe
from learnloop.ai.usage import TokenUsageAccounting, usage_from_chat_response
from learnloop.config import AIProviderConfig, CodexConfig

#: Transport-level keys an app-server may report beside a flat proposal body.
#: They belong to the response envelope, never to the wire contract.
_HTTP_ENVELOPE_KEYS = frozenset({"usage"})


class HttpCodexClient(TokenUsageAccounting):
    """Minimal local Codex app-server client.

    The MVP transport is intentionally small: JSON POSTs to a local app-server.
    The server may return the proposal directly or under a top-level
    ``proposal`` key.
    """

    def __init__(self, config: CodexConfig):
        self.config = config
        self.provider_name = "codex"
        self.provider_type = "http_adapter"
        self.model = config.model

    def supports(self, capability: str) -> bool:
        """Declare only the eight endpoint operations this adapter implements."""

        return capability in _HTTP_OPERATIONS

    def complete_legacy(
        self,
        request: StructuredRequest[WireResult],
        *,
        context: object,
    ) -> WireResult:
        """Execute one of the adapter's eight endpoint-bound operations.

        Feature code owns the context and result model.  The adapter owns only
        endpoint routing, the transport envelope, and validation against the
        model carried by ``StructuredRequest``; it never imports a domain.
        """

        purpose = request.purpose
        if purpose not in _HTTP_OPERATIONS:
            raise AIProviderUnavailable(
                f"Legacy HTTP adapter does not support structured operation {purpose!r}"
            )
        path_attribute, default_path = _HTTP_PATHS[purpose]
        path = getattr(self.config, path_attribute, default_path)
        payload = self._post(
            path,
            {"context": prompt_safe(context)},
            purpose=purpose,
        )
        return self._validated(request.result_model, payload, purpose=purpose)

    def _validated(self, model_type: type[BaseModel], payload: dict, *, purpose: str) -> Any:
        """Validate one app-server response body against its wire contract.

        The transport envelope is stripped first. The adapter contract says the
        server "may return the proposal directly or under a top-level
        ``proposal`` key", and separately that it may report ``usage`` beside it
        (see ``_post``) — so on the flat shape the metering object is part of
        the envelope, not of the proposal, and stripping it is what keeps
        ``WireModel``'s ban aimed at genuine contract divergence. Before that
        ban, a flat-shaped body simply had its ``usage`` deleted here in
        silence, which is the same failure mode from the other side: the model
        was never wrong, it just never learned it was being ignored.
        """

        if "proposal" in payload:
            body: Any = payload["proposal"]
        else:
            body = {key: value for key, value in payload.items() if key not in _HTTP_ENVELOPE_KEYS}
        try:
            return model_type.model_validate(body)
        except ValidationError as exc:
            raise AIInvalidOutput(
                f"Codex app-server returned an invalid {purpose} response: "
                f"{describe_wire_validation_error(model_type, exc)}"
            ) from exc

    def _post(self, path: str, payload: dict, *, purpose: str) -> dict:
        url = _url(self.config.base_url, path)
        _log_codex_debug(
            "codex.http.request",
            provider="codex",
            provider_type=self.provider_type,
            purpose=purpose,
            model=self.config.model,
            url=url,
            path=path,
            request_payload=payload,
        )
        request = urllib.request.Request(
            url,
            data=json.dumps(payload, sort_keys=True).encode("utf-8"),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.healthcheck_timeout_seconds) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            _log_codex_debug(
                "codex.error",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                url=url,
                path=path,
                error=f"HTTP {exc.code}",
            )
            raise CodexUnavailable(f"Codex app-server HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            _log_codex_debug(
                "codex.error",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                url=url,
                path=path,
                error=str(exc.reason),
            )
            raise CodexUnavailable(str(exc.reason)) from exc
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            _log_codex_debug(
                "codex.error",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                url=url,
                path=path,
                response_text=_decode_lossy(raw),
                error="invalid_json",
            )
            raise CodexUnavailable("Codex app-server returned invalid JSON") from exc
        if not isinstance(decoded, dict):
            _log_codex_debug(
                "codex.error",
                provider="codex",
                provider_type=self.provider_type,
                purpose=purpose,
                model=self.config.model,
                url=url,
                path=path,
                response=decoded,
                error="non_object_response",
            )
            raise CodexUnavailable("Codex app-server response must be a JSON object")
        # A7: the adapter contract does not require a `usage` object, so this is
        # opportunistic — an app-server that reports one in the OpenAI shape gets
        # metered, one that does not leaves the run's actual_* columns at 0.
        self.record_token_usage(*usage_from_chat_response(decoded))
        _log_codex_debug(
            "codex.http.response",
            provider="codex",
            provider_type=self.provider_type,
            purpose=purpose,
            model=self.config.model,
            url=url,
            path=path,
            response=decoded,
        )
        return decoded


def _url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def _decode_lossy(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace")


_HTTP_OPERATIONS = frozenset({
    "authoring",
    "canonical_ingest",
    "grading",
    "tutor_qa",
    "teach_back",
    "teach_back_authoring",
    "misconception_match",
    "promotion_analysis",
})

_HTTP_PATHS = {
    "authoring": ("authoring_path", "/authoring"),
    "canonical_ingest": ("canonical_ingest_path", "/canonical-ingest"),
    "grading": ("grading_path", "/grading"),
    "tutor_qa": ("tutor_qa_path", "/tutor-qa"),
    "teach_back": ("teach_back_path", "/teach-back"),
    "teach_back_authoring": ("teach_back_authoring_path", "/teach-back-authoring"),
    "misconception_match": ("misconception_match_path", "/misconception-match"),
    "promotion_analysis": ("promotion_analysis_path", "/promotion-analysis"),
}


# Keep the compatibility class surface without pretending this endpoint-bound
# adapter implements provider-neutral ``StructuredTransport.complete``.
LegacyHttpOperations = HttpCodexClient


class HttpAdapterProviderClient(HttpCodexClient):
    provider_type = "http_adapter"

    def __init__(self, provider_name: str, profile: AIProviderConfig):
        super().__init__(codex_config_from_ai_profile(profile))
        self.provider_name = provider_name
        self.model = profile.model or self.config.model

"""OpenAI-compatible chat structured transport."""

from __future__ import annotations

import email.utils
import json
import logging
import os
import random
import time
from contextvars import ContextVar
from typing import Any

from pydantic import BaseModel, ValidationError

from learnloop.ai.errors import AIInvalidOutput, AIOutputTruncated, CodexUnavailable
from learnloop.ai.execution import model_call, report_call_usage, single_request_active
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
from learnloop.ai.strict_schema import strict_output_schema
from learnloop.ai.transport import (
    BOUNDED_STRUCTURED_COMPLETION,
    MEDIA_MARKDOWN,
    MEDIA_TRANSCRIPTION,
    STRUCTURED_COMPLETION,
    StructuredRequest,
)
from learnloop.ai.usage import TokenUsageAccounting, receipt_fields_from_chat_response, usage_from_chat_response
from learnloop.config import AIProviderConfig

logger = logging.getLogger(__name__)

# Retry policy for one HTTP request. The SDK's own retries are disabled so
# that every physical attempt opens its own receipt; the loop below owns them.
# The configured request timeout bounds the whole loop, not each attempt, so a
# caller's deadline (for example the sidecar's) is never exceeded by retries.
_MAX_ATTEMPTS = 3
_BACKOFF_BASE_SECONDS = 1.0
_BACKOFF_CAP_SECONDS = 8.0
# A server that asks for a longer pause than this is treated as unavailable.
_RETRY_AFTER_CAP_SECONDS = 60.0
# Starting an attempt with less time than this left cannot plausibly succeed.
_MIN_ATTEMPT_SECONDS = 1.0
# Request timeout, lock contention and rate limiting; every 5xx is retried too.
_RETRYABLE_STATUS_CODES = frozenset({408, 409, 429})

# Module-level so tests can replace time and randomness.
_sleep = time.sleep
_monotonic = time.monotonic
_random = random.random
_JSON_ONLY_SYSTEM_PROMPT = "Return only valid JSON. Do not include Markdown fences."
_request_options: ContextVar[tuple[float | None, int | None]] = ContextVar("chat_request_options", default=(None, None))


class OpenAIChatProviderClient(TokenUsageAccounting):
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
            import openai
        except ImportError as exc:
            raise CodexUnavailable("The openai package is required for openai_chat providers.") from exc
        # The SDK wraps every transport failure (reset, DNS, read timeout) in
        # APIConnectionError; APITimeoutError is a subclass.
        sdk_connection_error = getattr(openai, "APIConnectionError", None)
        self._connection_errors: tuple[type[BaseException], ...] = (ConnectionError, TimeoutError) + (
            (sdk_connection_error,) if isinstance(sdk_connection_error, type) else ()
        )
        client_kwargs: dict[str, Any] = {
            "api_key": api_key,
            "base_url": base_url,
            "timeout": profile.timeout_seconds,
            "max_retries": 0,
        }
        headers = self._default_headers()
        if headers:
            client_kwargs["default_headers"] = headers
        self._client = openai.OpenAI(**client_kwargs)

    def complete(self, request: StructuredRequest[Any]) -> Any:
        """Execute one validated structured request with one bounded repair."""

        token = _request_options.set((request.timeout_seconds, request.output_budget_tokens))
        try:
            return self._run_json_messages(
                [
                    {"role": "system", "content": self._system_prompt(request.result_model)},
                    {"role": "user", "content": request.prompt},
                ],
                request.result_model,
            )
        finally:
            _request_options.reset(token)

    def supports(self, capability: str) -> bool:
        if capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION, "complete", "structured"}:
            return True
        modalities = set(self.profile.input_modalities or [])
        if capability in {MEDIA_TRANSCRIPTION, "audio"}:
            return "audio" in modalities
        if capability in {MEDIA_MARKDOWN, "pdf"}:
            return "pdf" in modalities
        return False

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

    def _run_json_messages(self, messages: list[dict[str, Any]], model_type: type[BaseModel]) -> Any:
        text = self._chat_messages(messages, model_type)
        try:
            return model_type.model_validate_json(text)
        except (ValidationError, ValueError, json.JSONDecodeError) as first_exc:
            if single_request_active():
                raise AIInvalidOutput(f"{self.provider_name} returned invalid {model_type.__name__} JSON") from first_exc
            repaired = self._chat(_repair_prompt(text, model_type), model_type)
            try:
                return model_type.model_validate_json(repaired)
            except (ValidationError, ValueError, json.JSONDecodeError) as second_exc:
                raise AIInvalidOutput(f"{self.provider_name} returned invalid {model_type.__name__} JSON") from second_exc

    def _chat(self, prompt: str, model_type: type[BaseModel] | None = None) -> str:
        return self._chat_messages(
            [
                {"role": "system", "content": _JSON_ONLY_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            model_type,
        )

    def _system_prompt(self, model_type: type[BaseModel]) -> str:
        """The system turn for a first structured attempt.

        Feature prompts end with "match the provided output schema", but only
        two routes actually provide one: Codex's Responses API and the
        ``json_schema`` response_format. A ``json_object`` profile (the
        OpenRouter/DeepSeek default) left the model guessing field names from
        prose; every field it did not guess defaulted at validation, so a
        provenance ``span`` arrived as empty strings and the synthesis gates
        rejected it as a citation to nowhere. Carry the same strict schema in
        the prompt whenever the wire does not.
        """

        response_format = self._response_format(model_type) or {}
        if response_format.get("type") == "json_schema":
            return _JSON_ONLY_SYSTEM_PROMPT
        schema = json.dumps(_prompt_schema(model_type), sort_keys=True, ensure_ascii=False)
        return (
            f"{_JSON_ONLY_SYSTEM_PROMPT} The JSON object must validate against this JSON "
            "schema; emit every declared field and no others.\n\n"
            f"Schema:\n{schema}"
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
        request_timeout, request_budget = _request_options.get()
        if request_timeout is not None:
            kwargs["timeout"] = request_timeout
        if use_response_format:
            response_format = self._response_format(model_type)
            if response_format:
                kwargs["response_format"] = response_format
        limits = [limit for limit in (self.profile.max_tokens, request_budget) if limit is not None]
        if limits:
            if min(limits) <= 0:
                raise AIOutputTruncated("No generation budget remains for JSON repair.")
            kwargs["max_tokens"] = min(limits)
        kwargs.update(self._reasoning_kwargs())
        response = self._create_with_retry(kwargs)
        content = response.choices[0].message.content
        if not isinstance(content, str) or not content.strip():
            raise CodexUnavailable(f"{self.provider_name} returned an empty response")
        return content.strip()

    def _create_with_retry(self, kwargs: dict[str, Any]) -> Any:
        request_timeout, _ = _request_options.get()
        deadline_seconds = request_timeout if request_timeout is not None else self.profile.timeout_seconds
        started = _monotonic()
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            attempt_kwargs = dict(kwargs)
            if deadline_seconds is not None:
                attempt_kwargs["timeout"] = max(_MIN_ATTEMPT_SECONDS, deadline_seconds - (_monotonic() - started))
            try:
                return self._send_once(attempt_kwargs)
            except _RequestFailed as failure:
                error = failure.error
            delay = self._retry_delay(error, attempt, started=started, deadline_seconds=deadline_seconds)
            if delay is None:
                logger.warning("AI provider %s (%s) request failed: %s", self.provider_name, self.model, error)
                raise CodexUnavailable(str(error)) from error
            logger.warning(
                "AI provider %s (%s) request failed with retryable error, retrying in %.1fs: %s",
                self.provider_name,
                self.model,
                delay,
                error,
            )
            _sleep(delay)
        raise AssertionError("unreachable: the final attempt either returns or raises")

    def _send_once(self, kwargs: dict[str, Any]) -> Any:
        """One physical request under its own receipt.

        Only an exception raised by the provider request becomes ``_RequestFailed``
        (a retry candidate). Anything the receipt observer raises, such as a job
        that lost its lease or was cancelled before the request started,
        propagates unchanged so the caller's control flow still sees it.
        """

        request_error: Exception | None = None
        with model_call(self, purpose="chat_request", prompt=kwargs.get("messages"), schema=kwargs.get("response_format"), budget=kwargs.get("max_tokens")) as receipt:
            try:
                response = self._client.chat.completions.create(**kwargs)
            except Exception as exc:
                request_error = exc
                receipt.update(status="failed", error_type=type(exc).__name__)
            else:
                # Meter before anything inspects the body: a truncated or
                # unparseable response was still paid for.
                self._meter_response(response)
                if getattr(response.choices[0], "finish_reason", None) == "length":
                    raise AIOutputTruncated(f"{self.provider_name} exhausted its output budget; increase the budget or reduce the window size.")
                return response
        raise _RequestFailed(request_error)

    def _meter_response(self, response: Any) -> None:
        """Record usage on the receipt and the run, and spend the request budget."""

        report_call_usage(receipt_fields_from_chat_response(response))
        input_tokens, output_tokens = usage_from_chat_response(response)
        self.record_token_usage(input_tokens, output_tokens)
        timeout, budget = _request_options.get()
        if budget is not None:
            content = response.choices[0].message.content or ""
            spent = output_tokens or max(1, (len(content) + 3) // 4)
            _request_options.set((timeout, max(0, budget - spent)))

    def _retry_delay(self, error: Exception, attempt: int, *, started: float, deadline_seconds: float | None) -> float | None:
        """Seconds to wait before the next attempt, or None to give up."""

        if single_request_active() or attempt >= _MAX_ATTEMPTS or not self._is_retryable(error):
            return None
        retry_after = _retry_after_seconds(error)
        if retry_after is not None:
            if retry_after > _RETRY_AFTER_CAP_SECONDS:
                return None
            delay = retry_after
        else:
            # Jitter keeps parallel inventory workers that failed together from
            # retrying in lockstep.
            ceiling = min(_BACKOFF_CAP_SECONDS, _BACKOFF_BASE_SECONDS * 2 ** (attempt - 1))
            delay = ceiling * (0.5 + 0.5 * _random())
        if deadline_seconds is not None:
            elapsed = _monotonic() - started
            if elapsed + delay + _MIN_ATTEMPT_SECONDS > deadline_seconds:
                return None
        return delay

    def _is_retryable(self, error: Exception) -> bool:
        if isinstance(error, self._connection_errors):
            return True
        status_code = getattr(error, "status_code", None)
        if not isinstance(status_code, int):
            return False
        return status_code in _RETRYABLE_STATUS_CODES or status_code >= 500

    def _response_format(self, model_type: type[BaseModel] | None) -> dict[str, Any] | None:
        # Consulted before the first turn to decide whether the schema must
        # ride in the prompt; a profile without response_format sends nothing
        # on the wire.
        configured = (getattr(self.profile, "response_format", None) or "").strip()
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
                    "schema": strict_output_schema(model_type),
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


class _RequestFailed(Exception):
    """The provider request itself failed; ``error`` is what it raised."""

    def __init__(self, error: Exception):
        super().__init__(str(error))
        self.error = error


def _retry_after_seconds(error: Exception) -> float | None:
    """The server's requested pause from ``retry-after-ms`` or ``Retry-After``.

    ``Retry-After`` may be delta-seconds or an HTTP date.
    """

    headers = getattr(getattr(error, "response", None), "headers", None)
    get_header = getattr(headers, "get", None)
    if not callable(get_header):
        return None
    for name, scale in (("retry-after-ms", 0.001), ("retry-after", 1.0)):
        try:
            return max(0.0, float(get_header(name)) * scale)
        except (TypeError, ValueError):
            continue
    parsed = email.utils.parsedate_tz(str(get_header("retry-after") or ""))
    if parsed is None:
        return None
    return max(0.0, email.utils.mktime_tz(parsed) - time.time())


def _prompt_schema(model_type: type[BaseModel]) -> dict[str, Any]:
    # The strict schema is the leaner one (no defaults/titles) and is what the
    # schema-carrying routes send; a plain BaseModel (media transcripts) has no
    # strict form, so its ordinary schema stands in.
    try:
        return strict_output_schema(model_type)
    except TypeError:
        return model_type.model_json_schema()


def _repair_prompt(text: str, model_type: type[BaseModel]) -> str:
    schema = json.dumps(model_type.model_json_schema(), sort_keys=True, ensure_ascii=False)
    return (
        "Repair the following model output into a JSON object that validates against "
        f"this JSON schema. Return only JSON.\n\nSchema:\n{schema}\n\nOutput:\n{text}"
    )

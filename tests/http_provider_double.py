"""A stand-in model for end-to-end tests: an endpoint-per-operation HTTP client.

The Codex HTTP adapter left the product with the rest of the Codex transport
(refactor C4). End-to-end CLI, sidecar and TUI tests still drive an in-process
HTTP server as their model: ``tests.helpers.configure_codex_http`` names an
``http`` profile, and the ``legacy_codex_http_double`` fixture (conftest)
installs this module for that profile type only. Production refuses an
``http`` profile at every entry (``learnloop.ai.agent_harness``); nothing
outside tests can serve one.

What the fixture installs, and why each seam:

* the agent-harness refusal stops covering ``http`` (routing, readiness and the
  client factory all ask ``learnloop.ai.agent_harness``);
* ``learnloop.ai.client.make_ai_provider_client_from_profile`` builds
  :class:`HttpProviderDouble` for an ``http`` profile;
* ``learnloop.ai.runtime.check_ai_runtime`` answers an ``http`` profile with
  the old adapter's readiness: the checkout path, its pinned revision, then a
  ``GET`` of the health path, so a test whose server is down still reads
  unavailable.

The client and the readiness keep the adapter's behaviour as the tests knew it
(its default endpoint paths, the ``proposal`` envelope, ``usage`` metering).
"""

from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from learnloop.ai.errors import AIInvalidOutput, AIProviderUnavailable, CodexUnavailable
from learnloop.ai.execution import report_call_usage
from learnloop.ai.schemas import describe_wire_validation_error
from learnloop.ai.transport import StructuredRequest, WireResult, prompt_safe
from learnloop.ai.usage import TokenUsageAccounting, receipt_fields_from_chat_response, usage_from_chat_response

HTTP_PROFILE_TYPES = frozenset({"http", "http_adapter"})

#: Transport-level keys an app-server may report beside a flat proposal body.
_HTTP_ENVELOPE_KEYS = frozenset({"usage"})

#: The eight operations and the endpoint path each posts to when the profile names none.
_HTTP_PATHS = {
    "authoring": ("authoring_path", "/authoring-proposal"),
    "canonical_ingest": ("canonical_ingest_path", "/canonical-ingest"),
    "grading": ("grading_path", "/grading-proposal"),
    "tutor_qa": ("tutor_qa_path", "/tutor-qa"),
    "teach_back": ("teach_back_path", "/teach-back"),
    "teach_back_authoring": ("teach_back_authoring_path", "/teach-back-authoring"),
    "misconception_match": ("misconception_match_path", "/misconception-match"),
    "promotion_analysis": ("promotion_analysis_path", "/promotion-analysis"),
}

_DEFAULT_BASE_URL = "http://127.0.0.1:8765"
_DEFAULT_MODEL = "gpt-5.6-sol"
_PINNED_REVISION_PLACEHOLDER = "<pinned-commit>"


def _setting(profile: Any, name: str, default: Any) -> Any:
    value = getattr(profile, name, None)
    return default if value in (None, "") else value


class HttpProviderDouble(TokenUsageAccounting):
    """JSON POSTs to a local server, one endpoint per operation.

    The server may return the proposal directly or under a top-level
    ``proposal`` key, and may report an OpenAI-shaped ``usage`` beside it.
    """

    provider_type = "http_adapter"

    def __init__(self, provider_name: str, profile: Any):
        self.provider_name = provider_name
        self.profile = profile
        self.model = _setting(profile, "model", _DEFAULT_MODEL)
        self.base_url = _setting(profile, "base_url", _DEFAULT_BASE_URL)
        self.timeout_seconds = _setting(profile, "timeout_seconds", 180)

    def supports(self, capability: str) -> bool:
        return capability in _HTTP_PATHS

    def complete_legacy(self, request: StructuredRequest[WireResult], *, context: object) -> WireResult:
        purpose = request.purpose
        if purpose not in _HTTP_PATHS:
            raise AIProviderUnavailable(f"Legacy HTTP adapter does not support structured operation {purpose!r}")
        attribute, default_path = _HTTP_PATHS[purpose]
        payload = self._post(
            _setting(self.profile, attribute, default_path),
            {"context": prompt_safe(context)},
            timeout_seconds=request.timeout_seconds,
        )
        return self._validated(request.result_model, payload, purpose=purpose)

    def _validated(self, model_type: type[BaseModel], payload: dict, *, purpose: str) -> Any:
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

    def _post(self, path: str, payload: dict, *, timeout_seconds: float | None = None) -> dict:
        request = urllib.request.Request(
            _url(self.base_url, path),
            data=json.dumps(payload, sort_keys=True).encode("utf-8"),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds or self.timeout_seconds) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raise CodexUnavailable(f"Codex app-server HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise CodexUnavailable(str(exc.reason)) from exc
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CodexUnavailable("Codex app-server returned invalid JSON") from exc
        if not isinstance(decoded, dict):
            raise CodexUnavailable("Codex app-server response must be a JSON object")
        report_call_usage(receipt_fields_from_chat_response(decoded))
        self.record_token_usage(*usage_from_chat_response(decoded))
        return decoded


def http_readiness(vault_root: Path, profile: Any) -> tuple[str, str | None, str]:
    """``(state, revision, message)`` as the old adapter's runtime check answered them."""

    checkout = str(_setting(profile, "checkout_path", "")).strip()
    if not checkout:
        return "provider_missing_config", None, "Codex checkout path is not configured."
    path = Path(checkout)
    path = path.resolve() if path.is_absolute() else (vault_root / path).resolve()
    if not path.is_dir():
        return "provider_missing_config", None, "Codex checkout path does not exist."
    configured = str(_setting(profile, "revision", _PINNED_REVISION_PLACEHOLDER))
    actual = _checkout_revision(path)
    if configured != _PINNED_REVISION_PLACEHOLDER:
        if actual is None:
            return "provider_unavailable", None, "Could not determine Codex checkout revision."
        if not actual.startswith(configured):
            return "provider_revision_mismatch", actual, "Codex checkout revision does not match configuration."
    health = urllib.request.Request(
        _url(_setting(profile, "base_url", _DEFAULT_BASE_URL), _setting(profile, "healthcheck_path", "/health")),
        headers={"Accept": "application/json"},
        method="GET",
    )
    timeout = _setting(profile, "healthcheck_timeout_seconds", None) or _setting(profile, "timeout_seconds", 5)
    try:
        with urllib.request.urlopen(health, timeout=timeout) as response:
            body = response.read(65536)
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403}:
            return "provider_auth_required", actual, "Codex app-server authentication is required."
        return "provider_unavailable", actual, f"Codex healthcheck HTTP {exc.code}."
    except (urllib.error.URLError, OSError) as exc:
        return "provider_unavailable", actual, str(getattr(exc, "reason", exc))
    if body:
        try:
            data = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return "provider_unavailable", actual, "Codex healthcheck returned invalid JSON."
        state = str(data.get("status") or data.get("state") or "ready").lower()
        if state in {"auth_required", "unauthorized", "login_required"}:
            return "provider_auth_required", actual, data.get("message") or "Codex authentication is required."
        if state not in {"ready", "ok", "healthy"}:
            return "provider_unavailable", actual, data.get("message") or f"Codex runtime is not ready: {state}"
    return "ready", actual, "Codex runtime is ready."


def install(monkeypatch: Any) -> None:
    """Let ``http`` profiles serve through :class:`HttpProviderDouble` for one test."""

    from learnloop.ai import agent_harness, client, runtime

    monkeypatch.setattr(
        agent_harness, "AGENT_HARNESS_PROFILE_TYPES",
        frozenset(agent_harness.AGENT_HARNESS_PROFILE_TYPES - HTTP_PROFILE_TYPES),
    )
    build = client.make_ai_provider_client_from_profile
    check = runtime.check_ai_runtime

    def make_client(provider_name: str, profile: Any, vault_root: Path, **kwargs: Any) -> Any:
        if str(profile.type).strip().lower() in HTTP_PROFILE_TYPES:
            return HttpProviderDouble(provider_name, profile)
        return build(provider_name, profile, vault_root, **kwargs)

    def check_ai_runtime(vault_root: Path, config: Any, *, provider_name: str | None = None, **kwargs: Any) -> Any:
        import os

        selected = provider_name or os.environ.get("LEARNLOOP_AI_PROVIDER") or config.ai.active_provider
        profile = config.ai.providers.get(selected)
        if profile is None or str(profile.type).strip().lower() not in HTTP_PROFILE_TYPES:
            return check(vault_root, config, provider_name=provider_name, **kwargs)
        state, revision, message = http_readiness(Path(vault_root), profile)
        return runtime.AIRuntimeReport(
            status=state, active_provider=selected, provider_type=str(profile.type).lower(),
            model=profile.model, provider_revision=revision, message=message,
        )

    monkeypatch.setattr(client, "make_ai_provider_client_from_profile", make_client)
    monkeypatch.setattr(runtime, "check_ai_runtime", check_ai_runtime)


def _url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def _checkout_revision(checkout_path: Path) -> str | None:
    if not (checkout_path / ".git").exists():
        head = checkout_path / "HEAD"
        return (head.read_text(encoding="utf-8").strip() or None) if head.exists() else None
    result = subprocess.run(
        ["git", "-C", str(checkout_path), "rev-parse", "HEAD"],
        check=False, capture_output=True, text=True, timeout=5,
    )
    return (result.stdout.strip() or None) if result.returncode == 0 else None

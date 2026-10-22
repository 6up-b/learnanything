"""The E0 provider boundary: no provider message leaves an E0 path (fix round 4, High 8).

A provider's error text can echo what was sent, a credential included (an
authentication error body quoting the submitted key). The shared production
chat client logs provider exceptions verbatim and raises
``CodexUnavailable(str(error))`` (``learnloop.ai.providers.openai_chat``);
the CLI used to print whatever it caught. Production code is not changed
here (recorded as a production follow-up). Instead, on every E0 path:

* :func:`provider_failure` turns any provider exception into
  :class:`~budget.E0ProviderFailure`, which carries only an allowlisted
  classification, an HTTP status code and a request id matching a safe
  pattern; the original exception is dropped (``raise ... from None``, and
  its context cleared), so no traceback carries its text either;
* :func:`quiet_provider_logs` sanitizes every log record from the provider
  and retrieval loggers (``learnloop.ai``, ``learnloop.source_retrieval``,
  ``openai``, ``httpx``, ``httpcore``) at every handler, the last-resort
  handler included: the record keeps its logger, level and the exception's
  type name, never its message, arguments or traceback;
* :func:`safe_message` is what the CLI prints for any failure.
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import logging
from pathlib import Path
import re
import threading
from typing import Any

from learnloop.experiments.contextual_embeddings.budget import E0ProviderFailure, E0Stop

#: Loggers whose records may carry provider text.
PROVIDER_LOGGERS = ("learnloop.ai", "learnloop.source_retrieval", "openai", "httpx", "httpcore")
CLASSIFICATIONS = ("auth", "rate_limited", "timeout", "unavailable", "invalid_output", "truncated", "interrupted", "refusal",
                   "contract", "pin_mismatch", "network", "unknown")
_SAFE_ID = re.compile(r"[A-Za-z0-9_.:-]{1,80}")
_SAFE_TEXT = re.compile(r"[A-Za-z0-9 _.,:;()'\"/$%=<>+{}\[\]!?#&*|~-]{0,600}")


def classify(exc: BaseException) -> str:
    """An allowlisted classification of a provider exception (never its text)."""

    from learnloop.ai.errors import AIInterrupted, AIInvalidOutput, AIOutputTruncated, AITurnTimeout

    names = {type(item).__name__ for item in _chain(exc)}
    status = status_code(exc)
    if isinstance(exc, AIOutputTruncated):
        return "truncated"
    if isinstance(exc, AIInterrupted):
        return "interrupted"
    if isinstance(exc, AIInvalidOutput) or "ValidationError" in names:
        return "invalid_output"
    if isinstance(exc, (AITurnTimeout, TimeoutError)) or any("Timeout" in name for name in names):
        return "timeout"
    if status in (401, 403) or any("Authentication" in name or "PermissionDenied" in name for name in names):
        return "auth"
    if status == 429 or any("RateLimit" in name for name in names):
        return "rate_limited"
    if "PinMismatch" in names:
        return "pin_mismatch"
    if any("Connection" in name for name in names):
        return "network"
    if "AdapterError" in names:
        return "contract"
    if names & {"AIProviderUnavailable", "CodexUnavailable"} or (status is not None and status >= 500):
        return "unavailable"
    return "unknown"


def _chain(exc: BaseException) -> list[BaseException]:
    seen: list[BaseException] = []
    current: BaseException | None = exc
    while current is not None and current not in seen and len(seen) < 8:
        seen.append(current)
        current = current.__cause__ or current.__context__
    return seen


def status_code(exc: BaseException) -> int | None:
    for item in _chain(exc):
        for name in ("status_code", "status", "http_status"):
            value = getattr(item, name, None)
            if isinstance(value, int) and not isinstance(value, bool) and 100 <= value <= 599:
                return value
        response = getattr(item, "response", None)
        value = getattr(response, "status_code", None)
        if isinstance(value, int) and not isinstance(value, bool) and 100 <= value <= 599:
            return value
    return None


def request_id(exc: BaseException) -> str | None:
    for item in _chain(exc):
        value = getattr(item, "request_id", None)
        if isinstance(value, str) and _SAFE_ID.fullmatch(value):
            return value
    return None


def provider_failure(exc: BaseException) -> E0ProviderFailure:
    """The sanitized stand-in for a provider exception (raise it ``from None``)."""

    return E0ProviderFailure(classify(exc), status_code=status_code(exc), request_id=request_id(exc))


def safe_message(exc: BaseException) -> str:
    """What an E0 command may print for a failure: an E0 stop's own message
    (built from allowlisted parts), else the exception's type name only."""

    if isinstance(exc, E0ProviderFailure):
        return str(exc)
    provider = any(type(item).__module__.startswith(("learnloop.ai", "openai", "httpx"))
                   for item in _chain(exc))
    ours = isinstance(exc, E0Stop | PermissionError | ValueError | FileNotFoundError) or type(
        exc).__module__.startswith("learnloop.experiments.contextual_embeddings")
    if ours and not provider:
        text = str(exc)
        if _SAFE_TEXT.fullmatch(text) and not _looks_secret(text):
            return text
    return f"{type(exc).__name__} (details suppressed)"


def _looks_secret(text: str) -> bool:
    """A credential shape: a provider key prefix, a bearer token, or a long token."""

    return bool(re.search(r"\b(?:sk|pk|pplx|pa|rk)-[A-Za-z0-9_-]{8,}|bearer\s+\S{8,}|[A-Za-z0-9_-]{32,}",
                          text, re.IGNORECASE))


class _Sanitize(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not record.name.startswith(PROVIDER_LOGGERS):
            return True
        kind = record.exc_info[0].__name__ if record.exc_info and record.exc_info[0] else None
        record.msg = "provider log record from %s suppressed by E0" + (" (%s)" if kind else "")
        record.args = (record.name, kind) if kind else (record.name,)
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        return True


_FILTER = _Sanitize()
_LOCK = threading.Lock()
_ACTIVE = {"depth": 0, "handlers": []}


@contextmanager
def quiet_provider_logs() -> Iterator[None]:
    """Sanitize provider log records at every handler while active (reentrant)."""

    with _LOCK:
        if _ACTIVE["depth"] == 0:
            handlers: list[Any] = list(logging.getLogger().handlers)
            for name in PROVIDER_LOGGERS:
                handlers.extend(logging.getLogger(name).handlers)
            for name, logger in list(logging.Logger.manager.loggerDict.items()):
                if isinstance(logger, logging.Logger) and name.startswith(PROVIDER_LOGGERS):
                    handlers.extend(logger.handlers)
            if logging.lastResort is not None:
                handlers.append(logging.lastResort)
            unique = list({id(handler): handler for handler in handlers}.values())
            for handler in unique:
                handler.addFilter(_FILTER)
            _ACTIVE["handlers"] = unique
        _ACTIVE["depth"] += 1
    try:
        yield
    finally:
        with _LOCK:
            _ACTIVE["depth"] -= 1
            if _ACTIVE["depth"] == 0:
                for handler in _ACTIVE["handlers"]:
                    handler.removeFilter(_FILTER)
                _ACTIVE["handlers"] = []


class CodexLockdownMissing(PermissionError):
    """The Codex tool lockdown is not in force: no E0 paid run starts."""


def require_codex_lockdown() -> dict[str, Any]:
    """Refuse the paid run unless every Codex turn is the locked-down one
    (security lockdown 55063be64): ``learnloop.ai.providers.codex_lockdown``
    must import, the Codex provider must use its ``TurnLockdown`` and approval
    path, and the isolated-turn overrides the provider launches every turn
    with must carry the lockdown's configuration, its command environment and
    every feature it switches off. E0's Codex roles (writer, contexts, both
    label passes, tutor, judges) all run isolated structured turns, so they
    go through this transport. Returns what was checked."""

    try:
        from learnloop.ai.providers import codex as provider
        from learnloop.ai.providers import codex_lockdown as lockdown
    except ImportError:
        raise CodexLockdownMissing("the Codex tool lockdown (codex_lockdown) is not importable; "
                                   "no E0 paid run starts") from None
    problems = []
    if getattr(provider, "TurnLockdown", None) is not lockdown.TurnLockdown:
        problems.append("the Codex provider does not use the lockdown's TurnLockdown")
    if not callable(getattr(getattr(provider, "SdkCodexClient", None), "_verified_isolated_overrides", None)):
        problems.append("the Codex provider has no verified (locked-down) isolated-turn launch")
    try:
        overrides = provider.isolated_turn_overrides(Path("."), shell=False)
    except Exception:  # noqa: BLE001 - an unreadable profile is no lockdown
        overrides = []
    required = [*lockdown.lockdown_config_overrides(), *lockdown.shell_environment_overrides(),
                *(f"features.{feature}=false" for feature in lockdown.disabled_features(shell=False))]
    missing = [item for item in required if item not in overrides]
    if missing:
        problems.append(f"{len(missing)} lockdown overrides are missing from the isolated turn")
    if problems:
        raise CodexLockdownMissing("the Codex tool lockdown is not active: " + "; ".join(problems))
    return {"codex_lockdown": "active", "overrides_checked": len(required)}


class CodexRoleRemaining(PermissionError):
    """An E0 role still bills a subscription (Codex) route: no paid run starts."""


def require_no_codex_roles(role_pins: Any = None) -> None:
    """Re-plan 2026-10-22: E0 makes NO Codex call. Every role pin must be a
    metered, non-Codex route (the paid ledger's Codex allowance is zero too)."""

    from learnloop.experiments.contextual_embeddings import pins

    remaining = sorted(name for name, pin in (role_pins or pins.ROLE_PINS).items()
                       if pin.billing == "subscription" or pin.transport == "codex_sdk")
    if remaining:
        raise CodexRoleRemaining("E0 roles still on Codex: " + ", ".join(remaining))

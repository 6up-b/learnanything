"""Request-scoped limits and durable call observations, without storage coupling.

An observer must durably accept a start before a paid request begins. A process
that disappears leaves an honest `started` receipt with unknown final usage.
Observers receive request text, schema, hashes and returned text for replay and
failure analysis. Provider credentials and inline media payloads are excluded.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from functools import wraps
import hashlib
import json
import logging
from typing import Any, Callable, Protocol
from uuid import uuid4

from learnloop.ai.errors import AIInterrupted, AIOutputTruncated

logger = logging.getLogger(__name__)

_observer: ContextVar[Callable[[str, dict[str, Any]], Any] | None] = ContextVar("model_observer", default=None)
_parent: ContextVar[str | None] = ContextVar("model_call_parent", default=None)
_output_limit: ContextVar[int | None] = ContextVar("model_output_limit", default=None)
_metadata: ContextVar[dict[str, Any] | None] = ContextVar("model_call_metadata", default=None)


def report_call_usage(values: dict[str, Any]) -> None:
    metadata = _metadata.get()
    if metadata is not None:
        for key, value in values.items():
            if key in {"input_tokens", "output_tokens", "cached_input_tokens", "cache_write_tokens", "reasoning_tokens", "cost"} and value is not None:
                metadata[key] = (metadata.get(key) or 0) + value
            else:
                metadata[key] = value


def content_key(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def model_settings(client: Any) -> dict[str, Any]:
    """The client settings that change what a request produces.

    Checkpoint keys include these so that switching the endpoint, reasoning
    effort, thinking mode or response format never replays output produced
    under different settings. Clients expose their settings either as an
    ``AIProviderConfig`` (``profile``) or a ``CodexConfig`` (``config``).
    """

    profile = getattr(client, "profile", None) or getattr(client, "config", None)
    return {
        "provider": getattr(client, "provider_name", None) or getattr(client, "provider_type", None),
        "model": getattr(client, "model", None) or getattr(profile, "model", None),
        "endpoint": getattr(profile, "base_url", None) or getattr(client, "default_base_url", None),
        "reasoning_effort": getattr(profile, "reasoning_effort", None),
        "thinking": getattr(profile, "thinking", None),
        "response_format": getattr(profile, "response_format", None),
    }


@contextmanager
def observe_model_calls(observer: Callable[[str, dict[str, Any]], Any]):
    token = _observer.set(observer)
    try:
        yield
    finally:
        _observer.reset(token)


class ModelEventStore(Protocol):
    def record_model_event(self, action: str, event: dict[str, Any], *, owner_kind: str, owner_id: str) -> None:
        ...


def record_model_calls(store: ModelEventStore, *, owner_kind: str, owner_id: str):
    """Observe every model call in this context into ``store`` under one owner.

    ``store`` is usually a ``Repository``; the owner names the unit of work
    (a sidecar request, a CLI command, a TUI session) whose calls these are.
    """

    return observe_model_calls(
        lambda action, event: store.record_model_event(action, event, owner_kind=owner_kind, owner_id=owner_id)
    )


@contextmanager
def generation_limit(output_tokens: int | None):
    if output_tokens is not None and output_tokens <= 0:
        raise ValueError("No output token budget remains")
    existing = _output_limit.get()
    limit = min(existing, output_tokens) if existing is not None and output_tokens is not None else (existing if output_tokens is None else output_tokens)
    token = _output_limit.set(limit)
    try:
        yield
    finally:
        _output_limit.reset(token)


def output_limit() -> int | None:
    return _output_limit.get()


def observed_sdk_turn(function):
    @wraps(function)
    def wrapped(client, prompt, output_schema, *, purpose, **kwargs):
        with model_call(client, purpose=f"{purpose}:sdk_turn", prompt=prompt, schema=output_schema, budget=output_limit()) as metadata:
            result = function(client, prompt, output_schema, purpose=purpose, **kwargs)
            metadata["output_text"] = result
            return result
    return wrapped


@contextmanager
def model_call(client: Any, *, purpose: str, prompt: Any = None, schema: Any = None, budget: int | None = None):
    observer = _observer.get()
    metadata: dict[str, Any] = {}
    if observer is None:
        yield metadata
        return
    call_id = f"call_{uuid4().hex}"
    profile = getattr(client, "profile", None) or getattr(client, "config", None)
    observer("start", {
        "id": call_id, "parent_call_id": _parent.get(), "purpose": purpose,
        "provider": getattr(client, "provider_name", None), "model": getattr(client, "model", None) or getattr(profile, "model", None),
        "endpoint": getattr(profile, "base_url", None) or getattr(client, "default_base_url", None),
        "prompt_hash": content_key(prompt), "schema_hash": content_key(schema),
        "input_text": prompt if isinstance(prompt, str) and _parent.get() is None else None,
        "schema_json": json.dumps(schema, sort_keys=True) if _parent.get() is None else None,
        "output_budget_tokens": budget, "started_at": datetime.now(timezone.utc).isoformat(),
    })
    token = _parent.set(call_id)
    metadata_token = _metadata.set(metadata)
    try:
        yield metadata
    except BaseException as exc:
        metadata.update(status=_failure_status(exc), error_type=type(exc).__name__)
        raise
    else:
        # A caller that handles a request failure itself (to classify it for
        # retry) records status "failed" on the metadata and exits normally.
        metadata.setdefault("status", "completed")
    finally:
        _parent.reset(token)
        _metadata.reset(metadata_token)
        _record_finish(observer, call_id, metadata)


def _failure_status(exc: BaseException) -> str:
    if isinstance(exc, AIOutputTruncated):
        return "truncated"
    if isinstance(exc, (AIInterrupted, KeyboardInterrupt)):
        return "interrupted"
    return "failed"


def _record_finish(observer: Callable[[str, dict[str, Any]], Any], call_id: str, metadata: dict[str, Any]) -> None:
    """Best-effort: the durable start is the safety guarantee, the finish is telemetry.

    Raising here would discard a response that was already paid for, or replace
    the call's own exception with a storage error. The receipt stays
    ``started`` with unknown usage, which is the honest record of a lost finish.
    """

    try:
        observer("finish", {"id": call_id, "finished_at": datetime.now(timezone.utc).isoformat(), **metadata})
    except Exception:
        logger.exception("Could not record the outcome of model call %s; its receipt stays 'started'", call_id)

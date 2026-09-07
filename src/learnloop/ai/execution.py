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
import hashlib
import json
from typing import Any, Callable
from uuid import uuid4
from functools import wraps

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


@contextmanager
def observe_model_calls(observer: Callable[[str, dict[str, Any]], Any]):
    token = _observer.set(observer)
    try:
        yield
    finally:
        _observer.reset(token)


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
        from learnloop.ai.errors import AIInterrupted, AIOutputTruncated
        metadata.update(status="truncated" if isinstance(exc, AIOutputTruncated) else "interrupted" if isinstance(exc, (AIInterrupted, KeyboardInterrupt)) else "failed", error_type=type(exc).__name__)
        raise
    else:
        metadata["status"] = "completed"
    finally:
        _parent.reset(token)
        _metadata.reset(metadata_token)
        observer("finish", {"id": call_id, "finished_at": datetime.now(timezone.utc).isoformat(), **metadata})

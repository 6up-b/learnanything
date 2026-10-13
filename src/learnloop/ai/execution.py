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
_budgets: ContextVar[dict[str, Any] | None] = ContextVar("model_call_budgets", default=None)
_single_request: ContextVar[bool] = ContextVar("model_single_request", default=False)
_labels: ContextVar[dict[str, str] | None] = ContextVar("model_call_labels", default=None)
_annotations: ContextVar[dict[str, Any] | None] = ContextVar("model_call_annotations", default=None)
_reasoning_effort: ContextVar[str | None] = ContextVar("model_reasoning_effort", default=None)
_truncation_retry: ContextVar[bool] = ContextVar("model_truncation_retry", default=False)

#: Receipt labels a caller may attach to the calls in its context (router
#: spec §6.2): which judge answered, the versioned question set, and the hash
#: of the state it was given. Unknown labels are refused, never stored.
CALL_LABELS = frozenset({"judge", "question_set_version", "state_hash"})
JUDGE_LABELS = frozenset({"decider", "llm"})


@contextmanager
def call_labels(**labels: str | None):
    """Label every model call started in this context on its receipt.

    ``judge`` is ``decider`` or ``llm``. Labels nest: an inner context adds to
    or replaces the outer one's values.
    """

    unknown = set(labels) - CALL_LABELS
    if unknown:
        raise ValueError(f"Unknown receipt labels: {', '.join(sorted(unknown))}")
    judge = labels.get("judge")
    if judge is not None and judge not in JUDGE_LABELS:
        raise ValueError(f"judge must be one of {sorted(JUDGE_LABELS)}")
    merged = {**(_labels.get() or {}), **{k: v for k, v in labels.items() if v is not None}}
    token = _labels.set(merged)
    try:
        yield
    finally:
        _labels.reset(token)


@contextmanager
def single_request():
    """Disable hidden paid retries/repairs for a caller-budgeted transport call.

    Wrap exactly one ``complete`` invocation per budget authorization. This is
    a transport policy, not a spend meter or a limit on caller-authored calls.
    Transports unable to bound their internal physical attempts must fail closed.
    Context-local state is restored even on failure and supports nested scopes.
    """

    token = _single_request.set(True)
    try:
        yield
    finally:
        _single_request.reset(token)


def single_request_active() -> bool:
    return _single_request.get()


@contextmanager
def annotate_calls(**notes: Any):
    """Add ``notes`` to the ``budget_json`` of every root receipt started here.

    Used for facts about why a request was sent, such as a truncation retry at
    double the output budget (``learnloop.ai.output_budget``). Notes nest.
    """

    merged = {**(_annotations.get() or {}), **notes}
    token = _annotations.set(merged)
    try:
        yield
    finally:
        _annotations.reset(token)


@contextmanager
def requested_reasoning_effort(effort: str | None):
    """Ask every request started here for ``effort`` (None keeps the profile's).

    A transport that supports a reasoning effort sends it (OpenRouter's
    ``reasoning.effort``, the Codex turn effort); others ignore it. The route
    owner resolves it from ``ai.route_reasoning_effort``.
    """

    token = _reasoning_effort.set(effort or None)
    try:
        yield
    finally:
        _reasoning_effort.reset(token)


def reasoning_effort_request() -> str | None:
    return _reasoning_effort.get()


@contextmanager
def truncation_retry_allowed():
    """Let the transport retry a truncated answer once at double the budget.

    For callers that admit every physical request as it starts (Slice 1's
    ``ReviewSpend``, the project probes) and so can pay for a retry the
    transport makes. Callers that own the retry (``single_request``) and
    owner-set budgets (``[ingest.budgets]``) never set it: there a truncation
    is raised, logged, and never answered past the budget.
    """

    token = _truncation_retry.set(True)
    try:
        yield
    finally:
        _truncation_retry.reset(token)


def truncation_retry_permitted() -> bool:
    return _truncation_retry.get()


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
def declared_budgets(budgets: dict[str, Any]):
    """Record the token budgets an operation runs under on its root receipts.

    Budgets can be overridden per request, so the vault's configuration at
    report time is not evidence of the budgets a past run was held to.
    """

    token = _budgets.set(dict(budgets))
    try:
        yield
    finally:
        _budgets.reset(token)


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
    is_root = _parent.get() is None
    budgets = _budgets.get()
    annotations = _annotations.get()
    if annotations:
        budgets = {**(budgets or {}), **annotations}
    observer("start", {
        "id": call_id, "parent_call_id": _parent.get(), "purpose": purpose,
        "provider": getattr(client, "provider_name", None), "model": getattr(client, "model", None) or getattr(profile, "model", None),
        "endpoint": getattr(profile, "base_url", None) or getattr(client, "default_base_url", None),
        "prompt_hash": content_key(prompt), "schema_hash": content_key(schema),
        "input_text": prompt if isinstance(prompt, str) and is_root else None,
        "schema_json": json.dumps(schema, sort_keys=True) if is_root else None,
        "budget_json": json.dumps(budgets, sort_keys=True) if is_root and budgets is not None else None,
        "output_budget_tokens": budget, "started_at": datetime.now(timezone.utc).isoformat(),
        **(_labels.get() or {}),
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

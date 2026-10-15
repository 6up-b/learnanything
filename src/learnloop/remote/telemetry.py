"""Every chat tool call in the existing ledgers (spec_mcp_frontend_c1 §5).

One ``interaction_events`` row per MCP tool call (migration 203): kind
``chat_tool_call``, origin ``chat_host`` (a host model acting in the learner's
chat), the surface ``chat_mcp``, the host (``claude`` | ``chatgpt`` |
``unknown``, from the request), the tool, a hash of its arguments and of its
result, the result's counts, the learning objects it touched and the exposure
rows it wrote. The row is written before the result is returned: a call that
cannot be recorded returns an error instead (everything the chat side does is
in the ledger).

Passages a chat tool shows are exposure exactly as in the Reader: one
``source_exposure_events`` row per span (``instructional.interventions.
record_shown_spans``, the rule every surface follows), with
``entity_type = 'chat_tool_call'`` and the call's id. The exposure rule, the
coldness receipts and the Reader's progress read those rows whatever their
surface.

Rows of this kind are salience-only (``authority_class``): telemetry, never
learner evidence. Replay never reads them as observations.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from learnloop.attempts.salience_firewall import salience_payload
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository

CHAT_TOOL_CALL_KIND = "chat_tool_call"
CHAT_HOST_ORIGIN = "chat_host"
CHAT_SURFACE = "chat_mcp"
CHAT_EXPOSURE_ENTITY = "chat_tool_call"
#: ``source_exposure_events.context`` for passages a chat tool showed: the
#: library's (the passages came from a library ``find_sources`` call; the
#: surface is named by ``entity_type``).
CHAT_EXPOSURE_CONTEXT = "library"
HOSTS = ("claude", "chatgpt", "unknown")
TRANSPORTS = ("streamable_http", "stdio", "in_process")
PAYLOAD_SCHEMA_VERSION = "chat-tool-call-v1"
ACTOR = "chat_host_model"


def canonical_hash(value: Any) -> str:
    text = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CallOrigin:
    """Where a call came from, read from the request (hints only: never authority)."""

    host: str = "unknown"
    transport: str = "in_process"
    host_signal: str = "none"

    def __post_init__(self) -> None:
        if self.host not in HOSTS:
            object.__setattr__(self, "host", "unknown")
        if self.transport not in TRANSPORTS:
            object.__setattr__(self, "transport", "in_process")


def record_shown_passages(repository: Repository, keys: Sequence[str], *, call_id: str,
                          source_versions: Mapping[str, Any] | None = None,
                          clock: Clock | None = None) -> list[str]:
    """Exposure first, always: one row per span a chat tool is about to show."""

    from learnloop.instructional.interventions import record_shown_spans

    return record_shown_spans(repository, list(keys), context=CHAT_EXPOSURE_CONTEXT,
                              entity_type=CHAT_EXPOSURE_ENTITY, entity_id=call_id,
                              source_versions=source_versions, clock=clock)


def record_tool_call(
    repository: Repository,
    *,
    call_id: str,
    tool: str,
    origin: CallOrigin,
    arguments: Mapping[str, Any],
    result: Any,
    status: str,
    summary: Mapping[str, Any] | None = None,
    error_code: str | None = None,
    duration_ms: int | None = None,
    learning_object_ids: Sequence[str] = (),
    exposure_event_ids: Sequence[str] = (),
    algorithm_version: str | None = None,
    adapter_version: str | None = None,
    started_at: str | None = None,
    clock: Clock | None = None,
) -> str:
    """The call's ``interaction_events`` row (its id)."""

    payload = salience_payload({
        "surface": CHAT_SURFACE,
        "host": origin.host,
        "host_signal": origin.host_signal,
        "transport": origin.transport,
        "tool": tool,
        "call_id": call_id,
        "status": status,
        "error_code": error_code,
        "arguments_hash": canonical_hash(arguments),
        "result_hash": canonical_hash(result) if result is not None else None,
        "summary": dict(summary or {}),
        "learning_object_ids": sorted(set(learning_object_ids))[:50],
        "exposure_event_ids": list(exposure_event_ids)[:100],
        "duration_ms": duration_ms,
    })
    payload_json = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    now = utc_now_iso(clock)
    return repository.append_interaction_event(
        kind=CHAT_TOOL_CALL_KIND,
        origin=CHAT_HOST_ORIGIN,
        subject_type="mcp_tool",
        subject_id=tool,
        payload_json=payload_json,
        occurred_at=started_at or now,
        received_at=started_at or now,
        actor=ACTOR,
        client_id=origin.host,
        payload_schema_version=PAYLOAD_SCHEMA_VERSION,
        payload_hash=canonical_hash(payload),
        client_idempotency_key=f"{CHAT_SURFACE}:{call_id}",
        privacy_locality="local_private",
        consent_context="owner_connector",
        producer_version=adapter_version,
        policy_version=algorithm_version,
        clock=clock,
    )


def chat_activity(repository: Repository, *, days: int = 7, limit: int = 20,
                  clock: Clock | None = None) -> dict[str, Any]:
    """What the chat frontend did in the last ``days`` days (read-only)."""

    now = (clock.now() if clock is not None else datetime.now(UTC)).astimezone(UTC)
    since = (now - timedelta(days=max(int(days), 0))).strftime("%Y-%m-%dT%H:%M:%SZ")
    events = repository.reader_interaction_events(kind=CHAT_TOOL_CALL_KIND, since=since)
    by_tool: Counter[str] = Counter()
    by_host: Counter[str] = Counter()
    by_status: Counter[str] = Counter()
    by_day: Counter[str] = Counter()
    touched: Counter[str] = Counter()
    calls: list[dict[str, Any]] = []
    for event in events:
        payload = event.get("payload") or {}
        by_tool[str(payload.get("tool") or event.get("subject_id"))] += 1
        by_host[str(payload.get("host") or event.get("client_id") or "unknown")] += 1
        by_status[str(payload.get("status") or "unknown")] += 1
        by_day[str(event.get("created_at") or "")[:10]] += 1
        for lo in payload.get("learning_object_ids") or ():
            touched[str(lo)] += 1
        calls.append({
            "at": event.get("created_at"), "host": payload.get("host"), "tool": payload.get("tool"),
            "status": payload.get("status"), "error_code": payload.get("error_code"),
            "summary": payload.get("summary") or {}, "transport": payload.get("transport"),
            "passages_shown": len(payload.get("exposure_event_ids") or ()),
        })
    exposures = repository.source_exposure_events(entity_type=CHAT_EXPOSURE_ENTITY, after=since)
    return {
        "since": since,
        "as_of": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "calls": len(events),
        "by_tool": dict(sorted(by_tool.items())),
        "by_host": dict(sorted(by_host.items())),
        "by_status": dict(sorted(by_status.items())),
        "by_day": dict(sorted(by_day.items())),
        "learning_objects_touched": dict(touched.most_common(20)),
        "passages_shown": len(exposures),
        "sources_shown": len({str(row.get("source_id") or row.get("extraction_id")) for row in exposures}),
        "recent": list(reversed(calls))[: max(int(limit), 0)],
    }


__all__ = [
    "ACTOR",
    "CHAT_EXPOSURE_CONTEXT",
    "CHAT_EXPOSURE_ENTITY",
    "CHAT_HOST_ORIGIN",
    "CHAT_SURFACE",
    "CHAT_TOOL_CALL_KIND",
    "CallOrigin",
    "HOSTS",
    "PAYLOAD_SCHEMA_VERSION",
    "canonical_hash",
    "chat_activity",
    "record_shown_passages",
    "record_tool_call",
]

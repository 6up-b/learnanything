"""Which chat host made a call, from the request (spec_mcp_frontend_c1 §5.1).

A label for telemetry only: never an authorization decision. Signals, in
order: the ``Origin`` header (``https://claude.ai``, ``https://chatgpt.com``),
the ``User-Agent``, OpenAI's ``openai/*`` request metadata, and the client
name the host gave at initialization. Anything else is ``unknown``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from learnloop.remote.telemetry import CallOrigin

_CLAUDE = ("claude", "anthropic")
_CHATGPT = ("chatgpt", "openai")


def _classify(text: str) -> str | None:
    value = text.lower()
    if any(token in value for token in _CLAUDE):
        return "claude"
    if any(token in value for token in _CHATGPT):
        return "chatgpt"
    return None


def detect_host(headers: Mapping[str, str] | None, *, meta: Any = None, client_name: str | None = None,
                transport: str = "in_process") -> CallOrigin:
    lowered = {str(key).lower(): str(value) for key, value in (headers or {}).items()}
    origin = lowered.get("origin", "")
    if origin:
        host = _classify(origin)
        if host:
            return CallOrigin(host=host, transport=transport, host_signal="origin_header")
    agent = lowered.get("user-agent", "")
    if agent:
        host = _classify(agent)
        if host:
            return CallOrigin(host=host, transport=transport, host_signal="user_agent")
    keys: list[str] = []
    if isinstance(meta, Mapping):
        keys = [str(key) for key in meta]
    elif meta is not None:
        dumped = getattr(meta, "model_dump", None)
        if callable(dumped):
            try:
                keys = [str(key) for key in dumped(by_alias=True, exclude_none=True)]
            except Exception:  # noqa: BLE001 - a hint only
                keys = []
        extra = getattr(meta, "model_extra", None) or {}
        keys += [str(key) for key in extra]
    if any(key.startswith("openai/") for key in keys):
        return CallOrigin(host="chatgpt", transport=transport, host_signal="request_meta")
    if client_name:
        host = _classify(client_name)
        if host:
            return CallOrigin(host=host, transport=transport, host_signal="client_info")
    return CallOrigin(host="unknown", transport=transport, host_signal="none")


__all__ = ["detect_host"]

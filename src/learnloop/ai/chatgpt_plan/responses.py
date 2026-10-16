"""One streamed Responses API request on the ChatGPT plan.

Pinned from developers.openai.com/siwc (models-and-inference,
preview-limitations, errors-and-recovery; re-verified 2026-10-12):

* ``POST {base_url}/responses`` with ``Authorization: Bearer <access token>``
  and ``store: false``, ``stream: true``. The prompt goes in ``input``; the
  system turn is ``instructions`` (``role: system`` items are rejected).
* Never sent: ``background``, ``conversation``, ``max_output_tokens``,
  ``max_tool_calls``, ``metadata``, ``moderation``, ``multi_agent``,
  ``prompt``, ``prompt_cache_retention``, ``safety_identifier``,
  ``temperature``, ``top_logprobs``, ``top_p``, ``truncation``, ``user``,
  ``previous_response_id`` (and LearnLoop's own ``tool_choice``).
* Tools (re-read 2026-10-15): function tools only, grouped in a namespace
  (``{"type": "namespace", "name", "description", "tools": [functions]}``);
  hosted tools (file search, code interpreter, image generation, computer
  use, hosted MCP, ``tool_search``) are unsupported. LearnLoop declares tools
  only on a read-only-workspace turn (``learnloop.ai.chatgpt_plan.workspace``).
  With ``store: false`` and no ``previous_response_id``, each round resends
  the whole history in ``input``: the model's reasoning items (requested with
  ``include: ["reasoning.encrypted_content"]``, so they need no stored id),
  its function calls, and LearnLoop's ``function_call_output`` items.
* Success is only ``response.completed``. ``response.failed`` (usage limits
  can arrive mid-stream), ``response.incomplete``, ``error`` events and a
  stream that ends early are failures. Before a stream opens, an error body
  may be the standard ``{"error": {...}}`` object or ``{"detail": "..."}``;
  the HTTP status, code, ``param`` and request id are kept.

The connection is ``http.client`` so a deadline or an interrupt can shut the
socket down from another thread, which wakes a blocked read at once.
"""
from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field
import http.client
import json
import socket
import ssl
import threading
import time
from typing import Any
import urllib.parse

#: Body fields the ChatGPT-plan route rejects (preview-limitations), plus
#: ``tool_choice``, which LearnLoop never sends. Kept as data so a test can
#: assert none is ever sent.
UNSUPPORTED_FIELDS = frozenset({
    "background", "conversation", "max_output_tokens", "max_tool_calls", "metadata", "moderation",
    "multi_agent", "prompt", "prompt_cache_retention", "safety_identifier", "temperature",
    "top_logprobs", "top_p", "truncation", "user", "previous_response_id", "tool_choice",
})
#: What a tool round asks to be returned so its reasoning can be resent with
#: ``store: false`` (an item id alone names nothing stored).
REASONING_INCLUDE = "reasoning.encrypted_content"
#: Output item types a tool round resends as input, and the fields kept of
#: each: ids and statuses are dropped (with ``store: false`` an id names
#: nothing the server kept). A reasoning item travels as its
#: ``encrypted_content`` (the state) and its ``summary`` (a required field);
#: its raw ``content`` is never resent.
_ECHOED_FIELDS = {
    "reasoning": ("type", "summary", "encrypted_content"),
    "function_call": ("type", "call_id", "name", "namespace", "arguments"),
    "message": ("type", "role", "content"),
}
_ERROR_TEXT_LIMIT = 300


class ResponsesError(Exception):
    """The request failed; ``code`` and ``param`` are the API's when it sent them."""

    def __init__(self, message: str, *, status: int | None, code: str | None = None, param: str | None = None,
                 request_id: str | None = None, response: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.param = param
        self.request_id = request_id
        self.response = dict(response) if isinstance(response, Mapping) else None


class StreamCancelled(Exception):
    """The deadline passed or the caller interrupted; ``reason`` says which."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class StreamIncomplete(Exception):
    def __init__(self, reason: str | None, response: Mapping[str, Any]) -> None:
        super().__init__(reason or "incomplete")
        self.reason = reason
        self.response = dict(response)


@dataclass
class StreamResult:
    response: dict[str, Any]
    text: str
    request_id: str | None
    status: int
    seconds_to_headers: float
    seconds_to_first_event: float | None
    seconds_total: float
    events: int = 0
    refusal: str | None = None
    event_types: list[str] = field(default_factory=list)
    #: ``response.output_item.done`` items in stream order: the fallback when
    #: the terminal response carries no ``output``.
    output_items: list[dict[str, Any]] = field(default_factory=list)

    @property
    def output(self) -> list[dict[str, Any]]:
        """The response's output items (the terminal response's, else the streamed ones)."""

        items = self.response.get("output")
        if isinstance(items, list) and items:
            return [dict(item) for item in items if isinstance(item, Mapping)]
        return list(self.output_items)


def request_body(
    *, model: str, instructions: str, prompt: str | None = None, text_format: Mapping[str, Any] | None,
    reasoning_effort: str | None = None, input_items: list[Mapping[str, Any]] | None = None,
    tools: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """One request body. ``input_items`` (a tool round's whole history) replaces ``prompt``."""

    if (prompt is None) == (input_items is None):
        raise ValueError("pass exactly one of prompt and input_items")
    body: dict[str, Any] = {
        "model": model,
        "instructions": instructions,
        "input": [dict(item) for item in input_items] if input_items is not None
        else [{"role": "user", "content": prompt}],
        "store": False,
        "stream": True,
    }
    if text_format is not None:
        body["text"] = {"format": dict(text_format)}
    if reasoning_effort:
        body["reasoning"] = {"effort": reasoning_effort}
    if tools:
        validate_tools(tools)
        body["tools"] = [dict(tool) for tool in tools]
        body["include"] = [REASONING_INCLUDE]
    return body


def validate_tools(tools: list[Mapping[str, Any]]) -> None:
    """The plan route takes function tools grouped in namespaces, and nothing hosted."""

    for tool in tools:
        if not isinstance(tool, Mapping) or tool.get("type") != "namespace" or not tool.get("name"):
            raise ValueError("the ChatGPT plan takes function tools only inside a namespace")
        functions = tool.get("tools")
        if not isinstance(functions, list) or not functions:
            raise ValueError(f"namespace {tool.get('name')!r} declares no functions")
        for function in functions:
            if not isinstance(function, Mapping) or function.get("type") != "function" or not function.get("name"):
                raise ValueError(f"namespace {tool.get('name')!r} may hold function tools only")


def function_calls(output: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """The ``function_call`` items of a response's output, in order."""

    return [dict(item) for item in output if isinstance(item, Mapping) and item.get("type") == "function_call"]


def echo_items(output: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """A tool round's output as the next request's input (see :data:`_ECHOED_FIELDS`).

    A reasoning item without ``encrypted_content`` cannot be resent with
    ``store: false`` and is dropped; any other item type is not resent.
    """

    echoed = []
    for item in output:
        if not isinstance(item, Mapping):
            continue
        fields = _ECHOED_FIELDS.get(str(item.get("type")))
        if fields is None:
            continue
        if item.get("type") == "reasoning" and not item.get("encrypted_content"):
            continue
        kept = {key: item[key] for key in fields if item.get(key) is not None}
        if kept["type"] == "reasoning":
            kept.setdefault("summary", [])
        echoed.append(kept)
    return echoed


def iter_sse(readline: Callable[[], bytes]) -> Iterator[tuple[str | None, str]]:
    """``(event name, data)`` per server-sent event (the WHATWG framing)."""

    event: str | None = None
    data: list[str] = []
    while True:
        raw = readline()
        if not raw:
            if data:
                yield event, "\n".join(data)
            return
        line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
        if not line:
            if data:
                yield event, "\n".join(data)
            event, data = None, []
            continue
        if line.startswith(":"):
            continue
        name, _, value = line.partition(":")
        value = value[1:] if value.startswith(" ") else value
        if name == "event":
            event = value
        elif name == "data":
            data.append(value)


def output_text(response: Mapping[str, Any]) -> tuple[str, str | None]:
    """``(text, refusal)`` from a terminal response's ``output`` items."""

    texts: list[str] = []
    refusals: list[str] = []
    for item in response.get("output") or []:
        if not isinstance(item, Mapping) or item.get("type") != "message":
            continue
        for part in item.get("content") or []:
            if not isinstance(part, Mapping):
                continue
            if part.get("type") == "output_text" and isinstance(part.get("text"), str):
                texts.append(part["text"])
            elif part.get("type") == "refusal" and isinstance(part.get("refusal"), str):
                refusals.append(part["refusal"])
    return "".join(texts), ("\n".join(refusals) or None)


def error_fields(payload: Any) -> tuple[str | None, str | None, str | None]:
    """``(code, message, param)`` from an error object, an error event or ``{"detail": ...}``."""

    if not isinstance(payload, Mapping):
        return None, None, None
    error = payload.get("error")
    if isinstance(error, Mapping):
        return _str(error.get("code") or error.get("type")), _str(error.get("message")), _str(error.get("param"))
    if payload.get("type") == "error" or "code" in payload:
        return _str(payload.get("code")), _str(payload.get("message")), _str(payload.get("param"))
    detail = payload.get("detail")
    if detail is not None:
        return None, _str(detail if isinstance(detail, str) else json.dumps(detail)), None
    return None, None, None


def _str(value: Any) -> str | None:
    return None if value is None else str(value)[:_ERROR_TEXT_LIMIT]


def _request_id(headers: Mapping[str, str] | http.client.HTTPMessage) -> str | None:
    for name in ("x-request-id", "openai-request-id", "request-id"):
        value = headers.get(name)
        if value:
            return str(value)[:120]
    return None


class ResponsesStream:
    """One request, one connection; ``cancel()`` shuts it down from any thread."""

    def __init__(self, base_url: str) -> None:
        parts = urllib.parse.urlsplit(base_url.rstrip("/"))
        if parts.scheme not in {"https", "http"} or not parts.hostname:
            raise ValueError(f"Unsupported base URL {base_url!r}")
        self._scheme = parts.scheme
        self._host = parts.hostname
        self._port = parts.port
        self._path = (parts.path or "") + "/responses"
        self._connection: http.client.HTTPConnection | None = None
        self._lock = threading.Lock()
        self._cancel_reason: str | None = None

    def cancel(self, reason: str) -> None:
        with self._lock:
            if self._cancel_reason is None:
                self._cancel_reason = reason
            connection = self._connection
        sock = getattr(connection, "sock", None) if connection is not None else None
        if sock is not None:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    def _raise_if_cancelled(self) -> None:
        if self._cancel_reason is not None:
            raise StreamCancelled(self._cancel_reason)

    def send(self, body: Mapping[str, Any], *, access_token: str, timeout: float,
             on_event: Callable[[str, Mapping[str, Any]], None] | None = None) -> StreamResult:
        started = time.monotonic()
        if timeout <= 0:
            # A spent deadline is never stretched into a request.
            raise StreamCancelled("deadline")
        encoded = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        connection_class = http.client.HTTPSConnection if self._scheme == "https" else http.client.HTTPConnection
        kwargs: dict[str, Any] = {"timeout": max(0.5, timeout)}
        if self._scheme == "https":
            kwargs["context"] = ssl.create_default_context()
        connection = connection_class(self._host, self._port, **kwargs)
        with self._lock:
            self._connection = connection
        self._raise_if_cancelled()
        timer = threading.Timer(max(0.0, timeout), self.cancel, args=("deadline",))
        timer.daemon = True
        timer.start()
        try:
            try:
                connection.request("POST", self._path, body=encoded, headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                    "User-Agent": "LearnLoop",
                })
                response = connection.getresponse()
            except (OSError, http.client.HTTPException) as exc:
                self._raise_if_cancelled()
                raise ResponsesError(f"The Responses endpoint could not be reached ({type(exc).__name__}).",
                                     status=None) from None
            headers_at = time.monotonic() - started
            request_id = _request_id(response.headers)
            if response.status != 200:
                try:
                    raw = response.read()
                except (OSError, http.client.HTTPException):
                    raw = b""
                try:
                    payload = json.loads(raw.decode("utf-8")) if raw else {}
                except (UnicodeDecodeError, ValueError):
                    payload = {}
                code, message, param = error_fields(payload)
                raise ResponsesError(
                    message or f"HTTP {response.status}", status=response.status, code=code, param=param,
                    request_id=request_id,
                )
            return self._read_stream(response, request_id=request_id, started=started,
                                     headers_at=headers_at, on_event=on_event)
        except (OSError, http.client.HTTPException) as exc:
            self._raise_if_cancelled()
            raise ResponsesError(f"The response stream broke ({type(exc).__name__}).", status=200) from None
        finally:
            timer.cancel()
            with self._lock:
                self._connection = None
            connection.close()

    def _read_stream(self, response: http.client.HTTPResponse, *, request_id: str | None, started: float,
                     headers_at: float, on_event: Callable[[str, Mapping[str, Any]], None] | None) -> StreamResult:
        deltas: list[str] = []
        items: list[dict[str, Any]] = []
        first_event: float | None = None
        count = 0
        types: list[str] = []
        for name, data in iter_sse(response.readline):
            self._raise_if_cancelled()
            if data.strip() == "[DONE]":
                break
            try:
                event = json.loads(data)
            except ValueError:
                continue
            if not isinstance(event, Mapping):
                continue
            kind = str(event.get("type") or name or "")
            count += 1
            if first_event is None:
                first_event = time.monotonic() - started
            if kind not in types:
                types.append(kind)
            if on_event is not None:
                on_event(kind, event)
            if kind == "response.output_text.delta" and isinstance(event.get("delta"), str):
                deltas.append(event["delta"])
            elif kind == "response.output_item.done" and isinstance(event.get("item"), Mapping):
                items.append(dict(event["item"]))
            elif kind == "response.completed":
                final = event.get("response") if isinstance(event.get("response"), Mapping) else {}
                text, refusal = output_text(final if final.get("output") else {"output": items})
                return StreamResult(
                    response=dict(final), text=text or "".join(deltas), request_id=request_id, status=200,
                    seconds_to_headers=headers_at, seconds_to_first_event=first_event,
                    seconds_total=time.monotonic() - started, events=count, refusal=refusal, event_types=types,
                    output_items=items,
                )
            elif kind == "response.failed":
                final = event.get("response") if isinstance(event.get("response"), Mapping) else {}
                code, message, param = error_fields(final)
                raise ResponsesError(message or "response.failed", status=200, code=code, param=param,
                                     request_id=request_id, response=final)
            elif kind == "response.incomplete":
                final = event.get("response") if isinstance(event.get("response"), Mapping) else {}
                details = final.get("incomplete_details") if isinstance(final.get("incomplete_details"), Mapping) else {}
                raise StreamIncomplete(_str(details.get("reason")), final)
            elif kind == "error":
                code, message, param = error_fields(event)
                raise ResponsesError(message or "error event", status=200, code=code, param=param,
                                     request_id=request_id)
        self._raise_if_cancelled()
        raise ResponsesError("The response stream ended before response.completed.", status=200,
                             code="stream_ended", request_id=request_id)


__all__ = [
    "REASONING_INCLUDE",
    "ResponsesError",
    "ResponsesStream",
    "StreamCancelled",
    "StreamIncomplete",
    "StreamResult",
    "UNSUPPORTED_FIELDS",
    "echo_items",
    "error_fields",
    "function_calls",
    "iter_sse",
    "output_text",
    "request_body",
    "validate_tools",
]

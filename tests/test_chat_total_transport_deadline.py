"""Reader follow-ups (Nov 1), item 4: an enforced TOTAL transport deadline in the
OpenAI-compatible chat adapter. Closes RW6b part 2's open item 1 (final verify F3,
ruling R3: "an abortable total transport deadline is an open item for the AI
transport layer"; ``docs/reviews/reader-rw6b-p2-digest-card.md``).

The SDK's ``timeout`` is httpx's per network operation, so a server that dribbles
bytes held a request open past it. Now each physical request is over, from the
caller's side, when its total deadline is: the request is aborted (its response
stream closed) and the attempt fails. reader_digest's narration lease is that
enforced bound plus the claims' liveness margin.

Everything runs through the real adapter and the real ``openai`` SDK over an
in-memory httpx transport: nothing leaves the machine.
"""
from __future__ import annotations

import json
import math
import threading
import time
from typing import Any

import httpx
import pytest

from learnloop.ai.errors import CodexUnavailable
from learnloop.ai.providers import openai_chat as OC
from learnloop.ai.providers.openai_chat import OpenAIChatProviderClient
from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import StructuredRequest
from learnloop.config import AIProviderConfig

KEY_ENV = "LEARNLOOP_TEST_DEADLINE_KEY"


class Answer(WireModel):
    text: str


def _completion(content: str) -> bytes:
    return json.dumps({
        "id": "chatcmpl-deadline", "object": "chat.completion", "created": 0, "model": "deadline-model",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 3, "completion_tokens": 5, "total_tokens": 8},
    }).encode()


class Dribble(httpx.SyncByteStream):
    """A valid completion body sent one byte every ``every`` seconds."""

    def __init__(self, body: bytes, *, every: float) -> None:
        self.body = body
        self.every = every
        self.served = 0
        self.closed = threading.Event()
        self.closed_at: float | None = None

    def __iter__(self):
        for index in range(len(self.body)):
            if self.closed.is_set():
                return
            time.sleep(self.every)
            self.served += 1
            yield self.body[index:index + 1]

    def close(self) -> None:
        if self.closed_at is None:
            self.closed_at = time.monotonic()
        self.closed.set()


class Server:
    """An in-memory endpoint: each request gets ``make_stream()`` as its body."""

    def __init__(self, make_stream) -> None:
        self.make_stream = make_stream
        self.streams: list[Any] = []
        self.started: list[float] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.started.append(time.monotonic())
        stream = self.make_stream()
        self.streams.append(stream)
        return httpx.Response(200, headers={"content-type": "application/json"}, stream=stream)


def _client(monkeypatch, server: Server, *, timeout: float = 1.0, name: str = "deadline_chat") -> Any:
    monkeypatch.setenv(KEY_ENV, "offline")
    profile = AIProviderConfig(type="openai_chat", base_url="http://deadline.invalid/v1", api_key_env=KEY_ENV,
                               model="deadline-model", response_format="json_object", timeout_seconds=timeout)
    return OpenAIChatProviderClient(name, profile, transport=httpx.MockTransport(server))


def _request_threads() -> list[threading.Thread]:
    return [thread for thread in threading.enumerate() if thread.name.startswith("chat-request:")]


def _join_request_threads() -> None:
    for thread in _request_threads():
        thread.join(timeout=5)
    assert _request_threads() == []


def test_rw6b2_f3_a_dribbling_response_is_aborted_at_the_total_deadline(monkeypatch):
    body = _completion(Answer(text="x" * 40).model_dump_json())
    # Every read arrives well inside the per-operation timeout, but the whole body would take ~5 s.
    server = Server(lambda: Dribble(body, every=5.0 / len(body)))
    client = _client(monkeypatch, server, timeout=1.0)
    started = time.monotonic()
    with pytest.raises(CodexUnavailable):
        client.complete(StructuredRequest(purpose="deadline_probe", prompt="p", result_model=Answer,
                                          timeout_seconds=1.0))
    elapsed = time.monotonic() - started
    assert elapsed < OC.enforced_total_seconds(1.0) + 0.75
    # One physical request (no retry past the deadline), aborted: its stream was closed long before the body ended.
    assert len(server.streams) == 1
    (stream,) = server.streams
    assert stream.closed.wait(5) and stream.served < len(body)
    _join_request_threads()


def test_rw6b2_f3_a_prompt_response_is_unchanged(monkeypatch):
    server = Server(lambda: httpx.ByteStream(_completion(Answer(text="ok").model_dump_json())))
    client = _client(monkeypatch, server, timeout=5.0)
    answer = client.complete(StructuredRequest(purpose="deadline_probe", prompt="p", result_model=Answer,
                                               timeout_seconds=5.0))
    assert answer.text == "ok" and len(server.streams) == 1
    _join_request_threads()


def test_rw6b2_f3_the_bound_is_the_attempts_timeout_with_its_floor():
    assert OC.enforced_total_seconds(0.25) == OC._MIN_ATTEMPT_SECONDS
    assert OC.enforced_total_seconds(42.5) == 42.5


# -- reader_digest: the narration's lease is the enforced bound plus the margin ---------------------


def test_rw6b2_f3_the_narration_lease_is_the_enforced_bound_plus_the_claim_margin():
    from learnloop.hints import map_builder
    from learnloop.instructional import reader_digest as RN

    for timeout in (0.25, 1.0, 180.0, 900.5):
        assert RN.narration_lease_seconds(timeout) == (
            math.ceil(OC.enforced_total_seconds(timeout)) + map_builder.CLAIM_LEASE_SECONDS)


def test_rw6b2_f3_a_dribbling_narration_request_ends_inside_its_lease_and_publishes_nothing(tmp_path, monkeypatch):
    from learnloop.instructional import reader_digest as RN
    from learnloop.vault.loader import load_vault
    from tests.test_reader_digest_narrative import _now, _row, _session_with_question, at

    vault, repo, row = _session_with_question(tmp_path, config="[digest]\nprice_per_million = 1.0\n")
    toml = vault.root / "learnloop.toml"
    text = toml.read_text(encoding="utf-8")
    assert "\n[ai]\n" in text and "\ntimeout_seconds" not in text.split("\n[ai]\n", 1)[1].split("\n[", 1)[0]
    toml.write_text(text.replace("\n[ai]\n", "\n[ai]\ntimeout_seconds = 1\n", 1), encoding="utf-8")
    vault = load_vault(vault.root)
    body = _completion(json.dumps({"narrative": "You read.", "cited_event_ids": []}))
    server = Server(lambda: Dribble(body, every=5.0 / len(body)))
    client = _client(monkeypatch, server, timeout=600, name="deadline_digest")
    route = RN.NarrativeRoute(vault, repo, client=client, envelope=None)
    assert not route.subscription and route.request_timeout == 1.0
    lease = RN.narration_lease_seconds(route.request_timeout)

    result = RN.narrate_digest(vault, repo, row["id"], client=client, now=_now(), clock=at(300))

    assert result.status != "narrated"
    assert _row(repo, row["id"])["narrative_md"] is None and _row(repo, row["id"])["prompt_version"] is None
    assert server.streams, "the narration sent its request"
    bound = OC.enforced_total_seconds(route.request_timeout)
    for stream, started in zip(server.streams, server.started):
        # Each physical request was aborted at the route's timeout (the enforced bound), inside the lease.
        assert stream.closed.wait(5) and stream.served < len(body)
        assert stream.closed_at - started < bound + 0.75 < lease
    _join_request_threads()

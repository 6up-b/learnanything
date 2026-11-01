"""Reader follow-ups (Nov 1), item 4: an enforced TOTAL transport deadline in the
OpenAI-compatible chat adapter. Closes RW6b part 2's open item 1 (final verify F3,
ruling R3: "an abortable total transport deadline is an open item for the AI
transport layer"; ``docs/reviews/reader-rw6b-p2-digest-card.md``).

The SDK's ``timeout`` is httpx's per network operation, so a server that dribbles
bytes held a request open past it. Each physical request now has a total
deadline enforced in the transport itself: every network operation (connect,
TLS, upload, response headers and body) is bounded by the deadline's remaining
time, in the calling thread. When the adapter raises, the request's transport
work is over (Codex review F2: the earlier worker-thread design abandoned a
request whose headers had not arrived, leaving it running while a retry or a
successor could send again). reader_digest's narration lease is that enforced
bound plus the claims' liveness margin.

Everything runs through the real adapter, the real ``openai`` SDK, httpx and
httpcore's HTTP/1.1 over a fake socket (a network backend that honours each
operation's timeout like a socket does): nothing leaves the machine.
"""
from __future__ import annotations

import json
import math
import threading
import time
from typing import Any

import httpcore
import pytest

from learnloop.ai.errors import CodexUnavailable
from learnloop.ai.providers import openai_chat as OC
from learnloop.ai.providers.openai_chat import OpenAIChatProviderClient
from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import StructuredRequest
from learnloop.config import AIProviderConfig

KEY_ENV = "LEARNLOOP_TEST_DEADLINE_KEY"
#: Slack for scheduling on a loaded test machine (the bound itself is exact).
SLACK = 0.75


class Answer(WireModel):
    text: str


def _completion(content: str) -> bytes:
    return json.dumps({
        "id": "chatcmpl-deadline", "object": "chat.completion", "created": 0, "model": "deadline-model",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 3, "completion_tokens": 5, "total_tokens": 8},
    }).encode()


def _http_response(body: bytes) -> tuple[bytes, bytes]:
    head = (b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
            + b"".join(b"X-Pad-%d: %s\r\n" % (index, b"p" * 20) for index in range(4))
            + b"Content-Length: %d\r\n\r\n" % len(body))
    return head, body


class FakeSocket(httpcore.NetworkStream):
    """One connection of the fake server. Each operation honours its timeout
    as a socket with ``settimeout`` does: an operation slower than it waits
    the timeout, then raises."""

    def __init__(self, server: "FakeServer") -> None:
        self.server = server
        self.head, self.body = _http_response(server.body)
        self.position = 0
        self.received = b""
        self.closed = threading.Event()
        self.closed_at: float | None = None

    def _operation(self, delay: float, timeout: float | None, error: type[Exception]) -> None:
        with self.server.lock:
            self.server.in_flight += 1
            self.server.max_in_flight = max(self.server.max_in_flight, self.server.in_flight)
        try:
            if timeout is not None and delay > timeout:
                time.sleep(max(0.0, timeout))
                raise error("timed out")
            time.sleep(delay)
        finally:
            with self.server.lock:
                self.server.in_flight -= 1
                self.server.last_operation_ended = time.monotonic()

    def write(self, buffer: bytes, timeout: float | None = None) -> None:
        self._operation(self.server.write_delay, timeout, httpcore.WriteTimeout)
        self.received += buffer

    def read(self, max_bytes: int, timeout: float | None = None) -> bytes:
        wire = self.head + self.body
        if self.position >= len(wire):
            return b""
        in_head = self.position < len(self.head)
        every = self.server.head_every if in_head else self.server.body_every
        self._operation(every, timeout, httpcore.ReadTimeout)
        # A slow part arrives a byte per read; a prompt one in one read (the head never runs into the body).
        end = self.position + 1 if every > 0 else (len(self.head) if in_head else len(wire))
        chunk = wire[self.position:min(end, self.position + max_bytes)]
        self.position += len(chunk)
        self.server.served += len(chunk)
        return chunk

    def close(self) -> None:
        if self.closed_at is None:
            self.closed_at = time.monotonic()
        self.closed.set()

    def start_tls(self, ssl_context: Any, server_hostname: str | None = None,
                  timeout: float | None = None) -> httpcore.NetworkStream:  # pragma: no cover - plain http here
        return self

    def get_extra_info(self, info: str) -> Any:
        return None


class FakeServer:
    """The fake network: connect, upload, header and body delays per operation."""

    def __init__(self, body: bytes, *, connect_delay: float = 0.0, write_delay: float = 0.0,
                 head_every: float = 0.0, body_every: float = 0.0) -> None:
        self.body = body
        self.connect_delay = connect_delay
        self.write_delay = write_delay
        self.head_every = head_every
        self.body_every = body_every
        self.lock = threading.Lock()
        self.sockets: list[FakeSocket] = []
        self.started: list[float] = []
        self.in_flight = 0
        self.max_in_flight = 0
        self.served = 0
        self.last_operation_ended: float | None = None
        #: Where each connection was opened: ``(host, port)``.
        self.hosts: list[tuple[str, int]] = []

    def backend(self) -> httpcore.NetworkBackend:
        server = self

        class Backend(httpcore.NetworkBackend):
            def connect_tcp(self, host: str, port: int, timeout: float | None = None,
                            local_address: str | None = None, socket_options: Any = None) -> httpcore.NetworkStream:
                server.started.append(time.monotonic())
                server.hosts.append((host, port))
                sock = FakeSocket(server)
                sock._operation(server.connect_delay, timeout, httpcore.ConnectTimeout)
                server.sockets.append(sock)
                return sock

            def connect_unix_socket(self, path: str, timeout: float | None = None,
                                    socket_options: Any = None) -> httpcore.NetworkStream:  # pragma: no cover
                raise httpcore.ConnectError("no unix sockets here")

            def sleep(self, seconds: float) -> None:  # pragma: no cover
                time.sleep(seconds)

        return Backend()


@pytest.fixture
def fake_network(monkeypatch):
    """Install a fake server as httpcore's default network backend (what the
    SDK's own httpx client uses); returns a function that sets it."""

    import httpcore._sync.connection_pool as pool_module

    def install(server: FakeServer) -> FakeServer:
        monkeypatch.setattr(pool_module, "SyncBackend", server.backend)
        return server

    return install


def _client(monkeypatch, *, timeout: float = 1.0, name: str = "deadline_chat",
            base_url: str = "http://deadline.invalid/v1") -> Any:
    monkeypatch.setenv(KEY_ENV, "offline")
    profile = AIProviderConfig(type="openai_chat", base_url=base_url, api_key_env=KEY_ENV,
                               model="deadline-model", response_format="json_object", timeout_seconds=timeout)
    return OpenAIChatProviderClient(name, profile)


def _ask(client: Any, timeout: float) -> Any:
    return client.complete(StructuredRequest(purpose="deadline_probe", prompt="p", result_model=Answer,
                                             timeout_seconds=timeout))


def _assert_transport_over(server: FakeServer, returned_at: float) -> None:
    """When the adapter returned, no network operation was in flight and none
    ran afterwards: the request was cancelled, not abandoned."""

    with server.lock:
        in_flight, served, ended = server.in_flight, server.served, server.last_operation_ended
    assert in_flight == 0, "a network operation was still running when the adapter returned"
    assert ended is None or ended <= returned_at
    time.sleep(0.3)
    assert server.served == served and server.in_flight == 0, "the request kept running after the adapter returned"
    assert all(sock.closed.is_set() for sock in server.sockets)


def test_rw6b2_f3_a_dribbling_response_is_aborted_at_the_total_deadline(monkeypatch, fake_network):
    body = _completion(Answer(text="x" * 40).model_dump_json())
    # Every read arrives well inside the per-operation timeout, but the whole body would take ~5 s.
    server = fake_network(FakeServer(body, body_every=5.0 / len(body)))
    client = _client(monkeypatch, timeout=1.0)
    started = time.monotonic()
    with pytest.raises(CodexUnavailable):
        _ask(client, 1.0)
    returned = time.monotonic()
    assert returned - started < OC.enforced_total_seconds(1.0) + SLACK
    # One physical request (no retry past the deadline), aborted long before the body ended.
    assert len(server.sockets) == 1 and server.served < len(server.sockets[0].head) + len(body)
    _assert_transport_over(server, returned)


def test_f2_delayed_response_headers_are_cancelled_at_the_deadline_not_abandoned(monkeypatch, fake_network):
    """Codex review F2: headers dribbled within each read timeout but past the
    total deadline. Before, the caller gave up while the request kept running
    on its worker (no response stream had been registered to close)."""

    body = _completion(Answer(text="ok").model_dump_json())
    head, _ = _http_response(body)
    server = fake_network(FakeServer(body, head_every=5.0 / len(head)))
    client = _client(monkeypatch, timeout=1.0)
    started = time.monotonic()
    with pytest.raises(CodexUnavailable):
        _ask(client, 1.0)
    returned = time.monotonic()
    assert returned - started < OC.enforced_total_seconds(1.0) + SLACK
    assert len(server.sockets) == 1 and server.served < len(head)
    _assert_transport_over(server, returned)
    assert server.max_in_flight == 1  # never two operations (a replacement request) at once


def test_f2_slow_connect_and_upload_count_against_the_same_deadline(monkeypatch, fake_network):
    """Connect and upload each finish inside the per-operation timeout; with the
    headers that follow, the request passes its total deadline and is
    cancelled within it."""

    body = _completion(Answer(text="ok").model_dump_json())
    head, _ = _http_response(body)
    server = fake_network(FakeServer(body, connect_delay=0.45, write_delay=0.45, head_every=0.9 / len(head)))
    client = _client(monkeypatch, timeout=1.0)
    started = time.monotonic()
    with pytest.raises(CodexUnavailable):
        _ask(client, 1.0)
    returned = time.monotonic()
    assert returned - started < OC.enforced_total_seconds(1.0) + SLACK
    assert len(server.sockets) == 1
    _assert_transport_over(server, returned)


def test_rw6b2_f3_a_prompt_response_is_unchanged(monkeypatch, fake_network):
    server = fake_network(FakeServer(_completion(Answer(text="ok").model_dump_json())))
    client = _client(monkeypatch, timeout=5.0)
    answer = _ask(client, 5.0)
    assert answer.text == "ok" and len(server.sockets) == 1
    assert b"POST /v1/chat/completions" in server.sockets[0].received


def test_f2_the_deadline_is_armed_on_the_sdks_own_http_client(monkeypatch):
    """The adapter arms the SDK's default httpx client (its pool's network
    backend); if a library upgrade moved it, this fails rather than the
    deadline silently lapsing."""

    client = _client(monkeypatch, timeout=5.0)
    assert client._enforce_deadline
    pool = client._client._client._transport._pool
    assert isinstance(pool._network_backend, OC._DeadlineNetworkBackend)
    # Codex re-review F2: the plain stream whose partial sends the deadline bounds one by one.
    import httpcore._backends.sync as sync_backend

    assert OC._SYNC_STREAM is sync_backend.SyncStream


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


def test_rw6b2_f3_a_dribbling_narration_request_ends_inside_its_lease_and_publishes_nothing(
        tmp_path, monkeypatch, fake_network):
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
    head, _ = _http_response(body)
    # Headers dribbled past the deadline (Codex review F2's case), each byte inside the read timeout.
    server = fake_network(FakeServer(body, head_every=5.0 / len(head)))
    client = _client(monkeypatch, timeout=600, name="deadline_digest")
    route = RN.NarrativeRoute(vault, repo, client=client, envelope=None)
    assert not route.subscription and route.request_timeout == 1.0
    lease = RN.narration_lease_seconds(route.request_timeout)

    result = RN.narrate_digest(vault, repo, row["id"], client=client, now=_now(), clock=at(300))
    returned = time.monotonic()

    assert result.status != "narrated"
    assert _row(repo, row["id"])["narrative_md"] is None and _row(repo, row["id"])["prompt_version"] is None
    assert server.sockets, "the narration sent its request"
    _assert_transport_over(server, returned)
    assert server.max_in_flight == 1
    bound = OC.enforced_total_seconds(route.request_timeout)
    for sock, started in zip(server.sockets, server.started):
        # Each physical request was cancelled at the route's timeout (the enforced bound), inside the lease.
        assert sock.closed_at - started < bound + SLACK < lease


# -- Codex re-review F2: partial socket sends inside one httpcore write ------------------------------


class PartialSendSocket:
    """A socket under httpcore's real ``SyncStream``: each ``send`` accepts a
    few bytes and takes most of its timeout (as a slow peer's window does), so
    one ``SyncStream.write`` loops over many partial sends. ``settimeout`` is
    honoured like a socket's: a send slower than it waits it, then raises."""

    def __init__(self, response: bytes, *, per_send: int, send_delay: float) -> None:
        self.response = response
        self.per_send = per_send
        self.send_delay = send_delay
        self.timeout: float | None = None
        self.sends: list[float] = []
        self.received = b""
        self.position = 0
        self.closed_at: float | None = None
        self.lock = threading.Lock()
        self.in_flight = 0

    def settimeout(self, timeout: float | None) -> None:
        self.timeout = timeout

    def send(self, data: bytes) -> int:
        import socket

        with self.lock:
            self.in_flight += 1
        try:
            self.sends.append(time.monotonic())
            if self.timeout is not None and self.send_delay > self.timeout:
                time.sleep(max(0.0, self.timeout))
                raise socket.timeout("timed out")
            time.sleep(self.send_delay)
            chunk = data[:self.per_send]
            self.received += chunk
            return len(chunk)
        finally:
            with self.lock:
                self.in_flight -= 1

    def recv(self, max_bytes: int) -> bytes:
        chunk = self.response[self.position:self.position + max_bytes]
        self.position += len(chunk)
        return chunk

    def close(self) -> None:
        if self.closed_at is None:
            self.closed_at = time.monotonic()

    def fileno(self) -> int:
        return -1  # no descriptor: httpcore's readability probe treats the connection as at its end

    def getsockname(self) -> tuple[str, int]:  # pragma: no cover - not asked for plain http
        return ("127.0.0.1", 0)

    def getpeername(self) -> tuple[str, int]:  # pragma: no cover
        return ("127.0.0.1", 9)


def _sync_stream_backend(sock: PartialSendSocket) -> Any:
    """httpcore's real ``SyncStream`` over the fake socket, as the default backend."""

    import httpcore._backends.sync as sync_backend

    class Backend(httpcore.NetworkBackend):
        def connect_tcp(self, host: str, port: int, timeout: float | None = None,
                        local_address: str | None = None, socket_options: Any = None) -> httpcore.NetworkStream:
            return sync_backend.SyncStream(sock)

        def connect_unix_socket(self, path: str, timeout: float | None = None,
                                socket_options: Any = None) -> httpcore.NetworkStream:  # pragma: no cover
            raise httpcore.ConnectError("no unix sockets here")

        def sleep(self, seconds: float) -> None:  # pragma: no cover
            time.sleep(seconds)

    return Backend


def test_f2_rereview_a_prompt_upload_in_partial_sends_completes_unchanged(monkeypatch):
    """The deadline stream's own send loop delivers the whole request, a few
    bytes per send, and the answer comes back as before."""

    import httpcore._sync.connection_pool as pool_module

    body = _completion(Answer(text="ok").model_dump_json())
    head, _ = _http_response(body)
    sock = PartialSendSocket(head + body, per_send=7, send_delay=0.0)
    monkeypatch.setattr(pool_module, "SyncBackend", _sync_stream_backend(sock))
    client = _client(monkeypatch, timeout=5.0)
    answer = client.complete(StructuredRequest(purpose="deadline_probe", prompt="q" * 500, result_model=Answer,
                                               timeout_seconds=5.0))
    assert answer.text == "ok"
    assert sock.received.startswith(b"POST /v1/chat/completions") and b"q" * 500 in sock.received
    assert len(sock.sends) > 50  # many partial sends, all delivered


def test_f2_rereview_partial_sends_inside_one_write_are_bounded_by_the_total_deadline(monkeypatch):
    """Codex re-review F2: the deadline bounded a whole ``SyncStream.write``
    once, and httpcore set that same timeout before every partial send inside
    it, so a slow peer kept the upload going past the deadline (1 s deadline
    returned after 2.21 s, 16 sends after expiry). Every partial send is now
    bounded by the deadline's remaining time: none starts after it."""

    import httpcore._sync.connection_pool as pool_module

    body = _completion(Answer(text="ok").model_dump_json())
    head, _ = _http_response(body)
    # Sends of 8 bytes, each 0.06 s (well inside the per-operation timeout): the request's
    # headers alone (one httpcore write) take ~4 s, its body (a second write) longer still.
    sock = PartialSendSocket(head + body, per_send=8, send_delay=0.06)

    monkeypatch.setattr(pool_module, "SyncBackend", _sync_stream_backend(sock))
    client = _client(monkeypatch, timeout=1.0)
    started = time.monotonic()
    with pytest.raises(CodexUnavailable):
        client.complete(StructuredRequest(purpose="deadline_probe", prompt="p" * 2000, result_model=Answer,
                                          timeout_seconds=1.0))
    returned = time.monotonic()

    assert returned - started < OC.enforced_total_seconds(1.0) + SLACK
    # The deadline is armed after ``started``: no partial send began past it.
    late = [at for at in sock.sends if at > started + OC.enforced_total_seconds(1.0)]
    assert late == [], f"{len(late)} partial sends started after the deadline"
    assert len(sock.received) < len(b"p" * 2000)  # the upload was cut off, not completed
    assert sock.in_flight == 0 and sock.closed_at is not None and sock.closed_at <= returned
    sent = len(sock.sends)
    time.sleep(0.3)
    assert len(sock.sends) == sent, "the upload kept running after the adapter returned"


# -- Reader follow-ups Nov 1b, item 3: no environment proxy on the metered adapter ----------------

PROXY_VARIABLES = ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy")


@pytest.mark.parametrize("scheme, port", [("https", 443), ("http", 80)])
def test_nov1_r1_an_environment_proxy_no_longer_routes_metered_calls(monkeypatch, fake_network, scheme, port):
    """Reader follow-ups Nov 1, ruling R1 (F2 remainder): under an
    environment HTTPS proxy the SDK's httpx client sent metered calls through
    the proxy, where a TLS-in-TLS read loops ``recv`` under one timeout
    (outside the total deadline's per-operation bound). The adapter's client
    no longer trusts the environment (``trust_env=False``; LearnLoop has no
    proxy setting of its own), so HTTPS_PROXY no longer routes metered calls:
    they connect straight to the provider, under the deadline."""

    for name in ("NO_PROXY", "no_proxy"):
        monkeypatch.delenv(name, raising=False)
    for name in PROXY_VARIABLES:
        monkeypatch.setenv(name, "http://proxy.invalid:3128")
    server = fake_network(FakeServer(_completion(Answer(text="ok").model_dump_json())))
    client = _client(monkeypatch, timeout=5.0, base_url=f"{scheme}://deadline.invalid/v1")
    try:
        answer: Any = _ask(client, 5.0)
    except CodexUnavailable as exc:  # through the proxy, the fake server answers no CONNECT
        answer = exc
    assert server.hosts[:1] == [("deadline.invalid", port)], "the metered call went through the environment proxy"
    assert getattr(answer, "text", None) == "ok" and len(server.hosts) == 1
    http_client = client._client._client
    assert http_client.trust_env is False
    assert not [pattern for pattern, transport in http_client._mounts.items() if transport is not None]
    assert client._enforce_deadline


def test_nov1_r1_the_certificate_store_still_follows_the_environment(monkeypatch, tmp_path):
    """Only the proxy is dropped: SSL_CERT_FILE still names the certificate
    store (a file that does not exist fails construction, as it did)."""

    monkeypatch.setenv("SSL_CERT_FILE", str(tmp_path / "missing.pem"))
    with pytest.raises((FileNotFoundError, OSError)):
        _client(monkeypatch, timeout=5.0, base_url="https://deadline.invalid/v1")
    monkeypatch.delenv("SSL_CERT_FILE")
    assert _client(monkeypatch, timeout=5.0, base_url="https://deadline.invalid/v1")._enforce_deadline

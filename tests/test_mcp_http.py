"""Chat frontend C1a: streamable HTTP on loopback behind the endpoint gate (spec_mcp_frontend_c1 §3.2).

A real uvicorn server on 127.0.0.1 in a thread (no network beyond loopback):

* only ``/<token>/mcp`` answers; ``/mcp`` and any other path is a 404;
* exact Host allowlist (421) and Origin allowlist (403); an absent Origin and
  ``https://claude.ai``, ``https://chatgpt.com`` and the public host's origin
  are accepted;
* an oversized body is a 413;
* the SDK's own client works over it, and the host it labels the call with
  comes from the request;
* a rotated token takes effect without a restart;
* the token never appears in a log record.
"""

from __future__ import annotations

import http.client
import json
import logging
import socket
import threading
import time

import anyio
import httpx2
import pytest
import uvicorn
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

from learnloop.remote.endpoint_token import ensure_token, rotate_token
from learnloop.remote.runtime import RemoteRuntime
from learnloop_mcp.http_app import ConfigurationError, build_http_app, transport_security, uvicorn_config
from tests.helpers import create_basic_vault
from tests.mcp_world import no_model_calls

PUBLIC = "learner-box.example.ts.net"
INITIALIZE = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
    "protocolVersion": "2025-11-25", "capabilities": {}, "clientInfo": {"name": "gate-test", "version": "1"}}})


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Running:
    def __init__(self, runtime: RemoteRuntime) -> None:
        self.port = _free_port()
        app = build_http_app(runtime, port=self.port, public_hosts=[PUBLIC])
        self.server = uvicorn.Server(uvicorn_config(app, port=self.port, log_level="debug"))
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        deadline = time.monotonic() + 15
        while not self.server.started:
            if time.monotonic() > deadline or not self.thread.is_alive():
                raise AssertionError("the MCP test server did not start")
            time.sleep(0.02)

    def post(self, path: str, body: str = INITIALIZE, **headers: str) -> int:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            connection.request("POST", path, body, {"Content-Type": "application/json",
                                                    "Accept": "application/json, text/event-stream", **headers})
            response = connection.getresponse()
            response.read()
            return response.status
        finally:
            connection.close()

    def stop(self) -> None:
        self.server.should_exit = True
        self.thread.join(timeout=10)


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    no_model_calls(monkeypatch)
    paths = create_basic_vault(tmp_path / "vault")
    return RemoteRuntime.attach(paths.root, load_environment=False)


@pytest.fixture
def running(runtime):
    server = Running(runtime)
    try:
        yield server
    finally:
        server.stop()


def test_only_the_secret_path_with_allowed_host_and_origin_answers(runtime, running):
    token = ensure_token(runtime.vault_root)
    path = f"/{token}/mcp"
    assert running.post("/mcp") == 404
    assert running.post("/wrong/mcp") == 404
    assert running.post(f"/{token}/mcp/") == 404
    assert running.post(f"/{token[:-1]}x/mcp") == 404
    assert running.post(path) == 200  # no Origin: server-to-server, allowed
    assert running.post(path, Origin="https://claude.ai") == 200
    assert running.post(path, Origin="https://chatgpt.com") == 200
    assert running.post(path, Host=PUBLIC, Origin=f"https://{PUBLIC}") == 200
    assert running.post(path, Origin="https://untrusted.example") == 403
    assert running.post(path, Origin="http://claude.ai") == 403
    assert running.post(path, Host="untrusted.example") == 421
    assert running.post(path, body="x" * (70 * 1024)) == 413


def test_the_sdk_client_works_over_http_and_the_call_is_labelled_by_host(runtime, running):
    token = ensure_token(runtime.vault_root)
    url = f"http://127.0.0.1:{running.port}/{token}/mcp"

    async def call(headers: dict[str, str]):
        async with httpx2.AsyncClient(headers=headers) as http_client:
            async with Client(streamable_http_client(url, http_client=http_client)) as client:
                names = {tool.name for tool in (await client.list_tools()).tools}
                result = await client.call_tool("status", {})
                return names, result

    for headers in ({"Origin": "https://claude.ai"}, {"User-Agent": "openai-mcp/1.0.0"}, {}):
        names, result = anyio.run(call, headers)
        assert "learning_context" in names and not result.is_error
    events = runtime.repository.reader_interaction_events(kind="chat_tool_call")
    assert [(e["payload"]["host"], e["payload"]["transport"]) for e in events] == [
        ("claude", "streamable_http"), ("chatgpt", "streamable_http"), ("unknown", "streamable_http")]


def test_a_rotated_token_takes_effect_without_a_restart(runtime, running):
    old = ensure_token(runtime.vault_root)
    assert running.post(f"/{old}/mcp") == 200
    new = rotate_token(runtime.vault_root)
    assert new != old
    assert running.post(f"/{old}/mcp") == 404
    assert running.post(f"/{new}/mcp") == 200


def test_the_token_never_reaches_a_log_record(runtime, running, caplog):
    token = ensure_token(runtime.vault_root)
    with caplog.at_level(logging.DEBUG):
        running.post(f"/{token}/mcp")
        running.post(f"/{token}/mcp", Origin="https://untrusted.example")
        running.post(f"/{token}/mcp", body="{not json")
        running.post("/mcp")
    text = "\n".join(record.getMessage() + str(record.args) for record in caplog.records)
    assert token not in text


def test_bind_and_allowlist_configuration_is_validated(runtime):
    from learnloop_mcp.cli import serve

    with pytest.raises(ConfigurationError):
        serve(runtime.vault_root, host="0.0.0.0")
    with pytest.raises(ConfigurationError):
        transport_security(8769, ["https://bad.example/path"], [])
    with pytest.raises(ConfigurationError):
        transport_security(8769, [], ["claude.ai"])
    security = transport_security(8769, [PUBLIC], ["http://localhost:6274"])
    assert security.allowed_hosts == ["127.0.0.1:8769", "localhost:8769", PUBLIC]
    assert security.allowed_origins == ["https://chatgpt.com", "https://claude.ai", f"https://{PUBLIC}",
                                        "http://localhost:6274"]

"""Streamable HTTP on loopback, behind the endpoint gate (spec_mcp_frontend_c1 §3.2).

The M0 probe's security model, which both ChatGPT and Claude accepted through
Tailscale Funnel on 443 (owner decision D1, 2026-10-13):

* bound to ``127.0.0.1`` only (Funnel or Serve proxies to it); the default
  port is 8769, so the probe on 8768 is untouched;
* the persistent secret path ``/<token>/mcp`` (``learnloop.remote.
  endpoint_token``), compared in constant time; every other path is a 404,
  ``/mcp`` included, and the token is reread when it is rotated;
* exact ``Host`` allowlist (loopback on this port and each ``--public-host``)
  and exact ``Origin`` allowlist (``https://chatgpt.com``, ``https://claude.ai``,
  ``https://<public host>`` and each ``--public-origin``); an absent Origin is
  allowed (server-to-server calls from the hosts' clouds carry none), a
  present wrong one is a 403 (the SDK's DNS-rebinding check);
* stateless, JSON responses (no SSE streams), a request-body limit, a bounded
  connection count and keep-alive, no proxy headers trusted;
* no access log: the request path carries the token, so it is never logged.

OAuth is deferred (C1 records it as a risk): the URL is the credential.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from learnloop.remote.endpoint_token import TokenStore

INTERNAL_PATH = "/mcp"
MAX_REQUEST_BODY_BYTES = 64 * 1024
LOOPBACK = "127.0.0.1"
HOST_ORIGINS = ("https://chatgpt.com", "https://claude.ai")
_HOST_RE = re.compile(r"(?=.{1,253}$)[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)*(?::\d{1,5})?")
_ORIGIN_RE = re.compile(r"https?://[a-z0-9.-]+(?::\d{1,5})?")


class ConfigurationError(ValueError):
    """A bind address, host or origin the server refuses to run with."""


def validate_public_hosts(hosts: Sequence[str]) -> list[str]:
    cleaned = []
    for host in hosts:
        value = host.strip().lower()
        if not _HOST_RE.fullmatch(value):
            raise ConfigurationError(f"--public-host must be a bare hostname (no scheme or path): {host!r}")
        cleaned.append(value)
    return cleaned


def validate_origins(origins: Sequence[str]) -> list[str]:
    cleaned = []
    for origin in origins:
        value = origin.strip().lower().rstrip("/")
        if not _ORIGIN_RE.fullmatch(value):
            raise ConfigurationError(f"--public-origin must be scheme://host[:port], exactly: {origin!r}")
        cleaned.append(value)
    return cleaned


def transport_security(port: int, public_hosts: Sequence[str], public_origins: Sequence[str]) -> Any:
    from mcp.server.transport_security import TransportSecuritySettings

    hosts = validate_public_hosts(public_hosts)
    origins = [*HOST_ORIGINS, *(f"https://{host.split(':')[0]}" for host in hosts), *validate_origins(public_origins)]
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[f"{LOOPBACK}:{int(port)}", f"localhost:{int(port)}", *hosts],
        allowed_origins=list(dict.fromkeys(origins)),
    )


async def _not_found(send: Any) -> None:
    await send({"type": "http.response.start", "status": 404,
                "headers": [(b"content-type", b"text/plain; charset=utf-8"), (b"cache-control", b"no-store")]})
    await send({"type": "http.response.body", "body": b"Not Found"})


class EndpointGate:
    """Only ``/<token>/mcp`` reaches the MCP app (rewritten to its internal path)."""

    def __init__(self, inner: Any, tokens: TokenStore) -> None:
        self.inner = inner
        self.tokens = tokens

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] == "lifespan":
            await self.inner(scope, receive, send)
            return
        if scope["type"] != "http":
            return
        if not self.tokens.matches_path(str(scope.get("path") or "")):
            await _not_found(send)
            return
        inner_scope = dict(scope)
        inner_scope["path"] = INTERNAL_PATH
        inner_scope["raw_path"] = INTERNAL_PATH.encode("ascii")
        inner_scope["root_path"] = ""
        await self.inner(inner_scope, receive, send)


def build_http_app(runtime: Any, *, port: int, public_hosts: Sequence[str] = (),
                   public_origins: Sequence[str] = (), clock: Any = None) -> EndpointGate:
    """The gated Starlette app (the server's lifespan included)."""

    from learnloop_mcp.server import build_server

    security = transport_security(port, public_hosts, public_origins)
    server = build_server(runtime, transport="streamable_http", clock=clock)
    app = server.streamable_http_app(
        streamable_http_path=INTERNAL_PATH, json_response=True, stateless_http=True,
        max_request_body_size=MAX_REQUEST_BODY_BYTES, transport_security=security, host=LOOPBACK,
    )
    return EndpointGate(app, TokenStore(runtime.vault_root))


def uvicorn_config(app: Any, *, port: int, log_level: str = "warning") -> Any:
    import uvicorn

    return uvicorn.Config(
        app, host=LOOPBACK, port=int(port), workers=1, proxy_headers=False, access_log=False,
        limit_concurrency=32, timeout_keep_alive=5, h11_max_incomplete_event_size=16 * 1024, http="h11",
        ws="none", lifespan="on", log_level=log_level, server_header=False,
    )


def run_http(runtime: Any, *, port: int, public_hosts: Sequence[str] = (), public_origins: Sequence[str] = (),
             log_level: str = "warning") -> None:
    import uvicorn

    app = build_http_app(runtime, port=port, public_hosts=public_hosts, public_origins=public_origins)
    uvicorn.Server(uvicorn_config(app, port=port, log_level=log_level)).run()


__all__ = [
    "ConfigurationError",
    "EndpointGate",
    "HOST_ORIGINS",
    "INTERNAL_PATH",
    "MAX_REQUEST_BODY_BYTES",
    "build_http_app",
    "run_http",
    "transport_security",
    "uvicorn_config",
]

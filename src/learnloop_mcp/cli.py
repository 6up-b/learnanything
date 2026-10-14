"""``learnloop mcp serve``: attach the vault as a second process and serve it (spec_mcp_frontend_c1 §3).

Called by ``learnloop.app_launch.serve_mcp`` so the ``learnloop`` CLI never
imports this adapter (or the SDK) until a server is asked for.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from learnloop.remote.endpoint_token import ensure_token
from learnloop.remote.runtime import RemoteRuntime
from learnloop_mcp import DEFAULT_PORT
from learnloop_mcp.http_app import LOOPBACK, ConfigurationError, run_http, validate_origins, validate_public_hosts


LOG_LEVELS = ("critical", "error", "warning", "info", "debug")


def serve(vault_root: Path, *, transport: str = "http", port: int = DEFAULT_PORT, host: str = LOOPBACK,
          public_hosts: Sequence[str] = (), public_origins: Sequence[str] = (), log_level: str = "warning") -> None:
    """Attach (SchemaMismatch if the desktop has not migrated) and serve until stopped."""

    if host != LOOPBACK:
        raise ConfigurationError("only --host 127.0.0.1 is permitted; expose it through Tailscale")
    if not 1 <= int(port) <= 65535:
        raise ConfigurationError("--port must be between 1 and 65535")
    if log_level not in LOG_LEVELS:
        # uvicorn's "trace" level logs each request's scope, path (and so the token) included.
        raise ConfigurationError(f"--log-level must be one of {', '.join(LOG_LEVELS)}")
    validate_public_hosts(public_hosts)
    validate_origins(public_origins)
    logging.basicConfig(stream=sys.stderr, level=getattr(logging, log_level.upper(), logging.WARNING))
    runtime = RemoteRuntime.attach(vault_root)
    if transport == "stdio":
        from learnloop_mcp.server import build_server

        build_server(runtime, transport="stdio").run(transport="stdio")
        return
    if transport != "http":
        raise ConfigurationError("--transport must be http or stdio")
    ensure_token(runtime.vault_root)
    print(
        f"LearnLoop MCP: serving {runtime.vault_root.name} on http://{LOOPBACK}:{int(port)}/<token>/mcp "
        "(secondary attach; `learnloop mcp token show` prints the path).",
        file=sys.stderr, flush=True,
    )
    run_http(runtime, port=int(port), public_hosts=public_hosts, public_origins=public_origins,
             log_level=log_level)


__all__ = ["serve"]

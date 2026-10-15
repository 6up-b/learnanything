"""`learnloop mcp`: the chat frontend over MCP (spec_mcp_frontend_c1).

* ``serve``: attach the vault as a second process beside the desktop and serve
  it to ChatGPT or Claude (streamable HTTP on 127.0.0.1, or stdio for
  development clients). Needs the ``mcp`` extra.
* ``token show`` / ``token rotate``: the secret endpoint path (machine-local,
  in ``<vault>/.learnloop/mcp``; printed only here, never logged).
* ``activity``: what the chat side did, from the same ledgers (read-only).

Agents never run Tailscale; the owner points Funnel at the printed local port.
"""
from __future__ import annotations

import json as jsonlib
from pathlib import Path
from typing import Annotated

import typer

from learnloop.cli.receipts import bind_command_vault

mcp_app = typer.Typer(
    no_args_is_help=True,
    help="Chat frontend (MCP): serve this vault to ChatGPT/Claude, its endpoint token, and chat activity.",
)
token_app = typer.Typer(no_args_is_help=True, help="The secret endpoint path the chat connector uses.")
mcp_app.add_typer(token_app, name="token")

DEFAULT_PORT = 8769
VaultOption = Annotated[Path | None, typer.Option("--vault", help="Vault root (default: the enclosing vault).")]


def _root(vault: Path | None) -> Path:
    from learnloop.vault.paths import find_vault_root

    root = vault.expanduser().resolve() if vault else find_vault_root(Path.cwd())
    if not (root / "learnloop.toml").is_file():
        typer.echo(f"{root} is not a LearnLoop vault (no learnloop.toml).", err=True)
        raise typer.Exit(2)
    bind_command_vault(root)
    return root


def _dump(payload: object) -> str:
    return jsonlib.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, default=str)


@mcp_app.command("serve")
def serve(
    vault: VaultOption = None,
    transport: Annotated[str, typer.Option("--transport", help="http (default) or stdio.")] = "http",
    port: Annotated[int, typer.Option("--port", help="Loopback port for http.", min=1, max=65535)] = DEFAULT_PORT,
    host: Annotated[str, typer.Option("--host", help="Bind address; only 127.0.0.1 is permitted.")] = "127.0.0.1",
    public_host: Annotated[list[str] | None, typer.Option(
        "--public-host", help="Exact public Host header the tunnel forwards (repeatable).")] = None,
    public_origin: Annotated[list[str] | None, typer.Option(
        "--public-origin", help="Extra exact browser Origin to accept (repeatable).")] = None,
    log_level: Annotated[str, typer.Option("--log-level", help="Server log level.")] = "warning",
) -> None:
    """Serve the vault to chat hosts (secondary attach: never migrates or runs startup work).

    Exits 78 when the vault's schema is not this code's: open the desktop app or
    run `learnloop doctor` once to migrate."""

    from learnloop.app_launch import serve_mcp
    from learnloop.remote.endpoint_token import TokenError
    from learnloop.remote.runtime import SchemaMismatch

    root = _root(vault)
    try:
        serve_mcp(root, transport=transport, port=port, host=host, public_hosts=list(public_host or []),
                  public_origins=list(public_origin or []), log_level=log_level)
    except ModuleNotFoundError as exc:
        if (exc.name or "").split(".")[0] != "mcp":
            raise
        typer.echo("The MCP server needs the mcp extra: uv sync --extra mcp", err=True)
        raise typer.Exit(1) from None
    except SchemaMismatch as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(78) from None
    except TokenError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(78) from None
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from None


def _token_payload(root: Path, token: str, port: int, public_hosts: list[str]) -> dict[str, object]:
    from learnloop.remote.endpoint_token import endpoint_path, token_path

    path = endpoint_path(token)
    return {
        "path": path,
        "local_url": f"http://127.0.0.1:{port}{path}",
        "public_urls": [f"https://{host}{path}" for host in public_hosts],
        "stored_in": str(token_path(root)),
        "note": "The URL is the credential (no OAuth in C1): share it only with the chat connector.",
    }


@token_app.command("show")
def token_show(
    vault: VaultOption = None,
    port: Annotated[int, typer.Option("--port", min=1, max=65535)] = DEFAULT_PORT,
    public_host: Annotated[list[str] | None, typer.Option("--public-host")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Print the endpoint path and URLs (the token is made on first use)."""

    from learnloop.remote.endpoint_token import TokenError, ensure_token

    root = _root(vault)
    try:
        token = ensure_token(root)
    except TokenError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from None
    payload = _token_payload(root, token, port, list(public_host or []))
    if json_output:
        typer.echo(_dump(payload))
        return
    typer.echo(f"Endpoint path: {payload['path']}")
    typer.echo(f"Local URL:     {payload['local_url']}")
    for url in payload["public_urls"]:  # type: ignore[union-attr]
        typer.echo(f"Public URL:    {url}")
    typer.echo(str(payload["note"]))


@token_app.command("rotate")
def token_rotate(
    vault: VaultOption = None,
    port: Annotated[int, typer.Option("--port", min=1, max=65535)] = DEFAULT_PORT,
    public_host: Annotated[list[str] | None, typer.Option("--public-host")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Replace the token; the old URL stops working (a running server rereads it)."""

    from learnloop.remote.endpoint_token import rotate_token

    root = _root(vault)
    payload = _token_payload(root, rotate_token(root), port, list(public_host or []))
    payload["rotated"] = True
    if json_output:
        typer.echo(_dump(payload))
        return
    typer.echo(f"New endpoint path: {payload['path']}")
    typer.echo("Update the connector URL in ChatGPT and Claude; the old one now answers 404.")


@mcp_app.command("activity")
def activity(
    vault: VaultOption = None,
    days: Annotated[int, typer.Option("--days", min=0, max=3650, help="Look back this many days.")] = 7,
    limit: Annotated[int, typer.Option("--limit", min=0, max=500, help="Recent calls to list.")] = 20,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """What chat hosts did with this vault: calls by tool and host, passages shown (read-only)."""

    from learnloop.db.repositories import Repository
    from learnloop.remote.runtime import vault_sqlite_path
    from learnloop.remote.telemetry import chat_activity

    root = _root(vault)
    report = chat_activity(Repository.attach(vault_sqlite_path(root), read_only=True), days=days, limit=limit)
    if json_output:
        typer.echo(_dump(report))
        return
    typer.echo(f"Chat activity since {report['since']}: {report['calls']} call(s), "
               f"{report['passages_shown']} passage(s) shown from {report['sources_shown']} source(s).")
    if report["by_host"]:
        typer.echo("By host: " + ", ".join(f"{host} {count}" for host, count in report["by_host"].items()))
    if report["by_tool"]:
        typer.echo("By tool: " + ", ".join(f"{tool} {count}" for tool, count in report["by_tool"].items()))
    for call in report["recent"]:
        line = f"  {call['at']}  {call['host'] or 'unknown':8} {call['tool']:17} {call['status']}"
        if call.get("error_code"):
            line += f" ({call['error_code']})"
        if call.get("passages_shown"):
            line += f", {call['passages_shown']} passage(s) shown"
        typer.echo(line)


__all__ = ["mcp_app"]

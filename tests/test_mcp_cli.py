"""Chat frontend C1a: ``learnloop mcp`` (serve, token show/rotate, activity).

* The endpoint token lives in the vault's machine-local state (directory 0700,
  file 0600, a ``.gitignore`` of ``*`` beside it), is stable until rotated and
  is printed only by ``token show``/``rotate``.
* ``serve`` binds loopback only, names the missing extra, and exits 78 on a
  schema it does not match.
* ``activity`` reports chat calls and passages shown from the same ledgers.
"""

from __future__ import annotations

import json
import stat

import anyio
from mcp import Client
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.remote.endpoint_token import read_token, token_path
from learnloop.remote.runtime import RemoteRuntime
from learnloop_mcp.server import build_server
from tests.helpers import create_basic_vault
from tests.mcp_world import build_world, no_model_calls

runner = CliRunner()


def test_token_show_makes_a_private_stable_token_and_rotate_replaces_it(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    first = runner.invoke(app, ["mcp", "token", "show", "--vault", str(paths.root), "--json",
                                "--public-host", "learner-box.example.ts.net"])
    assert first.exit_code == 0, first.output
    shown = json.loads(first.output)
    token = read_token(paths.root)
    assert shown["path"] == f"/{token}/mcp" and shown["local_url"] == f"http://127.0.0.1:8769/{token}/mcp"
    assert shown["public_urls"] == [f"https://learner-box.example.ts.net/{token}/mcp"]
    path = token_path(paths.root)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert (path.parent / ".gitignore").read_text() == "*\n"
    again = json.loads(runner.invoke(app, ["mcp", "token", "show", "--vault", str(paths.root), "--json"]).output)
    assert again["path"] == shown["path"]
    rotated = runner.invoke(app, ["mcp", "token", "rotate", "--vault", str(paths.root), "--json"])
    assert rotated.exit_code == 0 and json.loads(rotated.output)["path"] != shown["path"]
    assert read_token(paths.root) != token


def test_serve_binds_loopback_only_and_names_the_missing_extra(tmp_path, monkeypatch):
    paths = create_basic_vault(tmp_path / "vault")
    refused = runner.invoke(app, ["mcp", "serve", "--vault", str(paths.root), "--host", "0.0.0.0"])
    assert refused.exit_code == 2 and "127.0.0.1" in refused.output
    trace = runner.invoke(app, ["mcp", "serve", "--vault", str(paths.root), "--log-level", "trace"])
    assert trace.exit_code == 2 and "--log-level" in trace.output
    import learnloop.app_launch as app_launch

    def missing(*_args, **_kwargs):
        raise ModuleNotFoundError("No module named 'mcp'", name="mcp")

    monkeypatch.setattr(app_launch, "serve_mcp", missing)
    result = runner.invoke(app, ["mcp", "serve", "--vault", str(paths.root)])
    assert result.exit_code == 1 and "uv sync --extra mcp" in result.output


def test_activity_reports_chat_calls_and_passages_from_the_ledgers(tmp_path, monkeypatch):
    no_model_calls(monkeypatch)
    world = build_world(tmp_path / "w")
    server = build_server(RemoteRuntime.attach(world.root, load_environment=False))

    async def calls():
        async with Client(server) as client:
            await client.call_tool("status", {})
            await client.call_tool("find_sources", {"query": "the determinant changes sign when two rows are swapped"})
            await client.call_tool("progress", {"goal_id": "goal_nowhere"})

    anyio.run(calls)
    result = runner.invoke(app, ["mcp", "activity", "--vault", str(world.root), "--json", "--days", "3650"])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["calls"] == 3
    assert report["by_tool"] == {"find_sources": 1, "progress": 1, "status": 1}
    assert report["by_status"] == {"error": 1, "ok": 2} and report["by_host"] == {"unknown": 3}
    assert report["passages_shown"] >= 1 and report["sources_shown"] >= 1
    text = runner.invoke(app, ["mcp", "activity", "--vault", str(world.root), "--days", "3650"])
    assert text.exit_code == 0 and "3 call(s)" in text.output and "find_sources" in text.output

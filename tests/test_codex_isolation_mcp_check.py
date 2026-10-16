"""An isolated Codex turn's launch check: every MCP server off, or no turn.

Found 2026-10-15 (docs/reviews/codex-isolation-app-servers.md): codex-cli
0.163.0 lists, under ``codex mcp list --json``, the MCP servers an enabled
plugin brings (``codex_app``, ``cua_repl`` on the owner's machine) beside the
ones a config file defines. The transport disabled every listed name with
``-c mcp_servers.<name>.enabled=false``; for a server no config file defines
that override creates a table without a transport, and Codex refused to start:
``Codex process closed stdout. stderr_tail=Error: invalid transport in
mcp_servers.codex_app``. Every isolated turn (the blind grader, the diagnoser,
every isolated judge) failed before its model request.

Now the servers are listed under the isolated turn's own overrides, where
``features.plugins=false`` has already removed the plugin ones; only a server
still listed enabled gets a name override; and the full override set is
checked (``mcp list`` and ``features list``) before the app server starts. Any
server still enabled, a check that fails or times out, or an override Codex
rejects refuses the turn (fail closed).

The fakes model codex-cli 0.163.0 (tests/codex_cli_fakes.py); the ``codex``
tests run the installed binary under a throwaway ``CODEX_HOME`` with a
plugin of its own and make no model call.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from learnloop.ai.errors import CodexUnavailable
from learnloop.ai.providers import codex as codex_module
from learnloop.ai.providers.codex import SdkCodexClient, isolated_turn_overrides
from learnloop.ai.transport import StructuredRequest
from learnloop.config import CodexConfig
from learnloop.diagnosis.offline_review.judge import LinkJudgment

from tests.codex_cli_fakes import fake_codex_calls, write_fake_codex
from tests.project_support import install_fake_codex_sdk

CODEX = shutil.which("codex")
needs_codex = pytest.mark.skipif(CODEX is None, reason="the Codex CLI is not installed")

#: What `codex mcp list --json` showed on the owner's machine on 2026-10-15
#: (names and enabled state only): two config servers, two plugin servers.
OWNER_SHAPE = {
    "config_servers": {"node_repl": True, "openaiDeveloperDocs": True},
    "plugin_servers": {"codex_app": False, "cua_repl": True},
}


def _client(tmp_path: Path, program: Path) -> SdkCodexClient:
    vault_root = tmp_path / "vault"
    vault_root.mkdir(exist_ok=True)
    return SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex"), sdk_codex_bin=str(program)), vault_root)


def _isolated_turn(client: SdkCodexClient, *, workspace: Path | None = None):
    return client.complete(StructuredRequest(
        purpose="blind_grading", prompt="p", result_model=LinkJudgment, workspace=workspace, isolated=True,
    ))


def _launches(log: Path) -> list[list[str]]:
    return [call["overrides"] for call in fake_codex_calls(log) if call["command"][:1] == ["app-server"]]


def _probes(log: Path) -> list[tuple[str, list[str]]]:
    return [(" ".join(call["command"][:2]), call["overrides"]) for call in fake_codex_calls(log)
            if call["command"][:1] != ["app-server"]]


def test_plugin_servers_are_disabled_by_feature_and_config_servers_by_name(tmp_path, monkeypatch):
    """The 2026-10-15 failure: the launch must not name a plugin server."""

    program, log = write_fake_codex(tmp_path / "bin", **OWNER_SHAPE)
    captured = install_fake_codex_sdk(monkeypatch, final_response='{"links": []}', spawn=True,
                                      launch_failure_raises=True)
    client = _client(tmp_path, program)

    _isolated_turn(client)  # raised "invalid transport in `mcp_servers.codex_app`" before the fix

    (launched,) = _launches(log)
    assert launched == list(captured["app_config"]["config_overrides"])
    root = Path(captured["app_config"]["cwd"])
    assert launched == isolated_turn_overrides(root, shell=False, mcp_server_ids=("node_repl", "openaiDeveloperDocs"))
    assert {"features.plugins=false", "features.apps=false", "mcp_servers.node_repl.enabled=false",
            "mcp_servers.openaiDeveloperDocs.enabled=false"} <= set(launched)
    assert not any("codex_app" in override or "cua_repl" in override for override in launched)
    # Listed under the feature overrides, then the exact launch set checked.
    probes = _probes(log)
    assert probes == [
        ("mcp list", isolated_turn_overrides(root, shell=False)),
        ("mcp list", launched),
        ("features list", launched),
    ]
    assert captured["spawned"]["returncode"] == 0


def test_a_read_only_workspace_turn_is_checked_under_its_own_overrides(tmp_path, monkeypatch):
    program, log = write_fake_codex(tmp_path / "bin", **OWNER_SHAPE)
    captured = install_fake_codex_sdk(monkeypatch, final_response='{"links": []}', spawn=True,
                                      launch_failure_raises=True)
    workspace = tmp_path / "snapshot"
    workspace.mkdir()
    _isolated_turn(_client(tmp_path, program), workspace=workspace)
    (launched,) = _launches(log)
    assert launched == isolated_turn_overrides(workspace.resolve(), shell=True,
                                               mcp_server_ids=("node_repl", "openaiDeveloperDocs"))
    assert "features.shell_tool=false" not in launched
    assert {overrides == launched for probe, overrides in _probes(log)[1:]} == {True}
    assert captured["app_config"]["cwd"] == str(workspace.resolve())


def test_without_servers_the_first_listing_is_the_check(tmp_path, monkeypatch):
    program, log = write_fake_codex(tmp_path / "bin", plugin_servers={"cua_repl": True})
    captured = install_fake_codex_sdk(monkeypatch, final_response='{"links": []}', spawn=True,
                                      launch_failure_raises=True)
    _isolated_turn(_client(tmp_path, program))
    (launched,) = _launches(log)
    assert launched == isolated_turn_overrides(Path(captured["app_config"]["cwd"]), shell=False)
    assert _probes(log) == [("mcp list", launched), ("features list", launched)]


def test_the_old_cli_shape_still_disables_config_servers_by_name(tmp_path, monkeypatch):
    """A CLI from before plugin servers were listed: config servers only, fewer fields."""

    program, log = write_fake_codex(tmp_path / "bin", config_servers={"filesystem": True, "docs": False},
                                    old_shape=True)
    install_fake_codex_sdk(monkeypatch, final_response='{"links": []}', spawn=True, launch_failure_raises=True)
    _isolated_turn(_client(tmp_path, program))
    (launched,) = _launches(log)
    assert "mcp_servers.filesystem.enabled=false" in launched
    # Already off: no override needed, and none is added.
    assert not any(override.startswith("mcp_servers.docs.") for override in launched)


def test_config_server_names_with_path_characters_are_disabled_by_name(tmp_path, monkeypatch):
    """0.163.0's `codex mcp add` accepts `:`, `@` and `/`; a `-c` path addresses them."""

    program, log = write_fake_codex(tmp_path / "bin", config_servers={"org/docs": True, "team@host:9": True})
    install_fake_codex_sdk(monkeypatch, final_response='{"links": []}', spawn=True, launch_failure_raises=True)
    _isolated_turn(_client(tmp_path, program))
    (launched,) = _launches(log)
    assert {"mcp_servers.org/docs.enabled=false", "mcp_servers.team@host:9.enabled=false"} <= set(launched)


@pytest.mark.parametrize(
    "spec, named",
    [
        # Listed whatever the features, and not in a config file: its name
        # override is rejected (no transport), so nothing can disable it.
        ({"builtin_servers": {"codex_builtin": True}}, "codex_builtin"),
        # Its name override is accepted but does not turn it off.
        ({"builtin_servers": {"sticky": True}, "rejects_tableless_servers": False}, "sticky"),
        # A key a `-c` path cannot address (Codex splits it on ".").
        ({"config_servers": {"a.b": True}}, "a.b"),
    ],
)
def test_a_server_nothing_disables_refuses_the_turn(tmp_path, monkeypatch, spec, named):
    program, log = write_fake_codex(tmp_path / "bin", **{**OWNER_SHAPE, **spec,
                                                         "config_servers": {**OWNER_SHAPE["config_servers"],
                                                                            **spec.get("config_servers", {})}})
    captured = install_fake_codex_sdk(monkeypatch, final_response='{"links": []}', spawn=True,
                                      launch_failure_raises=True)
    with pytest.raises(CodexUnavailable, match="isolated turn") as refused:
        _isolated_turn(_client(tmp_path, program))
    assert f"'{named}'" in str(refused.value)
    assert _launches(log) == [] and "app_config" not in captured


@pytest.mark.parametrize(
    "behaviour, reason",
    [
        ({"mcp list": "fail"}, "exited 2"),
        ({"mcp list": "garbage"}, "server list"),
        ({"features list": "fail"}, "exited 2"),
        ({"mcp list": "hang"}, "did not finish"),
        ({"features list": "hang"}, "did not finish"),
    ],
)
def test_a_check_that_fails_or_times_out_refuses_the_turn(tmp_path, monkeypatch, behaviour, reason):
    monkeypatch.setattr(codex_module, "_CODEX_PROBE_TIMEOUT_SECONDS", 1.0)
    program, log = write_fake_codex(tmp_path / "bin", **OWNER_SHAPE, behaviour=behaviour)
    captured = install_fake_codex_sdk(monkeypatch, final_response='{"links": []}', spawn=True,
                                      launch_failure_raises=True)
    with pytest.raises(CodexUnavailable, match=reason) as refused:
        _isolated_turn(_client(tmp_path, program))
    assert "refusing the isolated turn" in str(refused.value)
    # Codex's stderr can quote config lines (headers, env): never passed on.
    assert "LEAKED-CONFIG-LINE" not in str(refused.value) and "SECRET-COMMAND" not in str(refused.value)
    assert _launches(log) == [] and "app_config" not in captured


@pytest.mark.parametrize("spec", [{"ignored_features": ["apps"]}, {"missing_features": ["plugins"]}])
def test_connectors_or_plugins_left_on_refuse_the_turn(tmp_path, monkeypatch, spec):
    """``codex_apps`` (the connectors) never shows in ``mcp list``: the feature is checked instead."""

    feature = (spec.get("ignored_features") or spec.get("missing_features"))[0]
    program, log = write_fake_codex(tmp_path / "bin", **OWNER_SHAPE, **spec)
    captured = install_fake_codex_sdk(monkeypatch, final_response='{"links": []}', spawn=True,
                                      launch_failure_raises=True)
    with pytest.raises(CodexUnavailable, match=feature):
        _isolated_turn(_client(tmp_path, program))
    assert _launches(log) == [] and "app_config" not in captured


def test_a_missing_codex_cli_refuses_the_turn(tmp_path, monkeypatch):
    captured = install_fake_codex_sdk(monkeypatch, final_response='{"links": []}')
    client = _client(tmp_path, tmp_path / "no-such-codex")
    with pytest.raises(CodexUnavailable, match="refusing the isolated turn"):
        _isolated_turn(client)
    assert "app_config" not in captured


def test_non_isolated_turns_run_no_check(tmp_path, monkeypatch):
    program, log = write_fake_codex(tmp_path / "bin", **OWNER_SHAPE)
    install_fake_codex_sdk(monkeypatch, final_response='{"links": []}', spawn=True, launch_failure_raises=True)
    _client(tmp_path, program).complete(StructuredRequest(purpose="tutor", prompt="p", result_model=LinkJudgment))
    assert _probes(log) == [] and _launches(log) == [[]]


# -- the installed binary --------------------------------------------------------------


def _plugin_home(tmp_path: Path) -> dict[str, str]:
    """A throwaway CODEX_HOME with one config server and one plugin server."""

    home = tmp_path / "codex-home"
    plugin = home / "plugins" / "cache" / "test" / "sample" / "local"
    (plugin / ".codex-plugin").mkdir(parents=True)
    (plugin / ".codex-plugin" / "plugin.json").write_text('{"name": "sample"}', encoding="utf-8")
    (plugin / ".mcp.json").write_text('{"mcpServers": {"sampleplug": {"command": "/bin/true"}}}', encoding="utf-8")
    (home / "config.toml").write_text(
        '[features]\nplugins = true\n\n[mcp_servers.fsserver]\ncommand = "/bin/true"\n\n'
        '[plugins."sample@test"]\nenabled = true\n',
        encoding="utf-8",
    )
    return {**os.environ, "CODEX_HOME": str(home)}


def _listed(env, overrides, cwd) -> subprocess.CompletedProcess:
    args = [CODEX]
    for override in overrides:
        args += ["-c", override]
    return subprocess.run([*args, "mcp", "list", "--json"], cwd=cwd, env=env, capture_output=True, text=True,
                          timeout=60)


@needs_codex
def test_the_installed_codex_rejects_a_name_override_for_a_plugin_server(tmp_path):
    """The cause, on the installed binary: the old override set could not launch."""

    env = _plugin_home(tmp_path)
    cwd = tmp_path / "turn"
    cwd.mkdir()
    listed = _listed(env, [], cwd)
    assert listed.returncode == 0, listed.stderr
    assert {server["name"] for server in json.loads(listed.stdout)} == {"fsserver", "sampleplug"}
    rejected = _listed(env, isolated_turn_overrides(cwd, shell=False, mcp_server_ids=("fsserver", "sampleplug")), cwd)
    assert rejected.returncode != 0
    assert "invalid transport" in rejected.stderr and "mcp_servers.sampleplug" in rejected.stderr


@needs_codex
@pytest.mark.parametrize("shell", [False, True])
def test_the_installed_codex_passes_the_launch_check(tmp_path, monkeypatch, shell):
    env = _plugin_home(tmp_path)
    monkeypatch.setenv("CODEX_HOME", env["CODEX_HOME"])
    cwd = tmp_path / "turn"
    cwd.mkdir()
    client = SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex"), sdk_codex_bin=CODEX), tmp_path)
    overrides = client._verified_isolated_overrides(cwd, shell=shell)
    assert overrides == isolated_turn_overrides(cwd, shell=shell, mcp_server_ids=("fsserver",))
    listed = _listed(env, overrides, cwd)
    assert listed.returncode == 0, listed.stderr
    assert [(server["name"], server["enabled"]) for server in json.loads(listed.stdout)] == [("fsserver", False)]


@needs_codex
def test_the_installed_codex_addresses_path_characters_but_not_dots(tmp_path, monkeypatch):
    """Why a dotted server name refuses the turn: its `-c` path names another table."""

    home = tmp_path / "codex-home"
    home.mkdir()
    (home / "config.toml").write_text(
        '[mcp_servers."org/docs"]\ncommand = "/bin/true"\n\n[mcp_servers."a.b"]\ncommand = "/bin/true"\n',
        encoding="utf-8",
    )
    env = {**os.environ, "CODEX_HOME": str(home)}
    cwd = tmp_path / "turn"
    cwd.mkdir()
    disabled = _listed(env, ["mcp_servers.org/docs.enabled=false"], cwd)
    assert disabled.returncode == 0, disabled.stderr
    assert dict((s["name"], s["enabled"]) for s in json.loads(disabled.stdout)) == {"org/docs": False, "a.b": True}
    dotted = _listed(env, ["mcp_servers.a.b.enabled=false"], cwd)
    assert dotted.returncode != 0 and "mcp_servers.a`" in dotted.stderr
    monkeypatch.setenv("CODEX_HOME", str(home))
    client = SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex"), sdk_codex_bin=CODEX), tmp_path)
    with pytest.raises(CodexUnavailable, match="'a.b'"):
        client._verified_isolated_overrides(cwd, shell=False)

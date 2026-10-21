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
``features.plugins=false`` has already removed the plugin ones; every server
still listed gets a name override (already-disabled ones too); and the full
override set is checked (``mcp list`` and ``features list``) before the app
server starts. Any server still enabled, a check that fails or times out, or
an override Codex rejects refuses the turn (fail closed).

The Codex review of that fix (docs/reviews/codex-isolation-app-servers-codex-review.md)
added: the check runs where the app server will (inside the bubblewrap sandbox,
in the turn's directory: F1), on the launch command's own configuration
options (F2), and inside the request's deadline, stopped by an interrupt (F3).

The fakes model codex-cli 0.163.0 (tests/codex_cli_fakes.py); the ``codex``
tests run the installed binary under a throwaway ``CODEX_HOME`` (one with a
plugin of its own) and make no model call.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path

import pytest

from learnloop.ai.errors import CodexInterrupted, CodexTurnTimeout, CodexUnavailable
from learnloop.ai.isolation import (
    ToolIsolation,
    ToolIsolationUnavailable,
    isolation_unavailable_reason,
    sandboxed_command,
    tool_isolation,
)
from learnloop.ai.providers import codex as codex_module
from learnloop.ai.providers.codex import SdkCodexClient, isolated_turn_overrides
from learnloop.ai.transport import StructuredRequest
from learnloop.config import CodexConfig
from learnloop.diagnosis.offline_review.judge import LinkJudgment

from learnloop.ai.providers.codex_lockdown import catalog_pin_path

from tests.codex_cli_fakes import fake_codex_calls, without_catalog_pin, write_fake_codex
from tests.project_support import install_fake_codex_sdk

CODEX = shutil.which("codex")
needs_codex = pytest.mark.skipif(CODEX is None, reason="the Codex CLI is not installed")


def _bwrap_works() -> bool:
    if isolation_unavailable_reason() is not None:
        return False
    try:
        with tempfile.TemporaryDirectory(prefix="learnloop-bwrap-probe-") as scratch:
            workdir = Path(scratch) / "workdir"
            workdir.mkdir()
            probe = sandboxed_command(ToolIsolation(workdir=workdir), ["true"], home=Path(scratch) / "agent-home")
            return subprocess.run(probe, capture_output=True, timeout=20).returncode == 0
    except (OSError, subprocess.SubprocessError, ToolIsolationUnavailable):
        return False


requires_bwrap = pytest.mark.skipif(not _bwrap_works(), reason="bubblewrap cannot create a sandbox on this host")

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
    assert launched == isolated_turn_overrides(root, shell=False, mcp_server_ids=("node_repl", "openaiDeveloperDocs"),
                                               model_catalog=catalog_pin_path(launched))
    assert {"features.plugins=false", "features.apps=false", "mcp_servers.node_repl.enabled=false",
            "mcp_servers.openaiDeveloperDocs.enabled=false"} <= set(launched)
    assert not any("codex_app" in override or "cua_repl" in override for override in launched)
    # Listed under the feature overrides, then the exact launch set checked.
    probes = _probes(log)
    unpinned = without_catalog_pin(launched)
    assert probes == [
        ("mcp list", isolated_turn_overrides(root, shell=False)),
        ("mcp list", unpinned),
        ("features list", unpinned),
        ("debug models", unpinned),  # --bundled: the catalog validated and then pinned
        ("debug models", launched),  # the catalog the turn would use: the pinned one
        ("debug prompt-input", launched),  # the effective permission profile
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
                                               mcp_server_ids=("node_repl", "openaiDeveloperDocs"),
                                               model_catalog=catalog_pin_path(launched))
    assert "features.shell_tool=false" not in launched
    assert {without_catalog_pin(overrides) == without_catalog_pin(launched)
            for probe, overrides in _probes(log)[1:]} == {True}
    assert captured["app_config"]["cwd"] == str(workspace.resolve())


def test_without_servers_the_first_listing_is_the_check(tmp_path, monkeypatch):
    program, log = write_fake_codex(tmp_path / "bin", plugin_servers={"cua_repl": True})
    captured = install_fake_codex_sdk(monkeypatch, final_response='{"links": []}', spawn=True,
                                      launch_failure_raises=True)
    _isolated_turn(_client(tmp_path, program))
    (launched,) = _launches(log)
    assert launched == isolated_turn_overrides(Path(captured["app_config"]["cwd"]), shell=False,
                                               model_catalog=catalog_pin_path(launched))
    unpinned = without_catalog_pin(launched)
    assert _probes(log) == [("mcp list", unpinned), ("features list", unpinned), ("debug models", unpinned),
                            ("debug models", launched), ("debug prompt-input", launched)]


def test_the_old_cli_shape_still_disables_config_servers_by_name(tmp_path, monkeypatch):
    """A CLI from before plugin servers were listed: config servers only, fewer fields."""

    program, log = write_fake_codex(tmp_path / "bin", config_servers={"filesystem": True, "docs": False},
                                    old_shape=True)
    install_fake_codex_sdk(monkeypatch, final_response='{"links": []}', spawn=True, launch_failure_raises=True)
    _isolated_turn(_client(tmp_path, program))
    (launched,) = _launches(log)
    assert "mcp_servers.filesystem.enabled=false" in launched
    # Already off, and pinned off all the same (Codex review F1): the layer that
    # turned it off might be one the launch does not load.
    assert "mcp_servers.docs.enabled=false" in launched


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


def test_a_turn_that_did_not_ask_for_isolation_is_checked_and_locked_down_too(tmp_path, monkeypatch):
    """Security stage 2026-10-21: a request without ``isolated`` (the tutor, every
    listwise and paid role) used to launch with no overrides in the vault; it
    now runs the same check and the same locked-down launch."""

    program, log = write_fake_codex(tmp_path / "bin", **OWNER_SHAPE)
    captured = install_fake_codex_sdk(monkeypatch, final_response='{"links": []}', spawn=True,
                                      launch_failure_raises=True)
    _client(tmp_path, program).complete(StructuredRequest(purpose="tutor", prompt="p", result_model=LinkJudgment))
    (launched,) = _launches(log)
    root = Path(captured["app_config"]["cwd"])
    assert launched == isolated_turn_overrides(root, shell=False, mcp_server_ids=("node_repl", "openaiDeveloperDocs"),
                                               model_catalog=catalog_pin_path(launched))
    assert [probe for probe, _overrides in _probes(log)] == ["mcp list", "mcp list", "features list", "debug models",
                                                             "debug models", "debug prompt-input"]
    assert root.name.startswith("learnloop-isolated-turn-") and root != (tmp_path / "vault").resolve()


# -- the check sees the configuration the launch loads (Codex review F1) ----------------

#: A ``codex`` for bubblewrap (``/bin/sh``, nothing outside the sandbox): its user
#: config enables ``fsserver``, and a trusted ancestor project's layer turns it
#: off wherever that layer can be read. It logs each probe and its directory.
_LAYERED_CODEX = r"""#!/bin/sh
pinned=
while [ $# -gt 0 ]; do
  case "$1" in
    -c|--config) [ "$2" = "mcp_servers.fsserver.enabled=false" ] && pinned=1; shift 2 ;;
    *) break ;;
  esac
done
printf '%s %s|%s\n' "$1" "$2" "$(pwd)" >> LOG
enabled=true
[ -r ANCESTOR/.codex/config.toml ] && enabled=false
[ -n "$pinned" ] && enabled=false
case "$1 $2" in
  "mcp list") printf '[{"name": "fsserver", "enabled": %s}]\n' "$enabled" ;;
  "features list") printf 'apps  stable  false\nplugins  stable  false\nmulti_agent  stable  false\n' ;;
  "debug models") printf '{"models": [{"slug": "gpt-5.6-sol", "tool_mode": "code_mode_only"}]}\n' ;;
  "debug prompt-input") printf '[{"type": "message", "role": "developer", "content": [{"type": "input_text", "text": "<permissions instructions>Network access is restricted.</permissions instructions>"}]}, {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "<permission_profile type=\\"managed\\"><file_system type=\\"restricted\\"><entry access=\\"read\\"><special>:minimal</special></entry><entry access=\\"read\\"><path>%s</path></entry></file_system></permission_profile>"}]}]\n' "$(pwd -P)" ;;
  *) exit 2 ;;
esac
"""


def _ancestor_project(tmp_path: Path) -> tuple[Path, Path]:
    """A project whose ``.codex/config.toml`` disables ``fsserver``, and the
    sandbox's working directory inside it (bubblewrap mounts only the latter)."""

    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)
    (project / ".codex").mkdir()
    (project / ".codex" / "config.toml").write_text("[mcp_servers.fsserver]\nenabled = false\n", encoding="utf-8")
    workdir = project / "work"
    workdir.mkdir()
    return project, workdir


@requires_bwrap
def test_the_check_runs_inside_the_sandbox_in_the_turns_own_directory(tmp_path, monkeypatch):
    """A layer the sandbox cannot see disabled the server on the host only: the
    check must list it where the app server will run, and pin it off."""

    project, workdir = _ancestor_project(tmp_path)
    home = tmp_path / "codex-home"
    home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(home))
    log = workdir / "probes.log"
    agent = tmp_path / "tools" / "codex"
    agent.parent.mkdir()
    agent.write_text(_LAYERED_CODEX.replace("LOG", shlex.quote(str(log))).replace("ANCESTOR", shlex.quote(str(project))),
                     encoding="utf-8")
    agent.chmod(0o755)
    captured = install_fake_codex_sdk(monkeypatch, final_response='{"links": []}')
    (tmp_path / "vault").mkdir()
    client = SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex"), sdk_codex_bin=str(agent)),
                            tmp_path / "vault")
    with tool_isolation(ToolIsolation(workdir=workdir)):
        _isolated_turn(client)
    root = captured["thread_start"]["cwd"]
    assert "mcp_servers.fsserver.enabled=false" in captured["app_config"]["config_overrides"]
    assert log.read_text(encoding="utf-8").splitlines() == [
        f"mcp list|{root}", f"mcp list|{root}", f"features list|{root}", f"debug models|{root}",
        f"debug models|{root}", f"debug prompt-input|{root}",
    ]
    # The pinned catalog sat in the one host directory the sandbox mounts, in
    # a directory of the turn's that is gone after it (H4).
    pin = catalog_pin_path(captured["app_config"]["config_overrides"])
    assert pin is not None and Path(pin).parent.parent == workdir.resolve()
    assert Path(pin).parent.name.startswith(".learnloop-codex-catalog-") and not Path(pin).parent.exists()


def test_a_check_the_sandbox_refuses_refuses_the_turn(tmp_path, monkeypatch):
    program, log = write_fake_codex(tmp_path / "bin", **OWNER_SHAPE)
    captured = install_fake_codex_sdk(monkeypatch, final_response='{"links": []}')
    monkeypatch.setattr("learnloop.ai.isolation.bubblewrap_path", lambda: None)
    with tool_isolation(ToolIsolation(workdir=tmp_path / "work")):
        (tmp_path / "work").mkdir()
        with pytest.raises(CodexUnavailable, match="refusing the isolated turn"):
            _isolated_turn(_client(tmp_path, program))
    assert fake_codex_calls(log) == [] and "app_config" not in captured


# -- the launch command's own configuration flags (Codex review F2) ---------------------


def _launch_command_client(tmp_path: Path, program: Path, *, before: str = "", after: str) -> SdkCodexClient:
    (tmp_path / "vault").mkdir(exist_ok=True)
    command = " ".join(part for part in (str(program), before, "app-server", after) if part)
    return SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex"), sdk_launch_command=command),
                          tmp_path / "vault")


def test_configuration_flags_after_app_server_are_checked_and_launched_as_one_set(tmp_path, monkeypatch):
    """`-c` is global in codex-cli 0.163.0: written after `app-server` it still
    applies, and after the turn's own overrides it would win over them."""

    program, log = write_fake_codex(tmp_path / "bin", **OWNER_SHAPE)
    captured = install_fake_codex_sdk(monkeypatch, final_response='{"links": []}', spawn=True,
                                      launch_failure_raises=True)
    after = ("-c features.apps=true --config=mcp_servers.node_repl.enabled=true -cfeatures.plugins=true "
             "--listen stdio://")
    _isolated_turn(_launch_command_client(tmp_path, program, after=after))

    loaded = json.loads(captured["spawned"]["stdout"])
    assert loaded["servers_on"] == []
    assert not {"apps", "plugins"} & set(loaded["features_on"])
    launch = captured["app_config"]["launch_args_override"]
    assert launch[-3:] == ("app-server", "--listen", "stdio://")
    # The user's flags first, then the turn's: the probes ran the same set.
    (launched,) = _launches(log)
    assert launched[:3] == ["features.apps=true", "mcp_servers.node_repl.enabled=true", "features.plugins=true"]
    unpinned = without_catalog_pin(launched)
    assert [overrides for _probe, overrides in _probes(log)][1:] == [unpinned, unpinned, unpinned, launched, launched]


@pytest.mark.parametrize(
    "before, after, flag",
    [
        ("", "--enable apps --listen stdio://", "--enable apps"),
        ("", "--enable=plugins", "--enable=plugins"),
        # Before `app-server` too: a toggle applies after every `-c`, wherever it stands.
        ("--enable hooks", "--listen stdio://", "--enable hooks"),
    ],
)
def test_a_feature_toggle_that_turns_an_isolation_feature_back_on_refuses_the_turn(
    tmp_path, monkeypatch, before, after, flag
):
    program, log = write_fake_codex(tmp_path / "bin", **OWNER_SHAPE)
    captured = install_fake_codex_sdk(monkeypatch, final_response='{"links": []}', spawn=True,
                                      launch_failure_raises=True)
    with pytest.raises(CodexUnavailable, match="refusing the isolated turn") as refused:
        _isolated_turn(_launch_command_client(tmp_path, program, before=before, after=after))
    assert flag.replace("=", " ").split()[-1] in str(refused.value)
    assert _launches(log) == [] and "app_config" not in captured


@pytest.mark.parametrize("after", ["--remote-control", "proxy", "--listen", "--analytics-default-enabled=x"])
def test_an_argument_after_app_server_the_check_cannot_read_refuses_the_turn(tmp_path, monkeypatch, after):
    program, log = write_fake_codex(tmp_path / "bin", **OWNER_SHAPE)
    captured = install_fake_codex_sdk(monkeypatch, final_response='{"links": []}', spawn=True,
                                      launch_failure_raises=True)
    with pytest.raises(CodexUnavailable, match="refusing the isolated turn"):
        _isolated_turn(_launch_command_client(tmp_path, program, after=after))
    assert fake_codex_calls(log) == [] and "app_config" not in captured


@pytest.mark.parametrize("after", ["--listen stdio://", "--listen=stdio://", "--stdio", "--strict-config", ""])
def test_the_app_servers_own_arguments_stay_after_it(tmp_path, monkeypatch, after):
    program, _log = write_fake_codex(tmp_path / "bin", **OWNER_SHAPE)
    captured = install_fake_codex_sdk(monkeypatch, final_response='{"links": []}', spawn=True,
                                      launch_failure_raises=True)
    _isolated_turn(_launch_command_client(tmp_path, program, after=after))
    launch = captured["app_config"]["launch_args_override"]
    assert list(launch[launch.index("app-server"):]) == ["app-server", *after.split()]


# -- the request deadline and cancellation cover the check (Codex review F3) --------------


def test_the_check_runs_inside_the_request_deadline(tmp_path, monkeypatch):
    monkeypatch.setattr(codex_module, "_CODEX_PROBE_TIMEOUT_SECONDS", 8.0)
    program, log = write_fake_codex(tmp_path / "bin", **OWNER_SHAPE, behaviour={"mcp list": "hang"})
    captured = install_fake_codex_sdk(monkeypatch, final_response='{"links": []}')
    started = time.monotonic()
    with pytest.raises(CodexTurnTimeout, match="1-second deadline"):
        _client(tmp_path, program).complete(StructuredRequest(
            purpose="blind_grading", prompt="p", result_model=LinkJudgment, isolated=True, timeout_seconds=1.0,
        ))
    assert time.monotonic() - started < 6
    assert len(_probes(log)) == 1 and _launches(log) == [] and "app_config" not in captured


def test_the_turn_gets_only_what_the_check_left_of_the_deadline(tmp_path, monkeypatch):
    # Two slow probes (no server to pin) take at least 1 s of a 1.6 s deadline;
    # the turn needs 1 s more, so the deadline ends it.
    program, _log = write_fake_codex(tmp_path / "bin", behaviour={"mcp list": "slow", "features list": "slow"},
                                     slow_seconds=0.5)
    install_fake_codex_sdk(monkeypatch, final_response='{"links": []}', turn_seconds=1.0)
    with pytest.raises(CodexTurnTimeout, match="1.6-second deadline"):
        _client(tmp_path, program).complete(StructuredRequest(
            purpose="blind_grading", prompt="p", result_model=LinkJudgment, isolated=True, timeout_seconds=1.6,
        ))


def _interrupted_during_the_check(client: SdkCodexClient, started, *, isolation: ToolIsolation | None = None):
    """Run an isolated turn, interrupt it once ``started()`` (the first probe
    is running); return its error and how long it took to stop."""

    outcome: dict[str, BaseException] = {}

    def run() -> None:
        try:
            if isolation is None:
                _isolated_turn(client)
            else:
                with tool_isolation(isolation):
                    _isolated_turn(client)
        except BaseException as exc:  # noqa: BLE001 - the test inspects it
            outcome["error"] = exc

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    waited = time.monotonic() + 20
    while not started() and time.monotonic() < waited:
        time.sleep(0.05)
    assert started(), "the launch check never started"
    interrupted_at = time.monotonic()
    client.interrupt()
    worker.join(15)
    assert not worker.is_alive()
    return outcome.get("error"), time.monotonic() - interrupted_at


def test_an_interrupt_during_the_check_stops_it_and_nothing_launches(tmp_path, monkeypatch):
    monkeypatch.setattr(codex_module, "_CODEX_PROBE_TIMEOUT_SECONDS", 12.0)
    program, log = write_fake_codex(tmp_path / "bin", **OWNER_SHAPE, behaviour={"mcp list": "hang"})
    captured = install_fake_codex_sdk(monkeypatch, final_response='{"links": []}')
    error, seconds = _interrupted_during_the_check(_client(tmp_path, program), lambda: bool(_probes(log)))
    assert isinstance(error, CodexInterrupted) and seconds < 8
    assert len(_probes(log)) == 1 and _launches(log) == [] and "app_config" not in captured


@requires_bwrap
def test_an_interrupt_stops_a_check_running_inside_the_sandbox(tmp_path, monkeypatch):
    monkeypatch.setattr(codex_module, "_CODEX_PROBE_TIMEOUT_SECONDS", 12.0)
    workdir = tmp_path / "work"
    workdir.mkdir()
    home = tmp_path / "codex-home"
    home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(home))
    log = workdir / "probes.log"
    agent = tmp_path / "tools" / "codex"
    agent.parent.mkdir()
    agent.write_text(f"#!/bin/sh\necho started >> {shlex.quote(str(log))}\nexec sleep 30\n", encoding="utf-8")
    agent.chmod(0o755)
    captured = install_fake_codex_sdk(monkeypatch, final_response='{"links": []}')
    (tmp_path / "vault").mkdir()
    client = SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex"), sdk_codex_bin=str(agent)),
                            tmp_path / "vault")
    error, seconds = _interrupted_during_the_check(client, log.exists, isolation=ToolIsolation(workdir=workdir))
    assert isinstance(error, CodexInterrupted) and seconds < 8
    assert log.read_text(encoding="utf-8").splitlines() == ["started"] and "app_config" not in captured


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
    assert overrides == isolated_turn_overrides(cwd, shell=shell, mcp_server_ids=("fsserver",),
                                                model_catalog=catalog_pin_path(overrides))
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


def _listed_in_sandbox(isolation: ToolIsolation, overrides, cwd: Path) -> list[tuple[str, bool]]:
    """`codex mcp list --json` inside ``isolation``, in ``cwd``: what the app server would load there."""

    args = [CODEX]
    for override in overrides:
        args += ["-c", override]
    command = sandboxed_command(isolation, ["/bin/sh", "-c", 'cd "$0" && exec "$@"', str(cwd), *args,
                                            "mcp", "list", "--json"])
    listed = subprocess.run(command, capture_output=True, text=True, timeout=60)
    assert listed.returncode == 0, listed.stderr
    return [(server["name"], server["enabled"]) for server in json.loads(listed.stdout)]


@needs_codex
@requires_bwrap
def test_the_installed_codex_pins_a_server_only_an_unseen_ancestor_project_disables(tmp_path, monkeypatch):
    """Codex review F1 on the installed binary: the user config enables a server,
    a trusted ancestor project disables it, and bubblewrap mounts only the
    working directory inside that project, so only the host sees the layer."""

    project, workdir = _ancestor_project(tmp_path)
    home = tmp_path / "codex-home"
    home.mkdir()
    (home / "config.toml").write_text(
        f'[mcp_servers.fsserver]\ncommand = "/bin/true"\n\n[projects.{json.dumps(str(project))}]\n'
        'trust_level = "trusted"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_HOME", str(home))
    isolation = ToolIsolation(workdir=workdir)
    # The cause: the two views disagree.
    seen = workdir / "seen"
    seen.mkdir()
    host = _listed({**os.environ, "CODEX_HOME": str(home)}, [], seen)
    assert host.returncode == 0, host.stderr
    assert [(server["name"], server["enabled"]) for server in json.loads(host.stdout)] == [("fsserver", False)]
    assert _listed_in_sandbox(isolation, [], seen) == [("fsserver", True)]

    captured = install_fake_codex_sdk(monkeypatch, final_response='{"links": []}')
    client = SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex"), sdk_codex_bin=CODEX), tmp_path)
    with tool_isolation(isolation):
        _isolated_turn(client)
    overrides = captured["app_config"]["config_overrides"]
    assert "mcp_servers.fsserver.enabled=false" in overrides
    root = Path(captured["thread_start"]["cwd"])
    root.mkdir()  # the turn's empty directory, removed after the turn
    # (The turn's catalog pin went with the turn: listed without it.)
    assert _listed_in_sandbox(isolation, without_catalog_pin(overrides), root) == [("fsserver", False)]

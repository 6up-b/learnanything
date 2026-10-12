"""Slice 1 §5.6 / §4: the Codex transport's read boundary and tool isolation.

Codex review F1/F2 (2026-10-12): Codex's built-in ``read-only`` sandbox grants
full-disk READ access, and a grading/judging/diagnosis turn started in the
vault root could read prior grades and diagnoses. The transport now starts
every isolated turn under a LearnLoop permission profile that can read only
the turn's workspace (a snapshot export, or an empty directory) plus the
platform minimum, with network, connectors, MCP servers, memories, hooks and
web search off, and the shell tool off when there is no workspace.

The ``codex`` tests below run the INSTALLED Codex binary's own sandbox with
the exact overrides the transport passes, under a throwaway ``CODEX_HOME``.
They make no model call and skip when Codex is not installed.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from learnloop.ai.errors import AIProviderUnavailable, CodexUnavailable
from learnloop.ai.providers.codex import (
    ISOLATED_PROFILE,
    SdkCodexClient,
    isolated_turn_overrides,
)
from learnloop.ai.transport import (
    ISOLATED_TURN,
    READ_ONLY_WORKSPACE,
    STRUCTURED_COMPLETION,
    StructuredRequest,
    execute_structured_operation,
)
from learnloop.attempts.blind_grading import blind_grading_context, request_blind_grading_proposal
from learnloop.config import CodexConfig
from learnloop.diagnosis.offline_review.judge import LinkJudgment

from tests.diagnosis_fakes import ReviewFakeClient
from tests.diagnosis_split_helpers import build_diagnosis_vault, seed_history

CODEX = shutil.which("codex")
needs_codex = pytest.mark.skipif(CODEX is None, reason="the Codex CLI is not installed")


def _codex_env(tmp_path: Path) -> dict[str, str]:
    home = tmp_path / "codex-home"
    home.mkdir(exist_ok=True)
    return {**os.environ, "CODEX_HOME": str(home)}


def _sandboxed(tmp_path: Path, overrides: list[str], cwd: Path, *command: str) -> subprocess.CompletedProcess:
    args = [CODEX, "sandbox"]
    for override in overrides:
        args += ["-c", override]
    return subprocess.run(
        [*args, "--", *command], cwd=cwd, env=_codex_env(tmp_path), capture_output=True, text=True, timeout=60,
    )


@pytest.fixture()
def layout(tmp_path):
    workspace = tmp_path / "snapshot"
    workspace.mkdir()
    (workspace / "INDEX.md").write_text("snapshot index\n", encoding="utf-8")
    vault = tmp_path / "vault"
    vault.mkdir()
    sentinel = vault / "sentinel.txt"
    sentinel.write_text("LIVE-VAULT-SENTINEL\n", encoding="utf-8")
    return workspace, vault, sentinel


@needs_codex
def test_the_builtin_read_only_sandbox_reads_the_whole_disk(tmp_path, layout):
    """The reviewer's premise, on the installed binary: read-only is not a read boundary."""

    workspace, _vault, sentinel = layout
    result = _sandboxed(tmp_path, ['default_permissions=":read-only"'], workspace, "cat", str(sentinel))
    assert "LIVE-VAULT-SENTINEL" in result.stdout


@needs_codex
@pytest.mark.parametrize("shell", [True, False])
def test_an_isolated_turn_cannot_read_a_sentinel_outside_its_workspace(tmp_path, layout, shell):
    workspace, _vault, sentinel = layout
    overrides = isolated_turn_overrides(workspace, shell=shell, mcp_server_ids=())
    outside = _sandboxed(tmp_path, overrides, workspace, "cat", str(sentinel))
    assert "LIVE-VAULT-SENTINEL" not in outside.stdout
    assert outside.returncode != 0
    inside = _sandboxed(tmp_path, overrides, workspace, "cat", str(workspace / "INDEX.md"))
    assert inside.stdout == "snapshot index\n"
    write = _sandboxed(tmp_path, overrides, workspace, "sh", "-c", f"echo x > {workspace / 'new.txt'}")
    assert write.returncode != 0 and not (workspace / "new.txt").exists()


def _app_server_thread(tmp_path: Path, overrides: list[str], cwd: Path, thread_params: dict[str, Any]) -> dict[str, Any]:
    args = [CODEX]
    for override in overrides:
        args += ["--config", override]
    args += ["app-server", "--listen", "stdio://"]
    process = subprocess.Popen(
        args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, cwd=cwd, env=_codex_env(tmp_path),
    )
    try:
        def send(message):
            process.stdin.write(json.dumps(message) + "\n")
            process.stdin.flush()

        def receive(request_id):
            while True:
                line = process.stdout.readline()
                assert line, "the app server closed its output"
                message = json.loads(line)
                if message.get("id") == request_id:
                    return message

        send({"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "learnloop-test", "title": "t", "version": "0"}, "capabilities": {"experimentalApi": True}}})
        receive(1)
        send({"method": "initialized"})
        send({"id": 2, "method": "thread/start", "params": {"cwd": str(cwd), "ephemeral": True, **thread_params}})
        return receive(2)
    finally:
        process.kill()
        process.wait(timeout=10)


@needs_codex
def test_the_app_server_starts_the_thread_under_the_learnloop_profile(tmp_path, layout):
    workspace, _vault, _sentinel = layout
    overrides = isolated_turn_overrides(workspace, shell=True, mcp_server_ids=())
    # Exactly what SdkCodexClient sends to thread_start in an isolated turn.
    started = _app_server_thread(tmp_path, overrides, workspace, {"serviceName": "learnloop:diagnosis"})["result"]
    assert started["activePermissionProfile"]["id"] == ISOLATED_PROFILE
    assert started["approvalPolicy"] == "never"
    assert started["sandbox"].get("networkAccess") is False
    # Why the client never passes a sandbox mode: it replaces the profile.
    replaced = _app_server_thread(tmp_path, overrides, workspace, {"sandbox": "read-only"})["result"]
    assert replaced.get("activePermissionProfile") is None


@needs_codex
def test_isolated_overrides_switch_the_tools_off(tmp_path, layout):
    workspace, _vault, _sentinel = layout
    args = [CODEX]
    for override in isolated_turn_overrides(workspace, shell=False, mcp_server_ids=()):
        args += ["-c", override]
    listed = subprocess.run([*args, "features", "list"], cwd=workspace, env=_codex_env(tmp_path), capture_output=True, text=True, timeout=60)
    states = {line.split()[0]: line.split()[-1] for line in listed.stdout.splitlines() if line.strip()}
    for feature in ("shell_tool", "apps", "plugins", "multi_agent", "hooks", "view_image", "browser_use", "computer_use", "memories"):
        assert states.get(feature) == "false", feature


# -- the transport ------------------------------------------------------------------


def _fake_sdk(monkeypatch, captured: dict[str, Any], *, overrides_field: bool = True):
    class FakeCodex:
        def __init__(self, config):
            captured["app_config"] = config.kwargs
            workspace = Path(config.kwargs["cwd"])
            captured["workspace_listing"] = sorted(path.name for path in workspace.iterdir())

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def close(self):
            return None

        def thread_start(self, **kwargs):
            captured["thread_start"] = kwargs
            return FakeThread()

    class FakeThread:
        def turn(self, prompt, **kwargs):
            captured["turn"] = kwargs
            return SimpleNamespace(run=lambda: SimpleNamespace(final_response='{"links": []}', items=[]), interrupt=lambda: None)

    if overrides_field:
        class SdkAppConfig:
            def __init__(self, *, codex_bin=None, launch_args_override=None, config_overrides=(), cwd=None, env=None, client_name="", client_title=""):
                self.kwargs = {"codex_bin": codex_bin, "launch_args_override": launch_args_override, "config_overrides": tuple(config_overrides), "cwd": cwd}
    else:
        class SdkAppConfig:
            def __init__(self, *, codex_bin=None, launch_args_override=None, cwd=None, env=None, client_name="", client_title=""):
                self.kwargs = {"codex_bin": codex_bin, "cwd": cwd}

    class ReasoningSummary:
        @classmethod
        def model_validate(cls, value):
            return value

    from enum import Enum

    class ReasoningEffort(Enum):
        low = "low"

    openai_codex = ModuleType("openai_codex")
    openai_codex.Codex = FakeCodex
    openai_codex.CodexConfig = SdkAppConfig
    types = ModuleType("openai_codex.types")
    types.Personality = SimpleNamespace(pragmatic="pragmatic")
    types.ReasoningEffort = ReasoningEffort
    types.ReasoningSummary = ReasoningSummary
    openai_codex.types = types
    monkeypatch.setitem(sys.modules, "openai_codex", openai_codex)
    monkeypatch.setitem(sys.modules, "openai_codex.types", types)


def _client(tmp_path, monkeypatch, *, mcp=("filesystem",)) -> SdkCodexClient:
    vault_root = tmp_path / "vault"
    vault_root.mkdir(exist_ok=True)
    client = SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex"), sdk_codex_bin="/usr/bin/codex-for-test"), vault_root)
    monkeypatch.setattr(client, "_configured_mcp_server_ids", lambda _cwd: tuple(mcp))
    return client


def test_a_snapshot_turn_runs_under_the_profile_never_the_builtin_sandbox(tmp_path, monkeypatch):
    captured: dict[str, Any] = {}
    _fake_sdk(monkeypatch, captured)
    client = _client(tmp_path, monkeypatch)
    workspace = tmp_path / "snapshot"
    workspace.mkdir()
    assert client.supports(READ_ONLY_WORKSPACE) and client.supports(ISOLATED_TURN)
    client.complete(StructuredRequest(purpose="diagnosis", prompt="p", result_model=LinkJudgment, workspace=workspace, isolated=True))
    overrides = captured["app_config"]["config_overrides"]
    assert overrides == tuple(isolated_turn_overrides(workspace.resolve(), shell=True, mcp_server_ids=("filesystem",)))
    assert f'default_permissions="{ISOLATED_PROFILE}"' in overrides
    assert "mcp_servers.filesystem.enabled=false" in overrides
    assert "sandbox" not in captured["thread_start"] and "sandbox_policy" not in captured["turn"]
    for cwd in (captured["app_config"]["cwd"], captured["thread_start"]["cwd"], captured["turn"]["cwd"]):
        assert cwd == str(workspace.resolve())


def test_an_isolated_turn_without_a_workspace_starts_in_an_empty_directory(tmp_path, monkeypatch):
    """F2: the blind grader, the judge and non-snapshot diagnoses never start in the vault."""

    captured: dict[str, Any] = {}
    _fake_sdk(monkeypatch, captured)
    client = _client(tmp_path, monkeypatch)
    client.complete(StructuredRequest(purpose="blind_grading", prompt="p", result_model=LinkJudgment, isolated=True))
    cwd = Path(captured["app_config"]["cwd"])
    assert cwd != client.vault_root and client.vault_root not in cwd.parents
    assert captured["workspace_listing"] == []
    assert not cwd.exists()  # removed after the turn
    overrides = captured["app_config"]["config_overrides"]
    assert "features.shell_tool=false" in overrides and "features.unified_exec=false" in overrides
    assert overrides == tuple(isolated_turn_overrides(cwd, shell=False, mcp_server_ids=("filesystem",)))


def test_an_sdk_that_cannot_take_config_overrides_fails_closed(tmp_path, monkeypatch):
    captured: dict[str, Any] = {}
    _fake_sdk(monkeypatch, captured, overrides_field=False)
    client = _client(tmp_path, monkeypatch)
    with pytest.raises(CodexUnavailable):
        client.complete(StructuredRequest(purpose="blind_grading", prompt="p", result_model=LinkJudgment, isolated=True))
    assert "turn" not in captured


def test_unlisted_mcp_servers_fail_closed(tmp_path, monkeypatch):
    captured: dict[str, Any] = {}
    _fake_sdk(monkeypatch, captured)
    client = _client(tmp_path, monkeypatch)

    def broken(_cwd):
        raise CodexUnavailable("cannot list MCP servers")

    monkeypatch.setattr(client, "_configured_mcp_server_ids", broken)
    with pytest.raises(CodexUnavailable):
        client.complete(StructuredRequest(purpose="blind_grading", prompt="p", result_model=LinkJudgment, isolated=True))
    assert "turn" not in captured


def test_a_launch_override_gets_the_overrides_before_app_server(tmp_path, monkeypatch):
    captured: dict[str, Any] = {}
    _fake_sdk(monkeypatch, captured)
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    client = SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex"), sdk_launch_command="/opt/codex app-server --listen stdio://"), vault_root)
    monkeypatch.setattr(client, "_configured_mcp_server_ids", lambda _cwd: ())
    client.complete(StructuredRequest(purpose="blind_grading", prompt="p", result_model=LinkJudgment, isolated=True))
    launch = captured["app_config"]["launch_args_override"]
    assert launch[0] == "/opt/codex" and launch[-3:] == ("app-server", "--listen", "stdio://")
    assert "--config" in launch and f'default_permissions="{ISOLATED_PROFILE}"' in launch


def test_non_isolated_turns_are_unchanged(tmp_path, monkeypatch):
    captured: dict[str, Any] = {}
    _fake_sdk(monkeypatch, captured)
    client = _client(tmp_path, monkeypatch)
    client.complete(StructuredRequest(purpose="tutor", prompt="p", result_model=LinkJudgment))
    assert captured["app_config"]["cwd"] == str(client.vault_root)
    assert captured["app_config"]["config_overrides"] == ()


class _NoIsolation:
    provider_name = "plain"
    provider_type = "codex_sdk"
    model = "m"

    def supports(self, capability: str) -> bool:
        return capability == STRUCTURED_COMPLETION

    def complete(self, request):  # pragma: no cover - must never be reached
        raise AssertionError("an isolated request reached a transport that cannot isolate it")


def test_isolated_operations_are_refused_by_a_transport_that_cannot_isolate(tmp_path):
    with pytest.raises(AIProviderUnavailable):
        execute_structured_operation(_NoIsolation(), purpose="x", prompt="p", result_model=LinkJudgment, isolated=True)


def test_the_blind_grader_always_asks_for_an_isolated_turn(tmp_path):
    paths = build_diagnosis_vault(tmp_path / "vault")
    vault, _repository = seed_history(paths)
    item = vault.practice_items["pi_svd_compute_001"]
    context = blind_grading_context(vault, item, attempt_id="att_new", learner_answer_md="U Sigma V")
    with pytest.raises(AIProviderUnavailable):
        request_blind_grading_proposal(_NoIsolation(), context)
    client = ReviewFakeClient()
    request_blind_grading_proposal(client, context)
    assert client.isolated == [True]


def test_openai_chat_transports_are_isolated_by_construction():
    from learnloop.ai.providers.openai_chat import OpenAIChatProviderClient

    assert OpenAIChatProviderClient.supports(SimpleNamespace(profile=SimpleNamespace(input_modalities=[])), ISOLATED_TURN)


@needs_codex
def test_configured_mcp_servers_are_listed_and_disabled(tmp_path, layout, monkeypatch):
    """An MCP tool runs outside the command sandbox: every configured server is switched off."""

    workspace, vault, _sentinel = layout
    env = _codex_env(tmp_path)
    (Path(env["CODEX_HOME"]) / "config.toml").write_text('[mcp_servers.fsserver]\ncommand = "/bin/true"\n', encoding="utf-8")
    monkeypatch.setenv("CODEX_HOME", env["CODEX_HOME"])
    client = SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex"), sdk_codex_bin=CODEX), vault)
    servers = client._configured_mcp_server_ids(workspace)
    assert servers == ("fsserver",)
    args = [CODEX]
    for override in isolated_turn_overrides(workspace, shell=False, mcp_server_ids=servers):
        args += ["-c", override]
    listed = subprocess.run([*args, "mcp", "list", "--json"], cwd=workspace, env=env, capture_output=True, text=True, timeout=60)
    assert listed.returncode == 0, listed.stderr
    assert [server["enabled"] for server in json.loads(listed.stdout)] == [False]


def test_a_review_refuses_a_grader_or_diagnoser_that_cannot_isolate(tmp_path):
    from learnloop.ai.spend import SpendCaps
    from learnloop.diagnosis.offline_review.runner import ReviewClients, ReviewOptions, run_review

    class Leaky(ReviewFakeClient):
        def supports(self, capability: str) -> bool:
            return capability == STRUCTURED_COMPLETION

    paths = build_diagnosis_vault(tmp_path / "vault")
    vault, _repository = seed_history(paths)
    good, leaky = ReviewFakeClient(), Leaky()
    result = run_review(
        vault, source_sqlite=paths.sqlite_path, run_dir=tmp_path / "run", options=ReviewOptions(sample_size=2),
        clients=ReviewClients(grading=good, diagnosis=leaky, judge=leaky, generator=good), caps=SpendCaps(max_calls=500),
    )
    assert result["status"] == "unavailable"
    assert "diagnosis" in result["reason"] and "isolate" in result["reason"]
    assert result["client_notes"]["diagnosis_judge"].startswith("not ready")
    assert not (tmp_path / "run").exists()
    assert good.calls == [] and leaky.calls == []

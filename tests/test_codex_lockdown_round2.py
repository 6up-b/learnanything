"""Hardening round 2 of the Codex tool lockdown (orchestrator verify 20261021-113946-qZgmYP).

The verify of ``c80c54cbb..bc90f31ae`` found four configuration-dependent
Highs and one Low:

* H1: the fixed ``learnloop_isolated_turn`` permission profile was overlaid on
  the user's configuration, and Codex merges ``permissions.<name>`` tables
  recursively and honours a lower layer's ``extends``: ``extends =
  ":read-only"`` (full-disk read) or an extra read/write root in a user,
  profile or project layer widened every turn's sandbox;
* H2: a relative ``CODEX_HOME`` and a bare ``codex`` were fingerprinted from
  LearnLoop's own directory, while the subprocess resolves them from the
  turn's, so an edit to the home the turn really loads reused a stale check;
* H3: the legacy HTTP Codex transport (``provider = "http"``, the ``http`` /
  ``http_adapter`` profiles) bypassed the lockdown, and its runtime check could
  launch its ``startup_command``;
* H4: ``debug models --bundled`` validated a catalog the turn need not use: a
  ``model_catalog_json`` (or a remote catalog) could give the same model slug
  a tool (``experimental_supported_tools = ["test_sync_tool"]``);
* L5: the AST sweep had a textual prefilter, missed ``sdk.Codex(...)`` and
  turns on any name but ``thread``, and did not cover HTTP or subprocess
  launches.

Fakes and the installed CLI's non-model commands only (``debug prompt-input``,
``debug models``, ``mcp list``, ``features list``) under throwaway homes: no
model call.
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import pytest

from learnloop.ai.providers.codex import SdkCodexClient, isolated_turn_overrides
from learnloop.ai.transport import StructuredRequest
from learnloop.config import AIProviderConfig, CodexConfig
from learnloop.diagnosis.offline_review.judge import LinkJudgment

from tests.codex_cli_fakes import bundled_catalog, fake_codex_calls, write_fake_codex
from tests.project_support import install_fake_codex_sdk

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
CODEX = shutil.which("codex")
needs_codex = pytest.mark.skipif(CODEX is None, reason="the Codex CLI is not installed")
ANSWER = '{"links": []}'
OLD_PROFILE = "learnloop_isolated_turn"  # the fixed name every turn used before this round


def _lockdown():
    from learnloop.ai.providers import codex_lockdown

    return codex_lockdown


def _turn(client: SdkCodexClient, workspace: Path | None = None):
    return client.complete(StructuredRequest(purpose="tutor_qa", prompt="p", result_model=LinkJudgment,
                                             workspace=workspace))


def _launched(log: Path) -> list[list[str]]:
    return [call["overrides"] for call in fake_codex_calls(log) if call["command"][:1] == ["app-server"]]


def _probe_count(log: Path) -> int:
    return sum(1 for call in fake_codex_calls(log) if call["command"][:1] != ["app-server"])


def _client(tmp_path: Path, **config: Any) -> SdkCodexClient:
    vault_root = tmp_path / "vault"
    vault_root.mkdir(exist_ok=True)
    return SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex"), **config), vault_root)


# -- H1: the permission profile inherits nothing, and is read back ----------------------

_ENTRY = re.compile(r'<entry access="([^"]*)"><(path|special)>([^<]*)</(?:path|special)></entry>')


def _effective_entries(stdout: str) -> set[tuple[str, str]]:
    """(access, target) of every filesystem entry `debug prompt-input` renders (parsed here, not by the code under test)."""

    texts = [content.get("text", "") for message in json.loads(stdout) for content in message.get("content", [])]
    (profile,) = [text for text in texts if "<permission_profile" in text]
    return {(access, target) for access, _kind, target in _ENTRY.findall(profile)}


def _prompt_input(home: Path, cwd: Path, overrides: list[str], *before: str) -> str:
    args = [CODEX, *before]
    for override in overrides:
        args += ["-c", override]
    environ = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home.parent / "home"),
               "CODEX_HOME": str(home)}
    (home.parent / "home").mkdir(exist_ok=True)
    done = subprocess.run([*args, "debug", "prompt-input"], cwd=cwd, env=environ, capture_output=True, text=True,
                          timeout=60)
    assert done.returncode == 0, done.stderr
    return done.stdout


def _widening(name: str, write_root: Path) -> str:
    return (f'[permissions.{name}]\nextends = ":read-only"\n\n[permissions.{name}.filesystem]\n'
            f'"/usr/share" = "read"\n{json.dumps(str(write_root))} = "write"\n')


def _layered_home(tmp_path: Path, layer: str, name: str) -> tuple[Path, Path, tuple[str, ...]]:
    """A Codex home and turn directory where ``layer`` (user, profile or project) widens profile ``name``."""

    home = tmp_path / "codex-home"
    home.mkdir()
    turn = tmp_path / "turn"
    turn.mkdir()
    write_root = tmp_path / "writable"
    write_root.mkdir()
    before: tuple[str, ...] = ()
    if layer == "user":
        (home / "config.toml").write_text(_widening(name, write_root), encoding="utf-8")
    elif layer == "profile":
        (home / "config.toml").write_text("", encoding="utf-8")
        (home / "wide.config.toml").write_text(_widening(name, write_root), encoding="utf-8")
        before = ("--profile", "wide")
    else:  # a trusted project's own layer, in the turn's directory
        (home / "config.toml").write_text(f'[projects.{json.dumps(str(turn.resolve()))}]\ntrust_level = "trusted"\n',
                                          encoding="utf-8")
        (turn / ".codex").mkdir()
        (turn / ".codex" / "config.toml").write_text(_widening(name, write_root), encoding="utf-8")
    return home, turn, before


@needs_codex
@pytest.mark.parametrize("layer", ["user", "profile", "project"])
def test_a_lower_layer_cannot_widen_the_turns_permission_profile(tmp_path, layer):
    """H1 on the installed binary: a layer that defines the profile name every turn
    used (``extends = ":read-only"``, an extra read root, a write root) no longer
    reaches the turn's profile, which reads its directory and the platform minimum only."""

    home, turn, before = _layered_home(tmp_path, layer, OLD_PROFILE)
    entries = _effective_entries(_prompt_input(home, turn, isolated_turn_overrides(turn, shell=False), *before))
    assert ("read", ":root") not in entries, "an inherited extends gave the turn full-disk read"
    assert not [entry for entry in entries if entry[0] != "read"], entries
    assert ("read", "/usr/share") not in entries
    expected = {("read", str(turn.resolve())), ("read", ":minimal")}
    assert expected <= entries
    assert {target for _access, target in entries - expected} <= {
        target for _access, target in entries if "/tmp/arg0" in target}  # Codex's own helper directory


@needs_codex
@pytest.mark.parametrize("layer", ["user", "profile", "project"])
def test_a_layer_that_names_the_turns_profile_is_caught_by_the_readback(tmp_path, layer):
    """The verification behind the fresh name: a layer that did name it shows in
    the effective profile, and the launch check's readback refuses it."""

    from learnloop.ai.providers.codex_lockdown import ISOLATED_PROFILE, permission_profile_violations

    home, turn, before = _layered_home(tmp_path, layer, ISOLATED_PROFILE)
    stdout = _prompt_input(home, turn, isolated_turn_overrides(turn, shell=False), *before)
    problems = permission_profile_violations(stdout, root=turn, codex_home=home)
    assert any(":root" in problem for problem in problems), problems
    assert any(problem.startswith("write access") for problem in problems), problems
    # The same check with nothing widening it passes on the same binary.
    clean = tmp_path / "clean-home"
    clean.mkdir()
    plain = _prompt_input(clean, turn, isolated_turn_overrides(turn, shell=False))
    if layer != "project":  # the trusted project layer is in the turn directory itself
        assert permission_profile_violations(plain, root=turn, codex_home=clean) == []


@needs_codex
@pytest.mark.parametrize("layer", ["user", "project"])
def test_the_launch_check_refuses_a_widened_profile_before_any_turn(tmp_path, monkeypatch, layer):
    from learnloop.ai.providers.codex_lockdown import ISOLATED_PROFILE, CodexLockdownUnavailable

    home, turn, _before = _layered_home(tmp_path, layer, ISOLATED_PROFILE)
    monkeypatch.setenv("CODEX_HOME", str(home))
    client = _client(tmp_path, sdk_codex_bin=CODEX)
    with pytest.raises(CodexLockdownUnavailable, match="effective Codex permission profile"):
        client._verified_isolated_overrides(turn, shell=layer == "project")


@pytest.mark.parametrize(
    "spec, reason",
    [
        ({"permission_layers": {"*": {}}, "forced_permissions": {"filesystem": {":root": "read"}}}, ":root"),
        ({"forced_permissions": {"filesystem": {"/srv/vault": "write"}}}, "write access to /srv/vault"),
        ({"forced_permissions": {"filesystem": {"/home/learner": "read"}}}, "read access to /home/learner"),
        ({"forced_permissions": {"network_enabled": True}}, "network access restricted"),
    ],
    ids=["full-disk-read", "write-root", "read-root", "network"],
)
def test_a_profile_the_turn_did_not_pass_refuses_it_and_launches_nothing(tmp_path, monkeypatch, spec, reason):
    """H1 with a fake CLI: whatever layer widens the effective profile (one the
    fresh name cannot avoid, such as a managed one), the readback refuses."""

    program, log = write_fake_codex(tmp_path / "bin", **spec)
    captured = install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    with pytest.raises(_lockdown().CodexLockdownUnavailable, match=re.escape(reason)):
        _turn(_client(tmp_path, sdk_codex_bin=str(program)))
    assert _launched(log) == [] and "app_config" not in captured


def test_the_profile_name_is_fresh_and_never_the_fixed_one():
    lockdown = _lockdown()
    assert lockdown.ISOLATED_PROFILE != OLD_PROFILE
    assert re.fullmatch(r"learnloop_isolated_turn_[0-9a-f]{16}", lockdown.ISOLATED_PROFILE)
    overrides = isolated_turn_overrides(Path("/tmp"), shell=False)
    assert f'default_permissions="{lockdown.ISOLATED_PROFILE}"' in overrides
    assert not [override for override in overrides if f"permissions.{OLD_PROFILE}." in override]


def test_an_unreadable_or_missing_readback_refuses():
    lockdown = _lockdown()
    assert lockdown.permission_profile_violations("not json", root=Path("/tmp"), codex_home=Path("/h"))
    assert lockdown.permission_profile_violations("[]", root=Path("/tmp"), codex_home=Path("/h"))


# -- H2: CODEX_HOME and the executable as the subprocess resolves them ------------------


def test_a_relative_codex_home_is_resolved_from_the_turns_directory_and_pinned(tmp_path, monkeypatch):
    """H2: ``CODEX_HOME=../codex-home`` loads ``<turn>/../codex-home``. An MCP
    server added there must be pinned off on the next turn (the check ran
    again), and the app server gets the absolute home it was checked against."""

    program, log = write_fake_codex(tmp_path / "bin")
    captured = install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    client = _client(tmp_path, sdk_codex_bin=str(program))
    workspaces = {}
    for name in ("one", "two"):
        base = tmp_path / "turns" / name
        (base / "codex-home").mkdir(parents=True)
        (base / "codex-home" / "config.toml").write_text("", encoding="utf-8")
        workspaces[name] = base / "workspace"
        workspaces[name].mkdir()
    monkeypatch.setenv("CODEX_HOME", "../codex-home")
    monkeypatch.chdir(tmp_path)

    _turn(client, workspaces["one"])
    first = json.loads(captured["spawned"]["stdout"])
    home_one = (tmp_path / "turns" / "one" / "codex-home").resolve()
    assert first["servers_on"] == []

    (home_one / "config.toml").write_text('[mcp_servers.shell_bridge]\ncommand = "/bin/true"\n', encoding="utf-8")
    _turn(client, workspaces["one"])
    assert "mcp_servers.shell_bridge.enabled=false" in _launched(log)[-1], "the stale check left the new server on"
    assert json.loads(captured["spawned"]["stdout"])["servers_on"] == []
    # Pinned: the app server loads the absolute home the check ran against.
    assert captured["app_config"]["env"] == {"CODEX_HOME": str(home_one)}
    assert json.loads(captured["spawned"]["stdout"])["codex_home"] == str(home_one)

    # A turn in another directory loads (and is checked against) its own home.
    _turn(client, workspaces["two"])
    home_two = (tmp_path / "turns" / "two" / "codex-home").resolve()
    assert captured["app_config"]["env"] == {"CODEX_HOME": str(home_two)}
    assert "mcp_servers.shell_bridge.enabled=false" not in _launched(log)[-1]


def test_a_relative_codex_home_missing_from_the_turns_directory_refuses(tmp_path, monkeypatch):
    program, log = write_fake_codex(tmp_path / "bin")
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    (tmp_path / "codex-home").mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CODEX_HOME", "codex-home")  # exists beside LearnLoop, not beside the turn
    with pytest.raises(_lockdown().CodexLockdownUnavailable, match="CODEX_HOME"):
        _turn(_client(tmp_path, sdk_codex_bin=str(program)))
    assert _launched(log) == []


def test_a_bare_codex_launch_command_is_resolved_through_path_and_pinned(tmp_path, monkeypatch):
    """H2: ``sdk_launch_command = "codex app-server"`` runs the ``codex`` the
    child finds on ``PATH``. A different one on ``PATH`` must get its own
    check, and the launch names the absolute file the check ran."""

    home = tmp_path / "codex-home"
    home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(home))
    first, first_log = write_fake_codex(tmp_path / "bin-one")
    second, second_log = write_fake_codex(tmp_path / "bin-two", config_servers={"shell_bridge": True})
    captured = install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    client = _client(tmp_path, sdk_launch_command="codex app-server")
    monkeypatch.chdir(tmp_path)
    path = os.environ.get("PATH", "")
    monkeypatch.setenv("PATH", f"{first.parent}{os.pathsep}{path}")
    _turn(client)
    first_launch = captured["app_config"]["launch_args_override"][0]
    monkeypatch.setenv("PATH", f"{second.parent}{os.pathsep}{path}")
    _turn(client)
    assert _probe_count(second_log) > 0, "the other codex on PATH reused the first one's check"
    (launched,) = _launched(second_log)
    assert "mcp_servers.shell_bridge.enabled=false" in launched
    assert json.loads(captured["spawned"]["stdout"])["servers_on"] == []
    # Pinned: each launch names the absolute file its check ran.
    assert (first_launch, captured["app_config"]["launch_args_override"][0]) == (str(first), str(second))


def test_resolution_follows_the_child_not_this_process():
    lockdown = _lockdown()
    assert lockdown.resolve_executable("/bin/sh", {"PATH": ""}, Path("/")) == "/bin/sh"
    with pytest.raises(lockdown.CodexLockdownUnavailable):
        lockdown.resolve_executable("no-such-codex-binary", {"PATH": "/nonexistent"}, Path("/"))
    with pytest.raises(lockdown.CodexLockdownUnavailable):
        lockdown.resolve_codex_home({"HOME": "relative/home"}, Path("/"))
    assert lockdown.resolve_codex_home({"HOME": "/home/learner"}, Path("/tmp")) == (Path("/home/learner/.codex"), False)


# -- H3: the legacy HTTP transport is refused at every entry ---------------------------


def _http_profile(kind: str) -> AIProviderConfig:
    from learnloop.config.schema import CodexHTTPProviderConfig

    profile = CodexHTTPProviderConfig.model_validate({"type": "http", "base_url": "http://127.0.0.1:9",
                                                      "startup_command": "touch STARTED"})
    # ``http_adapter`` is normalized to ``http`` on load; the factory takes both spellings.
    return profile if kind == "http" else profile.model_copy(update={"type": kind})


def _no_network(monkeypatch) -> list[Any]:
    reached: list[Any] = []

    def refuse(*args, **kwargs):
        reached.append(args)
        raise AssertionError("the legacy HTTP transport reached the network")

    import urllib.request

    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    return reached


@pytest.mark.parametrize("kind", ["http", "http_adapter"])
def test_an_http_profile_is_refused_by_the_lockdown(tmp_path, monkeypatch, kind):
    from learnloop.ai.client import make_ai_provider_client_from_profile

    reached = _no_network(monkeypatch)
    with pytest.raises(_lockdown().CodexHttpTransportRefused, match="tool lockdown"):
        make_ai_provider_client_from_profile("codex_http", _http_profile(kind), tmp_path)
    assert reached == []


def test_the_legacy_provider_http_is_refused_by_the_lockdown(tmp_path):
    from learnloop.ai.providers.codex import make_codex_client
    from learnloop.ai.providers.codex_http import HttpAdapterProviderClient, HttpCodexClient

    for build in (lambda: make_codex_client(CodexConfig(provider="http"), tmp_path),
                  lambda: HttpCodexClient(CodexConfig(provider="http")),
                  lambda: HttpAdapterProviderClient("codex", _http_profile("http"))):
        with pytest.raises(_lockdown().CodexHttpTransportRefused, match="tool lockdown"):
            build()


@pytest.mark.parametrize("operation", sorted(
    ["authoring", "canonical_ingest", "grading", "tutor_qa", "teach_back", "teach_back_authoring",
     "misconception_match", "promotion_analysis"]))
def test_every_legacy_operation_is_refused_even_on_an_existing_client(monkeypatch, operation):
    """An adapter built before (any way at all) still refuses each of its eight
    operations, declares none, and never posts."""

    from learnloop.ai.providers import codex_lockdown
    from learnloop.ai.providers.codex_http import HttpCodexClient

    reached = _no_network(monkeypatch)
    with monkeypatch.context() as patch:
        patch.setattr(codex_lockdown, "refuse_legacy_http_transport", lambda where: None, raising=False)
        client = HttpCodexClient(CodexConfig(provider="http"))
    assert client.supports(operation) is False
    request = StructuredRequest(purpose=operation, prompt="p", result_model=LinkJudgment)
    with pytest.raises(codex_lockdown.CodexHttpTransportRefused, match="tool lockdown"):
        client.complete_legacy(request, context={"x": 1})
    with pytest.raises(codex_lockdown.CodexHttpTransportRefused):
        client._post("/grading-proposal", {}, purpose=operation)
    assert reached == []


def test_the_http_runtime_check_never_runs_its_health_request_or_startup_command(tmp_path, monkeypatch):
    from learnloop.ai.providers.codex import check_codex_runtime, default_http_healthcheck, default_startup
    from learnloop.ai.runtime import check_ai_runtime
    from learnloop.config import LearnLoopConfig

    reached = _no_network(monkeypatch)
    launched: list[Any] = []
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: launched.append(a) or (_ for _ in ()).throw(
        AssertionError("the startup command ran")))
    checkout = tmp_path / "codex"
    checkout.mkdir()
    (checkout / "HEAD").write_text("abc123", encoding="utf-8")
    calls: list[str] = []
    config = CodexConfig(provider="http", checkout_path=str(checkout), revision="abc123",
                         startup_command="touch STARTED")
    report = check_codex_runtime(tmp_path, config, healthcheck=lambda *_: calls.append("health"),
                                 startup=lambda *_: calls.append("startup"))
    assert report.status == "codex_unavailable" and "tool lockdown" in (report.message or "")
    assert calls == [] and launched == [] and reached == []
    for entry in (lambda: default_startup(checkout, config), lambda: default_http_healthcheck(checkout, config)):
        with pytest.raises(_lockdown().CodexHttpTransportRefused):
            entry()
    assert launched == [] and reached == [] and not (checkout / "STARTED").exists()

    learnloop = LearnLoopConfig.model_validate({"ai": {"active_provider": "codex", "providers": {
        "codex": {"type": "http", "checkout_path": str(checkout), "revision": "abc123",
                  "startup_command": "touch STARTED"}}}})
    runtime = check_ai_runtime(tmp_path, learnloop)
    assert runtime.status == "provider_unavailable" and "tool lockdown" in (runtime.message or "")
    assert launched == [] and reached == []


# -- H4: the turn uses exactly the catalog the check validated -------------------------

_TOOLED = bundled_catalog("gpt-5.6-sol", experimental_supported_tools=["test_sync_tool"])


def test_a_configured_catalog_cannot_give_the_turns_model_a_tool(tmp_path, monkeypatch):
    """H4 (the verify's case): a ``model_catalog_json`` of the user's gives the
    same slug ``experimental_supported_tools = ["test_sync_tool"]``. The turn is
    pinned to the validated bundled catalog, which the app server then serves."""

    program, log = write_fake_codex(tmp_path / "bin", user_catalog=_TOOLED)
    captured = install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    _turn(_client(tmp_path, sdk_codex_bin=str(program)))
    (launched,) = _launched(log)
    pinned = _lockdown().catalog_pin_path(launched)
    assert pinned is not None, "the turn was not pinned to the validated catalog"
    assert json.loads(Path(pinned).read_text(encoding="utf-8")) == bundled_catalog()
    assert json.loads(captured["spawned"]["stdout"])["experimental_tools"]["gpt-5.6-sol"] == []


def test_a_catalog_layer_that_beats_the_pin_refuses_the_turn(tmp_path, monkeypatch):
    program, log = write_fake_codex(tmp_path / "bin", forced_catalog=_TOOLED)
    captured = install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    with pytest.raises(_lockdown().CodexLockdownUnavailable, match="test sync tool|gpt-5.6-sol"):
        _turn(_client(tmp_path, sdk_codex_bin=str(program)))
    assert _launched(log) == [] and "app_config" not in captured


def test_a_cached_check_still_pins_the_validated_catalog(tmp_path, monkeypatch):
    home = tmp_path / "codex-home"
    home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(home))
    program, log = write_fake_codex(tmp_path / "bin", user_catalog=_TOOLED)
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    client = _client(tmp_path, sdk_codex_bin=str(program))
    _turn(client)
    probes = _probe_count(log)
    pinned = _lockdown().catalog_pin_path(_launched(log)[-1])
    Path(pinned).unlink()  # a temp cleaner took it
    _turn(client)
    assert _probe_count(log) == probes  # cached
    again = _lockdown().catalog_pin_path(_launched(log)[-1])
    assert json.loads(Path(again).read_text(encoding="utf-8")) == bundled_catalog()


@needs_codex
def test_the_installed_codex_serves_the_pinned_catalog_over_a_configured_one(tmp_path, monkeypatch):
    """H4 on the installed binary: the user config's ``model_catalog_json``
    (the bundled catalog with ``test_sync_tool`` added) loses to the pin."""

    home = tmp_path / "codex-home"
    home.mkdir()
    environ = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(tmp_path), "CODEX_HOME": str(home)}
    bundled = subprocess.run([CODEX, "debug", "models", "--bundled"], env=environ, capture_output=True, text=True,
                             timeout=60, cwd=tmp_path)
    assert bundled.returncode == 0, bundled.stderr
    catalog = json.loads(bundled.stdout)
    for entry in catalog["models"]:
        entry["experimental_supported_tools"] = ["test_sync_tool"]
    tooled = tmp_path / "tooled-catalog.json"
    tooled.write_text(json.dumps(catalog), encoding="utf-8")
    (home / "config.toml").write_text(f"model_catalog_json = {json.dumps(str(tooled))}\n", encoding="utf-8")
    monkeypatch.setenv("CODEX_HOME", str(home))
    turn = tmp_path / "turn"
    turn.mkdir()
    overrides = _client(tmp_path, sdk_codex_bin=CODEX)._verified_isolated_overrides(turn, shell=False)
    args = [CODEX]
    for override in overrides:
        args += ["-c", override]
    effective = subprocess.run([*args, "debug", "models"], env=environ, capture_output=True, text=True, timeout=60,
                               cwd=turn)
    assert effective.returncode == 0, effective.stderr
    tools = [entry.get("experimental_supported_tools") for entry in json.loads(effective.stdout)["models"]]
    assert ["test_sync_tool"] not in tools
    assert json.loads(effective.stdout) == json.loads(bundled.stdout)


# -- L5: the sweep over every place a Codex turn, app server or transport can start -----

_CONSTRUCTORS = {"Codex", "AsyncCodex", "CodexClient", "AsyncCodexClient"}
_THREAD_STARTERS = {"thread_start", "thread_resume", "thread_fork"}
_SDK_MODULES = ("openai_codex", "codex_cli_bin")
_SUBPROCESS_CALLS = {("subprocess", name) for name in ("Popen", "run", "call", "check_call", "check_output")} | {
    ("os", name) for name in ("system", "execv", "execve", "execvp", "execvpe", "execl", "execlp", "spawnv",
                              "spawnve", "spawnvp", "posix_spawn", "posix_spawnp")} | {
    ("asyncio", "create_subprocess_exec"), ("asyncio", "create_subprocess_shell")}
_HTTP_CALLS = {"urlopen", "Request", "HTTPConnection", "HTTPSConnection", "post", "get", "request"}
_CODEXISH = re.compile(r"codex|startup_command|sdk_launch|launch_args", re.I)
#: The one locked-down turn and the launch check's probes; the refused HTTP startup.
_TURN_OWNER = ("learnloop/ai/providers/codex.py", "_run_verified_sdk_turn")
_LAUNCH_OWNERS = {("learnloop/ai/providers/codex.py", "_codex_probe"),
                  ("learnloop/ai/providers/codex.py", "default_startup")}


def _dotted(node: ast.AST) -> list[str]:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return parts[::-1]


class _Sweep(ast.NodeVisitor):
    """One module: SDK aliases, turn and thread starts, SDK constructions,
    subprocess launches that mention Codex, and HTTP calls, each with its
    enclosing function."""

    def __init__(self, relative: str):
        self.relative = relative
        self.stack: list[str] = []
        self.sdk_modules: set[str] = set()  # names bound to an SDK module
        self.sdk_names: dict[str, str] = {}  # local name -> SDK member
        self.thread_vars: set[tuple[str, str]] = set()  # (function, name) bound to a thread
        self.turn_vars: set[tuple[str, str]] = set()  # (function, name) bound to a turn
        self.starters: list[tuple[str, int, str, bool]] = []
        self.constructions: list[tuple[str, int, str]] = []
        self.launches: list[tuple[str, int, str]] = []
        self.http: list[tuple[str, int, str]] = []
        self.refusals: dict[str, list[int]] = {}
        self.sdk_imports: list[tuple[str, int, str]] = []
        self.http_adapter_imports: list[tuple[str, int, str]] = []

    @property
    def owner(self) -> str:
        return self.stack[-1] if self.stack else "<module>"

    def _function(self, node):
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    visit_FunctionDef = visit_AsyncFunctionDef = _function

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.split(".")[0] in _SDK_MODULES:
                self.sdk_modules.add(alias.asname or alias.name.split(".")[0])
                self.sdk_imports.append((self.relative, node.lineno, self.owner))
            if alias.name == "learnloop.ai.providers.codex_http":
                self.http_adapter_imports.append((self.relative, node.lineno, self.owner))
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ""
        if module.split(".")[0] in _SDK_MODULES:
            self.sdk_imports.append((self.relative, node.lineno, self.owner))
            for alias in node.names:
                self.sdk_names[alias.asname or alias.name] = alias.name
        if module == "learnloop.ai.providers.codex_http" or (
                module == "learnloop.ai.providers" and any(alias.name == "codex_http" for alias in node.names)):
            self.http_adapter_imports.append((self.relative, node.lineno, self.owner))
        self.generic_visit(node)

    def visit_Assign(self, node):
        value = node.value
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if value.func.attr in _THREAD_STARTERS:
                        self.thread_vars.add((self.owner, target.id))
                    elif value.func.attr == "turn":
                        self.turn_vars.add((self.owner, target.id))
        self.generic_visit(node)

    def visit_Call(self, node):
        func = node.func
        dotted = _dotted(func)
        where = (self.relative, node.lineno, self.owner)
        if dotted and dotted[-1] == "refuse_legacy_http_transport":
            self.refusals.setdefault(self.owner, []).append(node.lineno)
        if isinstance(func, ast.Attribute) and func.attr in _THREAD_STARTERS | {"turn", "run_turn"}:
            self.starters.append((*where, _passes_deny_all(node)))
        elif isinstance(func, ast.Attribute) and func.attr == "run" and isinstance(func.value, ast.Name):
            receiver = (self.owner, func.value.id)
            if receiver in self.thread_vars:  # Thread.run(input) starts a turn
                self.starters.append((*where, _passes_deny_all(node)))
            elif receiver in self.turn_vars:
                self.starters.append((*where, True))
        constructed = None
        if isinstance(func, ast.Name):
            constructed = self.sdk_names.get(func.id, func.id)
        elif len(dotted) >= 2 and dotted[0] in self.sdk_modules:
            constructed = dotted[-1]
        if constructed in _CONSTRUCTORS:
            self.constructions.append(where)
        if len(dotted) >= 2 and (dotted[-2], dotted[-1]) in _SUBPROCESS_CALLS:
            mentioned = " ".join(
                getattr(part, "id", "") or getattr(part, "attr", "") or
                (part.value if isinstance(part, ast.Constant) and isinstance(part.value, str) else "")
                for argument in [*node.args, *(keyword.value for keyword in node.keywords)]
                for part in ast.walk(argument))
            if _CODEXISH.search(mentioned):
                self.launches.append(where)
        if (isinstance(func, ast.Name) and func.id in {"urlopen", "Request", "HTTPConnection", "HTTPSConnection"}) or (
                len(dotted) >= 2 and dotted[-1] in _HTTP_CALLS
                and dotted[-2] in {"request", "urllib", "client", "requests", "httpx"}):
            self.http.append(where)
        self.generic_visit(node)


def _passes_deny_all(call: ast.Call) -> bool:
    for keyword in call.keywords:
        if keyword.arg == "approval_mode":
            return _dotted(keyword.value)[-1:] == ["deny_all"]
    return False


def _sweep_source(text: str, relative: str = "snippet.py") -> _Sweep:
    sweep = _Sweep(relative)
    sweep.visit(ast.parse(text))
    return sweep


def _sweep_tree() -> list[_Sweep]:
    roots = [SRC / "learnloop", SRC / "learnloop_sidecar", SRC / "learnloop_mobile", SRC / "learnloop_mcp"]
    paths = sorted(path for root in roots if root.is_dir() for path in root.rglob("*.py")
                   if "__pycache__" not in path.parts)
    assert len(paths) > 100
    return [_sweep_source(path.read_text(encoding="utf-8"), str(path.relative_to(SRC))) for path in paths]


def test_the_sweep_sees_aliases_qualified_constructors_and_turns_on_any_name():
    """The detector itself (the Low): no prefilter can skip these, an import
    alias resolves, and a turn on a variable of any name counts."""

    sweep = _sweep_source(
        "import openai_codex as sdk\n"
        "from openai_codex import Codex as C\n"
        "def f(cfg, deny_all):\n"
        "    a = sdk.Codex(config=cfg)\n"
        "    b = C(config=cfg)\n"
        "    c = sdk.client.CodexClient(cfg)\n"
        "    t = a.thread_start(approval_mode=deny_all)\n"
        "    t.run('prompt')\n"
        "    whatever = t.turn('p')\n"
        "    whatever.run()\n"
        "    import subprocess\n"
        "    subprocess.Popen([cfg.codex_bin, 'app-server'])\n"
        "    import urllib.request\n"
        "    urllib.request.urlopen(cfg.base_url)\n"
    )
    assert [line for _path, line, _owner in sweep.constructions] == [4, 5, 6]
    assert [(line, ok) for _path, line, _owner, ok in sweep.starters] == [(7, True), (8, False), (9, False), (10, True)]
    assert [line for _path, line, _owner in sweep.launches] == [12]
    assert [line for _path, line, _owner in sweep.http] == [14]
    assert len(sweep.sdk_imports) == 2


def test_every_codex_turn_app_server_and_transport_in_the_source_is_the_locked_down_one():
    """L5: over every module of every package (no textual prefilter), every SDK
    construction, thread or turn start (on any name, ``Thread.run`` included)
    sits in the one locked-down turn and passes ``deny_all``; every subprocess
    launch that names Codex is the launch check's probe or the refused HTTP
    startup; every HTTP call in a Codex provider module, and every import of
    the HTTP adapter, comes after the lockdown's refusal in its function; and
    only the Codex provider imports the SDK."""

    sweeps = _sweep_tree()
    starters = [item for sweep in sweeps for item in sweep.starters]
    constructions = [item for sweep in sweeps for item in sweep.constructions]
    assert starters and constructions
    assert {(path, owner) for path, _line, owner, _ok in starters} == {_TURN_OWNER}, starters
    assert [item for item in starters if not item[3]] == [], "a thread/turn start without approval_mode=deny_all"
    assert {(path, owner) for path, _line, owner in constructions} == {_TURN_OWNER}, constructions
    launches = [item for sweep in sweeps for item in sweep.launches]
    assert {(path, owner) for path, _line, owner in launches} <= _LAUNCH_OWNERS, launches
    assert {path for sweep in sweeps for path, _line, _owner in sweep.sdk_imports} == {
        "learnloop/ai/providers/codex.py"}

    by_path = {sweep.relative: sweep for sweep in sweeps}
    unrefused: list[tuple[str, int, str]] = []
    for sweep in sweeps:
        checked = list(sweep.http_adapter_imports)
        if Path(sweep.relative).name.startswith("codex") and "providers" in sweep.relative:
            checked += sweep.http
        if sweep.relative == "learnloop/ai/providers/codex.py":
            checked += [item for item in sweep.launches if item[2] == "default_startup"]
        for path, line, owner in checked:
            if path == "learnloop/ai/providers/codex.py" and owner == "<module>":
                continue
            if not any(earlier < line for earlier in by_path[path].refusals.get(owner, [])):
                unrefused.append((path, line, owner))
    assert unrefused == [], f"an HTTP call or adapter import before the lockdown's refusal: {unrefused}"
    # The adapter's own entries: construction, supports, each operation, the POST.
    adapter = by_path["learnloop/ai/providers/codex_http.py"]
    assert {"__init__", "supports", "complete_legacy", "_post"} <= set(adapter.refusals)


def test_only_the_codex_provider_may_import_the_sdk_by_import_contract():
    """L5: an import-linter contract keeps the SDK and its bundled CLI to the
    Codex provider (``uv run lint-imports`` enforces it in every gate)."""

    linter = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["importlinter"]
    assert linter["include_external_packages"] is True
    (contract,) = [entry for entry in linter["contracts"] if entry["id"] == "codex-sdk-only-in-its-provider"]
    assert contract["type"] == "forbidden"
    assert set(contract["source_modules"]) == set(linter["root_packages"])
    assert set(contract["forbidden_modules"]) == {"openai_codex", "codex_cli_bin"}
    assert set(contract["ignore_imports"]) == {"learnloop.ai.providers.codex -> openai_codex",
                                              "learnloop.ai.providers.codex -> codex_cli_bin"}

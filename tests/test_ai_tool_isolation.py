"""Tool isolation is enforced by the OS, not the prompt (project-understanding F2).

These tests run real processes under bubblewrap and try to read what an
isolated model call must never see: a vault's project store, a repository,
another file in the home directory, the agent's own session transcripts and
host processes. A payload-recording fake cannot show any of this.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest

from learnloop.ai.isolation import (
    ToolIsolation,
    ToolIsolationUnavailable,
    isolation_unavailable_reason,
    sandboxed_command,
    write_launcher,
)


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


@pytest.fixture
def layout(tmp_path):
    vault = tmp_path / "vault"
    (vault / "projects").mkdir(parents=True)
    (vault / "projects" / "project_store.sqlite").write_text("REFERENCE ANSWER", encoding="utf-8")
    (vault / "state.sqlite").write_text("LEARNER RECORDS", encoding="utf-8")
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "model.py").write_text("SOURCE CODE", encoding="utf-8")
    home = tmp_path / "agent-home"
    (home / "sessions").mkdir(parents=True)
    (home / "sessions" / "rollout.jsonl").write_text("AGENT TRANSCRIPT", encoding="utf-8")
    (home / "history.jsonl").write_text("AGENT HISTORY", encoding="utf-8")
    (home / "auth.json").write_text('{"token": "t"}', encoding="utf-8")
    (home / "config.toml").write_text('model = "m"\n', encoding="utf-8")
    workdir = tmp_path / "workdir"
    workdir.mkdir()
    return {"vault": vault, "repo": repo, "home": home, "workdir": workdir}


def _run(layout, script: str) -> subprocess.CompletedProcess:
    isolation = ToolIsolation(workdir=layout["workdir"], hidden=(layout["vault"], layout["repo"]))
    command = sandboxed_command(isolation, ["sh", "-c", script], home=layout["home"])
    return subprocess.run(command, capture_output=True, text=True, timeout=30)


@requires_bwrap
@pytest.mark.parametrize(
    "target",
    [
        "vault/projects/project_store.sqlite",
        "vault/state.sqlite",
        "repo/model.py",
        "agent-home/sessions/rollout.jsonl",
        "agent-home/history.jsonl",
    ],
)
def test_out_of_scope_reads_fail(layout, target):
    path = layout["vault"].parent / target
    assert path.is_file()
    result = _run(layout, f"cat '{path}'")
    assert result.returncode != 0
    assert path.read_text(encoding="utf-8") not in result.stdout


@requires_bwrap
def test_only_mount_points_exist_and_host_processes_are_absent(layout):
    parent = layout["vault"].parent
    result = _run(layout, f"ls -A '{parent}'; echo ---; ls /proc | grep -c '^[0-9]'")
    listing, processes = result.stdout.split("---")
    # The real directory also holds the vault and the repo; the sandbox only
    # has the empty skeleton leading to its two bind mounts.
    assert sorted(listing.split()) == ["agent-home", "workdir"]
    assert int(processes) < 10  # the sandbox init and this pipeline, never the host


@requires_bwrap
def test_the_agent_keeps_its_credentials_and_its_working_directory(layout):
    result = subprocess.run(
        sandboxed_command(
            ToolIsolation(workdir=layout["workdir"]),
            ["sh", "-c", 'cat "$1"; echo; pwd; echo note > scratch.txt && echo wrote', "sh",
             str(layout["home"] / "auth.json")],
            home=layout["home"],
        ),
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert '{"token": "t"}' in result.stdout
    assert str(layout["workdir"].resolve()) in result.stdout and "wrote" in result.stdout
    assert (layout["workdir"] / "scratch.txt").read_text(encoding="utf-8") == "note\n"


@requires_bwrap
def test_a_launcher_passes_its_arguments_through_the_sandbox(layout, tmp_path):
    tools = tmp_path / "tools"
    tools.mkdir()
    agent = tools / "agent"
    store = layout["vault"] / "projects" / "project_store.sqlite"
    agent.write_text(f"#!/bin/sh\necho args:$*\ncat '{store}' || echo blocked\n", encoding="utf-8")
    agent.chmod(0o755)
    launcher = write_launcher(tmp_path, ToolIsolation(workdir=layout["workdir"]), str(agent), home=layout["home"])
    result = subprocess.run([str(launcher), "app-server", "--listen", "stdio://"], capture_output=True, text=True, timeout=30)
    assert "args:app-server --listen stdio://" in result.stdout
    assert "REFERENCE ANSWER" not in result.stdout and "blocked" in result.stdout


def test_isolation_fails_closed_without_bubblewrap(monkeypatch, tmp_path):
    monkeypatch.setattr("learnloop.ai.isolation.shutil.which", lambda _name: None)
    assert "bubblewrap" in (isolation_unavailable_reason() or "")
    with pytest.raises(ToolIsolationUnavailable):
        sandboxed_command(ToolIsolation(workdir=tmp_path), ["true"])


# --- the project runtime and the Codex transport -------------------------------------


from learnloop.ai.errors import AIProviderUnavailable  # noqa: E402
from learnloop.ai.isolation import current_tool_isolation, tool_isolation  # noqa: E402
from learnloop.ai.spend import SpendCaps  # noqa: E402
from learnloop.config import LearnLoopConfig  # noqa: E402
from learnloop.projects import ai_runtime  # noqa: E402
from learnloop.projects.ai_contracts import ProbeGrade, ProbeGrades  # noqa: E402
from learnloop.projects.ai_runtime import PaidCalls, ProjectRoute, project_routes  # noqa: E402
from learnloop.projects.experiment_store import ProjectStore  # noqa: E402

CAPS = SpendCaps(max_candidates=10, max_pairs=0, max_retries=1, max_calls=10, max_total_tokens=10**6, max_estimated_usd=10.0)
GRADES = ProbeGrades(grades=[ProbeGrade(id="a1", verdict="correct", score=1.0, feedback="")])


class _Agent:
    """An agentic transport; ``confinable`` says whether it can honour isolation."""

    provider_name = "agent"
    provider_type = "codex_sdk"
    model = "m"

    def __init__(self, *, confinable: bool):
        self.confinable = confinable
        self.seen = []

    def supports(self, capability):
        return capability == "structured_completion" or (self.confinable and capability == "tool_isolation")

    def complete(self, request):
        self.seen.append(current_tool_isolation())
        return GRADES


def _route(client, **extra):
    return ProjectRoute(role="grading", task="grading", provider_name="agent", provider_type="codex_sdk",
                        model="m", subscription=True, ready=True, message=None, client=client, **extra)


def test_an_unconfinable_agent_is_refused_before_any_request(tmp_path):
    store = ProjectStore.for_vault(tmp_path)
    agent = _Agent(confinable=False)
    with pytest.raises(AIProviderUnavailable, match="cannot confine"):
        PaidCalls(store, caps=CAPS, run_id="r").call(_route(agent), purpose="project_probe_grading", prompt="x",
                                                     result_model=ProbeGrades, output_tokens=10)
    assert agent.seen == [] and store.receipts() == []


@requires_bwrap
def test_a_confinable_agent_runs_inside_the_isolation(tmp_path):
    store = ProjectStore.for_vault(tmp_path / "vault")
    agent = _Agent(confinable=True)
    isolation = ai_runtime.ToolIsolation(workdir=tmp_path, hidden=(tmp_path / "vault",))
    PaidCalls(store, caps=CAPS, run_id="r").call(_route(agent, isolation=isolation), purpose="project_probe_grading",
                                                 prompt="x", result_model=ProbeGrades, output_tokens=10)
    assert agent.seen == [isolation]
    (receipt,) = [row for row in store.receipts() if row["parent_call_id"] is None]
    assert '"tool_isolation": "bubblewrap"' in receipt["disclosure_json"]


def test_the_kill_switch_runs_unconfined_and_says_so(tmp_path):
    store = ProjectStore.for_vault(tmp_path)
    agent = _Agent(confinable=False)
    PaidCalls(store, caps=CAPS, run_id="r", require_tool_isolation=False).call(
        _route(agent), purpose="project_probe_grading", prompt="x", result_model=ProbeGrades, output_tokens=10,
    )
    assert agent.seen == [None]
    (receipt,) = store.receipts()
    assert '"tool_isolation": "none"' in receipt["disclosure_json"]


def test_project_routes_mark_an_unconfinable_agent_not_ready(monkeypatch, tmp_path):
    agent = _Agent(confinable=False)
    monkeypatch.setattr(ai_runtime, "_route_resolver", lambda workdir, config, role: _route(agent))
    config = LearnLoopConfig()
    with project_routes(tmp_path, config, ("grading",)) as routes:
        assert routes["grading"].ready is False
        assert "require_tool_isolation" in routes["grading"].message
    config.project.require_tool_isolation = False
    with project_routes(tmp_path, config, ("grading",)) as routes:
        assert routes["grading"].ready and routes["grading"].tool_isolation == "none"


@requires_bwrap
def test_project_routes_give_a_confinable_agent_the_vault_and_repos_as_hidden(monkeypatch, tmp_path):
    agent = _Agent(confinable=True)
    monkeypatch.setattr(ai_runtime, "_route_resolver", lambda workdir, config, role: _route(agent))
    with project_routes(tmp_path / "vault", LearnLoopConfig(), ("grading",), hidden=[tmp_path / "repo"]) as routes:
        route = routes["grading"]
        assert route.tool_isolation == "bubblewrap"
        assert route.isolation.hidden == (tmp_path / "vault", tmp_path / "repo")
        assert route.isolation.workdir.is_dir() and not any(route.isolation.workdir.iterdir())


@requires_bwrap
def test_the_codex_app_server_launches_inside_the_sandbox(monkeypatch, layout, tmp_path):
    from learnloop.ai.providers.codex import CodexSDKProviderClient
    from tests.project_support import install_fake_codex_sdk

    monkeypatch.setenv("CODEX_HOME", str(layout["home"]))
    store_file = layout["vault"] / "projects" / "project_store.sqlite"
    tools = tmp_path / "tools"
    tools.mkdir()
    agent = tools / "codex"
    agent.write_text(
        "#!/bin/sh\n"
        f"echo args:$*\necho cwd:$(pwd)\n"
        f"cat '{store_file}' 2>/dev/null || echo store-blocked\n"
        f"cat '{layout['repo'] / 'model.py'}' 2>/dev/null || echo repo-blocked\n"
        f"cat '{layout['home'] / 'sessions' / 'rollout.jsonl'}' 2>/dev/null || echo transcript-blocked\n",
        encoding="utf-8",
    )
    agent.chmod(0o755)
    captured = install_fake_codex_sdk(monkeypatch, spawn=True, final_response='{"grades": []}')
    profile = LearnLoopConfig().ai.providers["codex_low"].model_copy(update={"sdk_codex_bin": str(agent)})
    client = CodexSDKProviderClient("codex_low", profile, layout["workdir"])
    isolation = ToolIsolation(workdir=layout["workdir"], hidden=(layout["vault"], layout["repo"]))
    with tool_isolation(isolation):
        client._run_structured("p", {"type": "object"}, purpose="project_closed_book_check")
    out = captured["spawned"]["stdout"]
    assert "args:app-server --listen stdio://" in out
    assert f"cwd:{layout['workdir'].resolve()}" in out
    assert {"store-blocked", "repo-blocked", "transcript-blocked"} <= set(out.split())
    assert "REFERENCE ANSWER" not in out and "SOURCE CODE" not in out and "AGENT TRANSCRIPT" not in out
    assert captured["thread_start"]["cwd"] == str(layout["workdir"])
    # Without the isolation the same launch reads everything: the sandbox is what blocks it.
    client._run_structured("p", {"type": "object"}, purpose="project_closed_book_check")
    assert "REFERENCE ANSWER" in captured["spawned"]["stdout"]


def test_codex_refuses_an_isolated_request_without_bubblewrap(monkeypatch, tmp_path):
    from learnloop.ai.errors import CodexUnavailable
    from learnloop.ai.providers.codex import CodexSDKProviderClient
    from tests.project_support import install_fake_codex_sdk

    captured = install_fake_codex_sdk(monkeypatch)
    monkeypatch.setattr("learnloop.ai.isolation.bubblewrap_path", lambda: None)
    client = CodexSDKProviderClient("codex_low", LearnLoopConfig().ai.providers["codex_low"], tmp_path)
    with tool_isolation(ToolIsolation(workdir=tmp_path)), pytest.raises(CodexUnavailable, match="bubblewrap"):
        client._run_structured("p", {"type": "object"}, purpose="project_closed_book_check")
    assert "app_config" not in captured  # nothing was launched


# --- the agent's own run state stays private (fix-codex-sandbox) -----------------------------

# Writes where the real Codex 0.161 app-server writes, observed from inside the
# sandbox during a live turn (docs/reviews/fix-codex-sandbox.md). Startup opens
# installation_id read-write even when it exists: a read-only bind of it failed
# every live launch with "Error: Read-only file system (os error 30)". Like
# Codex, it puts its databases under config.toml's ``sqlite_home`` (relative to
# the file), else ``$CODEX_SQLITE_HOME`` (relative to the working directory),
# else ``$CODEX_HOME``, and writes a rollout trace under
# ``$CODEX_ROLLOUT_TRACE_ROOT`` when that is set. Both were observed in a
# credential-free real startup (Codex review F2,
# docs/reviews/fix-codex-sandbox-codex-review.md).
_CODEX_LIKE_APP_SERVER = r"""#!/bin/sh
home="${CODEX_HOME:-$HOME/.codex}"
fail() { echo "Error: $1" >&2; exit 1; }
echo "seen-id:$(cat "$home/installation_id" 2>/dev/null)"
echo "seen-history:$(cat "$home/history.jsonl" 2>/dev/null)"
printf '' 1<>"$home/installation_id" || fail "installation_id: Read-only file system (os error 30)"
[ -s "$home/installation_id" ] || printf 'sandbox-id\n' 1<>"$home/installation_id" || fail "installation_id"
configured=$(sed -n 's/^sqlite_home *= *"\(.*\)"$/\1/p' "$home/config.toml" 2>/dev/null)
case "$configured" in
  "") sqlite_home="${CODEX_SQLITE_HOME:-$home}" ;;
  /*) sqlite_home="$configured" ;;
  *) sqlite_home="$home/$configured" ;;
esac
mkdir -p "$sqlite_home" 2>/dev/null || fail "failed to initialize sqlite state runtime under $sqlite_home"
for db in state_5 logs_2 goals_1 memories_1 queue_1 thread_history_1; do
  for suffix in "" -wal -shm; do
    printf 'SANDBOX STATE' > "$sqlite_home/$db.sqlite$suffix" || fail "$db.sqlite$suffix"
  done
done
if [ -n "$CODEX_ROLLOUT_TRACE_ROOT" ]; then
  mkdir -p "$CODEX_ROLLOUT_TRACE_ROOT/trace-x" || fail "rollout trace"
  printf 'SANDBOX TRACE' > "$CODEX_ROLLOUT_TRACE_ROOT/trace-x/trace.jsonl" || fail "rollout trace"
fi
for dir in skills/.system tmp/arg0/codex-arg0x sessions/2026/10/12 shell_snapshots thread-writer-locks \
           mcp-oauth-locks cache/codex_apps_tools plugins/cache; do
  mkdir -p "$home/$dir" || fail "$dir"
done
for file in tmp/arg0/codex-arg0x/.lock thread-writer-locks/.coordination.lock mcp-oauth-locks/file-store.lock \
            skills/.system/.codex-system-skills.marker shell_snapshots/s.sh cache/codex_apps_tools/t.json \
            models_cache.json .sandbox_migration; do
  printf 'SANDBOX STATE' > "$home/$file" || fail "$file"
done
printf 'SANDBOX TRANSCRIPT\n' > "$home/sessions/2026/10/12/rollout-x.jsonl" || fail "session rollout"
printf 'scratch' > "${TMPDIR:-/tmp}/codex-scratch" || fail "TMPDIR"
printf '{"token": "refreshed"}' > "$home/auth.json" || fail "auth.json"
cat "$home/config.toml" > /dev/null || fail "config.toml is unreadable"
if (printf '#' >> "$home/config.toml") 2>/dev/null; then fail "config.toml is writable"; fi
echo answer > answer.txt || fail "working directory"
echo app-server-ready
"""


def _tree(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): path.read_text(encoding="utf-8") if path.is_file() else "<dir>"
        for path in sorted(root.rglob("*"))
    }


def _launch_codex_like(monkeypatch, tmp_path, *, home: Path, workdir: Path, hidden=(), launch="sdk_codex_bin"):
    """Run the Codex-like app-server through the real provider launch path, isolated.

    ``CodexSDKProviderClient._run_structured`` under ``tool_isolation``, then
    ``_isolated_launch``, then ``write_launcher`` or ``sandboxed_command``, then
    bwrap. Returns what the fake SDK captured and the provider error, if any.
    """

    import shlex

    from learnloop.ai.providers.codex import CodexSDKProviderClient
    from tests.project_support import install_fake_codex_sdk

    monkeypatch.setenv("CODEX_HOME", str(home))
    agent = _script(tmp_path / "tools" / "codex", _CODEX_LIKE_APP_SERVER.removeprefix("#!/bin/sh\n"))
    update = ({"sdk_codex_bin": str(agent)} if launch == "sdk_codex_bin"
              else {"sdk_launch_command": f"{shlex.quote(str(agent))} app-server --listen stdio://"})
    profile = LearnLoopConfig().ai.providers["codex_low"].model_copy(update=update)
    captured = install_fake_codex_sdk(monkeypatch, spawn=True, final_response='{"grades": []}')
    client = CodexSDKProviderClient("codex_low", profile, workdir)
    error = None
    with tool_isolation(ToolIsolation(workdir=workdir, hidden=tuple(hidden))):
        try:
            client._run_structured("p", {"type": "object"}, purpose="project_closed_book_check")
        except AIProviderUnavailable as exc:
            error = exc
    return captured, error


def _host_home_unchanged(before: dict[str, str], after: dict[str, str], *, refreshed: bool) -> bool:
    before, after = dict(before), dict(after)
    if refreshed:  # a token refresh persists; nothing else does
        assert after.pop("auth.json") == '{"token": "refreshed"}'
        before.pop("auth.json")
    return after == before


@requires_bwrap
@pytest.mark.parametrize("launch", ["sdk_codex_bin", "sdk_launch_command"])
def test_the_app_server_keeps_its_run_state_in_a_private_home(monkeypatch, layout, tmp_path, launch):
    home = layout["home"]
    (home / "installation_id").write_text("HOST-INSTALLATION-ID\n", encoding="utf-8")
    host_home_before = _tree(home)
    hidden_before = {name: _tree(layout[name]) for name in ("vault", "repo")}
    captured, error = _launch_codex_like(monkeypatch, tmp_path, home=home, workdir=layout["workdir"],
                                         hidden=(layout["vault"], layout["repo"]), launch=launch)

    assert error is None
    spawned = captured["spawned"]
    assert spawned["returncode"] == 0, spawned["stderr"]
    assert "app-server-ready" in spawned["stdout"] and "Read-only" not in spawned["stderr"]
    # The sandbox starts from an empty home: the host's id and history are not visible ...
    assert "seen-id:\n" in spawned["stdout"] and "HOST-INSTALLATION-ID" not in spawned["stdout"]
    assert "seen-history:\n" in spawned["stdout"] and "AGENT HISTORY" not in spawned["stdout"]
    # ... and its run state, transcript included, never reaches the host.
    assert _host_home_unchanged(host_home_before, _tree(home), refreshed=True)
    assert {name: _tree(layout[name]) for name in ("vault", "repo")} == hidden_before
    assert not (Path("/tmp") / "codex-scratch").exists()
    # The working directory holds the agent's output and nothing else.
    assert _tree(layout["workdir"]) == {"answer.txt": "answer\n"}


# --- a later mount never uncovers the private home (Codex review F1) ---------------------------


def _attempt(isolation: ToolIsolation, script: str, *, home: Path):
    """``(refusal, result)``: the sandbox refuses the layout, or runs ``script`` in it."""

    try:
        command = sandboxed_command(isolation, ["sh", "-c", script], home=home)
    except ToolIsolationUnavailable as exc:
        return exc, None
    return None, subprocess.run(command, capture_output=True, text=True, timeout=30)


def _agent_home_with_history(home: Path) -> Path:
    home.mkdir(parents=True, exist_ok=True)
    (home / "history.jsonl").write_text("AGENT HISTORY", encoding="utf-8")
    (home / "installation_id").write_text("HOST-INSTALLATION-ID\n", encoding="utf-8")
    (home / "auth.json").write_text('{"token": "t"}', encoding="utf-8")
    return home


@requires_bwrap
@pytest.mark.parametrize("home_at", ["workdir/.codex", "workdir"])
def test_a_working_directory_that_holds_the_agent_home_is_refused(tmp_path, home_at):
    # The working directory is bound after the in-memory home, so it would put
    # the host's home (history, transcripts, installation_id) back on top of it.
    workdir = tmp_path / "workdir"
    workdir.mkdir()
    home = _agent_home_with_history(tmp_path / home_at)
    script = f"cat '{home}/history.jsonl'; printf 'SANDBOX-ID\\n' > '{home}/installation_id'"
    refusal, result = _attempt(ToolIsolation(workdir=workdir), script, home=home)
    assert result is None or "AGENT HISTORY" not in result.stdout
    assert (home / "installation_id").read_text(encoding="utf-8") == "HOST-INSTALLATION-ID\n"
    assert refusal is not None and "contains the agent home" in str(refusal)


@requires_bwrap
@pytest.mark.skipif(__import__("shutil").which("node") is None, reason="needs node for a Node launcher")
def test_an_executable_package_that_holds_the_agent_home_is_refused(layout, tmp_path):
    # A Node launcher's whole package is bound (read-only) after the in-memory
    # home, so an agent home inside that package would be the host's again.
    package = tmp_path / "package"
    (package / "package.json").parent.mkdir()
    (package / "package.json").write_text("{}", encoding="utf-8")
    home = _agent_home_with_history(package / "agent-home")
    launcher = package / "bin" / "agent.js"
    launcher.parent.mkdir()
    launcher.write_text(
        "#!/usr/bin/env node\n"
        "const fs = require('fs');\n"
        "try { console.log(fs.readFileSync(process.argv[2], 'utf8')); } catch (e) { console.log('blocked'); }\n",
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    try:
        command = sandboxed_command(ToolIsolation(workdir=layout["workdir"]),
                                    [str(launcher), str(home / "history.jsonl")], home=home)
    except ToolIsolationUnavailable as exc:
        assert "contains the agent home" in str(exc)
    else:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        assert "AGENT HISTORY" not in result.stdout
        pytest.fail(f"an executable package holding the agent home was mounted: {result.stdout!r}")


@requires_bwrap
@pytest.mark.parametrize("launch", ["sdk_codex_bin", "sdk_launch_command"])
def test_codex_refuses_a_working_directory_that_holds_its_home(monkeypatch, tmp_path, launch):
    workdir = tmp_path / "workdir"
    workdir.mkdir()
    home = _agent_home_with_history(workdir / ".codex")
    (home / "config.toml").write_text('model = "m"\n', encoding="utf-8")
    host_home_before = _tree(home)
    captured, error = _launch_codex_like(monkeypatch, tmp_path, home=home, workdir=workdir, launch=launch)
    spawned = captured.get("spawned", {})
    assert "AGENT HISTORY" not in spawned.get("stdout", "") and "HOST-INSTALLATION-ID" not in spawned.get("stdout", "")
    assert _tree(home) == host_home_before  # the host id is unchanged, and no state was written next to it
    assert error is not None and "contains the agent home" in str(error)
    assert "spawned" not in captured  # refused before launch


# --- configured state locations stay private (Codex review F2) --------------------------------


@requires_bwrap
@pytest.mark.parametrize("launch", ["sdk_codex_bin", "sdk_launch_command"])
@pytest.mark.parametrize(
    "variable, value",
    [("CODEX_SQLITE_HOME", "."), ("CODEX_SQLITE_HOME", "{workdir}"), ("CODEX_ROLLOUT_TRACE_ROOT", ".")],
)
def test_inherited_state_locations_are_pinned_to_the_private_home(monkeypatch, layout, tmp_path, launch, variable,
                                                                  value):
    # The sandbox inherits the host environment. Codex reads these before its
    # own home, and a relative value is resolved against the working directory.
    monkeypatch.setenv(variable, value.format(workdir=layout["workdir"]))
    host_home_before = _tree(layout["home"])
    captured, error = _launch_codex_like(monkeypatch, tmp_path, home=layout["home"], workdir=layout["workdir"],
                                         hidden=(layout["vault"], layout["repo"]), launch=launch)
    assert error is None
    assert captured["spawned"]["returncode"] == 0, captured["spawned"]["stderr"]
    assert _tree(layout["workdir"]) == {"answer.txt": "answer\n"}  # no database, WAL or trace on the host
    assert _host_home_unchanged(host_home_before, _tree(layout["home"]), refreshed=True)


@requires_bwrap
@pytest.mark.parametrize("value", ["/opt/review-state", "{workdir}", "{workdir}/state", "../elsewhere"])
def test_a_configured_sqlite_home_outside_the_private_home_is_refused(monkeypatch, layout, tmp_path, value):
    # config.toml outranks $CODEX_SQLITE_HOME, and the sandbox cannot rewrite
    # it: a location outside the private home would be the host's working
    # directory (the databases persist there) or a read-only mount (startup fails).
    home = layout["home"]
    (home / "config.toml").write_text(f'sqlite_home = "{value.format(workdir=layout["workdir"])}"\n', encoding="utf-8")
    host_home_before = _tree(home)
    captured, error = _launch_codex_like(monkeypatch, tmp_path, home=home, workdir=layout["workdir"],
                                         hidden=(layout["vault"], layout["repo"]))
    assert _tree(layout["workdir"]) == {}
    assert _tree(home) == host_home_before
    assert error is not None and "sqlite_home" in str(error) and str(home / "config.toml") in str(error)
    assert "spawned" not in captured  # refused before launch, with the reason


@requires_bwrap
@pytest.mark.parametrize("value", ["state", "{home}/state", "."])
def test_a_configured_sqlite_home_inside_the_private_home_runs_privately(monkeypatch, layout, tmp_path, value):
    home = layout["home"]
    (home / "config.toml").write_text(f'sqlite_home = "{value.format(home=home)}"\n', encoding="utf-8")
    host_home_before = _tree(home)
    captured, error = _launch_codex_like(monkeypatch, tmp_path, home=home, workdir=layout["workdir"],
                                         hidden=(layout["vault"], layout["repo"]))
    assert error is None
    assert captured["spawned"]["returncode"] == 0, captured["spawned"]["stderr"]
    assert _tree(layout["workdir"]) == {"answer.txt": "answer\n"}
    assert _host_home_unchanged(host_home_before, _tree(home), refreshed=True)


@pytest.mark.parametrize("layer", ["system", "managed", "project", "cwd", "command_line"])
def test_every_config_layer_that_moves_the_state_databases_is_checked(monkeypatch, layout, tmp_path, layer):
    # Codex merges /etc/codex/config.toml, $CODEX_HOME/config.toml, project
    # .codex/config.toml files, -c overrides and /etc/codex/managed_config.toml
    # (on top of everything); any of them can set sqlite_home.
    from learnloop.ai import isolation as isolation_module

    workdir, home = layout["workdir"], layout["home"]
    system, managed = tmp_path / "etc" / "config.toml", tmp_path / "etc" / "managed_config.toml"
    monkeypatch.setattr(isolation_module, "AGENT_SYSTEM_CONFIG", (system, managed))
    arguments: list[str] = []
    setting = f'sqlite_home = "{workdir}"\n'
    if layer == "system":
        system.parent.mkdir()
        system.write_text(setting, encoding="utf-8")
    elif layer == "managed":
        managed.parent.mkdir()
        managed.write_text(setting, encoding="utf-8")
    elif layer == "project":
        (workdir / ".codex").mkdir()
        (workdir / ".codex" / "config.toml").write_text('sqlite_home = "state"\n', encoding="utf-8")
    elif layer == "cwd":
        (workdir / "config.toml").write_text(setting, encoding="utf-8")
    else:
        arguments = ["-c", "sqlite_home=.", "app-server"]
    isolation = ToolIsolation(workdir=workdir, hidden=(layout["vault"],))
    with pytest.raises(ToolIsolationUnavailable, match="sqlite_home"):
        isolation_module.sandbox_arguments(isolation, home=home, arguments=arguments)


def test_command_line_overrides_of_the_state_databases_are_parsed_like_codex(layout):
    from learnloop.ai.isolation import sandbox_arguments

    isolation = ToolIsolation(workdir=layout["workdir"])
    home = layout["home"]
    for override in (["-c", f'sqlite_home="{layout["workdir"]}"'], [f"--config=sqlite_home={layout['workdir']}"],
                     ["--config", "sqlite_home = 'state'"], ["-csqlite_home=/opt/review-state"]):
        with pytest.raises(ToolIsolationUnavailable, match="sqlite_home"):
            sandbox_arguments(isolation, home=home, arguments=[*override, "app-server"])
    for harmless in (["-c", f'sqlite_home="{home}/state"'], ["-c", 'model="m"'],
                     ["app-server", "--listen", "stdio://"]):
        sandbox_arguments(isolation, home=home, arguments=harmless)


def test_a_config_file_tomllib_cannot_parse_is_refused_only_when_it_could_name_the_setting(layout):
    from learnloop.ai.isolation import sandbox_arguments

    home, isolation = layout["home"], ToolIsolation(workdir=layout["workdir"])
    # TOML 1.1 (a newline inside an inline table): Codex's parser accepts it, tomllib does not.
    toml_1_1 = 'mcp_servers = { docs = {\n  command = "docs-server" } }\n'
    (home / "config.toml").write_text(toml_1_1, encoding="utf-8")
    sandbox_arguments(isolation, home=home)  # it cannot set sqlite_home, so it is not in the way
    (home / "config.toml").write_text('sqlite_home = "/opt/review-state"\n' + toml_1_1, encoding="utf-8")
    with pytest.raises(ToolIsolationUnavailable, match="cannot parse .* sqlite_home"):
        sandbox_arguments(isolation, home=home)


def test_the_sandbox_pins_the_agent_home_and_state_locations(monkeypatch, layout):
    from learnloop.ai.isolation import sandbox_arguments

    monkeypatch.chdir(layout["home"].parent)
    args = sandbox_arguments(ToolIsolation(workdir=layout["workdir"]), home=Path(layout["home"].name))
    pairs, triples = list(zip(args, args[1:])), list(zip(args, args[1:], args[2:]))
    home = str(layout["home"])  # a relative CODEX_HOME is made absolute: the tmpfs and the agent agree
    assert ("--tmpfs", home) in pairs
    assert ("--setenv", "CODEX_HOME", home) in triples and ("--setenv", "CODEX_SQLITE_HOME", home) in triples
    assert ("--unsetenv", "CODEX_ROLLOUT_TRACE_ROOT") in pairs


# --- the state checks follow the effective mounts and Codex's parsers (Codex re-review F2) ------


@requires_bwrap
@pytest.mark.parametrize("launch", ["sdk_codex_bin", "sdk_launch_command"])
@pytest.mark.parametrize(
    "workdir_at, setting",
    [
        ("work", 'sqlite_home = "{workdir}"\n'),  # the state location is a host bind inside the home
        ("work", 'sqlite_home = "work"\n'),  # the same, relative to the user's config file
        ("sessions", 'model = "m"\n'),  # no setting: a directory Codex always writes is the host bind
    ],
)
def test_a_working_directory_inside_the_agent_home_is_refused(monkeypatch, tmp_path, launch, workdir_at, setting):
    # The working directory is bound from the host on top of the in-memory
    # home: whatever the agent keeps beneath it (databases, sessions, skills)
    # would reach the host. Real Codex 0.161 left its 15 SQLite/WAL/SHM files
    # there, and with the directory at <home>/skills its 71 system-skill files.
    home = _agent_home_with_history(tmp_path / "agent-home")
    workdir = home / workdir_at
    workdir.mkdir()
    (home / "config.toml").write_text(setting.format(workdir=workdir), encoding="utf-8")
    captured, error = _launch_codex_like(monkeypatch, tmp_path, home=home, workdir=workdir, launch=launch)
    assert set(_tree(workdir)) <= {"answer.txt"}, "the agent's run state reached the host"
    assert error is not None and "inside the agent home" in str(error)
    assert "spawned" not in captured  # refused before launch


@pytest.mark.parametrize("location", ["{home}/package/state", "{home}/package", "{home}/auth.json"])
def test_a_state_location_under_any_host_bind_in_the_home_is_refused(layout, location):
    # Only the in-memory home itself is private. A Node package or a bound
    # credential file inside it is the host's: a state location there is either
    # written to the host or stops the agent on a read-only mount.
    from learnloop.ai.isolation import sandbox_arguments

    home = layout["home"]
    launcher = home / "package" / "bin" / "agent.js"
    launcher.parent.mkdir(parents=True)
    launcher.write_text("#!/usr/bin/env node\n", encoding="utf-8")
    (home / "package" / "package.json").write_text("{}", encoding="utf-8")
    isolation = ToolIsolation(workdir=layout["workdir"])
    (home / "config.toml").write_text(f'sqlite_home = "{location.format(home=home)}"\n', encoding="utf-8")
    with pytest.raises(ToolIsolationUnavailable, match="sqlite_home .* host"):
        sandbox_arguments(isolation, executables=[launcher], home=home)
    # The same package, with the state elsewhere in the private home, runs.
    (home / "config.toml").write_text(f'sqlite_home = "{home}/state"\n', encoding="utf-8")
    sandbox_arguments(isolation, executables=[launcher], home=home)


@pytest.mark.parametrize(
    "first_line",
    [
        '"sqlite_\\u0068ome" = "{workdir}"',  # the reviewer's spelling
        '"sqlite_\\U00000068ome" = "{workdir}"',
        '"sqlite_\\x68ome" = "{workdir}"',  # TOML 1.1's \xHH
        'notify = ["say", "done\\n"]',  # an escape elsewhere: tomllib cannot say where it is
    ],
)
def test_an_unparseable_config_that_could_spell_the_setting_with_an_escape_is_refused(layout, first_line):
    # Codex reads TOML 1.1 and tomllib only 1.0. Without the parse, the setting's
    # name is the one spelling left to look for, and a quoted key can spell it
    # with escapes: an unparseable file with any backslash is refused.
    from learnloop.ai.isolation import sandbox_arguments

    home = layout["home"]
    toml_1_1 = 'history = {\n  persistence = "none" }\n'
    (home / "config.toml").write_text(first_line.format(workdir=layout["workdir"]) + "\n" + toml_1_1, encoding="utf-8")
    with pytest.raises(ToolIsolationUnavailable, match="cannot parse .* sqlite_home"):
        sandbox_arguments(ToolIsolation(workdir=layout["workdir"]), home=home)


def test_an_escaped_setting_name_in_toml_1_0_is_read(layout):
    from learnloop.ai.isolation import sandbox_arguments

    (layout["home"] / "config.toml").write_text(f'"sqlite_\\u0068ome" = "{layout["workdir"]}"\n', encoding="utf-8")
    with pytest.raises(ToolIsolationUnavailable, match="sqlite_home in"):
        sandbox_arguments(ToolIsolation(workdir=layout["workdir"]), home=layout["home"])


def test_short_option_overrides_with_an_equals_sign_are_read_like_clap(layout):
    # clap takes ``-c=VALUE`` as ``-c VALUE``; Codex 0.161 accepted
    # ``-c=sqlite_home="<workdir>"`` and left its databases there.
    from learnloop.ai.isolation import sandbox_arguments

    workdir, home = layout["workdir"], layout["home"]
    isolation = ToolIsolation(workdir=workdir)
    for override in ([f'-c=sqlite_home="{workdir}"'], ["-c=sqlite_home=/opt/review-state"],
                     [f"-c= sqlite_home = '{workdir}'"], ["-c=sqlite_home=."]):
        with pytest.raises(ToolIsolationUnavailable, match="sqlite_home override"):
            sandbox_arguments(isolation, home=home, arguments=[*override, "app-server"])
    sandbox_arguments(isolation, home=home, arguments=[f'-c=sqlite_home="{home}/state"', "-c=model=m", "app-server"])


@pytest.mark.parametrize(
    "arguments",
    [["-Xc", "sqlite_home={workdir}"], ["-c", "sqlite_home.path={workdir}"], ["--sqlite_home={workdir}"]],
)
def test_an_argument_that_names_the_setting_in_an_unread_form_is_refused(layout, arguments):
    # Any other spelling (a flag cluster, a dotted path, an option this check
    # does not know) is refused rather than guessed at.
    from learnloop.ai.isolation import sandbox_arguments

    arguments = [part.format(workdir=layout["workdir"]) for part in arguments]
    with pytest.raises(ToolIsolationUnavailable, match="cannot tell"):
        sandbox_arguments(ToolIsolation(workdir=layout["workdir"]), home=layout["home"],
                          arguments=[*arguments, "app-server"])


# --- every mount honours the exclusions (F2 re-review) -------------------------------------


def _script(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\n" + body, encoding="utf-8")
    path.chmod(0o755)
    return path


@requires_bwrap
@pytest.mark.parametrize("launcher", ["codex", "tools/codex"])
def test_a_launcher_inside_a_hidden_repo_is_refused_not_exposed(layout, launcher):
    # A configured launcher inside an enrolled repo: mounting its directory
    # would show the repo the closed-book check must not see.
    agent = _script(layout["repo"] / launcher, f"cat '{layout['repo'] / 'model.py'}' 2>/dev/null || echo repo-blocked\n")
    isolation = ToolIsolation(workdir=layout["workdir"], hidden=(layout["vault"], layout["repo"]))
    with pytest.raises(ToolIsolationUnavailable, match="inside a path hidden from the agent"):
        sandboxed_command(isolation, [str(agent)], home=layout["home"])
    with pytest.raises(ToolIsolationUnavailable, match="inside a path hidden from the agent"):
        write_launcher(layout["workdir"].parent, isolation, str(agent), home=layout["home"])


@requires_bwrap
def test_only_the_executable_itself_is_mounted_not_its_directory(layout, tmp_path):
    tools = tmp_path / "tools"
    (tools / "notes.txt").parent.mkdir()
    (tools / "notes.txt").write_text("PRIVATE NOTES", encoding="utf-8")
    agent = _script(tools / "agent", f"echo ran; cat '{tools / 'notes.txt'}' 2>/dev/null || echo notes-blocked\n")
    isolation = ToolIsolation(workdir=layout["workdir"], hidden=(layout["vault"], layout["repo"]))
    result = subprocess.run(sandboxed_command(isolation, [str(agent)], home=layout["home"]),
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "ran" in result.stdout and "notes-blocked" in result.stdout and "PRIVATE NOTES" not in result.stdout


@requires_bwrap
@pytest.mark.skipif(__import__("shutil").which("node") is None, reason="needs node for a Node launcher")
def test_a_hidden_path_inside_a_mounted_package_is_masked(layout, tmp_path):
    # A Node launcher needs its whole package (it loads a vendored binary);
    # a hidden repo inside that package is still masked.
    package = tmp_path / "work"
    (package / "package.json").parent.mkdir()
    (package / "package.json").write_text("{}", encoding="utf-8")
    (package / "vendor.txt").write_text("VENDORED", encoding="utf-8")
    nested = package / "checkout"
    nested.mkdir()
    (nested / "model.py").write_text("NESTED SOURCE", encoding="utf-8")
    launcher = package / "bin" / "agent.js"
    launcher.parent.mkdir()
    launcher.write_text(
        "#!/usr/bin/env node\n"
        "const fs = require('fs');\n"
        "for (const p of process.argv.slice(2)) {\n"
        "  try { console.log(fs.readFileSync(p, 'utf8')); } catch (e) { console.log('blocked:' + p); }\n"
        "}\n",
        encoding="utf-8",
    )
    launcher.chmod(0o755)
    isolation = ToolIsolation(workdir=layout["workdir"], hidden=(layout["vault"], nested))
    command = sandboxed_command(isolation, [str(launcher), str(package / "vendor.txt"), str(nested / "model.py")],
                                home=layout["home"])
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "VENDORED" in result.stdout
    assert f"blocked:{nested / 'model.py'}" in result.stdout and "NESTED SOURCE" not in result.stdout


@requires_bwrap
def test_a_hidden_path_inside_the_working_directory_is_masked(tmp_path):
    workdir = tmp_path / "workdir"
    vault = workdir / "vault"
    vault.mkdir(parents=True)
    (vault / "state.sqlite").write_text("LEARNER RECORDS", encoding="utf-8")
    isolation = ToolIsolation(workdir=workdir, hidden=(vault,))
    command = sandboxed_command(isolation, ["sh", "-c", f"cat '{vault / 'state.sqlite'}' || echo vault-blocked"],
                                home=tmp_path / "no-home")
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert "vault-blocked" in result.stdout and "LEARNER RECORDS" not in result.stdout


@requires_bwrap
def test_a_hidden_path_holding_the_working_directory_or_agent_home_is_refused(layout):
    with pytest.raises(ToolIsolationUnavailable, match="working directory"):
        sandboxed_command(ToolIsolation(workdir=layout["workdir"], hidden=(layout["workdir"].parent,)), ["true"],
                          home=layout["home"])
    inside_vault = layout["vault"] / ".codex"
    inside_vault.mkdir()
    (inside_vault / "auth.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ToolIsolationUnavailable, match="agent home"):
        sandboxed_command(ToolIsolation(workdir=layout["workdir"], hidden=(layout["vault"],)), ["true"],
                          home=inside_vault)

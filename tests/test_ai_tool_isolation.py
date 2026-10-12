"""Tool isolation is enforced by the OS, not the prompt (project-understanding F2).

These tests run real processes under bubblewrap and try to read what an
isolated model call must never see: a vault's project store, a repository,
another file in the home directory, the agent's own session transcripts and
host processes. A payload-recording fake cannot show any of this.
"""

from __future__ import annotations

import subprocess
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
        probe = sandboxed_command(ToolIsolation(workdir=Path("/")), ["true"], home=Path("/nonexistent-home"))
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

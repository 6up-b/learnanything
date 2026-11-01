"""RW5d P2b: the Manim tier's sandbox, hardened (spec §9b.3, §9b.5; G-SM26).

* The bubblewrap profile carries the hardened flags (a mandatory user
  namespace with no further ones, every capability dropped) for figure
  renders, the inspector's renders and the declared-function checks (one
  profile: ``concept_animation._sandboxed_command``, no copies).
* A figure render runs inside a memory- and CPU-capped scope
  (``systemd-run --user --scope`` with MemoryMax, MemorySwapMax=0, CPUQuota and
  TasksMax), else ``prlimit --as``; background renders are niced.
* The hostile rich-figure corpus for Manim, in the real sandbox (skipped
  where bubblewrap is not installed, as tests/test_pf_sandbox.py): no
  network, no vault or home or checkout reads, no writes outside scratch, no
  capability, no new user namespace, only the sandbox's own processes in
  /proc, and the memory cap stops a big allocation. Never Manim: hostile
  Python goes straight to the sandbox, past the validator, to test the
  boundary itself; the declared-function harness runs real math/numpy code.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

import learnloop.content.authoring.concept_animation as CA
from learnloop.content.authoring.pf_sandbox import SandboxLimits, run_sandboxed_python, sandbox_available
from learnloop.figures import manim_figure as M

needs_bwrap = pytest.mark.skipif(not sandbox_available(), reason="bubblewrap is not installed")


def test_the_profile_is_hardened_for_every_caller(tmp_path):
    command = CA._sandboxed_command(["python", "-c", "pass"], tmp_path, "/usr/bin/bwrap")
    flags = command[:command.index("--")]
    assert "--unshare-all" in flags and "--die-with-parent" in flags
    for flag in ("--unshare-user", "--disable-userns", "--cap-drop"):
        assert flag in flags, flag
    assert flags[flags.index("--cap-drop") + 1] == "ALL"
    assert CA.HARDENED_BWRAP_FLAGS == ("--unshare-user", "--disable-userns", "--cap-drop", "ALL")


def test_render_scene_wraps_the_sandbox_in_the_capped_scope(monkeypatch, tmp_path):
    monkeypatch.setattr(CA.sys, "platform", "linux")
    monkeypatch.setattr(CA.shutil, "which", lambda name: f"/usr/bin/{name}")
    captured = {}

    def run(command, cwd=None, env=None, capture_output=None, timeout=None):
        captured["command"] = command
        raise FileNotFoundError("stop here")

    wrapper = ["/usr/bin/systemd-run", "--user", "--scope", "--quiet", "-p", "MemoryMax=1", "--"]
    CA.render_scene("from manim import *\nclass S(Scene):\n    pass\n", "S", run=run, wrapper=wrapper)
    command = captured["command"]
    assert command[:len(wrapper)] == wrapper
    rest = command[len(wrapper):]
    assert rest[0] == "/usr/bin/bwrap" and "--disable-userns" in rest and "--cap-drop" in rest


def test_the_capped_scope_prefix(monkeypatch):
    monkeypatch.setattr(CA.sys, "platform", "linux")
    monkeypatch.setattr(CA.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(CA, "_systemd_scope_works", lambda run=None: True)
    prefix = CA.capped_scope_prefix()
    assert prefix[:4] == ["/usr/bin/systemd-run", "--user", "--scope", "--quiet"]
    assert f"MemoryMax={CA.RENDER_MEMORY_MAX}" in prefix and "MemorySwapMax=0" in prefix
    assert f"CPUQuota={CA.RENDER_CPU_QUOTA}" in prefix and f"TasksMax={CA.RENDER_TASKS_MAX}" in prefix
    assert prefix[-1] == "--"
    assert CA.RENDER_MEMORY_MAX == 4 * 1024 ** 3 and CA.RENDER_CPU_QUOTA == "200%"
    background = CA.capped_scope_prefix(background=True)
    assert background[-5:] == ["/usr/bin/ionice", "-c3", "/usr/bin/nice", "-n", "19"]
    monkeypatch.setattr(CA, "_systemd_scope_works", lambda run=None: False)
    assert CA.capped_scope_prefix() == ["/usr/bin/prlimit", f"--as={CA.RENDER_MEMORY_MAX}", "--"]
    monkeypatch.setattr(CA.sys, "platform", "darwin")
    assert CA.capped_scope_prefix() == []


def test_the_scope_probe_runs_once_and_fails_closed_to_prlimit(monkeypatch):
    monkeypatch.setattr(CA.sys, "platform", "linux")
    monkeypatch.setattr(CA.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(CA, "_SCOPE_PROBE", {})
    calls = []

    class Done:
        returncode = 1

    def run(command, **kwargs):
        calls.append(command)
        return Done()

    assert CA._systemd_scope_works(run) is False
    assert CA._systemd_scope_works(run) is False
    assert len(calls) == 1 and calls[0][:3] == ["/usr/bin/systemd-run", "--user", "--scope"]


# --- Codex review F1: the scope launcher gets the session bus, the sandbox never does --


def test_the_render_launch_gives_the_scope_the_session_bus_and_unsets_it_in_the_sandbox(monkeypatch, tmp_path):
    """F1: the render's env dropped DBUS_SESSION_BUS_ADDRESS and XDG_RUNTIME_DIR,
    so ``systemd-run --user`` could not reach the user manager and every render failed."""

    monkeypatch.setenv("DBUS_SESSION_BUS_ADDRESS", "unix:path=/run/user/1000/bus")
    monkeypatch.setenv("XDG_RUNTIME_DIR", "/run/user/1000")
    monkeypatch.setenv("LEARNLOOP_SECRET_SHAPED", "never")
    wrapper = ["/usr/bin/systemd-run", "--user", "--scope", "--quiet", "--"]
    command, env = CA.render_launch(["python", "-m", "manim"], tmp_path, "/usr/bin/bwrap", wrapper)
    assert env["DBUS_SESSION_BUS_ADDRESS"] == "unix:path=/run/user/1000/bus"
    assert env["XDG_RUNTIME_DIR"] == "/run/user/1000" and "LEARNLOOP_SECRET_SHAPED" not in env
    assert env["HOME"] == str(tmp_path)
    assert command[:len(wrapper)] == wrapper
    flags = command[len(wrapper):command.index("--", len(wrapper))]
    unset = [flags[index + 1] for index, flag in enumerate(flags) if flag == "--unsetenv"]
    assert sorted(unset) == ["DBUS_SESSION_BUS_ADDRESS", "XDG_RUNTIME_DIR"]
    # Under prlimit (no scope) nothing of the session is passed at all.
    command, env = CA.render_launch(["python"], tmp_path, "/usr/bin/bwrap", ["/usr/bin/prlimit", "--as=1", "--"])
    assert "DBUS_SESSION_BUS_ADDRESS" not in env and "--unsetenv" not in command


def test_the_scope_probe_launches_exactly_as_a_render_does(monkeypatch):
    monkeypatch.setattr(CA.sys, "platform", "linux")
    monkeypatch.setattr(CA.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(CA, "_SCOPE_PROBE", {})
    monkeypatch.setenv("XDG_RUNTIME_DIR", "/run/user/1000")
    monkeypatch.setenv("LEARNLOOP_SECRET_SHAPED", "never")
    seen = {}

    class Done:
        returncode = 0

    def run(command, **kwargs):
        seen.update(kwargs)
        return Done()

    assert CA._systemd_scope_works(run) is True
    assert seen["env"]["XDG_RUNTIME_DIR"] == "/run/user/1000" and "LEARNLOOP_SECRET_SHAPED" not in seen["env"]


def _scope_runs_here() -> bool:
    import os
    import shutil
    import subprocess

    systemd_run = shutil.which("systemd-run")
    if not systemd_run or not os.environ.get("XDG_RUNTIME_DIR"):
        return False
    try:
        return subprocess.run([systemd_run, "--user", "--scope", "--quiet", "--", "true"], capture_output=True,
                              timeout=15).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


@needs_bwrap
@pytest.mark.skipif(not _scope_runs_here(), reason="no user systemd scope can start here")
def test_the_real_capped_scope_launches_the_sandbox_without_the_session_bus(monkeypatch, tmp_path):
    """F1, end to end on this machine: the capped scope and the hardened sandbox
    start through render_launch (a transient scope around ``env``, never Manim),
    and the sandboxed command sees neither session variable."""

    monkeypatch.setattr(CA, "_SCOPE_PROBE", {})
    wrapper = CA.capped_scope_prefix(memory_bytes=512 * 1024 * 1024)
    assert wrapper and wrapper[0].endswith("systemd-run")
    command, env = CA.render_launch(["/usr/bin/env"], tmp_path, CA.sandbox_bwrap_path(), wrapper)
    result = CA.bounded_run(command, cwd=str(tmp_path), env=env, timeout=60)
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    inner = result.stdout.decode()
    assert "DBUS_SESSION_BUS_ADDRESS" not in inner and "XDG_RUNTIME_DIR" not in inner
    assert f"HOME={tmp_path}" in inner


# --- Codex review F3: render output and the video are bounded in the sidecar ---------


def test_bounded_run_stops_a_flood_and_keeps_only_the_tails(tmp_path):
    """F3: a validator-accepted scene printing without end used to accumulate in
    the sidecar (capture_output); now the group is killed past the budget."""

    import sys

    flood = "import sys\nchunk = 'x' * 65536\nwhile True:\n    sys.stdout.write(chunk); sys.stderr.write(chunk)\n"
    result = CA.bounded_run([sys.executable, "-c", flood], cwd=str(tmp_path), timeout=60,
                            max_output_bytes=4 * 1024 * 1024, tail_bytes=1000)
    assert result.output_exceeded is True and result.returncode != 0
    assert len(result.stdout) <= 1000 and len(result.stderr) <= 1000


def test_bounded_run_returns_the_output_tails_and_times_out(tmp_path):
    import subprocess
    import sys

    result = CA.bounded_run([sys.executable, "-c", "import sys; print('out'); print('err', file=sys.stderr)"],
                            cwd=str(tmp_path), timeout=60)
    assert result.returncode == 0 and result.stdout.strip() == b"out" and result.stderr.strip() == b"err"
    assert result.output_exceeded is False
    with pytest.raises(subprocess.TimeoutExpired):
        CA.bounded_run([sys.executable, "-c", "import time; time.sleep(30)"], cwd=str(tmp_path), timeout=0.5)


# --- Codex re-review F12: cleanup on Windows (no os.killpg) ---------------------


def _as_windows(monkeypatch):
    """Windows as bounded_run sees it, on this machine: no ``os.killpg``, and
    the process tree ended by ``taskkill /T`` (recorded here, not run)."""

    import os

    killed: list[int] = []
    monkeypatch.delattr(os, "killpg", raising=False)
    monkeypatch.setattr(CA, "_WINDOWS", True, raising=False)
    monkeypatch.setattr(CA, "_kill_windows_tree", killed.append, raising=False)
    return killed


def _gone(pid: int) -> bool:
    import os

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True
    return False


def test_a_timeout_on_windows_ends_the_tree_and_reaps_the_renderer(tmp_path, monkeypatch):
    """F12: before the fix the timeout cleanup raised AttributeError
    (``os.killpg``) and the renderer kept running."""

    import subprocess
    import sys

    killed = _as_windows(monkeypatch)
    pid_file = tmp_path / "pid"
    script = f"import os, time\nopen({str(pid_file)!r}, 'w').write(str(os.getpid()))\ntime.sleep(30)\n"
    with pytest.raises(subprocess.TimeoutExpired):
        CA.bounded_run([sys.executable, "-c", script], cwd=str(tmp_path), timeout=2)
    pid = int(pid_file.read_text())
    assert killed == [pid] and _gone(pid)


def test_an_output_flood_on_windows_ends_the_tree_and_reaps_the_renderer(tmp_path, monkeypatch):
    import sys

    killed = _as_windows(monkeypatch)
    flood = "import sys\nchunk = 'x' * 65536\nwhile True:\n    sys.stdout.write(chunk); sys.stderr.write(chunk)\n"
    result = CA.bounded_run([sys.executable, "-c", flood], cwd=str(tmp_path), timeout=60,
                            max_output_bytes=4 * 1024 * 1024, tail_bytes=1000)
    assert result.output_exceeded is True and result.returncode not in (None, 0)
    assert killed and len(result.stdout) <= 1000 and len(result.stderr) <= 1000


class _Child:
    pid = 4242

    def __init__(self) -> None:
        self.killed = 0

    def kill(self) -> None:
        self.killed += 1


@pytest.mark.parametrize("windows", [True, False])
def test_the_tree_kill_always_falls_back_to_killing_the_renderer(monkeypatch, windows):
    """A failing tree kill (taskkill missing, a group already gone) still kills the process itself."""

    import os

    def refuses(*_args):
        raise OSError("not here")

    monkeypatch.setattr(CA, "_WINDOWS", windows, raising=False)
    monkeypatch.setattr(CA, "_kill_windows_tree", refuses, raising=False)
    monkeypatch.setattr(os, "killpg", refuses, raising=False)
    child = _Child()
    CA.terminate_process_tree(child)
    assert child.killed == 1


def test_render_scene_runs_bounded_by_default_and_fails_a_flood(monkeypatch):
    seen = {}

    def flooded(command, **kwargs):
        seen["called"] = True
        return CA.BoundedResult(list(command), -9, b"", b"x" * 100, output_exceeded=True)

    monkeypatch.setattr(CA, "bounded_run", flooded)
    result = CA.render_scene("from manim import *\nclass S(Scene):\n    pass\n", "S", sandbox=False)
    assert seen["called"] and result.ok is False and "MiB of output and was stopped" in result.stderr_tail


def test_a_video_past_the_cap_is_never_read(monkeypatch):
    def writes_big_video(command, cwd=None, **kwargs):
        media = Path(command[command.index("--media_dir") + 1]) / "videos" / "scene" / "480p15"
        media.mkdir(parents=True)
        (media / "S.mp4").write_bytes(b"\0" * 4096)
        return CA.BoundedResult(list(command), 0, b"", b"")

    monkeypatch.setattr(CA, "RENDER_MAX_VIDEO_BYTES", 1024)
    monkeypatch.setattr(Path, "read_bytes", lambda self: pytest.fail("the video must not be read"))
    result = CA.render_scene("from manim import *\nclass S(Scene):\n    pass\n", "S", sandbox=False,
                             run=writes_big_video)
    assert result.ok is False and "larger than" in result.stderr_tail


HOSTILE_PROBE = r'''
import json, os, sys
workdir = sys.argv[1]
payload = json.load(open(workdir + "/input.json"))
result = {}
def attempt(name, action):
    try:
        result[name] = "allowed:" + str(action())
    except BaseException as exc:
        result[name] = "denied:" + type(exc).__name__
import socket
attempt("network", lambda: socket.create_connection(("1.1.1.1", 53), timeout=2))
attempt("dns", lambda: socket.getaddrinfo("example.com", 443))
for index, target in enumerate(payload["secrets"]):
    attempt(f"read{index}", lambda target=target: open(target).read())
attempt("outside_write", lambda: open(payload["outside"], "w").write("escaped"))
attempt("usr_write", lambda: open("/usr/learnloop-escape", "w").write("escaped"))
attempt("userns", lambda: os.unshare(os.CLONE_NEWUSER))
result["cap_eff"] = open("/proc/self/status").read().split("CapEff:")[1].split()[0]
result["processes"] = len([entry for entry in os.listdir("/proc") if entry.isdigit()])
def allocate():
    block = bytearray(payload["allocate"])
    return len(block)
attempt("allocate", allocate)
sys.stdout.write("@@PF-SANDBOX-RESULT@@" + json.dumps(result))
'''


@needs_bwrap
def test_hostile_python_reaches_nothing_outside_the_sandbox(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    vault.mkdir()
    secret = vault / "state.sqlite"
    secret.write_text("LEARNER DATA", encoding="utf-8")
    checkout_secret = (Path(__file__).resolve().parents[1] / "fixtures-local"
                       / f"manim-sandbox-secret-{uuid4().hex}.txt")
    checkout_secret.parent.mkdir(exist_ok=True)
    checkout_secret.write_text("CHECKOUT SECRET", encoding="utf-8")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-secret")
    outside = tmp_path / "escaped.txt"
    try:
        result = run_sandboxed_python(
            HOSTILE_PROBE,
            {"secrets": [str(secret), str(checkout_secret), str(Path.home() / ".bashrc"), "/etc/shadow"],
             "outside": str(outside), "allocate": 1024 ** 3},
            limits=SandboxLimits(cpu_seconds=20, memory_mb=256, wall_seconds=60))
        assert result.ok, result.stderr_tail
        found = result.output
        for key in ("network", "dns", "read0", "read1", "read2", "read3", "outside_write", "usr_write", "userns"):
            assert found[key].startswith("denied"), (key, found[key])
        assert found["allocate"] == "denied:MemoryError"
        assert int(found["cap_eff"], 16) == 0
        assert found["processes"] <= 4  # its own pid namespace: bwrap's init, python
        assert not outside.exists()
    finally:
        checkout_secret.unlink(missing_ok=True)


@needs_bwrap
def test_the_declared_functions_run_in_the_real_sandbox_without_manim():
    """G-SM26: the extracted module (math and numpy only) runs in the
    sandboxed python and the claims check against the grammar oracle."""

    from tests import rich_fixtures as RF

    class Output:
        pass

    output = Output()
    output.__dict__.update(RF.scene_output())
    figure = M.parse_figure(output)
    report = M.check_claims(figure)  # the real sandboxed runner
    assert not report.failed, report.failures
    assert [line["function"] for line in report.checks] == ["x", "x"]
    assert report.not_checkable and report.not_checkable[0]["function"] == "helper_uses_manim"


@needs_bwrap
def test_a_runaway_declared_function_is_stopped_by_the_sandbox_clock(monkeypatch):
    monkeypatch.setattr(M, "FUNCTION_CHECK_SECONDS", 2)
    scene = ("from manim import *\nimport math\n\ndef f(t):\n    while True:\n        t = t + 1\n\n"
             "class S(Scene):\n    def construct(self):\n        pass\n")
    figure = M.ManimFigure(scene, "S", "t", "", (M.Function("f", (M.Argument("t", 0.0, 1.0),)),),
                           (M.Claim("invariant", "f", prop="finite"),), ())
    report = M.check_claims(figure)
    assert report.failed and "could not be run in the sandbox" in report.failures[0]

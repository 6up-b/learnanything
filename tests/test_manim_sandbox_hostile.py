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

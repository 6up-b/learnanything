"""PF-b sandbox acceptance (Slice 2 §5.3, §13): bubblewrap or nothing.

Network, vault reads and writes outside scratch are denied; generation fails
closed without bubblewrap on every platform; CPU and wall-clock limits hold.
"""
from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from learnloop.content.authoring import pf_sandbox
from learnloop.content.authoring.pf_sandbox import (
    SandboxLimits, SandboxUnavailable, run_equivalence_checks, run_generator_tests,
    run_sandboxed_python, sandbox_available,
)
from tests.pf_fakes import LINEAR_PROGRAM, SYMPY_CHECK

needs_bwrap = pytest.mark.skipif(not sandbox_available(), reason="bubblewrap is not installed")

PROBE = r'''
import json, sys
workdir = sys.argv[1]
with open(workdir + "/input.json") as handle:
    payload = json.load(handle)
result = {}
try:
    import socket
    sock = socket.create_connection(("1.1.1.1", 53), timeout=2)
    sock.close()
    result["network"] = "open"
except BaseException as exc:
    result["network"] = "denied:" + type(exc).__name__
try:
    with open(payload["secret"]) as handle:
        result["vault_read"] = "read:" + handle.read()
except BaseException as exc:
    result["vault_read"] = "denied:" + type(exc).__name__
try:
    with open(payload["outside"], "w") as handle:
        handle.write("escaped")
    result["outside_write"] = "written"
except BaseException as exc:
    result["outside_write"] = "denied:" + type(exc).__name__
try:
    with open(workdir + "/scratch.txt", "w") as handle:
        handle.write("ok")
    result["scratch_write"] = "written"
except BaseException as exc:
    result["scratch_write"] = "denied:" + type(exc).__name__
import os
result["env_keys"] = sorted(os.environ)
sys.stdout.write("@@PF-SANDBOX-RESULT@@" + json.dumps(result))
'''


@needs_bwrap
def test_network_vault_reads_and_outside_writes_are_denied(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    vault.mkdir()
    secret = vault / "state.sqlite"
    secret.write_text("LEARNER DATA", encoding="utf-8")
    # A path in the repository checkout too, outside the read-only venv mount.
    repo_secret = (Path(__file__).resolve().parents[1] / "fixtures-local"
                   / f"pf-sandbox-secret-{uuid4().hex}.txt")
    repo_secret.parent.mkdir(exist_ok=True)
    repo_secret.write_text("REPO SECRET", encoding="utf-8")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-secret")
    monkeypatch.setenv("LEARNLOOP_VAULT", str(vault))
    try:
        for target in (secret, repo_secret):
            outside = tmp_path / "escaped.txt"
            result = run_sandboxed_python(PROBE, {"secret": str(target), "outside": str(outside)})
            assert result.ok, result.stderr_tail
            assert result.output["network"].startswith("denied")
            assert result.output["vault_read"].startswith("denied")
            assert result.output["outside_write"].startswith("denied")
            assert result.output["scratch_write"] == "written"
            assert not outside.exists()
            assert "OPENROUTER_API_KEY" not in result.output["env_keys"]
            assert not any(key.startswith("LEARNLOOP") for key in result.output["env_keys"])
        home_write = Path.home() / "pf-sandbox-escape.txt"
        result = run_sandboxed_python(PROBE, {"secret": str(secret), "outside": str(home_write)})
        assert result.output["outside_write"].startswith("denied")
        assert not home_write.exists()
    finally:
        repo_secret.unlink(missing_ok=True)


def test_generation_fails_closed_without_bubblewrap(monkeypatch):
    monkeypatch.setattr(pf_sandbox, "_sandbox_bwrap_path", lambda: None)
    ran = []
    with pytest.raises(SandboxUnavailable, match="bubblewrap"):
        run_generator_tests(LINEAR_PROGRAM, seeds=[1], run=lambda *a, **k: ran.append(a))
    with pytest.raises(SandboxUnavailable):
        run_equivalence_checks({"c": SYMPY_CHECK}, [], run=lambda *a, **k: ran.append(a))
    assert not ran
    assert not pf_sandbox.sandbox_available()


def test_command_is_wrapped_in_bubblewrap_with_limits(monkeypatch):
    seen = {}

    def fake_run(command, **kwargs):
        seen["command"] = command
        seen["kwargs"] = kwargs
        raise pf_sandbox.subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(pf_sandbox, "_sandbox_bwrap_path", lambda: "/usr/bin/bwrap")
    result = run_sandboxed_python("print(1)", {}, limits=SandboxLimits(wall_seconds=7), run=fake_run)
    assert result.timed_out and not result.ok
    command = seen["command"]
    assert command[0] == "/usr/bin/bwrap"
    for flag in ("--die-with-parent", "--unshare-all", "--new-session"):
        assert flag in command
    assert command[command.index("--") + 2] == "-I"
    assert seen["kwargs"]["timeout"] == 7
    assert callable(seen["kwargs"]["preexec_fn"])
    assert set(seen["kwargs"]["env"]) == {"PATH", "HOME", "TMPDIR", "LANG", "XDG_CACHE_HOME",
                                          "PYTHONDONTWRITEBYTECODE", "MPLCONFIGDIR"}


@needs_bwrap
def test_cpu_limit_stops_a_runaway_program():
    result = run_sandboxed_python("while True:\n    pass\n", {},
                                  limits=SandboxLimits(cpu_seconds=1, wall_seconds=20))
    assert not result.ok


@needs_bwrap
def test_wall_clock_limit_kills_a_sleeping_program():
    result = run_sandboxed_python("import time\ntime.sleep(30)\n", {},
                                  limits=SandboxLimits(cpu_seconds=20, wall_seconds=2))
    assert result.timed_out


@needs_bwrap
def test_generator_harness_checks_invariance_and_negative_controls():
    result = run_generator_tests(LINEAR_PROGRAM, seeds=[1, 2, 3])
    assert result.ok
    draws = result.output["draws"]
    assert all(draw["self_check"] and draw["negative_controls_rejected"] for draw in draws)
    assert len({tuple(draw["draw"]["checkpoints"]) for draw in draws}) == 1
    assert all(draw["normal_form"] for draw in draws)
    lazy = LINEAR_PROGRAM.replace('    p = draw["parameters"]\n', '    return True\n    p = draw["parameters"]\n')
    lazy_draws = run_generator_tests(lazy, seeds=[1]).output["draws"]
    assert lazy_draws[0]["negative_controls_rejected"] is False


@needs_bwrap
def test_equivalence_harness_runs_model_written_checks():
    result = run_equivalence_checks(
        {"c": SYMPY_CHECK},
        [{"program": "c", "reference": "1/2", "answer": "0.5"},
         {"program": "c", "reference": "1/2", "answer": "x+1"},
         {"program": "c", "reference": "1/2", "answer": "__import__('os')"}],
        normal_forms={"ref": "2/4"},
    )
    assert result.ok
    assert result.output["checks"] == [True, False, False]
    assert result.output["normal_forms"]["ref"] == "Rational(1, 2)"

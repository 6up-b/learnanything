"""The sandbox may not reach the host through anything the unsandboxed side touches.

Notebook code plants each kind of trap from INSIDE a running notebook at the places the host side reads, writes or
connects to (the session's token and socket): a symlink to a host file, a hard link, a FIFO, a directory, and the
socket swapped for a symlink to a host socket. Then the server is killed (the supervisor restarts it) or the host
side connects. The host file stays as it was, the host socket is never reached, nothing hangs, and the session
restarts or is refused. Real bubblewrap; skipped where it or the notebook extra is missing."""

from __future__ import annotations

import asyncio
import os
import signal
import socket
import stat
import time
from types import SimpleNamespace

import pytest

from learnloop.notebook_runtime import runtime as runtime_module
from learnloop.notebook_runtime.sandbox import missing_requirements
from tests.notebook_runtime_helpers import LIMITS, frame_round_trip, short_base_dir, wait_state

pytestmark = [pytest.mark.notebook_sandbox,
              pytest.mark.skipif(bool(missing_requirements()), reason="; ".join(missing_requirements()) or "ok")]

#: The session id the runtime mints is fixed here, so the notebook knows where the host keeps its files.
FIXED_HEX = "ab"


def trap_notebook(run_dir: str, host_file: str, host_socket: str, kind: str) -> str:
    return f'''import marimo

app = marimo.App()


@app.cell
def trap():
    import json, os, sys
    import marimo as mo
    run_dir = {run_dir!r}
    token = os.path.join(run_dir, "token")
    sock = os.path.join(run_dir, "marimo.sock")
    kind = {kind!r}
    out = {{}}
    try:
        if kind == "symlink":
            os.symlink({host_file!r}, token + ".x")
            os.replace(token + ".x", token)
        elif kind == "hardlink":
            os.link(token, os.path.join(run_dir, "kept-token"))
        elif kind == "fifo":
            os.unlink(token)
            os.mkfifo(token)
        elif kind == "directory":
            os.unlink(token)
            os.mkdir(token)
        elif kind == "socket":
            os.unlink(sock)
            os.symlink({host_socket!r}, sock)
        out[kind] = "planted"
    except OSError as exc:
        out[kind] = "refused:" + str(exc.errno)
    mo.md("traps" + "-finished TR" + "AP=" + kind + ":" + out[kind].split(":")[0] + "=END")
    return


if __name__ == "__main__":
    app.run()
'''


def settled(runtime, session_id: str, timeout: float = 40.0) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = runtime.status(vault_key="/v1", session_id=session_id)["state"]
        if state in ("ready", "failed"):
            return state
        time.sleep(0.1)
    return "hung"


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo", "directory", "socket"])
def test_a_trap_planted_from_inside_never_reaches_the_host(kind, monkeypatch):
    from learnloop.notebook_runtime.runtime import NotebookRuntime

    monkeypatch.setattr(runtime_module, "secrets", SimpleNamespace(token_hex=lambda n: FIXED_HEX * n))
    with short_base_dir() as base:
        host_file = base / "host-file.txt"
        host_file.write_text("HOST", encoding="utf-8")
        host_socket = base / "host.sock"
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        listener.bind(str(host_socket))
        listener.listen(4)
        listener.setblocking(False)
        runtime = NotebookRuntime(base_dir=base)
        run_dir = base / "run" / (FIXED_HEX * 8)
        token = run_dir / "token"
        try:
            source = trap_notebook(str(run_dir), str(host_file), str(host_socket), kind).encode()
            view = runtime.open(vault_key="/v1", owner="pad:p1", source=source, view="app", limits=LIMITS,
                                idle_minutes=10, max_sessions=2)
            view = wait_state(runtime, "/v1", view["session_id"], "ready")
            seen = asyncio.run(frame_round_trip(view["frame_url"], marimo_session="s_trap", wanted=["traps-finished"],
                                                pattern=r"TRAP=(\w+):(\w+)=END"))
            session = runtime.sessions()[0]
            result = dict(seen.get("matches") or [])
            if kind == "socket":
                # The host side connects to its session's socket (a readiness probe, as after every restart).
                try:
                    runtime.run_on_loop(lambda: runtime._entries[session.session_id].supervisor.backend.ready(session))
                except Exception:  # noqa: BLE001 - a refused connection is a pass here
                    pass
            else:
                os.killpg(session.process.pid, signal.SIGKILL)
                time.sleep(0.5)
            state = settled(runtime, view["session_id"])
            try:
                listener.accept()
                reached = True
            except BlockingIOError:
                reached = False
            assert host_file.read_text(encoding="utf-8") == "HOST"
            assert not reached
            assert state in ("ready", "failed"), state
            assert result[kind].startswith("refused"), result
        finally:
            # A writer blocked on a planted FIFO is released, so a failing run cannot hang the suite.
            try:
                if stat.S_ISFIFO(os.lstat(token).st_mode):
                    os.close(os.open(token, os.O_RDONLY | os.O_NONBLOCK))
            except OSError:
                pass
            runtime.close()
            listener.close()


# -- static: no unsandboxed call site touches a runtime host path without the trusted helpers -----------------------

#: Filesystem calls the unsandboxed modules may not make on their own: every host path of a session goes through
#: ``notebook_runtime.hostfiles`` (no-follow, exclusive, through directory descriptors, verified).
FILESYSTEM_CALLS = {"write_text", "write_bytes", "read_text", "read_bytes", "unlink", "mkdir", "rmdir", "chmod",
                    "rename", "symlink_to", "hardlink_to", "exists", "is_file", "is_dir", "is_socket", "stat", "lstat",
                    "walk", "rmtree", "iterdir", "glob", "mkfifo", "link", "chown", "open", "unix_connect",
                    "AsyncHTTPTransport"}
#: Names too common to flag on any receiver (str.replace, a session's touch): flagged only on ``os``.
OS_ONLY_CALLS = {"replace", "remove", "symlink", "makedirs"}
#: The call sites that do not touch a session's host files, each with why.
ALLOWED = {
    ("sandbox.py", "is_dir"): "runtime_base_dir: whether the user's own XDG_RUNTIME_DIR exists (not sandbox-writable)",
    ("theme.py", "is_file"): "the vendored fonts in the installed package (not sandbox-writable)",
    ("proxy.py", "read_bytes"): "serving a vendored font from the installed package (not sandbox-writable)",
    ("runtime.py", "read_text"): "the session's cgroup memory from /proc and /sys (kernel files, not sandbox-writable)",
    ("lessons.py", "is_file"): "whether the vault holds a lesson's notebook (the vault; the sandbox never sees it)",
    ("proxy.py", "unix_connect"): "after hostfiles.check_socket on the session's socket",
    ("proxy.py", "AsyncHTTPTransport"): "after hostfiles.check_socket on the session's socket",
    ("supervisor.py", "AsyncHTTPTransport"): "after hostfiles.check_socket on the session's socket",
}
#: Code that runs INSIDE the sandbox, or the trusted helpers themselves.
NOT_HOST_SIDE = {"hostfiles.py", "adapter.py"}


def test_no_unsandboxed_call_site_touches_a_host_path_without_the_safe_helpers():
    import ast
    from pathlib import Path

    from learnloop.notebook_runtime import supervisor

    package = Path(supervisor.__file__).parent
    found = []
    for path in sorted(package.glob("*.py")):
        if path.name in NOT_HOST_SIDE:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", None)
            on_os = isinstance(node.func, ast.Attribute) and getattr(node.func.value, "id", None) == "os"
            if (name in FILESYSTEM_CALLS or (on_os and name in OS_ONLY_CALLS)) and (path.name, name) not in ALLOWED:
                found.append(f"{path.name}:{node.lineno} {name}")
    assert found == []


def test_the_launcher_inside_the_sandbox_only_serves_the_inherited_socket():
    import ast
    from pathlib import Path

    from learnloop.notebook_runtime import adapter

    module = ast.parse(Path(adapter.__file__).read_text(encoding="utf-8"))
    tree = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "launch")
    calls = {node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", None)
             for node in ast.walk(tree) if isinstance(node, ast.Call)}
    assert not calls & {"unlink", "open", "bind", "mkdir", "chmod"}


def test_the_sandbox_has_no_writable_host_path(tmp_path):
    from learnloop.notebook_runtime.sandbox import SANDBOX_TOKEN, Layout, Limits, launch_command

    layout = Layout(run_dir=tmp_path / "run", notebook=tmp_path / "nb.py", config_dir=tmp_path / "cfg",
                    hosts_file=tmp_path / "hosts")
    argv, _env = launch_command(layout, Limits(memory_mib=512, scratch_mib=64), base_url="/s/x", unit="u",
                                scoped=True, socket_fd=7, bwrap="/usr/bin/bwrap")
    assert not {"--bind", "--bind-try", "--dev-bind", "--dev-bind-try"} & set(argv)
    assert str(layout.run_dir) not in argv and str(layout.socket) not in " ".join(argv)
    token = argv.index(str(layout.token_file))
    assert argv[token - 1] == "--ro-bind" and argv[token + 1] == SANDBOX_TOKEN


# -- the frame's capability never appears in a process's arguments ----------------------------------------------

def test_the_secret_path_is_not_in_any_process_arguments(tmp_path):
    """Another local user can read every process's command line, so the session's secret path (the frame's
    capability) reaches the server through its environment instead (readable only by this user)."""

    from learnloop.notebook_runtime.sandbox import BASE_URL_ENV, Layout, Limits, launch_command

    layout = Layout(run_dir=tmp_path / "run", notebook=tmp_path / "nb.py", config_dir=tmp_path / "cfg",
                    hosts_file=tmp_path / "hosts")
    argv, env = launch_command(layout, Limits(memory_mib=512, scratch_mib=64), base_url="/s/SECRET123", unit="u",
                               scoped=True, socket_fd=7, bwrap="/usr/bin/bwrap")
    assert not any("SECRET123" in arg for arg in argv)
    assert env[BASE_URL_ENV] == "/s/SECRET123"


def test_a_running_sessions_secret_is_in_no_command_line():
    from pathlib import Path

    from learnloop.notebook_runtime.runtime import NotebookRuntime
    from tests.notebook_runtime_helpers import SYNTHETIC_NOTEBOOK

    with short_base_dir() as base:
        runtime = NotebookRuntime(base_dir=base)
        try:
            view = runtime.open(vault_key="/v1", owner="pad:p1", source=SYNTHETIC_NOTEBOOK.encode(), view="app",
                                limits=LIMITS, idle_minutes=10, max_sessions=2)
            view = wait_state(runtime, "/v1", view["session_id"], "ready")
            asyncio.run(frame_round_trip(view["frame_url"], marimo_session="s_argv", wanted=["square=9"]))
            secret = runtime.sessions()[0].secret
            leaked = []
            for entry in Path("/proc").iterdir():
                if entry.name.isdigit():
                    try:
                        if secret.encode() in (entry / "cmdline").read_bytes():
                            leaked.append(int(entry.name))
                    except OSError:
                        pass
            assert leaked == []
        finally:
            runtime.close()


# -- storage: nothing a notebook writes outlives its caps -------------------------------------------------------

def test_the_sandboxes_tmp_is_size_capped_like_its_scratch(tmp_path):
    from learnloop.notebook_runtime.sandbox import Layout, Limits, launch_command

    layout = Layout(run_dir=tmp_path / "run", notebook=tmp_path / "nb.py", config_dir=tmp_path / "cfg",
                    hosts_file=tmp_path / "hosts")
    argv, _env = launch_command(layout, Limits(memory_mib=512, scratch_mib=64), base_url="/s/x", unit="u",
                                scoped=True, socket_fd=7, bwrap="/usr/bin/bwrap")
    tmpfs = [i for i, arg in enumerate(argv) if arg == "--tmpfs" and argv[i + 1] == "/tmp"]
    assert tmpfs and argv[tmpfs[-1] - 2:tmpfs[-1]] == ["--size", str(64 * 1024 * 1024)]


def test_a_notebook_cannot_write_past_its_caps():
    from learnloop.notebook_runtime.runtime import NotebookRuntime

    source = '''import marimo

app = marimo.App()


@app.cell
def fill():
    import errno
    import marimo as mo
    found = {}
    for where in ("/tmp", "/scratch"):
        try:
            with open(where + "/fill", "wb") as handle:
                for _ in range(80):
                    handle.write(b"x" * (1024 * 1024))
            found[where] = "wrote"
        except OSError as exc:
            found[where] = "full" if exc.errno == errno.ENOSPC else str(exc.errno)
    mo.md("fi" + "lled " + " ".join(f"{k}={v}" for k, v in sorted(found.items())) + " END")
    return


if __name__ == "__main__":
    app.run()
'''
    with short_base_dir() as base:
        runtime = NotebookRuntime(base_dir=base)
        try:
            view = runtime.open(vault_key="/v1", owner="pad:p1", source=source.encode(), view="app", limits=LIMITS,
                                idle_minutes=10, max_sessions=2)
            view = wait_state(runtime, "/v1", view["session_id"], "ready")
            seen = asyncio.run(frame_round_trip(view["frame_url"], marimo_session="s_fill", wanted=["filled "],
                                                pattern=r"filled ([^E]*) END"))
            assert seen["matches"] == ["/scratch=full /tmp=full"], seen.get("matches")
        finally:
            runtime.close()

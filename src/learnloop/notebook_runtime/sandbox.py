"""How one marimo server is launched: the shared hardened profile, the server's own mounts, and its scope.

Inside the sandbox the server sees: the system and interpreter read-only (the profile), the notebook read-only at
a fixed path, this package's launcher read-only, marimo's config read-only, a two-line hosts file, its token
read-only, and a size-capped tmpfs as its home and working directory. No host path is writable: the server
listens on a socket trusted code created and handed to it as a descriptor (``hostfiles``), so nothing the
unsandboxed side reads, writes or connects to lies in a directory the sandbox can change. The root is remounted
read-only last. No network namespace but its own loopback, no session bus, no GPU.

Outside it, a ``systemd-run --user --scope`` caps memory (no swap), CPU and tasks, with ``OOMPolicy=continue``:
under systemd's default policy one cell's child passing the memory cap stops the whole scope, server and kernel
with it, and the session is lost. Without a user manager it falls back to ``prlimit --as``.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from learnloop.notebook_runtime import adapter, hostfiles, settings
from learnloop.sandbox_profile import bwrap_path, sandboxed_command

#: What ``systemd-run --user`` needs to reach the user manager; bubblewrap unsets them before marimo runs.
SESSION_BUS_VARS: tuple[str, ...] = ("DBUS_SESSION_BUS_ADDRESS", "XDG_RUNTIME_DIR")
#: marimo's edit kernel connects back to its server over multiprocessing's AF_INET listener, which binds
#: ``("localhost", 0)``. The profile mounts nothing of the host's ``/etc``, so without this file the name does not
#: resolve and no session ever starts its kernel. Our own two lines, never the host's file.
HOSTS_FILE_TEXT = "127.0.0.1 localhost\n::1 localhost\n"

SANDBOX_NOTEBOOK = "/nb/notebook.py"
SANDBOX_LAUNCHER = "/ll/launcher.py"
SANDBOX_CONFIG = "/ll/config"
SANDBOX_SCRATCH = "/scratch"
SANDBOX_TOKEN = "/ll/token"
#: The session's secret path reaches the server through this variable, never its arguments: any local user can
#: read a process's command line, only this user its environment. The launcher takes it out before marimo runs.
BASE_URL_ENV = adapter.BASE_URL_ENV


class RuntimeUnavailable(RuntimeError):
    """The notebook runtime cannot run here (no bubblewrap, no notebook extra); it refuses, never runs unsandboxed."""


@dataclass(frozen=True)
class Limits:
    memory_mib: int
    scratch_mib: int

    @classmethod
    def from_config(cls, config: object) -> Limits:
        return cls(memory_mib=int(config.memory_max_mib), scratch_mib=int(config.scratch_mib))  # type: ignore[attr-defined]


@dataclass(frozen=True)
class Layout:
    """A session's host paths, all in private directories the sandbox never sees (``run_dir`` holds the socket
    trusted code listens on and the token mounted read-only into the sandbox)."""

    run_dir: Path
    notebook: Path
    config_dir: Path
    hosts_file: Path

    @property
    def socket(self) -> Path:
        return self.run_dir / "marimo.sock"

    @property
    def token_file(self) -> Path:
        return self.run_dir / "token"


def missing_requirements() -> list[str]:
    """Why the runtime cannot run here, in words; empty when it can."""

    import importlib.util

    problems = []
    if not settings.LEARNER_CELLS_SANDBOXED or not settings.CPU_ONLY:
        problems.append("only the sandboxed, CPU-only runtime is built")
    if bwrap_path() is None:
        problems.append("bubblewrap (bwrap) is not installed; notebooks run only inside it")
    for module in ("marimo", "uvicorn", "websockets", "httpx"):
        if importlib.util.find_spec(module) is None:
            problems.append(f"the notebook extra is not installed ({module} is missing)")
            break
    return problems


#: A session's socket sits at ``<base>/run/<16 hex>/marimo.sock``: this many bytes past the base directory.
SOCKET_SUFFIX_BYTES = len("/run/") + 16 + len("/marimo.sock")
#: A Unix socket's path must fit ``sun_path`` (108 bytes on Linux, with its terminating zero), with room to spare.
SOCKET_PATH_MAX_BYTES = 100


def runtime_base_dir() -> Path:
    """Where sessions' run directories go: the user's runtime directory (short, private, gone at logout), else the
    temporary directory. A runtime directory too deep for a socket's path (a session started under another
    runtime directory) is passed over for the temporary directory rather than refusing every notebook."""

    name = f"learnloop-notebooks-{os.getuid()}"
    candidates = []
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if runtime and Path(runtime).is_dir():
        candidates.append(Path(runtime) / name)
    candidates.append(Path(tempfile.gettempdir()) / name)
    for base in candidates:
        if len(str(base).encode()) + SOCKET_SUFFIX_BYTES <= SOCKET_PATH_MAX_BYTES:
            return base
    return candidates[-1]


def write_shared_files(base: Path) -> tuple[Path, Path]:
    """marimo's config directory and the hosts file, written once under ``base`` (both mounted read-only). ``base``
    may sit in the shared temporary directory: it is made or checked as this user's private directory."""

    hostfiles.private_dir(base)
    config_dir = base / "config"
    hostfiles.private_dir(config_dir / "marimo")
    hostfiles.write_private(config_dir / "marimo", "marimo.toml", adapter.MARIMO_TOML.encode("utf-8"))
    hostfiles.write_private(base, "hosts", HOSTS_FILE_TEXT.encode("utf-8"))
    return config_dir, base / "hosts"


_SCOPE_PROBE: dict[str, bool] = {}


def scope_available() -> bool:
    """Whether ``systemd-run --user --scope`` can start a scope here (probed once per process)."""

    if "ok" in _SCOPE_PROBE:
        return _SCOPE_PROBE["ok"]
    ok = False
    systemd_run = shutil.which("systemd-run")
    if systemd_run and sys.platform == "linux" and os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
        env = {"PATH": "/usr/bin:/bin", **{k: os.environ[k] for k in SESSION_BUS_VARS if os.environ.get(k)}}
        try:
            ok = subprocess.run([systemd_run, "--user", "--scope", "--quiet", "--", "true"], capture_output=True,
                                timeout=15, env=env).returncode == 0
        except (OSError, subprocess.SubprocessError):
            ok = False
    _SCOPE_PROBE["ok"] = ok
    return ok


def scope_prefix(unit: str, limits: Limits, *, scoped: bool) -> list[str]:
    memory = limits.memory_mib * 1024 * 1024
    if scoped:
        return [shutil.which("systemd-run") or "systemd-run", "--user", "--scope", "--quiet", f"--unit={unit}",
                "-p", f"MemoryMax={memory}", "-p", "MemorySwapMax=0", "-p", f"CPUQuota={settings.CPU_QUOTA}",
                "-p", f"TasksMax={settings.TASKS_MAX}", "-p", "OOMPolicy=continue", "--"]
    prlimit = shutil.which("prlimit")
    return [prlimit, f"--as={memory}", "--"] if prlimit else []


def launch_command(layout: Layout, limits: Limits, *, base_url: str, unit: str, scoped: bool, socket_fd: int,
                   python: str | None = None, bwrap: str | None = None) -> tuple[list[str], dict[str, str]]:
    """The argv and environment that start one marimo server on the listening socket ``socket_fd`` (inherited)."""

    bwrap = bwrap or bwrap_path()
    if bwrap is None:
        raise RuntimeUnavailable("bubblewrap (bwrap) is not installed; notebooks run only inside it")
    python = python or sys.executable
    inner = [python, "-I", "-B", SANDBOX_LAUNCHER, str(socket_fd), "--",
             *adapter.marimo_edit_args(SANDBOX_NOTEBOOK, SANDBOX_TOKEN)]
    extra = ["--ro-bind", str(layout.notebook), SANDBOX_NOTEBOOK,
             "--ro-bind", str(layout.token_file), SANDBOX_TOKEN,
             "--ro-bind", adapter.__file__, SANDBOX_LAUNCHER,
             "--ro-bind", str(layout.config_dir), SANDBOX_CONFIG,
             "--ro-bind", str(layout.hosts_file), "/etc/hosts",
             "--size", str(limits.scratch_mib * 1024 * 1024), "--tmpfs", SANDBOX_SCRATCH,
             "--chdir", SANDBOX_SCRATCH,
             # Last: nothing but /tmp and the scratch (both tmpfs) is writable, including the root's own mount
             # points.
             "--remount-ro", "/"]
    argv = sandboxed_command(inner, None, bwrap, hardened=True, unset_env=SESSION_BUS_VARS,
                             extra_args=extra)
    env = {
        "PATH": "/usr/bin:/bin",
        "HOME": SANDBOX_SCRATCH,
        "TMPDIR": "/tmp",
        "LANG": "C.UTF-8",
        "XDG_CACHE_HOME": f"{SANDBOX_SCRATCH}/.cache",
        "XDG_CONFIG_HOME": SANDBOX_CONFIG,
        "XDG_DATA_HOME": f"{SANDBOX_SCRATCH}/.local/share",
        "XDG_STATE_HOME": f"{SANDBOX_SCRATCH}/.local/state",
        "MPLCONFIGDIR": f"{SANDBOX_SCRATCH}/.cache",
        "PYTHONDONTWRITEBYTECODE": "1",
        BASE_URL_ENV: base_url,
    }
    if scoped:
        env.update({key: os.environ[key] for key in SESSION_BUS_VARS if os.environ.get(key)})
    return [*scope_prefix(unit, limits, scoped=scoped), *argv], env

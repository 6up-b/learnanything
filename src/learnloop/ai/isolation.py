"""Tool and filesystem isolation for model calls that must stay closed-book.

A chat-completions transport never runs tools: the prompt is all it sees
(:data:`TOOL_FREE`). An *agentic* transport (Codex runs shell and file tools in
its app-server) can read any path its process can, whatever its working
directory. A caller that promises a scope in its receipts (``diff``,
``questions_only``, ``quoted_evidence``) therefore asks for isolation with
:func:`tool_isolation`, and a transport that declares :data:`TOOL_ISOLATION`
must honour it or refuse the request.

The isolation is enforced by the operating system, not by the prompt: the
agent's process runs under bubblewrap with a deny-by-default filesystem view.

- **Visible, read-only:** the system trees programs need (``/usr``, ``/etc``,
  the ``/lib*`` and ``/bin`` links, ``/opt``, ``/nix``, ``/sys``, the DNS
  resolver directory) and the agent's own executable.
- **Visible, writable:** an empty working directory, and the agent's
  credential file so a token refresh persists.
- **Everything else is absent:** home directories (so vaults, repositories and
  ``~/.config``), other mounts, and the agent's own history. The agent's home
  (``~/.codex``) is replaced by an empty in-memory directory into which only
  its credentials and configuration are bound back: session transcripts,
  history and memory databases may hold the very code a closed-book check must
  not see. Paths named in ``hidden`` are masked even if they sit inside a
  visible system tree. The process gets its own PID namespace, so ``/proc``
  shows no host process (and no host working directory).

The network is not unshared: the agent needs its model API.
"""

from __future__ import annotations

import os
import shlex
import shutil
import sys
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TOOL_FREE = "tool_free"
TOOL_ISOLATION = "tool_isolation"

_SYSTEM_READ_ONLY = ("/usr", "/etc", "/opt", "/nix", "/sys", "/run/systemd/resolve")
_SYSTEM_LINKS = ("/bin", "/sbin", "/lib", "/lib32", "/lib64", "/libx32")
# Bound back into the otherwise empty agent home. Only the credential file is
# writable (token refreshes are written in place).
AGENT_HOME_WRITABLE = ("auth.json",)
AGENT_HOME_READ_ONLY = ("config.toml", "installation_id")


@dataclass(frozen=True)
class ToolIsolation:
    """What an isolated call may see: one empty working directory, nothing else."""

    workdir: Path
    hidden: tuple[Path, ...] = field(default_factory=tuple)


_isolation: ContextVar[ToolIsolation | None] = ContextVar("model_tool_isolation", default=None)


@contextmanager
def tool_isolation(isolation: ToolIsolation) -> Iterator[ToolIsolation]:
    token = _isolation.set(isolation)
    try:
        yield isolation
    finally:
        _isolation.reset(token)


def current_tool_isolation() -> ToolIsolation | None:
    return _isolation.get()


class ToolIsolationUnavailable(RuntimeError):
    """The transport cannot confine its tools here; the call must not run."""


def bubblewrap_path() -> str | None:
    if not sys.platform.startswith("linux"):
        return None
    return shutil.which("bwrap")


def isolation_unavailable_reason() -> str | None:
    if not sys.platform.startswith("linux"):
        return "tool isolation needs Linux bubblewrap; this host is not Linux"
    if bubblewrap_path() is None:
        return "tool isolation needs bubblewrap (`bwrap`); install it, or set project.require_tool_isolation = false"
    return None


def isolation_mode(client: Any) -> tuple[str | None, str | None]:
    """``(mode, reason)``: how ``client`` would honour an isolation request.

    ``mode`` is ``"tool_free"`` (it never runs tools), ``"bubblewrap"`` (its
    tools run in the sandbox above) or ``None`` with the reason it cannot.
    """

    supports = getattr(client, "supports", None)
    if callable(supports) and supports(TOOL_FREE):
        return "tool_free", None
    if callable(supports) and supports(TOOL_ISOLATION):
        reason = isolation_unavailable_reason()
        return (None, reason) if reason else ("bubblewrap", None)
    name = getattr(client, "provider_name", type(client).__name__)
    return None, f"AI provider {name!r} may run tools and cannot confine them to the isolated working directory"


def agent_home() -> Path:
    configured = os.environ.get("CODEX_HOME", "").strip()
    return Path(configured).expanduser() if configured else Path.home() / ".codex"


def _inside(path: Path, roots: Iterable[str]) -> bool:
    return any(path == Path(root) or Path(root) in path.parents for root in roots)


def _executable_root(executable: Path) -> Path:
    """The directory an executable needs: its package for a Node launcher."""

    real = executable.resolve()
    try:
        with real.open("rb") as handle:
            head = handle.read(128)
    except OSError:
        head = b""
    if head.startswith(b"#!") and b"node" in head.split(b"\n", 1)[0]:
        # npm launchers (bin/codex.js) load their vendored binary from the
        # package next to bin/.
        return real.parent.parent
    return real.parent


def sandbox_arguments(
    isolation: ToolIsolation,
    *,
    executables: Iterable[Path] = (),
    home: Path | None = None,
) -> list[str]:
    """bubblewrap options (without the program) for one isolated process."""

    workdir = Path(isolation.workdir).resolve()
    home = (home or agent_home()).expanduser()
    args = [
        "--die-with-parent", "--new-session",
        "--unshare-pid", "--unshare-ipc", "--unshare-uts",
        "--proc", "/proc", "--dev", "/dev",
    ]
    for link in _SYSTEM_LINKS:
        path = Path(link)
        if path.is_symlink():
            args += ["--symlink", os.readlink(path), link]
        elif path.is_dir():
            args += ["--ro-bind", link, link]
    for root in _SYSTEM_READ_ONLY:
        args += ["--ro-bind-try", root, root]
    visible = (*_SYSTEM_READ_ONLY, *_SYSTEM_LINKS)
    # In-memory directories first: the binds below must sit on top of them.
    args += ["--tmpfs", "/tmp", "--tmpfs", str(home)]
    for name in AGENT_HOME_WRITABLE:
        args += ["--bind-try", str(home / name), str(home / name)]
    for name in AGENT_HOME_READ_ONLY:
        args += ["--ro-bind-try", str(home / name), str(home / name)]
    for executable in executables:
        root = _executable_root(Path(executable))
        if not _inside(root, visible):
            args += ["--ro-bind", str(root), str(root)]
    args += ["--bind", str(workdir), str(workdir)]
    for hidden in isolation.hidden:
        path = Path(hidden).expanduser().resolve()
        if not path.exists() or not _inside(path, visible):
            continue  # not mounted into the sandbox in the first place
        if path.is_dir():
            args += ["--tmpfs", str(path)]
        else:
            args += ["--ro-bind", "/dev/null", str(path)]
    args += ["--setenv", "TMPDIR", "/tmp", "--chdir", str(workdir)]
    return args


def sandboxed_command(
    isolation: ToolIsolation,
    command: list[str],
    *,
    home: Path | None = None,
) -> list[str]:
    """``command`` wrapped in bubblewrap; raises when bubblewrap is unavailable."""

    reason = isolation_unavailable_reason()
    bwrap = bubblewrap_path()
    if reason is not None or bwrap is None:
        raise ToolIsolationUnavailable(reason or "bubblewrap is unavailable")
    executable = shutil.which(command[0]) or command[0]
    needed = [Path(executable)]
    if _executable_root(Path(executable)) != Path(executable).resolve().parent:
        # A Node launcher also needs its interpreter.
        node = shutil.which("node")
        if node:
            needed.append(Path(node))
    return [bwrap, *sandbox_arguments(isolation, executables=needed, home=home), "--", executable, *command[1:]]


def write_launcher(directory: Path, isolation: ToolIsolation, executable: str, *, home: Path | None = None) -> Path:
    """A ``#!/bin/sh`` launcher that runs ``executable "$@"`` inside the sandbox.

    For SDKs that take a program path and append their own arguments.
    """

    command = sandboxed_command(isolation, [executable], home=home)
    launcher = Path(directory) / "isolated-agent"
    launcher.write_text("#!/bin/sh\nexec " + " ".join(shlex.quote(part) for part in command) + ' "$@"\n', encoding="utf-8")
    launcher.chmod(0o700)
    return launcher


__all__ = [
    "TOOL_FREE",
    "TOOL_ISOLATION",
    "ToolIsolation",
    "ToolIsolationUnavailable",
    "agent_home",
    "bubblewrap_path",
    "current_tool_isolation",
    "isolation_mode",
    "isolation_unavailable_reason",
    "sandbox_arguments",
    "sandboxed_command",
    "tool_isolation",
    "write_launcher",
]

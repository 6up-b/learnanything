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
  resolver directory) and the agent's executable: the file itself, or, for a
  Node launcher, its package (it loads a vendored binary from there), never
  the directory it happens to sit in.
- **Visible, writable:** an empty working directory, and the agent's
  credential file so a token refresh persists.
- **Private, writable, discarded at exit:** ``/tmp`` and the agent's home are
  in-memory directories. The agent keeps its run state there, so none of it
  reaches the host. Codex 0.161 writes its ``installation_id``, its state,
  log, goal, memory, queue and thread-history databases, session rollouts,
  shell snapshots, lock files, model/app/plugin caches, system skills and
  ``tmp/arg0`` helpers.
- **Everything else is absent:** home directories (so vaults, repositories and
  ``~/.config``), other mounts, and the agent's own history. The agent's home
  (``~/.codex``) is replaced by an empty in-memory directory into which only
  its credentials and configuration are bound back: session transcripts,
  history and memory databases may hold the very code a closed-book check must
  not see. The process gets its own PID namespace, so ``/proc`` shows no host
  process (and no host working directory).

A host file is bound back only in a mode the agent can open it with. Codex
opens ``installation_id`` read-write at startup, even when the file exists, so
a read-only bind stopped the app-server with ``Read-only file system (os error
30)``. A writable bind would let the sandbox write a host file that the
owner's own Codex reads and sends with its requests. So the file is not bound:
each isolated launch creates a fresh id in its private home.

Paths named in ``hidden`` are masked inside *every* mounted tree: the system
trees, the executable's package and the working directory. A layout the mask
cannot honour is refused (:class:`ToolIsolationUnavailable`), never run: an
executable, the working directory or the agent's home inside a hidden path
would put part of that path in front of the agent.

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
# Bound back into the otherwise empty, in-memory agent home. Only the credential
# file is writable (token refreshes are written in place); the configuration is
# read-only. A file the agent opens for writing must not be bound read-only:
# Codex opens ``installation_id`` read-write at startup, so it is created fresh
# in the private home instead (see the module docstring).
AGENT_HOME_WRITABLE = ("auth.json",)
AGENT_HOME_READ_ONLY = ("config.toml",)


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


def _is_node_launcher(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            head = handle.read(128)
    except OSError:
        return False
    return head.startswith(b"#!") and b"node" in head.split(b"\n", 1)[0]


def executable_assets(executable: Path) -> Path:
    """What an executable needs mounted: the file itself, or its Node package.

    An npm launcher (``bin/codex.js``) loads its vendored binary from the
    package beside ``bin/``, so a launcher under a ``package.json`` needs that
    package. Anything else gets only its own (resolved) file: its directory may
    hold anything, a repository included.
    """

    real = Path(executable).resolve()
    if _is_node_launcher(real) and (real.parent.parent / "package.json").is_file():
        return real.parent.parent
    return real


def _contains(outer: Path, inner: Path) -> bool:
    return inner == outer or outer in inner.parents


def sandbox_arguments(
    isolation: ToolIsolation,
    *,
    executables: Iterable[Path] = (),
    home: Path | None = None,
) -> list[str]:
    """bubblewrap options (without the program) for one isolated process.

    Raises :class:`ToolIsolationUnavailable` when a hidden path holds
    something the sandbox must mount (see the module docstring).
    """

    workdir = Path(isolation.workdir).resolve()
    home = (home or agent_home()).expanduser()
    hidden = [Path(path).expanduser().resolve() for path in isolation.hidden]
    args = [
        "--die-with-parent", "--new-session",
        "--unshare-pid", "--unshare-ipc", "--unshare-uts",
        "--proc", "/proc", "--dev", "/dev",
    ]
    # Every host tree mounted into the sandbox; hidden paths are masked in all of them.
    mounted: list[Path] = []
    for link in _SYSTEM_LINKS:
        path = Path(link)
        if path.is_symlink():
            args += ["--symlink", os.readlink(path), link]
        elif path.is_dir():
            args += ["--ro-bind", link, link]
            mounted.append(path)
    for root in _SYSTEM_READ_ONLY:
        args += ["--ro-bind-try", root, root]
        if Path(root).exists():
            mounted.append(Path(root))
    visible = (*_SYSTEM_READ_ONLY, *_SYSTEM_LINKS)
    # What the agent needs from the host: a hidden path may not hold any of it.
    needed: list[tuple[str, Path]] = [("the working directory", workdir)]
    # In-memory directories first: the binds below must sit on top of them.
    args += ["--tmpfs", "/tmp", "--tmpfs", str(home)]
    needed.append(("the agent home", home.resolve()))
    for name in (*AGENT_HOME_WRITABLE, *AGENT_HOME_READ_ONLY):
        option = "--bind-try" if name in AGENT_HOME_WRITABLE else "--ro-bind-try"
        args += [option, str(home / name), str(home / name)]
        needed.append((f"the agent home's {name}", (home / name).resolve()))
    for executable in executables:
        assets = executable_assets(Path(executable))
        needed.append((f"the agent executable {executable}", assets))
        if not _inside(assets, visible):
            args += ["--ro-bind", str(assets), str(assets)]
            mounted.append(assets)
    args += ["--bind", str(workdir), str(workdir)]
    mounted.append(workdir)
    for root in mounted:
        needed.append((f"the mounted tree {root}", root.resolve()))
    for path in hidden:
        for what, target in needed:
            if _contains(path, target):
                raise ToolIsolationUnavailable(
                    f"{what} is inside a path hidden from the agent ({path}), so the sandbox would show part of it; "
                    "move it outside the vault and the enrolled repositories"
                )
    for path in hidden:
        if not path.exists() or not any(_contains(root.resolve(), path) for root in mounted):
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
    if executable_assets(Path(executable)).is_dir():
        # A Node launcher also needs its interpreter.
        node = shutil.which("node")
        if node:
            needed.append(Path(node))
    arguments = sandbox_arguments(isolation, executables=needed, home=home)
    if not _inside(Path(executable), (*_SYSTEM_READ_ONLY, *_SYSTEM_LINKS)):
        # Only the resolved file (or its package) is mounted, not a link to it.
        executable = str(Path(executable).resolve())
    return [bwrap, *arguments, "--", executable, *command[1:]]


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
    "executable_assets",
    "isolation_mode",
    "isolation_unavailable_reason",
    "sandbox_arguments",
    "sandboxed_command",
    "tool_isolation",
    "write_launcher",
]

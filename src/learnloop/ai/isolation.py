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
  in-memory directories. The agent keeps its run state there (its state
  locations are pinned to the home, below), so none of it reaches the host.
  Codex 0.161 writes its ``installation_id``, its state, log, goal, memory,
  queue and thread-history databases, session rollouts, shell snapshots, lock
  files, model/app/plugin caches, system skills and ``tmp/arg0`` helpers.
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

Mount order keeps the home private. The working directory and an executable's
package are bound after the in-memory home, so either one containing the home
would put the host's home (its history, transcripts and ``installation_id``)
back on top of it. Such a layout is refused. The working directory must not
lie inside the home either: bound from the host on top of it, it would receive
whatever the agent keeps under that part of its home (Codex 0.161 installed its
system skills into a working directory at ``<home>/skills``, and its databases
into one named by ``sqlite_home``). An executable inside the home is a
read-only bind of the host's files, and stays allowed.

Settings can move the agent's run state out of its home. Codex 0.161 puts its
databases under ``sqlite_home`` from any config layer, else
``$CODEX_SQLITE_HOME`` (relative to the working directory), else
``$CODEX_HOME``. ``$CODEX_ROLLOUT_TRACE_ROOT`` adds a trace bundle with every
prompt and response. The sandbox inherits the host's environment, so it pins
``CODEX_HOME`` and ``CODEX_SQLITE_HOME`` to the private home and unsets the
trace root. A configured ``sqlite_home`` outranks the environment and is read
from files the sandbox cannot rewrite: the system, user, project and legacy
managed configuration and ``-c`` overrides. A launch is refused unless that
location's effective mount is the private home itself. Outside the home, or
under a host bind inside it (an executable's package, a bound credential
file), it would leave the databases on the host or stop the agent at startup
on a read-only mount.

The settings are read the way Codex reads them, or the launch is refused.
Codex parses TOML 1.1 and Python's ``tomllib`` only TOML 1.0, so a file
``tomllib`` cannot parse is refused when it could set the key: when it names
it, or holds a backslash, since a quoted key can spell the name with escapes
(``"sqlite_\\u0068ome"``). ``-c`` overrides are read in every form clap
accepts (``-c V``, ``-cV``, ``-c=V``, ``--config V``, ``--config=V``); an
argument that names the setting in any other form is refused.

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
import tomllib
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
# Where the agent's run state goes when a setting moves it (see the module
# docstring). The environment is pinned inside the sandbox; the settings are
# checked against the private home before launch.
AGENT_ENV_PINNED_TO_HOME = ("CODEX_HOME", "CODEX_SQLITE_HOME")
AGENT_ENV_UNSET = ("CODEX_ROLLOUT_TRACE_ROOT",)
AGENT_STATE_SETTINGS = ("sqlite_home",)
# Config layers outside the agent home that the sandbox shows the agent (``/etc``
# is mounted read-only). ``managed_config.toml`` sits on top of every other layer.
AGENT_SYSTEM_CONFIG = (Path("/etc/codex/config.toml"), Path("/etc/codex/managed_config.toml"))


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


def _refuse_if_it_covers_the_home(what: str, mount: Path, home: Path) -> None:
    """A bind that follows the in-memory home must not contain it (see the module docstring)."""

    if any(_contains(mount, path) for path in (home, home.resolve())):
        raise ToolIsolationUnavailable(
            f"{what} contains the agent home ({home}); it is mounted after the private in-memory home, so the agent "
            "would see and write the host's home (its history, transcripts and installation_id); use a working "
            "directory and an agent executable that do not contain the agent home"
        )


def _refuse_if_it_is_inside_the_home(what: str, mount: Path, home: Path) -> None:
    """A writable host bind inside the in-memory home would receive what the agent keeps there."""

    if any(_contains(path, mount) for path in (home, home.resolve())):
        raise ToolIsolationUnavailable(
            f"{what} is inside the agent home ({home}); it is bound from the host on top of the private in-memory "
            "home, so whatever the agent keeps under that part of its home (its databases, sessions, skills and "
            "caches) would reach the host; use a working directory outside the agent home"
        )


def _setting(path: Path, key: str) -> tuple[bool, Any]:
    """``(present, value)`` of the top-level ``key`` in the TOML file at ``path``."""

    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, NotADirectoryError):
        return False, None
    except (OSError, UnicodeDecodeError) as exc:
        raise ToolIsolationUnavailable(
            f"cannot read {path} to check where the agent keeps its run state ({exc})"
        ) from exc
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        # Codex parses TOML 1.1, tomllib only 1.0. A key is bare, a literal
        # string or a basic string: every spelling of ``key`` without an escape
        # contains ``key`` itself, and an escape needs a backslash.
        if key not in text and "\\" not in text:
            return False, None
        raise ToolIsolationUnavailable(
            f"cannot parse {path} to check its {key} setting ({exc}); Codex reads TOML 1.1 and this check only "
            f"TOML 1.0, and the file names {key} or holds an escape that could spell it in a quoted key; rewrite "
            "it in TOML 1.0 (no newlines or trailing commas in inline tables, no \\x or \\e escapes)"
        ) from exc
    return key in data, data.get(key)


def _override_name(override: str) -> str | None:
    """The key of a ``key=value`` override as Codex reads it: before the first ``=``, trimmed."""

    name, separator, _raw = override.partition("=")
    return name.strip() if separator else None


def _command_line_settings(arguments: Iterable[str], key: str) -> Iterator[tuple[str, Any]]:
    """Each ``-c``/``--config`` override of ``key``, parsed as Codex parses it.

    clap reads an override from ``-c VALUE``, ``-cVALUE``, ``-c=VALUE``,
    ``--config VALUE`` and ``--config=VALUE``; Codex 0.161's other short
    options take values or exit, so none hides a ``-c`` in a cluster. An
    argument may be read more than one way (``-c -cVALUE``); each reading is
    checked. An argument that names ``key`` other than as an override of it
    is refused: this check cannot tell what Codex would make of it.
    """

    arguments = list(arguments)
    readings: dict[int, list[str]] = {}
    for index, argument in enumerate(arguments):
        if argument in ("-c", "--config"):
            if index + 1 < len(arguments):
                readings.setdefault(index + 1, []).append(arguments[index + 1])
        elif argument.startswith("--config="):
            readings.setdefault(index, []).append(argument.removeprefix("--config="))
        elif argument.startswith("-c") and not argument.startswith("--"):
            # clap takes the rest of the argument as the value, less one leading "=".
            readings.setdefault(index, []).append(argument[2:].removeprefix("="))
    for index, argument in enumerate(arguments):
        if key not in argument:
            continue
        overrides = [override for override in readings.get(index, ()) if _override_name(override) == key]
        if not overrides:
            raise ToolIsolationUnavailable(
                f"the agent's command-line argument {argument!r} names {key} but is not a -c/--config override of "
                f"it, so this check cannot tell where the agent would keep its run state; remove the argument or "
                f"write it as -c {key}=<a path inside the agent home>"
            )
        for override in overrides:
            raw = override.partition("=")[2].strip()
            try:
                value = tomllib.loads(f"value = {raw}")["value"]
            except tomllib.TOMLDecodeError:
                value = raw.strip("\"'")  # Codex takes a value that is not TOML as a bare string
            yield override, value


def _refuse_state_outside_the_home(
    home: Path, workdir: Path, mounted: Iterable[Path], binds_over_home: Iterable[Path], arguments: Iterable[str]
) -> None:
    """Refuse a launch whose configuration moves the agent's run state out of its private home.

    Every config layer the sandbox shows the agent is checked: the system and
    legacy managed files, the user's (bound into the home), project files in
    the working directory and in any visible parent, and ``-c`` overrides. A
    relative value is resolved as Codex resolves it: against the directory of
    the file that sets it, or the working directory for an override. The
    location must be in the in-memory home and under none of the host binds
    on top of it (``binds_over_home``): its effective mount is then the home.
    """

    binds_over_home = list(binds_over_home)
    roots = [root.resolve() for root in mounted]
    files = [*AGENT_SYSTEM_CONFIG, home / "config.toml", workdir / "config.toml"]
    files += [
        directory / ".codex" / "config.toml"
        for directory in (workdir, *workdir.parents)
        if any(_contains(root, directory) for root in roots)
    ]
    for key in AGENT_STATE_SETTINGS:
        settings = [(f"{key} in {path}", *_setting(path, key), path.parent) for path in files]
        settings += [(f"{key} override -c {override!r}", True, value, workdir)
                     for override, value in _command_line_settings(arguments, key)]
        for where, present, value, base in settings:
            if not present:
                continue
            location: Any = value
            if isinstance(value, str) and value.strip():
                location = Path(os.path.normpath(base / Path(value).expanduser()))
                if _contains(home, location):
                    bind = next((path for path in binds_over_home if _contains(path, location)), None)
                    if bind is None:
                        continue
                    raise ToolIsolationUnavailable(
                        f"the agent's {where} puts its run state at {location}, under {bind}, which is bound from the "
                        f"host on top of its private in-memory home ({home}); there the state would reach the host, or "
                        f"the agent would not start on a read-only mount; remove the setting or point it elsewhere "
                        f"inside {home}"
                    )
            raise ToolIsolationUnavailable(
                f"the agent's {where} puts its run state at {location}, outside its private in-memory home ({home}); "
                "only that home is private by construction (in the working directory the state would reach the host, "
                f"on a read-only mount the agent would not start); remove the setting or point it inside {home}"
            )


def sandbox_arguments(
    isolation: ToolIsolation,
    *,
    executables: Iterable[Path] = (),
    home: Path | None = None,
    arguments: Iterable[str] = (),
) -> list[str]:
    """bubblewrap options (without the program) for one isolated process.

    ``arguments`` are the program's own arguments, checked for ``-c``
    overrides of the agent's state locations. Raises
    :class:`ToolIsolationUnavailable` when a hidden path holds something the
    sandbox must mount, when a mount would cover the private agent home, when
    the working directory lies inside that home, or when the configuration
    moves the agent's run state out of it (see the module docstring).
    """

    workdir = Path(isolation.workdir).resolve()
    # Absolute, so the in-memory home and the agent's $CODEX_HOME are one path.
    home = Path(os.path.abspath((home or agent_home()).expanduser()))
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
    # Host binds that follow the home tmpfs: where they sit, the home is the host's again.
    binds_over_home: list[Path] = []
    for name in (*AGENT_HOME_WRITABLE, *AGENT_HOME_READ_ONLY):
        option = "--bind-try" if name in AGENT_HOME_WRITABLE else "--ro-bind-try"
        args += [option, str(home / name), str(home / name)]
        binds_over_home.append(home / name)
        needed.append((f"the agent home's {name}", (home / name).resolve()))
    for executable in executables:
        assets = executable_assets(Path(executable))
        needed.append((f"the agent executable {executable}", assets))
        if not _inside(assets, visible):
            _refuse_if_it_covers_the_home(f"the agent executable's package {assets}", assets, home)
            args += ["--ro-bind", str(assets), str(assets)]
            binds_over_home.append(assets)
            mounted.append(assets)
    _refuse_if_it_covers_the_home(f"the working directory {workdir}", workdir, home)
    _refuse_if_it_is_inside_the_home(f"the working directory {workdir}", workdir, home)
    args += ["--bind", str(workdir), str(workdir)]
    binds_over_home.append(workdir)
    mounted.append(workdir)
    _refuse_state_outside_the_home(home, workdir, mounted, binds_over_home, arguments)
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
    for name in AGENT_ENV_PINNED_TO_HOME:
        args += ["--setenv", name, str(home)]
    for name in AGENT_ENV_UNSET:
        args += ["--unsetenv", name]
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
    options = sandbox_arguments(isolation, executables=needed, home=home, arguments=command[1:])
    if not _inside(Path(executable), (*_SYSTEM_READ_ONLY, *_SYSTEM_LINKS)):
        # Only the resolved file (or its package) is mounted, not a link to it.
        executable = str(Path(executable).resolve())
    return [bwrap, *options, "--", executable, *command[1:]]


def write_launcher(directory: Path, isolation: ToolIsolation, executable: str, *, home: Path | None = None) -> Path:
    """A ``#!/bin/sh`` launcher that runs ``executable "$@"`` inside the sandbox.

    For SDKs that take a program path and append their own arguments. Those
    arguments are not known here, so a ``-c`` override among them is not
    checked; LearnLoop's Codex client passes none (``app-server --listen
    stdio://`` only).
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

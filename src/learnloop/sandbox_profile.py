"""The hardened bubblewrap profile every sandboxed run of untrusted Python shares.

Figure renders, the inspector's renders, the declared-function checks, PF generator programs and the notebook
runtime's marimo servers all run under this one profile: every namespace unshared (so no network), system and
interpreter mounts read-only, a fresh ``/tmp``, one writable working directory, and the sandbox dying with the
process that started it. The hardened flags make the user namespace mandatory with no further ones inside it and
drop every capability. Callers add only their own mounts (``extra_args``); the profile itself has no copies.

Standard library only, so the notebook runtime can use it without importing the figure or authoring code.
"""
from __future__ import annotations

import os
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path

#: The hardened profile's extra flags. ``--unshare-user`` makes the user namespace mandatory (``--unshare-all`` only
#: tries it), which ``--disable-userns`` needs: the sandboxed code can create no further user namespace (the usual
#: first step of a kernel exploit from inside one), and holds no capability (``--cap-drop ALL``). keep: a security
#: boundary.
HARDENED_BWRAP_FLAGS: tuple[str, ...] = ("--unshare-user", "--disable-userns", "--cap-drop", "ALL")


def bwrap_path() -> str | None:
    """The bubblewrap binary to sandbox with, or None off Linux."""

    if sys.platform != "linux":
        return None
    return shutil.which("bwrap")


def executable_mount_roots(executable: str) -> set[str]:
    """Install roots (``<root>/bin/exe`` → ``<root>``) for an executable and every hop of its symlink chain, so a
    venv python that links into e.g. a uv-managed interpreter tree stays runnable inside the sandbox."""

    roots: set[str] = set()
    path = Path(executable)
    for _ in range(10):
        if len(path.parents) >= 2:
            roots.add(str(path.parents[1]))
        try:
            target = Path(os.readlink(path))
        except OSError:
            break
        path = target if target.is_absolute() else path.parent / target
    return roots


def sandboxed_command(command: list[str], workdir: Path | None, bwrap: str, *, hardened: bool = True,
                      unset_env: tuple[str, ...] = (), extra_args: Sequence[str] = ()) -> list[str]:
    """Wrap ``command`` in bubblewrap: every namespace unshared (so no network), system and interpreter mounts
    read-only, ``workdir`` as the only writable bind (None: no writable host path at all; the caller's
    ``extra_args`` then give the command its tmpfs and working directory), and the sandbox dying with its parent.

    ``hardened``: also :data:`HARDENED_BWRAP_FLAGS` (a mandatory user namespace with no further ones, every
    capability dropped).

    ``unset_env``: variables the launcher outside the sandbox needed (a scope's session bus) that the sandboxed
    command must not see; bubblewrap unsets them before it execs.

    ``extra_args``: the caller's own bubblewrap options, placed after the profile's (so a later ``--chdir`` or a
    final ``--remount-ro /`` wins). Empty for every caller that predates them, whose command is unchanged."""

    args = [
        bwrap,
        "--die-with-parent",
        "--new-session",
        "--unshare-all",
        *(HARDENED_BWRAP_FLAGS if hardened else ()),
        "--proc", "/proc",
        "--dev", "/dev",
        "--tmpfs", "/tmp",
        "--ro-bind", "/usr", "/usr",
        "--ro-bind-try", "/lib", "/lib",
        "--ro-bind-try", "/lib64", "/lib64",
        "--ro-bind-try", "/bin", "/bin",
        "--ro-bind-try", "/sbin", "/sbin",
        # Font/loader config manim + its ffmpeg need; nothing else from /etc.
        "--ro-bind-try", "/etc/fonts", "/etc/fonts",
        "--ro-bind-try", "/etc/alternatives", "/etc/alternatives",
        "--ro-bind-try", "/etc/ld.so.cache", "/etc/ld.so.cache",
    ]
    prefixes = {sys.prefix, sys.base_prefix}
    prefixes |= executable_mount_roots(sys.executable)
    # command[0] is whatever interpreter/executable the caller picked (a dedicated animation venv, a conda env, an
    # explicit override): its install tree is mounted too, or the sandboxed exec fails.
    if command:
        prefixes |= executable_mount_roots(command[0])
    for prefix in sorted(prefixes):
        if prefix and prefix != "/usr" and not prefix.startswith("/usr/"):
            args += ["--ro-bind-try", prefix, prefix]
    if workdir is not None:
        args += ["--bind", str(workdir), str(workdir), "--chdir", str(workdir)]
    for name in unset_env:
        args += ["--unsetenv", name]
    args += list(extra_args)
    return [*args, "--", *command]


__all__ = ["HARDENED_BWRAP_FLAGS", "bwrap_path", "executable_mount_roots", "sandboxed_command"]

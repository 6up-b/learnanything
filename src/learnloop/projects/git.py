"""The only door to git: ``git -C <repo> ...`` with an argument list, no shell.

Every call runs with a timeout, without a terminal prompt, without pagers, and
for diffs without external diff drivers or textconv filters, so a repo's own
configuration cannot run commands through LearnLoop. Failures become
:class:`GitError` and the caller decides; nothing here retries.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Sequence

GIT_TIMEOUT_SECONDS = 30.0
# Agent-written commits can be large, but a capture never needs more than this.
MAX_GIT_OUTPUT_BYTES = 64 * 1024 * 1024


class GitError(RuntimeError):
    """A git command failed, timed out, or is unavailable."""


# Variables that would silently retarget or reshape every `git -C` below (git
# sets several of them while running a hook). User-level settings such as
# GIT_CONFIG_GLOBAL stay in effect.
_RETARGETING_VARIABLES = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_NAMESPACE",
        "GIT_PREFIX",
        "GIT_QUARANTINE_PATH",
        "GIT_DIFF_OPTS",
        "GIT_EXTERNAL_DIFF",
    }
)


def _environment() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key not in _RETARGETING_VARIABLES}
    env.update(
        GIT_TERMINAL_PROMPT="0",
        GIT_PAGER="cat",
        PAGER="cat",
        LC_ALL="C",
        GIT_OPTIONAL_LOCKS="0",
    )
    return env


def run_git(
    repo: Path,
    args: Sequence[str],
    *,
    input_bytes: bytes | None = None,
    ok_codes: tuple[int, ...] = (0,),
    timeout: float = GIT_TIMEOUT_SECONDS,
) -> bytes:
    """Run ``git -C repo *args`` and return stdout bytes."""

    command = ["git", "-C", str(repo), *args]
    try:
        completed = subprocess.run(  # noqa: S603 - argument list, never a shell
            command,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_environment(),
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise GitError("git is not installed or not on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise GitError(f"git {' '.join(args[:2])} timed out after {timeout:g}s") from exc
    except OSError as exc:
        raise GitError(f"git could not run: {exc}") from exc
    if completed.returncode not in ok_codes:
        message = completed.stderr.decode("utf-8", "replace").strip().splitlines()
        detail = message[-1] if message else f"exit {completed.returncode}"
        raise GitError(f"git {' '.join(args[:2])} failed: {detail}")
    if len(completed.stdout) > MAX_GIT_OUTPUT_BYTES:
        raise GitError(f"git {' '.join(args[:2])} output exceeds {MAX_GIT_OUTPUT_BYTES} bytes")
    return completed.stdout


def git_text(repo: Path, args: Sequence[str], **kwargs) -> str:
    return run_git(repo, args, **kwargs).decode("utf-8", "replace")


def repo_toplevel(path: Path) -> Path:
    """The canonical work-tree root of the repo containing ``path``."""

    if not Path(path).is_dir():
        raise GitError(f"{path} is not a directory")
    top = git_text(path, ["rev-parse", "--show-toplevel"]).strip()
    if not top:
        raise GitError(f"{path} is not inside a git work tree")
    return Path(top).resolve()


def head_sha(repo: Path) -> str | None:
    """HEAD's commit id, or ``None`` for a repo without commits."""

    try:
        return git_text(repo, ["rev-parse", "--verify", "--quiet", "HEAD^{commit}"]).strip() or None
    except GitError:
        return None


def empty_tree_sha(repo: Path) -> str:
    """The empty tree's id in this repo's hash format (sha1 or sha256)."""

    return git_text(repo, ["hash-object", "-t", "tree", "--stdin"], input_bytes=b"").strip()


def patch_id(repo: Path, diff_bytes: bytes) -> str | None:
    """``git patch-id --stable`` of a diff: equal for rebased/cherry-picked copies."""

    if not diff_bytes.strip():
        return None
    output = git_text(repo, ["patch-id", "--stable"], input_bytes=diff_bytes).strip()
    return output.split()[0] if output else None


__all__ = [
    "GIT_TIMEOUT_SECONDS",
    "GitError",
    "empty_tree_sha",
    "git_text",
    "head_sha",
    "patch_id",
    "repo_toplevel",
    "run_git",
]

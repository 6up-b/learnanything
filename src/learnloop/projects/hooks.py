"""The optional append-only ``post-commit`` hook (spec §3.1–3.2, P1, gate G1).

The hook only appends one JSON line ``{"repo_id", "sha", "at"}`` to the vault's
``projects/pending.jsonl`` and always exits 0: it never prompts, never runs
LearnLoop, never reads code, and cannot fail or slow a commit. It writes
nothing when the vault's ``projects/`` directory is gone. The next sweep reads
the list: agent-trailer commits are captured, trailer-less ones are offered for
a one-tap self-report.

An existing shell hook keeps its content: the block is added between
markers and removed the same way. Each enrolled work tree gets its own block,
marked with its repo id and guarded by its top-level path, because linked git
worktrees share one hooks directory: a commit is logged only by the block of
the work tree it was made in, and uninstalling one registration leaves the
others. A non-shell hook, or a shared ``core.hooksPath`` (which would also run
for other repositories), is refused rather than modified.
"""

from __future__ import annotations

import os
import re
import shlex
import stat
from pathlib import Path
from typing import Any

from learnloop.projects.experiment_store import ProjectStore, pending_path
from learnloop.projects.git import GitError, git_text

HOOK_NAME = "post-commit"
# Every block's first line starts with HOOK_BEGIN; hook_markers() gives the
# full markers of one registration.
HOOK_BEGIN = "# >>> learnloop project capture"
HOOK_END = "# <<< learnloop project capture"
# The single-registration block of the first M1 build (no repo id, no guard).
_LEGACY_MARKERS = (
    "# >>> learnloop project capture (append-only; never blocks a commit) >>>",
    "# <<< learnloop project capture <<<",
)
_SHELL_SHEBANG = re.compile(r"^#!\s*(?:/usr/bin/env\s+)?(?:/\S*/)?(?:sh|bash|dash|zsh|ksh)\b")
_REPO_ID = re.compile(r"^[0-9A-Z]{26}$")


class HookError(RuntimeError):
    """The hook cannot be installed or removed safely."""


def hook_markers(repo_id: str) -> tuple[str, str]:
    return (
        f"{HOOK_BEGIN} {repo_id} (append-only; never blocks a commit) >>>",
        f"{HOOK_END} {repo_id} <<<",
    )


def hook_block(vault_root: Path, repo_id: str, work_tree: Path) -> str:
    if not _REPO_ID.match(repo_id):
        raise HookError(f"unexpected repo id {repo_id!r}")
    begin, end = hook_markers(repo_id)
    pending = pending_path(Path(vault_root).resolve())
    target = shlex.quote(str(pending))
    directory = shlex.quote(str(pending.parent))
    top = shlex.quote(str(work_tree))
    return (
        f"{begin}\n"
        "(\n"
        f"  [ -d {directory} ] || exit 0\n"
        # Linked worktrees share this hook: log only commits made in this one.
        f'  [ "$(git rev-parse --show-toplevel 2>/dev/null)" = {top} ] || exit 0\n'
        '  sha=$(git rev-parse --verify --quiet HEAD 2>/dev/null) || exit 0\n'
        '  at=$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null) || at=""\n'
        f"  printf '{{\"repo_id\":\"%s\",\"sha\":\"%s\",\"at\":\"%s\"}}\\n' '{repo_id}' \"$sha\" \"$at\" >> {target}\n"
        ") </dev/null >/dev/null 2>&1 || true\n"
        f"{end}\n"
    )


def _hooks_dir(repo: Path) -> Path:
    try:
        configured = git_text(repo, ["config", "--get", "core.hooksPath"], ok_codes=(0, 1)).strip()
    except GitError as exc:
        raise HookError(str(exc)) from exc
    if configured:
        raise HookError(
            f"core.hooksPath is set ({configured}); a shared hooks directory would log other "
            "repos' commits under this repo. Add the block to that hook yourself, or unset it."
        )
    relative = git_text(repo, ["rev-parse", "--git-path", "hooks"]).strip()
    path = Path(relative)
    return path if path.is_absolute() else (repo / path)


def _strip_block(text: str, repo_id: str) -> str:
    """Remove this registration's block (and a legacy unguarded one); keep the rest."""

    for begin, end in (hook_markers(repo_id), _LEGACY_MARKERS):
        pattern = re.compile(rf"\n?{re.escape(begin)}\n.*?{re.escape(end)}\n?", re.DOTALL)
        text = pattern.sub("\n", text)
    return text


def _has_block(text: str, repo_id: str) -> bool:
    return hook_markers(repo_id)[0] in text or _LEGACY_MARKERS[0] in text


def install_hook(vault_root: Path, store: ProjectStore, repo_row: dict[str, Any]) -> dict[str, Any]:
    repo = Path(repo_row["path"])
    hooks = _hooks_dir(repo)
    hooks.mkdir(parents=True, exist_ok=True)
    path = hooks / HOOK_NAME
    block = hook_block(vault_root, repo_row["id"], repo)
    existing = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    had_block = _has_block(existing, repo_row["id"])
    base = _strip_block(existing, repo_row["id"]) if had_block else existing
    if not base.strip():
        new_text = "#!/bin/sh\n" + block + "exit 0\n"
        action = "updated" if had_block else "installed"
    else:
        lines = base.splitlines(keepends=True)
        if not _SHELL_SHEBANG.match(lines[0]):
            raise HookError(
                f"{path} exists and is not a shell script; add the capture block to it yourself:\n{block}"
            )
        # An `exit` later in the existing hook would skip an appended block,
        # so the block goes right after the shebang line.
        first = lines[0] if lines[0].endswith("\n") else lines[0] + "\n"
        new_text = first + block + "".join(lines[1:])
        action = "updated" if had_block else "appended"
    path.write_text(new_text, encoding="utf-8")
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    store.set_hook_installed(repo_row["id"], True)
    return {"status": action, "hook": str(path)}


def uninstall_hook(store: ProjectStore, repo_row: dict[str, Any]) -> dict[str, Any]:
    repo = Path(repo_row["path"])
    path = _hooks_dir(repo) / HOOK_NAME
    if not path.exists():
        store.set_hook_installed(repo_row["id"], False)
        return {"status": "absent", "hook": str(path)}
    text = path.read_text(encoding="utf-8", errors="replace")
    if not _has_block(text, repo_row["id"]):
        store.set_hook_installed(repo_row["id"], False)
        return {"status": "absent", "hook": str(path)}
    remainder = _strip_block(text, repo_row["id"])
    if remainder.strip() in {"#!/bin/sh\n\nexit 0", "#!/bin/sh\nexit 0", "#!/bin/sh"}:
        os.unlink(path)
        action = "removed"
    else:
        path.write_text(remainder, encoding="utf-8")
        action = "block_removed"
    store.set_hook_installed(repo_row["id"], False)
    return {"status": action, "hook": str(path)}


__all__ = ["HOOK_BEGIN", "HOOK_END", "HookError", "hook_block", "hook_markers", "install_hook", "uninstall_hook"]

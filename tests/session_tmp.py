"""Each pytest run's scratch directory under ``.pytest_tmp``, removed when the run ends.

Fixture vaults, pytest's numbered ``tmp_path`` roots, the isolated config dir and the fresh-schema caches all live in
one ``run-<pid>-*`` directory per run. The process that made it deletes it when the run ends: the shared root used to
keep every run's vaults and grew to tens of gigabytes per checkout. xdist workers, and a pytest that a test starts,
inherit the directory through the environment and leave it to its owner. A run that was killed (oomd, Ctrl-C twice)
leaves its directory behind; the next run in the same checkout removes it once its pid is gone.

Set ``LEARNLOOP_KEEP_TEST_TMP=1`` to keep the directory, for instance to look at a failed test's vault.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

SESSION_ENV = "LEARNLOOP_TEST_SESSION_TMP"
OWNER_ENV = "LEARNLOOP_TEST_SESSION_TMP_OWNER"
KEEP_ENV = "LEARNLOOP_KEEP_TEST_TMP"
RUN_PREFIX = "run-"
# What runs before per-run directories left directly under the root; nothing writes there any more.
LEGACY_PREFIXES = ("pytest-of-", "global_settings_isolated", "fresh-schema-")


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _run_pid(name: str) -> int | None:
    if not name.startswith(RUN_PREFIX):
        return None
    pid, _, _ = name[len(RUN_PREFIX) :].partition("-")
    return int(pid) if pid.isdigit() else None


def sweep_stale(temp_root: Path) -> list[Path]:
    """Remove the directories of runs whose process is gone, and what older runs left directly under the root."""
    removed = []
    for entry in sorted(temp_root.iterdir()) if temp_root.is_dir() else ():
        pid = _run_pid(entry.name)
        stale = (pid is not None and pid != os.getpid() and not pid_alive(pid)) or entry.name.startswith(
            LEGACY_PREFIXES
        )
        if stale:
            shutil.rmtree(entry, ignore_errors=True) if entry.is_dir() else entry.unlink(missing_ok=True)
            removed.append(entry)
    return removed


def session_root(temp_root: Path) -> Path:
    """This run's directory: the owner's when a live run handed it down, otherwise a new one this process owns."""
    inherited, owner = os.environ.get(SESSION_ENV), os.environ.get(OWNER_ENV, "")
    if inherited and owner.isdigit() and pid_alive(int(owner)) and Path(inherited).is_dir():
        return Path(inherited)
    temp_root.mkdir(parents=True, exist_ok=True)
    sweep_stale(temp_root)
    root = Path(tempfile.mkdtemp(prefix=f"{RUN_PREFIX}{os.getpid()}-", dir=temp_root))
    os.environ[SESSION_ENV] = str(root)
    os.environ[OWNER_ENV] = str(os.getpid())
    return root


def finish(root: Path) -> str | None:
    """Delete ``root`` if this process owns it. Returns a line to print when it is kept on request, else None."""
    if os.environ.get(OWNER_ENV) != str(os.getpid()) or os.environ.get(SESSION_ENV) != str(root):
        return None
    if os.environ.get(KEEP_ENV, "").strip() not in ("", "0"):
        return f"{KEEP_ENV} is set: kept this run's test files in {root}"
    shutil.rmtree(root, ignore_errors=True)
    return None
